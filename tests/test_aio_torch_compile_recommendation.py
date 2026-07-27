from __future__ import annotations

import copy
import unittest

from easyuse_anima.aio.torch_compile_recommendation import (
    AIO_TORCH_COMPILE_RECOMMENDATION_POLICY_VERSION,
    classify_torch_compile_vram,
    classify_torch_compile_workload,
    recommend_torch_compile,
)


SUPPORTED_INPUTS = [
    "model",
    "backend",
    "fullgraph",
    "mode",
    "dynamic",
    "compile_transformer_blocks_only",
    "dynamo_cache_size_limit",
    "debug_compile_keys",
    "disable_dynamic_vram",
]


def _diagnostics(*, vram=16302, supported=True):
    return {
        "schema_version": 1,
        "policy_version": "diagnostics-v1",
        "supported": supported,
        "profile": "diagnostics_only" if supported else "unsupported",
        "values": {},
        "environment": {
            "python_version": "3.13.5",
            "torch_version": "2.12.1+cu130",
            "accelerator": "cuda" if supported else "cpu",
            "cuda_runtime_version": "13.0" if supported else None,
            "rocm_runtime_version": None,
            "device_name": "Fake Device",
            "compute_capability": "12.0" if supported else None,
            "total_vram_mb": vram,
            "kj_node_available": supported,
            "kj_contract_compatible": supported,
            "supported_inputs": list(SUPPORTED_INPUTS) if supported else [],
            "input_options": {
                "backend": ["inductor", "cudagraphs"],
                "mode": [
                    "default",
                    "max-autotune",
                    "max-autotune-no-cudagraphs",
                    "reduce-overhead",
                ],
                "dynamic": ["auto", "true", "false"],
            },
        },
        "reason_codes": ["diagnostics_ready"] if supported else ["cuda_unavailable"],
        "warnings": ["recommendation_policy_pending"],
    }


def _settings(*, highres=False, detailer=False, upscale=False, backend="usdu"):
    return {
        "highres": {"enabled": highres},
        "detailer": {"enabled": detailer},
        "upscale": {"enabled": upscale, "backend": backend},
    }


