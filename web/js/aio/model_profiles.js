// @ts-check

const COMMON_CAPABILITIES = {
  highres: true, detailer: true, upscale: true, kj: true, torchCompile: true, artistMix: true, hooks: true,
};
const ANIMA_CAPABILITIES = {
  ...COMMON_CAPABILITIES, modGuidance: true, negpip: true, dave: true,
  safePag: true, spectrum: true, ditCorrections: true,
};
const NATIVE_DIT_CAPABILITIES = {
  ...COMMON_CAPABILITIES, modGuidance: false, negpip: false, dave: false,
  safePag: false, spectrum: false, ditCorrections: false,
};

export const AIO_GENERATOR_MODEL_PROFILES = {
  EasyUseAnimaAIOGenerator: { family: "anima", label: "Anima", spectrumDependencyKey: "spectrumPatch", capabilities: ANIMA_CAPABILITIES },
  EasyUseMossAIOGenerator: { family: "moss_image", label: "MOSS", spectrumDependencyKey: "spectrumMossModelPatch", capabilities: { ...NATIVE_DIT_CAPABILITIES, negpip: true, torchCompile: false } },
  EasyUseKrea2AIOGenerator: { family: "krea2", label: "Krea2", spectrumDependencyKey: "spectrumKrea2ModelPatch", capabilities: NATIVE_DIT_CAPABILITIES },
};

export const AIO_MODEL_CAPABILITY_SPECS = Object.fromEntries(
  Object.entries(AIO_GENERATOR_MODEL_PROFILES).map(([nodeId, profile]) => [
    `modelProfile_${profile.family}`, { nodeId, pack: profile.label },
  ]),
);

const capabilityManifests = new Map();
const FEATURE_NAMES = {
  modGuidance: "mod_guidance",
  artistMix: "artist_mix",
  safePag: "safe_pag",
  ditCorrections: "dit_corrections",
  torchCompile: "torch_compile",
  hooks: "aio_hook",
};
const SAMPLING_STAGES = ["sampler", "highres", "detailer", "upscale"];

// Object-info metadata is runtime state, never part of saved settings. Invalid
// or older servers retain the conservative local profile.
export function aioUpdateModelCapabilities(nodeInfo) {
  for (const profile of Object.values(AIO_GENERATOR_MODEL_PROFILES)) {
    const info = nodeInfo?.[`modelProfile_${profile.family}`];
    const manifest = info?.input?.required?.generation_settings?.[1]?.aio_capabilities;
    if (
      manifest?.contract_version === 1
      && manifest.model_family === profile.family
      && manifest.features && typeof manifest.features === "object"
      && !Array.isArray(manifest.features)
    ) {
      capabilityManifests.set(profile.family, JSON.parse(JSON.stringify(manifest)));
    } else {
      capabilityManifests.delete(profile.family);
    }
  }
}

function featureCapability(profile, feature, stage = null) {
  const legacyName = Object.keys(FEATURE_NAMES).find((key) => FEATURE_NAMES[key] === feature) || feature;
  const key = FEATURE_NAMES[legacyName] || legacyName;
  const fallback = !!profile.capabilities[
    ["sage_attention", "fp16_accumulation"].includes(legacyName) ? "kj" : legacyName
  ] && (stage == null || SAMPLING_STAGES.includes(stage));
  const value = capabilityManifests.get(profile.family)?.features?.[key];
  if (
    value && typeof value.supported === "boolean"
    && ["available", "missing_dependency", "incompatible", "unsupported"].includes(value.status)
    && Array.isArray(value.stages)
  ) {
    const inStage = stage == null
      ? SAMPLING_STAGES.every((item) => value.stages.includes(item))
      : value.stages.includes(stage);
    const supported = value.supported && value.status === "available" && inStage;
    return {
      ...value,
      stages: [...value.stages],
      supported,
      status: value.supported && !inStage ? "unsupported" : value.status,
      reason_code: value.supported && !inStage ? "stage_not_supported" : value.reason_code,
    };
  }
  return {
    supported: fallback,
    status: fallback ? "available" : "unsupported",
    stages: [],
    reason_code: "capability_manifest_unavailable",
  };
}

function resolvedProfile(profile) {
  const capabilities = Object.fromEntries(
    Object.keys(profile.capabilities).map((key) => [
      key, key === "kj"
        ? featureCapability(profile, "sage_attention").supported
          && featureCapability(profile, "fp16_accumulation").supported
        : featureCapability(profile, key).supported,
    ]),
  );
  return {
    ...profile,
    capabilities,
    feature: (name, stage = "sampler") => featureCapability(profile, name, stage),
  };
}

export function aioGeneratorModelProfile(node) {
  const profile = AIO_GENERATOR_MODEL_PROFILES[node?.comfyClass]
    || AIO_GENERATOR_MODEL_PROFILES[node?.type];
  return profile ? resolvedProfile(profile) : undefined;
}

export function aioModelProfile(family = "anima") {
  return resolvedProfile(Object.values(AIO_GENERATOR_MODEL_PROFILES).find((profile) => profile.family === family)
    // Saved foreign/future identities remain inspectable; no capability is assumed.
    || { family, label: String(family), capabilities: {} });
}
