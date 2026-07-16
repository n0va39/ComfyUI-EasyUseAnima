import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function sourceModule(source) {
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

const queueModule = await import(
  dataModule("../web/js/prompt_studio/advanced_queue_seed_runtime.js")
);
assert.deepEqual(
  Object.keys(queueModule).sort(),
  [
    "createAdvancedQueueSeedRuntime",
    "installAdvancedQueueSeedGraphCleanup",
    "installAdvancedQueueSeedQueueHook",
  ],
);

const ADVANCED = "EasyUseAnimaPromptStudioAdvanced";
const ADVANCED_V2 = "EasyUseAnimaPromptStudioAdvancedV2";
const SEED_INDEX = 11;
const RESERVED_NEXT_SEED_INPUT = "easyuse_anima_reserved_wildcard_next_seed";

const nodeHookConstants = sourceModule(`
  export const NODE_TYPE = "EasyUseAnimaPromptStudio";
  export const ADVANCED_NODE_TYPE = "${ADVANCED}";
  export const ADVANCED_V2_NODE_TYPE = "${ADVANCED_V2}";
  export const EXTEND_NODE_TYPE = "EasyUseAnimaPromptStudioExtend";
  export const WILDCARD_NODE_TYPE = "EasyUseAnimaWildcard";
`);
const nodeHooksSource = readFileSync(
  new URL("../web/js/prompt_studio/node_hooks.js", import.meta.url),
  "utf8",
).replace('from "./constants.js"', `from "${nodeHookConstants}"`);
const nodeHooksModule = await import(sourceModule(nodeHooksSource));

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function widgetValues(seed, mode = "순차", control = "increment") {
  const values = Array(22).fill(null);
  values[10] = mode;
  values[SEED_INDEX] = seed;
  values[12] = control;
  return values;
}

function advancedNode(id, type = ADVANCED, seed = 7) {
  return {
    id,
    type,
    comfyClass: type,
    widgets: [
      { name: "wildcard_mode", value: "순차" },
      { name: "wildcard_seed", value: seed },
      { name: "wildcard_seed_after_generate", value: "increment" },
    ],
  };
}

function promptFor(nodes, options = {}) {
  const output = {};
  const workflowNodes = [];
  for (const node of nodes) {
    const mode = node.widgets.find((widget) => widget.name === "wildcard_mode").value;
    const seed = node.widgets.find((widget) => widget.name === "wildcard_seed").value;
    const control = node.widgets.find(
      (widget) => widget.name === "wildcard_seed_after_generate",
    ).value;
    output[String(node.id)] = {
      class_type: node.type,
      inputs: {
        advanced_fields: "[]",
        wildcard_mode: mode,
        wildcard_seed: seed,
        wildcard_seed_after_generate: control,
      },
    };
    workflowNodes.push({
      id: node.id,
      type: node.type,
      widgets_values: widgetValues(seed, mode, control),
    });
  }
  const consumers = Object.prototype.hasOwnProperty.call(options, "consumers")
    ? options.consumers
    : nodes.map((node, index) => ({ id: 20 + index, source: node.id }));
  for (const consumer of consumers) {
    output[String(consumer.id)] = {
      class_type: consumer.type || "PreviewImage",
      inputs: { source: [consumer.source, 0] },
    };
    workflowNodes.push({
      id: consumer.id,
      type: consumer.type || "PreviewImage",
      widgets_values: [],
    });
  }
  return {
    output,
    workflow: { nodes: workflowNodes, links: [] },
    extra_data: { untouched: true },
  };
}

function createFixture(options = {}) {
  const nodes = options.nodes || [advancedNode(10)];
  const outputNodes = options.outputNodes || nodes.map((_, index) => ({
    id: 20 + index,
    outputNode: true,
  }));
  const randomValues = [...(options.randomValues || [41, 42, 43, 44])];
  const commits = [];
  let randomCalls = 0;
  let cloneCalls = 0;
  let updateFailures = Number(options.updateFailures || 0);
  const runtime = queueModule.createAdvancedQueueSeedRuntime({
    seedWidgetIndex: SEED_INDEX,
    listNodes: () => [...nodes, ...outputNodes],
    isAdvancedNode: (node) => [ADVANCED, ADVANCED_V2].includes(node?.type),
    isOutputNode: (node) => node?.outputNode === true,
    getSeed(node) {
      return node.widgets.find((widget) => widget.name === "wildcard_seed")?.value;
    },
    updateSeed(node, seed) {
      if (updateFailures > 0) {
        updateFailures -= 1;
        throw new Error("seed publish failed");
      }
      commits.push([node.id, seed]);
      node.widgets.find((widget) => widget.name === "wildcard_seed").value = seed;
    },
    clonePrompt(value) {
      cloneCalls += 1;
      if (options.cloneError) {
        throw options.cloneError;
      }
      return clone(value);
    },
    randomSeed() {
      randomCalls += 1;
      return randomValues.shift() ?? 0;
    },
  });
  return {
    nodes,
    runtime,
    commits,
    randomCalls: () => randomCalls,
    cloneCalls: () => cloneCalls,
  };
}

function queuedSeed(prompt, nodeId) {
  return prompt.output[String(nodeId)].inputs.wildcard_seed;
}

function workflowSeed(prompt, nodeId) {
  return prompt.workflow.nodes.find((node) => String(node.id) === String(nodeId))
    .widgets_values[SEED_INDEX];
}

function reservedNextSeed(prompt, nodeId) {
  return reservedSeedState(prompt, nodeId)?.next_seed;
}

function reservedSeedState(prompt, nodeId) {
  const raw = prompt.output[String(nodeId)].inputs[RESERVED_NEXT_SEED_INPUT];
  return raw == null ? undefined : JSON.parse(raw);
}

{
  const events = [];
  const clearResult = { cleared: true };
  const firstArg = { first: true };
  const secondArg = { second: true };
  const graph = {
    clear(...args) {
      events.push(["clear", this, args]);
      return clearResult;
    },
  };
  const owner = { graphOwner: true };
  const runtime = {
    clearGraphNodes() {
      events.push(["cleanup"]);
    },
  };
  assert.equal(queueModule.installAdvancedQueueSeedGraphCleanup(graph, runtime), true);
  const installed = graph.clear;
  assert.equal(queueModule.installAdvancedQueueSeedGraphCleanup(graph, runtime), false);
  assert.equal(graph.clear, installed, "graph cleanup wrapper must install only once");
  assert.equal(graph.clear.call(owner, firstArg, secondArg), clearResult);
  assert.deepEqual(events, [
    ["clear", owner, [firstArg, secondArg]],
    ["cleanup"],
  ]);

  const clearError = new Error("graph clear failed");
  let failedCleanupCalls = 0;
  const failingGraph = {
    clear() {
      throw clearError;
    },
  };
  queueModule.installAdvancedQueueSeedGraphCleanup(failingGraph, {
    clearGraphNodes() {
      failedCleanupCalls += 1;
    },
  });
  assert.throws(() => failingGraph.clear(), (error) => error === clearError);
  assert.equal(
    failedCleanupCalls,
    0,
    "a failed original graph clear must preserve managed owners for the still-live graph",
  );
}

{
  const events = [];
  const configureResult = Symbol("configure-result");
  const removeResult = Symbol("remove-result");
  const serialized = { workflow: true };
  const configureTail = { extra: true };
  const removeArg = { reason: "test" };
  function AdvancedNodeType() {}
  AdvancedNodeType.prototype.onConfigure = function (...args) {
    events.push(["configure", this, args]);
    return configureResult;
  };
  AdvancedNodeType.prototype.onRemoved = function (...args) {
    events.push(["remove", this, args]);
    return removeResult;
  };
  const hooks = {
    captureAdvancedConfigure: (node, value) => events.push(["capture", node, value]),
    attachAdvancedQueueSeedNode: (node) => events.push(["attach", node]),
    scheduleHookAdvancedNode: (node) => events.push(["schedule", node]),
    disconnectAdvancedEditorWidthObserver: (node) => {
      events.push(["disconnect", node]);
      throw new Error("isolated observer cleanup failure");
    },
    detachAdvancedQueueSeedNode: (node) => events.push(["detach", node]),
  };
  assert.equal(
    nodeHooksModule.registerPromptStudioNodeHooks(
      AdvancedNodeType,
      { name: ADVANCED },
      hooks,
    ),
    true,
  );
  const node = new AdvancedNodeType();
  assert.equal(node.onConfigure(serialized, configureTail), configureResult);
  assert.equal(node.onRemoved(removeArg), removeResult);
  assert.deepEqual(events, [
    ["configure", node, [serialized, configureTail]],
    ["capture", node, serialized],
    ["attach", node],
    ["schedule", node],
    ["remove", node, [removeArg]],
    ["disconnect", node],
    ["detach", node],
  ]);
}

{
  for (const originalError of [
    new Error("original removal failure"),
    null,
    undefined,
    0,
    false,
  ]) {
    const events = [];
    function FailingAdvancedNodeType() {}
    FailingAdvancedNodeType.prototype.onRemoved = function () {
      events.push(["remove", this]);
      throw originalError;
    };
    nodeHooksModule.registerPromptStudioNodeHooks(
      FailingAdvancedNodeType,
      { name: ADVANCED_V2 },
      {
        captureAdvancedConfigure() {},
        scheduleHookAdvancedNode() {},
        disconnectAdvancedEditorWidthObserver(node) {
          events.push(["disconnect", node]);
          throw new Error("secondary disconnect failure");
        },
        detachAdvancedQueueSeedNode(node) {
          events.push(["detach", node]);
          throw new Error("secondary state cleanup failure");
        },
      },
    );
    const node = new FailingAdvancedNodeType();
    const notThrown = Symbol("not-thrown");
    let caught = notThrown;
    try {
      node.onRemoved();
    } catch (error) {
      caught = error;
    }
    assert.notEqual(caught, notThrown, "the original removal throw must not be swallowed");
    assert.equal(caught, originalError, "cleanup must preserve the original throw identity");
    assert.deepEqual(events, [
      ["remove", node],
      ["disconnect", node],
      ["detach", node],
    ]);
  }
}

{
  const nodes = [advancedNode(10, ADVANCED, 7), advancedNode(11, ADVANCED_V2, 27)];
  const fixture = createFixture({ nodes });
  const prompt = promptFor(nodes);
  const original = clone(prompt);
  const transaction = fixture.runtime.preparePrompt(prompt);

  assert.ok(transaction);
  assert.notEqual(transaction.prompt, prompt);
  assert.deepEqual(prompt, original, "queue preparation must not mutate the caller payload");
  assert.equal(nodes[0].widgets[1].value, 7, "reservation must not mutate live state");
  assert.equal(nodes[1].widgets[1].value, 27, "V2 live state must remain unchanged");
  assert.equal(queuedSeed(transaction.prompt, 10), 7);
  assert.equal(workflowSeed(transaction.prompt, 10), 7);
  assert.equal(reservedNextSeed(transaction.prompt, 10), 8);
  assert.equal(queuedSeed(transaction.prompt, 11), 27);
  assert.equal(workflowSeed(transaction.prompt, 11), 27);
  assert.equal(reservedNextSeed(transaction.prompt, 11), 28);
  assert.deepEqual(transaction.prompt.extra_data, { untouched: true });
}

{
  const fixture = createFixture();
  const calls = [];
  const gates = [deferred(), deferred(), deferred()];
  const wrapped = fixture.runtime.wrapQueuePrompt(function (...args) {
    calls.push({ owner: this, args });
    return gates[calls.length - 1].promise;
  });
  const owner = { name: "api-owner" };
  const options = { partialExecutionTargets: [20], previewMethod: "latent2rgb" };
  const tail = { preserve: true };
  const prompt = promptFor(fixture.nodes, { consumers: [{ id: 20, source: 10 }] });
  const original = clone(prompt);

  const pending = [
    wrapped.call(owner, -1, prompt, options, tail),
    wrapped.call(owner, -1, prompt, options, tail),
    wrapped.call(owner, -1, prompt, options, tail),
  ];
  assert.deepEqual(calls.map((call) => queuedSeed(call.args[1], 10)), [7, 8, 9]);
  assert.deepEqual(calls.map((call) => workflowSeed(call.args[1], 10)), [7, 8, 9]);
  assert.deepEqual(calls.map((call) => reservedNextSeed(call.args[1], 10)), [8, 9, 10]);
  assert.deepEqual(prompt, original, "rapid reservations must keep the caller payload immutable");
  assert.equal(fixture.nodes[0].widgets[1].value, 7, "live seed changes only after acceptance");
  for (const call of calls) {
    assert.equal(call.owner, owner);
    assert.equal(call.args.length, 4);
    assert.equal(call.args[0], -1);
    assert.equal(call.args[2], options, "partial execution options identity must survive");
    assert.equal(call.args[3], tail, "tail argument identity must survive");
  }

  gates[0].resolve({ prompt_id: "one", node_errors: {} });
  gates[1].resolve({ prompt_id: "two", node_errors: {} });
  gates[2].resolve({ prompt_id: "three", node_errors: {} });
  const results = await Promise.all(pending);
  assert.deepEqual(results.map((result) => result.prompt_id), ["one", "two", "three"]);
  assert.equal(fixture.nodes[0].widgets[1].value, 10);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], 8), false);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], 10), true);
}

