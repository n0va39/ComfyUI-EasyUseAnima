import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

async function moduleAt(path) {
  const source = readFileSync(new URL(path, import.meta.url), "utf8");
  return import("data:text/javascript;base64," + Buffer.from(source).toString("base64"));
}
const { AIO_GENERATOR_MODEL_PROFILES, aioGeneratorModelProfile, aioModelProfile, aioUpdateModelCapabilities } = await moduleAt("../web/js/aio/model_profiles.js");
const {
  AIO_DEFAULT_GENERATION_SETTINGS,
  aioParseSettingsValue,
  aioSettingsToCompactJson,
} = await moduleAt("../web/js/aio/settings.js");
const parse = (value, family) => aioParseSettingsValue(JSON.stringify(value), AIO_DEFAULT_GENERATION_SETTINGS, family);
const expected = [
  ["EasyUseAnimaAIOGenerator", "anima", 32, 5, 3, "er_sde"],
  ["EasyUseMossAIOGenerator", "moss_image", 25, 2.5, 5, "er_sde"],
  ["EasyUseKrea2AIOGenerator", "krea2", 8, 1, 1.15, "euler"],
];
assert.equal(Object.keys(AIO_GENERATOR_MODEL_PROFILES).length, expected.length);
for (const [type, family, steps, cfg, shift, sampler] of expected) {
  assert.equal(aioGeneratorModelProfile({ type }).family, family);
  assert.equal(aioGeneratorModelProfile({ comfyClass: type }).family, family);
  const settings = parse({}, family);
  assert.equal(settings.model_family, family);
  assert.equal(settings.sampler.steps, steps);
  assert.equal(settings.sampler.cfg, cfg);
  assert.equal(settings.model_patches.aura_flow.shift, shift);
  assert.equal(settings.sampler.sampler_name, sampler);
  assert.equal(settings.sampler.scheduler, "simple");
  assert.deepEqual(parse(JSON.parse(aioSettingsToCompactJson(settings)), family), settings);
  const caps = aioGeneratorModelProfile({ type }).capabilities;
  assert.equal(caps.torchCompile, family !== "moss_image");
  assert.ok(caps.highres && caps.detailer && caps.upscale && caps.kj && caps.artistMix && caps.hooks);
  if (family !== "anima") {
    assert.equal(caps.spectrum, false);
    assert.equal(caps.ditCorrections, false);
    assert.equal(caps.negpip, family === "moss_image");
    for (const stage of [settings.highres, settings.upscale, settings.detailer.face, settings.detailer.eye]) {
      assert.equal(stage.steps, steps);
      assert.equal(stage.cfg, cfg);
      assert.equal(stage.sampler_name, sampler);
      assert.equal(stage.scheduler, "simple");
      assert.equal(stage.spectrum.enabled, false);
      assert.equal(stage.dit_corrections.enabled, false);
    }
    assert.equal(settings.mod_guidance.mode, "disabled");
    assert.equal(settings.artist_mix.mode, "off");
    assert.equal(settings.detailer.face.spectrum.enabled, false);
    assert.equal(settings.highres.enabled, false);
  }
}
assert.equal(aioGeneratorModelProfile({ type: "Other" }), undefined);
const legacy = parse({ schema: "easyuse_anima_aio_generation_settings", version: 4, sampler: { cfg: 7.5 }, future_root: { keep: true } });
assert.equal(legacy.version, 5);
assert.equal(legacy.model_family, "anima");
assert.equal(legacy.sampler.cfg, 7.5);
assert.deepEqual(legacy.future_root, { keep: true });
const partial = parse({ sampler: { steps: 29 } }, "moss_image");
assert.equal(partial.sampler.steps, 29);
assert.equal(partial.sampler.cfg, 2.5);
const foreign = parse({ model_family: "moss_image", sampler: { cfg: 3.4 }, model_settings: { anima: { sampler: { cfg: 99 } } } }, "anima");
assert.equal(foreign.model_family, "moss_image", "explicit foreign identity must survive for visible rejection");
assert.equal(foreign.sampler.cfg, 3.4);
assert.equal(foreign.model_settings.anima.sampler.cfg, 99, "legacy inactive banks stay inert and lossless");
const exactSeed = aioParseSettingsValue('{"sampler":{"seed":18446744073709551615}}', AIO_DEFAULT_GENERATION_SETTINGS, "krea2");
assert.equal(exactSeed.sampler.seed, "18446744073709551615");
assert.equal(exactSeed.sampler.cfg, 1);

const kreaDefaults = parse({}, "krea2");
for (const stage of [kreaDefaults.sampler, kreaDefaults.highres, kreaDefaults.upscale, kreaDefaults.detailer.face, kreaDefaults.detailer.eye]) {
  assert.equal(stage.spectrum.enabled, false);
  assert.equal(stage.spectrum.warmup_steps, 3);
  assert.equal(stage.spectrum.tail_actual_steps, 2);
  assert.equal(stage.spectrum.cheby_degree, 1);
  assert.equal(stage.spectrum.history_size, 8);
}
const savedKrea = parse({sampler: {spectrum: {warmup_steps: 9}}, highres: {spectrum: {tail_actual_steps: 7}}, detailer: {face: {spectrum: {cheby_degree: 4}}}}, "krea2");
assert.equal(savedKrea.sampler.spectrum.warmup_steps, 9);
assert.equal(savedKrea.highres.spectrum.tail_actual_steps, 7);
assert.equal(savedKrea.detailer.face.spectrum.cheby_degree, 4);
assert.deepEqual(parse(JSON.parse(aioSettingsToCompactJson(savedKrea)), "krea2"), savedKrea);

