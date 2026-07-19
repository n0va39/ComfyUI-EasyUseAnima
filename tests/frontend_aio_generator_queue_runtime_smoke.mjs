import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [from, to] of Object.entries(replacements)) {
    source = source.replaceAll(from, to);
  }
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

const registryModuleUrl = dataModule("../web/js/lifecycle/host_hook_registry.js");
const queueModule = await import(dataModule(
  "../web/js/aio/generator_queue_runtime.js",
  { "../lifecycle/host_hook_registry.js": registryModuleUrl },
));
assert.deepEqual(
  Object.keys(queueModule),
  ["aioCreateGeneratorQueueRuntime", "aioInstallGeneratorQueuePromptHook"],
  "Generator queue runtime must expose only its factory and installer contracts",
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

function generationSettingsLabel(nodeId) {
  return Number(nodeId) === 42 ? "live-settings" : `live-settings-${nodeId}`;
}

function createGeneratorNode(options = {}) {
  const node = {
    id: options.nodeId ?? 42,
    mode: options.mode ?? 0,
    failAt: options.failAt || "",
    widgets: [
      { name: "seed" },
      { name: "generation_settings" },
    ],
    settings: {
      __fixtureNodeId: options.nodeId ?? 42,
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
  return node;
}

function createPrompt(nodeIds = [42]) {
  const normalizedNodeIds = Array.isArray(nodeIds) ? nodeIds : [nodeIds];
  return {
    output: Object.fromEntries([
      ...normalizedNodeIds.map((nodeId) => [String(nodeId), {
        class_type: "EasyUseAnimaAIOGenerator",
        inputs: {
          generation_settings: generationSettingsLabel(nodeId),
          untouched: "payload-value",
        },
      }]),
      ["99", {
        class_type: "OtherNode",
        inputs: { value: 9 },
      }],
    ]),
    workflow: {
      nodes: [
        ...normalizedNodeIds.map((nodeId) => ({
          id: nodeId,
          type: "EasyUseAnimaAIOGenerator",
          widgets_values: ["visible-widget", generationSettingsLabel(nodeId)],
        })),
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
  const node = createGeneratorNode(options);
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
        const cloned = clone(value);
        if (!cloned?.output || !Array.isArray(cloned?.workflow?.nodes)) {
          return cloned;
        }
        for (const candidate of nodes) {
          const nodeId = String(candidate.id);
          if (candidate.failAt === "output") {
            const queuedInputs = cloned.output[nodeId]?.inputs;
            if (queuedInputs) {
              cloned.output[nodeId].inputs = new Proxy(queuedInputs, {
                set(target, property, nextValue) {
                  if (property === "generation_settings") {
                    throw new Error(`output write failed for ${candidate.id}`);
                  }
                  return Reflect.set(target, property, nextValue);
                },
              });
            }
          }
          if (candidate.failAt === "workflow") {
            const workflowNode = cloned.workflow.nodes.find(
              (item) => String(item?.id) === nodeId,
            );
            if (workflowNode) {
              let currentValues = workflowNode.widgets_values;
              Object.defineProperty(workflowNode, "widgets_values", {
                configurable: true,
                enumerable: true,
                get() {
                  return currentValues;
                },
                set() {
                  throw new Error(`workflow write failed for ${candidate.id}`);
                },
              });
            }
          }
        }
        return cloned;
      },
      settingsToCompactJson(settings) {
        const candidate = nodes.find(
          (item) => String(item.id) === String(settings.__fixtureNodeId),
        );
        if (candidate?.failAt === "serialize") {
          throw new Error(`serialize failed for ${candidate.id}`);
        }
        return JSON.stringify(settings);
      },
    },
    nodeAdapter: {
      listNodes: () => nodes,
      isBypassed: (candidate) => candidate.mode === 4,
      getSettings(candidate) {
        if (candidate.failAt === "getSettings") {
          throw new Error(`getSettings failed for ${candidate.id}`);
        }
        return candidate.settings;
      },
      sanitizeSettings(settings) {
        trace.push("sanitize");
        const candidate = nodes.find(
          (item) => String(item.id) === String(settings.__fixtureNodeId),
        );
        if (candidate?.failAt === "sanitize") {
          throw new Error(`sanitize failed for ${candidate.id}`);
        }
        settings.optional_feature.enabled = false;
        settings.sampler.spectrum.enabled = false;
        return settings;
      },
      getLastQueuedSeed: (candidate) => candidate.lastSeed,
      commitLastQueuedSeed(candidate, seed) {
        candidate.lastSeed = seed;
      },
      updateSeed(candidate, seed, updateOptions) {
        trace.push(`commit:${seed}:${candidate.lastSeed}:${updateOptions.markDirty}`);
        if (options.commitError || candidate.failAt === "updateSeed") {
          throw options.commitError || new Error(`updateSeed failed for ${candidate.id}`);
        }
        candidate.settings.sampler.seed = seed;
      },
    },
    queueAdapter: {
      async loadOptionalDependencies(loadOptions) {
        trace.push(`load:${loadOptions?.retryErrors}`);
        if (options.loadError) {
          throw options.loadError;
        }
        await options.loadOptionalDependencies?.(loadOptions);
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
    nodes,
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

function preparedSeedCase(options) {
  const fixture = createFixture(options);
  const transaction = fixture.runtime.preparePrompt(createPrompt());
  assert.ok(transaction);
  return {
    commit: transaction.commits[0],
    randomCalls: fixture.trace.filter((item) => item === "random").length,
  };
}

{
  const { commit } = preparedSeedCase({ seed: 10, seedControl: "fixed" });
  assert.equal(commit.queuedSeed, 10);
  assert.equal(commit.liveSeed, 10);
}
{
  const { commit } = preparedSeedCase({ seed: 10, seedControl: "randomize", randomValues: [29] });
  assert.equal(commit.queuedSeed, 10);
  assert.equal(commit.liveSeed, 29);
}
{
  const { commit } = preparedSeedCase({ seed: MAX_SEED, seedControl: "increment" });
  assert.equal(commit.queuedSeed, MAX_SEED);
  assert.equal(commit.liveSeed, MAX_SEED, "increment must clamp at max seed");
}
{
  const { commit } = preparedSeedCase({ seed: MIN_SEED, seedControl: "decrement" });
  assert.equal(commit.queuedSeed, MIN_SEED);
  assert.equal(commit.liveSeed, MIN_SEED, "decrement must clamp at min seed");
}

for (const seed of [SPECIAL_RANDOM, SPECIAL_INCREMENT, SPECIAL_DECREMENT]) {
  for (const seedControl of SEED_CONTROLS) {
    for (const hasLastSeed of [false, true]) {
      const options = {
        seed,
        seedControl,
        randomValues: [17, 23, 31],
      };
      if (hasLastSeed) {
        options.lastSeed = 40;
      }
      let expectedQueuedSeed;
      let expectedRandomCalls;
      if (seed === SPECIAL_RANDOM) {
        expectedQueuedSeed = 17;
        expectedRandomCalls = 1;
      } else if (hasLastSeed) {
        expectedQueuedSeed = seed === SPECIAL_INCREMENT ? 41 : 39;
        expectedRandomCalls = 0;
      } else {
        expectedQueuedSeed = 17;
        expectedRandomCalls = 1;
      }
      let expectedLiveSeed;
      if (seedControl === "fixed") {
        expectedLiveSeed = seed;
      } else if (seedControl === "randomize") {
        expectedLiveSeed = expectedRandomCalls === 0 ? 17 : 23;
        expectedRandomCalls += 1;
      } else if (seedControl === "increment") {
        expectedLiveSeed = Math.min(MAX_SEED, expectedQueuedSeed + 1);
      } else {
        expectedLiveSeed = Math.max(MIN_SEED, expectedQueuedSeed - 1);
      }

      const { commit, randomCalls } = preparedSeedCase(options);
      const caseLabel = `${seed}/${seedControl}/last:${hasLastSeed}`;
      assert.equal(commit.queuedSeed, expectedQueuedSeed, `${caseLabel} queued seed`);
      assert.equal(commit.liveSeed, expectedLiveSeed, `${caseLabel} live seed`);
      assert.equal(randomCalls, expectedRandomCalls, `${caseLabel} random consumption`);
    }
  }
}

{
  const { commit } = preparedSeedCase({
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
  const dependencyGate = deferred();
  let originalCalls = 0;
  const fixture = createFixture({
    seed: 12,
    seedControl: "increment",
    loadOptionalDependencies: () => dependencyGate.promise,
  });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => {
    originalCalls += 1;
    return { prompt_id: "after-dependencies", node_errors: {} };
  });
  const pending = wrapped(0, createPrompt());
  await Promise.resolve();
  await Promise.resolve();
  assert.equal(originalCalls, 0, "the original queue must wait for optional dependency loading");
  assert.deepEqual(fixture.trace, ["load:true"]);
  dependencyGate.resolve();
  assert.equal((await pending).prompt_id, "after-dependencies");
  assert.equal(originalCalls, 1);
  assert.deepEqual(fixture.trace, ["load:true", "sanitize", "commit:13:12:false"]);
}

{
  const loadError = new Error("dependency load failed");
  let originalCalls = 0;
  const fixture = createFixture({ loadError });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => {
    originalCalls += 1;
    return { prompt_id: "unreachable", node_errors: {} };
  });
  await assert.rejects(wrapped(0, createPrompt()), (error) => error === loadError);
  assert.equal(originalCalls, 0);
  assert.deepEqual(fixture.trace, ["load:true"]);
}

{
  const queueError = new Error("original queue threw");
  const queuedSeeds = [];
  const fixture = createFixture({ seed: 15, seedControl: "increment" });
  const failing = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queuedSeeds.push(JSON.parse(
      prompt.output["42"].inputs.generation_settings,
    ).sampler.seed);
    throw queueError;
  });
  await assert.rejects(failing(0, createPrompt()), (error) => error === queueError);
  assert.equal(fixture.node.settings.sampler.seed, 15);
  assert.equal(fixture.node.lastSeed, undefined);
  const retry = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queuedSeeds.push(JSON.parse(
      prompt.output["42"].inputs.generation_settings,
    ).sampler.seed);
    return { prompt_id: "retry-after-throw", node_errors: {} };
  });
  await retry(0, createPrompt());
  assert.deepEqual(queuedSeeds, [15, 15], "a synchronous throw must reject its reservation");
}

{
  const fixture = createFixture({ seed: 7, seedControl: "increment" });
  assert.ok(fixture.runtime.preparePrompt(createPrompt()));
  let queuedSeed = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queuedSeed = JSON.parse(
      prompt.output["42"].inputs.generation_settings,
    ).sampler.seed;
    return { prompt_id: "after-standalone-prepare", node_errors: {} };
  });

  await wrapped(0, createPrompt());
  assert.equal(queuedSeed, 7, "standalone preparation must not consume a queue reservation");
  assert.equal(fixture.node.settings.sampler.seed, 8);
}

{
  const fixture = createFixture({ seed: 7, seedControl: "increment" });
  const calls = [];
  const gates = [deferred(), deferred(), deferred()];
  const wrapped = fixture.runtime.wrapQueuePrompt(function (...args) {
    calls.push({ owner: this, args });
    return gates[calls.length - 1].promise;
  });
  const owner = { name: "direct-api-owner" };
  const options = { partialExecutionTargets: [42], previewMethod: "latent2rgb" };
  const tail = { preserve: true };
  const prompt = createPrompt();
  const originalPrompt = clone(prompt);

  const pending = [
    wrapped.call(owner, 0, prompt, options, tail),
    wrapped.call(owner, 0, prompt, options, tail),
    wrapped.call(owner, 0, prompt, options, tail),
  ];
  await new Promise((resolve) => setImmediate(resolve));

  assert.equal(calls.length, 3, "direct API submissions must remain concurrent");
  assert.deepEqual(
    calls.map(({ args }) => JSON.parse(args[1].output["42"].inputs.generation_settings).sampler.seed),
    [7, 8, 9],
    "concurrent direct API submissions must reserve distinct sequential seeds",
  );
  assert.deepEqual(prompt, originalPrompt, "concurrent reservations must not mutate the caller prompt");
  assert.equal(fixture.node.settings.sampler.seed, 7, "live seed changes only after FIFO settlement");
  for (const call of calls) {
    assert.equal(call.owner, owner);
    assert.equal(call.args.length, 4);
    assert.equal(call.args[0], 0);
    assert.equal(call.args[2], options, "queue options identity must survive reservation");
    assert.equal(call.args[3], tail, "queue argument tail identity must survive reservation");
  }

  gates[1].resolve({ prompt_id: "second", node_errors: {} });
  await pending[1];
  assert.equal(
    fixture.node.settings.sampler.seed,
    7,
    "an accepted later reservation must wait for earlier direct API settlement",
  );

  gates[0].resolve({ prompt_id: "   ", node_errors: {} });
  await pending[0];
  assert.equal(
    fixture.node.settings.sampler.seed,
    9,
    "a blank prompt id must reject only its reservation and release the accepted successor",
  );
  assert.equal(fixture.node.lastSeed, 8);

  gates[2].resolve({ prompt_id: "third", node_errors: {} });
  await pending[2];
  assert.equal(fixture.node.settings.sampler.seed, 10);
  assert.equal(fixture.node.lastSeed, 9);
}

{
  const fixture = createFixture({ seed: 7, seedControl: "increment" });
  const queuedSeeds = [];
  const results = [
    { prompt_id: "", node_errors: {} },
    { prompt_id: "retry", node_errors: {} },
  ];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queuedSeeds.push(
      JSON.parse(prompt.output["42"].inputs.generation_settings).sampler.seed,
    );
    return results.shift();
  });

  await wrapped(0, createPrompt());
  assert.equal(fixture.node.settings.sampler.seed, 7);
  await wrapped(0, createPrompt());
  assert.deepEqual(queuedSeeds, [7, 7], "a rejected tail reservation must remain reusable");
  assert.equal(fixture.node.settings.sampler.seed, 8);
  assert.equal(fixture.node.lastSeed, 7);
}

