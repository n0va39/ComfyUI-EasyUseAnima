import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createFakeDocument } from "./frontend_support/fake_dom.mjs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

async function flushPromises() {
  for (let index = 0; index < 10; index += 1) {
    await Promise.resolve();
  }
}

function createScheduler() {
  let nextId = 1;
  const frames = [];
  const timers = new Map();
  const cleared = [];
  const canceledFrames = [];
  const staleFrames = [];
  const staleTimers = [];

  return {
    frames,
    timers,
    cleared,
    canceledFrames,
    requestAnimationFrame(callback) {
      const id = nextId++;
      frames.push({ id, callback });
      return id;
    },
    cancelAnimationFrame(id) {
      canceledFrames.push(id);
      const index = frames.findIndex((frame) => frame.id === id);
      if (index >= 0) {
        staleFrames.push(frames[index]);
        frames.splice(index, 1);
      }
    },
    setTimeout(callback, delay) {
      const id = nextId++;
      timers.set(id, { id, callback, delay });
      return id;
    },
    clearTimeout(id) {
      cleared.push(id);
      const timer = timers.get(id);
      if (timer) {
        staleTimers.push(timer);
      }
      timers.delete(id);
    },
    runNextFrame() {
      const frame = frames.shift();
      assert.ok(frame, "missing scheduled animation frame");
      frame.callback();
    },
    runAllFrames() {
      while (frames.length) {
        this.runNextFrame();
      }
    },
    runDelay(delay) {
      const entries = [...timers.values()]
        .filter((entry) => entry.delay === delay)
        .sort((left, right) => left.id - right.id);
      assert.ok(entries.length, `missing timer delay: ${delay}`);
      for (const entry of entries) {
        timers.delete(entry.id);
        entry.callback();
      }
    },
    delays() {
      return [...timers.values()].map(({ delay }) => delay).sort((left, right) => left - right);
    },
    runCanceledCallbacks() {
      const callbacks = [
        ...staleFrames.splice(0).map(({ callback }) => callback),
        ...staleTimers.splice(0).map(({ callback }) => callback),
      ];
      for (const callback of callbacks) {
        callback();
      }
    },
  };
}

function createDeferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function plannedResult(plan, fallback, context) {
  if (!plan?.length) {
    return fallback();
  }
  const value = plan.shift();
  if (value instanceof Error) {
    throw value;
  }
  if (typeof value === "function") {
    return value(context);
  }
  return value;
}

function graphFromNodes(nodes) {
  const byId = new Map(nodes.map((node) => [String(node.id), node]));
  return {
    _nodes_by_id: Object.fromEntries(byId),
    getNodeById(id) {
      return byId.get(String(id)) || null;
    },
  };
}

function adapterChannelSnapshot(calls) {
  return Object.fromEntries(
    Object.entries(calls).map(([name, value]) => [name, Array.isArray(value) ? value.length : value]),
  );
}

