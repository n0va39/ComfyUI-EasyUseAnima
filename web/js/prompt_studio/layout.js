// @ts-check

import {
  getAdvancedEditorElement,
} from "./state.js";

function advancedEditorWidth(node) {
  return Math.max(280, Math.round((Number(node?.size?.[0]) || 420) - 18));
}

function advancedTextareaPixelMetric(textarea, property) {
  const style = textarea instanceof HTMLElement ? getComputedStyle(textarea) : null;
  return Number.parseFloat(style?.[property] || "") || 0;
}

function advancedTextareaTwoLineHeight(textarea) {
  const style = textarea instanceof HTMLElement ? getComputedStyle(textarea) : null;
  const fontSize = Number.parseFloat(style?.fontSize || "") || 12;
  const lineHeightRaw = Number.parseFloat(style?.lineHeight || "");
  const lineHeight = Number.isFinite(lineHeightRaw) && lineHeightRaw > 0 ? lineHeightRaw : fontSize * 1.35;
  const verticalPadding =
    advancedTextareaPixelMetric(textarea, "paddingTop")
    + advancedTextareaPixelMetric(textarea, "paddingBottom");
  const verticalBorder =
    advancedTextareaPixelMetric(textarea, "borderTopWidth")
    + advancedTextareaPixelMetric(textarea, "borderBottomWidth");
  return Math.ceil(lineHeight * 2 + verticalPadding + verticalBorder);
}

function advancedTextareaContentHeight(textarea) {
  if (!(textarea instanceof HTMLTextAreaElement)) {
    return 0;
  }
  const previousHeight = textarea.style.height;
  const previousMinHeight = textarea.style.minHeight;
  const previousOverflow = textarea.style.overflowY;
  textarea.style.minHeight = "0px";
  textarea.style.height = "auto";
  textarea.style.overflowY = "hidden";
  const contentHeight = Math.ceil(
    (Number(textarea.scrollHeight) || 0)
    + advancedTextareaPixelMetric(textarea, "borderTopWidth")
    + advancedTextareaPixelMetric(textarea, "borderBottomWidth"),
  );
  textarea.style.height = previousHeight;
  textarea.style.minHeight = previousMinHeight;
  textarea.style.overflowY = previousOverflow;
  return contentHeight;
}

function advancedTextareaMinimumHeight(textarea) {
  return Math.max(
    46,
    advancedTextareaTwoLineHeight(textarea),
  );
}

function advancedTextareaCurrentHeight(textarea) {
  return Math.max(
    advancedTextareaMinimumHeight(textarea),
    Math.ceil(Number.parseFloat(textarea?.style?.height || "") || 0),
    Math.ceil(Number(textarea?.offsetHeight) || 0),
    Math.ceil(Number(textarea?.clientHeight) || 0),
  );
}

function updateAdvancedEditorWidth(node) {
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return;
  }
  const width = Number(node?.size?.[0]) || 360;
  const editorWidth = advancedEditorWidth(node);
  editor.style.width = `${editorWidth}px`;
  editor.style.maxWidth = `${editorWidth}px`;
  editor.classList.toggle("is-narrow", width < 620);
}

export {
  advancedEditorWidth,
  advancedTextareaContentHeight,
  advancedTextareaCurrentHeight,
  advancedTextareaMinimumHeight,
  updateAdvancedEditorWidth,
};
