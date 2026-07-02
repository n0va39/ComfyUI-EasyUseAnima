import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { easyuseAnimaText, easyuseAnimaWatchLocale } from "./easyuse_anima_i18n.js";

const INPUT_NODE_TYPE = "EasyUseAnimaInput";
const GENERATOR_NODE_TYPE = "EasyUseAnimaAIOGenerator";
const INPUT_SETTINGS_WIDGET = "input_settings";
const GENERATOR_SETTINGS_WIDGET = "generation_settings";
const GENERATOR_DOM_WIDGET = "easyuse_anima_generator_panel";
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
const GENERATOR_DEFAULT_DRAG_PIXELS = 8;
const GENERATOR_FALLBACK_SAMPLER_NAMES = [
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

const DEFAULT_GENERATION_SETTINGS = {
  schema: "easyuse_anima_aio_generation_settings",
  version: 1,
  mode: "txt2img",
  sampler: {
    backend: "comfy_ksampler",
    seed: GENERATOR_SPECIAL_SEED_RANDOM,
    seed_after_generate: "fixed",
    steps: 28,
    cfg: 5.0,
    sampler_name: "euler_ancestral",
    scheduler: "normal",
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
    scale_by: 1.25,
    upscale_method: "bicubic",
    multiple: "32",
    max_long_edge: 2560,
    steps: 20,
    inherit_sampler_settings: true,
    cfg: 8.0,
    sampler_name: "euler",
    scheduler: "simple",
    denoise: 0.31,
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
    "tip.shift": "AuraFlow model sampling shift. Always applied; range is 1.0 to 10.0.",
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
    "tip.samplerDetails": "Open sampler backend, model patch, Mod Guidance, and Spectrum options.",
    "tip.highresSettings": "Open all Highres scaling and optimization options.",
    "tip.detailerSettings": "Open all SAM3 and Impact Detailer options.",
    "tip.advancedOptions": "Open prompt-data driven advanced options.",
    "tip.saveOptions": "Open image saver and metadata options.",
    "tip.previewOptions": "Open node preview, comparison, and image feed options.",
    "tip.previewIntermediate": "Save temp previews for first pass, Highres, and Detailer stages.",
    "tip.previewComparePrevious": "When intermediate previews are enabled, compare the current preview with the previous queued result.",
    "tip.previewImageFeed": "Show the current run's preview images as a compact feed at the bottom of the preview panel.",
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
    "tip.shift": "AuraFlow 모델 샘플링 시프트입니다. 항상 적용되며 범위는 1.0부터 10.0까지입니다.",
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
    "tip.samplerDetails": "샘플러 백엔드, 모델 패치, Mod Guidance, Spectrum 옵션을 엽니다.",
    "tip.highresSettings": "Highres 확대와 최적화 전체 옵션을 엽니다.",
    "tip.detailerSettings": "SAM3와 Impact Detailer 전체 옵션을 엽니다.",
    "tip.advancedOptions": "Prompt Data 기반 고급 옵션을 엽니다.",
    "tip.saveOptions": "이미지 저장과 메타데이터 옵션을 엽니다.",
    "tip.previewOptions": "노드 프리뷰, 비교, 이미지 피드 옵션을 엽니다.",
    "tip.previewIntermediate": "1차, Highres, Detailer 단계의 temp 미리보기를 저장합니다.",
    "tip.previewComparePrevious": "중간 이미지 미리보기가 켜져 있을 때 현재 프리뷰와 이전 큐 결과를 비교합니다.",
    "tip.previewImageFeed": "현재 실행의 프리뷰 이미지들을 프리뷰 패널 하단에 작은 피드로 표시합니다.",
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
    "tip.shift": "AuraFlow のモデルサンプリングシフトです。常に適用されます。",
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
    "tip.samplerDetails": "サンプラーバックエンド、モデルパッチ、Mod Guidance、Spectrum オプションを開きます。",
    "tip.highresSettings": "Highres の拡大と最適化オプションを開きます。",
    "tip.detailerSettings": "SAM3 と Impact Detailer の全オプションを開きます。",
    "tip.advancedOptions": "Prompt Data ベースの詳細オプションを開きます。",
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
    "tip.shift": "AuraFlow 模型采样 Shift。始终应用，范围为 1.0 到 10.0。",
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
    "tip.samplerDetails": "打开采样后端、模型补丁、Mod Guidance 和 Spectrum 选项。",
    "tip.highresSettings": "打开 Highres 放大和优化选项。",
    "tip.detailerSettings": "打开 SAM3 和 Impact Detailer 全部选项。",
    "tip.advancedOptions": "打开基于 Prompt Data 的高级选项。",
    "tip.saveOptions": "打开图像保存和元数据选项。",
    "tip.size": "此节点最近生成图像的尺寸。",
  },
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

const generatorUiSettings = {
  sliderDragPixels: GENERATOR_DEFAULT_DRAG_PIXELS,
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

function parseDragPixels(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return GENERATOR_DEFAULT_DRAG_PIXELS;
  }
  return Math.max(1, Math.min(100, Math.round(number)));
}

function applyGeneratorUiSettings(settings = {}) {
  generatorUiSettings.sliderDragPixels = parseDragPixels(settings?.["lora_preset.strength_drag_pixels"]);
}

async function loadGeneratorUiSettings() {
  if (window.__easyuseAnimaSettings) {
    applyGeneratorUiSettings(window.__easyuseAnimaSettings);
  }
  try {
    const response = await fetch("/easyuse_anima/settings");
    if (response.ok) {
      const settings = await response.json();
      const values = {
        ...(settings?.settings || {}),
        ...(settings?.values || {}),
        ...(settings || {}),
      };
      delete values.settings;
      delete values.values;
      window.__easyuseAnimaSettings ||= {};
      Object.assign(window.__easyuseAnimaSettings, values);
      applyGeneratorUiSettings(values);
    }
  } catch {
    // Keep built-in defaults when settings are unavailable.
  }
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
      clip-path: inset(0 calc(100% - var(--aio-compare-x, 50%)) 0 0);
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
  for (const optionValue of options) {
    const option = document.createElement("option");
    option.value = optionValue;
    option.textContent = optionValue;
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
  settings.preview.compare_previous = (
    asBool(settings.preview.compare_previous, DEFAULT_GENERATION_SETTINGS.preview.compare_previous)
    && settings.preview.intermediate_images
  );
  settings.preview.image_feed = asBool(
    settings.preview.image_feed,
    DEFAULT_GENERATION_SETTINGS.preview.image_feed,
  );
  if (settings.save?.image_saver) {
    delete settings.save.image_saver.show_preview;
  }
  return settings.preview;
}

function normalizeGeneratorInputValues(node, settings = DEFAULT_GENERATION_SETTINGS) {
  const merged = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
  return {
    seed: normalizeSeedValue(widgetValue(node, "seed", merged.sampler.seed)),
    steps: Math.trunc(clampGeneratorNumber(widgetValue(node, "steps", merged.sampler.steps), 28, 1, 75)),
    cfg: clampGeneratorNumber(widgetValue(node, "cfg", merged.sampler.cfg), 5.0, 1.0, 10.0),
    sampler_name: String(widgetValue(node, "sampler_name", merged.sampler.sampler_name) || merged.sampler.sampler_name),
    scheduler: String(widgetValue(node, "scheduler", merged.sampler.scheduler) || merged.sampler.scheduler),
    denoise: clampGeneratorNumber(widgetValue(node, "denoise", merged.sampler.denoise), 1.0, 0.0, 1.0),
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
    settings.preview.intermediate_images
    && settings.preview.compare_previous
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
  const round = (next) => {
    const factor = 10 ** decimals;
    return Math.round(clamp(next) * factor) / factor;
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

  input.addEventListener("input", () => commit(input.value));
  track.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    track.setPointerCapture?.(event.pointerId);
    const rect = track.getBoundingClientRect();
    const relative = rect.width > 0 ? (event.clientX - rect.left) / rect.width : 0;
    const clicked = round(min + Math.max(0, Math.min(1, relative)) * (max - min));
    commit(clicked);
    const startX = event.clientX;
    const startValue = Number(input.value || clicked);
    const dragPixels = Math.max(1, generatorUiSettings.sliderDragPixels);
    const move = (moveEvent) => {
      moveEvent.preventDefault();
      moveEvent.stopPropagation();
      const deltaSteps = Math.trunc((moveEvent.clientX - startX) / dragPixels);
      commit(startValue + deltaSteps * step);
    };
    const up = (upEvent) => {
      upEvent.stopPropagation();
      track.releasePointerCapture?.(event.pointerId);
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
  const saveIcon = makeIconButton("▣", () => openSaveSettings(node), "tip.saveOptions");
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
  const tooltipText = tooltipKey
    ? aioText(tooltipKey)
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
  close.textContent = "Close";
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
  cancel.textContent = "Cancel";
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = "Apply";
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
    "Choose one of three sampler paths. Missing custom node packs are reported at queue time."
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
  const auraShift = field(
    base,
    "AuraFlow shift",
    numberInput(settings.model_patches.aura_flow.shift ?? 3.0, "0.5")
  );
  auraShift.min = "1";
  auraShift.max = "10";
  const denoise = field(base, "Denoise", numberInput(settings.sampler.denoise, "0.01"));

  const modelPatches = makeSection("Model Patch / Optimization");
  const fp16Accum = field(modelPatches, "KJNodes FP16 accum", checkbox(settings.model_patches.kj.fp16_accumulation));
  const sage = makeSubsection("KJNodes: SageAttention");
  const sageAttention = field(
    sage,
    "Mode",
    selectInput([
      "disabled",
      "auto",
      "sageattn_qk_int8_pv_fp16_cuda",
      "sageattn_qk_int8_pv_fp16_triton",
      "sageattn_qk_int8_pv_fp8_cuda",
      "sageattn_qk_int8_pv_fp8_cuda++",
      "sageattn3",
      "sageattn3_per_block_mean",
    ], settings.model_patches.kj.sage_attention)
  );
  const sageAllowCompile = field(sage, "Allow compile", checkbox(settings.model_patches.kj.sage_allow_compile));
  modelPatches.append(sage);

  const torch = makeSubsection("KJNodes: Torch Compile");
  const torchCompileEnabled = field(torch, "Use Torch compile", checkbox(settings.model_patches.kj.torch_compile.enabled));
  const torchDetails = document.createElement("div");
  torch.append(torchDetails);
  const torchCompileBackend = field(
    torchDetails,
    "Backend",
    selectInput(["inductor", "cudagraphs"], settings.model_patches.kj.torch_compile.backend)
  );
  const torchCompileFullgraph = field(torchDetails, "Fullgraph", checkbox(settings.model_patches.kj.torch_compile.fullgraph));
  const torchCompileMode = field(
    torchDetails,
    "Mode",
    selectInput(["default", "max-autotune", "max-autotune-no-cudagraphs", "reduce-overhead"], settings.model_patches.kj.torch_compile.mode)
  );
  const torchCompileDynamic = field(
    torchDetails,
    "Dynamic",
    selectInput(["auto", "true", "false"], settings.model_patches.kj.torch_compile.dynamic)
  );
  const torchCompileBlocksOnly = field(
    torchDetails,
    "Transformer blocks only",
    checkbox(settings.model_patches.kj.torch_compile.compile_transformer_blocks_only)
  );
  const torchCompileCache = field(
    torchDetails,
    "Dynamo cache limit",
    numberInput(settings.model_patches.kj.torch_compile.dynamo_cache_size_limit, "1")
  );
  const torchCompileDebug = field(torchDetails, "Debug keys", checkbox(settings.model_patches.kj.torch_compile.debug_compile_keys));
  const torchCompileDisableVram = field(
    torchDetails,
    "Disable dynamic VRAM",
    checkbox(settings.model_patches.kj.torch_compile.disable_dynamic_vram)
  );
  modelPatches.append(torch);

  const sampler = makeSection("Sampler Backend");
  const backend = field(
    sampler,
    "Sampler path",
    selectInput([
      "comfy_ksampler",
      "spectrum_mod_guidance_advanced",
      "spectrum_spd_speed",
    ], settings.sampler.backend || "comfy_ksampler")
  );
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
    selectInput(["prompt_data", "enabled", "disabled"], settings.mod_guidance.mode)
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
  body.append(base, modelPatches, sampler);

  const refreshBackendDetails = () => {
    const isComfy = backend.value === "comfy_ksampler";
    const isSpectrumAdvanced = backend.value === "spectrum_mod_guidance_advanced";
    spectrum.classList.toggle("hidden", !(isComfy || isSpectrumAdvanced));
    spectrumPatchEnabled.parentElement.style.display = isComfy ? "" : "none";
    spectrumCompat.parentElement.style.display = isComfy ? "" : "none";
    modAdvanced.style.display = isSpectrumAdvanced ? "" : "none";
    spd.classList.toggle("hidden", backend.value !== "spectrum_spd_speed");
  };
  const refreshSageDetails = () => {
    sageAllowCompile.parentElement.style.display = sageAttention.value === "disabled" ? "none" : "";
  };
  const refreshTorchDetails = () => {
    torchDetails.style.display = torchCompileEnabled.checked ? "" : "none";
  };
  backend.addEventListener("change", refreshBackendDetails);
  sageAttention.addEventListener("change", refreshSageDetails);
  torchCompileEnabled.addEventListener("change", refreshTorchDetails);
  refreshBackendDetails();
  refreshSageDetails();
  refreshTorchDetails();

  const cancel = document.createElement("button");
  cancel.textContent = "Cancel";
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = "Apply";
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    next.sampler.backend = backend.value || "comfy_ksampler";
    next.sampler.seed = normalizeSeedValue(seed.value, GENERATOR_SPECIAL_SEED_RANDOM);
    next.sampler.seed_after_generate = normalizeSeedControl(seedControl.value);
    next.sampler.steps = Math.trunc(clampGeneratorNumber(steps.value, 28, 1, 75));
    next.sampler.cfg = clampGeneratorNumber(cfg.value, 5, 1, 10);
    next.sampler.denoise = Number(denoise.value || 1);
    next.sampler.sampler_name = samplerName.value || "euler_ancestral";
    next.sampler.scheduler = scheduler.value || "normal";
    next.sampler.spectrum.enabled = (
      next.sampler.backend === "spectrum_mod_guidance_advanced"
      || (next.sampler.backend === "comfy_ksampler" && spectrumPatchEnabled.checked)
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
    next.sampler.dit_corrections.enabled = correctionsEnabled.checked;
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
    delete next.model_patches.aura_flow.enabled;
    next.model_patches.aura_flow.shift = clampGeneratorNumber(auraShift.value, 3, 1, 10);
    next.model_patches.kj.fp16_accumulation = fp16Accum.checked;
    next.model_patches.kj.sage_attention = sageAttention.value || "disabled";
    next.model_patches.kj.sage_allow_compile = sageAllowCompile.checked;
    next.model_patches.kj.torch_compile.enabled = torchCompileEnabled.checked;
    next.model_patches.kj.torch_compile.backend = torchCompileBackend.value || "inductor";
    next.model_patches.kj.torch_compile.fullgraph = torchCompileFullgraph.checked;
    next.model_patches.kj.torch_compile.mode = torchCompileMode.value || "max-autotune-no-cudagraphs";
    next.model_patches.kj.torch_compile.dynamic = torchCompileDynamic.value || "false";
    next.model_patches.kj.torch_compile.compile_transformer_blocks_only = torchCompileBlocksOnly.checked;
    next.model_patches.kj.torch_compile.dynamo_cache_size_limit = Number(torchCompileCache.value || 64);
    next.model_patches.kj.torch_compile.debug_compile_keys = torchCompileDebug.checked;
    next.model_patches.kj.torch_compile.disable_dynamic_vram = torchCompileDisableVram.checked;
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

  return {
    section,
    values() {
      return {
        spectrum: {
          enabled: spectrumEnabled.checked,
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
          enabled: correctionsEnabled.checked,
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
  cancel.textContent = "Cancel";
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = "Apply";
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    const optimized = optimization.values();
    next.highres = {
      ...next.highres,
      enabled: enabled.checked,
      scale_by: clampGeneratorNumber(scaleBy.value, 1.25, 0.01, 8),
      upscale_method: upscaleMethod.value || "bicubic",
      multiple: multiple.value || "32",
      max_long_edge: Math.trunc(clampGeneratorNumber(maxLongEdge.value, 2560, 0, 16384)),
      steps: Math.trunc(clampGeneratorNumber(steps.value, 20, 1, 75)),
      inherit_sampler_settings: inheritSampler.checked,
      cfg: clampGeneratorNumber(cfg.value, 8, 1, 10),
      sampler_name: samplerName.value || "euler",
      scheduler: scheduler.value || "simple",
      denoise: clampGeneratorNumber(denoise.value, 0.31, 0, 1),
      ...optimized,
    };
    writeSettings(node, widget, next);
    renderGeneratorPanel(node);
    backdrop.remove();
  });
}

function createDetailerTargetEditor(node, title, values, defaults, moveControls = null) {
  const target = mergeDefaults(defaults, values || {});
  const section = document.createElement("section");
  section.className = "easyuse-anima-aio-section";
  const header = document.createElement("div");
  header.className = "easyuse-anima-aio-node-stage-mini-header";
  header.append(Object.assign(document.createElement("h3"), { textContent: title }));
  if (moveControls) {
    header.append(moveControls);
  }
  section.append(header);
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
    values() {
      const optimized = optimization.values();
      return {
        ...target,
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
  const main = document.createElement("section");
  main.className = "easyuse-anima-aio-section full";
  main.append(Object.assign(document.createElement("h3"), { textContent: "Detailer" }));
  const enabled = field(main, "Enable detailer", checkbox(detailer.enabled));
  const checkpoint = field(main, "SAM3 checkpoint", textInput(detailer.sam3.checkpoint));
  body.append(main);

  const currentOrder = normalizeDetailerOrder(detailer.order);
  const moveButtons = {};
  const makeMoveControls = (targetName) => {
    const tools = document.createElement("div");
    tools.className = "easyuse-anima-aio-node-stage-tools";
    const moveUp = document.createElement("button");
    moveUp.type = "button";
    moveUp.className = "easyuse-anima-aio-node-icon-button";
    moveUp.textContent = "↑";
    applyTooltip(moveUp, "tip.detailerOrder");
    const moveDown = document.createElement("button");
    moveDown.type = "button";
    moveDown.className = "easyuse-anima-aio-node-icon-button";
    moveDown.textContent = "↓";
    applyTooltip(moveDown, "tip.detailerOrder");
    moveButtons[targetName] = { moveUp, moveDown };
    const move = (delta) => {
      const index = currentOrder.indexOf(targetName);
      const nextIndex = index + delta;
      if (index < 0 || nextIndex < 0 || nextIndex >= currentOrder.length) {
        return;
      }
      [currentOrder[index], currentOrder[nextIndex]] = [currentOrder[nextIndex], currentOrder[index]];
      renderTargetOrder();
    };
    moveUp.addEventListener("click", () => move(-1));
    moveDown.addEventListener("click", () => move(1));
    tools.append(moveUp, moveDown);
    return tools;
  };
  const face = createDetailerTargetEditor(
    node,
    "Face Detailer",
    detailer.face,
    DEFAULT_GENERATION_SETTINGS.detailer.face,
    makeMoveControls("face"),
  );
  const eye = createDetailerTargetEditor(
    node,
    "Eye Detailer",
    detailer.eye,
    DEFAULT_GENERATION_SETTINGS.detailer.eye,
    makeMoveControls("eye"),
  );
  const editors = { face, eye };
  function renderTargetOrder() {
    for (const targetName of currentOrder) {
      body.append(editors[targetName].section);
    }
    for (const [index, targetName] of currentOrder.entries()) {
      const buttons = moveButtons[targetName];
      if (!buttons) {
        continue;
      }
      buttons.moveUp.disabled = index === 0;
      buttons.moveDown.disabled = index === currentOrder.length - 1;
    }
  }
  renderTargetOrder();

  const cancel = document.createElement("button");
  cancel.textContent = "Cancel";
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = "Apply";
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    next.detailer = {
      ...next.detailer,
      enabled: enabled.checked,
      sam3: {
        context: "load_checkpoint",
        checkpoint: checkpoint.value || "sam3.1_multiplex_fp16.safetensors",
      },
      order: normalizeDetailerOrder(currentOrder),
      face: face.values(),
      eye: eye.values(),
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
  const syncCompare = () => {
    comparePrevious.disabled = !intermediate.checked;
    if (comparePrevious.disabled) {
      comparePrevious.checked = false;
    }
  };
  intermediate.addEventListener("change", syncCompare);
  syncCompare();
  body.append(section);

  const cancel = document.createElement("button");
  cancel.textContent = "Cancel";
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = "Apply";
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
    next.preview = {
      intermediate_images: intermediate.checked,
      compare_previous: intermediate.checked && comparePrevious.checked,
      image_feed: imageFeed.checked,
    };
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

  const cancel = document.createElement("button");
  cancel.textContent = "Cancel";
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = "Apply";
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
    ], settings.artist_mix.mode)
  );
  const artistStart = field(artistMix, "Start", numberInput(settings.artist_mix.start_percent, "0.01"));
  const artistStrength = field(artistMix, "Strength", numberInput(settings.artist_mix.strength_scale, "0.01"));
  body.append(artistMix);

  const cancel = document.createElement("button");
  cancel.textContent = "Cancel";
  const apply = document.createElement("button");
  apply.className = "primary";
  apply.textContent = "Apply";
  actions.append(cancel, apply);
  cancel.addEventListener("click", () => backdrop.remove());
  apply.addEventListener("click", () => {
    const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
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
    const settings = generatorSettings(node);
    const inputSeed = normalizeSeedValue(settings.sampler.seed, GENERATOR_SPECIAL_SEED_RANDOM);
    const seedToUse = resolveGeneratorSeedForQueue(node, inputSeed);
    settings.sampler.seed = seedToUse;
    outputInputs.generation_settings = settingsToCompactJson(settings);

    const workflowNode = findWorkflowNode(prompt.workflow, node.id);
    setWorkflowWidgetValue(node, workflowNode, GENERATOR_SETTINGS_WIDGET, outputInputs.generation_settings);

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

function updateGeneratorExecutedStatus(node, message) {
  if (!node) {
    return;
  }
  const nextImages = generatorPreviewImages(message);
  node.__easyuseAnimaGeneratorPreviewImages = nextImages;
  node.__easyuseAnimaSelectedPreviewIndex = generatorDefaultPreviewIndex(nextImages);
  node.__easyuseAnimaGeneratorStatus = {
    status: String(firstValue(message?.status, "generated") || "generated"),
    width: Number(firstValue(message?.width, 0)),
    height: Number(firstValue(message?.height, 0)),
    unet_name: String(firstValue(message?.unet_name, "")),
    sampler_backend: String(firstValue(message?.sampler_backend, "")),
  };
  updateGeneratorDomSummary(node);
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
    window.addEventListener("easyuse-anima-settings-updated", (event) => {
      applyGeneratorUiSettings(event.detail || {});
    });
    Promise.all([
      loadGeneratorSamplerOptions(),
      loadGeneratorUiSettings(),
    ]).then(refreshGeneratorPanels);
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
