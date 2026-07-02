import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { easyuseAnimaText, easyuseAnimaWatchLocale } from "./easyuse_anima_i18n.js";

const INPUT_NODE_TYPE = "EasyUseAnimaInput";
const GENERATOR_NODE_TYPE = "EasyUseAnimaAIOGenerator";
const INPUT_SETTINGS_WIDGET = "input_settings";
const GENERATOR_SETTINGS_WIDGET = "generation_settings";
const GENERATOR_DOM_WIDGET = "easyuse_anima_generator_panel";
const GENERATOR_PREVIEW_EVENT = "easyuse-anima-aio-preview";
const GENERATOR_SEED_CONTROLS = ["fixed", "randomize", "increment", "decrement"];
const GENERATOR_SPECIAL_SEED_RANDOM = -1;
const GENERATOR_SPECIAL_SEED_INCREMENT = -2;
const GENERATOR_SPECIAL_SEED_DECREMENT = -3;
const GENERATOR_SPECIAL_SEEDS = [
  GENERATOR_SPECIAL_SEED_RANDOM,
  GENERATOR_SPECIAL_SEED_INCREMENT,
  GENERATOR_SPECIAL_SEED_DECREMENT,
];
const GENERATOR_MAX_SEED = 1125899906842624;
const GENERATOR_NODE_MIN_WIDTH = 560;
const GENERATOR_NODE_DEFAULT_WIDTH = 620;
const GENERATOR_PANEL_MIN_HEIGHT = 430;
const GENERATOR_PANEL_CONTROL_SELECTOR = "input, select, textarea, button";
const GENERATOR_FALLBACK_SAMPLER_NAMES = [
  "er_sde",
  "euler",
  "euler_ancestral",
  "heun",
  "dpm_2",
  "dpm_2_ancestral",
  "dpmpp_2m",
  "dpmpp_sde",
  "ddim",
];
const GENERATOR_FALLBACK_SCHEDULER_NAMES = [
  "simple",
  "sgm_uniform",
  "karras",
  "exponential",
  "ddim_uniform",
  "beta",
  "normal",
  "linear_quadratic",
  "kl_optimal",
  "AYS SDXL",
  "AYS SD1",
  "AYS SVD",
  "GITS[coeff=1.2]",
  "LTXV[default]",
  "OSS FLUX",
  "OSS Wan",
  "OSS Chroma",
];
const GENERATOR_OPTIONAL_DEPENDENCY_SPECS = {
  spectrumAdvanced: {
    nodeId: "SpectrumKSamplerAdvanced",
    pack: "ComfyUI-Spectrum-KSampler",
  },
  spectrumSpd: {
    nodeId: "SpectrumSPDKSampler",
    pack: "ComfyUI-Spectrum-KSampler",
  },
  spectrumPatch: {
    nodeId: "DiTSpectrumPatchAdvanced",
    pack: "ComfyUI-Spectrum-KSampler",
  },
  dave: {
    nodeId: "AnimaDAVE",
    pack: "ComfyUI-Anima-DAVE",
  },
  imageSaver: {
    nodeId: "Image Saver",
    pack: "ComfyUI-Image-Saver",
  },
  kjFp16: {
    nodeId: "ModelPatchTorchSettings",
    pack: "ComfyUI-KJNodes",
  },
  kjSage: {
    nodeId: "PathchSageAttentionKJ",
    pack: "ComfyUI-KJNodes",
  },
  kjTorchCompile: {
    nodeId: "TorchCompileModelAdvanced",
    pack: "ComfyUI-KJNodes",
  },
  impactDetailer: {
    nodeId: "DetailerForEach",
    pack: "ComfyUI-Impact-Pack",
  },
  impactMaskToSegs: {
    nodeId: "MaskToSEGS",
    pack: "ComfyUI-Impact-Pack",
  },
};
const GENERATOR_BACKEND_DEPENDENCIES = {
  spectrum_mod_guidance_advanced: "spectrumAdvanced",
  spectrum_spd_speed: "spectrumSpd",
};

