import { app } from "../../../scripts/app.js";
import { easyuseAnimaWatchLocale } from "./easyuse_anima_i18n.js";
import {
  FIELD_NAMES,
  EXTEND_FIELD_NAMES,
  EXTEND_VISIBLE_SLOTS_PROPERTY,
  EXTEND_ACTIVE_SLOTS_WIDGET,
  FIELD_HEIGHTS,
  EXTEND_FIELD_HEIGHTS,
  STUDIO_WIDGET_VERTICAL_GAP,
  ADVANCED_NATIVE_CONTROL_EVENTS,
  ADVANCED_CONTROL_WIDGETS,
  ADVANCED_WILDCARD_MODES,
  ADVANCED_WILDCARD_SEED_CONTROLS,
  ADVANCED_WILDCARD_DEFAULT_MODE,
  ARTIST_MIX_MODES,
  ADVANCED_RESOLUTION_BUCKETS,
  CUSTOM_ADVANCED_RESOLUTION_BUCKET,
  NAIA_ADVANCED_RESOLUTION_BUCKET,
  DEFAULT_ADVANCED_RESOLUTION_BUCKET,
  DEFAULT_ADVANCED_RESOLUTION_SIZE,
  ADVANCED_WIDGET_INDEX,
  ADVANCED_INTERNAL_WIDGET_NAMES,
  ADVANCED_FIELDS_PROPERTY,
  ADVANCED_FIELD_LABELS,
} from "./prompt_studio/constants.js";
import {
  debounce,
  advancedResolutionLabel,
  snapResolution32,
  clampAdvancedNumber,
} from "./prompt_studio/utils.js";
import {
  advancedDefaultFields,
  advancedFieldInputName,
  advancedResolutionOptions,
  normalizeAdvancedField,
  normalizeAdvancedResolutionBucket,
  normalizeAdvancedResolutionSize,
  normalizeAdvancedWidgetQueueValue,
  normalizeArtistMixMode,
} from "./prompt_studio/schema.js";
import {
  getAdvancedEditorElement,
  getAdvancedFields,
  setAdvancedEditorElement,
  setAdvancedFields,
  setHiddenWidget,
} from "./prompt_studio/state.js";
import {
  closeAdvancedHelpPopovers,
  openAdvancedHelpPopover,
  protectAdvancedNativeControl,
  stopAdvancedControlEvent,
  updateAdvancedSummary,
} from "./prompt_studio/dom.js";
import {
  forwardAdvancedWheelToCanvas,
  installMiddlePanForwarder,
} from "./prompt_studio/canvas_forwarding.js";
import {
  desiredLegendHeight,
  ensureLegendWidget,
} from "./prompt_studio/legend.js";
import {
  applyExtendSlotVisibility,
  extendVisibleSlots,
  parseExtendSlots,
  writeExtendVisibleSlots,
} from "./prompt_studio/extend_slots.js";
import {
  ensureExtendSlotControls as ensureExtendSlotControlsWithHooks,
  refreshExtendSlotControlsSize,
  renderExtendSlotControls as renderExtendSlotControlsWithHooks,
} from "./prompt_studio/extend_slot_controls.js";
import {
  advancedPaneFields,
  hasAdvancedNaia,
  hasPositiveTrigger,
  moveAdvancedFieldInPane,
} from "./prompt_studio/fields.js";
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
  PROMPT_STUDIO_SETTINGS,
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
  firstValue,
  isWidgetInputLinked,
} from "./prompt_studio/widgets.js";
import {
  advancedEditorMinimumHeight,
  advancedEditorWidgetHeight,
  advancedMinimumNodeHeight,
  advancedTextareaContentHeight,
  advancedTextareaCurrentHeight,
  advancedTextareaMinimumHeight,
  clampAdvancedNodeToMinimumHeight,
  updateAdvancedEditorWidth,
} from "./prompt_studio/layout.js";
import {
  advancedFieldTextareaPlaceholder,
  advancedFieldTextareaTitle,
  captureAdvancedTextareaManualResize,
  rememberAdvancedTextareaResizeStart,
  syncAdvancedTextareaLinkedInputValue,
} from "./prompt_studio/textarea.js";
import {
  guardAdvancedEditorNativeControlEvent,
} from "./prompt_studio/wheel.js";
import {
  advancedFieldDisplayText,
  advancedFieldIndexLabel,
  advancedFieldInputLinked,
  advancedFieldsBackup,
  captureAdvancedConfigure,
  collectAdvancedEditorFields,
  ensureAdvancedWidgetValue,
  mergeAdvancedFieldInputValues,
  pruneDisconnectedAdvancedFieldInputValues,
  syncAdvancedFieldInputs,
  syncAdvancedFieldsBackup,
} from "./prompt_studio/serialization.js";

function repairAdvancedInternalWidgetValues(node) {
  let changed = false;
  for (const name of Object.keys(ADVANCED_WIDGET_INDEX)) {
    if (name === "advanced_fields") {
      continue;
    }
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    const next = normalizeAdvancedWidgetQueueValue(name, widget.value);
    if (widget.value !== next) {
      widget.value = next;
      const input = findInputEl(widget);
      if (input) {
        input.value = String(next ?? "");
      }
      changed = true;
    }
  }
  if (changed) {
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
  }
  return changed;
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







function textareaContentHeight(input, minimumHeight) {
  if (!input) {
    return minimumHeight;
  }
  const previousHeight = input.style.height;
  const previousOverflow = input.style.overflowY;
  input.style.height = "auto";
  input.style.overflowY = "hidden";
  const contentHeight = Math.ceil(Number(input.scrollHeight) || 0);
  input.style.height = previousHeight;
  input.style.overflowY = previousOverflow;
  return Math.max(minimumHeight, contentHeight);
}

function desiredTextareaHeight(input, currentHeight, minimumHeight, options = {}) {
  const includeCurrent = options.includeCurrent !== false;
  const contentHeight = textareaContentHeight(input, minimumHeight);
  return Math.max(
    minimumHeight,
    includeCurrent ? Math.round(Number(currentHeight) || 0) : 0,
    contentHeight,
  );
}

function studioVisualMinimumHeight(widget) {
  return Math.min(studioDefaultHeight(widget), 54);
}

function studioMinimumHeight(widget, input = findInputEl(widget)) {
  return studioVisualMinimumHeight(widget);
}

function studioContentHeight(widget, input = findInputEl(widget)) {
  return desiredTextareaHeight(input, 0, studioVisualMinimumHeight(widget), { includeCurrent: false });
}

function studioCurrentHeight(widget, input = findInputEl(widget)) {
  const styleHeight = Number.parseFloat(input?.style?.height || "");
  return Math.round(
    Number(input?.offsetHeight)
    || Number(input?.clientHeight)
    || styleHeight
    || Number(widget?.__easyuseAnimaHeight)
    || studioDefaultHeight(widget),
  );
}

function setStudioInputHeight(node, widget, height, refresh = false) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const minimumHeight = studioMinimumHeight(widget, input);
  const nextHeight = Math.max(minimumHeight, Math.round(Number(height) || 0));
  widget.__easyuseAnimaLayoutHeight = nextHeight + STUDIO_WIDGET_VERTICAL_GAP;
  if (Math.abs(nextHeight - (widget.__easyuseAnimaHeight || 0)) > 1) {
    widget.__easyuseAnimaHeight = nextHeight;
    input.style.height = `${nextHeight}px`;
    if (refresh) {
      refreshNodeSize(node, { immediate: refresh === "immediate" });
    }
  } else {
    input.style.height = `${nextHeight}px`;
  }
  syncStudioOverflow(widget);
  updateHighlight(node, widget);
}

function syncStudioOverflow(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const height = studioCurrentHeight(widget, input);
  const contentHeight = textareaContentHeight(input, studioVisualMinimumHeight(widget));
  input.style.overflowY = contentHeight > height + 2 ? "auto" : "hidden";
  if (input.__easyuseAnimaHighlightOverlay) {
    input.__easyuseAnimaHighlightOverlay.style.overflow = "hidden";
  }
}

function growStudioManualHeightToContent(node, widget, refresh = false) {
  const input = findInputEl(widget);
  if (!input || !widget.__easyuseAnimaManualHeight || widget.__easyuseAnimaExtendHidden) {
    return false;
  }
  const currentHeight = studioCurrentHeight(widget, input);
  const contentHeight = studioContentHeight(widget, input);
  if (contentHeight > currentHeight + 2) {
    setStudioInputHeight(node, widget, contentHeight, refresh);
    return true;
  }
  syncStudioOverflow(widget);
  updateHighlight(node, widget);
  return false;
}

function setStudioManualHeight(node, widget) {
  const input = findInputEl(widget);
  if (!input || widget.__easyuseAnimaExtendHidden) {
    return;
  }
  widget.__easyuseAnimaManualHeight = true;
  setStudioInputHeight(
    node,
    widget,
    Math.max(studioCurrentHeight(widget, input), studioContentHeight(widget, input)),
    "immediate",
  );
}

