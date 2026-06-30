import { app } from "../../../scripts/app.js";
import { easyuseAnimaText, easyuseAnimaWatchLocale } from "./easyuse_anima_i18n.js";
import { normalizePromptTagText } from "./easyuse_anima_prompt_rules.js";

const NODE_TYPE = "EasyUseAnimaPromptStudio";
const ADVANCED_NODE_TYPE = "EasyUseAnimaPromptStudioAdvanced";
const EXTEND_NODE_TYPE = "EasyUseAnimaPromptStudioExtend";
const WILDCARD_NODE_TYPE = "EasyUseAnimaWildcard";
const FIELD_NAMES = [
  "lora_trigger_tags",
  "quality_tags",
  "trigger_and_artist_tags",
  "prompt",
  "trailing_quality_tags",
];
const EXTEND_FIELD_NAMES = [
  "quality_tags_1",
  "quality_tags_2",
  "naia_prompt_3",
  "general_tags_4",
  "general_tags_5",
  "general_tags_6",
  "general_tags_7",
  "general_tags_8",
  "general_tags_9",
  "trailing_tags_10",
  "trailing_tags_11",
  "negative_prompt_1",
  "negative_prompt_2",
  "negative_prompt_3",
  "negative_prompt_4",
];
const EXTEND_VISIBLE_SLOTS_PROPERTY = "easyuse_anima_extend_visible_slots";
const EXTEND_ACTIVE_SLOTS_WIDGET = "active_slots";
const EXTEND_SLOT_GROUPS = [
  { id: "quality", label: "Quality", labelKey: "extend.group.quality", fields: ["quality_tags_1", "quality_tags_2"] },
  { id: "naia", label: "NAIA", labelKey: "extend.group.naia", fields: ["naia_prompt_3"] },
  { id: "general", label: "General", labelKey: "extend.group.general", fields: ["general_tags_4", "general_tags_5", "general_tags_6", "general_tags_7", "general_tags_8", "general_tags_9"] },
  { id: "trailing", label: "Trailing", labelKey: "extend.group.trailing", fields: ["trailing_tags_10", "trailing_tags_11"] },
  { id: "negative", label: "Negative", labelKey: "extend.group.negative", fields: ["negative_prompt_1", "negative_prompt_2", "negative_prompt_3", "negative_prompt_4"] },
];
const EXTEND_DEFAULT_VISIBLE_FIELDS = new Set(["quality_tags_1", "general_tags_4", "trailing_tags_10"]);

const PROMPT_STUDIO_TEXT = {
  en: {
    "section.quality": "Quality",
    "section.safety": "Rating",
    "section.year": "Year",
    "section.count": "Count",
    "section.character": "Character",
    "section.artist": "Artist",
    "section.artist_unknown": "Unregistered artist",
    "section.copyright": "Copyright",
    "section.meta": "Meta",
    "section.general": "Trained tag",
    "section.natural": "Natural language",
    "section.wildcard": "Wildcard",
    "section.syntax": "Syntax error",
    "section.unknown": "Unknown",
    "tag.generic": "tag",
    "tag.learned": "learned",
    "legend.color": "Color legend",
    "extend.group.quality": "Quality",
    "extend.group.naia": "NAIA",
    "extend.group.general": "General",
    "extend.group.trailing": "Trailing",
    "extend.group.negative": "Negative",
    "extend.noHiddenSlots": "No hidden slots left",
    "extend.showSlotTitle": "{name} input slot show",
    "extend.hideSlot": "Hide {slot}",
    "extend.hideSlotTitle": "{name} input slot hide",
    "extend.naiaResult": "NAIA result",
    "extend.naiaResultTitle": "Read-only NAIA result slot. Enable fill_naia_prompt to update it from NAIA.",
    "advanced.fillFromNaia": "Fill from NAIA",
    "advanced.fillFromNaiaTitle": "Keep filling the NAIA Prompt field with a fresh NAIA random prompt while this is enabled.",
    "advanced.fillOnce": "1x",
    "advanced.fillOnceTitle": "Save successful NAIA fills with the request flag turned off.",
    "advanced.modGuidance": "mod guidance",
    "advanced.modGuidanceTitle": "Send positive quality fields to Anima Mod Guidance output.",
    "advanced.negativeModGuidance": "negative mod",
    "advanced.negativeModGuidanceTitle": "Send negative quality fields to Anima Mod Guidance negative output.",
    "advanced.wildcard": "wildcard",
    "advanced.wildcardTitle": "Expand __wildcard__ and dynamic prompt syntax in Advanced Prompt Studio fields.",
    "advanced.wildcardSeed": "wildcard seed",
    "advanced.wildcardSeedControl": "seed control",
    "advanced.pin": "Pin",
    "advanced.pinTitle": "Keep positive artist/trigger fields at the front.",
    "advanced.linkedInputSuffix": "Linked input controls this value.",
    "advanced.resolutionTitle": "Latent image resolution output. Resolutions are sorted by width/height ratio.",
    "advanced.resolutionBucket": "resolution bucket",
    "advanced.resolutionSize": "resolution size",
    "advanced.customWidth": "custom width",
    "advanced.customHeight": "custom height",
    "advanced.naiaResolutionTitle": "Filled from NAIA on queue. Saved image workflows store this as Custom.",
    "advanced.field.quality": "Quality Tags",
    "advanced.field.artist": "Artist Tags",
    "advanced.field.trigger": "Trigger Words",
    "advanced.field.general": "General Tags",
    "advanced.field.naia": "NAIA Prompt",
    "advanced.on": "ON",
    "advanced.off": "OFF",
    "advanced.enableFieldTitle": "Enable or disable this field in prompt output",
    "advanced.autoOrder": "Auto order",
    "advanced.pinned": "Pinned",
    "advanced.autoOrderTitle": "Let prompt correction place trigger words automatically.",
    "advanced.pinnedTitle": "Keep trigger words fixed before corrected prompt text.",
    "advanced.moveUp": "Move up",
    "advanced.moveDown": "Move down",
    "advanced.deleteField": "Delete field",
    "advanced.placeholder.naia": "NAIA result appears here after queue",
    "advanced.placeholder.trigger": "Connect trigger_words STRING input",
    "advanced.placeholder.artist": "@artist_tag",
    "advanced.placeholder.general": "prompt tags",
    "advanced.title.naia": "Editable NAIA result field. Fill from NAIA can overwrite it on the next queue.",
    "advanced.title.trigger": "Editable trigger field. A connected STRING input can overwrite it on the next queue.",
    "advanced.title.linked": "Editable cached value. The connected STRING input can overwrite it on the next queue.",
    "advanced.positivePrompt": "Positive Prompt",
    "advanced.negativePrompt": "Negative Prompt",
    "advanced.add.quality": "+ Quality",
    "advanced.add.artist": "+ Artist",
    "advanced.add.trigger": "+ Trigger",
    "advanced.add.general": "+ General",
    "advanced.add.naia": "+ NAIA",
    "advanced.noFields": "No fields",
  },
  ko: {
    "section.quality": "품질",
    "section.safety": "등급",
    "section.year": "연도",
    "section.count": "인원수",
    "section.character": "캐릭터",
    "section.artist": "작가",
    "section.artist_unknown": "미등록 작가",
    "section.copyright": "작품",
    "section.meta": "메타",
    "section.general": "학습 태그",
    "section.natural": "자연어",
    "section.wildcard": "와일드카드",
    "section.syntax": "문법 오류",
    "section.unknown": "미확인",
    "tag.generic": "태그",
    "tag.learned": "학습됨",
    "legend.color": "색상 범례",
    "extend.group.quality": "품질",
    "extend.group.naia": "NAIA",
    "extend.group.general": "General",
    "extend.group.trailing": "후행",
    "extend.group.negative": "네거티브",
    "extend.noHiddenSlots": "숨겨진 슬롯이 없습니다",
    "extend.showSlotTitle": "{name} 입력 슬롯 표시",
    "extend.hideSlot": "{slot} 숨김",
    "extend.hideSlotTitle": "{name} 입력 슬롯 숨김",
    "extend.naiaResult": "NAIA 결과",
    "extend.naiaResultTitle": "읽기 전용 NAIA 결과 슬롯입니다. fill_naia_prompt를 켜면 NAIA 결과로 갱신됩니다.",
    "advanced.fillFromNaia": "NAIA 채우기",
    "advanced.fillFromNaiaTitle": "켜져 있으면 큐 실행 때마다 NAIA Prompt 필드를 새 NAIA 랜덤 프롬프트로 채웁니다.",
    "advanced.fillOnce": "1회",
    "advanced.fillOnceTitle": "NAIA 채우기에 성공하면 요청 플래그를 끈 상태로 저장합니다.",
    "advanced.modGuidance": "mod guidance",
    "advanced.modGuidanceTitle": "긍정 품질 필드를 Anima Mod Guidance 출력으로 보냅니다.",
    "advanced.negativeModGuidance": "negative mod",
    "advanced.negativeModGuidanceTitle": "부정 품질 필드를 Anima Mod Guidance 네거티브 출력으로 보냅니다.",
    "advanced.wildcard": "와일드카드",
    "advanced.wildcardTitle": "Advanced Prompt Studio 필드의 __wildcard__ 및 동적 프롬프트 문법을 확장합니다.",
    "advanced.wildcardSeed": "와일드카드 시드",
    "advanced.wildcardSeedControl": "시드 제어",
    "advanced.pin": "고정",
    "advanced.pinTitle": "긍정 작가/트리거 필드를 앞쪽에 유지합니다.",
    "advanced.linkedInputSuffix": "연결된 입력이 이 값을 제어합니다.",
    "advanced.resolutionTitle": "Latent 이미지 해상도 출력입니다. 해상도는 가로/세로 비율 순으로 정렬됩니다.",
    "advanced.resolutionBucket": "해상도 버킷",
    "advanced.resolutionSize": "해상도 크기",
    "advanced.customWidth": "사용자 너비",
    "advanced.customHeight": "사용자 높이",
    "advanced.naiaResolutionTitle": "큐 실행 때 NAIA에서 채워졌습니다. 저장된 이미지 워크플로우에는 Custom으로 저장됩니다.",
    "advanced.field.quality": "품질 태그",
    "advanced.field.artist": "작가 태그",
    "advanced.field.trigger": "트리거",
    "advanced.field.general": "일반 태그",
    "advanced.field.naia": "NAIA 프롬프트",
    "advanced.on": "ON",
    "advanced.off": "OFF",
    "advanced.enableFieldTitle": "이 필드를 프롬프트 출력에 포함하거나 제외합니다",
    "advanced.autoOrder": "자동 배치",
    "advanced.pinned": "고정됨",
    "advanced.autoOrderTitle": "프롬프트 교정기가 트리거 위치를 자동으로 배치하게 합니다.",
    "advanced.pinnedTitle": "트리거를 교정된 프롬프트 앞쪽에 고정합니다.",
    "advanced.moveUp": "위로 이동",
    "advanced.moveDown": "아래로 이동",
    "advanced.deleteField": "필드 삭제",
    "advanced.placeholder.naia": "큐 실행 후 NAIA 결과가 표시됩니다",
    "advanced.placeholder.trigger": "trigger_words STRING 입력 연결",
    "advanced.placeholder.artist": "@artist_tag",
    "advanced.placeholder.general": "프롬프트 태그",
    "advanced.title.naia": "편집 가능한 NAIA 결과 필드입니다. 다음 큐 실행에서 NAIA 채우기가 덮어쓸 수 있습니다.",
    "advanced.title.trigger": "편집 가능한 트리거 필드입니다. 연결된 STRING 입력이 다음 큐 실행에서 덮어쓸 수 있습니다.",
    "advanced.title.linked": "편집 가능한 캐시 값입니다. 연결된 STRING 입력이 다음 큐 실행에서 덮어쓸 수 있습니다.",
    "advanced.positivePrompt": "긍정 프롬프트",
    "advanced.negativePrompt": "네거티브 프롬프트",
    "advanced.add.quality": "+ 품질",
    "advanced.add.artist": "+ 작가",
    "advanced.add.trigger": "+ 트리거",
    "advanced.add.general": "+ 일반",
    "advanced.add.naia": "+ NAIA",
    "advanced.noFields": "필드 없음",
  },
};

function psText(key) {
  return easyuseAnimaText(PROMPT_STUDIO_TEXT, key);
}

function psFormat(key, values = {}) {
  return psText(key).replace(/\{(\w+)\}/g, (_match, name) => values[name] ?? "");
}

function sectionLabel(section) {
  const key = String(section || "unknown");
  const style = SECTION_STYLES[key] || SECTION_STYLES.unknown;
  return psText(`section.${key}`) || style?.label || key;
}

const FIELD_HEIGHTS = {
  lora_trigger_tags: 42,
  quality_tags: 72,
  trigger_and_artist_tags: 72,
  prompt: 150,
  trailing_quality_tags: 72,
};
const EXTEND_FIELD_HEIGHTS = {
  quality_tags_1: 72,
  quality_tags_2: 72,
  naia_prompt_3: 150,
  general_tags_4: 120,
  general_tags_5: 120,
  general_tags_6: 120,
  general_tags_7: 120,
  general_tags_8: 120,
  general_tags_9: 120,
  trailing_tags_10: 72,
  trailing_tags_11: 72,
  negative_prompt_1: 120,
  negative_prompt_2: 120,
  negative_prompt_3: 120,
  negative_prompt_4: 120,
};

const SECTION_STYLES = {
  quality: { label: "품질", color: "#facc15", background: "rgba(202, 138, 4, 0.18)", weight: 700 },
  safety: { label: "등급", color: "#38bdf8", background: "rgba(2, 132, 199, 0.18)", weight: 600 },
  year: { label: "연도", color: "#2dd4bf", background: "rgba(13, 148, 136, 0.18)", weight: 600 },
  count: { label: "인원수", color: "#60a5fa", background: "rgba(37, 99, 235, 0.18)", weight: 700 },
  character: { label: "캐릭터", color: "#f472b6", background: "rgba(219, 39, 119, 0.18)", weight: 700 },
  artist: { label: "작가", color: "#a78bfa", background: "rgba(124, 58, 237, 0.18)", weight: 700 },
  artist_unknown: { label: "미등록 작가", color: "#f87171", background: "transparent", underline: true, weight: 400 },
  copyright: { label: "작품", color: "#fb923c", background: "rgba(234, 88, 12, 0.18)", weight: 700 },
  meta: { label: "메타", color: "#94a3b8", background: "rgba(100, 116, 139, 0.18)", weight: 600 },
  general: { label: "학습 태그", color: "#4ade80", background: "rgba(22, 163, 74, 0.16)", weight: 600 },
  natural: { label: "자연어", color: "#cbd5e1", background: "rgba(71, 85, 105, 0.16)", weight: 400 },
  wildcard: { label: "와일드카드", color: "#c084fc", background: "rgba(126, 34, 206, 0.24)", weight: 700 },
  comment: { label: "주석", color: "#9ca3af", background: "rgba(156, 163, 175, 0.14)", weight: 400, italic: true },
  syntax: { label: "문법 오류", color: "#f87171", background: "transparent", underline: true, weight: 400 },
  unknown: { label: "미확인", color: "#cbd5e1", background: "transparent", underline: true, weight: 400 },
};

const LEGEND_ITEMS = [
  "quality",
  "safety",
  "year",
  "count",
  "character",
  "artist",
  "copyright",
  "general",
  "meta",
  "natural",
  "wildcard",
  "comment",
  "syntax",
  "artist_unknown",
  "unknown",
];
const LEGEND_TOP_GAP = 14;
const LEGEND_ROW_HEIGHT = 18;
const LEGEND_COLUMNS = 2;
const STUDIO_WIDGET_VERTICAL_GAP = 8;

