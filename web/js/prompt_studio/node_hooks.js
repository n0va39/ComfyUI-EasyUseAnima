// @ts-check

import {
  ADVANCED_NODE_TYPE,
  ADVANCED_V2_NODE_TYPE,
  EXTEND_NODE_TYPE,
  NODE_TYPE,
  WILDCARD_NODE_TYPE,
} from "./constants.js";

function isAdvancedNodeName(name) {
  return name === ADVANCED_NODE_TYPE || name === ADVANCED_V2_NODE_TYPE;
}

function isAdvancedNode(node) {
  return isAdvancedNodeName(node?.type) || isAdvancedNodeName(node?.comfyClass);
}

function isWildcardNode(node) {
  return node?.type === WILDCARD_NODE_TYPE || node?.comfyClass === WILDCARD_NODE_TYPE;
}

function isExtendNode(node) {
  return node?.type === EXTEND_NODE_TYPE || node?.comfyClass === EXTEND_NODE_TYPE;
}

function isPromptStudioNodeName(name) {
  return name === NODE_TYPE
    || isAdvancedNodeName(name)
    || name === EXTEND_NODE_TYPE
    || name === WILDCARD_NODE_TYPE;
}

function registerPromptStudioNodeHooks(nodeType, nodeData, hooks) {
  if (!isPromptStudioNodeName(nodeData?.name)) {
    return false;
  }
  if (nodeType.prototype.__easyuseAnimaPromptStudioWrapped) {
    return false;
  }
  nodeType.prototype.__easyuseAnimaPromptStudioWrapped = true;

  const nodeName = nodeData.name;
  const isAdvanced = isAdvancedNodeName(nodeName);
  const isWildcard = nodeName === WILDCARD_NODE_TYPE;

  const onNodeCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function () {
    onNodeCreated?.apply(this, arguments);
    if (isAdvanced) {
      hooks.scheduleHookAdvancedNode(this);
    } else if (!isWildcard) {
      hooks.hookStudioNode(this);
    }
  };

  const onConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function (serialized) {
    const result = onConfigure?.apply(this, arguments);
    if (isAdvanced) {
      hooks.captureAdvancedConfigure(this, serialized);
      hooks.attachAdvancedQueueSeedNode?.(this);
      hooks.scheduleHookAdvancedNode(this);
    } else if (!isWildcard) {
      hooks.hookStudioNode(this);
    }
    return result;
  };

  const onResize = nodeType.prototype.onResize;
  nodeType.prototype.onResize = function () {
    const result = onResize?.apply(this, arguments);
    if (this.__easyuseAnimaHandlingResize || this.__easyuseAnimaApplyingLayout) {
      return result;
    }
    this.__easyuseAnimaHandlingResize = true;
    try {
      if (isAdvanced) {
        hooks.updateAdvancedEditorWidth(this);
        hooks.scheduleAdvancedResizeFinalize(this);
        return result;
      }
      if (isWildcard) {
        return result;
      }
      if (hooks.isExtendNode(this)) {
        hooks.applyExtendSlotVisibility(this);
        hooks.renderExtendSlotControls(this);
      }
      hooks.rebalanceStudioInputHeights(this);
      if (hooks.isExtendNode(this)) {
        hooks.layoutExtendPromptWidgets(this);
      }
      return result;
    } finally {
      this.__easyuseAnimaHandlingResize = false;
    }
  };

  const onRemoved = nodeType.prototype.onRemoved;
  nodeType.prototype.onRemoved = function () {
    let result;
    let didThrow = false;
    let originalError;
    try {
      result = onRemoved?.apply(this, arguments);
    } catch (error) {
      didThrow = true;
      originalError = error;
    }
    if (isAdvanced) {
      try {
        hooks.disconnectAdvancedEditorWidthObserver?.(this);
      } catch {
        // Cleanup failures must not replace the node's original lifecycle result.
      }
      try {
        hooks.detachAdvancedQueueSeedNode?.(this);
      } catch {
        // State cleanup remains isolated from other node removal handlers.
      }
    }
    if (didThrow) {
      throw originalError;
    }
    return result;
  };

  const onConnectionsChange = nodeType.prototype.onConnectionsChange;
  nodeType.prototype.onConnectionsChange = function () {
    const result = onConnectionsChange?.apply(this, arguments);
    if (isAdvanced && !this.__easyuseAnimaHandlingConnectionsChange) {
      this.__easyuseAnimaHandlingConnectionsChange = true;
      requestAnimationFrame(() => {
        try {
          hooks.removeAdvancedInternalInputSockets(this);
          hooks.pruneDisconnectedAdvancedFieldInputValues(this);
          hooks.renderAdvancedEditor(this);
        } finally {
          this.__easyuseAnimaHandlingConnectionsChange = false;
        }
      });
    }
    return result;
  };

  const onSerialize = nodeType.prototype.onSerialize;
  nodeType.prototype.onSerialize = function (serialized) {
    const result = onSerialize?.apply(this, arguments);
    if (isAdvanced) {
      hooks.removeAdvancedInternalInputSockets(this);
      hooks.syncAdvancedValues(this, serialized);
    } else if (!isWildcard) {
      hooks.syncStudioValues(this, serialized);
    }
    return result;
  };

  const onExecuted = nodeType.prototype.onExecuted;
  nodeType.prototype.onExecuted = function (message) {
    onExecuted?.apply(this, arguments);
    if (isAdvanced) {
      hooks.applyAdvancedExecutedInputs(this, message);
    } else if (isWildcard) {
      hooks.applyWildcardExecutedInputs(this, message);
    } else {
      hooks.applyExecutedInputs(this, message);
    }
  };

  return true;
}

function syncAdvancedNodes(app, syncAdvancedValues) {
  const nodes = app?.graph?._nodes || [];
  for (const node of nodes) {
    if (isAdvancedNode(node)) {
      syncAdvancedValues(node);
    }
  }
}

function installAdvancedSaveSync(app, syncAllAdvancedNodes) {
  const graphProto = globalThis.LGraph?.prototype || app?.graph?.constructor?.prototype;
  if (graphProto?.serialize && !graphProto.serialize.__easyuseAnimaAdvancedWrapped) {
    const serialize = graphProto.serialize;
    graphProto.serialize = function () {
      syncAllAdvancedNodes();
      return serialize.apply(this, arguments);
    };
    graphProto.serialize.__easyuseAnimaAdvancedWrapped = true;
  }

  if (app?.queuePrompt && !app.queuePrompt.__easyuseAnimaAdvancedWrapped) {
    const queuePrompt = app.queuePrompt;
    app.queuePrompt = function () {
      syncAllAdvancedNodes();
      return queuePrompt.apply(this, arguments);
    };
    app.queuePrompt.__easyuseAnimaAdvancedWrapped = true;
  }
}

export {
  isAdvancedNode,
  isAdvancedNodeName,
  isExtendNode,
  isPromptStudioNodeName,
  isWildcardNode,
  installAdvancedSaveSync,
  registerPromptStudioNodeHooks,
  syncAdvancedNodes,
};
