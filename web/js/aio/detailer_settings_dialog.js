// @ts-check

/**
 * @typedef {object} AioDetailerDialogControls
 * @property {(title: any, subtitle: any) => {backdrop: any, body: any, actions: any}} createDialog
 * @property {(section: any, label: any, control: any, tooltipKey?: string) => any} field
 * @property {(value: any) => any} checkbox
 * @property {(value: any) => any} textInput
 * @property {(value: any) => any} textareaInput
 * @property {(value: any, step?: string) => any} numberInput
 * @property {(options: any[], value: any) => any} selectInput
 * @property {(select: any, options: any[]) => any} reconcileSelectInput
 */

/**
 * @typedef {object} AioDetailerDialogText
 * @property {(value: any) => string} staticText
 * @property {(key: string) => string} get
 * @property {(key: string, values?: Record<string, any>) => string} format
 * @property {(element: any, key: string) => any} applyTooltip
 */

/**
 * @typedef {object} AioDetailerDialogSettingsCore
 * @property {any} defaultGenerationSettings
 * @property {any[]} fallbackSamplerNames
 * @property {any[]} fallbackSchedulerNames
 * @property {(defaults: any, current: any) => any} mergeDefaults
 * @property {(value: any, fallback: number, min: number, max: number) => number} clampNumber
 * @property {(order: any, detailer?: any) => string[]} normalizeDetailerOrder
 * @property {(targetName: string) => boolean} isCustomDetailerTargetName
 * @property {(order: string[], detailer: any) => string} nextDetailerTargetName
 * @property {(targetName: string) => any} detailerTargetDefaults
 * @property {(targetName: string, target: any, index?: number) => string} detailerTargetTitle
 */

/**
 * @typedef {object} AioDetailerDialogNodeAdapter
 * @property {string} generatorSettingsWidget
 * @property {(node: any, name: string) => any} findWidget
 * @property {(node: any) => any} getSettings
 * @property {(node: any, name: string, fallback: any[]) => any[]} widgetOptions
 * @property {(dependencyKey: string, inputName: string, current: any, fallback?: any[]) => any[]} nodeInputChoiceOptions
 * @property {(node: any, widget: any, settings: any) => void} writeSettings
 * @property {(node: any) => void} renderPanel
 */

/**
 * @typedef {object} AioDetailerDialogDependencyAdapter
 * @property {(key: string) => boolean} available
 * @property {(key: string) => string} pack
 * @property {(control: any, missing: boolean, message?: string) => void} markMissingControl
 * @property {(backend: string, keys: string[]) => boolean} notifyMissing
 * @property {(options?: Record<string, any>) => Promise<any>} load
 */

/**
 * @typedef {object} AioDetailerSettingsDialogDependencies
 * @property {any} document
 * @property {AioDetailerDialogControls} controls
 * @property {AioDetailerDialogText} text
 * @property {AioDetailerDialogSettingsCore} settingsCore
 * @property {(title: any, values: any, defaults: any) => {section: any, values: () => any, setIntegratedMode?: (isIntegrated: boolean) => void}} stageOptimizationEditor
 * @property {AioDetailerDialogNodeAdapter} nodeAdapter
 * @property {AioDetailerDialogDependencyAdapter} dependencyAdapter
 */

/**
 * Own the Detailer settings dialog, target editor, tab order, custom-target,
 * dependency-lock, and apply/cancel lifecycle. Stage optimization, extension
 * registration, panel rendering, dependency discovery, and storage are adapters.
 *
 * @param {AioDetailerSettingsDialogDependencies} dependencies
 * @returns {(node: any) => void}
 */
