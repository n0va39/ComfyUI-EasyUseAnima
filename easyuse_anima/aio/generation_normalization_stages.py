from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from ..image.scaling import IMAGE_SCALE_MULTIPLES, IMAGE_UPSCALE_METHODS
from .generation_defaults import (
    AIO_FINAL_FIT_MODES,
    AIO_FINAL_UPSCALE_BACKENDS,
    AIO_GENERATION_DEFAULT_SETTINGS,
    AIO_RESHIFT_DTYPES,
    AIO_RESHIFT_SCALES,
    AIO_SAMPLER_CFG_MAX,
    AIO_SAMPLER_CFG_MIN,
    AIO_SAMPLER_STEPS_MAX,
    AIO_SAMPLER_STEPS_MIN,
    AIO_USDU_MODE_TYPES,
    AIO_USDU_PROMPT_MODES,
    AIO_USDU_PROMPT_NO_GENERAL,
    AIO_USDU_SEAM_FIX_MODES,
)

ValueHelper = Callable[..., Any]

AIO_DETAILER_RESERVED_KEYS = {"enabled", "order", "sam3"}
AIO_DETAILER_CUSTOM_RE = re.compile(r"^custom_\d+$")


def is_aio_detailer_target_name(
    name: str,
    *,
    custom_re,
) -> bool:
    return name in ("face", "eye") or bool(custom_re.fullmatch(name))


def aio_detailer_target_defaults(
    target_name: str,
    *,
    default_settings: dict[str, Any],
    json_clone: ValueHelper,
) -> dict[str, Any]:
    if target_name == "eye":
        return json_clone(default_settings["detailer"]["eye"])
    defaults = json_clone(default_settings["detailer"]["face"])
    if target_name not in ("face", "eye"):
        suffix = target_name.rsplit("_", 1)[-1]
        defaults["label"] = (
            f"Detailer Block {suffix}" if suffix.isdigit() else "Detailer Block"
        )
    return defaults


def aio_detailer_target_order(
    detailer_settings: dict[str, Any],
    *,
    is_target_name: ValueHelper,
    reserved_keys: set[str],
) -> list[str]:
    output: list[str] = []

    def append_target(name) -> None:
        text = str(name or "").strip()
        if is_target_name(text) and text not in output:
            output.append(text)

    order = detailer_settings.get("order")
    if isinstance(order, list):
        for name in order:
            append_target(name)
    for name, value in detailer_settings.items():
        if name in reserved_keys or not isinstance(value, dict):
            continue
        append_target(name)
    for name in ("face", "eye"):
        append_target(name)
    return output


def aio_detailer_has_enabled_targets(
    detailer_settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    target_order: ValueHelper,
) -> bool:
    if not as_bool(detailer_settings.get("enabled"), False):
        return False
    return any(
        isinstance(detailer_settings.get(name), dict)
        and as_bool(detailer_settings[name].get("enabled"), False)
        for name in target_order(detailer_settings)
    )


def _normalize_highres_settings(
    settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
    sampler_names: ValueHelper,
    scheduler_names: ValueHelper,
    normalize_spectrum: ValueHelper,
    normalize_corrections: ValueHelper,
) -> None:
    highres = settings["highres"]
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["highres"]
    highres["scale_by"] = max(0.01, min(8.0, as_float(highres.get("scale_by"), defaults["scale_by"])))
    highres["upscale_method"] = choice(highres.get("upscale_method"), IMAGE_UPSCALE_METHODS, defaults["upscale_method"])
    highres["multiple"] = choice(highres.get("multiple"), IMAGE_SCALE_MULTIPLES, defaults["multiple"])
    highres["max_long_edge"] = max(0, min(16384, as_int(highres.get("max_long_edge"), defaults["max_long_edge"])))
    highres["steps"] = max(
        AIO_SAMPLER_STEPS_MIN,
        min(AIO_SAMPLER_STEPS_MAX, as_int(highres.get("steps"), defaults["steps"])),
    )
    highres["inherit_sampler_settings"] = as_bool(highres.get("inherit_sampler_settings"), defaults["inherit_sampler_settings"])
    highres["cfg"] = max(
        AIO_SAMPLER_CFG_MIN,
        min(AIO_SAMPLER_CFG_MAX, as_float(highres.get("cfg"), defaults["cfg"])),
    )
    highres["sampler_name"] = choice(highres.get("sampler_name"), sampler_names(), defaults["sampler_name"])
    highres["scheduler"] = choice(highres.get("scheduler"), scheduler_names(), defaults["scheduler"])
    highres["denoise"] = max(0.0, min(1.0, as_float(highres.get("denoise"), defaults["denoise"])))
    highres["spectrum"] = normalize_spectrum(highres.get("spectrum"), defaults["spectrum"])
    highres["dit_corrections"] = normalize_corrections(highres.get("dit_corrections"), defaults["dit_corrections"])


