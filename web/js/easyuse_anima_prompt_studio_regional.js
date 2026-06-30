import { app } from "../../../scripts/app.js";
import {
  PROMPT_STUDIO_VARIANT_FIELD_LABELS,
  PROMPT_STUDIO_VARIANT_FIELD_TYPES,
  PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET,
  PROMPT_STUDIO_DEFAULT_RESOLUTION_BUCKET,
  PROMPT_STUDIO_DEFAULT_RESOLUTION_SIZE,
  PROMPT_STUDIO_RESOLUTION_BUCKETS,
  PROMPT_STUDIO_WILDCARD_DEFAULT_MODE,
  PROMPT_STUDIO_WILDCARD_MODES,
  PROMPT_STUDIO_WILDCARD_SEED_CONTROLS,
  createPromptStudioActionButton,
  ensurePromptStudioVariantStyle,
  promptStudioFieldIndexLabel,
  promptStudioFieldLabel,
  promptStudioText,
  refreshPromptStudioHighlights,
  registerPromptStudioTextarea,
  requestPromptStudioOverlaySync,
  schedulePromptStudioFieldHighlight,
  updatePromptStudioFieldHighlight,
} from "./easyuse_anima_prompt_studio_common.js";

const REGIONAL_NODE_TYPE = "EasyUseAnimaPromptStudioRegional";
const REGIONAL_CONDITIONING_NODE_TYPE = "EasyUseAnimaRegionalConditioning";
const REGIONAL_FIELDS_PROPERTY = "easyuse_anima_regional_fields";
const REGIONAL_CONFIG_PROPERTY = "easyuse_anima_regional_config";
const REGIONAL_WIDGET_INDEX = {
  regional_fields: 0,
  regional_config: 1,
  resolution_bucket: 2,
  resolution_size: 3,
  resolution_custom_width: 4,
  resolution_custom_height: 5,
  wildcard_mode: 6,
  wildcard_seed: 7,
  wildcard_seed_after_generate: 8,
};
const REGIONAL_INTERNAL_WIDGET_NAMES = new Set(Object.keys(REGIONAL_WIDGET_INDEX));
const REGIONAL_FIELD_TYPES = PROMPT_STUDIO_VARIANT_FIELD_TYPES;
const REGIONAL_FIELD_LABELS = PROMPT_STUDIO_VARIANT_FIELD_LABELS;
const REGIONAL_NODE_MIN_WIDTH = 560;
const REGIONAL_NODE_DEFAULT_WIDTH = 620;
const REGIONAL_EDITOR_MIN_VIEWPORT_HEIGHT = 360;
const REGIONAL_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT = 640;
const MASK_MIN_SIZE = 0.01;
const MASK_HANDLE_RADIUS = 0.018;
const MASK_HANDLE_NAMES = ["nw", "n", "ne", "e", "se", "s", "sw", "w"];
const REGIONAL_LAYOUT_REASON_PRIORITY = {
  layout: 0,
  render: 1,
  textarea: 1,
  executed: 1,
  settings: 1,
  resize: 3,
};
const REGIONAL_CONDITIONING_AREA_MODES = new Set(["mask bounds", "default"]);
let activeMaskPopover = null;

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function findWidget(node, name) {
  return node?.widgets?.find((widget) => widget.name === name) || null;
}

function isRegionalConditioningAreaMode(value) {
  return REGIONAL_CONDITIONING_AREA_MODES.has(String(value || ""));
}

function normalizeRegionalConditioningWidgetValues(values) {
  const raw = Array.isArray(values) ? values : [];
  let maskStrength = null;
  let setCondArea = null;
  for (const value of raw) {
    if (maskStrength == null && value != null && value !== "") {
      const number = Number(value);
      if (Number.isFinite(number) && !isRegionalConditioningAreaMode(value)) {
        maskStrength = number;
        continue;
      }
    }
    if (setCondArea == null && isRegionalConditioningAreaMode(value)) {
      setCondArea = String(value);
    }
  }
  return [
    maskStrength == null ? 1.0 : maskStrength,
    setCondArea || "mask bounds",
  ];
}

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

function wrapRegionalConditioningNode(nodeType) {
  if (nodeType.prototype.__easyuseAnimaRegionalConditioningWrapped) {
    return;
  }
  nodeType.prototype.__easyuseAnimaRegionalConditioningWrapped = true;

  const onNodeCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function () {
    const result = onNodeCreated?.apply(this, arguments);
    repairRegionalConditioningWidgets(this);
    return result;
  };

  const onConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function (serialized) {
    if (serialized && Array.isArray(serialized.widgets_values)) {
      serialized.widgets_values = normalizeRegionalConditioningWidgetValues(serialized.widgets_values);
    }
    const result = onConfigure?.apply(this, arguments);
    repairRegionalConditioningWidgets(this, serialized);
    return result;
  };

  const onSerialize = nodeType.prototype.onSerialize;
  nodeType.prototype.onSerialize = function (serialized) {
    const result = onSerialize?.apply(this, arguments);
    repairRegionalConditioningWidgets(this, serialized);
    return result;
  };
}

function firstValue(value, fallback = null) {
  return Array.isArray(value) ? (value.length ? value[0] : fallback) : (value ?? fallback);
}

function asBool(value, fallback = false) {
  if (value == null) {
    return fallback;
  }
  if (typeof value === "string") {
    return ["true", "1", "yes", "on", "enabled"].includes(value.trim().toLowerCase());
  }
  return !!value;
}

function asInt(value, fallback = 0) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function ratioLabel(width, height) {
  const gcd = (a, b) => (b ? gcd(b, a % b) : a);
  const divisor = gcd(Math.max(1, width), Math.max(1, height));
  return `${Math.floor(width / divisor)}:${Math.floor(height / divisor)}`;
}

function resolutionLabel(width, height) {
  return `${width} * ${height} (${ratioLabel(width, height)})`;
}

function resolutionOptions(bucket) {
  const values = PROMPT_STUDIO_RESOLUTION_BUCKETS[bucket]
    || PROMPT_STUDIO_RESOLUTION_BUCKETS[PROMPT_STUDIO_DEFAULT_RESOLUTION_BUCKET];
  return [...values]
    .sort((a, b) => (a[0] / a[1]) - (b[0] / b[1]) || a[0] - b[0] || a[1] - b[1])
    .map(([width, height]) => resolutionLabel(width, height));
}

function normalizeResolutionBucket(value) {
  const bucket = String(value || "").trim();
  if (bucket === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET) {
    return bucket;
  }
  return Object.prototype.hasOwnProperty.call(PROMPT_STUDIO_RESOLUTION_BUCKETS, bucket)
    ? bucket
    : PROMPT_STUDIO_DEFAULT_RESOLUTION_BUCKET;
}

function resolutionRatioFromLabel(value) {
  const match = String(value || "").match(/(\d+)\s*(?:\*|x|×)\s*(\d+)/i);
  if (!match) {
    return "";
  }
  return ratioLabel(Number(match[1]), Number(match[2]));
}

function normalizeResolutionSize(bucket, value) {
  if (bucket === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET) {
    return String(value || PROMPT_STUDIO_DEFAULT_RESOLUTION_SIZE);
  }
  const options = resolutionOptions(bucket);
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
  return options.includes(PROMPT_STUDIO_DEFAULT_RESOLUTION_SIZE)
    ? PROMPT_STUDIO_DEFAULT_RESOLUTION_SIZE
    : options[0];
}

function snapResolution32(value, fallback = 1024) {
  const raw = Number.parseInt(value, 10);
  const base = Number.isFinite(raw) && raw > 0 ? raw : fallback;
  return Math.max(32, Math.round(base / 32) * 32);
}

function customResolution(node) {
  return {
    width: snapResolution32(findWidget(node, "resolution_custom_width")?.value, 1024),
    height: snapResolution32(findWidget(node, "resolution_custom_height")?.value, 1024),
  };
}

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

function setCustomResolution(node, width, height, { normalize = false } = {}) {
  const nextWidth = normalize ? snapResolution32(width, 1024) : String(width || "");
  const nextHeight = normalize ? snapResolution32(height, 1024) : String(height || "");
  setRegionalWidgetValue(node, "resolution_custom_width", nextWidth);
  setRegionalWidgetValue(node, "resolution_custom_height", nextHeight);
  if (normalize) {
    setRegionalWidgetValue(node, "resolution_size", resolutionLabel(nextWidth, nextHeight));
  }
  updateRegionalConfigCanvas(node);
}

function readResolution(node) {
  const width = Math.max(32, asInt(findWidget(node, "resolution_custom_width")?.value, 1024));
  const height = Math.max(32, asInt(findWidget(node, "resolution_custom_height")?.value, 1024));
  const size = String(findWidget(node, "resolution_size")?.value || "");
  const match = size.match(/(\d+)\s*(?:\*|x|×)\s*(\d+)/i);
  if (normalizeResolutionBucket(findWidget(node, "resolution_bucket")?.value) !== PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET && match) {
    return {
      width: Math.max(32, asInt(match[1], width)),
      height: Math.max(32, asInt(match[2], height)),
    };
  }
  return { width, height };
}

