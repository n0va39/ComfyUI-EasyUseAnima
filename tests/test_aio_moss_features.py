from __future__ import annotations

import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from easyuse_anima.aio import generation_normalization, legacy_generation, moss_features


LAYOUT = json.dumps({
    "summary": {"caption": 'A sign says "hello, world" and <lora:literal:1>.'},
    "items": [{"label": "text", "caption": "Top line", "text": "hello, world",
               "bbox": [-400, -300, -250, 300]}],
    "bbox_format": "yxyx", "bbox_coord_space": "abs_centralized",
    "future_metadata": {"keep": True},
}, indent=2, ensure_ascii=False)


def settings(**bank):
    return {"model_family": "moss_image", "model_settings": {"moss_image": bank},
            "negpip": {"mode": "off"}, "artist_mix": {"mode": "off"}}


class TextGenerate:
    calls = []

    @classmethod
    def execute(cls, clip, prompt, max_length, sampling_mode, thinking=False,
                use_default_template=True, system_prompt=""):
        cls.calls.append(dict(clip=clip, prompt=prompt, max_length=max_length,
                              sampling_mode=sampling_mode, thinking=thinking,
                              use_default_template=use_default_template, system_prompt=system_prompt))
        return ('An illustration with the exact words "hello, world".', "")


class MOSSFeatureTests(unittest.TestCase):
    def test_defaults_copy_unknown_fields_and_preserve_inactive_values(self):
        source = {"future": {"x": [1]}, "prompt": {"mode": "original", "seed": "future-seed"}}
        result = moss_features.normalize_moss_settings(source)
        self.assertEqual(result["slg"]["layers"], "22")
        self.assertEqual(result["prompt"]["seed"], "future-seed")
        result["future"]["x"].append(2)
        self.assertEqual(source["future"]["x"], [1])
        result["slg"]["stage_scope"]["highres"] = False
        self.assertTrue(moss_features.normalize_moss_settings({})["slg"]["stage_scope"]["highres"])
        with self.assertRaisesRegex(ValueError, "object"):
            moss_features.normalize_moss_settings([])

    def test_active_values_validate_without_silently_clamping(self):
        for bank, message in (
            ({"slg": {"mode": "uncond", "layers": "-1"}}, "indices"),
            ({"slg": {"mode": "standard", "start_percent": .8, "end_percent": .2}}, "start_percent"),
            ({"prompt": {"mode": "enhance", "max_length": 32769}}, "max_length"),
            ({"prompt": {"mode": "enhance", "temperature": float("nan")}}, "temperature"),
        ):
            with self.subTest(bank=bank), self.assertRaisesRegex(ValueError, message):
                moss_features.normalize_moss_settings(bank)

    def test_stage_scope_and_inactive_family_do_not_apply_moss_settings(self):
        payload = settings(slg={"mode": "uncond", "stage_scope": {"highres": False}})
        self.assertEqual(moss_features.moss_slg_settings(payload, "first_pass")["layers"], "22")
        self.assertIsNone(moss_features.moss_slg_settings(payload, "highres"))
        self.assertIsNone(moss_features.moss_slg_settings({**payload, "model_family": "anima"}, "first_pass"))

    def test_slg_delegates_single_stream_layer_and_preserves_model(self):
        calls = []
        patched = object()

        class SimpleSLG:
            @classmethod
            def execute(cls, model, start_percent, end_percent, double_layers="", single_layers=""):
                calls.append((model, start_percent, end_percent, double_layers, single_layers))
                return (patched,)

        class StandardSLG:
            @classmethod
            def execute(cls, model, scale, start_percent, end_percent, double_layers="", single_layers="", rescaling_scale=0):
                calls.append((model, scale, start_percent, end_percent, double_layers, single_layers, rescaling_scale))
                return (patched,)

        model = SimpleNamespace(get_model_object=lambda _: SimpleNamespace(layers=[None] * 42))
        for mode, cls in (("uncond", SimpleSLG), ("standard", StandardSLG)):
            selected = moss_features.moss_slg_settings(settings(slg={"mode": mode}), "first_pass")
            lookup = Mock(return_value=cls)
            self.assertIs(moss_features.apply_moss_slg(model, selected, lookup), patched)
            lookup.assert_called_once_with("SkipLayerGuidanceDiTSimple" if mode == "uncond" else "SkipLayerGuidanceDiT")
        self.assertEqual(calls[0], (model, 0.0, 1.0, "", "22"))
        self.assertEqual(calls[1], (model, 3.0, 0.0, 1.0, "", "22", 0.0))
        selected["layers"] = "42"
        with self.assertRaisesRegex(ValueError, "layer count"):
            moss_features.apply_moss_slg(model, selected, lambda _: StandardSLG)
        self.assertIs(moss_features.apply_moss_slg(model, None), model)

    def test_missing_and_drifted_nodes_do_not_report_support(self):
        self.assertEqual(moss_features.moss_feature_provider("prompt_enhance", node_lookup=lambda _: None), (None, "missing_dependency"))
        self.assertEqual(moss_features.moss_feature_provider("slg", node_lookup=lambda _: object), (None, "incompatible"))
        with self.assertRaisesRegex(RuntimeError, "missing_dependency"):
            moss_features.prepare_moss_prompt(object(), "idea", settings(prompt={"mode": "enhance"}), lambda _: None)

    def test_enhancer_passes_seed_and_actual_caption_without_mutating_source(self):
        payload = settings(prompt={"mode": "enhance", "seed": "18446744073709551615", "max_length": 768})
        original = copy.deepcopy(payload)
        clip = object()
        effective, metadata = moss_features.prepare_moss_prompt(clip, "hello, world", payload, lambda _: TextGenerate)
        self.assertEqual(metadata["source_prompt"], "hello, world")
        self.assertEqual(metadata["used_prompt"], effective)
        self.assertEqual(TextGenerate.calls[-1]["sampling_mode"]["seed"], 0xffffffffffffffff)
        self.assertEqual(TextGenerate.calls[-1]["max_length"], 768)
        self.assertIs(TextGenerate.calls[-1]["clip"], clip)
        self.assertFalse(TextGenerate.calls[-1]["thinking"])
        self.assertEqual(payload, original)

    def test_layout_and_original_raw_json_are_byte_preserved(self):
        for prompt, bank in (
            ("ignored", {"mode": "layout", "layout_json": LAYOUT}),
            (LAYOUT, {"mode": "layout", "layout_json": ""}),
            (LAYOUT, {"mode": "original"}),
        ):
            effective, metadata = moss_features.prepare_moss_prompt(None, prompt, settings(prompt=bank), Mock(side_effect=AssertionError("no node needed")))
            self.assertEqual(effective, LAYOUT)
            self.assertEqual(metadata["mode"], "layout")
        self.assertEqual(moss_features.prepare_moss_prompt(None, "natural caption", settings()), ("natural caption", None))

    def test_layout_invalid_coordinates_and_conflicting_transforms_explain_failure(self):
        malformed = json.loads(LAYOUT)
        malformed["items"][0]["bbox"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            moss_features.prepare_moss_prompt(None, json.dumps(malformed), settings(prompt={"mode": "layout"}))
        for payload, message in (
            ({**settings(), "negpip": {"mode": "turbo"}}, "NegPip"),
            ({**settings(), "artist_mix": {"mode": "sequential"}}, "Artist Mix"),
            (settings(prompt={"mode": "enhance"}), "rewrite the layout"),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                moss_features.validate_moss_prompt(LAYOUT, payload)

    def test_layout_validation_precedes_resource_loading(self):
        payload = generation_normalization._normalize_aio_generation_settings(settings(prompt={"mode": "layout", "layout_json": "invalid"}))
        with patch.object(legacy_generation, "_load_aio_resources_from_input_context") as load:
            with self.assertRaisesRegex(ValueError, "MOSS Layout"):
                legacy_generation._run_aio_generation_pipeline(object(), {
                    "resource_info": {"clip_type": "moss_image"}, "prompt_data": {},
                }, payload)
        load.assert_not_called()

    def test_pipeline_layout_bypasses_tag_joining_and_records_used_prompt(self):
        captured, encode, cache, clip = self._prompt_to_sampling_boundary(LAYOUT)
        self.assertEqual(encode.call_args_list[0].args, (clip, LAYOUT))
        self.assertEqual(cache.call_args.kwargs["positive_prompt"], LAYOUT)
        self.assertEqual(captured["request"].prompts.metadata_positive_prompt, LAYOUT)
        self.assertEqual(captured["request"].prompts.prompt_data["outputs"]["positive_prompt"], LAYOUT)
        self.assertEqual(captured["state"].metadata["moss_prompt"]["used_prompt"], LAYOUT)

    def test_original_caption_preserves_rendered_text_and_newlines(self):
        caption = 'A note says:\n"첫째, hello\n# This is visible text\n둘째, world".'
        captured, encode, cache, clip = self._prompt_to_sampling_boundary(caption)
        self.assertEqual(encode.call_args_list[0].args, (clip, caption))
        self.assertEqual(cache.call_args.kwargs["positive_prompt"], caption)
        self.assertEqual(captured["request"].prompts.positive_prompt, caption)
        self.assertNotIn("moss_prompt", captured["state"].metadata)

    def _prompt_to_sampling_boundary(self, source):
        payload = generation_normalization._normalize_aio_generation_settings(settings())
        context = {"resource_info": {"clip_type": "moss_image"}, "prompt_data": {
            "outputs": {"positive_prompt": source, "negative_prompt": "bad", "width": 512, "height": 512},
        }}
        original = copy.deepcopy(context)
        model, clip, vae = object(), object(), object()
        captured = {}

        class Boundary(Exception):
            pass

        class StopBeforeSampling:
            def __init__(self, _hooks, request, state, *_args):
                captured.update(request=request, state=state)

            def __enter__(self):
                raise Boundary()

            def __exit__(self, *_args):
                return False

        with (
            patch.object(legacy_generation, "validate_aio_model_resources"),
            patch.object(legacy_generation, "_load_aio_resources_from_input_context", return_value=(model, clip, vae)),
            patch.object(legacy_generation, "_apply_aio_lora_stack", return_value=(model, clip, [])),
            patch.object(legacy_generation, "_apply_aio_stage_model_patch_plan", return_value=model),
            patch.object(legacy_generation, "_apply_aio_spectrum_model_patches_for_comfy_sampler", return_value=model),
            patch.object(legacy_generation, "_encode_with_comfy_clip", side_effect=lambda _clip, text: [text]) as encode,
            patch.object(legacy_generation, "_encode_prompt_data_positive_conditioning", side_effect=AssertionError("tag joining must be bypassed")),
            patch.object(legacy_generation, "_aio_first_pass_cache_key", return_value="key") as cache,
            patch.object(legacy_generation, "_cleanup_aio_ephemeral_model"),
            patch.object(legacy_generation, "AioHookRun", StopBeforeSampling),
        ):
            with self.assertRaises(Boundary):
                legacy_generation._run_aio_generation_pipeline(object(), context, payload)
        self.assertEqual(context, original)
        return captured, encode, cache, clip
