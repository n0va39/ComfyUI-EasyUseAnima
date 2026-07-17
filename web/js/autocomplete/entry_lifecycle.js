// @ts-check

const AUTOCOMPLETE_ENTRY_OWNER = "__easyuseAnimaAutocompleteEntryOwner";
const AUTOCOMPLETE_ENTRY_GENERATION = "__easyuseAnimaAutocompleteEntryGeneration";
const EXTERNAL_AUTOCOMPLETE_DISPOSE = "__easyuseAnimaExternalAutocompleteDispose";

/**
 * Register a Prompt Studio or other externally-created DOM input with the
 * autocomplete entry. The call site keeps one stable disposer even when the
 * entry is installed after the input or replaced by a newer entry owner.
 *
 * @param {any} hostWindow
 * @param {any} input
 * @param {any} [options]
 * @returns {null | (() => void)}
 */
export function registerExternalAutocompleteInput(hostWindow, input, options = {}) {
  if (!input) {
    return null;
  }
  disposeExternalAutocompleteInput(hostWindow, input);

  let disposed = false;
  let boundDispose = null;
  const pendingEntry = {
    input,
    options,
    onBound(dispose) {
      if (disposed) {
        dispose?.();
        return;
      }
      boundDispose = typeof dispose === "function" ? dispose : null;
    },
  };

  const dispose = () => {
    if (disposed) {
      return;
    }
    disposed = true;
    const pending = hostWindow.__easyuseAnimaPendingAutocompleteInputs;
    if (Array.isArray(pending)) {
      hostWindow.__easyuseAnimaPendingAutocompleteInputs = pending.filter(
        (entry) => entry !== pendingEntry,
      );
    }
    const currentDispose = input.__easyuseAnimaAutocompleteDispose;
    const ownedDispose = boundDispose;
    ownedDispose?.();
    boundDispose = null;
    if (typeof currentDispose === "function" && currentDispose !== ownedDispose) {
      currentDispose();
    }
    if (input[EXTERNAL_AUTOCOMPLETE_DISPOSE] === dispose) {
      delete input[EXTERNAL_AUTOCOMPLETE_DISPOSE];
    }
  };

  input[EXTERNAL_AUTOCOMPLETE_DISPOSE] = dispose;
  if (typeof hostWindow.easyuseAnimaHookAutocompleteInput === "function") {
    pendingEntry.onBound(hostWindow.easyuseAnimaHookAutocompleteInput(input, options));
  } else {
    hostWindow.__easyuseAnimaPendingAutocompleteInputs ||= [];
    hostWindow.__easyuseAnimaPendingAutocompleteInputs.push(pendingEntry);
  }
  return dispose;
}

/** @param {any} hostWindow @param {any} input */
export function disposeExternalAutocompleteInput(hostWindow, input) {
  if (!input) {
    return;
  }
  const dispose = input[EXTERNAL_AUTOCOMPLETE_DISPOSE];
  if (typeof dispose === "function") {
    dispose();
    return;
  }
  const pending = hostWindow?.__easyuseAnimaPendingAutocompleteInputs;
  if (Array.isArray(pending)) {
    hostWindow.__easyuseAnimaPendingAutocompleteInputs = pending.filter(
      (entry) => entry?.input !== input,
    );
  }
  input.__easyuseAnimaAutocompleteDispose?.();
}

/** @param {any} hostWindow @param {any} container */
export function disposeExternalAutocompleteInputs(hostWindow, container) {
  for (const input of container?.querySelectorAll?.("textarea, input") || []) {
    disposeExternalAutocompleteInput(hostWindow, input);
  }
}

/**
 * Owns the Autocomplete entry's process-wide hooks. Installation is
 * idempotent for one owner; a newer owner disposes the previous listener,
 * timer, input, and prototype-wrapper closure before taking authority.
 *
 * @param {{
 *   hostWindow: any,
 *   hostDocument: any,
 *   hookInput: (input: any, options?: any) => any,
 *   hookFocusedInput: (input: any) => void,
 *   entryTooltip: (entry: any) => any,
 *   handleScroll: (event: any) => void,
 *   handleWheel: (event: any) => void,
 *   handleOutsidePointer: (event: any) => void,
 *   handleSelectionChange: (event: any) => void,
 *   handleResize: (event: any) => void,
 *   handleSettingsUpdated: (event: any) => void,
 *   hookNode: (node: any, nodeData: any) => void,
 *   disposeInputs: () => void,
 *   disposeUi: () => void,
 *   setTimer?: (callback: () => void, delay: number) => any,
 *   clearTimer?: (handle: any) => void,
 * }} dependencies
 */
