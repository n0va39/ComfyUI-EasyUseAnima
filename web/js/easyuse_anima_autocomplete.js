import { app } from "../../../scripts/app.js";
import {
  normalizePromptTagText,
  promptCompletionTagText,
} from "./easyuse_anima_prompt_rules.js";
import { easyuseAnimaFetchJson, easyuseAnimaGetSettings } from "./easyuse_anima_api.js";
import { easyuseAnimaText } from "./easyuse_anima_i18n.js";
import {
  autocompleteQuery,
  currentToken as currentAutocompleteToken,
  currentWildcardToken as currentAutocompleteWildcardToken,
  isCaretInComment,
  isCaretInPromptTranslationMarker as caretInPromptTranslationMarker,
  normalizeWildcardSearchText,
  parseAutocompleteText,
  planAutocompleteInsertion,
  wildcardAutocompleteQuery,
} from "./autocomplete/text_model.js";

const TARGETS = {
  EasyUseAnimaPromptBuilder: new Set([
    "quality_tags",
    "trigger_and_artist_tags",
    "lora_trigger_tags",
    "prompt",
    "trailing_quality_tags",
  ]),
  EasyUseAnimaPromptStudio: new Set([
    "quality_tags",
    "trigger_and_artist_tags",
    "lora_trigger_tags",
    "prompt",
    "trailing_quality_tags",
  ]),
  EasyUseAnimaPromptCorrector: new Set([
    "prompt",
    "artist_overrides",
    "artist_exclusions",
  ]),
  EasyUseAnimaPromptCorrectorSimple: new Set([
    "prompt",
  ]),
  EasyUseAnimaLoraPreset: new Set([
    "style_prompt",
  ]),
  EasyUseAnimaWildcard: new Set([
    "text",
    "populated_text",
  ]),
};

const ARTIST_ONLY_TARGETS = {
  EasyUseAnimaLoraPreset: new Set([
    "style_prompt",
  ]),
};

const EXCLUDED_NODE_PATTERNS = [
  /lora\s*stacker/i,
  /loramanager/i,
  /lora[_\s-]*manager/i,
  /lora manager/i,
];

const EXCLUDED_INPUT_TYPE_PATTERNS = [
  /autocomplete/i,
  /lora/i,
  /embedding/i,
  /checkpoint/i,
  /model/i,
];

const GENERIC_NODE_PATTERNS = [
  /primitive.*string/i,
  /string.*primitive/i,
  /string.*multiline/i,
  /multiline.*string/i,
  /text/i,
  /prompt/i,
];

const DEFAULT_MAX_RESULTS = 20;
const MAX_RESULT_LIMIT = 100;
const DEFAULT_AUTOCOMPLETE_MODE = "compatible_global";
const DEFAULT_AUTOCOMPLETE_COMMIT_KEY = "enter";
const AUTOCOMPLETE_MODES = new Set([
  "off",
  "easyuse_nodes",
  "compatible_global",
]);
const AUTOCOMPLETE_COMMIT_KEYS = new Set([
  "enter",
  "tab",
]);
const TEXT_EDITING_SHORTCUT_KEYS = new Set(["a", "c", "v", "x", "z", "y"]);
const AUTOCOMPLETE_TEXT = {
  en: {
    "category.tag": "tag",
    "category.quality": "quality",
    "category.safety": "rating",
    "category.year": "year",
    "category.count": "count",
    "category.artist": "artist",
    "category.character": "character",
    "category.copyright": "copyright",
    "category.general": "general",
    "category.meta": "meta",
    "category.wildcard": "wildcard",
  },
  ko: {
    "category.tag": "태그",
    "category.quality": "품질",
    "category.safety": "등급",
    "category.year": "연도",
    "category.count": "인원수",
    "category.artist": "작가",
    "category.character": "캐릭터",
    "category.copyright": "작품",
    "category.general": "일반",
    "category.meta": "메타",
    "category.wildcard": "와일드카드",
  },
  ja: {
    "category.tag": "タグ",
    "category.quality": "品質",
    "category.safety": "レーティング",
    "category.year": "年代",
    "category.count": "人数",
    "category.artist": "作者",
    "category.character": "キャラクター",
    "category.copyright": "作品",
    "category.general": "一般",
    "category.meta": "メタ",
    "category.wildcard": "ワイルドカード",
  },
  zh: {
    "category.tag": "标签",
    "category.quality": "质量",
    "category.safety": "分级",
    "category.year": "年份",
    "category.count": "人数",
    "category.artist": "作者",
    "category.character": "角色",
    "category.copyright": "作品",
    "category.general": "通用",
    "category.meta": "元数据",
    "category.wildcard": "通配符",
  },
};
const PREVIEW_STYLES = {
  quality: { color: "#facc15", background: "rgba(202, 138, 4, 0.18)", weight: 700 },
  safety: { color: "#38bdf8", background: "rgba(2, 132, 199, 0.18)", weight: 600 },
  year: { color: "#2dd4bf", background: "rgba(13, 148, 136, 0.18)", weight: 600 },
  count: { color: "#60a5fa", background: "rgba(37, 99, 235, 0.18)", weight: 700 },
  character: { color: "#f472b6", background: "rgba(219, 39, 119, 0.18)", weight: 700 },
  artist: { color: "#a78bfa", background: "rgba(124, 58, 237, 0.18)", weight: 700 },
  copyright: { color: "#fb923c", background: "rgba(234, 88, 12, 0.18)", weight: 700 },
  meta: { color: "#94a3b8", background: "rgba(100, 116, 139, 0.18)", weight: 600 },
  general: { color: "#4ade80", background: "rgba(22, 163, 74, 0.16)", weight: 600 },
  wildcard: { color: "#c084fc", background: "rgba(126, 34, 206, 0.24)", weight: 700 },
  syntax: { color: "#a78bfa", background: "transparent", weight: 700 },
  unknown: { color: "#cbd5e1", background: "transparent", weight: 500 },
};
const MIN_QUERY_LENGTH = 1;
const cache = new Map();
let wildcardItemsCache = null;

let maxResults = DEFAULT_MAX_RESULTS;
let autocompleteMode = DEFAULT_AUTOCOMPLETE_MODE;
let autocompleteCommitKey = DEFAULT_AUTOCOMPLETE_COMMIT_KEY;
let autocompleteAppendSeparator = false;
let autocompleteNoCommaAfterPeriod = true;
let autocompleteDetectNaturalSentences = true;
let autocompletePreviewClosingBrackets = false;
let autocompletePreviewCompletion = false;
let popup = null;
let activeState = null;
let activeRefreshFrame = null;
let middlePanForwardActive = false;
const hookedAutocompleteInputs = new Set();
window.__easyuseAnimaPendingAutocompleteInputs ||= [];

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function clampMaxResults(value) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) {
    return DEFAULT_MAX_RESULTS;
  }
  return clamp(parsed, 1, MAX_RESULT_LIMIT);
}

