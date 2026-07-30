from __future__ import annotations

import unittest
from typing import get_type_hints
from unittest.mock import Mock, patch

from easyuse_anima.aio import conditioning
from easyuse_anima.aio.generation_defaults import (
    AIO_USDU_PROMPT_FULL,
    AIO_USDU_PROMPT_NO_GENERAL,
)
from easyuse_anima.prompt.contracts import AdvancedField
from tests.comfy_host_fakes import patch_comfy_helper


class AIOConditioningMoveTests(unittest.TestCase):
    def test_prompt_data_fields_use_canonical_advanced_field_contract(self):
        self.assertEqual(
            get_type_hints(conditioning._aio_prompt_data_fields_for_usdu)["return"],
            list[AdvancedField],
        )

    def test_conditioning_symbols_are_owned_by_the_canonical_module(self):
        for name in (
            "_aio_prompt_data_fields_for_usdu",
            "_aio_usdu_prompt_without_general",
            "_aio_usdu_conditioning",
        ):
            with self.subTest(name=name):
                self.assertEqual(getattr(conditioning, name).__module__, conditioning.__name__)

    def test_full_mode_preserves_original_conditioning_identity(self):
        positive = object()
        negative = object()
        with patch_comfy_helper(conditioning, "_encode_with_comfy_clip") as encode:
            result = conditioning._aio_usdu_conditioning(
                "clip",
                positive,
                negative,
                {"prompt_mode": AIO_USDU_PROMPT_FULL},
                "quality",
                "negative quality",
            )

        self.assertIs(result[0], positive)
        self.assertIs(result[1], negative)
        encode.assert_not_called()

    def test_no_general_mode_preserves_prompt_filtering_and_encode_order(self):
        prompt_data = {
            "pin_trigger_tags_to_front": True,
            "fields": [
                {
                    "id": "positive-general",
                    "type": "general",
                    "pane": "positive",
                    "enabled": True,
                    "text": "general prompt",
                },
                {
                    "id": "positive-trigger",
                    "type": "trigger",
                    "pane": "positive",
                    "enabled": True,
                    "text": "trigger prompt",
                },
                {
                    "id": "positive-quality",
                    "type": "quality",
                    "pane": "positive",
                    "enabled": True,
                    "text": "best quality",
                },
                {
                    "id": "negative-quality",
                    "type": "quality",
                    "pane": "negative",
                    "enabled": True,
                    "text": "bad anatomy",
                },
            ],
        }
        encoded: list[str] = []

        def encode(_clip, text):
            encoded.append(text)
            return f"encoded:{text}"

        with patch_comfy_helper(
            conditioning,
            "_encode_with_comfy_clip",
            side_effect=encode,
        ):
            result = conditioning._aio_usdu_conditioning(
                "clip",
                "original-positive",
                "original-negative",
                {"prompt_mode": AIO_USDU_PROMPT_NO_GENERAL},
                "fallback quality",
                "fallback negative",
                prompt_data=prompt_data,
            )

        self.assertEqual(
            result,
            (f"encoded:{encoded[0]}", f"encoded:{encoded[1]}"),
        )
        self.assertEqual(len(encoded), 2)
        self.assertNotIn("general prompt", encoded[0])
        self.assertIn("trigger prompt", encoded[0])
        self.assertIn("best quality", encoded[0])
        self.assertIn("bad anatomy", encoded[1])

    def test_no_general_turbo_reencodes_derived_positive_and_neutral_negative(self):
        prompt_data = {
            "fields": [
                {
                    "id": "positive-trigger",
                    "type": "trigger",
                    "pane": "positive",
                    "enabled": True,
                    "text": "detail subject",
                },
                {
                    "id": "negative-quality",
                    "type": "quality",
                    "pane": "negative",
                    "enabled": True,
                    "text": "bad anatomy",
                },
            ],
        }
        clip = object()
        calls: list[tuple[object, str]] = []

        def encode(source_clip, text):
            calls.append((source_clip, text))
            return {"prompt": text}

        with patch_comfy_helper(
            conditioning,
            "_encode_with_comfy_clip",
            side_effect=encode,
        ):
            result = conditioning._aio_usdu_conditioning(
                clip,
                "original-positive",
                "original-negative",
                {"prompt_mode": AIO_USDU_PROMPT_NO_GENERAL},
                "",
                "",
                prompt_data=prompt_data,
                negpip_mode="turbo",
            )

        self.assertEqual(
            calls,
            [
                (clip, "detail subject, (bad anatomy:-1)"),
                (clip, ""),
            ],
        )
        self.assertEqual(
            result,
            ({"prompt": calls[0][1]}, {"prompt": calls[1][1]}),
        )

    def test_no_general_fallback_respects_quality_exclusion_and_call_time_lookup(self):
        calls: list[tuple[str, str]] = []
        replacement_encode = Mock(
            side_effect=lambda _clip, text: calls.append(("replacement", text))
            or f"replacement:{text}"
        )

        def first_encode(_clip, text):
            calls.append(("first", text))
            encode.side_effect = replacement_encode
            return f"first:{text}"

        with (
            patch.object(
                conditioning,
                "_aio_usdu_prompt_without_general",
                return_value=("", False),
            ),
            patch_comfy_helper(
                conditioning,
                "_encode_with_comfy_clip",
                side_effect=first_encode,
            ) as encode,
        ):
            result = conditioning._aio_usdu_conditioning(
                "clip",
                "positive",
                "negative",
                {"prompt_mode": "quality_tags_only"},
                "fallback quality",
                "fallback negative",
                exclude_positive_quality=True,
            )

        self.assertEqual(result, ("first:", "replacement:fallback negative"))
        self.assertEqual(calls, [("first", ""), ("replacement", "fallback negative")])


if __name__ == "__main__":
    unittest.main()