function expandStudioInputToContent(node, widget, refresh = false) {
  const input = findInputEl(widget);
  if (!input || widget.__easyuseAnimaExtendHidden) {
    return;
  }
  if (widget.__easyuseAnimaManualHeight) {
    growStudioManualHeightToContent(node, widget, refresh);
    return;
  }
  const height = studioContentHeight(widget, input);
  setStudioInputHeight(node, widget, height, refresh);
}

function visibleStudioWidgets(node) {
  return studioFieldNames(node)
    .map((name) => findWidget(node, name))
    .filter((widget) => {
      const input = findInputEl(widget);
      return widget && input && !widget.hidden && !widget.__easyuseAnimaExtendHidden;
    });
}

function widgetHeight(widget, fallback = 24) {
  const input = findInputEl(widget);
  if (input && !widget.__easyuseAnimaExtendHidden) {
    return studioCurrentHeight(widget, input) + STUDIO_WIDGET_VERTICAL_GAP;
  }
  const size = widget?.computeSize?.();
  return Math.max(0, Number(size?.[1]) || Number(widget?.__height) || fallback);
}

function visibleExtendPromptWidgets(node) {
  return EXTEND_FIELD_NAMES
    .map((name) => findWidget(node, name))
    .filter((widget) => widget && !widget.hidden && !widget.__easyuseAnimaExtendHidden);
}

function firstExtendPromptY(node) {
  const visible = visibleExtendPromptWidgets(node);
  const yValues = visible
    .map((widget) => Number(widget.y))
    .filter((value) => Number.isFinite(value) && value > 0);
  if (yValues.length) {
    return Math.min(...yValues);
  }

  const firstIndex = node.widgets?.findIndex((widget) => EXTEND_FIELD_NAMES.includes(widget?.name)) ?? -1;
  if (firstIndex > 0) {
    for (let index = firstIndex - 1; index >= 0; index -= 1) {
      const widget = node.widgets[index];
      if (!widget || widget.hidden || widget.__easyuseAnimaExtendHidden) {
        continue;
      }
      const height = Number(widget.computeSize?.(node.size?.[0])?.[1]) || Number(widget.__height) || 24;
      const y = Number(widget.y);
      if (Number.isFinite(y)) {
        return y + height + 6;
      }
    }
  }
  return 120;
}

function layoutExtendPromptWidgets(node) {
  if (!isExtendNode(node)) {
    return;
  }

  let cursorY = firstExtendPromptY(node);
  const visible = visibleExtendPromptWidgets(node);
  for (const widget of visible) {
    widget.y = cursorY;
    const input = findInputEl(widget);
    if (input) {
      input.style.height = `${studioCurrentHeight(widget, input)}px`;
    }
    cursorY += widgetHeight(widget, 72);
  }

  const controlsWidget = findWidget(node, "easyuse_anima_extend_slot_controls");
  if (controlsWidget && !controlsWidget.hidden) {
    refreshExtendSlotControlsSize(node);
    controlsWidget.y = cursorY;
    cursorY += Math.max(30, Number(controlsWidget.__height) || 30) + 8;
  }

  const legendWidget = findWidget(node, "easyuse_anima_color_legend");
  if (legendWidget && !legendWidget.hidden) {
    legendWidget.y = cursorY;
    cursorY += Math.max(desiredLegendHeight(), Number(legendWidget.__height) || 0) + 8;
  }

  const minHeight = Math.ceil(cursorY + 8);
  if (Number(node.size?.[1]) < minHeight) {
    node.setSize?.([node.size?.[0] || node.computeSize?.()[0] || 300, minHeight]);
  }
  app.graph?.setDirtyCanvas(true, true);
  app.canvas?.setDirty?.(true, true);
}

