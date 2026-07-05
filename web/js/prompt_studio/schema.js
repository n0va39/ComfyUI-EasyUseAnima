// @ts-check

import {
  ADVANCED_BOOLEAN_WIDGET_NAMES,
  ADVANCED_DEFAULT_FIELDS,
  ADVANCED_FIELD_LABELS,
  ADVANCED_FIELD_SOCKET_PREFIX,
  ADVANCED_FIELD_TYPES,
  ADVANCED_FLOAT_WIDGET_NAMES,
  ADVANCED_INT_WIDGET_NAMES,
  ADVANCED_RESOLUTION_BUCKETS,
  ADVANCED_WIDGET_VALUE_DEFAULTS,
  ARTIST_MIX_MODES,
  CUSTOM_ADVANCED_RESOLUTION_BUCKET,
  DEFAULT_ADVANCED_RESOLUTION_BUCKET,
  DEFAULT_ADVANCED_RESOLUTION_SIZE,
  NAIA_ADVANCED_RESOLUTION_BUCKET,
} from "./constants.js";
import {
  advancedResolutionLabel,
  resolutionRatioLabel,
} from "./utils.js";

function advancedDefaultFields() {
  return JSON.parse(JSON.stringify(ADVANCED_DEFAULT_FIELDS));
}

function normalizeAdvancedBooleanValue(value, fallback) {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "1", "yes", "on", "enabled"].includes(normalized)) {
      return true;
    }
    if (["false", "0", "no", "off", "disabled"].includes(normalized)) {
      return false;
    }
    if (!normalized) {
      return !!fallback;
    }
  }
  return value == null ? !!fallback : !!value;
}

function normalizeArtistMixMode(value) {
  const mode = String(value || "off");
  return ARTIST_MIX_MODES.includes(mode) ? mode : "off";
}

function advancedResolutionOptions(bucket) {
  const values = ADVANCED_RESOLUTION_BUCKETS[bucket] || ADVANCED_RESOLUTION_BUCKETS[DEFAULT_ADVANCED_RESOLUTION_BUCKET];
  return [...values]
    .sort((a, b) => (a[0] / a[1]) - (b[0] / b[1]) || a[0] - b[0] || a[1] - b[1])
    .map(([width, height]) => advancedResolutionLabel(width, height));
}

function normalizeAdvancedResolutionBucket(value) {
  const bucket = String(value || "").trim();
  if (bucket === CUSTOM_ADVANCED_RESOLUTION_BUCKET || bucket === NAIA_ADVANCED_RESOLUTION_BUCKET) {
    return bucket;
  }
  return Object.prototype.hasOwnProperty.call(ADVANCED_RESOLUTION_BUCKETS, bucket)
    ? bucket
    : DEFAULT_ADVANCED_RESOLUTION_BUCKET;
}

function resolutionRatioFromLabel(value) {
  const match = String(value || "").match(/(\d+)\s*(?:\*|x|×)\s*(\d+)/);
  if (!match) {
    return "";
  }
  return resolutionRatioLabel(Number(match[1]), Number(match[2]));
}

function normalizeAdvancedResolutionSize(bucket, value) {
  if (bucket === CUSTOM_ADVANCED_RESOLUTION_BUCKET || bucket === NAIA_ADVANCED_RESOLUTION_BUCKET) {
    return String(value || DEFAULT_ADVANCED_RESOLUTION_SIZE);
  }
  const options = advancedResolutionOptions(bucket);
  const raw = String(value || "").trim();
  if (options.includes(raw)) {
    return raw;
  }
  const sameRatio = resolutionRatioFromLabel(raw);
  if (sameRatio) {
    const matched = options.find((option) => resolutionRatioFromLabel(option) === sameRatio);
    if (matched) {
      return matched;
    }
  }
  return options.includes(DEFAULT_ADVANCED_RESOLUTION_SIZE)
    ? DEFAULT_ADVANCED_RESOLUTION_SIZE
    : options[0];
}

function normalizeAdvancedWidgetQueueValue(name, value) {
  const fallback = ADVANCED_WIDGET_VALUE_DEFAULTS[name];
  if (name === "advanced_fields") {
    return String(value || fallback || advancedDefaultFieldsValue());
  }
  if (ADVANCED_BOOLEAN_WIDGET_NAMES.has(name)) {
    return normalizeAdvancedBooleanValue(value, fallback);
  }
  if (ADVANCED_INT_WIDGET_NAMES.has(name)) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.trunc(parsed) : fallback;
  }
  if (ADVANCED_FLOAT_WIDGET_NAMES.has(name)) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  if (name === "artist_mix_mode") {
    return normalizeArtistMixMode(value || fallback);
  }
  if (name === "resolution_bucket") {
    return normalizeAdvancedResolutionBucket(value || fallback);
  }
  if (name === "resolution_size") {
    return String(value || fallback || DEFAULT_ADVANCED_RESOLUTION_SIZE);
  }
  if (name === "wildcard_seed_after_generate") {
    return String(value || fallback || "fixed");
  }
  return value == null || value === "" ? fallback : value;
}

function normalizeAdvancedField(field, index = 0) {
  const pane = field?.pane === "negative" ? "negative" : "positive";
  let type = ADVANCED_FIELD_TYPES.includes(field?.type) ? field.type : "general";
  if (pane === "negative" && type === "trigger") {
    type = "general";
  }
  const label = String(field?.label || ADVANCED_FIELD_LABELS[type] || "General Tags");
  return {
    id: String(field?.id || `${pane}_${type}_${index + 1}`),
    pane,
    type,
    label,
    text: String(field?.text || ""),
    height: Math.max(42, Math.round(Number(field?.height) || 72)),
    heightMode: field?.heightMode === "manual" ? "manual" : "auto",
    enabled: field?.enabled !== false,
    pin: type === "trigger" ? field?.pin !== false : false,
  };
}

function advancedDefaultFieldsValue() {
  return JSON.stringify(advancedDefaultFields().map((field, index) => normalizeAdvancedField(field, index)));
}

function normalizeAdvancedFieldsValue(value) {
  if (value == null) {
    return "";
  }
  try {
    const parsed = typeof value === "string" ? JSON.parse(value || "[]") : value;
    if (!Array.isArray(parsed) || !parsed.length) {
      return "";
    }
    return JSON.stringify(parsed.map((field, index) => normalizeAdvancedField(field, index)));
  } catch {
    return "";
  }
}

function advancedFieldInputName(field) {
  const raw = String(field?.id || "field")
    .replace(/[^a-zA-Z0-9_]/g, "_")
    .replace(/^_+|_+$/g, "");
  return `${ADVANCED_FIELD_SOCKET_PREFIX}${raw || "field"}`;
}

export {
  advancedDefaultFields,
  advancedDefaultFieldsValue,
  advancedFieldInputName,
  advancedResolutionOptions,
  normalizeAdvancedBooleanValue,
  normalizeAdvancedField,
  normalizeAdvancedFieldsValue,
  normalizeAdvancedResolutionBucket,
  normalizeAdvancedResolutionSize,
  normalizeAdvancedWidgetQueueValue,
  normalizeArtistMixMode,
};
