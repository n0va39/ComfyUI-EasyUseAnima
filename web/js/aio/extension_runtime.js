// @ts-check

const INPUT_PROTOTYPE_HOOK_MARKER = "__easyuseAnimaAioInputHooksInstalled";
const GENERATOR_PROTOTYPE_HOOK_MARKER = "__easyuseAnimaAioGeneratorHooksInstalled";
const EXTENSION_SETUP_HOST_MARKER = "__easyuseAnimaAioExtensionSetupInstalled";

function graphNodes(graph) {
  if (Array.isArray(graph?.nodes)) {
    return graph.nodes;
  }
  if (Array.isArray(graph?._nodes)) {
    return graph._nodes;
  }
  return Object.values(graph?._nodes_by_id || {});
}

/**
 * List generator nodes reachable from the current root graph through attached
 * ComfyUI SubgraphNode.subgraph definitions. Shared or cyclic graph references
 * and repeated node objects are visited once per refresh.
 */
export function aioListAttachedGeneratorNodes(rootGraph, isGeneratorNode) {
  const result = [];
  const pendingGraphs = [rootGraph];
  const visitedGraphs = new Set();
  const visitedNodes = new Set();
  for (let index = 0; index < pendingGraphs.length; index += 1) {
    const graph = pendingGraphs[index];
    if (!graph || visitedGraphs.has(graph)) {
      continue;
    }
    visitedGraphs.add(graph);
    for (const node of graphNodes(graph)) {
      if (!node) {
        continue;
      }
      if (node.subgraph && !visitedGraphs.has(node.subgraph)) {
        pendingGraphs.push(node.subgraph);
      }
      if (visitedNodes.has(node) || !isGeneratorNode(node)) {
        continue;
      }
      visitedNodes.add(node);
      result.push(node);
    }
  }
  return result;
}

function extensionSetupState(api) {
  const existing = api[EXTENSION_SETUP_HOST_MARKER];
  if (
    existing
    && typeof existing === "object"
    && existing.completedSteps instanceof Set
  ) {
    return existing;
  }
  if (existing === true) {
    return null;
  }
  const state = {
    completedSteps: new Set(),
    inProgress: false,
    complete: false,
  };
  api[EXTENSION_SETUP_HOST_MARKER] = state;
  return state;
}

function runExtensionSetupStep(state, step, install) {
  if (state.completedSteps.has(step)) {
    return;
  }
  install();
  state.completedSteps.add(step);
}

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
      installSeedRuntime,
      disposeSeedRuntime,
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
      hookSeedNode,
      disposeSeedNode,
    },
  } = dependencies;

  function hookNode(node, nodeData) {
    if (nodeData.name === INPUT_NODE_TYPE) {
      hookInputNode(node);
    } else if (nodeData.name === GENERATOR_NODE_TYPE) {
      hookGeneratorNode(node);
      hookSeedNode(node);
    }
  }

  return {
    dispose: () => disposeSeedRuntime(),
    async setup() {
      const setupState = extensionSetupState(api);
      if (!setupState || setupState.inProgress) {
        return;
      }
      if (setupState.complete) {
        return;
      }
      setupState.inProgress = true;
      try {
        runExtensionSetupStep(setupState, "style", () => ensureStyle());
        runExtensionSetupStep(setupState, "wheel-forwarder", () => {
          installWheelForwarder();
        });
        runExtensionSetupStep(setupState, "locale-watch", () => {
          watchLocale(refreshPanels);
        });
        runExtensionSetupStep(setupState, "preview-listener", () => {
          api.addEventListener(GENERATOR_PREVIEW_EVENT, handlePreviewEvent);
        });
        runExtensionSetupStep(setupState, "progress-listener", () => {
          api.addEventListener("progress", handleProgressEvent);
        });
        runExtensionSetupStep(setupState, "progress-state-listener", () => {
          api.addEventListener("progress_state", handleProgressStateEvent);
        });
        runExtensionSetupStep(setupState, "denoise-preview-listener", () => {
          api.addEventListener("b_preview_with_metadata", handleDenoisePreviewEvent, true);
        });
        runExtensionSetupStep(setupState, "executing-listener", () => {
          api.addEventListener("executing", handleExecutingEvent);
        });
        runExtensionSetupStep(setupState, "execution-error-listener", () => {
          api.addEventListener("execution_error", clearDenoisePreviews);
        });
        runExtensionSetupStep(setupState, "execution-interrupted-listener", () => {
          api.addEventListener("execution_interrupted", clearDenoisePreviews);
        });
        runExtensionSetupStep(setupState, "execution-success-listener", () => {
          api.addEventListener("execution_success", clearDenoisePreviews);
        });
        runExtensionSetupStep(setupState, "seed-runtime", () => {
          installSeedRuntime();
        });
        runExtensionSetupStep(setupState, "sampler-options-load", () => {
          loadSamplerOptions().then(refreshPanels);
        });
        runExtensionSetupStep(setupState, "user-profiles-load", () => {
          loadUserProfiles()
            .then(refreshPanels)
            .catch(warnUserProfiles);
        });
        setupState.complete = true;
      } finally {
        setupState.inProgress = false;
      }
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
      if (nodeData.name !== INPUT_NODE_TYPE && nodeData.name !== GENERATOR_NODE_TYPE) {
        return;
      }
      const prototypeHookMarker = nodeData.name === GENERATOR_NODE_TYPE
        ? GENERATOR_PROTOTYPE_HOOK_MARKER
        : INPUT_PROTOTYPE_HOOK_MARKER;
      if (Object.prototype.hasOwnProperty.call(nodeType.prototype, prototypeHookMarker)) {
        return;
      }
      const patchedProperties = ["onNodeCreated", "onConfigure"];
      if (nodeData.name === GENERATOR_NODE_TYPE) {
        patchedProperties.push(
          "hideOutputImages",
          "onSerialize",
          "onExecuted",
          "onResize",
          "onRemoved",
        );
      }
      const originalDescriptors = new Map(patchedProperties.map((property) => [
        property,
        Object.getOwnPropertyDescriptor(nodeType.prototype, property),
      ]));
      try {
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
            disposeSeedNode(this, "reconfigure");
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
                disposeSeedNode(this, "remove");
              } finally {
                try {
                  disposePanel(this);
                } finally {
                  disposeNativePreviewLifecycle(this);
                }
              }
            }
          };
        }
        Object.defineProperty(nodeType.prototype, prototypeHookMarker, { value: true });
      } catch (error) {
        for (const property of [...patchedProperties].reverse()) {
          try {
            const descriptor = originalDescriptors.get(property);
            if (descriptor) {
              Object.defineProperty(nodeType.prototype, property, descriptor);
            } else {
              delete nodeType.prototype[property];
            }
          } catch {
            // Preserve the original installation error if rollback is blocked.
          }
        }
        throw error;
      }
    },
  };
}
