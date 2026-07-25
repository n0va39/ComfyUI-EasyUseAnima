import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [from, to] of Object.entries(replacements)) {
    source = source.replaceAll(from, to);
  }
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const extensionModule = await import(dataModule(
  "../web/js/aio/extension_runtime.js",
));
assert.deepEqual(
  Object.keys(extensionModule),
  ["aioCreateExtensionRuntime", "aioListAttachedGeneratorNodes"],
  "AiO extension runtime must expose only its factory and attached-node traversal contracts",
);

const INPUT_NODE_TYPE = "EasyUseAnimaInput";
const GENERATOR_NODE_TYPE = "EasyUseAnimaAIOGenerator";
const GENERATOR_PREVIEW_EVENT = "easyuse-anima-aio-preview";

function createFixture(options = {}) {
  const trace = [];
  const eventRegistrations = [];
  let samplerSetupFailures = Number(options.samplerSetupFailures || 0);
  let userSetupFailures = Number(options.userSetupFailures || 0);
  const callbacks = {
    refreshPanels() {
      trace.push("refreshPanels");
      if (options.getGraph || options.rootGraph) {
        const rootGraph = options.getGraph?.() ?? options.rootGraph;
        const isGeneratorNode = options.isGeneratorNode
          || ((node) => (
            node?.type === GENERATOR_NODE_TYPE
            || node?.comfyClass === GENERATOR_NODE_TYPE
          ));
        for (
          const node of extensionModule.aioListAttachedGeneratorNodes(
            rootGraph,
            isGeneratorNode,
          )
        ) {
          options.renderGeneratorPanel?.(node);
        }
      }
    },
    handlePreviewEvent() {},
    handleProgressEvent() {},
    handleProgressStateEvent() {},
    handleDenoisePreviewEvent() {},
    handleExecutingEvent() {},
    clearDenoisePreviews() {},
  };
  let localeRefresh = null;
  const api = options.api || {
    addEventListener(name, handler, capture) {
      eventRegistrations.push({ name, handler, capture });
      trace.push(`event:${name}:${capture === true}`);
    },
  };
  const runtime = extensionModule.aioCreateExtensionRuntime({
    api,
    constants: {
      inputNodeType: INPUT_NODE_TYPE,
      generatorNodeType: GENERATOR_NODE_TYPE,
      generatorPreviewEvent: GENERATOR_PREVIEW_EVENT,
    },
    setup: {
      ensureStyle() {
        trace.push("ensureStyle");
      },
      installWheelForwarder() {
        trace.push("installWheelForwarder");
        options.onInstallWheelForwarder?.();
      },
      watchLocale(callback) {
        trace.push("watchLocale");
        localeRefresh = callback;
      },
      refreshPanels: callbacks.refreshPanels,
      handlePreviewEvent: callbacks.handlePreviewEvent,
      handleProgressEvent: callbacks.handleProgressEvent,
      handleProgressStateEvent: callbacks.handleProgressStateEvent,
      handleDenoisePreviewEvent: callbacks.handleDenoisePreviewEvent,
      handleExecutingEvent: callbacks.handleExecutingEvent,
      clearDenoisePreviews: callbacks.clearDenoisePreviews,
      loadSamplerOptions() {
        trace.push("loadSamplerOptions");
        if (samplerSetupFailures > 0) {
          samplerSetupFailures -= 1;
          throw options.samplerSetupError;
        }
        return options.samplerOptionsPromise ?? Promise.resolve();
      },
      loadUserProfiles() {
        trace.push("loadUserProfiles");
        if (userSetupFailures > 0) {
          userSetupFailures -= 1;
          throw options.userSetupError;
        }
        return options.profileError
          ? Promise.reject(options.profileError)
          : options.userProfilesPromise ?? Promise.resolve();
      },
      warnUserProfiles(error) {
        trace.push(`warnUserProfiles:${error.message}`);
      },
    },
    nodes: {
      suppressDefaultPreview(_node, suppressOptions) {
        trace.push(
          suppressOptions?.markDirty === false
            ? "suppressDefaultPreview:markDirty=false"
            : suppressOptions?.purgeStore === false
              ? "suppressDefaultPreview:purgeStore=false"
              : "suppressDefaultPreview",
        );
      },
      hookInputNode() {
        trace.push("hookInputNode");
      },
      hookGeneratorNode() {
        trace.push("hookGeneratorNode");
      },
      syncSerializedWidgets(_node, serialized) {
        trace.push(`syncSerializedWidgets:${serialized.marker}`);
      },
      scheduleDefaultPreviewSuppression(_node, suppressOptions) {
        trace.push(
          suppressOptions?.purgeStore === false
            ? "scheduleDefaultPreviewSuppression:purgeStore=false"
            : "scheduleDefaultPreviewSuppression",
        );
      },
      updateExecutedStatus(_node, message) {
        trace.push(`updateExecutedStatus:${message.marker}`);
      },
      scheduleLayout() {
        trace.push("scheduleLayout");
      },
      disposePanel() {
        trace.push("disposePanel");
        if (options.panelError) {
          throw options.panelError;
        }
      },
      disposeNativePreviewLifecycle() {
        trace.push("disposeNativePreviewLifecycle");
        if (options.nativeError) {
          throw options.nativeError;
        }
      },
    },
  });
  return {
    api,
    runtime,
    trace,
    callbacks,
    eventRegistrations,
    localeRefresh: () => localeRefresh,
  };
}

