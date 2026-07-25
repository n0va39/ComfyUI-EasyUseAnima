import assert from "node:assert/strict";

// QSTATE-01 contract-only fixture. This reference owner is deliberately local
// to the test. QSTATE-02 replaces it with an import from
// web/js/lifecycle/queue_ui_transaction.js and must keep this scenario table.
//
// Direct-owner identity evidence:
// - app.queuePrompt's afterQueue callback can observe result.prompt_id.
// - a captured frontend node supplies node_id, but the queue result does not
//   supply the mapped/subgraph list_index component.
// - current onExecuted(message) adapters receive feature UI payloads without
//   prompt_id, node_id, or list_index.
// - the backend seed execution context distinguishes invocations with
//   prompt_id + node_id + list_index.
//
// Therefore a live commit requires the exact three-part identity below.
// Missing host correlation is a QSTATE-02 blocker and always fails closed; it
// does not authorize broader production wiring.
const IDENTITY_DECISION = Object.freeze({
  components: Object.freeze(["promptId", "nodeId", "listIndex"]),
  queueResult: Object.freeze(["promptId"]),
  executedUiPayload: Object.freeze([]),
  unavailableIdentityPolicy: "fail-closed",
});

// Shared ownership ends at opaque surface tokens and their revisions. QSTATE-03
// and QSTATE-04 feature adapters own atomic field catalogs, commit allowlists,
// and actual commit payload validation.
const TERMINAL_REASONS = new Set([
  "cancel",
  "reject",
  "clear",
  "remove",
  "reconfigure",
  "dispose",
]);

function createReferenceHarness() {
  let sequence = 0;
  const transactions = new Map();
  const revisionsByNode = new Map();
  const latestByNodeSurface = new Map();

  function normalizedNodeId(nodeId) {
    if (
      typeof nodeId === "string"
      && nodeId.trim() !== ""
    ) {
      return nodeId.trim();
    }
    if (typeof nodeId === "number" && Number.isInteger(nodeId)) {
      return String(nodeId);
    }
    return null;
  }

  function normalizedIdentity(identity) {
    const promptId = typeof identity?.promptId === "string"
      ? identity.promptId.trim()
      : "";
    const nodeId = normalizedNodeId(identity?.nodeId);
    const hasListIndex = Object.prototype.hasOwnProperty.call(
      identity || {},
      "listIndex",
    );
    const listIndex = identity?.listIndex;
    const validListIndex = listIndex === null
      || (
        typeof listIndex === "number"
        && Number.isInteger(listIndex)
        && listIndex >= 0
      );
    if (!promptId || nodeId == null || !hasListIndex || !validListIndex) {
      return null;
    }
    return { promptId, nodeId, listIndex };
  }

  function identityMatches(captured, result) {
    const normalizedResult = normalizedIdentity(result);
    return normalizedResult != null
      && captured.promptId === normalizedResult.promptId
      && captured.nodeId === normalizedResult.nodeId
      && captured.listIndex === normalizedResult.listIndex;
  }

  function nodeRevisions(nodeId) {
    let revisions = revisionsByNode.get(nodeId);
    if (!revisions) {
      revisions = new Map();
      revisionsByNode.set(nodeId, revisions);
    }
    return revisions;
  }

  function revision(nodeId, surface) {
    return revisionsByNode.get(nodeId)?.get(surface) || 0;
  }

  function validSurfaces(surfaces) {
    return Array.isArray(surfaces)
      && surfaces.length > 0
      && surfaces.every(
        (surface) => typeof surface === "string" && surface.trim() !== "",
      );
  }

  function tracked(transaction) {
    return Boolean(
      transaction
      && transactions.get(transaction.id) === transaction
      && transaction.state === "pending",
    );
  }

  function releaseTransaction(transaction) {
    transactions.delete(transaction.id);
    for (const surface of transaction.surfaces) {
      const key = `${transaction.nodeId}:${surface}`;
      if (latestByNodeSurface.get(key) === transaction.id) {
        latestByNodeSurface.delete(key);
      }
    }
  }

  function capture({ identity, surfaces }) {
    const normalized = normalizedIdentity(identity);
    if (normalized == null || !validSurfaces(surfaces)) {
      return null;
    }
    const id = `qstate-${++sequence}`;
    const transaction = {
      id,
      identity: normalized,
      nodeId: normalized.nodeId,
      surfaces: [...new Set(surfaces.map((surface) => surface.trim()))],
      revisions: {},
      state: "pending",
      reason: null,
    };
    for (const surface of transaction.surfaces) {
      transaction.revisions[surface] = revision(transaction.nodeId, surface);
      latestByNodeSurface.set(`${transaction.nodeId}:${surface}`, id);
    }
    transactions.set(id, transaction);
    return transaction;
  }

  function markEdited(nodeId, surfaces) {
    const normalized = normalizedNodeId(nodeId);
    if (normalized == null || !validSurfaces(surfaces)) {
      return false;
    }
    const revisions = nodeRevisions(normalized);
    for (const surface of new Set(surfaces.map((value) => value.trim()))) {
      revisions.set(surface, revision(normalized, surface) + 1);
    }
    return true;
  }

  function canCommit(transaction, resultIdentity, surface) {
    if (!tracked(transaction) || !identityMatches(transaction.identity, resultIdentity)) {
      return false;
    }
    if (!transaction.surfaces.includes(surface)) {
      return false;
    }
    if (latestByNodeSurface.get(`${transaction.nodeId}:${surface}`) !== transaction.id) {
      return false;
    }
    return revision(transaction.nodeId, surface) === transaction.revisions[surface];
  }

  function settle(transaction, resultIdentity) {
    if (!tracked(transaction) || !identityMatches(transaction.identity, resultIdentity)) {
      return false;
    }
    transaction.state = "settled";
    releaseTransaction(transaction);
    return true;
  }

  function cancel(transaction, reason = "cancel") {
    if (!tracked(transaction) || !TERMINAL_REASONS.has(reason)) {
      return false;
    }
    transaction.state = "cancelled";
    transaction.reason = reason;
    releaseTransaction(transaction);
    return true;
  }

  function disposeNode(nodeId, reason = "dispose") {
    const normalized = normalizedNodeId(nodeId);
    if (
      normalized == null
      || !["remove", "reconfigure", "dispose"].includes(reason)
    ) {
      return false;
    }
    for (const transaction of [...transactions.values()]) {
      if (transaction.nodeId === normalized) {
        cancel(transaction, reason);
      }
    }
    revisionsByNode.delete(normalized);
    const prefix = `${normalized}:`;
    for (const key of [...latestByNodeSurface.keys()]) {
      if (key.startsWith(prefix)) {
        latestByNodeSurface.delete(key);
      }
    }
    return true;
  }

  const owner = {
    capture,
    markEdited,
    canCommit,
    settle,
    cancel,
    disposeNode,
  };
  const inspect = () => ({
    transactionCount: transactions.size,
    revisionNodeCount: revisionsByNode.size,
    orderingReferenceCount: latestByNodeSurface.size,
  });
  return { owner, inspect };
}

