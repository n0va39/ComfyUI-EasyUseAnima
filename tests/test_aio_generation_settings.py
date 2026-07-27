from __future__ import annotations

import copy
import json
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import nodes
from easyuse_anima.aio import generation_defaults, generation_normalization
from easyuse_anima.aio.generation_detailer import AIOGenerationDetailerTargetConfig
from easyuse_anima.aio.generation_features import (
    AIOGenerationHighresConfig,
    AIOGenerationModelPatchesConfig,
    AIOGenerationUpscaleConfig,
)
from easyuse_anima.aio.generation_output import AIOGenerationImageSaverConfig
from easyuse_anima.aio.generation_sampling import AIOGenerationSpectrumConfig
from easyuse_anima.aio.generation_settings import (
    AIOGenerationConfig,
    _aio_generation_config_from_dict,
    _aio_generation_config_to_dict,
)
from tests.comfy_host_fakes import patch_comfy_helper

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "aio_generation_settings_0_5_2.json"


@contextmanager
def _deterministic_capabilities(
    *,
    samplers=("er_sde", "euler"),
    schedulers=("simple",),
    impact_schedulers=("sgm_uniform",),
    max_resolution=16384,
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
            return_value=max_resolution,
        ),
    ):
        yield


class AIOGenerationConfigTests(unittest.TestCase):
    def test_root_facade_reexports_canonical_normalizers_by_identity(self):
        self.assertIs(
            nodes.AIO_GENERATION_DEFAULT_SETTINGS,
            generation_defaults.AIO_GENERATION_DEFAULT_SETTINGS,
        )
        self.assertIs(
            nodes._merge_versioned_settings,
            generation_normalization._merge_versioned_settings,
        )
        self.assertIs(
            nodes._normalize_aio_generation_settings,
            generation_normalization._normalize_aio_generation_settings,
        )

    def test_canonical_normalizer_uses_canonical_helpers_at_call_time(self):
        original_choice = generation_normalization._choice
        calls: list[tuple[object, tuple[object, ...], object]] = []

        def tracking_choice(value, options, default):
            calls.append((value, tuple(options), default))
            return original_choice(value, options, default)

        with (
            patch.object(generation_normalization, "_choice", tracking_choice),
            _deterministic_capabilities(),
        ):
            normalized = generation_normalization._normalize_aio_generation_settings(
                {"mode": "img2img"}
            )

        self.assertEqual(normalized["mode"], "img2img")
        self.assertIn(
            ("img2img", ("txt2img", "img2img", "inpaint"), "txt2img"),
            calls,
        )

    def test_default_payload_round_trips_with_exact_shape_and_order(self):
        source = copy.deepcopy(nodes.AIO_GENERATION_DEFAULT_SETTINGS)

        config = _aio_generation_config_from_dict(source)
        restored = _aio_generation_config_to_dict(config)

        self.assertIsInstance(config, AIOGenerationConfig)
        self.assertIsInstance(config.sampler.spectrum, AIOGenerationSpectrumConfig)
        self.assertIsInstance(config.model_patches, AIOGenerationModelPatchesConfig)
        self.assertIsInstance(config.highres, AIOGenerationHighresConfig)
        self.assertIsInstance(config.upscale, AIOGenerationUpscaleConfig)
        self.assertIsInstance(config.detailer.targets[0].settings, AIOGenerationDetailerTargetConfig)
        self.assertIsInstance(config.save.image_saver, AIOGenerationImageSaverConfig)
        self.assertEqual(restored, source)
        self.assertEqual(list(restored), list(source))
        self.assertEqual(list(restored["sampler"]), list(source["sampler"]))
        self.assertEqual(list(restored["detailer"]), list(source["detailer"]))
        self.assertEqual(
            json.dumps(restored, ensure_ascii=False, separators=(",", ":")),
            json.dumps(source, ensure_ascii=False, separators=(",", ":")),
        )

    def test_negpip_turbo_round_trips_unknown_fields_and_owns_effective_cfg_only(self):
        with _deterministic_capabilities():
            normalized = nodes._normalize_aio_generation_settings({
                "negpip": {
                    "mode": "turbo",
                    "future_negpip": {"revision": 3},
                },
            })
        config = _aio_generation_config_from_dict(normalized)

        self.assertEqual(config.negpip.mode, "turbo")
        self.assertTrue(config.negpip.is_turbo)
        self.assertEqual(config.negpip.effective_cfg(7.5), 1.0)
        self.assertEqual(
            _aio_generation_config_to_dict(config)["negpip"],
            {
                "mode": "turbo",
                "future_negpip": {"revision": 3},
            },
        )

        with _deterministic_capabilities():
            invalid = nodes._normalize_aio_generation_settings({
                "negpip": {"mode": "unsupported"},
            })
        self.assertEqual(invalid["negpip"], {"mode": "off"})

    def test_fresh_v4_legacy_scopes_and_malformed_scopes_normalize_without_ambiguity(self):
        legacy = copy.deepcopy(nodes.AIO_GENERATION_DEFAULT_SETTINGS)
        legacy["version"] = 1
        legacy_dave = legacy["model_patches"]["dave"]
        del legacy_dave["stage_scope"]
        legacy_safe_pag = legacy["model_patches"]["safe_pag"]
        del legacy_safe_pag["stage_scope"]
        legacy_kj = legacy["model_patches"]["kj"]
        del legacy_kj["sage_stage_scope"]
        malformed = copy.deepcopy(nodes.AIO_GENERATION_DEFAULT_SETTINGS)
        malformed["model_patches"]["safe_pag"]["stage_scope"] = "all"
        malformed["model_patches"]["kj"]["sage_stage_scope"] = "all"

        with _deterministic_capabilities():
            fresh = nodes._normalize_aio_generation_settings({})
            migrated = nodes._normalize_aio_generation_settings(legacy)
            malformed_normalized = nodes._normalize_aio_generation_settings(malformed)

        self.assertEqual(fresh["version"], 4)
        self.assertEqual(
            fresh["model_patches"]["dave"]["stage_scope"],
            {
                "first_pass": True,
                "highres": False,
                "detailer": False,
                "upscale": False,
            },
        )
        self.assertEqual(
            fresh["model_patches"]["safe_pag"]["stage_scope"],
            {
                "first_pass": True,
                "highres": False,
                "detailer": False,
                "upscale": False,
            },
        )
        self.assertEqual(
            fresh["model_patches"]["kj"]["sage_stage_scope"],
            {
                "first_pass": True,
                "highres": False,
                "detailer": False,
                "upscale": False,
            },
        )
        self.assertEqual(migrated["version"], 4)
        self.assertEqual(
            migrated["model_patches"]["dave"]["stage_scope"],
            {
                "first_pass": True,
                "highres": True,
                "detailer": True,
                "upscale": True,
            },
        )
        self.assertEqual(
            migrated["model_patches"]["safe_pag"]["stage_scope"],
            {
                "first_pass": True,
                "highres": True,
                "detailer": True,
                "upscale": True,
            },
        )
        self.assertEqual(
            migrated["model_patches"]["kj"]["sage_stage_scope"],
            {
                "first_pass": True,
                "highres": True,
                "detailer": True,
                "upscale": True,
            },
        )
        self.assertEqual(
            malformed_normalized["model_patches"]["safe_pag"]["stage_scope"],
            {
                "first_pass": False,
                "highres": False,
                "detailer": False,
                "upscale": False,
            },
        )
        self.assertEqual(
            malformed_normalized["model_patches"]["kj"]["sage_stage_scope"],
            {
                "first_pass": False,
                "highres": False,
                "detailer": False,
                "upscale": False,
            },
        )

    def test_0_5_2_expected_normalized_payload_round_trips(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        expected = fixture["expected_normalized_generation_settings"]

        restored = _aio_generation_config_to_dict(
            _aio_generation_config_from_dict(expected)
        )

        self.assertEqual(restored, expected)

    def test_root_nested_unknown_and_extension_objects_are_isolated(self):
        source = copy.deepcopy(nodes.AIO_GENERATION_DEFAULT_SETTINGS)
        source["root_extension"] = {"rows": [{"name": "root", "values": [1, 2]}]}
        source["sampler"]["sampler_extension"] = {"nested": {"enabled": True}}
        source["model_patches"]["future_patch"] = {"weights": [0.25, 0.75]}
        source["detailer"]["future_metadata"] = {"label": "preserve me"}
        source["sampler"]["spectrum_extra"] = {
            "future_spectrum": {"curve": [1, 3, 5]}
        }
        source["sampler"]["spd_extra"] = {"future_spd": {"gain": 0.625}}
        expected = copy.deepcopy(source)

        config = _aio_generation_config_from_dict(source)
        source["root_extension"]["rows"][0]["name"] = "caller mutated"
        source["sampler"]["spectrum_extra"]["future_spectrum"]["curve"].append(7)

        first = _aio_generation_config_to_dict(config)
        self.assertEqual(first, expected)
        first["model_patches"]["future_patch"]["weights"][0] = 999
        first["sampler"]["spd_extra"]["future_spd"]["gain"] = 999

        self.assertEqual(_aio_generation_config_to_dict(config), expected)

    def test_every_typed_object_section_preserves_unknown_json(self):
        source = copy.deepcopy(nodes.AIO_GENERATION_DEFAULT_SETTINGS)
        section_paths = (
            ("sampler", "spectrum"),
            ("sampler", "spd"),
            ("sampler", "dit_corrections"),
            ("model_patches",),
            ("model_patches", "aura_flow"),
            ("model_patches", "dave"),
            ("model_patches", "safe_pag"),
            ("model_patches", "kj"),
            ("model_patches", "kj", "torch_compile"),
            ("mod_guidance",),
            ("mod_guidance", "advanced"),
            ("artist_mix",),
            ("highres",),
            ("highres", "spectrum"),
            ("highres", "dit_corrections"),
            ("upscale",),
            ("upscale", "spectrum"),
            ("upscale", "dit_corrections"),
            ("upscale", "usdu"),
            ("upscale", "resshift"),
            ("postprocess",),
            ("postprocess", "fit"),
            ("detailer", "sam3"),
            ("detailer", "face"),
            ("detailer", "face", "spectrum"),
            ("detailer", "face", "dit_corrections"),
            ("save",),
            ("save", "image_saver"),
            ("preview",),
        )
        for index, path in enumerate(section_paths):
            section = source
            for name in path:
                section = section[name]
            section[f"unknown_{index}"] = {"path": list(path), "value": index + 0.5}

        restored = _aio_generation_config_to_dict(
            _aio_generation_config_from_dict(source)
        )

        self.assertEqual(restored, source)

    def test_custom_detailer_targets_and_order_round_trip(self):
        source = copy.deepcopy(nodes.AIO_GENERATION_DEFAULT_SETTINGS)
        custom_target = copy.deepcopy(source["detailer"]["face"])
        custom_target["label"] = "Custom Detailer 12"
        custom_target["target_extension"] = {"tokens": ["a", "b"]}
        source["detailer"]["custom_12"] = custom_target
        source["detailer"]["order"] = ["custom_12", "eye", "face"]

        config = _aio_generation_config_from_dict(source)
        restored = _aio_generation_config_to_dict(config)

        self.assertEqual(config.detailer.order, ("custom_12", "eye", "face"))
        self.assertEqual(
            tuple(target.name for target in config.detailer.targets),
            ("face", "eye", "custom_12"),
        )
        self.assertEqual(restored, source)

    def test_non_object_custom_detailer_value_remains_an_extension(self):
        source = {"detailer": {"custom_9": "preserve non-object"}}

        with _deterministic_capabilities():
            normalized = nodes._normalize_aio_generation_settings(source)

        config = _aio_generation_config_from_dict(normalized)
        restored = _aio_generation_config_to_dict(config)

        self.assertEqual(normalized["detailer"]["custom_9"], "preserve non-object")
        self.assertNotIn("custom_9", normalized["detailer"]["order"])
        self.assertNotIn("custom_9", tuple(target.name for target in config.detailer.targets))
        self.assertEqual(restored, normalized)

    def test_non_decimal_custom_detailer_name_remains_an_object_extension(self):
        source = {"detailer": {"custom_²": {"future": {"value": 7}}}}

        with _deterministic_capabilities():
            normalized = nodes._normalize_aio_generation_settings(source)

        config = _aio_generation_config_from_dict(normalized)
        restored = _aio_generation_config_to_dict(config)

        self.assertEqual(normalized["detailer"]["custom_²"], {"future": {"value": 7}})
        self.assertNotIn("custom_²", normalized["detailer"]["order"])
        self.assertNotIn("custom_²", tuple(target.name for target in config.detailer.targets))
        self.assertEqual(restored, normalized)

    def test_facade_keeps_legacy_removal_and_returns_isolated_mutable_dict(self):
        legacy = {
            "sampler": {"dave": {"enabled": True}},
            "model_patches": {"aura_flow": {"enabled": True}},
            "upscale": {
                "fit": {
                    "enabled": True,
                    "mode": "max_megapixels",
                    "max_megapixels": 8.0,
                }
            },
            "save": {
                "filename_prefix": "legacy/path",
                "image_saver": {"show_preview": False},
            },
        }

        with _deterministic_capabilities():
            first = nodes._normalize_aio_generation_settings(legacy)
            second = nodes._normalize_aio_generation_settings(legacy)

        self.assertNotIn("dave", first["sampler"])
        self.assertNotIn("enabled", first["model_patches"]["aura_flow"])
        self.assertNotIn("fit", first["upscale"])
        self.assertNotIn("filename_prefix", first["save"])
        self.assertNotIn("show_preview", first["save"]["image_saver"])
        self.assertTrue(first["postprocess"]["enabled"])

        first["sampler"]["spectrum"]["window_size"] = 999
        first["detailer"]["order"].append("custom_99")
        self.assertEqual(second["sampler"]["spectrum"]["window_size"], 2.0)
        self.assertEqual(second["detailer"]["order"], ["face", "eye"])

    def test_facade_preserves_0_5_2_parity_through_typed_boundary(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        source = fixture["source"]
        serialized = fixture["serialized_generation_settings"]
        serialized_before = copy.deepcopy(serialized)
        capabilities = source["capabilities"]

        with _deterministic_capabilities(
            samplers=tuple(capabilities["samplers"]),
            schedulers=tuple(capabilities["schedulers"]),
            impact_schedulers=tuple(capabilities["impact_schedulers"]),
            max_resolution=capabilities["max_resolution"],
        ):
            normalized = nodes._normalize_aio_generation_settings(serialized)

        self.assertEqual(serialized, serialized_before)
        self.assertEqual(normalized, fixture["expected_normalized_generation_settings"])


if __name__ == "__main__":
    unittest.main()
