// @ts-check

/**
 * @typedef {object} AioProfileApiClientDependencies
 * @property {(url: string, options?: Record<string, any>) => Promise<any>} fetchJson
 * @property {(value: string) => string} encodeURIComponent
 */

/**
 * Own the AiO profile endpoint and JSON payload contract without taking
 * ownership of Comfy transport selection or profile UI lifecycle.
 *
 * @param {AioProfileApiClientDependencies} dependencies
 */
export function createAioProfileApiClient(dependencies) {
  const {
    fetchJson,
    encodeURIComponent,
  } = dependencies;

  function postJson(url, payload) {
    return fetchJson(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
  }

  function listProfiles() {
    return fetchJson("/easyuse_anima/aio_profiles");
  }

  function loadProfile(name) {
    return fetchJson(
      `/easyuse_anima/aio_profiles/load?name=${encodeURIComponent(name)}`,
    );
  }

  function saveProfile(name, overwrite, settings) {
    return postJson("/easyuse_anima/aio_profiles/save", {
      name,
      overwrite,
      settings,
    });
  }

  function renameProfile(oldName, newName, overwrite) {
    return postJson("/easyuse_anima/aio_profiles/rename", {
      old_name: oldName,
      new_name: newName,
      overwrite,
    });
  }

  function deleteProfile(name) {
    return postJson("/easyuse_anima/aio_profiles/delete", { name });
  }

  return {
    listProfiles,
    loadProfile,
    saveProfile,
    renameProfile,
    deleteProfile,
  };
}