const DEFAULT_GENERATION_SETTINGS = {
  schema: "easyuse_anima_aio_generation_settings",
  version: 1,
  mode: "txt2img",
  sampler: {
    backend: "comfy_ksampler",
    seed: GENERATOR_SPECIAL_SEED_RANDOM,
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
  model_patches: {
    aura_flow: {
      shift: 3.0,
    },
    dave: {
      enabled: false,
      mask: "dave_alpha.npz",
      strength: 0.30,
      tau: 0.10,
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
      enabled: true,
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

const AIO_TEXT = {
  en: {
    "title.sampler": "SAMPLER",
    "title.preview": "PREVIEW",
    "title.highres": "HIGHRES",
    "title.detailer": "DETAILER",
    "label.mode": "Mode",
    "label.seed": "Seed",
    "label.steps": "Steps",
    "label.cfg": "CFG",
    "label.shift": "Shift",
    "label.denoise": "Denoise",
    "label.sampler": "Sampler",
    "label.scheduler": "Scheduler",
    "label.enabled": "Enabled",
    "label.followMainSampler": "Follow main sampler",
    "label.scaleBy": "Scale",
    "label.maxLongEdge": "Max edge",
    "label.face": "Face",
    "label.eye": "Eye",
    "label.size": "size",
    "label.image": "image",
    "label.resolution": "resolution",
    "label.fileSize": "file size",
    "button.randomEach": "Randomize Each Time",
    "button.newFixed": "New Fixed Random",
    "button.useLast": "Use Last Queued: {seed}",
    "button.useLastNone": "Use Last Queued: -",
    "button.samplerDetails": "Sampler Details...",
    "button.highresSettings": "Highres Settings",
    "button.detailerSettings": "Detailer Settings",
    "button.advancedOptions": "Advanced Options...",
    "button.saveOn": "Save Options: ON",
    "button.saveOff": "Save Options: OFF",
    "button.previewOptions": "Preview Options...",
    "button.moveUp": "Up",
    "button.moveDown": "Down",
    "button.addCivitaiFetcher": "+ Add Civitai Hash Fetcher",
    "button.remove": "Remove",
    "text.previewTitle": "Generated Image Preview",
    "text.previewSubtitle": "Preview slot is reserved for this node output.",
    "text.previewOptionsSubtitle": "Preview settings control only this node UI. They do not change saved image metadata.",
    "text.previewPrevious": "Previous",
    "text.previewCurrent": "Current",
    "text.highresDisabled": "Enable Highres to expose resize and second-pass controls.",
    "text.detailerDisabled": "Enable Detailer to configure ordered processing blocks.",
    "text.inheritsMainSampler": "Uses main CFG, sampler, and scheduler.",
    "text.usesStageSamplerOverride": "Uses stage-specific CFG, sampler, and scheduler from the popup.",
    "text.civitaiHashPreview": "Adds as {model}:AutoV3",
    "tip.fieldGeneric": "{label} setting. This value is saved with the node workflow.",
    "tip.additionalHashes": "Manual Image Saver additional_hashes string. Supports Name:HASH, HASH:Weight, and Name:HASH:Weight.",
    "tip.hashBundles": "Manual chunks appended to Image Saver additional_hashes.",
    "tip.civitaiHashFetchers": "Runs Civitai Hash Fetcher (Image Saver) at queue time and appends model_name:AutoV3 to additional_hashes.",
    "tip.civitaiUsername": "Civitai username used by Civitai Hash Fetcher.",
    "tip.civitaiModelName": "Civitai model name. This is also used as the Name in Name:Hash.",
    "tip.civitaiVersion": "Optional version keyword passed to Civitai Hash Fetcher.",
    "tip.mode": "Shows the selected sampler backend and active special sampling patches.",
    "tip.seed": "The seed sent to queue. -1 resolves a new random seed at queue time.",
    "tip.randomEach": "Set seed to -1 so each queue resolves a new random seed.",
    "tip.newFixed": "Generate a concrete random seed now and keep it fixed.",
    "tip.useLast": "Reuse the last seed resolved for this node at queue time.",
    "tip.steps": "Main sampler steps. The compact slider range is 1 to 75.",
    "tip.cfg": "Main classifier-free guidance scale. Range is 1.0 to 10.0.",
    "tip.shift": "AuraFlow model sampling shift. Always applied; 3.0 is the Anima model-recommended default.",
    "tip.denoise": "Main denoise strength for the first sampling pass.",
    "tip.sampler": "Main ComfyUI sampler name used by the first pass.",
    "tip.scheduler": "Main ComfyUI scheduler used by the first pass.",
    "tip.highresEnabled": "Run a second pass after upscaling the first-pass image.",
    "tip.highresFollow": "When enabled, Highres uses the main CFG, sampler, and scheduler.",
    "tip.highresScale": "Upscale ratio before the Highres second pass.",
    "tip.highresMaxEdge": "Maximum long edge after upscaling. Use 0 to disable this cap.",
    "tip.highresSteps": "Highres second-pass steps. CFG, sampler, and scheduler follow the main sampler by default.",
    "tip.highresDenoise": "Highres second-pass denoise strength.",
    "tip.detailerEnabled": "Run SAM3 and Impact Detailer stages after generation.",
    "tip.detailerBlock": "Each block can be enabled, reordered, and tuned independently.",
    "tip.detailerFollow": "When enabled, this detailer block uses the main CFG, sampler, and scheduler.",
    "tip.detailerSteps": "Impact Detailer sampling steps for this block.",
    "tip.detailerDenoise": "Impact Detailer denoise strength for this block.",
    "tip.detailerOrder": "Move this image-processing block earlier or later.",
    "tip.detailerName": "Display name for this detailer tab. It is saved with the workflow for UI organization.",
    "tip.samplerDetails": "Open sampler backend, Mod Guidance, and Spectrum options.",
    "tip.highresSettings": "Open all Highres scaling and optimization options.",
    "tip.detailerSettings": "Open all SAM3 and Impact Detailer options.",
    "tip.advancedOptions": "Open model patch, optimization, and prompt-data driven advanced options.",
    "tip.saveOptions": "Open image saver and metadata options.",
    "tip.previewOptions": "Open node preview, comparison, and image feed options.",
    "tip.previewIntermediate": "Save temp previews for first pass, Highres, and Detailer stages.",
    "tip.previewComparePrevious": "When intermediate previews are enabled, compare the selected preview with the previous item in this run.",
    "tip.previewImageFeed": "Show the current run's preview images as a compact feed at the bottom of the preview panel.",
    "tip.previewFeedCount": "Maximum number of preview images kept in this node's feed history.",
    "tip.size": "Size of the latest generated image for this node.",
  },
  ko: {
    "title.sampler": "SAMPLER",
    "title.preview": "PREVIEW",
    "title.highres": "HIGHRES",
    "title.detailer": "DETAILER",
    "label.mode": "모드",
    "label.seed": "시드",
    "label.steps": "스텝",
    "label.cfg": "CFG",
    "label.shift": "시프트",
    "label.denoise": "디노이즈",
    "label.sampler": "샘플러",
    "label.scheduler": "스케줄러",
    "label.enabled": "활성화",
    "label.followMainSampler": "메인 샘플러 따름",
    "label.scaleBy": "확대",
    "label.maxLongEdge": "최대 긴 변",
    "label.face": "얼굴",
    "label.eye": "눈",
    "label.size": "크기",
    "label.image": "이미지",
    "label.resolution": "해상도",
    "label.fileSize": "저장용량",
    "button.randomEach": "매번 랜덤",
    "button.newFixed": "새 랜덤 고정",
    "button.useLast": "Last Queued: {seed}",
    "button.useLastNone": "Last Queued: -",
    "button.samplerDetails": "샘플러 상세...",
    "button.highresSettings": "Highres 설정",
    "button.detailerSettings": "디테일러 설정",
    "button.advancedOptions": "고급 옵션...",
    "button.saveOn": "저장 옵션: ON",
    "button.saveOff": "저장 옵션: OFF",
    "button.previewOptions": "프리뷰 옵션...",
    "button.moveUp": "위",
    "button.moveDown": "아래",
    "button.addCivitaiFetcher": "+ Civitai Hash Fetcher 추가",
    "button.remove": "삭제",
    "text.previewTitle": "생성 이미지 미리보기",
    "text.previewSubtitle": "이 노드 출력 전용 미리보기 영역입니다.",
    "text.previewOptionsSubtitle": "프리뷰 설정은 이 노드 UI에만 적용됩니다. 저장 이미지 메타데이터는 바꾸지 않습니다.",
    "text.previewPrevious": "이전",
    "text.previewCurrent": "현재",
    "text.highresDisabled": "Highres를 켜면 확대와 2차 샘플링 기본 설정이 표시됩니다.",
    "text.detailerDisabled": "디테일러를 켜면 순서 조정 가능한 처리 블럭이 표시됩니다.",
    "text.inheritsMainSampler": "메인 CFG, 샘플러, 스케줄러를 사용합니다.",
    "text.usesStageSamplerOverride": "팝업에 저장된 단계별 CFG, 샘플러, 스케줄러를 사용합니다.",
    "text.civitaiHashPreview": "{model}:AutoV3 형식으로 추가됩니다.",
    "tip.fieldGeneric": "{label} 설정입니다. 이 값은 노드 워크플로우에 저장됩니다.",
    "tip.additionalHashes": "Image Saver의 additional_hashes 수동 문자열입니다. Name:HASH, HASH:Weight, Name:HASH:Weight를 지원합니다.",
    "tip.hashBundles": "Image Saver additional_hashes에 붙일 수동 해시 묶음입니다.",
    "tip.civitaiHashFetchers": "큐 실행 시 Civitai Hash Fetcher (Image Saver)를 실행하고 model_name:AutoV3를 additional_hashes에 추가합니다.",
    "tip.civitaiUsername": "Civitai Hash Fetcher에 전달할 Civitai 유저네임입니다.",
    "tip.civitaiModelName": "Civitai 모델명입니다. Name:Hash의 Name으로도 사용됩니다.",
    "tip.civitaiVersion": "Civitai Hash Fetcher에 전달할 선택 버전 키워드입니다.",
    "tip.mode": "선택된 샘플러 백엔드와 적용 중인 특수 샘플링 패치를 표시합니다.",
    "tip.seed": "큐에 전달되는 시드입니다. -1은 큐 실행 시 새 랜덤 시드로 해석됩니다.",
    "tip.randomEach": "시드를 -1로 설정해 실행할 때마다 새 랜덤 시드를 사용합니다.",
    "tip.newFixed": "지금 랜덤 시드를 하나 생성하고 고정값으로 사용합니다.",
    "tip.useLast": "이 노드가 마지막 큐 실행에서 사용한 실제 시드를 다시 사용합니다.",
    "tip.steps": "1차 샘플러 스텝입니다. 기본 슬라이더 범위는 1부터 75까지입니다.",
    "tip.cfg": "1차 CFG 값입니다. 범위는 1.0부터 10.0까지입니다.",
    "tip.shift": "AuraFlow 모델 샘플링 시프트입니다. 항상 적용되며 3.0이 Anima 모델 권장 기본값입니다.",
    "tip.denoise": "1차 샘플링 디노이즈 강도입니다.",
    "tip.sampler": "1차 패스에 사용할 ComfyUI 샘플러 이름입니다.",
    "tip.scheduler": "1차 패스에 사용할 ComfyUI 스케줄러입니다.",
    "tip.highresEnabled": "1차 이미지 확대 후 2차 샘플링을 실행합니다.",
    "tip.highresFollow": "켜져 있으면 Highres가 메인 CFG, 샘플러, 스케줄러를 따릅니다.",
    "tip.highresScale": "Highres 2차 패스 전에 적용할 확대 배율입니다.",
    "tip.highresMaxEdge": "확대 후 긴 변 제한입니다. 0이면 제한하지 않습니다.",
    "tip.highresSteps": "Highres 2차 패스 스텝입니다. CFG, 샘플러, 스케줄러는 기본적으로 메인을 따릅니다.",
    "tip.highresDenoise": "Highres 2차 패스 디노이즈 강도입니다.",
    "tip.detailerEnabled": "생성 후 SAM3와 Impact Detailer 단계를 실행합니다.",
    "tip.detailerBlock": "각 블럭은 개별 활성화, 순서 변경, 기본 설정 조정이 가능합니다.",
    "tip.detailerFollow": "켜져 있으면 이 디테일러 블럭이 메인 CFG, 샘플러, 스케줄러를 따릅니다.",
    "tip.detailerSteps": "이 블럭의 Impact Detailer 샘플링 스텝입니다.",
    "tip.detailerDenoise": "이 블럭의 Impact Detailer 디노이즈 강도입니다.",
    "tip.detailerOrder": "이 이미지 처리 블럭의 실행 순서를 앞뒤로 이동합니다.",
    "tip.detailerName": "이 디테일러 탭의 표시 이름입니다. UI 정리를 위해 워크플로우에 저장됩니다.",
    "tip.samplerDetails": "샘플러 백엔드, Mod Guidance, Spectrum 옵션을 엽니다.",
    "tip.highresSettings": "Highres 확대와 최적화 전체 옵션을 엽니다.",
    "tip.detailerSettings": "SAM3와 Impact Detailer 전체 옵션을 엽니다.",
    "tip.advancedOptions": "모델 패치, 최적화, Prompt Data 기반 고급 옵션을 엽니다.",
    "tip.saveOptions": "이미지 저장과 메타데이터 옵션을 엽니다.",
    "tip.previewOptions": "노드 프리뷰, 비교, 이미지 피드 옵션을 엽니다.",
    "tip.previewIntermediate": "1차, Highres, Detailer 단계의 temp 미리보기를 저장합니다.",
    "tip.previewComparePrevious": "중간 이미지 미리보기가 켜져 있을 때 선택한 프리뷰와 현재 실행의 직전 항목을 비교합니다.",
    "tip.previewImageFeed": "현재 실행의 프리뷰 이미지들을 프리뷰 패널 하단에 작은 피드로 표시합니다.",
    "tip.previewFeedCount": "이 노드의 프리뷰 피드에 유지할 최대 이미지 개수입니다.",
    "tip.size": "이 노드가 마지막으로 생성한 이미지 크기입니다.",
  },
  ja: {
    "title.sampler": "SAMPLER",
    "title.preview": "PREVIEW",
    "title.highres": "HIGHRES",
    "title.detailer": "DETAILER",
    "label.mode": "モード",
    "label.seed": "シード",
    "label.steps": "ステップ",
    "label.cfg": "CFG",
    "label.shift": "シフト",
    "label.denoise": "デノイズ",
    "label.sampler": "サンプラー",
    "label.scheduler": "スケジューラー",
    "label.enabled": "有効",
    "label.followMainSampler": "メインサンプラーに追従",
    "label.scaleBy": "拡大",
    "label.maxLongEdge": "最大長辺",
    "label.face": "顔",
    "label.eye": "目",
    "label.size": "サイズ",
    "button.randomEach": "毎回ランダム",
    "button.newFixed": "新規固定ランダム",
    "button.useLast": "Last Queued: {seed}",
    "button.useLastNone": "Last Queued: -",
    "button.samplerDetails": "サンプラー詳細...",
    "button.highresSettings": "Highres 設定",
    "button.detailerSettings": "Detailer 設定",
    "button.advancedOptions": "詳細オプション...",
    "button.saveOn": "保存オプション: ON",
    "button.saveOff": "保存オプション: OFF",
    "button.moveUp": "上へ",
    "button.moveDown": "下へ",
    "button.addCivitaiFetcher": "+ Civitai Hash Fetcher を追加",
    "button.remove": "削除",
    "text.previewTitle": "生成画像プレビュー",
    "text.previewSubtitle": "このノード出力専用のプレビュー領域です。",
    "text.highresDisabled": "Highres を有効にすると拡大と二回目サンプリングの基本設定を表示します。",
    "text.detailerDisabled": "Detailer を有効にすると順序変更できる処理ブロックを表示します。",
    "text.inheritsMainSampler": "メイン CFG、サンプラー、スケジューラーを使用します。",
    "text.usesStageSamplerOverride": "ポップアップに保存された段階別 CFG、サンプラー、スケジューラーを使用します。",
    "text.civitaiHashPreview": "{model}:AutoV3 として追加されます。",
    "tip.fieldGeneric": "{label} の設定です。この値はノードのワークフローに保存されます。",
    "tip.additionalHashes": "Image Saver の additional_hashes 手動文字列です。Name:HASH、HASH:Weight、Name:HASH:Weight を使用できます。",
    "tip.hashBundles": "Image Saver additional_hashes に追加する手動ハッシュのまとまりです。",
    "tip.civitaiHashFetchers": "キュー時に Civitai Hash Fetcher (Image Saver) を実行し、model_name:AutoV3 を additional_hashes に追加します。",
    "tip.civitaiUsername": "Civitai Hash Fetcher に渡す Civitai ユーザー名です。",
    "tip.civitaiModelName": "Civitai モデル名です。Name:Hash の Name としても使われます。",
    "tip.civitaiVersion": "Civitai Hash Fetcher に渡す任意のバージョンキーワードです。",
    "tip.mode": "選択中のサンプラーバックエンドと有効な特殊パッチを表示します。",
    "tip.seed": "キューへ送るシードです。-1 はキュー時に新しいランダムシードになります。",
    "tip.randomEach": "シードを -1 にして、キューごとに新しいランダムシードを使います。",
    "tip.newFixed": "今ランダムシードを生成し、固定値として使います。",
    "tip.useLast": "このノードで最後にキューされた実シードを再利用します。",
    "tip.steps": "一回目サンプラーのステップです。範囲は 1 から 75 です。",
    "tip.cfg": "一回目の CFG 値です。範囲は 1.0 から 10.0 です。",
    "tip.shift": "AuraFlow のモデルサンプリングシフトです。常に適用され、3.0 が Anima model 推奨既定値です。",
    "tip.denoise": "一回目サンプリングのデノイズ強度です。",
    "tip.sampler": "一回目に使う ComfyUI サンプラー名です。",
    "tip.scheduler": "一回目に使う ComfyUI スケジューラーです。",
    "tip.highresEnabled": "一回目画像を拡大して二回目サンプリングを実行します。",
    "tip.highresFollow": "有効時、Highres はメイン CFG、サンプラー、スケジューラーに追従します。",
    "tip.highresScale": "Highres 二回目パス前の拡大倍率です。",
    "tip.highresMaxEdge": "拡大後の長辺上限です。0 で上限なしです。",
    "tip.highresSteps": "Highres 二回目パスのステップです。",
    "tip.highresDenoise": "Highres 二回目パスのデノイズ強度です。",
    "tip.detailerEnabled": "生成後に SAM3 と Impact Detailer を実行します。",
    "tip.detailerBlock": "各ブロックは個別に有効化、並べ替え、調整できます。",
    "tip.detailerFollow": "有効時、この Detailer ブロックはメインサンプラー設定に追従します。",
    "tip.detailerSteps": "このブロックの Impact Detailer ステップです。",
    "tip.detailerDenoise": "このブロックの Impact Detailer デノイズ強度です。",
    "tip.detailerOrder": "この画像処理ブロックの実行順を移動します。",
    "tip.detailerName": "この detailer tab の表示名です。UI 整理用に workflow へ保存されます。",
    "tip.samplerDetails": "サンプラーバックエンド、Mod Guidance、Spectrum オプションを開きます。",
    "tip.highresSettings": "Highres の拡大と最適化オプションを開きます。",
    "tip.detailerSettings": "SAM3 と Impact Detailer の全オプションを開きます。",
    "tip.advancedOptions": "モデルパッチ、最適化、Prompt Data ベースの詳細オプションを開きます。",
    "tip.saveOptions": "画像保存とメタデータオプションを開きます。",
    "tip.size": "このノードが最後に生成した画像サイズです。",
  },
  zh: {
    "title.sampler": "SAMPLER",
    "title.preview": "PREVIEW",
    "title.highres": "HIGHRES",
    "title.detailer": "DETAILER",
    "label.mode": "模式",
    "label.seed": "种子",
    "label.steps": "步数",
    "label.cfg": "CFG",
    "label.shift": "Shift",
    "label.denoise": "降噪",
    "label.sampler": "采样器",
    "label.scheduler": "调度器",
    "label.enabled": "启用",
    "label.followMainSampler": "跟随主采样器",
    "label.scaleBy": "放大",
    "label.maxLongEdge": "最长边",
    "label.face": "面部",
    "label.eye": "眼睛",
    "label.size": "尺寸",
    "button.randomEach": "每次随机",
    "button.newFixed": "新固定随机",
    "button.useLast": "Last Queued: {seed}",
    "button.useLastNone": "Last Queued: -",
    "button.samplerDetails": "采样器详情...",
    "button.highresSettings": "Highres 设置",
    "button.detailerSettings": "Detailer 设置",
    "button.advancedOptions": "高级选项...",
    "button.saveOn": "保存选项: ON",
    "button.saveOff": "保存选项: OFF",
    "button.moveUp": "上移",
    "button.moveDown": "下移",
    "button.addCivitaiFetcher": "+ 添加 Civitai Hash Fetcher",
    "button.remove": "删除",
    "text.previewTitle": "生成图像预览",
    "text.previewSubtitle": "此区域专用于该节点输出预览。",
    "text.highresDisabled": "启用 Highres 后显示放大和第二次采样基础设置。",
    "text.detailerDisabled": "启用 Detailer 后显示可排序的处理块。",
    "text.inheritsMainSampler": "使用主 CFG、采样器和调度器。",
    "text.usesStageSamplerOverride": "使用弹窗中保存的阶段专用 CFG、采样器和调度器。",
    "text.civitaiHashPreview": "将以 {model}:AutoV3 形式追加。",
    "tip.fieldGeneric": "{label} 设置。该值会随节点工作流保存。",
    "tip.additionalHashes": "Image Saver additional_hashes 手动字符串。支持 Name:HASH、HASH:Weight、Name:HASH:Weight。",
    "tip.hashBundles": "追加到 Image Saver additional_hashes 的手动哈希片段。",
    "tip.civitaiHashFetchers": "排队时运行 Civitai Hash Fetcher (Image Saver)，并将 model_name:AutoV3 追加到 additional_hashes。",
    "tip.civitaiUsername": "传给 Civitai Hash Fetcher 的 Civitai 用户名。",
    "tip.civitaiModelName": "Civitai 模型名，也会用作 Name:Hash 的 Name。",
    "tip.civitaiVersion": "传给 Civitai Hash Fetcher 的可选版本关键词。",
    "tip.mode": "显示当前采样后端和启用的特殊采样补丁。",
    "tip.seed": "发送到队列的种子。-1 会在排队时解析为新的随机种子。",
    "tip.randomEach": "将种子设为 -1，让每次排队使用新的随机种子。",
    "tip.newFixed": "立即生成一个随机种子并固定使用。",
    "tip.useLast": "复用此节点上次排队时解析出的真实种子。",
    "tip.steps": "第一次采样步数。紧凑滑条范围为 1 到 75。",
    "tip.cfg": "第一次 CFG 值。范围为 1.0 到 10.0。",
    "tip.shift": "AuraFlow 模型采样 Shift。始终应用，3.0 是 Anima model 推荐默认值。",
    "tip.denoise": "第一次采样的降噪强度。",
    "tip.sampler": "第一次使用的 ComfyUI 采样器名称。",
    "tip.scheduler": "第一次使用的 ComfyUI 调度器。",
    "tip.highresEnabled": "放大第一次图像后执行第二次采样。",
    "tip.highresFollow": "启用时，Highres 使用主 CFG、采样器和调度器。",
    "tip.highresScale": "Highres 第二次采样前的放大倍率。",
    "tip.highresMaxEdge": "放大后的最长边上限。0 表示不限制。",
    "tip.highresSteps": "Highres 第二次采样步数。",
    "tip.highresDenoise": "Highres 第二次采样的降噪强度。",
    "tip.detailerEnabled": "生成后运行 SAM3 和 Impact Detailer 阶段。",
    "tip.detailerBlock": "每个块都可单独启用、排序和调整。",
    "tip.detailerFollow": "启用时，此 Detailer 块跟随主采样器设置。",
    "tip.detailerSteps": "此块的 Impact Detailer 采样步数。",
    "tip.detailerDenoise": "此块的 Impact Detailer 降噪强度。",
    "tip.detailerOrder": "移动此图像处理块的执行顺序。",
    "tip.detailerName": "此 detailer tab 的显示名称，会随 workflow 保存用于 UI 管理。",
    "tip.samplerDetails": "打开采样后端、Mod Guidance 和 Spectrum 选项。",
    "tip.highresSettings": "打开 Highres 放大和优化选项。",
    "tip.detailerSettings": "打开 SAM3 和 Impact Detailer 全部选项。",
    "tip.advancedOptions": "打开模型补丁、优化和基于 Prompt Data 的高级选项。",
    "tip.saveOptions": "打开图像保存和元数据选项。",
    "tip.size": "此节点最近生成图像的尺寸。",
  },
};

const AIO_TOOLTIP_TEXT = {
  en: {
    "button.close": "Close",
    "button.cancel": "Cancel",
    "button.apply": "Apply",
    "tip.inputUnetDtype": "Weight dtype used when Easy Use Anima Input loads the diffusion model. Keep default unless VRAM or speed tuning requires another dtype.",
    "tip.inputClipDevice": "Device preference for loading CLIP. CPU can reduce VRAM use at the cost of slower prompt encoding.",
    "tip.seedMode": "After queue behavior for the seed value. This mirrors rgthree Seed controls.",
    "tip.kjFp16Accum": "Applies KJNodes FP16 accumulation patch to the model before sampling.",
    "tip.kjSageMode": "Selects the KJNodes SageAttention patch implementation. Disabled leaves attention unchanged.",
    "tip.kjSageCompile": "Allows SageAttention to participate in compile-related optimization when the selected KJNodes patch supports it.",
    "tip.torchCompileEnabled": "Runs KJNodes TorchCompileModelAdvanced before sampling. First run can be slower while graphs compile.",
    "tip.torchCompileBackend": "Backend passed to torch.compile through KJNodes.",
    "tip.torchCompileFullgraph": "Requests full-graph compilation. Use only when the model path is stable enough to compile fully.",
    "tip.torchCompileMode": "torch.compile tuning profile. Max-autotune can improve later runs but increases compile time.",
    "tip.torchCompileDynamic": "Dynamic-shape setting passed to torch.compile.",
    "tip.torchCompileBlocks": "Compile only transformer blocks instead of the whole model wrapper.",
    "tip.torchCompileCache": "Torch Dynamo cache size limit used by the compile node.",
    "tip.torchCompileDebug": "Enables debug compile keys in KJNodes for troubleshooting compile cache behavior.",
    "tip.torchCompileVram": "Disables ComfyUI dynamic VRAM handling around compiled model execution when enabled.",
    "tip.samplerBackend": "Selects the actual first-pass execution path. Model patches selected in Advanced Options are applied before this backend runs. SPD/SPEED is Euler-only, so its sampler is normalized to euler.",
    "warning.optionalDependencyMissing": "{backend} is locked because {pack} is not installed.",
    "tip.modMode": "Controls whether Mod Guidance follows prompt_data, is forced on, or is disabled.",
    "tip.modProfile": "Preset layer profile for Anima Mod Guidance. Off disables Mod Guidance even when prompt_data asks for it.",
    "tip.modAdapter": "Adapter name passed to Spectrum Mod Guidance. Auto-download default uses the node pack default adapter.",
    "tip.modW": "Main Mod Guidance strength sent to the integrated Spectrum sampler.",
    "tip.modStartLayer": "First transformer layer affected by Mod Guidance.",
    "tip.modEndLayer": "Last transformer layer affected by Mod Guidance.",
    "tip.modTaper": "Number of taper layers used to fade Mod Guidance.",
    "tip.modTaperScale": "Strength scale applied during the taper portion.",
    "tip.modFinalW": "Final-layer Mod Guidance strength override.",
    "tip.spectrumEnabled": "For Comfy KSampler mode, applies DiT Spectrum Patch before sampling. Integrated Spectrum sampler modes use their own Spectrum controls.",
    "tip.spectrumWindow": "Spectrum window size used by DiTSpectrumPatchAdvanced or SpectrumKSamplerAdvanced.",
    "tip.spectrumFlex": "Flexible window ratio for Spectrum forecast sampling.",
    "tip.spectrumWarmup": "Number of early steps before Spectrum forecast correction starts.",
    "tip.spectrumTail": "Number of actual sampler steps kept near the end of the schedule.",
    "tip.spectrumBlend": "Blend weight between forecast and actual sampling behavior.",
    "tip.spectrumCheby": "Chebyshev polynomial degree used by the Spectrum forecast path.",
    "tip.spectrumRidge": "Ridge regularization lambda for Spectrum forecast fitting.",
    "tip.spectrumCompat": "Compatibility policy for Spectrum patch behavior. Conservative is safest for mixed sampler setups.",
    "tip.correctionsEnabled": "Enables Spectrum advanced corrections such as DCW, SMC-CFG, CFG++, and FSG.",
    "tip.dcwMode": "DCW correction mode passed to Spectrum correction nodes.",
    "tip.dcwLambda": "DCW correction strength.",
    "tip.dcwBand": "Frequency band mask used by DCW correction.",
    "tip.smcCfg": "Enables adaptive SMC-CFG correction.",
    "tip.smcAlpha": "Adaptive SMC alpha value for Spectrum correction.",
    "tip.smcLambda": "SMC-CFG lambda strength.",
    "tip.cfgpp": "Enables CFG++ correction in Spectrum correction nodes.",
    "tip.cfgppLambda": "CFG++ lambda strength.",
    "tip.fsg": "Enables FSG correction in Spectrum correction nodes.",
    "tip.spdScale": "SPD/SPEED scale value sent to SpectrumSPDKSampler.",
    "tip.spdSigma": "SPD/SPEED sigma value sent to SpectrumSPDKSampler.",
    "tip.daveEnabled": "Apply the optional AnimaDAVE model patch before sampler execution.",
    "tip.daveMask": "DAVE pool mask file passed to AnimaDAVE. The bundled default is dave_alpha.npz.",
    "tip.daveStrength": "DAVE DC-removal dose. Start near 0.30, or sweep lower values for layout diversity.",
    "tip.daveTau": "Early denoising fraction where DAVE is active. Keep at or below 0.10 for legibility.",
    "tip.highresMethod": "Upscale method used before the Highres second pass.",
    "tip.highresMultiple": "Snaps Highres dimensions to this multiple before resampling.",
    "tip.detailerPrompt": "SAM3 text prompt used to detect the target region for this block.",
    "tip.detailerCount": "Maximum number of detected regions to process.",
    "tip.detailerThreshold": "SAM3 detection threshold. Higher values keep only stronger detections.",
    "tip.detailerRefine": "SAM3 mask refinement iterations before MaskToSEGS conversion.",
    "tip.detailerIndividual": "Processes detected masks independently instead of only as one combined mask.",
    "tip.detailerCombined": "Adds a combined SEGS entry from all detected masks.",
    "tip.detailerCropFactor": "Impact MaskToSEGS crop factor around the detected region.",
    "tip.detailerBboxFill": "Fills the bounding box area during MaskToSEGS conversion.",
    "tip.detailerDropSize": "Drops detected regions smaller than this size.",
    "tip.detailerContourFill": "Fills mask contours before detailer sampling.",
    "tip.detailerGuideSize": "Impact Detailer guide size for the inpaint crop.",
    "tip.detailerMaxSize": "Maximum Impact Detailer processing size.",
    "tip.detailerFeather": "Feather amount around the inpaint mask.",
    "tip.detailerNoiseMask": "Use a noise mask for detailer sampling.",
    "tip.detailerForceInpaint": "Forces inpaint behavior for the detailer crop.",
    "tip.detailerMaskFeather": "Extra feather applied to the noise mask.",
    "tip.detailerCycle": "Number of Impact Detailer cycles for this target.",
    "tip.detailerAlignment": "Aligns detailer crop sizes. 32 is the Anima default to avoid odd crop dimensions.",
    "tip.detailerCheckpoint": "SAM3 checkpoint loaded by the AiO detailer stage.",
    "tip.saveEnabled": "Controls whether this output node saves the final image during queue execution.",
    "tip.saveBackend": "Image Saver writes metadata-rich files. Comfy SaveImage uses ComfyUI's built-in saver.",
    "tip.saveFilename": "Filename pattern sent to Image Saver. Image Saver tokens such as %time and %basemodelname are preserved.",
    "tip.savePath": "Output subfolder passed to Image Saver.",
    "tip.saveExtension": "Image file extension for Image Saver output.",
    "tip.saveQuality": "JPEG/WebP quality value passed to Image Saver.",
    "tip.saveLosslessWebp": "Writes lossless WebP when WebP output is selected.",
    "tip.saveOptimizePng": "Runs PNG optimization when PNG output is selected.",
    "tip.saveCounter": "Image Saver counter value.",
    "tip.saveTimeFormat": "strftime-style time format used by Image Saver filename tokens.",
    "tip.saveClipSkip": "Clip skip metadata value written by Image Saver.",
    "tip.saveEmbedWorkflow": "Embeds the ComfyUI workflow in the saved image so it can be reloaded.",
    "tip.saveWorkflowJson": "Also writes a sidecar workflow JSON file.",
    "tip.saveCivitaiData": "Lets Image Saver download and embed Civitai model metadata.",
    "tip.saveEasyRemix": "Enables Image Saver easy-remix metadata fields.",
    "tip.saveCustom": "Custom metadata text passed directly to Image Saver.",
    "tip.artistMixMode": "Controls how artist tags from prompt_data are mixed into conditioning.",
    "tip.artistMixStart": "Start percent for late or scheduled artist-mix modes.",
    "tip.artistMixStrength": "Strength multiplier for artist-mix conditioning.",
  },
  ko: {
    "button.close": "닫기",
    "button.cancel": "취소",
    "button.apply": "적용",
    "tip.inputUnetDtype": "Easy Use Anima Input이 디퓨전 모델을 로드할 때 사용할 weight dtype입니다. VRAM/속도 튜닝이 필요 없으면 default를 유지합니다.",
    "tip.inputClipDevice": "CLIP 로드 장치 설정입니다. CPU는 VRAM을 줄일 수 있지만 프롬프트 인코딩이 느려질 수 있습니다.",
    "tip.seedMode": "큐 실행 후 시드 처리 방식입니다. rgthree Seed 컨트롤과 같은 의미로 동작합니다.",
    "tip.kjFp16Accum": "샘플링 전에 KJNodes FP16 accumulation 모델 패치를 적용합니다.",
    "tip.kjSageMode": "KJNodes SageAttention 패치 구현을 선택합니다. disabled는 attention을 변경하지 않습니다.",
    "tip.kjSageCompile": "선택한 SageAttention 패치가 지원할 때 compile 최적화에 포함되도록 허용합니다.",
    "tip.torchCompileEnabled": "샘플링 전에 KJNodes TorchCompileModelAdvanced를 실행합니다. 첫 실행은 컴파일 때문에 느릴 수 있습니다.",
    "tip.torchCompileBackend": "KJNodes를 통해 torch.compile에 전달할 backend입니다.",
    "tip.torchCompileFullgraph": "fullgraph 컴파일을 요청합니다. 모델 경로가 안정적일 때만 사용합니다.",
    "tip.torchCompileMode": "torch.compile 튜닝 프로필입니다. max-autotune은 이후 실행을 빠르게 할 수 있지만 컴파일 시간이 늘어납니다.",
    "tip.torchCompileDynamic": "torch.compile에 전달할 dynamic shape 설정입니다.",
    "tip.torchCompileBlocks": "모델 전체 대신 transformer block만 컴파일합니다.",
    "tip.torchCompileCache": "compile 노드가 사용할 Torch Dynamo cache size limit입니다.",
    "tip.torchCompileDebug": "컴파일 캐시 문제를 추적하기 위한 KJNodes debug compile keys를 켭니다.",
    "tip.torchCompileVram": "켜면 compiled model 실행 중 ComfyUI dynamic VRAM 처리를 끕니다.",
    "tip.samplerBackend": "실제 1차 샘플링 경로를 선택합니다. Advanced Options에서 선택한 모델 패치는 이 백엔드 실행 전에 적용됩니다. SPD/SPEED는 Euler 전용이라 내부 sampler는 euler로 정규화됩니다.",
    "warning.optionalDependencyMissing": "{pack}이 설치되지 않아 {backend} 옵션을 잠갔습니다.",
    "tip.modMode": "Mod Guidance를 prompt_data에 따르게 할지, 강제로 켤지, 끌지 정합니다.",
    "tip.modProfile": "Anima Mod Guidance 레이어 프리셋입니다. off는 prompt_data가 켜져 있어도 Mod Guidance를 비활성화합니다.",
    "tip.modAdapter": "Spectrum Mod Guidance에 전달할 adapter입니다. auto-download default는 노드팩 기본 adapter를 사용합니다.",
    "tip.modW": "통합 Spectrum 샘플러에 전달할 Mod Guidance 주 강도입니다.",
    "tip.modStartLayer": "Mod Guidance를 적용할 첫 transformer layer입니다.",
    "tip.modEndLayer": "Mod Guidance를 적용할 마지막 transformer layer입니다.",
    "tip.modTaper": "Mod Guidance를 서서히 줄일 taper layer 수입니다.",
    "tip.modTaperScale": "taper 구간에 적용할 강도 배율입니다.",
    "tip.modFinalW": "마지막 layer의 Mod Guidance 강도 override입니다.",
    "tip.spectrumEnabled": "Comfy KSampler 모드에서 샘플링 전에 DiT Spectrum Patch를 적용합니다. 통합 Spectrum 모드는 자체 Spectrum 설정을 사용합니다.",
    "tip.spectrumWindow": "DiTSpectrumPatchAdvanced 또는 SpectrumKSamplerAdvanced의 window size입니다.",
    "tip.spectrumFlex": "Spectrum forecast sampling의 flexible window 비율입니다.",
    "tip.spectrumWarmup": "Spectrum forecast 보정이 시작되기 전 warmup step 수입니다.",
    "tip.spectrumTail": "스케줄 마지막에 실제 sampler step으로 유지할 step 수입니다.",
    "tip.spectrumBlend": "forecast와 실제 sampling 동작의 blend weight입니다.",
    "tip.spectrumCheby": "Spectrum forecast 경로에서 사용하는 Chebyshev polynomial degree입니다.",
    "tip.spectrumRidge": "Spectrum forecast fitting의 ridge regularization lambda입니다.",
    "tip.spectrumCompat": "Spectrum patch 호환성 정책입니다. conservative가 혼합 샘플러 구성에서 가장 안전합니다.",
    "tip.correctionsEnabled": "DCW, SMC-CFG, CFG++, FSG 같은 Spectrum 고급 보정을 켭니다.",
    "tip.dcwMode": "Spectrum correction 노드에 전달할 DCW correction mode입니다.",
    "tip.dcwLambda": "DCW correction 강도입니다.",
    "tip.dcwBand": "DCW correction에 사용할 frequency band mask입니다.",
    "tip.smcCfg": "adaptive SMC-CFG 보정을 켭니다.",
    "tip.smcAlpha": "Spectrum correction의 adaptive SMC alpha 값입니다.",
    "tip.smcLambda": "SMC-CFG lambda 강도입니다.",
    "tip.cfgpp": "Spectrum correction 노드의 CFG++ 보정을 켭니다.",
    "tip.cfgppLambda": "CFG++ lambda 강도입니다.",
    "tip.fsg": "Spectrum correction 노드의 FSG 보정을 켭니다.",
    "tip.spdScale": "SpectrumSPDKSampler에 전달할 SPD/SPEED scale 값입니다.",
    "tip.spdSigma": "SpectrumSPDKSampler에 전달할 SPD/SPEED sigma 값입니다.",
    "tip.daveEnabled": "샘플러 실행 전에 선택 AnimaDAVE 모델 패치를 적용합니다.",
    "tip.daveMask": "AnimaDAVE에 전달할 DAVE pool mask 파일입니다. 기본 번들 파일은 dave_alpha.npz입니다.",
    "tip.daveStrength": "DAVE DC 제거 강도입니다. 기본은 0.30이며, 레이아웃 다양성 비교는 더 낮은 값부터 스윕합니다.",
    "tip.daveTau": "DAVE가 활성화되는 초기 denoising 비율입니다. 가독성을 위해 0.10 이하를 권장합니다.",
    "tip.highresMethod": "Highres 2차 패스 전에 사용할 업스케일 방법입니다.",
    "tip.highresMultiple": "Highres 크기를 이 배수에 맞춰 보정합니다.",
    "tip.detailerPrompt": "이 블럭의 대상 영역을 찾기 위해 SAM3에 전달할 텍스트 프롬프트입니다.",
    "tip.detailerCount": "처리할 최대 감지 영역 개수입니다.",
    "tip.detailerThreshold": "SAM3 감지 threshold입니다. 높을수록 강한 감지만 남습니다.",
    "tip.detailerRefine": "MaskToSEGS 변환 전 SAM3 mask refinement 반복 수입니다.",
    "tip.detailerIndividual": "감지된 mask를 하나씩 독립 처리합니다.",
    "tip.detailerCombined": "감지된 모든 mask를 합친 SEGS 항목을 추가합니다.",
    "tip.detailerCropFactor": "감지 영역 주변 Impact MaskToSEGS crop factor입니다.",
    "tip.detailerBboxFill": "MaskToSEGS 변환 중 bounding box 영역을 채웁니다.",
    "tip.detailerDropSize": "이 크기보다 작은 감지 영역을 버립니다.",
    "tip.detailerContourFill": "detailer 샘플링 전 mask contour를 채웁니다.",
    "tip.detailerGuideSize": "inpaint crop에 사용할 Impact Detailer guide size입니다.",
    "tip.detailerMaxSize": "Impact Detailer 처리 최대 크기입니다.",
    "tip.detailerFeather": "inpaint mask 경계 feather 값입니다.",
    "tip.detailerNoiseMask": "detailer 샘플링에 noise mask를 사용합니다.",
    "tip.detailerForceInpaint": "detailer crop을 inpaint 방식으로 강제 처리합니다.",
    "tip.detailerMaskFeather": "noise mask에 추가 feather를 적용합니다.",
    "tip.detailerCycle": "이 대상에 실행할 Impact Detailer cycle 수입니다.",
    "tip.detailerAlignment": "detailer crop 크기를 정렬합니다. Anima 기본값은 홀수 crop을 피하는 32입니다.",
    "tip.detailerCheckpoint": "AiO 디테일러 단계에서 로드할 SAM3 checkpoint입니다.",
    "tip.saveEnabled": "큐 실행 중 이 출력 노드가 최종 이미지를 저장할지 정합니다.",
    "tip.saveBackend": "Image Saver는 메타데이터가 풍부한 저장을 수행합니다. Comfy SaveImage는 기본 저장 노드를 사용합니다.",
    "tip.saveFilename": "Image Saver에 전달할 filename 패턴입니다. %time, %basemodelname 같은 Image Saver 토큰을 유지합니다.",
    "tip.savePath": "Image Saver에 전달할 출력 하위 폴더입니다.",
    "tip.saveExtension": "Image Saver 출력 이미지 확장자입니다.",
    "tip.saveQuality": "Image Saver에 전달할 JPEG/WebP quality 값입니다.",
    "tip.saveLosslessWebp": "WebP 출력 선택 시 lossless WebP로 저장합니다.",
    "tip.saveOptimizePng": "PNG 출력 선택 시 PNG 최적화를 실행합니다.",
    "tip.saveCounter": "Image Saver counter 값입니다.",
    "tip.saveTimeFormat": "Image Saver filename 토큰에 사용할 strftime 형식입니다.",
    "tip.saveClipSkip": "Image Saver가 기록할 clip skip 메타데이터 값입니다.",
    "tip.saveEmbedWorkflow": "저장 이미지에 ComfyUI workflow를 임베드해 다시 불러올 수 있게 합니다.",
    "tip.saveWorkflowJson": "workflow JSON sidecar 파일도 같이 저장합니다.",
    "tip.saveCivitaiData": "Image Saver가 Civitai 모델 메타데이터를 다운로드해 임베드하도록 합니다.",
    "tip.saveEasyRemix": "Image Saver easy-remix 메타데이터 필드를 켭니다.",
    "tip.saveCustom": "Image Saver에 그대로 전달할 custom metadata입니다.",
    "tip.artistMixMode": "prompt_data의 작가 태그를 conditioning에 혼합하는 방식을 정합니다.",
    "tip.artistMixStart": "late/scheduled artist mix 모드의 시작 percent입니다.",
    "tip.artistMixStrength": "artist mix conditioning 강도 배율입니다.",
  },
  ja: {
    "button.close": "閉じる",
    "button.cancel": "キャンセル",
    "button.apply": "適用",
    "tip.inputUnetDtype": "Easy Use Anima Input が diffusion model を読み込むときの weight dtype です。VRAM や速度調整が不要なら default を使います。",
    "tip.inputClipDevice": "CLIP の読み込みデバイスです。CPU は VRAM を抑えますが、プロンプトエンコードが遅くなります。",
    "tip.seedMode": "キュー後のシード制御です。rgthree Seed と同じ考え方で動作します。",
    "tip.kjFp16Accum": "サンプリング前に KJNodes FP16 accumulation パッチをモデルへ適用します。",
    "tip.kjSageMode": "KJNodes SageAttention の実装を選択します。disabled は attention を変更しません。",
    "tip.kjSageCompile": "選択した SageAttention パッチが対応する場合、compile 最適化への参加を許可します。",
    "tip.torchCompileEnabled": "サンプリング前に KJNodes TorchCompileModelAdvanced を実行します。初回は compile により遅くなる場合があります。",
    "tip.torchCompileBackend": "KJNodes 経由で torch.compile に渡す backend です。",
    "tip.torchCompileFullgraph": "fullgraph compile を要求します。モデル経路が安定している場合のみ使用してください。",
    "tip.torchCompileMode": "torch.compile の調整プロファイルです。max-autotune は後続実行を速くできますが compile 時間が増えます。",
    "tip.torchCompileDynamic": "torch.compile に渡す dynamic shape 設定です。",
    "tip.torchCompileBlocks": "モデル全体ではなく transformer block のみを compile します。",
    "tip.torchCompileCache": "compile ノードが使う Torch Dynamo cache size limit です。",
    "tip.torchCompileDebug": "compile cache の確認用に KJNodes debug compile keys を有効化します。",
    "tip.torchCompileVram": "有効時、compiled model 実行中の ComfyUI dynamic VRAM 処理を無効化します。",
    "tip.samplerBackend": "一回目の実行経路を選択します。Advanced Options で選んだ model patch は、この backend 実行前に適用されます。SPD/SPEED は Euler 専用のため、sampler は内部で euler に正規化されます。",
    "warning.optionalDependencyMissing": "{pack} が未インストールのため {backend} をロックしました。",
    "tip.modMode": "Mod Guidance を prompt_data に従わせるか、強制有効または無効にするかを選択します。",
    "tip.modProfile": "Anima Mod Guidance の layer profile です。off は prompt_data が有効でも Mod Guidance を無効化します。",
    "tip.modAdapter": "Spectrum Mod Guidance に渡す adapter です。auto-download default は node pack の既定 adapter を使います。",
    "tip.modW": "統合 Spectrum sampler に渡す Mod Guidance の主強度です。",
    "tip.modStartLayer": "Mod Guidance を適用する最初の transformer layer です。",
    "tip.modEndLayer": "Mod Guidance を適用する最後の transformer layer です。",
    "tip.modTaper": "Mod Guidance をフェードする taper layer 数です。",
    "tip.modTaperScale": "taper 区間に適用する強度スケールです。",
    "tip.modFinalW": "最終 layer の Mod Guidance 強度 override です。",
    "tip.spectrumEnabled": "Comfy KSampler mode でサンプリング前に DiT Spectrum Patch を適用します。統合 Spectrum mode は専用の Spectrum 設定を使います。",
    "tip.spectrumWindow": "DiTSpectrumPatchAdvanced または SpectrumKSamplerAdvanced の window size です。",
    "tip.spectrumFlex": "Spectrum forecast sampling の flexible window 比率です。",
    "tip.spectrumWarmup": "Spectrum forecast 補正を開始する前の warmup step 数です。",
    "tip.spectrumTail": "スケジュール末尾で実 sampler step として残す step 数です。",
    "tip.spectrumBlend": "forecast と実 sampling 動作の blend weight です。",
    "tip.spectrumCheby": "Spectrum forecast 経路で使う Chebyshev polynomial degree です。",
    "tip.spectrumRidge": "Spectrum forecast fitting の ridge regularization lambda です。",
    "tip.spectrumCompat": "Spectrum patch の互換性ポリシーです。混在構成では conservative が最も安全です。",
    "tip.correctionsEnabled": "DCW、SMC-CFG、CFG++、FSG などの Spectrum 高度補正を有効化します。",
    "tip.dcwMode": "Spectrum correction node に渡す DCW correction mode です。",
    "tip.dcwLambda": "DCW correction の強度です。",
    "tip.dcwBand": "DCW correction で使う frequency band mask です。",
    "tip.smcCfg": "adaptive SMC-CFG 補正を有効化します。",
    "tip.smcAlpha": "Spectrum correction の adaptive SMC alpha 値です。",
    "tip.smcLambda": "SMC-CFG lambda 強度です。",
    "tip.cfgpp": "Spectrum correction node の CFG++ 補正を有効化します。",
    "tip.cfgppLambda": "CFG++ lambda 強度です。",
    "tip.fsg": "Spectrum correction node の FSG 補正を有効化します。",
    "tip.spdScale": "SpectrumSPDKSampler に渡す SPD/SPEED scale 値です。",
    "tip.spdSigma": "SpectrumSPDKSampler に渡す SPD/SPEED sigma 値です。",
    "tip.daveEnabled": "Sampler 実行前に任意の AnimaDAVE model patch を適用します。",
    "tip.daveMask": "AnimaDAVE に渡す DAVE pool mask ファイルです。既定の同梱ファイルは dave_alpha.npz です。",
    "tip.daveStrength": "DAVE の DC 除去量です。既定は 0.30、レイアウト多様性の比較は低めの値から始めます。",
    "tip.daveTau": "DAVE が有効になる初期 denoising 比率です。可読性のため 0.10 以下を推奨します。",
    "tip.highresMethod": "Highres 二回目パス前に使う upscaler 方式です。",
    "tip.highresMultiple": "Highres の寸法をこの倍数に揃えます。",
    "tip.detailerPrompt": "この block の対象領域を検出するため SAM3 に渡す text prompt です。",
    "tip.detailerCount": "処理する検出領域の最大数です。",
    "tip.detailerThreshold": "SAM3 検出 threshold です。高いほど強い検出だけを残します。",
    "tip.detailerRefine": "MaskToSEGS 変換前の SAM3 mask refinement 回数です。",
    "tip.detailerIndividual": "検出 mask を個別に処理します。",
    "tip.detailerCombined": "検出 mask 全体を結合した SEGS を追加します。",
    "tip.detailerCropFactor": "検出領域周辺の Impact MaskToSEGS crop factor です。",
    "tip.detailerBboxFill": "MaskToSEGS 変換時に bounding box 領域を塗りつぶします。",
    "tip.detailerDropSize": "このサイズ未満の検出領域を破棄します。",
    "tip.detailerContourFill": "detailer sampling 前に mask contour を塗りつぶします。",
    "tip.detailerGuideSize": "inpaint crop に使う Impact Detailer guide size です。",
    "tip.detailerMaxSize": "Impact Detailer の最大処理サイズです。",
    "tip.detailerFeather": "inpaint mask 境界の feather 量です。",
    "tip.detailerNoiseMask": "detailer sampling に noise mask を使用します。",
    "tip.detailerForceInpaint": "detailer crop を inpaint 処理に強制します。",
    "tip.detailerMaskFeather": "noise mask に追加 feather を適用します。",
    "tip.detailerCycle": "この対象で実行する Impact Detailer cycle 数です。",
    "tip.detailerAlignment": "detailer crop size を整列します。Anima 既定は奇数 crop を避ける 32 です。",
    "tip.detailerCheckpoint": "AiO detailer stage で読み込む SAM3 checkpoint です。",
    "tip.saveEnabled": "キュー実行中、この出力 node が最終画像を保存するかを制御します。",
    "tip.saveBackend": "Image Saver は metadata 付き保存を行います。Comfy SaveImage は標準 saver を使います。",
    "tip.saveFilename": "Image Saver に渡す filename pattern です。%time や %basemodelname などの token を保持します。",
    "tip.savePath": "Image Saver に渡す出力 subfolder です。",
    "tip.saveExtension": "Image Saver の出力画像拡張子です。",
    "tip.saveQuality": "Image Saver に渡す JPEG/WebP quality 値です。",
    "tip.saveLosslessWebp": "WebP 出力時に lossless WebP で保存します。",
    "tip.saveOptimizePng": "PNG 出力時に PNG optimization を実行します。",
    "tip.saveCounter": "Image Saver counter 値です。",
    "tip.saveTimeFormat": "Image Saver filename token に使う strftime 形式です。",
    "tip.saveClipSkip": "Image Saver が記録する clip skip metadata 値です。",
    "tip.saveEmbedWorkflow": "保存画像に ComfyUI workflow を埋め込み、再読み込み可能にします。",
    "tip.saveWorkflowJson": "workflow JSON sidecar も保存します。",
    "tip.saveCivitaiData": "Image Saver が Civitai model metadata を取得して埋め込むようにします。",
    "tip.saveEasyRemix": "Image Saver easy-remix metadata fields を有効化します。",
    "tip.saveCustom": "Image Saver にそのまま渡す custom metadata です。",
    "tip.artistMixMode": "prompt_data の artist tags を conditioning に混合する方式です。",
    "tip.artistMixStart": "late/scheduled artist mix mode の開始 percent です。",
    "tip.artistMixStrength": "artist mix conditioning の強度倍率です。",
  },
  zh: {
    "button.close": "关闭",
    "button.cancel": "取消",
    "button.apply": "应用",
    "tip.inputUnetDtype": "Easy Use Anima Input 加载 diffusion model 时使用的 weight dtype。除非需要显存或速度调优，否则保持 default。",
    "tip.inputClipDevice": "CLIP 加载设备。CPU 可减少显存占用，但会降低提示词编码速度。",
    "tip.seedMode": "排队后的种子控制方式，行为与 rgthree Seed 控件一致。",
    "tip.kjFp16Accum": "采样前对模型应用 KJNodes FP16 accumulation patch。",
    "tip.kjSageMode": "选择 KJNodes SageAttention patch 实现。disabled 不改变 attention。",
    "tip.kjSageCompile": "所选 SageAttention patch 支持时，允许参与 compile 优化。",
    "tip.torchCompileEnabled": "采样前运行 KJNodes TorchCompileModelAdvanced。首次运行可能因编译变慢。",
    "tip.torchCompileBackend": "通过 KJNodes 传给 torch.compile 的 backend。",
    "tip.torchCompileFullgraph": "请求 fullgraph compile。仅在模型路径足够稳定时使用。",
    "tip.torchCompileMode": "torch.compile 调优配置。max-autotune 可加速后续运行，但会增加编译时间。",
    "tip.torchCompileDynamic": "传给 torch.compile 的 dynamic shape 设置。",
    "tip.torchCompileBlocks": "只编译 transformer blocks，而不是整个模型包装。",
    "tip.torchCompileCache": "compile 节点使用的 Torch Dynamo cache size limit。",
    "tip.torchCompileDebug": "启用 KJNodes debug compile keys，用于排查 compile cache 行为。",
    "tip.torchCompileVram": "启用后，在 compiled model 执行期间关闭 ComfyUI dynamic VRAM 处理。",
    "tip.samplerBackend": "选择第一次采样的实际执行路径。Advanced Options 中选择的 model patch 会在此 backend 执行前应用。SPD/SPEED 仅支持 Euler，因此内部 sampler 会规范化为 euler。",
    "warning.optionalDependencyMissing": "{pack} 未安装，因此已锁定 {backend} 选项。",
    "tip.modMode": "选择 Mod Guidance 跟随 prompt_data、强制开启或关闭。",
    "tip.modProfile": "Anima Mod Guidance layer profile。off 会禁用 Mod Guidance，即使 prompt_data 要求启用。",
    "tip.modAdapter": "传给 Spectrum Mod Guidance 的 adapter。auto-download default 使用节点包默认 adapter。",
    "tip.modW": "传给集成 Spectrum sampler 的 Mod Guidance 主强度。",
    "tip.modStartLayer": "Mod Guidance 影响的第一个 transformer layer。",
    "tip.modEndLayer": "Mod Guidance 影响的最后一个 transformer layer。",
    "tip.modTaper": "Mod Guidance 渐隐使用的 taper layer 数。",
    "tip.modTaperScale": "taper 区间的强度倍率。",
    "tip.modFinalW": "最终 layer 的 Mod Guidance 强度 override。",
    "tip.spectrumEnabled": "在 Comfy KSampler mode 中，采样前应用 DiT Spectrum Patch。集成 Spectrum mode 使用自己的 Spectrum 设置。",
    "tip.spectrumWindow": "DiTSpectrumPatchAdvanced 或 SpectrumKSamplerAdvanced 的 window size。",
    "tip.spectrumFlex": "Spectrum forecast sampling 的 flexible window 比例。",
    "tip.spectrumWarmup": "Spectrum forecast correction 开始前的 warmup step 数。",
    "tip.spectrumTail": "调度末尾保留为实际 sampler step 的步数。",
    "tip.spectrumBlend": "forecast 与实际 sampling 行为的 blend weight。",
    "tip.spectrumCheby": "Spectrum forecast 路径使用的 Chebyshev polynomial degree。",
    "tip.spectrumRidge": "Spectrum forecast fitting 的 ridge regularization lambda。",
    "tip.spectrumCompat": "Spectrum patch 兼容策略。混合采样器配置中 conservative 最安全。",
    "tip.correctionsEnabled": "启用 DCW、SMC-CFG、CFG++、FSG 等 Spectrum 高级校正。",
    "tip.dcwMode": "传给 Spectrum correction node 的 DCW correction mode。",
    "tip.dcwLambda": "DCW correction 强度。",
    "tip.dcwBand": "DCW correction 使用的 frequency band mask。",
    "tip.smcCfg": "启用 adaptive SMC-CFG correction。",
    "tip.smcAlpha": "Spectrum correction 的 adaptive SMC alpha 值。",
    "tip.smcLambda": "SMC-CFG lambda 强度。",
    "tip.cfgpp": "启用 Spectrum correction node 的 CFG++ correction。",
    "tip.cfgppLambda": "CFG++ lambda 强度。",
    "tip.fsg": "启用 Spectrum correction node 的 FSG correction。",
    "tip.spdScale": "传给 SpectrumSPDKSampler 的 SPD/SPEED scale 值。",
    "tip.spdSigma": "传给 SpectrumSPDKSampler 的 SPD/SPEED sigma 值。",
    "tip.daveEnabled": "在 sampler 执行前应用可选的 AnimaDAVE model patch。",
    "tip.daveMask": "传给 AnimaDAVE 的 DAVE pool mask 文件。默认内置文件是 dave_alpha.npz。",
    "tip.daveStrength": "DAVE DC removal 强度。默认 0.30；比较布局多样性时先从较低值扫起。",
    "tip.daveTau": "DAVE 生效的早期 denoising 比例。为保持可读性，建议不超过 0.10。",
    "tip.highresMethod": "Highres 第二次采样前使用的放大方法。",
    "tip.highresMultiple": "将 Highres 尺寸对齐到该倍数。",
    "tip.detailerPrompt": "传给 SAM3 的文本提示词，用于检测此 block 的目标区域。",
    "tip.detailerCount": "要处理的最大检测区域数。",
    "tip.detailerThreshold": "SAM3 检测 threshold。越高只保留越强的检测。",
    "tip.detailerRefine": "MaskToSEGS 转换前的 SAM3 mask refinement 次数。",
    "tip.detailerIndividual": "单独处理检测到的每个 mask。",
    "tip.detailerCombined": "添加由所有检测 mask 合并得到的 SEGS。",
    "tip.detailerCropFactor": "检测区域周围的 Impact MaskToSEGS crop factor。",
    "tip.detailerBboxFill": "MaskToSEGS 转换时填充 bounding box 区域。",
    "tip.detailerDropSize": "丢弃小于此尺寸的检测区域。",
    "tip.detailerContourFill": "detailer sampling 前填充 mask contour。",
    "tip.detailerGuideSize": "inpaint crop 使用的 Impact Detailer guide size。",
    "tip.detailerMaxSize": "Impact Detailer 最大处理尺寸。",
    "tip.detailerFeather": "inpaint mask 边缘 feather 值。",
    "tip.detailerNoiseMask": "detailer sampling 使用 noise mask。",
    "tip.detailerForceInpaint": "强制 detailer crop 使用 inpaint 行为。",
    "tip.detailerMaskFeather": "对 noise mask 应用额外 feather。",
    "tip.detailerCycle": "此目标运行的 Impact Detailer cycle 数。",
    "tip.detailerAlignment": "对齐 detailer crop size。Anima 默认 32，用于避免异常 crop 尺寸。",
    "tip.detailerCheckpoint": "AiO detailer stage 加载的 SAM3 checkpoint。",
    "tip.saveEnabled": "控制此输出节点在排队执行时是否保存最终图像。",
    "tip.saveBackend": "Image Saver 写入带丰富 metadata 的文件。Comfy SaveImage 使用 ComfyUI 内置 saver。",
    "tip.saveFilename": "传给 Image Saver 的 filename pattern。保留 %time、%basemodelname 等 token。",
    "tip.savePath": "传给 Image Saver 的输出子文件夹。",
    "tip.saveExtension": "Image Saver 输出图像扩展名。",
    "tip.saveQuality": "传给 Image Saver 的 JPEG/WebP quality 值。",
    "tip.saveLosslessWebp": "选择 WebP 输出时保存为 lossless WebP。",
    "tip.saveOptimizePng": "选择 PNG 输出时运行 PNG optimization。",
    "tip.saveCounter": "Image Saver counter 值。",
    "tip.saveTimeFormat": "Image Saver filename token 使用的 strftime 格式。",
    "tip.saveClipSkip": "Image Saver 写入的 clip skip metadata 值。",
    "tip.saveEmbedWorkflow": "将 ComfyUI workflow 嵌入保存图像，便于重新加载。",
    "tip.saveWorkflowJson": "同时保存 workflow JSON sidecar 文件。",
    "tip.saveCivitaiData": "让 Image Saver 下载并嵌入 Civitai model metadata。",
    "tip.saveEasyRemix": "启用 Image Saver easy-remix metadata fields。",
    "tip.saveCustom": "直接传给 Image Saver 的 custom metadata。",
    "tip.artistMixMode": "控制如何将 prompt_data 的 artist tags 混入 conditioning。",
    "tip.artistMixStart": "late/scheduled artist mix mode 的 start percent。",
    "tip.artistMixStrength": "artist mix conditioning 强度倍率。",
  },
};

for (const [language, entries] of Object.entries(AIO_TOOLTIP_TEXT)) {
  AIO_TEXT[language] = {
    ...AIO_TEXT.en,
    ...(AIO_TEXT[language] || {}),
    ...entries,
  };
}

const AIO_FIELD_TOOLTIP_KEYS = {
  "UNET weight dtype": "tip.inputUnetDtype",
  "CLIP device": "tip.inputClipDevice",
  "Seed": "tip.seed",
  "Seed mode": "tip.seedMode",
  "Steps": "tip.steps",
  "CFG": "tip.cfg",
  "AuraFlow shift": "tip.shift",
  "Denoise": "tip.denoise",
  "KJNodes FP16 accum": "tip.kjFp16Accum",
  "Mode": "tip.samplerBackend",
  "Allow compile": "tip.kjSageCompile",
  "Use Torch compile": "tip.torchCompileEnabled",
  "Backend": "tip.saveBackend",
  "Fullgraph": "tip.torchCompileFullgraph",
  "Dynamic": "tip.torchCompileDynamic",
  "Transformer blocks only": "tip.torchCompileBlocks",
  "Dynamo cache limit": "tip.torchCompileCache",
  "Debug keys": "tip.torchCompileDebug",
  "Disable dynamic VRAM": "tip.torchCompileVram",
  "Sampler": "tip.sampler",
  "Scheduler": "tip.scheduler",
  "Profile": "tip.modProfile",
  "Adapter": "tip.modAdapter",
  "Mod W": "tip.modW",
  "Start layer": "tip.modStartLayer",
  "End layer": "tip.modEndLayer",
  "Taper": "tip.modTaper",
  "Taper scale": "tip.modTaperScale",
  "Final W": "tip.modFinalW",
  "Block name": "tip.detailerName",
  "Use Spectrum patch": "tip.spectrumEnabled",
  "Spectrum patch": "tip.spectrumEnabled",
  "Window size": "tip.spectrumWindow",
  "Flex window": "tip.spectrumFlex",
  "Warmup steps": "tip.spectrumWarmup",
  "Warmup": "tip.spectrumWarmup",
  "Tail actual": "tip.spectrumTail",
  "Blend W": "tip.spectrumBlend",
  "Cheby degree": "tip.spectrumCheby",
  "Cheby": "tip.spectrumCheby",
  "Ridge lambda": "tip.spectrumRidge",
  "Compat policy": "tip.spectrumCompat",
  "Compat": "tip.spectrumCompat",
  "Use corrections": "tip.correctionsEnabled",
  "DCW mode": "tip.dcwMode",
  "DCW lambda": "tip.dcwLambda",
  "DCW band": "tip.dcwBand",
  "SMC-CFG": "tip.smcCfg",
  "SMC alpha": "tip.smcAlpha",
  "SMC lambda": "tip.smcLambda",
  "CFG++": "tip.cfgpp",
  "CFG++ lambda": "tip.cfgppLambda",
  "FSG": "tip.fsg",
  "Scale": "tip.spdScale",
  "Sigma": "tip.spdSigma",
  "Use DAVE": "tip.daveEnabled",
  "Mask": "tip.daveMask",
  "DAVE strength": "tip.daveStrength",
  "DAVE tau": "tip.daveTau",
  "Enable highres": "tip.highresEnabled",
  "Scale by": "tip.highresScale",
  "Method": "tip.highresMethod",
  "Multiple": "tip.highresMultiple",
  "Max long edge": "tip.highresMaxEdge",
  "Follow main sampler": "tip.highresFollow",
  "Enable": "tip.detailerBlock",
  "Prompt": "tip.detailerPrompt",
  "Count": "tip.detailerCount",
  "Threshold": "tip.detailerThreshold",
  "Refine": "tip.detailerRefine",
  "Individual": "tip.detailerIndividual",
  "Combined": "tip.detailerCombined",
  "Crop factor": "tip.detailerCropFactor",
  "BBox fill": "tip.detailerBboxFill",
  "Drop size": "tip.detailerDropSize",
  "Contour fill": "tip.detailerContourFill",
  "Guide size": "tip.detailerGuideSize",
  "Max size": "tip.detailerMaxSize",
  "Feather": "tip.detailerFeather",
  "Noise mask": "tip.detailerNoiseMask",
  "Force inpaint": "tip.detailerForceInpaint",
  "Mask feather": "tip.detailerMaskFeather",
  "Cycle": "tip.detailerCycle",
  "Alignment": "tip.detailerAlignment",
  "Enable detailer": "tip.detailerEnabled",
  "SAM3 checkpoint": "tip.detailerCheckpoint",
  "Save image": "tip.saveEnabled",
  "Filename": "tip.saveFilename",
  "Path": "tip.savePath",
  "Extension": "tip.saveExtension",
  "JPEG/WebP quality": "tip.saveQuality",
  "Lossless WebP": "tip.saveLosslessWebp",
  "Optimize PNG": "tip.saveOptimizePng",
  "Counter": "tip.saveCounter",
  "Time format": "tip.saveTimeFormat",
  "Clip skip": "tip.saveClipSkip",
  "Embed workflow": "tip.saveEmbedWorkflow",
  "Workflow JSON": "tip.saveWorkflowJson",
  "Civitai data": "tip.saveCivitaiData",
  "Easy remix": "tip.saveEasyRemix",
  "Custom metadata": "tip.saveCustom",
  "Start": "tip.artistMixStart",
  "Strength": "tip.artistMixStrength",
};

function aioText(key) {
  return easyuseAnimaText(AIO_TEXT, key);
}

function aioFormat(key, values = {}) {
  let text = aioText(key);
  for (const [name, value] of Object.entries(values)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }
  return text;
}

function applyTooltip(element, key) {
  if (!element || !key) {
    return element;
  }
  const text = aioText(key);
  if (text && text !== key) {
    element.title = text;
  }
  return element;
}

function applyTooltipText(element, text) {
  if (!element || !text) {
    return element;
  }
  element.title = text;
  return element;
}

const DEFAULT_INPUT_SETTINGS = {
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

const generatorSamplerOptionState = {
  loaded: false,
  loading: null,
  samplerNames: [...GENERATOR_FALLBACK_SAMPLER_NAMES],
  schedulerNames: [...GENERATOR_FALLBACK_SCHEDULER_NAMES],
};
const generatorOptionalDependencyState = {
  loaded: false,
  loading: null,
  available: {},
};

function uniqueStrings(values) {
  const output = [];
  for (const value of values || []) {
    const normalized = String(value ?? "");
    if (normalized && !output.includes(normalized)) {
      output.push(normalized);
    }
  }
  return output;
}

function choiceSpecValues(spec) {
  if (!Array.isArray(spec)) {
    return [];
  }
  if (Array.isArray(spec[0])) {
    return uniqueStrings(spec[0]);
  }
  return uniqueStrings(spec);
}

function optionsWithCurrent(options, current) {
  const merged = uniqueStrings(options);
  const normalized = String(current ?? "");
  if (normalized && !merged.includes(normalized)) {
    merged.unshift(normalized);
  }
  return merged;
}

async function fetchGeneratorSamplerOptions() {
  const response = api?.fetchApi
    ? await api.fetchApi("/object_info/KSampler")
    : await fetch("/object_info/KSampler");
  const data = await response.json();
  const ksamplerInfo = data?.KSampler || data;
  const required = ksamplerInfo?.input?.required || {};
  const samplerNames = choiceSpecValues(required.sampler_name);
  const schedulerNames = choiceSpecValues(required.scheduler);
  if (samplerNames.length) {
    generatorSamplerOptionState.samplerNames = samplerNames;
  }
  if (schedulerNames.length) {
    generatorSamplerOptionState.schedulerNames = schedulerNames;
  }
}

function loadGeneratorSamplerOptions() {
  if (generatorSamplerOptionState.loaded) {
    return Promise.resolve(generatorSamplerOptionState);
  }
  if (!generatorSamplerOptionState.loading) {
    generatorSamplerOptionState.loading = fetchGeneratorSamplerOptions()
      .catch((error) => {
        console.warn("[EasyUseAnima] Failed to load KSampler sampler/scheduler options.", error);
      })
      .finally(() => {
        generatorSamplerOptionState.loaded = true;
      })
      .then(() => generatorSamplerOptionState);
  }
  return generatorSamplerOptionState.loading;
}

async function fetchGeneratorOptionalDependencies() {
  const next = {};
  for (const [key, spec] of Object.entries(GENERATOR_OPTIONAL_DEPENDENCY_SPECS)) {
    try {
      const response = api?.fetchApi
        ? await api.fetchApi(`/object_info/${encodeURIComponent(spec.nodeId)}`)
        : await fetch(`/object_info/${encodeURIComponent(spec.nodeId)}`);
      const data = await response.json();
      next[key] = !!data?.[spec.nodeId];
    } catch {
      next[key] = false;
    }
  }
  generatorOptionalDependencyState.available = next;
}

function loadGeneratorOptionalDependencies() {
  if (generatorOptionalDependencyState.loaded) {
    return Promise.resolve(generatorOptionalDependencyState);
  }
  if (!generatorOptionalDependencyState.loading) {
    generatorOptionalDependencyState.loading = fetchGeneratorOptionalDependencies()
      .catch((error) => {
        console.warn("[EasyUseAnima] Failed to load optional dependency status.", error);
      })
      .finally(() => {
        generatorOptionalDependencyState.loaded = true;
      })
      .then(() => generatorOptionalDependencyState);
  }
  return generatorOptionalDependencyState.loading;
}

function optionalDependencyAvailable(key) {
  if (!key || !generatorOptionalDependencyState.loaded) {
    return true;
  }
  return !!generatorOptionalDependencyState.available[key];
}

function backendDependencyMissing(backend) {
  const dependencyKey = GENERATOR_BACKEND_DEPENDENCIES[backend];
  return dependencyKey && !optionalDependencyAvailable(dependencyKey);
}

function optionalDependencyPack(key) {
  return GENERATOR_OPTIONAL_DEPENDENCY_SPECS[key]?.pack || key || "";
}

function disableGeneratorSpectrumOptions(target) {
  if (!target || typeof target !== "object") {
    return;
  }
  if (target.spectrum && typeof target.spectrum === "object") {
    target.spectrum.enabled = false;
  }
  if (target.dit_corrections && typeof target.dit_corrections === "object") {
    target.dit_corrections.enabled = false;
  }
}

function sanitizeGeneratorSettingsForOptionalDependencies(settings) {
  const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
  delete next.sampler.dave;
  const backendDependency = GENERATOR_BACKEND_DEPENDENCIES[next.sampler.backend];
  if (backendDependency && !optionalDependencyAvailable(backendDependency)) {
    next.sampler.backend = "comfy_ksampler";
  }
  if (!optionalDependencyAvailable("spectrumPatch")) {
    disableGeneratorSpectrumOptions(next.sampler);
    disableGeneratorSpectrumOptions(next.highres);
    disableGeneratorSpectrumOptions(next.detailer?.face);
    disableGeneratorSpectrumOptions(next.detailer?.eye);
  }
  if (!optionalDependencyAvailable("kjFp16")) {
    next.model_patches.kj.fp16_accumulation = false;
  }
  if (!optionalDependencyAvailable("kjSage")) {
    next.model_patches.kj.sage_attention = "disabled";
    next.model_patches.kj.sage_allow_compile = false;
  }
  if (!optionalDependencyAvailable("kjTorchCompile")) {
    next.model_patches.kj.torch_compile.enabled = false;
  }
  if (!optionalDependencyAvailable("dave")) {
    next.model_patches.dave.enabled = false;
  }
  if (!optionalDependencyAvailable("imageSaver") && next.save.backend === "image_saver") {
    next.save.backend = "comfy_save_image";
  }
  const impactMissing = !optionalDependencyAvailable("impactDetailer")
    || !optionalDependencyAvailable("impactMaskToSegs");
  if (impactMissing) {
    next.detailer.enabled = false;
    next.detailer.face.enabled = false;
    next.detailer.eye.enabled = false;
  }
  return next;
}

function samplerNameOptions(current) {
  return optionsWithCurrent(generatorSamplerOptionState.samplerNames, current);
}

function schedulerNameOptions(current) {
  return optionsWithCurrent(generatorSamplerOptionState.schedulerNames, current);
}

function refreshGeneratorPanels() {
  for (const node of generatorGraphNodes()) {
    renderGeneratorPanel(node);
  }
}

function findWidget(node, name) {
  return node.widgets?.find((widget) => widget.name === name);
}

function hideWidget(widget) {
  if (!widget) {
    return;
  }
  widget.hidden = true;
  widget.serialize = true;
  widget.options ||= {};
  widget.options.hidden = true;
  widget.computeSize = () => [0, 0];
  widget.draw = () => {};
  if (widget.inputEl) {
    widget.inputEl.style.display = "none";
    widget.inputEl.style.pointerEvents = "none";
    widget.inputEl.tabIndex = -1;
  }
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function mergeDefaults(defaults, value) {
  const output = clone(defaults);
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return output;
  }
  const merge = (base, incoming) => {
    for (const [key, incomingValue] of Object.entries(incoming)) {
      if (
        base[key]
        && typeof base[key] === "object"
        && !Array.isArray(base[key])
        && incomingValue
        && typeof incomingValue === "object"
        && !Array.isArray(incomingValue)
      ) {
        merge(base[key], incomingValue);
      } else {
        base[key] = incomingValue;
      }
    }
    return base;
  };
  return merge(output, value);
}

function parseSettings(widget, defaults) {
  if (!widget) {
    return clone(defaults);
  }
  try {
    return mergeDefaults(defaults, JSON.parse(widget.value || "{}"));
  } catch {
    return clone(defaults);
  }
}

function writeSettings(node, widget, value, markDirty = true) {
  if (!widget) {
    return;
  }
  widget.value = JSON.stringify(value);
  widget.callback?.(widget.value);
  if (markDirty) {
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
  }
}

function ensureStyle() {
  if (document.getElementById("easyuse-anima-aio-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-aio-style";
  style.textContent = `
    .easyuse-anima-aio-backdrop {
      position: fixed;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100000;
      background: rgba(5, 7, 10, 0.55);
    }
    .easyuse-anima-aio-dialog {
      width: min(760px, calc(100vw - 48px));
      height: min(720px, calc(100vh - 48px));
      max-height: calc(100vh - 48px);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      color: #f3f0e8;
      background: #171b20;
      border: 1px solid #4b5661;
      box-shadow: 0 18px 56px rgba(0, 0, 0, 0.45);
      border-radius: 8px;
      font: 13px "Segoe UI", sans-serif;
    }
    .easyuse-anima-aio-dialog header {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 20px 12px;
      border-bottom: 1px solid #303943;
    }
    .easyuse-anima-aio-dialog h2 {
      margin: 0 0 6px;
      font-size: 20px;
    }
    .easyuse-anima-aio-dialog p {
      margin: 0;
      color: #98a3aa;
    }
    .easyuse-anima-aio-body {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      padding: 16px 20px 20px;
      overflow: auto;
      flex: 1 1 auto;
      min-height: 0;
    }
    .easyuse-anima-aio-body.easyuse-anima-aio-save-body {
      grid-template-columns: minmax(0, 1fr);
      overflow-x: hidden;
    }
    .easyuse-anima-aio-body.easyuse-anima-aio-one-column {
      grid-template-columns: minmax(0, 1fr);
      overflow-x: hidden;
    }
    .easyuse-anima-aio-section {
      min-width: 0;
      padding: 14px;
      background: #11161b;
      border: 1px solid #34404a;
      border-radius: 7px;
    }
    .easyuse-anima-aio-save-body .easyuse-anima-aio-section {
      grid-column: 1 / -1;
    }
    .easyuse-anima-aio-section.full {
      grid-column: 1 / -1;
    }
    .easyuse-anima-aio-section h3 {
      margin: 0 0 12px;
      font-size: 15px;
    }
    .easyuse-anima-aio-subsection {
      margin-top: 12px;
      padding: 12px;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid #2f3b44;
      border-radius: 6px;
    }
    .easyuse-anima-aio-subsection h4 {
      margin: 0 0 10px;
      color: #e8e2d7;
      font-size: 13px;
      font-weight: 700;
    }
    .easyuse-anima-aio-section .easyuse-anima-aio-node-stage-mini-header h3 {
      margin: 0;
    }
    .easyuse-anima-aio-subsection.hidden {
      display: none;
    }
    .easyuse-anima-aio-tabs {
      display: flex;
      gap: 6px;
      align-items: flex-end;
      min-width: 0;
      overflow-x: auto;
      padding: 0 0 8px;
      margin: 0 0 12px;
      border-bottom: 1px solid #34404a;
    }
    .easyuse-anima-aio-tab {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-width: 118px;
      max-width: 220px;
      padding: 7px 8px;
      color: #d7dde0;
      background: #151b21;
      border: 1px solid #34404a;
      border-bottom-color: #4b5661;
      border-radius: 7px 7px 0 0;
      font: inherit;
      cursor: pointer;
    }
    .easyuse-anima-aio-tab.active {
      color: #f3f0e8;
      background: #24313a;
      border-color: #5b6b78;
      border-bottom-color: #24313a;
    }
    .easyuse-anima-aio-tab-label {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 1 1 auto;
      text-align: left;
    }
    .easyuse-anima-aio-tab-tools {
      display: inline-flex;
      gap: 3px;
      flex: 0 0 auto;
    }
    .easyuse-anima-aio-tab-tools button {
      width: 20px;
      height: 20px;
      padding: 0;
      color: #f3f0e8;
      background: #26313a;
      border: 1px solid #526170;
      border-radius: 4px;
      font: 11px "Segoe UI", sans-serif;
      cursor: pointer;
    }
    .easyuse-anima-aio-tab-tools button:disabled {
      opacity: 0.45;
      cursor: default;
    }
    .easyuse-anima-aio-tab-panel {
      min-width: 0;
    }
    .easyuse-anima-aio-detailer-target-panel {
      min-width: 0;
    }
    .easyuse-anima-aio-detailer-target-panel > .easyuse-anima-aio-node-stage-mini-header {
      margin-top: 0;
    }
    .easyuse-anima-aio-warning {
      grid-column: 1 / -1;
      margin: 8px 0 0;
      padding: 8px 10px;
      color: #f3d39a;
      background: rgba(163, 111, 37, 0.16);
      border: 1px solid rgba(221, 164, 82, 0.45);
      border-radius: 6px;
      line-height: 1.35;
    }
    .easyuse-anima-aio-field {
      display: grid;
      grid-template-columns: 130px 1fr;
      align-items: center;
      gap: 10px;
      margin: 8px 0;
      min-width: 0;
    }
    .easyuse-anima-aio-save-body .easyuse-anima-aio-field {
      grid-template-columns: minmax(150px, 220px) minmax(0, 1fr);
    }
    .easyuse-anima-aio-field label {
      color: #c7ced0;
    }
    .easyuse-anima-aio-field input,
    .easyuse-anima-aio-field select,
    .easyuse-anima-aio-field textarea {
      width: 100%;
      box-sizing: border-box;
      color: #f0eee8;
      background: #0d1216;
      border: 1px solid #3a4650;
      border-radius: 5px;
      padding: 7px 9px;
      font: inherit;
    }
    .easyuse-anima-aio-field textarea {
      min-height: 58px;
      resize: vertical;
    }
    .easyuse-anima-aio-hash-bundle-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-top: 8px;
      min-width: 0;
    }
    .easyuse-anima-aio-hash-bundle-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: start;
      max-width: 100%;
      min-width: 0;
    }
    .easyuse-anima-aio-hash-bundle-row textarea {
      min-height: 42px;
      resize: vertical;
    }
    .easyuse-anima-aio-hash-bundle-row button {
      color: #f3f0e8;
      background: #26313a;
      border: 1px solid #526170;
      border-radius: 6px;
      padding: 7px 10px;
      font: inherit;
      cursor: pointer;
    }
    .easyuse-anima-aio-civitai-fetcher-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      min-width: 0;
    }
    .easyuse-anima-aio-civitai-fetcher-row {
      max-width: 100%;
      min-width: 0;
      overflow: hidden;
      padding: 9px;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid #2f3b44;
      border-radius: 6px;
    }
    .easyuse-anima-aio-civitai-fetcher-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }
    .easyuse-anima-aio-civitai-fetcher-enabled {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: #c7ced0;
      white-space: nowrap;
    }
    .easyuse-anima-aio-civitai-fetcher-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 8px;
      min-width: 0;
    }
    .easyuse-anima-aio-mini-field {
      min-width: 0;
    }
    .easyuse-anima-aio-mini-field input {
      min-width: 0;
    }
    .easyuse-anima-aio-mini-field label {
      display: block;
      margin: 0 0 4px;
      color: #aab3b7;
      font-size: 11px;
    }
    .easyuse-anima-aio-civitai-fetcher-preview {
      margin-top: 8px;
      padding: 6px 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      color: #b8c6cb;
      background: rgba(123, 194, 153, 0.08);
      border: 1px solid rgba(123, 194, 153, 0.16);
      border-radius: 5px;
      white-space: nowrap;
    }
    .easyuse-anima-aio-add-row {
      margin-top: 8px;
      color: #f3f0e8;
      background: #26313a;
      border: 1px solid #526170;
      border-radius: 6px;
      padding: 6px 10px;
      font: inherit;
      cursor: pointer;
    }
    @media (max-width: 760px) {
      .easyuse-anima-aio-field,
      .easyuse-anima-aio-save-body .easyuse-anima-aio-field {
        grid-template-columns: minmax(0, 1fr);
      }
      .easyuse-anima-aio-hash-bundle-row {
        grid-template-columns: minmax(0, 1fr);
      }
      .easyuse-anima-aio-civitai-fetcher-grid {
        grid-template-columns: minmax(0, 1fr);
      }
    }
    .easyuse-anima-aio-actions {
      display: flex;
      flex: 0 0 auto;
      justify-content: flex-end;
      gap: 10px;
      padding: 0 20px 18px;
    }
    .easyuse-anima-aio-actions button,
    .easyuse-anima-aio-close {
      color: #f3f0e8;
      background: #26313a;
      border: 1px solid #526170;
      border-radius: 6px;
      padding: 8px 14px;
      font: inherit;
      cursor: pointer;
    }
    .easyuse-anima-aio-actions button.primary {
      background: #2b6655;
      border-color: #78c8aa;
    }
    .easyuse-anima-aio-node-panel {
      box-sizing: border-box;
      width: 100%;
      min-width: 0;
      min-height: ${GENERATOR_PANEL_MIN_HEIGHT}px;
      padding: 9px;
      color: #ece7dc;
      font: 12px "Segoe UI", sans-serif;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      user-select: none;
    }
    .easyuse-anima-aio-node-panel * {
      box-sizing: border-box;
    }
    .easyuse-anima-aio-node-topbar {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 8px;
    }
    .easyuse-anima-aio-node-main {
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
      gap: 8px;
      flex: 1 1 auto;
      min-height: 284px;
      height: 100%;
    }
    .easyuse-anima-aio-node-card {
      min-width: 0;
      padding: 9px;
      background: #11171c;
      border: 1px solid #34424a;
      border-radius: 7px;
    }
    .easyuse-anima-aio-node-settings {
      display: flex;
      flex-direction: column;
      min-height: 0;
      height: 100%;
      overflow: hidden;
    }
    .easyuse-anima-aio-node-settings-scroll {
      flex: 1 1 auto;
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      padding-right: 4px;
    }
    .easyuse-anima-aio-node-settings-scroll::-webkit-scrollbar {
      width: 8px;
    }
    .easyuse-anima-aio-node-settings-scroll::-webkit-scrollbar-thumb {
      background: #3b4852;
      border-radius: 999px;
    }
    .easyuse-anima-aio-node-card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin: 0 0 8px;
    }
    .easyuse-anima-aio-node-card-title {
      min-width: 0;
      color: #f4efe5;
      font-size: 12px;
      font-weight: 700;
      line-height: 1;
    }
    .easyuse-anima-aio-node-card-actions {
      display: flex;
      align-items: center;
      gap: 4px;
      flex: 0 0 auto;
    }
    .easyuse-anima-aio-node-sampler-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 6px;
    }
    .easyuse-anima-aio-node-stage-block {
      margin-top: 8px;
      padding: 8px;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid #2e3a42;
      border-radius: 6px;
    }
    .easyuse-anima-aio-node-stage-header,
    .easyuse-anima-aio-node-stage-mini-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 7px;
    }
    .easyuse-anima-aio-node-stage-title,
    .easyuse-anima-aio-node-stage-mini-title {
      min-width: 0;
      color: #f2eee5;
      font-weight: 700;
      line-height: 1.1;
    }
    .easyuse-anima-aio-node-stage-title {
      font-size: 11px;
    }
    .easyuse-anima-aio-node-stage-mini-title {
      font-size: 10.5px;
    }
    .easyuse-anima-aio-node-stage-toggle {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      flex: 0 0 auto;
      color: #b7c2c7;
      font-size: 10px;
      white-space: nowrap;
    }
    .easyuse-anima-aio-node-stage-body {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 6px;
    }
    .easyuse-anima-aio-node-stage-note {
      grid-column: 1 / -1;
      padding: 5px 7px;
      color: #aebbc0;
      background: rgba(123, 194, 153, 0.08);
      border: 1px solid rgba(123, 194, 153, 0.18);
      border-radius: 5px;
      font-size: 10px;
      line-height: 1.35;
    }
    .easyuse-anima-aio-node-stage-mini {
      grid-column: 1 / -1;
      padding: 7px;
      background: rgba(0, 0, 0, 0.13);
      border: 1px solid #2f3a42;
      border-radius: 5px;
    }
    .easyuse-anima-aio-node-stage-tools {
      display: flex;
      gap: 4px;
      flex: 0 0 auto;
    }
    .easyuse-anima-aio-node-stage-tools .easyuse-anima-aio-node-icon-button {
      width: 22px;
      height: 20px;
      font-size: 10px;
    }
    .easyuse-anima-aio-node-field {
      min-width: 0;
    }
    .easyuse-anima-aio-node-field.seed {
      grid-column: 1 / -1;
    }
    .easyuse-anima-aio-node-field.mode,
    .easyuse-anima-aio-node-field.wide {
      grid-column: 1 / -1;
    }
    .easyuse-anima-aio-node-field.full {
      grid-column: 1 / -1;
    }
    .easyuse-anima-aio-node-field label {
      display: block;
      margin: 0 0 3px;
      color: #aab3b7;
      font-size: 10px;
      line-height: 1;
    }
    .easyuse-anima-aio-node-field input,
    .easyuse-anima-aio-node-field select {
      width: 100%;
      height: 24px;
      min-width: 0;
      padding: 3px 7px;
      color: #f2eee5;
      background: #10151a;
      border: 1px solid #394651;
      border-radius: 5px;
      font: 12px "Segoe UI", sans-serif;
      outline: none;
    }
    .easyuse-anima-aio-node-mode-badge {
      width: 100%;
      min-width: 0;
      min-height: 28px;
      padding: 5px 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      color: #daf0df;
      background: linear-gradient(135deg, rgba(65, 129, 99, 0.32), rgba(39, 64, 79, 0.78));
      border: 1px solid rgba(123, 194, 153, 0.55);
      border-radius: 999px;
      font: 700 11px "Segoe UI", sans-serif;
      line-height: 16px;
      text-align: center;
    }
    .easyuse-anima-aio-node-field input[type="checkbox"] {
      width: 16px;
      height: 16px;
      padding: 0;
      vertical-align: middle;
    }
    .easyuse-anima-aio-node-inline {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .easyuse-anima-aio-node-inline input[type="text"] {
      flex: 1 1 auto;
    }
    .easyuse-anima-aio-node-seed-actions {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 5px;
      margin-top: 6px;
    }
    .easyuse-anima-aio-node-seed-actions .easyuse-anima-aio-node-button {
      width: 100%;
      min-width: 0;
      padding: 3px 5px;
      font-size: 10.5px;
      text-align: center;
    }
    .easyuse-anima-aio-node-seed-actions [data-aio-seed-last] {
      grid-column: 1 / -1;
    }
    .easyuse-anima-aio-node-slider-control {
      display: grid;
      grid-template-columns: 72px minmax(0, 1fr);
      gap: 6px;
      align-items: center;
    }
    .easyuse-anima-aio-node-slider-track {
      position: relative;
      height: 20px;
      min-width: 0;
      cursor: ew-resize;
      touch-action: none;
    }
    .easyuse-anima-aio-node-slider-rail {
      position: absolute;
      left: 0;
      right: 0;
      top: 8px;
      height: 4px;
      border-radius: 999px;
      background: #22303a;
      border: 1px solid #3c4c56;
    }
    .easyuse-anima-aio-node-slider-fill {
      position: absolute;
      left: 0;
      top: 8px;
      height: 4px;
      border-radius: 999px;
      background: #7bc299;
    }
    .easyuse-anima-aio-node-slider-thumb {
      position: absolute;
      top: 3px;
      width: 12px;
      height: 12px;
      margin-left: -6px;
      border-radius: 999px;
      background: #f0eadf;
      border: 1px solid #8bb99d;
      box-shadow: 0 1px 4px rgba(0,0,0,0.35);
    }
    .easyuse-anima-aio-node-button,
    .easyuse-anima-aio-node-icon-button {
      height: 24px;
      color: #f2eee5;
      background: #26323b;
      border: 1px solid #53616c;
      border-radius: 5px;
      font: 12px "Segoe UI", sans-serif;
      cursor: pointer;
    }
    .easyuse-anima-aio-node-button {
      padding: 3px 9px;
      white-space: nowrap;
      flex: 1 1 0;
    }
    .easyuse-anima-aio-node-icon-button {
      width: 28px;
      padding: 0;
      flex: 0 0 auto;
    }
    .easyuse-anima-aio-node-icon-button.active {
      border-color: #78c8aa;
      background: #2b6655;
    }
    .easyuse-anima-aio-node-button:hover,
    .easyuse-anima-aio-node-icon-button:hover {
      border-color: #7d929f;
      background: #303d46;
    }
    .easyuse-anima-aio-node-preview {
      display: flex;
      flex-direction: column;
      height: 100%;
      min-height: 0;
    }
    .easyuse-anima-aio-node-sampler-actions {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      margin-top: 8px;
      flex: 0 0 auto;
    }
    .easyuse-anima-aio-node-sampler-actions .full {
      grid-column: 1 / -1;
    }
    .easyuse-anima-aio-node-sampler-actions .easyuse-anima-aio-node-button {
      width: 100%;
      min-width: 0;
      padding-left: 5px;
      padding-right: 5px;
      text-align: center;
    }
    .easyuse-anima-aio-node-preview {
      min-height: 284px;
    }
    .easyuse-anima-aio-node-preview-box {
      position: relative;
      flex: 1 1 auto;
      height: auto;
      min-height: 210px;
      overflow: hidden;
      border: 1px solid #3c4952;
      border-radius: 6px;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.035) 25%, transparent 25%) 0 0 / 18px 18px,
        linear-gradient(135deg, transparent 75%, rgba(255,255,255,0.035) 75%) 0 0 / 18px 18px,
        #151a1f;
    }
    .easyuse-anima-aio-node-preview-box img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: contain;
      background: #10151a;
    }
    .easyuse-anima-aio-node-preview-compare {
      position: relative;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #10151a;
      cursor: ew-resize;
      touch-action: none;
    }
    .easyuse-anima-aio-node-preview-layer {
      position: absolute;
      inset: 0;
      overflow: hidden;
    }
    .easyuse-anima-aio-node-preview-layer.after {
      clip-path: inset(0 0 0 var(--aio-compare-x, 50%));
    }
    .easyuse-anima-aio-node-preview-layer img {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    .easyuse-anima-aio-node-preview-divider {
      position: absolute;
      top: 0;
      bottom: 0;
      left: var(--aio-compare-x, 50%);
      width: 2px;
      transform: translateX(-1px);
      background: rgba(245, 241, 232, 0.92);
      box-shadow: 0 0 8px rgba(0,0,0,0.45);
      pointer-events: none;
    }
    .easyuse-anima-aio-node-preview-pane-label {
      position: absolute;
      left: 6px;
      top: 6px;
      z-index: 1;
      max-width: calc(100% - 12px);
      padding: 3px 6px;
      overflow: hidden;
      color: #f4efe5;
      background: rgba(10, 14, 18, 0.78);
      border: 1px solid rgba(255, 255, 255, 0.13);
      border-radius: 4px;
      font-size: 10px;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .easyuse-anima-aio-node-preview-layer.after .easyuse-anima-aio-node-preview-pane-label {
      right: 6px;
      left: auto;
      text-align: right;
    }
    .easyuse-anima-aio-node-preview-placeholder {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 5px;
      color: #d9d2c7;
      text-align: center;
      padding: 12px;
    }
    .easyuse-anima-aio-node-preview-placeholder strong {
      font-size: 12px;
      font-weight: 700;
    }
    .easyuse-anima-aio-node-preview-placeholder span {
      max-width: 240px;
      color: #93a0a6;
      font-size: 10px;
      line-height: 1.35;
    }
    .easyuse-anima-aio-node-preview-meta {
      min-height: 16px;
      margin: 6px 0 7px;
      overflow: hidden;
      color: #aebbc0;
      font-size: 10px;
      line-height: 1.35;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .easyuse-anima-aio-node-preview-feed {
      display: flex;
      flex: 0 0 auto;
      gap: 6px;
      max-width: 100%;
      min-height: 0;
      margin: 0 0 7px;
      padding: 6px;
      overflow-x: auto;
      overflow-y: hidden;
      overscroll-behavior-x: contain;
      scrollbar-gutter: stable;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 5px;
    }
    .easyuse-anima-aio-node-preview-feed[hidden] {
      display: none;
    }
    .easyuse-anima-aio-node-preview-thumb {
      position: relative;
      flex: 0 0 66px;
      width: 66px;
      height: 62px;
      padding: 0;
      overflow: hidden;
      background: #11161b;
      border: 1px solid #43515c;
      border-radius: 5px;
      cursor: pointer;
    }
    .easyuse-anima-aio-node-preview-thumb.active {
      border-color: #87c8eb;
      box-shadow: 0 0 0 1px rgba(135, 200, 235, 0.38);
    }
    .easyuse-anima-aio-node-preview-thumb img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: cover;
    }
    .easyuse-anima-aio-node-preview-thumb span {
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      padding: 2px 4px;
      overflow: hidden;
      color: #f4efe5;
      background: rgba(8, 12, 16, 0.76);
      font-size: 9px;
      line-height: 1.2;
      text-align: center;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  `;
  document.head.append(style);
}

function numberInput(value, step = "1") {
  const input = document.createElement("input");
  input.type = "number";
  input.step = step;
  input.value = value;
  return input;
}

function textInput(value) {
  const input = document.createElement("input");
  input.type = "text";
  input.value = value ?? "";
  return input;
}

function textareaInput(value) {
  const textarea = document.createElement("textarea");
  textarea.value = value ?? "";
  return textarea;
}

function checkbox(value) {
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = !!value;
  return input;
}

function selectInput(options, value) {
  const select = document.createElement("select");
  for (const optionSpec of options) {
    const optionValue = typeof optionSpec === "object" && optionSpec
      ? String(optionSpec.value ?? "")
      : String(optionSpec ?? "");
    const option = document.createElement("option");
    option.value = optionValue;
    option.textContent = typeof optionSpec === "object" && optionSpec
      ? String(optionSpec.label ?? optionValue)
      : optionValue;
    option.disabled = !!(typeof optionSpec === "object" && optionSpec?.disabled);
    if (typeof optionSpec === "object" && optionSpec?.title) {
      option.title = String(optionSpec.title);
    }
    if (optionValue === value) {
      option.selected = true;
    }
    select.append(option);
  }
  return select;
}

function widgetValue(node, name, fallback) {
  if (Object.prototype.hasOwnProperty.call(node?.__easyuseAnimaGeneratorUiValues || {}, name)) {
    return node.__easyuseAnimaGeneratorUiValues[name];
  }
  const widget = findWidget(node, name);
  return widget ? widget.value : fallback;
}

function setWidgetValue(node, name, value) {
  const widget = findWidget(node, name);
  if (widget) {
    widget.value = value;
    widget.callback?.(value);
  }
  node.__easyuseAnimaGeneratorUiValues ||= {};
  node.__easyuseAnimaGeneratorUiValues[name] = value;
}

function asBool(value, fallback = false) {
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

function firstValue(value, fallback = "") {
  if (Array.isArray(value)) {
    return value.length > 0 ? value[0] : fallback;
  }
  return value ?? fallback;
}

function generatorPreviewImages(message) {
  const value = message?.easyuse_anima_preview;
  const raw = Array.isArray(value) ? value : [firstValue(value, null)];
  const images = [];
  for (const item of raw) {
    if (Array.isArray(item)) {
      images.push(...item);
    } else if (item) {
      images.push(item);
    }
  }
  return images.filter((item) => item && typeof item === "object" && !Array.isArray(item));
}

function generatorPreviewRunId(message) {
  return String(firstValue(message?.easyuse_anima_run_id ?? message?.run_id, "") || "");
}

function generatorPreviewFeedLimit(settings) {
  return Math.trunc(clampGeneratorNumber(
    settings?.preview?.feed_count,
    DEFAULT_GENERATION_SETTINGS.preview.feed_count,
    1,
    100,
  ));
}

function generatorPreviewIdentity(image) {
  return [
    image?.stage || "",
    image?.type || "",
    image?.subfolder || "",
    image?.filename || image?.name || "",
  ].map((part) => String(part)).join("\u0001");
}

function tagGeneratorPreviewRun(images, runId = "", startIndex = 0) {
  const normalizedRunId = runId || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return images.map((image, index) => ({
    ...image,
    __aio_run_id: image.__aio_run_id || normalizedRunId,
    __aio_run_index: Number.isInteger(image.__aio_run_index) ? image.__aio_run_index : startIndex + index,
  }));
}

function mergeGeneratorPreviewImages(existingImages, nextImages, runId = "", limit = 0) {
  const existing = Array.isArray(existingImages)
    ? existingImages.filter((item) => item && typeof item === "object" && !Array.isArray(item))
    : [];
  const tagged = tagGeneratorPreviewRun(nextImages, runId, existing.length);
  const merged = [];
  const indexByKey = new Map();
  for (const item of [...existing, ...tagged]) {
    const key = generatorPreviewIdentity(item);
    if (!key.replace(/\u0001/g, "")) {
      merged.push(item);
      continue;
    }
    if (indexByKey.has(key)) {
      const index = indexByKey.get(key);
      merged[index] = { ...merged[index], ...item };
    } else {
      indexByKey.set(key, merged.length);
      merged.push(item);
    }
  }
  return limit > 0 ? merged.slice(Math.max(0, merged.length - limit)) : merged;
}

function appendGeneratorPreviewFeed(existingImages, nextImages, settings, runId = "") {
  return mergeGeneratorPreviewImages(
    existingImages,
    nextImages,
    runId,
    generatorPreviewFeedLimit(settings),
  );
}

function generatorPreviewEventDetail(event) {
  const detail = event?.detail || {};
  if (detail?.data && typeof detail.data === "object") {
    return detail.data;
  }
  return detail;
}

function generatorImageUrl(image) {
  if (!image || typeof image !== "object") {
    return "";
  }
  const params = new URLSearchParams();
  for (const key of ["filename", "subfolder", "type"]) {
    if (image[key] != null && image[key] !== "") {
      params.set(key, image[key]);
    }
  }
  if (!params.has("filename")) {
    return "";
  }
  params.set("preview", "webp;90");
  const path = `/view?${params.toString()}`;
  return typeof api?.apiURL === "function" ? api.apiURL(path) : path;
}

function generatorPreviewImageLabel(image) {
  return String(image?.label || image?.stage || "Preview");
}

function generatorPreviewImageName(image) {
  return String(image?.filename || image?.name || generatorPreviewImageLabel(image) || "-");
}

function generatorPreviewResolution(image) {
  const width = Number(image?.width || 0);
  const height = Number(image?.height || 0);
  return width > 0 && height > 0 ? `${Math.trunc(width)} x ${Math.trunc(height)}` : "-";
}

function generatorPreviewFileSize(image) {
  const bytes = Number(image?.bytes || image?.size || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "-";
  }
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const decimals = unit === 0 || value >= 10 ? 0 : 1;
  return `${value.toFixed(decimals)} ${units[unit]}`;
}

function generatorDefaultPreviewIndex(images) {
  if (!Array.isArray(images) || !images.length) {
    return -1;
  }
  for (let index = images.length - 1; index >= 0; index -= 1) {
    if (String(images[index]?.stage || "") === "final") {
      return index;
    }
  }
  return images.length - 1;
}

function generatorSelectedPreviewIndex(node, images) {
  const selected = Number(node?.__easyuseAnimaSelectedPreviewIndex);
  if (Number.isInteger(selected) && selected >= 0 && selected < images.length) {
    return selected;
  }
  return generatorDefaultPreviewIndex(images);
}

function generatorMainPreviewImage(node, images) {
  const index = generatorSelectedPreviewIndex(node, images);
  return index >= 0 ? images[index] : null;
}

function normalizeSeedControl(value) {
  const normalized = String(value || "").trim();
  return GENERATOR_SEED_CONTROLS.includes(normalized) ? normalized : "fixed";
}

function isSpecialSeed(value) {
  return GENERATOR_SPECIAL_SEEDS.includes(Number(value));
}

function normalizeSeedValue(value, fallback = GENERATOR_SPECIAL_SEED_RANDOM) {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) {
    return fallback;
  }
  return Math.max(GENERATOR_SPECIAL_SEED_DECREMENT, Math.min(GENERATOR_MAX_SEED, Math.trunc(numberValue)));
}

function clampGeneratorNumber(value, fallback, min, max) {
  const parsed = Number(value);
  const next = Number.isFinite(parsed) ? parsed : fallback;
  return Math.max(min, Math.min(max, next));
}

function normalizeDetailerOrder(order) {
  const output = [];
  for (const name of Array.isArray(order) ? order : DEFAULT_GENERATION_SETTINGS.detailer.order) {
    const normalized = String(name || "").trim();
    if ((normalized === "face" || normalized === "eye") && !output.includes(normalized)) {
      output.push(normalized);
    }
  }
  for (const name of DEFAULT_GENERATION_SETTINGS.detailer.order) {
    if (!output.includes(name)) {
      output.push(name);
    }
  }
  return output;
}

function normalizeGeneratorPreviewSettings(settings) {
  settings.preview = mergeDefaults(DEFAULT_GENERATION_SETTINGS.preview, settings.preview || {});
  settings.preview.intermediate_images = asBool(
    settings.preview.intermediate_images,
    DEFAULT_GENERATION_SETTINGS.preview.intermediate_images,
  );
  settings.preview.compare_previous = asBool(
    settings.preview.compare_previous,
    DEFAULT_GENERATION_SETTINGS.preview.compare_previous,
  );
  settings.preview.image_feed = asBool(
    settings.preview.image_feed,
    DEFAULT_GENERATION_SETTINGS.preview.image_feed,
  );
  settings.preview.feed_count = Math.trunc(clampGeneratorNumber(
    settings.preview.feed_count,
    DEFAULT_GENERATION_SETTINGS.preview.feed_count,
    1,
    100,
  ));
  if (settings.save?.image_saver) {
    delete settings.save.image_saver.show_preview;
  }
  return settings.preview;
}

function normalizeGeneratorInputValues(node, settings = DEFAULT_GENERATION_SETTINGS) {
  const merged = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
  return {
    seed: normalizeSeedValue(widgetValue(node, "seed", merged.sampler.seed)),
    steps: Math.trunc(clampGeneratorNumber(widgetValue(node, "steps", merged.sampler.steps), DEFAULT_GENERATION_SETTINGS.sampler.steps, 1, 75)),
    cfg: clampGeneratorNumber(widgetValue(node, "cfg", merged.sampler.cfg), DEFAULT_GENERATION_SETTINGS.sampler.cfg, 1.0, 10.0),
    sampler_name: String(widgetValue(node, "sampler_name", merged.sampler.sampler_name) || merged.sampler.sampler_name),
    scheduler: String(widgetValue(node, "scheduler", merged.sampler.scheduler) || merged.sampler.scheduler),
    denoise: clampGeneratorNumber(widgetValue(node, "denoise", merged.sampler.denoise), DEFAULT_GENERATION_SETTINGS.sampler.denoise, 0.0, 1.0),
    save_image: asBool(widgetValue(node, "save_image", merged.save.enabled), merged.save.enabled),
  };
}

function mergeVisibleGeneratorSettings(node, settings) {
  const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
  const inputs = normalizeGeneratorInputValues(node, next);
  next.sampler.seed = inputs.seed;
  next.sampler.seed_after_generate = normalizeSeedControl(next.sampler.seed_after_generate);
  next.sampler.steps = inputs.steps;
  next.sampler.cfg = inputs.cfg;
  next.sampler.sampler_name = inputs.sampler_name;
  next.sampler.scheduler = inputs.scheduler;
  next.sampler.denoise = inputs.denoise;
  delete next.sampler.dave;
  next.model_patches.aura_flow ||= {};
  delete next.model_patches.aura_flow.enabled;
  next.model_patches.aura_flow.shift = clampGeneratorNumber(
    next.model_patches.aura_flow.shift,
    DEFAULT_GENERATION_SETTINGS.model_patches.aura_flow.shift,
    1.0,
    10.0,
  );
  next.save.enabled = inputs.save_image;
  next.save.backend = ["image_saver", "comfy_save_image"].includes(next.save.backend)
    ? next.save.backend
    : "image_saver";
  delete next.save.filename_prefix;
  normalizeGeneratorPreviewSettings(next);
  return next;
}

function applyVisibleGeneratorSettings(node, settings) {
  setWidgetValue(node, "seed", settings.sampler.seed);
  setWidgetValue(node, "steps", settings.sampler.steps);
  setWidgetValue(node, "cfg", settings.sampler.cfg);
  setWidgetValue(node, "sampler_name", settings.sampler.sampler_name);
  setWidgetValue(node, "scheduler", settings.sampler.scheduler);
  setWidgetValue(node, "denoise", settings.sampler.denoise);
  setWidgetValue(node, "save_image", !!settings.save.enabled);
}

function syncGeneratorSettingsFromVisible(node) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  if (!widget) {
    return;
  }
  writeSettings(
    node,
    widget,
    mergeVisibleGeneratorSettings(node, parseSettings(widget, DEFAULT_GENERATION_SETTINGS)),
    false
  );
}

function widgetOptions(node, name, fallback = []) {
  const current = widgetValue(node, name, null);
  if (name === "sampler_name") {
    return samplerNameOptions(current);
  }
  if (name === "scheduler") {
    return schedulerNameOptions(current);
  }
  const widget = findWidget(node, name);
  const values = widget?.options?.values;
  const options = Array.isArray(values) ? values : fallback;
  return optionsWithCurrent(options, current);
}

function setWidgetValueIfChanged(node, name, value) {
  const widget = findWidget(node, name);
  const uiValues = node.__easyuseAnimaGeneratorUiValues || {};
  if (!widget && uiValues[name] === value) {
    return;
  }
  if (widget && widget.value === value && uiValues[name] === value) {
    return;
  }
  setWidgetValue(node, name, value);
}

function setWorkflowWidgetValue(node, workflowNode, name, value) {
  if (!workflowNode || !Array.isArray(workflowNode.widgets_values) || !Array.isArray(node?.widgets)) {
    return;
  }
  const index = node.widgets.findIndex((widget) => widget?.name === name);
  if (index < 0) {
    return;
  }
  while (workflowNode.widgets_values.length <= index) {
    workflowNode.widgets_values.push(null);
  }
  workflowNode.widgets_values[index] = value;
}

function settingsToCompactJson(settings) {
  const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
  delete next.save?.filename_prefix;
  normalizeGeneratorPreviewSettings(next);
  return JSON.stringify(next);
}

function syncGeneratorSerializedWidgets(node, serialized = null) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  const settings = generatorSettings(node);
  const value = settingsToCompactJson(settings);
  if (widget) {
    widget.value = value;
    widget.callback?.(value);
  }
  if (!serialized || !Array.isArray(serialized.widgets_values)) {
    return settings;
  }
  serialized.widgets_values.length = 0;
  serialized.widgets_values.push(value);
  return settings;
}

function markNodeDirty(node) {
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
}

function stopGeneratorControlPropagation(root) {
  if (!root || root.__easyuseAnimaAioStopPropagation) {
    return;
  }
  const stop = (event) => {
    if (event.target?.closest?.(GENERATOR_PANEL_CONTROL_SELECTOR)) {
      event.stopPropagation();
    }
  };
  for (const eventName of [
    "pointerdown",
    "mousedown",
    "pointerup",
    "mouseup",
    "click",
    "dblclick",
    "keydown",
    "keyup",
  ]) {
    root.addEventListener(eventName, stop);
  }
  root.addEventListener("wheel", (event) => {
    const previewFeed = event.target?.closest?.(".easyuse-anima-aio-node-preview-feed");
    if (previewFeed && previewFeed.scrollWidth > previewFeed.clientWidth) {
      event.preventDefault();
      event.stopPropagation();
      previewFeed.scrollLeft += event.deltaX || event.deltaY;
      return;
    }
    const scrollArea = event.target?.closest?.(".easyuse-anima-aio-node-settings-scroll");
    if (scrollArea && scrollArea.scrollHeight > scrollArea.clientHeight) {
      event.stopPropagation();
      return;
    }
    if (event.target?.closest?.(GENERATOR_PANEL_CONTROL_SELECTOR)) {
      return;
    }
    const canvas = app?.canvas?.canvas;
    if (!canvas) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    canvas.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      cancelable: true,
      deltaX: event.deltaX,
      deltaY: event.deltaY,
      deltaZ: event.deltaZ,
      deltaMode: event.deltaMode,
      clientX: event.clientX,
      clientY: event.clientY,
      screenX: event.screenX,
      screenY: event.screenY,
      ctrlKey: event.ctrlKey,
      shiftKey: event.shiftKey,
      altKey: event.altKey,
      metaKey: event.metaKey,
    }));
  }, { passive: false });
  root.__easyuseAnimaAioStopPropagation = true;
}

function samplerModeLabel(settingsOrBackend) {
  const settings = typeof settingsOrBackend === "object" && settingsOrBackend
    ? settingsOrBackend
    : null;
  const sampler = settings?.sampler || {};
  const backend = String(settings ? sampler.backend : settingsOrBackend || "comfy_ksampler");
  const corrections = !!sampler?.dit_corrections?.enabled;
  const spectrum = !!sampler?.spectrum?.enabled;
  switch (backend) {
    case "spectrum_mod_guidance_advanced":
      return corrections ? "Spectrum Mod Guidance + Corrections" : "Spectrum Mod Guidance";
    case "spectrum_spd_speed":
      return "Spectrum SPD / SPEED";
    case "comfy_ksampler": {
      const extras = [];
      if (spectrum) {
        extras.push("Spectrum Patch");
      }
      if (corrections) {
        extras.push("Corrections");
      }
      return extras.length ? `${extras.join(" + ")} / Comfy KSampler` : "Standard Comfy KSampler";
    }
    default:
      return "Standard Comfy KSampler";
  }
}

function generatorPanelWidth(node) {
  return Math.max(240, Math.floor((Number(node?.size?.[0]) || GENERATOR_NODE_DEFAULT_WIDTH) - 20));
}

function generatorPanelWidget(node) {
  return node?.__easyuseAnimaGeneratorPanelWidget
    || node?.widgets?.find?.((widget) => widget?.name === GENERATOR_DOM_WIDGET)
    || null;
}

function generatorNodeChromeOffset(node) {
  const widget = generatorPanelWidget(node);
  const widgetY = Math.max(Number(widget?.last_y) || 0, Number(widget?.y) || 0);
  return Math.ceil(Math.max(70, widgetY + 12));
}

function generatorPanelHeight(node) {
  return Math.max(GENERATOR_PANEL_MIN_HEIGHT, Number(node?.__easyuseAnimaGeneratorPanelHeight) || 0);
}

function generatorPanelMinHeight(node) {
  return Math.max(GENERATOR_PANEL_MIN_HEIGHT, Number(node?.__easyuseAnimaGeneratorPanelMinHeight) || 0);
}

function generatorAvailablePanelHeight(node) {
  const nodeHeight = Number(node?.size?.[1]) || 0;
  if (nodeHeight <= 0) {
    return 0;
  }
  return Math.max(0, Math.floor(nodeHeight - generatorNodeChromeOffset(node)));
}

function measureGeneratorPanelContentHeight(node) {
  const panel = node?.__easyuseAnimaGeneratorPanelEl;
  if (!panel) {
    return GENERATOR_PANEL_MIN_HEIGHT;
  }
  const minHeight = GENERATOR_PANEL_MIN_HEIGHT;
  node.__easyuseAnimaGeneratorPanelMinHeight = minHeight;
  return minHeight;
}

function generatorMinimumNodeHeight(node) {
  return Math.ceil(generatorPanelMinHeight(node) + generatorNodeChromeOffset(node));
}

function applyGeneratorLayout(node) {
  const panel = node?.__easyuseAnimaGeneratorPanelEl;
  if (!panel || !node.size || node.__easyuseAnimaGeneratorApplyingLayout) {
    return;
  }
  node.__easyuseAnimaGeneratorApplyingLayout = true;
  try {
    const width = generatorPanelWidth(node);
    panel.style.width = `${width}px`;
    panel.style.maxWidth = `${width}px`;
    const minPanelHeight = measureGeneratorPanelContentHeight(node);
    const panelHeight = Math.max(minPanelHeight, generatorAvailablePanelHeight(node));
    node.__easyuseAnimaGeneratorPanelHeight = panelHeight;
    panel.style.height = `${panelHeight}px`;
    const currentWidth = Number(node.size[0]) || GENERATOR_NODE_DEFAULT_WIDTH;
    const currentHeight = Number(node.size[1]) || 0;
    const minHeight = generatorMinimumNodeHeight(node);
    if (currentHeight < minHeight - 1 || currentWidth < GENERATOR_NODE_MIN_WIDTH) {
      node.setSize?.([
        Math.max(currentWidth, GENERATOR_NODE_DEFAULT_WIDTH),
        Math.max(currentHeight, minHeight),
      ]);
    }
    markNodeDirty(node);
  } finally {
    node.__easyuseAnimaGeneratorApplyingLayout = false;
  }
}

function scheduleGeneratorLayout(node) {
  if (!node?.__easyuseAnimaGeneratorPanelEl || node.__easyuseAnimaGeneratorLayoutScheduled) {
    return;
  }
  node.__easyuseAnimaGeneratorLayoutScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaGeneratorLayoutScheduled = false;
    applyGeneratorLayout(node);
  });
}