def _normalize_upscale_settings(
    settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
    sampler_names: ValueHelper,
    scheduler_names: ValueHelper,
    max_resolution_value: ValueHelper,
    normalize_spectrum: ValueHelper,
    normalize_corrections: ValueHelper,
) -> tuple[object, int]:
    upscale = settings["upscale"]
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["upscale"]
    upscale["backend"] = choice(upscale.get("backend"), AIO_FINAL_UPSCALE_BACKENDS, defaults["backend"])
    upscale["scale_by"] = max(0.05, min(4.0, as_float(upscale.get("scale_by"), defaults["scale_by"])))
    upscale["steps"] = max(
        AIO_SAMPLER_STEPS_MIN,
        min(AIO_SAMPLER_STEPS_MAX, as_int(upscale.get("steps"), defaults["steps"])),
    )
    upscale["inherit_sampler_settings"] = as_bool(upscale.get("inherit_sampler_settings"), defaults["inherit_sampler_settings"])
    upscale["cfg"] = max(
        AIO_SAMPLER_CFG_MIN,
        min(AIO_SAMPLER_CFG_MAX, as_float(upscale.get("cfg"), defaults["cfg"])),
    )
    upscale["sampler_name"] = choice(upscale.get("sampler_name"), sampler_names(), defaults["sampler_name"])
    upscale["scheduler"] = choice(upscale.get("scheduler"), scheduler_names(), defaults["scheduler"])
    upscale["denoise"] = max(0.0, min(1.0, as_float(upscale.get("denoise"), defaults["denoise"])))
    max_resolution = max_resolution_value()
    legacy_fit = upscale.pop("fit", None)
    upscale["spectrum"] = normalize_spectrum(upscale.get("spectrum"), defaults["spectrum"])
    upscale["dit_corrections"] = normalize_corrections(upscale.get("dit_corrections"), defaults["dit_corrections"])

    usdu = upscale.setdefault("usdu", {})
    if not isinstance(usdu, dict):
        usdu = {}
        upscale["usdu"] = usdu
    usdu_defaults = defaults["usdu"]
    usdu["upscale_model_name"] = str(usdu.get("upscale_model_name") or usdu_defaults["upscale_model_name"])
    usdu["auto_tile_size"] = as_bool(usdu.get("auto_tile_size"), usdu_defaults["auto_tile_size"])
    prompt_mode = str(usdu.get("prompt_mode") or usdu_defaults["prompt_mode"])
    if prompt_mode == "quality_tags_only":
        prompt_mode = AIO_USDU_PROMPT_NO_GENERAL
    usdu["prompt_mode"] = choice(prompt_mode, AIO_USDU_PROMPT_MODES, usdu_defaults["prompt_mode"])
    usdu["mode_type"] = choice(usdu.get("mode_type"), AIO_USDU_MODE_TYPES, usdu_defaults["mode_type"])
    target = max(64, min(max_resolution, as_int(usdu.get("auto_tile_target"), usdu_defaults["auto_tile_target"])))
    minimum = max(64, min(max_resolution, as_int(usdu.get("auto_tile_min"), usdu_defaults["auto_tile_min"])))
    maximum = max(minimum, min(max_resolution, as_int(usdu.get("auto_tile_max"), usdu_defaults["auto_tile_max"])))
    if target < minimum:
        minimum = target
    if target > maximum:
        maximum = target
    usdu["auto_tile_target"] = target
    usdu["auto_tile_min"] = minimum
    usdu["auto_tile_max"] = max(minimum, maximum)
    usdu["tile_width"] = max(64, min(max_resolution, as_int(usdu.get("tile_width"), usdu_defaults["tile_width"])))
    usdu["tile_height"] = max(64, min(max_resolution, as_int(usdu.get("tile_height"), usdu_defaults["tile_height"])))
    usdu["mask_blur"] = max(0, min(64, as_int(usdu.get("mask_blur"), usdu_defaults["mask_blur"])))
    usdu["tile_padding"] = max(0, min(max_resolution, as_int(usdu.get("tile_padding"), usdu_defaults["tile_padding"])))
    usdu["seam_fix_mode"] = choice(usdu.get("seam_fix_mode"), AIO_USDU_SEAM_FIX_MODES, usdu_defaults["seam_fix_mode"])
    usdu["seam_fix_denoise"] = max(0.0, min(1.0, as_float(usdu.get("seam_fix_denoise"), usdu_defaults["seam_fix_denoise"])))
    usdu["seam_fix_width"] = max(0, min(max_resolution, as_int(usdu.get("seam_fix_width"), usdu_defaults["seam_fix_width"])))
    usdu["seam_fix_mask_blur"] = max(0, min(64, as_int(usdu.get("seam_fix_mask_blur"), usdu_defaults["seam_fix_mask_blur"])))
    usdu["seam_fix_padding"] = max(0, min(max_resolution, as_int(usdu.get("seam_fix_padding"), usdu_defaults["seam_fix_padding"])))
    usdu["force_uniform_tiles"] = as_bool(usdu.get("force_uniform_tiles"), usdu_defaults["force_uniform_tiles"])
    usdu["tiled_decode"] = as_bool(usdu.get("tiled_decode"), usdu_defaults["tiled_decode"])
    usdu["batch_size"] = max(1, min(4096, as_int(usdu.get("batch_size"), usdu_defaults["batch_size"])))

    resshift = upscale.setdefault("resshift", {})
    if not isinstance(resshift, dict):
        resshift = {}
        upscale["resshift"] = resshift
    resshift_defaults = defaults["resshift"]
    resshift["scale"] = choice(resshift.get("scale"), AIO_RESHIFT_SCALES, resshift_defaults["scale"])
    resshift["student_name"] = str(resshift.get("student_name") or resshift_defaults["student_name"])
    resshift["dtype"] = choice(resshift.get("dtype"), AIO_RESHIFT_DTYPES, resshift_defaults["dtype"])
    resshift["chop"] = max(256, min(4096, as_int(resshift.get("chop"), resshift_defaults["chop"])))
    resshift["overlap"] = max(0, min(512, as_int(resshift.get("overlap"), resshift_defaults["overlap"])))
    resshift["tile_batch"] = max(1, min(32, as_int(resshift.get("tile_batch"), resshift_defaults["tile_batch"])))
    return legacy_fit, max_resolution


