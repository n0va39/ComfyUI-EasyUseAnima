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
  scheduleAdvancedFieldHighlight,
  scheduleAdvancedHighlights,
  updateAdvancedFieldHighlight,
} from "./advanced_highlights.js";
import {
  updateHighlight,
} from "./highlight_ui.js";
import {
  findWidget,
} from "./widgets.js";
import {
  resolveStudioInput as resolveStudioInputWithCanvas,
} from "./studio_input_resolver.js";
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
  restoreInputFromWidget,
  syncStudioValues as syncStudioValuesWithHooks,
  syncWidgetValue,
} from "./studio_values.js";
import {
  hookStudioNode as hookStudioNodeWithHooks,
} from "./studio_node_ui.js";
import {
  remeasureAdvancedTextareaHeightsForWidth as remeasureAdvancedTextareaHeightsForWidthWithHooks,
  syncAdvancedLinkedFieldTextarea as syncAdvancedLinkedFieldTextareaWithHooks,
  syncAdvancedNaiaFieldTextarea as syncAdvancedNaiaFieldTextareaWithHooks,
} from "./advanced_fields_ui.js";
import {
  disposeAdvancedAutocompleteInputs,
  renderAdvancedEditor as renderAdvancedEditorWithHooks,
  scheduleHookAdvancedNode as scheduleHookAdvancedNodeWithHooks,
} from "./advanced_node_ui.js";
import {
  WILDCARD_SEED_CONTROL_SURFACE,
  publishAdvancedExecution as publishAdvancedExecutionWithHooks,
  syncAdvancedValues as syncAdvancedValuesWithHooks,
} from "./advanced_values.js";
import {
  applyWildcardExecutedInputs as applyWildcardExecutedInputsWithHooks,
  hookWildcardSeedWidget,
  syncWildcardSerialization,
} from "./wildcard_values.js";
import {
  advancedLinkedFieldSurface,
  captureAdvancedLinkedFieldSnapshots,
  captureAdvancedConfigure,
  commitAdvancedLinkedFieldOverlay,
  isAdvancedFieldInput,
  pruneDisconnectedAdvancedFieldInputValues,
} from "./serialization.js";
import {
  ADVANCED_NAIA_RESOLUTION_SURFACE,
  advancedNaiaFieldSurface,
  captureAdvancedNaiaFieldSnapshots,
  captureAdvancedNaiaResolutionSnapshot,
  commitAdvancedNaiaFieldCanonical,
  commitAdvancedNaiaResolution,
} from "./naia_projection.js";
import {
  getAdvancedFields,
} from "./state.js";
import {
  markCanvasDirty as markCanvasDirtyWithApp,
  markGraphDirty as markGraphDirtyWithApp,
  markNodeDirty as markNodeDirtyWithApp,
  refreshNodeSize as refreshNodeSizeWithApp,
} from "./runtime_canvas.js";
import {
  createHostHookRuntimeLifecycle,
  registerHostHookCallbacks,
} from "../lifecycle/host_hook_registry.js";
import {
  createQueueUiTransactionOwner,
} from "../lifecycle/queue_ui_transaction.js";
import {
  createExecutedEventContext,
} from "../lifecycle/executed_event_context.js";
import {
  createPromptStudioExecutionTransaction,
} from "./execution_transaction.js";
import {
  commitAdvancedNaiaResolutionView,
  commitAdvancedWildcardSeedView,
} from "./advanced_controls.js";

const PROMPT_STUDIO_GLOBAL_HOOK_RUNTIME_OWNER = Symbol.for(
  "easyuse-anima.prompt-studio.global-hook-runtime-owner",
);
const PROMPT_STUDIO_WILDCARD_SEED_TRANSACTION_OWNER = Symbol.for(
  "easyuse-anima.prompt-studio.wildcard-seed-transaction",
);
const PROMPT_STUDIO_EDIT_BINDINGS = [
  {
    widgetNames: [
      "wildcard_seed",
      "wildcard_seed_after_generate",
    ],
    surfaces: [WILDCARD_SEED_CONTROL_SURFACE],
  },
  {
    widgetNames: [
      "resolution_bucket",
      "resolution_size",
      "resolution_custom_width",
      "resolution_custom_height",
    ],
    surfaces: [ADVANCED_NAIA_RESOLUTION_SURFACE],
  },
];

