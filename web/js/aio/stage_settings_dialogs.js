// @ts-check

/**
 * @typedef {object} AioStageDialogControls
 * @property {(title: any, subtitle: any) => {backdrop: any, body: any, actions: any}} createDialog
 * @property {(section: any, label: any, control: any, tooltipKey?: string) => any} field
 * @property {(value: any, step?: string) => any} numberInput
 * @property {(value: any) => any} checkbox
 * @property {(options: any[], value: any) => any} selectInput
 * @property {(select: any, options: any[]) => any} reconcileSelectInput
 */

/**
 * @typedef {object} AioStageDialogText
 * @property {(value: any) => string} staticText
 * @property {(key: string) => string} get
 * @property {(key: string, values?: Record<string, any>) => string} format
 */

/**
 * @typedef {object} AioStageDialogSettingsCore
 * @property {any} defaultGenerationSettings
 * @property {any[]} fallbackSamplerNames
 * @property {any[]} fallbackSchedulerNames
 * @property {(defaults: any, current: any) => any} mergeDefaults
 * @property {(value: any, fallback: number, min: number, max: number) => number} clampNumber
 * @property {(value: any) => any} normalizeUsduAutoTileRange
 */

/**
 * @typedef {object} AioStageDialogNodeAdapter
 * @property {string} generatorSettingsWidget
 * @property {(node: any, name: string) => any} findWidget
 * @property {(node: any) => any} getSettings
 * @property {(node: any, name: string, fallback: any[]) => any[]} widgetOptions
 * @property {(dependencyKey: string, inputName: string, current: any, fallback?: any[]) => any[]} nodeInputChoiceOptions
 * @property {(node: any, widget: any, settings: any) => void} writeSettings
 * @property {(node: any) => void} renderPanel
 */

/**
 * @typedef {object} AioStageDialogDependencyAdapter
 * @property {(key: string) => boolean} available
 * @property {(key: string) => string} pack
 * @property {(backend: string) => string[]} upscaleBackendMissingPacks
 * @property {(options?: Record<string, any>) => Promise<any>} load
 */

/**
 * @typedef {object} AioStageSettingsDialogDependencies
 * @property {any} document
 * @property {AioStageDialogControls} controls
 * @property {AioStageDialogText} text
 * @property {AioStageDialogSettingsCore} settingsCore
 * @property {AioStageDialogNodeAdapter} nodeAdapter
 * @property {AioStageDialogDependencyAdapter} dependencyAdapter
 */

/**
 * Own the Highres and Upscale settings dialog lifecycles plus their shared
 * stage-optimization editor. Extension registration, panel rendering,
 * optional-dependency discovery, and durable settings storage remain adapters.
 *
 * @param {AioStageSettingsDialogDependencies} dependencies
 * @returns {{
 *   createStageOptimizationEditor: (title: any, values: any, defaults: any) => any,
 *   openHighresSettings: (node: any) => void,
 *   openUpscaleSettings: (node: any) => void,
 * }}
 */
