// @ts-check

export const AIO_MODEL_FAMILIES = [
  { value: "anima", label: "Anima" },
  { value: "moss_image", label: "MOSS Image" },
];

const PROFILE_SECTIONS = [
  "sampler", "model_patches", "negpip", "mod_guidance", "artist_mix",
  "highres", "detailer", "upscale",
];
const SHARED_SAMPLER_FIELDS = ["seed", "seed_after_generate"];

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function snapshot(settings) {
  const profile = {};
  for (const key of PROFILE_SECTIONS) {
    if (settings[key] !== undefined) profile[key] = clone(settings[key]);
  }
  for (const key of SHARED_SAMPLER_FIELDS) delete profile.sampler?.[key];
  return profile;
}

// Banks are inert until an explicit family switch. Top-level values always own
// the active execution state, including edits made after restoring a profile.
export function aioSwitchModelFamily(settings, family, createDefaults) {
  if (!AIO_MODEL_FAMILIES.some((entry) => entry.value === family)) {
    throw new RangeError(`Unsupported model family: ${family}`);
  }
  const currentFamily = settings.model_family || "anima";
  const next = clone(settings);
  if (family === currentFamily) return next;
  next.model_settings ||= {};
  next.model_settings[currentFamily] = snapshot(settings);
  const saved = next.model_settings[family];
  const defaults = snapshot(createDefaults(family));
  // A saved bank comes from a full UI snapshot. Missing sections receive current
  // family defaults, while extension fields inside saved sections are retained.
  for (const key of PROFILE_SECTIONS) {
    next[key] = clone(saved?.[key] ?? defaults[key]);
  }
  for (const key of SHARED_SAMPLER_FIELDS) {
    if (settings.sampler?.[key] !== undefined) next.sampler[key] = settings.sampler[key];
  }
  next.model_family = family;
  next.version = 5;
  return next;
}
