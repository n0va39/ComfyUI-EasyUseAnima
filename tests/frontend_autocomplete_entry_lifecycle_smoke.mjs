import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function captureOf(options) {
  return options === true || !!options?.capture;
}

class FakeTarget {
  constructor() {
    this.listeners = new Map();
  }

  addEventListener(type, listener, options = false) {
    const records = this.listeners.get(type) || [];
    records.push({ listener, capture: captureOf(options) });
    this.listeners.set(type, records);
  }

  removeEventListener(type, listener, options = false) {
    const capture = captureOf(options);
    const records = this.listeners.get(type) || [];
    this.listeners.set(
      type,
      records.filter((record) => record.listener !== listener || record.capture !== capture),
    );
  }

  listenerCount(type = null) {
    if (type) {
      return (this.listeners.get(type) || []).length;
    }
    return [...this.listeners.values()].reduce((total, records) => total + records.length, 0);
  }

  emit(type, values = {}) {
    const event = { type, target: this, ...values };
    for (const { listener } of [...(this.listeners.get(type) || [])]) {
      listener.call(this, event);
    }
    return event;
  }
}

const lifecycleModule = await import(
  dataModule("../web/js/autocomplete/entry_lifecycle.js")
);
assert.deepEqual(Object.keys(lifecycleModule).sort(), [
  "createAutocompleteEntryLifecycle",
  "disposeExternalAutocompleteInput",
  "disposeExternalAutocompleteInputs",
  "registerExternalAutocompleteInput",
]);

const {
  createAutocompleteEntryLifecycle,
  disposeExternalAutocompleteInput,
  disposeExternalAutocompleteInputs,
  registerExternalAutocompleteInput,
} = lifecycleModule;

