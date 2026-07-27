// @ts-check

export const AIO_GENERATOR_SEED_CONTROLS = ["fixed", "randomize", "increment", "decrement"];
export const AIO_GENERATOR_SPECIAL_SEED_RANDOM = -1;
export const AIO_GENERATOR_SPECIAL_SEED_INCREMENT = -2;
export const AIO_GENERATOR_SPECIAL_SEED_DECREMENT = -3;
export const AIO_GENERATOR_MAX_SEED = 1125899906842624;
export const AIO_GENERATION_STAGE_IDS = ["first_pass", "highres", "detailer", "upscale"];

export const AIO_DEFAULT_GENERATION_SETTINGS = {
  schema: "easyuse_anima_aio_generation_settings",
  version: 2,
  mode: "txt2img",
  sampler: {
    backend: "comfy_ksampler",
    seed: AIO_GENERATOR_SPECIAL_SEED_RANDOM,
    seed_after_generate: "fixed",
    steps: 32,
    cfg: 5.0,
    sampler_name: "er_sde",
    scheduler: "simple",
    denoise: 1.0,
    spectrum: {
      enabled: false,
      window_size: 2.0,
      flex_window: 0.25,
      warmup_steps: 6,
      tail_actual_steps: 3,
      blend_w: 0.3,
      cheby_degree: 3,
      ridge_lambda: 0.1,
      history_size: 100,
      one_sampler_only: false,
      verbose: false,
      compat_policy: "conservative",
    },
    spd: {
      split_mode: "single",
      scale: 0.5,
      sigma: 0.7,
      adaptive_smc_alpha: 0.0,
    },
    spectrum_extra: {},
    spd_extra: {},
    dit_corrections: {
      enabled: false,
      dcw_mode: "off",
      dcw_lambda: 0.01,
      dcw_band_mask: "LL",
      dcw_calibrator: "(auto-download default)",
      smc_cfg: false,
      adaptive_smc_alpha: 0.0,
      smc_cfg_lambda: 6.0,
      cfgpp: false,
      cfgpp_lambda: 0.0,
      fsg: false,
      fsg_band_lo: 0.59,
      fsg_band_hi: 0.75,
      fsg_k: 3,
      fsg_d_sigma: 0.1,
      fsg_gamma: 0.0,
      replace_existing_cfg: false,
    },
  },
  negpip: {
    mode: "off",
  },
  model_patches: {
    aura_flow: {
      shift: 3.0,
    },
    dave: {
      enabled: false,
      mask: "dave_alpha.npz",
      strength: 0.30,
      tau: 0.10,
      stage_scope: {
        first_pass: true,
        highres: false,
        detailer: false,
        upscale: false,
      },
    },
    safe_pag: {
      enabled: false,
      scale: 4.0,
      block_indices: "18",
      perturbation_strength: 0.75,
      head_indices: "",
      start_percent: 0.0,
      end_percent: 0.7,
      rescale: 0.2,
      rescale_mode: "full",
    },
    kj: {
      fp16_accumulation: false,
      sage_attention: "disabled",
      sage_allow_compile: false,
      torch_compile: {
        enabled: false,
        backend: "inductor",
        fullgraph: false,
        mode: "max-autotune-no-cudagraphs",
        dynamic: "false",
        compile_transformer_blocks_only: true,
        dynamo_cache_size_limit: 64,
        debug_compile_keys: false,
        disable_dynamic_vram: true,
      },
    },
  },
  mod_guidance: {
    mode: "prompt_data",
    profile: "step_i8_skip27",
    advanced: {
      adapter: "(auto-download default)",
      quality_tags: "highres, best quality, score_7",
      quality_neg: "score_1, score_2, score_3, worst quality, lowres, old, bad hands, bad anatomy",
      mod_w: 3.0,
      mod_start_layer: 8,
      mod_end_layer: 27,
      mod_taper: 0,
      mod_taper_scale: 0.25,
      mod_final_w: 0.0,
    },
  },
  artist_mix: {
    mode: "prompt_data",
    start_percent: 0.5,
    strength_scale: 1.0,
    style_gain: 1.35,
    rms_scale_cap: 2.0,
    exact_top_k: 4,
    cluster_count: 4,
    dominant_isolation: true,
    dominant_threshold: 0.25,
  },
  highres: {
    enabled: false,
    scale_by: 1.5,
    upscale_method: "bicubic",
    multiple: "32",
    max_long_edge: 2560,
    steps: 20,
    inherit_sampler_settings: true,
    cfg: 8.0,
    sampler_name: "euler",
    scheduler: "simple",
    denoise: 0.25,
    spectrum: {
      enabled: false,
      window_size: 2.0,
      flex_window: 0.2,
      warmup_steps: 7,
      tail_actual_steps: 4,
      blend_w: 0.3,
      cheby_degree: 3,
      ridge_lambda: 0.1,
      history_size: 100,
      one_sampler_only: false,
      verbose: false,
      compat_policy: "conservative",
    },
    dit_corrections: {
      enabled: false,
      dcw_mode: "off",
      dcw_lambda: 0.02,
      dcw_band_mask: "LL",
      dcw_calibrator: "(auto-download default)",
      smc_cfg: false,
      adaptive_smc_alpha: 0.0,
      smc_cfg_lambda: 6.0,
      cfgpp: false,
      cfgpp_lambda: 0.0,
      fsg: false,
      fsg_band_lo: 0.59,
      fsg_band_hi: 0.75,
      fsg_k: 3,
      fsg_d_sigma: 0.1,
      fsg_gamma: 0.0,
      replace_existing_cfg: false,
    },
  },
  upscale: {
    enabled: false,
    backend: "usdu",
    scale_by: 2.0,
    steps: 20,
    inherit_sampler_settings: true,
    cfg: 8.0,
    sampler_name: "euler",
    scheduler: "simple",
    denoise: 0.2,
    spectrum: {
      enabled: false,
      window_size: 2.0,
      flex_window: 0.2,
      warmup_steps: 7,
      tail_actual_steps: 4,
      blend_w: 0.3,
      cheby_degree: 3,
      ridge_lambda: 0.1,
      history_size: 100,
      one_sampler_only: false,
      verbose: false,
      compat_policy: "conservative",
    },
    dit_corrections: {
      enabled: false,
      dcw_mode: "off",
      dcw_lambda: 0.02,
      dcw_band_mask: "LL",
      dcw_calibrator: "(auto-download default)",
      smc_cfg: false,
      adaptive_smc_alpha: 0.0,
      smc_cfg_lambda: 6.0,
      cfgpp: false,
      cfgpp_lambda: 0.0,
      fsg: false,
      fsg_band_lo: 0.59,
      fsg_band_hi: 0.75,
      fsg_k: 3,
      fsg_d_sigma: 0.1,
      fsg_gamma: 0.0,
      replace_existing_cfg: false,
    },
    usdu: {
      upscale_model_name: "2x-AnimeSharpV4_Fast_RCAN_PU.safetensors",
      auto_tile_size: true,
      prompt_mode: "full",
      mode_type: "Linear",
      auto_tile_target: 1024,
      auto_tile_min: 512,
      auto_tile_max: 2048,
      tile_width: 512,
      tile_height: 512,
      mask_blur: 8,
      tile_padding: 32,
      seam_fix_mode: "None",
      seam_fix_denoise: 1.0,
      seam_fix_width: 64,
      seam_fix_mask_blur: 8,
      seam_fix_padding: 16,
      force_uniform_tiles: true,
      tiled_decode: false,
      batch_size: 1,
    },
    resshift: {
      scale: "x2",
      student_name: "(auto-download)",
      dtype: "bf16",
      chop: 512,
      overlap: 64,
      tile_batch: 4,
    },
  },
  postprocess: {
    enabled: false,
    fit: {
      mode: "max_long_edge",
      max_long_edge: 2048,
      max_megapixels: 4.0,
      method: "bicubic",
    },
  },
  detailer: {
    enabled: false,
    order: ["face", "eye"],
    sam3: {
      context: "load_checkpoint",
      checkpoint: "sam3.1_multiplex_fp16.safetensors",
    },
    face: {
      label: "Face Detailer",
      enabled: false,
      detect_prompt: "face",
      detect_count: 1,
      threshold: 0.52,
      refine_iterations: 2,
      individual_masks: true,
      combined: false,
      crop_factor: 4.0,
      bbox_fill: false,
      drop_size: 100,
      contour_fill: true,
      guide_size: 1024,
      guide_size_for: false,
      max_size: 2048,
      steps: 20,
      inherit_sampler_settings: true,
      cfg: 8.0,
      sampler_name: "euler",
      scheduler: "sgm_uniform",
      denoise: 0.33,
      feather: 5,
      noise_mask: true,
      force_inpaint: true,
      wildcard: "",
      cycle: 1,
      alignment: "32",
      inpaint_model: false,
      noise_mask_feather: 10,
      tiled_encode: false,
      tiled_decode: false,
      spectrum: {
        enabled: true,
        window_size: 2.0,
        flex_window: 0.15,
        warmup_steps: 6,
        tail_actual_steps: 3,
        blend_w: 0.3,
        cheby_degree: 3,
        ridge_lambda: 0.1,
        history_size: 100,
        one_sampler_only: false,
        verbose: false,
        compat_policy: "conservative",
      },
      dit_corrections: {
        enabled: false,
        dcw_mode: "off",
        dcw_lambda: 0.02,
        dcw_band_mask: "LL",
        dcw_calibrator: "(auto-download default)",
        smc_cfg: false,
        adaptive_smc_alpha: 0.0,
        smc_cfg_lambda: 6.0,
        cfgpp: false,
        cfgpp_lambda: 0.0,
        fsg: false,
        fsg_band_lo: 0.59,
        fsg_band_hi: 0.75,
        fsg_k: 3,
        fsg_d_sigma: 0.1,
        fsg_gamma: 0.0,
        replace_existing_cfg: false,
      },
    },
    eye: {
      label: "Eye Detailer",
      enabled: false,
      detect_prompt: "eyes",
      detect_count: 1,
      threshold: 0.5,
      refine_iterations: 2,
      individual_masks: true,
      combined: false,
      crop_factor: 6.0,
      bbox_fill: false,
      drop_size: 40,
      contour_fill: true,
      guide_size: 1024,
      guide_size_for: false,
      max_size: 2048,
      steps: 20,
      inherit_sampler_settings: true,
      cfg: 8.0,
      sampler_name: "euler",
      scheduler: "sgm_uniform",
      denoise: 0.29,
      feather: 6,
      noise_mask: true,
      force_inpaint: true,
      wildcard: "",
      cycle: 1,
      alignment: "32",
      inpaint_model: false,
      noise_mask_feather: 20,
      tiled_encode: false,
      tiled_decode: false,
      spectrum: {
        enabled: true,
        window_size: 2.0,
        flex_window: 0.15,
        warmup_steps: 6,
        tail_actual_steps: 3,
        blend_w: 0.3,
        cheby_degree: 3,
        ridge_lambda: 0.1,
        history_size: 100,
        one_sampler_only: false,
        verbose: false,
        compat_policy: "conservative",
      },
      dit_corrections: {
        enabled: false,
        dcw_mode: "off",
        dcw_lambda: 0.02,
        dcw_band_mask: "LL",
        dcw_calibrator: "(auto-download default)",
        smc_cfg: false,
        adaptive_smc_alpha: 0.0,
        smc_cfg_lambda: 6.0,
        cfgpp: false,
        cfgpp_lambda: 0.0,
        fsg: false,
        fsg_band_lo: 0.59,
        fsg_band_hi: 0.75,
        fsg_k: 3,
        fsg_d_sigma: 0.1,
        fsg_gamma: 0.0,
        replace_existing_cfg: false,
      },
    },
  },
  save: {
    enabled: true,
    backend: "image_saver",
    image_saver: {
      filename: "%time_%basemodelname",
      path: "EasyUseAnima/AiO",
      extension: "webp",
      lossless_webp: false,
      quality_jpeg_or_webp: 97,
      optimize_png: true,
      counter: 0,
      clip_skip: 0,
      time_format: "%Y-%m-%d-%H%M%S",
      save_workflow_as_json: false,
      embed_workflow: true,
      save_prompt_metadata: true,
      additional_hashes: "",
      additional_hash_bundles: [],
      civitai_hash_fetchers: [],
      download_civitai_data: true,
      easy_remix: true,
      custom: "",
    },
  },
  preview: {
    intermediate_images: false,
    compare_previous: false,
    image_feed: true,
    feed_count: 12,
  },
};

