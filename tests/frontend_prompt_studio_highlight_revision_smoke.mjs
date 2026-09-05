import { readFileSync } from "node:fs";
import { deepStrictEqual } from "node:assert/strict";

const source = readFileSync(
  new URL("../web/js/prompt_studio/highlight_revision.js", import.meta.url),
  "utf8",
);
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const {
  highlightRequestOwnsText,
  highlightTokensForText,
} = await import(moduleUrl);

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const tokensA = [{ token: "text A", section: "general" }];
assert(
  highlightTokensForText("text A", "text A", tokensA) === tokensA,
  "Matching text must keep its classification token identity",
);
assert(
  highlightTokensForText("text B", "text A", tokensA).length === 0,
  "Pasted text must not render the previous text token cache",
);
assert(
  highlightTokensForText("text A", "text A", null).length === 0,
  "Malformed token caches must fail closed",
);

const requestA = { sequence: 1, text: "text A" };
assert(
  highlightRequestOwnsText(requestA, 1, "text A"),
  "Matching sequence and text must own the highlight result",
);
assert(
  !highlightRequestOwnsText(requestA, 1, "text B"),
  "A response must become stale as soon as paste changes the text",
);
assert(
  !highlightRequestOwnsText(requestA, 2, "text A"),
  "A superseded request sequence must not publish",
);
assert(
  !highlightRequestOwnsText(requestA, 1, "text A", false),
  "A disconnected textarea must not receive a result",
);

const requestB = { sequence: 2, text: "text B" };
const requestC = { sequence: 3, text: "text C" };
assert(
  !highlightRequestOwnsText(requestA, 3, "text C")
    && !highlightRequestOwnsText(requestB, 3, "text C")
    && highlightRequestOwnsText(requestC, 3, "text C"),
  "Rapid A to B to C input must leave only C as the publishing owner",
);

const highlightFixtureSource = `
  export const requests = [];
  export function classifyPrompt(text) {
    return new Promise((resolve) => requests.push({ text, resolve }));
  }
  export function ensureHighlightOverlay(input) { return input.overlay; }
  export function highlightOverlayHtml(value, tokens) {
    return JSON.stringify({ value, tokens });
  }
  export function copyInputTextMetrics() {}
  export function overlayBounds() { return {}; }
  export function overlayScrollbarPadding() { return {}; }
  export function syncOverlayBounds() {}
  export function applyPromptStudioTextStyle() {}
  export function parseAdvancedFields() { return []; }
  export function getAdvancedEditorElement() { return null; }
  export function getAdvancedFields() { return []; }
  export function registerExternalAutocompleteInput() {}
`;
const highlightFixtureUrl = `data:text/javascript;base64,${Buffer.from(highlightFixtureSource).toString("base64")}`;
const { requests } = await import(highlightFixtureUrl);
let advancedSource = readFileSync(
  new URL("../web/js/prompt_studio/advanced_highlights.js", import.meta.url),
  "utf8",
).replace('"./highlight_revision.js"', JSON.stringify(moduleUrl));
for (const dependency of [
  "./advanced_fields_state.js",
  "./highlight.js",
  "./settings.js",
  "./state.js",
  "../autocomplete/entry_lifecycle.js",
]) {
  advancedSource = advancedSource.replace(JSON.stringify(dependency), JSON.stringify(highlightFixtureUrl));
}
const advancedUrl = `data:text/javascript;base64,${Buffer.from(advancedSource).toString("base64")}`;
const { advancedHighlightState, scheduleAdvancedFieldHighlight } = await import(advancedUrl);

const previousTextareaClass = globalThis.HTMLTextAreaElement;
class MockTextarea {
  constructor(value = "") {
    this.value = value;
    this.placeholder = "";
    this.isConnected = true;
    this.overlay = { innerHTML: "" };
  }
}
globalThis.HTMLTextAreaElement = MockTextarea;
const prototypeTargets = [Object.prototype, Object, Object.prototype.toString];
const prototypeSnapshots = prototypeTargets.map((target) => Object.getOwnPropertyDescriptors(target));
function assertPrototypesUnchanged() {
  prototypeTargets.forEach((target, index) => {
    deepStrictEqual(
      Object.getOwnPropertyDescriptors(target),
      prototypeSnapshots[index],
      "Saved field IDs must not write highlight state onto shared JavaScript prototypes",
    );
  });
}
const flushClassification = () => new Promise((resolve) => setImmediate(resolve));

