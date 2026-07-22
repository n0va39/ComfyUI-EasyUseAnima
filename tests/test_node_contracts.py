from __future__ import annotations

import ast
import importlib.util
import json
import math
import re
import subprocess
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import call, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import nodes
from easyuse_anima.common import serialization as common_serialization
from easyuse_anima.common import values as common_values
from easyuse_anima.image import detailer as image_detailer
from easyuse_anima.image import geometry as image_geometry
from easyuse_anima.image import scaling as image_scaling
from easyuse_anima.infrastructure.comfy import capabilities as comfy_capabilities
from easyuse_anima.infrastructure.comfy import invocation as comfy_invocation
from easyuse_anima.infrastructure.comfy import resources as comfy_resources
from easyuse_anima.lora import metadata as lora_metadata
from easyuse_anima.lora import preset as lora_preset
from easyuse_anima.naia import client as naia_client
from easyuse_anima.naia import resolution as naia_resolution
from easyuse_anima.nodes import (
    image_nodes,
    impact_detailer_nodes,
    lora_nodes,
    naia_nodes,
    prompt_advanced_nodes,
    prompt_data_nodes,
    prompt_nodes,
    sam3_nodes,
    wildcard_nodes,
)
from easyuse_anima.prompt import artist_mix as prompt_artist_mix
from easyuse_anima.prompt import advanced as prompt_advanced
from easyuse_anima.prompt import conditioning as prompt_conditioning
from easyuse_anima.prompt import data as prompt_data
from easyuse_anima.prompt import correction as prompt_correction
from easyuse_anima.prompt import fields as prompt_fields


PACKAGE_INIT = ROOT / "__init__.py"
FIXTURE = ROOT / "tests" / "fixtures" / "node_contracts_0_5_2.json"
FIXTURE_PROVENANCE_VERSION = "0.5.2"
WORKFLOW_SELECTIONS = (
    (
        ROOT / "docs" / "example_workflows" / "EasyUse_Anima_artist_mix_release_ko.json",
        24,
        "EasyUseAnimaPromptDataConditioning",
    ),
    (
        ROOT / "docs" / "example_workflows" / "EasyUse_Anima_regional_prompt_release_ko.json",
        3,
        "EasyUseAnimaRegionalConditioning",
    ),
)
WINDOWS_DRIVE_PATH_FRAGMENT = re.compile(r"(?:^|[\"'\s])[A-Za-z]:[\\/]")
SERIALIZATION_IRRELEVANT_CONFIG_KEYS = frozenset({"tooltip"})


def _assignment_value(tree: ast.Module, name: str) -> ast.AST:
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in statement.targets):
            return statement.value
    raise AssertionError(f"Missing top-level assignment: {name}")


def _root_mappings() -> tuple[list[tuple[str, str]], dict[str, str]]:
    tree = ast.parse(PACKAGE_INIT.read_text(encoding="utf-8-sig"), filename=PACKAGE_INIT.name)
    class_mapping_node = _assignment_value(tree, "NODE_CLASS_MAPPINGS")
    display_mapping_node = _assignment_value(tree, "NODE_DISPLAY_NAME_MAPPINGS")
    if not isinstance(class_mapping_node, ast.Dict) or not isinstance(display_mapping_node, ast.Dict):
        raise AssertionError("Node mappings must remain literal dictionaries")

    class_mappings = []
    for key_node, value_node in zip(class_mapping_node.keys, class_mapping_node.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            raise AssertionError("NODE_CLASS_MAPPINGS keys must be string literals")
        if not isinstance(value_node, ast.Name):
            raise AssertionError("NODE_CLASS_MAPPINGS values must be imported class names")
        class_mappings.append((key_node.value, value_node.id))

    display_mappings = ast.literal_eval(display_mapping_node)
    if not isinstance(display_mappings, dict):
        raise AssertionError("NODE_DISPLAY_NAME_MAPPINGS must remain a dictionary")
    return class_mappings, display_mappings


def _contains_absolute_path(value: str) -> bool:
    if WINDOWS_DRIVE_PATH_FRAGMENT.search(value) or "/home/" in value or value.startswith("\\\\"):
        return True
    stripped = value.strip()
    if not stripped.startswith(("{", "[")):
        return False
    try:
        decoded = json.loads(stripped)
    except (TypeError, ValueError):
        return False
    return _value_contains_absolute_path(decoded)


def _value_contains_absolute_path(value) -> bool:
    if isinstance(value, dict):
        return any(_value_contains_absolute_path(child) for child in value.values())
    if isinstance(value, list):
        return any(_value_contains_absolute_path(child) for child in value)
    return isinstance(value, str) and _contains_absolute_path(value)


def _normalize(value):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return value
    if isinstance(value, dict):
        return {
            str(key): _normalize(child)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize(child) for child in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_normalize(child) for child in value), key=lambda child: str(child))
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"

    text = str(value)
    if _contains_absolute_path(text):
        raise AssertionError(f"Refusing to snapshot an absolute path from {type(value).__name__}")
    return text


def _input_spec(spec) -> dict:
    if isinstance(spec, (tuple, list)) and spec:
        input_type = spec[0]
        config = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
        extra = list(spec[2:]) if len(spec) > 2 else []
    else:
        input_type = spec
        config = {}
        extra = []

    contract_config = {
        key: value
        for key, value in config.items()
        if key not in SERIALIZATION_IRRELEVANT_CONFIG_KEYS
    }
    result = {
        "type": _normalize(input_type),
        "config": _normalize(contract_config),
    }
    if extra:
        result["extra"] = _normalize(extra)
    return result


@contextmanager
def _deterministic_comfy_inputs():
    replacements = {
        "_comfy_max_resolution": lambda: 16384,
        "_comfy_sampler_names": lambda: ["contract_sampler_a", "contract_sampler_b"],
        "_comfy_scheduler_names": lambda: ["contract_scheduler_a", "contract_scheduler_b"],
        "_comfy_diffusion_model_names": lambda: ["contract/diffusion_model.safetensors"],
        "_comfy_text_encoder_names": lambda: ["contract/text_encoder.safetensors"],
        "_comfy_vae_names": lambda: ["contract/vae.safetensors"],
        "_comfy_clip_loader_types": lambda: ["qwen_image", "stable_diffusion"],
        "_impact_scheduler_names": lambda: ["contract_impact_scheduler"],
        "_lora_combo_values": lambda: ["None", "contract/style.safetensors"],
        "resolve_metadata_filter_words": lambda: ["contract-filter"],
        "_prompt_translation_change_key": lambda: {"enabled": False},
        "wildcard_sources_signature": lambda: {"files": []},
        "resolve_naia_settings": lambda: {
            "use_naia_settings": False,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "host": "127.0.0.1",
            "port": 7243,
            "preprocessing": {},
            "allow_remote_api": False,
        },
    }
    with patch.multiple(nodes, **replacements), patch.object(
        sam3_nodes,
        "_comfy_checkpoint_names",
        return_value=["contract/checkpoint.safetensors"],
    ):
        yield


@contextmanager
def _loaded_package_entrypoint():
    package_name = "_easyuse_anima_contract_entrypoint"
    package_prefix = f"{package_name}."
    if any(name == package_name or name.startswith(package_prefix) for name in sys.modules):
        raise AssertionError(f"Synthetic package namespace is already loaded: {package_name}")

    package_spec = importlib.util.spec_from_file_location(
        package_name,
        PACKAGE_INIT,
        submodule_search_locations=[str(ROOT)],
    )
    if package_spec is None or package_spec.loader is None:
        raise AssertionError("Could not create package entrypoint spec")
    package_module = importlib.util.module_from_spec(package_spec)
    sys.modules[package_name] = package_module

    api_stub = types.ModuleType(f"{package_name}.api")
    sys.modules[api_stub.__name__] = api_stub
    package_module.api = api_stub

    try:
        nodes_spec = importlib.util.spec_from_file_location(
            f"{package_name}.nodes",
            ROOT / "nodes.py",
        )
        if nodes_spec is None or nodes_spec.loader is None:
            raise AssertionError("Could not create canonical package nodes spec")
        package_nodes = importlib.util.module_from_spec(nodes_spec)
        sys.modules[nodes_spec.name] = package_nodes
        nodes_spec.loader.exec_module(package_nodes)

        wildcard_module = sys.modules.get(f"{package_name}.wildcard_engine")
        if wildcard_module is None:
            raise AssertionError("Package nodes did not load wildcard_engine")
        with patch.object(wildcard_module, "ensure_default_wildcard_root", return_value=None):
            package_spec.loader.exec_module(package_module)
            yield package_module, package_nodes
    finally:
        for name in list(sys.modules):
            if name == package_name or name.startswith(package_prefix):
                sys.modules.pop(name, None)