function blockDirectNodeIdSelectors(document) {
  const querySelectorAll = document.querySelectorAll.bind(document);
  const blocked = [];
  document.querySelectorAll = (selector) => {
    if (/^\[data-node-id(?:=|\$=)/.test(String(selector))) {
      blocked.push(String(selector));
      return [];
    }
    return querySelectorAll(selector);
  };
  return blocked;
}

const nativePreviewModule = await import(dataModule("../web/js/aio/native_preview_runtime.js"));
const previewCoreModule = await import(dataModule("../web/js/aio/preview.js"));
assert.deepEqual(
  Object.keys(nativePreviewModule),
  ["aioCreateNativePreviewRuntime"],
  "Native preview runtime must expose only its lifecycle factory",
);

const GENERATOR_NODE_TYPE = "EasyUseAnimaAIOGenerator";
const GENERATOR_VUE_NODE_CLASS = "easyuse-anima-aio-hide-native-live-preview";
const NATIVE_HIDDEN_CLASS = "easyuse-anima-aio-native-live-preview-hidden";

function createFixture({
  storeMode = "direct",
  graph = graphFromNodes([]),
  generatorNodes = [],
  suppressResult = true,
  directStorePlan = null,
  frontendHtmlPlan = null,
  assetImportPlan = null,
} = {}) {
  const document = createFakeDocument();
  const scheduler = createScheduler();
  const mutationObservers = [];
  const legacyPreviewImages = new Map();
  const outputPreviewImages = new Map();
  const revokeCalls = [];
  const workflowLocatorCalls = [];
  const outputStore = {
    nodePreviewImages: outputPreviewImages,
    revokePreviewsByLocatorId(locator) {
      revokeCalls.push(String(locator));
    },
  };
  const workflowStore = {
    nodeIdToNodeLocatorId(id) {
      const text = String(id);
      workflowLocatorCalls.push(text);
      return `locator:${text}`;
    },
  };
  const calls = {
    legacyGets: 0,
    directStoreLoads: 0,
    frontendFetches: 0,
    assetImports: [],
    deleteStore: [],
    eventDetails: [],
    images: [],
    nodeIds: [],
    suppress: [],
    addImages: [],
    clearDenoise: [],
    setDenoise: [],
    markDirty: [],
    progress: [],
    progressState: [],
    progressClear: 0,
    graphGets: 0,
    generatorLists: 0,
  };

  class FakeMutationObserver {
    constructor(callback) {
      this.callback = callback;
      this.observeCalls = [];
      this.disconnectCalls = 0;
      mutationObservers.push(this);
    }

    observe(root, options) {
      this.observeCalls.push({ root, options });
    }

    disconnect() {
      this.disconnectCalls += 1;
    }

    trigger() {
      this.callback();
    }
  }

  const runtime = nativePreviewModule.aioCreateNativePreviewRuntime({
    environment: {
      document,
      window: { location: { href: "https://comfy.test/" } },
      MutationObserver: FakeMutationObserver,
      requestAnimationFrame: scheduler.requestAnimationFrame,
      cancelAnimationFrame: scheduler.cancelAnimationFrame,
      setTimeout: scheduler.setTimeout,
      clearTimeout: scheduler.clearTimeout,
    },
    constants: {
      generatorNodeType: GENERATOR_NODE_TYPE,
      generatorVueNodeClass: GENERATOR_VUE_NODE_CLASS,
    },
    storeAdapter: {
      getLegacyPreviewImages() {
        calls.legacyGets += 1;
        return legacyPreviewImages;
      },
      async loadDirectStoreModules() {
        calls.directStoreLoads += 1;
        return plannedResult(
          directStorePlan,
          () => {
            if (storeMode !== "direct") {
              throw new Error("direct stores unavailable");
            }
            return [
              { useNodeOutputStore: () => outputStore },
              { useWorkflowStore: () => workflowStore },
            ];
          },
          { outputStore, workflowStore },
        );
      },
      async fetchFrontendHtml() {
        calls.frontendFetches += 1;
        return plannedResult(
          frontendHtmlPlan,
          () => storeMode === "html-fallback"
            ? '<script src="./assets/dialogService-html.js"></script>'
            : "",
          { outputStore, workflowStore },
        );
      },
      async importAssetModule(url) {
        calls.assetImports.push(url);
        return plannedResult(
          assetImportPlan,
          () => {
            if (storeMode === "hashed" || storeMode === "html-fallback") {
              return {
                cn: () => outputStore,
                M: () => workflowStore,
              };
            }
            throw new Error("hashed store unavailable");
          },
          { outputStore, workflowStore, url },
        );
      },
    },
    previewCore: {
      deleteStoreEntry(container, locator) {
        calls.deleteStore.push({ container, locator: String(locator) });
        previewCoreModule.aioDeletePreviewStoreEntry(container, locator);
      },
      eventDetail(event) {
        const detail = previewCoreModule.aioPreviewEventDetail(event);
        calls.eventDetails.push(detail);
        return detail;
      },
      images(message) {
        const images = previewCoreModule.aioPreviewImages(message);
        calls.images.push(images);
        return images;
      },
      nodeIdsFromDetail(detail) {
        const ids = previewCoreModule.aioPreviewNodeIdsFromDetail(detail);
        calls.nodeIds.push(ids);
        return ids;
      },
      suppressDefaultPreview(node, options) {
        calls.suppress.push({ node, options });
        return suppressResult;
      },
    },
    nodeAdapter: {
      getGraph() {
        calls.graphGets += 1;
        return graph;
      },
      listGeneratorNodes() {
        calls.generatorLists += 1;
        return generatorNodes;
      },
      addPreviewImages(node, images, runId, options) {
        calls.addImages.push({ node, images, runId, options });
      },
      clearDenoisePreview(node, update) {
        calls.clearDenoise.push({ node, update });
      },
      setDenoisePreview(node, blob, detail) {
        calls.setDenoise.push({ node, blob, detail });
      },
      markDirty(node) {
        calls.markDirty.push(node);
      },
    },
    progressAdapter: {
      remember(detail) {
        calls.progress.push(detail);
      },
      rememberState(detail) {
        calls.progressState.push(detail);
      },
      clear() {
        calls.progressClear += 1;
      },
    },
  });

  return {
    runtime,
    document,
    scheduler,
    mutationObservers,
    legacyPreviewImages,
    outputPreviewImages,
    outputStore,
    workflowStore,
    revokeCalls,
    workflowLocatorCalls,
    calls,
  };
}

function appendNodeRoot(document, id, className = "lg-node") {
  const root = document.createElement("div");
  root.className = className;
  root.setAttribute("data-node-id", String(id));
  root.isConnected = true;
  document.body.append(root);
  return root;
}

function assertHidden(element, message) {
  assert.equal(element.classList.contains(NATIVE_HIDDEN_CLASS), true, message);
  assert.equal(element.getAttribute("aria-hidden"), "true", message);
  assert.equal(element.style.getPropertyValue("display"), "none", message);
  assert.equal(element.style.getPropertyPriority("display"), "important", message);
}

async function drainScheduledPreviewWork(fixture) {
  fixture.scheduler.runAllFrames();
  await flushPromises();
  for (const delay of [80, 120, 240, 360]) {
    if (fixture.scheduler.delays().includes(delay)) {
      fixture.scheduler.runDelay(delay);
      await flushPromises();
    }
  }
}

{
  const fixture = createFixture({ suppressResult: "suppressed" });
  assert.equal(fixture.document.createdElements.length, 0, "Factory must not create DOM elements");
  assert.equal(fixture.document.body.children.length, 0, "Factory must not attach DOM elements");
  assert.equal(fixture.calls.legacyGets, 0);
  assert.equal(fixture.calls.directStoreLoads, 0);
  assert.equal(fixture.calls.suppress.length, 0);
  assert.equal(fixture.scheduler.frames.length, 0);
  assert.equal(fixture.scheduler.timers.size, 0);
  assert.equal(fixture.mutationObservers.length, 0);
  assert.deepEqual(
    adapterChannelSnapshot(fixture.calls),
    Object.fromEntries(Object.keys(fixture.calls).map((name) => [name, 0])),
    "Factory construction must not invoke any tracked adapter channel",
  );
  assert.equal(fixture.revokeCalls.length, 0);
  assert.equal(fixture.workflowLocatorCalls.length, 0);
  assert.deepEqual(
    Object.keys(fixture.runtime).sort(),
    [
      "activateGeneratorNativePreviewLifecycle",
      "disposeGeneratorNativePreviewLifecycle",
      "markGeneratorNativeLivePreviewHidden",
      "suppressGeneratorDefaultPreview",
      "scheduleGeneratorDefaultPreviewSuppression",
      "handleGeneratorPreviewEvent",
      "handleGeneratorProgressEvent",
      "handleGeneratorProgressStateEvent",
      "handleGeneratorDenoisePreviewEvent",
      "handleGeneratorExecutingEvent",
      "clearGeneratorDenoisePreviews",
    ].sort(),
    "Runtime facade changed",
  );

  const root = appendNodeRoot(fixture.document, "42");
  const nativeContent = fixture.document.createElement("div");
  nativeContent.className = "lg-node-content";
  const mainImage = fixture.document.createElement("img");
  mainImage.setAttribute("data-testid", "main-image");
  nativeContent.append(mainImage);
  root.append(nativeContent);

  const legacyWrapper = fixture.document.createElement("div");
  const legacyImage = fixture.document.createElement("img");
  legacyImage.className = "pointer-events-none object-contain";
  const dimension = fixture.document.createElement("span");
  dimension.textContent = "1024 x 1536";
  legacyWrapper.append(legacyImage, dimension);
  root.append(legacyWrapper);

  const customContent = fixture.document.createElement("div");
  customContent.className = "lg-node-content";
  const panel = fixture.document.createElement("div");
  panel.className = "easyuse-anima-aio-node-panel";
  const panelImage = fixture.document.createElement("img");
  panelImage.className = "pointer-events-none object-contain";
  const panelLabel = fixture.document.createElement("span");
  panelLabel.className = "text-node-component-header-text";
  panel.append(panelImage, panelLabel);
  customContent.append(panel);
  root.append(customContent);

  const qualifiedRoot = appendNodeRoot(fixture.document, "7:42");
  const qualifiedLabel = fixture.document.createElement("span");
  qualifiedLabel.className = "text-node-component-header-text";
  qualifiedRoot.append(qualifiedLabel);
  const unrelatedRoot = appendNodeRoot(fixture.document, "99");
  const unrelatedImage = fixture.document.createElement("img");
  unrelatedImage.className = "pointer-events-none object-contain";
  unrelatedRoot.append(unrelatedImage);

  const node = { id: 42, __easyuseAnimaGeneratorPanelEl: panel };
  fixture.runtime.markGeneratorNativeLivePreviewHidden(node);
  assert.equal(root.classList.contains(GENERATOR_VUE_NODE_CLASS), true);
  assert.equal(qualifiedRoot.classList.contains(GENERATOR_VUE_NODE_CLASS), true);
  assert.equal(unrelatedRoot.classList.contains(GENERATOR_VUE_NODE_CLASS), false);
  assertHidden(nativeContent, "Node 2.0 native content must be hidden");
  assertHidden(legacyImage, "Legacy native image must be hidden");
  assertHidden(dimension, "Native dimension label must be hidden");
  assertHidden(legacyWrapper, "Native image/dimension wrapper must be hidden");
  assertHidden(qualifiedLabel, "Qualified Node 2.0 label must be hidden");
  for (const element of [customContent, panel, panelImage, panelLabel, unrelatedImage]) {
    assert.equal(
      element.classList.contains(NATIVE_HIDDEN_CLASS),
      false,
      "AiO and unrelated preview elements must remain visible",
    );
  }

  const result = fixture.runtime.suppressGeneratorDefaultPreview(node, { markDirty: false });
  assert.equal(result, "suppressed", "Suppression wrapper must preserve the core return value");
  assert.equal(fixture.calls.suppress.length, 1);
  assert.equal(fixture.calls.suppress[0].node, node);
  assert.equal(fixture.calls.suppress[0].options.markDirty, false);
  assert.equal(typeof fixture.calls.suppress[0].options.markNodeDirty, "function");
  fixture.calls.suppress[0].options.markNodeDirty(node);
  assert.deepEqual(fixture.calls.markDirty, [node]);
}

{
  const fixture = createFixture();
  const blockedSelectors = blockDirectNodeIdSelectors(fixture.document);
  const targetRoot = appendNodeRoot(fixture.document, "42");
  const targetPanel = fixture.document.createElement("div");
  targetPanel.className = "easyuse-anima-aio-node-panel";
  const targetNativeImage = fixture.document.createElement("img");
  targetNativeImage.className = "pointer-events-none object-contain";
  targetRoot.append(targetPanel, targetNativeImage);

  const unrelatedRoot = appendNodeRoot(fixture.document, "99");
  const unrelatedPanel = fixture.document.createElement("div");
  unrelatedPanel.className = "easyuse-anima-aio-node-panel";
  const unrelatedNativeImage = fixture.document.createElement("img");
  unrelatedNativeImage.className = "pointer-events-none object-contain";
  unrelatedRoot.append(unrelatedPanel, unrelatedNativeImage);

  fixture.runtime.markGeneratorNativeLivePreviewHidden({ id: 42 });
  assert.deepEqual(
    blockedSelectors,
    ['[data-node-id="42"]', '[data-node-id$=":42"]'],
    "Panel fallback must run after both direct data-id selectors are blocked",
  );
  assert.equal(targetRoot.classList.contains(GENERATOR_VUE_NODE_CLASS), true);
  assertHidden(targetNativeImage, "Panel fallback must hide only the matching root preview");
  assert.equal(targetPanel.classList.contains(NATIVE_HIDDEN_CLASS), false);
  assert.equal(unrelatedRoot.classList.contains(GENERATOR_VUE_NODE_CLASS), false);
  assert.equal(unrelatedNativeImage.classList.contains(NATIVE_HIDDEN_CLASS), false);
}

{
  const fixture = createFixture();
  const blockedSelectors = blockDirectNodeIdSelectors(fixture.document);
  const targetRoot = appendNodeRoot(fixture.document, "7:42");
  const targetHeader = fixture.document.createElement("span");
  targetHeader.className = "text-node-component-header-text";
  targetRoot.append(targetHeader);
  const unrelatedRoot = appendNodeRoot(fixture.document, "7:99");
  const unrelatedHeader = fixture.document.createElement("span");
  unrelatedHeader.className = "text-node-component-header-text";
  unrelatedRoot.append(unrelatedHeader);

  fixture.runtime.markGeneratorNativeLivePreviewHidden({ id: 42 });
  assert.deepEqual(
    blockedSelectors,
    ['[data-node-id="42"]', '[data-node-id$=":42"]'],
    "Header fallback must run after both direct data-id selectors are blocked",
  );
  assert.equal(targetRoot.classList.contains(GENERATOR_VUE_NODE_CLASS), true);
  assertHidden(targetHeader, "Header fallback must hide the qualified matching root");
  assert.equal(unrelatedRoot.classList.contains(GENERATOR_VUE_NODE_CLASS), false);
  assert.equal(unrelatedHeader.classList.contains(NATIVE_HIDDEN_CLASS), false);
}

{
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const graph = graphFromNodes([node]);
  const fixture = createFixture({ graph, storeMode: "direct" });
  appendNodeRoot(fixture.document, "7:42");
  for (const locator of ["42", "7:42", "8:42", "99", "locator:42", "locator:99", "unrelated"]) {
    fixture.legacyPreviewImages.set(locator, true);
    fixture.outputPreviewImages.set(locator, true);
  }

  fixture.runtime.handleGeneratorPreviewEvent({
    detail: {
      data: {
        node: "42",
        displayNodeId: "8:42",
        realNodeId: "99",
        images: [{ filename: "direct.webp" }],
        run_id: "run-direct",
      },
    },
  });
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1, "Direct store modules must load once");
  assert.equal(fixture.calls.frontendFetches, 0);
  assert.equal(fixture.calls.assetImports.length, 0);
  for (const locator of ["42", "7:42", "8:42", "99"]) {
    assert.equal(fixture.legacyPreviewImages.has(locator), false, `legacy store retained: ${locator}`);
    assert.equal(fixture.outputPreviewImages.has(locator), false, `output store retained: ${locator}`);
  }
  for (const locator of ["locator:42", "locator:99"]) {
    assert.equal(
      fixture.legacyPreviewImages.has(locator),
      true,
      `legacy store must not receive workflow-only locator deletion: ${locator}`,
    );
    assert.equal(fixture.outputPreviewImages.has(locator), false, `output store retained: ${locator}`);
  }
  assert.equal(fixture.legacyPreviewImages.has("unrelated"), true);
  assert.equal(fixture.outputPreviewImages.has("unrelated"), true);
  assert.equal(fixture.revokeCalls.filter((value) => value === "locator:42").length, 1);
  assert.equal(fixture.calls.addImages.length, 1);
  assert.equal(fixture.calls.addImages[0].runId, "run-direct");
  assert.equal(fixture.calls.addImages[0].images[0].filename, "direct.webp");
  assert.equal(fixture.scheduler.frames.length, 3, "Purge, hide, and suppression frames must be scheduled");

  fixture.scheduler.runNextFrame();
  await flushPromises();
  fixture.scheduler.runDelay(80);
  await flushPromises();
  fixture.scheduler.runDelay(240);
  await flushPromises();
  assert.equal(
    fixture.revokeCalls.filter((value) => value === "locator:42").length,
    4,
    "Store purge must run immediately, on RAF, at 80ms, and at 240ms",
  );
  assert.equal(
    fixture.revokeCalls.filter((value) => value === "locator:99").length,
    4,
    "A detail-only locator must reach every immediate and delayed purge",
  );
  assert.equal(
    fixture.workflowLocatorCalls.filter((value) => value === "99").length,
    4,
    "A detail-only node id must be remapped during every purge",
  );
  assert.equal(fixture.calls.directStoreLoads, 1, "Scheduled purges must reuse the store promise");
}

