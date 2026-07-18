from __future__ import annotations

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


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "easyuse_anima" / "aio" / "schemas" / "generation_settings.v1.json"
MANIFEST_REPOSITORY_PATH = MANIFEST_PATH.relative_to(ROOT).as_posix()
FRONTEND_SETTINGS_PATH = ROOT / "web" / "js" / "aio" / "settings.js"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


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
    with patch.multiple(
        nodes,
        _comfy_sampler_names=lambda: list(samplers),
        _comfy_scheduler_names=lambda: list(schedulers),
        _impact_scheduler_names=lambda: list(impact_schedulers),
        _comfy_max_resolution=lambda: 16384,
    ):
        yield


class AIOGenerationSettingsManifestTests(unittest.TestCase):
    def test_manifest_default_matches_python_runtime_default(self):
        manifest = _manifest()

        self.assertEqual(manifest["settings"]["schema"], nodes.AIO_GENERATION_SETTINGS_SCHEMA)
        self.assertEqual(manifest["settings"]["version"], nodes.AIO_GENERATION_SETTINGS_VERSION)
        self.assertEqual(manifest["default"], nodes.AIO_GENERATION_DEFAULT_SETTINGS)

    def test_manifest_shape_covers_every_default_leaf_with_matching_types(self):
        manifest = _manifest()
        contracts = dict(_leaf_contracts(manifest, manifest["shape"]))
        defaults = dict(_default_leaves(manifest["default"]))

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

    def test_static_enum_and_bounds_match_backend_normalization(self):
        manifest = _manifest()
        defaults = manifest["default"]
        contracts = dict(_leaf_contracts(manifest, manifest["shape"]))

        with _deterministic_capabilities():
            for path, contract in contracts.items():
                default = _get_path(defaults, path)
                if "enum" in contract:
                    with self.subTest(path="/" + "/".join(path), rule="enum"):
                        normalized = nodes._normalize_aio_generation_settings(
                            _payload_with(path, "__invalid_manifest_choice__")
                        )
                        self.assertEqual(_get_path(normalized, path), default)

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
        self.assertEqual(policies["version_migrations"], [])

    def test_schema_version_dynamic_owners_and_seed_surface_bounds_do_not_drift(self):
        manifest = _manifest()
        shape_fields = manifest["shape"]["fields"]
        capabilities = manifest["policies"]["dynamic_capabilities"]
        seed_contract = shape_fields["sampler"]["fields"]["seed"]
        frontend_source = FRONTEND_SETTINGS_PATH.read_text(encoding="utf-8")
        frontend_seed_match = re.search(
            r"export const AIO_GENERATOR_MAX_SEED = (?P<value>\d+);",
            frontend_source,
        )

        self.assertEqual(shape_fields["schema"]["const"], nodes.AIO_GENERATION_SETTINGS_SCHEMA)
        self.assertEqual(shape_fields["version"]["current"], nodes.AIO_GENERATION_SETTINGS_VERSION)
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
