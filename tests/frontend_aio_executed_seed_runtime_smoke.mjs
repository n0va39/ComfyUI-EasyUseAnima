import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const seedModule = await import(dataModule(
  "../web/js/aio/executed_seed_runtime.js",
));

const SPECIAL_SELECTION_BY_TOKEN = new Map([
  [-1, "randomize"],
  [-2, "increment"],
  [-3, "decrement"],
]);
const STORED_AFTER_GENERATE_CONTROLS = [
  "fixed",
  "randomize",
  "increment",
  "decrement",
];
const AIO_EDITABLE_MAXIMUM = 100;
const AIO_PAYLOAD_FIELDS = Object.freeze([
  "requested_seed",
  "selection",
  "effective_after_generate",
  "execution_seed",
  "next_seed",
]);
const AIO_SEED_INTENT_CONTRACT = Object.freeze({
  payloadFields: AIO_PAYLOAD_FIELDS,
  ownership: Object.freeze({
    seedSelection: Object.freeze({
      name: "aio.seed_selection",
      role: "only-editable-revision-surface",
      owns: Object.freeze(["requested-seed", "stored-after-generate"]),
    }),
    lastSeed: Object.freeze({
      name: "aio.last_seed",
      role: "monotonic-execution-history",
      editableRevisionSurface: false,
    }),
    concreteNextSeed: Object.freeze({
      name: "aio.concrete_next_seed",
      role: "publication-class",
      consumesRevision: "aio.seed_selection",
    }),
  }),
  specialEffectiveAfterGenerate: "fixed",
  specialDisplayPolicy: "never-publish-editable-result",
  concreteDisplayPolicy: "publish-next-seed-if-revision-current",
  lastSeedPolicy:
    "highest-local-queue-sequence-among-successfully-correlated-executed-results",
  queueAcceptancePolicy: "correlation-prerequisite-not-execution-success",
  randomEachPolicy: "one-random-source-call-per-queue-no-uniqueness-retry",
  workflowPolicy: "serialize-requested-seed-and-stored-control",
  useLastPolicy: "execution-seed-to-concrete-fixed",
  newFixedRandomPolicy: "one-random-seed-to-concrete-fixed",
});

function contractPayload({
  requestedSeed,
  storedAfterGenerate,
  executionSeed,
  nextSeed,
}) {
  const selection = SPECIAL_SELECTION_BY_TOKEN.get(requestedSeed) ?? "concrete";
  return {
    requested_seed: String(requestedSeed),
    selection,
    effective_after_generate:
      selection === "concrete" ? storedAfterGenerate : "fixed",
    execution_seed: String(executionSeed),
    next_seed: String(nextSeed),
  };
}

function parseContractSeed(value, { allowSpecial = false, maximum }) {
  if (typeof value !== "string") {
    return null;
  }
  if (allowSpecial && /^-[123]$/.test(value)) {
    return Number(value);
  }
  if (!/^(?:0|[1-9]\d*)$/.test(value)) {
    return null;
  }
  const parsed = BigInt(value);
  if (parsed > BigInt(maximum)) {
    return null;
  }
  return Number(parsed);
}

function validateContractPayload(
  payload,
  { maximum = AIO_EDITABLE_MAXIMUM, mappedItemCount = 1 } = {},
) {
  if (
    !payload
    || mappedItemCount !== 1
    || Object.keys(payload).length !== AIO_PAYLOAD_FIELDS.length
    || !AIO_PAYLOAD_FIELDS.every((field) => Object.hasOwn(payload, field))
  ) {
    return null;
  }
  const requestedSeed = parseContractSeed(
    payload.requested_seed,
    { allowSpecial: true, maximum },
  );
  const executionSeed = parseContractSeed(payload.execution_seed, { maximum });
  const nextSeed = parseContractSeed(payload.next_seed, { maximum });
  if (requestedSeed === null || executionSeed === null || nextSeed === null) {
    return null;
  }
  const selection = SPECIAL_SELECTION_BY_TOKEN.get(requestedSeed) ?? "concrete";
  if (payload.selection !== selection) {
    return null;
  }
  if (
    selection !== "concrete"
    && payload.effective_after_generate !== "fixed"
  ) {
    return null;
  }
  if (
    selection === "concrete"
    && !STORED_AFTER_GENERATE_CONTROLS.includes(
      payload.effective_after_generate,
    )
  ) {
    return null;
  }
  return {
    requestedSeed,
    selection,
    effectiveAfterGenerate: payload.effective_after_generate,
    executionSeed,
    nextSeed,
  };
}

