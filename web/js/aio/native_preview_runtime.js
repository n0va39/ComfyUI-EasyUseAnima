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

  function markGeneratorNativeLivePreviewHidden(node) {
    if (!node || typeof document === "undefined") {
      return;
    }
    for (const root of generatorVueNodeRoots(node)) {
      root.classList.add(GENERATOR_VUE_NODE_CLASS);
      hideGeneratorNativeLivePreviewElements(root);
    }
  }

  let generatorNativePreviewStoresPromise = null;
  let generatorDialogServiceAssetUrlPromise = null;

  async function generatorDialogServiceAssetUrl() {
    if (!generatorDialogServiceAssetUrlPromise) {
      generatorDialogServiceAssetUrlPromise = (async () => {
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
    }
    return generatorDialogServiceAssetUrlPromise;
  }

  async function generatorNativePreviewStores() {
    if (!generatorNativePreviewStoresPromise) {
      generatorNativePreviewStoresPromise = (async () => {
        try {
          const [nodeOutputStoreModule, workflowStoreModule] = await loadDirectStoreModules();
          if (nodeOutputStoreModule?.useNodeOutputStore && workflowStoreModule?.useWorkflowStore) {
            return {
              useNodeOutputStore: nodeOutputStoreModule.useNodeOutputStore,
              useWorkflowStore: workflowStoreModule.useWorkflowStore,
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
          return {
            useNodeOutputStore: module?.useNodeOutputStore || module?.cn || module?.L,
            useWorkflowStore: module?.useWorkflowStore || module?.M,
          };
        } catch {
          return null;
        }
      })();
    }
    return generatorNativePreviewStoresPromise;
  }

  async function purgeGeneratorNativeLivePreviewStore(node, detail = null) {
    try {
      if (!node) {
        return;
      }
      const ids = generatorPreviewLocatorCandidates(node, detail);
      if (!ids.length) {
        return;
      }
      const legacyPreviewImages = getLegacyPreviewImages();
      if (legacyPreviewImages && typeof legacyPreviewImages === "object") {
        for (const id of ids) {
          aioDeletePreviewStoreEntry(legacyPreviewImages, id);
        }
      }

      const stores = await generatorNativePreviewStores();
      const outputStore = stores?.useNodeOutputStore?.();
      if (!outputStore) {
        return;
      }
      const workflowStore = stores?.useWorkflowStore?.();
      const locators = new Set(ids);
      for (const id of ids) {
        const leaf = String(id).split(":").pop();
        if (!leaf) {
          continue;
        }
        locators.add(leaf);
        const locator = workflowStore?.nodeIdToNodeLocatorId?.(leaf);
        if (locator) {
          locators.add(locator);
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

  function scheduleGeneratorNativeLivePreviewPurge(node, detail = null) {
    void purgeGeneratorNativeLivePreviewStore(node, detail);
    requestAnimationFrame(() => {
      void purgeGeneratorNativeLivePreviewStore(node, detail);
    });
    setTimeout(() => {
      void purgeGeneratorNativeLivePreviewStore(node, detail);
    }, 80);
    setTimeout(() => {
      void purgeGeneratorNativeLivePreviewStore(node, detail);
    }, 240);
  }

  function stopGeneratorNativeLivePreviewObserver(node) {
    const observers = node?.__easyuseAnimaNativeLivePreviewObservers;
    if (!observers) {
      return;
    }
    for (const observer of observers.values()) {
      observer.disconnect();
    }
    observers.clear();
  }

  function ensureGeneratorNativeLivePreviewObserver(node) {
    if (!node || !MutationObserver) {
      return;
    }
    const observers = node.__easyuseAnimaNativeLivePreviewObservers || new Map();
    node.__easyuseAnimaNativeLivePreviewObservers = observers;
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
      const observer = new MutationObserver(() => markGeneratorNativeLivePreviewHidden(node));
      observer.observe(root, { childList: true, subtree: true });
      observers.set(root, observer);
    }
    clearTimeout(node.__easyuseAnimaNativeLivePreviewObserverStopTimer);
    node.__easyuseAnimaNativeLivePreviewObserverStopTimer = setTimeout(() => {
      stopGeneratorNativeLivePreviewObserver(node);
    }, 5000);
  }

  function scheduleGeneratorNativeLivePreviewHidden(node) {
    markGeneratorNativeLivePreviewHidden(node);
    ensureGeneratorNativeLivePreviewObserver(node);
    if (node.__easyuseAnimaNativeLivePreviewHideScheduled) {
      return;
    }
    node.__easyuseAnimaNativeLivePreviewHideScheduled = true;
    const hide = () => markGeneratorNativeLivePreviewHidden(node);
    requestAnimationFrame(hide);
    setTimeout(hide, 80);
    setTimeout(() => {
      node.__easyuseAnimaNativeLivePreviewHideScheduled = false;
      hide();
    }, 240);
  }

  function suppressGeneratorDefaultPreview(node, options = {}) {
    return aioSuppressDefaultPreview(node, {
      markDirty: options.markDirty,
      markNodeDirty,
    });
  }

  function scheduleGeneratorDefaultPreviewSuppression(node, options = {}) {
    const shouldPurgeStore = options.purgeStore !== false;
    const purgeDetail = options.purgeDetail || null;
    suppressGeneratorDefaultPreview(node);
    if (shouldPurgeStore) {
      scheduleGeneratorNativeLivePreviewPurge(node, purgeDetail);
    }
    scheduleGeneratorNativeLivePreviewHidden(node);
    if (node.__easyuseAnimaDefaultPreviewSuppressionScheduled) {
      return;
    }
    node.__easyuseAnimaDefaultPreviewSuppressionScheduled = true;
    const suppress = () => {
      suppressGeneratorDefaultPreview(node);
      if (shouldPurgeStore) {
        scheduleGeneratorNativeLivePreviewPurge(node, purgeDetail);
      }
      markGeneratorNativeLivePreviewHidden(node);
    };
    requestAnimationFrame(suppress);
    setTimeout(suppress, 120);
    setTimeout(() => {
      node.__easyuseAnimaDefaultPreviewSuppressionScheduled = false;
      suppress();
    }, 360);
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
    if (!node || node.type !== GENERATOR_NODE_TYPE) {
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
      if (node?.type === GENERATOR_NODE_TYPE) {
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
    if (node?.type === GENERATOR_NODE_TYPE) {
      clearGeneratorDenoisePreview(node, true);
      scheduleGeneratorDefaultPreviewSuppression(node);
    }
  }

  function clearGeneratorDenoisePreviews() {
    clearGeneratorPreviewProgress();
    for (const node of listGeneratorNodes()) {
      if (node?.type === GENERATOR_NODE_TYPE) {
        clearGeneratorDenoisePreview(node, true);
        scheduleGeneratorDefaultPreviewSuppression(node);
      }
    }
  }

  return {
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
