import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function sourceModule(source) {
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

const seedContractUrl = dataModule(
  "../web/js/prompt_studio/wildcard_seed_contract.js",
);
const seedHistorySource = readFileSync(
  new URL("../web/js/prompt_studio/wildcard_seed_history.js", import.meta.url),
  "utf8",
).replace('from "./wildcard_seed_contract.js"', `from "${seedContractUrl}"`);
const seedHistoryUrl = sourceModule(seedHistorySource);
const hostHookRegistryUrl = dataModule(
  "../web/js/lifecycle/host_hook_registry.js",
);
const queueSource = readFileSync(
  new URL("../web/js/prompt_studio/advanced_queue_seed_runtime.js", import.meta.url),
  "utf8",
)
  .replace('from "./wildcard_seed_contract.js"', `from "${seedContractUrl}"`)
  .replace('from "./wildcard_seed_history.js"', `from "${seedHistoryUrl}"`)
  .replace('from "../lifecycle/host_hook_registry.js"', `from "${hostHookRegistryUrl}"`);
const queueModule = await import(sourceModule(queueSource));
const seedContract = await import(seedContractUrl);
const seedHistory = await import(seedHistoryUrl);
assert.deepEqual(
  Object.keys(queueModule).sort(),
  [
    "createAdvancedQueueSeedRuntime",
    "installAdvancedQueueSeedGraphCleanup",
    "installAdvancedQueueSeedQueueHook",
  ],
);
assert.deepEqual(
  Object.keys(seedContract).sort(),
  [
    "WILDCARD_SEED_MAX",
    "bindWildcardSeedInput",
    "nextWildcardSeed",
    "normalizeWildcardSeed",
    "normalizeWildcardSeedControl",
    "normalizeWildcardSeedInput",
    "optionalWildcardSeed",
    "randomWildcardSeed",
  ],
);
assert.equal(seedContract.WILDCARD_SEED_MAX, Number.MAX_SAFE_INTEGER);
assert.deepEqual(Object.keys(seedHistory).sort(), [
  "PREVIOUS_WILDCARD_EXECUTION_PROPERTY",
  "normalizePreviousWildcardExecution",
  "normalizePreviousWildcardMode",
  "readPreviousWildcardExecution",
  "serializePreviousWildcardExecution",
  "wildcardModeWidgetValue",
  "writePreviousWildcardExecution",
]);
assert.equal(seedContract.optionalWildcardSeed(0), 0);
assert.equal(
  seedContract.optionalWildcardSeed(Number.MAX_SAFE_INTEGER),
  Number.MAX_SAFE_INTEGER,
);
assert.equal(seedContract.optionalWildcardSeed(Number.MAX_SAFE_INTEGER + 1), null);
assert.equal(seedContract.normalizeWildcardSeedInput(0), 0);
assert.equal(seedContract.normalizeWildcardSeedInput("00042"), 42);
assert.equal(
  seedContract.normalizeWildcardSeedInput(String(Number.MAX_SAFE_INTEGER)),
  Number.MAX_SAFE_INTEGER,
);
assert.equal(seedContract.normalizeWildcardSeedInput(-1), null);
assert.equal(seedContract.normalizeWildcardSeedInput(12.9), null);
assert.equal(seedContract.normalizeWildcardSeedInput("12.9"), null);
assert.equal(seedContract.normalizeWildcardSeedInput("1e3"), null);
assert.equal(seedContract.normalizeWildcardSeedInput("9007199254740990.9"), null);
assert.equal(seedContract.normalizeWildcardSeedInput("9007199254740991.0"), null);
assert.equal(seedContract.normalizeWildcardSeedInput("9007199254740992"), null);
assert.equal(seedContract.normalizeWildcardSeedInput(Number.MAX_SAFE_INTEGER + 1), null);
assert.equal(seedContract.nextWildcardSeed(0, "fixed"), 0);
assert.equal(seedContract.nextWildcardSeed(Number.MAX_SAFE_INTEGER, "increment"), 0);
assert.equal(
  seedContract.nextWildcardSeed(0, "decrement"),
  Number.MAX_SAFE_INTEGER,
);
assert.equal(
  seedContract.nextWildcardSeed(Number.MAX_SAFE_INTEGER, "decrement"),
  Number.MAX_SAFE_INTEGER - 1,
);
assert.equal(
  seedContract.nextWildcardSeed(7, "randomize", () => Number.MAX_SAFE_INTEGER),
  Number.MAX_SAFE_INTEGER,
);
assert.equal(
  seedContract.randomWildcardSeed(() => 1),
  Number.MAX_SAFE_INTEGER,
);

{
  const node = { properties: {} };
  assert.equal(seedHistory.readPreviousWildcardExecution(node), null);
  assert.deepEqual(
    seedHistory.writePreviousWildcardExecution(node, { seed: 7, mode: "sequential" }),
    { version: 1, seed: 7, mode: "sequential" },
  );
  const currentValues = Array(22).fill(null);
  currentValues[10] = "일반";
  currentValues[11] = 41;
  currentValues[12] = "randomize";
  const serialized = { widgets_values: currentValues, properties: {} };
  assert.equal(seedHistory.serializePreviousWildcardExecution(node, serialized, {
    modeWidgetIndex: 10,
    seedWidgetIndex: 11,
    controlWidgetIndex: 12,
  }), true);
  assert.equal(serialized.widgets_values[10], "순차");
  assert.equal(serialized.widgets_values[11], 7);
  assert.equal(serialized.widgets_values[12], "fixed");
  assert.deepEqual(
    seedHistory.normalizePreviousWildcardExecution(
      serialized.properties[seedHistory.PREVIOUS_WILDCARD_EXECUTION_PROPERTY],
    ),
    { version: 1, seed: 7, mode: "sequential" },
  );
}
assert.equal(seedContract.normalizeWildcardSeedControl("fixed"), "fixed");
assert.equal(seedContract.normalizeWildcardSeedControl("매번 랜덤"), "randomize");
assert.equal(seedContract.normalizeWildcardSeedControl("증가"), "increment");
assert.equal(seedContract.normalizeWildcardSeedControl("decrement"), "fixed");
assert.equal(
  seedContract.normalizeWildcardSeedControl("randomize", "재현"),
  "fixed",
);
assert.equal(
  seedContract.normalizeWildcardSeedControl("fixed", "순차"),
  "fixed",
  "Sequential must allow a fixed seed",
);

function normalizePromptStudioWildcardMode(value) {
  return ["sequential", "순차"].includes(String(value || "").trim().toLowerCase())
    ? "순차"
    : "일반";
}

for (const surface of ["advanced", "regional"]) {
  const node = {
    surface,
    widgets: {
      wildcard_mode: "일반",
      wildcard_seed: 42,
      wildcard_seed_after_generate: "randomize",
    },
  };
  const selectMode = (target, mode) => {
    const loadedMode = mode;
    target.widgets.wildcard_mode = normalizePromptStudioWildcardMode(mode);
    target.widgets.wildcard_seed_after_generate = seedContract.normalizeWildcardSeedControl(
      target.widgets.wildcard_seed_after_generate,
      loadedMode,
    );
  };

  selectMode(node, "재현");
  assert.equal(node.widgets.wildcard_mode, "일반");
  assert.equal(node.widgets.wildcard_seed_after_generate, "fixed");
  assert.equal(
    seedContract.nextWildcardSeed(
      node.widgets.wildcard_seed,
      node.widgets.wildcard_seed_after_generate,
    ),
    42,
    `${surface} legacy Reproduce alias changed a fixed seed`,
  );

  const reopened = clone(node);
  assert.equal(reopened.widgets.wildcard_mode, "일반");
  assert.equal(reopened.widgets.wildcard_seed_after_generate, "fixed");

  reopened.widgets.wildcard_seed_after_generate = "decrement";
  selectMode(reopened, "일반 채우기");
  assert.equal(reopened.widgets.wildcard_mode, "일반");
  assert.equal(reopened.widgets.wildcard_seed_after_generate, "fixed");
  assert.equal(
    seedContract.normalizeWildcardSeedControl("randomize", "고정"),
    "fixed",
  );
  assert.equal(
    seedContract.normalizeWildcardSeedControl("fixed", "순차"),
    "fixed",
  );
  for (const legacyMode of ["fixed", "고정", "reproduce", "재현"]) {
    selectMode(reopened, legacyMode);
    assert.equal(reopened.widgets.wildcard_mode, "일반");
    assert.equal(reopened.widgets.wildcard_seed_after_generate, "fixed");
  }

  reopened.widgets.wildcard_seed_after_generate = "fixed";
  selectMode(reopened, "순차");
  assert.equal(reopened.widgets.wildcard_mode, "순차");
  assert.equal(reopened.widgets.wildcard_seed_after_generate, "fixed");
}

function seedInputFixture(value) {
  const listeners = new Map();
  return {
    value,
    isConnected: true,
    min: "",
    max: "",
    step: "",
    addEventListener(type, listener) {
      const current = listeners.get(type) || [];
      current.push(listener);
      listeners.set(type, current);
    },
    dispatch(type) {
      for (const listener of listeners.get(type) || []) {
        listener({ type, target: this });
      }
    },
  };
}

function animationFrameFixture() {
  let nextId = 0;
  const frames = new Map();
  return {
    request(callback) {
      const id = ++nextId;
      frames.set(id, callback);
      return id;
    },
    cancel(id) {
      frames.delete(id);
    },
    flushOne() {
      const entry = frames.entries().next().value;
      assert.ok(entry, "an animation frame must be pending");
      const [id, callback] = entry;
      frames.delete(id);
      callback(0);
    },
    pendingCount() {
      return frames.size;
    },
  };
}

for (const surface of ["Advanced", "Regional"]) {
  const unsafeSeed = Number.MAX_SAFE_INTEGER + 1;
  let currentSeed = unsafeSeed;
  const published = [];
  const afterPublish = [];
  const input = seedInputFixture(String(unsafeSeed));
  seedContract.bindWildcardSeedInput(
    input,
    () => currentSeed,
    (seed) => {
      currentSeed = seed;
      published.push(seed);
    },
    surface === "Advanced" ? (seed) => afterPublish.push(seed) : undefined,
  );
  assert.equal(input.min, "0", `${surface} input minimum must use the public contract`);
  assert.equal(
    input.max,
    String(Number.MAX_SAFE_INTEGER),
    `${surface} input maximum must use the public contract`,
  );
  assert.equal(input.step, "1", `${surface} input step must be an exact integer`);

  input.dispatch("blur");
  assert.equal(input.value, String(unsafeSeed), `${surface} loaded unsafe seed must stay unchanged`);
  assert.deepEqual(published, [], `${surface} unsafe blur must not publish`);

  input.value = "41";
  input.dispatch("change");
  input.value = "42";
  input.dispatch("blur");
  assert.deepEqual(published, [41, 42], `${surface} change and blur must publish safe integers`);
  assert.equal(currentSeed, 42);

  for (const invalid of ["42.0", "4.2e1", "9007199254740991.1"]) {
    input.value = invalid;
    input.dispatch("change");
    assert.equal(input.value, "42", `${surface} invalid edit must restore the prior seed`);
  }
  assert.deepEqual(published, [41, 42], `${surface} invalid edits must not publish`);
  assert.deepEqual(
    afterPublish,
    surface === "Advanced" ? [41, 42] : [],
    `${surface} post-publish hook must match successful edits`,
  );
}

{
  const frames = animationFrameFixture();
  const previousRequestAnimationFrame = globalThis.requestAnimationFrame;
  const previousCancelAnimationFrame = globalThis.cancelAnimationFrame;
  globalThis.requestAnimationFrame = (callback) => frames.request(callback);
  globalThis.cancelAnimationFrame = (id) => frames.cancel(id);
  try {
    let canonicalSeed = 17;
    const published = [];
    const input = seedInputFixture("17");
    seedContract.bindWildcardSeedInput(
      input,
      () => canonicalSeed,
      (seed) => {
        canonicalSeed = seed;
        published.push(seed);
      },
    );
    assert.equal(frames.pendingCount(), 1);

    frames.flushOne();
    assert.equal(input.value, "17", "an unchanged canonical seed must not invent an advance");
    assert.deepEqual(published, []);
    assert.equal(frames.pendingCount(), 1);

    canonicalSeed = 18;
    frames.flushOne();
    assert.equal(input.value, "18", "an untouched open input must follow the canonical seed");
    assert.deepEqual(published, []);
    assert.equal(frames.pendingCount(), 1);

    input.value = "23";
    input.dispatch("input");
    canonicalSeed = 19;
    frames.flushOne();
    assert.equal(input.value, "23", "a dirty edit must keep ownership during frame sync");
    assert.deepEqual(published, []);
    assert.equal(frames.pendingCount(), 1);

    input.dispatch("change");
    assert.equal(canonicalSeed, 23);
    assert.deepEqual(published, [23]);
    frames.flushOne();
    assert.equal(input.value, "23");
    assert.equal(frames.pendingCount(), 1);

    input.isConnected = false;
    frames.flushOne();
    assert.equal(frames.pendingCount(), 0, "a detached input must stop frame reservations");
  } finally {
    if (previousRequestAnimationFrame === undefined) {
      delete globalThis.requestAnimationFrame;
    } else {
      globalThis.requestAnimationFrame = previousRequestAnimationFrame;
    }
    if (previousCancelAnimationFrame === undefined) {
      delete globalThis.cancelAnimationFrame;
    } else {
      globalThis.cancelAnimationFrame = previousCancelAnimationFrame;
    }
  }
}

const ADVANCED = "EasyUseAnimaPromptStudioAdvanced";
const ADVANCED_V2 = "EasyUseAnimaPromptStudioAdvancedV2";
const WILDCARD = "EasyUseAnimaWildcard";
const REGIONAL = "EasyUseAnimaPromptStudioRegional";
const SEED_INDEX = 11;
const REGIONAL_SEED_INDEX = 7;
const RESERVED_NEXT_SEED_INPUT = "easyuse_anima_reserved_wildcard_next_seed";
const ADVANCED_QUEUE_SEED_CONTRACT = Object.freeze({
  modeInputName: "wildcard_mode",
  seedInputName: "wildcard_seed",
  controlInputName: "wildcard_seed_after_generate",
  modeWidgetIndex: 10,
  seedWidgetIndex: SEED_INDEX,
  controlWidgetIndex: 12,
  supportsSubgraph: true,
});
const REGIONAL_QUEUE_SEED_CONTRACT = Object.freeze({
  modeInputName: "wildcard_mode",
  seedInputName: "wildcard_seed",
  controlInputName: "wildcard_seed_after_generate",
  modeWidgetIndex: 6,
  seedWidgetIndex: REGIONAL_SEED_INDEX,
  controlWidgetIndex: 8,
  supportsSubgraph: false,
});

const nodeHookConstants = sourceModule(`
  export const NODE_TYPE = "EasyUseAnimaPromptStudio";
  export const ADVANCED_NODE_TYPE = "${ADVANCED}";
  export const ADVANCED_V2_NODE_TYPE = "${ADVANCED_V2}";
  export const EXTEND_NODE_TYPE = "EasyUseAnimaPromptStudioExtend";
  export const WILDCARD_NODE_TYPE = "EasyUseAnimaWildcard";
`);
const nodeHooksSource = readFileSync(
  new URL("../web/js/prompt_studio/node_hooks.js", import.meta.url),
  "utf8",
)
  .replace('from "./constants.js"', `from "${nodeHookConstants}"`)
  .replace('from "../lifecycle/host_hook_registry.js"', `from "${hostHookRegistryUrl}"`);
const nodeHooksModule = await import(sourceModule(nodeHooksSource));
const wildcardWidgetHelpers = sourceModule(`
  export function findWidget(node, name) {
    return node?.widgets?.find((widget) => widget?.name === name) || null;
  }
  export function findInputEl() { return null; }
  export function firstValue(value, fallback) {
    const first = Array.isArray(value) ? value[0] : value;
    return first == null ? fallback : first;
  }
`);
const wildcardValuesSource = readFileSync(
  new URL("../web/js/prompt_studio/wildcard_values.js", import.meta.url),
  "utf8",
)
  .replace('from "./widgets.js"', `from "${wildcardWidgetHelpers}"`)
  .replace('from "./wildcard_seed_contract.js"', `from "${seedContractUrl}"`);
const wildcardValuesModule = await import(sourceModule(wildcardValuesSource));
assert.deepEqual(Object.keys(wildcardValuesModule).sort(), [
  "applyWildcardExecutedInputs",
  "hookWildcardSeedWidget",
  "setRegularWidgetValue",
  "syncWildcardSerialization",
]);

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function widgetValues(seed, mode = "순차", control = "increment") {
  const values = Array(22).fill(null);
  values[10] = mode;
  values[SEED_INDEX] = seed;
  values[12] = control;
  return values;
}

function regionalWidgetValues(seed, mode = "순차", control = "increment") {
  return ["[]", "{}", "1024", "1024 * 1024 (1:1)", 1024, 1024, mode, seed, control];
}

function advancedNode(id, type = ADVANCED, seed = 7) {
  return {
    id,
    type,
    comfyClass: type,
    properties: {},
    widgets: [
      { name: "wildcard_mode", value: "순차" },
      { name: "wildcard_seed", value: seed },
      { name: "wildcard_seed_after_generate", value: "increment" },
    ],
  };
}

function wildcardNode(id, seed = 7) {
  return {
    id,
    type: WILDCARD,
    comfyClass: WILDCARD,
    widgets: [
      { name: "text", value: "__style__" },
      { name: "populated_text", value: "" },
      { name: "mode", value: "일반" },
      { name: "seed", value: seed },
      { name: "control_after_generate", value: "fixed" },
    ],
  };
}

function regionalNode(id, seed = 7) {
  return {
    id,
    type: REGIONAL,
    comfyClass: REGIONAL,
    properties: {},
    widgets: [
      { name: "wildcard_mode", value: "순차" },
      { name: "wildcard_seed", value: seed },
      { name: "wildcard_seed_after_generate", value: "increment" },
    ],
  };
}

function queueSeedContract(node) {
  if ([ADVANCED, ADVANCED_V2].includes(node?.type)) {
    return ADVANCED_QUEUE_SEED_CONTRACT;
  }
  if (node?.type === REGIONAL) {
    return REGIONAL_QUEUE_SEED_CONTRACT;
  }
  return null;
}

function promptFor(nodes, options = {}) {
  const output = {};
  const workflowNodes = [];
  for (const node of nodes) {
    const contract = queueSeedContract(node);
    const mode = node.widgets.find((widget) => widget.name === contract.modeInputName).value;
    const seed = node.widgets.find((widget) => widget.name === contract.seedInputName).value;
    const control = node.widgets.find((widget) => widget.name === contract.controlInputName).value;
    let inputs;
    if (node.type === REGIONAL) {
      inputs = {
          regional_fields: "[]",
          regional_config: "{}",
          wildcard_mode: mode,
          wildcard_seed: seed,
          wildcard_seed_after_generate: control,
        };
    } else {
      inputs = {
          advanced_fields: "[]",
          wildcard_mode: mode,
          wildcard_seed: seed,
          wildcard_seed_after_generate: control,
        };
    }
    output[String(node.id)] = {
      class_type: node.type,
      inputs,
    };
    workflowNodes.push({
      id: node.id,
      type: node.type,
      widgets_values: node.type === REGIONAL
        ? regionalWidgetValues(seed, mode, control)
        : widgetValues(seed, mode, control),
    });
  }
  const consumers = Object.prototype.hasOwnProperty.call(options, "consumers")
    ? options.consumers
    : nodes.map((node, index) => ({ id: 20 + index, source: node.id }));
  for (const consumer of consumers) {
    output[String(consumer.id)] = {
      class_type: consumer.type || "PreviewImage",
      inputs: { source: [consumer.source, 0] },
    };
    workflowNodes.push({
      id: consumer.id,
      type: consumer.type || "PreviewImage",
      widgets_values: [],
    });
  }
  return {
    output,
    workflow: { nodes: workflowNodes, links: [] },
    extra_data: { untouched: true },
  };
}

function createFixture(options = {}) {
  const nodes = options.nodes || [advancedNode(10)];
  const outputNodes = options.outputNodes || nodes.map((_, index) => ({
    id: 20 + index,
    outputNode: true,
  }));
  const randomValues = [...(options.randomValues || [41, 42, 43, 44])];
  const commits = [];
  const previousExecutions = [];
  let randomCalls = 0;
  let cloneCalls = 0;
  let updateFailures = Number(options.updateFailures || 0);
  const runtime = queueModule.createAdvancedQueueSeedRuntime({
    listNodes: () => [...nodes, ...outputNodes],
    getNodeContract: queueSeedContract,
    isOutputNode: (node) => node?.outputNode === true,
    getSeed(node, contract) {
      return node.widgets.find((widget) => widget.name === contract.seedInputName)?.value;
    },
    updateSeed(node, seed, contract) {
      if (updateFailures > 0) {
        updateFailures -= 1;
        throw new Error("seed publish failed");
      }
      commits.push([node.id, seed]);
      node.widgets.find((widget) => widget.name === contract.seedInputName).value = seed;
    },
    updatePreviousExecution(node, execution) {
      previousExecutions.push([node.id, clone(execution)]);
      seedHistory.writePreviousWildcardExecution(node, execution);
    },
    clonePrompt(value) {
      cloneCalls += 1;
      if (options.cloneError) {
        throw options.cloneError;
      }
      return clone(value);
    },
    randomSeed() {
      randomCalls += 1;
      return randomValues.shift() ?? 0;
    },
  });
  return {
    nodes,
    runtime,
    commits,
    previousExecutions,
    randomCalls: () => randomCalls,
    cloneCalls: () => cloneCalls,
  };
}

function seedPromptInputs(node) {
  const contract = queueSeedContract(node);
  const mode = node.widgets.find((widget) => widget.name === contract.modeInputName).value;
  const seed = node.widgets.find((widget) => widget.name === contract.seedInputName).value;
  const control = node.widgets.find((widget) => widget.name === contract.controlInputName).value;
  if (node.type === REGIONAL) {
    return {
        regional_fields: "[]",
        regional_config: "{}",
        wildcard_mode: mode,
        wildcard_seed: seed,
        wildcard_seed_after_generate: control,
      };
  }
  return {
        advanced_fields: "[]",
        wildcard_mode: mode,
        wildcard_seed: seed,
        wildcard_seed_after_generate: control,
      };
}

function seedWorkflowNode(node) {
  const inputs = seedPromptInputs(node);
  return {
    id: node.id,
    type: node.type,
    widgets_values: node.type === REGIONAL
      ? regionalWidgetValues(
        inputs.wildcard_seed,
        inputs.wildcard_mode,
        inputs.wildcard_seed_after_generate,
      )
      : widgetValues(
        inputs.wildcard_seed,
        inputs.wildcard_mode,
        inputs.wildcard_seed_after_generate,
      ),
  };
}

function createSubgraphFixture(options = {}) {
  const nodes = options.nodes || [advancedNode(10)];
  const definition = {
    id: options.definitionId || "advanced-subgraph-definition",
    name: "Advanced seed subgraph",
    _nodes: nodes,
  };
  for (const node of nodes) {
    node.graph = definition;
  }
  const containers = (options.containerIds || [50]).map((id) => ({
    id,
    type: definition.id,
    subgraph: definition,
  }));
  const outputNodes = options.outputNodes || [{ id: 20, outputNode: true }];
  const rootGraph = {
    id: "root-graph",
    isRootGraph: true,
    _nodes: [...containers, ...outputNodes],
  };
  for (const node of rootGraph._nodes) {
    node.graph = rootGraph;
  }

  const randomValues = [...(options.randomValues || [41, 42, 43, 44])];
  const commits = [];
  const previousExecutions = [];
  let randomCalls = 0;
  let cloneCalls = 0;
  const graphHolder = {
    current: options.delayedRootGraph ? undefined : rootGraph,
  };
  const runtime = queueModule.createAdvancedQueueSeedRuntime({
    listNodes: () => graphHolder.current?._nodes || [],
    ...(options.delayedRootGraph
      ? { getRootGraph: () => graphHolder.current }
      : { rootGraph }),
    getNodeContract: queueSeedContract,
    isOutputNode: (node) => node?.outputNode === true,
    getSeed(node, contract) {
      return node.widgets.find((widget) => widget.name === contract.seedInputName)?.value;
    },
    updateSeed(node, seed, contract) {
      commits.push([definition.id, node.id, seed]);
      node.widgets.find((widget) => widget.name === contract.seedInputName).value = seed;
    },
    updatePreviousExecution(node, execution) {
      previousExecutions.push([definition.id, node.id, clone(execution)]);
      seedHistory.writePreviousWildcardExecution(node, execution);
    },
    clonePrompt(value) {
      cloneCalls += 1;
      return clone(value);
    },
    randomSeed() {
      randomCalls += 1;
      return randomValues.shift() ?? 0;
    },
  });
  return {
    commits,
    previousExecutions,
    containers,
    definition,
    nodes,
    outputNodes,
    rootGraph,
    runtime,
    setRootGraph(graph) {
      graphHolder.current = graph;
    },
    cloneCalls: () => cloneCalls,
    randomCalls: () => randomCalls,
  };
}

function subgraphPromptFor(fixture, options = {}) {
  const omittedContainerIds = new Set(
    (options.omittedContainerIds || []).map((value) => String(value)),
  );
  const output = {};
  for (const container of fixture.containers) {
    if (omittedContainerIds.has(String(container.id))) {
      continue;
    }
    for (const node of fixture.nodes) {
      output[`${container.id}:${node.id}`] = {
        class_type: node.type,
        inputs: seedPromptInputs(node),
      };
    }
  }

  const connections = options.connections || [{
    executionId: `${fixture.containers[0].id}:${fixture.nodes[0].id}`,
    targetId: fixture.outputNodes[0].id,
  }];
  for (const outputNode of fixture.outputNodes) {
    const inputs = {};
    connections
      .filter((connection) => String(connection.targetId) === String(outputNode.id))
      .forEach((connection, index) => {
        inputs[`source_${index}`] = [String(connection.executionId), 0];
      });
    output[String(outputNode.id)] = {
      class_type: "PreviewImage",
      inputs,
    };
  }

  return {
    output,
    workflow: {
      nodes: [
        ...fixture.containers.map((container) => ({
          id: container.id,
          type: fixture.definition.id,
          mode: omittedContainerIds.has(String(container.id)) ? 4 : 0,
          widgets_values: [],
        })),
        ...fixture.outputNodes.map((node) => ({
          id: node.id,
          type: "PreviewImage",
          widgets_values: [],
        })),
      ],
      definitions: {
        subgraphs: [{
          id: fixture.definition.id,
          name: fixture.definition.name,
          inputNode: { id: -10 },
          outputNode: { id: -20 },
          nodes: fixture.nodes.map(seedWorkflowNode),
        }],
      },
      links: [],
    },
  };
}

function queuedSeed(prompt, nodeId) {
  const promptNode = prompt.output[String(nodeId)];
  const contract = queueSeedContract({ type: promptNode.class_type });
  return promptNode.inputs[contract.seedInputName];
}

function workflowNode(prompt, nodeId) {
  const nodeIds = String(nodeId).split(":");
  const definitions = new Map(
    (prompt.workflow.definitions?.subgraphs || []).map((definition) => [
      String(definition.id),
      definition,
    ]),
  );
  let nodes = prompt.workflow.nodes;
  let workflowNodeValue = null;
  for (let index = 0; index < nodeIds.length; index += 1) {
    workflowNodeValue = nodes.find((node) => String(node.id) === nodeIds[index]) || null;
    if (!workflowNodeValue || index === nodeIds.length - 1) {
      break;
    }
    nodes = definitions.get(String(workflowNodeValue.type))?.nodes || [];
  }
  return workflowNodeValue;
}

function workflowSeed(prompt, nodeId) {
  const promptNode = prompt.output[String(nodeId)];
  const contract = queueSeedContract({ type: promptNode.class_type });
  return workflowNode(prompt, nodeId).widgets_values[contract.seedWidgetIndex];
}

function workflowMode(prompt, nodeId) {
  const promptNode = prompt.output[String(nodeId)];
  const contract = queueSeedContract({ type: promptNode.class_type });
  return workflowNode(prompt, nodeId).widgets_values[contract.modeWidgetIndex];
}

function workflowControl(prompt, nodeId) {
  const promptNode = prompt.output[String(nodeId)];
  const contract = queueSeedContract({ type: promptNode.class_type });
  return workflowNode(prompt, nodeId).widgets_values[contract.controlWidgetIndex];
}

function workflowPreviousExecution(prompt, nodeId) {
  return seedHistory.readPreviousWildcardExecution(workflowNode(prompt, nodeId));
}

function reservedNextSeed(prompt, nodeId) {
  return reservedSeedState(prompt, nodeId)?.next_seed;
}

function reservedSeedState(prompt, nodeId) {
  const raw = prompt.output[String(nodeId)].inputs[RESERVED_NEXT_SEED_INPUT];
  return raw == null ? undefined : JSON.parse(raw);
}

{
  const events = [];
  const clearResult = { cleared: true };
  const firstArg = { first: true };
  const secondArg = { second: true };
  const graph = {
    clear(...args) {
      events.push(["clear", this, args]);
      return clearResult;
    },
  };
  const owner = { graphOwner: true };
  const runtime = {
    clearGraphNodes() {
      events.push(["cleanup"]);
    },
  };
  const originalClear = graph.clear;
  const disposeCleanup = queueModule.installAdvancedQueueSeedGraphCleanup(graph, runtime);
  assert.equal(typeof disposeCleanup, "function");
  const installed = graph.clear;
  const disposeDuplicate = queueModule.installAdvancedQueueSeedGraphCleanup(graph, runtime);
  assert.equal(disposeDuplicate(), false);
  assert.equal(graph.clear, installed, "graph cleanup wrapper must install only once");
  assert.equal(graph.clear.call(owner, firstArg, secondArg), clearResult);
  assert.deepEqual(events, [
    ["clear", owner, [firstArg, secondArg]],
    ["cleanup"],
  ]);
  assert.equal(disposeCleanup(), true);
  assert.equal(graph.clear, originalClear);

  const clearError = new Error("graph clear failed");
  let failedCleanupCalls = 0;
  const failingGraph = {
    clear() {
      throw clearError;
    },
  };
  queueModule.installAdvancedQueueSeedGraphCleanup(failingGraph, {
    clearGraphNodes() {
      failedCleanupCalls += 1;
    },
  });
  assert.throws(() => failingGraph.clear(), (error) => error === clearError);
  assert.equal(
    failedCleanupCalls,
    0,
    "a failed original graph clear must preserve managed owners for the still-live graph",
  );
}

{
  const events = [];
  const configureResult = Symbol("configure-result");
  const removeResult = Symbol("remove-result");
  const serialized = { workflow: true };
  const configureTail = { extra: true };
  const removeArg = { reason: "test" };
  function AdvancedNodeType() {}
  AdvancedNodeType.prototype.onConfigure = function (...args) {
    events.push(["configure", this, args]);
    return configureResult;
  };
  AdvancedNodeType.prototype.onRemoved = function (...args) {
    events.push(["remove", this, args]);
    return removeResult;
  };
  const hooks = {
    captureAdvancedConfigure: (node, value) => events.push(["capture", node, value]),
    attachAdvancedQueueSeedNode: (node) => events.push(["attach", node]),
    scheduleHookAdvancedNode: (node) => events.push(["schedule", node]),
    disconnectAdvancedEditorWidthObserver: (node) => {
      events.push(["disconnect", node]);
      throw new Error("isolated observer cleanup failure");
    },
    detachAdvancedQueueSeedNode: (node) => events.push(["detach", node]),
  };
  assert.equal(
    nodeHooksModule.registerPromptStudioNodeHooks(
      AdvancedNodeType,
      { name: ADVANCED },
      hooks,
    ),
    true,
  );
  const node = new AdvancedNodeType();
  assert.equal(node.onConfigure(serialized, configureTail), configureResult);
  assert.equal(node.onRemoved(removeArg), removeResult);
  assert.deepEqual(events, [
    ["configure", node, [serialized, configureTail]],
    ["capture", node, serialized],
    ["attach", node],
    ["schedule", node],
    ["remove", node, [removeArg]],
    ["disconnect", node],
    ["detach", node],
  ]);
}

{
  const configureResult = Symbol("wildcard-configure-result");
  const serializeResult = Symbol("wildcard-serialize-result");
  const originalCallbackResult = Symbol("wildcard-callback-result");
  const originalCallbackCalls = [];
  function WildcardNodeType() {}
  WildcardNodeType.prototype.onConfigure = function (serialized) {
    for (const name of ["mode", "seed", "control_after_generate"]) {
      this.widgets.find((widget) => widget.name === name).value = serialized[name];
    }
    return configureResult;
  };
  WildcardNodeType.prototype.onSerialize = function () {
    return serializeResult;
  };
  const hooks = {
    hookWildcardSeedWidget: wildcardValuesModule.hookWildcardSeedWidget,
    attachAdvancedQueueSeedNode: () => false,
    detachAdvancedQueueSeedNode: () => false,
    syncWildcardSerialization: wildcardValuesModule.syncWildcardSerialization,
    applyWildcardExecutedInputs: wildcardValuesModule.applyWildcardExecutedInputs,
  };
  assert.equal(
    nodeHooksModule.registerPromptStudioNodeHooks(
      WildcardNodeType,
      { name: WILDCARD },
      hooks,
    ),
    true,
  );
  assert.equal(
    nodeHooksModule.registerPromptStudioNodeHooks(
      WildcardNodeType,
      { name: WILDCARD },
      hooks,
    ),
    false,
    "Wildcard prototype hook must install only once",
  );

  const seedWidget = {
    name: "seed",
    value: 0,
    options: { min: -10, max: 0, step: 0.5 },
    callback(value, ...args) {
      originalCallbackCalls.push([this, value, args]);
      return originalCallbackResult;
    },
  };
  const node = Object.assign(new WildcardNodeType(), wildcardNode(15, 0));
  node.widgets = node.widgets.map((widget) => widget.name === "seed" ? seedWidget : widget);
  node.onNodeCreated();
  assert.equal(seedWidget.options.min, 0);
  assert.equal(seedWidget.options.max, Number.MAX_SAFE_INTEGER);
  assert.equal(seedWidget.options.step, 1);
  const wrappedCallback = seedWidget.callback;

  const unsafeSeed = Number.MAX_SAFE_INTEGER + 1;
  assert.equal(node.onConfigure({
    mode: "reproduce",
    seed: unsafeSeed,
    control_after_generate: "increment",
  }), configureResult);
  assert.equal(seedWidget.value, unsafeSeed, "configure must preserve a loaded unsafe seed");
  assert.equal(seedWidget.callback, wrappedCallback, "configure must not stack the callback guard");
  assert.equal(node.widgets.find((widget) => widget.name === "mode").value, "재현");
  assert.equal(
    node.widgets.find((widget) => widget.name === "control_after_generate").value,
    "fixed",
    "native control_after_generate owns standalone wildcard seed advancement",
  );
  const reproduceSerialized = { widgets_values: node.widgets.map((widget) => widget.value) };
  assert.equal(node.onSerialize(reproduceSerialized), serializeResult);
  assert.equal(reproduceSerialized.widgets_values[2], "재현");
  assert.equal(reproduceSerialized.widgets_values[4], "fixed");

  for (const invalid of ["1.5", "1e3", "9007199254740991.1"]) {
    seedWidget.value = invalid;
    assert.equal(seedWidget.callback.call(node, invalid), undefined);
    assert.equal(seedWidget.value, unsafeSeed, "invalid native edit must restore the configured value");
  }
  assert.deepEqual(originalCallbackCalls, [], "invalid native edits must not call the original callback");

  seedWidget.value = "42";
  assert.equal(seedWidget.callback.call(node, "42", "tail"), originalCallbackResult);
  assert.equal(seedWidget.value, 42);
  assert.deepEqual(originalCallbackCalls, [[node, 42, ["tail"]]]);

  assert.equal(node.onConfigure({
    mode: "일반",
    seed: unsafeSeed,
    control_after_generate: "randomize",
  }), configureResult);
  assert.equal(seedWidget.callback, wrappedCallback, "reconfigure must keep one callback guard");
  seedWidget.value = "2e3";
  seedWidget.callback.call(node, "2e3");
  assert.equal(seedWidget.value, unsafeSeed);
  assert.equal(originalCallbackCalls.length, 1);

  node.onExecuted({
    wildcard: [{ populated_text: "resolved from file", mode: "일반", seed: 999 }],
  });
  assert.equal(
    node.widgets.find((widget) => widget.name === "populated_text").value,
    "resolved from file",
  );
  assert.equal(node.widgets.find((widget) => widget.name === "mode").value, "일반");
  assert.equal(seedWidget.value, unsafeSeed, "backend UI payload must not replace the native seed");

  assert.equal(node.onConfigure({
    mode: "sequential",
    seed: unsafeSeed,
    control_after_generate: "increment",
  }), configureResult);
  assert.equal(node.widgets.find((widget) => widget.name === "mode").value, "순차");
  const serialized = { widgets_values: node.widgets.map((widget) => widget.value) };
  assert.equal(node.onSerialize(serialized), serializeResult);
  assert.equal(serialized.widgets_values[2], "순차");
  assert.equal(serialized.widgets_values[4], "fixed");
  assert.equal(node.onRemoved(), undefined);
}

{
  const node = wildcardNode(15, 7);
  const fixture = createFixture({ nodes: [node] });
  assert.equal(
    fixture.runtime.attachNode(node),
    false,
    "standalone EasyUseAnimaWildcard must remain outside the Prompt Studio queue runtime",
  );
  assert.equal(fixture.runtime.trackedStateCount(), 0);
}

{
  for (const originalError of [
    new Error("original removal failure"),
    null,
    undefined,
    0,
    false,
  ]) {
    const events = [];
    function FailingAdvancedNodeType() {}
    FailingAdvancedNodeType.prototype.onRemoved = function () {
      events.push(["remove", this]);
      throw originalError;
    };
    nodeHooksModule.registerPromptStudioNodeHooks(
      FailingAdvancedNodeType,
      { name: ADVANCED_V2 },
      {
        captureAdvancedConfigure() {},
        scheduleHookAdvancedNode() {},
        disconnectAdvancedEditorWidthObserver(node) {
          events.push(["disconnect", node]);
          throw new Error("secondary disconnect failure");
        },
        detachAdvancedQueueSeedNode(node) {
          events.push(["detach", node]);
          throw new Error("secondary state cleanup failure");
        },
      },
    );
    const node = new FailingAdvancedNodeType();
    const notThrown = Symbol("not-thrown");
    let caught = notThrown;
    try {
      node.onRemoved();
    } catch (error) {
      caught = error;
    }
    assert.notEqual(caught, notThrown, "the original removal throw must not be swallowed");
    assert.equal(caught, originalError, "cleanup must preserve the original throw identity");
    assert.deepEqual(events, [
      ["remove", node],
      ["disconnect", node],
      ["detach", node],
    ]);
  }
}

{
  const nodes = [advancedNode(10, ADVANCED, 7), advancedNode(11, ADVANCED_V2, 27)];
  const fixture = createFixture({ nodes });
  const prompt = promptFor(nodes);
  const original = clone(prompt);
  const transaction = fixture.runtime.preparePrompt(prompt);

  assert.ok(transaction);
  assert.notEqual(transaction.prompt, prompt);
  assert.deepEqual(prompt, original, "queue preparation must not mutate the caller payload");
  assert.equal(nodes[0].widgets[1].value, 7, "reservation must not mutate live state");
  assert.equal(nodes[1].widgets[1].value, 27, "V2 live state must remain unchanged");
  assert.equal(queuedSeed(transaction.prompt, 10), 7);
  assert.equal(workflowSeed(transaction.prompt, 10), 7);
  assert.equal(reservedNextSeed(transaction.prompt, 10), 8);
  assert.equal(queuedSeed(transaction.prompt, 11), 27);
  assert.equal(workflowSeed(transaction.prompt, 11), 27);
  assert.equal(reservedNextSeed(transaction.prompt, 11), 28);
  assert.deepEqual(transaction.prompt.extra_data, { untouched: true });
}

{
  const fixture = createFixture();
  const calls = [];
  const gates = [deferred(), deferred(), deferred()];
  const wrapped = fixture.runtime.wrapQueuePrompt(function (...args) {
    calls.push({ owner: this, args });
    return gates[calls.length - 1].promise;
  });
  const owner = { name: "api-owner" };
  const options = { partialExecutionTargets: [20], previewMethod: "latent2rgb" };
  const tail = { preserve: true };
  const prompt = promptFor(fixture.nodes, { consumers: [{ id: 20, source: 10 }] });
  const original = clone(prompt);

  const pending = [
    wrapped.call(owner, -1, prompt, options, tail),
    wrapped.call(owner, -1, prompt, options, tail),
    wrapped.call(owner, -1, prompt, options, tail),
  ];
  assert.deepEqual(calls.map((call) => queuedSeed(call.args[1], 10)), [7, 8, 9]);
  assert.deepEqual(calls.map((call) => workflowSeed(call.args[1], 10)), [7, 8, 9]);
  assert.deepEqual(calls.map((call) => reservedNextSeed(call.args[1], 10)), [8, 9, 10]);
  assert.deepEqual(prompt, original, "rapid reservations must keep the caller payload immutable");
  assert.equal(fixture.nodes[0].widgets[1].value, 7, "live seed changes only after acceptance");
  for (const call of calls) {
    assert.equal(call.owner, owner);
    assert.equal(call.args.length, 4);
    assert.equal(call.args[0], -1);
    assert.equal(call.args[2], options, "partial execution options identity must survive");
    assert.equal(call.args[3], tail, "tail argument identity must survive");
  }

  gates[0].resolve({ prompt_id: "one", node_errors: {} });
  gates[1].resolve({ prompt_id: "two", node_errors: {} });
  gates[2].resolve({ prompt_id: "three", node_errors: {} });
  const results = await Promise.all(pending);
  assert.deepEqual(results.map((result) => result.prompt_id), ["one", "two", "three"]);
  assert.equal(fixture.nodes[0].widgets[1].value, 10);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], 8), false);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], 10), true);
}

