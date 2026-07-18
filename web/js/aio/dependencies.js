// @ts-check

export const AIO_OPTIONAL_DEPENDENCY_SPECS = {
  spectrumAdvanced: {
    nodeId: "SpectrumKSamplerAdvanced",
    pack: "ComfyUI-Spectrum-KSampler",
  },
  spectrumSpd: {
    nodeId: "SpectrumSPDKSampler",
    pack: "ComfyUI-Spectrum-KSampler",
  },
  spectrumPatch: {
    nodeId: "DiTSpectrumPatchAdvanced",
    pack: "ComfyUI-Spectrum-KSampler",
  },
  spectrumCorrections: {
    nodeId: "DiTCFGFSGPatch",
    pack: "ComfyUI-Spectrum-KSampler",
  },
  dave: {
    nodeId: "AnimaDAVE",
    pack: "ComfyUI-Anima-DAVE",
  },
  safePag: {
    nodeId: "AnimaSafePAG",
    pack: "Anima Safe PAG",
  },
  imageSaver: {
    nodeId: "Image Saver",
    pack: "ComfyUI-Image-Saver",
  },
  upscaleModelLoader: {
    nodeId: "UpscaleModelLoader",
    pack: "ComfyUI built-in upscale model loader",
  },
  checkpointLoader: {
    nodeId: "CheckpointLoaderSimple",
    pack: "ComfyUI built-in checkpoint loader",
  },
  ultimateSdUpscale: {
    nodeId: "UltimateSDUpscale",
    pack: "ComfyUI_UltimateSDUpscale",
  },
  resShiftLoader: {
    nodeId: "ResShiftLoader",
    pack: "ComfyUI-Distilled-ResShift",
  },
  resShiftUpscale: {
    nodeId: "ResShiftUpscale",
    pack: "ComfyUI-Distilled-ResShift",
  },
  kjFp16: {
    nodeId: "ModelPatchTorchSettings",
    pack: "ComfyUI-KJNodes",
  },
  kjSage: {
    nodeId: "PathchSageAttentionKJ",
    pack: "ComfyUI-KJNodes",
  },
  kjTorchCompile: {
    nodeId: "TorchCompileModelAdvanced",
    pack: "ComfyUI-KJNodes",
  },
  impactDetailer: {
    nodeId: "DetailerForEach",
    pack: "ComfyUI-Impact-Pack",
  },
  impactMaskToSegs: {
    nodeId: "MaskToSEGS",
    pack: "ComfyUI-Impact-Pack",
  },
};

export const AIO_BACKEND_DEPENDENCIES = {
  spectrum_mod_guidance_advanced: "spectrumAdvanced",
  spectrum_spd_speed: "spectrumSpd",
};

export async function aioQueryOptionalDependencies(specs, queryNodeInfo) {
  const available = {};
  const status = {};
  const nodeInfo = {};
  const errors = {};

  for (const [key, spec] of Object.entries(specs || {})) {
    try {
      const info = await queryNodeInfo(spec, key);
      available[key] = !!info;
      status[key] = info ? "available" : "missing";
      nodeInfo[key] = info || null;
    } catch (error) {
      status[key] = "error";
      nodeInfo[key] = null;
      errors[key] = error instanceof Error ? error.message : String(error || "Unknown error");
    }
  }

  return { available, status, nodeInfo, errors };
}

export function aioOptionalDependencyStatus(state, key) {
  if (!key || !state?.loaded) {
    return "unknown";
  }
  return state.status?.[key] || "unknown";
}

export function aioOptionalDependencyAvailable(state, key) {
  return aioOptionalDependencyStatus(state, key) !== "missing";
}

export function aioOptionalDependencyPack(key, specs = AIO_OPTIONAL_DEPENDENCY_SPECS) {
  return specs?.[key]?.pack || key || "";
}

export function aioUpscaleBackendDependencyKeys(backend) {
  if (backend === "usdu") {
    return ["ultimateSdUpscale", "upscaleModelLoader"];
  }
  if (backend === "resshift") {
    return ["resShiftLoader", "resShiftUpscale"];
  }
  return [];
}

export function aioUpscaleBackendMissingPacks(
  state,
  backend,
  specs = AIO_OPTIONAL_DEPENDENCY_SPECS,
) {
  return aioUpscaleBackendDependencyKeys(backend)
    .filter((key) => !aioOptionalDependencyAvailable(state, key))
    .map((key) => aioOptionalDependencyPack(key, specs));
}

export function aioNodeInputMap(state, dependencyKey) {
  const input = state?.nodeInfo?.[dependencyKey]?.input || {};
  return {
    ...(input.required || {}),
    ...(input.optional || {}),
  };
}

export function aioNodeInputSpec(state, dependencyKey, inputName) {
  return aioNodeInputMap(state, dependencyKey)?.[inputName] || null;
}

export function aioNodeInputTooltip(state, dependencyKey, inputName) {
  const spec = aioNodeInputSpec(state, dependencyKey, inputName);
  const options = Array.isArray(spec) && spec[1] && typeof spec[1] === "object"
    ? spec[1]
    : null;
  return options?.tooltip ? String(options.tooltip) : "";
}

export function aioNodeInputSupported(state, dependencyKey, inputName) {
  const status = aioOptionalDependencyStatus(state, dependencyKey);
  if (status === "unknown" || status === "error") {
    return true;
  }
  if (status === "missing") {
    return false;
  }
  return !!aioNodeInputSpec(state, dependencyKey, inputName);
}
