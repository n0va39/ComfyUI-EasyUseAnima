// @ts-check

import {
  advancedEditorWidgetHeight,
  advancedMinimumNodeHeight,
  applyAdvancedEditorViewportStyle,
  clampAdvancedNodeToMinimumHeight,
  updateAdvancedEditorWidth,
} from "./layout.js";
import {
  getAdvancedEditorElement,
} from "./state.js";
import {
  syncAdvancedTextareaHeightsForWidth,
} from "./advanced_fields_ui.js";

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
  syncAdvancedTextareaHeightsForWidth(node, hooks);
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
  }, 120);
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

    const currentWidth = Number(node.size[0]) || 360;
    const currentHeight = Number(node.size[1]) || 0;
    const minimumHeight = advancedMinimumNodeHeight(node);
    const widgetHeight = advancedEditorWidgetHeight(node);
    applyAdvancedEditorViewportStyle(editor, widgetHeight);
    node.__easyuseAnimaAdvancedWidgetHeight = widgetHeight;
    node.__easyuseAnimaAdvancedLastEditorHeight = widgetHeight;
    node.__easyuseAnimaAdvancedLastLayoutReason = reason;

    if (typeof node.setSize === "function" && currentHeight < minimumHeight - 1) {
      node.setSize([currentWidth, minimumHeight]);
    }

    hooks.markGraphDirty?.();
    requestAnimationFrame(() => hooks.markGraphDirty?.());
  } finally {
    node.__easyuseAnimaApplyingLayout = false;
  }
  hooks.scheduleAdvancedHighlights?.(node, { classify: reason !== "resize" });
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
  finalizeAdvancedResize,
  installAdvancedResizeEndListeners,
  scheduleAdvancedLayout,
  scheduleAdvancedResizeFinalize,
};
