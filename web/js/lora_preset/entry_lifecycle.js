// @ts-check

const LORA_PRESET_ENTRY_OWNER = Symbol.for(
  "easyuse-anima.lora-preset.entry-lifecycle-owner",
);

/**
 * Owns the LoRA Preset extension hooks that live outside an individual node.
 * Node/profile mutation, save synchronization, menu, preview, and canvas
 * behavior remain supplied by their existing owners.
 *
 * @param {{
 *   app: any,
 *   hostDocument: any,
 *   hostWindow: any,
 *   nodeTypeName: string,
 *   canvasWidgets: any,
 *   clientPointToCanvas: (event: any) => number[],
 *   profileCount: (node: any) => number,
 *   saveSync: {install: () => boolean, dispose: () => boolean},
 *   loadSettings: () => Promise<any>,
 *   refreshNodes: () => void,
 *   watchLocale: (callback: () => void) => (() => void),
 *   applySettings: (settings: any) => void,
 *   previewLifecycle: {hidePreview: () => void},
 *   menuLifecycle: {install: () => any, dispose?: () => any},
 *   nodeRuntime: {beforeRegisterNodeDef: (nodeType: any, nodeData: any) => any},
 *   now?: () => number,
 * }} dependencies
 */
export function createLoraPresetEntryLifecycle(dependencies) {
  const {
    app,
    hostDocument,
    hostWindow,
    nodeTypeName,
    canvasWidgets,
    clientPointToCanvas,
    profileCount,
    saveSync,
    loadSettings,
    refreshNodes,
    watchLocale,
    applySettings,
    previewLifecycle,
    menuLifecycle,
    nodeRuntime,
    now = () => performance.now(),
  } = dependencies;
  const listeners = [];
  let activeProfileWheelTarget = null;
  let installed = false;
  let disposeLocaleWatch = null;

  function isActive() {
    return installed && hostWindow[LORA_PRESET_ENTRY_OWNER] === lifecycle;
  }

  /**
   * @param {any} target
   * @param {string} type
   * @param {(event: any) => any} listener
   * @param {boolean | AddEventListenerOptions} [options]
   */
  function listen(target, type, listener, options = false) {
    target.addEventListener(type, listener, options);
    listeners.push([target, type, listener, options]);
  }

  function getActiveProfileWheelTarget() {
    return activeProfileWheelTarget;
  }

  function setActiveProfileWheelTarget(target) {
    activeProfileWheelTarget = target;
  }

  /**
   * Node 2.0 renders each custom widget into its own DOM canvas. The profile
   * bar's draw coordinates are local to that canvas, so the legacy graph-to-
   * client conversion cannot identify its wheel area after a Vue canvas zoom.
   *
   * @param {any} event
   * @param {any} node
   * @param {any} bar
   */
  function pointInNode2ProfileList(event, node, bar) {
    if (!Array.isArray(bar?.listArea) || !Array.isArray(node?.widgets)) {
      return false;
    }
    const eventPath = event?.composedPath?.() || [];
    const targetCanvas = eventPath.find((target) => target?.tagName === "CANVAS")
      || event?.target?.closest?.("canvas");
    const nodeElement = targetCanvas?.closest?.(".lg-node[data-node-id]");
    const nodeId = nodeElement?.dataset?.nodeId
      ?? nodeElement?.getAttribute?.("data-node-id");
    if (!targetCanvas || !nodeElement || String(nodeId) !== String(node.id)) {
      return false;
    }

    const customWidgets = node.widgets.filter((widget) => widget?.type === "custom");
    const profileWidgetIndex = customWidgets.indexOf(bar);
    const widgetCanvases = nodeElement.querySelectorAll?.(".lg-node-widget canvas") || [];
    const profileCanvas = widgetCanvases[profileWidgetIndex];
    if (profileWidgetIndex < 0 || profileCanvas !== targetCanvas) {
      return false;
    }

    const rect = profileCanvas.getBoundingClientRect?.();
    const computedSize = bar.computeSize?.(node.size?.[0], node);
    const logicalWidth = Number(profileCanvas.clientWidth)
      || Number(node.size?.[0])
      || Number(computedSize?.[0]);
    const logicalHeight = Number(profileCanvas.clientHeight)
      || Number(computedSize?.[1]);
    if (
      !rect
      || !(Number(rect.width) > 0)
      || !(Number(rect.height) > 0)
      || !(logicalWidth > 0)
      || !(logicalHeight > 0)
    ) {
      return false;
    }
    const localPos = [
      (Number(event?.clientX || 0) - Number(rect.left || 0)) * logicalWidth / Number(rect.width),
      (Number(event?.clientY || 0) - Number(rect.top || 0)) * logicalHeight / Number(rect.height),
    ];
    return canvasWidgets.pointInArea(localPos, bar.listArea);
  }

  function pointInProfileList(event, node, bar, clientPos) {
    return canvasWidgets.pointInArea(clientPos, bar?.listClientArea)
      || pointInNode2ProfileList(event, node, bar);
  }

  function scrollProfileListFromWheel(event) {
    const clientPos = [Number(event?.clientX || 0), Number(event?.clientY || 0)];
    if (
      activeProfileWheelTarget?.node?.comfyClass === nodeTypeName
      && activeProfileWheelTarget?.widget
      && (now() - activeProfileWheelTarget.time) < 30000
      && (app.graph?._nodes || []).includes(activeProfileWheelTarget.node)
    ) {
      if (!pointInProfileList(
        event,
        activeProfileWheelTarget.node,
        activeProfileWheelTarget.widget,
        clientPos,
      )) {
        activeProfileWheelTarget = null;
      } else {
        activeProfileWheelTarget.time = now();
        const handled = activeProfileWheelTarget.widget.scrollByWheel(
          event.deltaY,
          activeProfileWheelTarget.node,
        );
        if (handled) {
          event.preventDefault?.();
          event.stopPropagation?.();
          return true;
        }
      }
    }

    const nodesByZ = [...(app.graph?._nodes || [])].reverse();
    for (const node of nodesByZ) {
      const bar = node?.comfyClass === nodeTypeName ? node.__easyuseAnimaProfileBar : null;
      if (!bar || !pointInProfileList(event, node, bar, clientPos)) {
        continue;
      }
      const handled = bar.scrollByWheel(event.deltaY, node);
      if (handled) {
        activeProfileWheelTarget = {
          node,
          widget: bar,
          time: now(),
        };
        event.preventDefault?.();
        event.stopPropagation?.();
        return true;
      }
    }

    const canvas = app.canvas?.canvas;
    const rect = canvas?.getBoundingClientRect?.();
    if (
      !canvas
      || !rect
      || Number(event?.clientX || 0) < rect.left
      || Number(event?.clientX || 0) > rect.right
      || Number(event?.clientY || 0) < rect.top
      || Number(event?.clientY || 0) > rect.bottom
    ) {
      return false;
    }
    const graphPoint = clientPointToCanvas(event);
    for (const node of nodesByZ) {
      if (node?.comfyClass !== nodeTypeName || !node.__easyuseAnimaProfileBar || !Array.isArray(node.pos)) {
        continue;
      }
      const localPos = [
        Number(graphPoint[0] || 0) - Number(node.pos[0] || 0),
        Number(graphPoint[1] || 0) - Number(node.pos[1] || 0),
      ];
      const bar = node.__easyuseAnimaProfileBar;
      if (!canvasWidgets.pointInArea(localPos, bar.listArea)) {
        continue;
      }
      const count = profileCount(node);
      const maxOffset = Math.max(0, count - canvasWidgets.profileVisibleRows);
      if (maxOffset <= 0) {
        return false;
      }
      const direction = Number(event.deltaY || 0) > 0 ? 1 : -1;
      const nextOffset = Math.max(0, Math.min(maxOffset, (bar.scrollOffset || 0) + direction));
      if (nextOffset !== bar.scrollOffset) {
        bar.scrollOffset = nextOffset;
        node.setDirtyCanvas?.(true, true);
      }
      event.preventDefault?.();
      event.stopPropagation?.();
      return true;
    }
    return false;
  }

  function dispose() {
    if (!installed) {
      if (hostWindow[LORA_PRESET_ENTRY_OWNER] === lifecycle) {
        delete hostWindow[LORA_PRESET_ENTRY_OWNER];
      }
      return saveSync.dispose();
    }
    installed = false;
    activeProfileWheelTarget = null;
    for (const [target, type, listener, options] of listeners) {
      target.removeEventListener(type, listener, options);
    }
    listeners.length = 0;
    let cleanupError = null;
    const runCleanup = (callback) => {
      try {
        callback();
      } catch (error) {
        cleanupError ||= error;
      }
    };
    runCleanup(() => disposeLocaleWatch?.());
    disposeLocaleWatch = null;
    runCleanup(() => saveSync.dispose());
    runCleanup(() => menuLifecycle.dispose?.());
    runCleanup(() => previewLifecycle.hidePreview());
    if (hostWindow[LORA_PRESET_ENTRY_OWNER] === lifecycle) {
      delete hostWindow[LORA_PRESET_ENTRY_OWNER];
    }
    if (cleanupError) {
      throw cleanupError;
    }
    return true;
  }

  function install() {
    if (isActive()) {
      return false;
    }
    const previousOwner = hostWindow[LORA_PRESET_ENTRY_OWNER];
    if (previousOwner && previousOwner !== lifecycle) {
      previousOwner.dispose?.();
    }
    if (hostWindow[LORA_PRESET_ENTRY_OWNER]) {
      return false;
    }

    installed = true;
    hostWindow[LORA_PRESET_ENTRY_OWNER] = lifecycle;
    try {
      disposeLocaleWatch = watchLocale(() => {
        if (isActive()) {
          refreshNodes();
        }
      });
      listen(hostWindow, "easyuse-anima-settings-updated", (event) => {
        if (!isActive()) {
          return;
        }
        applySettings(event.detail || {});
        refreshNodes();
      });
      listen(hostDocument, "pointerdown", previewLifecycle.hidePreview, true);
      listen(hostDocument, "wheel", scrollProfileListFromWheel, { capture: true, passive: false });
      menuLifecycle.install();
    } catch (error) {
      try {
        dispose();
      } catch {
        // Preserve the installation error after releasing every owned hook.
      }
      throw error;
    }
    return true;
  }

  function initialize() {
    saveSync.install();
    if (!install()) {
      return false;
    }
    loadSettings().then(() => {
      if (isActive()) {
        refreshNodes();
      }
    });
    return true;
  }

  function setup() {
    saveSync.install();
  }

  async function beforeRegisterNodeDef(nodeType, nodeData) {
    nodeRuntime.beforeRegisterNodeDef(nodeType, nodeData);
  }

  const lifecycle = {
    beforeRegisterNodeDef,
    dispose,
    extension: {
      name: "EasyUseAnima.LoraPreset",
      init: initialize,
      setup,
      beforeRegisterNodeDef,
    },
    getActiveProfileWheelTarget,
    initialize,
    install,
    isActive,
    scrollProfileListFromWheel,
    setActiveProfileWheelTarget,
    setup,
  };
  return lifecycle;
}
