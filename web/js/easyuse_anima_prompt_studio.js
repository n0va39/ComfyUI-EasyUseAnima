import { app } from "../../../scripts/app.js";
import { easyuseAnimaClassifyPrompt, easyuseAnimaGetSettings } from "./easyuse_anima_api.js";
import { easyuseAnimaText, easyuseAnimaWatchLocale } from "./easyuse_anima_i18n.js";
import { normalizePromptTagText } from "./easyuse_anima_prompt_rules.js";
import {
  FIELD_NAMES,
  EXTEND_FIELD_NAMES,
  EXTEND_VISIBLE_SLOTS_PROPERTY,
  EXTEND_ACTIVE_SLOTS_WIDGET,
  EXTEND_SLOT_GROUPS,
  EXTEND_DEFAULT_VISIBLE_FIELDS,
  PROMPT_STUDIO_TEXT,
  FIELD_HEIGHTS,
  EXTEND_FIELD_HEIGHTS,
  SECTION_STYLES,
  LEGEND_ITEMS,
  LEGEND_TOP_GAP,
  LEGEND_ROW_HEIGHT,
  LEGEND_COLUMNS,
  STUDIO_WIDGET_VERTICAL_GAP,
  PROMPT_STUDIO_FONT_SIZE_DEFAULT,
  PROMPT_STUDIO_FONT_SIZE_MIN,
  PROMPT_STUDIO_FONT_SIZE_MAX,
  PROMPT_STUDIO_FONT_FAMILY,
  WEIGHT_NUMBER_RE,
  WEIGHTED_TOKEN_RE,
  WEIGHT_NUMBER_COLOR,
  WILDCARD_HIGHLIGHT_RE,
  ARTIST_MIX_GROUP_HIGHLIGHT_RE,
  INLINE_SPACE_RE,
  HIGHLIGHT_TEXT_METRIC_PROPERTIES,
  AUTOCOMPLETE_TOOLTIP_SECTIONS,
  ADVANCED_NATIVE_CONTROL_EVENTS,
  ADVANCED_CONTROL_WIDGETS,
  ADVANCED_WILDCARD_MODES,
  ADVANCED_WILDCARD_SEED_CONTROLS,
  ADVANCED_WILDCARD_DEFAULT_MODE,
  ARTIST_MIX_MODES,
  ADVANCED_RESOLUTION_BUCKETS,
  CUSTOM_ADVANCED_RESOLUTION_BUCKET,
  NAIA_ADVANCED_RESOLUTION_BUCKET,
  DEFAULT_ADVANCED_RESOLUTION_BUCKET,
  DEFAULT_ADVANCED_RESOLUTION_SIZE,
  ADVANCED_WIDGET_INDEX,
  ADVANCED_INTERNAL_WIDGET_NAMES,
  ADVANCED_FIELDS_PROPERTY,
  ADVANCED_FIELD_LABELS,
} from "./prompt_studio/constants.js";
import {
  debounce,
  isHexColor,
  hexToRgba,
  parseColorSettings,
  normalizePromptStudioFontSize,
  normalizePromptStudioFontFamily,
  escapeHtml,
  escapeAttr,
  advancedResolutionLabel,
  snapResolution32,
  clampAdvancedNumber,
} from "./prompt_studio/utils.js";
import {
  advancedDefaultFields,
  advancedFieldInputName,
  advancedResolutionOptions,
  normalizeAdvancedField,
  normalizeAdvancedResolutionBucket,
  normalizeAdvancedResolutionSize,
  normalizeAdvancedWidgetQueueValue,
  normalizeArtistMixMode,
} from "./prompt_studio/schema.js";
import {
  findHiddenWidget,
  getAdvancedEditorElement,
  getAdvancedFields,
  setAdvancedEditorElement,
  setAdvancedFields,
  setHiddenWidget,
} from "./prompt_studio/state.js";
import {
  closeAdvancedHelpPopovers,
  openAdvancedHelpPopover,
  protectAdvancedNativeControl,
  stopAdvancedControlEvent,
  updateAdvancedSummary,
} from "./prompt_studio/dom.js";
import {
  advancedPaneFields,
  hasAdvancedNaia,
  hasPositiveTrigger,
  moveAdvancedFieldInPane,
} from "./prompt_studio/fields.js";
import {
  isAdvancedNode,
  isExtendNode,
  installAdvancedSaveSync,
  registerPromptStudioNodeHooks,
  syncAdvancedNodes,
} from "./prompt_studio/node_hooks.js";
import {
  ensureAdvancedStyle,
} from "./prompt_studio/style.js";
import {
  advancedEditorMinimumHeight,
  advancedEditorWidgetHeight,
  advancedMinimumNodeHeight,
  advancedTextareaContentHeight,
  advancedTextareaCurrentHeight,
  advancedTextareaMinimumHeight,
  clampAdvancedNodeToMinimumHeight,
  updateAdvancedEditorWidth,
} from "./prompt_studio/layout.js";
import {
  advancedFieldTextareaPlaceholder,
  advancedFieldTextareaTitle,
  captureAdvancedTextareaManualResize,
  rememberAdvancedTextareaResizeStart,
  syncAdvancedTextareaLinkedInputValue,
} from "./prompt_studio/textarea.js";
import {
  canAdvancedEditorScrollWheelDelta,
  guardAdvancedEditorNativeControlEvent,
  isMiddlePanExcludedTarget,
  shouldKeepAdvancedWheelEvent,
} from "./prompt_studio/wheel.js";
import {
  advancedFieldDisplayText,
  advancedFieldIndexLabel,
  advancedFieldInputLinked,
  advancedFieldsBackup,
  captureAdvancedConfigure,
  collectAdvancedEditorFields,
  ensureAdvancedWidgetValue,
  mergeAdvancedFieldInputValues,
  pruneDisconnectedAdvancedFieldInputValues,
  syncAdvancedFieldInputs,
  syncAdvancedFieldsBackup,
} from "./prompt_studio/serialization.js";

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

const PROMPT_STUDIO_SETTINGS = {
  typoIndicator: true,
  weightSyntaxUnderline: false,
  commentItalic: true,
  fontOverride: false,
  fontFamily: "",
  fontSize: PROMPT_STUDIO_FONT_SIZE_DEFAULT,
  trainedTagTooltip: true,
  naiaGeneralAboveAutoToggle: false,
};
let middlePanForwardActive = false;
let promptStudioTagTooltip = null;
let promptStudioTagTooltipMoveFrame = 0;
let promptStudioTagTooltipPendingMove = null;
let promptStudioTagTooltipLastTarget = null;

