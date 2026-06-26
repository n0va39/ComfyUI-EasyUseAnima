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
  quality: { label: { en: "Quality", ko: "품질" }, color: "#facc15" },
  safety: { label: { en: "Rating", ko: "등급" }, color: "#38bdf8" },
  year: { label: { en: "Year", ko: "연도" }, color: "#2dd4bf" },
  count: { label: { en: "Count", ko: "인원수" }, color: "#60a5fa" },
  character: { label: { en: "Character", ko: "캐릭터" }, color: "#f472b6" },
  artist: { label: { en: "Artist", ko: "작가" }, color: "#a78bfa" },
  copyright: { label: { en: "Copyright", ko: "작품" }, color: "#fb923c" },
  general: { label: { en: "Trained tag", ko: "학습 태그" }, color: "#4ade80" },
  meta: { label: { en: "Meta", ko: "메타" }, color: "#94a3b8" },
  natural: { label: { en: "Natural language", ko: "자연어" }, color: "#cbd5e1" },
  artist_unknown: { label: { en: "Unregistered artist", ko: "미등록 작가" }, color: "#f87171" },
  unknown: { label: { en: "Unknown", ko: "미확인" }, color: "#cbd5e1" },
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

const SETTINGS_PANEL_STYLE =
  "box-sizing: border-box; max-width: 560px; line-height: 1.45; display: flex; flex-direction: column; gap: 8px;";
const SETTINGS_ROW_STYLE =
  "display: flex; align-items: center; flex-wrap: wrap; gap: 8px; min-width: 0;";
const SETTINGS_FIELD_STYLE =
  "display: flex; flex-direction: column; gap: 4px; min-width: min(100%, 180px);";
const SETTINGS_INPUT_STYLE =
  "box-sizing: border-box; width: 100%; min-width: 0; padding: 4px 7px;";
const SETTINGS_STATUS_STYLE = "opacity: 0.76; font-size: 0.92em;";
const autoSaveTimers = new Map();

const SETTINGS_TEXT = {
  en: {
    autoSave: "Auto-save enabled",
    saving: "Saving...",
    saved: "Saved automatically",
    current: "Current",
    saveFailed: "Save failed",
    languageTitle: "Settings language",
    languageGuide: "Controls labels inside EasyUse Anima settings panels. The ComfyUI settings list itself may need a browser refresh.",
    languageLabel: "Language",
    english: "English",
    korean: "Korean",
    promptMetadataTitle: "Prompt metadata",
    promptMetadataGuide: "Controls that affect generated prompt text or metadata-only output.",
    metadataFilterGuide: "Comma- or newline-separated prompt tags to remove only from Anima Prompt Builder metadata_prompt. The normal prompt output is not filtered.",
    noFilterWords: "no filter words",
    filterWords: "filter words",
    promptStudioGuide: "Controls Prompt Studio tag highlighting. Colors apply to both highlighted prompt text and the color legend.",
    typoIndicators: "Show typo indicators for unregistered artist / unknown tags",
    naiaGeneralAutoToggle: "When Advanced NAIA is enabled, disable General fields above the NAIA field and re-enable them when NAIA is disabled",
    resetColors: "Reset Colors",
    loraPresetTitle: "LoRA preset",
    loraPresetGuide: "Display options for Anima LoRA Preset.",
    loraDisplayGuide: "Controls how LoRA names are displayed inside Anima LoRA Preset rows.",
    loraDisplay: "LoRA display",
    nameOnly: "Name only",
    fullPath: "Full path",
    naiaBridgeTitle: "NAIA bridge",
    naiaBridgeGuide: "Connection and Prompt Engineering override settings used by Anima NAIA Random Prompt.",
    naiaSettingsGuide: "Controls Anima NAIA Random Prompt connection and Prompt Engineering override options. These values replace the advanced NAIA options that used to live on the node.",
    useDesktopNaia: "Use NAIA desktop Prompt Engineering settings",
    preprocessingOptions: "Preprocessing options",
    desktopSettings: "desktop settings",
    preprocessingOverrides: "preprocessing overrides",
    set: "set",
    empty: "empty",
  },
  ko: {
    autoSave: "자동 저장 사용 중",
    saving: "저장 중...",
    saved: "자동 저장됨",
    current: "현재",
    saveFailed: "저장 실패",
    languageTitle: "설정 언어",
    languageGuide: "EasyUse Anima 설정 패널 내부 라벨 언어를 바꿉니다. ComfyUI 설정 목록 이름은 브라우저 새로고침이 필요할 수 있습니다.",
    languageLabel: "언어",
    english: "영어",
    korean: "한국어",
    promptMetadataTitle: "프롬프트 메타데이터",
    promptMetadataGuide: "생성 프롬프트 텍스트 또는 metadata 전용 출력에 영향을 주는 설정입니다.",
    metadataFilterGuide: "Anima Prompt Builder metadata_prompt에서만 제거할 태그를 쉼표나 줄바꿈으로 입력합니다. 일반 prompt 출력에는 적용되지 않습니다.",
    noFilterWords: "필터 단어 없음",
    filterWords: "필터 단어",
    promptStudioGuide: "Prompt Studio 태그 하이라이트를 제어합니다. 색상은 입력 텍스트와 범례에 같이 적용됩니다.",
    typoIndicators: "미등록 작가 / 미확인 태그 오타 표시",
    naiaGeneralAutoToggle: "Advanced NAIA가 켜지면 NAIA 위쪽 General field를 끄고, NAIA가 꺼지면 다시 켭니다",
    resetColors: "색상 초기화",
    loraPresetTitle: "LoRA 프리셋",
    loraPresetGuide: "Anima LoRA Preset 표시 옵션입니다.",
    loraDisplayGuide: "Anima LoRA Preset 행에서 LoRA 이름을 표시하는 방식을 제어합니다.",
    loraDisplay: "LoRA 표시",
    nameOnly: "이름만",
    fullPath: "전체 경로",
    naiaBridgeTitle: "NAIA 브리지",
    naiaBridgeGuide: "Anima NAIA Random Prompt에 쓰는 연결 및 Prompt Engineering override 설정입니다.",
    naiaSettingsGuide: "Anima NAIA Random Prompt 연결과 Prompt Engineering override 옵션을 제어합니다. 기존에 노드에 있던 고급 NAIA 옵션을 대체합니다.",
    useDesktopNaia: "NAIA 데스크톱 Prompt Engineering 설정 사용",
    preprocessingOptions: "전처리 옵션",
    desktopSettings: "데스크톱 설정",
    preprocessingOverrides: "전처리 override",
    set: "입력됨",
    empty: "비어 있음",
  },
};

