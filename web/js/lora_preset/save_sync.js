/** Installs the graph-save and queue-preparation synchronization hooks. */
const installStates = new WeakMap();

function installStateFor(target, methodName) {
  let states = installStates.get(target);
  if (!states) {
    states = new Map();
    installStates.set(target, states);
  }
  let state = states.get(methodName);
  if (!state) {
    state = { wrapper: null, syncBeforeCall: null };
    states.set(methodName, state);
  }
  return state;
}

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

  function installWrapper(target, methodName, syncBeforeCall) {
    const current = target?.[methodName];
    if (typeof current !== "function") {
      return;
    }
    const state = installStateFor(target, methodName);
    state.syncBeforeCall = syncBeforeCall;
    if (current === state.wrapper) {
      return;
    }
    const wrapper = function () {
      // A host extension can wrap our previous function between installs.  Only
      // the outermost current wrapper owns synchronization.  The target-level
      // state also survives a new lifecycle instance after another extension
      // hides our marker by wrapping the previous function.
      if (state.wrapper === wrapper) {
        state.syncBeforeCall(this);
      }
      return current.apply(this, arguments);
    };
    wrapper.__easyuseAnimaLoraPresetWrapped = true;
    state.wrapper = wrapper;
    target[methodName] = wrapper;
  }

  function install() {
    const graphPrototype = getGraphPrototype();
    installWrapper(graphPrototype, "serialize", (graph) => syncAllNodes(graph));
    installWrapper(app, "queuePrompt", () => syncAllNodes());
  }

  return { install, syncNode, syncAllNodes };
}
