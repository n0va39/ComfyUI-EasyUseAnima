// @ts-check

import {
  ADVANCED_FIELD_LABELS,
  ADVANCED_INTERNAL_WIDGET_NAMES,
} from "./constants.js";
import {
  advancedDefaultFields,
  normalizeAdvancedField,
  normalizeAdvancedWidgetQueueValue,
} from "./schema.js";
import {
  setAdvancedFields,
  setHiddenWidget,
} from "./state.js";
import {
  PROMPT_STUDIO_SETTINGS,
} from "./settings.js";
import {
  psText,
} from "./text.js";
import {
  advancedFieldsBackup,
  ensureAdvancedWidgetValue,
  syncAdvancedFieldInputs,
  syncAdvancedFieldsBackup,
} from "./serialization.js";
import {
  findInputEl,
  findWidget,
} from "./widgets.js";

function advancedWidget(node) {
  return findWidget(node, "advanced_fields");
}

function repairAdvancedInternalWidgetValues(node, hooks = {}) {
  let changed = false;
  for (const name of Object.keys(hooks.advancedWidgetIndex || {})) {
    if (name === "advanced_fields") {
      continue;
    }
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    const next = normalizeAdvancedWidgetQueueValue(name, widget.value);
    if (widget.value !== next) {
      widget.value = next;
      const input = findInputEl(widget);
      if (input) {
        input.value = String(next ?? "");
      }
      changed = true;
    }
  }
  if (changed) {
    hooks.markNodeDirty?.(node);
  }
  return changed;
}

function hideAdvancedInternalWidget(node, name) {
  const widget = findWidget(node, name);
  if (!widget) {
    return;
  }
  widget.__easyuseAnimaAdvancedHidden = true;
  widget.hidden = true;
  widget.serialize = true;
  widget.options ||= {};
  widget.options.hidden = true;
  widget.computeSize = () => [0, 0];
  widget.draw = () => {};
  const input = findInputEl(widget);
  if (input) {
    input.style.display = "none";
    input.style.pointerEvents = "none";
    input.tabIndex = -1;
  }
  setHiddenWidget(node, name, widget);
  node.setDirtyCanvas?.(true, true);
}

function hideAdvancedControlWidgets(node, hooks = {}) {
  for (const name of ADVANCED_INTERNAL_WIDGET_NAMES) {
    hideAdvancedInternalWidget(node, name);
  }
  repairAdvancedInternalWidgetValues(node, hooks);
}

function removeAdvancedInternalInputSockets(node) {
  if (!Array.isArray(node.inputs)) {
    return;
  }
  for (let index = node.inputs.length - 1; index >= 0; index -= 1) {
    const input = node.inputs[index];
    const widgetName = input?.widget?.name || input?.name;
    if (!ADVANCED_INTERNAL_WIDGET_NAMES.has(widgetName)) {
      continue;
    }
    if (input?.link != null) {
      node.disconnectInput?.(index);
    }
    node.removeInput?.(index);
  }
}

function parseAdvancedFields(node) {
  const widget = advancedWidget(node);
  ensureAdvancedWidgetValue(node, widget);
  const sourceValue = String(widget?.value || advancedFieldsBackup(node) || "[]");
  try {
    const parsed = JSON.parse(sourceValue);
    if (Array.isArray(parsed) && parsed.length) {
      const fields = [];
      const seenNaiaPanes = new Set();
      let seenTrigger = false;
      parsed.forEach((field, index) => {
        const normalized = normalizeAdvancedField(field, index);
        if (normalized.type === "naia") {
          if (seenNaiaPanes.has(normalized.pane)) {
            return;
          }
          seenNaiaPanes.add(normalized.pane);
        }
        if (normalized.type === "trigger") {
          if (seenTrigger) {
            return;
          }
          seenTrigger = true;
          normalized.pane = "positive";
        }
        fields.push(normalized);
      });
      return fields.length ? fields : advancedDefaultFields();
    }
  } catch {
    // Fall through to default fields.
  }
  return advancedDefaultFields();
}

function advancedFieldLabel(field) {
  const base = ADVANCED_FIELD_LABELS[field.type] || "General Tags";
  const localizedBase = psText(`advanced.field.${field.type}`) || base;
  return field.label && field.label !== base && field.label !== localizedBase
    ? `${localizedBase} - ${field.label}`
    : localizedBase;
}

function writeAdvancedFields(node, fields, { render = false, syncInputs = true } = {}, hooks = {}) {
  const widget = advancedWidget(node);
  if (!widget) {
    return;
  }
  widget.value = JSON.stringify(fields.map((field, index) => normalizeAdvancedField(field, index)));
  syncAdvancedFieldsBackup(node, widget.value);
  setAdvancedFields(node, fields);
  if (syncInputs) {
    syncAdvancedFieldInputs(node, fields, { graph: hooks.graph, fieldLabel: advancedFieldLabel });
  }
  hooks.markNodeDirty?.(node);
  if (render) {
    hooks.renderAdvancedEditor?.(node);
  }
}

function applyAdvancedNaiaGeneralAutoToggle(node, fields) {
  if (!PROMPT_STUDIO_SETTINGS.naiaGeneralAboveAutoToggle || !Array.isArray(fields)) {
    return false;
  }
  const naiaIndex = fields.findIndex(
    (field) => field?.pane === "positive" && field?.type === "naia",
  );
  if (naiaIndex < 0) {
    return false;
  }
  const naiaEnabled = fields[naiaIndex]?.enabled !== false;
  let changed = false;
  for (let index = 0; index < naiaIndex; index += 1) {
    const field = fields[index];
    if (field?.pane !== "positive" || field?.type !== "general") {
      continue;
    }
    const nextEnabled = !naiaEnabled;
    if ((field.enabled !== false) !== nextEnabled) {
      field.enabled = nextEnabled;
      changed = true;
    }
  }
  return changed;
}

export {
  advancedFieldLabel,
  advancedWidget,
  applyAdvancedNaiaGeneralAutoToggle,
  hideAdvancedControlWidgets,
  hideAdvancedInternalWidget,
  parseAdvancedFields,
  removeAdvancedInternalInputSockets,
  repairAdvancedInternalWidgetValues,
  writeAdvancedFields,
};
