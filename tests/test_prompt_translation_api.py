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
    def test_route_runs_sync_translation_off_event_loop(self):
        api, routes, translation = load_api_routes()
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

    def test_route_timeout_has_stable_504_json(self):
        api, routes, translation = load_api_routes()
        handler = routes.handlers[ROUTE]

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
                side_effect=lambda *_args: (time.sleep(0.05), "late")[1],
            ),
        ):
            response = asyncio.run(handler(JsonRequest({"text": "%{text}"})))

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

    def test_route_cancellation_stops_waiting_with_stable_499_json(self):
        api, routes, translation = load_api_routes()
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
            response = await task
            release_worker.set()
            return response

        with (
            patch.object(
                api,
                "resolve_prompt_translation_settings",
                return_value=translation.PromptTranslationSettings(provider="google"),
            ),
            patch.object(api, "translate_prompt_markers", side_effect=blocking_translation),
        ):
            response = asyncio.run(exercise())

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

    def test_route_maps_unavailable_and_arbitrary_upstream_failures(self):
        api, routes, translation = load_api_routes()
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
                ValueError("provider internals must not leak"),
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
                    patch.object(api, "translate_prompt_markers", side_effect=error),
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

    def test_all_marker_budgets_return_413_before_provider_resolution(self):
        api, routes, translation = load_api_routes()
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
