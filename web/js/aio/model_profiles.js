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
  EasyUseAnimaAIOGenerator: { family: "anima", label: "Anima", capabilities: ANIMA_CAPABILITIES },
  EasyUseMossAIOGenerator: { family: "moss_image", label: "MOSS", capabilities: { ...NATIVE_DIT_CAPABILITIES, negpip: true, torchCompile: false } },
  EasyUseKrea2AIOGenerator: { family: "krea2", label: "Krea2", capabilities: NATIVE_DIT_CAPABILITIES },
};

export function aioGeneratorModelProfile(node) {
  return AIO_GENERATOR_MODEL_PROFILES[node?.comfyClass]
    || AIO_GENERATOR_MODEL_PROFILES[node?.type];
}

export function aioModelProfile(family = "anima") {
  return Object.values(AIO_GENERATOR_MODEL_PROFILES).find((profile) => profile.family === family)
    // Saved foreign/future identities remain inspectable; no capability is assumed.
    || { family, label: String(family), capabilities: {} };
}
