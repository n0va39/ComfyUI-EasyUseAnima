// @ts-check

/**
 * @typedef {object} AutocompleteInputUpdateContext
 * @property {() => boolean} isCurrent
 * @property {(key: string, loader: (signal: AbortSignal) => Promise<any>) => Promise<any>} request
 */

/**
 * @typedef {object} AutocompleteInputControllerDependencies
 * @property {(context: AutocompleteInputUpdateContext) => Promise<void>} onUpdate
 * @property {(error: unknown, context: AutocompleteInputUpdateContext) => void | Promise<void>} onError
 * @property {(callback: () => unknown) => any} requestFrame
 * @property {(handle: any) => void} cancelFrame
 * @property {(callback: () => unknown, delay: number) => any} setTimer
 * @property {(handle: any) => void} clearTimer
 * @property {number} [debounceDelay]
 */

/**
 * @typedef {object} AutocompleteInputControllerHandle
 * @property {() => void} invalidate
 */

/**
 * @typedef {object} AutocompleteControllerState
 * @property {AutocompleteInputControllerHandle | null | undefined} [controller]
 */

/**
 * @typedef {object} InFlightRequestOwner
 * @property {Promise<any>} promise
 * @property {AbortController} controller
 * @property {() => void} abortLoaded
 */

function isAbortError(error) {
  return !!error && typeof error === "object" && error.name === "AbortError";
}

/**
 * Invalidate every distinct input controller that can still publish results.
 * The active popup state may be a shallow clone of its hooked input state, so
 * controller identity owns de-duplication rather than state identity.
 *
 * @param {Iterable<AutocompleteControllerState | null | undefined>} states
 * @param {AutocompleteControllerState | null | undefined} [activeState]
 */
export function invalidateAutocompleteControllerStates(states, activeState = null) {
  const controllers = new Set();
  for (const state of states) {
    if (state?.controller) {
      controllers.add(state.controller);
    }
  }
  if (activeState?.controller) {
    controllers.add(activeState.controller);
  }
  for (const controller of controllers) {
    controller.invalidate();
  }
}

/**
 * Own one autocomplete input's scheduled updates, composition state, and
 * asynchronous request authority. DOM listeners and popup rendering stay in
 * the entry module; this controller only decides which update is current.
 *
 * @param {AutocompleteInputControllerDependencies} dependencies
 */
export function createAutocompleteInputController(dependencies) {
  const {
    onUpdate,
    onError,
    requestFrame,
    cancelFrame,
    setTimer,
    clearTimer,
    debounceDelay = 120,
  } = dependencies;
  let disposed = false;
  let composing = false;
  let generation = 0;
  let pendingTimer = null;
  let pendingFrame = null;
  let compositionEndFramePending = false;
  /** @type {Map<string, InFlightRequestOwner>} */
  const inFlight = new Map();

  function cancelScheduledUpdate() {
    if (pendingTimer != null) {
      clearTimer(pendingTimer);
      pendingTimer = null;
    }
    if (pendingFrame != null) {
      cancelFrame(pendingFrame);
      pendingFrame = null;
    }
    compositionEndFramePending = false;
  }

  function supersedeCurrentUpdate() {
    generation += 1;
  }

  /**
   * Cancel obsolete request owners without disturbing a same-key single flight.
   * Starting the replacement loader first lets shared adapter loads retain a
   * current consumer before the stale consumer releases its ownership.
   *
   * @param {string | null} keptKey
   */
  function cancelInFlightExcept(keptKey) {
    for (const [key, owner] of inFlight) {
      if (key === keptKey) {
        continue;
      }
      inFlight.delete(key);
      owner.controller.abort();
      owner.abortLoaded();
    }
  }

  function cancelInFlightRequests() {
    cancelInFlightExcept(null);
  }

  /**
   * @param {string} key
   * @param {(signal: AbortSignal) => Promise<any>} loader
   * @returns {Promise<any>}
   */
  function request(key, loader) {
    if (disposed) {
      return Promise.resolve(undefined);
    }
    const requestKey = String(key);
    const pending = inFlight.get(requestKey);
    if (pending) {
      cancelInFlightExcept(requestKey);
      return pending.promise;
    }
    const controller = new AbortController();
    /** @type {any} */
    let loaded;
    try {
      loaded = loader(controller.signal);
    } catch (error) {
      loaded = Promise.reject(error);
    }
    const abortLoaded = typeof loaded?.abort === "function"
      ? () => loaded.abort()
      : () => {};
    const promise = Promise.resolve(loaded);
    const owner = { promise, controller, abortLoaded };
    inFlight.set(requestKey, owner);
    cancelInFlightExcept(requestKey);
    const release = () => {
      if (inFlight.get(requestKey) === owner) {
        inFlight.delete(requestKey);
      }
    };
    promise.then(release, release);
    return promise;
  }

  async function updateNow() {
    if (disposed) {
      return;
    }
    cancelScheduledUpdate();
    const updateGeneration = ++generation;
    let requestCalled = false;
    const context = {
      isCurrent: () => !disposed && updateGeneration === generation,
      request: (key, loader) => {
        requestCalled = true;
        return request(key, loader);
      },
    };
    try {
      await onUpdate(context);
    } catch (error) {
      if (context.isCurrent() && !isAbortError(error)) {
        await onError(error, context);
      }
    } finally {
      if (context.isCurrent() && !requestCalled) {
        cancelInFlightRequests();
      }
    }
  }

  function scheduleUpdate() {
    if (disposed) {
      return;
    }
    if (isCompositionEndUpdatePending()) {
      return;
    }
    supersedeCurrentUpdate();
    cancelScheduledUpdate();
    pendingTimer = setTimer(() => {
      pendingTimer = null;
      return updateNow();
    }, debounceDelay);
  }

  function scheduleFrameUpdate(fromCompositionEnd) {
    if (disposed) {
      return;
    }
    supersedeCurrentUpdate();
    cancelScheduledUpdate();
    compositionEndFramePending = fromCompositionEnd;
    pendingFrame = requestFrame(() => {
      pendingFrame = null;
      compositionEndFramePending = false;
      return updateNow();
    });
  }

  function scheduleCaretUpdate() {
    scheduleFrameUpdate(false);
  }

  function isCompositionEndUpdatePending() {
    return !disposed && compositionEndFramePending && pendingFrame != null;
  }

  function beginComposition() {
    if (disposed) {
      return;
    }
    composing = true;
    supersedeCurrentUpdate();
    cancelScheduledUpdate();
    cancelInFlightRequests();
  }

  function endComposition() {
    if (disposed) {
      return;
    }
    composing = false;
    scheduleFrameUpdate(true);
  }

  function isComposing(event = null) {
    return composing || !!event?.isComposing || event?.keyCode === 229;
  }

  function invalidate() {
    if (disposed) {
      return;
    }
    supersedeCurrentUpdate();
    cancelScheduledUpdate();
    cancelInFlightRequests();
  }

  function dispose() {
    if (disposed) {
      return;
    }
    disposed = true;
    generation += 1;
    composing = false;
    cancelScheduledUpdate();
    cancelInFlightRequests();
  }

  return {
    beginComposition,
    dispose,
    endComposition,
    invalidate,
    isComposing,
    isCompositionEndUpdatePending,
    scheduleCaretUpdate,
    scheduleUpdate,
    updateNow,
  };
}