function createPromptStudioExtensionRuntime(app, api) {
  const globalHookLifecycle = createHostHookRuntimeLifecycle(
    app,
    PROMPT_STUDIO_GLOBAL_HOOK_RUNTIME_OWNER,
  );
  const queueUiTransactionOwner = createQueueUiTransactionOwner();
  let executionTransaction;
  const executedEventContext = createExecutedEventContext(api, {
    finishPrompt: (promptId) => executionTransaction.finishPrompt(promptId),
  });
  executionTransaction = createPromptStudioExecutionTransaction({
    owner: queueUiTransactionOwner,
    executedContext: executedEventContext,
    findWidget,
    editBindings: PROMPT_STUDIO_EDIT_BINDINGS,
  });
  const snapshotsByTransaction = new WeakMap();
  let advancedSaveSyncSerializeHost;
  let executionTransactionGraphHost;

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

  function syncAdvancedLinkedFieldTextarea(node, field, textarea, value) {
    return syncAdvancedLinkedFieldTextareaWithHooks(
      node,
      field,
      textarea,
      value,
      {
        scheduleAdvancedFieldHighlight,
        scheduleAdvancedLayout,
        updateAdvancedFieldHighlight,
      },
    );
  }

  function syncAdvancedNaiaFieldTextarea(node, field, textarea, value) {
    return syncAdvancedNaiaFieldTextareaWithHooks(
      node,
      field,
      textarea,
      value,
      {
        scheduleAdvancedFieldHighlight,
        scheduleAdvancedLayout,
        updateAdvancedFieldHighlight,
      },
    );
  }

  function createLinkedExecutionCommitter(node, inputName, value) {
    const currentSnapshot = captureAdvancedLinkedFieldSnapshots(
      node,
      getAdvancedFields(node) || parseAdvancedFields(node),
      app.graph,
    ).find((snapshot) => snapshot.inputName === inputName);
    if (!currentSnapshot) {
      return null;
    }
    return {
      surface: currentSnapshot.surface,
      commit: ({ transaction }) => {
        const queuedSnapshot = (snapshotsByTransaction.get(transaction)?.linked || [])
          .find((snapshot) => snapshot.inputName === inputName);
        if (!queuedSnapshot) {
          return false;
        }
        return commitAdvancedLinkedFieldOverlay(node, queuedSnapshot, value, {
          graph: app.graph,
          commitView: syncAdvancedLinkedFieldTextarea,
        });
      },
    };
  }

  function createNaiaExecutionCommitter(node, fieldId, value) {
    const currentSnapshot = captureAdvancedNaiaFieldSnapshots(
      getAdvancedFields(node) || parseAdvancedFields(node),
    ).find((snapshot) => snapshot.fieldId === fieldId);
    if (!currentSnapshot) {
      return null;
    }
    return {
      surface: currentSnapshot.surface,
      commit: ({ transaction }) => {
        const queuedSnapshot = (snapshotsByTransaction.get(transaction)?.naia || [])
          .find((snapshot) => snapshot.fieldId === fieldId);
        if (!queuedSnapshot) {
          return false;
        }
        return commitAdvancedNaiaFieldCanonical(node, queuedSnapshot, value, {
          persistFields: (target, fields) => writeAdvancedFields(
            target,
            fields,
            { syncInputs: false },
          ),
          commitView: syncAdvancedNaiaFieldTextarea,
        });
      },
    };
  }

  function createNaiaResolutionExecutionCommitter(node, value) {
    const currentSnapshot = captureAdvancedNaiaResolutionSnapshot(node);
    if (!currentSnapshot) {
      return null;
    }
    return {
      surface: currentSnapshot.surface,
      commit: ({ transaction }) => {
        const queuedSnapshot = snapshotsByTransaction.get(transaction)?.resolution;
        if (!queuedSnapshot) {
          return false;
        }
        return commitAdvancedNaiaResolution(node, queuedSnapshot, value, {
          commitView: commitAdvancedNaiaResolutionView,
        });
      },
    };
  }

  function advancedValuesHooks() {
    return {
      advancedWidget,
      commitAdvancedWildcardSeedView,
      consumePromptStudioExecution: executionTransaction.consumeExecution,
      createLinkedExecutionCommitter,
      createNaiaExecutionCommitter,
      createNaiaResolutionExecutionCommitter,
      markNodeDirty,
      parseAdvancedFields,
      repairAdvancedInternalWidgetValues,
      renderAdvancedEditor,
      writeAdvancedFields,
    };
  }

  function syncAdvancedValues(node, serialized = null) {
    syncAdvancedValuesWithHooks(node, serialized, advancedValuesHooks());
  }

  function publishAdvancedExecution(node, message) {
    publishAdvancedExecutionWithHooks(node, message, advancedValuesHooks());
  }

  function applyWildcardExecutedInputs(node, message) {
    applyWildcardExecutedInputsWithHooks(node, message, {
      markNodeDirty,
    });
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

  function resolveStudioInput(node, widget) {
    return resolveStudioInputWithCanvas(
      node,
      widget,
      studioFieldNames(node),
      app.canvas?.canvas,
    );
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
      resolveStudioInput,
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
      resolveStudioInput,
      restoreInputFromWidget,
      studioFieldNames,
      syncWidgetValue,
      updateHighlight,
    });
  }

  function installAdvancedSaveSyncForApp() {
    const serializeHost = globalThis.LGraph?.prototype || app?.graph?.constructor?.prototype || null;
    const replace = advancedSaveSyncSerializeHost !== undefined
      && serializeHost != null
      && serializeHost !== advancedSaveSyncSerializeHost;
    const installed = globalHookLifecycle.install(
      "advanced-save-sync",
      () => installAdvancedSaveSync(app, syncAllAdvancedNodes),
      { replace },
    );
    if (installed) {
      advancedSaveSyncSerializeHost = serializeHost;
    }
    return installed;
  }

  function capturePromptStudioExecutionQueue() {
    const snapshotsByNode = new Map();
    const entries = (app.graph?._nodes || []).filter(isAdvancedNode).map((node) => {
      const fields = getAdvancedFields(node) || parseAdvancedFields(node);
      const linked = captureAdvancedLinkedFieldSnapshots(
        node,
        fields,
        app.graph,
      );
      const naia = captureAdvancedNaiaFieldSnapshots(fields);
      const resolution = captureAdvancedNaiaResolutionSnapshot(node);
      snapshotsByNode.set(node, { linked, naia, resolution });
      return {
        node,
        surfaces: [
          WILDCARD_SEED_CONTROL_SURFACE,
          ...linked.map((snapshot) => snapshot.surface),
          ...naia.map((snapshot) => snapshot.surface),
          ...(resolution ? [resolution.surface] : []),
        ],
      };
    });
    const captured = executionTransaction.captureQueue(entries);
    for (const entry of captured) {
      snapshotsByTransaction.set(
        entry.transaction,
        snapshotsByNode.get(entry.node) || { linked: [], naia: [], resolution: null },
      );
    }
    return captured;
  }

  function installPromptStudioExecutionTransactionForApp() {
    const graphHost = app?.graph || null;
    const replace = executionTransactionGraphHost !== undefined
      && graphHost != null
      && graphHost !== executionTransactionGraphHost;
    const installed = globalHookLifecycle.install(
      "advanced-wildcard-seed-transaction",
      () => registerHostHookCallbacks({
        owner: PROMPT_STUDIO_WILDCARD_SEED_TRANSACTION_OWNER,
        // ComfyApp.queuePrompt resolves to a boolean after draining its local
        // batch. ComfyApi.queuePrompt is the per-submission host call whose
        // successful result owns the accepted prompt_id.
        queueHost: api,
        graphHost,
        beforeQueue: capturePromptStudioExecutionQueue,
        afterQueue: (context) => executionTransaction.acceptQueue(
          context.callbackState,
          context,
        ),
        onGraphClear: () => executionTransaction.clear(),
      }),
      { replace },
    );
    if (installed) {
      executionTransactionGraphHost = graphHost;
    }
    return installed;
  }

  function installGlobalHooks() {
    installAdvancedSaveSyncForApp();
    installPromptStudioExecutionTransactionForApp();
  }

  function disposeGlobalHooks() {
    advancedSaveSyncSerializeHost = undefined;
    executionTransactionGraphHost = undefined;
    return globalHookLifecycle.dispose();
  }

  function disposeRuntime() {
    let changed = disposeGlobalHooks();
    changed = executedEventContext.dispose() || changed;
    changed = executionTransaction.dispose() || changed;
    return changed;
  }

  function markAdvancedFieldEdited(node, field) {
    const surface = field?.type === "naia"
      ? advancedNaiaFieldSurface(field?.id)
      : advancedLinkedFieldSurface(field?.id);
    return surface != null && executionTransaction.markEdited(node, [surface]);
  }

  function markAdvancedConnectionChanged(node, args) {
    if (Number(args?.[0]) !== 1) {
      return false;
    }
    const slot = Number(args?.[1]);
    const input = Number.isInteger(slot) ? node?.inputs?.[slot] : null;
    if (!isAdvancedFieldInput(input)) {
      return false;
    }
    const surface = advancedLinkedFieldSurface(input.__easyuseAnimaAdvancedFieldId);
    return surface != null && executionTransaction.markEdited(node, [surface]);
  }

  function advancedNodeUiHooks() {
    return {
      hideAdvancedControlWidgets,
      installAdvancedSaveSync: installAdvancedSaveSyncForApp,
      markAdvancedFieldEdited,
      markAdvancedFieldStructureChanged: markAdvancedFieldEdited,
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
    dispose: disposeRuntime,
    async setup() {
      installAdvancedWheelForwarder();
      installMiddlePanForwarder();
      executedEventContext.install();
      installGlobalHooks();
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
        applyExtendSlotVisibility,
        applyWildcardExecutedInputs,
        captureAdvancedConfigure: (node, serialized) => (
          captureAdvancedConfigure(node, serialized, advancedWidget(node))
        ),
        disconnectAdvancedEditorWidthObserver,
        disposeAdvancedAutocompleteInputs,
        disposeAdvancedWildcardSeedNode: executionTransaction.disposeNode,
        hookWildcardSeedWidget,
        hookAdvancedWildcardSeedNode: executionTransaction.hookNode,
        hookStudioNode,
        isExtendNode,
        layoutExtendPromptWidgets,
        markAdvancedConnectionChanged,
        pruneDisconnectedAdvancedFieldInputValues,
        publishAdvancedExecution,
        rebalanceStudioInputHeights,
        removeAdvancedInternalInputSockets,
        renderAdvancedEditor,
        renderExtendSlotControls,
        scheduleAdvancedResizeFinalize,
        scheduleHookAdvancedNode,
        syncAdvancedValues,
        syncStudioValues,
        syncWildcardSerialization,
        updateAdvancedEditorWidth,
      });
    },
  };
}

export {
  createPromptStudioExtensionRuntime,
};
