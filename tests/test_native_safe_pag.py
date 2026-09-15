from __future__ import annotations

import copy
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch

from easyuse_anima.aio import model_preparation, safe_pag
from easyuse_anima.nodes.safe_pag_nodes import EasyAnimaSafePAG
from easyuse_anima.registration import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS


class Attention(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.n_heads = 2
        self.output_proj = torch.nn.Identity()

    def compute_attention(self, q, k, v, transformer_options=None):
        return safe_pag._project_attention(self, safe_pag._sdpa_attention(q, k, v))


class Model:
    def __init__(self, count=28):
        self.blocks = [SimpleNamespace(self_attn=Attention()) for _ in range(count)]
        self.model_options = {}

    def clone(self):
        result = copy.copy(self)
        result.model_options = {
            k: list(v) if isinstance(v, list) else v
            for k, v in self.model_options.items()
        }
        return result

    def get_model_object(self, name):
        if name == "diffusion_model":
            return SimpleNamespace(blocks=self.blocks)
        return SimpleNamespace(percent_to_sigma=lambda percent: 1 - percent)

    def set_model_sampler_calc_cond_batch_function(self, callback):
        self.model_options["sampler_calc_cond_batch_function"] = callback

    def set_model_sampler_post_cfg_function(self, callback):
        self.model_options.setdefault("sampler_post_cfg_function", []).append(callback)


def tensors(batch=1):
    values = torch.arange(batch * 3 * 2 * 2, dtype=torch.float32).reshape(
        batch, 3, 2, 2
    )
    return values.sin(), (values * 0.7).cos(), (values * 0.3).sin()


def calculate(args):
    count = len(args["conds"])
    q, k, v = tensors(count)

    def forward(_input, _sigma, transformer_options):
        return (
            args["model"]
            .blocks[18]
            .self_attn.compute_attention(q, k, v, transformer_options)
        )

    output = args["model_options"]["model_function_wrapper"](
        forward,
        {
            "input": args["input"],
            "timestep": args["sigma"],
            "c": {"transformer_options": {}},
            "cond_or_uncond": list(range(count)),
        },
    )
    return list(output.split(1))


def run_calc(model, sigma=0.6):
    return model.model_options["sampler_calc_cond_batch_function"](
        {
            "model": model,
            "conds": [{}, {}],
            "input": torch.zeros(1),
            "sigma": sigma,
            "model_options": model.model_options,
        }
    )


def run_post(model, outputs, sigma=0.6):
    value = outputs[0] * 1.2
    for callback in model.model_options["sampler_post_cfg_function"]:
        value = callback(
            {"denoised": value, "cond_denoised": outputs[0], "sigma": sigma}
        )
    return value


class NativeSafePAGTests(unittest.TestCase):
    def test_frozen_upstream_attention_and_rescale_parity(self):
        fixture = json.loads(
            (Path(__file__).parent / "fixtures/native_safe_pag_parity.json").read_text()
        )
        self.assertEqual(
            fixture["upstream"], "905b0107d1f924fc6acbcac3b6a879b566ff671c"
        )
        q, k, v = tensors()
        for case in fixture["attention"]:
            actual = safe_pag._soft_pag_attention(
                Attention(), q, k, v, case["strength"], case["heads"]
            )
            torch.testing.assert_close(
                actual, torch.tensor(case["output"]), rtol=1e-6, atol=1e-7
            )
        for case in fixture["rescale"]:
            cond = v.reshape(1, 3, 4)
            guidance = (cond - q.reshape(1, 3, 4)) * 0.4
            actual = safe_pag._rescale_guidance(
                guidance, cond, cond * 1.2, case["amount"], case["mode"]
            )
            torch.testing.assert_close(
                actual, torch.tensor(case["output"]), rtol=1e-6, atol=1e-7
            )

    def test_restoration_success_failure_interrupt_partial_setup_and_shared_blocks(
        self,
    ):
        for error in (None, RuntimeError, KeyboardInterrupt):
            for count in (28, 40):
                with self.subTest(error=error, count=count):
                    model = Model(count)
                    attention = model.blocks[18].self_attn
                    original = attention.compute_attention
                    attention.compute_attention = original
                    model.blocks[19].self_attn = attention
                    token = object()
                    try:
                        with safe_pag._patch_anima_attention(
                            model.blocks, [18, 19], 2, 0.75, "", token
                        ):
                            self.assertIsNot(attention.compute_attention, original)
                            if error:
                                raise error("interrupt")
                    except (RuntimeError, KeyboardInterrupt):
                        pass
                    self.assertIs(attention.compute_attention, original)
        model = Model()
        model.blocks[19] = object()
        original = model.blocks[18].self_attn.compute_attention
        with self.assertRaisesRegex(RuntimeError, "Block 19"):
            with safe_pag._patch_anima_attention(
                model.blocks, [18, 19], 2, 0.75, "", object()
            ):
                self.fail("invalid block accepted")
        self.assertNotIn("compute_attention", vars(model.blocks[18].self_attn))
        self.assertEqual(model.blocks[18].self_attn.compute_attention, original)

    def test_concurrent_sibling_without_owner_token_uses_original_attention(self):
        model = Model()
        attention = model.blocks[18].self_attn
        q, k, v = tensors()
        expected = attention.compute_attention(q, k, v)
        token = object()
        with safe_pag._patch_anima_attention(model.blocks, [18], 0, 0.75, "", token):
            with ThreadPoolExecutor(max_workers=1) as executor:
                actual = executor.submit(
                    attention.compute_attention, q, k, v, {"cond_or_uncond": [0]}
                ).result(5)
            self.assertTrue(torch.equal(actual, expected))
            perturbed = attention.compute_attention(
                q,
                k,
                v,
                {
                    "cond_or_uncond": [0],
                    "easyuse_anima_safe_pag_token": token,
                },
            )
            self.assertFalse(torch.equal(perturbed, expected))

    def test_engine_preserves_callbacks_and_reapplication_does_not_stack(self):
        base = Model()
        calc_calls = []

        def previous_calc(args):
            calc_calls.append(len(args["conds"]))
            return calculate(args)

        def previous_post(args):
            return args["denoised"] + 0.1

        base.model_options = {
            "sampler_calc_cond_batch_function": previous_calc,
            "sampler_post_cfg_function": [previous_post],
        }
        first = EasyAnimaSafePAG().patch(base)[0]
        second = EasyAnimaSafePAG().patch(first)[0]
        self.assertEqual(len(second.model_options["sampler_post_cfg_function"]), 2)
        self.assertIs(
            second.model_options["sampler_post_cfg_function"][0], previous_post
        )
        self.assertEqual(
            base.model_options["sampler_post_cfg_function"], [previous_post]
        )
        outputs = run_calc(second)
        self.assertEqual(calc_calls, [3])
        value = run_post(second, outputs)
        self.assertTrue(torch.isfinite(value).all())
        self.assertNotIn("compute_attention", vars(base.blocks[18].self_attn))

    def test_active_and_inactive_padding_and_interrupted_calc_clear_prediction(self):
        model = EasyAnimaSafePAG().patch(Model())[0]
        with patch.object(
            safe_pag, "_calculate_condition_batch", side_effect=calculate
        ) as calc:
            active = run_calc(model)
            self.assertEqual(len(calc.call_args.args[0]["conds"]), 3)
            run_post(model, active)
            inactive = run_calc(model, sigma=0.1)
            self.assertEqual(len(calc.call_args.args[0]["conds"]), 3)
            self.assertTrue(
                torch.equal(run_post(model, inactive, sigma=0.1), inactive[0] * 1.2)
            )
        with patch.object(
            safe_pag, "_calculate_condition_batch", side_effect=KeyboardInterrupt
        ):
            with self.assertRaises(KeyboardInterrupt):
                run_calc(model)
        self.assertNotIn("compute_attention", vars(model.blocks[18].self_attn))
        self.assertTrue(torch.equal(run_post(model, active), active[0] * 1.2))

    def test_prediction_is_isolated_between_execution_contexts(self):
        model = EasyAnimaSafePAG().patch(Model())[0]
        one, two = copy_context(), copy_context()
        with patch.object(
            safe_pag, "_calculate_condition_batch", side_effect=calculate
        ):
            outputs = one.run(run_calc, model)
            two.run(run_calc, model, 0.1)
        guided = one.run(run_post, model, outputs)
        empty = two.run(run_post, model, outputs)
        self.assertFalse(torch.equal(guided, empty))
        self.assertTrue(torch.equal(empty, outputs[0] * 1.2))

    def test_rebuilt_model_uses_live_attention_with_copied_callbacks(self):
        original = EasyAnimaSafePAG().patch(Model())[0]
        rebuilt = Model()
        rebuilt.model_options = original.model_options.copy()
        with patch.object(safe_pag, "_calculate_condition_batch", side_effect=calculate):
            expected = run_post(original, run_calc(original))
            actual = run_post(rebuilt, run_calc(rebuilt))
        self.assertTrue(torch.equal(actual, expected))
        self.assertNotIn("compute_attention", vars(original.blocks[18].self_attn))
        self.assertNotIn("compute_attention", vars(rebuilt.blocks[18].self_attn))
        self.assertIs(
            safe_pag._get_anima_blocks(SimpleNamespace(diffusion_model=SimpleNamespace(blocks=rebuilt.blocks))),
            rebuilt.blocks,
        )

    def test_standalone_identity_names_and_aio_use_internal_engine(self):
        self.assertIs(NODE_CLASS_MAPPINGS["EasyAnimaSafePAG"], EasyAnimaSafePAG)
        self.assertEqual(
            NODE_DISPLAY_NAME_MAPPINGS["EasyAnimaSafePAG"], "Easy Anima Safe PAG"
        )
        self.assertNotIn("AnimaSafePAG", NODE_CLASS_MAPPINGS)
        base = Model()
        self.assertIs(EasyAnimaSafePAG().patch(base, scale=0)[0], base)
        self.assertIsNot(model_preparation._apply_aio_safe_pag_patch(base, {}), base)
        self.assertEqual(base.model_options, {})

    def test_unsupported_model_or_indices_fail_before_shared_mutation(self):
        model = Model()
        for kwargs in ({"block_indices": "99"}, {"head_indices": "99"}):
            with self.subTest(kwargs=kwargs):
                if "block_indices" in kwargs:
                    with self.assertRaises(RuntimeError):
                        EasyAnimaSafePAG().patch(model, **kwargs)
                else:
                    variant = EasyAnimaSafePAG().patch(model, **kwargs)[0]
                    with self.assertRaises(RuntimeError):
                        run_calc(variant)
                self.assertNotIn("compute_attention", vars(model.blocks[18].self_attn))


if __name__ == "__main__":
    unittest.main()
