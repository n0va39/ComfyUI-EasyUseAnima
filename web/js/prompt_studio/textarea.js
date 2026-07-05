// @ts-check

import {
  advancedTextareaCurrentBoxHeight,
} from "./layout.js";

function advancedText(text, key) {
  return typeof text === "function" ? text(key) : key;
}

function advancedFieldTextareaPlaceholder(field, text) {
  if (field?.type === "naia") {
    return advancedText(text, "advanced.placeholder.naia");
  }
  if (field?.type === "trigger") {
    return advancedText(text, "advanced.placeholder.trigger");
  }
  if (field?.type === "artist") {
    return advancedText(text, "advanced.placeholder.artist");
  }
  return advancedText(text, "advanced.placeholder.general");
}

function advancedFieldTextareaTitle(field, linked, text) {
  if (field?.type === "naia") {
    return advancedText(text, "advanced.title.naia");
  }
  if (field?.type === "trigger") {
    return advancedText(text, "advanced.title.trigger");
  }
  return linked ? advancedText(text, "advanced.title.linked") : "";
}

function rememberAdvancedTextareaResizeStart(textarea) {
  textarea.__easyuseAnimaAdvancedResizeStartHeight = advancedTextareaCurrentBoxHeight(textarea);
}

function captureAdvancedTextareaManualResize(textarea, threshold = 2) {
  const startHeight = Number(textarea.__easyuseAnimaAdvancedResizeStartHeight || 0);
  const currentHeight = advancedTextareaCurrentBoxHeight(textarea);
  textarea.__easyuseAnimaAdvancedResizeStartHeight = currentHeight;
  return {
    changed: Math.abs(currentHeight - startHeight) > threshold,
    currentHeight,
  };
}

function syncAdvancedTextareaLinkedInputValue(node, inputName, value, linked) {
  if (!linked) {
    return false;
  }
  node.__easyuseAnimaAdvancedFieldInputValues ||= {};
  node.__easyuseAnimaAdvancedFieldInputValues[inputName] = value;
  return true;
}

export {
  advancedFieldTextareaPlaceholder,
  advancedFieldTextareaTitle,
  captureAdvancedTextareaManualResize,
  rememberAdvancedTextareaResizeStart,
  syncAdvancedTextareaLinkedInputValue,
};
