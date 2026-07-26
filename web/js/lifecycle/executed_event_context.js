// @ts-check

const DEFAULT_MAX_PENDING_OUTPUTS = 32;
const TERMINAL_EVENT_TYPES = Object.freeze([
  "execution_success",
  "execution_error",
  "execution_interrupted",
]);

/** @param {unknown} value @returns {value is object} */
function isReference(value) {
  return value !== null && (
    typeof value === "object"
    || typeof value === "function"
  );
}

/** @param {unknown} value */
function normalizeId(value) {
  if (typeof value === "string" && value.trim() !== "") {
    return value.trim();
  }
  if (typeof value === "number" && Number.isInteger(value)) {
    return String(value);
  }
  return null;
}

/** @param {any} detail */
function envelopeFromDetail(detail) {
  const promptId = normalizeId(detail?.prompt_id);
  const executionNodeId = normalizeId(detail?.node);
  const displayNodeId = detail?.display_node == null
    ? null
    : normalizeId(detail.display_node);
  const output = detail?.output;
  if (
    promptId == null
    || executionNodeId == null
    || (detail?.display_node != null && displayNodeId == null)
    || !isReference(output)
  ) {
    return null;
  }
  return Object.freeze({
    promptId,
    executionNodeId,
    displayNodeId,
    output,
  });
}

/** @param {unknown} value @returns {number} */
function positiveInteger(value) {
  if (typeof value !== "number" || !Number.isInteger(value) || value <= 0) {
    throw new TypeError("maxPendingOutputs must be a positive integer.");
  }
  return value;
}

/**
 * Preserve the outer ComfyUI executed envelope until the exact output object is
 * consumed by a node adapter. When the node adapter runs before this listener,
 * one pending consumer may wait for the remainder of the current event turn.
 * This owner does not inspect feature payloads or register feature callbacks.
 *
 * @param {{
 *   addEventListener: Function,
 *   removeEventListener: Function,
 * }} api
 * @param {{
 *   maxPendingOutputs?: number,
 *   finishPrompt?: ((promptId: string) => unknown) | null,
 *   scheduleMicrotask?: ((callback: () => void) => unknown) | null,
 * }} [options]
 */
