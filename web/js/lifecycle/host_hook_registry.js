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
function methodRecordFor(target, methodName, kind) {
  const registry = targetRegistry(target);
  let record = registry.methods.get(methodName);
  if (!record) {
    record = {
      registry,
      target,
      methodName,
      kind,
      segments: new Set(),
      owners: new Map(),
      topState: null,
    };
    registry.methods.set(methodName, record);
  }
  return record;
}

/** @param {any} record */
function ensureMethodState(record) {
  const { target, methodName, kind } = record;
  const current = target[methodName];
  if (record.topState?.active && current === record.topState.wrapper) {
    return record.topState;
  }

  const staleState = current?.[HOST_HOOK_WRAPPER];
  if (
    staleState?.version === REGISTRY_VERSION
    && staleState.target === target
    && staleState.methodName === methodName
    && staleState.kind === kind
    && staleState.callbacks.size === 0
  ) {
    staleState.active = true;
    staleState.methodRecord = record;
    record.segments.add(staleState);
    record.topState = staleState;
    return staleState;
  }

  const state = {
    version: REGISTRY_VERSION,
    target,
    methodName,
    kind,
    methodRecord: record,
    original: current,
    wrapper: null,
    callbacks: new Map(),
    active: true,
  };
  state.wrapper = createWrapper(state);
  target[methodName] = state.wrapper;
  record.segments.add(state);
  record.topState = state;
  return state;
}

/** @param {any} state */
function releaseMethodState(state) {
  state.active = false;
  state.callbacks.clear();
  if (state.target[state.methodName] === state.wrapper) {
    state.target[state.methodName] = state.original;
  }
  const record = state.methodRecord;
  record?.segments?.delete(state);
  if (record?.topState === state) {
    const currentState = state.target[state.methodName]?.[HOST_HOOK_WRAPPER];
    record.topState = currentState?.active && record.segments.has(currentState)
      ? currentState
      : null;
  }
  if (record?.segments?.size === 0) {
    record.registry.methods.delete(state.methodName);
  }
  const registry = record?.registry;
  if (
    registry?.methods?.size === 0
    && state.target[HOST_HOOK_REGISTRY] === registry
  ) {
    delete state.target[HOST_HOOK_REGISTRY];
  }
}

/** @param {any} record @param {any} state @param {any} owner @param {any} entry */
function createCallbackDisposer(record, state, owner, entry) {
  let disposed = false;
  return () => {
    const current = record.owners.get(owner);
    if (
      disposed
      || current?.state !== state
      || current?.entry !== entry
      || state.callbacks.get(owner) !== entry
    ) {
      return false;
    }
    disposed = true;
    record.owners.delete(owner);
    state.callbacks.delete(owner);
    if (state.callbacks.size === 0) {
      releaseMethodState(state);
    }
    return true;
  };
}

/**
 * @param {any} target
 * @param {string} methodName
 * @param {"serialize" | "queue" | "graph-clear"} kind
 * @param {any} owner
 * @param {Record<string, any>} callbacks
 */
function registerMethodCallbacks(target, methodName, kind, owner, callbacks) {
  if (!target || typeof target[methodName] !== "function") {
    return noOpDispose;
  }
  const record = methodRecordFor(target, methodName, kind);
  if (record.owners.has(owner)) {
    return noOpDispose;
  }

  const state = ensureMethodState(record);
  const entry = { owner, callbacks };
  state.callbacks.set(owner, entry);
  record.owners.set(owner, { state, entry });
  return createCallbackDisposer(record, state, owner, entry);
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

/**
 * Own a composition root's current global-hook leases on a collision-safe host
 * Symbol. A newer runtime claims the host by disposing the previous runtime's
 * hook leases first. Only leases installed through this lifecycle are owned;
 * listeners, locale watchers, DOM state, and node-local resources remain out
 * of scope.
 *
 * @param {any} host
 * @param {symbol} owner
 */
export function createHostHookRuntimeLifecycle(host, owner) {
  if (!host || typeof owner !== "symbol") {
    throw new TypeError("A host object and Symbol runtime owner are required.");
  }
  const leases = new Map();

  function isOwner() {
    return host[owner] === lifecycle;
  }

  function claim() {
    if (isOwner()) {
      return false;
    }
    const previous = host[owner];
    previous?.dispose?.();
    host[owner] = lifecycle;
    return true;
  }

  /**
   * @param {any} key
   * @param {() => (() => boolean)} installer
   * @param {{ replace?: boolean }} [options]
   */
  function install(key, installer, options = {}) {
    claim();
    const previous = leases.get(key);
    if (previous && options.replace !== true) {
      return false;
    }
    if (previous) {
      leases.delete(key);
      previous();
    }
    const dispose = installer();
    if (typeof dispose !== "function") {
      throw new TypeError("A host hook installer must return a disposer.");
    }
    leases.set(key, dispose);
    return true;
  }

  function dispose() {
    let changed = false;
    let cleanupError = null;
    for (const release of [...leases.values()].reverse()) {
      try {
        changed = release() || changed;
      } catch (error) {
        cleanupError ||= error;
      }
    }
    leases.clear();
    if (isOwner()) {
      delete host[owner];
    }
    if (cleanupError) {
      throw cleanupError;
    }
    return changed;
  }

  const lifecycle = {
    claim,
    dispose,
    install,
    isOwner,
  };
  return lifecycle;
}