{
  const fixture = createFixture({ seed: 7, seedControl: "increment" });
  const queuedSeeds = [];
  const gates = [deferred(), deferred(), deferred(), deferred()];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queuedSeeds.push(
      JSON.parse(prompt.output["42"].inputs.generation_settings).sampler.seed,
    );
    return gates[queuedSeeds.length - 1].promise;
  });
  const pending = [
    wrapped(0, createPrompt()),
    wrapped(0, createPrompt()),
    wrapped(0, createPrompt()),
  ];
  await new Promise((resolve) => setImmediate(resolve));

  gates[1].resolve({ prompt_id: "", node_errors: {} });
  await pending[1];
  const rejection = new Error("rejected-tail");
  gates[2].reject(rejection);
  let caught = null;
  try {
    await pending[2];
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, rejection);

  const retry = wrapped(0, createPrompt());
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(
    queuedSeeds,
    [7, 8, 9, 8],
    "contiguous rejected tail reservations must collapse to the earliest reusable seed",
  );
  gates[3].resolve({ prompt_id: "retry", node_errors: {} });
  await retry;
  assert.equal(fixture.node.settings.sampler.seed, 7);
  gates[0].resolve({ prompt_id: "first", node_errors: {} });
  await pending[0];
  assert.equal(fixture.node.settings.sampler.seed, 9);
  assert.equal(fixture.node.lastSeed, 8);
}

