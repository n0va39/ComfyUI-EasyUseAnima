import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

const queueModule = await import(dataModule("../web/js/aio/generator_queue_runtime.js"));
assert.deepEqual(
  Object.keys(queueModule),
  ["aioCreateGeneratorQueueRuntime"],
  "Generator queue runtime must expose only its factory contract",
);

const SPECIAL_RANDOM = -1;
const SPECIAL_INCREMENT = -2;
const SPECIAL_DECREMENT = -3;
const MIN_SEED = 0;
const MAX_SEED = 100;
const SEED_CONTROLS = ["fixed", "randomize", "increment", "decrement"];

function normalizeSeedValue(value, fallback = SPECIAL_RANDOM) {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) {
    return fallback;
  }
  return Math.max(SPECIAL_DECREMENT, Math.min(MAX_SEED, Math.trunc(numberValue)));
}

function normalizeSeedControl(value) {
  const normalized = String(value || "").trim();
  return SEED_CONTROLS.includes(normalized) ? normalized : "fixed";
}

function createPrompt(nodeId = 42) {
  return {
    output: {
      [String(nodeId)]: {
        class_type: "EasyUseAnimaAIOGenerator",
        inputs: {
          generation_settings: "live-settings",
          untouched: "payload-value",
        },
      },
      99: {
        class_type: "OtherNode",
        inputs: { value: 9 },
      },
    },
    workflow: {
      nodes: [
        {
          id: nodeId,
          type: "EasyUseAnimaAIOGenerator",
          widgets_values: ["visible-widget", "live-settings"],
        },
        { id: 99, type: "OtherNode", widgets_values: [9] },
      ],
      links: [],
    },
    extra_data: { keep: true },
  };
}

function createFixture(options = {}) {
  const trace = [];
  const randomValues = [...(options.randomValues || [17, 23, 31])];
  const node = {
    id: options.nodeId ?? 42,
    mode: options.mode ?? 0,
    widgets: [
      { name: "seed" },
      { name: "generation_settings" },
    ],
    settings: {
      sampler: {
        seed: options.seed ?? SPECIAL_RANDOM,
        seed_after_generate: options.seedControl ?? "fixed",
        spectrum: { enabled: true },
      },
      optional_feature: { enabled: true },
    },
  };
  if (Object.prototype.hasOwnProperty.call(options, "lastSeed")) {
    node.lastSeed = options.lastSeed;
  }
  const nodes = options.nodes || [node];
  let cloneCalls = 0;
  const runtime = queueModule.aioCreateGeneratorQueueRuntime({
    constants: {
      settingsWidgetName: "generation_settings",
      minSeed: MIN_SEED,
      maxSeed: MAX_SEED,
      specialSeedRandom: SPECIAL_RANDOM,
      specialSeedIncrement: SPECIAL_INCREMENT,
      specialSeedDecrement: SPECIAL_DECREMENT,
    },
    settingsCore: {
      normalizeSeedValue,
      normalizeSeedControl,
      cloneJson(value) {
        cloneCalls += 1;
        return clone(value);
      },
      settingsToCompactJson: JSON.stringify,
    },
    nodeAdapter: {
      listNodes: () => nodes,
      isBypassed: (candidate) => candidate.mode === 4,
      getSettings: (candidate) => candidate.settings,
      sanitizeSettings(settings) {
        trace.push("sanitize");
        settings.optional_feature.enabled = false;
        settings.sampler.spectrum.enabled = false;
        return settings;
      },
      getLastQueuedSeed: (candidate) => candidate.lastSeed,
      updateSeed(candidate, seed, updateOptions) {
        trace.push(`commit:${seed}:${updateOptions.lastQueuedSeed}:${updateOptions.markDirty}`);
        if (options.commitError) {
          throw options.commitError;
        }
        candidate.settings.sampler.seed = seed;
        candidate.lastSeed = updateOptions.lastQueuedSeed;
      },
    },
    queueAdapter: {
      async loadOptionalDependencies(loadOptions) {
        trace.push(`load:${loadOptions?.retryErrors}`);
      },
    },
    randomSeed() {
      trace.push("random");
      return randomValues.length ? randomValues.shift() : 0;
    },
  });
  return {
    runtime,
    node,
    trace,
    cloneCalls: () => cloneCalls,
  };
}

