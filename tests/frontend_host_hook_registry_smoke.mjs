import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const registry = await import(dataModule(
  "../web/js/lifecycle/host_hook_registry.js",
));
const loraSaveSync = await import(dataModule(
  "../web/js/lora_preset/save_sync.js",
));
const aioQueueRuntime = await import(dataModule(
  "../web/js/aio/generator_queue_runtime.js",
));

assert.deepEqual(Object.keys(registry).sort(), [
  "createHostHookRuntimeLifecycle",
  "registerHostHookCallbacks",
]);

{
  const events = [];
  const returnValue = { serialized: true };
  const firstArg = { first: true };
  const secondArg = { second: true };
  const receiver = { receiver: true };
  const serializeHost = {
    serialize(...args) {
      events.push(["original", this, args]);
      return returnValue;
    },
  };
  const original = serializeHost.serialize;
  const ownerA = Symbol("serialize-a");
  const ownerB = Symbol("serialize-b");
  const disposeA = registry.registerHostHookCallbacks({
    owner: ownerA,
    serializeHost,
    beforeSerialize: (context) => events.push(["a", context.thisArg, context.args]),
  });
  const installed = serializeHost.serialize;
  const disposeDuplicate = registry.registerHostHookCallbacks({
    owner: ownerA,
    serializeHost,
    beforeSerialize: () => events.push(["duplicate"]),
  });
  const disposeB = registry.registerHostHookCallbacks({
    owner: ownerB,
    serializeHost,
    beforeSerialize: (context) => events.push(["b", context.thisArg, context.args]),
  });

  assert.equal(serializeHost.serialize, installed);
  assert.equal(disposeDuplicate(), false, "duplicate setup must not own the existing callback");
  assert.equal(serializeHost.serialize.call(receiver, firstArg, secondArg), returnValue);
  assert.deepEqual(events, [
    ["b", receiver, [firstArg, secondArg]],
    ["a", receiver, [firstArg, secondArg]],
    ["original", receiver, [firstArg, secondArg]],
  ]);

  assert.equal(disposeB(), true);
  assert.equal(serializeHost.serialize, installed);
  events.length = 0;
  serializeHost.serialize.call(receiver, firstArg);
  assert.deepEqual(events.map(([name]) => name), ["a", "original"]);
  assert.equal(disposeA(), true);
  assert.equal(serializeHost.serialize, original, "last callback must restore the original hook");
  assert.equal(disposeA(), false);

  const callbackError = new Error("before serialize failed");
  let originalCalls = 0;
  serializeHost.serialize = function () {
    originalCalls += 1;
  };
  const failingOriginal = serializeHost.serialize;
  const disposeFailure = registry.registerHostHookCallbacks({
    owner: Symbol("serialize-failure"),
    serializeHost,
    beforeSerialize() {
      throw callbackError;
    },
  });
  assert.throws(() => serializeHost.serialize(), (error) => error === callbackError);
  assert.equal(originalCalls, 0, "a legacy before-hook failure must still prevent serialize");
  disposeFailure();
  assert.equal(serializeHost.serialize, failingOriginal);
}

{
  const events = [];
  const returnValue = Symbol("clear-result");
  const clearError = new Error("clear failed");
  let fail = false;
  const graph = {
    clear(...args) {
      events.push(["original", this, args]);
      if (fail) {
        throw clearError;
      }
      return returnValue;
    },
  };
  const original = graph.clear;
  const disposeA = registry.registerHostHookCallbacks({
    owner: Symbol("clear-a"),
    graphHost: graph,
    onGraphClear: () => events.push(["a"]),
  });
  const installed = graph.clear;
  const disposeB = registry.registerHostHookCallbacks({
    owner: Symbol("clear-b"),
    graphHost: graph,
    onGraphClear: () => events.push(["b"]),
  });
  const receiver = { graph: true };
  const arg = { clear: true };
  assert.equal(graph.clear.call(receiver, arg), returnValue);
  assert.deepEqual(events, [
    ["original", receiver, [arg]],
    ["a"],
    ["b"],
  ]);

  events.length = 0;
  fail = true;
  assert.throws(() => graph.clear.call(receiver, arg), (error) => error === clearError);
  assert.deepEqual(events, [["original", receiver, [arg]]]);
  disposeB();
  assert.equal(graph.clear, installed);
  disposeA();
  assert.equal(graph.clear, original);
}