{
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({ graph: graphFromNodes([node]), storeMode: "direct" });
  appendNodeRoot(fixture.document, "42");
  const detailOnlyIds = ["91", "92", "93"];
  for (const [index, realNodeId] of detailOnlyIds.entries()) {
    fixture.runtime.handleGeneratorPreviewEvent({
      detail: {
        data: {
          node: "42",
          realNodeId,
          images: [{ filename: `burst-${index}.webp` }],
          run_id: `burst-${index}`,
        },
      },
    });
  }
  await flushPromises();

  assert.equal(fixture.calls.legacyGets, detailOnlyIds.length, "Every burst request needs its immediate purge");
  assert.equal(fixture.scheduler.frames.length, 3, "Burst requests must share purge, hide, and suppression RAF tails");
  assert.deepEqual(
    fixture.scheduler.delays(),
    [80, 80, 120, 240, 240, 360, 5000],
    "Burst requests must keep one bounded timer set",
  );
  for (const id of detailOnlyIds) {
    assert.equal(fixture.revokeCalls.filter((value) => value === `locator:${id}`).length, 1);
  }

  await drainScheduledPreviewWork(fixture);
  assert.equal(
    fixture.calls.legacyGets,
    detailOnlyIds.length + 3,
    "A burst of N requests must add only one shared RAF/80/240 purge tail",
  );
  assert.equal(fixture.scheduler.frames.length, 0);
  assert.deepEqual(fixture.scheduler.delays(), [5000]);
  for (const id of detailOnlyIds) {
    assert.equal(
      fixture.revokeCalls.filter((value) => value === `locator:${id}`).length,
      4,
      `The shared tail lost a burst locator: ${id}`,
    );
  }

  fixture.runtime.handleGeneratorPreviewEvent({
    detail: {
      data: {
        node: "42",
        realNodeId: "94",
        images: [{ filename: "next-batch.webp" }],
        run_id: "next-batch",
      },
    },
  });
  await flushPromises();
  assert.equal(fixture.calls.legacyGets, detailOnlyIds.length + 4, "A terminal batch must release the next immediate purge");
  assert.equal(fixture.scheduler.frames.length, 3, "A new post-terminal request must own a fresh tail");
  await drainScheduledPreviewWork(fixture);
  assert.equal(fixture.calls.legacyGets, detailOnlyIds.length + 7);
  assert.equal(fixture.revokeCalls.filter((value) => value === "locator:94").length, 4);
  assert.equal(fixture.calls.directStoreLoads, 1, "Purge coalescing must preserve the positive store cache");
}

