import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

async function moduleAt(path) {
  const source = readFileSync(new URL(path, import.meta.url), "utf8");
  return import("data:text/javascript;base64," + Buffer.from(source).toString("base64"));
}
const { AIO_GENERATOR_MODEL_PROFILES, aioGeneratorModelProfile, aioModelProfile } = await moduleAt("../web/js/aio/model_profiles.js");
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
console.log("AiO fixed model profiles smoke passed.");

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
assert.deepEqual(aioModelProfile("future-model"), {family: "future-model", label: "future-model", capabilities: {}});
