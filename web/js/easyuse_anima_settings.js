import { app } from "../../../scripts/app.js";

async function getSettings() {
  try {
    const response = await fetch("/easyuse_anima/settings");
    if (!response.ok) {
      return {};
    }
    return await response.json();
  } catch {
    return {};
  }
}

function setSetting(key, value) {
  return fetch("/easyuse_anima/set_setting", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, value }),
  });
}

async function saveSetting(key, value) {
  const response = await setSetting(key, value);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  return data;
}

async function getAutocompleteStatus() {
  const response = await fetch("/easyuse_anima/autocomplete_status");
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  return data;
}

const autocompletePanels = new Set();

const PROMPT_STUDIO_COLOR_DEFAULTS = {
  quality: { label: "품질", color: "#facc15" },
  safety: { label: "등급", color: "#38bdf8" },
  year: { label: "연도", color: "#2dd4bf" },
  count: { label: "인원수", color: "#60a5fa" },
  character: { label: "캐릭터", color: "#f472b6" },
  artist: { label: "작가", color: "#a78bfa" },
  copyright: { label: "작품", color: "#fb923c" },
  general: { label: "학습 태그", color: "#4ade80" },
  meta: { label: "메타", color: "#94a3b8" },
  natural: { label: "자연어", color: "#cbd5e1" },
  artist_unknown: { label: "미등록 작가", color: "#f87171" },
  unknown: { label: "미확인", color: "#cbd5e1" },
};

const NAIA_PREPROCESSING_OPTIONS = [
  ["remove_author", "Remove author"],
  ["remove_work_title", "Remove work title"],
  ["remove_character_name", "Remove character name"],
  ["remove_character_features", "Remove character features"],
  ["remove_clothes", "Remove clothes"],
  ["remove_color", "Remove color"],
  ["remove_location_and_background_color", "Remove location/background color"],
  ["remove_expression", "Remove expression"],
  ["remove_pose_action", "Remove pose/action"],
  ["remove_meta_tags", "Remove meta tags"],
  ["remove_object_tags", "Remove object tags"],
  ["remove_noise_tags", "Remove noise tags"],
  ["e621_auto_boost", "e621 auto boost"],
  ["danbooru_auto_weight", "Danbooru auto weight"],
  ["tag_implication_compression", "Tag implication compression"],
];

function sectionHeader(title, description) {
  const container = document.createElement("div");
  container.style.cssText =
    "max-width: 760px; padding: 9px 0 4px; border-top: 1px solid rgba(128, 128, 128, 0.28);";

  const heading = document.createElement("div");
  heading.textContent = title;
  heading.style.cssText = "font-weight: 700; margin-bottom: 3px;";
  container.append(heading);

  if (description) {
    const text = document.createElement("div");
    text.textContent = description;
    text.style.cssText = "opacity: 0.74; line-height: 1.45; font-size: 0.92em;";
    container.append(text);
  }

  return container;
}

function metadataFilterEditor(initialValue = "") {
  const container = document.createElement("div");
  container.style.cssText = "max-width: 760px; line-height: 1.45;";

  const guide = document.createElement("div");
  guide.textContent =
    "Comma- or newline-separated prompt tags to remove only from Anima Prompt Builder metadata_prompt. The normal prompt output is not filtered.";
  guide.style.cssText = "margin-bottom: 6px; opacity: 0.78;";
  container.append(guide);

  const textarea = document.createElement("textarea");
  textarea.value = initialValue || "";
  textarea.placeholder = "best quality\nlowres\nhigh detail";
  textarea.rows = 4;
  textarea.style.cssText =
    "box-sizing: border-box; width: min(100%, 560px); min-height: 86px; resize: vertical;";
  container.append(textarea);

  const controls = document.createElement("div");
  controls.style.cssText = "display: flex; align-items: center; gap: 8px; margin-top: 7px;";

  const saveButton = document.createElement("button");
  saveButton.textContent = "Save Metadata Filter";
  saveButton.style.cssText = "padding: 5px 10px; cursor: pointer;";

  const status = document.createElement("span");
  status.style.cssText = "opacity: 0.76;";

  saveButton.onclick = async () => {
    const originalText = saveButton.textContent;
    try {
      saveButton.disabled = true;
      saveButton.textContent = "Saving...";
      await saveSetting("prompt.metadata_filter_words", textarea.value);
      status.textContent = "Saved";
      status.style.color = "#16a34a";
    } catch (error) {
      status.textContent = `Save failed: ${error.message || error}`;
      status.style.color = "#dc2626";
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = originalText;
    }
  };

  controls.append(saveButton, status);
  container.append(controls);

  return container;
}