export const AIO_DEFAULT_INPUT_SETTINGS = {
  schema: "easy_use_anima_input",
  version: 1,
  resources: {
    loader_mode: "split",
    clip_loader: "single",
    unet_weight_dtype: "default",
    clip_device: "default",
  },
  metadata: {},
};

export function aioCloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

export function aioMigrateGenerationSettingsVersion(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return value;
  }
  const migrated = aioCloneJson(value);
  if (
    migrated.schema === AIO_DEFAULT_GENERATION_SETTINGS.schema
    && migrated.version === 1
  ) {
    const dave = migrated.model_patches?.dave;
    if (
      dave
      && typeof dave === "object"
      && !Array.isArray(dave)
      && !Object.prototype.hasOwnProperty.call(dave, "stage_scope")
    ) {
      dave.stage_scope = Object.fromEntries(
        AIO_GENERATION_STAGE_IDS.map((stageId) => [stageId, true]),
      );
    }
    migrated.version = 2;
  }
  return migrated;
}

export function aioMergeDefaults(defaults, value) {
  const output = aioCloneJson(defaults);
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return output;
  }
  const merge = (base, incoming) => {
    for (const [key, incomingValue] of Object.entries(incoming)) {
      const baseValue = Object.prototype.hasOwnProperty.call(base, key)
        ? base[key]
        : undefined;
      if (
        baseValue
        && typeof baseValue === "object"
        && !Array.isArray(baseValue)
        && incomingValue
        && typeof incomingValue === "object"
        && !Array.isArray(incomingValue)
      ) {
        merge(baseValue, incomingValue);
      } else {
        Object.defineProperty(base, key, {
          value: incomingValue,
          enumerable: true,
          configurable: true,
          writable: true,
        });
      }
    }
    return base;
  };
  return merge(output, value);
}