{
  // ComfyUI v0.27 app.queuePrompt calls api.queuePrompt once per batch after a
  // fresh graphToPrompt. The accepted commit must feed the next serialization.
  const fixture = createFixture();
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt, options) => {
    queued.push({ seed: queuedSeed(prompt, 10), options });
    return { prompt_id: `batch-${queued.length}`, node_errors: {} };
  });
  const options = { partialExecutionTargets: [20] };
  for (let index = 0; index < 3; index += 1) {
    const prompt = promptFor(fixture.nodes, { consumers: [{ id: 20, source: 10 }] });
    await wrapped(0, prompt, options);
  }
  assert.deepEqual(queued.map((entry) => entry.seed), [7, 8, 9]);
  assert.equal(fixture.nodes[0].widgets[1].value, 10);
  assert.equal(queued.every((entry) => entry.options === options), true);
}

for (const [surface, createNode] of [
  ["Advanced", () => advancedNode(10, ADVANCED, 17)],
  ["Regional", () => regionalNode(30, 17)],
]) {
  const node = createNode();
  const seedWidget = node.widgets.find((widget) => widget.name === "wildcard_seed");
  const fixture = createFixture({ nodes: [node] });
  const popupPublishes = [];
  const popupInput = seedInputFixture("17");
  seedContract.bindWildcardSeedInput(
    popupInput,
    () => seedWidget.value,
    (seed) => {
      popupPublishes.push(seed);
      seedWidget.value = seed;
    },
  );
  popupInput.dispatch("blur");
  assert.equal(seedWidget.value, 17, `${surface} untouched close must not invent a seed advance`);
  assert.deepEqual(popupPublishes, [], `${surface} untouched close must not publish`);

  const rejected = fixture.runtime.wrapQueuePrompt(() => ({ node_errors: {} }));
  await rejected(0, promptFor([node]));
  popupInput.dispatch("blur");
  assert.equal(seedWidget.value, 17, `${surface} rejected queue must keep canonical seed`);
  assert.deepEqual(popupPublishes, [], `${surface} rejected queue must not trigger popup publish`);

  let acceptedCount = 0;
  const accepted = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: `${surface.toLowerCase()}-popup-open-${++acceptedCount}`,
    node_errors: {},
  }));
  await Promise.all([
    accepted(0, promptFor([node])),
    accepted(0, promptFor([node])),
    accepted(0, promptFor([node])),
  ]);
  assert.equal(seedWidget.value, 20, `${surface} three rapid queues must advance canonical seed`);
  assert.equal(popupInput.value, "17", `${surface} open popup starts with its prior snapshot`);

  popupInput.dispatch("blur");
  assert.equal(popupInput.value, "20", `${surface} untouched blur must refresh from canonical seed`);
  assert.equal(seedWidget.value, 20, `${surface} untouched blur must not roll back canonical seed`);
  assert.deepEqual(popupPublishes, [], `${surface} untouched popup must not publish a stale seed`);

  popupInput.value = "23";
  popupInput.dispatch("input");
  popupInput.dispatch("change");
  popupInput.dispatch("blur");
  assert.equal(seedWidget.value, 23, `${surface} real popup edit must update canonical seed`);
  assert.deepEqual(popupPublishes, [23], `${surface} real edit must publish exactly once`);
}

