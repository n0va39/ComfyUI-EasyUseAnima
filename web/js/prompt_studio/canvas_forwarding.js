// @ts-check

/** @typedef {import("./types.js").PromptStudioWindow} PromptStudioWindow */

// @ts-expect-error ComfyUI provides this host module at runtime.
import { app } from "../../../../scripts/app.js";
import {
  advancedEditorFromWheelEvent,
  consumeAdvancedEditorWheel,
  isMiddlePanExcludedTarget,
} from "./wheel.js";

let middlePanForwardActive = false;

/** @returns {PromptStudioWindow} */
function promptStudioWindow() {
  return /** @type {PromptStudioWindow} */ (window);
}

function dispatchCanvasMouseEvent(type, sourceEvent, overrides = {}) {
  const canvas = app.canvas?.canvas;
  if (!canvas) {
    return;
  }
  const event = new MouseEvent(type, {
    bubbles: true,
    cancelable: true,
    view: window,
    clientX: sourceEvent.clientX,
    clientY: sourceEvent.clientY,
    screenX: sourceEvent.screenX,
    screenY: sourceEvent.screenY,
    button: overrides.button ?? sourceEvent.button,
    buttons: overrides.buttons ?? sourceEvent.buttons,
    ctrlKey: sourceEvent.ctrlKey,
    shiftKey: sourceEvent.shiftKey,
    altKey: sourceEvent.altKey,
    metaKey: sourceEvent.metaKey,
  });
  Object.defineProperty(event, "__easyuseAnimaForwarded", { value: true });
  canvas.dispatchEvent(event);
}

function dispatchCanvasWheelEvent(sourceEvent) {
  const canvas = app.canvas?.canvas;
  if (!canvas) {
    return;
  }
  const event = new WheelEvent("wheel", {
    bubbles: true,
    cancelable: true,
    view: window,
    clientX: sourceEvent.clientX,
    clientY: sourceEvent.clientY,
    screenX: sourceEvent.screenX,
    screenY: sourceEvent.screenY,
    deltaX: sourceEvent.deltaX,
    deltaY: sourceEvent.deltaY,
    deltaZ: sourceEvent.deltaZ,
    deltaMode: sourceEvent.deltaMode,
    ctrlKey: sourceEvent.ctrlKey,
    shiftKey: sourceEvent.shiftKey,
    altKey: sourceEvent.altKey,
    metaKey: sourceEvent.metaKey,
  });
  Object.defineProperty(event, "__easyuseAnimaForwarded", { value: true });
  canvas.dispatchEvent(event);
}

function dispatchCanvasPointerEvent(type, sourceEvent, overrides = {}) {
  const canvas = app.canvas?.canvas;
  if (!canvas || typeof PointerEvent === "undefined") {
    return;
  }
  const event = new PointerEvent(type, {
    bubbles: true,
    cancelable: true,
    view: window,
    clientX: sourceEvent.clientX,
    clientY: sourceEvent.clientY,
    screenX: sourceEvent.screenX,
    screenY: sourceEvent.screenY,
    button: overrides.button ?? sourceEvent.button,
    buttons: overrides.buttons ?? sourceEvent.buttons,
    ctrlKey: sourceEvent.ctrlKey,
    shiftKey: sourceEvent.shiftKey,
    altKey: sourceEvent.altKey,
    metaKey: sourceEvent.metaKey,
    pointerId: sourceEvent.pointerId || 1,
    pointerType: sourceEvent.pointerType || "mouse",
    isPrimary: sourceEvent.isPrimary ?? true,
  });
  Object.defineProperty(event, "__easyuseAnimaForwarded", { value: true });
  canvas.dispatchEvent(event);
}

function isCanvasAreaEvent(event) {
  const canvas = app.canvas?.canvas;
  const rect = canvas?.getBoundingClientRect?.();
  if (!canvas || !rect || event.target === canvas) {
    return false;
  }
  return (
    event.clientX >= rect.left
    && event.clientX <= rect.right
    && event.clientY >= rect.top
    && event.clientY <= rect.bottom
  );
}

