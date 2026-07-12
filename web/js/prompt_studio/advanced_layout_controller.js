// @ts-check

import {
  updateAdvancedEditorWidth,
} from "./layout.js";
import {
  getAdvancedEditorElement,
} from "./state.js";

const ADVANCED_RESIZE_SETTLE_DELAY = 120;

function advancedEditorClientWidth(editor) {
  return Math.ceil(Number(editor?.clientWidth) || 0);
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
    hooks.remeasureAdvancedTextareaHeightsForWidth?.(node);
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
  node.__easyuseAnimaAdvancedObservedEditorWidth = advancedEditorClientWidth(editor);
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
    const currentWidth = advancedEditorClientWidth(editor);
    node.__easyuseAnimaAdvancedObservedEditorWidth = currentWidth;
    if (Math.abs(currentWidth - previousWidth) > 1) {
      scheduleAdvancedWidthRemeasure(node, hooks);
    }
  });
  node.__easyuseAnimaAdvancedWidthObserver = observer;
  observer.observe(editor);
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
    node.__easyuseAnimaAdvancedLastLayoutReason = reason;

    hooks.markGraphDirty?.();
    requestAnimationFrame(() => hooks.markGraphDirty?.());
  } finally {
    node.__easyuseAnimaApplyingLayout = false;
  }
  hooks.scheduleAdvancedHighlights?.(node, {
    classify: reason !== "resize" && reason !== "width",
  });
}

const ADVANCED_LAYOUT_REASON_PRIORITY = {
  layout: 0,
  render: 1,
  textarea: 1,
  connections: 1,
  executed: 1,
  settings: 1,
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