export function aioAsBool(value, fallback = false) {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "1", "yes", "on"].includes(normalized)) {
      return true;
    }
    if (["false", "0", "no", "off"].includes(normalized)) {
      return false;
    }
  }
  return value == null ? fallback : !!value;
}

export function aioMigrateGeneratorPostprocessSettings(settings) {
  if (!settings || typeof settings !== "object" || Array.isArray(settings)) {
    return settings;
  }
  const legacyFit = settings.upscale?.fit;
  if (legacyFit && typeof legacyFit === "object" && !Array.isArray(legacyFit)) {
    const defaults = AIO_DEFAULT_GENERATION_SETTINGS.postprocess;
    const defaultFit = defaults.fit;
    settings.postprocess = aioMergeDefaults(defaults, settings.postprocess || {});
    settings.postprocess.fit = aioMergeDefaults(defaultFit, settings.postprocess.fit || {});
    if (aioAsBool(legacyFit.enabled, false)) {
      settings.postprocess.enabled = true;
    }
    for (const key of ["mode", "max_long_edge", "max_megapixels", "method"]) {
      if (
        Object.prototype.hasOwnProperty.call(legacyFit, key)
        && settings.postprocess.fit[key] === defaultFit[key]
      ) {
        settings.postprocess.fit[key] = legacyFit[key];
      }
    }
  }
  if (settings.upscale && typeof settings.upscale === "object" && !Array.isArray(settings.upscale)) {
    delete settings.upscale.fit;
  }
  return settings;
}