function defaultFields() {
  return [
    {
      id: "positive_quality",
      pane: "positive",
      type: "quality",
      label: "Quality Tags",
      text: "newest, masterpiece, best quality, score_8, score_7:, highres, absurdres, very aesthetic",
      height: 72,
      enabled: true,
      pin: false,
      collapsed: false,
      mask_ids: [],
    },
    {
      id: "positive_artist",
      pane: "positive",
      type: "artist",
      label: "Artist Tags",
      text: "",
      height: 72,
      enabled: true,
      pin: false,
      collapsed: false,
      mask_ids: [],
    },
    {
      id: "positive_trigger",
      pane: "positive",
      type: "trigger",
      label: "Trigger Words",
      text: "",
      height: 72,
      enabled: true,
      pin: true,
      collapsed: false,
      mask_ids: [],
    },
    {
      id: "positive_general",
      pane: "positive",
      type: "general",
      label: "General Tags",
      text: "",
      height: 150,
      enabled: true,
      pin: false,
      collapsed: false,
      mask_ids: [],
    },
    {
      id: "negative_general",
      pane: "negative",
      type: "general",
      label: "Negative Prompt",
      text: "",
      height: 120,
      enabled: true,
      pin: false,
      collapsed: false,
      mask_ids: [],
    },
  ];
}

function defaultConfig(node = null) {
  const { width, height } = node ? readResolution(node) : { width: 1024, height: 1024 };
  return {
    version: 1,
    canvas: {
      width,
      height,
      aspect_ratio: ratioLabel(width, height),
      source: "resolution_fields",
    },
    mask_authoring: {
      render_space: "image_pixels",
      storage_space: "normalized_canvas",
      preview_enabled: true,
    },
    global_prompt: "",
    negative_prompt: "",
    next_mask_id: 1,
    masks: [],
    regional_enabled: false,
    mask_prompts: [],
    assignments: [],
    artist_mix: {},
    conditioning_settings: {},
    regional_settings: {},
  };
}

function parseJson(value, fallback) {
  if (value == null || value === "") {
    return deepClone(fallback);
  }
  try {
    const parsed = typeof value === "string" ? JSON.parse(value) : value;
    return parsed == null ? deepClone(fallback) : parsed;
  } catch {
    return deepClone(fallback);
  }
}

function normalizeMaskIds(value) {
  const values = Array.isArray(value) ? value : String(value ?? "").split(/[,\s;]+/);
  const result = [];
  for (const raw of values) {
    const id = asInt(raw, 0);
    if (id > 0 && !result.includes(id)) {
      result.push(id);
    }
  }
  return result;
}

function normalizeField(field, index = 0) {
  const pane = field?.pane === "negative" ? "negative" : "positive";
  let type = String(field?.type || "general").toLowerCase();
  if (!REGIONAL_FIELD_TYPES.includes(type)) {
    type = "general";
  }
  if (pane === "negative" && type === "trigger") {
    type = "general";
  }
  const label = String(field?.label || REGIONAL_FIELD_LABELS[type] || "Prompt").trim();
  const id = String(field?.id || `${pane}_${type}_${index + 1}`).trim() || `${pane}_${type}_${index + 1}`;
  return {
    id,
    pane,
    type,
    label,
    text: String(field?.text || ""),
    height: Math.max(36, asInt(field?.height, 72)),
    enabled: asBool(field?.enabled, true),
    pin: asBool(field?.pin, type === "trigger"),
    collapsed: asBool(field?.collapsed, false),
    mask_ids: pane === "positive" ? normalizeMaskIds(field?.mask_ids) : [],
  };
}

function normalizeFieldsValue(value) {
  const parsed = parseJson(value, []);
  const raw = Array.isArray(parsed) && parsed.length ? parsed : defaultFields();
  const fields = raw.map((field, index) => normalizeField(field, index));
  return fields.length ? fields : defaultFields();
}

function normalizeGeometry(geometry) {
  const raw = geometry && typeof geometry === "object" ? geometry : {};
  const shape = String(raw.type || "rect").toLowerCase() === "ellipse" ? "ellipse" : "rect";
  const x = clamp(Number(raw.x ?? 0.1), 0, 1);
  const y = clamp(Number(raw.y ?? 0.1), 0, 1);
  const width = clamp(Number(raw.width ?? 0.35), 0.01, 1);
  const height = clamp(Number(raw.height ?? 0.35), 0.01, 1);
  return {
    type: shape,
    x: Number(clamp(x, 0, 0.99).toFixed(6)),
    y: Number(clamp(y, 0, 0.99).toFixed(6)),
    width: Number(clamp(width, 0.01, 1 - x).toFixed(6)),
    height: Number(clamp(height, 0.01, 1 - y).toFixed(6)),
  };
}

function normalizeMask(mask, index) {
  const maskId = asInt(mask?.mask_id ?? mask?.id, index + 1);
  const label = String(mask?.label || mask?.name || `Mask ${maskId}`);
  const color = /^#[0-9A-Fa-f]{6}$/.test(String(mask?.color || "")) ? String(mask.color) : "#3b82f6";
  return {
    mask_id: maskId,
    label,
    name: String(mask?.name || ""),
    color,
    enabled: asBool(mask?.enabled, true),
    geometry: normalizeGeometry(mask?.geometry),
    strokes: Array.isArray(mask?.strokes) ? mask.strokes : undefined,
    shapes: Array.isArray(mask?.shapes) ? mask.shapes : undefined,
  };
}

function normalizeConfigValue(node, value) {
  const parsed = parseJson(value, {});
  const base = defaultConfig(node);
  const rawMasks = Array.isArray(parsed.masks) ? parsed.masks : (Array.isArray(parsed.regions) ? parsed.regions : []);
  const used = new Set();
  const masks = [];
  for (const [index, raw] of rawMasks.entries()) {
    const mask = normalizeMask(raw, index);
    if (mask.mask_id <= 0 || used.has(mask.mask_id)) {
      continue;
    }
    used.add(mask.mask_id);
    masks.push(mask);
  }
  const maxMaskId = masks.reduce((max, mask) => Math.max(max, mask.mask_id), 0);
  return {
    ...base,
    artist_mix: parsed.artist_mix && typeof parsed.artist_mix === "object" ? parsed.artist_mix : {},
    conditioning_settings: parsed.conditioning_settings && typeof parsed.conditioning_settings === "object" ? parsed.conditioning_settings : {},
    regional_settings: parsed.regional_settings && typeof parsed.regional_settings === "object" ? parsed.regional_settings : {},
    mask_authoring: {
      ...base.mask_authoring,
      ...(parsed.mask_authoring && typeof parsed.mask_authoring === "object" ? parsed.mask_authoring : {}),
    },
    next_mask_id: Math.max(1, asInt(parsed.next_mask_id, 1), maxMaskId + 1),
    masks,
  };
}

function regionalFieldsWidget(node) {
  return findWidget(node, "regional_fields");
}

function regionalConfigWidget(node) {
  return findWidget(node, "regional_config");
}

function syncBackup(node, fieldsValue, configValue) {
  node.properties ||= {};
  node.properties[REGIONAL_FIELDS_PROPERTY] = String(fieldsValue || "");
  node.properties[REGIONAL_CONFIG_PROPERTY] = String(configValue || "");
}

function fieldsBackup(node) {
  const value = node?.properties?.[REGIONAL_FIELDS_PROPERTY];
  return typeof value === "string" && value.trim() ? value : "";
}

function configBackup(node) {
  const value = node?.properties?.[REGIONAL_CONFIG_PROPERTY];
  return typeof value === "string" && value.trim() ? value : "";
}

function normalizedFieldsString(value) {
  return JSON.stringify(normalizeFieldsValue(value));
}

function normalizedConfigString(node, value) {
  return JSON.stringify(normalizeConfigValue(node, value));
}

function serializedRegionalValue(node, serialized, name) {
  const propertyName = name === "regional_fields" ? REGIONAL_FIELDS_PROPERTY : REGIONAL_CONFIG_PROPERTY;
  const propertyValue = serialized?.properties?.[propertyName];
  if (propertyValue != null && String(propertyValue).trim()) {
    return name === "regional_fields" ? normalizedFieldsString(propertyValue) : normalizedConfigString(node, propertyValue);
  }
  const widgetValue = serialized?.widgets_values?.[REGIONAL_WIDGET_INDEX[name]];
  if (widgetValue != null && String(widgetValue).trim()) {
    return name === "regional_fields" ? normalizedFieldsString(widgetValue) : normalizedConfigString(node, widgetValue);
  }
  return "";
}

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

function ensureRegionalWidgetValues(node) {
  const fieldsWidget = regionalFieldsWidget(node);
  const configWidget = regionalConfigWidget(node);
  let fieldsValue = node.__easyuseAnimaPendingRegionalFields || fieldsBackup(node) || fieldsWidget?.value || JSON.stringify(defaultFields());
  let configValue = node.__easyuseAnimaPendingRegionalConfig || configBackup(node) || configWidget?.value || JSON.stringify(defaultConfig(node));
  fieldsValue = normalizedFieldsString(fieldsValue);
  configValue = normalizedConfigString(node, configValue);
  if (fieldsWidget) {
    fieldsWidget.value = fieldsValue;
  }
  if (configWidget) {
    configWidget.value = configValue;
  }
  node.__easyuseAnimaRegionalFields = normalizeFieldsValue(fieldsValue);
  node.__easyuseAnimaRegionalConfig = normalizeConfigValue(node, configValue);
  syncBackup(node, fieldsValue, configValue);
  delete node.__easyuseAnimaPendingRegionalFields;
  delete node.__easyuseAnimaPendingRegionalConfig;
}

