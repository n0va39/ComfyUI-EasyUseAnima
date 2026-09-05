// @ts-expect-error ComfyUI provides this host module outside the custom-node typecheck root.
import { app } from "../../../scripts/app.js";
import {
  normalizePromptTagText,
  promptCompletionTagText,
} from "./easyuse_anima_prompt_rules.js";
import { easyuseAnimaFetchJson, easyuseAnimaGetSettings } from "./easyuse_anima_api.js";
import { easyuseAnimaText } from "./easyuse_anima_i18n.js";
import { createAutocompleteDataAdapter } from "./autocomplete/data_adapter.js";
import {
  createAutocompleteInputController,
  invalidateAutocompleteControllerStates,
} from "./autocomplete/input_controller.js";
import { createAutocompleteInputBinding } from "./autocomplete/input_binding.js";
import { createAutocompleteEntryLifecycle } from "./autocomplete/entry_lifecycle.js";
import {
  calculateAutocompletePopupGeometry,
  calculateCaretMirrorGeometry,
  normalizeCaretClientRect,
} from "./autocomplete/popup_geometry.js";
import {
  artistCompletionText,
  autocompleteQuery,
  currentLoraToken as currentAutocompleteLoraToken,
  currentToken as currentAutocompleteToken,
  currentWildcardToken as currentAutocompleteWildcardToken,
  isCaretInComment,
  isCaretInPromptTranslationMarker as caretInPromptTranslationMarker,
  loraAutocompleteQuery,
  normalizeAutocompleteArtistPrefix,
  normalizeAutocompleteCommitMode,
  normalizeLoraSearchText,
  normalizeWildcardSearchText,
  parseAutocompleteText,
  planAutocompleteInsertion,
  planBracketInsertion,
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
  EasyUseAnimaWildcardLora: new Set([
    "text",
    "populated_text",
  ]),
};

const ARTIST_ONLY_TARGETS = {
  EasyUseAnimaLoraPreset: new Set([
    "style_prompt",
  ]),
};

const LORA_AUTOCOMPLETE_NODE_TYPES = new Set([
  "EasyUseAnimaPromptStudioAdvancedV2",
  "EasyUseAnimaPromptStudioAdvancedLora",
  "EasyUseAnimaWildcardLora",
]);

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
const DEFAULT_AUTOCOMPLETE_COMMIT_MODE = "smart";
const DEFAULT_AUTOCOMPLETE_ARTIST_PREFIX = "@";
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
    "category.lora": "LoRA",
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
    "category.lora": "LoRA",
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
    "category.lora": "LoRA",
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
    "category.lora": "LoRA",
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
  lora: { color: "#e879f9", background: "rgba(192, 38, 211, 0.22)", weight: 700 },
  syntax: { color: "#a78bfa", background: "transparent", weight: 700 },
  unknown: { color: "#cbd5e1", background: "transparent", weight: 500 },
};
const MIN_QUERY_LENGTH = 1;

let maxResults = DEFAULT_MAX_RESULTS;
let autocompleteMode = DEFAULT_AUTOCOMPLETE_MODE;
let autocompleteCommitKey = DEFAULT_AUTOCOMPLETE_COMMIT_KEY;
let autocompleteCommitMode = DEFAULT_AUTOCOMPLETE_COMMIT_MODE;
let autocompleteArtistPrefix = DEFAULT_AUTOCOMPLETE_ARTIST_PREFIX;
let autocompleteAppendSeparator = false;
let autocompleteNoCommaAfterPeriod = true;
let autocompleteDetectNaturalSentences = true;
let autocompletePreviewClosingBrackets = false;
let autocompletePreviewCompletion = false;
let promptStudioSelectionParenthesisWeight = false;
let promptStudioLoraAutocomplete = true;
let popup = null;
let activeState = null;
let activeRefreshFrame = null;
let activeRefreshNeedsUpdate = false;
let middlePanForwardCleanup = null;
const autocompleteInputOwner = {};
const hookedAutocompleteInputs = new Set();
let autocompleteEntryLifecycle = null;