function createNodeType(trace, options = {}) {
  const returns = {
    created: { hook: "created" },
    configured: { hook: "configured" },
    serialized: { hook: "serialized" },
    executed: { hook: "executed" },
    resized: { hook: "resized" },
    removed: { hook: "removed" },
  };
  function NodeType() {}
  NodeType.prototype.onNodeCreated = function (...args) {
    trace.push(`original:onNodeCreated:${args.join(",")}`);
    if (options.createdError) {
      throw options.createdError;
    }
    return returns.created;
  };
  NodeType.prototype.onConfigure = function (...args) {
    trace.push(`original:onConfigure:${args.join(",")}`);
    if (options.configuredError) {
      throw options.configuredError;
    }
    return returns.configured;
  };
  NodeType.prototype.onSerialize = function (serialized) {
    trace.push(`original:onSerialize:${serialized.marker}`);
    if (options.serializedError) {
      throw options.serializedError;
    }
    return returns.serialized;
  };
  NodeType.prototype.onExecuted = function (message) {
    trace.push(`original:onExecuted:${message.marker}`);
    return returns.executed;
  };
  NodeType.prototype.onResize = function (...args) {
    trace.push(`original:onResize:${args.join(",")}`);
    if (options.resizedError) {
      throw options.resizedError;
    }
    return returns.resized;
  };
  NodeType.prototype.onRemoved = function (...args) {
    trace.push(`original:onRemoved:${args.join(",")}`);
    if (options.removedError) {
      throw options.removedError;
    }
    return returns.removed;
  };
  return { NodeType, returns };
}