function generatorSettings(node) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  return mergeVisibleGeneratorSettings(node, parseSettings(widget, DEFAULT_GENERATION_SETTINGS));
}

function writeGeneratorSettingsFromState(node, settings, markDirty = true) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  writeSettings(node, widget, settings, markDirty);
}

function updateGeneratorSettings(node, updater, markDirty = true) {
  const settings = generatorSettings(node);
  updater?.(settings);
  settings.sampler.seed_after_generate = normalizeSeedControl(settings.sampler.seed_after_generate);
  applyVisibleGeneratorSettings(node, settings);
  writeGeneratorSettingsFromState(node, settings, markDirty);
  updateGeneratorDomSummary(node);
  return settings;
}

function updateGeneratorDomSummary(node) {
  const panel = node?.__easyuseAnimaGeneratorPanelEl;
  if (!panel) {
    return;
  }
  const status = node.__easyuseAnimaGeneratorStatus || {};
  const settings = generatorSettings(node);
  const backendSummaryEl = panel.querySelector("[data-aio-backend-summary]");
  const saveButtonEl = panel.querySelector("[data-aio-save-button]");
  if (saveButtonEl) {
    saveButtonEl.classList.toggle("active", !!settings.save.enabled);
    saveButtonEl.title = settings.save.enabled ? aioText("button.saveOn") : aioText("button.saveOff");
  }
  if (backendSummaryEl) {
    backendSummaryEl.textContent = samplerModeLabel(settings);
    backendSummaryEl.title = samplerModeLabel(settings);
  }
  updateGeneratorDomPreview(node);
}