function currentSettings(settings = {}) {
  return {
    ...settings,
    ...(window.__easyuseAnimaSettings || {}),
  };
}

function settingsLanguage(settings = {}) {
  const language = String(currentSettings(settings)["ui.language"] || "en").toLowerCase();
  return language === "ko" ? "ko" : "en";
}

function textFor(settings, key) {
  const language = settingsLanguage(settings);
  return SETTINGS_TEXT[language]?.[key] || SETTINGS_TEXT.en[key] || key;
}

function colorLabel(item, settings = {}) {
  const language = settingsLanguage(settings);
  return item.label?.[language] || item.label?.en || "";
}

function mergeSettingCache(settings = {}) {
  window.__easyuseAnimaSettings = {
    ...(window.__easyuseAnimaSettings || {}),
    ...settings,
  };
  return window.__easyuseAnimaSettings;
}

function currentValue(text) {
  const value = document.createElement("div");
  value.textContent = text;
  value.style.cssText = "opacity: 0.68; font-size: 0.9em;";
  return value;
}

function statusLine(initialText = textFor({}, "autoSave")) {
  const status = document.createElement("span");
  status.textContent = initialText;
  status.style.cssText = SETTINGS_STATUS_STYLE;
  return status;
}

function setStatus(status, text, color = "") {
  status.textContent = text;
  status.style.color = color;
}

function formatOnOff(value) {
  return value ? "on" : "off";
}

function updateSettingCache(key, value) {
  window.__easyuseAnimaSettings ||= {};
  window.__easyuseAnimaSettings[key] = String(value ?? "");
}

async function saveSettingAndNotify(key, value, status = null) {
  try {
    if (status) {
      setStatus(status, textFor({}, "saving"), "#64748b");
    }
    const data = await saveSetting(key, value);
    mergeSettingCache(data);
    updateSettingCache(key, value);
    window.dispatchEvent(new CustomEvent("easyuse-anima-settings-updated", { detail: data }));
    if (status) {
      setStatus(status, textFor({}, "saved"), "#16a34a");
    }
    return data;
  } catch (error) {
    if (status) {
      setStatus(status, `${textFor({}, "saveFailed")}: ${error.message || error}`, "#dc2626");
    }
    throw error;
  }
}