{
  const fixture = createFixture({ seed: SPECIAL_RANDOM, seedControl: "fixed" });
  const prompt = createPrompt();
  const originalPrompt = clone(prompt);
  const originalSettings = clone(fixture.node.settings);
  const transaction = fixture.runtime.preparePrompt(prompt);

  assert.ok(transaction, "a live generator output must produce a queue transaction");
  assert.notEqual(transaction.prompt, prompt, "queue preparation must clone the prompt");
  assert.deepEqual(prompt, originalPrompt, "queue preparation must not mutate the caller prompt");
  assert.deepEqual(
    fixture.node.settings,
    originalSettings,
    "optional dependency sanitization must not mutate live settings",
  );
  assert.equal(transaction.commits.length, 1);
  assert.equal(transaction.commits[0].queuedSeed, 17);
  assert.equal(
    transaction.commits[0].liveSeed,
    SPECIAL_RANDOM,
    "fixed mode must preserve the live random sentinel",
  );
  const queuedSettingsText = transaction.prompt.output["42"].inputs.generation_settings;
  const queuedSettings = JSON.parse(queuedSettingsText);
  assert.equal(queuedSettings.sampler.seed, 17);
  assert.equal(queuedSettings.sampler.spectrum.enabled, false);
  assert.equal(queuedSettings.optional_feature.enabled, false);
  assert.equal(transaction.prompt.output["42"].inputs.untouched, "payload-value");
  assert.equal(
    transaction.prompt.workflow.nodes[0].widgets_values[1],
    queuedSettingsText,
    "the cloned workflow hidden widget must match the queued payload",
  );
  assert.equal(prompt.workflow.nodes[0].widgets_values[1], "live-settings");
  assert.deepEqual(transaction.prompt.output["99"], prompt.output["99"]);
}

function preparedSeeds(options) {
  const fixture = createFixture(options);
  const transaction = fixture.runtime.preparePrompt(createPrompt());
  assert.ok(transaction);
  return transaction.commits[0];
}

{
  const commit = preparedSeeds({ seed: 10, seedControl: "fixed" });
  assert.equal(commit.queuedSeed, 10);
  assert.equal(commit.liveSeed, 10);
}
{
  const commit = preparedSeeds({ seed: 10, seedControl: "randomize", randomValues: [29] });
  assert.equal(commit.queuedSeed, 10);
  assert.equal(commit.liveSeed, 29);
}
{
  const commit = preparedSeeds({ seed: MAX_SEED, seedControl: "increment" });
  assert.equal(commit.queuedSeed, MAX_SEED);
  assert.equal(commit.liveSeed, MAX_SEED, "increment must clamp at max seed");
}
{
  const commit = preparedSeeds({ seed: MIN_SEED, seedControl: "decrement" });
  assert.equal(commit.queuedSeed, MIN_SEED);
  assert.equal(commit.liveSeed, MIN_SEED, "decrement must clamp at min seed");
}
{
  const commit = preparedSeeds({
    seed: SPECIAL_INCREMENT,
    seedControl: "fixed",
    lastSeed: 99,
  });
  assert.equal(commit.queuedSeed, MAX_SEED);
  assert.equal(commit.liveSeed, SPECIAL_INCREMENT);
}
{
  const commit = preparedSeeds({
    seed: SPECIAL_DECREMENT,
    seedControl: "fixed",
    lastSeed: MIN_SEED,
  });
  assert.equal(commit.queuedSeed, MIN_SEED);
  assert.equal(commit.liveSeed, SPECIAL_DECREMENT);
}
{
  const commit = preparedSeeds({
    seed: SPECIAL_INCREMENT,
    seedControl: "fixed",
    lastSeed: null,
    randomValues: [37],
  });
  assert.equal(commit.queuedSeed, 37, "a null last seed must use a fresh random seed");
}

{
  const fixture = createFixture({
    seed: SPECIAL_RANDOM,
    seedControl: "increment",
    randomValues: [40],
  });
  const prompt = createPrompt();
  const tailObject = { tail: true };
  const owner = { name: "queue-owner" };
  const result = { prompt_id: "accepted", node_errors: {} };
  let receivedArgs = null;
  let receivedThis = null;
  const wrapped = fixture.runtime.wrapQueuePrompt(function (...args) {
    fixture.trace.push("queue");
    receivedArgs = args;
    receivedThis = this;
    return result;
  });

  const returned = await wrapped.call(owner, 5, prompt, "tail", tailObject);
  assert.equal(receivedThis, owner, "the original queue receiver must be preserved");
  assert.equal(receivedArgs.length, 4);
  assert.equal(receivedArgs[0], 5);
  assert.notEqual(receivedArgs[1], prompt);
  assert.equal(receivedArgs[2], "tail");
  assert.equal(receivedArgs[3], tailObject);
  assert.equal(returned, result, "the original resolved result must be preserved");
  assert.deepEqual(fixture.trace, [
    "load:true",
    "sanitize",
    "random",
    "queue",
    "commit:41:40:false",
  ]);
  assert.equal(fixture.node.lastSeed, 40);
  assert.equal(fixture.node.settings.sampler.seed, 41);
  assert.equal(
    fixture.node.settings.sampler.spectrum.enabled,
    true,
    "accepted seed commit must not copy sanitized optional settings into live state",
  );
  assert.equal(JSON.parse(receivedArgs[1].output["42"].inputs.generation_settings).sampler.seed, 40);
  assert.equal(prompt.output["42"].inputs.generation_settings, "live-settings");
}