function writeRegionalFields(node, fields, { syncInputs = true } = {}) {
  const normalized = fields.map((field, index) => normalizeField(field, index));
  const value = JSON.stringify(normalized);
  const widget = regionalFieldsWidget(node);
  if (widget) {
    widget.value = value;
  }
  node.__easyuseAnimaRegionalFields = normalized;
  syncBackup(node, value, regionalConfigWidget(node)?.value || JSON.stringify(node.__easyuseAnimaRegionalConfig || defaultConfig(node)));
  if (syncInputs) {
    syncRegionalFieldInputs(node, normalized);
  }
}

function writeRegionalConfig(node, config) {
  const normalized = normalizeConfigValue(node, config);
  const value = JSON.stringify(normalized);
  const widget = regionalConfigWidget(node);
  if (widget) {
    widget.value = value;
  }
  node.__easyuseAnimaRegionalConfig = normalized;
  syncBackup(node, regionalFieldsWidget(node)?.value || JSON.stringify(node.__easyuseAnimaRegionalFields || defaultFields()), value);
}

function updateRegionalConfigCanvas(node) {
  const config = normalizeConfigValue(node, node.__easyuseAnimaRegionalConfig || regionalConfigWidget(node)?.value);
  const { width, height } = readResolution(node);
  config.canvas = {
    width,
    height,
    aspect_ratio: ratioLabel(width, height),
    source: "resolution_fields",
  };
  writeRegionalConfig(node, config);
}

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

function hideRegionalInternalWidgets(node) {
  for (const name of REGIONAL_INTERNAL_WIDGET_NAMES) {
    hideRegionalInternalWidget(node, name);
  }
}

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

function normalizeWildcardMode(value) {
  return PROMPT_STUDIO_WILDCARD_MODES.includes(String(value || ""))
    ? String(value)
    : PROMPT_STUDIO_WILDCARD_DEFAULT_MODE;
}

function normalizeSeedControl(value) {
  return PROMPT_STUDIO_WILDCARD_SEED_CONTROLS.includes(String(value || ""))
    ? String(value)
    : "fixed";
}

function createRegionalWildcardBar(node) {
  const modeWidget = findWidget(node, "wildcard_mode");
  const seedWidget = findWidget(node, "wildcard_seed");
  const controlWidget = findWidget(node, "wildcard_seed_after_generate");
  if (!modeWidget || !seedWidget || !controlWidget) {
    return document.createDocumentFragment();
  }

  const row = document.createElement("div");
  row.className = "easyuse-anima-advanced-wildcardbar";
  row.title = promptStudioText("advanced.wildcardTitle");

  const modeSelect = document.createElement("select");
  modeSelect.setAttribute("aria-label", promptStudioText("advanced.wildcard"));
  const modeValue = normalizeWildcardMode(modeWidget.value);
  for (const mode of PROMPT_STUDIO_WILDCARD_MODES) {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = mode;
    option.selected = mode === modeValue;
    modeSelect.append(option);
  }

  const seedInput = document.createElement("input");
  seedInput.type = "number";
  seedInput.min = "0";
  seedInput.step = "1";
  seedInput.value = String(seedWidget.value ?? "0");
  seedInput.setAttribute("aria-label", promptStudioText("advanced.wildcardSeed"));

  const controlSelect = document.createElement("select");
  controlSelect.setAttribute("aria-label", promptStudioText("advanced.wildcardSeedControl"));
  const controlValue = modeValue === "순차"
    ? "increment"
    : normalizeSeedControl(controlWidget.value);
  for (const control of PROMPT_STUDIO_WILDCARD_SEED_CONTROLS) {
    const option = document.createElement("option");
    option.value = control;
    option.textContent = control;
    option.selected = control === controlValue;
    controlSelect.append(option);
  }
  controlSelect.disabled = modeValue === "순차";

  const syncMode = () => {
    const nextMode = normalizeWildcardMode(modeSelect.value);
    setRegionalWidgetValue(node, "wildcard_mode", nextMode);
    if (nextMode === "순차") {
      setRegionalWidgetValue(node, "wildcard_seed_after_generate", "increment");
    }
    renderRegionalEditor(node);
  };
  const syncSeed = () => {
    const seed = Math.max(0, Math.trunc(Number(seedInput.value) || 0));
    seedInput.value = String(seed);
    setRegionalWidgetValue(node, "wildcard_seed", seed);
  };
  const syncControl = () => {
    setRegionalWidgetValue(node, "wildcard_seed_after_generate", normalizeSeedControl(controlSelect.value));
  };

  modeSelect.addEventListener("change", syncMode);
  seedInput.addEventListener("change", syncSeed);
  seedInput.addEventListener("blur", syncSeed);
  controlSelect.addEventListener("change", syncControl);
  row.append(modeSelect, seedInput, controlSelect);
  return row;
}

function createRegionalResolutionBar(node) {
  const bucketWidget = findWidget(node, "resolution_bucket");
  const sizeWidget = findWidget(node, "resolution_size");
  if (!bucketWidget || !sizeWidget) {
    return document.createDocumentFragment();
  }

  const bucketValue = normalizeResolutionBucket(bucketWidget.value);
  const custom = customResolution(node);
  const sizeValue = bucketValue === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET
    ? resolutionLabel(custom.width, custom.height)
    : normalizeResolutionSize(bucketValue, sizeWidget.value);
  if (bucketWidget.value !== bucketValue) {
    setRegionalWidgetValue(node, "resolution_bucket", bucketValue);
  }
  if (sizeWidget.value !== sizeValue) {
    setRegionalWidgetValue(node, "resolution_size", sizeValue);
  }

  const row = document.createElement("div");
  row.className = "easyuse-anima-advanced-resolutionbar";
  row.title = promptStudioText("advanced.resolutionTitle");

  const bucketSelect = document.createElement("select");
  bucketSelect.setAttribute("aria-label", promptStudioText("advanced.resolutionBucket"));
  for (const bucket of Object.keys(PROMPT_STUDIO_RESOLUTION_BUCKETS)) {
    const option = document.createElement("option");
    option.value = bucket;
    option.textContent = bucket;
    option.selected = bucket === bucketValue;
    bucketSelect.append(option);
  }
  const customOption = document.createElement("option");
  customOption.value = PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET;
  customOption.textContent = PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET;
  customOption.selected = bucketValue === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET;
  bucketSelect.append(customOption);

  const valueBox = document.createElement("div");
  const renderPresetSelect = (bucket, selected) => {
    valueBox.innerHTML = "";
    valueBox.className = "";
    const sizeSelect = document.createElement("select");
    sizeSelect.setAttribute("aria-label", promptStudioText("advanced.resolutionSize"));
    for (const label of resolutionOptions(bucket)) {
      const option = document.createElement("option");
      option.value = label;
      option.textContent = label;
      option.selected = label === selected;
      sizeSelect.append(option);
    }
    sizeSelect.addEventListener("change", () => {
      setRegionalWidgetValue(node, "resolution_size", normalizeResolutionSize(bucketSelect.value, sizeSelect.value));
      updateRegionalConfigCanvas(node);
      scheduleRegionalLayout(node, "settings");
    });
    valueBox.append(sizeSelect);
  };
  const renderCustomInputs = () => {
    valueBox.innerHTML = "";
    valueBox.className = "easyuse-anima-advanced-resolution-custom";
    const widthInput = document.createElement("input");
    widthInput.type = "number";
    widthInput.min = "32";
    widthInput.step = "32";
    widthInput.value = String(customResolution(node).width);
    widthInput.setAttribute("aria-label", promptStudioText("advanced.customWidth"));
    const separator = document.createElement("span");
    separator.textContent = "×";
    const heightInput = document.createElement("input");
    heightInput.type = "number";
    heightInput.min = "32";
    heightInput.step = "32";
    heightInput.value = String(customResolution(node).height);
    heightInput.setAttribute("aria-label", promptStudioText("advanced.customHeight"));
    const syncRaw = () => {
      setRegionalWidgetValue(node, "resolution_custom_width", widthInput.value);
      setRegionalWidgetValue(node, "resolution_custom_height", heightInput.value);
    };
    const normalize = () => {
      const width = snapResolution32(widthInput.value, 1024);
      const height = snapResolution32(heightInput.value, 1024);
      widthInput.value = String(width);
      heightInput.value = String(height);
      setCustomResolution(node, width, height, { normalize: true });
      scheduleRegionalLayout(node, "settings");
    };
    widthInput.addEventListener("input", syncRaw);
    heightInput.addEventListener("input", syncRaw);
    widthInput.addEventListener("change", normalize);
    heightInput.addEventListener("change", normalize);
    widthInput.addEventListener("blur", normalize);
    heightInput.addEventListener("blur", normalize);
    valueBox.append(widthInput, separator, heightInput);
    setCustomResolution(node, widthInput.value, heightInput.value, { normalize: true });
  };
  const fillSizeOptions = (bucket, selected) => {
    if (bucket === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET) {
      renderCustomInputs();
      return;
    }
    renderPresetSelect(bucket, selected);
  };
  fillSizeOptions(bucketValue, sizeValue);

  bucketSelect.addEventListener("change", () => {
    const nextBucket = normalizeResolutionBucket(bucketSelect.value);
    const nextSize = nextBucket === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET
      ? resolutionLabel(customResolution(node).width, customResolution(node).height)
      : normalizeResolutionSize(nextBucket, sizeWidget.value);
    setRegionalWidgetValue(node, "resolution_bucket", nextBucket);
    setRegionalWidgetValue(node, "resolution_size", nextSize);
    fillSizeOptions(nextBucket, nextSize);
    updateRegionalConfigCanvas(node);
    scheduleRegionalLayout(node, "settings");
    scheduleRegionalFieldHighlights(node, false);
  });

  row.append(bucketSelect, valueBox);
  updateRegionalConfigCanvas(node);
  return row;
}

