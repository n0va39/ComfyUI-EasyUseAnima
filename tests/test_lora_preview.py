import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


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