const entrySource = readFileSync(
  new URL("../web/js/easyuse_anima_autocomplete.js", import.meta.url),
  "utf8",
);
assert.match(entrySource, /createAutocompleteEntryLifecycle\(\{/);
assert.match(entrySource, /autocompleteEntryLifecycle\.install\(\)/);
assert.match(entrySource, /autocompleteEntryLifecycle\.installNodeTypeHooks\(nodeType, nodeData\)/);
assert.doesNotMatch(entrySource, /document\.addEventListener\("(?:focusin|scroll|wheel|pointerdown|mousedown|selectionchange)"/);
assert.doesNotMatch(entrySource, /window\.addEventListener\("(?:resize|easyuse-anima-settings-updated)"/);

for (const relativePath of [
  "../web/js/prompt_studio/advanced_node_ui.js",
  "../web/js/prompt_studio/regional/field_editor.js",
  "../web/js/prompt_studio/regional/extension.js",
]) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  assert.match(source, /disposeExternalAutocompleteInputs\(/, `${relativePath} must dispose external inputs`);
}
const promptStudioNodeHooksSource = readFileSync(
  new URL("../web/js/prompt_studio/node_hooks.js", import.meta.url),
  "utf8",
);
const promptStudioRuntimeSource = readFileSync(
  new URL("../web/js/prompt_studio/extension_runtime.js", import.meta.url),
  "utf8",
);
assert.match(promptStudioNodeHooksSource, /hooks\.disposeAdvancedAutocompleteInputs\?\.\(this\)/);
assert.match(promptStudioRuntimeSource, /disposeAdvancedAutocompleteInputs,/);

function createRuntime(hostWindow, hostDocument, name) {
  const calls = {
    disposedInputs: 0,
    disposedUi: 0,
    focused: [],
    hookedInputs: [],
    hookedNodes: [],
    settings: 0,
  };
  const timers = new Map();
  let nextTimer = 1;
  const runtime = createAutocompleteEntryLifecycle({
    hostWindow,
    hostDocument,
    hookInput(input, options) {
      calls.hookedInputs.push({ input, options });
      let disposed = false;
      return () => {
        if (!disposed) {
          disposed = true;
          input.disposedBy = name;
        }
      };
    },
    hookFocusedInput(input) {
      calls.focused.push(input);
    },
    entryTooltip(entry) {
      return `${name}:${entry.tag}`;
    },
    handleScroll() {},
    handleWheel() {},
    handleOutsidePointer() {},
    handleSelectionChange() {},
    handleResize() {},
    handleSettingsUpdated() {
      calls.settings += 1;
    },
    hookNode(node, nodeData) {
      calls.hookedNodes.push({ node, nodeData });
    },
    disposeInputs() {
      calls.disposedInputs += 1;
    },
    disposeUi() {
      calls.disposedUi += 1;
    },
    setTimer(callback, delay) {
      const handle = nextTimer++;
      timers.set(handle, { callback, delay });
      return handle;
    },
    clearTimer(handle) {
      timers.delete(handle);
    },
  });
  return { calls, runtime, timers };
}

{
  const hostWindow = new FakeTarget();
  const hostDocument = new FakeTarget();
  const focusedInput = { id: "focused" };
  const pendingInput = { id: "pending" };
  hostDocument.activeElement = focusedInput;
  let pendingDispose = null;
  hostWindow.__easyuseAnimaPendingAutocompleteInputs = [{
    input: pendingInput,
    options: { scope: "easyuse" },
    onBound(dispose) {
      pendingDispose = dispose;
    },
  }];

  const first = createRuntime(hostWindow, hostDocument, "first");
  assert.equal(first.runtime.install(), true);
  assert.equal(hostDocument.listenerCount(), 6, "one owner must install one document listener set");
  assert.equal(hostWindow.listenerCount(), 2, "one owner must install resize and settings listeners");
  assert.equal(first.calls.hookedInputs.length, 1, "pending inputs must bind during install");
  assert.equal(typeof pendingDispose, "function");
  assert.deepEqual(first.calls.focused, [focusedInput]);
  assert.equal(first.runtime.install(), false, "same-owner re-entry must be idempotent");
  assert.equal(hostDocument.listenerCount(), 6);
  assert.equal(hostWindow.listenerCount(), 2);

  const externalInput = { id: "external" };
  const externalDispose = hostWindow.easyuseAnimaHookAutocompleteInput(externalInput, { scope: "compatible" });
  assert.equal(typeof externalDispose, "function");
  assert.equal(hostWindow.easyuseAnimaAutocompleteEntryTooltip({ tag: "tag" }), "first:tag");

  const originalCalls = [];
  class NodeType {}
  NodeType.prototype.onNodeCreated = function (value) {
    originalCalls.push(["created", this, value]);
    return `created:${value}`;
  };
  NodeType.prototype.onConfigure = function (value) {
    originalCalls.push(["configured", this, value]);
    return `configured:${value}`;
  };
  const originalCreated = NodeType.prototype.onNodeCreated;
  const originalConfigure = NodeType.prototype.onConfigure;
  const nodeData = { name: "Prompt" };
  assert.equal(first.runtime.installNodeTypeHooks(NodeType, nodeData), true);
  assert.equal(first.runtime.installNodeTypeHooks(NodeType, nodeData), false);
  const node = new NodeType();
  assert.equal(node.onNodeCreated("a"), "created:a");
  assert.equal(node.onConfigure("b"), "configured:b");
  assert.deepEqual(originalCalls.map((call) => [call[0], call[2]]), [
    ["created", "a"],
    ["configured", "b"],
  ]);
  assert.equal(originalCalls.every((call) => call[1] === node), true, "wrappers must preserve this");
  assert.equal(first.calls.hookedNodes.length, 2);

  class BaseNode {}
  BaseNode.prototype.onNodeCreated = function () { return "base"; };
  class InheritedNode extends BaseNode {}
  assert.equal(Object.hasOwn(InheritedNode.prototype, "onNodeCreated"), false);
  assert.equal(first.runtime.installNodeTypeHooks(InheritedNode, nodeData), true);
  assert.equal(new InheritedNode().onNodeCreated(), "base");
  assert.equal(Object.hasOwn(InheritedNode.prototype, "onNodeCreated"), true);

  let staleTimerCalls = 0;
  first.runtime.schedule(() => { staleTimerCalls += 1; }, 80);
  assert.deepEqual([...first.timers.values()].map((entry) => entry.delay), [80]);

  const second = createRuntime(hostWindow, hostDocument, "second");
  assert.equal(second.runtime.install(), true, "a new owner must replace the previous owner");
  assert.equal(first.calls.disposedInputs, 1);
  assert.equal(first.calls.disposedUi, 1);
  assert.equal(first.timers.size, 0, "owner replacement must cancel retry timers");
  assert.equal(staleTimerCalls, 0);
  assert.equal(NodeType.prototype.onNodeCreated, originalCreated, "replacement must restore old wrappers");
  assert.equal(NodeType.prototype.onConfigure, originalConfigure);
  assert.equal(
    Object.hasOwn(InheritedNode.prototype, "onNodeCreated"),
    false,
    "teardown must restore an inherited hook without leaving an own property",
  );
  assert.equal(hostDocument.listenerCount(), 6, "replacement must leave one document listener set");
  assert.equal(hostWindow.listenerCount(), 2, "replacement must leave one window listener set");
  assert.equal(hostWindow.easyuseAnimaAutocompleteEntryTooltip({ tag: "tag" }), "second:tag");
  hostWindow.emit("easyuse-anima-settings-updated");
  assert.equal(first.calls.settings, 0);
  assert.equal(second.calls.settings, 1, "only the current owner may receive settings events");

  assert.equal(second.runtime.installNodeTypeHooks(NodeType, nodeData), true);
  assert.equal(second.runtime.installNodeTypeHooks(InheritedNode, nodeData), true);
  const secondWrapper = NodeType.prototype.onNodeCreated;
  first.runtime.dispose();
  assert.equal(NodeType.prototype.onNodeCreated, secondWrapper, "a stale disposer must not clear the new wrapper");
  assert.equal(hostDocument.listenerCount(), 6);
  assert.equal(hostWindow.listenerCount(), 2);

  second.runtime.dispose();
  second.runtime.dispose();
  assert.equal(hostDocument.listenerCount(), 0);
  assert.equal(hostWindow.listenerCount(), 0);
  assert.equal(NodeType.prototype.onNodeCreated, originalCreated);
  assert.equal(NodeType.prototype.onConfigure, originalConfigure);
  assert.equal(Object.hasOwn(InheritedNode.prototype, "onNodeCreated"), false);
  assert.equal(hostWindow.easyuseAnimaHookAutocompleteInput, undefined);
  assert.equal(hostWindow.easyuseAnimaAutocompleteEntryTooltip, undefined);
  assert.equal(second.calls.disposedInputs, 1, "teardown must be idempotent");
  assert.equal(second.calls.disposedUi, 1);
  externalDispose();
  pendingDispose();
}

{
  const hostWindow = {};
  const pendingInput = {};
  const pendingDispose = registerExternalAutocompleteInput(hostWindow, pendingInput, { node: 1 });
  assert.equal(hostWindow.__easyuseAnimaPendingAutocompleteInputs.length, 1);
  pendingDispose();
  assert.equal(hostWindow.__easyuseAnimaPendingAutocompleteInputs.length, 0, "pending disposal must remove its queue entry");

  let oldDisposed = 0;
  let oldDone = false;
  const boundInput = {};
  hostWindow.easyuseAnimaHookAutocompleteInput = (input) => {
    const dispose = () => {
      if (!oldDone) {
        oldDone = true;
        oldDisposed += 1;
      }
    };
    input.__easyuseAnimaAutocompleteDispose = dispose;
    return dispose;
  };
  const callSiteDispose = registerExternalAutocompleteInput(hostWindow, boundInput, {});
  assert.equal(typeof callSiteDispose, "function");
  let replacementDisposed = 0;
  boundInput.__easyuseAnimaAutocompleteDispose = () => { replacementDisposed += 1; };
  callSiteDispose();
  assert.equal(oldDisposed, 1, "the call site must release its originally bound owner");
  assert.equal(replacementDisposed, 1, "the call site must also release a replacement entry binding");
  assert.equal(boundInput.__easyuseAnimaExternalAutocompleteDispose, undefined);

  const first = {};
  const second = {};
  let firstDisposed = 0;
  let secondDisposed = 0;
  first.__easyuseAnimaAutocompleteDispose = () => { firstDisposed += 1; };
  second.__easyuseAnimaAutocompleteDispose = () => { secondDisposed += 1; };
  disposeExternalAutocompleteInputs(hostWindow, {
    querySelectorAll() {
      return [first, second];
    },
  });
  assert.equal(firstDisposed, 1);
  assert.equal(secondDisposed, 1);
  disposeExternalAutocompleteInput(hostWindow, null);
}

console.log("Autocomplete entry lifecycle smoke passed.");
