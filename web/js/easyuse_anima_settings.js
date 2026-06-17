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

async function getDatasetStatus() {
  const response = await fetch("/easyuse_anima/animadex_status");
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

async function downloadAnimaDexDataset(forceRefresh = false) {
  const response = await fetch("/easyuse_anima/download_animadex", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ force_refresh: forceRefresh }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  return data;
}

async function runDownload(forceRefresh = false, button = null) {
  const originalText = button?.textContent;
  try {
    if (button) {
      button.disabled = true;
      button.textContent = forceRefresh ? "Refreshing..." : "Downloading...";
    }
    const result = await downloadAnimaDexDataset(forceRefresh);
    alert(
      [
        `AnimaDex dataset ${result.status}.`,
        "",
        `Character index: ${result.character_index || ""}`,
        `Artist index: ${result.artist_index || ""}`,
      ].join("\n"),
    );
    await refreshStatusPanels();
  } catch (error) {
    alert(`AnimaDex dataset download failed:\n${error.message || error}`);
    await refreshStatusPanels();
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
  }
}

const statusPanels = new Set();
const autocompletePanels = new Set();

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

function formatFileStatus(fileStatus) {
  if (!fileStatus?.exists) {
    return {
      state: "missing",
      detail: "",
      path: fileStatus?.path || "",
    };
  }
  const size = Number(fileStatus.size || 0).toLocaleString();
  const mtime = fileStatus.mtime
    ? new Date(fileStatus.mtime * 1000).toLocaleString()
    : "unknown time";
  return {
    state: "found",
    detail: `${size} bytes, ${mtime}`,
    path: fileStatus.path || "",
  };
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

function appendFileStatusLine(container, label, fileStatus) {
  const info = formatFileStatus(fileStatus);
  const row = document.createElement("div");
  row.style.cssText = "margin: 2px 0;";

  const strong = document.createElement("strong");
  strong.textContent = `${label}: `;

  const status = document.createElement("span");
  status.textContent = info.detail ? `${info.state} (${info.detail})` : info.state;

  const path = document.createElement("span");
  path.textContent = info.path ? ` - ${info.path}` : "";
  path.style.cssText = "opacity: 0.58; font-weight: 400;";

  row.append(strong, status, path);
  container.append(row);
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

function renderStatusPanel(panel, status) {
  panel.replaceChildren();

  const guide = document.createElement("div");
  guide.style.cssText = "margin-bottom: 8px; line-height: 1.45;";
  guide.textContent =
    "Paste the AnimaDex export token above, then click Download. Dataset files are saved inside this custom node under __easyuse_anima__ and are ignored by git.";
  panel.append(guide);

  const banner = document.createElement("div");
  banner.textContent = status.downloaded
    ? "AnimaDex dataset is downloaded and ready."
    : "AnimaDex dataset is not downloaded yet.";
  banner.style.cssText = status.downloaded
    ? "margin: 8px 0; padding: 8px 10px; border-radius: 6px; background: rgba(22, 163, 74, 0.16); color: #16a34a; font-weight: 700;"
    : "margin: 8px 0; padding: 8px 10px; border-radius: 6px; background: rgba(234, 179, 8, 0.14); color: #ca8a04; font-weight: 700;";
  panel.append(banner);

  const statusText = status.downloaded ? "Downloaded" : "Not downloaded";
  appendLine(
    panel,
    "Dataset",
    statusText,
    status.downloaded
      ? "color: #16a34a; font-weight: 700;"
      : "color: #ca8a04; font-weight: 700;",
  );
  appendLine(panel, "Token", status.token_configured ? "configured" : "not configured");
  appendPathLine(panel, "Storage", status.data_dir || "");
  appendFileStatusLine(panel, "Character index", status.character_index);
  appendFileStatusLine(panel, "Artist index", status.artist_index);

  const refresh = document.createElement("button");
  refresh.textContent = "Refresh Status";
  refresh.style.cssText = "margin-top: 8px; padding: 4px 10px; cursor: pointer;";
  refresh.onclick = () => refreshStatusPanel(panel);
  panel.append(refresh);
}

async function refreshStatusPanel(panel) {
  try {
    const status = await getDatasetStatus();
    renderStatusPanel(panel, status);
  } catch (error) {
    panel.textContent = `Could not read AnimaDex dataset status: ${error.message || error}`;
  }
}

async function refreshStatusPanels() {
  await Promise.all([...statusPanels].map((panel) => refreshStatusPanel(panel)));
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

function datasetStatusPanel() {
  const panel = document.createElement("div");
  panel.style.cssText = "max-width: 760px; line-height: 1.45; white-space: normal;";
  panel.textContent = "Checking AnimaDex dataset status...";
  statusPanels.add(panel);
  refreshStatusPanel(panel);
  return panel;
}

function downloadButton(label, forceRefresh = false) {
  const button = document.createElement("button");
  button.textContent = label;
  button.style.cssText = "padding: 6px 12px; cursor: pointer;";
  button.onclick = () => runDownload(forceRefresh, button);
  return button;
}

app.registerExtension({
  name: "easyuse-anima.settings",
  async setup() {
    const settings = await getSettings();
    const tokenConfigured = settings["animadex.token_configured"] === true;

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
      id: "EasyUseAnima.Section.AnimaDex",
      name: "EasyUse Anima: AnimaDex",
      type: () => sectionHeader(
        "AnimaDex dataset",
        "Token, download status, and dataset refresh controls.",
      ),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.AnimaDex.Token",
      name: tokenConfigured
        ? "EasyUse Anima: AnimaDex Export Token (saved; enter to replace)"
        : "EasyUse Anima: AnimaDex Export Token",
      type: "text",
      defaultValue: "",
      onChange: async (value) => {
        await saveSetting("animadex.token", value);
        await refreshStatusPanels();
      },
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.AnimaDex.Status",
      name: "EasyUse Anima: AnimaDex Dataset Status",
      type: () => datasetStatusPanel(),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.AnimaDex.Site",
      name: "EasyUse Anima: AnimaDex Site",
      type: "text",
      defaultValue: settings["animadex.site"] || "https://animadex.net",
      onChange: (value) => saveSetting("animadex.site", value),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.AnimaDex.Download",
      name: "EasyUse Anima: Download AnimaDex Dataset",
      type: () => downloadButton("Download", false),
      tooltip: "Download character/artist CSVs and build local indexes under this custom node.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.AnimaDex.Refresh",
      name: "EasyUse Anima: Force Refresh AnimaDex Dataset",
      type: () => downloadButton("Force Refresh", true),
      tooltip: "Download again even if local indexes already exist.",
    });
  },
});