function rebalanceStudioInputHeights(node) {
  const widgets = visibleStudioWidgets(node);
  if (!widgets.length) {
    return;
  }

  const currentHeights = widgets.map((widget) => studioCurrentHeight(widget));
  const minimumHeights = widgets.map((widget) => studioMinimumHeight(widget));
  const currentTotal = currentHeights.reduce((sum, value) => sum + value, 0);
  const minimumTotal = minimumHeights.reduce((sum, value) => sum + value, 0);
  const computedHeight = Number(node.computeSize?.()[1]) || currentTotal;
  const nonInputHeight = Math.max(0, computedHeight - currentTotal);
  const targetInputTotal = Math.max(minimumTotal, (Number(node.size?.[1]) || computedHeight) - nonInputHeight);

  if (targetInputTotal < currentTotal - 2) {
    const currentExtra = Math.max(0, currentTotal - minimumTotal);
    const targetExtra = Math.max(0, targetInputTotal - minimumTotal);
    const ratio = currentExtra > 0 ? targetExtra / currentExtra : 0;
    for (const [index, widget] of widgets.entries()) {
      const nextHeight = minimumHeights[index] + (currentHeights[index] - minimumHeights[index]) * ratio;
      setStudioInputHeight(node, widget, nextHeight);
    }
    refreshNodeSize(node, { immediate: true });
    return;
  }

  for (const widget of widgets) {
    expandStudioInputToContent(node, widget);
  }
  refreshNodeSize(node, { immediate: true });
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

function studioDefaultHeight(widget) {
  return EXTEND_FIELD_HEIGHTS[widget.name] || FIELD_HEIGHTS[widget.name] || 72;
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

function syncWidgetValue(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  widget.value = input.value;
}

function syncStudioValues(node, serialized = null) {
  const fieldNames = studioFieldNames(node);
  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (widget) {
      syncWidgetValue(widget);
    }
  }

  if (!serialized || !Array.isArray(node.widgets) || !Array.isArray(serialized.widgets_values)) {
    return;
  }
  if (isExtendNode(node)) {
    applyExtendSlotVisibility(node);
    const activeSlotsValue = JSON.stringify([...extendVisibleSlots(node)]);
    const activeSlotsWidget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
    if (activeSlotsWidget) {
      activeSlotsWidget.value = activeSlotsValue;
    }
    serialized.properties ||= {};
    serialized.properties[EXTEND_VISIBLE_SLOTS_PROPERTY] = [...parseExtendSlots(activeSlotsValue)];
  }

  for (const name of fieldNames) {
    const widgetIndex = node.widgets.findIndex((widget) => widget?.name === name);
    const widget = widgetIndex >= 0 ? node.widgets[widgetIndex] : null;
    if (widgetIndex >= 0 && widget) {
      serialized.widgets_values[widgetIndex] = widget.value ?? "";
    }
  }

  if (isExtendNode(node)) {
    const widgetIndex = node.widgets.findIndex((widget) => widget?.name === EXTEND_ACTIVE_SLOTS_WIDGET);
    const widget = widgetIndex >= 0 ? node.widgets[widgetIndex] : null;
    if (widgetIndex >= 0 && widget) {
      serialized.widgets_values[widgetIndex] = widget.value ?? JSON.stringify([...extendVisibleSlots(node)]);
    }
  }
}

function restoreInputFromWidget(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const value = String(widget?.value ?? input.value ?? "");
  if (input.value !== value) {
    input.value = value;
  }
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

function applyExecutedInputs(node, message) {
  const slotPayload = firstValue(message?.prompt_studio_slots, null);
  const payload = slotPayload || firstValue(message?.prompt_studio_inputs, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  const fieldNames = studioFieldNames(node);
  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    if (slotPayload && Object.prototype.hasOwnProperty.call(payload, name)) {
      widget.value = String(payload[name] ?? "");
      restoreInputFromWidget(widget);
      widget.__easyuseAnimaExecutedText = null;
      expandStudioInputToContent(node, widget, true);
    } else {
      widget.__easyuseAnimaExecutedText = String(payload[name] ?? "");
      expandStudioInputToContent(node, widget, true);
    }
  }
  if (slotPayload) {
    if (payload.active_slots != null) {
      writeExtendVisibleSlots(node, parseExtendSlots(payload.active_slots));
    }
    const fillNaia = findWidget(node, "fill_naia_prompt");
    if (fillNaia && payload.fill_naia_prompt != null) {
      fillNaia.value = !!payload.fill_naia_prompt;
    }
  }
  hookStudioNode(node);
}

function advancedWidget(node) {
  return findWidget(node, "advanced_fields");
}

function hideAdvancedInternalWidget(node, name) {
  const widget = findWidget(node, name);
  if (!widget) {
    return;
  }
  widget.__easyuseAnimaAdvancedHidden = true;
  widget.hidden = true;
  widget.serialize = true;
  widget.options ||= {};
  widget.options.hidden = true;
  widget.computeSize = () => [0, 0];
  widget.draw = () => {};
  const input = findInputEl(widget);
  if (input) {
    input.style.display = "none";
    input.style.pointerEvents = "none";
    input.tabIndex = -1;
  }
  setHiddenWidget(node, name, widget);
  node.setDirtyCanvas?.(true, true);
}

function hideAdvancedControlWidgets(node) {
  for (const name of ADVANCED_INTERNAL_WIDGET_NAMES) {
    hideAdvancedInternalWidget(node, name);
  }
  repairAdvancedInternalWidgetValues(node);
}

function removeAdvancedInternalInputSockets(node) {
  if (!Array.isArray(node.inputs)) {
    return;
  }
  for (let index = node.inputs.length - 1; index >= 0; index -= 1) {
    const input = node.inputs[index];
    const widgetName = input?.widget?.name || input?.name;
    if (!ADVANCED_INTERNAL_WIDGET_NAMES.has(widgetName)) {
      continue;
    }
    if (input?.link != null) {
      node.disconnectInput?.(index);
    }
    node.removeInput?.(index);
  }
}

function parseAdvancedFields(node) {
  const widget = advancedWidget(node);
  ensureAdvancedWidgetValue(node, widget);
  const sourceValue = String(widget?.value || advancedFieldsBackup(node) || "[]");
  try {
    const parsed = JSON.parse(sourceValue);
    if (Array.isArray(parsed) && parsed.length) {
      const fields = [];
      const seenNaiaPanes = new Set();
      let seenTrigger = false;
      parsed.forEach((field, index) => {
        const normalized = normalizeAdvancedField(field, index);
        if (normalized.type === "naia") {
          if (seenNaiaPanes.has(normalized.pane)) {
            return;
          }
          seenNaiaPanes.add(normalized.pane);
        }
        if (normalized.type === "trigger") {
          if (seenTrigger) {
            return;
          }
          seenTrigger = true;
          normalized.pane = "positive";
        }
        fields.push(normalized);
      });
      return fields.length ? fields : advancedDefaultFields();
    }
  } catch {
    // Fall through to default fields.
  }
  return advancedDefaultFields();
}

function writeAdvancedFields(node, fields, { render = false, syncInputs = true } = {}) {
  const widget = advancedWidget(node);
  if (!widget) {
    return;
  }
  widget.value = JSON.stringify(fields.map((field, index) => normalizeAdvancedField(field, index)));
  syncAdvancedFieldsBackup(node, widget.value);
  setAdvancedFields(node, fields);
  if (syncInputs) {
    syncAdvancedFieldInputs(node, fields, { graph: app.graph, fieldLabel: advancedFieldLabel });
  }
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  if (render) {
    renderAdvancedEditor(node);
  }
}

function applyAdvancedNaiaGeneralAutoToggle(node, fields) {
  if (!PROMPT_STUDIO_SETTINGS.naiaGeneralAboveAutoToggle || !Array.isArray(fields)) {
    return false;
  }
  const naiaIndex = fields.findIndex(
    (field) => field?.pane === "positive" && field?.type === "naia",
  );
  if (naiaIndex < 0) {
    return false;
  }
  const naiaEnabled = fields[naiaIndex]?.enabled !== false;
  let changed = false;
  for (let index = 0; index < naiaIndex; index += 1) {
    const field = fields[index];
    if (field?.pane !== "positive" || field?.type !== "general") {
      continue;
    }
    const nextEnabled = !naiaEnabled;
    if ((field.enabled !== false) !== nextEnabled) {
      field.enabled = nextEnabled;
      changed = true;
    }
  }
  return changed;
}

function advancedFieldLabel(field) {
  const base = ADVANCED_FIELD_LABELS[field.type] || "General Tags";
  const localizedBase = psText(`advanced.field.${field.type}`) || base;
  return field.label && field.label !== base && field.label !== localizedBase
    ? `${localizedBase} - ${field.label}`
    : localizedBase;
}

function setAdvancedControlValue(node, name, value) {
  const widget = findWidget(node, name);
  if (!widget || isWidgetInputLinked(node, name)) {
    return false;
  }
  widget.value = !!value;
  widget.callback?.(widget.value);
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  return true;
}

function setAdvancedWidgetValue(node, name, value) {
  const widget = findWidget(node, name);
  if (!widget) {
    return false;
  }
  widget.value = normalizeAdvancedWidgetQueueValue(name, value);
  const input = findInputEl(widget);
  if (input) {
    input.value = String(widget.value ?? "");
  }
  widget.callback?.(widget.value);
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  return true;
}

function advancedCustomResolution(node) {
  return {
    width: snapResolution32(findWidget(node, "resolution_custom_width")?.value, 1024),
    height: snapResolution32(findWidget(node, "resolution_custom_height")?.value, 1024),
  };
}

function setAdvancedCustomResolution(node, width, height, { normalize = false } = {}) {
  const nextWidth = normalize ? snapResolution32(width, 1024) : String(width || "");
  const nextHeight = normalize ? snapResolution32(height, 1024) : String(height || "");
  setAdvancedWidgetValue(node, "resolution_custom_width", nextWidth);
  setAdvancedWidgetValue(node, "resolution_custom_height", nextHeight);
  if (normalize) {
    setAdvancedWidgetValue(node, "resolution_size", advancedResolutionLabel(nextWidth, nextHeight));
  }
}

function createAdvancedControlBar(node) {
  const bar = document.createElement("div");
  bar.className = "easyuse-anima-advanced-controlbar";
  const modGuidanceGroup = createAdvancedModGuidanceGroup(node);
  const artistMixGroup = createAdvancedArtistMixGroup(node);
  if (modGuidanceGroup) {
    bar.append(modGuidanceGroup);
  }
  if (artistMixGroup) {
    bar.append(artistMixGroup);
  }
  return bar;
}

function openAdvancedSettingsPopup(node, titleKey, subtitleKey, createBody, onClose = null) {
  ensureAdvancedStyle();
  const backdrop = document.createElement("div");
  backdrop.className = "easyuse-anima-advanced-popup-backdrop";
  const dialog = document.createElement("div");
  dialog.className = "easyuse-anima-advanced-popup";
  dialog.addEventListener("pointerdown", stopAdvancedControlEvent);
  dialog.addEventListener("mousedown", stopAdvancedControlEvent);
  dialog.addEventListener("click", stopAdvancedControlEvent);
  dialog.addEventListener("keydown", stopAdvancedControlEvent);

  const header = document.createElement("header");
  const titleBox = document.createElement("div");
  const heading = document.createElement("h2");
  heading.textContent = psText(titleKey);
  const desc = document.createElement("p");
  desc.textContent = psText(subtitleKey);
  titleBox.append(heading, desc);
  const close = document.createElement("button");
  close.type = "button";
  close.className = "easyuse-anima-advanced-popup-close";
  close.textContent = psText("advanced.close");
  header.append(titleBox, close);

  const body = document.createElement("div");
  body.className = "easyuse-anima-advanced-popup-body";
  const content = createBody?.();
  if (content instanceof DocumentFragment) {
    body.append(content);
  } else if (content instanceof HTMLElement) {
    body.append(...Array.from(content.childNodes));
  }
  dialog.append(header, body);
  backdrop.append(dialog);

  const closePopup = () => {
    closeAdvancedHelpPopovers();
    backdrop.remove();
    onClose?.();
    renderAdvancedEditor(node);
  };
  close.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    closePopup();
  });
  backdrop.addEventListener("pointerdown", (event) => {
    if (event.target === backdrop) {
      closePopup();
    }
  });
  document.body.append(backdrop);
  return backdrop;
}

function createAdvancedControlGroup(node, groupId, labelKey, titleKey, summary, active, createBody) {
  const group = document.createElement("div");
  group.className = "easyuse-anima-advanced-controlgroup";
  group.classList.toggle("is-active", !!active);
  group.addEventListener("pointerdown", stopAdvancedControlEvent);
  group.addEventListener("mousedown", stopAdvancedControlEvent);
  group.addEventListener("click", stopAdvancedControlEvent);

  const header = document.createElement("button");
  header.type = "button";
  header.className = "easyuse-anima-advanced-controlgroup-header";
  header.title = psText(titleKey);
  header.textContent = psText(labelKey) || psText("advanced.settingsButton");

  const summaryEl = document.createElement("span");
  summaryEl.className = "easyuse-anima-advanced-controlgroup-summary";
  summaryEl.dataset.easyuseAnimaControlSummary = groupId;
  summaryEl.textContent = summary;

  header.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const subtitleKey = groupId === "mod_guidance"
      ? "advanced.modGuidanceSubtitle"
      : "advanced.artistMixSubtitle";
    openAdvancedSettingsPopup(node, labelKey, subtitleKey, createBody);
  });
  group.append(header, summaryEl);
  return group;
}

