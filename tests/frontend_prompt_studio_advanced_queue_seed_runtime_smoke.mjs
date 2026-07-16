import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
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
    "installAdvancedQueueSeedQueueHook",
  ],
);

const ADVANCED = "EasyUseAnimaPromptStudioAdvanced";
const ADVANCED_V2 = "EasyUseAnimaPromptStudioAdvancedV2";
const SEED_INDEX = 11;

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
  for (const consumer of options.consumers || []) {
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
  const randomValues = [...(options.randomValues || [41, 42, 43, 44])];
  const commits = [];
  let randomCalls = 0;
  let cloneCalls = 0;
  const runtime = queueModule.createAdvancedQueueSeedRuntime({
    seedWidgetIndex: SEED_INDEX,
    listNodes: () => nodes,
    isAdvancedNode: (node) => [ADVANCED, ADVANCED_V2].includes(node?.type),
    getSeed(node) {
      return node.widgets.find((widget) => widget.name === "wildcard_seed")?.value;
    },
    updateSeed(node, seed) {
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
  assert.equal(queuedSeed(transaction.prompt, 11), 27);
  assert.equal(workflowSeed(transaction.prompt, 11), 27);
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
    queued.push(queuedSeed(prompt, 10));
    return { prompt_id: `random-${queued.length}`, node_errors: {} };
  });
  await Promise.all([
    wrapped(0, promptFor([node])),
    wrapped(0, promptFor([node])),
    wrapped(0, promptFor([node])),
  ]);
  assert.deepEqual(queued, [7, 41, 42]);
  assert.equal(node.widgets[1].value, 43);
  assert.equal(fixture.randomCalls(), 3);
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
