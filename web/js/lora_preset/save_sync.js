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

  function syncAllNodes() {
    for (const node of app.graph?._nodes || []) {
      syncNode(node);
    }
  }

  function install() {
    const graphPrototype = getGraphPrototype();
    if (graphPrototype?.serialize && !graphPrototype.serialize.__easyuseAnimaLoraPresetWrapped) {
      const serialize = graphPrototype.serialize;
      graphPrototype.serialize = function () {
        syncAllNodes();
        return serialize.apply(this, arguments);
      };
      graphPrototype.serialize.__easyuseAnimaLoraPresetWrapped = true;
    }
    if (app.queuePrompt && !app.queuePrompt.__easyuseAnimaLoraPresetWrapped) {
      const queuePrompt = app.queuePrompt;
      app.queuePrompt = function () {
        syncAllNodes();
        return queuePrompt.apply(this, arguments);
      };
      app.queuePrompt.__easyuseAnimaLoraPresetWrapped = true;
    }
  }

  return { install, syncNode, syncAllNodes };
}
