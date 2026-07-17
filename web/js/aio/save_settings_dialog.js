// @ts-check

/**
 * @typedef {object} AioSaveDialogControls
 * @property {(title: any, subtitle: any) => {backdrop: any, body: any, actions: any}} createDialog
 * @property {(section: any, label: any, control: any, tooltipKey?: string) => any} field
 * @property {(value: any) => any} checkbox
 * @property {(options: any[], value: any) => any} selectInput
 * @property {(value: any) => any} textInput
 * @property {(value: any, step?: string) => any} numberInput
 * @property {(value: any) => any} textareaInput
 */

/**
 * @typedef {object} AioSaveDialogText
 * @property {(value: any) => string} staticText
 * @property {(key: string) => string} get
 * @property {(key: string, values?: Record<string, any>) => string} format
 * @property {(element: any, key: string) => any} applyTooltip
 * @property {(element: any, value: any) => any} applyTooltipText
 */

/**
 * @typedef {object} AioSaveDialogSettingsCore
 * @property {any} defaultGenerationSettings
 * @property {(value: any, fallback?: boolean) => boolean} asBool
 * @property {(defaults: any, current: any) => any} mergeDefaults
 */

/**
 * @typedef {object} AioSaveDialogNodeAdapter
 * @property {string} generatorSettingsWidget
 * @property {(node: any, name: string) => any} findWidget
 * @property {(node: any) => any} getSettings
 * @property {(node: any, settings: any) => void} applyVisibleSettings
 * @property {(node: any, widget: any, settings: any) => void} writeSettings
 * @property {(node: any) => void} renderPanel
 */

/**
 * @typedef {object} AioSaveDialogDependencyAdapter
 * @property {(key: string) => boolean} available
 * @property {(key: string) => string} pack
 * @property {(options?: Record<string, any>) => Promise<any>} load
 */

/**
 * @typedef {object} AioSaveSettingsDialogDependencies
 * @property {any} document
 * @property {AioSaveDialogControls} controls
 * @property {AioSaveDialogText} text
 * @property {AioSaveDialogSettingsCore} settingsCore
 * @property {AioSaveDialogNodeAdapter} nodeAdapter
 * @property {AioSaveDialogDependencyAdapter} dependencyAdapter
 */

/**
 * Own the Save settings dialog, Image Saver hash editors, normalization, and
 * Apply/Cancel lifecycle. Extension registration, dependency discovery,
 * generator-panel rendering, and durable storage remain adapters.
 *
 * @param {AioSaveSettingsDialogDependencies} dependencies
 * @returns {(node: any) => void}
 */