{
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({ storeMode: "direct" });
  appendNodeRoot(fixture.document, "42");
  fixture.runtime.scheduleGeneratorDefaultPreviewSuppression(node);
  await flushPromises();
  assert.equal(fixture.calls.legacyGets, 1);
  assert.equal(fixture.scheduler.frames.length, 3);
  assert.deepEqual(fixture.scheduler.delays(), [80, 80, 120, 240, 240, 360, 5000]);

  await drainScheduledPreviewWork(fixture);
  assert.equal(
    fixture.calls.legacyGets,
    7,
    "Default suppression may run three direct delayed purges but must not recursively schedule purge waves",
  );
  assert.equal(fixture.revokeCalls.filter((value) => value === "locator:42").length, 7);
  assert.equal(fixture.scheduler.frames.length, 0);
  assert.deepEqual(fixture.scheduler.delays(), [5000]);

  const noPurgeFixture = createFixture({ storeMode: "direct" });
  appendNodeRoot(noPurgeFixture.document, "42");
  noPurgeFixture.runtime.scheduleGeneratorDefaultPreviewSuppression(
    { id: 42 },
    { purgeStore: false },
  );
  await drainScheduledPreviewWork(noPurgeFixture);
  assert.equal(noPurgeFixture.calls.legacyGets, 0);
  assert.equal(noPurgeFixture.calls.directStoreLoads, 0);
  assert.equal(noPurgeFixture.revokeCalls.length, 0, "purgeStore false must survive every delayed callback");
}

{
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({ graph: graphFromNodes([node]), storeMode: "hashed" });
  const script = fixture.document.createElement("script");
  script.setAttribute("src", "/assets/dialogService-hash.js?build=1");
  fixture.document.body.append(script);
  fixture.outputPreviewImages.set("42", true);
  fixture.outputPreviewImages.set("locator:42", true);

  const event = {
    detail: { data: { node: "42", images: [{ filename: "hashed.webp" }], run_id: "hash-a" } },
  };
  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(fixture.calls.frontendFetches, 0, "Visible hashed asset must avoid an HTML fetch");
  assert.deepEqual(
    fixture.calls.assetImports,
    ["https://comfy.test/assets/dialogService-hash.js?build=1"],
  );
  assert.equal(fixture.outputPreviewImages.has("42"), false);
  assert.equal(fixture.outputPreviewImages.has("locator:42"), false);

  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1, "Store resolution must stay promise-cached");
  assert.equal(fixture.calls.assetImports.length, 1, "Hashed module import must stay promise-cached");
}

for (const { label, assetModule, expectWorkflowPurge } of [
  {
    label: "later-callable-aliases",
    assetModule: ({ outputStore, workflowStore }) => ({
      useNodeOutputStore: "not-a-function",
      cn: () => outputStore,
      useWorkflowStore: { invalid: true },
      M: () => workflowStore,
    }),
    expectWorkflowPurge: true,
  },
  {
    label: "workflow-alias-unavailable",
    assetModule: ({ outputStore }) => ({
      useNodeOutputStore: "not-a-function",
      cn: () => outputStore,
      useWorkflowStore: { invalid: true },
      M: "not-a-function",
    }),
    expectWorkflowPurge: false,
  },
]) {
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({
    graph: graphFromNodes([node]),
    storeMode: "none",
    assetImportPlan: [assetModule],
  });
  const script = fixture.document.createElement("script");
  script.setAttribute("src", `/assets/dialogService-${label}.js`);
  fixture.document.body.append(script);
  fixture.outputPreviewImages.set("42", true);
  fixture.outputPreviewImages.set("locator:42", true);

  fixture.runtime.handleGeneratorPreviewEvent({
    detail: { data: { node: "42", images: [{ filename: `${label}.webp` }] } },
  });
  await flushPromises();

  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(fixture.calls.frontendFetches, 0);
  assert.deepEqual(
    fixture.calls.assetImports,
    [`https://comfy.test/assets/dialogService-${label}.js`],
  );
  assert.equal(fixture.outputPreviewImages.has("42"), false);
  assert.equal(
    fixture.outputPreviewImages.has("locator:42"),
    !expectWorkflowPurge,
    `Unexpected workflow-locator purge for ${label}`,
  );
  assert.equal(
    fixture.workflowLocatorCalls.length > 0,
    expectWorkflowPurge,
    `Unexpected workflow provider normalization for ${label}`,
  );
}

for (const label of ["workflow-provider-throws", "workflow-mapper-throws"]) {
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const workflowBoundaryCalls = [];
  const useWorkflowStore = label === "workflow-provider-throws"
    ? () => {
      workflowBoundaryCalls.push("provider");
      throw new Error("optional workflow provider unavailable");
    }
    : () => ({
      nodeIdToNodeLocatorId(id) {
        workflowBoundaryCalls.push(String(id));
        throw new Error("optional workflow mapper unavailable");
      },
    });
  const fixture = createFixture({
    graph: graphFromNodes([node]),
    storeMode: "none",
    directStorePlan: [({ outputStore }) => [
      { useNodeOutputStore: () => outputStore },
      { useWorkflowStore },
    ]],
  });
  appendNodeRoot(fixture.document, "7:42");
  const rawLocators = ["42", "7:42", "8:42", "99"];
  for (const locator of [...rawLocators, "locator:42", "locator:99"]) {
    fixture.outputPreviewImages.set(locator, true);
  }

  fixture.runtime.handleGeneratorPreviewEvent({
    detail: {
      data: {
        node: "42",
        displayNodeId: "8:42",
        realNodeId: "99",
        images: [{ filename: `${label}.webp` }],
      },
    },
  });
  await flushPromises();

  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(fixture.calls.frontendFetches, 0);
  assert.equal(fixture.calls.assetImports.length, 0);
  for (const locator of rawLocators) {
    assert.equal(fixture.outputPreviewImages.has(locator), false, `${label} retained ${locator}`);
    assert.equal(
      fixture.revokeCalls.includes(locator),
      true,
      `${label} prevented raw/leaf revoke for ${locator}`,
    );
  }
  assert.equal(fixture.outputPreviewImages.has("locator:42"), true);
  assert.equal(fixture.outputPreviewImages.has("locator:99"), true);
  if (label === "workflow-provider-throws") {
    assert.deepEqual(workflowBoundaryCalls, ["provider"]);
  } else {
    assert.equal(workflowBoundaryCalls.includes("42"), true);
    assert.equal(workflowBoundaryCalls.includes("99"), true);
  }
}

{
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({ graph: graphFromNodes([node]), storeMode: "html-fallback" });
  fixture.outputPreviewImages.set("42", true);
  fixture.outputPreviewImages.set("locator:42", true);
  const event = {
    detail: { data: { node: "42", images: [{ filename: "html.webp" }], run_id: "html-a" } },
  };

  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(fixture.calls.frontendFetches, 1, "Missing asset tags must use the HTML fallback");
  assert.deepEqual(
    fixture.calls.assetImports,
    ["https://comfy.test/assets/dialogService-html.js"],
  );
  assert.equal(fixture.outputPreviewImages.has("42"), false);
  assert.equal(fixture.outputPreviewImages.has("locator:42"), false);

  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1, "HTML fallback store resolution must stay cached");
  assert.equal(fixture.calls.frontendFetches, 1, "HTML discovery must stay promise-cached");
  assert.equal(fixture.calls.assetImports.length, 1, "HTML-discovered module import must stay cached");
}

