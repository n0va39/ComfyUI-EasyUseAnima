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

function autocompleteDatasetSelector(initialValue = "") {
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

  const saveButton = document.createElement("button");
  saveButton.textContent = "Save Autocomplete CSV";
  saveButton.style.cssText = "padding: 5px 10px; cursor: pointer;";

  const message = document.createElement("span");
  message.style.cssText = "opacity: 0.76;";

  row.append(select, saveButton, message);
  container.append(row);

  const panel = document.createElement("div");
  panel.style.cssText = "margin-top: 8px;";
  container.append(panel);
  autocompletePanels.add(panel);

  const renderOptions = (status) => {
    const sources = Array.isArray(status.sources) ? status.sources : [];
    const selected = status.source || initialValue;
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
      const data = await saveSetting("autocomplete.source", select.value);
      message.textContent = "Saved";
      message.style.color = "#16a34a";
      renderOptions({ sources: panel._easyuseSources || [], source: data["autocomplete.source"] });
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
      type: () => autocompleteDatasetSelector(settings["autocomplete.source"] || ""),
      tooltip: "Select which bundled Korean Danbooru CSV powers autocomplete and tag highlighting.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Prompt.PromptStudio",
      name: "EasyUse Anima: Prompt Studio Highlighting",
      type: () => promptStudioEditor(settings),
      tooltip: "Configure Prompt Studio typo indicators and tag highlight colors.",
    });

  },
});