function scheduleSettingSave(key, value, status, delay = 400) {
  const timerKey = `${key}`;
  if (autoSaveTimers.has(timerKey)) {
    clearTimeout(autoSaveTimers.get(timerKey));
  }
  autoSaveTimers.set(
    timerKey,
    setTimeout(() => {
      autoSaveTimers.delete(timerKey);
      saveSettingAndNotify(key, value, status).catch(() => {});
    }, delay),
  );
}

function sectionHeader(title, description) {
  const container = document.createElement("div");
  container.style.cssText =
    "box-sizing: border-box; max-width: 560px; padding: 10px 0 4px; border-top: 1px solid rgba(128, 128, 128, 0.28);";

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

function languageEditor(settings = {}) {
  settings = currentSettings(settings);
  const container = document.createElement("div");
  container.style.cssText = SETTINGS_PANEL_STYLE;

  const guide = document.createElement("div");
  guide.textContent = textFor(settings, "languageGuide");
  guide.style.cssText = "opacity: 0.78;";
  container.append(guide);

  const row = document.createElement("div");
  row.style.cssText = SETTINGS_ROW_STYLE;
  const label = document.createElement("label");
  label.style.cssText = SETTINGS_FIELD_STYLE;
  const text = document.createElement("span");
  text.textContent = textFor(settings, "languageLabel");
  const select = document.createElement("select");
  select.style.cssText = SETTINGS_INPUT_STYLE;
  for (const [value, labelText] of [
    ["en", textFor(settings, "english")],
    ["ko", textFor(settings, "korean")],
  ]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labelText;
    option.selected = settingsLanguage(settings) === value;
    select.append(option);
  }
  label.append(text, select);

  const current = currentValue("");
  const status = document.createElement("span");
  status.style.cssText = SETTINGS_STATUS_STYLE;
  const refreshCurrent = () => {
    current.textContent = `${textFor(settings, "current")}: ${select.selectedOptions[0]?.textContent || select.value}`;
  };
  refreshCurrent();
  select.addEventListener("change", () => {
    updateSettingCache("ui.language", select.value);
    refreshCurrent();
    saveSettingAndNotify("ui.language", select.value, status).catch(() => {});
  });

  row.append(label, status);
  container.append(row, current);
  return container;
}

function metadataFilterEditor(initialValue = "") {
  const settings = currentSettings();
  const container = document.createElement("div");
  container.style.cssText = SETTINGS_PANEL_STYLE;

  const guide = document.createElement("div");
  guide.textContent = textFor(settings, "metadataFilterGuide");
  guide.style.cssText = "opacity: 0.78;";
  container.append(guide);

  const textarea = document.createElement("textarea");
  textarea.value = initialValue || "";
  textarea.placeholder = "best quality\nlowres\nhigh detail";
  textarea.rows = 4;
  textarea.style.cssText =
    "box-sizing: border-box; width: 100%; min-height: 86px; resize: vertical;";
  container.append(textarea);

  const current = currentValue("");
  const status = document.createElement("span");
  status.style.cssText = SETTINGS_STATUS_STYLE;
  const refreshCurrent = () => {
    const count = textarea.value
      .split(/[\n,]+/)
      .map((value) => value.trim())
      .filter(Boolean)
      .length;
    current.textContent =
      `${textFor(settings, "current")}: ${count ? `${count} ${textFor(settings, "filterWords")}` : textFor(settings, "noFilterWords")}`;
  };
  refreshCurrent();
  textarea.addEventListener("input", () => {
    refreshCurrent();
    scheduleSettingSave("prompt.metadata_filter_words", textarea.value, status);
  });

  container.append(current, status);

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
  settings = currentSettings(settings);
  const container = document.createElement("div");
  container.style.cssText = SETTINGS_PANEL_STYLE;

  const guide = document.createElement("div");
  guide.textContent = textFor(settings, "promptStudioGuide");
  guide.style.cssText = "opacity: 0.78;";
  container.append(guide);

  const typoRow = document.createElement("label");
  typoRow.style.cssText = SETTINGS_ROW_STYLE;
  const typoToggle = document.createElement("input");
  typoToggle.type = "checkbox";
  typoToggle.checked = settings["prompt_studio.typo_indicator"] !== "false";
  const typoText = document.createElement("span");
  typoText.textContent = textFor(settings, "typoIndicators");
  typoRow.append(typoToggle, typoText);
  container.append(typoRow);

  const naiaGeneralRow = document.createElement("label");
  naiaGeneralRow.style.cssText = "display: flex; align-items: flex-start; flex-wrap: wrap; gap: 7px; min-width: 0;";
  const naiaGeneralToggle = document.createElement("input");
  naiaGeneralToggle.type = "checkbox";
  naiaGeneralToggle.checked = settings["prompt_studio.naia_general_above_auto_toggle"] === "true";
  const naiaGeneralText = document.createElement("span");
  naiaGeneralText.textContent = textFor(settings, "naiaGeneralAutoToggle");
  naiaGeneralText.style.cssText = "min-width: min(100%, 280px);";
  naiaGeneralRow.append(naiaGeneralToggle, naiaGeneralText);
  container.append(naiaGeneralRow);

  const colors = parseColorSettings(settings["prompt_studio.colors"]);
  const grid = document.createElement("div");
  grid.style.cssText =
    "display: grid; grid-template-columns: repeat(auto-fit, minmax(118px, 1fr)); gap: 6px 10px; width: 100%;";
  const colorInputs = new Map();
  for (const [key, item] of Object.entries(PROMPT_STUDIO_COLOR_DEFAULTS)) {
    const label = document.createElement("label");
    label.style.cssText = "display: flex; align-items: center; gap: 7px; font-size: 0.92em;";
    const input = document.createElement("input");
    input.type = "color";
    input.value = colors[key] || item.color;
    input.style.cssText = "width: 34px; height: 24px; padding: 0;";
    const text = document.createElement("span");
    text.textContent = colorLabel(item, settings);
    label.append(input, text);
    grid.append(label);
    colorInputs.set(key, input);
  }
  container.append(grid);

  const controls = document.createElement("div");
  controls.style.cssText = SETTINGS_ROW_STYLE;

  const resetButton = document.createElement("button");
  resetButton.textContent = textFor(settings, "resetColors");
  resetButton.style.cssText = "padding: 5px 10px; cursor: pointer;";

  const current = currentValue("");
  const status = document.createElement("span");
  status.style.cssText = SETTINGS_STATUS_STYLE;

  const collectColors = () => {
    const colorSettings = {};
    for (const [key, input] of colorInputs.entries()) {
      colorSettings[key] = input.value;
    }
    return colorSettings;
  };

  const refreshCurrent = () => {
    current.textContent =
      `${textFor(settings, "current")}: typo ${formatOnOff(typoToggle.checked)}, ` +
      `NAIA general auto-toggle ${formatOnOff(naiaGeneralToggle.checked)}`;
  };

  const saveColors = () => {
    scheduleSettingSave("prompt_studio.colors", JSON.stringify(collectColors()), status, 200);
  };

  resetButton.onclick = () => {
    for (const [key, input] of colorInputs.entries()) {
      input.value = PROMPT_STUDIO_COLOR_DEFAULTS[key].color;
    }
    saveColors();
  };
  typoToggle.addEventListener("change", () => {
    refreshCurrent();
    saveSettingAndNotify("prompt_studio.typo_indicator", typoToggle.checked ? "true" : "false", status).catch(() => {});
  });
  naiaGeneralToggle.addEventListener("change", () => {
    refreshCurrent();
    saveSettingAndNotify(
      "prompt_studio.naia_general_above_auto_toggle",
      naiaGeneralToggle.checked ? "true" : "false",
      status,
    ).catch(() => {});
  });
  for (const input of colorInputs.values()) {
    input.addEventListener("input", saveColors);
    input.addEventListener("change", saveColors);
  }
  refreshCurrent();

  controls.append(resetButton, status);
  container.append(current, controls);
  return container;
}

function loraPresetEditor(settings = {}) {
  settings = currentSettings(settings);
  const container = document.createElement("div");
  container.style.cssText = SETTINGS_PANEL_STYLE;

  const guide = document.createElement("div");
  guide.textContent = textFor(settings, "loraDisplayGuide");
  guide.style.cssText = "opacity: 0.78;";
  container.append(guide);

  const row = document.createElement("div");
  row.style.cssText = SETTINGS_ROW_STYLE;

  const label = document.createElement("label");
  label.style.cssText = SETTINGS_FIELD_STYLE;
  const text = document.createElement("span");
  text.textContent = textFor(settings, "loraDisplay");
  const select = document.createElement("select");
  select.style.cssText = SETTINGS_INPUT_STYLE;
  for (const [value, labelText] of [
    ["name", textFor(settings, "nameOnly")],
    ["path", textFor(settings, "fullPath")],
  ]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labelText;
    option.selected = (settings["lora_preset.name_display"] || "name") === value;
    select.append(option);
  }
  label.append(text, select);

  const current = currentValue("");
  const status = document.createElement("span");
  status.style.cssText = SETTINGS_STATUS_STYLE;

  const refreshCurrent = () => {
    current.textContent = `${textFor(settings, "current")}: ${select.selectedOptions[0]?.textContent || select.value}`;
  };
  refreshCurrent();
  select.addEventListener("change", () => {
    refreshCurrent();
    saveSettingAndNotify("lora_preset.name_display", select.value, status).catch(() => {});
  });

  row.append(label, status);
  container.append(row, current);
  return container;
}

function naiaSettingsEditor(settings = {}) {
  settings = currentSettings(settings);
  const container = document.createElement("div");
  container.style.cssText = SETTINGS_PANEL_STYLE;

  const guide = document.createElement("div");
  guide.textContent = textFor(settings, "naiaSettingsGuide");
  guide.style.cssText = "opacity: 0.78;";
  container.append(guide);

  const endpointRow = document.createElement("div");
  endpointRow.style.cssText = "display: grid; grid-template-columns: minmax(150px, 1fr) minmax(92px, 120px); gap: 8px;";

  const hostLabel = document.createElement("label");
  hostLabel.style.cssText = SETTINGS_FIELD_STYLE;
  const hostText = document.createElement("span");
  hostText.textContent = "Host";
  const hostInput = document.createElement("input");
  hostInput.type = "text";
  hostInput.value = settings["naia.host"] || "127.0.0.1";
  hostInput.style.cssText = SETTINGS_INPUT_STYLE;
  hostLabel.append(hostText, hostInput);

  const portLabel = document.createElement("label");
  portLabel.style.cssText = SETTINGS_FIELD_STYLE;
  const portText = document.createElement("span");
  portText.textContent = "Port";
  const portInput = document.createElement("input");
  portInput.type = "number";
  portInput.min = "1";
  portInput.max = "65535";
  portInput.step = "1";
  portInput.value = String(settings["naia.port"] || 7243);
  portInput.style.cssText = SETTINGS_INPUT_STYLE;
  portLabel.append(portText, portInput);
  endpointRow.append(hostLabel, portLabel);
  container.append(endpointRow);

  const useSettingsRow = document.createElement("label");
  useSettingsRow.style.cssText = SETTINGS_ROW_STYLE;
  const useSettingsToggle = document.createElement("input");
  useSettingsToggle.type = "checkbox";
  useSettingsToggle.checked = settings["naia.use_naia_settings"] !== "false";
  const useSettingsText = document.createElement("span");
  useSettingsText.textContent = textFor(settings, "useDesktopNaia");
  useSettingsRow.append(useSettingsToggle, useSettingsText);
  container.append(useSettingsRow);

  const textStack = document.createElement("div");
  textStack.style.cssText = "display: flex; flex-direction: column; gap: 6px; width: 100%;";
  const promptInputs = new Map();
  for (const [key, labelText] of [
    ["pre_prompt", "Pre prompt"],
    ["post_prompt", "Post prompt"],
    ["auto_hide", "Auto hide"],
  ]) {
    const label = document.createElement("label");
    label.style.cssText = "display: grid; grid-template-columns: 94px minmax(0, 1fr); align-items: center; gap: 8px;";
    const text = document.createElement("span");
    text.textContent = labelText;
    const input = document.createElement("input");
    input.type = "text";
    input.value = settings[`naia.${key}`] || "";
    input.style.cssText = SETTINGS_INPUT_STYLE;
    label.append(text, input);
    textStack.append(label);
    promptInputs.set(key, input);
  }
  container.append(textStack);

  const ppTitle = document.createElement("div");
  ppTitle.textContent = textFor(settings, "preprocessingOptions");
  ppTitle.style.cssText = "font-weight: 700;";
  container.append(ppTitle);

  const ppGrid = document.createElement("div");
  ppGrid.style.cssText =
    "display: grid; grid-template-columns: repeat(auto-fit, minmax(185px, 1fr)); gap: 6px 10px; width: 100%;";
  const preprocessingSelects = new Map();
  for (const [key, labelText] of NAIA_PREPROCESSING_OPTIONS) {
    const label = document.createElement("label");
    label.style.cssText =
      "display: grid; grid-template-columns: minmax(0, 1fr) 68px; align-items: center; gap: 7px; font-size: 0.92em;";
    const text = document.createElement("span");
    text.textContent = labelText;
    text.style.cssText = "min-width: 0;";
    const select = document.createElement("select");
    select.style.cssText = "width: 68px; padding: 3px 4px;";
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
  controls.style.cssText = SETTINGS_ROW_STYLE;

  const current = currentValue("");
  const status = document.createElement("span");
  status.style.cssText = SETTINGS_STATUS_STYLE;

  const sanitizePort = () => {
    const port = Math.max(1, Math.min(65535, Number.parseInt(portInput.value || "7243", 10) || 7243));
    portInput.value = String(port);
    return port;
  };
  const refreshCurrent = () => {
    const promptState = [...promptInputs.entries()]
      .map(([key, input]) => `${key.replace("_", " ")} ${input.value.trim() ? textFor(settings, "set") : textFor(settings, "empty")}`)
      .join(", ");
    const overrideCount = [...preprocessingSelects.values()].filter((select) => select.value !== "skip").length;
    current.textContent =
      `${textFor(settings, "current")}: ${hostInput.value.trim() || "127.0.0.1"}:${portInput.value || "7243"}, ` +
      `${textFor(settings, "desktopSettings")} ${formatOnOff(useSettingsToggle.checked)}, ` +
      `${promptState}, ${textFor(settings, "preprocessingOverrides")} ${overrideCount}`;
  };
  refreshCurrent();

  hostInput.addEventListener("input", () => {
    refreshCurrent();
    scheduleSettingSave("naia.host", hostInput.value.trim() || "127.0.0.1", status);
  });
  hostInput.addEventListener("change", () => {
    refreshCurrent();
    saveSettingAndNotify("naia.host", hostInput.value.trim() || "127.0.0.1", status).catch(() => {});
  });
  portInput.addEventListener("input", () => {
    sanitizePort();
    refreshCurrent();
    scheduleSettingSave("naia.port", portInput.value, status);
  });
  portInput.addEventListener("change", () => {
    sanitizePort();
    refreshCurrent();
    saveSettingAndNotify("naia.port", portInput.value, status).catch(() => {});
  });
  useSettingsToggle.addEventListener("change", () => {
    refreshCurrent();
    saveSettingAndNotify("naia.use_naia_settings", useSettingsToggle.checked ? "true" : "false", status).catch(() => {});
  });
  for (const [key, input] of promptInputs.entries()) {
    input.addEventListener("input", () => {
      refreshCurrent();
      scheduleSettingSave(`naia.${key}`, input.value, status);
    });
    input.addEventListener("change", () => {
      refreshCurrent();
      saveSettingAndNotify(`naia.${key}`, input.value, status).catch(() => {});
    });
  }
  for (const [key, select] of preprocessingSelects.entries()) {
    select.addEventListener("change", () => {
      refreshCurrent();
      saveSettingAndNotify(`naia.${key}`, select.value, status).catch(() => {});
    });
  }

  controls.append(status);
  container.append(current, controls);
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
  container.style.cssText = SETTINGS_PANEL_STYLE;

  const guide = document.createElement("div");
  guide.textContent =
    "Choose which bundled CSV is used for tag autocomplete and Prompt Studio tag highlighting. Korean searches use the selected CSV description text.";
  guide.style.cssText = "opacity: 0.78;";
  container.append(guide);

  const row = document.createElement("div");
  row.style.cssText = SETTINGS_ROW_STYLE;

  const select = document.createElement("select");
  select.style.cssText = "box-sizing: border-box; width: min(100%, 340px); padding: 4px 8px;";

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

  const message = document.createElement("span");
  message.style.cssText = SETTINGS_STATUS_STYLE;

  row.append(select, limitLabel, message);
  container.append(row);

  const panel = document.createElement("div");
  panel.style.cssText = "margin-top: 8px;";
  container.append(panel);
  for (const p of autocompletePanels) {
    if (!p.isConnected) {
      autocompletePanels.delete(p);
    }
  }
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

  const saveAutocompleteSettings = async () => {
    try {
      const limit = Math.max(1, Math.min(100, Number.parseInt(limitInput.value || "20", 10) || 20));
      limitInput.value = String(limit);
      setStatus(message, "Saving...", "#64748b");
      await saveSetting("autocomplete.source", select.value);
      const data = await saveSetting("autocomplete.limit", String(limit));
      updateSettingCache("autocomplete.source", select.value);
      updateSettingCache("autocomplete.limit", String(limit));
      setStatus(message, "Saved automatically", "#16a34a");
      renderOptions({ sources: panel._easyuseSources || [], source: data["autocomplete.source"] });
      window.dispatchEvent(new CustomEvent("easyuse-anima-settings-updated", { detail: data }));
      await refreshAutocompletePanels();
    } catch (error) {
      setStatus(message, `Save failed: ${error.message || error}`, "#dc2626");
    }
  };

  select.addEventListener("change", () => saveAutocompleteSettings());
  limitInput.addEventListener("input", () => {
    scheduleSettingSave("autocomplete.limit", String(
      Math.max(1, Math.min(100, Number.parseInt(limitInput.value || "20", 10) || 20)),
    ), message);
  });
  limitInput.addEventListener("change", () => saveAutocompleteSettings());

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
  for (const p of autocompletePanels) {
    if (!p.isConnected) {
      autocompletePanels.delete(p);
    }
  }
  await Promise.all([...autocompletePanels].map((panel) => refreshAutocompletePanel(panel)));
}

app.registerExtension({
  name: "easyuse-anima.settings",
  async setup() {
    const settings = await getSettings();
    window.__easyuseAnimaSettings = { ...settings };
    const latestSettings = () => currentSettings(settings);

    app.ui.settings.addSetting({
      id: "EasyUseAnima.UI.Language",
      name: "EasyUse Anima: Settings Language",
      type: () => languageEditor(latestSettings()),
      tooltip: "Choose English or Korean labels inside EasyUse Anima settings panels.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Section.Prompt",
      name: "EasyUse Anima: Prompt",
      type: () => sectionHeader(
        textFor(latestSettings(), "promptMetadataTitle"),
        textFor(latestSettings(), "promptMetadataGuide"),
      ),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Prompt.MetadataFilter",
      name: "EasyUse Anima: Metadata Prompt Filter",
      type: () => metadataFilterEditor(latestSettings()["prompt.metadata_filter_words"] || ""),
      tooltip: "Remove these tags only from Anima Prompt Builder metadata_prompt.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Prompt.AutocompleteCsv",
      name: "EasyUse Anima: Autocomplete CSV",
      type: () => autocompleteDatasetSelector({
        source: latestSettings()["autocomplete.source"] || "",
        limit: latestSettings()["autocomplete.limit"] || 20,
      }),
      tooltip: "Select which bundled Korean Danbooru CSV powers autocomplete and tag highlighting.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Prompt.PromptStudio",
      name: "EasyUse Anima: Prompt Studio Highlighting",
      type: () => promptStudioEditor(latestSettings()),
      tooltip: "Configure Prompt Studio typo indicators and tag highlight colors.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Section.LoraPreset",
      name: "EasyUse Anima: LoRA Preset",
      type: () => sectionHeader(
        textFor(latestSettings(), "loraPresetTitle"),
        textFor(latestSettings(), "loraPresetGuide"),
      ),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.LoraPreset.Display",
      name: "EasyUse Anima: LoRA Preset Display",
      type: () => loraPresetEditor(latestSettings()),
      tooltip: "Choose whether LoRA preset rows show only filenames or full relative paths.",
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Section.NAIA",
      name: "EasyUse Anima: NAIA",
      type: () => sectionHeader(
        textFor(latestSettings(), "naiaBridgeTitle"),
        textFor(latestSettings(), "naiaBridgeGuide"),
      ),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.NAIA.Settings",
      name: "EasyUse Anima: NAIA Settings",
      type: () => naiaSettingsEditor(latestSettings()),
      tooltip: "Configure NAIA host, port, Prompt Engineering override, and preprocessing options.",
    });

  },
});
