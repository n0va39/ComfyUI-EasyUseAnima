// @ts-check

import {
  PROMPT_STUDIO_FONT_SIZE_DEFAULT,
  PROMPT_STUDIO_FONT_SIZE_MAX,
  PROMPT_STUDIO_FONT_SIZE_MIN,
} from "./constants.js";

function debounce(fn, delay = 180) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function isHexColor(value) {
  return /^#[0-9a-f]{6}$/i.test(String(value || ""));
}

function hexToRgba(value, alpha) {
  if (!isHexColor(value)) {
    return "transparent";
  }
  const red = Number.parseInt(value.slice(1, 3), 16);
  const green = Number.parseInt(value.slice(3, 5), 16);
  const blue = Number.parseInt(value.slice(5, 7), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function parseColorSettings(value) {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function normalizePromptStudioFontSize(value) {
  const parsed = Number.parseFloat(String(value ?? "").trim());
  if (!Number.isFinite(parsed)) {
    return PROMPT_STUDIO_FONT_SIZE_DEFAULT;
  }
  return Math.max(
    PROMPT_STUDIO_FONT_SIZE_MIN,
    Math.min(PROMPT_STUDIO_FONT_SIZE_MAX, Math.round(parsed)),
  );
}

function normalizePromptStudioFontFamily(value) {
  return String(value ?? "")
    .replace(/[;{}\r\n]/g, "")
    .trim()
    .slice(0, 160);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll('"', "&quot;");
}

function gcdInt(a, b) {
  let x = Math.abs(Math.trunc(a || 0));
  let y = Math.abs(Math.trunc(b || 0));
  while (y) {
    const next = x % y;
    x = y;
    y = next;
  }
  return x || 1;
}

function resolutionRatioLabel(width, height) {
  const divisor = gcdInt(width, height);
  return `${Math.trunc(width / divisor)}:${Math.trunc(height / divisor)}`;
}

function advancedResolutionLabel(width, height) {
  return `${width} * ${height} (${resolutionRatioLabel(width, height)})`;
}

function snapResolution32(value, fallback = 1024) {
  const raw = Number.parseInt(value, 10);
  const base = Number.isFinite(raw) && raw > 0 ? raw : fallback;
  return Math.max(32, Math.round(base / 32) * 32);
}

function clampAdvancedNumber(value, fallback, min, max) {
  const parsed = Number(value);
  const next = Number.isFinite(parsed) ? parsed : fallback;
  return Math.max(min, Math.min(max, next));
}

export {
  debounce,
  isHexColor,
  hexToRgba,
  parseColorSettings,
  normalizePromptStudioFontSize,
  normalizePromptStudioFontFamily,
  escapeHtml,
  escapeAttr,
  gcdInt,
  resolutionRatioLabel,
  advancedResolutionLabel,
  snapResolution32,
  clampAdvancedNumber,
};