{
  const node = advancedNode(10, ADVANCED, 7);
  node.widgets[0].value = "일반 채우기";
  node.widgets[2].value = "randomize";
  const fixture = createFixture({ nodes: [node], randomValues: [41, 42, 43] });
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queued.push({
      current: queuedSeed(prompt, 10),
      next: reservedNextSeed(prompt, 10),
    });
    return { prompt_id: `random-${queued.length}`, node_errors: {} };
  });
  await Promise.all([
    wrapped(0, promptFor([node])),
    wrapped(0, promptFor([node])),
    wrapped(0, promptFor([node])),
  ]);
  assert.deepEqual(queued, [
    { current: 7, next: 41 },
    { current: 41, next: 42 },
    { current: 42, next: 43 },
  ]);
  assert.equal(node.widgets[1].value, 43);
  assert.deepEqual(seedHistory.readPreviousWildcardExecution(node), {
    version: 1,
    seed: 42,
    mode: "populate",
  });
  assert.equal(fixture.randomCalls(), 3);
}

{
  const fixed = advancedNode(10, ADVANCED, 7);
  fixed.widgets[0].value = "고정";
  fixed.widgets[2].value = "randomize";
  const fixture = createFixture({ nodes: [fixed], randomValues: [41, 42, 43] });
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queued.push([queuedSeed(prompt, 10), reservedNextSeed(prompt, 10)]);
    return { prompt_id: `fixed-random-${queued.length}`, node_errors: {} };
  });
  await Promise.all([
    wrapped(0, promptFor([fixed])),
    wrapped(0, promptFor([fixed])),
    wrapped(0, promptFor([fixed])),
  ]);
  assert.deepEqual(queued, [[7, 7], [7, 7], [7, 7]]);
  assert.equal(fixed.widgets[1].value, 7);
  assert.equal(fixture.randomCalls(), 0);
}

