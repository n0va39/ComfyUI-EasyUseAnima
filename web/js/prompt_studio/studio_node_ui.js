// @ts-check

import {
  classifyPrompt,
} from "./highlight.js";
import {
  displayText,
} from "./highlight_ui.js";
import {
  highlightRequestOwnsText,
} from "./highlight_revision.js";
import {
  psText,
} from "./text.js";
import {
  debounce,
} from "./utils.js";
import {
  findInputEl,
  findWidget,
} from "./widgets.js";

function hookStudioNode(node, attempt = 0, hooks = {}) {
  const {
    applyExtendSlotVisibility = () => {},
    enhanceResizableInput = () => {},
    ensureExtendSlotControls = () => {},
    ensureLegendWidget = () => {},
    isExtendNode = () => false,
    layoutExtendPromptWidgets = () => {},
    refreshNodeSize = () => {},
    resolveStudioInput = (_node, widget) => findInputEl(widget),
    restoreInputFromWidget = () => {},
    studioFieldNames = () => [],
    syncWidgetValue = () => {},
    updateHighlight = () => {},
  } = hooks;
  const fieldNames = studioFieldNames(node);
  const updateByField = new Map();
  let pendingInput = false;

  const getUpdateField = (fieldName) => {
    if (updateByField.has(fieldName)) {
      return updateByField.get(fieldName);
    }
    let classifySeq = 0;
    const update = debounce(async () => {
      const widget = findWidget(node, fieldName);
      if (!widget) {
        return;
      }
      const text = displayText(node, widget);
      if (!text.trim()) {
        widget.__easyuseAnimaTokens = [];
        widget.__easyuseAnimaLastClassifiedText = "";
        widget.__easyuseAnimaPendingClassifyText = null;
        updateHighlight(node, widget);
        return;
      }
      if (
        widget.__easyuseAnimaLastClassifiedText === text
        && Array.isArray(widget.__easyuseAnimaTokens)
      ) {
        updateHighlight(node, widget, widget.__easyuseAnimaTokens);
        return;
      }
      if (widget.__easyuseAnimaPendingClassifyText === text) {
        return;
      }

      const seq = ++classifySeq;
      widget.__easyuseAnimaPendingClassifyText = text;
      const request = { sequence: seq, text };
      try {
        const tokens = await classifyPrompt(text);
        if (!highlightRequestOwnsText(
          request,
          classifySeq,
          displayText(node, widget),
        )) {
          return;
        }
        widget.__easyuseAnimaLastClassifiedText = text;
        widget.__easyuseAnimaTokens = tokens;
        updateHighlight(node, widget, tokens);
      } catch {
        if (!highlightRequestOwnsText(
          request,
          classifySeq,
          displayText(node, widget),
        )) {
          return;
        }
        widget.__easyuseAnimaTokens = [];
        updateHighlight(node, widget);
      } finally {
        if (widget.__easyuseAnimaPendingClassifyText === text) {
          widget.__easyuseAnimaPendingClassifyText = null;
        }
      }
    });
    updateByField.set(fieldName, update);
    return update;
  };

  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    const input = resolveStudioInput(node, widget);
    if (!input) {
      pendingInput = true;
      continue;
    }
    restoreInputFromWidget(widget);
    if (isExtendNode(node) && name === "naia_prompt_3") {
      input.readOnly = true;
      input.placeholder = psText("extend.naiaResult");
      input.title = psText("extend.naiaResultTitle");
    }
    enhanceResizableInput(node, widget);
    const updateField = getUpdateField(name);

    if (!widget.__easyuseAnimaStudioCallbackHooked) {
      const callback = widget.callback;
      widget.callback = function (_value) {
        const result = callback?.apply(this, arguments);
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
        return result;
      };
      widget.__easyuseAnimaStudioCallbackHooked = true;
    }
    if (widget.__easyuseAnimaStudioHookInput !== input) {
      input.addEventListener("input", () => {
        widget.value = input.value;
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
      });
      input.addEventListener("change", () => {
        widget.value = input.value;
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
      });
      input.addEventListener("blur", () => syncWidgetValue(widget));
      input.addEventListener("click", () => updateHighlight(node, widget));
      input.addEventListener("keyup", () => updateHighlight(node, widget));
      widget.__easyuseAnimaStudioHookInput = input;
      widget.__easyuseAnimaStudioHooked = true;
    }
    updateField();
  }

  if (isExtendNode(node)) {
    applyExtendSlotVisibility(node);
    ensureExtendSlotControls(node);
  }
  ensureLegendWidget(node, refreshNodeSize);
  if (isExtendNode(node)) {
    layoutExtendPromptWidgets(node);
  }
  refreshNodeSize(node);
  if (pendingInput && attempt < 12) {
    setTimeout(() => hookStudioNode(node, attempt + 1, hooks), 80);
  }
}

export {
  hookStudioNode,
};
