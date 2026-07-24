import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath, replacements = {}) {
  let source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  for (const [from, to] of Object.entries(replacements)) {
    source = source.replaceAll(from, to);
  }
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const settingValues = { "Comfy.Locale": "" };
globalThis.window = {};
globalThis.__easyuseAnimaI18nTestApp = {
  ui: {
    settings: {
      getSettingValue(id) {
        return settingValues[id];
      },
    },
  },
};
const i18nModuleUrl = dataModule("../web/js/easyuse_anima_i18n.js", {
  'import { app } from "../../../scripts/app.js";':
    "const app = globalThis.__easyuseAnimaI18nTestApp;",
});
const i18nModule = await import(i18nModuleUrl);
const definitionDataUrl = dataModule("../web/js/settings/definition_data.js");
const definitionsModule = await import(
  dataModule("../web/js/settings/definitions.js", {
    "./definition_data.js": definitionDataUrl,
    "../easyuse_anima_i18n.js": i18nModuleUrl,
  })
);

assert.deepEqual(Object.keys(definitionsModule), ["createEasyUseAnimaSettings"]);

const textCalls = [];
const labelCalls = [];
const updateCalls = [];
const renderCalls = [];

function renderer(name) {
  return (...args) => {
    renderCalls.push({ name, args });
    return { name, args };
  };
}

const createLongTextEditorButton = renderer("long-text");
const createPromptStudioColorEditorButton = renderer("color");
const createWildcardExtraPathsEditor = renderer("wildcard");
const createNaiaResolutionModeEditor = renderer("resolution-mode");
const createNaiaResolutionScaleEditor = renderer("resolution-scale");

const dependencies = {
  text(key) {
    textCalls.push(key);
    return key === "autocompleteLimitTip" ? "" : "t:" + key;
  },
  localeLabel(item) {
    labelCalls.push(item);
    return "label:" + item.en;
  },
  updateInternalSetting(id, value, type) {
    updateCalls.push({ id, value, type });
  },
  createLongTextEditorButton,
  createPromptStudioColorEditorButton,
  createWildcardExtraPathsEditor,
  createNaiaResolutionModeEditor,
  createNaiaResolutionScaleEditor,
};
const settings = definitionsModule.createEasyUseAnimaSettings(dependencies);

assert.equal(updateCalls.length, 0, "Building descriptors must not update settings");
assert.equal(renderCalls.length, 0, "Building descriptors must not render DOM");

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
const expectedIds = [
  "EasyUseAnima.PromptStudio.EditLongText",
  "EasyUseAnima.Prompt.AutocompleteMode",
  "EasyUseAnima.Prompt.AutocompleteSource",
  "EasyUseAnima.Prompt.AutocompleteLimit",
  "EasyUseAnima.Prompt.AutocompleteCommitKey",
  "EasyUseAnima.Prompt.AutocompleteAppendSeparator",
  "EasyUseAnima.Prompt.AutocompleteNoCommaAfterPeriod",
  "EasyUseAnima.Prompt.AutocompleteDetectNaturalSentences",
  "EasyUseAnima.Prompt.AutocompletePreviewCompletion",
  "EasyUseAnima.Prompt.AutocompletePreviewClosingBrackets",
  "EasyUseAnima.Prompt.TranslationProvider",
  "EasyUseAnima.Prompt.TranslationSource",
  "EasyUseAnima.Prompt.TranslationTarget",
  "EasyUseAnima.Prompt.TypoIndicator",
  "EasyUseAnima.Prompt.WeightSyntaxUnderline",
  "EasyUseAnima.Prompt.CommentItalic",
  "EasyUseAnima.Prompt.TrainedTagTooltip",
  "EasyUseAnima.Prompt.FontOverride",
  "EasyUseAnima.Prompt.FontFamily",
  "EasyUseAnima.Prompt.FontSize",
  "EasyUseAnima.Prompt.NaiaGeneralAutoToggle",
  "EasyUseAnima.Prompt.HighlightColors",
  "EasyUseAnima.Wildcard.ExtraPaths",
  "EasyUseAnima.LoraPreset.NameDisplay",
  "EasyUseAnima.LoraPreset.MenuMode",
  "EasyUseAnima.LoraPreset.StrengthButtonStep",
  "EasyUseAnima.LoraPreset.StrengthDragStep",
  "EasyUseAnima.LoraPreset.StrengthDragPixels",
  "EasyUseAnima.NAIA.Host",
  "EasyUseAnima.NAIA.Port",
  "EasyUseAnima.NAIA.AllowRemoteAPI",
  "EasyUseAnima.NAIA.UseDesktopPromptEngineering",
  "EasyUseAnima.NAIA.ResolutionMode",
  "EasyUseAnima.NAIA.ResolutionBucket",
  "EasyUseAnima.NAIA.ResolutionScale",
  "EasyUseAnima.NAIA.ResolutionMaxLongEdge",
  "EasyUseAnima.NAIA.EditLongText",
  ...preprocessingKeys.map((key) => "EasyUseAnima.NAIA." + key),
];

assert.deepEqual(settings.map((item) => item.id), expectedIds);
assert.equal(settings.length, 52);
assert.equal(new Set(expectedIds).size, settings.length, "Setting IDs must be unique");
assert.ok(
  settings.every((item) => item.category[0] === "EASY USE ANIMA"),
  "Every descriptor must retain the root category",
);

const byId = new Map(settings.map((item) => [item.id, item]));
const autocompleteMode = byId.get("EasyUseAnima.Prompt.AutocompleteMode");
const autocompleteSource = byId.get("EasyUseAnima.Prompt.AutocompleteSource");
assert.equal(typeof autocompleteSource.defaultValue, "function");
assert.equal(
  autocompleteSource.defaultValue(),
  "dbr_danbooru_2025_09_01",
);
assert.deepEqual(autocompleteMode, {
  id: "EasyUseAnima.Prompt.AutocompleteMode",
  name: "t:autocompleteMode",
  category: ["EASY USE ANIMA", "Autocomplete", "t:autocompleteMode"],
  type: "combo",
  defaultValue: "compatible_global",
  tooltip: "t:autocompleteModeTip",
  options: ["off", "easyuse_nodes", "compatible_global"],
  onChange: autocompleteMode.onChange,
});
autocompleteMode.onChange("off");
assert.deepEqual(updateCalls, [
  {
    id: "EasyUseAnima.Prompt.AutocompleteMode",
    value: "off",
    type: "combo",
  },
]);

const autocompleteLimit = byId.get("EasyUseAnima.Prompt.AutocompleteLimit");
assert.equal(Object.hasOwn(autocompleteLimit, "tooltip"), false);
assert.deepEqual(autocompleteLimit.attrs, { min: 1, max: 100, step: 1 });

assert.deepEqual(
  byId.get("EasyUseAnima.NAIA.ResolutionBucket").options,
  ["512", "768", "896", "1024", "1280", "1536"],
);
assert.deepEqual(
  byId.get("EasyUseAnima.LoraPreset.StrengthDragStep").attrs,
  { min: 0.001, max: 0.2, step: 0.001 },
);
assert.equal(byId.get("EasyUseAnima.NAIA.Host").defaultValue, "127.0.0.1");
assert.equal(byId.get("EasyUseAnima.NAIA.Port").defaultValue, "7243");

function schema(type, defaultValue, options = null, attrs = null) {
  return { type, defaultValue, options, attrs };
}

function projectSchema(item) {
  return {
    type: item.type,
    defaultValue: item.defaultValue,
    options: item.options ?? null,
    attrs: item.attrs ?? null,
  };
}

const expectedRegularSchemas = new Map([
  [
    "EasyUseAnima.Prompt.AutocompleteMode",
    schema("combo", "compatible_global", ["off", "easyuse_nodes", "compatible_global"]),
  ],
  [
    "EasyUseAnima.Prompt.AutocompleteSource",
    schema("combo", autocompleteSource.defaultValue, [
      "dbr_danbooru_2025_09_01",
      "dbr_e621_2025_09_01",
      "dbr_danbooru_e621_merged_2025_09_01",
      "localsmile_kr_wiki",
    ]),
  ],
  [
    "EasyUseAnima.Prompt.AutocompleteLimit",
    schema("number", 20, null, { min: 1, max: 100, step: 1 }),
  ],
  [
    "EasyUseAnima.Prompt.AutocompleteCommitKey",
    schema("combo", "enter", ["enter", "tab"]),
  ],
  ["EasyUseAnima.Prompt.AutocompleteAppendSeparator", schema("boolean", false)],
  ["EasyUseAnima.Prompt.AutocompleteNoCommaAfterPeriod", schema("boolean", true)],
  ["EasyUseAnima.Prompt.AutocompleteDetectNaturalSentences", schema("boolean", true)],
  ["EasyUseAnima.Prompt.AutocompletePreviewCompletion", schema("boolean", false)],
  ["EasyUseAnima.Prompt.AutocompletePreviewClosingBrackets", schema("boolean", false)],
  [
    "EasyUseAnima.Prompt.TranslationProvider",
    schema("combo", "off", ["off", "google"]),
  ],
  ["EasyUseAnima.Prompt.TranslationSource", schema("text", "auto")],
  ["EasyUseAnima.Prompt.TranslationTarget", schema("text", "en")],
  ["EasyUseAnima.Prompt.TypoIndicator", schema("boolean", true)],
  ["EasyUseAnima.Prompt.WeightSyntaxUnderline", schema("boolean", false)],
  ["EasyUseAnima.Prompt.CommentItalic", schema("boolean", true)],
  ["EasyUseAnima.Prompt.TrainedTagTooltip", schema("boolean", true)],
  ["EasyUseAnima.Prompt.FontOverride", schema("boolean", false)],
  ["EasyUseAnima.Prompt.FontFamily", schema("text", "")],
  [
    "EasyUseAnima.Prompt.FontSize",
    schema("number", 12, null, { min: 8, max: 24, step: 1 }),
  ],
  ["EasyUseAnima.Prompt.NaiaGeneralAutoToggle", schema("boolean", false)],
  [
    "EasyUseAnima.LoraPreset.NameDisplay",
    schema("combo", "name", ["name", "path"]),
  ],
  [
    "EasyUseAnima.LoraPreset.MenuMode",
    schema("combo", "tree", ["tree", "list"]),
  ],
  [
    "EasyUseAnima.LoraPreset.StrengthButtonStep",
    schema("number", 0.05, null, { min: 0.001, max: 0.5, step: 0.001 }),
  ],
  [
    "EasyUseAnima.LoraPreset.StrengthDragStep",
    schema("number", 0.05, null, { min: 0.001, max: 0.2, step: 0.001 }),
  ],
  [
    "EasyUseAnima.LoraPreset.StrengthDragPixels",
    schema("number", 8, null, { min: 1, max: 100, step: 1 }),
  ],
  ["EasyUseAnima.NAIA.Host", schema("text", "127.0.0.1")],
  ["EasyUseAnima.NAIA.Port", schema("text", "7243")],
  ["EasyUseAnima.NAIA.AllowRemoteAPI", schema("boolean", false)],
  ["EasyUseAnima.NAIA.UseDesktopPromptEngineering", schema("boolean", true)],
  [
    "EasyUseAnima.NAIA.ResolutionBucket",
    schema("combo", "1024", ["512", "768", "896", "1024", "1280", "1536"]),
  ],
  [
    "EasyUseAnima.NAIA.ResolutionMaxLongEdge",
    schema("number", 0, null, { min: 0, max: 16384, step: 32 }),
  ],
]);

for (const [id, expected] of expectedRegularSchemas) {
  assert.deepEqual(projectSchema(byId.get(id)), expected, id);
}
for (const key of preprocessingKeys) {
  const id = "EasyUseAnima.NAIA." + key;
  assert.deepEqual(
    projectSchema(byId.get(id)),
    schema("combo", "skip", ["skip", "on", "off"]),
    id,
  );
}

const directRenderers = [
  ["EasyUseAnima.Prompt.HighlightColors", createPromptStudioColorEditorButton],
  ["EasyUseAnima.Wildcard.ExtraPaths", createWildcardExtraPathsEditor],
  ["EasyUseAnima.NAIA.ResolutionMode", createNaiaResolutionModeEditor],
  ["EasyUseAnima.NAIA.ResolutionScale", createNaiaResolutionScaleEditor],
];
for (const [id, expectedRenderer] of directRenderers) {
  const descriptor = byId.get(id);
  assert.equal(descriptor.type, expectedRenderer);
  assert.equal(descriptor.defaultValue, "");
  assert.equal(Object.hasOwn(descriptor, "onChange"), false);
}

const promptLongText = byId.get("EasyUseAnima.PromptStudio.EditLongText");
const naiaLongText = byId.get("EasyUseAnima.NAIA.EditLongText");
assert.notEqual(promptLongText.type, createLongTextEditorButton);
assert.notEqual(naiaLongText.type, createLongTextEditorButton);
assert.equal(promptLongText.defaultValue, "");
assert.equal(naiaLongText.defaultValue, "");
assert.deepEqual(promptLongText.type("name", "setter", "value"), {
  name: "long-text",
  args: ["promptStudio"],
});
assert.deepEqual(naiaLongText.type("name", "setter", "value"), {
  name: "long-text",
  args: ["naia"],
});
assert.deepEqual(renderCalls, [
  { name: "long-text", args: ["promptStudio"] },
  { name: "long-text", args: ["naia"] },
]);
assert.equal(
  expectedRegularSchemas.size + directRenderers.length + 2 + preprocessingKeys.length,
  settings.length,
  "Every descriptor must be covered by a literal or renderer contract",
);

assert.equal(labelCalls.length, preprocessingKeys.length);
assert.equal(
  byId.get("EasyUseAnima.NAIA.remove_author").name,
  "label:Remove author",
);
assert.equal(
  byId.get("EasyUseAnima.NAIA.tag_implication_compression").name,
  "label:Tag implication compression",
);
assert.ok(textCalls.includes("autocomplete"));
assert.ok(textCalls.includes("preprocessingOptions"));

for (const locale of ["ko", "ko-KR", "Korean", "한국어"]) {
  settingValues["Comfy.Locale"] = locale;
  assert.equal(
    i18nModule.easyuseAnimaInitialAutocompleteSource(),
    "localsmile_kr_wiki",
  );
}
for (const locale of ["", "en", "ja-JP", "unknown"]) {
  settingValues["Comfy.Locale"] = locale;
  assert.equal(
    i18nModule.easyuseAnimaInitialAutocompleteSource(),
    "dbr_danbooru_2025_09_01",
  );
}

settingValues["Comfy.Locale"] = "ko-KR";
const koreanSettings =
  definitionsModule.createEasyUseAnimaSettings(dependencies);
const koreanAutocompleteSource = koreanSettings.find(
  (item) => item.id === "EasyUseAnima.Prompt.AutocompleteSource",
);
assert.equal(koreanAutocompleteSource.defaultValue(), "localsmile_kr_wiki");

globalThis.window.__easyuseAnimaSettings = {
  "autocomplete.source": "dbr_danbooru_2025_09_01",
};
assert.equal(
  koreanAutocompleteSource.defaultValue(),
  "dbr_danbooru_2025_09_01",
  "backend-loaded explicit internal source must replace the provisional locale default",
);
settingValues["Comfy.Locale"] = "en";
assert.equal(
  koreanAutocompleteSource.defaultValue(),
  "dbr_danbooru_2025_09_01",
  "locale changes must not replace the backend-loaded source",
);

console.log("Settings definitions smoke passed.");
