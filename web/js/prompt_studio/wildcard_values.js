// @ts-check

import {
  findInputEl,
  findWidget,
  firstValue,
} from "./widgets.js";

function setRegularWidgetValue(node, name, value, hooks = {}) {
  const widget = findWidget(node, name);
  if (!widget) {
    return false;
  }
  widget.value = value;
  const input = findInputEl(widget);
  if (input) {
    input.value = String(value ?? "");
  }
  widget.callback?.(widget.value);
  hooks.markNodeDirty?.(node);
  return true;
}

function applyWildcardExecutedInputs(node, message, hooks = {}) {
  const payload = firstValue(message?.wildcard, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  if (payload.populated_text != null) {
    setRegularWidgetValue(node, "populated_text", String(payload.populated_text), hooks);
  }
  if (payload.mode != null) {
    setRegularWidgetValue(node, "mode", String(payload.mode), hooks);
  }
  if (payload.seed != null) {
    setRegularWidgetValue(node, "seed", Number(payload.seed), hooks);
  }
}

export {
  applyWildcardExecutedInputs,
  setRegularWidgetValue,
};
