// @ts-check

/**
 * @typedef {object} AutocompleteRect
 * @property {number} left
 * @property {number} right
 * @property {number} top
 * @property {number} bottom
 * @property {number} width
 * @property {number} height
 */

/**
 * @param {number} value
 * @param {number} min
 * @param {number} max
 */
function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

/**
 * Calculate the unscaled mirror size and the transform needed to match the
 * rendered input rectangle.
 *
 * @param {AutocompleteRect} inputRect
 * @param {number} offsetWidth
 * @param {number} offsetHeight
 */
export function calculateCaretMirrorGeometry(inputRect, offsetWidth, offsetHeight) {
  const layoutWidth = offsetWidth || inputRect.width || 1;
  const layoutHeight = offsetHeight || inputRect.height || 1;
  const scaleX = inputRect.width > 0 ? inputRect.width / layoutWidth : 1;
  const scaleY = inputRect.height > 0 ? inputRect.height / layoutHeight : scaleX;
  return {
    layoutWidth,
    layoutHeight,
    scaleX,
    scaleY,
  };
}

/**
 * Normalize the temporary mirror marker into the caret rectangle consumed by
 * popup placement. A failed marker measurement falls back to the input.
 *
 * @param {AutocompleteRect} markerRect
 * @param {AutocompleteRect} inputRect
 * @param {number} fallbackLineHeight
 * @returns {AutocompleteRect}
 */
export function normalizeCaretClientRect(markerRect, inputRect, fallbackLineHeight) {
  if (!Number.isFinite(markerRect.left) || !Number.isFinite(markerRect.top)) {
    return inputRect;
  }
  return {
    left: markerRect.left,
    right: markerRect.right,
    top: markerRect.top,
    bottom: markerRect.bottom,
    width: markerRect.width,
    height: markerRect.height || fallbackLineHeight || 18,
  };
}

/**
 * Calculate fixed-position popup geometry from measured input/caret rectangles.
 *
 * @param {AutocompleteRect} inputRect
 * @param {AutocompleteRect} caretRect
 * @param {{ width: number, height: number }} viewport
 * @param {number} fallbackLineHeight
 */
export function calculateAutocompletePopupGeometry(
  inputRect,
  caretRect,
  viewport,
  fallbackLineHeight,
) {
  const width = Math.max(260, Math.min(380, inputRect.width, viewport.width - 8));
  const lineHeight = Math.max(14, caretRect.height || fallbackLineHeight || 18);
  const caretLeft = clamp(caretRect.left, inputRect.left, inputRect.right);
  const caretTop = clamp(
    caretRect.top,
    inputRect.top,
    Math.max(inputRect.top, inputRect.bottom - lineHeight),
  );
  const caretBottom = clamp(
    caretTop + lineHeight,
    inputRect.top + lineHeight,
    inputRect.bottom,
  );
  const left = clamp(caretLeft, 4, Math.max(4, viewport.width - width - 4));
  const top = clamp(
    caretBottom + lineHeight + 12,
    4,
    Math.max(4, viewport.height - 8 - 56),
  );
  const maxHeight = Math.max(56, viewport.height - top - 8);
  return {
    left,
    top,
    width,
    maxHeight: Math.min(280, maxHeight),
  };
}