{
  const commitError = new Error("panel update failed");
  const fixture = createFixture({
    seed: 18,
    seedControl: "increment",
    commitError,
  });
  const result = { prompt_id: "accepted-despite-local-commit", node_errors: {} };
  const wrapped = fixture.runtime.wrapQueuePrompt(() => result);
  assert.equal(
    await wrapped(0, createPrompt()),
    result,
    "a local seed commit failure must preserve the accepted queue result",
  );
  assert.equal(fixture.node.settings.sampler.seed, 18);
  assert.equal(fixture.node.lastSeed, undefined);
  assert.equal(fixture.trace.includes("commit:19:18:false"), true);
}

for (const nodeErrors of [
  { 42: { errors: ["bad input"] } },
  ["bad input"],
  "bad input",
]) {
  const fixture = createFixture({ seed: 12, seedControl: "increment" });
  const result = { node_errors: nodeErrors };
  const wrapped = fixture.runtime.wrapQueuePrompt(() => result);
  assert.equal(await wrapped(0, createPrompt()), result);
  assert.equal(fixture.node.lastSeed, undefined);
  assert.equal(fixture.node.settings.sampler.seed, 12);
  assert.equal(
    fixture.trace.some((item) => item.startsWith("commit:")),
    false,
    "non-empty node_errors must not commit queued or live seeds",
  );
}

{
  const fixture = createFixture({ seed: 13, seedControl: "increment" });
  const result = { prompt_id: "accepted-with-malformed-validation-metadata" };
  Object.defineProperty(result, "node_errors", {
    get() {
      throw new Error("malformed node_errors getter");
    },
  });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => result);
  assert.equal(await wrapped(0, createPrompt()), result);
  assert.equal(fixture.node.settings.sampler.seed, 13);
  assert.equal(fixture.node.lastSeed, undefined);
}

for (const failureMode of ["throw", "reject"]) {
  const fixture = createFixture({ seed: 15, seedControl: "decrement" });
  const failure = new Error(`queue-${failureMode}`);
  const wrapped = fixture.runtime.wrapQueuePrompt(() => {
    if (failureMode === "throw") {
      throw failure;
    }
    return Promise.reject(failure);
  });
  let caught = null;
  try {
    await wrapped(0, createPrompt());
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, failure, "the original thrown/rejected error must be preserved");
  assert.equal(fixture.node.lastSeed, undefined);
  assert.equal(fixture.node.settings.sampler.seed, 15);
  assert.equal(fixture.trace.some((item) => item.startsWith("commit:")), false);
}

{
  const fixture = createFixture({ mode: 4 });
  const prompt = createPrompt();
  assert.equal(fixture.runtime.preparePrompt(prompt), null);
  assert.equal(fixture.cloneCalls(), 0, "bypassed generators must not clone the prompt");
}

for (const malformedPrompt of [
  null,
  {},
  { output: [] },
  { output: { 42: { inputs: [] } } },
]) {
  const fixture = createFixture();
  assert.equal(fixture.runtime.preparePrompt(malformedPrompt), null);
  assert.equal(fixture.cloneCalls(), 0);
}

{
  const fixture = createFixture();
  const circularPrompt = createPrompt();
  circularPrompt.circular = circularPrompt;
  assert.equal(fixture.runtime.preparePrompt(circularPrompt), null);
  assert.equal(fixture.node.settings.sampler.seed, SPECIAL_RANDOM);
}

{
  const fixture = createFixture();
  const prompt = { output: {}, workflow: { nodes: [] } };
  const result = { prompt_id: "pass-through" };
  let receivedPrompt = null;
  const wrapped = fixture.runtime.wrapQueuePrompt(function (number, nextPrompt) {
    receivedPrompt = nextPrompt;
    assert.equal(number, 3);
    return result;
  });
  assert.equal(await wrapped(3, prompt), result);
  assert.equal(receivedPrompt, prompt, "missing generator output must pass the original prompt through");
  assert.deepEqual(fixture.trace, ["load:true"]);
}

console.log("Frontend AiO generator queue runtime smoke passed.");