const WEIGHTED_TOKEN_RE = /^\((.*):[-+]?\d+(?:\.\d+)?\)$/s;
const WEIGHT_NUMBER_COLOR = "#fb923c";
const WILDCARD_HIGHLIGHT_RE = /(?:\d+#)?__[\w.\-+/*\\]+?__/g;
const INLINE_SPACE_RE = /[ \t]+/g;
const HIGHLIGHT_TEXT_METRIC_PROPERTIES = [
  "font",
  "fontFamily",
  "fontSize",
  "fontSizeAdjust",
  "fontStretch",
  "fontWeight",
  "fontStyle",
  "fontVariant",
  "fontKerning",
  "fontOpticalSizing",
  "fontFeatureSettings",
  "fontVariationSettings",
  "lineHeight",
  "letterSpacing",
  "wordSpacing",
  "textIndent",
  "padding",
  "border",
  "borderRadius",
  "boxSizing",
  "textAlign",
  "textTransform",
  "textRendering",
  "direction",
  "tabSize",
  "whiteSpace",
  "overflowWrap",
  "wordBreak",
];
const PROMPT_STUDIO_SETTINGS = {
  typoIndicator: true,
  commentItalic: true,
  naiaGeneralAboveAutoToggle: false,
};
let middlePanForwardActive = false;
const ADVANCED_CONTROL_WIDGETS = [
  {
    name: "use_naia",
    labelKey: "advanced.fillFromNaia",
    titleKey: "advanced.fillFromNaiaTitle",
    showInControlBar: false,
  },
  {
    name: "consume_naia_on_queue",
    labelKey: "advanced.fillOnce",
    titleKey: "advanced.fillOnceTitle",
    showInControlBar: false,
  },
  {
    name: "use_anima_mod_guidance",
    labelKey: "advanced.modGuidance",
    titleKey: "advanced.modGuidanceTitle",
  },
  {
    name: "use_negative_anima_mod_guidance",
    labelKey: "advanced.negativeModGuidance",
    titleKey: "advanced.negativeModGuidanceTitle",
  },
  {
    name: "pin_trigger_tags_to_front",
    labelKey: "advanced.pin",
    titleKey: "advanced.pinTitle",
    showInControlBar: false,
  },
];
const ADVANCED_WILDCARD_MODES = ["일반 채우기", "고정", "순차", "재현"];
const ADVANCED_WILDCARD_SEED_CONTROLS = ["fixed", "randomize", "increment", "decrement"];
const ADVANCED_WILDCARD_DEFAULT_MODE = "고정";
const ADVANCED_RESOLUTION_BUCKETS = {
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
const CUSTOM_ADVANCED_RESOLUTION_BUCKET = "Custom";
const NAIA_ADVANCED_RESOLUTION_BUCKET = "NAIA";
const DEFAULT_ADVANCED_RESOLUTION_BUCKET = "1024";
const DEFAULT_ADVANCED_RESOLUTION_SIZE = "1024 * 1024 (1:1)";
const ADVANCED_WIDGET_INDEX = {
  use_naia: 0,
  consume_naia_on_queue: 1,
  use_anima_mod_guidance: 2,
  resolution_bucket: 3,
  resolution_size: 4,
  resolution_custom_width: 5,
  resolution_custom_height: 6,
  pin_trigger_tags_to_front: 7,
  advanced_fields: 8,
  use_negative_anima_mod_guidance: 9,
  wildcard_mode: 10,
  wildcard_seed: 11,
  wildcard_seed_after_generate: 12,
};
const ADVANCED_LEGACY_FIELDS_WIDGET_INDEXES = [6, 4];
const ADVANCED_INTERNAL_WIDGET_NAMES = new Set(Object.keys(ADVANCED_WIDGET_INDEX));
const ADVANCED_FIELDS_PROPERTY = "easyuse_anima_advanced_fields";
const ADVANCED_FIELD_SOCKET_PREFIX = "field_";
const ADVANCED_FIELD_TYPES = ["quality", "artist", "trigger", "general", "naia"];
const ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT = 360;
const ADVANCED_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT = 640;
const ADVANCED_FIELD_LABELS = {
  quality: "Quality Tags",
  artist: "Artist Tags",
  trigger: "Trigger Words",
  general: "General Tags",
  naia: "NAIA Prompt",
};
const ADVANCED_DEFAULT_FIELDS = [
  {
    id: "positive_quality",
    pane: "positive",
    type: "quality",
    label: "Quality Tags",
    text: "newest, masterpiece, best quality, score_8, score_7:, highres, absurdres, very aesthetic",
    height: 72,
    enabled: true,
  },
  {
    id: "positive_artist",
    pane: "positive",
    type: "artist",
    label: "Artist Tags",
    text: "",
    height: 72,
    enabled: true,
  },
  {
    id: "positive_trigger",
    pane: "positive",
    type: "trigger",
    label: "Trigger Words",
    text: "",
    height: 72,
    enabled: true,
    pin: true,
  },
  {
    id: "positive_general",
    pane: "positive",
    type: "general",
    label: "General Tags",
    text: "",
    height: 150,
    enabled: true,
  },
  {
    id: "positive_trailing",
    pane: "positive",
    type: "general",
    label: "General Tags",
    text: "location, (A highly aesthetic Pixiv style illustration, clean composition, high-quality digital art, detailed background, sharp focus on facial expressions.:0.6)",
    height: 72,
    enabled: true,
  },
  {
    id: "negative_general",
    pane: "negative",
    type: "general",
    label: "General Tags",
    text: "",
    height: 120,
    enabled: true,
  },
];

function findWidget(node, name) {
  return node.__easyuseAnimaHiddenWidgets?.[name]
    || node.widgets?.find((widget) => widget.name === name);
}

function findInputEl(widget) {
  const input = widget?.inputEl;
  if (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement) {
    return input;
  }
  return null;
}

function firstValue(value, fallback = null) {
  if (Array.isArray(value)) {
    return value.length ? value[0] : fallback;
  }
  return value ?? fallback;
}

function isWidgetInputLinked(node, name) {
  return !!node.inputs?.some((input) => input.widget?.name === name && input.link != null);
}

function ensureHighlightStyle() {
  if (document.getElementById("easyuse-anima-highlight-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-highlight-style";
  style.textContent = `
    .easyuse-anima-highlight-input {
      color: transparent !important;
      -webkit-text-fill-color: transparent !important;
      caret-color: var(--input-text, #ddd) !important;
      background: transparent !important;
      white-space: pre-wrap !important;
      overflow-wrap: break-word !important;
      word-break: normal !important;
      text-size-adjust: 100% !important;
      -webkit-text-size-adjust: 100% !important;
    }
    .easyuse-anima-highlight-input::selection {
      color: transparent !important;
      -webkit-text-fill-color: transparent !important;
      background: rgba(37, 99, 235, 0.28) !important;
    }
    .easyuse-anima-highlight-overlay {
      text-size-adjust: 100%;
      -webkit-text-size-adjust: 100%;
      contain: paint;
    }
  `;
  document.head.append(style);
}

function ensureAdvancedStyle() {
  if (document.getElementById("easyuse-anima-advanced-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-advanced-style";
  style.textContent = `
    .easyuse-anima-advanced-editor {
      box-sizing: border-box;
      width: 100%;
      min-width: 0;
      overflow-x: hidden;
      overflow-y: auto;
      overscroll-behavior: contain;
      color: var(--fg-color, #ddd);
      font: 12px sans-serif;
      user-select: none;
    }
    .easyuse-anima-advanced-panes {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .easyuse-anima-advanced-editor.is-narrow .easyuse-anima-advanced-panes {
      flex-direction: column;
    }
    .easyuse-anima-advanced-controlbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 5px;
      margin-bottom: 7px;
    }
    .easyuse-anima-advanced-toggle {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 34px;
      height: 21px;
      padding: 0 7px;
      border: 1px solid rgba(148, 163, 184, 0.36);
      background: rgba(30, 41, 59, 0.78);
      color: rgba(226, 232, 240, 0.72);
      font: 10px sans-serif;
      line-height: 1;
      cursor: pointer;
    }
    .easyuse-anima-advanced-toggle.is-on {
      border-color: rgba(96, 165, 250, 0.78);
      background: rgba(37, 99, 235, 0.68);
      color: #fff;
      font-weight: 700;
    }
    .easyuse-anima-advanced-toggle.is-linked {
      opacity: 0.55;
      cursor: default;
    }
    .easyuse-anima-advanced-resolutionbar {
      display: grid;
      grid-template-columns: minmax(82px, 0.34fr) minmax(0, 1fr);
      gap: 8px;
      margin: 0 0 10px;
    }
    .easyuse-anima-advanced-wildcardbar {
      display: grid;
      grid-template-columns: minmax(92px, 0.34fr) minmax(74px, 0.28fr) minmax(92px, 0.38fr);
      gap: 8px;
      margin: 0 0 10px;
    }
    .easyuse-anima-advanced-wildcardbar select,
    .easyuse-anima-advanced-wildcardbar input {
      box-sizing: border-box;
      min-width: 0;
      width: 100%;
      height: 27px;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(15, 23, 42, 0.88);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      padding: 2px 8px;
      outline: none;
    }
    .easyuse-anima-advanced-wildcardbar select:focus,
    .easyuse-anima-advanced-wildcardbar input:focus {
      border-color: rgba(96, 165, 250, 0.76);
    }
    .easyuse-anima-advanced-resolutionbar select,
    .easyuse-anima-advanced-resolutionbar input {
      box-sizing: border-box;
      min-width: 0;
      width: 100%;
      height: 27px;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(15, 23, 42, 0.88);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      padding: 2px 8px;
      outline: none;
    }
    .easyuse-anima-advanced-resolutionbar select:focus,
    .easyuse-anima-advanced-resolutionbar input:focus {
      border-color: rgba(96, 165, 250, 0.76);
    }
    .easyuse-anima-advanced-resolution-custom {
      display: grid;
      grid-template-columns: minmax(72px, 1fr) auto minmax(72px, 1fr);
      gap: 6px;
      align-items: center;
    }
    .easyuse-anima-advanced-resolution-custom span {
      color: rgba(203, 213, 225, 0.72);
      font: 12px sans-serif;
    }
    .easyuse-anima-advanced-pane {
      min-width: 0;
      border: 1px solid rgba(148, 163, 184, 0.28);
      background: rgba(15, 23, 42, 0.28);
      padding: 6px;
      box-sizing: border-box;
    }
    .easyuse-anima-advanced-pane-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      margin-bottom: 6px;
      color: rgba(226, 232, 240, 0.82);
      font-weight: 700;
    }
    .easyuse-anima-advanced-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      justify-content: flex-end;
    }
    .easyuse-anima-advanced-actions button,
    .easyuse-anima-field-tools button {
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(30, 41, 59, 0.8);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      min-height: 20px;
      padding: 1px 6px;
      cursor: pointer;
    }
    .easyuse-anima-advanced-actions button:disabled,
    .easyuse-anima-field-tools button:disabled {
      opacity: 0.35;
      cursor: default;
    }
    .easyuse-anima-advanced-field {
      margin: 0 0 6px;
    }
    .easyuse-anima-advanced-field.is-disabled {
      opacity: 0.58;
    }
    .easyuse-anima-field-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      min-height: 20px;
      color: rgba(203, 213, 225, 0.86);
    }
    .easyuse-anima-field-label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .easyuse-anima-field-tools {
      display: flex;
      gap: 3px;
      flex: 0 0 auto;
    }
    .easyuse-anima-field-tools button.easyuse-anima-naia-fill {
      min-width: 78px;
      font-weight: 700;
    }
    .easyuse-anima-field-tools button.easyuse-anima-trigger-pin {
      min-width: 58px;
      font-weight: 700;
    }
    .easyuse-anima-field-tools button.is-on {
      border-color: rgba(96, 165, 250, 0.78);
      background: rgba(37, 99, 235, 0.58);
      color: #fff;
    }
    .easyuse-anima-advanced-field textarea {
      box-sizing: border-box;
      width: 100%;
      min-height: 46px;
      resize: vertical;
      overflow: hidden;
      border: 1px solid rgba(148, 163, 184, 0.28);
      background: rgba(10, 10, 12, 0.78);
      color: var(--input-text, #ddd);
      padding: 6px;
      font: 12px monospace;
      line-height: 1.35;
      outline: none;
    }
    .easyuse-anima-advanced-field textarea:focus {
      border-color: rgba(96, 165, 250, 0.7);
    }
    .easyuse-anima-advanced-field textarea.is-linked {
      opacity: 0.72;
      border-style: dashed;
      cursor: default;
    }
    .easyuse-anima-advanced-field.is-naia textarea {
      border-style: dashed;
      background: rgba(15, 23, 42, 0.74);
      cursor: default;
    }
    .easyuse-anima-advanced-field.is-trigger textarea {
      border-style: dashed;
      background: rgba(12, 20, 34, 0.78);
      cursor: default;
    }
    .easyuse-anima-empty-pane {
      padding: 10px 4px;
      color: rgba(148, 163, 184, 0.72);
      font-size: 11px;
    }
  `;
  document.head.append(style);
}

function ensureExtendSlotStyle() {
  if (document.getElementById("easyuse-anima-extend-slot-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-extend-slot-style";
  style.textContent = `
    .easyuse-anima-extend-slots {
      box-sizing: border-box;
      width: 100%;
      padding-bottom: 4px;
      color: var(--fg-color, #ddd);
      font: 11px sans-serif;
      user-select: none;
    }
    .easyuse-anima-extend-slot-row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 5px;
      width: 100%;
    }
    .easyuse-anima-extend-slot-hide-row {
      display: flex;
      flex-wrap: wrap;
      margin-top: 5px;
    }
    .easyuse-anima-extend-slot-row button {
      box-sizing: border-box;
      min-width: 0;
      height: 24px;
      border: 1px solid rgba(148, 163, 184, 0.38);
      border-radius: 4px;
      background: rgba(17, 24, 39, 0.7);
      color: var(--fg-color, #ddd);
      font: 11px sans-serif;
      cursor: pointer;
    }
    .easyuse-anima-extend-slot-row button:hover:not(:disabled) {
      border-color: rgba(96, 165, 250, 0.74);
      background: rgba(30, 64, 175, 0.5);
    }
    .easyuse-anima-extend-slot-row button:disabled {
      opacity: 0.42;
      cursor: default;
    }
    .easyuse-anima-extend-slot-hide-row button {
      flex: 0 1 auto;
      height: 21px;
      padding: 0 6px;
      font-size: 10px;
    }
  `;
  document.head.append(style);
}

function refreshNodeSize(node, options = {}) {
  const update = () => {
    const size = node.computeSize();
    const width = Math.max(size[0], node.size?.[0] || size[0]);
    const height = Math.max(size[1], 80);
    if (
      Math.abs(width - (node.size?.[0] || 0)) > 1
      || Math.abs(height - (node.size?.[1] || 0)) > 1
    ) {
      node.setSize?.([width, height]);
    }
    app.graph.setDirtyCanvas(true, true);
  };
  if (options.immediate) {
    update();
  } else {
    requestAnimationFrame(update);
  }
}

function debounce(fn, delay = 180) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function isHexColor(value) {
  return /^#[0-9a-f]{6}$/i.test(String(value || ""));
}

function hexToRgba(value, alpha) {
  if (!isHexColor(value)) {
    return "transparent";
  }
  const red = Number.parseInt(value.slice(1, 3), 16);
  const green = Number.parseInt(value.slice(3, 5), 16);
  const blue = Number.parseInt(value.slice(5, 7), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function parseColorSettings(value) {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function applyPromptStudioSettings(settings) {
  PROMPT_STUDIO_SETTINGS.typoIndicator = settings?.["prompt_studio.typo_indicator"] !== "false";
  PROMPT_STUDIO_SETTINGS.commentItalic = settings?.["prompt_studio.comment_italic"] !== "false";
  PROMPT_STUDIO_SETTINGS.naiaGeneralAboveAutoToggle =
    settings?.["prompt_studio.naia_general_above_auto_toggle"] === "true";
  const colors = parseColorSettings(settings?.["prompt_studio.colors"]);
  for (const [key, color] of Object.entries(colors)) {
    if (!SECTION_STYLES[key] || !isHexColor(color)) {
      continue;
    }
    SECTION_STYLES[key].color = color;
    if (SECTION_STYLES[key].background && SECTION_STYLES[key].background !== "transparent") {
      SECTION_STYLES[key].background = hexToRgba(color, 0.18);
    }
  }
}

async function loadPromptStudioSettings() {
  try {
    const response = await fetch("/easyuse_anima/settings");
    if (!response.ok) {
      return;
    }
    applyPromptStudioSettings(await response.json());
    refreshAllPromptHighlights();
    app.graph?.setDirtyCanvas(true, true);
  } catch {
    // Keep built-in defaults if the settings endpoint is not available yet.
  }
}

async function classifyPrompt(text) {
  const response = await fetch("/easyuse_anima/classify_prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, limit: 240 }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  return Array.isArray(data.tokens) ? data.tokens : [];
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function normalize(value) {
  return normalizePromptTagText(value, { unescapeAll: true })
    .toLocaleLowerCase()
    .replace(INLINE_SPACE_RE, " ")
    .trim();
}

function tokenBase(token) {
  let value = String(token ?? "").trim();
  const weighted = WEIGHTED_TOKEN_RE.exec(value);
  if (weighted) {
    value = weighted[1].trim();
  }
  value = value.replace(/:+$/, "").trim();
  value = value.replace(/\\(.)/g, "$1");
  if (value.startsWith("@")) {
    return value.slice(1).trim();
  }
  return value;
}

function isPromptLineCommentStart(value, index) {
  if (value[index] !== "#") {
    return false;
  }
  const lineStart = value.lastIndexOf("\n", index - 1) + 1;
  return /^[ \t]*$/.test(value.slice(lineStart, index));
}

function splitPromptText(text) {
  const parts = [];
  let start = 0;
  let depth = 0;
  let escaped = false;
  const value = String(text ?? "");

  for (let index = 0; index < value.length; index += 1) {
    const char = value[index];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
      continue;
    }

    if (isPromptLineCommentStart(value, index)) {
      const nextNewLine = value.indexOf("\n", index);
      index = nextNewLine === -1 ? value.length : nextNewLine - 1;
      continue;
    }

    if (char === "(") {
      depth += 1;
      continue;
    }
    if (char === ")" && depth > 0) {
      depth -= 1;
      continue;
    }
    if (char === "{") {
      const dynamicEnd = findDynamicPromptEnd(value, index);
      if (dynamicEnd > index) {
        index = dynamicEnd - 1;
      }
      continue;
    }
    if ((char === "," || char === "\n") && depth === 0) {
      if (index > start) {
        parts.push({ text: value.slice(start, index), delimiter: false });
      }
      parts.push({ text: char, delimiter: true });
      start = index + 1;
    }
  }

  if (start < value.length) {
    parts.push({ text: value.slice(start), delimiter: false });
  }
  return parts;
}

function tokenStyle(token) {
  const style = SECTION_STYLES[token?.section] || SECTION_STYLES.unknown;
  const opacity = token?.learned || token?.section === "count" ? 1 : 0.88;
  const rules = [
    `color: ${style.color}`,
    `opacity: ${opacity}`,
  ];
  if (style.background && style.background !== "transparent") {
    rules.push(`background: ${style.background}`, "border-radius: 3px");
  }
  if (style.italic && PROMPT_STUDIO_SETTINGS.commentItalic) {
    rules.push("font-style: italic");
  }
  if (style.underline && PROMPT_STUDIO_SETTINGS.typoIndicator && !token?.weighted) {
    rules.push(
      "text-decoration-line: underline",
      "text-decoration-style: wavy",
      "text-decoration-color: #ef4444",
      "text-underline-offset: 2px",
    );
  }
  return rules.join("; ");
}

function tokenTitle(token) {
  const style = SECTION_STYLES[token?.section] || SECTION_STYLES.unknown;
  const label = token?.label || sectionLabel(token?.section) || style.label || token?.section || psText("tag.generic");
  const learned = token?.learned ? ` / ${psText("tag.learned")}` : "";
  return `${label}${learned}`;
}

function tokenSpanHtml(text, token) {
  return `<span style="${tokenStyle(token)}" title="${escapeHtml(tokenTitle(token))}">`
    + escapeHtml(text)
    + "</span>";
}

function basicSyntaxHtml(text) {
  return escapeHtml(text).replace(
    /(:)([-+]?\d+(?:\.\d+)?)(\))/g,
    `$1<span style="color: ${WEIGHT_NUMBER_COLOR}">$2</span>$3`,
  );
}

function wildcardSyntaxSpanHtml(text) {
  return `<span style="${tokenStyle({ section: "wildcard" })}" title="${escapeHtml(sectionLabel("wildcard"))}">`
    + escapeHtml(text)
    + "</span>";
}

function isEscapedAt(value, index) {
  let slashCount = 0;
  for (let cursor = index - 1; cursor >= 0 && value[cursor] === "\\"; cursor -= 1) {
    slashCount += 1;
  }
  return slashCount % 2 === 1;
}

function findDynamicPromptEnd(value, start) {
  for (let cursor = start + 1; cursor < value.length; cursor += 1) {
    if (value[cursor] === "\\" && cursor + 1 < value.length) {
      cursor += 1;
      continue;
    }
    if (value[cursor] === "{") {
      return -1;
    }
    if (value[cursor] === "}") {
      return cursor + 1;
    }
  }
  return -1;
}

function findDynamicPromptRange(value, offset) {
  for (let start = offset; start < value.length; start += 1) {
    if (value[start] !== "{" || isEscapedAt(value, start)) {
      continue;
    }
    const end = findDynamicPromptEnd(value, start);
    if (end > start) {
      return { start, end };
    }
  }
  return null;
}

function findWildcardSyntaxRange(value, offset) {
  WILDCARD_HIGHLIGHT_RE.lastIndex = offset;
  const wildcardMatch = WILDCARD_HIGHLIGHT_RE.exec(value);
  const wildcard = wildcardMatch
    ? { start: wildcardMatch.index, end: wildcardMatch.index + wildcardMatch[0].length }
    : null;
  const dynamic = findDynamicPromptRange(value, offset);
  if (!wildcard) {
    return dynamic;
  }
  if (!dynamic || wildcard.start <= dynamic.start) {
    return wildcard;
  }
  return dynamic;
}

function hasWildcardHighlightSyntax(text) {
  return !!findWildcardSyntaxRange(String(text ?? ""), 0);
}

function syntaxHtml(text) {
  const value = String(text ?? "");
  let cursor = 0;
  const html = [];
  while (cursor < value.length) {
    const range = findWildcardSyntaxRange(value, cursor);
    if (!range) {
      break;
    }
    html.push(basicSyntaxHtml(value.slice(cursor, range.start)));
    html.push(wildcardSyntaxSpanHtml(value.slice(range.start, range.end)));
    cursor = range.end;
  }
  html.push(basicSyntaxHtml(value.slice(cursor)));
  return html.join("");
}

function weightedTokenSpanHtml(text, token) {
  const match = findTokenMatch(text, 0, token);
  if (!match) {
    return tokenSpanHtml(text, token);
  }
  return [
    syntaxHtml(text.slice(0, match.start)),
    tokenSpanHtml(text.slice(match.start, match.end), token),
    syntaxHtml(text.slice(match.end)),
  ].join("");
}

function findTokenMatch(body, offset, token) {
  let start = offset;
  const skipWeightedSyntax = !!token?.weighted;
  while (
    start < body.length
    && (
      /\s/.test(body[start])
      || (skipWeightedSyntax && (body[start] === "(" || body[start] === ","))
    )
  ) {
    start += 1;
  }

  const candidates = [
    String(token?.token || ""),
    String(token?.base || ""),
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (body.slice(start, start + candidate.length) === candidate) {
      return { start, end: start + candidate.length };
    }
    const normalized = normalize(candidate);
    const maxEnd = Math.min(body.length, start + candidate.length + 32);
    for (let end = start + 1; end <= maxEnd; end += 1) {
      const prefix = normalize(body.slice(start, end));
      if (prefix === normalized) {
        return { start, end };
      }
      if (prefix.length > normalized.length + 8) {
        break;
      }
    }
  }
  return null;
}

function tokenKey(token) {
  return normalize(token?.base || token?.token);
}

function nextUnconsumedToken(tokens, startIndex, consumed) {
  let index = startIndex;
  while (index < (tokens?.length || 0) && consumed.has(tokens[index])) {
    index += 1;
  }
  return { token: tokens?.[index], index };
}

function takeTokenByBase(byBase, baseKey, consumed) {
  const candidates = byBase.get(baseKey);
  while (candidates?.length) {
    const token = candidates.shift();
    if (!consumed.has(token)) {
      consumed.add(token);
      return token;
    }
  }
  return null;
}

function renderSequentialBody(body, tokens, startIndex, consumed) {
  let cursor = 0;
  let index = startIndex;
  let matched = 0;
  const html = [];

  while (index < (tokens?.length || 0)) {
    const next = nextUnconsumedToken(tokens, index, consumed);
    const token = next.token;
    index = next.index;
    if (!token) {
      break;
    }
    const match = findTokenMatch(body, cursor, token);
    if (!match) {
      break;
    }
    html.push(syntaxHtml(body.slice(cursor, match.start)));
    html.push(tokenSpanHtml(body.slice(match.start, match.end), token));
    consumed.add(token);
    cursor = match.end;
    index += 1;
    matched += 1;
    if (!body.slice(cursor).trim()) {
      break;
    }
  }

  if (!matched) {
    return null;
  }
  html.push(syntaxHtml(body.slice(cursor)));
  return { html: html.join(""), nextIndex: index };
}

function renderHighlightedText(text, tokens) {
  const byBase = new Map();
  for (const token of tokens || []) {
    const key = tokenKey(token);
    if (!key) {
      continue;
    }
    byBase.set(key, [...(byBase.get(key) || []), token]);
  }

  let tokenIndex = 0;
  const consumed = new Set();
  const html = [];
  for (const part of splitPromptText(text)) {
    if (part.delimiter) {
      html.push(escapeHtml(part.text));
      continue;
    }

    const match = /^(\s*)([\s\S]*?)(\s*)$/.exec(part.text);
    const leading = match?.[1] || "";
    const body = match?.[2] || "";
    const trailing = match?.[3] || "";
    if (!body) {
      html.push(escapeHtml(part.text));
      continue;
    }

    if (hasWildcardHighlightSyntax(body)) {
      html.push(escapeHtml(leading));
      html.push(syntaxHtml(body));
      html.push(escapeHtml(trailing));
      continue;
    }

    const baseKey = normalize(tokenBase(body));
    const next = nextUnconsumedToken(tokens, tokenIndex, consumed);
    const sequential = next.token;
    tokenIndex = next.index;
    let token = null;
    if (tokenKey(sequential) === baseKey) {
      token = sequential;
      consumed.add(token);
      tokenIndex += 1;
    } else {
      token = takeTokenByBase(byBase, baseKey, consumed);
    }

    if (token) {
      html.push(escapeHtml(leading));
      html.push(token?.weighted && WEIGHTED_TOKEN_RE.test(body)
        ? weightedTokenSpanHtml(body, token)
        : tokenSpanHtml(body, token));
      html.push(escapeHtml(trailing));
      continue;
    }

    const rendered = renderSequentialBody(body, tokens, tokenIndex, consumed);
    if (rendered) {
      tokenIndex = rendered.nextIndex;
      html.push(escapeHtml(leading));
      html.push(rendered.html);
      html.push(escapeHtml(trailing));
      continue;
    }

    html.push(syntaxHtml(part.text));
  }
  return html.join("") || " ";
}

function cssPixelNumber(value) {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function cssPixel(value) {
  const rounded = Math.round(Number(value || 0) * 100) / 100;
  return `${rounded}px`;
}

function overlayScrollbarPadding(input, style = getComputedStyle(input)) {
  const verticalGutter = Math.max(
    0,
    (Number(input.offsetWidth) || 0)
      - (Number(input.clientWidth) || 0)
      - cssPixelNumber(style.borderLeftWidth)
      - cssPixelNumber(style.borderRightWidth),
  );
  const horizontalGutter = Math.max(
    0,
    (Number(input.offsetHeight) || 0)
      - (Number(input.clientHeight) || 0)
      - cssPixelNumber(style.borderTopWidth)
      - cssPixelNumber(style.borderBottomWidth),
  );
  return {
    right: cssPixel(cssPixelNumber(style.paddingRight) + verticalGutter),
    bottom: cssPixel(cssPixelNumber(style.paddingBottom) + horizontalGutter),
  };
}

function applyOverlayScrollbarPadding(input, overlay, style = getComputedStyle(input)) {
  const padding = overlayScrollbarPadding(input, style);
  if (overlay.style.paddingRight !== padding.right) overlay.style.paddingRight = padding.right;
  if (overlay.style.paddingBottom !== padding.bottom) overlay.style.paddingBottom = padding.bottom;
}

function overlayBounds(input) {
  return {
    left: `${input.offsetLeft}px`,
    top: `${input.offsetTop}px`,
    width: `${input.offsetWidth}px`,
    height: `${input.offsetHeight}px`,
  };
}

function highlightOverlayHtml(value, tokens, placeholder = "") {
  const text = String(value || "");
  if (!text) {
    return `<span style="opacity: 0.45">${escapeHtml(placeholder)}</span>`;
  }
  const html = renderHighlightedText(text, tokens);
  return text.endsWith("\n") ? `${html} ` : html;
}

function copyInputTextMetrics(input, overlay, style = getComputedStyle(input)) {
  for (const property of HIGHLIGHT_TEXT_METRIC_PROPERTIES) {
    const val = style[property];
    if (overlay.style[property] !== val) {
      overlay.style[property] = val;
    }
  }
  overlay.style.boxSizing = "border-box";
  overlay.style.whiteSpace = "pre-wrap";
  overlay.style.overflowWrap = "break-word";
  overlay.style.wordWrap = "break-word";
  overlay.style.wordBreak = "normal";
  overlay.style.margin = "0";
  applyOverlayScrollbarPadding(input, overlay, style);
}

function syncOverlayBounds(input, overlay) {
  if (!overlay) return;
  const style = getComputedStyle(input);
  const { left, top, width, height } = overlayBounds(input);

  if (overlay.style.left !== left) overlay.style.left = left;
  if (overlay.style.top !== top) overlay.style.top = top;
  if (overlay.style.width !== width) overlay.style.width = width;
  if (overlay.style.height !== height) overlay.style.height = height;
  applyOverlayScrollbarPadding(input, overlay, style);

  if (overlay.scrollTop !== input.scrollTop) overlay.scrollTop = input.scrollTop;
  if (overlay.scrollLeft !== input.scrollLeft) overlay.scrollLeft = input.scrollLeft;
}

function requestOverlaySync(input, forceCopyMetrics = false) {
  const overlay = input?.__easyuseAnimaHighlightOverlay;
  if (!overlay) {
    return;
  }
  input.__easyuseAnimaHighlightForceCopyMetrics ||= forceCopyMetrics;
  if (input.__easyuseAnimaHighlightSyncRaf) {
    return;
  }
  input.__easyuseAnimaHighlightSyncRaf = requestAnimationFrame(() => {
    input.__easyuseAnimaHighlightSyncRaf = 0;
    const currentOverlay = input.__easyuseAnimaHighlightOverlay;
    if (!input.isConnected || !currentOverlay?.isConnected) {
      input.__easyuseAnimaHighlightForceCopyMetrics = false;
      return;
    }
    if (input.__easyuseAnimaHighlightForceCopyMetrics) {
      copyInputTextMetrics(input, currentOverlay);
    }
    input.__easyuseAnimaHighlightForceCopyMetrics = false;
    syncOverlayBounds(input, currentOverlay);
    requestAnimationFrame(() => {
      if (input.isConnected && currentOverlay.isConnected) {
        syncOverlayBounds(input, currentOverlay);
      }
    });
  });
}

function installOverlaySyncListeners(input) {
  if (input.__easyuseAnimaHighlightSyncInstalled) {
    return;
  }
  const schedule = () => requestOverlaySync(input);
  const scheduleMetrics = () => requestOverlaySync(input, true);
  input.addEventListener("scroll", schedule, { passive: true });
  input.addEventListener("input", schedule);
  input.addEventListener("keyup", schedule);
  input.addEventListener("click", schedule);
  input.addEventListener("compositionupdate", schedule);
  input.addEventListener("compositionend", scheduleMetrics);
  input.__easyuseAnimaHighlightSyncInstalled = true;
}

function ensureHighlightOverlay(input) {
  input.spellcheck = false;
  input.autocomplete = "off";
  input.setAttribute("autocorrect", "off");
  input.setAttribute("autocapitalize", "off");

  if (input.__easyuseAnimaHighlightOverlay) {
    const overlay = input.__easyuseAnimaHighlightOverlay;
    if (overlay.isConnected && overlay.parentElement === input.parentElement) {
      return overlay;
    }
    overlay.remove?.();
    input.__easyuseAnimaHighlightOverlay = null;
  }

  const parent = input.parentElement;
  if (!parent) {
    return null;
  }
  if (getComputedStyle(parent).position === "static") {
    parent.style.position = "relative";
  }

  const overlay = document.createElement("pre");
  overlay.className = "easyuse-anima-highlight-overlay";
  overlay.setAttribute("aria-hidden", "true");
  overlay.style.cssText = [
    "position: absolute",
    "box-sizing: border-box",
    "margin: 0",
    "overflow: hidden",
    "white-space: pre-wrap",
    "overflow-wrap: break-word",
    "word-break: normal",
    "pointer-events: none",
    "z-index: 0",
    "background: rgba(15, 23, 42, 0.62)",
    "color: var(--input-text, #ddd)",
  ].join("; ");
  copyInputTextMetrics(input, overlay);
  parent.insertBefore(overlay, input);

  ensureHighlightStyle();
  input.classList.add("easyuse-anima-highlight-input");
  input.style.position = input.style.position || "relative";
  input.style.zIndex = "1";
  input.style.background = "transparent";
  input.style.color = "transparent";
  input.style.caretColor = "var(--input-text, #ddd)";
  input.style.webkitTextFillColor = "transparent";
  input.style.whiteSpace = "pre-wrap";
  input.style.overflowWrap = "break-word";
  input.style.wordBreak = "normal";
  input.style.textSizeAdjust = "100%";
  input.style.webkitTextSizeAdjust = "100%";

  input.__easyuseAnimaHighlightOverlay = overlay;
  installOverlaySyncListeners(input);
  return overlay;
}

function textareaContentHeight(input, minimumHeight) {
  if (!input) {
    return minimumHeight;
  }
  const previousHeight = input.style.height;
  const previousOverflow = input.style.overflowY;
  input.style.height = "auto";
  input.style.overflowY = "hidden";
  const contentHeight = Math.ceil(Number(input.scrollHeight) || 0);
  input.style.height = previousHeight;
  input.style.overflowY = previousOverflow;
  return Math.max(minimumHeight, contentHeight);
}

function desiredTextareaHeight(input, currentHeight, minimumHeight, options = {}) {
  const includeCurrent = options.includeCurrent !== false;
  const contentHeight = textareaContentHeight(input, minimumHeight);
  return Math.max(
    minimumHeight,
    includeCurrent ? Math.round(Number(currentHeight) || 0) : 0,
    contentHeight,
  );
}

function studioVisualMinimumHeight(widget) {
  return Math.min(studioDefaultHeight(widget), 54);
}

function studioMinimumHeight(widget, input = findInputEl(widget)) {
  return studioVisualMinimumHeight(widget);
}

function studioContentHeight(widget, input = findInputEl(widget)) {
  return desiredTextareaHeight(input, 0, studioVisualMinimumHeight(widget), { includeCurrent: false });
}

function studioCurrentHeight(widget, input = findInputEl(widget)) {
  const styleHeight = Number.parseFloat(input?.style?.height || "");
  return Math.round(
    Number(input?.offsetHeight)
    || Number(input?.clientHeight)
    || styleHeight
    || Number(widget?.__easyuseAnimaHeight)
    || studioDefaultHeight(widget),
  );
}

function setStudioInputHeight(node, widget, height, refresh = false) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const minimumHeight = studioMinimumHeight(widget, input);
  const nextHeight = Math.max(minimumHeight, Math.round(Number(height) || 0));
  widget.__easyuseAnimaLayoutHeight = nextHeight + STUDIO_WIDGET_VERTICAL_GAP;
  if (Math.abs(nextHeight - (widget.__easyuseAnimaHeight || 0)) > 1) {
    widget.__easyuseAnimaHeight = nextHeight;
    input.style.height = `${nextHeight}px`;
    if (refresh) {
      refreshNodeSize(node, { immediate: refresh === "immediate" });
    }
  } else {
    input.style.height = `${nextHeight}px`;
  }
  syncStudioOverflow(widget);
  updateHighlight(node, widget);
}

function syncStudioOverflow(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const height = studioCurrentHeight(widget, input);
  const contentHeight = textareaContentHeight(input, studioVisualMinimumHeight(widget));
  input.style.overflowY = contentHeight > height + 2 ? "auto" : "hidden";
  if (input.__easyuseAnimaHighlightOverlay) {
    input.__easyuseAnimaHighlightOverlay.style.overflow = "hidden";
  }
}

function growStudioManualHeightToContent(node, widget, refresh = false) {
  const input = findInputEl(widget);
  if (!input || !widget.__easyuseAnimaManualHeight || widget.__easyuseAnimaExtendHidden) {
    return false;
  }
  const currentHeight = studioCurrentHeight(widget, input);
  const contentHeight = studioContentHeight(widget, input);
  if (contentHeight > currentHeight + 2) {
    setStudioInputHeight(node, widget, contentHeight, refresh);
    return true;
  }
  syncStudioOverflow(widget);
  updateHighlight(node, widget);
  return false;
}

function setStudioManualHeight(node, widget) {
  const input = findInputEl(widget);
  if (!input || widget.__easyuseAnimaExtendHidden) {
    return;
  }
  widget.__easyuseAnimaManualHeight = true;
  setStudioInputHeight(
    node,
    widget,
    Math.max(studioCurrentHeight(widget, input), studioContentHeight(widget, input)),
    "immediate",
  );
}

function expandStudioInputToContent(node, widget, refresh = false) {
  const input = findInputEl(widget);
  if (!input || widget.__easyuseAnimaExtendHidden) {
    return;
  }
  if (widget.__easyuseAnimaManualHeight) {
    growStudioManualHeightToContent(node, widget, refresh);
    return;
  }
  const height = studioContentHeight(widget, input);
  setStudioInputHeight(node, widget, height, refresh);
}

function visibleStudioWidgets(node) {
  return studioFieldNames(node)
    .map((name) => findWidget(node, name))
    .filter((widget) => {
      const input = findInputEl(widget);
      return widget && input && !widget.hidden && !widget.__easyuseAnimaExtendHidden;
    });
}

function widgetHeight(widget, fallback = 24) {
  const input = findInputEl(widget);
  if (input && !widget.__easyuseAnimaExtendHidden) {
    return studioCurrentHeight(widget, input) + STUDIO_WIDGET_VERTICAL_GAP;
  }
  const size = widget?.computeSize?.();
  return Math.max(0, Number(size?.[1]) || Number(widget?.__height) || fallback);
}

function visibleExtendPromptWidgets(node) {
  return EXTEND_FIELD_NAMES
    .map((name) => findWidget(node, name))
    .filter((widget) => widget && !widget.hidden && !widget.__easyuseAnimaExtendHidden);
}

function firstExtendPromptY(node) {
  const visible = visibleExtendPromptWidgets(node);
  const yValues = visible
    .map((widget) => Number(widget.y))
    .filter((value) => Number.isFinite(value) && value > 0);
  if (yValues.length) {
    return Math.min(...yValues);
  }

  const firstIndex = node.widgets?.findIndex((widget) => EXTEND_FIELD_NAMES.includes(widget?.name)) ?? -1;
  if (firstIndex > 0) {
    for (let index = firstIndex - 1; index >= 0; index -= 1) {
      const widget = node.widgets[index];
      if (!widget || widget.hidden || widget.__easyuseAnimaExtendHidden) {
        continue;
      }
      const height = Number(widget.computeSize?.(node.size?.[0])?.[1]) || Number(widget.__height) || 24;
      const y = Number(widget.y);
      if (Number.isFinite(y)) {
        return y + height + 6;
      }
    }
  }
  return 120;
}

function layoutExtendPromptWidgets(node) {
  if (!isExtendNode(node)) {
    return;
  }

  let cursorY = firstExtendPromptY(node);
  const visible = visibleExtendPromptWidgets(node);
  for (const widget of visible) {
    widget.y = cursorY;
    const input = findInputEl(widget);
    if (input) {
      input.style.height = `${studioCurrentHeight(widget, input)}px`;
    }
    cursorY += widgetHeight(widget, 72);
  }

  const controlsWidget = findWidget(node, "easyuse_anima_extend_slot_controls");
  if (controlsWidget && !controlsWidget.hidden) {
    refreshExtendSlotControlsSize(node);
    controlsWidget.y = cursorY;
    cursorY += Math.max(30, Number(controlsWidget.__height) || 30) + 8;
  }

  const legendWidget = findWidget(node, "easyuse_anima_color_legend");
  if (legendWidget && !legendWidget.hidden) {
    legendWidget.y = cursorY;
    cursorY += Math.max(desiredLegendHeight(), Number(legendWidget.__height) || 0) + 8;
  }

  const minHeight = Math.ceil(cursorY + 8);
  if (Number(node.size?.[1]) < minHeight) {
    node.setSize?.([node.size?.[0] || node.computeSize?.()[0] || 300, minHeight]);
  }
  app.graph?.setDirtyCanvas(true, true);
  app.canvas?.setDirty?.(true, true);
}

function rebalanceStudioInputHeights(node) {
  const widgets = visibleStudioWidgets(node);
  if (!widgets.length) {
    return;
  }

  const currentHeights = widgets.map((widget) => studioCurrentHeight(widget));
  const minimumHeights = widgets.map((widget) => studioMinimumHeight(widget));
  const currentTotal = currentHeights.reduce((sum, value) => sum + value, 0);
  const minimumTotal = minimumHeights.reduce((sum, value) => sum + value, 0);
  const computedHeight = Number(node.computeSize?.()[1]) || currentTotal;
  const nonInputHeight = Math.max(0, computedHeight - currentTotal);
  const targetInputTotal = Math.max(minimumTotal, (Number(node.size?.[1]) || computedHeight) - nonInputHeight);

  if (targetInputTotal < currentTotal - 2) {
    const currentExtra = Math.max(0, currentTotal - minimumTotal);
    const targetExtra = Math.max(0, targetInputTotal - minimumTotal);
    const ratio = currentExtra > 0 ? targetExtra / currentExtra : 0;
    for (const [index, widget] of widgets.entries()) {
      const nextHeight = minimumHeights[index] + (currentHeights[index] - minimumHeights[index]) * ratio;
      setStudioInputHeight(node, widget, nextHeight);
    }
    refreshNodeSize(node, { immediate: true });
    return;
  }

  for (const widget of widgets) {
    expandStudioInputToContent(node, widget);
  }
  refreshNodeSize(node, { immediate: true });
}

function desiredLegendHeight() {
  return LEGEND_TOP_GAP + 16 + Math.ceil(LEGEND_ITEMS.length / LEGEND_COLUMNS) * LEGEND_ROW_HEIGHT;
}

function drawLegend(ctx, node, widget, width, y) {
  const nextHeight = desiredLegendHeight();
  if (Math.abs(nextHeight - widget.__height) > 2) {
    widget.__height = nextHeight;
    refreshNodeSize(node);
  }
  ctx.save();

  ctx.font = "9px sans-serif";
  ctx.fillStyle = "#94a3b8";
  ctx.fillText(psText("legend.color"), 14, y + LEGEND_TOP_GAP + 12);

  const left = 14;
  const availableWidth = Math.max(160, width - 28);
  ctx.font = "9px sans-serif";
  const maxItemWidth = Math.max(
    ...LEGEND_ITEMS.map((key) => 14 + ctx.measureText(sectionLabel(key)).width),
  );
  const columnWidth = Math.min(
    availableWidth / LEGEND_COLUMNS,
    Math.ceil(maxItemWidth + 24),
  );
  const rows = Math.ceil(LEGEND_ITEMS.length / LEGEND_COLUMNS);
  for (const [index, key] of LEGEND_ITEMS.entries()) {
    const style = SECTION_STYLES[key];
    const label = sectionLabel(key);
    const column = Math.floor(index / rows);
    const row = index % rows;
    const x = left + column * columnWidth;
    const rowY = y + LEGEND_TOP_GAP + 29 + row * LEGEND_ROW_HEIGHT;
    ctx.fillStyle = style.background;
    ctx.fillRect(x, rowY - 8, 10, 10);
    ctx.fillStyle = style.color;
    ctx.fillText(label, x + 14, rowY);
  }
  ctx.restore();
}

function ensureLegendWidget(node) {
  const name = "easyuse_anima_color_legend";
  let widget = findWidget(node, name);
  if (widget) {
    return widget;
  }
  widget = {
    name,
    type: "easyuse_anima_color_legend",
    serialize: false,
    __height: desiredLegendHeight(),
    computeSize(width) {
      return [width, this.__height];
    },
    draw(ctx, node, width, y) {
      drawLegend(ctx, node, this, width, y);
    },
  };
  node.widgets ||= [];
  node.widgets.push(widget);
  return widget;
}

function displayText(node, widget) {
  if (isWidgetInputLinked(node, widget.name) && widget.__easyuseAnimaExecutedText != null) {
    return String(widget.__easyuseAnimaExecutedText);
  }
  return String(widget?.inputEl?.value ?? widget?.value ?? "");
}

function isExtendNode(node) {
  return node?.type === EXTEND_NODE_TYPE || node?.comfyClass === EXTEND_NODE_TYPE;
}

function studioFieldNames(node) {
  return isExtendNode(node) ? EXTEND_FIELD_NAMES : FIELD_NAMES;
}

function parseExtendSlots(raw) {
  if (Array.isArray(raw)) {
    return new Set(raw.filter((name) => EXTEND_FIELD_NAMES.includes(name)));
  }
  if (typeof raw === "string" && raw.trim()) {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return new Set(parsed.filter((name) => EXTEND_FIELD_NAMES.includes(name)));
      }
    } catch {
      return new Set();
    }
  }
  return new Set();
}

function extendVisibleSlotsState(node) {
  const propertyRaw = node?.properties?.[EXTEND_VISIBLE_SLOTS_PROPERTY];
  if (propertyRaw != null) {
    return { slots: parseExtendSlots(propertyRaw), explicit: true };
  }
  return { slots: new Set(EXTEND_DEFAULT_VISIBLE_FIELDS), explicit: true };
}

function extendVisibleSlots(node) {
  return extendVisibleSlotsState(node).slots;
}

function writeExtendVisibleSlots(node, slots) {
  const filtered = [...slots].filter((name) => EXTEND_FIELD_NAMES.includes(name));
  node.properties ||= {};
  node.properties[EXTEND_VISIBLE_SLOTS_PROPERTY] = filtered;
  const widget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
  if (widget) {
    widget.value = JSON.stringify(filtered);
  }
}

function extendSlotShouldShow(node, fieldName, state = extendVisibleSlotsState(node)) {
  if (isWidgetInputLinked(node, fieldName)) {
    return true;
  }
  return state.slots.has(fieldName);
}

function setExtendWidgetHidden(widget, hidden) {
  if (!widget) {
    return;
  }
  if (!widget.__easyuseAnimaExtendOriginalComputeSize) {
    widget.__easyuseAnimaExtendOriginalComputeSize = widget.computeSize;
  }
  if (!widget.__easyuseAnimaExtendOriginalDraw) {
    widget.__easyuseAnimaExtendOriginalDraw = widget.draw;
  }

  widget.__easyuseAnimaExtendHidden = hidden;
  widget.hidden = hidden;
  widget.options ||= {};
  widget.options.hidden = hidden;
  if (hidden) {
    widget.computeSize = () => [0, -4];
    widget.draw = () => {};
  } else {
    widget.computeSize = widget.__easyuseAnimaExtendOriginalComputeSize;
    widget.draw = widget.__easyuseAnimaExtendOriginalDraw;
  }

  const input = findInputEl(widget);
  if (input) {
    input.style.display = hidden ? "none" : "";
    input.style.pointerEvents = hidden ? "none" : "";
    if (input.__easyuseAnimaHighlightOverlay) {
      input.__easyuseAnimaHighlightOverlay.style.display = hidden ? "none" : "";
    }
  }
}

function hideExtendStateWidget(node) {
  const widget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
  if (!widget || widget.__easyuseAnimaExtendStateHidden) {
    return;
  }
  widget.__easyuseAnimaExtendStateHidden = true;
  widget.hidden = true;
  widget.serialize = true;
  widget.options ||= {};
  widget.options.hidden = true;
  widget.computeSize = () => [0, -4];
  widget.draw = () => {};
  const input = findInputEl(widget);
  if (input) {
    input.style.display = "none";
  }
}

function applyExtendSlotVisibility(node) {
  if (!isExtendNode(node)) {
    return;
  }
  hideExtendStateWidget(node);
  const state = extendVisibleSlotsState(node);
  const visible = new Set(state.slots);
  for (const fieldName of EXTEND_FIELD_NAMES) {
    const shouldShow = extendSlotShouldShow(node, fieldName, state);
    if (shouldShow) {
      visible.add(fieldName);
    }
    setExtendWidgetHidden(findWidget(node, fieldName), !shouldShow);
  }
  writeExtendVisibleSlots(node, visible);
}

function measureExtendSlotControlsHeight(node) {
  const container = node.__easyuseAnimaExtendSlotControlsEl;
  if (!container) {
    return 30;
  }
  return Math.max(
    30,
    Math.ceil(
      Number(container.scrollHeight)
      || Number(container.getBoundingClientRect?.().height)
      || 0,
    ) + 4,
  );
}

function refreshExtendSlotControlsSize(node) {
  const widget = findWidget(node, "easyuse_anima_extend_slot_controls");
  if (widget) {
    widget.__height = measureExtendSlotControlsHeight(node);
  }
}

function refreshExtendLayoutAfterSlotChange(node) {
  refreshExtendSlotControlsSize(node);
  for (const widget of visibleStudioWidgets(node)) {
    expandStudioInputToContent(node, widget);
  }
  layoutExtendPromptWidgets(node);
  refreshNodeSize(node, { immediate: true });
  requestAnimationFrame(() => {
    refreshExtendSlotControlsSize(node);
    for (const widget of visibleStudioWidgets(node)) {
      expandStudioInputToContent(node, widget);
    }
    layoutExtendPromptWidgets(node);
    refreshNodeSize(node, { immediate: true });
  });
}

function addNextExtendSlot(node, group) {
  const visible = extendVisibleSlots(node);
  const next = group.fields.find((fieldName) => !extendSlotShouldShow(node, fieldName));
  if (!next) {
    return;
  }
  visible.add(next);
  writeExtendVisibleSlots(node, visible);
  applyExtendSlotVisibility(node);
  renderExtendSlotControls(node);
  refreshExtendLayoutAfterSlotChange(node);
}

function hideExtendSlot(node, fieldName) {
  if (!EXTEND_FIELD_NAMES.includes(fieldName) || isWidgetInputLinked(node, fieldName)) {
    return;
  }
  const visible = extendVisibleSlots(node);
  visible.delete(fieldName);
  writeExtendVisibleSlots(node, visible);
  applyExtendSlotVisibility(node);
  renderExtendSlotControls(node);
  refreshExtendLayoutAfterSlotChange(node);
}

function extendSlotShortLabel(fieldName) {
  if (fieldName === "naia_prompt_3") {
    return "NAIA3";
  }
  const match = /_(\d+)$/.exec(fieldName);
  const index = match?.[1] || "";
  if (fieldName.startsWith("quality_")) {
    return `Q${index}`;
  }
  if (fieldName.startsWith("general_")) {
    return `G${index}`;
  }
  if (fieldName.startsWith("trailing_")) {
    return `T${index}`;
  }
  if (fieldName.startsWith("negative_")) {
    return `N${index}`;
  }
  return fieldName;
}

function extendSlotGroupLabel(group) {
  return group?.labelKey ? psText(group.labelKey) : String(group?.label || "");
}

function renderExtendSlotControls(node) {
  const container = node.__easyuseAnimaExtendSlotControlsEl;
  if (!container) {
    return;
  }
  container.innerHTML = "";
  const row = document.createElement("div");
  row.className = "easyuse-anima-extend-slot-row";
  for (const group of EXTEND_SLOT_GROUPS) {
    const shown = group.fields.filter((fieldName) => extendSlotShouldShow(node, fieldName)).length;
    const next = group.fields.find((fieldName) => !extendSlotShouldShow(node, fieldName));
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `+ ${extendSlotGroupLabel(group)} ${shown}/${group.fields.length}`;
    button.disabled = !next;
    button.title = next ? psFormat("extend.showSlotTitle", { name: next }) : psText("extend.noHiddenSlots");
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      addNextExtendSlot(node, group);
    });
    row.append(button);
  }
  container.append(row);

  const visibleFields = EXTEND_SLOT_GROUPS
    .flatMap((group) => group.fields)
    .filter((fieldName) => extendSlotShouldShow(node, fieldName) && !isWidgetInputLinked(node, fieldName));
  if (visibleFields.length) {
    const hideRow = document.createElement("div");
    hideRow.className = "easyuse-anima-extend-slot-row easyuse-anima-extend-slot-hide-row";
    for (const fieldName of visibleFields) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = psFormat("extend.hideSlot", { slot: extendSlotShortLabel(fieldName) });
      button.title = psFormat("extend.hideSlotTitle", { name: fieldName });
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        hideExtendSlot(node, fieldName);
      });
      hideRow.append(button);
    }
    container.append(hideRow);
  }
  refreshExtendSlotControlsSize(node);
}

function ensureExtendSlotControls(node) {
  if (!isExtendNode(node)) {
    return;
  }
  ensureExtendSlotStyle();
  if (!node.__easyuseAnimaExtendSlotControlsEl) {
    const container = document.createElement("div");
    container.className = "easyuse-anima-extend-slots";
    node.__easyuseAnimaExtendSlotControlsEl = container;
    node.addDOMWidget?.("easyuse_anima_extend_slot_controls", "EasyUseAnimaExtendSlotControls", container, {
      serialize: false,
      hideOnZoom: false,
      getMinHeight: () => measureExtendSlotControlsHeight(node),
    });
  }
  renderExtendSlotControls(node);
}

function studioDefaultHeight(widget) {
  return EXTEND_FIELD_HEIGHTS[widget.name] || FIELD_HEIGHTS[widget.name] || 72;
}

function updateHighlight(node, widget, tokens = widget.__easyuseAnimaTokens || [], forceCopyMetrics = false) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  input.__easyuseAnimaHighlightRefresh = (force = false) => updateHighlight(node, widget, widget.__easyuseAnimaTokens || [], force);
  const overlay = ensureHighlightOverlay(input);
  if (!overlay) {
    return;
  }
  if (forceCopyMetrics) {
    copyInputTextMetrics(input, overlay);
  }
  syncOverlayBounds(input, overlay);
  const value = displayText(node, widget);
  overlay.innerHTML = highlightOverlayHtml(value, tokens, input.placeholder || "");
}

function advancedHighlightState(node, field) {
  node.__easyuseAnimaAdvancedHighlightStates ||= {};
  const id = String(field?.id || "field");
  node.__easyuseAnimaAdvancedHighlightStates[id] ||= {
    seq: 0,
    lastText: "",
    pendingText: null,
    tokens: [],
  };
  return node.__easyuseAnimaAdvancedHighlightStates[id];
}

function updateAdvancedFieldHighlight(node, field, textarea, tokens = null, forceCopyMetrics = false) {
  if (!(textarea instanceof HTMLTextAreaElement)) {
    return;
  }
  textarea.__easyuseAnimaNode = node;
  textarea.__easyuseAnimaField = field;
  textarea.__easyuseAnimaHighlightRefresh = (force = false) => updateAdvancedFieldHighlight(node, field, textarea, null, force);
  const overlay = ensureHighlightOverlay(textarea);
  if (!overlay) {
    return;
  }
  const state = advancedHighlightState(node, field);
  const value = String(textarea.value || "");
  if (forceCopyMetrics) {
    copyInputTextMetrics(textarea, overlay);
  }
  syncOverlayBounds(textarea, overlay);
  overlay.innerHTML = highlightOverlayHtml(value, tokens || state.tokens || [], textarea.placeholder || "");
}

function scheduleAdvancedFieldHighlight(node, field, textarea) {
  const state = advancedHighlightState(node, field);
  const text = String(textarea?.value || "");
  if (!text.trim()) {
    state.tokens = [];
    state.lastText = "";
    state.pendingText = null;
    updateAdvancedFieldHighlight(node, field, textarea, []);
    return;
  }
  if (state.lastText === text && Array.isArray(state.tokens)) {
    updateAdvancedFieldHighlight(node, field, textarea, state.tokens);
    return;
  }
  if (state.pendingText === text) {
    updateAdvancedFieldHighlight(node, field, textarea, state.tokens);
    return;
  }

  const seq = ++state.seq;
  state.pendingText = text;
  updateAdvancedFieldHighlight(node, field, textarea, state.tokens);
  classifyPrompt(text)
    .then((tokens) => {
      if (seq !== state.seq || !textarea.isConnected) {
        return;
      }
      state.lastText = text;
      state.tokens = tokens;
      updateAdvancedFieldHighlight(node, field, textarea, tokens);
    })
    .catch(() => {
      if (seq !== state.seq || !textarea.isConnected) {
        return;
      }
      state.tokens = [];
      updateAdvancedFieldHighlight(node, field, textarea, []);
    })
    .finally(() => {
      if (state.pendingText === text) {
        state.pendingText = null;
      }
    });
}

function registerAdvancedAutocompleteInput(node, field, textarea) {
  if (!(textarea instanceof HTMLTextAreaElement) || textarea.readOnly) {
    return;
  }
  const options = {
    node,
    forceArtistOnly: field?.type === "artist",
  };
  if (typeof window.easyuseAnimaHookAutocompleteInput === "function") {
    window.easyuseAnimaHookAutocompleteInput(textarea, options);
    return;
  }
  window.__easyuseAnimaPendingAutocompleteInputs ||= [];
  window.__easyuseAnimaPendingAutocompleteInputs.push({ input: textarea, options });
}

function refreshAdvancedHighlights(node, { classify = true } = {}) {
  const editor = node?.__easyuseAnimaAdvancedEditorEl;
  if (!editor) {
    return;
  }
  const fields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
  const byId = new Map(fields.map((field) => [String(field.id), field]));
  const textareas = Array.from(editor.querySelectorAll("textarea[data-easyuse-anima-advanced-field-id]"));

  const updates = [];

  // Read DOM Sizes
  for (const textarea of textareas) {
    const field = byId.get(String(textarea.dataset.easyuseAnimaAdvancedFieldId || ""));
    if (!field) {
      continue;
    }
    const overlay = ensureHighlightOverlay(textarea);
    if (!overlay) {
      continue;
    }

    const { left, top, width, height } = overlayBounds(textarea);
    const padding = overlayScrollbarPadding(textarea);
    const scrollTop = textarea.scrollTop;
    const scrollLeft = textarea.scrollLeft;

    const state = advancedHighlightState(node, field);
    const value = String(textarea.value || "");
    const htmlContent = highlightOverlayHtml(value, state.tokens || [], textarea.placeholder || "");

    updates.push({
      overlay,
      left,
      top,
      width,
      height,
      padding,
      scrollTop,
      scrollLeft,
      htmlContent,
      textarea,
      field,
      state,
      value
    });
  }

  // Write DOM
  for (const update of updates) {
    const { overlay, left, top, width, height, padding, scrollTop, scrollLeft, htmlContent, textarea, field, state, value } = update;

    if (overlay.style.left !== left) overlay.style.left = left;
    if (overlay.style.top !== top) overlay.style.top = top;
    if (overlay.style.width !== width) overlay.style.width = width;
    if (overlay.style.height !== height) overlay.style.height = height;
    if (overlay.style.paddingRight !== padding.right) overlay.style.paddingRight = padding.right;
    if (overlay.style.paddingBottom !== padding.bottom) overlay.style.paddingBottom = padding.bottom;
    if (overlay.scrollTop !== scrollTop) overlay.scrollTop = scrollTop;
    if (overlay.scrollLeft !== scrollLeft) overlay.scrollLeft = scrollLeft;

    if (overlay.innerHTML !== htmlContent) {
      overlay.innerHTML = htmlContent;
    }

    if (classify && (state.lastText !== value || !Array.isArray(state.tokens))) {
      scheduleAdvancedFieldHighlight(node, field, textarea);
    }
  }
}

function scheduleAdvancedHighlights(node, options = {}) {
  if (!node?.__easyuseAnimaAdvancedEditorEl) {
    return;
  }
  node.__easyuseAnimaAdvancedHighlightOptions = {
    classify: options.classify !== false,
  };
  if (node.__easyuseAnimaAdvancedHighlightScheduled) {
    return;
  }
  node.__easyuseAnimaAdvancedHighlightScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaAdvancedHighlightScheduled = false;
    const refreshOptions = node.__easyuseAnimaAdvancedHighlightOptions || {};
    refreshAdvancedHighlights(node, refreshOptions);
    requestAnimationFrame(() => refreshAdvancedHighlights(node, { classify: false }));
  });
}

let promptHighlightRefreshRaf = 0;

function refreshConnectedHighlightOverlays() {
  const inputs = Array.from(document.querySelectorAll(".easyuse-anima-highlight-input"));
  const updates = [];

  // DOM Style Read
  for (const input of inputs) {
    if (!(input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement)) {
      continue;
    }
    const overlay = ensureHighlightOverlay(input);
    if (!overlay) {
      continue;
    }

    // Font metrics reads
    const style = getComputedStyle(input);
    const metricValues = {};
    for (const prop of HIGHLIGHT_TEXT_METRIC_PROPERTIES) {
      metricValues[prop] = style[prop];
    }

    // Bounds reads
    const { left, top, width, height } = overlayBounds(input);
    const padding = overlayScrollbarPadding(input, style);
    const scrollTop = input.scrollTop;
    const scrollLeft = input.scrollLeft;

    updates.push({
      overlay,
      metricValues,
      left,
      top,
      width,
      height,
      padding,
      scrollTop,
      scrollLeft
    });
  }

  // DOM Style Write
  for (const update of updates) {
    const { overlay, metricValues, left, top, width, height, padding, scrollTop, scrollLeft } = update;

    // Apply metrics (only if they changed)
    for (const prop in metricValues) {
      const val = metricValues[prop];
      if (overlay.style[prop] !== val) {
        overlay.style[prop] = val;
      }
    }

    // Apply bounds styles (only if they changed)
    if (overlay.style.left !== left) overlay.style.left = left;
    if (overlay.style.top !== top) overlay.style.top = top;
    if (overlay.style.width !== width) overlay.style.width = width;
    if (overlay.style.height !== height) overlay.style.height = height;
    overlay.style.boxSizing = "border-box";
    overlay.style.whiteSpace = "pre-wrap";
    overlay.style.overflowWrap = "break-word";
    overlay.style.wordWrap = "break-word";
    overlay.style.wordBreak = "normal";
    if (overlay.style.paddingRight !== padding.right) overlay.style.paddingRight = padding.right;
    if (overlay.style.paddingBottom !== padding.bottom) overlay.style.paddingBottom = padding.bottom;
    if (overlay.scrollTop !== scrollTop) overlay.scrollTop = scrollTop;
    if (overlay.scrollLeft !== scrollLeft) overlay.scrollLeft = scrollLeft;
  }
}

function requestConnectedHighlightOverlayRefresh() {
  if (promptHighlightRefreshRaf) {
    return;
  }
  promptHighlightRefreshRaf = requestAnimationFrame(() => {
    promptHighlightRefreshRaf = 0;
    refreshConnectedHighlightOverlays();
    setTimeout(refreshConnectedHighlightOverlays, 80);
  });
}

function installPromptHighlightOverlayRefresh() {
  if (window.__easyuseAnimaHighlightOverlayRefreshInstalled) {
    return;
  }
  window.__easyuseAnimaHighlightOverlayRefreshInstalled = true;
  const schedule = () => requestConnectedHighlightOverlayRefresh();
  window.addEventListener("focus", schedule);
  window.addEventListener("resize", schedule);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      schedule();
    }
  });
  const installCanvasListeners = () => {
    const canvas = app?.canvas?.canvas;
    if (!canvas || canvas.__easyuseAnimaHighlightRefreshInstalled) {
      return;
    }
    canvas.__easyuseAnimaHighlightRefreshInstalled = true;
    canvas.addEventListener("pointerup", schedule, { passive: true });
    canvas.addEventListener("wheel", schedule, { passive: true });
  };
  installCanvasListeners();
  setTimeout(installCanvasListeners, 250);
}

