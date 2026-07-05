// @ts-check

import {
  ADVANCED_FIELD_LABELS,
} from "./constants.js";
import { debounce } from "./utils.js";
import { advancedFieldInputName } from "./schema.js";
import { getAdvancedFields } from "./state.js";
import {
  advancedPaneFields,
  hasAdvancedNaia,
  hasPositiveTrigger,
  moveAdvancedFieldInPane,
} from "./fields.js";
import {
  advancedTextareaAutoHeight,
  advancedTextareaContentHeight,
  advancedTextareaCurrentBoxHeight,
  advancedTextareaMinimumHeight,
} from "./layout.js";
import { setAdvancedControlValue } from "./advanced_controls.js";
import { requestOverlaySync } from "./highlight.js";
import {
  advancedFieldDisplayText,
  advancedFieldIndexLabel,
  advancedFieldInputLinked,
} from "./serialization.js";
import {
  advancedFieldTextareaPlaceholder,
  advancedFieldTextareaTitle,
  captureAdvancedTextareaManualResize,
  rememberAdvancedTextareaResizeStart,
  syncAdvancedTextareaLinkedInputValue,
} from "./textarea.js";
import { psText } from "./text.js";
import {
  findWidget,
  isWidgetInputLinked,
} from "./widgets.js";

function advancedFieldByTextarea(node, textarea, hooks = {}) {
  const id = String(textarea?.dataset?.easyuseAnimaAdvancedFieldId || "");
  if (!id) {
    return null;
  }
  return (getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [])
    .find((field) => field.id === id) || null;
}

function markAdvancedTextareaProgrammaticHeight(textarea) {
  textarea.__easyuseAnimaAdvancedApplyingHeight = true;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      textarea.__easyuseAnimaAdvancedApplyingHeight = false;
    });
  });
}

function setAdvancedTextareaHeight(node, textarea, height, options = {}, hooks = {}) {
  const mode = options.mode === "manual" ? "manual" : "auto";
  const minimumHeight = advancedTextareaMinimumHeight(textarea);
  const contentHeight = advancedTextareaContentHeight(textarea);
  const requiredHeight = mode === "manual" ? minimumHeight : Math.max(minimumHeight, contentHeight);
  const nextHeight = Math.max(requiredHeight, Math.round(Number(height) || 0));
  markAdvancedTextareaProgrammaticHeight(textarea);
  textarea.style.minHeight = `${minimumHeight}px`;
  textarea.style.height = `${nextHeight}px`;
  textarea.style.overflowY = mode === "manual" && contentHeight > nextHeight ? "auto" : "hidden";
  let field = null;
  if (options.syncField !== false || options.refreshHighlight !== false) {
    field = advancedFieldByTextarea(node, textarea, hooks);
  }
  if (options.syncField !== false && field) {
    field.height = nextHeight;
    field.heightMode = mode;
  }
  if (options.refreshHighlight !== false) {
    hooks.updateAdvancedFieldHighlight?.(node, field, textarea);
  }
  return nextHeight;
}

function syncAdvancedTextareaHeightsForWidth(node, hooks = {}) {
  const fields = getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [];
  const textareas = [...(node?.__easyuseAnimaAdvancedEditorEl?.querySelectorAll?.(
    "textarea[data-easyuse-anima-advanced-field-id]",
  ) || [])];
  let changed = false;

  for (const textarea of textareas) {
    if (!(textarea instanceof HTMLTextAreaElement)) {
      continue;
    }
    const field = advancedFieldByTextarea(node, textarea, hooks);
    if (!field) {
      continue;
    }
    const mode = field.heightMode === "manual" ? "manual" : "auto";
    const previousHeight = Math.round(
      Number.parseFloat(textarea.style.height || "")
      || Number(textarea.offsetHeight)
      || Number(field.height)
      || 0,
    );
    const requestedHeight = mode === "manual"
      ? Math.max(
        advancedTextareaMinimumHeight(textarea),
        Math.round(Number(field.height) || 0) || advancedTextareaCurrentBoxHeight(textarea),
      )
      : advancedTextareaAutoHeight(textarea);
    const nextHeight = setAdvancedTextareaHeight(node, textarea, requestedHeight, {
      mode,
      syncField: false,
      refreshHighlight: false,
    }, hooks);
    if (Math.abs(nextHeight - previousHeight) > 1) {
      changed = true;
      requestOverlaySync(textarea);
    }
  }

  return changed;
}

function installAdvancedTextareaResizeObserver(textarea, persistTextareaHeight) {
  if (!(textarea instanceof HTMLTextAreaElement) || typeof ResizeObserver !== "function") {
    return;
  }
  let lastHeight = advancedTextareaCurrentBoxHeight(textarea);
  const observer = new ResizeObserver(() => {
    if (textarea.__easyuseAnimaAdvancedApplyingHeight || !textarea.isConnected) {
      lastHeight = advancedTextareaCurrentBoxHeight(textarea);
      return;
    }
    const currentHeight = advancedTextareaCurrentBoxHeight(textarea);
    if (Math.abs(currentHeight - lastHeight) <= 1) {
      return;
    }
    lastHeight = currentHeight;
    persistTextareaHeight(currentHeight, "manual");
  });
  observer.observe(textarea);
  textarea.__easyuseAnimaAdvancedResizeObserver = observer;
}

