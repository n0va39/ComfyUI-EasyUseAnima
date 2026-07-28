import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_api_module():
    package_name = "easyuse_anima_test_package"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ROOT)]
    sys.modules[package_name] = package

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.api",
        ROOT / "api.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LoraPreviewTests(unittest.TestCase):
    def test_resolver_is_owned_by_the_canonical_factory(self):
        api = load_api_module()
        resolver = api._resolve_lora_preview_path

        self.assertEqual(resolver.__name__, "_resolve_lora_preview_path")
        self.assertTrue(
            resolver.__module__.endswith(
                ".easyuse_anima.api.routes.lora_preview"
            )
        )
        self.assertEqual(resolver.__code__.co_argcount, 1)
        owner = sys.modules[resolver.__module__]
        self.assertIs(api.LORA_PREVIEW_EXTENSIONS, owner.LORA_PREVIEW_EXTENSIONS)
        self.assertEqual(
            api.LORA_PREVIEW_EXTENSIONS,
            (".webp", ".png", ".jpg", ".jpeg"),
        )
        self.assertEqual(owner.__all__, ("build_lora_preview_handler",))

    def test_resolver_import_failure_and_name_normalization_are_preserved(self):
        api = load_api_module()
        original_import = __import__

        def guarded_import(name, *args, **kwargs):
            if name == "folder_paths":
                raise RuntimeError("folder paths unavailable")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=guarded_import):
            self.assertIsNone(api._resolve_lora_preview_path("example.safetensors"))

        calls = []
        folder_paths = types.SimpleNamespace(
            get_full_path=lambda category, name: calls.append((category, name))
        )
        with patch.dict(sys.modules, {"folder_paths": folder_paths}):
            for name in (None, "", "  ", "None", " None "):
                with self.subTest(name=name):
                    self.assertIsNone(api._resolve_lora_preview_path(name))
            self.assertIsNone(
                api._resolve_lora_preview_path(" style/example.safetensors ")
            )

        self.assertEqual(calls, [("loras", "style/example.safetensors")])

    def test_resolver_keeps_path_order_containment_and_first_match(self):
        api = load_api_module()
        calls = []
        resolved_lora = "/safe/example.safetensors"
        resolved_preview = "/safe/example.jpeg"

        def get_full_path(category, name):
            calls.append(("full_path", category, name))
            return "relative/example.safetensors"

        def abspath(path):
            calls.append(("abspath", path))
            return {
                "relative/example.safetensors": resolved_lora,
                "/safe/example.webp": "/outside/example.webp",
                "/safe/example.png": "Z:/example.png",
            }.get(path, path)

        def dirname(path):
            calls.append(("dirname", path))
            return "/safe"

        def splitext(path):
            calls.append(("splitext", path))
            return "/safe/example", ".safetensors"

        def commonpath(paths):
            calls.append(("commonpath", paths))
            if paths[1] == "Z:/example.png":
                raise ValueError("different drive")
            if paths[1] == "/outside/example.webp":
                return "/outside"
            return "/safe"

        def isfile(path):
            calls.append(("isfile", path))
            return path == resolved_preview

        folder_paths = types.SimpleNamespace(get_full_path=get_full_path)
        with (
            patch.dict(sys.modules, {"folder_paths": folder_paths}),
            patch.object(api.os.path, "abspath", side_effect=abspath),
            patch.object(api.os.path, "dirname", side_effect=dirname),
            patch.object(api.os.path, "splitext", side_effect=splitext),
            patch.object(api.os.path, "commonpath", side_effect=commonpath),
            patch.object(api.os.path, "isfile", side_effect=isfile),
        ):
            preview = api._resolve_lora_preview_path(
                "style/example.safetensors"
            )

        self.assertEqual(preview, resolved_preview)
        self.assertEqual(
            calls,
            [
                ("full_path", "loras", "style/example.safetensors"),
                ("abspath", "relative/example.safetensors"),
                ("dirname", resolved_lora),
                ("splitext", resolved_lora),
                ("abspath", "/safe/example.webp"),
                ("commonpath", ("/safe", "/outside/example.webp")),
                ("abspath", "/safe/example.png"),
                ("commonpath", ("/safe", "Z:/example.png")),
                ("abspath", "/safe/example.jpg"),
                ("commonpath", ("/safe", "/safe/example.jpg")),
                ("isfile", "/safe/example.jpg"),
                ("abspath", resolved_preview),
                ("commonpath", ("/safe", resolved_preview)),
                ("isfile", resolved_preview),
            ],
        )

    def test_resolve_lora_preview_accepts_jpeg_fallback(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            lora_path = folder / "example.safetensors"
            preview_path = folder / "example.jpeg"
            lora_path.write_bytes(b"lora")
            preview_path.write_bytes(b"jpeg")

            sys.modules["folder_paths"] = types.SimpleNamespace(
                get_full_path=lambda category, name: str(lora_path)
                if category == "loras" and name == "style/example.safetensors"
                else None,
            )
            try:
                self.assertEqual(
                    api._resolve_lora_preview_path("style/example.safetensors"),
                    str(preview_path.resolve()),
                )
            finally:
                sys.modules.pop("folder_paths", None)


if __name__ == "__main__":
    unittest.main()