function createAdvancedToggleControl(node, control) {
  const widget = findWidget(node, control.name);
  if (!widget) {
    return null;
  }
  const linked = isWidgetInputLinked(node, control.name);
  const button = document.createElement("button");
  button.type = "button";
  button.className = "easyuse-anima-advanced-toggle";
  button.classList.toggle("is-on", !!widget.value);
  button.classList.toggle("is-linked", linked);
  const title = psText(control.titleKey);
  button.textContent = psText(control.labelKey);
  button.title = linked ? `${title} ${psText("advanced.linkedInputSuffix")}` : title;
  button.disabled = linked;
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const next = !widget.value;
    setAdvancedControlValue(node, control.name, next);
    button.classList.toggle("is-on", next);
    updateAdvancedSummary(node, "mod_guidance", advancedModGuidanceSummary(node));
  });
  return button;
}

function advancedModGuidanceSummary(node) {
  const positiveOn = !!findWidget(node, "use_anima_mod_guidance")?.value;
  const negativeOn = !!findWidget(node, "use_negative_anima_mod_guidance")?.value;
  return [positiveOn ? "positive" : "", negativeOn ? "negative" : ""]
    .filter(Boolean)
    .join(" + ") || psText("advanced.off");
}

function createAdvancedModGuidanceGroup(node) {
  const controls = ADVANCED_CONTROL_WIDGETS.filter(
    (control) => control.showInControlBar !== false && findWidget(node, control.name),
  );
  if (!controls.length) {
    return null;
  }
  const positiveOn = !!findWidget(node, "use_anima_mod_guidance")?.value;
  const negativeOn = !!findWidget(node, "use_negative_anima_mod_guidance")?.value;
  const summary = advancedModGuidanceSummary(node);
  return createAdvancedControlGroup(
    node,
    "mod_guidance",
    "advanced.modGuidanceGroup",
    "advanced.modGuidanceGroupTitle",
    summary,
    positiveOn || negativeOn,
    () => {
      const body = document.createElement("div");
      for (const control of controls) {
        const button = createAdvancedToggleControl(node, control);
        if (button) {
          body.append(button);
        }
      }
      return body;
    },
  );
}

function artistMixModeTitle(mode) {
  return psText(`advanced.artistMixMode.${normalizeArtistMixMode(mode)}Title`);
}


function createAdvancedControlRow(labelKey, controlEl, titleKey = null) {
  const row = document.createElement("div");
  row.className = "easyuse-anima-advanced-controlgroup-row";
  const label = document.createElement("span");
  label.className = "easyuse-anima-advanced-controlgroup-label";
  label.textContent = psText(labelKey);
  const title = titleKey ? psText(titleKey) : "";
  if (title) {
    row.title = title;
    label.title = title;
    controlEl.title = title;
  }
  row.append(label, controlEl);
  if (title) {
    const help = document.createElement("button");
    help.type = "button";
    help.className = "easyuse-anima-advanced-help";
    help.textContent = "i";
    help.title = title;
    help.setAttribute("aria-label", `${psText(labelKey)} help`);
    help.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openAdvancedHelpPopover(help, help.title || title);
    });
    row.append(help);
  }
  return row;
}

function createArtistMixNumberInput(node, name, labelKey, titleKey, min, max, step, fallback) {
  const widget = findWidget(node, name);
  if (!widget) {
    return null;
  }
  const input = document.createElement("input");
  protectAdvancedNativeControl(input);
  input.type = "number";
  input.min = String(min);
  input.max = String(max);
  input.step = String(step);
  input.value = String(clampAdvancedNumber(widget.value, fallback, min, max));
  input.setAttribute("aria-label", psText(labelKey));
  const syncValue = () => {
    const next = clampAdvancedNumber(input.value, fallback, min, max);
    input.value = String(next);
    setAdvancedWidgetValue(node, name, next);
  };
  input.addEventListener("change", syncValue);
  input.addEventListener("blur", syncValue);
  input.addEventListener("keydown", stopAdvancedControlEvent);
  return createAdvancedControlRow(labelKey, input, titleKey);
}

function createArtistMixBooleanInput(node, name, labelKey, titleKey, fallback) {
  const widget = findWidget(node, name);
  if (!widget) {
    return null;
  }
  const button = document.createElement("button");
  protectAdvancedNativeControl(button);
  button.type = "button";
  button.className = "easyuse-anima-advanced-toggle";
  const initial = widget.value ?? fallback;
  button.classList.toggle("is-on", !!initial);
  button.textContent = initial ? psText("advanced.on") : psText("advanced.off");
  button.setAttribute("aria-label", psText(labelKey));
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const next = !(widget.value ?? fallback);
    setAdvancedControlValue(node, name, next);
    button.classList.toggle("is-on", next);
    button.textContent = next ? psText("advanced.on") : psText("advanced.off");
  });
  return createAdvancedControlRow(labelKey, button, titleKey);
}

function createAdvancedArtistMixGroup(node) {
  const modeWidget = findWidget(node, "artist_mix_mode");
  if (!modeWidget) {
    return null;
  }
  const modeValue = normalizeArtistMixMode(modeWidget.value);
  const active = modeValue !== "off";
  return createAdvancedControlGroup(
    node,
    "artist_mix",
    "advanced.artistMix",
    "advanced.artistMixTitle",
    modeValue,
    active,
    () => {
      const body = document.createElement("div");
      const modeSelect = document.createElement("select");
      protectAdvancedNativeControl(modeSelect);
      modeSelect.setAttribute("aria-label", psText("advanced.artistMixMode"));
      modeSelect.title = artistMixModeTitle(modeValue);
      for (const mode of ARTIST_MIX_MODES) {
        const option = document.createElement("option");
        option.value = mode;
        option.textContent = mode;
        option.selected = mode === modeValue;
        option.title = artistMixModeTitle(mode);
        modeSelect.append(option);
      }
      const modeRow = createAdvancedControlRow("advanced.artistMixMode", modeSelect, `advanced.artistMixMode.${modeValue}Title`);
      modeSelect.addEventListener("change", () => {
        const nextMode = normalizeArtistMixMode(modeSelect.value);
        setAdvancedWidgetValue(node, "artist_mix_mode", nextMode);
        const nextTitle = artistMixModeTitle(nextMode);
        modeSelect.title = nextTitle;
        modeRow.title = nextTitle;
        modeRow.querySelector(".easyuse-anima-advanced-controlgroup-label")?.setAttribute("title", nextTitle);
        modeRow.querySelector(".easyuse-anima-advanced-help")?.setAttribute("title", nextTitle);
        updateAdvancedSummary(node, "artist_mix", nextMode);
      });
      body.append(modeRow);
      const syntaxNote = document.createElement("div");
      syntaxNote.className = "easyuse-anima-advanced-popup-note";
      syntaxNote.textContent = psText("advanced.artistMixSyntaxTitle");
      body.append(syntaxNote);
      const startRow = createArtistMixNumberInput(
        node,
        "artist_mix_start_percent",
        "advanced.artistMixStart",
        "advanced.artistMixStartTitle",
        0,
        1,
        0.01,
        0.5,
      );
      const strengthRow = createArtistMixNumberInput(
        node,
        "artist_mix_strength_scale",
        "advanced.artistMixStrength",
        "advanced.artistMixStrengthTitle",
        0,
        5,
        0.01,
        1,
      );
      const styleGainRow = createArtistMixNumberInput(
        node,
        "artist_mix_style_gain",
        "advanced.artistMixStyleGain",
        "advanced.artistMixStyleGainTitle",
        0,
        3,
        0.01,
        1.35,
      );
      const rmsScaleCapRow = createArtistMixNumberInput(
        node,
        "artist_mix_rms_scale_cap",
        "advanced.artistMixRmsCap",
        "advanced.artistMixRmsCapTitle",
        1,
        5,
        0.01,
        2,
      );
      const exactTopKRow = createArtistMixNumberInput(
        node,
        "artist_mix_exact_top_k",
        "advanced.artistMixTopK",
        "advanced.artistMixTopKTitle",
        0,
        64,
        1,
        4,
      );
      const clusterCountRow = createArtistMixNumberInput(
        node,
        "artist_mix_cluster_count",
        "advanced.artistMixClusters",
        "advanced.artistMixClustersTitle",
        1,
        32,
        1,
        4,
      );
      const dominantRow = createArtistMixBooleanInput(
        node,
        "artist_mix_dominant_isolation",
        "advanced.artistMixDominant",
        "advanced.artistMixDominantTitle",
        true,
      );
      const dominantThresholdRow = createArtistMixNumberInput(
        node,
        "artist_mix_dominant_threshold",
        "advanced.artistMixDominantThreshold",
        "advanced.artistMixDominantThresholdTitle",
        0,
        1,
        0.01,
        0.25,
      );
      if (startRow) {
        body.append(startRow);
      }
      if (strengthRow) {
        body.append(strengthRow);
      }
      for (const row of [styleGainRow, rmsScaleCapRow, exactTopKRow, clusterCountRow, dominantRow, dominantThresholdRow]) {
        if (row) {
          body.append(row);
        }
      }
      return body;
    },
  );
}