export function aioParseSettingsValue(rawValue, defaults) {
  try {
    const rawParsed = JSON.parse(rawValue || "{}");
    const incoming = defaults === AIO_DEFAULT_GENERATION_SETTINGS
      ? aioMigrateGenerationSettingsVersion(rawParsed)
      : rawParsed;
    const parsed = aioMergeDefaults(defaults, incoming);
    return defaults === AIO_DEFAULT_GENERATION_SETTINGS
      ? aioMigrateGeneratorPostprocessSettings(parsed)
      : parsed;
  } catch {
    return aioCloneJson(defaults);
  }
}

export function aioNormalizeSeedControl(value) {
  const normalized = String(value || "").trim();
  return AIO_GENERATOR_SEED_CONTROLS.includes(normalized) ? normalized : "fixed";
}

export function aioNormalizeSeedValue(value, fallback = AIO_GENERATOR_SPECIAL_SEED_RANDOM) {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) {
    return fallback;
  }
  return Math.max(AIO_GENERATOR_SPECIAL_SEED_DECREMENT, Math.min(AIO_GENERATOR_MAX_SEED, Math.trunc(numberValue)));
}

function clampNumber(value, fallback, min, max) {
  const parsed = Number(value);
  const next = Number.isFinite(parsed) ? parsed : fallback;
  return Math.max(min, Math.min(max, next));
}

export function aioNormalizeGeneratorPreviewSettings(settings) {
  settings.preview = aioMergeDefaults(AIO_DEFAULT_GENERATION_SETTINGS.preview, settings.preview || {});
  settings.preview.intermediate_images = aioAsBool(
    settings.preview.intermediate_images,
    AIO_DEFAULT_GENERATION_SETTINGS.preview.intermediate_images,
  );
  settings.preview.compare_previous = aioAsBool(
    settings.preview.compare_previous,
    AIO_DEFAULT_GENERATION_SETTINGS.preview.compare_previous,
  );
  settings.preview.image_feed = aioAsBool(
    settings.preview.image_feed,
    AIO_DEFAULT_GENERATION_SETTINGS.preview.image_feed,
  );
  settings.preview.feed_count = Math.trunc(clampNumber(
    settings.preview.feed_count,
    AIO_DEFAULT_GENERATION_SETTINGS.preview.feed_count,
    1,
    100,
  ));
  if (settings.save?.image_saver) {
    delete settings.save.image_saver.show_preview;
  }
  return settings.preview;
}

export function aioSettingsToCompactJson(settings) {
  const next = aioMergeDefaults(
    AIO_DEFAULT_GENERATION_SETTINGS,
    aioMigrateGenerationSettingsVersion(settings),
  );
  delete next.save?.filename_prefix;
  aioNormalizeGeneratorPreviewSettings(next);
  return JSON.stringify(next);
}
