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
  ["remove_author", { en: "Remove author", ko: "작가 제거" }],
  ["remove_work_title", { en: "Remove work title", ko: "작품명 제거" }],
  ["remove_character_name", { en: "Remove character name", ko: "캐릭터명 제거" }],
  ["remove_character_features", { en: "Remove character features", ko: "캐릭터 특징 제거" }],
  ["remove_clothes", { en: "Remove clothes", ko: "의상 제거" }],
  ["remove_color", { en: "Remove color", ko: "색상 제거" }],
  ["remove_location_and_background_color", { en: "Remove location/background color", ko: "장소/배경색 제거" }],
  ["remove_expression", { en: "Remove expression", ko: "표정 제거" }],
  ["remove_pose_action", { en: "Remove pose/action", ko: "포즈/동작 제거" }],
  ["remove_meta_tags", { en: "Remove meta tags", ko: "메타 태그 제거" }],
  ["remove_object_tags", { en: "Remove object tags", ko: "오브젝트 태그 제거" }],
  ["remove_noise_tags", { en: "Remove noise tags", ko: "노이즈 태그 제거" }],
  ["e621_auto_boost", { en: "e621 auto boost", ko: "e621 자동 강화" }],
  ["danbooru_auto_weight", { en: "Danbooru auto weight", ko: "Danbooru 자동 가중치" }],
  ["tag_implication_compression", { en: "Tag implication compression", ko: "태그 함의 압축" }],
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
const SETTINGS_BLOCK_STYLE =
  "display: flex; flex-direction: column; gap: 6px; padding: 8px 0 0; border-top: 1px solid rgba(128, 128, 128, 0.22);";
const SETTINGS_DESCRIPTION_STYLE = "opacity: 0.7; font-size: 0.92em; line-height: 1.45;";
const SETTINGS_SETTING_ROW_STYLE =
  "display: grid; grid-template-columns: minmax(160px, 240px) minmax(180px, 1fr); align-items: center; gap: 10px 24px; padding: 8px 0;";
const SETTINGS_SETTING_LABEL_STYLE = "opacity: 0.78; min-width: 0;";
const SETTINGS_SETTING_CONTROL_STYLE = "display: flex; justify-content: flex-end; min-width: 0;";
const autoSaveTimers = new Map();

