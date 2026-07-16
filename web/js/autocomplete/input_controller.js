// @ts-check

/**
 * @typedef {object} AutocompleteInputUpdateContext
 * @property {() => boolean} isCurrent
 * @property {(key: string, loader: () => Promise<any>) => Promise<any>} request
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

  function request(key, loader) {
    if (disposed) {
      return Promise.resolve(undefined);
    }
    const requestKey = String(key);
    const pending = inFlight.get(requestKey);
    if (pending) {
      return pending;
    }
    let promise;
    try {
      promise = Promise.resolve(loader());
    } catch (error) {
      promise = Promise.reject(error);
    }
    inFlight.set(requestKey, promise);
    const release = () => {
      if (inFlight.get(requestKey) === promise) {
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
    const context = {
      isCurrent: () => !disposed && updateGeneration === generation,
      request,
    };
    try {
      await onUpdate(context);
    } catch (error) {
      if (context.isCurrent()) {
        await onError(error, context);
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
    inFlight.clear();
  }

  function dispose() {
    if (disposed) {
      return;
    }
    disposed = true;
    generation += 1;
    composing = false;
    cancelScheduledUpdate();
    inFlight.clear();
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
