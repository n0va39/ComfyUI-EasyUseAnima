const BUILTIN_PROFILE_IDS = ["normal", "turbo", "optimized"];
const BUILTIN_FINGERPRINT_CACHE = new WeakMap();

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function detailerTargets(settings) {
  const detailer = settings?.detailer;
  if (!detailer || typeof detailer !== "object" || Array.isArray(detailer)) {
    return [];
  }
  return Object.entries(detailer)
    .filter(([name, value]) => (
      name !== "sam3"
      && name !== "order"
      && name !== "enabled"
      && value
      && typeof value === "object"
      && !Array.isArray(value)
    ))
    .map(([, value]) => value);
}

function samplingOptimizationTargets(settings) {
  return [
    settings?.sampler,
    settings?.highres,
    settings?.upscale,
    ...detailerTargets(settings),
  ].filter((value) => value && typeof value === "object" && !Array.isArray(value));
}

function setSamplingOptimizations(settings, enabled) {
  for (const target of samplingOptimizationTargets(settings)) {
    if (target.spectrum && typeof target.spectrum === "object") {
      target.spectrum.enabled = enabled;
    }
    if (target.dit_corrections && typeof target.dit_corrections === "object") {
      target.dit_corrections.enabled = enabled;
      target.dit_corrections.dcw_mode = enabled ? "auto" : "off";
      if (!enabled) {
        target.dit_corrections.smc_cfg = false;
        target.dit_corrections.cfgpp = false;
        target.dit_corrections.fsg = false;
        target.dit_corrections.replace_existing_cfg = false;
      }
    }
  }
}

function setKjOptimizations(settings, enabled) {
  const patches = settings.model_patches ||= {};
  const kj = patches.kj ||= {};
  kj.fp16_accumulation = enabled;
  kj.sage_attention = enabled ? "auto" : "disabled";
  kj.sage_allow_compile = enabled;
  const compile = kj.torch_compile ||= {};
  compile.enabled = enabled;
}

function normalProfile(defaultSettings) {
  const settings = cloneJson(defaultSettings);
  setSamplingOptimizations(settings, false);
  setKjOptimizations(settings, false);

  // DAVE and Safe PAG can intentionally change the generated result. They are
  // separate model-patch choices, not universal speed/quality optimizations.
  if (settings.model_patches?.dave) {
    settings.model_patches.dave.enabled = false;
  }
  if (settings.model_patches?.safe_pag) {
    settings.model_patches.safe_pag.enabled = false;
  }
  return settings;
}

export function aioBuiltinProfileIds() {
  return [...BUILTIN_PROFILE_IDS];
}

export function aioBuiltinProfileSettings(profileId, defaultSettings) {
  if (!BUILTIN_PROFILE_IDS.includes(profileId)) {
    throw new Error(`Unknown AiO built-in profile: ${profileId}`);
  }
  const settings = normalProfile(defaultSettings);
  if (profileId === "turbo") {
    settings.sampler.steps = 10;
    settings.sampler.cfg = 1.0;
    settings.sampler.sampler_name = "er_sde";
    settings.sampler.scheduler = "simple";
  } else if (profileId === "optimized") {
    setSamplingOptimizations(settings, true);
    setKjOptimizations(settings, true);
  }
  return settings;
}

function canonicalizeSettings(value) {
  if (Array.isArray(value)) {
    return value.map(canonicalizeSettings);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonicalizeSettings(value[key])]),
    );
  }
  return value;
}

export function aioProfileSettingsFingerprint(settings) {
  return JSON.stringify(canonicalizeSettings(settings));
}

export function aioBuiltinProfileIdForSettings(settings, defaultSettings) {
  if (!defaultSettings || typeof defaultSettings !== "object") {
    return "";
  }
  let fingerprints = BUILTIN_FINGERPRINT_CACHE.get(defaultSettings);
  if (!fingerprints) {
    fingerprints = Object.fromEntries(BUILTIN_PROFILE_IDS.map((profileId) => [
      profileId,
      aioProfileSettingsFingerprint(aioBuiltinProfileSettings(profileId, defaultSettings)),
    ]));
    BUILTIN_FINGERPRINT_CACHE.set(defaultSettings, fingerprints);
  }

  // Profile identity intentionally covers the complete settings snapshot. Any
  // changed value must read as Custom instead of implying a built-in profile.
  const fingerprint = aioProfileSettingsFingerprint(settings);
  return BUILTIN_PROFILE_IDS.find((profileId) => fingerprints[profileId] === fingerprint) || "";
}

export function aioUserProfileValue(name) {
  return `user:${String(name || "")}`;
}

export function aioUserProfileName(value) {
  const text = String(value || "");
  return text.startsWith("user:") ? text.slice(5) : "";
}

export function aioFindUserProfileByName(profiles, name) {
  const expected = String(name || "").toLowerCase();
  return (Array.isArray(profiles) ? profiles : []).find(
    (profile) => String(profile?.name || "").toLowerCase() === expected,
  ) || null;
}

export function aioResolvedProfileValue({
  settings,
  defaultSettings,
  selectedValue,
  selectedFingerprint,
  profiles,
  customValue = "custom",
}) {
  const builtinId = aioBuiltinProfileIdForSettings(settings, defaultSettings);
  if (builtinId) {
    return `builtin:${builtinId}`;
  }

  const textValue = String(selectedValue || "");
  const userName = aioUserProfileName(textValue);
  const fingerprint = aioProfileSettingsFingerprint(settings);
  if (
    userName
    && aioFindUserProfileByName(profiles, userName)
    && selectedFingerprint === fingerprint
  ) {
    return textValue;
  }
  return customValue;
}