for (const [label, workflowStoreModule] of [
  ["absent", {}],
  ["non-function", { useWorkflowStore: "not-a-function" }],
]) {
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({
    graph: graphFromNodes([node]),
    storeMode: "none",
    directStorePlan: [({ outputStore }) => [
      { useNodeOutputStore: () => outputStore },
      workflowStoreModule,
    ]],
  });
  fixture.outputPreviewImages.set("42", true);
  fixture.outputPreviewImages.set("locator:42", true);

  fixture.runtime.handleGeneratorPreviewEvent({
    detail: { data: { node: "42", images: [{ filename: `output-only-${label}.webp` }] } },
  });
  await flushPromises();

  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(
    fixture.calls.frontendFetches,
    0,
    `An output-only direct tuple must not fall back when workflow is ${label}`,
  );
  assert.equal(fixture.calls.assetImports.length, 0);
  assert.equal(fixture.workflowLocatorCalls.length, 0);
  assert.equal(fixture.outputPreviewImages.has("42"), false);
  assert.equal(
    fixture.outputPreviewImages.has("locator:42"),
    true,
    "Without a workflow provider only raw output locators can be purged",
  );
}

{
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({
    graph: graphFromNodes([node]),
    storeMode: "none",
    directStorePlan: [({ workflowStore }) => [
      { useNodeOutputStore: "not-a-function" },
      { useWorkflowStore: () => workflowStore },
    ]],
    frontendHtmlPlan: ['<script src="./assets/dialogService-invalid-output.js"></script>'],
    assetImportPlan: [({ outputStore, workflowStore }) => ({
      cn: () => outputStore,
      M: () => workflowStore,
    })],
  });
  fixture.outputPreviewImages.set("42", true);
  fixture.outputPreviewImages.set("locator:42", true);

  fixture.runtime.handleGeneratorPreviewEvent({
    detail: { data: { node: "42", images: [{ filename: "invalid-output.webp" }] } },
  });
  await flushPromises();

  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(
    fixture.calls.frontendFetches,
    1,
    "An invalid output provider must fall through to frontend discovery",
  );
  assert.deepEqual(
    fixture.calls.assetImports,
    ["https://comfy.test/assets/dialogService-invalid-output.js"],
  );
  assert.equal(fixture.outputPreviewImages.has("42"), false);
  assert.equal(fixture.outputPreviewImages.has("locator:42"), false);
}

{
  const pendingDirectStore = createDeferred();
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const directStorePlan = [
    pendingDirectStore.promise,
    ({ outputStore, workflowStore }) => [
      { useNodeOutputStore: () => outputStore },
      { useWorkflowStore: () => workflowStore },
    ],
  ];
  const fixture = createFixture({
    graph: graphFromNodes([node]),
    storeMode: "none",
    directStorePlan,
    frontendHtmlPlan: [""],
  });
  const previewEvent = (realNodeId) => ({
    detail: {
      data: {
        node: "42",
        realNodeId,
        images: [{ filename: `${realNodeId}.webp` }],
        run_id: `retry-${realNodeId}`,
      },
    },
  });

  fixture.runtime.handleGeneratorPreviewEvent(previewEvent("91"));
  fixture.runtime.handleGeneratorPreviewEvent(previewEvent("92"));
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1, "Concurrent purges must share one provider attempt");
  pendingDirectStore.reject(new Error("transient direct-store failure"));
  await flushPromises();
  assert.equal(fixture.calls.frontendFetches, 1);
  await drainScheduledPreviewWork(fixture);
  assert.equal(fixture.calls.directStoreLoads, 1, "A failed provider lookup must not retry inside its active batch");
  assert.equal(fixture.calls.frontendFetches, 1);

  fixture.outputPreviewImages.set("93", true);
  fixture.outputPreviewImages.set("locator:93", true);
  fixture.runtime.handleGeneratorPreviewEvent(previewEvent("93"));
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 2, "A later batch must retry a transient direct-store failure");
  assert.equal(fixture.outputPreviewImages.has("93"), false);
  assert.equal(fixture.outputPreviewImages.has("locator:93"), false);

  await drainScheduledPreviewWork(fixture);
  fixture.runtime.handleGeneratorPreviewEvent(previewEvent("94"));
  await flushPromises();
  assert.equal(
    fixture.calls.directStoreLoads,
    2,
    "A successful retry must remain positive-cached in a later batch",
  );
  assert.equal(fixture.calls.frontendFetches, 1);
}

{
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({
    graph: graphFromNodes([node]),
    storeMode: "none",
    directStorePlan: [
      new Error("direct unavailable first batch"),
      new Error("direct unavailable second batch"),
    ],
    frontendHtmlPlan: [
      "",
      '<script src="./assets/dialogService-retry-html.js"></script>',
    ],
    assetImportPlan: [({ outputStore, workflowStore }) => ({
      cn: () => outputStore,
      M: () => workflowStore,
    })],
  });
  const event = {
    detail: { data: { node: "42", images: [{ filename: "html-retry.webp" }] } },
  };

  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(fixture.calls.frontendFetches, 1);
  assert.equal(fixture.calls.assetImports.length, 0);
  await drainScheduledPreviewWork(fixture);
  assert.equal(fixture.calls.frontendFetches, 1, "Empty HTML discovery must stay bounded to one active batch");

  fixture.outputPreviewImages.set("42", true);
  fixture.outputPreviewImages.set("locator:42", true);
  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 2);
  assert.equal(fixture.calls.frontendFetches, 2, "A later batch must retry empty HTML discovery");
  assert.deepEqual(
    fixture.calls.assetImports,
    ["https://comfy.test/assets/dialogService-retry-html.js"],
  );
  assert.equal(fixture.outputPreviewImages.has("42"), false);
  assert.equal(fixture.outputPreviewImages.has("locator:42"), false);

  await drainScheduledPreviewWork(fixture);
  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 2);
  assert.equal(fixture.calls.frontendFetches, 2);
  assert.equal(
    fixture.calls.assetImports.length,
    1,
    "Recovered HTML providers must remain positive-cached in a later batch",
  );
}

{
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({
    graph: graphFromNodes([node]),
    storeMode: "none",
    directStorePlan: [
      new Error("direct unavailable first batch"),
      new Error("direct unavailable second batch"),
    ],
    frontendHtmlPlan: ['<script src="./assets/dialogService-retry-import.js"></script>'],
    assetImportPlan: [
      new Error("transient asset import failure"),
      ({ outputStore, workflowStore }) => ({
        cn: () => outputStore,
        M: () => workflowStore,
      }),
    ],
  });
  const event = {
    detail: { data: { node: "42", images: [{ filename: "import-retry.webp" }] } },
  };

  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(fixture.calls.frontendFetches, 1);
  assert.equal(fixture.calls.assetImports.length, 1);
  await drainScheduledPreviewWork(fixture);
  assert.equal(fixture.calls.assetImports.length, 1, "A failed import must not retry inside its active batch");

  fixture.outputPreviewImages.set("42", true);
  fixture.outputPreviewImages.set("locator:42", true);
  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 2);
  assert.equal(fixture.calls.frontendFetches, 1, "A successful asset URL may remain cached across import retry");
  assert.equal(fixture.calls.assetImports.length, 2, "A later batch must retry a transient asset import failure");
  assert.equal(fixture.outputPreviewImages.has("42"), false);
  assert.equal(fixture.outputPreviewImages.has("locator:42"), false);

  await drainScheduledPreviewWork(fixture);
  fixture.runtime.handleGeneratorPreviewEvent(event);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 2);
  assert.equal(fixture.calls.frontendFetches, 1);
  assert.equal(
    fixture.calls.assetImports.length,
    2,
    "Recovered asset providers must remain positive-cached in a later batch",
  );
}

