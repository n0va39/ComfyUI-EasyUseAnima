// @ts-check

import {
  REGIONAL_CONFIG_PROPERTY,
  REGIONAL_FIELDS_PROPERTY,
  REGIONAL_INTERNAL_WIDGET_NAMES,
  REGIONAL_NODE_TYPE,
  REGIONAL_WIDGET_INDEX,
} from "./constants.js";
import {
  readRegionalResolutionValues,
  resolutionLabel,
  snapResolution32,
  ratioLabel,
} from "./resolution.js";
import {
  createDefaultRegionalConfig,
  createDefaultRegionalFields,
  firstRegionalValue,
  normalizeRegionalConditioningWidgetValues,
  normalizeRegionalConfig,
  normalizeRegionalField,
  normalizeRegionalFields,
} from "./schema.js";
import {
  normalizeRegionalConfigString,
  normalizeRegionalFieldsString,
  serializedRegionalValue as readSerializedRegionalValue,
} from "./serialization.js";

/**
 * Build the DOM-independent state, socket, and serialization runtime for one
 * ComfyUI app instance.
 *
 * @param {any} app
 * @param {{ fieldLabel?: (field: any) => string }} [hooks]
 */
function createRegionalRuntime(app, hooks = {}) {
  /** @param {any} node @param {string} name */
  function findWidget(node, name) {
    return node?.widgets?.find((widget) => widget.name === name) || null;
  }

  /** @param {any} node @param {any} [serialized] */
  function repairRegionalConditioningWidgets(node, serialized = null) {
    const currentValues = Array.isArray(serialized?.widgets_values)
      ? serialized.widgets_values
      : (Array.isArray(node?.widgets) ? node.widgets.map((widget) => widget.value) : []);
    const values = normalizeRegionalConditioningWidgetValues(currentValues);
    if (serialized && Array.isArray(serialized.widgets_values)) {
      serialized.widgets_values = values;
    }
    const maskStrength = findWidget(node, "mask_strength");
    if (maskStrength) {
      maskStrength.value = values[0];
    }
    const setCondArea = findWidget(node, "set_cond_area");
    if (setCondArea) {
      setCondArea.value = values[1];
    }
  }

  /** @param {any} node */
  function customResolution(node) {
    return {
      width: snapResolution32(findWidget(node, "resolution_custom_width")?.value, 1024),
      height: snapResolution32(findWidget(node, "resolution_custom_height")?.value, 1024),
    };
  }

  /** @param {any} node @param {string} name @param {any} value */
  function setRegionalWidgetValue(node, name, value) {
    const widget = findWidget(node, name);
    if (!widget) {
      return false;
    }
    widget.value = value;
    widget.callback?.(widget.value);
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
    return true;
  }

  /**
   * @param {any} node
   * @param {any} width
   * @param {any} height
   * @param {{ normalize?: boolean }} [options]
   */
  function setCustomResolution(node, width, height, options = {}) {
    const nextWidth = options.normalize ? snapResolution32(width, 1024) : String(width || "");
    const nextHeight = options.normalize ? snapResolution32(height, 1024) : String(height || "");
    setRegionalWidgetValue(node, "resolution_custom_width", nextWidth);
    setRegionalWidgetValue(node, "resolution_custom_height", nextHeight);
    if (options.normalize) {
      setRegionalWidgetValue(node, "resolution_size", resolutionLabel(nextWidth, nextHeight));
    }
    updateRegionalConfigCanvas(node);
  }

  /** @param {any} node */
  function readResolution(node) {
    return readRegionalResolutionValues({
      bucket: findWidget(node, "resolution_bucket")?.value,
      size: findWidget(node, "resolution_size")?.value,
      customWidth: findWidget(node, "resolution_custom_width")?.value,
      customHeight: findWidget(node, "resolution_custom_height")?.value,
    });
  }

  /** @param {any} [node] */
  function defaultConfig(node = null) {
    return createDefaultRegionalConfig(node ? readResolution(node) : null);
  }

  /** @param {any} node @param {any} value */
  function normalizeConfigValue(node, value) {
    return normalizeRegionalConfig(value, node ? readResolution(node) : null);
  }

  /** @param {any} node */
  function regionalFieldsWidget(node) {
    return findWidget(node, "regional_fields");
  }

  /** @param {any} node */
  function regionalConfigWidget(node) {
    return findWidget(node, "regional_config");
  }

  /** @param {any} node @param {any} fieldsValue @param {any} configValue */
  function syncBackup(node, fieldsValue, configValue) {
    node.properties ||= {};
    node.properties[REGIONAL_FIELDS_PROPERTY] = String(fieldsValue || "");
    node.properties[REGIONAL_CONFIG_PROPERTY] = String(configValue || "");
  }

  /** @param {any} node */
  function fieldsBackup(node) {
    const value = node?.properties?.[REGIONAL_FIELDS_PROPERTY];
    return typeof value === "string" && value.trim() ? value : "";
  }

  /** @param {any} node */
  function configBackup(node) {
    const value = node?.properties?.[REGIONAL_CONFIG_PROPERTY];
    return typeof value === "string" && value.trim() ? value : "";
  }

  /** @param {any} node @param {any} value */
  function normalizedConfigString(node, value) {
    return normalizeRegionalConfigString(value, node ? readResolution(node) : null);
  }

  /** @param {any} node @param {any} serialized @param {string} name */
  function serializedRegionalValue(node, serialized, name) {
    return readSerializedRegionalValue(serialized, name, node ? readResolution(node) : null);
  }

  /** @param {any} node @param {any} serialized */
  function captureRegionalConfigure(node, serialized) {
    const fields = serializedRegionalValue(node, serialized, "regional_fields");
    const config = serializedRegionalValue(node, serialized, "regional_config");
    if (fields) {
      node.__easyuseAnimaPendingRegionalFields = fields;
    }
    if (config) {
      node.__easyuseAnimaPendingRegionalConfig = config;
    }
    if (fields || config) {
      syncBackup(node, fields || fieldsBackup(node), config || configBackup(node));
    }
  }

  /** @param {any} node */
  function ensureRegionalWidgetValues(node) {
    const fieldsWidget = regionalFieldsWidget(node);
    const configWidget = regionalConfigWidget(node);
    let fieldsValue = node.__easyuseAnimaPendingRegionalFields
      || fieldsBackup(node)
      || fieldsWidget?.value
      || JSON.stringify(createDefaultRegionalFields());
    let configValue = node.__easyuseAnimaPendingRegionalConfig
      || configBackup(node)
      || configWidget?.value
      || JSON.stringify(defaultConfig(node));
    fieldsValue = normalizeRegionalFieldsString(fieldsValue);
    configValue = normalizedConfigString(node, configValue);
    if (fieldsWidget) {
      fieldsWidget.value = fieldsValue;
    }
    if (configWidget) {
      configWidget.value = configValue;
    }
    node.__easyuseAnimaRegionalFields = normalizeRegionalFields(fieldsValue);
    node.__easyuseAnimaRegionalConfig = normalizeConfigValue(node, configValue);
    syncBackup(node, fieldsValue, configValue);
    delete node.__easyuseAnimaPendingRegionalFields;
    delete node.__easyuseAnimaPendingRegionalConfig;
  }

  /**
   * @param {any} node
   * @param {any[]} fields
   * @param {{ syncInputs?: boolean }} [options]
   */
  function writeRegionalFields(node, fields, options = {}) {
    const normalized = fields.map((field, index) => normalizeRegionalField(field, index));
    const value = JSON.stringify(normalized);
    const widget = regionalFieldsWidget(node);
    if (widget) {
      widget.value = value;
    }
    node.__easyuseAnimaRegionalFields = normalized;
    syncBackup(
      node,
      value,
      regionalConfigWidget(node)?.value
        || JSON.stringify(node.__easyuseAnimaRegionalConfig || defaultConfig(node)),
    );
    if (options.syncInputs !== false) {
      syncRegionalFieldInputs(node, normalized);
    }
  }

  /** @param {any} node @param {any} config */
  function writeRegionalConfig(node, config) {
    const normalized = normalizeConfigValue(node, config);
    const value = JSON.stringify(normalized);
    const widget = regionalConfigWidget(node);
    if (widget) {
      widget.value = value;
    }
    node.__easyuseAnimaRegionalConfig = normalized;
    syncBackup(
      node,
      regionalFieldsWidget(node)?.value
        || JSON.stringify(node.__easyuseAnimaRegionalFields || createDefaultRegionalFields()),
      value,
    );
  }

  /** @param {any} node */
  function updateRegionalConfigCanvas(node) {
    const config = normalizeConfigValue(
      node,
      node.__easyuseAnimaRegionalConfig || regionalConfigWidget(node)?.value,
    );
    const { width, height } = readResolution(node);
    config.canvas = {
      width,
      height,
      aspect_ratio: ratioLabel(width, height),
      source: "resolution_fields",
    };
    writeRegionalConfig(node, config);
  }

  /** @param {any} node @param {string} name */
  function hideRegionalInternalWidget(node, name) {
    const widget = findWidget(node, name);
    if (!widget || widget.__easyuseAnimaRegionalHidden) {
      return;
    }
    widget.__easyuseAnimaRegionalHidden = true;
    widget.hidden = true;
    widget.serialize = true;
    widget.options ||= {};
    widget.options.hidden = true;
    widget.computeSize = () => [0, 0];
    widget.draw = () => {};
  }

  /** @param {any} node */
  function hideRegionalInternalWidgets(node) {
    for (const name of REGIONAL_INTERNAL_WIDGET_NAMES) {
      hideRegionalInternalWidget(node, name);
    }
  }

  /** @param {any} node */
  function removeRegionalInternalInputSockets(node) {
    if (!Array.isArray(node?.inputs)) {
      return;
    }
    for (let index = node.inputs.length - 1; index >= 0; index -= 1) {
      const input = node.inputs[index];
      const widgetName = input?.widget?.name || input?.name;
      if (widgetName && REGIONAL_INTERNAL_WIDGET_NAMES.has(widgetName)) {
        if (input?.link != null) {
          node.disconnectInput?.(index);
        }
        node.removeInput?.(index);
      }
    }
  }

  /** @param {any} field */
  function fieldSocketName(field) {
    return `field_${String(field.id || "field").replace(/[^A-Za-z0-9_]/g, "_") || "field"}`;
  }

  /** @param {any} input */
  function isRegionalFieldInput(input) {
    return !!input?.__easyuseAnimaRegionalFieldInput
      || String(input?.name || "").startsWith("field_");
  }

  /** @param {any[]} fields @param {any} field */
  function regionalFieldIndexLabel(fields, field) {
    const paneFields = (fields || []).filter((item) => item.pane === field.pane);
    const paneIndex = paneFields.findIndex((item) => item.id === field.id);
    const number = Math.max(0, paneIndex) + 1;
    return field.pane === "negative" ? `neg${number}` : `${number}`;
  }

  /** @param {any} node */
  function updateRegionalNodeInputLinkSlots(node) {
    if (!node?.inputs || !app.graph?.links) {
      return;
    }
    const expectedLinks = new Set();
    node.inputs.forEach((input, index) => {
      if (input?.link == null) {
        return;
      }
      const link = app.graph.links[input.link];
      if (link) {
        expectedLinks.add(Number(input.link));
        link.target_id = node.id;
        link.target_slot = index;
      }
    });

    for (const [rawLinkId, link] of Object.entries(app.graph.links)) {
      const linkId = Number(rawLinkId);
      if (!link || Number(link.target_id) !== Number(node.id)) {
        continue;
      }
      const targetInput = node.inputs?.[link.target_slot];
      if (targetInput?.link === linkId) {
        continue;
      }
      const originNode = app.graph.getNodeById?.(link.origin_id);
      const originOutput = originNode?.outputs?.[link.origin_slot];
      if (Array.isArray(originOutput?.links)) {
        originOutput.links = originOutput.links.filter((id) => Number(id) !== linkId);
      }
      if (!expectedLinks.has(linkId)) {
        delete app.graph.links[rawLinkId];
      }
    }
  }

  /** @param {any} node @param {any[]} fields */
  function syncRegionalFieldInputs(node, fields) {
    if (!node || typeof node.addInput !== "function") {
      return;
    }
    const wanted = new Map();
    (fields || []).forEach((field) => {
      const normalized = normalizeRegionalField(field, wanted.size);
      const name = fieldSocketName(normalized);
      wanted.set(name, {
        field: normalized,
        indexLabel: regionalFieldIndexLabel(fields, normalized),
      });
    });

    for (let index = (node.inputs?.length || 0) - 1; index >= 0; index -= 1) {
      const input = node.inputs[index];
      if (isRegionalFieldInput(input) && !wanted.has(input.name)) {
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
      input.type = "STRING";
      input.label = `${indexLabel}. ${hooks.fieldLabel?.(field) || field.label || field.type || "Prompt"}`;
      input.__easyuseAnimaRegionalFieldInput = true;
      input.__easyuseAnimaRegionalFieldId = field.id;
    }

    const fieldInputs = [];
    for (const [name] of wanted) {
      const input = node.inputs?.find((item) => item.name === name);
      if (input) {
        fieldInputs.push(input);
      }
    }
    const otherInputs = (node.inputs || []).filter((input) => !isRegionalFieldInput(input));
    node.inputs = [...fieldInputs, ...otherInputs];
    updateRegionalNodeInputLinkSlots(node);
  }

  /** @param {any} node @param {any} field */
  function regionalFieldInputLinked(node, field) {
    const name = fieldSocketName(field);
    return !!node.inputs?.some((input) => input.name === name && input.link != null);
  }

  /** @param {any} node @param {any} field */
  function regionalFieldDisplayText(node, field) {
    const name = fieldSocketName(field);
    const values = node.__easyuseAnimaRegionalFieldInputValues || {};
    if (
      regionalFieldInputLinked(node, field)
      && Object.prototype.hasOwnProperty.call(values, name)
    ) {
      return String(values[name] ?? "");
    }
    return String(field?.text || "");
  }

  /** @param {any[]} fields @param {any} values */
  function mergeRegionalFieldInputValues(fields, values) {
    if (!values || typeof values !== "object" || !Array.isArray(fields)) {
      return false;
    }
    let changed = false;
    for (const field of fields) {
      const name = fieldSocketName(field);
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

  /** @param {any} node */
  function pruneDisconnectedRegionalFieldInputValues(node) {
    const values = node.__easyuseAnimaRegionalFieldInputValues;
    if (!values || typeof values !== "object") {
      return;
    }
    const linkedNames = new Set(
      (node.inputs || [])
        .filter((input) => isRegionalFieldInput(input) && input.link != null)
        .map((input) => input.name),
    );
    for (const name of Object.keys(values)) {
      if (!linkedNames.has(name)) {
        delete values[name];
      }
    }
  }

  /**
   * @param {any} node
   * @param {any} [serialized]
   * @param {((node: any) => any[]) | null} [collectFields]
   */
  function syncRegionalValues(node, serialized = null, collectFields = null) {
    const fields = collectFields
      ? collectFields(node)
      : (node.__easyuseAnimaRegionalFields || createDefaultRegionalFields());
    const config = node.__easyuseAnimaRegionalConfig
      || normalizeConfigValue(node, regionalConfigWidget(node)?.value);
    writeRegionalFields(node, fields, { syncInputs: false });
    writeRegionalConfig(node, config);
    if (!serialized || !Array.isArray(serialized.widgets_values)) {
      return;
    }
    serialized.properties ||= {};
    serialized.properties[REGIONAL_FIELDS_PROPERTY] = regionalFieldsWidget(node)?.value
      || JSON.stringify(fields);
    serialized.properties[REGIONAL_CONFIG_PROPERTY] = regionalConfigWidget(node)?.value
      || JSON.stringify(config);
    for (const [name, index] of Object.entries(REGIONAL_WIDGET_INDEX)) {
      const widget = findWidget(node, name);
      while (serialized.widgets_values.length <= index) {
        serialized.widgets_values.push(null);
      }
      if (name === "regional_fields") {
        serialized.widgets_values[index] = serialized.properties[REGIONAL_FIELDS_PROPERTY];
      } else if (name === "regional_config") {
        serialized.widgets_values[index] = serialized.properties[REGIONAL_CONFIG_PROPERTY];
      } else if (widget) {
        serialized.widgets_values[index] = widget.value;
      }
    }
  }

  /**
   * @param {any} node
   * @param {any} message
   * @param {{ shouldApplyExecutedSeed?: (node: any, value: any) => boolean }} [options]
   */
  function applyRegionalExecutedInputs(node, message, options = {}) {
    const payload = firstRegionalValue(message?.prompt_studio_regional, null);
    if (!payload || typeof payload !== "object") {
      return false;
    }
    node.__easyuseAnimaRegionalFieldInputValues =
      payload.field_inputs && typeof payload.field_inputs === "object"
        ? payload.field_inputs
        : {};
    if (payload.regional_fields != null) {
      const widget = regionalFieldsWidget(node);
      if (widget) {
        widget.value = normalizeRegionalFieldsString(payload.regional_fields);
      }
    }
    if (payload.regional_config != null) {
      const widget = regionalConfigWidget(node);
      if (widget) {
        widget.value = normalizedConfigString(node, payload.regional_config);
      }
    }
    for (const name of ["wildcard_mode", "wildcard_seed", "wildcard_seed_after_generate"]) {
      const widget = findWidget(node, name);
      if (!widget || payload[name] == null) {
        continue;
      }
      if (name === "wildcard_seed" && typeof options.shouldApplyExecutedSeed === "function") {
        let shouldApply = false;
        try {
          shouldApply = options.shouldApplyExecutedSeed(node, payload[name]) !== false;
        } catch {
          // A failed authority check must not let stale execution metadata win.
        }
        if (!shouldApply) {
          continue;
        }
      }
      widget.value = payload[name];
    }
    ensureRegionalWidgetValues(node);
    const fields = node.__easyuseAnimaRegionalFields || createDefaultRegionalFields();
    if (mergeRegionalFieldInputValues(fields, node.__easyuseAnimaRegionalFieldInputValues)) {
      writeRegionalFields(node, fields, { syncInputs: false });
    } else {
      syncRegionalFieldInputs(node, fields);
    }
    return true;
  }

  /** @param {any} node */
  function isRegionalNode(node) {
    return node?.type === REGIONAL_NODE_TYPE || node?.comfyClass === REGIONAL_NODE_TYPE;
  }

  return {
    applyRegionalExecutedInputs,
    captureRegionalConfigure,
    customResolution,
    defaultConfig,
    defaultFields: createDefaultRegionalFields,
    ensureRegionalWidgetValues,
    fieldSocketName,
    findWidget,
    hideRegionalInternalWidgets,
    isRegionalFieldInput,
    isRegionalNode,
    normalizeConfigValue,
    normalizedConfigString,
    pruneDisconnectedRegionalFieldInputValues,
    readResolution,
    regionalConfigWidget,
    regionalFieldDisplayText,
    regionalFieldInputLinked,
    regionalFieldsWidget,
    removeRegionalInternalInputSockets,
    repairRegionalConditioningWidgets,
    setCustomResolution,
    setRegionalWidgetValue,
    syncRegionalFieldInputs,
    syncRegionalValues,
    updateRegionalConfigCanvas,
    writeRegionalConfig,
    writeRegionalFields,
  };
}

export {
  createRegionalRuntime,
};