const SETTINGS_TEXT = {
  en: {
    autoSave: "Auto-save enabled",
    saving: "Saving...",
    saved: "Saved automatically",
    current: "Current",
    saveFailed: "Save failed",
    on: "on",
    off: "off",
    settingsPromptSectionName: "Prompt",
    settingsPromptMetadataName: "Metadata Prompt Filter",
    settingsPromptMetadataTooltip: "Remove these tags only from Anima Prompt Builder metadata_prompt.",
    settingsAutocompleteCsvName: "Autocomplete",
    settingsAutocompleteCsvTooltip: "Select which bundled Korean Danbooru CSV powers autocomplete and tag highlighting.",
    settingsPromptStudioName: "Prompt Studio Highlighting",
    settingsPromptStudioTooltip: "Configure Prompt Studio typo indicators and tag highlight colors.",
    settingsLoraSectionName: "LoraPreset",
    settingsLoraDisplayName: "LoRA display",
    settingsLoraDisplayTooltip: "Choose whether LoRA preset rows show only filenames or full relative paths.",
    settingsNaiaSectionName: "NAIA",
    settingsNaiaName: "NAIA settings",
    settingsNaiaTooltip: "Configure NAIA host, port, Prompt Engineering override, and preprocessing options.",
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
    autocompleteGuide: "Choose which bundled CSV is used for tag autocomplete and Prompt Studio tag highlighting. Korean searches use the selected CSV description text.",
    autocompleteMode: "Autocomplete mode",
    autocompleteModeOff: "Off",
    autocompleteModeEasyUse: "EasyUse Anima nodes only",
    autocompleteModeCompatible: "Compatible global",
    autocompleteModeGuide: "Controls where EasyUse Anima autocomplete is active. Compatible global keeps the current behavior and avoids nodes that already provide their own autocomplete.",
    autocompleteCsv: "Autocomplete CSV",
    highlightBehavior: "Highlight behavior",
    highlightColors: "Highlight colors",
    naiaEndpoint: "Connection",
    naiaPromptEngineering: "Prompt Engineering",
    suggestions: "Suggestions",
    autocompleteReady: "Autocomplete CSV is ready",
    autocompleteMissing: "Selected autocomplete CSV is missing.",
    selected: "Selected",
    selectedCsv: "selected CSV",
    tagCount: "Tag count",
    path: "Path",
    source: "Source",
    refreshAutocompleteStatus: "Refresh Autocomplete Status",
    autocompleteStatusFailed: "Could not read autocomplete CSV status",
    missing: "missing",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
  },
  ko: {
    autoSave: "자동 저장 사용 중",
    saving: "저장 중...",
    saved: "자동 저장됨",
    current: "현재",
    saveFailed: "저장 실패",
    on: "켜짐",
    off: "꺼짐",
    settingsPromptSectionName: "Prompt",
    settingsPromptMetadataName: "Metadata Prompt 필터",
    settingsPromptMetadataTooltip: "Anima Prompt Builder metadata_prompt에서만 지정 태그를 제거합니다.",
    settingsAutocompleteCsvName: "자동완성",
    settingsAutocompleteCsvTooltip: "자동완성과 태그 하이라이트에 사용할 한국어 Danbooru CSV를 선택합니다.",
    settingsPromptStudioName: "Prompt Studio 하이라이트",
    settingsPromptStudioTooltip: "Prompt Studio 오타 표시와 태그 하이라이트 색상을 설정합니다.",
    settingsLoraSectionName: "LoraPreset",
    settingsLoraDisplayName: "LoRA 표시",
    settingsLoraDisplayTooltip: "LoRA 프리셋 행에 파일명만 표시할지 상대 경로를 표시할지 선택합니다.",
    settingsNaiaSectionName: "NAIA",
    settingsNaiaName: "NAIA 설정",
    settingsNaiaTooltip: "NAIA host, port, Prompt Engineering override, 전처리 옵션을 설정합니다.",
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
    autocompleteGuide: "태그 자동완성과 Prompt Studio 태그 하이라이트에 사용할 내장 CSV를 선택합니다. 한국어 검색은 선택한 CSV의 설명 텍스트를 사용합니다.",
    autocompleteMode: "자동완성 적용 범위",
    autocompleteModeOff: "전부 끄기",
    autocompleteModeEasyUse: "EasyUse Anima 노드에서만",
    autocompleteModeCompatible: "호환 전역 모드",
    autocompleteModeGuide: "EasyUse Anima 자동완성이 동작할 위치를 정합니다. 호환 전역 모드는 기존 방식이며 자체 자동완성을 가진 노드는 제외합니다.",
    autocompleteCsv: "자동완성 CSV",
    highlightBehavior: "하이라이트 동작",
    highlightColors: "하이라이트 색상",
    naiaEndpoint: "연결",
    naiaPromptEngineering: "Prompt Engineering",
    suggestions: "추천 수",
    autocompleteReady: "자동완성 CSV 준비됨",
    autocompleteMissing: "선택한 자동완성 CSV가 없습니다.",
    selected: "선택됨",
    selectedCsv: "선택된 CSV",
    tagCount: "태그 수",
    path: "경로",
    source: "출처",
    refreshAutocompleteStatus: "자동완성 상태 새로고침",
    autocompleteStatusFailed: "자동완성 CSV 상태를 읽을 수 없음",
    missing: "없음",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
  },
};

function currentSettings(settings = {}) {
  return {
    ...settings,
    ...(window.__easyuseAnimaSettings || {}),
  };
}

const COMFY_LANGUAGE_SETTING_KEYS = [
  "Comfy.Locale",
  "Comfy.Locale.Language",
  "Comfy.Language",
  "ComfyUI.Locale",
  "ComfyUI.Language",
  "locale",
  "language",
];

function settingValueFromObject(container, key) {
  const entry = container?.[key];
  if (entry == null) {
    return undefined;
  }
  if (typeof entry === "object" && "value" in entry) {
    return entry.value;
  }
  return entry;
}

