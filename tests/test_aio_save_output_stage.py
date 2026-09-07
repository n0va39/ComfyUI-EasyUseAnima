from __future__ import annotations

import copy
import json
import unittest
from dataclasses import replace

from easyuse_anima.aio.generation_normalization import (
    _normalize_aio_generation_settings,
)
from easyuse_anima.aio.generation_pipeline import (
    ConditioningBundle,
    GenerationRequest,
    GenerationStage,
    GenerationState,
    PromptExecutionData,
    ResourceBundle,
    WorkflowContext,
)
from easyuse_anima.aio.generation_save_output_stage import (
    AIOSaveOutputStage,
    SaveOutputRuntime,
)
from easyuse_anima.aio.generation_settings import (
    _aio_generation_config_from_dict,
)


def _request(
    *,
    save_enabled: bool,
    save_backend: str = "comfy_save_image",
    metadata_positive: str = "metadata positive",
    metadata_negative: str = "metadata negative",
) -> GenerationRequest:
    normalized = _normalize_aio_generation_settings(json.dumps({
        "sampler": {
            "backend": "comfy_ksampler",
            "seed": 17,
        },
        "save": {
            "enabled": save_enabled,
            "backend": save_backend,
        },
    }))
    return GenerationRequest(
        config=_aio_generation_config_from_dict(normalized),
        prompts=PromptExecutionData(
            prompt_data={"positive_prompt": "prompt"},
            positive_prompt="positive",
            negative_prompt="negative",
            quality_tags="quality",
            quality_negative="quality-negative",
            metadata_positive_prompt=metadata_positive,
            metadata_negative_prompt=metadata_negative,
            use_anima_mod_guidance=True,
            use_negative_anima_mod_guidance=True,
        ),
        resources=ResourceBundle(
            base_model="base-model",
            base_clip="base-clip",
            model_with_lora="lora-model",
            model="model",
            clip="clip",
            vae="vae",
            applied_loras=({"name": "style.safetensors"},),
        ),
        conditioning=ConditioningBundle(
            positive="positive-conditioning",
            negative="negative-conditioning",
        ),
        workflow=WorkflowContext(
            input_context={
                "resource_info": {"unet_name": "model.safetensors"},
                "input_settings": {"schema": "input-settings"},
            },
            lora_stack=(),
            workflow_prompt={"workflow": True},
            extra_pnginfo={"pnginfo": True},
            unique_id="node-7",
            cache_scope="node-7",
        ),
    )


def _state(
    *,
    previews: list[dict[str, object]] | None = None,
) -> GenerationState:
    return GenerationState(
        latent="final-latent",
        image="final-image",
        width=96,
        height=144,
        metadata={
            "first_pass": {"cache_hit": False},
            "postprocess": {"enabled": True},
        },
        previews=list(previews or []),
    )


def _runtime(**overrides) -> SaveOutputRuntime:
    helpers = {
        "save_comfy": lambda *_args, **_kwargs: {},
        "save_image_saver": lambda *_args, **_kwargs: {},
        "filename_prefix": lambda _settings: "EasyUseAnima/AiO",
        "tag_images": lambda images, stage, **_kwargs: [
            {**item, "stage": stage}
            for item in images
        ],
        "save_temp_preview": lambda *_args, **_kwargs: [
            {"filename": "final-temp.png", "stage": "final", "type": "temp"}
        ],
        "json_safe": lambda value: value,
        **overrides,
    }
    return SaveOutputRuntime(**helpers)


