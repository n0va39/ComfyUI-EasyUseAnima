from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easyuse_anima import bootstrap, runtime as runtime_module
from easyuse_anima.aio import first_pass_cache as aio_first_pass_cache
from easyuse_anima.autocomplete import dataset as autocomplete_dataset
from easyuse_anima.autocomplete import index as autocomplete_index
from easyuse_anima.autocomplete import service as autocomplete_service
from easyuse_anima.infrastructure.comfy.provider import DefaultComfyHostProvider
from easyuse_anima.infrastructure.filesystem import paths as storage_paths
from easyuse_anima.runtime import (
    Clock,
    RuntimeConfig,
    RuntimeResource,
    RuntimeServices,
    get_runtime,
    install_runtime,
)
from easyuse_anima.seed.service import InMemorySeedReservationService
from easyuse_anima.translation import service as translation_service
from easyuse_anima.translation.service import PromptTranslationService
from easyuse_anima.wildcard import snapshot as wildcard_snapshot


class FakeComfyHostProvider:
    def max_resolution(self) -> int:
        return 16384

    def find_node_class(self, node_id: str) -> type[object] | None:
        return None

    def find_node_mapping_class(self, node_id: str) -> type[object] | None:
        return None

    def find_loaded_node_class(self, node_id: str) -> type[object] | None:
        return None


class FakeClock:
    def monotonic(self) -> float:
        return 0.0


class FakeAutocompleteService:
    def resolve_source(self, source=None):
        raise AssertionError(source)

    def available_sources(self, selected=None):
        raise AssertionError(selected)

    def status(self, path):
        raise AssertionError(path)

    def search(self, query, limit=20, path=None, category=None):
        raise AssertionError((query, limit, path, category))

    def classify(self, text, limit=240, path=None):
        raise AssertionError((text, limit, path))


class FakeWildcardSnapshots:
    def snapshot_for_roots(self, roots, *, scan_sources, build_snapshot):
        raise AssertionError((roots, scan_sources, build_snapshot))


class FakeAIOFirstPassCache:
    def get(self, cache_key):
        raise AssertionError(cache_key)

    def put(self, cache_key, latent, image):
        raise AssertionError((cache_key, latent, image))