function updateGeneratorDomPreview(node) {
  const panel = node?.__easyuseAnimaGeneratorPanelEl;
  const previewBox = panel?.querySelector?.("[data-aio-preview-box]");
  if (!previewBox) {
    return;
  }
  const settings = generatorSettings(node);
  const images = Array.isArray(node.__easyuseAnimaGeneratorPreviewImages)
    ? node.__easyuseAnimaGeneratorPreviewImages
    : [];
  if (!images.length) {
    const feed = panel?.querySelector?.("[data-aio-preview-feed]");
    if (feed) {
      feed.hidden = true;
      feed.replaceChildren();
    }
    const metaEl = panel.querySelector("[data-aio-preview-meta]");
    if (metaEl) {
      metaEl.textContent = "-";
      metaEl.title = "";
    }
    return;
  }
  const currentImage = generatorMainPreviewImage(node, images);
  const imageUrl = generatorImageUrl(currentImage);
  if (!currentImage || !imageUrl) {
    return;
  }
  const selectedIndex = generatorSelectedPreviewIndex(node, images);
  const metaEl = panel.querySelector("[data-aio-preview-meta]");
  if (metaEl) {
    const parts = [
      generatorPreviewImageName(currentImage),
      generatorPreviewResolution(currentImage),
      generatorPreviewFileSize(currentImage),
    ].filter((part) => part && part !== "-");
    const metaText = parts.length ? parts.join(" · ") : "-";
    metaEl.textContent = metaText;
    metaEl.title = metaText === "-" ? "" : metaText;
  }

  const makeImage = (image) => {
    const img = document.createElement("img");
    img.src = generatorImageUrl(image);
    img.alt = "";
    img.loading = "lazy";
    return img;
  };
  const makeLayer = (className, label, image) => {
    const pane = document.createElement("div");
    pane.className = `easyuse-anima-aio-node-preview-layer ${className}`.trim();
    const labelEl = document.createElement("div");
    labelEl.className = "easyuse-anima-aio-node-preview-pane-label";
    labelEl.textContent = label;
    pane.append(labelEl, makeImage(image));
    return pane;
  };
  const previousImage = selectedIndex > 0 ? images[selectedIndex - 1] : null;
  const canCompare = (
    settings.preview.compare_previous
    && previousImage
    && generatorImageUrl(previousImage)
  );
  if (canCompare) {
    const compare = document.createElement("div");
    compare.className = "easyuse-anima-aio-node-preview-compare";
    compare.style.setProperty("--aio-compare-x", "50%");
    const updateCompareX = (event) => {
      const rect = compare.getBoundingClientRect();
      const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
      const percent = rect.width > 0 ? (x / rect.width) * 100 : 50;
      compare.style.setProperty("--aio-compare-x", `${percent.toFixed(2)}%`);
    };
    for (const eventName of ["pointerdown", "pointermove"]) {
      compare.addEventListener(eventName, (event) => {
        event.stopPropagation();
        updateCompareX(event);
      });
    }
    compare.append(
      makeLayer("before", `${aioText("text.previewPrevious")} · ${generatorPreviewImageLabel(previousImage)}`, previousImage),
      makeLayer("after", `${aioText("text.previewCurrent")} · ${generatorPreviewImageLabel(currentImage)}`, currentImage),
      Object.assign(document.createElement("div"), { className: "easyuse-anima-aio-node-preview-divider" }),
    );
    previewBox.replaceChildren(compare);
  } else {
    previewBox.replaceChildren(makeImage(currentImage));
  }

  const feed = panel?.querySelector?.("[data-aio-preview-feed]");
  if (!feed) {
    return;
  }
  feed.replaceChildren();
  feed.hidden = !settings.preview.image_feed;
  if (feed.hidden) {
    return;
  }
  let selectedThumb = null;
  for (const [index, image] of images.entries()) {
    const thumbUrl = generatorImageUrl(image);
    if (!thumbUrl) {
      continue;
    }
    const thumb = document.createElement("button");
    thumb.type = "button";
    thumb.className = "easyuse-anima-aio-node-preview-thumb";
    if (index === selectedIndex) {
      thumb.classList.add("active");
      selectedThumb = thumb;
    }
    thumb.title = generatorPreviewImageLabel(image);
    const thumbImage = document.createElement("img");
    thumbImage.src = thumbUrl;
    thumbImage.alt = "";
    thumbImage.loading = "lazy";
    const label = document.createElement("span");
    label.textContent = generatorPreviewImageLabel(image);
    thumb.append(thumbImage, label);
    thumb.addEventListener("click", () => {
      node.__easyuseAnimaSelectedPreviewIndex = index;
      updateGeneratorDomPreview(node);
    });
    feed.append(thumb);
  }
  selectedThumb?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
}

