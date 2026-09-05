// @ts-check

import { easyuseAnimaGetSettings } from "../easyuse_anima_api.js";
import {
  PROMPT_STUDIO_FONT_FAMILY,
  PROMPT_STUDIO_FONT_SIZE_DEFAULT,
  SECTION_STYLES,
} from "./constants.js";
import {
  hexToRgba,
  isHexColor,
  normalizePromptStudioFontFamily,
  normalizePromptStudioFontSize,
  parseColorSettings,
} from "./utils.js";

const PROMPT_STUDIO_SETTINGS = {
  renderRevision: 0,
  typoIndicator: true,
  weightSyntaxUnderline: false,
  // Keep the legacy setting key, but use it only for paint-only emphasis.
  // Per-token font changes can wrap differently from the native textarea.
  commentEmphasis: true,
  fontOverride: false,
  fontFamily: "",
  fontSize: PROMPT_STUDIO_FONT_SIZE_DEFAULT,
  trainedTagTooltip: true,
  naiaGeneralAboveAutoToggle: false,
};

function applyPromptStudioTextStyle(input) {
  if (!(input instanceof HTMLElement)) {
    return;
  }
  const nextFamily = (PROMPT_STUDIO_SETTINGS.fontOverride && PROMPT_STUDIO_SETTINGS.fontFamily)
    ? PROMPT_STUDIO_SETTINGS.fontFamily
    : PROMPT_STUDIO_FONT_FAMILY;
  if (input.style.fontFamily !== nextFamily) {
    input.style.fontFamily = nextFamily;
  }
  if (!PROMPT_STUDIO_SETTINGS.fontOverride) {
    if (input.dataset.easyuseAnimaPromptTextOverride === "true") {
      input.style.fontSize = "";
      delete input.dataset.easyuseAnimaPromptTextOverride;
    }
    return;
  }
  const nextSize = `${PROMPT_STUDIO_SETTINGS.fontSize}px`;
  if (input.style.fontSize !== nextSize) {
    input.style.fontSize = nextSize;
  }
  input.dataset.easyuseAnimaPromptTextOverride = "true";
}

function applyPromptStudioSettings(settings, { hideTrainedTagTooltip = null } = {}) {
  PROMPT_STUDIO_SETTINGS.renderRevision += 1;
  PROMPT_STUDIO_SETTINGS.typoIndicator = settings?.["prompt_studio.typo_indicator"] !== "false";
  PROMPT_STUDIO_SETTINGS.weightSyntaxUnderline = settings?.["prompt_studio.weight_syntax_underline"] === "true";
  PROMPT_STUDIO_SETTINGS.commentEmphasis = settings?.["prompt_studio.comment_italic"] !== "false";
  PROMPT_STUDIO_SETTINGS.trainedTagTooltip = settings?.["prompt_studio.trained_tag_tooltip"] !== "false";
  if (!PROMPT_STUDIO_SETTINGS.trainedTagTooltip) {
    hideTrainedTagTooltip?.();
  }
  PROMPT_STUDIO_SETTINGS.fontOverride = settings?.["prompt_studio.font_override"] === "true";
  PROMPT_STUDIO_SETTINGS.fontFamily = normalizePromptStudioFontFamily(settings?.["prompt_studio.font_family"]);
  PROMPT_STUDIO_SETTINGS.fontSize = normalizePromptStudioFontSize(settings?.["prompt_studio.font_size"]);
  if (PROMPT_STUDIO_SETTINGS.fontOverride) {
    document.documentElement?.style?.setProperty(
      "--easyuse-anima-prompt-studio-font-size",
      `${PROMPT_STUDIO_SETTINGS.fontSize}px`,
    );
    document.documentElement?.style?.setProperty(
      "--easyuse-anima-prompt-studio-font-family",
      PROMPT_STUDIO_SETTINGS.fontFamily || PROMPT_STUDIO_FONT_FAMILY,
    );
  } else {
    document.documentElement?.style?.removeProperty("--easyuse-anima-prompt-studio-font-size");
    document.documentElement?.style?.removeProperty("--easyuse-anima-prompt-studio-font-family");
  }
  PROMPT_STUDIO_SETTINGS.naiaGeneralAboveAutoToggle =
    settings?.["prompt_studio.naia_general_above_auto_toggle"] === "true";
  const colors = parseColorSettings(settings?.["prompt_studio.colors"]);
  for (const [key, color] of Object.entries(colors)) {
    if (!SECTION_STYLES[key] || !isHexColor(color)) {
      continue;
    }
    SECTION_STYLES[key].color = color;
    if (SECTION_STYLES[key].background && SECTION_STYLES[key].background !== "transparent") {
      SECTION_STYLES[key].background = hexToRgba(color, 0.18);
    }
  }
}

async function loadPromptStudioSettings({ afterApply = null, hideTrainedTagTooltip = null } = {}) {
  try {
    const settings = await easyuseAnimaGetSettings({ fallback: null });
    if (!settings) {
      return;
    }
    applyPromptStudioSettings(settings, { hideTrainedTagTooltip });
    afterApply?.();
  } catch {
    // Keep built-in defaults if the settings endpoint is not available yet.
  }
}

export {
  PROMPT_STUDIO_SETTINGS,
  applyPromptStudioSettings,
  applyPromptStudioTextStyle,
  loadPromptStudioSettings,
};