export function createAutocompleteEntryLifecycle(dependencies) {
  const {
    hostWindow,
    hostDocument,
    hookInput,
    hookFocusedInput,
    entryTooltip,
    handleScroll,
    handleWheel,
    handleOutsidePointer,
    handleSelectionChange,
    handleResize,
    handleSettingsUpdated,
    hookNode,
    disposeInputs,
    disposeUi,
    setTimer = (callback, delay) => setTimeout(callback, delay),
    clearTimer = (handle) => clearTimeout(handle),
  } = dependencies;
  const listeners = [];
  const timers = new Set();
  const wrappers = new Map();
  const generation = (Number(hostWindow[AUTOCOMPLETE_ENTRY_GENERATION]) || 0) + 1;
  hostWindow[AUTOCOMPLETE_ENTRY_GENERATION] = generation;
  let installed = false;

  const externalHook = (input, options = {}) => hookInput(input, options);
  const tooltipHook = (entry) => entryTooltip(entry);
  const focusHook = (event) => hookFocusedInput(event?.target);

  function listen(target, type, listener, options = false) {
    target.addEventListener(type, listener, options);
    listeners.push([target, type, listener, options]);
  }

  function isActive() {
    return installed && hostWindow[AUTOCOMPLETE_ENTRY_OWNER] === lifecycle;
  }

  function install() {
    if (hostWindow[AUTOCOMPLETE_ENTRY_GENERATION] !== generation) {
      return false;
    }
    if (isActive()) {
      return false;
    }
    const previousOwner = hostWindow[AUTOCOMPLETE_ENTRY_OWNER];
    if (previousOwner && previousOwner !== lifecycle) {
      previousOwner.dispose?.();
    }
    installed = true;
    hostWindow[AUTOCOMPLETE_ENTRY_OWNER] = lifecycle;
    hostWindow.__easyuseAnimaPendingAutocompleteInputs ||= [];
    hostWindow.easyuseAnimaHookAutocompleteInput = externalHook;
    hostWindow.easyuseAnimaAutocompleteEntryTooltip = tooltipHook;

    listen(hostDocument, "focusin", focusHook, true);
    listen(hostDocument, "scroll", handleScroll, true);
    listen(hostDocument, "wheel", handleWheel, true);
    listen(hostDocument, "pointerdown", handleOutsidePointer, true);
    listen(hostDocument, "mousedown", handleOutsidePointer, true);
    listen(hostDocument, "selectionchange", handleSelectionChange);
    listen(hostWindow, "resize", handleResize);
    listen(hostWindow, "easyuse-anima-settings-updated", handleSettingsUpdated);

    const pending = hostWindow.__easyuseAnimaPendingAutocompleteInputs || [];
    hostWindow.__easyuseAnimaPendingAutocompleteInputs = [];
    for (const item of pending) {
      const dispose = hookInput(item?.input, item?.options || {});
      item?.onBound?.(dispose);
    }
    hookFocusedInput(hostDocument.activeElement);
    return true;
  }

  function schedule(callback, delay) {
    if (!isActive()) {
      return null;
    }
    let handle = null;
    handle = setTimer(() => {
      timers.delete(handle);
      if (isActive()) {
        callback();
      }
    }, delay);
    timers.add(handle);
    return handle;
  }

  function installNodeTypeHooks(nodeType, nodeData) {
    if (!isActive() || !nodeType?.prototype || wrappers.has(nodeType)) {
      return false;
    }
    const prototype = nodeType.prototype;
    const hadOwnCreated = Object.prototype.hasOwnProperty.call(prototype, "onNodeCreated");
    const hadOwnConfigure = Object.prototype.hasOwnProperty.call(prototype, "onConfigure");
    const originalCreated = prototype.onNodeCreated;
    const originalConfigure = prototype.onConfigure;
    const wrappedCreated = function (...args) {
      const result = originalCreated?.apply(this, args);
      if (isActive()) {
        hookNode(this, nodeData);
      }
      return result;
    };
    const wrappedConfigure = function (...args) {
      const result = originalConfigure?.apply(this, args);
      if (isActive()) {
        hookNode(this, nodeData);
      }
      return result;
    };
    prototype.onNodeCreated = wrappedCreated;
    prototype.onConfigure = wrappedConfigure;
    wrappers.set(nodeType, {
      prototype,
      hadOwnCreated,
      hadOwnConfigure,
      originalCreated,
      originalConfigure,
      wrappedCreated,
      wrappedConfigure,
    });
    return true;
  }

  function dispose() {
    if (!installed) {
      return;
    }
    installed = false;
    for (const handle of timers) {
      clearTimer(handle);
    }
    timers.clear();
    for (const [target, type, listener, options] of listeners) {
      target.removeEventListener(type, listener, options);
    }
    listeners.length = 0;
    for (const record of wrappers.values()) {
      if (record.prototype.onNodeCreated === record.wrappedCreated) {
        if (record.hadOwnCreated) {
          record.prototype.onNodeCreated = record.originalCreated;
        } else {
          delete record.prototype.onNodeCreated;
        }
      }
      if (record.prototype.onConfigure === record.wrappedConfigure) {
        if (record.hadOwnConfigure) {
          record.prototype.onConfigure = record.originalConfigure;
        } else {
          delete record.prototype.onConfigure;
        }
      }
    }
    wrappers.clear();
    disposeInputs();
    disposeUi();
    if (hostWindow.easyuseAnimaHookAutocompleteInput === externalHook) {
      delete hostWindow.easyuseAnimaHookAutocompleteInput;
    }
    if (hostWindow.easyuseAnimaAutocompleteEntryTooltip === tooltipHook) {
      delete hostWindow.easyuseAnimaAutocompleteEntryTooltip;
    }
    if (hostWindow[AUTOCOMPLETE_ENTRY_OWNER] === lifecycle) {
      delete hostWindow[AUTOCOMPLETE_ENTRY_OWNER];
    }
  }

  const lifecycle = {
    dispose,
    install,
    installNodeTypeHooks,
    isActive,
    schedule,
  };
  return lifecycle;
}
