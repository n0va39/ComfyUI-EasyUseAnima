// @ts-check

const AIO_SEED_SELECTION_SURFACE = "aio.seed_selection";
const AIO_SEED_WIDGET_NAMES = Object.freeze(["seed", "generation_settings"]);
const AIO_SEED_CONTROLS = new Set([
  "fixed",
  "randomize",
  "increment",
  "decrement",
]);
const SPECIAL_SELECTION_BY_TOKEN = new Map([
  [-1, "randomize"],
  [-2, "increment"],
  [-3, "decrement"],
]);
const AIO_PAYLOAD_FIELDS = Object.freeze([
  "requested_seed",
  "selection",
  "effective_after_generate",
  "execution_seed",
  "next_seed",
]);
const AIO_SEED_CALLBACK_OWNER = Symbol.for(
  "easyuse-anima.aio.seed-transaction-callback-owner",
);
const MAX_TRACKED_TRANSACTIONS_PER_NODE = 8;

/** @param {unknown} value */
function isReference(value) {
  return value !== null && (
    typeof value === "object"
    || typeof value === "function"
  );
}

/** @param {unknown} value @returns {value is Record<string, unknown>} */
function isRecord(value) {
  return value !== null && typeof value === "object";
}

/** @param {unknown} value @param {number} maximum */
function editableSeed(value, maximum) {
  if (typeof value !== "string" || !/^(?:0|[1-9]\d*)$/.test(value)) {
    return null;
  }
  try {
    const parsed = BigInt(value);
    if (parsed > BigInt(maximum)) {
      return null;
    }
    return Number(parsed);
  } catch {
    return null;
  }
}

/** @param {unknown} value @param {number} maximum */
function requestedSeed(value, maximum) {
  if (typeof value !== "string") {
    return null;
  }
  if (/^-[123]$/.test(value)) {
    return Number(value);
  }
  return editableSeed(value, maximum);
}

/** @param {unknown} value @param {number} maximum */
function normalizeSelectionSnapshot(value, maximum) {
  if (!isRecord(value)) {
    return null;
  }
  const seed = Number(value?.requestedSeed);
  const storedAfterGenerate = String(value?.storedAfterGenerate || "");
  if (
    !Number.isSafeInteger(seed)
    || seed < -3
    || seed > maximum
    || !AIO_SEED_CONTROLS.has(storedAfterGenerate)
  ) {
    return null;
  }
  return { requestedSeed: seed, storedAfterGenerate };
}

/** @param {any} left @param {any} right */
function sameSelection(left, right) {
  return Boolean(
    left
    && right
    && left.requestedSeed === right.requestedSeed
    && left.storedAfterGenerate === right.storedAfterGenerate,
  );
}

/** @param {unknown} message @param {number} maximum */
function parsePayload(message, maximum) {
  const items = isRecord(message) && Array.isArray(message.easyuse_anima_aio_seed)
    ? message.easyuse_anima_aio_seed
    : null;
  if (items?.length !== 1) {
    return null;
  }
  const payload = items[0];
  if (
    !payload
    || typeof payload !== "object"
    || Object.keys(payload).length !== AIO_PAYLOAD_FIELDS.length
    || !AIO_PAYLOAD_FIELDS.every((field) => Object.hasOwn(payload, field))
  ) {
    return null;
  }
  const normalizedRequestedSeed = requestedSeed(payload.requested_seed, maximum);
  const executionSeed = editableSeed(payload.execution_seed, maximum);
  const nextSeed = editableSeed(payload.next_seed, maximum);
  if (
    normalizedRequestedSeed == null
    || executionSeed == null
    || nextSeed == null
  ) {
    return null;
  }
  const selection = SPECIAL_SELECTION_BY_TOKEN.get(normalizedRequestedSeed)
    || "concrete";
  const effectiveAfterGenerate = String(payload.effective_after_generate || "");
  if (
    payload.selection !== selection
    || !AIO_SEED_CONTROLS.has(effectiveAfterGenerate)
    || (
      selection !== "concrete"
      && (
        effectiveAfterGenerate !== "fixed"
        || nextSeed !== executionSeed
      )
    )
  ) {
    return null;
  }
  return {
    requestedSeed: normalizedRequestedSeed,
    selection,
    effectiveAfterGenerate,
    executionSeed,
    nextSeed,
  };
}

/**
 * Bind AiO seed publication to the shared queue transaction and exact executed
 * envelope owners. The shared owners receive only an opaque surface token;
 * this feature adapter owns every seed field and editable mutation.
 *
 * @param {{
 *   owner: ReturnType<import("../lifecycle/queue_ui_transaction.js").createQueueUiTransactionOwner>,
 *   executedContext: ReturnType<import("../lifecycle/executed_event_context.js").createExecutedEventContext>,
 *   maximum: number,
 *   findWidget: (node: any, name: string) => any,
 *   readSelection: (node: any) => unknown,
 *   publishLastSeed: (node: any, seed: number) => unknown,
 *   publishConcreteNextSeed: (node: any, seed: number) => unknown,
 * }} options
 */
