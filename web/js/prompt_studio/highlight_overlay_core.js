// @ts-check

/**
 * @typedef {Object} HighlightAutocompletePreview
 * @property {unknown} [sourceValue]
 * @property {unknown} [value]
 * @property {unknown} [color]
 * @property {number} [candidateStart]
 * @property {number} [candidateEnd]
 * @property {number} [ghostStart]
 * @property {number} [ghostEnd]
 */

/**
 * @typedef {(HTMLTextAreaElement | HTMLInputElement) & {
 *   __easyuseAnimaAutocompletePreview?: HighlightAutocompletePreview | null
 * }} HighlightOverlayInput
 */

/**
 * @callback HighlightTextRenderer
 * @param {string} text
 * @param {Array<any>} tokens
 * @returns {string}
 */

const HIGHLIGHT_TEXT_METRIC_PROPERTIES = [
  "font",
  "fontFamily",
  "fontSize",
  "fontSizeAdjust",
  "fontStretch",
  "fontWeight",
  "fontStyle",
  "fontVariant",
  "fontKerning",
  "fontOpticalSizing",
  "fontFeatureSettings",
  "fontVariationSettings",
  "lineHeight",
  "letterSpacing",
  "wordSpacing",
  "textIndent",
  "padding",
  "border",
  "borderRadius",
  "boxSizing",
  "textAlign",
  "textTransform",
  "textRendering",
  "direction",
  "tabSize",
  "whiteSpace",
  "overflowWrap",
  "wordBreak",
];

