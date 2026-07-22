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

function collectLeafPaths(value, path = [], output = []) {
  if (value && typeof value === "object" && !Array.isArray(value) && Object.keys(value).length > 0) {
    for (const [name, child] of Object.entries(value)) {
      collectLeafPaths(child, [...path, name], output);
    }
    return output;
  }
  output.push(`/${path.join("/")}`);
  return output;
}

function collectContractPaths(contract, path, output = []) {
  if (Object.prototype.hasOwnProperty.call(contract, "$ref")) {
    output.push(`/${path.join("/")}`);
    return output;
  }
  const fields = contract?.fields;
  if (fields && typeof fields === "object" && !Array.isArray(fields) && Object.keys(fields).length > 0) {
    for (const [name, child] of Object.entries(fields)) {
      collectContractPaths(child, [...path, name], output);
    }
    return output;
  }
  output.push(`/${path.join("/")}`);
  return output;
}

function manifestContractPaths(manifest) {
  const paths = collectContractPaths(manifest.shape, ["shape"]);
  for (const [name, definition] of Object.entries(manifest.definitions)) {
    collectContractPaths(definition, ["definitions", name], paths);
  }
  return paths.sort();
}

function assertSurfacePaths(expectedPaths, actualPaths, surface) {
  const expected = new Set(expectedPaths);
  const actual = new Set(actualPaths);
  const failures = [
    ...[...expected].filter((path) => !actual.has(path)).sort()
      .map((path) => `${path}: missing surface ${surface}`),
    ...[...actual].filter((path) => !expected.has(path)).sort()
      .map((path) => `${path}: stale surface ${surface}`),
  ];
  assert(failures.length === 0, failures.join("\n"));
}

function coverageEntries(coverage) {
  const entries = {};
  assert(Array.isArray(coverage.groups) && coverage.groups.length > 0, "Surface coverage groups are missing");
  for (const [index, group] of coverage.groups.entries()) {
    assert(
      group && typeof group.coverage === "object" && Array.isArray(group.paths) && group.paths.length > 0,
      `Surface coverage group ${index} is invalid`,
    );
    for (const path of group.paths) {
      assert(!Object.prototype.hasOwnProperty.call(entries, path), `${path}: duplicate surface coverage entry`);
      entries[path] = group.coverage;
    }
  }
  return entries;
}

function collectCoercionReferences(value, output = new Set()) {
  if (Array.isArray(value)) {
    for (const child of value) {
      collectCoercionReferences(child, output);
    }
    return output;
  }
  if (!value || typeof value !== "object") {
    return output;
  }
  for (const [name, child] of Object.entries(value)) {
    if ((name === "coercion" || name === "item_coercion") && typeof child === "string") {
      output.add(child);
    }
    collectCoercionReferences(child, output);
  }
  return output;
}

const settingsModule = await import(dataModule("../web/js/aio/settings.js"));
const generationManifest = JSON.parse(readFileSync(
  new URL("../easyuse_anima/aio/schemas/generation_settings.v1.json", import.meta.url),
  "utf8",
));
const generationSurfaceCoverage = JSON.parse(readFileSync(
  new URL("./fixtures/aio_generation_settings_surface_coverage.v1.json", import.meta.url),
  "utf8",
));
const aioRuntimeSource = readFileSync(
  new URL("../web/js/easyuse_anima_aio.js", import.meta.url),
  "utf8",
);
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
  generationManifest.settings.schema === AIO_DEFAULT_GENERATION_SETTINGS.schema
    && generationManifest.settings.version === AIO_DEFAULT_GENERATION_SETTINGS.version,
  "AiO manifest identity must match the frontend v1 settings identity",
);
assertJsonEqual(
  AIO_DEFAULT_GENERATION_SETTINGS,
  generationManifest.default,
  "AiO manifest defaults must deep-equal the frontend generation defaults",
);
assertSurfacePaths(
  collectLeafPaths(generationManifest.default, ["shape"]),
  collectLeafPaths(AIO_DEFAULT_GENERATION_SETTINGS, ["shape"]),
  "frontend_default",
);
const requiredSettingSurfaces = [
  "python_default",
  "python_typed",
  "frontend_default",
  "frontend_sanitization",
  "ui",
  "documentation",
];
assertJsonEqual(
  generationSurfaceCoverage.required_surfaces,
  requiredSettingSurfaces,
  "AiO surface coverage must retain every required maintenance surface",
);
const surfaceCoverageEntries = coverageEntries(generationSurfaceCoverage);
assertSurfacePaths(
  manifestContractPaths(generationManifest),
  Object.keys(surfaceCoverageEntries),
  "ui_metadata",
);
for (const [path, record] of Object.entries(surfaceCoverageEntries)) {
  for (const surface of requiredSettingSurfaces) {
    assert(
      typeof record[surface] === "string" && record[surface].length > 0,
      `${path}: missing surface ${surface}`,
    );
    assert(
      Object.prototype.hasOwnProperty.call(generationSurfaceCoverage.owners[surface], record[surface]),
      `${path}: unknown owner ${String(record[surface])} for surface ${surface}`,
    );
  }
}
const sanitizedGenerationDefaults = JSON.parse(
  aioSettingsToCompactJson(AIO_DEFAULT_GENERATION_SETTINGS),
);
assertSurfacePaths(
  collectLeafPaths(generationManifest.default, ["shape"]),
  collectLeafPaths(sanitizedGenerationDefaults, ["shape"]),
  "frontend_sanitization",
);
const coercionReferences = collectCoercionReferences({
  shape: generationManifest.shape,
  definitions: generationManifest.definitions,
  coercions: generationManifest.coercions,
});
const undefinedCoercions = [...coercionReferences]
  .filter((name) => !Object.prototype.hasOwnProperty.call(generationManifest.coercions, name));
