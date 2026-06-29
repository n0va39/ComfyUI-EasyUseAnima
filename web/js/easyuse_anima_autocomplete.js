import { app } from "../../../scripts/app.js";
import {
  normalizePromptTagText,
  promptCompletionTagText,
} from "./easyuse_anima_prompt_rules.js";
import { easyuseAnimaText } from "./easyuse_anima_i18n.js";

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
  EasyUseAnimaLoraPreset: new Set([
    "style_prompt",
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
const SENTENCE_PERIODS = new Set([".", "。", "．", "｡"]);
const TEXT_EDITING_SHORTCUT_KEYS = new Set(["a", "c", "v", "x", "z", "y"]);
const AUTOCOMPLETE_TEXT = {
  en: {
    "category.tag": "tag",
    "category.quality": "quality",
    "category.artist": "artist",
    "category.character": "character",
    "category.copyright": "copyright",
    "category.general": "general",
    "category.meta": "meta",
  },
  ko: {
    "category.tag": "태그",
    "category.quality": "품질",
    "category.artist": "작가",
    "category.character": "캐릭터",
    "category.copyright": "작품",
    "category.general": "일반",
    "category.meta": "메타",
  },
};
const MIN_QUERY_LENGTH = 1;
const cache = new Map();

let maxResults = DEFAULT_MAX_RESULTS;
let autocompleteMode = DEFAULT_AUTOCOMPLETE_MODE;
let autocompleteCommitKey = DEFAULT_AUTOCOMPLETE_COMMIT_KEY;
let autocompleteAppendSeparator = false;
let autocompleteNoCommaAfterPeriod = true;
let autocompleteDetectNaturalSentences = true;
let popup = null;
let activeState = null;
let activeRefreshFrame = null;
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

function setAutocompleteMode(value) {
  const nextMode = normalizeAutocompleteMode(value);
  if (nextMode === autocompleteMode) {
    return;
  }
  autocompleteMode = nextMode;
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

async function refreshAutocompleteSettings() {
  try {
    const response = await fetch("/easyuse_anima/settings");
    if (!response.ok) {
      return;
    }
    const settings = await response.json();
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
  if (popup) {
    popup.classList.add("hidden");
    popup.replaceChildren();
  }
  activeState = null;
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
  return String(inputSpec || "");
}

function inputOptions(inputSpec) {
  if (Array.isArray(inputSpec) && typeof inputSpec[1] === "object" && inputSpec[1] !== null) {
    return inputSpec[1];
  }
  return {};
}

function allInputSpecs(nodeData) {
  const inputs = nodeData?.input || {};
  const specs = [];
  for (const group of ["required", "optional"]) {
    const values = inputs[group] || {};
    for (const [name, spec] of Object.entries(values)) {
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
  if (!type.split(",").map((item) => item.trim()).includes("STRING")) {
    return false;
  }
  if (isExcludedInput(inputSpec)) {
    return false;
  }
  if (options.multiline === true) {
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
  const input = widget?.inputEl;
  if (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement) {
    return input;
  }
  return null;
}

function isEscaped(value, index) {
  let count = 0;
  for (let cursor = index - 1; cursor >= 0 && value[cursor] === "\\"; cursor -= 1) {
    count += 1;
  }
  return count % 2 === 1;
}

function isSentencePeriod(value, index) {
  if (!SENTENCE_PERIODS.has(value[index]) || isEscaped(value, index)) {
    return false;
  }
  return !(/\d/.test(value[index - 1] || "") && /\d/.test(value[index + 1] || ""));
}

function naturalSentenceStart(value, segmentStart, caret) {
  if (!autocompleteDetectNaturalSentences) {
    return segmentStart;
  }
  for (let index = caret - 1; index >= segmentStart; index -= 1) {
    if (!isSentencePeriod(value, index)) {
      continue;
    }
    let start = index + 1;
    while (start < caret && /[ \t]/.test(value[start])) {
      start += 1;
    }
    return start < caret ? start : segmentStart;
  }
  return segmentStart;
}

function naturalSentenceEnd(value, caret, segmentEnd) {
  for (let index = caret; index < segmentEnd; index += 1) {
    if (isSentencePeriod(value, index)) {
      return index;
    }
  }
  return segmentEnd;
}

function currentToken(input) {
  const value = input.value || "";
  const caret = input.selectionStart ?? value.length;
  let start = caret;
  while (start > 0 && value[start - 1] !== "," && value[start - 1] !== "\n") {
    start -= 1;
  }
  let end = caret;
  while (end < value.length && value[end] !== "," && value[end] !== "\n") {
    end += 1;
  }
  const naturalStart = naturalSentenceStart(value, start, caret);
  const sentenceDelimited = naturalStart > start;
  if (sentenceDelimited) {
    start = naturalStart;
    end = naturalSentenceEnd(value, caret, end);
  }
  const raw = value.slice(start, caret);
  const segment = value.slice(start, end);
  return {
    value,
    start,
    end,
    caret,
    segment,
    sentenceDelimited,
    query: raw.trim(),
  };
}

function autocompleteQuery(token, forceArtistOnly = false) {
  const raw = String(token.query || "");
  const parsed = parseAutocompleteText(raw);
  const artistOnly = forceArtistOnly || parsed.artistOnly;
  const query = artistOnly ? parsed.query : raw.trim();
  const category = artistOnly ? "artist" : "";
  return { query, artistOnly, category };
}

function autocompleteStateSignature(token, context, state) {
  return JSON.stringify({
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
  });
}

function parseAutocompleteText(value) {
  let query = String(value || "").trim();
  if (query.startsWith("(")) {
    query = query.slice(1).trimStart();
  }
  const artistOnly = query.startsWith("@");
  if (artistOnly) {
    query = query.slice(1).trimStart();
    query = query.replace(/:\s*[-+]?\d*(?:\.\d*)?\)?\s*$/, "");
    query = query.replace(/\)+\s*$/, "");
  }
  return { query, artistOnly };
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
  const response = await fetch(
    `/easyuse_anima/autocomplete?q=${encodeURIComponent(query)}&limit=${maxResults}${categoryParam}`,
  );
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  const results = Array.isArray(data.results) ? data.results : [];
  cache.set(key, results);
  return results;
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
  [...ensurePopup().children].forEach((child, childIndex) => {
    child.classList.toggle("active", childIndex === activeState.index);
  });
}

function endsWithSentencePeriod(value) {
  const text = String(value || "").replace(/[ \t]+$/g, "");
  return text.length > 0 && isSentencePeriod(text, text.length - 1);
}

function startsWithSentencePeriod(value) {
  const text = String(value || "").replace(/^[ \t]+/g, "");
  return text.length > 0 && isSentencePeriod(text, 0);
}

function insertPrefixForBefore(before) {
  if (!before || before.endsWith("\n")) {
    return "";
  }
  if (before.endsWith(",")) {
    return " ";
  }
  if (/[ \t]$/.test(before)) {
    return "";
  }
  if (autocompleteNoCommaAfterPeriod && endsWithSentencePeriod(before)) {
    return " ";
  }
  return ", ";
}

function insertSuffixForAfter(after, appendSeparator = false) {
  if (!after) {
    return appendSeparator ? ", " : "";
  }
  if (after.startsWith("\n") || after.startsWith(",")) {
    return "";
  }
  if (autocompleteNoCommaAfterPeriod && startsWithSentencePeriod(after)) {
    return "";
  }
  return ", ";
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

function commitSuggestion(state, entry) {
  const token = currentToken(state.input);
  const before = token.value.slice(0, token.start);
  const after = token.value.slice(token.end);
  const insert = completionText(token, entry, state.forceArtistOnly);
  const prefix = insertPrefixForBefore(before);
  const suffix = insertSuffixForAfter(after, autocompleteAppendSeparator);
  const replacement = `${prefix}${insert}${suffix}`;
  const caretOffset = prefix.length + insert.length + (!after ? suffix.length : 0);
  replaceInputRange(state.input, token.start, token.end, replacement, caretOffset);
  if (state.widget) {
    state.widget.value = state.input.value;
    state.widget.callback?.(state.input.value);
  }
  state.onCommit?.(state.input.value);
  hidePopup();
}

function displayTagText(value) {
  return normalizePromptTagText(value);
}

function promptTagText(value) {
  return promptCompletionTagText(value);
}

function completionText(token, entry, forceArtistOnly = false) {
  const tag = promptTagText(entry?.tag);
  const segment = String(token.segment || "").trim();
  const query = parseAutocompleteText(token.query);
  const weighted = /^\(\s*@?[\s\S]*(:\s*[-+]?\d+(?:\.\d+)?)\s*\)\s*$/.exec(segment);
  const artistOnly = forceArtistOnly || query.artistOnly;
  if (artistOnly && weighted) {
    return `(@${tag}${weighted[1]})`;
  }
  if (artistOnly) {
    return `@${tag}`;
  }
  return tag;
}

function renderResults(state, results, signature = "") {
  const menu = ensurePopup();
  const previousIndex = activeState?.input === state.input && activeState?.signature === signature
    ? activeState.index
    : 0;
  menu.replaceChildren();
  activeState = {
    ...state,
    results,
    signature,
    index: results.length ? clamp(previousIndex, 0, results.length - 1) : 0,
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
    const count = Number(entry.count || 0).toLocaleString();
    meta.textContent = `${autocompleteCategoryLabel(entry.category)} · ${count}`;
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
      commitSuggestion(activeState, entry);
    });
    menu.append(item);
  }

  positionPopup(state.input);
  menu.classList.remove("hidden");
}

function isCaretInComment(value, caret) {
  const text = String(value ?? "");
  const safeCaret = Math.max(0, Math.min(Number(caret) || 0, text.length));
  const lineStart = text.lastIndexOf("\n", safeCaret - 1) + 1;
  return /^[ \t]*#/.test(text.slice(lineStart, safeCaret));
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
  if (input.__easyuseAnimaAutocomplete) {
    const existing = input.__easyuseAnimaAutocompleteState;
    if (existing) {
      existing.node = options.node || existing.node || null;
      existing.widget = options.widget || existing.widget || null;
      existing.scope = autocompleteScope(options);
      existing.forceArtistOnly = !!options.forceArtistOnly;
      existing.onCommit = typeof options.onCommit === "function" ? options.onCommit : existing.onCommit;
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
  };

  const updateNow = async () => {
    if (composing || document.activeElement !== input || !autocompleteEnabledForState(state)) {
      if (activeState?.input === input) {
        hidePopup();
      }
      return;
    }
    if (isCaretInComment(input.value || "", input.selectionStart ?? 0)) {
      hidePopup();
      return;
    }
    const token = currentToken(input);
    const context = autocompleteQuery(token, state.forceArtistOnly);
    if (context.query.length < MIN_QUERY_LENGTH) {
      hidePopup();
      return;
    }
    const signature = autocompleteStateSignature(token, context, state);
    if (activeState?.input === input && activeState.signature === signature) {
      positionPopup(input);
      return;
    }
    const seq = ++updateSeq;
    try {
      const results = await search(context.query, context.category);
      if (document.activeElement === input && seq === updateSeq) {
        renderResults(state, results, signature);
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
      commitSuggestion(activeState, activeState.results[activeState.index]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      hidePopup();
    }
  });

  input.__easyuseAnimaAutocomplete = true;
  input.__easyuseAnimaAutocompleteState = state;
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

function installExternalInputHook() {
  window.easyuseAnimaHookAutocompleteInput = (input, options = {}) => {
    hookInput(input, options);
  };
  const pending = window.__easyuseAnimaPendingAutocompleteInputs || [];
  window.__easyuseAnimaPendingAutocompleteInputs = [];
  for (const item of pending) {
    hookInput(item?.input, item?.options || {});
  }
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
  if ("autocomplete.limit" in detail) {
    maxResults = clampMaxResults(detail["autocomplete.limit"]);
    cache.clear();
  }
  if ("autocomplete.source" in detail) {
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
