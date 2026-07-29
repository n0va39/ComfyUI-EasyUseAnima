from __future__ import annotations

import asyncio
import importlib.util
import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "easyuse_anima_translation_api_test_package"
ROUTE = "/easyuse_anima/translate_prompt"


def _clear_package_modules():
    prefix = f"{PACKAGE_NAME}."
    for name in list(sys.modules):
        if name == PACKAGE_NAME or name.startswith(prefix):
            sys.modules.pop(name, None)


class RouteRegistry:
    def __init__(self):
        self.handlers = {}

    def get(self, path):
        def register(handler):
            self.handlers[path] = handler
            return handler

        return register

    def post(self, path):
        return self.get(path)


class JsonRequest:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload


def load_api_routes():
    _clear_package_modules()
    package = types.ModuleType(PACKAGE_NAME)
    package.__path__ = [str(ROOT)]
    sys.modules[PACKAGE_NAME] = package

    routes = RouteRegistry()
    fake_server = types.ModuleType("server")
    fake_server.PromptServer = type(
        "PromptServer",
        (),
        {"instance": types.SimpleNamespace(routes=routes)},
    )
    fake_aiohttp = types.ModuleType("aiohttp")
    fake_aiohttp.web = types.SimpleNamespace(
        json_response=lambda payload, status=200: {"payload": payload, "status": status},
    )

    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE_NAME}.api",
        ROOT / "api.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    missing = object()
    previous_modules = {
        name: sys.modules.get(name, missing)
        for name in ("server", "aiohttp")
    }
    sys.modules.update({"server": fake_server, "aiohttp": fake_aiohttp})
    try:
        spec.loader.exec_module(module)
        module.register_routes()
        translation_contracts = sys.modules[
            module.PromptTranslationError.__module__
        ]
        translation_service = sys.modules[
            module.translate_prompt_markers.__module__
        ]
    finally:
        for name, previous in previous_modules.items():
            if previous is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
    return module, routes, translation_contracts, translation_service


