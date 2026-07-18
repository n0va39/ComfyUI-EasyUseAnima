// @ts-check

import {
  nextWildcardSeed,
  normalizeWildcardSeed as normalizeSeed,
  optionalWildcardSeed as optionalSeed,
} from "./wildcard_seed_contract.js";
import {
  registerHostHookCallbacks,
} from "../lifecycle/host_hook_registry.js";

const ACTIVE_WILDCARD_MODES = new Set(["populate", "fixed", "sequential"]);
const WILDCARD_MODE_ALIASES = new Map([
  ["populate", "populate"],
  ["normal", "populate"],
  ["fill", "populate"],
  ["일반", "populate"],
  ["일반 채우기", "populate"],
  ["fixed", "fixed"],
  ["고정", "fixed"],
  ["sequential", "sequential"],
  ["순차", "sequential"],
  ["reproduce", "reproduce"],
  ["재현", "reproduce"],
]);
const SEED_CONTROLS = new Set(["fixed", "randomize", "increment", "decrement"]);
const ADVANCED_QUEUE_SEED_OWNER = Symbol.for(
  "easyuse-anima.prompt-studio.advanced-queue-seed",
);
const ADVANCED_QUEUE_SEED_CLEAR_OWNER = Symbol.for(
  "easyuse-anima.prompt-studio.advanced-queue-seed-clear",
);
const RESERVED_NEXT_SEED_INPUT = "easyuse_anima_reserved_wildcard_next_seed";

