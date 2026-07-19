from __future__ import annotations

import ast
import importlib.util
import json
import math
import re
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

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
from easyuse_anima import nodes as canonical_nodes
from easyuse_anima.nodes import image_nodes


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
        "_comfy_checkpoint_names": lambda: ["contract/checkpoint.safetensors"],
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
    with patch.multiple(nodes, **replacements):
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
                "mode": "reproduce",
                "seed": 17,
                "seed_after_generate": "fixed",
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
            (
                "_alignment_value",
                "_align_up",
                "_align_nearest",
                "_align_down",
                "_aligned_size_near_scale",
            ),
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

    def test_package_nodes_private_aliases_are_canonical_objects(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
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
                    sys.modules[f"{package_name}.easyuse_anima.image.geometry"],
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

        self.assertEqual(nodes._alignment_value(["64"]), 64)
        self.assertIsNone(nodes._alignment_value("impact"))
        self.assertEqual(nodes._align_up(65, 64), 128)
        self.assertEqual(nodes._align_nearest(95, 64), 64)
        self.assertEqual(nodes._align_nearest(96, 64), 128)
        self.assertEqual(nodes._align_down(65, 64), 64)
        self.assertEqual(
            nodes._aligned_size_near_scale(128, 64, 2.0, 64, 0),
            (256, 128, 2.0),
        )


class ComfyAdapterMoveContractTests(unittest.TestCase):
    DIRECT_HELPER_MODULES = (
        (
            comfy_capabilities,
            ("_comfy_sampler_names", "_comfy_scheduler_names"),
        ),
        (
            comfy_resources,
            ("_comfy_checkpoint_names", "_folder_path_names"),
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
            package_name = package_nodes.__package__
            package_helper_modules = (
                (
                    sys.modules[
                        f"{package_name}.easyuse_anima.infrastructure.comfy.capabilities"
                    ],
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
    SCALING_ALIASES = (
        "IMAGE_SCALE_MULTIPLES",
        "IMAGE_UPSCALE_METHODS",
        "_image_scale_by_multiple_size",
        "_max_long_edge_value",
        "_normalize_image_scale_options",
        "_scale_by_value",
    )

    def test_root_nodes_image_objects_are_direct_canonical_aliases(self):
        for name in self.SCALING_ALIASES:
            with self.subTest(name=name):
                self.assertIs(getattr(nodes, name), getattr(image_scaling, name))

        self.assertIs(
            nodes._EasyUseAnimaAlignedDetailerHook,
            image_detailer._EasyUseAnimaAlignedDetailerHook,
        )
        self.assertIs(
            nodes.EasyUseAnimaImageScaleByMultiple,
            image_nodes.EasyUseAnimaImageScaleByMultiple,
        )
        self.assertIs(
            nodes.EasyUseAnimaDetailerAlignHook,
            image_nodes.EasyUseAnimaDetailerAlignHook,
        )
        self.assertIs(
            canonical_nodes.EasyUseAnimaImageScaleByMultiple,
            image_nodes.EasyUseAnimaImageScaleByMultiple,
        )
        self.assertIs(
            canonical_nodes.EasyUseAnimaDetailerAlignHook,
            image_nodes.EasyUseAnimaDetailerAlignHook,
        )
        self.assertIs(image_nodes._common_upscale_image, comfy_invocation._common_upscale_image)

    def test_package_loaded_root_nodes_image_objects_are_direct_canonical_aliases(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_scaling = sys.modules[f"{package_name}.easyuse_anima.image.scaling"]
            package_detailer = sys.modules[f"{package_name}.easyuse_anima.image.detailer"]
            package_invocation = sys.modules[
                f"{package_name}.easyuse_anima.infrastructure.comfy.invocation"
            ]
            package_node_adapters = sys.modules[
                f"{package_name}.easyuse_anima.nodes.image_nodes"
            ]
            package_node_exports = sys.modules[f"{package_name}.easyuse_anima.nodes"]

            for name in self.SCALING_ALIASES:
                with self.subTest(name=name):
                    self.assertIs(
                        getattr(package_nodes, name),
                        getattr(package_scaling, name),
                    )

            self.assertIs(
                package_nodes._EasyUseAnimaAlignedDetailerHook,
                package_detailer._EasyUseAnimaAlignedDetailerHook,
            )
            for name in (
                "EasyUseAnimaDetailerAlignHook",
                "EasyUseAnimaImageScaleByMultiple",
            ):
                with self.subTest(name=name):
                    canonical_class = getattr(package_node_adapters, name)
                    self.assertIs(getattr(package_nodes, name), canonical_class)
                    self.assertIs(getattr(package_node_exports, name), canonical_class)
            self.assertIs(
                package_node_adapters._common_upscale_image,
                package_invocation._common_upscale_image,
            )


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