{
  // ComfyUI v0.27 app.queuePrompt calls api.queuePrompt once per batch after a
  // fresh graphToPrompt. The accepted commit must feed the next serialization.
  const fixture = createFixture();
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt, options) => {
    queued.push({ seed: queuedSeed(prompt, 10), options });
    return { prompt_id: `batch-${queued.length}`, node_errors: {} };
  });
  const options = { partialExecutionTargets: [20] };
  for (let index = 0; index < 3; index += 1) {
    const prompt = promptFor(fixture.nodes, { consumers: [{ id: 20, source: 10 }] });
    await wrapped(0, prompt, options);
  }
  assert.deepEqual(queued.map((entry) => entry.seed), [7, 8, 9]);
  assert.equal(fixture.nodes[0].widgets[1].value, 10);
  assert.equal(queued.every((entry) => entry.options === options), true);
}

{
  const node = advancedNode(10, ADVANCED, 7);
  node.widgets[0].value = "일반 채우기";
  node.widgets[2].value = "randomize";
  const fixture = createFixture({ nodes: [node], randomValues: [41, 42, 43] });
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queued.push({
      current: queuedSeed(prompt, 10),
      next: reservedNextSeed(prompt, 10),
    });
    return { prompt_id: `random-${queued.length}`, node_errors: {} };
  });
  await Promise.all([
    wrapped(0, promptFor([node])),
    wrapped(0, promptFor([node])),
    wrapped(0, promptFor([node])),
  ]);
  assert.deepEqual(queued, [
    { current: 7, next: 41 },
    { current: 41, next: 42 },
    { current: 42, next: 43 },
  ]);
  assert.equal(node.widgets[1].value, 43);
  assert.equal(fixture.randomCalls(), 3);
}

