// @ts-check

export const ROOT_CATEGORY = "EASY USE ANIMA";

export const NAIA_PREPROCESSING_OPTIONS = [
  ["remove_author", { en: "Remove author", ko: "작가 제거", ja: "作者を削除", zh: "移除作者" }],
  ["remove_work_title", { en: "Remove work title", ko: "작품명 제거", ja: "作品名を削除", zh: "移除作品名" }],
  ["remove_character_name", { en: "Remove character name", ko: "캐릭터명 제거", ja: "キャラクター名を削除", zh: "移除角色名" }],
  ["remove_character_features", { en: "Remove character features", ko: "캐릭터 특징 제거", ja: "キャラクター特徴を削除", zh: "移除角色特征" }],
  ["remove_clothes", { en: "Remove clothes", ko: "의상 제거", ja: "衣装を削除", zh: "移除服装" }],
  ["remove_color", { en: "Remove color", ko: "색상 제거", ja: "色を削除", zh: "移除颜色" }],
  ["remove_location_and_background_color", { en: "Remove location/background color", ko: "장소/배경색 제거", ja: "場所/背景色を削除", zh: "移除地点/背景色" }],
  ["remove_expression", { en: "Remove expression", ko: "표정 제거", ja: "表情を削除", zh: "移除表情" }],
  ["remove_pose_action", { en: "Remove pose/action", ko: "포즈/동작 제거", ja: "ポーズ/動作を削除", zh: "移除姿势/动作" }],
  ["remove_meta_tags", { en: "Remove meta tags", ko: "메타 태그 제거", ja: "メタタグを削除", zh: "移除元数据标签" }],
  ["remove_object_tags", { en: "Remove object tags", ko: "오브젝트 태그 제거", ja: "オブジェクトタグを削除", zh: "移除物体标签" }],
  ["remove_noise_tags", { en: "Remove noise tags", ko: "노이즈 태그 제거", ja: "ノイズタグを削除", zh: "移除噪声标签" }],
  ["e621_auto_boost", { en: "e621 auto boost", ko: "e621 자동 강화", ja: "e621 自動強化", zh: "e621 自动增强" }],
  ["danbooru_auto_weight", { en: "Danbooru auto weight", ko: "Danbooru 자동 가중치", ja: "Danbooru 自動重み付け", zh: "Danbooru 自动加权" }],
  ["tag_implication_compression", { en: "Tag implication compression", ko: "태그 함의 압축", ja: "タグ含意圧縮", zh: "标签含义压缩" }],
];

export const NAIA_RESOLUTION_MODE_SCALE = "scale";
export const NAIA_RESOLUTION_MODE_BUCKET = "bucket";
export const NAIA_RESOLUTION_BUCKET_OPTIONS = ["512", "768", "896", "1024", "1280", "1536"];

