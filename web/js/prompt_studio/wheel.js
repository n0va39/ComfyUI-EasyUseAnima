// @ts-check

import {
  ADVANCED_NATIVE_CONTROL_SELECTOR,
} from "./constants.js";

function isAdvancedNativeControlTarget(target) {
  if (!(target instanceof Element)) {
    return false;
  }
  return !!target.closest(".easyuse-anima-advanced-editor")
    && !!target.closest(ADVANCED_NATIVE_CONTROL_SELECTOR);
}

function isMiddlePanExcludedTarget(target) {
  if (!(target instanceof Element)) {
    return false;
  }
  return isAdvancedNativeControlTarget(target) || !!target.closest([
    ".comfy-menu",
    ".comfy-modal",
    ".comfyui-menu",
    ".comfyui-settings",
    ".litegraph.litemenu",
    ".easyuse-anima-autocomplete",
    ".easyuse-anima-lora-menu",
  ].join(","));
}

function guardAdvancedEditorNativeControlEvent(event) {
  if (isAdvancedNativeControlTarget(event.target)) {
    event.stopPropagation();
  }
}

function advancedEditorMaxScrollTop(editor) {
  if (!(editor instanceof HTMLElement)) {
    return 0;
  }
  return Math.max(0, editor.scrollHeight - editor.clientHeight);
}

function advancedEditorFromWheelEvent(event) {
  for (const candidate of event?.composedPath?.() || []) {
    if (
      candidate instanceof HTMLElement
      && candidate.classList?.contains("easyuse-anima-advanced-editor")
    ) {
      return candidate;
    }
  }
  const target = event?.target;
  return target instanceof Element
    ? target.closest(".easyuse-anima-advanced-editor")
    : null;
}

function advancedWheelDeltaPixels(event, editor) {
  const deltaY = Number(event?.deltaY) || 0;
  const deltaMode = Number(event?.deltaMode) || 0;
  if (deltaMode === 1) {
    return deltaY * 16;
  }
  if (deltaMode === 2) {
    return deltaY * Math.max(1, Number(editor?.clientHeight) || 0);
  }
  return deltaY;
}

/**
 * The Advanced editor owns every wheel event while its vertical scrollbar
 * exists. Boundary events stay consumed, so reaching the top or bottom never
 * falls through to ComfyUI canvas zoom. Canvas forwarding is allowed only when
 * the editor has no vertical overflow at all.
 */
function consumeAdvancedEditorWheel(event, editor) {
  const maxScrollTop = advancedEditorMaxScrollTop(editor);
  if (maxScrollTop <= 1) {
    return false;
  }
  event.preventDefault?.();
  event.stopPropagation?.();
  event.stopImmediatePropagation?.();
  const currentScrollTop = Number(editor.scrollTop) || 0;
  const nextScrollTop = Math.max(
    0,
    Math.min(maxScrollTop, currentScrollTop + advancedWheelDeltaPixels(event, editor)),
  );
  editor.scrollTop = nextScrollTop;
  return true;
}

export {
  advancedEditorFromWheelEvent,
  advancedEditorMaxScrollTop,
  advancedWheelDeltaPixels,
  consumeAdvancedEditorWheel,
  guardAdvancedEditorNativeControlEvent,
  isAdvancedNativeControlTarget,
  isMiddlePanExcludedTarget,
};