def _node_contract(node_id: str, class_name: str, display_name: str) -> dict:
    node_class = getattr(nodes, class_name)
    input_types = node_class.INPUT_TYPES()
    sections = []
    for section_name, entries in input_types.items():
        sections.append(
            {
                "name": section_name,
                "entries": [
                    {
                        "name": input_name,
                        **_input_spec(spec),
                    }
                    for input_name, spec in entries.items()
                ],
            }
        )

    return {
        "id": node_id,
        "class_name": class_name,
        "display_name": display_name,
        "input_sections": sections,
        "return_types": _normalize(getattr(node_class, "RETURN_TYPES")),
        "return_names": _normalize(getattr(node_class, "RETURN_NAMES", None)),
        "function": getattr(node_class, "FUNCTION"),
        "category": getattr(node_class, "CATEGORY"),
        "output_node": bool(getattr(node_class, "OUTPUT_NODE", False)),
    }


def _representative_is_changed() -> list[dict]:
    input_context = nodes.EasyUseAnimaInput().build(
        {
            "positive_prompt": "contract prompt",
            "negative_prompt": "",
            "width": 1024,
            "height": 1024,
        },
        "contract/diffusion_model.safetensors",
        "contract/vae.safetensors",
        "contract/text_encoder.safetensors",
        "qwen_image",
        {},
    )[0]
    samples = (
        (
            "EasyUseAnimaPromptCorrector",
            {
                "prompt": "1girl, blue eyes",
                "artist_overrides": "",
                "artist_exclusions": "",
            },
        ),
        (
            "EasyUseAnimaWildcard",
            {
                "text": "plain contract prompt",
                "populated_text": "",
                "mode": "고정",
                "seed": 17,
            },
        ),
        (
            "EasyUseAnimaPromptStudioAdvancedV2",
            {
                "use_naia": False,
                "advanced_fields": "[]",
                "artist_mix_mode": "off",
            },
        ),
        (
            "EasyUseAnimaInput",
            {
                "EASYUSE_ANIMA_PROMPT_DATA": {
                    "positive_prompt": "contract prompt",
                    "negative_prompt": "",
                    "width": 1024,
                    "height": 1024,
                },
                "unet_name": "contract/diffusion_model.safetensors",
                "vae_name": "contract/vae.safetensors",
                "clip_name": "contract/text_encoder.safetensors",
                "clip_type": "qwen_image",
                "input_settings": {},
            },
        ),
        (
            "EasyUseAnimaAIOGenerator",
            {
                "easy_use_anima_input": input_context,
                "lora_stack": None,
                "generation_settings": {"sampler": {"seed": 17}},
            },
        ),
        (
            "EasyUseAnimaNAIARandomPrompt",
            {
                "use_naia_bridge": False,
                "prompt": "contract prompt",
                "negative_prompt": "",
                "width": 1024,
                "height": 1024,
            },
        ),
    )

    return [
        {
            "id": node_id,
            "inputs": _normalize(kwargs),
            "result": _normalize(getattr(nodes, node_id).IS_CHANGED(**kwargs)),
        }
        for node_id, kwargs in samples
    ]


def _workflow_nodes() -> list[dict]:
    snapshots = []
    for workflow_path, node_number, expected_type in WORKFLOW_SELECTIONS:
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow_node = next(
            node
            for node in workflow.get("nodes", [])
            if int(node.get("id")) == node_number
        )
        if workflow_node.get("type") != expected_type:
            raise AssertionError(
                f"{workflow_path.name}: node {node_number} changed type to {workflow_node.get('type')}"
            )
        snapshots.append(
            {
                "source": workflow_path.relative_to(ROOT).as_posix(),
                "node_number": node_number,
                "class_id": expected_type,
                "widgets_values": _normalize(workflow_node.get("widgets_values", [])),
            }
        )
    return snapshots


def build_contract_snapshot() -> dict:
    class_mappings, display_mappings = _root_mappings()
    if list(display_mappings) != [node_id for node_id, _class_name in class_mappings]:
        raise AssertionError("Class and display mapping order or keys diverged")

    with _deterministic_comfy_inputs():
        snapshot = {
            "schema_version": 1,
            "package_version": FIXTURE_PROVENANCE_VERSION,
            "dynamic_inputs": {
                "samplers": ["contract_sampler_a", "contract_sampler_b"],
                "schedulers": ["contract_scheduler_a", "contract_scheduler_b"],
                "impact_schedulers": ["contract_impact_scheduler"],
                "diffusion_models": ["contract/diffusion_model.safetensors"],
                "text_encoders": ["contract/text_encoder.safetensors"],
                "vae_models": ["contract/vae.safetensors"],
                "lora_models": ["None", "contract/style.safetensors"],
            },
            "nodes": [
                _node_contract(node_id, class_name, display_mappings[node_id])
                for node_id, class_name in class_mappings
            ],
            "is_changed": _representative_is_changed(),
            "workflow_nodes": _workflow_nodes(),
        }
    _assert_no_absolute_paths(snapshot)
    return snapshot


