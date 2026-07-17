// @ts-check

import {
  REGIONAL_CONDITIONING_NODE_TYPE,
  REGIONAL_NODE_TYPE,
} from "./constants.js";
import {
  activateRegionalNodeLifecycle,
  disposeRegionalNodeLifecycle,
  scheduleRegionalNodeFrame,
  setRegionalNodeCleanup,
} from "./lifecycle.js";
import {
  REGIONAL_NODE_DEFAULT_WIDTH,
  REGIONAL_NODE_MIN_WIDTH,
} from "./layout.js";
import {
  promptStudioQueueSeedBridge,
} from "../queue_seed_bridge.js";

/**
 * @param {any} nodeType
 * @param {(node: any, serialized?: any) => void} repairWidgets
 */
function registerRegionalConditioningNodeHooks(nodeType, repairWidgets) {
  if (nodeType.prototype.__easyuseAnimaRegionalConditioningWrapped) {
    return false;
  }
  nodeType.prototype.__easyuseAnimaRegionalConditioningWrapped = true;

  const onNodeCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function () {
    const result = onNodeCreated?.apply(this, arguments);
    repairWidgets(this);
    return result;
  };

  const onConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function (serialized) {
    repairWidgets(this, serialized);
    const result = onConfigure?.apply(this, arguments);
    repairWidgets(this, serialized);
    return result;
  };

  const onSerialize = nodeType.prototype.onSerialize;
  nodeType.prototype.onSerialize = function (serialized) {
    const result = onSerialize?.apply(this, arguments);
    repairWidgets(this, serialized);
    return result;
  };
  return true;
}

/**
 * @param {any} app
 * @param {() => void} syncAllRegionalNodes
 * @param {any} [graph]
 */
function installRegionalSaveSync(app, syncAllRegionalNodes, graph = null) {
  const graphProto = globalThis.LGraph?.prototype || graph?.constructor?.prototype;
  if (graphProto?.serialize && !graphProto.serialize.__easyuseAnimaRegionalWrapped) {
    const serialize = graphProto.serialize;
    const wrappedSerialize = function () {
      syncAllRegionalNodes();
      return serialize.apply(this, arguments);
    };
    wrappedSerialize.__easyuseAnimaRegionalWrapped = true;
    graphProto.serialize = wrappedSerialize;
  }
  if (app.queuePrompt && !app.queuePrompt.__easyuseAnimaRegionalWrapped) {
    const queuePrompt = app.queuePrompt;
    const wrappedQueuePrompt = function () {
      syncAllRegionalNodes();
      return queuePrompt.apply(this, arguments);
    };
    wrappedQueuePrompt.__easyuseAnimaRegionalWrapped = true;
    app.queuePrompt = wrappedQueuePrompt;
  }
}

/**
 * @param {any} nodeType
 * @param {{
 *   attachQueueSeedNode?: (node: any) => void,
 *   applyRegionalExecutedInputs: (node: any, message: any) => void,
 *   captureRegionalConfigure: (node: any, serialized: any) => void,
 *   disposeRegionalNode: (node: any) => void,
 *   pruneDisconnectedRegionalFieldInputValues: (node: any) => void,
 *   removeRegionalInternalInputSockets: (node: any) => void,
 *   renderRegionalEditor: (node: any) => void,
 *   scheduleHookRegionalNode: (node: any) => void,
 *   scheduleRegionalLayout: (node: any, reason: string) => void,
 *   syncRegionalValues: (node: any, serialized?: any) => void,
 * }} hooks
 */
