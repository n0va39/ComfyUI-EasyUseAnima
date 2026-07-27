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

const presets = await import(dataModule("../web/js/aio/presets.js"));
const {
  aioBuiltinProfileSettings,
  aioFindUserProfileByName,
  aioProfileSettingsFingerprint,
  aioResolvedProfileValue,
} = presets;

const profiles = [
  { name: "Portrait", settings: { sampler: { steps: 32 } } },
  { name: "Landscape", settings: { sampler: { steps: 24 } } },
];
assert(
  aioFindUserProfileByName(profiles, "pOrTrAiT") === profiles[0],
  "User-profile lookup must remain case-insensitive",
);
assert(
  aioFindUserProfileByName(profiles, "missing") === null,
  "Unknown user profiles must resolve to null",
);
assert(
  aioFindUserProfileByName(null, "Portrait") === null,
  "Invalid profile collections must resolve to null",
);

const orderedSettings = {
  sampler: { steps: 24, scheduler: "simple" },
  nested: { enabled: true, values: [{ alpha: 1, beta: 2 }] },
};
const reorderedSettings = {
  nested: { values: [{ beta: 2, alpha: 1 }], enabled: true },
  sampler: { scheduler: "simple", steps: 24 },
};
assert(
  aioProfileSettingsFingerprint(orderedSettings)
    === aioProfileSettingsFingerprint(reorderedSettings),
  "Profile fingerprints must be stable across object key order",
);

const disabledCorrections = {
  enabled: false,
  dcw_mode: "off",
  smc_cfg: false,
  cfgpp: false,
  fsg: false,
  replace_existing_cfg: false,
};
const defaultSettings = {
  sampler: {
    steps: 28,
    cfg: 4,
    sampler_name: "euler",
    scheduler: "normal",
    spectrum: { enabled: false },
    dit_corrections: { ...disabledCorrections },
  },
  highres: {
    spectrum: { enabled: false },
    dit_corrections: { ...disabledCorrections },
  },
  upscale: {
    spectrum: { enabled: false },
    dit_corrections: { ...disabledCorrections },
  },
  detailer: {
    enabled: true,
    order: ["face"],
    sam3: {},
    face: {
      spectrum: { enabled: false },
      dit_corrections: { ...disabledCorrections },
    },
  },
  model_patches: {
    kj: {
      fp16_accumulation: false,
      sage_attention: "disabled",
      sage_allow_compile: false,
      torch_compile: { enabled: false },
    },
    dave: {
      enabled: false,
      stage_scope: {
        first_pass: true,
        highres: false,
        detailer: false,
        upscale: false,
      },
    },
    safe_pag: { enabled: false },
  },
};
const defaultSnapshot = JSON.stringify(defaultSettings);
const normalSettings = aioBuiltinProfileSettings("normal", defaultSettings);
assert(
  JSON.stringify(defaultSettings) === defaultSnapshot,
  "Building a built-in profile must not mutate default settings",
);
assert(
  JSON.stringify(normalSettings.model_patches.dave.stage_scope)
    === JSON.stringify(defaultSettings.model_patches.dave.stage_scope),
  "Built-in profiles must preserve the fresh first-pass-only DAVE scope",
);

const allStageProfile = JSON.parse(JSON.stringify(normalSettings));
allStageProfile.model_patches.dave.stage_scope = {
  first_pass: true,
  highres: true,
  detailer: true,
  upscale: true,
};
assert(
  aioProfileSettingsFingerprint(allStageProfile)
    !== aioProfileSettingsFingerprint(normalSettings),
  "User-profile identity must include the complete DAVE stage scope",
);

const normalSnapshot = JSON.stringify(normalSettings);
const builtinValue = aioResolvedProfileValue({
  settings: normalSettings,
  defaultSettings,
  selectedValue: "user:Portrait",
  selectedFingerprint: aioProfileSettingsFingerprint(normalSettings),
  profiles,
  customValue: "sentinel-custom",
});
assert(builtinValue === "builtin:normal", "Built-in profile identity must take priority");
assert(
  JSON.stringify(normalSettings) === normalSnapshot
    && JSON.stringify(defaultSettings) === defaultSnapshot,
  "Built-in profile resolution must not mutate its settings inputs",
);

const customSettings = {
  ...normalSettings,
  sampler: { ...normalSettings.sampler, steps: normalSettings.sampler.steps + 1 },
};
const customFingerprint = aioProfileSettingsFingerprint(customSettings);
assert(
  aioResolvedProfileValue({
    settings: customSettings,
    defaultSettings,
    selectedValue: "user:pOrTrAiT",
    selectedFingerprint: customFingerprint,
    profiles,
    customValue: "sentinel-custom",
  }) === "user:pOrTrAiT",
  "Existing user profiles with an exact fingerprint must preserve the selected value",
);
assert(
  aioResolvedProfileValue({
    settings: customSettings,
    defaultSettings,
    selectedValue: "user:Portrait",
    selectedFingerprint: "stale-fingerprint",
    profiles,
    customValue: "sentinel-custom",
  }) === "sentinel-custom",
  "Changed user-profile settings must resolve to Custom",
);
assert(
  aioResolvedProfileValue({
    settings: customSettings,
    defaultSettings,
    selectedValue: "user:Deleted",
    selectedFingerprint: customFingerprint,
    profiles,
    customValue: "sentinel-custom",
  }) === "sentinel-custom",
  "Missing user profiles must resolve to Custom",
);
assert(
  aioResolvedProfileValue({
    settings: customSettings,
    defaultSettings,
    selectedValue: "custom",
    selectedFingerprint: customFingerprint,
    profiles,
  }) === "custom",
  "Non-profile selections must use the default Custom value",
);

console.log("AiO profile core smoke passed.");