export function aioCreateStageSettingsDialogs(dependencies) {
  const {
    document,
    controls,
    text,
    settingsCore,
    nodeAdapter,
    dependencyAdapter,
  } = dependencies;
  const {
    createDialog,
    field,
    numberInput,
    checkbox,
    selectInput,
    reconcileSelectInput,
  } = controls;
  const {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
  } = text;
  const {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,
    fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,
    mergeDefaults,
    clampNumber: clampGeneratorNumber,
    normalizeUsduAutoTileRange: normalizeGeneratorUsduAutoTileRange,
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
    upscaleBackendMissingPacks,
    load: loadGeneratorOptionalDependencies,
  } = dependencyAdapter;

  function createStageOptimizationEditor(title, values, defaults) {
    const section = document.createElement("section");
    section.className = "easyuse-anima-aio-section";
    section.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText(title) }));
    const spectrumValues = mergeDefaults(defaults.spectrum || {}, values.spectrum || {});
    const correctionValues = mergeDefaults(defaults.dit_corrections || {}, values.dit_corrections || {});

    const spectrumEnabled = field(section, "Spectrum patch", checkbox(spectrumValues.enabled));
    const windowSize = field(section, "Window size", numberInput(spectrumValues.window_size, "0.25"));
    const flexWindow = field(section, "Flex window", numberInput(spectrumValues.flex_window, "0.05"));
    const warmupSteps = field(section, "Warmup", numberInput(spectrumValues.warmup_steps, "1"));
    const tailSteps = field(section, "Tail actual", numberInput(spectrumValues.tail_actual_steps, "1"));
    const blendW = field(section, "Blend W", numberInput(spectrumValues.blend_w, "0.05"));
    const chebyDegree = field(section, "Cheby", numberInput(spectrumValues.cheby_degree, "1"));
    const ridgeLambda = field(section, "Ridge lambda", numberInput(spectrumValues.ridge_lambda, "0.01"));
    const compatPolicy = field(
      section,
      "Compat",
      selectInput(["conservative", "legacy", "strict"], spectrumValues.compat_policy || "conservative")
    );

    const corrections = document.createElement("div");
    corrections.className = "easyuse-anima-aio-subsection";
    corrections.append(Object.assign(document.createElement("h4"), { textContent: aioStaticText("Spectrum DCW / Corrections") }));
    const correctionsEnabled = field(corrections, "Use corrections", checkbox(correctionValues.enabled));
    const dcwMode = field(corrections, "DCW mode", selectInput(["off", "manual", "auto"], correctionValues.dcw_mode || "off"));
    const dcwLambda = field(corrections, "DCW lambda", numberInput(correctionValues.dcw_lambda, "0.001"));
    const dcwBand = field(corrections, "DCW band", selectInput(["LL", "all", "HH", "LH+HL+HH"], correctionValues.dcw_band_mask || "LL"));
    const smcCfg = field(corrections, "SMC-CFG", checkbox(correctionValues.smc_cfg));
    const smcAlpha = field(corrections, "SMC alpha", numberInput(correctionValues.adaptive_smc_alpha, "0.01"));
    const smcLambda = field(corrections, "SMC lambda", numberInput(correctionValues.smc_cfg_lambda, "0.1"));
    const cfgpp = field(corrections, "CFG++", checkbox(correctionValues.cfgpp));
    const cfgppLambda = field(corrections, "CFG++ lambda", numberInput(correctionValues.cfgpp_lambda, "0.1"));
    const fsg = field(corrections, "FSG", checkbox(correctionValues.fsg));
    section.append(corrections);
    const dependencyWarning = document.createElement("div");
    dependencyWarning.className = "easyuse-anima-aio-warning";
    dependencyWarning.hidden = true;
    section.append(dependencyWarning);
    const refreshDependencyLocks = () => {
      const spectrumPatchMissing = !optionalDependencyAvailable("spectrumPatch");
      spectrumEnabled.disabled = spectrumPatchMissing;
      correctionsEnabled.disabled = spectrumPatchMissing;
      if (spectrumPatchMissing) {
        spectrumEnabled.checked = false;
        correctionsEnabled.checked = false;
        dependencyWarning.hidden = false;
        dependencyWarning.textContent = aioFormat("warning.optionalDependencyMissing", {
          backend: title,
          pack: optionalDependencyPack("spectrumPatch"),
        });
      } else {
        dependencyWarning.hidden = true;
        dependencyWarning.textContent = "";
      }
    };
    refreshDependencyLocks();
    loadGeneratorOptionalDependencies().then(refreshDependencyLocks);

    return {
      section,
      setIntegratedMode(isIntegrated) {
        if (spectrumEnabled?.parentElement) {
          spectrumEnabled.parentElement.style.display = isIntegrated ? "none" : "";
        }
        if (compatPolicy?.parentElement) {
          compatPolicy.parentElement.style.display = isIntegrated ? "none" : "";
        }
      },
      values() {
        return {
          spectrum: {
            enabled: spectrumEnabled.checked && !spectrumEnabled.disabled,
            window_size: Number(windowSize.value || defaults.spectrum.window_size || 2),
            flex_window: Number(flexWindow.value || defaults.spectrum.flex_window || 0.25),
            warmup_steps: Number(warmupSteps.value || defaults.spectrum.warmup_steps || 6),
            tail_actual_steps: Number(tailSteps.value || defaults.spectrum.tail_actual_steps || 3),
            blend_w: Number(blendW.value || defaults.spectrum.blend_w || 0.3),
            cheby_degree: Number(chebyDegree.value || defaults.spectrum.cheby_degree || 3),
            ridge_lambda: Number(ridgeLambda.value || defaults.spectrum.ridge_lambda || 0.1),
            history_size: Number(spectrumValues.history_size || defaults.spectrum.history_size || 100),
            one_sampler_only: !!spectrumValues.one_sampler_only,
            verbose: !!spectrumValues.verbose,
            compat_policy: compatPolicy.value || "conservative",
          },
          dit_corrections: {
            enabled: correctionsEnabled.checked && !correctionsEnabled.disabled,
            dcw_mode: dcwMode.value || "off",
            dcw_lambda: Number(dcwLambda.value || defaults.dit_corrections.dcw_lambda || 0.01),
            dcw_band_mask: dcwBand.value || "LL",
            dcw_calibrator: correctionValues.dcw_calibrator || "(auto-download default)",
            smc_cfg: smcCfg.checked,
            adaptive_smc_alpha: Number(smcAlpha.value || defaults.dit_corrections.adaptive_smc_alpha || 0),
            smc_cfg_lambda: Number(smcLambda.value || defaults.dit_corrections.smc_cfg_lambda || 6),
            cfgpp: cfgpp.checked,
            cfgpp_lambda: Number(cfgppLambda.value || defaults.dit_corrections.cfgpp_lambda || 0),
            fsg: fsg.checked,
            fsg_band_lo: Number(correctionValues.fsg_band_lo || defaults.dit_corrections.fsg_band_lo || 0.59),
            fsg_band_hi: Number(correctionValues.fsg_band_hi || defaults.dit_corrections.fsg_band_hi || 0.75),
            fsg_k: Number(correctionValues.fsg_k || defaults.dit_corrections.fsg_k || 3),
            fsg_d_sigma: Number(correctionValues.fsg_d_sigma || defaults.dit_corrections.fsg_d_sigma || 0.1),
            fsg_gamma: Number(correctionValues.fsg_gamma || defaults.dit_corrections.fsg_gamma || 0),
            replace_existing_cfg: !!correctionValues.replace_existing_cfg,
          },
        };
      },
    };
  }

  function openHighresSettings(node) {
    const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
    const settings = generatorSettings(node);
    const highres = mergeDefaults(DEFAULT_GENERATION_SETTINGS.highres, settings.highres || {});
    const mainBackendIsSpd = settings.sampler?.backend === "spectrum_spd_speed";
    const { backdrop, body, actions } = createDialog(
      "Highres Settings",
      "Image scaling and Highres resampling settings are saved with the node."
    );
    body.classList.add("easyuse-anima-aio-one-column");

    const image = document.createElement("section");
    image.className = "easyuse-anima-aio-section";
    image.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Image Scale") }));
    const enabled = field(image, "Enable highres", checkbox(highres.enabled));
    const scaleBy = field(image, "Scale by", numberInput(highres.scale_by, "0.01"));
    const upscaleMethod = field(image, "Method", selectInput(["bicubic", "nearest-exact", "bilinear", "area", "lanczos"], highres.upscale_method));
    const multiple = field(image, "Multiple", selectInput(["8", "16", "32", "64"], highres.multiple));
    const maxLongEdge = field(image, "Max long edge", numberInput(highres.max_long_edge, "32"));

    const sampler = document.createElement("section");
    sampler.className = "easyuse-anima-aio-section";
    sampler.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Highres Sampler") }));
    const steps = field(sampler, "Steps", numberInput(highres.steps, "1"));
    steps.min = "1";
    steps.max = "75";
    const effectiveInherit = !!highres.inherit_sampler_settings;
    const inheritSampler = field(
      sampler,
      "Follow main sampler",
      checkbox(effectiveInherit),
      "tip.highresFollow",
    );
    const dependencyWarning = document.createElement("div");
    dependencyWarning.className = "easyuse-anima-aio-warning";
    dependencyWarning.hidden = true;
    sampler.append(dependencyWarning);
    const cfg = field(sampler, "CFG", numberInput(highres.cfg, "0.1"));
    cfg.min = "1";
    cfg.max = "10";
    const samplerName = field(
      sampler,
      "Sampler",
      selectInput(widgetOptions(node, "sampler_name", GENERATOR_FALLBACK_SAMPLER_NAMES), highres.sampler_name)
    );
    const scheduler = field(
      sampler,
      "Scheduler",
      selectInput(widgetOptions(node, "scheduler", GENERATOR_FALLBACK_SCHEDULER_NAMES), highres.scheduler)
    );
    const denoise = field(sampler, "Denoise", numberInput(highres.denoise, "0.01"));
    const optimization = createStageOptimizationEditor("Highres Optimization", highres, DEFAULT_GENERATION_SETTINGS.highres);
    const updateInheritedRows = () => {
      const usesMain = inheritSampler.checked;
      const display = usesMain ? "none" : "";
      for (const control of [cfg, samplerName, scheduler]) {
        if (control?.parentElement) {
          control.parentElement.style.display = display;
        }
      }
    };
    const refreshDependencyLocks = () => {
      const messages = [];
      if (mainBackendIsSpd && inheritSampler.checked) {
        messages.push(aioText("text.highresSpdManualRequired"));
      }
      dependencyWarning.hidden = messages.length === 0;
      dependencyWarning.textContent = messages.join(" ");
      updateInheritedRows();
    };
    inheritSampler.addEventListener("change", refreshDependencyLocks);
    updateInheritedRows();
    refreshDependencyLocks();
    body.append(image, sampler, optimization.section);

    const cancel = document.createElement("button");
    cancel.textContent = aioText("button.cancel");
    const apply = document.createElement("button");
    apply.className = "primary";
    apply.textContent = aioText("button.apply");
    actions.append(cancel, apply);
    cancel.addEventListener("click", () => backdrop.remove());
    apply.addEventListener("click", () => {
      const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
      const optimized = optimization.values();
      next.highres = {
        ...next.highres,
        enabled: enabled.checked,
        scale_by: clampGeneratorNumber(scaleBy.value, DEFAULT_GENERATION_SETTINGS.highres.scale_by, 0.01, 8),
        upscale_method: upscaleMethod.value || "bicubic",
        multiple: multiple.value || "32",
        max_long_edge: Math.trunc(clampGeneratorNumber(maxLongEdge.value, 2560, 0, 16384)),
        steps: Math.trunc(clampGeneratorNumber(steps.value, 20, 1, 75)),
        inherit_sampler_settings: inheritSampler.checked,
        cfg: clampGeneratorNumber(cfg.value, 8, 1, 10),
        sampler_name: samplerName.value || "euler",
        scheduler: scheduler.value || "simple",
        denoise: clampGeneratorNumber(denoise.value, DEFAULT_GENERATION_SETTINGS.highres.denoise, 0, 1),
        ...optimized,
      };
      writeSettings(node, widget, next);
      renderGeneratorPanel(node);
      backdrop.remove();
    });
  }

  function openUpscaleSettings(node) {
    const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
    const settings = generatorSettings(node);
    const upscale = mergeDefaults(DEFAULT_GENERATION_SETTINGS.upscale, settings.upscale || {});
    const usdu = mergeDefaults(DEFAULT_GENERATION_SETTINGS.upscale.usdu, upscale.usdu || {});
    const resshift = mergeDefaults(DEFAULT_GENERATION_SETTINGS.upscale.resshift, upscale.resshift || {});
    const { backdrop, body, actions } = createDialog(
      "Upscale Settings",
      "Final-stage upscale runs after Detailer and before Save. Choose USDU or ResShift."
    );
    body.classList.add("easyuse-anima-aio-one-column");
    let closed = false;

    const main = document.createElement("section");
    main.className = "easyuse-anima-aio-section";
    main.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Image Scale") }));
    const enabled = field(main, "Enable upscale", checkbox(upscale.enabled), "tip.upscaleEnabled");
    const backend = field(
      main,
      "Upscale backend",
      selectInput(["usdu", "resshift"], upscale.backend || "usdu"),
      "tip.upscaleBackend",
    );
    const dependencyWarning = document.createElement("div");
    dependencyWarning.className = "easyuse-anima-aio-warning";
    dependencyWarning.hidden = true;
    main.append(dependencyWarning);

    const usduSection = document.createElement("section");
    usduSection.className = "easyuse-anima-aio-section";
    usduSection.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("USDU Upscale") }));
    const scaleBy = field(usduSection, "Scale by", numberInput(upscale.scale_by, "0.05"), "tip.upscaleScale");
    scaleBy.min = "0.05";
    scaleBy.max = "4";
    const upscaleModel = field(
      usduSection,
      "Upscale model",
      selectInput(
        nodeInputChoiceOptions("upscaleModelLoader", "model_name", usdu.upscale_model_name, [usdu.upscale_model_name]),
        usdu.upscale_model_name,
      ),
      "tip.usduUpscaleModel",
    );
    const promptMode = field(
      usduSection,
      "USDU prompt",
      selectInput(["full", "no_general"], usdu.prompt_mode === "quality_tags_only" ? "no_general" : usdu.prompt_mode || "full"),
      "tip.usduPrompt",
    );
    const autoTile = field(usduSection, "Auto tile size", checkbox(usdu.auto_tile_size), "tip.usduAutoTile");
    const autoTileTarget = field(usduSection, "Auto tile target", numberInput(usdu.auto_tile_target, "64"), "tip.usduAutoTile");
    const autoTileMin = field(usduSection, "Auto tile min", numberInput(usdu.auto_tile_min, "64"), "tip.usduAutoTile");
    const autoTileMax = field(usduSection, "Auto tile max", numberInput(usdu.auto_tile_max, "64"), "tip.usduAutoTile");
    const modeType = field(usduSection, "Mode", selectInput(["Linear", "Chess", "None"], usdu.mode_type || "Linear"), "tip.usduMode");
    const tileWidth = field(usduSection, "Tile width", numberInput(usdu.tile_width, "8"), "tip.usduTile");
    const tileHeight = field(usduSection, "Tile height", numberInput(usdu.tile_height, "8"), "tip.usduTile");
    const maskBlur = field(usduSection, "Mask blur", numberInput(usdu.mask_blur, "1"), "tip.usduTile");
    const tilePadding = field(usduSection, "Tile padding", numberInput(usdu.tile_padding, "8"), "tip.usduTile");
    const forceUniformTiles = field(usduSection, "Force uniform tiles", checkbox(usdu.force_uniform_tiles), "tip.usduTile");
    const tiledDecode = field(usduSection, "Tiled decode", checkbox(usdu.tiled_decode), "tip.usduTile");
    const batchSize = field(usduSection, "Tile batch", numberInput(usdu.batch_size, "1"), "tip.usduTile");
    const seamFix = field(
      usduSection,
      "Seam fix",
      selectInput(["None", "Band Pass", "Half Tile", "Half Tile + Intersections"], usdu.seam_fix_mode || "None"),
      "tip.usduSeam",
    );
    const seamDenoise = field(usduSection, "Seam denoise", numberInput(usdu.seam_fix_denoise, "0.01"), "tip.usduSeam");
    const seamWidth = field(usduSection, "Seam width", numberInput(usdu.seam_fix_width, "8"), "tip.usduSeam");
    const seamMaskBlur = field(usduSection, "Seam mask blur", numberInput(usdu.seam_fix_mask_blur, "1"), "tip.usduSeam");
    const seamPadding = field(usduSection, "Seam padding", numberInput(usdu.seam_fix_padding, "8"), "tip.usduSeam");

    const usduSampler = document.createElement("section");
    usduSampler.className = "easyuse-anima-aio-section";
    usduSampler.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("USDU Sampler") }));
    const inheritSampler = field(usduSampler, "Follow main sampler", checkbox(upscale.inherit_sampler_settings), "tip.highresFollow");
    const steps = field(usduSampler, "Steps", numberInput(upscale.steps, "1"), "tip.steps");
    const cfg = field(usduSampler, "CFG", numberInput(upscale.cfg, "0.1"), "tip.cfg");
    const samplerName = field(
      usduSampler,
      "Sampler",
      selectInput(widgetOptions(node, "sampler_name", GENERATOR_FALLBACK_SAMPLER_NAMES), upscale.sampler_name),
      "tip.sampler",
    );
    const scheduler = field(
      usduSampler,
      "Scheduler",
      selectInput(widgetOptions(node, "scheduler", GENERATOR_FALLBACK_SCHEDULER_NAMES), upscale.scheduler),
      "tip.scheduler",
    );
    const denoise = field(usduSampler, "Denoise", numberInput(upscale.denoise, "0.01"), "tip.denoise");
    const optimization = createStageOptimizationEditor("USDU Spectrum/DCW", upscale, DEFAULT_GENERATION_SETTINGS.upscale);

    const resshiftSection = document.createElement("section");
    resshiftSection.className = "easyuse-anima-aio-section";
    resshiftSection.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("ResShift Upscale") }));
    const resshiftScale = field(resshiftSection, "Scale", selectInput(["x2", "x4"], resshift.scale || "x2"), "tip.resshiftScale");
    const student = field(
      resshiftSection,
      "Student",
      selectInput(
        nodeInputChoiceOptions("resShiftLoader", "student_name", resshift.student_name, ["(auto-download)"]),
        resshift.student_name || "(auto-download)",
      ),
      "tip.resshiftStudent",
    );
    const dtype = field(resshiftSection, "Dtype", selectInput(["bf16", "fp32"], resshift.dtype || "bf16"), "tip.resshiftDtype");
    const chop = field(resshiftSection, "Chop", numberInput(resshift.chop, "256"), "tip.resshiftTiling");
    const overlap = field(resshiftSection, "Overlap", numberInput(resshift.overlap, "16"), "tip.resshiftTiling");
    const tileBatch = field(resshiftSection, "Tile batch", numberInput(resshift.tile_batch, "1"), "tip.resshiftTiling");

    const updateVisibility = () => {
      const isUsdu = backend.value === "usdu";
      usduSection.classList.toggle("hidden", !isUsdu);
      usduSampler.classList.toggle("hidden", !isUsdu);
      optimization.section.classList.toggle("hidden", !isUsdu);
      resshiftSection.classList.toggle("hidden", isUsdu);
      const autoTileDisplay = autoTile.checked ? "" : "none";
      for (const control of [autoTileTarget, autoTileMin, autoTileMax]) {
        if (control?.parentElement) {
          control.parentElement.style.display = autoTileDisplay;
        }
      }
      const manualTileDisplay = autoTile.checked ? "none" : "";
      for (const control of [tileWidth, tileHeight]) {
        if (control?.parentElement) {
          control.parentElement.style.display = manualTileDisplay;
        }
      }
      const samplerOverrideDisplay = inheritSampler.checked ? "none" : "";
      for (const control of [cfg, samplerName, scheduler]) {
        if (control?.parentElement) {
          control.parentElement.style.display = samplerOverrideDisplay;
        }
      }
    };
    const refreshDependencyLocks = () => {
      const messages = [];
      for (const option of Array.from(backend.options)) {
        const missingPacks = upscaleBackendMissingPacks(option.value);
        option.disabled = missingPacks.length > 0;
        option.textContent = missingPacks.length
          ? `${option.value} (${missingPacks.join(", ")} missing)`
          : option.value;
        if (option.selected && missingPacks.length) {
          messages.push(aioFormat("warning.optionalDependencyMissing", {
            backend: option.value,
            pack: missingPacks.join(", "),
          }));
          enabled.checked = false;
        }
      }
      dependencyWarning.hidden = messages.length === 0;
      dependencyWarning.textContent = messages.join(" ");
      updateVisibility();
    };
    backend.addEventListener("change", refreshDependencyLocks);
    autoTile.addEventListener("change", updateVisibility);
    inheritSampler.addEventListener("change", updateVisibility);
    body.append(main, usduSection, usduSampler, optimization.section, resshiftSection);
    updateVisibility();
    refreshDependencyLocks();
    loadGeneratorOptionalDependencies().then(() => {
      if (closed || backdrop.isConnected === false) {
        return;
      }
      reconcileSelectInput(
        upscaleModel,
        nodeInputChoiceOptions(
          "upscaleModelLoader",
          "model_name",
          upscaleModel.value,
          [upscaleModel.value],
        ),
      );
      reconcileSelectInput(
        student,
        nodeInputChoiceOptions(
          "resShiftLoader",
          "student_name",
          student.value,
          ["(auto-download)"],
        ),
      );
      refreshDependencyLocks();
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
      const missingPacks = upscaleBackendMissingPacks(backend.value);
      const optimized = optimization.values();
      next.upscale = {
        ...next.upscale,
        enabled: enabled.checked && missingPacks.length === 0,
        backend: backend.value || "usdu",
        scale_by: clampGeneratorNumber(scaleBy.value, DEFAULT_GENERATION_SETTINGS.upscale.scale_by, 0.05, 4),
        steps: Math.trunc(clampGeneratorNumber(steps.value, DEFAULT_GENERATION_SETTINGS.upscale.steps, 1, 1000)),
        inherit_sampler_settings: inheritSampler.checked,
        cfg: clampGeneratorNumber(cfg.value, DEFAULT_GENERATION_SETTINGS.upscale.cfg, 0, 100),
        sampler_name: samplerName.value || "euler",
        scheduler: scheduler.value || "simple",
        denoise: clampGeneratorNumber(denoise.value, DEFAULT_GENERATION_SETTINGS.upscale.denoise, 0, 1),
        ...optimized,
        usdu: normalizeGeneratorUsduAutoTileRange({
          upscale_model_name: upscaleModel.value || DEFAULT_GENERATION_SETTINGS.upscale.usdu.upscale_model_name,
          auto_tile_size: autoTile.checked,
          prompt_mode: promptMode.value || "full",
          mode_type: modeType.value || "Linear",
          auto_tile_target: Math.trunc(clampGeneratorNumber(autoTileTarget.value, 1024, 64, 16384)),
          auto_tile_min: Math.trunc(clampGeneratorNumber(autoTileMin.value, 512, 64, 16384)),
          auto_tile_max: Math.trunc(clampGeneratorNumber(autoTileMax.value, 2048, 64, 16384)),
          tile_width: Math.trunc(clampGeneratorNumber(tileWidth.value, 512, 64, 16384)),
          tile_height: Math.trunc(clampGeneratorNumber(tileHeight.value, 512, 64, 16384)),
          mask_blur: Math.trunc(clampGeneratorNumber(maskBlur.value, 8, 0, 64)),
          tile_padding: Math.trunc(clampGeneratorNumber(tilePadding.value, 32, 0, 16384)),
          seam_fix_mode: seamFix.value || "None",
          seam_fix_denoise: clampGeneratorNumber(seamDenoise.value, 1, 0, 1),
          seam_fix_width: Math.trunc(clampGeneratorNumber(seamWidth.value, 64, 0, 16384)),
          seam_fix_mask_blur: Math.trunc(clampGeneratorNumber(seamMaskBlur.value, 8, 0, 64)),
          seam_fix_padding: Math.trunc(clampGeneratorNumber(seamPadding.value, 16, 0, 16384)),
          force_uniform_tiles: forceUniformTiles.checked,
          tiled_decode: tiledDecode.checked,
          batch_size: Math.trunc(clampGeneratorNumber(batchSize.value, 1, 1, 4096)),
        }),
        resshift: {
          scale: resshiftScale.value || "x2",
          student_name: student.value || "(auto-download)",
          dtype: dtype.value || "bf16",
          chop: Math.trunc(clampGeneratorNumber(chop.value, 512, 256, 4096)),
          overlap: Math.trunc(clampGeneratorNumber(overlap.value, 64, 0, 512)),
          tile_batch: Math.trunc(clampGeneratorNumber(tileBatch.value, 4, 1, 32)),
        },
      };
      writeSettings(node, widget, next);
      renderGeneratorPanel(node);
      closed = true;
      backdrop.remove();
    });
  }

  return {
    createStageOptimizationEditor,
    openHighresSettings,
    openUpscaleSettings,
  };
}
