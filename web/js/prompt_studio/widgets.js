// @ts-check

import {
  findHiddenWidget,
} from "./state.js";

function findWidget(node, name) {
  return findHiddenWidget(node, name)
    || node.widgets?.find((widget) => widget.name === name);
}

function findInputEl(widget) {
  const input = widget?.inputEl;
  if (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement) {
    return input;
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