def _assert_no_absolute_paths(value, path: str = "fixture") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_no_absolute_paths(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_absolute_paths(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if _contains_absolute_path(value):
            raise AssertionError(f"Absolute path at {path}: {value}")


def write_fixture() -> None:
    snapshot = build_contract_snapshot()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


class CommonHelperMoveContractTests(unittest.TestCase):
    RETIRED_IMAGE_GEOMETRY_HELPERS = (
        "_align_up",
        "_aligned_size_near_scale",
        "_alignment_value",
    )
    HELPER_MODULES = (
        (
            common_values,
            ("_single_value", "_as_bool", "_as_int", "_as_float", "_choice"),
        ),
        (
            common_serialization,
            ("_stable_change_key", "_json_clone", "_json_object"),
        ),
        (
            image_geometry,
            ("_align_nearest", "_align_down"),
        ),
    )

    def test_root_nodes_private_aliases_are_canonical_objects(self):
        for canonical_module, helper_names in self.HELPER_MODULES:
            for helper_name in helper_names:
                with self.subTest(module=canonical_module.__name__, helper=helper_name):
                    self.assertIs(
                        getattr(nodes, helper_name),
                        getattr(canonical_module, helper_name),
                    )
        for helper_name in self.RETIRED_IMAGE_GEOMETRY_HELPERS:
            with self.subTest(retired=helper_name):
                self.assertFalse(hasattr(nodes, helper_name))

    def test_package_nodes_private_aliases_are_canonical_objects(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_geometry = sys.modules[
                f"{package_name}.easyuse_anima.image.geometry"
            ]
            package_helper_modules = (
                (
                    sys.modules[f"{package_name}.easyuse_anima.common.values"],
                    self.HELPER_MODULES[0][1],
                ),
                (
                    sys.modules[f"{package_name}.easyuse_anima.common.serialization"],
                    self.HELPER_MODULES[1][1],
                ),
                (
                    package_geometry,
                    self.HELPER_MODULES[2][1],
                ),
            )
            for canonical_module, helper_names in package_helper_modules:
                for helper_name in helper_names:
                    with self.subTest(module=canonical_module.__name__, helper=helper_name):
                        self.assertIs(
                            getattr(package_nodes, helper_name),
                            getattr(canonical_module, helper_name),
                        )
            for helper_name in self.RETIRED_IMAGE_GEOMETRY_HELPERS:
                with self.subTest(retired=helper_name):
                    self.assertFalse(hasattr(package_nodes, helper_name))
            self.assertEqual(package_geometry._alignment_value(["64"]), 64)
            self.assertIsNone(package_geometry._alignment_value("impact"))
            self.assertEqual(package_geometry._align_up(65, 64), 128)
            self.assertEqual(
                package_geometry._aligned_size_near_scale(128, 64, 2.0, 64, 0),
                (256, 128, 2.0),
            )

    def test_moved_helper_behavior_matches_existing_contract(self):
        self.assertEqual(nodes._single_value(["first", "second"]), "first")
        self.assertIsNone(nodes._single_value(()))
        self.assertTrue(nodes._as_bool(" enabled "))
        self.assertFalse(nodes._as_bool("false", True))
        self.assertEqual(nodes._as_int(["7"], 3), 7)
        self.assertEqual(nodes._as_int("invalid", 3), 3)
        self.assertEqual(nodes._as_float(["1.5"], 3.0), 1.5)
        self.assertEqual(nodes._choice(" beta ", ("alpha", "beta"), "alpha"), "beta")
        self.assertEqual(nodes._choice("missing", ("alpha", "beta"), "beta"), "beta")

        self.assertEqual(
            nodes._stable_change_key({"b": 2, "a": "한"}),
            '{"a":"한","b":2}',
        )
        source = {"nested": [{"value": "한"}]}
        clone = nodes._json_clone(source)
        self.assertEqual(clone, source)
        self.assertIsNot(clone, source)
        self.assertIsNot(clone["nested"], source["nested"])
        json_object_source = {"value": 1}
        self.assertEqual(nodes._json_object(json_object_source), json_object_source)
        self.assertIsNot(nodes._json_object(json_object_source), json_object_source)
        self.assertEqual(nodes._json_object('{"value": 1}'), {"value": 1})
        self.assertEqual(nodes._json_object("invalid"), {})

        self.assertEqual(image_geometry._alignment_value(["64"]), 64)
        self.assertIsNone(image_geometry._alignment_value("impact"))
        self.assertEqual(image_geometry._align_up(65, 64), 128)
        self.assertEqual(nodes._align_nearest(95, 64), 64)
        self.assertEqual(nodes._align_nearest(96, 64), 128)
        self.assertEqual(nodes._align_down(65, 64), 64)
        self.assertEqual(
            image_geometry._aligned_size_near_scale(128, 64, 2.0, 64, 0),
            (256, 128, 2.0),
        )


class ComfyAdapterMoveContractTests(unittest.TestCase):
    RETIRED_SAM3_SERVICE_HELPERS = (
        "_call_impact_detailer",
        "_empty_mask_for_image",
        "_empty_segs_for_image",
        "_find_impact_detailer_class",
        "_find_impact_mask_to_segs_class",
        "_find_sam3_detect_class",
        "_format_sam3_detection_prompt",
    )
    DIRECT_HELPER_MODULES = (
        (
            comfy_capabilities,
            ("_comfy_sampler_names", "_comfy_scheduler_names"),
        ),
        (
            comfy_resources,
            ("_folder_path_names",),
        ),
        (
            comfy_invocation,
            ("_node_output_tuple", "_call_with_supported_kwargs", "_common_upscale_image"),
        ),
    )

    def test_root_nodes_comfy_aliases_are_canonical_objects(self):
        for canonical_module, helper_names in self.DIRECT_HELPER_MODULES:
            for helper_name in helper_names:
                with self.subTest(module=canonical_module.__name__, helper=helper_name):
                    self.assertIs(
                        getattr(nodes, helper_name),
                        getattr(canonical_module, helper_name),
                    )

    def test_package_nodes_comfy_aliases_are_canonical_objects(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            self.assertFalse(hasattr(package_nodes, "_comfy_checkpoint_names"))
            self.assertFalse(hasattr(package_nodes, "_impact_core_module"))
            self.assertFalse(
                hasattr(package_nodes, "_EasyUseAnimaImpactDetailerDelegate")
            )
            for helper_name in self.RETIRED_SAM3_SERVICE_HELPERS:
                with self.subTest(retired=helper_name):
                    self.assertFalse(hasattr(package_nodes, helper_name))
            package_name = package_nodes.__package__
            package_capabilities = sys.modules[
                f"{package_name}.easyuse_anima.infrastructure.comfy.capabilities"
            ]
            package_sam3_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.sam3_nodes"
            ]
            package_impact_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.impact_detailer_nodes"
            ]
            package_resources = sys.modules[
                f"{package_name}.easyuse_anima.infrastructure.comfy.resources"
            ]
            self.assertIs(
                package_sam3_nodes._comfy_checkpoint_names,
                package_resources._comfy_checkpoint_names,
            )
            checkpoint_names = ["package/sam3.safetensors"]
            with (
                patch.object(
                    package_sam3_nodes,
                    "_comfy_checkpoint_names",
                    return_value=checkpoint_names,
                ),
                patch.object(
                    package_sam3_nodes,
                    "_preferred_checkpoint_default",
                    return_value="package/sam3.safetensors",
                ),
            ):
                input_types = package_sam3_nodes.EasyUseAnimaSAM3Context.INPUT_TYPES()
            self.assertIs(
                input_types["required"]["ckpt_name"][0],
                checkpoint_names,
            )
            self.assertEqual(
                input_types["required"]["ckpt_name"][1]["default"],
                "package/sam3.safetensors",
            )
            self.assertIs(
                package_sam3_nodes._EasyUseAnimaImpactDetailerDelegate,
                package_impact_nodes._EasyUseAnimaImpactDetailerDelegate,
            )
            with (
                patch.object(
                    package_impact_nodes,
                    "_comfy_max_resolution",
                    return_value=8192,
                ),
                patch.object(
                    package_impact_nodes,
                    "_comfy_sampler_names",
                    return_value=["package-sampler"],
                ),
                patch.object(
                    package_impact_nodes,
                    "_impact_scheduler_names",
                    return_value=["package-scheduler"],
                ),
            ):
                detailer_inputs = (
                    package_sam3_nodes._EasyUseAnimaImpactDetailerDelegate.INPUT_TYPES()
                )
            self.assertEqual(
                detailer_inputs["required"]["guide_size"][1]["max"],
                8192,
            )
            self.assertEqual(
                detailer_inputs["required"]["sampler_name"][0],
                ["package-sampler"],
            )
            self.assertEqual(
                detailer_inputs["required"]["scheduler"][0],
                ["package-scheduler"],
            )
            with patch.object(
                package_capabilities,
                "_impact_core_module",
                return_value=types.SimpleNamespace(
                    get_schedulers=lambda: ("package-impact",)
                ),
            ) as impact_core:
                self.assertEqual(
                    package_capabilities._impact_scheduler_names(),
                    ["package-impact"],
                )
            impact_core.assert_called_once_with()
            package_helper_modules = (
                (
                    package_capabilities,
                    self.DIRECT_HELPER_MODULES[0][1],
                ),
                (
                    sys.modules[
                        f"{package_name}.easyuse_anima.infrastructure.comfy.resources"
                    ],
                    self.DIRECT_HELPER_MODULES[1][1],
                ),
                (
                    sys.modules[
                        f"{package_name}.easyuse_anima.infrastructure.comfy.invocation"
                    ],
                    self.DIRECT_HELPER_MODULES[2][1],
                ),
            )
            for canonical_module, helper_names in package_helper_modules:
                for helper_name in helper_names:
                    with self.subTest(module=canonical_module.__name__, helper=helper_name):
                        self.assertIs(
                            getattr(package_nodes, helper_name),
                            getattr(canonical_module, helper_name),
                        )


class ImageNodeMoveContractTests(unittest.TestCase):
    RETAINED_SCALING_ALIASES = (
        "IMAGE_SCALE_MULTIPLES",
        "IMAGE_UPSCALE_METHODS",
    )
    RETIRED_SCALING_HELPERS = (
        "_image_scale_by_multiple_size",
        "_max_long_edge_value",
        "_normalize_image_scale_options",
        "_scale_by_value",
    )

    def test_root_nodes_image_objects_are_direct_canonical_aliases(self):
        for name in self.RETAINED_SCALING_ALIASES:
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(image_scaling, name))
        for name in self.RETIRED_SCALING_HELPERS:
            with self.subTest(retired=name):
                self.assertFalse(hasattr(nodes, name))

        self.assertFalse(hasattr(nodes, "_EasyUseAnimaAlignedDetailerHook"))
        self.assertIs(
            image_nodes._EasyUseAnimaAlignedDetailerHook,
            image_detailer._EasyUseAnimaAlignedDetailerHook,
        )
        self.assertIs(
            impact_detailer_nodes._EasyUseAnimaAlignedDetailerHook,
            image_detailer._EasyUseAnimaAlignedDetailerHook,
        )
        aligned_hook = image_nodes.EasyUseAnimaDetailerAlignHook().build(
            alignment="32",
            detailer_hook="existing-hook",
        )[0]
        self.assertIsInstance(
            aligned_hook,
            image_detailer._EasyUseAnimaAlignedDetailerHook,
        )
        self.assertEqual(aligned_hook.base_hook, "existing-hook")
        self.assertEqual(aligned_hook.alignment, 32)
        self.assertIs(
            nodes.EasyUseAnimaImageScaleByMultiple,
            image_nodes.EasyUseAnimaImageScaleByMultiple,
        )
        self.assertIs(
            nodes.EasyUseAnimaDetailerAlignHook,
            image_nodes.EasyUseAnimaDetailerAlignHook,
        )
        self.assertIs(image_nodes._common_upscale_image, comfy_invocation._common_upscale_image)

    def test_package_loaded_root_nodes_image_objects_are_direct_canonical_aliases(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            self.assertFalse(
                hasattr(package_nodes, "_EasyUseAnimaAlignedDetailerHook")
            )
            package_name = package_nodes.__package__
            package_scaling = sys.modules[f"{package_name}.easyuse_anima.image.scaling"]
            package_detailer = sys.modules[f"{package_name}.easyuse_anima.image.detailer"]
            package_invocation = sys.modules[
                f"{package_name}.easyuse_anima.infrastructure.comfy.invocation"
            ]
            package_node_adapters = sys.modules[
                f"{package_name}.easyuse_anima.nodes.image_nodes"
            ]
            package_impact_adapters = sys.modules[
                f"{package_name}.easyuse_anima.nodes.impact_detailer_nodes"
            ]
            for name in self.RETAINED_SCALING_ALIASES:
                with self.subTest(name=name):
                    self.assertIs(
                        getattr(package_nodes, name),
                        getattr(package_scaling, name),
                    )
            for name in self.RETIRED_SCALING_HELPERS:
                with self.subTest(retired=name):
                    self.assertFalse(hasattr(package_nodes, name))
            self.assertEqual(package_scaling._scale_by_value("1.25"), 1.25)
            self.assertEqual(package_scaling._max_long_edge_value("20000"), 16384)
            self.assertEqual(
                package_scaling._normalize_image_scale_options(
                    "32", "32", "bicubic"
                ),
                ("bicubic", "32", 0),
            )
            self.assertEqual(
                package_scaling._image_scale_by_multiple_size(
                    1024, 1536, 1.25, "32"
                ),
                (1280, 1920, 1.25),
            )

            self.assertIs(
                package_node_adapters._EasyUseAnimaAlignedDetailerHook,
                package_detailer._EasyUseAnimaAlignedDetailerHook,
            )
            self.assertIs(
                package_impact_adapters._EasyUseAnimaAlignedDetailerHook,
                package_detailer._EasyUseAnimaAlignedDetailerHook,
            )
            aligned_hook = package_node_adapters.EasyUseAnimaDetailerAlignHook().build(
                alignment="32",
                detailer_hook=None,
            )[0]
            self.assertIs(
                type(aligned_hook),
                package_detailer._EasyUseAnimaAlignedDetailerHook,
            )
            for name in (
                "EasyUseAnimaDetailerAlignHook",
                "EasyUseAnimaImageScaleByMultiple",
            ):
                with self.subTest(name=name):
                    canonical_class = getattr(package_node_adapters, name)
                    self.assertIs(getattr(package_nodes, name), canonical_class)
            self.assertIs(
                package_node_adapters._common_upscale_image,
                package_invocation._common_upscale_image,
            )


class WildcardNaiaMoveContractTests(unittest.TestCase):
    RETIRED_CLIENT_ALIASES = (
        "DEFAULT_HOST",
        "DEFAULT_PORT",
        "HTTP_TIMEOUT",
        "NAI_1MP",
        "NAIA_LOCAL_HOSTS",
        "NAIA_MAX_RESOLUTION",
        "NAIA_REQUEST_TIMEOUT",
        "PP_STATE_CHOICES",
        "PREPROCESSING_KEYS",
        "_build_naia_random_url",
        "_clean_prompt",
        "_fit_to_1mp",
        "_is_local_naia_host",
    )
    RETAINED_CLIENT_ALIASES = (
        "LATENT_ALIGN",
        "_parse_random_response",
        "_post_random",
    )
    RETIRED_RESOLUTION_ALIASES = (
        "ADVANCED_RESOLUTION_BUCKETS",
        "CUSTOM_ADVANCED_RESOLUTION_BUCKET",
        "DEFAULT_ADVANCED_RESOLUTION_BUCKET",
        "DEFAULT_ADVANCED_RESOLUTION_SIZE",
        "NAIA_ADVANCED_RESOLUTION_BUCKET",
        "NAIA_RESOLUTION_MODE_BUCKET",
        "NAIA_RESOLUTION_MODE_SCALE",
        "_fit_naia_resolution_to_bucket",
        "_resolve_naia_resolution_bucket",
        "_resolve_naia_resolution_max_long_edge",
        "_resolve_naia_resolution_mode",
        "_resolve_naia_resolution_scale",
        "_scale_naia_resolution",
        "_snap_resolution_32",
        "_snap_scaled_resolution_32",
        "_sorted_resolution_options",
    )
    RETAINED_RESOLUTION_ALIASES = (
        "_advanced_resolution_from_selection",
        "_normalize_resolution_bucket",
        "_ratio_label",
        "_resolution_label",
        "_resolve_naia_resolution",
    )

    def test_root_nodes_wildcard_naia_objects_are_direct_canonical_aliases(self):
        for name in self.RETIRED_CLIENT_ALIASES:
            with self.subTest(retired=name):
                self.assertFalse(hasattr(nodes, name))
        for name in self.RETAINED_CLIENT_ALIASES:
            with self.subTest(module="client", name=name):
                self.assertIs(getattr(nodes, name), getattr(naia_client, name))
        for name in self.RETIRED_RESOLUTION_ALIASES:
            with self.subTest(retired=name):
                self.assertFalse(hasattr(nodes, name))
        for name in self.RETAINED_RESOLUTION_ALIASES:
            with self.subTest(module="resolution", name=name):
                self.assertIs(getattr(nodes, name), getattr(naia_resolution, name))

        self.assertIs(
            nodes.EasyUseAnimaWildcard,
            wildcard_nodes.EasyUseAnimaWildcard,
        )
        self.assertIs(
            nodes.EasyUseAnimaNAIARandomPrompt,
            naia_nodes.EasyUseAnimaNAIARandomPrompt,
        )
        self.assertFalse(hasattr(nodes, "WILDCARD_SEED_RANGE_NOTE"))
        self.assertIn(
            wildcard_nodes.WILDCARD_SEED_RANGE_NOTE,
            wildcard_nodes.EasyUseAnimaWildcard.INPUT_TYPES()["required"]["seed"][1][
                "tooltip"
            ],
        )

    def test_package_loaded_root_wildcard_naia_objects_are_direct_canonical_aliases(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_client = sys.modules[f"{package_name}.easyuse_anima.naia.client"]
            package_resolution = sys.modules[f"{package_name}.easyuse_anima.naia.resolution"]
            package_naia_nodes = sys.modules[f"{package_name}.easyuse_anima.nodes.naia_nodes"]
            package_wildcard_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.wildcard_nodes"
            ]

            for name in self.RETIRED_CLIENT_ALIASES:
                with self.subTest(retired=name):
                    self.assertFalse(hasattr(package_nodes, name))
            for name in self.RETAINED_CLIENT_ALIASES:
                with self.subTest(module="client", name=name):
                    self.assertIs(getattr(package_nodes, name), getattr(package_client, name))
            for name in self.RETIRED_RESOLUTION_ALIASES:
                with self.subTest(retired=name):
                    self.assertFalse(hasattr(package_nodes, name))
            for name in self.RETAINED_RESOLUTION_ALIASES:
                with self.subTest(module="resolution", name=name):
                    self.assertIs(
                        getattr(package_nodes, name),
                        getattr(package_resolution, name),
                    )
            self.assertIs(
                package_nodes.EasyUseAnimaWildcard,
                package_wildcard_nodes.EasyUseAnimaWildcard,
            )
            self.assertIs(
                package_nodes.EasyUseAnimaNAIARandomPrompt,
                package_naia_nodes.EasyUseAnimaNAIARandomPrompt,
            )
            self.assertFalse(hasattr(package_nodes, "WILDCARD_SEED_RANGE_NOTE"))


class LoraPresetMoveContractTests(unittest.TestCase):
    METADATA_HELPERS = (
        "_apply_lora_syntax_format",
        "_fallback_lora_path",
        "_lora_stack_name",
        "_dedupe_text_values",
        "_trigger_words_from_value",
        "_metadata_json_paths_for_lora",
        "_load_lora_manager_metadata",
        "_lora_manager_trigger_words_from_metadata",
        "_get_lora_manager_trigger_words",
        "_get_lora_info",
        "_lora_combo_values",
        "_lora_model_exists",
        "_missing_lora_display_name",
        "_raise_missing_loras",
    )
    PRESET_HELPERS = (
        "_profile_key",
        "_wrap_profile_index",
        "_load_profile_data",
        "_get_loras_list",
        "_correct_style_prompt",
        "_format_strength",
        "_select_profile_values",
    )

    def test_root_lora_objects_are_direct_canonical_aliases(self):
        for name in self.METADATA_HELPERS:
            with self.subTest(module="metadata", name=name):
                self.assertIs(getattr(nodes, name), getattr(lora_metadata, name))
        for name in self.PRESET_HELPERS:
            with self.subTest(module="preset", name=name):
                self.assertIs(getattr(nodes, name), getattr(lora_preset, name))
        self.assertIs(nodes.EasyUseAnimaLoraPreset, lora_nodes.EasyUseAnimaLoraPreset)

    def test_package_loaded_root_lora_objects_are_direct_canonical_aliases(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_metadata = sys.modules[f"{package_name}.easyuse_anima.lora.metadata"]
            package_preset = sys.modules[f"{package_name}.easyuse_anima.lora.preset"]
            package_lora_nodes = sys.modules[f"{package_name}.easyuse_anima.nodes.lora_nodes"]

            for name in self.METADATA_HELPERS:
                with self.subTest(module="metadata", name=name):
                    self.assertIs(getattr(package_nodes, name), getattr(package_metadata, name))
            for name in self.PRESET_HELPERS:
                with self.subTest(module="preset", name=name):
                    self.assertIs(getattr(package_nodes, name), getattr(package_preset, name))
            self.assertIs(
                package_nodes.EasyUseAnimaLoraPreset,
                package_lora_nodes.EasyUseAnimaLoraPreset,
            )

    def test_root_monkeypatches_drive_the_canonical_lora_node(self):
        canonical_node = lora_nodes.EasyUseAnimaLoraPreset()
        with (
            patch.object(nodes, "_correct_style_prompt", side_effect=lambda value: f"bound:{value}"),
            patch.object(nodes, "_get_lora_info", return_value=("foo.safetensors", ["@bound"])),
            patch.object(nodes, "_lora_model_exists", return_value=True),
        ):
            result = canonical_node.build(
                style_prompt="style",
                profile_index=1,
                loras='[{"name":"foo.safetensors","strength":1}]',
                profile_data="{}",
            )["result"]

        self.assertEqual(result[0], "bound:style")
        self.assertEqual(result[2], "@bound")

    def test_fresh_process_direct_imports_do_not_load_root_nodes(self):
        script = f"""
import importlib
import json
import sys
sys.path.insert(0, {str(ROOT)!r})
sys.dont_write_bytecode = True
modules = [
    importlib.import_module("easyuse_anima.lora.metadata"),
    importlib.import_module("easyuse_anima.lora.preset"),
    importlib.import_module("easyuse_anima.nodes.lora_nodes"),
]
print(json.dumps({{
    "class_module": modules[-1].EasyUseAnimaLoraPreset.__module__,
    "root_nodes_loaded": "nodes" in sys.modules,
}}))
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["class_module"], "easyuse_anima.nodes.lora_nodes")
        self.assertFalse(payload["root_nodes_loaded"])


class PromptCorrectorMoveContractTests(unittest.TestCase):
    CORRECTION_HELPERS = (
        "_split_tag_text",
        "_translate_prompt_text",
        "_prompt_translation_change_key",
    )
    NODE_CLASSES = (
        "EasyUseAnimaPromptCorrector",
        "EasyUseAnimaPromptCorrectorSimple",
    )

    def test_root_prompt_corrector_objects_are_direct_canonical_aliases(self):
        for name in self.CORRECTION_HELPERS:
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(prompt_correction, name))
        for name in self.NODE_CLASSES:
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(prompt_nodes, name))

    def test_package_loaded_root_prompt_corrector_objects_are_direct_canonical_aliases(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_correction = sys.modules[
                f"{package_name}.easyuse_anima.prompt.correction"
            ]
            package_prompt_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.prompt_nodes"
            ]

            for name in self.CORRECTION_HELPERS:
                with self.subTest(name=name):
                    self.assertIs(getattr(package_nodes, name), getattr(package_correction, name))
            for name in self.NODE_CLASSES:
                with self.subTest(name=name):
                    self.assertIs(getattr(package_nodes, name), getattr(package_prompt_nodes, name))

    def test_root_monkeypatches_drive_the_canonical_prompt_corrector_nodes(self):
        settings = types.SimpleNamespace(provider="off", source="auto", target="en")
        correction_result = types.SimpleNamespace(
            text="canonical result",
            changed=True,
            unknown_tags=("unknown",),
            duplicate_tags=("duplicate",),
            warnings=("warning",),
            report={"sections": ["count", "general"]},
        )

        with (
            patch.object(
                nodes,
                "resolve_prompt_translation_settings",
                return_value=settings,
            ) as resolve_settings,
            patch.object(
                nodes,
                "_prompt_translation_change_key",
                return_value={"bound": "translation"},
            ) as translation_key,
            patch.object(nodes, "_stable_change_key", side_effect=lambda payload: payload) as stable_key,
            patch.object(nodes, "load_knowledge_base", return_value="bound kb") as load_kb,
            patch.object(nodes, "correct_prompt", return_value=correction_result) as correct,
        ):
            change_key = prompt_nodes.EasyUseAnimaPromptCorrector.IS_CHANGED(
                prompt="%{bound prompt}",
                artist_overrides="artist_a\nartist_b",
                artist_exclusions="artist_c",
            )
            corrected, report_text = prompt_nodes.EasyUseAnimaPromptCorrector().correct(
                "%{bound prompt}",
                "artist_a\nartist_b",
                "artist_c",
            )

        self.assertEqual(change_key["prompt_translation"], {"bound": "translation"})
        translation_key.assert_called_once_with()
        stable_key.assert_called_once_with(change_key)
        resolve_settings.assert_called_once_with()
        load_kb.assert_called_once_with(allow_missing=True)
        correct.assert_called_once_with(
            "bound prompt",
            profile="prompt",
            knowledge_base="bound kb",
            validate_artist_tags=False,
            artist_overrides=["artist_a", "artist_b"],
            artist_exclusions=["artist_c"],
        )
        self.assertEqual(corrected, "canonical result")
        report = json.loads(report_text, object_pairs_hook=dict)
        self.assertEqual(
            list(report),
            ["changed", "unknown_tags", "duplicate_tags", "warnings", "sections"],
        )

    def test_root_translation_monkeypatches_drive_the_canonical_helper(self):
        settings = types.SimpleNamespace(provider="off", source="auto", target="en")

        with (
            patch.object(
                nodes,
                "has_prompt_translation_markers",
                return_value=False,
            ) as has_markers,
            patch.object(nodes, "translate_prompt_markers") as translate_markers,
        ):
            untranslated = nodes._translate_prompt_text("%{abc}")

        self.assertEqual(untranslated, "%{abc}")
        has_markers.assert_called_once_with("%{abc}")
        translate_markers.assert_not_called()

        with (
            patch.object(
                nodes,
                "has_prompt_translation_markers",
                return_value=True,
            ) as has_markers,
            patch.object(
                nodes,
                "translate_prompt_markers",
                return_value="bound",
            ) as translate_markers,
            patch.object(
                nodes,
                "resolve_prompt_translation_settings",
                return_value=settings,
            ) as resolve_settings,
        ):
            translated = nodes._translate_prompt_text("%{abc}")

        self.assertEqual(translated, "bound")
        has_markers.assert_called_once_with("%{abc}")
        resolve_settings.assert_called_once_with()
        translate_markers.assert_called_once_with("%{abc}", settings)

    def test_translation_stays_outside_the_correction_error_mapping(self):
        with patch.object(nodes, "_translate_prompt_text", side_effect=ValueError("translate")):
            with self.assertRaisesRegex(ValueError, "^translate$"):
                prompt_nodes.EasyUseAnimaPromptCorrector().correct("prompt", "", "")

        with patch.object(nodes, "load_knowledge_base", side_effect=ValueError("correct")):
            with self.assertRaisesRegex(
                RuntimeError,
                r"^\[EasyUse Anima\] prompt correction failed: correct$",
            ):
                prompt_nodes.EasyUseAnimaPromptCorrector().correct("prompt", "", "")

    def test_public_nodes_share_the_private_correction_adapter(self):
        with patch.object(
            prompt_nodes,
            "_correct_prompt_with_report",
            return_value=("shared", "{}"),
        ) as adapter:
            full = prompt_nodes.EasyUseAnimaPromptCorrector().correct("prompt", "a", "b")
            simple = prompt_nodes.EasyUseAnimaPromptCorrectorSimple().correct("prompt")

        self.assertEqual(full, ("shared", "{}"))
        self.assertEqual(simple, ("shared",))
        self.assertEqual(
            adapter.call_args_list,
            [
                call("prompt", "a", "b"),
                call("prompt", "", ""),
            ],
        )

    def test_fresh_process_direct_imports_do_not_load_root_nodes(self):
        script = f"""
import importlib
import json
import sys
sys.path.insert(0, {str(ROOT)!r})
sys.dont_write_bytecode = True
modules = [
    importlib.import_module("easyuse_anima.prompt.correction"),
    importlib.import_module("easyuse_anima.nodes.prompt_nodes"),
]
print(json.dumps({{
    "class_modules": [
        modules[-1].EasyUseAnimaPromptCorrector.__module__,
        modules[-1].EasyUseAnimaPromptCorrectorSimple.__module__,
    ],
    "root_nodes_loaded": "nodes" in sys.modules,
}}))
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["class_modules"],
            ["easyuse_anima.nodes.prompt_nodes", "easyuse_anima.nodes.prompt_nodes"],
        )
        self.assertFalse(payload["root_nodes_loaded"])


class PromptDataConditioningMoveContractTests(unittest.TestCase):
    RETIRED_PROMPT_DATA_ALIASES = (
        "PROMPT_DATA_COMPAT_OUTPUT_TOOLTIPS",
        "PROMPT_DATA_COMPAT_RETURN_NAMES",
        "PROMPT_DATA_COMPAT_RETURN_TYPES",
        "PROMPT_DATA_SCHEMA",
        "PROMPT_DATA_VERSION",
        "_prompt_data_input_default",
        "_prompt_data_nested",
        "_prompt_data_output",
        "_set_prompt_data_output",
    )
    RETIRED_CONDITIONING_ALIASES = (
        "ANIMA_MOD_GUIDANCE_MODE_DISABLED",
        "ANIMA_MOD_GUIDANCE_MODE_ENABLED",
        "ANIMA_MOD_GUIDANCE_PROFILES",
        "_SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED",
        "_warn_old_spectrum_anima_mod_guidance_once",
    )
    NODE_CLASSES = (
        "EasyUseAnimaPromptDataUnpack",
        "EasyUseAnimaArtistMixConditioning",
        "EasyUseAnimaPromptDataConditioning",
    )
    MOVED_HELPERS = {
        prompt_data: (
            "_normalize_prompt_data",
            "_prompt_data_parameter_snapshot",
            "_advanced_outputs_from_prompt_data",
            "_apply_prompt_data_overrides",
        ),
        prompt_artist_mix: (
            "_parse_artist_mix_items",
            "_artist_prompt_with_position",
            "_blend_conditionings",
            "_encode_artist_delta_rms",
            "_encode_artist_clustered",
            "_encode_prompt_data_positive_conditioning",
        ),
        prompt_conditioning: (
            "_find_spectrum_anima_mod_guidance_class",
            "_resolve_anima_mod_guidance_enabled",
            "_normalize_anima_mod_guidance_profile",
            "_apply_spectrum_anima_mod_guidance",
        ),
    }

    def test_root_prompt_data_conditioning_objects_are_direct_canonical_aliases(self):
        for name in (
            *self.RETIRED_PROMPT_DATA_ALIASES,
            *self.RETIRED_CONDITIONING_ALIASES,
        ):
            with self.subTest(retired=name):
                self.assertFalse(hasattr(nodes, name))
        for name in self.NODE_CLASSES:
            with self.subTest(module="prompt_data_nodes", name=name):
                self.assertIs(getattr(nodes, name), getattr(prompt_data_nodes, name))
        for module, names in self.MOVED_HELPERS.items():
            for name in names:
                with self.subTest(module=module.__name__, name=name):
                    self.assertIs(getattr(nodes, name), getattr(module, name))

    def test_package_entrypoint_mappings_keep_canonical_class_identity_and_display(self):
        expected_display = {
            "EasyUseAnimaPromptDataUnpack": nodes.PROMPT_DATA_TYPE,
            "EasyUseAnimaArtistMixConditioning": "Anima Artist Mix Conditioning",
            "EasyUseAnimaPromptDataConditioning": "Anima Prompt Data Conditioning",
        }
        with _loaded_package_entrypoint() as (package_entry, package_nodes):
            package_name = package_nodes.__package__
            package_adapters = sys.modules[
                f"{package_name}.easyuse_anima.nodes.prompt_data_nodes"
            ]
            for name in (
                *self.RETIRED_PROMPT_DATA_ALIASES,
                *self.RETIRED_CONDITIONING_ALIASES,
            ):
                with self.subTest(retired=name):
                    self.assertFalse(hasattr(package_nodes, name))
            for name in self.NODE_CLASSES:
                with self.subTest(name=name):
                    canonical_class = getattr(package_adapters, name)
                    self.assertIs(getattr(package_nodes, name), canonical_class)
                    self.assertIs(package_entry.NODE_CLASS_MAPPINGS[name], canonical_class)
                    self.assertEqual(
                        package_entry.NODE_DISPLAY_NAME_MAPPINGS[name],
                        expected_display[name],
                    )

    def test_unpack_contract_is_fixed_without_importing_advanced_from_root(self):
        self.assertEqual(
            prompt_data_nodes.EasyUseAnimaPromptDataUnpack.OUTPUT_TOOLTIPS,
            (
                "Pass-through prompt data for downstream prompt-data nodes.",
                *prompt_data.PROMPT_DATA_COMPAT_OUTPUT_TOOLTIPS,
            ),
        )
        self.assertEqual(
            prompt_data_nodes.EasyUseAnimaPromptDataUnpack.RETURN_TYPES,
            (nodes.PROMPT_DATA_TYPE, *nodes.EasyUseAnimaPromptStudioAdvanced.RETURN_TYPES),
        )
        self.assertEqual(
            prompt_data_nodes.EasyUseAnimaPromptDataUnpack.RETURN_NAMES,
            (nodes.PROMPT_DATA_TYPE, *nodes.EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES),
        )

    def test_root_change_key_monkeypatch_drives_canonical_adapter(self):
        with patch.object(nodes, "_stable_change_key", side_effect=lambda value: value) as stable:
            change_key = prompt_data_nodes.EasyUseAnimaPromptDataUnpack.IS_CHANGED(
                {nodes.PROMPT_DATA_TYPE: True}
            )

        self.assertEqual(change_key["mode"], "prompt_data_unpack")
        self.assertEqual(change_key["prompt_data"], {nodes.PROMPT_DATA_TYPE: True})
        stable.assert_called_once_with(change_key)

    def test_fresh_process_direct_imports_do_not_load_root_nodes(self):
        script = f"""
import importlib
import json
import sys
sys.path.insert(0, {str(ROOT)!r})
sys.dont_write_bytecode = True
modules = [
    importlib.import_module("easyuse_anima.prompt.data"),
    importlib.import_module("easyuse_anima.prompt.artist_mix"),
    importlib.import_module("easyuse_anima.prompt.conditioning"),
    importlib.import_module("easyuse_anima.nodes.prompt_data_nodes"),
]
print(json.dumps({{
    "class_modules": [
        modules[-1].EasyUseAnimaPromptDataUnpack.__module__,
        modules[-1].EasyUseAnimaArtistMixConditioning.__module__,
        modules[-1].EasyUseAnimaPromptDataConditioning.__module__,
    ],
    "root_nodes_loaded": "nodes" in sys.modules,
}}))
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["class_modules"],
            ["easyuse_anima.nodes.prompt_data_nodes"] * 3,
        )
        self.assertFalse(payload["root_nodes_loaded"])


class PromptBuilderStudioMoveContractTests(unittest.TestCase):
    RETIRED_FIELD_DEFAULTS = (
        "DEFAULT_QUALITY_TAGS",
        "DEFAULT_TRAILING_QUALITY_TAGS",
    )
    FIELD_OBJECTS = (
        "_HASH_COMMENT_RE",
        "_INLINE_SPACE_RE",
        "_WEIGHTED_TOKEN_RE",
        "_prompt_tokens",
        "_join_prompt_tokens",
        "_correct_builder_prompt",
        "_metadata_filter_key",
        "_metadata_filter_keys",
        "_filter_metadata_prompt",
    )
    NODE_CLASSES = (
        "EasyUseAnimaPromptBuilder",
        "EasyUseAnimaPromptStudio",
    )

    def test_root_prompt_builder_studio_objects_are_direct_canonical_aliases(self):
        for name in self.RETIRED_FIELD_DEFAULTS:
            with self.subTest(retired=name):
                self.assertFalse(hasattr(nodes, name))
        for name in self.FIELD_OBJECTS:
            with self.subTest(module="fields", name=name):
                self.assertIs(getattr(nodes, name), getattr(prompt_fields, name))
        for name in self.NODE_CLASSES:
            with self.subTest(module="prompt_nodes", name=name):
                self.assertIs(getattr(nodes, name), getattr(prompt_nodes, name))

    def test_package_loaded_root_prompt_builder_studio_objects_are_direct_aliases(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_fields = sys.modules[f"{package_name}.easyuse_anima.prompt.fields"]
            package_prompt_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.prompt_nodes"
            ]

            for name in self.RETIRED_FIELD_DEFAULTS:
                with self.subTest(retired=name):
                    self.assertFalse(hasattr(package_nodes, name))
            for name in self.FIELD_OBJECTS:
                with self.subTest(module="fields", name=name):
                    self.assertIs(getattr(package_nodes, name), getattr(package_fields, name))
            for name in self.NODE_CLASSES:
                with self.subTest(module="prompt_nodes", name=name):
                    self.assertIs(
                        getattr(package_nodes, name),
                        getattr(package_prompt_nodes, name),
                    )

    def test_classic_studio_directly_inherits_the_canonical_builder(self):
        self.assertEqual(
            prompt_nodes.EasyUseAnimaPromptStudio.__bases__,
            (prompt_nodes.EasyUseAnimaPromptBuilder,),
        )
        self.assertTrue(
            issubclass(
                nodes.EasyUseAnimaPromptStudio,
                nodes.EasyUseAnimaPromptBuilder,
            )
        )

    def test_root_parser_and_correction_monkeypatches_drive_canonical_fields(self):
        parsed = types.SimpleNamespace(tokens=("  bound_token  ",))
        correction_result = types.SimpleNamespace(text="bound correction")

        with patch.object(nodes, "parse_prompt", return_value=parsed) as parser:
            tokens = prompt_fields._prompt_tokens("source")

        self.assertEqual(tokens, ["bound_token"])
        parser.assert_called_once_with("source", profile="prompt")

        with (
            patch.object(nodes, "_prompt_tokens", return_value=["bound_artist"]) as tokens,
            patch.object(nodes, "load_knowledge_base", return_value="bound kb") as load_kb,
            patch.object(nodes, "correct_prompt", return_value=correction_result) as correct,
        ):
            corrected = prompt_fields._correct_builder_prompt("prompt", "artist")

        self.assertEqual(corrected, "bound correction")
        tokens.assert_called_once_with("artist")
        load_kb.assert_called_once_with(allow_missing=True)
        correct.assert_called_once_with(
            "prompt",
            profile="prompt",
            knowledge_base="bound kb",
            validate_artist_tags=False,
            artist_overrides=["bound_artist"],
        )

    def test_root_monkeypatches_drive_canonical_builder_order_and_change_key(self):
        with (
            patch.object(nodes, "_stable_change_key", side_effect=lambda value: value) as stable,
            patch.object(
                nodes,
                "_prompt_translation_change_key",
                return_value={"bound": "translation"},
            ) as translation_key,
            patch.object(
                nodes,
                "resolve_metadata_filter_words",
                return_value="bound filters",
            ) as resolve_filter,
        ):
            change_key = prompt_nodes.EasyUseAnimaPromptBuilder.IS_CHANGED(prompt="source")

        self.assertEqual(change_key["mode"], "prompt_builder")
        self.assertEqual(change_key["metadata_filter_words"], "bound filters")
        self.assertEqual(change_key["prompt_translation"], {"bound": "translation"})
        self.assertEqual(change_key["prompt"], "source")
        stable.assert_called_once_with(change_key)
        translation_key.assert_called_once_with()
        resolve_filter.assert_called_once_with()

        with (
            patch.object(nodes, "_as_bool", side_effect=(True, False)),
            patch.object(nodes, "_translate_prompt_text", side_effect=lambda value: f"t:{value}"),
            patch.object(nodes, "_join_prompt_tokens", side_effect=lambda *parts: "|".join(parts)),
            patch.object(
                nodes,
                "_correct_builder_prompt",
                side_effect=lambda value, artist_overrides="": f"c:{value}:{artist_overrides}",
            ),
            patch.object(
                nodes,
                "_filter_metadata_prompt",
                side_effect=lambda prompt, words: f"f:{prompt}:{words}",
            ),
            patch.object(nodes, "resolve_metadata_filter_words", return_value="filters"),
        ):
            result = prompt_nodes.EasyUseAnimaPromptBuilder().build(
                True,
                False,
                "quality",
                "trigger",
                "lora",
                "body",
                "trailing",
            )

        self.assertEqual(
            result,
            (
                "c:t:trigger|t:lora|t:body:t:trigger|t:lora|t:trailing",
                "t:quality",
                True,
                (
                    "f:c:t:quality|t:trigger|t:lora|t:body:"
                    "t:trigger|t:lora|t:trailing:filters"
                ),
            ),
        )

    def test_fresh_process_direct_imports_do_not_load_root_nodes(self):
        script = f"""
import importlib
import json
import sys
sys.path.insert(0, {str(ROOT)!r})
sys.dont_write_bytecode = True
fields = importlib.import_module("easyuse_anima.prompt.fields")
prompt_nodes = importlib.import_module("easyuse_anima.nodes.prompt_nodes")
print(json.dumps({{
    "class_modules": [
        prompt_nodes.EasyUseAnimaPromptBuilder.__module__,
        prompt_nodes.EasyUseAnimaPromptStudio.__module__,
    ],
    "helper_module": fields._prompt_tokens.__module__,
    "root_nodes_loaded": "nodes" in sys.modules,
}}))
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["class_modules"],
            ["easyuse_anima.nodes.prompt_nodes", "easyuse_anima.nodes.prompt_nodes"],
        )
        self.assertEqual(payload["helper_module"], "easyuse_anima.prompt.fields")
        self.assertFalse(payload["root_nodes_loaded"])


class PromptAdvancedMoveContractTests(unittest.TestCase):
    RETIRED_NODE_CLASSES = (
        "EasyUseAnimaPromptStudioExtend",
    )
    RETIRED_ADVANCED_ALIASES = (
        "ADVANCED_FIELDS_WORKFLOW_PROPERTY",
        "ADVANCED_FIELD_LABELS",
        "ADVANCED_FIELD_PANES",
        "ADVANCED_FIELD_TYPES",
        "EXTEND_PROMPT_SLOT_SPECS",
        "PROMPT_STUDIO_ADVANCED_RETURN_NAMES",
        "PROMPT_STUDIO_ADVANCED_RETURN_TYPES",
        "PROMPT_STUDIO_LEGACY_FIXED_WILDCARD_MODES",
        "PROMPT_STUDIO_WILDCARD_SEED_CONTROL_ALIASES",
        "_advanced_fields_with_artist_override",
        "_advanced_pane_parts",
        "_advanced_prompt_data_fields",
    )
    SERVICE_OBJECTS = (
        "_normalize_prompt_studio_wildcard_seed_control",
        "_translate_prompt_fields",
        "_advanced_default_fields",
        "_advanced_fields_json",
        "_normalize_advanced_fields",
        "_clone_advanced_fields",
        "_advanced_field_input_values",
        "_apply_advanced_field_inputs",
        "_build_advanced_prompts",
        "_expand_advanced_wildcard_fields",
        "_build_advanced_prompt_data",
    )
    NODE_CLASSES = (
        "EasyUseAnimaPromptStudioAdvanced",
        "EasyUseAnimaPromptStudioAdvancedV2",
    )

    def test_root_advanced_objects_are_direct_canonical_aliases(self):
        for name in (*self.RETIRED_NODE_CLASSES, *self.RETIRED_ADVANCED_ALIASES):
            with self.subTest(retired=name):
                self.assertFalse(hasattr(nodes, name))
        for name in self.SERVICE_OBJECTS:
            with self.subTest(module="advanced", name=name):
                self.assertIs(getattr(nodes, name), getattr(prompt_advanced, name))
        for name in self.NODE_CLASSES:
            with self.subTest(module="prompt_advanced_nodes", name=name):
                self.assertIs(getattr(nodes, name), getattr(prompt_advanced_nodes, name))

    def test_package_loaded_root_advanced_objects_are_direct_aliases(self):
        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            package_name = package_nodes.__package__
            package_advanced = sys.modules[f"{package_name}.easyuse_anima.prompt.advanced"]
            package_advanced_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.prompt_advanced_nodes"
            ]

            for name in (*self.RETIRED_NODE_CLASSES, *self.RETIRED_ADVANCED_ALIASES):
                with self.subTest(retired=name):
                    self.assertFalse(hasattr(package_nodes, name))
            for name in self.SERVICE_OBJECTS:
                with self.subTest(module="advanced", name=name):
                    self.assertIs(getattr(package_nodes, name), getattr(package_advanced, name))
            for name in self.NODE_CLASSES:
                with self.subTest(module="prompt_advanced_nodes", name=name):
                    self.assertIs(
                        getattr(package_nodes, name),
                        getattr(package_advanced_nodes, name),
                    )

            self.assertIs(
                package_entrypoint.NODE_CLASS_MAPPINGS["EasyUseAnimaPromptStudioAdvanced"],
                package_advanced_nodes.EasyUseAnimaPromptStudioAdvanced,
            )
            self.assertIs(
                package_entrypoint.NODE_CLASS_MAPPINGS["EasyUseAnimaPromptStudioAdvancedV2"],
                package_advanced_nodes.EasyUseAnimaPromptStudioAdvancedV2,
            )
            self.assertNotIn(
                "EasyUseAnimaPromptStudioExtend",
                package_entrypoint.NODE_CLASS_MAPPINGS,
            )

    def test_advanced_v2_directly_inherits_the_canonical_advanced_node(self):
        self.assertEqual(
            prompt_advanced_nodes.EasyUseAnimaPromptStudioAdvancedV2.__bases__,
            (prompt_advanced_nodes.EasyUseAnimaPromptStudioAdvanced,),
        )

    def test_root_monkeypatches_drive_the_canonical_advanced_change_key(self):
        with (
            patch.object(nodes, "_stable_change_key", side_effect=lambda value: value) as stable,
            patch.object(
                nodes,
                "_prompt_translation_change_key",
                return_value={"bound": "translation"},
            ) as translation_key,
            patch.object(
                nodes,
                "resolve_metadata_filter_words",
                return_value="bound filters",
            ) as resolve_filters,
        ):
            change_key = prompt_advanced_nodes.EasyUseAnimaPromptStudioAdvanced.IS_CHANGED()

        self.assertEqual(change_key["mode"], "prompt_studio_advanced")
        self.assertEqual(change_key["metadata_filter_words"], "bound filters")
        self.assertEqual(change_key["prompt_translation"], {"bound": "translation"})
        stable.assert_called_once_with(change_key)
        translation_key.assert_called_once_with()
        resolve_filters.assert_called_once_with()

    def test_root_naia_class_monkeypatch_drives_advanced_and_extend(self):
        request_bodies = []

        class BoundNAIARandomPrompt:
            @staticmethod
            def _make_request_body(*_args):
                return {"bound": True}

        def post_random(_host, _port, body, **_kwargs):
            request_bodies.append(body)
            return {
                "ok": True,
                "prompt": f"bound prompt {len(request_bodies)}",
                "negative_prompt": "",
                "width": 1024,
                "height": 1024,
            }

        settings = {
            "host": "127.0.0.1",
            "port": 8188,
            "use_naia_settings": True,
            "pre_prompt": "",
            "post_prompt": "",
            "auto_hide": "",
            "preprocessing": {},
        }
        fields = json.dumps([
            {
                "id": "positive_naia",
                "pane": "positive",
                "type": "naia",
                "label": "NAIA Prompt",
                "text": "old prompt",
                "height": 120,
                "enabled": True,
            }
        ])

        with (
            patch.object(nodes, "EasyUseAnimaNAIARandomPrompt", BoundNAIARandomPrompt),
            patch.object(nodes, "resolve_naia_settings", return_value=settings),
            patch.object(nodes, "_post_random", side_effect=post_random),
        ):
            advanced = prompt_advanced_nodes.EasyUseAnimaPromptStudioAdvanced().build(
                True,
                True,
                False,
                False,
                fields,
            )
            extended = prompt_advanced_nodes.EasyUseAnimaPromptStudioExtend().build(
                True,
                False,
                False,
            )

        self.assertEqual(request_bodies, [{"bound": True}, {"bound": True}])
        self.assertEqual(advanced["result"][0], "bound prompt 1")
        self.assertIn("bound prompt 2", extended["result"][0])

    def test_fresh_process_direct_imports_do_not_load_root_nodes(self):
        script = f"""
import importlib
import json
import sys
sys.path.insert(0, {str(ROOT)!r})
sys.dont_write_bytecode = True
advanced = importlib.import_module("easyuse_anima.prompt.advanced")
advanced_nodes = importlib.import_module("easyuse_anima.nodes.prompt_advanced_nodes")
print(json.dumps({{
    "advanced_all": list(advanced.__all__),
    "nodes_all": list(advanced_nodes.__all__),
    "class_modules": [
        advanced_nodes.EasyUseAnimaPromptStudioAdvanced.__module__,
        advanced_nodes.EasyUseAnimaPromptStudioAdvancedV2.__module__,
        advanced_nodes.EasyUseAnimaPromptStudioExtend.__module__,
    ],
    "root_nodes_loaded": "nodes" in sys.modules,
}}))
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["advanced_all"], [])
        self.assertEqual(payload["nodes_all"], [])
        self.assertEqual(
            payload["class_modules"],
            ["easyuse_anima.nodes.prompt_advanced_nodes"] * 3,
        )
        self.assertFalse(payload["root_nodes_loaded"])


class PublicNodeContractTests(unittest.TestCase):
    def test_generated_contract_matches_versioned_fixture(self):
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(build_contract_snapshot(), expected)

    def test_package_mappings_use_the_canonical_runtime_class_objects(self):
        class_mappings, display_mappings = _root_mappings()

        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            runtime_mappings = package_entrypoint.NODE_CLASS_MAPPINGS
            self.assertEqual(list(runtime_mappings), [node_id for node_id, _ in class_mappings])
            self.assertEqual(package_entrypoint.NODE_DISPLAY_NAME_MAPPINGS, display_mappings)
            for node_id, class_name in class_mappings:
                with self.subTest(node_id=node_id):
                    mapped_class = runtime_mappings[node_id]
                    self.assertIs(mapped_class, getattr(package_entrypoint, class_name))
                    self.assertIs(mapped_class, getattr(package_nodes, class_name))

    def test_fixture_provenance_is_the_explicit_0_5_2_baseline(self):
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(expected["package_version"], FIXTURE_PROVENANCE_VERSION)
        self.assertEqual(
            FIXTURE.name,
            f"node_contracts_{FIXTURE_PROVENANCE_VERSION.replace('.', '_')}.json",
        )

    def test_fixture_contains_no_machine_specific_absolute_paths(self):
        _assert_no_absolute_paths(json.loads(FIXTURE.read_text(encoding="utf-8")))

    def test_absolute_path_guard_handles_nested_json_strings(self):
        nested_contract = json.dumps({"payload": json.dumps({"text": "contract"})})
        nested_path = json.dumps({"payload": json.dumps({"path": "Q:\\private\\file.json"})})

        self.assertFalse(_contains_absolute_path(nested_contract))
        self.assertTrue(_contains_absolute_path(nested_path))

    def test_representative_workflow_class_ids_remain_public(self):
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        public_ids = {node["id"] for node in expected["nodes"]}

        for workflow_node in expected["workflow_nodes"]:
            self.assertIn(workflow_node["class_id"], public_ids)
            self.assertIsInstance(workflow_node["widgets_values"], list)


if __name__ == "__main__":
    if sys.argv[1:] == ["--write-fixture"]:
        write_fixture()
    else:
        unittest.main()
