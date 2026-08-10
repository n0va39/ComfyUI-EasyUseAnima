// @ts-check

/**
 * Return classification tokens only when they belong to the current text.
 *
 * @param {unknown} currentText
 * @param {unknown} classifiedText
 * @param {unknown} tokens
 * @returns {any[]}
 */
function highlightTokensForText(currentText, classifiedText, tokens) {
  if (String(currentText ?? "") !== String(classifiedText ?? "")) {
    return [];
  }
  return Array.isArray(tokens) ? tokens : [];
}

/**
 * Check both request sequence and text revision before publishing a result.
 *
 * @param {Object} request
 * @param {number} request.sequence
 * @param {unknown} request.text
 * @param {number} currentSequence
 * @param {unknown} currentText
 * @param {boolean} [connected]
 */
function highlightRequestOwnsText(
  request,
  currentSequence,
  currentText,
  connected = true,
) {
  return connected
    && request.sequence === currentSequence
    && String(request.text ?? "") === String(currentText ?? "");
}

export {
  highlightRequestOwnsText,
  highlightTokensForText,
};