{
  const fixed = advancedNode(10, ADVANCED, 7);
  fixed.widgets[0].value = "고정";
  fixed.widgets[2].value = "randomize";
  const fixture = createFixture({ nodes: [fixed], randomValues: [41, 42, 43] });
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queued.push([queuedSeed(prompt, 10), reservedNextSeed(prompt, 10)]);
    return { prompt_id: `fixed-random-${queued.length}`, node_errors: {} };
  });
  await Promise.all([
    wrapped(0, promptFor([fixed])),
    wrapped(0, promptFor([fixed])),
    wrapped(0, promptFor([fixed])),
  ]);
  assert.deepEqual(queued, [[7, 41], [41, 42], [42, 43]]);
  assert.equal(fixed.widgets[1].value, 43);
  assert.equal(fixture.randomCalls(), 3);
}

{
  const decrement = advancedNode(10, ADVANCED, 0);
  decrement.widgets[0].value = "일반 채우기";
  decrement.widgets[2].value = "decrement";
  const fixture = createFixture({ nodes: [decrement] });
  const transaction = fixture.runtime.preparePrompt(promptFor([decrement]));
  assert.ok(transaction);
  assert.equal(queuedSeed(transaction.prompt, 10), 0);
  assert.equal(reservedNextSeed(transaction.prompt, 10), Number.MAX_SAFE_INTEGER);
}