const autocompleteData = createAutocompleteDataAdapter({
  fetchJson: easyuseAnimaFetchJson,
  normalizeWildcardSearchText,
  normalizeLoraSearchText,
  getLimit: () => maxResults,
});

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

function setPromptStudioSelectionParenthesisWeight(value) {
  promptStudioSelectionParenthesisWeight = parseBooleanSetting(value, false);
}

function setAutocompletePreviewCompletion(value) {
  autocompletePreviewCompletion = parseBooleanSetting(value, false);
  if (!autocompletePreviewCompletion) {
    clearAutocompletePreview(activeState?.input);
  }
}

function setPromptStudioLoraAutocomplete(value) {
  const next = parseBooleanSetting(value, true);
  const changed = next !== promptStudioLoraAutocomplete;
  promptStudioLoraAutocomplete = next;
  return changed;
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
  return entry?.kind === "wildcard" || entry?.kind === "lora"
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
  autocompleteData.clearResults();
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
  if (!input.__easyuseAnimaAutocomplete) {
    state?.controller?.invalidate();
  }
}

function disposeAutocompleteInput(input, expectedState = input?.__easyuseAnimaAutocompleteState) {
  if (!input) {
    return;
  }
  if (!expectedState) {
    const staleDispose = input.__easyuseAnimaAutocompleteDispose;
    if (typeof staleDispose === "function") {
      staleDispose();
    }
    if (!input.__easyuseAnimaAutocompleteState) {
      hookedAutocompleteInputs.delete(input);
      delete input.__easyuseAnimaAutocompleteHooked;
      delete input.__easyuseAnimaAutocompleteDispose;
      input.__easyuseAnimaAutocomplete = false;
    }
    return;
  }
  if (typeof expectedState.dispose === "function") {
    expectedState.dispose();
    return;
  }
  const ownsCurrentState = input.__easyuseAnimaAutocompleteState === expectedState;
  if (activeState?.input === input && activeState.controller === expectedState.controller) {
    hidePopup();
  } else if (ownsCurrentState) {
    clearAutocompletePreview(input);
  }
  expectedState.binding?.dispose();
  expectedState.controller?.dispose?.();
  expectedState.binding = null;
  if (!ownsCurrentState) {
    return;
  }
  hookedAutocompleteInputs.delete(input);
  if (input.__easyuseAnimaAutocompleteDispose === expectedState.dispose) {
    delete input.__easyuseAnimaAutocompleteDispose;
  }
  delete input.__easyuseAnimaAutocompleteState;
  delete input.__easyuseAnimaAutocompleteHooked;
  input.__easyuseAnimaAutocomplete = false;
}

function pruneDisconnectedAutocompleteInputs(exceptInput = null) {
  for (const input of [...hookedAutocompleteInputs]) {
    if (input === exceptInput) {
      continue;
    }
    const state = input?.__easyuseAnimaAutocompleteState;
    if (!state || input?.isConnected === false) {
      disposeAutocompleteInput(input, state);
    }
  }
}

