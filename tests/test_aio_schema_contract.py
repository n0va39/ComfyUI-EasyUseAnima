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
def _deterministic_capabilities():
    with patch.multiple(
        nodes,
        _comfy_sampler_names=lambda: ["er_sde", "euler"],
        _comfy_scheduler_names=lambda: ["simple"],
        _impact_scheduler_names=lambda: ["sgm_uniform"],
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

                if "dynamic_enum" in contract:
                    with self.subTest(path="/" + "/".join(path), rule="dynamic-enum"):
                        normalized = nodes._normalize_aio_generation_settings(
                            _payload_with(path, "__invalid_dynamic_choice__")
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