{
  const events = [];
  const returnValue = { queued: true };
  const receiver = { queue: true };
  const firstArg = { first: true };
  const secondArg = { second: true };
  const queueHost = {
    queuePrompt(...args) {
      events.push(["original", this, args]);
      return returnValue;
    },
  };
  const original = queueHost.queuePrompt;
  const disposeA = registry.registerHostHookCallbacks({
    owner: Symbol("queue-sync-a"),
    queueHost,
    beforeQueue: (context) => events.push(["a", context.thisArg, context.args]),
  });
  const disposeB = registry.registerHostHookCallbacks({
    owner: Symbol("queue-sync-b"),
    queueHost,
    beforeQueue: (context) => events.push(["b", context.thisArg, context.args]),
  });
  const result = queueHost.queuePrompt.call(receiver, firstArg, secondArg);
  assert.equal(result, returnValue);
  assert.equal(typeof result?.then, "undefined", "before-only queue hooks must stay synchronous");
  assert.deepEqual(events, [
    ["b", receiver, [firstArg, secondArg]],
    ["a", receiver, [firstArg, secondArg]],
    ["original", receiver, [firstArg, secondArg]],
  ]);
  disposeB();
  disposeA();
  assert.equal(queueHost.queuePrompt, original);
}

{
  const events = [];
  const resolved = { prompt_id: "resolved" };
  const rejected = new Error("queue rejected");
  const thrown = new Error("queue threw");
  let mode = "resolve";
  const queueHost = {
    queuePrompt(...args) {
      events.push(["original", this, args]);
      if (mode === "reject") {
        return Promise.reject(rejected);
      }
      if (mode === "throw") {
        throw thrown;
      }
      return resolved;
    },
  };
  const receiver = { queue: true };
  const arg = { prompt: true };
  const registerOwner = (name) => registry.registerHostHookCallbacks({
    owner: Symbol(name),
    queueHost,
    beforeQueue(context) {
      events.push([`${name}:before`, context.thisArg, context.args]);
      return `${name}:state`;
    },
    afterQueue(context) {
      events.push([
        `${name}:after`,
        context.ok,
        context.callbackState,
        context.ok ? context.result : context.error,
      ]);
    },
  });
  const disposeA = registerOwner("a");
  const disposeB = registerOwner("b");

  const pending = queueHost.queuePrompt.call(receiver, arg);
  assert.equal(typeof pending.then, "function", "afterQueue ownership must preserve async wrapping");
  assert.equal(await pending, resolved);
  assert.deepEqual(events, [
    ["b:before", receiver, [arg]],
    ["a:before", receiver, [arg]],
    ["original", receiver, [arg]],
    ["a:after", true, "a:state", resolved],
    ["b:after", true, "b:state", resolved],
  ]);

  events.length = 0;
  mode = "reject";
  await assert.rejects(queueHost.queuePrompt.call(receiver, arg), (error) => error === rejected);
  assert.deepEqual(events.map(([name]) => name), [
    "b:before", "a:before", "original", "a:after", "b:after",
  ]);
  assert.equal(events[3][3], rejected);
  assert.equal(events[4][3], rejected);

  events.length = 0;
  mode = "throw";
  await assert.rejects(queueHost.queuePrompt.call(receiver, arg), (error) => error === thrown);
  assert.deepEqual(events.map(([name]) => name), [
    "b:before", "a:before", "original", "a:after", "b:after",
  ]);
  disposeB();
  disposeA();
}

{
  const beforeError = new Error("before queue failed");
  const afterError = new Error("after queue failed");
  let originalCalls = 0;
  const host = {
    queuePrompt() {
      originalCalls += 1;
      return "queued";
    },
  };
  const disposeBeforeFailure = registry.registerHostHookCallbacks({
    owner: Symbol("queue-before-failure"),
    queueHost: host,
    beforeQueue() {
      throw beforeError;
    },
    afterQueue() {
      throw new Error("afterQueue must not run when its own beforeQueue fails");
    },
  });
  await assert.rejects(host.queuePrompt(), (error) => error === beforeError);
  assert.equal(originalCalls, 0);
  disposeBeforeFailure();

  const disposeAfterFailure = registry.registerHostHookCallbacks({
    owner: Symbol("queue-after-failure"),
    queueHost: host,
    afterQueue() {
      throw afterError;
    },
  });
  await assert.rejects(host.queuePrompt(), (error) => error === afterError);
  assert.equal(originalCalls, 1, "afterQueue failure must occur after the original resolves");
  disposeAfterFailure();
}