{
  const fixture = createFixture();
  assert.equal(
    await fixture.runtime.setup(),
    undefined,
    "setup must preserve the extension hook's undefined result",
  );
  await Promise.resolve();

  assert.deepEqual(fixture.trace.slice(0, 13), [
    "ensureStyle",
    "installWheelForwarder",
    "watchLocale",
    `event:${GENERATOR_PREVIEW_EVENT}:false`,
    "event:progress:false",
    "event:progress_state:false",
    "event:b_preview_with_metadata:true",
    "event:executing:false",
    "event:execution_error:false",
    "event:execution_interrupted:false",
    "event:execution_success:false",
    "loadSamplerOptions",
    "loadUserProfiles",
  ]);
  assert.deepEqual(
    fixture.eventRegistrations.map(({ name }) => name),
    [
      GENERATOR_PREVIEW_EVENT,
      "progress",
      "progress_state",
      "b_preview_with_metadata",
      "executing",
      "execution_error",
      "execution_interrupted",
      "execution_success",
    ],
  );
  assert.equal(
    fixture.eventRegistrations.find(({ name }) => name === GENERATOR_PREVIEW_EVENT).handler,
    fixture.callbacks.handlePreviewEvent,
  );
  assert.equal(
    fixture.eventRegistrations.find(({ name }) => name === "progress").handler,
    fixture.callbacks.handleProgressEvent,
  );
  assert.equal(
    fixture.eventRegistrations.find(({ name }) => name === "progress_state").handler,
    fixture.callbacks.handleProgressStateEvent,
  );
  assert.equal(
    fixture.eventRegistrations.find(({ name }) => name === "b_preview_with_metadata").handler,
    fixture.callbacks.handleDenoisePreviewEvent,
  );
  assert.equal(
    fixture.eventRegistrations.find(({ name }) => name === "b_preview_with_metadata").capture,
    true,
  );
  assert.equal(
    fixture.eventRegistrations.find(({ name }) => name === "executing").handler,
    fixture.callbacks.handleExecutingEvent,
  );
  for (const name of ["execution_error", "execution_interrupted", "execution_success"]) {
    assert.equal(
      fixture.eventRegistrations.find((registration) => registration.name === name).handler,
      fixture.callbacks.clearDenoisePreviews,
      `${name} must keep the shared preview cleanup handler`,
    );
  }
  assert.equal(fixture.trace.filter((item) => item === "refreshPanels").length, 2);
  assert.equal(fixture.localeRefresh(), fixture.callbacks.refreshPanels);
  fixture.localeRefresh()();
  assert.equal(fixture.trace.filter((item) => item === "refreshPanels").length, 3);

  const firstSetupTrace = [...fixture.trace];
  const firstSetupRegistrations = [...fixture.eventRegistrations];
  assert.equal(await fixture.runtime.setup(), undefined);
  await Promise.resolve();
  assert.deepEqual(
    fixture.trace,
    firstSetupTrace,
    "repeated setup must not reload data or reinstall global listeners",
  );
  assert.deepEqual(fixture.eventRegistrations, firstSetupRegistrations);
}

{
  let resolveSamplerOptions;
  const samplerOptionsPromise = new Promise((resolve) => {
    resolveSamplerOptions = resolve;
  });
  const rootGraph = { _nodes: [] };
  const refreshedPanels = [];
  const fixture = createFixture({
    samplerOptionsPromise,
    userProfilesPromise: new Promise(() => {}),
    getGraph: () => rootGraph,
    renderGeneratorPanel(node) {
      refreshedPanels.push(node);
    },
  });
  await fixture.runtime.setup();
  const { NodeType } = createNodeType(fixture.trace);
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  const topGenerator = Object.assign(new NodeType(), {
    id: 1,
    type: GENERATOR_NODE_TYPE,
    graph: rootGraph,
  });
  const subgraph = { nodes: [] };
  const subgraphGenerator = Object.assign(new NodeType(), {
    id: 7,
    type: GENERATOR_NODE_TYPE,
    graph: subgraph,
  });
  const detachedGenerator = Object.assign(new NodeType(), {
    id: 99,
    type: GENERATOR_NODE_TYPE,
  });
  const firstSubgraphNode = { id: 5, type: "Subgraph", graph: rootGraph, subgraph };
  const secondSubgraphNode = { id: 6, type: "Subgraph", graph: rootGraph, subgraph };

  topGenerator.onNodeCreated("cold-top");
  subgraphGenerator.onConfigure("cold-subgraph");
  detachedGenerator.onNodeCreated("cold-detached");
  subgraph.nodes.push(subgraphGenerator);
  rootGraph._nodes.push(topGenerator, firstSubgraphNode, secondSubgraphNode);

  assert.equal(
    fixture.trace.filter((item) => item === "hookGeneratorNode").length,
    3,
    "generator creation/configure must keep their normal per-node hook path while hydration is pending",
  );
  assert.equal(
    fixture.trace.filter((item) => item === "refreshPanels").length,
    0,
    "sampler hydration must not refresh panels before its shared load resolves",
  );
  assert.deepEqual(refreshedPanels, []);

  resolveSamplerOptions();
  await samplerOptionsPromise;
  await Promise.resolve();
  assert.equal(
    fixture.trace.filter((item) => item === "refreshPanels").length,
    1,
    "sampler hydration must have one extension-owned global panel refresh regardless of node hook count",
  );
  assert.deepEqual(
    refreshedPanels,
    [topGenerator, subgraphGenerator],
    "the shared hydration refresh must render each attached top-level/subgraph panel once and skip detached nodes",
  );
}