function contractSeedDecision({
  payload,
  storedAfterGenerate,
  currentDisplaySeed,
  revisionCurrent,
  maximum = AIO_EDITABLE_MAXIMUM,
  mappedItemCount = 1,
}) {
  const parsed = validateContractPayload(
    payload,
    { maximum, mappedItemCount },
  );
  if (
    parsed === null
    || !STORED_AFTER_GENERATE_CONTROLS.includes(storedAfterGenerate)
    || (
      parsed.selection === "concrete"
      && parsed.effectiveAfterGenerate !== storedAfterGenerate
    )
  ) {
    return null;
  }
  const special = parsed.selection !== "concrete";
  const shouldPublishEditable =
    !special
    && revisionCurrent === true
    && parsed.nextSeed !== currentDisplaySeed;
  return {
    ...parsed,
    storedAfterGenerate,
    shouldPublishEditable,
    editablePublicationSeed: shouldPublishEditable ? parsed.nextSeed : null,
    workflowSeed: parsed.requestedSeed,
    workflowAfterGenerate: storedAfterGenerate,
  };
}

function contractExplicitConcreteTransition(
  action,
  seed,
  maximum = AIO_EDITABLE_MAXIMUM,
) {
  if (
    !["use-last", "new-fixed-random"].includes(action)
    || !Number.isSafeInteger(seed)
    || seed < 0
    || seed > maximum
  ) {
    return null;
  }
  return { seed, afterGenerate: "fixed" };
}

function recordLastExecutedSeed(state, {
  localQueueSequence,
  executionSeed,
  queueAccepted,
  executionSucceeded,
  correlationSucceeded,
  maximum = AIO_EDITABLE_MAXIMUM,
}) {
  if (
    queueAccepted !== true
    || executionSucceeded !== true
    || correlationSucceeded !== true
    || !Number.isSafeInteger(localQueueSequence)
    || localQueueSequence <= state.localQueueSequence
    || !Number.isSafeInteger(executionSeed)
    || executionSeed < 0
    || executionSeed > maximum
  ) {
    return false;
  }
  state.localQueueSequence = localQueueSequence;
  state.executionSeed = executionSeed;
  return true;
}

assert.deepEqual(
  Object.keys(seedModule),
  ["aioApplyExecutedSeedDisplay"],
);

{
  // Characterization: the current production path destructively replaces a
  // persistent special selection token with the backend concrete next seed.
  const node = { seed: -1 };
  const updates = [];
  assert.equal(seedModule.aioApplyExecutedSeedDisplay(
    node,
    {
      easyuse_anima_aio_seed: [{
        execution_seed: "41",
        next_seed: "42",
      }],
    },
    {
      maximum: 100,
      updateSeed(candidate, seed, options) {
        updates.push([candidate, seed, options]);
        candidate.seed = seed;
      },
    },
  ), true);
  assert.equal(node.__easyuseAnimaLastExecutedSeed, 41);
  assert.equal(node.seed, 42, "current production replaces the -1 selection intent");
  assert.deepEqual(updates, [[node, 42, { markDirty: false }]]);
}

{
  const node = {};
  const updates = [];
  assert.equal(seedModule.aioApplyExecutedSeedDisplay(
    node,
    {
      easyuse_anima_aio_seed: [{
        execution_seed: "18446744073709551615",
        next_seed: "100",
      }],
    },
    {
      maximum: 100,
      updateSeed(_candidate, seed) {
        updates.push(seed);
      },
    },
  ), true);
  assert.equal(node.__easyuseAnimaLastExecutedSeed, undefined);
  assert.deepEqual(updates, [100]);
}

