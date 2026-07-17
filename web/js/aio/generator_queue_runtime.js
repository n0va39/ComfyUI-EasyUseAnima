// @ts-check

const QUEUE_HOOK_MARKER = "__easyuseAnimaAioWrapped";
const QUEUE_HOST_MARKER = "__easyuseAnimaAioQueuePromptInstalled";

/**
 * @typedef {object} AioGeneratorQueueSettingsCore
 * @property {(value: any, fallback?: number) => number} normalizeSeedValue
 * @property {(value: any) => string} normalizeSeedControl
 * @property {(value: any) => any} cloneJson
 * @property {(settings: any) => string} settingsToCompactJson
 */

/**
 * @typedef {object} AioGeneratorQueueNodeAdapter
 * @property {() => any[]} listNodes
 * @property {(node: any) => boolean} isBypassed
 * @property {(node: any) => any} getSettings
 * @property {(settings: any) => any} sanitizeSettings
 * @property {(node: any) => any} getLastQueuedSeed
 * @property {(node: any, seed: number) => void} commitLastQueuedSeed
 * @property {(node: any, seed: number, options: {markDirty: boolean}) => void} updateSeed
 */

/**
 * @typedef {object} AioGeneratorQueueDependencies
 * @property {{settingsWidgetName: string, minSeed: number, maxSeed: number, specialSeedRandom: number, specialSeedIncrement: number, specialSeedDecrement: number}} constants
 * @property {AioGeneratorQueueSettingsCore} settingsCore
 * @property {AioGeneratorQueueNodeAdapter} nodeAdapter
 * @property {{loadOptionalDependencies: (options?: {retryErrors?: boolean}) => any}} queueAdapter
 * @property {() => number} randomSeed
 */

/**
 * Own the transactional AiO queue payload and seed lifecycle. The runtime is
 * DOM-free: extension registration, api.queuePrompt replacement, optional
 * dependency discovery, settings sanitization, and panel rendering stay behind
 * injected adapters.
 *
 * @param {AioGeneratorQueueDependencies} dependencies
 */
