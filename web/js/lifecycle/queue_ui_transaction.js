// @ts-check

const DEFAULT_MAX_TRANSACTIONS_PER_NODE = 8;
const DEFAULT_MAX_TRANSACTIONS_PER_PROMPT = 128;
const ACTIVE_STATES = new Set(["provisional", "accepted"]);
const CANCELLATION_REASONS = new Set([
  "cancel",
  "reject",
  "clear",
  "remove",
  "reconfigure",
  "dispose",
]);

/** @param {unknown} value @returns {value is object} */
function isReference(value) {
  return value !== null && (
    typeof value === "object"
    || typeof value === "function"
  );
}

/** @param {unknown} value */
function normalizePromptId(value) {
  return typeof value === "string" && value.trim() !== ""
    ? value.trim()
    : null;
}

/** @param {unknown} value */
function normalizeNodeId(value) {
  if (typeof value === "string" && value.trim() !== "") {
    return value.trim();
  }
  if (typeof value === "number" && Number.isInteger(value)) {
    return String(value);
  }
  return null;
}

/** @param {unknown} value */
function normalizeSurface(value) {
  return typeof value === "string" && value.trim() !== ""
    ? value.trim()
    : null;
}

/** @param {unknown} surfaces @returns {string[] | null} */
function normalizeSurfaces(surfaces) {
  if (!Array.isArray(surfaces) || surfaces.length === 0) {
    return null;
  }
  /** @type {string[]} */
  const normalized = [];
  for (const surface of surfaces) {
    const token = normalizeSurface(surface);
    if (token == null) {
      return null;
    }
    normalized.push(token);
  }
  return [...new Set(normalized)];
}

/** @param {any} envelope */
function normalizeEnvelope(envelope) {
  if (!envelope || typeof envelope !== "object") {
    return null;
  }
  const promptId = normalizePromptId(envelope.promptId);
  const executionNodeId = normalizeNodeId(envelope.executionNodeId);
  const displayNodeId = envelope.displayNodeId == null
    ? null
    : normalizeNodeId(envelope.displayNodeId);
  const output = envelope.output;
  if (
    promptId == null
    || executionNodeId == null
    || (envelope.displayNodeId != null && displayNodeId == null)
    || !isReference(output)
  ) {
    return null;
  }
  return { promptId, executionNodeId, displayNodeId, output };
}

/** @param {unknown} value @param {string} name @returns {number} */
function positiveInteger(value, name) {
  if (typeof value !== "number" || !Number.isInteger(value) || value <= 0) {
    throw new TypeError(`${name} must be a positive integer.`);
  }
  return value;
}

/**
 * Create one seed- and feature-agnostic queue UI transaction owner.
 *
 * Surface strings are opaque to this module. Callers retain ownership of field
 * catalogs, payload parsing, editable mutations, and every feature-specific
 * interpretation of a surface.
 *
 * @param {{
 *   maxTransactionsPerNode?: number,
 *   maxTransactionsPerPrompt?: number,
 * }} [options]
 */