function ensureRegionalStyle() {
  ensurePromptStudioVariantStyle();
}

function fieldSocketName(field) {
  return `field_${String(field.id || "field").replace(/[^A-Za-z0-9_]/g, "_") || "field"}`;
}

function isRegionalFieldInput(input) {
  return !!input?.__easyuseAnimaRegionalFieldInput
    || String(input?.name || "").startsWith("field_");
}

function regionalFieldIndexLabel(fields, field) {
  const paneFields = (fields || []).filter((item) => item.pane === field.pane);
  const paneIndex = paneFields.findIndex((item) => item.id === field.id);
  const number = Math.max(0, paneIndex) + 1;
  return field.pane === "negative" ? `neg${number}` : `${number}`;
}

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

function syncRegionalFieldInputs(node, fields) {
  if (!node || typeof node.addInput !== "function") {
    return;
  }

  const wanted = new Map();
  (fields || []).forEach((field) => {
    const normalized = normalizeField(field, wanted.size);
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
    input.label = `${indexLabel}. ${promptStudioFieldLabel(field)}`;
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

function regionalFieldInputLinked(node, field) {
  const name = fieldSocketName(field);
  return !!node.inputs?.some((input) => input.name === name && input.link != null);
}

function regionalFieldDisplayText(node, field) {
  const name = fieldSocketName(field);
  const values = node.__easyuseAnimaRegionalFieldInputValues || {};
  if (regionalFieldInputLinked(node, field) && Object.prototype.hasOwnProperty.call(values, name)) {
    return String(values[name] ?? "");
  }
  return String(field?.text || "");
}

function mergeRegionalFieldInputValues(node, fields, values) {
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

function createButton(label, title, onClick) {
  return createPromptStudioActionButton(label, title, onClick);
}

function collectRegionalEditorFields(node) {
  const editor = node.__easyuseAnimaRegionalEditorEl;
  if (!editor) {
    return node.__easyuseAnimaRegionalFields || defaultFields();
  }
  const fields = [];
  for (const card of editor.querySelectorAll(".easyuse-anima-regional-field")) {
    const id = card.dataset.fieldId || "";
    const existing = (node.__easyuseAnimaRegionalFields || []).find((field) => field.id === id) || {};
    const pane = card.dataset.pane || existing.pane || "positive";
    const enabled = card.querySelector("[data-role='enabled']")?.checked ?? true;
    const label = card.querySelector("[data-role='label']")?.value ?? existing.label ?? "";
    const type = card.querySelector("[data-role='type']")?.value ?? existing.type ?? "general";
    const text = card.querySelector("[data-role='text']")?.value ?? "";
    const maskControl = card.querySelector("[data-role='mask_ids']");
    let maskIds = [];
    if (maskControl instanceof HTMLSelectElement) {
      maskIds = Array.from(maskControl.selectedOptions).map((option) => option.value);
    } else if (maskControl) {
      maskIds = normalizeMaskIds(maskControl.dataset.maskIds);
    }
    fields.push(normalizeField({
      ...existing,
      id,
      pane,
      enabled,
      label,
      type,
      text,
      mask_ids: maskIds,
      height: Math.max(36, card.querySelector("[data-role='text']")?.offsetHeight || existing.height || 72),
    }, fields.length));
  }
  return fields;
}

function syncRegionalValues(node, serialized = null) {
  const fields = collectRegionalEditorFields(node);
  const config = node.__easyuseAnimaRegionalConfig || normalizeConfigValue(node, regionalConfigWidget(node)?.value);
  writeRegionalFields(node, fields, { syncInputs: false });
  writeRegionalConfig(node, config);
  if (!serialized || !Array.isArray(serialized.widgets_values)) {
    return;
  }
  serialized.properties ||= {};
  serialized.properties[REGIONAL_FIELDS_PROPERTY] = regionalFieldsWidget(node)?.value || JSON.stringify(fields);
  serialized.properties[REGIONAL_CONFIG_PROPERTY] = regionalConfigWidget(node)?.value || JSON.stringify(config);
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

function maskOptionLabel(mask) {
  return `${mask.mask_id}: ${mask.name || mask.label || `Mask ${mask.mask_id}`}`;
}

function maskSelectionLabel(config, selectedIds) {
  const ids = normalizeMaskIds(selectedIds);
  if (!ids.length) {
    return "None";
  }
  const masks = Array.isArray(config.masks) ? config.masks : [];
  const labels = ids.map((id) => {
    const mask = masks.find((item) => item.mask_id === id);
    return mask ? maskOptionLabel(mask) : `${id}: missing mask`;
  });
  if (labels.length <= 2) {
    return labels.join(", ");
  }
  return `${labels.length} masks`;
}

function closeMaskPopover() {
  if (!activeMaskPopover) {
    return;
  }
  activeMaskPopover.cleanup?.();
  activeMaskPopover.remove?.();
  activeMaskPopover = null;
}

function positionMaskPopover(button, popover) {
  const rect = button.getBoundingClientRect();
  const margin = 8;
  const width = Math.max(rect.width, 180);
  popover.style.minWidth = `${width}px`;
  const popoverWidth = Number(popover.offsetWidth) || width;
  const left = Math.max(margin, Math.min(rect.left, window.innerWidth - popoverWidth - margin));
  const top = Math.min(rect.bottom + 4, window.innerHeight - margin);
  popover.style.left = `${left}px`;
  popover.style.top = `${top}px`;
}

function eventTargetInside(element, target) {
  return target instanceof Node && !!element?.contains?.(target);
}

function updateMaskButton(button, config, ids) {
  const normalized = normalizeMaskIds(ids);
  button.dataset.maskIds = normalized.join(",");
  button.textContent = maskSelectionLabel(config, normalized);
  button.classList.toggle("has-mask", normalized.length > 0);
  button.title = normalized.length ? button.textContent : "No mask selected";
}

function openMaskPopover(node, button, config, selectedIds, onChange) {
  closeMaskPopover();
  const workingIds = new Set(normalizeMaskIds(selectedIds));
  const popover = document.createElement("div");
  popover.className = "easyuse-anima-regional-mask-popover";
  const applyIds = () => {
    const ids = [...workingIds].sort((a, b) => a - b);
    updateMaskButton(button, config, ids);
    onChange?.(ids);
  };
  const addOption = (label, id = null) => {
    const row = document.createElement("label");
    row.className = "easyuse-anima-regional-mask-option";
    const input = document.createElement("input");
    input.type = id == null ? "radio" : "checkbox";
    input.checked = id == null ? workingIds.size === 0 : workingIds.has(id);
    const text = document.createElement("span");
    text.textContent = label;
    row.append(input, text);
    row.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (id == null) {
        workingIds.clear();
        applyIds();
        closeMaskPopover();
        return;
      }
      if (workingIds.has(id)) {
        workingIds.delete(id);
      } else {
        workingIds.add(id);
      }
      applyIds();
      renderOptions();
    });
    return row;
  };
  const renderOptions = () => {
    popover.innerHTML = "";
    popover.append(addOption("None", null));
    const masks = Array.isArray(config.masks) ? config.masks : [];
    for (const mask of masks) {
      popover.append(addOption(maskOptionLabel(mask), mask.mask_id));
    }
    for (const id of workingIds) {
      if (masks.some((mask) => mask.mask_id === id)) {
        continue;
      }
      popover.append(addOption(`${id}: missing mask`, id));
    }
  };
  renderOptions();
  document.body.appendChild(popover);
  positionMaskPopover(button, popover);
  const onOutsidePointer = (event) => {
    if (eventTargetInside(popover, event.target) || eventTargetInside(button, event.target)) {
      return;
    }
    closeMaskPopover();
  };
  const onKeyDown = (event) => {
    if (event.key === "Escape") {
      closeMaskPopover();
    }
  };
  const onWindowResize = () => positionMaskPopover(button, popover);
  const canvas = app.canvas?.canvas;
  document.addEventListener("pointerdown", onOutsidePointer, true);
  document.addEventListener("mousedown", onOutsidePointer, true);
  document.addEventListener("keydown", onKeyDown, true);
  window.addEventListener("resize", onWindowResize);
  window.addEventListener("blur", closeMaskPopover);
  canvas?.addEventListener?.("pointerdown", onOutsidePointer, true);
  canvas?.addEventListener?.("mousedown", onOutsidePointer, true);
  popover.cleanup = () => {
    document.removeEventListener("pointerdown", onOutsidePointer, true);
    document.removeEventListener("mousedown", onOutsidePointer, true);
    document.removeEventListener("keydown", onKeyDown, true);
    window.removeEventListener("resize", onWindowResize);
    window.removeEventListener("blur", closeMaskPopover);
    canvas?.removeEventListener?.("pointerdown", onOutsidePointer, true);
    canvas?.removeEventListener?.("mousedown", onOutsidePointer, true);
  };
  activeMaskPopover = popover;
}

function createMaskSelectorButton(node, config, selectedIds) {
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.role = "mask_ids";
  button.className = "easyuse-anima-regional-mask-button";
  updateMaskButton(button, config, selectedIds);
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    openMaskPopover(node, button, config, normalizeMaskIds(button.dataset.maskIds), () => {
      writeRegionalFields(node, collectRegionalEditorFields(node));
      scheduleRegionalFieldHighlights(node, false);
    });
  });
  return button;
}

function createFieldCard(node, field) {
  const config = node.__easyuseAnimaRegionalConfig || defaultConfig(node);
  const fields = node.__easyuseAnimaRegionalFields || defaultFields();
  const card = document.createElement("div");
  card.className = "easyuse-anima-advanced-field easyuse-anima-regional-field";
  card.classList.toggle("is-trigger", field.type === "trigger");
  card.classList.toggle("is-disabled", field.enabled === false);
  card.dataset.fieldId = field.id;
  card.dataset.pane = field.pane;

  const head = document.createElement("div");
  head.className = "easyuse-anima-field-header";

  const enabled = document.createElement("input");
  enabled.type = "checkbox";
  enabled.checked = field.enabled !== false;
  enabled.dataset.role = "enabled";
  enabled.title = "Include this field in prompt output";
  enabled.addEventListener("change", () => {
    writeRegionalFields(node, collectRegionalEditorFields(node));
    renderRegionalEditor(node);
  });

  const label = document.createElement("input");
  label.type = "text";
  label.value = field.label || "";
  label.dataset.role = "label";
  label.className = "easyuse-anima-regional-field-label-input";
  label.addEventListener("input", () => writeRegionalFields(node, collectRegionalEditorFields(node)));

  const type = document.createElement("select");
  type.dataset.role = "type";
  type.className = "easyuse-anima-regional-field-type";
  for (const typeName of REGIONAL_FIELD_TYPES) {
    const option = document.createElement("option");
    option.value = typeName;
    option.textContent = REGIONAL_FIELD_LABELS[typeName] || typeName;
    option.selected = field.type === typeName;
    type.appendChild(option);
  }
  type.addEventListener("change", () => {
    writeRegionalFields(node, collectRegionalEditorFields(node));
    renderRegionalEditor(node);
  });

  const pane = document.createElement("span");
  pane.className = "easyuse-anima-regional-pane-badge";
  pane.textContent = field.pane === "negative" ? "negative" : "positive";

  const title = document.createElement("div");
  title.className = "easyuse-anima-field-label";
  const titleText = document.createElement("span");
  titleText.textContent = `${promptStudioFieldIndexLabel(fields, field)}. ${promptStudioFieldLabel(field)}`;
  title.append(enabled, titleText);

  const tools = document.createElement("div");
  tools.className = "easyuse-anima-field-tools";
  const remove = createButton("X", "Remove this prompt field", () => {
    const fields = collectRegionalEditorFields(node).filter((item) => item.id !== field.id);
    writeRegionalFields(node, fields.length ? fields : defaultFields());
    renderRegionalEditor(node);
  });
  tools.append(label, type, pane, remove);

  head.append(title, tools);

  const textarea = document.createElement("textarea");
  const linked = regionalFieldInputLinked(node, field);
  const inputName = fieldSocketName(field);
  textarea.dataset.role = "text";
  textarea.dataset.easyuseAnimaPromptStudioVariantFieldId = field.id;
  textarea.value = regionalFieldDisplayText(node, field);
  textarea.placeholder = field.type === "artist"
    ? "@artist_tag"
    : field.type === "trigger" ? "trigger words" : "prompt tags";
  textarea.style.height = `${Math.max(44, field.height || 72)}px`;
  textarea.classList.toggle("is-linked", linked);
  textarea.title = linked ? "Connected STRING input can overwrite this prompt on queue." : "";
  const syncTextareaHeight = () => {
    textarea.style.height = "auto";
    textarea.style.height = `${Math.max(44, textarea.scrollHeight)}px`;
  };
  registerPromptStudioTextarea(node, field, textarea, {
    namespace: "regional",
    onInput: () => {
      if (linked) {
        node.__easyuseAnimaRegionalFieldInputValues ||= {};
        node.__easyuseAnimaRegionalFieldInputValues[inputName] = textarea.value;
      }
      syncTextareaHeight();
      writeRegionalFields(node, collectRegionalEditorFields(node));
      scheduleRegionalLayout(node);
    },
    onChange: () => {
      writeRegionalFields(node, collectRegionalEditorFields(node));
      scheduleRegionalLayout(node);
    },
    onManualResize: (height) => {
      field.height = Math.max(44, height);
      writeRegionalFields(node, collectRegionalEditorFields(node));
    },
    scheduleLayout: () => scheduleRegionalLayout(node),
  });

  const assignment = document.createElement("div");
  assignment.className = "easyuse-anima-regional-assignment";
  const socket = document.createElement("div");
  socket.textContent = `socket: ${fieldSocketName(field)}`;
  assignment.appendChild(socket);
  if (field.pane === "positive") {
    assignment.appendChild(createMaskSelectorButton(node, config, normalizeMaskIds(field.mask_ids)));
  } else {
    const negativeNote = document.createElement("div");
    negativeNote.textContent = "global";
    assignment.appendChild(negativeNote);
  }

  requestAnimationFrame(() => {
    if (!textarea.isConnected) {
      return;
    }
    updatePromptStudioFieldHighlight(node, field, textarea, null, true, "regional");
    schedulePromptStudioFieldHighlight(node, field, textarea, { namespace: "regional" });
    writeRegionalFields(node, collectRegionalEditorFields(node));
    scheduleRegionalLayout(node);
  });

  card.append(head, textarea, assignment);
  return card;
}

function addRegionalField(node, pane, type = "general") {
  const fields = collectRegionalEditorFields(node);
  const count = fields.filter((field) => field.pane === pane).length + 1;
  const fieldType = pane === "negative" && type === "trigger" ? "general" : type;
  fields.push(normalizeField({
    id: `${pane}_${fieldType}_${Date.now().toString(36)}`,
    pane,
    type: fieldType,
    label: pane === "negative"
      ? `Negative Prompt ${count}`
      : `${REGIONAL_FIELD_LABELS[fieldType] || "Prompt"} ${count}`,
    text: "",
    height: 90,
    enabled: true,
    mask_ids: [],
  }, fields.length));
  writeRegionalFields(node, fields);
  renderRegionalEditor(node);
}

function drawMaskCanvas(canvas, config, activeMaskId = 0) {
  const ctx = canvas.getContext("2d");
  const masks = Array.isArray(config.masks) ? config.masks : [];
  const ratio = (config.canvas?.width || 1024) / Math.max(1, config.canvas?.height || 1024);
  const width = 720;
  const height = Math.max(240, Math.round(width / ratio));
  canvas.width = width;
  canvas.height = height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#05070a";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "#334155";
  ctx.lineWidth = 1;
  ctx.strokeRect(0.5, 0.5, width - 1, height - 1);
  for (const mask of masks) {
    if (mask.enabled === false) {
      continue;
    }
    const geometry = normalizeGeometry(mask.geometry);
    const rect = geometryToCanvasRect(geometry, width, height);
    ctx.fillStyle = `${mask.color || "#3b82f6"}66`;
    ctx.strokeStyle = mask.mask_id === activeMaskId ? "#f8fafc" : (mask.color || "#3b82f6");
    ctx.lineWidth = mask.mask_id === activeMaskId ? 3 : 2;
    drawMaskShape(ctx, geometry, rect, true);
    ctx.save();
    ctx.fillStyle = "#f8fafc";
    ctx.font = "13px system-ui";
    ctx.fillText(String(mask.mask_id), rect.x + 6, rect.y + 18);
    ctx.restore();
    if (mask.mask_id === activeMaskId) {
      drawMaskHandles(ctx, geometry, width, height);
    }
  }
}

function geometryToCanvasRect(geometry, width, height) {
  return {
    x: geometry.x * width,
    y: geometry.y * height,
    width: geometry.width * width,
    height: geometry.height * height,
  };
}

function drawMaskShape(ctx, geometry, rect, fill = true) {
  ctx.beginPath();
  if (geometry.type === "ellipse") {
    ctx.ellipse(
      rect.x + rect.width / 2,
      rect.y + rect.height / 2,
      Math.max(1, rect.width / 2),
      Math.max(1, rect.height / 2),
      0,
      0,
      Math.PI * 2,
    );
  } else {
    ctx.rect(rect.x, rect.y, rect.width, rect.height);
  }
  if (fill) {
    ctx.fill();
  }
  ctx.stroke();
}

function maskHandlePoints(geometry) {
  const left = geometry.x;
  const top = geometry.y;
  const right = geometry.x + geometry.width;
  const bottom = geometry.y + geometry.height;
  const midX = geometry.x + geometry.width / 2;
  const midY = geometry.y + geometry.height / 2;
  return {
    nw: { x: left, y: top },
    n: { x: midX, y: top },
    ne: { x: right, y: top },
    e: { x: right, y: midY },
    se: { x: right, y: bottom },
    s: { x: midX, y: bottom },
    sw: { x: left, y: bottom },
    w: { x: left, y: midY },
  };
}

function drawMaskHandles(ctx, geometry, width, height) {
  const points = maskHandlePoints(geometry);
  ctx.save();
  ctx.fillStyle = "#f8fafc";
  ctx.strokeStyle = "#0f172a";
  ctx.lineWidth = 1;
  for (const point of Object.values(points)) {
    const x = point.x * width;
    const y = point.y * height;
    ctx.beginPath();
    ctx.rect(x - 4, y - 4, 8, 8);
    ctx.fill();
    ctx.stroke();
  }
  ctx.restore();
}

function canvasPoint(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: clamp((event.clientX - rect.left) / rect.width, 0, 1),
    y: clamp((event.clientY - rect.top) / rect.height, 0, 1),
  };
}

