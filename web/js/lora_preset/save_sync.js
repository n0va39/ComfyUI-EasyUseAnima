// @ts-check

import {
  createHostHookRuntimeLifecycle,
  registerHostHookCallbacks,
} from "../lifecycle/host_hook_registry.js";

const LORA_PRESET_SAVE_SYNC_OWNER = Symbol.for(
  "easyuse-anima.lora-preset.save-sync",
);
const LORA_PRESET_SAVE_SYNC_RUNTIME_OWNER = Symbol.for(
  "easyuse-anima.lora-preset.save-sync-runtime-owner",
);

/** Installs the graph-save and queue-preparation synchronization hooks. */
export function createLoraPresetSaveSync({
  app,
  nodeTypeName,
  saveCurrentProfile,
  getGraphPrototype = () => globalThis.LGraph?.prototype || app.graph?.constructor?.prototype,
}) {
  const globalHookLifecycle = createHostHookRuntimeLifecycle(
    app,
    LORA_PRESET_SAVE_SYNC_RUNTIME_OWNER,
  );
  let leaseInstalled = false;
  let serializeHost;

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

  function install() {
    const graphPrototype = getGraphPrototype();
    const replace = leaseInstalled
      && graphPrototype != null
      && graphPrototype !== serializeHost;
    const installed = globalHookLifecycle.install(
      "save-sync",
      () => registerHostHookCallbacks({
        owner: LORA_PRESET_SAVE_SYNC_OWNER,
        serializeHost: graphPrototype,
        queueHost: app,
        beforeSerialize: ({ thisArg }) => syncAllNodes(thisArg),
        beforeQueue: () => syncAllNodes(),
      }),
      { replace },
    );
    if (installed) {
      leaseInstalled = true;
      serializeHost = graphPrototype;
    }
    return installed;
  }

  function dispose() {
    leaseInstalled = false;
    serializeHost = undefined;
    return globalHookLifecycle.dispose();
  }

  return { dispose, install, syncNode, syncAllNodes };
}
