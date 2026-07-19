// @ts-check

export const REGIONAL_NODE_TYPE = "EasyUseAnimaPromptStudioRegional";
export const REGIONAL_CONDITIONING_NODE_TYPE = "EasyUseAnimaRegionalConditioning";
export const REGIONAL_FIELDS_PROPERTY = "easyuse_anima_regional_fields";
export const REGIONAL_CONFIG_PROPERTY = "easyuse_anima_regional_config";

export const REGIONAL_WIDGET_INDEX = {
  regional_fields: 0,
  regional_config: 1,
  resolution_bucket: 2,
  resolution_size: 3,
  resolution_custom_width: 4,
  resolution_custom_height: 5,
  wildcard_mode: 6,
  wildcard_seed: 7,
  wildcard_seed_after_generate: 8,
};

export const REGIONAL_INTERNAL_WIDGET_NAMES = new Set(Object.keys(REGIONAL_WIDGET_INDEX));
export const REGIONAL_CONDITIONING_AREA_MODES = new Set(["mask bounds", "default"]);

export const PROMPT_STUDIO_VARIANT_FIELD_TYPES = ["quality", "artist", "trigger", "general"];
export const PROMPT_STUDIO_VARIANT_FIELD_LABELS = {
  quality: "Quality Tags",
  artist: "Artist Tags",
  trigger: "Trigger Words",
  general: "General Tags",
};

export const PROMPT_STUDIO_WILDCARD_MODES = ["일반", "순차"];
export const PROMPT_STUDIO_WILDCARD_SEED_CONTROLS = ["fixed", "randomize", "increment", "decrement"];
export const PROMPT_STUDIO_WILDCARD_DEFAULT_MODE = "일반";

export const PROMPT_STUDIO_RESOLUTION_BUCKETS = {
  "512": [
    [256, 1024], [1024, 256],
    [288, 896], [896, 288],
    [384, 672], [672, 384],
    [512, 512],
    [448, 576], [576, 448],
  ],
  "768": [
    [384, 1440], [1440, 384],
    [480, 1152], [1152, 480],
    [576, 960], [960, 576],
    [640, 864], [864, 640],
    [768, 768],
  ],
  "896": [
    [448, 1728], [1728, 448],
    [480, 1600], [1600, 480],
    [576, 1344], [1344, 576],
    [672, 1152], [1152, 672],
    [800, 960], [960, 800],
    [896, 896],
  ],
  "1024": [
    [512, 2016], [2016, 512],
    [576, 1792], [1792, 576],
    [672, 1536], [1536, 672],
    [672, 1600], [1600, 672],
    [768, 1344], [1344, 768],
    [800, 1344], [1344, 800],
    [896, 1152], [1152, 896],
    [960, 1120], [1120, 960],
    [1024, 1024],
  ],
  "1280": [
    [672, 2400], [2400, 672],
    [800, 2016], [2016, 800],
    [1024, 1536], [1536, 1024],
    [1024, 1600], [1600, 1024],
    [1120, 1440], [1440, 1120],
    [1280, 1280],
  ],
  "1536": [
    [1440, 1536], [1536, 1440],
    [1280, 1728], [1728, 1280],
    [1152, 1920], [1920, 1152],
    [1024, 2176], [2176, 1024],
    [960, 2304], [2304, 960],
    [864, 2560], [2560, 864],
    [768, 2880], [2880, 768],
    [1536, 1536],
  ],
};

export const PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET = "Custom";
export const PROMPT_STUDIO_DEFAULT_RESOLUTION_BUCKET = "1024";
export const PROMPT_STUDIO_DEFAULT_RESOLUTION_SIZE = "1024 * 1024 (1:1)";