{
  const fixture = createFixture();
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "unsafe-pass-through", node_errors: {} };
  });
  await wrapped(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 8);
  fixture.nodes[0].widgets[1].value = Number.MAX_SAFE_INTEGER + 1;
  const prompt = promptFor(fixture.nodes);
  await wrapped(0, prompt);
  assert.equal(received, prompt, "unsafe 64-bit seeds must not be rounded in a queue clone");
  assert.equal(fixture.nodes[0].widgets[1].value, Number.MAX_SAFE_INTEGER + 1);
  assert.equal(fixture.cloneCalls(), 1, "the unsafe transition itself must not clone");
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], Number.MAX_SAFE_INTEGER),
    true,
    "an old safe-state guard must not block the backend pass-through path",
  );
}

{
  const fixed = advancedNode(10, ADVANCED, 7);
  fixed.widgets[0].value = "고정";
  fixed.widgets[2].value = "fixed";
  const fixture = createFixture({ nodes: [fixed] });
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queued.push(queuedSeed(prompt, 10));
    return { prompt_id: `fixed-${queued.length}`, node_errors: {} };
  });
  await Promise.all([
    wrapped(0, promptFor([fixed])),
    wrapped(0, promptFor([fixed])),
    wrapped(0, promptFor([fixed])),
  ]);
  assert.deepEqual(queued, [7, 7, 7]);
  assert.equal(fixed.widgets[1].value, 7);
  assert.equal(fixture.randomCalls(), 0);
}