function parseColorSettings(value = "") {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function promptStudioEditor(settings = {}) {
  const container = document.createElement("div");
  container.style.cssText = "max-width: 760px; line-height: 1.45;";

  const guide = document.createElement("div");
  guide.textContent =
    "Controls Prompt Studio tag highlighting. Colors apply to both highlighted prompt text and the color legend.";
  guide.style.cssText = "margin-bottom: 8px; opacity: 0.78;";
  container.append(guide);

  const typoRow = document.createElement("label");
  typoRow.style.cssText = "display: flex; align-items: center; gap: 7px; margin-bottom: 10px;";
  const typoToggle = document.createElement("input");
  typoToggle.type = "checkbox";
  typoToggle.checked = settings["prompt_studio.typo_indicator"] !== "false";
  const typoText = document.createElement("span");
  typoText.textContent = "Show typo indicators for unregistered artist / unknown tags";
  typoRow.append(typoToggle, typoText);
  container.append(typoRow);

  const colors = parseColorSettings(settings["prompt_studio.colors"]);
  const grid = document.createElement("div");
  grid.style.cssText =
    "display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 6px 12px; max-width: 560px;";
  const colorInputs = new Map();
  for (const [key, item] of Object.entries(PROMPT_STUDIO_COLOR_DEFAULTS)) {
    const label = document.createElement("label");
    label.style.cssText = "display: flex; align-items: center; gap: 7px; font-size: 0.92em;";
    const input = document.createElement("input");
    input.type = "color";
    input.value = colors[key] || item.color;
    input.style.cssText = "width: 34px; height: 24px; padding: 0;";
    const text = document.createElement("span");
    text.textContent = item.label;
    label.append(input, text);
    grid.append(label);
    colorInputs.set(key, input);
  }
  container.append(grid);

  const controls = document.createElement("div");
  controls.style.cssText = "display: flex; align-items: center; gap: 8px; margin-top: 9px; flex-wrap: wrap;";

  const saveButton = document.createElement("button");
  saveButton.textContent = "Save Prompt Studio";
  saveButton.style.cssText = "padding: 5px 10px; cursor: pointer;";

  const resetButton = document.createElement("button");
  resetButton.textContent = "Reset Colors";
  resetButton.style.cssText = "padding: 5px 10px; cursor: pointer;";

  const status = document.createElement("span");
  status.style.cssText = "opacity: 0.76;";

  resetButton.onclick = () => {
    for (const [key, input] of colorInputs.entries()) {
      input.value = PROMPT_STUDIO_COLOR_DEFAULTS[key].color;
    }
  };

  saveButton.onclick = async () => {
    const originalText = saveButton.textContent;
    const colorSettings = {};
    for (const [key, input] of colorInputs.entries()) {
      colorSettings[key] = input.value;
    }
    try {
      saveButton.disabled = true;
      saveButton.textContent = "Saving...";
      await saveSetting("prompt_studio.typo_indicator", typoToggle.checked ? "true" : "false");
      await saveSetting("prompt_studio.colors", JSON.stringify(colorSettings));
      status.textContent = "Saved. Reload ComfyUI page to apply.";
      status.style.color = "#16a34a";
    } catch (error) {
      status.textContent = `Save failed: ${error.message || error}`;
      status.style.color = "#dc2626";
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = originalText;
    }
  };

  controls.append(saveButton, resetButton, status);
  container.append(controls);
  return container;
}

function loraPresetEditor(settings = {}) {
  const container = document.createElement("div");
  container.style.cssText = "max-width: 760px; line-height: 1.45;";

  const guide = document.createElement("div");
  guide.textContent = "Controls how LoRA names are displayed inside Anima LoRA Preset rows.";
  guide.style.cssText = "margin-bottom: 8px; opacity: 0.78;";
  container.append(guide);

  const row = document.createElement("div");
  row.style.cssText = "display: flex; align-items: center; flex-wrap: wrap; gap: 8px;";

  const label = document.createElement("label");
  label.style.cssText = "display: flex; align-items: center; gap: 7px;";
  const text = document.createElement("span");
  text.textContent = "LoRA display";
  const select = document.createElement("select");
  select.style.cssText = "min-width: 180px; padding: 4px 8px;";
  for (const [value, labelText] of [
    ["name", "Name only"],
    ["path", "Full path"],
  ]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labelText;
    option.selected = (settings["lora_preset.name_display"] || "name") === value;
    select.append(option);
  }
  label.append(text, select);

  const saveButton = document.createElement("button");
  saveButton.textContent = "Save LoRA Preset";
  saveButton.style.cssText = "padding: 5px 10px; cursor: pointer;";

  const status = document.createElement("span");
  status.style.cssText = "opacity: 0.76;";

  saveButton.onclick = async () => {
    const originalText = saveButton.textContent;
    try {
      saveButton.disabled = true;
      saveButton.textContent = "Saving...";
      const data = await saveSetting("lora_preset.name_display", select.value);
      status.textContent = "Saved";
      status.style.color = "#16a34a";
      window.dispatchEvent(new CustomEvent("easyuse-anima-settings-updated", { detail: data }));
    } catch (error) {
      status.textContent = `Save failed: ${error.message || error}`;
      status.style.color = "#dc2626";
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = originalText;
    }
  };

  row.append(label, saveButton, status);
  container.append(row);
  return container;
}

function naiaSettingsEditor(settings = {}) {
  const container = document.createElement("div");
  container.style.cssText = "max-width: 760px; line-height: 1.45;";

  const guide = document.createElement("div");
  guide.textContent =
    "Controls Anima NAIA Random Prompt connection and Prompt Engineering override options. These values replace the advanced NAIA options that used to live on the node.";
  guide.style.cssText = "margin-bottom: 8px; opacity: 0.78;";
  container.append(guide);

  const endpointRow = document.createElement("div");
  endpointRow.style.cssText = "display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;";

  const hostLabel = document.createElement("label");
  hostLabel.style.cssText = "display: flex; align-items: center; gap: 6px;";
  const hostText = document.createElement("span");
  hostText.textContent = "Host";
  const hostInput = document.createElement("input");
  hostInput.type = "text";
  hostInput.value = settings["naia.host"] || "127.0.0.1";
  hostInput.style.cssText = "width: 150px; padding: 4px 6px;";
  hostLabel.append(hostText, hostInput);

  const portLabel = document.createElement("label");
  portLabel.style.cssText = "display: flex; align-items: center; gap: 6px;";
  const portText = document.createElement("span");
  portText.textContent = "Port";
  const portInput = document.createElement("input");
  portInput.type = "number";
  portInput.min = "1";
  portInput.max = "65535";
  portInput.step = "1";
  portInput.value = String(settings["naia.port"] || 7243);
  portInput.style.cssText = "width: 86px; padding: 4px 6px;";
  portLabel.append(portText, portInput);
  endpointRow.append(hostLabel, portLabel);
  container.append(endpointRow);

  const useSettingsRow = document.createElement("label");
  useSettingsRow.style.cssText = "display: flex; align-items: center; gap: 7px; margin-bottom: 8px;";
  const useSettingsToggle = document.createElement("input");
  useSettingsToggle.type = "checkbox";
  useSettingsToggle.checked = settings["naia.use_naia_settings"] !== "false";
  const useSettingsText = document.createElement("span");
  useSettingsText.textContent = "Use NAIA desktop Prompt Engineering settings";
  useSettingsRow.append(useSettingsToggle, useSettingsText);
  container.append(useSettingsRow);

  const textGrid = document.createElement("div");
  textGrid.style.cssText = "display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 8px; max-width: 680px;";
  const textareas = new Map();
  for (const [key, labelText] of [
    ["pre_prompt", "Pre prompt"],
    ["post_prompt", "Post prompt"],
    ["auto_hide", "Auto hide"],
  ]) {
    const label = document.createElement("label");
    label.style.cssText = "display: flex; flex-direction: column; gap: 4px;";
    const text = document.createElement("span");
    text.textContent = labelText;
    const textarea = document.createElement("textarea");
    textarea.value = settings[`naia.${key}`] || "";
    textarea.rows = 4;
    textarea.style.cssText = "box-sizing: border-box; width: 100%; min-height: 76px; resize: vertical;";
    label.append(text, textarea);
    textGrid.append(label);
    textareas.set(key, textarea);
  }
  container.append(textGrid);

  const ppTitle = document.createElement("div");
  ppTitle.textContent = "Preprocessing options";
  ppTitle.style.cssText = "margin: 10px 0 5px; font-weight: 700;";
  container.append(ppTitle);

  const ppGrid = document.createElement("div");
  ppGrid.style.cssText =
    "display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 6px 12px; max-width: 680px;";
  const preprocessingSelects = new Map();
  for (const [key, labelText] of NAIA_PREPROCESSING_OPTIONS) {
    const label = document.createElement("label");
    label.style.cssText = "display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 0.92em;";
    const text = document.createElement("span");
    text.textContent = labelText;
    const select = document.createElement("select");
    select.style.cssText = "width: 76px; padding: 3px 4px;";
    for (const value of ["skip", "on", "off"]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      option.selected = (settings[`naia.${key}`] || "skip") === value;
      select.append(option);
    }
    label.append(text, select);
    ppGrid.append(label);
    preprocessingSelects.set(key, select);
  }
  container.append(ppGrid);

  const controls = document.createElement("div");
  controls.style.cssText = "display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap;";

  const saveButton = document.createElement("button");
  saveButton.textContent = "Save NAIA Settings";
  saveButton.style.cssText = "padding: 5px 10px; cursor: pointer;";

  const status = document.createElement("span");
  status.style.cssText = "opacity: 0.76;";

  saveButton.onclick = async () => {
    const originalText = saveButton.textContent;
    try {
      saveButton.disabled = true;
      saveButton.textContent = "Saving...";
      const port = Math.max(1, Math.min(65535, Number.parseInt(portInput.value || "7243", 10) || 7243));
      portInput.value = String(port);
      await saveSetting("naia.host", hostInput.value.trim() || "127.0.0.1");
      await saveSetting("naia.port", String(port));
      await saveSetting("naia.use_naia_settings", useSettingsToggle.checked ? "true" : "false");
      for (const [key, textarea] of textareas.entries()) {
        await saveSetting(`naia.${key}`, textarea.value);
      }
      for (const [key, select] of preprocessingSelects.entries()) {
        await saveSetting(`naia.${key}`, select.value);
      }
      status.textContent = "Saved. Queue again to apply.";
      status.style.color = "#16a34a";
    } catch (error) {
      status.textContent = `Save failed: ${error.message || error}`;
      status.style.color = "#dc2626";
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = originalText;
    }
  };

  controls.append(saveButton, status);
  container.append(controls);
  return container;
}

function autocompleteDatasetSelector(initialValue = {}) {
  const initialSource =
    typeof initialValue === "object" && initialValue !== null
      ? initialValue.source || ""
      : String(initialValue || "");
  const initialLimit =
    typeof initialValue === "object" && initialValue !== null
      ? initialValue.limit || 20
      : 20;
  const container = document.createElement("div");
  container.style.cssText = "max-width: 760px; line-height: 1.45;";

  const guide = document.createElement("div");
  guide.textContent =
    "Choose which bundled CSV is used for tag autocomplete and Prompt Studio tag highlighting. Korean searches use the selected CSV description text.";
  guide.style.cssText = "margin-bottom: 7px; opacity: 0.78;";
  container.append(guide);

  const row = document.createElement("div");
  row.style.cssText = "display: flex; align-items: center; flex-wrap: wrap; gap: 8px;";

  const select = document.createElement("select");
  select.style.cssText = "min-width: min(100%, 340px); padding: 4px 8px;";

  const limitLabel = document.createElement("label");
  limitLabel.style.cssText = "display: flex; align-items: center; gap: 6px;";
  const limitText = document.createElement("span");
  limitText.textContent = "Suggestions";
  const limitInput = document.createElement("input");
  limitInput.type = "number";
  limitInput.min = "1";
  limitInput.max = "100";
  limitInput.step = "1";
  limitInput.value = String(initialLimit);
  limitInput.style.cssText = "width: 72px; padding: 4px 6px;";
  limitLabel.append(limitText, limitInput);

  const saveButton = document.createElement("button");
  saveButton.textContent = "Save Autocomplete";
  saveButton.style.cssText = "padding: 5px 10px; cursor: pointer;";

  const message = document.createElement("span");
  message.style.cssText = "opacity: 0.76;";

  row.append(select, limitLabel, saveButton, message);
  container.append(row);

  const panel = document.createElement("div");
  panel.style.cssText = "margin-top: 8px;";
  container.append(panel);
  autocompletePanels.add(panel);

  const renderOptions = (status) => {
    const sources = Array.isArray(status.sources) ? status.sources : [];
    const selected = status.source || initialSource;
    select.replaceChildren();
    for (const source of sources) {
      const option = document.createElement("option");
      option.value = source.key;
      option.textContent = source.exists ? source.label : `${source.label} (missing)`;
      option.selected = source.key === selected;
      select.append(option);
    }
  };

  const refresh = async () => {
    try {
      const status = await getAutocompleteStatus();
      renderOptions(status);
      renderAutocompletePanel(panel, status);
    } catch (error) {
      panel.textContent = `Could not read autocomplete CSV status: ${error.message || error}`;
    }
  };

  saveButton.onclick = async () => {
    const originalText = saveButton.textContent;
    try {
      saveButton.disabled = true;
      saveButton.textContent = "Saving...";
      const limit = Math.max(1, Math.min(100, Number.parseInt(limitInput.value || "20", 10) || 20));
      limitInput.value = String(limit);
      await saveSetting("autocomplete.source", select.value);
      const data = await saveSetting("autocomplete.limit", String(limit));
      message.textContent = "Saved";
      message.style.color = "#16a34a";
      renderOptions({ sources: panel._easyuseSources || [], source: data["autocomplete.source"] });
      window.dispatchEvent(new CustomEvent("easyuse-anima-settings-updated", { detail: data }));
      await refreshAutocompletePanels();
    } catch (error) {
      message.textContent = `Save failed: ${error.message || error}`;
      message.style.color = "#dc2626";
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = originalText;
    }
  };

  refresh();
  return container;
}

function appendLine(container, label, value, valueStyle = "") {
  const row = document.createElement("div");
  const strong = document.createElement("strong");
  const span = document.createElement("span");
  strong.textContent = `${label}: `;
  span.textContent = value;
  if (valueStyle) {
    span.style.cssText = valueStyle;
  }
  row.append(strong, span);
  container.append(row);
}

function appendPathLine(container, label, value) {
  appendLine(container, label, value, "opacity: 0.66; font-weight: 400;");
}

function renderAutocompletePanel(panel, status) {
  panel.replaceChildren();
  panel._easyuseSources = Array.isArray(status.sources) ? status.sources : [];

  const selected = panel._easyuseSources.find((source) => source.key === status.source);
  const banner = document.createElement("div");
  banner.textContent = status.exists
    ? `Autocomplete CSV is ready: ${selected?.label || status.source || "selected CSV"}`
    : "Selected autocomplete CSV is missing.";
  banner.style.cssText = status.exists
    ? "margin: 8px 0; padding: 8px 10px; border-radius: 6px; background: rgba(22, 163, 74, 0.16); color: #16a34a; font-weight: 700;"
    : "margin: 8px 0; padding: 8px 10px; border-radius: 6px; background: rgba(220, 38, 38, 0.14); color: #dc2626; font-weight: 700;";
  panel.append(banner);

  appendLine(panel, "Selected", selected?.label || status.source || "");
  appendLine(panel, "Tag count", Number(status.count || 0).toLocaleString());
  appendPathLine(panel, "Path", status.path || "");

  if (selected?.source) {
    appendLine(panel, "Source", selected.source, "opacity: 0.72; font-weight: 400;");
  }

  const refresh = document.createElement("button");
  refresh.textContent = "Refresh Autocomplete Status";
  refresh.style.cssText = "margin-top: 8px; padding: 4px 10px; cursor: pointer;";
  refresh.onclick = () => refreshAutocompletePanel(panel);
  panel.append(refresh);
}

async function refreshAutocompletePanel(panel) {
  try {
    const status = await getAutocompleteStatus();
    renderAutocompletePanel(panel, status);
  } catch (error) {
    panel.textContent = `Could not read autocomplete CSV status: ${error.message || error}`;
  }
}

async function refreshAutocompletePanels() {
  await Promise.all([...autocompletePanels].map((panel) => refreshAutocompletePanel(panel)));
}

app.registerExtension({
  name: "easyuse-anima.settings",
  async setup() {
    const settings = await getSettings();

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Section.Prompt",
      name: "EasyUse Anima: Prompt",
      type: () => sectionHeader(
        "Prompt metadata",
        "Controls that affect generated prompt text or metadata-only output.",
      ),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Prompt.MetadataFilter",
      name: "EasyUse Anima: Metadata Prompt Filter",
      type: () => metadataFilterEditor(settings["prompt.metadata_filter_words"] || ""),
      tooltip: "Remove these tags only from Anima Prompt Builder metadata_prompt.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Prompt.AutocompleteCsv",
      name: "EasyUse Anima: Autocomplete CSV",
      type: () => autocompleteDatasetSelector({
        source: settings["autocomplete.source"] || "",
        limit: settings["autocomplete.limit"] || 20,
      }),
      tooltip: "Select which bundled Korean Danbooru CSV powers autocomplete and tag highlighting.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Prompt.PromptStudio",
      name: "EasyUse Anima: Prompt Studio Highlighting",
      type: () => promptStudioEditor(settings),
      tooltip: "Configure Prompt Studio typo indicators and tag highlight colors.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Section.LoraPreset",
      name: "EasyUse Anima: LoRA Preset",
      type: () => sectionHeader(
        "LoRA preset",
        "Display options for Anima LoRA Preset.",
      ),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.LoraPreset.Display",
      name: "EasyUse Anima: LoRA Preset Display",
      type: () => loraPresetEditor(settings),
      tooltip: "Choose whether LoRA preset rows show only filenames or full relative paths.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Section.NAIA",
      name: "EasyUse Anima: NAIA",
      type: () => sectionHeader(
        "NAIA bridge",
        "Connection and Prompt Engineering override settings used by Anima NAIA Random Prompt.",
      ),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.NAIA.Settings",
      name: "EasyUse Anima: NAIA Settings",
      type: () => naiaSettingsEditor(settings),
      tooltip: "Configure NAIA host, port, Prompt Engineering override, and preprocessing options.",
    });

  },
});
