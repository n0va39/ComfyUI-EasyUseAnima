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
  ["consume", "consumeWithinTurn", "dispose", "install", "peek"],
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
assert.throws(
  () => createExecutedEventContext({
    addEventListener() {},
    removeEventListener() {},
  }, { scheduleMicrotask: "invalid" }),
  /scheduleMicrotask/,
);

// ComfyApi is one EventTarget. Listeners on that same target run in registration
// order even when a later listener requests capture.
class OrderedEventTargetFixture {
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
    for (const listener of listeners) {
      listener.callback.call(this, event);
    }
    return true;
  }
}

function createMicrotaskFixture() {
  const callbacks = [];
  return {
    schedule(callback) {
      callbacks.push(callback);
    },
    get size() {
      return callbacks.length;
    },
    flush() {
      const queued = callbacks.splice(0);
      for (const callback of queued) {
        callback();
      }
    },
  };
}

function event(type, detail) {
  return { type, detail };
}

{
  const api = new OrderedEventTargetFixture();
  const trace = [];
  let delivery;
  const bridge = createExecutedEventContext(api);
  assert.equal(bridge.install(), true);
  assert.equal(bridge.install(), false);
  const node = {
    onExecuted(message) {
      trace.push("node-onExecuted");
      delivery = bridge.consumeWithinTurn(message);
    },
  };

  // Bridge-first ordering consumes synchronously through the existing API.
  api.addEventListener("executed", ({ detail }) => {
    trace.push(bridge.peek(detail.output) ? "captured-before-core" : "missing");
    trace.push("core-listener");
    node.onExecuted(detail.output);
  });

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
  const consumedEnvelope = await delivery;
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
  const api = new OrderedEventTargetFixture();
  const microtasks = createMicrotaskFixture();
  const trace = [];
  let bridge;
  let delivery;
  const node = {
    onExecuted(message) {
      trace.push("node-onExecuted");
      delivery = bridge.consumeWithinTurn(message);
    },
  };

  // Mirrors the supported live order: core registered first, then the bridge.
  api.addEventListener("executed", ({ detail }) => {
    trace.push("core-listener");
    node.onExecuted(detail.output);
  });
  bridge = createExecutedEventContext(api, {
    scheduleMicrotask: microtasks.schedule,
  });
  bridge.install();

  const output = { feature_payload: [{ value: "accepted-late" }] };
  api.dispatchEvent(event("executed", {
    prompt_id: "prompt-node-first",
    node: "backend-node",
    display_node: "frontend-node",
    output,
  }));

  assert.deepEqual(trace, ["core-listener", "node-onExecuted"]);
  assert.equal(microtasks.size, 1);
  const envelope = await delivery;
  assert(envelope);
  assert.equal(envelope.promptId, "prompt-node-first");
  assert.equal(envelope.output, output);
  assert.equal(bridge.peek(output), null);
  assert.equal(bridge.consume(output), null);
  microtasks.flush();
  assert.equal(microtasks.size, 0);
}

{
  const api = new OrderedEventTargetFixture();
  const microtasks = createMicrotaskFixture();
  let bridge;
  const clonedDeliveries = [];
  const originalOutputs = [];
  const node = {
    onExecuted(message) {
      clonedDeliveries.push(bridge.consumeWithinTurn(message));
    },
  };

  api.addEventListener("executed", ({ detail }) => {
    node.onExecuted({ ...detail.output });
  });
  bridge = createExecutedEventContext(api, {
    maxPendingOutputs: 2,
    scheduleMicrotask: microtasks.schedule,
  });
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

  assert.equal(microtasks.size, 3);
  microtasks.flush();
  assert.deepEqual(await Promise.all(clonedDeliveries), [null, null, null]);
  assert.equal(bridge.peek(originalOutputs[0]), null);
  assert.equal(bridge.peek(originalOutputs[1])?.promptId, "prompt-clone-1");
  assert.equal(bridge.consume(originalOutputs[2])?.promptId, "prompt-clone-2");
  assert.equal(bridge.peek(originalOutputs[2]), null);
}

