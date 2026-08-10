// @ts-check

import {
  parseAdvancedFields,
} from "./advanced_fields_state.js";
import {
  classifyPrompt,
  copyInputTextMetrics,
  ensureHighlightOverlay,
  highlightOverlayHtml,
  overlayBounds,
  overlayScrollbarPadding,
  syncOverlayBounds,
} from "./highlight.js";
import {
  applyPromptStudioTextStyle,
} from "./settings.js";
import {
  highlightRequestOwnsText,
  highlightTokensForText,
} from "./highlight_revision.js";
import {
  getAdvancedEditorElement,
  getAdvancedFields,
} from "./state.js";
import { registerExternalAutocompleteInput } from "../autocomplete/entry_lifecycle.js";

/** @typedef {import("./types.js").PromptStudioAdvancedTextarea} PromptStudioAdvancedTextarea */
/** @typedef {import("./types.js").PromptStudioWindow} PromptStudioWindow */

/** @returns {PromptStudioWindow} */
function promptStudioWindow() {
  return /** @type {PromptStudioWindow} */ (window);
}

/**
 * @param {HTMLTextAreaElement} textarea
 * @returns {PromptStudioAdvancedTextarea}
 */
function advancedTextarea(textarea) {
  return /** @type {PromptStudioAdvancedTextarea} */ (textarea);
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
  const input = advancedTextarea(textarea);
  applyPromptStudioTextStyle(textarea);
  input.__easyuseAnimaNode = node;
  input.__easyuseAnimaField = field;
  input.__easyuseAnimaHighlightRefresh = (force = false) => updateAdvancedFieldHighlight(node, field, textarea, null, force);
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
  const currentTokens = highlightTokensForText(
    value,
    state.lastText,
    tokens || state.tokens || [],
  );
  overlay.innerHTML = highlightOverlayHtml(value, currentTokens, textarea.placeholder || "", textarea);
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
  const request = { sequence: seq, text };
  updateAdvancedFieldHighlight(node, field, textarea, state.tokens);
  classifyPrompt(text)
    .then((tokens) => {
      if (!highlightRequestOwnsText(
        request,
        state.seq,
        textarea.value,
        textarea.isConnected,
      )) {
        return;
      }
      state.lastText = text;
      state.tokens = tokens;
      updateAdvancedFieldHighlight(node, field, textarea, tokens);
    })
    .catch(() => {
      if (!highlightRequestOwnsText(
        request,
        state.seq,
        textarea.value,
        textarea.isConnected,
      )) {
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
  const hostWindow = promptStudioWindow();
  registerExternalAutocompleteInput(hostWindow, textarea, options);
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
    const htmlContent = highlightOverlayHtml(
      value,
      highlightTokensForText(value, state.lastText, state.tokens),
      textarea.placeholder || "",
      textarea,
    );

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

export {
  advancedHighlightState,
  refreshAdvancedHighlights,
  registerAdvancedAutocompleteInput,
  scheduleAdvancedFieldHighlight,
  scheduleAdvancedHighlights,
  updateAdvancedFieldHighlight,
};
