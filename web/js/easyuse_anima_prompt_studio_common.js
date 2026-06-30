import { easyuseAnimaText } from "./easyuse_anima_i18n.js";
import { normalizePromptTagText } from "./easyuse_anima_prompt_rules.js";

export const PROMPT_STUDIO_VARIANT_FIELD_TYPES = ["quality", "artist", "trigger", "general"];
export const PROMPT_STUDIO_VARIANT_FIELD_LABELS = {
  quality: "Quality Tags",
  artist: "Artist Tags",
  trigger: "Trigger Words",
  general: "General Tags",
};
export const PROMPT_STUDIO_WILDCARD_MODES = ["일반 채우기", "고정", "순차", "재현"];
export const PROMPT_STUDIO_WILDCARD_SEED_CONTROLS = ["fixed", "randomize", "increment", "decrement"];
export const PROMPT_STUDIO_WILDCARD_DEFAULT_MODE = "고정";
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

const PROMPT_STUDIO_COMMON_TEXT = {
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
    "section.comment": "Comment",
    "section.syntax": "Syntax error",
    "section.unknown": "Unknown",
    "tag.generic": "Tag",
    "tag.learned": "learned",
    "field.quality": "Quality Tags",
    "field.artist": "Artist Tags",
    "field.trigger": "Trigger Words",
    "field.general": "General Tags",
    "advanced.wildcard": "Wildcard",
    "advanced.wildcardTitle": "Expand __wildcard__ and dynamic prompt syntax in prompt fields.",
    "advanced.wildcardSeed": "Wildcard seed",
    "advanced.wildcardSeedControl": "Seed control",
    "advanced.resolutionTitle": "Latent image resolution output. Resolutions are sorted by aspect ratio.",
    "advanced.resolutionBucket": "Resolution bucket",
    "advanced.resolutionSize": "Resolution size",
    "advanced.customWidth": "Custom width",
    "advanced.customHeight": "Custom height",
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
    "section.comment": "주석",
    "section.syntax": "문법 오류",
    "section.unknown": "미확인",
    "tag.generic": "태그",
    "tag.learned": "학습됨",
    "field.quality": "Quality Tags",
    "field.artist": "Artist Tags",
    "field.trigger": "Trigger Words",
    "field.general": "General Tags",
    "advanced.wildcard": "와일드카드",
    "advanced.wildcardTitle": "프롬프트 필드의 __wildcard__와 동적 프롬프트 문법을 확장합니다.",
    "advanced.wildcardSeed": "와일드카드 시드",
    "advanced.wildcardSeedControl": "시드 제어",
    "advanced.resolutionTitle": "Latent 이미지 해상도 출력입니다. 해상도는 화면비 기준으로 정렬됩니다.",
    "advanced.resolutionBucket": "해상도 버킷",
    "advanced.resolutionSize": "해상도 크기",
    "advanced.customWidth": "사용자 너비",
    "advanced.customHeight": "사용자 높이",
  },
  ja: {
    "section.quality": "品質",
    "section.safety": "レーティング",
    "section.year": "年代",
    "section.count": "人数",
    "section.character": "キャラクター",
    "section.artist": "作者",
    "section.artist_unknown": "未登録作者",
    "section.copyright": "作品",
    "section.meta": "メタ",
    "section.general": "学習タグ",
    "section.natural": "自然文",
    "section.wildcard": "ワイルドカード",
    "section.comment": "コメント",
    "section.syntax": "構文エラー",
    "section.unknown": "不明",
    "tag.generic": "タグ",
    "tag.learned": "学習済み",
    "field.quality": "Quality Tags",
    "field.artist": "Artist Tags",
    "field.trigger": "Trigger Words",
    "field.general": "General Tags",
    "advanced.wildcard": "ワイルドカード",
    "advanced.wildcardTitle": "プロンプト欄の __wildcard__ と動的プロンプト構文を展開します。",
    "advanced.wildcardSeed": "ワイルドカードシード",
    "advanced.wildcardSeedControl": "シード制御",
    "advanced.resolutionTitle": "Latent 画像解像度出力。解像度はアスペクト比順に並びます。",
    "advanced.resolutionBucket": "解像度バケット",
    "advanced.resolutionSize": "解像度サイズ",
    "advanced.customWidth": "カスタム幅",
    "advanced.customHeight": "カスタム高さ",
  },
  zh: {
    "section.quality": "质量",
    "section.safety": "分级",
    "section.year": "年份",
    "section.count": "人数",
    "section.character": "角色",
    "section.artist": "作者",
    "section.artist_unknown": "未注册作者",
    "section.copyright": "作品",
    "section.meta": "元数据",
    "section.general": "训练标签",
    "section.natural": "自然语言",
    "section.wildcard": "通配符",
    "section.comment": "注释",
    "section.syntax": "语法错误",
    "section.unknown": "未知",
    "tag.generic": "标签",
    "tag.learned": "已学习",
    "field.quality": "Quality Tags",
    "field.artist": "Artist Tags",
    "field.trigger": "Trigger Words",
    "field.general": "General Tags",
    "advanced.wildcard": "通配符",
    "advanced.wildcardTitle": "展开提示词字段中的 __wildcard__ 和动态提示词语法。",
    "advanced.wildcardSeed": "通配符种子",
    "advanced.wildcardSeedControl": "种子控制",
    "advanced.resolutionTitle": "Latent 图像分辨率输出。分辨率按宽高比排序。",
    "advanced.resolutionBucket": "分辨率桶",
    "advanced.resolutionSize": "分辨率尺寸",
    "advanced.customWidth": "自定义宽度",
    "advanced.customHeight": "自定义高度",
  },
};

