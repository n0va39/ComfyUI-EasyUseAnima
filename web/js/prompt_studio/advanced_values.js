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
  setAdvancedFields,
} from "./state.js";
import {
  collectAdvancedEditorFields,
  mergeAdvancedFieldInputValues,
  syncAdvancedFieldsBackup,
} from "./serialization.js";
import {
  findWidget,
  firstValue,
} from "./widgets.js";
import {
  serializePreviousWildcardExecution,
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

function applyAdvancedExecutedInputs(node, message, hooks = {}) {
  const payload = firstValue(message?.prompt_studio_advanced, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  node.__easyuseAnimaAdvancedFieldInputValues =
    payload.field_inputs && typeof payload.field_inputs === "object" ? payload.field_inputs : {};
  const widget = hooks.advancedWidget?.(node);
  if (widget && payload.advanced_fields != null) {
    widget.value = String(payload.advanced_fields);
    syncAdvancedFieldsBackup(node, widget.value);
  }
  const fields = hooks.parseAdvancedFields?.(node) || [];
  if (mergeAdvancedFieldInputValues(fields, node.__easyuseAnimaAdvancedFieldInputValues)) {
    hooks.writeAdvancedFields?.(node, fields, { syncInputs: false });
  } else {
    setAdvancedFields(node, fields);
  }
  const useNaia = findWidget(node, "use_naia");
  if (useNaia && payload.use_naia != null) {
    useNaia.value = !!payload.use_naia;
  }
  for (const name of ["resolution_bucket", "resolution_size", "resolution_custom_width", "resolution_custom_height"]) {
    const widget = findWidget(node, name);
    if (widget && payload[name] != null) {
      widget.value = payload[name];
    }
  }
  for (const name of ["wildcard_mode", "wildcard_seed_after_generate"]) {
    const widget = findWidget(node, name);
    if (widget && payload[name] != null) {
      widget.value = payload[name];
    }
  }
  const wildcardSeed = findWidget(node, "wildcard_seed");
  if (
    wildcardSeed
    && payload.wildcard_seed != null
    && hooks.shouldApplyExecutedSeed?.(node, payload.wildcard_seed) !== false
  ) {
    wildcardSeed.value = payload.wildcard_seed;
  }
  for (const name of [
    "artist_mix_mode",
    "artist_mix_start_percent",
    "artist_mix_strength_scale",
    "artist_mix_style_gain",
    "artist_mix_rms_scale_cap",
    "artist_mix_exact_top_k",
    "artist_mix_cluster_count",
    "artist_mix_dominant_isolation",
    "artist_mix_dominant_threshold",
  ]) {
    const widget = findWidget(node, name);
    if (widget && payload[name] != null) {
      widget.value = payload[name];
    }
  }
  hooks.renderAdvancedEditor?.(node);
}

export {
  applyAdvancedExecutedInputs,
  syncAdvancedValues,
};