function refreshAllPromptHighlights() {
  for (const node of app.graph?._nodes || []) {
    if (isAdvancedNode(node)) {
      scheduleAdvancedHighlights(node);
      continue;
    }
    for (const name of studioFieldNames(node)) {
      const widget = findWidget(node, name);
      if (widget) {
        updateHighlight(node, widget);
      }
    }
  }
}

function enhanceResizableInput(node, widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }

  const defaultHeight = studioDefaultHeight(widget);
  const minimumHeight = Math.min(defaultHeight, 54);

  widget.__easyuseAnimaHeight = Math.max(minimumHeight, widget.__easyuseAnimaHeight || defaultHeight);
  widget.__easyuseAnimaLayoutHeight = widget.__easyuseAnimaHeight + STUDIO_WIDGET_VERTICAL_GAP;
  input.style.boxSizing = "border-box";
  input.style.resize = "vertical";
  input.style.overflowY = "hidden";
  input.style.minHeight = `${minimumHeight}px`;
  input.style.height = `${widget.__easyuseAnimaHeight}px`;

  if (!widget.__easyuseAnimaStudioComputeWrapped) {
    const computeSize = widget.computeSize;
    widget.computeSize = function (width) {
      const base = computeSize?.apply(this, arguments) || [width, minimumHeight];
      const layoutHeight = (this.__easyuseAnimaHeight || minimumHeight) + STUDIO_WIDGET_VERTICAL_GAP;
      this.__easyuseAnimaLayoutHeight = layoutHeight;
      return [base[0], Math.max(base[1], layoutHeight)];
    };
    widget.__easyuseAnimaStudioComputeWrapped = true;
  }

  const syncHeight = () => {
    if (widget.__easyuseAnimaManualHeight) {
      growStudioManualHeightToContent(node, widget, "immediate");
      requestOverlaySync(input);
      return;
    }
    const height = desiredTextareaHeight(input, 0, minimumHeight, { includeCurrent: false });
    setStudioInputHeight(node, widget, height, "immediate");
  };
  const rememberResizeStart = () => {
    widget.__easyuseAnimaResizeStartHeight = studioCurrentHeight(widget, input);
  };
  const captureManualResize = () => {
    const startHeight = Number(widget.__easyuseAnimaResizeStartHeight || widget.__easyuseAnimaHeight || 0);
    const currentHeight = studioCurrentHeight(widget, input);
    widget.__easyuseAnimaResizeStartHeight = currentHeight;
    if (Math.abs(currentHeight - startHeight) > 2) {
      setStudioManualHeight(node, widget);
    } else {
      updateHighlight(node, widget);
    }
  };

  requestAnimationFrame(() => expandStudioInputToContent(node, widget, true));
  if (input.__easyuseAnimaStudioResizable) {
    return;
  }

  input.addEventListener("mousedown", rememberResizeStart);
  input.addEventListener("pointerdown", rememberResizeStart);
  input.addEventListener("mouseup", captureManualResize);
  input.addEventListener("pointerup", captureManualResize);
  input.addEventListener("input", syncHeight);
  input.__easyuseAnimaStudioResizable = true;
}

