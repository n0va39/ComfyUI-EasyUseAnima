import { app } from "../../../scripts/app.js";
import { easyuseAnimaWatchLocale } from "./easyuse_anima_i18n.js";
import {
  FIELD_NAMES,
  EXTEND_FIELD_NAMES,
  STUDIO_WIDGET_VERTICAL_GAP,
  ADVANCED_NATIVE_CONTROL_EVENTS,
  DEFAULT_ADVANCED_RESOLUTION_BUCKET,
  DEFAULT_ADVANCED_RESOLUTION_SIZE,
  ADVANCED_WIDGET_INDEX,
} from "./prompt_studio/constants.js";
import {
  debounce,
} from "./prompt_studio/utils.js";
import {
  normalizeAdvancedResolutionBucket,
  normalizeAdvancedResolutionSize,
} from "./prompt_studio/schema.js";
import {
  getAdvancedEditorElement,
  getAdvancedFields,
  setAdvancedEditorElement,
  setAdvancedFields,
} from "./prompt_studio/state.js";
import {
  stopAdvancedControlEvent,
} from "./prompt_studio/dom.js";
import {
  forwardAdvancedWheelToCanvas,
  installMiddlePanForwarder,
} from "./prompt_studio/canvas_forwarding.js";
import {
  ensureLegendWidget,
} from "./prompt_studio/legend.js";
import {
  applyExtendSlotVisibility,
} from "./prompt_studio/extend_slots.js";
import {
  ensureExtendSlotControls as ensureExtendSlotControlsWithHooks,
  refreshExtendSlotControlsSize,
  renderExtendSlotControls as renderExtendSlotControlsWithHooks,
} from "./prompt_studio/extend_slot_controls.js";
import {
  layoutExtendPromptWidgets as layoutExtendPromptWidgetsWithHooks,
} from "./prompt_studio/extend_layout.js";
import {
  isAdvancedNode,
  isExtendNode,
  installAdvancedSaveSync,
  registerPromptStudioNodeHooks,
  syncAdvancedNodes,
} from "./prompt_studio/node_hooks.js";
import {
  ensureAdvancedStyle,
} from "./prompt_studio/style.js";
import {
  applyPromptStudioSettings,
  applyPromptStudioTextStyle,
  loadPromptStudioSettings,
} from "./prompt_studio/settings.js";
import {
  psText,
} from "./prompt_studio/text.js";
import {
  hideTrainedTagTooltip,
} from "./prompt_studio/tooltip.js";
import {
  createAdvancedControlBar,
  createAdvancedResolutionBar,
  createAdvancedWildcardBar,
} from "./prompt_studio/advanced_controls.js";
import {
  createAdvancedPane,
} from "./prompt_studio/advanced_fields_ui.js";
import {
  advancedFieldLabel,
  advancedWidget,
  applyAdvancedNaiaGeneralAutoToggle,
  hideAdvancedControlWidgets as hideAdvancedControlWidgetsWithHooks,
  hideAdvancedInternalWidget,
  parseAdvancedFields,
  removeAdvancedInternalInputSockets,
  repairAdvancedInternalWidgetValues as repairAdvancedInternalWidgetValuesWithHooks,
  writeAdvancedFields as writeAdvancedFieldsWithHooks,
} from "./prompt_studio/advanced_fields_state.js";
import {
  classifyPrompt,
  copyInputTextMetrics,
  ensureHighlightOverlay,
  highlightOverlayHtml,
  installPromptHighlightOverlayRefresh,
  overlayBounds,
  overlayScrollbarPadding,
  refreshAllPromptHighlights,
  requestOverlaySync,
  syncOverlayBounds,
} from "./prompt_studio/highlight.js";
import {
  findInputEl,
  findWidget,
  isWidgetInputLinked,
} from "./prompt_studio/widgets.js";
import {
  advancedEditorMinimumHeight,
  advancedEditorWidgetHeight,
  updateAdvancedEditorWidth,
} from "./prompt_studio/layout.js";
import {
  scheduleAdvancedLayout as scheduleAdvancedLayoutWithHooks,
  scheduleAdvancedResizeFinalize as scheduleAdvancedResizeFinalizeWithHooks,
} from "./prompt_studio/advanced_layout_controller.js";
import {
  guardAdvancedEditorNativeControlEvent,
} from "./prompt_studio/wheel.js";
import {
  desiredTextareaHeight,
  expandStudioInputToContent as expandStudioInputToContentWithHooks,
  growStudioManualHeightToContent as growStudioManualHeightToContentWithHooks,
  rebalanceStudioInputHeights as rebalanceStudioInputHeightsWithHooks,
  setStudioInputHeight as setStudioInputHeightWithHooks,
  setStudioManualHeight as setStudioManualHeightWithHooks,
  studioCurrentHeight,
  studioDefaultHeight,
  visibleStudioWidgets as visibleStudioWidgetsWithHooks,
} from "./prompt_studio/studio_textareas.js";
import {
  applyExecutedInputs as applyExecutedInputsWithHooks,
  restoreInputFromWidget,
  syncStudioValues as syncStudioValuesWithHooks,
  syncWidgetValue,
} from "./prompt_studio/studio_values.js";
import {
  applyAdvancedExecutedInputs as applyAdvancedExecutedInputsWithHooks,
  syncAdvancedValues as syncAdvancedValuesWithHooks,
} from "./prompt_studio/advanced_values.js";
import {
  applyWildcardExecutedInputs as applyWildcardExecutedInputsWithHooks,
} from "./prompt_studio/wildcard_values.js";
import {
  captureAdvancedConfigure,
  ensureAdvancedWidgetValue,
  pruneDisconnectedAdvancedFieldInputValues,
} from "./prompt_studio/serialization.js";

