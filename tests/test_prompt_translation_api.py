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
    with patch.dict(sys.modules, {"server": fake_server, "aiohttp": fake_aiohttp}):
        spec.loader.exec_module(module)
        translation = sys.modules[module.translate_prompt_markers.__module__]
    return module, routes, translation


class PromptTranslationApiTests(unittest.TestCase):
    def load_routes(self):
        api, routes, translation = load_api_routes()
        self.addCleanup(api._PROMPT_TRANSLATION_WORKER.shutdown)
        return api, routes, translation

    def test_route_runs_sync_translation_off_event_loop(self):
        api, routes, translation = self.load_routes()
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
                api,
                "resolve_prompt_translation_settings",
                return_value=translation.PromptTranslationSettings(provider="google"),
            ),
            patch.object(api, "translate_prompt_markers", side_effect=slow_translation),
        ):
            response, heartbeat = asyncio.run(exercise())

        self.assertEqual(response, {"payload": {"status": "ok", "text": "translated"}, "status": 200})
        self.assertGreaterEqual(heartbeat, 3)

    def test_timeout_keeps_bounded_admission_without_using_shared_executor(self):
        api, routes, translation = self.load_routes()
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
                api,
                "resolve_prompt_translation_settings",
                return_value=translation.PromptTranslationSettings(provider="google"),
            ),
            patch.object(api, "PROMPT_TRANSLATION_ROUTE_TIMEOUT_SECONDS", 0.01),
            patch.object(
                api,
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
        api, routes, translation = self.load_routes()
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
                api,
                "resolve_prompt_translation_settings",
                return_value=translation.PromptTranslationSettings(provider="google"),
            ),
            patch.object(api, "translate_prompt_markers", side_effect=blocking_translation),
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
        api, routes, translation = self.load_routes()
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
                        api,
                        "resolve_prompt_translation_settings",
                        return_value=settings,
                    ),
                    patch.object(
                        api,
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

    def test_route_does_not_mask_settings_or_payload_programming_errors_as_upstream(self):
        api, routes, _translation = self.load_routes()
        handler = routes.handlers[ROUTE]

        for error in (
            RuntimeError("settings storage failed"),
            TimeoutError("settings storage timeout"),
        ):
            with self.subTest(error=type(error).__name__):
                with (
                    patch.object(
                        api,
                        "resolve_prompt_translation_settings",
                        side_effect=error,
                    ),
                    patch.object(api._LOGGER, "exception") as log_exception,
                ):
                    response = asyncio.run(handler(JsonRequest({"text": "%{text}"})))
                self.assertEqual(response["status"], 500)
                self.assertEqual(response["payload"]["code"], "internal_error")
                self.assertNotEqual(response["payload"]["code"], "translation_upstream_error")
                log_exception.assert_called_once()

        response = asyncio.run(handler(JsonRequest([])))
        self.assertEqual(response["status"], 400)
        self.assertEqual(response["payload"]["code"], "json_object_required")

    def test_all_marker_budgets_return_413_before_provider_resolution(self):
        api, routes, translation = self.load_routes()
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
            patch.object(api, "resolve_prompt_translation_settings", return_value=settings),
            patch.object(translation, "get_translation_provider") as provider_factory,
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