function normalizeAdvancedWildcardMode(value) {
  return ADVANCED_WILDCARD_MODES.includes(String(value || ""))
    ? String(value)
    : ADVANCED_WILDCARD_DEFAULT_MODE;
}

function normalizeAdvancedSeedControl(value) {
  return ADVANCED_WILDCARD_SEED_CONTROLS.includes(String(value || ""))
    ? String(value)
    : "fixed";
}

function advancedWildcardSummary(node) {
  const modeWidget = findWidget(node, "wildcard_mode");
  const seedWidget = findWidget(node, "wildcard_seed");
  const controlWidget = findWidget(node, "wildcard_seed_after_generate");
  const modeValue = normalizeAdvancedWildcardMode(modeWidget?.value);
  const controlValue = modeValue === "순차"
    ? "increment"
    : normalizeAdvancedSeedControl(controlWidget?.value);
  return `${modeValue} · seed ${Math.max(0, Math.trunc(Number(seedWidget?.value) || 0))} · ${controlValue}`;
}

function createAdvancedSummaryButtonRow(className, buttonLabelKey, titleKey, summaryId, summaryText, onClick) {
  const row = document.createElement("div");
  row.className = className;
  row.title = psText(titleKey);
  const button = document.createElement("button");
  button.type = "button";
  button.className = "easyuse-anima-advanced-popup-button";
  button.textContent = psText(buttonLabelKey);
  button.title = psText(titleKey);
  const summary = document.createElement("span");
  summary.className = "easyuse-anima-advanced-inline-summary";
  summary.dataset.easyuseAnimaControlSummary = summaryId;
  summary.textContent = summaryText;
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    onClick?.();
  });
  row.append(button, summary);
  return row;
}

function createAdvancedWildcardSettingsBody(node) {
  const modeWidget = findWidget(node, "wildcard_mode");
  const seedWidget = findWidget(node, "wildcard_seed");
  const controlWidget = findWidget(node, "wildcard_seed_after_generate");
  if (!modeWidget || !seedWidget || !controlWidget) {
    return document.createDocumentFragment();
  }

  const body = document.createElement("div");

  const modeSelect = document.createElement("select");
  protectAdvancedNativeControl(modeSelect);
  modeSelect.setAttribute("aria-label", psText("advanced.wildcard"));
  modeSelect.title = psText("advanced.wildcardModeTitle");
  const modeValue = normalizeAdvancedWildcardMode(modeWidget.value);
  for (const mode of ADVANCED_WILDCARD_MODES) {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = mode;
    option.selected = mode === modeValue;
    modeSelect.append(option);
  }

  const seedInput = document.createElement("input");
  protectAdvancedNativeControl(seedInput);
  seedInput.type = "number";
  seedInput.min = "0";
  seedInput.step = "1";
  seedInput.value = String(seedWidget.value ?? "0");
  seedInput.setAttribute("aria-label", psText("advanced.wildcardSeed"));
  seedInput.title = psText("advanced.wildcardSeedTitle");

  const controlSelect = document.createElement("select");
  protectAdvancedNativeControl(controlSelect);
  controlSelect.setAttribute("aria-label", psText("advanced.wildcardSeedControl"));
  controlSelect.title = psText("advanced.wildcardSeedControlTitle");
  const controlValue = modeValue === "순차"
    ? "increment"
    : normalizeAdvancedSeedControl(controlWidget.value);
  for (const control of ADVANCED_WILDCARD_SEED_CONTROLS) {
    const option = document.createElement("option");
    option.value = control;
    option.textContent = control;
    option.selected = control === controlValue;
    controlSelect.append(option);
  }
  controlSelect.disabled = modeValue === "순차";

  const refreshSummary = () => updateAdvancedSummary(node, "wildcard", advancedWildcardSummary(node));
  const syncMode = () => {
    const nextMode = normalizeAdvancedWildcardMode(modeSelect.value);
    setAdvancedWidgetValue(node, "wildcard_mode", nextMode);
    if (nextMode === "순차") {
      setAdvancedWidgetValue(node, "wildcard_seed_after_generate", "increment");
      controlSelect.value = "increment";
    }
    controlSelect.disabled = nextMode === "순차";
    refreshSummary();
  };
  const syncSeed = () => {
    const seed = Math.max(0, Math.trunc(Number(seedInput.value) || 0));
    seedInput.value = String(seed);
    setAdvancedWidgetValue(node, "wildcard_seed", seed);
    refreshSummary();
  };
  const syncControl = () => {
    setAdvancedWidgetValue(node, "wildcard_seed_after_generate", normalizeAdvancedSeedControl(controlSelect.value));
    refreshSummary();
  };

  modeSelect.addEventListener("change", syncMode);
  seedInput.addEventListener("change", syncSeed);
  seedInput.addEventListener("blur", syncSeed);
  controlSelect.addEventListener("change", syncControl);

  body.append(
    createAdvancedControlRow("advanced.wildcard", modeSelect, "advanced.wildcardModeTitle"),
    createAdvancedControlRow("advanced.wildcardSeed", seedInput, "advanced.wildcardSeedTitle"),
    createAdvancedControlRow("advanced.wildcardSeedControl", controlSelect, "advanced.wildcardSeedControlTitle"),
  );
  return body;
}

function createAdvancedWildcardBar(node) {
  const modeWidget = findWidget(node, "wildcard_mode");
  const seedWidget = findWidget(node, "wildcard_seed");
  const controlWidget = findWidget(node, "wildcard_seed_after_generate");
  if (!modeWidget || !seedWidget || !controlWidget) {
    return document.createDocumentFragment();
  }
  return createAdvancedSummaryButtonRow(
    "easyuse-anima-advanced-wildcardbar",
    "advanced.wildcardSeed",
    "advanced.wildcardTitle",
    "wildcard",
    advancedWildcardSummary(node),
    () => openAdvancedSettingsPopup(
      node,
      "advanced.wildcardSeed",
      "advanced.wildcardTitle",
      () => createAdvancedWildcardSettingsBody(node),
    ),
  );
}

function advancedResolutionSummary(node) {
  const bucketWidget = findWidget(node, "resolution_bucket");
  const sizeWidget = findWidget(node, "resolution_size");
  const bucketValue = normalizeAdvancedResolutionBucket(bucketWidget?.value);
  const customResolution = advancedCustomResolution(node);
  const sizeValue = bucketValue === CUSTOM_ADVANCED_RESOLUTION_BUCKET || bucketValue === NAIA_ADVANCED_RESOLUTION_BUCKET
    ? advancedResolutionLabel(customResolution.width, customResolution.height)
    : normalizeAdvancedResolutionSize(bucketValue, sizeWidget?.value);
  return `${bucketValue} · ${sizeValue}`;
}

