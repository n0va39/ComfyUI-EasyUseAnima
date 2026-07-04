// @ts-check

import {
  ADVANCED_FIELD_SOCKET_PREFIX,
  ADVANCED_FIELDS_PROPERTY,
  ADVANCED_LEGACY_FIELDS_WIDGET_INDEXES,
  ADVANCED_WIDGET_INDEX,
} from "./constants.js";
import {
  advancedFieldInputName,
  advancedDefaultFieldsValue,
  normalizeAdvancedField,
  normalizeAdvancedFieldsValue,
} from "./schema.js";
import {
  clearPendingAdvancedFieldsValue,
  getAdvancedEditorElement,
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

function collectAdvancedEditorFields(node, sourceFields) {
  const fields = (sourceFields || [])
    .map((field, index) => normalizeAdvancedField(field, index));
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return fields;
  }

  const byId = new Map(fields.map((field) => [field.id, field]));
  editor.querySelectorAll("textarea[data-easyuse-anima-advanced-field-id]").forEach((textarea) => {
    const id = textarea.dataset.easyuseAnimaAdvancedFieldId;
    const field = byId.get(id);
    if (!field) {
      return;
    }
    field.text = textarea.value;
    const height = Number.parseInt(textarea.style.height || "", 10);
    if (Number.isFinite(height) && height > 0) {
      field.height = Math.max(42, height);
    }
  });
  return fields;
}

function advancedFieldIndexLabel(fields, field) {
  const paneFields = (fields || []).filter((item) => item.pane === field.pane);
  const paneIndex = paneFields.findIndex((item) => item.id === field.id);
  const number = Math.max(0, paneIndex) + 1;
  return field.pane === "negative" ? `neg${number}` : `${number}`;
}

function isAdvancedFieldInput(input) {
  return !!input?.__easyuseAnimaAdvancedFieldInput
    || String(input?.name || "").startsWith(ADVANCED_FIELD_SOCKET_PREFIX);
}

function updateNodeInputLinkSlots(node, graph = null) {
  if (!node?.inputs || !graph?.links) {
    return;
  }
  const expectedLinks = new Set();
  node.inputs.forEach((input, index) => {
    if (input?.link == null) {
      return;
    }
    const link = graph.links[input.link];
    if (link) {
      expectedLinks.add(Number(input.link));
      link.target_id = node.id;
      link.target_slot = index;
    }
  });

  for (const [rawLinkId, link] of Object.entries(graph.links)) {
    const linkId = Number(rawLinkId);
    if (!link || Number(link.target_id) !== Number(node.id)) {
      continue;
    }
    const targetInput = node.inputs?.[link.target_slot];
    if (targetInput?.link === linkId) {
      continue;
    }
    const originNode = graph.getNodeById?.(link.origin_id);
    const originOutput = originNode?.outputs?.[link.origin_slot];
    if (Array.isArray(originOutput?.links)) {
      originOutput.links = originOutput.links.filter((id) => Number(id) !== linkId);
    }
    if (!expectedLinks.has(linkId)) {
      delete graph.links[rawLinkId];
    }
  }
}

function syncAdvancedFieldInputs(node, fields, { graph = null, fieldLabel = null } = {}) {
  if (!node || typeof node.addInput !== "function") {
    return;
  }

  const wanted = new Map();
  (fields || []).forEach((field) => {
    if (field?.type === "naia") {
      return;
    }
    wanted.set(advancedFieldInputName(field), { field, indexLabel: advancedFieldIndexLabel(fields, field) });
  });

  for (let index = (node.inputs?.length || 0) - 1; index >= 0; index -= 1) {
    const input = node.inputs[index];
    if (isAdvancedFieldInput(input) && !wanted.has(input.name)) {
      node.removeInput?.(index);
    }
  }

  for (const [name, { field, indexLabel }] of wanted) {
    let input = node.inputs?.find((item) => item.name === name);
    if (!input) {
      node.addInput(name, "STRING");
      input = node.inputs?.find((item) => item.name === name);
    }
    if (!input) {
      continue;
    }
    const label = typeof fieldLabel === "function"
      ? fieldLabel(field)
      : String(field?.label || field?.type || "Field");
    input.type = "STRING";
    input.label = `${indexLabel}. ${label}`;
    input.__easyuseAnimaAdvancedFieldInput = true;
    input.__easyuseAnimaAdvancedFieldId = field.id;
  }

  const fieldInputs = [];
  for (const [name] of wanted) {
    const input = node.inputs?.find((item) => item.name === name);
    if (input) {
      fieldInputs.push(input);
    }
  }
  const otherInputs = (node.inputs || []).filter((input) => !isAdvancedFieldInput(input));
  node.inputs = [...fieldInputs, ...otherInputs];
  updateNodeInputLinkSlots(node, graph);
}

function advancedFieldInputLinked(node, field) {
  const name = advancedFieldInputName(field);
  return !!node.inputs?.some((input) => input.name === name && input.link != null);
}

function advancedFieldDisplayText(node, field) {
  const name = advancedFieldInputName(field);
  const values = node.__easyuseAnimaAdvancedFieldInputValues || {};
  if (advancedFieldInputLinked(node, field) && Object.prototype.hasOwnProperty.call(values, name)) {
    return String(values[name] ?? "");
  }
  return String(field?.text || "");
}

function mergeAdvancedFieldInputValues(node, fields, values) {
  if (!values || typeof values !== "object" || !Array.isArray(fields)) {
    return false;
  }
  let changed = false;
  for (const field of fields) {
    const name = advancedFieldInputName(field);
    if (!Object.prototype.hasOwnProperty.call(values, name)) {
      continue;
    }
    const text = String(values[name] ?? "");
    if (field.text !== text) {
      field.text = text;
      changed = true;
    }
  }
  return changed;
}

function pruneDisconnectedAdvancedFieldInputValues(node) {
  const values = node.__easyuseAnimaAdvancedFieldInputValues;
  if (!values || typeof values !== "object") {
    return;
  }
  const linkedNames = new Set(
    (node.inputs || [])
      .filter((input) => isAdvancedFieldInput(input) && input.link != null)
      .map((input) => input.name),
  );
  for (const name of Object.keys(values)) {
    if (!linkedNames.has(name)) {
      delete values[name];
    }
  }
}

export {
  advancedFieldDisplayText,
  advancedFieldIndexLabel,
  advancedFieldInputLinked,
  advancedFieldsBackup,
  captureAdvancedConfigure,
  collectAdvancedEditorFields,
  ensureAdvancedWidgetValue,
  isAdvancedFieldInput,
  mergeAdvancedFieldInputValues,
  pruneDisconnectedAdvancedFieldInputValues,
  serializedAdvancedFieldsValue,
  syncAdvancedFieldInputs,
  syncAdvancedFieldsBackup,
  updateNodeInputLinkSlots,
};