function syncWidgetValue(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  widget.value = input.value;
}

function syncStudioValues(node, serialized = null) {
  const fieldNames = studioFieldNames(node);
  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (widget) {
      syncWidgetValue(widget);
    }
  }

  if (!serialized || !Array.isArray(node.widgets) || !Array.isArray(serialized.widgets_values)) {
    return;
  }
  if (isExtendNode(node)) {
    applyExtendSlotVisibility(node);
    const activeSlotsValue = JSON.stringify([...extendVisibleSlots(node)]);
    const activeSlotsWidget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
    if (activeSlotsWidget) {
      activeSlotsWidget.value = activeSlotsValue;
    }
    serialized.properties ||= {};
    serialized.properties[EXTEND_VISIBLE_SLOTS_PROPERTY] = [...parseExtendSlots(activeSlotsValue)];
  }

  for (const name of fieldNames) {
    const widgetIndex = node.widgets.findIndex((widget) => widget?.name === name);
    const widget = widgetIndex >= 0 ? node.widgets[widgetIndex] : null;
    if (widgetIndex >= 0 && widget) {
      serialized.widgets_values[widgetIndex] = widget.value ?? "";
    }
  }

  if (isExtendNode(node)) {
    const widgetIndex = node.widgets.findIndex((widget) => widget?.name === EXTEND_ACTIVE_SLOTS_WIDGET);
    const widget = widgetIndex >= 0 ? node.widgets[widgetIndex] : null;
    if (widgetIndex >= 0 && widget) {
      serialized.widgets_values[widgetIndex] = widget.value ?? JSON.stringify([...extendVisibleSlots(node)]);
    }
  }
}