const expectedApi = [
  "capture",
  "markEdited",
  "canCommit",
  "settle",
  "cancel",
  "disposeNode",
].sort();
assert.deepEqual(Object.keys(createReferenceHarness().owner).sort(), expectedApi);

const scenarios = [
  {
    name: "identity is exact and unavailable components fail closed",
    run({ owner }) {
      const surfaces = ["surface-a"];
      for (const identity of [
        { nodeId: "7", listIndex: null },
        { promptId: "prompt-a", nodeId: "7" },
        { promptId: "prompt-a", nodeId: "7", listIndex: -1 },
      ]) {
        assert.equal(owner.capture({ identity, surfaces }), null);
      }
      const identity = {
        promptId: "prompt-a",
        nodeId: "7",
        listIndex: null,
      };
      const transaction = owner.capture({ identity, surfaces });
      assert(transaction);
      assert.equal(owner.canCommit(transaction, identity, "surface-a"), true);
      assert.equal(
        owner.canCommit(
          transaction,
          { promptId: "prompt-a", nodeId: "7" },
          "surface-a",
        ),
        false,
      );
      assert.equal(
        owner.canCommit(
          transaction,
          { promptId: "prompt-b", nodeId: "7", listIndex: null },
          "surface-a",
        ),
        false,
      );
    },
  },
  {
    name: "list index distinguishes mapped and subgraph invocations",
    run({ owner }) {
      const identity = {
        promptId: "prompt-list",
        nodeId: "8",
        listIndex: 0,
      };
      const transaction = owner.capture({
        identity,
        surfaces: ["surface-a"],
      });
      assert(transaction);
      assert.equal(
        owner.canCommit(
          transaction,
          { ...identity, listIndex: 1 },
          "surface-a",
        ),
        false,
      );
      assert.equal(owner.canCommit(transaction, identity, "surface-a"), true);
    },
  },
  {
    name: "feature-defined surface revisions invalidate one atomic token",
    run({ owner }) {
      const identity = {
        promptId: "prompt-edit",
        nodeId: "9",
        listIndex: null,
      };
      const transaction = owner.capture({
        identity,
        surfaces: ["surface-a", "surface-b"],
      });
      assert(transaction);
      assert.equal(owner.markEdited("9", ["surface-a"]), true);
      assert.equal(owner.canCommit(transaction, identity, "surface-a"), false);
      assert.equal(owner.canCommit(transaction, identity, "surface-b"), true);
      assert.equal(owner.canCommit(transaction, identity, "unknown-surface"), false);
    },
  },
  {
    name: "latest capture wins while older diagnostic settlement remains valid",
    run({ owner, inspect }) {
      const olderIdentity = {
        promptId: "prompt-old",
        nodeId: "10",
        listIndex: null,
      };
      const newerIdentity = {
        promptId: "prompt-new",
        nodeId: "10",
        listIndex: null,
      };
      const older = owner.capture({
        identity: olderIdentity,
        surfaces: ["surface-a"],
      });
      const newer = owner.capture({
        identity: newerIdentity,
        surfaces: ["surface-a"],
      });
      assert(older && newer);
      assert.equal(owner.canCommit(older, olderIdentity, "surface-a"), false);
      assert.equal(owner.canCommit(newer, newerIdentity, "surface-a"), true);
      assert.equal(owner.settle(older, olderIdentity), true);
      assert.equal(inspect().transactionCount, 1);
      assert.equal(owner.canCommit(newer, newerIdentity, "surface-a"), true);
      assert.equal(owner.settle(newer, newerIdentity), true);
      assert.equal(owner.settle(newer, newerIdentity), false);
      assert.equal(inspect().transactionCount, 0);
      assert.equal(inspect().orderingReferenceCount, 0);
    },
  },
  {
    name: "cancel reject and clear remove terminal transaction references",
    run({ owner, inspect }) {
      for (const [index, reason] of ["cancel", "reject", "clear"].entries()) {
        const identity = {
          promptId: `prompt-${reason}`,
          nodeId: `11-${index}`,
          listIndex: null,
        };
        const transaction = owner.capture({
          identity,
          surfaces: ["surface-a"],
        });
        assert(transaction);
        assert.equal(owner.cancel(transaction, reason), true);
        assert.equal(owner.canCommit(transaction, identity, "surface-a"), false);
        assert.equal(owner.cancel(transaction, reason), false);
        assert.equal(inspect().transactionCount, 0);
        assert.equal(inspect().orderingReferenceCount, 0);
      }
    },
  },
  {
    name: "remove reconfigure and dispose release every node reference",
    run({ owner, inspect }) {
      for (const [index, reason] of ["remove", "reconfigure", "dispose"].entries()) {
        const nodeId = `12-${index}`;
        const firstIdentity = {
          promptId: `prompt-${reason}-0`,
          nodeId,
          listIndex: 0,
        };
        const secondIdentity = {
          promptId: `prompt-${reason}-1`,
          nodeId,
          listIndex: 1,
        };
        const first = owner.capture({
          identity: firstIdentity,
          surfaces: ["surface-a"],
        });
        const second = owner.capture({
          identity: secondIdentity,
          surfaces: ["surface-b"],
        });
        assert(first && second);
        assert.equal(owner.markEdited(nodeId, ["surface-a"]), true);
        assert.equal(owner.disposeNode(nodeId, reason), true);
        assert.equal(owner.canCommit(first, firstIdentity, "surface-a"), false);
        assert.equal(owner.canCommit(second, secondIdentity, "surface-b"), false);
        assert.deepEqual(inspect(), {
          transactionCount: 0,
          revisionNodeCount: 0,
          orderingReferenceCount: 0,
        });
      }
    },
  },
];

for (const scenario of scenarios) {
  scenario.run(createReferenceHarness());
}

assert.deepEqual(
  IDENTITY_DECISION,
  {
    components: ["promptId", "nodeId", "listIndex"],
    queueResult: ["promptId"],
    executedUiPayload: [],
    unavailableIdentityPolicy: "fail-closed",
  },
);

console.log(`Queue UI transaction contract smoke passed: ${scenarios.length} scenarios.`);