function markNodeDirty(node) {
  node?.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
}

function advancedFieldsStateHooks() {
  return {
    advancedWidgetIndex: ADVANCED_WIDGET_INDEX,
    graph: app.graph,
    markNodeDirty,
    renderAdvancedEditor,
  };
}

function repairAdvancedInternalWidgetValues(node) {
  return repairAdvancedInternalWidgetValuesWithHooks(node, advancedFieldsStateHooks());
}

function hideAdvancedControlWidgets(node) {
  hideAdvancedControlWidgetsWithHooks(node, advancedFieldsStateHooks());
}

function writeAdvancedFields(node, fields, options = {}) {
  writeAdvancedFieldsWithHooks(node, fields, options, advancedFieldsStateHooks());
}

function advancedValuesHooks() {
  return {
    advancedWidget,
    parseAdvancedFields,
    repairAdvancedInternalWidgetValues,
    renderAdvancedEditor,
    writeAdvancedFields,
  };
}

function syncAdvancedValues(node, serialized = null) {
  syncAdvancedValuesWithHooks(node, serialized, advancedValuesHooks());
}

function applyAdvancedExecutedInputs(node, message) {
  applyAdvancedExecutedInputsWithHooks(node, message, advancedValuesHooks());
}

function applyWildcardExecutedInputs(node, message) {
  applyWildcardExecutedInputsWithHooks(node, message, { markNodeDirty });
}

function refreshNodeSize(node, options = {}) {
  const update = () => {
    const size = node.computeSize();
    const width = Math.max(size[0], node.size?.[0] || size[0]);
    const height = Math.max(size[1], 80);
    if (
      Math.abs(width - (node.size?.[0] || 0)) > 1
      || Math.abs(height - (node.size?.[1] || 0)) > 1
    ) {
      node.setSize?.([width, height]);
    }
    app.graph.setDirtyCanvas(true, true);
  };
  if (options.immediate) {
    update();
  } else {
    requestAnimationFrame(update);
  }
}

function studioTextareaHooks() {
  return {
    refreshNodeSize,
    studioFieldNames,
    updateHighlight,
  };
}

function setStudioInputHeight(node, widget, height, refresh = false) {
  setStudioInputHeightWithHooks(node, widget, height, refresh, studioTextareaHooks());
}