def _normalize_postprocess_settings(
    settings: dict[str, Any],
    legacy_fit,
    max_resolution: int,
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
) -> None:
    postprocess = settings["postprocess"]
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["postprocess"]
    fit = postprocess.setdefault("fit", {})
    if not isinstance(fit, dict):
        fit = {}
        postprocess["fit"] = fit
    fit_defaults = defaults["fit"]
    if isinstance(legacy_fit, dict):
        if as_bool(legacy_fit.get("enabled"), False):
            postprocess["enabled"] = True
        for key in ("mode", "max_long_edge", "max_megapixels", "method"):
            if key in legacy_fit and fit.get(key) == fit_defaults.get(key):
                fit[key] = legacy_fit[key]
    postprocess["enabled"] = as_bool(postprocess.get("enabled"), defaults["enabled"])
    fit["mode"] = choice(fit.get("mode"), AIO_FINAL_FIT_MODES, fit_defaults["mode"])
    fit["max_long_edge"] = max(64, min(max_resolution, as_int(fit.get("max_long_edge"), fit_defaults["max_long_edge"])))
    fit["max_megapixels"] = max(0.1, min(256.0, as_float(fit.get("max_megapixels"), fit_defaults["max_megapixels"])))
    fit["method"] = choice(fit.get("method"), IMAGE_UPSCALE_METHODS, fit_defaults["method"])


