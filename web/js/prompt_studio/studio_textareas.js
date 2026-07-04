// @ts-check

import {
  EXTEND_FIELD_HEIGHTS,
  FIELD_HEIGHTS,
  STUDIO_WIDGET_VERTICAL_GAP,
} from "./constants.js";
import {
  findInputEl,
  findWidget,
} from "./widgets.js";

/** @typedef {import("./types.js").PromptStudioInputElement} PromptStudioInputElement */

/**
 * @param {unknown} widget
 * @returns {PromptStudioInputElement | null}
 */
function findStudioInput(widget) {
  return findInputEl(widget);
}

function studioDefaultHeight(widget) {
  return EXTEND_FIELD_HEIGHTS[widget.name] || FIELD_HEIGHTS[widget.name] || 72;
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

function studioMinimumHeight(widget, input = findStudioInput(widget)) {
  return studioVisualMinimumHeight(widget);
}

function studioContentHeight(widget, input = findStudioInput(widget)) {
  return desiredTextareaHeight(input, 0, studioVisualMinimumHeight(widget), { includeCurrent: false });
}

function studioCurrentHeight(widget, input = findStudioInput(widget)) {
  const styleHeight = Number.parseFloat(input?.style?.height || "");
  return Math.round(
    Number(input?.offsetHeight)
    || Number(input?.clientHeight)
    || styleHeight
    || Number(widget?.__easyuseAnimaHeight)
    || studioDefaultHeight(widget),
  );
}

/**
 * @param {boolean | "immediate"} [refresh=false]
 */
function setStudioInputHeight(node, widget, height, refresh = false, hooks = {}) {
  const input = findStudioInput(widget);
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
      hooks.refreshNodeSize?.(node, { immediate: refresh === "immediate" });
    }
  } else {
    input.style.height = `${nextHeight}px`;
  }
  syncStudioOverflow(widget);
  hooks.updateHighlight?.(node, widget);
}

function syncStudioOverflow(widget) {
  const input = findStudioInput(widget);
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

/**
 * @param {boolean | "immediate"} [refresh=false]
 */
function growStudioManualHeightToContent(node, widget, refresh = false, hooks = {}) {
  const input = findStudioInput(widget);
  if (!input || !widget.__easyuseAnimaManualHeight || widget.__easyuseAnimaExtendHidden) {
    return false;
  }
  const currentHeight = studioCurrentHeight(widget, input);
  const contentHeight = studioContentHeight(widget, input);
  if (contentHeight > currentHeight + 2) {
    setStudioInputHeight(node, widget, contentHeight, refresh, hooks);
    return true;
  }
  syncStudioOverflow(widget);
  hooks.updateHighlight?.(node, widget);
  return false;
}

function setStudioManualHeight(node, widget, hooks = {}) {
  const input = findStudioInput(widget);
  if (!input || widget.__easyuseAnimaExtendHidden) {
    return;
  }
  widget.__easyuseAnimaManualHeight = true;
  setStudioInputHeight(
    node,
    widget,
    Math.max(studioCurrentHeight(widget, input), studioContentHeight(widget, input)),
    "immediate",
    hooks,
  );
}

/**
 * @param {boolean | "immediate"} [refresh=false]
 */
function expandStudioInputToContent(node, widget, refresh = false, hooks = {}) {
  const input = findStudioInput(widget);
  if (!input || widget.__easyuseAnimaExtendHidden) {
    return;
  }
  if (widget.__easyuseAnimaManualHeight) {
    growStudioManualHeightToContent(node, widget, refresh, hooks);
    return;
  }
  const height = studioContentHeight(widget, input);
  setStudioInputHeight(node, widget, height, refresh, hooks);
}

function visibleStudioWidgets(node, hooks = {}) {
  const fieldNames = hooks.studioFieldNames?.(node) || [];
  return fieldNames
    .map((name) => findWidget(node, name))
    .filter((widget) => {
      const input = findStudioInput(widget);
      return widget && input && !widget.hidden && !widget.__easyuseAnimaExtendHidden;
    });
}

function widgetHeight(widget, fallback = 24) {
  const input = findStudioInput(widget);
  if (input && !widget.__easyuseAnimaExtendHidden) {
    return studioCurrentHeight(widget, input) + STUDIO_WIDGET_VERTICAL_GAP;
  }
  const size = widget?.computeSize?.();
  return Math.max(0, Number(size?.[1]) || Number(widget?.__height) || fallback);
}

function rebalanceStudioInputHeights(node, hooks = {}) {
  const widgets = visibleStudioWidgets(node, hooks);
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
      setStudioInputHeight(node, widget, nextHeight, false, hooks);
    }
    hooks.refreshNodeSize?.(node, { immediate: true });
    return;
  }

  for (const widget of widgets) {
    expandStudioInputToContent(node, widget, false, hooks);
  }
  hooks.refreshNodeSize?.(node, { immediate: true });
}

export {
  desiredTextareaHeight,
  expandStudioInputToContent,
  growStudioManualHeightToContent,
  rebalanceStudioInputHeights,
  setStudioInputHeight,
  setStudioManualHeight,
  studioCurrentHeight,
  studioDefaultHeight,
  syncStudioOverflow,
  textareaContentHeight,
  visibleStudioWidgets,
  widgetHeight,
};
