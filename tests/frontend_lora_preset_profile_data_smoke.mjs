import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const profileData = await import(dataModule("../web/js/lora_preset/profile_data.js"));

assert.deepEqual(Object.keys(profileData).sort(), [
  "INTERNAL_WIDGET_DEFAULTS",
  "MAX_PROFILES",
  "WIDGET_INDEX",
  "emptyProfile",
  "isMeaningfulProfile",
  "normalizeLoraEntry",
  "normalizeProfileDataValue",
  "normalizeSerializedWidgets",
  "profileContent",
  "profileKey",
  "profileSavedName",
  "profileSnapshot",
  "withSavedMeta",
  "wrapProfileIndex",
].sort());

const {
  INTERNAL_WIDGET_DEFAULTS,
  MAX_PROFILES,
  WIDGET_INDEX,
  emptyProfile,
  isMeaningfulProfile,
  normalizeLoraEntry,
  normalizeProfileDataValue,
  normalizeSerializedWidgets,
  profileContent,
  profileKey,
  profileSavedName,
  profileSnapshot,
  withSavedMeta,
  wrapProfileIndex,
} = profileData;

assert.equal(MAX_PROFILES, 16);
assert.deepEqual(WIDGET_INDEX, {
  stylePrompt: 0,
  profileIndex: 1,
  profileCount: 2,
  loraName: 3,
  loras: 4,
  profileData: 5,
});
assert.deepEqual(INTERNAL_WIDGET_DEFAULTS, {
  profile_count: "4",
  lora_name: "None",
  loras: "[]",
  profile_data: "{}",
});

const preservedProfileJson = ' {"1":{"style_prompt":"keep"}} ';
const serializedValues = [
  "style",
  2,
  "",
  "legacy-name",
  [{ name: "style/example.safetensors", strength: 0.75 }],
  preservedProfileJson,
];
const serializedInfo = { widgets_values: serializedValues };
assert.equal(normalizeSerializedWidgets(serializedInfo), undefined);
assert.strictEqual(serializedInfo.widgets_values, serializedValues);
assert.equal(serializedValues[WIDGET_INDEX.stylePrompt], "style");
assert.equal(serializedValues[WIDGET_INDEX.profileIndex], 2);
assert.equal(serializedValues[WIDGET_INDEX.profileCount], "4");
assert.equal(serializedValues[WIDGET_INDEX.loraName], "None");
assert.equal(
  serializedValues[WIDGET_INDEX.loras],
  '[{"name":"style/example.safetensors","strength":0.75}]',
);
assert.equal(serializedValues[WIDGET_INDEX.profileData], preservedProfileJson);

const malformedLoraString = "[not-valid-json";
const fallbackValues = ["", 1, null, "anything", malformedLoraString, "[]"];
normalizeSerializedWidgets({ widgets_values: fallbackValues });
assert.equal(fallbackValues[WIDGET_INDEX.profileCount], "4");
assert.equal(fallbackValues[WIDGET_INDEX.loraName], "None");
assert.equal(fallbackValues[WIDGET_INDEX.loras], malformedLoraString);
assert.equal(fallbackValues[WIDGET_INDEX.profileData], "{}");

const malformedProfileValues = ["", 1, "4", "anything", "[]", "{bad-json"];
assert.doesNotThrow(() => normalizeSerializedWidgets({ widgets_values: malformedProfileValues }));
assert.equal(malformedProfileValues[WIDGET_INDEX.profileData], "{}");

const nonStringValues = ["", 1, "2", "anything", { invalid: true }, { "1": {} }];
normalizeSerializedWidgets({ widgets_values: nonStringValues });
assert.equal(nonStringValues[WIDGET_INDEX.profileCount], "2");
assert.equal(nonStringValues[WIDGET_INDEX.loras], "[]");
assert.equal(nonStringValues[WIDGET_INDEX.profileData], "{}");
const nonArrayInfo = { widgets_values: { untouched: true } };
assert.equal(normalizeSerializedWidgets(nonArrayInfo), undefined);
assert.deepEqual(nonArrayInfo.widgets_values, { untouched: true });

assert.equal(profileKey(-3), "1");
assert.equal(profileKey("12suffix"), "12");
assert.equal(profileKey(99), "16");
assert.equal(profileKey("invalid"), "1");
assert.equal(wrapProfileIndex(1, 4), 1);
assert.equal(wrapProfileIndex(5, 4), 1);
assert.equal(wrapProfileIndex(16, 20), 16);
assert.equal(wrapProfileIndex(17, 20), 1);
assert.equal(wrapProfileIndex(-1, 0), 1);

