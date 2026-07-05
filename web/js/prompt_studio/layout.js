// @ts-check

import {
  ADVANCED_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT,
  ADVANCED_EDITOR_MIN_RESIZE_VIEWPORT_HEIGHT,
  ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT,
} from "./constants.js";
import {
  getAdvancedEditorElement,
} from "./state.js";
import {
  isNodeUserResizeActive,
} from "./node_resize_tracking.js";

const ADVANCED_NODE_CHROME_OFFSET_FLOOR = 72;
const ADVANCED_NODE_CHROME_OFFSET_MAX = 220;

function advancedEditorWidth(node) {
  return Math.max(280, Math.round((Number(node?.size?.[0]) || 420) - 18));
}

function measureAdvancedEditorHeight(editor) {
  if (!editor) {
    return 0;
  }
  return Math.ceil(Math.max(
    Number(editor.scrollHeight) || 0,
    Number(editor.offsetHeight) || 0,
    measureAdvancedEditorContentHeight(editor),
  ));
}

function measureAdvancedEditorContentHeight(editor) {
  if (!editor) {
    return 0;
  }
  const childrenHeight = [...editor.children].reduce((total, child) => {
    if (!(child instanceof HTMLElement)) {
      return total;
    }
    const style = getComputedStyle(child);
    const marginTop = Number.parseFloat(style?.marginTop || "") || 0;
    const marginBottom = Number.parseFloat(style?.marginBottom || "") || 0;
    return total + marginTop + Number(child.offsetHeight || 0) + marginBottom;
  }, 0);
  return Math.ceil(Math.max(childrenHeight, 0));
}

function advancedEditorTextareas(editor) {
  return [...(editor?.querySelectorAll?.("textarea[data-easyuse-anima-advanced-field-id]") || [])];
}

function advancedTextareaPixelMetric(textarea, property) {
  const style = textarea instanceof HTMLElement ? getComputedStyle(textarea) : null;
  return Number.parseFloat(style?.[property] || "") || 0;
}

function advancedTextareaTwoLineHeight(textarea) {
  const style = textarea instanceof HTMLElement ? getComputedStyle(textarea) : null;
  const fontSize = Number.parseFloat(style?.fontSize || "") || 12;
  const lineHeightRaw = Number.parseFloat(style?.lineHeight || "");
  const lineHeight = Number.isFinite(lineHeightRaw) && lineHeightRaw > 0 ? lineHeightRaw : fontSize * 1.35;
  const verticalPadding =
    advancedTextareaPixelMetric(textarea, "paddingTop")
    + advancedTextareaPixelMetric(textarea, "paddingBottom");
  const verticalBorder =
    advancedTextareaPixelMetric(textarea, "borderTopWidth")
    + advancedTextareaPixelMetric(textarea, "borderBottomWidth");
  return Math.ceil(lineHeight * 2 + verticalPadding + verticalBorder);
}

function advancedTextareaContentHeight(textarea) {
  if (!(textarea instanceof HTMLTextAreaElement)) {
    return 0;
  }
  const previousHeight = textarea.style.height;
  const previousMinHeight = textarea.style.minHeight;
  const previousOverflow = textarea.style.overflowY;
  textarea.style.minHeight = "0px";
  textarea.style.height = "auto";
  textarea.style.overflowY = "hidden";
  const contentHeight = Math.ceil(
    (Number(textarea.scrollHeight) || 0)
    + advancedTextareaPixelMetric(textarea, "borderTopWidth")
    + advancedTextareaPixelMetric(textarea, "borderBottomWidth"),
  );
  textarea.style.height = previousHeight;
  textarea.style.minHeight = previousMinHeight;
  textarea.style.overflowY = previousOverflow;
  return contentHeight;
}

function advancedTextareaMinimumHeight(textarea) {
  return Math.max(
    46,
    advancedTextareaTwoLineHeight(textarea),
  );
}