export function aioCreateGeneratorQueueRuntime(dependencies) {
  const {
    constants,
    settingsCore,
    nodeAdapter,
    queueAdapter,
    randomSeed,
  } = dependencies;
  const {
    settingsWidgetName,
    minSeed,
    maxSeed,
    specialSeedRandom,
    specialSeedIncrement,
    specialSeedDecrement,
  } = constants;
  const {
    normalizeSeedValue,
    normalizeSeedControl,
    cloneJson,
    settingsToCompactJson,
  } = settingsCore;
  const {
    listNodes,
    isBypassed,
    getSettings,
    sanitizeSettings,
    getLastQueuedSeed,
    commitLastQueuedSeed,
    updateSeed,
  } = nodeAdapter;
  const { loadOptionalDependencies } = queueAdapter;
  const specialSeeds = new Set([
    specialSeedRandom,
    specialSeedIncrement,
    specialSeedDecrement,
  ]);

  function isRecord(value) {
    return !!value && typeof value === "object" && !Array.isArray(value);
  }

  function clampConcreteSeed(value, fallback = minSeed) {
    const numberValue = Number(value);
    const concrete = Number.isFinite(numberValue) ? Math.trunc(numberValue) : fallback;
    return Math.max(minSeed, Math.min(maxSeed, concrete));
  }

  function randomConcreteSeed() {
    return clampConcreteSeed(randomSeed(), minSeed);
  }

  function lastConcreteSeed(node) {
    const rawValue = getLastQueuedSeed(node);
    if (rawValue == null) {
      return null;
    }
    const value = Number(rawValue);
    if (!Number.isFinite(value) || specialSeeds.has(value)) {
      return null;
    }
    return clampConcreteSeed(value);
  }

  function resolveQueuedSeed(node, inputSeed) {
    const seed = normalizeSeedValue(inputSeed, specialSeedRandom);
    if (!specialSeeds.has(seed)) {
      return clampConcreteSeed(seed);
    }
    const lastSeed = lastConcreteSeed(node);
    if (lastSeed != null && seed === specialSeedIncrement) {
      return clampConcreteSeed(lastSeed + 1);
    }
    if (lastSeed != null && seed === specialSeedDecrement) {
      return clampConcreteSeed(lastSeed - 1);
    }
    return randomConcreteSeed();
  }

  function nextLiveSeed(seedControl, inputSeed, queuedSeed) {
    switch (normalizeSeedControl(seedControl)) {
      case "randomize":
        return randomConcreteSeed();
      case "increment":
        return clampConcreteSeed(queuedSeed + 1);
      case "decrement":
        return clampConcreteSeed(queuedSeed - 1);
      default:
        return normalizeSeedValue(inputSeed, specialSeedRandom);
    }
  }

  function findWorkflowNode(workflow, id) {
    if (!Array.isArray(workflow?.nodes)) {
      return null;
    }
    return workflow.nodes.find(
      (workflowNode) => String(workflowNode?.id) === String(id),
    ) || null;
  }

  function stageWorkflowSettingsValue(node, workflowNode, value) {
    if (
      !workflowNode
      || !Array.isArray(workflowNode.widgets_values)
      || !Array.isArray(node?.widgets)
    ) {
      return false;
    }
    const index = node.widgets.findIndex(
      (widget) => widget?.name === settingsWidgetName,
    );
    if (index < 0) {
      return false;
    }
    const nextValues = [...workflowNode.widgets_values];
    while (nextValues.length <= index) {
      nextValues.push(null);
    }
    nextValues[index] = value;
    return {
      workflowNode,
      previousValues: workflowNode.widgets_values,
      nextValues,
    };
  }

  function applyQueuedSettingsTransaction(queuedInputs, serializedSettings, workflowWrite) {
    const hadOutputSettings = Object.prototype.hasOwnProperty.call(
      queuedInputs,
      "generation_settings",
    );
    const previousOutputSettings = queuedInputs.generation_settings;
    try {
      queuedInputs.generation_settings = serializedSettings;
      workflowWrite.workflowNode.widgets_values = workflowWrite.nextValues;
    } catch (error) {
      try {
        if (hadOutputSettings) {
          queuedInputs.generation_settings = previousOutputSettings;
        } else {
          delete queuedInputs.generation_settings;
        }
      } catch {
        // A hostile/malformed output setter may reject both apply and rollback.
      }
      try {
        workflowWrite.workflowNode.widgets_values = workflowWrite.previousValues;
      } catch {
        // A hostile/malformed workflow setter may reject both operations.
      }
      throw error;
    }
  }

  function partialExecutionTargetIds(options) {
    if (
      !isRecord(options)
      || !Object.prototype.hasOwnProperty.call(options, "partialExecutionTargets")
      || options.partialExecutionTargets == null
    ) {
      return null;
    }
    if (!Array.isArray(options.partialExecutionTargets)) {
      return new Set();
    }
    return new Set(options.partialExecutionTargets.map((target) => String(target)));
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
    const targetIds = partialExecutionTargetIds(options);
    return nodes.filter((node) => {
      if (!node) {
        return false;
      }
      try {
        const nodeId = String(node.id);
        return (
          !isBypassed(node)
          && (!targetIds || targetIds.has(nodeId))
          && isRecord(output[nodeId]?.inputs)
        );
      } catch {
        return false;
      }
    });
  }

  /**
   * Build a queue-only clone and a deferred live-seed commit plan. Returning
   * null means the original prompt should pass through untouched.
   *
   * @param {any} prompt
   * @param {any} [options]
   */
  function preparePrompt(prompt, options = null) {
    const nodes = candidateNodes(prompt, options);
    if (!nodes.length) {
      return null;
    }
    let queuedPrompt;
    try {
      queuedPrompt = cloneJson(prompt);
    } catch {
      return null;
    }
    if (!isRecord(queuedPrompt) || !isRecord(queuedPrompt.output)) {
      return null;
    }

    const commits = [];
    for (const node of nodes) {
      try {
        const queuedInputs = queuedPrompt.output[String(node.id)]?.inputs;
        if (!isRecord(queuedInputs)) {
          continue;
        }
        const liveSettings = getSettings(node);
        const settingsSnapshot = cloneJson(liveSettings);
        const queuedSettings = sanitizeSettings(settingsSnapshot);
        if (!isRecord(queuedSettings) || !isRecord(queuedSettings.sampler)) {
          continue;
        }
        const inputSeed = normalizeSeedValue(
          queuedSettings.sampler.seed,
          specialSeedRandom,
        );
        const queuedSeed = resolveQueuedSeed(node, inputSeed);
        queuedSettings.sampler.seed = queuedSeed;
        const serializedSettings = settingsToCompactJson(queuedSettings);
        if (typeof serializedSettings !== "string") {
          continue;
        }
        const workflowWrite = stageWorkflowSettingsValue(
          node,
          findWorkflowNode(queuedPrompt.workflow, node.id),
          serializedSettings,
        );
        if (!workflowWrite) {
          continue;
        }
        applyQueuedSettingsTransaction(
          queuedInputs,
          serializedSettings,
          workflowWrite,
        );
        commits.push({
          node,
          nodeId: String(node.id),
          queuedSeed,
          liveSeed: nextLiveSeed(
            queuedSettings.sampler.seed_after_generate,
            inputSeed,
            queuedSeed,
          ),
        });
      } catch {
        // One malformed generator must not prevent unrelated prompt nodes from
        // queueing. It remains untouched in the cloned payload.
      }
    }
    return commits.length ? { prompt: queuedPrompt, commits } : null;
  }

  function invalidCommitTargetIds(result) {
    try {
      const promptId = result?.prompt_id;
      if (promptId == null || String(promptId).trim() === "") {
        return null;
      }
      const nodeErrors = result?.node_errors;
      if (nodeErrors == null) {
        return new Set();
      }
      if (typeof nodeErrors === "string" || Array.isArray(nodeErrors)) {
        return nodeErrors.length > 0 ? null : new Set();
      }
      if (typeof nodeErrors === "object") {
        const invalidTargets = new Set();
        for (const [nodeId, details] of Object.entries(nodeErrors)) {
          invalidTargets.add(String(nodeId));
          if (Array.isArray(details?.dependent_outputs)) {
            for (const dependentOutput of details.dependent_outputs) {
              invalidTargets.add(String(dependentOutput));
            }
          }
        }
        return invalidTargets;
      }
      return nodeErrors ? null : new Set();
    } catch {
      // Treat malformed validation metadata conservatively without changing
      // the original accepted queue return into a local wrapper rejection.
      return null;
    }
  }

  function commitPreparedSeeds(transaction, result) {
    const invalidTargets = invalidCommitTargetIds(result);
    if (!invalidTargets) {
      return;
    }
    for (const commit of transaction.commits) {
      if (invalidTargets.has(commit.nodeId)) {
        continue;
      }
      try {
        commitLastQueuedSeed(commit.node, commit.queuedSeed);
      } catch {
        continue;
      }
      try {
        updateSeed(commit.node, commit.liveSeed, { markDirty: false });
      } catch {
        // The durable last-seed reservation is already committed. A local
        // panel/widget failure cannot reject the accepted queue result or block
        // another node's reservation and live-seed update.
      }
    }
  }

  /**
   * Wrap api.queuePrompt without owning the global hook. The original receiver,
   * argument tail, resolved value, and thrown/rejected error are preserved.
   *
   * @param {(...args: any[]) => any} queuePrompt
   */
  function wrapQueuePrompt(queuePrompt) {
    return async function (...args) {
      await loadOptionalDependencies({ retryErrors: true });
      const transaction = preparePrompt(args[1], args[2]);
      const queueArgs = transaction ? [...args] : args;
      if (transaction) {
        queueArgs[1] = transaction.prompt;
      }
      const result = await queuePrompt.apply(this, queueArgs);
      if (transaction) {
        commitPreparedSeeds(transaction, result);
      }
      return result;
    };
  }

  return {
    preparePrompt,
    wrapQueuePrompt,
  };
}

/**
 * Install the AiO queue wrapper once per queue owner. The owner marker remains
 * visible when another extension later wraps queuePrompt, so repeated setup
 * cannot hide and then stack another AiO wrapper.
 *
 * @param {any} queueHost
 * @param {{wrapQueuePrompt: (queuePrompt: (...args: any[]) => any) => (...args: any[]) => any}} runtime
 */
export function aioInstallGeneratorQueuePromptHook(queueHost, runtime) {
  if (
    !queueHost
    || typeof queueHost.queuePrompt !== "function"
    || queueHost[QUEUE_HOST_MARKER]
  ) {
    return false;
  }
  if (queueHost.queuePrompt[QUEUE_HOOK_MARKER]) {
    queueHost[QUEUE_HOST_MARKER] = true;
    return false;
  }
  const wrappedQueuePrompt = runtime.wrapQueuePrompt(queueHost.queuePrompt);
  wrappedQueuePrompt[QUEUE_HOOK_MARKER] = true;
  queueHost.queuePrompt = wrappedQueuePrompt;
  queueHost[QUEUE_HOST_MARKER] = true;
  return true;
}