{
  const reproduce = advancedNode(10, ADVANCED_V2, 7);
  reproduce.widgets[0].value = "재현";
  reproduce.widgets[2].value = "randomize";
  const fixture = createFixture({ nodes: [reproduce], randomValues: [41] });
  const prompt = promptFor([reproduce]);
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "reproduce", node_errors: {} };
  });
  await wrapped(0, prompt);
  assert.equal(received, prompt, "reproduce mode must pass the original payload through");
  assert.equal(reproduce.widgets[1].value, 7);
  assert.equal(fixture.randomCalls(), 0);
}

{
  const fixture = createFixture();
  const failure = new Error("queue rejected");
  let attempts = 0;
  let retriedSeed = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    attempts += 1;
    if (attempts === 1) {
      return Promise.reject(failure);
    }
    retriedSeed = queuedSeed(prompt, 10);
    return { prompt_id: "retry", node_errors: {} };
  });
  await assert.rejects(wrapped(0, promptFor(fixture.nodes)), (error) => error === failure);
  assert.equal(fixture.nodes[0].widgets[1].value, 7, "rejection must not advance live state");
  await wrapped(0, promptFor(fixture.nodes));
  assert.equal(retriedSeed, 7, "a rejected reservation must be reusable");
  assert.equal(fixture.nodes[0].widgets[1].value, 8);
}

{
  const fixture = createFixture();
  const calls = [];
  const gates = [deferred(), deferred(), deferred()];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    calls.push(queuedSeed(prompt, 10));
    return gates[calls.length - 1].promise;
  });
  const pending = [
    wrapped(0, promptFor(fixture.nodes)),
    wrapped(0, promptFor(fixture.nodes)),
    wrapped(0, promptFor(fixture.nodes)),
  ];
  gates[1].resolve({ prompt_id: "second", node_errors: {} });
  await pending[1];
  assert.equal(fixture.nodes[0].widgets[1].value, 7, "later results wait for FIFO settlement");
  gates[0].resolve({ prompt_id: "   ", node_errors: {} });
  await pending[0];
  assert.equal(fixture.nodes[0].widgets[1].value, 9, "blank prompt ids reject only their reservation");
  gates[2].resolve({ prompt_id: "third", node_errors: {} });
  await pending[2];
  assert.deepEqual(calls, [7, 8, 9]);
  assert.equal(fixture.nodes[0].widgets[1].value, 10);
}

{
  const fixture = createFixture({ updateFailures: 1 });
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queued.push(queuedSeed(prompt, 10));
    return { prompt_id: `publish-${queued.length}`, node_errors: {} };
  });
  await wrapped(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 7, "failed publication leaves the widget untouched");
  await wrapped(0, promptFor(fixture.nodes));
  assert.deepEqual(queued, [7, 8], "a failed widget refresh must not reuse an accepted seed");
  assert.equal(fixture.nodes[0].widgets[1].value, 9);
  assert.deepEqual(fixture.commits, [[10, 8], [10, 9]]);
}