{
  const decrement = advancedNode(10, ADVANCED, 0);
  decrement.widgets[0].value = "일반 채우기";
  decrement.widgets[2].value = "decrement";
  const fixture = createFixture({ nodes: [decrement] });
  const transaction = fixture.runtime.preparePrompt(promptFor([decrement]));
  assert.ok(transaction);
  assert.equal(queuedSeed(transaction.prompt, 10), 0);
  assert.equal(reservedNextSeed(transaction.prompt, 10), 0);
}

{
  const increment = advancedNode(10, ADVANCED, Number.MAX_SAFE_INTEGER);
  const fixture = createFixture({ nodes: [increment] });
  const transaction = fixture.runtime.preparePrompt(promptFor([increment]));
  assert.ok(transaction);
  assert.equal(queuedSeed(transaction.prompt, 10), Number.MAX_SAFE_INTEGER);
  assert.equal(reservedNextSeed(transaction.prompt, 10), 0);
}

{
  const sequentialFixed = advancedNode(10, ADVANCED, 7);
  sequentialFixed.widgets[2].value = "fixed";
  const fixture = createFixture({ nodes: [sequentialFixed] });
  const transaction = fixture.runtime.preparePrompt(promptFor([sequentialFixed]));
  assert.ok(transaction);
  assert.deepEqual(reservedSeedState(transaction.prompt, 10), {
    version: 1,
    current_seed: 7,
    next_seed: 7,
    mode: "sequential",
    control: "fixed",
  });
}