function restoreInputFromWidget(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const value = String(widget?.value ?? input.value ?? "");
  if (input.value !== value) {
    input.value = value;
  }
}

function hookStudioNode(node, attempt = 0) {
  const fieldNames = studioFieldNames(node);
  const updateByField = new Map();
  let pendingInput = false;

  const getUpdateField = (fieldName) => {
    if (updateByField.has(fieldName)) {
      return updateByField.get(fieldName);
    }
    let classifySeq = 0;
    const update = debounce(async () => {
      const widget = findWidget(node, fieldName);
      if (!widget) {
        return;
      }
      const text = displayText(node, widget);
      if (!text.trim()) {
        widget.__easyuseAnimaTokens = [];
        widget.__easyuseAnimaLastClassifiedText = "";
        widget.__easyuseAnimaPendingClassifyText = null;
        updateHighlight(node, widget);
        return;
      }
      if (
        widget.__easyuseAnimaLastClassifiedText === text
        && Array.isArray(widget.__easyuseAnimaTokens)
      ) {
        updateHighlight(node, widget, widget.__easyuseAnimaTokens);
        return;
      }
      if (widget.__easyuseAnimaPendingClassifyText === text) {
        return;
      }

      const seq = ++classifySeq;
      widget.__easyuseAnimaPendingClassifyText = text;
      try {
        const tokens = await classifyPrompt(text);
        if (seq !== classifySeq) {
          return;
        }
        widget.__easyuseAnimaLastClassifiedText = text;
        widget.__easyuseAnimaTokens = tokens;
        updateHighlight(node, widget, tokens);
      } catch {
        widget.__easyuseAnimaTokens = [];
        updateHighlight(node, widget);
      } finally {
        if (widget.__easyuseAnimaPendingClassifyText === text) {
          widget.__easyuseAnimaPendingClassifyText = null;
        }
      }
    });
    updateByField.set(fieldName, update);
    return update;
  };

  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    const input = findInputEl(widget);
    if (!input) {
      pendingInput = true;
      continue;
    }
    restoreInputFromWidget(widget);
    if (isExtendNode(node) && name === "naia_prompt_3") {
      input.readOnly = true;
      input.placeholder = psText("extend.naiaResult");
      input.title = psText("extend.naiaResultTitle");
    }
    enhanceResizableInput(node, widget);
    const updateField = getUpdateField(name);

    if (!widget.__easyuseAnimaStudioHooked) {
      const callback = widget.callback;
      widget.callback = function (value) {
        const result = callback?.apply(this, arguments);
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
        return result;
      };
      input.addEventListener("input", () => {
        widget.value = input.value;
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
      });
      input.addEventListener("change", () => {
        widget.value = input.value;
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
      });
      input.addEventListener("blur", () => syncWidgetValue(widget));
      input.addEventListener("click", () => updateHighlight(node, widget));
      input.addEventListener("keyup", () => updateHighlight(node, widget));
      widget.__easyuseAnimaStudioHooked = true;
    }
    updateField();
  }

  if (isExtendNode(node)) {
    applyExtendSlotVisibility(node);
    ensureExtendSlotControls(node);
  }
  ensureLegendWidget(node);
  if (isExtendNode(node)) {
    layoutExtendPromptWidgets(node);
  }
  refreshNodeSize(node);
  if (pendingInput && attempt < 12) {
    setTimeout(() => hookStudioNode(node, attempt + 1), 80);
  }
}

function applyExecutedInputs(node, message) {
  const slotPayload = firstValue(message?.prompt_studio_slots, null);
  const payload = slotPayload || firstValue(message?.prompt_studio_inputs, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  const fieldNames = studioFieldNames(node);
  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    if (slotPayload && Object.prototype.hasOwnProperty.call(payload, name)) {
      widget.value = String(payload[name] ?? "");
      restoreInputFromWidget(widget);
      widget.__easyuseAnimaExecutedText = null;
      expandStudioInputToContent(node, widget, true);
    } else {
      widget.__easyuseAnimaExecutedText = String(payload[name] ?? "");
      expandStudioInputToContent(node, widget, true);
    }
  }
  if (slotPayload) {
    if (payload.active_slots != null) {
      writeExtendVisibleSlots(node, parseExtendSlots(payload.active_slots));
    }
    const fillNaia = findWidget(node, "fill_naia_prompt");
    if (fillNaia && payload.fill_naia_prompt != null) {
      fillNaia.value = !!payload.fill_naia_prompt;
    }
  }
  hookStudioNode(node);
}

function advancedDefaultFields() {
  return JSON.parse(JSON.stringify(ADVANCED_DEFAULT_FIELDS));
}

function advancedDefaultFieldsValue() {
  return JSON.stringify(advancedDefaultFields().map((field, index) => normalizeAdvancedField(field, index)));
}

function advancedWidget(node) {
  return findWidget(node, "advanced_fields");
}

function advancedFieldsBackup(node) {
  const value = node?.properties?.[ADVANCED_FIELDS_PROPERTY];
  return typeof value === "string" && value.trim() ? value : "";
}

function syncAdvancedFieldsBackup(node, value) {
  node.properties ||= {};
  node.properties[ADVANCED_FIELDS_PROPERTY] = String(value || "");
}

function normalizeAdvancedFieldsValue(value) {
  if (value == null) {
    return "";
  }
  try {
    const parsed = typeof value === "string" ? JSON.parse(value || "[]") : value;
    if (!Array.isArray(parsed) || !parsed.length) {
      return "";
    }
    return JSON.stringify(parsed.map((field, index) => normalizeAdvancedField(field, index)));
  } catch {
    return "";
  }
}

function serializedAdvancedFieldsValue(serialized) {
  const propertyValue = normalizeAdvancedFieldsValue(serialized?.properties?.[ADVANCED_FIELDS_PROPERTY]);
  if (propertyValue) {
    return propertyValue;
  }
  const widgetsValue = normalizeAdvancedFieldsValue(serialized?.widgets_values?.[ADVANCED_WIDGET_INDEX.advanced_fields]);
  if (widgetsValue) {
    return widgetsValue;
  }
  for (const index of ADVANCED_LEGACY_FIELDS_WIDGET_INDEXES) {
    const legacyValue = normalizeAdvancedFieldsValue(serialized?.widgets_values?.[index]);
    if (legacyValue) {
      return legacyValue;
    }
  }
  return "";
}

function captureAdvancedConfigure(node, serialized) {
  const value = serializedAdvancedFieldsValue(serialized);
  if (!value) {
    return;
  }
  node.__easyuseAnimaPendingAdvancedFieldsValue = value;
  syncAdvancedFieldsBackup(node, value);
  const widget = advancedWidget(node);
  if (widget) {
    widget.value = value;
  }
}

function ensureAdvancedWidgetValue(node) {
  const widget = advancedWidget(node);
  if (!widget) {
    return;
  }
  if (node.__easyuseAnimaPendingAdvancedFieldsValue) {
    widget.value = node.__easyuseAnimaPendingAdvancedFieldsValue;
    syncAdvancedFieldsBackup(node, widget.value);
    delete node.__easyuseAnimaPendingAdvancedFieldsValue;
    return;
  }
  const backup = advancedFieldsBackup(node);
  const widgetValue = String(widget.value || "");
  if (
    backup
    && (!widgetValue.trim() || widgetValue === advancedDefaultFieldsValue())
  ) {
    widget.value = backup;
  }
}

function hideAdvancedInternalWidget(node, name) {
  const widget = findWidget(node, name);
  if (!widget) {
    return;
  }
  widget.__easyuseAnimaAdvancedHidden = true;
  widget.hidden = true;
  widget.serialize = true;
  widget.options ||= {};
  widget.options.hidden = true;
  widget.computeSize = () => [0, 0];
  widget.draw = () => {};
  const input = findInputEl(widget);
  if (input) {
    input.style.display = "none";
    input.style.pointerEvents = "none";
    input.tabIndex = -1;
  }
  node.__easyuseAnimaHiddenWidgets ||= {};
  node.__easyuseAnimaHiddenWidgets[name] = widget;
  node.setDirtyCanvas?.(true, true);
}

function hideAdvancedControlWidgets(node) {
  for (const name of ADVANCED_INTERNAL_WIDGET_NAMES) {
    hideAdvancedInternalWidget(node, name);
  }
}

function removeAdvancedInternalInputSockets(node) {
  if (!Array.isArray(node.inputs)) {
    return;
  }
  for (let index = node.inputs.length - 1; index >= 0; index -= 1) {
    const input = node.inputs[index];
    const widgetName = input?.widget?.name || input?.name;
    if (!ADVANCED_INTERNAL_WIDGET_NAMES.has(widgetName)) {
      continue;
    }
    if (input?.link != null) {
      node.disconnectInput?.(index);
    }
    node.removeInput?.(index);
  }
}

function normalizeAdvancedField(field, index = 0) {
  const pane = field?.pane === "negative" ? "negative" : "positive";
  let type = ADVANCED_FIELD_TYPES.includes(field?.type) ? field.type : "general";
  if (pane === "negative" && type === "trigger") {
    type = "general";
  }
  const label = String(field?.label || ADVANCED_FIELD_LABELS[type] || "General Tags");
  return {
    id: String(field?.id || `${pane}_${type}_${index + 1}`),
    pane,
    type,
    label,
    text: String(field?.text || ""),
    height: Math.max(42, Math.round(Number(field?.height) || 72)),
    heightMode: field?.heightMode === "manual" ? "manual" : "auto",
    enabled: field?.enabled !== false,
    pin: type === "trigger" ? field?.pin !== false : false,
  };
}

function parseAdvancedFields(node) {
  ensureAdvancedWidgetValue(node);
  const widget = advancedWidget(node);
  const sourceValue = String(widget?.value || advancedFieldsBackup(node) || "[]");
  try {
    const parsed = JSON.parse(sourceValue);
    if (Array.isArray(parsed) && parsed.length) {
      const fields = [];
      const seenNaiaPanes = new Set();
      let seenTrigger = false;
      parsed.forEach((field, index) => {
        const normalized = normalizeAdvancedField(field, index);
        if (normalized.type === "naia") {
          if (seenNaiaPanes.has(normalized.pane)) {
            return;
          }
          seenNaiaPanes.add(normalized.pane);
        }
        if (normalized.type === "trigger") {
          if (seenTrigger) {
            return;
          }
          seenTrigger = true;
          normalized.pane = "positive";
        }
        fields.push(normalized);
      });
      return fields.length ? fields : advancedDefaultFields();
    }
  } catch {
    // Fall through to default fields.
  }
  return advancedDefaultFields();
}

function collectAdvancedEditorFields(node) {
  const fields = (node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node))
    .map((field, index) => normalizeAdvancedField(field, index));
  const editor = node.__easyuseAnimaAdvancedEditorEl;
  if (!editor) {
    return fields;
  }

  const byId = new Map(fields.map((field) => [field.id, field]));
  editor.querySelectorAll("textarea[data-easyuse-anima-advanced-field-id]").forEach((textarea) => {
    const id = textarea.dataset.easyuseAnimaAdvancedFieldId;
    const field = byId.get(id);
    if (!field) {
      return;
    }
    field.text = textarea.value;
    const height = Number.parseInt(textarea.style.height || "", 10);
    if (Number.isFinite(height) && height > 0) {
      field.height = Math.max(42, height);
    }
  });
  return fields;
}

function writeAdvancedFields(node, fields, { render = false, syncInputs = true } = {}) {
  const widget = advancedWidget(node);
  if (!widget) {
    return;
  }
  widget.value = JSON.stringify(fields.map((field, index) => normalizeAdvancedField(field, index)));
  syncAdvancedFieldsBackup(node, widget.value);
  node.__easyuseAnimaAdvancedFields = fields;
  if (syncInputs) {
    syncAdvancedFieldInputs(node, fields);
  }
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  if (render) {
    renderAdvancedEditor(node);
  }
}

function applyAdvancedNaiaGeneralAutoToggle(node, fields) {
  if (!PROMPT_STUDIO_SETTINGS.naiaGeneralAboveAutoToggle || !Array.isArray(fields)) {
    return false;
  }
  const naiaIndex = fields.findIndex(
    (field) => field?.pane === "positive" && field?.type === "naia",
  );
  if (naiaIndex < 0) {
    return false;
  }
  const naiaEnabled = fields[naiaIndex]?.enabled !== false;
  let changed = false;
  for (let index = 0; index < naiaIndex; index += 1) {
    const field = fields[index];
    if (field?.pane !== "positive" || field?.type !== "general") {
      continue;
    }
    const nextEnabled = !naiaEnabled;
    if ((field.enabled !== false) !== nextEnabled) {
      field.enabled = nextEnabled;
      changed = true;
    }
  }
  return changed;
}

function advancedFieldInputName(field) {
  const raw = String(field?.id || "field")
    .replace(/[^a-zA-Z0-9_]/g, "_")
    .replace(/^_+|_+$/g, "");
  return `${ADVANCED_FIELD_SOCKET_PREFIX}${raw || "field"}`;
}

function advancedFieldIndexLabel(fields, field) {
  const paneFields = (fields || []).filter((item) => item.pane === field.pane);
  const paneIndex = paneFields.findIndex((item) => item.id === field.id);
  const number = Math.max(0, paneIndex) + 1;
  return field.pane === "negative" ? `neg${number}` : `${number}`;
}

function isAdvancedFieldInput(input) {
  return !!input?.__easyuseAnimaAdvancedFieldInput
    || String(input?.name || "").startsWith(ADVANCED_FIELD_SOCKET_PREFIX);
}

function updateNodeInputLinkSlots(node) {
  if (!node?.inputs || !app.graph?.links) {
    return;
  }
  const expectedLinks = new Set();
  node.inputs.forEach((input, index) => {
    if (input?.link == null) {
      return;
    }
    const link = app.graph.links[input.link];
    if (link) {
      expectedLinks.add(Number(input.link));
      link.target_id = node.id;
      link.target_slot = index;
    }
  });

  for (const [rawLinkId, link] of Object.entries(app.graph.links)) {
    const linkId = Number(rawLinkId);
    if (!link || Number(link.target_id) !== Number(node.id)) {
      continue;
    }
    const targetInput = node.inputs?.[link.target_slot];
    if (targetInput?.link === linkId) {
      continue;
    }
    const originNode = app.graph.getNodeById?.(link.origin_id);
    const originOutput = originNode?.outputs?.[link.origin_slot];
    if (Array.isArray(originOutput?.links)) {
      originOutput.links = originOutput.links.filter((id) => Number(id) !== linkId);
    }
    if (!expectedLinks.has(linkId)) {
      delete app.graph.links[rawLinkId];
    }
  }
}

function syncAdvancedFieldInputs(node, fields) {
  if (!node || typeof node.addInput !== "function") {
    return;
  }

  const wanted = new Map();
  (fields || []).forEach((field) => {
    if (field?.type === "naia") {
      return;
    }
    wanted.set(advancedFieldInputName(field), { field, indexLabel: advancedFieldIndexLabel(fields, field) });
  });

  for (let index = (node.inputs?.length || 0) - 1; index >= 0; index -= 1) {
    const input = node.inputs[index];
    if (isAdvancedFieldInput(input) && !wanted.has(input.name)) {
      node.removeInput?.(index);
    }
  }

  for (const [name, { field, indexLabel }] of wanted) {
    let input = node.inputs?.find((item) => item.name === name);
    if (!input) {
      node.addInput(name, "STRING");
      input = node.inputs?.find((item) => item.name === name);
    }
    if (!input) {
      continue;
    }
    input.type = "STRING";
    input.label = `${indexLabel}. ${advancedFieldLabel(field)}`;
    input.__easyuseAnimaAdvancedFieldInput = true;
    input.__easyuseAnimaAdvancedFieldId = field.id;
  }

  const fieldInputs = [];
  for (const [name] of wanted) {
    const input = node.inputs?.find((item) => item.name === name);
    if (input) {
      fieldInputs.push(input);
    }
  }
  const otherInputs = (node.inputs || []).filter((input) => !isAdvancedFieldInput(input));
  node.inputs = [...fieldInputs, ...otherInputs];
  updateNodeInputLinkSlots(node);
}

