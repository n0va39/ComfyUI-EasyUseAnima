// @ts-check

import { easyuseAnimaClassifyPrompt } from "../easyuse_anima_api.js";
import {
  SECTION_STYLES,
  AUTOCOMPLETE_TOOLTIP_SECTIONS,
} from "./constants.js";
import {
  escapeHtml,
  escapeAttr,
} from "./utils.js";
import { PROMPT_STUDIO_SETTINGS } from "./settings.js";
import { ensureHighlightStyle } from "./style.js";
import { psText, sectionLabel } from "./text.js";
import { installTrainedTagTooltipListeners } from "./tooltip.js";
import {
  createPromptHighlightRenderer,
  hasHighlightSyntax,
} from "./highlight_core.js";
import {
  HIGHLIGHT_TEXT_METRIC_PROPERTIES,
  copyInputTextMetrics,
  createHighlightOverlayRenderer,
  overlayBounds,
  overlayScrollbarPadding,
  syncOverlayBounds,
} from "./highlight_overlay_core.js";

/** @typedef {import("./types.js").PromptStudioWindow} PromptStudioWindow */

/** @returns {PromptStudioWindow} */
function promptStudioWindow() {
  return /** @type {PromptStudioWindow} */ (window);
}

async function classifyPrompt(text) {
  return easyuseAnimaClassifyPrompt(text);
}

function tokenStyle(token) {
  const style = SECTION_STYLES[token?.section] || SECTION_STYLES.unknown;
  const opacity = token?.learned || token?.section === "count" ? 1 : 0.88;
  const rules = [
    `color: ${style.color}`,
    `opacity: ${opacity}`,
  ];
  if (style.background && style.background !== "transparent") {
    rules.push(`background: ${style.background}`, "border-radius: 3px");
  }
  if (style.italic && PROMPT_STUDIO_SETTINGS.commentItalic) {
    rules.push("font-style: italic");
  }
  if (style.underline && PROMPT_STUDIO_SETTINGS.typoIndicator && !token?.weighted) {
    rules.push(
      "text-decoration-line: underline",
      "text-decoration-style: wavy",
      "text-decoration-color: #ef4444",
      "text-underline-offset: 2px",
    );
  }
  return rules.join("; ");
}

function tokenTitle(token) {
  const style = SECTION_STYLES[token?.section] || SECTION_STYLES.unknown;
  const label = token?.label || sectionLabel(token?.section) || style.label || token?.section || psText("tag.generic");
  const learned = token?.learned ? ` / ${psText("tag.learned")}` : "";
  return `${label}${learned}`;
}

function trainedTagTooltipEntry(text, token) {
  if (!PROMPT_STUDIO_SETTINGS.trainedTagTooltip) {
    return null;
  }
  const section = String(token?.section || "");
  if (!AUTOCOMPLETE_TOOLTIP_SECTIONS.has(section) || !token?.learned) {
    return null;
  }
  const tag = String(token?.base || text || token?.token || "").trim();
  if (!tag) {
    return null;
  }
  return {
    tag,
    category: section,
    count: Number(token?.count || 0),
    description: String(token?.description || ""),
  };
}

function trainedTagTooltipData(text, token) {
  const entry = trainedTagTooltipEntry(text, token);
  if (!entry) {
    return null;
  }
  const hostWindow = promptStudioWindow();
  const tooltip = typeof hostWindow.easyuseAnimaAutocompleteEntryTooltip === "function"
    ? hostWindow.easyuseAnimaAutocompleteEntryTooltip(entry)
    : {
      tag: entry.tag,
      meta: `${sectionLabel(entry.category)} · ${Number(entry.count || 0).toLocaleString()}`,
      description: entry.description,
    };
  return {
    tag: String(tooltip?.tag || entry.tag),
    meta: String(tooltip?.meta || ""),
    description: String(tooltip?.description || ""),
  };
}

function trainedTagTooltipAttrs(text, token) {
  const tooltip = trainedTagTooltipData(text, token);
  if (!tooltip) {
    return "";
  }
  const title = [tooltip.tag, tooltip.meta, tooltip.description].filter(Boolean).join("\n");
  return [
    'data-easyuse-anima-trained-tag-tooltip="true"',
    `data-easyuse-anima-tooltip-tag="${escapeAttr(tooltip.tag)}"`,
    `data-easyuse-anima-tooltip-meta="${escapeAttr(tooltip.meta)}"`,
    `data-easyuse-anima-tooltip-description="${escapeAttr(tooltip.description)}"`,
    `aria-label="${escapeAttr(title)}"`,
  ].join(" ");
}

function tokenSpanHtml(text, token) {
  const tooltip = trainedTagTooltipData(text, token);
  const title = tooltip
    ? [tooltip.tag, tooltip.meta, tooltip.description].filter(Boolean).join("\n")
    : tokenTitle(token);
  const attrs = trainedTagTooltipAttrs(text, token);
  return `<span style="${tokenStyle(token)}" title="${escapeAttr(title)}"${attrs ? ` ${attrs}` : ""}>`
    + escapeHtml(text)
    + "</span>";
}

