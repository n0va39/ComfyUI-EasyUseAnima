import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

const module = await import(dataModule("../web/js/aio/torch_compile_recommendation.js"));
assert.deepEqual(Object.keys(module), [
  "aioNormalizeTorchCompileRecommendation",
  "aioTorchCompileRecommendationDiff",
  "aioTorchCompileRecommendationRequest",
  "createAioTorchCompileRecommendationClient",
]);

const settings = {
  highres: { enabled: true, prompt: "must-not-leak" },
  detailer: { enabled: false, user_data: { secret: true } },
  upscale: { enabled: true, backend: "ultimate_sd_upscale", workflow: { id: 9 } },
  prompt: "must-not-leak",
  profile: { name: "must-not-leak" },
  model: "must-not-leak",
  future_root: "must-not-leak",
};
const originalSettings = clone(settings);
assert.deepEqual(
  module.aioTorchCompileRecommendationRequest(settings, {
    resolution: { width: 1024, height: 1536, prompt: "must-not-leak" },
    batchSize: 4,
    user: "must-not-leak",
  }),
  {
    generation_settings: {
      highres: { enabled: true },
      detailer: { enabled: false },
      upscale: { enabled: true, backend: "ultimate_sd_upscale" },
    },
    resolution: { width: 1024, height: 1536 },
    batch_size: 4,
  },
  "The request must contain only bounded workload facts",
);
assert.deepEqual(settings, originalSettings, "Building a request must not mutate settings");
assert.deepEqual(
  module.aioTorchCompileRecommendationRequest({
    highres: { enabled: "true" },
    detailer: null,
    upscale: { enabled: true, backend: "x".repeat(100) },
  }, {
    resolution: { width: 0, height: 99999 },
    batchSize: 0,
  }),
  {
    generation_settings: {
      highres: { enabled: null },
      detailer: { enabled: null },
      upscale: { enabled: true, backend: "x".repeat(80) },
    },
    resolution: {},
    batch_size: 1,
  },
  "Invalid optional context must fall back without guessing",
);

const backendResponse = {
  supported: true,
  profile: "stable_variable_shapes",
  policy_version: "recommendation-v1",
  values: {
    enabled: true,
    backend: "inductor",
    fullgraph: false,
    mode: "default",
    dynamic: "auto",
    compile_transformer_blocks_only: true,
    dynamo_cache_size_limit: 64,
    debug_compile_keys: false,
    disable_dynamic_vram: false,
    future_backend_field: "ignored",
  },
  reason_codes: ["highres_changes_shape"],
  warnings: ["first_compile_may_be_slow"],
  environment: {
    accelerator: "cuda",
    total_vram_mb: 16302,
    device_name: "must-not-propagate",
  },
  future_response_field: "ignored",
};
const expectedNormalized = {
  supported: true,
  profile: "stable_variable_shapes",
  policyVersion: "recommendation-v1",
  values: {
    enabled: true,
    backend: "inductor",
    fullgraph: false,
    mode: "default",
    dynamic: "auto",
    compile_transformer_blocks_only: true,
    dynamo_cache_size_limit: 64,
    debug_compile_keys: false,
    disable_dynamic_vram: false,
  },
  reasonCodes: ["highres_changes_shape"],
  warnings: ["first_compile_may_be_slow"],
  environment: { accelerator: "cuda", totalVramMb: 16302 },
};
assert.deepEqual(
  module.aioNormalizeTorchCompileRecommendation(backendResponse),
  expectedNormalized,
  "Only the canonical response allowlist may reach dialog controls",
);
assert.deepEqual(
  module.aioNormalizeTorchCompileRecommendation({
    supported: false,
    profile: "unsupported_environment",
    policy_version: "recommendation-v1",
    values: { enabled: true },
    reason_codes: ["unsupported_accelerator"],
    warnings: [],
    environment: { accelerator: 9, total_vram_mb: -1 },
  }),
  {
    supported: false,
    profile: "unsupported_environment",
    policyVersion: "recommendation-v1",
    values: null,
    reasonCodes: ["unsupported_accelerator"],
    warnings: [],
    environment: { accelerator: "unknown", totalVramMb: null },
  },
  "Unsupported recommendations must never expose partial control values",
);

