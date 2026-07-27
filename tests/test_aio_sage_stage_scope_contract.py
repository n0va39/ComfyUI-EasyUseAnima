from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "aio_sage_stage_scope_contract.v1.json"


class SageContractError(ValueError):
    pass


@dataclass
class FakeModel:
    name: str
    model_options: dict[str, Any]

    def clone(self) -> FakeModel:
        return FakeModel(
            name=f"{self.name}:clone",
            model_options=_deepcopy_list_dict(self.model_options),
        )


def _deepcopy_list_dict(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _deepcopy_list_dict(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_deepcopy_list_dict(item) for item in value]
    return value


def _scope(mode: str, raw: object, fixture: dict[str, Any]) -> dict[str, bool]:
    stage_ids = tuple(fixture["stage_ids"])
    if mode == "disabled":
        return {stage_id: False for stage_id in stage_ids}
    if raw is None:
        return dict(fixture["legacy_missing_scope"])
    if not isinstance(raw, dict):
        return dict(fixture["malformed_scope"]["expected"])
    return {stage_id: raw.get(stage_id) is True for stage_id in stage_ids}


def _selected_stages(
    mode: str,
    raw: object,
    fixture: dict[str, Any],
) -> list[str]:
    normalized = _scope(mode, raw, fixture)
    return [stage_id for stage_id in fixture["stage_ids"] if normalized[stage_id]]


def _validate_node_contract(
    object_info: object,
    patch_parameters: object,
    fixture: dict[str, Any],
) -> bool:
    if not isinstance(object_info, dict):
        return False
    node_id = fixture["upstream"]["node_id"]
    node = object_info.get(node_id)
    if not isinstance(node, dict):
        return False
    inputs = node.get("input")
    if not isinstance(inputs, dict):
        return False
    required = inputs.get("required")
    optional = inputs.get("optional")
    if not isinstance(required, dict) or not isinstance(optional, dict):
        return False
    contract = fixture["node_contract"]
    if list(required) != contract["required_inputs"]:
        return False
    if list(optional) != contract["optional_inputs"]:
        return False
    allow_compile = optional.get("allow_compile")
    if not (
        isinstance(allow_compile, list)
        and allow_compile
        and allow_compile[0] == "BOOLEAN"
    ):
        return False
    return patch_parameters == contract["patch_parameters"]


def _apply_selected_stage(
    base_model: FakeModel,
    *,
    stage_id: str,
    selected: bool,
    mode: str,
    allow_compile: bool,
    fixture: dict[str, Any],
    lookups: list[str],
    disable_wrapper: Callable[[object], object],
    compile_calls: list[str],
    override_factory: Callable[[], object] = object,
) -> FakeModel:
    if not selected:
        return base_model
    if mode not in fixture["node_contract"]["sage_modes"] or mode == "disabled":
        raise SageContractError("unsupported SageAttention mode")

    lookups.append(stage_id)
    cloned = base_model.clone()
    override = override_factory()
    if not allow_compile:
        override = disable_wrapper(override)
    # PathchSageAttentionKJ does not call torch.compile. The boolean only
    # permits a downstream compile owner to trace the attention function.
    if compile_calls:
        raise AssertionError("test harness must not pre-populate compile calls")
    cloned.model_options.setdefault("transformer_options", {})[
        "optimized_attention_override"
    ] = override
    return cloned


class AioSageStageScopeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_upstream_scope_and_ownership_decisions_are_frozen(self) -> None:
        fixture = self.fixture

        self.assertEqual(fixture["decision"], "FEASIBLE")
        self.assertEqual(
            fixture["upstream"],
            {
                "repository": "kijai/ComfyUI-KJNodes",
                "pinned_commit": "e27a505b3ba6ce42687fe00500deda103d9d6071",
                "verified_current_commit": "bb131be9e83d2f773c90f1d6f1e4b248a498c8c5",
                "node_id": "PathchSageAttentionKJ",
                "function": "patch",
                "experimental": True,
                "model_options_path": [
                    "transformer_options",
                    "optimized_attention_override",
                ],
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
        self.assertEqual(
            fixture["ownership"]["fp16_accumulation_scope"],
            "run-global",
        )
        self.assertEqual(
            fixture["ownership"]["torch_compile_scope"],
            "run-wide",
        )

    def test_scope_cases_select_only_known_sampling_stages(self) -> None:
        fixture = self.fixture

        for case in fixture["scope_cases"]:
            with self.subTest(case=case["id"]):
                raw_scope = None if case.get("scope_missing") else case.get("scope")
                self.assertEqual(
                    _selected_stages(case["mode"], raw_scope, fixture),
                    case["selected_stages"],
                )

        self.assertTrue(
            set(fixture["non_sampling_ids"]).isdisjoint(fixture["stage_ids"])
        )

    def test_selected_clones_isolate_override_from_base_and_siblings(self) -> None:
        fixture = self.fixture
        custom = next(
            case
            for case in fixture["scope_cases"]
            if case["id"] == "custom-highres-detailer"
        )
        selected = set(_selected_stages(custom["mode"], custom["scope"], fixture))
        existing_leaf = object()
        base = FakeModel(
            "model_with_lora",
            {"transformer_options": {"existing": existing_leaf}},
        )
        lookups: list[str] = []
        disable_calls: list[object] = []
        compile_calls: list[str] = []

        def disable(value: object) -> object:
            disable_calls.append(value)
            return ("compiler-disabled", value)

        variants = {
            stage_id: _apply_selected_stage(
                base,
                stage_id=stage_id,
                selected=stage_id in selected,
                mode=custom["mode"],
                allow_compile=False,
                fixture=fixture,
                lookups=lookups,
                disable_wrapper=disable,
                compile_calls=compile_calls,
            )
            for stage_id in fixture["stage_ids"]
        }

        self.assertEqual(lookups, ["highres", "detailer"])
        self.assertEqual(len(disable_calls), 2)
        self.assertEqual(compile_calls, [])
        self.assertIs(variants["first_pass"], base)
        self.assertIs(variants["upscale"], base)
        self.assertIsNot(variants["highres"], base)
        self.assertIsNot(variants["detailer"], base)
        self.assertIsNot(variants["highres"], variants["detailer"])
        self.assertIsNot(
            variants["highres"].model_options["transformer_options"],
            variants["detailer"].model_options["transformer_options"],
        )
        self.assertIs(
            variants["highres"].model_options["transformer_options"]["existing"],
            existing_leaf,
        )
        self.assertNotIn(
            "optimized_attention_override",
            base.model_options["transformer_options"],
        )
        highres_override = variants["highres"].model_options["transformer_options"][
            "optimized_attention_override"
        ]
        detailer_override = variants["detailer"].model_options[
            "transformer_options"
        ]["optimized_attention_override"]
        self.assertIsNot(highres_override, detailer_override)

    def test_allow_compile_and_failure_paths_do_not_mutate_shared_base(self) -> None:
        fixture = self.fixture
        base = FakeModel("base", {"transformer_options": {}})
        compile_calls: list[str] = []
        disable_calls: list[object] = []
        lookups: list[str] = []

        def disable(value: object) -> object:
            disable_calls.append(value)
            return value

        disabled = _apply_selected_stage(
            base,
            stage_id="first_pass",
            selected=True,
            mode="auto",
            allow_compile=False,
            fixture=fixture,
            lookups=lookups,
            disable_wrapper=disable,
            compile_calls=compile_calls,
        )
        traceable = _apply_selected_stage(
            base,
            stage_id="highres",
            selected=True,
            mode="auto",
            allow_compile=True,
            fixture=fixture,
            lookups=lookups,
            disable_wrapper=disable,
            compile_calls=compile_calls,
        )

        self.assertEqual(len(disable_calls), 1)
        self.assertEqual(compile_calls, [])
        self.assertIsNot(disabled, traceable)
        self.assertNotIn(
            "optimized_attention_override",
            base.model_options["transformer_options"],
        )

        with self.assertRaisesRegex(RuntimeError, "override construction failed"):
            _apply_selected_stage(
                base,
                stage_id="detailer",
                selected=True,
                mode="auto",
                allow_compile=True,
                fixture=fixture,
                lookups=lookups,
                disable_wrapper=disable,
                compile_calls=compile_calls,
                override_factory=lambda: (_ for _ in ()).throw(
                    RuntimeError("override construction failed")
                ),
            )
        self.assertNotIn(
            "optimized_attention_override",
            base.model_options["transformer_options"],
        )

        before_unknown = list(lookups)
        with self.assertRaisesRegex(SageContractError, "unsupported"):
            _apply_selected_stage(
                base,
                stage_id="upscale",
                selected=True,
                mode="future-mode",
                allow_compile=False,
                fixture=fixture,
                lookups=lookups,
                disable_wrapper=disable,
                compile_calls=compile_calls,
            )
        self.assertEqual(lookups, before_unknown)

    def test_node_drift_precedence_and_backend_handoff_are_bounded(self) -> None:
        fixture = self.fixture
        valid_info = {
            "PathchSageAttentionKJ": {
                "input": {
                    "required": {
                        "model": ["MODEL"],
                        "sage_attention": [fixture["node_contract"]["sage_modes"]],
                    },
                    "optional": {"allow_compile": ["BOOLEAN"]},
                }
            }
        }
        valid_parameters = ["model", "sage_attention", "allow_compile"]

        self.assertTrue(
            _validate_node_contract(valid_info, valid_parameters, fixture)
        )
        drift_cases = [
            ({}, valid_parameters),
            (
                {
                    "PathchSageAttentionKJ": {
                        "input": {
                            "required": valid_info["PathchSageAttentionKJ"]["input"][
                                "required"
                            ],
                            "optional": {},
                        }
                    }
                },
                valid_parameters,
            ),
            (valid_info, ["model", "sage_attention"]),
        ]
        for info, parameters in drift_cases:
            with self.subTest(info=info, parameters=parameters):
                self.assertFalse(
                    _validate_node_contract(info, parameters, fixture)
                )

        precedence = fixture["precedence"]
        for chain_name in ("dave_selected_chain", "dave_unselected_chain"):
            chain = precedence[chain_name]
            for before, after in precedence["fixed_edges"]:
                if before in chain and after in chain:
                    with self.subTest(chain=chain_name, edge=(before, after)):
                        self.assertLess(chain.index(before), chain.index(after))
        self.assertEqual(
            precedence["torch_compile_pairwise"],
            "preserve-current-dave-dependent-order",
        )

        handoff = fixture["handoff"]
        self.assertEqual(handoff["next"], "AIO-SAGE-02")
        self.assertEqual(
            handoff["allowed_production_files"],
            [
                "easyuse_anima/aio/model_preparation.py",
                "easyuse_anima/aio/first_pass_cache.py",
            ],
        )
        self.assertIn("schema-settings-ui-cutover", handoff["forbidden"])
        self.assertFalse(
            fixture["ownership"]["public_socket_or_workflow_schema_change"]
        )


if __name__ == "__main__":
    unittest.main()