{
  const fixture = createFixture({ seed: 10, seedControl: "increment" });
  const original = function () {
    this.calls += 1;
    return { prompt_id: "installed", node_errors: {} };
  };
  const host = {
    calls: 0,
    queuePrompt: original,
  };
  const dispose = queueModule.aioInstallGeneratorQueuePromptHook(host, fixture.runtime);
  const installed = host.queuePrompt;
  assert.equal(
    queueModule.aioInstallGeneratorQueuePromptHook(host, fixture.runtime)(),
    false,
  );
  assert.equal(host.queuePrompt, installed, "duplicate registration must not stack AiO callbacks");

  host.queuePrompt = async function (...args) {
    return installed.apply(this, args);
  };
  const foreignWrapper = host.queuePrompt;
  assert.equal(
    queueModule.aioInstallGeneratorQueuePromptHook(host, fixture.runtime)(),
    false,
  );
  assert.equal(
    host.queuePrompt,
    foreignWrapper,
    "registry ownership must stay idempotent below a foreign outer wrapper",
  );
  const result = await host.queuePrompt(0, createPrompt(), "tail");
  assert.equal(result.prompt_id, "installed");
  assert.equal(host.calls, 1, "foreign composition must still reach the original queue once");
  assert.deepEqual(fixture.trace, ["load:true", "sanitize", "commit:11:10:false"]);
  assert.equal(fixture.node.lastSeed, 10);
  assert.equal(fixture.node.settings.sampler.seed, 11);

  fixture.trace.length = 0;
  assert.equal(dispose(), true);
  assert.equal(host.queuePrompt, foreignWrapper, "dispose must preserve a foreign outer wrapper");
  assert.equal((await host.queuePrompt(0, createPrompt())).prompt_id, "installed");
  assert.deepEqual(fixture.trace, [], "disposed AiO callbacks must not remain stale");

  host.queuePrompt = installed;
  const disposeReinstalled = queueModule.aioInstallGeneratorQueuePromptHook(
    host,
    fixture.runtime,
  );
  assert.equal(host.queuePrompt, installed, "reinstall must reuse the current stale registry wrapper");
  await host.queuePrompt(0, createPrompt());
  assert.equal(
    fixture.trace.filter((item) => item === "load:true").length,
    1,
    "reinstall must execute the AiO callback exactly once",
  );
  assert.equal(disposeReinstalled(), true);
  assert.equal(host.queuePrompt, original);
}

