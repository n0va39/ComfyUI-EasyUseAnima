from __future__ import annotations

import builtins
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch

from prompt_translation import (
    PROMPT_TRANSLATION_PROVIDER_GOOGLE,
    BoundedTranslationCache,
    GoogleTranslationProvider,
    PromptTranslationService,
    PromptTranslationSettings,
    TranslationMarkerCountError,
    TranslationMarkerSizeError,
    TranslationProviderUnavailableError,
    TranslationTimeoutError,
    TranslationTotalSizeError,
    TranslationUpstreamError,
    _TRANSLATION_PROVIDER_FACTORIES,
    _TRANSLATION_PROVIDER_INSTANCES,
    get_translation_provider,
)


GOOGLE_SETTINGS = PromptTranslationSettings(
    provider=PROMPT_TRANSLATION_PROVIDER_GOOGLE,
    source="ko",
    target="en",
)


class PromptTranslationServiceTests(unittest.TestCase):
    def test_repeated_identical_markers_call_provider_once_and_replace_every_position(self):
        service = PromptTranslationService(
            cache=BoundedTranslationCache(max_entries=8, ttl_seconds=60)
        )

        with patch(
            "prompt_translation.google_translate_text",
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
            patch("prompt_translation.get_translation_provider") as provider_factory,
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

    def test_provider_factory_reuses_one_provider_instance(self):
        provider = GoogleTranslationProvider(translator_factory=lambda: object())
        factory_calls = []

        def factory():
            factory_calls.append(True)
            return provider

        with (
            patch.dict(_TRANSLATION_PROVIDER_INSTANCES, {}, clear=True),
            patch.dict(
                _TRANSLATION_PROVIDER_FACTORIES,
                {PROMPT_TRANSLATION_PROVIDER_GOOGLE: factory},
                clear=True,
            ),
        ):
            first = get_translation_provider(PROMPT_TRANSLATION_PROVIDER_GOOGLE)
            second = get_translation_provider(PROMPT_TRANSLATION_PROVIDER_GOOGLE)

        self.assertIs(first, provider)
        self.assertIs(second, provider)
        self.assertEqual(len(factory_calls), 1)

    def test_cache_hit_ttl_expiry_and_lru_bound_are_deterministic(self):
        now = [0.0]
        lru_cache = BoundedTranslationCache(
            max_entries=2,
            ttl_seconds=10,
            time_func=lambda: now[0],
        )
        lru_service = PromptTranslationService(cache=lru_cache)

        with patch(
            "prompt_translation.google_translate_text",
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
            "prompt_translation.google_translate_text",
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
            "prompt_translation.google_translate_text",
            side_effect=lambda text, source, target: f"{source}:{target}:{text}",
        ) as provider:
            for item in settings:
                service.translate_prompt("%{same}", item)
            service.translate_prompt("%{different}", GOOGLE_SETTINGS)
            service.translate_prompt("%{same}", GOOGLE_SETTINGS)

        self.assertEqual(provider.call_count, 4)

    def test_cache_and_request_dedup_are_thread_safe(self):
        service = PromptTranslationService(
            cache=BoundedTranslationCache(max_entries=8, ttl_seconds=60)
        )

        def translate(text, source, target):
            time.sleep(0.01)
            return "shared"

        with patch(
            "prompt_translation.google_translate_text",
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

        with patch("prompt_translation.google_translate_text") as provider:
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

    def test_timeout_and_arbitrary_upstream_errors_are_normalized(self):
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