function hitTestMaskHandle(geometry, point) {
  const points = maskHandlePoints(geometry);
  for (const name of MASK_HANDLE_NAMES) {
    const handle = points[name];
    if (Math.abs(point.x - handle.x) <= MASK_HANDLE_RADIUS && Math.abs(point.y - handle.y) <= MASK_HANDLE_RADIUS) {
      return name;
    }
  }
  return "";
}

function maskContainsPoint(geometry, point) {
  if (
    point.x < geometry.x
    || point.x > geometry.x + geometry.width
    || point.y < geometry.y
    || point.y > geometry.y + geometry.height
  ) {
    return false;
  }
  if (geometry.type !== "ellipse") {
    return true;
  }
  const rx = Math.max(MASK_MIN_SIZE / 2, geometry.width / 2);
  const ry = Math.max(MASK_MIN_SIZE / 2, geometry.height / 2);
  const cx = geometry.x + geometry.width / 2;
  const cy = geometry.y + geometry.height / 2;
  return (((point.x - cx) / rx) ** 2 + ((point.y - cy) / ry) ** 2) <= 1;
}

function findMaskHandleAt(config, point, activeMaskId = 0) {
  const masks = Array.isArray(config.masks) ? config.masks : [];
  const active = masks.find((mask) => mask.mask_id === activeMaskId);
  if (!active) {
    return null;
  }
  const geometry = normalizeGeometry(active.geometry);
  const handle = hitTestMaskHandle(geometry, point);
  return handle ? { mask: active, geometry, handle } : null;
}