/** @param {string} value */
function cssPixelNumber(value) {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

/** @param {number} value */
function cssPixel(value) {
  const rounded = Math.round(Number(value || 0) * 100) / 100;
  return `${rounded}px`;
}

/**
 * @param {HTMLTextAreaElement | HTMLInputElement} input
 * @param {CSSStyleDeclaration} style
 */
function hasVisibleVerticalScrollbar(input, style) {
  const overflowY = String(style.overflowY || "").trim().toLowerCase();
  if (overflowY === "scroll") {
    return true;
  }
  if (overflowY !== "auto" && overflowY !== "overlay") {
    return false;
  }
  return (Number(input.scrollHeight) || 0) > (Number(input.clientHeight) || 0);
}

/**
 * @param {HTMLTextAreaElement | HTMLInputElement} input
 * @param {CSSStyleDeclaration} [style]
 */
function overlayScrollbarPadding(input, style = getComputedStyle(input)) {
  const verticalGutter = hasVisibleVerticalScrollbar(input, style)
    ? Math.max(
      0,
      (Number(input.offsetWidth) || 0)
        - (Number(input.clientWidth) || 0)
        - cssPixelNumber(style.borderLeftWidth)
        - cssPixelNumber(style.borderRightWidth),
    )
    : 0;
  const horizontalGutter = Math.max(
    0,
    (Number(input.offsetHeight) || 0)
      - (Number(input.clientHeight) || 0)
      - cssPixelNumber(style.borderTopWidth)
      - cssPixelNumber(style.borderBottomWidth),
  );
  return {
    right: cssPixel(cssPixelNumber(style.paddingRight) + verticalGutter),
    bottom: cssPixel(cssPixelNumber(style.paddingBottom) + horizontalGutter),
  };
}

/**
 * @param {HTMLTextAreaElement | HTMLInputElement} input
 * @param {HTMLElement} overlay
 * @param {CSSStyleDeclaration} [style]
 */
function applyOverlayScrollbarPadding(input, overlay, style = getComputedStyle(input)) {
  const padding = overlayScrollbarPadding(input, style);
  if (overlay.style.paddingRight !== padding.right) overlay.style.paddingRight = padding.right;
  if (overlay.style.paddingBottom !== padding.bottom) overlay.style.paddingBottom = padding.bottom;
}

/** @param {HTMLTextAreaElement | HTMLInputElement} input */
function overlayBounds(input) {
  return {
    left: `${input.offsetLeft}px`,
    top: `${input.offsetTop}px`,
    width: `${input.offsetWidth}px`,
    height: `${input.offsetHeight}px`,
  };
}

/**
 * @param {string} text
 * @param {HighlightAutocompletePreview} preview
 * @param {(value: unknown) => string} escapeHtml
 * @param {number} [opacity]
 */
function autocompletePreviewSpanHtml(text, preview, escapeHtml, opacity = 0.95) {
  const color = String(preview?.color || "rgba(203, 213, 225, 0.86)");
  return `<span style="font: inherit; line-height: inherit; letter-spacing: inherit; vertical-align: baseline; color: ${escapeHtml(color)}; opacity: ${opacity}">`
    + escapeHtml(text)
    + "</span>";
}

/**
 * @param {string} value
 * @param {Array<any>} tokens
 * @param {HighlightAutocompletePreview | null | undefined} preview
 * @param {HighlightTextRenderer} renderHighlightedText
 * @param {(value: unknown) => string} escapeHtml
 */
function highlightOverlayPreviewHtml(value, tokens, preview, renderHighlightedText, escapeHtml) {
  if (!preview || String(preview.sourceValue || "") !== String(value || "")) {
    return null;
  }
  const text = String(preview.value || "");
  const candidateStart = Math.max(0, Math.min(Number(preview.candidateStart ?? preview.ghostStart) || 0, text.length));
  const candidateEnd = Math.max(candidateStart, Math.min(Number(preview.candidateEnd ?? preview.ghostEnd) || 0, text.length));
  const ghostStart = Math.max(0, Math.min(Number(preview.ghostStart) || 0, text.length));
  const ghostEnd = Math.max(ghostStart, Math.min(Number(preview.ghostEnd) || 0, text.length));
  if (!text || candidateEnd <= candidateStart || ghostEnd <= ghostStart) {
    return null;
  }
  const safeGhostStart = Math.max(candidateStart, Math.min(ghostStart, candidateEnd));
  const safeGhostEnd = Math.max(safeGhostStart, Math.min(ghostEnd, candidateEnd));
  const html = [
    renderHighlightedText(text.slice(0, candidateStart), tokens || []),
    autocompletePreviewSpanHtml(text.slice(candidateStart, safeGhostStart), preview, escapeHtml, 0.95),
    autocompletePreviewSpanHtml(text.slice(safeGhostStart, safeGhostEnd), preview, escapeHtml, 0.52),
    autocompletePreviewSpanHtml(text.slice(safeGhostEnd, candidateEnd), preview, escapeHtml, 0.95),
    renderHighlightedText(text.slice(candidateEnd), tokens || []),
  ].join("");
  return text.endsWith("\n") ? `${html} ` : html;
}

/**
 * @param {Object} dependencies
 * @param {HighlightTextRenderer} dependencies.renderHighlightedText
 * @param {(value: unknown) => string} dependencies.escapeHtml
 */
function createHighlightOverlayRenderer({ renderHighlightedText, escapeHtml }) {
  /**
   * @param {unknown} value
   * @param {Array<any>} tokens
   * @param {unknown} [placeholder]
   * @param {HighlightOverlayInput | null} [input]
   */
  return function highlightOverlayHtml(value, tokens, placeholder = "", input = null) {
    const text = String(value || "");
    if (!text) {
      return `<span style="opacity: 0.45">${escapeHtml(placeholder)}</span>`;
    }
    const previewHtml = highlightOverlayPreviewHtml(
      text,
      tokens,
      input?.__easyuseAnimaAutocompletePreview,
      renderHighlightedText,
      escapeHtml,
    );
    if (previewHtml != null) {
      return previewHtml;
    }
    const html = renderHighlightedText(text, tokens);
    return text.endsWith("\n") ? `${html} ` : html;
  };
}

/**
 * @param {HTMLTextAreaElement | HTMLInputElement} input
 * @param {HTMLElement} overlay
 * @param {CSSStyleDeclaration} [style]
 */
function copyInputTextMetrics(input, overlay, style = getComputedStyle(input)) {
  for (const property of HIGHLIGHT_TEXT_METRIC_PROPERTIES) {
    const val = style[property];
    if (overlay.style[property] !== val) {
      overlay.style[property] = val;
    }
  }
  overlay.style.boxSizing = "border-box";
  overlay.style.whiteSpace = "pre-wrap";
  overlay.style.overflowWrap = "break-word";
  overlay.style.wordWrap = "break-word";
  overlay.style.wordBreak = "normal";
  overlay.style.margin = "0";
  applyOverlayScrollbarPadding(input, overlay, style);
}

/**
 * @param {HTMLTextAreaElement | HTMLInputElement} input
 * @param {HTMLElement | null | undefined} overlay
 * @param {CSSStyleDeclaration} [style]
 */
function syncOverlayBounds(input, overlay, style) {
  if (!overlay) return;
  const currentStyle = style || getComputedStyle(input);
  const { left, top, width, height } = overlayBounds(input);

  if (overlay.style.left !== left) overlay.style.left = left;
  if (overlay.style.top !== top) overlay.style.top = top;
  if (overlay.style.width !== width) overlay.style.width = width;
  if (overlay.style.height !== height) overlay.style.height = height;
  applyOverlayScrollbarPadding(input, overlay, currentStyle);

  if (overlay.scrollTop !== input.scrollTop) overlay.scrollTop = input.scrollTop;
  if (overlay.scrollLeft !== input.scrollLeft) overlay.scrollLeft = input.scrollLeft;
}

export {
  HIGHLIGHT_TEXT_METRIC_PROPERTIES,
  copyInputTextMetrics,
  createHighlightOverlayRenderer,
  overlayBounds,
  overlayScrollbarPadding,
  syncOverlayBounds,
};
