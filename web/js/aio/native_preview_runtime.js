// @ts-check

/**
 * Own the native-preview store purge, DOM suppression, observer scheduling,
 * and preview API event lifecycle. Extension registration and custom preview
 * rendering remain adapters owned by the entry module.
 *
 * @param {{
 *   environment: {
 *     document: any,
 *     window: any,
 *     MutationObserver: any,
 *     requestAnimationFrame: (callback: any) => any,
 *     cancelAnimationFrame: (frame: any) => void,
 *     setTimeout: (callback: any, delay: number) => any,
 *     clearTimeout: (timer: any) => void,
 *   },
 *   constants: {
 *     generatorNodeType: string,
 *     generatorVueNodeClass: string,
 *   },
 *   storeAdapter: {
 *     getLegacyPreviewImages: () => any,
 *     loadDirectStoreModules: () => Promise<any[]>,
 *     fetchFrontendHtml: () => Promise<string>,
 *     importAssetModule: (url: string) => Promise<any>,
 *   },
 *   previewCore: {
 *     deleteStoreEntry: (container: any, locator: any) => void,
 *     eventDetail: (event: any) => any,
 *     images: (message: any) => any[],
 *     nodeIdsFromDetail: (detail: any) => string[],
 *     suppressDefaultPreview: (node: any, options?: Record<string, any>) => boolean,
 *   },
 *   nodeAdapter: {
 *     getGraph: () => any,
 *     listGeneratorNodes: () => any[],
 *     addPreviewImages: (node: any, images: any[], runId?: string, options?: Record<string, any>) => void,
 *     clearDenoisePreview: (node: any, update?: boolean) => void,
 *     setDenoisePreview: (node: any, blob: any, detail?: Record<string, any>) => void,
 *     markDirty: (node: any) => void,
 *   },
 *   progressAdapter: {
 *     remember: (detail: any) => void,
 *     rememberState: (detail: any) => void,
 *     clear: () => void,
 *   },
 * }} dependencies
 */