function suppressGeneratorDefaultPreview(node) {
  if (!node) {
    return;
  }
  node.imgs = [];
  node.images = [];
  node.imageIndex = null;
  node.overIndex = null;
  markNodeDirty(node);
}

function createNodeField(label, control, className = "", tooltipKey = "") {
  const wrapper = document.createElement("div");
  wrapper.className = `easyuse-anima-aio-node-field ${className}`.trim();
  const labelEl = document.createElement("label");
  labelEl.textContent = label;
  applyTooltip(wrapper, tooltipKey);
  applyTooltip(labelEl, tooltipKey);
  applyTooltip(control, tooltipKey);
  wrapper.append(labelEl, control);
  return wrapper;
}

function createDomNumberControl(node, name, value, step = "1") {
  const input = numberInput(value, step);
  input.addEventListener("input", () => {
    const nextValue = name === "seed"
      ? normalizeSeedValue(input.value, GENERATOR_SPECIAL_SEED_RANDOM)
      : Number(input.value || 0);
    setWidgetValueIfChanged(node, name, nextValue);
    syncGeneratorSettingsFromVisible(node);
    updateGeneratorDomSummary(node);
    if (name === "seed") {
      refreshGeneratorSeedButtons(node);
    }
    markNodeDirty(node);
  });
  return input;
}

function createDomSliderNumberControl(node, name, value, options = {}) {
  const min = Number(options.min ?? 0);
  const max = Number(options.max ?? 100);
  const step = Number(options.step ?? 1);
  const decimals = Number(options.decimals ?? 0);
  const clamp = (next) => Math.max(min, Math.min(max, Number(next)));
  const snap = (next) => {
    const clamped = clamp(next);
    if (!Number.isFinite(step) || step <= 0) {
      return clamped;
    }
    return min + Math.round((clamped - min) / step) * step;
  };
  const round = (next) => {
    const factor = 10 ** decimals;
    return Math.round(clamp(snap(next)) * factor) / factor;
  };
  const currentValue = round(value);
  const wrapper = document.createElement("div");
  wrapper.className = "easyuse-anima-aio-node-slider-control";
  const input = numberInput(currentValue, String(step));
  input.min = String(min);
  input.max = String(max);
  const track = document.createElement("div");
  track.className = "easyuse-anima-aio-node-slider-track";
  const rail = document.createElement("div");
  rail.className = "easyuse-anima-aio-node-slider-rail";
  const fill = document.createElement("div");
  fill.className = "easyuse-anima-aio-node-slider-fill";
  const thumb = document.createElement("div");
  thumb.className = "easyuse-anima-aio-node-slider-thumb";
  track.append(rail, fill, thumb);

  const normalizeValue = typeof options.normalize === "function"
    ? options.normalize
    : (next) => (name === "steps" ? Math.trunc(next) : next);
  const commit = (nextValue) => {
    const next = round(nextValue);
    input.value = String(next);
    const normalized = normalizeValue(next);
    if (typeof options.onCommit === "function") {
      options.onCommit(normalized);
    } else {
      setWidgetValueIfChanged(node, name, normalized);
      syncGeneratorSettingsFromVisible(node);
    }
    updateGeneratorDomSummary(node);
    updateSlider();
    markNodeDirty(node);
  };
  const updateSlider = () => {
    const next = round(input.value || currentValue);
    const percent = max <= min ? 0 : ((next - min) / (max - min)) * 100;
    const clampedPercent = Math.max(0, Math.min(100, percent));
    fill.style.width = `${clampedPercent}%`;
    thumb.style.left = `${clampedPercent}%`;
  };
  const valueFromPointer = (pointerEvent) => {
    const rect = track.getBoundingClientRect();
    const relative = rect.width > 0 ? (pointerEvent.clientX - rect.left) / rect.width : 0;
    return round(min + Math.max(0, Math.min(1, relative)) * (max - min));
  };

  input.addEventListener("input", () => commit(input.value));
  track.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const pointerId = event.pointerId;
    track.setPointerCapture?.(pointerId);
    commit(valueFromPointer(event));
    const move = (moveEvent) => {
      moveEvent.preventDefault();
      moveEvent.stopPropagation();
      commit(valueFromPointer(moveEvent));
    };
    const up = (upEvent) => {
      upEvent.stopPropagation();
      track.releasePointerCapture?.(pointerId);
      window.removeEventListener("pointermove", move, true);
      window.removeEventListener("pointerup", up, true);
    };
    window.addEventListener("pointermove", move, true);
    window.addEventListener("pointerup", up, true);
  });
  wrapper.append(input, track);
  updateSlider();
  return wrapper;
}

function createDomSettingsSliderNumberControl(node, value, options, updater) {
  return createDomSliderNumberControl(node, "__settings__", value, {
    ...options,
    onCommit(nextValue) {
      updateGeneratorSettings(node, (settings) => {
        updater?.(settings, nextValue);
      });
    },
  });
}

function createDomTextControl(node, name, value) {
  const input = textInput(value);
  input.addEventListener("input", () => {
    setWidgetValueIfChanged(node, name, input.value);
    syncGeneratorSettingsFromVisible(node);
    updateGeneratorDomSummary(node);
    markNodeDirty(node);
  });
  return input;
}

function createDomCheckboxControl(node, name, value) {
  const input = checkbox(value);
  input.addEventListener("change", () => {
    setWidgetValueIfChanged(node, name, input.checked);
    syncGeneratorSettingsFromVisible(node);
    updateGeneratorDomSummary(node);
    markNodeDirty(node);
  });
  return input;
}

function createDomSettingsCheckboxControl(node, value, updater, options = {}) {
  const input = checkbox(value);
  input.addEventListener("change", () => {
    updateGeneratorSettings(node, (settings) => {
      updater?.(settings, input.checked);
    });
    if (options.rerender) {
      renderGeneratorPanel(node);
    } else {
      updateGeneratorDomSummary(node);
      scheduleGeneratorLayout(node);
      markNodeDirty(node);
    }
  });
  return input;
}

function createDomSettingsNumberControl(node, value, step, updater, options = {}) {
  const input = numberInput(value, step);
  if (options.min != null) {
    input.min = String(options.min);
  }
  if (options.max != null) {
    input.max = String(options.max);
  }
  const decimals = Number(options.decimals ?? 0);
  const commit = () => {
    const fallback = Number(value) || 0;
    const min = Number(options.min ?? -Infinity);
    const max = Number(options.max ?? Infinity);
    const factor = 10 ** decimals;
    const clamped = clampGeneratorNumber(input.value, fallback, min, max);
    const nextValue = decimals > 0 ? Math.round(clamped * factor) / factor : Math.trunc(clamped);
    input.value = nextValue;
    updateGeneratorSettings(node, (settings) => {
      updater?.(settings, nextValue);
    });
    if (options.rerender) {
      renderGeneratorPanel(node);
    } else {
      updateGeneratorDomSummary(node);
      scheduleGeneratorLayout(node);
      markNodeDirty(node);
    }
  };
  input.addEventListener("input", commit);
  return input;
}

function createDomSelectControl(node, name, value, fallbackOptions = []) {
  const select = selectInput(widgetOptions(node, name, fallbackOptions), String(value ?? ""));
  select.addEventListener("change", () => {
    setWidgetValueIfChanged(node, name, select.value);
    syncGeneratorSettingsFromVisible(node);
    updateGeneratorDomSummary(node);
    markNodeDirty(node);
  });
  return select;
}

function createSeedControlSelect(node, value) {
  const select = selectInput(GENERATOR_SEED_CONTROLS, normalizeSeedControl(value));
  select.addEventListener("change", () => {
    updateGeneratorSettings(node, (settings) => {
      settings.sampler.seed_after_generate = normalizeSeedControl(select.value);
    });
    markNodeDirty(node);
  });
  return select;
}

function syncGeneratorStateFromDom(node) {
  const settings = generatorSettings(node);
  writeGeneratorSettingsFromState(node, settings, false);
}

function randomSeed() {
  const limit = GENERATOR_MAX_SEED;
  let seed;
  if (globalThis.crypto?.getRandomValues) {
    const values = new Uint32Array(2);
    globalThis.crypto.getRandomValues(values);
    seed = Number((BigInt(values[0]) << 21n) + BigInt(values[1] & 0x1fffff)) % limit;
  } else {
    seed = Math.floor(Math.random() * limit);
  }
  return isSpecialSeed(seed) ? 0 : seed;
}

function setGeneratorSeedFromUi(node, value) {
  const seed = normalizeSeedValue(value, GENERATOR_SPECIAL_SEED_RANDOM);
  const panel = node?.__easyuseAnimaGeneratorPanelEl;
  const seedInput = panel?.querySelector?.("[data-aio-seed-input]");
  if (seedInput) {
    seedInput.value = seed;
  }
  setWidgetValueIfChanged(node, "seed", seed);
  syncGeneratorSettingsFromVisible(node);
  updateGeneratorDomSummary(node);
  refreshGeneratorSeedButtons(node);
  markNodeDirty(node);
}

function refreshGeneratorSeedButtons(node) {
  const panel = node?.__easyuseAnimaGeneratorPanelEl;
  if (!panel) {
    return;
  }
  const lastSeed = node.__easyuseAnimaLastQueuedSeed;
  const currentSeed = normalizeSeedValue(widgetValue(node, "seed", GENERATOR_SPECIAL_SEED_RANDOM));
  const lastButton = panel.querySelector("[data-aio-seed-last]");
  if (lastButton) {
    const hasLastSeed = lastSeed != null;
    lastButton.disabled = !hasLastSeed || Number(lastSeed) === currentSeed;
    lastButton.textContent = hasLastSeed
      ? aioFormat("button.useLast", { seed: lastSeed })
      : aioText("button.useLastNone");
    lastButton.title = aioText("tip.useLast");
  }
}