export function aioCreateSaveSettingsDialog(dependencies) {
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
    checkbox,
    selectInput,
    textInput,
    numberInput,
    textareaInput,
  } = controls;
  const {
    staticText: aioStaticText,
    get: aioText,
    format: aioFormat,
    applyTooltip,
    applyTooltipText,
  } = text;
  const {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    asBool,
    mergeDefaults,
  } = settingsCore;
  const {
    generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,
    findWidget,
    getSettings: generatorSettings,
    applyVisibleSettings: applyVisibleGeneratorSettings,
    writeSettings,
    renderPanel: renderGeneratorPanel,
  } = nodeAdapter;
  const {
    available: optionalDependencyAvailable,
    pack: optionalDependencyPack,
    load: loadGeneratorOptionalDependencies,
  } = dependencyAdapter;

  function normalizeImageSaverHashBundles(value) {
    if (typeof value === "string") {
      try {
        return normalizeImageSaverHashBundles(JSON.parse(value || "[]"));
      } catch {
        return value.trim() ? [value.trim()] : [];
      }
    }
    if (!Array.isArray(value)) {
      return [];
    }
    return value
      .map((item) => String(item ?? "").trim().replace(/^[,\s]+|[,\s]+$/g, ""))
      .filter(Boolean);
  }

  function normalizeImageSaverCivitaiHashFetchers(value) {
    if (typeof value === "string") {
      try {
        return normalizeImageSaverCivitaiHashFetchers(JSON.parse(value || "[]"));
      } catch {
        return [];
      }
    }
    if (!Array.isArray(value)) {
      return [];
    }
    return value
      .filter((item) => item && typeof item === "object" && !Array.isArray(item))
      .map((item) => ({
        enabled: asBool(item.enabled, true),
        username: String(item.username || "").trim(),
        model_name: String(item.model_name || "").trim(),
        version: String(item.version || "").trim(),
      }))
      .filter((item) => item.username || item.model_name || item.version);
  }

  function createImageSaverHashBundleEditor(initialBundles) {
    const wrapper = document.createElement("div");
    const list = document.createElement("div");
    list.className = "easyuse-anima-aio-hash-bundle-list";
    const addButton = document.createElement("button");
    addButton.type = "button";
    addButton.className = "easyuse-anima-aio-add-row";
    addButton.textContent = aioText("button.addHashBundle");

    const addRow = (value = "") => {
      const row = document.createElement("div");
      row.className = "easyuse-anima-aio-hash-bundle-row";
      const textarea = textareaInput(value);
      textarea.placeholder = "Name:HASH, HASH:Weight, Name:HASH:Weight";
      applyTooltip(textarea, "tip.hashBundles");
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = aioText("button.remove");
      applyTooltip(remove, "tip.hashBundles");
      remove.addEventListener("click", () => {
        row.remove();
      });
      row.append(textarea, remove);
      list.append(row);
    };

    const bundles = normalizeImageSaverHashBundles(initialBundles);
    if (bundles.length) {
      for (const bundle of bundles) {
        addRow(bundle);
      }
    } else {
      addRow();
    }
    addButton.addEventListener("click", () => addRow());
    wrapper.append(list, addButton);

    return {
      element: wrapper,
      values() {
        return [...list.querySelectorAll("textarea")]
          .map((textarea) => String(textarea.value || "").trim().replace(/^[,\s]+|[,\s]+$/g, ""))
          .filter(Boolean);
      },
    };
  }

  function createImageSaverCivitaiHashFetcherEditor(initialFetchers) {
    const wrapper = document.createElement("div");
    const list = document.createElement("div");
    list.className = "easyuse-anima-aio-civitai-fetcher-list";
    const addButton = document.createElement("button");
    addButton.type = "button";
    addButton.className = "easyuse-anima-aio-add-row";
    addButton.textContent = aioText("button.addCivitaiFetcher");
    applyTooltip(addButton, "tip.civitaiHashFetchers");

    const miniField = (label, control, tooltipKey) => {
      const item = document.createElement("div");
      item.className = "easyuse-anima-aio-mini-field";
      const labelEl = document.createElement("label");
      labelEl.textContent = label;
      const tooltip = aioText(tooltipKey);
      applyTooltipText(item, tooltip);
      applyTooltipText(labelEl, tooltip);
      applyTooltipText(control, tooltip);
      item.append(labelEl, control);
      return item;
    };

    const addRow = (value = {}) => {
      const row = document.createElement("div");
      row.className = "easyuse-anima-aio-civitai-fetcher-row";
      applyTooltip(row, "tip.civitaiHashFetchers");

      const header = document.createElement("div");
      header.className = "easyuse-anima-aio-civitai-fetcher-head";
      const enabledLabel = document.createElement("label");
      enabledLabel.className = "easyuse-anima-aio-civitai-fetcher-enabled";
      const enabled = checkbox(value.enabled !== false);
      enabledLabel.append(enabled, document.createTextNode(aioText("label.enabled")));
      applyTooltip(enabledLabel, "tip.civitaiHashFetchers");
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = aioText("button.remove");
      applyTooltip(remove, "tip.civitaiHashFetchers");
      remove.addEventListener("click", () => row.remove());
      header.append(enabledLabel, remove);

      const grid = document.createElement("div");
      grid.className = "easyuse-anima-aio-civitai-fetcher-grid";
      const username = textInput(value.username || "");
      const modelName = textInput(value.model_name || "");
      const version = textInput(value.version || "");
      username.placeholder = "N0VA39";
      modelName.placeholder = "Anima All in One workflow";
      version.placeholder = "";
      grid.append(
        miniField("Username", username, "tip.civitaiUsername"),
        miniField("Model name", modelName, "tip.civitaiModelName"),
        miniField("Version", version, "tip.civitaiVersion"),
      );

      const preview = document.createElement("div");
      preview.className = "easyuse-anima-aio-civitai-fetcher-preview";
      applyTooltip(preview, "tip.civitaiHashFetchers");
      const updatePreview = () => {
        const name = String(modelName.value || "").trim() || "model_name";
        preview.textContent = aioFormat("text.civitaiHashPreview", { model: name });
      };
      modelName.addEventListener("input", updatePreview);
      updatePreview();

      row.append(header, grid, preview);
      list.append(row);
    };

    const fetchers = normalizeImageSaverCivitaiHashFetchers(initialFetchers);
    if (fetchers.length) {
      for (const fetcher of fetchers) {
        addRow(fetcher);
      }
    } else {
      addRow();
    }
    addButton.addEventListener("click", () => addRow());
    wrapper.append(list, addButton);

    return {
      element: wrapper,
      values() {
        return [...list.querySelectorAll(".easyuse-anima-aio-civitai-fetcher-row")]
          .map((row) => {
            const inputs = row.querySelectorAll("input");
            const enabled = inputs[0]?.checked !== false;
            const username = String(inputs[1]?.value || "").trim();
            const modelName = String(inputs[2]?.value || "").trim();
            const version = String(inputs[3]?.value || "").trim();
            return {
              enabled,
              username,
              model_name: modelName,
              version,
            };
          })
          .filter((item) => item.username || item.model_name || item.version);
      },
    };
  }

  function openSaveSettings(node) {
    const widget = findWidget(node, GENERATOR_SETTINGS_WIDGET);
    const settings = generatorSettings(node);
    const imageSaver = mergeDefaults(
      DEFAULT_GENERATION_SETTINGS.save.image_saver,
      settings.save.image_saver,
    );
    const { backdrop, body, actions } = createDialog(
      "Save Options",
      "Image Saver requires ComfyUI-Image-Saver. Missing node packs are reported during queue execution."
    );
    body.classList.add("easyuse-anima-aio-save-body");
    const main = document.createElement("section");
    main.className = "easyuse-anima-aio-section full";
    main.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Save Backend") }));
    const save = field(main, "Save image", checkbox(settings.save.enabled));
    const backend = field(
      main,
      "Backend",
      selectInput(["image_saver", "comfy_save_image"], settings.save.backend || "image_saver"),
    );
    const dependencyWarning = document.createElement("div");
    dependencyWarning.className = "easyuse-anima-aio-warning";
    dependencyWarning.hidden = true;
    main.append(dependencyWarning);
    const refreshSaveDependencyLocks = () => {
      const imageSaverMissing = !optionalDependencyAvailable("imageSaver");
      for (const option of Array.from(backend.options)) {
        if (option.value === "image_saver") {
          option.disabled = imageSaverMissing;
          option.textContent = imageSaverMissing
            ? `image_saver (${optionalDependencyPack("imageSaver")} missing)`
            : "image_saver";
        }
      }
      if (imageSaverMissing && backend.value === "image_saver") {
        backend.value = "comfy_save_image";
        dependencyWarning.hidden = false;
        dependencyWarning.textContent = aioFormat("warning.optionalDependencyMissing", {
          backend: "image_saver",
          pack: optionalDependencyPack("imageSaver"),
        });
      } else {
        dependencyWarning.hidden = true;
        dependencyWarning.textContent = "";
      }
    };

    const files = document.createElement("section");
    files.className = "easyuse-anima-aio-section full";
    files.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Image Saver Files") }));
    const filename = field(files, "Filename", textInput(imageSaver.filename));
    const path = field(files, "Path", textInput(imageSaver.path));
    const extension = field(files, "Extension", selectInput(["webp", "png", "jpeg", "jpg"], imageSaver.extension));
    const quality = field(files, "JPEG/WebP quality", numberInput(imageSaver.quality_jpeg_or_webp, "1"));
    const losslessWebp = field(files, "Lossless WebP", checkbox(imageSaver.lossless_webp));
    const optimizePng = field(files, "Optimize PNG", checkbox(imageSaver.optimize_png));
    const counter = field(files, "Counter", numberInput(imageSaver.counter, "1"));

    const metadata = document.createElement("section");
    metadata.className = "easyuse-anima-aio-section full";
    metadata.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Image Saver Metadata") }));
    const timeFormat = field(metadata, "Time format", textInput(imageSaver.time_format));
    const clipSkip = field(metadata, "Clip skip", numberInput(imageSaver.clip_skip, "1"));
    const embedWorkflow = field(metadata, "Embed workflow", checkbox(imageSaver.embed_workflow));
    const saveWorkflowJson = field(metadata, "Workflow JSON", checkbox(imageSaver.save_workflow_as_json));
    const savePromptMetadata = field(metadata, "Save prompt metadata", checkbox(imageSaver.save_prompt_metadata));
    const additionalHashes = field(metadata, "Additional hashes", textInput(imageSaver.additional_hashes), "tip.additionalHashes");
    const hashBundles = createImageSaverHashBundleEditor(imageSaver.additional_hash_bundles);
    field(metadata, "Manual hash bundles", hashBundles.element, "tip.hashBundles");
    const civitaiHashFetchers = createImageSaverCivitaiHashFetcherEditor(imageSaver.civitai_hash_fetchers);
    field(metadata, "Civitai Hash Fetchers", civitaiHashFetchers.element, "tip.civitaiHashFetchers");
    const civitai = field(metadata, "Civitai data", checkbox(imageSaver.download_civitai_data));
    const easyRemix = field(metadata, "Easy remix", checkbox(imageSaver.easy_remix));
    const custom = field(metadata, "Custom metadata", textareaInput(imageSaver.custom));
    body.append(main, files, metadata);
    refreshSaveDependencyLocks();
    loadGeneratorOptionalDependencies().then(refreshSaveDependencyLocks);

    const cancel = document.createElement("button");
    cancel.textContent = aioText("button.cancel");
    const apply = document.createElement("button");
    apply.className = "primary";
    apply.textContent = aioText("button.apply");
    actions.append(cancel, apply);
    cancel.addEventListener("click", () => backdrop.remove());
    apply.addEventListener("click", () => {
      const next = mergeDefaults(DEFAULT_GENERATION_SETTINGS, settings);
      next.save.enabled = save.checked;
      next.save.backend = backend.value || "image_saver";
      next.save.image_saver = {
        filename: filename.value || "%time_%basemodelname",
        path: path.value || "EasyUseAnima/AiO",
        extension: extension.value || "webp",
        lossless_webp: losslessWebp.checked,
        quality_jpeg_or_webp: Number(quality.value || 97),
        optimize_png: optimizePng.checked,
        counter: Number(counter.value || 0),
        clip_skip: Number(clipSkip.value || 0),
        time_format: timeFormat.value || "%Y-%m-%d-%H%M%S",
        save_workflow_as_json: saveWorkflowJson.checked,
        embed_workflow: embedWorkflow.checked,
        save_prompt_metadata: savePromptMetadata.checked,
        additional_hashes: additionalHashes.value || "",
        additional_hash_bundles: hashBundles.values(),
        civitai_hash_fetchers: civitaiHashFetchers.values(),
        download_civitai_data: civitai.checked,
        easy_remix: easyRemix.checked,
        custom: custom.value || "",
      };
      applyVisibleGeneratorSettings(node, next);
      writeSettings(node, widget, next);
      renderGeneratorPanel(node);
      backdrop.remove();
    });
  }


  return openSaveSettings;
}