function advancedTextareaCurrentHeight(textarea) {
  return Math.max(
    advancedTextareaMinimumHeight(textarea),
    Math.ceil(Number.parseFloat(textarea?.style?.height || "") || 0),
    Math.ceil(Number(textarea?.offsetHeight) || 0),
    Math.ceil(Number(textarea?.clientHeight) || 0),
  );
}

function advancedTextareaHeightTotal(textareas, measure) {
  return textareas.reduce((sum, textarea) => sum + measure(textarea), 0);
}

function advancedEditorFixedHeight(editor, textareas = advancedEditorTextareas(editor)) {
  const editorHeight = measureAdvancedEditorContentHeight(editor);
  const textareaTotal = advancedTextareaHeightTotal(textareas, advancedTextareaCurrentHeight);
  return Math.max(0, editorHeight - textareaTotal);
}

function advancedEditorContentMinimumHeight(node) {
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT;
  }
  const textareas = advancedEditorTextareas(editor);
  const fixedHeight = advancedEditorFixedHeight(editor, textareas);
  const textareaMinTotal = advancedTextareaHeightTotal(textareas, advancedTextareaMinimumHeight);
  return Math.ceil(Math.max(ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT, fixedHeight + textareaMinTotal));
}

function advancedEditorAutoViewportCap() {
  const viewportHeight = Number(globalThis.innerHeight) || 0;
  const viewportCap = viewportHeight > 0 ? Math.floor(viewportHeight * 0.72) : ADVANCED_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT;
  return Math.ceil(Math.max(
    ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT,
    Math.min(ADVANCED_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT, viewportCap),
  ));
}

function advancedEditorMinimumHeight(node) {
  const contentMinimum = advancedEditorContentMinimumHeight(node);
  return Math.ceil(Math.max(
    ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT,
    Math.min(contentMinimum, advancedEditorAutoViewportCap()),
  ));
}

function advancedEditorResizeMinimumHeight() {
  return ADVANCED_EDITOR_MIN_RESIZE_VIEWPORT_HEIGHT;
}

function hasAdvancedUserViewportHeight(node) {
  return Number.isFinite(Number(node?.__easyuseAnimaAdvancedUserViewportHeight));
}

function advancedEditorViewportMinimumHeight(node) {
  return node?.__easyuseAnimaAdvancedUserResizing
    || isNodeUserResizeActive(node)
    || hasAdvancedUserViewportHeight(node)
    ? advancedEditorResizeMinimumHeight()
    : advancedEditorMinimumHeight(node);
}

function advancedNodeAvailableEditorViewportHeight(node) {
  const minimumHeight = advancedEditorResizeMinimumHeight();
  const nodeHeight = Number(node?.size?.[1]) || 0;
  const chromeOffset = advancedNodeChromeOffset(node);
  const availableHeight = Math.max(0, nodeHeight - chromeOffset);
  return Math.ceil(Math.max(minimumHeight, availableHeight));
}

function advancedAvailableEditorViewportHeight(node) {
  const minimumHeight = advancedEditorViewportMinimumHeight(node);
  const nodeHeight = Number(node?.size?.[1]) || 0;
  const chromeOffset = advancedNodeChromeOffset(node);
  const availableHeight = Math.max(0, nodeHeight - chromeOffset);
  return Math.ceil(Math.max(minimumHeight, availableHeight));
}

function advancedEditorWidgetHeight(node) {
  if (node?.__easyuseAnimaAdvancedUserResizing || isNodeUserResizeActive(node)) {
    return advancedNodeAvailableEditorViewportHeight(node);
  }
  if (hasAdvancedUserViewportHeight(node)) {
    return Math.ceil(Math.max(
      advancedEditorResizeMinimumHeight(),
      Number(node.__easyuseAnimaAdvancedUserViewportHeight) || 0,
    ));
  }
  if (getAdvancedEditorElement(node)?.isConnected) {
    return advancedAvailableEditorViewportHeight(node);
  }
  return Math.ceil(Math.max(
    advancedEditorMinimumHeight(node),
    Number(node?.__easyuseAnimaAdvancedWidgetHeight) || 0,
  ));
}