function registerRegionalNodeHooks(nodeType, hooks) {
  if (nodeType.prototype.__easyuseAnimaRegionalWrapped) {
    return false;
  }
  nodeType.prototype.__easyuseAnimaRegionalWrapped = true;

  const onNodeCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function () {
    const result = onNodeCreated?.apply(this, arguments);
    hooks.scheduleHookRegionalNode(this);
    return result;
  };

  const onConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function (serialized) {
    const result = onConfigure?.apply(this, arguments);
    hooks.captureRegionalConfigure(this, serialized);
    hooks.removeRegionalInternalInputSockets(this);
    hooks.attachQueueSeedNode?.(this);
    hooks.scheduleHookRegionalNode(this);
    return result;
  };

  const onResize = nodeType.prototype.onResize;
  nodeType.prototype.onResize = function () {
    const result = onResize?.apply(this, arguments);
    hooks.scheduleRegionalLayout(this, "resize");
    return result;
  };

  const onConnectionsChange = nodeType.prototype.onConnectionsChange;
  nodeType.prototype.onConnectionsChange = function () {
    const result = onConnectionsChange?.apply(this, arguments);
    if (!this.__easyuseAnimaRegionalHandlingConnectionsChange) {
      this.__easyuseAnimaRegionalHandlingConnectionsChange = true;
      scheduleRegionalNodeFrame(this, "connections-change", () => {
        try {
          hooks.removeRegionalInternalInputSockets(this);
          hooks.pruneDisconnectedRegionalFieldInputValues(this);
          hooks.renderRegionalEditor(this);
        } finally {
          this.__easyuseAnimaRegionalHandlingConnectionsChange = false;
        }
      });
    }
    return result;
  };

  const onSerialize = nodeType.prototype.onSerialize;
  nodeType.prototype.onSerialize = function (serialized) {
    const result = onSerialize?.apply(this, arguments);
    hooks.syncRegionalValues(this, serialized);
    return result;
  };

  const onExecuted = nodeType.prototype.onExecuted;
  nodeType.prototype.onExecuted = function (message) {
    const result = onExecuted?.apply(this, arguments);
    hooks.applyRegionalExecutedInputs(this, message);
    return result;
  };

  const onRemoved = nodeType.prototype.onRemoved;
  nodeType.prototype.onRemoved = function () {
    let result;
    try {
      result = onRemoved?.apply(this, arguments);
    } finally {
      hooks.disposeRegionalNode(this);
    }
    return result;
  };

  return true;
}

/**
 * @param {any} app
 * @param {any} runtime
 * @param {any} layout
 * @param {any} fieldEditor
 * @param {{
 *   ensureRegionalStyle: () => void,
 *   installRegionalAdapter: () => void,
 * }} hooks
 */
