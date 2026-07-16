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
  installAdvancedWheelForwarder,
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
  disconnectAdvancedEditorWidthObserver,
  observeAdvancedEditorWidth as observeAdvancedEditorWidthWithHooks,
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
  remeasureAdvancedTextareaHeightsForWidth as remeasureAdvancedTextareaHeightsForWidthWithHooks,
} from "./advanced_fields_ui.js";
import {
  renderAdvancedEditor as renderAdvancedEditorWithHooks,
  scheduleHookAdvancedNode as scheduleHookAdvancedNodeWithHooks,
} from "./advanced_node_ui.js";
import {
  applyAdvancedExecutedInputs as applyAdvancedExecutedInputsWithHooks,
  syncAdvancedValues as syncAdvancedValuesWithHooks,
} from "./advanced_values.js";
import {
  createAdvancedQueueSeedRuntime,
  installAdvancedQueueSeedGraphCleanup,
  installAdvancedQueueSeedQueueHook,
} from "./advanced_queue_seed_runtime.js";
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

function createPromptStudioExtensionRuntime(app, api = null) {
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
      shouldApplyExecutedSeed: advancedQueueSeedRuntime.shouldApplyExecutedSeed,
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

  const advancedQueueSeedRuntime = createAdvancedQueueSeedRuntime({
    seedWidgetIndex: ADVANCED_WIDGET_INDEX.wildcard_seed,
    listNodes: () => app.graph?._nodes || [],
    isAdvancedNode,
    isOutputNode: (node) => node?.constructor?.nodeData?.output_node === true,
    getSeed: (node) => findWidget(node, "wildcard_seed")?.value,
    updateSeed(node, seed) {
      const widget = findWidget(node, "wildcard_seed");
      if (!widget) {
        throw new Error("Prompt Studio wildcard_seed widget is unavailable.");
      }
      widget.value = seed;
      renderAdvancedEditor(node);
    },
    clonePrompt: (value) => JSON.parse(JSON.stringify(value)),
    randomSeed() {
      const values = new Uint32Array(2);
      if (globalThis.crypto?.getRandomValues) {
        globalThis.crypto.getRandomValues(values);
        return (values[0] & 0x1fffff) * 0x100000000 + values[1];
      }
      return Math.floor(Math.random() * Number.MAX_SAFE_INTEGER);
    },
  });

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
      remeasureAdvancedTextareaHeightsForWidth,
      scheduleAdvancedHighlights,
    };
  }

  function remeasureAdvancedTextareaHeightsForWidth(node) {
    return remeasureAdvancedTextareaHeightsForWidthWithHooks(node, {
      parseAdvancedFields,
      writeAdvancedFields,
    });
  }

  function scheduleAdvancedLayout(node, reason = "layout") {
    scheduleAdvancedLayoutWithHooks(node, reason, advancedLayoutControllerHooks());
  }

  function scheduleAdvancedResizeFinalize(node) {
    scheduleAdvancedResizeFinalizeWithHooks(node, advancedLayoutControllerHooks());
  }

  function observeAdvancedEditorWidth(node) {
    observeAdvancedEditorWidthWithHooks(node, advancedLayoutControllerHooks());
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
      observeAdvancedEditorWidth,
      scheduleAdvancedHighlights,
      scheduleAdvancedLayout,
      writeAdvancedFields,
    };
  }

  function renderAdvancedEditor(node) {
    renderAdvancedEditorWithHooks(node, advancedNodeUiHooks());
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
      installAdvancedWheelForwarder();
      installMiddlePanForwarder();
      installAdvancedSaveSync(app, syncAllAdvancedNodes);
      installAdvancedQueueSeedGraphCleanup(app.graph, advancedQueueSeedRuntime);
      installAdvancedQueueSeedQueueHook(api, advancedQueueSeedRuntime);
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
        attachAdvancedQueueSeedNode: advancedQueueSeedRuntime.attachNode,
        applyAdvancedExecutedInputs,
        applyExecutedInputs,
        applyExtendSlotVisibility,
        applyWildcardExecutedInputs,
        captureAdvancedConfigure: (node, serialized) => (
          captureAdvancedConfigure(node, serialized, advancedWidget(node))
        ),
        disconnectAdvancedEditorWidthObserver,
        detachAdvancedQueueSeedNode: advancedQueueSeedRuntime.detachNode,
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
