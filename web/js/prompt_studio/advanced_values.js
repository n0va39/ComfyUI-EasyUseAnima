// @ts-check

import {
  ADVANCED_FIELDS_PROPERTY,
  ADVANCED_WIDGET_INDEX,
} from "./constants.js";
import {
  normalizeAdvancedWidgetQueueValue,
} from "./schema.js";
import {
  getAdvancedFields,
} from "./state.js";
import {
  collectAdvancedEditorFields,
  syncAdvancedFieldsBackup,
} from "./serialization.js";
import {
  findWidget,
  firstValue,
} from "./widgets.js";
import {
  serializePreviousWildcardExecution,
  writePreviousWildcardExecution,
} from "./wildcard_seed_history.js";

function syncAdvancedValues(node, serialized = null, hooks = {}) {
  hooks.repairAdvancedInternalWidgetValues?.(node);
  const fields = collectAdvancedEditorFields(
    node,
    getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [],
  );
  hooks.writeAdvancedFields?.(node, fields, { syncInputs: false });
  if (!serialized || !Array.isArray(node.widgets) || !Array.isArray(serialized.widgets_values)) {
    return;
  }
  const fieldsValue = hooks.advancedWidget?.(node)?.value || JSON.stringify(fields);
  syncAdvancedFieldsBackup(node, fieldsValue);
  serialized.properties ||= {};
  serialized.properties[ADVANCED_FIELDS_PROPERTY] = fieldsValue;

  for (const name of Object.keys(ADVANCED_WIDGET_INDEX)) {
    const index = ADVANCED_WIDGET_INDEX[name];
    const widget = findWidget(node, name);
    if (name !== "advanced_fields" && !widget) {
      continue;
    }
    while (serialized.widgets_values.length <= index) {
      serialized.widgets_values.push(null);
    }
    if (name === "advanced_fields") {
      serialized.widgets_values[index] = fieldsValue;
    } else if (widget) {
      const value = normalizeAdvancedWidgetQueueValue(name, widget.value);
      widget.value = value;
      serialized.widgets_values[index] = value;
    }
  }
  serializePreviousWildcardExecution(node, serialized, {
    modeWidgetIndex: ADVANCED_WIDGET_INDEX.wildcard_mode,
    seedWidgetIndex: ADVANCED_WIDGET_INDEX.wildcard_seed,
    controlWidgetIndex: ADVANCED_WIDGET_INDEX.wildcard_seed_after_generate,
  });
}

function publishAdvancedWildcardExecution(node, message, hooks = {}) {
  const mappedPayload = message?.prompt_studio_advanced;
  const payload = firstValue(mappedPayload, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  const mappedItemCount = Array.isArray(mappedPayload) ? mappedPayload.length : 1;
  const wildcardSeed = findWidget(node, "wildcard_seed");
  hooks.consumeWildcardSeedExecution?.(
    node,
    message,
    mappedItemCount,
    wildcardSeed && payload.wildcard_seed != null
      ? () => {
        if (typeof hooks.commitAdvancedWildcardSeedView === "function") {
          hooks.commitAdvancedWildcardSeedView(node, payload.wildcard_seed);
        } else {
          wildcardSeed.value = payload.wildcard_seed;
        }
      }
      : null,
  );
  if (writePreviousWildcardExecution(node, {
    seed: payload.wildcard_execution_seed,
    mode: payload.wildcard_mode,
  })) {
    hooks.markNodeDirty?.(node);
  }
}

export {
  publishAdvancedWildcardExecution,
  syncAdvancedValues,
};