{
  const skippedNode = createGeneratorNode({
    nodeId: 42,
    seed: 10,
    seedControl: "increment",
  });
  const targetedNode = createGeneratorNode({
    nodeId: 43,
    seed: 20,
    seedControl: "increment",
  });
  const fixture = createFixture({ nodes: [skippedNode, targetedNode] });
  const prompt = createPrompt([42, 43]);
  const options = {
    partialExecutionTargets: ["43"],
    previewMethod: "latent2rgb",
  };
  let receivedPrompt = null;
  let receivedOptions = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((number, queuedPrompt, queuedOptions) => {
    assert.equal(number, 0);
    receivedPrompt = queuedPrompt;
    receivedOptions = queuedOptions;
    return { prompt_id: "partial-target", node_errors: {} };
  });
  await wrapped(0, prompt, options);

  assert.equal(receivedOptions, options, "partial execution options must preserve identity");
  assert.equal(
    receivedPrompt.output["42"].inputs.generation_settings,
    generationSettingsLabel(42),
    "untargeted AiO payload must stay untouched",
  );
  assert.equal(
    receivedPrompt.workflow.nodes.find((item) => item.id === 42).widgets_values[1],
    generationSettingsLabel(42),
    "untargeted AiO workflow state must stay untouched",
  );
  assert.equal(
    JSON.parse(receivedPrompt.output["43"].inputs.generation_settings).sampler.seed,
    20,
  );
  assert.equal(skippedNode.settings.sampler.seed, 10);
  assert.equal(skippedNode.lastSeed, undefined);
  assert.equal(targetedNode.settings.sampler.seed, 21);
  assert.equal(targetedNode.lastSeed, 20);
}