{
  const api = new OrderedEventTargetFixture();
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
  const api = new OrderedEventTargetFixture();
  const microtasks = createMicrotaskFixture();
  let bridge;
  const deliveries = [];
  const node = {
    onExecuted(message) {
      deliveries.push(bridge.consumeWithinTurn(message));
    },
  };
  api.addEventListener("executed", ({ detail }) => {
    node.onExecuted(detail.output);
  });
  bridge = createExecutedEventContext(api, {
    scheduleMicrotask: microtasks.schedule,
  });
  bridge.install();

  api.dispatchEvent(event("executed", {
    node: "backend-node",
    output: { missing: "prompt-id" },
  }));
  microtasks.flush();
  assert.deepEqual(await Promise.all(deliveries), [null]);
  assert.equal(bridge.dispose(), true);
}

{
  const api = new OrderedEventTargetFixture();
  const microtasks = createMicrotaskFixture();
  const bridge = createExecutedEventContext(api, {
    scheduleMicrotask: microtasks.schedule,
  });
  bridge.install();

  const output = { expires: true };
  const delivery = bridge.consumeWithinTurn(output);
  assert.equal(microtasks.size, 1);
  microtasks.flush();
  assert.equal(await delivery, null);

  api.dispatchEvent(event("executed", {
    prompt_id: "prompt-after-expiry",
    node: "backend-node",
    output,
  }));
  assert.equal(bridge.consume(output)?.promptId, "prompt-after-expiry");
  assert.equal(bridge.consume(output), null);
  assert.equal(bridge.dispose(), true);
}

{
  const api = new OrderedEventTargetFixture();
  const microtasks = createMicrotaskFixture();
  const bridge = createExecutedEventContext(api, {
    scheduleMicrotask: microtasks.schedule,
  });
  bridge.install();

  const output = { duplicate: true };
  const first = bridge.consumeWithinTurn(output);
  const duplicate = bridge.consumeWithinTurn(output);
  assert.equal(await duplicate, null);
  api.dispatchEvent(event("executed", {
    prompt_id: "prompt-duplicate",
    node: "backend-node",
    output,
  }));
  assert.equal((await first)?.promptId, "prompt-duplicate");
  assert.equal(bridge.consume(output), null);
  microtasks.flush();
  assert.equal(bridge.dispose(), true);
}

{
  const api = new OrderedEventTargetFixture();
  const microtasks = createMicrotaskFixture();
  const bridge = createExecutedEventContext(api, {
    scheduleMicrotask: microtasks.schedule,
  });
  bridge.install();

  const output = { disposed: true };
  const delivery = bridge.consumeWithinTurn(output);
  assert.equal(bridge.dispose(), true);
  assert.equal(bridge.dispose(), false);
  assert.equal(await delivery, null);
  microtasks.flush();
  api.dispatchEvent(event("executed", {
    prompt_id: "prompt-after-dispose",
    node: "backend-node",
    output,
  }));
  assert.equal(bridge.peek(output), null);
  assert.equal(bridge.install(), true);
  assert.equal(bridge.dispose(), true);
}

{
  const api = new OrderedEventTargetFixture();
  const microtasks = createMicrotaskFixture();
  const bridge = createExecutedEventContext(api, {
    maxPendingOutputs: 2,
    scheduleMicrotask: microtasks.schedule,
  });
  bridge.install();

  const outputs = [{ index: 0 }, { index: 1 }, { index: 2 }];
  const deliveries = outputs.map(
    (output) => bridge.consumeWithinTurn(output),
  );
  assert.equal(await deliveries[0], null);
  for (let index = 1; index < outputs.length; index += 1) {
    api.dispatchEvent(event("executed", {
      prompt_id: `prompt-bounded-${index}`,
      node: "backend-node",
      output: outputs[index],
    }));
  }
  assert.equal((await deliveries[1])?.promptId, "prompt-bounded-1");
  assert.equal((await deliveries[2])?.promptId, "prompt-bounded-2");
  assert.equal(bridge.peek(outputs[1]), null);
  assert.equal(bridge.peek(outputs[2]), null);
  microtasks.flush();
  assert.equal(bridge.dispose(), true);
}

console.log("Executed event context production smoke passed.");