const profileObject = { "1": { style_prompt: "same object" } };
assert.strictEqual(normalizeProfileDataValue(profileObject), profileObject);
assert.deepEqual(normalizeProfileDataValue('{"1":{"style_prompt":"json"}}'), {
  "1": { style_prompt: "json" },
});
assert.deepEqual(normalizeProfileDataValue("invalid"), {});
assert.deepEqual(normalizeProfileDataValue("[]"), {});
assert.deepEqual(normalizeProfileDataValue([]), {});
assert.deepEqual(normalizeProfileDataValue(null), {});

assert.deepEqual(normalizeLoraEntry({
  lora: " style/example.safetensors ",
  active: false,
  strength: "0.75",
  clipStrength: "0.5",
  unknown: "drop",
}), {
  name: "style/example.safetensors",
  on: false,
  strength: 0.75,
  strengthTwo: 0.5,
});
assert.deepEqual(normalizeLoraEntry({
  name: "bad.safetensors",
  on: true,
  strength: "bad",
  strengthTwo: "bad",
}), {
  name: "bad.safetensors",
  on: true,
  strength: 1,
  strengthTwo: null,
});
assert.deepEqual(normalizeLoraEntry({
  name: "canonical.safetensors",
  lora: "legacy.safetensors",
  on: false,
  active: true,
  strength: 1,
  strengthTwo: "",
  clipStrength: "0.9",
}), {
  name: "canonical.safetensors",
  on: false,
  strength: 1,
  strengthTwo: null,
});
assert.equal(normalizeLoraEntry({ name: "zero.safetensors", strength: "" }).strength, 0);

const rawProfile = {
  style_prompt: 123,
  loras: [
    { name: "", strength: 1 },
    { lora: " kept.safetensors ", active: false, strength: "1.25" },
  ],
  saved_name: "must be stripped",
  saved_snapshot: "must be stripped",
  unknown: true,
};
const normalizedContent = profileContent(rawProfile);
assert.deepEqual(normalizedContent, {
  style_prompt: "123",
  loras: [{
    name: "kept.safetensors",
    on: false,
    strength: 1.25,
    strengthTwo: null,
  }],
});
assert.equal(
  profileSnapshot(rawProfile),
  '{"style_prompt":"123","loras":[{"name":"kept.safetensors","on":false,"strength":1.25,"strengthTwo":null}]}',
);
assert.equal(isMeaningfulProfile({ style_prompt: "   ", loras: [] }), false);
assert.equal(isMeaningfulProfile({ style_prompt: "", loras: [{ name: "" }] }), false);
assert.equal(isMeaningfulProfile({ style_prompt: " tag ", loras: [] }), true);
assert.equal(isMeaningfulProfile({ style_prompt: "", loras: [{ name: "kept.safetensors" }] }), true);
assert.equal(profileSavedName({ saved_name: " Saved Set " }), "Saved Set");

const contentInput = { style_prompt: "prompt", loras: [] };
const previousInput = { saved_name: " Saved Set ", saved_snapshot: "snapshot" };
assert.deepEqual(withSavedMeta(contentInput, previousInput), {
  style_prompt: "prompt",
  loras: [],
  saved_name: "Saved Set",
  saved_snapshot: "snapshot",
});
assert.deepEqual(contentInput, { style_prompt: "prompt", loras: [] });
assert.deepEqual(previousInput, { saved_name: " Saved Set ", saved_snapshot: "snapshot" });
assert.deepEqual(withSavedMeta(contentInput, { saved_name: "Saved Set" }), {
  style_prompt: "prompt",
  loras: [],
});
assert.deepEqual(withSavedMeta(contentInput, { saved_snapshot: "snapshot" }), {
  style_prompt: "prompt",
  loras: [],
});

const firstEmpty = emptyProfile(1);
const secondEmpty = emptyProfile(16);
assert.deepEqual(firstEmpty, { style_prompt: "", loras: [] });
assert.deepEqual(secondEmpty, { style_prompt: "", loras: [] });
assert.notStrictEqual(firstEmpty, secondEmpty);
assert.notStrictEqual(firstEmpty.loras, secondEmpty.loras);
