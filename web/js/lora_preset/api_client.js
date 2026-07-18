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

  function listProfiles() {
    return fetchJson("/easyuse_anima/lora_profiles");
  }

  function loadProfile(name) {
    return fetchJson(
      `/easyuse_anima/lora_profiles/load?name=${encodeURIComponent(name)}`,
    );
  }

  function saveProfile(name, payload, overwrite = false) {
    return postJson("/easyuse_anima/lora_profiles/save", {
      name,
      ...payload,
      overwrite,
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