function advancedFieldInputLinked(node, field) {
  const name = advancedFieldInputName(field);
  return !!node.inputs?.some((input) => input.name === name && input.link != null);
}

function advancedFieldDisplayText(node, field) {
  const name = advancedFieldInputName(field);
  const values = node.__easyuseAnimaAdvancedFieldInputValues || {};
  if (advancedFieldInputLinked(node, field) && Object.prototype.hasOwnProperty.call(values, name)) {
    return String(values[name] ?? "");
  }
  return String(field?.text || "");
}

function mergeAdvancedFieldInputValues(node, fields, values) {
  if (!values || typeof values !== "object" || !Array.isArray(fields)) {
    return false;
  }
  let changed = false;
  for (const field of fields) {
    const name = advancedFieldInputName(field);
    if (!Object.prototype.hasOwnProperty.call(values, name)) {
      continue;
    }
    const text = String(values[name] ?? "");
    if (field.text !== text) {
      field.text = text;
      changed = true;
    }
  }
  return changed;
}

function pruneDisconnectedAdvancedFieldInputValues(node) {
  const values = node.__easyuseAnimaAdvancedFieldInputValues;
  if (!values || typeof values !== "object") {
    return;
  }
  const linkedNames = new Set(
    (node.inputs || [])
      .filter((input) => isAdvancedFieldInput(input) && input.link != null)
      .map((input) => input.name),
  );
  for (const name of Object.keys(values)) {
    if (!linkedNames.has(name)) {
      delete values[name];
    }
  }
}

function advancedFieldLabel(field) {
  const base = ADVANCED_FIELD_LABELS[field.type] || "General Tags";
  const localizedBase = psText(`advanced.field.${field.type}`) || base;
  return field.label && field.label !== base && field.label !== localizedBase
    ? `${localizedBase} - ${field.label}`
    : localizedBase;
}

function setAdvancedControlValue(node, name, value) {
  const widget = findWidget(node, name);
  if (!widget || isWidgetInputLinked(node, name)) {
    return false;
  }
  widget.value = !!value;
  widget.callback?.(widget.value);
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  return true;
}

function setAdvancedWidgetValue(node, name, value) {
  const widget = findWidget(node, name);
  if (!widget) {
    return false;
  }
  widget.value = String(value ?? "");
  widget.callback?.(widget.value);
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  return true;
}

function gcdInt(a, b) {
  let x = Math.abs(Math.trunc(a || 0));
  let y = Math.abs(Math.trunc(b || 0));
  while (y) {
    const next = x % y;
    x = y;
    y = next;
  }
  return x || 1;
}

function resolutionRatioLabel(width, height) {
  const divisor = gcdInt(width, height);
  return `${Math.trunc(width / divisor)}:${Math.trunc(height / divisor)}`;
}

function advancedResolutionLabel(width, height) {
  return `${width} * ${height} (${resolutionRatioLabel(width, height)})`;
}

function advancedResolutionOptions(bucket) {
  const values = ADVANCED_RESOLUTION_BUCKETS[bucket] || ADVANCED_RESOLUTION_BUCKETS[DEFAULT_ADVANCED_RESOLUTION_BUCKET];
  return [...values]
    .sort((a, b) => (a[0] / a[1]) - (b[0] / b[1]) || a[0] - b[0] || a[1] - b[1])
    .map(([width, height]) => advancedResolutionLabel(width, height));
}

function normalizeAdvancedResolutionBucket(value) {
  const bucket = String(value || "").trim();
  if (bucket === CUSTOM_ADVANCED_RESOLUTION_BUCKET || bucket === NAIA_ADVANCED_RESOLUTION_BUCKET) {
    return bucket;
  }
  return Object.prototype.hasOwnProperty.call(ADVANCED_RESOLUTION_BUCKETS, bucket)
    ? bucket
    : DEFAULT_ADVANCED_RESOLUTION_BUCKET;
}

function resolutionRatioFromLabel(value) {
  const match = String(value || "").match(/(\d+)\s*(?:\*|x|×)\s*(\d+)/);
  if (!match) {
    return "";
  }
  return resolutionRatioLabel(Number(match[1]), Number(match[2]));
}

function normalizeAdvancedResolutionSize(bucket, value) {
  if (bucket === CUSTOM_ADVANCED_RESOLUTION_BUCKET || bucket === NAIA_ADVANCED_RESOLUTION_BUCKET) {
    return String(value || DEFAULT_ADVANCED_RESOLUTION_SIZE);
  }
  const options = advancedResolutionOptions(bucket);
  const raw = String(value || "").trim();
  if (options.includes(raw)) {
    return raw;
  }
  const sameRatio = resolutionRatioFromLabel(raw);
  if (sameRatio) {
    const matched = options.find((option) => resolutionRatioFromLabel(option) === sameRatio);
    if (matched) {
      return matched;
    }
  }
  return options.includes(DEFAULT_ADVANCED_RESOLUTION_SIZE)
    ? DEFAULT_ADVANCED_RESOLUTION_SIZE
    : options[0];
}

function snapResolution32(value, fallback = 1024) {
  const raw = Number.parseInt(value, 10);
  const base = Number.isFinite(raw) && raw > 0 ? raw : fallback;
  return Math.max(32, Math.round(base / 32) * 32);
}

function advancedCustomResolution(node) {
  return {
    width: snapResolution32(findWidget(node, "resolution_custom_width")?.value, 1024),
    height: snapResolution32(findWidget(node, "resolution_custom_height")?.value, 1024),
  };
}

function setAdvancedCustomResolution(node, width, height, { normalize = false } = {}) {
  const nextWidth = normalize ? snapResolution32(width, 1024) : String(width || "");
  const nextHeight = normalize ? snapResolution32(height, 1024) : String(height || "");
  setAdvancedWidgetValue(node, "resolution_custom_width", nextWidth);
  setAdvancedWidgetValue(node, "resolution_custom_height", nextHeight);
  if (normalize) {
    setAdvancedWidgetValue(node, "resolution_size", advancedResolutionLabel(nextWidth, nextHeight));
  }
}

function createAdvancedControlBar(node) {
  const bar = document.createElement("div");
  bar.className = "easyuse-anima-advanced-controlbar";
  for (const control of ADVANCED_CONTROL_WIDGETS) {
    if (control.showInControlBar === false) {
      continue;
    }
    const widget = findWidget(node, control.name);
    if (!widget) {
      continue;
    }
    const linked = isWidgetInputLinked(node, control.name);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "easyuse-anima-advanced-toggle";
    button.classList.toggle("is-on", !!widget.value);
    button.classList.toggle("is-linked", linked);
    const title = psText(control.titleKey);
    button.textContent = psText(control.labelKey);
    button.title = linked ? `${title} ${psText("advanced.linkedInputSuffix")}` : title;
    button.disabled = linked;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      setAdvancedControlValue(node, control.name, !widget.value);
      renderAdvancedEditor(node);
    });
    bar.append(button);
  }
  return bar;
}

function normalizeAdvancedWildcardMode(value) {
  return ADVANCED_WILDCARD_MODES.includes(String(value || ""))
    ? String(value)
    : ADVANCED_WILDCARD_DEFAULT_MODE;
}

function normalizeAdvancedSeedControl(value) {
  return ADVANCED_WILDCARD_SEED_CONTROLS.includes(String(value || ""))
    ? String(value)
    : "fixed";
}

function createAdvancedWildcardBar(node) {
  const modeWidget = findWidget(node, "wildcard_mode");
  const seedWidget = findWidget(node, "wildcard_seed");
  const controlWidget = findWidget(node, "wildcard_seed_after_generate");
  if (!modeWidget || !seedWidget || !controlWidget) {
    return document.createDocumentFragment();
  }

  const row = document.createElement("div");
  row.className = "easyuse-anima-advanced-wildcardbar";
  row.title = psText("advanced.wildcardTitle");

  const modeSelect = document.createElement("select");
  modeSelect.setAttribute("aria-label", psText("advanced.wildcard"));
  const modeValue = normalizeAdvancedWildcardMode(modeWidget.value);
  for (const mode of ADVANCED_WILDCARD_MODES) {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = mode;
    option.selected = mode === modeValue;
    modeSelect.append(option);
  }

  const seedInput = document.createElement("input");
  seedInput.type = "number";
  seedInput.min = "0";
  seedInput.step = "1";
  seedInput.value = String(seedWidget.value ?? "0");
  seedInput.setAttribute("aria-label", psText("advanced.wildcardSeed"));

  const controlSelect = document.createElement("select");
  controlSelect.setAttribute("aria-label", psText("advanced.wildcardSeedControl"));
  const controlValue = modeValue === "순차"
    ? "increment"
    : normalizeAdvancedSeedControl(controlWidget.value);
  for (const control of ADVANCED_WILDCARD_SEED_CONTROLS) {
    const option = document.createElement("option");
    option.value = control;
    option.textContent = control;
    option.selected = control === controlValue;
    controlSelect.append(option);
  }
  controlSelect.disabled = modeValue === "순차";

  const syncMode = () => {
    const nextMode = normalizeAdvancedWildcardMode(modeSelect.value);
    setAdvancedWidgetValue(node, "wildcard_mode", nextMode);
    if (nextMode === "순차") {
      setAdvancedWidgetValue(node, "wildcard_seed_after_generate", "increment");
    }
    renderAdvancedEditor(node);
  };
  const syncSeed = () => {
    const seed = Math.max(0, Math.trunc(Number(seedInput.value) || 0));
    seedInput.value = String(seed);
    setAdvancedWidgetValue(node, "wildcard_seed", seed);
  };
  const syncControl = () => {
    setAdvancedWidgetValue(node, "wildcard_seed_after_generate", normalizeAdvancedSeedControl(controlSelect.value));
  };

  modeSelect.addEventListener("change", syncMode);
  seedInput.addEventListener("change", syncSeed);
  seedInput.addEventListener("blur", syncSeed);
  controlSelect.addEventListener("change", syncControl);

  row.append(modeSelect, seedInput, controlSelect);
  return row;
}

function createAdvancedResolutionBar(node) {
  const bucketWidget = findWidget(node, "resolution_bucket");
  const sizeWidget = findWidget(node, "resolution_size");
  if (!bucketWidget || !sizeWidget) {
    return document.createDocumentFragment();
  }

  const bucketValue = normalizeAdvancedResolutionBucket(bucketWidget.value);
  const customResolution = advancedCustomResolution(node);
  const sizeValue = bucketValue === CUSTOM_ADVANCED_RESOLUTION_BUCKET || bucketValue === NAIA_ADVANCED_RESOLUTION_BUCKET
    ? advancedResolutionLabel(customResolution.width, customResolution.height)
    : normalizeAdvancedResolutionSize(bucketValue, sizeWidget.value);
  if (bucketWidget.value !== bucketValue) {
    setAdvancedWidgetValue(node, "resolution_bucket", bucketValue);
  }
  if (sizeWidget.value !== sizeValue) {
    setAdvancedWidgetValue(node, "resolution_size", sizeValue);
  }

  const row = document.createElement("div");
  row.className = "easyuse-anima-advanced-resolutionbar";
  row.title = psText("advanced.resolutionTitle");

  const bucketSelect = document.createElement("select");
  bucketSelect.setAttribute("aria-label", psText("advanced.resolutionBucket"));
  for (const bucket of Object.keys(ADVANCED_RESOLUTION_BUCKETS)) {
    const option = document.createElement("option");
    option.value = bucket;
    option.textContent = bucket;
    option.selected = bucket === bucketValue;
    bucketSelect.append(option);
  }
  const naiaOption = document.createElement("option");
  naiaOption.value = NAIA_ADVANCED_RESOLUTION_BUCKET;
  naiaOption.textContent = NAIA_ADVANCED_RESOLUTION_BUCKET;
  naiaOption.selected = bucketValue === NAIA_ADVANCED_RESOLUTION_BUCKET;
  bucketSelect.append(naiaOption);
  const customOption = document.createElement("option");
  customOption.value = CUSTOM_ADVANCED_RESOLUTION_BUCKET;
  customOption.textContent = CUSTOM_ADVANCED_RESOLUTION_BUCKET;
  customOption.selected = bucketValue === CUSTOM_ADVANCED_RESOLUTION_BUCKET;
  bucketSelect.append(customOption);

  const valueBox = document.createElement("div");
  const renderPresetSelect = (bucket, selected) => {
    valueBox.innerHTML = "";
    const sizeSelect = document.createElement("select");
    sizeSelect.setAttribute("aria-label", psText("advanced.resolutionSize"));
    for (const label of advancedResolutionOptions(bucket)) {
      const option = document.createElement("option");
      option.value = label;
      option.textContent = label;
      option.selected = label === selected;
      sizeSelect.append(option);
    }
    sizeSelect.addEventListener("change", () => {
      setAdvancedWidgetValue(node, "resolution_size", normalizeAdvancedResolutionSize(bucketSelect.value, sizeSelect.value));
      scheduleAdvancedLayout(node, "settings");
    });
    valueBox.append(sizeSelect);
  };
  const renderCustomInputs = () => {
    valueBox.innerHTML = "";
    valueBox.className = "easyuse-anima-advanced-resolution-custom";
    const widthInput = document.createElement("input");
    widthInput.type = "number";
    widthInput.min = "32";
    widthInput.step = "32";
    widthInput.value = String(advancedCustomResolution(node).width);
    widthInput.setAttribute("aria-label", psText("advanced.customWidth"));
    const separator = document.createElement("span");
    separator.textContent = "×";
    const heightInput = document.createElement("input");
    heightInput.type = "number";
    heightInput.min = "32";
    heightInput.step = "32";
    heightInput.value = String(advancedCustomResolution(node).height);
    heightInput.setAttribute("aria-label", psText("advanced.customHeight"));
    const syncRaw = () => {
      setAdvancedCustomResolution(node, widthInput.value, heightInput.value);
    };
    const normalize = () => {
      const width = snapResolution32(widthInput.value, 1024);
      const height = snapResolution32(heightInput.value, 1024);
      widthInput.value = String(width);
      heightInput.value = String(height);
      setAdvancedCustomResolution(node, width, height, { normalize: true });
    };
    widthInput.addEventListener("input", syncRaw);
    heightInput.addEventListener("input", syncRaw);
    widthInput.addEventListener("change", normalize);
    heightInput.addEventListener("change", normalize);
    widthInput.addEventListener("blur", normalize);
    heightInput.addEventListener("blur", normalize);
    valueBox.append(widthInput, separator, heightInput);
    setAdvancedCustomResolution(node, widthInput.value, heightInput.value, { normalize: true });
  };
  const renderNaiaResolution = () => {
    valueBox.innerHTML = "";
    valueBox.className = "easyuse-anima-advanced-resolution-custom";
    const current = advancedCustomResolution(node);
    const label = document.createElement("span");
    label.textContent = advancedResolutionLabel(current.width, current.height);
    label.title = psText("advanced.naiaResolutionTitle");
    valueBox.append(label);
    setAdvancedWidgetValue(node, "resolution_size", advancedResolutionLabel(current.width, current.height));
  };
  const fillSizeOptions = (bucket, selected) => {
    valueBox.className = "";
    if (bucket === NAIA_ADVANCED_RESOLUTION_BUCKET) {
      renderNaiaResolution();
      return;
    }
    if (bucket === CUSTOM_ADVANCED_RESOLUTION_BUCKET) {
      renderCustomInputs();
      return;
    }
    renderPresetSelect(bucket, selected);
  };
  fillSizeOptions(bucketValue, sizeValue);

  bucketSelect.addEventListener("change", () => {
    const nextBucket = normalizeAdvancedResolutionBucket(bucketSelect.value);
    const nextSize = nextBucket === CUSTOM_ADVANCED_RESOLUTION_BUCKET || nextBucket === NAIA_ADVANCED_RESOLUTION_BUCKET
      ? advancedResolutionLabel(advancedCustomResolution(node).width, advancedCustomResolution(node).height)
      : normalizeAdvancedResolutionSize(nextBucket, sizeWidget.value);
    setAdvancedWidgetValue(node, "resolution_bucket", nextBucket);
    setAdvancedWidgetValue(node, "resolution_size", nextSize);
    if (nextBucket === NAIA_ADVANCED_RESOLUTION_BUCKET) {
      setAdvancedControlValue(node, "consume_naia_on_queue", true);
      setAdvancedControlValue(node, "use_naia", true);
    }
    fillSizeOptions(nextBucket, nextSize);
    scheduleAdvancedLayout(node, "settings");
    scheduleAdvancedHighlights(node, { classify: false });
  });

  row.append(bucketSelect, valueBox);
  return row;
}

function advancedPaneFields(node, pane) {
  return (node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node))
    .filter((field) => field.pane === pane);
}

function hasAdvancedNaia(node, pane) {
  return (node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node))
    .some((field) => field.pane === pane && field.type === "naia");
}

function hasPositiveNaia(node) {
  return (node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node))
    .some((field) => field.pane === "positive" && field.type === "naia");
}

function hasPositiveTrigger(node) {
  return (node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node))
    .some((field) => field.pane === "positive" && field.type === "trigger");
}

function advancedEditorWidth(node) {
  return Math.max(280, Math.round((Number(node?.size?.[0]) || 420) - 18));
}

function measureAdvancedEditorHeight(editor) {
  if (!editor) {
    return 0;
  }
  return Math.ceil(Math.max(
    Number(editor.scrollHeight) || 0,
    Number(editor.offsetHeight) || 0,
    measureAdvancedEditorContentHeight(editor),
  ));
}

function measureAdvancedEditorContentHeight(editor) {
  if (!editor) {
    return 0;
  }
  const childrenHeight = [...editor.children].reduce((total, child) => {
    if (!(child instanceof HTMLElement)) {
      return total;
    }
    const style = getComputedStyle(child);
    const marginTop = Number.parseFloat(style?.marginTop || "") || 0;
    const marginBottom = Number.parseFloat(style?.marginBottom || "") || 0;
    return total + marginTop + Number(child.offsetHeight || 0) + marginBottom;
  }, 0);
  return Math.ceil(Math.max(childrenHeight, 0));
}

function advancedEditorTextareas(editor) {
  return [...(editor?.querySelectorAll?.("textarea[data-easyuse-anima-advanced-field-id]") || [])];
}

function advancedTextareaPixelMetric(textarea, property) {
  const style = textarea instanceof HTMLElement ? getComputedStyle(textarea) : null;
  return Number.parseFloat(style?.[property] || "") || 0;
}

function advancedTextareaTwoLineHeight(textarea) {
  const style = textarea instanceof HTMLElement ? getComputedStyle(textarea) : null;
  const fontSize = Number.parseFloat(style?.fontSize || "") || 12;
  const lineHeightRaw = Number.parseFloat(style?.lineHeight || "");
  const lineHeight = Number.isFinite(lineHeightRaw) && lineHeightRaw > 0 ? lineHeightRaw : fontSize * 1.35;
  const verticalPadding =
    advancedTextareaPixelMetric(textarea, "paddingTop")
    + advancedTextareaPixelMetric(textarea, "paddingBottom");
  const verticalBorder =
    advancedTextareaPixelMetric(textarea, "borderTopWidth")
    + advancedTextareaPixelMetric(textarea, "borderBottomWidth");
  return Math.ceil(lineHeight * 2 + verticalPadding + verticalBorder);
}

function advancedTextareaContentHeight(textarea) {
  if (!(textarea instanceof HTMLTextAreaElement)) {
    return 0;
  }
  const previousHeight = textarea.style.height;
  const previousMinHeight = textarea.style.minHeight;
  const previousOverflow = textarea.style.overflowY;
  textarea.style.minHeight = "0px";
  textarea.style.height = "auto";
  textarea.style.overflowY = "hidden";
  const contentHeight = Math.ceil(
    (Number(textarea.scrollHeight) || 0)
    + advancedTextareaPixelMetric(textarea, "borderTopWidth")
    + advancedTextareaPixelMetric(textarea, "borderBottomWidth"),
  );
  textarea.style.height = previousHeight;
  textarea.style.minHeight = previousMinHeight;
  textarea.style.overflowY = previousOverflow;
  return contentHeight;
}