const SECTION_STYLES = {
  quality: { label: "Quality", color: "#facc15", background: "rgba(202, 138, 4, 0.18)", weight: 700 },
  safety: { label: "Rating", color: "#38bdf8", background: "rgba(2, 132, 199, 0.18)", weight: 600 },
  year: { label: "Year", color: "#2dd4bf", background: "rgba(13, 148, 136, 0.18)", weight: 600 },
  count: { label: "Count", color: "#60a5fa", background: "rgba(37, 99, 235, 0.18)", weight: 700 },
  character: { label: "Character", color: "#f472b6", background: "rgba(219, 39, 119, 0.18)", weight: 700 },
  artist: { label: "Artist", color: "#a78bfa", background: "rgba(124, 58, 237, 0.18)", weight: 700 },
  artist_unknown: { label: "Unregistered artist", color: "#f87171", background: "transparent", underline: true, weight: 400 },
  copyright: { label: "Copyright", color: "#fb923c", background: "rgba(234, 88, 12, 0.18)", weight: 700 },
  meta: { label: "Meta", color: "#94a3b8", background: "rgba(100, 116, 139, 0.18)", weight: 600 },
  general: { label: "Trained tag", color: "#4ade80", background: "rgba(22, 163, 74, 0.16)", weight: 600 },
  natural: { label: "Natural language", color: "#cbd5e1", background: "rgba(71, 85, 105, 0.16)", weight: 400 },
  wildcard: { label: "Wildcard", color: "#c084fc", background: "rgba(126, 34, 206, 0.24)", weight: 700 },
  comment: { label: "Comment", color: "#9ca3af", background: "rgba(156, 163, 175, 0.14)", weight: 400, italic: true },
  syntax: { label: "Syntax error", color: "#f87171", background: "transparent", underline: true, weight: 400 },
  unknown: { label: "Unknown", color: "#cbd5e1", background: "transparent", underline: true, weight: 400 },
};

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

function commonText(key) {
  return easyuseAnimaText(PROMPT_STUDIO_COMMON_TEXT, key);
}

export function promptStudioText(key) {
  return commonText(key);
}

export function promptStudioFieldLabel(field) {
  const type = String(field?.type || "general");
  const fallback = PROMPT_STUDIO_VARIANT_FIELD_LABELS[type] || PROMPT_STUDIO_VARIANT_FIELD_LABELS.general;
  return String(field?.label || commonText(`field.${type}`) || fallback);
}

export function promptStudioFieldIndexLabel(fields, field) {
  const index = (fields || []).findIndex((item) => item?.id === field?.id);
  return index >= 0 ? String(index + 1) : "-";
}