function syncAutocompleteInputFlags() {
  pruneDisconnectedAutocompleteInputs();
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
    let dataRequestsInvalidated = autocompleteData.syncSourceSettings(
      settings,
      { initialize: true },
    );
    const nextMaxResults = clampMaxResults(settings["autocomplete.limit"]);
    if (nextMaxResults !== maxResults) {
      maxResults = nextMaxResults;
      autocompleteData.clearResults();
      dataRequestsInvalidated = true;
    }
    const previousMode = autocompleteMode;
    setAutocompleteMode(settings["autocomplete.mode"]);
    if (autocompleteMode !== previousMode) {
      dataRequestsInvalidated = true;
    }
    const nextArtistPrefix = normalizeAutocompleteArtistPrefix(
      settings["autocomplete.artist_prefix"],
    );
    if (nextArtistPrefix !== autocompleteArtistPrefix) {
      autocompleteArtistPrefix = nextArtistPrefix;
      dataRequestsInvalidated = true;
    }
    setAutocompleteCommitKey(settings["autocomplete.commit_key"]);
    autocompleteCommitMode = normalizeAutocompleteCommitMode(
      settings["autocomplete.commit_mode"],
    );
    setAutocompleteAppendSeparator(settings["autocomplete.append_separator"]);
    setAutocompleteNoCommaAfterPeriod(settings["autocomplete.no_comma_after_period"]);
    const previousDetectNaturalSentences = autocompleteDetectNaturalSentences;
    setAutocompleteDetectNaturalSentences(settings["autocomplete.detect_natural_sentences"]);
    if (autocompleteDetectNaturalSentences !== previousDetectNaturalSentences) {
      dataRequestsInvalidated = true;
    }
    setAutocompletePreviewClosingBrackets(settings["autocomplete.preview_closing_brackets"]);
    setPromptStudioSelectionParenthesisWeight(
      settings["prompt_studio.selection_parenthesis_weight"],
    );
    if (setPromptStudioLoraAutocomplete(settings["prompt_studio.lora_autocomplete"])) {
      dataRequestsInvalidated = true;
    }
    const previousPreviewCompletion = autocompletePreviewCompletion;
    setAutocompletePreviewCompletion(settings["autocomplete.preview_completion"]);
    if (autocompletePreviewCompletion !== previousPreviewCompletion) {
      dataRequestsInvalidated = true;
    }
    if (dataRequestsInvalidated) {
      invalidateAutocompleteDataRequests();
    }
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
      box-sizing: border-box;
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

function hidePopup(options = {}) {
  const input = activeState?.input;
  if (!options.preserveController) {
    input?.__easyuseAnimaAutocompleteState?.controller?.invalidate();
  }
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

function invalidateAutocompleteDataRequests() {
  pruneDisconnectedAutocompleteInputs();
  const states = [];
  let focusedState = null;
  for (const input of [...hookedAutocompleteInputs]) {
    const state = input?.__easyuseAnimaAutocompleteState;
    if (!state) {
      hookedAutocompleteInputs.delete(input);
      continue;
    }
    states.push(state);
    if (document.activeElement === input) {
      focusedState = state;
    }
  }
  invalidateAutocompleteControllerStates(states, activeState);
  hidePopup({ preserveController: true });
  if (autocompleteEnabledForState(focusedState)) {
    focusedState.controller.scheduleUpdate();
  }
}

function refreshActiveAutocomplete(positionOnly = false) {
  pruneDisconnectedAutocompleteInputs();
  if (!activeState?.input || document.activeElement !== activeState.input || !autocompleteEnabledForState(activeState)) {
    hidePopup();
    return;
  }
  if (positionOnly) {
    activeState.reposition?.();
  } else {
    activeState.refresh?.();
  }
}

function scheduleActiveRefresh({ positionOnly = false } = {}) {
  activeRefreshNeedsUpdate ||= !positionOnly;
  if (activeRefreshFrame != null) {
    return;
  }
  activeRefreshFrame = requestAnimationFrame(() => {
    activeRefreshFrame = null;
    const refreshPositionOnly = !activeRefreshNeedsUpdate;
    activeRefreshNeedsUpdate = false;
    refreshActiveAutocomplete(refreshPositionOnly);
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
  for (const candidate of [widget?.inputEl, widget?.element]) {
    if (
      (candidate instanceof HTMLTextAreaElement || candidate instanceof HTMLInputElement)
      && candidate.isConnected !== false
    ) {
      return candidate;
    }
    const nested = candidate?.querySelector?.("textarea, input");
    if (
      (nested instanceof HTMLTextAreaElement || nested instanceof HTMLInputElement)
      && nested.isConnected !== false
    ) {
      return nested;
    }
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
      selectionStart: input?.selectionStart,
      selectionEnd: input?.selectionEnd,
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

function currentLoraToken(input) {
  const value = input?.value || "";
  return currentAutocompleteLoraToken(
    value,
    input?.selectionStart ?? value.length,
  );
}

function nodeSupportsLoraAutocomplete(node) {
  return [node?.type, node?.comfyClass, node?.constructor?.nodeData?.name]
    .filter(Boolean)
    .some((value) => LORA_AUTOCOMPLETE_NODE_TYPES.has(String(value)));
}

function loraAutocompleteEnabledForState(state) {
  return promptStudioLoraAutocomplete && nodeSupportsLoraAutocomplete(state?.node);
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
    commitMode: autocompleteCommitMode,
  });
}

function strictAutocompleteResults(context, token, _state, results) {
  if (!autocompletePreviewCompletion) {
    return results;
  }
  if (context.kind === "lora") {
    return results;
  }
  const rawQuery = context.kind === "wildcard"
    ? String(token?.query || "")
    : parseAutocompleteText(token?.query || "", autocompleteArtistPrefix).query;
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
  const {
    layoutWidth,
    layoutHeight,
    scaleX,
    scaleY,
  } = calculateCaretMirrorGeometry(rect, input.offsetWidth, input.offsetHeight);

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
  const fallbackLineHeight = (
    Number.isFinite(markerRect.left)
    && Number.isFinite(markerRect.top)
    && !markerRect.height
  )
    ? Number.parseFloat(getComputedStyle(input).lineHeight)
    : 0;
  return normalizeCaretClientRect(
    markerRect,
    rect,
    fallbackLineHeight,
  );
}

function positionPopup(input) {
  const menu = ensurePopup();
  const inputRect = input.getBoundingClientRect();
  const caretRect = caretClientRect(input);
  const fallbackLineHeight = caretRect.height
    ? 0
    : Number.parseFloat(getComputedStyle(input).lineHeight);
  const geometry = calculateAutocompletePopupGeometry(
    inputRect,
    caretRect,
    { width: window.innerWidth, height: window.innerHeight },
    fallbackLineHeight,
  );
  menu.style.left = `${geometry.left}px`;
  menu.style.top = `${geometry.top}px`;
  menu.style.width = `${geometry.width}px`;
  menu.style.maxHeight = `${geometry.maxHeight}px`;
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

function replaceInputRange(
  input,
  start,
  end,
  replacement,
  selectionStartOffset,
  selectionEndOffset = selectionStartOffset,
) {
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
  input.setSelectionRange(
    start + selectionStartOffset,
    start + selectionEndOffset,
  );
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
    return null;
  }
  event.preventDefault();
  event.stopPropagation();
  if (middlePanForwardCleanup) {
    return middlePanForwardCleanup;
  }
  const activeElement = document.activeElement;
  if (activeElement && "blur" in activeElement && typeof activeElement.blur === "function") {
    activeElement.blur();
  }
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
  const cleanup = (upEvent = null) => {
    if (middlePanForwardCleanup !== cleanup) {
      return;
    }
    const releaseEvent = upEvent || event;
    upEvent?.preventDefault?.();
    upEvent?.stopPropagation?.();
    dispatchAutocompleteCanvasPointerEvent("pointerup", releaseEvent, { button: 1, buttons: 0 });
    dispatchAutocompleteCanvasMouseEvent("mouseup", releaseEvent, { button: 1, buttons: 0 });
    middlePanForwardCleanup = null;
    document.removeEventListener("pointermove", move, true);
    document.removeEventListener("pointerup", stop, true);
    document.removeEventListener("pointercancel", stop, true);
    document.removeEventListener("mousemove", move, true);
    document.removeEventListener("mouseup", stop, true);
  };
  const stop = (upEvent) => {
    if (!upEvent.__easyuseAnimaForwarded) {
      cleanup(upEvent);
    }
  };
  middlePanForwardCleanup = cleanup;
  document.addEventListener("pointermove", move, true);
  document.addEventListener("pointerup", stop, true);
  document.addEventListener("pointercancel", stop, true);
  document.addEventListener("mousemove", move, true);
  document.addEventListener("mouseup", stop, true);
  return cleanup;
}

function commitSuggestion(state, entry, options = {}) {
  const promptToken = currentToken(state.input);
  const loraToken = entry?.kind === "lora" ? currentLoraToken(state.input) : null;
  const wildcardToken = entry?.kind === "wildcard" ? currentWildcardToken(state.input) : null;
  const token = loraToken || wildcardToken || promptToken;
  const insert = completionText(token, entry, state.forceArtistOnly);
  const plan = planAutocompleteInsertion(token, insert, {
    appendSeparator: autocompleteAppendSeparator,
    commitMode: autocompleteCommitMode,
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
    plan.selectionStartOffset ?? plan.caretOffset,
    plan.selectionEndOffset ?? plan.caretOffset,
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
  if (entry?.kind === "lora") {
    const name = String(entry.tag || "").replaceAll("\\", "/");
    return `<lora:${name}:1.0>`;
  }
  if (entry?.kind === "wildcard") {
    return `__${String(entry.tag || "").replace(/^__|__$/g, "")}__`;
  }
  const tag = promptTagText(entry?.tag);
  const query = parseAutocompleteText(token.query, autocompleteArtistPrefix);
  const artistOnly = forceArtistOnly || query.artistOnly;
  if (artistOnly) {
    return artistCompletionText(tag, autocompleteArtistPrefix);
  }
  return tag;
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
  if (entry?.kind === "lora") {
    return "lora";
  }
  if (entry?.kind === "wildcard") {
    return "wildcard";
  }
  const query = parseAutocompleteText(token?.query || "", autocompleteArtistPrefix);
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
  const prefix = autocompleteArtistPrefix;
  const typedWithoutPrefix = typedRaw.startsWith(prefix)
    ? typedRaw.slice(prefix.length)
    : typedRaw;
  const typedNormalized = normalizedCompletionPreviewText(typedWithoutPrefix);
  if (
    typedRaw.startsWith(prefix)
    && insert.startsWith(prefix)
    && typedNormalized
    && normalizedCompletionPreviewText(insert.slice(prefix.length)).startsWith(typedNormalized)
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
  const loraToken = entry?.kind === "lora" ? currentLoraToken(state.input) : null;
  const wildcardToken = entry?.kind === "wildcard" ? currentWildcardToken(state.input) : null;
  if (entry?.kind === "lora" && !loraToken) {
    return null;
  }
  if (entry?.kind === "wildcard" && !wildcardToken) {
    return null;
  }
  const token = loraToken || wildcardToken || currentToken(state.input);
  const insert = completionText(token, entry, state.forceArtistOnly);
  const plan = planAutocompleteInsertion(token, insert, {
    appendSeparator: autocompleteAppendSeparator,
    commitMode: autocompleteCommitMode,
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
    category: token.lora
      ? "lora"
      : token.wildcard
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

function insertBracketPair(state, event, plan) {
  if (!autocompletePreviewClosingBrackets || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) {
    return false;
  }
  const input = state?.input;
  if (!input || !plan) {
    return false;
  }
  event.preventDefault();
  replaceInputRange(
    input,
    plan.start,
    plan.end,
    plan.replacement,
    plan.selectionStartOffset,
    plan.selectionEndOffset,
  );
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
  const plan = planBracketInsertion(
    input.value,
    start,
    end,
    event.key,
    {
      selectionParenthesisWeight: promptStudioSelectionParenthesisWeight,
    },
  );
  if (plan) {
    return insertBracketPair(state, event, plan);
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

function isTextEditingShortcut(event) {
  if (!(event.ctrlKey || event.metaKey) || event.altKey) {
    return false;
  }
  return TEXT_EDITING_SHORTCUT_KEYS.has(String(event.key || "").toLocaleLowerCase());
}

function hookInput(input, options = {}) {
  if (!input) {
    return null;
  }
  pruneDisconnectedAutocompleteInputs(input);
  const existing = input.__easyuseAnimaAutocompleteState;
  if (existing?.owner === autocompleteInputOwner && typeof existing.dispose === "function") {
    input.__easyuseAnimaAutocompleteHooked = true;
    input.__easyuseAnimaAutocompleteDispose = existing.dispose;
    existing.node = options.node || existing.node || null;
    existing.widget = options.widget || existing.widget || null;
    existing.scope = autocompleteScope(options);
    existing.forceArtistOnly = !!options.forceArtistOnly;
    existing.onCommit = typeof options.onCommit === "function" ? options.onCommit : existing.onCommit;
    syncAutocompleteInputFlag(input, existing);
    return existing.dispose;
  }

  const state = {
    owner: autocompleteInputOwner,
    node: options.node || null,
    widget: options.widget || null,
    input,
    scope: autocompleteScope(options),
    forceArtistOnly: !!options.forceArtistOnly,
    onCommit: typeof options.onCommit === "function" ? options.onCommit : null,
    lastAutocompleteSignature: undefined,
    binding: null,
    dispose: null,
  };

  const markAutocompleteInactive = () => {
    state.lastAutocompleteSignature = "";
  };

  const controller = createAutocompleteInputController({
    requestFrame: (callback) => requestAnimationFrame(callback),
    cancelFrame: (handle) => cancelAnimationFrame(handle),
    setTimer: (callback, delay) => setTimeout(callback, delay),
    clearTimer: (handle) => clearTimeout(handle),
    onUpdate: async ({ isCurrent, request }) => {
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
      const loraToken = loraAutocompleteEnabledForState(state)
        ? currentLoraToken(input)
        : null;
      const wildcardToken = loraToken ? null : currentWildcardToken(input);
      const token = loraToken || wildcardToken || currentToken(input);
      if (!token?.active) {
        markAutocompleteInactive();
        hidePopup();
        return;
      }
      const context = loraToken
        ? loraAutocompleteQuery(loraToken)
        : wildcardToken
          ? wildcardAutocompleteQuery(wildcardToken)
          : autocompleteQuery(token, state.forceArtistOnly, autocompleteArtistPrefix);
      if (!["wildcard", "lora"].includes(context.kind) && context.query.length < MIN_QUERY_LENGTH) {
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
      const results = await request(
        signature,
        () => context.kind === "lora"
          ? autocompleteData.searchLoras(context.query)
          : context.kind === "wildcard"
            ? autocompleteData.searchWildcards(context.query)
            : autocompleteData.search(context.query, context.category),
      );
      if (
        isCurrent()
        && document.activeElement === input
        && autocompleteEnabledForState(state)
        && !shouldSuppressAutocomplete(input)
      ) {
        renderResults(state, strictAutocompleteResults(context, token, state, results), signature);
      }
    },
    onError: () => {
      if (document.activeElement === input && (!activeState || activeState.input === input)) {
        hidePopup();
      }
    },
  });
  state.controller = controller;
  state.refresh = controller.updateNow;
  state.reposition = () => positionPopup(input);
  state.binding = createAutocompleteInputBinding({
    input,
    state,
    owner: autocompleteInputOwner,
    registry: hookedAutocompleteInputs,
    controller,
    onBeforeDispose: (ownedInput, ownedState, ownsCurrentState) => {
      if (activeState?.input === ownedInput && activeState.controller === ownedState.controller) {
        hidePopup({ preserveController: true });
        return;
      }
      if (ownsCurrentState) {
        clearAutocompletePreview(ownedInput);
      }
    },
    getActiveState: () => activeState,
    hidePopup,
    isTextEditingShortcut,
    handleBracketPreviewKeydown,
    forwardMiddlePan: forwardMiddlePanFromAutocompleteInput,
    setActive,
    commitSuggestion,
    getCommitKey: () => autocompleteCommitKey,
    setTimer: (callback, delay) => setTimeout(callback, delay),
    clearTimer: (handle) => clearTimeout(handle),
  });
  syncAutocompleteInputFlag(input, state);
  return state.dispose;
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
  if (Array.isArray(graph?.nodes)) {
    return graph.nodes.filter(Boolean);
  }
  if (Array.isArray(graph?._nodes)) {
    return graph._nodes.filter(Boolean);
  }
  return Object.values(graph?._nodes_by_id || {}).filter(Boolean);
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
  const rootElement = /** @type {HTMLElement | SVGElement | null} */ (root);
  const id = root?.getAttribute?.("data-node-id")
    || rootElement?.dataset?.nodeId
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

function autocompleteDomInputOwner(input) {
  const ancestryNode = nodeFromDomElement(input);
  if (ancestryNode) {
    const widget = widgetForDomInput(ancestryNode, input);
    if (widget) {
      return { node: ancestryNode, widget };
    }
  }
  for (const node of autocompleteGraphNodes()) {
    if (node === ancestryNode) {
      continue;
    }
    const widget = widgetForDomInput(node, input);
    if (widget) {
      return { node, widget };
    }
  }
  return ancestryNode ? { node: ancestryNode, widget: null } : null;
}

function hookFocusedDomInput(input) {
  if (!isAutocompleteDomInput(input) || popup?.contains(input)) {
    return;
  }
  const owner = autocompleteDomInputOwner(input);
  if (!owner) {
    return;
  }
  const { node, widget } = owner;
  const nodeData = node?.constructor?.nodeData || null;
  const targets = nodeData ? targetWidgets(nodeData) : null;
  if (nodeData && (!targets || (!hasExplicitTargets(nodeData) && shouldSkipNode(node, nodeData)))) {
    return;
  }
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

function handleAutocompleteScroll(event) {
  if (popup?.contains(event.target)) {
    return;
  }
  scheduleActiveRefresh({ positionOnly: true });
}

function handleAutocompleteWheel(event) {
  if (popup?.contains(event.target)) {
    return;
  }
  scheduleActiveRefresh({ positionOnly: true });
}

function hookNode(node, nodeData, attempt = 0) {
  if (!autocompleteEntryLifecycle?.isActive()) {
    return;
  }
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
    autocompleteEntryLifecycle.schedule(() => hookNode(node, nodeData, attempt + 1), 80);
  }
}

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

function handleAutocompleteSettingsUpdated(event) {
  const detail = event?.detail || {};
  let dataRequestsInvalidated = false;
  if ("autocomplete.mode" in detail) {
    const previousMode = autocompleteMode;
    setAutocompleteMode(detail["autocomplete.mode"]);
    if (autocompleteMode !== previousMode) {
      dataRequestsInvalidated = true;
    }
  }
  if ("autocomplete.commit_key" in detail) {
    setAutocompleteCommitKey(detail["autocomplete.commit_key"]);
  }
  if ("autocomplete.commit_mode" in detail) {
    autocompleteCommitMode = normalizeAutocompleteCommitMode(
      detail["autocomplete.commit_mode"],
    );
  }
  if ("autocomplete.artist_prefix" in detail) {
    const nextArtistPrefix = normalizeAutocompleteArtistPrefix(
      detail["autocomplete.artist_prefix"],
    );
    if (nextArtistPrefix !== autocompleteArtistPrefix) {
      autocompleteArtistPrefix = nextArtistPrefix;
      dataRequestsInvalidated = true;
    }
  }
  if ("autocomplete.append_separator" in detail) {
    setAutocompleteAppendSeparator(detail["autocomplete.append_separator"]);
  }
  if ("autocomplete.no_comma_after_period" in detail) {
    setAutocompleteNoCommaAfterPeriod(detail["autocomplete.no_comma_after_period"]);
  }
  if ("autocomplete.detect_natural_sentences" in detail) {
    const previousDetectNaturalSentences = autocompleteDetectNaturalSentences;
    setAutocompleteDetectNaturalSentences(detail["autocomplete.detect_natural_sentences"]);
    if (autocompleteDetectNaturalSentences !== previousDetectNaturalSentences) {
      dataRequestsInvalidated = true;
    }
  }
  if ("autocomplete.preview_closing_brackets" in detail) {
    setAutocompletePreviewClosingBrackets(detail["autocomplete.preview_closing_brackets"]);
  }
  if ("prompt_studio.selection_parenthesis_weight" in detail) {
    setPromptStudioSelectionParenthesisWeight(
      detail["prompt_studio.selection_parenthesis_weight"],
    );
  }
  if ("prompt_studio.lora_autocomplete" in detail) {
    if (setPromptStudioLoraAutocomplete(detail["prompt_studio.lora_autocomplete"])) {
      dataRequestsInvalidated = true;
    }
  }
  if ("autocomplete.preview_completion" in detail) {
    const previousPreviewCompletion = autocompletePreviewCompletion;
    setAutocompletePreviewCompletion(detail["autocomplete.preview_completion"]);
    if (autocompletePreviewCompletion !== previousPreviewCompletion) {
      dataRequestsInvalidated = true;
    }
  }
  if ("autocomplete.limit" in detail) {
    const nextMaxResults = clampMaxResults(detail["autocomplete.limit"]);
    if (nextMaxResults !== maxResults) {
      maxResults = nextMaxResults;
      autocompleteData.clearResults();
      dataRequestsInvalidated = true;
    }
  }
  if (autocompleteData.syncSourceSettings(detail)) {
    dataRequestsInvalidated = true;
  }
  if (dataRequestsInvalidated) {
    invalidateAutocompleteDataRequests();
  } else {
    scheduleActiveRefresh();
  }
}

function disposeAutocompleteEntryInputs() {
  for (const input of [...hookedAutocompleteInputs]) {
    disposeAutocompleteInput(input);
  }
  hookedAutocompleteInputs.clear();
}

function disposeAutocompleteEntryUi() {
  if (activeRefreshFrame != null) {
    cancelAnimationFrame(activeRefreshFrame);
    activeRefreshFrame = null;
  }
  activeRefreshNeedsUpdate = false;
  middlePanForwardCleanup?.();
  middlePanForwardCleanup = null;
  hidePopup();
  popup?.remove?.();
  popup = null;
  document.getElementById("easyuse-anima-autocomplete-style")?.remove?.();
}

autocompleteEntryLifecycle = createAutocompleteEntryLifecycle({
  hostWindow: window,
  hostDocument: document,
  hookInput,
  hookFocusedInput: hookFocusedDomInput,
  entryTooltip: autocompleteEntryTooltip,
  handleScroll: handleAutocompleteScroll,
  handleWheel: handleAutocompleteWheel,
  handleOutsidePointer: handleOutsideAutocompletePointer,
  handleSelectionChange: scheduleActiveRefresh,
  handleResize: scheduleActiveRefresh,
  handleSettingsUpdated: handleAutocompleteSettingsUpdated,
  hookNode: (node, nodeData) => hookNode(node, nodeData),
  disposeInputs: disposeAutocompleteEntryInputs,
  disposeUi: disposeAutocompleteEntryUi,
});

app.registerExtension({
  name: "easyuse-anima.autocomplete",
  async init() {
    autocompleteEntryLifecycle.install();
  },
  async setup() {
    autocompleteEntryLifecycle.install();
    if (!autocompleteEntryLifecycle.isActive()) {
      return;
    }
    await refreshAutocompleteSettings();
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!targetWidgets(nodeData)) {
      return;
    }

    autocompleteEntryLifecycle.installNodeTypeHooks(nodeType, nodeData);
  },
});