for (const [surface, makeNode] of [
  ["advanced", () => advancedNode(10, ADVANCED, 7)],
  ["regional", () => regionalNode(10, 7)],
]) {
  for (const [mode, normalizedMode] of [
    ["일반", "populate"],
    ["순차", "sequential"],
  ]) {
    for (const [control, expectedNext] of [
      ["fixed", 7],
      ["randomize", 41],
      ["increment", 8],
    ]) {
      const node = makeNode();
      node.widgets[0].value = mode;
      node.widgets[2].value = control;
      const fixture = createFixture({ nodes: [node], randomValues: [41] });
      let reserved = null;
      let savedPrompt = null;
      const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
        reserved = reservedSeedState(prompt, 10);
        savedPrompt = prompt;
        return { prompt_id: `${surface}-${mode}-${control}`, node_errors: {} };
      });

      await wrapped(0, promptFor([node]));

      assert.deepEqual(reserved, {
        version: 1,
        current_seed: 7,
        next_seed: expectedNext,
        mode: normalizedMode,
        control,
      });
      assert.equal(workflowMode(savedPrompt, 10), mode);
      assert.equal(workflowSeed(savedPrompt, 10), 7);
      assert.equal(workflowControl(savedPrompt, 10), "fixed");
      assert.deepEqual(workflowPreviousExecution(savedPrompt, 10), {
        version: 1,
        seed: 7,
        mode: normalizedMode,
      });
      assert.equal(
        node.widgets[1].value,
        expectedNext,
        `${surface} ${mode} + ${control} committed the wrong next seed`,
      );
      assert.deepEqual(seedHistory.readPreviousWildcardExecution(node), {
        version: 1,
        seed: 7,
        mode: normalizedMode,
      });
      assert.equal(fixture.randomCalls(), control === "randomize" ? 1 : 0);
    }
  }
}

{
  const node = advancedNode(10, ADVANCED, 7);
  node.widgets[0].value = "순차";
  node.widgets[2].value = "randomize";
  const fixture = createFixture({ nodes: [node], randomValues: [41, 42] });
  let attempts = 0;
  let retried = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    attempts += 1;
    if (attempts === 1) {
      return Promise.reject(new Error("random queue rejected"));
    }
    retried = reservedSeedState(prompt, 10);
    return { prompt_id: "random-retry", node_errors: {} };
  });

  await assert.rejects(wrapped(0, promptFor([node])), /random queue rejected/);
  assert.equal(node.widgets[1].value, 7, "a rejected random seed must not commit");
  assert.equal(
    seedHistory.readPreviousWildcardExecution(node),
    null,
    "a rejected queue must not publish a previous execution seed",
  );
  await wrapped(0, promptFor([node]));
  assert.deepEqual(retried, {
    version: 1,
    current_seed: 7,
    next_seed: 42,
    mode: "sequential",
    control: "randomize",
  });
  assert.equal(node.widgets[1].value, 42);
  assert.deepEqual(seedHistory.readPreviousWildcardExecution(node), {
    version: 1,
    seed: 7,
    mode: "sequential",
  });
  assert.equal(fixture.randomCalls(), 2);
}

for (const linkedInput of ["wildcard_mode", "wildcard_seed_after_generate"]) {
  const node = advancedNode(10, ADVANCED, 7);
  const fixture = createFixture({ nodes: [node] });
  const prompt = promptFor([node]);
  prompt.output["10"].inputs[linkedInput] = [99, 0];
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: `linked-${linkedInput}`, node_errors: {} };
  });

  await wrapped(0, prompt);

  assert.equal(received, prompt, `${linkedInput} link must remain backend-owned`);
  assert.deepEqual(prompt.output["10"].inputs[linkedInput], [99, 0]);
  assert.equal(fixture.cloneCalls(), 0);
  assert.equal(node.widgets[1].value, 7);
}

{
  const randomize = advancedNode(10, ADVANCED, 7);
  randomize.widgets[0].value = "일반 채우기";
  randomize.widgets[2].value = "randomize";
  const fixture = createFixture({
    nodes: [randomize],
    randomValues: [Number.MAX_SAFE_INTEGER],
  });
  const transaction = fixture.runtime.preparePrompt(promptFor([randomize]));
  assert.ok(transaction);
  assert.equal(reservedNextSeed(transaction.prompt, 10), Number.MAX_SAFE_INTEGER);
  assert.equal(fixture.randomCalls(), 1);
}

{
  const fixture = createFixture();
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "unsafe-pass-through", node_errors: {} };
  });
  await wrapped(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 8);
  fixture.nodes[0].widgets[1].value = Number.MAX_SAFE_INTEGER + 1;
  const prompt = promptFor(fixture.nodes);
  await wrapped(0, prompt);
  assert.equal(received, prompt, "unsafe 64-bit seeds must not be rounded in a queue clone");
  assert.equal(fixture.nodes[0].widgets[1].value, Number.MAX_SAFE_INTEGER + 1);
  assert.equal(fixture.cloneCalls(), 1, "the unsafe transition itself must not clone");
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], Number.MAX_SAFE_INTEGER),
    true,
    "an old safe-state guard must not block the backend pass-through path",
  );
}