{
  const pendingStores = createDeferred();
  const nodeA = { id: 41, type: GENERATOR_NODE_TYPE };
  const nodeB = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({
    graph: graphFromNodes([nodeA, nodeB]),
    storeMode: "none",
    directStorePlan: [pendingStores.promise],
  });
  const rootA = appendNodeRoot(fixture.document, "41");
  const rootB = appendNodeRoot(fixture.document, "42");
  for (const locator of ["41", "locator:41", "42", "locator:42"]) {
    fixture.outputPreviewImages.set(locator, true);
  }
  const previewEvent = (nodeId) => ({
    detail: {
      data: {
        node: String(nodeId),
        images: [{ filename: `multi-${nodeId}.webp` }],
        run_id: `multi-${nodeId}`,
      },
    },
  });

  fixture.runtime.handleGeneratorPreviewEvent(previewEvent(41));
  await flushPromises();
  const nodeAFrameIds = fixture.scheduler.frames.map(({ id }) => id);
  const nodeATimerIds = [...fixture.scheduler.timers.keys()];
  const nodeAObserver = fixture.mutationObservers[0];
  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(nodeAFrameIds.length, 3);
  assert.equal(nodeATimerIds.length, 7);

  fixture.runtime.handleGeneratorPreviewEvent(previewEvent(42));
  await flushPromises();
  const nodeBFrameIds = fixture.scheduler.frames
    .map(({ id }) => id)
    .filter((id) => !nodeAFrameIds.includes(id));
  const nodeBTimerIds = [...fixture.scheduler.timers.keys()]
    .filter((id) => !nodeATimerIds.includes(id));
  const nodeBObserver = fixture.mutationObservers[1];
  assert.equal(
    fixture.calls.directStoreLoads,
    1,
    "Concurrent nodes must share one unresolved provider attempt",
  );
  assert.equal(nodeBFrameIds.length, 3);
  assert.equal(nodeBTimerIds.length, 7);
  assert.equal(fixture.mutationObservers.length, 2);

  fixture.runtime.disposeGeneratorNativePreviewLifecycle(nodeA);
  assert.deepEqual(
    fixture.scheduler.frames.map(({ id }) => id).sort((left, right) => left - right),
    [...nodeBFrameIds].sort((left, right) => left - right),
    "Disposing node A must retain every node B frame",
  );
  assert.deepEqual(
    [...fixture.scheduler.timers.keys()].sort((left, right) => left - right),
    [...nodeBTimerIds].sort((left, right) => left - right),
    "Disposing node A must retain every node B timer",
  );
  assert.deepEqual(
    [...fixture.scheduler.canceledFrames].sort((left, right) => left - right),
    [...nodeAFrameIds].sort((left, right) => left - right),
  );
  for (const timerId of nodeATimerIds) {
    assert.equal(fixture.scheduler.cleared.includes(timerId), true);
  }
  assert.equal(nodeAObserver.disconnectCalls, 1);
  assert.equal(nodeBObserver.disconnectCalls, 0);

  const lateNodeAImage = fixture.document.createElement("img");
  lateNodeAImage.className = "pointer-events-none object-contain";
  rootA.append(lateNodeAImage);
  const afterDisposeSnapshot = adapterChannelSnapshot(fixture.calls);
  fixture.scheduler.runCanceledCallbacks();
  nodeAObserver.trigger();
  assert.deepEqual(
    adapterChannelSnapshot(fixture.calls),
    afterDisposeSnapshot,
    "Node A stale callbacks must not affect node B adapters",
  );
  assert.equal(lateNodeAImage.classList.contains(NATIVE_HIDDEN_CLASS), false);
  assert.deepEqual(fixture.scheduler.frames.map(({ id }) => id), nodeBFrameIds);
  assert.deepEqual([...fixture.scheduler.timers.keys()], nodeBTimerIds);
  assert.equal(nodeBObserver.disconnectCalls, 0);

  pendingStores.resolve([
    { useNodeOutputStore: () => fixture.outputStore },
    { useWorkflowStore: () => fixture.workflowStore },
  ]);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(fixture.outputPreviewImages.has("41"), true);
  assert.equal(fixture.outputPreviewImages.has("locator:41"), true);
  assert.equal(fixture.revokeCalls.filter((value) => value === "locator:41").length, 0);
  assert.equal(fixture.outputPreviewImages.has("42"), false);
  assert.equal(fixture.outputPreviewImages.has("locator:42"), false);
  assert.equal(fixture.revokeCalls.filter((value) => value === "locator:42").length, 1);

  await drainScheduledPreviewWork(fixture);
  assert.equal(fixture.scheduler.frames.length, 0);
  assert.deepEqual(fixture.scheduler.delays(), [5000]);
  assert.equal(fixture.revokeCalls.filter((value) => value === "locator:41").length, 0);
  assert.equal(fixture.revokeCalls.filter((value) => value === "locator:42").length, 4);
  const lateNodeBImage = fixture.document.createElement("img");
  lateNodeBImage.className = "pointer-events-none object-contain";
  rootB.append(lateNodeBImage);
  nodeBObserver.trigger();
  assertHidden(lateNodeBImage, "Node B observer must remain live after node A disposal");
  assert.equal(nodeBObserver.disconnectCalls, 0);
}