function findMaskAt(config, point) {
  const masks = Array.isArray(config.masks) ? [...config.masks].reverse() : [];
  for (const mask of masks) {
    const geometry = normalizeGeometry(mask.geometry);
    if (maskContainsPoint(geometry, point)) {
      return mask;
    }
  }
  return null;
}

function moveGeometry(geometry, dx, dy) {
  const width = clamp(geometry.width, MASK_MIN_SIZE, 1);
  const height = clamp(geometry.height, MASK_MIN_SIZE, 1);
  return normalizeGeometry({
    ...geometry,
    x: clamp(geometry.x + dx, 0, Math.max(0, 1 - width)),
    y: clamp(geometry.y + dy, 0, Math.max(0, 1 - height)),
    width,
    height,
  });
}

function resizeGeometry(geometry, handle, dx, dy) {
  let left = geometry.x;
  let top = geometry.y;
  let right = geometry.x + geometry.width;
  let bottom = geometry.y + geometry.height;

  if (handle.includes("w")) {
    left += dx;
  }
  if (handle.includes("e")) {
    right += dx;
  }
  if (handle.includes("n")) {
    top += dy;
  }
  if (handle.includes("s")) {
    bottom += dy;
  }

  left = clamp(left, 0, 1 - MASK_MIN_SIZE);
  top = clamp(top, 0, 1 - MASK_MIN_SIZE);
  right = clamp(right, MASK_MIN_SIZE, 1);
  bottom = clamp(bottom, MASK_MIN_SIZE, 1);

  if (right - left < MASK_MIN_SIZE) {
    if (handle.includes("w")) {
      left = right - MASK_MIN_SIZE;
    } else {
      right = left + MASK_MIN_SIZE;
    }
  }
  if (bottom - top < MASK_MIN_SIZE) {
    if (handle.includes("n")) {
      top = bottom - MASK_MIN_SIZE;
    } else {
      bottom = top + MASK_MIN_SIZE;
    }
  }

  return normalizeGeometry({
    type: geometry.type,
    x: left,
    y: top,
    width: right - left,
    height: bottom - top,
  });
}

function openMaskEditor(node) {
  const working = normalizeConfigValue(node, node.__easyuseAnimaRegionalConfig || regionalConfigWidget(node)?.value);
  let activeMaskId = working.masks[0]?.mask_id || 0;
  let drag = null;

  const backdrop = document.createElement("div");
  backdrop.className = "easyuse-anima-regional-modal-backdrop";
  const modal = document.createElement("div");
  modal.className = "easyuse-anima-regional-modal";
  const head = document.createElement("div");
  head.className = "easyuse-anima-regional-modal-head";
  const title = document.createElement("div");
  title.className = "easyuse-anima-regional-modal-title";
  title.textContent = "Mask editor";
  const resolution = readResolution(node);
  const size = document.createElement("div");
  size.textContent = `${resolution.width} x ${resolution.height}`;
  size.style.color = "#94a3b8";
  size.style.marginLeft = "auto";
  head.append(title, size);

  const body = document.createElement("div");
  body.className = "easyuse-anima-regional-modal-body";
  const canvasWrap = document.createElement("div");
  canvasWrap.className = "easyuse-anima-regional-canvas-wrap";
  const canvas = document.createElement("canvas");
  canvas.className = "easyuse-anima-regional-canvas";
  canvasWrap.appendChild(canvas);
  const sidebar = document.createElement("div");
  sidebar.className = "easyuse-anima-regional-mask-sidebar";
  const list = document.createElement("div");
  list.className = "easyuse-anima-regional-mask-list";
  const inspector = document.createElement("div");
  inspector.className = "easyuse-anima-regional-mask-inspector";
  sidebar.append(list, inspector);
  body.append(canvasWrap, sidebar);

  const foot = document.createElement("div");
  foot.className = "easyuse-anima-regional-modal-foot";
  const closeModal = () => {
    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("mouseup", onMouseUp);
    backdrop.remove();
  };
  const add = createButton("Add mask", "Create a new numbered mask", () => {
    const id = Math.max(1, asInt(working.next_mask_id, 1));
    working.next_mask_id = id + 1;
    working.masks.push({
      mask_id: id,
      label: `Mask ${id}`,
      name: "",
      color: ["#3b82f6", "#22c55e", "#f97316", "#e879f9", "#f43f5e"][(id - 1) % 5],
      enabled: true,
      geometry: {
        type: "rect",
        x: clamp(0.08 + ((id - 1) % 4) * 0.08, 0, 0.7),
        y: clamp(0.08 + ((id - 1) % 3) * 0.08, 0, 0.7),
        width: 0.32,
        height: 0.32,
      },
    });
    activeMaskId = id;
    renderModal();
  });
  const cancel = createButton("Cancel", "Close without applying changes", closeModal);
  const apply = createButton("Apply", "Apply mask changes to this node", () => {
    writeRegionalConfig(node, working);
    renderRegionalEditor(node);
    closeModal();
  });
  foot.append(add, cancel, apply);
  modal.append(head, body, foot);
  backdrop.appendChild(modal);
  document.body.appendChild(backdrop);

  function renderMaskList() {
    list.innerHTML = "";
    for (const mask of working.masks) {
      const row = document.createElement("div");
      row.className = `easyuse-anima-regional-mask-row${mask.mask_id === activeMaskId ? " active" : ""}`;
      row.addEventListener("click", () => {
        activeMaskId = mask.mask_id;
        renderModal();
      });
      const enabled = document.createElement("input");
      enabled.type = "checkbox";
      enabled.checked = mask.enabled !== false;
      enabled.addEventListener("click", (event) => event.stopPropagation());
      enabled.addEventListener("change", (event) => {
        event.stopPropagation();
        mask.enabled = enabled.checked;
        drawMaskCanvas(canvas, working, activeMaskId);
      });
      const name = document.createElement("input");
      name.type = "text";
      name.value = mask.name || mask.label || `Mask ${mask.mask_id}`;
      name.addEventListener("click", (event) => event.stopPropagation());
      name.addEventListener("input", () => {
        mask.name = name.value;
        mask.label = name.value || `Mask ${mask.mask_id}`;
      });
      const color = document.createElement("input");
      color.type = "color";
      color.value = mask.color || "#3b82f6";
      color.addEventListener("click", (event) => event.stopPropagation());
      color.addEventListener("input", () => {
        mask.color = color.value;
        drawMaskCanvas(canvas, working, activeMaskId);
      });
      const remove = createButton("X", "Delete this mask without renumbering other masks", (event) => {
        event.stopPropagation();
        working.masks = working.masks.filter((item) => item.mask_id !== mask.mask_id);
        activeMaskId = working.masks[0]?.mask_id || 0;
        renderModal();
      });
      row.append(enabled, name, color, remove);
      list.appendChild(row);
    }
  }

  function renderInspector() {
    inspector.innerHTML = "";
    const mask = working.masks.find((item) => item.mask_id === activeMaskId);
    if (!mask) {
      const empty = document.createElement("div");
      empty.className = "easyuse-anima-regional-mask-inspector-empty";
      empty.textContent = "Select a mask";
      inspector.appendChild(empty);
      return;
    }
    const geometry = normalizeGeometry(mask.geometry);
    const titleRow = document.createElement("div");
    titleRow.className = "easyuse-anima-regional-mask-inspector-title";
    titleRow.textContent = `Mask ${mask.mask_id}`;

    const shapeRow = document.createElement("label");
    shapeRow.className = "easyuse-anima-regional-mask-control";
    const shapeLabel = document.createElement("span");
    shapeLabel.textContent = "Shape";
    const shape = document.createElement("select");
    for (const value of ["rect", "ellipse"]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value === "rect" ? "Rectangle" : "Ellipse";
      shape.appendChild(option);
    }
    shape.value = geometry.type;
    shape.addEventListener("click", (event) => event.stopPropagation());
    shape.addEventListener("change", () => {
      mask.geometry = normalizeGeometry({
        ...normalizeGeometry(mask.geometry),
        type: shape.value,
      });
      drawMaskCanvas(canvas, working, activeMaskId);
    });
    shapeRow.append(shapeLabel, shape);
    inspector.append(titleRow, shapeRow);

    const addNumber = (label, key, min, max) => {
      const row = document.createElement("label");
      row.className = "easyuse-anima-regional-mask-control";
      const text = document.createElement("span");
      text.textContent = label;
      const input = document.createElement("input");
      input.type = "number";
      input.min = String(min);
      input.max = String(max);
      input.step = "1";
      input.value = String(Math.round((geometry[key] || 0) * 100));
      input.addEventListener("click", (event) => event.stopPropagation());
      input.addEventListener("input", () => {
        const current = normalizeGeometry(mask.geometry);
        current[key] = clamp((Number(input.value) || 0) / 100, min / 100, max / 100);
        mask.geometry = normalizeGeometry(current);
        input.value = String(Math.round((mask.geometry[key] || 0) * 100));
        drawMaskCanvas(canvas, working, activeMaskId);
      });
      row.append(text, input);
      inspector.appendChild(row);
    };

    addNumber("X %", "x", 0, 99);
    addNumber("Y %", "y", 0, 99);
    addNumber("Width %", "width", 1, 100);
    addNumber("Height %", "height", 1, 100);
  }

  function renderModal() {
    working.canvas = {
      width: resolution.width,
      height: resolution.height,
      aspect_ratio: ratioLabel(resolution.width, resolution.height),
      source: "resolution_fields",
    };
    renderMaskList();
    renderInspector();
    drawMaskCanvas(canvas, working, activeMaskId);
  }

  canvas.addEventListener("mousedown", (event) => {
    event.preventDefault();
    const point = canvasPoint(canvas, event);
    const handleHit = findMaskHandleAt(working, point, activeMaskId);
    if (handleHit) {
      drag = {
        mode: "resize",
        handle: handleHit.handle,
        mask: handleHit.mask,
        start: point,
        geometry: handleHit.geometry,
      };
      drawMaskCanvas(canvas, working, activeMaskId);
      return;
    }
    const selected = findMaskAt(working, point);
    if (selected) {
      activeMaskId = selected.mask_id;
      const geometry = normalizeGeometry(selected.geometry);
      drag = {
        mode: "move",
        mask: selected,
        start: point,
        geometry,
      };
      renderModal();
    }
  });
  window.addEventListener("mousemove", onMouseMove);
  window.addEventListener("mouseup", onMouseUp);

  function onMouseMove(event) {
    if (!drag) {
      return;
    }
    const point = canvasPoint(canvas, event);
    const dx = point.x - drag.start.x;
    const dy = point.y - drag.start.y;
    if (drag.mode === "resize") {
      drag.mask.geometry = resizeGeometry(drag.geometry, drag.handle || "se", dx, dy);
    } else {
      drag.mask.geometry = moveGeometry(drag.geometry, dx, dy);
    }
    drawMaskCanvas(canvas, working, activeMaskId);
  }

  function onMouseUp() {
    if (drag) {
      renderModal();
    }
    drag = null;
  }

  renderModal();
}

