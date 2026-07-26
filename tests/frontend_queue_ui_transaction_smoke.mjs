import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const transactionModule = await import(dataModule(
  "../web/js/lifecycle/queue_ui_transaction.js",
));
const { createQueueUiTransactionOwner } = transactionModule;

assert.deepEqual(Object.keys(transactionModule), [
  "createQueueUiTransactionOwner",
]);

const CONTRACT_DECISIONS = Object.freeze({
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
  featureSemanticsPolicy: "adapter-owned",
});

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

assert.equal(typeof createQueueUiTransactionOwner, "function");
assert.deepEqual(
  Object.keys(createQueueUiTransactionOwner()).sort(),
  expectedApi,
);
assert.throws(
  () => createQueueUiTransactionOwner({ maxTransactionsPerNode: 0 }),
  /positive integer/,
);
assert.throws(
  () => createQueueUiTransactionOwner({ maxTransactionsPerPrompt: 1.5 }),
  /positive integer/,
);

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
    name: "provisional capture requires only local node and opaque surfaces",
    run() {
      const owner = createQueueUiTransactionOwner();
      const node = {};
      assert.equal(
        owner.captureProvisional({ node: null, surfaces: ["surface-a"] }),
        null,
      );
      assert.equal(owner.captureProvisional({ node, surfaces: [] }), null);
      assert.equal(
        owner.captureProvisional({ node, surfaces: ["surface-a", 1] }),
        null,
      );

      const transaction = owner.captureProvisional({
        node,
        surfaces: [" surface-a ", "surface-a"],
      });
      assert(transaction);
      assert.equal(Object.isFrozen(transaction), true);
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
      assert.equal(owner.acceptPrompt(transaction, " prompt-a "), true);
      assert.equal(transaction.promptId, "prompt-a");
      assert.equal(transaction.state, "accepted");
      assert.equal(owner.acceptPrompt(transaction, "prompt-a"), false);
    },
  },
  {
    name: "queue rejection cancels provisional state",
    run() {
      const owner = createQueueUiTransactionOwner();
      const transaction = owner.captureProvisional({
        node: {},
        surfaces: ["surface-a"],
      });
      assert(transaction);
      assert.equal(owner.cancel(transaction, "unknown"), false);
      assert.equal(owner.cancel(transaction, "reject"), true);
      assert.equal(transaction.state, "cancelled");
      assert.equal(transaction.reason, "reject");
      assert.equal(owner.acceptPrompt(transaction, "prompt-rejected"), false);
      assert.equal(owner.cancel(transaction, "reject"), false);
    },
  },
  {
    name: "accepted prompt envelope and frontend node gate editable commit",
    run() {
      const owner = createQueueUiTransactionOwner();
      const node = {};
      const transaction = owner.captureProvisional({
        node,
        surfaces: ["surface-a"],
      });
      assert(transaction);
      assert.equal(owner.acceptPrompt(transaction, "prompt-a"), true);

      const executedEnvelope = envelope("prompt-a");
      assert.equal(owner.canCommit(transaction, {
        envelope: executedEnvelope,
        node,
        surface: "surface-a",
      }), true);
      for (const invalidEnvelope of [
        null,
        { ...executedEnvelope, promptId: "" },
        { ...executedEnvelope, promptId: "prompt-other" },
        { ...executedEnvelope, executionNodeId: null },
        { ...executedEnvelope, displayNodeId: {} },
        { ...executedEnvelope, output: null },
      ]) {
        assert.equal(owner.canCommit(transaction, {
          envelope: invalidEnvelope,
          node,
          surface: "surface-a",
        }), false);
      }
      assert.equal(owner.canCommit(transaction, {
        envelope: executedEnvelope,
        node: {},
        surface: "surface-a",
      }), false);
      assert.equal(owner.canCommit(transaction, {
        envelope: executedEnvelope,
        node,
        surface: "unknown-surface",
      }), false);
    },
  },
  {
    name: "ambiguous accepted identity fails closed",
    run() {
      const owner = createQueueUiTransactionOwner();
      const node = {};
      const first = owner.captureProvisional({
        node,
        surfaces: ["surface-a"],
      });
      const ambiguous = owner.captureProvisional({
        node,
        surfaces: ["surface-b"],
      });
      assert(first && ambiguous);
      assert.equal(owner.acceptPrompt(first, "prompt-shared"), true);
      assert.equal(owner.acceptPrompt(ambiguous, "prompt-shared"), false);
      assert.equal(ambiguous.state, "cancelled");
      assert.equal(ambiguous.reason, "ambiguous-prompt");
      assert.equal(owner.canCommit(ambiguous, {
        envelope: envelope("prompt-shared"),
        node,
        surface: "surface-b",
      }), false);
    },
  },
  {
    name: "multiple mapped payloads cannot commit editable state",
    run() {
      const owner = createQueueUiTransactionOwner();
      const node = {};
      const transaction = owner.captureProvisional({
        node,
        surfaces: ["surface-a"],
      });
      assert(transaction);
      assert.equal(owner.acceptPrompt(transaction, "prompt-mapped"), true);
      const executedEnvelope = envelope("prompt-mapped");

      for (const mappedItemCount of [0, 2, 3]) {
        assert.equal(owner.canCommit(transaction, {
          envelope: executedEnvelope,
          node,
          surface: "surface-a",
          mappedItemCount,
        }), false);
      }
      assert.equal(owner.canCommit(transaction, {
        envelope: executedEnvelope,
        node,
        surface: "surface-a",
        mappedItemCount: 1,
      }), true);
    },
  },
  {
    name: "opaque revisions invalidate only the edited surface",
    run() {
      const owner = createQueueUiTransactionOwner();
      const node = {};
      const transaction = owner.captureProvisional({
        node,
        surfaces: ["surface-a", "surface-b"],
      });
      assert(transaction);
      assert.equal(owner.acceptPrompt(transaction, "prompt-edit"), true);
      assert.equal(owner.markEdited(node, [" surface-a "]), true);
      assert.equal(owner.markEdited(node, []), false);

      const executedEnvelope = envelope("prompt-edit");
      assert.equal(owner.canCommit(transaction, {
        envelope: executedEnvelope,
        node,
        surface: "surface-a",
      }), false);
      assert.equal(owner.canCommit(transaction, {
        envelope: executedEnvelope,
        node,
        surface: "surface-b",
      }), true);
    },
  },
  {
    name: "latest capture wins while older settlement remains valid",
    run() {
      const owner = createQueueUiTransactionOwner();
      const node = {};
      const older = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      const newer = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      assert(older && newer);
      assert.equal(owner.acceptPrompt(older, "prompt-old"), true);
      assert.equal(owner.acceptPrompt(newer, "prompt-new"), true);

      const olderEnvelope = envelope("prompt-old");
      const newerEnvelope = envelope("prompt-new");
      assert.equal(owner.canCommit(older, {
        envelope: olderEnvelope,
        node,
        surface: "surface-a",
      }), false);
      assert.equal(owner.canCommit(newer, {
        envelope: newerEnvelope,
        node,
        surface: "surface-a",
      }), true);
      assert.equal(owner.settle(older, envelope("wrong-prompt")), false);
      assert.equal(owner.settle(older, olderEnvelope), true);
      assert.equal(older.state, "settled");
      assert.equal(older.reason, "executed");
      assert.equal(owner.settle(newer, newerEnvelope), true);
      assert.equal(owner.settle(newer, newerEnvelope), false);
      assert.equal(owner.finishPrompt("prompt-old"), 0);
    },
  },
  {
    name: "cancel clear and prompt terminal signals release transactions",
    run() {
      const owner = createQueueUiTransactionOwner();
      for (const reason of ["cancel", "clear"]) {
        const transaction = owner.captureProvisional({
          node: {},
          surfaces: ["surface-a"],
        });
        assert(transaction);
        assert.equal(owner.acceptPrompt(transaction, `prompt-${reason}`), true);
        assert.equal(owner.cancel(transaction, reason), true);
        assert.equal(transaction.state, "cancelled");
        assert.equal(transaction.reason, reason);
      }

      const first = owner.captureProvisional({
        node: {},
        surfaces: ["surface-a"],
      });
      const second = owner.captureProvisional({
        node: {},
        surfaces: ["surface-b"],
      });
      assert(first && second);
      assert.equal(owner.acceptPrompt(first, "prompt-terminal"), true);
      assert.equal(owner.acceptPrompt(second, "prompt-terminal"), true);
      assert.equal(owner.finishPrompt("prompt-terminal"), 2);
      assert.equal(first.state, "finished");
      assert.equal(second.state, "finished");
      assert.equal(first.reason, "prompt-terminal");
      assert.equal(owner.finishPrompt("prompt-terminal"), 0);
    },
  },
  {
    name: "remove reconfigure and dispose invalidate node epochs",
    run() {
      for (const reason of ["remove", "reconfigure", "dispose"]) {
        const owner = createQueueUiTransactionOwner();
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
        assert.equal(owner.disposeNode(node, reason), true);
        assert.equal(first.state, "cancelled");
        assert.equal(second.state, "cancelled");
        assert.equal(first.reason, reason);
        assert.equal(owner.disposeNode(node, reason), false);

        const replacement = owner.captureProvisional({
          node,
          surfaces: ["surface-a"],
        });
        assert(replacement);
        assert.equal(replacement.nodeEpoch, first.nodeEpoch + 1);
        assert.equal(owner.disposeNode(node), true);
      }
    },
  },
  {
    name: "orphaned transaction retention is bounded by node and prompt",
    run() {
      const owner = createQueueUiTransactionOwner({
        maxTransactionsPerNode: 2,
        maxTransactionsPerPrompt: 2,
      });
      const node = {};
      const first = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      const second = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      assert(first && second);
      assert.equal(owner.acceptPrompt(first, "prompt-retained-a"), true);
      assert.equal(owner.acceptPrompt(second, "prompt-retained-b"), true);
      const third = owner.captureProvisional({ node, surfaces: ["surface-a"] });
      assert(third);
      assert.equal(first.state, "cancelled");
      assert.equal(first.reason, "retention");
      assert.equal(owner.acceptPrompt(third, "prompt-retained-c"), true);
      assert.equal(owner.canCommit(first, {
        envelope: envelope("prompt-retained-a"),
        node,
        surface: "surface-a",
      }), false);

      const promptTransactions = [0, 1, 2].map((index) => {
        const promptNode = {};
        const transaction = owner.captureProvisional({
          node: promptNode,
          surfaces: ["surface-prompt"],
        });
        assert(transaction);
        assert.equal(owner.acceptPrompt(transaction, "prompt-wide"), true);
        return { promptNode, transaction };
      });
      assert.equal(promptTransactions[0].transaction.state, "cancelled");
      assert.equal(promptTransactions[0].transaction.reason, "retention");
      assert.equal(owner.finishPrompt("prompt-wide"), 2);
      assert.equal(promptTransactions[1].transaction.state, "finished");
      assert.equal(promptTransactions[2].transaction.state, "finished");
      assert.equal(owner.disposeNode(node), true);
    },
  },
];

for (const scenario of scenarios) {
  scenario.run();
}

assert.deepEqual(CONTRACT_DECISIONS, {
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
  featureSemanticsPolicy: "adapter-owned",
});

console.log(`Queue UI transaction production smoke passed: ${scenarios.length} scenarios.`);