{
  let callbackCalls = 0;
  let originalCalls = 0;
  const host = {
    queuePrompt() {
      originalCalls += 1;
      return originalCalls;
    },
  };
  const original = host.queuePrompt;
  const dispose = registry.registerHostHookCallbacks({
    owner: Symbol("identity-guard"),
    queueHost: host,
    beforeQueue: () => { callbackCalls += 1; },
  });
  const registryWrapper = host.queuePrompt;
  host.queuePrompt = function (...args) {
    return registryWrapper.apply(this, args);
  };
  const foreignWrapper = host.queuePrompt;
  assert.equal(dispose(), true);
  assert.equal(host.queuePrompt, foreignWrapper, "dispose must not overwrite a foreign outer wrapper");
  assert.equal(host.queuePrompt(), 1);
  assert.equal(callbackCalls, 0, "disposed callbacks must not survive in a hidden wrapper");

  host.queuePrompt = registryWrapper;
  const disposeRevived = registry.registerHostHookCallbacks({
    owner: Symbol("revived-stale-wrapper"),
    queueHost: host,
    beforeQueue: () => { callbackCalls += 1; },
  });
  assert.equal(host.queuePrompt, registryWrapper, "a stale current wrapper must be reused, not stacked");
  assert.equal(host.queuePrompt(), 2);
  assert.equal(callbackCalls, 1);
  disposeRevived();
  assert.equal(host.queuePrompt, original);
}

{
  const events = [];
  const host = {
    serialize(value) {
      events.push("original");
      return value;
    },
  };
  const original = host.serialize;
  const disposeA = registry.registerHostHookCallbacks({
    owner: Symbol("interleaved-serialize-a"),
    serializeHost: host,
    beforeSerialize: () => events.push("a"),
  });
  const registryA = host.serialize;
  host.serialize = function (...args) {
    events.push("legacy");
    return registryA.apply(this, args);
  };
  const legacy = host.serialize;
  const disposeB = registry.registerHostHookCallbacks({
    owner: Symbol("interleaved-serialize-b"),
    serializeHost: host,
    beforeSerialize: () => events.push("b"),
  });

  assert.notEqual(host.serialize, legacy, "a new owner must be reachable above a foreign wrapper");
  assert.equal(host.serialize("value"), "value");
  assert.deepEqual(events, ["b", "legacy", "a", "original"]);
  assert.equal(disposeB(), true);
  assert.equal(host.serialize, legacy, "the outer segment must restore the foreign wrapper");
  assert.equal(disposeA(), true);
  assert.equal(host.serialize, legacy, "an inner disposer must not overwrite a foreign wrapper");
  events.length = 0;
  assert.equal(host.serialize("after-dispose"), "after-dispose");
  assert.deepEqual(events, ["legacy", "original"], "a stale inner wrapper kept its callback");
  assert.notEqual(host.serialize, original);
}

{
  const events = [];
  const resolved = { prompt_id: "interleaved" };
  const host = {
    queuePrompt() {
      events.push("original");
      return Promise.resolve(resolved);
    },
  };
  const disposeA = registry.registerHostHookCallbacks({
    owner: Symbol("interleaved-queue-a"),
    queueHost: host,
    beforeQueue: () => { events.push("a:before"); return "a"; },
    afterQueue: () => events.push("a:after"),
  });
  const registryA = host.queuePrompt;
  host.queuePrompt = async function (...args) {
    events.push("legacy:before");
    const result = await registryA.apply(this, args);
    events.push("legacy:after");
    return result;
  };
  const legacy = host.queuePrompt;
  const disposeB = registry.registerHostHookCallbacks({
    owner: Symbol("interleaved-queue-b"),
    queueHost: host,
    beforeQueue: () => { events.push("b:before"); return "b"; },
    afterQueue: () => events.push("b:after"),
  });

  assert.equal(await host.queuePrompt(), resolved);
  assert.deepEqual(events, [
    "b:before",
    "legacy:before",
    "a:before",
    "original",
    "a:after",
    "legacy:after",
    "b:after",
  ]);

  events.length = 0;
  assert.equal(disposeA(), true, "an inner segment must be independently disposable");
  assert.equal(await host.queuePrompt(), resolved);
  assert.deepEqual(events, [
    "b:before", "legacy:before", "original", "legacy:after", "b:after",
  ]);
  assert.equal(disposeB(), true);
  assert.equal(host.queuePrompt, legacy);
}

