// @ts-check

import {
  PROMPT_STUDIO_VARIANT_FIELD_LABELS,
  PROMPT_STUDIO_VARIANT_FIELD_TYPES,
  REGIONAL_CONDITIONING_AREA_MODES,
} from "./constants.js";
import { normalizeGeometry } from "./mask_geometry.js";
import { ratioLabel } from "./resolution.js";

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
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

export function toRegionalInteger(value, fallback = 0) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function firstRegionalValue(value, fallback = null) {
  return Array.isArray(value) ? (value.length ? value[0] : fallback) : (value ?? fallback);
}

export function isRegionalConditioningAreaMode(value) {
  return REGIONAL_CONDITIONING_AREA_MODES.has(String(value || ""));
}

export function normalizeRegionalConditioningWidgetValues(values) {
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

export function createDefaultRegionalFields() {
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

export function createDefaultRegionalConfig(resolution = null) {
  const width = Math.max(32, toRegionalInteger(resolution?.width, 1024));
  const height = Math.max(32, toRegionalInteger(resolution?.height, 1024));
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

export function normalizeRegionalMaskIds(value) {
  const values = Array.isArray(value) ? value : String(value ?? "").split(/[,\s;]+/);
  const result = [];
  for (const raw of values) {
    const id = toRegionalInteger(raw, 0);
    if (id > 0 && !result.includes(id)) {
      result.push(id);
    }
  }
  return result;
}

export function normalizeRegionalField(field, index = 0) {
  const pane = field?.pane === "negative" ? "negative" : "positive";
  let type = String(field?.type || "general").toLowerCase();
  if (!PROMPT_STUDIO_VARIANT_FIELD_TYPES.includes(type)) {
    type = "general";
  }
  if (pane === "negative" && type === "trigger") {
    type = "general";
  }
  const label = String(field?.label || PROMPT_STUDIO_VARIANT_FIELD_LABELS[type] || "Prompt").trim();
  const id = String(field?.id || `${pane}_${type}_${index + 1}`).trim() || `${pane}_${type}_${index + 1}`;
  return {
    id,
    pane,
    type,
    label,
    text: String(field?.text || ""),
    height: Math.max(36, toRegionalInteger(field?.height, 72)),
    enabled: asBool(field?.enabled, true),
    pin: asBool(field?.pin, type === "trigger"),
    collapsed: asBool(field?.collapsed, false),
    mask_ids: pane === "positive" ? normalizeRegionalMaskIds(field?.mask_ids) : [],
  };
}

export function normalizeRegionalFields(value) {
  const parsed = parseJson(value, []);
  const raw = Array.isArray(parsed) && parsed.length ? parsed : createDefaultRegionalFields();
  const fields = raw.map((field, index) => normalizeRegionalField(field, index));
  return fields.length ? fields : createDefaultRegionalFields();
}

export function normalizeRegionalMask(mask, index) {
  const maskId = toRegionalInteger(mask?.mask_id ?? mask?.id, index + 1);
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

export function normalizeRegionalConfig(value, resolution = null) {
  const parsed = parseJson(value, {});
  const base = createDefaultRegionalConfig(resolution);
  const rawMasks = Array.isArray(parsed.masks)
    ? parsed.masks
    : (Array.isArray(parsed.regions) ? parsed.regions : []);
  const used = new Set();
  const masks = [];
  for (const [index, raw] of rawMasks.entries()) {
    const mask = normalizeRegionalMask(raw, index);
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
    conditioning_settings: parsed.conditioning_settings && typeof parsed.conditioning_settings === "object"
      ? parsed.conditioning_settings
      : {},
    regional_settings: parsed.regional_settings && typeof parsed.regional_settings === "object"
      ? parsed.regional_settings
      : {},
    mask_authoring: {
      ...base.mask_authoring,
      ...(parsed.mask_authoring && typeof parsed.mask_authoring === "object" ? parsed.mask_authoring : {}),
    },
    next_mask_id: Math.max(1, toRegionalInteger(parsed.next_mask_id, 1), maxMaskId + 1),
    masks,
  };
}
