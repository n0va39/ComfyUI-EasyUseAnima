from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from easyuse_anima.aio import sampling
from tests.comfy_host_fakes import patch_comfy_helper


class AIOSamplingMoveTests(unittest.TestCase):
    def test_backend_dispatch_uses_selected_canonical_helper_at_call_time(self):
        settings = {
            "seed": 1,
            "steps": 2,
            "cfg": 3.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 0.5,
        }
        cases = (
            (
                "spectrum_mod_guidance_advanced",
                "_sample_latent_with_spectrum_mod_guidance_advanced",
            ),
            ("spectrum_spd_speed", "_sample_latent_with_spectrum_spd"),
            ("unknown_backend", "_sample_latent_with_comfy"),
        )
        for backend, helper_name in cases:
            with self.subTest(backend=backend):
                replacement = Mock(return_value=f"{backend}-latent")
                with patch.object(sampling, helper_name, replacement):
                    result = sampling._sample_latent_with_aio_backend(
                        "model",
                        "clip",
                        "positive",
                        "negative",
                        "latent",
                        {**settings, "backend": backend},
                        {"profile": "off"},
                        False,
                        "quality",
                        "quality-neg",
                    )
                self.assertEqual(result, f"{backend}-latent")
                replacement.assert_called_once()

    def test_comfy_latent_sampler_and_vae_calls_preserve_arguments_and_shapes(self):
        calls: list[tuple[object, ...]] = []

        class EmptyLatentImage:
            def generate(self, *args):
                calls.append(("empty", *args))
                return ("empty-latent", "ignored")

        class KSampler:
            def sample(self, *args):
                calls.append(("sample", *args))
                return {"result": ("sampled-latent",)}

        class VAEDecode:
            def decode(self, *args):
                calls.append(("decode", *args))
                return ("image",)

        class VAEEncode:
            def encode(self, *args):
                calls.append(("encode", *args))
                return ("encoded-latent",)

        classes = {
            "EmptyLatentImage": EmptyLatentImage,
            "KSampler": KSampler,
            "VAEDecode": VAEDecode,
            "VAEEncode": VAEEncode,
        }
        with (
            patch_comfy_helper(
                sampling,
                "_find_comfy_node_class",
                side_effect=classes.get,
            ),
            patch.object(sampling, "_resolve_aio_runtime_seed", return_value=987),
        ):
            empty = sampling._generate_empty_latent_with_comfy(8, 20)
            sampled = sampling._sample_latent_with_comfy(
                "model", 123, 0, "4.5", "euler", "normal", "pos", "neg", empty, "0.75"
            )
            decoded = sampling._decode_latent_with_comfy("vae", sampled)
            encoded = sampling._encode_image_with_comfy_vae("vae", decoded)

        self.assertEqual(
            (empty, sampled, decoded, encoded),
            ("empty-latent", "sampled-latent", "image", "encoded-latent"),
        )
        self.assertEqual(calls[0], ("empty", 16, 20, 1))
        self.assertEqual(
            calls[1],
            (
                "sample",
                "model",
                987,
                1,
                4.5,
                "euler",
                "normal",
                "pos",
                "neg",
                "empty-latent",
                0.75,
            ),
        )
        self.assertEqual(calls[2], ("decode", "vae", "sampled-latent"))
        self.assertEqual(calls[3], ("encode", "vae", "image"))

    def test_comfy_missing_api_and_no_output_errors_are_unchanged(self):
        class MissingAPI:
            pass

        with patch_comfy_helper(
            sampling,
            "_find_comfy_node_class",
            return_value=None,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "Could not find ComfyUI KSampler"
            ):
                sampling._sample_latent_with_comfy(
                    None, 0, 1, 1.0, "euler", "normal", None, None, None, 1.0
                )
        with patch_comfy_helper(
            sampling,
            "_find_comfy_node_class",
            return_value=MissingAPI,
        ):
            with self.assertRaisesRegex(
                RuntimeError, r"VAEEncode does not expose encode\(\)"
            ):
                sampling._encode_image_with_comfy_vae(None, None)

        class EmptyLatentImage:
            def generate(self, *_args):
                return ()

        with patch_comfy_helper(
            sampling,
            "_find_comfy_node_class",
            return_value=EmptyLatentImage,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "EmptyLatentImage returned no LATENT"
            ):
                sampling._generate_empty_latent_with_comfy(512, 512)

    def test_advanced_sampler_preserves_gating_defaults_filtering_and_extra_precedence(
        self,
    ):
        captured: dict[str, object] = {}

        class SpectrumKSamplerAdvanced:
            def sample(self, **kwargs):
                captured.update(kwargs)
                return ("advanced-latent",)

        settings = {
            "seed": "41",
            "steps": "31",
            "cfg": "6.5",
            "sampler_name": "dpmpp_2m",
            "scheduler": "beta",
            "denoise": "0.8",
            "spectrum": {"window_size": "3.0"},
            "dit_corrections": {
                "enabled": True,
                "smc_cfg": True,
                "smc_cfg_lambda": "7.0",
            },
            "spectrum_extra": {"quality_tags": "must-not-win", "custom": 9},
        }
        with (
            patch_comfy_helper(
                sampling,
                "_require_custom_node_class",
                return_value=SpectrumKSamplerAdvanced,
            ),
            patch.object(sampling, "_resolve_aio_runtime_seed", return_value=4242),
        ):
            result = sampling._sample_latent_with_spectrum_mod_guidance_advanced(
                "model",
                "clip",
                settings,
                {
                    "profile": "off",
                    "advanced": {"mod_w": 4, "quality_tags": "fallback"},
                },
                True,
                "pos",
                "neg",
                "latent",
                "quality",
                "quality-neg",
            )

        self.assertEqual(result, "advanced-latent")
        self.assertEqual(captured["seed"], 4242)
        self.assertEqual(captured["mod_w"], 0.0)
        self.assertEqual(captured["quality_tags"], "quality")
        self.assertEqual(captured["smc_cfg_lambda"], 7.0)
        self.assertEqual(captured["custom"], 9)
        self.assertEqual(captured["window_size"], 3.0)

    def test_spd_sampler_forces_euler_and_preserves_defaults_and_extra_precedence(self):
        captured: dict[str, object] = {}

        class SpectrumSPDKSampler:
            def sample(self, **kwargs):
                captured.update(kwargs)
                return {"result": ("spd-latent",)}

        with (
            patch_comfy_helper(
                sampling,
                "_require_custom_node_class",
                return_value=SpectrumSPDKSampler,
            ),
            patch.object(sampling, "_resolve_aio_runtime_seed", return_value=55),
        ):
            result = sampling._sample_latent_with_spectrum_spd(
                "model",
                {
                    "seed": 1,
                    "steps": 20,
                    "cfg": 5,
                    "sampler_name": "dpmpp_2m",
                    "spd": {"scale": 0.6},
                    "spd_extra": {"sampler_name": "must-not-win", "custom": "ok"},
                },
                "pos",
                "neg",
                "latent",
            )

        self.assertEqual(result, "spd-latent")
        self.assertEqual(captured["seed"], 55)
        self.assertEqual(captured["sampler_name"], "euler")
        self.assertEqual(captured["scheduler"], "simple")
        self.assertEqual(captured["denoise"], 1.0)
        self.assertEqual(captured["custom"], "ok")

    def test_stage_settings_preserve_seed_identity_clones_and_spd_fallback(self):
        base = {
            "backend": "spectrum_spd_speed",
            "seed": 7,
            "steps": 30,
            "cfg": 6.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "beta",
        }
        spectrum = {"enabled": True}
        corrections = {"enabled": True}
        spd = {"scale": 0.5}
        with patch.object(sampling, "_resolve_aio_runtime_seed", return_value=77):
            result = sampling._aio_stage_sampler_settings(
                base,
                {
                    "inherit_sampler_settings": True,
                    "denoise": 0.4,
                    "spectrum": spectrum,
                    "dit_corrections": corrections,
                    "spd": spd,
                },
                scheduler_default="simple",
                inherit_backend=True,
            )

        self.assertEqual(result["backend"], "comfy_ksampler")
        self.assertEqual(result["seed"], 77)
        self.assertEqual(result["seed_after_generate"], sampling.SEED_CONTROL_FIXED)
        self.assertEqual(result["sampler_name"], "euler")
        self.assertEqual(result["scheduler"], "beta")
        self.assertEqual(result["steps"], 30)
        self.assertEqual(result["cfg"], 6.0)
        self.assertEqual(result["denoise"], 0.4)
        self.assertEqual(result["spectrum_extra"], {})
        self.assertEqual(result["spd_extra"], {})
        self.assertEqual(result["spectrum"], spectrum)
        self.assertIsNot(result["spectrum"], spectrum)
        self.assertIsNot(result["dit_corrections"], corrections)
        self.assertIsNot(result["spd"], spd)

    def test_highres_effective_backend_preserves_disabled_inherit_and_spd_fallback(
        self,
    ):
        self.assertEqual(
            sampling._aio_highres_effective_backend({}, {"enabled": False}), ""
        )
        self.assertEqual(
            sampling._aio_highres_effective_backend(
                {"backend": "spectrum_mod_guidance_advanced"},
                {"enabled": True, "inherit_sampler_settings": True},
            ),
            "spectrum_mod_guidance_advanced",
        )
        self.assertEqual(
            sampling._aio_highres_effective_backend(
                {"backend": "spectrum_spd_speed"},
                {"enabled": True, "inherit_sampler_settings": True},
            ),
            "comfy_ksampler",
        )
        self.assertEqual(
            sampling._aio_highres_effective_backend(
                {"backend": "spectrum_mod_guidance_advanced"},
                {"enabled": True, "inherit_sampler_settings": False},
            ),
            "comfy_ksampler",
        )


if __name__ == "__main__":
    unittest.main()
