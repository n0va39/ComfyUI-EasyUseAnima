// @ts-check

// @ts-expect-error ComfyUI provides this host module at runtime.
import { app } from "../../../../scripts/app.js";

const RESIZE_EDGE_SLOP_PX = 42;
const RECENT_POINTER_MS = 350;

const resizePointerState = {
  active: false,
  pointerId: null,
  x: 0,
  y: 0,
  lastAt: 0,
};

function nowMs() {
  return Number(globalThis.performance?.now?.()) || Date.now();
}

function pointerId(event) {
  return event?.pointerId ?? "mouse";
}

function updateResizePointer(event, active) {
  if (!event || typeof event.clientX !== "number" || typeof event.clientY !== "number") {
    return;
  }
  resizePointerState.active = active;
  resizePointerState.pointerId = pointerId(event);
  resizePointerState.x = event.clientX;
  resizePointerState.y = event.clientY;
  resizePointerState.lastAt = nowMs();
}

function moveResizePointer(event) {
  const id = pointerId(event);
  if (
    resizePointerState.pointerId !== null
    && id !== resizePointerState.pointerId
  ) {
    return;
  }
  const buttons = Number(event?.buttons) || 0;
  updateResizePointer(event, buttons > 0);
}

function finishResizePointer(event) {
  const id = pointerId(event);
  if (
    resizePointerState.pointerId !== null
    && id !== resizePointerState.pointerId
  ) {
    return;
  }
  updateResizePointer(event, false);
}

function pushRect(rects, rect) {
  if (
    rect
    && Number.isFinite(rect.left)
    && Number.isFinite(rect.top)
    && Number.isFinite(rect.right)
    && Number.isFinite(rect.bottom)
    && rect.right > rect.left
    && rect.bottom > rect.top
  ) {
    rects.push(rect);
  }
}

function installNodeResizePointerTracker() {
  if (globalThis.__easyuseAnimaNodeResizePointerTrackerInstalled || typeof document === "undefined") {
    return;
  }
  globalThis.__easyuseAnimaNodeResizePointerTrackerInstalled = true;
  document.addEventListener("pointerdown", (event) => updateResizePointer(event, true), true);
  document.addEventListener("pointermove", moveResizePointer, true);
  document.addEventListener("pointerup", finishResizePointer, true);
  document.addEventListener("pointercancel", finishResizePointer, true);
  document.addEventListener("mousedown", (event) => updateResizePointer(event, true), true);
  document.addEventListener("mousemove", moveResizePointer, true);
  document.addEventListener("mouseup", finishResizePointer, true);
}

function elementScreenRect(element) {
  const rect = element?.getBoundingClientRect?.();
  if (!rect) {
    return null;
  }
  return {
    left: rect.left,
    top: rect.top,
    right: rect.right,
    bottom: rect.bottom,
  };
}

function nodeDomScreenRects(node) {
  const rects = [];
  const candidates = [
    node?.__easyuseAnimaAdvancedEditorEl,
    node?.__easyuseAnimaAdvancedDomWidget?.element,
    node?.__easyuseAnimaGeneratorPanelEl,
    node?.__easyuseAnimaGeneratorPanelWidget?.element,
  ];
  for (const element of candidates) {
    if (!(element instanceof HTMLElement)) {
      continue;
    }
    const nodeElement = element.closest?.(".lg-node")
      || element.closest?.("[data-node-id]")
      || element;
    pushRect(rects, elementScreenRect(nodeElement));
  }
  return rects;
}

function canvasNodeScreenRect(node) {
  const canvas = app?.canvas;
  const canvasElement = canvas?.canvas;
  const canvasRect = canvasElement?.getBoundingClientRect?.();
  const scale = Number(canvas?.ds?.scale) || 1;
  const offset = Array.isArray(canvas?.ds?.offset) ? canvas.ds.offset : [0, 0];
  const pos = Array.isArray(node?.pos) ? node.pos : [0, 0];
  const size = Array.isArray(node?.size) ? node.size : [0, 0];
  if (!canvasRect || !Number.isFinite(scale) || scale <= 0) {
    return null;
  }
  const left = canvasRect.left + ((Number(pos[0]) || 0) + (Number(offset[0]) || 0)) * scale;
  const top = canvasRect.top + ((Number(pos[1]) || 0) + (Number(offset[1]) || 0)) * scale;
  const width = Math.max(0, (Number(size[0]) || 0) * scale);
  const height = Math.max(0, (Number(size[1]) || 0) * scale);
  if (width <= 0 || height <= 0) {
    return null;
  }
  return {
    left,
    top,
    right: left + width,
    bottom: top + height,
  };
}

function nodeScreenRects(node) {
  const rects = nodeDomScreenRects(node);
  pushRect(rects, canvasNodeScreenRect(node));
  return rects;
}

function isPointerRecentlyActive() {
  return resizePointerState.active || nowMs() - resizePointerState.lastAt <= RECENT_POINTER_MS;
}

function isPointerNearRectResizeEdge(rect) {
  const { x, y } = resizePointerState;
  const slop = RESIZE_EDGE_SLOP_PX;
  const inHorizontalRange = x >= rect.left - slop && x <= rect.right + slop;
  const inVerticalRange = y >= rect.top - slop && y <= rect.bottom + slop;
  const nearBottom = inHorizontalRange && y >= rect.bottom - slop && y <= rect.bottom + slop;
  const nearRight = inVerticalRange && x >= rect.right - slop && x <= rect.right + slop;
  return nearBottom || nearRight;
}

function isPointerNearNodeResizeEdge(node) {
  installNodeResizePointerTracker();
  if (!isPointerRecentlyActive()) {
    return false;
  }
  return nodeScreenRects(node).some((rect) => isPointerNearRectResizeEdge(rect));
}

function isCanvasResizingNode(node) {
  const canvas = app?.canvas;
  return canvas?.resizing_node === node
    || canvas?.resizingNode === node
    || canvas?.resizing_node?.node === node;
}

function isNodeUserResizeActive(node) {
  return isCanvasResizingNode(node) || isPointerNearNodeResizeEdge(node);
}

export {
  installNodeResizePointerTracker,
  isCanvasResizingNode,
  isNodeUserResizeActive,
};
