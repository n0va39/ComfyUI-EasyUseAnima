// @ts-check

const RECOMMENDATION_ENDPOINT = "/easyuse_anima/aio/torch-compile/recommend";
const RECOMMENDATION_FIELDS = Object.freeze([
  "enabled",
  "backend",
  "fullgraph",
  "mode",
  "dynamic",
  "compile_transformer_blocks_only",
  "dynamo_cache_size_limit",
  "debug_compile_keys",
  "disable_dynamic_vram",
]);
const MODES = new Set([
  "default",
  "reduce-overhead",
  "max-autotune",
  "max-autotune-no-cudagraphs",
]);
const DYNAMIC_VALUES = new Set(["auto", "true", "false"]);

function objectValue(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function explicitBoolean(value) {
  return typeof value === "boolean" ? value : null;
}

function boundedString(value, name, { maximum = 160, allowed = null } = {}) {
  if (typeof value !== "string" || !value || value.length > maximum) {
    throw new TypeError(`Malformed Torch Compile recommendation ${name}`);
  }
  if (allowed && !allowed.has(value)) {
    throw new TypeError(`Unsupported Torch Compile recommendation ${name}`);
  }
  return value;
}

function boundedStringList(value, name) {
  if (!Array.isArray(value) || value.length > 32) {
    throw new TypeError(`Malformed Torch Compile recommendation ${name}`);
  }
  return value.map((item) => boundedString(item, name));
}

function requiredBoolean(value, name) {
  if (typeof value !== "boolean") {
    throw new TypeError(`Malformed Torch Compile recommendation ${name}`);
  }
  return value;
}

function requiredInteger(value, name) {
  if (!Number.isInteger(value) || value < 1 || value > 4096) {
    throw new TypeError(`Malformed Torch Compile recommendation ${name}`);
  }
  return value;
}

function stageRequest(settings, name) {
  const section = objectValue(settings?.[name]);
  /** @type {{ enabled: boolean | null, backend?: string | null }} */
  const request = { enabled: explicitBoolean(section?.enabled) };
  if (name === "upscale") {
    request.backend = typeof section?.backend === "string" && section.backend
      ? section.backend.slice(0, 80)
      : null;
  }
  return request;
}

/**
 * Build the minimum workload request. Prompt fields, profiles, workflow data,
 * and model/user values are intentionally excluded.
 */
export function aioTorchCompileRecommendationRequest(settings, context = {}) {
  const resolution = objectValue(context?.resolution);
  const width = resolution?.width;
  const height = resolution?.height;
  const exactResolution = Number.isInteger(width)
    && width > 0
    && width <= 16384
    && Number.isInteger(height)
    && height > 0
    && height <= 16384
      ? { width, height }
      : {};
  const requestedBatch = context?.batchSize;
  const batchSize = Number.isInteger(requestedBatch)
    && requestedBatch > 0
    && requestedBatch <= 4096
      ? requestedBatch
      : 1;

  return {
    generation_settings: {
      highres: stageRequest(settings, "highres"),
      detailer: stageRequest(settings, "detailer"),
      upscale: stageRequest(settings, "upscale"),
    },
    resolution: exactResolution,
    batch_size: batchSize,
  };
}

/**
 * Validate and narrow the backend response before any dialog control changes.
 */
export function aioNormalizeTorchCompileRecommendation(payload) {
  const source = objectValue(payload);
  if (!source || typeof source.supported !== "boolean") {
    throw new TypeError("Malformed Torch Compile recommendation response");
  }
  const profile = boundedString(source.profile, "profile", { maximum: 80 });
  const policyVersion = boundedString(source.policy_version, "policy version", { maximum: 80 });
  const reasonCodes = boundedStringList(source.reason_codes, "reason codes");
  const warnings = boundedStringList(source.warnings, "warnings");
  const environment = objectValue(source.environment) || {};
  const accelerator = typeof environment.accelerator === "string"
    ? environment.accelerator.slice(0, 40)
    : "unknown";
  const totalVramMb = Number.isInteger(environment.total_vram_mb)
    && environment.total_vram_mb > 0
      ? environment.total_vram_mb
      : null;

  if (!source.supported) {
    return {
      supported: false,
      profile,
      policyVersion,
      values: null,
      reasonCodes,
      warnings,
      environment: { accelerator, totalVramMb },
    };
  }

  const values = objectValue(source.values);
  if (!values) {
    throw new TypeError("Malformed Torch Compile recommendation values");
  }
  const normalizedValues = {
    enabled: requiredBoolean(values.enabled, "enabled"),
    backend: boundedString(values.backend, "backend", {
      maximum: 80,
      allowed: new Set(["inductor"]),
    }),
    fullgraph: requiredBoolean(values.fullgraph, "fullgraph"),
    mode: boundedString(values.mode, "mode", { maximum: 80, allowed: MODES }),
    dynamic: boundedString(values.dynamic, "dynamic", {
      maximum: 16,
      allowed: DYNAMIC_VALUES,
    }),
    compile_transformer_blocks_only: requiredBoolean(
      values.compile_transformer_blocks_only,
      "compile_transformer_blocks_only",
    ),
    dynamo_cache_size_limit: requiredInteger(
      values.dynamo_cache_size_limit,
      "dynamo_cache_size_limit",
    ),
    debug_compile_keys: requiredBoolean(values.debug_compile_keys, "debug_compile_keys"),
    disable_dynamic_vram: requiredBoolean(
      values.disable_dynamic_vram,
      "disable_dynamic_vram",
    ),
  };

  return {
    supported: true,
    profile,
    policyVersion,
    values: normalizedValues,
    reasonCodes,
    warnings,
    environment: { accelerator, totalVramMb },
  };
}

export function aioTorchCompileRecommendationDiff(current, recommendationValues) {
  const currentValues = objectValue(current) || {};
  const nextValues = objectValue(recommendationValues) || {};
  return RECOMMENDATION_FIELDS
    .filter((name) => Object.hasOwn(nextValues, name) && currentValues[name] !== nextValues[name])
    .map((name) => ({
      name,
      current: currentValues[name],
      recommended: nextValues[name],
    }));
}

export function createAioTorchCompileRecommendationClient(dependencies) {
  const { fetchJson } = dependencies;
  return {
    recommend(settings, context = {}) {
      return fetchJson(RECOMMENDATION_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(aioTorchCompileRecommendationRequest(settings, context)),
      }).then(aioNormalizeTorchCompileRecommendation);
    },
  };
}
