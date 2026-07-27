from __future__ import annotations

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

from easyuse_anima.aio import negpip as negpip_contract
from tests.comfy_host_fakes import FakeComfyHostProvider, use_fake_comfy_host

_ROOT_MODULE = SimpleNamespace(__package__="")


class FakeValue:
    def __init__(self, *, patch_depth: int = 0):
        self.patch_depth = patch_depth


class CompatibleCLIPNegPip:
    calls: list[dict[str, FakeValue]] = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP")

    @classmethod
    def execute(cls, **kwargs):
        cls.calls.append(dict(kwargs))
        incoming_depth = max(
            kwargs["model"].patch_depth,
            kwargs["clip"].patch_depth,
        )
        applied_depth = max(1, incoming_depth)
        return SimpleNamespace(
            result=(
                FakeValue(patch_depth=applied_depth),
                FakeValue(patch_depth=applied_depth),
            )
        )


class NegPipExternalContractTests(unittest.TestCase):
    def setUp(self):
        CompatibleCLIPNegPip.calls = []

    def test_dependency_absence_is_serializable_and_does_not_invoke(self):
        requested = []

        payload = negpip_contract.collect_negpip_contract(
            lambda node_id: requested.append(node_id) or None
        )

        self.assertEqual(requested, ["CLIPNegPip"])
        self.assertEqual(
            payload,
            {
                "available": False,
                "compatible": False,
                "node_id": "CLIPNegPip",
                "node_pack": "ComfyUI-ppm",
                "repository": "https://github.com/pamparamm/ComfyUI-ppm",
                "contract_revision": 1,
                "reason_codes": ["ppm_negpip_missing"],
            },
        )
        self.assertEqual(CompatibleCLIPNegPip.calls, [])

    def test_compatible_v3_schema_and_node_output_are_adapted_once(self):
        payload = negpip_contract.collect_negpip_contract(
            lambda _node_id: CompatibleCLIPNegPip
        )
        model = FakeValue()
        clip = FakeValue()

        patched_model, patched_clip = negpip_contract.invoke_negpip_node(
            CompatibleCLIPNegPip,
            model,
            clip,
        )

        self.assertTrue(payload["available"])
        self.assertTrue(payload["compatible"])
        self.assertEqual(payload["reason_codes"], ["ppm_negpip_contract_ready"])
        self.assertEqual(CompatibleCLIPNegPip.calls, [{"model": model, "clip": clip}])
        self.assertIsNot(patched_model, model)
        self.assertIsNot(patched_clip, clip)
        self.assertEqual((patched_model.patch_depth, patched_clip.patch_depth), (1, 1))

    def test_input_output_and_execute_drift_fail_closed_without_invocation(self):
        class InputDrift(CompatibleCLIPNegPip):
            @classmethod
            def INPUT_TYPES(cls):
                inputs = super().INPUT_TYPES()
                inputs["required"]["mode"] = ("STRING",)
                return inputs

        class OutputDrift(CompatibleCLIPNegPip):
            RETURN_TYPES = ("MODEL",)

        class ExecuteDrift(CompatibleCLIPNegPip):
            @classmethod
            def execute(cls, model, clip, new_required):
                raise AssertionError("drifted contract must not be invoked")

        for node_class, reason_code in (
            (InputDrift, "ppm_negpip_input_contract_drift"),
            (OutputDrift, "ppm_negpip_output_contract_drift"),
            (ExecuteDrift, "ppm_negpip_execute_contract_drift"),
        ):
            with self.subTest(node_class=node_class.__name__):
                payload = negpip_contract.collect_negpip_contract(
                    lambda _node_id, node_class=node_class: node_class
                )
                self.assertFalse(payload["compatible"])
                self.assertIn(reason_code, payload["reason_codes"])
                with self.assertRaisesRegex(RuntimeError, reason_code):
                    negpip_contract.invoke_negpip_node(
                        node_class,
                        FakeValue(),
                        FakeValue(),
                    )
        self.assertEqual(CompatibleCLIPNegPip.calls, [])

    def test_unreadable_and_malformed_outputs_fail_closed(self):
        class Unreadable(CompatibleCLIPNegPip):
            @classmethod
            def INPUT_TYPES(cls):
                raise RuntimeError(r"C:\Users\alice\private-token")

        payload = negpip_contract.collect_negpip_contract(
            lambda _node_id: Unreadable
        )
        self.assertEqual(
            payload["reason_codes"],
            ["ppm_negpip_contract_unreadable"],
        )
        self.assertNotIn("alice", str(payload))
        self.assertNotIn("private-token", str(payload))

        model = FakeValue()
        clip = FakeValue()
        malformed_results = (
            SimpleNamespace(result=(FakeValue(),)),
            SimpleNamespace(result=(FakeValue(), FakeValue(), FakeValue())),
            SimpleNamespace(result=(None, FakeValue())),
            SimpleNamespace(result=(model, FakeValue())),
            SimpleNamespace(result=(FakeValue(), clip)),
        )
        for malformed in malformed_results:
            with self.subTest(result=malformed.result):
                class Malformed(CompatibleCLIPNegPip):
                    @classmethod
                    def execute(cls, **_kwargs):
                        return malformed

                with self.assertRaisesRegex(RuntimeError, "CLIPNegPip"):
                    negpip_contract.invoke_negpip_node(Malformed, model, clip)

    def test_repeated_invocation_calls_upstream_once_and_preserves_idempotency(self):
        first_model, first_clip = negpip_contract.invoke_negpip_node(
            CompatibleCLIPNegPip,
            FakeValue(),
            FakeValue(),
        )
        second_model, second_clip = negpip_contract.invoke_negpip_node(
            CompatibleCLIPNegPip,
            first_model,
            first_clip,
        )

        self.assertEqual(len(CompatibleCLIPNegPip.calls), 2)
        self.assertEqual((first_model.patch_depth, first_clip.patch_depth), (1, 1))
        self.assertEqual((second_model.patch_depth, second_clip.patch_depth), (1, 1))
        self.assertIs(CompatibleCLIPNegPip.calls[1]["model"], first_model)
        self.assertIs(CompatibleCLIPNegPip.calls[1]["clip"], first_clip)

    def test_module_has_no_eager_private_import_or_vendored_upstream_symbols(self):
        module_path = Path(negpip_contract.__file__)
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        self.assertFalse(
            any(
                name == "comfy"
                or name.startswith("comfy.")
                or name.startswith("comfy_api")
                or name.startswith("nodes_ppm")
                for name in imported_modules
            )
        )
        self.assertNotIn("importlib", imported_modules)
        for upstream_symbol in (
            "patch_adv_encode",
            "patch_negpip",
            "anima_extra_conds_negpip",
            "cosmos_diffusion_negpip_wrapper",
        ):
            self.assertNotIn(upstream_symbol, source)


