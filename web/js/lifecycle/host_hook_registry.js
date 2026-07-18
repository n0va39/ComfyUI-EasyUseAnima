// @ts-check

const HOST_HOOK_REGISTRY = Symbol.for(
  "easyuse-anima.lifecycle.host-hook-registry.v1",
);
const HOST_HOOK_WRAPPER = Symbol.for(
  "easyuse-anima.lifecycle.host-hook-wrapper.v1",
);
const REGISTRY_VERSION = 1;

/** @returns {false} */
function noOpDispose() {
  return false;
}

/** @param {any} target */
function targetRegistry(target) {
  const existing = target?.[HOST_HOOK_REGISTRY];
  if (existing?.version === REGISTRY_VERSION && existing.methods instanceof Map) {
    return existing;
  }
  const registry = {
    version: REGISTRY_VERSION,
    methods: new Map(),
  };
  Object.defineProperty(target, HOST_HOOK_REGISTRY, {
    configurable: true,
    value: registry,
  });
  return registry;
}

/** @param {any} state */
function callbackEntries(state) {
  return [...state.callbacks.values()];
}

/** @param {any} state */
function callbacksOuterToInner(state) {
  return callbackEntries(state).reverse();
}

/**
 * @param {any} state
 * @param {any} thisArg
 * @param {any[]} args
 */
function invokeSerialize(state, thisArg, args) {
  const originalArgs = args;
  let callArgs = args;
  for (const entry of callbacksOuterToInner(state)) {
    const callback = entry.callbacks.beforeSerialize;
    if (typeof callback !== "function") {
      continue;
    }
    const context = {
      host: state.target,
      thisArg,
      args: callArgs,
      originalArgs,
    };
    callback(context);
    callArgs = Array.isArray(context.args) ? context.args : callArgs;
  }
  return state.original.apply(thisArg, callArgs);
}

/**
 * @param {any} state
 * @param {any} thisArg
 * @param {any[]} args
 */
function invokeQueueSync(state, thisArg, args) {
  const originalArgs = args;
  let callArgs = args;
  for (const entry of callbacksOuterToInner(state)) {
    const callback = entry.callbacks.beforeQueue;
    if (typeof callback !== "function") {
      continue;
    }
    const context = {
      host: state.target,
      thisArg,
      args: callArgs,
      originalArgs,
    };
    callback(context);
    callArgs = Array.isArray(context.args) ? context.args : callArgs;
  }
  return state.original.apply(thisArg, callArgs);
}

/**
 * Recursively model nested queue wrappers. Each entry's afterQueue callback
 * observes the resolve/reject result of the entries registered before it,
 * which preserves the unwind order of the legacy wrapper chain.
 *
 * @param {any} state
 * @param {any[]} entries
 * @param {number} index
 * @param {any} thisArg
 * @param {any[]} args
 * @param {any[]} originalArgs
 */
function invokeQueueLayer(state, entries, index, thisArg, args, originalArgs) {
  if (index >= entries.length) {
    return state.original.apply(thisArg, args);
  }

  const entry = entries[index];
  const beforeQueue = entry.callbacks.beforeQueue;
  const afterQueue = entry.callbacks.afterQueue;
  const context = {
    host: state.target,
    thisArg,
    args,
    originalArgs,
  };
  const callbackState = typeof beforeQueue === "function"
    ? beforeQueue(context)
    : undefined;
  const callArgs = Array.isArray(context.args) ? context.args : args;

  let result;
  try {
    result = invokeQueueLayer(
      state,
      entries,
      index + 1,
      thisArg,
      callArgs,
      originalArgs,
    );
  } catch (error) {
    if (typeof afterQueue === "function") {
      afterQueue({
        host: state.target,
        thisArg,
        args: callArgs,
        originalArgs,
        callbackState,
        ok: false,
        error,
      });
    }
    throw error;
  }

  if (typeof afterQueue !== "function") {
    return result;
  }
  return Promise.resolve(result).then(
    (value) => {
      afterQueue({
        host: state.target,
        thisArg,
        args: callArgs,
        originalArgs,
        callbackState,
        ok: true,
        result: value,
      });
      return value;
    },
    (error) => {
      afterQueue({
        host: state.target,
        thisArg,
        args: callArgs,
        originalArgs,
        callbackState,
        ok: false,
        error,
      });
      throw error;
    },
  );
}

/**
 * @param {any} state
 * @param {any} thisArg
 * @param {any[]} args
 */
async function invokeQueueAsync(state, thisArg, args) {
  return invokeQueueLayer(
    state,
    callbacksOuterToInner(state),
    0,
    thisArg,
    args,
    args,
  );
}

/**
 * @param {any} state
 * @param {any} thisArg
 * @param {any[]} args
 */
function invokeQueue(state, thisArg, args) {
  const hasAfterQueue = callbackEntries(state).some(
    (entry) => typeof entry.callbacks.afterQueue === "function",
  );
  return hasAfterQueue
    ? invokeQueueAsync(state, thisArg, args)
    : invokeQueueSync(state, thisArg, args);
}

/**
 * @param {any} state
 * @param {any} thisArg
 * @param {any[]} args
 */