function createAdvancedTextareaResizeHandle(node, textarea, persistTextareaHeight, hooks = {}) {
  const handle = document.createElement("div");
  handle.className = "easyuse-anima-advanced-textarea-resize";
  handle.draggable = false;
  const startResize = (event) => {
    if (Number(event.button) > 0) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    if (handle.__easyuseAnimaAdvancedTextareaResizing) {
      return;
    }
    handle.__easyuseAnimaAdvancedTextareaResizing = true;
    rememberAdvancedTextareaResizeStart(textarea);
    const startY = event.clientY;
    const startHeight = advancedTextareaCurrentBoxHeight(textarea);
    const rectHeight = Math.max(1, textarea.getBoundingClientRect().height);
    const cssPixelScale = startHeight / rectHeight;
    const moveEventName = event.type === "mousedown" ? "mousemove" : "pointermove";
    const upEventName = event.type === "mousedown" ? "mouseup" : "pointerup";
    const cancelEventName = event.type === "mousedown" ? null : "pointercancel";

    const move = (moveEvent) => {
      moveEvent.preventDefault();
      moveEvent.stopPropagation();
      const nextHeight = startHeight + ((moveEvent.clientY - startY) * cssPixelScale);
      setAdvancedTextareaHeight(node, textarea, nextHeight, {
        mode: "manual",
        syncField: false,
        refreshHighlight: false,
      }, hooks);
      requestOverlaySync(textarea);
    };
    const finish = (finishEvent) => {
      finishEvent?.preventDefault?.();
      finishEvent?.stopPropagation?.();
      handle.__easyuseAnimaAdvancedTextareaResizing = false;
      document.removeEventListener(moveEventName, move, true);
      document.removeEventListener(upEventName, finish, true);
      if (cancelEventName) {
        document.removeEventListener(cancelEventName, finish, true);
      }
      persistTextareaHeight(advancedTextareaCurrentBoxHeight(textarea), "manual");
    };

    document.addEventListener(moveEventName, move, true);
    document.addEventListener(upEventName, finish, true);
    if (cancelEventName) {
      document.addEventListener(cancelEventName, finish, true);
    }
    try {
      handle.setPointerCapture?.(event.pointerId);
    } catch {
      // Pointer capture can fail in transformed/canvas-hosted DOM overlays.
    }
  };
  handle.addEventListener("pointerdown", startResize, true);
  handle.addEventListener("mousedown", startResize, true);
  handle.addEventListener("click", (event) => event.stopPropagation(), true);
  return handle;
}

