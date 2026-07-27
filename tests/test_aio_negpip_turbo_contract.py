from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from easyuse_anima.aio import negpip as negpip_contract
from easyuse_anima.prompt import artist_mix
from tests.comfy_host_fakes import FakeComfyHostProvider, use_fake_comfy_host


_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "aio_negpip_turbo_contract.v1.json"
)


class AIONegPipTurboContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.policy = cls.fixture["policy"]

    def test_contract_identity_and_ownership_are_fixed(self):
        self.assertEqual(
            self.fixture["schema"],
            "easyuse_anima_aio_negpip_turbo_contract",
        )
        self.assertEqual(self.fixture["version"], 1)
        self.assertEqual(self.policy["mode"], "turbo")
        self.assertEqual(
            self.policy["policy_revision"],
            negpip_contract.NEGPIP_TURBO_POLICY_REVISION,
        )
        self.assertEqual(
            self.policy["negative_scale"],
            negpip_contract.NEGPIP_TURBO_NEGATIVE_SCALE,
        )
        self.assertEqual(self.policy["composition"], "whole_prompt_group")
        self.assertEqual(
            self.policy["input_phase"],
            "after_translation_and_wildcard_expansion",
        )
        self.assertEqual(self.policy["neutral_negative_prompt"], "")
        self.assertEqual(self.policy["malformed_policy"], "fail_closed")
        self.assertEqual(
            self.policy["malformed_reason_code"],
            negpip_contract.NEGPIP_TURBO_MALFORMED_REASON,
        )
        self.assertEqual(
            self.policy["rejected_composition"],
            "per_top_level_item",
        )

    def test_prompt_golden_covers_items_nesting_escapes_weights_and_empty(self):
        observed_ids = set()
        for case in self.fixture["prompt_cases"]:
            with self.subTest(case=case["id"]):
                observed_ids.add(case["id"])
                self.assertEqual(
                    negpip_contract._derive_aio_negpip_turbo_negative_contribution(
                        case["negative_prompt"]
                    ),
                    case["derived_negative_contribution"],
                )

        self.assertEqual(
            observed_ids,
            {
                "top_level_comma",
                "top_level_newline_empty_and_comment",
                "nested_delimiters",
                "existing_numeric_weights",
                "escaped_delimiters",
                "inline_hash_is_prompt_text",
                "empty",
                "comment_only",
            },
        )

    def test_malformed_prompt_fails_closed_without_mutating_source(self):
        for case in self.fixture["malformed_cases"]:
            with self.subTest(case=case["id"]):
                source = case["negative_prompt"]
                with self.assertRaisesRegex(
                    RuntimeError,
                    self.policy["malformed_reason_code"],
                ):
                    negpip_contract._derive_aio_negpip_turbo_negative_contribution(
                        source
                    )
                self.assertEqual(case["negative_prompt"], source)

    def test_conditioning_uses_same_patched_clip_and_neutral_empty_prompt(self):
        patched_clip = object()
        for case in self.fixture["conditioning_cases"]:
            calls: list[tuple[object, str]] = []
            encoded: list[dict[str, object]] = []

            def encode(clip: object, prompt: str) -> dict[str, object]:
                calls.append((clip, prompt))
                result = {
                    "conditioning": prompt,
                    "shape": (1, 512, 2048),
                    "metadata": {"source": "patched_clip"},
                }
                encoded.append(result)
                return result

            with self.subTest(case=case["id"]):
                positive_source = case["positive_prompt"]
                negative_source = case["negative_prompt"]
                positive_prompt, negative_prompt, _derived = (
                    negpip_contract._aio_negpip_execution_prompts(
                        positive_source,
                        negative_source,
                        "turbo",
                    )
                )
                positive = encode(patched_clip, positive_prompt)
                negative = encode(patched_clip, negative_prompt)

                self.assertEqual(
                    positive_prompt,
                    case["positive_execution_prompt"],
                )
                self.assertEqual(
                    calls,
                    [
                        (patched_clip, case["positive_execution_prompt"]),
                        (patched_clip, case["negative_execution_prompt"]),
                    ],
                )
                self.assertIs(positive, encoded[0])
                self.assertIs(negative, encoded[1])
                self.assertEqual(negative["shape"], (1, 512, 2048))
                self.assertEqual(
                    negative["metadata"],
                    {"source": "patched_clip"},
                )
                self.assertEqual(case["positive_prompt"], positive_source)
                self.assertEqual(case["negative_prompt"], negative_source)

    def test_artist_mix_variants_keep_runtime_only_turbo_contribution(self):
        source = {
            "fields": [
                {
                    "id": "positive-general",
                    "type": "general",
                    "pane": "positive",
                    "enabled": True,
                    "text": "base subject",
                },
            ],
            "positive_without_artist_section": "base subject",
            "artist_mix": {
                "enabled": True,
                "mode": "exact",
                "artist_prompt": "artist alpha",
                "artist_position": "correct",
            },
        }
        saved = deepcopy(source)
        clip = object()
        calls: list[tuple[object, str]] = []

        class ClipTextEncode:
            def encode(self, source_clip, prompt):
                calls.append((source_clip, prompt))
                return ([[object(), {"prompt": prompt}]],)

        provider = FakeComfyHostProvider(
            node_classes={"CLIPTextEncode": ClipTextEncode}
        )
        with use_fake_comfy_host(
            SimpleNamespace(__package__=""),
            provider,
        ):
            conditioning = artist_mix._encode_prompt_data_positive_conditioning(
                clip,
                source,
                "full positive",
                artist_mix_mode="exact",
                positive_execution_suffix="(bad anatomy:-1)",
            )

        self.assertTrue(conditioning)
        self.assertTrue(calls)
        self.assertTrue(all(source_clip is clip for source_clip, _ in calls))
        self.assertTrue(
            all("(bad anatomy:-1)" in prompt for _, prompt in calls)
        )
        self.assertEqual(source, saved)

    def test_sampling_cfg_is_runtime_only_and_saved_values_are_preserved(self):
        cases = self.fixture["stage_cfg_cases"]
        saved = deepcopy(cases)
        config = negpip_contract.AIOGenerationNegPipConfig.from_value(
            {"mode": "turbo"}
        )
        observed = {
            case["stage"]: (
                config.effective_cfg(case["stored_cfg"])
                if case["stage"] in self.policy["sampling_stages"]
                else case["stored_cfg"]
            )
            for case in cases
        }

        self.assertEqual(
            observed,
            {
                "first_pass": 1.0,
                "highres": 1.0,
                "detailer": 1.0,
                "upscale_usdu": 1.0,
                "upscale_resshift": None,
                "postprocess": None,
                "save_output": None,
            },
        )
        self.assertEqual(cases, saved)
        self.assertEqual(
            set(self.policy["sampling_stages"]),
            {"first_pass", "highres", "detailer", "upscale_usdu"},
        )
        self.assertEqual(
            set(self.policy["non_sampling_stages"]),
            {"upscale_resshift", "postprocess", "save_output"},
        )


if __name__ == "__main__":
    unittest.main()