const renderHighlightedText = createPromptHighlightRenderer({
  escapeHtml,
  sectionLabel,
  tokenStyle,
  tokenSpanHtml,
  weightSyntaxUnderlineEnabled: () => PROMPT_STUDIO_SETTINGS.weightSyntaxUnderline,
  preferSyntaxBeforeToken: false,
});

const highlightOverlayHtml = createHighlightOverlayRenderer({
  escapeHtml,
  renderHighlightedText,
});

function requestOverlaySync(input, forceCopyMetrics = false) {
  const overlay = input?.__easyuseAnimaHighlightOverlay;
  if (!overlay) {
    return;
  }
  input.__easyuseAnimaHighlightForceCopyMetrics ||= forceCopyMetrics;
  if (input.__easyuseAnimaHighlightSyncRaf) {
    return;
  }
  input.__easyuseAnimaHighlightSyncRaf = requestAnimationFrame(() => {
    input.__easyuseAnimaHighlightSyncRaf = 0;
    const currentOverlay = input.__easyuseAnimaHighlightOverlay;
    if (!input.isConnected || !currentOverlay?.isConnected) {
      input.__easyuseAnimaHighlightForceCopyMetrics = false;
      return;
    }
    if (input.__easyuseAnimaHighlightForceCopyMetrics) {
      copyInputTextMetrics(input, currentOverlay);
    }
    input.__easyuseAnimaHighlightForceCopyMetrics = false;
    syncOverlayBounds(input, currentOverlay);
    requestAnimationFrame(() => {
      if (input.isConnected && currentOverlay.isConnected) {
        syncOverlayBounds(input, currentOverlay);
      }
    });
  });
}

function installOverlaySyncListeners(input) {
  if (input.__easyuseAnimaHighlightSyncInstalled) {
    return;
  }
  const schedule = () => requestOverlaySync(input);
  const scheduleMetrics = () => requestOverlaySync(input, true);
  input.addEventListener("scroll", schedule, { passive: true });
  input.addEventListener("input", schedule);
  input.addEventListener("keyup", schedule);
  input.addEventListener("click", schedule);
  input.addEventListener("compositionupdate", schedule);
  input.addEventListener("compositionend", scheduleMetrics);
  input.__easyuseAnimaHighlightSyncInstalled = true;
}

function ensureHighlightOverlay(input) {
  input.spellcheck = false;
  input.autocomplete = "off";
  input.setAttribute("autocorrect", "off");
  input.setAttribute("autocapitalize", "off");

  if (input.__easyuseAnimaHighlightOverlay) {
    const overlay = input.__easyuseAnimaHighlightOverlay;
    if (overlay.isConnected && overlay.parentElement === input.parentElement) {
      return overlay;
    }
    overlay.remove?.();
    input.__easyuseAnimaHighlightOverlay = null;
  }

  const parent = input.parentElement;
  if (!parent) {
    return null;
  }
  if (getComputedStyle(parent).position === "static") {
    parent.style.position = "relative";
  }

  const overlay = document.createElement("pre");
  overlay.className = "easyuse-anima-highlight-overlay";
  overlay.setAttribute("aria-hidden", "true");
  overlay.style.cssText = [
    "position: absolute",
    "box-sizing: border-box",
    "margin: 0",
    "overflow: hidden",
    "white-space: pre-wrap",
    "overflow-wrap: break-word",
    "word-break: normal",
    "pointer-events: none",
    "z-index: 0",
    "background: rgba(15, 23, 42, 0.62)",
    "color: var(--input-text, #ddd)",
  ].join("; ");
  copyInputTextMetrics(input, overlay);
  parent.insertBefore(overlay, input);

  ensureHighlightStyle();
  input.classList.add("easyuse-anima-highlight-input");
  input.style.position = input.style.position || "relative";
  input.style.zIndex = "1";
  input.style.background = "transparent";
  input.style.color = "transparent";
  input.style.caretColor = "var(--input-text, #ddd)";
  input.style.webkitTextFillColor = "transparent";
  input.style.whiteSpace = "pre-wrap";
  input.style.overflowWrap = "break-word";
  input.style.wordBreak = "normal";
  input.style.textSizeAdjust = "100%";
  input.style.webkitTextSizeAdjust = "100%";

  input.__easyuseAnimaHighlightOverlay = overlay;
  installOverlaySyncListeners(input);
  installTrainedTagTooltipListeners(input);
  return overlay;
}

let promptHighlightRefreshRaf = 0;

