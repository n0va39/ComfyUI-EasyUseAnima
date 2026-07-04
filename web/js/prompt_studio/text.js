// @ts-check

import { easyuseAnimaText } from "../easyuse_anima_i18n.js";
import {
  PROMPT_STUDIO_TEXT,
  SECTION_STYLES,
} from "./constants.js";

function psText(key) {
  return easyuseAnimaText(PROMPT_STUDIO_TEXT, key);
}

function psFormat(key, values = {}) {
  return psText(key).replace(/\{(\w+)\}/g, (_match, name) => values[name] ?? "");
}

function sectionLabel(section) {
  const key = String(section || "unknown");
  const style = SECTION_STYLES[key] || SECTION_STYLES.unknown;
  return psText(`section.${key}`) || style?.label || key;
}

export {
  psFormat,
  psText,
  sectionLabel,
};