{
  const node = advancedNode(10, ADVANCED, 7);
  const fixture = createFixture({ nodes: [node] });
  const oldSafeResponse = deferred();
  let calls = 0;
  let unsafeReceived = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    calls += 1;
    if (calls === 1) {
      return oldSafeResponse.promise;
    }
    unsafeReceived = nextPrompt;
    return { prompt_id: "unsafe-new", node_errors: {} };
  });

  const oldSafeQueue = wrapped(0, promptFor([node]));
  node.widgets[1].value = Number.MAX_SAFE_INTEGER + 1;
  const unsafePrompt = promptFor([node]);
  await wrapped(0, unsafePrompt);
  assert.equal(unsafeReceived, unsafePrompt, "unsafe prompt must bypass the managed clone");

  oldSafeResponse.resolve({ prompt_id: "safe-old", node_errors: {} });
  await oldSafeQueue;
  assert.equal(
    node.widgets[1].value,
    Number.MAX_SAFE_INTEGER + 1,
    "a late accepted safe response must not overwrite the unsafe live seed",
  );
  assert.deepEqual(fixture.commits, [], "retired safe reservations must lose publish authority");
  assert.equal(fixture.runtime.trackedStateCount(), 0);

  const unsafeBackendNext = 0;
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(node, unsafeBackendNext),
    true,
    "the unsafe backend next seed must not be filtered by retired safe state",
  );
  node.widgets[1].value = unsafeBackendNext;
  assert.equal(node.widgets[1].value, 0);
}

{
  const reproduce = advancedNode(10, ADVANCED_V2, 7);
  reproduce.widgets[0].value = "재현";
  reproduce.widgets[2].value = "randomize";
  const fixture = createFixture({ nodes: [reproduce], randomValues: [41] });
  const prompt = promptFor([reproduce]);
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "reproduce", node_errors: {} };
  });
  await wrapped(0, prompt);
  assert.notEqual(received, prompt, "legacy reproduce must use the managed General contract");
  assert.deepEqual(reservedSeedState(received, 10), {
    version: 1,
    current_seed: 7,
    next_seed: 7,
    mode: "populate",
    control: "fixed",
  });
  assert.equal(reproduce.widgets[1].value, 7);
  assert.equal(fixture.randomCalls(), 0);
}

{
  const fixture = createFixture();
  const failure = new Error("queue rejected");
  let attempts = 0;
  let retriedSeed = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    attempts += 1;
    if (attempts === 1) {
      return Promise.reject(failure);
    }
    retriedSeed = queuedSeed(prompt, 10);
    return { prompt_id: "retry", node_errors: {} };
  });
  await assert.rejects(wrapped(0, promptFor(fixture.nodes)), (error) => error === failure);
  assert.equal(fixture.nodes[0].widgets[1].value, 7, "rejection must not advance live state");
  await wrapped(0, promptFor(fixture.nodes));
  assert.equal(retriedSeed, 7, "a rejected reservation must be reusable");
  assert.equal(fixture.nodes[0].widgets[1].value, 8);
}

{
  const fixture = createFixture();
  const calls = [];
  const gates = [deferred(), deferred(), deferred()];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    calls.push(queuedSeed(prompt, 10));
    return gates[calls.length - 1].promise;
  });
  const pending = [
    wrapped(0, promptFor(fixture.nodes)),
    wrapped(0, promptFor(fixture.nodes)),
    wrapped(0, promptFor(fixture.nodes)),
  ];
  gates[1].resolve({ prompt_id: "second", node_errors: {} });
  await pending[1];
  assert.equal(fixture.nodes[0].widgets[1].value, 7, "later results wait for FIFO settlement");
  gates[0].resolve({ prompt_id: "   ", node_errors: {} });
  await pending[0];
  assert.equal(fixture.nodes[0].widgets[1].value, 9, "blank prompt ids reject only their reservation");
  gates[2].resolve({ prompt_id: "third", node_errors: {} });
  await pending[2];
  assert.deepEqual(calls, [7, 8, 9]);
  assert.equal(fixture.nodes[0].widgets[1].value, 10);
}

{
  const fixture = createFixture({ updateFailures: 1 });
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queued.push(queuedSeed(prompt, 10));
    return { prompt_id: `publish-${queued.length}`, node_errors: {} };
  });
  await wrapped(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 7, "failed publication leaves the widget untouched");
  await wrapped(0, promptFor(fixture.nodes));
  assert.deepEqual(queued, [7, 8], "a failed widget refresh must not reuse an accepted seed");
  assert.equal(fixture.nodes[0].widgets[1].value, 9);
  assert.deepEqual(fixture.commits, [[10, 8], [10, 9]]);
}

{
  const fixture = createFixture();
  const accepted = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "accepted-before-manual-edit", node_errors: {},
  }));
  await accepted(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 8);
  fixture.nodes[0].widgets[1].value = 100;
  const rejected = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "", node_errors: {},
  }));
  await rejected(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 100);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], 8),
    false,
    "a rejected queue after a manual edit must not reopen an older executed seed",
  );
  await accepted(0, promptFor(fixture.nodes));
  assert.equal(fixture.nodes[0].widgets[1].value, 101);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(fixture.nodes[0], 101), true);
}

{
  const nodes = [advancedNode(10, ADVANCED, 7), advancedNode(11, ADVANCED_V2, 30)];
  const fixture = createFixture({ nodes });
  const prompt = promptFor(nodes, { consumers: [{ id: 20, source: 10 }] });
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "connected-only", node_errors: {} };
  });
  await wrapped(0, prompt);
  assert.equal(nodes[0].widgets[1].value, 8);
  assert.equal(nodes[1].widgets[1].value, 30, "disconnected Advanced nodes must not reserve seeds");
  assert.equal(reservedNextSeed(received, 10), 8);
  assert.equal(reservedSeedState(received, 11), undefined);
}

{
  const nodes = [advancedNode(10, ADVANCED, 7), advancedNode(11, ADVANCED_V2, 30)];
  const fixture = createSubgraphFixture({ nodes });
  const prompt = subgraphPromptFor(fixture, {
    connections: [{ executionId: "50:10", targetId: 20 }],
  });
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "subgraph-connected-only", node_errors: {} };
  });
  await wrapped(0, prompt);

  assert.notEqual(received, prompt);
  assert.equal(queuedSeed(received, "50:10"), 7);
  assert.equal(workflowSeed(received, "50:10"), 7);
  assert.deepEqual(reservedSeedState(received, "50:10"), {
    version: 1,
    current_seed: 7,
    next_seed: 8,
    mode: "sequential",
    control: "increment",
  });
  assert.equal(nodes[0].widgets[1].value, 8);
  assert.equal(
    nodes[1].widgets[1].value,
    30,
    "a disconnected Advanced V2 node in the same definition must not reserve",
  );
  assert.equal(reservedSeedState(received, "50:11"), undefined);
  assert.equal(workflowSeed(received, "50:11"), 30);
  assert.equal(reservedSeedState(prompt, "50:10"), undefined, "the caller prompt stays immutable");
  assert.equal(workflowSeed(prompt, "50:10"), 7);
}

{
  const node = advancedNode(10, ADVANCED_V2, 7);
  const fixture = createSubgraphFixture({
    nodes: [node],
    delayedRootGraph: true,
  });
  fixture.setRootGraph(fixture.rootGraph);

  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    queued.push({
      current: queuedSeed(nextPrompt, "50:10"),
      workflow: workflowSeed(nextPrompt, "50:10"),
      next: reservedNextSeed(nextPrompt, "50:10"),
    });
    return {
      prompt_id: `delayed-root-graph-rapid-${queued.length}`,
      node_errors: {},
    };
  });
  await Promise.all([
    wrapped(0, subgraphPromptFor(fixture)),
    wrapped(0, subgraphPromptFor(fixture)),
    wrapped(0, subgraphPromptFor(fixture)),
  ]);

  assert.deepEqual(queued, [
    { current: 7, workflow: 7, next: 8 },
    { current: 8, workflow: 8, next: 9 },
    { current: 9, workflow: 9, next: 10 },
  ]);
  assert.equal(node.widgets[1].value, 10);
  assert.equal(fixture.cloneCalls(), 3);
}

{
  const node = advancedNode(10, ADVANCED_V2, 7);
  node.widgets[0].value = "일반 채우기";
  node.widgets[2].value = "randomize";
  const fixture = createSubgraphFixture({ nodes: [node], randomValues: [41, 42, 43] });
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queued.push({
      current: queuedSeed(prompt, "50:10"),
      workflow: workflowSeed(prompt, "50:10"),
      next: reservedNextSeed(prompt, "50:10"),
    });
    return { prompt_id: `subgraph-rapid-${queued.length}`, node_errors: {} };
  });
  await Promise.all([
    wrapped(0, subgraphPromptFor(fixture)),
    wrapped(0, subgraphPromptFor(fixture)),
    wrapped(0, subgraphPromptFor(fixture)),
  ]);
  assert.deepEqual(queued, [
    { current: 7, workflow: 7, next: 41 },
    { current: 41, workflow: 41, next: 42 },
    { current: 42, workflow: 42, next: 43 },
  ]);
  assert.equal(node.widgets[1].value, 43);
  assert.equal(fixture.randomCalls(), 3);
}

{
  const node = advancedNode(10, ADVANCED, 7);
  node.widgets[0].value = "일반 채우기";
  node.widgets[2].value = "randomize";
  const fixture = createSubgraphFixture({
    nodes: [node],
    containerIds: [50, 51],
    randomValues: [41, 42],
  });
  const prompt = subgraphPromptFor(fixture, {
    connections: [
      { executionId: "50:10", targetId: 20 },
      { executionId: "51:10", targetId: 20 },
    ],
  });
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "shared-subgraph-definition", node_errors: {} };
  });
  await wrapped(0, prompt);

  for (const executionId of ["50:10", "51:10"]) {
    assert.equal(queuedSeed(received, executionId), 7);
    assert.equal(reservedNextSeed(received, executionId), 41);
  }
  assert.equal(workflowSeed(received, "50:10"), 7);
  assert.equal(node.widgets[1].value, 41);
  assert.equal(fixture.randomCalls(), 1);
  assert.deepEqual(fixture.commits, [[fixture.definition.id, 10, 41]]);
}

{
  const node = advancedNode(10, ADVANCED_V2, 7);
  const fixture = createSubgraphFixture({
    nodes: [node],
    definitionId: "inner-advanced-definition",
    containerIds: [60],
  });
  const innerDefinition = fixture.definition;
  const innerContainer = {
    id: 50,
    type: innerDefinition.id,
    subgraph: innerDefinition,
  };
  const outerDefinition = {
    id: "outer-advanced-definition",
    name: "Outer Advanced seed subgraph",
    _nodes: [innerContainer],
  };
  innerContainer.graph = outerDefinition;
  fixture.containers[0].type = outerDefinition.id;
  fixture.containers[0].subgraph = outerDefinition;
  const prompt = {
    output: {
      "60:50:10": {
        class_type: node.type,
        inputs: seedPromptInputs(node),
      },
      20: {
        class_type: "PreviewImage",
        inputs: { source: ["60:50:10", 0] },
      },
    },
    workflow: {
      nodes: [
        { id: 60, type: outerDefinition.id, widgets_values: [] },
        { id: 20, type: "PreviewImage", widgets_values: [] },
      ],
      definitions: {
        subgraphs: [
          {
            id: outerDefinition.id,
            name: outerDefinition.name,
            inputNode: { id: -10 },
            outputNode: { id: -20 },
            nodes: [{ id: 50, type: innerDefinition.id, widgets_values: [] }],
          },
          {
            id: innerDefinition.id,
            name: innerDefinition.name,
            inputNode: { id: -10 },
            outputNode: { id: -20 },
            nodes: [seedWorkflowNode(node)],
          },
        ],
      },
      links: [],
    },
  };
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "nested-subgraph", node_errors: {} };
  });
  await wrapped(0, prompt);

  assert.equal(queuedSeed(received, "60:50:10"), 7);
  assert.equal(workflowSeed(received, "60:50:10"), 7);
  assert.equal(reservedNextSeed(received, "60:50:10"), 8);
  assert.equal(node.widgets[1].value, 8);
}

