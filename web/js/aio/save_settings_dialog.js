// @ts-check

const MAX_SAVED_HASH_ROWS = 32;
const MAX_SAVED_HASH_CANDIDATES = 64;
const MAX_SAVED_HASH_JSON_BYTES = 512 * 1024;
const MAX_HASH_BUNDLE_BYTES = 8 * 1024;
const MAX_CIVITAI_FIELD_CHARACTERS = 200;
const MAX_CIVITAI_FIELD_BYTES = 800;
const UTF8_ENCODER = new TextEncoder();
const CONTROL_RE = /[\x00-\x1f\x7f]/;

/**
 * @param {string} value
 * @param {number} maxCharacters
 * @param {number} maxBytes
 * @returns {boolean}
 */
function fitsUtf8Limit(value, maxCharacters, maxBytes) {
  return value.length <= maxCharacters
    && UTF8_ENCODER.encode(value).byteLength <= maxBytes;
}

/**
 * @param {any} value
 * @param {boolean} fallbackPlainText
 * @returns {any[] | null}
 */
function savedList(value, fallbackPlainText) {
  if (typeof value === "string") {
    if (!fitsUtf8Limit(value, MAX_SAVED_HASH_JSON_BYTES, MAX_SAVED_HASH_JSON_BYTES)) {
      return null;
    }
    try {
      value = JSON.parse(value || "[]");
    } catch {
      value = fallbackPlainText ? [value] : null;
    }
  }
  return Array.isArray(value) ? value : null;
}

/**
 * @param {any} value
 * @param {number} maxCharacters
 * @param {number} maxBytes
 * @param {boolean} stripHashEdges
 * @returns {string | null}
 */
function boundedScalarText(value, maxCharacters, maxBytes, stripHashEdges = false) {
  if (value == null) return "";
  if (!["string", "boolean", "number"].includes(typeof value)) return null;
  const raw = String(value);
  if (!fitsUtf8Limit(raw, maxCharacters, maxBytes)) return null;
  const text = stripHashEdges
    ? raw.trim().replace(/^[,\s]+|[,\s]+$/g, "")
    : raw.trim();
  if (!fitsUtf8Limit(text, maxCharacters, maxBytes)) return null;
  return text;
}

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
 * @typedef {object} AioSaveSettingsDialogDependencies
 * @property {any} document
 * @property {AioSaveDialogControls} controls
 * @property {AioSaveDialogText} text
 * @property {AioSaveDialogSettingsCore} settingsCore
 * @property {AioSaveDialogNodeAdapter} nodeAdapter
 */

/**
 * Own the Save settings dialog, native output hash editors, normalization, and
 * Apply/Cancel lifecycle. Extension registration, generator-panel rendering,
 * and durable storage remain adapters.
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
  function normalizeImageSaverHashBundles(value) {
    const values = savedList(value, true);
    if (!values) return [];
    const bundles = [];
    for (const item of values.slice(0, MAX_SAVED_HASH_CANDIDATES)) {
      const text = boundedScalarText(
        item,
        MAX_HASH_BUNDLE_BYTES,
        MAX_HASH_BUNDLE_BYTES,
        true,
      );
      if (!text) continue;
      bundles.push(text);
      if (bundles.length >= MAX_SAVED_HASH_ROWS) break;
    }
    return bundles;
  }

  function normalizeImageSaverCivitaiHashFetchers(value) {
    const values = savedList(value, false);
    if (!values) return [];
    const fetchers = [];
    for (const item of values.slice(0, MAX_SAVED_HASH_CANDIDATES)) {
      if (!item || typeof item !== "object" || Array.isArray(item)) continue;
      const fields = ["username", "model_name", "version"].map((fieldName) => (
        boundedScalarText(
          item[fieldName],
          MAX_CIVITAI_FIELD_CHARACTERS,
          MAX_CIVITAI_FIELD_BYTES,
        )
      ));
      if (fields.some((fieldValue) => fieldValue == null || CONTROL_RE.test(fieldValue))) {
        continue;
      }
      const [username, modelName, version] = fields;
      if (!username && !modelName && !version) continue;
      fetchers.push({
        enabled: asBool(item.enabled, true),
        username,
        model_name: modelName,
        version,
      });
      if (fetchers.length >= MAX_SAVED_HASH_ROWS) break;
    }
    return fetchers;
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
      if (list.querySelectorAll(".easyuse-anima-aio-hash-bundle-row").length >= MAX_SAVED_HASH_ROWS) {
        return;
      }
      const row = document.createElement("div");
      row.className = "easyuse-anima-aio-hash-bundle-row";
      const textarea = textareaInput(value);
      textarea.maxLength = MAX_HASH_BUNDLE_BYTES;
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
        return normalizeImageSaverHashBundles(
          [...list.querySelectorAll("textarea")].map((textarea) => textarea.value),
        );
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
      if (list.querySelectorAll(".easyuse-anima-aio-civitai-fetcher-row").length >= MAX_SAVED_HASH_ROWS) {
        return;
      }
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
      username.maxLength = MAX_CIVITAI_FIELD_CHARACTERS;
      modelName.maxLength = MAX_CIVITAI_FIELD_CHARACTERS;
      version.maxLength = MAX_CIVITAI_FIELD_CHARACTERS;
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
        return normalizeImageSaverCivitaiHashFetchers(
          [...list.querySelectorAll(".easyuse-anima-aio-civitai-fetcher-row")]
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
            }),
        );
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
      "EasyUse native output saves A1111 metadata and ComfyUI workflows in PNG, JPEG, and WebP."
    );
    body.classList.add("easyuse-anima-aio-save-body");
    const main = document.createElement("section");
    main.className = "easyuse-anima-aio-section full";
    main.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Save Backend") }));
    const save = field(main, "Save image", checkbox(settings.save.enabled));
    const backend = field(
      main,
      "Backend",
      selectInput([
        { value: "image_saver", label: "EasyUse Native" },
        "comfy_save_image",
      ], settings.save.backend || "image_saver"),
    );

    const files = document.createElement("section");
    files.className = "easyuse-anima-aio-section full";
    files.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Native Image Files") }));
    const filename = field(files, "Filename", textInput(imageSaver.filename));
    const path = field(files, "Path", textInput(imageSaver.path));
    const extension = field(files, "Extension", selectInput(["webp", "png", "jpeg", "jpg"], imageSaver.extension));
    const quality = field(files, "JPEG/WebP quality", numberInput(imageSaver.quality_jpeg_or_webp, "1"));
    const losslessWebp = field(files, "Lossless WebP", checkbox(imageSaver.lossless_webp));
    const optimizePng = field(files, "Optimize PNG", checkbox(imageSaver.optimize_png));
    const counter = field(files, "Counter", numberInput(imageSaver.counter, "1"));

    const metadata = document.createElement("section");
    metadata.className = "easyuse-anima-aio-section full";
    metadata.append(Object.assign(document.createElement("h3"), { textContent: aioStaticText("Native Image Metadata") }));
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
