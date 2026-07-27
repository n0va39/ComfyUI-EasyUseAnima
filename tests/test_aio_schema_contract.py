from __future__ import annotations

import copy
import io
import json
import re
import subprocess
import tarfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import nodes
from easyuse_anima.aio import generation_normalization
from easyuse_anima.aio.generation_migrations import (
    AIO_GENERATION_STAGE_IDS,
    AIO_MODEL_PATCH_ORDER_REVISION,
    AIO_MODEL_PATCH_PRECEDENCE,
)
from easyuse_anima.aio.generation_settings import (
    _aio_generation_config_from_dict,
)
from easyuse_anima.aio.negpip import NEGPIP_MODES
from easyuse_anima.prompt.conditioning import ANIMA_MOD_GUIDANCE_PROFILES
from tests.comfy_host_fakes import (
    FakeComfyHostProvider,
    patch_comfy_helper,
    use_fake_comfy_host,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "easyuse_anima" / "aio" / "schemas" / "generation_settings.v3.json"
MANIFEST_REPOSITORY_PATH = MANIFEST_PATH.relative_to(ROOT).as_posix()
FRONTEND_SETTINGS_PATH = ROOT / "web" / "js" / "aio" / "settings.js"
AIO_WORKFLOW_0_5_2_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "aio_generation_settings_0_5_2.json"
SURFACE_COVERAGE_PATH = (
    ROOT / "tests" / "fixtures" / "aio_generation_settings_surface_coverage.v3.json"
)
REQUIRED_SETTING_SURFACES = (
    "python_default",
    "python_typed",
    "frontend_default",
    "frontend_sanitization",
    "ui",
    "documentation",
)

_DEFAULT_COMFY_HOST = use_fake_comfy_host(nodes, FakeComfyHostProvider())


def setUpModule():
    _DEFAULT_COMFY_HOST.__enter__()


def tearDownModule():
    _DEFAULT_COMFY_HOST.__exit__(None, None, None)


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _surface_coverage() -> dict:
    return json.loads(SURFACE_COVERAGE_PATH.read_text(encoding="utf-8"))


def _resolve_contract(manifest: dict, contract: dict) -> dict:
    while "$ref" in contract:
        reference = contract["$ref"]
        if not reference.startswith("#/"):
            raise AssertionError(f"Unsupported manifest reference: {reference}")
        resolved = manifest
        for part in reference[2:].split("/"):
            resolved = resolved[part]
        contract = resolved
    return contract


def _leaf_contracts(manifest: dict, contract: dict, path: tuple[str, ...] = ()):
    contract = _resolve_contract(manifest, contract)
    fields = contract.get("fields")
    if isinstance(fields, dict) and fields:
        for name, child in fields.items():
            yield from _leaf_contracts(manifest, child, (*path, name))
        return
    yield path, contract


def _contract_nodes(contract: dict, path: tuple[str, ...] = ()):
    yield path, contract
    for group_name in ("fields", "pattern_fields"):
        children = contract.get(group_name)
        if isinstance(children, dict):
            for name, child in children.items():
                if isinstance(child, dict):
                    yield from _contract_nodes(child, (*path, group_name, name))
    for child_name in ("items", "additional_properties"):
        child = contract.get(child_name)
        if isinstance(child, dict):
            yield from _contract_nodes(child, (*path, child_name))
    for group_name in ("one_of", "any_of"):
        children = contract.get(group_name)
        if isinstance(children, list):
            for index, child in enumerate(children):
                if isinstance(child, dict):
                    yield from _contract_nodes(child, (*path, group_name, str(index)))


def _all_contract_nodes(manifest: dict):
    yield from _contract_nodes(manifest["shape"], ("shape",))
    for name, definition in manifest["definitions"].items():
        yield from _contract_nodes(definition, ("definitions", name))


def _coercion_references(value):
    if isinstance(value, dict):
        for name, child in value.items():
            if name in {"coercion", "item_coercion"} and isinstance(child, str):
                yield child
            yield from _coercion_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from _coercion_references(child)


def _default_leaves(value, path: tuple[str, ...] = ()):
    if isinstance(value, dict) and value:
        for name, child in value.items():
            yield from _default_leaves(child, (*path, name))
        return
    yield path, value


def _contract_surface_paths(contract: dict, path: tuple[str, ...]):
    if "$ref" in contract:
        yield "/" + "/".join(path)
        return
    fields = contract.get("fields")
    if isinstance(fields, dict) and fields:
        for name, child in fields.items():
            yield from _contract_surface_paths(child, (*path, name))
        return
    yield "/" + "/".join(path)


def _all_contract_surface_paths(manifest: dict) -> tuple[str, ...]:
    paths = list(_contract_surface_paths(manifest["shape"], ("shape",)))
    for name, definition in manifest["definitions"].items():
        paths.extend(
            _contract_surface_paths(definition, ("definitions", name))
        )
    return tuple(sorted(paths))


def _manifest_shape_default_failures(manifest: dict) -> list[str]:
    contract_paths = {
        "/shape/" + "/".join(path)
        for path, _contract in _leaf_contracts(manifest, manifest["shape"])
    }
    default_paths = {
        "/shape/" + "/".join(path)
        for path, _value in _default_leaves(manifest["default"])
    }
    return [
        *(
            f"{path}: missing surface manifest_default"
            for path in sorted(contract_paths - default_paths)
        ),
        *(
            f"{path}: missing surface manifest_shape"
            for path in sorted(default_paths - contract_paths)
        ),
    ]


def _coverage_entries(coverage: dict) -> tuple[dict[str, dict], list[str]]:
    groups = coverage.get("groups")
    if not isinstance(groups, list) or not groups:
        return {}, ["surface coverage: groups must be a non-empty array"]

    entries: dict[str, dict] = {}
    failures: list[str] = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict) or set(group) != {"coverage", "paths"}:
            failures.append(
                f"surface coverage: groups[{index}] must contain coverage and paths"
            )
            continue
        record = group["coverage"]
        paths = group["paths"]
        if not isinstance(record, dict):
            failures.append(f"surface coverage: groups[{index}].coverage must be an object")
            continue
        if (
            not isinstance(paths, list)
            or not paths
            or any(not isinstance(path, str) or not path.startswith("/") for path in paths)
        ):
            failures.append(
                f"surface coverage: groups[{index}].paths must be canonical paths"
            )
            continue
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            failures.append(
                f"surface coverage: groups[{index}].paths must be sorted and unique"
            )
        for path in paths:
            if path in entries:
                failures.append(f"{path}: duplicate surface coverage entry")
            else:
                entries[path] = record
    return entries, failures


