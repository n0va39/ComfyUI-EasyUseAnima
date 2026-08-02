from __future__ import annotations

import json
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

from easyuse_anima.nodes import prompt_advanced_nodes, regional_nodes
from easyuse_anima.nodes.prompt_advanced_nodes import (
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioAdvancedV2,
)
from easyuse_anima.nodes.regional_nodes import EasyUseAnimaPromptStudioRegional
from easyuse_anima.nodes.seed_adapters import PromptStudioSeedExecution
from easyuse_anima.seed.execution_identity import SeedExecutionIdentity
from easyuse_anima.seed.service import InMemorySeedReservationService


@contextmanager
def authoritative_seed(**_kwargs):
    yield PromptStudioSeedExecution(execution_seed=9, next_seed=10)


def passthrough_expansion(fields, seed, _mode):
    return fields, {
        "changed": False,
        "seed": seed,
        "used_keys": (),
        "missing_keys": (),
    }


class PromptStudioSeedCutoverTests(unittest.TestCase):
    def test_nonfixed_controls_force_backend_execution(self):
        for node_class in (
            EasyUseAnimaPromptStudioAdvanced,
            EasyUseAnimaPromptStudioAdvancedV2,
            EasyUseAnimaPromptStudioRegional,
        ):
            with self.subTest(node=node_class.__name__):
                changed = node_class.IS_CHANGED(
                    wildcard_seed=7,
                    wildcard_seed_after_generate="increment",
                )
                self.assertNotEqual(changed, changed)

    def test_advanced_uses_authoritative_execution_and_next_seed(self):
        with (
            patch.object(
                prompt_advanced_nodes,
                "prompt_studio_seed_execution",
                side_effect=authoritative_seed,
            ) as session,
            patch.object(
                prompt_advanced_nodes,
                "_expand_advanced_wildcard_fields",
                side_effect=passthrough_expansion,
            ) as expand,
        ):
            result = EasyUseAnimaPromptStudioAdvanced().build(
                False,
                True,
                False,
                False,
                "[]",
                wildcard_seed=7,
                wildcard_seed_after_generate="increment",
                unique_id="41",
            )

        payload = result["ui"]["prompt_studio_advanced"][0]
        self.assertEqual(payload["wildcard_execution_seed"], 9)
        self.assertEqual(payload["wildcard_seed"], 10)
        self.assertEqual(expand.call_args.args[1], 9)
        session.assert_called_once()

    def test_advanced_emits_explicit_linked_and_naia_execution_deltas(self):
        fields = [
            {
                "id": "positive_general",
                "pane": "positive",
                "type": "general",
                "text": "local fallback",
                "enabled": True,
            },
            {
                "id": "positive_naia",
                "pane": "positive",
                "type": "naia",
                "text": "old positive",
                "enabled": True,
            },
            {
                "id": "negative_naia",
                "pane": "negative",
                "type": "naia",
                "text": "old negative",
                "enabled": True,
            },
        ]
        settings = {
            "use_naia_settings": True,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
            "host": "127.0.0.1",
            "port": 7243,
            "allow_remote_api": False,
        }
        with (
            patch.object(
                prompt_advanced_nodes,
                "resolve_naia_settings",
                return_value=settings,
            ),
            patch.object(prompt_advanced_nodes, "_post_random", return_value={}),
            patch.object(
                prompt_advanced_nodes,
                "_parse_random_response",
                return_value=("generated positive", "generated negative", 1024, 1536),
            ),
            patch.object(
                prompt_advanced_nodes,
                "_resolve_naia_resolution",
                return_value=(1024, 1536),
            ),
        ):
            result = EasyUseAnimaPromptStudioAdvanced().build(
                use_naia=True,
                consume_naia_on_queue=True,
                use_anima_mod_guidance=False,
                pin_trigger_tags_to_front=False,
                advanced_fields=json.dumps(fields),
                resolution_bucket=prompt_advanced_nodes.NAIA_ADVANCED_RESOLUTION_BUCKET,
                _seed_execution=PromptStudioSeedExecution(
                    execution_seed=9,
                    next_seed=10,
                ),
                field_positive_general="resolved connected text",
            )

        payload = result["ui"]["prompt_studio_advanced"][0]
        self.assertEqual(
            payload["field_inputs"],
            {"field_positive_general": "resolved connected text"},
        )
        self.assertEqual(
            payload["naia_field_updates"],
            {
                "positive_naia": "generated positive",
                "negative_naia": "generated negative",
            },
        )
        self.assertEqual(
            payload["naia_resolution_update"],
            {"width": 1024, "height": 1536},
        )

    def test_advanced_omits_inactive_naia_execution_deltas(self):
        result = EasyUseAnimaPromptStudioAdvanced().build(
            use_naia=False,
            consume_naia_on_queue=True,
            use_anima_mod_guidance=False,
            pin_trigger_tags_to_front=False,
            advanced_fields=json.dumps([
                {
                    "id": "positive_general",
                    "pane": "positive",
                    "type": "general",
                    "text": "local fallback",
                    "enabled": True,
                },
            ]),
            _seed_execution=PromptStudioSeedExecution(
                execution_seed=9,
                next_seed=10,
            ),
            field_positive_general="resolved connected text",
        )

        payload = result["ui"]["prompt_studio_advanced"][0]
        self.assertEqual(
            payload["field_inputs"],
            {"field_positive_general": "resolved connected text"},
        )
        self.assertNotIn("naia_field_updates", payload)
        self.assertNotIn("naia_resolution_update", payload)

    def test_advanced_v2_keeps_one_session_through_structured_output(self):
        expansion_seeds: list[int] = []

        def record_expansion(fields, seed, mode):
            expansion_seeds.append(seed)
            return passthrough_expansion(fields, seed, mode)

        with (
            patch.object(
                prompt_advanced_nodes,
                "prompt_studio_seed_execution",
                side_effect=authoritative_seed,
            ) as session,
            patch.object(
                prompt_advanced_nodes,
                "_expand_advanced_wildcard_fields",
                side_effect=record_expansion,
            ),
        ):
            result = EasyUseAnimaPromptStudioAdvancedV2().build(
                False,
                True,
                False,
                False,
                "[]",
                wildcard_seed=7,
                wildcard_seed_after_generate="increment",
                unique_id="42",
            )

        payload = result["ui"]["prompt_studio_advanced"][0]
        prompt_data = result["result"][0]
        self.assertEqual(payload["wildcard_execution_seed"], 9)
        self.assertEqual(payload["wildcard_seed"], 10)
        self.assertEqual(expansion_seeds, [9])
        self.assertEqual(prompt_data["parameters"]["wildcard_seed"], 9)
        session.assert_called_once()

    def test_advanced_v2_reuses_first_effective_field_snapshot(self):
        fields = [{
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "text": "saved fallback",
            "enabled": True,
        }]
        expansion_results = iter((
            (
                [{**fields[0], "text": "old snapshot"}],
                {
                    "changed": True,
                    "used_keys": ("old-key",),
                    "missing_keys": ("old-missing",),
                },
            ),
            (
                [{**fields[0], "text": "new snapshot"}],
                {
                    "changed": True,
                    "used_keys": ("new-key",),
                    "missing_keys": ("new-missing",),
                },
            ),
        ))

        def changing_expansion(expand_fields, _seed, _mode):
            self.assertEqual(expand_fields[0]["text"], "{cat|dog}")
            return next(expansion_results)

        with patch.object(
            prompt_advanced_nodes,
            "_expand_advanced_wildcard_fields",
            side_effect=changing_expansion,
        ) as expand:
            result = EasyUseAnimaPromptStudioAdvancedV2().build(
                False,
                False,
                False,
                False,
                json.dumps(fields),
                wildcard_seed=17,
                wildcard_seed_after_generate="fixed",
                field_positive_general="{cat|dog}",
            )

        prompt_data = result["result"][0]
        self.assertEqual(expand.call_count, 1)
        self.assertEqual(prompt_data["positive_prompt"], "old snapshot")
        self.assertEqual(prompt_data["global_prompt"], "old snapshot")
        self.assertEqual(prompt_data["fields"][0]["text"], "old snapshot")
        self.assertEqual(
            prompt_data["field_inputs"],
            {"field_positive_general": "{cat|dog}"},
        )
        self.assertEqual(prompt_data["wildcard"]["used_keys"], ["old-key"])
        self.assertEqual(prompt_data["wildcard"]["missing_keys"], ["old-missing"])
        parameter_fields = json.loads(prompt_data["parameters"]["advanced_fields"])
        self.assertEqual(parameter_fields[0]["text"], "saved fallback")

    def test_regional_uses_authoritative_execution_and_next_seed(self):
        with (
            patch.object(
                regional_nodes,
                "prompt_studio_seed_execution",
                side_effect=authoritative_seed,
            ) as session,
            patch.object(
                regional_nodes,
                "_expand_advanced_wildcard_fields",
                side_effect=passthrough_expansion,
            ) as expand,
        ):
            result = EasyUseAnimaPromptStudioRegional().build(
                "",
                "",
                wildcard_seed=7,
                wildcard_seed_after_generate="increment",
                unique_id="43",
            )

        payload = result["ui"]["prompt_studio_regional"][0]
        self.assertEqual(payload["wildcard_execution_seed"], 9)
        self.assertEqual(payload["wildcard_seed"], 10)
        self.assertEqual(expand.call_args.args[1], 9)
        session.assert_called_once()

    def test_advanced_real_service_advances_then_fixed_replays_saved_seed(self):
        service = InMemorySeedReservationService()
        identities = [
            SeedExecutionIdentity("advanced:41", request_id)
            for request_id in ("request:1", "request:2", "request:3")
        ]
        with (
            patch(
                "easyuse_anima.nodes.seed_adapters.resolve_seed_execution_identity",
                side_effect=identities,
            ),
            patch(
                "easyuse_anima.nodes.seed_adapters.get_runtime",
                return_value=SimpleNamespace(seed_reservations=service),
            ),
        ):
            advancing = [
                EasyUseAnimaPromptStudioAdvanced().build(
                    False,
                    True,
                    False,
                    False,
                    "[]",
                    wildcard_seed=7,
                    wildcard_seed_after_generate="increment",
                    unique_id="41",
                )
                for _ in range(2)
            ]
            replay = EasyUseAnimaPromptStudioAdvanced().build(
                False,
                True,
                False,
                False,
                "[]",
                wildcard_seed=7,
                wildcard_seed_after_generate="fixed",
                unique_id="41",
            )

        advancing_payloads = [
            result["ui"]["prompt_studio_advanced"][0]
            for result in advancing
        ]
        replay_payload = replay["ui"]["prompt_studio_advanced"][0]
        self.assertEqual(
            [
                (
                    payload["wildcard_execution_seed"],
                    payload["wildcard_seed"],
                )
                for payload in advancing_payloads
            ],
            [(7, 8), (8, 9)],
        )
        self.assertEqual(
            (
                replay_payload["wildcard_execution_seed"],
                replay_payload["wildcard_seed"],
            ),
            (7, 7),
        )


if __name__ == "__main__":
    unittest.main()