{
  const node = {};
  assert.equal(seedModule.aioApplyExecutedSeedDisplay(
    node,
    {
      easyuse_anima_aio_seed: [{
        execution_seed: "7",
        next_seed: "8",
      }],
    },
    {
      maximum: 100,
      updateSeed() {
        throw new Error("disposed panel");
      },
    },
  ), true);
  assert.equal(
    node.__easyuseAnimaLastExecutedSeed,
    7,
    "backend acceptance remains visible after next-seed publication fails",
  );
}

for (const message of [
  null,
  {},
  { easyuse_anima_aio_seed: [] },
  {
    easyuse_anima_aio_seed: [{
      execution_seed: "-1",
      next_seed: "not-a-seed",
    }],
  },
]) {
  assert.equal(seedModule.aioApplyExecutedSeedDisplay(
    {},
    message,
    {
      maximum: 100,
      updateSeed() {
        throw new Error("must not update");
      },
    },
  ), false);
}

for (const [requestedSeed, selection] of SPECIAL_SELECTION_BY_TOKEN) {
  for (const storedAfterGenerate of STORED_AFTER_GENERATE_CONTROLS) {
    const payload = contractPayload({
      requestedSeed,
      storedAfterGenerate,
      executionSeed: 41,
      nextSeed: 41,
    });
    const decision = contractSeedDecision({
      payload,
      storedAfterGenerate,
      currentDisplaySeed: requestedSeed,
      revisionCurrent: true,
    });
    assert.equal(decision.selection, selection);
    assert.equal(decision.effectiveAfterGenerate, "fixed");
    assert.equal(decision.shouldPublishEditable, false);
    assert.equal(decision.editablePublicationSeed, null);
    assert.equal(decision.workflowSeed, requestedSeed);
    assert.equal(decision.workflowAfterGenerate, storedAfterGenerate);

    const differentCurrentDisplay = contractSeedDecision({
      payload,
      storedAfterGenerate,
      currentDisplaySeed: 99,
      revisionCurrent: true,
    });
    assert.equal(differentCurrentDisplay.shouldPublishEditable, false);
    assert.equal(differentCurrentDisplay.editablePublicationSeed, null);

    const stale = contractSeedDecision({
      payload,
      storedAfterGenerate,
      currentDisplaySeed: 99,
      revisionCurrent: false,
    });
    assert.equal(stale.shouldPublishEditable, false);
  }
}

const concreteNextByControl = new Map([
  ["fixed", 7],
  ["randomize", 91],
  ["increment", 8],
  ["decrement", 6],
]);
for (const [storedAfterGenerate, nextSeed] of concreteNextByControl) {
  const payload = contractPayload({
    requestedSeed: 7,
    storedAfterGenerate,
    executionSeed: 7,
    nextSeed,
  });
  const current = contractSeedDecision({
    payload,
    storedAfterGenerate,
    currentDisplaySeed: 7,
    revisionCurrent: true,
  });
  assert.equal(current.selection, "concrete");
  assert.equal(current.effectiveAfterGenerate, storedAfterGenerate);
  assert.equal(current.shouldPublishEditable, nextSeed !== 7);
  assert.equal(
    current.editablePublicationSeed,
    nextSeed !== 7 ? nextSeed : null,
  );
  assert.equal(current.workflowSeed, 7);
  assert.equal(current.workflowAfterGenerate, storedAfterGenerate);

  const stale = contractSeedDecision({
    payload,
    storedAfterGenerate,
    currentDisplaySeed: 99,
    revisionCurrent: false,
  });
  assert.equal(stale.shouldPublishEditable, false);
}

