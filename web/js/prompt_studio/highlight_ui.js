import {
  copyInputTextMetrics,
  ensureHighlightOverlay,
  highlightOverlayHtml,
  syncOverlayBounds,
} from "./highlight.js";
import {
  applyPromptStudioTextStyle,
} from "./settings.js";
import {
  findInputEl,
  isWidgetInputLinked,
} from "./widgets.js";

function displayText(node, widget) {
  if (isWidgetInputLinked(node, widget.name) && widget.__easyuseAnimaExecutedText != null) {
    return String(widget.__easyuseAnimaExecutedText);
  }
  return String(widget?.inputEl?.value ?? widget?.value ?? "");
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

export {
  displayText,
  updateHighlight,
};
