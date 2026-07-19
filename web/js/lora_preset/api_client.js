// @ts-check

/**
 * @typedef {object} LoraPresetApiClientDependencies
 * @property {(url: string, options?: Record<string, any>) => Promise<any>} fetchJson
 * @property {(value: string) => string} encodeURIComponent
 */

/**
 * Own the LoRA preset endpoint and JSON request contract without taking
 * ownership of Comfy transport selection, response policy, or UI lifecycle.
 *
 * @param {LoraPresetApiClientDependencies} dependencies
 */
export function createLoraPresetApiClient(dependencies) {
  const {
    fetchJson,
    encodeURIComponent,
  } = dependencies;

  function postJson(url, payload) {
    return fetchJson(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  function profileToken(profile) {
    if (typeof profile?.profile_id !== "string" || !profile.profile_id || !Number.isInteger(profile?.revision) || profile.revision < 0) {
      return {};
    }
    return { profile_id: profile.profile_id, revision: profile.revision };
  }

  function profilePayload(payload) {
    const sanitized = { ...(payload || {}) };
    for (const field of ["name", "overwrite", "profile_id", "revision"]) {
      delete sanitized[field];
    }
    return sanitized;
  }

  function listProfiles() {
    return fetchJson("/easyuse_anima/lora_profiles");
  }

  function loadProfile(name) {
    return fetchJson(
      `/easyuse_anima/lora_profiles/load?name=${encodeURIComponent(name)}`,
    );
  }

  function saveProfile(name, payload, overwrite = false, profile = null) {
    return postJson("/easyuse_anima/lora_profiles/save", {
      name,
      ...profilePayload(payload),
      overwrite,
      ...profileToken(overwrite ? profile : null),
    });
  }

  function fixProfile(payload) {
    return postJson("/easyuse_anima/lora_profiles/fix", payload);
  }

  function listLoras() {
    return fetchJson("/easyuse_anima/loras");
  }

  return {
    listProfiles,
    loadProfile,
    saveProfile,
    fixProfile,
    listLoras,
  };
}
