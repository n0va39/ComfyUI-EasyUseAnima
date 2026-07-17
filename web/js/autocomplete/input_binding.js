// @ts-check

/**
 * Owns every DOM listener and delayed blur action for one autocomplete input.
 * Search authority and popup behavior remain injected so replacing or removing
 * an input can dispose this boundary without reaching through to host globals.
 *
 * @param {{
 *   input: any,
 *   state: any,
 *   owner: object,
 *   registry: Set<any>,
 *   controller: any,
 *   onBeforeDispose?: (input: any, state: any, ownsCurrentState: boolean) => void,
 *   getActiveState: () => any,
 *   hidePopup: (options?: { preserveController?: boolean }) => void,
 *   isTextEditingShortcut: (event: any) => boolean,
 *   handleBracketPreviewKeydown: (state: any, event: any) => boolean,
 *   forwardMiddlePan: (event: any) => null | false | true | (() => void),
 *   setActive: (index: number) => void,
 *   commitSuggestion: (state: any, entry: any, options?: any) => void,
 *   getCommitKey: () => string,
 *   setTimer: (callback: () => unknown, delay: number) => any,
 *   clearTimer: (handle: any) => void,
 * }} dependencies
 */
export function createAutocompleteInputBinding(dependencies) {
  const {
    input,
    state,
    owner,
    registry,
    controller,
    onBeforeDispose = () => {},
    getActiveState,
    hidePopup,
    isTextEditingShortcut,
    handleBracketPreviewKeydown,
    forwardMiddlePan,
    setActive,
    commitSuggestion,
    getCommitKey,
    setTimer,
    clearTimer,
  } = dependencies;
  let disposed = false;
  let blurTimer = null;
  let middlePanCleanup = null;
  const listeners = [];

  function listen(type, listener, options = false) {
    input.addEventListener(type, listener, options);
    listeners.push([type, listener, options]);
  }

  function activeForInput() {
    const active = getActiveState();
    return active?.input === input ? active : null;
  }

  function scheduleInputUpdate() {
    const preserveController = controller.isCompositionEndUpdatePending();
    if (activeForInput()) {
      hidePopup({ preserveController });
    }
    controller.scheduleUpdate();
  }

  function handleMiddlePanStart(event) {
    const cleanup = forwardMiddlePan(event);
    if (!cleanup) {
      return;
    }
    if (typeof cleanup === "function") {
      middlePanCleanup = cleanup;
    }
    hidePopup();
  }

  function handleMiddleAuxClick(event) {
    if (event.button !== 1) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
  }

  function handleCaretKeyup(event) {
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", "PageUp", "PageDown"].includes(event.key)) {
      controller.scheduleCaretUpdate();
    }
  }

  function handleBlur() {
    controller.invalidate();
    if (blurTimer != null) {
      clearTimer(blurTimer);
    }
    blurTimer = setTimer(() => {
      blurTimer = null;
      if (!disposed && activeForInput()) {
        hidePopup();
      }
    }, 120);
  }

  function handleTextEditingShortcut(event) {
    if (isTextEditingShortcut(event)) {
      event.stopPropagation();
    }
  }

  function handleBracketPreview(event) {
    if (!controller.isComposing(event) && handleBracketPreviewKeydown(state, event)) {
      controller.scheduleCaretUpdate();
    }
  }

  function handleNavigation(event) {
    if (controller.isComposing(event)) {
      return;
    }
    if (event.key === "Escape") {
      controller.invalidate();
      if (activeForInput()) {
        event.preventDefault();
        hidePopup();
      }
      return;
    }
    const active = activeForInput();
    if (!active) {
      return;
    }
    if (event.key === "Enter" && event.shiftKey) {
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive(active.index + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive(active.index - 1);
    } else if (
      (event.key === "Tab" && !event.shiftKey)
      || (event.key === "Enter" && getCommitKey() === "enter")
    ) {
      event.preventDefault();
      commitSuggestion(active, active.results[active.index], {
        suppressPopup: true,
      });
    }
  }

  const previousState = input.__easyuseAnimaAutocompleteState;
  if (previousState && previousState !== state) {
    if (typeof previousState.dispose === "function") {
      previousState.dispose();
    } else {
      previousState.binding?.dispose?.();
      previousState.controller?.dispose?.();
      if (input.__easyuseAnimaAutocompleteState === previousState) {
        delete input.__easyuseAnimaAutocompleteState;
        delete input.__easyuseAnimaAutocompleteHooked;
        delete input.__easyuseAnimaAutocompleteDispose;
        input.__easyuseAnimaAutocomplete = false;
      }
    }
  } else if (!previousState && input.__easyuseAnimaAutocompleteHooked) {
    const staleDispose = input.__easyuseAnimaAutocompleteDispose;
    if (typeof staleDispose === "function") {
      staleDispose();
    }
    if (!input.__easyuseAnimaAutocompleteState) {
      delete input.__easyuseAnimaAutocompleteHooked;
      delete input.__easyuseAnimaAutocompleteDispose;
      input.__easyuseAnimaAutocomplete = false;
    }
  }

  listen("compositionstart", controller.beginComposition);
  listen("compositionupdate", controller.scheduleUpdate);
  listen("compositionend", controller.endComposition);
  listen("input", scheduleInputUpdate);
  listen("focus", controller.updateNow);
  listen("click", controller.scheduleCaretUpdate);
  listen("mousedown", controller.scheduleCaretUpdate);
  listen("mouseup", controller.scheduleCaretUpdate);
  listen("pointerup", controller.scheduleCaretUpdate);
  listen("pointerdown", handleMiddlePanStart, true);
  listen("mousedown", handleMiddlePanStart, true);
  listen("auxclick", handleMiddleAuxClick, true);
  listen("keyup", handleCaretKeyup);
  listen("select", controller.scheduleCaretUpdate);
  listen("blur", handleBlur);
  listen("keydown", handleTextEditingShortcut);
  listen("keydown", handleBracketPreview);
  listen("keydown", handleNavigation);

  function dispose() {
    if (disposed) {
      return;
    }
    disposed = true;
    const ownsCurrentState = input.__easyuseAnimaAutocompleteState === state;
    onBeforeDispose(input, state, ownsCurrentState);
    if (blurTimer != null) {
      clearTimer(blurTimer);
      blurTimer = null;
    }
    middlePanCleanup?.();
    middlePanCleanup = null;
    for (const [type, listener, options] of listeners) {
      input.removeEventListener(type, listener, options);
    }
    listeners.length = 0;
    controller.dispose();
    registry.delete(input);
    state.binding = null;
    if (ownsCurrentState) {
      if (input.__easyuseAnimaAutocompleteDispose === dispose) {
        delete input.__easyuseAnimaAutocompleteDispose;
      }
      delete input.__easyuseAnimaAutocompleteState;
      delete input.__easyuseAnimaAutocompleteHooked;
      input.__easyuseAnimaAutocomplete = false;
    }
  }

  const binding = { dispose };
  state.owner = owner;
  state.binding = binding;
  state.dispose = dispose;
  input.__easyuseAnimaAutocompleteHooked = true;
  input.__easyuseAnimaAutocompleteState = state;
  input.__easyuseAnimaAutocompleteDispose = dispose;
  registry.add(input);
  return binding;
}
