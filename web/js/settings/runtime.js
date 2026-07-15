// @ts-check

/** @typedef {Record<string, any>} SettingsState */

/**
 * @typedef {object} SettingsRuntimeDependencies
 * @property {() => SettingsState | null | undefined} getSettingsState
 * @property {(value: any) => void} setSettingsState
 * @property {(detail: SettingsState) => void} notifySettingsUpdated
 * @property {Record<string, string>} internalKeys
 * @property {(type: string, value: any) => string} normalizeValue
 * @property {() => Promise<any>} fetchInitialSettings
 * @property {(route: string, options?: object) => Promise<any>} fetchJson
 * @property {(route: string, body: object, options?: object) => Promise<any>} postJson
 */

/**
 * Own settings state normalization, persistence, and initial loading while
 * leaving browser globals and ComfyUI registration with the caller.
 *
 * @param {SettingsRuntimeDependencies} dependencies
 */
export function createSettingsRuntime(dependencies) {
  const {
    getSettingsState,
    setSettingsState,
    notifySettingsUpdated,
    internalKeys,
    normalizeValue,
    fetchInitialSettings,
    fetchJson,
    postJson,
  } = dependencies;

  function ensureSettingsState() {
    let state = getSettingsState();
    if (!state) {
      state = {};
      setSettingsState(state);
    }
    return state;
  }

  function updateInternalSetting(id, value, type = "text") {
    const internalKey = internalKeys[id];
    if (!internalKey) {
      return;
    }
    const state = ensureSettingsState();
    state[internalKey] = normalizeValue(type, value);
    notifySettingsUpdated({ ...state });
  }

  function readInternalSetting(key, fallback) {
    const state = getSettingsState();
    if (state && Object.prototype.hasOwnProperty.call(state, key)) {
      return state[key];
    }
    return fallback;
  }

  async function loadLongTextSettings() {
    const data = await fetchJson("/easyuse_anima/long_text_settings", {
      fallbackJson: {},
    });
    const values = data.values || {};
    const state = ensureSettingsState();
    Object.assign(state, data.settings || {}, values);
    return { ...state };
  }

  async function saveLongTextSettings(values) {
    const data = await postJson(
      "/easyuse_anima/long_text_settings/save",
      { values },
      { fallbackJson: {} },
    );
    const state = ensureSettingsState();
    Object.assign(state, data.settings || {}, data.values || {});
    notifySettingsUpdated({ ...state });
    return data;
  }

  async function loadInitialSettings() {
    try {
      return await fetchInitialSettings();
    } catch {
      return {};
    }
  }

  return {
    updateInternalSetting,
    readInternalSetting,
    loadLongTextSettings,
    saveLongTextSettings,
    loadInitialSettings,
  };
}