{
  let rootGraph;
  const refreshedPanels = [];
  const fixture = createFixture({
    getGraph: () => rootGraph,
    userProfilesPromise: new Promise(() => {}),
    renderGeneratorPanel(node) {
      refreshedPanels.push(node);
    },
  });
  await fixture.runtime.setup();
  await Promise.resolve();
  assert.equal(
    fixture.trace.filter((item) => item === "refreshPanels").length,
    1,
    "sampler hydration before lazy graph initialization must complete as one safe no-op refresh",
  );
  assert.deepEqual(refreshedPanels, []);

  rootGraph = { nodes: [] };
  const { NodeType } = createNodeType(fixture.trace);
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  const warmTopGenerator = Object.assign(new NodeType(), {
    id: 11,
    type: GENERATOR_NODE_TYPE,
    graph: rootGraph,
  });
  const warmSubgraph = { _nodes: [] };
  const warmSubgraphGenerator = Object.assign(new NodeType(), {
    id: 17,
    type: GENERATOR_NODE_TYPE,
    graph: warmSubgraph,
  });
  const warmSubgraphNode = {
    id: 15,
    type: "Subgraph",
    graph: rootGraph,
    subgraph: warmSubgraph,
  };
  rootGraph.nodes.push(warmTopGenerator, warmSubgraphNode);
  warmSubgraph._nodes.push(warmSubgraphGenerator);
  warmTopGenerator.onNodeCreated("warm-top");
  warmSubgraphGenerator.onConfigure("warm-subgraph");
  await Promise.resolve();

  assert.equal(
    fixture.trace.filter((item) => item === "hookGeneratorNode").length,
    2,
    "warm top-level/subgraph nodes must keep their per-node initial hook path",
  );
  assert.equal(
    fixture.trace.filter((item) => item === "refreshPanels").length,
    1,
    "warm node hooks must not restore a per-node sampler hydration refresh owner",
  );
  assert.deepEqual(refreshedPanels, []);
}

{
  const ownerFixture = createFixture();
  await ownerFixture.runtime.setup();
  await Promise.resolve();
  const ownerTraceBeforeReentry = [...ownerFixture.trace];
  const reentryFixture = createFixture({ api: ownerFixture.api });
  assert.equal(await reentryFixture.runtime.setup(), undefined);
  await Promise.resolve();
  assert.deepEqual(
    reentryFixture.trace,
    [],
    "a new runtime sharing the completed API host must remain a no-op",
  );
  assert.deepEqual(
    ownerFixture.trace,
    ownerTraceBeforeReentry,
    "runtime reentry must not repeat or dispose completed setup",
  );
  assert.equal(reentryFixture.runtime.dispose(), false);
}

{
  let reentryFixture = null;
  let reentryPromise = null;
  const ownerFixture = createFixture({
    onInstallWheelForwarder() {
      reentryPromise = reentryFixture.runtime.setup();
    },
  });
  reentryFixture = createFixture({ api: ownerFixture.api });
  assert.equal(await ownerFixture.runtime.setup(), undefined);
  assert.equal(await reentryPromise, undefined);
  await Promise.resolve();
  assert.deepEqual(
    reentryFixture.trace,
    [],
    "a second factory must not enter setup while the shared API state is in progress",
  );
  assert.equal(ownerFixture.eventRegistrations.length, 8);
}