class TorchCompileWorkloadClassificationTests(unittest.TestCase):
    def test_fixed_variable_unknown_and_resshift_boundaries(self):
        cases = (
            (
                "fixed",
                _settings(),
                {"width": 1024, "height": 1024},
                "fixed_shapes",
                [],
            ),
            (
                "highres",
                _settings(highres=True),
                {"width": 1024, "height": 1024},
                "variable_shapes",
                ["highres"],
            ),
            (
                "detailer",
                _settings(detailer=True),
                {"width": 1024, "height": 1024},
                "variable_shapes",
                ["detailer"],
            ),
            (
                "usdu",
                _settings(upscale=True, backend="usdu"),
                {"width": 1024, "height": 1024},
                "variable_shapes",
                ["upscale"],
            ),
            (
                "resshift",
                _settings(upscale=True, backend="resshift"),
                {"width": 1024, "height": 1024},
                "fixed_shapes",
                [],
            ),
            (
                "missing resolution",
                _settings(),
                {},
                "unknown",
                [],
            ),
            (
                "unknown upscale backend",
                _settings(upscale=True, backend="future"),
                {"width": 1024, "height": 1024},
                "unknown",
                [],
            ),
            (
                "missing stage contract",
                {"highres": {}, "detailer": {"enabled": False}, "upscale": {"enabled": False}},
                {"width": 1024, "height": 1024},
                "unknown",
                [],
            ),
        )
        for name, settings, resolution, expected_class, expected_stages in cases:
            with self.subTest(name=name):
                workload = classify_torch_compile_workload(
                    settings,
                    resolution,
                    1,
                )
                self.assertEqual(workload["shape_class"], expected_class)
                self.assertEqual(workload["active_shape_stages"], expected_stages)

    def test_non_positive_batch_is_unknown(self):
        workload = classify_torch_compile_workload(
            _settings(),
            {"width": 1024, "height": 1024},
            0,
        )

        self.assertEqual(workload["shape_class"], "unknown")
        self.assertIsNone(workload["batch_size"])
        self.assertIn("batch_size_unknown", workload["reason_codes"])

    def test_vram_tiers_have_explicit_practical_boundaries(self):
        cases = (
            (None, "unknown"),
            (0, "unknown"),
            (8191, "low"),
            (8192, "medium"),
            (15359, "medium"),
            (15360, "high"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(classify_torch_compile_vram(value), expected)


class TorchCompileRecommendationPolicyTests(unittest.TestCase):
    def test_fixed_high_vram_uses_balanced_static_safe_axis(self):
        payload = recommend_torch_compile(
            _diagnostics(),
            _settings(),
            {"width": 1024, "height": 1024},
            1,
        )

        self.assertTrue(payload["supported"])
        self.assertEqual(payload["policy_version"], AIO_TORCH_COMPILE_RECOMMENDATION_POLICY_VERSION)
        self.assertEqual(payload["profile"], "stable_fixed_shapes")
        self.assertEqual(
            payload["values"],
            {
                "enabled": True,
                "backend": "inductor",
                "fullgraph": False,
                "mode": "default",
                "dynamic": "false",
                "compile_transformer_blocks_only": True,
                "dynamo_cache_size_limit": 64,
                "debug_compile_keys": False,
                "disable_dynamic_vram": False,
            },
        )
        self.assertEqual(payload["workload"]["shape_class"], "fixed_shapes")
        self.assertEqual(payload["workload"]["vram_tier"], "high")
        self.assertIn("first_compile_may_be_slow", payload["warnings"])
        self.assertNotIn("recommendation_policy_pending", payload["warnings"])

    def test_variable_stage_profiles_use_automatic_dynamic_shapes(self):
        cases = (
            (_settings(highres=True), "highres_changes_shape"),
            (_settings(detailer=True), "detailer_uses_variable_crops"),
            (_settings(upscale=True, backend="usdu"), "usdu_uses_tiles"),
        )
        for settings, reason in cases:
            with self.subTest(reason=reason):
                payload = recommend_torch_compile(
                    _diagnostics(vram=12288),
                    settings,
                    {"width": 1024, "height": 1024},
                    1,
                )
                self.assertTrue(payload["supported"])
                self.assertEqual(payload["profile"], "stable_variable_shapes")
                self.assertEqual(payload["values"]["dynamic"], "auto")
                self.assertEqual(payload["values"]["mode"], "default")
                self.assertIn(reason, payload["reason_codes"])
                self.assertIn("shape_changes_may_recompile", payload["warnings"])

    def test_low_and_unknown_inputs_remain_conservative_without_forcing_dynamic_vram(self):
        cases = (
            (
                4096,
                _settings(),
                {"width": 1024, "height": 1024},
                "conservative_low_vram",
                "false",
                "low_vram_peak_risk",
            ),
            (
                None,
                _settings(),
                {"width": 1024, "height": 1024},
                "conservative_unknown",
                "false",
                "vram_unknown",
            ),
            (
                16302,
                _settings(),
                {},
                "conservative_unknown",
                "auto",
                "workload_shape_unknown",
            ),
        )
        for vram, settings, resolution, profile, dynamic, warning in cases:
            with self.subTest(profile=profile, warning=warning):
                payload = recommend_torch_compile(
                    _diagnostics(vram=vram),
                    settings,
                    resolution,
                    1,
                )
                self.assertEqual(payload["profile"], profile)
                self.assertEqual(payload["values"]["mode"], "default")
                self.assertEqual(payload["values"]["dynamic"], dynamic)
                self.assertFalse(payload["values"]["disable_dynamic_vram"])
                self.assertIn(warning, payload["warnings"])

    def test_batch_warning_and_resshift_no_sampling_model_contract(self):
        payload = recommend_torch_compile(
            _diagnostics(),
            _settings(upscale=True, backend="resshift"),
            {"width": 1024, "height": 1024},
            2,
        )

        self.assertEqual(payload["workload"]["shape_class"], "fixed_shapes")
        self.assertEqual(payload["workload"]["active_shape_stages"], [])
        self.assertIn("resshift_has_no_sampling_model", payload["reason_codes"])
        self.assertIn("batch_size_increases_memory", payload["warnings"])

    def test_unsupported_diagnostics_and_contract_drift_fail_closed(self):
        unsupported = recommend_torch_compile(
            _diagnostics(supported=False),
            _settings(),
            {"width": 1024, "height": 1024},
            1,
        )
        self.assertFalse(unsupported["supported"])
        self.assertEqual(unsupported["values"], {})
        self.assertIn("recommendation_unavailable", unsupported["warnings"])

        missing_input = _diagnostics()
        missing_input["environment"]["supported_inputs"].remove("debug_compile_keys")
        drift = recommend_torch_compile(
            missing_input,
            _settings(),
            {"width": 1024, "height": 1024},
            1,
        )
        self.assertFalse(drift["supported"])
        self.assertEqual(drift["values"], {})
        self.assertIn("kj_recommendation_input_drift", drift["reason_codes"])

    def test_missing_safe_choices_fail_closed_and_fixed_dynamic_has_bounded_fallback(self):
        unsafe = _diagnostics()
        unsafe["environment"]["input_options"]["backend"] = ["future"]
        failed = recommend_torch_compile(
            unsafe,
            _settings(),
            {"width": 1024, "height": 1024},
            1,
        )
        self.assertFalse(failed["supported"])
        self.assertIn("kj_safe_choice_unavailable", failed["reason_codes"])

        fixed_fallback = _diagnostics()
        fixed_fallback["environment"]["input_options"]["dynamic"] = ["auto"]
        fixed = recommend_torch_compile(
            fixed_fallback,
            _settings(),
            {"width": 1024, "height": 1024},
            1,
        )
        self.assertEqual(fixed["values"]["dynamic"], "auto")
        self.assertIn("dynamic_choice_conservative_fallback", fixed["warnings"])

        variable_drift = _diagnostics()
        variable_drift["environment"]["input_options"]["dynamic"] = ["false"]
        variable = recommend_torch_compile(
            variable_drift,
            _settings(highres=True),
            {"width": 1024, "height": 1024},
            1,
        )
        self.assertFalse(variable["supported"])
        self.assertEqual(variable["values"], {})
        self.assertIn("kj_safe_choice_unavailable", variable["reason_codes"])

    def test_policy_is_deterministic_and_does_not_mutate_inputs(self):
        diagnostics = _diagnostics()
        settings = _settings(highres=True)
        resolution = {"width": 1024, "height": 1536}
        originals = copy.deepcopy((diagnostics, settings, resolution))

        first = recommend_torch_compile(diagnostics, settings, resolution, 1)
        second = recommend_torch_compile(diagnostics, settings, resolution, 1)

        self.assertEqual(first, second)
        self.assertEqual((diagnostics, settings, resolution), originals)


if __name__ == "__main__":
    unittest.main()