try {
  for (const id of ["__proto__", "constructor", "toString", "positive_general_1"]) {
    const nodeA = { __easyuseAnimaAdvancedHighlightStates: {} };
    const nodeB = {};
    const fieldA = { id };
    const fieldB = { id };
    const textareaA = new MockTextarea();
    const textareaB = new MockTextarea();
    scheduleAdvancedFieldHighlight(nodeA, fieldA, textareaA);
    scheduleAdvancedFieldHighlight(nodeB, fieldB, textareaB);
    assertPrototypesUnchanged();
    const stateA = advancedHighlightState(nodeA, fieldA);
    const stateB = advancedHighlightState(nodeB, fieldB);
    assert(stateA !== stateB && stateA.tokens !== stateB.tokens, "Each node must own its field state");
    assert(fieldA.id === id && fieldB.id === id, "Saved field IDs must remain unchanged");
    assert(
      Object.hasOwn(nodeA.__easyuseAnimaAdvancedHighlightStates, id)
        && Object.hasOwn(nodeB.__easyuseAnimaAdvancedHighlightStates, id),
      "Both existing and new state stores must own reserved field IDs",
    );

    textareaA.value = `${id} node A`;
    textareaB.value = `${id} node B`;
    const firstRequest = requests.length;
    scheduleAdvancedFieldHighlight(nodeA, fieldA, textareaA);
    scheduleAdvancedFieldHighlight(nodeB, fieldB, textareaB);
    assert(requests.length === firstRequest + 2, "Both node callers must request classification");
    const tokensForA = [{ token: textareaA.value, section: "general" }];
    const tokensForB = [{ token: textareaB.value, section: "general" }];
    requests[firstRequest + 1].resolve(tokensForB);
    await flushClassification();
    assert(stateA.pendingText === textareaA.value, "The other node result must not clear a pending request");
    requests[firstRequest].resolve(tokensForA);
    await flushClassification();
    assert(stateA.tokens === tokensForA && stateB.tokens === tokensForB, "Results must stay isolated by node");
    assert(stateA.lastText === textareaA.value && stateB.lastText === textareaB.value, "Each result must retain its own text");
    assert(stateA.seq === 1 && stateB.seq === 1, "Reserved IDs must have normal request sequencing");
    assert(stateA.pendingText === null && stateB.pendingText === null, "Finished requests must clear their own pending state");
    assert(JSON.parse(textareaA.overlay.innerHTML).tokens[0].token === textareaA.value, "The actual caller must render its result");
    const requestCount = requests.length;
    scheduleAdvancedFieldHighlight(nodeA, fieldA, textareaA);
    assert(requests.length === requestCount, "Unchanged text must reuse cached classification");
    assert(advancedHighlightState(nodeA, fieldA) === stateA, "Repeated lookup must reuse field state");
    assertPrototypesUnchanged();
  }

  const cachedState = { seq: 7, lastText: "cached", pendingText: null, tokens: tokensA };
  const cachedNode = { __easyuseAnimaAdvancedHighlightStates: { positive_general_1: cachedState } };
  const requestCount = requests.length;
  scheduleAdvancedFieldHighlight(cachedNode, { id: "positive_general_1" }, new MockTextarea("cached"));
  assert(advancedHighlightState(cachedNode, { id: "positive_general_1" }) === cachedState, "Existing ordinary field state must keep its identity");
  assert(requests.length === requestCount, "Existing ordinary field caches must not be reclassified");
  assertPrototypesUnchanged();
} finally {
  if (previousTextareaClass === undefined) {
    delete globalThis.HTMLTextAreaElement;
  } else {
    globalThis.HTMLTextAreaElement = previousTextareaClass;
  }
}

console.log("Prompt Studio highlight revision smoke passed.");
