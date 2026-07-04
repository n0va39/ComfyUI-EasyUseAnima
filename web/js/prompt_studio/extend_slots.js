// @ts-check

import {
  EXTEND_ACTIVE_SLOTS_WIDGET,
  EXTEND_DEFAULT_VISIBLE_FIELDS,
  EXTEND_FIELD_NAMES,
  EXTEND_VISIBLE_SLOTS_PROPERTY,
} from "./constants.js";
import {
  isExtendNode,
} from "./node_hooks.js";
import {
  findInputEl,
  findWidget,
  isWidgetInputLinked,
} from "./widgets.js";

/** @typedef {import("./types.js").PromptStudioInputElement} PromptStudioInputElement */

/**
 * @param {unknown} widget
 * @returns {PromptStudioInputElement | null}
 */
function findExtendInput(widget) {
  return findInputEl(widget);
}

function parseExtendSlots(raw) {
  if (Array.isArray(raw)) {
    return new Set(raw.filter((name) => EXTEND_FIELD_NAMES.includes(name)));
  }
  if (typeof raw === "string" && raw.trim()) {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return new Set(parsed.filter((name) => EXTEND_FIELD_NAMES.includes(name)));
      }
    } catch {
      return new Set();
    }
  }
  return new Set();
}

function extendVisibleSlotsState(node) {
  const propertyRaw = node?.properties?.[EXTEND_VISIBLE_SLOTS_PROPERTY];
  if (propertyRaw != null) {
    return { slots: parseExtendSlots(propertyRaw), explicit: true };
  }
  return { slots: new Set(EXTEND_DEFAULT_VISIBLE_FIELDS), explicit: true };
}

function extendVisibleSlots(node) {
  return extendVisibleSlotsState(node).slots;
}

function writeExtendVisibleSlots(node, slots) {
  const filtered = [...slots].filter((name) => EXTEND_FIELD_NAMES.includes(name));
  node.properties ||= {};
  node.properties[EXTEND_VISIBLE_SLOTS_PROPERTY] = filtered;
  const widget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
  if (widget) {
    widget.value = JSON.stringify(filtered);
  }
}

function extendSlotShouldShow(node, fieldName, state = extendVisibleSlotsState(node)) {
  if (isWidgetInputLinked(node, fieldName)) {
    return true;
  }
  return state.slots.has(fieldName);
}

function setExtendWidgetHidden(widget, hidden) {
  if (!widget) {
    return;
  }
  if (!widget.__easyuseAnimaExtendOriginalComputeSize) {
    widget.__easyuseAnimaExtendOriginalComputeSize = widget.computeSize;
  }
  if (!widget.__easyuseAnimaExtendOriginalDraw) {
    widget.__easyuseAnimaExtendOriginalDraw = widget.draw;
  }

  widget.__easyuseAnimaExtendHidden = hidden;
  widget.hidden = hidden;
  widget.options ||= {};
  widget.options.hidden = hidden;
  if (hidden) {
    widget.computeSize = () => [0, -4];
    widget.draw = () => {};
  } else {
    widget.computeSize = widget.__easyuseAnimaExtendOriginalComputeSize;
    widget.draw = widget.__easyuseAnimaExtendOriginalDraw;
  }

  const input = findExtendInput(widget);
  if (input) {
    input.style.display = hidden ? "none" : "";
    input.style.pointerEvents = hidden ? "none" : "";
    if (input.__easyuseAnimaHighlightOverlay) {
      input.__easyuseAnimaHighlightOverlay.style.display = hidden ? "none" : "";
    }
  }
}

function hideExtendStateWidget(node) {
  const widget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
  if (!widget || widget.__easyuseAnimaExtendStateHidden) {
    return;
  }
  widget.__easyuseAnimaExtendStateHidden = true;
  widget.hidden = true;
  widget.serialize = true;
  widget.options ||= {};
  widget.options.hidden = true;
  widget.computeSize = () => [0, -4];
  widget.draw = () => {};
  const input = findInputEl(widget);
  if (input) {
    input.style.display = "none";
  }
}

function applyExtendSlotVisibility(node) {
  if (!isExtendNode(node)) {
    return;
  }
  hideExtendStateWidget(node);
  const state = extendVisibleSlotsState(node);
  const visible = new Set(state.slots);
  for (const fieldName of EXTEND_FIELD_NAMES) {
    const shouldShow = extendSlotShouldShow(node, fieldName, state);
    if (shouldShow) {
      visible.add(fieldName);
    }
    setExtendWidgetHidden(findWidget(node, fieldName), !shouldShow);
  }
  writeExtendVisibleSlots(node, visible);
}

export {
  applyExtendSlotVisibility,
  extendSlotShouldShow,
  extendVisibleSlots,
  extendVisibleSlotsState,
  hideExtendStateWidget,
  parseExtendSlots,
  setExtendWidgetHidden,
  writeExtendVisibleSlots,
};
