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
 * synchronously consumed by a node adapter. This owner does not inspect feature
 * payloads or register feature callbacks.
 *
 * @param {{
 *   addEventListener: Function,
 *   removeEventListener: Function,
 * }} api
 * @param {{
 *   maxPendingOutputs?: number,
 *   finishPrompt?: ((promptId: string) => unknown) | null,
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

  let installed = false;
  let envelopesByOutput = new WeakMap();
  /** @type {object[]} */
  const pendingOutputs = [];

  /** @param {object} output */
  function removePending(output) {
    const index = pendingOutputs.indexOf(output);
    if (index >= 0) {
      pendingOutputs.splice(index, 1);
    }
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
    return true;
  }

  return Object.freeze({
    install,
    peek,
    consume,
    dispose,
  });
}