function advancedTextareaMinimumHeight(textarea) {
  return Math.max(
    46,
    advancedTextareaTwoLineHeight(textarea),
  );
}

function advancedTextareaCurrentHeight(textarea) {
  return Math.max(
    advancedTextareaMinimumHeight(textarea),
    Math.ceil(Number.parseFloat(textarea?.style?.height || "") || 0),
    Math.ceil(Number(textarea?.offsetHeight) || 0),
    Math.ceil(Number(textarea?.clientHeight) || 0),
  );
}

function advancedTextareaHeightTotal(textareas, measure) {
  return textareas.reduce((sum, textarea) => sum + measure(textarea), 0);
}

function advancedEditorFixedHeight(editor, textareas = advancedEditorTextareas(editor)) {
  const editorHeight = measureAdvancedEditorContentHeight(editor);
  const textareaTotal = advancedTextareaHeightTotal(textareas, advancedTextareaCurrentHeight);
  return Math.max(0, editorHeight - textareaTotal);
}

function advancedEditorContentMinimumHeight(node) {
  const editor = node?.__easyuseAnimaAdvancedEditorEl;
  if (!editor) {
    return ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT;
  }
  const textareas = advancedEditorTextareas(editor);
  const fixedHeight = advancedEditorFixedHeight(editor, textareas);
  const textareaMinTotal = advancedTextareaHeightTotal(textareas, advancedTextareaMinimumHeight);
  return Math.ceil(Math.max(ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT, fixedHeight + textareaMinTotal));
}

function advancedEditorAutoViewportCap() {
  const viewportHeight = Number(globalThis.innerHeight) || 0;
  const viewportCap = viewportHeight > 0 ? Math.floor(viewportHeight * 0.72) : ADVANCED_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT;
  return Math.ceil(Math.max(
    ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT,
    Math.min(ADVANCED_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT, viewportCap),
  ));
}

function advancedEditorMinimumHeight(node) {
  const contentMinimum = advancedEditorContentMinimumHeight(node);
  return Math.ceil(Math.max(
    ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT,
    Math.min(contentMinimum, advancedEditorAutoViewportCap()),
  ));
}

function advancedAvailableEditorViewportHeight(node) {
  const minimumHeight = advancedEditorMinimumHeight(node);
  const nodeHeight = Number(node?.size?.[1]) || 0;
  const chromeOffset = advancedNodeChromeOffset(node, minimumHeight);
  const availableHeight = Math.max(0, nodeHeight - chromeOffset);
  return Math.ceil(Math.max(minimumHeight, availableHeight));
}

function advancedEditorWidgetHeight(node) {
  if (node?.__easyuseAnimaAdvancedEditorEl?.isConnected) {
    return advancedAvailableEditorViewportHeight(node);
  }
  return Math.ceil(Math.max(
    advancedEditorMinimumHeight(node),
    Number(node?.__easyuseAnimaAdvancedWidgetHeight) || 0,
  ));
}

function advancedEditorWidget(node) {
  return node?.__easyuseAnimaAdvancedDomWidget
    || node?.widgets?.find?.((widget) => widget?.name === "easyuse_anima_advanced_editor")
    || null;
}

function advancedNodeChromeOffset(node, editorHeight = measureAdvancedEditorContentHeight(node?.__easyuseAnimaAdvancedEditorEl)) {
  const widget = advancedEditorWidget(node);
  const widgetY = Math.max(
    Number(widget?.last_y) || 0,
    Number(widget?.y) || 0,
  );
  return Math.ceil(Math.max(72, widgetY + 12));
}

function advancedMinimumNodeHeight(node) {
  const editor = node?.__easyuseAnimaAdvancedEditorEl;
  if (!editor) {
    return ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT;
  }
  const viewportMinimum = advancedEditorMinimumHeight(node);
  const chromeOffset = advancedNodeChromeOffset(node, viewportMinimum);
  return Math.ceil(Math.max(
    ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT,
    viewportMinimum + chromeOffset,
  ));
}

function clampAdvancedNodeToMinimumHeight(node) {
  if (!node?.size || typeof node.setSize !== "function") {
    return false;
  }
  const currentWidth = Number(node.size[0]) || 360;
  const currentHeight = Number(node.size[1]) || 0;
  const minimumHeight = advancedMinimumNodeHeight(node);
  if (currentHeight >= minimumHeight - 1) {
    return false;
  }
  node.__easyuseAnimaApplyingLayout = true;
  try {
    node.setSize([currentWidth, minimumHeight]);
  } finally {
    node.__easyuseAnimaApplyingLayout = false;
  }
  return true;
}

function advancedFieldByTextarea(node, textarea) {
  const id = String(textarea?.dataset?.easyuseAnimaAdvancedFieldId || "");
  if (!id) {
    return null;
  }
  return (node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node))
    .find((field) => field.id === id) || null;
}

function setAdvancedTextareaHeight(node, textarea, height, options = {}) {
  const requiredHeight = Math.max(
    advancedTextareaMinimumHeight(textarea),
    advancedTextareaContentHeight(textarea),
  );
  const nextHeight = Math.max(requiredHeight, Math.round(Number(height) || 0));
  textarea.style.minHeight = `${requiredHeight}px`;
  textarea.style.height = `${nextHeight}px`;
  textarea.style.overflowY = "hidden";
  let field = null;
  if (options.syncField !== false || options.refreshHighlight !== false) {
    field = advancedFieldByTextarea(node, textarea);
  }
  if (options.syncField !== false && field) {
    field.height = nextHeight;
  }
  if (options.refreshHighlight !== false) {
    updateAdvancedFieldHighlight(node, field, textarea);
  }
  return nextHeight;
}

function clearAdvancedResizeEndListeners(node) {
  const handler = node?.__easyuseAnimaAdvancedResizeEndHandler;
  if (!handler) {
    return;
  }
  document.removeEventListener("pointerup", handler, true);
  document.removeEventListener("pointercancel", handler, true);
  document.removeEventListener("mouseup", handler, true);
  node.__easyuseAnimaAdvancedResizeEndHandler = null;
}

function finalizeAdvancedResize(node) {
  if (node) {
    clearTimeout(node.__easyuseAnimaAdvancedResizeFinalizeTimer);
    node.__easyuseAnimaAdvancedResizeFinalizeTimer = null;
    clearAdvancedResizeEndListeners(node);
  }
  if (
    !node
    || !node.graph
    || !node.__easyuseAnimaAdvancedEditorEl
    || !node.__easyuseAnimaAdvancedEditorEl.isConnected
  ) {
    return;
  }
  updateAdvancedEditorWidth(node);
  clampAdvancedNodeToMinimumHeight(node);
  scheduleAdvancedLayout(node, "resize");
}

function installAdvancedResizeEndListeners(node) {
  if (!node || node.__easyuseAnimaAdvancedResizeEndHandler) {
    return;
  }
  const handler = () => finalizeAdvancedResize(node);
  node.__easyuseAnimaAdvancedResizeEndHandler = handler;
  document.addEventListener("pointerup", handler, true);
  document.addEventListener("pointercancel", handler, true);
  document.addEventListener("mouseup", handler, true);
}

function scheduleAdvancedResizeFinalize(node) {
  if (!node?.__easyuseAnimaAdvancedEditorEl?.isConnected) {
    finalizeAdvancedResize(node);
    return;
  }
  installAdvancedResizeEndListeners(node);
  clearTimeout(node.__easyuseAnimaAdvancedResizeFinalizeTimer);
  node.__easyuseAnimaAdvancedResizeFinalizeTimer = setTimeout(() => {
    finalizeAdvancedResize(node);
  }, 120);
}

function updateAdvancedEditorWidth(node) {
  const editor = node?.__easyuseAnimaAdvancedEditorEl;
  if (!editor) {
    return;
  }
  const width = Number(node?.size?.[0]) || 360;
  const editorWidth = advancedEditorWidth(node);
  editor.style.width = `${editorWidth}px`;
  editor.style.maxWidth = `${editorWidth}px`;
  editor.classList.toggle("is-narrow", width < 620);
}

function applyAdvancedLayout(node, reason = "layout") {
  const editor = node?.__easyuseAnimaAdvancedEditorEl;
  if (!editor || !node.size) {
    return;
  }
  if (node.__easyuseAnimaApplyingLayout) {
    return;
  }

  node.__easyuseAnimaApplyingLayout = true;
  try {
    updateAdvancedEditorWidth(node);

    const currentWidth = Number(node.size[0]) || 360;
    const currentHeight = Number(node.size[1]) || 0;
    const minimumHeight = advancedMinimumNodeHeight(node);
    const widgetHeight = advancedEditorWidgetHeight(node);
    editor.style.height = `${widgetHeight}px`;
    editor.style.maxHeight = `${widgetHeight}px`;
    node.__easyuseAnimaAdvancedWidgetHeight = widgetHeight;
    node.__easyuseAnimaAdvancedLastEditorHeight = widgetHeight;
    node.__easyuseAnimaAdvancedLastLayoutReason = reason;

    if (typeof node.setSize === "function" && currentHeight < minimumHeight - 1) {
      node.setSize([currentWidth, minimumHeight]);
    }

    app.graph?.setDirtyCanvas?.(true, true);
    requestAnimationFrame(() => app.graph?.setDirtyCanvas?.(true, true));
  } finally {
    node.__easyuseAnimaApplyingLayout = false;
  }
  scheduleAdvancedHighlights(node, { classify: reason !== "resize" });
}

const ADVANCED_LAYOUT_REASON_PRIORITY = {
  layout: 0,
  render: 1,
  textarea: 1,
  connections: 1,
  executed: 1,
  settings: 1,
  resize: 3,
};

function advancedLayoutReasonPriority(reason) {
  return ADVANCED_LAYOUT_REASON_PRIORITY[reason] ?? 0;
}

function scheduleAdvancedLayout(node, reason = "layout") {
  if (!node?.__easyuseAnimaAdvancedEditorEl) {
    return;
  }
  updateAdvancedEditorWidth(node);
  const currentReason = node.__easyuseAnimaAdvancedLayoutReason || "layout";
  if (
    !node.__easyuseAnimaAdvancedLayoutScheduled
    || advancedLayoutReasonPriority(reason) >= advancedLayoutReasonPriority(currentReason)
  ) {
    node.__easyuseAnimaAdvancedLayoutReason = reason;
  }
  if (node.__easyuseAnimaAdvancedLayoutScheduled) {
    return;
  }
  node.__easyuseAnimaAdvancedLayoutScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaAdvancedLayoutScheduled = false;
    const layoutReason = node.__easyuseAnimaAdvancedLayoutReason || reason;
    node.__easyuseAnimaAdvancedLayoutReason = null;
    applyAdvancedLayout(node, layoutReason);
  });
}

function dispatchCanvasMouseEvent(type, sourceEvent, overrides = {}) {
  const canvas = app.canvas?.canvas;
  if (!canvas) {
    return;
  }
  const event = new MouseEvent(type, {
    bubbles: true,
    cancelable: true,
    view: window,
    clientX: sourceEvent.clientX,
    clientY: sourceEvent.clientY,
    screenX: sourceEvent.screenX,
    screenY: sourceEvent.screenY,
    button: overrides.button ?? sourceEvent.button,
    buttons: overrides.buttons ?? sourceEvent.buttons,
    ctrlKey: sourceEvent.ctrlKey,
    shiftKey: sourceEvent.shiftKey,
    altKey: sourceEvent.altKey,
    metaKey: sourceEvent.metaKey,
  });
  Object.defineProperty(event, "__easyuseAnimaForwarded", { value: true });
  canvas.dispatchEvent(event);
}

function dispatchCanvasWheelEvent(sourceEvent) {
  const canvas = app.canvas?.canvas;
  if (!canvas) {
    return;
  }
  const event = new WheelEvent("wheel", {
    bubbles: true,
    cancelable: true,
    view: window,
    clientX: sourceEvent.clientX,
    clientY: sourceEvent.clientY,
    screenX: sourceEvent.screenX,
    screenY: sourceEvent.screenY,
    deltaX: sourceEvent.deltaX,
    deltaY: sourceEvent.deltaY,
    deltaZ: sourceEvent.deltaZ,
    deltaMode: sourceEvent.deltaMode,
    ctrlKey: sourceEvent.ctrlKey,
    shiftKey: sourceEvent.shiftKey,
    altKey: sourceEvent.altKey,
    metaKey: sourceEvent.metaKey,
  });
  Object.defineProperty(event, "__easyuseAnimaForwarded", { value: true });
  canvas.dispatchEvent(event);
}

function dispatchCanvasPointerEvent(type, sourceEvent, overrides = {}) {
  const canvas = app.canvas?.canvas;
  if (!canvas || typeof PointerEvent === "undefined") {
    return;
  }
  const event = new PointerEvent(type, {
    bubbles: true,
    cancelable: true,
    view: window,
    clientX: sourceEvent.clientX,
    clientY: sourceEvent.clientY,
    screenX: sourceEvent.screenX,
    screenY: sourceEvent.screenY,
    button: overrides.button ?? sourceEvent.button,
    buttons: overrides.buttons ?? sourceEvent.buttons,
    ctrlKey: sourceEvent.ctrlKey,
    shiftKey: sourceEvent.shiftKey,
    altKey: sourceEvent.altKey,
    metaKey: sourceEvent.metaKey,
    pointerId: sourceEvent.pointerId || 1,
    pointerType: sourceEvent.pointerType || "mouse",
    isPrimary: sourceEvent.isPrimary ?? true,
  });
  Object.defineProperty(event, "__easyuseAnimaForwarded", { value: true });
  canvas.dispatchEvent(event);
}

function isCanvasAreaEvent(event) {
  const canvas = app.canvas?.canvas;
  const rect = canvas?.getBoundingClientRect?.();
  if (!canvas || !rect || event.target === canvas) {
    return false;
  }
  return (
    event.clientX >= rect.left
    && event.clientX <= rect.right
    && event.clientY >= rect.top
    && event.clientY <= rect.bottom
  );
}

function isMiddlePanExcludedTarget(target) {
  if (!(target instanceof Element)) {
    return false;
  }
  return !!target.closest([
    ".comfy-menu",
    ".comfy-modal",
    ".comfyui-menu",
    ".comfyui-settings",
    ".litegraph.litemenu",
    ".easyuse-anima-autocomplete",
    ".easyuse-anima-lora-menu",
  ].join(","));
}

function shouldForwardMiddlePan(event) {
  return (
    !event.__easyuseAnimaForwarded
    && event.button === 1
    && isCanvasAreaEvent(event)
    && !isMiddlePanExcludedTarget(event.target)
  );
}

function startCanvasPanFromDom(event) {
  if (!shouldForwardMiddlePan(event)) {
    return false;
  }
  if (middlePanForwardActive) {
    event.preventDefault();
    event.stopPropagation();
    return true;
  }
  middlePanForwardActive = true;
  event.preventDefault();
  event.stopPropagation();
  document.activeElement?.blur?.();
  dispatchCanvasPointerEvent("pointerdown", event, { button: 1, buttons: 4 });
  dispatchCanvasMouseEvent("mousedown", event, { button: 1, buttons: 4 });

  const move = (moveEvent) => {
    if (moveEvent.__easyuseAnimaForwarded) {
      return;
    }
    moveEvent.preventDefault();
    moveEvent.stopPropagation();
    dispatchCanvasPointerEvent("pointermove", moveEvent, { button: 1, buttons: 4 });
    dispatchCanvasMouseEvent("mousemove", moveEvent, { button: 1, buttons: 4 });
  };
  const stop = (upEvent) => {
    if (upEvent.__easyuseAnimaForwarded) {
      return;
    }
    upEvent.preventDefault();
    upEvent.stopPropagation();
    dispatchCanvasPointerEvent("pointerup", upEvent, { button: 1, buttons: 0 });
    dispatchCanvasMouseEvent("mouseup", upEvent, { button: 1, buttons: 0 });
    middlePanForwardActive = false;
    document.removeEventListener("pointermove", move, true);
    document.removeEventListener("pointerup", stop, true);
    document.removeEventListener("pointercancel", stop, true);
    document.removeEventListener("mousemove", move, true);
    document.removeEventListener("mouseup", stop, true);
  };
  document.addEventListener("pointermove", move, true);
  document.addEventListener("pointerup", stop, true);
  document.addEventListener("pointercancel", stop, true);
  document.addEventListener("mousemove", move, true);
  document.addEventListener("mouseup", stop, true);
  return true;
}

function advancedEditorMaxScrollTop(editor) {
  if (!(editor instanceof HTMLElement)) {
    return 0;
  }
  return Math.max(0, editor.scrollHeight - editor.clientHeight);
}

function canAdvancedEditorScroll(editor) {
  return advancedEditorMaxScrollTop(editor) > 1;
}

function canAdvancedEditorScrollWheelDelta(editor, deltaY) {
  const maxScrollTop = advancedEditorMaxScrollTop(editor);
  if (maxScrollTop <= 1) {
    return false;
  }
  return (deltaY < 0 && editor.scrollTop > 0) || (deltaY > 0 && editor.scrollTop < maxScrollTop - 1);
}

function shouldKeepAdvancedWheelEvent(event, editor) {
  if (!canAdvancedEditorScroll(editor)) {
    return false;
  }
  const target = event?.target;
  if (!(target instanceof Element)) {
    return false;
  }
  return !!target.closest("textarea, input, select");
}

function forwardAdvancedWheelToCanvas(event) {
  if (event.__easyuseAnimaForwarded) {
    return;
  }
  const editor = event.currentTarget;
  if (shouldKeepAdvancedWheelEvent(event, editor)) {
    return;
  }
  if (canAdvancedEditorScrollWheelDelta(editor, Number(event.deltaY) || 0)) {
    return;
  }
  event.preventDefault();
  event.stopPropagation();
  dispatchCanvasWheelEvent(event);
}

