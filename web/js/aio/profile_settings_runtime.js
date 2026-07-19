// @ts-check

/**
 * @typedef {object} AioProfileApi
 * @property {() => Promise<any>} listProfiles
 * @property {(name: string) => Promise<any>} loadProfile
 * @property {(name: string, overwrite: boolean, settings: any, profile?: any) => Promise<any>} saveProfile
 * @property {(oldName: string, newName: string, overwrite: boolean, profile?: any, targetProfile?: any) => Promise<any>} renameProfile
 * @property {(name: string, profile?: any) => Promise<any>} deleteProfile
 */

/**
 * @typedef {object} AioProfileCore
 * @property {string} customValue
 * @property {() => string[]} builtinIds
 * @property {(profileId: string, defaultSettings: any) => any} builtinSettings
 * @property {(settings: any) => string} fingerprint
 * @property {(name: string) => string} userValue
 * @property {(value: string) => string} userName
 * @property {(profiles: any[], name: string) => any} findUser
 * @property {(options: Record<string, any>) => string} resolveValue
 */

/**
 * @typedef {object} AioProfileSettingsCore
 * @property {any} defaultSettings
 * @property {(defaults: any, current: any) => any} mergeDefaults
 * @property {(settings: any) => any} migratePostprocess
 */

/**
 * @typedef {object} AioProfileNodeAdapter
 * @property {(node: any) => any} getSettings
 * @property {(node: any, settings: any) => void} applyVisibleSettings
 * @property {(node: any, settings: any, markDirty?: boolean) => void} writeSettings
 * @property {(node: any) => void} renderPanel
 * @property {() => void} refreshPanels
 * @property {(node: any) => void} markDirty
 */

/**
 * @typedef {object} AioProfileDialogs
 * @property {(message: string, defaultValue?: string) => string | null} prompt
 * @property {(message: string) => void} alert
 * @property {(message: string) => boolean} confirm
 */

/**
 * @typedef {object} AioProfileSettingsRuntimeDependencies
 * @property {any} document
 * @property {(title: string, subtitle: string) => {backdrop: any, body: any, actions: any}} createDialog
 * @property {(section: any, label: string, control: any, tooltipKey?: string) => any} field
 * @property {(key: string) => string} text
 * @property {(key: string, values?: Record<string, any>) => string} format
 * @property {AioProfileDialogs} dialogs
 * @property {AioProfileApi} profileApi
 * @property {AioProfileCore} profileCore
 * @property {AioProfileSettingsCore} settingsCore
 * @property {AioProfileNodeAdapter} nodeAdapter
 */

/**
 * Own the AiO profile cache, CRUD, node-identity, and profile-dialog lifecycle.
 * Extension registration, panel placement, graph traversal, and workflow
 * serialization remain in the entry module and are supplied as adapters.
 *
 * @param {AioProfileSettingsRuntimeDependencies} dependencies
 */
