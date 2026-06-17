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
  } catch (error) {
    alert(`AnimaDex dataset download failed:\n${error.message || error}`);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
  }
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
      id: "EasyUseAnima.AnimaDex.Token",
      name: tokenConfigured
        ? "EasyUse Anima: AnimaDex Export Token (saved; enter to replace)"
        : "EasyUse Anima: AnimaDex Export Token",
      type: "text",
      defaultValue: "",
      onChange: (value) => setSetting("animadex.token", value),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.AnimaDex.TokenFile",
      name: "EasyUse Anima: AnimaDex Token File",
      type: "text",
      defaultValue: settings["animadex.token_file"] || "",
      onChange: (value) => setSetting("animadex.token_file", value),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.AnimaDex.Site",
      name: "EasyUse Anima: AnimaDex Site",
      type: "text",
      defaultValue: settings["animadex.site"] || "https://animadex.net",
      onChange: (value) => setSetting("animadex.site", value),
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