export function createExecutedEventContext(api, options = {}) {
  if (
    !api
    || typeof api.addEventListener !== "function"
    || typeof api.removeEventListener !== "function"
  ) {
    throw new TypeError("An EventTarget-compatible Comfy API is required.");
  }
  const maxPendingOutputs = positiveInteger(
    options.maxPendingOutputs ?? DEFAULT_MAX_PENDING_OUTPUTS,
  );
  const finishPrompt = options.finishPrompt ?? null;
  if (finishPrompt != null && typeof finishPrompt !== "function") {
    throw new TypeError("finishPrompt must be a function when provided.");
  }
  const scheduleMicrotask = options.scheduleMicrotask ?? globalThis.queueMicrotask;
  if (typeof scheduleMicrotask !== "function") {
    throw new TypeError("scheduleMicrotask must be a function when provided.");
  }

  let installed = false;
  let envelopesByOutput = new WeakMap();
  let consumersByOutput = new WeakMap();
  /** @type {object[]} */
  const pendingOutputs = [];
  /** @type {object[]} */
  const pendingConsumerOutputs = [];

  /** @param {object} output */
  function removePending(output) {
    const index = pendingOutputs.indexOf(output);
    if (index >= 0) {
      pendingOutputs.splice(index, 1);
    }
  }

  /** @param {object} output */
  function removePendingConsumer(output) {
    const index = pendingConsumerOutputs.indexOf(output);
    if (index >= 0) {
      pendingConsumerOutputs.splice(index, 1);
    }
  }

  /** @param {object} output @param {any} expected */
  function expireConsumer(output, expected) {
    if (consumersByOutput.get(output) !== expected) {
      return false;
    }
    consumersByOutput.delete(output);
    removePendingConsumer(output);
    expected.resolve(null);
    return true;
  }

  /** @param {string} promptId */
  function releasePromptOutputs(promptId) {
    for (let index = pendingOutputs.length - 1; index >= 0; index -= 1) {
      const output = pendingOutputs[index];
      const envelope = envelopesByOutput.get(output);
      if (envelope?.promptId === promptId) {
        pendingOutputs.splice(index, 1);
        envelopesByOutput.delete(output);
      }
    }
  }

  /** @param {{ detail?: any }} event */
  function captureExecuted({ detail }) {
    const envelope = envelopeFromDetail(detail);
    if (!envelope) {
      return;
    }
    const consumer = consumersByOutput.get(envelope.output);
    if (consumer) {
      consumersByOutput.delete(envelope.output);
      removePendingConsumer(envelope.output);
      consumer.resolve(envelope);
      return;
    }
    removePending(envelope.output);
    envelopesByOutput.set(envelope.output, envelope);
    pendingOutputs.push(envelope.output);

    while (pendingOutputs.length > maxPendingOutputs) {
      const expiredOutput = pendingOutputs.shift();
      if (expiredOutput) {
        envelopesByOutput.delete(expiredOutput);
      }
    }
  }

  /** @param {{ detail?: any }} event */
  function handlePromptTerminal({ detail }) {
    const promptId = normalizeId(detail?.prompt_id);
    if (promptId == null) {
      return;
    }
    releasePromptOutputs(promptId);
    finishPrompt?.(promptId);
  }

  function install() {
    if (installed) {
      return false;
    }
    api.addEventListener("executed", captureExecuted, { capture: true });
    for (const eventType of TERMINAL_EVENT_TYPES) {
      api.addEventListener(eventType, handlePromptTerminal);
    }
    installed = true;
    return true;
  }

  /** @param {unknown} output */
  function peek(output) {
    return isReference(output)
      ? envelopesByOutput.get(output) || null
      : null;
  }

  /** @param {unknown} output */
  function consume(output) {
    if (!isReference(output)) {
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

  /**
   * Consume an already-captured envelope or wait for a later listener in the
   * current event turn to capture the exact same output object. An unmatched
   * consumer expires after one injected microtask and duplicate consumers fail
   * closed.
   *
   * @param {unknown} output
   * @returns {Promise<any | null>}
   */
  function consumeWithinTurn(output) {
    if (!isReference(output)) {
      return Promise.resolve(null);
    }
    const envelope = consume(output);
    if (envelope) {
      return Promise.resolve(envelope);
    }
    if (consumersByOutput.has(output)) {
      return Promise.resolve(null);
    }

    let resolveConsumer;
    const promise = new Promise((resolve) => {
      resolveConsumer = resolve;
    });
    const consumer = { resolve: resolveConsumer };
    consumersByOutput.set(output, consumer);
    pendingConsumerOutputs.push(output);

    while (pendingConsumerOutputs.length > maxPendingOutputs) {
      const expiredOutput = pendingConsumerOutputs[0];
      const expiredConsumer = consumersByOutput.get(expiredOutput);
      if (!expiredConsumer) {
        pendingConsumerOutputs.shift();
        continue;
      }
      expireConsumer(expiredOutput, expiredConsumer);
    }

    scheduleMicrotask(() => expireConsumer(output, consumer));
    return promise;
  }

  function releaseConsumers() {
    for (const output of [...pendingConsumerOutputs]) {
      const consumer = consumersByOutput.get(output);
      if (consumer) {
        expireConsumer(output, consumer);
      }
    }
    consumersByOutput = new WeakMap();
    pendingConsumerOutputs.length = 0;
  }

  function dispose() {
    if (!installed) {
      return false;
    }
    api.removeEventListener("executed", captureExecuted, { capture: true });
    for (const eventType of TERMINAL_EVENT_TYPES) {
      api.removeEventListener(eventType, handlePromptTerminal);
    }
    installed = false;
    envelopesByOutput = new WeakMap();
    pendingOutputs.length = 0;
    releaseConsumers();
    return true;
  }

  return Object.freeze({
    install,
    peek,
    consume,
    consumeWithinTurn,
    dispose,
  });
}