{
  const node = advancedNode(10, ADVANCED, 7);
  node.widgets[0].value = "일반 채우기";
  node.widgets[2].value = "randomize";
  const fixture = createSubgraphFixture({ nodes: [node], randomValues: [41] });
  const prompt = subgraphPromptFor(fixture, {
    omittedContainerIds: [50],
    connections: [],
  });
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "bypassed-subgraph", node_errors: {} };
  });
  await wrapped(0, prompt);

  assert.equal(received, prompt, "a bypassed subgraph stays on the unmanaged queue path");
  assert.equal(fixture.cloneCalls(), 0);
  assert.equal(fixture.randomCalls(), 0);
  assert.deepEqual(fixture.commits, []);
  assert.equal(node.widgets[1].value, 7);
}

{
  const node = advancedNode(10, ADVANCED, 7);
  node.widgets[0].value = "일반 채우기";
  node.widgets[2].value = "randomize";
  const fixture = createSubgraphFixture({
    nodes: [node],
    containerIds: [50, 51],
    randomValues: [41],
  });
  const prompt = subgraphPromptFor(fixture, {
    connections: [
      { executionId: "50:10", targetId: 20 },
      { executionId: "51:10", targetId: 20 },
    ],
  });
  prompt.output["51:10"].inputs.wildcard_seed = 99;
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "promoted-seed-mismatch", node_errors: {} };
  });
  await wrapped(0, prompt);

  assert.equal(received, prompt, "different per-instance seeds cannot share one workflow value");
  assert.equal(fixture.cloneCalls(), 0);
  assert.equal(fixture.randomCalls(), 0);
  assert.deepEqual(fixture.commits, []);
  assert.equal(node.widgets[1].value, 7);
}

{
  const nodes = [advancedNode(10, ADVANCED, 7)];
  const fixture = createFixture({
    nodes,
    outputNodes: [
      { id: 20, outputNode: true },
      { id: 21, outputNode: true },
    ],
  });
  const prompt = promptFor(nodes, {
    consumers: [
      { id: 20, source: 10 },
      { id: 21, source: 10 },
    ],
  });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "one-valid-output",
    node_errors: {
      99: { errors: ["bad input"], dependent_outputs: ["20"] },
    },
  }));
  await wrapped(0, prompt);
  assert.equal(nodes[0].widgets[1].value, 8, "a shared upstream seed commits when one output executes");
}

{
  const nodes = [advancedNode(10, ADVANCED, 7), advancedNode(11, ADVANCED_V2, 30)];
  const fixture = createFixture({ nodes });
  const prompt = promptFor(nodes, {
    consumers: [
      { id: 20, source: 10 },
      { id: 21, source: 11 },
    ],
  });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "partial-valid",
    node_errors: {
      99: { errors: ["bad input"], dependent_outputs: ["20"] },
    },
  }));
  await wrapped(0, prompt);
  assert.equal(nodes[0].widgets[1].value, 7, "errored branch must not commit");
  assert.equal(nodes[1].widgets[1].value, 31, "unrelated valid branch must commit");
}

{
  const nodes = [advancedNode(10, ADVANCED, 7), advancedNode(11, ADVANCED_V2, 30)];
  const fixture = createFixture({ nodes });
  const prompt = promptFor(nodes, {
    consumers: [
      { id: 20, source: 10 },
      { id: 21, source: 11 },
    ],
  });
  let received = null;
  const options = { partialExecutionTargets: ["20"], previewMethod: "none" };
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt, nextOptions) => {
    received = nextPrompt;
    assert.equal(nextOptions, options);
    return { prompt_id: "partial-target", node_errors: {} };
  });
  await wrapped(0, prompt, options);
  assert.equal(queuedSeed(received, 10), 7);
  assert.equal(workflowSeed(received, 10), 7);
  assert.equal(queuedSeed(received, 11), 30, "unselected branch output must remain unchanged");
  assert.equal(workflowSeed(received, 11), 30, "unselected workflow metadata must remain unchanged");
  assert.equal(nodes[0].widgets[1].value, 8);
  assert.equal(nodes[1].widgets[1].value, 30);
}

{
  const fixture = createFixture();
  const prompt = promptFor(fixture.nodes);
  for (const options of [
    { partialExecutionTargets: [] },
    { partialExecutionTargets: "20" },
    { partialExecutionTargets: [999] },
  ]) {
    let received = null;
    const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
      received = nextPrompt;
      return { prompt_id: "empty-partial", node_errors: {} };
    });
    await wrapped(0, prompt, options);
    assert.equal(received, prompt, "empty or invalid partial execution must pass through");
  }
  assert.equal(fixture.nodes[0].widgets[1].value, 7);
  assert.equal(fixture.cloneCalls(), 0);
}

{
  const fixture = createFixture();
  const gate = deferred();
  const node = fixture.nodes[0];
  const wrapped = fixture.runtime.wrapQueuePrompt(() => gate.promise);
  const pending = wrapped(0, promptFor([node]));
  assert.equal(fixture.runtime.trackedStateCount(), 1);
  assert.equal(
    fixture.runtime.attachNode(node),
    true,
    "reconfiguring the same object must attach a new lifecycle epoch",
  );
  assert.equal(fixture.runtime.trackedStateCount(), 2);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(node, 8),
    false,
    "the new same-object epoch must block the old epoch's executed seed",
  );
  gate.resolve({ prompt_id: "same-object-old-epoch", node_errors: {} });
  await pending;
  assert.deepEqual(fixture.commits, []);
  assert.equal(node.widgets[1].value, 7, "late settlement must not publish across epochs");
  assert.equal(fixture.runtime.trackedStateCount(), 1);
  fixture.runtime.detachNode(node);
  assert.equal(fixture.runtime.trackedStateCount(), 0);
}

{
  for (const invalidId of [
    null,
    undefined,
    "",
    "   ",
    -1,
    "-1",
    1.5,
    Number.MAX_SAFE_INTEGER + 1,
    Number.NaN,
    Infinity,
    -Infinity,
  ]) {
    const node = advancedNode(invalidId, ADVANCED, 7);
    const fixture = createFixture({ nodes: [node] });
    const prompt = promptFor([node]);
    assert.equal(fixture.runtime.attachNode(node), false);
    assert.equal(fixture.runtime.trackedStateCount(), 0);
    assert.equal(fixture.runtime.preparePrompt(prompt), null);
    assert.equal(fixture.runtime.trackedStateCount(), 0);
    let received = null;
    const result = { prompt_id: "invalid-node-id-pass-through", node_errors: {} };
    const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
      received = nextPrompt;
      return result;
    });
    assert.equal(await wrapped(0, prompt), result);
    assert.equal(received, prompt, "invalid node ids must remain on the unmanaged pass-through path");
    assert.equal(fixture.runtime.trackedStateCount(), 0);
    assert.equal(fixture.runtime.detachNode(node), false);
    assert.equal(fixture.runtime.shouldApplyExecutedSeed(node, 8), true);
  }
}

{
  const fixture = createFixture();
  const node = fixture.nodes[0];
  assert.equal(fixture.runtime.attachNode(node), true);
  assert.equal(fixture.runtime.trackedStateCount(), 1);
  assert.equal(fixture.runtime.detachNode(node), true);
  assert.equal(
    fixture.runtime.trackedStateCount(),
    0,
    "removing an idle node must release its managed state immediately",
  );
}

{
  const fixture = createFixture();
  let current = fixture.nodes[0];
  fixture.runtime.attachNode(current);
  for (let index = 0; index < 50; index += 1) {
    assert.equal(fixture.runtime.detachNode(current), true);
    current = advancedNode(1000 + index, ADVANCED, index);
    fixture.nodes.splice(0, 1, current);
    assert.equal(fixture.runtime.attachNode(current), true);
    assert.equal(
      fixture.runtime.trackedStateCount(),
      1,
      "repeated workflow replacement must retain only the live idle owner",
    );
  }
  fixture.runtime.clearGraphNodes();
  assert.equal(
    fixture.runtime.trackedStateCount(),
    0,
    "graph clear must release every idle managed owner",
  );
}

{
  const fixture = createFixture();
  const gate = deferred();
  const oldNode = fixture.nodes[0];
  const wrapped = fixture.runtime.wrapQueuePrompt(() => gate.promise);
  const pending = wrapped(0, promptFor([oldNode]));
  assert.equal(fixture.runtime.trackedStateCount(), 1);

  fixture.runtime.clearGraphNodes();
  assert.equal(
    fixture.runtime.trackedStateCount(),
    1,
    "graph clear must retain a detached state until its queue settles",
  );

  const replacement = advancedNode(10, ADVANCED, 100);
  fixture.nodes.splice(0, 1, replacement);
  assert.equal(fixture.runtime.attachNode(replacement), true);
  assert.equal(
    fixture.runtime.trackedStateCount(),
    2,
    "a pending retired owner and its same-id replacement must have separate identities",
  );
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(replacement, 8),
    false,
    "a configured same-id replacement must reject the retired owner's executed seed",
  );

  gate.resolve({ prompt_id: "retired-owner", node_errors: {} });
  await pending;
  assert.equal(oldNode.widgets[1].value, 7, "late settlement must not publish to a removed owner");
  assert.equal(replacement.widgets[1].value, 100, "late settlement must not publish to a new owner");
  assert.deepEqual(fixture.commits, []);
  assert.equal(
    fixture.runtime.trackedStateCount(),
    1,
    "settlement must release the retired state and retain only the live owner",
  );
  fixture.runtime.detachNode(replacement);
  assert.equal(fixture.runtime.trackedStateCount(), 0);
}

{
  const fixture = createFixture();
  const wrapped = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "old-workflow", node_errors: {},
  }));
  await wrapped(0, promptFor(fixture.nodes));
  const oldNode = fixture.nodes[0];
  const replacement = advancedNode(10, ADVANCED, 100);
  fixture.nodes.splice(0, 1, replacement);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(replacement, 8),
    false,
    "a late executed event must not overwrite a reloaded node with the same id",
  );
  await wrapped(0, promptFor([replacement]));
  assert.equal(replacement.widgets[1].value, 101);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(replacement, 101), true);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(oldNode, 101), false);
}