function createAdvancedFieldElement(node, field, hooks = {}) {
  const fields = getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [];
  const globalIndex = fields.findIndex((item) => item.id === field.id);
  const samePane = fields.filter((item) => item.pane === field.pane);
  const paneIndex = samePane.findIndex((item) => item.id === field.id);
  const block = document.createElement("div");
  block.className = "easyuse-anima-advanced-field";
  block.classList.toggle("is-naia", field.type === "naia");
  block.classList.toggle("is-trigger", field.type === "trigger");
  block.classList.toggle("is-disabled", field.enabled === false);
  const textareaWrap = document.createElement("div");
  textareaWrap.className = "easyuse-anima-advanced-textarea-wrap";

  const header = document.createElement("div");
  header.className = "easyuse-anima-field-header";
  const label = document.createElement("div");
  label.className = "easyuse-anima-field-label";
  const fallbackLabel = field.label || ADVANCED_FIELD_LABELS[field.type] || "General Tags";
  label.textContent = `${advancedFieldIndexLabel(fields, field)}. ${hooks.advancedFieldLabel?.(field) || fallbackLabel}`;
  const tools = document.createElement("div");
  tools.className = "easyuse-anima-field-tools";

  const move = (direction) => {
    const currentFields = getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [];
    if (moveAdvancedFieldInPane(currentFields, field, direction)) {
      hooks.writeAdvancedFields?.(node, currentFields, { render: true });
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
      hooks.writeAdvancedFields?.(node, fields, { render: true });
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
        hooks.writeAdvancedFields?.(node, fields, { render: true });
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
      const currentFields = getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [];
      const target = currentFields.find((item) => item.id === field.id);
      if (target?.enabled === false) {
        return;
      }
      const nextValue = !findWidget(node, "use_naia")?.value;
      setAdvancedControlValue(node, "consume_naia_on_queue", true);
      setAdvancedControlValue(node, "use_naia", nextValue);
      hooks.applyAdvancedNaiaGeneralAutoToggle?.(node, currentFields);
      hooks.writeAdvancedFields?.(node, currentFields, { render: true });
    }, linkedUseNaia || field.enabled === false, field.enabled !== false && !!useNaiaWidget?.value);
    fillButton.classList.add("easyuse-anima-naia-fill");
    fillButton.classList.toggle("is-on", field.enabled !== false && !!useNaiaWidget?.value);
    fillButton.classList.toggle("is-linked", linkedUseNaia);
  }
  addTool("↑", psText("advanced.moveUp"), () => move(-1), paneIndex <= 0);
  addTool("↓", psText("advanced.moveDown"), () => move(1), paneIndex >= samePane.length - 1);
  addTool("X", psText("advanced.deleteField"), () => {
    const currentFields = getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [];
    currentFields.splice(globalIndex, 1);
    hooks.writeAdvancedFields?.(node, currentFields, { render: true });
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
    hooks.scheduleAdvancedFieldHighlight?.(node, field, textarea);
  }, 180);
  const persistTextareaHeight = (height, mode = field.heightMode || "auto") => {
    const previousHeight = Math.round(Number(field.height) || 0);
    const previousMode = field.heightMode || "auto";
    const nextHeight = setAdvancedTextareaHeight(node, textarea, height, {
      mode,
    }, hooks);
    field.height = nextHeight;
    field.heightMode = mode === "manual" ? "manual" : "auto";
    hooks.writeAdvancedFields?.(node, fields, { syncInputs: false });
    hooks.updateAdvancedFieldHighlight?.(node, field, textarea);
    updateFieldHighlight();
    if (Math.abs(nextHeight - previousHeight) > 1 || field.heightMode !== previousMode) {
      hooks.scheduleAdvancedLayout?.(node, "textarea");
    } else {
      requestOverlaySync(textarea);
    }
  };
  const syncHeight = () => {
    if (field.heightMode === "manual") {
      const nextHeight = setAdvancedTextareaHeight(node, textarea, field.height || advancedTextareaCurrentBoxHeight(textarea), {
        mode: "manual",
        syncField: false,
      }, hooks);
      hooks.writeAdvancedFields?.(node, fields, { syncInputs: false });
      hooks.updateAdvancedFieldHighlight?.(node, field, textarea);
      updateFieldHighlight();
      if (Math.abs(nextHeight - (Number(field.height) || 0)) > 1) {
        hooks.scheduleAdvancedLayout?.(node, "textarea");
      } else {
        requestOverlaySync(textarea);
      }
      return;
    }
    textarea.style.height = "auto";
    textarea.style.overflowY = "hidden";
    field.heightMode = "auto";
    persistTextareaHeight(advancedTextareaAutoHeight(textarea), "auto");
  };
  const rememberTextareaResizeStart = () => rememberAdvancedTextareaResizeStart(textarea);
  const captureTextareaManualResize = () => {
    const { changed, currentHeight } = captureAdvancedTextareaManualResize(textarea);
    if (!changed) {
      hooks.updateAdvancedFieldHighlight?.(node, field, textarea);
      return;
    }
    persistTextareaHeight(currentHeight, "manual");
  };
  installAdvancedTextareaResizeObserver(textarea, persistTextareaHeight);
  textareaWrap.append(textarea, createAdvancedTextareaResizeHandle(node, textarea, persistTextareaHeight, hooks));
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
  hooks.registerAdvancedAutocompleteInput?.(node, field, textarea);
  requestAnimationFrame(() => {
    setAdvancedTextareaHeight(node, textarea, field.height || 72, {
      mode: field.heightMode === "manual" ? "manual" : "auto",
      syncField: false,
      refreshHighlight: false,
    }, hooks);
    hooks.updateAdvancedFieldHighlight?.(node, field, textarea);
    updateFieldHighlight();
    hooks.scheduleAdvancedLayout?.(node, "render");
  });

  header.append(label, tools);
  block.append(header, textareaWrap);
  return block;
}

function addAdvancedField(node, pane, type, hooks = {}) {
  const fields = getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [];
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
  hooks.writeAdvancedFields?.(node, fields, { render: true });
}

function createAdvancedPane(node, pane, titleKey, hooks = {}) {
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
    const currentFields = getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [];
    button.disabled = (type === "naia" && hasAdvancedNaia(currentFields, pane))
      || (type === "trigger" && hasPositiveTrigger(currentFields));
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      addAdvancedField(node, pane, type, hooks);
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

  const fields = advancedPaneFields(getAdvancedFields(node) || hooks.parseAdvancedFields?.(node) || [], pane);
  if (!fields.length) {
    const empty = document.createElement("div");
    empty.className = "easyuse-anima-empty-pane";
    empty.textContent = psText("advanced.noFields");
    section.append(empty);
  } else {
    for (const field of fields) {
      section.append(createAdvancedFieldElement(node, field, hooks));
    }
  }
  return section;
}

export {
  addAdvancedField,
  createAdvancedFieldElement,
  createAdvancedPane,
  setAdvancedTextareaHeight,
  syncAdvancedTextareaHeightsForWidth,
};