function refreshConnectedHighlightOverlays(applyTextStyle) {
  const inputs = Array.from(document.querySelectorAll(".easyuse-anima-highlight-input"));
  const updates = [];

  // DOM Style Read
  for (const input of inputs) {
    if (!(input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement)) {
      continue;
    }
    applyTextStyle?.(input);
    const overlay = ensureHighlightOverlay(input);
    if (!overlay) {
      continue;
    }

    // Font metrics reads
    const style = getComputedStyle(input);
    const metricValues = {};
    for (const prop of HIGHLIGHT_TEXT_METRIC_PROPERTIES) {
      metricValues[prop] = style[prop];
    }

    // Bounds reads
    const { left, top, width, height } = overlayBounds(input);
    const padding = overlayScrollbarPadding(input, style);
    const scrollTop = input.scrollTop;
    const scrollLeft = input.scrollLeft;

    updates.push({
      overlay,
      metricValues,
      left,
      top,
      width,
      height,
      padding,
      scrollTop,
      scrollLeft
    });
  }

  // DOM Style Write
  for (const update of updates) {
    const { overlay, metricValues, left, top, width, height, padding, scrollTop, scrollLeft } = update;

    // Apply metrics (only if they changed)
    for (const prop in metricValues) {
      const val = metricValues[prop];
      if (overlay.style[prop] !== val) {
        overlay.style[prop] = val;
      }
    }

    // Apply bounds styles (only if they changed)
    if (overlay.style.left !== left) overlay.style.left = left;
    if (overlay.style.top !== top) overlay.style.top = top;
    if (overlay.style.width !== width) overlay.style.width = width;
    if (overlay.style.height !== height) overlay.style.height = height;
    overlay.style.boxSizing = "border-box";
    overlay.style.whiteSpace = "pre-wrap";
    overlay.style.overflowWrap = "break-word";
    overlay.style.wordWrap = "break-word";
    overlay.style.wordBreak = "normal";
    if (overlay.style.paddingRight !== padding.right) overlay.style.paddingRight = padding.right;
    if (overlay.style.paddingBottom !== padding.bottom) overlay.style.paddingBottom = padding.bottom;
    if (overlay.scrollTop !== scrollTop) overlay.scrollTop = scrollTop;
    if (overlay.scrollLeft !== scrollLeft) overlay.scrollLeft = scrollLeft;
  }
}

function requestConnectedHighlightOverlayRefresh(applyTextStyle) {
  if (promptHighlightRefreshRaf) {
    return;
  }
  promptHighlightRefreshRaf = requestAnimationFrame(() => {
    promptHighlightRefreshRaf = 0;
    refreshConnectedHighlightOverlays(applyTextStyle);
    setTimeout(() => refreshConnectedHighlightOverlays(applyTextStyle), 80);
  });
}

function installPromptHighlightOverlayRefresh(app, applyTextStyle) {
  const hostWindow = promptStudioWindow();
  if (hostWindow.__easyuseAnimaHighlightOverlayRefreshInstalled) {
    return;
  }
  hostWindow.__easyuseAnimaHighlightOverlayRefreshInstalled = true;
  const schedule = () => requestConnectedHighlightOverlayRefresh(applyTextStyle);
  window.addEventListener("focus", schedule);
  window.addEventListener("resize", schedule);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      schedule();
    }
  });
  const installCanvasListeners = () => {
    const canvas = app?.canvas?.canvas;
    if (!canvas || canvas.__easyuseAnimaHighlightRefreshInstalled) {
      return;
    }
    canvas.__easyuseAnimaHighlightRefreshInstalled = true;
    canvas.addEventListener("pointerup", schedule, { passive: true });
    canvas.addEventListener("wheel", schedule, { passive: true });
  };
  installCanvasListeners();
  setTimeout(installCanvasListeners, 250);
}

function refreshAllPromptHighlights(app, hooks, forceCopyMetrics = false) {
  const {
    findWidget,
    isAdvancedNode,
    scheduleAdvancedHighlights,
    studioFieldNames,
    updateHighlight,
  } = hooks || {};
  for (const node of app?.graph?._nodes || []) {
    if (isAdvancedNode?.(node)) {
      scheduleAdvancedHighlights?.(node, { forceCopyMetrics });
      continue;
    }
    for (const name of studioFieldNames?.(node) || []) {
      const widget = findWidget?.(node, name);
      if (widget) {
        updateHighlight?.(node, widget, widget.__easyuseAnimaTokens || [], forceCopyMetrics);
      }
    }
  }
}

export {
  classifyPrompt,
  copyInputTextMetrics,
  ensureHighlightOverlay,
  hasHighlightSyntax,
  highlightOverlayHtml,
  installPromptHighlightOverlayRefresh,
  overlayBounds,
  overlayScrollbarPadding,
  refreshAllPromptHighlights,
  refreshConnectedHighlightOverlays,
  renderHighlightedText,
  requestConnectedHighlightOverlayRefresh,
  requestOverlaySync,
  syncOverlayBounds,
};