function growStudioManualHeightToContent(node, widget, refresh = false) {
  return growStudioManualHeightToContentWithHooks(node, widget, refresh, studioTextareaHooks());
}

function setStudioManualHeight(node, widget) {
  setStudioManualHeightWithHooks(node, widget, studioTextareaHooks());
}

function expandStudioInputToContent(node, widget, refresh = false) {
  expandStudioInputToContentWithHooks(node, widget, refresh, studioTextareaHooks());
}

function visibleStudioWidgets(node) {
  return visibleStudioWidgetsWithHooks(node, studioTextareaHooks());
}

function studioValuesHooks() {
  return {
    applyExtendSlotVisibility,
    expandStudioInputToContent,
    hookStudioNode,
    isExtendNode,
    studioFieldNames,
  };
}

function syncStudioValues(node, serialized = null) {
  syncStudioValuesWithHooks(node, serialized, studioValuesHooks());
}

function applyExecutedInputs(node, message) {
  applyExecutedInputsWithHooks(node, message, studioValuesHooks());
}

function markCanvasDirty() {
  app.graph?.setDirtyCanvas(true, true);
  app.canvas?.setDirty?.(true, true);
}

function extendLayoutHooks() {
  return {
    isExtendNode,
    markCanvasDirty,
    refreshExtendSlotControlsSize,
  };
}

function layoutExtendPromptWidgets(node) {
  layoutExtendPromptWidgetsWithHooks(node, extendLayoutHooks());
}

function rebalanceStudioInputHeights(node) {
  rebalanceStudioInputHeightsWithHooks(node, studioTextareaHooks());
}

function displayText(node, widget) {
  if (isWidgetInputLinked(node, widget.name) && widget.__easyuseAnimaExecutedText != null) {
    return String(widget.__easyuseAnimaExecutedText);
  }
  return String(widget?.inputEl?.value ?? widget?.value ?? "");
}

function studioFieldNames(node) {
  return isExtendNode(node) ? EXTEND_FIELD_NAMES : FIELD_NAMES;
}

function promptHighlightHooks() {
  return {
    findWidget,
    isAdvancedNode,
    scheduleAdvancedHighlights,
    studioFieldNames,
    updateHighlight,
  };
}

function advancedControlHooks() {
  return {
    renderAdvancedEditor,
    scheduleAdvancedHighlights,
    scheduleAdvancedLayout,
  };
}

function advancedFieldsUiHooks() {
  return {
    advancedFieldLabel,
    applyAdvancedNaiaGeneralAutoToggle,
    parseAdvancedFields,
    registerAdvancedAutocompleteInput,
    scheduleAdvancedFieldHighlight,
    scheduleAdvancedLayout,
    updateAdvancedFieldHighlight,
    writeAdvancedFields,
  };
}

function markGraphDirty() {
  app.graph?.setDirtyCanvas?.(true, true);
}

function advancedLayoutControllerHooks() {
  return {
    markGraphDirty,
    scheduleAdvancedHighlights,
  };
}

function scheduleAdvancedLayout(node, reason = "layout") {
  scheduleAdvancedLayoutWithHooks(node, reason, advancedLayoutControllerHooks());
}

function scheduleAdvancedResizeFinalize(node) {
  scheduleAdvancedResizeFinalizeWithHooks(node, advancedLayoutControllerHooks());
}

function extendSlotControlHooks() {
  return {
    expandStudioInputToContent,
    isExtendNode,
    layoutExtendPromptWidgets,
    refreshNodeSize,
    visibleStudioWidgets,
  };
}

function renderExtendSlotControls(node) {
  renderExtendSlotControlsWithHooks(node, extendSlotControlHooks());
}

function ensureExtendSlotControls(node) {
  ensureExtendSlotControlsWithHooks(node, extendSlotControlHooks());
}

