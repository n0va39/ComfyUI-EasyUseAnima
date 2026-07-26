import assert from "node:assert/strict";

// QSTATE-02B contract-only fixture. The reference owner remains test-local;
// QSTATE-02C will replace it with the production transaction core.
//
// Shared ownership stops at frontend-node lifecycle, opaque surface revisions,
// prompt ordering, settlement, and cleanup. Feature adapters retain ownership
// of field catalogs, payload parsing, and actual editable mutations.
const IDENTITY_DECISION = Object.freeze({
  provisional: Object.freeze([
    "frontendNode",
    "nodeEpoch",
    "surfaceRevisions",
    "localSequence",
  ]),
  accepted: Object.freeze(["promptId"]),
  executedEnvelope: Object.freeze([
    "promptId",
    "executionNodeId",
    "displayNodeId",
    "output",
  ]),
  listIndexPolicy: "feature-contract-only",
  mappedEditableCommitPolicy: "single-item-only",
  unavailableIdentityPolicy: "fail-closed",
});

const TERMINAL_REASONS = new Set([
  "cancel",
  "reject",
  "clear",
  "remove",
  "reconfigure",
  "dispose",
]);

function createReferenceHarness({ maxTransactionsPerNode = 3 } = {}) {
  assert(Number.isInteger(maxTransactionsPerNode) && maxTransactionsPerNode > 0);

  let sequence = 0;
  const transactions = new Map();
  const nodeEpochs = new WeakMap();
  const nodeStates = new Map();
  const transactionsByPrompt = new Map();

  function validNode(node) {
    return (
      node !== null
      && (typeof node === "object" || typeof node === "function")
    );
  }

  function normalizedPromptId(promptId) {
    return typeof promptId === "string" && promptId.trim() !== ""
      ? promptId.trim()
      : null;
  }

  function normalizedNodeId(nodeId) {
    if (typeof nodeId === "string" && nodeId.trim() !== "") {
      return nodeId.trim();
    }
    if (typeof nodeId === "number" && Number.isInteger(nodeId)) {
      return String(nodeId);
    }
    return null;
  }

  function normalizedEnvelope(envelope) {
    const promptId = normalizedPromptId(envelope?.promptId);
    const executionNodeId = normalizedNodeId(envelope?.executionNodeId);
    const displayNodeId = envelope?.displayNodeId == null
      ? null
      : normalizedNodeId(envelope.displayNodeId);
    const output = envelope?.output;
    if (
      promptId == null
      || executionNodeId == null
      || (envelope?.displayNodeId != null && displayNodeId == null)
      || output === null
      || (typeof output !== "object" && typeof output !== "function")
    ) {
      return null;
    }
    return { promptId, executionNodeId, displayNodeId, output };
  }

  function validSurfaces(surfaces) {
    return Array.isArray(surfaces)
      && surfaces.length > 0
      && surfaces.every(
        (surface) => typeof surface === "string" && surface.trim() !== "",
      );
  }

  function nodeState(node) {
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

  function revision(state, surface) {
    return state.revisions.get(surface) || 0;
  }

  function tracked(transaction) {
    return Boolean(
      transaction
      && transactions.get(transaction.id) === transaction
      && ["provisional", "accepted"].includes(transaction.state),
    );
  }

  function releasePromptReference(transaction) {
    if (transaction.promptId == null) {
      return;
    }
    const promptTransactions = transactionsByPrompt.get(transaction.promptId);
    promptTransactions?.delete(transaction.id);
    if (promptTransactions?.size === 0) {
      transactionsByPrompt.delete(transaction.promptId);
    }
  }

  function releaseTransaction(transaction) {
    transactions.delete(transaction.id);
    releasePromptReference(transaction);

    const state = nodeStates.get(transaction.node);
    if (state?.epoch !== transaction.nodeEpoch) {
      return;
    }
    state.transactionIds = state.transactionIds.filter(
      (transactionId) => transactionId !== transaction.id,
    );
    for (const surface of transaction.surfaces) {
      if (state.latestBySurface.get(surface) === transaction.id) {
        state.latestBySurface.delete(surface);
      }
    }
  }

  function terminate(transaction, state, reason) {
    if (!tracked(transaction)) {
      return false;
    }
    transaction.state = state;
    transaction.reason = reason;
    releaseTransaction(transaction);
    return true;
  }

  function enforceNodeRetention(state) {
    while (state.transactionIds.length > maxTransactionsPerNode) {
      const oldest = transactions.get(state.transactionIds[0]);
      if (!oldest) {
        state.transactionIds.shift();
        continue;
      }
      terminate(oldest, "cancelled", "retention");
    }
  }

  function captureProvisional({ node, surfaces }) {
    if (!validNode(node) || !validSurfaces(surfaces)) {
      return null;
    }

    const state = nodeState(node);
    const id = `qstate-${++sequence}`;
    const normalizedSurfaces = [
      ...new Set(surfaces.map((surface) => surface.trim())),
    ];
    const transaction = {
      id,
      localSequence: sequence,
      node,
      nodeEpoch: state.epoch,
      promptId: null,
      surfaces: normalizedSurfaces,
      revisions: {},
      state: "provisional",
      reason: null,
    };

    for (const surface of normalizedSurfaces) {
      transaction.revisions[surface] = revision(state, surface);
      state.latestBySurface.set(surface, id);
    }
    transactions.set(id, transaction);
    state.transactionIds.push(id);
    enforceNodeRetention(state);
    return transaction;
  }

  function acceptPrompt(transaction, promptId) {
    const normalized = normalizedPromptId(promptId);
    if (
      !tracked(transaction)
      || transaction.state !== "provisional"
      || normalized == null
    ) {
      return false;
    }

    const promptTransactions = transactionsByPrompt.get(normalized) || new Set();
    const ambiguousNodePrompt = [...promptTransactions].some(
      (transactionId) => transactions.get(transactionId)?.node === transaction.node,
    );
    if (ambiguousNodePrompt) {
      terminate(transaction, "cancelled", "ambiguous-prompt");
      return false;
    }

    transaction.promptId = normalized;
    transaction.state = "accepted";
    promptTransactions.add(transaction.id);
    transactionsByPrompt.set(normalized, promptTransactions);
    return true;
  }

  function markEdited(node, surfaces) {
    const state = validNode(node) ? nodeStates.get(node) : null;
    if (!state || !validSurfaces(surfaces)) {
      return false;
    }
    for (const surface of new Set(surfaces.map((value) => value.trim()))) {
      state.revisions.set(surface, revision(state, surface) + 1);
    }
    return true;
  }

  function canCommit(
    transaction,
    { envelope, node, surface, mappedItemCount = 1 } = {},
  ) {
    const normalized = normalizedEnvelope(envelope);
    if (
      !tracked(transaction)
      || transaction.state !== "accepted"
      || normalized == null
      || transaction.promptId !== normalized.promptId
      || node !== transaction.node
      || mappedItemCount !== 1
    ) {
      return false;
    }

    const state = nodeStates.get(node);
    if (state?.epoch !== transaction.nodeEpoch) {
      return false;
    }
    if (!transaction.surfaces.includes(surface)) {
      return false;
    }
    if (state.latestBySurface.get(surface) !== transaction.id) {
      return false;
    }
    return revision(state, surface) === transaction.revisions[surface];
  }

  function settle(transaction, envelope) {
    const normalized = normalizedEnvelope(envelope);
    if (
      !tracked(transaction)
      || transaction.state !== "accepted"
      || normalized == null
      || transaction.promptId !== normalized.promptId
    ) {
      return false;
    }
    return terminate(transaction, "settled", "executed");
  }

  function cancel(transaction, reason = "cancel") {
    if (!TERMINAL_REASONS.has(reason)) {
      return false;
    }
    return terminate(transaction, "cancelled", reason);
  }

  function finishPrompt(promptId) {
    const normalized = normalizedPromptId(promptId);
    const promptTransactions = normalized == null
      ? null
      : transactionsByPrompt.get(normalized);
    if (!promptTransactions) {
      return 0;
    }
    let finished = 0;
    for (const transactionId of [...promptTransactions]) {
      const transaction = transactions.get(transactionId);
      if (transaction && terminate(transaction, "finished", "prompt-terminal")) {
        finished += 1;
      }
    }
    return finished;
  }

  function disposeNode(node, reason = "dispose") {
    if (
      !validNode(node)
      || !["remove", "reconfigure", "dispose"].includes(reason)
    ) {
      return false;
    }
    const state = nodeStates.get(node);
    if (!state) {
      return false;
    }
    for (const transactionId of [...state.transactionIds]) {
      const transaction = transactions.get(transactionId);
      if (transaction) {
        terminate(transaction, "cancelled", reason);
      }
    }
    state.revisions.clear();
    state.latestBySurface.clear();
    state.transactionIds.length = 0;
    nodeStates.delete(node);
    return true;
  }

  const owner = {
    captureProvisional,
    acceptPrompt,
    markEdited,
    canCommit,
    settle,
    cancel,
    finishPrompt,
    disposeNode,
  };
  const inspect = () => ({
    transactionCount: transactions.size,
    nodeStateCount: nodeStates.size,
    promptReferenceCount: [...transactionsByPrompt.values()].reduce(
      (count, promptTransactions) => count + promptTransactions.size,
      0,
    ),
    orderingReferenceCount: [...nodeStates.values()].reduce(
      (count, state) => count + state.latestBySurface.size,
      0,
    ),
  });
  return { owner, inspect };
}

const expectedApi = [
  "captureProvisional",
  "acceptPrompt",
  "markEdited",
  "canCommit",
  "settle",
  "cancel",
  "finishPrompt",
  "disposeNode",
].sort();
assert.deepEqual(Object.keys(createReferenceHarness().owner).sort(), expectedApi);

function envelope(promptId, output = {}) {
  return {
    promptId,
    executionNodeId: "backend-node",
    displayNodeId: "frontend-node",
    output,
  };
}

const scenarios = [
  {
    name: "provisional capture requires only local node and surfaces",
    run({ owner }) {
      const node = {};
      assert.equal(owner.captureProvisional({ node: null, surfaces: ["surface-a"] }), null);
      assert.equal(owner.captureProvisional({ node, surfaces: [] }), null);

      const transaction = owner.captureProvisional({
        node,
        surfaces: ["surface-a"],
      });
      assert(transaction);
      assert.equal(transaction.promptId, null);
      assert.equal(transaction.state, "provisional");
      assert.equal(
        owner.canCommit(transaction, {
          envelope: envelope("prompt-a"),
          node,
          surface: "surface-a",
        }),
        false,
      );
      assert.equal(owner.acceptPrompt(transaction, ""), false);
      assert.equal(owner.acceptPrompt(transaction, "prompt-a"), true);
      assert.equal(owner.acceptPrompt(transaction, "prompt-a"), false);
    },
  },
  {
    name: "queue rejection cancels provisional state and references",
    run({ owner, inspect }) {
      const node = {};
      const transaction = owner.captureProvisional({
        node,
        surfaces: ["surface-a"],
      });
      assert(transaction);
      assert.equal(owner.cancel(transaction, "reject"), true);
      assert.equal(owner.acceptPrompt(transaction, "prompt-rejected"), false);
      assert.deepEqual(inspect(), {
        transactionCount: 0,
        nodeStateCount: 1,
        promptReferenceCount: 0,
        orderingReferenceCount: 0,
      });
    },
  },
  {
    name: "accepted prompt and frontend node ownership gate editable commit",
    run({ owner }) {
      const node = {};
      const transaction = owner.captureProvisional({
        node,
        surfaces: ["surface-a"],
      });
      assert(transaction);
      assert.equal(owner.acceptPrompt(transaction, "prompt-a"), true);

      const executedEnvelope = envelope("prompt-a");
      assert.equal(
        owner.canCommit(transaction, {
          envelope: executedEnvelope,
          node,
          surface: "surface-a",
        }),
        true,
      );
      assert.equal(
        owner.canCommit(transaction, {
          envelope: null,
          node,
          surface: "surface-a",
        }),
        false,
      );
      assert.equal(
        owner.canCommit(transaction, {
          envelope: envelope("prompt-other"),
          node,
          surface: "surface-a",
        }),
        false,
      );
      assert.equal(
        owner.canCommit(transaction, {
          envelope: executedEnvelope,
          node: {},
          surface: "surface-a",
        }),
        false,
      );
    },
  },
  {
    name: "multiple mapped payloads cannot commit editable state",
    run({ owner }) {
      const node = {};
      const transaction = owner.captureProvisional({
        node,
        surfaces: ["surface-a"],
      });
      assert(transaction);
      assert.equal(owner.acceptPrompt(transaction, "prompt-mapped"), true);
      const executedEnvelope = envelope("prompt-mapped");

      for (const mappedItemCount of [0, 2, 3]) {
        assert.equal(
          owner.canCommit(transaction, {
            envelope: executedEnvelope,
            node,
            surface: "surface-a",
            mappedItemCount,
          }),
          false,
        );
      }
      assert.equal(
        owner.canCommit(transaction, {
          envelope: executedEnvelope,
          node,
          surface: "surface-a",
          mappedItemCount: 1,
        }),
        true,
      );
    },
  },
  {
    name: "opaque surface revisions invalidate only the edited surface",
    run({ owner }) {
      const node = {};
      const transaction = owner.captureProvisional({
        node,
        surfaces: ["surface-a", "surface-b"],
      });
      assert(transaction);
      assert.equal(owner.acceptPrompt(transaction, "prompt-edit"), true);
      assert.equal(owner.markEdited(node, ["surface-a"]), true);

      const executedEnvelope = envelope("prompt-edit");
      assert.equal(
        owner.canCommit(transaction, {
          envelope: executedEnvelope,
          node,
          surface: "surface-a",
        }),
        false,
      );
      assert.equal(
        owner.canCommit(transaction, {
          envelope: executedEnvelope,
          node,
          surface: "surface-b",
        }),
        true,
      );
      assert.equal(
        owner.canCommit(transaction, {
          envelope: executedEnvelope,
          node,
          surface: "unknown-surface",
        }),
        false,
      );
    },
  },
  {
    name: "latest capture wins while older settlement remains valid",
    run({ owner, inspect }) {
      const node = {};
      const older = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      const newer = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      assert(older && newer);
      assert.equal(owner.acceptPrompt(older, "prompt-old"), true);
      assert.equal(owner.acceptPrompt(newer, "prompt-new"), true);

      const olderEnvelope = envelope("prompt-old");
      const newerEnvelope = envelope("prompt-new");
      assert.equal(
        owner.canCommit(older, {
          envelope: olderEnvelope,
          node,
          surface: "surface-a",
        }),
        false,
      );
      assert.equal(
        owner.canCommit(newer, {
          envelope: newerEnvelope,
          node,
          surface: "surface-a",
        }),
        true,
      );
      assert.equal(owner.settle(older, olderEnvelope), true);
      assert.equal(inspect().transactionCount, 1);
      assert.equal(owner.settle(newer, newerEnvelope), true);
      assert.equal(owner.settle(newer, newerEnvelope), false);
      assert.equal(inspect().transactionCount, 0);
      assert.equal(inspect().promptReferenceCount, 0);
      assert.equal(inspect().orderingReferenceCount, 0);
    },
  },
  {
    name: "cancel clear and prompt terminal signals release transactions",
    run({ owner, inspect }) {
      for (const reason of ["cancel", "clear"]) {
        const node = {};
        const transaction = owner.captureProvisional({
          node,
          surfaces: ["surface-a"],
        });
        assert(transaction);
        assert.equal(owner.acceptPrompt(transaction, `prompt-${reason}`), true);
        assert.equal(owner.cancel(transaction, reason), true);
        assert.equal(owner.cancel(transaction, reason), false);
      }

      const firstNode = {};
      const secondNode = {};
      const first = owner.captureProvisional({
        node: firstNode,
        surfaces: ["surface-a"],
      });
      const second = owner.captureProvisional({
        node: secondNode,
        surfaces: ["surface-b"],
      });
      assert(first && second);
      assert.equal(owner.acceptPrompt(first, "prompt-terminal"), true);
      assert.equal(owner.acceptPrompt(second, "prompt-terminal"), true);
      assert.equal(owner.finishPrompt("prompt-terminal"), 2);
      assert.equal(owner.finishPrompt("prompt-terminal"), 0);
      assert.equal(inspect().transactionCount, 0);
      assert.equal(inspect().promptReferenceCount, 0);
      assert.equal(inspect().orderingReferenceCount, 0);
    },
  },
  {
    name: "remove reconfigure and dispose release every node reference",
    run({ owner, inspect }) {
      for (const reason of ["remove", "reconfigure", "dispose"]) {
        const node = {};
        const first = owner.captureProvisional({
          node,
          surfaces: ["surface-a"],
        });
        const second = owner.captureProvisional({
          node,
          surfaces: ["surface-b"],
        });
        assert(first && second);
        assert.equal(owner.acceptPrompt(first, `prompt-${reason}-a`), true);
        assert.equal(owner.acceptPrompt(second, `prompt-${reason}-b`), true);
        assert.equal(owner.markEdited(node, ["surface-a"]), true);
        assert.equal(owner.disposeNode(node, reason), true);
        assert.equal(
          owner.canCommit(first, {
            envelope: envelope(`prompt-${reason}-a`),
            node,
            surface: "surface-a",
          }),
          false,
        );
        assert.equal(
          owner.canCommit(second, {
            envelope: envelope(`prompt-${reason}-b`),
            node,
            surface: "surface-b",
          }),
          false,
        );
      }
      assert.deepEqual(inspect(), {
        transactionCount: 0,
        nodeStateCount: 0,
        promptReferenceCount: 0,
        orderingReferenceCount: 0,
      });
    },
  },
  {
    name: "superseded in-flight retention is bounded per node",
    run() {
      const { owner, inspect } = createReferenceHarness({
        maxTransactionsPerNode: 2,
      });
      const node = {};
      const first = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      const second = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      assert(first && second);
      assert.equal(owner.acceptPrompt(first, "prompt-retained-a"), true);
      assert.equal(owner.acceptPrompt(second, "prompt-retained-b"), true);

      const third = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      assert(third);
      assert.equal(owner.acceptPrompt(third, "prompt-retained-c"), true);
      assert.equal(first.state, "cancelled");
      assert.equal(first.reason, "retention");
      assert.equal(inspect().transactionCount, 2);
      assert.equal(inspect().promptReferenceCount, 2);
      assert.equal(inspect().orderingReferenceCount, 1);
      assert.equal(
        owner.canCommit(first, {
          envelope: envelope("prompt-retained-a"),
          node,
          surface: "surface-a",
        }),
        false,
      );
      assert.equal(owner.disposeNode(node), true);
      assert.deepEqual(inspect(), {
        transactionCount: 0,
        nodeStateCount: 0,
        promptReferenceCount: 0,
        orderingReferenceCount: 0,
      });
    },
  },
];

for (const scenario of scenarios) {
  scenario.run(createReferenceHarness());
}

assert.deepEqual(
  IDENTITY_DECISION,
  {
    provisional: [
      "frontendNode",
      "nodeEpoch",
      "surfaceRevisions",
      "localSequence",
    ],
    accepted: ["promptId"],
    executedEnvelope: [
      "promptId",
      "executionNodeId",
      "displayNodeId",
      "output",
    ],
    listIndexPolicy: "feature-contract-only",
    mappedEditableCommitPolicy: "single-item-only",
    unavailableIdentityPolicy: "fail-closed",
  },
);

console.log(`Queue UI transaction contract smoke passed: ${scenarios.length} scenarios.`);