{
  const setupError = new Error("sampler setup failed");
  const factoryA = createFixture({
    samplerSetupError: setupError,
    samplerSetupFailures: 1,
  });
  let caught = null;
  try {
    await factoryA.runtime.setup();
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, setupError, "setup must preserve the original synchronous error");
  const factoryB = createFixture({ api: factoryA.api });
  assert.equal(await factoryB.runtime.setup(), undefined);
  await Promise.resolve();
  const combinedTrace = [...factoryA.trace, ...factoryB.trace];
  for (const completedStep of [
    "ensureStyle",
    "installWheelForwarder",
    "watchLocale",
  ]) {
    assert.equal(
      combinedTrace.filter((item) => item === completedStep).length,
      1,
      `${completedStep} must remain owned by factory A after the later failure`,
    );
  }
  assert.equal(
    factoryA.eventRegistrations.length,
    8,
    "factory B must not duplicate factory A's completed API listener steps",
  );
  assert.equal(
    combinedTrace.filter((item) => item === "loadSamplerOptions").length,
    2,
    "only the failing sampler loader step must retry in factory B",
  );
  assert.equal(
    combinedTrace.filter((item) => item === "loadUserProfiles").length,
    1,
    "factory B must continue with the first not-yet-run step",
  );

  const factoryC = createFixture({ api: factoryA.api });
  assert.equal(await factoryC.runtime.setup(), undefined);
  await Promise.resolve();
  assert.deepEqual(
    factoryC.trace,
    [],
    "a later runtime must not repeat completed setup",
  );
  assert.equal(factoryC.runtime.dispose(), false);
}

{
  const setupError = new Error("user profile setup failed");
  const factoryA = createFixture({
    userSetupError: setupError,
    userSetupFailures: 1,
  });
  let caught = null;
  try {
    await factoryA.runtime.setup();
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, setupError);
  const factoryB = createFixture({ api: factoryA.api });
  assert.equal(await factoryB.runtime.setup(), undefined);
  await Promise.resolve();
  const combinedTrace = [...factoryA.trace, ...factoryB.trace];
  assert.equal(
    combinedTrace.filter((item) => item === "loadSamplerOptions").length,
    1,
    "a sampler loader and its refresh tail must not restart after a later step fails",
  );
  assert.equal(
    combinedTrace.filter((item) => item === "loadUserProfiles").length,
    2,
    "the failing user-profile loader step alone must retry",
  );
  assert.equal(
    combinedTrace.filter((item) => item === "refreshPanels").length,
    2,
    "the sampler and successful user-profile refresh tails must each run once",
  );
}

{
  const profileError = new Error("profile load failed");
  const fixture = createFixture({ profileError });
  await fixture.runtime.setup();
  await Promise.resolve();
  assert.ok(
    fixture.trace.includes("warnUserProfiles:profile load failed"),
    "the user-profile rejection must reach the entry warning adapter",
  );
}

{
  const fixture = createFixture();
  const originalTrace = [];
  const { NodeType } = createNodeType(originalTrace);
  const originalHooks = {
    onNodeCreated: NodeType.prototype.onNodeCreated,
    onConfigure: NodeType.prototype.onConfigure,
    onSerialize: NodeType.prototype.onSerialize,
    onExecuted: NodeType.prototype.onExecuted,
    onResize: NodeType.prototype.onResize,
    onRemoved: NodeType.prototype.onRemoved,
  };
  assert.equal(
    await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: "OtherNode" }),
    undefined,
  );
  for (const [name, hook] of Object.entries(originalHooks)) {
    assert.equal(NodeType.prototype[name], hook, `unrelated ${name} must stay untouched`);
  }
  assert.equal(NodeType.prototype.hideOutputImages, undefined);
}