function renderGeneratorPanel(node) {
  const panel = node?.__easyuseAnimaGeneratorPanelEl;
  if (!panel) {
    return;
  }
  const settings = generatorSettings(node);
  panel.replaceChildren();

  const makeButton = (label, callback, className = "", tooltipKey = "") => {
    const button = document.createElement("button");
    button.className = `easyuse-anima-aio-node-button ${className}`.trim();
    button.type = "button";
    button.textContent = label;
    applyTooltip(button, tooltipKey);
    button.addEventListener("click", callback);
    return button;
  };
  const makeIconButton = (label, callback, tooltipKey = "") => {
    const button = document.createElement("button");
    button.className = "easyuse-anima-aio-node-icon-button";
    button.type = "button";
    button.textContent = label;
    applyTooltip(button, tooltipKey);
    button.addEventListener("click", callback);
    return button;
  };
  const makeCardHeader = (title, actions = []) => {
    const header = document.createElement("div");
    header.className = "easyuse-anima-aio-node-card-header";
    const titleEl = document.createElement("div");
    titleEl.className = "easyuse-anima-aio-node-card-title";
    titleEl.textContent = title;
    const actionBox = document.createElement("div");
    actionBox.className = "easyuse-anima-aio-node-card-actions";
    actionBox.append(...actions.filter(Boolean));
    header.append(titleEl, actionBox);
    return header;
  };
  const makeStageHeader = (title, toggle, tooltipKey = "", actions = []) => {
    const header = document.createElement("div");
    header.className = "easyuse-anima-aio-node-stage-header";
    const titleEl = document.createElement("div");
    titleEl.className = "easyuse-anima-aio-node-stage-title";
    titleEl.textContent = title;
    applyTooltip(titleEl, tooltipKey);
    const toggleLabel = document.createElement("label");
    toggleLabel.className = "easyuse-anima-aio-node-stage-toggle";
    toggleLabel.append(toggle, document.createTextNode(aioText("label.enabled")));
    applyTooltip(toggleLabel, tooltipKey);
    const actionBox = document.createElement("div");
    actionBox.className = "easyuse-anima-aio-node-stage-tools";
    actionBox.append(...actions.filter(Boolean), toggleLabel);
    header.append(titleEl, actionBox);
    return header;
  };
  const makeNote = (textKey, tooltipKey = "") => {
    const note = document.createElement("div");
    note.className = "easyuse-anima-aio-node-stage-note";
    note.textContent = aioText(textKey);
    applyTooltip(note, tooltipKey);
    return note;
  };
  const moveDetailerTarget = (targetName, delta) => {
    updateGeneratorSettings(node, (nextSettings) => {
      const order = normalizeDetailerOrder(nextSettings.detailer?.order);
      const currentIndex = order.indexOf(targetName);
      const nextIndex = currentIndex + delta;
      if (currentIndex < 0 || nextIndex < 0 || nextIndex >= order.length) {
        return;
      }
      [order[currentIndex], order[nextIndex]] = [order[nextIndex], order[currentIndex]];
      nextSettings.detailer ||= {};
      nextSettings.detailer.order = order;
    });
    renderGeneratorPanel(node);
  };

  const main = document.createElement("div");
  main.className = "easyuse-anima-aio-node-main";

  const samplerCard = document.createElement("section");
  samplerCard.className = "easyuse-anima-aio-node-card easyuse-anima-aio-node-settings";
  const saveIcon = makeIconButton("💾", () => openSaveSettings(node), "tip.saveOptions");
  saveIcon.setAttribute("data-aio-save-button", "");
  const samplerHeader = makeCardHeader(aioText("title.sampler"), [
    makeIconButton("⚙", () => openSamplerSettings(node), "tip.samplerDetails"),
    makeIconButton("⋯", () => openAdvancedSettings(node), "tip.advancedOptions"),
    saveIcon,
  ]);
  const settingsScroll = document.createElement("div");
  settingsScroll.className = "easyuse-anima-aio-node-settings-scroll";

  const samplerGrid = document.createElement("div");
  samplerGrid.className = "easyuse-anima-aio-node-sampler-grid";

  const seedBlock = document.createElement("div");
  const seedInput = createDomNumberControl(node, "seed", settings.sampler.seed);
  seedInput.setAttribute("data-aio-seed-input", "");
  applyTooltip(seedInput, "tip.seed");
  const seedActions = document.createElement("div");
  seedActions.className = "easyuse-anima-aio-node-seed-actions";
  const seedRandomEach = makeButton(
    aioText("button.randomEach"),
    () => setGeneratorSeedFromUi(node, GENERATOR_SPECIAL_SEED_RANDOM),
    "",
    "tip.randomEach",
  );
  const seedNewFixed = makeButton(
    aioText("button.newFixed"),
    () => setGeneratorSeedFromUi(node, randomSeed()),
    "",
    "tip.newFixed",
  );
  const seedLast = makeButton(
    aioText("button.useLastNone"),
    () => {
      if (node.__easyuseAnimaLastQueuedSeed == null) {
        return;
      }
      setGeneratorSeedFromUi(node, node.__easyuseAnimaLastQueuedSeed);
    },
    "",
    "tip.useLast",
  );
  seedLast.setAttribute("data-aio-seed-last", "");
  seedActions.append(seedRandomEach, seedNewFixed, seedLast);
  seedBlock.append(seedInput, seedActions);

  const modeBadge = Object.assign(document.createElement("div"), {
    className: "easyuse-anima-aio-node-mode-badge",
  });
  modeBadge.setAttribute("data-aio-backend-summary", "");
  samplerGrid.append(
    createNodeField(aioText("label.mode"), modeBadge, "wide", "tip.mode"),
    createNodeField(aioText("label.seed"), seedBlock, "seed", "tip.seed"),
    createNodeField(
      aioText("label.steps"),
      createDomSliderNumberControl(node, "steps", settings.sampler.steps, {
        min: 1,
        max: 75,
        step: 1,
        decimals: 0,
      }),
      "wide",
      "tip.steps",
    ),
    createNodeField(
      aioText("label.cfg"),
      createDomSliderNumberControl(node, "cfg", settings.sampler.cfg, {
        min: 1,
        max: 10,
        step: 0.1,
        decimals: 1,
      }),
      "wide",
      "tip.cfg",
    ),
    createNodeField(
      aioText("label.shift"),
      createDomSettingsSliderNumberControl(
        node,
        settings.model_patches.aura_flow.shift ?? DEFAULT_GENERATION_SETTINGS.model_patches.aura_flow.shift,
        {
          min: 1,
          max: 10,
          step: 0.5,
          decimals: 1,
        },
        (nextSettings, value) => {
          nextSettings.model_patches.aura_flow ||= {};
          delete nextSettings.model_patches.aura_flow.enabled;
          nextSettings.model_patches.aura_flow.shift = value;
        },
      ),
      "wide",
      "tip.shift",
    ),
    createNodeField(
      aioText("label.denoise"),
      createDomNumberControl(node, "denoise", settings.sampler.denoise, "0.01"),
      "",
      "tip.denoise",
    ),
    createNodeField(
      aioText("label.sampler"),
      createDomSelectControl(node, "sampler_name", settings.sampler.sampler_name, GENERATOR_FALLBACK_SAMPLER_NAMES),
      "wide",
      "tip.sampler",
    ),
    createNodeField(
      aioText("label.scheduler"),
      createDomSelectControl(node, "scheduler", settings.sampler.scheduler, GENERATOR_FALLBACK_SCHEDULER_NAMES),
      "wide",
      "tip.scheduler",
    ),
  );

  const highresBlock = document.createElement("div");
  highresBlock.className = "easyuse-anima-aio-node-stage-block";
  const highresEnabled = createDomSettingsCheckboxControl(
    node,
    settings.highres.enabled,
    (nextSettings, value) => {
      nextSettings.highres ||= {};
      nextSettings.highres.enabled = value;
    },
    { rerender: true },
  );
  highresBlock.append(makeStageHeader(
    aioText("title.highres"),
    highresEnabled,
    "tip.highresEnabled",
    [makeIconButton("⚙", () => openHighresSettings(node), "tip.highresSettings")],
  ));
  const highresBody = document.createElement("div");
  highresBody.className = "easyuse-anima-aio-node-stage-body";
  if (settings.highres.enabled) {
    const followMain = createDomSettingsCheckboxControl(
      node,
      settings.highres.inherit_sampler_settings,
      (nextSettings, value) => {
        nextSettings.highres ||= {};
        nextSettings.highres.inherit_sampler_settings = value;
      },
      { rerender: true },
    );
    highresBody.append(
      createNodeField(aioText("label.followMainSampler"), followMain, "wide", "tip.highresFollow"),
      makeNote(
        settings.highres.inherit_sampler_settings ? "text.inheritsMainSampler" : "text.usesStageSamplerOverride",
        "tip.highresFollow",
      ),
      createNodeField(
        aioText("label.scaleBy"),
        createDomSettingsSliderNumberControl(
          node,
          settings.highres.scale_by,
          { min: 1, max: 4, step: 0.05, decimals: 2 },
          (nextSettings, value) => {
            nextSettings.highres ||= {};
            nextSettings.highres.scale_by = value;
          },
        ),
        "wide",
        "tip.highresScale",
      ),
      createNodeField(
        aioText("label.steps"),
        createDomSettingsSliderNumberControl(
          node,
          settings.highres.steps,
          { min: 1, max: 75, step: 1, decimals: 0 },
          (nextSettings, value) => {
            nextSettings.highres ||= {};
            nextSettings.highres.steps = Math.trunc(value);
          },
        ),
        "wide",
        "tip.highresSteps",
      ),
      createNodeField(
        aioText("label.denoise"),
        createDomSettingsSliderNumberControl(
          node,
          settings.highres.denoise,
          { min: 0, max: 1, step: 0.01, decimals: 2 },
          (nextSettings, value) => {
            nextSettings.highres ||= {};
            nextSettings.highres.denoise = value;
          },
        ),
        "wide",
        "tip.highresDenoise",
      ),
      createNodeField(
        aioText("label.maxLongEdge"),
        createDomSettingsNumberControl(
          node,
          settings.highres.max_long_edge,
          "32",
          (nextSettings, value) => {
            nextSettings.highres ||= {};
            nextSettings.highres.max_long_edge = Math.trunc(value);
          },
          { min: 0, max: 16384, decimals: 0 },
        ),
        "wide",
        "tip.highresMaxEdge",
      ),
    );
  } else {
    highresBody.append(makeNote("text.highresDisabled", "tip.highresEnabled"));
  }
  highresBlock.append(highresBody);

  const detailerBlock = document.createElement("div");
  detailerBlock.className = "easyuse-anima-aio-node-stage-block";
  const detailerEnabled = createDomSettingsCheckboxControl(
    node,
    settings.detailer.enabled,
    (nextSettings, value) => {
      nextSettings.detailer ||= {};
      nextSettings.detailer.enabled = value;
    },
    { rerender: true },
  );
  detailerBlock.append(makeStageHeader(
    aioText("title.detailer"),
    detailerEnabled,
    "tip.detailerEnabled",
    [makeIconButton("⚙", () => openDetailerSettings(node), "tip.detailerSettings")],
  ));
  const detailerBody = document.createElement("div");
  detailerBody.className = "easyuse-anima-aio-node-stage-body";
  if (settings.detailer.enabled) {
    const order = normalizeDetailerOrder(settings.detailer.order);
    for (const [index, targetName] of order.entries()) {
      const defaults = DEFAULT_GENERATION_SETTINGS.detailer[targetName];
      const target = mergeDefaults(defaults, settings.detailer[targetName] || {});
      const targetBlock = document.createElement("div");
      targetBlock.className = "easyuse-anima-aio-node-stage-mini";
      applyTooltip(targetBlock, "tip.detailerBlock");
      const targetHeader = document.createElement("div");
      targetHeader.className = "easyuse-anima-aio-node-stage-mini-header";
      const targetTitle = document.createElement("div");
      targetTitle.className = "easyuse-anima-aio-node-stage-mini-title";
      targetTitle.textContent = `${index + 1}. ${aioText(targetName === "face" ? "label.face" : "label.eye")}`;
      applyTooltip(targetTitle, "tip.detailerBlock");
      const targetTools = document.createElement("div");
      targetTools.className = "easyuse-anima-aio-node-stage-tools";
      const moveUp = makeIconButton("↑", () => moveDetailerTarget(targetName, -1), "tip.detailerOrder");
      const moveDown = makeIconButton("↓", () => moveDetailerTarget(targetName, 1), "tip.detailerOrder");
      moveUp.disabled = index === 0;
      moveDown.disabled = index === order.length - 1;
      targetTools.append(moveUp, moveDown);
      targetHeader.append(targetTitle, targetTools);
      targetBlock.append(targetHeader);

      const targetGrid = document.createElement("div");
      targetGrid.className = "easyuse-anima-aio-node-stage-body";
      const targetEnabled = createDomSettingsCheckboxControl(
        node,
        target.enabled,
        (nextSettings, value) => {
          nextSettings.detailer ||= {};
          nextSettings.detailer[targetName] ||= {};
          nextSettings.detailer[targetName].enabled = value;
        },
        { rerender: true },
      );
      targetGrid.append(createNodeField(aioText("label.enabled"), targetEnabled, "wide", "tip.detailerBlock"));
      if (target.enabled) {
        const followMain = createDomSettingsCheckboxControl(
          node,
          target.inherit_sampler_settings,
          (nextSettings, value) => {
            nextSettings.detailer ||= {};
            nextSettings.detailer[targetName] ||= {};
            nextSettings.detailer[targetName].inherit_sampler_settings = value;
          },
          { rerender: true },
        );
        targetGrid.append(
          createNodeField(aioText("label.followMainSampler"), followMain, "wide", "tip.detailerFollow"),
          makeNote(
            target.inherit_sampler_settings ? "text.inheritsMainSampler" : "text.usesStageSamplerOverride",
            "tip.detailerFollow",
          ),
          createNodeField(
            aioText("label.steps"),
            createDomSettingsSliderNumberControl(
              node,
              target.steps,
              { min: 1, max: 75, step: 1, decimals: 0 },
              (nextSettings, value) => {
                nextSettings.detailer ||= {};
                nextSettings.detailer[targetName] ||= {};
                nextSettings.detailer[targetName].steps = Math.trunc(value);
              },
            ),
            "wide",
            "tip.detailerSteps",
          ),
          createNodeField(
            aioText("label.denoise"),
            createDomSettingsSliderNumberControl(
              node,
              target.denoise,
              { min: 0, max: 1, step: 0.01, decimals: 2 },
              (nextSettings, value) => {
                nextSettings.detailer ||= {};
                nextSettings.detailer[targetName] ||= {};
                nextSettings.detailer[targetName].denoise = value;
              },
            ),
            "wide",
            "tip.detailerDenoise",
          ),
        );
      }
      targetBlock.append(targetGrid);
      detailerBody.append(targetBlock);
    }
  } else {
    detailerBody.append(makeNote("text.detailerDisabled", "tip.detailerEnabled"));
  }
  detailerBlock.append(detailerBody);

  settingsScroll.append(samplerGrid, highresBlock, detailerBlock);

  samplerCard.append(samplerHeader, settingsScroll);

  const previewCard = document.createElement("section");
  previewCard.className = "easyuse-anima-aio-node-card easyuse-anima-aio-node-preview";
  const previewHeader = makeCardHeader(aioText("title.preview"), [
    makeIconButton("⚙", () => openPreviewSettings(node), "tip.previewOptions"),
  ]);
  const previewBox = document.createElement("div");
  previewBox.className = "easyuse-anima-aio-node-preview-box";
  previewBox.setAttribute("data-aio-preview-box", "");
  const previewPlaceholder = document.createElement("div");
  previewPlaceholder.className = "easyuse-anima-aio-node-preview-placeholder";
  const previewStrong = document.createElement("strong");
  previewStrong.textContent = aioText("text.previewTitle");
  const previewText = document.createElement("span");
  previewText.textContent = aioText("text.previewSubtitle");
  previewPlaceholder.append(previewStrong, previewText);
  previewBox.append(previewPlaceholder);

  const previewMeta = document.createElement("div");
  previewMeta.className = "easyuse-anima-aio-node-preview-meta";
  previewMeta.setAttribute("data-aio-preview-meta", "");
  previewMeta.textContent = "-";
  applyTooltip(previewMeta, "tip.size");

  const previewFeed = document.createElement("div");
  previewFeed.className = "easyuse-anima-aio-node-preview-feed";
  previewFeed.setAttribute("data-aio-preview-feed", "");
  previewFeed.hidden = true;

  previewCard.append(previewHeader, previewBox, previewMeta, previewFeed);

  main.append(samplerCard, previewCard);
  panel.append(main);
  stopGeneratorControlPropagation(panel);
  updateGeneratorDomSummary(node);
  refreshGeneratorSeedButtons(node);
  scheduleGeneratorLayout(node);
}

function ensureGeneratorPanel(node) {
  ensureStyle();
  node.serialize_widgets = true;
  node.minWidth = Math.max(Number(node.minWidth) || 0, GENERATOR_NODE_MIN_WIDTH);
  if (Array.isArray(node.size)) {
    node.size[0] = Math.max(Number(node.size[0]) || 0, GENERATOR_NODE_DEFAULT_WIDTH);
  }
  if (!node.__easyuseAnimaGeneratorPanelEl) {
    const panel = document.createElement("div");
    panel.className = "easyuse-anima-aio-node-panel";
    node.__easyuseAnimaGeneratorPanelEl = panel;
    const widget = node.addDOMWidget?.(GENERATOR_DOM_WIDGET, "EasyUseAnimaGeneratorPanel", panel, {
      serialize: false,
      hideOnZoom: false,
      getMinHeight: () => generatorPanelMinHeight(node),
      getHeight: () => generatorPanelHeight(node),
    });
    if (widget) {
      node.__easyuseAnimaGeneratorPanelWidget = widget;
      widget.computeLayoutSize = () => ({
        minHeight: generatorPanelMinHeight(node),
        height: generatorPanelHeight(node),
        minWidth: GENERATOR_NODE_MIN_WIDTH - 18,
      });
    }
  }
  renderGeneratorPanel(node);
}

function field(section, label, control, tooltipKey = "") {
  const row = document.createElement("div");
  row.className = "easyuse-anima-aio-field";
  const labelEl = document.createElement("label");
  labelEl.textContent = label;
  const resolvedTooltipKey = tooltipKey || AIO_FIELD_TOOLTIP_KEYS[label] || "";
  const tooltipText = resolvedTooltipKey
    ? aioText(resolvedTooltipKey)
    : aioFormat("tip.fieldGeneric", { label });
  applyTooltipText(row, tooltipText);
  applyTooltipText(labelEl, tooltipText);
  applyTooltipText(control, tooltipText);
  row.append(labelEl, control);
  section.append(row);
  return control;
}

function createDialog(title, subtitle) {
  ensureStyle();
  const backdrop = document.createElement("div");
  backdrop.className = "easyuse-anima-aio-backdrop";
  const dialog = document.createElement("div");
  dialog.className = "easyuse-anima-aio-dialog";
  const header = document.createElement("header");
  const titleBox = document.createElement("div");
  const heading = document.createElement("h2");
  heading.textContent = title;
  const desc = document.createElement("p");
  desc.textContent = subtitle;
  titleBox.append(heading, desc);
  const close = document.createElement("button");
  close.className = "easyuse-anima-aio-close";
  close.textContent = aioText("button.close");
  header.append(titleBox, close);
  const body = document.createElement("div");
  body.className = "easyuse-anima-aio-body";
  const actions = document.createElement("div");
  actions.className = "easyuse-anima-aio-actions";
  dialog.append(header, body, actions);
  backdrop.append(dialog);
  close.addEventListener("click", () => backdrop.remove());
  backdrop.addEventListener("pointerdown", (event) => {
    if (event.target === backdrop) {
      backdrop.remove();
    }
  });
  document.body.append(backdrop);
  return { backdrop, body, actions };
}

function openInputSettings(node) {
  const widget = findWidget(node, INPUT_SETTINGS_WIDGET);
  const settings = parseSettings(widget, DEFAULT_INPUT_SETTINGS);
  const { backdrop, body, actions } = createDialog(
    "Easy Use Anima Input Settings",
    "Advanced resource options are saved internally with the workflow."
  );
  const section = document.createElement("section");
  section.className = "easyuse-anima-aio-section full";
  section.append(Object.assign(document.createElement("h3"), { textContent: "Loader Options" }));
  const weightDtype = field(
    section,
    "UNET weight dtype",
    selectInput(["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"], settings.resources.unet_weight_dtype)
  );
  const clipDevice = field(
    section,
    "CLIP device",
    selectInput(["default", "cpu"], settings.resources.clip_device)
  );
  const loaderMode = document.createElement("p");
  loaderMode.textContent = "Loader mode: split diffusion model + VAE + CLIP";
  section.append(loaderMode);
  body.append(section);

  const cancel = document.createElement("button");
  cancel.textContent = aioText("button.cancel");
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = aioText("button.apply");
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_INPUT_SETTINGS, settings);
    next.resources.loader_mode = "split";
    next.resources.clip_loader = "single";
    next.resources.unet_weight_dtype = weightDtype.value || "default";
    next.resources.clip_device = clipDevice.value || "default";
    writeSettings(node, widget, next);
    backdrop.remove();
  });
}

function openSamplerSettings(node) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  const settings = mergeVisibleGeneratorSettings(node, parseSettings(widget, DEFAULT_GENERATION_SETTINGS));
  const { backdrop, body, actions } = createDialog(
    "Sampler Details",
    "Choose one of three sampler paths. Missing optional node packs are locked before queue execution."
  );

  const makeSection = (title, className = "easyuse-anima-aio-section full") => {
    const section = document.createElement("section");
    section.className = className;
    section.append(Object.assign(document.createElement("h3"), { textContent: title }));
    return section;
  };
  const makeSubsection = (title) => {
    const section = document.createElement("div");
    section.className = "easyuse-anima-aio-subsection";
    section.append(Object.assign(document.createElement("h4"), { textContent: title }));
    return section;
  };

  const base = makeSection("Base Parameters");
  const seed = field(base, "Seed", numberInput(settings.sampler.seed));
  const seedControl = field(
    base,
    "Seed mode",
    selectInput(GENERATOR_SEED_CONTROLS, normalizeSeedControl(settings.sampler.seed_after_generate))
  );
  const steps = field(base, "Steps", numberInput(settings.sampler.steps));
  steps.min = "1";
  steps.max = "75";
  const cfg = field(base, "CFG", numberInput(settings.sampler.cfg, "0.1"));
  cfg.min = "1";
  cfg.max = "10";
  const denoise = field(base, "Denoise", numberInput(settings.sampler.denoise, "0.01"));

  const sampler = makeSection("Sampler Backend");
  const backendValues = [
    "comfy_ksampler",
    "spectrum_mod_guidance_advanced",
    "spectrum_spd_speed",
  ];
  const backend = field(
    sampler,
    "Mode",
    selectInput(backendValues, settings.sampler.backend || "comfy_ksampler")
  );
  const dependencyWarning = document.createElement("div");
  dependencyWarning.className = "easyuse-anima-aio-warning";
  dependencyWarning.hidden = true;
  sampler.append(dependencyWarning);
  const samplerName = field(
    sampler,
    "Sampler",
    selectInput(widgetOptions(node, "sampler_name", GENERATOR_FALLBACK_SAMPLER_NAMES), settings.sampler.sampler_name)
  );
  const scheduler = field(
    sampler,
    "Scheduler",
    selectInput(widgetOptions(node, "scheduler", GENERATOR_FALLBACK_SCHEDULER_NAMES), settings.sampler.scheduler)
  );

  const modGuidance = makeSubsection("Mod Guidance");
  const modMode = field(
    modGuidance,
    "Mode",
    selectInput(["prompt_data", "enabled", "disabled"], settings.mod_guidance.mode),
    "tip.modMode",
  );
  const modProfile = field(
    modGuidance,
    "Profile",
    selectInput(["off", "step_i8_skip27", "step_i14", "uniform_w3"], settings.mod_guidance.profile)
  );
  const modAdvanced = document.createElement("div");
  modGuidance.append(modAdvanced);
  const modAdapter = field(modAdvanced, "Adapter", textInput(settings.mod_guidance.advanced.adapter));
  const modW = field(modAdvanced, "Mod W", numberInput(settings.mod_guidance.advanced.mod_w, "0.1"));
  const modStart = field(modAdvanced, "Start layer", numberInput(settings.mod_guidance.advanced.mod_start_layer));
  const modEnd = field(modAdvanced, "End layer", numberInput(settings.mod_guidance.advanced.mod_end_layer));
  const modTaper = field(modAdvanced, "Taper", numberInput(settings.mod_guidance.advanced.mod_taper));
  const modTaperScale = field(modAdvanced, "Taper scale", numberInput(settings.mod_guidance.advanced.mod_taper_scale, "0.05"));
  const modFinalW = field(modAdvanced, "Final W", numberInput(settings.mod_guidance.advanced.mod_final_w, "0.1"));
  sampler.append(modGuidance);

  const backendDetails = document.createElement("div");
  const spectrum = makeSubsection("Spectrum Patch / Advanced Sampler");
  const spectrumPatchEnabled = field(spectrum, "Use Spectrum patch", checkbox(settings.sampler.spectrum.enabled));
  const windowSize = field(spectrum, "Window size", numberInput(settings.sampler.spectrum.window_size, "0.25"));
  const flexWindow = field(spectrum, "Flex window", numberInput(settings.sampler.spectrum.flex_window, "0.05"));
  const warmupSteps = field(spectrum, "Warmup steps", numberInput(settings.sampler.spectrum.warmup_steps));
  const tailSteps = field(spectrum, "Tail actual", numberInput(settings.sampler.spectrum.tail_actual_steps));
  const blendW = field(spectrum, "Blend W", numberInput(settings.sampler.spectrum.blend_w, "0.05"));
  const chebyDegree = field(spectrum, "Cheby degree", numberInput(settings.sampler.spectrum.cheby_degree));
  const ridgeLambda = field(spectrum, "Ridge lambda", numberInput(settings.sampler.spectrum.ridge_lambda, "0.01"));
  const spectrumCompat = field(
    spectrum,
    "Compat policy",
    selectInput(["conservative", "legacy", "strict"], settings.sampler.spectrum.compat_policy || "conservative")
  );

  const corrections = makeSubsection("Spectrum Advanced Corrections");
  const correctionsEnabled = field(corrections, "Use corrections", checkbox(settings.sampler.dit_corrections.enabled));
  const dcwMode = field(corrections, "DCW mode", selectInput(["off", "manual", "auto"], settings.sampler.dit_corrections.dcw_mode));
  const dcwLambda = field(corrections, "DCW lambda", numberInput(settings.sampler.dit_corrections.dcw_lambda, "0.001"));
  const dcwBand = field(corrections, "DCW band", selectInput(["LL", "all", "HH", "LH+HL+HH"], settings.sampler.dit_corrections.dcw_band_mask));
  const smcCfg = field(corrections, "SMC-CFG", checkbox(settings.sampler.dit_corrections.smc_cfg));
  const smcAlpha = field(corrections, "SMC alpha", numberInput(settings.sampler.dit_corrections.adaptive_smc_alpha, "0.01"));
  const smcLambda = field(corrections, "SMC lambda", numberInput(settings.sampler.dit_corrections.smc_cfg_lambda, "0.1"));
  const cfgpp = field(corrections, "CFG++", checkbox(settings.sampler.dit_corrections.cfgpp));
  const cfgppLambda = field(corrections, "CFG++ lambda", numberInput(settings.sampler.dit_corrections.cfgpp_lambda, "0.1"));
  const fsg = field(corrections, "FSG", checkbox(settings.sampler.dit_corrections.fsg));
  spectrum.append(corrections);

  const spd = makeSubsection("Spectrum + SPD / SPEED");
  const spdScale = field(spd, "Scale", numberInput(settings.sampler.spd.scale, "0.05"));
  const spdSigma = field(spd, "Sigma", numberInput(settings.sampler.spd.sigma, "0.01"));
  const spdSmc = field(spd, "SMC alpha", numberInput(settings.sampler.spd.adaptive_smc_alpha, "0.01"));
  backendDetails.append(spectrum, spd);
  sampler.append(backendDetails);
  body.append(base, sampler);

  const refreshBackendDetails = () => {
    const isComfy = backend.value === "comfy_ksampler";
    const isSpectrumAdvanced = backend.value === "spectrum_mod_guidance_advanced";
    spectrum.classList.toggle("hidden", !(isComfy || isSpectrumAdvanced));
    spectrumPatchEnabled.parentElement.style.display = isComfy ? "" : "none";
    spectrumCompat.parentElement.style.display = isComfy ? "" : "none";
    modAdvanced.style.display = isSpectrumAdvanced ? "" : "none";
    spd.classList.toggle("hidden", backend.value !== "spectrum_spd_speed");
  };
  const refreshDependencyLocks = () => {
    const messages = [];
    for (const option of Array.from(backend.options)) {
      const dependencyKey = GENERATOR_BACKEND_DEPENDENCIES[option.value];
      const pack = optionalDependencyPack(dependencyKey);
      const missing = !!dependencyKey && !optionalDependencyAvailable(dependencyKey);
      option.disabled = missing;
      option.textContent = missing ? `${option.value} (${pack} missing)` : option.value;
      if (missing && option.selected) {
        messages.push(aioFormat("warning.optionalDependencyMissing", {
          backend: option.value,
          pack,
        }));
        backend.value = "comfy_ksampler";
      }
    }
    const spectrumPatchMissing = !optionalDependencyAvailable("spectrumPatch");
    spectrumPatchEnabled.disabled = spectrumPatchMissing;
    correctionsEnabled.disabled = spectrumPatchMissing;
    if (spectrumPatchMissing && (spectrumPatchEnabled.checked || correctionsEnabled.checked)) {
      messages.push(aioFormat("warning.optionalDependencyMissing", {
        backend: "Spectrum Patch",
        pack: optionalDependencyPack("spectrumPatch"),
      }));
      spectrumPatchEnabled.checked = false;
      correctionsEnabled.checked = false;
    }
    dependencyWarning.hidden = messages.length === 0;
    dependencyWarning.textContent = messages.join(" ");
    refreshBackendDetails();
  };
  backend.addEventListener("change", refreshBackendDetails);
  refreshBackendDetails();
  refreshDependencyLocks();
  loadGeneratorOptionalDependencies().then(refreshDependencyLocks);

  const cancel = document.createElement("button");
  cancel.textContent = aioText("button.cancel");
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = aioText("button.apply");
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    delete next.sampler.dave;
    next.sampler.backend = backend.value || "comfy_ksampler";
    next.sampler.seed = normalizeSeedValue(seed.value, GENERATOR_SPECIAL_SEED_RANDOM);
    next.sampler.seed_after_generate = normalizeSeedControl(seedControl.value);
    next.sampler.steps = Math.trunc(clampGeneratorNumber(steps.value, DEFAULT_GENERATION_SETTINGS.sampler.steps, 1, 75));
    next.sampler.cfg = clampGeneratorNumber(cfg.value, DEFAULT_GENERATION_SETTINGS.sampler.cfg, 1, 10);
    next.sampler.denoise = clampGeneratorNumber(denoise.value, DEFAULT_GENERATION_SETTINGS.sampler.denoise, 0, 1);
    next.sampler.sampler_name = samplerName.value || DEFAULT_GENERATION_SETTINGS.sampler.sampler_name;
    next.sampler.scheduler = scheduler.value || DEFAULT_GENERATION_SETTINGS.sampler.scheduler;
    next.sampler.spectrum.enabled = (
      next.sampler.backend === "spectrum_mod_guidance_advanced"
      || (next.sampler.backend === "comfy_ksampler" && spectrumPatchEnabled.checked && !spectrumPatchEnabled.disabled)
    );
    next.sampler.spectrum.window_size = Number(windowSize.value || 2);
    next.sampler.spectrum.flex_window = Number(flexWindow.value || 0.25);
    next.sampler.spectrum.warmup_steps = Number(warmupSteps.value || 6);
    next.sampler.spectrum.tail_actual_steps = Number(tailSteps.value || 3);
    next.sampler.spectrum.blend_w = Number(blendW.value || 0.3);
    next.sampler.spectrum.cheby_degree = Number(chebyDegree.value || 3);
    next.sampler.spectrum.ridge_lambda = Number(ridgeLambda.value || 0.1);
    next.sampler.spectrum.compat_policy = spectrumCompat.value || "conservative";
    next.sampler.spd.scale = Number(spdScale.value || 0.5);
    next.sampler.spd.sigma = Number(spdSigma.value || 0.7);
    next.sampler.spd.adaptive_smc_alpha = Number(spdSmc.value || 0);
    next.sampler.dit_corrections.enabled = correctionsEnabled.checked && !correctionsEnabled.disabled;
    next.sampler.dit_corrections.dcw_mode = dcwMode.value || "off";
    next.sampler.dit_corrections.dcw_lambda = Number(dcwLambda.value || 0.01);
    next.sampler.dit_corrections.dcw_band_mask = dcwBand.value || "LL";
    next.sampler.dit_corrections.smc_cfg = smcCfg.checked;
    next.sampler.dit_corrections.adaptive_smc_alpha = Number(smcAlpha.value || 0);
    next.sampler.dit_corrections.smc_cfg_lambda = Number(smcLambda.value || 6);
    next.sampler.dit_corrections.cfgpp = cfgpp.checked;
    next.sampler.dit_corrections.cfgpp_lambda = Number(cfgppLambda.value || 0);
    next.sampler.dit_corrections.fsg = fsg.checked;
    next.mod_guidance.mode = modMode.value || "prompt_data";
    next.mod_guidance.profile = modProfile.value || "step_i8_skip27";
    next.mod_guidance.advanced.adapter = modAdapter.value || "(auto-download default)";
    next.mod_guidance.advanced.mod_w = Number(modW.value || 3);
    next.mod_guidance.advanced.mod_start_layer = Number(modStart.value || 8);
    next.mod_guidance.advanced.mod_end_layer = Number(modEnd.value || 27);
    next.mod_guidance.advanced.mod_taper = Number(modTaper.value || 0);
    next.mod_guidance.advanced.mod_taper_scale = Number(modTaperScale.value || 0.25);
    next.mod_guidance.advanced.mod_final_w = Number(modFinalW.value || 0);
    applyVisibleGeneratorSettings(node, next);
    writeSettings(node, widget, next);
    renderGeneratorPanel(node);
    backdrop.remove();
  });
}