{
  const validSpecial = contractPayload({
    requestedSeed: -1,
    storedAfterGenerate: "randomize",
    executionSeed: 7,
    nextSeed: 7,
  });
  const invalidPayloads = [
    { ...validSpecial, selection: "increment" },
    { ...validSpecial, effective_after_generate: "randomize" },
    { ...validSpecial, requested_seed: "-4", selection: "concrete" },
    { ...validSpecial, requested_seed: "7.0", selection: "concrete" },
    { ...validSpecial, execution_seed: "7.0" },
    { ...validSpecial, execution_seed: "101" },
    { ...validSpecial, next_seed: "101" },
    { ...validSpecial, next_display_seed: "-1" },
  ];
  for (const payload of invalidPayloads) {
    assert.equal(contractSeedDecision({
      payload,
      storedAfterGenerate: "randomize",
      currentDisplaySeed: -1,
      revisionCurrent: true,
    }), null);
  }
  assert.equal(contractSeedDecision({
    payload: validSpecial,
    storedAfterGenerate: "randomize",
    currentDisplaySeed: -1,
    revisionCurrent: true,
    mappedItemCount: 2,
  }), null);
}

assert.deepEqual(
  contractExplicitConcreteTransition("use-last", 20),
  { seed: 20, afterGenerate: "fixed" },
);
assert.deepEqual(
  contractExplicitConcreteTransition("new-fixed-random", 30),
  { seed: 30, afterGenerate: "fixed" },
);
assert.equal(contractExplicitConcreteTransition("automatic-result", 404), null);
assert.equal(contractExplicitConcreteTransition("use-last", -1), null);
assert.equal(contractExplicitConcreteTransition("use-last", 101), null);

{
  const state = { localQueueSequence: 0, executionSeed: null };
  const result = (overrides) => ({
    localQueueSequence: 2,
    executionSeed: 20,
    queueAccepted: true,
    executionSucceeded: true,
    correlationSucceeded: true,
    ...overrides,
  });
  assert.equal(recordLastExecutedSeed(state, result()), true);
  assert.equal(recordLastExecutedSeed(state, result({
    localQueueSequence: 1,
    executionSeed: 10,
  })), false);
  assert.equal(recordLastExecutedSeed(state, result()), false);
  assert.equal(recordLastExecutedSeed(state, result({
    localQueueSequence: 3,
    executionSeed: 30,
    executionSucceeded: false,
  })), false);
  assert.equal(recordLastExecutedSeed(state, result({
    localQueueSequence: 3,
    executionSeed: 30,
    correlationSucceeded: false,
  })), false);
  assert.equal(recordLastExecutedSeed(state, result({
    localQueueSequence: 3,
    executionSeed: 101,
  })), false);
  assert.deepEqual(state, { localQueueSequence: 2, executionSeed: 20 });
  assert.equal(recordLastExecutedSeed(state, result({
    localQueueSequence: 3,
    executionSeed: 30,
  })), true);
  assert.deepEqual(state, { localQueueSequence: 3, executionSeed: 30 });
}

assert.deepEqual(AIO_SEED_INTENT_CONTRACT, {
  payloadFields: [
    "requested_seed",
    "selection",
    "effective_after_generate",
    "execution_seed",
    "next_seed",
  ],
  ownership: {
    seedSelection: {
      name: "aio.seed_selection",
      role: "only-editable-revision-surface",
      owns: ["requested-seed", "stored-after-generate"],
    },
    lastSeed: {
      name: "aio.last_seed",
      role: "monotonic-execution-history",
      editableRevisionSurface: false,
    },
    concreteNextSeed: {
      name: "aio.concrete_next_seed",
      role: "publication-class",
      consumesRevision: "aio.seed_selection",
    },
  },
  specialEffectiveAfterGenerate: "fixed",
  specialDisplayPolicy: "never-publish-editable-result",
  concreteDisplayPolicy: "publish-next-seed-if-revision-current",
  lastSeedPolicy:
    "highest-local-queue-sequence-among-successfully-correlated-executed-results",
  queueAcceptancePolicy: "correlation-prerequisite-not-execution-success",
  randomEachPolicy: "one-random-source-call-per-queue-no-uniqueness-retry",
  workflowPolicy: "serialize-requested-seed-and-stored-control",
  useLastPolicy: "execution-seed-to-concrete-fixed",
  newFixedRandomPolicy: "one-random-seed-to-concrete-fixed",
});

console.log("AiO executed seed runtime smoke passed.");