function isRecord(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function normalizeNodeId(value) {
  if (typeof value === "number") {
    return Number.isSafeInteger(value) && value >= 0 ? String(value) : null;
  }
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized && normalized !== "-1" ? normalized : null;
}

function normalizeMode(value) {
  return WILDCARD_MODE_ALIASES.get(String(value || "").trim()) || "populate";
}

function normalizeControl(value) {
  const normalized = String(value || "").trim();
  return SEED_CONTROLS.has(normalized) ? normalized : "fixed";
}

function nextSeed(seed, mode, control, randomSeed) {
  const effectiveControl = mode === "sequential" ? "increment" : normalizeControl(control);
  return nextWildcardSeed(seed, effectiveControl, randomSeed);
}

function workflowSubgraphDefinitions(workflow) {
  const definitions = new Map();
  const pending = Array.isArray(workflow?.definitions?.subgraphs)
    ? [...workflow.definitions.subgraphs]
    : [];
  while (pending.length) {
    const definition = pending.shift();
    const definitionId = normalizeNodeId(definition?.id);
    if (definitionId == null || definitions.has(definitionId)) {
      continue;
    }
    definitions.set(definitionId, definition);
    if (Array.isArray(definition?.definitions?.subgraphs)) {
      pending.push(...definition.definitions.subgraphs);
    }
  }
  return definitions;
}

function workflowNode(workflow, executionId) {
  if (!Array.isArray(workflow?.nodes)) {
    return null;
  }
  const nodeIds = String(executionId || "")
    .split(":")
    .map((value) => normalizeNodeId(value));
  if (!nodeIds.length || nodeIds.some((value) => value == null)) {
    return null;
  }
  const definitions = workflowSubgraphDefinitions(workflow);
  let nodes = workflow.nodes;
  let found = null;
  for (let index = 0; index < nodeIds.length; index += 1) {
    found = nodes.find((node) => normalizeNodeId(node?.id) === nodeIds[index]) || null;
    if (!found || index === nodeIds.length - 1) {
      break;
    }
    const definition = definitions.get(normalizeNodeId(found.type));
    if (!Array.isArray(definition?.nodes)) {
      return null;
    }
    nodes = definition.nodes;
  }
  return found;
}

function graphNodeEntries(rootGraph) {
  if (!Array.isArray(rootGraph?._nodes)) {
    return [];
  }
  const entries = new Map();

  function visit(graph, parentPath, ancestors) {
    if (!Array.isArray(graph?._nodes)) {
      return;
    }
    for (const node of graph._nodes) {
      const nodeId = normalizeNodeId(node?.id);
      if (!node || nodeId == null) {
        continue;
      }
      const executionId = [...parentPath, nodeId].join(":");
      let entry = entries.get(node);
      if (!entry) {
        entry = { node, executionIds: [] };
        entries.set(node, entry);
      }
      if (!entry.executionIds.includes(executionId)) {
        entry.executionIds.push(executionId);
      }

      const subgraph = node.subgraph;
      if (!Array.isArray(subgraph?._nodes) || ancestors.has(node)) {
        continue;
      }
      const nestedAncestors = new Set(ancestors);
      nestedAncestors.add(node);
      visit(subgraph, [...parentPath, nodeId], nestedAncestors);
    }
  }

  visit(rootGraph, [], new Set());
  return [...entries.values()];
}

function nodeStateKey(rootGraph, node) {
  const nodeId = normalizeNodeId(node?.id);
  if (nodeId == null) {
    return null;
  }
  const graph = node?.graph;
  if (!graph || graph === rootGraph || graph.isRootGraph === true) {
    return nodeId;
  }
  const graphId = normalizeNodeId(graph.id);
  return graphId == null ? nodeId : `${graphId}:${nodeId}`;
}

function inputSourceIds(value, output, result = new Set()) {
  if (!Array.isArray(value)) {
    return result;
  }
  const sourceId = normalizeNodeId(value[0]);
  if (
    value.length >= 2
    && sourceId != null
    && Object.prototype.hasOwnProperty.call(output, sourceId)
  ) {
    result.add(sourceId);
    return result;
  }
  for (const item of value) {
    inputSourceIds(item, output, result);
  }
  return result;
}

function directInputSourceIds(output, nodeId) {
  const inputs = output?.[String(nodeId)]?.inputs;
  if (!isRecord(inputs)) {
    return new Set();
  }
  const sources = new Set();
  for (const value of Object.values(inputs)) {
    inputSourceIds(value, output, sources);
  }
  return sources;
}

function upstreamNodeIds(output, targetId, memo = new Map(), visiting = new Set()) {
  const key = String(targetId);
  if (memo.has(key)) {
    return memo.get(key);
  }
  if (visiting.has(key)) {
    return new Set([key]);
  }
  visiting.add(key);
  const upstream = new Set([key]);
  for (const sourceId of directInputSourceIds(output, key)) {
    for (const nestedId of upstreamNodeIds(output, sourceId, memo, visiting)) {
      upstream.add(nestedId);
    }
  }
  visiting.delete(key);
  memo.set(key, upstream);
  return upstream;
}

function isUpstreamOf(output, sourceId, targetId, memo = new Map()) {
  return upstreamNodeIds(output, targetId, memo).has(String(sourceId));
}

function partialExecutionTargets(options, output) {
  let rawTargets;
  try {
    if (
      !isRecord(options)
      || !Object.prototype.hasOwnProperty.call(options, "partialExecutionTargets")
      || options.partialExecutionTargets == null
    ) {
      return null;
    }
    rawTargets = options.partialExecutionTargets;
  } catch {
    return [];
  }
  if (!Array.isArray(rawTargets)) {
    return [];
  }
  return rawTargets
    .map((target) => normalizeNodeId(target))
    .filter((target) => (
      target != null && Object.prototype.hasOwnProperty.call(output, target)
    ));
}

function queueResultPromptId(result) {
  try {
    const promptId = result?.prompt_id;
    return promptId == null || String(promptId).trim() === "" ? null : promptId;
  } catch {
    return null;
  }
}

function queueResultNodeErrors(result) {
  try {
    return result?.node_errors;
  } catch {
    return true;
  }
}

function reservationWasAccepted(result, reservation, prompt) {
  if (queueResultPromptId(result) == null) {
    return false;
  }
  const nodeErrors = queueResultNodeErrors(result);
  if (nodeErrors == null || nodeErrors === false || nodeErrors === 0 || nodeErrors === "") {
    return true;
  }
  if (Array.isArray(nodeErrors)) {
    return nodeErrors.length === 0;
  }
  if (!isRecord(nodeErrors)) {
    return false;
  }
  const entries = Object.entries(nodeErrors);
  if (!entries.length) {
    return true;
  }
  const output = prompt?.output;
  if (!isRecord(output)) {
    return false;
  }
  const memo = new Map();
  return reservation.targetIds.some((targetId) => !entries.some(([errorNodeId, detail]) => {
    if (
      String(errorNodeId) === String(targetId)
      || isUpstreamOf(output, errorNodeId, targetId, memo)
    ) {
      return true;
    }
    const dependentOutputs = isRecord(detail) ? detail.dependent_outputs : null;
    return Array.isArray(dependentOutputs)
      && dependentOutputs.some((value) => String(value) === String(targetId));
  }));
}

/**
 * @typedef {object} WildcardQueueSeedContract
 * @property {string} modeInputName
 * @property {string} seedInputName
 * @property {string} controlInputName
 * @property {number} seedWidgetIndex
 * @property {boolean} [supportsSubgraph]
 */

/**
 * @typedef {object} AdvancedQueueSeedDependencies
 * @property {() => any[]} listNodes
 * @property {() => any} [getRootGraph]
 * @property {any} [rootGraph]
 * @property {(node: any) => WildcardQueueSeedContract | null} getNodeContract
 * @property {(node: any) => boolean} isOutputNode
 * @property {(node: any, contract: WildcardQueueSeedContract) => any} getSeed
 * @property {(node: any, seed: number, contract: WildcardQueueSeedContract) => void} updateSeed
 * @property {(value: any) => any} clonePrompt
 * @property {() => number} randomSeed
 */

/**
 * Reserve eligible wildcard seeds upstream of root output targets in queue-only prompt clones.
 * Live widgets advance only after ComfyUI accepts the corresponding queue.
 *
 * @param {AdvancedQueueSeedDependencies} dependencies
 */
function createAdvancedQueueSeedRuntime(dependencies) {
  const {
    listNodes,
    getRootGraph = null,
    rootGraph: initialRootGraph = null,
    getNodeContract,
    isOutputNode,
    getSeed,
    updateSeed,
    clonePrompt,
    randomSeed,
  } = dependencies;
  const nodeStates = new Map();
  const retiredStates = new Set();
  let reservationId = 0;

  function resolveRootGraph() {
    if (typeof getRootGraph === "function") {
      try {
        return getRootGraph() || initialRootGraph;
      } catch {
        return initialRootGraph;
      }
    }
    return initialRootGraph;
  }

  function forgetState(state) {
    if (nodeStates.get(state.stateKey) === state) {
      nodeStates.delete(state.stateKey);
    }
    retiredStates.delete(state);
  }

  function retireState(state) {
    state.attached = false;
    if (state.reservations.length) {
      if (nodeStates.get(state.stateKey) === state) {
        nodeStates.delete(state.stateKey);
      }
      retiredStates.add(state);
      return;
    }
    forgetState(state);
  }

  function retireCandidateState(candidate) {
    const state = nodeStates.get(candidate.stateKey);
    if (state) {
      retireState(state);
    }
  }

  function retireCandidateStates(candidates) {
    for (const candidate of candidates) {
      retireCandidateState(candidate);
    }
  }

  function createState(node, stateKey, inputSeed, contract, blockUnknownExecuted) {
    return {
      node,
      stateKey,
      contract,
      attached: true,
      committedSeed: normalizeSeed(inputSeed),
      authoritative: false,
      blockUnknownExecuted,
      publishFailed: false,
      reservations: [],
    };
  }

  function stateForNode(node, stateKey, inputSeed, contract) {
    let state = nodeStates.get(stateKey);
    if (!state || state.node !== node) {
      const replacedState = state;
      if (replacedState) {
        retireState(replacedState);
      }
      state = createState(node, stateKey, inputSeed, contract, !!replacedState);
      nodeStates.set(stateKey, state);
      return state;
    }
    state.attached = true;
    if (!state.reservations.length) {
      if (state.publishFailed) {
        try {
          updateSeed(node, state.committedSeed, state.contract);
          state.publishFailed = false;
        } catch {
          return state;
        }
      }
      const liveSeed = optionalSeed(getSeed(node, state.contract));
      if (liveSeed != null && liveSeed !== state.committedSeed) {
        state.committedSeed = liveSeed;
        state.authoritative = false;
        state.blockUnknownExecuted = true;
      }
    }
    return state;
  }

  function reservedCurrentSeed(state) {
    const tail = state.reservations[state.reservations.length - 1];
    return tail ? tail.nextSeed : state.committedSeed;
  }

  function flushResolvedReservations(state, node) {
    let committed = false;
    while (state.reservations.length && state.reservations[0].status !== "pending") {
      const reservation = state.reservations.shift();
      if (reservation.status === "accepted") {
        state.committedSeed = reservation.nextSeed;
        state.authoritative = true;
        committed = true;
      }
    }
    if (
      committed
      && state.attached
      && state.node === node
      && nodeStates.get(state.stateKey) === state
    ) {
      try {
        updateSeed(node, state.committedSeed, state.contract);
        state.publishFailed = false;
      } catch {
        state.publishFailed = true;
      }
    }
    if (!state.reservations.length && !state.attached) {
      forgetState(state);
    }
  }

  function settleReservation(reservation, accepted) {
    const { state, node } = reservation;
    if (reservation.status !== "pending") {
      return;
    }
    reservation.status = accepted ? "accepted" : "rejected";
    if (!accepted && state.reservations[state.reservations.length - 1] === reservation) {
      state.reservations.pop();
    }
    flushResolvedReservations(state, node);
  }

  function candidateNodes(prompt, options) {
    let output;
    try {
      output = prompt?.output;
    } catch {
      return [];
    }
    if (!isRecord(prompt) || !isRecord(output)) {
      return [];
    }
    const rootGraph = resolveRootGraph();
    let entries;
    let rootNodes;
    try {
      if (rootGraph) {
        entries = graphNodeEntries(rootGraph);
        rootNodes = Array.isArray(rootGraph?._nodes) ? rootGraph._nodes : [];
      } else {
        const nodes = listNodes();
        if (!Array.isArray(nodes)) {
          return [];
        }
        rootNodes = nodes;
        entries = nodes.map((node) => ({
          node,
          executionIds: [normalizeNodeId(node?.id)].filter((value) => value != null),
        }));
      }
    } catch {
      return [];
    }
    if (!Array.isArray(entries) || !Array.isArray(rootNodes)) {
      return [];
    }
    let targets = partialExecutionTargets(options, output);
    if (targets == null) {
      targets = rootNodes.flatMap((node) => {
        try {
          const nodeId = normalizeNodeId(node?.id);
          if (nodeId == null) {
            return [];
          }
          return node && isOutputNode(node) && isRecord(output[nodeId]) ? [nodeId] : [];
        } catch {
          return [];
        }
      });
    }
    if (!targets.length) {
      return [];
    }
    const memo = new Map();
    return entries.flatMap((entry) => {
      try {
        const node = entry?.node;
        const contract = node ? getNodeContract(node) : null;
        const stateKey = nodeStateKey(rootGraph, node);
        if (!node || !contract || stateKey == null || !Array.isArray(entry.executionIds)) {
          return [];
        }
        const executionIds = entry.executionIds.filter((nodeId) => (
          contract.supportsSubgraph === true || !String(nodeId).includes(":")
        ));
        if (!executionIds.length && entry.executionIds.length) {
          const state = nodeStates.get(stateKey);
          if (state) {
            // Top-level-only contracts remain backend-owned when their only
            // executions are colon-qualified subgraph instances. Release the
            // configured authority guard so backend next-seed metadata can
            // settle the live widget after the unmanaged queue completes.
            retireState(state);
          }
          return [];
        }
        const executions = executionIds.flatMap((nodeId) => {
          const inputs = output[nodeId]?.inputs;
          if (!isRecord(inputs)) {
            return [];
          }
          const targetIds = targets.filter(
            (targetId) => isUpstreamOf(output, nodeId, targetId, memo),
          );
          return targetIds.length ? [{ nodeId, inputs, targetIds }] : [];
        });
        if (!executions.length) {
          return [];
        }
        const inputSeeds = executions.map(
          ({ inputs }) => optionalSeed(inputs[contract.seedInputName]),
        );
        if (
          inputSeeds.some((value) => value == null)
          || inputSeeds.some((value) => value !== inputSeeds[0])
        ) {
          const state = nodeStates.get(stateKey);
          if (state) {
            // Unsafe 64-bit values stay entirely on the pre-existing backend
            // path. Multiple live instances that resolve the same definition
            // node to different seeds are also backend-owned because one
            // workflow definition cannot persist distinct current values.
            retireState(state);
          }
          return [];
        }
        const targetIds = [...new Set(executions.flatMap((value) => value.targetIds))];
        return [{ node, stateKey, executions, targetIds, contract }];
      } catch {
        return [];
      }
    });
  }

  function preparePrompt(prompt, options = null) {
    const candidates = candidateNodes(prompt, options);
    if (!candidates.length) {
      return null;
    }
    let queuedPrompt;
    try {
      queuedPrompt = clonePrompt(prompt);
    } catch {
      retireCandidateStates(candidates);
      return null;
    }
    if (!isRecord(queuedPrompt) || !isRecord(queuedPrompt.output)) {
      retireCandidateStates(candidates);
      return null;
    }

    const reservations = [];
    for (const candidate of candidates) {
      const { node, stateKey, executions, targetIds, contract } = candidate;
      try {
        const preparedExecutions = executions.map(({ nodeId }) => {
          const inputs = queuedPrompt.output[nodeId]?.inputs;
          const workflow = workflowNode(queuedPrompt.workflow, nodeId);
          if (!isRecord(inputs) || !workflow || !Array.isArray(workflow.widgets_values)) {
            return null;
          }
          const mode = normalizeMode(inputs[contract.modeInputName]);
          const inputSeed = optionalSeed(inputs[contract.seedInputName]);
          const effectiveControl = mode === "sequential"
            ? "increment"
            : normalizeControl(inputs[contract.controlInputName]);
          return { nodeId, inputs, workflow, mode, inputSeed, effectiveControl };
        });
        if (preparedExecutions.some((value) => value == null)) {
          retireCandidateState(candidate);
          continue;
        }
        const first = preparedExecutions[0];
        const { workflow, mode, inputSeed, effectiveControl } = first;
        if (!ACTIVE_WILDCARD_MODES.has(mode)) {
          retireCandidateState(candidate);
          continue;
        }
        if (
          inputSeed == null
          || preparedExecutions.some((value) => (
            value.workflow !== workflow
            || value.mode !== mode
            || value.inputSeed !== inputSeed
            || value.effectiveControl !== effectiveControl
          ))
        ) {
          // JavaScript cannot reserve 64-bit backend seeds without losing
          // precision. Per-instance promoted values also stay backend-owned
          // when one shared definition cannot persist one coherent state.
          retireCandidateState(candidate);
          continue;
        }
        const state = stateForNode(node, stateKey, inputSeed, contract);
        const queuedSeed = reservedCurrentSeed(state);
        const reservedNextSeed = nextSeed(
          queuedSeed,
          mode,
          effectiveControl,
          randomSeed,
        );
        const workflowValues = [...workflow.widgets_values];
        while (workflowValues.length <= contract.seedWidgetIndex) {
          workflowValues.push(null);
        }
        workflowValues[contract.seedWidgetIndex] = queuedSeed;
        workflow.widgets_values = workflowValues;
        const reservationInput = JSON.stringify({
          version: 1,
          current_seed: queuedSeed,
          next_seed: reservedNextSeed,
          mode,
          control: effectiveControl,
        });
        for (const { inputs } of preparedExecutions) {
          inputs[RESERVED_NEXT_SEED_INPUT] = reservationInput;
          inputs[contract.seedInputName] = queuedSeed;
        }
        const reservation = {
          id: ++reservationId,
          node,
          nodeId: first.nodeId,
          nodeIds: preparedExecutions.map((value) => value.nodeId),
          state,
          targetIds,
          queuedSeed,
          nextSeed: reservedNextSeed,
          status: "pending",
        };
        state.reservations.push(reservation);
        reservations.push(reservation);
      } catch {
        // One malformed wildcard-seed node must not block unrelated prompt
        // nodes or leave its configured guard attached to an unmanaged queue.
        retireCandidateState(candidate);
      }
    }
    return reservations.length ? { prompt: queuedPrompt, reservations } : null;
  }

  function settleTransaction(transaction, result) {
    for (const reservation of transaction.reservations) {
      let accepted = false;
      try {
        accepted = reservationWasAccepted(result, reservation, transaction.prompt);
      } catch {
        // Malformed validation metadata is a failed reservation, not a reason
        // to replace ComfyUI's already-resolved queue result with a rejection.
      }
      settleReservation(reservation, accepted);
    }
  }

  function rejectTransaction(transaction) {
    for (const reservation of transaction.reservations) {
      settleReservation(reservation, false);
    }
  }

  function beforeQueue(context) {
    const transaction = preparePrompt(context.args[1], context.args[2]);
    if (transaction) {
      const queueArgs = [...context.args];
      queueArgs[1] = transaction.prompt;
      context.args = queueArgs;
    }
    return transaction;
  }

  function afterQueue(context) {
    const transaction = context.callbackState;
    if (!transaction) {
      return;
    }
    if (context.ok) {
      settleTransaction(transaction, context.result);
    } else {
      rejectTransaction(transaction);
    }
  }

  function wrapQueuePrompt(queuePrompt) {
    return async function (...args) {
      const context = { args };
      const transaction = beforeQueue(context);
      let result;
      try {
        result = await queuePrompt.apply(this, context.args);
      } catch (error) {
        afterQueue({ callbackState: transaction, ok: false, error });
        throw error;
      }
      afterQueue({ callbackState: transaction, ok: true, result });
      return result;
    };
  }

  function attachNode(node) {
    const contract = node ? getNodeContract(node) : null;
    if (!node || !contract) {
      return false;
    }
    const stateKey = nodeStateKey(resolveRootGraph(), node);
    if (stateKey == null) {
      return false;
    }
    const inputSeed = optionalSeed(getSeed(node, contract));
    const existing = nodeStates.get(stateKey);
    if (inputSeed == null) {
      if (existing) {
        retireState(existing);
      }
      return false;
    }
    if (existing?.node === node) {
      if (existing.reservations.length) {
        retireState(existing);
        const state = createState(node, stateKey, inputSeed, contract, true);
        nodeStates.set(stateKey, state);
        return true;
      }
      existing.attached = true;
      existing.committedSeed = inputSeed;
      existing.authoritative = false;
      existing.blockUnknownExecuted = true;
      existing.publishFailed = false;
      return true;
    }
    if (existing) {
      retireState(existing);
    }
    const state = createState(node, stateKey, inputSeed, contract, true);
    nodeStates.set(stateKey, state);
    return true;
  }

  function detachNode(node) {
    const stateKey = nodeStateKey(resolveRootGraph(), node);
    if (stateKey == null) {
      return false;
    }
    const state = nodeStates.get(stateKey);
    if (!state || state.node !== node) {
      return false;
    }
    retireState(state);
    return true;
  }

  function clearGraphNodes() {
    for (const state of [...nodeStates.values()]) {
      retireState(state);
    }
  }

  function trackedStateCount() {
    return nodeStates.size + retiredStates.size;
  }

  function shouldApplyExecutedSeed(node, value) {
    const stateKey = nodeStateKey(resolveRootGraph(), node);
    if (stateKey == null) {
      return true;
    }
    const state = nodeStates.get(stateKey);
    if (!state) {
      return true;
    }
    if (state.node !== node) {
      return false;
    }
    if (state.blockUnknownExecuted && !state.authoritative) {
      return false;
    }
    if (!state.authoritative) {
      return true;
    }
    const executedSeed = normalizeSeed(value);
    if (state.publishFailed && executedSeed === state.committedSeed) {
      state.publishFailed = false;
      return true;
    }
    const liveSeed = optionalSeed(getSeed(node, state.contract));
    return liveSeed != null
      && liveSeed === state.committedSeed
      && executedSeed === state.committedSeed;
  }

  return {
    afterQueue,
    attachNode,
    beforeQueue,
    clearGraphNodes,
    detachNode,
    preparePrompt,
    shouldApplyExecutedSeed,
    trackedStateCount,
    wrapQueuePrompt,
  };
}

function installAdvancedQueueSeedGraphCleanup(graph, runtime) {
  return registerHostHookCallbacks({
    owner: ADVANCED_QUEUE_SEED_CLEAR_OWNER,
    graphHost: graph,
    onGraphClear: runtime.clearGraphNodes,
  });
}

function installAdvancedQueueSeedQueueHook(queueHost, runtime) {
  return registerHostHookCallbacks({
    owner: ADVANCED_QUEUE_SEED_OWNER,
    queueHost,
    beforeQueue: runtime.beforeQueue,
    afterQueue: runtime.afterQueue,
  });
}

export {
  createAdvancedQueueSeedRuntime,
  installAdvancedQueueSeedGraphCleanup,
  installAdvancedQueueSeedQueueHook,
};
