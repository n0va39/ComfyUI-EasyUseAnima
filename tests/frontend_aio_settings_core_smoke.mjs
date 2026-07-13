import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertJsonEqual(actual, expected, message) {
  assert(JSON.stringify(actual) === JSON.stringify(expected), message);
}

const settingsModule = await import(dataModule("../web/js/aio/settings.js"));
const {
  AIO_DEFAULT_GENERATION_SETTINGS,
  AIO_DEFAULT_INPUT_SETTINGS,
  AIO_GENERATOR_MAX_SEED,
  AIO_GENERATOR_SEED_CONTROLS,
  AIO_GENERATOR_SPECIAL_SEED_DECREMENT,
  AIO_GENERATOR_SPECIAL_SEED_INCREMENT,
  AIO_GENERATOR_SPECIAL_SEED_RANDOM,
  aioAsBool,
  aioCloneJson,
  aioMergeDefaults,
  aioMigrateGeneratorPostprocessSettings,
  aioNormalizeGeneratorPreviewSettings,
  aioNormalizeSeedControl,
  aioNormalizeSeedValue,
  aioParseSettingsValue,
  aioSettingsToCompactJson,
} = settingsModule;

assert(
  AIO_DEFAULT_INPUT_SETTINGS.schema === "easy_use_anima_input"
    && AIO_DEFAULT_INPUT_SETTINGS.version === 1,
  "AiO input settings must keep their versioned schema",
);
assertJsonEqual(
  AIO_DEFAULT_INPUT_SETTINGS.resources,
  {
    loader_mode: "split",
    clip_loader: "single",
    unet_weight_dtype: "default",
    clip_device: "default",
  },
  "AiO input resource defaults must remain stable",
);
assert(
  AIO_DEFAULT_GENERATION_SETTINGS.schema === "easyuse_anima_aio_generation_settings"
    && AIO_DEFAULT_GENERATION_SETTINGS.version === 1
    && AIO_DEFAULT_GENERATION_SETTINGS.mode === "txt2img",
  "AiO generation settings must keep their versioned schema",
);
assert(
  AIO_DEFAULT_GENERATION_SETTINGS.sampler.seed === AIO_GENERATOR_SPECIAL_SEED_RANDOM
    && AIO_DEFAULT_GENERATION_SETTINGS.sampler.steps === 32
    && AIO_DEFAULT_GENERATION_SETTINGS.sampler.cfg === 5
    && AIO_DEFAULT_GENERATION_SETTINGS.preview.feed_count === 12,
  "AiO generation defaults must retain their serialized baseline",
);

const cloneSource = {
  nested: { value: 1 },
  rows: [{ name: "first" }],
};
const cloned = aioCloneJson(cloneSource);
assertJsonEqual(cloned, cloneSource, "JSON cloning must preserve serializable data");
cloned.nested.value = 2;
cloned.rows[0].name = "changed";
assert(
  cloneSource.nested.value === 1 && cloneSource.rows[0].name === "first",
  "JSON cloning must detach nested objects and arrays",
);

const mergeDefaults = {
  enabled: false,
  nested: {
    alpha: 1,
    beta: 2,
  },
  rows: ["default-a", "default-b"],
};
const mergeValue = {
  nested: {
    beta: 9,
    future_nested: "kept",
  },
  rows: ["replacement"],
  future_root: {
    value: 42,
  },
};
const mergeDefaultsSnapshot = JSON.stringify(mergeDefaults);
const mergeValueSnapshot = JSON.stringify(mergeValue);
const merged = aioMergeDefaults(mergeDefaults, mergeValue);
assertJsonEqual(
  merged,
  {
    enabled: false,
    nested: {
      alpha: 1,
      beta: 9,
      future_nested: "kept",
    },
    rows: ["replacement"],
    future_root: {
      value: 42,
    },
  },
  "Default merging must deep-merge objects, replace arrays, and preserve future keys",
);
assert(
  JSON.stringify(mergeDefaults) === mergeDefaultsSnapshot
    && JSON.stringify(mergeValue) === mergeValueSnapshot,
  "Default merging must not mutate either input while merging",
);
assertJsonEqual(
  aioMergeDefaults(mergeDefaults, null),
  mergeDefaults,
  "Invalid merge values must fall back to a cloned default object",
);
assertJsonEqual(
  aioMergeDefaults(mergeDefaults, ["invalid"]),
  mergeDefaults,
  "Root arrays must not replace a settings object",
);

