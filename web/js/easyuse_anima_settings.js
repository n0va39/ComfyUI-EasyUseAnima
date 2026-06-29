import { app } from "../../../scripts/app.js";
import {
  easyuseAnimaLocaleText,
  easyuseAnimaText,
} from "./easyuse_anima_i18n.js";

const ROOT_CATEGORY = "EASY USE ANIMA";

const PROMPT_STUDIO_COLORS = {
  quality: {
    en: "Quality",
    ko: "품질",
    color: "#facc15",
    tip: {
      en: "ANIMA quality/meta tags such as masterpiece, best quality, highres, and aesthetic. Not a Danbooru category number.",
      ko: "masterpiece, best quality, highres, aesthetic 같은 ANIMA 품질/메타 태그입니다. Danbooru 카테고리 번호는 없습니다.",
    },
  },
  safety: {
    en: "Rating",
    ko: "등급",
    color: "#38bdf8",
    tip: {
      en: "Rating-style tags such as safe, sensitive, nsfw, explicit, or rating_*.",
      ko: "safe, sensitive, nsfw, explicit, rating_* 같은 등급 계열 태그입니다.",
    },
  },
  year: {
    en: "Year",
    ko: "연도",
    color: "#2dd4bf",
    tip: {
      en: "Year bucket tags such as newest, recent, mid, early, oldest, or year n.",
      ko: "newest, recent, mid, early, oldest, year n 같은 연도 버킷 태그입니다.",
    },
  },
  count: {
    en: "Count",
    ko: "인원수",
    color: "#60a5fa",
    tip: {
      en: "Person-count tags such as 1girl, 2boys, or multiple girls. These are usually Danbooru category 0 but are highlighted separately.",
      ko: "1girl, 2boys, multiple girls 같은 인원수 태그입니다. 보통 Danbooru category 0이지만 별도 색상으로 표시합니다.",
    },
  },
  character: {
    en: "Character",
    ko: "캐릭터",
    color: "#f472b6",
    tip: {
      en: "Danbooru category 4: character tags.",
      ko: "Danbooru category 4: 캐릭터 태그입니다.",
    },
  },
  artist: {
    en: "Artist",
    ko: "작가",
    color: "#a78bfa",
    tip: {
      en: "Danbooru category 1: artist tags. EasyUse Anima also treats @artist prompt tokens as artist tags.",
      ko: "Danbooru category 1: 작가 태그입니다. EasyUse Anima는 @작가 형식의 프롬프트 토큰도 작가 태그로 취급합니다.",
    },
  },
  copyright: {
    en: "Copyright",
    ko: "작품",
    color: "#fb923c",
    tip: {
      en: "Danbooru category 3: copyright/work tags.",
      ko: "Danbooru category 3: 작품명/저작권 태그입니다.",
    },
  },
  general: {
    en: "Trained tag",
    ko: "학습 태그",
    color: "#4ade80",
    tip: {
      en: "Danbooru category 0: general tags that are present in the selected autocomplete CSV.",
      ko: "Danbooru category 0: 선택한 자동완성 CSV에 있는 일반 태그입니다.",
    },
  },
  meta: {
    en: "Meta",
    ko: "메타",
    color: "#94a3b8",
    tip: {
      en: "Danbooru category 5: meta tags.",
      ko: "Danbooru category 5: 메타 태그입니다.",
    },
  },
  natural: {
    en: "Natural language",
    ko: "자연어",
    color: "#cbd5e1",
    tip: {
      en: "Natural-language prompt text, not a Danbooru tag category.",
      ko: "자연어 프롬프트 문장입니다. Danbooru 태그 카테고리가 아닙니다.",
    },
  },
  comment: {
    en: "Comment",
    ko: "주석",
    color: "#9ca3af",
    tip: {
      en: "Line-start # comments. These are displayed in Prompt Studio but removed from queued prompt tokens.",
      ko: "줄 시작 # 주석입니다. Prompt Studio에는 표시되지만 큐 실행 프롬프트 토큰에서는 제거됩니다.",
    },
  },
  artist_unknown: {
    en: "Unregistered artist",
    ko: "미등록 작가",
    color: "#f87171",
    tip: {
      en: "An @artist token that is not found in the artist index.",
      ko: "@작가 형식이지만 작가 인덱스에서 찾지 못한 토큰입니다.",
    },
  },
  unknown: {
    en: "Unknown",
    ko: "미확인",
    color: "#cbd5e1",
    tip: {
      en: "A tag that was not found in the selected autocomplete CSV or built-in meta rules.",
      ko: "선택한 자동완성 CSV와 내장 메타 규칙에서 찾지 못한 태그입니다.",
    },
  },
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
    autocompleteCommitKey: "Autocomplete commit key",
    autocompleteCommitKeyTip: "Choose whether Enter and Tab commit suggestions, or only Tab commits. Shift+Enter always inserts a line break.",
    autocompleteAppendSeparator: "Append comma after autocomplete",
    autocompleteAppendSeparatorTip: "After committing a suggestion, add ', ' and place the caret after it for the next tag.",
    autocompleteCsvTip: "Select which bundled Korean Danbooru CSV powers autocomplete and tag highlighting.",
    autocompleteLimitTip: "",
    highlightBehavior: "Highlight behavior",
    highlightColor: "Highlight color",
    loraDisplay: "LoRA display",
    loraDisplayTip: "Choose whether LoRA preset rows show only filenames or full relative paths.",
    metadataFilter: "Metadata Prompt Filter",
    metadataFilterTip: "Remove these tags only from Anima Prompt Builder metadata_prompt.",
    promptStudio: "PromptStudio",
    editPromptStudioLongText: "Edit PromptStudio long text",
    editPromptStudioLongTextTip:
      "Open a multiline editor for Metadata Prompt Filter. Values are stored in EasyUse Anima's user data folder.",
    editNaiaLongText: "Edit NAIA long text",
    editNaiaLongTextTip:
      "Open a multiline editor for NAIA Pre prompt, Post prompt, and Auto hide. Values are stored in EasyUse Anima's user data folder.",
    openEditor: "Open editor",
    save: "Save",
    cancel: "Cancel",
    saved: "Saved",
    saveFailed: "Save failed",
    naiaGeneralAutoToggle: "Auto toggle General fields above NAIA",
    naiaGeneralAutoToggleTip:
      "In Anima Prompt Studio Advanced, when the positive NAIA Prompt field is ON, this disables only positive General fields placed above that NAIA field. When the NAIA field is OFF, those General fields are enabled again. Fields below NAIA and negative fields are not changed.",
    naiaEndpoint: "Connection",
    naiaPromptEngineering: "Prompt Engineering",
    naiaDesktopPromptEngineeringTip:
      "ON: ComfyUI does not send Prompt Engineering override values and NAIA 2.0 uses its own desktop settings. OFF: ComfyUI sends the values below as overrides for this request.",
    preprocessingOptions: "Preprocessing options",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
    promptMetadata: "Prompt metadata",
    showTypoIndicators: "Show typo indicators",
    italicizeComments: "Italicize comment lines",
    useDesktopNaia: "Use NAIA desktop Prompt Engineering settings",
  },
  ko: {
    autocomplete: "자동완성",
    autocompleteCsv: "자동완성 CSV",
    autocompleteLimit: "자동완성 추천 수",
    autocompleteMode: "자동완성 적용 범위",
    autocompleteModeTip: "EasyUse Anima 자동완성이 동작할 위치를 정합니다.",
    autocompleteCommitKey: "자동완성 적용 키",
    autocompleteCommitKeyTip: "Enter와 Tab 모두 자동완성을 적용할지, Tab만 적용할지 선택합니다. Shift+Enter는 항상 줄바꿈입니다.",
    autocompleteAppendSeparator: "자동완성 뒤 쉼표 추가",
    autocompleteAppendSeparatorTip: "자동완성 적용 후 ', '를 붙이고 다음 태그를 바로 입력할 수 있게 커서를 이동합니다.",
    autocompleteCsvTip: "자동완성과 태그 하이라이트에 사용할 한국어 Danbooru CSV를 선택합니다.",
    autocompleteLimitTip: "",
    highlightBehavior: "하이라이트 동작",
    highlightColor: "하이라이트 색상",
    loraDisplay: "LoRA 표시",
    loraDisplayTip: "LoRA 프리셋 행에 파일명만 표시할지 상대 경로를 표시할지 선택합니다.",
    metadataFilter: "Metadata Prompt 필터",
    metadataFilterTip: "Anima Prompt Builder metadata_prompt에서만 지정 태그를 제거합니다.",
    promptStudio: "PromptStudio",
    editPromptStudioLongText: "PromptStudio 긴 텍스트 편집",
    editPromptStudioLongTextTip:
      "Metadata Prompt 필터를 여러 줄로 편집합니다. 값은 EasyUse Anima 사용자 데이터 폴더에 저장됩니다.",
    editNaiaLongText: "NAIA 긴 텍스트 편집",
    editNaiaLongTextTip:
      "NAIA Pre prompt, Post prompt, Auto hide를 여러 줄로 편집합니다. 값은 EasyUse Anima 사용자 데이터 폴더에 저장됩니다.",
    openEditor: "편집 열기",
    save: "저장",
    cancel: "취소",
    saved: "저장됨",
    saveFailed: "저장 실패",
    naiaGeneralAutoToggle: "NAIA 위쪽 General 자동 토글",
    naiaGeneralAutoToggleTip:
      "Anima Prompt Studio Advanced에서 긍정 프롬프트의 NAIA Prompt 필드가 켜지면, 그 NAIA 필드보다 위에 있는 긍정 General 필드만 자동으로 OFF합니다. NAIA 필드가 꺼지면 해당 General 필드를 다시 ON합니다. NAIA 아래 필드와 네거티브 필드는 건드리지 않습니다.",
    naiaEndpoint: "연결",
    naiaPromptEngineering: "Prompt Engineering",
    naiaDesktopPromptEngineeringTip:
      "ON: ComfyUI의 Prompt Engineering override 값을 보내지 않고 NAIA 2.0 프로그램의 자체 설정을 사용합니다. OFF: 아래 ComfyUI 설정값을 이번 요청의 override로 NAIA에 보냅니다.",
    preprocessingOptions: "전처리 옵션",
    prePrompt: "Pre prompt",
    postPrompt: "Post prompt",
    autoHide: "Auto hide",
    promptMetadata: "프롬프트 메타데이터",
    showTypoIndicators: "오타 표시",
    italicizeComments: "주석 라인 이탤릭체",
    useDesktopNaia: "NAIA 데스크톱 Prompt Engineering 설정 사용",
  },
};

