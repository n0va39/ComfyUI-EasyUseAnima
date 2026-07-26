import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const seedModule = await import(dataModule(
  "../web/js/aio/executed_seed_runtime.js",
));
const queueModule = await import(dataModule(
  "../web/js/lifecycle/queue_ui_transaction.js",
));
const contextModule = await import(dataModule(
  "../web/js/lifecycle/executed_event_context.js",
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
  ["AIO_SEED_SELECTION_SURFACE", "createAioSeedTransaction"],
);

class FakeApi {
  constructor() {
    this.listeners = new Map();
  }

  addEventListener(type, handler) {
    const handlers = this.listeners.get(type) || [];
    handlers.push(handler);
    this.listeners.set(type, handlers);
  }

  removeEventListener(type, handler) {
    this.listeners.set(
      type,
      (this.listeners.get(type) || []).filter((candidate) => candidate !== handler),
    );
  }

  dispatch(type, detail) {
    for (const handler of [...(this.listeners.get(type) || [])]) {
      handler({ detail });
    }
  }
}

function runtimePayload({
  requestedSeed,
  storedAfterGenerate,
  executionSeed,
  nextSeed,
  overrides = {},
}) {
  return {
    easyuse_anima_aio_seed: [{
      ...contractPayload({
        requestedSeed,
        storedAfterGenerate,
        executionSeed,
        nextSeed,
      }),
      ...overrides,
    }],
  };
}

function createRuntimeFixture({
  requestedSeed = 7,
  storedAfterGenerate = "increment",
} = {}) {
  const api = new FakeApi();
  const owner = queueModule.createQueueUiTransactionOwner();
  let runtime = null;
  const context = contextModule.createExecutedEventContext(api, {
    finishPrompt: (promptId) => runtime.finishPrompt(promptId),
  });
  const selection = { requestedSeed, storedAfterGenerate };
  const node = {
    widgets: [
      { name: "seed", callback() {} },
      { name: "generation_settings", callback() {} },
    ],
  };
  const lastPublications = [];
  const editablePublications = [];
  runtime = seedModule.createAioSeedTransaction({
    owner,
    executedContext: context,
    maximum: AIO_EDITABLE_MAXIMUM,
    findWidget(candidate, name) {
      return candidate.widgets.find((widget) => widget.name === name);
    },
    readSelection() {
      return selection;
    },
    publishLastSeed(_candidate, seed) {
      lastPublications.push(seed);
      return true;
    },
    publishConcreteNextSeed(candidate, seed) {
      editablePublications.push(seed);
      selection.requestedSeed = seed;
      candidate.widgets[0].callback(seed);
      candidate.widgets[1].callback();
      return true;
    },
  });
  context.install();

  function capture(promptId, { accept = true } = {}) {
    const captured = runtime.captureQueue([node]);
    assert.equal(captured.length, 1);
    if (accept) {
      assert.equal(runtime.acceptQueue(captured, {
        ok: true,
        result: { prompt_id: promptId },
      }), 1);
    }
    return captured;
  }

  async function execute(promptId, output, { dispatch = true } = {}) {
    if (dispatch) {
      api.dispatch("executed", {
        prompt_id: promptId,
        node: "41",
        output,
      });
    }
    return runtime.consumeExecution(node, output);
  }

  function edit({ seed = selection.requestedSeed, control = selection.storedAfterGenerate }) {
    selection.requestedSeed = seed;
    selection.storedAfterGenerate = control;
    node.widgets[1].callback();
  }

  return {
    api,
    capture,
    context,
    edit,
    editablePublications,
    execute,
    lastPublications,
    node,
    owner,
    runtime,
    selection,
  };
}

{
  const fixture = createRuntimeFixture({
    requestedSeed: -1,
    storedAfterGenerate: "increment",
  });
  fixture.capture("special");
  const output = runtimePayload({
    requestedSeed: -1,
    storedAfterGenerate: "increment",
    executionSeed: 41,
    nextSeed: 41,
  });
  assert.equal(await fixture.execute("special", output), true);
  assert.deepEqual(fixture.lastPublications, [41]);
  assert.deepEqual(fixture.editablePublications, []);
  assert.deepEqual(fixture.selection, {
    requestedSeed: -1,
    storedAfterGenerate: "increment",
  });
}

{
  const fixture = createRuntimeFixture();
  fixture.capture("concrete");
  const output = runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 7,
    nextSeed: 8,
  });
  assert.equal(await fixture.execute("concrete", output), true);
  assert.deepEqual(fixture.lastPublications, [7]);
  assert.deepEqual(fixture.editablePublications, [8]);
  assert.deepEqual(fixture.selection, {
    requestedSeed: 8,
    storedAfterGenerate: "increment",
  });
}

