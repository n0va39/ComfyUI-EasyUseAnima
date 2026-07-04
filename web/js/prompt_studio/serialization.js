// @ts-check

import {
  ADVANCED_FIELDS_PROPERTY,
  ADVANCED_LEGACY_FIELDS_WIDGET_INDEXES,
  ADVANCED_WIDGET_INDEX,
} from "./constants.js";
import {
  advancedDefaultFieldsValue,
  normalizeAdvancedFieldsValue,
} from "./schema.js";
import {
  clearPendingAdvancedFieldsValue,
  getPendingAdvancedFieldsValue,
  setPendingAdvancedFieldsValue,
} from "./state.js";

function advancedFieldsBackup(node) {
  const value = node?.properties?.[ADVANCED_FIELDS_PROPERTY];
  return typeof value === "string" && value.trim() ? value : "";
}

function syncAdvancedFieldsBackup(node, value) {
  node.properties ||= {};
  node.properties[ADVANCED_FIELDS_PROPERTY] = String(value || "");
}

function serializedAdvancedFieldsValue(serialized) {
  const propertyValue = normalizeAdvancedFieldsValue(serialized?.properties?.[ADVANCED_FIELDS_PROPERTY]);
  if (propertyValue) {
    return propertyValue;
  }
  const widgetsValue = normalizeAdvancedFieldsValue(serialized?.widgets_values?.[ADVANCED_WIDGET_INDEX.advanced_fields]);
  if (widgetsValue) {
    return widgetsValue;
  }
  for (const index of ADVANCED_LEGACY_FIELDS_WIDGET_INDEXES) {
    const legacyValue = normalizeAdvancedFieldsValue(serialized?.widgets_values?.[index]);
    if (legacyValue) {
      return legacyValue;
    }
  }
  return "";
}

function captureAdvancedConfigure(node, serialized, widget = null) {
  const value = serializedAdvancedFieldsValue(serialized);
  if (!value) {
    return;
  }
  setPendingAdvancedFieldsValue(node, value);
  syncAdvancedFieldsBackup(node, value);
  if (widget) {
    widget.value = value;
  }
}

function ensureAdvancedWidgetValue(node, widget = null) {
  if (!widget) {
    return;
  }
  const pendingValue = getPendingAdvancedFieldsValue(node);
  if (pendingValue) {
    widget.value = pendingValue;
    syncAdvancedFieldsBackup(node, widget.value);
    clearPendingAdvancedFieldsValue(node);
    return;
  }
  const backup = advancedFieldsBackup(node);
  const widgetValue = String(widget.value || "");
  if (
    backup
    && (!widgetValue.trim() || widgetValue === advancedDefaultFieldsValue())
  ) {
    widget.value = backup;
  }
}

export {
  advancedFieldsBackup,
  captureAdvancedConfigure,
  ensureAdvancedWidgetValue,
  serializedAdvancedFieldsValue,
  syncAdvancedFieldsBackup,
};
