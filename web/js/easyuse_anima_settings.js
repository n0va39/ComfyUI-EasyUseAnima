import { app } from "../../../scripts/app.js";

const ROOT_CATEGORY = "EASY USE ANIMA";

const PROMPT_STUDIO_COLORS = {
  quality: { en: "Quality", ko: "품질", color: "#facc15" },
  safety: { en: "Rating", ko: "등급", color: "#38bdf8" },
  year: { en: "Year", ko: "연도", color: "#2dd4bf" },
  count: { en: "Count", ko: "인원수", color: "#60a5fa" },
  character: { en: "Character", ko: "캐릭터", color: "#f472b6" },
  artist: { en: "Artist", ko: "작가", color: "#a78bfa" },
  copyright: { en: "Copyright", ko: "작품", color: "#fb923c" },
  general: { en: "Trained tag", ko: "학습 태그", color: "#4ade80" },
  meta: { en: "Meta", ko: "메타", color: "#94a3b8" },
  natural: { en: "Natural language", ko: "자연어", color: "#cbd5e1" },
  artist_unknown: { en: "Unregistered artist", ko: "미등록 작가", color: "#f87171" },
  unknown: { en: "Unknown", ko: "미확인", color: "#cbd5e1" },
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

const TEXT = {
  en: {
    autocomplete: "Autocomplete",
    autocompleteCsv: "Autocomplete CSV",
    autocompleteLimit: "Autocomplete suggestions",
    autocompleteMode: "Autocomplete mode",
    autocompleteModeTip: "Controls where EasyUse Anima autocomplete is active.",
    autocompleteCsvTip: "Select which bundled Korean Danbooru CSV powers autocomplete and tag highlighting.",
    autocompleteLimitTip: "Maximum number of autocomplete suggestions to show.",
    highlightBehavior: "Highlight behavior",
    highlightColor: "Highlight color",
    loraDisplay: "LoRA display",
    loraDisplayTip: "Choose whether LoRA preset rows show only filenames or full relative paths.",
    metadataFilter: "Metadata Prompt Filter",
    metadataFilterTip: "Remove these tags only from Anima Prompt Builder metadata_prompt.",
    naiaGeneralAutoToggle: "Auto toggle General fields above NAIA",
    naiaEndpoint: "Connection",
    naiaPromptEngineering: "Prompt Engineering",
    naiaSettingsTip: "Configure NAIA host, port, Prompt Engineering override, and preprocessing options.",
    preprocessingOptions: "Preprocessing options",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
    promptMetadata: "Prompt metadata",
    showTypoIndicators: "Show typo indicators",
    useDesktopNaia: "Use NAIA desktop Prompt Engineering settings",
  },
  ko: {
    autocomplete: "자동완성",
    autocompleteCsv: "자동완성 CSV",
    autocompleteLimit: "자동완성 추천 수",
    autocompleteMode: "자동완성 적용 범위",
    autocompleteModeTip: "EasyUse Anima 자동완성이 동작할 위치를 정합니다.",
    autocompleteCsvTip: "자동완성과 태그 하이라이트에 사용할 한국어 Danbooru CSV를 선택합니다.",
    autocompleteLimitTip: "자동완성 창에 표시할 추천 항목 수입니다.",
    highlightBehavior: "하이라이트 동작",
    highlightColor: "하이라이트 색상",
    loraDisplay: "LoRA 표시",
    loraDisplayTip: "LoRA 프리셋 행에 파일명만 표시할지 상대 경로를 표시할지 선택합니다.",
    metadataFilter: "Metadata Prompt 필터",
    metadataFilterTip: "Anima Prompt Builder metadata_prompt에서만 지정 태그를 제거합니다.",
    naiaGeneralAutoToggle: "NAIA 위쪽 General 자동 토글",
    naiaEndpoint: "연결",
    naiaPromptEngineering: "Prompt Engineering",
    naiaSettingsTip: "NAIA host, port, Prompt Engineering override, 전처리 옵션을 설정합니다.",
    preprocessingOptions: "전처리 옵션",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
    promptMetadata: "프롬프트 메타데이터",
    showTypoIndicators: "오타 표시",
    useDesktopNaia: "NAIA 데스크톱 Prompt Engineering 설정 사용",
  },
};

const INTERNAL_KEYS = {
  "EasyUseAnima.Prompt.MetadataFilter": "prompt.metadata_filter_words",
  "EasyUseAnima.Prompt.AutocompleteMode": "autocomplete.mode",
  "EasyUseAnima.Prompt.AutocompleteSource": "autocomplete.source",
  "EasyUseAnima.Prompt.AutocompleteLimit": "autocomplete.limit",
  "EasyUseAnima.Prompt.TypoIndicator": "prompt_studio.typo_indicator",
  "EasyUseAnima.Prompt.NaiaGeneralAutoToggle": "prompt_studio.naia_general_above_auto_toggle",
  "EasyUseAnima.LoraPreset.NameDisplay": "lora_preset.name_display",
  "EasyUseAnima.NAIA.Host": "naia.host",
  "EasyUseAnima.NAIA.Port": "naia.port",
  "EasyUseAnima.NAIA.UseDesktopPromptEngineering": "naia.use_naia_settings",
  "EasyUseAnima.NAIA.pre_prompt": "naia.pre_prompt",
  "EasyUseAnima.NAIA.post_prompt": "naia.post_prompt",
  "EasyUseAnima.NAIA.auto_hide": "naia.auto_hide",
};

for (const [key] of NAIA_PREPROCESSING_OPTIONS) {
  INTERNAL_KEYS[`EasyUseAnima.NAIA.${key}`] = `naia.${key}`;
}

function readSettingValue(id) {
  try {
    if (typeof app?.ui?.settings?.getSettingValue === "function") {
      const value = app.ui.settings.getSettingValue(id);
      if (value && typeof value === "object" && "value" in value) {
        return value.value;
      }
      if (value !== undefined) {
        return value;
      }
    }
  } catch {}
  return undefined;
}

function isKorean() {
  const value = String(readSettingValue("Comfy.Locale") || "").toLowerCase();
  return value === "ko" || value.startsWith("ko-") || value.includes("korean") || value.includes("한국어");
}

function t(key) {
  const language = isKorean() ? "ko" : "en";
  return TEXT[language]?.[key] || TEXT.en[key] || key;
}

function label(item) {
  return item?.[isKorean() ? "ko" : "en"] || item?.en || "";
}

function parseColors(value) {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function normalizeValue(type, value) {
  if (type === "boolean") {
    return value ? "true" : "false";
  }
  return String(value ?? "");
}

function updateInternalSetting(id, value, type = "text") {
  const internalKey = INTERNAL_KEYS[id];
  if (!internalKey) {
    return;
  }
  window.__easyuseAnimaSettings ||= {};
  window.__easyuseAnimaSettings[internalKey] = normalizeValue(type, value);
  window.dispatchEvent(
    new CustomEvent("easyuse-anima-settings-updated", {
      detail: { ...window.__easyuseAnimaSettings },
    }),
  );
}

function updateColorSetting(colorKey, value) {
  window.__easyuseAnimaSettings ||= {};
  const colors = parseColors(window.__easyuseAnimaSettings["prompt_studio.colors"]);
  colors[colorKey] = String(value || PROMPT_STUDIO_COLORS[colorKey]?.color || "#ffffff");
  window.__easyuseAnimaSettings["prompt_studio.colors"] = JSON.stringify(colors);
  window.dispatchEvent(
    new CustomEvent("easyuse-anima-settings-updated", {
      detail: { ...window.__easyuseAnimaSettings },
    }),
  );
}

function setting({ id, section, group, name, tooltip, type, defaultValue, options, attrs, onChange }) {
  return {
    id,
    name,
    category: [ROOT_CATEGORY, section, group || name],
    tooltip,
    type,
    defaultValue,
    ...(options ? { options } : {}),
    ...(attrs ? { attrs } : {}),
    onChange:
      onChange ||
      ((value) => {
        updateInternalSetting(id, value, type);
      }),
  };
}

function colorSetting(colorKey, item) {
  const id = `EasyUseAnima.Prompt.HighlightColor.${colorKey}`;
  return setting({
    id,
    section: "Prompt",
    group: t("highlightColor"),
    name: `${t("highlightColor")}: ${label(item)}`,
    tooltip: t("highlightColor"),
    type: "color",
    defaultValue: item.color,
    onChange: (value) => updateColorSetting(colorKey, value),
  });
}

const EASYUSE_ANIMA_SETTINGS = [
  setting({
    id: "EasyUseAnima.Prompt.MetadataFilter",
    section: "Prompt",
    group: t("promptMetadata"),
    name: t("metadataFilter"),
    tooltip: t("metadataFilterTip"),
    type: "text",
    defaultValue: "",
  }),
  setting({
    id: "EasyUseAnima.Prompt.AutocompleteMode",
    section: "Prompt",
    group: t("autocomplete"),
    name: t("autocompleteMode"),
    tooltip: t("autocompleteModeTip"),
    type: "combo",
    defaultValue: "compatible_global",
    options: ["off", "easyuse_nodes", "compatible_global"],
  }),
  setting({
    id: "EasyUseAnima.Prompt.AutocompleteSource",
    section: "Prompt",
    group: t("autocomplete"),
    name: t("autocompleteCsv"),
    tooltip: t("autocompleteCsvTip"),
    type: "combo",
    defaultValue: "localsmile_kr_wiki",
    options: ["localsmile_kr_wiki", "kr_modified"],
  }),
  setting({
    id: "EasyUseAnima.Prompt.AutocompleteLimit",
    section: "Prompt",
    group: t("autocomplete"),
    name: t("autocompleteLimit"),
    tooltip: t("autocompleteLimitTip"),
    type: "number",
    defaultValue: 20,
    attrs: { min: 1, max: 100, step: 1 },
  }),
  setting({
    id: "EasyUseAnima.Prompt.TypoIndicator",
    section: "Prompt",
    group: t("highlightBehavior"),
    name: t("showTypoIndicators"),
    tooltip: t("showTypoIndicators"),
    type: "boolean",
    defaultValue: true,
  }),
  setting({
    id: "EasyUseAnima.Prompt.NaiaGeneralAutoToggle",
    section: "Prompt",
    group: t("highlightBehavior"),
    name: t("naiaGeneralAutoToggle"),
    tooltip: t("naiaGeneralAutoToggle"),
    type: "boolean",
    defaultValue: false,
  }),
  ...Object.entries(PROMPT_STUDIO_COLORS).map(([colorKey, item]) => colorSetting(colorKey, item)),
  setting({
    id: "EasyUseAnima.LoraPreset.NameDisplay",
    section: "LoraPreset",
    group: t("loraDisplay"),
    name: t("loraDisplay"),
    tooltip: t("loraDisplayTip"),
    type: "combo",
    defaultValue: "name",
    options: ["name", "path"],
  }),
  setting({
    id: "EasyUseAnima.NAIA.Host",
    section: "NAIA",
    group: t("naiaEndpoint"),
    name: "Host",
    tooltip: t("naiaSettingsTip"),
    type: "text",
    defaultValue: "127.0.0.1",
  }),
  setting({
    id: "EasyUseAnima.NAIA.Port",
    section: "NAIA",
    group: t("naiaEndpoint"),
    name: "Port",
    tooltip: t("naiaSettingsTip"),
    type: "number",
    defaultValue: 7243,
    attrs: { min: 1, max: 65535, step: 1 },
  }),
  setting({
    id: "EasyUseAnima.NAIA.UseDesktopPromptEngineering",
    section: "NAIA",
    group: t("naiaPromptEngineering"),
    name: t("useDesktopNaia"),
    tooltip: t("naiaSettingsTip"),
    type: "boolean",
    defaultValue: true,
  }),
  ...[
    ["pre_prompt", "prePrompt"],
    ["post_prompt", "postPrompt"],
    ["auto_hide", "autoHide"],
  ].map(([key, textKey]) =>
    setting({
      id: `EasyUseAnima.NAIA.${key}`,
      section: "NAIA",
      group: t("naiaPromptEngineering"),
      name: t(textKey),
      tooltip: t("naiaSettingsTip"),
      type: "text",
      defaultValue: "",
    }),
  ),
  ...NAIA_PREPROCESSING_OPTIONS.map(([key, item]) =>
    setting({
      id: `EasyUseAnima.NAIA.${key}`,
      section: "NAIA",
      group: t("preprocessingOptions"),
      name: label(item),
      tooltip: t("naiaSettingsTip"),
      type: "combo",
      defaultValue: "skip",
      options: ["skip", "on", "off"],
    }),
  ),
];

async function loadInitialSettings() {
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

function addSettingsFallback() {
  const addSetting = app?.ui?.settings?.addSetting;
  if (typeof addSetting !== "function") {
    return;
  }
  const lookup = app.ui.settings.settingsLookup || {};
  for (const item of EASYUSE_ANIMA_SETTINGS) {
    if (!lookup[item.id]) {
      addSetting.call(app.ui.settings, item);
    }
  }
}

app.registerExtension({
  name: "easyuse-anima.settings",
  settings: EASYUSE_ANIMA_SETTINGS,
  async setup() {
    window.__easyuseAnimaSettings = await loadInitialSettings();
    addSettingsFallback();
  },
});