function shouldForwardMiddlePan(event) {
  return (
    !event.__easyuseAnimaForwarded
    && event.button === 1
    && isCanvasAreaEvent(event)
    && !isMiddlePanExcludedTarget(event.target)
  );
}

function startCanvasPanFromDom(event) {
  if (!shouldForwardMiddlePan(event)) {
    return false;
  }
  if (middlePanForwardActive) {
    event.preventDefault();
    event.stopPropagation();
    return true;
  }
  middlePanForwardActive = true;
  event.preventDefault();
  event.stopPropagation();
  if (document.activeElement instanceof HTMLElement || document.activeElement instanceof SVGElement) {
    document.activeElement.blur();
  }
  dispatchCanvasPointerEvent("pointerdown", event, { button: 1, buttons: 4 });
  dispatchCanvasMouseEvent("mousedown", event, { button: 1, buttons: 4 });

  const move = (moveEvent) => {
    if (moveEvent.__easyuseAnimaForwarded) {
      return;
    }
    moveEvent.preventDefault();
    moveEvent.stopPropagation();
    dispatchCanvasPointerEvent("pointermove", moveEvent, { button: 1, buttons: 4 });
    dispatchCanvasMouseEvent("mousemove", moveEvent, { button: 1, buttons: 4 });
  };
  const stop = (upEvent) => {
    if (upEvent.__easyuseAnimaForwarded) {
      return;
    }
    upEvent.preventDefault();
    upEvent.stopPropagation();
    dispatchCanvasPointerEvent("pointerup", upEvent, { button: 1, buttons: 0 });
    dispatchCanvasMouseEvent("mouseup", upEvent, { button: 1, buttons: 0 });
    middlePanForwardActive = false;
    document.removeEventListener("pointermove", move, true);
    document.removeEventListener("pointerup", stop, true);
    document.removeEventListener("pointercancel", stop, true);
    document.removeEventListener("mousemove", move, true);
    document.removeEventListener("mouseup", stop, true);
  };
  document.addEventListener("pointermove", move, true);
  document.addEventListener("pointerup", stop, true);
  document.addEventListener("pointercancel", stop, true);
  document.addEventListener("mousemove", move, true);
  document.addEventListener("mouseup", stop, true);
  return true;
}

function forwardAdvancedWheelToCanvas(event) {
  if (event.__easyuseAnimaForwarded) {
    return false;
  }
  const editor = advancedEditorFromWheelEvent(event);
  if (!editor) {
    return false;
  }
  if (consumeAdvancedEditorWheel(event, editor)) {
    return true;
  }
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation?.();
  dispatchCanvasWheelEvent(event);
  return true;
}

function installAdvancedWheelForwarder() {
  const hostWindow = promptStudioWindow();
  if (hostWindow.__easyuseAnimaWheelForwarderInstalled) {
    return;
  }
  hostWindow.__easyuseAnimaWheelForwarderInstalled = true;
  // Node 2.0 handles wheel on an ancestor of the DOM widget. Window capture
  // must decide ownership before that ancestor can zoom the canvas.
  hostWindow.addEventListener("wheel", forwardAdvancedWheelToCanvas, {
    capture: true,
    passive: false,
  });
}

function installMiddlePanForwarder() {
  const hostWindow = promptStudioWindow();
  if (hostWindow.__easyuseAnimaMiddlePanForwarderInstalled) {
    return;
  }
  hostWindow.__easyuseAnimaMiddlePanForwarderInstalled = true;
  document.addEventListener("pointerdown", startCanvasPanFromDom, true);
  document.addEventListener("mousedown", startCanvasPanFromDom, true);
  document.addEventListener("auxclick", (event) => {
    if (shouldForwardMiddlePan(event)) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);
}

export {
  forwardAdvancedWheelToCanvas,
  installAdvancedWheelForwarder,
  installMiddlePanForwarder,
};
