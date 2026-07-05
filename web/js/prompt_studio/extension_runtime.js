// @ts-check

import {
  easyuseAnimaWatchLocale,
} from "../easyuse_anima_i18n.js";
import {
  FIELD_NAMES,
  EXTEND_FIELD_NAMES,
  ADVANCED_WIDGET_INDEX,
} from "./constants.js";
import {
  installMiddlePanForwarder,
} from "./canvas_forwarding.js";
import {
  ensureLegendWidget,
} from "./legend.js";
import {
  applyExtendSlotVisibility,
} from "./extend_slots.js";
import {
  ensureExtendSlotControls as ensureExtendSlotControlsWithHooks,
  refreshExtendSlotControlsSize,
  renderExtendSlotControls as renderExtendSlotControlsWithHooks,
} from "./extend_slot_controls.js";
import {
  layoutExtendPromptWidgets as layoutExtendPromptWidgetsWithHooks,
} from "./extend_layout.js";
import {
  isAdvancedNode,
  isExtendNode,
  installAdvancedSaveSync,
  registerPromptStudioNodeHooks,
  syncAdvancedNodes,
} from "./node_hooks.js";
import {
  applyPromptStudioSettings,
  applyPromptStudioTextStyle,
  loadPromptStudioSettings,
} from "./settings.js";
import {
  hideTrainedTagTooltip,
} from "./tooltip.js";
import {
  advancedWidget,
  hideAdvancedControlWidgets as hideAdvancedControlWidgetsWithHooks,
  parseAdvancedFields,
  removeAdvancedInternalInputSockets,
  repairAdvancedInternalWidgetValues as repairAdvancedInternalWidgetValuesWithHooks,
  writeAdvancedFields as writeAdvancedFieldsWithHooks,
} from "./advanced_fields_state.js";
import {
  installPromptHighlightOverlayRefresh,
  refreshAllPromptHighlights,
} from "./highlight.js";
import {
  scheduleAdvancedHighlights,
} from "./advanced_highlights.js";
import {
  updateHighlight,
} from "./highlight_ui.js";
import {
  findWidget,
} from "./widgets.js";
import {
  updateAdvancedEditorWidth,
} from "./layout.js";
import {
  scheduleAdvancedLayout as scheduleAdvancedLayoutWithHooks,
  scheduleAdvancedResizeFinalize as scheduleAdvancedResizeFinalizeWithHooks,
} from "./advanced_layout_controller.js";
import {
  expandStudioInputToContent as expandStudioInputToContentWithHooks,
  growStudioManualHeightToContent as growStudioManualHeightToContentWithHooks,
  rebalanceStudioInputHeights as rebalanceStudioInputHeightsWithHooks,
  setStudioInputHeight as setStudioInputHeightWithHooks,
  setStudioManualHeight as setStudioManualHeightWithHooks,
  visibleStudioWidgets as visibleStudioWidgetsWithHooks,
} from "./studio_textareas.js";
import {
  enhanceResizableInput as enhanceResizableInputWithHooks,
} from "./studio_resizable_input.js";
import {
  applyExecutedInputs as applyExecutedInputsWithHooks,
  restoreInputFromWidget,
  syncStudioValues as syncStudioValuesWithHooks,
  syncWidgetValue,
} from "./studio_values.js";
import {
  hookStudioNode as hookStudioNodeWithHooks,
} from "./studio_node_ui.js";
import {
  hookAdvancedNode as hookAdvancedNodeWithHooks,
  renderAdvancedEditor as renderAdvancedEditorWithHooks,
  scheduleHookAdvancedNode as scheduleHookAdvancedNodeWithHooks,
} from "./advanced_node_ui.js";
import {
  applyAdvancedExecutedInputs as applyAdvancedExecutedInputsWithHooks,
  syncAdvancedValues as syncAdvancedValuesWithHooks,
} from "./advanced_values.js";
import {
  applyWildcardExecutedInputs as applyWildcardExecutedInputsWithHooks,
} from "./wildcard_values.js";
import {
  captureAdvancedConfigure,
  pruneDisconnectedAdvancedFieldInputValues,
} from "./serialization.js";
import {
  markCanvasDirty as markCanvasDirtyWithApp,
  markGraphDirty as markGraphDirtyWithApp,
  markNodeDirty as markNodeDirtyWithApp,
  refreshNodeSize as refreshNodeSizeWithApp,
} from "./runtime_canvas.js";

function createPromptStudioExtensionRuntime(app) {
  function markNodeDirty(node) {
    markNodeDirtyWithApp(app, node);
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
    refreshNodeSizeWithApp(app, node, options);
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
    markCanvasDirtyWithApp(app);
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
    markGraphDirtyWithApp(app);
  }

  function advancedLayoutControllerHooks() {
    return {
      markGraphDirty,
      parseAdvancedFields,
      scheduleAdvancedHighlights,
      writeAdvancedFields,
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

  return {
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
        const settingsEvent = /** @type {CustomEvent<Record<string, unknown>>} */ (event);
        if (!settingsEvent.detail) {
          return;
        }
        applyPromptStudioSettings(settingsEvent.detail, { hideTrainedTagTooltip });
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
  };
}

export {
  createPromptStudioExtensionRuntime,
};
