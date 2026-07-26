import assert from "node:assert/strict";

// QSTATE-02B contract-only fixture. Node's flat EventTarget does not model a
// browser capture phase, so this test-local host preserves the DOM ordering the
// ComfyUI adapter relies on: capture listeners run before normal listeners at
// the target, even when the capture listener was registered later.
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

function createExecutedEventContext(
  api,
  { maxPendingOutputs = 2, onCapture = null } = {},
) {
  assert(Number.isInteger(maxPendingOutputs) && maxPendingOutputs > 0);

  let installed = false;
  let envelopesByOutput = new WeakMap();
  const pendingOutputs = [];

  function normalizedId(value) {
    if (typeof value === "string" && value.trim() !== "") {
      return value.trim();
    }
    if (typeof value === "number" && Number.isInteger(value)) {
      return String(value);
    }
    return null;
  }

  function envelopeFromDetail(detail) {
    const promptId = normalizedId(detail?.prompt_id);
    const executionNodeId = normalizedId(detail?.node);
    const displayNodeId = detail?.display_node == null
      ? null
      : normalizedId(detail.display_node);
    const output = detail?.output;
    if (
      promptId == null
      || executionNodeId == null
      || (detail?.display_node != null && displayNodeId == null)
      || output === null
      || (typeof output !== "object" && typeof output !== "function")
    ) {
      return null;
    }
    return { promptId, executionNodeId, displayNodeId, output };
  }

  function removePending(output) {
    const index = pendingOutputs.indexOf(output);
    if (index >= 0) {
      pendingOutputs.splice(index, 1);
    }
  }

  function captureExecuted({ detail }) {
    const envelope = envelopeFromDetail(detail);
    if (!envelope) {
      return;
    }
    removePending(envelope.output);
    envelopesByOutput.set(envelope.output, envelope);
    pendingOutputs.push(envelope.output);
    onCapture?.(envelope);

    while (pendingOutputs.length > maxPendingOutputs) {
      const expiredOutput = pendingOutputs.shift();
      envelopesByOutput.delete(expiredOutput);
    }
  }

  function install() {
    if (installed) {
      return false;
    }
    api.addEventListener("executed", captureExecuted, { capture: true });
    installed = true;
    return true;
  }

  function consume(output) {
    if (
      output === null
      || (typeof output !== "object" && typeof output !== "function")
    ) {
      return null;
    }
    const envelope = envelopesByOutput.get(output) || null;
    if (!envelope) {
      return null;
    }
    envelopesByOutput.delete(output);
    removePending(output);
    return envelope;
  }

  function dispose() {
    if (installed) {
      api.removeEventListener("executed", captureExecuted, { capture: true });
    }
    installed = false;
    envelopesByOutput = new WeakMap();
    pendingOutputs.length = 0;
  }

  return {
    install,
    consume,
    dispose,
    inspect: () => ({ installed, pendingCount: pendingOutputs.length }),
  };
}

function executedEvent(detail) {
  return { type: "executed", detail };
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

  // Mirrors current ComfyUI app.ts: the normal core listener is registered
  // first and passes the same detail.output object to node.onExecuted().
  api.addEventListener("executed", ({ detail }) => {
    trace.push("core-listener");
    node.onExecuted(detail.output);
  });

  bridge = createExecutedEventContext(api, {
    onCapture: () => trace.push("capture-listener"),
  });
  assert.equal(bridge.install(), true);
  assert.equal(bridge.install(), false);

  const output = { prompt_studio_inputs: [{ text: "accepted" }] };
  api.dispatchEvent(executedEvent({
    prompt_id: "prompt-a",
    node: "backend-node",
    display_node: "frontend-node",
    output,
  }));

  assert.deepEqual(trace, [
    "capture-listener",
    "core-listener",
    "node-onExecuted",
  ]);
  assert(consumedEnvelope);
  assert.equal(consumedEnvelope.promptId, "prompt-a");
  assert.equal(consumedEnvelope.executionNodeId, "backend-node");
  assert.equal(consumedEnvelope.displayNodeId, "frontend-node");
  assert.equal(consumedEnvelope.output, output);
  assert.deepEqual(bridge.inspect(), { installed: true, pendingCount: 0 });
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
    api.dispatchEvent(executedEvent({
      prompt_id: `prompt-clone-${index}`,
      node: "backend-node",
      output,
    }));
  }

  assert.deepEqual(clonedConsumes, [null, null, null]);
  assert.deepEqual(bridge.inspect(), { installed: true, pendingCount: 2 });
  assert.equal(bridge.consume(originalOutputs[0]), null);
  assert.equal(bridge.consume(originalOutputs[2])?.promptId, "prompt-clone-2");
  assert.deepEqual(bridge.inspect(), { installed: true, pendingCount: 1 });
  bridge.dispose();
  assert.deepEqual(bridge.inspect(), { installed: false, pendingCount: 0 });
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

  api.dispatchEvent(executedEvent({
    node: "backend-node",
    output: { missing: "prompt-id" },
  }));
  assert.deepEqual(consumes, [null]);
  assert.deepEqual(bridge.inspect(), { installed: true, pendingCount: 0 });

  bridge.dispose();
  api.dispatchEvent(executedEvent({
    prompt_id: "prompt-after-dispose",
    node: "backend-node",
    output: {},
  }));
  assert.deepEqual(consumes, [null, null]);
  assert.deepEqual(bridge.inspect(), { installed: false, pendingCount: 0 });
}

console.log("Executed event context contract smoke passed.");
