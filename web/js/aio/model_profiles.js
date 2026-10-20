// @ts-check

export const AIO_GENERATOR_MODEL_PROFILES = {
  EasyUseAnimaAIOGenerator: { family: "anima", label: "Anima", basicOnly: false },
  EasyUseMossAIOGenerator: { family: "moss_image", label: "MOSS", basicOnly: true },
  EasyUseKrea2AIOGenerator: { family: "krea2", label: "Krea2", basicOnly: true },
};

export function aioGeneratorModelProfile(node) {
  return AIO_GENERATOR_MODEL_PROFILES[node?.comfyClass]
    || AIO_GENERATOR_MODEL_PROFILES[node?.type];
}