function findWidget(node, name) {
  return findHiddenWidget(node, name)
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

function repairAdvancedInternalWidgetValues(node) {
  let changed = false;
  for (const name of Object.keys(ADVANCED_WIDGET_INDEX)) {
    if (name === "advanced_fields") {
      continue;
    }
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    const next = normalizeAdvancedWidgetQueueValue(name, widget.value);
    if (widget.value !== next) {
      widget.value = next;
      const input = findInputEl(widget);
      if (input) {
        input.value = String(next ?? "");
      }
      changed = true;
    }
  }
  if (changed) {
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
  }
  return changed;
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

function ensureTrainedTagTooltipStyle() {
  if (document.getElementById("easyuse-anima-trained-tag-tooltip-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-trained-tag-tooltip-style";
  style.textContent = `
    .easyuse-anima-trained-tag-tooltip {
      position: fixed;
      z-index: 99999;
      max-width: min(560px, calc(100vw - 16px));
      border: 1px solid rgba(128, 128, 128, 0.45);
      border-radius: 7px;
      background: var(--comfy-menu-bg, #202124);
      color: var(--input-text, #ddd);
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35);
      font: 12px/1.35 sans-serif;
      padding: 8px 10px;
      pointer-events: none;
    }
    .easyuse-anima-trained-tag-tooltip.hidden {
      display: none;
    }
    .easyuse-anima-trained-tag-tooltip .easyuse-anima-autocomplete-tag {
      font-weight: 700;
    }
    .easyuse-anima-trained-tag-tooltip .easyuse-anima-autocomplete-meta {
      margin-left: 6px;
      opacity: 0.62;
      font-size: 11px;
    }
    .easyuse-anima-trained-tag-tooltip .easyuse-anima-autocomplete-desc {
      margin-top: 2px;
      opacity: 0.78;
      white-space: normal;
    }
  `;
  document.head.append(style);
}

function ensureTrainedTagTooltip() {
  ensureTrainedTagTooltipStyle();
  if (promptStudioTagTooltip?.isConnected) {
    return promptStudioTagTooltip;
  }
  promptStudioTagTooltip = document.createElement("div");
  promptStudioTagTooltip.className = "easyuse-anima-trained-tag-tooltip hidden";
  document.body.append(promptStudioTagTooltip);
  return promptStudioTagTooltip;
}

function hideTrainedTagTooltip() {
  promptStudioTagTooltipPendingMove = null;
  promptStudioTagTooltipLastTarget = null;
  if (promptStudioTagTooltip) {
    promptStudioTagTooltip.classList.add("hidden");
  }
}

function visibleAutocompletePopupExists() {
  return !!document.querySelector(".easyuse-anima-autocomplete:not(.hidden)");
}

function trainedTagTooltipTargetAt(overlay, clientX, clientY) {
  if (!overlay?.isConnected) {
    return null;
  }
  const targets = overlay.querySelectorAll("[data-easyuse-anima-trained-tag-tooltip='true']");
  for (const target of targets) {
    for (const rect of target.getClientRects()) {
      if (
        clientX >= rect.left - 1
        && clientX <= rect.right + 1
        && clientY >= rect.top - 1
        && clientY <= rect.bottom + 1
      ) {
        return target;
      }
    }
  }
  return null;
}

function positionTrainedTagTooltip(tooltip, event) {
  const margin = 8;
  const offset = 14;
  const rect = tooltip.getBoundingClientRect();
  const left = Math.min(
    Math.max(margin, event.clientX + offset),
    Math.max(margin, window.innerWidth - rect.width - margin),
  );
  const below = event.clientY + offset;
  const top = below + rect.height + margin <= window.innerHeight
    ? below
    : Math.max(margin, event.clientY - rect.height - offset);
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function showTrainedTagTooltip(target, event) {
  const tooltip = ensureTrainedTagTooltip();
  if (
    promptStudioTagTooltipLastTarget === target
    && !tooltip.classList.contains("hidden")
  ) {
    positionTrainedTagTooltip(tooltip, event);
    return;
  }
  promptStudioTagTooltipLastTarget = target;
  const tag = target.dataset.easyuseAnimaTooltipTag || "";
  const meta = target.dataset.easyuseAnimaTooltipMeta || "";
  const description = target.dataset.easyuseAnimaTooltipDescription || "";
  tooltip.replaceChildren();

  const top = document.createElement("div");
  const tagEl = document.createElement("span");
  tagEl.className = "easyuse-anima-autocomplete-tag";
  tagEl.textContent = tag;
  top.append(tagEl);
  if (meta) {
    const metaEl = document.createElement("span");
    metaEl.className = "easyuse-anima-autocomplete-meta";
    metaEl.textContent = meta;
    top.append(metaEl);
  }
  tooltip.append(top);
  if (description) {
    const desc = document.createElement("div");
    desc.className = "easyuse-anima-autocomplete-desc";
    desc.textContent = description;
    tooltip.append(desc);
  }

  tooltip.classList.remove("hidden");
  positionTrainedTagTooltip(tooltip, event);
}

function updateTrainedTagTooltipMove(input, clientX, clientY) {
  if (visibleAutocompletePopupExists()) {
    hideTrainedTagTooltip();
    return;
  }
  const target = trainedTagTooltipTargetAt(input?.__easyuseAnimaHighlightOverlay, clientX, clientY);
  if (!target) {
    hideTrainedTagTooltip();
    return;
  }
  showTrainedTagTooltip(target, { clientX, clientY });
}

function handleTrainedTagTooltipMove(input, event) {
  if (!PROMPT_STUDIO_SETTINGS.trainedTagTooltip) {
    hideTrainedTagTooltip();
    return;
  }
  promptStudioTagTooltipPendingMove = {
    input,
    clientX: event.clientX,
    clientY: event.clientY,
  };
  if (promptStudioTagTooltipMoveFrame) {
    return;
  }
  promptStudioTagTooltipMoveFrame = requestAnimationFrame(() => {
    promptStudioTagTooltipMoveFrame = 0;
    const move = promptStudioTagTooltipPendingMove;
    promptStudioTagTooltipPendingMove = null;
    if (!move) {
      return;
    }
    updateTrainedTagTooltipMove(move.input, move.clientX, move.clientY);
  });
}

function installTrainedTagTooltipListeners(input) {
  if (input.__easyuseAnimaTrainedTagTooltipInstalled) {
    return;
  }
  input.addEventListener("mousemove", (event) => handleTrainedTagTooltipMove(input, event));
  input.addEventListener("mouseleave", hideTrainedTagTooltip);
  input.addEventListener("scroll", hideTrainedTagTooltip);
  input.addEventListener("input", hideTrainedTagTooltip);
  input.addEventListener("blur", hideTrainedTagTooltip);
  input.__easyuseAnimaTrainedTagTooltipInstalled = true;
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







function applyPromptStudioTextStyle(input) {
  if (!(input instanceof HTMLElement)) {
    return;
  }
  const nextFamily = (PROMPT_STUDIO_SETTINGS.fontOverride && PROMPT_STUDIO_SETTINGS.fontFamily)
    ? PROMPT_STUDIO_SETTINGS.fontFamily
    : PROMPT_STUDIO_FONT_FAMILY;
  if (input.style.fontFamily !== nextFamily) {
    input.style.fontFamily = nextFamily;
  }
  if (!PROMPT_STUDIO_SETTINGS.fontOverride) {
    if (input.dataset.easyuseAnimaPromptTextOverride === "true") {
      input.style.fontSize = "";
      delete input.dataset.easyuseAnimaPromptTextOverride;
    }
    return;
  }
  const nextSize = `${PROMPT_STUDIO_SETTINGS.fontSize}px`;
  if (input.style.fontSize !== nextSize) {
    input.style.fontSize = nextSize;
  }
  input.dataset.easyuseAnimaPromptTextOverride = "true";
}

function applyPromptStudioSettings(settings) {
  PROMPT_STUDIO_SETTINGS.typoIndicator = settings?.["prompt_studio.typo_indicator"] !== "false";
  PROMPT_STUDIO_SETTINGS.weightSyntaxUnderline = settings?.["prompt_studio.weight_syntax_underline"] === "true";
  PROMPT_STUDIO_SETTINGS.commentItalic = settings?.["prompt_studio.comment_italic"] !== "false";
  PROMPT_STUDIO_SETTINGS.trainedTagTooltip = settings?.["prompt_studio.trained_tag_tooltip"] !== "false";
  if (!PROMPT_STUDIO_SETTINGS.trainedTagTooltip) {
    hideTrainedTagTooltip();
  }
  PROMPT_STUDIO_SETTINGS.fontOverride = settings?.["prompt_studio.font_override"] === "true";
  PROMPT_STUDIO_SETTINGS.fontFamily = normalizePromptStudioFontFamily(settings?.["prompt_studio.font_family"]);
  PROMPT_STUDIO_SETTINGS.fontSize = normalizePromptStudioFontSize(settings?.["prompt_studio.font_size"]);
  if (PROMPT_STUDIO_SETTINGS.fontOverride) {
    document.documentElement?.style?.setProperty(
      "--easyuse-anima-prompt-studio-font-size",
      `${PROMPT_STUDIO_SETTINGS.fontSize}px`,
    );
    document.documentElement?.style?.setProperty(
      "--easyuse-anima-prompt-studio-font-family",
      PROMPT_STUDIO_SETTINGS.fontFamily || PROMPT_STUDIO_FONT_FAMILY,
    );
  } else {
    document.documentElement?.style?.removeProperty("--easyuse-anima-prompt-studio-font-size");
    document.documentElement?.style?.removeProperty("--easyuse-anima-prompt-studio-font-family");
  }
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
    const settings = await easyuseAnimaGetSettings({ fallback: null });
    if (!settings) {
      return;
    }
    applyPromptStudioSettings(settings);
    refreshAllPromptHighlights(true);
    app.graph?.setDirtyCanvas(true, true);
  } catch {
    // Keep built-in defaults if the settings endpoint is not available yet.
  }
}

async function classifyPrompt(text) {
  return easyuseAnimaClassifyPrompt(text);
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
  let artistGroupDepth = 0;
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
    if (char === "[" && value[index + 1] === "[") {
      artistGroupDepth += 1;
      index += 1;
      continue;
    }
    if (char === "]" && value[index + 1] === "]" && artistGroupDepth > 0) {
      artistGroupDepth -= 1;
      index += 1;
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
    if ((char === "," || char === "\n") && depth === 0 && artistGroupDepth === 0) {
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

function trainedTagTooltipEntry(text, token) {
  if (!PROMPT_STUDIO_SETTINGS.trainedTagTooltip) {
    return null;
  }
  const section = String(token?.section || "");
  if (!AUTOCOMPLETE_TOOLTIP_SECTIONS.has(section) || !token?.learned) {
    return null;
  }
  const tag = String(token?.base || text || token?.token || "").trim();
  if (!tag) {
    return null;
  }
  return {
    tag,
    category: section,
    count: Number(token?.count || 0),
    description: String(token?.description || ""),
  };
}

function trainedTagTooltipData(text, token) {
  const entry = trainedTagTooltipEntry(text, token);
  if (!entry) {
    return null;
  }
  const tooltip = typeof window !== "undefined" && typeof window.easyuseAnimaAutocompleteEntryTooltip === "function"
    ? window.easyuseAnimaAutocompleteEntryTooltip(entry)
    : {
      tag: entry.tag,
      meta: `${sectionLabel(entry.category)} · ${Number(entry.count || 0).toLocaleString()}`,
      description: entry.description,
    };
  return {
    tag: String(tooltip?.tag || entry.tag),
    meta: String(tooltip?.meta || ""),
    description: String(tooltip?.description || ""),
  };
}

function trainedTagTooltipAttrs(text, token) {
  const tooltip = trainedTagTooltipData(text, token);
  if (!tooltip) {
    return "";
  }
  const title = [tooltip.tag, tooltip.meta, tooltip.description].filter(Boolean).join("\n");
  return [
    'data-easyuse-anima-trained-tag-tooltip="true"',
    `data-easyuse-anima-tooltip-tag="${escapeAttr(tooltip.tag)}"`,
    `data-easyuse-anima-tooltip-meta="${escapeAttr(tooltip.meta)}"`,
    `data-easyuse-anima-tooltip-description="${escapeAttr(tooltip.description)}"`,
    `aria-label="${escapeAttr(title)}"`,
  ].join(" ");
}

function tokenSpanHtml(text, token) {
  const tooltip = trainedTagTooltipData(text, token);
  const title = tooltip
    ? [tooltip.tag, tooltip.meta, tooltip.description].filter(Boolean).join("\n")
    : tokenTitle(token);
  const attrs = trainedTagTooltipAttrs(text, token);
  return `<span style="${tokenStyle(token)}" title="${escapeAttr(title)}"${attrs ? ` ${attrs}` : ""}>`
    + escapeHtml(text)
    + "</span>";
}

function weightSyntaxDecoration() {
  return PROMPT_STUDIO_SETTINGS.weightSyntaxUnderline
    ? [
      "text-decoration-line: underline",
      "text-decoration-style: solid",
      "text-decoration-color: rgba(148, 163, 184, 0.95)",
      "text-underline-offset: 3px",
      "text-decoration-skip-ink: none",
    ].join("; ")
    : "";
}

function wrapWeightSyntaxHtml(html) {
  const decoration = weightSyntaxDecoration();
  return decoration
    ? `<span style="${decoration}">${html}</span>`
    : html;
}

function weightSyntaxSpanHtml(text, style = "") {
  const rules = [style].filter(Boolean).join("; ");
  return rules
    ? `<span style="${rules}">${escapeHtml(text)}</span>`
    : escapeHtml(text);
}

function syntaxErrorSpanHtml(text, title = sectionLabel("syntax")) {
  return `<span style="${tokenStyle({ section: "syntax" })}" title="${escapeHtml(title)}">`
    + escapeHtml(text)
    + "</span>";
}

function weightedParenSyntaxHtml(text) {
  const match = /^(\()([\s\S]*?)(:)(\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+))(\s*\))$/.exec(String(text ?? ""));
  if (!match) {
    return syntaxErrorSpanHtml(text);
  }
  const [, open, body, colon, weight, close] = match;
  return wrapWeightSyntaxHtml(
    weightSyntaxSpanHtml(open)
    + escapeHtml(body)
    + weightSyntaxSpanHtml(colon)
    + weightSyntaxSpanHtml(weight, `color: ${WEIGHT_NUMBER_COLOR}`)
    + weightSyntaxSpanHtml(close),
  );
}

function basicSyntaxHtml(text) {
  const value = String(text ?? "");
  const html = [];
  const pattern = /\([^()\n]*:[^()\n]*\)/g;
  let cursor = 0;
  let match = null;
  while ((match = pattern.exec(value))) {
    html.push(escapeHtml(value.slice(cursor, match.index)));
    html.push(weightedParenSyntaxHtml(match[0]));
    cursor = match.index + match[0].length;
  }
  html.push(escapeHtml(value.slice(cursor)));
  return html.join("");
}

function wildcardSyntaxSpanHtml(text) {
  return `<span style="${tokenStyle({ section: "wildcard" })}" title="${escapeHtml(sectionLabel("wildcard"))}">`
    + escapeHtml(text)
    + "</span>";
}

function translationSyntaxSpanHtml(text) {
  return `<span style="${tokenStyle({ section: "translation" })}" title="${escapeHtml(sectionLabel("translation"))}">`
    + escapeHtml(text)
    + "</span>";
}

function findTopLevelWeightColon(value) {
  let depth = 0;
  let colon = -1;
  let escaped = false;
  const text = String(value ?? "");
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
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
    if (char === ":" && depth === 0) {
      colon = index;
    }
  }
  return colon;
}

function artistMixGroupParts(text) {
  const match = /^(\[\[)([\s\S]*?)(\]\])$/.exec(String(text ?? ""));
  if (!match) {
    return null;
  }
  const body = match[2];
  const colon = findTopLevelWeightColon(body);
  if (colon < 0) {
    return { open: match[1], body, weight: "", close: match[3], syntaxError: false };
  }
  const weight = body.slice(colon + 1).trim();
  if (!weight || !WEIGHT_NUMBER_RE.test(weight)) {
    return { open: match[1], body, weight: "", close: match[3], syntaxError: true };
  }
  return {
    open: match[1],
    body: body.slice(0, colon).replace(/[ \t\r\n,]+$/g, ""),
    weight,
    close: match[3],
    syntaxError: false,
  };
}

function artistMixGroupShellHtml(parts, bodyHtml) {
  if (!parts || parts.syntaxError) {
    return syntaxErrorSpanHtml(`${parts?.open || ""}${parts?.body || ""}${parts?.close || ""}`);
  }
  const openHtml = weightSyntaxSpanHtml(parts.open);
  const closeHtml = weightSyntaxSpanHtml(parts.close);
  const weightHtml = parts.weight
    ? weightSyntaxSpanHtml(":")
      + weightSyntaxSpanHtml(parts.weight, `color: ${WEIGHT_NUMBER_COLOR}`)
    : "";
  const html = `${openHtml}${bodyHtml}${weightHtml}${closeHtml}`;
  return wrapWeightSyntaxHtml(html);
}

function artistMixGroupSyntaxHtml(text) {
  const parts = artistMixGroupParts(text);
  if (!parts) {
    return basicSyntaxHtml(text);
  }
  if (parts.syntaxError) {
    return syntaxErrorSpanHtml(text);
  }
  return artistMixGroupShellHtml(parts, syntaxHtml(parts.body));
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

function findPromptTranslationRange(value, offset) {
  for (let start = offset; start < value.length; start += 1) {
    if (value[start] !== "%" || value[start + 1] !== "{" || isEscapedAt(value, start)) {
      continue;
    }
    for (let cursor = start + 2; cursor < value.length; cursor += 1) {
      if (value[cursor] === "}" && !isEscapedAt(value, cursor)) {
        return { start, end: cursor + 1 };
      }
    }
    return null;
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

function findArtistMixGroupSyntaxRange(value, offset) {
  ARTIST_MIX_GROUP_HIGHLIGHT_RE.lastIndex = offset;
  const match = ARTIST_MIX_GROUP_HIGHLIGHT_RE.exec(value);
  return match
    ? { start: match.index, end: match.index + match[0].length }
    : null;
}

function firstSyntaxRange(value, offset) {
  const ranges = [
    findWildcardSyntaxRange(value, offset),
    findPromptTranslationRange(value, offset),
    findArtistMixGroupSyntaxRange(value, offset),
  ].filter(Boolean);
  if (!ranges.length) {
    return null;
  }
  return ranges.reduce((first, range) => (range.start < first.start ? range : first), ranges[0]);
}

function hasHighlightSyntax(text) {
  return !!firstSyntaxRange(String(text ?? ""), 0);
}

function syntaxHtml(text) {
  const value = String(text ?? "");
  let cursor = 0;
  const html = [];
  while (cursor < value.length) {
    const range = firstSyntaxRange(value, cursor);
    if (!range) {
      break;
    }
    html.push(basicSyntaxHtml(value.slice(cursor, range.start)));
    const snippet = value.slice(range.start, range.end);
    if (snippet.startsWith("[[")) {
      html.push(artistMixGroupSyntaxHtml(snippet));
    } else if (snippet.startsWith("%{")) {
      html.push(translationSyntaxSpanHtml(snippet));
    } else {
      html.push(wildcardSyntaxSpanHtml(snippet));
    }
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
  const html = [
    syntaxHtml(text.slice(0, match.start)),
    tokenSpanHtml(text.slice(match.start, match.end), token),
    syntaxHtml(text.slice(match.end)),
  ].join("");
  return WEIGHTED_TOKEN_RE.test(String(text ?? "").trim())
    ? wrapWeightSyntaxHtml(html)
    : html;
}

function weightedTokenSegmentRange(body, cursor, match) {
  const open = body.lastIndexOf("(", Math.max(cursor, match.start));
  if (open < cursor) {
    return null;
  }
  const suffix = /^\s*:\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*\)/.exec(body.slice(match.end));
  if (!suffix) {
    return null;
  }
  return { start: open, end: match.end + suffix[0].length };
}

function findTokenMatch(body, offset, token) {
  let start = offset;
  while (
    start < body.length
    && (
      /\s/.test(body[start])
      || body[start] === ","
      || body[start] === "("
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
    const weightedRange = token?.weighted ? weightedTokenSegmentRange(body, cursor, match) : null;
    if (weightedRange) {
      html.push(syntaxHtml(body.slice(cursor, weightedRange.start)));
      html.push(weightedTokenSpanHtml(body.slice(weightedRange.start, weightedRange.end), token));
      cursor = weightedRange.end;
    } else {
      html.push(syntaxHtml(body.slice(cursor, match.start)));
      html.push(tokenSpanHtml(body.slice(match.start, match.end), token));
      cursor = match.end;
    }
    consumed.add(token);
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

    const artistGroupParts = artistMixGroupParts(body);
    if (artistGroupParts) {
      const rendered = artistGroupParts.syntaxError
        ? null
        : renderSequentialBody(artistGroupParts.body, tokens, tokenIndex, consumed);
      html.push(escapeHtml(leading));
      if (artistGroupParts.syntaxError) {
        html.push(syntaxErrorSpanHtml(body));
      } else {
        if (rendered) {
          tokenIndex = rendered.nextIndex;
        }
        html.push(artistMixGroupShellHtml(
          artistGroupParts,
          rendered ? rendered.html : syntaxHtml(artistGroupParts.body),
        ));
      }
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

function autocompletePreviewSpanHtml(text, preview, opacity = 0.95) {
  const color = String(preview?.color || "rgba(203, 213, 225, 0.86)");
  return `<span style="font: inherit; line-height: inherit; letter-spacing: inherit; vertical-align: baseline; color: ${escapeHtml(color)}; opacity: ${opacity}">`
    + escapeHtml(text)
    + "</span>";
}

function highlightOverlayPreviewHtml(value, tokens, preview) {
  if (!preview || String(preview.sourceValue || "") !== String(value || "")) {
    return null;
  }
  const text = String(preview.value || "");
  const candidateStart = Math.max(0, Math.min(Number(preview.candidateStart ?? preview.ghostStart) || 0, text.length));
  const candidateEnd = Math.max(candidateStart, Math.min(Number(preview.candidateEnd ?? preview.ghostEnd) || 0, text.length));
  const ghostStart = Math.max(0, Math.min(Number(preview.ghostStart) || 0, text.length));
  const ghostEnd = Math.max(ghostStart, Math.min(Number(preview.ghostEnd) || 0, text.length));
  if (!text || candidateEnd <= candidateStart || ghostEnd <= ghostStart) {
    return null;
  }
  const safeGhostStart = Math.max(candidateStart, Math.min(ghostStart, candidateEnd));
  const safeGhostEnd = Math.max(safeGhostStart, Math.min(ghostEnd, candidateEnd));
  const html = [
    renderHighlightedText(text.slice(0, candidateStart), tokens || []),
    autocompletePreviewSpanHtml(text.slice(candidateStart, safeGhostStart), preview, 0.95),
    autocompletePreviewSpanHtml(text.slice(safeGhostStart, safeGhostEnd), preview, 0.52),
    autocompletePreviewSpanHtml(text.slice(safeGhostEnd, candidateEnd), preview, 0.95),
    renderHighlightedText(text.slice(candidateEnd), tokens || []),
  ].join("");
  return text.endsWith("\n") ? `${html} ` : html;
}

function highlightOverlayHtml(value, tokens, placeholder = "", input = null) {
  const text = String(value || "");
  if (!text) {
    return `<span style="opacity: 0.45">${escapeHtml(placeholder)}</span>`;
  }
  const previewHtml = highlightOverlayPreviewHtml(text, tokens, input?.__easyuseAnimaAutocompletePreview);
  if (previewHtml != null) {
    return previewHtml;
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
  installTrainedTagTooltipListeners(input);
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
  applyPromptStudioTextStyle(input);
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
  overlay.innerHTML = highlightOverlayHtml(value, tokens, input.placeholder || "", input);
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
  applyPromptStudioTextStyle(textarea);
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
  overlay.innerHTML = highlightOverlayHtml(value, tokens || state.tokens || [], textarea.placeholder || "", textarea);
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

function refreshAdvancedHighlights(node, { classify = true, forceCopyMetrics = false } = {}) {
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return;
  }
  const fields = getAdvancedFields(node) || parseAdvancedFields(node);
  const byId = new Map(fields.map((field) => [String(field.id), field]));
  const textareas = Array.from(editor.querySelectorAll("textarea[data-easyuse-anima-advanced-field-id]"));

  const updates = [];

  // Read DOM Sizes
  for (const textarea of textareas) {
    const field = byId.get(String(textarea.dataset.easyuseAnimaAdvancedFieldId || ""));
    if (!field) {
      continue;
    }
    applyPromptStudioTextStyle(textarea);
    const overlay = ensureHighlightOverlay(textarea);
    if (!overlay) {
      continue;
    }
    if (forceCopyMetrics) {
      copyInputTextMetrics(textarea, overlay);
    }

    const { left, top, width, height } = overlayBounds(textarea);
    const padding = overlayScrollbarPadding(textarea);
    const scrollTop = textarea.scrollTop;
    const scrollLeft = textarea.scrollLeft;

    const state = advancedHighlightState(node, field);
    const value = String(textarea.value || "");
    const htmlContent = highlightOverlayHtml(value, state.tokens || [], textarea.placeholder || "", textarea);

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
  if (!getAdvancedEditorElement(node)) {
    return;
  }
  const previousOptions = node.__easyuseAnimaAdvancedHighlightOptions || {};
  node.__easyuseAnimaAdvancedHighlightOptions = {
    classify: options.classify !== false,
    forceCopyMetrics: previousOptions.forceCopyMetrics === true || options.forceCopyMetrics === true,
  };
  if (node.__easyuseAnimaAdvancedHighlightScheduled) {
    return;
  }
  node.__easyuseAnimaAdvancedHighlightScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaAdvancedHighlightScheduled = false;
    const refreshOptions = node.__easyuseAnimaAdvancedHighlightOptions || {};
    refreshAdvancedHighlights(node, refreshOptions);
    requestAnimationFrame(() => refreshAdvancedHighlights(node, { classify: false, forceCopyMetrics: refreshOptions.forceCopyMetrics === true }));
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
    applyPromptStudioTextStyle(input);
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

function refreshAllPromptHighlights(forceCopyMetrics = false) {
  for (const node of app.graph?._nodes || []) {
    if (isAdvancedNode(node)) {
      scheduleAdvancedHighlights(node, { forceCopyMetrics });
      continue;
    }
    for (const name of studioFieldNames(node)) {
      const widget = findWidget(node, name);
      if (widget) {
        updateHighlight(node, widget, widget.__easyuseAnimaTokens || [], forceCopyMetrics);
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

  applyPromptStudioTextStyle(input);
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

function advancedWidget(node) {
  return findWidget(node, "advanced_fields");
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
  setHiddenWidget(node, name, widget);
  node.setDirtyCanvas?.(true, true);
}

function hideAdvancedControlWidgets(node) {
  for (const name of ADVANCED_INTERNAL_WIDGET_NAMES) {
    hideAdvancedInternalWidget(node, name);
  }
  repairAdvancedInternalWidgetValues(node);
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

function parseAdvancedFields(node) {
  const widget = advancedWidget(node);
  ensureAdvancedWidgetValue(node, widget);
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

function writeAdvancedFields(node, fields, { render = false, syncInputs = true } = {}) {
  const widget = advancedWidget(node);
  if (!widget) {
    return;
  }
  widget.value = JSON.stringify(fields.map((field, index) => normalizeAdvancedField(field, index)));
  syncAdvancedFieldsBackup(node, widget.value);
  setAdvancedFields(node, fields);
  if (syncInputs) {
    syncAdvancedFieldInputs(node, fields, { graph: app.graph, fieldLabel: advancedFieldLabel });
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
  widget.value = normalizeAdvancedWidgetQueueValue(name, value);
  const input = findInputEl(widget);
  if (input) {
    input.value = String(widget.value ?? "");
  }
  widget.callback?.(widget.value);
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  return true;
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
  const modGuidanceGroup = createAdvancedModGuidanceGroup(node);
  const artistMixGroup = createAdvancedArtistMixGroup(node);
  if (modGuidanceGroup) {
    bar.append(modGuidanceGroup);
  }
  if (artistMixGroup) {
    bar.append(artistMixGroup);
  }
  return bar;
}

function openAdvancedSettingsPopup(node, titleKey, subtitleKey, createBody, onClose = null) {
  ensureAdvancedStyle();
  const backdrop = document.createElement("div");
  backdrop.className = "easyuse-anima-advanced-popup-backdrop";
  const dialog = document.createElement("div");
  dialog.className = "easyuse-anima-advanced-popup";
  dialog.addEventListener("pointerdown", stopAdvancedControlEvent);
  dialog.addEventListener("mousedown", stopAdvancedControlEvent);
  dialog.addEventListener("click", stopAdvancedControlEvent);
  dialog.addEventListener("keydown", stopAdvancedControlEvent);

  const header = document.createElement("header");
  const titleBox = document.createElement("div");
  const heading = document.createElement("h2");
  heading.textContent = psText(titleKey);
  const desc = document.createElement("p");
  desc.textContent = psText(subtitleKey);
  titleBox.append(heading, desc);
  const close = document.createElement("button");
  close.type = "button";
  close.className = "easyuse-anima-advanced-popup-close";
  close.textContent = psText("advanced.close");
  header.append(titleBox, close);

  const body = document.createElement("div");
  body.className = "easyuse-anima-advanced-popup-body";
  const content = createBody?.();
  if (content instanceof DocumentFragment) {
    body.append(content);
  } else if (content instanceof HTMLElement) {
    body.append(...Array.from(content.childNodes));
  }
  dialog.append(header, body);
  backdrop.append(dialog);

  const closePopup = () => {
    closeAdvancedHelpPopovers();
    backdrop.remove();
    onClose?.();
    renderAdvancedEditor(node);
  };
  close.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    closePopup();
  });
  backdrop.addEventListener("pointerdown", (event) => {
    if (event.target === backdrop) {
      closePopup();
    }
  });
  document.body.append(backdrop);
  return backdrop;
}

function createAdvancedControlGroup(node, groupId, labelKey, titleKey, summary, active, createBody) {
  const group = document.createElement("div");
  group.className = "easyuse-anima-advanced-controlgroup";
  group.classList.toggle("is-active", !!active);
  group.addEventListener("pointerdown", stopAdvancedControlEvent);
  group.addEventListener("mousedown", stopAdvancedControlEvent);
  group.addEventListener("click", stopAdvancedControlEvent);

  const header = document.createElement("button");
  header.type = "button";
  header.className = "easyuse-anima-advanced-controlgroup-header";
  header.title = psText(titleKey);
  header.textContent = psText(labelKey) || psText("advanced.settingsButton");

  const summaryEl = document.createElement("span");
  summaryEl.className = "easyuse-anima-advanced-controlgroup-summary";
  summaryEl.dataset.easyuseAnimaControlSummary = groupId;
  summaryEl.textContent = summary;

  header.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const subtitleKey = groupId === "mod_guidance"
      ? "advanced.modGuidanceSubtitle"
      : "advanced.artistMixSubtitle";
    openAdvancedSettingsPopup(node, labelKey, subtitleKey, createBody);
  });
  group.append(header, summaryEl);
  return group;
}

function createAdvancedToggleControl(node, control) {
  const widget = findWidget(node, control.name);
  if (!widget) {
    return null;
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
    const next = !widget.value;
    setAdvancedControlValue(node, control.name, next);
    button.classList.toggle("is-on", next);
    updateAdvancedSummary(node, "mod_guidance", advancedModGuidanceSummary(node));
  });
  return button;
}

function advancedModGuidanceSummary(node) {
  const positiveOn = !!findWidget(node, "use_anima_mod_guidance")?.value;
  const negativeOn = !!findWidget(node, "use_negative_anima_mod_guidance")?.value;
  return [positiveOn ? "positive" : "", negativeOn ? "negative" : ""]
    .filter(Boolean)
    .join(" + ") || psText("advanced.off");
}

function createAdvancedModGuidanceGroup(node) {
  const controls = ADVANCED_CONTROL_WIDGETS.filter(
    (control) => control.showInControlBar !== false && findWidget(node, control.name),
  );
  if (!controls.length) {
    return null;
  }
  const positiveOn = !!findWidget(node, "use_anima_mod_guidance")?.value;
  const negativeOn = !!findWidget(node, "use_negative_anima_mod_guidance")?.value;
  const summary = advancedModGuidanceSummary(node);
  return createAdvancedControlGroup(
    node,
    "mod_guidance",
    "advanced.modGuidanceGroup",
    "advanced.modGuidanceGroupTitle",
    summary,
    positiveOn || negativeOn,
    () => {
      const body = document.createElement("div");
      for (const control of controls) {
        const button = createAdvancedToggleControl(node, control);
        if (button) {
          body.append(button);
        }
      }
      return body;
    },
  );
}

function artistMixModeTitle(mode) {
  return psText(`advanced.artistMixMode.${normalizeArtistMixMode(mode)}Title`);
}


function createAdvancedControlRow(labelKey, controlEl, titleKey = null) {
  const row = document.createElement("div");
  row.className = "easyuse-anima-advanced-controlgroup-row";
  const label = document.createElement("span");
  label.className = "easyuse-anima-advanced-controlgroup-label";
  label.textContent = psText(labelKey);
  const title = titleKey ? psText(titleKey) : "";
  if (title) {
    row.title = title;
    label.title = title;
    controlEl.title = title;
  }
  row.append(label, controlEl);
  if (title) {
    const help = document.createElement("button");
    help.type = "button";
    help.className = "easyuse-anima-advanced-help";
    help.textContent = "i";
    help.title = title;
    help.setAttribute("aria-label", `${psText(labelKey)} help`);
    help.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openAdvancedHelpPopover(help, help.title || title);
    });
    row.append(help);
  }
  return row;
}

function createArtistMixNumberInput(node, name, labelKey, titleKey, min, max, step, fallback) {
  const widget = findWidget(node, name);
  if (!widget) {
    return null;
  }
  const input = document.createElement("input");
  protectAdvancedNativeControl(input);
  input.type = "number";
  input.min = String(min);
  input.max = String(max);
  input.step = String(step);
  input.value = String(clampAdvancedNumber(widget.value, fallback, min, max));
  input.setAttribute("aria-label", psText(labelKey));
  const syncValue = () => {
    const next = clampAdvancedNumber(input.value, fallback, min, max);
    input.value = String(next);
    setAdvancedWidgetValue(node, name, next);
  };
  input.addEventListener("change", syncValue);
  input.addEventListener("blur", syncValue);
  input.addEventListener("keydown", stopAdvancedControlEvent);
  return createAdvancedControlRow(labelKey, input, titleKey);
}

function createArtistMixBooleanInput(node, name, labelKey, titleKey, fallback) {
  const widget = findWidget(node, name);
  if (!widget) {
    return null;
  }
  const button = document.createElement("button");
  protectAdvancedNativeControl(button);
  button.type = "button";
  button.className = "easyuse-anima-advanced-toggle";
  const initial = widget.value ?? fallback;
  button.classList.toggle("is-on", !!initial);
  button.textContent = initial ? psText("advanced.on") : psText("advanced.off");
  button.setAttribute("aria-label", psText(labelKey));
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const next = !(widget.value ?? fallback);
    setAdvancedControlValue(node, name, next);
    button.classList.toggle("is-on", next);
    button.textContent = next ? psText("advanced.on") : psText("advanced.off");
  });
  return createAdvancedControlRow(labelKey, button, titleKey);
}

function createAdvancedArtistMixGroup(node) {
  const modeWidget = findWidget(node, "artist_mix_mode");
  if (!modeWidget) {
    return null;
  }
  const modeValue = normalizeArtistMixMode(modeWidget.value);
  const active = modeValue !== "off";
  return createAdvancedControlGroup(
    node,
    "artist_mix",
    "advanced.artistMix",
    "advanced.artistMixTitle",
    modeValue,
    active,
    () => {
      const body = document.createElement("div");
      const modeSelect = document.createElement("select");
      protectAdvancedNativeControl(modeSelect);
      modeSelect.setAttribute("aria-label", psText("advanced.artistMixMode"));
      modeSelect.title = artistMixModeTitle(modeValue);
      for (const mode of ARTIST_MIX_MODES) {
        const option = document.createElement("option");
        option.value = mode;
        option.textContent = mode;
        option.selected = mode === modeValue;
        option.title = artistMixModeTitle(mode);
        modeSelect.append(option);
      }
      const modeRow = createAdvancedControlRow("advanced.artistMixMode", modeSelect, `advanced.artistMixMode.${modeValue}Title`);
      modeSelect.addEventListener("change", () => {
        const nextMode = normalizeArtistMixMode(modeSelect.value);
        setAdvancedWidgetValue(node, "artist_mix_mode", nextMode);
        const nextTitle = artistMixModeTitle(nextMode);
        modeSelect.title = nextTitle;
        modeRow.title = nextTitle;
        modeRow.querySelector(".easyuse-anima-advanced-controlgroup-label")?.setAttribute("title", nextTitle);
        modeRow.querySelector(".easyuse-anima-advanced-help")?.setAttribute("title", nextTitle);
        updateAdvancedSummary(node, "artist_mix", nextMode);
      });
      body.append(modeRow);
      const syntaxNote = document.createElement("div");
      syntaxNote.className = "easyuse-anima-advanced-popup-note";
      syntaxNote.textContent = psText("advanced.artistMixSyntaxTitle");
      body.append(syntaxNote);
      const startRow = createArtistMixNumberInput(
        node,
        "artist_mix_start_percent",
        "advanced.artistMixStart",
        "advanced.artistMixStartTitle",
        0,
        1,
        0.01,
        0.5,
      );
      const strengthRow = createArtistMixNumberInput(
        node,
        "artist_mix_strength_scale",
        "advanced.artistMixStrength",
        "advanced.artistMixStrengthTitle",
        0,
        5,
        0.01,
        1,
      );
      const styleGainRow = createArtistMixNumberInput(
        node,
        "artist_mix_style_gain",
        "advanced.artistMixStyleGain",
        "advanced.artistMixStyleGainTitle",
        0,
        3,
        0.01,
        1.35,
      );
      const rmsScaleCapRow = createArtistMixNumberInput(
        node,
        "artist_mix_rms_scale_cap",
        "advanced.artistMixRmsCap",
        "advanced.artistMixRmsCapTitle",
        1,
        5,
        0.01,
        2,
      );
      const exactTopKRow = createArtistMixNumberInput(
        node,
        "artist_mix_exact_top_k",
        "advanced.artistMixTopK",
        "advanced.artistMixTopKTitle",
        0,
        64,
        1,
        4,
      );
      const clusterCountRow = createArtistMixNumberInput(
        node,
        "artist_mix_cluster_count",
        "advanced.artistMixClusters",
        "advanced.artistMixClustersTitle",
        1,
        32,
        1,
        4,
      );
      const dominantRow = createArtistMixBooleanInput(
        node,
        "artist_mix_dominant_isolation",
        "advanced.artistMixDominant",
        "advanced.artistMixDominantTitle",
        true,
      );
      const dominantThresholdRow = createArtistMixNumberInput(
        node,
        "artist_mix_dominant_threshold",
        "advanced.artistMixDominantThreshold",
        "advanced.artistMixDominantThresholdTitle",
        0,
        1,
        0.01,
        0.25,
      );
      if (startRow) {
        body.append(startRow);
      }
      if (strengthRow) {
        body.append(strengthRow);
      }
      for (const row of [styleGainRow, rmsScaleCapRow, exactTopKRow, clusterCountRow, dominantRow, dominantThresholdRow]) {
        if (row) {
          body.append(row);
        }
      }
      return body;
    },
  );
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

function advancedWildcardSummary(node) {
  const modeWidget = findWidget(node, "wildcard_mode");
  const seedWidget = findWidget(node, "wildcard_seed");
  const controlWidget = findWidget(node, "wildcard_seed_after_generate");
  const modeValue = normalizeAdvancedWildcardMode(modeWidget?.value);
  const controlValue = modeValue === "순차"
    ? "increment"
    : normalizeAdvancedSeedControl(controlWidget?.value);
  return `${modeValue} · seed ${Math.max(0, Math.trunc(Number(seedWidget?.value) || 0))} · ${controlValue}`;
}

function createAdvancedSummaryButtonRow(className, buttonLabelKey, titleKey, summaryId, summaryText, onClick) {
  const row = document.createElement("div");
  row.className = className;
  row.title = psText(titleKey);
  const button = document.createElement("button");
  button.type = "button";
  button.className = "easyuse-anima-advanced-popup-button";
  button.textContent = psText(buttonLabelKey);
  button.title = psText(titleKey);
  const summary = document.createElement("span");
  summary.className = "easyuse-anima-advanced-inline-summary";
  summary.dataset.easyuseAnimaControlSummary = summaryId;
  summary.textContent = summaryText;
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    onClick?.();
  });
  row.append(button, summary);
  return row;
}

function createAdvancedWildcardSettingsBody(node) {
  const modeWidget = findWidget(node, "wildcard_mode");
  const seedWidget = findWidget(node, "wildcard_seed");
  const controlWidget = findWidget(node, "wildcard_seed_after_generate");
  if (!modeWidget || !seedWidget || !controlWidget) {
    return document.createDocumentFragment();
  }

  const body = document.createElement("div");

  const modeSelect = document.createElement("select");
  protectAdvancedNativeControl(modeSelect);
  modeSelect.setAttribute("aria-label", psText("advanced.wildcard"));
  modeSelect.title = psText("advanced.wildcardModeTitle");
  const modeValue = normalizeAdvancedWildcardMode(modeWidget.value);
  for (const mode of ADVANCED_WILDCARD_MODES) {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = mode;
    option.selected = mode === modeValue;
    modeSelect.append(option);
  }

  const seedInput = document.createElement("input");
  protectAdvancedNativeControl(seedInput);
  seedInput.type = "number";
  seedInput.min = "0";
  seedInput.step = "1";
  seedInput.value = String(seedWidget.value ?? "0");
  seedInput.setAttribute("aria-label", psText("advanced.wildcardSeed"));
  seedInput.title = psText("advanced.wildcardSeedTitle");

  const controlSelect = document.createElement("select");
  protectAdvancedNativeControl(controlSelect);
  controlSelect.setAttribute("aria-label", psText("advanced.wildcardSeedControl"));
  controlSelect.title = psText("advanced.wildcardSeedControlTitle");
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

  const refreshSummary = () => updateAdvancedSummary(node, "wildcard", advancedWildcardSummary(node));
  const syncMode = () => {
    const nextMode = normalizeAdvancedWildcardMode(modeSelect.value);
    setAdvancedWidgetValue(node, "wildcard_mode", nextMode);
    if (nextMode === "순차") {
      setAdvancedWidgetValue(node, "wildcard_seed_after_generate", "increment");
      controlSelect.value = "increment";
    }
    controlSelect.disabled = nextMode === "순차";
    refreshSummary();
  };
  const syncSeed = () => {
    const seed = Math.max(0, Math.trunc(Number(seedInput.value) || 0));
    seedInput.value = String(seed);
    setAdvancedWidgetValue(node, "wildcard_seed", seed);
    refreshSummary();
  };
  const syncControl = () => {
    setAdvancedWidgetValue(node, "wildcard_seed_after_generate", normalizeAdvancedSeedControl(controlSelect.value));
    refreshSummary();
  };

  modeSelect.addEventListener("change", syncMode);
  seedInput.addEventListener("change", syncSeed);
  seedInput.addEventListener("blur", syncSeed);
  controlSelect.addEventListener("change", syncControl);

  body.append(
    createAdvancedControlRow("advanced.wildcard", modeSelect, "advanced.wildcardModeTitle"),
    createAdvancedControlRow("advanced.wildcardSeed", seedInput, "advanced.wildcardSeedTitle"),
    createAdvancedControlRow("advanced.wildcardSeedControl", controlSelect, "advanced.wildcardSeedControlTitle"),
  );
  return body;
}

function createAdvancedWildcardBar(node) {
  const modeWidget = findWidget(node, "wildcard_mode");
  const seedWidget = findWidget(node, "wildcard_seed");
  const controlWidget = findWidget(node, "wildcard_seed_after_generate");
  if (!modeWidget || !seedWidget || !controlWidget) {
    return document.createDocumentFragment();
  }
  return createAdvancedSummaryButtonRow(
    "easyuse-anima-advanced-wildcardbar",
    "advanced.wildcardSeed",
    "advanced.wildcardTitle",
    "wildcard",
    advancedWildcardSummary(node),
    () => openAdvancedSettingsPopup(
      node,
      "advanced.wildcardSeed",
      "advanced.wildcardTitle",
      () => createAdvancedWildcardSettingsBody(node),
    ),
  );
}

function advancedResolutionSummary(node) {
  const bucketWidget = findWidget(node, "resolution_bucket");
  const sizeWidget = findWidget(node, "resolution_size");
  const bucketValue = normalizeAdvancedResolutionBucket(bucketWidget?.value);
  const customResolution = advancedCustomResolution(node);
  const sizeValue = bucketValue === CUSTOM_ADVANCED_RESOLUTION_BUCKET || bucketValue === NAIA_ADVANCED_RESOLUTION_BUCKET
    ? advancedResolutionLabel(customResolution.width, customResolution.height)
    : normalizeAdvancedResolutionSize(bucketValue, sizeWidget?.value);
  return `${bucketValue} · ${sizeValue}`;
}

function createAdvancedResolutionSettingsBody(node) {
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

  const body = document.createElement("div");

  const bucketSelect = document.createElement("select");
  protectAdvancedNativeControl(bucketSelect);
  bucketSelect.setAttribute("aria-label", psText("advanced.resolutionBucket"));
  bucketSelect.title = psText("advanced.resolutionBucketTitle");
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
  const refreshSummary = () => updateAdvancedSummary(node, "resolution", advancedResolutionSummary(node));
  const renderPresetSelect = (bucket, selected) => {
    valueBox.innerHTML = "";
    const sizeSelect = document.createElement("select");
    protectAdvancedNativeControl(sizeSelect);
    sizeSelect.setAttribute("aria-label", psText("advanced.resolutionSize"));
    sizeSelect.title = psText("advanced.resolutionSizeTitle");
    for (const label of advancedResolutionOptions(bucket)) {
      const option = document.createElement("option");
      option.value = label;
      option.textContent = label;
      option.selected = label === selected;
      sizeSelect.append(option);
    }
    sizeSelect.addEventListener("change", () => {
      setAdvancedWidgetValue(node, "resolution_size", normalizeAdvancedResolutionSize(bucketSelect.value, sizeSelect.value));
      refreshSummary();
      scheduleAdvancedLayout(node, "settings");
    });
    valueBox.append(sizeSelect);
  };
  const renderCustomInputs = () => {
    valueBox.innerHTML = "";
    valueBox.className = "easyuse-anima-advanced-resolution-custom";
    const widthInput = document.createElement("input");
    protectAdvancedNativeControl(widthInput);
    widthInput.type = "number";
    widthInput.min = "32";
    widthInput.step = "32";
    widthInput.value = String(advancedCustomResolution(node).width);
    widthInput.setAttribute("aria-label", psText("advanced.customWidth"));
    widthInput.title = psText("advanced.customWidthTitle");
    const separator = document.createElement("span");
    separator.textContent = "×";
    const heightInput = document.createElement("input");
    protectAdvancedNativeControl(heightInput);
    heightInput.type = "number";
    heightInput.min = "32";
    heightInput.step = "32";
    heightInput.value = String(advancedCustomResolution(node).height);
    heightInput.setAttribute("aria-label", psText("advanced.customHeight"));
    heightInput.title = psText("advanced.customHeightTitle");
    const syncRaw = () => {
      setAdvancedCustomResolution(node, widthInput.value, heightInput.value);
      refreshSummary();
    };
    const normalize = () => {
      const width = snapResolution32(widthInput.value, 1024);
      const height = snapResolution32(heightInput.value, 1024);
      widthInput.value = String(width);
      heightInput.value = String(height);
      setAdvancedCustomResolution(node, width, height, { normalize: true });
      refreshSummary();
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
    refreshSummary();
    scheduleAdvancedLayout(node, "settings");
    scheduleAdvancedHighlights(node, { classify: false });
  });

  body.append(
    createAdvancedControlRow("advanced.resolutionBucket", bucketSelect, "advanced.resolutionBucketTitle"),
    createAdvancedControlRow("advanced.resolutionSize", valueBox, "advanced.resolutionSizeTitle"),
  );
  return body;
}

function createAdvancedResolutionBar(node) {
  const bucketWidget = findWidget(node, "resolution_bucket");
  const sizeWidget = findWidget(node, "resolution_size");
  if (!bucketWidget || !sizeWidget) {
    return document.createDocumentFragment();
  }
  return createAdvancedSummaryButtonRow(
    "easyuse-anima-advanced-resolutionbar",
    "advanced.resolutionBucket",
    "advanced.resolutionTitle",
    "resolution",
    advancedResolutionSummary(node),
    () => openAdvancedSettingsPopup(
      node,
      "advanced.resolutionBucket",
      "advanced.resolutionTitle",
      () => createAdvancedResolutionSettingsBody(node),
    ),
  );
}

function advancedFieldByTextarea(node, textarea) {
  const id = String(textarea?.dataset?.easyuseAnimaAdvancedFieldId || "");
  if (!id) {
    return null;
  }
  return (getAdvancedFields(node) || parseAdvancedFields(node))
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
    || !getAdvancedEditorElement(node)?.isConnected
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
  if (!getAdvancedEditorElement(node)?.isConnected) {
    finalizeAdvancedResize(node);
    return;
  }
  installAdvancedResizeEndListeners(node);
  clearTimeout(node.__easyuseAnimaAdvancedResizeFinalizeTimer);
  node.__easyuseAnimaAdvancedResizeFinalizeTimer = setTimeout(() => {
    finalizeAdvancedResize(node);
  }, 120);
}

function applyAdvancedLayout(node, reason = "layout") {
  const editor = getAdvancedEditorElement(node);
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
  if (!getAdvancedEditorElement(node)) {
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
  const fields = getAdvancedFields(node) || parseAdvancedFields(node);
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
    const currentFields = getAdvancedFields(node) || parseAdvancedFields(node);
    if (moveAdvancedFieldInPane(currentFields, field, direction)) {
      writeAdvancedFields(node, currentFields, { render: true });
    }
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
      const currentFields = getAdvancedFields(node) || parseAdvancedFields(node);
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
    const currentFields = getAdvancedFields(node) || parseAdvancedFields(node);
    currentFields.splice(globalIndex, 1);
    writeAdvancedFields(node, currentFields, { render: true });
  });

  const textarea = document.createElement("textarea");
  const linked = advancedFieldInputLinked(node, field);
  const inputName = advancedFieldInputName(field);
  textarea.value = advancedFieldDisplayText(node, field);
  textarea.style.height = `${field.height || 72}px`;
  textarea.style.overflowY = "hidden";
  textarea.placeholder = advancedFieldTextareaPlaceholder(field, psText);
  textarea.readOnly = false;
  textarea.classList.toggle("is-linked", linked);
  textarea.title = advancedFieldTextareaTitle(field, linked, psText);
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
  const rememberTextareaResizeStart = () => rememberAdvancedTextareaResizeStart(textarea);
  const captureTextareaManualResize = () => {
    const { changed, currentHeight } = captureAdvancedTextareaManualResize(textarea);
    if (!changed) {
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
    syncAdvancedTextareaLinkedInputValue(node, inputName, textarea.value, linked);
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
  const fields = getAdvancedFields(node) || parseAdvancedFields(node);
  if (type === "naia" && hasAdvancedNaia(fields, pane)) {
    return;
  }
  if (type === "trigger" && hasPositiveTrigger(fields)) {
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
    const currentFields = getAdvancedFields(node) || parseAdvancedFields(node);
    button.disabled = (type === "naia" && hasAdvancedNaia(currentFields, pane))
      || (type === "trigger" && hasPositiveTrigger(currentFields));
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

  const fields = advancedPaneFields(getAdvancedFields(node) || parseAdvancedFields(node), pane);
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
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return;
  }
  const fields = setAdvancedFields(node, parseAdvancedFields(node));
  applyAdvancedNaiaGeneralAutoToggle(node, fields);
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
  writeAdvancedFields(node, fields);
  scheduleAdvancedLayout(node, "render");
}

function hookAdvancedNode(node) {
  ensureAdvancedStyle();
  installAdvancedSaveSync(app, syncAllAdvancedNodes);
  ensureAdvancedWidgetValue(node, advancedWidget(node));
  removeAdvancedInternalInputSockets(node);
  hideAdvancedInternalWidget(node, "advanced_fields");
  hideAdvancedControlWidgets(node);
  node.serialize_widgets = true;
  node.minWidth = Math.max(Number(node.minWidth) || 0, 360);
  if (Array.isArray(node.size)) {
    node.size[0] = Math.max(Number(node.size[0]) || 420, 360);
  }
  if (!getAdvancedEditorElement(node)) {
    const editor = document.createElement("div");
    editor.className = "easyuse-anima-advanced-editor";
    editor.addEventListener("wheel", forwardAdvancedWheelToCanvas, { capture: true, passive: false });
    for (const eventName of ADVANCED_NATIVE_CONTROL_EVENTS) {
      editor.addEventListener(eventName, guardAdvancedEditorNativeControlEvent);
    }
    setAdvancedEditorElement(node, editor);
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
  repairAdvancedInternalWidgetValues(node);
  const fields = collectAdvancedEditorFields(node, getAdvancedFields(node) || parseAdvancedFields(node));
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
    if (name !== "advanced_fields" && !widget) {
      continue;
    }
    while (serialized.widgets_values.length <= index) {
      serialized.widgets_values.push(null);
    }
    if (name === "advanced_fields") {
      serialized.widgets_values[index] = fieldsValue;
    } else if (widget) {
      const value = normalizeAdvancedWidgetQueueValue(name, widget.value);
      widget.value = value;
      serialized.widgets_values[index] = value;
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
    setAdvancedFields(node, fields);
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
  for (const name of [
    "artist_mix_mode",
    "artist_mix_start_percent",
    "artist_mix_strength_scale",
    "artist_mix_style_gain",
    "artist_mix_rms_scale_cap",
    "artist_mix_exact_top_k",
    "artist_mix_cluster_count",
    "artist_mix_dominant_isolation",
    "artist_mix_dominant_threshold",
  ]) {
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

const syncAllAdvancedNodes = () => syncAdvancedNodes(app, syncAdvancedValues);

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

app.registerExtension({
  name: "easyuse-anima.prompt-studio",
  async setup() {
    installMiddlePanForwarder();
    installAdvancedSaveSync(app, syncAllAdvancedNodes);
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
      refreshAllPromptHighlights(true);
    });
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    registerPromptStudioNodeHooks(nodeType, nodeData, {
      applyAdvancedExecutedInputs,
      applyExecutedInputs,
      applyExtendSlotVisibility,
      applyWildcardExecutedInputs,
      captureAdvancedConfigure: (node, serialized) => (
        captureAdvancedConfigure(node, serialized, advancedWidget(node))
      ),
      hookStudioNode,
      isExtendNode,
      layoutExtendPromptWidgets,
      pruneDisconnectedAdvancedFieldInputValues,
      rebalanceStudioInputHeights,
      removeAdvancedInternalInputSockets,
      renderAdvancedEditor,
      renderExtendSlotControls,
      scheduleAdvancedResizeFinalize,
      scheduleHookAdvancedNode,
      syncAdvancedValues,
      syncStudioValues,
      updateAdvancedEditorWidth,
    });
  },
});
