import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { easyuseAnimaFetchComfyJson, easyuseAnimaFetchText } from "./easyuse_anima_api.js";
import { easyuseAnimaText, easyuseAnimaWatchLocale } from "./easyuse_anima_i18n.js";
import {
  aioCreateCheckboxInput as checkbox,
  aioCreateNumberInput as numberInput,
  aioCreateSelectInput as selectInput,
  aioCreateTextareaInput as textareaInput,
  aioCreateTextInput as textInput,
  aioNodeInputControlForSpec as nodeInputControlForSpec,
  aioNodeInputDefault as nodeInputDefault,
  aioValueFromNodeInputControl as valueFromNodeInputControl,
} from "./aio/dom_controls.js";
import { aioCreateDialogPrimitives } from "./aio/dialog_primitives.js";
import { aioCreateInputSettingsDialog } from "./aio/input_settings_dialog.js";
import { aioCreatePostprocessSettingsDialog } from "./aio/postprocess_settings_dialog.js";
import { aioCreatePreviewSettingsDialog } from "./aio/preview_settings_dialog.js";
import { createAioProfileApiClient } from "./aio/profile_api_client.js";
import { aioCreateProfileSettingsRuntime } from "./aio/profile_settings_runtime.js";
import { aioCreateGeneratorPanelRuntime } from "./aio/generator_panel_runtime.js";
import {
  aioCreateGeneratorQueueRuntime,
  aioInstallGeneratorQueuePromptHook,
} from "./aio/generator_queue_runtime.js";
import { aioCreateStageSettingsDialogs } from "./aio/stage_settings_dialogs.js";
import { aioCreateDetailerSettingsDialog } from "./aio/detailer_settings_dialog.js";
import { aioCreateSamplerSettingsDialog } from "./aio/sampler_settings_dialog.js";
import { aioCreateSaveSettingsDialog } from "./aio/save_settings_dialog.js";
import { aioCreateAdvancedSettingsDialog } from "./aio/advanced_settings_dialog.js";
import { aioCreateNativePreviewRuntime } from "./aio/native_preview_runtime.js";
import {
  aioCreateExtensionRuntime,
  aioListAttachedGeneratorNodes,
} from "./aio/extension_runtime.js";
import {
  AIO_BACKEND_DEPENDENCIES,
  AIO_OPTIONAL_DEPENDENCY_SPECS,
  aioNodeInputMap,
  aioNodeInputSpec,
  aioNodeInputSupported,
  aioNodeInputTooltip,
  aioOptionalDependencyAvailable,
  aioOptionalDependencyPack,
  aioOptionalDependencyStatus,
  aioQueryOptionalDependencies,
  aioUpscaleBackendMissingPacks,
} from "./aio/dependencies.js";
import {
  aioAppendPreviewFeed,
  aioCreatePreviewProgressTracker,
  aioDefaultPreviewIndex,
  aioDeletePreviewStoreEntry,
  aioMainPreviewImage,
  aioMergePreviewImages,
  aioPreviewEventDetail,
  aioPreviewFileSize,
  aioPreviewImageLabel,
  aioPreviewImageName,
  aioPreviewImages,
  aioPreviewNodeIdsFromDetail,
  aioPreviewResolution,
  aioPreviewRunId,
  aioRemovePreviewRun,
  aioResolveTerminalPreviewState,
  aioSelectedPreviewIndex,
  aioSuppressDefaultPreview,
  aioTagPreviewRun,
} from "./aio/preview.js";
import { aioPanelFromWheelEvent, consumeAioPanelWheel } from "./aio/wheel.js";
import {
  aioBuiltinProfileIds,
  aioBuiltinProfileSettings,
  aioFindUserProfileByName,
  aioProfileSettingsFingerprint,
  aioResolvedProfileValue,
  aioUserProfileName,
  aioUserProfileValue,
} from "./aio/presets.js";
import {
  AIO_DEFAULT_GENERATION_SETTINGS as DEFAULT_GENERATION_SETTINGS,
  AIO_DEFAULT_INPUT_SETTINGS as DEFAULT_INPUT_SETTINGS,
  AIO_GENERATOR_MAX_SEED as GENERATOR_MAX_SEED,
  AIO_GENERATOR_SEED_CONTROLS as GENERATOR_SEED_CONTROLS,
  AIO_GENERATOR_SPECIAL_SEED_DECREMENT as GENERATOR_SPECIAL_SEED_DECREMENT,
  AIO_GENERATOR_SPECIAL_SEED_INCREMENT as GENERATOR_SPECIAL_SEED_INCREMENT,
  AIO_GENERATOR_SPECIAL_SEED_RANDOM as GENERATOR_SPECIAL_SEED_RANDOM,
  aioAsBool as asBool,
  aioCloneJson as clone,
  aioMergeDefaults as mergeDefaults,
  aioMigrateGeneratorPostprocessSettings as migrateGeneratorPostprocessSettings,
  aioNormalizeGeneratorPreviewSettings as normalizeGeneratorPreviewSettings,
  aioNormalizeSeedControl as normalizeSeedControl,
  aioNormalizeSeedValue as normalizeSeedValue,
  aioParseSettingsValue,
  aioSettingsToCompactJson as settingsToCompactJson,
} from "./aio/settings.js";

const INPUT_NODE_TYPE = "EasyUseAnimaInput";
const GENERATOR_NODE_TYPE = "EasyUseAnimaAIOGenerator";
const INPUT_SETTINGS_WIDGET = "input_settings";
const GENERATOR_SETTINGS_WIDGET = "generation_settings";
const GENERATOR_PROFILE_CUSTOM_VALUE = "custom";
const GENERATOR_PREVIEW_EVENT = "easyuse-anima-aio-preview";
const GENERATOR_PANEL_MIN_HEIGHT = 430;
const GENERATOR_SPECIAL_SEEDS = [
  GENERATOR_SPECIAL_SEED_RANDOM,
  GENERATOR_SPECIAL_SEED_INCREMENT,
  GENERATOR_SPECIAL_SEED_DECREMENT,
];
const GENERATOR_VUE_NODE_CLASS = "easyuse-anima-aio-hide-native-live-preview";
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



