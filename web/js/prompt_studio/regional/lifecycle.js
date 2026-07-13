// @ts-check

const REGIONAL_LIFECYCLE_PROPERTY = "__easyuseAnimaRegionalLifecycle";
const REGIONAL_DISPOSED_PROPERTY = "__easyuseAnimaRegionalDisposed";

/** @param {any} node */
function lifecycleState(node) {
  if (!node) {
    return null;
  }
  if (!node[REGIONAL_LIFECYCLE_PROPERTY]) {
    node[REGIONAL_LIFECYCLE_PROPERTY] = {
      frames: new Map(),
      cleanups: new Map(),
    };
  }
  return node[REGIONAL_LIFECYCLE_PROPERTY];
}

/** @param {any} node */
function activateRegionalNodeLifecycle(node) {
  if (!node) {
    return null;
  }
  node[REGIONAL_DISPOSED_PROPERTY] = false;
  return lifecycleState(node);
}

/** @param {any} node */
function isRegionalNodeDisposed(node) {
  return !node || node[REGIONAL_DISPOSED_PROPERTY] === true;
}

/**
 * Schedule one node-owned animation frame per key. Replacing a key cancels the
 * stale callback, which keeps rerenders and node removal from reviving old DOM.
 *
 * @param {any} node
 * @param {string} key
 * @param {() => void} callback
 * @param {{ replace?: boolean }} [options]
 */
function scheduleRegionalNodeFrame(node, key, callback, options = {}) {
  if (isRegionalNodeDisposed(node)) {
    return 0;
  }
  const state = lifecycleState(node);
  if (!state) {
    return 0;
  }
  const existing = state.frames.get(key);
  if (existing != null) {
    if (options.replace !== true) {
      return existing;
    }
    cancelAnimationFrame(existing);
    state.frames.delete(key);
  }
  const frame = requestAnimationFrame(() => {
    if (state.frames.get(key) !== frame) {
      return;
    }
    state.frames.delete(key);
    if (!isRegionalNodeDisposed(node)) {
      callback();
    }
  });
  state.frames.set(key, frame);
  return frame;
}

/**
 * @param {any} node
 * @param {string} key
 */
function cancelRegionalNodeFrame(node, key) {
  const state = node?.[REGIONAL_LIFECYCLE_PROPERTY];
  const frame = state?.frames?.get?.(key);
  if (frame == null) {
    return false;
  }
  cancelAnimationFrame(frame);
  state.frames.delete(key);
  return true;
}

/**
 * Register one cleanup per node/key. Replacing a resource first disposes the
 * previous resource, so only the current modal, popover, observer, or listener
 * group remains owned by the node.
 *
 * @param {any} node
 * @param {string} key
 * @param {() => void} cleanup
 */
function setRegionalNodeCleanup(node, key, cleanup) {
  if (isRegionalNodeDisposed(node)) {
    cleanup();
    return false;
  }
  clearRegionalNodeCleanup(node, key);
  const state = lifecycleState(node);
  state?.cleanups.set(key, cleanup);
  return true;
}

/**
 * @param {any} node
 * @param {string} key
 * @param {boolean} [run]
 */
function clearRegionalNodeCleanup(node, key, run = true) {
  const state = node?.[REGIONAL_LIFECYCLE_PROPERTY];
  const cleanup = state?.cleanups?.get?.(key);
  if (!cleanup) {
    return false;
  }
  state.cleanups.delete(key);
  if (run) {
    cleanup();
  }
  return true;
}

/** @param {any} node */
function disposeRegionalNodeLifecycle(node) {
  if (!node || isRegionalNodeDisposed(node)) {
    return false;
  }
  node[REGIONAL_DISPOSED_PROPERTY] = true;
  const state = node[REGIONAL_LIFECYCLE_PROPERTY];
  if (state) {
    for (const frame of state.frames.values()) {
      cancelAnimationFrame(frame);
    }
    state.frames.clear();
    const cleanups = [...state.cleanups.values()];
    state.cleanups.clear();
    for (const cleanup of cleanups) {
      try {
        cleanup();
      } catch (error) {
        console.warn("EasyUse Anima Regional cleanup failed", error);
      }
    }
  }
  delete node[REGIONAL_LIFECYCLE_PROPERTY];
  return true;
}

export {
  activateRegionalNodeLifecycle,
  cancelRegionalNodeFrame,
  clearRegionalNodeCleanup,
  disposeRegionalNodeLifecycle,
  isRegionalNodeDisposed,
  scheduleRegionalNodeFrame,
  setRegionalNodeCleanup,
};