function regionalTextareas(node) {
  const editor = node?.__easyuseAnimaRegionalEditorEl;
  if (!editor) {
    return [];
  }
  return Array.from(editor.querySelectorAll("textarea[data-easyuse-anima-prompt-studio-variant-field-id]"));
}

function scheduleRegionalFieldHighlights(node, classify = true) {
  if (!node || node.__easyuseAnimaRegionalHighlightScheduled) {
    return;
  }
  node.__easyuseAnimaRegionalHighlightScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaRegionalHighlightScheduled = false;
    refreshPromptStudioHighlights(
      node,
      regionalTextareas(node),
      node.__easyuseAnimaRegionalFields || defaultFields(),
      { namespace: "regional", classify },
    );
  });
}

function createToolbarButton(label, title, onClick) {
  const button = createButton(label, title, onClick);
  button.className = "easyuse-anima-advanced-toggle";
  return button;
}

function createRegionalPane(node, pane, titleText) {
  const section = document.createElement("section");
  section.className = "easyuse-anima-advanced-pane";

  const header = document.createElement("div");
  header.className = "easyuse-anima-advanced-pane-title";
  const heading = document.createElement("span");
  heading.textContent = titleText;
  const actions = document.createElement("div");
  actions.className = "easyuse-anima-advanced-actions";
  const addButton = (type, label) => {
    actions.append(createButton(label, `Add ${label.replace(/^\+\s*/, "")}`, () => addRegionalField(node, pane, type)));
  };
  if (pane === "positive") {
    addButton("quality", "+ Quality");
    addButton("artist", "+ Artist");
    addButton("trigger", "+ Trigger");
  }
  addButton("general", "+ General");
  header.append(heading, actions);
  section.append(header);

  const fields = (node.__easyuseAnimaRegionalFields || defaultFields()).filter((item) => item.pane === pane);
  if (!fields.length) {
    const empty = document.createElement("div");
    empty.className = "easyuse-anima-empty-pane";
    empty.textContent = "No fields";
    section.append(empty);
  } else {
    for (const field of fields) {
      section.append(createFieldCard(node, field));
    }
  }
  return section;
}

function renderRegionalEditor(node) {
  ensureRegionalWidgetValues(node);
  const editor = node.__easyuseAnimaRegionalEditorEl;
  if (!editor) {
    syncRegionalFieldInputs(node, node.__easyuseAnimaRegionalFields || defaultFields());
    return;
  }
  const fields = node.__easyuseAnimaRegionalFields || defaultFields();
  const config = node.__easyuseAnimaRegionalConfig || defaultConfig(node);
  editor.innerHTML = "";

  const toolbar = document.createElement("div");
  toolbar.className = "easyuse-anima-advanced-controlbar";
  toolbar.append(
    createToolbarButton("Edit Masks", "Open numbered mask editor", () => openMaskEditor(node)),
  );
  const summary = document.createElement("div");
  summary.className = "easyuse-anima-regional-summary";
  summary.textContent = `${config.masks?.length || 0} masks`;
  toolbar.appendChild(summary);
  editor.appendChild(toolbar);
  editor.append(
    createRegionalWildcardBar(node),
    createRegionalResolutionBar(node),
  );

  const panes = document.createElement("div");
  panes.className = "easyuse-anima-advanced-panes";
  panes.append(
    createRegionalPane(node, "positive", "Positive prompts"),
    createRegionalPane(node, "negative", "Negative prompts"),
  );
  editor.appendChild(panes);
  writeRegionalFields(node, fields);
  writeRegionalConfig(node, node.__easyuseAnimaRegionalConfig || config);
  scheduleRegionalFieldHighlights(node, true);
  scheduleRegionalLayout(node, "render");
}

function regionalEditorWidth(node) {
  return Math.max(REGIONAL_NODE_MIN_WIDTH - 18, Math.round((Number(node?.size?.[0]) || REGIONAL_NODE_DEFAULT_WIDTH) - 18));
}

function measureRegionalEditorContentHeight(editor) {
  if (!editor) {
    return 0;
  }
  const childrenHeight = [...editor.children].reduce((total, child) => {
    if (!(child instanceof HTMLElement)) {
      return total;
    }
    const style = getComputedStyle(child);
    const marginTop = Number.parseFloat(style?.marginTop || "") || 0;
    const marginBottom = Number.parseFloat(style?.marginBottom || "") || 0;
    return total + marginTop + Number(child.offsetHeight || 0) + marginBottom;
  }, 0);
  return Math.ceil(Math.max(
    childrenHeight,
    Number(editor.scrollHeight) || 0,
    Number(editor.offsetHeight) || 0,
  ));
}

function regionalEditorAutoViewportCap() {
  const viewportHeight = Number(globalThis.innerHeight) || 0;
  const viewportCap = viewportHeight > 0 ? Math.floor(viewportHeight * 0.72) : REGIONAL_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT;
  return Math.ceil(Math.max(
    REGIONAL_EDITOR_MIN_VIEWPORT_HEIGHT,
    Math.min(REGIONAL_EDITOR_MAX_AUTO_VIEWPORT_HEIGHT, viewportCap),
  ));
}

function regionalEditorMinimumHeight(node) {
  const contentHeight = measureRegionalEditorContentHeight(node?.__easyuseAnimaRegionalEditorEl);
  return Math.ceil(Math.max(
    REGIONAL_EDITOR_MIN_VIEWPORT_HEIGHT,
    Math.min(Math.max(contentHeight, REGIONAL_EDITOR_MIN_VIEWPORT_HEIGHT), regionalEditorAutoViewportCap()),
  ));
}

function regionalEditorWidget(node) {
  return node?.__easyuseAnimaRegionalDomWidget
    || node?.widgets?.find?.((widget) => widget?.name === "easyuse_anima_regional_editor")
    || null;
}

function regionalNodeChromeOffset(node) {
  const widget = regionalEditorWidget(node);
  const widgetY = Math.max(
    Number(widget?.last_y) || 0,
    Number(widget?.y) || 0,
  );
  return Math.ceil(Math.max(72, widgetY + 12));
}

function regionalMinimumNodeHeight(node) {
  return Math.ceil(regionalEditorMinimumHeight(node) + regionalNodeChromeOffset(node));
}

function regionalAvailableEditorViewportHeight(node) {
  const minimumHeight = regionalEditorMinimumHeight(node);
  const nodeHeight = Number(node?.size?.[1]) || 0;
  const availableHeight = Math.max(0, nodeHeight - regionalNodeChromeOffset(node));
  return Math.ceil(Math.max(minimumHeight, availableHeight));
}

