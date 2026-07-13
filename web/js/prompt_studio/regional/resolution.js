// @ts-check

import {
  PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET,
  PROMPT_STUDIO_DEFAULT_RESOLUTION_BUCKET,
  PROMPT_STUDIO_DEFAULT_RESOLUTION_SIZE,
  PROMPT_STUDIO_RESOLUTION_BUCKETS,
} from "./constants.js";

function toInteger(value, fallback = 0) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function ratioLabel(width, height) {
  const gcd = (a, b) => (b ? gcd(b, a % b) : a);
  const divisor = gcd(Math.max(1, width), Math.max(1, height));
  return `${Math.floor(width / divisor)}:${Math.floor(height / divisor)}`;
}

export function resolutionLabel(width, height) {
  return `${width} * ${height} (${ratioLabel(width, height)})`;
}

export function resolutionOptions(bucket) {
  const values = PROMPT_STUDIO_RESOLUTION_BUCKETS[bucket]
    || PROMPT_STUDIO_RESOLUTION_BUCKETS[PROMPT_STUDIO_DEFAULT_RESOLUTION_BUCKET];
  return [...values]
    .sort((a, b) => (a[0] / a[1]) - (b[0] / b[1]) || a[0] - b[0] || a[1] - b[1])
    .map(([width, height]) => resolutionLabel(width, height));
}

export function normalizeResolutionBucket(value) {
  const bucket = String(value || "").trim();
  if (bucket === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET) {
    return bucket;
  }
  return Object.prototype.hasOwnProperty.call(PROMPT_STUDIO_RESOLUTION_BUCKETS, bucket)
    ? bucket
    : PROMPT_STUDIO_DEFAULT_RESOLUTION_BUCKET;
}

export function resolutionRatioFromLabel(value) {
  const match = String(value || "").match(/(\d+)\s*(?:\*|x|×)\s*(\d+)/i);
  if (!match) {
    return "";
  }
  return ratioLabel(Number(match[1]), Number(match[2]));
}

export function normalizeResolutionSize(bucket, value) {
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

export function snapResolution32(value, fallback = 1024) {
  const raw = Number.parseInt(value, 10);
  const base = Number.isFinite(raw) && raw > 0 ? raw : fallback;
  return Math.max(32, Math.round(base / 32) * 32);
}

export function readRegionalResolutionValues({
  bucket,
  size,
  customWidth,
  customHeight,
} = {}) {
  const width = Math.max(32, toInteger(customWidth, 1024));
  const height = Math.max(32, toInteger(customHeight, 1024));
  const match = String(size || "").match(/(\d+)\s*(?:\*|x|×)\s*(\d+)/i);
  if (normalizeResolutionBucket(bucket) !== PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET && match) {
    return {
      width: Math.max(32, toInteger(match[1], width)),
      height: Math.max(32, toInteger(match[2], height)),
    };
  }
  return { width, height };
}