def _normalize_detailer_settings(
    settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
    sampler_names: ValueHelper,
    impact_scheduler_names: ValueHelper,
    target_order: ValueHelper,
    target_defaults: ValueHelper,
    normalize_spectrum: ValueHelper,
    normalize_corrections: ValueHelper,
) -> None:
    detailer = settings["detailer"]
    sam3 = detailer.setdefault("sam3", {})
    if not isinstance(sam3, dict):
        sam3 = {}
        detailer["sam3"] = sam3
    order = target_order(detailer)
    detailer["order"] = order
    sam3["context"] = choice(sam3.get("context"), ("load_checkpoint",), "load_checkpoint")
    sam3["checkpoint"] = str(sam3.get("checkpoint") or "sam3.1_multiplex_fp16.safetensors")
    for target_name in order:
        defaults = target_defaults(target_name)
        target = detailer.setdefault(target_name, {})
        if not isinstance(target, dict):
            target = {}
            detailer[target_name] = target
        target["label"] = str(target.get("label") or defaults.get("label") or target_name.title())
        target["enabled"] = as_bool(target.get("enabled"), defaults["enabled"])
        target["detect_prompt"] = str(target.get("detect_prompt") or defaults["detect_prompt"])
        target["detect_count"] = max(1, min(20, as_int(target.get("detect_count"), defaults["detect_count"])))
        target["threshold"] = max(0.0, min(1.0, as_float(target.get("threshold"), defaults["threshold"])))
        target["refine_iterations"] = max(0, min(16, as_int(target.get("refine_iterations"), defaults["refine_iterations"])))
        target["individual_masks"] = as_bool(target.get("individual_masks"), defaults["individual_masks"])
        target["combined"] = as_bool(target.get("combined"), defaults["combined"])
        target["crop_factor"] = max(1.0, min(16.0, as_float(target.get("crop_factor"), defaults["crop_factor"])))
        target["bbox_fill"] = as_bool(target.get("bbox_fill"), defaults["bbox_fill"])
        target["drop_size"] = max(1, min(4096, as_int(target.get("drop_size"), defaults["drop_size"])))
        target["contour_fill"] = as_bool(target.get("contour_fill"), defaults["contour_fill"])
        target["guide_size"] = max(64, min(4096, as_int(target.get("guide_size"), defaults["guide_size"])))
        target["guide_size_for"] = as_bool(target.get("guide_size_for"), defaults["guide_size_for"])
        target["max_size"] = max(64, min(8192, as_int(target.get("max_size"), defaults["max_size"])))
        target["steps"] = max(
            AIO_SAMPLER_STEPS_MIN,
            min(AIO_SAMPLER_STEPS_MAX, as_int(target.get("steps"), defaults["steps"])),
        )
        target["inherit_sampler_settings"] = as_bool(target.get("inherit_sampler_settings"), defaults["inherit_sampler_settings"])
        target["cfg"] = max(
            AIO_SAMPLER_CFG_MIN,
            min(AIO_SAMPLER_CFG_MAX, as_float(target.get("cfg"), defaults["cfg"])),
        )
        target["sampler_name"] = choice(target.get("sampler_name"), sampler_names(), defaults["sampler_name"])
        target["scheduler"] = choice(target.get("scheduler"), impact_scheduler_names(), defaults["scheduler"])
        target["denoise"] = max(0.0, min(1.0, as_float(target.get("denoise"), defaults["denoise"])))
        target["feather"] = max(0, min(256, as_int(target.get("feather"), defaults["feather"])))
        target["noise_mask"] = as_bool(target.get("noise_mask"), defaults["noise_mask"])
        target["force_inpaint"] = as_bool(target.get("force_inpaint"), defaults["force_inpaint"])
        target["wildcard"] = str(target.get("wildcard") or "")
        target["cycle"] = max(1, min(16, as_int(target.get("cycle"), defaults["cycle"])))
        target["alignment"] = choice(str(target.get("alignment") or defaults["alignment"]), ("impact", "none", "32", "64"), "32")
        target["inpaint_model"] = as_bool(target.get("inpaint_model"), defaults["inpaint_model"])
        target["noise_mask_feather"] = max(0, min(256, as_int(target.get("noise_mask_feather"), defaults["noise_mask_feather"])))
        target["tiled_encode"] = as_bool(target.get("tiled_encode"), defaults["tiled_encode"])
        target["tiled_decode"] = as_bool(target.get("tiled_decode"), defaults["tiled_decode"])
        target["spectrum"] = normalize_spectrum(target.get("spectrum"), defaults["spectrum"])
        target["dit_corrections"] = normalize_corrections(target.get("dit_corrections"), defaults["dit_corrections"])


