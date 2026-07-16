// @ts-check

import {
  nextWildcardSeed,
  normalizeWildcardSeed as normalizeSeed,
  optionalWildcardSeed as optionalSeed,
} from "./wildcard_seed_contract.js";

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
const QUEUE_HOOK_MARKER = "__easyuseAnimaAdvancedQueueSeedWrapped";
const QUEUE_HOST_MARKER = "__easyuseAnimaAdvancedQueueSeedInstalled";
const GRAPH_CLEANUP_MARKER = "__easyuseAnimaAdvancedQueueSeedCleanup";
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

function workflowNode(workflow, nodeId) {
  if (!Array.isArray(workflow?.nodes)) {
    return null;
  }
  return workflow.nodes.find((node) => normalizeNodeId(node?.id) === nodeId) || null;
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
 */

/**
 * @typedef {object} AdvancedQueueSeedDependencies
 * @property {() => any[]} listNodes
 * @property {(node: any) => WildcardQueueSeedContract | null} getNodeContract
 * @property {(node: any) => boolean} isOutputNode
 * @property {(node: any, contract: WildcardQueueSeedContract) => any} getSeed
 * @property {(node: any, seed: number, contract: WildcardQueueSeedContract) => void} updateSeed
 * @property {(value: any) => any} clonePrompt
 * @property {() => number} randomSeed
 */

/**
 * Reserve top-level wildcard seeds in queue-only prompt clones.
 * Live widgets advance only after ComfyUI accepts the corresponding queue.
 *
 * @param {AdvancedQueueSeedDependencies} dependencies
 */
function createAdvancedQueueSeedRuntime(dependencies) {
  const {
    listNodes,
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

  function forgetState(state) {
    if (nodeStates.get(state.nodeId) === state) {
      nodeStates.delete(state.nodeId);
    }
    retiredStates.delete(state);
  }

  function retireState(state) {
    state.attached = false;
    if (state.reservations.length) {
      if (nodeStates.get(state.nodeId) === state) {
        nodeStates.delete(state.nodeId);
      }
      retiredStates.add(state);
      return;
    }
    forgetState(state);
  }

  function createState(node, nodeId, inputSeed, contract, blockUnknownExecuted) {
    return {
      node,
      nodeId,
      contract,
      attached: true,
      committedSeed: normalizeSeed(inputSeed),
      authoritative: false,
      blockUnknownExecuted,
      publishFailed: false,
      reservations: [],
    };
  }

  function stateForNode(node, nodeId, inputSeed, contract) {
    let state = nodeStates.get(nodeId);
    if (!state || state.node !== node) {
      const replacedState = state;
      if (replacedState) {
        retireState(replacedState);
      }
      state = createState(node, nodeId, inputSeed, contract, !!replacedState);
      nodeStates.set(nodeId, state);
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
      && nodeStates.get(state.nodeId) === state
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
    let nodes;
    try {
      nodes = listNodes();
    } catch {
      return [];
    }
    if (!Array.isArray(nodes)) {
      return [];
    }
    let targets = partialExecutionTargets(options, output);
    if (targets == null) {
      targets = nodes.flatMap((node) => {
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
    return nodes.flatMap((node) => {
      try {
        const nodeId = normalizeNodeId(node?.id);
        const inputs = nodeId == null ? null : output[nodeId]?.inputs;
        const contract = node ? getNodeContract(node) : null;
        if (
          !node
          || nodeId == null
          || !contract
          || !isRecord(inputs)
        ) {
          return [];
        }
        if (optionalSeed(inputs[contract.seedInputName]) == null) {
          const state = nodeStates.get(nodeId);
          if (state) {
            // Unsafe 64-bit values stay entirely on the pre-existing backend
            // path. Retire even pending safe reservations so a late accepted
            // response can finish bookkeeping without publishing over the
            // unsafe live widget or remaining authoritative for its backend
            // onExecuted update.
            retireState(state);
          }
          return [];
        }
        const targetIds = targets.filter(
          (targetId) => isUpstreamOf(output, nodeId, targetId, memo),
        );
        return targetIds.length ? [{ node, nodeId, targetIds, contract }] : [];
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
      return null;
    }
    if (!isRecord(queuedPrompt) || !isRecord(queuedPrompt.output)) {
      return null;
    }

    const reservations = [];
    for (const { node, nodeId, targetIds, contract } of candidates) {
      try {
        const inputs = queuedPrompt.output[nodeId]?.inputs;
        const workflow = workflowNode(queuedPrompt.workflow, nodeId);
        if (!isRecord(inputs) || !workflow || !Array.isArray(workflow.widgets_values)) {
          continue;
        }
        const mode = normalizeMode(inputs[contract.modeInputName]);
        if (!ACTIVE_WILDCARD_MODES.has(mode)) {
          continue;
        }
        const inputSeed = optionalSeed(inputs[contract.seedInputName]);
        if (inputSeed == null) {
          // JavaScript cannot reserve 64-bit backend seeds without losing
          // precision. Preserve the original queue payload for those values.
          continue;
        }
        const state = stateForNode(node, nodeId, inputSeed, contract);
        const queuedSeed = reservedCurrentSeed(state);
        const effectiveControl = mode === "sequential"
          ? "increment"
          : normalizeControl(inputs[contract.controlInputName]);
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
        inputs[RESERVED_NEXT_SEED_INPUT] = JSON.stringify({
          version: 1,
          current_seed: queuedSeed,
          next_seed: reservedNextSeed,
          mode,
          control: effectiveControl,
        });
        inputs[contract.seedInputName] = queuedSeed;
        const reservation = {
          id: ++reservationId,
          node,
          nodeId,
          state,
          targetIds,
          queuedSeed,
          nextSeed: reservedNextSeed,
          status: "pending",
        };
        state.reservations.push(reservation);
        reservations.push(reservation);
      } catch {
        // One malformed Advanced node must not block unrelated prompt nodes.
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

  function wrapQueuePrompt(queuePrompt) {
    return async function (...args) {
      const transaction = preparePrompt(args[1], args[2]);
      const queueArgs = transaction ? [...args] : args;
      if (transaction) {
        queueArgs[1] = transaction.prompt;
      }
      let result;
      try {
        result = await queuePrompt.apply(this, queueArgs);
      } catch (error) {
        if (transaction) {
          rejectTransaction(transaction);
        }
        throw error;
      }
      if (transaction) {
        settleTransaction(transaction, result);
      }
      return result;
    };
  }

  function attachNode(node) {
    const contract = node ? getNodeContract(node) : null;
    if (!node || !contract) {
      return false;
    }
    const nodeId = normalizeNodeId(node.id);
    if (nodeId == null) {
      return false;
    }
    const inputSeed = optionalSeed(getSeed(node, contract));
    const existing = nodeStates.get(nodeId);
    if (inputSeed == null) {
      if (existing) {
        retireState(existing);
      }
      return false;
    }
    if (existing?.node === node) {
      if (existing.reservations.length) {
        retireState(existing);
        const state = createState(node, nodeId, inputSeed, contract, true);
        nodeStates.set(nodeId, state);
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
    const state = createState(node, nodeId, inputSeed, contract, true);
    nodeStates.set(nodeId, state);
    return true;
  }

  function detachNode(node) {
    const nodeId = normalizeNodeId(node?.id);
    if (nodeId == null) {
      return false;
    }
    const state = nodeStates.get(nodeId);
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
    const nodeId = normalizeNodeId(node?.id);
    if (nodeId == null) {
      return true;
    }
    const state = nodeStates.get(nodeId);
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
    attachNode,
    clearGraphNodes,
    detachNode,
    preparePrompt,
    shouldApplyExecutedSeed,
    trackedStateCount,
    wrapQueuePrompt,
  };
}

function installAdvancedQueueSeedGraphCleanup(graph, runtime) {
  if (
    !graph
    || typeof graph.clear !== "function"
    || graph.clear[GRAPH_CLEANUP_MARKER]
  ) {
    return false;
  }
  const clear = graph.clear;
  const wrappedClear = function () {
    const result = clear.apply(this, arguments);
    runtime.clearGraphNodes();
    return result;
  };
  wrappedClear[GRAPH_CLEANUP_MARKER] = true;
  graph.clear = wrappedClear;
  return true;
}

function installAdvancedQueueSeedQueueHook(queueHost, runtime) {
  if (
    !queueHost
    || typeof queueHost.queuePrompt !== "function"
    || queueHost[QUEUE_HOST_MARKER]
    || queueHost.queuePrompt[QUEUE_HOOK_MARKER]
  ) {
    return false;
  }
  const wrappedQueuePrompt = runtime.wrapQueuePrompt(queueHost.queuePrompt);
  wrappedQueuePrompt[QUEUE_HOOK_MARKER] = true;
  queueHost.queuePrompt = wrappedQueuePrompt;
  queueHost[QUEUE_HOST_MARKER] = true;
  return true;
}

export {
  createAdvancedQueueSeedRuntime,
  installAdvancedQueueSeedGraphCleanup,
  installAdvancedQueueSeedQueueHook,
};