{
  const invalidNode = createGeneratorNode({
    nodeId: 42,
    seed: 30,
    seedControl: "increment",
  });
  const validNode = createGeneratorNode({
    nodeId: 43,
    seed: 50,
    seedControl: "decrement",
  });
  const fixture = createFixture({ nodes: [invalidNode, validNode] });
  const result = {
    prompt_id: "partial-valid-queue",
    node_errors: {
      upstream_bad: {
        errors: ["bad input"],
        dependent_outputs: ["42"],
      },
    },
  };
  const wrapped = fixture.runtime.wrapQueuePrompt(() => result);
  assert.equal(await wrapped(0, createPrompt([42, 43])), result);
  assert.equal(invalidNode.settings.sampler.seed, 30);
  assert.equal(invalidNode.lastSeed, undefined);
  assert.equal(validNode.settings.sampler.seed, 49);
  assert.equal(validNode.lastSeed, 50);
}

for (const failAt of ["getSettings", "sanitize", "serialize", "output", "workflow"]) {
  const malformedNode = createGeneratorNode({
    nodeId: 42,
    seed: 11,
    seedControl: "increment",
    failAt,
  });
  const healthyNode = createGeneratorNode({
    nodeId: 43,
    seed: 21,
    seedControl: "increment",
  });
  const fixture = createFixture({ nodes: [malformedNode, healthyNode] });
  const prompt = createPrompt([42, 43]);
  const originalMalformedSettings = clone(malformedNode.settings);
  let queuedPrompt = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    queuedPrompt = nextPrompt;
    return { prompt_id: `isolated-${failAt}`, node_errors: {} };
  });
  await wrapped(0, prompt);

  assert.equal(
    queuedPrompt.output["42"].inputs.generation_settings,
    generationSettingsLabel(42),
    `${failAt}: malformed output payload must stay untouched`,
  );
  assert.equal(
    queuedPrompt.workflow.nodes.find((item) => item.id === 42).widgets_values[1],
    generationSettingsLabel(42),
    `${failAt}: malformed workflow hidden state must stay untouched`,
  );
  assert.deepEqual(
    malformedNode.settings,
    originalMalformedSettings,
    `${failAt}: malformed live settings must stay untouched`,
  );
  assert.equal(malformedNode.lastSeed, undefined);
  assert.equal(
    JSON.parse(queuedPrompt.output["43"].inputs.generation_settings).sampler.seed,
    21,
    `${failAt}: healthy node must still queue`,
  );
  assert.equal(healthyNode.settings.sampler.seed, 22, `${failAt}: healthy live seed`);
  assert.equal(healthyNode.lastSeed, 21, `${failAt}: healthy last seed`);
}

