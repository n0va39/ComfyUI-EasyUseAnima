// @ts-check

// @ts-expect-error ComfyUI provides this host module at runtime.
import { app } from "../../../../scripts/app.js";
import {
  ADVANCED_CONTROL_WIDGETS,
  ADVANCED_WILDCARD_DEFAULT_MODE,
  ADVANCED_WILDCARD_MODES,
  ADVANCED_WILDCARD_SEED_CONTROLS,
  ADVANCED_RESOLUTION_BUCKETS,
  ARTIST_MIX_MODES,
  CUSTOM_ADVANCED_RESOLUTION_BUCKET,
  NAIA_ADVANCED_RESOLUTION_BUCKET,
} from "./constants.js";
import {
  closeAdvancedHelpPopovers,
  openAdvancedHelpPopover,
  protectAdvancedNativeControl,
  stopAdvancedControlEvent,
  updateAdvancedSummary,
} from "./dom.js";
import {
  advancedResolutionOptions,
  normalizeAdvancedResolutionBucket,
  normalizeAdvancedResolutionSize,
  normalizeAdvancedWidgetQueueValue,
  normalizeArtistMixMode,
} from "./schema.js";
import { ensureAdvancedStyle } from "./style.js";
import { psText } from "./text.js";
import {
  advancedResolutionLabel,
  clampAdvancedNumber,
  snapResolution32,
} from "./utils.js";
import {
  findInputEl,
  findWidget,
  isWidgetInputLinked,
} from "./widgets.js";
import {
  bindWildcardSeedInput,
} from "./wildcard_seed_contract.js";

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

function openAdvancedSettingsPopup(node, titleKey, subtitleKey, createBody, onClose = null, hooks = {}) {
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
    hooks.renderAdvancedEditor?.(node);
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

function createAdvancedControlGroup(node, groupId, labelKey, titleKey, summary, active, createBody, hooks = {}) {
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
    openAdvancedSettingsPopup(node, labelKey, subtitleKey, createBody, null, hooks);
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

function createAdvancedModGuidanceGroup(node, hooks = {}) {
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
    hooks,
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

function createAdvancedArtistMixGroup(node, hooks = {}) {
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
    hooks,
  );
}

function createAdvancedControlBar(node, hooks = {}) {
  const bar = document.createElement("div");
  bar.className = "easyuse-anima-advanced-controlbar";
  const modGuidanceGroup = createAdvancedModGuidanceGroup(node, hooks);
  const artistMixGroup = createAdvancedArtistMixGroup(node, hooks);
  if (modGuidanceGroup) {
    bar.append(modGuidanceGroup);
  }
  if (artistMixGroup) {
    bar.append(artistMixGroup);
  }
  return bar;
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
  const syncControl = () => {
    setAdvancedWidgetValue(node, "wildcard_seed_after_generate", normalizeAdvancedSeedControl(controlSelect.value));
    refreshSummary();
  };

  modeSelect.addEventListener("change", syncMode);
  bindWildcardSeedInput(
    seedInput,
    () => seedWidget.value,
    (seed) => setAdvancedWidgetValue(node, "wildcard_seed", seed),
    refreshSummary,
  );
  controlSelect.addEventListener("change", syncControl);

  body.append(
    createAdvancedControlRow("advanced.wildcard", modeSelect, "advanced.wildcardModeTitle"),
    createAdvancedControlRow("advanced.wildcardSeed", seedInput, "advanced.wildcardSeedTitle"),
    createAdvancedControlRow("advanced.wildcardSeedControl", controlSelect, "advanced.wildcardSeedControlTitle"),
  );
  return body;
}

function createAdvancedWildcardBar(node, hooks = {}) {
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
      null,
      hooks,
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

function createAdvancedResolutionSettingsBody(node, hooks = {}) {
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
      hooks.scheduleAdvancedLayout?.(node, "settings");
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
    hooks.scheduleAdvancedLayout?.(node, "settings");
    hooks.scheduleAdvancedHighlights?.(node, { classify: false });
  });

  body.append(
    createAdvancedControlRow("advanced.resolutionBucket", bucketSelect, "advanced.resolutionBucketTitle"),
    createAdvancedControlRow("advanced.resolutionSize", valueBox, "advanced.resolutionSizeTitle"),
  );
  return body;
}

function createAdvancedResolutionBar(node, hooks = {}) {
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
      () => createAdvancedResolutionSettingsBody(node, hooks),
      null,
      hooks,
    ),
  );
}

export {
  advancedCustomResolution,
  advancedModGuidanceSummary,
  advancedResolutionSummary,
  advancedWildcardSummary,
  createAdvancedControlBar,
  createAdvancedResolutionBar,
  createAdvancedWildcardBar,
  setAdvancedControlValue,
  setAdvancedWidgetValue,
};
