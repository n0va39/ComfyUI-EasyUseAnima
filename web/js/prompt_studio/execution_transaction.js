// @ts-check

const WIDGET_CALLBACK_OWNER = Symbol.for(
  "easyuse-anima.prompt-studio.wildcard-seed-callback-owner",
);
const MAX_TRACKED_TRANSACTIONS_PER_NODE = 8;

/** @param {unknown} value */
function isReference(value) {
  return value !== null && (
    typeof value === "object"
    || typeof value === "function"
  );
}

/** @param {unknown} value */
function normalizeSurface(value) {
  return typeof value === "string" && value.trim() !== ""
    ? value.trim()
    : null;
}

/**
 * @param {unknown} value
 * @returns {Array<{
 *   surface: string,
 *   commit: (context: { transaction: any, envelope: any }) => unknown,
 * }> | null}
 */
function normalizeCommitters(value) {
  if (value == null) {
    return [];
  }
  if (!Array.isArray(value)) {
    return null;
  }
  const surfaces = new Set();
  const committers = [];
  for (const candidate of value) {
    const surface = normalizeSurface(candidate?.surface);
    if (
      surface == null
      || surfaces.has(surface)
      || typeof candidate?.commit !== "function"
    ) {
      return null;
    }
    surfaces.add(surface);
    committers.push({ surface, commit: candidate.commit });
  }
  return committers;
}

/**
 * Bind Prompt Studio feature-owned surfaces to the shared queue UI transaction
 * and executed-envelope contracts. Surface strings, edit bindings, and commit
 * callbacks remain opaque; this lifecycle does not parse feature payloads.
 *
 * @param {{
 *   owner: ReturnType<import("../lifecycle/queue_ui_transaction.js").createQueueUiTransactionOwner>,
 *   executedContext: ReturnType<import("../lifecycle/executed_event_context.js").createExecutedEventContext>,
 *   findWidget?: ((node: any, name: string) => any) | null,
 *   editBindings?: Array<{ widgetNames: string[], surfaces: string[] }>,
 * }} options
 */
function createPromptStudioExecutionTransaction(options) {
  const {
    owner,
    executedContext,
    findWidget = null,
    editBindings = [],
  } = options || {};
  if (
    !owner
    || !executedContext
    || !Array.isArray(editBindings)
    || (editBindings.length > 0 && typeof findWidget !== "function")
  ) {
    throw new TypeError("Prompt Studio execution transaction dependencies are required.");
  }

  let disposed = false;
  const transactionsByNode = new WeakMap();
  const pendingExecutions = new WeakMap();
  const activeNodes = new Set();

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
      owner.cancel(active.shift(), "cancel");
    }
    active.push(transaction);
    transactionsByNode.set(node, active);
    activeNodes.add(node);
  }

  /** @param {any} node @param {any} transaction */
  function forget(node, transaction) {
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

  /** @param {any} node @param {unknown} surfaces */
  function markEdited(node, surfaces) {
    return !disposed && owner.markEdited(node, surfaces);
  }

  /** @param {any} node */
  function hookNode(node) {
    if (disposed || !isReference(node)) {
      return false;
    }
    let changed = false;
    for (const binding of editBindings) {
      if (
        !Array.isArray(binding?.widgetNames)
        || !Array.isArray(binding?.surfaces)
      ) {
        continue;
      }
      for (const name of binding.widgetNames) {
        const widget = findWidget?.(node, name);
        if (!widget || typeof widget !== "object") {
          continue;
        }
        const current = widget.callback;
        const callbackState = current?.[WIDGET_CALLBACK_OWNER];
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
            markEdited(node, binding.surfaces);
          }
        };
        Object.defineProperty(wrapped, WIDGET_CALLBACK_OWNER, {
          value: { runtime, original },
        });
        widget.callback = wrapped;
        changed = true;
      }
    }
    return changed;
  }

  /** @param {Array<{ node: any, surfaces: string[] }>} entries */
  function captureQueue(entries) {
    if (disposed || !Array.isArray(entries)) {
      return [];
    }
    const captured = [];
    for (const entry of entries) {
      const node = entry?.node;
      if (!isReference(node)) {
        continue;
      }
      hookNode(node);
      const transaction = owner.captureProvisional({
        node,
        surfaces: entry.surfaces,
      });
      if (transaction) {
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
      if (
        !disposed
        && owner.acceptPrompt(entry.transaction, promptId)
      ) {
        accepted += 1;
        const pending = pendingExecutions.get(entry.transaction);
        if (pending) {
          pendingExecutions.delete(entry.transaction);
          finishExecution(entry.node, entry.transaction, pending);
        }
      } else {
        pendingExecutions.delete(entry.transaction);
        owner.cancel(entry.transaction, "reject");
        forget(entry.node, entry.transaction);
      }
    }
    return accepted;
  }

  /**
   * @param {any} node
   * @param {any} transaction
   * @param {{
   *   envelope: any,
   *   mappedItemCount: number,
   *   committers: Array<{
   *     surface: string,
   *     commit: (context: { transaction: any, envelope: any }) => unknown,
   *   }> | null,
   * }} pending
   */
  function finishExecution(node, transaction, pending) {
    if (transaction.promptId !== pending.envelope.promptId) {
      owner.cancel(transaction, "reject");
      forget(node, transaction);
      return false;
    }
    let committed = false;
    for (const committer of pending.committers || []) {
      const canCommit = owner.canCommit(transaction, {
        envelope: pending.envelope,
        node,
        surface: committer.surface,
        mappedItemCount: pending.mappedItemCount,
      });
      if (!canCommit) {
        continue;
      }
      try {
        const result = committer.commit({ transaction, envelope: pending.envelope });
        committed = result !== false || committed;
      } catch {
        // One feature commit failure must not block independent surfaces.
      }
    }
    owner.settle(transaction, pending.envelope);
    forget(node, transaction);
    return committed;
  }

  /**
   * Consume only the exact output object captured from ComfyUI's outer
   * `executed` event, fan out feature-owned callbacks, then settle once.
   *
   * @param {any} node
   * @param {unknown} output
   * @param {number} mappedItemCount
   * @param {Array<{
   *   surface: string,
   *   commit: (context: { transaction: any, envelope: any }) => unknown,
   * }> | null} [committers]
   */
  async function consumeExecution(
    node,
    output,
    mappedItemCount,
    committers = [],
  ) {
    if (disposed || !isReference(node)) {
      return false;
    }
    const envelope = await executedContext.consumeWithinTurn(output);
    if (!envelope || disposed || !isReference(node)) {
      return false;
    }
    const normalizedCommitters = normalizeCommitters(committers);
    const active = activeTransactions(node);
    const matches = active.filter(
      (transaction) => transaction.state === "accepted"
        && transaction.promptId === envelope.promptId,
    );
    if (matches.length === 1) {
      return finishExecution(node, matches[0], {
        envelope,
        mappedItemCount,
        committers: normalizedCommitters,
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
      committers: normalizedCommitters,
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
    }
    const changed = owner.disposeNode(node, reason);
    transactionsByNode.delete(node);
    activeNodes.delete(node);
    return changed;
  }

  function clear() {
    let cancelled = 0;
    for (const node of [...activeNodes]) {
      for (const transaction of activeTransactions(node)) {
        pendingExecutions.delete(transaction);
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
    markEdited,
  });
  return runtime;
}

export {
  createPromptStudioExecutionTransaction,
};