def _surface_coverage_failures(manifest: dict, coverage: dict) -> list[str]:
    expected_paths = set(_all_contract_surface_paths(manifest))
    entries, failures = _coverage_entries(coverage)
    required = tuple(coverage.get("required_surfaces", ()))
    if required != REQUIRED_SETTING_SURFACES:
        failures.append(
            "surface coverage: required_surfaces changed: "
            f"expected {list(REQUIRED_SETTING_SURFACES)!r}, got {list(required)!r}"
        )

    entry_paths = set(entries)
    for path in sorted(expected_paths - entry_paths):
        for surface in REQUIRED_SETTING_SURFACES:
            failures.append(f"{path}: missing surface {surface}")
    for path in sorted(entry_paths - expected_paths):
        failures.append(f"{path}: stale surface coverage entry")

    owners = coverage.get("owners")
    if not isinstance(owners, dict):
        failures.append("surface coverage: owners must be an object")
        owners = {}
    owner_registries: dict[str, dict] = {}
    for surface in REQUIRED_SETTING_SURFACES:
        surface_owners = owners.get(surface)
        if not isinstance(surface_owners, dict) or not surface_owners:
            failures.append(f"surface coverage: missing owner registry {surface}")
            surface_owners = {}
        owner_registries[surface] = surface_owners

    for path in sorted(expected_paths & entry_paths):
        record = entries[path]
        if not isinstance(record, dict):
            failures.append(f"{path}: surface record must be an object")
            continue
        missing = [name for name in REQUIRED_SETTING_SURFACES if name not in record]
        extra = sorted(set(record) - set(REQUIRED_SETTING_SURFACES))
        for name in missing:
            failures.append(f"{path}: missing surface {name}")
        for name in extra:
            failures.append(f"{path}: unsupported surface {name}")
        for surface in REQUIRED_SETTING_SURFACES:
            owner = record.get(surface)
            if not isinstance(owner, str) or not owner:
                failures.append(f"{path}: invalid owner for surface {surface}")
            elif owner not in owner_registries[surface]:
                failures.append(
                    f"{path}: unknown owner {owner!r} for surface {surface}"
                )

    return failures


def _surface_owner_failures(coverage: dict) -> list[str]:
    failures: list[str] = []
    for surface, owners in coverage["owners"].items():
        for owner, metadata in owners.items():
            if not isinstance(metadata, dict):
                failures.append(f"{surface}/{owner}: owner metadata must be an object")
                continue
            if isinstance(metadata.get("module"), str):
                repository_paths = [metadata["module"]]
            elif (
                isinstance(metadata.get("modules"), list)
                and metadata["modules"]
                and all(isinstance(path, str) and path for path in metadata["modules"])
            ):
                repository_paths = metadata["modules"]
            elif isinstance(metadata.get("path"), str):
                repository_paths = [metadata["path"]]
            else:
                failures.append(f"{surface}/{owner}: owner path is missing")
                continue
            if surface == "ui" and metadata.get("exposure") not in {
                "editable",
                "hidden",
                "visible-readonly",
            }:
                failures.append(f"{surface}/{owner}: UI exposure must be explicit")
            if surface == "documentation" and not isinstance(
                metadata.get("heading"), str
            ):
                failures.append(
                    f"{surface}/{owner}: documentation heading must be explicit"
                )
            owner_paths: list[Path] = []
            for repository_path in repository_paths:
                owner_path = ROOT / repository_path
                owner_paths.append(owner_path)
                if not owner_path.is_file():
                    failures.append(
                        f"{surface}/{owner}: owner path does not exist: {repository_path}"
                    )
                    continue
                try:
                    tracked = _git("ls-files", "--error-unmatch", "--", repository_path)
                except subprocess.CalledProcessError:
                    failures.append(
                        f"{surface}/{owner}: owner path is not tracked: {repository_path}"
                    )
                else:
                    if tracked.stdout.strip() != repository_path:
                        failures.append(
                            f"{surface}/{owner}: owner path is not tracked: {repository_path}"
                        )
            heading = metadata.get("heading")
            if heading is not None:
                text = (
                    owner_paths[0].read_text(encoding="utf-8")
                    if owner_paths[0].is_file()
                    else ""
                )
                if not isinstance(heading, str) or heading not in text.splitlines():
                    failures.append(
                        f"{surface}/{owner}: documentation heading is missing: {heading!r}"
                    )
    return failures