{
  const fixture = createFixture();
  const accepted = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "accepted-before-manual-edit", node_errors: {},
  }));
  await accepted(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 8);
  fixture.nodes[0].widgets[1].value = 100;
  const rejected = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "", node_errors: {},
  }));
  await rejected(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 100);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], 8),
    false,
    "a rejected queue after a manual edit must not reopen an older executed seed",
  );
  await accepted(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 101);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], 101), true);
}

{
  const nodes = [advancedNode(10, ADVANCED, 7), advancedNode(11, ADVANCED_V2, 30)];
  const fixture = createFixture({ nodes });
  const prompt = promptFor(nodes, { consumers: [{ id: 20, source: 10 }] });
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "connected-only", node_errors: {} };
  });
  await wrapped(0, prompt);
  assert.equal(nodes[0].widgets[1].value, 8);
  assert.equal(nodes[1].widgets[1].value, 30, "disconnected Advanced nodes must not reserve seeds");
  assert.equal(reservedNextSeed(received, 10), 8);
  assert.equal(reservedSeedState(received, 11), undefined);
}

{
  const nodes = [advancedNode(10, ADVANCED, 7)];
  const fixture = createFixture({
    nodes,
    outputNodes: [
      { id: 20, outputNode: true },
      { id: 21, outputNode: true },
    ],
  });
  const prompt = promptFor(nodes, {
    consumers: [
      { id: 20, source: 10 },
      { id: 21, source: 10 },
    ],
  });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "one-valid-output",
    node_errors: {
      99: { errors: ["bad input"], dependent_outputs: ["20"] },
    },
  }));
  await wrapped(0, prompt);
  assert.equal(nodes[0].widgets[1].value, 8, "a shared upstream seed commits when one output executes");
}

{
  const nodes = [advancedNode(10, ADVANCED, 7), advancedNode(11, ADVANCED_V2, 30)];
  const fixture = createFixture({ nodes });
  const prompt = promptFor(nodes, {
    consumers: [
      { id: 20, source: 10 },
      { id: 21, source: 11 },
    ],
  });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "partial-valid",
    node_errors: {
      99: { errors: ["bad input"], dependent_outputs: ["20"] },
    },
  }));
  await wrapped(0, prompt);
  assert.equal(nodes[0].widgets[1].value, 7, "errored branch must not commit");
  assert.equal(nodes[1].widgets[1].value, 31, "unrelated valid branch must commit");
}

{
  const nodes = [advancedNode(10, ADVANCED, 7), advancedNode(11, ADVANCED_V2, 30)];
  const fixture = createFixture({ nodes });
  const prompt = promptFor(nodes, {
    consumers: [
      { id: 20, source: 10 },
      { id: 21, source: 11 },
    ],
  });
  let received = null;
  const options = { partialExecutionTargets: ["20"], previewMethod: "none" };
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt, nextOptions) => {
    received = nextPrompt;
    assert.equal(nextOptions, options);
    return { prompt_id: "partial-target", node_errors: {} };
  });
  await wrapped(0, prompt, options);
  assert.equal(queuedSeed(received, 10), 7);
  assert.equal(workflowSeed(received, 10), 7);
  assert.equal(queuedSeed(received, 11), 30, "unselected branch output must remain unchanged");
  assert.equal(workflowSeed(received, 11), 30, "unselected workflow metadata must remain unchanged");
  assert.equal(nodes[0].widgets[1].value, 8);
  assert.equal(nodes[1].widgets[1].value, 30);
}

{
  const fixture = createFixture();
  const prompt = promptFor(fixture.nodes);
  for (const options of [
    { partialExecutionTargets: [] },
    { partialExecutionTargets: "20" },
    { partialExecutionTargets: [999] },
  ]) {
    let received = null;
    const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
      received = nextPrompt;
      return { prompt_id: "empty-partial", node_errors: {} };
    });
    await wrapped(0, prompt, options);
    assert.equal(received, prompt, "empty or invalid partial execution must pass through");
  }
  assert.equal(fixture.nodes[0].widgets[1].value, 7);
  assert.equal(fixture.cloneCalls(), 0);
}