{
  const fixture = createFixture({ storeMode: "none" });
  const root = appendNodeRoot(fixture.document, "42");
  const node = { id: 42 };

  fixture.runtime.scheduleGeneratorDefaultPreviewSuppression(node, { purgeStore: false });
  assert.equal(fixture.calls.suppress.length, 1);
  assert.equal(fixture.mutationObservers.length, 1);
  assert.deepEqual(
    fixture.mutationObservers[0].observeCalls,
    [{ root, options: { childList: true, subtree: true } }],
  );
  const existingObserver = fixture.mutationObservers[0];
  assert.equal(fixture.scheduler.frames.length, 2, "Hide and suppression RAF batches must be scheduled");
  assert.deepEqual(fixture.scheduler.delays(), [80, 120, 240, 360, 5000]);

  const lateImage = fixture.document.createElement("img");
  lateImage.className = "pointer-events-none object-contain";
  root.append(lateImage);
  const qualifiedRoot = appendNodeRoot(fixture.document, "7:42");
  const qualifiedImage = fixture.document.createElement("img");
  qualifiedImage.className = "pointer-events-none object-contain";
  qualifiedRoot.append(qualifiedImage);
  const unrelatedRoot = appendNodeRoot(fixture.document, "99");
  fixture.runtime.scheduleGeneratorDefaultPreviewSuppression(node, { purgeStore: false });
  assertHidden(lateImage, "A deduped call must still perform its immediate hide");
  assertHidden(qualifiedImage, "A newly matched qualified root must be hidden immediately");
  assert.equal(fixture.calls.suppress.length, 2, "A deduped call must still suppress immediately");
  assert.equal(fixture.mutationObservers.length, 2, "Only the new qualified root needs an observer");
  assert.equal(existingObserver.disconnectCalls, 0, "The existing connected observer must be retained");
  assert.deepEqual(
    fixture.mutationObservers[1].observeCalls,
    [{ root: qualifiedRoot, options: { childList: true, subtree: true } }],
  );
  const observedRoots = fixture.mutationObservers.flatMap(
    (observer) => observer.observeCalls.map(({ root: observedRoot }) => observedRoot),
  );
  assert.equal(observedRoots.includes(unrelatedRoot), false);
  assert.deepEqual(observedRoots, [root, qualifiedRoot]);
  assert.equal(fixture.scheduler.frames.length, 2, "A deduped call must not add delayed RAF batches");
  assert.deepEqual(fixture.scheduler.delays(), [80, 120, 240, 360, 5000]);
  assert.equal(fixture.scheduler.cleared.length, 1, "Observer stop timer must be refreshed on each ensure");

  fixture.runtime.scheduleGeneratorDefaultPreviewSuppression(node, { purgeStore: false });
  assert.equal(fixture.calls.suppress.length, 3);
  assert.equal(fixture.mutationObservers.length, 2, "Existing root observers must not be duplicated");
  assert.equal(existingObserver.disconnectCalls, 0);
  assert.equal(fixture.scheduler.frames.length, 2, "Partial dedupe must retain the original RAF batches");
  assert.deepEqual(fixture.scheduler.delays(), [80, 120, 240, 360, 5000]);
  assert.equal(fixture.scheduler.cleared.length, 2);

  fixture.scheduler.runNextFrame();
  fixture.scheduler.runNextFrame();
  assert.equal(fixture.calls.suppress.length, 4);
  assert.equal(fixture.scheduler.frames.length, 0);

  const observerImage = fixture.document.createElement("img");
  observerImage.className = "pointer-events-none object-contain";
  root.append(observerImage);
  const unobservedQualifiedRoot = appendNodeRoot(fixture.document, "8:42");
  const unobservedQualifiedImage = fixture.document.createElement("img");
  unobservedQualifiedImage.className = "pointer-events-none object-contain";
  unobservedQualifiedRoot.append(unobservedQualifiedImage);
  fixture.mutationObservers[0].trigger();
  assertHidden(observerImage, "Observer callback must re-hide late native previews");
  assert.equal(
    unobservedQualifiedImage.classList.contains(NATIVE_HIDDEN_CLASS),
    false,
    "A root-scoped observer callback must not rescan and hide another unobserved root",
  );
  assert.equal(unobservedQualifiedRoot.classList.contains(GENERATOR_VUE_NODE_CLASS), false);
  assert.equal(fixture.scheduler.frames.length, 1, "The first mutation must schedule one root tail");

  const burstObserverImage = fixture.document.createElement("img");
  burstObserverImage.className = "pointer-events-none object-contain";
  root.append(burstObserverImage);
  fixture.mutationObservers[0].trigger();
  fixture.mutationObservers[0].trigger();
  assert.equal(
    fixture.scheduler.frames.length,
    1,
    "Repeated callbacks in one mutation burst must share one root-scoped RAF tail",
  );
  assert.equal(
    burstObserverImage.classList.contains(NATIVE_HIDDEN_CLASS),
    false,
    "A coalesced burst must not repeat its immediate root scan",
  );
  fixture.scheduler.runNextFrame();
  assertHidden(burstObserverImage, "The shared observer RAF tail must re-scan its root");
  assert.equal(unobservedQualifiedImage.classList.contains(NATIVE_HIDDEN_CLASS), false);
  assert.equal(fixture.scheduler.frames.length, 0);

  fixture.mutationObservers[0].trigger();
  fixture.mutationObservers[1].trigger();
  const rootScopedFrameIds = fixture.scheduler.frames.map(({ id }) => id);
  assert.equal(
    rootScopedFrameIds.length,
    2,
    "Two observed roots must reserve independent RAF tails in the same mutation burst",
  );
  const rootTailImage = fixture.document.createElement("img");
  rootTailImage.className = "pointer-events-none object-contain";
  root.append(rootTailImage);
  const qualifiedTailImage = fixture.document.createElement("img");
  qualifiedTailImage.className = "pointer-events-none object-contain";
  qualifiedRoot.append(qualifiedTailImage);
  fixture.mutationObservers[0].trigger();
  fixture.mutationObservers[1].trigger();
  assert.deepEqual(
    fixture.scheduler.frames.map(({ id }) => id),
    rootScopedFrameIds,
    "Repeated callbacks must retain exactly one RAF tail per observed root",
  );
  assert.equal(rootTailImage.classList.contains(NATIVE_HIDDEN_CLASS), false);
  assert.equal(qualifiedTailImage.classList.contains(NATIVE_HIDDEN_CLASS), false);

  fixture.scheduler.runNextFrame();
  assertHidden(rootTailImage, "The first root tail must re-scan only its own root");
  assert.equal(qualifiedTailImage.classList.contains(NATIVE_HIDDEN_CLASS), false);
  fixture.scheduler.runNextFrame();
  assertHidden(qualifiedTailImage, "The qualified root must execute its independent tail");
  assert.equal(fixture.scheduler.frames.length, 0);
  fixture.scheduler.runDelay(80);
  fixture.scheduler.runDelay(120);
  assert.equal(fixture.calls.suppress.length, 5);
  fixture.scheduler.runDelay(240);
  fixture.scheduler.runDelay(360);
  assert.equal(fixture.calls.suppress.length, 6);
  assert.equal(fixture.scheduler.frames.length, 0);
  assert.deepEqual(fixture.scheduler.delays(), [5000]);
  assert.equal(fixture.calls.legacyGets, 0, "purgeStore false must survive every delayed callback");

  fixture.scheduler.runDelay(5000);
  assert.equal(existingObserver.disconnectCalls, 1);
  assert.equal(fixture.mutationObservers[1].disconnectCalls, 1);
}

{
  const fixture = createFixture({ storeMode: "none" });
  const node = { id: 42 };
  const staleRoot = appendNodeRoot(fixture.document, "42");
  fixture.runtime.scheduleGeneratorDefaultPreviewSuppression(node, { purgeStore: false });
  const staleObserver = fixture.mutationObservers[0];

  staleRoot.remove();
  staleRoot.isConnected = false;
  const replacementRoot = appendNodeRoot(fixture.document, "42");
  fixture.runtime.scheduleGeneratorDefaultPreviewSuppression(node, { purgeStore: false });

  assert.equal(staleObserver.disconnectCalls, 1, "Disconnected roots must be pruned");
  assert.equal(fixture.mutationObservers.length, 2);
  assert.deepEqual(
    fixture.mutationObservers[1].observeCalls,
    [{ root: replacementRoot, options: { childList: true, subtree: true } }],
  );
}