{
  const failingCommitNode = createGeneratorNode({
    nodeId: 42,
    seed: 61,
    seedControl: "increment",
    failAt: "updateSeed",
  });
  const healthyCommitNode = createGeneratorNode({
    nodeId: 43,
    seed: 71,
    seedControl: "decrement",
  });
  const fixture = createFixture({ nodes: [failingCommitNode, healthyCommitNode] });
  const result = { prompt_id: "isolated-commit", node_errors: {} };
  const wrapped = fixture.runtime.wrapQueuePrompt(() => result);
  assert.equal(await wrapped(0, createPrompt([42, 43])), result);
  assert.equal(failingCommitNode.settings.sampler.seed, 61);
  assert.equal(
    failingCommitNode.lastSeed,
    61,
    "accepted queue reservation must survive a live widget update failure",
  );
  assert.equal(healthyCommitNode.settings.sampler.seed, 70);
  assert.equal(healthyCommitNode.lastSeed, 71);
}

{
  const commitError = new Error("panel update failed");
  const fixture = createFixture({
    seed: 18,
    seedControl: "increment",
    commitError,
  });
  const result = { prompt_id: "accepted-despite-local-commit", node_errors: {} };
  const queuedSeeds = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queuedSeeds.push(
      JSON.parse(prompt.output["42"].inputs.generation_settings).sampler.seed,
    );
    return result;
  });
  assert.equal(
    await wrapped(0, createPrompt()),
    result,
    "a local seed commit failure must preserve the accepted queue result",
  );
  assert.equal(fixture.node.settings.sampler.seed, 18);
  assert.equal(fixture.node.lastSeed, 18);
  assert.equal(fixture.trace.includes("commit:19:18:false"), true);
  assert.equal(await wrapped(0, createPrompt()), result);
  assert.deepEqual(
    queuedSeeds,
    [18, 19],
    "an accepted reservation remains authoritative after updateSeed fails",
  );
  assert.equal(fixture.node.settings.sampler.seed, 18);
  assert.equal(fixture.node.lastSeed, 19);
}