{
  const fixture = createFixture();
  const gate = deferred();
  const node = fixture.nodes[0];
  const wrapped = fixture.runtime.wrapQueuePrompt(() => gate.promise);
  const pending = wrapped(0, promptFor([node]));
  assert.equal(fixture.runtime.trackedStateCount(), 1);
  assert.equal(
    fixture.runtime.attachNode(node),
    true,
    "reconfiguring the same object must attach a new lifecycle epoch",
  );
  assert.equal(fixture.runtime.trackedStateCount(), 2);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(node, 8),
    false,
    "the new same-object epoch must block the old epoch's executed seed",
  );
  gate.resolve({ prompt_id: "same-object-old-epoch", node_errors: {} });
  await pending;
  assert.deepEqual(fixture.commits, []);
  assert.equal(node.widgets[1].value, 7, "late settlement must not publish across epochs");
  assert.equal(fixture.runtime.trackedStateCount(), 1);
  fixture.runtime.detachNode(node);
  assert.equal(fixture.runtime.trackedStateCount(), 0);
}

{
  for (const invalidId of [
    null,
    undefined,
    "",
    "   ",
    -1,
    "-1",
    1.5,
    Number.MAX_SAFE_INTEGER + 1,
    Number.NaN,
    Infinity,
    -Infinity,
  ]) {
    const node = advancedNode(invalidId, ADVANCED, 7);
    const fixture = createFixture({ nodes: [node] });
    const prompt = promptFor([node]);
    assert.equal(fixture.runtime.attachNode(node), false);
    assert.equal(fixture.runtime.trackedStateCount(), 0);
    assert.equal(fixture.runtime.preparePrompt(prompt), null);
    assert.equal(fixture.runtime.trackedStateCount(), 0);
    let received = null;
    const result = { prompt_id: "invalid-node-id-pass-through", node_errors: {} };
    const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
      received = nextPrompt;
      return result;
    });
    assert.equal(await wrapped(0, prompt), result);
    assert.equal(received, prompt, "invalid node ids must remain on the unmanaged pass-through path");
    assert.equal(fixture.runtime.trackedStateCount(), 0);
    assert.equal(fixture.runtime.detachNode(node), false);
    assert.equal(fixture.runtime.shouldApplyExecutedSeed(node, 8), true);
  }
}

{
  const fixture = createFixture();
  const node = fixture.nodes[0];
  assert.equal(fixture.runtime.attachNode(node), true);
  assert.equal(fixture.runtime.trackedStateCount(), 1);
  assert.equal(fixture.runtime.detachNode(node), true);
  assert.equal(
    fixture.runtime.trackedStateCount(),
    0,
    "removing an idle node must release its managed state immediately",
  );
}

{
  const fixture = createFixture();
  let current = fixture.nodes[0];
  fixture.runtime.attachNode(current);
  for (let index = 0; index < 50; index += 1) {
    assert.equal(fixture.runtime.detachNode(current), true);
    current = advancedNode(1000 + index, ADVANCED, index);
    fixture.nodes.splice(0, 1, current);
    assert.equal(fixture.runtime.attachNode(current), true);
    assert.equal(
      fixture.runtime.trackedStateCount(),
      1,
      "repeated workflow replacement must retain only the live idle owner",
    );
  }
  fixture.runtime.clearGraphNodes();
  assert.equal(
    fixture.runtime.trackedStateCount(),
    0,
    "graph clear must release every idle managed owner",
  );
}

{
  const fixture = createFixture();
  const gate = deferred();
  const oldNode = fixture.nodes[0];
  const wrapped = fixture.runtime.wrapQueuePrompt(() => gate.promise);
  const pending = wrapped(0, promptFor([oldNode]));
  assert.equal(fixture.runtime.trackedStateCount(), 1);

  fixture.runtime.clearGraphNodes();
  assert.equal(
    fixture.runtime.trackedStateCount(),
    1,
    "graph clear must retain a detached state until its queue settles",
  );

  const replacement = advancedNode(10, ADVANCED, 100);
  fixture.nodes.splice(0, 1, replacement);
  assert.equal(fixture.runtime.attachNode(replacement), true);
  assert.equal(
    fixture.runtime.trackedStateCount(),
    2,
    "a pending retired owner and its same-id replacement must have separate identities",
  );
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(replacement, 8),
    false,
    "a configured same-id replacement must reject the retired owner's executed seed",
  );

  gate.resolve({ prompt_id: "retired-owner", node_errors: {} });
  await pending;
  assert.equal(oldNode.widgets[1].value, 7, "late settlement must not publish to a removed owner");
  assert.equal(replacement.widgets[1].value, 100, "late settlement must not publish to a new owner");
  assert.deepEqual(fixture.commits, []);
  assert.equal(
    fixture.runtime.trackedStateCount(),
    1,
    "settlement must release the retired state and retain only the live owner",
  );
  fixture.runtime.detachNode(replacement);
  assert.equal(fixture.runtime.trackedStateCount(), 0);
}

