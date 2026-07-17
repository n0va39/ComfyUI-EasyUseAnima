// @ts-check

import {
  NAIA_RESOLUTION_MODE_BUCKET,
  NAIA_RESOLUTION_MODE_SCALE,
  normalizeNaiaResolutionModeValue,
  normalizeNaiaResolutionScaleValue,
} from "./definition_data.js";

/**
 * @typedef {object} ResolutionEditorDependencies
 * @property {Document} document
 * @property {(key: string) => string} text
 * @property {(key: string, fallback: any) => any} readInternalSetting
 * @property {(id: string, value: any, type?: string) => void} updateInternalSetting
 */

/**
 * Own the NAIA resolution-mode and scale DOM controls while leaving global
 * settings lookup and persistence with the caller.
 *
 * @param {ResolutionEditorDependencies} dependencies
 */
export function createResolutionEditors(dependencies) {
  const {
    document,
    text,
    readInternalSetting,
    updateInternalSetting,
  } = dependencies;

  function naiaResolutionModeSettingValue(value) {
    return readInternalSetting(
      "naia.resolution_mode",
      value ?? NAIA_RESOLUTION_MODE_SCALE,
    );
  }

  function createNaiaResolutionModeEditor(name, setter, value) {
    const settingId = "EasyUseAnima.NAIA.ResolutionMode";
    let persistedValue = normalizeNaiaResolutionModeValue(
      naiaResolutionModeSettingValue(value),
    );

    const row = document.createElement("tr");

    const labelCell = document.createElement("td");
    const labelEl = document.createElement("label");
    labelEl.textContent = name;
    labelEl.title = text("naiaResolutionModeTip");
    labelCell.append(labelEl);

    const controlCell = document.createElement("td");
    const select = document.createElement("select");
    select.setAttribute("aria-label", name);
    select.style.cssText = "box-sizing: border-box; min-width: 150px; padding: 4px 6px;";
    for (const [mode, labelKey] of [
      [NAIA_RESOLUTION_MODE_SCALE, "naiaResolutionModeOriginalScale"],
      [NAIA_RESOLUTION_MODE_BUCKET, "naiaResolutionModeBucketFit"],
    ]) {
      const option = document.createElement("option");
      option.value = mode;
      option.textContent = text(labelKey);
      option.selected = mode === persistedValue;
      select.append(option);
    }

    const persist = () => {
      const nextValue = normalizeNaiaResolutionModeValue(select.value);
      select.value = nextValue;
      updateInternalSetting(settingId, nextValue, "text");
      if (nextValue === persistedValue) {
        return;
      }
      persistedValue = nextValue;
      setter?.(nextValue);
    };

    select.addEventListener("change", persist);
    controlCell.append(select);
    row.append(labelCell, controlCell);
    updateInternalSetting(settingId, persistedValue, "text");
    return row;
  }

  function naiaResolutionScaleSettingValue(value) {
    return readInternalSetting("naia.resolution_scale", value ?? "1.0");
  }

  function createNaiaResolutionScaleEditor(name, setter, value) {
    const settingId = "EasyUseAnima.NAIA.ResolutionScale";
    let persistedValue = normalizeNaiaResolutionScaleValue(
      naiaResolutionScaleSettingValue(value),
    );

    const row = document.createElement("tr");

    const labelCell = document.createElement("td");
    const labelEl = document.createElement("label");
    labelEl.textContent = name;
    labelEl.title = text("naiaResolutionScaleTip");
    labelCell.append(labelEl);

    const controlCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.value = persistedValue;
    input.placeholder = "1.5";
    input.spellcheck = false;
    input.style.cssText = "box-sizing: border-box; width: 92px; padding: 4px 6px;";

    const syncRaw = () => {
      updateInternalSetting(settingId, input.value.replace(",", "."), "text");
    };
    const persist = () => {
      const normalized = normalizeNaiaResolutionScaleValue(input.value);
      input.value = normalized;
      updateInternalSetting(settingId, normalized, "text");
      if (normalized === persistedValue) {
        return;
      }
      persistedValue = normalized;
      setter?.(normalized);
    };

    input.addEventListener("input", syncRaw);
    input.addEventListener("change", persist);
    input.addEventListener("blur", persist);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        input.blur();
      }
    });

    controlCell.append(input);
    row.append(labelCell, controlCell);
    updateInternalSetting(settingId, persistedValue, "text");
    return row;
  }

  return {
    createNaiaResolutionModeEditor,
    createNaiaResolutionScaleEditor,
  };
}
