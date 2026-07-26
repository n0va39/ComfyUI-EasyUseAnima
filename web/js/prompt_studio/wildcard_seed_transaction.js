// @ts-check

const WILDCARD_SEED_CONTROL_SURFACE = "prompt.wildcard_seed_control";
const WILDCARD_HISTORY_SURFACE = "prompt.wildcard_history";
const EDITABLE_WIDGET_NAMES = Object.freeze([
  "wildcard_seed",
  "wildcard_seed_after_generate",
]);
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

/**
 * Bind Prompt Studio's concrete next-seed publication to the shared queue UI
 * transaction contract. Seed values and controls remain feature-owned; the
 * shared owner sees only an opaque surface token and its revision.
 *
 * @param {{
 *   owner: ReturnType<import("../lifecycle/queue_ui_transaction.js").createQueueUiTransactionOwner>,
 *   executedContext: ReturnType<import("../lifecycle/executed_event_context.js").createExecutedEventContext>,
 *   findWidget: (node: any, name: string) => any,
 * }} options
 */
function createPromptStudioWildcardSeedTransaction(options) {
  const { owner, executedContext, findWidget } = options || {};
  if (
    !owner
    || !executedContext
    || typeof findWidget !== "function"
  ) {
    throw new TypeError("Prompt Studio wildcard transaction dependencies are required.");
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

  /** @param {any} node */
  function hookNode(node) {
    if (disposed || !isReference(node)) {
      return false;
    }
    let changed = false;
    for (const name of EDITABLE_WIDGET_NAMES) {
      const widget = findWidget(node, name);
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
          if (!disposed) {
            owner.markEdited(node, [WILDCARD_SEED_CONTROL_SURFACE]);
          }
        }
      };
      Object.defineProperty(wrapped, WIDGET_CALLBACK_OWNER, {
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
      const transaction = owner.captureProvisional({
        node,
        surfaces: [WILDCARD_SEED_CONTROL_SURFACE],
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
   * @param {{ envelope: any, mappedItemCount: number, commit?: (() => unknown) | null }} pending
   */
  function finishExecution(node, transaction, pending) {
    if (transaction.promptId !== pending.envelope.promptId) {
      owner.cancel(transaction, "reject");
      forget(node, transaction);
      return false;
    }
    const canCommit = owner.canCommit(transaction, {
      envelope: pending.envelope,
      node,
      surface: WILDCARD_SEED_CONTROL_SURFACE,
      mappedItemCount: pending.mappedItemCount,
    });
    let committed = canCommit;
    if (canCommit && typeof pending.commit === "function") {
      try {
        pending.commit();
      } catch {
        committed = false;
      }
    }
    owner.settle(transaction, pending.envelope);
    forget(node, transaction);
    return committed;
  }

  /**
   * Consume only the exact output object captured from ComfyUI's outer
   * `executed` event. Multiple mapped payloads settle the transaction but are
   * never allowed to publish an editable next seed.
   *
   * @param {any} node
   * @param {unknown} output
   * @param {number} mappedItemCount
   * @param {(() => unknown) | null} [commit]
   */
  async function consumeExecution(node, output, mappedItemCount, commit = null) {
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
    if (matches.length === 1) {
      return finishExecution(node, matches[0], {
        envelope,
        mappedItemCount,
        commit,
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
      commit,
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
  });
  return runtime;
}

export {
  WILDCARD_HISTORY_SURFACE,
  WILDCARD_SEED_CONTROL_SURFACE,
  createPromptStudioWildcardSeedTransaction,
};
