// @ts-check

export function aioCreateExtensionRuntime(dependencies) {
  const {
    api,
    constants: {
      inputNodeType: INPUT_NODE_TYPE,
      generatorNodeType: GENERATOR_NODE_TYPE,
      generatorPreviewEvent: GENERATOR_PREVIEW_EVENT,
    },
    setup: {
      ensureStyle,
      installWheelForwarder,
      installQueuePromptHook,
      watchLocale,
      refreshPanels,
      handlePreviewEvent,
      handleProgressEvent,
      handleProgressStateEvent,
      handleDenoisePreviewEvent,
      handleExecutingEvent,
      clearDenoisePreviews,
      loadSamplerOptions,
      loadUserProfiles,
      warnUserProfiles,
    },
    nodes: {
      suppressDefaultPreview,
      hookInputNode,
      hookGeneratorNode,
      syncSerializedWidgets,
      scheduleDefaultPreviewSuppression,
      updateExecutedStatus,
      scheduleLayout,
      disposePanel,
      disposeNativePreviewLifecycle,
    },
  } = dependencies;

  function hookNode(node, nodeData) {
    if (nodeData.name === INPUT_NODE_TYPE) {
      hookInputNode(node);
    } else if (nodeData.name === GENERATOR_NODE_TYPE) {
      hookGeneratorNode(node);
    }
  }

  return {
    async setup() {
      ensureStyle();
      installWheelForwarder();
      installQueuePromptHook();
      watchLocale(refreshPanels);
      api.addEventListener(GENERATOR_PREVIEW_EVENT, handlePreviewEvent);
      api.addEventListener("progress", handleProgressEvent);
      api.addEventListener("progress_state", handleProgressStateEvent);
      api.addEventListener("b_preview_with_metadata", handleDenoisePreviewEvent, true);
      api.addEventListener("executing", handleExecutingEvent);
      api.addEventListener("execution_error", clearDenoisePreviews);
      api.addEventListener("execution_interrupted", clearDenoisePreviews);
      api.addEventListener("execution_success", clearDenoisePreviews);
      loadSamplerOptions().then(refreshPanels);
      loadUserProfiles()
        .then(refreshPanels)
        .catch(warnUserProfiles);
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
      if (nodeData.name !== INPUT_NODE_TYPE && nodeData.name !== GENERATOR_NODE_TYPE) {
        return;
      }
      if (nodeData.name === GENERATOR_NODE_TYPE) {
        nodeType.prototype.hideOutputImages = true;
      }
      const onNodeCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        if (nodeData.name === GENERATOR_NODE_TYPE) {
          suppressDefaultPreview(this, { markDirty: false });
        }
        const result = onNodeCreated?.apply(this, arguments);
        hookNode(this, nodeData);
        return result;
      };
      const onConfigure = nodeType.prototype.onConfigure;
      nodeType.prototype.onConfigure = function () {
        if (nodeData.name === GENERATOR_NODE_TYPE) {
          suppressDefaultPreview(this, { markDirty: false });
        }
        const result = onConfigure?.apply(this, arguments);
        hookNode(this, nodeData);
        return result;
      };
      if (nodeData.name === GENERATOR_NODE_TYPE) {
        const onSerialize = nodeType.prototype.onSerialize;
        nodeType.prototype.onSerialize = function (serialized) {
          const result = onSerialize?.apply(this, arguments);
          syncSerializedWidgets(this, serialized);
          return result;
        };
        nodeType.prototype.onExecuted = function (message) {
          scheduleDefaultPreviewSuppression(this);
          updateExecutedStatus(this, message);
          scheduleDefaultPreviewSuppression(this, { purgeStore: false });
          return undefined;
        };
        const onResize = nodeType.prototype.onResize;
        nodeType.prototype.onResize = function () {
          const result = onResize?.apply(this, arguments);
          scheduleLayout(this);
          return result;
        };
        const onRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
          try {
            return onRemoved?.apply(this, arguments);
          } finally {
            try {
              disposePanel(this);
            } finally {
              disposeNativePreviewLifecycle(this);
            }
          }
        };
      }
    },
  };
}