function updateHighlight(node, widget, tokens = widget.__easyuseAnimaTokens || [], forceCopyMetrics = false) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  applyPromptStudioTextStyle(input);
  input.__easyuseAnimaHighlightRefresh = (force = false) => updateHighlight(node, widget, widget.__easyuseAnimaTokens || [], force);
  const overlay = ensureHighlightOverlay(input);
  if (!overlay) {
    return;
  }
  if (forceCopyMetrics) {
    copyInputTextMetrics(input, overlay);
  }
  syncOverlayBounds(input, overlay);
  const value = displayText(node, widget);
  overlay.innerHTML = highlightOverlayHtml(value, tokens, input.placeholder || "", input);
}

function advancedHighlightState(node, field) {
  node.__easyuseAnimaAdvancedHighlightStates ||= {};
  const id = String(field?.id || "field");
  node.__easyuseAnimaAdvancedHighlightStates[id] ||= {
    seq: 0,
    lastText: "",
    pendingText: null,
    tokens: [],
  };
  return node.__easyuseAnimaAdvancedHighlightStates[id];
}

function updateAdvancedFieldHighlight(node, field, textarea, tokens = null, forceCopyMetrics = false) {
  if (!(textarea instanceof HTMLTextAreaElement)) {
    return;
  }
  applyPromptStudioTextStyle(textarea);
  textarea.__easyuseAnimaNode = node;
  textarea.__easyuseAnimaField = field;
  textarea.__easyuseAnimaHighlightRefresh = (force = false) => updateAdvancedFieldHighlight(node, field, textarea, null, force);
  const overlay = ensureHighlightOverlay(textarea);
  if (!overlay) {
    return;
  }
  const state = advancedHighlightState(node, field);
  const value = String(textarea.value || "");
  if (forceCopyMetrics) {
    copyInputTextMetrics(textarea, overlay);
  }
  syncOverlayBounds(textarea, overlay);
  overlay.innerHTML = highlightOverlayHtml(value, tokens || state.tokens || [], textarea.placeholder || "", textarea);
}

function scheduleAdvancedFieldHighlight(node, field, textarea) {
  const state = advancedHighlightState(node, field);
  const text = String(textarea?.value || "");
  if (!text.trim()) {
    state.tokens = [];
    state.lastText = "";
    state.pendingText = null;
    updateAdvancedFieldHighlight(node, field, textarea, []);
    return;
  }
  if (state.lastText === text && Array.isArray(state.tokens)) {
    updateAdvancedFieldHighlight(node, field, textarea, state.tokens);
    return;
  }
  if (state.pendingText === text) {
    updateAdvancedFieldHighlight(node, field, textarea, state.tokens);
    return;
  }

  const seq = ++state.seq;
  state.pendingText = text;
  updateAdvancedFieldHighlight(node, field, textarea, state.tokens);
  classifyPrompt(text)
    .then((tokens) => {
      if (seq !== state.seq || !textarea.isConnected) {
        return;
      }
      state.lastText = text;
      state.tokens = tokens;
      updateAdvancedFieldHighlight(node, field, textarea, tokens);
    })
    .catch(() => {
      if (seq !== state.seq || !textarea.isConnected) {
        return;
      }
      state.tokens = [];
      updateAdvancedFieldHighlight(node, field, textarea, []);
    })
    .finally(() => {
      if (state.pendingText === text) {
        state.pendingText = null;
      }
    });
}

function registerAdvancedAutocompleteInput(node, field, textarea) {
  if (!(textarea instanceof HTMLTextAreaElement) || textarea.readOnly) {
    return;
  }
  const options = {
    node,
    forceArtistOnly: field?.type === "artist",
  };
  if (typeof window.easyuseAnimaHookAutocompleteInput === "function") {
    window.easyuseAnimaHookAutocompleteInput(textarea, options);
    return;
  }
  window.__easyuseAnimaPendingAutocompleteInputs ||= [];
  window.__easyuseAnimaPendingAutocompleteInputs.push({ input: textarea, options });
}