export function createAioSeedTransaction(options) {
  const {
    owner,
    executedContext,
    maximum,
    findWidget,
    readSelection,
    publishLastSeed,
    publishConcreteNextSeed,
  } = options || {};
  if (
    !owner
    || !executedContext
    || !Number.isSafeInteger(maximum)
    || maximum < 0
    || typeof findWidget !== "function"
    || typeof readSelection !== "function"
    || typeof publishLastSeed !== "function"
    || typeof publishConcreteNextSeed !== "function"
  ) {
    throw new TypeError("AiO seed transaction dependencies are required.");
  }

  let disposed = false;
  const transactionsByNode = new WeakMap();
  const snapshotsByTransaction = new WeakMap();
  const pendingExecutions = new WeakMap();
  const observedSelections = new WeakMap();
  const lastSequenceByNode = new WeakMap();
  const suppressedNodes = new WeakSet();
  const activeNodes = new Set();

  /** @param {any} node */
  function currentSelection(node) {
    return normalizeSelectionSnapshot(readSelection(node), maximum);
  }

  /** @param {any} node */
  function observeSelection(node) {
    const previousKnown = observedSelections.has(node);
    const previous = observedSelections.get(node) || null;
    const current = currentSelection(node);
    if (current) {
      observedSelections.set(node, current);
    } else {
      observedSelections.delete(node);
    }
    if (
      previousKnown
      && !suppressedNodes.has(node)
      && !sameSelection(previous, current)
    ) {
      return owner.markEdited(node, [AIO_SEED_SELECTION_SURFACE]);
    }
    return false;
  }

  /** @param {any} node @param {() => unknown} callback */
  function withoutRevision(node, callback) {
    suppressedNodes.add(node);
    try {
      return callback();
    } finally {
      observeSelection(node);
      suppressedNodes.delete(node);
    }
  }

  /** @param {any} node */
  function activeTransactions(node) {
    const current = transactionsByNode.get(node) || [];
    const active = current.filter(
      (transaction) => transaction?.state === "provisional"
        || transaction?.state === "accepted",
    );
    if (active.length === 0) {
      transactionsByNode.delete(node);
      activeNodes.delete(node);
    } else if (active.length !== current.length) {
      transactionsByNode.set(node, active);
    }
    return active;
  }

  /** @param {any} node @param {any} transaction */
  function remember(node, transaction) {
    const active = activeTransactions(node);
    while (active.length >= MAX_TRACKED_TRANSACTIONS_PER_NODE) {
      const expired = active.shift();
      pendingExecutions.delete(expired);
      snapshotsByTransaction.delete(expired);
      owner.cancel(expired, "cancel");
    }
    active.push(transaction);
    transactionsByNode.set(node, active);
    activeNodes.add(node);
  }

  /** @param {any} node @param {any} transaction */
  function forget(node, transaction) {
    pendingExecutions.delete(transaction);
    snapshotsByTransaction.delete(transaction);
    const active = activeTransactions(node).filter(
      (candidate) => candidate !== transaction,
    );
    if (active.length === 0) {
      transactionsByNode.delete(node);
      activeNodes.delete(node);
    } else {
      transactionsByNode.set(node, active);
    }
  }

  /** @param {any} node */
  function hookNode(node) {
    if (disposed || !isReference(node)) {
      return false;
    }
    observeSelection(node);
    let changed = false;
    for (const name of AIO_SEED_WIDGET_NAMES) {
      const widget = findWidget(node, name);
      if (!widget || typeof widget !== "object") {
        continue;
      }
      const current = widget.callback;
      const callbackState = current?.[AIO_SEED_CALLBACK_OWNER];
      if (callbackState?.runtime === runtime) {
        continue;
      }
      const original = callbackState?.original ?? current;
      const wrapped = function (...args) {
        try {
          return typeof original === "function"
            ? original.apply(this, args)
            : undefined;
        } finally {
          if (!disposed) {
            observeSelection(node);
          }
        }
      };
      Object.defineProperty(wrapped, AIO_SEED_CALLBACK_OWNER, {
        value: { runtime, original },
      });
      widget.callback = wrapped;
      changed = true;
    }
    return changed;
  }

  /** @param {any[]} nodes */
  function captureQueue(nodes) {
    if (disposed || !Array.isArray(nodes)) {
      return [];
    }
    const captured = [];
    for (const node of nodes) {
      if (!isReference(node)) {
        continue;
      }
      hookNode(node);
      const snapshot = currentSelection(node);
      if (!snapshot) {
        continue;
      }
      const transaction = owner.captureProvisional({
        node,
        surfaces: [AIO_SEED_SELECTION_SURFACE],
      });
      if (transaction) {
        snapshotsByTransaction.set(transaction, snapshot);
        remember(node, transaction);
        captured.push({ node, transaction });
      }
    }
    return captured;
  }

  /**
   * @param {{ node: any, transaction: any }[]} captured
   * @param {{ ok?: boolean, result?: any }} outcome
   */
  function acceptQueue(captured, outcome = {}) {
    if (!Array.isArray(captured)) {
      return 0;
    }
    const promptId = outcome.ok === true ? outcome.result?.prompt_id : null;
    let accepted = 0;
    for (const entry of captured) {
      if (!disposed && owner.acceptPrompt(entry.transaction, promptId)) {
        accepted += 1;
        const pending = pendingExecutions.get(entry.transaction);
        if (pending) {
          pendingExecutions.delete(entry.transaction);
          finishExecution(entry.node, entry.transaction, pending);
        }
      } else {
        owner.cancel(entry.transaction, "reject");
        forget(entry.node, entry.transaction);
      }
    }
    return accepted;
  }

  /** @param {any} node @param {any} transaction @param {any} pending */
  function finishExecution(node, transaction, pending) {
    if (transaction.promptId !== pending.envelope.promptId) {
      owner.cancel(transaction, "reject");
      forget(node, transaction);
      return false;
    }
    const snapshot = snapshotsByTransaction.get(transaction) || null;
    const payload = pending.mappedItemCount === 1
      ? parsePayload(pending.envelope.output, maximum)
      : null;
    const matchesSnapshot = Boolean(
      snapshot
      && payload
      && payload.requestedSeed === snapshot.requestedSeed
      && payload.selection === (
        SPECIAL_SELECTION_BY_TOKEN.get(snapshot.requestedSeed) || "concrete"
      )
      && (
        payload.selection !== "concrete"
        || payload.effectiveAfterGenerate === snapshot.storedAfterGenerate
      ),
    );
    let lastPublished = false;
    let editablePublished = false;
    if (matchesSnapshot) {
      const lastSequence = lastSequenceByNode.get(node) || 0;
      if (transaction.localSequence > lastSequence) {
        try {
          lastPublished = publishLastSeed(node, payload.executionSeed) !== false;
          if (lastPublished) {
            lastSequenceByNode.set(node, transaction.localSequence);
          }
        } catch {
          lastPublished = false;
        }
      }
      if (
        payload.selection === "concrete"
        && owner.canCommit(transaction, {
          envelope: pending.envelope,
          node,
          surface: AIO_SEED_SELECTION_SURFACE,
          mappedItemCount: pending.mappedItemCount,
        })
      ) {
        try {
          editablePublished = withoutRevision(
            node,
            () => publishConcreteNextSeed(node, payload.nextSeed),
          ) !== false;
        } catch {
          editablePublished = false;
        }
      }
    }
    owner.settle(transaction, pending.envelope);
    forget(node, transaction);
    return lastPublished || editablePublished;
  }

  /** @param {any} node @param {unknown} output */
  async function consumeExecution(node, output) {
    if (disposed || !isReference(node)) {
      return false;
    }
    const envelope = await executedContext.consumeWithinTurn(output);
    if (!envelope || disposed || !isReference(node)) {
      return false;
    }
    const active = activeTransactions(node);
    const matches = active.filter(
      (transaction) => transaction.state === "accepted"
        && transaction.promptId === envelope.promptId,
    );
    const mappedItemCount = isRecord(output) && Array.isArray(output.easyuse_anima_aio_seed)
      ? output.easyuse_anima_aio_seed.length
      : 0;
    if (matches.length === 1) {
      return finishExecution(node, matches[0], {
        envelope,
        mappedItemCount,
      });
    }
    const provisional = active.filter(
      (transaction) => transaction.state === "provisional",
    );
    if (matches.length !== 0 || provisional.length !== 1) {
      return false;
    }
    pendingExecutions.set(provisional[0], {
      envelope,
      mappedItemCount,
    });
    return false;
  }

  /** @param {unknown} promptId */
  function finishPrompt(promptId) {
    const finished = owner.finishPrompt(promptId);
    for (const node of [...activeNodes]) {
      activeTransactions(node);
    }
    return finished;
  }

  /** @param {any} node @param {"remove" | "reconfigure" | "dispose"} [reason] */
  function disposeNode(node, reason = "dispose") {
    for (const transaction of activeTransactions(node)) {
      pendingExecutions.delete(transaction);
      snapshotsByTransaction.delete(transaction);
    }
    const changed = owner.disposeNode(node, reason);
    transactionsByNode.delete(node);
    observedSelections.delete(node);
    lastSequenceByNode.delete(node);
    activeNodes.delete(node);
    return changed;
  }

  function clear() {
    let cancelled = 0;
    for (const node of [...activeNodes]) {
      for (const transaction of activeTransactions(node)) {
        pendingExecutions.delete(transaction);
        snapshotsByTransaction.delete(transaction);
        if (owner.cancel(transaction, "clear")) {
          cancelled += 1;
        }
      }
      transactionsByNode.delete(node);
      activeNodes.delete(node);
    }
    return cancelled;
  }

  function dispose() {
    if (disposed) {
      return false;
    }
    clear();
    disposed = true;
    return true;
  }

  const runtime = Object.freeze({
    acceptQueue,
    captureQueue,
    clear,
    consumeExecution,
    dispose,
    disposeNode,
    finishPrompt,
    hookNode,
  });
  return runtime;
}

export { AIO_SEED_SELECTION_SURFACE };