def _delete_path(value: dict, path: tuple[str, ...]) -> None:
    current = value
    for name in path[:-1]:
        current = current[name]
    del current[path[-1]]


def _get_path(value: dict, path: tuple[str, ...]):
    current = value
    for name in path:
        current = current[name]
    return current


def _payload_with(path: tuple[str, ...], value) -> dict:
    payload: dict = {}
    current = payload
    for name in path[:-1]:
        current[name] = {}
        current = current[name]
    current[path[-1]] = value
    return payload


def _git(*args: str, binary: bool = False):
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
        timeout=30,
    )


@contextmanager
def _deterministic_capabilities(
    *,
    samplers=("er_sde", "euler"),
    schedulers=("simple",),
    impact_schedulers=("sgm_uniform",),
):
    with (
        patch.multiple(
            generation_normalization,
            _comfy_sampler_names=lambda: list(samplers),
            _comfy_scheduler_names=lambda: list(schedulers),
            _impact_scheduler_names=lambda: list(impact_schedulers),
        ),
        patch_comfy_helper(
            nodes,
            "_comfy_max_resolution",
            return_value=16384,
        ),
    ):
        yield


def _authoritative_static_enum_choices() -> dict[tuple[str, ...], tuple[str, ...]]:
    choices = {
        ("mode",): ("txt2img", "img2img", "inpaint"),
        ("sampler", "backend"): (
            "comfy_ksampler",
            "spectrum_mod_guidance_advanced",
            "spectrum_spd_speed",
        ),
        ("sampler", "seed_after_generate"): tuple(nodes.SEED_CONTROL_MODES),
        ("sampler", "spd", "split_mode"): ("single",),
        ("negpip", "mode"): tuple(NEGPIP_MODES),
        ("model_patches", "safe_pag", "rescale_mode"): ("full", "partial"),
        ("model_patches", "kj", "sage_attention"): (
            "disabled",
            "auto",
            "sageattn_qk_int8_pv_fp16_cuda",
            "sageattn_qk_int8_pv_fp16_triton",
            "sageattn_qk_int8_pv_fp8_cuda",
            "sageattn_qk_int8_pv_fp8_cuda++",
            "sageattn3",
            "sageattn3_per_block_mean",
        ),
        ("model_patches", "kj", "torch_compile", "backend"): ("inductor", "cudagraphs"),
        ("model_patches", "kj", "torch_compile", "mode"): (
            "default",
            "max-autotune",
            "max-autotune-no-cudagraphs",
            "reduce-overhead",
        ),
        ("model_patches", "kj", "torch_compile", "dynamic"): ("auto", "true", "false"),
        ("mod_guidance", "mode"): tuple(nodes.ANIMA_MOD_GUIDANCE_MODES),
        ("mod_guidance", "profile"): tuple(ANIMA_MOD_GUIDANCE_PROFILES),
        ("artist_mix", "mode"): tuple(nodes.ARTIST_MIX_INPUT_MODES),
        ("highres", "upscale_method"): tuple(nodes.IMAGE_UPSCALE_METHODS),
        ("highres", "multiple"): tuple(nodes.IMAGE_SCALE_MULTIPLES),
        ("upscale", "backend"): tuple(nodes.AIO_FINAL_UPSCALE_BACKENDS),
        ("upscale", "usdu", "prompt_mode"): tuple(nodes.AIO_USDU_PROMPT_MODES),
        ("upscale", "usdu", "mode_type"): tuple(nodes.AIO_USDU_MODE_TYPES),
        ("upscale", "usdu", "seam_fix_mode"): tuple(nodes.AIO_USDU_SEAM_FIX_MODES),
        ("upscale", "resshift", "scale"): tuple(nodes.AIO_RESHIFT_SCALES),
        ("upscale", "resshift", "dtype"): tuple(nodes.AIO_RESHIFT_DTYPES),
        ("postprocess", "fit", "mode"): tuple(nodes.AIO_FINAL_FIT_MODES),
        ("postprocess", "fit", "method"): tuple(nodes.IMAGE_UPSCALE_METHODS),
        ("detailer", "sam3", "context"): ("load_checkpoint",),
        ("save", "backend"): ("image_saver", "comfy_save_image"),
        ("save", "image_saver", "extension"): ("png", "jpeg", "jpg", "webp"),
    }
    for prefix in (
        ("sampler",),
        ("highres",),
        ("upscale",),
        ("detailer", "face"),
        ("detailer", "eye"),
    ):
        choices[(*prefix, "spectrum", "compat_policy")] = ("legacy", "conservative", "strict")
        choices[(*prefix, "dit_corrections", "dcw_mode")] = ("off", "manual", "auto")
        choices[(*prefix, "dit_corrections", "dcw_band_mask")] = ("LL", "all", "HH", "LH+HL+HH")
    for target_name in ("face", "eye"):
        choices[("detailer", target_name, "alignment")] = ("impact", "none", "32", "64")
    return choices


def _runtime_static_enum_choices(path: tuple[str, ...]) -> tuple[str, ...]:
    if path == ("mod_guidance", "profile"):
        return tuple(ANIMA_MOD_GUIDANCE_PROFILES)

    marker = "__capture_runtime_static_enum_choices__"
    observed: list[tuple[str, ...]] = []
    original_choice = generation_normalization._choice

    def capture_choice(value, choices, default):
        if value == marker:
            observed.append(tuple(choices or ()))
        return original_choice(value, choices, default)

    with _deterministic_capabilities(), patch.object(
        generation_normalization,
        "_choice",
        side_effect=capture_choice,
    ):
        nodes._normalize_aio_generation_settings(_payload_with(path, marker))
    if len(observed) != 1:
        raise AssertionError(f"Expected one runtime choice source for {path}, got {observed}")
    return observed[0]


