from __future__ import annotations

import threading
import time
import unittest
from unittest.mock import Mock, patch

from easyuse_anima import bootstrap, runtime as runtime_module
from easyuse_anima.translation import service as translation_service


class PythonBootstrapTests(unittest.TestCase):
    def setUp(self):
        patchers = (
            patch.object(bootstrap, "_WILDCARDS_INITIALIZED", False),
            patch.object(bootstrap, "_DEFAULT_RUNTIME", None),
            patch.object(bootstrap, "_TRANSLATION_ROUTE_EXECUTOR", None),
            patch.object(bootstrap, "_ATEXIT_REGISTERED", False),
            patch.object(bootstrap, "_SHUTDOWN", False),
            patch.object(runtime_module, "_RUNTIME_SERVICES", None),
            patch.object(bootstrap.atexit, "register"),
            patch.object(
                translation_service,
                "_DEFAULT_TRANSLATION_SERVICE",
                translation_service.PromptTranslationService(),
            ),
        )
        for state in patchers:
            state.start()
            self.addCleanup(state.stop)

    def test_repeated_initialize_keeps_routes_refreshable_and_wildcards_once(self):
        register_routes = Mock(return_value=True)
        initialize_wildcards = Mock(return_value=object())

        bootstrap.initialize(
            register_routes=register_routes,
            initialize_wildcards=initialize_wildcards,
        )
        bootstrap.initialize(
            register_routes=register_routes,
            initialize_wildcards=initialize_wildcards,
        )

        self.assertEqual(register_routes.call_count, 2)
        initialize_wildcards.assert_called_once_with()

    def test_wildcard_oserror_warns_and_retries_without_losing_route_refresh(self):
        error = OSError("blocked")
        register_routes = Mock(return_value=True)
        initialize_wildcards = Mock(side_effect=(error, object()))

        with patch.object(bootstrap._LOGGER, "warning") as warning:
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
            )
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
            )

        self.assertEqual(register_routes.call_count, 2)
        self.assertEqual(initialize_wildcards.call_count, 2)
        warning.assert_called_once_with(
            "EasyUse Anima wildcard folder could not be initialized: %s",
            error,
        )

    def test_route_false_is_nonterminal_and_refreshes_on_the_next_initialize(self):
        register_routes = Mock(side_effect=(False, True))
        initialize_wildcards = Mock(return_value=object())

        bootstrap.initialize(
            register_routes=register_routes,
            initialize_wildcards=initialize_wildcards,
        )
        first = runtime_module.get_runtime()
        bootstrap.initialize(
            register_routes=register_routes,
            initialize_wildcards=initialize_wildcards,
        )

        self.assertIs(runtime_module.get_runtime(), first)
        self.assertEqual(register_routes.call_count, 2)
        initialize_wildcards.assert_called_once_with()

    def test_route_failure_preserves_order_and_retries_all_startup_work(self):
        register_routes = Mock(side_effect=(RuntimeError("routes"), True))
        initialize_wildcards = Mock(return_value=object())

        with self.assertRaisesRegex(RuntimeError, "routes"):
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
            )
        initialize_wildcards.assert_not_called()

        bootstrap.initialize(
            register_routes=register_routes,
            initialize_wildcards=initialize_wildcards,
        )
        self.assertEqual(register_routes.call_count, 2)
        initialize_wildcards.assert_called_once_with()

    def test_unexpected_wildcard_error_propagates_and_retries(self):
        register_routes = Mock(return_value=True)
        initialize_wildcards = Mock(side_effect=(ValueError("wildcards"), object()))

        with self.assertRaisesRegex(ValueError, "wildcards"):
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
            )

        bootstrap.initialize(
            register_routes=register_routes,
            initialize_wildcards=initialize_wildcards,
        )
        self.assertEqual(register_routes.call_count, 2)
        self.assertEqual(initialize_wildcards.call_count, 2)

    def test_concurrent_initialize_serializes_wildcard_startup(self):
        register_routes = Mock(return_value=True)
        wildcard_calls = []

        def initialize_wildcards():
            wildcard_calls.append(threading.get_ident())
            time.sleep(0.01)

        threads = [
            threading.Thread(
                target=bootstrap.initialize,
                kwargs={
                    "register_routes": register_routes,
                    "initialize_wildcards": initialize_wildcards,
                },
            )
            for _index in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=1)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(register_routes.call_count, len(threads))
        self.assertEqual(len(wildcard_calls), 1)

    def test_initialize_registers_bootstrap_shutdown_once(self):
        register_routes = Mock(return_value=True)
        initialize_wildcards = Mock(return_value=object())

        bootstrap.initialize(
            register_routes=register_routes,
            initialize_wildcards=initialize_wildcards,
        )
        bootstrap.initialize(
            register_routes=register_routes,
            initialize_wildcards=initialize_wildcards,
        )

        bootstrap.atexit.register.assert_called_once_with(bootstrap.shutdown)

    def test_shutdown_is_idempotent_terminal_and_detaches_expected_runtime(self):
        register_routes = Mock(return_value=True)
        initialize_wildcards = Mock(return_value=object())
        previous_translation = translation_service._DEFAULT_TRANSLATION_SERVICE
        bootstrap.initialize(
            register_routes=register_routes,
            initialize_wildcards=initialize_wildcards,
        )
        runtime = runtime_module.get_runtime()

        bootstrap.shutdown()
        bootstrap.shutdown()

        self.assertIsNone(bootstrap._DEFAULT_RUNTIME)
        self.assertIs(
            translation_service._DEFAULT_TRANSLATION_SERVICE,
            previous_translation,
        )
        with self.assertRaisesRegex(RuntimeError, "has not been installed"):
            runtime_module.get_runtime()
        runtime.close()

        register_routes.reset_mock()
        initialize_wildcards.reset_mock()
        with self.assertRaisesRegex(
            RuntimeError,
            "RuntimeServices has already been shut down",
        ):
            bootstrap.initialize(
                register_routes=register_routes,
                initialize_wildcards=initialize_wildcards,
            )
        register_routes.assert_not_called()
        initialize_wildcards.assert_not_called()

    def test_shutdown_runs_the_composed_cleanup_order(self):
        calls = []

        class Resource:
            def __init__(self, name):
                self.name = name

            def shutdown(self):
                calls.append(self.name)

            def clear(self):
                calls.append(self.name)

            def close(self):
                calls.append(self.name)

        worker = Resource("translation-route-executor")
        aio_cache = Resource("aio-first-pass-cache")
        wildcard_cache = Resource("wildcard-snapshot-cache")
        autocomplete_index = Resource("autocomplete-index-store")
        autocomplete_snapshots = Resource("autocomplete-snapshot-store")
        translation = Resource("translation-service-cache")
        restore = translation_service._restore_default_translation_service

        def restore_facade(expected, replacement):
            calls.append("translation-default-facade")
            return restore(expected, replacement)

        with (
            patch.object(bootstrap, "_TRANSLATION_ROUTE_EXECUTOR", worker),
            patch.object(bootstrap, "_DEFAULT_AIO_FIRST_PASS_CACHE", aio_cache),
            patch.object(
                bootstrap,
                "_DEFAULT_WILDCARD_SNAPSHOTS",
                wildcard_cache,
            ),
            patch.object(
                bootstrap,
                "_DEFAULT_AUTOCOMPLETE_INDEX_STORE",
                autocomplete_index,
            ),
            patch.object(
                bootstrap,
                "_DEFAULT_AUTOCOMPLETE_SNAPSHOTS",
                autocomplete_snapshots,
            ),
            patch.object(
                bootstrap,
                "PromptTranslationService",
                return_value=translation,
            ),
            patch.object(
                bootstrap,
                "_restore_default_translation_service",
                side_effect=restore_facade,
            ),
        ):
            bootstrap.initialize(
                register_routes=Mock(return_value=True),
                initialize_wildcards=Mock(return_value=object()),
            )
            bootstrap.shutdown()

        self.assertEqual(
            calls,
            [
                "translation-route-executor",
                "aio-first-pass-cache",
                "wildcard-snapshot-cache",
                "autocomplete-index-store",
                "autocomplete-snapshot-store",
                "translation-default-facade",
                "translation-service-cache",
            ],
        )

    def test_route_exception_rolls_back_only_attempt_created_runtime(self):
        calls = []

        class Translation:
            def close(self):
                calls.append("translation-close")

        previous_translation = translation_service._DEFAULT_TRANSLATION_SERVICE
        with patch.object(
            bootstrap,
            "PromptTranslationService",
            return_value=Translation(),
        ):
            with self.assertRaisesRegex(RuntimeError, "routes"):
                bootstrap.initialize(
                    register_routes=Mock(side_effect=RuntimeError("routes")),
                    initialize_wildcards=Mock(return_value=object()),
                )

        self.assertEqual(calls, ["translation-close"])
        self.assertIsNone(bootstrap._DEFAULT_RUNTIME)
        self.assertIs(
            translation_service._DEFAULT_TRANSLATION_SERVICE,
            previous_translation,
        )
        with self.assertRaisesRegex(RuntimeError, "has not been installed"):
            runtime_module.get_runtime()

    def test_repeated_initialize_failure_restores_only_attempt_bound_facade(self):
        bootstrap.initialize(
            register_routes=Mock(return_value=True),
            initialize_wildcards=Mock(return_value=object()),
        )
        runtime = runtime_module.get_runtime()
        foreign_translation = translation_service.PromptTranslationService()
        translation_service._DEFAULT_TRANSLATION_SERVICE = foreign_translation

        with (
            patch.object(runtime.translation, "close") as close,
            self.assertRaisesRegex(RuntimeError, "routes"),
        ):
            bootstrap.initialize(
                register_routes=Mock(side_effect=RuntimeError("routes")),
                initialize_wildcards=Mock(return_value=object()),
            )

        self.assertIs(runtime_module.get_runtime(), runtime)
        self.assertIs(bootstrap._DEFAULT_RUNTIME, runtime)
        self.assertIs(
            translation_service._DEFAULT_TRANSLATION_SERVICE,
            foreign_translation,
        )
        close.assert_not_called()

    def test_startup_exception_survives_rollback_cleanup_failure(self):
        startup_error = ValueError("wildcards")

        class Translation:
            def close(self):
                raise RuntimeError("cleanup")

        with (
            patch.object(
                bootstrap,
                "PromptTranslationService",
                return_value=Translation(),
            ),
            patch.object(bootstrap._LOGGER, "exception") as cleanup_log,
        ):
            with self.assertRaisesRegex(ValueError, "wildcards") as raised:
                bootstrap.initialize(
                    register_routes=Mock(return_value=True),
                    initialize_wildcards=Mock(side_effect=startup_error),
                )

        self.assertIs(raised.exception, startup_error)
        cleanup_log.assert_called_once_with(
            "EasyUse Anima translation cleanup failed during startup rollback."
        )

    def test_shutdown_waits_for_in_progress_initialize(self):
        entered = threading.Event()
        release = threading.Event()
        errors = []

        def register_routes():
            entered.set()
            release.wait(timeout=1)
            return True

        def run_initialize():
            try:
                bootstrap.initialize(
                    register_routes=register_routes,
                    initialize_wildcards=Mock(return_value=object()),
                )
            except BaseException as exc:
                errors.append(exc)

        initialize_thread = threading.Thread(target=run_initialize)
        shutdown_thread = threading.Thread(target=bootstrap.shutdown)
        initialize_thread.start()
        self.assertTrue(entered.wait(timeout=1))
        shutdown_thread.start()
        time.sleep(0.01)

        self.assertTrue(shutdown_thread.is_alive())
        self.assertFalse(bootstrap._SHUTDOWN)
        release.set()
        initialize_thread.join(timeout=1)
        shutdown_thread.join(timeout=1)

        self.assertEqual(errors, [])
        self.assertFalse(initialize_thread.is_alive())
        self.assertFalse(shutdown_thread.is_alive())
        self.assertTrue(bootstrap._SHUTDOWN)


if __name__ == "__main__":
    unittest.main()
