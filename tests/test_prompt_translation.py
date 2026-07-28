from __future__ import annotations

import builtins
import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch

import prompt_translation as root_translation
from easyuse_anima.translation import contracts, markers, service
from easyuse_anima.translation.contracts import (
    PROMPT_TRANSLATION_PROVIDER_GOOGLE,
    PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS,
    PromptTranslationSettings,
    TranslationMarkerCountError,
    TranslationMarkerSizeError,
    TranslationProviderUnavailableError,
    TranslationTimeoutError,
    TranslationTotalSizeError,
    TranslationUpstreamError,
)
from easyuse_anima.translation.providers import google as google_provider
from easyuse_anima.translation.providers.google import (
    GoogleTranslationProvider,
)
from easyuse_anima.translation.provider_registry import (
    _TranslationProviderRegistry,
)
from easyuse_anima.translation.service import (
    BoundedTranslationCache,
    PromptTranslationService,
    get_translation_provider,
)
from tests.runtime_test_support import isolated_translation_facade


GOOGLE_SETTINGS = PromptTranslationSettings(
    provider=PROMPT_TRANSLATION_PROVIDER_GOOGLE,
    source="ko",
    target="en",
)


class PromptTranslationCompatibilityTests(unittest.TestCase):
    def test_root_shim_exports_identical_canonical_objects(self):
        canonical = {
            name: getattr(module, name)
            for module in (
                contracts,
                markers,
                google_provider,
                service,
            )
            for name in module.__all__
        }

        self.assertEqual(set(root_translation.__all__), set(canonical))
        self.assertEqual(
            len(root_translation.__all__),
            len(set(root_translation.__all__)),
        )
        for name, value in canonical.items():
            with self.subTest(name=name):
                self.assertIs(getattr(root_translation, name), value)


