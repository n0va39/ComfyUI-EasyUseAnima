// @ts-check

import {
  advancedEditorWidgetHeight,
  advancedMinimumNodeHeight,
  clampAdvancedNodeToMinimumHeight,
  updateAdvancedEditorWidth,
} from "./layout.js";
import {
  getAdvancedEditorElement,
} from "./state.js";

const ADVANCED_RESIZE_SETTLE_DELAY = 120;

function advancedEditorLayoutMetrics(editor) {
  return {
    clientWidth: Math.ceil(Number(editor?.clientWidth) || 0),
    scrollHeight: Math.ceil(Number(editor?.scrollHeight) || 0),
  };
}

function advancedEditorLayoutMetricsChanged(previous, current) {
  return Math.abs(current.clientWidth - previous.clientWidth) > 1
    || Math.abs(current.scrollHeight - previous.scrollHeight) > 1;
}

function disconnectAdvancedEditorWidthObserver(node) {
  node?.__easyuseAnimaAdvancedWidthObserver?.disconnect?.();
  if (!node) {
    return;
  }
  clearTimeout(node.__easyuseAnimaAdvancedWidthRemeasureTimer);
  node.__easyuseAnimaAdvancedWidthObserver = null;
  node.__easyuseAnimaAdvancedWidthObserverEditor = null;
  node.__easyuseAnimaAdvancedObservedEditorWidth = null;
  node.__easyuseAnimaAdvancedWidthRemeasureTimer = null;
}

function scheduleAdvancedWidthRemeasure(node, hooks = {}) {
  clearTimeout(node?.__easyuseAnimaAdvancedWidthRemeasureTimer);
  if (!node) {
    return;
  }
  node.__easyuseAnimaAdvancedWidthRemeasureTimer = setTimeout(() => {
    node.__easyuseAnimaAdvancedWidthRemeasureTimer = null;
    if (!node.graph || !getAdvancedEditorElement(node)?.isConnected) {
      return;
    }
    scheduleAdvancedLayout(node, "width", hooks);
  }, ADVANCED_RESIZE_SETTLE_DELAY);
}

function observeAdvancedEditorWidth(node, hooks = {}) {
  const editor = getAdvancedEditorElement(node);
  if (!node || !editor) {
    return;
  }
  if (
    node.__easyuseAnimaAdvancedWidthObserver
    && node.__easyuseAnimaAdvancedWidthObserverEditor === editor
  ) {
    return;
  }

  disconnectAdvancedEditorWidthObserver(node);
  node.__easyuseAnimaAdvancedWidthObserverEditor = editor;
  node.__easyuseAnimaAdvancedObservedEditorWidth = advancedEditorLayoutMetrics(editor).clientWidth;
  if (typeof ResizeObserver !== "function") {
    return;
  }

  const observer = new ResizeObserver(() => {
    if (
      !node.graph
      || !editor.isConnected
      || getAdvancedEditorElement(node) !== editor
    ) {
      disconnectAdvancedEditorWidthObserver(node);
      return;
    }
    const previousWidth = Number(node.__easyuseAnimaAdvancedObservedEditorWidth) || 0;
    const currentWidth = advancedEditorLayoutMetrics(editor).clientWidth;
    node.__easyuseAnimaAdvancedObservedEditorWidth = currentWidth;
    if (Math.abs(currentWidth - previousWidth) > 1) {
      scheduleAdvancedWidthRemeasure(node, hooks);
    }
  });
  node.__easyuseAnimaAdvancedWidthObserver = observer;
  observer.observe(editor);
}

function scheduleAdvancedScrollbarRemeasure(node, editor, previousMetrics, hooks = {}) {
  cancelAnimationFrame(node?.__easyuseAnimaAdvancedScrollbarMeasureFrame);
  if (!node || !editor?.isConnected) {
    return;
  }
  node.__easyuseAnimaAdvancedScrollbarMeasureFrame = requestAnimationFrame(() => {
    node.__easyuseAnimaAdvancedScrollbarMeasureFrame = null;
    if (!node.graph || !editor.isConnected) {
      return;
    }
    const currentMetrics = advancedEditorLayoutMetrics(editor);
    if (advancedEditorLayoutMetricsChanged(previousMetrics, currentMetrics)) {
      scheduleAdvancedLayout(node, "scrollbar", hooks);
    }
  });
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

function finalizeAdvancedResize(node, hooks = {}) {
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
  scheduleAdvancedLayout(node, "resize", hooks);
}

function installAdvancedResizeEndListeners(node, hooks = {}) {
  if (!node || node.__easyuseAnimaAdvancedResizeEndHandler) {
    return;
  }
  const handler = () => finalizeAdvancedResize(node, hooks);
  node.__easyuseAnimaAdvancedResizeEndHandler = handler;
  document.addEventListener("pointerup", handler, true);
  document.addEventListener("pointercancel", handler, true);
  document.addEventListener("mouseup", handler, true);
}

function scheduleAdvancedResizeFinalize(node, hooks = {}) {
  if (!getAdvancedEditorElement(node)?.isConnected) {
    finalizeAdvancedResize(node, hooks);
    return;
  }
  installAdvancedResizeEndListeners(node, hooks);
  clearTimeout(node.__easyuseAnimaAdvancedResizeFinalizeTimer);
  node.__easyuseAnimaAdvancedResizeFinalizeTimer = setTimeout(() => {
    finalizeAdvancedResize(node, hooks);
  }, ADVANCED_RESIZE_SETTLE_DELAY);
}

function applyAdvancedLayout(node, reason = "layout", hooks = {}) {
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
    const previousMetrics = advancedEditorLayoutMetrics(editor);

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

    scheduleAdvancedScrollbarRemeasure(node, editor, previousMetrics, hooks);

    hooks.markGraphDirty?.();
    requestAnimationFrame(() => hooks.markGraphDirty?.());
  } finally {
    node.__easyuseAnimaApplyingLayout = false;
  }
  hooks.scheduleAdvancedHighlights?.(node, {
    classify: reason !== "resize" && reason !== "scrollbar" && reason !== "width",
  });
}

const ADVANCED_LAYOUT_REASON_PRIORITY = {
  layout: 0,
  render: 1,
  textarea: 1,
  connections: 1,
  executed: 1,
  settings: 1,
  scrollbar: 2,
  width: 2,
  resize: 3,
};

function advancedLayoutReasonPriority(reason) {
  return ADVANCED_LAYOUT_REASON_PRIORITY[reason] ?? 0;
}

function scheduleAdvancedLayout(node, reason = "layout", hooks = {}) {
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
    applyAdvancedLayout(node, layoutReason, hooks);
  });
}

export {
  applyAdvancedLayout,
  clearAdvancedResizeEndListeners,
  disconnectAdvancedEditorWidthObserver,
  finalizeAdvancedResize,
  installAdvancedResizeEndListeners,
  observeAdvancedEditorWidth,
  scheduleAdvancedLayout,
  scheduleAdvancedResizeFinalize,
};
