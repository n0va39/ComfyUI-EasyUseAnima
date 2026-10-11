from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from contextlib import contextmanager
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import torch

from easyuse_anima.aio import ipadapter_hook as bridge
from easyuse_anima.aio import ipadapter_lifecycle as lifecycle
from easyuse_anima.aio.hooks import aio_hook_change_token
from easyuse_anima.aio.hooks.contracts import AioHookPoint, AioStage, AioStagePhase
from easyuse_anima.nodes.ipadapter_nodes import EasyAnimaIPAdapterHook
from easyuse_anima.registration import NODE_CLASS_MAPPINGS


class Attention(torch.nn.Module):
    def __init__(self):
        super().__init__()
        for name in ("q_proj", "k_proj", "v_proj", "output_proj"):
            setattr(self, name, torch.nn.Linear(2, 2))

    def forward(self, x):
        return self.output_proj(self.v_proj(x))


class Block(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.cross_attn = Attention()

    def forward(self, x):
        return self.cross_attn(x)


class Encoder(torch.nn.Linear):
    """Track upstream placement requests without requiring a GPU in unit tests."""

    def __init__(self):
        super().__init__(2, 2)
        self.moves = []

    def to(self, device):
        self.moves.append(torch.device(device))
        return self


def clone_containers(value):
    if isinstance(value, dict):
        return {key: clone_containers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clone_containers(item) for item in value]
    return value


class Model:
    def __init__(self, count=28):
        dit = torch.nn.Module()
        dit.blocks = torch.nn.ModuleList(Block() for _ in range(count))
        self.model = SimpleNamespace(diffusion_model=dit, model_lowvram=False)
        self.load_device = torch.device("cpu")
        self.model_options = {"transformer_options": {}}
        self.wrappers = {}
        self.dynamic = False
        self.additional_models = {}

    def clone(self):
        result = copy.copy(self)
        result.model_options = clone_containers(self.model_options)
        result.wrappers = clone_containers(self.wrappers)
        return result

    def is_dynamic(self):
        return self.dynamic

    def get_additional_models_with_key(self, key):
        return self.additional_models.get(key, [])

    def add_wrapper_with_key(self, kind, key, wrapper):
        self.wrappers.setdefault(kind, {}).setdefault(key, []).append(wrapper)

    def get_wrappers(self, kind, key):
        return self.wrappers.get(kind, {}).get(key, [])


def adapter():
    return {
        "num_blocks": 28,
        "ip_weights": {},
        "lora_weights": {},
        **{key: Encoder() for key in (
            "siglip_encoder", "siglip_norm", "siglip_compressor", "ip_self_attn"
        )},
    }


@contextmanager
def comfy_contract():
    """Only the two imported Comfy interfaces are stubbed; rollback uses real torch."""
    comfy = ModuleType("comfy")
    patcher = ModuleType("comfy.model_patcher")
    patcher.create_model_options_clone = clone_containers
    extension = ModuleType("comfy.patcher_extension")
    extension.WrappersMP = SimpleNamespace(SAMPLER_SAMPLE="sampler_sample")
    comfy.model_patcher = patcher
    comfy.patcher_extension = extension
    with patch.dict(sys.modules, {
        "comfy": comfy, "comfy.model_patcher": patcher,
        "comfy.patcher_extension": extension,
    }):
        yield


def mutate(model, payload, *, partial=False):
    """Exercise the reviewed external mutation surfaces, without copying its math."""
    dit = model.model.diffusion_model
    dit.shared_ip_k_proj = torch.nn.Linear(2, 2)
    dit.shared_ip_v_proj = torch.nn.Linear(2, 2)
    for block in dit.blocks[:1] if partial else dit.blocks:
        block.ip_k_proj = torch.nn.Linear(2, 2)
        block.ip_v_proj = torch.nn.Linear(2, 2)
        block.adaln_ip = torch.nn.Linear(2, 2)
        block.ip_k_norm = torch.nn.LayerNorm(2)
        block.use_ip_adapter = True
        block.ip_norm_keys = True
        block.ip_inject_before_mlp = False
        original = block.forward
        block.forward = lambda x, original=original: original(x) + 1
        block._ip_fwd_patched = True
        block._ip_hook_installed = True
        block._x_cross_flat = torch.ones(1, 2)
        block.cross_attn.register_forward_pre_hook(lambda module, args: None)
        block.cross_attn.register_forward_pre_hook(
            lambda module, args, kwargs: None, with_kwargs=True,
        )
        for name in ("q_proj", "k_proj", "v_proj", "output_proj"):
            setattr(block.cross_attn, name, torch.nn.Sequential(getattr(block.cross_attn, name)))
    for key in ("siglip_encoder", "siglip_norm", "siglip_compressor", "ip_self_attn"):
        payload[key].to("cuda")


class AioIPAdapterHookTests(unittest.TestCase):
    def build(self, payload=None, **kwargs):
        with patch.object(bridge, "resolve_apply"):
            return EasyAnimaIPAdapterHook().build(
                payload or adapter(), torch.zeros(1, 4, 4, 3), 0.75, **kwargs
            )[0]

    def assert_clean(self, model, original_state, original_layers, original_hooks):
        dit = model.model.diffusion_model
        self.assertEqual(set(dit.state_dict()), set(original_state))
        for name, value in dit.state_dict().items():
            self.assertTrue(torch.equal(value, original_state[name]), name)
        for index, block in enumerate(dit.blocks):
            self.assertNotIn("forward", vars(block))
            self.assertFalse(hasattr(block, "_x_cross_flat"))
            self.assertFalse(hasattr(block, "use_ip_adapter"))
            self.assertFalse(hasattr(block, "_ip_fwd_patched"))
            self.assertFalse(hasattr(block, "_ip_hook_installed"))
            self.assertEqual(dict(block.cross_attn._forward_pre_hooks), original_hooks[index][0])
            self.assertEqual(dict(block.cross_attn._forward_pre_hooks_with_kwargs), original_hooks[index][1])
            for name, layer in original_layers[index].items():
                self.assertIs(getattr(block.cross_attn, name), layer)
        lifecycle.validate_clean_model(model, {"num_blocks": 28})

    def snapshot(self, model):
        blocks = model.model.diffusion_model.blocks
        return (
            {k: v.clone() for k, v in model.model.diffusion_model.state_dict().items()},
            [{name: getattr(b.cross_attn, name) for name in (
                "q_proj", "k_proj", "v_proj", "output_proj"
            )} for b in blocks],
            [(dict(b.cross_attn._forward_pre_hooks), dict(b.cross_attn._forward_pre_hooks_with_kwargs))
             for b in blocks],
        )

    def test_public_node_contract_settings_and_cache_bypass(self):
        self.assertIs(NODE_CLASS_MAPPINGS["EasyAnimaIPAdapterHook"], EasyAnimaIPAdapterHook)
        inputs = EasyAnimaIPAdapterHook.INPUT_TYPES()["required"]
        self.assertEqual(inputs["ip_adapter"][0], "ANIMA_IP_ADAPTER")
        self.assertEqual(inputs["ref_image"][0], "IMAGE")
        self.assertEqual(EasyAnimaIPAdapterHook.RETURN_NAMES, ("aio_hook",))
        hook = self.build(ip_cfg_separate=True, gray_null=True, use_lora=False)
        self.assertEqual(hook.settings["strength"], 0.75)
        self.assertTrue(hook.settings["ip_cfg_separate"])
        self.assertTrue(hook.settings["gray_null"])
        self.assertFalse(hook.settings["use_lora"])
        self.assertEqual(hook.describe().points, frozenset({
            AioHookPoint(AioStage.FIRST_PASS, AioStagePhase.BEFORE)
        }))
        self.assertIsNone(hook.describe().fingerprint)
        self.assertFalse(aio_hook_change_token(hook)[0])

    def test_missing_wrong_and_changed_upstream_rejected(self):
        with patch.object(bridge, "_find_comfy_node_class", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "Install/enable"):
                bridge.resolve_apply()
        source = b"reviewed fixture\n"
        expected = hashlib.sha256(source).hexdigest()
        cls = type("ExternalApply", (), {"FUNCTION": "apply", "RETURN_TYPES": ("MODEL",)})
        with patch.object(bridge, "_find_comfy_node_class", return_value=cls), \
                patch.object(bridge.inspect, "getsourcefile", return_value="fixture.py"), \
                patch.object(bridge.Path, "read_bytes", return_value=source.replace(b"\n", b"\r\n")), \
                patch.object(bridge, "_SOURCE_SHA256", expected):
            self.assertIs(bridge.resolve_apply(), cls)
            cls.RETURN_TYPES = ("IMAGE",)
            with self.assertRaisesRegex(RuntimeError, "contract"):
                bridge.resolve_apply()
            cls.RETURN_TYPES = ("MODEL",)
            with patch.object(bridge.Path, "read_bytes", return_value=source + b"changed"):
                with self.assertRaisesRegex(RuntimeError, "Unsupported"):
                    bridge.resolve_apply()

    def test_invalid_reference_and_size_rejected_before_hook_use(self):
        with patch.object(bridge, "resolve_apply"):
            for shape in ((2, 4, 4, 3), (1, 4, 4, 4), (4, 4, 3)):
                with self.subTest(shape=shape), self.assertRaisesRegex(RuntimeError, "one RGB"):
                    EasyAnimaIPAdapterHook().build(adapter(), torch.zeros(shape), 1.0)
        with self.assertRaisesRegex(ValueError, "multiple of 16"):
            self.build(ref_image_size=225)

    def test_session_registers_only_sampling_wrapper_and_rejects_duplicate(self):
        model = Model()
        model.load_device = torch.device("cuda", 0)
        hook = self.build()
        event = SimpleNamespace(
            state=SimpleNamespace(model=model),
            request=SimpleNamespace(settings={"sampler": {"backend": "comfy_ksampler"}}),
        )
        before = self.snapshot(model)
        with comfy_contract(), patch("torch.cuda.current_device", return_value=0):
            result = hook.create_session(None).before_stage(event)
            self.assertIsNot(result.model, model)
            self.assertIs(result.model.model, model.model)
            self.assertEqual(result.metadata["upstream_commit"], bridge.UPSTREAM_COMMIT)
            self.assertEqual(result.metadata["stage"], "first_pass")
            self.assertEqual(result.metadata["settings"], hook.settings)
            self.assertEqual(model.model_options, {"transformer_options": {}})
            self.assertEqual(model.wrappers, {})
            wrappers = result.model.wrappers
            self.assertEqual(set(wrappers), {"sampler_sample"})
            self.assertEqual(len(wrappers["sampler_sample"][bridge._WRAPPER_KEY]), 1)
            event.state.model = result.model
            with self.assertRaisesRegex(RuntimeError, "only one"):
                hook.create_session(None).before_stage(event)
        self.assert_clean(model, *before)

    def test_success_failures_and_interrupts_restore_partial_mutations_and_options(self):
        for where, error in ((None, None), ("apply", RuntimeError), ("apply", KeyboardInterrupt),
                             ("sample", RuntimeError), ("sample", KeyboardInterrupt)):
            with self.subTest(where=where, error=error):
                model, payload = Model(), adapter()
                block = model.model.diffusion_model.blocks[0]
                calls = []
                block.cross_attn.register_forward_pre_hook(lambda m, a: calls.append("existing"))
                block.cross_attn.register_forward_pre_hook(lambda m, a, k: None, with_kwargs=True)
                before = self.snapshot(model)
                original_output = block(torch.ones(1, 2)).detach().clone()
                options = {"transformer_options": {"wrappers": {
                    "sampler_sample": {bridge._WRAPPER_KEY: [object()]}
                }}, "existing": "preserved"}
                original_wrapper = options["transformer_options"]["wrappers"]["sampler_sample"][bridge._WRAPPER_KEY][0]
                extra = {"model_options": options, "seed": 7}
                guider = SimpleNamespace(model_patcher=model, model_options={"owner": "guider"})
                guider_options = guider.model_options
                owner = self

                class Apply:
                    def apply(self, clone, supplied, image, **settings):
                        owner.assertIsNot(clone, model)
                        owner.assertIs(clone.model, model.model)
                        owner.assertIs(supplied, payload)
                        mutate(clone, supplied, partial=where == "apply")
                        if where == "apply":
                            raise error("apply failed")
                        clone.model_options["model_function_wrapper"] = "adapter wrapper"
                        return (clone,)

                def sample(actual_guider, sigmas, supplied, callback, noise, *args, **kwargs):
                    self.assertIs(actual_guider, guider)
                    self.assertIsNot(supplied, extra)
                    self.assertEqual(supplied["seed"], 7)
                    self.assertEqual(supplied["model_options"]["model_function_wrapper"], "adapter wrapper")
                    self.assertNotIn(bridge._WRAPPER_KEY, supplied["model_options"]["transformer_options"]["wrappers"]["sampler_sample"])
                    self.assertTrue(torch.allclose(block(torch.ones(1, 2)), original_output + 1))
                    if where == "sample":
                        raise error("sample failed")
                    return "sample result"

                with comfy_contract(), patch.object(bridge, "resolve_apply", return_value=Apply):
                    operation = lambda: bridge.IPAdapterSample(payload, torch.zeros(1, 4, 4, 3), {})(
                        sample, guider, torch.ones(2), extra, None, torch.zeros(1, 4, 2, 2)
                    )
                    if error:
                        with self.assertRaises(error):
                            operation()
                    else:
                        self.assertEqual(operation(), "sample result")
                self.assert_clean(model, *before)
                self.assertTrue(torch.equal(block(torch.ones(1, 2)), original_output))
                self.assertIs(guider.model_patcher, model)
                self.assertIs(guider.model_options, guider_options)
                self.assertNotIn("model_function_wrapper", options)
                self.assertIs(options["transformer_options"]["wrappers"]["sampler_sample"][bridge._WRAPPER_KEY][0], original_wrapper)
                for key in ("siglip_encoder", "siglip_norm", "siglip_compressor", "ip_self_attn"):
                    self.assertEqual(payload[key].moves, [torch.device("cuda"), torch.device("cpu")])
                self.assertGreaterEqual(len(calls), 2)

    def test_repeated_on_off_calls_do_not_accumulate_model_changes(self):
        model, payload = Model(), adapter()
        before = self.snapshot(model)
        block = model.model.diffusion_model.blocks[0]
        image = torch.ones(1, 2)
        off = block(image).detach().clone()
        for _ in range(3):
            with lifecycle.temporary_ipadapter(model, payload):
                mutate(model, payload)
                self.assertTrue(torch.allclose(block(image), off + 1))
            self.assert_clean(model, *before)
            self.assertTrue(torch.equal(block(image), off))

    def test_prepatched_or_unsupported_architectures_rejected_without_mutation(self):
        cases = (
            (lambda m, a: setattr(m.model.diffusion_model, "shared_ip_k_proj", object()), "existing"),
            (lambda m, a: setattr(m.model.diffusion_model.blocks[0], "_ip_hook_installed", True), "clean blocks"),
            (lambda m, a: setattr(m.model.diffusion_model.blocks[0], "forward", lambda x: x), "replaced"),
            (lambda m, a: a.update(num_blocks=40), "28-block"),
            (lambda m, a: a.update(ip_inject_before_mlp=True), "architecture"),
            (lambda m, a: a["ip_weights"].update({"shared_ip_q_proj.weight": torch.zeros(2, 2)}), "architecture"),
            (lambda m, a: a.update(lora_weights={0: {"unexpected": {}}}), "target layers"),
        )
        for change, message in cases:
            with self.subTest(message=message):
                model, payload = Model(), adapter()
                change(model, payload)
                state = {k: v.clone() for k, v in model.model.diffusion_model.state_dict().items()}
                with self.assertRaisesRegex(RuntimeError, message):
                    with lifecycle.temporary_ipadapter(model, payload):
                        self.fail("unsupported model reached Apply")
                for key, value in model.model.diffusion_model.state_dict().items():
                    self.assertTrue(torch.equal(value, state[key]))

    def test_options_added_after_construction_rejected_before_apply(self):
        for key, value in (("registered_hooks", [object()]),
                           ("model_function_wrapper", object()), ("sampler_cfg_function", object()),
                           ("sampler_post_cfg_function", [object()]),
                           ("sampler_pre_cfg_function", [object()]),
                           ("sampler_calc_cond_batch_function", object())):
            with self.subTest(key=key), comfy_contract(), patch.object(bridge, "resolve_apply") as resolve:
                model, payload = Model(), adapter()
                operation = bridge.IPAdapterSample(payload, torch.zeros(1, 4, 4, 3), {})
                with self.assertRaises(RuntimeError):
                    operation(lambda *args: self.fail("sampler invoked"), SimpleNamespace(model_patcher=model),
                              torch.ones(2), {"model_options": {key: value}}, None, torch.zeros(1, 4, 2, 2))
                resolve.assert_not_called()

    def test_sampling_rejects_batch_lowvram_and_offloaded_weights(self):
        for mode in ("batch", "lowvram", "offloaded", "multigpu"):
            with self.subTest(mode=mode), comfy_contract(), patch.object(bridge, "resolve_apply") as resolve:
                model, payload = Model(), adapter()
                if mode == "lowvram":
                    model.model.model_lowvram = True
                if mode == "offloaded":
                    model.load_device = torch.device("cuda", 0)
                if mode == "multigpu":
                    model.additional_models["multigpu"] = [object()]
                operation = bridge.IPAdapterSample(payload, torch.zeros(1, 4, 4, 3), {})
                with self.assertRaises(RuntimeError):
                    operation(lambda *args: self.fail("sampler invoked"), SimpleNamespace(model_patcher=model),
                              torch.ones(2), {"model_options": {}}, None, torch.zeros(2 if mode == "batch" else 1, 4, 2, 2))
                resolve.assert_not_called()

    def test_stage_rejects_backend_spectrum_compile_dynamic_cpu_and_multigpu(self):
        for mode in ("backend", "spectrum", "compile", "dynamic", "cpu", "other_gpu", "multigpu"):
            with self.subTest(mode=mode), comfy_contract(), patch("torch.cuda.current_device", return_value=0):
                model = Model()
                model.load_device = torch.device("cuda", 0)
                settings = {"sampler": {"backend": "comfy_ksampler"}}
                if mode == "backend":
                    settings["sampler"]["backend"] = "other"
                elif mode == "spectrum":
                    settings["sampler"]["spectrum"] = {"enabled": True}
                elif mode == "compile":
                    settings["model_patches"] = {"kj": {"torch_compile": {"enabled": True}}}
                elif mode == "dynamic":
                    model.dynamic = True
                elif mode == "cpu":
                    model.load_device = torch.device("cpu")
                elif mode == "other_gpu":
                    model.load_device = torch.device("cuda", 1)
                else:
                    model.additional_models["multigpu"] = [object()]
                event = SimpleNamespace(state=SimpleNamespace(model=model), request=SimpleNamespace(settings=settings))
                with self.assertRaises(RuntimeError):
                    self.build().create_session(None).before_stage(event)
                self.assertEqual(model.model_options, {"transformer_options": {}})


if __name__ == "__main__":
    unittest.main()