function readComfySettingValue(key) {
  try {
    const getter = app?.ui?.settings?.getSettingValue;
    if (typeof getter === "function") {
      const value = getter.call(app.ui.settings, key);
      if (value != null && typeof value !== "object") {
        return value;
      }
      if (value && "value" in value) {
        return value.value;
      }
    }
  } catch {}

  for (const container of [
    app?.ui?.settings?.settings,
    app?.ui?.settings?._settings,
    app?.ui?.settings?.settingValues,
    window?.comfyAPI?.settings,
  ]) {
    const value = settingValueFromObject(container, key);
    if (value != null) {
      return value;
    }
  }

  if (key.toLowerCase().includes("comfy")) {
    try {
      const value = localStorage.getItem(key);
      if (value != null) {
        return value;
      }
    } catch {}
  }

  return undefined;
}

function readComfyLanguage() {
  for (const key of COMFY_LANGUAGE_SETTING_KEYS) {
    const value = readComfySettingValue(key);
    if (value != null && String(value).trim()) {
      return String(value);
    }
  }
  return "";
}

function isKoreanLanguage(value) {
  const normalized = String(value || "").trim().replace(/^["']|["']$/g, "").toLowerCase().replace("_", "-");
  return normalized === "ko" || normalized.startsWith("ko-") || normalized.includes("korean") || normalized.includes("한국어");
}

function settingsLanguage(_settings = {}) {
  return isKoreanLanguage(readComfyLanguage()) ? "ko" : "en";
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

function formatOnOff(value, settings = {}) {
  return value ? textFor(settings, "on") : textFor(settings, "off");
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

function createSettingBlock(title) {
  const block = document.createElement("div");
  block.style.cssText = SETTINGS_BLOCK_STYLE;

  const heading = document.createElement("div");
  heading.textContent = title;
  heading.style.cssText = "font-weight: 650;";
  block.append(heading);

  return block;
}

function wrapEditorBlock(title, editor) {
  const block = createSettingBlock(title);
  for (const child of [...editor.childNodes]) {
    block.append(child);
  }
  return block;
}

function appendDescription(container, description = "") {
  if (!description) {
    return null;
  }
  const text = document.createElement("div");
  text.textContent = description;
  text.style.cssText = SETTINGS_DESCRIPTION_STYLE;
  container.append(text);
  return text;
}

function createSettingsRow(labelText, control, description = "") {
  const container = document.createElement("div");
  container.style.cssText = "display: flex; flex-direction: column; gap: 4px;";

  const row = document.createElement("label");
  row.style.cssText = SETTINGS_SETTING_ROW_STYLE;

  const label = document.createElement("span");
  label.textContent = labelText;
  label.style.cssText = SETTINGS_SETTING_LABEL_STYLE;

  const controlWrap = document.createElement("div");
  controlWrap.style.cssText = SETTINGS_SETTING_CONTROL_STYLE;
  controlWrap.append(control);

  row.append(label, controlWrap);
  container.append(row);
  appendDescription(container, description);
  return container;
}

function metadataFilterEditor(initialValue = "") {
  const settings = currentSettings();
  const container = document.createElement("div");
  container.style.cssText = SETTINGS_PANEL_STYLE;

  const textarea = document.createElement("textarea");
  textarea.value = initialValue || "";
  textarea.placeholder = "best quality\nlowres\nhigh detail";
  textarea.rows = 4;
  textarea.style.cssText =
    "box-sizing: border-box; width: 100%; min-height: 86px; resize: vertical;";
  container.append(textarea);
  appendDescription(container, textFor(settings, "metadataFilterGuide"));

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

  const behaviorBlock = createSettingBlock(textFor(settings, "highlightBehavior"));

  const typoRow = document.createElement("label");
  typoRow.style.cssText = SETTINGS_ROW_STYLE;
  const typoToggle = document.createElement("input");
  typoToggle.type = "checkbox";
  typoToggle.checked = settings["prompt_studio.typo_indicator"] !== "false";
  const typoText = document.createElement("span");
  typoText.textContent = textFor(settings, "typoIndicators");
  typoRow.append(typoToggle, typoText);
  behaviorBlock.append(typoRow);

  const naiaGeneralRow = document.createElement("label");
  naiaGeneralRow.style.cssText = "display: flex; align-items: flex-start; flex-wrap: wrap; gap: 7px; min-width: 0;";
  const naiaGeneralToggle = document.createElement("input");
  naiaGeneralToggle.type = "checkbox";
  naiaGeneralToggle.checked = settings["prompt_studio.naia_general_above_auto_toggle"] === "true";
  const naiaGeneralText = document.createElement("span");
  naiaGeneralText.textContent = textFor(settings, "naiaGeneralAutoToggle");
  naiaGeneralText.style.cssText = "min-width: min(100%, 280px);";
  naiaGeneralRow.append(naiaGeneralToggle, naiaGeneralText);
  behaviorBlock.append(naiaGeneralRow);

  const colors = parseColorSettings(settings["prompt_studio.colors"]);
  const colorBlock = createSettingBlock(textFor(settings, "highlightColors"));
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
  colorBlock.append(grid);

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
      `${textFor(settings, "current")}: typo ${formatOnOff(typoToggle.checked, settings)}, ` +
      `NAIA general auto-toggle ${formatOnOff(naiaGeneralToggle.checked, settings)}`;
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

  behaviorBlock.append(current);
  appendDescription(behaviorBlock, textFor(settings, "promptStudioGuide"));
  controls.append(resetButton, status);
  colorBlock.append(controls);
  container.append(behaviorBlock, colorBlock);
  return container;
}

function promptSettingsEditor(settings = {}) {
  settings = currentSettings(settings);
  const container = document.createElement("div");
  container.style.cssText = `${SETTINGS_PANEL_STYLE} gap: 14px;`;

  container.append(
    wrapEditorBlock(
      textFor(settings, "settingsPromptMetadataName"),
      metadataFilterEditor(settings["prompt.metadata_filter_words"] || ""),
    ),
    wrapEditorBlock(
      textFor(settings, "settingsAutocompleteCsvName"),
      autocompleteDatasetSelector({
        source: settings["autocomplete.source"] || "",
        limit: settings["autocomplete.limit"] || 20,
        mode: settings["autocomplete.mode"] || "compatible_global",
      }),
    ),
    wrapEditorBlock(textFor(settings, "settingsPromptStudioName"), promptStudioEditor(settings)),
  );

  return container;
}

function loraPresetEditor(settings = {}) {
  settings = currentSettings(settings);
  const container = document.createElement("div");
  container.style.cssText = SETTINGS_PANEL_STYLE;
  const block = createSettingBlock(textFor(settings, "settingsLoraDisplayName"));

  const row = document.createElement("div");
  row.style.cssText = SETTINGS_ROW_STYLE;

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

  row.append(select, status);
  block.append(row);
  appendDescription(block, textFor(settings, "loraDisplayGuide"));
  block.append(current);
  container.append(block);
  return container;
}

function naiaSettingsEditor(settings = {}) {
  settings = currentSettings(settings);
  const container = document.createElement("div");
  container.style.cssText = SETTINGS_PANEL_STYLE;

  const endpointBlock = createSettingBlock(textFor(settings, "naiaEndpoint"));
  const promptBlock = createSettingBlock(textFor(settings, "naiaPromptEngineering"));
  const preprocessingBlock = createSettingBlock(textFor(settings, "preprocessingOptions"));

  const hostInput = document.createElement("input");
  hostInput.type = "text";
  hostInput.value = settings["naia.host"] || "127.0.0.1";
  hostInput.style.cssText = `${SETTINGS_INPUT_STYLE} max-width: 360px;`;

  const portInput = document.createElement("input");
  portInput.type = "number";
  portInput.min = "1";
  portInput.max = "65535";
  portInput.step = "1";
  portInput.value = String(settings["naia.port"] || 7243);
  portInput.style.cssText = `${SETTINGS_INPUT_STYLE} max-width: 180px;`;

  endpointBlock.append(
    createSettingsRow("Host", hostInput),
    createSettingsRow("Port", portInput),
  );
  appendDescription(endpointBlock, textFor(settings, "naiaSettingsGuide"));

  const useSettingsToggle = document.createElement("input");
  useSettingsToggle.type = "checkbox";
  useSettingsToggle.checked = settings["naia.use_naia_settings"] !== "false";
  promptBlock.append(createSettingsRow(textFor(settings, "useDesktopNaia"), useSettingsToggle));

  const textStack = document.createElement("div");
  textStack.style.cssText = "display: flex; flex-direction: column; gap: 2px; width: 100%;";
  const promptInputs = new Map();
  for (const [key, labelText] of [
    ["pre_prompt", textFor(settings, "prePrompt")],
    ["post_prompt", textFor(settings, "postPrompt")],
    ["auto_hide", textFor(settings, "autoHide")],
  ]) {
    const input = document.createElement("input");
    input.type = "text";
    input.value = settings[`naia.${key}`] || "";
    input.style.cssText = `${SETTINGS_INPUT_STYLE} max-width: 420px;`;
    textStack.append(createSettingsRow(labelText, input));
    promptInputs.set(key, input);
  }
  promptBlock.append(textStack);

  const ppStack = document.createElement("div");
  ppStack.style.cssText = "display: flex; flex-direction: column; gap: 2px; width: 100%;";
  const preprocessingSelects = new Map();
  for (const [key, labelText] of NAIA_PREPROCESSING_OPTIONS) {
    const select = document.createElement("select");
    select.style.cssText = "width: 96px; padding: 4px 6px;";
    for (const value of ["skip", "on", "off"]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      option.selected = (settings[`naia.${key}`] || "skip") === value;
      select.append(option);
    }
    ppStack.append(createSettingsRow(labelText?.[settingsLanguage(settings)] || labelText?.en || String(labelText || key), select));
    preprocessingSelects.set(key, select);
  }
  preprocessingBlock.append(ppStack);

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
      `${textFor(settings, "desktopSettings")} ${formatOnOff(useSettingsToggle.checked, settings)}, ` +
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
  container.append(endpointBlock, promptBlock, preprocessingBlock, current, controls);
  return container;
}

function autocompleteDatasetSelector(initialValue = {}) {
  const settings = currentSettings();
  const initialSource =
    typeof initialValue === "object" && initialValue !== null
      ? initialValue.source || ""
      : String(initialValue || "");
  const initialLimit =
    typeof initialValue === "object" && initialValue !== null
      ? initialValue.limit || 20
      : 20;
  const initialMode =
    typeof initialValue === "object" && initialValue !== null
      ? initialValue.mode || "compatible_global"
      : "compatible_global";
  const container = document.createElement("div");
  container.style.cssText = SETTINGS_PANEL_STYLE;

  const modeBlock = createSettingBlock(textFor(settings, "autocompleteMode"));
  const csvBlock = createSettingBlock(textFor(settings, "autocompleteCsv"));

  const modeRow = document.createElement("label");
  modeRow.style.cssText = "display: flex; flex-direction: column; gap: 4px; min-width: 0;";
  const modeSelect = document.createElement("select");
  modeSelect.style.cssText = "box-sizing: border-box; width: min(100%, 340px); padding: 4px 8px;";
  for (const [value, labelKey] of [
    ["off", "autocompleteModeOff"],
    ["easyuse_nodes", "autocompleteModeEasyUse"],
    ["compatible_global", "autocompleteModeCompatible"],
  ]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = textFor(settings, labelKey);
    option.selected = value === initialMode;
    modeSelect.append(option);
  }
  modeRow.append(modeSelect);
  modeBlock.append(modeRow);
  appendDescription(modeBlock, textFor(settings, "autocompleteModeGuide"));

  const row = document.createElement("div");
  row.style.cssText = SETTINGS_ROW_STYLE;

  const select = document.createElement("select");
  select.style.cssText = "box-sizing: border-box; width: min(100%, 340px); padding: 4px 8px;";

  const limitLabel = document.createElement("label");
  limitLabel.style.cssText = "display: flex; align-items: center; gap: 6px;";
  const limitText = document.createElement("span");
  limitText.textContent = textFor(settings, "suggestions");
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
  csvBlock.append(row);
  appendDescription(csvBlock, textFor(settings, "autocompleteGuide"));

  const panel = document.createElement("div");
  panel.style.cssText = "margin-top: 8px;";
  csvBlock.append(panel);
  container.append(modeBlock, csvBlock);
  autocompletePanels.add(panel);

  const renderOptions = (status) => {
    const sources = Array.isArray(status.sources) ? status.sources : [];
    const selected = status.source || initialSource;
    select.replaceChildren();
    for (const source of sources) {
      const option = document.createElement("option");
      option.value = source.key;
      option.textContent = source.exists ? source.label : `${source.label} (${textFor(settings, "missing")})`;
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
      panel.textContent = `${textFor(settings, "autocompleteStatusFailed")}: ${error.message || error}`;
    }
  };

  const saveAutocompleteSettings = async () => {
    try {
      const limit = Math.max(1, Math.min(100, Number.parseInt(limitInput.value || "20", 10) || 20));
      const sourceValue = select.value || initialSource || settings["autocomplete.source"] || "";
      limitInput.value = String(limit);
      setStatus(message, textFor(settings, "saving"), "#64748b");
      await saveSetting("autocomplete.source", sourceValue);
      await saveSetting("autocomplete.limit", String(limit));
      const data = await saveSetting("autocomplete.mode", modeSelect.value);
      updateSettingCache("autocomplete.source", sourceValue);
      updateSettingCache("autocomplete.limit", String(limit));
      updateSettingCache("autocomplete.mode", modeSelect.value);
      setStatus(message, textFor(settings, "saved"), "#16a34a");
      renderOptions({ sources: panel._easyuseSources || [], source: data["autocomplete.source"] });
      window.dispatchEvent(new CustomEvent("easyuse-anima-settings-updated", { detail: data }));
      await refreshAutocompletePanels();
    } catch (error) {
      setStatus(message, `${textFor(settings, "saveFailed")}: ${error.message || error}`, "#dc2626");
    }
  };

  modeSelect.addEventListener("change", () => saveAutocompleteSettings());
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
  const settings = currentSettings();
  panel.replaceChildren();
  panel._easyuseSources = Array.isArray(status.sources) ? status.sources : [];

  const selected = panel._easyuseSources.find((source) => source.key === status.source);
  const banner = document.createElement("div");
  banner.textContent = status.exists
    ? `${textFor(settings, "autocompleteReady")}: ${selected?.label || status.source || textFor(settings, "selectedCsv")}`
    : textFor(settings, "autocompleteMissing");
  banner.style.cssText = status.exists
    ? "margin: 8px 0; padding: 8px 10px; border-radius: 6px; background: rgba(22, 163, 74, 0.16); color: #16a34a; font-weight: 700;"
    : "margin: 8px 0; padding: 8px 10px; border-radius: 6px; background: rgba(220, 38, 38, 0.14); color: #dc2626; font-weight: 700;";
  panel.append(banner);

  appendLine(panel, textFor(settings, "selected"), selected?.label || status.source || "");
  appendLine(panel, textFor(settings, "tagCount"), Number(status.count || 0).toLocaleString());
  appendPathLine(panel, textFor(settings, "path"), status.path || "");

  if (selected?.source) {
    appendLine(panel, textFor(settings, "source"), selected.source, "opacity: 0.72; font-weight: 400;");
  }

  const refresh = document.createElement("button");
  refresh.textContent = textFor(settings, "refreshAutocompleteStatus");
  refresh.style.cssText = "margin-top: 8px; padding: 4px 10px; cursor: pointer;";
  refresh.onclick = () => refreshAutocompletePanel(panel);
  panel.append(refresh);
}

async function refreshAutocompletePanel(panel) {
  const settings = currentSettings();
  try {
    const status = await getAutocompleteStatus();
    renderAutocompletePanel(panel, status);
  } catch (error) {
    panel.textContent = `${textFor(settings, "autocompleteStatusFailed")}: ${error.message || error}`;
  }
}

async function refreshAutocompletePanels() {
  await Promise.all([...autocompletePanels].map((panel) => refreshAutocompletePanel(panel)));
}

app.registerExtension({
  name: "easyuse-anima.settings",
  async setup() {
    const settings = await getSettings();
    window.__easyuseAnimaSettings = { ...settings };
    const latestSettings = () => currentSettings(settings);

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Section.Prompt",
      name: textFor(latestSettings(), "settingsPromptSectionName"),
      type: () => promptSettingsEditor(latestSettings()),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Section.LoraPreset",
      name: textFor(latestSettings(), "settingsLoraSectionName"),
      type: () => loraPresetEditor(latestSettings()),
      tooltip: textFor(latestSettings(), "settingsLoraDisplayTooltip"),
    });

    app.ui.settings.addSetting({
      id: "EasyUseAnima.Section.NAIA",
      name: textFor(latestSettings(), "settingsNaiaSectionName"),
      type: () => naiaSettingsEditor(latestSettings()),
      tooltip: textFor(latestSettings(), "settingsNaiaTooltip"),
    });

  },
});
