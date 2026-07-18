// @ts-check

import {
  ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT,
  ADVANCED_NATIVE_CONTROL_EVENTS,
} from "./constants.js";
import {
  createAdvancedControlBar,
  createAdvancedResolutionBar,
  createAdvancedWildcardBar,
} from "./advanced_controls.js";
import {
  createAdvancedPane,
} from "./advanced_fields_ui.js";
import {
  advancedFieldLabel,
  advancedWidget,
  applyAdvancedNaiaGeneralAutoToggle,
  hideAdvancedInternalWidget,
  parseAdvancedFields,
  removeAdvancedInternalInputSockets,
} from "./advanced_fields_state.js";
import {
  registerAdvancedAutocompleteInput,
  scheduleAdvancedFieldHighlight,
  updateAdvancedFieldHighlight,
} from "./advanced_highlights.js";
import {
  updateAdvancedEditorWidth,
} from "./layout.js";
import {
  ensureAdvancedWidgetValue,
} from "./serialization.js";
import {
  getAdvancedEditorElement,
  setAdvancedEditorElement,
  setAdvancedFields,
} from "./state.js";
import {
  ensureAdvancedStyle,
} from "./style.js";
import {
  guardAdvancedEditorNativeControlEvent,
} from "./wheel.js";
import { disposeExternalAutocompleteInputs } from "../autocomplete/entry_lifecycle.js";

function advancedControlHooks(hooks = {}) {
  return {
    renderAdvancedEditor: (node) => renderAdvancedEditor(node, hooks),
    scheduleAdvancedHighlights: hooks.scheduleAdvancedHighlights,
    scheduleAdvancedLayout: hooks.scheduleAdvancedLayout,
  };
}

function advancedFieldsUiHooks(hooks = {}) {
  return {
    advancedFieldLabel,
    applyAdvancedNaiaGeneralAutoToggle,
    parseAdvancedFields,
    registerAdvancedAutocompleteInput,
    scheduleAdvancedFieldHighlight,
    scheduleAdvancedLayout: hooks.scheduleAdvancedLayout,
    updateAdvancedFieldHighlight,
    writeAdvancedFields: hooks.writeAdvancedFields,
  };
}

function disposeAdvancedAutocompleteInputs(node) {
  disposeExternalAutocompleteInputs(window, getAdvancedEditorElement(node));
}

function renderAdvancedEditor(node, hooks = {}) {
  const {
    scheduleAdvancedLayout = () => {},
    writeAdvancedFields = () => {},
  } = hooks;
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return;
  }
  const fields = setAdvancedFields(node, parseAdvancedFields(node));
  applyAdvancedNaiaGeneralAutoToggle(fields);
  disposeAdvancedAutocompleteInputs(node);
  editor.innerHTML = "";
  updateAdvancedEditorWidth(node);
  const panes = document.createElement("div");
  panes.className = "easyuse-anima-advanced-panes";
  const fieldHooks = advancedFieldsUiHooks(hooks);
  const controlHooks = advancedControlHooks(hooks);
  panes.append(
    createAdvancedPane(node, "positive", "advanced.positivePrompt", fieldHooks),
    createAdvancedPane(node, "negative", "advanced.negativePrompt", fieldHooks),
  );
  editor.append(
    createAdvancedControlBar(node, controlHooks),
    createAdvancedWildcardBar(node, controlHooks),
    createAdvancedResolutionBar(node, controlHooks),
    panes,
  );
  writeAdvancedFields(node, fields);
  scheduleAdvancedLayout(node, "render");
}

function hookAdvancedNode(node, hooks = {}) {
  const {
    hideAdvancedControlWidgets = () => {},
    installAdvancedSaveSync = () => {},
    observeAdvancedEditorWidth = () => {},
  } = hooks;
  ensureAdvancedStyle();
  installAdvancedSaveSync();
  ensureAdvancedWidgetValue(node, advancedWidget(node));
  removeAdvancedInternalInputSockets(node);
  hideAdvancedInternalWidget(node, "advanced_fields");
  hideAdvancedControlWidgets(node);
  node.serialize_widgets = true;
  node.minWidth = Math.max(Number(node.minWidth) || 0, 360);
  if (Array.isArray(node.size)) {
    node.size[0] = Math.max(Number(node.size[0]) || 420, 360);
  }
  if (!getAdvancedEditorElement(node)) {
    const editor = document.createElement("div");
    editor.className = "easyuse-anima-advanced-editor";
    for (const eventName of ADVANCED_NATIVE_CONTROL_EVENTS) {
      editor.addEventListener(eventName, guardAdvancedEditorNativeControlEvent);
    }
    setAdvancedEditorElement(node, editor);
    const widget = node.addDOMWidget?.("easyuse_anima_advanced_editor", "EasyUseAnimaAdvancedEditor", editor, {
      serialize: false,
      hideOnZoom: false,
      getMinHeight: () => ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT,
    });
    if (widget) {
      node.__easyuseAnimaAdvancedDomWidget = widget;
    }
  }
  observeAdvancedEditorWidth(node);
  renderAdvancedEditor(node, hooks);
}

function scheduleHookAdvancedNode(node, hooks = {}) {
  if (!node || node.__easyuseAnimaAdvancedHookScheduled) {
    return;
  }
  node.__easyuseAnimaAdvancedHookScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaAdvancedHookScheduled = false;
    hookAdvancedNode(node, hooks);
  });
}

export {
  disposeAdvancedAutocompleteInputs,
  hookAdvancedNode,
  renderAdvancedEditor,
  scheduleHookAdvancedNode,
};