{
  const installError = new Error("prototype install failed");
  const fixture = createFixture();
  const { NodeType, returns } = createNodeType(fixture.trace);
  const originalOnNodeCreated = NodeType.prototype.onNodeCreated;
  let currentOnConfigure = NodeType.prototype.onConfigure;
  let configureAssignmentFailures = 1;
  Object.defineProperty(NodeType.prototype, "onConfigure", {
    configurable: true,
    get() {
      return currentOnConfigure;
    },
    set(value) {
      if (configureAssignmentFailures > 0) {
        configureAssignmentFailures -= 1;
        throw installError;
      }
      currentOnConfigure = value;
    },
  });

  let caught = null;
  try {
    await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, installError, "prototype install must preserve its original error");
  assert.equal(
    NodeType.prototype.onNodeCreated,
    originalOnNodeCreated,
    "a partial install must roll back hooks patched before the failure",
  );
  assert.equal(NodeType.prototype.hideOutputImages, undefined);
  assert.equal(
    Object.prototype.hasOwnProperty.call(
      NodeType.prototype,
      "__easyuseAnimaAioGeneratorHooksInstalled",
    ),
    false,
    "a failed install must not publish prototype ownership",
  );

  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  const node = new NodeType();
  assert.equal(node.onNodeCreated("retry"), returns.created);
  assert.deepEqual(fixture.trace, [
    "suppressDefaultPreview:markDirty=false",
    "original:onNodeCreated:retry",
    "hookGeneratorNode",
  ]);
}

{
  const fixture = createFixture();
  const { NodeType, returns } = createNodeType(fixture.trace);
  const generatorOnlyHooks = {
    onSerialize: NodeType.prototype.onSerialize,
    onExecuted: NodeType.prototype.onExecuted,
    onResize: NodeType.prototype.onResize,
    onRemoved: NodeType.prototype.onRemoved,
  };
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: INPUT_NODE_TYPE });
  const installedHooks = {
    onNodeCreated: NodeType.prototype.onNodeCreated,
    onConfigure: NodeType.prototype.onConfigure,
  };
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: INPUT_NODE_TYPE });
  for (const [name, hook] of Object.entries(installedHooks)) {
    assert.equal(NodeType.prototype[name], hook, `input ${name} must not be wrapped twice`);
  }
  const node = new NodeType();

  assert.equal(node.onNodeCreated("a", "b"), returns.created);
  assert.deepEqual(fixture.trace, [
    "original:onNodeCreated:a,b",
    "hookInputNode",
  ]);
  fixture.trace.length = 0;
  assert.equal(node.onConfigure("saved"), returns.configured);
  assert.deepEqual(fixture.trace, [
    "original:onConfigure:saved",
    "hookInputNode",
  ]);
  for (const [name, hook] of Object.entries(generatorOnlyHooks)) {
    assert.equal(NodeType.prototype[name], hook, `input ${name} must stay untouched`);
  }
  assert.equal(NodeType.prototype.hideOutputImages, undefined);
}

{
  const fixture = createFixture();
  const { NodeType, returns } = createNodeType(fixture.trace);
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  const installedHooks = {
    onNodeCreated: NodeType.prototype.onNodeCreated,
    onConfigure: NodeType.prototype.onConfigure,
    onSerialize: NodeType.prototype.onSerialize,
    onExecuted: NodeType.prototype.onExecuted,
    onResize: NodeType.prototype.onResize,
    onRemoved: NodeType.prototype.onRemoved,
  };
  const reentryFixture = createFixture();
  await reentryFixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  for (const [name, hook] of Object.entries(installedHooks)) {
    assert.equal(NodeType.prototype[name], hook, `generator ${name} must not be wrapped twice`);
  }
  assert.deepEqual(
    reentryFixture.trace,
    [],
    "a second runtime must not take ownership of an already-installed prototype",
  );
  const node = new NodeType();

  assert.equal(NodeType.prototype.hideOutputImages, true);
  assert.equal(node.onNodeCreated("new"), returns.created);
  assert.deepEqual(fixture.trace, [
    "suppressDefaultPreview:markDirty=false",
    "original:onNodeCreated:new",
    "hookGeneratorNode",
  ]);

  fixture.trace.length = 0;
  assert.equal(node.onConfigure("saved"), returns.configured);
  assert.deepEqual(fixture.trace, [
    "suppressDefaultPreview:markDirty=false",
    "original:onConfigure:saved",
    "hookGeneratorNode",
  ]);

  fixture.trace.length = 0;
  assert.equal(node.onSerialize({ marker: "workflow" }), returns.serialized);
  assert.deepEqual(fixture.trace, [
    "original:onSerialize:workflow",
    "syncSerializedWidgets:workflow",
  ]);

  fixture.trace.length = 0;
  assert.equal(node.onExecuted({ marker: "done" }), undefined);
  assert.deepEqual(fixture.trace, [
    "scheduleDefaultPreviewSuppression",
    "updateExecutedStatus:done",
    "scheduleDefaultPreviewSuppression:purgeStore=false",
  ]);

  fixture.trace.length = 0;
  assert.equal(node.onResize(512, 640), returns.resized);
  assert.deepEqual(fixture.trace, [
    "original:onResize:512,640",
    "scheduleLayout",
  ]);

  fixture.trace.length = 0;
  assert.equal(node.onRemoved("delete"), returns.removed);
  assert.deepEqual(fixture.trace, [
    "original:onRemoved:delete",
    "disposePanel",
    "disposeNativePreviewLifecycle",
  ]);
}