function refreshAdvancedHighlights(node, { classify = true, forceCopyMetrics = false } = {}) {
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return;
  }
  const fields = getAdvancedFields(node) || parseAdvancedFields(node);
  const byId = new Map(fields.map((field) => [String(field.id), field]));
  const textareas = Array.from(editor.querySelectorAll("textarea[data-easyuse-anima-advanced-field-id]"));

  const updates = [];

  // Read DOM Sizes
  for (const textarea of textareas) {
    const field = byId.get(String(textarea.dataset.easyuseAnimaAdvancedFieldId || ""));
    if (!field) {
      continue;
    }
    applyPromptStudioTextStyle(textarea);
    const overlay = ensureHighlightOverlay(textarea);
    if (!overlay) {
      continue;
    }
    if (forceCopyMetrics) {
      copyInputTextMetrics(textarea, overlay);
    }

    const { left, top, width, height } = overlayBounds(textarea);
    const padding = overlayScrollbarPadding(textarea);
    const scrollTop = textarea.scrollTop;
    const scrollLeft = textarea.scrollLeft;

    const state = advancedHighlightState(node, field);
    const value = String(textarea.value || "");
    const htmlContent = highlightOverlayHtml(value, state.tokens || [], textarea.placeholder || "", textarea);

    updates.push({
      overlay,
      left,
      top,
      width,
      height,
      padding,
      scrollTop,
      scrollLeft,
      htmlContent,
      textarea,
      field,
      state,
      value
    });
  }

  // Write DOM
  for (const update of updates) {
    const { overlay, left, top, width, height, padding, scrollTop, scrollLeft, htmlContent, textarea, field, state, value } = update;

    if (overlay.style.left !== left) overlay.style.left = left;
    if (overlay.style.top !== top) overlay.style.top = top;
    if (overlay.style.width !== width) overlay.style.width = width;
    if (overlay.style.height !== height) overlay.style.height = height;
    if (overlay.style.paddingRight !== padding.right) overlay.style.paddingRight = padding.right;
    if (overlay.style.paddingBottom !== padding.bottom) overlay.style.paddingBottom = padding.bottom;
    if (overlay.scrollTop !== scrollTop) overlay.scrollTop = scrollTop;
    if (overlay.scrollLeft !== scrollLeft) overlay.scrollLeft = scrollLeft;

    if (overlay.innerHTML !== htmlContent) {
      overlay.innerHTML = htmlContent;
    }

    if (classify && (state.lastText !== value || !Array.isArray(state.tokens))) {
      scheduleAdvancedFieldHighlight(node, field, textarea);
    }
  }
}

function scheduleAdvancedHighlights(node, options = {}) {
  if (!getAdvancedEditorElement(node)) {
    return;
  }
  const previousOptions = node.__easyuseAnimaAdvancedHighlightOptions || {};
  node.__easyuseAnimaAdvancedHighlightOptions = {
    classify: options.classify !== false,
    forceCopyMetrics: previousOptions.forceCopyMetrics === true || options.forceCopyMetrics === true,
  };
  if (node.__easyuseAnimaAdvancedHighlightScheduled) {
    return;
  }
  node.__easyuseAnimaAdvancedHighlightScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaAdvancedHighlightScheduled = false;
    const refreshOptions = node.__easyuseAnimaAdvancedHighlightOptions || {};
    refreshAdvancedHighlights(node, refreshOptions);
    requestAnimationFrame(() => refreshAdvancedHighlights(node, { classify: false, forceCopyMetrics: refreshOptions.forceCopyMetrics === true }));
  });
}