function regionalEditorWidgetHeight(node) {
  if (node?.__easyuseAnimaRegionalEditorEl?.isConnected) {
    return regionalAvailableEditorViewportHeight(node);
  }
  return Math.ceil(Math.max(
    regionalEditorMinimumHeight(node),
    Number(node?.__easyuseAnimaRegionalWidgetHeight) || 0,
  ));
}

function updateRegionalEditorWidth(node) {
  const editor = node?.__easyuseAnimaRegionalEditorEl;
  if (!editor) {
    return;
  }
  const width = Number(node?.size?.[0]) || REGIONAL_NODE_DEFAULT_WIDTH;
  const editorWidth = regionalEditorWidth(node);
  editor.style.width = `${editorWidth}px`;
  editor.style.maxWidth = `${editorWidth}px`;
  editor.classList.toggle("is-narrow", width < 620);
}

function applyRegionalLayout(node, reason = "layout") {
  const editor = node?.__easyuseAnimaRegionalEditorEl;
  if (!editor || !node.size || node.__easyuseAnimaRegionalApplyingLayout) {
    return;
  }
  node.__easyuseAnimaRegionalApplyingLayout = true;
  try {
    updateRegionalEditorWidth(node);
    const currentWidth = Number(node.size[0]) || REGIONAL_NODE_DEFAULT_WIDTH;
    const currentHeight = Number(node.size[1]) || 0;
    const minimumHeight = regionalMinimumNodeHeight(node);
    const widgetHeight = regionalEditorWidgetHeight(node);
    editor.style.height = `${widgetHeight}px`;
    editor.style.maxHeight = `${widgetHeight}px`;
    node.__easyuseAnimaRegionalWidgetHeight = widgetHeight;
    node.__easyuseAnimaRegionalLastLayoutReason = reason;
    const widget = regionalEditorWidget(node);
    if (widget) {
      widget.computedHeight = widgetHeight;
    }
    if (typeof node.setSize === "function" && currentHeight < minimumHeight - 1) {
      node.setSize([Math.max(currentWidth, REGIONAL_NODE_MIN_WIDTH), minimumHeight]);
    }
    for (const textarea of regionalTextareas(node)) {
      requestPromptStudioOverlaySync(textarea, true);
    }
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
    requestAnimationFrame(() => app.graph?.setDirtyCanvas?.(true, true));
  } finally {
    node.__easyuseAnimaRegionalApplyingLayout = false;
  }
  scheduleRegionalFieldHighlights(node, reason !== "resize");
}

function regionalLayoutReasonPriority(reason) {
  return REGIONAL_LAYOUT_REASON_PRIORITY[reason] ?? 0;
}

function scheduleRegionalLayout(node, reason = "layout") {
  if (!node?.__easyuseAnimaRegionalEditorEl) {
    return;
  }
  updateRegionalEditorWidth(node);
  const currentReason = node.__easyuseAnimaRegionalLayoutReason || "layout";
  if (
    !node.__easyuseAnimaRegionalLayoutScheduled
    || regionalLayoutReasonPriority(reason) >= regionalLayoutReasonPriority(currentReason)
  ) {
    node.__easyuseAnimaRegionalLayoutReason = reason;
  }
  if (node.__easyuseAnimaRegionalLayoutScheduled) {
    return;
  }
  node.__easyuseAnimaRegionalLayoutScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaRegionalLayoutScheduled = false;
    const layoutReason = node.__easyuseAnimaRegionalLayoutReason || reason;
    node.__easyuseAnimaRegionalLayoutReason = null;
    applyRegionalLayout(node, layoutReason);
  });
}

function hookRegionalNode(node) {
  ensureRegionalStyle();
  installRegionalSaveSync();
  ensureRegionalWidgetValues(node);
  removeRegionalInternalInputSockets(node);
  hideRegionalInternalWidgets(node);
  node.serialize_widgets = true;
  node.minWidth = Math.max(Number(node.minWidth) || 0, REGIONAL_NODE_MIN_WIDTH);
  if (Array.isArray(node.size)) {
    const currentWidth = Number(node.size[0]) || 0;
    node.size[0] = currentWidth < REGIONAL_NODE_MIN_WIDTH ? REGIONAL_NODE_DEFAULT_WIDTH : currentWidth;
  }
  if (!node.__easyuseAnimaRegionalEditorEl) {
    const editor = document.createElement("div");
    editor.className = "easyuse-anima-advanced-editor easyuse-anima-prompt-studio-variant easyuse-anima-regional-editor";
    node.__easyuseAnimaRegionalEditorEl = editor;
    const widget = node.addDOMWidget?.("easyuse_anima_regional_editor", "EasyUseAnimaRegionalEditor", editor, {
      serialize: false,
      hideOnZoom: false,
      getMinHeight: () => regionalEditorMinimumHeight(node),
      getHeight: () => regionalEditorWidgetHeight(node),
    });
    if (widget) {
      node.__easyuseAnimaRegionalDomWidget = widget;
      widget.computeLayoutSize = () => ({
        minHeight: regionalEditorMinimumHeight(node),
        height: regionalEditorWidgetHeight(node),
        minWidth: REGIONAL_NODE_MIN_WIDTH - 18,
      });
    }
  }
  renderRegionalEditor(node);
}

function scheduleHookRegionalNode(node) {
  if (!node || node.__easyuseAnimaRegionalHookScheduled) {
    return;
  }
  node.__easyuseAnimaRegionalHookScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaRegionalHookScheduled = false;
    hookRegionalNode(node);
  });
}

function isRegionalNode(node) {
  return node?.type === REGIONAL_NODE_TYPE || node?.comfyClass === REGIONAL_NODE_TYPE;
}

function syncAllRegionalNodes() {
  for (const node of app.graph?._nodes || []) {
    if (isRegionalNode(node)) {
      syncRegionalValues(node);
    }
  }
}

function installRegionalSaveSync() {
  const graphProto = globalThis.LGraph?.prototype || app.graph?.constructor?.prototype;
  if (graphProto?.serialize && !graphProto.serialize.__easyuseAnimaRegionalWrapped) {
    const serialize = graphProto.serialize;
    graphProto.serialize = function () {
      syncAllRegionalNodes();
      return serialize.apply(this, arguments);
    };
    graphProto.serialize.__easyuseAnimaRegionalWrapped = true;
  }
  if (app.queuePrompt && !app.queuePrompt.__easyuseAnimaRegionalWrapped) {
    const queuePrompt = app.queuePrompt;
    app.queuePrompt = function () {
      syncAllRegionalNodes();
      return queuePrompt.apply(this, arguments);
    };
    app.queuePrompt.__easyuseAnimaRegionalWrapped = true;
  }
}

function applyRegionalExecutedInputs(node, message) {
  const payload = firstValue(message?.prompt_studio_regional, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  node.__easyuseAnimaRegionalFieldInputValues =
    payload.field_inputs && typeof payload.field_inputs === "object" ? payload.field_inputs : {};
  if (payload.regional_fields != null) {
    const widget = regionalFieldsWidget(node);
    if (widget) {
      widget.value = normalizedFieldsString(payload.regional_fields);
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
    if (widget && payload[name] != null) {
      widget.value = payload[name];
    }
  }
  ensureRegionalWidgetValues(node);
  const fields = node.__easyuseAnimaRegionalFields || defaultFields();
  if (mergeRegionalFieldInputValues(node, fields, node.__easyuseAnimaRegionalFieldInputValues)) {
    writeRegionalFields(node, fields, { syncInputs: false });
  } else {
    syncRegionalFieldInputs(node, fields);
  }
  renderRegionalEditor(node);
}

app.registerExtension({
  name: "easyuse-anima.prompt-studio-regional",
  async setup() {
    installRegionalSaveSync();
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === REGIONAL_CONDITIONING_NODE_TYPE) {
      wrapRegionalConditioningNode(nodeType);
      return;
    }
    if (nodeData.name !== REGIONAL_NODE_TYPE) {
      return;
    }
    if (nodeType.prototype.__easyuseAnimaRegionalWrapped) {
      return;
    }
    nodeType.prototype.__easyuseAnimaRegionalWrapped = true;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      scheduleHookRegionalNode(this);
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (serialized) {
      onConfigure?.apply(this, arguments);
      captureRegionalConfigure(this, serialized);
      removeRegionalInternalInputSockets(this);
      scheduleHookRegionalNode(this);
    };

    const onResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function () {
      const result = onResize?.apply(this, arguments);
      scheduleRegionalLayout(this, "resize");
      return result;
    };

    const onConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function () {
      const result = onConnectionsChange?.apply(this, arguments);
      if (!this.__easyuseAnimaRegionalHandlingConnectionsChange) {
        this.__easyuseAnimaRegionalHandlingConnectionsChange = true;
        requestAnimationFrame(() => {
          try {
            removeRegionalInternalInputSockets(this);
            pruneDisconnectedRegionalFieldInputValues(this);
            renderRegionalEditor(this);
          } finally {
            this.__easyuseAnimaRegionalHandlingConnectionsChange = false;
          }
        });
      }
      return result;
    };

    const onSerialize = nodeType.prototype.onSerialize;
    nodeType.prototype.onSerialize = function (serialized) {
      const result = onSerialize?.apply(this, arguments);
      syncRegionalValues(this, serialized);
      return result;
    };

    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      applyRegionalExecutedInputs(this, message);
    };
  },
});