class AIOSaveOutputStageTests(unittest.TestCase):
    def test_disabled_save_uses_temp_final_preview_and_builds_output(self):
        trace: list[str] = []

        def unexpected(*_args, **_kwargs):
            self.fail("disabled Save must not invoke a save backend")

        def tag_images(images, stage, *, width, height):
            trace.append("tag_images")
            self.assertEqual((images, stage, width, height), (
                [],
                "final",
                96,
                144,
            ))
            return []

        def save_temp(image, stage, **kwargs):
            trace.append("save_temp")
            self.assertEqual((image, stage), ("final-image", "final"))
            self.assertEqual(kwargs, {
                "workflow_prompt": {"workflow": True},
                "extra_pnginfo": {"pnginfo": True},
            })
            return [
                {
                    "filename": "final-temp.png",
                    "stage": "final",
                    "type": "temp",
                },
            ]

        stage: GenerationStage = AIOSaveOutputStage(
            runtime=_runtime(
                save_comfy=unexpected,
                save_image_saver=unexpected,
                filename_prefix=unexpected,
                tag_images=tag_images,
                save_temp_preview=save_temp,
            ),
            applied_loras=[],
            preview_run_id="node-7:run",
        )
        state = _state()
        request = _request(save_enabled=False)

        stage.validate(request, {})
        stage.run(request, state)

        self.assertEqual(trace, ["tag_images", "save_temp"])
        output = stage.output
        self.assertIsNotNone(output)
        metadata = json.loads(output["result"][2])
        self.assertEqual(output["result"][:2], (
            "final-image",
            "final-latent",
        ))
        self.assertEqual(metadata["width"], 96)
        self.assertEqual(metadata["height"], 144)
        self.assertEqual(metadata["resource_info"]["unet_name"], "model.safetensors")
        self.assertEqual(
            list(metadata["stages"]),
            ["first_pass", "postprocess"],
        )
        self.assertNotIn("extensions", metadata)
        self.assertEqual(output["ui"]["status"], ["generated"])
        self.assertEqual(output["ui"]["width"], [96])
        self.assertEqual(output["ui"]["height"], [144])
        self.assertEqual(output["ui"]["unet_name"], ["model.safetensors"])
        self.assertEqual(output["ui"]["sampler_backend"], ["comfy_ksampler"])
        self.assertEqual(output["ui"]["easyuse_anima_run_id"], ["node-7:run"])
        self.assertEqual(
            output["ui"]["images"][0]["filename"],
            "final-temp.png",
        )
        self.assertEqual(
            output["ui"]["easyuse_anima_preview"],
            output["ui"]["images"],
        )

    def test_comfy_backend_preserves_prefix_kwargs_and_saved_preview(self):
        trace: list[str] = []

        def filename_prefix(settings):
            trace.append("filename_prefix")
            self.assertTrue(settings["enabled"])
            self.assertEqual(settings["backend"], "comfy_save_image")
            return "Anima/Final"

        def save_comfy(image, prefix, **kwargs):
            trace.append("save_comfy")
            self.assertEqual((image, prefix), ("final-image", "Anima/Final"))
            self.assertEqual(kwargs, {
                "workflow_prompt": {"workflow": True},
                "extra_pnginfo": {"pnginfo": True},
            })
            return {
                "ui": {
                    "images": [
                        {"filename": "saved.png", "type": "output"},
                    ],
                },
            }

        def tag_images(images, stage, *, width, height):
            trace.append("tag_images")
            self.assertEqual((stage, width, height), ("final", 96, 144))
            return [
                {
                    **images[0],
                    "stage": stage,
                    "width": width,
                    "height": height,
                },
            ]

        def unexpected_temp(*_args, **_kwargs):
            self.fail("saved final image must not use temp fallback")

        stage = AIOSaveOutputStage(
            runtime=_runtime(
                save_comfy=save_comfy,
                filename_prefix=filename_prefix,
                tag_images=tag_images,
                save_temp_preview=unexpected_temp,
            ),
            applied_loras=[],
            preview_run_id="node-7:run",
        )
        stage.run(_request(save_enabled=True), _state())

        self.assertEqual(
            trace,
            ["filename_prefix", "save_comfy", "tag_images"],
        )
        self.assertEqual(stage.output["ui"]["images"], [
            {
                "filename": "saved.png",
                "type": "output",
                "stage": "final",
                "width": 96,
                "height": 144,
            },
        ])

    def test_image_saver_preserves_original_lora_list_and_prompt_fallbacks(self):
        applied_loras = [
            {"name": "style.safetensors", "strength_model": 0.8},
        ]
        captured: dict[str, object] = {}

        def save_image_saver(image, settings, **kwargs):
            captured["image"] = image
            captured["settings"] = settings
            captured["kwargs"] = kwargs
            return {
                "ui": {
                    "images": [
                        {"filename": "saved.webp", "type": "output"},
                    ],
                },
            }

        stage = AIOSaveOutputStage(
            runtime=_runtime(save_image_saver=save_image_saver),
            applied_loras=applied_loras,
            preview_run_id="node-7:run",
        )
        stage.run(
            _request(
                save_enabled=True,
                save_backend="image_saver",
                metadata_positive="",
                metadata_negative="",
            ),
            _state(),
        )

        self.assertEqual(captured["image"], "final-image")
        kwargs = captured["kwargs"]
        self.assertEqual(kwargs["positive_prompt"], "positive")
        self.assertEqual(kwargs["negative_prompt"], "negative")
        self.assertEqual((kwargs["width"], kwargs["height"]), (96, 144))
        self.assertEqual(kwargs["sampler_settings"]["seed"], 17)
        self.assertIs(kwargs["applied_loras"], applied_loras)
        self.assertEqual(
            kwargs["resource_info"],
            {"unet_name": "model.safetensors"},
        )
        metadata = json.loads(stage.output["result"][2])
        self.assertEqual(metadata["lora_stack"], applied_loras)

    def test_hook_extension_metadata_is_serialized_without_changing_core_stages(self):
        state = _state()
        state.extensions = {
            "hooks": [{"hook_id": "example.brightness", "ordinal": 0}],
            "hook_data": {"example.brightness#0": {"strength": 0.9}},
        }
        stage = AIOSaveOutputStage(
            runtime=_runtime(),
            applied_loras=[],
            preview_run_id="node-7:run",
        )

        stage.run(_request(save_enabled=False), state)

        metadata = json.loads(stage.output["result"][2])
        self.assertEqual(metadata["extensions"], state.extensions)
        self.assertEqual(
            list(metadata["stages"]),
            ["first_pass", "postprocess"],
        )

    def test_successive_saves_freeze_actual_settings_without_mutating_prompt(self):
        cases = (
            (-1, 101, "randomize", 23, 5.5, "euler", "normal", 1.0, True, 1.5),
            (202, 202, "increment", 37, 7.0, "dpmpp_2m", "karras", 0.75, True, 2.0),
            (303, 303, "fixed", 19, 4.0, "heun", "simple", 0.9, False, 1.25),
        )
        for backend in ("image_saver", "comfy_save_image", "temp"):
            with self.subTest(backend=backend):
                captured = []

                def save(*_args, **kwargs):
                    captured.append(kwargs)
                    return {"ui": {"images": [{"filename": "saved.png", "type": "output"}]}}

                def save_temp(*_args, **kwargs):
                    captured.append(kwargs)
                    return [{"filename": "saved-temp.png", "type": "temp"}]

                prompt = {"7": {"class_type": "EasyUseAnimaAIOGenerator", "inputs": {
                    "easy_use_anima_input": ["source", 0],
                }}}
                extra = {"workflow": {"nodes": [{
                    "id": 7, "type": "EasyUseAnimaAIOGenerator", "widgets_values": [],
                }]}}
                base = _request(save_enabled=backend != "temp", save_backend=backend)
                base = replace(base, workflow=replace(
                    base.workflow, workflow_prompt=prompt, extra_pnginfo=extra, unique_id="7",
                ))
                stage = AIOSaveOutputStage(
                    runtime=_runtime(save_image_saver=save, save_comfy=save, save_temp_preview=save_temp),
                    applied_loras=[], preview_run_id="7:run",
                )
                expected_snapshots = []
                for queued_seed, actual_seed, control, steps, cfg, name, scheduler, denoise, highres, scale in cases:
                    settings = base.config.to_dict()
                    settings["sampler"].update({
                        "seed": queued_seed, "seed_after_generate": control,
                        "steps": steps, "cfg": cfg, "sampler_name": name,
                        "scheduler": scheduler, "denoise": denoise,
                    })
                    settings["highres"].update({
                        "enabled": highres, "scale_by": scale, "steps": steps + 2,
                        "inherit_sampler_settings": False, "cfg": cfg + 1,
                        "sampler_name": name, "scheduler": scheduler, "denoise": 0.25,
                    })
                    prompt["7"]["inputs"]["generation_settings"] = json.dumps(settings)
                    extra["workflow"]["nodes"][0]["widgets_values"] = [json.dumps(settings)]
                    original_prompt = copy.deepcopy(prompt)
                    settings["sampler"]["seed"] = actual_seed
                    request = replace(base, config=_aio_generation_config_from_dict(settings))
                    state = _state()
                    actual_sampler = {**request.config.sampler.to_dict(), "cfg": 1.0, "sampler_name": "euler"}
                    state.metadata["first_pass"]["sampler"] = actual_sampler
                    state.metadata["highres"] = {"enabled": highres, "sampler": {"steps": steps + 2}}
                    stage.run(request, state)

                    saved = captured[-1]
                    saved_settings = json.loads(saved["workflow_prompt"]["7"]["inputs"]["generation_settings"])
                    expected_settings = request.config.to_dict()
                    expected_settings["sampler"]["seed_after_generate"] = "fixed"
                    self.assertEqual(saved_settings, expected_settings)
                    workflow = saved["extra_pnginfo"]["workflow"]
                    self.assertEqual(json.loads(workflow["nodes"][0]["widgets_values"][0]), saved_settings)
                    replay = _normalize_aio_generation_settings(workflow["nodes"][0]["widgets_values"][0])
                    self.assertEqual((replay["sampler"]["seed"], replay["sampler"]["seed_after_generate"]), (actual_seed, "fixed"))
                    record = workflow["extra"]["easyuse_anima_executions"]["7"]
                    self.assertEqual(record["execution"]["stages"], state.metadata)
                    if backend == "image_saver":
                        self.assertEqual(saved["sampler_settings"], actual_sampler)
                    self.assertEqual(prompt, original_prompt)
                    self.assertIsNot(saved["workflow_prompt"], prompt)
                    self.assertIsNot(saved["extra_pnginfo"], extra)
                    expected_snapshots.append(copy.deepcopy(saved))
                    self.assertEqual(captured, expected_snapshots)
                self.assertEqual(len(captured), len(cases))

    def test_invalid_save_ui_falls_back_and_reconciles_last_detailer_preview(self):
        previews = [
            {"filename": "first.png", "stage": "first_pass"},
            {"filename": "eye.png", "stage": "detailer_eye"},
        ]
        stage = AIOSaveOutputStage(
            runtime=_runtime(
                save_comfy=lambda *_args, **_kwargs: {"ui": "invalid"},
                tag_images=lambda *_args, **_kwargs: [],
                save_temp_preview=lambda *_args, **_kwargs: [
                    {"filename": "final-a.png", "stage": "final"},
                    {"filename": "final-b.png", "stage": "final"},
                ],
            ),
            applied_loras=[],
            preview_run_id="node-7:run",
        )
        state = _state(previews=previews)
        stage.run(_request(save_enabled=True), state)

        self.assertEqual(state.previews, [
            {"filename": "first.png", "stage": "first_pass"},
            {"filename": "final-a.png", "stage": "final"},
        ])
        self.assertEqual(stage.output["ui"]["images"], [
            {"filename": "final-b.png", "stage": "final"},
        ])
        self.assertEqual(
            stage.output["ui"]["easyuse_anima_preview"],
            [
                {"filename": "first.png", "stage": "first_pass"},
                {"filename": "final-a.png", "stage": "final"},
                {"filename": "final-b.png", "stage": "final"},
            ],
        )

    def test_validation_and_helper_or_serialization_failures_propagate(self):
        request = _request(save_enabled=True)
        invalid_request = replace(
            request,
            config=replace(request.config, mode="img2img"),
        )
        stage = AIOSaveOutputStage(
            runtime=_runtime(
                save_comfy=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    RuntimeError("save failed")
                ),
            ),
            applied_loras=[],
            preview_run_id="node-7:run",
        )

        with self.assertRaisesRegex(RuntimeError, "supports txt2img only"):
            stage.validate(invalid_request, {})
        with self.assertRaisesRegex(RuntimeError, "save failed"):
            stage.run(request, _state())
        self.assertIsNone(stage.output)

        stage = AIOSaveOutputStage(
            runtime=_runtime(
                save_comfy=lambda *_args, **_kwargs: {
                    "ui": {"images": [{"filename": "saved.png"}]},
                },
                json_safe=lambda _value: (_ for _ in ()).throw(
                    RuntimeError("serialize failed")
                ),
            ),
            applied_loras=[],
            preview_run_id="node-7:run",
        )
        with self.assertRaisesRegex(RuntimeError, "serialize failed"):
            stage.run(request, _state())
        self.assertIsNone(stage.output)


if __name__ == "__main__":
    unittest.main()