class AIOGenerationSettingsManifestTests(unittest.TestCase):
    def test_manifest_default_matches_python_runtime_default(self):
        manifest = _manifest()

        manifest_paths = dict(_default_leaves(manifest["default"]))
        python_paths = dict(_default_leaves(nodes.AIO_GENERATION_DEFAULT_SETTINGS))
        failures = [
            *(
                f"/shape/{'/'.join(path)}: missing surface python_default"
                for path in sorted(set(manifest_paths) - set(python_paths))
            ),
            *(
                f"/shape/{'/'.join(path)}: stale surface python_default"
                for path in sorted(set(python_paths) - set(manifest_paths))
            ),
        ]
        if failures:
            self.fail("\n".join(failures))

        self.assertEqual(manifest["settings"]["schema"], nodes.AIO_GENERATION_SETTINGS_SCHEMA)
        self.assertEqual(manifest["settings"]["version"], nodes.AIO_GENERATION_SETTINGS_VERSION)
        self.assertEqual(manifest["default"], nodes.AIO_GENERATION_DEFAULT_SETTINGS)

    def test_every_manifest_default_leaf_is_owned_by_typed_config(self):
        manifest = _manifest()
        missing: list[str] = []

        for path, _value in _default_leaves(manifest["default"]):
            source = copy.deepcopy(nodes.AIO_GENERATION_DEFAULT_SETTINGS)
            _delete_path(source, path)
            try:
                _aio_generation_config_from_dict(source)
            except (TypeError, ValueError):
                continue
            missing.append(f"/shape/{'/'.join(path)}: missing surface python_typed")

        fetcher_fields = tuple(
            manifest["definitions"]["civitai_hash_fetcher"]["fields"]
        )
        fetcher = {
            "enabled": True,
            "username": "owner",
            "model_name": "model",
            "version": "v1",
        }
        for field in fetcher_fields:
            source = copy.deepcopy(nodes.AIO_GENERATION_DEFAULT_SETTINGS)
            source["save"]["image_saver"]["civitai_hash_fetchers"] = [
                {name: value for name, value in fetcher.items() if name != field}
            ]
            try:
                _aio_generation_config_from_dict(source)
            except (TypeError, ValueError):
                continue
            missing.append(
                f"/definitions/civitai_hash_fetcher/{field}: "
                "missing surface python_typed"
            )

        if missing:
            self.fail("\n".join(missing))

    def test_surface_coverage_registry_matches_every_manifest_contract_path(self):
        manifest = _manifest()
        coverage = _surface_coverage()

        self.assertEqual(
            coverage["schema"],
            "easyuse_anima_aio_generation_settings_surface_coverage",
        )
        self.assertEqual(coverage["version"], 3)
        self.assertEqual(coverage["manifest"], MANIFEST_REPOSITORY_PATH)
        self.assertEqual(
            [group["paths"][0] for group in coverage["groups"]],
            sorted(group["paths"][0] for group in coverage["groups"]),
            "Surface coverage groups must remain deterministically sorted",
        )
        failures = _surface_coverage_failures(manifest, coverage)
        if failures:
            self.fail("\n".join(failures))

    def test_surface_coverage_reports_exact_missing_path_and_surface(self):
        manifest = _manifest()
        coverage = _surface_coverage()
        path = coverage["groups"][0]["paths"][0]
        del coverage["groups"][0]["coverage"]["ui"]

        failures = _surface_coverage_failures(manifest, coverage)

        self.assertIn(f"{path}: missing surface ui", failures)
        self.assertNotIn(f"{path}: missing surface python_typed", failures)

        manifest["shape"]["fields"]["omission_probe"] = {"type": "string"}
        failures = _surface_coverage_failures(manifest, _surface_coverage())
        for surface in REQUIRED_SETTING_SURFACES:
            self.assertIn(
                f"/shape/omission_probe: missing surface {surface}",
                failures,
            )
        self.assertIn(
            "/shape/omission_probe: missing surface manifest_default",
            _manifest_shape_default_failures(manifest),
        )

        owner_coverage = _surface_coverage()
        ui_owner = next(iter(owner_coverage["owners"]["ui"]))
        documentation_owner = next(iter(owner_coverage["owners"]["documentation"]))
        del owner_coverage["owners"]["ui"][ui_owner]["exposure"]
        del owner_coverage["owners"]["documentation"][documentation_owner]["heading"]
        owner_failures = _surface_owner_failures(owner_coverage)
        self.assertIn(
            f"ui/{ui_owner}: UI exposure must be explicit",
            owner_failures,
        )
        self.assertIn(
            f"documentation/{documentation_owner}: documentation heading must be explicit",
            owner_failures,
        )

    def test_surface_coverage_owners_are_tracked_and_documented(self):
        coverage = _surface_coverage()
        failures = _surface_owner_failures(coverage)

        if failures:
            self.fail("\n".join(failures))

    def test_0_5_2_saved_aio_workflow_normalizes_generation_settings_identically(self):
        fixture = json.loads(AIO_WORKFLOW_0_5_2_FIXTURE_PATH.read_text(encoding="utf-8"))
        source = fixture["source"]
        serialized = fixture["serialized_generation_settings"]
        serialized_before = copy.deepcopy(serialized)
        capabilities = source["capabilities"]

        self.assertEqual(source["git_tag"], "v0.5.2")
        self.assertEqual(source["package_version"], "0.5.2")
        self.assertEqual(source["node_id"], 86)
        self.assertEqual(source["node_type"], "EasyUseAnimaAIOGenerator")
        self.assertEqual(source["widget_index"], 0)

        with _deterministic_capabilities(
            samplers=tuple(capabilities["samplers"]),
            schedulers=tuple(capabilities["schedulers"]),
            impact_schedulers=tuple(capabilities["impact_schedulers"]),
        ):
            with patch_comfy_helper(
                nodes,
                "_comfy_max_resolution",
                return_value=capabilities["max_resolution"],
            ):
                normalized = nodes._normalize_aio_generation_settings(serialized)

        self.assertEqual(serialized, serialized_before)
        self.assertEqual(normalized, fixture["expected_normalized_generation_settings"])

    def test_manifest_shape_covers_every_default_leaf_with_matching_types(self):
        manifest = _manifest()
        contracts = dict(_leaf_contracts(manifest, manifest["shape"]))
        defaults = dict(_default_leaves(manifest["default"]))

        failures = _manifest_shape_default_failures(manifest)
        if failures:
            self.fail("\n".join(failures))
        self.assertEqual(set(contracts), set(defaults))
        for path, value in defaults.items():
            contract = contracts[path]
            field_type = contract["type"]
            with self.subTest(path="/" + "/".join(path), field_type=field_type):
                if field_type == "boolean":
                    self.assertIs(type(value), bool)
                elif field_type == "integer":
                    self.assertIs(type(value), int)
                elif field_type == "number":
                    self.assertIsInstance(value, (int, float))
                    self.assertIsNot(type(value), bool)
                elif field_type == "string":
                    self.assertIsInstance(value, str)
                elif field_type == "array":
                    self.assertIsInstance(value, list)
                elif field_type == "object":
                    self.assertIsInstance(value, dict)
                else:
                    self.fail(f"Unsupported manifest field type at {path}: {field_type}")

                if "const" in contract:
                    self.assertEqual(value, contract["const"])
                if "enum" in contract:
                    self.assertIn(value, contract["enum"])
                if "minimum" in contract:
                    self.assertGreaterEqual(value, contract["minimum"])
                if "maximum" in contract:
                    self.assertLessEqual(value, contract["maximum"])

    def test_static_enum_sets_and_members_match_backend_normalization(self):
        manifest = _manifest()
        defaults = manifest["default"]
        contracts = dict(_leaf_contracts(manifest, manifest["shape"]))
        enum_contracts = {
            path: contract
            for path, contract in contracts.items()
            if "enum" in contract
        }
        authoritative = _authoritative_static_enum_choices()

        self.assertEqual(set(enum_contracts), set(authoritative))
        for path, contract in enum_contracts.items():
            with self.subTest(path="/" + "/".join(path), rule="accepted-set"):
                self.assertEqual(tuple(contract["enum"]), authoritative[path])
                self.assertEqual(_runtime_static_enum_choices(path), authoritative[path])

        with _deterministic_capabilities():
            for path, contract in enum_contracts.items():
                default = _get_path(defaults, path)
                with self.subTest(path="/" + "/".join(path), rule="invalid"):
                    normalized = nodes._normalize_aio_generation_settings(
                        _payload_with(path, "__invalid_manifest_choice__")
                    )
                    self.assertEqual(_get_path(normalized, path), default)

                for member in contract["enum"]:
                    with self.subTest(path="/" + "/".join(path), rule="round-trip", member=member):
                        normalized = nodes._normalize_aio_generation_settings(
                            _payload_with(path, member)
                        )
                        self.assertEqual(_get_path(normalized, path), member)

    def test_static_bounds_match_backend_normalization(self):
        manifest = _manifest()
        contracts = dict(_leaf_contracts(manifest, manifest["shape"]))

        with _deterministic_capabilities():
            for path, contract in contracts.items():
                if "minimum" in contract:
                    with self.subTest(path="/" + "/".join(path), rule="minimum"):
                        minimum = contract["minimum"]
                        normalized = nodes._normalize_aio_generation_settings(
                            _payload_with(path, minimum - 1)
                        )
                        self.assertEqual(_get_path(normalized, path), minimum)

                if "maximum" in contract:
                    with self.subTest(path="/" + "/".join(path), rule="maximum"):
                        maximum = contract["maximum"]
                        normalized = nodes._normalize_aio_generation_settings(
                            _payload_with(path, maximum + 1)
                        )
                        self.assertEqual(_get_path(normalized, path), maximum)

    def test_coercion_profiles_match_current_backend_helpers(self):
        manifest = _manifest()
        coercions = manifest["coercions"]

        for value in coercions["backend_boolean"]["true_strings"]:
            with self.subTest(value=value):
                self.assertTrue(nodes._as_bool(value, False))
        for value in ("false", "0", "no", "off", "disabled", "unknown"):
            with self.subTest(value=value):
                self.assertFalse(nodes._as_bool(value, True))

        self.assertEqual(nodes._as_int("12", 7), 12)
        self.assertEqual(nodes._as_int("12.9", 7), 7)
        self.assertEqual(nodes._as_float("12.9", 7.0), 12.9)
        self.assertEqual(nodes._choice(" two ", ("one", "two"), "one"), "two")
        self.assertEqual(nodes._choice("missing", ("one", "two"), "one"), "one")
        self.assertEqual(coercions["choice"]["invalid"]["static_enum"], "default")
        self.assertEqual(coercions["backend_boolean"]["list_or_tuple"], "first-value")
        self.assertEqual(coercions["backend_boolean"]["empty_list_or_tuple"], "default")
        self.assertTrue(nodes._as_bool(["yes"], False))
        self.assertTrue(nodes._as_bool(("enabled",), False))
        self.assertFalse(nodes._as_bool(["off"], True))
        self.assertTrue(nodes._as_bool([], True))
        self.assertFalse(nodes._as_bool((), False))

    def test_field_specific_choice_coercions_match_current_backend(self):
        manifest = _manifest()
        contracts = dict(_leaf_contracts(manifest, manifest["shape"]))
        self.assertEqual(contracts[("mod_guidance", "profile")]["coercion"], "mod-guidance-profile")
        self.assertEqual(contracts[("upscale", "usdu", "prompt_mode")]["coercion"], "string-then-choice")
        self.assertEqual(contracts[("detailer", "face", "alignment")]["coercion"], "string-then-choice")

        cases = (
            (("mod_guidance", "profile"), "step_i14", "step_i14"),
            (("mod_guidance", "profile"), " step_i14 ", nodes.ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE),
            (("mod_guidance", "profile"), "STEP_I14", nodes.ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE),
            (("mod_guidance", "profile"), ["step_i14"], nodes.ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE),
            (("mod_guidance", "profile"), ("step_i14",), nodes.ANIMA_MOD_GUIDANCE_DEFAULT_PROFILE),
            (("upscale", "usdu", "prompt_mode"), " no_general ", "no_general"),
            (("upscale", "usdu", "prompt_mode"), "quality_tags_only", "no_general"),
            (("upscale", "usdu", "prompt_mode"), " quality_tags_only ", "full"),
            (("upscale", "usdu", "prompt_mode"), ["no_general"], "full"),
            (("upscale", "usdu", "prompt_mode"), ("no_general",), "full"),
            (("detailer", "face", "alignment"), " none ", "none"),
            (("detailer", "face", "alignment"), ["none"], "32"),
            (("detailer", "face", "alignment"), ("none",), "32"),
        )
        with _deterministic_capabilities():
            for path, value, expected in cases:
                with self.subTest(path="/" + "/".join(path), value=value):
                    normalized = nodes._normalize_aio_generation_settings(_payload_with(path, value))
                    self.assertEqual(_get_path(normalized, path), expected)

    def test_every_referenced_coercion_has_a_self_contained_definition(self):
        manifest = _manifest()
        defined = set(manifest["coercions"])
        referenced = set(_coercion_references({
            "shape": manifest["shape"],
            "definitions": manifest["definitions"],
            "coercions": manifest["coercions"],
        }))

        self.assertEqual(referenced - defined, set())
        self.assertTrue({
            "constant",
            "string-then-choice",
            "mod-guidance-profile",
            "string-or-default",
            "string",
            "string-list",
            "civitai-fetcher-list",
            "detailer-order",
            "json-object-or-empty",
            "surface-specific-seed",
        }.issubset(referenced))

    def test_container_item_contracts_match_current_backend_normalizers(self):
        manifest = _manifest()
        image_saver = manifest["shape"]["fields"]["save"]["fields"]["image_saver"]["fields"]

        for path, contract in _all_contract_nodes(manifest):
            if contract.get("type") == "array":
                with self.subTest(path="/".join(path), container="array"):
                    self.assertIsInstance(contract.get("items"), dict)
                    item_contract = _resolve_contract(manifest, contract["items"])
                    self.assertTrue(
                        any(name in item_contract for name in ("type", "one_of", "any_of")),
                        f"Missing item type contract at {'/'.join(path)}",
                    )
            if contract.get("type") == "object" and contract.get("open_content"):
                with self.subTest(path="/".join(path), container="open-object"):
                    self.assertIsInstance(contract.get("additional_properties"), dict)
                    _resolve_contract(manifest, contract["additional_properties"])

        fetcher_contract = _resolve_contract(manifest, image_saver["civitai_hash_fetchers"]["items"])
        self.assertEqual(
            set(fetcher_contract["fields"]),
            {"enabled", "username", "model_name", "version"},
        )
        self.assertEqual(fetcher_contract["unknown_fields"], "discard")
        self.assertEqual(
            set(fetcher_contract["required"]),
            {"enabled", "username", "model_name", "version"},
        )

        normalized = nodes._normalize_aio_generation_settings({
            "save": {
                "image_saver": {
                    "additional_hash_bundles": '[" alpha, ", null, " beta "]',
                    "civitai_hash_fetchers": json.dumps([
                        {
                            "enabled": "off",
                            "username": " user ",
                            "model_name": " model ",
                            "version": " v1 ",
                            "future": "discarded",
                        },
                        {"enabled": True, "username": " ", "model_name": "", "version": ""},
                        "not-an-object",
                    ]),
                }
            }
        })
        self.assertEqual(
            normalized["save"]["image_saver"]["additional_hash_bundles"],
            ["alpha", "beta"],
        )
        self.assertEqual(
            normalized["save"]["image_saver"]["civitai_hash_fetchers"],
            [{"enabled": False, "username": "user", "model_name": "model", "version": "v1"}],
        )
        self.assertEqual(nodes._normalize_aio_hash_bundles(" raw, "), ["raw"])
        self.assertEqual(nodes._normalize_aio_hash_bundles('"json-string"'), [])
        self.assertEqual(nodes._normalize_aio_civitai_hash_fetchers("not-json"), [])
        self.assertEqual(
            nodes._aio_detailer_target_order({
                "order": [" custom_2 ", "face", "custom_2", "invalid"],
                "custom_3": {},
                "custom_4": "not-an-object",
            }),
            ["custom_2", "face", "custom_3", "eye"],
        )

    def test_refs_and_detailer_pattern_fields_cover_non_default_targets(self):
        manifest = _manifest()
        for path, contract in _all_contract_nodes(manifest):
            if "$ref" in contract:
                with self.subTest(path="/".join(path), reference=contract["$ref"]):
                    resolved = _resolve_contract(manifest, contract)
                    self.assertTrue(any(name in resolved for name in ("type", "one_of", "any_of")))

        detailer_contract = manifest["shape"]["fields"]["detailer"]
        pattern_fields = detailer_contract["pattern_fields"]
        self.assertEqual(set(pattern_fields), {"^custom_[0-9]+$"})
        pattern = next(iter(pattern_fields))
        self.assertIsNotNone(re.fullmatch(pattern, "custom_7"))
        self.assertIsNone(re.fullmatch(pattern, "custom_name"))
        self.assertIs(
            _resolve_contract(manifest, pattern_fields[pattern]),
            manifest["definitions"]["detailer_target"],
        )

        with _deterministic_capabilities():
            normalized = nodes._normalize_aio_generation_settings({
                "detailer": {
                    "order": ["custom_7"],
                    "custom_7": {
                        "label": "",
                        "detect_count": 0,
                        "threshold": -1,
                        "sampler_name": "invalid",
                        "scheduler": "invalid",
                        "future_target_key": {"kept": True},
                    },
                }
            })
        target = normalized["detailer"]["custom_7"]
        self.assertEqual(target["label"], "Detailer Block 7")
        self.assertEqual(target["detect_count"], 1)
        self.assertEqual(target["threshold"], 0.0)
        self.assertEqual(target["sampler_name"], "euler")
        self.assertEqual(target["scheduler"], "sgm_uniform")
        self.assertEqual(target["future_target_key"], {"kept": True})

    def test_dynamic_choice_fallback_policy_matches_runtime_capabilities(self):
        manifest = _manifest()
        dynamic_contracts = [
            (path, contract)
            for path, contract in _leaf_contracts(manifest, manifest["shape"])
            if "dynamic_enum" in contract
        ]
        dynamic_policy = manifest["coercions"]["choice"]["invalid"]["dynamic_enum"]
        self.assertEqual(dynamic_policy, {
            "policy": "default-if-present-else-first",
            "preferred_default_present": "default",
            "preferred_default_absent": "first-capability",
            "empty_capabilities": "default",
        })

        defaults = manifest["default"]
        with _deterministic_capabilities():
            for path, contract in dynamic_contracts:
                with self.subTest(path="/" + "/".join(path), default_present=True):
                    normalized = nodes._normalize_aio_generation_settings(
                        _payload_with(path, "__invalid_dynamic_choice__")
                    )
                    self.assertEqual(_get_path(normalized, path), _get_path(defaults, path))

        first_by_source = {
            "comfy.samplers": "cap-sampler-first",
            "comfy.schedulers": "cap-scheduler-first",
            "impact.schedulers": "cap-impact-first",
        }
        with _deterministic_capabilities(
            samplers=("cap-sampler-first", "cap-sampler-second"),
            schedulers=("cap-scheduler-first", "cap-scheduler-second"),
            impact_schedulers=("cap-impact-first", "cap-impact-second"),
        ):
            for path, contract in dynamic_contracts:
                with self.subTest(path="/" + "/".join(path), default_present=False):
                    normalized = nodes._normalize_aio_generation_settings(
                        _payload_with(path, "__invalid_dynamic_choice__")
                    )
                    self.assertEqual(
                        _get_path(normalized, path),
                        first_by_source[contract["dynamic_enum"]],
                    )

        self.assertEqual(nodes._choice("missing", (), "preferred"), "preferred")

    def test_alias_unknown_field_and_surface_drift_policies_match_current_code(self):
        manifest = _manifest()
        policies = manifest["policies"]
        normalized = nodes._normalize_aio_generation_settings({
            "sampler": {"dave": {"enabled": True}, "future_sampler": "kept"},
            "model_patches": {"aura_flow": {"enabled": True}},
            "highres": {"backend": "future_backend"},
            "upscale": {
                "fit": {
                    "enabled": True,
                    "mode": "megapixels",
                    "max_megapixels": 9,
                },
                "usdu": {"prompt_mode": "quality_tags_only"},
            },
            "save": {
                "filename_prefix": "legacy/prefix",
                "image_saver": {"show_preview": True},
            },
            "future_section": {"value": 42},
        })

        self.assertNotIn("dave", normalized["sampler"])
        self.assertNotIn("enabled", normalized["model_patches"]["aura_flow"])
        self.assertNotIn("fit", normalized["upscale"])
        self.assertEqual(normalized["upscale"]["usdu"]["prompt_mode"], "no_general")
        self.assertTrue(normalized["postprocess"]["enabled"])
        self.assertEqual(normalized["postprocess"]["fit"]["mode"], "megapixels")
        self.assertEqual(normalized["postprocess"]["fit"]["max_megapixels"], 9.0)
        self.assertNotIn("filename_prefix", normalized["save"])
        self.assertNotIn("show_preview", normalized["save"]["image_saver"])
        self.assertEqual(normalized["future_section"], {"value": 42})
        self.assertEqual(normalized["sampler"]["future_sampler"], "kept")
        self.assertEqual(normalized["highres"]["backend"], "future_backend")

        backend_policy = policies["unknown_fields"]["backend"]
        visible_policy = policies["unknown_fields"]["frontend_visible_merge"]
        self.assertEqual(backend_policy["mode"], "preserve-recursively")
        self.assertNotIn("/highres/backend", backend_policy["removed_known_legacy_paths"])
        self.assertIn("/highres/backend", visible_policy["removed_paths"])
        self.assertFalse(policies["persistence"]["write_on_read"])
        self.assertEqual(
            policies["version_migrations"],
            [
                {
                    "from": 1,
                    "to": 2,
                    "owner": "easyuse_anima.aio.generation_migrations",
                    "mode": "pure-in-memory",
                    "missing_dave_stage_scope": "legacy-all-sampling-stages",
                },
                {
                    "from": 2,
                    "to": 3,
                    "owner": "easyuse_anima.aio.generation_migrations",
                    "mode": "pure-in-memory",
                    "missing_safe_pag_stage_scope": "legacy-all-sampling-stages",
                },
            ],
        )

    def test_schema_version_dynamic_owners_and_seed_surface_bounds_do_not_drift(self):
        manifest = _manifest()
        shape_fields = manifest["shape"]["fields"]
        capabilities = manifest["policies"]["dynamic_capabilities"]
        patch_contract = manifest["policies"]["model_patch_contract"]
        seed_contract = shape_fields["sampler"]["fields"]["seed"]
        frontend_source = FRONTEND_SETTINGS_PATH.read_text(encoding="utf-8")
        frontend_seed_match = re.search(
            r"export const AIO_GENERATOR_MAX_SEED = (?P<value>\d+);",
            frontend_source,
        )

        self.assertEqual(shape_fields["schema"]["const"], nodes.AIO_GENERATION_SETTINGS_SCHEMA)
        self.assertEqual(shape_fields["version"]["current"], nodes.AIO_GENERATION_SETTINGS_VERSION)
        self.assertEqual(
            tuple(patch_contract["sampling_stage_ids"]),
            AIO_GENERATION_STAGE_IDS,
        )
        self.assertEqual(
            patch_contract["patch_order_revision"],
            AIO_MODEL_PATCH_ORDER_REVISION,
        )
        self.assertEqual(
            tuple(tuple(edge) for edge in patch_contract["precedence_edges"]),
            AIO_MODEL_PATCH_PRECEDENCE,
        )
        self.assertEqual(patch_contract["dave_fresh_default"], "first-pass-only")
        self.assertEqual(patch_contract["safe_pag_fresh_default"], "first-pass-only")
        self.assertEqual(
            patch_contract["execution_cutover"],
            "complete-through-AIO-SAFEPAG-03",
        )
        self.assertEqual(
            patch_contract["stage_scope_policy"],
            {
                "generic_scope_ui": False,
                "owners": {
                    "dave": {
                        "decision": "supported",
                        "stages": [
                            "first_pass",
                            "highres",
                            "detailer",
                            "upscale",
                        ],
                    },
                    "safe_pag": {
                        "decision": "supported",
                        "stages": [
                            "first_pass",
                            "highres",
                            "detailer",
                            "upscale",
                        ],
                    },
                    "kj.fp16_accumulation": {
                        "decision": "run-global-not-stage-scoped",
                        "reason": "process-global-torch-setting-callback",
                    },
                    "kj.sage_attention": {
                        "decision": "follow-up-required",
                        "reason": "experimental-clone-local-override",
                    },
                    "kj.torch_compile": {
                        "decision": "run-global-not-stage-scoped",
                        "reason": (
                            "shared-base-model-compile-registry-and-dynamo-config"
                        ),
                    },
                },
            },
        )
        self.assertFalse(capabilities["owned_by_manifest"])
        self.assertEqual(
            set(capabilities["sources"]),
            {"comfy.samplers", "comfy.schedulers", "impact.schedulers", "comfy.max_resolution"},
        )
        self.assertEqual(seed_contract["maximum_by_surface"]["backend"], str(nodes.MAX_SEED))
        self.assertIsNotNone(frontend_seed_match)
        self.assertEqual(
            seed_contract["maximum_by_surface"]["frontend"],
            int(frontend_seed_match.group("value")),
        )

    def test_manifest_is_tracked_registry_included_and_present_in_head_archive(self):
        tracked = _git("ls-files", "--error-unmatch", "--", MANIFEST_REPOSITORY_PATH)
        self.assertEqual(tracked.stdout.strip(), MANIFEST_REPOSITORY_PATH)

        ignored = _git(
            "ls-files",
            "-ci",
            "--exclude-from=.comfyignore",
            "--",
            MANIFEST_REPOSITORY_PATH,
        )
        self.assertEqual(ignored.stdout.strip(), "")

        archive = _git(
            "archive",
            "--format=tar",
            "HEAD",
            "--",
            MANIFEST_REPOSITORY_PATH,
            binary=True,
        )
        with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
            self.assertIn(MANIFEST_REPOSITORY_PATH, tar.getnames())


if __name__ == "__main__":
    unittest.main()