export const INTERNAL_KEYS = {
  "EasyUseAnima.Prompt.MetadataFilter": "prompt.metadata_filter_words",
  "EasyUseAnima.Prompt.AutocompleteMode": "autocomplete.mode",
  "EasyUseAnima.Prompt.AutocompleteSource": "autocomplete.source",
  "EasyUseAnima.Prompt.AutocompleteLimit": "autocomplete.limit",
  "EasyUseAnima.Prompt.AutocompleteCommitKey": "autocomplete.commit_key",
  "EasyUseAnima.Prompt.AutocompleteAppendSeparator": "autocomplete.append_separator",
  "EasyUseAnima.Prompt.AutocompleteNoCommaAfterPeriod": "autocomplete.no_comma_after_period",
  "EasyUseAnima.Prompt.AutocompleteDetectNaturalSentences": "autocomplete.detect_natural_sentences",
  "EasyUseAnima.Prompt.AutocompletePreviewCompletion": "autocomplete.preview_completion",
  "EasyUseAnima.Prompt.AutocompletePreviewClosingBrackets": "autocomplete.preview_closing_brackets",
  "EasyUseAnima.Prompt.TypoIndicator": "prompt_studio.typo_indicator",
  "EasyUseAnima.Prompt.WeightSyntaxUnderline": "prompt_studio.weight_syntax_underline",
  "EasyUseAnima.Prompt.CommentItalic": "prompt_studio.comment_italic",
  "EasyUseAnima.Prompt.FontOverride": "prompt_studio.font_override",
  "EasyUseAnima.Prompt.FontFamily": "prompt_studio.font_family",
  "EasyUseAnima.Prompt.FontSize": "prompt_studio.font_size",
  "EasyUseAnima.Prompt.HighlightColors": "prompt_studio.colors",
  "EasyUseAnima.Prompt.TrainedTagTooltip": "prompt_studio.trained_tag_tooltip",
  "EasyUseAnima.Prompt.NaiaGeneralAutoToggle": "prompt_studio.naia_general_above_auto_toggle",
  "EasyUseAnima.Prompt.TranslationProvider": "prompt_translation.provider",
  "EasyUseAnima.Prompt.TranslationSource": "prompt_translation.source",
  "EasyUseAnima.Prompt.TranslationTarget": "prompt_translation.target",
  "EasyUseAnima.Wildcard.ExtraPaths": "wildcard.extra_paths",
  "EasyUseAnima.LoraPreset.NameDisplay": "lora_preset.name_display",
  "EasyUseAnima.LoraPreset.MenuMode": "lora_preset.menu_mode",
  "EasyUseAnima.LoraPreset.StrengthButtonStep": "lora_preset.strength_button_step",
  "EasyUseAnima.LoraPreset.StrengthDragStep": "lora_preset.strength_drag_step",
  "EasyUseAnima.LoraPreset.StrengthDragPixels": "lora_preset.strength_drag_pixels",
  "EasyUseAnima.NAIA.Host": "naia.host",
  "EasyUseAnima.NAIA.Port": "naia.port",
  "EasyUseAnima.NAIA.AllowRemoteAPI": "naia.allow_remote_api",
  "EasyUseAnima.NAIA.UseDesktopPromptEngineering": "naia.use_naia_settings",
  "EasyUseAnima.NAIA.ResolutionMode": "naia.resolution_mode",
  "EasyUseAnima.NAIA.ResolutionBucket": "naia.resolution_bucket",
  "EasyUseAnima.NAIA.ResolutionScale": "naia.resolution_scale",
  "EasyUseAnima.NAIA.ResolutionMaxLongEdge": "naia.resolution_max_long_edge",
  "EasyUseAnima.NAIA.pre_prompt": "naia.pre_prompt",
  "EasyUseAnima.NAIA.post_prompt": "naia.post_prompt",
  "EasyUseAnima.NAIA.auto_hide": "naia.auto_hide",
};

for (const [key] of NAIA_PREPROCESSING_OPTIONS) {
  INTERNAL_KEYS[`EasyUseAnima.NAIA.${key}`] = `naia.${key}`;
}

export const LONG_TEXT_FIELDS = [
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

export const LONG_TEXT_FIELD_GROUPS = {
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

export function normalizeValue(type, value) {
  if (type === "boolean") {
    return value ? "true" : "false";
  }
  return String(value ?? "");
}

export function parseWildcardExtraPathItems(value) {
  return String(value ?? "")
    .split(/\r?\n/)
    .map((item) => item.trim().replace(/^"|"$/g, ""))
    .filter(Boolean);
}

export function serializeWildcardExtraPathItems(items) {
  return items
    .map((item) => String(item ?? "").trim())
    .filter(Boolean)
    .join("\n");
}

export function normalizeNaiaResolutionModeValue(value) {
  const raw = String(value ?? "").trim().toLowerCase();
  if (raw === NAIA_RESOLUTION_MODE_BUCKET || raw === "bucket_fit") {
    return NAIA_RESOLUTION_MODE_BUCKET;
  }
  return NAIA_RESOLUTION_MODE_SCALE;
}

export function normalizeNaiaResolutionScaleValue(value) {
  const parsed = Number.parseFloat(String(value ?? "").replace(",", "."));
  const clamped = Number.isFinite(parsed)
    ? Math.min(4.0, Math.max(0.25, parsed))
    : 1.0;
  const rounded = Math.round(clamped * 1000) / 1000;
  return Number.isInteger(rounded) ? `${rounded}.0` : String(rounded);
}