export function ensurePromptStudioVariantStyle() {
  if (document.getElementById("easyuse-anima-prompt-studio-variant-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-prompt-studio-variant-style";
  style.textContent = `
    .easyuse-anima-prompt-studio-variant.easyuse-anima-advanced-editor {
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
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-panes {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-controlbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 5px;
      margin-bottom: 7px;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-toggle {
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
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-toggle.is-on {
      border-color: rgba(96, 165, 250, 0.78);
      background: rgba(37, 99, 235, 0.68);
      color: #fff;
      font-weight: 700;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-resolutionbar {
      display: grid;
      grid-template-columns: minmax(82px, 0.34fr) minmax(0, 1fr);
      gap: 8px;
      margin: 0 0 10px;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-wildcardbar {
      display: grid;
      grid-template-columns: minmax(92px, 0.34fr) minmax(74px, 0.28fr) minmax(92px, 0.38fr);
      gap: 8px;
      margin: 0 0 10px;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-wildcardbar select,
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-wildcardbar input,
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-resolutionbar select,
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-resolutionbar input {
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
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-wildcardbar select:focus,
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-wildcardbar input:focus,
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-resolutionbar select:focus,
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-resolutionbar input:focus {
      border-color: rgba(96, 165, 250, 0.76);
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-resolution-custom {
      display: grid;
      grid-template-columns: minmax(72px, 1fr) auto minmax(72px, 1fr);
      gap: 6px;
      align-items: center;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-resolution-custom span {
      color: rgba(203, 213, 225, 0.72);
      font: 12px sans-serif;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-pane {
      min-width: 0;
      border: 1px solid rgba(148, 163, 184, 0.28);
      background: rgba(15, 23, 42, 0.28);
      padding: 6px;
      box-sizing: border-box;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-pane-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      margin-bottom: 6px;
      color: rgba(226, 232, 240, 0.82);
      font-weight: 700;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      justify-content: flex-end;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-actions button,
    .easyuse-anima-prompt-studio-variant .easyuse-anima-field-tools button,
    .easyuse-anima-regional-modal button {
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(30, 41, 59, 0.8);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      min-height: 20px;
      padding: 1px 6px;
      cursor: pointer;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-actions button:disabled,
    .easyuse-anima-prompt-studio-variant .easyuse-anima-field-tools button:disabled {
      opacity: 0.35;
      cursor: default;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-field-tools button.is-on {
      border-color: rgba(96, 165, 250, 0.78);
      background: rgba(37, 99, 235, 0.58);
      color: #fff;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-field {
      margin: 0 0 6px;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-field.is-disabled {
      opacity: 0.58;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-field-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      min-height: 20px;
      color: rgba(203, 213, 225, 0.86);
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-field-label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-field-tools {
      display: flex;
      gap: 3px;
      flex: 0 0 auto;
      align-items: center;
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-field textarea {
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
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-field textarea:focus {
      border-color: rgba(96, 165, 250, 0.7);
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-advanced-field.is-trigger textarea {
      border-style: dashed;
      background: rgba(12, 20, 34, 0.78);
    }
    .easyuse-anima-prompt-studio-variant .easyuse-anima-empty-pane {
      padding: 10px 4px;
      color: rgba(148, 163, 184, 0.72);
      font-size: 11px;
    }
    .easyuse-anima-prompt-studio-variant {
      padding: 8px;
    }
    .easyuse-anima-regional-summary {
      color: rgba(203, 213, 225, 0.72);
      font-size: 11px;
      margin-left: auto;
    }
    .easyuse-anima-regional-field .easyuse-anima-field-label {
      display: flex;
      align-items: center;
      gap: 5px;
      min-width: 0;
      flex: 1 1 auto;
    }
    .easyuse-anima-regional-field .easyuse-anima-field-header {
      display: grid;
      grid-template-columns: minmax(130px, 1fr) minmax(210px, 0.72fr);
      align-items: center;
      gap: 6px;
      min-width: 0;
    }
    .easyuse-anima-regional-field .easyuse-anima-field-label span {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .easyuse-anima-regional-field .easyuse-anima-field-tools {
      display: grid;
      grid-template-columns: minmax(74px, 1fr) minmax(70px, 0.82fr) minmax(42px, auto) 22px;
      align-items: center;
      gap: 3px;
      min-width: 0;
      max-width: 100%;
    }
    .easyuse-anima-regional-field-label-input,
    .easyuse-anima-regional-field-type,
    .easyuse-anima-regional-modal input[type="text"] {
      box-sizing: border-box;
      min-width: 0;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(15, 23, 42, 0.88);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      padding: 2px 6px;
      outline: none;
    }
    .easyuse-anima-regional-field-label-input {
      width: 100%;
      max-width: none;
      height: 22px;
    }
    .easyuse-anima-regional-field-type {
      width: 100%;
      min-width: 0;
      height: 22px;
    }
    .easyuse-anima-regional-pane-badge {
      flex: 0 0 auto;
      color: rgba(147, 197, 253, 0.9);
      font-size: 10px;
      text-transform: uppercase;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .easyuse-anima-regional-field[data-pane="negative"] .easyuse-anima-regional-pane-badge {
      color: rgba(252, 165, 165, 0.92);
    }
    .easyuse-anima-regional-assignment {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(130px, 0.34fr);
      gap: 6px;
      align-items: start;
      margin-top: 5px;
      color: rgba(148, 163, 184, 0.82);
      font-size: 11px;
    }
    .easyuse-anima-regional-mask-button {
      box-sizing: border-box;
      width: 100%;
      min-height: 24px;
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(30, 41, 59, 0.8);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      padding: 2px 6px;
      text-align: left;
      cursor: pointer;
    }
    .easyuse-anima-regional-mask-button.has-mask {
      border-color: rgba(96, 165, 250, 0.65);
      color: #fff;
    }
    .easyuse-anima-regional-mask-popover {
      position: absolute;
      z-index: 10000;
      min-width: 180px;
      max-width: min(320px, calc(100vw - 24px));
      max-height: 240px;
      overflow: auto;
      border: 1px solid rgba(148, 163, 184, 0.38);
      background: #111827;
      color: #e5e7eb;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
      padding: 4px;
    }
    .easyuse-anima-regional-mask-option {
      display: flex;
      align-items: center;
      gap: 6px;
      min-height: 24px;
      padding: 2px 4px;
      cursor: pointer;
      font: 11px sans-serif;
    }
    .easyuse-anima-regional-mask-option:hover {
      background: rgba(51, 65, 85, 0.82);
    }
    .easyuse-anima-regional-mask-option input {
      margin: 0;
    }
    .easyuse-anima-regional-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.55);
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .easyuse-anima-regional-modal {
      width: min(920px, calc(100vw - 40px));
      max-height: calc(100vh - 42px);
      overflow: hidden;
      background: #111827;
      color: #e5e7eb;
      border: 1px solid #4b5563;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
      display: flex;
      flex-direction: column;
    }
    .easyuse-anima-regional-modal-head {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border-bottom: 1px solid #374151;
    }
    .easyuse-anima-regional-modal-title {
      font-weight: 700;
      font-size: 13px;
    }
    .easyuse-anima-regional-modal-body {
      display: grid;
      grid-template-columns: minmax(300px, 1fr) 260px;
      gap: 10px;
      min-height: 0;
      padding: 10px;
      overflow: auto;
    }
    .easyuse-anima-regional-canvas-wrap {
      background: #0b0f16;
      border: 1px solid #374151;
      padding: 8px;
      min-width: 0;
    }
    .easyuse-anima-regional-canvas {
      display: block;
      width: 100%;
      max-height: 62vh;
      background: #05070a;
      cursor: crosshair;
      touch-action: none;
    }
    .easyuse-anima-regional-mask-sidebar {
      display: grid;
      grid-template-rows: minmax(120px, 1fr) auto;
      gap: 8px;
      min-width: 0;
      min-height: 0;
    }
    .easyuse-anima-regional-mask-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
      min-width: 0;
      overflow: auto;
    }
    .easyuse-anima-regional-mask-row {
      border: 1px solid #374151;
      background: #151b24;
      padding: 6px;
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto auto;
      gap: 5px;
      align-items: center;
    }
    .easyuse-anima-regional-mask-row.active {
      border-color: #60a5fa;
    }
    .easyuse-anima-regional-mask-inspector {
      border: 1px solid #374151;
      background: #111827;
      padding: 8px;
      display: grid;
      gap: 6px;
      min-width: 0;
    }
    .easyuse-anima-regional-mask-inspector-empty {
      color: #94a3b8;
      font-size: 12px;
    }
    .easyuse-anima-regional-mask-inspector-title {
      color: #d1d5db;
      font-size: 12px;
      font-weight: 700;
    }
    .easyuse-anima-regional-mask-control {
      display: grid;
      grid-template-columns: 72px minmax(0, 1fr);
      gap: 6px;
      align-items: center;
      color: #aab4c4;
      font-size: 12px;
      min-width: 0;
    }
    .easyuse-anima-regional-mask-control input,
    .easyuse-anima-regional-mask-control select {
      width: 100%;
      min-width: 0;
      box-sizing: border-box;
      background: #111827;
      border: 1px solid #334155;
      color: #e5e7eb;
      min-height: 24px;
      font-size: 12px;
    }
    .easyuse-anima-regional-modal-foot {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
      padding: 10px 12px;
      border-top: 1px solid #374151;
    }
  `;
  document.head.append(style);
}

export function ensurePromptStudioHighlightStyle() {
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

export function createPromptStudioActionButton(label, title, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  if (title) {
    button.title = title;
  }
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    onClick?.(event);
  });
  return button;
}

export function debounce(fn, delay = 180) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
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

function sectionLabel(section) {
  const key = String(section || "unknown");
  const style = SECTION_STYLES[key] || SECTION_STYLES.unknown;
  return commonText(`section.${key}`) || style?.label || key;
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
  if (style.italic) {
    rules.push("font-style: italic");
  }
  if (style.underline && !token?.weighted) {
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
  const label = token?.label || sectionLabel(token?.section) || style?.label || token?.section || commonText("tag.generic");
  const learned = token?.learned ? ` / ${commonText("tag.learned")}` : "";
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

export function requestPromptStudioOverlaySync(input, forceCopyMetrics = false) {
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
  const schedule = () => requestPromptStudioOverlaySync(input);
  const scheduleMetrics = () => requestPromptStudioOverlaySync(input, true);
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

  ensurePromptStudioHighlightStyle();
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

function promptStudioHighlightState(node, field, namespace = "variant") {
  node.__easyuseAnimaPromptStudioHighlightStates ||= {};
  const id = `${namespace}:${String(field?.id || "field")}`;
  node.__easyuseAnimaPromptStudioHighlightStates[id] ||= {
    seq: 0,
    lastText: "",
    pendingText: null,
    tokens: [],
  };
  return node.__easyuseAnimaPromptStudioHighlightStates[id];
}

export function updatePromptStudioFieldHighlight(node, field, textarea, tokens = null, forceCopyMetrics = false, namespace = "variant") {
  if (!(textarea instanceof HTMLTextAreaElement)) {
    return;
  }
  textarea.__easyuseAnimaNode = node;
  textarea.__easyuseAnimaField = field;
  textarea.__easyuseAnimaHighlightRefresh = (force = false) => {
    updatePromptStudioFieldHighlight(node, field, textarea, null, force, namespace);
  };
  const overlay = ensureHighlightOverlay(textarea);
  if (!overlay) {
    return;
  }
  const state = promptStudioHighlightState(node, field, namespace);
  const value = String(textarea.value || "");
  if (forceCopyMetrics) {
    copyInputTextMetrics(textarea, overlay);
  }
  syncOverlayBounds(textarea, overlay);
  overlay.innerHTML = highlightOverlayHtml(value, tokens || state.tokens || [], textarea.placeholder || "");
}

export function schedulePromptStudioFieldHighlight(node, field, textarea, { namespace = "variant" } = {}) {
  const state = promptStudioHighlightState(node, field, namespace);
  const text = String(textarea?.value || "");
  if (!text.trim()) {
    state.tokens = [];
    state.lastText = "";
    state.pendingText = null;
    updatePromptStudioFieldHighlight(node, field, textarea, [], false, namespace);
    return;
  }
  if (state.lastText === text && Array.isArray(state.tokens)) {
    updatePromptStudioFieldHighlight(node, field, textarea, state.tokens, false, namespace);
    return;
  }
  if (state.pendingText === text) {
    updatePromptStudioFieldHighlight(node, field, textarea, state.tokens, false, namespace);
    return;
  }

  const seq = ++state.seq;
  state.pendingText = text;
  updatePromptStudioFieldHighlight(node, field, textarea, state.tokens, false, namespace);
  classifyPrompt(text)
    .then((tokens) => {
      if (seq !== state.seq || !textarea.isConnected) {
        return;
      }
      state.lastText = text;
      state.tokens = tokens;
      updatePromptStudioFieldHighlight(node, field, textarea, tokens, false, namespace);
    })
    .catch(() => {
      if (seq !== state.seq || !textarea.isConnected) {
        return;
      }
      state.tokens = [];
      updatePromptStudioFieldHighlight(node, field, textarea, [], false, namespace);
    })
    .finally(() => {
      if (state.pendingText === text) {
        state.pendingText = null;
      }
    });
}

function registerPromptStudioAutocompleteInput(node, field, textarea) {
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

function textareaCurrentHeight(textarea) {
  return Math.max(0, Math.round(textarea.getBoundingClientRect?.().height || textarea.offsetHeight || 0));
}

export function registerPromptStudioTextarea(node, field, textarea, options = {}) {
  if (!(textarea instanceof HTMLTextAreaElement)) {
    return;
  }
  const {
    namespace = "variant",
    onInput = null,
    onChange = null,
    onManualResize = null,
    scheduleLayout = null,
    debounceMs = 180,
  } = options;
  const updateFieldHighlight = debounce(() => {
    schedulePromptStudioFieldHighlight(node, field, textarea, { namespace });
  }, debounceMs);
  const rememberResizeStart = () => {
    textarea.__easyuseAnimaPromptStudioResizeStartHeight = textareaCurrentHeight(textarea);
  };
  const captureManualResize = () => {
    const startHeight = Number(textarea.__easyuseAnimaPromptStudioResizeStartHeight || 0);
    const currentHeight = textareaCurrentHeight(textarea);
    textarea.__easyuseAnimaPromptStudioResizeStartHeight = currentHeight;
    if (Math.abs(currentHeight - startHeight) > 2) {
      onManualResize?.(currentHeight);
      scheduleLayout?.();
    }
    updatePromptStudioFieldHighlight(node, field, textarea, null, true, namespace);
    updateFieldHighlight();
  };

  textarea.addEventListener("mousedown", rememberResizeStart);
  textarea.addEventListener("pointerdown", rememberResizeStart);
  textarea.addEventListener("mouseup", captureManualResize);
  textarea.addEventListener("pointerup", captureManualResize);
  textarea.addEventListener("input", () => {
    onInput?.(textarea);
    updateFieldHighlight();
  });
  textarea.addEventListener("change", () => {
    onChange?.(textarea);
    updateFieldHighlight();
  });
  registerPromptStudioAutocompleteInput(node, field, textarea);
  requestAnimationFrame(() => {
    if (!textarea.isConnected) {
      return;
    }
    updatePromptStudioFieldHighlight(node, field, textarea, null, true, namespace);
    updateFieldHighlight();
    scheduleLayout?.();
  });
}

export function refreshPromptStudioHighlights(node, textareas, fields, { namespace = "variant", classify = true } = {}) {
  const byId = new Map((fields || []).map((field) => [String(field.id), field]));
  for (const textarea of textareas || []) {
    const fieldId = String(textarea.dataset.easyuseAnimaPromptStudioVariantFieldId || "");
    const field = byId.get(fieldId);
    if (!field) {
      continue;
    }
    updatePromptStudioFieldHighlight(node, field, textarea, null, true, namespace);
    if (classify) {
      schedulePromptStudioFieldHighlight(node, field, textarea, { namespace });
    }
  }
}
