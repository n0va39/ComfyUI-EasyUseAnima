// @ts-check

/**
 * Installs the per-node lifecycle for the LoRA Preset node.
 *
 * All host and profile behavior is injected so this module remains usable in
 * frontend semantic tests without reaching through to the application shell.
 */
export function createLoraPresetNodeRuntime({
  nodeTypeName,
  internalWidgetDefaults,
  widgetIndex,
  findWidget,
  findInputEl,
  widgetValue,
  ensureWidgetValue,
  resetInternalLoraSelector,
  normalizeSerializedWidgets,
  profileCount,
  selectedProfileIndex,
  activeProfileIndex,
  wrapProfileIndex,
  setProfileIndex,
  lorasWidgetValue,
  saveProfile,
  saveCurrentProfile,
  loadProfile,
  verifyProfileProvenance,
  scrollProfileBarTo,
  refreshLoraAvailability,
  canvasWidgets,
  enforceNodeLayout,
  requestAnimationFrame,
}) {
  function compactSerializedWidgetValues(node, workflowNode) {
    const values = workflowNode?.widgets_values;
    const widgets = node?.widgets;
    if (!Array.isArray(values) || !Array.isArray(widgets)) {
      return values;
    }
    const serializableCount = widgets.reduce(
      (count, widget) => count + (widget?.serialize === false ? 0 : 1),
      0,
    );
    if (values.length <= serializableCount) {
      return values.slice(0, serializableCount);
    }
    const compact = [];
    for (let widgetIndex = 0; widgetIndex < widgets.length; widgetIndex += 1) {
      const widget = widgets[widgetIndex];
      if (widget?.serialize === false) {
        continue;
      }
      compact.push(values[widgetIndex] ?? widgetValue(widget, null));
    }
    return compact;
  }

  function hideInternalWidget(node, name) {
    const widget = findWidget(node, name);
    if (!widget) {
      return;
    }
    ensureWidgetValue(node, name);
    if (name === "lora_name") {
      resetInternalLoraSelector(node);
    }
    widget.__easyuseAnimaHidden = true;
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
    node.__easyuseAnimaHiddenWidgets ||= {};
    node.__easyuseAnimaHiddenWidgets[name] = widget;
    node.setDirtyCanvas?.(true, true);
  }

  function restoreInternalWidgetsForConfigure(node) {
    const hidden = node.__easyuseAnimaHiddenWidgets;
    if (!hidden || !Array.isArray(node.widgets)) {
      return;
    }
    const entries = [
      ["profile_count", widgetIndex.profileCount],
      ["lora_name", widgetIndex.loraName],
      ["loras", widgetIndex.loras],
      ["profile_data", widgetIndex.profileData],
    ];
    for (const [name, index] of entries) {
      const widget = hidden[name];
      if (!widget || node.widgets.includes(widget)) {
        continue;
      }
      widget.__easyuseAnimaHidden = true;
      widget.hidden = true;
      widget.serialize = true;
      widget.options ||= {};
      widget.options.hidden = true;
      widget.computeSize = () => [0, 0];
      widget.draw = () => {};
      node.widgets.splice(Math.min(index, node.widgets.length), 0, widget);
    }
  }

  function finalizeInternalWidgets(node) {
    resetInternalLoraSelector(node);
    hideInternalWidget(node, "profile_data");
    hideInternalWidget(node, "profile_count");
    hideInternalWidget(node, "lora_name");
    hideInternalWidget(node, "loras");
  }

  function ensureLoraStackInput(node) {
    if (!node.inputs?.some((input) => input.name === "lora_stack")) {
      node.addInput?.("lora_stack", "LORA_STACK");
    }
  }

  function wrapWidgetCallback(node, name, callback) {
    const widget = findWidget(node, name);
    if (!widget || widget.__easyuseAnimaLoraWrapped) {
      return;
    }
    widget.__easyuseAnimaLoraWrapped = true;
    const previous = widget.callback;
    widget.callback = function (...args) {
      const result = previous?.apply(this, args);
      callback?.();
      return result;
    };
  }

  function rehydrateNode(node) {
    finalizeInternalWidgets(node);
    canvasWidgets.ensureProfileBar(node);
    node.__easyuseAnimaActiveProfileIndex = selectedProfileIndex(node);
    loadProfile(node, selectedProfileIndex(node), { initializeFromCurrent: true });
    verifyProfileProvenance(node);
    scrollProfileBarTo(node, selectedProfileIndex(node));
    canvasWidgets.renderProfileBar(node);
    refreshLoraAvailability(node);
    enforceNodeLayout(node);
  }

  function initializeNode(node) {
    if (node.__easyuseAnimaLoraPresetInitialized) {
      return;
    }
    node.__easyuseAnimaLoraPresetInitialized = true;
    node.serialize_widgets = true;
    ensureLoraStackInput(node);
    for (const name of Object.keys(internalWidgetDefaults)) {
      ensureWidgetValue(node, name);
    }
    resetInternalLoraSelector(node);

    wrapWidgetCallback(node, "style_prompt", () => {
      if (!node.__easyuseAnimaLoadingProfile) {
        saveCurrentProfile(node);
        canvasWidgets.renderProfileBar(node);
      }
    });
    wrapWidgetCallback(node, "loras", () => {
      if (!node.__easyuseAnimaLoadingProfile) {
        saveCurrentProfile(node);
        canvasWidgets.renderProfileBar(node);
      }
    });
    wrapWidgetCallback(node, "profile_count", () => {
      if (!node.__easyuseAnimaSuppressProfileCountCallback) {
        saveCurrentProfile(node);
        canvasWidgets.renderProfileBar(node);
      }
    });
    wrapWidgetCallback(node, "profile_index", () => {
      if (node.__easyuseAnimaSuppressProfileIndexCallback) {
        return;
      }
      const index = selectedProfileIndex(node);
      const current = activeProfileIndex(node);
      if (index !== current) {
        saveProfile(node, current);
      }
      node.__easyuseAnimaActiveProfileIndex = index;
      loadProfile(node, index);
      scrollProfileBarTo(node, index);
      canvasWidgets.renderProfileBar(node);
    });

    const originalOnSerialize = node.onSerialize;
    node.onSerialize = function (workflowNode) {
      saveCurrentProfile(this);
      originalOnSerialize?.apply(this, arguments);
      const dataWidget = findWidget(this, "profile_data");
      if (workflowNode?.widgets_values && dataWidget) {
        const values = compactSerializedWidgetValues(this, workflowNode);
        workflowNode.widgets_values = values;
        values[widgetIndex.profileIndex] = activeProfileIndex(this);
        values[widgetIndex.profileCount] = String(profileCount(this));
        values[widgetIndex.loraName] = internalWidgetDefaults.lora_name;
        values[widgetIndex.loras] = JSON.stringify(lorasWidgetValue(this));
        values[widgetIndex.profileData] = widgetValue(dataWidget, "{}");
      }
    };

    const originalOnConfigure = node.onConfigure;
    node.onConfigure = function (...args) {
      originalOnConfigure?.apply(this, args);
      requestAnimationFrame(() => rehydrateNode(this));
    };

    requestAnimationFrame(() => rehydrateNode(node));
  }

  function applyExecutedProfile(node, message) {
    const payload = Array.isArray(message?.lora_preset_profile)
      ? message.lora_preset_profile[0]
      : message?.lora_preset_profile;
    const index = Number.parseInt(payload?.profile_index, 10);
    if (!Number.isFinite(index)) {
      return;
    }
    const nextIndex = wrapProfileIndex(index, profileCount(node));
    const currentIndex = activeProfileIndex(node);
    if (nextIndex === currentIndex) {
      canvasWidgets.renderProfileBar(node);
      return;
    }
    saveProfile(node, currentIndex);
    setProfileIndex(node, nextIndex);
    node.__easyuseAnimaActiveProfileIndex = nextIndex;
    loadProfile(node, nextIndex);
    scrollProfileBarTo(node, nextIndex);
    canvasWidgets.renderProfileBar(node);
    canvasWidgets.renderLoraWidgets(node);
    node.setDirtyCanvas?.(true, true);
  }

  function beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== nodeTypeName) {
      return;
    }
    const originalConfigure = nodeType.prototype.configure;
    nodeType.prototype.configure = function (info) {
      restoreInternalWidgetsForConfigure(this);
      normalizeSerializedWidgets(info);
      return originalConfigure?.apply(this, arguments);
    };
    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function (...args) {
      const result = originalOnNodeCreated?.apply(this, args);
      initializeNode(this);
      return result;
    };
    const originalOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      originalOnExecuted?.apply(this, arguments);
      applyExecutedProfile(this, message);
    };
  }

  return {
    beforeRegisterNodeDef,
    initializeNode,
  };
}