assertJsonEqual(
  undefinedCoercions,
  [],
  "Every manifest coercion reference must have a self-contained definition",
);
const imageSaverContract = generationManifest.shape.fields.save.fields.image_saver.fields;
assert(
  imageSaverContract.additional_hash_bundles.items?.type === "string"
    && imageSaverContract.civitai_hash_fetchers.items?.$ref === "#/definitions/civitai_hash_fetcher"
    && generationManifest.shape.fields.detailer.fields.order.items?.$ref === "#/definitions/detailer_target_name",
  "Empty-default arrays must retain explicit item contracts",
);
assertJsonEqual(
  Object.keys(generationManifest.definitions.civitai_hash_fetcher.fields),
  ["enabled", "username", "model_name", "version"],
  "The Civitai fetcher item contract must retain its normalized backend fields",
);
assertJsonEqual(
  generationManifest.coercions.choice.invalid.dynamic_enum,
  {
    policy: "default-if-present-else-first",
    preferred_default_present: "default",
    preferred_default_absent: "first-capability",
    empty_capabilities: "default",
  },
  "Dynamic capability choices must not use the static-enum fallback claim",
);
assert(
  generationManifest.coercions.backend_boolean.list_or_tuple === "first-value"
    && generationManifest.coercions.backend_boolean.empty_list_or_tuple === "default",
  "Backend boolean coercion must record first-value and empty-container fallback behavior",
);
assert(
  generationManifest.shape.fields.mod_guidance.fields.profile.coercion === "mod-guidance-profile"
    && generationManifest.shape.fields.upscale.fields.usdu.fields.prompt_mode.coercion === "string-then-choice"
    && generationManifest.definitions.detailer_target.fields.alignment.coercion === "string-then-choice",
  "Field-specific backend choice pipelines must not claim the generic choice coercion",
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

const prototypePollutionKey = "__easyuseAnimaMergePollution";
delete Object.prototype[prototypePollutionKey];
try {
  const specialKeyMerge = aioMergeDefaults({}, JSON.parse(`{
    "__proto__": {"${prototypePollutionKey}": true},
    "constructor": {"mode": "saved"},
    "toString": "saved"
  }`));
  assert(
    Object.getPrototypeOf(specialKeyMerge) === Object.prototype
      && !Object.prototype.hasOwnProperty.call(Object.prototype, prototypePollutionKey),
    "Default merging must not mutate Object.prototype",
  );
  assertJsonEqual(
    specialKeyMerge,
    JSON.parse(`{
      "__proto__": {"${prototypePollutionKey}": true},
      "constructor": {"mode": "saved"},
      "toString": "saved"
    }`),
    "Default merging must preserve special names as own data properties",
  );
} finally {
  delete Object.prototype[prototypePollutionKey];
}

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

assertJsonEqual(
  generationManifest.coercions.frontend_boolean.true_strings,
  ["true", "1", "yes", "on"],
  "Manifest frontend true-string coercion tokens must remain stable",
);
assertJsonEqual(
  generationManifest.coercions.frontend_boolean.false_strings,
  ["false", "0", "no", "off"],
  "Manifest frontend false-string coercion tokens must remain stable",
);
for (const value of [true, ...generationManifest.coercions.frontend_boolean.true_strings, " TRUE "]) {
  assert(aioAsBool(value, false) === true, `Boolean value ${String(value)} must normalize true`);
}
for (const value of [false, ...generationManifest.coercions.frontend_boolean.false_strings, " FALSE "]) {
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
  generationManifest.shape.fields.sampler.fields.seed.minimum === AIO_GENERATOR_SPECIAL_SEED_DECREMENT
    && generationManifest.shape.fields.sampler.fields.seed.maximum_by_surface.frontend === AIO_GENERATOR_MAX_SEED,
  "Manifest frontend seed bounds must match the current settings core",
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

const unknownFieldPolicy = generationManifest.policies.unknown_fields;
assert(
  unknownFieldPolicy.frontend_default_merge.mode === "preserve-recursively"
    && unknownFieldPolicy.frontend_visible_merge.removed_paths.includes("/highres/backend")
    && !unknownFieldPolicy.backend.removed_known_legacy_paths.includes("/highres/backend"),
  "Manifest must record the current highres.backend surface drift without changing it",
);
const visibleMergeSource = aioRuntimeSource.slice(
  aioRuntimeSource.indexOf("function mergeVisibleGeneratorSettings"),
  aioRuntimeSource.indexOf("function applyVisibleGeneratorSettings"),
);
assert(
  visibleMergeSource.includes("delete next.highres?.backend;"),
  "Frontend visible merge must keep removing highres.backend while the manifest records the drift",
);
assert(
  generationManifest.policies.persistence.write_on_read === false
    && generationManifest.policies.version_migrations.length === 0,
  "The v1 contract must not introduce write-on-read or a version migration",
);

console.log("AiO settings core smoke passed.");