export function aioCreateProfileSettingsRuntime(dependencies) {
  const {
    document,
    createDialog,
    field,
    text,
    format,
    dialogs,
    profileApi,
    profileCore,
    settingsCore,
    nodeAdapter,
  } = dependencies;
  const {
    customValue,
    builtinIds,
    builtinSettings,
    fingerprint,
    userValue,
    userName,
    findUser,
    resolveValue,
  } = profileCore;
  const {
    defaultSettings,
    mergeDefaults,
    migratePostprocess,
  } = settingsCore;
  const {
    getSettings,
    applyVisibleSettings,
    writeSettings,
    renderPanel,
    refreshPanels,
    markDirty,
  } = nodeAdapter;

  const state = {
    loaded: false,
    loading: null,
    profiles: [],
  };

  function errorMessage(error) {
    return error instanceof Error ? error.message : String(error || "Unknown error");
  }

  function userProfileByName(name) {
    return findUser(state.profiles, name);
  }

  function rememberProfile(profile, ...replacedNames) {
    const name = String(profile?.name || "").trim();
    if (!name) {
      return;
    }
    const replaced = new Set([...replacedNames, name].map((value) => String(value || "").toLowerCase()));
    state.profiles = state.profiles.filter(
      (current) => !replaced.has(String(current?.name || "").toLowerCase()),
    );
    state.profiles.push(profile);
  }

  function forgetProfile(name) {
    const expected = String(name || "").toLowerCase();
    state.profiles = state.profiles.filter(
      (profile) => String(profile?.name || "").toLowerCase() !== expected,
    );
  }

  async function loadProfiles({ force = false } = {}) {
    if (state.loaded && !force) {
      return state.profiles;
    }
    if (!state.loading) {
      state.loading = profileApi.listProfiles()
        .then((data) => {
          state.profiles = Array.isArray(data?.profiles)
            ? data.profiles.filter((profile) => String(profile?.name || "").trim())
            : [];
          state.loaded = true;
          return state.profiles;
        })
        .finally(() => {
          state.loading = null;
        });
    }
    return state.loading;
  }

  function applyProfileSettings(node, value, settings) {
    const next = migratePostprocess(mergeDefaults(defaultSettings, settings));
    applyVisibleSettings(node, next);
    writeSettings(node, next, true);
    node.__easyuseAnimaGeneratorProfileValue = value;
    node.__easyuseAnimaGeneratorProfileFingerprint = fingerprint(getSettings(node));
    renderPanel(node);
    markDirty(node);
  }

  async function applyProfile(node, value) {
    const textValue = String(value || customValue);
    if (textValue === customValue) {
      return;
    }
    if (textValue.startsWith("builtin:")) {
      const profileId = textValue.slice(8);
      applyProfileSettings(
        node,
        textValue,
        builtinSettings(profileId, defaultSettings),
      );
      return;
    }
    const name = userName(textValue);
    const data = await profileApi.loadProfile(name);
    const profile = data?.profile || null;
    rememberProfile(profile ? { ...profile, name } : null, name);
    if (!profile?.settings || typeof profile.settings !== "object") {
      throw new Error("Profile settings are missing");
    }
    applyProfileSettings(node, userValue(profile.name || name), profile.settings);
  }

  async function saveUserProfile(node, selectedValue = node.__easyuseAnimaGeneratorProfileValue) {
    const selectedName = userName(selectedValue);
    const requestedName = dialogs.prompt(text("profile.savePrompt"), selectedName || "");
    if (requestedName == null) {
      return;
    }
    const name = requestedName.trim();
    if (!name) {
      dialogs.alert(text("profile.nameRequired"));
      return;
    }
    const existing = userProfileByName(name);
    const overwrite = !!existing;
    if (overwrite && !dialogs.confirm(format("profile.overwriteConfirm", { name: existing.name }))) {
      return;
    }
    const settings = getSettings(node);
    const data = await profileApi.saveProfile(name, overwrite, settings, existing);
    rememberProfile(data?.profile, name);
    await loadProfiles({ force: true });
    node.__easyuseAnimaGeneratorProfileValue = userValue(data?.profile?.name || name);
    node.__easyuseAnimaGeneratorProfileFingerprint = fingerprint(settings);
    refreshPanels();
  }

  async function renameUserProfile(node, selectedValue = node.__easyuseAnimaGeneratorProfileValue) {
    const oldName = userName(selectedValue);
    if (!oldName) {
      return;
    }
    const currentName = userName(syncValue(node));
    const requestedName = dialogs.prompt(text("profile.renamePrompt"), oldName);
    if (requestedName == null) {
      return;
    }
    const newName = requestedName.trim();
    if (!newName) {
      dialogs.alert(text("profile.nameRequired"));
      return;
    }
    const existing = userProfileByName(newName);
    const overwrite = !!existing && existing.name.toLowerCase() !== oldName.toLowerCase();
    if (overwrite && !dialogs.confirm(format("profile.overwriteConfirm", { name: existing.name }))) {
      return;
    }
    const current = userProfileByName(oldName);
    const data = await profileApi.renameProfile(
      oldName,
      newName,
      overwrite,
      current,
      overwrite ? existing : null,
    );
    rememberProfile(data?.profile, oldName, newName);
    await loadProfiles({ force: true });
    if (currentName.toLowerCase() === oldName.toLowerCase()) {
      node.__easyuseAnimaGeneratorProfileValue = userValue(data?.profile?.name || newName);
    }
    refreshPanels();
  }

  async function deleteUserProfile(node, selectedValue = node.__easyuseAnimaGeneratorProfileValue) {
    const name = userName(selectedValue);
    if (!name || !dialogs.confirm(format("profile.deleteConfirm", { name }))) {
      return;
    }
    const currentName = userName(syncValue(node));
    const current = userProfileByName(name);
    await profileApi.deleteProfile(name, current);
    forgetProfile(name);
    await loadProfiles({ force: true });
    if (currentName.toLowerCase() === name.toLowerCase()) {
      node.__easyuseAnimaGeneratorProfileValue = customValue;
      delete node.__easyuseAnimaGeneratorProfileFingerprint;
    }
    refreshPanels();
  }

  function resolvedValue(node, settings = getSettings(node)) {
    return resolveValue({
      settings,
      defaultSettings,
      selectedValue: node?.__easyuseAnimaGeneratorProfileValue,
      selectedFingerprint: node?.__easyuseAnimaGeneratorProfileFingerprint,
      profiles: state.profiles,
      customValue,
    });
  }

  function syncValue(node, settings = getSettings(node)) {
    const value = resolvedValue(node, settings);
    node.__easyuseAnimaGeneratorProfileValue = value;
    if (value === customValue) {
      delete node.__easyuseAnimaGeneratorProfileFingerprint;
    }
    return value;
  }

  function displayLabel(value) {
    const textValue = String(value || customValue);
    if (textValue === customValue) {
      return text("profile.custom");
    }
    const profileName = userName(textValue);
    if (profileName) {
      return profileName;
    }
    const builtinId = textValue.startsWith("builtin:") ? textValue.slice(8) : "";
    return builtinIds().includes(builtinId)
      ? text(`profile.${builtinId}`)
      : text("profile.custom");
  }

  function open(node) {
    const currentValue = syncValue(node);
    const { backdrop, body, actions } = createDialog(
      text("dialog.profile.title"),
      text("dialog.profile.subtitle"),
    );
    body.classList.add("easyuse-anima-aio-one-column");

    const section = document.createElement("section");
    section.className = "easyuse-anima-aio-section full";
    const profileSelect = document.createElement("select");
    profileSelect.title = text("profile.selectTip");
    if (currentValue === customValue) {
      const customOption = document.createElement("option");
      customOption.value = customValue;
      customOption.textContent = text("profile.custom");
      profileSelect.append(customOption);
    }
    const builtInGroup = document.createElement("optgroup");
    builtInGroup.label = text("profile.groupBuiltIn");
    for (const profileId of builtinIds()) {
      const option = document.createElement("option");
      option.value = `builtin:${profileId}`;
      option.textContent = text(`profile.${profileId}`);
      builtInGroup.append(option);
    }
    profileSelect.append(builtInGroup);
    if (state.profiles.length) {
      const userGroup = document.createElement("optgroup");
      userGroup.label = text("profile.groupUser");
      for (const profile of state.profiles) {
        const option = document.createElement("option");
        option.value = userValue(profile.name);
        option.textContent = profile.name;
        userGroup.append(option);
      }
      profileSelect.append(userGroup);
    }
    profileSelect.value = currentValue;
    field(section, "Profile", profileSelect, "profile.selectTip");

    const managerActions = document.createElement("div");
    managerActions.className = "easyuse-anima-aio-profile-manager-actions";
    const makeActionButton = (label) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      return button;
    };
    const saveProfile = makeActionButton(text("button.profileSave"));
    const renameProfile = makeActionButton(text("button.profileRename"));
    const deleteProfile = makeActionButton(text("button.profileDelete"));
    managerActions.append(saveProfile, renameProfile, deleteProfile);
    section.append(managerActions);
    body.append(section);

    const cancel = makeActionButton(text("button.cancel"));
    const apply = makeActionButton(text("button.profileApply"));
    apply.className = "primary";
    actions.append(cancel, apply);

    let busy = false;
    const refreshActions = () => {
      const isUserProfile = !!userName(profileSelect.value);
      renameProfile.disabled = busy || !isUserProfile;
      deleteProfile.disabled = busy || !isUserProfile;
      saveProfile.disabled = busy;
      cancel.disabled = busy;
      apply.disabled = busy || profileSelect.value === customValue;
    };
    const run = async (callback, { reopen = false } = {}) => {
      if (busy) {
        return;
      }
      busy = true;
      refreshActions();
      try {
        await callback();
        backdrop.remove();
        if (reopen) {
          open(node);
        }
      } catch (error) {
        dialogs.alert(format("profile.requestFailed", {
          message: errorMessage(error),
        }));
      } finally {
        busy = false;
        if (backdrop.isConnected) {
          refreshActions();
        }
      }
    };
    profileSelect.addEventListener("change", refreshActions);
    cancel.addEventListener("click", () => backdrop.remove());
    apply.addEventListener("click", () => run(
      () => applyProfile(node, profileSelect.value),
    ));
    saveProfile.addEventListener("click", () => run(
      () => saveUserProfile(node, profileSelect.value),
      { reopen: true },
    ));
    renameProfile.addEventListener("click", () => run(
      () => renameUserProfile(node, profileSelect.value),
      { reopen: true },
    ));
    deleteProfile.addEventListener("click", () => run(
      () => deleteUserProfile(node, profileSelect.value),
      { reopen: true },
    ));
    refreshActions();
  }

  return {
    loadProfiles,
    syncValue,
    displayLabel,
    open,
  };
}
