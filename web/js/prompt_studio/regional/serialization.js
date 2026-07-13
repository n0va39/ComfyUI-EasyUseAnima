// @ts-check

import {
  REGIONAL_CONFIG_PROPERTY,
  REGIONAL_FIELDS_PROPERTY,
  REGIONAL_WIDGET_INDEX,
} from "./constants.js";
import {
  normalizeRegionalConfig,
  normalizeRegionalFields,
} from "./schema.js";

export function normalizeRegionalFieldsString(value) {
  return JSON.stringify(normalizeRegionalFields(value));
}

export function normalizeRegionalConfigString(value, resolution = null) {
  return JSON.stringify(normalizeRegionalConfig(value, resolution));
}

export function serializedRegionalValue(serialized, name, resolution = null) {
  const propertyName = name === "regional_fields" ? REGIONAL_FIELDS_PROPERTY : REGIONAL_CONFIG_PROPERTY;
  const propertyValue = serialized?.properties?.[propertyName];
  if (propertyValue != null && String(propertyValue).trim()) {
    return name === "regional_fields"
      ? normalizeRegionalFieldsString(propertyValue)
      : normalizeRegionalConfigString(propertyValue, resolution);
  }
  const widgetValue = serialized?.widgets_values?.[REGIONAL_WIDGET_INDEX[name]];
  if (widgetValue != null && String(widgetValue).trim()) {
    return name === "regional_fields"
      ? normalizeRegionalFieldsString(widgetValue)
      : normalizeRegionalConfigString(widgetValue, resolution);
  }
  return "";
}
