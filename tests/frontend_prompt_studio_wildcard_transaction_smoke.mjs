import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const ownerModule = await import(dataModule(
  "../web/js/lifecycle/queue_ui_transaction.js",
));
const contextModule = await import(dataModule(
  "../web/js/lifecycle/executed_event_context.js",
));
const transactionModule = await import(dataModule(
  "../web/js/prompt_studio/execution_transaction.js",
));

assert.deepEqual(
  Object.keys(transactionModule).sort(),
  ["createPromptStudioExecutionTransaction"],
);

const WILDCARD_SEED_CONTROL_SURFACE = "prompt.wildcard_seed_control";

class FakeApi {
  constructor() {
    this.listeners = new Map();
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  removeEventListener(type, listener) {
    this.listeners.set(
      type,
      (this.listeners.get(type) || []).filter((candidate) => candidate !== listener),
    );
  }

  emit(type, detail) {
    for (const listener of this.listeners.get(type) || []) {
      listener({ detail });
    }
  }
}

function createNode(id) {
  const callbackLog = [];
  const widgets = [
    {
      name: "wildcard_seed",
      value: 7,
      callback(value) { callbackLog.push(["seed", value]); },
    },
    {
      name: "wildcard_seed_after_generate",
      value: "fixed",
      callback(value) { callbackLog.push(["control", value]); },
    },
  ];
  return { id, widgets, callbackLog };
}

function createHarness() {
  const api = new FakeApi();
  const transactionOwner = ownerModule.createQueueUiTransactionOwner();
  let settleCount = 0;
  const owner = Object.freeze({
    ...transactionOwner,
    settle(...args) {
      settleCount += 1;
      return transactionOwner.settle(...args);
    },
  });
  let runtime;
  const executedContext = contextModule.createExecutedEventContext(api, {
    finishPrompt: (promptId) => runtime.finishPrompt(promptId),
  });
  runtime = transactionModule.createPromptStudioExecutionTransaction({
    owner,
    executedContext,
    findWidget: (node, name) => node.widgets.find((widget) => widget.name === name),
    editBindings: [{
      widgetNames: ["wildcard_seed", "wildcard_seed_after_generate"],
      surfaces: [WILDCARD_SEED_CONTROL_SURFACE],
    }],
  });
  executedContext.install();
  return {
    api,
    executedContext,
    runtime,
    settleCount: () => settleCount,
  };
}

function accepted(
  runtime,
  node,
  promptId,
  surfaces = [WILDCARD_SEED_CONTROL_SURFACE],
) {
  const captured = runtime.captureQueue([{ node, surfaces }]);
  assert.equal(captured.length, 1);
  assert.equal(
    runtime.acceptQueue(captured, { ok: true, result: { prompt_id: promptId } }),
    1,
  );
  return captured[0].transaction;
}

function captureEnvelope(api, promptId, node, output) {
  api.emit("executed", {
    prompt_id: promptId,
    node: String(node.id),
    output,
  });
}

{
  const { api, runtime } = createHarness();
  const node = createNode(7);
  const transaction = accepted(runtime, node, "prompt-current");
  const output = { prompt_studio_advanced: [{ wildcard_seed: 8 }] };
  let commitCount = 0;
  captureEnvelope(api, "prompt-current", node, output);
  assert.equal(
    await runtime.consumeExecution(node, output, 1, [{
      surface: WILDCARD_SEED_CONTROL_SURFACE,
      commit: () => { commitCount += 1; },
    }]),
    true,
  );
  assert.equal(commitCount, 1);
  assert.equal(transaction.state, "settled");
  assert.equal(transaction.reason, "executed");
  assert.equal(
    await runtime.consumeExecution(node, output, 1),
    false,
    "duplicate must fail closed",
  );
}

{
  const { api, runtime } = createHarness();
  const node = createNode("node-first");
  const transaction = accepted(runtime, node, "prompt-node-first");
  const output = { prompt_studio_advanced: [{ wildcard_seed: 8 }] };
  let commitCount = 0;
  const delivery = runtime.consumeExecution(
    node,
    output,
    1,
    [{
      surface: WILDCARD_SEED_CONTROL_SURFACE,
      commit: () => { commitCount += 1; },
    }],
  );
  captureEnvelope(api, "prompt-node-first", node, output);
  assert.equal(await delivery, true, "node-first delivery must wait within the event turn");
  assert.equal(commitCount, 1);
  assert.equal(transaction.state, "settled");
}

for (const widgetName of ["wildcard_seed", "wildcard_seed_after_generate"]) {
  const { api, runtime } = createHarness();
  const node = createNode(widgetName);
  const transaction = accepted(runtime, node, `prompt-edited-${widgetName}`);
  const widget = node.widgets.find((candidate) => candidate.name === widgetName);
  widget.callback(widget.value);
  assert.equal(node.callbackLog.length, 1, "wrapped callback must preserve the feature callback");
  const output = { prompt_studio_advanced: [{ wildcard_seed: 9 }] };
  let commitCount = 0;
  captureEnvelope(api, transaction.promptId, node, output);
  assert.equal(
    await runtime.consumeExecution(node, output, 1, [{
      surface: WILDCARD_SEED_CONTROL_SURFACE,
      commit: () => { commitCount += 1; },
    }]),
    false,
    `${widgetName} edit must invalidate the atomic seed/control surface`,
  );
  assert.equal(commitCount, 0);
  assert.equal(transaction.state, "settled");
}

{
  const { api, runtime } = createHarness();
  const node = createNode(8);
  accepted(runtime, node, "prompt-clone");
  const output = { prompt_studio_advanced: [{ wildcard_seed: 10 }] };
  captureEnvelope(api, "prompt-clone", node, output);
  assert.equal(
    await runtime.consumeExecution(node, structuredClone(output), 1),
    false,
    "cloned output must fail closed",
  );
  assert.equal(await runtime.consumeExecution(node, output, 1, [{
    surface: WILDCARD_SEED_CONTROL_SURFACE,
    commit: () => {},
  }]), true);
}

{
  const { api, runtime } = createHarness();
  const node = createNode(9);
  const transaction = accepted(runtime, node, "prompt-mapped");
  const output = {
    prompt_studio_advanced: [
      { wildcard_seed: 11 },
      { wildcard_seed: 12 },
    ],
  };
  captureEnvelope(api, "prompt-mapped", node, output);
  assert.equal(
    await runtime.consumeExecution(node, output, 2, [{
      surface: WILDCARD_SEED_CONTROL_SURFACE,
      commit: () => {},
    }]),
    false,
    "multiple mapped payloads must not publish editable state",
  );
  assert.equal(transaction.state, "settled");
}

{
  const { api, runtime } = createHarness();
  const node = createNode(10);
  const captured = runtime.captureQueue([{
    node,
    surfaces: [WILDCARD_SEED_CONTROL_SURFACE],
  }]);
  const transaction = captured[0].transaction;
  const output = { prompt_studio_advanced: [{ wildcard_seed: 14 }] };
  let commitCount = 0;
  captureEnvelope(api, "prompt-out-of-order", node, output);
  assert.equal(
    await runtime.consumeExecution(node, output, 1, [{
      surface: WILDCARD_SEED_CONTROL_SURFACE,
      commit: () => { commitCount += 1; },
    }]),
    false,
    "executed-before-accept must defer editable publication",
  );
  assert.equal(transaction.state, "provisional");
  assert.equal(commitCount, 0);
  assert.equal(
    runtime.acceptQueue(captured, {
      ok: true,
      result: { prompt_id: "prompt-out-of-order" },
    }),
    1,
  );
  assert.equal(commitCount, 1, "acceptance must finalize the deferred commit once");
  assert.equal(transaction.state, "settled");
}

{
  const { runtime } = createHarness();
  const node = createNode(11);
  const captured = runtime.captureQueue([{
    node,
    surfaces: [WILDCARD_SEED_CONTROL_SURFACE],
  }]);
  assert.equal(runtime.acceptQueue(captured, { ok: true, result: {} }), 0);
  assert.equal(captured[0].transaction.state, "cancelled");
  assert.equal(captured[0].transaction.reason, "reject");
}

{
  const { api, runtime } = createHarness();
  const node = createNode(12);
  const transaction = accepted(runtime, node, "prompt-disposed");
  assert.equal(runtime.disposeNode(node, "remove"), true);
  const output = { prompt_studio_advanced: [{ wildcard_seed: 13 }] };
  captureEnvelope(api, "prompt-disposed", node, output);
  assert.equal(await runtime.consumeExecution(node, output, 1), false);
  assert.equal(transaction.state, "cancelled");
  assert.equal(transaction.reason, "remove");
}

{
  const { api, runtime } = createHarness();
  const node = createNode(13);
  const transaction = accepted(runtime, node, "prompt-terminal");
  api.emit("execution_error", { prompt_id: "prompt-terminal" });
  assert.equal(transaction.state, "finished");
  assert.equal(transaction.reason, "prompt-terminal");
}

{
  const { api, runtime, settleCount } = createHarness();
  const node = createNode("fan-out");
  const surfaces = [
    WILDCARD_SEED_CONTROL_SURFACE,
    "prompt.execution.linked:positive_general",
    "prompt.execution.naia:positive_naia",
  ];
  const transaction = accepted(runtime, node, "prompt-fan-out", surfaces);
  const output = { prompt_studio_advanced: [{ wildcard_seed: 15 }] };
  const commits = [];
  captureEnvelope(api, "prompt-fan-out", node, output);
  assert.equal(await runtime.consumeExecution(node, output, 1, [
    {
      surface: WILDCARD_SEED_CONTROL_SURFACE,
      commit: () => { commits.push("wildcard"); },
    },
    {
      surface: "prompt.execution.linked:positive_general",
      commit: () => { commits.push("linked"); },
    },
    {
      surface: "prompt.execution.naia:positive_naia",
      commit: () => { commits.push("naia"); },
    },
  ]), true);
  assert.deepEqual(commits, ["wildcard", "linked", "naia"]);
  assert.equal(transaction.state, "settled", "one fan-out must settle once");
  assert.equal(settleCount(), 1);
  assert.equal(
    await runtime.consumeExecution(node, output, 1, [{
      surface: WILDCARD_SEED_CONTROL_SURFACE,
      commit: () => { commits.push("duplicate"); },
    }]),
    false,
    "the consumed envelope must not fan out twice",
  );
  assert.deepEqual(commits, ["wildcard", "linked", "naia"]);
  assert.equal(settleCount(), 1, "duplicate delivery must not settle twice");
}

console.log("Prompt Studio execution transaction and Wildcard parity smoke passed.");
