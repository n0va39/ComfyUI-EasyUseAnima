// @ts-check

import {
  PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET,
  PROMPT_STUDIO_RESOLUTION_BUCKETS,
  PROMPT_STUDIO_VARIANT_FIELD_LABELS as REGIONAL_FIELD_LABELS,
  PROMPT_STUDIO_VARIANT_FIELD_TYPES as REGIONAL_FIELD_TYPES,
  PROMPT_STUDIO_WILDCARD_DEFAULT_MODE,
  PROMPT_STUDIO_WILDCARD_MODES,
  PROMPT_STUDIO_WILDCARD_SEED_CONTROLS,
} from "./constants.js";
import {
  normalizeResolutionBucket,
  normalizeResolutionSize,
  resolutionLabel,
  resolutionOptions,
  snapResolution32,
} from "./resolution.js";
import {
  createDefaultRegionalFields,
  normalizeRegionalField,
  normalizeRegionalMaskIds,
} from "./schema.js";
import {
  scheduleRegionalNodeFrame,
} from "./lifecycle.js";
import {
  bindWildcardSeedInput,
} from "../wildcard_seed_contract.js";
import { disposeExternalAutocompleteInputs } from "../../autocomplete/entry_lifecycle.js";

/**
 * Move a field within its current pane without changing its id or crossing the
 * positive/negative boundary. Swapping global positions preserves any mixed
 * legacy ordering while socket identity remains id-based.
 *
 * @param {any[]} fields
 * @param {string} fieldId
 * @param {number} direction
 */
function moveRegionalFieldInPane(fields, fieldId, direction) {
  const currentIndex = fields.findIndex((field) => field.id === fieldId);
  if (currentIndex < 0) {
    return false;
  }
  const pane = fields[currentIndex].pane;
  const paneIndices = fields
    .map((field, index) => (field.pane === pane ? index : -1))
    .filter((index) => index >= 0);
  const paneIndex = paneIndices.indexOf(currentIndex);
  const targetPaneIndex = paneIndex + Math.sign(direction);
  if (paneIndex < 0 || targetPaneIndex < 0 || targetPaneIndex >= paneIndices.length) {
    return false;
  }
  const targetIndex = paneIndices[targetPaneIndex];
  [fields[currentIndex], fields[targetIndex]] = [fields[targetIndex], fields[currentIndex]];
  return true;
}

/**
 * @param {any} runtime
 * @param {any} layout
 * @param {any} maskEditor
 * @param {{
 *   createPromptStudioActionButton: (label: string, title: string, onClick: (event?: any) => void) => any,
 *   promptStudioFieldIndexLabel: (fields: any[], field: any) => string,
 *   promptStudioFieldLabel: (field: any) => string,
 *   promptStudioText: (key: string) => string,
 *   registerPromptStudioTextarea: (node: any, field: any, textarea: any, options: any) => void,
 *   schedulePromptStudioFieldHighlight: (node: any, field: any, textarea: any, options: any) => void,
 *   updatePromptStudioFieldHighlight: (node: any, field: any, textarea: any, tokens: any, force: boolean, namespace: string) => void,
 * }} hooks
 */