export function createQueueUiTransactionOwner(options = {}) {
  const maxTransactionsPerNode = positiveInteger(
    options.maxTransactionsPerNode ?? DEFAULT_MAX_TRANSACTIONS_PER_NODE,
    "maxTransactionsPerNode",
  );
  const maxTransactionsPerPrompt = positiveInteger(
    options.maxTransactionsPerPrompt ?? DEFAULT_MAX_TRANSACTIONS_PER_PROMPT,
    "maxTransactionsPerPrompt",
  );

  let sequence = 0;
  const records = new Map();
  const transactionIds = new WeakMap();
  const nodeEpochs = new WeakMap();
  const nodeStates = new WeakMap();
  const transactionsByPrompt = new Map();

  /** @param {object | Function} node */
  function stateForNode(node) {
    let state = nodeStates.get(node);
    if (!state) {
      const epoch = (nodeEpochs.get(node) || 0) + 1;
      nodeEpochs.set(node, epoch);
      state = {
        epoch,
        revisions: new Map(),
        latestBySurface: new Map(),
        transactionIds: [],
      };
      nodeStates.set(node, state);
    }
    return state;
  }

  /** @param {any} state @param {string} surface */
  function revisionFor(state, surface) {
    return state.revisions.get(surface) || 0;
  }

  /** @param {unknown} transaction */
  function recordFor(transaction) {
    if (!isReference(transaction)) {
      return null;
    }
    const id = transactionIds.get(transaction);
    const record = id == null ? null : records.get(id);
    return record?.token === transaction ? record : null;
  }

  /** @param {any} record */
  function isTracked(record) {
    return Boolean(
      record
      && records.get(record.id) === record
      && ACTIVE_STATES.has(record.publicState.state),
    );
  }

  /** @param {any} record */
  function releasePromptReference(record) {
    if (record.promptId == null) {
      return;
    }
    const promptTransactions = transactionsByPrompt.get(record.promptId);
    promptTransactions?.delete(record.id);
    if (promptTransactions?.size === 0) {
      transactionsByPrompt.delete(record.promptId);
    }
  }

  /** @param {any} record */
  function releaseTransaction(record) {
    records.delete(record.id);
    releasePromptReference(record);

    const node = record.node;
    const state = nodeStates.get(node);
    if (state?.epoch === record.nodeEpoch) {
      state.transactionIds = state.transactionIds.filter(
        (transactionId) => transactionId !== record.id,
      );
      for (const surface of record.surfaces) {
        if (state.latestBySurface.get(surface) === record.id) {
          state.latestBySurface.delete(surface);
        }
      }
    }
    record.node = null;
  }

  /** @param {any} record @param {string} state @param {string} reason */
  function terminate(record, state, reason) {
    if (!isTracked(record)) {
      return false;
    }
    record.publicState.state = state;
    record.publicState.reason = reason;
    releaseTransaction(record);
    return true;
  }

  /** @param {any} state */
  function enforceNodeRetention(state) {
    while (state.transactionIds.length > maxTransactionsPerNode) {
      const oldestId = state.transactionIds[0];
      const oldest = records.get(oldestId);
      if (!oldest) {
        state.transactionIds.shift();
        continue;
      }
      terminate(oldest, "cancelled", "retention");
    }
  }

  /** @param {string} promptId */
  function enforcePromptRetention(promptId) {
    const promptTransactions = transactionsByPrompt.get(promptId);
    while (promptTransactions?.size > maxTransactionsPerPrompt) {
      const oldestId = promptTransactions.values().next().value;
      const oldest = records.get(oldestId);
      if (!oldest) {
        promptTransactions.delete(oldestId);
        continue;
      }
      terminate(oldest, "cancelled", "retention");
    }
  }

  /** @param {any} record */
  function createToken(record) {
    const { id, localSequence, nodeEpoch, publicState } = record;
    const token = {};
    Object.defineProperties(token, {
      id: { enumerable: true, value: id },
      localSequence: { enumerable: true, value: localSequence },
      nodeEpoch: { enumerable: true, value: nodeEpoch },
      promptId: {
        enumerable: true,
        get: () => publicState.promptId,
      },
      state: {
        enumerable: true,
        get: () => publicState.state,
      },
      reason: {
        enumerable: true,
        get: () => publicState.reason,
      },
    });
    return Object.freeze(token);
  }

  /** @param {{ node?: unknown, surfaces?: unknown }} [request] */
  function captureProvisional({ node, surfaces } = {}) {
    const normalizedSurfaces = normalizeSurfaces(surfaces);
    if (!isReference(node) || normalizedSurfaces == null) {
      return null;
    }

    const state = stateForNode(node);
    const id = `qstate-${++sequence}`;
    /** @type {any} */
    const record = {
      id,
      localSequence: sequence,
      node,
      nodeEpoch: state.epoch,
      promptId: null,
      surfaces: normalizedSurfaces,
      revisions: new Map(),
      publicState: {
        promptId: null,
        state: "provisional",
        reason: null,
      },
      token: null,
    };
    record.token = createToken(record);

    for (const surface of normalizedSurfaces) {
      record.revisions.set(surface, revisionFor(state, surface));
      state.latestBySurface.set(surface, id);
    }
    records.set(id, record);
    transactionIds.set(record.token, id);
    state.transactionIds.push(id);
    enforceNodeRetention(state);
    return record.token;
  }

  /** @param {unknown} transaction @param {unknown} promptId */
  function acceptPrompt(transaction, promptId) {
    const record = recordFor(transaction);
    const normalized = normalizePromptId(promptId);
    if (
      !isTracked(record)
      || record.publicState.state !== "provisional"
      || normalized == null
    ) {
      return false;
    }

    const promptTransactions = transactionsByPrompt.get(normalized) || new Set();
    const ambiguousNodePrompt = [...promptTransactions].some(
      (transactionId) => records.get(transactionId)?.node === record.node,
    );
    if (ambiguousNodePrompt) {
      terminate(record, "cancelled", "ambiguous-prompt");
      return false;
    }

    record.promptId = normalized;
    record.publicState.promptId = normalized;
    record.publicState.state = "accepted";
    promptTransactions.add(record.id);
    transactionsByPrompt.set(normalized, promptTransactions);
    enforcePromptRetention(normalized);
    return record.publicState.state === "accepted";
  }

  /** @param {unknown} node @param {unknown} surfaces */
  function markEdited(node, surfaces) {
    const normalizedSurfaces = normalizeSurfaces(surfaces);
    const state = isReference(node) ? nodeStates.get(node) : null;
    if (!state || normalizedSurfaces == null) {
      return false;
    }
    for (const surface of normalizedSurfaces) {
      state.revisions.set(surface, revisionFor(state, surface) + 1);
    }
    return true;
  }

  /**
   * @param {unknown} transaction
   * @param {{
   *   envelope?: unknown,
   *   node?: unknown,
   *   surface?: unknown,
   *   mappedItemCount?: number,
   * }} [request]
   */
  function canCommit(transaction, request = {}) {
    const record = recordFor(transaction);
    const envelope = normalizeEnvelope(request.envelope);
    const surface = normalizeSurface(request.surface);
    if (
      !isTracked(record)
      || record.publicState.state !== "accepted"
      || envelope == null
      || record.promptId !== envelope.promptId
      || request.node !== record.node
      || (
        request.mappedItemCount !== undefined
        && request.mappedItemCount !== 1
      )
      || surface == null
    ) {
      return false;
    }

    const state = nodeStates.get(record.node);
    return Boolean(
      state?.epoch === record.nodeEpoch
      && record.revisions.has(surface)
      && state.latestBySurface.get(surface) === record.id
      && revisionFor(state, surface) === record.revisions.get(surface),
    );
  }

  /** @param {unknown} transaction @param {unknown} envelope */
  function settle(transaction, envelope) {
    const record = recordFor(transaction);
    const normalized = normalizeEnvelope(envelope);
    if (
      !isTracked(record)
      || record.publicState.state !== "accepted"
      || normalized == null
      || record.promptId !== normalized.promptId
    ) {
      return false;
    }
    return terminate(record, "settled", "executed");
  }

  /** @param {unknown} transaction @param {string} [reason] */
  function cancel(transaction, reason = "cancel") {
    if (!CANCELLATION_REASONS.has(reason)) {
      return false;
    }
    return terminate(recordFor(transaction), "cancelled", reason);
  }

  /** @param {unknown} promptId */
  function finishPrompt(promptId) {
    const normalized = normalizePromptId(promptId);
    const promptTransactions = normalized == null
      ? null
      : transactionsByPrompt.get(normalized);
    if (!promptTransactions) {
      return 0;
    }
    let finished = 0;
    for (const transactionId of [...promptTransactions]) {
      const record = records.get(transactionId);
      if (record && terminate(record, "finished", "prompt-terminal")) {
        finished += 1;
      }
    }
    return finished;
  }

  /** @param {unknown} node @param {string} [reason] */
  function disposeNode(node, reason = "dispose") {
    if (
      !isReference(node)
      || !["remove", "reconfigure", "dispose"].includes(reason)
    ) {
      return false;
    }
    const state = nodeStates.get(node);
    if (!state) {
      return false;
    }
    for (const transactionId of [...state.transactionIds]) {
      const record = records.get(transactionId);
      if (record) {
        terminate(record, "cancelled", reason);
      }
    }
    state.revisions.clear();
    state.latestBySurface.clear();
    state.transactionIds.length = 0;
    nodeStates.delete(node);
    return true;
  }

  return Object.freeze({
    captureProvisional,
    acceptPrompt,
    markEdited,
    canCommit,
    settle,
    cancel,
    finishPrompt,
    disposeNode,
  });
}