// RAW's published steps/CFG and an arbitrary user shift must survive the same
// settings path. 2.3 is a preservation fixture, not a RAW shift recommendation.
const rawKrea = parse({
  sampler: { steps: 52, cfg: 3.5 },
  model_patches: { aura_flow: { shift: 2.3 } },
}, "krea2");
const restoredRawKrea = parse(JSON.parse(aioSettingsToCompactJson(rawKrea)), "krea2");
assert.equal(restoredRawKrea.sampler.steps, 52);
assert.equal(restoredRawKrea.sampler.cfg, 3.5);
assert.equal(restoredRawKrea.model_patches.aura_flow.shift, 2.3);
assert.deepEqual(restoredRawKrea, rawKrea, "RAW/custom sampling is never reset to Turbo defaults");


const entry = readFileSync(new URL("../web/js/easyuse_anima_aio.js", import.meta.url), "utf8");
const kreaResourceHints = entry.split("\n").filter((line) => line.includes('"text.kreaRequirements":'));
assert.equal(kreaResourceHints.length, 4);
for (const hint of kreaResourceHints) {
  assert.ok(hint.includes("qwen_image_vae.safetensors"), "each locale must identify Krea2's compatible VAE");
  assert.ok(!hint.includes("FLUX.2"));
}

const explicit = parse({model_family: "moss_image", highres: {cfg: 7, spectrum: {enabled: true}}, detailer: {custom_1: {cfg: 8, spectrum: {enabled: true}}}}, "moss_image");
assert.equal(explicit.highres.cfg, 7);
assert.equal(explicit.highres.spectrum.enabled, true);
assert.equal(explicit.detailer.custom_1.spectrum.enabled, true);

assert.equal(aioModelProfile().family, "anima");
assert.equal(aioModelProfile("future-model").feature("spectrum", "sampler").supported, false);
assert.deepEqual(aioModelProfile("future-model").capabilities, {});

function modelInfo(family, features, contractVersion = 1) {
  return { input: { required: { generation_settings: ["STRING", {
    aio_capabilities: { contract_version: contractVersion, model_family: family, features },
  }] } } };
}
const forecast = {
  supported: true, status: "available", stages: ["sampler"],
  provider: "ComfyUI-Spectrum-KSampler", adapter: "SpectrumMossModelPatch", reason_code: "",
};
const allStages = { supported: true, status: "available", stages: ["sampler", "highres", "detailer", "upscale"], provider: "", adapter: "", reason_code: "" };
aioUpdateModelCapabilities({
  modelProfile_moss_image: modelInfo("moss_image", { spectrum: forecast, artist_mix: allStages, aio_hook: allStages }),
  modelProfile_anima: modelInfo("anima", { spectrum: allStages, mod_guidance: allStages }),
});
assert.equal(aioModelProfile("moss_image").feature("spectrum", "sampler").supported, true);
assert.equal(aioModelProfile("moss_image").capabilities.spectrum, false, "legacy stage editors must remain conservative");
assert.equal(aioModelProfile("moss_image").capabilities.artistMix, true);
assert.equal(aioModelProfile("moss_image").capabilities.hooks, true);
assert.equal(aioModelProfile("anima").capabilities.spectrum, true);
assert.equal(aioModelProfile("anima").capabilities.modGuidance, true);
assert.equal(aioModelProfile("krea2").feature("spectrum", "sampler").supported, false, "capability cache is separated by family");
for (const stage of ["highres", "detailer", "upscale"]) {
  const capability = aioModelProfile("moss_image").feature("spectrum", stage);
  assert.equal(capability.supported, false);
  assert.equal(capability.reason_code, "stage_not_supported");
}
for (const status of ["missing_dependency", "incompatible"]) {
  aioUpdateModelCapabilities({modelProfile_moss_image: modelInfo("moss_image", {spectrum: {...forecast, supported: false, status, reason_code: `native_moss_adapter_${status}`}})});
  assert.equal(aioModelProfile("moss_image").feature("spectrum", "sampler").supported, false);
  assert.equal(aioModelProfile("moss_image").feature("spectrum", "sampler").status, status);
}
for (const invalid of [modelInfo("moss_image", {spectrum: forecast}, 2), modelInfo("krea2", {spectrum: forecast}), null]) {
  aioUpdateModelCapabilities({modelProfile_moss_image: modelInfo("moss_image", {spectrum: forecast})});
  assert.equal(aioModelProfile("moss_image").feature("spectrum", "sampler").supported, true);
  aioUpdateModelCapabilities({modelProfile_moss_image: invalid});
  assert.equal(aioModelProfile("moss_image").feature("spectrum", "sampler").supported, false, "invalid/missing capability reads invalidate old support");
}
const {aioQueryOptionalDependencies} = await moduleAt("../web/js/aio/dependencies.js");
const profilesModule = await moduleAt("../web/js/aio/model_profiles.js");
aioUpdateModelCapabilities({modelProfile_moss_image: modelInfo("moss_image", {spectrum: forecast})});
const failedFetch = await aioQueryOptionalDependencies(profilesModule.AIO_MODEL_CAPABILITY_SPECS, async () => { throw new Error("offline"); });
aioUpdateModelCapabilities(failedFetch.nodeInfo);
assert.equal(aioModelProfile("moss_image").feature("spectrum", "sampler").supported, false, "network failures must revoke previously available runtime support");
assert.match(entry, /async function fetchGeneratorOptionalDependencies\(\) \{\s*aioUpdateModelCapabilities\(\{\}\)/);
assert.match(entry, /aioUpdateModelCapabilities\(next\.nodeInfo\)/);
assert.match(entry, /\.\.\.AIO_OPTIONAL_DEPENDENCY_SPECS, \.\.\.AIO_MODEL_CAPABILITY_SPECS/);
console.log("AiO fixed model profiles smoke passed.");
