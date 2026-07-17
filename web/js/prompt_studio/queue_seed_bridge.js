// @ts-check

const QUEUE_SEED_BRIDGES = new WeakMap();

/**
 * Keep the Prompt Studio queue hook owned by one runtime while allowing the
 * independently registered Regional extension to share its node lifecycle and
 * visible seed publisher.
 *
 * @param {object} app
 */
function promptStudioQueueSeedBridge(app) {
  const existing = QUEUE_SEED_BRIDGES.get(app);
  if (existing) {
    return existing;
  }

  let runtime = null;
  let regionalSeedPublisher = null;
  const bridge = Object.freeze({
    bindRuntime(value) {
      runtime = value;
    },
    bindRegionalSeedPublisher(value) {
      regionalSeedPublisher = typeof value === "function" ? value : null;
    },
    attachNode(node) {
      return runtime?.attachNode?.(node) === true;
    },
    detachNode(node) {
      return runtime?.detachNode?.(node) === true;
    },
    publishRegionalSeed(node, seed) {
      if (typeof regionalSeedPublisher !== "function") {
        return false;
      }
      return regionalSeedPublisher(node, seed) !== false;
    },
    shouldApplyExecutedSeed(node, value) {
      return runtime?.shouldApplyExecutedSeed?.(node, value) !== false;
    },
  });
  QUEUE_SEED_BRIDGES.set(app, bridge);
  return bridge;
}

export {
  promptStudioQueueSeedBridge,
};
