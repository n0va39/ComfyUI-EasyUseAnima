from __future__ import annotations

import ast
import atexit
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
from unittest.mock import Mock, call, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easyuse_anima import workflow
from easyuse_anima.aio import (
    generation_normalization as aio_generation_normalization,
    postprocess as aio_postprocess,
    resources as aio_resources,
    sampling as aio_sampling,
    usdu as aio_usdu,
)
from easyuse_anima.aio import model_preparation as aio_model_preparation
from easyuse_anima.common import serialization as common_serialization
from easyuse_anima.common import values as common_values
from easyuse_anima.image import detailer as image_detailer
from easyuse_anima.image import geometry as image_geometry
from easyuse_anima.image import sam3_detailer as image_sam3_detailer
from easyuse_anima.image import upscale as image_upscale
from easyuse_anima.infrastructure.comfy import capabilities as comfy_capabilities
from easyuse_anima.infrastructure.comfy import invocation as comfy_invocation
from easyuse_anima.infrastructure.comfy import resources as comfy_resources
from easyuse_anima.lora import metadata as lora_metadata
from easyuse_anima.lora import preset as lora_preset
from easyuse_anima.nodes import (
    aio_nodes,
    image_nodes,
    input_types,
    lora_nodes,
    naia_nodes,
    prompt_advanced_nodes,
    prompt_data_nodes,
    prompt_nodes,
    regional_nodes,
    sam3_nodes,
    wildcard_nodes,
)
from tests.comfy_host_fakes import patch_comfy_helper
from easyuse_anima.prompt import artist_mix as prompt_artist_mix
from easyuse_anima.prompt import artist_mix_primitives as prompt_artist_mix_primitives
from easyuse_anima.prompt import advanced as prompt_advanced
from easyuse_anima.prompt import conditioning as prompt_conditioning
from easyuse_anima.prompt import data as prompt_data
from easyuse_anima.prompt import correction as prompt_correction
from easyuse_anima.prompt import fields as prompt_fields
from easyuse_anima.prompt import regional as prompt_regional
from easyuse_anima.registration import NODE_CLASS_MAPPINGS


PACKAGE_INIT = ROOT / "__init__.py"
REGISTRATION_MODULE = ROOT / "easyuse_anima" / "registration.py"
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


