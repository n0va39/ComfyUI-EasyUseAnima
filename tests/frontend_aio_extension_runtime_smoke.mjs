import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const extensionModule = await import(dataModule("../web/js/aio/extension_runtime.js"));
assert.deepEqual(
  Object.keys(extensionModule),
  ["aioCreateExtensionRuntime"],
  "AiO extension runtime must expose only its factory contract",
);

const INPUT_NODE_TYPE = "EasyUseAnimaInput";
const GENERATOR_NODE_TYPE = "EasyUseAnimaAIOGenerator";
const GENERATOR_PREVIEW_EVENT = "easyuse-anima-aio-preview";

function createFixture(options = {}) {
  const trace = [];
  const eventRegistrations = [];
  const callbacks = {
    refreshPanels() {
      trace.push("refreshPanels");
    },
    handlePreviewEvent() {},
    handleProgressEvent() {},
    handleProgressStateEvent() {},
    handleDenoisePreviewEvent() {},
    handleExecutingEvent() {},
    clearDenoisePreviews() {},
  };
  let localeRefresh = null;
  const runtime = extensionModule.aioCreateExtensionRuntime({
    api: {
      addEventListener(name, handler, capture) {
        eventRegistrations.push({ name, handler, capture });
        trace.push(`event:${name}:${capture === true}`);
      },
    },
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
      },
      installQueuePromptHook() {
        trace.push("installQueuePromptHook");
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
        return Promise.resolve();
      },
      loadUserProfiles() {
        trace.push("loadUserProfiles");
        return options.profileError
          ? Promise.reject(options.profileError)
          : Promise.resolve();
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

  assert.deepEqual(fixture.trace.slice(0, 14), [
    "ensureStyle",
    "installWheelForwarder",
    "installQueuePromptHook",
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
  const fixture = createFixture();
  const { NodeType, returns } = createNodeType(fixture.trace);
  const generatorOnlyHooks = {
    onSerialize: NodeType.prototype.onSerialize,
    onExecuted: NodeType.prototype.onExecuted,
    onResize: NodeType.prototype.onResize,
    onRemoved: NodeType.prototype.onRemoved,
  };
  await fixture.runtime.beforeRegisterNodeDef(NodeType, { name: INPUT_NODE_TYPE });
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