const INTERNAL_KEYS = {
  "EasyUseAnima.Prompt.MetadataFilter": "prompt.metadata_filter_words",
  "EasyUseAnima.Prompt.AutocompleteMode": "autocomplete.mode",
  "EasyUseAnima.Prompt.AutocompleteSource": "autocomplete.source",
  "EasyUseAnima.Prompt.AutocompleteLimit": "autocomplete.limit",
  "EasyUseAnima.Prompt.AutocompleteCommitKey": "autocomplete.commit_key",
  "EasyUseAnima.Prompt.AutocompleteAppendSeparator": "autocomplete.append_separator",
  "EasyUseAnima.Prompt.TypoIndicator": "prompt_studio.typo_indicator",
  "EasyUseAnima.Prompt.CommentItalic": "prompt_studio.comment_italic",
  "EasyUseAnima.Prompt.NaiaGeneralAutoToggle": "prompt_studio.naia_general_above_auto_toggle",
  "EasyUseAnima.LoraPreset.NameDisplay": "lora_preset.name_display",
  "EasyUseAnima.NAIA.Host": "naia.host",
  "EasyUseAnima.NAIA.Port": "naia.port",
  "EasyUseAnima.NAIA.UseDesktopPromptEngineering": "naia.use_naia_settings",
  "EasyUseAnima.NAIA.pre_prompt": "naia.pre_prompt",
  "EasyUseAnima.NAIA.post_prompt": "naia.post_prompt",
  "EasyUseAnima.NAIA.auto_hide": "naia.auto_hide",
};

