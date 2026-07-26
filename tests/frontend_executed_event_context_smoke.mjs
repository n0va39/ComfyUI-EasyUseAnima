import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const contextModule = await import(dataModule(
  "../web/js/lifecycle/executed_event_context.js",
));
const transactionModule = await import(dataModule(
  "../web/js/lifecycle/queue_ui_transaction.js",
));
const { createExecutedEventContext } = contextModule;
const { createQueueUiTransactionOwner } = transactionModule;

assert.deepEqual(Object.keys(contextModule), ["createExecutedEventContext"]);
assert.deepEqual(
  Object.keys(createExecutedEventContext({
    addEventListener() {},
    removeEventListener() {},
  })).sort(),
  ["consume", "dispose", "install", "peek"],
);
assert.throws(() => createExecutedEventContext(null), /Comfy API/);
assert.throws(
  () => createExecutedEventContext({
    addEventListener() {},
    removeEventListener() {},
  }, { maxPendingOutputs: 0 }),
  /positive integer/,
);
assert.throws(
  () => createExecutedEventContext({
    addEventListener() {},
    removeEventListener() {},
  }, { finishPrompt: "invalid" }),
  /finishPrompt/,
);

// Node's flat EventTarget does not model a browser capture phase. This fixture
// preserves supported DOM target ordering: capture listeners run before normal
// listeners even when the core normal listener was registered first.
class BrowserPhaseEventTargetFixture {
  constructor() {
    this.listeners = new Map();
  }

  addEventListener(type, callback, options = {}) {
    const capture = typeof options === "boolean"
      ? options
      : Boolean(options?.capture);
    const listeners = this.listeners.get(type) || [];
    if (!listeners.some(
      (listener) => listener.callback === callback && listener.capture === capture,
    )) {
      listeners.push({ callback, capture });
      this.listeners.set(type, listeners);
    }
  }

  removeEventListener(type, callback, options = {}) {
    const capture = typeof options === "boolean"
      ? options
      : Boolean(options?.capture);
    const listeners = this.listeners.get(type) || [];
    this.listeners.set(
      type,
      listeners.filter(
        (listener) => listener.callback !== callback || listener.capture !== capture,
      ),
    );
  }

  dispatchEvent(event) {
    const listeners = [...(this.listeners.get(event.type) || [])];
    for (const capture of [true, false]) {
      for (const listener of listeners) {
        if (listener.capture === capture) {
          listener.callback.call(this, event);
        }
      }
    }
    return true;
  }
}

function event(type, detail) {
  return { type, detail };
}

{
  const api = new BrowserPhaseEventTargetFixture();
  const trace = [];
  let bridge;
  let consumedEnvelope = null;
  const node = {
    onExecuted(message) {
      trace.push("node-onExecuted");
      consumedEnvelope = bridge.consume(message);
    },
  };

  // Mirrors current ComfyUI app.ts: core registers first and passes the exact
  // detail.output object to node.onExecuted().
  api.addEventListener("executed", ({ detail }) => {
    trace.push(bridge.peek(detail.output) ? "captured-before-core" : "missing");
    trace.push("core-listener");
    node.onExecuted(detail.output);
  });

  bridge = createExecutedEventContext(api);
  assert.equal(bridge.install(), true);
  assert.equal(bridge.install(), false);

  const output = { feature_payload: [{ value: "accepted" }] };
  api.dispatchEvent(event("executed", {
    prompt_id: "prompt-a",
    node: "backend-node",
    display_node: "frontend-node",
    output,
  }));

  assert.deepEqual(trace, [
    "captured-before-core",
    "core-listener",
    "node-onExecuted",
  ]);
  assert(consumedEnvelope);
  assert.equal(Object.isFrozen(consumedEnvelope), true);
  assert.equal(consumedEnvelope.promptId, "prompt-a");
  assert.equal(consumedEnvelope.executionNodeId, "backend-node");
  assert.equal(consumedEnvelope.displayNodeId, "frontend-node");
  assert.equal(consumedEnvelope.output, output);
  assert.equal(bridge.peek(output), null);
  assert.equal(bridge.consume(output), null);
  assert.equal(bridge.consume({ ...output }), null);
}

