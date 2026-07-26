// @ts-check

import {
  EXTEND_ACTIVE_SLOTS_WIDGET,
  EXTEND_VISIBLE_SLOTS_PROPERTY,
} from "./constants.js";
import {
  extendVisibleSlots,
  parseExtendSlots,
} from "./extend_slots.js";
import {
  findInputEl,
  findWidget,
} from "./widgets.js";

function syncWidgetValue(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  widget.value = input.value;
}

function restoreInputFromWidget(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const value = String(widget?.value ?? input.value ?? "");
  if (input.value !== value) {
    input.value = value;
  }
}

function syncStudioValues(node, serialized = null, hooks = {}) {
  const fieldNames = hooks.studioFieldNames?.(node) || [];
  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (widget) {
      syncWidgetValue(widget);
    }
  }

  if (!serialized || !Array.isArray(node.widgets) || !Array.isArray(serialized.widgets_values)) {
    return;
  }
  if (hooks.isExtendNode?.(node)) {
    hooks.applyExtendSlotVisibility?.(node);
    const activeSlotsValue = JSON.stringify([...extendVisibleSlots(node)]);
    const activeSlotsWidget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
    if (activeSlotsWidget) {
      activeSlotsWidget.value = activeSlotsValue;
    }
    serialized.properties ||= {};
    serialized.properties[EXTEND_VISIBLE_SLOTS_PROPERTY] = [...parseExtendSlots(activeSlotsValue)];
  }

  for (const name of fieldNames) {
    const widgetIndex = node.widgets.findIndex((widget) => widget?.name === name);
    const widget = widgetIndex >= 0 ? node.widgets[widgetIndex] : null;
    if (widgetIndex >= 0 && widget) {
      serialized.widgets_values[widgetIndex] = widget.value ?? "";
    }
  }

  if (hooks.isExtendNode?.(node)) {
    const widgetIndex = node.widgets.findIndex((widget) => widget?.name === EXTEND_ACTIVE_SLOTS_WIDGET);
    const widget = widgetIndex >= 0 ? node.widgets[widgetIndex] : null;
    if (widgetIndex >= 0 && widget) {
      serialized.widgets_values[widgetIndex] = widget.value ?? JSON.stringify([...extendVisibleSlots(node)]);
    }
  }
}

export {
  restoreInputFromWidget,
  syncStudioValues,
  syncWidgetValue,
};
