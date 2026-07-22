from __future__ import annotations

import threading
import time
import unittest
from unittest.mock import Mock, patch

from easyuse_anima import bootstrap


class PythonBootstrapTests(unittest.TestCase):
    def setUp(self):
        state = patch.object(bootstrap, "_WILDCARDS_INITIALIZED", False)
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


if __name__ == "__main__":
    unittest.main()