function createStageOptimizationEditor(title, values, defaults) {
  const section = document.createElement("section");
  section.className = "easyuse-anima-aio-section";
  section.append(Object.assign(document.createElement("h3"), { textContent: title }));
  const spectrumValues = mergeDefaults(defaults.spectrum || {}, values.spectrum || {});
  const correctionValues = mergeDefaults(defaults.dit_corrections || {}, values.dit_corrections || {});

  const spectrumEnabled = field(section, "Spectrum patch", checkbox(spectrumValues.enabled));
  const windowSize = field(section, "Window size", numberInput(spectrumValues.window_size, "0.25"));
  const flexWindow = field(section, "Flex window", numberInput(spectrumValues.flex_window, "0.05"));
  const warmupSteps = field(section, "Warmup", numberInput(spectrumValues.warmup_steps, "1"));
  const tailSteps = field(section, "Tail actual", numberInput(spectrumValues.tail_actual_steps, "1"));
  const blendW = field(section, "Blend W", numberInput(spectrumValues.blend_w, "0.05"));
  const chebyDegree = field(section, "Cheby", numberInput(spectrumValues.cheby_degree, "1"));
  const ridgeLambda = field(section, "Ridge lambda", numberInput(spectrumValues.ridge_lambda, "0.01"));
  const compatPolicy = field(
    section,
    "Compat",
    selectInput(["conservative", "legacy", "strict"], spectrumValues.compat_policy || "conservative")
  );

  const corrections = document.createElement("div");
  corrections.className = "easyuse-anima-aio-subsection";
  corrections.append(Object.assign(document.createElement("h4"), { textContent: "Spectrum DCW / Corrections" }));
  const correctionsEnabled = field(corrections, "Use corrections", checkbox(correctionValues.enabled));
  const dcwMode = field(corrections, "DCW mode", selectInput(["off", "manual", "auto"], correctionValues.dcw_mode || "off"));
  const dcwLambda = field(corrections, "DCW lambda", numberInput(correctionValues.dcw_lambda, "0.001"));
  const dcwBand = field(corrections, "DCW band", selectInput(["LL", "all", "HH", "LH+HL+HH"], correctionValues.dcw_band_mask || "LL"));
  const smcCfg = field(corrections, "SMC-CFG", checkbox(correctionValues.smc_cfg));
  const smcAlpha = field(corrections, "SMC alpha", numberInput(correctionValues.adaptive_smc_alpha, "0.01"));
  const smcLambda = field(corrections, "SMC lambda", numberInput(correctionValues.smc_cfg_lambda, "0.1"));
  const cfgpp = field(corrections, "CFG++", checkbox(correctionValues.cfgpp));
  const cfgppLambda = field(corrections, "CFG++ lambda", numberInput(correctionValues.cfgpp_lambda, "0.1"));
  const fsg = field(corrections, "FSG", checkbox(correctionValues.fsg));
  section.append(corrections);
  const dependencyWarning = document.createElement("div");
  dependencyWarning.className = "easyuse-anima-aio-warning";
  dependencyWarning.hidden = true;
  section.append(dependencyWarning);
  const refreshDependencyLocks = () => {
    const spectrumPatchMissing = !optionalDependencyAvailable("spectrumPatch");
    spectrumEnabled.disabled = spectrumPatchMissing;
    correctionsEnabled.disabled = spectrumPatchMissing;
    if (spectrumPatchMissing) {
      spectrumEnabled.checked = false;
      correctionsEnabled.checked = false;
      dependencyWarning.hidden = false;
      dependencyWarning.textContent = aioFormat("warning.optionalDependencyMissing", {
        backend: title,
        pack: optionalDependencyPack("spectrumPatch"),
      });
    } else {
      dependencyWarning.hidden = true;
      dependencyWarning.textContent = "";
    }
  };
  refreshDependencyLocks();
  loadGeneratorOptionalDependencies().then(refreshDependencyLocks);

  return {
    section,
    values() {
      return {
        spectrum: {
          enabled: spectrumEnabled.checked && !spectrumEnabled.disabled,
          window_size: Number(windowSize.value || defaults.spectrum.window_size || 2),
          flex_window: Number(flexWindow.value || defaults.spectrum.flex_window || 0.25),
          warmup_steps: Number(warmupSteps.value || defaults.spectrum.warmup_steps || 6),
          tail_actual_steps: Number(tailSteps.value || defaults.spectrum.tail_actual_steps || 3),
          blend_w: Number(blendW.value || defaults.spectrum.blend_w || 0.3),
          cheby_degree: Number(chebyDegree.value || defaults.spectrum.cheby_degree || 3),
          ridge_lambda: Number(ridgeLambda.value || defaults.spectrum.ridge_lambda || 0.1),
          history_size: Number(spectrumValues.history_size || defaults.spectrum.history_size || 100),
          one_sampler_only: !!spectrumValues.one_sampler_only,
          verbose: !!spectrumValues.verbose,
          compat_policy: compatPolicy.value || "conservative",
        },
        dit_corrections: {
          enabled: correctionsEnabled.checked && !correctionsEnabled.disabled,
          dcw_mode: dcwMode.value || "off",
          dcw_lambda: Number(dcwLambda.value || defaults.dit_corrections.dcw_lambda || 0.01),
          dcw_band_mask: dcwBand.value || "LL",
          dcw_calibrator: correctionValues.dcw_calibrator || "(auto-download default)",
          smc_cfg: smcCfg.checked,
          adaptive_smc_alpha: Number(smcAlpha.value || defaults.dit_corrections.adaptive_smc_alpha || 0),
          smc_cfg_lambda: Number(smcLambda.value || defaults.dit_corrections.smc_cfg_lambda || 6),
          cfgpp: cfgpp.checked,
          cfgpp_lambda: Number(cfgppLambda.value || defaults.dit_corrections.cfgpp_lambda || 0),
          fsg: fsg.checked,
          fsg_band_lo: Number(correctionValues.fsg_band_lo || defaults.dit_corrections.fsg_band_lo || 0.59),
          fsg_band_hi: Number(correctionValues.fsg_band_hi || defaults.dit_corrections.fsg_band_hi || 0.75),
          fsg_k: Number(correctionValues.fsg_k || defaults.dit_corrections.fsg_k || 3),
          fsg_d_sigma: Number(correctionValues.fsg_d_sigma || defaults.dit_corrections.fsg_d_sigma || 0.1),
          fsg_gamma: Number(correctionValues.fsg_gamma || defaults.dit_corrections.fsg_gamma || 0),
          replace_existing_cfg: !!correctionValues.replace_existing_cfg,
        },
      };
    },
  };
}

function openHighresSettings(node) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  const settings = generatorSettings(node);
  const highres = mergeDefaults(DEFAULT_GENERATION_SETTINGS.highres, settings.highres || {});
  const { backdrop, body, actions } = createDialog(
    "Highres Settings",
    "Image scaling, highres resampling, and Spectrum optimization are saved with the node."
  );
  body.classList.add("easyuse-anima-aio-one-column");

  const image = document.createElement("section");
  image.className = "easyuse-anima-aio-section";
  image.append(Object.assign(document.createElement("h3"), { textContent: "Image Scale" }));
  const enabled = field(image, "Enable highres", checkbox(highres.enabled));
  const scaleBy = field(image, "Scale by", numberInput(highres.scale_by, "0.01"));
  const upscaleMethod = field(image, "Method", selectInput(["bicubic", "nearest-exact", "bilinear", "area", "lanczos"], highres.upscale_method));
  const multiple = field(image, "Multiple", selectInput(["8", "16", "32", "64"], highres.multiple));
  const maxLongEdge = field(image, "Max long edge", numberInput(highres.max_long_edge, "32"));

  const sampler = document.createElement("section");
  sampler.className = "easyuse-anima-aio-section";
  sampler.append(Object.assign(document.createElement("h3"), { textContent: "Highres Sampler" }));
  const steps = field(sampler, "Steps", numberInput(highres.steps, "1"));
  steps.min = "1";
  steps.max = "75";
  const inheritSampler = field(
    sampler,
    "Follow main sampler",
    checkbox(highres.inherit_sampler_settings),
    "tip.highresFollow",
  );
  const cfg = field(sampler, "CFG", numberInput(highres.cfg, "0.1"));
  cfg.min = "1";
  cfg.max = "10";
  const samplerName = field(
    sampler,
    "Sampler",
    selectInput(widgetOptions(node, "sampler_name", GENERATOR_FALLBACK_SAMPLER_NAMES), highres.sampler_name)
  );
  const scheduler = field(
    sampler,
    "Scheduler",
    selectInput(widgetOptions(node, "scheduler", GENERATOR_FALLBACK_SCHEDULER_NAMES), highres.scheduler)
  );
  const denoise = field(sampler, "Denoise", numberInput(highres.denoise, "0.01"));
  const updateInheritedRows = () => {
    const display = inheritSampler.checked ? "none" : "grid";
    for (const control of [cfg, samplerName, scheduler]) {
      if (control?.parentElement) {
        control.parentElement.style.display = display;
      }
    }
  };
  inheritSampler.addEventListener("change", updateInheritedRows);
  updateInheritedRows();
  const optimization = createStageOptimizationEditor(
    "Highres Optimization",
    highres,
    DEFAULT_GENERATION_SETTINGS.highres,
  );
  body.append(image, sampler, optimization.section);

  const cancel = document.createElement("button");
  cancel.textContent = aioText("button.cancel");
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = aioText("button.apply");
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    const optimized = optimization.values();
    next.highres = {
      ...next.highres,
      enabled: enabled.checked,
      scale_by: clampGeneratorNumber(scaleBy.value, DEFAULT_GENERATION_SETTINGS.highres.scale_by, 0.01, 8),
      upscale_method: upscaleMethod.value || "bicubic",
      multiple: multiple.value || "32",
      max_long_edge: Math.trunc(clampGeneratorNumber(maxLongEdge.value, 2560, 0, 16384)),
      steps: Math.trunc(clampGeneratorNumber(steps.value, 20, 1, 75)),
      inherit_sampler_settings: inheritSampler.checked,
      cfg: clampGeneratorNumber(cfg.value, 8, 1, 10),
      sampler_name: samplerName.value || "euler",
      scheduler: scheduler.value || "simple",
      denoise: clampGeneratorNumber(denoise.value, DEFAULT_GENERATION_SETTINGS.highres.denoise, 0, 1),
      ...optimized,
    };
    writeSettings(node, widget, next);
    renderGeneratorPanel(node);
    backdrop.remove();
  });
}

function createDetailerTargetEditor(node, title, values, defaults, onLabelChange = null) {
  const target = mergeDefaults(defaults, values || {});
  const section = document.createElement("section");
  section.className = "easyuse-anima-aio-detailer-target-panel";
  const header = document.createElement("div");
  header.className = "easyuse-anima-aio-node-stage-mini-header";
  header.append(Object.assign(document.createElement("h3"), { textContent: title }));
  section.append(header);
  const labelInput = field(
    section,
    "Block name",
    textInput(target.label || defaults.label || title),
    "tip.detailerName",
  );
  labelInput.addEventListener("input", () => onLabelChange?.());
  const enabled = field(section, "Enable", checkbox(target.enabled));

  const detect = document.createElement("div");
  detect.className = "easyuse-anima-aio-subsection";
  detect.append(Object.assign(document.createElement("h4"), { textContent: "SAM3 Detect" }));
  const detectPrompt = field(detect, "Prompt", textInput(target.detect_prompt));
  const detectCount = field(detect, "Count", numberInput(target.detect_count, "1"));
  const threshold = field(detect, "Threshold", numberInput(target.threshold, "0.01"));
  const refine = field(detect, "Refine", numberInput(target.refine_iterations, "1"));
  const individual = field(detect, "Individual", checkbox(target.individual_masks));
  const combined = field(detect, "Combined", checkbox(target.combined));
  section.append(detect);

  const segs = document.createElement("div");
  segs.className = "easyuse-anima-aio-subsection";
  segs.append(Object.assign(document.createElement("h4"), { textContent: "MaskToSEGS" }));
  const cropFactor = field(segs, "Crop factor", numberInput(target.crop_factor, "0.1"));
  const bboxFill = field(segs, "BBox fill", checkbox(target.bbox_fill));
  const dropSize = field(segs, "Drop size", numberInput(target.drop_size, "1"));
  const contourFill = field(segs, "Contour fill", checkbox(target.contour_fill));
  section.append(segs);

  const detail = document.createElement("div");
  detail.className = "easyuse-anima-aio-subsection";
  detail.append(Object.assign(document.createElement("h4"), { textContent: "Impact Detailer" }));
  const guideSize = field(detail, "Guide size", numberInput(target.guide_size, "8"));
  const maxSize = field(detail, "Max size", numberInput(target.max_size, "8"));
  const steps = field(detail, "Steps", numberInput(target.steps, "1"));
  steps.min = "1";
  steps.max = "75";
  const inheritSampler = field(
    detail,
    "Follow main sampler",
    checkbox(target.inherit_sampler_settings),
    "tip.detailerFollow",
  );
  const cfg = field(detail, "CFG", numberInput(target.cfg, "0.1"));
  cfg.min = "1";
  cfg.max = "10";
  const samplerName = field(detail, "Sampler", selectInput(widgetOptions(node, "sampler_name", GENERATOR_FALLBACK_SAMPLER_NAMES), target.sampler_name));
  const scheduler = field(detail, "Scheduler", selectInput(widgetOptions(node, "scheduler", GENERATOR_FALLBACK_SCHEDULER_NAMES), target.scheduler));
  const denoise = field(detail, "Denoise", numberInput(target.denoise, "0.01"));
  const feather = field(detail, "Feather", numberInput(target.feather, "1"));
  const noiseMask = field(detail, "Noise mask", checkbox(target.noise_mask));
  const forceInpaint = field(detail, "Force inpaint", checkbox(target.force_inpaint));
  const noiseMaskFeather = field(detail, "Mask feather", numberInput(target.noise_mask_feather, "1"));
  const cycle = field(detail, "Cycle", numberInput(target.cycle, "1"));
  const alignment = field(detail, "Alignment", selectInput(["impact", "none", "32", "64"], target.alignment || "32"));
  const updateInheritedRows = () => {
    const display = inheritSampler.checked ? "none" : "grid";
    for (const control of [cfg, samplerName, scheduler]) {
      if (control?.parentElement) {
        control.parentElement.style.display = display;
      }
    }
  };
  inheritSampler.addEventListener("change", updateInheritedRows);
  updateInheritedRows();
  section.append(detail);

  const optimization = createStageOptimizationEditor(`${title} Optimization`, target, defaults);
  section.append(optimization.section);

  return {
    section,
    label() {
      return String(labelInput.value || defaults.label || title).trim() || title;
    },
    values() {
      const optimized = optimization.values();
      return {
        ...target,
        label: String(labelInput.value || defaults.label || title).trim() || title,
        enabled: enabled.checked,
        detect_prompt: detectPrompt.value || defaults.detect_prompt,
        detect_count: Number(detectCount.value || defaults.detect_count),
        threshold: Number(threshold.value || defaults.threshold),
        refine_iterations: Number(refine.value || defaults.refine_iterations),
        individual_masks: individual.checked,
        combined: combined.checked,
        crop_factor: Number(cropFactor.value || defaults.crop_factor),
        bbox_fill: bboxFill.checked,
        drop_size: Number(dropSize.value || defaults.drop_size),
        contour_fill: contourFill.checked,
        guide_size: Number(guideSize.value || defaults.guide_size),
        guide_size_for: false,
        max_size: Number(maxSize.value || defaults.max_size),
        steps: Math.trunc(clampGeneratorNumber(steps.value, defaults.steps, 1, 75)),
        inherit_sampler_settings: inheritSampler.checked,
        cfg: clampGeneratorNumber(cfg.value, defaults.cfg, 1, 10),
        sampler_name: samplerName.value || defaults.sampler_name,
        scheduler: scheduler.value || defaults.scheduler,
        denoise: clampGeneratorNumber(denoise.value, defaults.denoise, 0, 1),
        feather: Number(feather.value || defaults.feather),
        noise_mask: noiseMask.checked,
        force_inpaint: forceInpaint.checked,
        wildcard: target.wildcard || "",
        cycle: Number(cycle.value || defaults.cycle),
        alignment: alignment.value || "32",
        inpaint_model: false,
        noise_mask_feather: Number(noiseMaskFeather.value || defaults.noise_mask_feather || 0),
        tiled_encode: false,
        tiled_decode: false,
        ...optimized,
      };
    },
  };
}

function openDetailerSettings(node) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  const settings = generatorSettings(node);
  const detailer = mergeDefaults(DEFAULT_GENERATION_SETTINGS.detailer, settings.detailer || {});
  const { backdrop, body, actions } = createDialog(
    "Detailer Settings",
    "SAM3 detection and Impact detailer settings are saved with the node."
  );
  body.classList.add("easyuse-anima-aio-one-column");
  const main = document.createElement("section");
  main.className = "easyuse-anima-aio-section full";
  main.append(Object.assign(document.createElement("h3"), { textContent: "Detailer" }));
  const enabled = field(main, "Enable detailer", checkbox(detailer.enabled));
  const checkpoint = field(main, "SAM3 checkpoint", textInput(detailer.sam3.checkpoint));
  const dependencyWarning = document.createElement("div");
  dependencyWarning.className = "easyuse-anima-aio-warning";
  dependencyWarning.hidden = true;
  main.append(dependencyWarning);
  body.append(main);

  const currentOrder = normalizeDetailerOrder(detailer.order);
  let activeTargetName = currentOrder[0] || "face";
  const tabsSection = document.createElement("section");
  tabsSection.className = "easyuse-anima-aio-section full";
  tabsSection.append(Object.assign(document.createElement("h3"), { textContent: "Detailer Blocks" }));
  const tabBar = document.createElement("div");
  tabBar.className = "easyuse-anima-aio-tabs";
  const tabPanel = document.createElement("div");
  tabPanel.className = "easyuse-anima-aio-tab-panel";
  tabsSection.append(tabBar, tabPanel);
  body.append(tabsSection);

  let editors = {};
  const moveTarget = (targetName, delta) => {
    const index = currentOrder.indexOf(targetName);
    const nextIndex = index + delta;
    if (index < 0 || nextIndex < 0 || nextIndex >= currentOrder.length) {
      return;
    }
    [currentOrder[index], currentOrder[nextIndex]] = [currentOrder[nextIndex], currentOrder[index]];
    renderDetailerTabs();
  };
  const selectTarget = (targetName) => {
    activeTargetName = targetName;
    renderDetailerTabs();
  };
  function renderDetailerTabs() {
    tabBar.replaceChildren();
    for (const [index, targetName] of currentOrder.entries()) {
      const editor = editors[targetName];
      if (!editor) {
        continue;
      }
      const tab = document.createElement("div");
      tab.className = "easyuse-anima-aio-tab";
      tab.classList.toggle("active", targetName === activeTargetName);
      tab.tabIndex = 0;
      tab.setAttribute("role", "button");
      tab.setAttribute("aria-selected", targetName === activeTargetName ? "true" : "false");
      applyTooltip(tab, "tip.detailerBlock");
      const label = document.createElement("span");
      label.className = "easyuse-anima-aio-tab-label";
      label.textContent = editor.label();
      const tools = document.createElement("span");
      tools.className = "easyuse-anima-aio-tab-tools";
      const moveLeft = document.createElement("button");
      moveLeft.type = "button";
      moveLeft.textContent = "<";
      moveLeft.disabled = index === 0;
      applyTooltip(moveLeft, "tip.detailerOrder");
      const moveRight = document.createElement("button");
      moveRight.type = "button";
      moveRight.textContent = ">";
      moveRight.disabled = index === currentOrder.length - 1;
      applyTooltip(moveRight, "tip.detailerOrder");
      moveLeft.addEventListener("click", (event) => {
        event.stopPropagation();
        moveTarget(targetName, -1);
      });
      moveRight.addEventListener("click", (event) => {
        event.stopPropagation();
        moveTarget(targetName, 1);
      });
      tools.append(moveLeft, moveRight);
      tab.append(label, tools);
      tab.addEventListener("click", () => selectTarget(targetName));
      tab.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectTarget(targetName);
        }
      });
      tabBar.append(tab);
    }
    if (!editors[activeTargetName]) {
      activeTargetName = currentOrder[0] || "face";
    }
    tabPanel.replaceChildren(editors[activeTargetName]?.section || document.createElement("div"));
  }
  const face = createDetailerTargetEditor(
    node,
    "Face Detailer",
    detailer.face,
    DEFAULT_GENERATION_SETTINGS.detailer.face,
    renderDetailerTabs,
  );
  const eye = createDetailerTargetEditor(
    node,
    "Eye Detailer",
    detailer.eye,
    DEFAULT_GENERATION_SETTINGS.detailer.eye,
    renderDetailerTabs,
  );
  editors = { face, eye };
  renderDetailerTabs();
  const refreshDetailerDependencyLocks = () => {
    const missingPacks = [];
    if (!optionalDependencyAvailable("impactDetailer")) {
      missingPacks.push(optionalDependencyPack("impactDetailer"));
    }
    if (!optionalDependencyAvailable("impactMaskToSegs")) {
      missingPacks.push(optionalDependencyPack("impactMaskToSegs"));
    }
    const missing = missingPacks.length > 0;
    enabled.disabled = missing;
    if (missing && enabled.checked) {
      enabled.checked = false;
    }
    dependencyWarning.hidden = !missing;
    dependencyWarning.textContent = missing
      ? aioFormat("warning.optionalDependencyMissing", {
          backend: "Detailer",
          pack: [...new Set(missingPacks)].join(", "),
        })
      : "";
  };
  refreshDetailerDependencyLocks();
  loadGeneratorOptionalDependencies().then(refreshDetailerDependencyLocks);

  const cancel = document.createElement("button");
  cancel.textContent = aioText("button.cancel");
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = aioText("button.apply");
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    const detailerEnabled = enabled.checked && !enabled.disabled;
    const faceValues = face.values();
    const eyeValues = eye.values();
    if (!detailerEnabled) {
      faceValues.enabled = false;
      eyeValues.enabled = false;
    }
    next.detailer = {
      ...next.detailer,
      enabled: detailerEnabled,
      sam3: {
        context: "load_checkpoint",
        checkpoint: checkpoint.value || "sam3.1_multiplex_fp16.safetensors",
      },
      order: normalizeDetailerOrder(currentOrder),
      face: faceValues,
      eye: eyeValues,
    };
    writeSettings(node, widget, next);
    renderGeneratorPanel(node);
    backdrop.remove();
  });
}

function normalizeImageSaverHashBundles(value) {
  if (typeof value === "string") {
    try {
      return normalizeImageSaverHashBundles(JSON.parse(value || "[]"));
    } catch {
      return value.trim() ? [value.trim()] : [];
    }
  }
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => String(item ?? "").trim().replace(/^[,\s]+|[,\s]+$/g, ""))
    .filter(Boolean);
}

function normalizeImageSaverCivitaiHashFetchers(value) {
  if (typeof value === "string") {
    try {
      return normalizeImageSaverCivitaiHashFetchers(JSON.parse(value || "[]"));
    } catch {
      return [];
    }
  }
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item) => item && typeof item === "object" && !Array.isArray(item))
    .map((item) => ({
      enabled: asBool(item.enabled, true),
      username: String(item.username || "").trim(),
      model_name: String(item.model_name || "").trim(),
      version: String(item.version || "").trim(),
    }))
    .filter((item) => item.username || item.model_name || item.version);
}

function createImageSaverHashBundleEditor(initialBundles) {
  const wrapper = document.createElement("div");
  const list = document.createElement("div");
  list.className = "easyuse-anima-aio-hash-bundle-list";
  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.className = "easyuse-anima-aio-add-row";
  addButton.textContent = "+ Add Hash Fetcher Bundle";

  const addRow = (value = "") => {
    const row = document.createElement("div");
    row.className = "easyuse-anima-aio-hash-bundle-row";
    const textarea = textareaInput(value);
    textarea.placeholder = "Name:HASH, HASH:Weight, Name:HASH:Weight";
    applyTooltip(textarea, "tip.hashBundles");
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = aioText("button.remove");
    applyTooltip(remove, "tip.hashBundles");
    remove.addEventListener("click", () => {
      row.remove();
    });
    row.append(textarea, remove);
    list.append(row);
  };

  const bundles = normalizeImageSaverHashBundles(initialBundles);
  if (bundles.length) {
    for (const bundle of bundles) {
      addRow(bundle);
    }
  } else {
    addRow();
  }
  addButton.addEventListener("click", () => addRow());
  wrapper.append(list, addButton);

  return {
    element: wrapper,
    values() {
      return [...list.querySelectorAll("textarea")]
        .map((textarea) => String(textarea.value || "").trim().replace(/^[,\s]+|[,\s]+$/g, ""))
        .filter(Boolean);
    },
  };
}

function createImageSaverCivitaiHashFetcherEditor(initialFetchers) {
  const wrapper = document.createElement("div");
  const list = document.createElement("div");
  list.className = "easyuse-anima-aio-civitai-fetcher-list";
  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.className = "easyuse-anima-aio-add-row";
  addButton.textContent = aioText("button.addCivitaiFetcher");
  applyTooltip(addButton, "tip.civitaiHashFetchers");

  const miniField = (label, control, tooltipKey) => {
    const item = document.createElement("div");
    item.className = "easyuse-anima-aio-mini-field";
    const labelEl = document.createElement("label");
    labelEl.textContent = label;
    const tooltip = aioText(tooltipKey);
    applyTooltipText(item, tooltip);
    applyTooltipText(labelEl, tooltip);
    applyTooltipText(control, tooltip);
    item.append(labelEl, control);
    return item;
  };

  const addRow = (value = {}) => {
    const row = document.createElement("div");
    row.className = "easyuse-anima-aio-civitai-fetcher-row";
    applyTooltip(row, "tip.civitaiHashFetchers");

    const header = document.createElement("div");
    header.className = "easyuse-anima-aio-civitai-fetcher-head";
    const enabledLabel = document.createElement("label");
    enabledLabel.className = "easyuse-anima-aio-civitai-fetcher-enabled";
    const enabled = checkbox(value.enabled !== false);
    enabledLabel.append(enabled, document.createTextNode(aioText("label.enabled")));
    applyTooltip(enabledLabel, "tip.civitaiHashFetchers");
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = aioText("button.remove");
    applyTooltip(remove, "tip.civitaiHashFetchers");
    remove.addEventListener("click", () => row.remove());
    header.append(enabledLabel, remove);

    const grid = document.createElement("div");
    grid.className = "easyuse-anima-aio-civitai-fetcher-grid";
    const username = textInput(value.username || "");
    const modelName = textInput(value.model_name || "");
    const version = textInput(value.version || "");
    username.placeholder = "N0VA39";
    modelName.placeholder = "Anima All in One workflow";
    version.placeholder = "";
    grid.append(
      miniField("Username", username, "tip.civitaiUsername"),
      miniField("Model name", modelName, "tip.civitaiModelName"),
      miniField("Version", version, "tip.civitaiVersion"),
    );

    const preview = document.createElement("div");
    preview.className = "easyuse-anima-aio-civitai-fetcher-preview";
    applyTooltip(preview, "tip.civitaiHashFetchers");
    const updatePreview = () => {
      const name = String(modelName.value || "").trim() || "model_name";
      preview.textContent = aioFormat("text.civitaiHashPreview", { model: name });
    };
    modelName.addEventListener("input", updatePreview);
    updatePreview();

    row.append(header, grid, preview);
    list.append(row);
  };

  const fetchers = normalizeImageSaverCivitaiHashFetchers(initialFetchers);
  if (fetchers.length) {
    for (const fetcher of fetchers) {
      addRow(fetcher);
    }
  } else {
    addRow();
  }
  addButton.addEventListener("click", () => addRow());
  wrapper.append(list, addButton);

  return {
    element: wrapper,
    values() {
      return [...list.querySelectorAll(".easyuse-anima-aio-civitai-fetcher-row")]
        .map((row) => {
          const inputs = row.querySelectorAll("input");
          const enabled = inputs[0]?.checked !== false;
          const username = String(inputs[1]?.value || "").trim();
          const modelName = String(inputs[2]?.value || "").trim();
          const version = String(inputs[3]?.value || "").trim();
          return {
            enabled,
            username,
            model_name: modelName,
            version,
          };
        })
        .filter((item) => item.username || item.model_name || item.version);
    },
  };
}

