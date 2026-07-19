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

  function profileToken(profile, prefix = "") {
    if (typeof profile?.profile_id !== "string" || !profile.profile_id || !Number.isInteger(profile?.revision) || profile.revision < 0) {
      return {};
    }
    return { [`${prefix}profile_id`]: profile.profile_id, [`${prefix}revision`]: profile.revision };
  }

  function listProfiles() {
    return fetchJson("/easyuse_anima/aio_profiles");
  }

  function loadProfile(name) {
    return fetchJson(
      `/easyuse_anima/aio_profiles/load?name=${encodeURIComponent(name)}`,
    );
  }

  function saveProfile(name, overwrite, settings, profile = null) {
    return postJson("/easyuse_anima/aio_profiles/save", {
      name,
      overwrite,
      settings,
      ...profileToken(overwrite ? profile : null),
    });
  }

  function renameProfile(oldName, newName, overwrite, profile = null, targetProfile = null) {
    return postJson("/easyuse_anima/aio_profiles/rename", {
      old_name: oldName,
      new_name: newName,
      overwrite,
      ...profileToken(profile),
      ...profileToken(overwrite ? targetProfile : null, "target_"),
    });
  }

  function deleteProfile(name, profile = null) {
    return postJson("/easyuse_anima/aio_profiles/delete", {
      name,
      ...profileToken(profile),
    });
  }

  return {
    listProfiles,
    loadProfile,
    saveProfile,
    renameProfile,
    deleteProfile,
  };
}
