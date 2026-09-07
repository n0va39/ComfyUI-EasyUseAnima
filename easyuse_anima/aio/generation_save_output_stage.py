# pyright: strict
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, TypeAlias, cast

from .execution_metadata import snapshot_aio_execution_metadata
from .generation_pipeline import (
    GenerationCapabilities,
    GenerationRequest,
    GenerationState,
)

OutputHelper: TypeAlias = Callable[..., object]
FilenamePrefix: TypeAlias = Callable[[dict[str, Any]], str]
JsonSafe: TypeAlias = Callable[[object], object]


@dataclass(frozen=True, slots=True)
class SaveOutputRuntime:
    save_comfy: OutputHelper
    save_image_saver: OutputHelper
    filename_prefix: FilenamePrefix
    tag_images: OutputHelper
    save_temp_preview: OutputHelper
    json_safe: JsonSafe


@dataclass(slots=True)
class AIOSaveOutputStage:
    runtime: SaveOutputRuntime
    applied_loras: object
    preview_run_id: str
    output: dict[str, Any] | None = field(init=False, default=None)

    name: ClassVar[str] = "save_output"

    def validate(
        self,
        request: GenerationRequest,
        capabilities: GenerationCapabilities,
    ) -> None:
        del capabilities
        if request.config.mode != "txt2img":
            raise RuntimeError(
                "[EasyUseAnima] AiO Generator draft currently supports txt2img only."
            )

    def run(
        self,
        request: GenerationRequest,
        state: GenerationState,
    ) -> None:
        save_settings = cast(
            dict[str, Any],
            request.config.save.to_dict(),
        )
        first_pass = cast(dict[str, Any], state.metadata.get("first_pass", {}))
        sampler = cast(
            dict[str, Any],
            first_pass.get(
                "sampler", request.config.sampler.to_dict()
            ),
        )
        generation_settings = cast(
            dict[str, Any],
            request.config.to_dict(),
        )
        context = cast(
            dict[str, Any],
            request.workflow.input_context,
        )
        resource_info = cast(
            dict[str, Any],
            context.get("resource_info", {}),
        )
        metadata = {
            "schema": "easyuse_anima_aio_generation_result",
            "version": 1,
            "width": int(state.width),
            "height": int(state.height),
            "resource_info": self.runtime.json_safe(resource_info),
            "input_settings": self.runtime.json_safe(context.get("input_settings", {})),
            "lora_stack": self.runtime.json_safe(self.applied_loras),
            "generation_settings": self.runtime.json_safe(generation_settings),
            "stages": self.runtime.json_safe(state.metadata),
            "prompt_data": self.runtime.json_safe(request.prompts.prompt_data),
        }
        if state.extensions:
            metadata["extensions"] = self.runtime.json_safe(state.extensions)
        workflow_prompt, extra_pnginfo = snapshot_aio_execution_metadata(
            request.workflow.workflow_prompt,
            request.workflow.extra_pnginfo,
            request.workflow.unique_id,
            generation_settings,
            metadata,
        )
        save_ui: dict[str, Any] = {}
        if save_settings.get("enabled"):
            if save_settings.get("backend") == "image_saver":
                positive_prompt = (
                    request.prompts.metadata_positive_prompt
                    or request.prompts.positive_prompt
                )
                negative_prompt = (
                    request.prompts.metadata_negative_prompt
                    or request.prompts.negative_prompt
                )
                save_result = self.runtime.save_image_saver(
                    state.image,
                    save_settings,
                    positive_prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    width=state.width,
                    height=state.height,
                    sampler_settings=sampler,
                    applied_loras=self.applied_loras,
                    resource_info=resource_info,
                    workflow_prompt=workflow_prompt,
                    extra_pnginfo=extra_pnginfo,
                )
            else:
                save_result = self.runtime.save_comfy(
                    state.image,
                    self.runtime.filename_prefix(save_settings),
                    workflow_prompt=workflow_prompt,
                    extra_pnginfo=extra_pnginfo,
                )
            if isinstance(save_result, dict):
                save_result_dict = cast(
                    dict[str, object],
                    save_result,
                )
                if isinstance(save_result_dict.get("ui"), dict):
                    save_ui = cast(
                        dict[str, Any],
                        save_result_dict["ui"],
                    )
        final_preview = cast(
            list[dict[str, Any]],
            self.runtime.tag_images(
                save_ui.get("images", []),
                "final",
                width=state.width,
                height=state.height,
            ),
        )
        if not final_preview:
            preview_embeds_workflow = (
                save_settings.get("backend") != "image_saver"
                or save_settings.get("image_saver", {}).get("embed_workflow", True)
            )
            final_preview = cast(
                list[dict[str, Any]],
                self.runtime.save_temp_preview(
                    state.image,
                    "final",
                    workflow_prompt=workflow_prompt if preview_embeds_workflow else None,
                    extra_pnginfo=extra_pnginfo if preview_embeds_workflow else None,
                ),
            )
        if (
            final_preview
            and state.previews
            and str(state.previews[-1].get("stage") or "").startswith(
                "detailer_"
            )
        ):
            state.previews[-1] = final_preview[0]
            final_preview = final_preview[1:]
        metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
        ui: dict[str, Any] = {
            "status": ["generated"],
            "width": [int(state.width)],
            "height": [int(state.height)],
            "unet_name": [str(resource_info.get("unet_name", ""))],
            "sampler_backend": [
                str(sampler.get("backend") or "comfy_ksampler")
            ],
            "easyuse_anima_run_id": [self.preview_run_id],
        }
        preview_payload = state.previews + final_preview
        if final_preview:
            ui["images"] = final_preview
        if preview_payload:
            ui["easyuse_anima_preview"] = preview_payload
        self.output = {
            "ui": ui,
            "result": (state.image, state.latent, metadata_json),
        }


__all__ = ()
