// @ts-check

import {
  copyInputTextMetrics,
  ensureHighlightOverlay,
  highlightOverlayHtml,
  setHighlightOverlayHtml,
  syncOverlayBounds,
} from "./highlight.js";
import {
  applyPromptStudioTextStyle,
} from "./settings.js";
import {
  highlightTokensForText,
} from "./highlight_revision.js";
import {
  findInputEl,
} from "./widgets.js";

/** @typedef {import("./types.js").PromptStudioInputElement} PromptStudioInputElement */

/**
 * @param {unknown} widget
 * @returns {PromptStudioInputElement | null}
 */
function findHighlightInput(widget) {
  return findInputEl(widget);
}

function displayText(_node, widget, input = findHighlightInput(widget)) {
  return String(input?.value ?? widget?.value ?? "");
}

function updateHighlight(node, widget, tokens = widget.__easyuseAnimaTokens || [], forceCopyMetrics = false) {
  const input = findHighlightInput(widget);
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
  const value = displayText(node, widget, input);
  const currentTokens = highlightTokensForText(
    value,
    widget.__easyuseAnimaLastClassifiedText,
    tokens,
  );
  setHighlightOverlayHtml(overlay, highlightOverlayHtml(
    value, currentTokens, input.placeholder || "", input,
  ));
  syncOverlayBounds(input, overlay);
}

export {
  displayText,
  updateHighlight,
};