function openPreviewSettings(node) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  const settings = generatorSettings(node);
  const preview = mergeDefaults(DEFAULT_GENERATION_SETTINGS.preview, settings.preview || {});
  const { backdrop, body, actions } = createDialog(
    "Preview Options",
    aioText("text.previewOptionsSubtitle"),
  );
  const section = document.createElement("section");
  section.className = "easyuse-anima-aio-section full";
  section.append(Object.assign(document.createElement("h3"), { textContent: "Node Preview" }));
  const intermediate = field(
    section,
    "Intermediate images",
    checkbox(preview.intermediate_images),
    "tip.previewIntermediate",
  );
  const comparePrevious = field(
    section,
    "Compare previous",
    checkbox(preview.compare_previous),
    "tip.previewComparePrevious",
  );
  const imageFeed = field(
    section,
    "Image feed",
    checkbox(preview.image_feed),
    "tip.previewImageFeed",
  );
  const feedCount = field(
    section,
    "Feed count",
    numberInput(preview.feed_count, "1"),
    "tip.previewFeedCount",
  );
  feedCount.min = "1";
  feedCount.max = "100";
  const syncFeedCount = () => {
    feedCount.disabled = !imageFeed.checked;
  };
  imageFeed.addEventListener("change", syncFeedCount);
  syncFeedCount();
  body.append(section);

  const cancel = document.createElement("button");
  cancel.textContent = aioText("button.cancel");
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = aioText("button.apply");
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    next.preview = {
      intermediate_images: intermediate.checked,
      compare_previous: comparePrevious.checked,
      image_feed: imageFeed.checked,
      feed_count: Math.trunc(clampGeneratorNumber(feedCount.value, preview.feed_count, 1, 100)),
    };
    if (Array.isArray(node.__easyuseAnimaGeneratorPreviewFeedImages)) {
      node.__easyuseAnimaGeneratorPreviewFeedImages = node.__easyuseAnimaGeneratorPreviewFeedImages.slice(
        -next.preview.feed_count,
      );
    }
    node.__easyuseAnimaGeneratorPreviewImages = next.preview.image_feed
      ? (node.__easyuseAnimaGeneratorPreviewFeedImages || [])
      : (node.__easyuseAnimaGeneratorCurrentRunImages || []);
    node.__easyuseAnimaSelectedPreviewIndex = generatorDefaultPreviewIndex(node.__easyuseAnimaGeneratorPreviewImages);
    applyVisibleGeneratorSettings(node, next);
    writeSettings(node, widget, next);
    renderGeneratorPanel(node);
    backdrop.remove();
  });
}

function openSaveSettings(node) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  const settings = generatorSettings(node);
  const imageSaver = mergeDefaults(
    DEFAULT_GENERATION_SETTINGS.save.image_saver,
    settings.save.image_saver,
  );
  const { backdrop, body, actions } = createDialog(
    "Save Options",
    "Image Saver requires ComfyUI-Image-Saver. Missing node packs are reported during queue execution."
  );
  body.classList.add("easyuse-anima-aio-save-body");
  const main = document.createElement("section");
  main.className = "easyuse-anima-aio-section full";
  main.append(Object.assign(document.createElement("h3"), { textContent: "Save Backend" }));
  const save = field(main, "Save image", checkbox(settings.save.enabled));
  const backend = field(
    main,
    "Backend",
    selectInput(["image_saver", "comfy_save_image"], settings.save.backend || "image_saver"),
  );
  const dependencyWarning = document.createElement("div");
  dependencyWarning.className = "easyuse-anima-aio-warning";
  dependencyWarning.hidden = true;
  main.append(dependencyWarning);
  const refreshSaveDependencyLocks = () => {
    const imageSaverMissing = !optionalDependencyAvailable("imageSaver");
    for (const option of Array.from(backend.options)) {
      if (option.value === "image_saver") {
        option.disabled = imageSaverMissing;
        option.textContent = imageSaverMissing
          ? `image_saver (${optionalDependencyPack("imageSaver")} missing)`
          : "image_saver";
      }
    }
    if (imageSaverMissing && backend.value === "image_saver") {
      backend.value = "comfy_save_image";
      dependencyWarning.hidden = false;
      dependencyWarning.textContent = aioFormat("warning.optionalDependencyMissing", {
        backend: "image_saver",
        pack: optionalDependencyPack("imageSaver"),
      });
    } else {
      dependencyWarning.hidden = true;
      dependencyWarning.textContent = "";
    }
  };

  const files = document.createElement("section");
  files.className = "easyuse-anima-aio-section full";
  files.append(Object.assign(document.createElement("h3"), { textContent: "Image Saver Files" }));
  const filename = field(files, "Filename", textInput(imageSaver.filename));
  const path = field(files, "Path", textInput(imageSaver.path));
  const extension = field(files, "Extension", selectInput(["webp", "png", "jpeg", "jpg"], imageSaver.extension));
  const quality = field(files, "JPEG/WebP quality", numberInput(imageSaver.quality_jpeg_or_webp, "1"));
  const losslessWebp = field(files, "Lossless WebP", checkbox(imageSaver.lossless_webp));
  const optimizePng = field(files, "Optimize PNG", checkbox(imageSaver.optimize_png));
  const counter = field(files, "Counter", numberInput(imageSaver.counter, "1"));

  const metadata = document.createElement("section");
  metadata.className = "easyuse-anima-aio-section full";
  metadata.append(Object.assign(document.createElement("h3"), { textContent: "Image Saver Metadata" }));
  const timeFormat = field(metadata, "Time format", textInput(imageSaver.time_format));
  const clipSkip = field(metadata, "Clip skip", numberInput(imageSaver.clip_skip, "1"));
  const embedWorkflow = field(metadata, "Embed workflow", checkbox(imageSaver.embed_workflow));
  const saveWorkflowJson = field(metadata, "Workflow JSON", checkbox(imageSaver.save_workflow_as_json));
  const additionalHashes = field(metadata, "Additional hashes", textInput(imageSaver.additional_hashes), "tip.additionalHashes");
  const hashBundles = createImageSaverHashBundleEditor(imageSaver.additional_hash_bundles);
  field(metadata, "Manual hash bundles", hashBundles.element, "tip.hashBundles");
  const civitaiHashFetchers = createImageSaverCivitaiHashFetcherEditor(imageSaver.civitai_hash_fetchers);
  field(metadata, "Civitai Hash Fetchers", civitaiHashFetchers.element, "tip.civitaiHashFetchers");
  const civitai = field(metadata, "Civitai data", checkbox(imageSaver.download_civitai_data));
  const easyRemix = field(metadata, "Easy remix", checkbox(imageSaver.easy_remix));
  const custom = field(metadata, "Custom metadata", textareaInput(imageSaver.custom));
  body.append(main, files, metadata);
  refreshSaveDependencyLocks();
  loadGeneratorOptionalDependencies().then(refreshSaveDependencyLocks);

  const cancel = document.createElement("button");
  cancel.textContent = aioText("button.cancel");
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = aioText("button.apply");
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    next.save.enabled = save.checked;
    next.save.backend = backend.value || "image_saver";
    next.save.image_saver = {
      filename: filename.value || "%time_%basemodelname",
      path: path.value || "EasyUseAnima/AiO",
      extension: extension.value || "webp",
      lossless_webp: losslessWebp.checked,
      quality_jpeg_or_webp: Number(quality.value || 97),
      optimize_png: optimizePng.checked,
      counter: Number(counter.value || 0),
      clip_skip: Number(clipSkip.value || 0),
      time_format: timeFormat.value || "%Y-%m-%d-%H%M%S",
      save_workflow_as_json: saveWorkflowJson.checked,
      embed_workflow: embedWorkflow.checked,
      additional_hashes: additionalHashes.value || "",
      additional_hash_bundles: hashBundles.values(),
      civitai_hash_fetchers: civitaiHashFetchers.values(),
      download_civitai_data: civitai.checked,
      easy_remix: easyRemix.checked,
      custom: custom.value || "",
    };
    applyVisibleGeneratorSettings(node, next);
    writeSettings(node, widget, next);
    renderGeneratorPanel(node);
    backdrop.remove();
  });
}

function openAdvancedSettings(node) {
  const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  const settings = generatorSettings(node);
  const { backdrop, body, actions } = createDialog(
    "Advanced Options",
    "Advanced generation options stay in a popup and are serialized as versioned settings."
  );

  const makeSubsection = (title) => {
    const section = document.createElement("div");
    section.className = "easyuse-anima-aio-subsection";
    section.append(Object.assign(document.createElement("h4"), { textContent: title }));
    return section;
  };

  const modelPatches = document.createElement("section");
  modelPatches.className = "easyuse-anima-aio-section full";
  modelPatches.append(Object.assign(document.createElement("h3"), { textContent: "Model Patch / Optimization" }));

  const auraShift = field(
    modelPatches,
    "AuraFlow shift",
    numberInput(settings.model_patches.aura_flow.shift, "0.5"),
    "tip.shift",
  );
  auraShift.min = "1";
  auraShift.max = "10";

  const dave = makeSubsection("Anima DAVE");
  const daveEnabled = field(dave, "Use DAVE", checkbox(settings.model_patches.dave.enabled), "tip.daveEnabled");
  const daveMask = field(dave, "Mask", textInput(settings.model_patches.dave.mask || "dave_alpha.npz"), "tip.daveMask");
  const daveStrength = field(dave, "DAVE strength", numberInput(settings.model_patches.dave.strength ?? 0.30, "0.01"), "tip.daveStrength");
  const daveTau = field(dave, "DAVE tau", numberInput(settings.model_patches.dave.tau ?? 0.10, "0.01"), "tip.daveTau");
  daveStrength.min = "0";
  daveTau.min = "0";
  daveTau.max = "1";

  const kj = makeSubsection("KJNodes Optimization");
  const fp16Accum = field(kj, "KJNodes FP16 accum", checkbox(settings.model_patches.kj.fp16_accumulation), "tip.kjFp16Accum");

  const sage = makeSubsection("SageAttention (KJNodes)");
  const sageAttention = field(
    sage,
    "Mode",
    selectInput([
      "disabled",
      "auto",
      "sageattn",
      "sageattn_qk_int8_pv_fp16_cuda",
      "sageattn_qk_int8_pv_fp8_cuda",
    ], settings.model_patches.kj.sage_attention),
    "tip.kjSageMode",
  );
  const sageAllowCompile = field(sage, "Allow compile", checkbox(settings.model_patches.kj.sage_allow_compile), "tip.kjSageCompile");
  kj.append(sage);

  const torch = makeSubsection("Torch Compile (KJNodes)");
  const torchCompileEnabled = field(
    torch,
    "Use Torch compile",
    checkbox(settings.model_patches.kj.torch_compile.enabled),
    "tip.torchCompileEnabled",
  );
  const torchDetails = document.createElement("div");
  torchDetails.className = "easyuse-anima-aio-subsection";
  torchDetails.append(Object.assign(document.createElement("h4"), { textContent: "Torch Compile Parameters" }));
  const torchCompileBackend = field(torchDetails, "Backend", textInput(settings.model_patches.kj.torch_compile.backend), "tip.torchCompileBackend");
  const torchCompileFullgraph = field(torchDetails, "Fullgraph", checkbox(settings.model_patches.kj.torch_compile.fullgraph), "tip.torchCompileFullgraph");
  const torchCompileMode = field(
    torchDetails,
    "Mode",
    selectInput([
      "default",
      "reduce-overhead",
      "max-autotune",
      "max-autotune-no-cudagraphs",
    ], settings.model_patches.kj.torch_compile.mode),
    "tip.torchCompileMode",
  );
  const torchCompileDynamic = field(
    torchDetails,
    "Dynamic",
    selectInput(["false", "true", "default"], settings.model_patches.kj.torch_compile.dynamic),
    "tip.torchCompileDynamic",
  );
  const torchCompileBlocksOnly = field(
    torchDetails,
    "Transformer blocks only",
    checkbox(settings.model_patches.kj.torch_compile.compile_transformer_blocks_only),
    "tip.torchCompileBlocks",
  );
  const torchCompileCache = field(
    torchDetails,
    "Dynamo cache limit",
    numberInput(settings.model_patches.kj.torch_compile.dynamo_cache_size_limit, "1"),
    "tip.torchCompileCache",
  );
  const torchCompileDebug = field(
    torchDetails,
    "Debug keys",
    checkbox(settings.model_patches.kj.torch_compile.debug_compile_keys),
    "tip.torchCompileDebug",
  );
  const torchCompileDisableVram = field(
    torchDetails,
    "Disable dynamic VRAM",
    checkbox(settings.model_patches.kj.torch_compile.disable_dynamic_vram),
    "tip.torchCompileVram",
  );
  torch.append(torchDetails);
  kj.append(torch);

  const modelWarning = document.createElement("div");
  modelWarning.className = "easyuse-anima-aio-warning";
  modelWarning.hidden = true;
  modelPatches.append(dave, kj, modelWarning);
  body.append(modelPatches);

  const artistMix = document.createElement("section");
  artistMix.className = "easyuse-anima-aio-section full";
  artistMix.append(Object.assign(document.createElement("h3"), { textContent: "Artist Mix" }));
  const artistMode = field(
    artistMix,
    "Mode",
    selectInput([
      "prompt_data",
      "off",
      "prompt",
      "average",
      "delta_rms",
      "hybrid",
      "clustered",
      "exact",
      "composite_exact",
      "late_exact",
      "average_late_exact",
      "scheduled_average",
    ], settings.artist_mix.mode),
    "tip.artistMixMode",
  );
  const artistStart = field(artistMix, "Start", numberInput(settings.artist_mix.start_percent, "0.01"));
  const artistStrength = field(artistMix, "Strength", numberInput(settings.artist_mix.strength_scale, "0.01"));
  body.append(artistMix);

  const refreshSageDetails = () => {
    sageAllowCompile.parentElement.style.display = sageAttention.value === "disabled" ? "none" : "grid";
  };
  const refreshTorchDetails = () => {
    torchDetails.style.display = torchCompileEnabled.checked ? "" : "none";
  };
  const setControlsDisabled = (controls, disabled) => {
    for (const control of controls) {
      if (control) {
        control.disabled = disabled;
      }
    }
  };
  const refreshAdvancedDependencyLocks = () => {
    const messages = [];

    const daveMissing = !optionalDependencyAvailable("dave");
    setControlsDisabled([daveEnabled, daveMask, daveStrength, daveTau], daveMissing);
    if (daveMissing && daveEnabled.checked) {
      daveEnabled.checked = false;
    }
    if (daveMissing) {
      messages.push(aioFormat("warning.optionalDependencyMissing", {
        backend: "Anima DAVE",
        pack: optionalDependencyPack("dave"),
      }));
    }

    const kjFp16Missing = !optionalDependencyAvailable("kjFp16");
    fp16Accum.disabled = kjFp16Missing;
    if (kjFp16Missing && fp16Accum.checked) {
      fp16Accum.checked = false;
    }
    if (kjFp16Missing) {
      messages.push(aioFormat("warning.optionalDependencyMissing", {
        backend: "KJNodes FP16 accum",
        pack: optionalDependencyPack("kjFp16"),
      }));
    }

    const kjSageMissing = !optionalDependencyAvailable("kjSage");
    setControlsDisabled([sageAttention, sageAllowCompile], kjSageMissing);
    if (kjSageMissing && sageAttention.value !== "disabled") {
      sageAttention.value = "disabled";
      sageAllowCompile.checked = false;
    }
    if (kjSageMissing) {
      messages.push(aioFormat("warning.optionalDependencyMissing", {
        backend: "SageAttention",
        pack: optionalDependencyPack("kjSage"),
      }));
    }

    const kjCompileMissing = !optionalDependencyAvailable("kjTorchCompile");
    setControlsDisabled([
      torchCompileEnabled,
      torchCompileBackend,
      torchCompileFullgraph,
      torchCompileMode,
      torchCompileDynamic,
      torchCompileBlocksOnly,
      torchCompileCache,
      torchCompileDebug,
      torchCompileDisableVram,
    ], kjCompileMissing);
    if (kjCompileMissing && torchCompileEnabled.checked) {
      torchCompileEnabled.checked = false;
    }
    if (kjCompileMissing) {
      messages.push(aioFormat("warning.optionalDependencyMissing", {
        backend: "Torch Compile",
        pack: optionalDependencyPack("kjTorchCompile"),
      }));
    }

    modelWarning.hidden = messages.length === 0;
    modelWarning.textContent = messages.join(" ");
    refreshSageDetails();
    refreshTorchDetails();
  };
  sageAttention.addEventListener("change", refreshSageDetails);
  torchCompileEnabled.addEventListener("change", refreshTorchDetails);
  refreshSageDetails();
  refreshTorchDetails();
  refreshAdvancedDependencyLocks();
  loadGeneratorOptionalDependencies().then(refreshAdvancedDependencyLocks);

  const cancel = document.createElement("button");
  cancel.textContent = aioText("button.cancel");
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = aioText("button.apply");
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    delete next.sampler.dave;
    delete next.model_patches.aura_flow.enabled;
    next.model_patches.aura_flow.shift = clampGeneratorNumber(
      auraShift.value,
      DEFAULT_GENERATION_SETTINGS.model_patches.aura_flow.shift,
      1,
      10,
    );
    next.model_patches.dave.enabled = daveEnabled.checked && !daveEnabled.disabled;
    next.model_patches.dave.mask = daveMask.value || "dave_alpha.npz";
    next.model_patches.dave.strength = Number(daveStrength.value || 0.30);
    next.model_patches.dave.tau = Number(daveTau.value || 0.10);
    next.model_patches.kj.fp16_accumulation = fp16Accum.checked && !fp16Accum.disabled;
    next.model_patches.kj.sage_attention = sageAttention.disabled ? "disabled" : (sageAttention.value || "disabled");
    next.model_patches.kj.sage_allow_compile = sageAllowCompile.checked && !sageAttention.disabled;
    next.model_patches.kj.torch_compile.enabled = torchCompileEnabled.checked && !torchCompileEnabled.disabled;
    next.model_patches.kj.torch_compile.backend = torchCompileBackend.value || "inductor";
    next.model_patches.kj.torch_compile.fullgraph = torchCompileFullgraph.checked;
    next.model_patches.kj.torch_compile.mode = torchCompileMode.value || "max-autotune-no-cudagraphs";
    next.model_patches.kj.torch_compile.dynamic = torchCompileDynamic.value || "false";
    next.model_patches.kj.torch_compile.compile_transformer_blocks_only = torchCompileBlocksOnly.checked;
    next.model_patches.kj.torch_compile.dynamo_cache_size_limit = Number(torchCompileCache.value || 64);
    next.model_patches.kj.torch_compile.debug_compile_keys = torchCompileDebug.checked;
    next.model_patches.kj.torch_compile.disable_dynamic_vram = torchCompileDisableVram.checked;
    next.artist_mix.mode = artistMode.value || "prompt_data";
    next.artist_mix.start_percent = Number(artistStart.value || 0.5);
    next.artist_mix.strength_scale = Number(artistStrength.value || 1.0);
    writeSettings(node, widget, next);
    renderGeneratorPanel(node);
    backdrop.remove();
  });
}

function openGeneratorSettings(node) {
  openAdvancedSettings(node);
}

function isGeneratorGraphNode(node) {
  return node?.type === GENERATOR_NODE_TYPE || node?.comfyClass === GENERATOR_NODE_TYPE;
}

function generatorGraphNodes() {
  if (Array.isArray(app.graph?._nodes)) {
    return app.graph._nodes.filter(isGeneratorGraphNode);
  }
  return Object.values(app.graph?._nodes_by_id || {}).filter(isGeneratorGraphNode);
}

function findWorkflowNode(workflow, id) {
  const nodes = workflow?.nodes;
  if (!Array.isArray(nodes)) {
    return null;
  }
  return nodes.find((workflowNode) => String(workflowNode?.id) === String(id)) || null;
}

function resolveGeneratorSeedForQueue(node, inputSeed) {
  const seed = normalizeSeedValue(inputSeed, GENERATOR_SPECIAL_SEED_RANDOM);
  if (!isSpecialSeed(seed)) {
    return seed;
  }
  const lastSeed = Number(node.__easyuseAnimaLastQueuedSeed);
  if (Number.isFinite(lastSeed) && !isSpecialSeed(lastSeed)) {
    if (seed === GENERATOR_SPECIAL_SEED_INCREMENT) {
      return Math.min(GENERATOR_MAX_SEED, lastSeed + 1);
    }
    if (seed === GENERATOR_SPECIAL_SEED_DECREMENT) {
      return Math.max(0, lastSeed - 1);
    }
  }
  return randomSeed();
}

function prepareGeneratorPromptForQueue(prompt) {
  const output = prompt?.output;
  if (!output || typeof output !== "object") {
    return;
  }
  for (const node of generatorGraphNodes()) {
    if (node.mode === 4 || node.mode === globalThis.LiteGraph?.NEVER) {
      continue;
    }
    const outputNode = output[String(node.id)];
    const outputInputs = outputNode?.inputs;
    if (!outputInputs) {
      continue;
    }
    syncGeneratorStateFromDom(node);
    const settings = sanitizeGeneratorSettingsForOptionalDependencies(generatorSettings(node));
    const inputSeed = normalizeSeedValue(settings.sampler.seed, GENERATOR_SPECIAL_SEED_RANDOM);
    const seedToUse = resolveGeneratorSeedForQueue(node, inputSeed);
    settings.sampler.seed = seedToUse;
    outputInputs.generation_settings = settingsToCompactJson(settings);

    const workflowNode = findWorkflowNode(prompt.workflow, node.id);
    setWorkflowWidgetValue(node, workflowNode, GENERATOR_SETTINGS_WIDGET, outputInputs.generation_settings);
    const settingsWidget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
    if (settingsWidget) {
      writeSettings(node, settingsWidget, settings, false);
    }

    node.__easyuseAnimaLastQueuedSeed = seedToUse;
    refreshGeneratorSeedButtons(node);
  }
}

function installGeneratorQueuePromptHook() {
  if (!api?.queuePrompt || api.queuePrompt.__easyuseAnimaAioWrapped) {
    return;
  }
  const queuePrompt = api.queuePrompt;
  api.queuePrompt = async function (number, prompt, ...args) {
    await loadGeneratorOptionalDependencies();
    prepareGeneratorPromptForQueue(prompt);
    return queuePrompt.call(this, number, prompt, ...args);
  };
  api.queuePrompt.__easyuseAnimaAioWrapped = true;
}

function ensureButton(node, key, label, callback) {
  if (node.widgets?.some((widget) => widget.__easyuseAnimaAioButtonKey === key)) {
    return;
  }
  const widget = node.addWidget?.("button", label, null, callback, { serialize: false });
  if (widget) {
    widget.__easyuseAnimaAioButtonKey = key;
    widget.serialize = false;
  }
}

function hookInputNode(node) {
  node.serialize_widgets = true;
  hideWidget(findWidget(node, INPUT_SETTINGS_WIDGET));
  ensureButton(node, "easyuse_anima_input_settings", "Settings...", () => openInputSettings(node));
}

function hookGeneratorNode(node) {
  node.serialize_widgets = true;
  hideWidget(findWidget(node, GENERATOR_SETTINGS_WIDGET));
  ensureGeneratorPanel(node);
  syncGeneratorStateFromDom(node);
  suppressGeneratorDefaultPreview(node);
  loadGeneratorSamplerOptions().then(() => {
    if (node?.__easyuseAnimaGeneratorPanelEl) {
      renderGeneratorPanel(node);
    }
  });
}

function findGeneratorNodeByQualifiedId(rootGraph, nodeId) {
  if (!rootGraph || nodeId == null) {
    return null;
  }
  const textId = String(nodeId);
  if (!textId.includes(":")) {
    const numericId = Number(textId);
    return rootGraph.getNodeById?.(Number.isFinite(numericId) ? numericId : textId)
      || rootGraph.getNodeById?.(textId)
      || rootGraph._nodes_by_id?.[textId]
      || rootGraph._nodes_by_id?.[numericId]
      || null;
  }
  const parts = textId.split(":");
  let graph = rootGraph;
  for (let index = 0; index < parts.length - 1; index += 1) {
    const parentId = Number(parts[index]);
    if (!Number.isFinite(parentId)) {
      return null;
    }
    const parentNode = graph?.getNodeById?.(parentId) || graph?._nodes_by_id?.[parentId];
    if (!parentNode?.subgraph) {
      return null;
    }
    graph = parentNode.subgraph;
  }
  const leafId = Number(parts[parts.length - 1]);
  if (!Number.isFinite(leafId)) {
    return null;
  }
  return graph?.getNodeById?.(leafId) || graph?._nodes_by_id?.[leafId] || null;
}

function addGeneratorPreviewImagesToNode(node, nextImages, runId = "") {
  if (!node || !Array.isArray(nextImages) || !nextImages.length) {
    return;
  }
  const settings = generatorSettings(node);
  const currentImages = Array.isArray(node.__easyuseAnimaGeneratorCurrentRunImages)
    ? node.__easyuseAnimaGeneratorCurrentRunImages
    : [];
  const currentRunId = String(currentImages[0]?.__aio_run_id || "");
  const currentBase = runId && currentRunId && currentRunId !== runId ? [] : currentImages;
  const taggedNextImages = tagGeneratorPreviewRun(nextImages, runId, currentBase.length);
  node.__easyuseAnimaGeneratorCurrentRunImages = mergeGeneratorPreviewImages(currentBase, taggedNextImages, runId);
  if (settings.preview.image_feed) {
    node.__easyuseAnimaGeneratorPreviewFeedImages = appendGeneratorPreviewFeed(
      node.__easyuseAnimaGeneratorPreviewFeedImages,
      taggedNextImages,
      settings,
      runId,
    );
    node.__easyuseAnimaGeneratorPreviewImages = node.__easyuseAnimaGeneratorPreviewFeedImages;
  } else {
    node.__easyuseAnimaGeneratorPreviewImages = node.__easyuseAnimaGeneratorCurrentRunImages;
  }
  node.__easyuseAnimaSelectedPreviewIndex = generatorDefaultPreviewIndex(node.__easyuseAnimaGeneratorPreviewImages);
  updateGeneratorDomSummary(node);
  requestAnimationFrame(() => updateGeneratorDomSummary(node));
  scheduleGeneratorLayout(node);
  markNodeDirty(node);
}

function updateGeneratorExecutedStatus(node, message) {
  if (!node) {
    return;
  }
  const nextImages = generatorPreviewImages(message);
  const runId = generatorPreviewRunId(message);
  addGeneratorPreviewImagesToNode(node, nextImages, runId);
  node.__easyuseAnimaGeneratorStatus = {
    status: String(firstValue(message?.status, "generated") || "generated"),
    width: Number(firstValue(message?.width, 0)),
    height: Number(firstValue(message?.height, 0)),
    unet_name: String(firstValue(message?.unet_name, "")),
    sampler_backend: String(firstValue(message?.sampler_backend, "")),
  };
  updateGeneratorDomSummary(node);
}

function handleGeneratorPreviewEvent(event) {
  const detail = generatorPreviewEventDetail(event);
  const node = findGeneratorNodeByQualifiedId(app.graph, detail.node);
  if (!node || node.type !== GENERATOR_NODE_TYPE) {
    return;
  }
  const images = generatorPreviewImages({ easyuse_anima_preview: detail.images });
  addGeneratorPreviewImagesToNode(node, images, String(detail.run_id || ""));
}

function hookNode(node, nodeData) {
  if (nodeData.name === INPUT_NODE_TYPE) {
    hookInputNode(node);
  } else if (nodeData.name === GENERATOR_NODE_TYPE) {
    hookGeneratorNode(node);
  }
}

app.registerExtension({
  name: "easyuse-anima.aio",
  async setup() {
    installGeneratorQueuePromptHook();
    easyuseAnimaWatchLocale(refreshGeneratorPanels);
    api.addEventListener(GENERATOR_PREVIEW_EVENT, handleGeneratorPreviewEvent);
    loadGeneratorSamplerOptions().then(refreshGeneratorPanels);
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== INPUT_NODE_TYPE && nodeData.name !== GENERATOR_NODE_TYPE) {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = onNodeCreated?.apply(this, arguments);
      hookNode(this, nodeData);
      return result;
    };
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const result = onConfigure?.apply(this, arguments);
      setTimeout(() => hookNode(this, nodeData), 0);
      return result;
    };
    if (nodeData.name === GENERATOR_NODE_TYPE) {
      const onSerialize = nodeType.prototype.onSerialize;
      nodeType.prototype.onSerialize = function (serialized) {
        const result = onSerialize?.apply(this, arguments);
        syncGeneratorSerializedWidgets(this, serialized);
        return result;
      };
      nodeType.prototype.onExecuted = function (message) {
        suppressGeneratorDefaultPreview(this);
        updateGeneratorExecutedStatus(this, message);
        suppressGeneratorDefaultPreview(this);
        requestAnimationFrame(() => suppressGeneratorDefaultPreview(this));
        setTimeout(() => suppressGeneratorDefaultPreview(this), 0);
        return undefined;
      };
      const onResize = nodeType.prototype.onResize;
      nodeType.prototype.onResize = function () {
        const result = onResize?.apply(this, arguments);
        scheduleGeneratorLayout(this);
        return result;
      };
    }
  },
});
