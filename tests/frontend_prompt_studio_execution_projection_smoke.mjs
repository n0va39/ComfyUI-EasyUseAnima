import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const contract = JSON.parse(readFileSync(new URL(
  "./fixtures/prompt_studio_execution_projection_contract.v1.json",
  import.meta.url,
), "utf8"));

assert.equal(contract.contract, "QSTATE-04C1");
assert.equal(contract.version, 1);
assert.deepEqual(
  Object.keys(contract.state_classes).sort(),
  ["execution_derived_delta", "non_editable_history", "submitted_snapshot"],
);
assert.deepEqual(contract.persistence, {
  linked: "overlay_only",
  naia: "canonical",
});
assert.deepEqual(contract.surfaces, [
  "prompt.execution.linked:<fieldId>",
  "prompt.execution.naia:<fieldId>",
  "prompt.execution.naia_resolution",
  "prompt.wildcard_seed_control",
]);

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function snapshotFields(fields) {
  return Object.fromEntries(Object.entries(fields).map(([fieldId, field]) => [
    fieldId,
    {
      kind: field.kind,
      textRevision: field.text_revision,
      structureRevision: field.structure_revision,
      connectionFingerprint: field.connection_fingerprint ?? null,
    },
  ]));
}

function createState(initial = {}) {
  return {
    editable: clone(initial.editable ?? {}),
    fields: clone(initial.fields ?? {}),
    wildcardSeed: initial.wildcard_seed,
    wildcardRevision: 0,
    latestAccepted: null,
    transactions: new Map(),
    consumedEnvelopes: new Set(),
    linkedOverlay: {},
    commits: [],
    settledEnvelopes: [],
    terminalFailures: [],
    ignored: [],
  };
}

function accept(state, event) {
  state.transactions.set(event.prompt_id, {
    promptId: event.prompt_id,
    fields: snapshotFields(state.fields),
    wildcardRevision: state.wildcardRevision,
    terminal: false,
    settled: false,
  });
  state.latestAccepted = event.prompt_id;
}

function editField(state, event) {
  const field = state.fields[event.field_id];
  assert(field, `unknown edit field: ${event.field_id}`);
  field.text_revision += 1;
  if (field.kind === "linked") {
    field.local_fallback = event.value;
    delete state.linkedOverlay[event.field_id];
  } else if (field.kind === "naia") {
    field.canonical = event.value;
  }
}

function changeStructure(state, event) {
  const field = state.fields[event.field_id];
  assert(field, `unknown structure field: ${event.field_id}`);
  field.structure_revision += 1;
  if ("connection_fingerprint" in event) {
    field.connection_fingerprint = event.connection_fingerprint;
  }
  if ("kind" in event) {
    field.kind = event.kind;
  }
  delete state.linkedOverlay[event.field_id];
}

function failTransaction(state, event) {
  const transaction = state.transactions.get(event.prompt_id);
  assert(transaction, `unknown failed prompt: ${event.prompt_id}`);
  transaction.terminal = true;
  transaction.settled = true;
  state.terminalFailures.push(event.prompt_id);
}

function canProjectField(state, transaction, fieldId, expectedKind) {
  const queued = transaction.fields[fieldId];
  const current = state.fields[fieldId];
  if (!queued || !current || queued.kind !== expectedKind || current.kind !== expectedKind) {
    state.ignored.push(`field_identity:${fieldId}`);
    return false;
  }
  if (queued.textRevision !== current.text_revision) {
    state.ignored.push(`text_revision:${fieldId}`);
    return false;
  }
  if (queued.structureRevision !== current.structure_revision) {
    state.ignored.push(`structure_revision:${fieldId}`);
    return false;
  }
  return true;
}

function projectLinked(state, transaction, delta) {
  if (!canProjectField(state, transaction, delta.field_id, "linked")) {
    return;
  }
  const queued = transaction.fields[delta.field_id];
  const current = state.fields[delta.field_id];
  if (
    queued.connectionFingerprint !== current.connection_fingerprint
    || delta.connection_fingerprint !== current.connection_fingerprint
  ) {
    state.ignored.push(`connection_fingerprint:${delta.field_id}`);
    return;
  }
  state.linkedOverlay[delta.field_id] = delta.value;
  state.commits.push(`linked:${delta.field_id}`);
}

function projectNaia(state, transaction, delta) {
  if (!canProjectField(state, transaction, delta.field_id, "naia")) {
    return;
  }
  state.fields[delta.field_id].canonical = delta.value;
  state.commits.push(`naia:${delta.field_id}`);
}

function consumeEnvelope(state, event) {
  if (!event.identity) {
    state.ignored.push("missing_identity");
    return;
  }
  const transaction = state.transactions.get(event.prompt_id);
  if (!transaction) {
    state.ignored.push("missing_identity");
    return;
  }
  if (
    transaction.settled
    || transaction.terminal
    || state.consumedEnvelopes.has(event.identity)
  ) {
    state.ignored.push(`duplicate:${event.identity}`);
    return;
  }

  transaction.settled = true;
  state.consumedEnvelopes.add(event.identity);
  state.settledEnvelopes.push(event.identity);

  if (event.mapped_count !== 1) {
    state.ignored.push(`mapped_count:${event.mapped_count}`);
    return;
  }
  if (event.prompt_id !== state.latestAccepted) {
    state.ignored.push(`not_latest:${event.prompt_id}`);
    return;
  }

  const delta = event.execution_delta ?? {};
  for (const linked of delta.linked ?? []) {
    projectLinked(state, transaction, linked);
  }
  for (const naia of delta.naia ?? []) {
    projectNaia(state, transaction, naia);
  }
  if (
    "wildcard_seed" in delta
    && transaction.wildcardRevision === state.wildcardRevision
  ) {
    state.wildcardSeed = delta.wildcard_seed;
    state.commits.push("wildcard_seed_control");
  }
}

function runScenario(scenario) {
  const state = createState(scenario.initial);
  for (const event of scenario.events) {
    if (event.type === "accept") {
      accept(state, event);
    } else if (event.type === "edit") {
      editField(state, event);
    } else if (event.type === "structure") {
      changeStructure(state, event);
    } else if (event.type === "failure") {
      failTransaction(state, event);
    } else if (event.type === "envelope") {
      consumeEnvelope(state, event);
    } else {
      assert.fail(`unknown event type: ${event.type}`);
    }
  }

  const canonicalText = {};
  const serializedText = {};
  for (const [fieldId, field] of Object.entries(state.fields)) {
    if (field.kind === "linked") {
      serializedText[fieldId] = field.local_fallback;
    } else if (field.kind === "naia") {
      canonicalText[fieldId] = field.canonical;
      serializedText[fieldId] = field.canonical;
    }
  }

  const actual = {
    latest_accepted: state.latestAccepted,
    editable: state.editable,
    linked_overlay: state.linkedOverlay,
    canonical_text: canonicalText,
    serialized_text: serializedText,
    commits: state.commits,
    settled_envelopes: state.settledEnvelopes,
    ignored: state.ignored,
  };
  if (state.wildcardSeed !== undefined) {
    actual.wildcard_seed = state.wildcardSeed;
  }
  if (state.terminalFailures.length) {
    actual.terminal_failures = state.terminalFailures;
  }

  assert.deepEqual(actual, scenario.expected, scenario.id);
}

assert.equal(contract.scenarios.length, 12);
for (const scenario of contract.scenarios) {
  runScenario(scenario);
}

console.log("Prompt Studio execution projection contract smoke passed.");