class PromptTranslationServiceTests(unittest.TestCase):
    def test_repeated_identical_markers_call_provider_once_and_replace_every_position(self):
        service = PromptTranslationService(
            cache=BoundedTranslationCache(max_entries=8, ttl_seconds=60)
        )

        with patch(
            "easyuse_anima.translation.service.google_translate_text",
            return_value="girl with red hair",
        ) as provider:
            translated = service.translate_prompt(
                "%{빨간 머리의 소녀}, %{빨간 머리의 소녀}, %{ 빨간 머리의 소녀 }",
                GOOGLE_SETTINGS,
            )

        self.assertEqual(
            translated,
            "girl with red hair, girl with red hair, girl with red hair",
        )
        provider.assert_called_once_with("빨간 머리의 소녀", "ko", "en")

    def test_off_mode_preserves_unwrap_and_literal_marker_without_import_or_provider(self):
        service = PromptTranslationService()
        real_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name == "googletrans" or name.startswith("googletrans."):
                self.fail("off mode must not import googletrans")
            return real_import(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=guarded_import),
            patch(
                "easyuse_anima.translation.service.get_translation_provider"
            ) as provider_factory,
        ):
            translated = service.translate_prompt(
                r"1girl, %{검은 드레스}, \%{literal}",
                PromptTranslationSettings(),
            )

        self.assertEqual(translated, r"1girl, 검은 드레스, \%{literal}")
        provider_factory.assert_not_called()

    def test_google_provider_lazily_creates_and_reuses_one_client(self):
        factory_calls = []
        translate_calls = []

        class Translator:
            def translate(self, text, *, src, dest):
                translate_calls.append((text, src, dest))
                return SimpleNamespace(text=f"{text}:{dest}")

        def factory():
            factory_calls.append(True)
            return Translator()

        provider = GoogleTranslationProvider(translator_factory=factory)
        self.assertEqual(factory_calls, [])

        self.assertEqual(provider.translate("하나", "ko", "en"), "하나:en")
        self.assertEqual(provider.translate("둘", "ko", "ja"), "둘:ja")

        self.assertEqual(len(factory_calls), 1)
        self.assertEqual(
            translate_calls,
            [("하나", "ko", "en"), ("둘", "ko", "ja")],
        )

    def test_google_provider_passes_timeout_to_real_client_constructor(self):
        received_timeouts = []

        class Translator:
            def __init__(self, *, timeout):
                received_timeouts.append(timeout)

            def translate(self, text, *, src, dest):
                return SimpleNamespace(text=f"{src}:{dest}:{text}")

        fake_googletrans = SimpleNamespace(Translator=Translator)
        with patch.dict(sys.modules, {"googletrans": fake_googletrans}):
            provider = GoogleTranslationProvider(timeout_seconds=2.5)
            result = provider.translate("text", "auto", "en")

        self.assertEqual(result, "auto:en:text")
        self.assertEqual(received_timeouts, [2.5])
        self.assertGreater(PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS, 0)

    def test_provider_factory_reuses_one_provider_instance(self):
        provider = GoogleTranslationProvider(translator_factory=lambda: object())
        factory_calls = []

        def factory():
            factory_calls.append(True)
            return provider

        registry = _TranslationProviderRegistry(
            {PROMPT_TRANSLATION_PROVIDER_GOOGLE: factory}
        )
        first = registry.get(PROMPT_TRANSLATION_PROVIDER_GOOGLE)
        second = registry.get(PROMPT_TRANSLATION_PROVIDER_GOOGLE)

        self.assertIs(first, provider)
        self.assertIs(second, provider)
        self.assertEqual(len(factory_calls), 1)

    def test_provider_registry_constructs_once_under_concurrency(self):
        provider = GoogleTranslationProvider(translator_factory=lambda: object())
        factory_calls = []

        def factory():
            factory_calls.append(True)
            return provider

        registry = _TranslationProviderRegistry(
            {PROMPT_TRANSLATION_PROVIDER_GOOGLE: factory}
        )
        with ThreadPoolExecutor(max_workers=8) as executor:
            instances = list(
                executor.map(
                    registry.get,
                    [PROMPT_TRANSLATION_PROVIDER_GOOGLE] * 16,
                )
            )

        self.assertTrue(all(instance is provider for instance in instances))
        self.assertEqual(len(factory_calls), 1)

    def test_provider_registry_preserves_factory_error_policy(self):
        timeout = TranslationTimeoutError()

        def timeout_factory():
            raise timeout

        def broken_factory():
            raise ValueError("broken provider")

        with self.assertRaises(TranslationProviderUnavailableError):
            _TranslationProviderRegistry({}).get("missing")
        with self.assertRaises(TranslationTimeoutError) as raised:
            _TranslationProviderRegistry(
                {PROMPT_TRANSLATION_PROVIDER_GOOGLE: timeout_factory}
            ).get(PROMPT_TRANSLATION_PROVIDER_GOOGLE)
        self.assertIs(raised.exception, timeout)

        with self.assertRaises(TranslationProviderUnavailableError) as raised:
            _TranslationProviderRegistry(
                {PROMPT_TRANSLATION_PROVIDER_GOOGLE: broken_factory}
            ).get(PROMPT_TRANSLATION_PROVIDER_GOOGLE)
        self.assertIsInstance(raised.exception.__cause__, ValueError)

    def test_provider_facade_resolves_current_default_registry(self):
        provider = GoogleTranslationProvider(translator_factory=lambda: object())

        class Registry:
            def __init__(self):
                self.calls = []

            def get(self, name):
                self.calls.append(name)
                return provider

        registry = Registry()
        with patch.object(
            service,
            "_DEFAULT_TRANSLATION_PROVIDER_REGISTRY",
            registry,
        ):
            resolved = get_translation_provider(" GOOGLE ")

        self.assertIs(resolved, provider)
        self.assertEqual(registry.calls, [" GOOGLE "])

    def test_cache_hit_ttl_expiry_and_lru_bound_are_deterministic(self):
        now = [0.0]
        lru_cache = BoundedTranslationCache(
            max_entries=2,
            ttl_seconds=10,
            time_func=lambda: now[0],
        )
        lru_service = PromptTranslationService(cache=lru_cache)

        with patch(
            "easyuse_anima.translation.service.google_translate_text",
            side_effect=lambda text, source, target: text.upper(),
        ) as provider:
            self.assertEqual(lru_service.translate_prompt("%{a}", GOOGLE_SETTINGS), "A")
            self.assertEqual(lru_service.translate_prompt("%{b}", GOOGLE_SETTINGS), "B")
            self.assertEqual(lru_service.translate_prompt("%{a}", GOOGLE_SETTINGS), "A")
            self.assertEqual(lru_service.translate_prompt("%{c}", GOOGLE_SETTINGS), "C")
            self.assertEqual(len(lru_cache), 2)
            self.assertEqual(lru_service.translate_prompt("%{b}", GOOGLE_SETTINGS), "B")
            self.assertEqual(provider.call_count, 4)

        ttl_cache = BoundedTranslationCache(
            max_entries=2,
            ttl_seconds=5,
            time_func=lambda: now[0],
        )
        ttl_service = PromptTranslationService(cache=ttl_cache)
        now[0] = 0.0
        with patch(
            "easyuse_anima.translation.service.google_translate_text",
            return_value="cached",
        ) as provider:
            ttl_service.translate_prompt("%{ttl}", GOOGLE_SETTINGS)
            now[0] = 4.0
            ttl_service.translate_prompt("%{ttl}", GOOGLE_SETTINGS)
            now[0] = 5.0
            ttl_service.translate_prompt("%{ttl}", GOOGLE_SETTINGS)
            self.assertEqual(provider.call_count, 2)

    def test_cache_key_partitions_source_target_and_text(self):
        service = PromptTranslationService(
            cache=BoundedTranslationCache(max_entries=8, ttl_seconds=60)
        )
        settings = (
            GOOGLE_SETTINGS,
            PromptTranslationSettings(provider="google", source="auto", target="en"),
            PromptTranslationSettings(provider="google", source="ko", target="ja"),
        )

        with patch(
            "easyuse_anima.translation.service.google_translate_text",
            side_effect=lambda text, source, target: f"{source}:{target}:{text}",
        ) as provider:
            for item in settings:
                service.translate_prompt("%{same}", item)
            service.translate_prompt("%{different}", GOOGLE_SETTINGS)
            service.translate_prompt("%{same}", GOOGLE_SETTINGS)

        self.assertEqual(provider.call_count, 4)

    def test_service_close_clears_cache_and_is_idempotent(self):
        cache = BoundedTranslationCache(max_entries=8, ttl_seconds=60)
        translation = PromptTranslationService(cache=cache)

        with patch(
            "easyuse_anima.translation.service.google_translate_text",
            return_value="cached",
        ) as provider:
            translation.translate_prompt("%{same}", GOOGLE_SETTINGS)
            translation.translate_prompt("%{same}", GOOGLE_SETTINGS)
            self.assertEqual(len(cache), 1)
            translation.close()
            translation.close()
            self.assertEqual(len(cache), 0)
            translation.translate_prompt("%{same}", GOOGLE_SETTINGS)

        self.assertEqual(provider.call_count, 2)

    def test_translation_facade_resolves_current_default_service(self):
        current = SimpleNamespace(
            translate_prompt=lambda text, settings=None: (
                text,
                settings,
            )
        )
        with isolated_translation_facade(
            service,
            current,
        ):
            resolved = service.translate_prompt_markers(
                "%{value}",
                GOOGLE_SETTINGS,
            )

        self.assertEqual(resolved, ("%{value}", GOOGLE_SETTINGS))

    def test_cache_and_request_dedup_are_thread_safe(self):
        service = PromptTranslationService(
            cache=BoundedTranslationCache(max_entries=8, ttl_seconds=60)
        )

        def translate(text, source, target):
            time.sleep(0.01)
            return "shared"

        with patch(
            "easyuse_anima.translation.service.google_translate_text",
            side_effect=translate,
        ) as provider:
            with ThreadPoolExecutor(max_workers=8) as executor:
                results = list(
                    executor.map(
                        lambda _index: service.translate_prompt("%{same}", GOOGLE_SETTINGS),
                        range(16),
                    )
                )

        self.assertEqual(results, ["shared"] * 16)
        provider.assert_called_once_with("same", "ko", "en")

    def test_different_cache_keys_do_not_share_a_service_wide_cache_lock(self):
        service = PromptTranslationService(
            cache=BoundedTranslationCache(max_entries=8, ttl_seconds=60)
        )
        both_providers_started = threading.Barrier(2)

        def translate(text, source, target):
            both_providers_started.wait(timeout=1)
            return text.upper()

        with patch(
            "easyuse_anima.translation.service.google_translate_text",
            side_effect=translate,
        ):
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(
                    executor.map(
                        lambda text: service.translate_prompt(f"%{{{text}}}", GOOGLE_SETTINGS),
                        ("first", "second"),
                    )
                )

        self.assertEqual(results, ["FIRST", "SECOND"])

    def test_all_marker_budgets_fail_before_provider_call(self):
        service = PromptTranslationService(
            max_markers=2,
            max_marker_characters=4,
            max_total_characters=6,
        )
        cases = (
            ("%{a}%{b}%{c}", TranslationMarkerCountError),
            ("%{abcde}", TranslationMarkerSizeError),
            ("%{abcd}%{abc}", TranslationTotalSizeError),
        )

        with patch(
            "easyuse_anima.translation.service.google_translate_text"
        ) as provider:
            for text, error_type in cases:
                with self.subTest(error=error_type.__name__):
                    with self.assertRaises(error_type):
                        service.translate_prompt(text, GOOGLE_SETTINGS)
            provider.assert_not_called()