{
  const events = [];
  const graph = {
    clear() {
      events.push("original");
      return "cleared";
    },
  };
  const disposeA = registry.registerHostHookCallbacks({
    owner: Symbol("interleaved-clear-a"),
    graphHost: graph,
    onGraphClear: () => events.push("a"),
  });
  const registryA = graph.clear;
  graph.clear = function (...args) {
    events.push("legacy:before");
    const result = registryA.apply(this, args);
    events.push("legacy:after");
    return result;
  };
  const legacy = graph.clear;
  const disposeB = registry.registerHostHookCallbacks({
    owner: Symbol("interleaved-clear-b"),
    graphHost: graph,
    onGraphClear: () => events.push("b"),
  });

  assert.equal(graph.clear(), "cleared");
  assert.deepEqual(events, ["legacy:before", "original", "a", "legacy:after", "b"]);
  assert.equal(disposeA(), true);
  events.length = 0;
  assert.equal(graph.clear(), "cleared");
  assert.deepEqual(events, ["legacy:before", "original", "legacy:after", "b"]);
  assert.equal(disposeB(), true);
  assert.equal(graph.clear, legacy);
}

{
  const events = [];
  const host = {
    queuePrompt(value) {
      events.push("original");
      return value;
    },
  };
  const disposeA = registry.registerHostHookCallbacks({
    owner: Symbol("non-delegating-a"),
    queueHost: host,
    beforeQueue: () => events.push("a"),
  });
  const hiddenRegistryA = host.queuePrompt;
  host.queuePrompt = function (value) {
    events.push("foreign");
    return value;
  };
  const foreign = host.queuePrompt;
  const disposeB = registry.registerHostHookCallbacks({
    owner: Symbol("non-delegating-b"),
    queueHost: host,
    beforeQueue: () => events.push("b"),
  });

  assert.equal(host.queuePrompt("reachable"), "reachable");
  assert.deepEqual(events, ["b", "foreign"], "the new owner was hidden below a replacement");
  assert.equal(disposeB(), true);
  assert.equal(host.queuePrompt, foreign);
  assert.equal(disposeA(), true);
  events.length = 0;
  assert.equal(hiddenRegistryA("stale"), "stale");
  assert.deepEqual(events, ["original"], "an inactive hidden segment retained callbacks");
}

{
  const events = [];
  const runtimeOwner = Symbol("runtime-owner");
  const callbackOwner = Symbol("runtime-callback");
  const host = {
    queuePrompt(value) {
      events.push("original");
      return value;
    },
  };
  const original = host.queuePrompt;
  const install = (lifecycle, label, options) => lifecycle.install(
    "queue",
    () => registry.registerHostHookCallbacks({
      owner: callbackOwner,
      queueHost: host,
      beforeQueue: () => events.push(label),
    }),
    options,
  );

  const firstRuntime = registry.createHostHookRuntimeLifecycle(host, runtimeOwner);
  assert.equal(install(firstRuntime, "first"), true);
  const firstWrapper = host.queuePrompt;
  assert.equal(install(firstRuntime, "ignored"), false, "setup twice must reuse its lease");
  assert.equal(host.queuePrompt, firstWrapper);
  host.queuePrompt("first-call");
  assert.deepEqual(events, ["first", "original"]);

  events.length = 0;
  assert.equal(install(firstRuntime, "first-replaced", { replace: true }), true);
  host.queuePrompt("first-replaced-call");
  assert.deepEqual(
    events,
    ["first-replaced", "original"],
    "an explicit lease replacement kept the prior callback closure",
  );

  events.length = 0;
  const secondRuntime = registry.createHostHookRuntimeLifecycle(host, runtimeOwner);
  assert.equal(install(secondRuntime, "second"), true);
  host.queuePrompt("second-call");
  assert.deepEqual(events, ["second", "original"], "runtime replacement kept the stale closure");
  assert.equal(firstRuntime.dispose(), false, "a superseded runtime must not release the new lease");
  assert.equal(secondRuntime.dispose(), true);
  assert.equal(host.queuePrompt, original);

  events.length = 0;
  assert.equal(install(secondRuntime, "second-reinstalled"), true);
  host.queuePrompt("reinstalled-call");
  assert.deepEqual(events, ["second-reinstalled", "original"]);
  assert.equal(secondRuntime.dispose(), true);
  assert.equal(host.queuePrompt, original);
}