for (const hookCase of [
  {
    method: "onNodeCreated",
    option: "createdError",
    args: ["new"],
    expectedTrace: [
      "suppressDefaultPreview:markDirty=false",
      "original:onNodeCreated:new",
    ],
  },
  {
    method: "onConfigure",
    option: "configuredError",
    args: ["saved"],
    expectedTrace: [
      "suppressDefaultPreview:markDirty=false",
      "original:onConfigure:saved",
    ],
  },
  {
    method: "onSerialize",
    option: "serializedError",
    args: [{ marker: "workflow" }],
    expectedTrace: ["original:onSerialize:workflow"],
  },
  {
    method: "onResize",
    option: "resizedError",
    args: [512, 640],
    expectedTrace: ["original:onResize:512,640"],
  },
]) {
  const originalError = new Error(`${hookCase.method} failed`);
  const fixture = createFixture();
  const { NodeType } = createNodeType(fixture.trace, {
    [hookCase.option]: originalError,
  });
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  const node = new NodeType();
  let caught = null;
  try {
    node[hookCase.method](...hookCase.args);
  } catch (error) {
    caught = error;
  }
  assert.equal(
    caught,
    originalError,
    `${hookCase.method} must preserve the original error identity`,
  );
  assert.deepEqual(
    fixture.trace,
    hookCase.expectedTrace,
    `${hookCase.method} must not run its tail adapter after the original hook fails`,
  );
}

{
  const removedError = new Error("original removal failed");
  const fixture = createFixture();
  const { NodeType } = createNodeType(fixture.trace, { removedError });
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  const node = new NodeType();
  let caught = null;
  try {
    node.onRemoved("delete");
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, removedError, "the original removal error identity must be preserved");
  assert.deepEqual(fixture.trace, [
    "original:onRemoved:delete",
    "disposePanel",
    "disposeNativePreviewLifecycle",
  ]);
}

{
  const panelError = new Error("panel disposal failed");
  const fixture = createFixture({ panelError });
  const { NodeType } = createNodeType(fixture.trace);
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  const node = new NodeType();
  let caught = null;
  try {
    node.onRemoved("delete");
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, panelError, "the panel disposal error identity must be preserved");
  assert.deepEqual(fixture.trace, [
    "original:onRemoved:delete",
    "disposePanel",
    "disposeNativePreviewLifecycle",
  ]);
}

{
  const removedError = new Error("original removal failed");
  const panelError = new Error("panel disposal failed");
  const nativeError = new Error("native preview disposal failed");
  const fixture = createFixture({ panelError, nativeError });
  const { NodeType } = createNodeType(fixture.trace, { removedError });
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: GENERATOR_NODE_TYPE });
  const node = new NodeType();
  let caught = null;
  try {
    node.onRemoved("delete");
  } catch (error) {
    caught = error;
  }
  assert.equal(
    caught,
    nativeError,
    "the innermost cleanup error must preserve nested-finally precedence",
  );
  assert.deepEqual(fixture.trace, [
    "original:onRemoved:delete",
    "disposePanel",
    "disposeNativePreviewLifecycle",
  ]);
}

console.log("Frontend AiO extension runtime smoke passed.");