class GoogleTranslationProviderErrorTests(unittest.TestCase):
    def test_missing_optional_dependency_has_stable_unavailable_error(self):
        def unavailable():
            raise ImportError("googletrans is not installed")

        provider = GoogleTranslationProvider(translator_factory=unavailable)
        with self.assertRaises(TranslationProviderUnavailableError) as raised:
            provider.translate("text", "auto", "en")
        self.assertEqual(raised.exception.code, "translation_provider_unavailable")

    def test_provider_boundary_normalizes_timeout_and_arbitrary_upstream_errors(self):
        class TimeoutTranslator:
            def translate(self, *_args, **_kwargs):
                raise TimeoutError("slow")

        class FailedTranslator:
            def translate(self, *_args, **_kwargs):
                raise ValueError("provider internals must not leak")

        with self.assertRaises(TranslationTimeoutError) as timeout:
            GoogleTranslationProvider(lambda: TimeoutTranslator()).translate(
                "text", "auto", "en"
            )
        self.assertEqual(timeout.exception.message, "The translation provider timed out.")

        with self.assertRaises(TranslationUpstreamError) as upstream:
            GoogleTranslationProvider(lambda: FailedTranslator()).translate(
                "text", "auto", "en"
            )
        self.assertEqual(
            upstream.exception.message,
            "The translation provider request failed.",
        )


if __name__ == "__main__":
    unittest.main()
