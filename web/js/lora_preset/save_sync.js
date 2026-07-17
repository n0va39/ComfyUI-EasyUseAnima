/** Installs the graph-save and queue-preparation synchronization hooks. */
export function createLoraPresetSaveSync({
  app,
  nodeTypeName,
  saveCurrentProfile,
  getGraphPrototype = () => globalThis.LGraph?.prototype || app.graph?.constructor?.prototype,
}) {
  function syncNode(node) {
    if (node?.comfyClass === nodeTypeName) {
      saveCurrentProfile(node);
    }
  }

  function syncAllNodes(graph = app.graph) {
    for (const node of graph?._nodes || []) {
      syncNode(node);
    }
  }

  const serializeInstall = { target: null, wrapper: null };
  const queueInstall = { target: null, wrapper: null };

  function installWrapper(state, target, methodName, syncBeforeCall) {
    const current = target?.[methodName];
    if (typeof current !== "function" || (state.target === target && current === state.wrapper)) {
      return;
    }
    const wrapper = function () {
      // A host extension can wrap our previous function between installs.  Only
      // the outermost current wrapper owns synchronization, so reinstalling
      // composes with that extension without double-saving profiles.
      if (state.target === target && state.wrapper === wrapper) {
        syncBeforeCall(this);
      }
      return current.apply(this, arguments);
    };
    wrapper.__easyuseAnimaLoraPresetWrapped = true;
    state.target = target;
    state.wrapper = wrapper;
    target[methodName] = wrapper;
  }

  function install() {
    const graphPrototype = getGraphPrototype();
    installWrapper(serializeInstall, graphPrototype, "serialize", (graph) => syncAllNodes(graph));
    installWrapper(queueInstall, app, "queuePrompt", () => syncAllNodes());
  }

  return { install, syncNode, syncAllNodes };
}