function enhanceResizableInput(node, widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }

  const defaultHeight = studioDefaultHeight(widget);
  const minimumHeight = Math.min(defaultHeight, 54);

  applyPromptStudioTextStyle(input);
  widget.__easyuseAnimaHeight = Math.max(minimumHeight, widget.__easyuseAnimaHeight || defaultHeight);
  widget.__easyuseAnimaLayoutHeight = widget.__easyuseAnimaHeight + STUDIO_WIDGET_VERTICAL_GAP;
  input.style.boxSizing = "border-box";
  input.style.resize = "vertical";
  input.style.overflowY = "hidden";
  input.style.minHeight = `${minimumHeight}px`;
  input.style.height = `${widget.__easyuseAnimaHeight}px`;

  if (!widget.__easyuseAnimaStudioComputeWrapped) {
    const computeSize = widget.computeSize;
    widget.computeSize = function (width) {
      const base = computeSize?.apply(this, arguments) || [width, minimumHeight];
      const layoutHeight = (this.__easyuseAnimaHeight || minimumHeight) + STUDIO_WIDGET_VERTICAL_GAP;
      this.__easyuseAnimaLayoutHeight = layoutHeight;
      return [base[0], Math.max(base[1], layoutHeight)];
    };
    widget.__easyuseAnimaStudioComputeWrapped = true;
  }

  const syncHeight = () => {
    if (widget.__easyuseAnimaManualHeight) {
      growStudioManualHeightToContent(node, widget, "immediate");
      requestOverlaySync(input);
      return;
    }
    const height = desiredTextareaHeight(input, 0, minimumHeight, { includeCurrent: false });
    setStudioInputHeight(node, widget, height, "immediate");
  };
  const rememberResizeStart = () => {
    widget.__easyuseAnimaResizeStartHeight = studioCurrentHeight(widget, input);
  };
  const captureManualResize = () => {
    const startHeight = Number(widget.__easyuseAnimaResizeStartHeight || widget.__easyuseAnimaHeight || 0);
    const currentHeight = studioCurrentHeight(widget, input);
    widget.__easyuseAnimaResizeStartHeight = currentHeight;
    if (Math.abs(currentHeight - startHeight) > 2) {
      setStudioManualHeight(node, widget);
    } else {
      updateHighlight(node, widget);
    }
  };

  requestAnimationFrame(() => expandStudioInputToContent(node, widget, true));
  if (input.__easyuseAnimaStudioResizable) {
    return;
  }

  input.addEventListener("mousedown", rememberResizeStart);
  input.addEventListener("pointerdown", rememberResizeStart);
  input.addEventListener("mouseup", captureManualResize);
  input.addEventListener("pointerup", captureManualResize);
  input.addEventListener("input", syncHeight);
  input.__easyuseAnimaStudioResizable = true;
}

function hookStudioNode(node, attempt = 0) {
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
      try {
        const tokens = await classifyPrompt(text);
        if (seq !== classifySeq) {
          return;
        }
        widget.__easyuseAnimaLastClassifiedText = text;
        widget.__easyuseAnimaTokens = tokens;
        updateHighlight(node, widget, tokens);
      } catch {
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
    const input = findInputEl(widget);
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

    if (!widget.__easyuseAnimaStudioHooked) {
      const callback = widget.callback;
      widget.callback = function (value) {
        const result = callback?.apply(this, arguments);
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
        return result;
      };
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
    setTimeout(() => hookStudioNode(node, attempt + 1), 80);
  }
}

function renderAdvancedEditor(node) {
  const editor = getAdvancedEditorElement(node);
  if (!editor) {
    return;
  }
  const fields = setAdvancedFields(node, parseAdvancedFields(node));
  applyAdvancedNaiaGeneralAutoToggle(node, fields);
  editor.innerHTML = "";
  updateAdvancedEditorWidth(node);
  const panes = document.createElement("div");
  panes.className = "easyuse-anima-advanced-panes";
  const fieldHooks = advancedFieldsUiHooks();
  panes.append(
    createAdvancedPane(node, "positive", "advanced.positivePrompt", fieldHooks),
    createAdvancedPane(node, "negative", "advanced.negativePrompt", fieldHooks),
  );
  editor.append(
    createAdvancedControlBar(node, advancedControlHooks()),
    createAdvancedWildcardBar(node, advancedControlHooks()),
    createAdvancedResolutionBar(node, advancedControlHooks()),
    panes,
  );
  writeAdvancedFields(node, fields);
  scheduleAdvancedLayout(node, "render");
}

function hookAdvancedNode(node) {
  ensureAdvancedStyle();
  installAdvancedSaveSync(app, syncAllAdvancedNodes);
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
    editor.addEventListener("wheel", forwardAdvancedWheelToCanvas, { capture: true, passive: false });
    for (const eventName of ADVANCED_NATIVE_CONTROL_EVENTS) {
      editor.addEventListener(eventName, guardAdvancedEditorNativeControlEvent);
    }
    setAdvancedEditorElement(node, editor);
    const widget = node.addDOMWidget?.("easyuse_anima_advanced_editor", "EasyUseAnimaAdvancedEditor", editor, {
      serialize: false,
      hideOnZoom: false,
      getMinHeight: () => advancedEditorMinimumHeight(node),
      getHeight: () => advancedEditorWidgetHeight(node),
    });
    if (widget) {
      node.__easyuseAnimaAdvancedDomWidget = widget;
      widget.computeLayoutSize = () => {
        const height = advancedEditorWidgetHeight(node);
        return {
          minHeight: advancedEditorMinimumHeight(node),
          height,
          minWidth: 280,
        };
      };
    }
  }
  renderAdvancedEditor(node);
}