function installMiddlePanForwarder() {
  if (window.__easyuseAnimaMiddlePanForwarderInstalled) {
    return;
  }
  window.__easyuseAnimaMiddlePanForwarderInstalled = true;
  document.addEventListener("pointerdown", startCanvasPanFromDom, true);
  document.addEventListener("mousedown", startCanvasPanFromDom, true);
  document.addEventListener("auxclick", (event) => {
    if (shouldForwardMiddlePan(event)) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);
}

function createAdvancedFieldElement(node, field) {
  const fields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
  const globalIndex = fields.findIndex((item) => item.id === field.id);
  const samePane = fields.filter((item) => item.pane === field.pane);
  const paneIndex = samePane.findIndex((item) => item.id === field.id);
  const block = document.createElement("div");
  block.className = "easyuse-anima-advanced-field";
  block.classList.toggle("is-naia", field.type === "naia");
  block.classList.toggle("is-trigger", field.type === "trigger");
  block.classList.toggle("is-disabled", field.enabled === false);

  const header = document.createElement("div");
  header.className = "easyuse-anima-field-header";
  const label = document.createElement("div");
  label.className = "easyuse-anima-field-label";
  label.textContent = `${advancedFieldIndexLabel(fields, field)}. ${advancedFieldLabel(field)}`;
  const tools = document.createElement("div");
  tools.className = "easyuse-anima-field-tools";

  const move = (direction) => {
    const currentFields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
    const paneFields = currentFields
      .map((item, index) => ({ item, index }))
      .filter(({ item }) => item.pane === field.pane);
    const current = paneFields.findIndex(({ item }) => item.id === field.id);
    const target = current + direction;
    if (current < 0 || target < 0 || target >= paneFields.length) {
      return;
    }
    const from = paneFields[current].index;
    const to = paneFields[target].index;
    const [removed] = currentFields.splice(from, 1);
    currentFields.splice(to, 0, removed);
    writeAdvancedFields(node, currentFields, { render: true });
  };

  const addTool = (text, title, callback, disabled = false, active = false) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text;
    button.title = title;
    button.disabled = disabled;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (!button.disabled) {
        callback();
      }
    });
    if (active) {
      button.classList.add("is-on");
    }
    tools.append(button);
    return button;
  };

  const toggleButton = addTool(
    field.enabled === false ? psText("advanced.off") : psText("advanced.on"),
    psText("advanced.enableFieldTitle"),
    () => {
      field.enabled = field.enabled === false;
      writeAdvancedFields(node, fields, { render: true });
    },
    false,
    field.enabled !== false,
  );
  toggleButton.classList.toggle("is-on", field.enabled !== false);
  if (field.type === "trigger") {
    const pinButton = addTool(
      field.pin === false ? psText("advanced.autoOrder") : psText("advanced.pinned"),
      field.pin === false ? psText("advanced.autoOrderTitle") : psText("advanced.pinnedTitle"),
      () => {
        field.pin = field.pin === false;
        writeAdvancedFields(node, fields, { render: true });
      },
      false,
      field.pin !== false,
    );
    pinButton.classList.add("easyuse-anima-trigger-pin");
    pinButton.classList.toggle("is-on", field.pin !== false);
  }
  if (field.type === "naia") {
    const useNaiaWidget = findWidget(node, "use_naia");
    const linkedUseNaia = isWidgetInputLinked(node, "use_naia");
    const fillButton = addTool(psText("advanced.fillFromNaia"), psText("advanced.fillFromNaiaTitle"), () => {
      const currentFields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
      const target = currentFields.find((item) => item.id === field.id);
      if (target?.enabled === false) {
        return;
      }
      const nextValue = !findWidget(node, "use_naia")?.value;
      setAdvancedControlValue(node, "consume_naia_on_queue", true);
      setAdvancedControlValue(node, "use_naia", nextValue);
      applyAdvancedNaiaGeneralAutoToggle(node, currentFields);
      writeAdvancedFields(node, currentFields, { render: true });
    }, linkedUseNaia || field.enabled === false, field.enabled !== false && !!useNaiaWidget?.value);
    fillButton.classList.add("easyuse-anima-naia-fill");
    fillButton.classList.toggle("is-on", field.enabled !== false && !!useNaiaWidget?.value);
    fillButton.classList.toggle("is-linked", linkedUseNaia);
  }
  addTool("↑", psText("advanced.moveUp"), () => move(-1), paneIndex <= 0);
  addTool("↓", psText("advanced.moveDown"), () => move(1), paneIndex >= samePane.length - 1);
  addTool("X", psText("advanced.deleteField"), () => {
    const currentFields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
    currentFields.splice(globalIndex, 1);
    writeAdvancedFields(node, currentFields, { render: true });
  });

  const textarea = document.createElement("textarea");
  const linked = advancedFieldInputLinked(node, field);
  const inputName = advancedFieldInputName(field);
  textarea.value = advancedFieldDisplayText(node, field);
  textarea.style.height = `${field.height || 72}px`;
  textarea.style.overflowY = "hidden";
  textarea.placeholder = field.type === "naia"
    ? psText("advanced.placeholder.naia")
    : field.type === "trigger" ? psText("advanced.placeholder.trigger")
    : field.type === "artist" ? psText("advanced.placeholder.artist") : psText("advanced.placeholder.general");
  textarea.readOnly = false;
  textarea.classList.toggle("is-linked", linked);
  textarea.title = field.type === "naia"
    ? psText("advanced.title.naia")
    : field.type === "trigger"
      ? psText("advanced.title.trigger")
    : linked ? psText("advanced.title.linked") : "";
  textarea.dataset.easyuseAnimaAdvancedFieldId = field.id;
  const updateFieldHighlight = debounce(() => {
    scheduleAdvancedFieldHighlight(node, field, textarea);
  }, 180);
  const persistTextareaHeight = (height, mode = field.heightMode || "auto") => {
    const previousHeight = Math.round(Number(field.height) || 0);
    const previousMode = field.heightMode || "auto";
    const nextHeight = setAdvancedTextareaHeight(node, textarea, height);
    field.height = nextHeight;
    field.heightMode = mode === "manual" ? "manual" : "auto";
    writeAdvancedFields(node, fields, { syncInputs: false });
    updateAdvancedFieldHighlight(node, field, textarea);
    updateFieldHighlight();
    if (Math.abs(nextHeight - previousHeight) > 1 || field.heightMode !== previousMode) {
      scheduleAdvancedLayout(node, "textarea");
    } else {
      requestOverlaySync(textarea);
    }
  };
  const syncHeight = () => {
    if (field.heightMode === "manual") {
      persistTextareaHeight(advancedTextareaCurrentHeight(textarea), "manual");
      return;
    }
    textarea.style.height = "auto";
    textarea.style.overflowY = "hidden";
    const height = Math.max(
      advancedTextareaMinimumHeight(textarea),
      advancedTextareaContentHeight(textarea),
    );
    field.heightMode = "auto";
    persistTextareaHeight(height, "auto");
  };
  const rememberTextareaResizeStart = () => {
    textarea.__easyuseAnimaAdvancedResizeStartHeight = advancedTextareaCurrentHeight(textarea);
  };
  const captureTextareaManualResize = () => {
    const startHeight = Number(textarea.__easyuseAnimaAdvancedResizeStartHeight || 0);
    const currentHeight = advancedTextareaCurrentHeight(textarea);
    textarea.__easyuseAnimaAdvancedResizeStartHeight = currentHeight;
    if (Math.abs(currentHeight - startHeight) <= 2) {
      updateAdvancedFieldHighlight(node, field, textarea);
      return;
    }
    persistTextareaHeight(currentHeight, "manual");
  };
  textarea.addEventListener("mousedown", rememberTextareaResizeStart);
  textarea.addEventListener("pointerdown", rememberTextareaResizeStart);
  textarea.addEventListener("mouseup", captureTextareaManualResize);
  textarea.addEventListener("pointerup", captureTextareaManualResize);
  textarea.addEventListener("input", () => {
    if (linked) {
      node.__easyuseAnimaAdvancedFieldInputValues ||= {};
      node.__easyuseAnimaAdvancedFieldInputValues[inputName] = textarea.value;
    }
    field.text = textarea.value;
    updateFieldHighlight();
    syncHeight();
  });
  textarea.addEventListener("change", () => {
    updateFieldHighlight();
    syncHeight();
  });
  registerAdvancedAutocompleteInput(node, field, textarea);
  requestAnimationFrame(() => {
    const nextHeight = setAdvancedTextareaHeight(node, textarea, field.height || 72, {
      syncField: false,
      refreshHighlight: false,
    });
    if (nextHeight !== field.height) {
      field.height = nextHeight;
      writeAdvancedFields(node, fields, { syncInputs: false });
    }
    updateAdvancedFieldHighlight(node, field, textarea);
    updateFieldHighlight();
    scheduleAdvancedLayout(node, "render");
  });

  header.append(label, tools);
  block.append(header, textarea);
  return block;
}

function addAdvancedField(node, pane, type) {
  const fields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
  if (type === "naia" && hasAdvancedNaia(node, pane)) {
    return;
  }
  if (type === "trigger" && hasPositiveTrigger(node)) {
    return;
  }
  const nextId = `${pane}_${type}_${Date.now().toString(36)}`;
  fields.push({
    id: nextId,
    pane,
    type,
    label: ADVANCED_FIELD_LABELS[type] || "General Tags",
    text: "",
    height: type === "general" || type === "naia" ? 120 : 72,
    enabled: true,
  });
  if (type === "naia") {
    setAdvancedControlValue(node, "consume_naia_on_queue", true);
    setAdvancedControlValue(node, "use_naia", true);
  }
  writeAdvancedFields(node, fields, { render: true });
}

function createAdvancedPane(node, pane, titleKey) {
  const section = document.createElement("section");
  section.className = "easyuse-anima-advanced-pane";

  const header = document.createElement("div");
  header.className = "easyuse-anima-advanced-pane-title";
  const heading = document.createElement("span");
  heading.textContent = psText(titleKey);
  const actions = document.createElement("div");
  actions.className = "easyuse-anima-advanced-actions";
  const addButton = (type, label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.disabled = (type === "naia" && hasAdvancedNaia(node, pane))
      || (type === "trigger" && hasPositiveTrigger(node));
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      addAdvancedField(node, pane, type);
    });
    actions.append(button);
  };
  addButton("quality", psText("advanced.add.quality"));
  addButton("artist", psText("advanced.add.artist"));
  if (pane === "positive") {
    addButton("trigger", psText("advanced.add.trigger"));
  }
  addButton("general", psText("advanced.add.general"));
  addButton("naia", psText("advanced.add.naia"));
  header.append(heading, actions);
  section.append(header);

  const fields = advancedPaneFields(node, pane);
  if (!fields.length) {
    const empty = document.createElement("div");
    empty.className = "easyuse-anima-empty-pane";
    empty.textContent = psText("advanced.noFields");
    section.append(empty);
  } else {
    for (const field of fields) {
      section.append(createAdvancedFieldElement(node, field));
    }
  }
  return section;
}

function renderAdvancedEditor(node) {
  const editor = node.__easyuseAnimaAdvancedEditorEl;
  if (!editor) {
    return;
  }
  node.__easyuseAnimaAdvancedFields = parseAdvancedFields(node);
  applyAdvancedNaiaGeneralAutoToggle(node, node.__easyuseAnimaAdvancedFields);
  editor.innerHTML = "";
  updateAdvancedEditorWidth(node);
  const panes = document.createElement("div");
  panes.className = "easyuse-anima-advanced-panes";
  panes.append(
    createAdvancedPane(node, "positive", "advanced.positivePrompt"),
    createAdvancedPane(node, "negative", "advanced.negativePrompt"),
  );
  editor.append(
    createAdvancedControlBar(node),
    createAdvancedWildcardBar(node),
    createAdvancedResolutionBar(node),
    panes,
  );
  writeAdvancedFields(node, node.__easyuseAnimaAdvancedFields);
  scheduleAdvancedLayout(node, "render");
}

function hookAdvancedNode(node) {
  ensureAdvancedStyle();
  installAdvancedSaveSync();
  ensureAdvancedWidgetValue(node);
  removeAdvancedInternalInputSockets(node);
  hideAdvancedInternalWidget(node, "advanced_fields");
  hideAdvancedControlWidgets(node);
  node.serialize_widgets = true;
  node.minWidth = Math.max(Number(node.minWidth) || 0, 360);
  if (Array.isArray(node.size)) {
    node.size[0] = Math.max(Number(node.size[0]) || 420, 360);
  }
  if (!node.__easyuseAnimaAdvancedEditorEl) {
    const editor = document.createElement("div");
    editor.className = "easyuse-anima-advanced-editor";
    editor.addEventListener("wheel", forwardAdvancedWheelToCanvas, { capture: true, passive: false });
    node.__easyuseAnimaAdvancedEditorEl = editor;
    const widget = node.addDOMWidget?.("easyuse_anima_advanced_editor", "EasyUseAnimaAdvancedEditor", editor, {
      serialize: false,
      hideOnZoom: false,
      getMinHeight: () => advancedEditorMinimumHeight(node),
      getHeight: () => advancedEditorWidgetHeight(node),
    });
    if (widget) {
      node.__easyuseAnimaAdvancedDomWidget = widget;
      widget.computeLayoutSize = () => {
        const height = advancedEditorWidgetHeight(node);
        return {
          minHeight: advancedEditorMinimumHeight(node),
          height,
          minWidth: 280,
        };
      };
    }
  }
  renderAdvancedEditor(node);
}

function scheduleHookAdvancedNode(node) {
  if (!node || node.__easyuseAnimaAdvancedHookScheduled) {
    return;
  }
  node.__easyuseAnimaAdvancedHookScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaAdvancedHookScheduled = false;
    hookAdvancedNode(node);
  });
}

function syncAdvancedValues(node, serialized = null) {
  const fields = collectAdvancedEditorFields(node);
  writeAdvancedFields(node, fields, { syncInputs: false });
  if (!serialized || !Array.isArray(node.widgets) || !Array.isArray(serialized.widgets_values)) {
    return;
  }
  const fieldsValue = advancedWidget(node)?.value || JSON.stringify(fields);
  syncAdvancedFieldsBackup(node, fieldsValue);
  serialized.properties ||= {};
  serialized.properties[ADVANCED_FIELDS_PROPERTY] = fieldsValue;

  for (const name of Object.keys(ADVANCED_WIDGET_INDEX)) {
    const index = ADVANCED_WIDGET_INDEX[name];
    const widget = findWidget(node, name);
    while (serialized.widgets_values.length <= index) {
      serialized.widgets_values.push(null);
    }
    if (name === "advanced_fields") {
      serialized.widgets_values[index] = fieldsValue;
    } else if (widget) {
      serialized.widgets_values[index] = widget.value;
    }
  }
}

function applyAdvancedExecutedInputs(node, message) {
  const payload = firstValue(message?.prompt_studio_advanced, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  node.__easyuseAnimaAdvancedFieldInputValues =
    payload.field_inputs && typeof payload.field_inputs === "object" ? payload.field_inputs : {};
  const widget = advancedWidget(node);
  if (widget && payload.advanced_fields != null) {
    widget.value = String(payload.advanced_fields);
    syncAdvancedFieldsBackup(node, widget.value);
  }
  const fields = parseAdvancedFields(node);
  if (mergeAdvancedFieldInputValues(node, fields, node.__easyuseAnimaAdvancedFieldInputValues)) {
    writeAdvancedFields(node, fields, { syncInputs: false });
  } else {
    node.__easyuseAnimaAdvancedFields = fields;
  }
  const useNaia = findWidget(node, "use_naia");
  if (useNaia && payload.use_naia != null) {
    useNaia.value = !!payload.use_naia;
  }
  for (const name of ["resolution_bucket", "resolution_size", "resolution_custom_width", "resolution_custom_height"]) {
    const widget = findWidget(node, name);
    if (widget && payload[name] != null) {
      widget.value = payload[name];
    }
  }
  for (const name of ["wildcard_mode", "wildcard_seed", "wildcard_seed_after_generate"]) {
    const widget = findWidget(node, name);
    if (widget && payload[name] != null) {
      widget.value = payload[name];
    }
  }
  renderAdvancedEditor(node);
}

function setRegularWidgetValue(node, name, value) {
  const widget = findWidget(node, name);
  if (!widget) {
    return false;
  }
  widget.value = value;
  const input = findInputEl(widget);
  if (input) {
    input.value = String(value ?? "");
  }
  widget.callback?.(widget.value);
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  return true;
}

function applyWildcardExecutedInputs(node, message) {
  const payload = firstValue(message?.wildcard, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  if (payload.populated_text != null) {
    setRegularWidgetValue(node, "populated_text", String(payload.populated_text));
  }
  if (payload.mode != null) {
    setRegularWidgetValue(node, "mode", String(payload.mode));
  }
  if (payload.seed != null) {
    setRegularWidgetValue(node, "seed", Number(payload.seed));
  }
}

function isAdvancedNode(node) {
  return node?.type === ADVANCED_NODE_TYPE || node?.comfyClass === ADVANCED_NODE_TYPE;
}

function isWildcardNode(node) {
  return node?.type === WILDCARD_NODE_TYPE || node?.comfyClass === WILDCARD_NODE_TYPE;
}

function syncAllAdvancedNodes() {
  const nodes = app.graph?._nodes || [];
  for (const node of nodes) {
    if (isAdvancedNode(node)) {
      syncAdvancedValues(node);
    }
  }
}

function refreshPromptStudioLocaleDom() {
  for (const node of app.graph?._nodes || []) {
    if (isAdvancedNode(node)) {
      renderAdvancedEditor(node);
    } else if (isExtendNode(node)) {
      hookStudioNode(node);
      renderExtendSlotControls(node);
    }
    node?.setDirtyCanvas?.(true, true);
  }
  app.graph?.setDirtyCanvas?.(true, true);
}

function installAdvancedSaveSync() {
  const graphProto = globalThis.LGraph?.prototype || app.graph?.constructor?.prototype;
  if (graphProto?.serialize && !graphProto.serialize.__easyuseAnimaAdvancedWrapped) {
    const serialize = graphProto.serialize;
    graphProto.serialize = function () {
      syncAllAdvancedNodes();
      return serialize.apply(this, arguments);
    };
    graphProto.serialize.__easyuseAnimaAdvancedWrapped = true;
  }

  if (app.queuePrompt && !app.queuePrompt.__easyuseAnimaAdvancedWrapped) {
    const queuePrompt = app.queuePrompt;
    app.queuePrompt = function () {
      syncAllAdvancedNodes();
      return queuePrompt.apply(this, arguments);
    };
    app.queuePrompt.__easyuseAnimaAdvancedWrapped = true;
  }
}

app.registerExtension({
  name: "easyuse-anima.prompt-studio",
  async setup() {
    installMiddlePanForwarder();
    installAdvancedSaveSync();
    installPromptHighlightOverlayRefresh();
    await loadPromptStudioSettings();
    easyuseAnimaWatchLocale(() => {
      refreshPromptStudioLocaleDom();
      refreshAllPromptHighlights();
    });
    window.addEventListener("easyuse-anima-settings-updated", (event) => {
      if (!event?.detail) {
        return;
      }
      applyPromptStudioSettings(event.detail);
      for (const node of app.graph?._nodes || []) {
        if (isAdvancedNode(node)) {
          renderAdvancedEditor(node);
        }
      }
      refreshAllPromptHighlights();
    });
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (
      nodeData.name !== NODE_TYPE
      && nodeData.name !== ADVANCED_NODE_TYPE
      && nodeData.name !== EXTEND_NODE_TYPE
      && nodeData.name !== WILDCARD_NODE_TYPE
    ) {
      return;
    }
    if (nodeType.prototype.__easyuseAnimaPromptStudioWrapped) {
      return;
    }
    nodeType.prototype.__easyuseAnimaPromptStudioWrapped = true;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE) {
        scheduleHookAdvancedNode(this);
      } else if (nodeData.name === WILDCARD_NODE_TYPE) {
        return;
      } else {
        hookStudioNode(this);
      }
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (serialized) {
      onConfigure?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE) {
        captureAdvancedConfigure(this, serialized);
        scheduleHookAdvancedNode(this);
      } else if (nodeData.name === WILDCARD_NODE_TYPE) {
        return;
      } else {
        hookStudioNode(this);
      }
    };

    const onResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function () {
      const result = onResize?.apply(this, arguments);
      if (this.__easyuseAnimaHandlingResize || this.__easyuseAnimaApplyingLayout) {
        return result;
      }
      this.__easyuseAnimaHandlingResize = true;
      try {
        if (nodeData.name === ADVANCED_NODE_TYPE) {
          updateAdvancedEditorWidth(this);
          scheduleAdvancedResizeFinalize(this);
          return result;
        }
        if (nodeData.name === WILDCARD_NODE_TYPE) {
          return result;
        }
        if (isExtendNode(this)) {
          applyExtendSlotVisibility(this);
          renderExtendSlotControls(this);
        }
        rebalanceStudioInputHeights(this);
        if (isExtendNode(this)) {
          layoutExtendPromptWidgets(this);
        }
        return result;
      } finally {
        this.__easyuseAnimaHandlingResize = false;
      }
    };

    const onConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function () {
      const result = onConnectionsChange?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE && !this.__easyuseAnimaHandlingConnectionsChange) {
        this.__easyuseAnimaHandlingConnectionsChange = true;
        requestAnimationFrame(() => {
          try {
            removeAdvancedInternalInputSockets(this);
            pruneDisconnectedAdvancedFieldInputValues(this);
            renderAdvancedEditor(this);
          } finally {
            this.__easyuseAnimaHandlingConnectionsChange = false;
          }
        });
      }
      return result;
    };

    const onSerialize = nodeType.prototype.onSerialize;
    nodeType.prototype.onSerialize = function (serialized) {
      const result = onSerialize?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE) {
        removeAdvancedInternalInputSockets(this);
        syncAdvancedValues(this, serialized);
      } else if (nodeData.name === WILDCARD_NODE_TYPE) {
        return result;
      } else {
        syncStudioValues(this, serialized);
      }
      return result;
    };

    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE) {
        applyAdvancedExecutedInputs(this, message);
      } else if (nodeData.name === WILDCARD_NODE_TYPE) {
        applyWildcardExecutedInputs(this, message);
      } else {
        applyExecutedInputs(this, message);
      }
    };
  },
});