const LONG_TEXT_FIELDS = [
  {
    key: "prompt.metadata_filter_words",
    labelKey: "metadataFilter",
    tipKey: "metadataFilterTip",
  },
  {
    key: "naia.pre_prompt",
    labelKey: "prePrompt",
  },
  {
    key: "naia.post_prompt",
    labelKey: "postPrompt",
  },
  {
    key: "naia.auto_hide",
    labelKey: "autoHide",
  },
];

const LONG_TEXT_FIELD_GROUPS = {
  promptStudio: {
    settingId: "EasyUseAnima.PromptStudio.EditLongText",
    section: "PromptStudio",
    nameKey: "editPromptStudioLongText",
    tipKey: "editPromptStudioLongTextTip",
    fields: LONG_TEXT_FIELDS.filter((field) => field.key === "prompt.metadata_filter_words"),
  },
  naia: {
    settingId: "EasyUseAnima.NAIA.EditLongText",
    section: "NAIA",
    nameKey: "editNaiaLongText",
    tipKey: "editNaiaLongTextTip",
    fields: LONG_TEXT_FIELDS.filter((field) => field.key !== "prompt.metadata_filter_words"),
  },
};

let activeLongTextEditor = null;

for (const [key] of NAIA_PREPROCESSING_OPTIONS) {
  INTERNAL_KEYS[`EasyUseAnima.NAIA.${key}`] = `naia.${key}`;
}