for (const nodeErrors of [
  { 42: { errors: ["bad input"] } },
  ["bad input"],
  "bad input",
  true,
  1,
]) {
  const fixture = createFixture({ seed: 12, seedControl: "increment" });
  const result = { prompt_id: "accepted-with-errors", node_errors: nodeErrors };
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

for (const emptyNodeErrors of [undefined, null, [], "", false, 0]) {
  const fixture = createFixture({ seed: 14, seedControl: "increment" });
  const result = { prompt_id: "accepted-empty-node-errors" };
  if (emptyNodeErrors !== undefined) {
    result.node_errors = emptyNodeErrors;
  }
  const wrapped = fixture.runtime.wrapQueuePrompt(() => result);
  assert.equal(await wrapped(0, createPrompt()), result);
  assert.equal(fixture.node.settings.sampler.seed, 15);
  assert.equal(fixture.node.lastSeed, 14);
}

for (const result of [
  { node_errors: {} },
  { prompt_id: null, node_errors: {} },
  { prompt_id: "", node_errors: {} },
  { prompt_id: " \t\r\n", node_errors: {} },
]) {
  const fixture = createFixture({ seed: 16, seedControl: "increment" });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => result);
  assert.equal(await wrapped(0, createPrompt()), result);
  assert.equal(
    fixture.node.lastSeed,
    undefined,
    "missing or blank prompt ids must not commit a queued seed reservation",
  );
  assert.equal(
    fixture.node.settings.sampler.seed,
    16,
    "missing or blank prompt ids must not advance the live seed",
  );
  assert.equal(
    fixture.trace.some((item) => item.startsWith("commit:")),
    false,
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
  const queuedSeeds = [];
  let queueCalls = 0;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queueCalls += 1;
    queuedSeeds.push(
      JSON.parse(prompt.output["42"].inputs.generation_settings).sampler.seed,
    );
    if (queueCalls === 1 && failureMode === "throw") {
      throw failure;
    }
    if (queueCalls === 1) {
      return Promise.reject(failure);
    }
    return { prompt_id: `retry-${failureMode}`, node_errors: {} };
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
  await wrapped(0, createPrompt());
  assert.deepEqual(
    queuedSeeds,
    [15, 15],
    `${failureMode}: rejected tail seed must remain reusable`,
  );
  assert.equal(fixture.node.lastSeed, 15);
  assert.equal(fixture.node.settings.sampler.seed, 14);
}

{
  const loadError = new Error("optional dependency load failed");
  const fixture = createFixture({
    seed: SPECIAL_RANDOM,
    seedControl: "increment",
    loadError,
  });
  const prompt = createPrompt();
  const originalPrompt = clone(prompt);
  const originalSettings = clone(fixture.node.settings);
  let queueCalls = 0;
  const wrapped = fixture.runtime.wrapQueuePrompt(() => {
    queueCalls += 1;
    return { prompt_id: "must-not-run", node_errors: {} };
  });
  let caught = null;
  try {
    await wrapped(0, prompt);
  } catch (error) {
    caught = error;
  }
  assert.equal(caught, loadError, "optional dependency rejection identity must be preserved");
  assert.equal(queueCalls, 0);
  assert.equal(fixture.cloneCalls(), 0);
  assert.deepEqual(prompt, originalPrompt);
  assert.deepEqual(fixture.node.settings, originalSettings);
  assert.equal(fixture.node.lastSeed, undefined);
  assert.deepEqual(fixture.trace, ["load:true"]);
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