def _registration_mappings() -> tuple[list[tuple[str, str]], dict[str, str]]:
    tree = ast.parse(
        REGISTRATION_MODULE.read_text(encoding="utf-8-sig"),
        filename=REGISTRATION_MODULE.name,
    )
    class_mapping_node = _assignment_value(tree, "NODE_CLASS_MAPPINGS")
    display_mapping_node = _assignment_value(tree, "NODE_DISPLAY_NAME_MAPPINGS")
    if not isinstance(class_mapping_node, ast.Dict) or not isinstance(display_mapping_node, ast.Dict):
        raise AssertionError("Registration mappings must remain literal dictionaries")

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
        "_comfy_sampler_names": lambda: ["contract_sampler_a", "contract_sampler_b"],
        "_comfy_scheduler_names": lambda: ["contract_scheduler_a", "contract_scheduler_b"],
        "_comfy_diffusion_model_names": lambda: ["contract/diffusion_model.safetensors"],
        "_comfy_text_encoder_names": lambda: ["contract/text_encoder.safetensors"],
        "_comfy_vae_names": lambda: ["contract/vae.safetensors"],
        "_comfy_clip_loader_types": lambda: ["qwen_image", "stable_diffusion"],
        "_impact_scheduler_names": lambda: ["contract_impact_scheduler"],
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
    with (
        patch.multiple(
            aio_nodes,
            _comfy_diffusion_model_names=replacements[
                "_comfy_diffusion_model_names"
            ],
            _comfy_text_encoder_names=replacements[
                "_comfy_text_encoder_names"
            ],
            _comfy_vae_names=replacements["_comfy_vae_names"],
            _comfy_clip_loader_types=replacements["_comfy_clip_loader_types"],
        ),
        patch.multiple(
            aio_generation_normalization,
            _comfy_sampler_names=replacements["_comfy_sampler_names"],
            _comfy_scheduler_names=replacements["_comfy_scheduler_names"],
            _impact_scheduler_names=replacements["_impact_scheduler_names"],
        ),
        patch.multiple(
            prompt_nodes,
            resolve_metadata_filter_words=replacements[
                "resolve_metadata_filter_words"
            ],
            _prompt_translation_change_key=replacements[
                "_prompt_translation_change_key"
            ],
        ),
        patch.multiple(
            prompt_advanced_nodes,
            resolve_metadata_filter_words=replacements[
                "resolve_metadata_filter_words"
            ],
            resolve_naia_settings=replacements["resolve_naia_settings"],
            _prompt_translation_change_key=replacements[
                "_prompt_translation_change_key"
            ],
            wildcard_sources_signature=replacements[
                "wildcard_sources_signature"
            ],
        ),
        patch.multiple(
            regional_nodes,
            resolve_metadata_filter_words=replacements[
                "resolve_metadata_filter_words"
            ],
            _prompt_translation_change_key=replacements[
                "_prompt_translation_change_key"
            ],
            wildcard_sources_signature=replacements[
                "wildcard_sources_signature"
            ],
        ),
        patch.multiple(
            wildcard_nodes,
            wildcard_sources_signature=replacements[
                "wildcard_sources_signature"
            ],
        ),
        patch.multiple(
            naia_nodes,
            resolve_naia_settings=replacements["resolve_naia_settings"],
        ),
        patch_comfy_helper(
            aio_nodes,
            "_comfy_max_resolution",
            return_value=16384,
        ),
        patch.object(
            sam3_nodes,
            "_comfy_checkpoint_names",
            return_value=["contract/checkpoint.safetensors"],
        ),
        patch.object(
            lora_nodes,
            "_lora_combo_values",
            return_value=["None", "contract/style.safetensors"],
        ),
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
    host_nodes = types.ModuleType("nodes")
    host_nodes.MAX_RESOLUTION = 16384

    registrations = []

    def route_decorator(method, path):
        def register(handler):
            registrations.append((method, path, handler))
            return handler

        return register

    routes = types.SimpleNamespace(
        get=lambda path: route_decorator("GET", path),
        post=lambda path: route_decorator("POST", path),
    )
    server = types.ModuleType("server")
    server.PromptServer = type(
        "PromptServer",
        (),
        {"instance": types.SimpleNamespace(routes=routes)},
    )
    aiohttp = types.ModuleType("aiohttp")
    aiohttp.web = types.SimpleNamespace(
        FileResponse=object,
        HTTPException=Exception,
        Response=object,
        json_response=lambda payload, status=200: (payload, status),
    )
    bootstrap = None

    try:
        with (
            patch.dict(
                sys.modules,
                {"aiohttp": aiohttp, "nodes": host_nodes, "server": server},
            ),
            patch.object(atexit, "register"),
        ):
            wildcard_sources_module = importlib.import_module(
                f"{package_name}.easyuse_anima.wildcard.sources"
            )
            with patch.object(
                wildcard_sources_module,
                "ensure_default_wildcard_root",
                return_value=None,
            ):
                package_spec.loader.exec_module(package_module)
                bootstrap = sys.modules[f"{package_name}.easyuse_anima.bootstrap"]
                yield package_module, package_module
    finally:
        try:
            if bootstrap is not None:
                bootstrap.shutdown()
        finally:
            for name in list(sys.modules):
                if name == package_name or name.startswith(package_prefix):
                    sys.modules.pop(name, None)


def _node_contract(node_id: str, class_name: str, display_name: str) -> dict:
    node_class = NODE_CLASS_MAPPINGS[node_id]
    if node_class.__name__ != class_name:
        raise AssertionError(f"Unexpected class mapping for {node_id}: {node_class!r}")
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
    input_context = aio_nodes.EasyUseAnimaInput().build(
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
            "result": _normalize(NODE_CLASS_MAPPINGS[node_id].IS_CHANGED(**kwargs)),
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
    class_mappings, display_mappings = _registration_mappings()
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
            ("_align_nearest", "_align_down", "_image_tensor_size"),
        ),
    )

    def test_package_canonical_geometry_preserves_behavior(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_geometry = sys.modules[
                f"{package_name}.easyuse_anima.image.geometry"
            ]
            self.assertEqual(package_geometry._alignment_value(["64"]), 64)
            self.assertIsNone(package_geometry._alignment_value("impact"))
            self.assertEqual(package_geometry._align_up(65, 64), 128)
            self.assertEqual(
                package_geometry._aligned_size_near_scale(128, 64, 2.0, 64, 0),
                (256, 128, 2.0),
            )

    def test_moved_helper_behavior_matches_existing_contract(self):
        self.assertEqual(common_values._single_value(["first", "second"]), "first")
        self.assertIsNone(common_values._single_value(()))
        self.assertTrue(common_values._as_bool(" enabled "))
        self.assertFalse(common_values._as_bool("false", True))
        self.assertEqual(common_values._as_int(["7"], 3), 7)
        self.assertEqual(common_values._as_int("invalid", 3), 3)
        self.assertEqual(common_values._as_float(["1.5"], 3.0), 1.5)
        self.assertEqual(common_values._choice(" beta ", ("alpha", "beta"), "alpha"), "beta")
        self.assertEqual(common_values._choice("missing", ("alpha", "beta"), "beta"), "beta")

        self.assertEqual(
            common_serialization._stable_change_key({"b": 2, "a": "한"}),
            '{"a":"한","b":2}',
        )
        source = {"nested": [{"value": "한"}]}
        clone = common_serialization._json_clone(source)
        self.assertEqual(clone, source)
        self.assertIsNot(clone, source)
        self.assertIsNot(clone["nested"], source["nested"])
        json_object_source = {"value": 1}
        self.assertEqual(common_serialization._json_object(json_object_source), json_object_source)
        self.assertIsNot(common_serialization._json_object(json_object_source), json_object_source)
        self.assertEqual(common_serialization._json_object('{"value": 1}'), {"value": 1})
        self.assertEqual(common_serialization._json_object("invalid"), {})

        self.assertEqual(image_geometry._alignment_value(["64"]), 64)
        self.assertIsNone(image_geometry._alignment_value("impact"))
        self.assertEqual(image_geometry._align_up(65, 64), 128)
        self.assertEqual(image_geometry._align_nearest(95, 64), 64)
        self.assertEqual(image_geometry._align_nearest(96, 64), 128)
        self.assertEqual(image_geometry._align_down(65, 64), 64)
        self.assertEqual(
            image_geometry._image_tensor_size(
                types.SimpleNamespace(shape=(1, 5, 7, 4)),
                32,
                48,
            ),
            (7, 5),
        )
        self.assertEqual(
            image_geometry._image_tensor_size(object(), "32", "48"),
            (32, 48),
        )
        self.assertEqual(
            image_geometry._aligned_size_near_scale(128, 64, 2.0, 64, 0),
            (256, 128, 2.0),
        )


class AioLoraSignatureMoveContractTests(unittest.TestCase):
    EXPECTED_SIGNATURE = [
        {
            "name": "styles/test.safetensors",
            "strength_model": 0.8,
            "strength_clip": 0.6,
        }
    ]

    def test_root_alias_and_canonical_normalizer_rebind(self):
        self.assertIs(
            aio_model_preparation._aio_lora_stack_signature,
            aio_model_preparation._aio_lora_stack_signature,
        )
        normalized = [("styles/test.safetensors", 0.8, 0.6)]
        with patch.object(
            aio_model_preparation,
            "_normalize_aio_lora_stack",
            return_value=normalized,
        ) as normalize:
            self.assertEqual(
                aio_model_preparation._aio_lora_stack_signature("raw"),
                self.EXPECTED_SIGNATURE,
            )
        normalize.assert_called_once_with("raw")

    def test_package_alias_and_canonical_normalizer_rebind(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_model_preparation = sys.modules[
                f"{package_name}.easyuse_anima.aio.model_preparation"
            ]
            normalized = [("styles/test.safetensors", 0.8, 0.6)]
            with patch.object(
                package_model_preparation,
                "_normalize_aio_lora_stack",
                return_value=normalized,
            ) as normalize:
                self.assertEqual(
                    package_model_preparation._aio_lora_stack_signature("raw"),
                    self.EXPECTED_SIGNATURE,
                )
            normalize.assert_called_once_with("raw")


class AioSpectrumNormalizationMoveContractTests(unittest.TestCase):
    DEFAULTS = {
        "enabled": False,
        "window_size": 2.0,
        "flex_window": 0.25,
        "warmup_steps": 6,
        "tail_actual_steps": 3,
        "blend_w": 0.3,
        "cheby_degree": 3,
        "ridge_lambda": 0.1,
        "history_size": 100,
        "one_sampler_only": False,
        "verbose": False,
        "compat_policy": "legacy",
    }
    EXPECTED = {
        "enabled": True,
        "window_size": 10.0,
        "flex_window": 0.0,
        "warmup_steps": 0,
        "tail_actual_steps": 10000,
        "blend_w": 1.0,
        "cheby_degree": 1,
        "ridge_lambda": 0.001,
        "history_size": 5,
        "one_sampler_only": True,
        "verbose": False,
        "compat_policy": "legacy",
        "future": "kept",
    }

    def _assert_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._normalize_aio_spectrum_settings,
            canonical_module._normalize_aio_spectrum_settings,
        )
        value = {
            "enabled": True,
            "window_size": 99,
            "flex_window": -1,
            "warmup_steps": -5,
            "tail_actual_steps": 20000,
            "blend_w": 2,
            "cheby_degree": 0,
            "ridge_lambda": 0,
            "history_size": 1,
            "one_sampler_only": True,
            "verbose": False,
            "compat_policy": "unknown",
            "future": "kept",
        }
        with (
            patch.object(
                canonical_module,
                "_as_bool",
                wraps=canonical_module._as_bool,
            ) as as_bool,
            patch.object(
                canonical_module,
                "_as_float",
                wraps=canonical_module._as_float,
            ) as as_float,
            patch.object(
                canonical_module,
                "_as_int",
                wraps=canonical_module._as_int,
            ) as as_int,
            patch.object(
                canonical_module,
                "_choice",
                wraps=canonical_module._choice,
            ) as choice,
        ):
            result = canonical_module._normalize_aio_spectrum_settings(
                value,
                self.DEFAULTS,
            )
        self.assertIs(result, value)
        self.assertEqual(result, self.EXPECTED)
        for helper in (as_bool, as_float, as_int, choice):
            self.assertGreater(helper.call_count, 0)

    def test_root_alias_and_canonical_helpers(self):
        self._assert_contract(aio_generation_normalization, aio_generation_normalization)

    def test_package_alias_and_canonical_helpers(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_generation_normalization = sys.modules[
                f"{package_name}.easyuse_anima.aio.generation_normalization"
            ]
            self._assert_contract(package_generation_normalization, package_generation_normalization)


class AioDitNormalizationMoveContractTests(unittest.TestCase):
    DEFAULTS = {
        "enabled": False,
        "dcw_mode": "off",
        "dcw_lambda": 0.01,
        "dcw_band_mask": "LL",
        "dcw_calibrator": "(auto-download default)",
        "smc_cfg": False,
        "adaptive_smc_alpha": 0.0,
        "smc_cfg_lambda": 6.0,
        "cfgpp": False,
        "cfgpp_lambda": 0.0,
        "fsg": False,
        "fsg_band_lo": 0.59,
        "fsg_band_hi": 0.75,
        "fsg_k": 3,
        "fsg_d_sigma": 0.1,
        "fsg_gamma": 0.0,
        "replace_existing_cfg": False,
    }
    EXPECTED = {
        "enabled": True,
        "dcw_mode": "off",
        "dcw_lambda": 1.0,
        "dcw_band_mask": "LL",
        "dcw_calibrator": "(auto-download default)",
        "smc_cfg": True,
        "adaptive_smc_alpha": 1.0,
        "smc_cfg_lambda": 20.0,
        "cfgpp": True,
        "cfgpp_lambda": 8.0,
        "fsg": True,
        "fsg_band_lo": 0.0,
        "fsg_band_hi": 1.0,
        "fsg_k": 32,
        "fsg_d_sigma": 1.0,
        "fsg_gamma": 10.0,
        "replace_existing_cfg": True,
        "future": "kept",
    }

    def _assert_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._normalize_aio_dit_corrections_settings,
            canonical_module._normalize_aio_dit_corrections_settings,
        )
        value = {
            "enabled": True,
            "dcw_mode": "unknown",
            "dcw_lambda": 5,
            "dcw_band_mask": "unknown",
            "dcw_calibrator": "",
            "smc_cfg": True,
            "adaptive_smc_alpha": 2,
            "smc_cfg_lambda": 99,
            "cfgpp": True,
            "cfgpp_lambda": 99,
            "fsg": True,
            "fsg_band_lo": -1,
            "fsg_band_hi": 2,
            "fsg_k": 99,
            "fsg_d_sigma": 2,
            "fsg_gamma": 99,
            "replace_existing_cfg": True,
            "future": "kept",
        }
        with (
            patch.object(
                canonical_module,
                "_as_bool",
                wraps=canonical_module._as_bool,
            ) as as_bool,
            patch.object(
                canonical_module,
                "_as_float",
                wraps=canonical_module._as_float,
            ) as as_float,
            patch.object(
                canonical_module,
                "_as_int",
                wraps=canonical_module._as_int,
            ) as as_int,
            patch.object(
                canonical_module,
                "_choice",
                wraps=canonical_module._choice,
            ) as choice,
        ):
            result = canonical_module._normalize_aio_dit_corrections_settings(
                value,
                self.DEFAULTS,
            )
        self.assertIs(result, value)
        self.assertEqual(result, self.EXPECTED)
        for helper in (as_bool, as_float, as_int, choice):
            self.assertGreater(helper.call_count, 0)

    def test_root_alias_and_canonical_helpers(self):
        self._assert_contract(aio_generation_normalization, aio_generation_normalization)

    def test_package_alias_and_canonical_helpers(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_generation_normalization = sys.modules[
                f"{package_name}.easyuse_anima.aio.generation_normalization"
            ]
            self._assert_contract(package_generation_normalization, package_generation_normalization)


class AioDetailerNormalizationMoveContractTests(unittest.TestCase):
    SYMBOL_NAMES = (
        "_AIO_DETAILER_CUSTOM_RE",
        "_AIO_DETAILER_RESERVED_KEYS",
        "_is_aio_detailer_target_name",
        "_aio_detailer_has_enabled_targets",
        "_aio_detailer_target_defaults",
        "_aio_detailer_target_order",
    )

    def _assert_contract(self, root_module, canonical_module):
        for name in self.SYMBOL_NAMES:
            with self.subTest(name=name):
                self.assertIs(getattr(root_module, name), getattr(canonical_module, name))

        self.assertEqual(root_module._AIO_DETAILER_RESERVED_KEYS, {"enabled", "order", "sam3"})
        self.assertEqual(root_module._AIO_DETAILER_CUSTOM_RE.pattern, r"^custom_\d+$")
        self.assertIs(
            root_module.AIO_GENERATION_DEFAULT_SETTINGS,
            canonical_module.AIO_GENERATION_DEFAULT_SETTINGS,
        )

        with patch.object(canonical_module, "_AIO_DETAILER_CUSTOM_RE") as custom_re:
            custom_re.fullmatch.side_effect = lambda name: name == "replacement"
            self.assertTrue(canonical_module._is_aio_detailer_target_name("replacement"))
            self.assertFalse(canonical_module._is_aio_detailer_target_name("custom_7"))
        self.assertEqual(
            custom_re.fullmatch.call_args_list,
            [call("replacement"), call("custom_7")],
        )

        defaults = {
            "detailer": {
                "face": {"label": "Face", "nested": ["face"]},
                "eye": {"label": "Eye", "nested": ["eye"]},
            }
        }
        with (
            patch.object(canonical_module, "AIO_GENERATION_DEFAULT_SETTINGS", defaults),
            patch.object(
                canonical_module,
                "_json_clone",
                side_effect=lambda value: json.loads(json.dumps(value)),
            ) as json_clone,
        ):
            eye = canonical_module._aio_detailer_target_defaults("eye")
            custom = canonical_module._aio_detailer_target_defaults("custom_12")
        self.assertEqual(eye, defaults["detailer"]["eye"])
        self.assertIsNot(eye["nested"], defaults["detailer"]["eye"]["nested"])
        self.assertEqual(custom["label"], "Detailer Block 12")
        self.assertEqual(
            json_clone.call_args_list,
            [call(defaults["detailer"]["eye"]), call(defaults["detailer"]["face"])],
        )

        root_module._AIO_DETAILER_RESERVED_KEYS.add("custom_9")
        try:
            self.assertEqual(
                canonical_module._aio_detailer_target_order({"custom_9": {}}),
                ["face", "eye"],
            )
        finally:
            root_module._AIO_DETAILER_RESERVED_KEYS.discard("custom_9")

        with (
            patch.object(
                canonical_module,
                "_is_aio_detailer_target_name",
                side_effect=lambda name: name in {"special", "face", "eye"},
            ) as is_target,
            patch.object(canonical_module, "_AIO_DETAILER_RESERVED_KEYS", {"reserved"}),
        ):
            order = canonical_module._aio_detailer_target_order(
                {
                    "order": [" special ", "special", "invalid"],
                    "reserved": {},
                    "late": {},
                    "scalar": "ignored",
                }
            )
        self.assertEqual(order, ["special", "face", "eye"])
        self.assertNotIn(call("reserved"), is_target.call_args_list)

        disabled = {"enabled": False, "face": {"enabled": True}}
        with (
            patch.object(canonical_module, "_as_bool", return_value=False) as as_bool,
            patch.object(canonical_module, "_aio_detailer_target_order") as target_order,
        ):
            self.assertFalse(
                canonical_module._aio_detailer_has_enabled_targets(disabled)
            )
        as_bool.assert_called_once_with(False, False)
        target_order.assert_not_called()

        enabled = {
            "enabled": "overall",
            "scalar": "ignored",
            "first": {"enabled": "first"},
            "second": {"enabled": "second"},
        }
        with (
            patch.object(
                canonical_module,
                "_as_bool",
                side_effect=lambda value, default: value in {"overall", "first"},
            ) as as_bool,
            patch.object(
                canonical_module,
                "_aio_detailer_target_order",
                return_value=["scalar", "first", "second"],
            ) as target_order,
        ):
            self.assertTrue(canonical_module._aio_detailer_has_enabled_targets(enabled))
        target_order.assert_called_once_with(enabled)
        self.assertEqual(
            as_bool.call_args_list,
            [call("overall", False), call("first", False)],
        )

    def test_root_aliases_and_canonical_state(self):
        self._assert_contract(aio_generation_normalization, aio_generation_normalization)

    def test_package_aliases_and_canonical_state(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_generation_normalization = sys.modules[
                f"{package_name}.easyuse_anima.aio.generation_normalization"
            ]
            self._assert_contract(package_generation_normalization, package_generation_normalization)


class AioUsduTilePlanningMoveContractTests(unittest.TestCase):
    MOVED_NAMES = (
        "_aio_usdu_auto_tile_dimension",
        "_aio_usdu_tile_plan",
    )

    def _assert_contract(self, root_module, canonical_module):
        for name in self.MOVED_NAMES:
            with self.subTest(name=name):
                self.assertIs(getattr(root_module, name), getattr(canonical_module, name))
        self.assertFalse(hasattr(root_module, "_bind_aio_usdu_planning_runtime"))
        self.assertFalse(hasattr(canonical_module, "_bind_aio_usdu_planning_runtime"))
        self.assertFalse(hasattr(root_module, "_aio_usdu_tile_size"))

        with (
            patch.object(canonical_module, "ceil", wraps=math.ceil) as ceil,
            patch.object(
                canonical_module,
                "_align_nearest",
                wraps=canonical_module._align_nearest,
            ) as align_nearest,
        ):
            self.assertEqual(
                canonical_module._aio_usdu_auto_tile_dimension(1500, 1000, 512, 2048),
                768,
            )
        self.assertEqual(ceil.call_args_list, [call(1.5), call(750.0)])
        align_nearest.assert_called_once_with(750, 64)

        with (
            patch.object(canonical_module, "_image_tensor_size", return_value=(320, 240)) as image_size,
            patch.object(canonical_module, "_as_bool", return_value=False) as as_bool,
            patch.object(canonical_module, "_as_int", side_effect=(321, 241)) as as_int,
        ):
            manual = canonical_module._aio_usdu_tile_plan(
                "image",
                0.01,
                {
                    "auto_tile_size": False,
                    "tile_width": "321",
                    "tile_height": "241",
                },
            )
        self.assertEqual(
            manual,
            {
                "auto": False,
                "input_width": 320,
                "input_height": 240,
                "target_width": 16,
                "target_height": 12,
                "tile_width": 321,
                "tile_height": 241,
            },
        )
        image_size.assert_called_once_with("image", 512, 512)
        as_bool.assert_called_once_with(False, True)
        self.assertEqual(as_int.call_args_list, [call("321", 512), call("241", 512)])

        with (
            patch.object(canonical_module, "_image_tensor_size", return_value=(512, 768)),
            patch.object(canonical_module, "_as_bool", return_value=True),
            patch.object(canonical_module, "_as_int", side_effect=(900, 500, 2000)),
            patch.object(
                canonical_module,
                "_aio_usdu_auto_tile_dimension",
                side_effect=(1024, 1536),
            ) as auto_dimension,
        ):
            automatic = canonical_module._aio_usdu_tile_plan(
                "image",
                2.0,
                {
                    "auto_tile_size": True,
                    "auto_tile_target": 900,
                    "auto_tile_min": 500,
                    "auto_tile_max": 2000,
                },
            )
        self.assertEqual(
            automatic,
            {
                "auto": True,
                "input_width": 512,
                "input_height": 768,
                "target_width": 1024,
                "target_height": 1536,
                "preferred": 900,
                "min": 500,
                "max": 2000,
                "tile_width": 1024,
                "tile_height": 1536,
            },
        )
        self.assertEqual(
            auto_dimension.call_args_list,
            [call(1024, 900, 500, 2000), call(1536, 900, 500, 2000)],
        )

    def test_root_aliases_and_canonical_helpers(self):
        self._assert_contract(aio_usdu, aio_usdu)

    def test_package_aliases_and_canonical_helpers(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_usdu = sys.modules[f"{package_name}.easyuse_anima.aio.usdu"]
            self._assert_contract(package_usdu, package_usdu)


class AioFinalFitPlanningMoveContractTests(unittest.TestCase):
    MOVED_NAMES = (
        "_apply_aio_final_fit",
        "_aio_final_fit_size",
        "_resize_image_to_size_if_needed",
        "_run_aio_postprocess_stage",
    )

    def _assert_resize_contract(self, root_module, canonical_module):
        events = []

        class Dimension:
            def __init__(self, name, value):
                self.name = name
                self.value = value

            def __int__(self):
                events.append(("int", self.name))
                return self.value

        class Tensor:
            def __init__(self, name):
                self.name = name

            def movedim(self, source, target):
                events.append((f"{self.name}.movedim", (source, target)))
                return samples if self is image else output

        image = Tensor("image")
        samples = Tensor("samples")
        resized = Tensor("resized")
        output = object()

        def image_size(value, width, height):
            events.append(("image_tensor_size", (value, width, height)))
            return 320, 240

        def upscale(value, width, height, method):
            events.append(("common_upscale_image", (value, width, height, method)))
            return resized

        with (
            patch.object(canonical_module, "_image_tensor_size", image_size),
            patch.object(canonical_module, "_common_upscale_image", upscale),
        ):
            result = canonical_module._resize_image_to_size_if_needed(
                image,
                Dimension("width", 640),
                Dimension("height", 480),
                "",
            )

        self.assertEqual(result, (output, True))
        self.assertEqual(
            events,
            [
                ("int", "width"),
                ("int", "height"),
                ("image_tensor_size", (image, 640, 480)),
                ("image.movedim", (-1, 1)),
                ("common_upscale_image", (samples, 640, 480, "bicubic")),
                ("resized.movedim", (1, -1)),
            ],
        )

        with (
            patch.object(canonical_module, "_image_tensor_size", return_value=(1, 1)),
            patch.object(canonical_module, "_common_upscale_image") as common_upscale,
        ):
            result = canonical_module._resize_image_to_size_if_needed(image, 0, -5)
        self.assertIs(result[0], image)
        self.assertFalse(result[1])
        common_upscale.assert_not_called()

        failure = RuntimeError("resize failed")
        with (
            patch.object(canonical_module, "_image_tensor_size", return_value=(320, 240)),
            patch.object(canonical_module, "_common_upscale_image", side_effect=failure),
            self.assertRaises(RuntimeError) as raised,
        ):
            canonical_module._resize_image_to_size_if_needed(image, 640, 480)
        self.assertIs(raised.exception, failure)

    def _assert_stage_contract(self, root_module, canonical_module):
        image = object()
        events = []

        class StageLogger:
            def info(self, *args):
                events.append(("logger.info", args))

        stage_logger = StageLogger()

        def disabled_as_bool(value, default):
            events.append(("as_bool", (value, default)))
            return False

        def disabled_size(value, width, height):
            events.append(("image_tensor_size", (value, width, height)))
            return 640, 480

        def unexpected_apply(*args):
            raise AssertionError(f"disabled postprocess applied final fit: {args!r}")

        with (
            patch.object(canonical_module, "_as_bool", disabled_as_bool),
            patch.object(canonical_module, "_image_tensor_size", disabled_size),
            patch.object(canonical_module, "_apply_aio_final_fit", unexpected_apply),
            patch.object(canonical_module, "logger", stage_logger),
        ):
            output, metadata = canonical_module._run_aio_postprocess_stage(
                image,
                {"enabled": "off"},
            )

        self.assertIs(output, image)
        self.assertEqual(
            events,
            [
                ("as_bool", ("off", False)),
                ("image_tensor_size", (image, 0, 0)),
            ],
        )
        self.assertEqual(list(metadata), ["enabled", "width", "height"])
        self.assertEqual(
            metadata,
            {"enabled": False, "width": 640, "height": 480},
        )

        for mode, expected_limit in (
            ("max_long_edge", "2048px"),
            ("megapixels", "4.5MP"),
        ):
            with self.subTest(mode=mode):
                output_image = object()
                fit_metadata = {
                    "width": 1024,
                    "height": 768,
                    "mode": mode,
                    "max_long_edge": 2048,
                    "max_megapixels": 4.5,
                    "method": "bicubic",
                    "applied": 1,
                    "target_width": 800,
                    "target_height": 600,
                }
                settings = {"enabled": "on", "fit": {"mode": mode}}
                events = []

                def enabled_as_bool(value, default):
                    events.append(("as_bool", (value, default)))
                    return True

                def apply_final_fit(value, stage_settings):
                    events.append(("apply_final_fit", (value, stage_settings)))
                    return output_image, fit_metadata

                def enabled_size(value, width, height):
                    events.append(("image_tensor_size", (value, width, height)))
                    return 800, 600

                with (
                    patch.object(canonical_module, "_as_bool", enabled_as_bool),
                    patch.object(
                        canonical_module,
                        "_apply_aio_final_fit",
                        apply_final_fit,
                    ),
                    patch.object(canonical_module, "_image_tensor_size", enabled_size),
                    patch.object(canonical_module, "logger", stage_logger),
                ):
                    output, metadata = canonical_module._run_aio_postprocess_stage(
                        image,
                        settings,
                    )

                self.assertIs(output, output_image)
                self.assertEqual(
                    events,
                    [
                        ("as_bool", ("on", False)),
                        ("apply_final_fit", (image, settings)),
                        ("image_tensor_size", (output_image, 800, 600)),
                        (
                            "logger.info",
                            (
                                "[EasyUseAnima][AiO] Postprocess final fit: input=%sx%s mode=%s limit=%s method=%s applied=%s output=%sx%s",
                                1024,
                                768,
                                mode,
                                expected_limit,
                                "bicubic",
                                True,
                                800,
                                600,
                            ),
                        ),
                    ],
                )
                self.assertEqual(
                    list(metadata),
                    ["enabled", "width", "height", "fit"],
                )
                self.assertEqual(metadata["enabled"], True)
                self.assertEqual(metadata["width"], 800)
                self.assertEqual(metadata["height"], 600)
                self.assertIs(metadata["fit"], fit_metadata)

    def _assert_contract(self, root_module, canonical_module):
        for name in self.MOVED_NAMES:
            with self.subTest(name=name):
                self.assertIs(getattr(root_module, name), getattr(canonical_module, name))
        self.assertFalse(hasattr(root_module, "_bind_aio_postprocess_runtime"))
        self.assertFalse(hasattr(canonical_module, "_bind_aio_postprocess_runtime"))

        self._assert_resize_contract(root_module, canonical_module)

        disabled = {"enabled": False, "mode": "megapixels"}
        with (
            patch.object(canonical_module, "_as_bool", return_value=False) as as_bool,
            patch.object(canonical_module, "_as_float") as as_float,
            patch.object(canonical_module, "_as_int") as as_int,
            patch.object(canonical_module, "sqrt") as sqrt,
            patch.object(canonical_module, "_align_down") as align_down,
        ):
            self.assertEqual(
                canonical_module._aio_final_fit_size(0, -3, disabled),
                (1, 1, 1.0),
            )
        as_bool.assert_called_once_with(False, False)
        as_float.assert_not_called()
        as_int.assert_not_called()
        sqrt.assert_not_called()
        align_down.assert_not_called()

        no_downscale = {"enabled": True, "mode": "unknown", "max_long_edge": 2048}
        with (
            patch.object(canonical_module, "_as_bool", return_value=True),
            patch.object(canonical_module, "_as_int", return_value=2048) as as_int,
            patch.object(canonical_module, "_as_float") as as_float,
            patch.object(canonical_module, "sqrt") as sqrt,
            patch.object(canonical_module, "_align_down") as align_down,
        ):
            self.assertEqual(
                canonical_module._aio_final_fit_size(1024, 512, no_downscale),
                (1024, 512, 1.0),
            )
        as_int.assert_called_once_with(2048, 2048)
        as_float.assert_not_called()
        sqrt.assert_not_called()
        align_down.assert_not_called()

        megapixels = {"enabled": True, "mode": "megapixels", "max_megapixels": 4}
        original = dict(megapixels)
        expected_scale = math.sqrt(4_000_000.0 / 12_000_000.0)
        with (
            patch.object(canonical_module, "_as_bool", return_value=True),
            patch.object(canonical_module, "_as_float", return_value=4.0) as as_float,
            patch.object(canonical_module, "_as_int") as as_int,
            patch.object(canonical_module, "sqrt", wraps=math.sqrt) as sqrt,
            patch.object(canonical_module, "LATENT_ALIGN", 32),
            patch.object(canonical_module, "_align_down", side_effect=(2304, 1728)) as align_down,
        ):
            result = canonical_module._aio_final_fit_size(4000, 3000, megapixels)
        self.assertEqual(result, (2304, 1728, expected_scale))
        self.assertEqual(megapixels, original)
        as_float.assert_called_once_with(4, 4.0)
        as_int.assert_not_called()
        sqrt.assert_called_once_with(4_000_000.0 / 12_000_000.0)
        self.assertEqual(
            align_down.call_args_list,
            [
                call(round(4000 * expected_scale), 32),
                call(round(3000 * expected_scale), 32),
            ],
        )

        image = object()
        source_fit = {
            "mode": "max_long_edge",
            "max_long_edge": "1920",
            "max_megapixels": "4.25",
            "method": "",
        }
        source_settings = {"enabled": "enabled", "fit": source_fit}
        events = []
        copied_fits = []

        def record(name, result):
            def side_effect(*args):
                events.append((name, args))
                return result

            return side_effect

        def final_fit_size(width, height, fit_settings):
            events.append(("final_fit_size", (width, height, dict(fit_settings))))
            copied_fits.append(fit_settings)
            return 640, 480, 1.0

        with (
            patch.object(
                canonical_module,
                "_as_bool",
                side_effect=record("as_bool", True),
            ),
            patch.object(
                canonical_module,
                "_image_tensor_size",
                side_effect=record("image_tensor_size", (640, 480)),
            ) as image_tensor_size,
            patch.object(
                canonical_module,
                "_aio_final_fit_size",
                side_effect=final_fit_size,
            ),
            patch.object(
                canonical_module,
                "_as_int",
                side_effect=record("as_int", 1920),
            ),
            patch.object(
                canonical_module,
                "_as_float",
                side_effect=record("as_float", 4.25),
            ),
            patch.object(canonical_module, "_resize_image_to_size_if_needed") as resize,
        ):
            output, metadata = canonical_module._apply_aio_final_fit(
                image,
                source_settings,
            )

        self.assertIs(output, image)
        self.assertEqual(
            [name for name, _ in events],
            [
                "as_bool",
                "image_tensor_size",
                "final_fit_size",
                "as_bool",
                "as_int",
                "as_float",
            ],
        )
        image_tensor_size.assert_called_once_with(image, 0, 0)
        self.assertEqual(
            copied_fits,
            [
                {
                    "mode": "max_long_edge",
                    "max_long_edge": "1920",
                    "max_megapixels": "4.25",
                    "method": "",
                    "enabled": True,
                }
            ],
        )
        self.assertIsNot(copied_fits[0], source_fit)
        self.assertEqual(
            source_fit,
            {
                "mode": "max_long_edge",
                "max_long_edge": "1920",
                "max_megapixels": "4.25",
                "method": "",
            },
        )
        self.assertEqual(source_settings["enabled"], "enabled")
        self.assertEqual(
            list(metadata),
            [
                "enabled",
                "mode",
                "max_long_edge",
                "max_megapixels",
                "method",
                "applied",
                "scale",
                "width",
                "height",
                "target_width",
                "target_height",
            ],
        )
        self.assertEqual(
            metadata,
            {
                "enabled": True,
                "mode": "max_long_edge",
                "max_long_edge": 1920,
                "max_megapixels": 4.25,
                "method": "bicubic",
                "applied": False,
                "scale": 1.0,
                "width": 640,
                "height": 480,
                "target_width": 640,
                "target_height": 480,
            },
        )
        resize.assert_not_called()

        invalid_fit = ["not", "a", "mapping"]
        invalid_settings = {"enabled": 1, "fit": invalid_fit}
        with (
            patch.object(canonical_module, "_as_bool", return_value=True) as as_bool,
            patch.object(
                canonical_module,
                "_image_tensor_size",
                return_value=(640, 480),
            ),
            patch.object(
                canonical_module,
                "_aio_final_fit_size",
                return_value=(320, 240, 0.5),
            ) as final_fit,
            patch.object(canonical_module, "_as_int", return_value=2048),
            patch.object(canonical_module, "_as_float", return_value=4.0),
            patch.object(
                canonical_module,
                "_resize_image_to_size_if_needed",
                return_value=("resized", False),
            ) as resize,
        ):
            output, metadata = canonical_module._apply_aio_final_fit(
                image,
                invalid_settings,
            )

        self.assertEqual(output, "resized")
        self.assertEqual(invalid_settings, {"enabled": 1, "fit": invalid_fit})
        self.assertEqual(as_bool.call_args_list, [call(1, False), call(1, False)])
        final_fit.assert_called_once_with(640, 480, {"enabled": True})
        resize.assert_called_once_with(image, 320, 240, "bicubic")
        self.assertFalse(metadata["applied"])
        self.assertEqual(metadata["scale"], 0.5)
        self.assertEqual(metadata["target_width"], 320)
        self.assertEqual(metadata["target_height"], 240)

        self._assert_stage_contract(root_module, canonical_module)

    def test_root_aliases_and_canonical_helpers(self):
        self._assert_contract(aio_postprocess, aio_postprocess)

    def test_package_aliases_and_canonical_helpers(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_postprocess = sys.modules[
                f"{package_name}.easyuse_anima.aio.postprocess"
            ]
            self._assert_contract(package_postprocess, package_postprocess)


class AioResourceNameMoveContractTests(unittest.TestCase):
    def _assert_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._comfy_diffusion_model_names,
            canonical_module._comfy_diffusion_model_names,
        )

        candidates = ("preferred.safetensors", "fallback.safetensors")
        returned = ["runtime.safetensors"]
        events = []

        def folder_names(_folder, _fallback):
            return ["runtime.safetensors"]

        def adapter(candidate_values, folder_lookup):
            events.append(("adapter_call", candidate_values, folder_lookup))
            return returned

        with (
            patch.object(
                canonical_module,
                "ANIMA_DEFAULT_DIFFUSION_MODEL_CANDIDATES",
                candidates,
            ),
            patch.object(
                canonical_module,
                "_adapter_comfy_diffusion_model_names",
                adapter,
            ),
            patch.object(canonical_module, "_folder_path_names", folder_names),
        ):
            result = canonical_module._comfy_diffusion_model_names()

        self.assertIs(result, returned)
        self.assertEqual(
            events,
            [("adapter_call", candidates, folder_names)],
        )

    def test_root_alias_and_call_time_dependencies(self):
        self._assert_contract(aio_resources, aio_resources)

    def test_package_alias_and_call_time_dependencies(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_resources = sys.modules[
                f"{package_name}.easyuse_anima.aio.resources"
            ]
            self._assert_contract(package_resources, package_resources)

    def _assert_text_encoder_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._comfy_text_encoder_names,
            canonical_module._comfy_text_encoder_names,
        )

        candidates = ("preferred-clip.safetensors", "fallback-clip.safetensors")
        returned = ["runtime-clip.safetensors"]
        events = []

        def folder_names(_folder, _fallback):
            return ["runtime-clip.safetensors"]

        def adapter(candidate_values, folder_lookup):
            events.append(("adapter_call", candidate_values, folder_lookup))
            return returned

        with (
            patch.object(
                canonical_module,
                "ANIMA_DEFAULT_CLIP_CANDIDATES",
                candidates,
            ),
            patch.object(
                canonical_module,
                "_adapter_comfy_text_encoder_names",
                adapter,
            ),
            patch.object(canonical_module, "_folder_path_names", folder_names),
        ):
            result = canonical_module._comfy_text_encoder_names()

        self.assertIs(result, returned)
        self.assertEqual(
            events,
            [("adapter_call", candidates, folder_names)],
        )

    def test_text_encoder_root_alias_and_call_time_dependencies(self):
        self._assert_text_encoder_contract(aio_resources, aio_resources)

    def test_text_encoder_package_alias_and_call_time_dependencies(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_resources = sys.modules[
                f"{package_name}.easyuse_anima.aio.resources"
            ]
            self._assert_text_encoder_contract(package_resources, package_resources)

    def _assert_vae_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._comfy_vae_names,
            canonical_module._comfy_vae_names,
        )

        candidates = ("preferred.vae", "fallback.vae")
        returned = ["runtime.vae"]
        events = []
        find_calls = []

        def find_node_class(node_id):
            find_calls.append(node_id)
            return None

        def folder_names(_folder, _fallback):
            return ["runtime.vae"]

        def adapter(candidate_values, node_finder, folder_lookup):
            events.append(
                (
                    "adapter_call",
                    candidate_values,
                    node_finder("ContractProbe"),
                    folder_lookup,
                )
            )
            return returned

        with (
            patch.object(
                canonical_module,
                "ANIMA_DEFAULT_VAE_CANDIDATES",
                candidates,
            ),
            patch.object(canonical_module, "_adapter_comfy_vae_names", adapter),
            patch_comfy_helper(
                root_module,
                "_find_comfy_node_class",
                find_node_class,
            ),
            patch.object(canonical_module, "_folder_path_names", folder_names),
        ):
            result = canonical_module._comfy_vae_names()

        self.assertIs(result, returned)
        self.assertEqual(
            events,
            [("adapter_call", candidates, None, folder_names)],
        )
        self.assertEqual(find_calls, ["ContractProbe"])

    def test_vae_root_alias_and_call_time_dependencies(self):
        self._assert_vae_contract(aio_resources, aio_resources)

    def test_vae_package_alias_and_call_time_dependencies(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_resources = sys.modules[
                f"{package_name}.easyuse_anima.aio.resources"
            ]
            self._assert_vae_contract(package_resources, package_resources)

    def _assert_clip_loader_type_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._comfy_clip_loader_types,
            canonical_module._comfy_clip_loader_types,
        )

        candidates = ("qwen_image", "stable_diffusion")
        returned = ["runtime_clip_type"]
        events = []
        find_calls = []

        def find_node_class(node_id):
            find_calls.append(node_id)
            return None

        def adapter(candidate_values, node_finder):
            events.append(
                ("adapter_call", candidate_values, node_finder("ContractProbe"))
            )
            return returned

        with (
            patch.object(canonical_module, "ANIMA_CLIP_TYPES", candidates),
            patch.object(
                canonical_module,
                "_adapter_comfy_clip_loader_types",
                adapter,
            ),
            patch_comfy_helper(
                root_module,
                "_find_comfy_node_class",
                find_node_class,
            ),
        ):
            result = canonical_module._comfy_clip_loader_types()

        self.assertIs(result, returned)
        self.assertEqual(
            events,
            [("adapter_call", candidates, None)],
        )
        self.assertEqual(find_calls, ["ContractProbe"])

    def test_clip_loader_type_root_alias_and_call_time_dependencies(self):
        self._assert_clip_loader_type_contract(aio_resources, aio_resources)

    def test_clip_loader_type_package_alias_and_call_time_dependencies(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_resources = sys.modules[
                f"{package_name}.easyuse_anima.aio.resources"
            ]
            self._assert_clip_loader_type_contract(package_resources, package_resources)


class AioSeedNormalizationMoveContractTests(unittest.TestCase):
    CONSTANT_NAMES = (
        "AIO_SPECIAL_SEED_RANDOM",
        "AIO_SPECIAL_SEED_INCREMENT",
        "AIO_SPECIAL_SEED_DECREMENT",
        "AIO_SPECIAL_SEEDS",
    )

    def _assert_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._normalize_aio_seed,
            canonical_module._normalize_aio_seed,
        )
        for name in self.CONSTANT_NAMES:
            with self.subTest(name=name):
                self.assertIs(getattr(root_module, name), getattr(canonical_module, name))

        self.assertEqual(root_module.AIO_SPECIAL_SEED_RANDOM, -1)
        self.assertEqual(root_module.AIO_SPECIAL_SEED_INCREMENT, -2)
        self.assertEqual(root_module.AIO_SPECIAL_SEED_DECREMENT, -3)
        self.assertIsInstance(root_module.AIO_SPECIAL_SEEDS, set)
        self.assertEqual(root_module.AIO_SPECIAL_SEEDS, {-1, -2, -3})
        self.assertEqual(canonical_module.MAX_SEED, root_module.MAX_SEED)
        self.assertEqual(
            canonical_module.SEED_CONTROL_MODES,
            root_module.SEED_CONTROL_MODES,
        )

        with (
            patch.object(canonical_module, "_as_int", side_effect=(99, -99)) as as_int,
            patch.object(canonical_module, "MAX_SEED", 12),
            patch.object(canonical_module, "AIO_SPECIAL_SEED_DECREMENT", -7),
        ):
            self.assertEqual(canonical_module._normalize_aio_seed("high"), 12)
            self.assertEqual(canonical_module._normalize_aio_seed("low"), -7)

        self.assertEqual(
            as_int.call_args_list,
            [call("high", -1), call("low", -1)],
        )

    def test_root_aliases_and_canonical_clamp_helpers(self):
        self._assert_contract(aio_generation_normalization, aio_generation_normalization)

    def test_package_aliases_and_canonical_clamp_helpers(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_generation_normalization = sys.modules[
                f"{package_name}.easyuse_anima.aio.generation_normalization"
            ]
            self._assert_contract(package_generation_normalization, package_generation_normalization)


class AioRuntimeSeedMoveContractTests(unittest.TestCase):
    def _assert_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._new_aio_random_seed,
            canonical_module._new_aio_random_seed,
        )
        self.assertIs(
            root_module._resolve_aio_runtime_seed,
            canonical_module._resolve_aio_runtime_seed,
        )

        randint_calls = []
        random_module = types.SimpleNamespace(
            randint=lambda lower, upper: randint_calls.append((lower, upper)) or 7
        )
        with (
            patch.object(canonical_module, "random", random_module),
            patch.object(canonical_module, "MAX_SEED", 12),
        ):
            self.assertEqual(canonical_module._new_aio_random_seed(), 7)
        self.assertEqual(randint_calls, [(0, 12)])

        with (
            patch.object(
                canonical_module,
                "_normalize_aio_seed",
                side_effect=(-1, 99, -99),
            ) as normalize_seed,
            patch.object(canonical_module, "AIO_SPECIAL_SEEDS", {-1}),
            patch.object(
                canonical_module,
                "_new_aio_random_seed",
                return_value=777,
            ) as new_seed,
            patch.object(canonical_module, "MAX_SEED", 12),
        ):
            self.assertEqual(canonical_module._resolve_aio_runtime_seed("special"), 777)
            self.assertEqual(canonical_module._resolve_aio_runtime_seed("high"), 12)
            self.assertEqual(canonical_module._resolve_aio_runtime_seed("low"), 0)

        self.assertEqual(
            normalize_seed.call_args_list,
            [call("special"), call("high"), call("low")],
        )
        new_seed.assert_called_once_with()

    def test_root_aliases_and_canonical_replacements(self):
        self._assert_contract(aio_sampling, aio_sampling)

    def test_package_aliases_and_canonical_replacements(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_sampling = sys.modules[f"{package_name}.easyuse_anima.aio.sampling"]
            self._assert_contract(package_sampling, package_sampling)


class AioWidgetDefaultSerializerMoveContractTests(unittest.TestCase):
    def _assert_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._aio_input_settings_json,
            canonical_module._aio_input_settings_json,
        )
        self.assertIs(
            root_module._aio_generation_settings_json,
            canonical_module._aio_generation_settings_json,
        )

        input_defaults = {"schema": "입력"}
        generation_defaults = {"schema": "생성"}
        dumps_calls = []

        def dumps(value, *, ensure_ascii, separators):
            dumps_calls.append((value, ensure_ascii, separators))
            return "input-json" if value is input_defaults else "generation-json"

        with (
            patch.object(canonical_module, "json", types.SimpleNamespace(dumps=dumps)),
            patch.object(
                canonical_module,
                "AIO_INPUT_DEFAULT_SETTINGS",
                input_defaults,
            ),
            patch.object(
                canonical_module,
                "AIO_GENERATION_DEFAULT_SETTINGS",
                generation_defaults,
            ),
        ):
            self.assertEqual(canonical_module._aio_input_settings_json(), "input-json")
            self.assertEqual(
                canonical_module._aio_generation_settings_json(),
                "generation-json",
            )

        self.assertEqual(
            dumps_calls,
            [
                (input_defaults, False, (",", ":")),
                (generation_defaults, False, (",", ":")),
            ],
        )

        mutable_defaults = {"schema": "가"}
        with patch.object(
            canonical_module,
            "AIO_INPUT_DEFAULT_SETTINGS",
            mutable_defaults,
        ):
            self.assertEqual(
                canonical_module._aio_input_settings_json(),
                '{"schema":"가"}',
            )
            mutable_defaults["version"] = 1
            self.assertEqual(
                canonical_module._aio_input_settings_json(),
                '{"schema":"가","version":1}',
            )

    def test_root_aliases_and_call_time_serialization_inputs(self):
        self._assert_contract(aio_nodes, aio_nodes)

    def test_package_aliases_and_call_time_serialization_inputs(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_aio_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.aio_nodes"
            ]
            self._assert_contract(package_aio_nodes, package_aio_nodes)


class AioSettingsJsonRetirementContractTests(unittest.TestCase):
    def _assert_contract(self, canonical_module):
        self.assertFalse(hasattr(canonical_module, "_settings_json"))
        self.assertTrue(callable(canonical_module._aio_input_settings_json))
        self.assertTrue(callable(canonical_module._aio_generation_settings_json))

    def test_canonical_adapter_has_no_dead_settings_json_helper(self):
        self._assert_contract(aio_nodes)

    def test_package_canonical_adapter_has_no_dead_settings_json_helper(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_aio_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.aio_nodes"
            ]
            self._assert_contract(package_aio_nodes)


class AioInputSettingsNormalizerMoveContractTests(unittest.TestCase):
    def _assert_contract(self, root_module, canonical_module):
        self.assertIs(
            root_module._normalize_aio_input_settings,
            canonical_module._normalize_aio_input_settings,
        )

        defaults = {"default": "sentinel"}
        merged = {
            "version": "legacy-version",
            "resources": {
                "clip_loader": "legacy-loader",
                "unet_weight_dtype": "legacy-dtype",
                "clip_device": "legacy-device",
            },
            "future": {"kept": True},
        }
        merge_calls = []
        as_int_calls = []
        choice_calls = []

        def merge_versioned_settings(current_defaults, value):
            merge_calls.append((current_defaults, value))
            return merged

        def as_int(value, default):
            as_int_calls.append((value, default))
            return 9

        def choice(value, choices, default):
            choice_calls.append((value, choices, default))
            return f"normalized:{value}"

        with (
            patch.object(
                canonical_module,
                "_merge_versioned_settings",
                merge_versioned_settings,
            ),
            patch.object(canonical_module, "AIO_INPUT_DEFAULT_SETTINGS", defaults),
            patch.object(
                canonical_module,
                "EASY_USE_ANIMA_INPUT_SCHEMA",
                "input-schema",
            ),
            patch.object(
                canonical_module,
                "EASY_USE_ANIMA_INPUT_SETTINGS_VERSION",
                7,
            ),
            patch.object(canonical_module, "_as_int", as_int),
            patch.object(canonical_module, "_choice", choice),
            patch.object(
                canonical_module,
                "ANIMA_UNET_WEIGHT_DTYPES",
                ("dtype-a",),
            ),
            patch.object(canonical_module, "ANIMA_CLIP_DEVICES", ("device-a",)),
        ):
            result = canonical_module._normalize_aio_input_settings("payload")

        self.assertIs(result, merged)
        self.assertEqual(merge_calls, [(defaults, "payload")])
        self.assertEqual(as_int_calls, [("legacy-version", 7)])
        self.assertEqual(
            choice_calls,
            [
                ("legacy-loader", ("single",), "single"),
                ("legacy-dtype", ("dtype-a",), "default"),
                ("legacy-device", ("device-a",), "default"),
            ],
        )
        self.assertEqual(result["schema"], "input-schema")
        self.assertEqual(result["version"], 9)
        self.assertEqual(
            result["resources"],
            {
                "loader_mode": "split",
                "clip_loader": "normalized:legacy-loader",
                "unet_weight_dtype": "normalized:legacy-dtype",
                "clip_device": "normalized:legacy-device",
            },
        )
        self.assertEqual(result["future"], {"kept": True})

    def test_root_alias_and_call_time_input_contract(self):
        self._assert_contract(aio_resources, aio_resources)

    def test_package_alias_and_call_time_input_contract(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_resources = sys.modules[
                f"{package_name}.easyuse_anima.aio.resources"
            ]
            self._assert_contract(package_resources, package_resources)


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

    def test_package_canonical_comfy_adapters_preserve_behavior(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_capabilities = sys.modules[
                f"{package_name}.easyuse_anima.infrastructure.comfy.capabilities"
            ]
            package_sam3_nodes = importlib.import_module(
                f"{package_name}.easyuse_anima.nodes.sam3_nodes"
            )
            package_impact_nodes = importlib.import_module(
                f"{package_name}.easyuse_anima.nodes.impact_detailer_nodes"
            )
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

    def test_canonical_image_node_adapters_preserve_behavior(self):
        self.assertIs(
            image_nodes._EasyUseAnimaAlignedDetailerHook,
            image_detailer._EasyUseAnimaAlignedDetailerHook,
        )
        self.assertIs(
            image_sam3_detailer._EasyUseAnimaAlignedDetailerHook,
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
            image_upscale._common_upscale_image,
            comfy_invocation._common_upscale_image,
        )
        self.assertIs(
            image_nodes._upscale_image_by_multiple,
            image_upscale._upscale_image_by_multiple,
        )

    def test_package_canonical_image_objects_preserve_behavior(self):
        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            package_name = package_nodes.__package__
            package_scaling = sys.modules[f"{package_name}.easyuse_anima.image.scaling"]
            package_detailer = sys.modules[f"{package_name}.easyuse_anima.image.detailer"]
            package_sam3_detailer = sys.modules[
                f"{package_name}.easyuse_anima.image.sam3_detailer"
            ]
            package_upscale = sys.modules[f"{package_name}.easyuse_anima.image.upscale"]
            package_invocation = sys.modules[
                f"{package_name}.easyuse_anima.infrastructure.comfy.invocation"
            ]
            package_node_adapters = sys.modules[
                f"{package_name}.easyuse_anima.nodes.image_nodes"
            ]
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
                package_sam3_detailer._EasyUseAnimaAlignedDetailerHook,
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
                    self.assertIs(
                        package_entrypoint.NODE_CLASS_MAPPINGS[name],
                        canonical_class,
                    )
            self.assertIs(
                package_upscale._common_upscale_image,
                package_invocation._common_upscale_image,
            )
            self.assertIs(
                package_node_adapters._upscale_image_by_multiple,
                package_upscale._upscale_image_by_multiple,
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

    def test_canonical_wildcard_node_preserves_seed_tooltip(self):
        self.assertIn(
            wildcard_nodes.WILDCARD_SEED_RANGE_NOTE,
            wildcard_nodes.EasyUseAnimaWildcard.INPUT_TYPES()["required"]["seed"][1][
                "tooltip"
            ],
        )

    def test_package_mappings_use_canonical_wildcard_and_naia_nodes(self):
        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            package_name = package_nodes.__package__
            package_naia_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.naia_nodes"
            ]
            package_wildcard_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.wildcard_nodes"
            ]
            self.assertIs(
                package_entrypoint.NODE_CLASS_MAPPINGS["EasyUseAnimaWildcard"],
                package_wildcard_nodes.EasyUseAnimaWildcard,
            )
            self.assertIs(
                package_entrypoint.NODE_CLASS_MAPPINGS[
                    "EasyUseAnimaNAIARandomPrompt"
                ],
                package_naia_nodes.EasyUseAnimaNAIARandomPrompt,
            )


class WorkflowLookupMoveContractTests(unittest.TestCase):
    def test_canonical_workflow_lookup_preserves_top_level_and_subgraph_behavior(self):
        inner_node = {"id": 7, "title": "inner"}
        extra_pnginfo = {
            "workflow": {
                "nodes": [{"id": 3, "type": "nested-graph", "title": "outer"}],
                "definitions": {
                    "subgraphs": [
                        {"id": "nested-graph", "nodes": [inner_node]},
                    ],
                },
            },
        }
        original = json.loads(json.dumps(extra_pnginfo))

        self.assertEqual(
            workflow._get_workflow_node(extra_pnginfo, "3")["title"],
            "outer",
        )
        self.assertIs(
            workflow._get_workflow_node([extra_pnginfo], "3:7"),
            inner_node,
        )
        self.assertIsNone(workflow._get_workflow_node(extra_pnginfo, "missing"))
        self.assertIsNone(workflow._get_workflow_node(None, "3"))
        self.assertEqual(extra_pnginfo, original)

    def test_wildcard_naia_adapters_use_the_canonical_workflow_lookup(self):
        for adapter in (wildcard_nodes, naia_nodes):
            with self.subTest(adapter=adapter.__name__):
                self.assertIs(
                    adapter._get_workflow_node,
                    workflow._get_workflow_node,
                )

    def test_retired_prompt_adapters_use_the_canonical_workflow_lookup(self):
        for adapter in (prompt_advanced_nodes, regional_nodes):
            with self.subTest(adapter=adapter.__name__):
                self.assertIs(adapter._get_workflow_node, workflow._get_workflow_node)


class InputTypeMoveContractTests(unittest.TestCase):
    def test_shared_input_type_behavior_and_flat_root_identity(self):
        wildcard_type = input_types._AnyType("*")
        self.assertFalse(wildcard_type != "IMAGE")

        optional_inputs = input_types._FlexibleOptionalInputType(
            input_types._ANY_TYPE
        )
        self.assertIn("arbitrary_name", optional_inputs)
        self.assertIs(
            optional_inputs["arbitrary_name"][0],
            input_types._ANY_TYPE,
        )

        self.assertIs(lora_nodes._ANY_TYPE, input_types._ANY_TYPE)
        for adapter in (
            lora_nodes,
            prompt_advanced_nodes,
            regional_nodes,
            wildcard_nodes,
        ):
            with self.subTest(adapter=adapter.__name__):
                self.assertIs(
                    adapter._FlexibleOptionalInputType,
                    input_types._FlexibleOptionalInputType,
                )

    def test_package_adapters_share_the_canonical_input_types(self):
        with _loaded_package_entrypoint() as (_, package_nodes):
            package_name = package_nodes.__package__
            package_input_types = sys.modules[
                f"{package_name}.easyuse_anima.nodes.input_types"
            ]
            package_adapters = (
                sys.modules[f"{package_name}.easyuse_anima.nodes.lora_nodes"],
                sys.modules[
                    f"{package_name}.easyuse_anima.nodes.prompt_advanced_nodes"
                ],
                sys.modules[
                    f"{package_name}.easyuse_anima.nodes.regional_nodes"
                ],
                sys.modules[f"{package_name}.easyuse_anima.nodes.wildcard_nodes"],
            )

            self.assertIs(
                package_adapters[0]._ANY_TYPE,
                package_input_types._ANY_TYPE,
            )
            for adapter in package_adapters:
                with self.subTest(adapter=adapter.__name__):
                    self.assertIs(
                        adapter._FlexibleOptionalInputType,
                        package_input_types._FlexibleOptionalInputType,
                    )


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

    def test_canonical_lora_owners_have_no_runtime_binders(self):
        for module, binder_name in (
            (lora_metadata, "_bind_lora_metadata_runtime"),
            (lora_preset, "_bind_lora_preset_runtime"),
            (lora_nodes, "_bind_lora_node_runtime"),
        ):
            with self.subTest(module=module.__name__, binder=binder_name):
                self.assertFalse(hasattr(module, binder_name))

    def test_package_mapping_uses_canonical_lora_node(self):
        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            package_name = package_nodes.__package__
            package_lora_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.lora_nodes"
            ]
            self.assertIs(
                package_entrypoint.NODE_CLASS_MAPPINGS["EasyUseAnimaLoraPreset"],
                package_lora_nodes.EasyUseAnimaLoraPreset,
            )

    def test_canonical_monkeypatches_drive_the_canonical_lora_node(self):
        canonical_node = lora_nodes.EasyUseAnimaLoraPreset()
        with (
            patch.object(lora_nodes, "_correct_style_prompt", side_effect=lambda value: f"bound:{value}"),
            patch.object(lora_nodes, "_get_lora_info", return_value=("foo.safetensors", ["@bound"])),
            patch.object(lora_nodes, "_lora_model_exists", return_value=True),
        ):
            result = canonical_node.build(
                style_prompt="style",
                profile_index=1,
                loras='[{"name":"foo.safetensors","strength":1}]',
                profile_data="{}",
            )["result"]

        self.assertEqual(result[0], "bound:style")
        self.assertEqual(result[2], "@bound")

    def test_metadata_and_preset_callbacks_remain_use_time(self):
        logger = types.SimpleNamespace(warning=Mock())
        with (
            patch.object(lora_metadata, "_resolve_logger", return_value=logger),
            patch.object(prompt_fields, "_prompt_tokens", return_value=["@bound"]) as tokens,
            patch.object(
                prompt_fields,
                "_correct_builder_prompt",
                return_value="corrected",
            ) as correct,
        ):
            lora_metadata.logger.warning("message")
            self.assertEqual(
                lora_metadata._trigger_words_from_value("source"),
                ["@bound"],
            )
            self.assertEqual(lora_preset._correct_style_prompt("style"), "corrected")

        logger.warning.assert_called_once_with("message")
        tokens.assert_called_once_with("source")
        correct.assert_called_once_with("style")

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

    def test_canonical_prompt_corrector_owners_have_no_runtime_binders(self):
        self.assertFalse(hasattr(prompt_correction, "_bind_prompt_correction_runtime"))
        self.assertFalse(hasattr(prompt_nodes, "_bind_prompt_node_runtime"))

    def test_package_mappings_use_canonical_prompt_corrector_nodes(self):
        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            package_name = package_nodes.__package__
            package_prompt_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.prompt_nodes"
            ]
            for name in self.NODE_CLASSES:
                with self.subTest(name=name):
                    self.assertIs(
                        package_entrypoint.NODE_CLASS_MAPPINGS[name],
                        getattr(package_prompt_nodes, name),
                    )

    def test_canonical_service_and_adapter_monkeypatches_drive_prompt_corrector_nodes(self):
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
                prompt_correction,
                "resolve_prompt_translation_settings",
                return_value=settings,
            ) as resolve_settings,
            patch.object(
                prompt_nodes,
                "_prompt_translation_change_key",
                return_value={"bound": "translation"},
            ) as translation_key,
            patch.object(
                prompt_nodes,
                "_stable_change_key",
                side_effect=lambda payload: payload,
            ) as stable_key,
            patch.object(
                prompt_nodes,
                "load_knowledge_base",
                return_value="bound kb",
            ) as load_kb,
            patch.object(
                prompt_nodes,
                "correct_prompt",
                return_value=correction_result,
            ) as correct,
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

    def test_canonical_translation_monkeypatches_drive_the_canonical_helper(self):
        settings = types.SimpleNamespace(provider="off", source="auto", target="en")

        with (
            patch.object(
                prompt_correction,
                "has_prompt_translation_markers",
                return_value=False,
            ) as has_markers,
            patch.object(prompt_correction, "translate_prompt_markers") as translate_markers,
        ):
            untranslated = prompt_correction._translate_prompt_text("%{abc}")

        self.assertEqual(untranslated, "%{abc}")
        has_markers.assert_called_once_with("%{abc}")
        translate_markers.assert_not_called()

        with (
            patch.object(
                prompt_correction,
                "has_prompt_translation_markers",
                return_value=True,
            ) as has_markers,
            patch.object(
                prompt_correction,
                "translate_prompt_markers",
                return_value="bound",
            ) as translate_markers,
            patch.object(
                prompt_correction,
                "resolve_prompt_translation_settings",
                return_value=settings,
            ) as resolve_settings,
        ):
            translated = prompt_correction._translate_prompt_text("%{abc}")

        self.assertEqual(translated, "bound")
        has_markers.assert_called_once_with("%{abc}")
        resolve_settings.assert_called_once_with()
        translate_markers.assert_called_once_with("%{abc}", settings)

    def test_translation_stays_outside_the_correction_error_mapping(self):
        with patch.object(
            prompt_nodes,
            "_translate_prompt_text",
            side_effect=ValueError("translate"),
        ):
            with self.assertRaisesRegex(ValueError, "^translate$"):
                prompt_nodes.EasyUseAnimaPromptCorrector().correct("prompt", "", "")

        with patch.object(
            prompt_nodes,
            "load_knowledge_base",
            side_effect=ValueError("correct"),
        ):
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
    ARTIST_MIX_PRIMITIVE_ALIASES = (
        "ARTIST_MIX_DEFAULT_CLUSTER_COUNT",
        "ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION",
        "ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD",
        "ARTIST_MIX_DEFAULT_EXACT_TOP_K",
        "ARTIST_MIX_DEFAULT_RMS_SCALE_CAP",
        "ARTIST_MIX_DEFAULT_START_PERCENT",
        "ARTIST_MIX_DEFAULT_STRENGTH_SCALE",
        "ARTIST_MIX_DEFAULT_STYLE_GAIN",
        "ARTIST_MIX_MODE_AVERAGE",
        "ARTIST_MIX_MODE_AVERAGE_LATE_EXACT",
        "ARTIST_MIX_MODE_CLUSTERED",
        "ARTIST_MIX_MODE_COMPOSITE_EXACT",
        "ARTIST_MIX_MODE_DELTA_RMS",
        "ARTIST_MIX_MODE_EXACT",
        "ARTIST_MIX_MODE_FROM_PROMPT_DATA",
        "ARTIST_MIX_MODE_HYBRID",
        "ARTIST_MIX_MODE_LATE_EXACT",
        "ARTIST_MIX_MODE_OFF",
        "ARTIST_MIX_MODE_PROMPT",
        "ARTIST_MIX_MODE_SCHEDULED_AVERAGE",
        "ARTIST_MIX_MODES",
        "_ARTIST_GROUP_RE",
        "_SECTION_SEPARATOR_RE",
        "_WEIGHTED_ARTIST_RE",
        "_artist_group_token",
        "_artist_mix_inline_prompt",
        "_artist_tags_from_prompt",
        "_bounded_artist_mix_float",
        "_bounded_artist_mix_int",
        "_join_artist_mix_source_prompts",
        "_normalize_artist_mix_mode",
        "_parse_artist_mix_entries",
        "_parse_artist_mix_group",
        "_parse_artist_mix_items",
        "_split_artist_mix_blocks",
        "_split_artist_mix_items",
    )
    ADVANCED_ARTIST_MIX_PRIMITIVE_ALIASES = (
        "ARTIST_MIX_DEFAULT_CLUSTER_COUNT",
        "ARTIST_MIX_DEFAULT_DOMINANT_ISOLATION",
        "ARTIST_MIX_DEFAULT_DOMINANT_THRESHOLD",
        "ARTIST_MIX_DEFAULT_EXACT_TOP_K",
        "ARTIST_MIX_DEFAULT_RMS_SCALE_CAP",
        "ARTIST_MIX_DEFAULT_START_PERCENT",
        "ARTIST_MIX_DEFAULT_STRENGTH_SCALE",
        "ARTIST_MIX_DEFAULT_STYLE_GAIN",
        "ARTIST_MIX_MODE_OFF",
        "ARTIST_MIX_MODE_PROMPT",
        "_artist_mix_inline_prompt",
        "_artist_tags_from_prompt",
        "_bounded_artist_mix_float",
        "_bounded_artist_mix_int",
        "_join_artist_mix_source_prompts",
        "_normalize_artist_mix_mode",
        "_parse_artist_mix_items",
    )
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
    RETIRED_ARTIST_MIX_PARSING_ALIASES = (
        "_artist_group_token",
        "_artist_mix_prompt_tags",
        "_artist_variant_prompt_from_prompt_data",
        "_coalesce_artist_mix_items",
        "_parse_artist_mix_entries",
        "_parse_artist_mix_group",
        "_prompt_data_artist_base_prompt",
        "_prompt_data_artist_mix_config",
        "_prompt_data_positive_fields",
        "_split_artist_mix_blocks",
        "_split_artist_mix_items",
    )
    RETIRED_ARTIST_MIX_MODE_ALIASES = (
        "ARTIST_MIX_CONTROL_KEY",
        "ARTIST_MIX_EXACT_KEY",
        "ARTIST_MIX_MODES",
        "ARTIST_MIX_MODE_AVERAGE",
        "ARTIST_MIX_MODE_AVERAGE_LATE_EXACT",
        "ARTIST_MIX_MODE_CLUSTERED",
        "ARTIST_MIX_MODE_COMPOSITE_EXACT",
        "ARTIST_MIX_MODE_DELTA_RMS",
        "ARTIST_MIX_MODE_DESCRIPTIONS",
        "ARTIST_MIX_MODE_EXACT",
        "ARTIST_MIX_MODE_HYBRID",
        "ARTIST_MIX_MODE_LATE_EXACT",
        "ARTIST_MIX_MODE_OFF",
        "ARTIST_MIX_MODE_PROMPT",
        "ARTIST_MIX_MODE_SCHEDULED_AVERAGE",
        "ARTIST_MIX_SCHEDULE_KEY",
        "ARTIST_MIX_STUDIO_MODES",
        "ARTIST_TAG_POSITION_BACK",
        "ARTIST_TAG_POSITION_CORRECT",
        "ARTIST_TAG_POSITION_FRONT",
        "ARTIST_TAG_POSITION_MODES",
    )
    RETIRED_ARTIST_MIX_CONDITIONING_ALIASES = (
        "_artist_conditioning_feature",
        "_artist_delta_rms_from_encoded",
        "_conditionings_with_range",
        "_conditionings_with_strength",
        "_conditionings_with_values",
        "_copy_conditioning_metadata",
        "_encode_artist_average",
        "_encode_artist_average_late_exact",
        "_encode_artist_composite_exact",
        "_encode_artist_exact",
        "_encode_artist_hybrid",
        "_encode_artist_scheduled_average",
        "_encoded_artist_conditionings",
        "_equal_artist_weights",
        "_fallback_artist_average_or_exact",
        "_greedy_cluster_encoded_artists",
        "_interpolate_artist_weights",
        "_mark_artist_mix_conditioning",
        "_normalize_weight_values",
        "_normalized_artist_weights",
        "_pad_conditioning_tensor",
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

    def test_canonical_prompt_data_owners_have_no_runtime_binders(self):
        self.assertFalse(hasattr(prompt_artist_mix, "_bind_artist_mix_runtime"))
        self.assertFalse(hasattr(prompt_conditioning, "_bind_conditioning_runtime"))
        self.assertFalse(hasattr(prompt_data_nodes, "_bind_prompt_data_node_runtime"))

    def test_artist_mix_primitives_keep_canonical_alias_identity(self):
        for name in self.ARTIST_MIX_PRIMITIVE_ALIASES:
            with self.subTest(module="artist_mix", name=name):
                self.assertIs(
                    getattr(prompt_artist_mix, name),
                    getattr(prompt_artist_mix_primitives, name),
                )
        for name in self.ADVANCED_ARTIST_MIX_PRIMITIVE_ALIASES:
            with self.subTest(module="advanced", name=name):
                self.assertIs(
                    getattr(prompt_advanced, name),
                    getattr(prompt_artist_mix_primitives, name),
                )

    def test_package_entrypoint_mappings_keep_canonical_class_identity_and_display(self):
        expected_display = {
            "EasyUseAnimaPromptDataUnpack": prompt_data.PROMPT_DATA_TYPE,
            "EasyUseAnimaArtistMixConditioning": "Anima Artist Mix Conditioning",
            "EasyUseAnimaPromptDataConditioning": "Anima Prompt Data Conditioning",
        }
        with _loaded_package_entrypoint() as (package_entry, package_nodes):
            package_name = package_nodes.__package__
            package_adapters = sys.modules[
                f"{package_name}.easyuse_anima.nodes.prompt_data_nodes"
            ]
            for name in self.NODE_CLASSES:
                with self.subTest(name=name):
                    canonical_class = getattr(package_adapters, name)
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
            (
                prompt_data.PROMPT_DATA_TYPE,
                *prompt_advanced_nodes.EasyUseAnimaPromptStudioAdvanced.RETURN_TYPES,
            ),
        )
        self.assertEqual(
            prompt_data_nodes.EasyUseAnimaPromptDataUnpack.RETURN_NAMES,
            (
                prompt_data.PROMPT_DATA_TYPE,
                *prompt_advanced_nodes.EasyUseAnimaPromptStudioAdvanced.RETURN_NAMES,
            ),
        )

    def test_canonical_change_key_monkeypatch_drives_canonical_adapter(self):
        with patch.object(
            prompt_data_nodes,
            "_stable_change_key",
            side_effect=lambda value: value,
        ) as stable:
            change_key = prompt_data_nodes.EasyUseAnimaPromptDataUnpack.IS_CHANGED(
                {prompt_data.PROMPT_DATA_TYPE: True}
            )

        self.assertEqual(change_key["mode"], "prompt_data_unpack")
        self.assertEqual(change_key["prompt_data"], {prompt_data.PROMPT_DATA_TYPE: True})
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

    def test_canonical_prompt_builder_owners_have_no_runtime_binders(self):
        self.assertFalse(hasattr(prompt_fields, "_bind_prompt_fields_runtime"))
        self.assertFalse(hasattr(prompt_nodes, "_bind_prompt_node_runtime"))

    def test_package_mappings_use_canonical_prompt_builder_nodes(self):
        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            package_name = package_nodes.__package__
            package_prompt_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.prompt_nodes"
            ]
            for name in self.NODE_CLASSES:
                with self.subTest(module="prompt_nodes", name=name):
                    self.assertIs(
                        package_entrypoint.NODE_CLASS_MAPPINGS[name],
                        getattr(package_prompt_nodes, name),
                    )

    def test_classic_studio_directly_inherits_the_canonical_builder(self):
        self.assertEqual(
            prompt_nodes.EasyUseAnimaPromptStudio.__bases__,
            (prompt_nodes.EasyUseAnimaPromptBuilder,),
        )
        self.assertTrue(
            issubclass(
                prompt_nodes.EasyUseAnimaPromptStudio,
                prompt_nodes.EasyUseAnimaPromptBuilder,
            )
        )

    def test_canonical_parser_and_correction_monkeypatches_drive_canonical_fields(self):
        parsed = types.SimpleNamespace(tokens=("  bound_token  ",))
        correction_result = types.SimpleNamespace(text="bound correction")

        with patch.object(prompt_fields, "parse_prompt", return_value=parsed) as parser:
            tokens = prompt_fields._prompt_tokens("source")

        self.assertEqual(tokens, ["bound_token"])
        parser.assert_called_once_with("source", profile="prompt")

        with (
            patch.object(
                prompt_fields,
                "_prompt_tokens",
                return_value=["bound_artist"],
            ) as tokens,
            patch.object(
                prompt_fields,
                "load_knowledge_base",
                return_value="bound kb",
            ) as load_kb,
            patch.object(
                prompt_fields,
                "correct_prompt",
                return_value=correction_result,
            ) as correct,
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

    def test_canonical_adapter_monkeypatches_drive_builder_order_and_change_key(self):
        with (
            patch.object(
                prompt_nodes,
                "_stable_change_key",
                side_effect=lambda value: value,
            ) as stable,
            patch.object(
                prompt_nodes,
                "_prompt_translation_change_key",
                return_value={"bound": "translation"},
            ) as translation_key,
            patch.object(
                prompt_nodes,
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
            patch.object(prompt_nodes, "_as_bool", side_effect=(True, False)),
            patch.object(
                prompt_nodes,
                "_translate_prompt_text",
                side_effect=lambda value: f"t:{value}",
            ),
            patch.object(
                prompt_nodes,
                "_join_prompt_tokens",
                side_effect=lambda *parts: "|".join(parts),
            ),
            patch.object(
                prompt_nodes,
                "_correct_builder_prompt",
                side_effect=lambda value, artist_overrides="": f"c:{value}:{artist_overrides}",
            ),
            patch.object(
                prompt_nodes,
                "_filter_metadata_prompt",
                side_effect=lambda prompt, words: f"f:{prompt}:{words}",
            ),
            patch.object(
                prompt_nodes,
                "resolve_metadata_filter_words",
                return_value="filters",
            ),
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

    def test_canonical_advanced_owners_have_no_runtime_binders(self):
        self.assertFalse(hasattr(prompt_advanced, "_bind_advanced_runtime"))
        self.assertFalse(
            hasattr(prompt_advanced_nodes, "_bind_prompt_advanced_node_runtime")
        )

    def test_package_mappings_use_canonical_advanced_nodes(self):
        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            package_name = package_nodes.__package__
            package_advanced_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.prompt_advanced_nodes"
            ]

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

    def test_canonical_monkeypatches_drive_the_advanced_change_key(self):
        with (
            patch.object(
                prompt_advanced_nodes,
                "_stable_change_key",
                side_effect=lambda value: value,
            ) as stable,
            patch.object(
                prompt_advanced_nodes,
                "_prompt_translation_change_key",
                return_value={"bound": "translation"},
            ) as translation_key,
            patch.object(
                prompt_advanced_nodes,
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

    def test_canonical_naia_monkeypatch_drives_advanced_and_extend(self):
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
            patch.object(
                prompt_advanced_nodes,
                "EasyUseAnimaNAIARandomPrompt",
                BoundNAIARandomPrompt,
            ),
            patch.object(
                prompt_advanced_nodes,
                "resolve_naia_settings",
                return_value=settings,
            ),
            patch.object(
                prompt_advanced_nodes,
                "_post_random",
                side_effect=post_random,
            ),
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


class RegionalMoveContractTests(unittest.TestCase):
    RETIRED_REGIONAL_ALIASES = (
        "REGIONAL_CONFIG_VERSION",
        "REGIONAL_CONFIG_WORKFLOW_PROPERTY",
        "REGIONAL_FIELDS_WORKFLOW_PROPERTY",
        "REGIONAL_FIELD_TYPES",
        "REGIONAL_PROMPT_BUNDLE_SCHEMA",
        "REGIONAL_PROMPT_DATA_SCHEMA",
        "REGIONAL_PROMPT_DATA_TYPE",
        "_normalize_mask_geometry",
        "_normalize_regional_mask",
        "_regional_default_config",
        "_regional_default_fields",
        "_regional_field_prompt",
    )
    SERVICE_OBJECTS = (
        "_apply_regional_field_inputs",
        "_build_regional_outputs",
        "_clone_regional_fields",
        "_conditioning_set_values",
        "_normalize_mask_ids",
        "_normalize_regional_config",
        "_normalize_regional_fields",
        "_parse_json_object",
        "_regional_config_json",
        "_regional_fields_json",
        "_regional_mask_bounds_area",
        "_regional_payload_canvas",
        "_regional_union_mask_for_ids",
    )
    NODE_CLASSES = (
        "EasyUseAnimaPromptStudioRegional",
        "EasyUseAnimaRegionalConditioning",
    )

    def test_canonical_regional_owners_have_no_runtime_binders(self):
        self.assertFalse(hasattr(prompt_regional, "_bind_regional_runtime"))
        self.assertFalse(hasattr(regional_nodes, "_bind_regional_node_runtime"))

    def test_package_mappings_use_canonical_regional_nodes(self):
        expected_display = {
            "EasyUseAnimaPromptStudioRegional": "Anima Prompt Studio Regional",
            "EasyUseAnimaRegionalConditioning": "Anima Regional Conditioning",
        }
        with _loaded_package_entrypoint() as (package_entrypoint, package_nodes):
            package_name = package_nodes.__package__
            package_regional_nodes = sys.modules[
                f"{package_name}.easyuse_anima.nodes.regional_nodes"
            ]
            for name in self.NODE_CLASSES:
                with self.subTest(module="regional_nodes", name=name):
                    canonical_class = getattr(package_regional_nodes, name)
                    self.assertIs(package_entrypoint.NODE_CLASS_MAPPINGS[name], canonical_class)
                    self.assertEqual(
                        package_entrypoint.NODE_DISPLAY_NAME_MAPPINGS[name],
                        expected_display[name],
                    )


class PublicNodeContractTests(unittest.TestCase):
    def test_generated_contract_matches_versioned_fixture(self):
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(build_contract_snapshot(), expected)

    def test_package_mappings_use_the_canonical_runtime_class_objects(self):
        class_mappings, display_mappings = _registration_mappings()

        with _loaded_package_entrypoint() as (package_entrypoint, _):
            runtime_mappings = package_entrypoint.NODE_CLASS_MAPPINGS
            package_registration = sys.modules[
                f"{package_entrypoint.__package__}.easyuse_anima.registration"
            ]
            self.assertIs(runtime_mappings, package_registration.NODE_CLASS_MAPPINGS)
            self.assertIs(
                package_entrypoint.NODE_DISPLAY_NAME_MAPPINGS,
                package_registration.NODE_DISPLAY_NAME_MAPPINGS,
            )
            self.assertEqual(list(runtime_mappings), [node_id for node_id, _ in class_mappings])
            self.assertEqual(package_entrypoint.NODE_DISPLAY_NAME_MAPPINGS, display_mappings)
            self.assertEqual(
                package_entrypoint.__all__,
                [
                    "NODE_CLASS_MAPPINGS",
                    "NODE_DISPLAY_NAME_MAPPINGS",
                    "WEB_DIRECTORY",
                ],
            )
            for node_id, class_name in class_mappings:
                with self.subTest(node_id=node_id):
                    mapped_class = runtime_mappings[node_id]
                    self.assertEqual(mapped_class.__name__, class_name)
                    self.assertFalse(hasattr(package_entrypoint, class_name))

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