function t(key) {
  return easyuseAnimaText(TEXT, key);
}

function label(item) {
  return easyuseAnimaLocaleText(item);
}

function tip(item) {
  return easyuseAnimaLocaleText(item?.tip);
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

async function loadLongTextSettings() {
  const response = await fetch("/easyuse_anima/long_text_settings");
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  const values = data.values || {};
  window.__easyuseAnimaSettings ||= {};
  Object.assign(window.__easyuseAnimaSettings, data.settings || {}, values);
  return { ...window.__easyuseAnimaSettings };
}

async function saveLongTextSettings(values) {
  const response = await fetch("/easyuse_anima/long_text_settings/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ values }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  window.__easyuseAnimaSettings ||= {};
  Object.assign(window.__easyuseAnimaSettings, data.settings || {}, data.values || {});
  window.dispatchEvent(
    new CustomEvent("easyuse-anima-settings-updated", {
      detail: { ...window.__easyuseAnimaSettings },
    }),
  );
  return data;
}

function createLongTextEditorButton(groupKey) {
  const group = LONG_TEXT_FIELD_GROUPS[groupKey];
  const container = document.createElement("div");
  container.style.cssText = "display: flex; align-items: center; gap: 10px; min-width: 0;";

  const button = document.createElement("button");
  button.type = "button";
  button.textContent = t("openEditor");
  button.style.cssText = "padding: 6px 12px; cursor: pointer;";
  button.onclick = () => openLongTextEditor(groupKey);

  const hint = document.createElement("span");
  hint.textContent = t(group.tipKey);
  hint.style.cssText = "opacity: 0.68; font-size: 0.9em; line-height: 1.35;";

  container.append(button, hint);
  return container;
}

function closeLongTextEditor() {
  if (!activeLongTextEditor) {
    return;
  }
  const { overlay, keyHandler } = activeLongTextEditor;
  document.removeEventListener("keydown", keyHandler, true);
  overlay.remove();
  activeLongTextEditor = null;
}

function openLongTextEditor(groupKey) {
  const group = LONG_TEXT_FIELD_GROUPS[groupKey];
  if (!group) {
    return;
  }
  closeLongTextEditor();

  const overlay = document.createElement("div");
  overlay.className = "easyuse-anima-long-text-overlay";
  overlay.style.cssText =
    "position: fixed; inset: 0; z-index: 2147483000; display: flex; align-items: center; justify-content: center; padding: 24px; box-sizing: border-box; background: rgba(0, 0, 0, 0.52);";

  const panel = document.createElement("div");
  panel.className = "comfy-settings easyuse-anima-long-text-panel";
  panel.style.cssText =
    "box-sizing: border-box; width: min(820px, 92vw); max-height: min(780px, 86vh); overflow: hidden; display: flex; flex-direction: column; gap: 12px; padding: 18px; border-radius: 8px; background: var(--comfy-menu-bg, #202020); color: var(--fg-color, #ddd); box-shadow: 0 18px 60px rgba(0, 0, 0, 0.55);";

  const container = document.createElement("div");
  container.style.cssText =
    "box-sizing: border-box; overflow: auto; display: flex; flex-direction: column; gap: 14px; padding-right: 4px;";

  const title = document.createElement("h3");
  title.textContent = t(group.nameKey);
  title.style.margin = "0 0 2px";

  const description = document.createElement("div");
  description.textContent = t(group.tipKey);
  description.style.cssText = "opacity: 0.72; line-height: 1.45;";

  const status = document.createElement("div");
  status.style.cssText = "min-height: 1.4em; opacity: 0.76;";

  const textareas = new Map();
  for (const field of group.fields) {
    const wrapper = document.createElement("label");
    wrapper.style.cssText = "display: flex; flex-direction: column; gap: 6px;";

    const labelText = document.createElement("span");
    labelText.textContent = t(field.labelKey);
    labelText.style.fontWeight = "600";

    const textarea = document.createElement("textarea");
    textarea.spellcheck = false;
    textarea.rows = field.key === "prompt.metadata_filter_words" ? 8 : 7;
    textarea.style.cssText =
      "box-sizing: border-box; width: 100%; min-height: 130px; resize: vertical; padding: 8px; font-family: monospace; white-space: pre-wrap;";

    const help = document.createElement("span");
    help.textContent = field.tipKey ? t(field.tipKey) : "";
    help.style.cssText = "opacity: 0.62; font-size: 0.9em;";

    wrapper.append(labelText, textarea);
    if (help.textContent) {
      wrapper.append(help);
    }
    container.append(wrapper);
    textareas.set(field.key, textarea);
  }

  container.prepend(title, description);
  container.append(status);

  const setStatus = (message, color = "") => {
    status.textContent = message;
    status.style.color = color;
  };

  const actions = document.createElement("div");
  actions.style.cssText = "display: flex; justify-content: flex-end; gap: 8px; flex: 0 0 auto;";

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.textContent = t("cancel");
  cancelButton.style.cssText = "padding: 6px 12px; cursor: pointer;";
  cancelButton.onclick = closeLongTextEditor;

  const saveButton = document.createElement("button");
  saveButton.type = "button";
  saveButton.textContent = t("save");
  saveButton.style.cssText = "padding: 6px 12px; cursor: pointer;";

  saveButton.onclick = async () => {
    const values = {};
    for (const [key, textarea] of textareas.entries()) {
      values[key] = textarea.value;
    }
    saveButton.disabled = true;
    setStatus("...");
    try {
      await saveLongTextSettings(values);
      setStatus(t("saved"), "#16a34a");
      setTimeout(() => {
        if (activeLongTextEditor?.overlay === overlay) {
          closeLongTextEditor();
        }
      }, 150);
    } catch (error) {
      setStatus(`${t("saveFailed")}: ${error.message || error}`, "#dc2626");
    } finally {
      saveButton.disabled = false;
    }
  };

  actions.append(cancelButton, saveButton);
  panel.append(container, actions);
  overlay.append(panel);

  overlay.addEventListener("mousedown", (event) => {
    if (event.target === overlay) {
      closeLongTextEditor();
    }
  });
  panel.addEventListener("mousedown", (event) => event.stopPropagation());

  const keyHandler = (event) => {
    if (event.key === "Escape") {
      closeLongTextEditor();
    }
  };
  document.addEventListener("keydown", keyHandler, true);
  activeLongTextEditor = { overlay, keyHandler };

  document.body.append(overlay);
  loadLongTextSettings()
    .then((settings) => {
      if (activeLongTextEditor?.overlay !== overlay) {
        return;
      }
      for (const [key, textarea] of textareas.entries()) {
        textarea.value = settings[key] || "";
      }
      textareas.values().next().value?.focus();
    })
    .catch((error) => {
      if (activeLongTextEditor?.overlay !== overlay) {
        return;
      }
      setStatus(`${t("saveFailed")}: ${error.message || error}`, "#dc2626");
    });
}

function setting({ id, section, group, name, tooltip, type, defaultValue, options, attrs, onChange }) {
  return {
    id,
    name,
    category: [ROOT_CATEGORY, section, name],
    type,
    defaultValue,
    ...(tooltip ? { tooltip } : {}),
    ...(options ? { options } : {}),
    ...(attrs ? { attrs } : {}),
    onChange:
      onChange ||
      ((value) => {
        updateInternalSetting(id, value, type);
      }),
  };
}

function customSetting({ id, section, name, tooltip, render }) {
  return {
    id,
    name,
    category: [ROOT_CATEGORY, section, name],
    type: render,
    defaultValue: "",
    ...(tooltip ? { tooltip } : {}),
  };
}

function colorSetting(colorKey, item) {
  const id = `EasyUseAnima.Prompt.HighlightColor.${colorKey}`;
  return setting({
    id,
    section: "PromptStudio",
    group: t("highlightColor"),
    name: `${t("highlightColor")}: ${label(item)}`,
    tooltip: tip(item),
    type: "color",
    defaultValue: item.color,
    onChange: (value) => updateColorSetting(colorKey, value),
  });
}

const EASYUSE_ANIMA_SETTINGS = [
  customSetting({
    id: LONG_TEXT_FIELD_GROUPS.promptStudio.settingId,
    section: LONG_TEXT_FIELD_GROUPS.promptStudio.section,
    name: t(LONG_TEXT_FIELD_GROUPS.promptStudio.nameKey),
    tooltip: t(LONG_TEXT_FIELD_GROUPS.promptStudio.tipKey),
    render: () => createLongTextEditorButton("promptStudio"),
  }),
  setting({
    id: "EasyUseAnima.Prompt.AutocompleteMode",
    section: "Autocomplete",
    group: t("autocomplete"),
    name: t("autocompleteMode"),
    tooltip: t("autocompleteModeTip"),
    type: "combo",
    defaultValue: "compatible_global",
    options: ["off", "easyuse_nodes", "compatible_global"],
  }),
  setting({
    id: "EasyUseAnima.Prompt.AutocompleteSource",
    section: "Autocomplete",
    group: t("autocomplete"),
    name: t("autocompleteCsv"),
    tooltip: t("autocompleteCsvTip"),
    type: "combo",
    defaultValue: "localsmile_kr_wiki",
    options: ["localsmile_kr_wiki", "kr_modified"],
  }),
  setting({
    id: "EasyUseAnima.Prompt.AutocompleteLimit",
    section: "Autocomplete",
    group: t("autocomplete"),
    name: t("autocompleteLimit"),
    tooltip: t("autocompleteLimitTip"),
    type: "number",
    defaultValue: 20,
    attrs: { min: 1, max: 100, step: 1 },
  }),
  setting({
    id: "EasyUseAnima.Prompt.AutocompleteCommitKey",
    section: "Autocomplete",
    group: t("autocomplete"),
    name: t("autocompleteCommitKey"),
    tooltip: t("autocompleteCommitKeyTip"),
    type: "combo",
    defaultValue: "enter",
    options: ["enter", "tab"],
  }),
  setting({
    id: "EasyUseAnima.Prompt.AutocompleteAppendSeparator",
    section: "Autocomplete",
    group: t("autocomplete"),
    name: t("autocompleteAppendSeparator"),
    tooltip: t("autocompleteAppendSeparatorTip"),
    type: "boolean",
    defaultValue: false,
  }),
  setting({
    id: "EasyUseAnima.Prompt.TypoIndicator",
    section: "PromptStudio",
    group: t("highlightBehavior"),
    name: t("showTypoIndicators"),
    type: "boolean",
    defaultValue: true,
  }),
  setting({
    id: "EasyUseAnima.Prompt.CommentItalic",
    section: "PromptStudio",
    group: t("highlightBehavior"),
    name: t("italicizeComments"),
    type: "boolean",
    defaultValue: true,
  }),
  setting({
    id: "EasyUseAnima.Prompt.NaiaGeneralAutoToggle",
    section: "PromptStudio",
    group: t("highlightBehavior"),
    name: t("naiaGeneralAutoToggle"),
    tooltip: t("naiaGeneralAutoToggleTip"),
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
    type: "text",
    defaultValue: "127.0.0.1",
  }),
  setting({
    id: "EasyUseAnima.NAIA.Port",
    section: "NAIA",
    group: t("naiaEndpoint"),
    name: "Port",
    type: "text",
    defaultValue: "7243",
  }),
  setting({
    id: "EasyUseAnima.NAIA.UseDesktopPromptEngineering",
    section: "NAIA",
    group: t("naiaPromptEngineering"),
    name: t("useDesktopNaia"),
    tooltip: t("naiaDesktopPromptEngineeringTip"),
    type: "boolean",
    defaultValue: true,
  }),
  customSetting({
    id: LONG_TEXT_FIELD_GROUPS.naia.settingId,
    section: LONG_TEXT_FIELD_GROUPS.naia.section,
    name: t(LONG_TEXT_FIELD_GROUPS.naia.nameKey),
    tooltip: t(LONG_TEXT_FIELD_GROUPS.naia.tipKey),
    render: () => createLongTextEditorButton("naia"),
  }),
  ...NAIA_PREPROCESSING_OPTIONS.map(([key, item]) =>
    setting({
      id: `EasyUseAnima.NAIA.${key}`,
      section: "NAIA",
      group: t("preprocessingOptions"),
      name: label(item),
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