function exerciseLoraLegacyLoadOrder(registryFirst) {
  const events = [];
  class Graph {
    constructor() {
      this._nodes = [{ comfyClass: "EasyUseAnimaLoraPreset" }];
    }

    serialize(value) {
      events.push("original:serialize");
      return value;
    }
  }
  const app = {
    graph: new Graph(),
    queuePrompt(value) {
      events.push("original:queue");
      return value;
    },
  };
  const legacy = loraSaveSync.createLoraPresetSaveSync({
    app,
    nodeTypeName: "EasyUseAnimaLoraPreset",
    saveCurrentProfile: () => events.push("legacy"),
    getGraphPrototype: () => Graph.prototype,
  });
  const installRegistry = () => registry.registerHostHookCallbacks({
    owner: Symbol(`lora-registry-${registryFirst}`),
    serializeHost: Graph.prototype,
    queueHost: app,
    beforeSerialize: () => events.push("registry"),
    beforeQueue: () => events.push("registry"),
  });

  let disposeRegistry;
  let legacySerialize;
  let legacyQueue;
  if (registryFirst) {
    disposeRegistry = installRegistry();
    legacy.install();
    legacySerialize = Graph.prototype.serialize;
    legacyQueue = app.queuePrompt;
  } else {
    legacy.install();
    legacySerialize = Graph.prototype.serialize;
    legacyQueue = app.queuePrompt;
    disposeRegistry = installRegistry();
  }
  Graph.prototype.serialize.call(app.graph, "serialize");
  app.queuePrompt.call(app, "queue");
  const expectedCall = registryFirst
    ? ["legacy", "registry", "original:serialize", "legacy", "registry", "original:queue"]
    : ["registry", "legacy", "original:serialize", "registry", "legacy", "original:queue"];
  assert.deepEqual(events, expectedCall);

  events.length = 0;
  disposeRegistry();
  assert.equal(Graph.prototype.serialize, legacySerialize);
  assert.equal(app.queuePrompt, legacyQueue);
  Graph.prototype.serialize.call(app.graph, "serialize");
  app.queuePrompt.call(app, "queue");
  assert.deepEqual(events, ["legacy", "original:serialize", "legacy", "original:queue"]);
}

exerciseLoraLegacyLoadOrder(false);
exerciseLoraLegacyLoadOrder(true);

function exerciseAioLegacyLoadOrder(registryFirst) {
  const events = [];
  const host = {
    queuePrompt(value) {
      events.push("original");
      return value;
    },
  };
  const runtime = {
    wrapQueuePrompt(queuePrompt) {
      return function (...args) {
        events.push("legacy");
        return queuePrompt.apply(this, args);
      };
    },
  };
  const installRegistry = () => registry.registerHostHookCallbacks({
    owner: Symbol(`aio-registry-${registryFirst}`),
    queueHost: host,
    beforeQueue: () => events.push("registry"),
  });
  let disposeRegistry;
  let legacyWrapper;
  if (registryFirst) {
    disposeRegistry = installRegistry();
    aioQueueRuntime.aioInstallGeneratorQueuePromptHook(host, runtime);
    legacyWrapper = host.queuePrompt;
  } else {
    aioQueueRuntime.aioInstallGeneratorQueuePromptHook(host, runtime);
    legacyWrapper = host.queuePrompt;
    disposeRegistry = installRegistry();
  }
  assert.equal(host.queuePrompt("queued"), "queued");
  assert.deepEqual(
    events,
    registryFirst ? ["legacy", "registry", "original"] : ["registry", "legacy", "original"],
  );

  events.length = 0;
  disposeRegistry();
  assert.equal(host.queuePrompt, legacyWrapper);
  assert.equal(host.queuePrompt("queued"), "queued");
  assert.deepEqual(events, ["legacy", "original"]);
}

exerciseAioLegacyLoadOrder(false);
exerciseAioLegacyLoadOrder(true);

console.log("Host hook registry smoke passed.");
