// @ts-check

export const MAX_PROFILES = 16;

export const WIDGET_INDEX = {
  stylePrompt: 0,
  profileIndex: 1,
  profileCount: 2,
  loraName: 3,
  loras: 4,
  profileData: 5,
};

export const INTERNAL_WIDGET_DEFAULTS = {
  profile_count: "4",
  lora_name: "None",
  loras: "[]",
  profile_data: "{}",
};

function looksLikeProfileData(value) {
  if (typeof value !== "string") {
    return false;
  }
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" && !Array.isArray(parsed);
  } catch {
    return false;
  }
}

export function normalizeSerializedWidgets(info) {
  const values = info?.widgets_values;
  if (!Array.isArray(values)) {
    return;
  }
  if (values[WIDGET_INDEX.profileCount] == null || values[WIDGET_INDEX.profileCount] === "") {
    values[WIDGET_INDEX.profileCount] = INTERNAL_WIDGET_DEFAULTS.profile_count;
  }
  values[WIDGET_INDEX.loraName] = INTERNAL_WIDGET_DEFAULTS.lora_name;
  if (Array.isArray(values[WIDGET_INDEX.loras])) {
    values[WIDGET_INDEX.loras] = JSON.stringify(values[WIDGET_INDEX.loras]);
  } else if (typeof values[WIDGET_INDEX.loras] !== "string") {
    values[WIDGET_INDEX.loras] = INTERNAL_WIDGET_DEFAULTS.loras;
  }
  if (!looksLikeProfileData(values[WIDGET_INDEX.profileData])) {
    values[WIDGET_INDEX.profileData] = INTERNAL_WIDGET_DEFAULTS.profile_data;
  }
}

export function profileKey(index) {
  return String(Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(index, 10) || 1)));
}

export function normalizeProfileDataValue(value) {
  try {
    const parsed = typeof value === "string" ? JSON.parse(String(value || "{}")) : value;
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

export function wrapProfileIndex(index, count) {
  const safeCount = Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(count, 10) || 1));
  const safeIndex = Math.max(1, Number.parseInt(index, 10) || 1);
  return ((safeIndex - 1) % safeCount) + 1;
}

export function normalizeLoraEntry(entry) {
  const name = String(entry?.name ?? entry?.lora ?? "").trim();
  const strength = Number.isFinite(Number(entry?.strength)) ? Number(entry.strength) : 1;
  const strengthTwoRaw = entry?.strengthTwo ?? entry?.clipStrength;
  const strengthTwo = strengthTwoRaw == null || strengthTwoRaw === "" ? null : Number(strengthTwoRaw);
  return {
    name,
    on: entry?.on ?? entry?.active ?? true,
    strength,
    strengthTwo: Number.isFinite(strengthTwo) ? strengthTwo : null,
  };
}

export function profileContent(profile) {
  return {
    style_prompt: String(profile?.style_prompt || ""),
    loras: Array.isArray(profile?.loras)
      ? profile.loras.map(normalizeLoraEntry).filter((entry) => entry.name)
      : [],
  };
}

export function profileSnapshot(profile) {
  return JSON.stringify(profileContent(profile));
}

export function isMeaningfulProfile(profile) {
  const content = profileContent(profile);
  return !!content.style_prompt.trim() || content.loras.length > 0;
}

export function profileSavedName(profile) {
  return String(profile?.saved_name || "").trim();
}

export function profileSavedId(profile) {
  return String(profile?.saved_profile_id || "").trim().toLowerCase();
}

export function withSavedMeta(content, previous) {
  const profile = profileContent(content);
  const savedName = profileSavedName(previous);
  const savedProfileId = profileSavedId(previous);
  const savedSnapshot = String(previous?.saved_snapshot || "");
  if (savedName && savedSnapshot) {
    return {
      ...profile,
      saved_name: savedName,
      ...(savedProfileId ? { saved_profile_id: savedProfileId } : {}),
      saved_snapshot: savedSnapshot,
    };
  }
  return profile;
}

export function emptyProfile(_index = 1) {
  void _index;
  return {
    style_prompt: "",
    loras: [],
  };
}
