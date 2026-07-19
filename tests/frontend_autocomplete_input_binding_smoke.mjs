import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function captureOf(options) {
  return options === true || !!options?.capture;
}

function createEvent(values = {}) {
  return {
    type: "",
    key: "",
    button: 0,
    shiftKey: false,
    defaultPrevented: false,
    propagationStopped: false,
    preventDefault() {
      this.defaultPrevented = true;
    },
    stopPropagation() {
      this.propagationStopped = true;
    },
    ...values,
  };
}

class FakeInput {
  constructor() {
    this.listeners = new Map();
    this.isConnected = true;
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

  listenerLedger() {
    return [...this.listeners.entries()].map(([type, records]) => [
      type,
      records.map((record) => record.capture),
    ]);
  }

  emit(type, values = {}) {
    const event = createEvent({ type, ...values });
    for (const { listener } of [...(this.listeners.get(type) || [])]) {
      listener.call(this, event);
    }
    return event;
  }
}

const entrySource = readFileSync(
  new URL("../web/js/easyuse_anima_autocomplete.js", import.meta.url),
  "utf8",
);

function createDisconnectedInputPruner(registry, disposeInput) {
  const functionStart = entrySource.indexOf("function pruneDisconnectedAutocompleteInputs");
  const functionEnd = entrySource.indexOf("\nfunction syncAutocompleteInputFlags", functionStart);
  assert.ok(functionStart >= 0 && functionEnd > functionStart);
  return new Function(
    "hookedAutocompleteInputs",
    "disposeAutocompleteInput",
    `"use strict";\n${entrySource.slice(functionStart, functionEnd)}\nreturn pruneDisconnectedAutocompleteInputs;`,
  )(registry, disposeInput);
}

function createAutocompleteInputDisposer(registry) {
  const functionStart = entrySource.indexOf("function disposeAutocompleteInput");
  const functionEnd = entrySource.indexOf("\nfunction pruneDisconnectedAutocompleteInputs", functionStart);
  assert.ok(functionStart >= 0 && functionEnd > functionStart);
  return new Function(
    "hookedAutocompleteInputs",
    "activeState",
    "hidePopup",
    "clearAutocompletePreview",
    `"use strict";\n${entrySource.slice(functionStart, functionEnd)}\nreturn disposeAutocompleteInput;`,
  )(registry, null, () => {}, () => {});
}

const bindingModule = await import(
  dataModule("../web/js/autocomplete/input_binding.js")
);
assert.deepEqual(Object.keys(bindingModule), ["createAutocompleteInputBinding"]);

const { createAutocompleteInputBinding } = bindingModule;

{
  const input = new FakeInput();
  const state = { input };
  const owner = {};
  const registry = new Set();
  let activeState = { input, index: 0, results: ["first", "second"] };
  let compositionEndPending = true;
  const calls = {
    beginComposition: 0,
    cancelMiddlePan: 0,
    caret: 0,
    commit: [],
    dispose: 0,
    endComposition: 0,
    hide: [],
    invalidate: 0,
    schedule: 0,
    setActive: [],
    update: 0,
  };
  const timers = new Map();
  let nextTimer = 1;
  const controller = {
    beginComposition() {
      calls.beginComposition += 1;
    },
    dispose() {
      calls.dispose += 1;
    },
    endComposition() {
      calls.endComposition += 1;
    },
    invalidate() {
      calls.invalidate += 1;
    },
    isComposing(event) {
      return !!event?.composing;
    },
    isCompositionEndUpdatePending() {
      return compositionEndPending;
    },
    scheduleCaretUpdate() {
      calls.caret += 1;
    },
    scheduleUpdate() {
      calls.schedule += 1;
    },
    updateNow() {
      calls.update += 1;
    },
  };

  const binding = createAutocompleteInputBinding({
    input,
    state,
    owner,
    registry,
    controller,
    getActiveState: () => activeState,
    hidePopup: (options = {}) => calls.hide.push(options),
    isTextEditingShortcut: (event) => !!event.shortcut,
    handleBracketPreviewKeydown: (_state, event) => !!event.bracket,
    forwardMiddlePan: (event) => {
      if (!event.middle) {
        return null;
      }
      return () => {
        calls.cancelMiddlePan += 1;
      };
    },
    setActive: (index) => calls.setActive.push(index),
    commitSuggestion: (active, entry, options) => {
      calls.commit.push({ active, entry, options });
    },
    getCommitKey: () => "enter",
    setTimer(callback, delay) {
      const handle = nextTimer++;
      timers.set(handle, { callback, delay });
      return handle;
    },
    clearTimer(handle) {
      timers.delete(handle);
    },
  });

  assert.equal(input.listenerCount(), 18, "one binding must own one exact listener set");
  assert.deepEqual(input.listenerLedger(), [
    ["compositionstart", [false]],
    ["compositionupdate", [false]],
    ["compositionend", [false]],
    ["input", [false]],
    ["focus", [false]],
    ["click", [false]],
    ["mousedown", [false, true]],
    ["mouseup", [false]],
    ["pointerup", [false]],
    ["pointerdown", [true]],
    ["auxclick", [true]],
    ["keyup", [false]],
    ["select", [false]],
    ["blur", [false]],
    ["keydown", [false, false, false]],
  ], "the listener type and capture ledger must remain exact");
  assert.equal(input.__easyuseAnimaAutocompleteState, state);
  assert.equal(input.__easyuseAnimaAutocompleteDispose, state.dispose);
  assert.equal(registry.has(input), true);
  assert.equal(input.listenerCount("mousedown"), 2);
  assert.equal(input.listenerCount("keydown"), 3);

  input.emit("compositionstart");
  input.emit("compositionupdate");
  input.emit("compositionend");
  assert.equal(calls.beginComposition, 1);
  assert.equal(calls.schedule, 1);
  assert.equal(calls.endComposition, 1);

  input.emit("input");
  assert.deepEqual(calls.hide.at(-1), { preserveController: true });
  assert.equal(calls.schedule, 2);
  compositionEndPending = false;

  input.emit("focus");
  input.emit("click");
  input.emit("mousedown");
  input.emit("mouseup");
  input.emit("pointerup");
  input.emit("keyup", { key: "ArrowLeft" });
  input.emit("select");
  assert.equal(calls.update, 1);
  assert.equal(calls.caret, 6);

  input.emit("keydown", { bracket: true });
  assert.equal(calls.caret, 7, "bracket preview must retain its caret refresh");

  const shortcut = input.emit("keydown", { key: "a", shortcut: true });
  assert.equal(shortcut.propagationStopped, true);

  const down = input.emit("keydown", { key: "ArrowDown" });
  const up = input.emit("keydown", { key: "ArrowUp" });
  assert.equal(down.defaultPrevented, true);
  assert.equal(up.defaultPrevented, true);
  assert.deepEqual(calls.setActive, [1, -1]);

  const tab = input.emit("keydown", { key: "Tab" });
  const enter = input.emit("keydown", { key: "Enter" });
  assert.equal(tab.defaultPrevented, true);
  assert.equal(enter.defaultPrevented, true);
  assert.equal(calls.commit.length, 2);
  assert.equal(calls.commit[0].entry, "first");
  assert.deepEqual(calls.commit[0].options, { suppressPopup: true });

  const composingEnter = input.emit("keydown", { key: "Enter", composing: true });
  assert.equal(composingEnter.defaultPrevented, false);
  assert.equal(calls.commit.length, 2);

  const escape = input.emit("keydown", { key: "Escape" });
  assert.equal(escape.defaultPrevented, true);
  assert.equal(calls.invalidate, 1);

  const middle = input.emit("pointerdown", { button: 1, middle: true });
  assert.equal(middle.defaultPrevented, false, "the forwarding dependency owns event cancellation");

  const aux = input.emit("auxclick", { button: 1 });
  assert.equal(aux.defaultPrevented, true);
  assert.equal(aux.propagationStopped, true);

  input.emit("blur");
  assert.equal(calls.invalidate, 2);
  assert.deepEqual([...timers.values()].map((entry) => entry.delay), [120]);
  const firstBlurHandle = [...timers.keys()][0];
  input.emit("blur");
  assert.equal(calls.invalidate, 3);
  assert.equal(timers.has(firstBlurHandle), false, "a repeated blur must replace its timer");
  assert.deepEqual([...timers.values()].map((entry) => entry.delay), [120]);
  const staleBlur = [...timers.values()][0].callback;

  const pruneDisconnected = createDisconnectedInputPruner(
    registry,
    createAutocompleteInputDisposer(registry),
  );
  pruneDisconnected();
  assert.equal(registry.has(input), true, "a connected input must remain registered");
  input.isConnected = false;
  pruneDisconnected(input);
  assert.equal(registry.has(input), true, "the candidate input must survive its own hook pass");
  pruneDisconnected();
  binding.dispose();
  assert.equal(input.listenerCount(), 0, "dispose must remove capture and bubble listeners");
  assert.equal(timers.size, 0, "dispose must cancel the pending blur timer");
  assert.equal(calls.dispose, 1, "controller disposal must be idempotent");
  assert.equal(calls.cancelMiddlePan, 1, "the binding must cancel only its forwarded pan");
  assert.equal(registry.has(input), false);
  assert.equal(input.__easyuseAnimaAutocompleteState, undefined);
  assert.equal(input.__easyuseAnimaAutocompleteHooked, undefined);

  const hideCount = calls.hide.length;
  staleBlur();
  input.emit("input");
  assert.equal(calls.hide.length, hideCount, "disposed timer/listeners must not mutate popup state");

  activeState = null;
}

{
  const connected = new FakeInput();
  const disconnected = new FakeInput();
  const stateless = new FakeInput();
  connected.__easyuseAnimaAutocompleteState = { input: connected };
  disconnected.__easyuseAnimaAutocompleteState = { input: disconnected };
  disconnected.isConnected = false;
  const registry = new Set([connected, disconnected, stateless]);
  const pruneDisconnected = createDisconnectedInputPruner(
    registry,
    createAutocompleteInputDisposer(registry),
  );

  pruneDisconnected(disconnected);
  assert.equal(registry.has(stateless), false, "a stateless marker must be pruned");
  assert.equal(stateless.__easyuseAnimaAutocomplete, false);
  assert.equal(registry.has(connected), true);
  assert.equal(registry.has(disconnected), true, "exceptInput must be preserved while hooking it");

  pruneDisconnected();
  assert.equal(registry.has(connected), true, "connected inputs must remain registered");
  assert.equal(registry.has(disconnected), false, "disconnected inputs must be disposed");
  assert.equal(disconnected.__easyuseAnimaAutocompleteState, undefined);
  assert.equal(disconnected.__easyuseAnimaAutocomplete, false);
}

{
  const functionStart = entrySource.indexOf("function forwardMiddlePanFromAutocompleteInput");
  const functionEnd = entrySource.indexOf("\nfunction commitSuggestion", functionStart);
  assert.ok(functionStart >= 0 && functionEnd > functionStart);

  const documentTarget = new FakeInput();
  let blurCalls = 0;
  documentTarget.activeElement = { blur: () => { blurCalls += 1; } };
  const app = { canvas: { canvas: {} } };
  const dispatches = [];
  const forwardMiddlePan = new Function(
    "app",
    "document",
    "dispatchAutocompleteCanvasPointerEvent",
    "dispatchAutocompleteCanvasMouseEvent",
    `"use strict";\nlet middlePanForwardCleanup = null;\n${entrySource.slice(functionStart, functionEnd)}\nreturn forwardMiddlePanFromAutocompleteInput;`,
  )(
    app,
    documentTarget,
    (type, event, overrides) => dispatches.push(["pointer", type, event, overrides]),
    (type, event, overrides) => dispatches.push(["mouse", type, event, overrides]),
  );

  const firstDown = createEvent({ button: 1 });
  const firstCleanup = forwardMiddlePan(firstDown);
  assert.equal(typeof firstCleanup, "function");
  assert.equal(firstDown.defaultPrevented, true);
  assert.equal(firstDown.propagationStopped, true);
  assert.equal(blurCalls, 1);
  assert.deepEqual(dispatches.map((entry) => entry.slice(0, 2)), [
    ["pointer", "pointerdown"],
    ["mouse", "mousedown"],
  ]);
  assert.deepEqual(documentTarget.listenerLedger(), [
    ["pointermove", [true]],
    ["pointerup", [true]],
    ["pointercancel", [true]],
    ["mousemove", [true]],
    ["mouseup", [true]],
  ]);

  const repeatedDown = createEvent({ button: 1 });
  assert.equal(forwardMiddlePan(repeatedDown), firstCleanup);
  assert.equal(repeatedDown.defaultPrevented, true);
  assert.equal(dispatches.length, 2, "an active pan must not dispatch a second down pair");
  assert.equal(documentTarget.listenerCount(), 5, "an active pan must retain one document listener set");

  documentTarget.emit("pointermove", { button: 1 });
  assert.deepEqual(dispatches.slice(-2).map((entry) => entry.slice(0, 2)), [
    ["pointer", "pointermove"],
    ["mouse", "mousemove"],
  ]);
  documentTarget.emit("pointerup", { button: 1 });
  assert.deepEqual(dispatches.slice(-2).map((entry) => entry.slice(0, 2)), [
    ["pointer", "pointerup"],
    ["mouse", "mouseup"],
  ]);
  assert.equal(documentTarget.listenerCount(), 0, "a natural release must remove every document listener");
  const dispatchCountAfterRelease = dispatches.length;
  firstCleanup();
  assert.equal(dispatches.length, dispatchCountAfterRelease, "cleanup must be idempotent after release");

  const secondDown = createEvent({ button: 1 });
  const secondCleanup = forwardMiddlePan(secondDown);
  const dispatchCountBeforeSyntheticRelease = dispatches.length;
  secondCleanup();
  secondCleanup();
  assert.equal(
    dispatches.length,
    dispatchCountBeforeSyntheticRelease + 2,
    "disposal cleanup must synthesize exactly one release pair",
  );
  assert.equal(documentTarget.listenerCount(), 0, "disposal cleanup must remove every document listener");
  assert.deepEqual(dispatches.slice(-2).map((entry) => entry.slice(0, 2)), [
    ["pointer", "pointerup"],
    ["mouse", "mouseup"],
  ]);

  const forwarded = createEvent({ button: 1, __easyuseAnimaForwarded: true });
  assert.equal(forwardMiddlePan(forwarded), null);
  app.canvas.canvas = null;
  const noCanvas = createEvent({ button: 1 });
  assert.equal(forwardMiddlePan(noCanvas), null);
  assert.equal(noCanvas.defaultPrevented, false);
}

{
  const strictStart = entrySource.indexOf("function strictAutocompleteResults");
  const strictEnd = entrySource.indexOf("\nfunction copyCaretMirrorStyle", strictStart);
  assert.ok(strictStart >= 0 && strictEnd > strictStart);
  const strictAutocompleteResults = new Function(
    `"use strict";\n${entrySource.slice(strictStart, strictEnd)}\nreturn strictAutocompleteResults;`,
  )();
  assert.equal(
    strictAutocompleteResults.length,
    4,
    "the unused state slot must preserve the positional four-argument contract",
  );
}

{
  const bracketStart = entrySource.indexOf("function insertBracketPair");
  const bracketEnd = entrySource.indexOf("\nfunction widgetValueSetterCallsCallback", bracketStart);
  assert.ok(bracketStart >= 0 && bracketEnd > bracketStart);
  const handleBracketPreviewKeydown = new Function(
    "replaceInputRange",
    "syncWidgetValue",
    `"use strict";\nconst autocompletePreviewClosingBrackets = true;\n${entrySource.slice(bracketStart, bracketEnd)}\nreturn handleBracketPreviewKeydown;`,
  )(
    (input, start, end, replacement, caretOffset) => {
      input.value = `${input.value.slice(0, start)}${replacement}${input.value.slice(end)}`;
      input.setSelectionRange(start + caretOffset, start + caretOffset);
    },
    (state) => { state.syncCalls += 1; },
  );

  const input = {
    value: "tag",
    selectionStart: 0,
    selectionEnd: 3,
    setSelectionRange(start, end) {
      this.selectionStart = start;
      this.selectionEnd = end;
    },
  };
  const state = { input, syncCalls: 0 };
  const openEvent = createEvent({ key: "(" });
  assert.equal(handleBracketPreviewKeydown(state, openEvent), true);
  assert.equal(input.value, "(tag)");
  assert.equal(input.selectionStart, 4);
  assert.equal(state.syncCalls, 1);

  input.selectionStart = 4;
  input.selectionEnd = 4;
  const closeEvent = createEvent({ key: ")" });
  assert.equal(handleBracketPreviewKeydown(state, closeEvent), true);
  assert.equal(input.value, "(tag)", "typing an existing closer must not duplicate it");
  assert.equal(input.selectionStart, 5);
  assert.equal(state.syncCalls, 1, "skipping an existing closer must not rewrite widget state");
}

function noOpController(disposeCall) {
  return {
    beginComposition() {},
    dispose: disposeCall,
    endComposition() {},
    invalidate() {},
    isComposing() { return false; },
    isCompositionEndUpdatePending() { return false; },
    scheduleCaretUpdate() {},
    scheduleUpdate() {},
    updateNow() {},
  };
}

function replacementBinding(input, state, owner, registry, controller) {
  return createAutocompleteInputBinding({
    input,
    state,
    owner,
    registry,
    controller,
    getActiveState: () => null,
    hidePopup() {},
    isTextEditingShortcut: () => false,
    handleBracketPreviewKeydown: () => false,
    forwardMiddlePan: () => null,
    setActive() {},
    commitSuggestion() {},
    getCommitKey: () => "enter",
    setTimer: () => 1,
    clearTimer() {},
  });
}

{
  const input = new FakeInput();
  const ownerA = {};
  const ownerB = {};
  const registryA = new Set();
  const registryB = new Set();
  let disposeA = 0;
  let disposeB = 0;
  const stateA = { input };
  const stateB = { input };
  const bindingA = replacementBinding(
    input,
    stateA,
    ownerA,
    registryA,
    noOpController(() => { disposeA += 1; }),
  );
  const staleDispose = stateA.dispose;

  assert.equal(input.listenerCount(), 18);
  assert.equal(registryA.has(input), true);

  const bindingB = replacementBinding(
    input,
    stateB,
    ownerB,
    registryB,
    noOpController(() => { disposeB += 1; }),
  );
  assert.equal(disposeA, 1, "a new owner must dispose the previous binding");
  assert.equal(registryA.has(input), false);
  assert.equal(registryB.has(input), true);
  assert.equal(input.__easyuseAnimaAutocompleteState, stateB);
  assert.equal(input.listenerCount(), 18, "owner replacement must leave one listener set");

  staleDispose();
  assert.equal(input.__easyuseAnimaAutocompleteState, stateB);
  assert.equal(input.listenerCount(), 18, "an old disposer must not clear the new owner");

  bindingA.dispose();
  bindingB.dispose();
  assert.equal(disposeA, 1);
  assert.equal(disposeB, 1);
  assert.equal(input.listenerCount(), 0);
  assert.equal(registryB.has(input), false);

  input.__easyuseAnimaAutocompleteHooked = true;
  const registryC = new Set();
  let disposeC = 0;
  const stateC = { input };
  const bindingC = replacementBinding(
    input,
    stateC,
    {},
    registryC,
    noOpController(() => { disposeC += 1; }),
  );
  assert.equal(input.__easyuseAnimaAutocompleteState, stateC);
  assert.equal(input.listenerCount(), 18, "a state-less stale marker must not block re-hook");

  delete input.__easyuseAnimaAutocompleteState;
  const pruneMissingState = createDisconnectedInputPruner(
    registryC,
    createAutocompleteInputDisposer(registryC),
  );
  pruneMissingState();
  assert.equal(disposeC, 1, "prune must invoke the saved disposer for a missing state expando");
  assert.equal(registryC.has(input), false);
  assert.equal(input.listenerCount(), 0, "missing-state prune must remove the live listener set");

  const registryD = new Set();
  let disposeD = 0;
  const stateD = { input };
  const bindingD = replacementBinding(
    input,
    stateD,
    {},
    registryD,
    noOpController(() => { disposeD += 1; }),
  );
  assert.equal(registryD.has(input), true);
  assert.equal(input.__easyuseAnimaAutocompleteState, stateD);
  assert.equal(input.listenerCount(), 18);

  delete input.__easyuseAnimaAutocompleteState;
  const registryE = new Set();
  let disposeE = 0;
  const stateE = { input };
  const bindingE = replacementBinding(
    input,
    stateE,
    {},
    registryE,
    noOpController(() => { disposeE += 1; }),
  );
  assert.equal(disposeD, 1, "direct re-hook must invoke the saved disposer for a missing state expando");
  assert.equal(registryD.has(input), false);
  assert.equal(registryE.has(input), true);
  assert.equal(input.__easyuseAnimaAutocompleteState, stateE);
  assert.equal(input.listenerCount(), 18, "state repair must not leave duplicate listeners");

  bindingC.dispose();
  bindingD.dispose();
  bindingE.dispose();
  assert.equal(disposeC, 1);
  assert.equal(disposeD, 1);
  assert.equal(disposeE, 1);
  assert.equal(input.listenerCount(), 0);
}

{
  class FakeTextAreaElement extends FakeInput {}
  class FakeHtmlInputElement extends FakeInput {}
  class FakeContainer {
    constructor(nested = null) {
      this.nested = nested;
    }

    querySelector(selector) {
      assert.equal(selector, "textarea, input");
      return this.nested;
    }
  }

  const findStart = entrySource.indexOf("function findInputEl");
  const findEnd = entrySource.indexOf("\nfunction currentToken", findStart);
  assert.ok(findStart >= 0 && findEnd > findStart);
  const findInputEl = new Function(
    "HTMLTextAreaElement",
    "HTMLInputElement",
    `"use strict";\n${entrySource.slice(findStart, findEnd)}\nreturn findInputEl;`,
  )(FakeTextAreaElement, FakeHtmlInputElement);

  const disconnected = new FakeTextAreaElement();
  disconnected.isConnected = false;
  assert.equal(
    findInputEl({ inputEl: disconnected, element: disconnected }),
    null,
    "a pre-mount legacy textarea must stay pending instead of receiving a disposable binding",
  );

  const connectedFallback = new FakeTextAreaElement();
  const fallbackContainer = new FakeContainer(connectedFallback);
  assert.equal(
    findInputEl({ inputEl: disconnected, element: fallbackContainer }),
    connectedFallback,
    "a connected nested element must win over a stale direct inputEl",
  );

  const direct = new FakeHtmlInputElement();
  assert.equal(findInputEl({ inputEl: direct }), direct);

  const graphNodesStart = entrySource.indexOf("function autocompleteGraphNodes");
  const graphNodesEnd = entrySource.indexOf("\nfunction findGraphNodeById", graphNodesStart);
  assert.ok(graphNodesStart >= 0 && graphNodesEnd > graphNodesStart);
  const autocompleteGraphNodesFor = (app) => new Function(
    "app",
    `"use strict";\n${entrySource.slice(graphNodesStart, graphNodesEnd)}\nreturn autocompleteGraphNodes;`,
  )(app)();
  const legacyNode = { id: 1 };
  const node2Node = { id: 2 };
  assert.deepEqual(autocompleteGraphNodesFor({ graph: { _nodes: [legacyNode, null] } }), [legacyNode]);
  assert.deepEqual(autocompleteGraphNodesFor({ graph: { nodes: [node2Node, null] } }), [node2Node]);
  assert.deepEqual(
    autocompleteGraphNodesFor({ graph: { _nodes_by_id: { 1: legacyNode, empty: null } } }),
    [legacyNode],
  );

  class FakeElement {
    constructor(root = null) {
      this.root = root || this;
      this.dataset = {};
      this.id = "";
    }

    closest() {
      return this.root;
    }

    getAttribute() {
      return null;
    }
  }
  const nodeFromDomStart = entrySource.indexOf("function nodeFromDomElement");
  const nodeFromDomEnd = entrySource.indexOf("\nfunction isAutocompleteDomInput", nodeFromDomStart);
  assert.ok(nodeFromDomStart >= 0 && nodeFromDomEnd > nodeFromDomStart);
  const nodeFromDomElement = new Function(
    "Element",
    "findGraphNodeById",
    `"use strict";\n${entrySource.slice(nodeFromDomStart, nodeFromDomEnd)}\nreturn nodeFromDomElement;`,
  )(FakeElement, (id) => id);
  const datasetRoot = new FakeElement();
  datasetRoot.dataset.nodeId = "42";
  assert.equal(
    nodeFromDomElement(new FakeElement(datasetRoot)),
    "42",
    "DOM ownership lookup must retain the dataset fallback when the attribute path is empty",
  );

  let graphNodes = [];
  const ownerStart = entrySource.indexOf("function autocompleteDomInputOwner");
  const ownerEnd = entrySource.indexOf("\nfunction hookFocusedDomInput", ownerStart);
  assert.ok(ownerStart >= 0 && ownerEnd > ownerStart);
  const autocompleteDomInputOwner = new Function(
    "nodeFromDomElement",
    "autocompleteGraphNodes",
    "widgetForDomInput",
    `"use strict";\n${entrySource.slice(ownerStart, ownerEnd)}\nreturn autocompleteDomInputOwner;`,
  )(
    () => null,
    () => graphNodes,
    (node, input) => (node?.widgets || []).find((widget) => {
      const widgetInput = findInputEl(widget);
      return widgetInput === input || widget?.element?.contains?.(input);
    }) || null,
  );

  const hookStart = entrySource.indexOf("function hookNode");
  const hookEnd = entrySource.indexOf("\nfunction handleOutsideAutocompletePointer", hookStart);
  assert.ok(hookStart >= 0 && hookEnd > hookStart);

  const scheduled = [];
  const hooked = [];
  const lifecycle = {
    isActive: () => true,
    schedule(callback, delay) {
      scheduled.push({ callback, delay });
    },
  };
  const targetWidgets = () => new Set(["text", "populated_text"]);
  const hookNode = new Function(
    "autocompleteEntryLifecycle",
    "targetWidgets",
    "hasExplicitTargets",
    "shouldSkipNode",
    "artistOnlyWidgets",
    "findInputEl",
    "hookWidget",
    `"use strict";\n${entrySource.slice(hookStart, hookEnd)}\nreturn hookNode;`,
  )(
    lifecycle,
    targetWidgets,
    () => true,
    () => false,
    () => new Set(),
    findInputEl,
    (_node, widget) => {
      const input = findInputEl(widget);
      if (input) {
        hooked.push(input);
      }
    },
  );

  const textInput = new FakeTextAreaElement();
  const populatedInput = new FakeTextAreaElement();
  textInput.isConnected = false;
  populatedInput.isConnected = false;
  const node = {
    constructor: { nodeData: { name: "EasyUseAnimaWildcard" } },
    __easyuseAnimaArtistOnlyWidgets: new Set(),
    widgets: [
      { name: "text", inputEl: textInput, element: textInput },
      { name: "populated_text", inputEl: populatedInput, element: populatedInput },
    ],
  };
  graphNodes = [node];

  hookNode(node, { name: "EasyUseAnimaWildcard" });
  assert.equal(hooked.length, 0);
  for (let attempt = 0; attempt < 12; attempt += 1) {
    assert.equal(scheduled.length, 1);
    const scheduledAttempt = scheduled.shift();
    assert.equal(scheduledAttempt.delay, 80);
    scheduledAttempt.callback();
  }
  assert.equal(scheduled.length, 0, "the existing bounded retry must be fully exhausted");
  assert.equal(hooked.length, 0);

  textInput.isConnected = true;
  const lateOwner = autocompleteDomInputOwner(textInput);
  assert.equal(lateOwner?.node, node);
  assert.equal(lateOwner?.widget, node.widgets[0]);

  const focusStart = entrySource.indexOf("function hookFocusedDomInput");
  const focusEnd = entrySource.indexOf("\nfunction handleAutocompleteScroll", focusStart);
  assert.ok(focusStart >= 0 && focusEnd > focusStart);
  const focusedHooks = [];
  const hookFocusedDomInput = new Function(
    "isAutocompleteDomInput",
    "popup",
    "autocompleteDomInputOwner",
    "targetWidgets",
    "hasExplicitTargets",
    "shouldSkipNode",
    "autocompleteScope",
    "hookInput",
    `"use strict";\n${entrySource.slice(focusStart, focusEnd)}\nreturn hookFocusedDomInput;`,
  )(
    () => true,
    null,
    autocompleteDomInputOwner,
    targetWidgets,
    () => true,
    () => false,
    () => "compatible",
    (input, options) => focusedHooks.push({ input, options }),
  );

  hookFocusedDomInput(textInput);
  assert.equal(focusedHooks.length, 1);
  assert.equal(focusedHooks[0].input, textInput);
  assert.equal(focusedHooks[0].options.node, node);
  assert.equal(focusedHooks[0].options.widget, node.widgets[0]);
  assert.equal(focusedHooks[0].options.scope, "easyuse");
}

console.log("Autocomplete input binding smoke passed.");