class PromptTranslationApiTests(unittest.TestCase):
    def load_routes(self):
        api, routes, translation, translation_service = load_api_routes()
        self.addCleanup(_clear_package_modules)
        self.addCleanup(api._PROMPT_TRANSLATION_WORKER.shutdown)
        return api, routes, translation, translation_service

    def test_route_handler_is_owned_by_the_canonical_factory(self):
        api, routes, _translation, _translation_service = self.load_routes()
        handler = routes.handlers[ROUTE]

        self.assertIs(api.translate_prompt_handler, handler)
        self.assertEqual(handler.__name__, "translate_prompt_handler")
        self.assertEqual(
            handler.__module__,
            f"{PACKAGE_NAME}.easyuse_anima.api.routes.translation",
        )
        self.assertTrue(handler._easyuse_anima_request_correlation)

    def test_route_runtime_helpers_are_owned_by_the_canonical_factory(self):
        api, _routes, _translation, _translation_service = self.load_routes()
        cases = (
            ("_translate_prompt_sync", 1),
            ("_translate_prompt_for_route", 1),
            ("_prompt_translation_error_response", 1),
        )

        for name, argcount in cases:
            with self.subTest(name=name):
                helper = getattr(api, name)
                self.assertEqual(helper.__name__, name)
                self.assertEqual(
                    helper.__module__,
                    f"{PACKAGE_NAME}.easyuse_anima.api.routes.translation",
                )
                self.assertEqual(helper.__code__.co_argcount, argcount)

        owner = sys.modules[api._translate_prompt_sync.__module__]
        self.assertIs(
            api.PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS,
            owner.PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS,
        )
        self.assertEqual(api.PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS, 15.0)
        self.assertEqual(owner.__all__, ("build_translate_prompt_handler",))
        self.assertFalse(hasattr(owner, "_PROMPT_TRANSLATION_WORKER"))

    def test_repeated_registration_keeps_one_bootstrap_composed_runtime(self):
        api, routes, _translation, _translation_service = self.load_routes()
        runtime = (
            api._PROMPT_TRANSLATION_WORKER,
            api._translate_prompt_sync,
            api._translate_prompt_for_route,
            api._prompt_translation_error_response,
        )

        api.register_routes()

        self.assertEqual(
            (
                api._PROMPT_TRANSLATION_WORKER,
                api._translate_prompt_sync,
                api._translate_prompt_for_route,
                api._prompt_translation_error_response,
            ),
            runtime,
        )
        self.assertIs(routes.handlers[ROUTE], api.translate_prompt_handler)

    def test_runtime_builder_constructs_one_worker_without_lifecycle_side_effect(self):
        api, _routes, translation, _translation_service = self.load_routes()
        owner = sys.modules[api._translate_prompt_sync.__module__]
        created = []

        class FakeExecutor:
            def __init__(
                self,
                *,
                busy_error_type,
                cancelled_error_type,
                timeout_error_type,
            ):
                created.append(
                    (
                        busy_error_type,
                        cancelled_error_type,
                        timeout_error_type,
                    )
                )

            def shutdown(self):
                return None

        runtime = owner.build_translation_runtime(
            executor_type=FakeExecutor,
            busy_error_type=api.TranslationBusyError,
            cancelled_error_type=api.TranslationCancelledError,
            timeout_error_type=api.TranslationTimeoutError,
            translate_prompt_markers=lambda text, settings: text,
            resolve_prompt_translation_settings=lambda: object(),
            get_worker=lambda: runtime[0],
            get_translate_prompt_sync=lambda: runtime[1],
            get_timeout_seconds=lambda: 15.0,
            translation_error_types={
                "marker_count": translation.TranslationMarkerCountError,
                "marker_size": translation.TranslationMarkerSizeError,
                "total_size": translation.TranslationTotalSizeError,
                "limit": translation.PromptTranslationLimitError,
                "provider_unavailable": (
                    translation.TranslationProviderUnavailableError
                ),
                "timeout": translation.TranslationTimeoutError,
                "cancelled": translation.TranslationCancelledError,
                "busy": translation.TranslationBusyError,
                "upstream": translation.TranslationUpstreamError,
                "base": translation.PromptTranslationError,
            },
            error_response=lambda *args: args,
        )

        self.assertEqual(
            created,
            [
                (
                    api.TranslationBusyError,
                    api.TranslationCancelledError,
                    api.TranslationTimeoutError,
                )
            ],
        )
        self.assertFalse(hasattr(owner, "_PROMPT_TRANSLATION_WORKER"))

    def test_runtime_helpers_keep_dynamic_application_dependencies(self):
        api, _routes, _translation, _translation_service = self.load_routes()
        calls = []
        settings = object()

        def resolve_settings():
            calls.append(("settings",))
            return settings

        def translate(text, resolved_settings):
            calls.append(("translate", text, resolved_settings))
            return "translated"

        with (
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "resolve_prompt_translation_settings",
                side_effect=resolve_settings,
            ),
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "translate_prompt_markers",
                side_effect=translate,
            ),
        ):
            translated = api._translate_prompt_sync("%{text}")

        self.assertEqual(translated, "translated")
        self.assertEqual(
            calls,
            [
                ("settings",),
                ("translate", "%{text}", settings),
            ],
        )

        calls.clear()
        async def execute(function, text, *, timeout_seconds):
            calls.append(("execute", function, text, timeout_seconds))
            return "async-translated"

        with (
            patch.object(
                api._PROMPT_TRANSLATION_WORKER,
                "execute",
                side_effect=execute,
            ),
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "route_timeout_seconds",
                0.25,
            ),
        ):
            translated = asyncio.run(api._translate_prompt_for_route("%{async}"))

        self.assertEqual(translated, "async-translated")
        self.assertEqual(
            calls,
            [("execute", api._translate_prompt_sync, "%{async}", 0.25)],
        )

    def test_translation_error_boundary_uses_static_policy_and_semantic_messages(self):
        api, _routes, translation, _translation_service = self.load_routes()

        class DerivedMarkerCountError(translation.TranslationMarkerCountError):
            pass

        class RootDerivedTranslationError(translation.PromptTranslationError):
            status = 502
            code = "translation_upstream_error"

        cases = (
            (
                translation.PromptTranslationError(),
                500,
                "translation_error",
                "Prompt translation failed.",
            ),
            (
                translation.PromptTranslationLimitError(),
                413,
                "translation_error",
                "Prompt translation failed.",
            ),
            (
                translation.TranslationMarkerCountError(),
                413,
                "translation_marker_count_exceeded",
                "Prompt translation failed.",
            ),
            (
                translation.TranslationMarkerSizeError(),
                413,
                "translation_marker_too_long",
                "Prompt translation failed.",
            ),
            (
                translation.TranslationTotalSizeError(),
                413,
                "translation_marker_characters_exceeded",
                "Prompt translation failed.",
            ),
            (
                translation.TranslationProviderUnavailableError(),
                503,
                "translation_provider_unavailable",
                "The selected translation provider is unavailable.",
            ),
            (
                translation.TranslationTimeoutError(),
                504,
                "translation_timeout",
                "The translation provider timed out.",
            ),
            (
                translation.TranslationCancelledError(),
                499,
                "translation_cancelled",
                "The translation request was cancelled.",
            ),
            (
                translation.TranslationBusyError(),
                503,
                "translation_busy",
                "A prompt translation request is already in progress.",
            ),
            (
                translation.TranslationUpstreamError(),
                502,
                "translation_upstream_error",
                "The translation provider request failed.",
            ),
            (
                translation.TranslationMarkerCountError("Custom marker limit"),
                413,
                "translation_marker_count_exceeded",
                "Custom marker limit",
            ),
            (
                DerivedMarkerCountError("Derived marker limit"),
                413,
                "translation_marker_count_exceeded",
                "Derived marker limit",
            ),
        )

        for error, status, code, message in cases:
            error.status = 599
            error.code = "tampered_code"
            error.message = "Tampered message"
            expected_response = object()
            with self.subTest(error=type(error).__name__, message=message), patch.object(
                api._APPLICATION_DEPENDENCIES.request,
                "error_response",
                return_value=expected_response,
            ) as error_response:
                response = api._prompt_translation_error_response(error)

            self.assertIs(response, expected_response)
            error_response.assert_called_once_with(status, code, message)

        compatibility_error = RootDerivedTranslationError(
            "Derived translation compatibility failure."
        )
        expected_response = object()
        with patch.object(
            api._APPLICATION_DEPENDENCIES.request,
            "error_response",
            return_value=expected_response,
        ) as error_response:
            response = api._prompt_translation_error_response(compatibility_error)

        self.assertIs(response, expected_response)
        error_response.assert_called_once_with(
            502,
            "translation_upstream_error",
            "Derived translation compatibility failure.",
        )

        unexpected = RuntimeError("unexpected")
        with self.assertRaises(RuntimeError) as raised:
            api._prompt_translation_error_response(unexpected)
        self.assertIs(raised.exception, unexpected)

    def test_route_executor_is_owned_by_the_canonical_module(self):
        api, _routes, _translation, _translation_service = self.load_routes()
        executor = api._PROMPT_TRANSLATION_WORKER
        executor_module = sys.modules[type(executor).__module__]

        self.assertEqual(
            type(executor).__module__,
            f"{PACKAGE_NAME}.easyuse_anima.api.routes.translation_execution",
        )
        self.assertIs(
            type(executor),
            executor_module.PromptTranslationRouteExecutor,
        )
        self.assertEqual(
            executor_module.__all__,
            ("PromptTranslationRouteExecutor",),
        )
        self.assertFalse(hasattr(executor_module, "_PROMPT_TRANSLATION_WORKER"))

    def test_route_runs_sync_translation_off_event_loop(self):
        api, routes, translation, _translation_service = self.load_routes()
        handler = routes.handlers[ROUTE]
        worker_started = threading.Event()

        def slow_translation(text, settings):
            worker_started.set()
            time.sleep(0.05)
            return "translated"

        async def exercise():
            heartbeat = 0
            task = asyncio.create_task(handler(JsonRequest({"text": "%{text}"})))
            while not worker_started.is_set():
                await asyncio.sleep(0)
            while not task.done():
                heartbeat += 1
                await asyncio.sleep(0.002)
            return await task, heartbeat

        with (
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "resolve_prompt_translation_settings",
                return_value=translation.PromptTranslationSettings(provider="google"),
            ),
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "translate_prompt_markers",
                side_effect=slow_translation,
            ),
        ):
            response, heartbeat = asyncio.run(exercise())

        self.assertEqual(response, {"payload": {"status": "ok", "text": "translated"}, "status": 200})
        self.assertGreaterEqual(heartbeat, 3)

    def test_timeout_keeps_bounded_admission_without_using_shared_executor(self):
        api, routes, translation, _translation_service = self.load_routes()
        handler = routes.handlers[ROUTE]
        worker_started = threading.Event()
        release_worker = threading.Event()

        def blocking_translation(*_args):
            worker_started.set()
            release_worker.wait(timeout=1)
            return "late"

        async def exercise():
            heartbeat = 0
            stop_heartbeat = False

            async def beat():
                nonlocal heartbeat
                while not stop_heartbeat:
                    heartbeat += 1
                    await asyncio.sleep(0.001)

            heartbeat_task = asyncio.create_task(beat())
            try:
                first_response = await handler(JsonRequest({"text": "%{first}"}))
                self.assertTrue(worker_started.is_set())
                self.assertTrue(api._PROMPT_TRANSLATION_WORKER.has_in_flight)
                repeated_responses = await asyncio.gather(
                    *(
                        handler(JsonRequest({"text": f"%{{later-{index}}}"}))
                        for index in range(20)
                    )
                )
            finally:
                release_worker.set()
                deadline = asyncio.get_running_loop().time() + 1
                while (
                    api._PROMPT_TRANSLATION_WORKER.has_in_flight
                    and asyncio.get_running_loop().time() < deadline
                ):
                    await asyncio.sleep(0.001)
                stop_heartbeat = True
                await heartbeat_task
            return first_response, repeated_responses, heartbeat

        with (
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "resolve_prompt_translation_settings",
                return_value=translation.PromptTranslationSettings(provider="google"),
            ),
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "route_timeout_seconds",
                0.01,
            ),
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "translate_prompt_markers",
                side_effect=blocking_translation,
            ) as worker,
            patch.object(api.asyncio, "to_thread") as shared_executor_submit,
        ):
            response, repeated_responses, heartbeat = asyncio.run(exercise())

        self.assertEqual(
            response,
            {
                "payload": {
                    "status": "error",
                    "code": "translation_timeout",
                    "message": "The translation provider timed out.",
                },
                "status": 504,
            },
        )
        self.assertEqual(worker.call_count, 1)
        shared_executor_submit.assert_not_called()
        self.assertGreaterEqual(heartbeat, 3)
        self.assertFalse(api._PROMPT_TRANSLATION_WORKER.has_in_flight)
        self.assertEqual(
            repeated_responses,
            [
                {
                    "payload": {
                        "status": "error",
                        "code": "translation_busy",
                        "message": "A prompt translation request is already in progress.",
                    },
                    "status": 503,
                }
            ]
            * 20,
        )

    def test_route_cancellation_stops_waiting_with_stable_499_json(self):
        api, routes, translation, _translation_service = self.load_routes()
        handler = routes.handlers[ROUTE]
        worker_started = threading.Event()
        release_worker = threading.Event()

        def blocking_translation(*_args):
            worker_started.set()
            release_worker.wait(timeout=1)
            return "late"

        async def exercise():
            task = asyncio.create_task(handler(JsonRequest({"text": "%{text}"})))
            while not worker_started.is_set():
                await asyncio.sleep(0)
            task.cancel()
            try:
                response = await task
                self.assertTrue(api._PROMPT_TRANSLATION_WORKER.has_in_flight)
                busy_response = await handler(JsonRequest({"text": "%{later}"}))
            finally:
                release_worker.set()
                deadline = asyncio.get_running_loop().time() + 1
                while (
                    api._PROMPT_TRANSLATION_WORKER.has_in_flight
                    and asyncio.get_running_loop().time() < deadline
                ):
                    await asyncio.sleep(0.001)
            return response, busy_response

        with (
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "resolve_prompt_translation_settings",
                return_value=translation.PromptTranslationSettings(provider="google"),
            ),
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "translate_prompt_markers",
                side_effect=blocking_translation,
            ),
        ):
            response, busy_response = asyncio.run(exercise())

        self.assertEqual(
            response,
            {
                "payload": {
                    "status": "error",
                    "code": "translation_cancelled",
                    "message": "The translation request was cancelled.",
                },
                "status": 499,
            },
        )
        self.assertEqual(busy_response["status"], 503)
        self.assertEqual(busy_response["payload"]["code"], "translation_busy")
        self.assertFalse(api._PROMPT_TRANSLATION_WORKER.has_in_flight)

    def test_route_maps_only_prompt_translation_errors(self):
        api, routes, translation, _translation_service = self.load_routes()
        handler = routes.handlers[ROUTE]
        settings = translation.PromptTranslationSettings(provider="google")
        cases = (
            (
                translation.TranslationProviderUnavailableError(),
                503,
                "translation_provider_unavailable",
                "The selected translation provider is unavailable.",
            ),
            (
                translation.TranslationUpstreamError(),
                502,
                "translation_upstream_error",
                "The translation provider request failed.",
            ),
        )
        for error, status, code, message in cases:
            with self.subTest(code=code):
                with (
                    patch.object(
                        api._APPLICATION_DEPENDENCIES.translation,
                        "resolve_prompt_translation_settings",
                        return_value=settings,
                    ),
                    patch.object(
                        api._APPLICATION_DEPENDENCIES.translation,
                        "translate_prompt_markers",
                        side_effect=error,
                    ),
                ):
                    response = asyncio.run(handler(JsonRequest({"text": "%{text}"})))

                self.assertEqual(
                    response,
                    {
                        "payload": {
                            "status": "error",
                            "code": code,
                            "message": message,
                        },
                        "status": status,
                    },
                )

    def test_route_observes_translation_error_type_and_response_leaves_at_call_time(self):
        api, routes, _translation, _translation_service = self.load_routes()
        handler = routes.handlers[ROUTE]

        class InjectedTranslationError(Exception):
            pass

        error = InjectedTranslationError("injected")
        expected_response = object()
        with (
            patch.object(
                api._PROMPT_TRANSLATION_WORKER,
                "execute",
                side_effect=error,
            ),
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "prompt_translation_error_type",
                InjectedTranslationError,
            ),
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "prompt_translation_error_response",
                return_value=expected_response,
            ) as error_response,
        ):
            response = asyncio.run(handler(JsonRequest({"text": "%{text}"})))

        self.assertIs(response, expected_response)
        error_response.assert_called_once_with(error)

    def test_route_does_not_mask_settings_or_payload_programming_errors_as_upstream(self):
        api, routes, _translation, _translation_service = self.load_routes()
        handler = routes.handlers[ROUTE]

        for error in (
            RuntimeError("settings storage failed"),
            TimeoutError("settings storage timeout"),
        ):
            with self.subTest(error=type(error).__name__):
                with (
                    patch.object(
                        api._APPLICATION_DEPENDENCIES.translation,
                        "resolve_prompt_translation_settings",
                        side_effect=error,
                    ),
                    patch.object(api._LOGGER, "error") as log_error,
                ):
                    response = asyncio.run(handler(JsonRequest({"text": "%{text}"})))
                self.assertEqual(response["status"], 500)
                self.assertEqual(response["payload"]["code"], "internal_error")
                self.assertNotEqual(response["payload"]["code"], "translation_upstream_error")
                log_error.assert_called_once()

        response = asyncio.run(handler(JsonRequest([])))
        self.assertEqual(response["status"], 400)
        self.assertEqual(response["payload"]["code"], "json_object_required")

    def test_all_marker_budgets_return_413_before_provider_resolution(self):
        api, routes, translation, translation_service = self.load_routes()
        handler = routes.handlers[ROUTE]
        settings = translation.PromptTranslationSettings(provider="google")
        cases = (
            (
                "%{a}" * (translation.MAX_PROMPT_TRANSLATION_MARKERS + 1),
                "translation_marker_count_exceeded",
            ),
            (
                "%{" + "a" * (translation.MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS + 1) + "}",
                "translation_marker_too_long",
            ),
            (
                "".join(
                    "%{" + "a" * 1000 + "}"
                    for _index in range(
                        translation.MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS // 1000 + 1
                    )
                ),
                "translation_marker_characters_exceeded",
            ),
        )

        with (
            patch.object(
                api._APPLICATION_DEPENDENCIES.translation,
                "resolve_prompt_translation_settings",
                return_value=settings,
            ),
            patch.object(
                translation_service,
                "get_translation_provider",
            ) as provider_factory,
        ):
            for text, code in cases:
                with self.subTest(code=code):
                    response = asyncio.run(handler(JsonRequest({"text": text})))
                    self.assertEqual(response["status"], 413)
                    self.assertEqual(response["payload"]["status"], "error")
                    self.assertEqual(response["payload"]["code"], code)
            provider_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
