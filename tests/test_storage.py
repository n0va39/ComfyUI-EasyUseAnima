import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_storage_module(folder_paths_module=None):
    package_name = "easyuse_anima_storage_test_package"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ROOT)]
    sys.modules[package_name] = package

    previous_folder_paths = sys.modules.get("folder_paths")
    if folder_paths_module is not None:
        sys.modules["folder_paths"] = folder_paths_module
    elif "folder_paths" in sys.modules:
        del sys.modules["folder_paths"]

    try:
        spec = importlib.util.spec_from_file_location(
            f"{package_name}.storage",
            ROOT / "storage.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if previous_folder_paths is not None:
            sys.modules["folder_paths"] = previous_folder_paths
        elif "folder_paths" in sys.modules:
            del sys.modules["folder_paths"]


class StoragePathTests(unittest.TestCase):
    def test_uses_comfyui_system_user_directory_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_folder_paths = types.SimpleNamespace(
                get_system_user_directory=lambda name: str(root / f"__{name}")
            )
            storage = load_storage_module(fake_folder_paths)

            self.assertEqual(storage.USER_DATA_DIR, root / "__easyuse_anima")

    def test_falls_back_to_package_data_dir_without_comfyui_folder_paths(self):
        storage = load_storage_module()

        self.assertEqual(storage.USER_DATA_DIR, storage.PACKAGE_DATA_DIR)


if __name__ == "__main__":
    unittest.main()