{
  const fixture = createRuntimeFixture();
  fixture.capture("unrelated-settings-edit");
  fixture.node.widgets[1].callback();
  const output = runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 7,
    nextSeed: 8,
  });
  assert.equal(await fixture.execute("unrelated-settings-edit", output), true);
  assert.deepEqual(fixture.lastPublications, [7]);
  assert.deepEqual(
    fixture.editablePublications,
    [8],
    "only the atomic seed/control pair owns the editable revision",
  );
}

{
  const fixture = createRuntimeFixture();
  fixture.capture("stale");
  fixture.edit({ seed: 23, control: "fixed" });
  const output = runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 7,
    nextSeed: 8,
  });
  assert.equal(await fixture.execute("stale", output), true);
  assert.deepEqual(fixture.lastPublications, [7]);
  assert.deepEqual(fixture.editablePublications, []);
  assert.deepEqual(fixture.selection, {
    requestedSeed: 23,
    storedAfterGenerate: "fixed",
  });
}

{
  const fixture = createRuntimeFixture();
  fixture.capture("older");
  fixture.capture("newer");
  const newer = runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 20,
    nextSeed: 21,
  });
  const older = runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 10,
    nextSeed: 11,
  });
  assert.equal(await fixture.execute("newer", newer), true);
  assert.equal(await fixture.execute("older", older), false);
  assert.deepEqual(fixture.lastPublications, [20]);
  assert.deepEqual(fixture.editablePublications, [21]);
}

{
  const fixture = createRuntimeFixture();
  const captured = fixture.capture("adapter-first", { accept: false });
  const output = runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 7,
    nextSeed: 8,
  });
  const pending = fixture.execute("adapter-first", output, { dispatch: false });
  fixture.api.dispatch("executed", {
    prompt_id: "adapter-first",
    node: "41",
    output,
  });
  assert.equal(await pending, false);
  assert.deepEqual(fixture.lastPublications, []);
  assert.equal(fixture.runtime.acceptQueue(captured, {
    ok: true,
    result: { prompt_id: "adapter-first" },
  }), 1);
  assert.deepEqual(fixture.lastPublications, [7]);
  assert.deepEqual(fixture.editablePublications, [8]);
}

for (const output of [
  runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 101,
    nextSeed: 8,
  }),
  runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 7,
    nextSeed: 8,
    overrides: { next_display_seed: "8" },
  }),
  {
    easyuse_anima_aio_seed: [
      contractPayload({
        requestedSeed: 7,
        storedAfterGenerate: "increment",
        executionSeed: 7,
        nextSeed: 8,
      }),
      contractPayload({
        requestedSeed: 7,
        storedAfterGenerate: "increment",
        executionSeed: 7,
        nextSeed: 8,
      }),
    ],
  },
]) {
  const fixture = createRuntimeFixture();
  fixture.capture("invalid");
  assert.equal(await fixture.execute("invalid", output), false);
  assert.deepEqual(fixture.lastPublications, []);
  assert.deepEqual(fixture.editablePublications, []);
}

{
  const fixture = createRuntimeFixture();
  fixture.capture("clone");
  const output = runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 7,
    nextSeed: 8,
  });
  fixture.api.dispatch("executed", {
    prompt_id: "clone",
    node: "41",
    output,
  });
  assert.equal(await fixture.runtime.consumeExecution(
    fixture.node,
    structuredClone(output),
  ), false);
  assert.deepEqual(fixture.lastPublications, []);
  assert.deepEqual(fixture.editablePublications, []);
  fixture.runtime.disposeNode(fixture.node, "dispose");
}

{
  const fixture = createRuntimeFixture();
  fixture.capture("duplicate");
  const output = runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 7,
    nextSeed: 8,
  });
  assert.equal(await fixture.execute("duplicate", output), true);
  assert.equal(await fixture.execute("duplicate", output), false);
  assert.deepEqual(fixture.lastPublications, [7]);
  assert.deepEqual(fixture.editablePublications, [8]);
}

{
  const fixture = createRuntimeFixture();
  fixture.capture("disposed");
  assert.equal(fixture.runtime.disposeNode(fixture.node, "remove"), true);
  const output = runtimePayload({
    requestedSeed: 7,
    storedAfterGenerate: "increment",
    executionSeed: 7,
    nextSeed: 8,
  });
  assert.equal(await fixture.execute("disposed", output), false);
  assert.deepEqual(fixture.lastPublications, []);
  assert.deepEqual(fixture.editablePublications, []);
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