function createRegionalExtensionRuntime(app, runtime, layout, fieldEditor, hooks) {
  const queueSeedBridge = promptStudioQueueSeedBridge(app);
  queueSeedBridge.bindRegionalSeedPublisher((node, seed) => {
    if (!runtime.isRegionalNode(node)) {
      return false;
    }
    if (!runtime.setRegionalWidgetValue(node, "wildcard_seed", seed)) {
      throw new Error("Prompt Studio Regional wildcard_seed widget is unavailable.");
    }
    fieldEditor.renderRegionalEditor(node);
    return true;
  });

  /** @param {any} node */
  function cleanupRegionalEditor(node) {
    const editor = node?.__easyuseAnimaRegionalEditorEl;
    if (editor) {
      for (const textarea of editor.querySelectorAll("textarea")) {
        const frame = Number(textarea.__easyuseAnimaHighlightSyncRaf) || 0;
        if (frame) {
          cancelAnimationFrame(frame);
          textarea.__easyuseAnimaHighlightSyncRaf = 0;
        }
        textarea.__easyuseAnimaHighlightOverlay?.remove?.();
        textarea.__easyuseAnimaHighlightOverlay = null;
      }
      if (Array.isArray(globalThis.__easyuseAnimaPendingAutocompleteInputs)) {
        globalThis.__easyuseAnimaPendingAutocompleteInputs =
          globalThis.__easyuseAnimaPendingAutocompleteInputs.filter(
            (entry) => !editor.contains(entry?.input),
          );
      }
      editor.remove?.();
    }
    delete node.__easyuseAnimaRegionalEditorEl;
    delete node.__easyuseAnimaRegionalDomWidget;
    delete node.__easyuseAnimaRegionalWidgetHeight;
    delete node.__easyuseAnimaRegionalLayoutReason;
    node.__easyuseAnimaRegionalApplyingLayout = false;
    node.__easyuseAnimaRegionalHandlingConnectionsChange = false;
    node.__easyuseAnimaRegionalLayoutScheduled = false;
    node.__easyuseAnimaRegionalHookScheduled = false;
  }

  /** @param {any} node */
  function disposeRegionalNode(node) {
    try {
      queueSeedBridge.detachNode(node);
    } catch {
      // Queue state cleanup remains isolated from the Regional DOM lifecycle.
    }
    disposeRegionalNodeLifecycle(node);
    node.__easyuseAnimaRegionalApplyingLayout = false;
    node.__easyuseAnimaRegionalHandlingConnectionsChange = false;
    node.__easyuseAnimaRegionalLayoutScheduled = false;
    node.__easyuseAnimaRegionalHookScheduled = false;
  }

  /** @param {any} node */
  function syncRegionalValues(node, serialized = null) {
    runtime.syncRegionalValues(
      node,
      serialized,
      fieldEditor.collectRegionalEditorFields,
    );
  }

  function syncAllRegionalNodes() {
    for (const node of app.graph?._nodes || []) {
      if (runtime.isRegionalNode(node)) {
        syncRegionalValues(node);
      }
    }
  }

  /** @param {any} [graph] */
  function installSaveSync(graph = null) {
    installRegionalSaveSync(app, syncAllRegionalNodes, graph);
  }

  /** @param {any} node */
  function hookRegionalNode(node) {
    activateRegionalNodeLifecycle(node);
    hooks.ensureRegionalStyle();
    installSaveSync(node.graph);
    runtime.ensureRegionalWidgetValues(node);
    runtime.removeRegionalInternalInputSockets(node);
    runtime.hideRegionalInternalWidgets(node);
    node.serialize_widgets = true;
    node.minWidth = Math.max(Number(node.minWidth) || 0, REGIONAL_NODE_MIN_WIDTH);
    if (Array.isArray(node.size)) {
      const currentWidth = Number(node.size[0]) || 0;
      node.size[0] = currentWidth < REGIONAL_NODE_MIN_WIDTH
        ? REGIONAL_NODE_DEFAULT_WIDTH
        : currentWidth;
    }
    if (!node.__easyuseAnimaRegionalEditorEl) {
      const editor = document.createElement("div");
      editor.className = "easyuse-anima-advanced-editor easyuse-anima-prompt-studio-variant easyuse-anima-regional-editor";
      node.__easyuseAnimaRegionalEditorEl = editor;
      const widget = node.addDOMWidget?.(
        "easyuse_anima_regional_editor",
        "EasyUseAnimaRegionalEditor",
        editor,
        {
          serialize: false,
          hideOnZoom: false,
          getMinHeight: () => layout.regionalEditorMinimumHeight(node),
          getHeight: () => layout.regionalEditorWidgetHeight(node),
        },
      );
      if (widget) {
        node.__easyuseAnimaRegionalDomWidget = widget;
        widget.computeLayoutSize = () => ({
          minHeight: layout.regionalEditorMinimumHeight(node),
          height: layout.regionalEditorWidgetHeight(node),
          minWidth: REGIONAL_NODE_MIN_WIDTH - 18,
        });
      }
      setRegionalNodeCleanup(node, "editor", () => cleanupRegionalEditor(node));
    }
    fieldEditor.renderRegionalEditor(node);
  }

  /** @param {any} node */
  function scheduleHookRegionalNode(node) {
    if (!node || node.__easyuseAnimaRegionalHookScheduled) {
      return;
    }
    node.__easyuseAnimaRegionalHookScheduled = true;
    scheduleRegionalNodeFrame(node, "hook", () => {
      node.__easyuseAnimaRegionalHookScheduled = false;
      hookRegionalNode(node);
    });
  }

  function applyRegionalExecutedInputs(node, message) {
    if (runtime.applyRegionalExecutedInputs(node, message, {
      shouldApplyExecutedSeed: (target, value) => (
        queueSeedBridge.shouldApplyExecutedSeed(target, value)
      ),
    })) {
      fieldEditor.renderRegionalEditor(node);
    }
  }

  return {
    async setup() {
      hooks.installRegionalAdapter();
      installSaveSync();
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
      if (nodeData.name === REGIONAL_CONDITIONING_NODE_TYPE) {
        registerRegionalConditioningNodeHooks(
          nodeType,
          runtime.repairRegionalConditioningWidgets,
        );
        return;
      }
      if (nodeData.name !== REGIONAL_NODE_TYPE) {
        return;
      }
      registerRegionalNodeHooks(nodeType, {
        attachQueueSeedNode: queueSeedBridge.attachNode,
        applyRegionalExecutedInputs,
        captureRegionalConfigure: runtime.captureRegionalConfigure,
        disposeRegionalNode,
        pruneDisconnectedRegionalFieldInputValues:
          runtime.pruneDisconnectedRegionalFieldInputValues,
        removeRegionalInternalInputSockets: runtime.removeRegionalInternalInputSockets,
        renderRegionalEditor: fieldEditor.renderRegionalEditor,
        scheduleHookRegionalNode,
        scheduleRegionalLayout: layout.scheduleRegionalLayout,
        syncRegionalValues,
      });
    },
  };
}

export {
  createRegionalExtensionRuntime,
  installRegionalSaveSync,
  registerRegionalConditioningNodeHooks,
  registerRegionalNodeHooks,
};