function advancedEditorWidget(node) {
  return node?.__easyuseAnimaAdvancedDomWidget
    || node?.widgets?.find?.((widget) => widget?.name === "easyuse_anima_advanced_editor")
    || null;
}

function applyAdvancedEditorViewportStyle(editor, height) {
  if (!(editor instanceof HTMLElement)) {
    return;
  }
  const viewportHeight = Math.max(
    advancedEditorResizeMinimumHeight(),
    Math.round(Number(height) || 0),
  );
  const heightValue = `${viewportHeight}px`;
  editor.style.setProperty("--easyuse-anima-advanced-editor-height", heightValue);
  editor.style.height = heightValue;
  editor.style.maxHeight = heightValue;
  editor.style.minHeight = "0px";
  editor.style.overflowY = "auto";
}

function applyAdvancedWidgetAllocation(node, height, options = {}) {
  const widget = advancedEditorWidget(node);
  const viewportHeight = Math.max(
    advancedEditorResizeMinimumHeight(),
    Math.round(Number(height) || 0),
  );
  if (widget) {
    widget.computedHeight = viewportHeight;
  }
  node.__easyuseAnimaAdvancedWidgetHeight = viewportHeight;
  if (options.rememberUserViewport === true) {
    node.__easyuseAnimaAdvancedUserViewportHeight = viewportHeight;
  }
  return viewportHeight;
}

function advancedNodeChromeOffset(node) {
  const widget = advancedEditorWidget(node);
  const widgetY = Number(widget?.y);
  const stableWidgetTop = Number.isFinite(widgetY) && widgetY > 0
    ? Math.min(widgetY, ADVANCED_NODE_CHROME_OFFSET_MAX - 12)
    : 0;
  return Math.ceil(Math.max(ADVANCED_NODE_CHROME_OFFSET_FLOOR, stableWidgetTop + 12));
}

function advancedMinimumNodeHeight(node) {
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return advancedEditorResizeMinimumHeight();
  }
  const viewportMinimum = advancedEditorViewportMinimumHeight(node);
  const chromeOffset = advancedNodeChromeOffset(node);
  return Math.ceil(Math.max(
    advancedEditorResizeMinimumHeight(),
    viewportMinimum + chromeOffset,
  ));
}

function clampAdvancedNodeToMinimumHeight(node) {
  if (!node?.size || typeof node.setSize !== "function") {
    return false;
  }
  const currentWidth = Number(node.size[0]) || 360;
  const currentHeight = Number(node.size[1]) || 0;
  const minimumHeight = advancedMinimumNodeHeight(node);
  if (currentHeight >= minimumHeight - 1) {
    return false;
  }
  node.__easyuseAnimaApplyingLayout = true;
  try {
    node.setSize([currentWidth, minimumHeight]);
  } finally {
    node.__easyuseAnimaApplyingLayout = false;
  }
  return true;
}

function updateAdvancedEditorWidth(node) {
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return;
  }
  const width = Number(node?.size?.[0]) || 360;
  const editorWidth = advancedEditorWidth(node);
  editor.style.width = `${editorWidth}px`;
  editor.style.maxWidth = `${editorWidth}px`;
  editor.classList.toggle("is-narrow", width < 620);
}

export {
  advancedEditorAutoViewportCap,
  advancedEditorContentMinimumHeight,
  advancedEditorFixedHeight,
  advancedEditorMinimumHeight,
  advancedEditorResizeMinimumHeight,
  advancedEditorTextareas,
  advancedEditorViewportMinimumHeight,
  advancedEditorWidget,
  advancedEditorWidgetHeight,
  advancedEditorWidth,
  advancedNodeAvailableEditorViewportHeight,
  advancedMinimumNodeHeight,
  advancedNodeChromeOffset,
  advancedTextareaContentHeight,
  advancedTextareaCurrentHeight,
  advancedTextareaMinimumHeight,
  applyAdvancedEditorViewportStyle,
  applyAdvancedWidgetAllocation,
  clampAdvancedNodeToMinimumHeight,
  measureAdvancedEditorContentHeight,
  measureAdvancedEditorHeight,
  updateAdvancedEditorWidth,
};