function invokeGraphClear(state, thisArg, args) {
  const result = state.original.apply(thisArg, args);
  for (const entry of callbackEntries(state)) {
    const callback = entry.callbacks.onGraphClear;
    if (typeof callback === "function") {
      callback({
        host: state.target,
        thisArg,
        args,
        originalArgs: args,
        result,
      });
    }
  }
  return result;
}

/** @param {any} state */
function createWrapper(state) {
  const wrapper = function (...args) {
    if (!state.active || state.callbacks.size === 0) {
      return state.original.apply(this, args);
    }
    if (state.kind === "serialize") {
      return invokeSerialize(state, this, args);
    }
    if (state.kind === "queue") {
      return invokeQueue(state, this, args);
    }
    return invokeGraphClear(state, this, args);
  };
  Object.defineProperty(wrapper, HOST_HOOK_WRAPPER, {
    value: state,
  });
  return wrapper;
}

/**
 * @param {any} target
 * @param {string} methodName
 * @param {"serialize" | "queue" | "graph-clear"} kind
 */
function ensureMethodState(target, methodName, kind) {
  if (!target || typeof target[methodName] !== "function") {
    return null;
  }
  const registry = targetRegistry(target);
  const registered = registry.methods.get(methodName);
  if (registered?.active) {
    return registered;
  }

  const current = target[methodName];
  const staleState = current?.[HOST_HOOK_WRAPPER];
  if (
    staleState?.version === REGISTRY_VERSION
    && staleState.target === target
    && staleState.methodName === methodName
    && staleState.kind === kind
  ) {
    staleState.active = true;
    registry.methods.set(methodName, staleState);
    return staleState;
  }

  const state = {
    version: REGISTRY_VERSION,
    target,
    methodName,
    kind,
    original: current,
    wrapper: null,
    callbacks: new Map(),
    active: true,
  };
  state.wrapper = createWrapper(state);
  target[methodName] = state.wrapper;
  registry.methods.set(methodName, state);
  return state;
}

/** @param {any} state */
function releaseMethodState(state) {
  state.active = false;
  state.callbacks.clear();
  if (state.target[state.methodName] === state.wrapper) {
    state.target[state.methodName] = state.original;
  }
  const registry = state.target[HOST_HOOK_REGISTRY];
  if (registry?.methods?.get(state.methodName) === state) {
    registry.methods.delete(state.methodName);
  }
  if (
    registry?.methods?.size === 0
    && state.target[HOST_HOOK_REGISTRY] === registry
  ) {
    delete state.target[HOST_HOOK_REGISTRY];
  }
}

/**
 * @param {any} target
 * @param {string} methodName
 * @param {"serialize" | "queue" | "graph-clear"} kind
 * @param {any} owner
 * @param {Record<string, any>} callbacks
 */
function registerMethodCallbacks(target, methodName, kind, owner, callbacks) {
  const state = ensureMethodState(target, methodName, kind);
  if (!state || state.callbacks.has(owner)) {
    return noOpDispose;
  }
  const entry = { owner, callbacks };
  state.callbacks.set(owner, entry);
  let disposed = false;
  return () => {
    if (disposed || state.callbacks.get(owner) !== entry) {
      return false;
    }
    disposed = true;
    state.callbacks.delete(owner);
    if (state.callbacks.size === 0) {
      releaseMethodState(state);
    }
    return true;
  };
}

/**
 * Register one logical owner's global lifecycle callbacks. Later owners run
 * first for before hooks, matching nested wrapper installation. afterQueue and
 * onGraphClear unwind in the corresponding inner-to-outer order.
 *
 * Re-registering the same owner/target/method is an idempotent no-op. The
 * returned disposer removes only callbacks created by this registration call.
 *
 * @param {{
 *   owner: any,
 *   serializeHost?: any,
 *   queueHost?: any,
 *   graphHost?: any,
 *   beforeSerialize?: (context: any) => any,
 *   beforeQueue?: (context: any) => any,
 *   afterQueue?: (context: any) => any,
 *   onGraphClear?: (context: any) => any,
 * }} options
 */
export function registerHostHookCallbacks(options) {
  if (!options || options.owner == null) {
    throw new TypeError("A lifecycle hook owner is required.");
  }
  const disposers = [];
  if (typeof options.beforeSerialize === "function") {
    disposers.push(registerMethodCallbacks(
      options.serializeHost,
      "serialize",
      "serialize",
      options.owner,
      { beforeSerialize: options.beforeSerialize },
    ));
  }
  if (
    typeof options.beforeQueue === "function"
    || typeof options.afterQueue === "function"
  ) {
    disposers.push(registerMethodCallbacks(
      options.queueHost,
      "queuePrompt",
      "queue",
      options.owner,
      {
        beforeQueue: options.beforeQueue,
        afterQueue: options.afterQueue,
      },
    ));
  }
  if (typeof options.onGraphClear === "function") {
    disposers.push(registerMethodCallbacks(
      options.graphHost,
      "clear",
      "graph-clear",
      options.owner,
      { onGraphClear: options.onGraphClear },
    ));
  }

  let disposed = false;
  return () => {
    if (disposed) {
      return false;
    }
    disposed = true;
    let changed = false;
    for (const dispose of [...disposers].reverse()) {
      changed = dispose() || changed;
    }
    return changed;
  };
}