function normalizeAutocompleteMode(value) {
  const normalized = String(value || "").trim();
  return AUTOCOMPLETE_MODES.has(normalized) ? normalized : DEFAULT_AUTOCOMPLETE_MODE;
}

function normalizeAutocompleteCommitKey(value) {
  const normalized = String(value || "").trim();
  return AUTOCOMPLETE_COMMIT_KEYS.has(normalized) ? normalized : DEFAULT_AUTOCOMPLETE_COMMIT_KEY;
}

function setAutocompleteCommitKey(value) {
  autocompleteCommitKey = normalizeAutocompleteCommitKey(value);
}

function parseBooleanSetting(value, defaultValue = false) {
  if (value === true || value === false) {
    return value;
  }
  const normalized = String(value ?? "").trim().toLowerCase();
  if (!normalized) {
    return defaultValue;
  }
  return normalized === "true" || normalized === "1" || normalized === "yes";
}

function setAutocompleteAppendSeparator(value) {
  autocompleteAppendSeparator = parseBooleanSetting(value, false);
}

function setAutocompleteNoCommaAfterPeriod(value) {
  autocompleteNoCommaAfterPeriod = parseBooleanSetting(value, true);
}

function setAutocompleteDetectNaturalSentences(value) {
  autocompleteDetectNaturalSentences = parseBooleanSetting(value, true);
}

function setAutocompletePreviewClosingBrackets(value) {
  autocompletePreviewClosingBrackets = parseBooleanSetting(value, false);
}

function setAutocompletePreviewCompletion(value) {
  autocompletePreviewCompletion = parseBooleanSetting(value, false);
  if (!autocompletePreviewCompletion) {
    clearAutocompletePreview(activeState?.input);
  }
}

function autocompleteText(key) {
  return easyuseAnimaText(AUTOCOMPLETE_TEXT, key);
}

function autocompleteCategoryLabel(category) {
  const raw = String(category || "").trim();
  if (!raw) {
    return autocompleteText("category.tag");
  }
  const key = raw.toLocaleLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  return autocompleteText(`category.${key}`) || raw;
}

function autocompleteEntryMetaText(entry) {
  const count = Number(entry?.count || 0).toLocaleString();
  return entry?.kind === "wildcard"
    ? autocompleteCategoryLabel(entry?.category)
    : `${autocompleteCategoryLabel(entry?.category)} · ${count}`;
}

function autocompleteEntryTooltip(entry) {
  return {
    tag: displayTagText(entry?.tag || ""),
    meta: autocompleteEntryMetaText(entry || {}),
    description: String(entry?.description || ""),
  };
}

function setAutocompleteMode(value) {
  const nextMode = normalizeAutocompleteMode(value);
  if (nextMode === autocompleteMode) {
    return;
  }
  autocompleteMode = nextMode;
  syncAutocompleteInputFlags();
  if (!autocompleteEnabledForState(activeState)) {
    hidePopup();
  }
  cache.clear();
}

function isEasyUseAnimaNode(node) {
  const values = [
    node?.type,
    node?.comfyClass,
    node?.title,
    node?.constructor?.name,
  ].filter(Boolean).map((value) => String(value));
  return values.some((value) => /^EasyUseAnima/.test(value) || /Anima Prompt/i.test(value));
}

function autocompleteScope(options = {}) {
  const scope = String(options.scope || "").trim();
  if (scope === "easyuse" || scope === "compatible") {
    return scope;
  }
  if (options.easyuseOnly || options.dedicated || isEasyUseAnimaNode(options.node)) {
    return "easyuse";
  }
  return "compatible";
}

function autocompleteEnabledForScope(scope) {
  if (autocompleteMode === "off") {
    return false;
  }
  if (autocompleteMode === "easyuse_nodes") {
    return scope === "easyuse";
  }
  return true;
}

function autocompleteEnabledForState(state) {
  return !!state && autocompleteEnabledForScope(state.scope || "compatible");
}

function syncAutocompleteInputFlag(input, state = input?.__easyuseAnimaAutocompleteState) {
  if (!input) {
    return;
  }
  input.__easyuseAnimaAutocomplete = autocompleteEnabledForState(state);
}

function syncAutocompleteInputFlags() {
  for (const input of [...hookedAutocompleteInputs]) {
    const state = input?.__easyuseAnimaAutocompleteState;
    if (!state) {
      hookedAutocompleteInputs.delete(input);
      continue;
    }
    syncAutocompleteInputFlag(input, state);
  }
}

async function refreshAutocompleteSettings() {
  try {
    const settings = await easyuseAnimaGetSettings({ fallback: null });
    if (!settings) {
      return;
    }
    const nextMaxResults = clampMaxResults(settings["autocomplete.limit"]);
    if (nextMaxResults !== maxResults) {
      maxResults = nextMaxResults;
      cache.clear();
    }
    setAutocompleteMode(settings["autocomplete.mode"]);
    setAutocompleteCommitKey(settings["autocomplete.commit_key"]);
    setAutocompleteAppendSeparator(settings["autocomplete.append_separator"]);
    setAutocompleteNoCommaAfterPeriod(settings["autocomplete.no_comma_after_period"]);
    setAutocompleteDetectNaturalSentences(settings["autocomplete.detect_natural_sentences"]);
    setAutocompletePreviewClosingBrackets(settings["autocomplete.preview_closing_brackets"]);
    setAutocompletePreviewCompletion(settings["autocomplete.preview_completion"]);
  } catch {
    // Keep the built-in default if settings cannot be read.
  }
}

