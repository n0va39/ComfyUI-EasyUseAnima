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

function canAdvancedEditorScroll(editor) {
  return advancedEditorMaxScrollTop(editor) > 1;
}

function canAdvancedEditorScrollWheelDelta(editor, deltaY) {
  const maxScrollTop = advancedEditorMaxScrollTop(editor);
  if (maxScrollTop <= 1) {
    return false;
  }
  return (deltaY < 0 && editor.scrollTop > 0) || (deltaY > 0 && editor.scrollTop < maxScrollTop - 1);
}

function advancedWheelScrollableControl(target) {
  if (!(target instanceof Element)) {
    return null;
  }
  const control = target.closest(ADVANCED_NATIVE_CONTROL_SELECTOR);
  return control instanceof HTMLElement ? control : null;
}

function canAdvancedControlScrollWheelDelta(control, deltaY) {
  const maxScrollTop = advancedEditorMaxScrollTop(control);
  if (maxScrollTop <= 1) {
    return false;
  }
  return (deltaY < 0 && control.scrollTop > 0) || (deltaY > 0 && control.scrollTop < maxScrollTop - 1);
}

function shouldKeepAdvancedWheelEvent(event, editor) {
  const target = event?.target;
  if (!(target instanceof Element)) {
    return false;
  }
  const control = advancedWheelScrollableControl(target);
  if (!control || !isAdvancedNativeControlTarget(control)) {
    return false;
  }
  return canAdvancedControlScrollWheelDelta(control, Number(event?.deltaY) || 0);
}

export {
  advancedEditorMaxScrollTop,
  canAdvancedEditorScroll,
  canAdvancedEditorScrollWheelDelta,
  guardAdvancedEditorNativeControlEvent,
  isAdvancedNativeControlTarget,
  isMiddlePanExcludedTarget,
  shouldKeepAdvancedWheelEvent,
};