const partialInput = aioParseSettingsValue(JSON.stringify({
  resources: {
    future_loader_mode: "external",
  },
  future_root: {
    enabled: true,
  },
}), AIO_DEFAULT_INPUT_SETTINGS);
assert(
  partialInput.resources.loader_mode === "split"
    && partialInput.resources.future_loader_mode === "external"
    && partialInput.future_root.enabled === true,
  "Input settings parsing must merge defaults and preserve unknown future keys",
);
const invalidGeneration = aioParseSettingsValue("{", AIO_DEFAULT_GENERATION_SETTINGS);
assertJsonEqual(
  invalidGeneration,
  AIO_DEFAULT_GENERATION_SETTINGS,
  "Invalid generation JSON must fall back to versioned defaults",
);
invalidGeneration.sampler.steps = 1;
assert(
  AIO_DEFAULT_GENERATION_SETTINGS.sampler.steps === 32,
  "Invalid JSON fallback must return a fresh settings clone",
);
assertJsonEqual(
  aioParseSettingsValue("[]", AIO_DEFAULT_GENERATION_SETTINGS),
  AIO_DEFAULT_GENERATION_SETTINGS,
  "A root JSON array must fall back to generation defaults",
);
const parsedLegacyGeneration = aioParseSettingsValue(JSON.stringify({
  upscale: {
    fit: {
      enabled: true,
      mode: "megapixels",
      max_megapixels: 9,
    },
  },
}), AIO_DEFAULT_GENERATION_SETTINGS);
assert(
  !Object.prototype.hasOwnProperty.call(parsedLegacyGeneration.upscale, "fit")
    && parsedLegacyGeneration.postprocess.enabled === true
    && parsedLegacyGeneration.postprocess.fit.mode === "megapixels"
    && parsedLegacyGeneration.postprocess.fit.max_megapixels === 9,
  "Parsing with the canonical generation defaults must run legacy fit migration",
);

const legacySettings = aioMergeDefaults(AIO_DEFAULT_GENERATION_SETTINGS, {
  upscale: {
    fit: {
      enabled: "true",
      mode: "megapixels",
      max_long_edge: 1536,
      max_megapixels: 8,
      method: "lanczos",
    },
  },
});
const migratedIdentity = aioMigrateGeneratorPostprocessSettings(legacySettings);
assert(
  migratedIdentity === legacySettings,
  "Legacy postprocess migration must retain its current in-place mutation contract",
);
assert(
  !Object.prototype.hasOwnProperty.call(legacySettings.upscale, "fit")
    && legacySettings.postprocess.enabled === true,
  "Legacy upscale.fit must be removed and enable the postprocess stage",
);
assertJsonEqual(
  legacySettings.postprocess.fit,
  {
    mode: "megapixels",
    max_long_edge: 1536,
    max_megapixels: 8,
    method: "lanczos",
  },
  "Legacy final-fit fields must migrate into postprocess.fit",
);
const migratedSnapshot = JSON.stringify(legacySettings);
aioMigrateGeneratorPostprocessSettings(legacySettings);
assert(
  JSON.stringify(legacySettings) === migratedSnapshot,
  "Legacy postprocess migration must be idempotent",
);

const precedenceSettings = aioMergeDefaults(AIO_DEFAULT_GENERATION_SETTINGS, {
  upscale: {
    fit: {
      enabled: true,
      mode: "max_long_edge",
      max_long_edge: 1024,
      max_megapixels: 2,
      method: "bicubic",
    },
  },
  postprocess: {
    enabled: false,
    fit: {
      mode: "megapixels",
      max_long_edge: 3072,
      max_megapixels: 12,
      method: "lanczos",
    },
  },
});
aioMigrateGeneratorPostprocessSettings(precedenceSettings);
assertJsonEqual(
  precedenceSettings.postprocess.fit,
  {
    mode: "megapixels",
    max_long_edge: 3072,
    max_megapixels: 12,
    method: "lanczos",
  },
  "Explicit non-default postprocess values must win over legacy upscale.fit values",
);
assert(
  precedenceSettings.postprocess.enabled === true,
  "The legacy enabled flag must keep enabling postprocess during migration",
);

for (const value of [true, "true", "1", "yes", "on", " TRUE "]) {
  assert(aioAsBool(value, false) === true, `Boolean value ${String(value)} must normalize true`);
}
for (const value of [false, "false", "0", "no", "off", " FALSE "]) {
  assert(aioAsBool(value, true) === false, `Boolean value ${String(value)} must normalize false`);
}
assert(aioAsBool(null, true) === true, "Null booleans must use their fallback");
assert(aioAsBool(undefined, false) === false, "Missing booleans must use their fallback");