function ensureStyle() {
  if (document.getElementById("easyuse-anima-autocomplete-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-autocomplete-style";
  style.textContent = `
    .easyuse-anima-autocomplete {
      position: fixed;
      z-index: 100000;
      max-width: 520px;
      min-width: 280px;
      max-height: 280px;
      overflow: auto;
      overflow-anchor: none;
      overscroll-behavior: contain;
      border: 1px solid rgba(128, 128, 128, 0.45);
      border-radius: 7px;
      background: var(--comfy-menu-bg, #202124);
      color: var(--input-text, #ddd);
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35);
      font: 12px/1.35 sans-serif;
    }
    .easyuse-anima-autocomplete.hidden {
      display: none;
    }
    .easyuse-anima-autocomplete-item {
      padding: 6px 8px;
      cursor: pointer;
      border-bottom: 1px solid rgba(128, 128, 128, 0.16);
    }
    .easyuse-anima-autocomplete-item:last-child {
      border-bottom: 0;
    }
    .easyuse-anima-autocomplete-item.active,
    .easyuse-anima-autocomplete-item:hover {
      background: rgba(99, 102, 241, 0.28);
    }
    .easyuse-anima-autocomplete-tag {
      font-weight: 700;
    }
    .easyuse-anima-autocomplete-meta {
      margin-left: 6px;
      opacity: 0.62;
      font-size: 11px;
    }
    .easyuse-anima-autocomplete-desc {
      margin-top: 2px;
      opacity: 0.78;
      white-space: normal;
    }
  `;
  document.head.append(style);
}

function ensurePopup() {
  ensureStyle();
  if (popup) {
    return popup;
  }
  popup = document.createElement("div");
  popup.className = "easyuse-anima-autocomplete hidden";
  document.body.append(popup);
  return popup;
}

function hidePopup() {
  const input = activeState?.input;
  markAutocompleteInputInactive(input);
  if (popup) {
    popup.replaceChildren();
    resetAutocompleteMenuToTop(popup);
    popup.classList.add("hidden");
  }
  clearAutocompletePreview(input);
  activeState = null;
}

function markAutocompleteInputInactive(input) {
  const state = input?.__easyuseAnimaAutocompleteState;
  if (state) {
    state.lastAutocompleteSignature = "";
  }
}

function hideTrainedTagTooltips() {
  for (const tooltip of document.querySelectorAll(".easyuse-anima-trained-tag-tooltip")) {
    tooltip.classList.add("hidden");
  }
}

function refreshActiveAutocomplete() {
  if (!activeState?.input || document.activeElement !== activeState.input || !autocompleteEnabledForState(activeState)) {
    hidePopup();
    return;
  }
  activeState.reposition?.();
  activeState.refresh?.();
}

function scheduleActiveRefresh() {
  if (activeRefreshFrame != null) {
    cancelAnimationFrame(activeRefreshFrame);
  }
  activeRefreshFrame = requestAnimationFrame(() => {
    activeRefreshFrame = null;
    refreshActiveAutocomplete();
  });
}

function inputTypeName(inputSpec) {
  if (Array.isArray(inputSpec)) {
    return String(inputSpec[0] || "");
  }
  if (typeof inputSpec === "object" && inputSpec !== null) {
    return String(inputSpec.widgetType || inputSpec.type || "");
  }
  return String(inputSpec || "");
}

function inputOptions(inputSpec) {
  if (Array.isArray(inputSpec) && typeof inputSpec[1] === "object" && inputSpec[1] !== null) {
    return inputSpec[1];
  }
  if (typeof inputSpec === "object" && inputSpec !== null) {
    return {
      ...inputSpec,
      ...(inputSpec.options || {}),
    };
  }
  return {};
}

function allInputSpecs(nodeData) {
  const specs = [];
  const v2Inputs = nodeData?.inputs || {};
  for (const [name, spec] of Object.entries(v2Inputs)) {
    specs.push([name, spec]);
  }
  const inputs = nodeData?.input || {};
  for (const group of ["required", "optional"]) {
    const values = inputs[group] || {};
    for (const [name, spec] of Object.entries(values)) {
      if (v2Inputs[name]) {
        continue;
      }
      specs.push([name, spec]);
    }
  }
  return specs;
}

function isExcludedInput(inputSpec) {
  const type = inputTypeName(inputSpec);
  const options = inputOptions(inputSpec);
  const values = [
    type,
    options.widgetType,
    options.placeholder,
    options.tooltip,
  ].filter(Boolean).map((value) => String(value));
  return values.some((value) => EXCLUDED_INPUT_TYPE_PATTERNS.some((pattern) => pattern.test(value)));
}

function isGenericStringNode(nodeData) {
  const values = [nodeData?.name, nodeData?.display_name, nodeData?.category]
    .filter(Boolean)
    .map((value) => String(value));
  return values.some((value) => GENERIC_NODE_PATTERNS.some((pattern) => pattern.test(value)));
}

function isPromptLikeWidgetName(name) {
  return /prompt|tag|text|string|caption|positive|negative/i.test(String(name || ""));
}

function isTargetStringInput(nodeData, name, inputSpec) {
  const type = inputTypeName(inputSpec);
  const options = inputOptions(inputSpec);
  const typeNames = type.split(",").map((item) => item.trim().toUpperCase());
  if (!typeNames.some((item) => item === "STRING" || item === "TEXTAREA")) {
    return false;
  }
  if (isExcludedInput(inputSpec)) {
    return false;
  }
  if (typeNames.includes("TEXTAREA") || options.multiline === true) {
    return isGenericStringNode(nodeData) || isPromptLikeWidgetName(name);
  }
  return isGenericStringNode(nodeData) && isPromptLikeWidgetName(name);
}

function targetWidgets(nodeData) {
  if (TARGETS[nodeData.name]) {
    return TARGETS[nodeData.name];
  }
  if (shouldSkipNode(null, nodeData)) {
    return null;
  }
  const names = new Set();
  for (const [name, spec] of allInputSpecs(nodeData)) {
    if (isTargetStringInput(nodeData, name, spec)) {
      names.add(name);
    }
  }
  return names.size ? names : null;
}

function hasExplicitTargets(nodeData) {
  return !!TARGETS[nodeData?.name];
}

function artistOnlyWidgets(nodeData) {
  return ARTIST_ONLY_TARGETS[nodeData.name] ?? new Set();
}

function shouldSkipNode(node, nodeData) {
  const values = [nodeData?.name, nodeData?.display_name, nodeData?.category, node?.type, node?.title]
    .filter(Boolean)
    .map((value) => String(value));
  return values.some((value) => EXCLUDED_NODE_PATTERNS.some((pattern) => pattern.test(value)));
}

function findInputEl(widget) {
  const input = widget?.inputEl || widget?.element;
  if (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement) {
    return input;
  }
  const nested = input?.querySelector?.("textarea, input");
  if (nested instanceof HTMLTextAreaElement || nested instanceof HTMLInputElement) {
    return nested;
  }
  return null;
}

function currentToken(input) {
  const value = input?.value || "";
  return currentAutocompleteToken(
    value,
    input?.selectionStart ?? value.length,
    {
      detectNaturalSentences: autocompleteDetectNaturalSentences,
      previewCompletion: autocompletePreviewCompletion,
    },
  );
}

function currentWildcardToken(input) {
  const value = input?.value || "";
  return currentAutocompleteWildcardToken(
    value,
    input?.selectionStart ?? value.length,
  );
}

function isCaretInPromptTranslationMarker(input) {
  const value = input?.value || "";
  return caretInPromptTranslationMarker(
    value,
    input?.selectionStart ?? value.length,
  );
}

function autocompleteStateSignature(token, context, state) {
  return JSON.stringify({
    kind: context.kind || "tag",
    value: token.value,
    start: token.start,
    end: token.end,
    caret: token.caret,
    query: context.query,
    category: context.category,
    limit: maxResults,
    forceArtistOnly: !!state.forceArtistOnly,
    noCommaAfterPeriod: autocompleteNoCommaAfterPeriod,
    detectNaturalSentences: autocompleteDetectNaturalSentences,
    previewClosingBrackets: autocompletePreviewClosingBrackets,
    previewCompletion: autocompletePreviewCompletion,
  });
}

function strictAutocompleteResults(context, token, state, results) {
  if (!autocompletePreviewCompletion) {
    return results;
  }
  const rawQuery = context.kind === "wildcard"
    ? String(token?.query || "")
    : parseAutocompleteText(token?.query || "").query;
  const query = context.kind === "wildcard"
    ? normalizeWildcardSearchText(rawQuery)
    : normalizePromptTagText(rawQuery).trim().toLocaleLowerCase();
  if (!query) {
    return context.kind === "wildcard" ? results : [];
  }
  return results.filter((entry) => {
    if (entry?.kind === "wildcard") {
      const candidateKey = normalizeWildcardSearchText(String(entry.tag || "").replace(/^__|__$/g, ""));
      return candidateKey.startsWith(query);
    }
    const candidate = promptTagText(entry?.tag);
    const candidateKey = normalizePromptTagText(candidate).trim().toLocaleLowerCase();
    const descriptionKey = normalizePromptTagText(entry?.description || "").trim().toLocaleLowerCase();
    return candidateKey.startsWith(query) || candidateKey.includes(query) || descriptionKey.includes(query);
  });
}

function copyCaretMirrorStyle(input, mirror) {
  const style = getComputedStyle(input);
  const properties = [
    "boxSizing",
    "width",
    "height",
    "font",
    "fontFamily",
    "fontSize",
    "fontWeight",
    "fontStyle",
    "lineHeight",
    "letterSpacing",
    "padding",
    "border",
    "textAlign",
    "textTransform",
    "tabSize",
  ];
  for (const property of properties) {
    mirror.style[property] = style[property];
  }
}

function caretClientRect(input) {
  const rect = input.getBoundingClientRect();
  const caret = input.selectionStart ?? String(input.value || "").length;
  const mirror = document.createElement("div");
  const marker = document.createElement("span");
  const value = String(input.value || "");
  const layoutWidth = input.offsetWidth || rect.width || 1;
  const layoutHeight = input.offsetHeight || rect.height || 1;
  const scaleX = rect.width > 0 ? rect.width / layoutWidth : 1;
  const scaleY = rect.height > 0 ? rect.height / layoutHeight : scaleX;

  mirror.style.cssText = [
    "position: fixed",
    `left: ${rect.left}px`,
    `top: ${rect.top}px`,
    `width: ${layoutWidth}px`,
    `height: ${layoutHeight}px`,
    `transform: scale(${scaleX}, ${scaleY})`,
    "transform-origin: 0 0",
    "visibility: hidden",
    "overflow: hidden",
    "white-space: pre-wrap",
    "overflow-wrap: break-word",
    "word-break: normal",
    "pointer-events: none",
    "z-index: -1",
  ].join("; ");
  copyCaretMirrorStyle(input, mirror);
  mirror.style.width = `${layoutWidth}px`;
  mirror.style.height = `${layoutHeight}px`;
  mirror.style.transform = `scale(${scaleX}, ${scaleY})`;
  mirror.style.transformOrigin = "0 0";

  if (input instanceof HTMLInputElement) {
    mirror.style.whiteSpace = "pre";
  }

  mirror.textContent = value.slice(0, caret);
  marker.textContent = value.slice(caret, caret + 1) || "\u200b";
  mirror.append(marker);
  document.body.append(mirror);

  mirror.scrollTop = input.scrollTop;
  mirror.scrollLeft = input.scrollLeft;
  const markerRect = marker.getBoundingClientRect();
  mirror.remove();

  if (!Number.isFinite(markerRect.left) || !Number.isFinite(markerRect.top)) {
    return rect;
  }
  return {
    left: markerRect.left,
    right: markerRect.right,
    top: markerRect.top,
    bottom: markerRect.bottom,
    width: markerRect.width,
    height: markerRect.height || Number.parseFloat(getComputedStyle(input).lineHeight) || 18,
  };
}

function positionPopup(input) {
  const menu = ensurePopup();
  const inputRect = input.getBoundingClientRect();
  const caretRect = caretClientRect(input);
  const width = Math.max(260, Math.min(380, inputRect.width, window.innerWidth - 8));
  const lineHeight = Math.max(14, caretRect.height || Number.parseFloat(getComputedStyle(input).lineHeight) || 18);
  const caretLeft = clamp(caretRect.left, inputRect.left, inputRect.right);
  const caretTop = clamp(
    caretRect.top,
    inputRect.top,
    Math.max(inputRect.top, inputRect.bottom - lineHeight),
  );
  const caretBottom = clamp(
    caretTop + lineHeight,
    inputRect.top + lineHeight,
    inputRect.bottom,
  );
  const left = clamp(caretLeft, 4, Math.max(4, window.innerWidth - width - 4));
  const top = caretBottom + lineHeight + 12;
  const maxHeight = Math.max(56, window.innerHeight - top - 8);
  menu.style.left = `${left}px`;
  menu.style.top = `${top}px`;
  menu.style.width = `${width}px`;
  menu.style.maxHeight = `${Math.min(280, maxHeight)}px`;
}

async function search(query, category = "") {
  const key = `${category || "all"}:${maxResults}:${query.toLocaleLowerCase()}`;
  if (cache.has(key)) {
    return cache.get(key);
  }
  const categoryParam = category ? `&category=${encodeURIComponent(category)}` : "";
  const data = await easyuseAnimaFetchJson(
    `/easyuse_anima/autocomplete?q=${encodeURIComponent(query)}&limit=${maxResults}${categoryParam}`,
  );
  const results = Array.isArray(data.results) ? data.results : [];
  cache.set(key, results);
  return results;
}

async function loadWildcardItems() {
  if (Array.isArray(wildcardItemsCache)) {
    return wildcardItemsCache;
  }
  const data = await easyuseAnimaFetchJson("/easyuse_anima/wildcards");
  wildcardItemsCache = Array.isArray(data.items) ? data.items.map((item) => String(item || "")).filter(Boolean) : [];
  return wildcardItemsCache;
}

async function searchWildcards(query) {
  const normalized = normalizeWildcardSearchText(query);
  const key = `wildcard:${maxResults}:${normalized}`;
  if (cache.has(key)) {
    return cache.get(key);
  }
  const items = await loadWildcardItems();
  const results = items
    .filter((item) => !normalized || normalizeWildcardSearchText(item).includes(normalized))
    .slice(0, maxResults)
    .map((item) => ({
      tag: item,
      category: "wildcard",
      count: 0,
      kind: "wildcard",
    }));
  cache.set(key, results);
  return results;
}

function scrollActiveAutocompleteItemIntoView(menu, index) {
  const children = [...(menu?.children || [])];
  const active = children[index];
  if (!active || !menu.clientHeight) {
    return;
  }
  const firstVisibleIndex = Math.max(0, index - 1);
  const lastVisibleIndex = Math.min(children.length - 1, index + 1);
  const first = children[firstVisibleIndex] || active;
  const last = children[lastVisibleIndex] || active;
  const targetTop = first.offsetTop;
  const targetBottom = last.offsetTop + last.offsetHeight;
  const viewTop = menu.scrollTop;
  const viewBottom = viewTop + menu.clientHeight;
  if (targetTop < viewTop) {
    menu.scrollTop = targetTop;
  } else if (targetBottom > viewBottom) {
    menu.scrollTop = targetBottom - menu.clientHeight;
  }
}

function setActive(index) {
  if (!activeState) {
    return;
  }
  const count = activeState.results.length;
  if (!count) {
    return;
  }
  activeState.index = (index + count) % count;
  const menu = ensurePopup();
  [...menu.children].forEach((child, childIndex) => {
    child.classList.toggle("active", childIndex === activeState.index);
  });
  scrollActiveAutocompleteItemIntoView(menu, activeState.index);
  updateAutocompletePreview();
}

function resetAutocompleteMenuToTop(menu) {
  if (!menu) {
    return;
  }
  menu.scrollTop = 0;
  menu.scrollLeft = 0;
}

function resetActiveAutocompleteMenu(menu) {
  if (!activeState) {
    return;
  }
  activeState.index = 0;
  [...(menu?.children || [])].forEach((child, childIndex) => {
    child.classList.toggle("active", childIndex === activeState.index);
  });
  resetAutocompleteMenuToTop(menu);
}

function resetVisibleAutocompleteMenuSoon(menu, input) {
  resetAutocompleteMenuToTop(menu);
  requestAnimationFrame(() => {
    if (popup === menu && activeState?.input === input && !menu.classList.contains("hidden")) {
      resetAutocompleteMenuToTop(menu);
    }
  });
}

function replaceInputRange(input, start, end, replacement, caretOffset) {
  input.focus?.();
  input.setSelectionRange(start, end);
  const beforeValue = input.value;
  let changedByCommand = false;
  if (typeof document.execCommand === "function") {
    changedByCommand = document.execCommand("insertText", false, replacement);
  }
  if (!changedByCommand || input.value === beforeValue) {
    input.setRangeText(replacement, start, end, "end");
    input.dispatchEvent(new Event("input", { bubbles: true }));
  }
  const caret = start + caretOffset;
  input.setSelectionRange(caret, caret);
}

function suppressAutocompleteUntilInputChanges(input) {
  if (!input) {
    return;
  }
  const start = input.selectionStart ?? 0;
  input.__easyuseAnimaSuppressAutocomplete = {
    value: input.value || "",
    selectionStart: start,
    selectionEnd: input.selectionEnd ?? start,
  };
}

function shouldSuppressAutocomplete(input) {
  const suppression = input?.__easyuseAnimaSuppressAutocomplete;
  if (!suppression) {
    return false;
  }
  const start = input.selectionStart ?? 0;
  const end = input.selectionEnd ?? start;
  if (
    suppression.value === (input.value || "")
    && suppression.selectionStart === start
    && suppression.selectionEnd === end
  ) {
    return true;
  }
  input.__easyuseAnimaSuppressAutocomplete = null;
  return false;
}

function dispatchAutocompleteCanvasPointerEvent(type, sourceEvent, overrides = {}) {
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

function dispatchAutocompleteCanvasMouseEvent(type, sourceEvent, overrides = {}) {
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

function forwardMiddlePanFromAutocompleteInput(event) {
  if (event.__easyuseAnimaForwarded || event.button !== 1 || !app.canvas?.canvas) {
    return false;
  }
  event.preventDefault();
  event.stopPropagation();
  if (middlePanForwardActive) {
    return true;
  }
  middlePanForwardActive = true;
  document.activeElement?.blur?.();
  dispatchAutocompleteCanvasPointerEvent("pointerdown", event, { button: 1, buttons: 4 });
  dispatchAutocompleteCanvasMouseEvent("mousedown", event, { button: 1, buttons: 4 });

  const move = (moveEvent) => {
    if (moveEvent.__easyuseAnimaForwarded) {
      return;
    }
    moveEvent.preventDefault();
    moveEvent.stopPropagation();
    dispatchAutocompleteCanvasPointerEvent("pointermove", moveEvent, { button: 1, buttons: 4 });
    dispatchAutocompleteCanvasMouseEvent("mousemove", moveEvent, { button: 1, buttons: 4 });
  };
  const stop = (upEvent) => {
    if (upEvent.__easyuseAnimaForwarded) {
      return;
    }
    upEvent.preventDefault();
    upEvent.stopPropagation();
    dispatchAutocompleteCanvasPointerEvent("pointerup", upEvent, { button: 1, buttons: 0 });
    dispatchAutocompleteCanvasMouseEvent("mouseup", upEvent, { button: 1, buttons: 0 });
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

function commitSuggestion(state, entry, options = {}) {
  const promptToken = currentToken(state.input);
  const wildcardToken = entry?.kind === "wildcard" ? currentWildcardToken(state.input) : null;
  const token = wildcardToken || promptToken;
  const insert = completionText(token, entry, state.forceArtistOnly);
  const plan = planAutocompleteInsertion(token, insert, {
    appendSeparator: autocompleteAppendSeparator,
    noCommaAfterPeriod: autocompleteNoCommaAfterPeriod,
  });
  if (!plan) {
    return;
  }
  replaceInputRange(
    state.input,
    plan.start,
    plan.end,
    plan.replacement,
    plan.caretOffset,
  );
  syncWidgetValue(state);
  state.onCommit?.(state.input.value);
  if (options.suppressPopup) {
    suppressAutocompleteUntilInputChanges(state.input);
  }
  hidePopup();
}

function displayTagText(value) {
  return normalizePromptTagText(value);
}

function promptTagText(value) {
  return promptCompletionTagText(value);
}

function completionText(token, entry, forceArtistOnly = false) {
  if (entry?.kind === "wildcard") {
    return `__${String(entry.tag || "").replace(/^__|__$/g, "")}__`;
  }
  const tag = promptTagText(entry?.tag);
  const query = parseAutocompleteText(token.query);
  const artistOnly = forceArtistOnly || query.artistOnly;
  if (artistOnly) {
    return `@${tag}`;
  }
  return tag;
}

function closingBracketPreview(token) {
  if (!autocompletePreviewClosingBrackets || !token) {
    return "";
  }
  const before = token.value.slice(token.segmentStart, token.start);
  const after = token.value.slice(token.end, token.segmentEnd);
  if (before.includes("[[") && !after.includes("]]")) {
    return "]]";
  }
  if (before.includes("(") && !after.includes(")")) {
    return ")";
  }
  if (before.includes("{") && !after.includes("}")) {
    return "}";
  }
  return "";
}

function autocompletePreviewStyle(category) {
  return PREVIEW_STYLES[category] || PREVIEW_STYLES.unknown;
}

function refreshAutocompleteHighlightPreview(input) {
  input?.__easyuseAnimaHighlightRefresh?.(false);
}

function clearAutocompletePreview(input) {
  if (!input?.__easyuseAnimaAutocompletePreview) {
    return;
  }
  input.__easyuseAnimaAutocompletePreview = null;
  refreshAutocompleteHighlightPreview(input);
}

function autocompletePreviewCategory(state, entry, token) {
  if (entry?.kind === "wildcard") {
    return "wildcard";
  }
  const query = parseAutocompleteText(token?.query || "");
  return state?.forceArtistOnly || query.artistOnly
    ? "artist"
    : String(entry?.category || "general").toLocaleLowerCase();
}

function normalizedCompletionPreviewText(value) {
  return normalizePromptTagText(value).toLocaleLowerCase();
}

function typedCompletionLength(token, insert) {
  const typedRaw = token.value.slice(token.start, Math.min(token.caret, token.end));
  if (!typedRaw) {
    return 0;
  }
  if (insert.toLocaleLowerCase().startsWith(typedRaw.toLocaleLowerCase())) {
    return typedRaw.length;
  }
  const typedNormalized = normalizedCompletionPreviewText(typedRaw.replace(/^@/, ""));
  if (
    typedRaw.startsWith("@")
    && insert.startsWith("@")
    && typedNormalized
    && normalizedCompletionPreviewText(insert.slice(1)).startsWith(typedNormalized)
  ) {
    return typedRaw.length;
  }
  return 0;
}

function completionPreviewPlan(state, entry) {
  if (!state?.input) {
    return null;
  }
  const sourceValue = String(state.input.value || "");
  const wildcardToken = entry?.kind === "wildcard" ? currentWildcardToken(state.input) : null;
  if (entry?.kind === "wildcard" && !wildcardToken) {
    return null;
  }
  const token = wildcardToken || currentToken(state.input);
  const insert = completionText(token, entry, state.forceArtistOnly);
  const plan = planAutocompleteInsertion(token, insert, {
    appendSeparator: autocompleteAppendSeparator,
    noCommaAfterPeriod: autocompleteNoCommaAfterPeriod,
  });
  if (!plan) {
    return null;
  }
  let typedLength;
  if (token.wildcard) {
    const typed = token.value.slice(token.start, token.caret);
    const lowerInsert = insert.toLocaleLowerCase();
    const lowerTyped = typed.toLocaleLowerCase();
    typedLength = typed && lowerInsert.startsWith(lowerTyped)
      ? typed.length
      : 0;
  } else {
    typedLength = plan.prefix ? 0 : typedCompletionLength(token, insert);
  }
  const value = `${sourceValue.slice(0, plan.start)}${plan.replacement}${sourceValue.slice(plan.end)}`;
  const candidateStart = plan.start + plan.prefix.length;
  const candidateEnd = candidateStart + insert.length;
  const ghostStart = candidateStart + typedLength;
  const ghostEnd = candidateEnd;
  return {
    sourceValue,
    value,
    candidateStart,
    candidateEnd,
    ghostStart,
    ghostEnd,
    category: token.wildcard
      ? "wildcard"
      : autocompletePreviewCategory(state, entry, token),
  };
}

function updateAutocompletePreview() {
  if (!autocompletePreviewCompletion || !activeState?.input || popup?.classList.contains("hidden")) {
    clearAutocompletePreview(activeState?.input);
    return;
  }
  const input = activeState.input;
  if (document.activeElement !== input || !activeState.results?.length) {
    clearAutocompletePreview(input);
    return;
  }
  const entry = activeState.results[activeState.index];
  const preview = completionPreviewPlan(activeState, entry);
  if (
    !preview?.value
    || preview.value === preview.sourceValue
    || preview.ghostEnd <= preview.ghostStart
  ) {
    clearAutocompletePreview(input);
    return;
  }
  const style = autocompletePreviewStyle(preview.category);
  const nextPreview = {
    ...preview,
    color: style.color,
  };
  const current = input.__easyuseAnimaAutocompletePreview;
  if (
    current?.sourceValue === nextPreview.sourceValue
    && current?.value === nextPreview.value
    && current?.candidateStart === nextPreview.candidateStart
    && current?.candidateEnd === nextPreview.candidateEnd
    && current?.ghostStart === nextPreview.ghostStart
    && current?.ghostEnd === nextPreview.ghostEnd
    && current?.color === nextPreview.color
  ) {
    return;
  }
  input.__easyuseAnimaAutocompletePreview = nextPreview;
  refreshAutocompleteHighlightPreview(input);
}

function insertBracketPair(state, event, open, close, replacement = null, caretOffset = null) {
  if (!autocompletePreviewClosingBrackets || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) {
    return false;
  }
  const input = state?.input;
  if (!input || input.selectionStart == null || input.selectionEnd == null) {
    return false;
  }
  event.preventDefault();
  const start = input.selectionStart;
  const end = input.selectionEnd;
  const selected = input.value.slice(start, end);
  const text = replacement ?? `${open}${selected}${close}`;
  const offset = caretOffset ?? (open.length + selected.length);
  replaceInputRange(input, start, end, text, offset);
  syncWidgetValue(state);
  return true;
}

function handleBracketPreviewKeydown(state, event) {
  const input = state?.input;
  if (!input || !autocompletePreviewClosingBrackets || event.defaultPrevented) {
    return false;
  }
  const start = input.selectionStart ?? 0;
  const end = input.selectionEnd ?? start;
  if (event.key === "(") {
    return insertBracketPair(state, event, "(", ")");
  }
  if (event.key === "{") {
    return insertBracketPair(state, event, "{", "}");
  }
  if (event.key === "[" && start === end && input.value[start - 1] === "[") {
    return insertBracketPair(state, event, "[", "]]", "[]]", 1);
  }
  if ((event.key === ")" || event.key === "]" || event.key === "}") && start === end && input.value[start] === event.key) {
    event.preventDefault();
    input.setSelectionRange(start + 1, start + 1);
    return true;
  }
  return false;
}

function widgetValueSetterCallsCallback(widget) {
  return !!widget?.element;
}

function syncWidgetValue(state) {
  if (state?.widget) {
    state.widget.value = state.input.value;
    if (!widgetValueSetterCallsCallback(state.widget)) {
      state.widget.callback?.(state.input.value);
    }
  }
}

function renderResults(state, results, signature = "") {
  const menu = ensurePopup();
  resetAutocompleteMenuToTop(menu);
  if (activeState?.input && activeState.input !== state.input) {
    clearAutocompletePreview(activeState.input);
  }
  menu.replaceChildren();
  activeState = {
    ...state,
    results,
    signature,
    index: 0,
  };

  if (!results.length) {
    hidePopup();
    return;
  }

  for (const [index, entry] of results.entries()) {
    const item = document.createElement("div");
    item.className = "easyuse-anima-autocomplete-item";
    if (index === activeState.index) {
      item.classList.add("active");
    }

    const top = document.createElement("div");
    const tag = document.createElement("span");
    tag.className = "easyuse-anima-autocomplete-tag";
    tag.textContent = displayTagText(entry.tag);

    const meta = document.createElement("span");
    meta.className = "easyuse-anima-autocomplete-meta";
    meta.textContent = autocompleteEntryMetaText(entry);
    top.append(tag, meta);
    item.append(top);

    if (entry.description) {
      const desc = document.createElement("div");
      desc.className = "easyuse-anima-autocomplete-desc";
      desc.textContent = entry.description;
      item.append(desc);
    }

    item.addEventListener("mousedown", (event) => {
      if (event.button !== 0) {
        return;
      }
      event.preventDefault();
      commitSuggestion(activeState, entry, {
        suppressPopup: true,
      });
    });
    menu.append(item);
  }
  resetActiveAutocompleteMenu(menu);

  positionPopup(state.input);
  hideTrainedTagTooltips();
  menu.classList.remove("hidden");
  resetActiveAutocompleteMenu(menu);
  resetVisibleAutocompleteMenuSoon(menu, state.input);
  updateAutocompletePreview();
}

function debounce(fn, delay = 120) {
  let timer = null;
  const wrapped = (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
  wrapped.cancel = () => clearTimeout(timer);
  return wrapped;
}

function isTextEditingShortcut(event) {
  if (!(event.ctrlKey || event.metaKey) || event.altKey) {
    return false;
  }
  return TEXT_EDITING_SHORTCUT_KEYS.has(String(event.key || "").toLocaleLowerCase());
}

function hookInput(input, options = {}) {
  if (!input) {
    return;
  }
  if (input.__easyuseAnimaAutocompleteHooked) {
    const existing = input.__easyuseAnimaAutocompleteState;
    if (existing) {
      existing.node = options.node || existing.node || null;
      existing.widget = options.widget || existing.widget || null;
      existing.scope = autocompleteScope(options);
      existing.forceArtistOnly = !!options.forceArtistOnly;
      existing.onCommit = typeof options.onCommit === "function" ? options.onCommit : existing.onCommit;
      syncAutocompleteInputFlag(input, existing);
    }
    return;
  }

  let composing = false;
  let updateSeq = 0;
  const state = {
    node: options.node || null,
    widget: options.widget || null,
    input,
    scope: autocompleteScope(options),
    forceArtistOnly: !!options.forceArtistOnly,
    onCommit: typeof options.onCommit === "function" ? options.onCommit : null,
    lastAutocompleteSignature: undefined,
  };

  const markAutocompleteInactive = () => {
    state.lastAutocompleteSignature = "";
  };

  const updateNow = async () => {
    if (document.activeElement !== input || !autocompleteEnabledForState(state)) {
      if (activeState?.input === input) {
        hidePopup();
      }
      return;
    }
    if (shouldSuppressAutocomplete(input)) {
      markAutocompleteInactive();
      if (activeState?.input === input) {
        hidePopup();
      }
      return;
    }
    if (isCaretInComment(input.value || "", input.selectionStart ?? 0)) {
      markAutocompleteInactive();
      hidePopup();
      return;
    }
    if (isCaretInPromptTranslationMarker(input)) {
      markAutocompleteInactive();
      hidePopup();
      return;
    }
    const wildcardToken = currentWildcardToken(input);
    const token = wildcardToken || currentToken(input);
    if (!token?.active) {
      markAutocompleteInactive();
      hidePopup();
      return;
    }
    const context = wildcardToken
      ? wildcardAutocompleteQuery(wildcardToken)
      : autocompleteQuery(token, state.forceArtistOnly);
    if (context.kind !== "wildcard" && context.query.length < MIN_QUERY_LENGTH) {
      markAutocompleteInactive();
      hidePopup();
      return;
    }
    const signature = autocompleteStateSignature(token, context, state);
    const previousSignature = state.lastAutocompleteSignature;
    state.lastAutocompleteSignature = signature;
    if (activeState?.input === input && activeState.signature === signature) {
      if (previousSignature !== undefined && previousSignature !== signature) {
        resetActiveAutocompleteMenu(ensurePopup());
      }
      positionPopup(input);
      updateAutocompletePreview();
      return;
    }
    const seq = ++updateSeq;
    try {
      const results = context.kind === "wildcard"
        ? await searchWildcards(context.query)
        : await search(context.query, context.category);
      if (document.activeElement === input && seq === updateSeq && !shouldSuppressAutocomplete(input)) {
        renderResults(state, strictAutocompleteResults(context, token, state, results), signature);
      }
    } catch {
      hidePopup();
    }
  };
  const update = debounce(updateNow);
  const updateFromCaret = () => {
    update.cancel();
    updateNow();
  };
  const updateAfterCaretMove = () => {
    update.cancel();
    requestAnimationFrame(updateNow);
    setTimeout(updateNow, 0);
  };
  state.refresh = updateFromCaret;
  state.reposition = () => positionPopup(input);

  input.addEventListener("compositionstart", () => {
    composing = true;
  });
  input.addEventListener("compositionupdate", update);
  input.addEventListener("compositionend", () => {
    composing = false;
    updateAfterCaretMove();
  });
  input.addEventListener("input", update);
  input.addEventListener("focus", updateFromCaret);
  input.addEventListener("click", updateAfterCaretMove);
  input.addEventListener("mousedown", updateAfterCaretMove);
  input.addEventListener("mouseup", updateAfterCaretMove);
  input.addEventListener("pointerup", updateAfterCaretMove);
  input.addEventListener("pointerdown", (event) => {
    if (forwardMiddlePanFromAutocompleteInput(event)) {
      hidePopup();
    }
  }, true);
  input.addEventListener("mousedown", (event) => {
    if (forwardMiddlePanFromAutocompleteInput(event)) {
      hidePopup();
    }
  }, true);
  input.addEventListener("auxclick", (event) => {
    if (event.button === 1) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);
  input.addEventListener("keyup", (event) => {
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", "PageUp", "PageDown"].includes(event.key)) {
      updateAfterCaretMove();
    }
  });
  input.addEventListener("select", updateAfterCaretMove);
  input.addEventListener("blur", () => {
    setTimeout(() => {
      if (activeState?.input === input) {
        hidePopup();
      }
    }, 120);
  });
  input.addEventListener("keydown", (event) => {
    if (isTextEditingShortcut(event)) {
      event.stopPropagation();
    }
  });
  input.addEventListener("keydown", (event) => {
    if (handleBracketPreviewKeydown(state, event)) {
      updateAfterCaretMove();
    }
  });
  input.addEventListener("keydown", (event) => {
    if (composing || event.isComposing || event.keyCode === 229) {
      return;
    }
    if (!activeState || activeState.input !== input) {
      return;
    }
    if (event.key === "Enter" && event.shiftKey) {
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive(activeState.index + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive(activeState.index - 1);
    } else if (
      (event.key === "Tab" && !event.shiftKey)
      || (event.key === "Enter" && autocompleteCommitKey === "enter")
    ) {
      event.preventDefault();
      commitSuggestion(activeState, activeState.results[activeState.index], {
        suppressPopup: true,
      });
    } else if (event.key === "Escape") {
      event.preventDefault();
      hidePopup();
    }
  });

  input.__easyuseAnimaAutocompleteHooked = true;
  input.__easyuseAnimaAutocompleteState = state;
  hookedAutocompleteInputs.add(input);
  syncAutocompleteInputFlag(input, state);
}

function hookWidget(node, widget, scope = "compatible") {
  const input = findInputEl(widget);
  hookInput(input, {
    node,
    widget,
    scope,
    forceArtistOnly: !!node.__easyuseAnimaArtistOnlyWidgets?.has(widget.name),
  });
}

function autocompleteGraphNodes() {
  const graph = app?.canvas?.graph || app?.graph || app?.rootGraph;
  return Array.isArray(graph?.nodes) ? graph.nodes.filter(Boolean) : [];
}

function findGraphNodeById(id) {
  if (id == null || id === "") {
    return null;
  }
  const graph = app?.canvas?.graph || app?.graph || app?.rootGraph;
  const normalized = String(id);
  return graph?.getNodeById?.(id)
    || graph?.getNodeById?.(Number(id))
    || autocompleteGraphNodes().find((node) => String(node?.id) === normalized)
    || null;
}

function nodeFromDomElement(element) {
  if (!(element instanceof Element)) {
    return null;
  }
  const root = element.closest?.("[data-node-id], .lg-node");
  const id = root?.getAttribute?.("data-node-id")
    || root?.dataset?.nodeId
    || root?.id?.match?.(/\d+/)?.[0];
  return findGraphNodeById(id);
}

function isAutocompleteDomInput(input) {
  if (input instanceof HTMLTextAreaElement) {
    return !input.disabled && !input.readOnly;
  }
  if (!(input instanceof HTMLInputElement) || input.disabled || input.readOnly) {
    return false;
  }
  const type = String(input.type || "text").toLocaleLowerCase();
  return ["", "text", "search"].includes(type);
}

function widgetForDomInput(node, input) {
  for (const widget of node?.widgets || []) {
    const widgetInput = findInputEl(widget);
    if (widgetInput === input || widget?.element?.contains?.(input)) {
      return widget;
    }
  }
  return null;
}

function hookFocusedDomInput(input) {
  if (!isAutocompleteDomInput(input) || popup?.contains(input)) {
    return;
  }
  const node = nodeFromDomElement(input);
  if (!node) {
    return;
  }
  const nodeData = node?.constructor?.nodeData || null;
  const targets = nodeData ? targetWidgets(nodeData) : null;
  if (nodeData && (!targets || (!hasExplicitTargets(nodeData) && shouldSkipNode(node, nodeData)))) {
    return;
  }
  const widget = widgetForDomInput(node, input);
  if (targets && widget?.name && !targets.has(widget.name)) {
    return;
  }
  const scope = nodeData && hasExplicitTargets(nodeData) ? "easyuse" : autocompleteScope({ node });
  hookInput(input, {
    node,
    widget,
    scope,
    forceArtistOnly: !!(widget?.name && node?.__easyuseAnimaArtistOnlyWidgets?.has(widget.name)),
  });
}

function installExternalInputHook() {
  window.easyuseAnimaHookAutocompleteInput = (input, options = {}) => {
    hookInput(input, options);
  };
  window.easyuseAnimaAutocompleteEntryTooltip = (entry) => autocompleteEntryTooltip(entry);
  const pending = window.__easyuseAnimaPendingAutocompleteInputs || [];
  window.__easyuseAnimaPendingAutocompleteInputs = [];
  for (const item of pending) {
    hookInput(item?.input, item?.options || {});
  }
  document.addEventListener("focusin", (event) => {
    hookFocusedDomInput(event.target);
  }, true);
  hookFocusedDomInput(document.activeElement);
}

function hookNode(node, nodeData, attempt = 0) {
  const names = targetWidgets(nodeData);
  if (!names || (!hasExplicitTargets(nodeData) && shouldSkipNode(node, nodeData))) {
    return;
  }
  const scope = hasExplicitTargets(nodeData) ? "easyuse" : "compatible";
  node.__easyuseAnimaArtistOnlyWidgets = artistOnlyWidgets(nodeData);
  let pendingInput = false;
  for (const widget of node.widgets || []) {
    if (names.has(widget.name)) {
      if (!findInputEl(widget)) {
        pendingInput = true;
      }
      hookWidget(node, widget, scope);
    }
  }
  if (pendingInput && attempt < 12) {
    setTimeout(() => hookNode(node, nodeData, attempt + 1), 80);
  }
}

document.addEventListener("scroll", (event) => {
  if (popup?.contains(event.target)) {
    return;
  }
  scheduleActiveRefresh();
}, true);
document.addEventListener("wheel", (event) => {
  if (popup?.contains(event.target)) {
    return;
  }
  scheduleActiveRefresh();
}, true);
function handleOutsideAutocompletePointer(event) {
  if (!activeState || popup?.contains(event.target)) {
    return;
  }
  const input = activeState.input;
  if (event.target === input || input?.contains?.(event.target)) {
    return;
  }
  markAutocompleteInputInactive(input);
  hidePopup();
}

document.addEventListener("pointerdown", handleOutsideAutocompletePointer, true);
document.addEventListener("mousedown", handleOutsideAutocompletePointer, true);
document.addEventListener("selectionchange", scheduleActiveRefresh);
window.addEventListener("resize", scheduleActiveRefresh);
window.addEventListener("easyuse-anima-settings-updated", (event) => {
  const detail = event?.detail || {};
  if ("autocomplete.mode" in detail) {
    setAutocompleteMode(detail["autocomplete.mode"]);
  }
  if ("autocomplete.commit_key" in detail) {
    setAutocompleteCommitKey(detail["autocomplete.commit_key"]);
  }
  if ("autocomplete.append_separator" in detail) {
    setAutocompleteAppendSeparator(detail["autocomplete.append_separator"]);
  }
  if ("autocomplete.no_comma_after_period" in detail) {
    setAutocompleteNoCommaAfterPeriod(detail["autocomplete.no_comma_after_period"]);
  }
  if ("autocomplete.detect_natural_sentences" in detail) {
    setAutocompleteDetectNaturalSentences(detail["autocomplete.detect_natural_sentences"]);
  }
  if ("autocomplete.preview_closing_brackets" in detail) {
    setAutocompletePreviewClosingBrackets(detail["autocomplete.preview_closing_brackets"]);
  }
  if ("autocomplete.preview_completion" in detail) {
    setAutocompletePreviewCompletion(detail["autocomplete.preview_completion"]);
  }
  if ("autocomplete.limit" in detail) {
    maxResults = clampMaxResults(detail["autocomplete.limit"]);
    cache.clear();
  }
  if ("autocomplete.source" in detail) {
    cache.clear();
    hidePopup();
  }
  if ("wildcard.extra_paths" in detail) {
    wildcardItemsCache = null;
    cache.clear();
    hidePopup();
  }
  scheduleActiveRefresh();
});

app.registerExtension({
  name: "easyuse-anima.autocomplete",
  async setup() {
    installExternalInputHook();
    await refreshAutocompleteSettings();
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!targetWidgets(nodeData)) {
      return;
    }

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      hookNode(this, nodeData);
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      onConfigure?.apply(this, arguments);
      hookNode(this, nodeData);
    };
  },
});