{
  const fixture = createFixture();
  const wrapped = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "old-workflow", node_errors: {},
  }));
  await wrapped(0, promptFor(fixture.nodes));
  const oldNode = fixture.nodes[0];
  const replacement = advancedNode(10, ADVANCED, 100);
  fixture.nodes.splice(0, 1, replacement);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(replacement, 8),
    false,
    "a late executed event must not overwrite a reloaded node with the same id",
  );
  await wrapped(0, promptFor([replacement]));
  assert.equal(replacement.widgets[1].value, 101);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(replacement, 101), true);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(oldNode, 101), false);
}

{
  const fixture = createFixture();
  const wrapped = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "old-safe-workflow", node_errors: {},
  }));
  await wrapped(0, promptFor(fixture.nodes));
  const replacement = advancedNode(10, ADVANCED, Number.MAX_SAFE_INTEGER + 1);
  fixture.nodes.splice(0, 1, replacement);
  const prompt = promptFor([replacement]);
  let received = null;
  const passThrough = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "replacement-unsafe", node_errors: {} };
  });
  await passThrough(0, prompt);
  assert.equal(received, prompt);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(replacement, 0),
    true,
    "a replacement's backend pass-through update may return to the safe range",
  );
}

{
  const fixture = createFixture();
  const host = {
    calls: 0,
    queuePrompt() {
      this.calls += 1;
      return { prompt_id: "installed", node_errors: {} };
    },
  };
  assert.equal(queueModule.installAdvancedQueueSeedQueueHook(host, fixture.runtime), true);
  const installed = host.queuePrompt;
  assert.equal(queueModule.installAdvancedQueueSeedQueueHook(host, fixture.runtime), false);
  assert.equal(host.queuePrompt, installed, "repeated setup must not stack wrappers");
  host.queuePrompt = async function (...args) {
    return installed.apply(this, args);
  };
  const foreignWrapper = host.queuePrompt;
  assert.equal(queueModule.installAdvancedQueueSeedQueueHook(host, fixture.runtime), false);
  assert.equal(host.queuePrompt, foreignWrapper, "the host marker survives foreign wrapper composition");
  const result = await host.queuePrompt(0, promptFor(fixture.nodes));
  assert.equal(result.prompt_id, "installed");
  assert.equal(host.calls, 1);
}

{
  const cloneError = new Error("clone failed");
  const fixture = createFixture({ cloneError });
  const prompt = promptFor(fixture.nodes);
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "pass-through", node_errors: {} };
  });
  await wrapped(0, prompt);
  assert.equal(received, prompt);
  assert.equal(fixture.nodes[0].widgets[1].value, 7);
  assert.equal(fixture.cloneCalls(), 1);
}

{
  const fixture = createFixture();
  const prompt = {};
  Object.defineProperty(prompt, "output", {
    get() {
      throw new Error("malformed output getter");
    },
  });
  let received = null;
  const result = { prompt_id: "malformed-prompt-pass-through", node_errors: {} };
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return result;
  });
  assert.equal(await wrapped(0, prompt), result);
  assert.equal(received, prompt);
  assert.equal(fixture.nodes[0].widgets[1].value, 7);
}

{
  const fixture = createFixture();
  const result = { prompt_id: "malformed-validation" };
  Object.defineProperty(result, "node_errors", {
    get() {
      throw new Error("malformed node_errors getter");
    },
  });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => result);
  assert.equal(await wrapped(0, promptFor(fixture.nodes)), result);
  assert.equal(fixture.nodes[0].widgets[1].value, 7);
}

console.log("Frontend Prompt Studio Advanced queue seed runtime smoke passed.");