{
  const fixture = createFixture();
  const wrapped = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "old-safe-workflow", node_errors: {},
  }));
  await wrapped(0, promptFor(fixture.nodes));
  const replacement = advancedNode(10, ADVANCED, Number.MAX_SAFE_INTEGER + 1);
  fixture.nodes.splice(0, 1, replacement);
  const prompt = promptFor([replacement]);
  let received = null;
  const passThrough = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "replacement-unsafe", node_errors: {} };
  });
  await passThrough(0, prompt);
  assert.equal(received, prompt);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(replacement, 0),
    true,
    "a replacement's backend pass-through update may return to the safe range",
  );
}

{
  const fixture = createFixture();
  const host = {
    calls: 0,
    queuePrompt() {
      this.calls += 1;
      return { prompt_id: "installed", node_errors: {} };
    },
  };
  const disposeQueueHook = queueModule.installAdvancedQueueSeedQueueHook(host, fixture.runtime);
  assert.equal(typeof disposeQueueHook, "function");
  const installed = host.queuePrompt;
  const disposeDuplicate = queueModule.installAdvancedQueueSeedQueueHook(host, fixture.runtime);
  assert.equal(disposeDuplicate(), false);
  assert.equal(host.queuePrompt, installed, "repeated setup must not stack wrappers");
  host.queuePrompt = async function (...args) {
    return installed.apply(this, args);
  };
  const foreignWrapper = host.queuePrompt;
  const disposeForeignDuplicate = queueModule.installAdvancedQueueSeedQueueHook(
    host,
    fixture.runtime,
  );
  assert.equal(disposeForeignDuplicate(), false);
  assert.equal(host.queuePrompt, foreignWrapper, "the host marker survives foreign wrapper composition");
  const result = await host.queuePrompt(0, promptFor(fixture.nodes));
  assert.equal(result.prompt_id, "installed");
  assert.equal(host.calls, 1);
  assert.equal(disposeQueueHook(), true);
  assert.equal(host.queuePrompt, foreignWrapper, "dispose must preserve a foreign outer wrapper");
}

{
  const cloneError = new Error("clone failed");
  const fixture = createFixture({ cloneError });
  const prompt = promptFor(fixture.nodes);
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "pass-through", node_errors: {} };
  });
  await wrapped(0, prompt);
  assert.equal(received, prompt);
  assert.equal(fixture.nodes[0].widgets[1].value, 7);
  assert.equal(fixture.cloneCalls(), 1);
}

{
  const fixture = createFixture();
  const prompt = {};
  Object.defineProperty(prompt, "output", {
    get() {
      throw new Error("malformed output getter");
    },
  });
  let received = null;
  const result = { prompt_id: "malformed-prompt-pass-through", node_errors: {} };
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return result;
  });
  assert.equal(await wrapped(0, prompt), result);
  assert.equal(received, prompt);
  assert.equal(fixture.nodes[0].widgets[1].value, 7);
}

{
  const fixture = createFixture();
  const result = { prompt_id: "malformed-validation" };
  Object.defineProperty(result, "node_errors", {
    get() {
      throw new Error("malformed node_errors getter");
    },
  });
  const wrapped = fixture.runtime.wrapQueuePrompt(() => result);
  assert.equal(await wrapped(0, promptFor(fixture.nodes)), result);
  assert.equal(fixture.nodes[0].widgets[1].value, 7);
}

{
  const node = regionalNode(30, 7);
  const fixture = createFixture({ nodes: [node] });
  const gates = [deferred(), deferred(), deferred()];
  const queued = [];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    queued.push({
      current: queuedSeed(prompt, node.id),
      workflow: workflowSeed(prompt, node.id),
      next: reservedNextSeed(prompt, node.id),
    });
    return gates[queued.length - 1].promise;
  });
  const pending = [
    wrapped(0, promptFor([node])),
    wrapped(0, promptFor([node])),
    wrapped(0, promptFor([node])),
  ];

  assert.deepEqual(queued, [
    { current: 7, workflow: 7, next: 8 },
    { current: 8, workflow: 8, next: 9 },
    { current: 9, workflow: 9, next: 10 },
  ]);
  assert.equal(node.widgets[1].value, 7, "Regional live seed changes only after acceptance");

  gates[1].resolve({ prompt_id: "regional-second", node_errors: {} });
  await pending[1];
  assert.equal(node.widgets[1].value, 7, "Regional out-of-order settlement must wait for FIFO");
  gates[0].resolve({ node_errors: {} });
  await pending[0];
  assert.equal(node.widgets[1].value, 9, "a missing prompt_id rolls back only its reservation");
  gates[2].resolve({ prompt_id: "regional-third", node_errors: {} });
  await pending[2];
  assert.equal(node.widgets[1].value, 10);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(node, 8), false);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(node, 10), true);
}

{
  const node = regionalNode(30, 7);
  const fixture = createFixture({ nodes: [node] });
  const seen = [];
  const results = [
    { prompt_id: "   ", node_errors: {} },
    { prompt_id: "regional-retry", node_errors: {} },
  ];
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    seen.push(queuedSeed(prompt, node.id));
    return results.shift();
  });
  await wrapped(0, promptFor([node]));
  assert.equal(node.widgets[1].value, 7, "an empty Regional prompt_id must not advance live state");
  await wrapped(0, promptFor([node]));
  assert.deepEqual(seen, [7, 7], "a rejected Regional seed must remain reusable");
  assert.equal(node.widgets[1].value, 8);
}

{
  const nodes = [regionalNode(30, 7), regionalNode(31, 30)];
  const outputNodes = [{ id: 40, outputNode: true }, { id: 41, outputNode: true }];
  const fixture = createFixture({ nodes, outputNodes });
  const prompt = promptFor(nodes, {
    consumers: [
      { id: 40, source: 30 },
      { id: 41, source: 31 },
    ],
  });
  let received = null;
  const rejected = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return {
      prompt_id: "regional-partial-error",
      node_errors: {
        30: { dependent_outputs: ["40"] },
      },
    };
  });
  await rejected(0, prompt, { partialExecutionTargets: [40] });
  assert.equal(reservedNextSeed(received, 30), 8);
  assert.equal(reservedSeedState(received, 31), undefined);
  assert.equal(nodes[0].widgets[1].value, 7, "a related Regional node_error must rollback");
  assert.equal(nodes[1].widgets[1].value, 30, "a disjoint partial target must not consume seed");

  const accepted = fixture.runtime.wrapQueuePrompt(() => ({
    prompt_id: "regional-partial-valid",
    node_errors: {},
  }));
  await accepted(0, promptFor(nodes, {
    consumers: [
      { id: 40, source: 30 },
      { id: 41, source: 31 },
    ],
  }), { partialExecutionTargets: [40] });
  assert.equal(nodes[0].widgets[1].value, 8);
  assert.equal(nodes[1].widgets[1].value, 30);
}

{
  const nodes = [regionalNode(30, 7), regionalNode(31, 30)];
  const fixture = createFixture({
    nodes,
    outputNodes: [{ id: 40, outputNode: true }],
  });
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, prompt) => {
    received = prompt;
    return { prompt_id: "regional-connected-only", node_errors: {} };
  });
  await wrapped(0, promptFor(nodes, {
    consumers: [{ id: 40, source: 30 }],
  }));
  assert.equal(nodes[0].widgets[1].value, 8);
  assert.equal(nodes[1].widgets[1].value, 30, "a disconnected Regional node must not consume seed");
  assert.equal(reservedNextSeed(received, 30), 8);
  assert.equal(reservedSeedState(received, 31), undefined);
}

{
  const node = regionalNode(30, 7);
  const fixture = createFixture({ nodes: [node] });
  const failure = new Error("Regional queue rejected");
  const wrapped = fixture.runtime.wrapQueuePrompt(() => Promise.reject(failure));
  await assert.rejects(wrapped(0, promptFor([node])), (error) => error === failure);
  assert.equal(node.widgets[1].value, 7, "a thrown Regional queue must rollback its reservation");
}

{
  const node = regionalNode(30, 7);
  const fixture = createFixture({ nodes: [node], cloneError: new Error("Regional clone failed") });
  assert.equal(fixture.runtime.attachNode(node), true);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(node, 8), false);
  const prompt = promptFor([node]);
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "regional-clone-pass-through", node_errors: {} };
  });
  await wrapped(0, prompt);
  assert.equal(received, prompt);
  assert.equal(fixture.runtime.trackedStateCount(), 0);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(node, 8),
    true,
    "Regional clone failure must release the configured authority guard",
  );
}

{
  const node = regionalNode(30, 7);
  const fixture = createFixture({ nodes: [node] });
  assert.equal(fixture.runtime.attachNode(node), true);
  const prompt = promptFor([node]);
  prompt.workflow.nodes = prompt.workflow.nodes.filter(
    (workflowNodeValue) => String(workflowNodeValue.id) !== String(node.id),
  );
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "regional-workflow-pass-through", node_errors: {} };
  });
  await wrapped(0, prompt);
  assert.equal(received, prompt);
  assert.equal(fixture.runtime.trackedStateCount(), 0);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(node, 8),
    true,
    "Regional workflow preparation failure must release the unmanaged guard",
  );
}

{
  const node = regionalNode(30, 7);
  const fixture = createSubgraphFixture({ nodes: [node] });
  assert.equal(fixture.runtime.attachNode(node), true);
  assert.equal(fixture.runtime.shouldApplyExecutedSeed(node, 8), false);
  const prompt = subgraphPromptFor(fixture, {
    connections: [{ executionId: "50:30", targetId: 20 }],
  });
  let received = null;
  const wrapped = fixture.runtime.wrapQueuePrompt((_number, nextPrompt) => {
    received = nextPrompt;
    return { prompt_id: "regional-colon-pass-through", node_errors: {} };
  });
  await wrapped(0, prompt);
  assert.equal(received, prompt, "Regional colon execution ids must remain backend-owned");
  assert.equal(fixture.cloneCalls(), 0);
  assert.equal(node.widgets[1].value, 7);
  assert.equal(reservedSeedState(prompt, "50:30"), undefined);
  assert.equal(fixture.runtime.trackedStateCount(), 0);
  assert.equal(
    fixture.runtime.shouldApplyExecutedSeed(node, 8),
    true,
    "Regional colon pass-through must release the configured guard",
  );
}

{
  const node = regionalNode(30, 7);
  const fixture = createFixture({ nodes: [node] });
  const gate = deferred();
  const wrapped = fixture.runtime.wrapQueuePrompt(() => gate.promise);
  const pending = wrapped(0, promptFor([node]));
  fixture.runtime.clearGraphNodes();
  gate.resolve({ prompt_id: "regional-retired-on-clear", node_errors: {} });
  await pending;
  assert.equal(node.widgets[1].value, 7, "graph clear must retire Regional publish authority");
  assert.equal(fixture.runtime.trackedStateCount(), 0);
}

console.log("Frontend Prompt Studio Advanced queue seed runtime smoke passed.");
