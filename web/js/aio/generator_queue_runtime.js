// @ts-check

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
 * @property {(node: any, seed: number, options: {lastQueuedSeed: number, markDirty: boolean}) => void} updateSeed
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

  function setWorkflowSettingsValue(node, workflowNode, value) {
    if (
      !workflowNode
      || !Array.isArray(workflowNode.widgets_values)
      || !Array.isArray(node?.widgets)
    ) {
      return;
    }
    const index = node.widgets.findIndex(
      (widget) => widget?.name === settingsWidgetName,
    );
    if (index < 0) {
      return;
    }
    while (workflowNode.widgets_values.length <= index) {
      workflowNode.widgets_values.push(null);
    }
    workflowNode.widgets_values[index] = value;
  }

  function candidateNodes(prompt) {
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
    return nodes.filter((node) => {
      if (!node) {
        return false;
      }
      try {
        return !isBypassed(node) && isRecord(output[String(node.id)]?.inputs);
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
   */
  function preparePrompt(prompt) {
    const nodes = candidateNodes(prompt);
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
        queuedInputs.generation_settings = serializedSettings;
        setWorkflowSettingsValue(
          node,
          findWorkflowNode(queuedPrompt.workflow, node.id),
          serializedSettings,
        );
        commits.push({
          node,
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

  function hasNodeErrors(result) {
    try {
      const nodeErrors = result?.node_errors;
      if (nodeErrors == null) {
        return false;
      }
      if (typeof nodeErrors === "string" || Array.isArray(nodeErrors)) {
        return nodeErrors.length > 0;
      }
      if (typeof nodeErrors === "object") {
        return Object.keys(nodeErrors).length > 0;
      }
      return !!nodeErrors;
    } catch {
      // Treat malformed validation metadata conservatively without changing
      // the original accepted queue return into a local wrapper rejection.
      return true;
    }
  }

  function commitPreparedSeeds(transaction) {
    for (const commit of transaction.commits) {
      try {
        updateSeed(commit.node, commit.liveSeed, {
          lastQueuedSeed: commit.queuedSeed,
          markDirty: false,
        });
      } catch {
        // A local panel/widget update cannot turn an already accepted queue
        // response into a rejection or block another node's seed commit.
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
      const transaction = preparePrompt(args[1]);
      const queueArgs = transaction ? [...args] : args;
      if (transaction) {
        queueArgs[1] = transaction.prompt;
      }
      const result = await queuePrompt.apply(this, queueArgs);
      if (transaction && !hasNodeErrors(result)) {
        commitPreparedSeeds(transaction);
      }
      return result;
    };
  }

  return {
    preparePrompt,
    wrapQueuePrompt,
  };
}