{
  const pendingDirectStore = createDeferred();
  const node = { id: 42, type: GENERATOR_NODE_TYPE };
  const fixture = createFixture({
    storeMode: "none",
    directStorePlan: [pendingDirectStore.promise],
  });
  const root = appendNodeRoot(fixture.document, "42");

  fixture.runtime.scheduleGeneratorDefaultPreviewSuppression(node);
  await flushPromises();
  assert.equal(fixture.calls.directStoreLoads, 1);
  assert.equal(fixture.mutationObservers.length, 1);
  const disposedObserver = fixture.mutationObservers[0];
  const pendingFrameIds = fixture.scheduler.frames.map(({ id }) => id).sort((left, right) => left - right);
  const pendingTimerIds = [...fixture.scheduler.timers.keys()].sort((left, right) => left - right);

  fixture.runtime.disposeGeneratorNativePreviewLifecycle(node);
  assert.equal(fixture.scheduler.frames.length, 0, "Dispose must cancel every node-owned RAF");
  assert.equal(fixture.scheduler.timers.size, 0, "Dispose must clear every node-owned timer");
  assert.deepEqual(
    [...fixture.scheduler.canceledFrames].sort((left, right) => left - right),
    pendingFrameIds,
  );
  for (const timerId of pendingTimerIds) {
    assert.equal(fixture.scheduler.cleared.includes(timerId), true, `Dispose retained timer ${timerId}`);
  }
  assert.equal(disposedObserver.disconnectCalls, 1, "Dispose must disconnect each observer once");

  const canceledFramesAfterDispose = [...fixture.scheduler.canceledFrames];
  const clearedAfterDispose = [...fixture.scheduler.cleared];
  fixture.runtime.disposeGeneratorNativePreviewLifecycle(node);
  assert.deepEqual(fixture.scheduler.canceledFrames, canceledFramesAfterDispose, "Dispose must be idempotent");
  assert.deepEqual(fixture.scheduler.cleared, clearedAfterDispose, "Idempotent dispose must not clear twice");
  assert.equal(disposedObserver.disconnectCalls, 1);

  const disposedSnapshot = adapterChannelSnapshot(fixture.calls);
  fixture.runtime.scheduleGeneratorDefaultPreviewSuppression(node);
  assert.deepEqual(
    adapterChannelSnapshot(fixture.calls),
    disposedSnapshot,
    "A disposed lifecycle must reject new scheduling",
  );
  assert.equal(fixture.scheduler.frames.length, 0);
  assert.equal(fixture.scheduler.timers.size, 0);
  assert.equal(fixture.mutationObservers.length, 1);

  fixture.runtime.activateGeneratorNativePreviewLifecycle(node);
  fixture.runtime.scheduleGeneratorDefaultPreviewSuppression(node, { purgeStore: false });
  assert.equal(fixture.calls.suppress.length, disposedSnapshot.suppress + 1);
  assert.equal(fixture.mutationObservers.length, 2, "Activate must permit a fresh observer");
  const activeObserver = fixture.mutationObservers[1];
  const activeFrameIds = fixture.scheduler.frames.map(({ id }) => id);
  const activeTimerIds = [...fixture.scheduler.timers.keys()];
  const reactivatedTarget = fixture.document.createElement("img");
  reactivatedTarget.className = "pointer-events-none object-contain";
  root.append(reactivatedTarget);
  const unobservedRoot = appendNodeRoot(fixture.document, "7:42");
  const unobservedTarget = fixture.document.createElement("img");
  unobservedTarget.className = "pointer-events-none object-contain";
  unobservedRoot.append(unobservedTarget);
  const activeSnapshot = adapterChannelSnapshot(fixture.calls);

  fixture.scheduler.runCanceledCallbacks();
  assert.deepEqual(
    adapterChannelSnapshot(fixture.calls),
    activeSnapshot,
    "Canceled callbacks from a disposed generation must remain no-ops after activate",
  );
  assert.deepEqual(fixture.scheduler.frames.map(({ id }) => id), activeFrameIds);
  assert.deepEqual([...fixture.scheduler.timers.keys()], activeTimerIds);
  assert.equal(activeObserver.disconnectCalls, 0, "A stale stop timer must not disconnect the active observer");
  disposedObserver.trigger();
  assert.equal(
    reactivatedTarget.classList.contains(NATIVE_HIDDEN_CLASS),
    false,
    "An observer from the disposed generation must not touch the reactivated root",
  );
  assert.equal(
    unobservedTarget.classList.contains(NATIVE_HIDDEN_CLASS),
    false,
    "An observer from the disposed generation must not rescan an unobserved root",
  );

  pendingDirectStore.resolve([
    { useNodeOutputStore: () => fixture.outputStore },
    { useWorkflowStore: () => fixture.workflowStore },
  ]);
  await flushPromises();
  assert.equal(fixture.revokeCalls.length, 0, "A late store resolution from a disposed generation must be ignored");
  assert.equal(fixture.workflowLocatorCalls.length, 0);

  activeObserver.trigger();
  assertHidden(reactivatedTarget, "Activate must restore the current observer lifecycle");
  assert.equal(unobservedTarget.classList.contains(NATIVE_HIDDEN_CLASS), false);
}

{
  const topGenerator = { id: 2, type: GENERATOR_NODE_TYPE };
  const nonGenerator = { id: 3, type: "OtherNode" };
  const subGenerator = { id: 7, type: GENERATOR_NODE_TYPE };
  const subgraph = graphFromNodes([subGenerator]);
  const parent = { id: 5, type: "Subgraph", subgraph };
  const graph = graphFromNodes([topGenerator, nonGenerator, parent]);
  const fixture = createFixture({
    graph,
    generatorNodes: [topGenerator, nonGenerator, subGenerator],
    storeMode: "none",
  });

  fixture.runtime.handleGeneratorPreviewEvent({
    detail: {
      data: {
        node: "5:7",
        images: [{ filename: "event.webp" }],
        run_id: "event-run",
      },
    },
  });
  assert.equal(fixture.calls.addImages.length, 1);
  assert.equal(fixture.calls.addImages[0].node, subGenerator);
  assert.equal(fixture.calls.addImages[0].runId, "event-run");
  assert.equal(fixture.calls.legacyGets, 1, "Preview suppression must not duplicate explicit purge");
  const previewCounts = {
    add: fixture.calls.addImages.length,
    purge: fixture.calls.legacyGets,
    suppress: fixture.calls.suppress.length,
  };
  fixture.runtime.handleGeneratorPreviewEvent({
    detail: { data: { node: "3", images: [{ filename: "ignored.webp" }] } },
  });
  fixture.runtime.handleGeneratorPreviewEvent({
    detail: { data: { node: "404", images: [{ filename: "missing.webp" }] } },
  });
  assert.deepEqual(
    {
      add: fixture.calls.addImages.length,
      purge: fixture.calls.legacyGets,
      suppress: fixture.calls.suppress.length,
    },
    previewCounts,
    "Wrong-type and missing preview targets must be no-ops",
  );

  let stopCalls = 0;
  const blob = { type: "image/webp" };
  fixture.runtime.handleGeneratorDenoisePreviewEvent({
    detail: {
      data: {
        nodeId: "3",
        realNodeId: "5:7",
        blob,
      },
    },
    stopImmediatePropagation() {
      stopCalls += 1;
    },
  });
  assert.equal(stopCalls, 1, "Valid denoise events must stop native capture propagation");
  assert.equal(fixture.calls.setDenoise.length, 1);
  assert.equal(fixture.calls.setDenoise[0].node, subGenerator);
  assert.equal(fixture.calls.setDenoise[0].blob, blob);
  assert.equal(fixture.calls.legacyGets, 2, "Denoise suppression must not duplicate explicit purge");
  fixture.runtime.handleGeneratorDenoisePreviewEvent({
    detail: { data: { nodeId: "5:7" } },
    stopImmediatePropagation() {
      stopCalls += 1;
    },
  });
  fixture.runtime.handleGeneratorDenoisePreviewEvent({
    detail: { data: { nodeId: "3", blob } },
    stopImmediatePropagation() {
      stopCalls += 1;
    },
  });
  assert.equal(stopCalls, 1, "Missing-blob and wrong-type denoise events must not stop propagation");
  assert.equal(fixture.calls.setDenoise.length, 1);

  const progressDetail = { nodeId: "2", value: 3, max: 10 };
  const progressStateDetail = { nodes: { 2: { node_id: "2", value: 4, max: 10 } } };
  fixture.runtime.handleGeneratorProgressEvent({ detail: { data: progressDetail } });
  fixture.runtime.handleGeneratorProgressStateEvent({ detail: { data: progressStateDetail } });
  assert.deepEqual(fixture.calls.progress, [progressDetail]);
  assert.deepEqual(fixture.calls.progressState, [progressStateDetail]);

  fixture.runtime.handleGeneratorExecutingEvent({ detail: "5:7" });
  assert.deepEqual(fixture.calls.clearDenoise.at(-1), { node: subGenerator, update: true });
  const executingClearCount = fixture.calls.clearDenoise.length;
  fixture.runtime.handleGeneratorExecutingEvent({ detail: "3" });
  assert.equal(fixture.calls.clearDenoise.length, executingClearCount);

  fixture.runtime.clearGeneratorDenoisePreviews();
  assert.equal(fixture.calls.progressClear, 1);
  assert.deepEqual(
    fixture.calls.clearDenoise.slice(-2),
    [
      { node: topGenerator, update: true },
      { node: subGenerator, update: true },
    ],
    "Terminal routing must clear only Generator nodes",
  );
  assert.equal(
    fixture.calls.legacyGets,
    5,
    "Preview, denoise, executing, and two terminal Generator nodes must each own one purge batch",
  );
  assert.equal(fixture.calls.suppress.length, 5);
  await flushPromises();
}

console.log("AiO native preview runtime smoke passed.");
