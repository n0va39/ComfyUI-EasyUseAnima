// @ts-check

import {
  parseWildcardExtraPathItems,
  serializeWildcardExtraPathItems,
} from "./definition_data.js";

/**
 * @typedef {object} WildcardExtraPathsEditorDependencies
 * @property {Document} document
 * @property {(key: string) => string} text
 * @property {(key: string, fallback: any) => any} readInternalSetting
 * @property {(id: string, value: any, type?: string) => void} updateInternalSetting
 */

/**
 * Own the wildcard path-list DOM while leaving global settings lookup and
 * persistence with the caller.
 *
 * @param {WildcardExtraPathsEditorDependencies} dependencies
 */
export function createWildcardExtraPathsEditorFactory(dependencies) {
  const {
    document,
    text,
    readInternalSetting,
    updateInternalSetting,
  } = dependencies;

  function wildcardExtraPathsSettingValue(value) {
    return readInternalSetting("wildcard.extra_paths", value ?? "");
  }

  function createWildcardExtraPathsEditor(name, setter, value) {
    const settingId = "EasyUseAnima.Wildcard.ExtraPaths";
    let items = parseWildcardExtraPathItems(wildcardExtraPathsSettingValue(value));
    if (!items.length) {
      items = [""];
    }

    const row = document.createElement("tr");

    const labelCell = document.createElement("td");
    const labelEl = document.createElement("label");
    labelEl.textContent = name;
    labelEl.title = text("wildcardExtraPathsTip");
    labelCell.append(labelEl);

    const controlCell = document.createElement("td");
    const wrapper = document.createElement("div");
    wrapper.style.cssText = "display: flex; flex-direction: column; gap: 6px; min-width: 260px;";

    const list = document.createElement("div");
    list.style.cssText = "display: flex; flex-direction: column; gap: 6px;";

    let persistedValue = serializeWildcardExtraPathItems(items);

    const syncInternal = () => {
      const serialized = serializeWildcardExtraPathItems(items);
      updateInternalSetting(settingId, serialized, "text");
    };

    const persist = () => {
      const serialized = serializeWildcardExtraPathItems(items);
      updateInternalSetting(settingId, serialized, "text");
      if (serialized === persistedValue) {
        return;
      }
      persistedValue = serialized;
      setter?.(serialized);
    };

    const render = () => {
      list.replaceChildren();
      if (!items.length) {
        items = [""];
      }

      items.forEach((item, index) => {
        const itemRow = document.createElement("div");
        itemRow.style.cssText = "display: flex; align-items: center; gap: 6px; min-width: 0;";

        const input = document.createElement("input");
        input.type = "text";
        input.value = item;
        input.placeholder = text("wildcardExtraPathPlaceholder");
        input.spellcheck = false;
        input.style.cssText = "box-sizing: border-box; flex: 1 1 auto; min-width: 120px; padding: 4px 6px;";
        input.addEventListener("input", () => {
          items[index] = input.value;
          syncInternal();
        });
        input.addEventListener("change", persist);
        input.addEventListener("blur", persist);
        input.addEventListener("keydown", (event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            input.blur();
          }
        });

        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.textContent = "x";
        removeButton.title = text("removeWildcardPath");
        removeButton.style.cssText = "width: 28px; min-width: 28px; height: 28px; padding: 0; cursor: pointer;";
        removeButton.addEventListener("click", () => {
          if (items.length <= 1) {
            items[0] = "";
          } else {
            items.splice(index, 1);
          }
          persist();
          render();
        });

        itemRow.append(input, removeButton);
        list.append(itemRow);
      });
    };

    const addButton = document.createElement("button");
    addButton.type = "button";
    addButton.textContent = "+";
    addButton.title = text("addWildcardPath");
    addButton.style.cssText = "align-self: flex-start; min-width: 32px; height: 28px; padding: 0 10px; cursor: pointer;";
    addButton.addEventListener("click", () => {
      items.push("");
      render();
      list.lastElementChild?.querySelector("input")?.focus();
    });

    render();
    wrapper.append(list, addButton);
    controlCell.append(wrapper);
    row.append(labelCell, controlCell);
    return row;
  }

  return createWildcardExtraPathsEditor;
}