function createAdvancedResolutionSettingsBody(node) {
  const bucketWidget = findWidget(node, "resolution_bucket");
  const sizeWidget = findWidget(node, "resolution_size");
  if (!bucketWidget || !sizeWidget) {
    return document.createDocumentFragment();
  }

  const bucketValue = normalizeAdvancedResolutionBucket(bucketWidget.value);
  const customResolution = advancedCustomResolution(node);
  const sizeValue = bucketValue === CUSTOM_ADVANCED_RESOLUTION_BUCKET || bucketValue === NAIA_ADVANCED_RESOLUTION_BUCKET
    ? advancedResolutionLabel(customResolution.width, customResolution.height)
    : normalizeAdvancedResolutionSize(bucketValue, sizeWidget.value);
  if (bucketWidget.value !== bucketValue) {
    setAdvancedWidgetValue(node, "resolution_bucket", bucketValue);
  }
  if (sizeWidget.value !== sizeValue) {
    setAdvancedWidgetValue(node, "resolution_size", sizeValue);
  }

  const body = document.createElement("div");

  const bucketSelect = document.createElement("select");
  protectAdvancedNativeControl(bucketSelect);
  bucketSelect.setAttribute("aria-label", psText("advanced.resolutionBucket"));
  bucketSelect.title = psText("advanced.resolutionBucketTitle");
  for (const bucket of Object.keys(ADVANCED_RESOLUTION_BUCKETS)) {
    const option = document.createElement("option");
    option.value = bucket;
    option.textContent = bucket;
    option.selected = bucket === bucketValue;
    bucketSelect.append(option);
  }
  const naiaOption = document.createElement("option");
  naiaOption.value = NAIA_ADVANCED_RESOLUTION_BUCKET;
  naiaOption.textContent = NAIA_ADVANCED_RESOLUTION_BUCKET;
  naiaOption.selected = bucketValue === NAIA_ADVANCED_RESOLUTION_BUCKET;
  bucketSelect.append(naiaOption);
  const customOption = document.createElement("option");
  customOption.value = CUSTOM_ADVANCED_RESOLUTION_BUCKET;
  customOption.textContent = CUSTOM_ADVANCED_RESOLUTION_BUCKET;
  customOption.selected = bucketValue === CUSTOM_ADVANCED_RESOLUTION_BUCKET;
  bucketSelect.append(customOption);

  const valueBox = document.createElement("div");
  const refreshSummary = () => updateAdvancedSummary(node, "resolution", advancedResolutionSummary(node));
  const renderPresetSelect = (bucket, selected) => {
    valueBox.innerHTML = "";
    const sizeSelect = document.createElement("select");
    protectAdvancedNativeControl(sizeSelect);
    sizeSelect.setAttribute("aria-label", psText("advanced.resolutionSize"));
    sizeSelect.title = psText("advanced.resolutionSizeTitle");
    for (const label of advancedResolutionOptions(bucket)) {
      const option = document.createElement("option");
      option.value = label;
      option.textContent = label;
      option.selected = label === selected;
      sizeSelect.append(option);
    }
    sizeSelect.addEventListener("change", () => {
      setAdvancedWidgetValue(node, "resolution_size", normalizeAdvancedResolutionSize(bucketSelect.value, sizeSelect.value));
      refreshSummary();
      scheduleAdvancedLayout(node, "settings");
    });
    valueBox.append(sizeSelect);
  };
  const renderCustomInputs = () => {
    valueBox.innerHTML = "";
    valueBox.className = "easyuse-anima-advanced-resolution-custom";
    const widthInput = document.createElement("input");
    protectAdvancedNativeControl(widthInput);
    widthInput.type = "number";
    widthInput.min = "32";
    widthInput.step = "32";
    widthInput.value = String(advancedCustomResolution(node).width);
    widthInput.setAttribute("aria-label", psText("advanced.customWidth"));
    widthInput.title = psText("advanced.customWidthTitle");
    const separator = document.createElement("span");
    separator.textContent = "×";
    const heightInput = document.createElement("input");
    protectAdvancedNativeControl(heightInput);
    heightInput.type = "number";
    heightInput.min = "32";
    heightInput.step = "32";
    heightInput.value = String(advancedCustomResolution(node).height);
    heightInput.setAttribute("aria-label", psText("advanced.customHeight"));
    heightInput.title = psText("advanced.customHeightTitle");
    const syncRaw = () => {
      setAdvancedCustomResolution(node, widthInput.value, heightInput.value);
      refreshSummary();
    };
    const normalize = () => {
      const width = snapResolution32(widthInput.value, 1024);
      const height = snapResolution32(heightInput.value, 1024);
      widthInput.value = String(width);
      heightInput.value = String(height);
      setAdvancedCustomResolution(node, width, height, { normalize: true });
      refreshSummary();
    };
    widthInput.addEventListener("input", syncRaw);
    heightInput.addEventListener("input", syncRaw);
    widthInput.addEventListener("change", normalize);
    heightInput.addEventListener("change", normalize);
    widthInput.addEventListener("blur", normalize);
    heightInput.addEventListener("blur", normalize);
    valueBox.append(widthInput, separator, heightInput);
    setAdvancedCustomResolution(node, widthInput.value, heightInput.value, { normalize: true });
  };
  const renderNaiaResolution = () => {
    valueBox.innerHTML = "";
    valueBox.className = "easyuse-anima-advanced-resolution-custom";
    const current = advancedCustomResolution(node);
    const label = document.createElement("span");
    label.textContent = advancedResolutionLabel(current.width, current.height);
    label.title = psText("advanced.naiaResolutionTitle");
    valueBox.append(label);
    setAdvancedWidgetValue(node, "resolution_size", advancedResolutionLabel(current.width, current.height));
  };
  const fillSizeOptions = (bucket, selected) => {
    valueBox.className = "";
    if (bucket === NAIA_ADVANCED_RESOLUTION_BUCKET) {
      renderNaiaResolution();
      return;
    }
    if (bucket === CUSTOM_ADVANCED_RESOLUTION_BUCKET) {
      renderCustomInputs();
      return;
    }
    renderPresetSelect(bucket, selected);
  };
  fillSizeOptions(bucketValue, sizeValue);

  bucketSelect.addEventListener("change", () => {
    const nextBucket = normalizeAdvancedResolutionBucket(bucketSelect.value);
    const nextSize = nextBucket === CUSTOM_ADVANCED_RESOLUTION_BUCKET || nextBucket === NAIA_ADVANCED_RESOLUTION_BUCKET
      ? advancedResolutionLabel(advancedCustomResolution(node).width, advancedCustomResolution(node).height)
      : normalizeAdvancedResolutionSize(nextBucket, sizeWidget.value);
    setAdvancedWidgetValue(node, "resolution_bucket", nextBucket);
    setAdvancedWidgetValue(node, "resolution_size", nextSize);
    if (nextBucket === NAIA_ADVANCED_RESOLUTION_BUCKET) {
      setAdvancedControlValue(node, "consume_naia_on_queue", true);
      setAdvancedControlValue(node, "use_naia", true);
    }
    fillSizeOptions(nextBucket, nextSize);
    refreshSummary();
    scheduleAdvancedLayout(node, "settings");
    scheduleAdvancedHighlights(node, { classify: false });
  });

  body.append(
    createAdvancedControlRow("advanced.resolutionBucket", bucketSelect, "advanced.resolutionBucketTitle"),
    createAdvancedControlRow("advanced.resolutionSize", valueBox, "advanced.resolutionSizeTitle"),
  );
  return body;
}

function createAdvancedResolutionBar(node) {
  const bucketWidget = findWidget(node, "resolution_bucket");
  const sizeWidget = findWidget(node, "resolution_size");
  if (!bucketWidget || !sizeWidget) {
    return document.createDocumentFragment();
  }
  return createAdvancedSummaryButtonRow(
    "easyuse-anima-advanced-resolutionbar",
    "advanced.resolutionBucket",
    "advanced.resolutionTitle",
    "resolution",
    advancedResolutionSummary(node),
    () => openAdvancedSettingsPopup(
      node,
      "advanced.resolutionBucket",
      "advanced.resolutionTitle",
      () => createAdvancedResolutionSettingsBody(node),
    ),
  );
}

function advancedFieldByTextarea(node, textarea) {
  const id = String(textarea?.dataset?.easyuseAnimaAdvancedFieldId || "");
  if (!id) {
    return null;
  }
  return (getAdvancedFields(node) || parseAdvancedFields(node))
    .find((field) => field.id === id) || null;
}

function setAdvancedTextareaHeight(node, textarea, height, options = {}) {
  const requiredHeight = Math.max(
    advancedTextareaMinimumHeight(textarea),
    advancedTextareaContentHeight(textarea),
  );
  const nextHeight = Math.max(requiredHeight, Math.round(Number(height) || 0));
  textarea.style.minHeight = `${requiredHeight}px`;
  textarea.style.height = `${nextHeight}px`;
  textarea.style.overflowY = "hidden";
  let field = null;
  if (options.syncField !== false || options.refreshHighlight !== false) {
    field = advancedFieldByTextarea(node, textarea);
  }
  if (options.syncField !== false && field) {
    field.height = nextHeight;
  }
  if (options.refreshHighlight !== false) {
    updateAdvancedFieldHighlight(node, field, textarea);
  }
  return nextHeight;
}

function clearAdvancedResizeEndListeners(node) {
  const handler = node?.__easyuseAnimaAdvancedResizeEndHandler;
  if (!handler) {
    return;
  }
  document.removeEventListener("pointerup", handler, true);
  document.removeEventListener("pointercancel", handler, true);
  document.removeEventListener("mouseup", handler, true);
  node.__easyuseAnimaAdvancedResizeEndHandler = null;
}

function finalizeAdvancedResize(node) {
  if (node) {
    clearTimeout(node.__easyuseAnimaAdvancedResizeFinalizeTimer);
    node.__easyuseAnimaAdvancedResizeFinalizeTimer = null;
    clearAdvancedResizeEndListeners(node);
  }
  if (
    !node
    || !node.graph
    || !getAdvancedEditorElement(node)?.isConnected
  ) {
    return;
  }
  updateAdvancedEditorWidth(node);
  clampAdvancedNodeToMinimumHeight(node);
  scheduleAdvancedLayout(node, "resize");
}

function installAdvancedResizeEndListeners(node) {
  if (!node || node.__easyuseAnimaAdvancedResizeEndHandler) {
    return;
  }
  const handler = () => finalizeAdvancedResize(node);
  node.__easyuseAnimaAdvancedResizeEndHandler = handler;
  document.addEventListener("pointerup", handler, true);
  document.addEventListener("pointercancel", handler, true);
  document.addEventListener("mouseup", handler, true);
}