function scheduleHookAdvancedNode(node) {
  if (!node || node.__easyuseAnimaAdvancedHookScheduled) {
    return;
  }
  node.__easyuseAnimaAdvancedHookScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaAdvancedHookScheduled = false;
    hookAdvancedNode(node);
  });
}

const syncAllAdvancedNodes = () => syncAdvancedNodes(app, syncAdvancedValues);

function refreshPromptStudioLocaleDom() {
  for (const node of app.graph?._nodes || []) {
    if (isAdvancedNode(node)) {
      renderAdvancedEditor(node);
    } else if (isExtendNode(node)) {
      hookStudioNode(node);
      renderExtendSlotControls(node);
    }
    node?.setDirtyCanvas?.(true, true);
  }
  app.graph?.setDirtyCanvas?.(true, true);
}

app.registerExtension({
  name: "easyuse-anima.prompt-studio",
  async setup() {
    installMiddlePanForwarder();
    installAdvancedSaveSync(app, syncAllAdvancedNodes);
    installPromptHighlightOverlayRefresh(app, applyPromptStudioTextStyle);
    await loadPromptStudioSettings({
      hideTrainedTagTooltip,
      afterApply: () => {
        refreshAllPromptHighlights(app, promptHighlightHooks(), true);
        app.graph?.setDirtyCanvas(true, true);
      },
    });
    easyuseAnimaWatchLocale(() => {
      refreshPromptStudioLocaleDom();
      refreshAllPromptHighlights(app, promptHighlightHooks());
    });
    window.addEventListener("easyuse-anima-settings-updated", (event) => {
      if (!event?.detail) {
        return;
      }
      applyPromptStudioSettings(event.detail, { hideTrainedTagTooltip });
      for (const node of app.graph?._nodes || []) {
        if (isAdvancedNode(node)) {
          renderAdvancedEditor(node);
        }
      }
      refreshAllPromptHighlights(app, promptHighlightHooks(), true);
    });
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    registerPromptStudioNodeHooks(nodeType, nodeData, {
      applyAdvancedExecutedInputs,
      applyExecutedInputs,
      applyExtendSlotVisibility,
      applyWildcardExecutedInputs,
      captureAdvancedConfigure: (node, serialized) => (
        captureAdvancedConfigure(node, serialized, advancedWidget(node))
      ),
      hookStudioNode,
      isExtendNode,
      layoutExtendPromptWidgets,
      pruneDisconnectedAdvancedFieldInputValues,
      rebalanceStudioInputHeights,
      removeAdvancedInternalInputSockets,
      renderAdvancedEditor,
      renderExtendSlotControls,
      scheduleAdvancedResizeFinalize,
      scheduleHookAdvancedNode,
      syncAdvancedValues,
      syncStudioValues,
      updateAdvancedEditorWidth,
    });
  },
});