function createRegionalFieldEditor(runtime, layout, maskEditor, hooks) {
  /** @param {any} value */
  function normalizeWildcardMode(value) {
    return PROMPT_STUDIO_WILDCARD_MODES.includes(String(value || ""))
      ? String(value)
      : PROMPT_STUDIO_WILDCARD_DEFAULT_MODE;
  }

  /** @param {any} mode */
  function wildcardModeTitle(mode) {
    const modeKey = {
      "일반 채우기": "populate",
      "고정": "fixed",
      "순차": "sequential",
      "재현": "reproduce",
    }[normalizeWildcardMode(mode)];
    return hooks.promptStudioText(`advanced.wildcardMode.${modeKey}Title`);
  }

  /** @param {any} value */
  function normalizeSeedControl(value) {
    return PROMPT_STUDIO_WILDCARD_SEED_CONTROLS.includes(String(value || ""))
      ? String(value)
      : "fixed";
  }

  /** @param {string} label @param {string} title @param {(event?: any) => void} onClick */
  function createButton(label, title, onClick) {
    return hooks.createPromptStudioActionButton(label, title, onClick);
  }

  /** @param {any} node */
  function createRegionalWildcardBar(node) {
    const modeWidget = runtime.findWidget(node, "wildcard_mode");
    const seedWidget = runtime.findWidget(node, "wildcard_seed");
    const controlWidget = runtime.findWidget(node, "wildcard_seed_after_generate");
    if (!modeWidget || !seedWidget || !controlWidget) {
      return document.createDocumentFragment();
    }

    const row = document.createElement("div");
    row.className = "easyuse-anima-advanced-wildcardbar";
    const modeSelect = document.createElement("select");
    modeSelect.setAttribute("aria-label", hooks.promptStudioText("advanced.wildcard"));
    const modeValue = normalizeWildcardMode(modeWidget.value);
    const selectedModeTitle = wildcardModeTitle(modeValue);
    row.title = `${selectedModeTitle}\n${hooks.promptStudioText("advanced.wildcardTitle")}`;
    modeSelect.title = selectedModeTitle;
    modeSelect.setAttribute("aria-description", selectedModeTitle);
    for (const mode of PROMPT_STUDIO_WILDCARD_MODES) {
      const option = document.createElement("option");
      option.value = mode;
      option.textContent = mode;
      option.title = wildcardModeTitle(mode);
      option.selected = mode === modeValue;
      modeSelect.append(option);
    }

    const seedInput = document.createElement("input");
    seedInput.type = "number";
    seedInput.value = String(seedWidget.value ?? "0");
    seedInput.setAttribute("aria-label", hooks.promptStudioText("advanced.wildcardSeed"));
    seedInput.title = hooks.promptStudioText("advanced.wildcardSeedTitle");
    seedInput.setAttribute("aria-description", seedInput.title);

    const controlSelect = document.createElement("select");
    controlSelect.setAttribute(
      "aria-label",
      hooks.promptStudioText("advanced.wildcardSeedControl"),
    );
    controlSelect.title = hooks.promptStudioText("advanced.wildcardSeedControlTitle");
    controlSelect.setAttribute("aria-description", controlSelect.title);
    const controlValue = modeValue === "순차"
      ? "increment"
      : normalizeSeedControl(controlWidget.value);
    for (const control of PROMPT_STUDIO_WILDCARD_SEED_CONTROLS) {
      const option = document.createElement("option");
      option.value = control;
      option.textContent = control;
      option.selected = control === controlValue;
      controlSelect.append(option);
    }
    controlSelect.disabled = modeValue === "순차";

    const syncMode = () => {
      const nextMode = normalizeWildcardMode(modeSelect.value);
      runtime.setRegionalWidgetValue(node, "wildcard_mode", nextMode);
      if (nextMode === "순차") {
        runtime.setRegionalWidgetValue(
          node,
          "wildcard_seed_after_generate",
          "increment",
        );
      }
      renderRegionalEditor(node);
    };
    const syncControl = () => {
      runtime.setRegionalWidgetValue(
        node,
        "wildcard_seed_after_generate",
        normalizeSeedControl(controlSelect.value),
      );
    };

    modeSelect.addEventListener("change", syncMode);
    bindWildcardSeedInput(
      seedInput,
      () => seedWidget.value,
      (seed) => runtime.setRegionalWidgetValue(node, "wildcard_seed", seed),
    );
    controlSelect.addEventListener("change", syncControl);
    row.append(modeSelect, seedInput, controlSelect);
    return row;
  }

  /** @param {any} node */
  function createRegionalResolutionBar(node) {
    const bucketWidget = runtime.findWidget(node, "resolution_bucket");
    const sizeWidget = runtime.findWidget(node, "resolution_size");
    if (!bucketWidget || !sizeWidget) {
      return document.createDocumentFragment();
    }

    const bucketValue = normalizeResolutionBucket(bucketWidget.value);
    const custom = runtime.customResolution(node);
    const sizeValue = bucketValue === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET
      ? resolutionLabel(custom.width, custom.height)
      : normalizeResolutionSize(bucketValue, sizeWidget.value);
    if (bucketWidget.value !== bucketValue) {
      runtime.setRegionalWidgetValue(node, "resolution_bucket", bucketValue);
    }
    if (sizeWidget.value !== sizeValue) {
      runtime.setRegionalWidgetValue(node, "resolution_size", sizeValue);
    }

    const row = document.createElement("div");
    row.className = "easyuse-anima-advanced-resolutionbar";
    row.title = hooks.promptStudioText("advanced.resolutionTitle");

    const bucketSelect = document.createElement("select");
    bucketSelect.setAttribute(
      "aria-label",
      hooks.promptStudioText("advanced.resolutionBucket"),
    );
    for (const bucket of Object.keys(PROMPT_STUDIO_RESOLUTION_BUCKETS)) {
      const option = document.createElement("option");
      option.value = bucket;
      option.textContent = bucket;
      option.selected = bucket === bucketValue;
      bucketSelect.append(option);
    }
    const customOption = document.createElement("option");
    customOption.value = PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET;
    customOption.textContent = PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET;
    customOption.selected = bucketValue === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET;
    bucketSelect.append(customOption);

    const valueBox = document.createElement("div");
    const renderPresetSelect = (bucket, selected) => {
      valueBox.innerHTML = "";
      valueBox.className = "";
      const sizeSelect = document.createElement("select");
      sizeSelect.setAttribute(
        "aria-label",
        hooks.promptStudioText("advanced.resolutionSize"),
      );
      for (const label of resolutionOptions(bucket)) {
        const option = document.createElement("option");
        option.value = label;
        option.textContent = label;
        option.selected = label === selected;
        sizeSelect.append(option);
      }
      sizeSelect.addEventListener("change", () => {
        runtime.setRegionalWidgetValue(
          node,
          "resolution_size",
          normalizeResolutionSize(bucketSelect.value, sizeSelect.value),
        );
        runtime.updateRegionalConfigCanvas(node);
        layout.scheduleRegionalLayout(node, "settings");
      });
      valueBox.append(sizeSelect);
    };
    const renderCustomInputs = () => {
      valueBox.innerHTML = "";
      valueBox.className = "easyuse-anima-advanced-resolution-custom";
      const widthInput = document.createElement("input");
      widthInput.type = "number";
      widthInput.min = "32";
      widthInput.step = "32";
      widthInput.value = String(runtime.customResolution(node).width);
      widthInput.setAttribute(
        "aria-label",
        hooks.promptStudioText("advanced.customWidth"),
      );
      const separator = document.createElement("span");
      separator.textContent = "×";
      const heightInput = document.createElement("input");
      heightInput.type = "number";
      heightInput.min = "32";
      heightInput.step = "32";
      heightInput.value = String(runtime.customResolution(node).height);
      heightInput.setAttribute(
        "aria-label",
        hooks.promptStudioText("advanced.customHeight"),
      );
      const syncRaw = () => {
        runtime.setRegionalWidgetValue(
          node,
          "resolution_custom_width",
          widthInput.value,
        );
        runtime.setRegionalWidgetValue(
          node,
          "resolution_custom_height",
          heightInput.value,
        );
      };
      const normalize = () => {
        const width = snapResolution32(widthInput.value, 1024);
        const height = snapResolution32(heightInput.value, 1024);
        widthInput.value = String(width);
        heightInput.value = String(height);
        runtime.setCustomResolution(node, width, height, { normalize: true });
        layout.scheduleRegionalLayout(node, "settings");
      };
      widthInput.addEventListener("input", syncRaw);
      heightInput.addEventListener("input", syncRaw);
      widthInput.addEventListener("change", normalize);
      heightInput.addEventListener("change", normalize);
      widthInput.addEventListener("blur", normalize);
      heightInput.addEventListener("blur", normalize);
      valueBox.append(widthInput, separator, heightInput);
      runtime.setCustomResolution(
        node,
        widthInput.value,
        heightInput.value,
        { normalize: true },
      );
    };
    const fillSizeOptions = (bucket, selected) => {
      if (bucket === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET) {
        renderCustomInputs();
        return;
      }
      renderPresetSelect(bucket, selected);
    };
    fillSizeOptions(bucketValue, sizeValue);

    bucketSelect.addEventListener("change", () => {
      const nextBucket = normalizeResolutionBucket(bucketSelect.value);
      const nextSize = nextBucket === PROMPT_STUDIO_CUSTOM_RESOLUTION_BUCKET
        ? resolutionLabel(
          runtime.customResolution(node).width,
          runtime.customResolution(node).height,
        )
        : normalizeResolutionSize(nextBucket, sizeWidget.value);
      runtime.setRegionalWidgetValue(node, "resolution_bucket", nextBucket);
      runtime.setRegionalWidgetValue(node, "resolution_size", nextSize);
      fillSizeOptions(nextBucket, nextSize);
      runtime.updateRegionalConfigCanvas(node);
      layout.scheduleRegionalLayout(node, "settings");
      layout.scheduleRegionalFieldHighlights(node, false);
    });

    row.append(bucketSelect, valueBox);
    runtime.updateRegionalConfigCanvas(node);
    return row;
  }

  /** @param {any} node */
  function collectRegionalEditorFields(node) {
    const editor = node.__easyuseAnimaRegionalEditorEl;
    if (!editor) {
      return node.__easyuseAnimaRegionalFields || createDefaultRegionalFields();
    }
    const fields = [];
    for (const card of editor.querySelectorAll(".easyuse-anima-regional-field")) {
      const id = card.dataset.fieldId || "";
      const existing = (node.__easyuseAnimaRegionalFields || [])
        .find((field) => field.id === id) || {};
      const pane = card.dataset.pane || existing.pane || "positive";
      const enabled = card.querySelector("[data-role='enabled']")?.checked ?? true;
      const label = card.querySelector("[data-role='label']")?.value ?? existing.label ?? "";
      const type = card.querySelector("[data-role='type']")?.value ?? existing.type ?? "general";
      const text = card.querySelector("[data-role='text']")?.value ?? "";
      const maskControl = card.querySelector("[data-role='mask_ids']");
      let maskIds = [];
      if (maskControl instanceof HTMLSelectElement) {
        maskIds = Array.from(maskControl.selectedOptions).map((option) => option.value);
      } else if (maskControl) {
        maskIds = normalizeRegionalMaskIds(maskControl.dataset.maskIds);
      }
      fields.push(normalizeRegionalField({
        ...existing,
        id,
        pane,
        enabled,
        label,
        type,
        text,
        mask_ids: maskIds,
        height: Math.max(
          36,
          card.querySelector("[data-role='text']")?.offsetHeight
            || existing.height
            || 72,
        ),
      }, fields.length));
    }
    return fields;
  }

  /** @param {any} node @param {any} field */
  function moveField(node, field, direction) {
    const fields = collectRegionalEditorFields(node);
    if (!moveRegionalFieldInPane(fields, field.id, direction)) {
      return;
    }
    runtime.writeRegionalFields(node, fields);
    renderRegionalEditor(node);
  }

  /** @param {any} node @param {any} field */
  function createFieldCard(node, field) {
    const config = node.__easyuseAnimaRegionalConfig || runtime.defaultConfig(node);
    const fields = node.__easyuseAnimaRegionalFields || createDefaultRegionalFields();
    const samePane = fields.filter((item) => item.pane === field.pane);
    const paneIndex = samePane.findIndex((item) => item.id === field.id);
    const card = document.createElement("div");
    card.className = "easyuse-anima-advanced-field easyuse-anima-regional-field";
    card.classList.toggle("is-trigger", field.type === "trigger");
    card.classList.toggle("is-disabled", field.enabled === false);
    card.dataset.fieldId = field.id;
    card.dataset.pane = field.pane;

    const head = document.createElement("div");
    head.className = "easyuse-anima-field-header";

    const enabled = document.createElement("input");
    enabled.type = "checkbox";
    enabled.checked = field.enabled !== false;
    enabled.dataset.role = "enabled";
    enabled.title = "Include this field in prompt output";
    enabled.addEventListener("change", () => {
      runtime.writeRegionalFields(node, collectRegionalEditorFields(node));
      renderRegionalEditor(node);
    });

    const label = document.createElement("input");
    label.type = "text";
    label.value = field.label || "";
    label.dataset.role = "label";
    label.className = "easyuse-anima-regional-field-label-input";
    label.addEventListener("input", () => {
      runtime.writeRegionalFields(node, collectRegionalEditorFields(node));
    });

    const type = document.createElement("select");
    type.dataset.role = "type";
    type.className = "easyuse-anima-regional-field-type";
    for (const typeName of REGIONAL_FIELD_TYPES) {
      const option = document.createElement("option");
      option.value = typeName;
      option.textContent = REGIONAL_FIELD_LABELS[typeName] || typeName;
      option.selected = field.type === typeName;
      type.appendChild(option);
    }
    type.addEventListener("change", () => {
      runtime.writeRegionalFields(node, collectRegionalEditorFields(node));
      renderRegionalEditor(node);
    });

    const pane = document.createElement("span");
    pane.className = "easyuse-anima-regional-pane-badge";
    pane.textContent = field.pane === "negative" ? "negative" : "positive";

    const title = document.createElement("div");
    title.className = "easyuse-anima-field-label";
    const titleText = document.createElement("span");
    titleText.textContent = `${hooks.promptStudioFieldIndexLabel(fields, field)}. ${hooks.promptStudioFieldLabel(field)}`;
    title.append(enabled, titleText);

    const tools = document.createElement("div");
    tools.className = "easyuse-anima-field-tools";
    const moveUp = createButton(
      "↑",
      "Move this prompt field up",
      () => moveField(node, field, -1),
    );
    moveUp.disabled = paneIndex <= 0;
    const moveDown = createButton(
      "↓",
      "Move this prompt field down",
      () => moveField(node, field, 1),
    );
    moveDown.disabled = paneIndex >= samePane.length - 1;
    const remove = createButton("X", "Remove this prompt field", () => {
      const nextFields = collectRegionalEditorFields(node)
        .filter((item) => item.id !== field.id);
      runtime.writeRegionalFields(
        node,
        nextFields.length ? nextFields : createDefaultRegionalFields(),
      );
      renderRegionalEditor(node);
    });
    tools.append(label, type, pane, moveUp, moveDown, remove);

    head.append(title, tools);

    const textarea = document.createElement("textarea");
    const linked = runtime.regionalFieldInputLinked(node, field);
    const inputName = runtime.fieldSocketName(field);
    textarea.dataset.role = "text";
    textarea.dataset.easyuseAnimaPromptStudioVariantFieldId = field.id;
    textarea.value = runtime.regionalFieldDisplayText(node, field);
    textarea.placeholder = field.type === "artist"
      ? "@artist_tag"
      : field.type === "trigger" ? "trigger words" : "prompt tags";
    textarea.style.height = `${Math.max(44, field.height || 72)}px`;
    textarea.classList.toggle("is-linked", linked);
    textarea.title = linked
      ? "Connected STRING input can overwrite this prompt on queue."
      : "";
    const syncTextareaHeight = () => {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.max(44, textarea.scrollHeight)}px`;
    };
    hooks.registerPromptStudioTextarea(node, field, textarea, {
      namespace: "regional",
      onInput: () => {
        if (linked) {
          node.__easyuseAnimaRegionalFieldInputValues ||= {};
          node.__easyuseAnimaRegionalFieldInputValues[inputName] = textarea.value;
        }
        syncTextareaHeight();
        runtime.writeRegionalFields(node, collectRegionalEditorFields(node));
        layout.scheduleRegionalLayout(node);
      },
      onChange: () => {
        runtime.writeRegionalFields(node, collectRegionalEditorFields(node));
        layout.scheduleRegionalLayout(node);
      },
      onManualResize: (height) => {
        field.height = Math.max(44, height);
        runtime.writeRegionalFields(node, collectRegionalEditorFields(node));
      },
      scheduleLayout: () => layout.scheduleRegionalLayout(node),
    });

    const assignment = document.createElement("div");
    assignment.className = "easyuse-anima-regional-assignment";
    const socket = document.createElement("div");
    socket.textContent = `socket: ${runtime.fieldSocketName(field)}`;
    assignment.appendChild(socket);
    if (field.pane === "positive") {
      assignment.appendChild(
        maskEditor.createMaskSelectorButton(
          node,
          config,
          normalizeRegionalMaskIds(field.mask_ids),
        ),
      );
    } else {
      const negativeNote = document.createElement("div");
      negativeNote.textContent = "global";
      assignment.appendChild(negativeNote);
    }

    scheduleRegionalNodeFrame(node, `field-card:${field.id}`, () => {
      if (!textarea.isConnected) {
        return;
      }
      hooks.updatePromptStudioFieldHighlight(
        node,
        field,
        textarea,
        null,
        true,
        "regional",
      );
      hooks.schedulePromptStudioFieldHighlight(
        node,
        field,
        textarea,
        { namespace: "regional" },
      );
      runtime.writeRegionalFields(node, collectRegionalEditorFields(node));
      layout.scheduleRegionalLayout(node);
    }, { replace: true });

    card.append(head, textarea, assignment);
    return card;
  }

  /** @param {any} node @param {string} pane @param {string} [type] */
  function addRegionalField(node, pane, type = "general") {
    const fields = collectRegionalEditorFields(node);
    const count = fields.filter((field) => field.pane === pane).length + 1;
    const fieldType = pane === "negative" && type === "trigger" ? "general" : type;
    fields.push(normalizeRegionalField({
      id: `${pane}_${fieldType}_${Date.now().toString(36)}`,
      pane,
      type: fieldType,
      label: pane === "negative"
        ? `Negative Prompt ${count}`
        : `${REGIONAL_FIELD_LABELS[fieldType] || "Prompt"} ${count}`,
      text: "",
      height: 90,
      enabled: true,
      mask_ids: [],
    }, fields.length));
    runtime.writeRegionalFields(node, fields);
    renderRegionalEditor(node);
  }

  /** @param {string} label @param {string} title @param {(event?: any) => void} onClick */
  function createToolbarButton(label, title, onClick) {
    const button = createButton(label, title, onClick);
    button.className = "easyuse-anima-advanced-toggle";
    return button;
  }

  /** @param {any} node @param {string} pane @param {string} titleText */
  function createRegionalPane(node, pane, titleText) {
    const section = document.createElement("section");
    section.className = "easyuse-anima-advanced-pane";

    const header = document.createElement("div");
    header.className = "easyuse-anima-advanced-pane-title";
    const heading = document.createElement("span");
    heading.textContent = titleText;
    const actions = document.createElement("div");
    actions.className = "easyuse-anima-advanced-actions";
    const addButton = (type, label) => {
      actions.append(
        createButton(
          label,
          `Add ${label.replace(/^\+\s*/, "")}`,
          () => addRegionalField(node, pane, type),
        ),
      );
    };
    if (pane === "positive") {
      addButton("quality", "+ Quality");
      addButton("artist", "+ Artist");
      addButton("trigger", "+ Trigger");
    }
    addButton("general", "+ General");
    header.append(heading, actions);
    section.append(header);

    const fields = (node.__easyuseAnimaRegionalFields || createDefaultRegionalFields())
      .filter((item) => item.pane === pane);
    if (!fields.length) {
      const empty = document.createElement("div");
      empty.className = "easyuse-anima-empty-pane";
      empty.textContent = "No fields";
      section.append(empty);
    } else {
      for (const field of fields) {
        section.append(createFieldCard(node, field));
      }
    }
    return section;
  }

  /** @param {any} node */
  function renderRegionalEditor(node) {
    runtime.ensureRegionalWidgetValues(node);
    const editor = node.__easyuseAnimaRegionalEditorEl;
    if (!editor) {
      runtime.syncRegionalFieldInputs(
        node,
        node.__easyuseAnimaRegionalFields || createDefaultRegionalFields(),
      );
      return;
    }
    const fields = node.__easyuseAnimaRegionalFields || createDefaultRegionalFields();
    const config = node.__easyuseAnimaRegionalConfig || runtime.defaultConfig(node);
    maskEditor.closeMaskPopover(node);
    disposeExternalAutocompleteInputs(window, editor);
    editor.innerHTML = "";

    const toolbar = document.createElement("div");
    toolbar.className = "easyuse-anima-advanced-controlbar";
    toolbar.append(
      createToolbarButton(
        "Edit Masks",
        "Open numbered mask editor",
        () => maskEditor.openMaskEditor(node),
      ),
    );
    const summary = document.createElement("div");
    summary.className = "easyuse-anima-regional-summary";
    summary.textContent = `${config.masks?.length || 0} masks`;
    toolbar.appendChild(summary);
    editor.appendChild(toolbar);
    editor.append(
      createRegionalWildcardBar(node),
      createRegionalResolutionBar(node),
    );

    const panes = document.createElement("div");
    panes.className = "easyuse-anima-advanced-panes";
    panes.append(
      createRegionalPane(node, "positive", "Positive prompts"),
      createRegionalPane(node, "negative", "Negative prompts"),
    );
    editor.appendChild(panes);
    runtime.writeRegionalFields(node, fields);
    runtime.writeRegionalConfig(node, node.__easyuseAnimaRegionalConfig || config);
    layout.scheduleRegionalFieldHighlights(node, true);
    layout.scheduleRegionalLayout(node, "render");
  }

  return {
    addRegionalField,
    collectRegionalEditorFields,
    renderRegionalEditor,
  };
}

export {
  createRegionalFieldEditor,
  moveRegionalFieldInPane,
};
