import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

async function moduleAt(path) {
  const source = readFileSync(new URL(path, import.meta.url), "utf8");
  return import("data:text/javascript;base64," + Buffer.from(source).toString("base64"));
}
const { aioSwitchModelFamily, AIO_MODEL_FAMILIES } = await moduleAt("../web/js/aio/model_profiles.js");
const {
  AIO_DEFAULT_GENERATION_SETTINGS,
  aioGenerationDefaultsForFamily,
  aioParseSettingsValue,
  aioSettingsToCompactJson,
} = await moduleAt("../web/js/aio/settings.js");
const parse = (value) => aioParseSettingsValue(JSON.stringify(value), AIO_DEFAULT_GENERATION_SETTINGS);
const switchFamily = (settings, family) => aioSwitchModelFamily(settings, family, aioGenerationDefaultsForFamily);

assert.deepEqual(AIO_MODEL_FAMILIES.map((entry) => entry.value), ["anima", "moss_image"]);
const legacy = parse({
  schema: "easyuse_anima_aio_generation_settings",
  version: 4,
  sampler: { cfg: 7.5, seed: "18446744073709551615", seed_after_generate: "increment" },
  model_patches: { dave: { enabled: true, strength: 0.7 } },
  highres: { enabled: true, scale_by: 1.7 },
  save: { enabled: false },
  postprocess: { enabled: true },
  future_root: { keep: true },
});
assert.equal(legacy.version, 5);
assert.equal(legacy.model_family, "anima");
assert.deepEqual(legacy.model_settings, {});
const original = JSON.stringify(legacy);
const moss = switchFamily(legacy, "moss_image");
assert.equal(JSON.stringify(legacy), original, "switch must not mutate its source");
assert.equal(moss.model_family, "moss_image");
assert.equal(moss.sampler.steps, 25);
assert.equal(moss.sampler.cfg, 2.5);
assert.equal(moss.sampler.sampler_name, "er_sde");
assert.equal(moss.sampler.scheduler, "simple");
assert.equal(moss.model_patches.aura_flow.shift, 5);
assert.equal(moss.mod_guidance.mode, "disabled");
assert.equal(moss.artist_mix.mode, "off");
assert.equal(moss.model_patches.dave.enabled, false);
assert.equal(moss.model_patches.kj.torch_compile.enabled, false);
assert.equal(moss.model_patches.safe_pag.enabled, false);
assert.equal(moss.highres.enabled, false);
assert.equal(moss.detailer.enabled, false);
assert.equal(moss.detailer.face.spectrum.enabled, false);
assert.equal(moss.upscale.enabled, false);
assert.equal(moss.sampler.seed, "18446744073709551615");
assert.equal(moss.sampler.seed_after_generate, "increment");
assert.equal(moss.model_settings.anima.sampler.seed, undefined);
assert.equal(moss.model_settings.anima.sampler.seed_after_generate, undefined);
assert.equal(moss.save.enabled, false);
assert.equal(moss.postprocess.enabled, true);
assert.deepEqual(moss.future_root, { keep: true });

moss.sampler.cfg = 3.4;
moss.sampler.seed = 52;
moss.sampler.seed_after_generate = "fixed";
moss.sampler.future_sampler = "preserved";
moss.preview.feed_count = 7;
const anima = switchFamily(moss, "anima");
assert.equal(anima.sampler.cfg, 7.5);
assert.equal(anima.model_patches.dave.strength, 0.7);
assert.equal(anima.model_patches.dave.enabled, true);
assert.equal(anima.highres.enabled, true);
assert.equal(anima.sampler.seed, 52);
assert.equal(anima.sampler.seed_after_generate, "fixed");
assert.equal(anima.preview.feed_count, 7);
const restoredMoss = switchFamily(anima, "moss_image");
assert.equal(restoredMoss.sampler.cfg, 3.4);
assert.equal(restoredMoss.sampler.future_sampler, "preserved");
assert.deepEqual(parse(restoredMoss), restoredMoss);
assert.deepEqual(JSON.parse(aioSettingsToCompactJson(restoredMoss)), restoredMoss);
assert.deepEqual(switchFamily(restoredMoss, "moss_image"), restoredMoss, "same-family selection cannot restore stale bank values");
assert.throws(() => switchFamily(restoredMoss, "unknown"), /Unsupported model family/);

const partial = parse({ model_family: "moss_image", sampler: { steps: 29 } });
assert.equal(partial.sampler.steps, 29);
assert.equal(partial.sampler.cfg, 2.5);
assert.equal(partial.model_patches.aura_flow.shift, 5);
assert.equal(partial.mod_guidance.mode, "disabled");
assert.equal(partial.artist_mix.mode, "off");
assert.equal(parse({}).sampler.cfg, 5);
assert.equal(parse({}).mod_guidance.mode, "prompt_data");
const inertBank = parse({
  model_family: "moss_image",
  sampler: { cfg: 2.8 },
  model_settings: { moss_image: { sampler: { cfg: 90 } } },
});
assert.equal(inertBank.sampler.cfg, 2.8, "saved banks must remain inert during parse");
assert.equal(JSON.parse(aioSettingsToCompactJson(inertBank)).sampler.cfg, 2.8);
console.log("AiO model family profiles smoke passed.");
