import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const definitionData = await import(dataModule("../web/js/settings/definition_data.js"));

assert.deepEqual(Object.keys(definitionData).sort(), [
  "INTERNAL_KEYS",
  "LONG_TEXT_FIELDS",
  "LONG_TEXT_FIELD_GROUPS",
  "NAIA_PREPROCESSING_OPTIONS",
  "NAIA_RESOLUTION_BUCKET_OPTIONS",
  "NAIA_RESOLUTION_MODE_BUCKET",
  "NAIA_RESOLUTION_MODE_SCALE",
  "ROOT_CATEGORY",
  "normalizeNaiaResolutionModeValue",
  "normalizeNaiaResolutionScaleValue",
  "normalizeValue",
  "parseWildcardExtraPathItems",
  "serializeWildcardExtraPathItems",
].sort());

const {
  INTERNAL_KEYS,
  LONG_TEXT_FIELDS,
  LONG_TEXT_FIELD_GROUPS,
  NAIA_PREPROCESSING_OPTIONS,
  NAIA_RESOLUTION_BUCKET_OPTIONS,
  NAIA_RESOLUTION_MODE_BUCKET,
  NAIA_RESOLUTION_MODE_SCALE,
  ROOT_CATEGORY,
  normalizeNaiaResolutionModeValue,
  normalizeNaiaResolutionScaleValue,
  normalizeValue,
  parseWildcardExtraPathItems,
  serializeWildcardExtraPathItems,
} = definitionData;

assert.equal(ROOT_CATEGORY, "EASY USE ANIMA");
assert.equal(NAIA_RESOLUTION_MODE_SCALE, "scale");
assert.equal(NAIA_RESOLUTION_MODE_BUCKET, "bucket");
assert.deepEqual(NAIA_RESOLUTION_BUCKET_OPTIONS, [
  "512",
  "768",
  "896",
  "1024",
  "1280",
  "1536",
]);

const preprocessingKeys = [
  "remove_author",
  "remove_work_title",
  "remove_character_name",
  "remove_character_features",
  "remove_clothes",
  "remove_color",
  "remove_location_and_background_color",
  "remove_expression",
  "remove_pose_action",
  "remove_meta_tags",
  "remove_object_tags",
  "remove_noise_tags",
  "e621_auto_boost",
  "danbooru_auto_weight",
  "tag_implication_compression",
];
assert.deepEqual(NAIA_PREPROCESSING_OPTIONS.map(([key]) => key), preprocessingKeys);
for (const [, labels] of NAIA_PREPROCESSING_OPTIONS) {
  assert.deepEqual(Object.keys(labels).sort(), ["en", "ja", "ko", "zh"]);
  for (const value of Object.values(labels)) {
    assert.equal(typeof value, "string");
    assert.ok(value.length > 0);
  }
}

const expectedInternalKeys = {
  "EasyUseAnima.Prompt.MetadataFilter": "prompt.metadata_filter_words",
  "EasyUseAnima.Prompt.AutocompleteMode": "autocomplete.mode",
  "EasyUseAnima.Prompt.AutocompleteSource": "autocomplete.source",
  "EasyUseAnima.Prompt.AutocompleteLimit": "autocomplete.limit",
  "EasyUseAnima.Prompt.AutocompleteArtistPrefix": "autocomplete.artist_prefix",
  "EasyUseAnima.Prompt.AutocompleteCommitKey": "autocomplete.commit_key",
  "EasyUseAnima.Prompt.AutocompleteCommitMode": "autocomplete.commit_mode",
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
for (const key of preprocessingKeys) {
  expectedInternalKeys[`EasyUseAnima.NAIA.${key}`] = `naia.${key}`;
}
assert.deepEqual(INTERNAL_KEYS, expectedInternalKeys);

assert.deepEqual(LONG_TEXT_FIELDS, [
  {
    key: "prompt.metadata_filter_words",
    labelKey: "metadataFilter",
    tipKey: "metadataFilterTip",
  },
  { key: "naia.pre_prompt", labelKey: "prePrompt" },
  { key: "naia.post_prompt", labelKey: "postPrompt" },
  { key: "naia.auto_hide", labelKey: "autoHide" },
]);
assert.deepEqual(LONG_TEXT_FIELD_GROUPS, {
  promptStudio: {
    settingId: "EasyUseAnima.PromptStudio.EditLongText",
    section: "PromptStudio",
    nameKey: "editPromptStudioLongText",
    tipKey: "editPromptStudioLongTextTip",
    fields: [LONG_TEXT_FIELDS[0]],
  },
  naia: {
    settingId: "EasyUseAnima.NAIA.EditLongText",
    section: "NAIA",
    nameKey: "editNaiaLongText",
    tipKey: "editNaiaLongTextTip",
    fields: LONG_TEXT_FIELDS.slice(1),
  },
});

assert.equal(normalizeValue("boolean", true), "true");
assert.equal(normalizeValue("boolean", false), "false");
assert.equal(normalizeValue("boolean", 0), "false");
assert.equal(normalizeValue("boolean", "false"), "true");
assert.equal(normalizeValue("number", 0), "0");
assert.equal(normalizeValue("text", null), "");
assert.equal(normalizeValue("text", undefined), "");

assert.deepEqual(
  parseWildcardExtraPathItems(' D:/wildcards \r\n "relative path"\n\n"opening-only\nclosing-only" '),
  ["D:/wildcards", "relative path", "opening-only", "closing-only"],
);
assert.deepEqual(parseWildcardExtraPathItems(null), []);
const wildcardItems = [" D:/one ", "", null, " relative/two ", undefined];
const wildcardItemsSnapshot = [...wildcardItems];
assert.equal(serializeWildcardExtraPathItems(wildcardItems), "D:/one\nrelative/two");
assert.deepEqual(wildcardItems, wildcardItemsSnapshot);

assert.equal(normalizeNaiaResolutionModeValue("BUCKET"), "bucket");
assert.equal(normalizeNaiaResolutionModeValue("bucket_fit"), "bucket");
assert.equal(normalizeNaiaResolutionModeValue("scale"), "scale");
assert.equal(normalizeNaiaResolutionModeValue("invalid"), "scale");
assert.equal(normalizeNaiaResolutionModeValue(null), "scale");

assert.equal(normalizeNaiaResolutionScaleValue("1,5"), "1.5");
assert.equal(normalizeNaiaResolutionScaleValue("1.2346"), "1.235");
assert.equal(normalizeNaiaResolutionScaleValue(2), "2.0");
assert.equal(normalizeNaiaResolutionScaleValue(0), "0.25");
assert.equal(normalizeNaiaResolutionScaleValue(9), "4.0");
assert.equal(normalizeNaiaResolutionScaleValue("invalid"), "1.0");
assert.equal(normalizeNaiaResolutionScaleValue("Infinity"), "1.0");