export function aioCreateNativePreviewRuntime(dependencies) {
  const {
    document,
    window,
    MutationObserver,
    requestAnimationFrame,
    cancelAnimationFrame,
    setTimeout,
    clearTimeout,
  } = dependencies.environment;
  const {
    generatorNodeType: GENERATOR_NODE_TYPE,
    generatorVueNodeClass: GENERATOR_VUE_NODE_CLASS,
  } = dependencies.constants;
  const {
    getLegacyPreviewImages,
    loadDirectStoreModules,
    fetchFrontendHtml,
    importAssetModule,
  } = dependencies.storeAdapter;
  const {
    deleteStoreEntry: aioDeletePreviewStoreEntry,
    eventDetail: aioPreviewEventDetail,
    images: aioPreviewImages,
    nodeIdsFromDetail: aioPreviewNodeIdsFromDetail,
    suppressDefaultPreview: aioSuppressDefaultPreview,
  } = dependencies.previewCore;
  const {
    getGraph,
    listGeneratorNodes,
    addPreviewImages: addGeneratorPreviewImagesToNode,
    clearDenoisePreview: clearGeneratorDenoisePreview,
    setDenoisePreview: setGeneratorDenoisePreview,
    markDirty: markNodeDirty,
  } = dependencies.nodeAdapter;
  const {
    remember: rememberGeneratorProgress,
    rememberState: rememberGeneratorProgressState,
    clear: clearGeneratorPreviewProgress,
  } = dependencies.progressAdapter;

  const generatorNativePreviewLifecycleStates = new WeakMap();
  const disposedGeneratorNativePreviewNodes = new WeakSet();

  function createGeneratorNativePreviewLifecycleState() {
    return {
      frames: new Map(),
      timers: new Map(),
      observers: new Map(),
      purgeBatchActive: false,
      purgeIds: new Set(),
      purgeStorePromise: null,
      hideBatchActive: false,
      suppressionBatchActive: false,
      suppressionShouldPurge: false,
      suppressionPurgeIds: new Set(),
      suppressionStorePromise: null,
    };
  }

  function activateGeneratorNativePreviewLifecycle(node) {
    if (!node) {
      return false;
    }
    disposedGeneratorNativePreviewNodes.delete(node);
    if (!generatorNativePreviewLifecycleStates.has(node)) {
      generatorNativePreviewLifecycleStates.set(
        node,
        createGeneratorNativePreviewLifecycleState(),
      );
    }
    return true;
  }

  function isGeneratorNativePreviewDisposed(node) {
    return !node || disposedGeneratorNativePreviewNodes.has(node);
  }

  function generatorNativePreviewLifecycleState(node) {
    if (isGeneratorNativePreviewDisposed(node)) {
      return null;
    }
    activateGeneratorNativePreviewLifecycle(node);
    return generatorNativePreviewLifecycleStates.get(node) || null;
  }

  function isGeneratorNativePreviewLifecycleCurrent(node, state) {
    return (
      !!state
      && !isGeneratorNativePreviewDisposed(node)
      && generatorNativePreviewLifecycleStates.get(node) === state
    );
  }

  function scheduleGeneratorNativePreviewFrame(node, key, callback) {
    const state = generatorNativePreviewLifecycleState(node);
    if (!state) {
      return null;
    }
    const existing = state.frames.get(key);
    if (existing != null) {
      return existing;
    }
    let frame = null;
    frame = requestAnimationFrame(() => {
      if (state.frames.get(key) !== frame) {
        return;
      }
      state.frames.delete(key);
      if (isGeneratorNativePreviewLifecycleCurrent(node, state)) {
        callback(state);
      }
    });
    state.frames.set(key, frame);
    return frame;
  }

  function scheduleGeneratorNativePreviewTimer(node, key, delay, callback, options = {}) {
    const state = generatorNativePreviewLifecycleState(node);
    if (!state) {
      return null;
    }
    const existing = state.timers.get(key);
    if (existing != null) {
      if (options.replace !== true) {
        return existing;
      }
      clearTimeout(existing);
      state.timers.delete(key);
    }
    let timer = null;
    timer = setTimeout(() => {
      if (state.timers.get(key) !== timer) {
        return;
      }
      state.timers.delete(key);
      if (isGeneratorNativePreviewLifecycleCurrent(node, state)) {
        callback(state);
      }
    }, delay);
    state.timers.set(key, timer);
    return timer;
  }

  function disconnectGeneratorNativePreviewObservers(state) {
    for (const observer of state?.observers?.values?.() || []) {
      observer.disconnect();
    }
    state?.observers?.clear?.();
  }

  function disposeGeneratorNativePreviewLifecycle(node) {
    if (!node || disposedGeneratorNativePreviewNodes.has(node)) {
      return false;
    }
    disposedGeneratorNativePreviewNodes.add(node);
    const state = generatorNativePreviewLifecycleStates.get(node);
    if (state) {
      for (const frame of state.frames.values()) {
        cancelAnimationFrame(frame);
      }
      state.frames.clear();
      for (const timer of state.timers.values()) {
        clearTimeout(timer);
      }
      state.timers.clear();
      disconnectGeneratorNativePreviewObservers(state);
      state.purgeIds.clear();
      state.suppressionPurgeIds.clear();
      generatorNativePreviewLifecycleStates.delete(node);
    }
    clearGeneratorDenoisePreview(node, false);
    return true;
  }

  function cssEscape(value) {
    if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
      return CSS.escape(value);
    }
    return String(value).replace(/["\\]/g, "\\$&");
  }

  function generatorVueNodeRoots(node) {
    const roots = new Set();
    if (!node || typeof document === "undefined") {
      return roots;
    }
    const panel = node?.__easyuseAnimaGeneratorPanelEl;
    if (panel) {
      const panelNodeRoot = panel.closest?.(".lg-node");
      const panelDataRoot = panel.closest?.("[data-node-id]");
      if (panelNodeRoot) {
        roots.add(panelNodeRoot);
      }
      if (panelDataRoot) {
        roots.add(panelDataRoot);
      }
    }
    const id = node?.id;
    if (id == null) {
      return roots;
    }
    const textId = String(id);
    const escapedId = cssEscape(textId);
    const selectors = [
      `[data-node-id="${escapedId}"]`,
      `[data-node-id$=":${escapedId}"]`,
    ];
    for (const selector of selectors) {
      for (const element of document.querySelectorAll(selector)) {
        roots.add(element);
      }
    }
    if (!roots.size) {
      for (const element of document.querySelectorAll(".easyuse-anima-aio-node-panel")) {
        const root = element.closest?.(".lg-node") || element.closest?.("[data-node-id]");
        if (generatorNativePreviewRootMatchesNode(root, node)) {
          roots.add(root);
        }
      }
    }
    if (!roots.size) {
      for (const element of document.querySelectorAll(".text-node-component-header-text")) {
        const root = element.closest?.("[data-node-id]");
        if (generatorNativePreviewRootMatchesNode(root, node)) {
          roots.add(root);
        }
      }
    }
    return roots;
  }

  function generatorNativePreviewRootMatchesNode(root, node) {
    if (!root || !node) {
      return false;
    }
    const panel = node.__easyuseAnimaGeneratorPanelEl;
    if (panel && root.contains?.(panel)) {
      return true;
    }
    const id = node.id == null ? "" : String(node.id);
    const rootId = String(root.getAttribute?.("data-node-id") || "");
    if (!id || !rootId) {
      return false;
    }
    if (rootId === id) {
      return true;
    }
    const parts = rootId.split(":");
    return parts[parts.length - 1] === id;
  }

  function addGeneratorPreviewLocatorCandidate(ids, value) {
    const text = String(value ?? "").trim();
    if (!text) {
      return;
    }
    ids.add(text);
    const leaf = text.split(":").pop();
    if (leaf) {
      ids.add(leaf);
    }
  }

  function generatorPreviewLocatorCandidates(node, detail = null) {
    const ids = new Set();
    if (node?.id != null) {
      addGeneratorPreviewLocatorCandidate(ids, node.id);
    }
    for (const id of aioPreviewNodeIdsFromDetail(detail)) {
      addGeneratorPreviewLocatorCandidate(ids, id);
    }
    for (const root of generatorVueNodeRoots(node)) {
      addGeneratorPreviewLocatorCandidate(ids, root.getAttribute?.("data-node-id"));
    }
    return [...ids].filter(Boolean);
  }

  function hideGeneratorNativeLivePreviewElement(element) {
    if (!element) {
      return;
    }
    element.classList?.add("easyuse-anima-aio-native-live-preview-hidden");
    element.setAttribute?.("aria-hidden", "true");
    element.style?.setProperty?.("display", "none", "important");
  }

  function isGeneratorNativeDimensionLabel(element) {
    const text = String(element?.textContent || "").trim();
    return /^\d+\s*[x×]\s*\d+$/i.test(text) || /calculating dimensions/i.test(text);
  }

  function hideGeneratorComfyOutputPreviewElements(root) {
    const contentRoots = root.matches?.(".lg-node-content")
      ? [root, ...root.querySelectorAll(".lg-node-content")]
      : root.querySelectorAll(".lg-node-content");
    for (const content of contentRoots) {
      if (content.querySelector?.(".easyuse-anima-aio-node-panel")) {
        continue;
      }
      if (
        content.querySelector?.('[data-testid="main-image"]')
        || content.querySelector?.(".text-node-component-header-text")
        || content.textContent?.match?.(/\b\d+\s*[x×]\s*\d+\b/i)
      ) {
        hideGeneratorNativeLivePreviewElement(content);
      }
    }
    for (const image of root.querySelectorAll('[data-testid="main-image"]')) {
      const content = image.closest?.(".lg-node-content");
      if (content && !content.querySelector?.(".easyuse-anima-aio-node-panel")) {
        hideGeneratorNativeLivePreviewElement(content);
        continue;
      }
      hideGeneratorNativeLivePreviewElement(image);
      const previewRoot = image.closest?.(".flex-auto, .relative, .overflow-hidden");
      if (previewRoot && !previewRoot.querySelector?.(".easyuse-anima-aio-node-panel")) {
        hideGeneratorNativeLivePreviewElement(previewRoot);
      }
    }
  }

  function hideGeneratorNativeLivePreviewElements(root) {
    if (!root?.querySelectorAll) {
      return;
    }
    hideGeneratorComfyOutputPreviewElements(root);
    for (const image of root.querySelectorAll("img.pointer-events-none.object-contain")) {
      if (image.closest?.(".easyuse-anima-aio-node-panel")) {
        continue;
      }
      hideGeneratorNativeLivePreviewElement(image);
    }
    for (const element of root.querySelectorAll(".text-node-component-header-text, div, span")) {
      if (element.closest?.(".easyuse-anima-aio-node-panel")) {
        continue;
      }
      const shouldHide = element.classList?.contains("text-node-component-header-text")
        || (!element.children?.length && isGeneratorNativeDimensionLabel(element));
      if (!shouldHide) {
        continue;
      }
      hideGeneratorNativeLivePreviewElement(element);
      const parent = element.parentElement;
      if (
        parent
        && !parent.querySelector?.(".easyuse-anima-aio-node-panel")
        && parent.querySelector?.("img.pointer-events-none.object-contain")
      ) {
        hideGeneratorNativeLivePreviewElement(parent);
      }
    }
  }

  function hideGeneratorNativeLivePreviewRoot(root) {
    root.classList?.add?.(GENERATOR_VUE_NODE_CLASS);
    hideGeneratorNativeLivePreviewElements(root);
  }

  function markGeneratorNativeLivePreviewHidden(node) {
    if (isGeneratorNativePreviewDisposed(node) || typeof document === "undefined") {
      return;
    }
    for (const root of generatorVueNodeRoots(node)) {
      hideGeneratorNativeLivePreviewRoot(root);
    }
  }

  let generatorNativePreviewStoresPromise = null;
  let generatorDialogServiceAssetUrlPromise = null;

  function generatorDialogServiceAssetUrl() {
    if (!generatorDialogServiceAssetUrlPromise) {
      const attempt = (async () => {
        if (typeof document !== "undefined") {
          const elements = document.querySelectorAll("link[href], script[src]");
          for (const element of elements) {
            const value = element.getAttribute("href") || element.getAttribute("src") || "";
            if (/\/?assets\/dialogService-[^/]+\.js(?:$|\?)/.test(value)) {
              return new URL(value, window.location.href).href;
            }
          }
        }
        const html = await fetchFrontendHtml();
        const match = html.match(/(?:\.\/)?assets\/dialogService-[^"'<>]+\.js/);
        return match ? new URL(match[0], window.location.href).href : "";
      })().catch(() => "");
      generatorDialogServiceAssetUrlPromise = attempt;
      void attempt.then((url) => {
        if (!url && generatorDialogServiceAssetUrlPromise === attempt) {
          generatorDialogServiceAssetUrlPromise = null;
        }
      });
    }
    return generatorDialogServiceAssetUrlPromise;
  }

  function generatorNativePreviewStores() {
    if (!generatorNativePreviewStoresPromise) {
      const attempt = (async () => {
        try {
          const [nodeOutputStoreModule, workflowStoreModule] = await loadDirectStoreModules();
          const useNodeOutputStore = nodeOutputStoreModule?.useNodeOutputStore;
          const useWorkflowStore = workflowStoreModule?.useWorkflowStore;
          if (typeof useNodeOutputStore === "function") {
            return {
              useNodeOutputStore,
              useWorkflowStore: typeof useWorkflowStore === "function"
                ? useWorkflowStore
                : null,
            };
          }
        } catch {
          // Packaged ComfyUI frontend builds bundle these stores into hashed assets.
        }

        const url = await generatorDialogServiceAssetUrl();
        if (!url) {
          return null;
        }
        try {
          const module = await importAssetModule(url);
          const useNodeOutputStore = [
            module?.useNodeOutputStore,
            module?.cn,
            module?.L,
          ].find((candidate) => typeof candidate === "function") || null;
          const useWorkflowStore = [
            module?.useWorkflowStore,
            module?.M,
          ].find((candidate) => typeof candidate === "function") || null;
          const stores = {
            useNodeOutputStore,
            useWorkflowStore: typeof useWorkflowStore === "function"
              ? useWorkflowStore
              : null,
          };
          if (typeof stores.useNodeOutputStore === "function") {
            return stores;
          }
          return null;
        } catch {
          return null;
        }
      })().catch(() => null);
      generatorNativePreviewStoresPromise = attempt;
      void attempt.then((stores) => {
        if (!stores && generatorNativePreviewStoresPromise === attempt) {
          generatorNativePreviewStoresPromise = null;
        }
      });
    }
    return generatorNativePreviewStoresPromise;
  }

  async function purgeGeneratorNativeLivePreviewStore(node, ids, storesPromise, lifecycleState) {
    try {
      if (!isGeneratorNativePreviewLifecycleCurrent(node, lifecycleState)) {
        return;
      }
      const purgeIds = [...new Set(ids || [])].filter(Boolean);
      if (!purgeIds.length) {
        return;
      }
      const legacyPreviewImages = getLegacyPreviewImages();
      if (legacyPreviewImages && typeof legacyPreviewImages === "object") {
        for (const id of purgeIds) {
          aioDeletePreviewStoreEntry(legacyPreviewImages, id);
        }
      }

      const stores = await storesPromise;
      if (!isGeneratorNativePreviewLifecycleCurrent(node, lifecycleState)) {
        return;
      }
      const outputStore = stores?.useNodeOutputStore?.();
      if (!outputStore) {
        return;
      }
      let workflowStore = null;
      try {
        workflowStore = stores?.useWorkflowStore?.() ?? null;
      } catch {
        // Workflow locator support is optional; raw output locators must still be purged.
      }
      const locators = new Set(purgeIds);
      for (const id of purgeIds) {
        const leaf = String(id).split(":").pop();
        if (!leaf) {
          continue;
        }
        locators.add(leaf);
        try {
          const locator = workflowStore?.nodeIdToNodeLocatorId?.(leaf);
          if (locator) {
            locators.add(locator);
          }
        } catch {
          // Keep best-effort workflow mapping isolated from raw output-store cleanup.
        }
      }
      for (const locator of locators) {
        outputStore.revokePreviewsByLocatorId?.(locator);
        aioDeletePreviewStoreEntry(outputStore.nodePreviewImages, locator);
      }
    } catch {
      // Native preview store access is version-dependent; CSS/DOM fallback remains scoped to this node.
    }
  }

  function addGeneratorNativePreviewPurgeIds(target, node, detail = null) {
    const ids = generatorPreviewLocatorCandidates(node, detail);
    for (const id of ids) {
      target.add(id);
    }
    return ids;
  }

  function scheduleGeneratorNativeLivePreviewPurge(node, detail = null) {
    const state = generatorNativePreviewLifecycleState(node);
    if (!state) {
      return;
    }
    const requestIds = addGeneratorNativePreviewPurgeIds(state.purgeIds, node, detail);
    if (!requestIds.length) {
      return;
    }
    if (!state.purgeStorePromise) {
      state.purgeStorePromise = generatorNativePreviewStores();
    }
    void purgeGeneratorNativeLivePreviewStore(
      node,
      requestIds,
      state.purgeStorePromise,
      state,
    );
    if (!state.purgeBatchActive) {
      state.purgeBatchActive = true;
      scheduleGeneratorNativePreviewFrame(node, "purge", (current) => {
        addGeneratorNativePreviewPurgeIds(current.purgeIds, node);
        void purgeGeneratorNativeLivePreviewStore(
          node,
          [...current.purgeIds],
          current.purgeStorePromise,
          current,
        );
      });
    }
    scheduleGeneratorNativePreviewTimer(node, "purge-80", 80, (current) => {
      addGeneratorNativePreviewPurgeIds(current.purgeIds, node);
      void purgeGeneratorNativeLivePreviewStore(
        node,
        [...current.purgeIds],
        current.purgeStorePromise,
        current,
      );
    }, { replace: true });
    scheduleGeneratorNativePreviewTimer(node, "purge-240", 240, (current) => {
      addGeneratorNativePreviewPurgeIds(current.purgeIds, node);
      const pendingIds = [...current.purgeIds];
      const storePromise = current.purgeStorePromise;
      current.purgeBatchActive = false;
      current.purgeIds.clear();
      current.purgeStorePromise = null;
      void purgeGeneratorNativeLivePreviewStore(node, pendingIds, storePromise, current);
    }, { replace: true });
  }

  function stopGeneratorNativeLivePreviewObserver(node) {
    const state = generatorNativePreviewLifecycleStates.get(node);
    if (!state) {
      return;
    }
    disconnectGeneratorNativePreviewObservers(state);
  }

  function ensureGeneratorNativeLivePreviewObserver(node) {
    const state = generatorNativePreviewLifecycleState(node);
    if (!state || !MutationObserver) {
      return;
    }
    const { observers } = state;
    for (const [root, observer] of observers) {
      if (!root?.isConnected) {
        observer.disconnect();
        observers.delete(root);
      }
    }
    for (const root of generatorVueNodeRoots(node)) {
      if (!root || observers.has(root)) {
        continue;
      }
      const observer = new MutationObserver(() => {
        if (!isGeneratorNativePreviewLifecycleCurrent(node, state)) {
          return;
        }
        if (!root?.isConnected) {
          return;
        }
        if (state.frames.has(root)) {
          return;
        }
        hideGeneratorNativeLivePreviewRoot(root);
        scheduleGeneratorNativePreviewFrame(node, root, () => {
          if (root?.isConnected) {
            hideGeneratorNativeLivePreviewRoot(root);
          }
        });
      });
      observer.observe(root, { childList: true, subtree: true });
      observers.set(root, observer);
    }
    scheduleGeneratorNativePreviewTimer(node, "observer-stop", 5000, () => {
      stopGeneratorNativeLivePreviewObserver(node);
    }, { replace: true });
  }

  function scheduleGeneratorNativeLivePreviewHidden(node) {
    const state = generatorNativePreviewLifecycleState(node);
    if (!state) {
      return;
    }
    markGeneratorNativeLivePreviewHidden(node);
    ensureGeneratorNativeLivePreviewObserver(node);
    if (state.hideBatchActive) {
      return;
    }
    state.hideBatchActive = true;
    const hide = () => markGeneratorNativeLivePreviewHidden(node);
    scheduleGeneratorNativePreviewFrame(node, "hide", hide);
    scheduleGeneratorNativePreviewTimer(node, "hide-80", 80, hide);
    scheduleGeneratorNativePreviewTimer(node, "hide-240", 240, (current) => {
      current.hideBatchActive = false;
      hide();
    });
  }

  function suppressGeneratorDefaultPreview(node, options = {}) {
    if (isGeneratorNativePreviewDisposed(node)) {
      return false;
    }
    return aioSuppressDefaultPreview(node, {
      markDirty: options.markDirty,
      markNodeDirty,
    });
  }

  function scheduleGeneratorDefaultPreviewSuppression(node, options = {}) {
    const state = generatorNativePreviewLifecycleState(node);
    if (!state) {
      return;
    }
    const shouldPurgeStore = options.purgeStore !== false;
    const purgeDetail = options.purgeDetail || null;
    suppressGeneratorDefaultPreview(node);
    if (shouldPurgeStore) {
      addGeneratorNativePreviewPurgeIds(state.suppressionPurgeIds, node, purgeDetail);
      state.suppressionShouldPurge = true;
      scheduleGeneratorNativeLivePreviewPurge(node, purgeDetail);
      state.suppressionStorePromise ||= state.purgeStorePromise;
    }
    scheduleGeneratorNativeLivePreviewHidden(node);
    if (state.suppressionBatchActive) {
      return;
    }
    state.suppressionBatchActive = true;
    const suppress = (current, final = false) => {
      suppressGeneratorDefaultPreview(node);
      if (current.suppressionShouldPurge) {
        addGeneratorNativePreviewPurgeIds(current.suppressionPurgeIds, node);
        const pendingIds = [...current.suppressionPurgeIds];
        const storePromise = current.suppressionStorePromise;
        if (final) {
          current.suppressionShouldPurge = false;
          current.suppressionPurgeIds.clear();
          current.suppressionStorePromise = null;
        }
        void purgeGeneratorNativeLivePreviewStore(
          node,
          pendingIds,
          storePromise,
          current,
        );
      }
      markGeneratorNativeLivePreviewHidden(node);
    };
    scheduleGeneratorNativePreviewFrame(node, "suppress", suppress);
    scheduleGeneratorNativePreviewTimer(node, "suppress-120", 120, suppress);
    scheduleGeneratorNativePreviewTimer(node, "suppress-360", 360, (current) => {
      current.suppressionBatchActive = false;
      suppress(current, true);
    });
  }

  function findGeneratorNodeByQualifiedId(rootGraph, nodeId) {
    if (!rootGraph || nodeId == null) {
      return null;
    }
    const textId = String(nodeId);
    if (!textId.includes(":")) {
      const numericId = Number(textId);
      return rootGraph.getNodeById?.(Number.isFinite(numericId) ? numericId : textId)
        || rootGraph.getNodeById?.(textId)
        || rootGraph._nodes_by_id?.[textId]
        || rootGraph._nodes_by_id?.[numericId]
        || null;
    }
    const parts = textId.split(":");
    let graph = rootGraph;
    for (let index = 0; index < parts.length - 1; index += 1) {
      const parentId = Number(parts[index]);
      if (!Number.isFinite(parentId)) {
        return null;
      }
      const parentNode = graph?.getNodeById?.(parentId) || graph?._nodes_by_id?.[parentId];
      if (!parentNode?.subgraph) {
        return null;
      }
      graph = parentNode.subgraph;
    }
    const leafId = Number(parts[parts.length - 1]);
    if (!Number.isFinite(leafId)) {
      return null;
    }
    return graph?.getNodeById?.(leafId) || graph?._nodes_by_id?.[leafId] || null;
  }

  function handleGeneratorPreviewEvent(event) {
    const detail = aioPreviewEventDetail(event);
    const node = findGeneratorNodeByQualifiedId(getGraph(), detail.node);
    if (!node || node.type !== GENERATOR_NODE_TYPE || isGeneratorNativePreviewDisposed(node)) {
      return;
    }
    scheduleGeneratorNativeLivePreviewPurge(node, detail);
    const images = aioPreviewImages({ easyuse_anima_preview: detail.images });
    scheduleGeneratorDefaultPreviewSuppression(node, { purgeStore: false });
    addGeneratorPreviewImagesToNode(node, images, String(detail.run_id || ""));
  }

  function findGeneratorNodeForDenoisePreview(detail) {
    for (const id of aioPreviewNodeIdsFromDetail(detail)) {
      const node = findGeneratorNodeByQualifiedId(getGraph(), id);
      if (node?.type === GENERATOR_NODE_TYPE && !isGeneratorNativePreviewDisposed(node)) {
        return node;
      }
    }
    return null;
  }

  function handleGeneratorProgressEvent(event) {
    rememberGeneratorProgress(aioPreviewEventDetail(event));
  }

  function handleGeneratorProgressStateEvent(event) {
    rememberGeneratorProgressState(aioPreviewEventDetail(event));
  }

  function handleGeneratorDenoisePreviewEvent(event) {
    const detail = aioPreviewEventDetail(event);
    const node = findGeneratorNodeForDenoisePreview(detail);
    const blob = detail?.blob;
    if (!node || !blob) {
      return;
    }
    event.stopImmediatePropagation?.();
    scheduleGeneratorNativeLivePreviewPurge(node, detail);
    scheduleGeneratorDefaultPreviewSuppression(node, { purgeStore: false });
    setGeneratorDenoisePreview(node, blob, detail);
  }

  function handleGeneratorExecutingEvent(event) {
    const nodeId = aioPreviewEventDetail(event);
    const node = findGeneratorNodeByQualifiedId(getGraph(), nodeId);
    if (node?.type === GENERATOR_NODE_TYPE && !isGeneratorNativePreviewDisposed(node)) {
      clearGeneratorDenoisePreview(node, true);
      scheduleGeneratorDefaultPreviewSuppression(node);
    }
  }

  function clearGeneratorDenoisePreviews() {
    clearGeneratorPreviewProgress();
    for (const node of listGeneratorNodes()) {
      if (node?.type === GENERATOR_NODE_TYPE && !isGeneratorNativePreviewDisposed(node)) {
        clearGeneratorDenoisePreview(node, true);
        scheduleGeneratorDefaultPreviewSuppression(node);
      }
    }
  }

  return {
    activateGeneratorNativePreviewLifecycle,
    disposeGeneratorNativePreviewLifecycle,
    markGeneratorNativeLivePreviewHidden,
    suppressGeneratorDefaultPreview,
    scheduleGeneratorDefaultPreviewSuppression,
    handleGeneratorPreviewEvent,
    handleGeneratorProgressEvent,
    handleGeneratorProgressStateEvent,
    handleGeneratorDenoisePreviewEvent,
    handleGeneratorExecutingEvent,
    clearGeneratorDenoisePreviews,
  };
}