function scheduleAdvancedResizeFinalize(node) {
  if (!getAdvancedEditorElement(node)?.isConnected) {
    finalizeAdvancedResize(node);
    return;
  }
  installAdvancedResizeEndListeners(node);
  clearTimeout(node.__easyuseAnimaAdvancedResizeFinalizeTimer);
  node.__easyuseAnimaAdvancedResizeFinalizeTimer = setTimeout(() => {
    finalizeAdvancedResize(node);
  }, 120);
}

function applyAdvancedLayout(node, reason = "layout") {
  const editor = getAdvancedEditorElement(node);
  if (!editor || !node.size) {
    return;
  }
  if (node.__easyuseAnimaApplyingLayout) {
    return;
  }

  node.__easyuseAnimaApplyingLayout = true;
  try {
    updateAdvancedEditorWidth(node);

    const currentWidth = Number(node.size[0]) || 360;
    const currentHeight = Number(node.size[1]) || 0;
    const minimumHeight = advancedMinimumNodeHeight(node);
    const widgetHeight = advancedEditorWidgetHeight(node);
    editor.style.height = `${widgetHeight}px`;
    editor.style.maxHeight = `${widgetHeight}px`;
    node.__easyuseAnimaAdvancedWidgetHeight = widgetHeight;
    node.__easyuseAnimaAdvancedLastEditorHeight = widgetHeight;
    node.__easyuseAnimaAdvancedLastLayoutReason = reason;

    if (typeof node.setSize === "function" && currentHeight < minimumHeight - 1) {
      node.setSize([currentWidth, minimumHeight]);
    }

    app.graph?.setDirtyCanvas?.(true, true);
    requestAnimationFrame(() => app.graph?.setDirtyCanvas?.(true, true));
  } finally {
    node.__easyuseAnimaApplyingLayout = false;
  }
  scheduleAdvancedHighlights(node, { classify: reason !== "resize" });
}

const ADVANCED_LAYOUT_REASON_PRIORITY = {
  layout: 0,
  render: 1,
  textarea: 1,
  connections: 1,
  executed: 1,
  settings: 1,
  resize: 3,
};

function advancedLayoutReasonPriority(reason) {
  return ADVANCED_LAYOUT_REASON_PRIORITY[reason] ?? 0;
}

function scheduleAdvancedLayout(node, reason = "layout") {
  if (!getAdvancedEditorElement(node)) {
    return;
  }
  updateAdvancedEditorWidth(node);
  const currentReason = node.__easyuseAnimaAdvancedLayoutReason || "layout";
  if (
    !node.__easyuseAnimaAdvancedLayoutScheduled
    || advancedLayoutReasonPriority(reason) >= advancedLayoutReasonPriority(currentReason)
  ) {
    node.__easyuseAnimaAdvancedLayoutReason = reason;
  }
  if (node.__easyuseAnimaAdvancedLayoutScheduled) {
    return;
  }
  node.__easyuseAnimaAdvancedLayoutScheduled = true;
  requestAnimationFrame(() => {
    node.__easyuseAnimaAdvancedLayoutScheduled = false;
    const layoutReason = node.__easyuseAnimaAdvancedLayoutReason || reason;
    node.__easyuseAnimaAdvancedLayoutReason = null;
    applyAdvancedLayout(node, layoutReason);
  });
}

function createAdvancedFieldElement(node, field) {
  const fields = getAdvancedFields(node) || parseAdvancedFields(node);
  const globalIndex = fields.findIndex((item) => item.id === field.id);
  const samePane = fields.filter((item) => item.pane === field.pane);
  const paneIndex = samePane.findIndex((item) => item.id === field.id);
  const block = document.createElement("div");
  block.className = "easyuse-anima-advanced-field";
  block.classList.toggle("is-naia", field.type === "naia");
  block.classList.toggle("is-trigger", field.type === "trigger");
  block.classList.toggle("is-disabled", field.enabled === false);

  const header = document.createElement("div");
  header.className = "easyuse-anima-field-header";
  const label = document.createElement("div");
  label.className = "easyuse-anima-field-label";
  label.textContent = `${advancedFieldIndexLabel(fields, field)}. ${advancedFieldLabel(field)}`;
  const tools = document.createElement("div");
  tools.className = "easyuse-anima-field-tools";

  const move = (direction) => {
    const currentFields = getAdvancedFields(node) || parseAdvancedFields(node);
    if (moveAdvancedFieldInPane(currentFields, field, direction)) {
      writeAdvancedFields(node, currentFields, { render: true });
    }
  };

  const addTool = (text, title, callback, disabled = false, active = false) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text;
    button.title = title;
    button.disabled = disabled;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (!button.disabled) {
        callback();
      }
    });
    if (active) {
      button.classList.add("is-on");
    }
    tools.append(button);
    return button;
  };

  const toggleButton = addTool(
    field.enabled === false ? psText("advanced.off") : psText("advanced.on"),
    psText("advanced.enableFieldTitle"),
    () => {
      field.enabled = field.enabled === false;
      writeAdvancedFields(node, fields, { render: true });
    },
    false,
    field.enabled !== false,
  );
  toggleButton.classList.toggle("is-on", field.enabled !== false);
  if (field.type === "trigger") {
    const pinButton = addTool(
      field.pin === false ? psText("advanced.autoOrder") : psText("advanced.pinned"),
      field.pin === false ? psText("advanced.autoOrderTitle") : psText("advanced.pinnedTitle"),
      () => {
        field.pin = field.pin === false;
        writeAdvancedFields(node, fields, { render: true });
      },
      false,
      field.pin !== false,
    );
    pinButton.classList.add("easyuse-anima-trigger-pin");
    pinButton.classList.toggle("is-on", field.pin !== false);
  }
  if (field.type === "naia") {
    const useNaiaWidget = findWidget(node, "use_naia");
    const linkedUseNaia = isWidgetInputLinked(node, "use_naia");
    const fillButton = addTool(psText("advanced.fillFromNaia"), psText("advanced.fillFromNaiaTitle"), () => {
      const currentFields = getAdvancedFields(node) || parseAdvancedFields(node);
      const target = currentFields.find((item) => item.id === field.id);
      if (target?.enabled === false) {
        return;
      }
      const nextValue = !findWidget(node, "use_naia")?.value;
      setAdvancedControlValue(node, "consume_naia_on_queue", true);
      setAdvancedControlValue(node, "use_naia", nextValue);
      applyAdvancedNaiaGeneralAutoToggle(node, currentFields);
      writeAdvancedFields(node, currentFields, { render: true });
    }, linkedUseNaia || field.enabled === false, field.enabled !== false && !!useNaiaWidget?.value);
    fillButton.classList.add("easyuse-anima-naia-fill");
    fillButton.classList.toggle("is-on", field.enabled !== false && !!useNaiaWidget?.value);
    fillButton.classList.toggle("is-linked", linkedUseNaia);
  }
  addTool("↑", psText("advanced.moveUp"), () => move(-1), paneIndex <= 0);
  addTool("↓", psText("advanced.moveDown"), () => move(1), paneIndex >= samePane.length - 1);
  addTool("X", psText("advanced.deleteField"), () => {
    const currentFields = getAdvancedFields(node) || parseAdvancedFields(node);
    currentFields.splice(globalIndex, 1);
    writeAdvancedFields(node, currentFields, { render: true });
  });

  const textarea = document.createElement("textarea");
  const linked = advancedFieldInputLinked(node, field);
  const inputName = advancedFieldInputName(field);
  textarea.value = advancedFieldDisplayText(node, field);
  textarea.style.height = `${field.height || 72}px`;
  textarea.style.overflowY = "hidden";
  textarea.placeholder = advancedFieldTextareaPlaceholder(field, psText);
  textarea.readOnly = false;
  textarea.classList.toggle("is-linked", linked);
  textarea.title = advancedFieldTextareaTitle(field, linked, psText);
  textarea.dataset.easyuseAnimaAdvancedFieldId = field.id;
  const updateFieldHighlight = debounce(() => {
    scheduleAdvancedFieldHighlight(node, field, textarea);
  }, 180);
  const persistTextareaHeight = (height, mode = field.heightMode || "auto") => {
    const previousHeight = Math.round(Number(field.height) || 0);
    const previousMode = field.heightMode || "auto";
    const nextHeight = setAdvancedTextareaHeight(node, textarea, height);
    field.height = nextHeight;
    field.heightMode = mode === "manual" ? "manual" : "auto";
    writeAdvancedFields(node, fields, { syncInputs: false });
    updateAdvancedFieldHighlight(node, field, textarea);
    updateFieldHighlight();
    if (Math.abs(nextHeight - previousHeight) > 1 || field.heightMode !== previousMode) {
      scheduleAdvancedLayout(node, "textarea");
    } else {
      requestOverlaySync(textarea);
    }
  };
  const syncHeight = () => {
    if (field.heightMode === "manual") {
      persistTextareaHeight(advancedTextareaCurrentHeight(textarea), "manual");
      return;
    }
    textarea.style.height = "auto";
    textarea.style.overflowY = "hidden";
    const height = Math.max(
      advancedTextareaMinimumHeight(textarea),
      advancedTextareaContentHeight(textarea),
    );
    field.heightMode = "auto";
    persistTextareaHeight(height, "auto");
  };
  const rememberTextareaResizeStart = () => rememberAdvancedTextareaResizeStart(textarea);
  const captureTextareaManualResize = () => {
    const { changed, currentHeight } = captureAdvancedTextareaManualResize(textarea);
    if (!changed) {
      updateAdvancedFieldHighlight(node, field, textarea);
      return;
    }
    persistTextareaHeight(currentHeight, "manual");
  };
  textarea.addEventListener("mousedown", rememberTextareaResizeStart);
  textarea.addEventListener("pointerdown", rememberTextareaResizeStart);
  textarea.addEventListener("mouseup", captureTextareaManualResize);
  textarea.addEventListener("pointerup", captureTextareaManualResize);
  textarea.addEventListener("input", () => {
    syncAdvancedTextareaLinkedInputValue(node, inputName, textarea.value, linked);
    field.text = textarea.value;
    updateFieldHighlight();
    syncHeight();
  });
  textarea.addEventListener("change", () => {
    updateFieldHighlight();
    syncHeight();
  });
  registerAdvancedAutocompleteInput(node, field, textarea);
  requestAnimationFrame(() => {
    const nextHeight = setAdvancedTextareaHeight(node, textarea, field.height || 72, {
      syncField: false,
      refreshHighlight: false,
    });
    if (nextHeight !== field.height) {
      field.height = nextHeight;
      writeAdvancedFields(node, fields, { syncInputs: false });
    }
    updateAdvancedFieldHighlight(node, field, textarea);
    updateFieldHighlight();
    scheduleAdvancedLayout(node, "render");
  });

  header.append(label, tools);
  block.append(header, textarea);
  return block;
}