class NegPipOnModeTests(unittest.TestCase):
    def setUp(self):
        CompatibleCLIPNegPip.calls = []

    def test_absent_and_explicit_off_preserve_identity_without_dependency_lookup(self):
        class TrackingProvider(FakeComfyHostProvider):
            def __init__(self):
                super().__init__()
                self.requests = []

            def find_node_class(self, node_id: str):
                self.requests.append(node_id)
                return super().find_node_class(node_id)

        provider = TrackingProvider()
        model = FakeValue()
        clip = FakeValue()
        with use_fake_comfy_host(_ROOT_MODULE, provider):
            for value in (None, {"mode": "off"}):
                with self.subTest(value=value):
                    mode = negpip_contract._aio_negpip_mode(value)
                    result = negpip_contract.apply_aio_negpip(model, clip, mode)
                    self.assertEqual(result, (model, clip))
                    self.assertIs(result[0], model)
                    self.assertIs(result[1], clip)
                    self.assertIsNone(
                        negpip_contract._aio_negpip_cache_signature(value)
                    )
                    self.assertIsNone(negpip_contract._aio_negpip_metadata(mode))
        self.assertEqual(provider.requests, [])

    def test_on_requires_public_node_and_invokes_exactly_once(self):
        model = FakeValue()
        clip = FakeValue()
        provider = FakeComfyHostProvider(
            node_classes={"CLIPNegPip": CompatibleCLIPNegPip}
        )
        with use_fake_comfy_host(_ROOT_MODULE, provider):
            patched_model, patched_clip = negpip_contract.apply_aio_negpip(
                model,
                clip,
                negpip_contract._aio_negpip_mode({"mode": "on"}),
            )

        self.assertEqual(CompatibleCLIPNegPip.calls, [{"model": model, "clip": clip}])
        self.assertIsNot(patched_model, model)
        self.assertIsNot(patched_clip, clip)
        self.assertEqual(
            negpip_contract._aio_negpip_cache_signature({"mode": "on"}),
            {"mode": "on", "contract_revision": 1},
        )
        self.assertEqual(
            negpip_contract._aio_negpip_metadata("on"),
            {"mode": "on", "contract_revision": 1},
        )

    def test_turbo_uses_same_public_node_and_records_derived_contract(self):
        model = FakeValue()
        clip = FakeValue()
        provider = FakeComfyHostProvider(
            node_classes={"CLIPNegPip": CompatibleCLIPNegPip}
        )
        with use_fake_comfy_host(_ROOT_MODULE, provider):
            patched_model, patched_clip = negpip_contract.apply_aio_negpip(
                model,
                clip,
                negpip_contract._aio_negpip_mode({"mode": "turbo"}),
            )

        self.assertEqual(CompatibleCLIPNegPip.calls, [{"model": model, "clip": clip}])
        self.assertIsNot(patched_model, model)
        self.assertIsNot(patched_clip, clip)
        cache_signature = negpip_contract._aio_negpip_cache_signature(
            {"mode": "turbo"},
            negative_prompt="bad anatomy",
        )
        metadata = negpip_contract._aio_negpip_metadata(
            "turbo",
            negative_prompt="bad anatomy",
        )
        self.assertEqual(cache_signature["mode"], "turbo")
        self.assertEqual(cache_signature["contract_revision"], 1)
        self.assertEqual(cache_signature["policy_revision"], 1)
        self.assertEqual(cache_signature["negative_scale"], -1.0)
        self.assertEqual(cache_signature["effective_first_pass_cfg"], 1.0)
        self.assertEqual(
            metadata,
            {
                "mode": "turbo",
                "contract_revision": 1,
                "policy_revision": 1,
                "negative_scale": -1.0,
                "derived_prompt_fingerprint": cache_signature[
                    "derived_prompt_fingerprint"
                ],
                "effective_cfg": {
                    "first_pass": 1.0,
                    "highres": 1.0,
                    "detailer": 1.0,
                    "upscale_usdu": 1.0,
                },
            },
        )

    def test_missing_dependency_and_unsupported_modes_fail_closed(self):
        with use_fake_comfy_host(_ROOT_MODULE, FakeComfyHostProvider()):
            for mode in ("on", "turbo"):
                with self.subTest(mode=mode):
                    with self.assertRaisesRegex(RuntimeError, "ComfyUI-ppm"):
                        negpip_contract.apply_aio_negpip(
                            FakeValue(),
                            FakeValue(),
                            mode,
                        )

        for value in ({}, {"mode": "unknown"}, "on", {"mode": None}):
            with self.subTest(value=value):
                with self.assertRaisesRegex(RuntimeError, "NegPip"):
                    negpip_contract._aio_negpip_mode(value)


if __name__ == "__main__":
    unittest.main()
