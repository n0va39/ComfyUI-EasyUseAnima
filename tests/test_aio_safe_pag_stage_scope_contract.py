from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "aio_safe_pag_stage_scope_contract.v1.json"


def _scope(enabled: bool, raw: object, fixture: dict[str, Any]) -> dict[str, bool]:
    stage_ids = tuple(fixture["stage_ids"])
    if not enabled:
        return {stage_id: False for stage_id in stage_ids}
    if raw is None:
        return dict(fixture["legacy_missing_scope"])
    if not isinstance(raw, dict):
        return dict(fixture["malformed_scope"]["expected"])
    return {stage_id: raw.get(stage_id) is True for stage_id in stage_ids}


def _selected_stages(enabled: bool, raw: object, fixture: dict[str, Any]) -> list[str]:
    normalized = _scope(enabled, raw, fixture)
    return [stage_id for stage_id in fixture["stage_ids"] if normalized[stage_id]]


def _apply_selected_stage(
    base_model: dict[str, Any],
    *,
    stage_id: str,
    selected: bool,
    lookups: list[str],
) -> dict[str, Any]:
    if not selected:
        return base_model
    lookups.append(stage_id)
    cloned = {**base_model, "lineage": list(base_model["lineage"])}
    cloned["lineage"].append(f"safe_pag:{stage_id}")
    return cloned


def _with_temporary_attention(
    module: dict[str, object],
    replacement: object,
    sampler: Callable[[], object],
) -> object:
    original = module["optimized_attention"]
    module["optimized_attention"] = replacement
    try:
        return sampler()
    finally:
        module["optimized_attention"] = original


class AioSafePagStageScopeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_identity_scope_and_ownership_decisions_are_frozen(self) -> None:
        fixture = self.fixture

        self.assertEqual(
            fixture["upstream"],
            {
                "repository": "iljung1106/comfyui-anima-safe-pag",
                "commit": "905b0107d1f924fc6acbcac3b6a879b566ff671c",
                "node_id": "AnimaSafePAG",
            },
        )
        self.assertEqual(
            fixture["stage_ids"],
            ["first_pass", "highres", "detailer", "upscale"],
        )
        self.assertEqual(
            fixture["fresh_stage_scope"],
            {
                "first_pass": True,
                "highres": False,
                "detailer": False,
                "upscale": False,
            },
        )
        self.assertTrue(all(fixture["legacy_missing_scope"].values()))
        self.assertEqual(
            fixture["malformed_scope"]["policy"],
            "fail-closed-all-disabled",
        )
        self.assertFalse(fixture["ownership"]["generic_patch_registry"])
        self.assertFalse(fixture["ownership"]["generic_scope_ui"])
        self.assertFalse(
            fixture["ownership"]["public_socket_or_workflow_schema_change"]
        )

    def test_scope_cases_select_only_known_sampling_stages(self) -> None:
        fixture = self.fixture

        for case in fixture["scope_cases"]:
            with self.subTest(case=case["id"]):
                raw_scope = None if case.get("scope_missing") else case.get("scope")
                self.assertEqual(
                    _selected_stages(case["enabled"], raw_scope, fixture),
                    case["selected_stages"],
                )

        self.assertTrue(
            set(fixture["non_sampling_ids"]).isdisjoint(fixture["stage_ids"])
        )

    def test_lookup_and_clone_happen_only_for_selected_stage(self) -> None:
        fixture = self.fixture
        custom = next(
            case for case in fixture["scope_cases"] if case["id"] == "custom-highres-upscale"
        )
        selected = set(
            _selected_stages(custom["enabled"], custom["scope"], fixture)
        )
        base_model = {"lineage": ["model_with_lora"]}
        lookups: list[str] = []

        variants = {
            stage_id: _apply_selected_stage(
                base_model,
                stage_id=stage_id,
                selected=stage_id in selected,
                lookups=lookups,
            )
            for stage_id in fixture["stage_ids"]
        }

        self.assertEqual(lookups, ["highres", "upscale"])
        self.assertIs(variants["first_pass"], base_model)
        self.assertIs(variants["detailer"], base_model)
        self.assertIsNot(variants["highres"], base_model)
        self.assertIsNot(variants["upscale"], base_model)
        self.assertIsNot(variants["highres"], variants["upscale"])
        self.assertEqual(base_model, {"lineage": ["model_with_lora"]})

    def test_temporary_attention_mutation_restores_exact_reference(self) -> None:
        original = object()
        replacement = object()
        module: dict[str, object] = {"optimized_attention": original}

        seen = _with_temporary_attention(
            module,
            replacement,
            lambda: module["optimized_attention"],
        )

        self.assertIs(seen, replacement)
        self.assertIs(module["optimized_attention"], original)

        def fail() -> object:
            self.assertIs(module["optimized_attention"], replacement)
            raise RuntimeError("sampling failed")

        with self.assertRaisesRegex(RuntimeError, "sampling failed"):
            _with_temporary_attention(module, replacement, fail)
        self.assertIs(module["optimized_attention"], original)

    def test_precedence_keeps_safe_pag_feature_owned_and_defers_sage_scope(self) -> None:
        precedence = self.fixture["precedence"]
        chain = precedence["current_chain"]

        for before, after in precedence["fixed_edges"]:
            with self.subTest(edge=(before, after)):
                self.assertLess(chain.index(before), chain.index(after))

        self.assertEqual(precedence["sage_stage_scope_owner"], "#441")
        self.assertEqual(
            self.fixture["ownership"]["feature_payload_owner"],
            "safe-pag-adapter",
        )
        self.assertFalse(self.fixture["lifecycle"]["persistent_shared_mutation"])
        self.assertEqual(
            self.fixture["lifecycle"]["restore_on"],
            ["success", "exception"],
        )


if __name__ == "__main__":
    unittest.main()