function addAdvancedField(node, pane, type) {
  const fields = getAdvancedFields(node) || parseAdvancedFields(node);
  if (type === "naia" && hasAdvancedNaia(fields, pane)) {
    return;
  }
  if (type === "trigger" && hasPositiveTrigger(fields)) {
    return;
  }
  const nextId = `${pane}_${type}_${Date.now().toString(36)}`;
  fields.push({
    id: nextId,
    pane,
    type,
    label: ADVANCED_FIELD_LABELS[type] || "General Tags",
    text: "",
    height: type === "general" || type === "naia" ? 120 : 72,
    enabled: true,
  });
  if (type === "naia") {
    setAdvancedControlValue(node, "consume_naia_on_queue", true);
    setAdvancedControlValue(node, "use_naia", true);
  }
  writeAdvancedFields(node, fields, { render: true });
}

function createAdvancedPane(node, pane, titleKey) {
  const section = document.createElement("section");
  section.className = "easyuse-anima-advanced-pane";

  const header = document.createElement("div");
  header.className = "easyuse-anima-advanced-pane-title";
  const heading = document.createElement("span");
  heading.textContent = psText(titleKey);
  const actions = document.createElement("div");
  actions.className = "easyuse-anima-advanced-actions";
  const addButton = (type, label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    const currentFields = getAdvancedFields(node) || parseAdvancedFields(node);
    button.disabled = (type === "naia" && hasAdvancedNaia(currentFields, pane))
      || (type === "trigger" && hasPositiveTrigger(currentFields));
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      addAdvancedField(node, pane, type);
    });
    actions.append(button);
  };
  addButton("quality", psText("advanced.add.quality"));
  addButton("artist", psText("advanced.add.artist"));
  if (pane === "positive") {
    addButton("trigger", psText("advanced.add.trigger"));
  }
  addButton("general", psText("advanced.add.general"));
  addButton("naia", psText("advanced.add.naia"));
  header.append(heading, actions);
  section.append(header);

  const fields = advancedPaneFields(getAdvancedFields(node) || parseAdvancedFields(node), pane);
  if (!fields.length) {
    const empty = document.createElement("div");
    empty.className = "easyuse-anima-empty-pane";
    empty.textContent = psText("advanced.noFields");
    section.append(empty);
  } else {
    for (const field of fields) {
      section.append(createAdvancedFieldElement(node, field));
    }
  }
  return section;
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
  panes.append(
    createAdvancedPane(node, "positive", "advanced.positivePrompt"),
    createAdvancedPane(node, "negative", "advanced.negativePrompt"),
  );
  editor.append(
    createAdvancedControlBar(node),
    createAdvancedWildcardBar(node),
    createAdvancedResolutionBar(node),
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

function syncAdvancedValues(node, serialized = null) {
  repairAdvancedInternalWidgetValues(node);
  const fields = collectAdvancedEditorFields(node, getAdvancedFields(node) || parseAdvancedFields(node));
  writeAdvancedFields(node, fields, { syncInputs: false });
  if (!serialized || !Array.isArray(node.widgets) || !Array.isArray(serialized.widgets_values)) {
    return;
  }
  const fieldsValue = advancedWidget(node)?.value || JSON.stringify(fields);
  syncAdvancedFieldsBackup(node, fieldsValue);
  serialized.properties ||= {};
  serialized.properties[ADVANCED_FIELDS_PROPERTY] = fieldsValue;

  for (const name of Object.keys(ADVANCED_WIDGET_INDEX)) {
    const index = ADVANCED_WIDGET_INDEX[name];
    const widget = findWidget(node, name);
    if (name !== "advanced_fields" && !widget) {
      continue;
    }
    while (serialized.widgets_values.length <= index) {
      serialized.widgets_values.push(null);
    }
    if (name === "advanced_fields") {
      serialized.widgets_values[index] = fieldsValue;
    } else if (widget) {
      const value = normalizeAdvancedWidgetQueueValue(name, widget.value);
      widget.value = value;
      serialized.widgets_values[index] = value;
    }
  }
}

function applyAdvancedExecutedInputs(node, message) {
  const payload = firstValue(message?.prompt_studio_advanced, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  node.__easyuseAnimaAdvancedFieldInputValues =
    payload.field_inputs && typeof payload.field_inputs === "object" ? payload.field_inputs : {};
  const widget = advancedWidget(node);
  if (widget && payload.advanced_fields != null) {
    widget.value = String(payload.advanced_fields);
    syncAdvancedFieldsBackup(node, widget.value);
  }
  const fields = parseAdvancedFields(node);
  if (mergeAdvancedFieldInputValues(node, fields, node.__easyuseAnimaAdvancedFieldInputValues)) {
    writeAdvancedFields(node, fields, { syncInputs: false });
  } else {
    setAdvancedFields(node, fields);
  }
  const useNaia = findWidget(node, "use_naia");
  if (useNaia && payload.use_naia != null) {
    useNaia.value = !!payload.use_naia;
  }
  for (const name of ["resolution_bucket", "resolution_size", "resolution_custom_width", "resolution_custom_height"]) {
    const widget = findWidget(node, name);
    if (widget && payload[name] != null) {
      widget.value = payload[name];
    }
  }
  for (const name of ["wildcard_mode", "wildcard_seed", "wildcard_seed_after_generate"]) {
    const widget = findWidget(node, name);
    if (widget && payload[name] != null) {
      widget.value = payload[name];
    }
  }
  for (const name of [
    "artist_mix_mode",
    "artist_mix_start_percent",
    "artist_mix_strength_scale",
    "artist_mix_style_gain",
    "artist_mix_rms_scale_cap",
    "artist_mix_exact_top_k",
    "artist_mix_cluster_count",
    "artist_mix_dominant_isolation",
    "artist_mix_dominant_threshold",
  ]) {
    const widget = findWidget(node, name);
    if (widget && payload[name] != null) {
      widget.value = payload[name];
    }
  }
  renderAdvancedEditor(node);
}

function setRegularWidgetValue(node, name, value) {
  const widget = findWidget(node, name);
  if (!widget) {
    return false;
  }
  widget.value = value;
  const input = findInputEl(widget);
  if (input) {
    input.value = String(value ?? "");
  }
  widget.callback?.(widget.value);
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  return true;
}

function applyWildcardExecutedInputs(node, message) {
  const payload = firstValue(message?.wildcard, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  if (payload.populated_text != null) {
    setRegularWidgetValue(node, "populated_text", String(payload.populated_text));
  }
  if (payload.mode != null) {
    setRegularWidgetValue(node, "mode", String(payload.mode));
  }
  if (payload.seed != null) {
    setRegularWidgetValue(node, "seed", Number(payload.seed));
  }
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
