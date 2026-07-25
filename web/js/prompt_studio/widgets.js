// @ts-check

import {
  findHiddenWidget,
} from "./state.js";

function findWidget(node, name) {
  return findHiddenWidget(node, name)
    || node.widgets?.find((widget) => widget.name === name);
}

function findInputEl(widget) {
  for (const candidate of [
    widget?.__easyuseAnimaStudioInput,
    widget?.inputEl,
    widget?.element,
  ]) {
    if (
      (candidate instanceof HTMLTextAreaElement || candidate instanceof HTMLInputElement)
      && candidate.isConnected !== false
    ) {
      return candidate;
    }
    const input = candidate?.querySelector?.("textarea, input");
    if (
      (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement)
      && input.isConnected !== false
    ) {
      return input;
    }
  }
  return null;
}

function firstValue(value, fallback = null) {
  if (Array.isArray(value)) {
    return value.length ? value[0] : fallback;
  }
  return value ?? fallback;
}

function isWidgetInputLinked(node, name) {
  return !!node.inputs?.some((input) => input.widget?.name === name && input.link != null);
}

export {
  findInputEl,
  findWidget,
  firstValue,
  isWidgetInputLinked,
};
