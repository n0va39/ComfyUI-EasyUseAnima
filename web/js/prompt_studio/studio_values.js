// @ts-check

import {
  EXTEND_ACTIVE_SLOTS_WIDGET,
  EXTEND_VISIBLE_SLOTS_PROPERTY,
} from "./constants.js";
import {
  extendVisibleSlots,
  parseExtendSlots,
  writeExtendVisibleSlots,
} from "./extend_slots.js";
import {
  findInputEl,
  findWidget,
  firstValue,
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

function applyExecutedInputs(node, message, hooks = {}) {
  const slotPayload = firstValue(message?.prompt_studio_slots, null);
  const payload = slotPayload || firstValue(message?.prompt_studio_inputs, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  const fieldNames = hooks.studioFieldNames?.(node) || [];
  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    if (slotPayload && Object.prototype.hasOwnProperty.call(payload, name)) {
      widget.value = String(payload[name] ?? "");
      restoreInputFromWidget(widget);
      widget.__easyuseAnimaExecutedText = null;
      hooks.expandStudioInputToContent?.(node, widget, true);
    } else {
      widget.__easyuseAnimaExecutedText = String(payload[name] ?? "");
      hooks.expandStudioInputToContent?.(node, widget, true);
    }
  }
  if (slotPayload) {
    if (payload.active_slots != null) {
      writeExtendVisibleSlots(node, parseExtendSlots(payload.active_slots));
    }
    const fillNaia = findWidget(node, "fill_naia_prompt");
    if (fillNaia && payload.fill_naia_prompt != null) {
      fillNaia.value = !!payload.fill_naia_prompt;
    }
  }
  hooks.hookStudioNode?.(node);
}

export {
  applyExecutedInputs,
  restoreInputFromWidget,
  syncStudioValues,
  syncWidgetValue,
};
