import { app } from "../../../scripts/app.js";
import { easyuseAnimaWatchLocale } from "./easyuse_anima_i18n.js";
import {
  FIELD_NAMES,
  EXTEND_FIELD_NAMES,
  DEFAULT_ADVANCED_RESOLUTION_BUCKET,
  DEFAULT_ADVANCED_RESOLUTION_SIZE,
  ADVANCED_WIDGET_INDEX,
} from "./prompt_studio/constants.js";
import {
  normalizeAdvancedResolutionBucket,
  normalizeAdvancedResolutionSize,
} from "./prompt_studio/schema.js";
import {
  getAdvancedEditorElement,
} from "./prompt_studio/state.js";
import {
  stopAdvancedControlEvent,
} from "./prompt_studio/dom.js";
import {
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
  applyPromptStudioSettings,
  applyPromptStudioTextStyle,
  loadPromptStudioSettings,
} from "./prompt_studio/settings.js";
import {
  hideTrainedTagTooltip,
} from "./prompt_studio/tooltip.js";
import {
  advancedWidget,
  hideAdvancedControlWidgets as hideAdvancedControlWidgetsWithHooks,
  parseAdvancedFields,
  removeAdvancedInternalInputSockets,
  repairAdvancedInternalWidgetValues as repairAdvancedInternalWidgetValuesWithHooks,
  writeAdvancedFields as writeAdvancedFieldsWithHooks,
} from "./prompt_studio/advanced_fields_state.js";
import {
  installPromptHighlightOverlayRefresh,
  refreshAllPromptHighlights,
} from "./prompt_studio/highlight.js";
import {
  scheduleAdvancedHighlights,
} from "./prompt_studio/advanced_highlights.js";
import {
  updateHighlight,
} from "./prompt_studio/highlight_ui.js";
import {
  findWidget,
} from "./prompt_studio/widgets.js";
import {
  updateAdvancedEditorWidth,
} from "./prompt_studio/layout.js";
import {
  scheduleAdvancedLayout as scheduleAdvancedLayoutWithHooks,
  scheduleAdvancedResizeFinalize as scheduleAdvancedResizeFinalizeWithHooks,
} from "./prompt_studio/advanced_layout_controller.js";
import {
  expandStudioInputToContent as expandStudioInputToContentWithHooks,
  growStudioManualHeightToContent as growStudioManualHeightToContentWithHooks,
  rebalanceStudioInputHeights as rebalanceStudioInputHeightsWithHooks,
  setStudioInputHeight as setStudioInputHeightWithHooks,
  setStudioManualHeight as setStudioManualHeightWithHooks,
  visibleStudioWidgets as visibleStudioWidgetsWithHooks,
} from "./prompt_studio/studio_textareas.js";
import {
  enhanceResizableInput as enhanceResizableInputWithHooks,
} from "./prompt_studio/studio_resizable_input.js";
import {
  applyExecutedInputs as applyExecutedInputsWithHooks,
  restoreInputFromWidget,
  syncStudioValues as syncStudioValuesWithHooks,
  syncWidgetValue,
} from "./prompt_studio/studio_values.js";
import {
  hookStudioNode as hookStudioNodeWithHooks,
} from "./prompt_studio/studio_node_ui.js";
import {
  hookAdvancedNode as hookAdvancedNodeWithHooks,
  renderAdvancedEditor as renderAdvancedEditorWithHooks,
  scheduleHookAdvancedNode as scheduleHookAdvancedNodeWithHooks,
} from "./prompt_studio/advanced_node_ui.js";
import {
  applyAdvancedExecutedInputs as applyAdvancedExecutedInputsWithHooks,
  syncAdvancedValues as syncAdvancedValuesWithHooks,
} from "./prompt_studio/advanced_values.js";
import {
  applyWildcardExecutedInputs as applyWildcardExecutedInputsWithHooks,
} from "./prompt_studio/wildcard_values.js";
import {
  captureAdvancedConfigure,
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

function enhanceResizableInput(node, widget) {
  enhanceResizableInputWithHooks(node, widget, {
    expandStudioInputToContent,
    growStudioManualHeightToContent,
    setStudioInputHeight,
    setStudioManualHeight,
    updateHighlight,
  });
}

function hookStudioNode(node, attempt = 0) {
  hookStudioNodeWithHooks(node, attempt, {
    applyExtendSlotVisibility,
    enhanceResizableInput,
    ensureExtendSlotControls,
    ensureLegendWidget,
    isExtendNode,
    layoutExtendPromptWidgets,
    refreshNodeSize,
    restoreInputFromWidget,
    studioFieldNames,
    syncWidgetValue,
    updateHighlight,
  });
}

function installAdvancedSaveSyncForApp() {
  installAdvancedSaveSync(app, syncAllAdvancedNodes);
}

function advancedNodeUiHooks() {
  return {
    hideAdvancedControlWidgets,
    installAdvancedSaveSync: installAdvancedSaveSyncForApp,
    scheduleAdvancedHighlights,
    scheduleAdvancedLayout,
    writeAdvancedFields,
  };
}

function renderAdvancedEditor(node) {
  renderAdvancedEditorWithHooks(node, advancedNodeUiHooks());
}

function hookAdvancedNode(node) {
  hookAdvancedNodeWithHooks(node, advancedNodeUiHooks());
}

function scheduleHookAdvancedNode(node) {
  scheduleHookAdvancedNodeWithHooks(node, advancedNodeUiHooks());
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
