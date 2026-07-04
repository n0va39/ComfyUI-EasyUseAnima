// @ts-check

import { app } from "../../../../scripts/app.js";
import {
  canAdvancedEditorScrollWheelDelta,
  isMiddlePanExcludedTarget,
  shouldKeepAdvancedWheelEvent,
} from "./wheel.js";

let middlePanForwardActive = false;

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
  document.activeElement?.blur?.();
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
    return;
  }
  const editor = event.currentTarget;
  if (shouldKeepAdvancedWheelEvent(event, editor)) {
    return;
  }
  if (canAdvancedEditorScrollWheelDelta(editor, Number(event.deltaY) || 0)) {
    return;
  }
  event.preventDefault();
  event.stopPropagation();
  dispatchCanvasWheelEvent(event);
}

function installMiddlePanForwarder() {
  if (window.__easyuseAnimaMiddlePanForwarderInstalled) {
    return;
  }
  window.__easyuseAnimaMiddlePanForwarderInstalled = true;
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
  installMiddlePanForwarder,
};