export function aioCreateDetailerSettingsDialog(dependencies) {
  const {
    document,
    controls,
    text,
    settingsCore,
    stageOptimizationEditor: createStageOptimizationEditor,
    nodeAdapter,
    dependencyAdapter,
  } = dependencies;
  const {
    createDialog,
    field,
    checkbox,
    textInput,
    textareaInput,
    numberInput,
    selectInput,
    reconcileSelectInput,
  } = controls;
  const {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
    applyTooltip,
  } = text;
  const {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,
    fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,
    mergeDefaults,
    clampNumber: clampGeneratorNumber,
    normalizeDetailerOrder,
    isCustomDetailerTargetName,
    nextDetailerTargetName,
    detailerTargetDefaults,
    detailerTargetTitle,
  } = settingsCore;
  const {
    generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
    findWidget,
    getSettings: generatorSettings,
    widgetOptions,
    nodeInputChoiceOptions,
    writeSettings,
    renderPanel: renderGeneratorPanel,
  } = nodeAdapter;
  const {
    available: optionalDependencyAvailable,
    pack: optionalDependencyPack,
    markMissingControl: aioMarkMissingDependencyControl,
    notifyMissing: notifyMissingDependency,
    load: loadGeneratorOptionalDependencies,
  } = dependencyAdapter;

  function createDetailerTargetEditor(node, title, values, defaults, onLabelChange = null) {
    const target = mergeDefaults(defaults, values || {});
    const section = document.createElement("section");
    section.className = "easyuse-anima-aio-detailer-target-panel";
    const header = document.createElement("div");
    header.className = "easyuse-anima-aio-node-stage-mini-header";
    header.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText(title) }));
    section.append(header);
    const labelInput = field(
      section,
      "Block name",
      textInput(target.label || defaults.label || title),
      "tip.detailerName",
    );
    labelInput.addEventListener("input", () => onLabelChange?.());
    const enabled = field(section, "Enable", checkbox(target.enabled));

    const detect = document.createElement("div");
    detect.className = "easyuse-anima-aio-subsection";
    detect.append(Object.assign(document.createElement("h4"), { textContent: aioStaticText("SAM3 Detect") }));
    const detectPrompt = field(detect, "Prompt", textInput(target.detect_prompt));
    const detectCount = field(detect, "Count", numberInput(target.detect_count, "1"));
    const threshold = field(detect, "Threshold", numberInput(target.threshold, "0.01"));
    const refine = field(detect, "Refine", numberInput(target.refine_iterations, "1"));
    const individual = field(detect, "Individual", checkbox(target.individual_masks));
    const combined = field(detect, "Combined", checkbox(target.combined));
    section.append(detect);

    const segs = document.createElement("div");
    segs.className = "easyuse-anima-aio-subsection";
    segs.append(Object.assign(document.createElement("h4"), { textContent: aioStaticText("MaskToSEGS") }));
    const cropFactor = field(segs, "Crop factor", numberInput(target.crop_factor, "0.1"));
    const bboxFill = field(segs, "BBox fill", checkbox(target.bbox_fill));
    const dropSize = field(segs, "Drop size", numberInput(target.drop_size, "1"));
    const contourFill = field(segs, "Contour fill", checkbox(target.contour_fill));
    section.append(segs);

    const detail = document.createElement("div");
    detail.className = "easyuse-anima-aio-subsection";
    detail.append(Object.assign(document.createElement("h4"), { textContent: aioStaticText("Impact Detailer") }));
    const guideSize = field(detail, "Guide size", numberInput(target.guide_size, "8"));
    const guideSizeFor = field(
      detail,
      "Guide size basis",
      selectInput([
        { value: "bbox", label: "bbox" },
        { value: "crop_region", label: "crop_region" },
      ], target.guide_size_for ? "bbox" : "crop_region"),
    );
    const maxSize = field(detail, "Max size", numberInput(target.max_size, "8"));
    const steps = field(detail, "Steps", numberInput(target.steps, "1"));
    steps.min = "1";
    steps.max = "75";
    const inheritSampler = field(
      detail,
      "Follow main sampler",
      checkbox(target.inherit_sampler_settings),
      "tip.detailerFollow",
    );
    const cfg = field(detail, "CFG", numberInput(target.cfg, "0.1"));
    cfg.min = "1";
    cfg.max = "10";
    const samplerName = field(detail, "Sampler", selectInput(widgetOptions(node, "sampler_name", GENERATOR_FALLBACK_SAMPLER_NAMES), target.sampler_name));
    const scheduler = field(detail, "Scheduler", selectInput(widgetOptions(node, "scheduler", GENERATOR_FALLBACK_SCHEDULER_NAMES), target.scheduler));
    const denoise = field(detail, "Denoise", numberInput(target.denoise, "0.01"));
    const feather = field(detail, "Feather", numberInput(target.feather, "1"));
    const noiseMask = field(detail, "Noise mask", checkbox(target.noise_mask));
    const forceInpaint = field(detail, "Force inpaint", checkbox(target.force_inpaint));
    const wildcard = field(detail, "Wildcard", textareaInput(target.wildcard));
    const noiseMaskFeather = field(detail, "Mask feather", numberInput(target.noise_mask_feather, "1"));
    const cycle = field(detail, "Cycle", numberInput(target.cycle, "1"));
    const alignment = field(detail, "Alignment", selectInput(["impact", "none", "32", "64"], target.alignment || "32"));
    const inpaintModel = field(detail, "Inpaint model", checkbox(target.inpaint_model));
    const tiledEncode = field(detail, "Tiled encode", checkbox(target.tiled_encode));
    const tiledDecode = field(detail, "Tiled decode", checkbox(target.tiled_decode));
    const optimization = createStageOptimizationEditor(`${title} Optimization`, target, defaults);
    const updateInheritedRows = () => {
      const display = inheritSampler.checked ? "none" : "";
      for (const control of [cfg, samplerName, scheduler]) {
        if (control?.parentElement) {
          control.parentElement.style.display = display;
        }
      }
    };
    inheritSampler.addEventListener("change", updateInheritedRows);
    updateInheritedRows();
    section.append(detail);

    section.append(optimization.section);

    return {
      section,
      label() {
        return String(labelInput.value || defaults.label || title).trim() || title;
      },
      values() {
        const optimized = optimization.values();
        return {
          ...target,
          label: String(labelInput.value || defaults.label || title).trim() || title,
          enabled: enabled.checked,
          detect_prompt: detectPrompt.value || defaults.detect_prompt,
          detect_count: Number(detectCount.value || defaults.detect_count),
          threshold: Number(threshold.value || defaults.threshold),
          refine_iterations: Number(refine.value || defaults.refine_iterations),
          individual_masks: individual.checked,
          combined: combined.checked,
          crop_factor: Number(cropFactor.value || defaults.crop_factor),
          bbox_fill: bboxFill.checked,
          drop_size: Number(dropSize.value || defaults.drop_size),
          contour_fill: contourFill.checked,
          guide_size: Number(guideSize.value || defaults.guide_size),
          guide_size_for: guideSizeFor.value === "bbox",
          max_size: Number(maxSize.value || defaults.max_size),
          steps: Math.trunc(clampGeneratorNumber(steps.value, defaults.steps, 1, 75)),
          inherit_sampler_settings: inheritSampler.checked,
          cfg: clampGeneratorNumber(cfg.value, defaults.cfg, 1, 10),
          sampler_name: samplerName.value || defaults.sampler_name,
          scheduler: scheduler.value || defaults.scheduler,
          denoise: clampGeneratorNumber(denoise.value, defaults.denoise, 0, 1),
          feather: Number(feather.value || defaults.feather),
          noise_mask: noiseMask.checked,
          force_inpaint: forceInpaint.checked,
          wildcard: String(wildcard.value || ""),
          cycle: Number(cycle.value || defaults.cycle),
          alignment: alignment.value || "32",
          inpaint_model: inpaintModel.checked,
          noise_mask_feather: Number(noiseMaskFeather.value || defaults.noise_mask_feather || 0),
          tiled_encode: tiledEncode.checked,
          tiled_decode: tiledDecode.checked,
          ...optimized,
        };
      },
    };
  }

  function openDetailerSettings(node) {
    const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
    const settings = generatorSettings(node);
    const detailer = mergeDefaults(DEFAULT_GENERATION_SETTINGS.detailer, settings.detailer || {});
    const { backdrop, body, actions } = createDialog(
      "Detailer Settings",
      "SAM3 detection and Impact detailer settings are saved with the node."
    );
    body.classList.add("easyuse-anima-aio-one-column");
    let closed = false;
    const main = document.createElement("section");
    main.className = "easyuse-anima-aio-section full";
    main.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Detailer") }));
    const enabled = field(main, "Enable detailer", checkbox(detailer.enabled));
    const checkpoint = field(
      main,
      "SAM3 checkpoint",
      selectInput(
        nodeInputChoiceOptions(
          "checkpointLoader",
          "ckpt_name",
          detailer.sam3.checkpoint,
          [detailer.sam3.checkpoint],
        ),
        detailer.sam3.checkpoint,
      ),
    );
    const dependencyWarning = document.createElement("div");
    dependencyWarning.className = "easyuse-anima-aio-warning";
    dependencyWarning.hidden = true;
    main.append(dependencyWarning);
    body.append(main);

    const currentOrder = normalizeDetailerOrder(detailer.order, detailer);
    let activeTargetName = currentOrder[0] || "face";
    const tabsSection = document.createElement("section");
    tabsSection.className = "easyuse-anima-aio-section full";
    tabsSection.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Detailer Blocks") }));
    const addBlock = document.createElement("button");
    addBlock.type = "button";
    addBlock.className = "easyuse-anima-aio-add-row";
    addBlock.textContent = aioText("button.addDetailerBlock");
    applyTooltip(addBlock, "tip.addDetailerBlock");
    const tabBar = document.createElement("div");
    tabBar.className = "easyuse-anima-aio-tabs";
    const tabPanel = document.createElement("div");
    tabPanel.className = "easyuse-anima-aio-tab-panel";
    tabsSection.append(addBlock, tabBar, tabPanel);
    body.append(tabsSection);

    let editors = {};
    const createEditor = (targetName, values = null) => {
      const defaults = detailerTargetDefaults(targetName);
      const targetValues = mergeDefaults(defaults, values || detailer[targetName] || {});
      return createDetailerTargetEditor(
        node,
        detailerTargetTitle(targetName, targetValues),
        targetValues,
        defaults,
        renderDetailerTabs,
      );
    };
    const moveTarget = (targetName, delta) => {
      const index = currentOrder.indexOf(targetName);
      const nextIndex = index + delta;
      if (index < 0 || nextIndex < 0 || nextIndex >= currentOrder.length) {
        return;
      }
      [currentOrder[index], currentOrder[nextIndex]] = [currentOrder[nextIndex], currentOrder[index]];
      renderDetailerTabs();
    };
    const selectTarget = (targetName) => {
      activeTargetName = targetName;
      renderDetailerTabs();
    };
    const removeTarget = (targetName) => {
      if (!isCustomDetailerTargetName(targetName)) {
        return;
      }
      const index = currentOrder.indexOf(targetName);
      if (index < 0) {
        return;
      }
      currentOrder.splice(index, 1);
      delete editors[targetName];
      if (activeTargetName === targetName) {
        activeTargetName = currentOrder[Math.min(index, currentOrder.length - 1)] || "face";
      }
      renderDetailerTabs();
    };
    const addTarget = () => {
      const targetName = nextDetailerTargetName(currentOrder, detailer);
      const defaults = detailerTargetDefaults(targetName);
      const targetValues = {
        ...defaults,
        enabled: true,
      };
      currentOrder.push(targetName);
      editors[targetName] = createEditor(targetName, targetValues);
      activeTargetName = targetName;
      renderDetailerTabs();
    };
    addBlock.addEventListener("click", addTarget);
    function renderDetailerTabs() {
      tabBar.replaceChildren();
      for (const [index, targetName] of currentOrder.entries()) {
        const editor = editors[targetName];
        if (!editor) {
          continue;
        }
        const tab = document.createElement("div");
        tab.className = "easyuse-anima-aio-tab";
        tab.classList.toggle("active", targetName === activeTargetName);
        tab.tabIndex = 0;
        tab.setAttribute("role", "button");
        tab.setAttribute("aria-selected", targetName === activeTargetName ? "true" : "false");
        applyTooltip(tab, "tip.detailerBlock");
        const label = document.createElement("span");
        label.className = "easyuse-anima-aio-tab-label";
        label.textContent = editor.label();
        const tools = document.createElement("span");
        tools.className = "easyuse-anima-aio-tab-tools";
        const moveLeft = document.createElement("button");
        moveLeft.type = "button";
        moveLeft.textContent = "<";
        moveLeft.disabled = index === 0;
        applyTooltip(moveLeft, "tip.detailerOrder");
        const moveRight = document.createElement("button");
        moveRight.type = "button";
        moveRight.textContent = ">";
        moveRight.disabled = index === currentOrder.length - 1;
        applyTooltip(moveRight, "tip.detailerOrder");
        moveLeft.addEventListener("click", (event) => {
          event.stopPropagation();
          moveTarget(targetName, -1);
        });
        moveRight.addEventListener("click", (event) => {
          event.stopPropagation();
          moveTarget(targetName, 1);
        });
        const remove = document.createElement("button");
        remove.type = "button";
        remove.textContent = "x";
        remove.disabled = !isCustomDetailerTargetName(targetName);
        applyTooltip(remove, "button.remove");
        remove.addEventListener("click", (event) => {
          event.stopPropagation();
          removeTarget(targetName);
        });
        tools.append(moveLeft, moveRight, remove);
        tab.append(label, tools);
        tab.addEventListener("click", () => selectTarget(targetName));
        tab.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectTarget(targetName);
          }
        });
        tabBar.append(tab);
      }
      if (!editors[activeTargetName]) {
        activeTargetName = currentOrder[0] || "face";
      }
      tabPanel.replaceChildren(editors[activeTargetName]?.section || document.createElement("div"));
    }
    editors = Object.fromEntries(currentOrder.map((targetName) => [targetName, createEditor(targetName)]));
    renderDetailerTabs();
    const refreshDetailerDependencyLocks = () => {
      const missingPacks = [];
      if (!optionalDependencyAvailable("impactDetailer")) {
        missingPacks.push(optionalDependencyPack("impactDetailer"));
      }
      if (!optionalDependencyAvailable("impactMaskToSegs")) {
        missingPacks.push(optionalDependencyPack("impactMaskToSegs"));
      }
      const missing = missingPacks.length > 0;
      const message = missing
        ? aioFormat("warning.optionalDependencyMissing", {
            backend: "Detailer",
            pack: [...new Set(missingPacks)].join(", "),
          })
        : "";
      aioMarkMissingDependencyControl(enabled, missing, message);
      if (missing && enabled.checked) {
        enabled.checked = false;
      }
      dependencyWarning.hidden = !missing;
      dependencyWarning.textContent = message;
    };
    enabled.addEventListener("change", () => {
      if (enabled.checked) {
        const missingKeys = ["impactDetailer", "impactMaskToSegs"]
          .filter((key) => !optionalDependencyAvailable(key));
        if (missingKeys.length) {
          notifyMissingDependency("Detailer", missingKeys);
          enabled.checked = false;
        }
      }
      refreshDetailerDependencyLocks();
    });
    refreshDetailerDependencyLocks();
    loadGeneratorOptionalDependencies().then(() => {
      if (closed || backdrop.isConnected === false) {
        return;
      }
      reconcileSelectInput(
        checkpoint,
        nodeInputChoiceOptions(
          "checkpointLoader",
          "ckpt_name",
          checkpoint.value,
          [checkpoint.value],
        ),
      );
      refreshDetailerDependencyLocks();
    });

    const cancel = document.createElement("button");
    cancel.textContent = aioText("button.cancel");
    const apply = document.createElement("button");
    apply.className = "primary";
    apply.textContent = aioText("button.apply");
    actions.append(cancel, apply);
    cancel.addEventListener("click", () => {
      closed = true;
      backdrop.remove();
    });
    apply.addEventListener("click", () => {
      const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
      const detailerEnabled = enabled.checked
        && optionalDependencyAvailable("impactDetailer")
        && optionalDependencyAvailable("impactMaskToSegs");
      const nextDetailer = {
        ...next.detailer,
        enabled: detailerEnabled,
        sam3: {
          context: "load_checkpoint",
          checkpoint: checkpoint.value || "sam3.1_multiplex_fp16.safetensors",
        },
      };
      for (const targetName of Object.keys(nextDetailer)) {
        if (isCustomDetailerTargetName(targetName)) {
          delete nextDetailer[targetName];
        }
      }
      for (const targetName of currentOrder) {
        const editor = editors[targetName];
        if (!editor) {
          continue;
        }
        const values = editor.values();
        if (!detailerEnabled) {
          values.enabled = false;
        }
        nextDetailer[targetName] = values;
      }
      nextDetailer.order = normalizeDetailerOrder(currentOrder, nextDetailer);
      next.detailer = nextDetailer;
      writeSettings(node, widget, next);
      renderGeneratorPanel(node);
      closed = true;
      backdrop.remove();
    });
  }

  return openDetailerSettings;
}