assertJsonEqual(
  AIO_GENERATOR_SEED_CONTROLS,
  ["fixed", "randomize", "increment", "decrement"],
  "AiO seed control modes must remain stable",
);
assert(
  AIO_GENERATOR_SPECIAL_SEED_RANDOM === -1
    && AIO_GENERATOR_SPECIAL_SEED_INCREMENT === -2
    && AIO_GENERATOR_SPECIAL_SEED_DECREMENT === -3,
  "rgthree-compatible special seed values must remain stable",
);
assert(
  aioNormalizeSeedControl(" increment ") === "increment"
    && aioNormalizeSeedControl("invalid") === "fixed",
  "Seed controls must trim valid values and fall back to fixed",
);
assert(aioNormalizeSeedValue("12.9") === 12, "Seed values must truncate finite numbers");
assert(
  aioNormalizeSeedValue("invalid", 77) === 77,
  "Invalid seed values must use the supplied fallback",
);
assert(
  aioNormalizeSeedValue(-999) === AIO_GENERATOR_SPECIAL_SEED_DECREMENT,
  "Seeds below the rgthree decrement sentinel must clamp to -3",
);
assert(
  aioNormalizeSeedValue(AIO_GENERATOR_MAX_SEED + 100) === AIO_GENERATOR_MAX_SEED,
  "Seeds above ComfyUI's supported range must clamp to the maximum",
);

const previewSettings = {
  save: {
    image_saver: {
      show_preview: true,
      future_save_key: "kept",
    },
  },
  preview: {
    intermediate_images: "yes",
    compare_previous: "0",
    image_feed: "off",
    feed_count: 999,
    future_preview_key: "kept",
  },
};
const normalizedPreview = aioNormalizeGeneratorPreviewSettings(previewSettings);
assert(
  normalizedPreview === previewSettings.preview,
  "Preview normalization must return the preview object stored on the settings input",
);
assert(
  normalizedPreview.intermediate_images === true
    && normalizedPreview.compare_previous === false
    && normalizedPreview.image_feed === false
    && normalizedPreview.feed_count === 100,
  "Preview booleans and feed count must normalize to their UI contract",
);
assert(
  normalizedPreview.future_preview_key === "kept"
    && previewSettings.save.image_saver.future_save_key === "kept"
    && !Object.prototype.hasOwnProperty.call(previewSettings.save.image_saver, "show_preview"),
  "Preview normalization must preserve future keys and remove legacy show_preview",
);
const minimumPreviewSettings = { preview: { feed_count: 0 } };
aioNormalizeGeneratorPreviewSettings(minimumPreviewSettings);
assert(minimumPreviewSettings.preview.feed_count === 1, "Preview feed count must clamp to one");
const fallbackPreviewSettings = { preview: { feed_count: "invalid" } };
aioNormalizeGeneratorPreviewSettings(fallbackPreviewSettings);
assert(fallbackPreviewSettings.preview.feed_count === 12, "Invalid preview feed counts must use defaults");

const compactSource = {
  sampler: {
    steps: 24,
  },
  save: {
    filename_prefix: "legacy/prefix",
    image_saver: {
      show_preview: true,
    },
  },
  preview: {
    feed_count: 0,
  },
  future_section: {
    value: 42,
  },
};
const compactSourceSnapshot = JSON.stringify(compactSource);
const compactJson = aioSettingsToCompactJson(compactSource);
assert(!compactJson.includes("\n"), "Serialized generation settings must remain compact JSON");
const compactSettings = JSON.parse(compactJson);
assert(
  compactSettings.schema === "easyuse_anima_aio_generation_settings"
    && compactSettings.sampler.steps === 24
    && compactSettings.preview.feed_count === 1,
  "Compact generation settings must merge defaults and normalize preview values",
);
assert(
  !Object.prototype.hasOwnProperty.call(compactSettings.save, "filename_prefix")
    && !Object.prototype.hasOwnProperty.call(compactSettings.save.image_saver, "show_preview"),
  "Compact generation settings must remove obsolete save and preview storage keys",
);
assert(
  compactSettings.future_section.value === 42,
  "Compact generation settings must preserve future sections",
);
assert(
  JSON.stringify(compactSource) === compactSourceSnapshot,
  "Compact generation serialization must not mutate the caller's settings object",
);

console.log("AiO settings core smoke passed.");