const AIO_TEXT = {
  en: {
    "title.sampler": "SAMPLER",
    "title.preview": "PREVIEW",
    "title.highres": "HIGHRES",
    "title.detailer": "DETAILER",
    "title.upscale": "UPSCALE",
    "title.postprocess": "POSTPROCESS",
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
    "profile.groupBuiltIn": "Built-in profiles",
    "profile.groupUser": "User profiles",
    "profile.normal": "Normal",
    "profile.turbo": "Turbo",
    "profile.optimized": "Optimized",
    "profile.custom": "Custom",
    "profile.selectTip": "Choose a generation profile. Applying a profile replaces the node's complete generation settings.",
    "dialog.profile.title": "Generation Profiles",
    "dialog.profile.subtitle": "Choose a built-in profile or manage complete user setting snapshots.",
    "profile.savePrompt": "Save the current AiO settings as a user profile:",
    "profile.renamePrompt": "Rename the selected user profile:",
    "profile.overwriteConfirm": "A user profile named {name} already exists. Overwrite it?",
    "profile.deleteConfirm": "Delete the user profile {name}?",
    "profile.nameRequired": "Enter a profile name.",
    "profile.requestFailed": "Profile operation failed: {message}",
    "dialog.input.title": "Easy Use Anima Input Settings",
    "dialog.input.subtitle": "Advanced resource options are saved internally with the workflow.",
    "dialog.sampler.title": "Sampler Details",
    "dialog.sampler.subtitle": "Choose one of three sampler paths. Missing optional node packs are locked before queue execution.",
    "dialog.highres.title": "Highres Settings",
    "dialog.highres.subtitle": "Image scaling and Highres resampling settings are saved with the node.",
    "dialog.detailer.title": "Detailer Settings",
    "dialog.detailer.subtitle": "SAM3 detection and Impact detailer settings are saved with the node.",
    "dialog.upscale.title": "Upscale Settings",
    "dialog.upscale.subtitle": "Final-stage upscale runs after Detailer and before Save. Choose USDU or ResShift.",
    "dialog.postprocess.title": "Postprocess Settings",
    "dialog.postprocess.subtitle": "Final size fit runs after Detailer and Upscale, before Save. Cap by long edge or megapixels.",
    "dialog.preview.title": "Preview Options",
    "dialog.save.title": "Save Options",
    "dialog.save.subtitle": "Image Saver requires ComfyUI-Image-Saver. Missing node packs are reported during queue execution.",
    "dialog.advanced.title": "Advanced Options",
    "dialog.advanced.subtitle": "Advanced generation options stay in a popup and are serialized as versioned settings.",
    "section.loaderOptions": "Loader Options",
    "section.baseParameters": "Base Parameters",
    "section.samplerBackend": "Sampler Backend",
    "section.modGuidance": "Mod Guidance",
    "section.spectrumPatchAdvancedSampler": "Spectrum Patch / Advanced Sampler",
    "section.spectrumAdvancedCorrections": "Spectrum Advanced Corrections",
    "section.spectrumDcwCorrections": "Spectrum DCW / Corrections",
    "section.spdSpeed": "Spectrum + SPD / SPEED",
    "section.imageScale": "Image Scale",
    "section.highresSampler": "Highres Sampler",
    "section.highresOptimization": "Highres Optimization",
    "section.usduUpscale": "USDU Upscale",
    "section.usduSampler": "USDU Sampler",
    "section.usduOptimization": "USDU Spectrum/DCW",
    "section.resshiftUpscale": "ResShift Upscale",
    "section.finalFit": "Final Size Fit",
    "section.detailer": "Detailer",
    "section.detailerBlocks": "Detailer Blocks",
    "section.sam3Detect": "SAM3 Detect",
    "section.maskToSegs": "MaskToSEGS",
    "section.impactDetailer": "Impact Detailer",
    "section.nodePreview": "Node Preview",
    "section.saveBackend": "Save Backend",
    "section.imageSaverFiles": "Image Saver Files",
    "section.imageSaverMetadata": "Image Saver Metadata",
    "section.modelPatchOptimization": "Model Patch / Optimization",
    "section.animaDave": "Anima DAVE",
    "section.safePag": "Anima Safe PAG",
    "section.kjNodesOptimization": "KJNodes Optimization",
    "section.sageAttention": "SageAttention (KJNodes)",
    "section.torchCompile": "Torch Compile (KJNodes)",
    "section.torchCompileParameters": "Torch Compile Parameters",
    "section.artistMix": "Artist Mix",
    "field.unetWeightDtype": "UNET weight dtype",
    "field.clipDevice": "CLIP device",
    "field.seedMode": "Seed mode",
    "field.auraFlowShift": "AuraFlow shift",
    "field.profile": "Profile",
    "field.adapter": "Adapter",
    "field.modW": "Mod W",
    "field.startLayer": "Start layer",
    "field.endLayer": "End layer",
    "field.taper": "Taper",
    "field.taperScale": "Taper scale",
    "field.finalW": "Final W",
    "field.useSpectrumPatch": "Use Spectrum patch",
    "field.spectrumPatch": "Spectrum patch",
    "field.windowSize": "Window size",
    "field.flexWindow": "Flex window",
    "field.warmupSteps": "Warmup steps",
    "field.warmup": "Warmup",
    "field.tailActual": "Tail actual",
    "field.blendW": "Blend W",
    "field.chebyDegree": "Cheby degree",
    "field.cheby": "Cheby",
    "field.ridgeLambda": "Ridge lambda",
    "field.compatPolicy": "Compat policy",
    "field.compat": "Compat",
    "field.useCorrections": "Use corrections",
    "field.dcwMode": "DCW mode",
    "field.dcwLambda": "DCW lambda",
    "field.dcwBand": "DCW band",
    "field.smcCfg": "SMC-CFG",
    "field.smcAlpha": "SMC alpha",
    "field.smcLambda": "SMC lambda",
    "field.cfgppLambda": "CFG++ lambda",
    "field.sigma": "Sigma",
    "field.enableHighres": "Enable highres",
    "field.enableUpscale": "Enable upscale",
    "field.enablePostprocess": "Enable postprocess",
    "field.scaleBy": "Scale by",
    "field.upscaleBackend": "Upscale backend",
    "field.upscaleModel": "Upscale model",
    "field.autoTileSize": "Auto tile size",
    "field.autoTileTarget": "Auto tile target",
    "field.autoTileMin": "Auto tile min",
    "field.autoTileMax": "Auto tile max",
    "field.usduPrompt": "USDU prompt",
    "field.fitFinalSize": "Fit final size",
    "field.fitMode": "Fit by",
    "field.maxMegapixels": "Max megapixels",
    "field.fitMethod": "Fit method",
    "field.tileWidth": "Tile width",
    "field.tileHeight": "Tile height",
    "field.maskBlur": "Mask blur",
    "field.tilePadding": "Tile padding",
    "field.seamFix": "Seam fix",
    "field.seamDenoise": "Seam denoise",
    "field.seamWidth": "Seam width",
    "field.seamMaskBlur": "Seam mask blur",
    "field.seamPadding": "Seam padding",
    "field.forceUniformTiles": "Force uniform tiles",
    "field.tiledDecode": "Tiled decode",
    "field.tileBatch": "Tile batch",
    "field.student": "Student",
    "field.dtype": "Dtype",
    "field.chop": "Chop",
    "field.overlap": "Overlap",
    "field.method": "Method",
    "field.multiple": "Multiple",
    "field.maxLongEdge": "Max long edge",
    "field.blockName": "Block name",
    "field.prompt": "Prompt",
    "field.count": "Count",
    "field.threshold": "Threshold",
    "field.refine": "Refine",
    "field.individual": "Individual",
    "field.combined": "Combined",
    "field.cropFactor": "Crop factor",
    "field.bboxFill": "BBox fill",
    "field.dropSize": "Drop size",
    "field.contourFill": "Contour fill",
    "field.guideSize": "Guide size",
    "field.maxSize": "Max size",
    "field.feather": "Feather",
    "field.noiseMask": "Noise mask",
    "field.forceInpaint": "Force inpaint",
    "field.maskFeather": "Mask feather",
    "field.cycle": "Cycle",
    "field.alignment": "Alignment",
    "field.enableDetailer": "Enable detailer",
    "field.sam3Checkpoint": "SAM3 checkpoint",
    "field.intermediateImages": "Intermediate images",
    "field.comparePrevious": "Compare previous",
    "field.imageFeed": "Image feed",
    "field.feedCount": "Feed count",
    "field.saveImage": "Save image",
    "field.backend": "Backend",
    "field.filename": "Filename",
    "field.path": "Path",
    "field.extension": "Extension",
    "field.quality": "JPEG/WebP quality",
    "field.losslessWebp": "Lossless WebP",
    "field.optimizePng": "Optimize PNG",
    "field.counter": "Counter",
    "field.timeFormat": "Time format",
    "field.clipSkip": "Clip skip",
    "field.embedWorkflow": "Embed workflow",
    "field.workflowJson": "Workflow JSON",
    "field.savePromptMetadata": "Save prompt metadata",
    "field.additionalHashes": "Additional hashes",
    "field.manualHashBundles": "Manual hash bundles",
    "field.civitaiHashFetchers": "Civitai Hash Fetchers",
    "field.civitaiData": "Civitai data",
    "field.easyRemix": "Easy remix",
    "field.customMetadata": "Custom metadata",
    "field.useDave": "Use DAVE",
    "field.mask": "Mask",
    "field.daveStrength": "DAVE strength",
    "field.daveTau": "DAVE tau",
    "field.useSafePag": "Use Safe PAG",
    "field.pagScale": "Safe PAG scale",
    "field.blockIndices": "Safe PAG blocks",
    "field.perturbationStrength": "PAG perturbation",
    "field.headIndices": "PAG heads",
    "field.startPercent": "PAG start percent",
    "field.endPercent": "PAG end percent",
    "field.rescale": "PAG rescale",
    "field.rescaleMode": "PAG rescale mode",
    "field.kjFp16Accum": "KJNodes FP16 accum",
    "field.allowCompile": "Allow compile",
    "field.useTorchCompile": "Use Torch compile",
    "field.fullgraph": "Fullgraph",
    "field.dynamic": "Dynamic",
    "field.transformerBlocksOnly": "Transformer blocks only",
    "field.dynamoCacheLimit": "Dynamo cache limit",
    "field.debugKeys": "Debug keys",
    "field.disableDynamicVram": "Disable dynamic VRAM",
    "field.start": "Start",
    "field.strength": "Strength",
    "button.randomEach": "Randomize Each Time",
    "button.newFixed": "New Fixed Random",
    "button.useLast": "Use Last Queued: {seed}",
    "button.useLastNone": "Use Last Queued: -",
    "button.samplerDetails": "Sampler Details...",
    "button.highresSettings": "Highres Settings",
    "button.detailerSettings": "Detailer Settings",
    "button.upscaleSettings": "Upscale Settings",
    "button.postprocessSettings": "Postprocess Settings",
    "button.advancedOptions": "Advanced Options...",
    "button.saveOn": "Save Options: ON",
    "button.saveOff": "Save Options: OFF",
    "button.previewOptions": "Preview Options...",
    "button.moveUp": "Up",
    "button.moveDown": "Down",
    "button.addDetailerBlock": "+ Add Detailer Block",
    "button.addHashBundle": "+ Add Hash Fetcher Bundle",
    "button.addCivitaiFetcher": "+ Add Civitai Hash Fetcher",
    "button.remove": "Remove",
    "button.profileApply": "Apply",
    "button.profileSave": "Save",
    "button.profileRename": "Rename",
    "button.profileDelete": "Delete",
    "text.previewTitle": "Generated Image Preview",
    "text.previewSubtitle": "Preview slot is reserved for this node output.",
    "text.previewOptionsSubtitle": "Preview settings control only this node UI. They do not change saved image metadata.",
    "text.previewPrevious": "Previous",
    "text.previewCurrent": "Current",
    "text.previewDenoise": "Denoising preview",
    "text.previewGenerating": "Generating",
    "text.inputLoaderMode": "Loader mode: split diffusion model + VAE + CLIP",
    "text.highresDisabled": "Enable Highres to expose resize and second-pass controls.",
    "text.highresSpdManualRequired": "Spectrum SPD / SPEED is not reused by Highres. Highres uses the general KSampler path.",
    "text.detailerDisabled": "Enable Detailer to configure ordered processing blocks.",
    "text.upscaleDisabled": "Enable Upscale to run one final USDU or ResShift pass before saving.",
    "text.postprocessDisabled": "Enable Postprocess to cap the final image size before saving.",
    "text.usduAutoTile": "Auto tile uses target/min/max tile sizes",
    "text.usduManualTile": "Manual tile size",
    "text.inheritsMainSampler": "Reuses main CFG, sampler, and scheduler. Stage Spectrum/DCW stays independent.",
    "text.usesStageSamplerOverride": "Uses stage CFG, sampler, and scheduler with stage Spectrum/DCW.",
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
    "tip.highresFollow": "When enabled, Highres reuses the main CFG, sampler, and scheduler. Highres steps, denoise, Spectrum, and DCW remain stage-specific. SPD/SPEED falls back to general KSampler.",
    "tip.highresBackend": "Highres manual mode uses the general KSampler path to avoid second-pass model-patch conflicts.",
    "tip.highresScale": "Upscale ratio before the Highres second pass.",
    "tip.highresMaxEdge": "Maximum long edge after upscaling. Use 0 to disable this cap.",
    "tip.highresSteps": "Highres second-pass steps. This remains Highres-specific even when the main sampler is reused.",
    "tip.highresDenoise": "Highres second-pass denoise strength.",
    "tip.upscaleEnabled": "Runs one final upscale stage after Detailer and before Save.",
    "tip.upscaleSettings": "Open final-stage USDU or ResShift upscale options.",
    "tip.upscaleBackend": "Selects the final upscale backend. Only one backend is used for each run.",
    "tip.upscaleScale": "USDU upscale ratio used by Ultimate SD Upscale.",
    "tip.usduUpscaleModel": "Upscale model loaded through ComfyUI UpscaleModelLoader for USDU.",
    "tip.usduPrompt": "Full uses the current positive/negative conditioning. No-general rebuilds the USDU prompt from quality, artist, and trigger fields only; if Mod Guidance already applies quality tags, they are not duplicated in the USDU prompt.",
    "tip.usduMode": "USDU tile redraw order.",
    "tip.usduTile": "USDU manual tile, padding, and seam controls.",
    "tip.usduAutoTile": "When enabled, tile width/height are calculated from the expected upscaled size. Target is the preferred tile size, min and max clamp the automatic result, and values align to 64 pixels.",
    "tip.usduSeam": "USDU seam-fix controls.",
    "tip.postprocessEnabled": "Runs after Upscale and before Save. Use it for final size capping only.",
    "tip.postprocessSettings": "Open final size fit options for the Postprocess stage.",
    "tip.finalFit": "In Postprocess, downscale only when the final image exceeds the selected max long edge or megapixel limit.",
    "tip.resshiftScale": "ResShift super-resolution factor. The loader scale must match the selected student.",
    "tip.resshiftStudent": "ResShift student checkpoint. Auto-download fetches the matching released student.",
    "tip.resshiftDtype": "ResShift loader precision.",
    "tip.resshiftTiling": "ResShift tiling controls for large images.",
    "tip.detailerEnabled": "Run SAM3 and Impact Detailer stages after generation.",
    "tip.detailerBlock": "Each block can be enabled, reordered, and tuned independently.",
    "tip.detailerFollow": "When enabled, this detailer block uses the main CFG, sampler, and scheduler. Spectrum/DCW remain block-specific.",
    "tip.detailerSteps": "Impact Detailer sampling steps for this block.",
    "tip.detailerDenoise": "Impact Detailer denoise strength for this block.",
    "tip.detailerOrder": "Move this image-processing block earlier or later.",
    "tip.detailerName": "Display name for this detailer tab. It is saved with the workflow for UI organization.",
    "tip.addDetailerBlock": "Add a custom detailer block using the face detailer defaults.",
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
    "title.upscale": "UPSCALE",
    "title.postprocess": "후보정",
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
    "profile.groupBuiltIn": "기본 프로필",
    "profile.groupUser": "사용자 프로필",
    "profile.normal": "일반",
    "profile.turbo": "터보",
    "profile.optimized": "최적화",
    "profile.custom": "커스텀",
    "profile.selectTip": "생성 프로필을 선택합니다. 프로필 적용 시 노드의 전체 생성 설정이 교체됩니다.",
    "dialog.profile.title": "생성 프로필",
    "dialog.profile.subtitle": "기본 프로필을 선택하거나 전체 설정을 저장한 사용자 프로필을 관리합니다.",
    "profile.savePrompt": "현재 AiO 설정을 사용자 프로필로 저장합니다:",
    "profile.renamePrompt": "선택한 사용자 프로필의 새 이름을 입력합니다:",
    "profile.overwriteConfirm": "{name} 사용자 프로필이 이미 있습니다. 덮어쓸까요?",
    "profile.deleteConfirm": "{name} 사용자 프로필을 삭제할까요?",
    "profile.nameRequired": "프로필 이름을 입력하세요.",
    "profile.requestFailed": "프로필 작업 실패: {message}",
    "dialog.input.title": "Easy Use Anima Input 설정",
    "dialog.input.subtitle": "고급 리소스 옵션은 워크플로우 내부 설정으로 저장됩니다.",
    "dialog.sampler.title": "샘플러 상세 설정",
    "dialog.sampler.subtitle": "세 가지 샘플러 경로 중 하나를 선택합니다. 없는 선택 의존성은 큐 실행 전에 잠깁니다.",
    "dialog.highres.title": "Highres 설정",
    "dialog.highres.subtitle": "이미지 확대와 Highres 재샘플링 설정이 노드에 저장됩니다.",
    "dialog.detailer.title": "디테일러 설정",
    "dialog.detailer.subtitle": "SAM3 감지와 Impact Detailer 설정이 노드에 저장됩니다.",
    "dialog.upscale.title": "업스케일 설정",
    "dialog.upscale.subtitle": "최종 업스케일은 Detailer 이후 Save 전에 실행됩니다. USDU 또는 ResShift 중 하나를 선택합니다.",
    "dialog.postprocess.title": "후보정 설정",
    "dialog.postprocess.subtitle": "최종 해상도 맞춤은 Detailer와 Upscale 이후, Save 전에 실행됩니다. 긴 변 또는 메가픽셀 기준으로 제한합니다.",
    "dialog.preview.title": "프리뷰 옵션",
    "dialog.save.title": "저장 옵션",
    "dialog.save.subtitle": "Image Saver는 ComfyUI-Image-Saver가 필요합니다. 누락된 노드팩은 큐 실행 중 명확히 보고됩니다.",
    "dialog.advanced.title": "고급 옵션",
    "dialog.advanced.subtitle": "고급 생성 옵션은 팝업에서 관리되며 버전이 있는 설정으로 저장됩니다.",
    "section.loaderOptions": "로드 옵션",
    "section.baseParameters": "기본 파라미터",
    "section.samplerBackend": "샘플러 백엔드",
    "section.modGuidance": "Mod Guidance",
    "section.spectrumPatchAdvancedSampler": "Spectrum Patch / 고급 샘플러",
    "section.spectrumAdvancedCorrections": "Spectrum 고급 보정",
    "section.spectrumDcwCorrections": "Spectrum DCW / 보정",
    "section.spdSpeed": "Spectrum + SPD / SPEED",
    "section.imageScale": "이미지 확대",
    "section.highresSampler": "Highres 샘플러",
    "section.highresOptimization": "Highres 최적화",
    "section.usduUpscale": "USDU 업스케일",
    "section.usduSampler": "USDU 샘플러",
    "section.usduOptimization": "USDU Spectrum/DCW",
    "section.resshiftUpscale": "ResShift 업스케일",
    "section.finalFit": "최종 해상도 맞춤",
    "section.detailer": "디테일러",
    "section.detailerBlocks": "디테일러 블럭",
    "section.sam3Detect": "SAM3 감지",
    "section.maskToSegs": "MaskToSEGS",
    "section.impactDetailer": "Impact Detailer",
    "section.nodePreview": "노드 프리뷰",
    "section.saveBackend": "저장 백엔드",
    "section.imageSaverFiles": "Image Saver 파일",
    "section.imageSaverMetadata": "Image Saver 메타데이터",
    "section.modelPatchOptimization": "모델 패치 / 최적화",
    "section.animaDave": "Anima DAVE",
    "section.safePag": "Anima Safe PAG",
    "section.kjNodesOptimization": "KJNodes 최적화",
    "section.sageAttention": "SageAttention (KJNodes)",
    "section.torchCompile": "Torch Compile (KJNodes)",
    "section.torchCompileParameters": "Torch Compile 파라미터",
    "section.artistMix": "작가 태그 혼합",
    "field.unetWeightDtype": "UNET weight dtype",
    "field.clipDevice": "CLIP 장치",
    "field.seedMode": "시드 제어",
    "field.auraFlowShift": "AuraFlow 시프트",
    "field.profile": "프로필",
    "field.adapter": "어댑터",
    "field.modW": "Mod W",
    "field.startLayer": "시작 레이어",
    "field.endLayer": "끝 레이어",
    "field.taper": "테이퍼",
    "field.taperScale": "테이퍼 배율",
    "field.finalW": "Final W",
    "field.useSpectrumPatch": "Spectrum 패치 사용",
    "field.spectrumPatch": "Spectrum 패치",
    "field.windowSize": "윈도우 크기",
    "field.flexWindow": "Flex 윈도우",
    "field.warmupSteps": "웜업 스텝",
    "field.warmup": "웜업",
    "field.tailActual": "Tail 실제 스텝",
    "field.blendW": "Blend W",
    "field.chebyDegree": "Cheby 차수",
    "field.cheby": "Cheby",
    "field.ridgeLambda": "Ridge lambda",
    "field.compatPolicy": "호환 정책",
    "field.compat": "호환",
    "field.useCorrections": "보정 사용",
    "field.dcwMode": "DCW 모드",
    "field.dcwLambda": "DCW lambda",
    "field.dcwBand": "DCW 밴드",
    "field.smcCfg": "SMC-CFG",
    "field.smcAlpha": "SMC alpha",
    "field.smcLambda": "SMC lambda",
    "field.cfgppLambda": "CFG++ lambda",
    "field.sigma": "Sigma",
    "field.enableHighres": "Highres 활성화",
    "field.enableUpscale": "업스케일 활성화",
    "field.enablePostprocess": "후보정 활성화",
    "field.scaleBy": "확대 배율",
    "field.upscaleBackend": "업스케일 백엔드",
    "field.upscaleModel": "업스케일 모델",
    "field.autoTileSize": "타일 크기 자동지정",
    "field.autoTileTarget": "자동 타일 목표",
    "field.autoTileMin": "자동 타일 최소",
    "field.autoTileMax": "자동 타일 최대",
    "field.usduPrompt": "USDU 프롬프트",
    "field.fitFinalSize": "최종 해상도 맞춤",
    "field.fitMode": "맞춤 기준",
    "field.maxMegapixels": "최대 메가픽셀",
    "field.fitMethod": "맞춤 방식",
    "field.tileWidth": "타일 너비",
    "field.tileHeight": "타일 높이",
    "field.maskBlur": "마스크 블러",
    "field.tilePadding": "타일 패딩",
    "field.seamFix": "Seam fix",
    "field.seamDenoise": "Seam 디노이즈",
    "field.seamWidth": "Seam 너비",
    "field.seamMaskBlur": "Seam 마스크 블러",
    "field.seamPadding": "Seam 패딩",
    "field.forceUniformTiles": "균일 타일 강제",
    "field.tiledDecode": "타일 디코드",
    "field.tileBatch": "타일 배치",
    "field.student": "Student",
    "field.dtype": "Dtype",
    "field.chop": "Chop",
    "field.overlap": "Overlap",
    "field.method": "방식",
    "field.multiple": "배수 정렬",
    "field.maxLongEdge": "최대 긴 변",
    "field.blockName": "블럭 이름",
    "field.prompt": "프롬프트",
    "field.count": "개수",
    "field.threshold": "임계값",
    "field.refine": "정제",
    "field.individual": "개별 마스크",
    "field.combined": "통합 마스크",
    "field.cropFactor": "Crop factor",
    "field.bboxFill": "BBox 채우기",
    "field.dropSize": "Drop size",
    "field.contourFill": "Contour 채우기",
    "field.guideSize": "Guide size",
    "field.maxSize": "최대 크기",
    "field.feather": "Feather",
    "field.noiseMask": "노이즈 마스크",
    "field.forceInpaint": "인페인트 강제",
    "field.maskFeather": "마스크 Feather",
    "field.cycle": "반복",
    "field.alignment": "정렬",
    "field.enableDetailer": "디테일러 활성화",
    "field.sam3Checkpoint": "SAM3 체크포인트",
    "field.intermediateImages": "중간 이미지",
    "field.comparePrevious": "이전 이미지와 비교",
    "field.imageFeed": "이미지 피드",
    "field.feedCount": "피드 개수",
    "field.saveImage": "이미지 저장",
    "field.backend": "백엔드",
    "field.filename": "파일명",
    "field.path": "경로",
    "field.extension": "확장자",
    "field.quality": "JPEG/WebP 품질",
    "field.losslessWebp": "무손실 WebP",
    "field.optimizePng": "PNG 최적화",
    "field.counter": "카운터",
    "field.timeFormat": "시간 형식",
    "field.clipSkip": "Clip skip",
    "field.embedWorkflow": "워크플로우 임베드",
    "field.workflowJson": "워크플로우 JSON",
    "field.savePromptMetadata": "프롬프트 메타데이터 저장",
    "field.additionalHashes": "추가 해시",
    "field.manualHashBundles": "수동 해시 묶음",
    "field.civitaiHashFetchers": "Civitai Hash Fetcher",
    "field.civitaiData": "Civitai 데이터",
    "field.easyRemix": "Easy remix",
    "field.customMetadata": "사용자 메타데이터",
    "field.useDave": "DAVE 사용",
    "field.mask": "마스크",
    "field.daveStrength": "DAVE 강도",
    "field.daveTau": "DAVE tau",
    "field.useSafePag": "Safe PAG 사용",
    "field.pagScale": "Safe PAG scale",
    "field.blockIndices": "Safe PAG 블럭",
    "field.perturbationStrength": "PAG perturbation",
    "field.headIndices": "PAG 헤드",
    "field.startPercent": "PAG 시작 percent",
    "field.endPercent": "PAG 끝 percent",
    "field.rescale": "PAG rescale",
    "field.rescaleMode": "PAG rescale 모드",
    "field.kjFp16Accum": "KJNodes FP16 accumulation",
    "field.allowCompile": "컴파일 허용",
    "field.useTorchCompile": "Torch compile 사용",
    "field.fullgraph": "Fullgraph",
    "field.dynamic": "Dynamic",
    "field.transformerBlocksOnly": "Transformer block만",
    "field.dynamoCacheLimit": "Dynamo cache limit",
    "field.debugKeys": "Debug keys",
    "field.disableDynamicVram": "Dynamic VRAM 비활성화",
    "field.start": "시작",
    "field.strength": "강도",
    "button.randomEach": "매번 랜덤",
    "button.newFixed": "새 랜덤 고정",
    "button.useLast": "Last Queued: {seed}",
    "button.useLastNone": "Last Queued: -",
    "button.samplerDetails": "샘플러 상세...",
    "button.highresSettings": "Highres 설정",
    "button.detailerSettings": "디테일러 설정",
    "button.upscaleSettings": "업스케일 설정",
    "button.postprocessSettings": "후보정 설정",
    "button.advancedOptions": "고급 옵션...",
    "button.saveOn": "저장 옵션: ON",
    "button.saveOff": "저장 옵션: OFF",
    "button.previewOptions": "프리뷰 옵션...",
    "button.moveUp": "위",
    "button.moveDown": "아래",
    "button.addDetailerBlock": "+ 디테일러 블럭 추가",
    "button.addHashBundle": "+ Hash Fetcher 묶음 추가",
    "button.addCivitaiFetcher": "+ Civitai Hash Fetcher 추가",
    "button.remove": "삭제",
    "button.profileApply": "적용",
    "button.profileSave": "저장",
    "button.profileRename": "이름 변경",
    "button.profileDelete": "삭제",
    "text.previewTitle": "생성 이미지 미리보기",
    "text.previewSubtitle": "이 노드 출력 전용 미리보기 영역입니다.",
    "text.previewOptionsSubtitle": "프리뷰 설정은 이 노드 UI에만 적용됩니다. 저장 이미지 메타데이터는 바꾸지 않습니다.",
    "text.previewPrevious": "이전",
    "text.previewCurrent": "현재",
    "text.previewDenoise": "노이즈 제거 미리보기",
    "text.previewGenerating": "생성 중",
    "text.inputLoaderMode": "로드 방식: 디퓨전 모델 + VAE + CLIP 분리 로드",
    "text.highresDisabled": "Highres를 켜면 확대와 2차 샘플링 기본 설정이 표시됩니다.",
    "text.highresSpdManualRequired": "Spectrum SPD / SPEED는 Highres에서 재사용하지 않습니다. Highres는 일반 KSampler 경로를 사용합니다.",
    "text.detailerDisabled": "디테일러를 켜면 순서 조정 가능한 처리 블럭이 표시됩니다.",
    "text.upscaleDisabled": "Upscale을 켜면 저장 전에 USDU 또는 ResShift 최종 패스 하나를 실행합니다.",
    "text.postprocessDisabled": "후보정을 켜면 저장 전 최종 이미지 크기를 제한합니다.",
    "text.usduAutoTile": "자동 타일 target/min/max 사용",
    "text.usduManualTile": "수동 타일 크기",
    "text.inheritsMainSampler": "메인 CFG, 샘플러, 스케줄러를 따릅니다. Spectrum/DCW는 이 stage 설정을 사용합니다.",
    "text.usesStageSamplerOverride": "이 stage의 CFG, 샘플러, 스케줄러와 Spectrum/DCW를 사용합니다.",
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
    "tip.highresFollow": "켜져 있으면 Highres가 메인 CFG, 샘플러, 스케줄러를 따릅니다. Highres 스텝, 디노이즈, Spectrum, DCW는 stage별로 적용됩니다. SPD/SPEED는 일반 KSampler로 대체됩니다.",
    "tip.highresBackend": "Highres 수동 모드는 2차 모델패치 충돌을 피하기 위해 일반 KSampler 경로를 사용합니다.",
    "tip.highresScale": "Highres 2차 패스 전에 적용할 확대 배율입니다.",
    "tip.highresMaxEdge": "확대 후 긴 변 제한입니다. 0이면 제한하지 않습니다.",
    "tip.highresSteps": "Highres 2차 패스 스텝입니다. 메인 샘플러를 재사용해도 이 값은 Highres 전용으로 적용됩니다.",
    "tip.highresDenoise": "Highres 2차 패스 디노이즈 강도입니다.",
    "tip.upscaleEnabled": "Detailer 이후 Save 전에 최종 업스케일 단계를 한 번 실행합니다.",
    "tip.upscaleSettings": "최종 USDU 또는 ResShift 업스케일 옵션을 엽니다.",
    "tip.upscaleBackend": "최종 업스케일 백엔드입니다. 한 번 실행할 때 하나만 사용합니다.",
    "tip.upscaleScale": "Ultimate SD Upscale에 전달할 USDU 확대 배율입니다.",
    "tip.usduUpscaleModel": "USDU에서 ComfyUI UpscaleModelLoader로 로드할 업스케일 모델입니다.",
    "tip.usduPrompt": "full은 현재 positive/negative conditioning을 그대로 사용합니다. no_general은 USDU 프롬프트를 quality, artist, trigger 필드만으로 다시 만들며, Mod Guidance가 quality 태그를 이미 적용 중이면 USDU 프롬프트에 중복으로 넣지 않습니다.",
    "tip.usduMode": "USDU 타일 redraw 순서입니다.",
    "tip.usduTile": "USDU 수동 타일, padding, seam 설정입니다.",
    "tip.usduAutoTile": "활성화하면 최종 업스케일 예상 크기에서 타일 너비/높이를 계산합니다. 목표값은 선호 타일 크기, 최소/최대는 자동 결과의 하한/상한이며 64px 단위로 정렬합니다.",
    "tip.usduSeam": "USDU seam-fix 설정입니다.",
    "tip.postprocessEnabled": "Upscale 이후 Save 전에 실행됩니다. 최종 크기 제한만 담당합니다.",
    "tip.postprocessSettings": "후보정 단계의 최종 해상도 맞춤 옵션을 엽니다.",
    "tip.finalFit": "후보정 단계에서 최종 이미지가 선택한 최대 긴 변 또는 메가픽셀 수를 넘을 때만 다운스케일합니다.",
    "tip.resshiftScale": "ResShift 초해상도 배율입니다. Loader scale은 선택한 student와 일치해야 합니다.",
    "tip.resshiftStudent": "ResShift student 체크포인트입니다. Auto-download는 배율에 맞는 공개 student를 받습니다.",
    "tip.resshiftDtype": "ResShift loader precision입니다.",
    "tip.resshiftTiling": "큰 이미지용 ResShift 타일링 설정입니다.",
    "tip.detailerEnabled": "생성 후 SAM3와 Impact Detailer 단계를 실행합니다.",
    "tip.detailerBlock": "각 블럭은 개별 활성화, 순서 변경, 기본 설정 조정이 가능합니다.",
    "tip.detailerFollow": "켜져 있으면 이 디테일러 블럭이 메인 CFG, 샘플러, 스케줄러를 따릅니다. Spectrum/DCW는 블럭별 설정을 사용합니다.",
    "tip.detailerSteps": "이 블럭의 Impact Detailer 샘플링 스텝입니다.",
    "tip.detailerDenoise": "이 블럭의 Impact Detailer 디노이즈 강도입니다.",
    "tip.detailerOrder": "이 이미지 처리 블럭의 실행 순서를 앞뒤로 이동합니다.",
    "tip.detailerName": "이 디테일러 탭의 표시 이름입니다. UI 정리를 위해 워크플로우에 저장됩니다.",
    "tip.addDetailerBlock": "얼굴 디테일러 기본값으로 커스텀 디테일러 블럭을 추가합니다.",
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
    "button.upscaleSettings": "Upscale 設定",
    "button.advancedOptions": "詳細オプション...",
    "button.saveOn": "保存オプション: ON",
    "button.saveOff": "保存オプション: OFF",
    "button.moveUp": "上へ",
    "button.moveDown": "下へ",
    "button.addDetailerBlock": "+ Detailer ブロックを追加",
    "button.addCivitaiFetcher": "+ Civitai Hash Fetcher を追加",
    "button.remove": "削除",
    "text.previewTitle": "生成画像プレビュー",
    "text.previewSubtitle": "このノード出力専用のプレビュー領域です。",
    "text.previewDenoise": "デノイズプレビュー",
    "text.previewGenerating": "生成中",
    "text.highresDisabled": "Highres を有効にすると拡大と二回目サンプリングの基本設定を表示します。",
    "text.highresSpdManualRequired": "Spectrum SPD / SPEED は Highres では再利用しません。Highres は通常 KSampler 経路を使います。",
    "text.detailerDisabled": "Detailer を有効にすると順序変更できる処理ブロックを表示します。",
    "text.upscaleDisabled": "Upscale を有効にすると保存前に USDU または ResShift の最終パスを一つ実行します。",
    "text.inheritsMainSampler": "メイン CFG、サンプラー、スケジューラーに追従します。Spectrum/DCW はこの stage の設定を使います。",
    "text.usesStageSamplerOverride": "この stage の CFG、サンプラー、スケジューラーと Spectrum/DCW を使います。",
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
    "tip.highresFollow": "有効時、Highres はメイン CFG、サンプラー、スケジューラーに追従します。Highres ステップ、デノイズ、Spectrum、DCW は stage 別に適用されます。SPD/SPEED は通常 KSampler に置き換えます。",
    "tip.highresBackend": "Highres 手動モードは二回目の model patch 衝突を避けるため通常 KSampler 経路を使います。",
    "tip.highresScale": "Highres 二回目パス前の拡大倍率です。",
    "tip.highresMaxEdge": "拡大後の長辺上限です。0 で上限なしです。",
    "tip.highresSteps": "Highres 二回目パスのステップです。メインサンプラーを再利用してもこの値は Highres 専用です。",
    "tip.highresDenoise": "Highres 二回目パスのデノイズ強度です。",
    "tip.detailerEnabled": "生成後に SAM3 と Impact Detailer を実行します。",
    "tip.detailerBlock": "各ブロックは個別に有効化、並べ替え、調整できます。",
    "tip.detailerFollow": "有効時、この Detailer ブロックはメイン CFG、サンプラー、スケジューラーに追従します。Spectrum/DCW はブロック別設定を使います。",
    "tip.detailerSteps": "このブロックの Impact Detailer ステップです。",
    "tip.detailerDenoise": "このブロックの Impact Detailer デノイズ強度です。",
    "tip.detailerOrder": "この画像処理ブロックの実行順を移動します。",
    "tip.detailerName": "この detailer tab の表示名です。UI 整理用に workflow へ保存されます。",
    "tip.addDetailerBlock": "顔 Detailer の既定値でカスタム Detailer ブロックを追加します。",
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
    "button.upscaleSettings": "Upscale 设置",
    "button.advancedOptions": "高级选项...",
    "button.saveOn": "保存选项: ON",
    "button.saveOff": "保存选项: OFF",
    "button.moveUp": "上移",
    "button.moveDown": "下移",
    "button.addDetailerBlock": "+ 添加 Detailer 块",
    "button.addCivitaiFetcher": "+ 添加 Civitai Hash Fetcher",
    "button.remove": "删除",
    "text.previewTitle": "生成图像预览",
    "text.previewSubtitle": "此区域专用于该节点输出预览。",
    "text.previewDenoise": "降噪预览",
    "text.previewGenerating": "生成中",
    "text.highresDisabled": "启用 Highres 后显示放大和第二次采样基础设置。",
    "text.highresSpdManualRequired": "Spectrum SPD / SPEED 不会被 Highres 复用。Highres 使用普通 KSampler 路径。",
    "text.detailerDisabled": "启用 Detailer 后显示可排序的处理块。",
    "text.upscaleDisabled": "启用 Upscale 后在保存前运行一次 USDU 或 ResShift 最终处理。",
    "text.inheritsMainSampler": "跟随主 CFG、采样器和调度器。Spectrum/DCW 使用此 stage 的设置。",
    "text.usesStageSamplerOverride": "使用此 stage 的 CFG、采样器、调度器和 Spectrum/DCW。",
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
    "tip.highresFollow": "启用时，Highres 跟随主 CFG、采样器和调度器。Highres 步数、降噪、Spectrum 和 DCW 按 stage 独立应用。SPD/SPEED 会回退到普通 KSampler。",
    "tip.highresBackend": "Highres 手动模式使用普通 KSampler 路径，以避免第二次模型补丁冲突。",
    "tip.highresScale": "Highres 第二次采样前的放大倍率。",
    "tip.highresMaxEdge": "放大后的最长边上限。0 表示不限制。",
    "tip.highresSteps": "Highres 第二次采样步数。即使复用主采样器，此值也只用于 Highres。",
    "tip.highresDenoise": "Highres 第二次采样的降噪强度。",
    "tip.detailerEnabled": "生成后运行 SAM3 和 Impact Detailer 阶段。",
    "tip.detailerBlock": "每个块都可单独启用、排序和调整。",
    "tip.detailerFollow": "启用时，此 Detailer 块跟随主 CFG、采样器和调度器。Spectrum/DCW 使用块级设置。",
    "tip.detailerSteps": "此块的 Impact Detailer 采样步数。",
    "tip.detailerDenoise": "此块的 Impact Detailer 降噪强度。",
    "tip.detailerOrder": "移动此图像处理块的执行顺序。",
    "tip.detailerName": "此 detailer tab 的显示名称，会随 workflow 保存用于 UI 管理。",
    "tip.addDetailerBlock": "使用面部 Detailer 默认值添加自定义 Detailer 块。",
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
    "info.optionalDependency.title": "EasyUseAnima AiO dependency check",
    "info.optionalDependency.complete": "Available: {available}/{total}.",
    "info.optionalDependency.missing": "Missing: {items}. Related features will be disabled or changed before queueing.",
    "info.optionalDependency.error": "Query failed: {items}. Settings were kept unchanged and will be checked again before queueing.",
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
    "tip.safePagEnabled": "Applies Anima Safe PAG before KJNodes optimization and Torch Compile.",
    "tip.safePagScale": "Safe PAG guidance scale. 0 disables the guidance contribution.",
    "tip.safePagBlocks": "Comma-separated transformer block indices passed to AnimaSafePAG.",
    "tip.safePagPerturbation": "Attention perturbation blend strength. 1.0 is closest to hard PAG.",
    "tip.safePagHeads": "Optional comma-separated attention head indices. Empty targets all heads.",
    "tip.safePagStart": "Sampling percent where Safe PAG starts.",
    "tip.safePagEnd": "Sampling percent where Safe PAG ends.",
    "tip.safePagRescale": "Guidance rescale amount after Safe PAG correction.",
    "tip.safePagRescaleMode": "Rescale mode passed to AnimaSafePAG.",
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
    "tip.savePromptMetadata": "Writes positive and negative prompt text to Image Saver metadata. Disable to save without prompt text.",
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
    "info.optionalDependency.title": "EasyUseAnima AiO 의존성 조회",
    "info.optionalDependency.complete": "사용 가능: {available}/{total}.",
    "info.optionalDependency.missing": "미설치: {items}. 관련 기능은 큐 실행 전에 비활성화되거나 대체됩니다.",
    "info.optionalDependency.error": "조회 실패: {items}. 설정을 변경하지 않았으며 다음 큐 실행 전에 다시 조회합니다.",
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
    "tip.safePagEnabled": "KJNodes 최적화와 Torch Compile 전에 Anima Safe PAG를 적용합니다.",
    "tip.safePagScale": "Safe PAG guidance scale입니다. 0이면 guidance 기여를 비활성화합니다.",
    "tip.safePagBlocks": "AnimaSafePAG에 전달할 transformer block 인덱스입니다. 쉼표로 여러 개를 지정합니다.",
    "tip.safePagPerturbation": "attention perturbation 혼합 강도입니다. 1.0은 hard PAG에 가장 가깝습니다.",
    "tip.safePagHeads": "선택 attention head 인덱스입니다. 비우면 모든 head를 대상으로 합니다.",
    "tip.safePagStart": "Safe PAG가 시작되는 샘플링 percent입니다.",
    "tip.safePagEnd": "Safe PAG가 끝나는 샘플링 percent입니다.",
    "tip.safePagRescale": "Safe PAG 보정 뒤 guidance를 rescale하는 양입니다.",
    "tip.safePagRescaleMode": "AnimaSafePAG에 전달할 rescale 모드입니다.",
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
    "tip.savePromptMetadata": "Image Saver 메타데이터에 positive/negative 프롬프트 텍스트를 기록합니다. 끄면 프롬프트 텍스트를 비워 저장합니다.",
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
    "info.optionalDependency.title": "EasyUseAnima AiO 依存関係チェック",
    "info.optionalDependency.complete": "利用可能: {available}/{total}。",
    "info.optionalDependency.missing": "未インストール: {items}。関連機能はキュー実行前に無効化または変更されます。",
    "info.optionalDependency.error": "照会失敗: {items}。設定は変更せず、次回のキュー実行前に再確認します。",
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
    "tip.savePromptMetadata": "Image Saver metadata に positive/negative prompt text を書き込みます。無効にすると prompt text は空で保存されます。",
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
    "info.optionalDependency.title": "EasyUseAnima AiO 依赖项检查",
    "info.optionalDependency.complete": "可用: {available}/{total}。",
    "info.optionalDependency.missing": "未安装: {items}。相关功能将在加入队列前被禁用或替换。",
    "info.optionalDependency.error": "查询失败: {items}。设置未被修改，并将在下次加入队列前重新检查。",
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
    "tip.savePromptMetadata": "将 positive/negative prompt text 写入 Image Saver metadata。关闭后以空 prompt text 保存。",
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
  "Use Safe PAG": "tip.safePagEnabled",
  "Safe PAG scale": "tip.safePagScale",
  "Safe PAG blocks": "tip.safePagBlocks",
  "PAG perturbation": "tip.safePagPerturbation",
  "PAG heads": "tip.safePagHeads",
  "PAG start percent": "tip.safePagStart",
  "PAG end percent": "tip.safePagEnd",
  "PAG rescale": "tip.safePagRescale",
  "PAG rescale mode": "tip.safePagRescaleMode",
  "Enable highres": "tip.highresEnabled",
  "Enable upscale": "tip.upscaleEnabled",
  "Enable postprocess": "tip.postprocessEnabled",
  "Scale by": "tip.highresScale",
  "Upscale backend": "tip.upscaleBackend",
  "Upscale model": "tip.usduUpscaleModel",
  "Auto tile size": "tip.usduAutoTile",
  "Auto tile target": "tip.usduAutoTile",
  "Auto tile min": "tip.usduAutoTile",
  "Auto tile max": "tip.usduAutoTile",
  "USDU prompt": "tip.usduPrompt",
  "Fit final size": "tip.finalFit",
  "Fit by": "tip.finalFit",
  "Max long edge": "tip.finalFit",
  "Max megapixels": "tip.finalFit",
  "Fit method": "tip.finalFit",
  "Tile width": "tip.usduTile",
  "Tile height": "tip.usduTile",
  "Mask blur": "tip.usduTile",
  "Tile padding": "tip.usduTile",
  "Seam fix": "tip.usduSeam",
  "Seam denoise": "tip.usduSeam",
  "Seam width": "tip.usduSeam",
  "Seam mask blur": "tip.usduSeam",
  "Seam padding": "tip.usduSeam",
  "Force uniform tiles": "tip.usduTile",
  "Tiled decode": "tip.usduTile",
  "Tile batch": "tip.resshiftTiling",
  "Student": "tip.resshiftStudent",
  "Dtype": "tip.resshiftDtype",
  "Chop": "tip.resshiftTiling",
  "Overlap": "tip.resshiftTiling",
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
  "Save prompt metadata": "tip.savePromptMetadata",
  "Civitai data": "tip.saveCivitaiData",
  "Easy remix": "tip.saveEasyRemix",
  "Custom metadata": "tip.saveCustom",
  "Start": "tip.artistMixStart",
  "Strength": "tip.artistMixStrength",
};

const AIO_STATIC_TEXT_KEYS = {
  "Easy Use Anima Input Settings": "dialog.input.title",
  "Advanced resource options are saved internally with the workflow.": "dialog.input.subtitle",
  "Sampler Details": "dialog.sampler.title",
  "Choose one of three sampler paths. Missing optional node packs are locked before queue execution.": "dialog.sampler.subtitle",
  "Highres Settings": "dialog.highres.title",
  "Image scaling, highres resampling, and Spectrum optimization are saved with the node.": "dialog.highres.subtitle",
  "Image scaling and Highres resampling settings are saved with the node.": "dialog.highres.subtitle",
  "Upscale Settings": "dialog.upscale.title",
  "Final-stage upscale runs after Detailer and before Save. Choose USDU or ResShift.": "dialog.upscale.subtitle",
  "Postprocess Settings": "dialog.postprocess.title",
  "Final size fit runs after Detailer and Upscale, before Save. Cap by long edge or megapixels.": "dialog.postprocess.subtitle",
  "Detailer Settings": "dialog.detailer.title",
  "SAM3 detection and Impact detailer settings are saved with the node.": "dialog.detailer.subtitle",
  "Preview Options": "dialog.preview.title",
  "Save Options": "dialog.save.title",
  "Image Saver requires ComfyUI-Image-Saver. Missing node packs are reported during queue execution.": "dialog.save.subtitle",
  "Advanced Options": "dialog.advanced.title",
  "Advanced generation options stay in a popup and are serialized as versioned settings.": "dialog.advanced.subtitle",
  "Loader Options": "section.loaderOptions",
  "Base Parameters": "section.baseParameters",
  "Sampler Backend": "section.samplerBackend",
  "Mod Guidance": "section.modGuidance",
  "Spectrum Patch / Advanced Sampler": "section.spectrumPatchAdvancedSampler",
  "Spectrum Advanced Corrections": "section.spectrumAdvancedCorrections",
  "Spectrum DCW / Corrections": "section.spectrumDcwCorrections",
  "Spectrum + SPD / SPEED": "section.spdSpeed",
  "Image Scale": "section.imageScale",
  "Highres Sampler": "section.highresSampler",
  "Highres Optimization": "section.highresOptimization",
  "USDU Upscale": "section.usduUpscale",
  "USDU Sampler": "section.usduSampler",
  "USDU Spectrum/DCW": "section.usduOptimization",
  "ResShift Upscale": "section.resshiftUpscale",
  "Final Size Fit": "section.finalFit",
  "Detailer": "section.detailer",
  "Detailer Blocks": "section.detailerBlocks",
  "SAM3 Detect": "section.sam3Detect",
  "MaskToSEGS": "section.maskToSegs",
  "Impact Detailer": "section.impactDetailer",
  "Node Preview": "section.nodePreview",
  "Save Backend": "section.saveBackend",
  "Image Saver Files": "section.imageSaverFiles",
  "Image Saver Metadata": "section.imageSaverMetadata",
  "Model Patch / Optimization": "section.modelPatchOptimization",
  "Anima DAVE": "section.animaDave",
  "Anima Safe PAG": "section.safePag",
  "KJNodes Optimization": "section.kjNodesOptimization",
  "SageAttention (KJNodes)": "section.sageAttention",
  "Torch Compile (KJNodes)": "section.torchCompile",
  "Torch Compile Parameters": "section.torchCompileParameters",
  "Artist Mix": "section.artistMix",
};

const AIO_FIELD_LABEL_KEYS = {
  "UNET weight dtype": "field.unetWeightDtype",
  "CLIP device": "field.clipDevice",
  "Seed": "label.seed",
  "Seed mode": "field.seedMode",
  "Steps": "label.steps",
  "CFG": "label.cfg",
  "AuraFlow shift": "field.auraFlowShift",
  "Denoise": "label.denoise",
  "Mode": "label.mode",
  "Sampler": "label.sampler",
  "Scheduler": "label.scheduler",
  "Profile": "field.profile",
  "Adapter": "field.adapter",
  "Mod W": "field.modW",
  "Start layer": "field.startLayer",
  "End layer": "field.endLayer",
  "Taper": "field.taper",
  "Taper scale": "field.taperScale",
  "Final W": "field.finalW",
  "Use Spectrum patch": "field.useSpectrumPatch",
  "Spectrum patch": "field.spectrumPatch",
  "Window size": "field.windowSize",
  "Flex window": "field.flexWindow",
  "Warmup steps": "field.warmupSteps",
  "Warmup": "field.warmup",
  "Tail actual": "field.tailActual",
  "Blend W": "field.blendW",
  "Cheby degree": "field.chebyDegree",
  "Cheby": "field.cheby",
  "Ridge lambda": "field.ridgeLambda",
  "Compat policy": "field.compatPolicy",
  "Compat": "field.compat",
  "Use corrections": "field.useCorrections",
  "DCW mode": "field.dcwMode",
  "DCW lambda": "field.dcwLambda",
  "DCW band": "field.dcwBand",
  "SMC-CFG": "field.smcCfg",
  "SMC alpha": "field.smcAlpha",
  "SMC lambda": "field.smcLambda",
  "CFG++ lambda": "field.cfgppLambda",
  "Scale": "label.scaleBy",
  "Sigma": "field.sigma",
  "Enable highres": "field.enableHighres",
  "Enable upscale": "field.enableUpscale",
  "Enable postprocess": "field.enablePostprocess",
  "Scale by": "field.scaleBy",
  "Upscale backend": "field.upscaleBackend",
  "Upscale model": "field.upscaleModel",
  "Auto tile size": "field.autoTileSize",
  "Auto tile target": "field.autoTileTarget",
  "Auto tile min": "field.autoTileMin",
  "Auto tile max": "field.autoTileMax",
  "USDU prompt": "field.usduPrompt",
  "Fit final size": "field.fitFinalSize",
  "Fit by": "field.fitMode",
  "Max megapixels": "field.maxMegapixels",
  "Fit method": "field.fitMethod",
  "Tile width": "field.tileWidth",
  "Tile height": "field.tileHeight",
  "Mask blur": "field.maskBlur",
  "Tile padding": "field.tilePadding",
  "Seam fix": "field.seamFix",
  "Seam denoise": "field.seamDenoise",
  "Seam width": "field.seamWidth",
  "Seam mask blur": "field.seamMaskBlur",
  "Seam padding": "field.seamPadding",
  "Force uniform tiles": "field.forceUniformTiles",
  "Tiled decode": "field.tiledDecode",
  "Tile batch": "field.tileBatch",
  "Student": "field.student",
  "Dtype": "field.dtype",
  "Chop": "field.chop",
  "Overlap": "field.overlap",
  "Method": "field.method",
  "Multiple": "field.multiple",
  "Max long edge": "field.maxLongEdge",
  "Follow main sampler": "label.followMainSampler",
  "Block name": "field.blockName",
  "Enable": "label.enabled",
  "Prompt": "field.prompt",
  "Count": "field.count",
  "Threshold": "field.threshold",
  "Refine": "field.refine",
  "Individual": "field.individual",
  "Combined": "field.combined",
  "Crop factor": "field.cropFactor",
  "BBox fill": "field.bboxFill",
  "Drop size": "field.dropSize",
  "Contour fill": "field.contourFill",
  "Guide size": "field.guideSize",
  "Max size": "field.maxSize",
  "Feather": "field.feather",
  "Noise mask": "field.noiseMask",
  "Force inpaint": "field.forceInpaint",
  "Mask feather": "field.maskFeather",
  "Cycle": "field.cycle",
  "Alignment": "field.alignment",
  "Enable detailer": "field.enableDetailer",
  "SAM3 checkpoint": "field.sam3Checkpoint",
  "Intermediate images": "field.intermediateImages",
  "Compare previous": "field.comparePrevious",
  "Image feed": "field.imageFeed",
  "Feed count": "field.feedCount",
  "Save image": "field.saveImage",
  "Backend": "field.backend",
  "Filename": "field.filename",
  "Path": "field.path",
  "Extension": "field.extension",
  "JPEG/WebP quality": "field.quality",
  "Lossless WebP": "field.losslessWebp",
  "Optimize PNG": "field.optimizePng",
  "Counter": "field.counter",
  "Time format": "field.timeFormat",
  "Clip skip": "field.clipSkip",
  "Embed workflow": "field.embedWorkflow",
  "Workflow JSON": "field.workflowJson",
  "Save prompt metadata": "field.savePromptMetadata",
  "Additional hashes": "field.additionalHashes",
  "Manual hash bundles": "field.manualHashBundles",
  "Civitai Hash Fetchers": "field.civitaiHashFetchers",
  "Civitai data": "field.civitaiData",
  "Easy remix": "field.easyRemix",
  "Custom metadata": "field.customMetadata",
  "Use DAVE": "field.useDave",
  "Mask": "field.mask",
  "DAVE strength": "field.daveStrength",
  "DAVE tau": "field.daveTau",
  "Use Safe PAG": "field.useSafePag",
  "Safe PAG scale": "field.pagScale",
  "Safe PAG blocks": "field.blockIndices",
  "PAG perturbation": "field.perturbationStrength",
  "PAG heads": "field.headIndices",
  "PAG start percent": "field.startPercent",
  "PAG end percent": "field.endPercent",
  "PAG rescale": "field.rescale",
  "PAG rescale mode": "field.rescaleMode",
  "KJNodes FP16 accum": "field.kjFp16Accum",
  "Allow compile": "field.allowCompile",
  "Use Torch compile": "field.useTorchCompile",
  "Fullgraph": "field.fullgraph",
  "Dynamic": "field.dynamic",
  "Transformer blocks only": "field.transformerBlocksOnly",
  "Dynamo cache limit": "field.dynamoCacheLimit",
  "Debug keys": "field.debugKeys",
  "Disable dynamic VRAM": "field.disableDynamicVram",
  "Start": "field.start",
  "Strength": "field.strength",
};

function aioText(key) {
  return easyuseAnimaText(AIO_TEXT, key);
}

function aioTextOr(key, fallback) {
  const text = key ? aioText(key) : "";
  return text && text !== key ? text : fallback;
}

function aioStaticText(text) {
  return aioTextOr(AIO_STATIC_TEXT_KEYS[text], text);
}

function aioFieldLabel(label) {
  return aioTextOr(AIO_FIELD_LABEL_KEYS[label], label);
}

function aioFormat(key, values = {}) {
  let text = aioText(key);
  for (const [name, value] of Object.entries(values)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }
  return text;
}

function aioFieldPresentation(label, tooltipKey = "") {
  const displayLabel = aioFieldLabel(label);
  const resolvedTooltipKey = tooltipKey || AIO_FIELD_TOOLTIP_KEYS[label] || "";
  const tooltipText = resolvedTooltipKey
    ? aioText(resolvedTooltipKey)
    : aioFormat("tip.fieldGeneric", { label: displayLabel });
  return { displayLabel, tooltipText };
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
  status: {},
  nodeInfo: {},
  errors: {},
  reportedSignature: "",
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
  const data = await easyuseAnimaFetchComfyJson(api, "/object_info/KSampler");
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
  const next = await aioQueryOptionalDependencies(
    AIO_OPTIONAL_DEPENDENCY_SPECS,
    async (spec) => {
      const data = await easyuseAnimaFetchComfyJson(api, `/object_info/${encodeURIComponent(spec.nodeId)}`);
      return data?.[spec.nodeId] || null;
    },
  );
  generatorOptionalDependencyState.available = next.available;
  generatorOptionalDependencyState.status = next.status;
  generatorOptionalDependencyState.nodeInfo = next.nodeInfo;
  generatorOptionalDependencyState.errors = next.errors;
}

function optionalDependencyResultLabel(key) {
  const spec = AIO_OPTIONAL_DEPENDENCY_SPECS[key];
  return spec ? `${spec.nodeId} (${spec.pack})` : key;
}

function reportGeneratorOptionalDependencyStatus() {
  const rows = Object.entries(AIO_OPTIONAL_DEPENDENCY_SPECS).map(([key, spec]) => ({
    key,
    node: spec.nodeId,
    pack: spec.pack,
    status: generatorOptionalDependencyState.status[key] || "error",
    error: generatorOptionalDependencyState.errors[key] || "",
  }));
  const available = rows.filter((row) => row.status === "available");
  const missing = rows.filter((row) => row.status === "missing");
  const failed = rows.filter((row) => row.status === "error");
  console.info("[EasyUseAnima] AiO optional dependency query result", rows);

  const details = [aioFormat("info.optionalDependency.complete", {
    available: available.length,
    total: rows.length,
  })];
  if (missing.length) {
    details.push(aioFormat("info.optionalDependency.missing", {
      items: missing.map((row) => optionalDependencyResultLabel(row.key)).join(", "),
    }));
  }
  if (failed.length) {
    details.push(aioFormat("info.optionalDependency.error", {
      items: failed.map((row) => optionalDependencyResultLabel(row.key)).join(", "),
    }));
  }

  const signature = rows.map((row) => `${row.key}:${row.status}:${row.error}`).join("|");
  if (signature === generatorOptionalDependencyState.reportedSignature) {
    return;
  }
  generatorOptionalDependencyState.reportedSignature = signature;
  const summary = aioText("info.optionalDependency.title");
  const detail = details.join(" ");
  const toast = app?.extensionManager?.toast;
  if (typeof toast?.add === "function") {
    toast.add({
      severity: failed.length ? "warn" : "info",
      summary,
      detail,
      life: failed.length || missing.length ? 10000 : 5000,
    });
  } else if (typeof app?.ui?.dialog?.show === "function") {
    app.ui.dialog.show(`${summary}\n${detail}`);
  }
}

function loadGeneratorOptionalDependencies({ retryErrors = false } = {}) {
  const hasQueryErrors = Object.values(generatorOptionalDependencyState.status).includes("error");
  if (generatorOptionalDependencyState.loaded && (!retryErrors || !hasQueryErrors)) {
    return Promise.resolve(generatorOptionalDependencyState);
  }
  if (!generatorOptionalDependencyState.loading) {
    generatorOptionalDependencyState.loading = fetchGeneratorOptionalDependencies()
      .catch((error) => {
        console.warn("[EasyUseAnima] Failed to load optional dependency status.", error);
        const message = error instanceof Error ? error.message : String(error || "Unknown error");
        generatorOptionalDependencyState.status = Object.fromEntries(
          Object.keys(AIO_OPTIONAL_DEPENDENCY_SPECS).map((key) => [key, "error"]),
        );
        generatorOptionalDependencyState.errors = Object.fromEntries(
          Object.keys(AIO_OPTIONAL_DEPENDENCY_SPECS).map((key) => [key, message]),
        );
      })
      .then(() => {
        generatorOptionalDependencyState.loaded = true;
        reportGeneratorOptionalDependencyStatus();
        return generatorOptionalDependencyState;
      })
      .finally(() => {
        generatorOptionalDependencyState.loading = null;
      });
  }
  return generatorOptionalDependencyState.loading;
}

function optionalDependencyStatus(key) {
  return aioOptionalDependencyStatus(generatorOptionalDependencyState, key);
}

function optionalDependencyAvailable(key) {
  return aioOptionalDependencyAvailable(generatorOptionalDependencyState, key);
}

function optionalDependencyPack(key) {
  return aioOptionalDependencyPack(key);
}

function upscaleBackendMissingPacks(backend) {
  return aioUpscaleBackendMissingPacks(generatorOptionalDependencyState, backend);
}

function nodeInputMap(dependencyKey) {
  return aioNodeInputMap(generatorOptionalDependencyState, dependencyKey);
}

function nodeInputSpec(dependencyKey, inputName) {
  return aioNodeInputSpec(generatorOptionalDependencyState, dependencyKey, inputName);
}

function nodeInputTooltip(dependencyKey, inputName) {
  return aioNodeInputTooltip(generatorOptionalDependencyState, dependencyKey, inputName);
}

function nodeInputChoiceOptions(dependencyKey, inputName, current, fallback = []) {
  const values = choiceSpecValues(nodeInputSpec(dependencyKey, inputName));
  return optionsWithCurrent(values.length ? values : fallback, current);
}

function nodeInputSupported(dependencyKey, inputName) {
  return aioNodeInputSupported(generatorOptionalDependencyState, dependencyKey, inputName);
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
  const next = migrateGeneratorPostprocessSettings(mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings));
  delete next.sampler.dave;
  const backendDependency = AIO_BACKEND_DEPENDENCIES[next.sampler.backend];
  if (backendDependency && !optionalDependencyAvailable(backendDependency)) {
    next.sampler.backend = "comfy_ksampler";
  }
  delete next.highres?.backend;
  if (!optionalDependencyAvailable("spectrumPatch")) {
    disableGeneratorSpectrumOptions(next.sampler);
    disableGeneratorSpectrumOptions(next.highres);
    disableGeneratorSpectrumOptions(next.upscale);
    for (const targetName of normalizeDetailerOrder(next.detailer?.order, next.detailer)) {
      disableGeneratorSpectrumOptions(next.detailer?.[targetName]);
    }
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
  if (!optionalDependencyAvailable("safePag")) {
    next.model_patches.safe_pag.enabled = false;
  }
  if (!optionalDependencyAvailable("imageSaver") && next.save.backend === "image_saver") {
    next.save.backend = "comfy_save_image";
  }
  const impactMissing = !optionalDependencyAvailable("impactDetailer")
    || !optionalDependencyAvailable("impactMaskToSegs");
  if (impactMissing) {
    next.detailer.enabled = false;
    for (const targetName of normalizeDetailerOrder(next.detailer?.order, next.detailer)) {
      if (next.detailer[targetName]) {
        next.detailer[targetName].enabled = false;
      }
    }
  }
  if (next.upscale?.enabled && upscaleBackendMissingPacks(next.upscale.backend).length) {
    next.upscale.enabled = false;
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
  for (const node of aioListAttachedGeneratorNodes(app.graph, isGeneratorGraphNode)) {
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

function parseSettings(widget, defaults) {
  if (!widget) {
    return clone(defaults);
  }
  return aioParseSettingsValue(widget.value, defaults);
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
    .easyuse-anima-aio-field.checkbox {
      grid-template-columns: minmax(0, 1fr);
      justify-items: start;
    }
    .easyuse-anima-aio-field.checkbox label {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
      line-height: 1.35;
      cursor: pointer;
    }
    .easyuse-anima-aio-field.checkbox input[type="checkbox"] {
      width: 16px;
      height: 16px;
      flex: 0 0 auto;
      margin: 0;
      padding: 0;
    }
    .easyuse-anima-aio-field.easyuse-anima-aio-unsupported {
      opacity: 0.48;
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
    .easyuse-anima-aio-profile-manager-actions button,
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
    .easyuse-anima-aio-profile-manager-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 12px;
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
      flex: 1 1 0%;
      contain: size;
      overflow: hidden;
      user-select: none;
    }
    .easyuse-anima-aio-node-panel * {
      box-sizing: border-box;
    }
    @keyframes easyuse-anima-aio-spin {
      to {
        transform: rotate(360deg);
      }
    }
    .easyuse-anima-aio-node-profile-button {
      max-width: 76px;
      min-width: 44px;
      flex: 0 1 auto;
      overflow: hidden;
      padding-left: 7px;
      padding-right: 7px;
      text-overflow: ellipsis;
    }
    .easyuse-anima-aio-node-main {
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
      gap: 8px;
      flex: 1 1 0%;
      min-width: 0;
      min-height: 0;
      overflow: hidden;
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
      overflow: hidden;
    }
    .easyuse-anima-aio-node-settings-scroll {
      flex: 1 1 0%;
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      overscroll-behavior: contain;
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
    .easyuse-anima-aio-node-field.checkbox label {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      width: auto;
      margin: 0;
      cursor: pointer;
    }
    .easyuse-anima-aio-node-field.checkbox label span {
      min-width: 0;
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
      min-height: 0;
      overflow: hidden;
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
    .easyuse-anima-aio-node-preview-box {
      position: relative;
      flex: 1 1 0%;
      height: auto;
      min-height: 0;
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
    .easyuse-anima-aio-node-denoise-preview {
      position: relative;
      width: 100%;
      height: 100%;
      background: #10151a;
    }
    .easyuse-anima-aio-node-denoise-preview img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: contain;
      background: #10151a;
    }
    .easyuse-anima-aio-node-denoise-preview-label {
      position: absolute;
      left: 8px;
      bottom: 8px;
      max-width: calc(100% - 16px);
      padding: 3px 7px;
      overflow: hidden;
      color: #f4efe5;
      background: rgba(8, 12, 16, 0.78);
      border: 1px solid rgba(255, 255, 255, 0.13);
      border-radius: 4px;
      font-size: 10px;
      line-height: 1.25;
      text-overflow: ellipsis;
      white-space: nowrap;
      pointer-events: none;
    }
    .${GENERATOR_VUE_NODE_CLASS} img.pointer-events-none.object-contain.contain-size,
    .${GENERATOR_VUE_NODE_CLASS} img.pointer-events-none.object-contain + .text-node-component-header-text,
    .${GENERATOR_VUE_NODE_CLASS} .text-node-component-header-text,
    .${GENERATOR_VUE_NODE_CLASS} .text-node-component-header-text.mt-1.text-center.text-xs,
    .lg-node:has(.easyuse-anima-aio-node-panel) .text-node-component-header-text,
    .lg-node:has(.easyuse-anima-aio-node-panel) .pt-2.text-center.text-xs.text-base-foreground,
    [data-node-id]:has(.easyuse-anima-aio-node-panel) .text-node-component-header-text,
    [data-node-id]:has(.easyuse-anima-aio-node-panel) .pt-2.text-center.text-xs.text-base-foreground,
    .${GENERATOR_VUE_NODE_CLASS} [data-testid="main-image"],
    .${GENERATOR_VUE_NODE_CLASS} .easyuse-anima-aio-native-live-preview-hidden {
      display: none !important;
    }
    .${GENERATOR_VUE_NODE_CLASS} .lg-node-content,
    .${GENERATOR_VUE_NODE_CLASS}.lg-node .lg-node-content {
      display: none !important;
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
    .easyuse-anima-aio-node-preview-compare-labels {
      position: absolute;
      inset: 6px 6px auto 6px;
      z-index: 2;
      display: flex;
      justify-content: space-between;
      gap: 8px;
      pointer-events: none;
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
      max-width: min(44%, 260px);
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
    .easyuse-anima-aio-node-preview-pane-label.previous {
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
    .easyuse-anima-aio-node-preview-thumb.pending {
      display: flex;
      align-items: center;
      justify-content: center;
      background:
        linear-gradient(135deg, rgba(135, 200, 235, 0.08), rgba(255, 255, 255, 0.02)),
        #11161b;
      border-style: dashed;
      cursor: default;
    }
    .easyuse-anima-aio-node-preview-thumb.pending::before {
      content: "";
      width: 18px;
      height: 18px;
      border: 2px solid rgba(174, 187, 192, 0.38);
      border-top-color: rgba(135, 200, 235, 0.88);
      border-radius: 50%;
      animation: easyuse-anima-aio-spin 0.9s linear infinite;
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

const {
  createDialog,
  createNodeField,
  field,
} = aioCreateDialogPrimitives({
  document,
  ensureStyle,
  staticText: aioStaticText,
  text: aioText,
  resolveFieldPresentation: aioFieldPresentation,
  applyTooltip,
  applyTooltipText,
});

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

function firstValue(value, fallback = "") {
  if (Array.isArray(value)) {
    return value.length > 0 ? value[0] : fallback;
  }
  return value ?? fallback;
}

const {
  remember: rememberGeneratorProgress,
  rememberState: rememberGeneratorProgressState,
  find: generatorProgressForPreviewDetail,
  clear: clearGeneratorPreviewProgress,
} = aioCreatePreviewProgressTracker();


function clearGeneratorDenoisePreview(node, update = false) {
  const preview = node?.__easyuseAnimaGeneratorDenoisePreview;
  if (
    preview?.url
    && typeof URL !== "undefined"
    && typeof URL.revokeObjectURL === "function"
  ) {
    URL.revokeObjectURL(preview.url);
  }
  if (node) {
    delete node.__easyuseAnimaGeneratorDenoisePreview;
  }
  if (update && node?.__easyuseAnimaGeneratorPanelEl) {
    updateGeneratorDomSummary(node);
    scheduleGeneratorLayout(node);
  }
}

function setGeneratorDenoisePreview(node, blob, detail = {}) {
  if (
    !node
    || !blob
    || typeof URL === "undefined"
    || typeof URL.createObjectURL !== "function"
  ) {
    return;
  }
  const progress = generatorProgressForPreviewDetail(detail);
  clearGeneratorDenoisePreview(node);
  node.__easyuseAnimaGeneratorDenoisePreview = {
    url: URL.createObjectURL(blob),
    value: progress?.value ?? null,
    max: progress?.max ?? null,
  };
  updateGeneratorDomSummary(node);
  scheduleGeneratorLayout(node);
  markNodeDirty(node);
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

function isSpecialSeed(value) {
  return GENERATOR_SPECIAL_SEEDS.includes(Number(value));
}

function clampGeneratorNumber(value, fallback, min, max) {
  const parsed = Number(value);
  const next = Number.isFinite(parsed) ? parsed : fallback;
  return Math.max(min, Math.min(max, next));
}

function normalizeGeneratorUsduAutoTileRange(usdu) {
  const defaults = DEFAULT_GENERATION_SETTINGS.upscale.usdu;
  const target = Math.trunc(clampGeneratorNumber(usdu.auto_tile_target, defaults.auto_tile_target, 64, 16384));
  let min = Math.trunc(clampGeneratorNumber(usdu.auto_tile_min, defaults.auto_tile_min, 64, 16384));
  let max = Math.trunc(clampGeneratorNumber(usdu.auto_tile_max, defaults.auto_tile_max, 64, 16384));
  max = Math.max(min, max);
  if (target < min) {
    min = target;
  }
  if (target > max) {
    max = target;
  }
  usdu.auto_tile_target = target;
  usdu.auto_tile_min = min;
  usdu.auto_tile_max = Math.max(min, max);
  return usdu;
}

function setGeneratorUsduAutoTileTarget(settings, value) {
  settings.upscale ||= {};
  settings.upscale.usdu ||= {};
  settings.upscale.usdu.auto_tile_target = Math.trunc(clampGeneratorNumber(value, 1024, 64, 16384));
  normalizeGeneratorUsduAutoTileRange(settings.upscale.usdu);
}

function isDetailerTargetName(name) {
  return name === "face" || name === "eye" || /^custom_\d+$/.test(name);
}

function isCustomDetailerTargetName(name) {
  return /^custom_\d+$/.test(String(name || ""));
}

function detailerTargetDefaults(targetName) {
  const defaults = targetName === "eye"
    ? DEFAULT_GENERATION_SETTINGS.detailer.eye
    : DEFAULT_GENERATION_SETTINGS.detailer.face;
  const output = clone(defaults);
  if (isCustomDetailerTargetName(targetName)) {
    const suffix = String(targetName).split("_").pop();
    output.label = `Detailer Block ${suffix}`;
  }
  return output;
}

function detailerTargetTitle(targetName, target, index = 0) {
  if (target?.label) {
    return String(target.label);
  }
  if (targetName === "face") {
    return aioText("label.face");
  }
  if (targetName === "eye") {
    return aioText("label.eye");
  }
  const suffix = String(targetName || "").split("_").pop();
  return `Detailer Block ${suffix || index + 1}`;
}

function normalizeDetailerOrder(order, detailer = null) {
  const output = [];
  const appendTarget = (name) => {
    const normalized = String(name || "").trim();
    if (isDetailerTargetName(normalized) && !output.includes(normalized)) {
      output.push(normalized);
    }
  };
  for (const name of Array.isArray(order) ? order : DEFAULT_GENERATION_SETTINGS.detailer.order) {
    appendTarget(name);
  }
  if (detailer && typeof detailer === "object") {
    for (const [name, value] of Object.entries(detailer)) {
      if (["enabled", "order", "sam3"].includes(name) || !value || typeof value !== "object" || Array.isArray(value)) {
        continue;
      }
      appendTarget(name);
    }
  }
  for (const name of DEFAULT_GENERATION_SETTINGS.detailer.order) {
    appendTarget(name);
  }
  return output;
}

function nextDetailerTargetName(order, detailer = null) {
  const used = new Set(normalizeDetailerOrder(order, detailer));
  if (detailer && typeof detailer === "object") {
    for (const key of Object.keys(detailer)) {
      used.add(key);
    }
  }
  for (let index = 1; index < 1000; index += 1) {
    const candidate = `custom_${index}`;
    if (!used.has(candidate)) {
      return candidate;
    }
  }
  return `custom_${Date.now()}`;
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
  const next = migrateGeneratorPostprocessSettings(mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings));
  const inputs = normalizeGeneratorInputValues(node, next);
  next.sampler.seed = inputs.seed;
  next.sampler.seed_after_generate = normalizeSeedControl(next.sampler.seed_after_generate);
  next.sampler.steps = inputs.steps;
  next.sampler.cfg = inputs.cfg;
  next.sampler.sampler_name = inputs.sampler_name;
  next.sampler.scheduler = inputs.scheduler;
  next.sampler.denoise = inputs.denoise;
  delete next.sampler.dave;
  delete next.highres?.backend;
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

function commitGeneratorSeedValue(node, seed) {
  const seedWidget = findWidget(node, "seed");
  const settingsWidget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
  const settings = generatorSettings(node);
  settings.sampler.seed = seed;
  const serializedSettings = JSON.stringify(settings);

  if (seedWidget) {
    seedWidget.value = seed;
  }
  node.__easyuseAnimaGeneratorUiValues ||= {};
  node.__easyuseAnimaGeneratorUiValues.seed = seed;
  if (settingsWidget) {
    settingsWidget.value = serializedSettings;
  }
  try {
    seedWidget?.callback?.(seed);
  } catch {
    // Widget callbacks are notifications after the durable state write.
  }
  try {
    settingsWidget?.callback?.(serializedSettings);
  } catch {
    // Hidden-widget callbacks are also best-effort notifications.
  }
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


function dispatchGeneratorCanvasWheelEvent(sourceEvent) {
  const canvas = app?.canvas?.canvas;
  if (!canvas) {
    return;
  }
  const event = new WheelEvent("wheel", {
    bubbles: true,
    cancelable: true,
    view: window,
    deltaX: sourceEvent.deltaX,
    deltaY: sourceEvent.deltaY,
    deltaZ: sourceEvent.deltaZ,
    deltaMode: sourceEvent.deltaMode,
    clientX: sourceEvent.clientX,
    clientY: sourceEvent.clientY,
    screenX: sourceEvent.screenX,
    screenY: sourceEvent.screenY,
    ctrlKey: sourceEvent.ctrlKey,
    shiftKey: sourceEvent.shiftKey,
    altKey: sourceEvent.altKey,
    metaKey: sourceEvent.metaKey,
  });
  Object.defineProperty(event, "__easyuseAnimaForwarded", { value: true });
  canvas.dispatchEvent(event);
}

function forwardGeneratorPanelWheel(event) {
  if (event.__easyuseAnimaForwarded) {
    return false;
  }
  const panel = aioPanelFromWheelEvent(event);
  if (!panel) {
    return false;
  }
  if (consumeAioPanelWheel(event, panel)) {
    return true;
  }
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation?.();
  dispatchGeneratorCanvasWheelEvent(event);
  return true;
}

function installGeneratorWheelForwarder() {
  if (window.__easyuseAnimaAioWheelForwarderInstalled) {
    return;
  }
  window.__easyuseAnimaAioWheelForwarderInstalled = true;
  // Node 2.0 handles wheel on an ancestor of the DOM widget, so ownership must
  // be decided during window capture before that ancestor can zoom the canvas.
  window.addEventListener("wheel", forwardGeneratorPanelWheel, {
    capture: true,
    passive: false,
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

function activateGeneratorPanel(node) {
  return generatorPanelRuntime.activatePanel(node);
}

function disposeGeneratorPanel(node) {
  return generatorPanelRuntime.disposePanel(node);
}

function renderGeneratorPanel(node, expectedLifecycle = null) {
  return generatorPanelRuntime.renderPanel(node, expectedLifecycle);
}

function ensureGeneratorPanel(node) {
  return generatorPanelRuntime.ensurePanel(node);
}

function updateGeneratorDomSummary(node) {
  return generatorPanelRuntime.updateSummary(node);
}

function scheduleGeneratorLayout(node) {
  return generatorPanelRuntime.scheduleLayout(node);
}

function scheduleGeneratorSummary(node) {
  return generatorPanelRuntime.scheduleSummary(node);
}

function refreshGeneratorSeedButtons(node) {
  return generatorPanelRuntime.refreshSeedButtons(node);
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

function installGeneratorQueuePromptHook() {
  return aioInstallGeneratorQueuePromptHook(api, generatorQueueRuntime);
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

const generatorProfileApi = createAioProfileApiClient({
  fetchJson: (url, options) => easyuseAnimaFetchComfyJson(api, url, options),
  encodeURIComponent,
});

const generatorProfileRuntime = aioCreateProfileSettingsRuntime({
  document,
  createDialog,
  field,
  text: aioText,
  format: aioFormat,
  dialogs: {
    prompt: (message, defaultValue) => window.prompt(message, defaultValue),
    alert: (message) => window.alert(message),
    confirm: (message) => window.confirm(message),
  },
  profileApi: generatorProfileApi,
  profileCore: {
    customValue: GENERATOR_PROFILE_CUSTOM_VALUE,
    builtinIds: aioBuiltinProfileIds,
    builtinSettings: aioBuiltinProfileSettings,
    fingerprint: aioProfileSettingsFingerprint,
    userValue: aioUserProfileValue,
    userName: aioUserProfileName,
    findUser: aioFindUserProfileByName,
    resolveValue: aioResolvedProfileValue,
  },
  settingsCore: {
    defaultSettings: DEFAULT_GENERATION_SETTINGS,
    mergeDefaults,
    migratePostprocess: migrateGeneratorPostprocessSettings,
  },
  nodeAdapter: {
    getSettings: generatorSettings,
    applyVisibleSettings: applyVisibleGeneratorSettings,
    writeSettings: writeGeneratorSettingsFromState,
    renderPanel: renderGeneratorPanel,
    refreshPanels: refreshGeneratorPanels,
    markDirty: markNodeDirty,
  },
});

const {
  loadProfiles: loadGeneratorUserProfiles,
  syncValue: syncGeneratorProfileValue,
  displayLabel: generatorProfileDisplayLabel,
  open: openGeneratorProfileSettings,
} = generatorProfileRuntime;

const openInputSettings = aioCreateInputSettingsDialog({
  document,
  createDialog,
  field,
  selectInput,
  staticText: aioStaticText,
  text: aioText,
  defaultInputSettings: DEFAULT_INPUT_SETTINGS,
  inputSettingsWidget: INPUT_SETTINGS_WIDGET,
  findWidget,
  parseSettings,
  mergeDefaults,
  writeSettings,
});

const openPostprocessSettings = aioCreatePostprocessSettingsDialog({
  document,
  createDialog,
  field,
  checkbox,
  selectInput,
  numberInput,
  staticText: aioStaticText,
  text: aioText,
  defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
  generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
  findWidget,
  generatorSettings,
  mergeDefaults,
  clampNumber: clampGeneratorNumber,
  writeSettings,
  renderGeneratorPanel,
});

const openPreviewSettings = aioCreatePreviewSettingsDialog({
  document,
  createDialog,
  field,
  checkbox,
  numberInput,
  staticText: aioStaticText,
  text: aioText,
  defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
  generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
  findWidget,
  generatorSettings,
  mergeDefaults,
  clampNumber: clampGeneratorNumber,
  defaultPreviewIndex: aioDefaultPreviewIndex,
  applyVisibleSettings: applyVisibleGeneratorSettings,
  writeSettings,
  renderGeneratorPanel,
});

const {
  createStageOptimizationEditor,
  openHighresSettings,
  openUpscaleSettings,
} = aioCreateStageSettingsDialogs({
  document,
  controls: {
    createDialog,
    field,
    numberInput,
    checkbox,
    selectInput,
  },
  text: {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
  },
  settingsCore: {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,
    fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,
    mergeDefaults,
    clampNumber: clampGeneratorNumber,
    normalizeUsduAutoTileRange: normalizeGeneratorUsduAutoTileRange,
  },
  nodeAdapter: {
    generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
    findWidget,
    getSettings: generatorSettings,
    widgetOptions,
    nodeInputChoiceOptions,
    writeSettings,
    renderPanel: renderGeneratorPanel,
  },
  dependencyAdapter: {
    available: optionalDependencyAvailable,
    pack: optionalDependencyPack,
    upscaleBackendMissingPacks,
    load: loadGeneratorOptionalDependencies,
  },
});

const openDetailerSettings = aioCreateDetailerSettingsDialog({
  document,
  controls: {
    createDialog,
    field,
    checkbox,
    textInput,
    numberInput,
    selectInput,
  },
  text: {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
    applyTooltip,
  },
  settingsCore: {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,
    fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,
    mergeDefaults,
    clampNumber: clampGeneratorNumber,
    normalizeDetailerOrder,
    isCustomDetailerTargetName,
    nextDetailerTargetName,
    detailerTargetDefaults,
    detailerTargetTitle,
  },
  stageOptimizationEditor: createStageOptimizationEditor,
  nodeAdapter: {
    generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
    findWidget,
    getSettings: generatorSettings,
    widgetOptions,
    writeSettings,
    renderPanel: renderGeneratorPanel,
  },
  dependencyAdapter: {
    available: optionalDependencyAvailable,
    pack: optionalDependencyPack,
    load: loadGeneratorOptionalDependencies,
  },
});

const openSamplerSettings = aioCreateSamplerSettingsDialog({
  document,
  controls: {
    createDialog,
    field,
    numberInput,
    selectInput,
    checkbox,
    textInput,
    nodeInputControlForSpec,
    valueFromNodeInputControl,
  },
  text: {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
    applyTooltipText,
  },
  settingsCore: {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    seedControls: GENERATOR_SEED_CONTROLS,
    specialSeedRandom: GENERATOR_SPECIAL_SEED_RANDOM,
    fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,
    fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,
    mergeDefaults,
    normalizeSeedControl,
    normalizeSeedValue,
    clampNumber: clampGeneratorNumber,
  },
  nodeAdapter: {
    generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
    findWidget,
    parseSettings,
    mergeVisibleSettings: mergeVisibleGeneratorSettings,
    widgetOptions,
    applyVisibleSettings: applyVisibleGeneratorSettings,
    writeSettings,
    renderPanel: renderGeneratorPanel,
  },
  dependencyAdapter: {
    backendDependencies: AIO_BACKEND_DEPENDENCIES,
    isLoaded: () => generatorOptionalDependencyState.loaded,
    available: optionalDependencyAvailable,
    pack: optionalDependencyPack,
    nodeInputMap,
    nodeInputTooltip,
    nodeInputSupported,
    load: loadGeneratorOptionalDependencies,
  },
});

const openSaveSettings = aioCreateSaveSettingsDialog({
  document,
  controls: {
    createDialog,
    field,
    checkbox,
    selectInput,
    textInput,
    numberInput,
    textareaInput,
  },
  text: {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
    applyTooltip,
    applyTooltipText,
  },
  settingsCore: {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    asBool,
    mergeDefaults,
  },
  nodeAdapter: {
    generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
    findWidget,
    getSettings: generatorSettings,
    applyVisibleSettings: applyVisibleGeneratorSettings,
    writeSettings,
    renderPanel: renderGeneratorPanel,
  },
  dependencyAdapter: {
    available: optionalDependencyAvailable,
    pack: optionalDependencyPack,
    load: loadGeneratorOptionalDependencies,
  },
});

const openAdvancedSettings = aioCreateAdvancedSettingsDialog({
  document,
  controls: {
    createDialog,
    field,
    numberInput,
    checkbox,
    textInput,
    selectInput,
  },
  text: {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
  },
  settingsCore: {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    mergeDefaults,
    clampNumber: clampGeneratorNumber,
  },
  nodeAdapter: {
    generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
    findWidget,
    getSettings: generatorSettings,
    writeSettings,
    renderPanel: renderGeneratorPanel,
  },
  dependencyAdapter: {
    available: optionalDependencyAvailable,
    pack: optionalDependencyPack,
    load: loadGeneratorOptionalDependencies,
  },
});

const {
  activateGeneratorNativePreviewLifecycle,
  disposeGeneratorNativePreviewLifecycle,
  markGeneratorNativeLivePreviewHidden,
  suppressGeneratorDefaultPreview,
  scheduleGeneratorDefaultPreviewSuppression,
  handleGeneratorPreviewEvent,
  handleGeneratorProgressEvent,
  handleGeneratorProgressStateEvent,
  handleGeneratorDenoisePreviewEvent,
  handleGeneratorExecutingEvent,
  clearGeneratorDenoisePreviews,
} = aioCreateNativePreviewRuntime({
  environment: {
    document,
    window,
    MutationObserver: globalThis.MutationObserver,
    requestAnimationFrame: (callback) => requestAnimationFrame(callback),
    cancelAnimationFrame: (frame) => cancelAnimationFrame(frame),
    setTimeout: (callback, delay) => setTimeout(callback, delay),
    clearTimeout: (timer) => clearTimeout(timer),
  },
  constants: {
    generatorNodeType: GENERATOR_NODE_TYPE,
    generatorVueNodeClass: GENERATOR_VUE_NODE_CLASS,
  },
  storeAdapter: {
    getLegacyPreviewImages: () => app.nodePreviewImages,
    loadDirectStoreModules: () => Promise.all([
      import("../../../stores/nodeOutputStore.js").catch(() => null),
      import("../../../platform/workflow/management/stores/workflowStore.js").catch(() => null),
    ]),
    fetchFrontendHtml: () => easyuseAnimaFetchText("/"),
    importAssetModule: (url) => import(url),
  },
  previewCore: {
    deleteStoreEntry: aioDeletePreviewStoreEntry,
    eventDetail: aioPreviewEventDetail,
    images: aioPreviewImages,
    nodeIdsFromDetail: aioPreviewNodeIdsFromDetail,
    suppressDefaultPreview: aioSuppressDefaultPreview,
  },
  nodeAdapter: {
    getGraph: () => app.graph,
    listGeneratorNodes: generatorGraphNodes,
    addPreviewImages: addGeneratorPreviewImagesToNode,
    clearDenoisePreview: clearGeneratorDenoisePreview,
    setDenoisePreview: setGeneratorDenoisePreview,
    markDirty: markNodeDirty,
  },
  progressAdapter: {
    remember: rememberGeneratorProgress,
    rememberState: rememberGeneratorProgressState,
    clear: clearGeneratorPreviewProgress,
  },
});

const generatorPanelRuntime = aioCreateGeneratorPanelRuntime({
  document,
  window,
  requestAnimationFrame: (callback) => requestAnimationFrame(callback),
  cancelAnimationFrame: (frame) => cancelAnimationFrame(frame),
  panelMinHeight: GENERATOR_PANEL_MIN_HEIGHT,
  controls: {
    numberInput,
    checkbox,
    selectInput,
    createNodeField,
  },
  text: {
    get: aioText,
    format: aioFormat,
    applyTooltip,
  },
  settingsCore: {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    specialSeedRandom: GENERATOR_SPECIAL_SEED_RANDOM,
    fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,
    fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,
    mergeDefaults,
    normalizeSeedControl,
    normalizeSeedValue,
    clampNumber: clampGeneratorNumber,
    normalizeUsduAutoTileRange: normalizeGeneratorUsduAutoTileRange,
    setUsduAutoTileTarget: setGeneratorUsduAutoTileTarget,
    normalizeDetailerOrder,
    detailerTargetDefaults,
    detailerTargetTitle,
  },
  nodeAdapter: {
    getSettings: generatorSettings,
    applyVisibleSettings: applyVisibleGeneratorSettings,
    writeSettings: writeGeneratorSettingsFromState,
    syncSettingsFromVisible: syncGeneratorSettingsFromVisible,
    widgetValue,
    widgetOptions,
    setWidgetValueIfChanged,
    commitSeedValue: commitGeneratorSeedValue,
    markDirty: markNodeDirty,
    ensureStyle,
    suppressDefaultPreview: suppressGeneratorDefaultPreview,
    markNativePreviewHidden: markGeneratorNativeLivePreviewHidden,
    imageUrl: generatorImageUrl,
    randomSeed,
    forwardPanelWheel: forwardGeneratorPanelWheel,
  },
  profileAdapter: {
    syncValue: syncGeneratorProfileValue,
    displayLabel: generatorProfileDisplayLabel,
  },
  previewAdapter: {
    mainImage: aioMainPreviewImage,
    selectedIndex: aioSelectedPreviewIndex,
    imageLabel: aioPreviewImageLabel,
    imageName: aioPreviewImageName,
    imageResolution: aioPreviewResolution,
    imageFileSize: aioPreviewFileSize,
  },
  actions: {
    openProfileSettings: openGeneratorProfileSettings,
    openSaveSettings,
    openSamplerSettings,
    openAdvancedSettings,
    openHighresSettings,
    openDetailerSettings,
    openUpscaleSettings,
    openPostprocessSettings,
    openPreviewSettings,
  },
});

const generatorQueueRuntime = aioCreateGeneratorQueueRuntime({
  constants: {
    settingsWidgetName: GENERATOR_SETTINGS_WIDGET,
    minSeed: 0,
    maxSeed: GENERATOR_MAX_SEED,
    specialSeedRandom: GENERATOR_SPECIAL_SEED_RANDOM,
    specialSeedIncrement: GENERATOR_SPECIAL_SEED_INCREMENT,
    specialSeedDecrement: GENERATOR_SPECIAL_SEED_DECREMENT,
  },
  settingsCore: {
    normalizeSeedValue,
    normalizeSeedControl,
    cloneJson: clone,
    settingsToCompactJson,
  },
  nodeAdapter: {
    listNodes: generatorGraphNodes,
    isBypassed: (node) => node.mode === 4 || node.mode === globalThis.LiteGraph?.NEVER,
    getSettings: generatorSettings,
    sanitizeSettings: sanitizeGeneratorSettingsForOptionalDependencies,
    getLastQueuedSeed: (node) => node.__easyuseAnimaLastQueuedSeed,
    commitLastQueuedSeed: (node, seed) => {
      node.__easyuseAnimaLastQueuedSeed = seed;
    },
    updateSeed: (node, seed, options) => generatorPanelRuntime.updateSeed(node, seed, options),
  },
  queueAdapter: {
    loadOptionalDependencies: loadGeneratorOptionalDependencies,
  },
  randomSeed,
});

function hookInputNode(node) {
  node.serialize_widgets = true;
  hideWidget(findWidget(node, INPUT_SETTINGS_WIDGET));
  ensureButton(node, "easyuse_anima_input_settings", "Settings...", () => openInputSettings(node));
}

function hookGeneratorNode(node) {
  activateGeneratorPanel(node);
  activateGeneratorNativePreviewLifecycle(node);
  node.serialize_widgets = true;
  suppressGeneratorDefaultPreview(node, { markDirty: false });
  hideWidget(findWidget(node, GENERATOR_SETTINGS_WIDGET));
  ensureGeneratorPanel(node);
  syncGeneratorStateFromDom(node);
  scheduleGeneratorDefaultPreviewSuppression(node);
}

function addGeneratorPreviewImagesToNode(node, nextImages, runId = "", options = {}) {
  if (!node || !Array.isArray(nextImages)) {
    return;
  }
  const replaceCurrentRun = !!options.replaceCurrentRun;
  if (!nextImages.length) {
    if (!replaceCurrentRun) {
      return;
    }
    clearGeneratorDenoisePreview(node);
    const settings = generatorSettings(node);
    const terminalState = aioResolveTerminalPreviewState(
      node.__easyuseAnimaGeneratorPreviewFeedImages,
      settings,
      runId,
    );
    node.__easyuseAnimaGeneratorCurrentRunImages = terminalState.currentRunImages;
    node.__easyuseAnimaGeneratorPreviewFeedImages = terminalState.previewFeedImages;
    node.__easyuseAnimaGeneratorPreviewImages = terminalState.previewImages;
    if (terminalState.selectedIndex >= 0) {
      node.__easyuseAnimaSelectedPreviewIndex = terminalState.selectedIndex;
    } else {
      delete node.__easyuseAnimaSelectedPreviewIndex;
    }
    updateGeneratorDomSummary(node);
    scheduleGeneratorSummary(node);
    scheduleGeneratorLayout(node);
    markNodeDirty(node);
    return;
  }
  clearGeneratorDenoisePreview(node);
  const settings = generatorSettings(node);
  const currentImages = Array.isArray(node.__easyuseAnimaGeneratorCurrentRunImages)
    ? node.__easyuseAnimaGeneratorCurrentRunImages
    : [];
  const currentRunId = String(currentImages[0]?.__aio_run_id || "");
  const currentBase = replaceCurrentRun || (runId && currentRunId && currentRunId !== runId)
    ? []
    : currentImages;
  const taggedNextImages = aioTagPreviewRun(nextImages, runId, currentBase.length);
  node.__easyuseAnimaGeneratorCurrentRunImages = aioMergePreviewImages(currentBase, taggedNextImages, runId);
  if (settings.preview.image_feed) {
    const feedBase = replaceCurrentRun
      ? aioRemovePreviewRun(node.__easyuseAnimaGeneratorPreviewFeedImages, runId)
      : node.__easyuseAnimaGeneratorPreviewFeedImages;
    node.__easyuseAnimaGeneratorPreviewFeedImages = aioAppendPreviewFeed(
      feedBase,
      taggedNextImages,
      settings,
      runId,
      DEFAULT_GENERATION_SETTINGS.preview.feed_count,
    );
    node.__easyuseAnimaGeneratorPreviewImages = node.__easyuseAnimaGeneratorPreviewFeedImages;
  } else {
    node.__easyuseAnimaGeneratorPreviewImages = node.__easyuseAnimaGeneratorCurrentRunImages;
  }
  node.__easyuseAnimaSelectedPreviewIndex = aioDefaultPreviewIndex(node.__easyuseAnimaGeneratorPreviewImages);
  updateGeneratorDomSummary(node);
  scheduleGeneratorSummary(node);
  scheduleGeneratorLayout(node);
  markNodeDirty(node);
}

function updateGeneratorExecutedStatus(node, message) {
  if (!node) {
    return;
  }
  const nextImages = aioPreviewImages(message);
  const runId = aioPreviewRunId(message);
  addGeneratorPreviewImagesToNode(node, nextImages, runId, { replaceCurrentRun: true });
  node.__easyuseAnimaGeneratorStatus = {
    status: String(firstValue(message?.status, "generated") || "generated"),
    width: Number(firstValue(message?.width, 0)),
    height: Number(firstValue(message?.height, 0)),
    unet_name: String(firstValue(message?.unet_name, "")),
    sampler_backend: String(firstValue(message?.sampler_backend, "")),
  };
  updateGeneratorDomSummary(node);
}

const aioExtensionRuntime = aioCreateExtensionRuntime({
  api,
  constants: {
    inputNodeType: INPUT_NODE_TYPE,
    generatorNodeType: GENERATOR_NODE_TYPE,
    generatorPreviewEvent: GENERATOR_PREVIEW_EVENT,
  },
  setup: {
    ensureStyle,
    installWheelForwarder: installGeneratorWheelForwarder,
    installQueuePromptHook: installGeneratorQueuePromptHook,
    watchLocale: easyuseAnimaWatchLocale,
    refreshPanels: refreshGeneratorPanels,
    handlePreviewEvent: handleGeneratorPreviewEvent,
    handleProgressEvent: handleGeneratorProgressEvent,
    handleProgressStateEvent: handleGeneratorProgressStateEvent,
    handleDenoisePreviewEvent: handleGeneratorDenoisePreviewEvent,
    handleExecutingEvent: handleGeneratorExecutingEvent,
    clearDenoisePreviews: clearGeneratorDenoisePreviews,
    loadSamplerOptions: loadGeneratorSamplerOptions,
    loadUserProfiles: loadGeneratorUserProfiles,
    warnUserProfiles(error) {
      console.warn("[EasyUseAnima] Failed to load AiO user profiles.", error);
    },
  },
  nodes: {
    suppressDefaultPreview: suppressGeneratorDefaultPreview,
    hookInputNode,
    hookGeneratorNode,
    syncSerializedWidgets: syncGeneratorSerializedWidgets,
    scheduleDefaultPreviewSuppression: scheduleGeneratorDefaultPreviewSuppression,
    updateExecutedStatus: updateGeneratorExecutedStatus,
    scheduleLayout: scheduleGeneratorLayout,
    disposePanel: disposeGeneratorPanel,
    disposeNativePreviewLifecycle: disposeGeneratorNativePreviewLifecycle,
  },
});

app.registerExtension({
  name: "easyuse-anima.aio",
  ...aioExtensionRuntime,
});