{
  const api = new BrowserPhaseEventTargetFixture();
  let bridge;
  const clonedConsumes = [];
  const originalOutputs = [];
  const node = {
    onExecuted(message) {
      clonedConsumes.push(bridge.consume(message));
    },
  };

  api.addEventListener("executed", ({ detail }) => {
    node.onExecuted({ ...detail.output });
  });
  bridge = createExecutedEventContext(api, { maxPendingOutputs: 2 });
  bridge.install();

  for (let index = 0; index < 3; index += 1) {
    const output = { index };
    originalOutputs.push(output);
    api.dispatchEvent(event("executed", {
      prompt_id: `prompt-clone-${index}`,
      node: "backend-node",
      output,
    }));
  }

  assert.deepEqual(clonedConsumes, [null, null, null]);
  assert.equal(bridge.peek(originalOutputs[0]), null);
  assert.equal(bridge.peek(originalOutputs[1])?.promptId, "prompt-clone-1");
  assert.equal(bridge.consume(originalOutputs[2])?.promptId, "prompt-clone-2");
  assert.equal(bridge.peek(originalOutputs[2]), null);
}

{
  const api = new BrowserPhaseEventTargetFixture();
  const owner = createQueueUiTransactionOwner();
  const bridge = createExecutedEventContext(api, {
    finishPrompt: owner.finishPrompt,
  });
  bridge.install();

  for (const terminalType of [
    "execution_success",
    "execution_error",
    "execution_interrupted",
  ]) {
    const node = {};
    const promptId = `prompt-${terminalType}`;
    const transaction = owner.captureProvisional({
      node,
      surfaces: ["opaque-surface"],
    });
    assert(transaction);
    assert.equal(owner.acceptPrompt(transaction, promptId), true);

    const output = { terminalType };
    api.dispatchEvent(event("executed", {
      prompt_id: promptId,
      node: "backend-node",
      output,
    }));
    assert.equal(bridge.peek(output)?.promptId, promptId);

    api.dispatchEvent(event(terminalType, {
      prompt_id: promptId,
      timestamp: Date.now(),
    }));
    assert.equal(transaction.state, "finished");
    assert.equal(transaction.reason, "prompt-terminal");
    assert.equal(bridge.peek(output), null);
    assert.equal(owner.finishPrompt(promptId), 0);
  }

  const stillAccepted = owner.captureProvisional({
    node: {},
    surfaces: ["opaque-surface"],
  });
  assert(stillAccepted);
  assert.equal(owner.acceptPrompt(stillAccepted, "prompt-missing-terminal"), true);
  api.dispatchEvent(event("execution_success", { timestamp: Date.now() }));
  assert.equal(stillAccepted.state, "accepted");
  assert.equal(owner.cancel(stillAccepted), true);
}

{
  const api = new BrowserPhaseEventTargetFixture();
  let bridge;
  const consumes = [];
  const node = {
    onExecuted(message) {
      consumes.push(bridge.consume(message));
    },
  };
  api.addEventListener("executed", ({ detail }) => {
    node.onExecuted(detail.output);
  });
  bridge = createExecutedEventContext(api);
  bridge.install();

  api.dispatchEvent(event("executed", {
    node: "backend-node",
    output: { missing: "prompt-id" },
  }));
  assert.deepEqual(consumes, [null]);

  assert.equal(bridge.dispose(), true);
  assert.equal(bridge.dispose(), false);
  api.dispatchEvent(event("executed", {
    prompt_id: "prompt-after-dispose",
    node: "backend-node",
    output: {},
  }));
  assert.deepEqual(consumes, [null, null]);
  assert.equal(bridge.install(), true);
  assert.equal(bridge.dispose(), true);
}

console.log("Executed event context production smoke passed.");