assert.deepEqual(
  module.aioTorchCompileRecommendationDiff(
    {
      enabled: false,
      backend: "manual-backend",
      dynamic: "false",
      future_manual_field: "preserve",
    },
    {
      ...expectedNormalized.values,
      future_recommendation_field: "ignored",
    },
  ),
  [
    { name: "enabled", current: false, recommended: true },
    { name: "backend", current: "manual-backend", recommended: "inductor" },
    { name: "fullgraph", current: undefined, recommended: false },
    { name: "mode", current: undefined, recommended: "default" },
    { name: "dynamic", current: "false", recommended: "auto" },
    { name: "compile_transformer_blocks_only", current: undefined, recommended: true },
    { name: "dynamo_cache_size_limit", current: undefined, recommended: 64 },
    { name: "debug_compile_keys", current: undefined, recommended: false },
    { name: "disable_dynamic_vram", current: undefined, recommended: false },
  ],
  "Diffs must be restricted to the nine Torch Compile controls",
);

const calls = [];
const client = module.createAioTorchCompileRecommendationClient({
  fetchJson(url, options) {
    calls.push({ url, options: clone(options) });
    return Promise.resolve(clone(backendResponse));
  },
});
assert.equal(calls.length, 0, "Client composition must be side-effect free");
assert.deepEqual(
  await client.recommend(settings, {
    resolution: { width: 1024, height: 1536 },
    batchSize: 4,
  }),
  expectedNormalized,
);
assert.deepEqual(calls, [{
  url: "/easyuse_anima/aio/torch-compile/recommend",
  options: {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      generation_settings: {
        highres: { enabled: true },
        detailer: { enabled: false },
        upscale: { enabled: true, backend: "ultimate_sd_upscale" },
      },
      resolution: { width: 1024, height: 1536 },
      batch_size: 4,
    }),
  },
}]);

const validValues = backendResponse.values;
for (const [name, malformed] of [
  ["missing supported", { ...backendResponse, supported: undefined }],
  ["bad profile", { ...backendResponse, profile: "" }],
  ["bad policy", { ...backendResponse, policy_version: 7 }],
  ["bad reasons", { ...backendResponse, reason_codes: "reason" }],
  ["too many warnings", { ...backendResponse, warnings: Array(33).fill("warning") }],
  ["long reason", { ...backendResponse, reason_codes: ["x".repeat(161)] }],
  ["missing values", { ...backendResponse, values: null }],
  ["bad enabled", { ...backendResponse, values: { ...validValues, enabled: 1 } }],
  ["bad backend", { ...backendResponse, values: { ...validValues, backend: "future" } }],
  ["bad fullgraph", { ...backendResponse, values: { ...validValues, fullgraph: "false" } }],
  ["bad mode", { ...backendResponse, values: { ...validValues, mode: "future" } }],
  ["bad dynamic", { ...backendResponse, values: { ...validValues, dynamic: "default" } }],
  ["bad blocks", {
    ...backendResponse,
    values: { ...validValues, compile_transformer_blocks_only: null },
  }],
  ["bad cache", {
    ...backendResponse,
    values: { ...validValues, dynamo_cache_size_limit: 4097 },
  }],
  ["bad debug", { ...backendResponse, values: { ...validValues, debug_compile_keys: 0 } }],
  ["bad vram flag", {
    ...backendResponse,
    values: { ...validValues, disable_dynamic_vram: "false" },
  }],
]) {
  assert.throws(
    () => module.aioNormalizeTorchCompileRecommendation(malformed),
    TypeError,
    `${name} must fail closed`,
  );
}

const fetchFailure = new Error("network unavailable");
const failingClient = module.createAioTorchCompileRecommendationClient({
  fetchJson() {
    return Promise.reject(fetchFailure);
  },
});
await assert.rejects(failingClient.recommend({}, {}), (error) => error === fetchFailure);

console.log("AiO Torch Compile recommendation smoke passed.");
