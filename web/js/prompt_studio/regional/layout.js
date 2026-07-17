// @ts-check

import {
  scheduleRegionalNodeFrame,
} from "./lifecycle.js";

const REGIONAL_NODE_MIN_WIDTH = 560;
const REGIONAL_NODE_DEFAULT_WIDTH = 620;
const REGIONAL_EDITOR_MIN_VIEWPORT_HEIGHT = 360;
const REGIONAL_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT = 640;
const REGIONAL_LAYOUT_REASON_PRIORITY = {
  layout: 0,
  render: 1,
  textarea: 1,
  executed: 1,
  settings: 1,
  resize: 3,
};

/**
 * @param {any} app
 * @param {any} runtime
 * @param {{
 *   refreshPromptStudioHighlights: (node: any, textareas: any[], fields: any[], options: any) => void,
 *   requestPromptStudioOverlaySync: (textarea: any, forceCopyMetrics?: boolean) => void,
 * }} hooks
 */
function createRegionalLayout(app, runtime, hooks) {
  /** @param {any} node */
  function regionalTextareas(node) {
    const editor = node?.__easyuseAnimaRegionalEditorEl;
    if (!editor) {
      return [];
    }
    return Array.from(
      editor.querySelectorAll(
        "textarea[data-easyuse-anima-prompt-studio-variant-field-id]",
      ),
    );
  }

  /** @param {any} node @param {boolean} [classify] */
  function scheduleRegionalFieldHighlights(node, classify = true) {
    scheduleRegionalNodeFrame(node, "field-highlights", () => {
      hooks.refreshPromptStudioHighlights(
        node,
        regionalTextareas(node),
        node.__easyuseAnimaRegionalFields || runtime.defaultFields(),
        { namespace: "regional", classify },
      );
    }, { replace: true });
  }

  /** @param {any} node */
  function regionalEditorWidth(node) {
    return Math.max(
      REGIONAL_NODE_MIN_WIDTH - 18,
      Math.round((Number(node?.size?.[0]) || REGIONAL_NODE_DEFAULT_WIDTH) - 18),
    );
  }

  /** @param {any} editor */
  function measureRegionalEditorContentHeight(editor) {
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
    return Math.ceil(Math.max(
      childrenHeight,
      Number(editor.scrollHeight) || 0,
      Number(editor.offsetHeight) || 0,
    ));
  }

  function regionalEditorAutoViewportCap() {
    const viewportHeight = Number(globalThis.innerHeight) || 0;
    const viewportCap = viewportHeight > 0
      ? Math.floor(viewportHeight * 0.72)
      : REGIONAL_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT;
    return Math.ceil(Math.max(
      REGIONAL_EDITOR_MIN_VIEWPORT_HEIGHT,
      Math.min(REGIONAL_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT, viewportCap),
    ));
  }

  /** @param {any} node */
  function regionalEditorMinimumHeight(node) {
    const contentHeight = measureRegionalEditorContentHeight(
      node?.__easyuseAnimaRegionalEditorEl,
    );
    return Math.ceil(Math.max(
      REGIONAL_EDITOR_MIN_VIEWPORT_HEIGHT,
      Math.min(
        Math.max(contentHeight, REGIONAL_EDITOR_MIN_VIEWPORT_HEIGHT),
        regionalEditorAutoViewportCap(),
      ),
    ));
  }

  /** @param {any} node */
  function regionalEditorWidget(node) {
    return node?.__easyuseAnimaRegionalDomWidget
      || node?.widgets?.find?.(
        (widget) => widget?.name === "easyuse_anima_regional_editor",
      )
      || null;
  }

  /** @param {any} node */
  function regionalNodeChromeOffset(node) {
    const widget = regionalEditorWidget(node);
    const widgetY = Math.max(
      Number(widget?.last_y) || 0,
      Number(widget?.y) || 0,
    );
    return Math.ceil(Math.max(72, widgetY + 12));
  }

  /** @param {any} node */
  function regionalMinimumNodeHeight(node) {
    return Math.ceil(regionalEditorMinimumHeight(node) + regionalNodeChromeOffset(node));
  }

  /** @param {any} node */
  function regionalAvailableEditorViewportHeight(node) {
    const minimumHeight = regionalEditorMinimumHeight(node);
    const nodeHeight = Number(node?.size?.[1]) || 0;
    const availableHeight = Math.max(0, nodeHeight - regionalNodeChromeOffset(node));
    return Math.ceil(Math.max(minimumHeight, availableHeight));
  }

  /** @param {any} node */
  function regionalEditorWidgetHeight(node) {
    if (node?.__easyuseAnimaRegionalEditorEl?.isConnected) {
      return regionalAvailableEditorViewportHeight(node);
    }
    return Math.ceil(Math.max(
      regionalEditorMinimumHeight(node),
      Number(node?.__easyuseAnimaRegionalWidgetHeight) || 0,
    ));
  }

  /** @param {any} node */
  function updateRegionalEditorWidth(node) {
    const editor = node?.__easyuseAnimaRegionalEditorEl;
    if (!editor) {
      return;
    }
    const width = Number(node?.size?.[0]) || REGIONAL_NODE_DEFAULT_WIDTH;
    const editorWidth = regionalEditorWidth(node);
    editor.style.width = `${editorWidth}px`;
    editor.style.maxWidth = `${editorWidth}px`;
    editor.classList.toggle("is-narrow", width < 620);
  }

  /** @param {any} node @param {string} [reason] */
  function applyRegionalLayout(node, reason = "layout") {
    const editor = node?.__easyuseAnimaRegionalEditorEl;
    if (!editor || !node.size || node.__easyuseAnimaRegionalApplyingLayout) {
      return;
    }
    node.__easyuseAnimaRegionalApplyingLayout = true;
    try {
      updateRegionalEditorWidth(node);
      const currentWidth = Number(node.size[0]) || REGIONAL_NODE_DEFAULT_WIDTH;
      const currentHeight = Number(node.size[1]) || 0;
      const minimumHeight = regionalMinimumNodeHeight(node);
      const widgetHeight = regionalEditorWidgetHeight(node);
      editor.style.height = `${widgetHeight}px`;
      editor.style.maxHeight = `${widgetHeight}px`;
      node.__easyuseAnimaRegionalWidgetHeight = widgetHeight;
      node.__easyuseAnimaRegionalLastLayoutReason = reason;
      const widget = regionalEditorWidget(node);
      if (widget) {
        widget.computedHeight = widgetHeight;
      }
      if (typeof node.setSize === "function" && currentHeight < minimumHeight - 1) {
        node.setSize([Math.max(currentWidth, REGIONAL_NODE_MIN_WIDTH), minimumHeight]);
      }
      for (const textarea of regionalTextareas(node)) {
        hooks.requestPromptStudioOverlaySync(textarea, true);
      }
      node.setDirtyCanvas?.(true, true);
      app.graph?.setDirtyCanvas?.(true, true);
      scheduleRegionalNodeFrame(
        node,
        "layout-dirty-canvas",
        () => app.graph?.setDirtyCanvas?.(true, true),
        { replace: true },
      );
    } finally {
      node.__easyuseAnimaRegionalApplyingLayout = false;
    }
    scheduleRegionalFieldHighlights(node, reason !== "resize");
  }

  /** @param {string} reason */
  function regionalLayoutReasonPriority(reason) {
    return REGIONAL_LAYOUT_REASON_PRIORITY[reason] ?? 0;
  }

  /** @param {any} node @param {string} [reason] */
  function scheduleRegionalLayout(node, reason = "layout") {
    if (!node?.__easyuseAnimaRegionalEditorEl) {
      return;
    }
    updateRegionalEditorWidth(node);
    const currentReason = node.__easyuseAnimaRegionalLayoutReason || "layout";
    if (
      !node.__easyuseAnimaRegionalLayoutScheduled
      || regionalLayoutReasonPriority(reason) >= regionalLayoutReasonPriority(currentReason)
    ) {
      node.__easyuseAnimaRegionalLayoutReason = reason;
    }
    if (node.__easyuseAnimaRegionalLayoutScheduled) {
      return;
    }
    node.__easyuseAnimaRegionalLayoutScheduled = true;
    scheduleRegionalNodeFrame(node, "layout", () => {
      node.__easyuseAnimaRegionalLayoutScheduled = false;
      const layoutReason = node.__easyuseAnimaRegionalLayoutReason || reason;
      node.__easyuseAnimaRegionalLayoutReason = null;
      applyRegionalLayout(node, layoutReason);
    });
  }

  return {
    applyRegionalLayout,
    regionalEditorMinimumHeight,
    regionalEditorWidgetHeight,
    regionalTextareas,
    scheduleRegionalFieldHighlights,
    scheduleRegionalLayout,
    updateRegionalEditorWidth,
  };
}

export {
  REGIONAL_NODE_DEFAULT_WIDTH,
  REGIONAL_NODE_MIN_WIDTH,
  createRegionalLayout,
};