def _normalize_save_settings(
    settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
    normalize_hash_bundles: ValueHelper,
    normalize_hash_fetchers: ValueHelper,
) -> None:
    save = settings["save"]
    save["backend"] = choice(save.get("backend"), ("image_saver", "comfy_save_image"), "image_saver")
    save.pop("filename_prefix", None)
    image_saver = save.setdefault("image_saver", {})
    if not isinstance(image_saver, dict):
        image_saver = {}
        save["image_saver"] = image_saver
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["save"]["image_saver"]
    image_saver["filename"] = str(image_saver.get("filename") or defaults["filename"])
    image_saver["path"] = str(image_saver.get("path") or defaults["path"])
    image_saver["extension"] = choice(image_saver.get("extension"), ("png", "jpeg", "jpg", "webp"), defaults["extension"])
    image_saver["lossless_webp"] = as_bool(image_saver.get("lossless_webp"), defaults["lossless_webp"])
    image_saver["quality_jpeg_or_webp"] = max(1, min(100, as_int(image_saver.get("quality_jpeg_or_webp"), defaults["quality_jpeg_or_webp"])))
    image_saver["optimize_png"] = as_bool(image_saver.get("optimize_png"), defaults["optimize_png"])
    image_saver["counter"] = max(0, as_int(image_saver.get("counter"), defaults["counter"]))
    image_saver["clip_skip"] = max(-24, min(24, as_int(image_saver.get("clip_skip"), defaults["clip_skip"])))
    image_saver["time_format"] = str(image_saver.get("time_format") or defaults["time_format"])
    image_saver["save_workflow_as_json"] = as_bool(image_saver.get("save_workflow_as_json"), defaults["save_workflow_as_json"])
    image_saver["embed_workflow"] = as_bool(image_saver.get("embed_workflow"), defaults["embed_workflow"])
    image_saver["save_prompt_metadata"] = as_bool(image_saver.get("save_prompt_metadata"), defaults["save_prompt_metadata"])
    image_saver["additional_hashes"] = str(image_saver.get("additional_hashes") or "")
    image_saver["additional_hash_bundles"] = normalize_hash_bundles(image_saver.get("additional_hash_bundles"))
    image_saver["civitai_hash_fetchers"] = normalize_hash_fetchers(image_saver.get("civitai_hash_fetchers"))
    image_saver["download_civitai_data"] = as_bool(image_saver.get("download_civitai_data"), defaults["download_civitai_data"])
    image_saver["easy_remix"] = as_bool(image_saver.get("easy_remix"), defaults["easy_remix"])
    image_saver.pop("show_preview", None)
    image_saver["custom"] = str(image_saver.get("custom") or "")


def _normalize_preview_settings(
    settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_int: ValueHelper,
) -> None:
    preview = settings.setdefault("preview", {})
    if not isinstance(preview, dict):
        preview = {}
        settings["preview"] = preview
    defaults = AIO_GENERATION_DEFAULT_SETTINGS["preview"]
    preview["intermediate_images"] = as_bool(preview.get("intermediate_images"), defaults["intermediate_images"])
    preview["compare_previous"] = as_bool(preview.get("compare_previous"), defaults["compare_previous"])
    preview["image_feed"] = as_bool(preview.get("image_feed"), defaults["image_feed"])
    preview["feed_count"] = max(1, min(100, as_int(preview.get("feed_count"), defaults["feed_count"])))


def normalize_stage_settings(
    settings: dict[str, Any],
    *,
    as_bool: ValueHelper,
    as_float: ValueHelper,
    as_int: ValueHelper,
    choice: ValueHelper,
    sampler_names: ValueHelper,
    scheduler_names: ValueHelper,
    impact_scheduler_names: ValueHelper,
    max_resolution_value: ValueHelper,
    target_order: ValueHelper,
    target_defaults: ValueHelper,
    normalize_spectrum: ValueHelper,
    normalize_corrections: ValueHelper,
    normalize_hash_bundles: ValueHelper,
    normalize_hash_fetchers: ValueHelper,
    round_trip: ValueHelper,
) -> dict[str, Any]:
    for key in ("highres", "detailer", "upscale", "postprocess", "save"):
        section = settings.setdefault(key, {})
        if not isinstance(section, dict):
            section = {}
            settings[key] = section
        section["enabled"] = as_bool(section.get("enabled"), False)
    common = {"as_bool": as_bool, "as_float": as_float, "as_int": as_int, "choice": choice}
    capabilities = {"sampler_names": sampler_names, "scheduler_names": scheduler_names}
    normalizers = {"normalize_spectrum": normalize_spectrum, "normalize_corrections": normalize_corrections}
    _normalize_highres_settings(settings, **common, **capabilities, **normalizers)
    legacy_fit, max_resolution = _normalize_upscale_settings(
        settings, **common, **capabilities, max_resolution_value=max_resolution_value, **normalizers
    )
    _normalize_postprocess_settings(settings, legacy_fit, max_resolution, **common)
    _normalize_detailer_settings(
        settings,
        **common,
        sampler_names=sampler_names,
        impact_scheduler_names=impact_scheduler_names,
        target_order=target_order,
        target_defaults=target_defaults,
        **normalizers,
    )
    _normalize_save_settings(
        settings,
        as_bool=as_bool,
        as_int=as_int,
        choice=choice,
        normalize_hash_bundles=normalize_hash_bundles,
        normalize_hash_fetchers=normalize_hash_fetchers,
    )
    _normalize_preview_settings(settings, as_bool=as_bool, as_int=as_int)
    return round_trip(settings)


__all__ = ()