class RuntimeBaseContractTests(unittest.TestCase):
    def test_runtime_config_is_frozen_slotted_and_does_not_resolve_paths(self):
        package_root = Path("package-root")
        package_data_dir = Path("package-data")
        user_data_dir = Path("user-data")

        config = RuntimeConfig(
            package_root=package_root,
            package_data_dir=package_data_dir,
            user_data_dir=user_data_dir,
        )

        self.assertIs(config.package_root, package_root)
        self.assertIs(config.package_data_dir, package_data_dir)
        self.assertIs(config.user_data_dir, user_data_dir)
        self.assertFalse(hasattr(config, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            config.user_data_dir = Path("other")

    def test_clock_is_a_narrow_monotonic_structural_contract(self):
        class FakeClock:
            def monotonic(self) -> float:
                return 12.5

        clock: Clock = FakeClock()

        self.assertEqual(clock.monotonic(), 12.5)

    def test_runtime_resource_is_an_idempotent_close_structural_contract(self):
        class FakeResource:
            def __init__(self) -> None:
                self.closed = False
                self.release_calls = 0

            def close(self) -> None:
                if self.closed:
                    return
                self.release_calls += 1
                self.closed = True

        resource: RuntimeResource = FakeResource()

        resource.close()
        resource.close()

        self.assertTrue(resource.closed)
        self.assertEqual(resource.release_calls, 1)

    def test_runtime_public_surface_adds_only_base_contracts(self):
        self.assertEqual(
            runtime_module.__all__,
            (
                "Clock",
                "RuntimeConfig",
                "RuntimeResource",
                "RuntimeServices",
                "get_runtime",
                "install_runtime",
            ),
        )

    def test_runtime_contract_document_is_linked_from_architecture_entry(self):
        contract_name = "python-runtime-base-contract.md"
        contract = ROOT / "docs" / "architecture" / contract_name
        architecture_entry = ROOT / "docs" / "architecture" / "README.md"

        self.assertTrue(contract.is_file())
        self.assertIn(
            contract_name,
            architecture_entry.read_text(encoding="utf-8"),
        )


class RuntimeServicesTests(unittest.TestCase):
    def setUp(self):
        self.runtime_state = patch.object(runtime_module, "_RUNTIME_SERVICES", None)
        self.runtime_state.start()
        self.default_runtime_state = patch.object(bootstrap, "_DEFAULT_RUNTIME", None)
        self.default_runtime_state.start()

    def tearDown(self):
        self.default_runtime_state.stop()
        self.runtime_state.stop()

    @staticmethod
    def make_runtime() -> RuntimeServices:
        return RuntimeServices(
            comfy=FakeComfyHostProvider(),
            seed_reservations=InMemorySeedReservationService(),
            config=RuntimeConfig(
                package_root=Path("package-root"),
                package_data_dir=Path("package-data"),
                user_data_dir=Path("user-data"),
            ),
            clock=FakeClock(),
            translation=PromptTranslationService(),
            autocomplete=FakeAutocompleteService(),
            wildcard_snapshots=FakeWildcardSnapshots(),
            aio_first_pass_cache=FakeAIOFirstPassCache(),
        )

    def test_runtime_value_is_frozen(self):
        runtime = self.make_runtime()

        with self.assertRaises(FrozenInstanceError):
            runtime.comfy = FakeComfyHostProvider()

    def test_isolated_construction_does_not_install_runtime(self):
        self.make_runtime()

        with self.assertRaisesRegex(
            RuntimeError,
            r"^\[EasyUseAnima\] RuntimeServices has not been installed\.$",
        ):
            get_runtime()

    def test_first_install_is_returned_and_available(self):
        runtime = self.make_runtime()

        self.assertIs(install_runtime(runtime), runtime)
        self.assertIs(get_runtime(), runtime)

    def test_reinstalling_same_runtime_identity_is_safe(self):
        runtime = self.make_runtime()
        install_runtime(runtime)

        self.assertIs(install_runtime(runtime), runtime)
        self.assertIs(get_runtime(), runtime)

    def test_conflicting_runtime_is_rejected_without_replacing_first(self):
        first = self.make_runtime()
        second = self.make_runtime()
        install_runtime(first)

        with self.assertRaisesRegex(
            RuntimeError,
            (
                r"^\[EasyUseAnima\] A different RuntimeServices instance "
                r"is already installed\.$"
            ),
        ):
            install_runtime(second)

        self.assertIs(get_runtime(), first)

    def test_bootstrap_installs_and_reuses_the_default_runtime(self):
        register_routes = Mock(return_value=True)
        initialize_wildcards = Mock(return_value=object())
        host = type("Host", (), {"MAX_RESOLUTION": "8192"})()
        load_comfy_nodes = Mock(return_value=host)

        with (
            patch.object(bootstrap, "_WILDCARDS_INITIALIZED", False),
            patch.object(
                bootstrap,
                "_load_runtime_config",
                wraps=bootstrap._load_runtime_config,
            ) as load_runtime_config,
        ):
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
                load_comfy_nodes=load_comfy_nodes,
            )
            first = get_runtime()
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
                load_comfy_nodes=load_comfy_nodes,
            )

        self.assertIs(first, bootstrap._DEFAULT_RUNTIME)
        self.assertIsInstance(first.comfy, DefaultComfyHostProvider)
        self.assertIsInstance(
            first.seed_reservations,
            InMemorySeedReservationService,
        )
        self.assertIs(first.config.package_root, storage_paths.PACKAGE_ROOT)
        self.assertIs(first.config.package_data_dir, storage_paths.PACKAGE_DATA_DIR)
        self.assertIs(first.config.user_data_dir, storage_paths.USER_DATA_DIR)
        self.assertIs(
            first.translation,
            translation_service._DEFAULT_TRANSLATION_SERVICE,
        )
        self.assertIs(
            first.translation.cache._time_func.__self__,
            first.clock,
        )
        self.assertIsInstance(
            first.autocomplete,
            autocomplete_service._AutocompleteService,
        )
        self.assertIs(
            first.autocomplete.snapshots,
            autocomplete_dataset._DEFAULT_AUTOCOMPLETE_SNAPSHOTS,
        )
        self.assertIs(
            first.autocomplete.index_store,
            autocomplete_index._DEFAULT_AUTOCOMPLETE_INDEX_STORE,
        )
        self.assertIs(
            first.wildcard_snapshots,
            wildcard_snapshot._DEFAULT_WILDCARD_SNAPSHOTS,
        )
        self.assertIs(
            first.aio_first_pass_cache,
            aio_first_pass_cache._DEFAULT_AIO_FIRST_PASS_CACHE,
        )
        with patch.object(bootstrap.time, "monotonic", return_value=12.5):
            self.assertEqual(first.clock.monotonic(), 12.5)
        self.assertEqual(first.comfy.max_resolution(), 8192)
        self.assertIs(get_runtime(), first)
        load_runtime_config.assert_called_once_with()
        load_comfy_nodes.assert_called_once_with()
        self.assertEqual(register_routes.call_count, 2)
        initialize_wildcards.assert_called_once_with()

    def test_bootstrap_rejects_conflicting_runtime_before_startup_callbacks(self):
        runtime = self.make_runtime()
        register_routes = Mock(return_value=True)
        initialize_wildcards = Mock(return_value=object())
        install_runtime(runtime)

        with (
            patch.object(bootstrap, "_WILDCARDS_INITIALIZED", False),
            self.assertRaisesRegex(
                RuntimeError,
                (
                    r"^\[EasyUseAnima\] A different RuntimeServices instance "
                    r"is already installed\.$"
                ),
            ),
        ):
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
            )

        self.assertIs(get_runtime(), runtime)
        register_routes.assert_not_called()
        initialize_wildcards.assert_not_called()

    def test_import_does_not_require_comfyui_host_modules(self):
        script = """
import builtins

real_import = builtins.__import__
forbidden = {"comfy", "folder_paths", "nodes", "server"}

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".", 1)[0] in forbidden:
        raise AssertionError(f"unexpected host import: {name}")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import

from easyuse_anima.infrastructure.comfy.provider import ComfyHostProvider
from easyuse_anima.infrastructure.comfy.provider import DefaultComfyHostProvider
from easyuse_anima.runtime import (
    Clock,
    RuntimeConfig,
    RuntimeResource,
    RuntimeServices,
    get_runtime,
    install_runtime,
)
from easyuse_anima.bootstrap import initialize
from easyuse_anima.seed.service import InMemorySeedReservationService
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
