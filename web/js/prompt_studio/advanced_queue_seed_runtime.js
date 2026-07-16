// @ts-check

const MAX_SAFE_SEED = Number.MAX_SAFE_INTEGER;
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
const RESERVED_NEXT_SEED_INPUT = "easyuse_anima_reserved_wildcard_next_seed";

function isRecord(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function normalizeSeed(value) {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) {
    return 0;
  }
  return Math.max(0, Math.min(MAX_SAFE_SEED, Math.trunc(numberValue)));
}

function optionalSeed(value) {
  const numberValue = Number(value);
  return Number.isSafeInteger(numberValue)
    && numberValue >= 0
    && numberValue <= MAX_SAFE_SEED
    ? numberValue
    : null;
}

function normalizeMode(value) {
  return WILDCARD_MODE_ALIASES.get(String(value || "").trim()) || "populate";
}

function normalizeControl(value) {
  const normalized = String(value || "").trim();
  return SEED_CONTROLS.has(normalized) ? normalized : "fixed";
}

function incrementSeed(seed) {
  return seed >= MAX_SAFE_SEED ? 0 : seed + 1;
}

function decrementSeed(seed) {
  return seed <= 0 ? MAX_SAFE_SEED : seed - 1;
}

function nextSeed(seed, mode, control, randomSeed) {
  const effectiveControl = mode === "sequential" ? "increment" : normalizeControl(control);
  if (effectiveControl === "randomize") {
    return normalizeSeed(randomSeed());
  }
  if (effectiveControl === "increment") {
    return incrementSeed(seed);
  }
  if (effectiveControl === "decrement") {
    return decrementSeed(seed);
  }
  return seed;
}

function workflowNode(workflow, nodeId) {
  if (!Array.isArray(workflow?.nodes)) {
    return null;
  }
  return workflow.nodes.find((node) => String(node?.id) === String(nodeId)) || null;
}

function inputSourceIds(value, output, result = new Set()) {
  if (!Array.isArray(value)) {
    return result;
  }
  if (
    value.length >= 2
    && (typeof value[0] === "string" || typeof value[0] === "number")
    && Object.prototype.hasOwnProperty.call(output, String(value[0]))
  ) {
    result.add(String(value[0]));
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
    .map((target) => String(target))
    .filter((target) => Object.prototype.hasOwnProperty.call(output, target));
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
 * @typedef {object} AdvancedQueueSeedDependencies
 * @property {number} seedWidgetIndex
 * @property {() => any[]} listNodes
 * @property {(node: any) => boolean} isAdvancedNode
 * @property {(node: any) => boolean} isOutputNode
 * @property {(node: any) => any} getSeed
 * @property {(node: any, seed: number) => void} updateSeed
 * @property {(value: any) => any} clonePrompt
 * @property {() => number} randomSeed
 */

/**
 * Reserve Prompt Studio Advanced wildcard seeds in queue-only prompt clones.
 * Live widgets advance only after ComfyUI accepts the corresponding queue.
 *
 * @param {AdvancedQueueSeedDependencies} dependencies
 */
function createAdvancedQueueSeedRuntime(dependencies) {
  const {
    seedWidgetIndex,
    listNodes,
    isAdvancedNode,
    isOutputNode,
    getSeed,
    updateSeed,
    clonePrompt,
    randomSeed,
  } = dependencies;
  const nodeStates = new Map();
  let reservationId = 0;

  function stateForNode(node, inputSeed) {
    const nodeId = String(node.id);
    let state = nodeStates.get(nodeId);
    if (!state || state.node !== node) {
      state = {
        node,
        committedSeed: normalizeSeed(inputSeed),
        authoritative: false,
        blockUnknownExecuted: !!state,
        publishFailed: false,
        reservations: [],
      };
      nodeStates.set(nodeId, state);
      return state;
    }
    if (!state.reservations.length) {
      if (state.publishFailed) {
        try {
          updateSeed(node, state.committedSeed);
          state.publishFailed = false;
        } catch {
          return state;
        }
      }
      const liveSeed = optionalSeed(getSeed(node));
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
    if (committed) {
      try {
        updateSeed(node, state.committedSeed);
        state.publishFailed = false;
      } catch {
        state.publishFailed = true;
      }
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
          const nodeId = String(node?.id);
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
        const inputs = output[String(node?.id)]?.inputs;
        if (
          !node
          || !isAdvancedNode(node)
          || !isRecord(inputs)
        ) {
          return [];
        }
        if (optionalSeed(inputs.wildcard_seed) == null) {
          const nodeId = String(node.id);
          const state = nodeStates.get(nodeId);
          if (!state?.reservations.length) {
            // Unsafe 64-bit values stay entirely on the pre-existing backend
            // path. Drop idle managed state so its executed UI update is not
            // filtered by a previous safe reservation or node owner.
            nodeStates.delete(nodeId);
          }
          return [];
        }
        const targetIds = targets.filter(
          (targetId) => isUpstreamOf(output, node.id, targetId, memo),
        );
        return targetIds.length ? [{ node, targetIds }] : [];
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
    for (const { node, targetIds } of candidates) {
      try {
        const inputs = queuedPrompt.output[String(node.id)]?.inputs;
        const workflow = workflowNode(queuedPrompt.workflow, node.id);
        if (!isRecord(inputs) || !workflow || !Array.isArray(workflow.widgets_values)) {
          continue;
        }
        const mode = normalizeMode(inputs.wildcard_mode);
        if (!ACTIVE_WILDCARD_MODES.has(mode)) {
          continue;
        }
        const inputSeed = optionalSeed(inputs.wildcard_seed);
        if (inputSeed == null) {
          // JavaScript cannot reserve 64-bit backend seeds without losing
          // precision. Preserve the original queue payload for those values.
          continue;
        }
        const state = stateForNode(node, inputSeed);
        const queuedSeed = reservedCurrentSeed(state);
        const effectiveControl = mode === "sequential"
          ? "increment"
          : normalizeControl(inputs.wildcard_seed_after_generate);
        const reservedNextSeed = nextSeed(
          queuedSeed,
          mode,
          effectiveControl,
          randomSeed,
        );
        const workflowValues = [...workflow.widgets_values];
        while (workflowValues.length <= seedWidgetIndex) {
          workflowValues.push(null);
        }
        workflowValues[seedWidgetIndex] = queuedSeed;
        workflow.widgets_values = workflowValues;
        inputs[RESERVED_NEXT_SEED_INPUT] = JSON.stringify({
          version: 1,
          current_seed: queuedSeed,
          next_seed: reservedNextSeed,
          mode,
          control: effectiveControl,
        });
        inputs.wildcard_seed = queuedSeed;
        const reservation = {
          id: ++reservationId,
          node,
          nodeId: String(node.id),
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

  function shouldApplyExecutedSeed(node, value) {
    const state = nodeStates.get(String(node?.id));
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
    const liveSeed = optionalSeed(getSeed(node));
    return liveSeed != null
      && liveSeed === state.committedSeed
      && executedSeed === state.committedSeed;
  }

  return {
    preparePrompt,
    shouldApplyExecutedSeed,
    wrapQueuePrompt,
  };
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
  installAdvancedQueueSeedQueueHook,
};
