// @ts-check

/**
 * @typedef {object} LongTextEditorDependencies
 * @property {Document} document
 * @property {Record<string, any>} fieldGroups
 * @property {(key: string) => string} text
 * @property {() => Promise<Record<string, any>>} loadSettings
 * @property {(values: Record<string, string>) => Promise<any>} saveSettings
 * @property {(callback: () => void, delay: number) => any} schedule
 */

/**
 * Own the long-text settings dialog DOM and listener lifecycle while leaving
 * endpoint access and global settings synchronization with the caller.
 *
 * @param {LongTextEditorDependencies} dependencies
 */
export function createLongTextEditorButtonFactory(dependencies) {
  const {
    document,
    fieldGroups,
    text,
    loadSettings,
    saveSettings,
    schedule,
  } = dependencies;
  let activeLongTextEditor = null;

  function closeLongTextEditor() {
    if (!activeLongTextEditor) {
      return;
    }
    const { overlay, keyHandler } = activeLongTextEditor;
    document.removeEventListener("keydown", keyHandler, true);
    overlay.remove();
    activeLongTextEditor = null;
  }

  function openLongTextEditor(groupKey) {
    const group = fieldGroups[groupKey];
    if (!group) {
      return;
    }
    closeLongTextEditor();

    const overlay = document.createElement("div");
    overlay.className = "easyuse-anima-long-text-overlay";
    overlay.style.cssText =
      "position: fixed; inset: 0; z-index: 2147483000; display: flex; align-items: center; justify-content: center; padding: 24px; box-sizing: border-box; background: rgba(0, 0, 0, 0.52);";

    const panel = document.createElement("div");
    panel.className = "comfy-settings easyuse-anima-long-text-panel";
    panel.style.cssText =
      "box-sizing: border-box; width: min(820px, 92vw); max-height: min(780px, 86vh); overflow: hidden; display: flex; flex-direction: column; gap: 12px; padding: 18px; border-radius: 8px; background: var(--comfy-menu-bg, #202020); color: var(--fg-color, #ddd); box-shadow: 0 18px 60px rgba(0, 0, 0, 0.55);";

    const container = document.createElement("div");
    container.style.cssText =
      "box-sizing: border-box; overflow: auto; display: flex; flex-direction: column; gap: 14px; padding-right: 4px;";

    const title = document.createElement("h3");
    title.textContent = text(group.nameKey);
    title.style.margin = "0 0 2px";

    const description = document.createElement("div");
    description.textContent = text(group.tipKey);
    description.style.cssText = "opacity: 0.72; line-height: 1.45;";

    const status = document.createElement("div");
    status.style.cssText = "min-height: 1.4em; opacity: 0.76;";

    const textareas = new Map();
    for (const field of group.fields) {
      const wrapper = document.createElement("label");
      wrapper.style.cssText = "display: flex; flex-direction: column; gap: 6px;";

      const labelText = document.createElement("span");
      labelText.textContent = text(field.labelKey);
      labelText.style.fontWeight = "600";

      const textarea = document.createElement("textarea");
      textarea.spellcheck = false;
      textarea.rows = field.key === "prompt.metadata_filter_words" ? 8 : 7;
      textarea.style.cssText =
        "box-sizing: border-box; width: 100%; min-height: 130px; resize: vertical; padding: 8px; font-family: monospace; white-space: pre-wrap;";

      const help = document.createElement("span");
      help.textContent = field.tipKey ? text(field.tipKey) : "";
      help.style.cssText = "opacity: 0.62; font-size: 0.9em;";

      wrapper.append(labelText, textarea);
      if (help.textContent) {
        wrapper.append(help);
      }
      container.append(wrapper);
      textareas.set(field.key, textarea);
    }

    container.prepend(title, description);
    container.append(status);

    const setStatus = (message, color = "") => {
      status.textContent = message;
      status.style.color = color;
    };

    const actions = document.createElement("div");
    actions.style.cssText = "display: flex; justify-content: flex-end; gap: 8px; flex: 0 0 auto;";

    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.textContent = text("cancel");
    cancelButton.style.cssText = "padding: 6px 12px; cursor: pointer;";
    cancelButton.onclick = closeLongTextEditor;

    const saveButton = document.createElement("button");
    saveButton.type = "button";
    saveButton.textContent = text("save");
    saveButton.style.cssText = "padding: 6px 12px; cursor: pointer;";

    saveButton.onclick = async () => {
      /** @type {Record<string, string>} */
      const values = {};
      for (const [key, textarea] of textareas.entries()) {
        values[key] = textarea.value;
      }
      saveButton.disabled = true;
      setStatus("...");
      try {
        await saveSettings(values);
        setStatus(text("saved"), "#16a34a");
        schedule(() => {
          if (activeLongTextEditor?.overlay === overlay) {
            closeLongTextEditor();
          }
        }, 150);
      } catch (error) {
        setStatus(`${text("saveFailed")}: ${error.message || error}`, "#dc2626");
      } finally {
        saveButton.disabled = false;
      }
    };

    actions.append(cancelButton, saveButton);
    panel.append(container, actions);
    overlay.append(panel);

    overlay.addEventListener("mousedown", (event) => {
      if (event.target === overlay) {
        closeLongTextEditor();
      }
    });
    panel.addEventListener("mousedown", (event) => event.stopPropagation());

    const keyHandler = (event) => {
      if (event.key === "Escape") {
        closeLongTextEditor();
      }
    };
    document.addEventListener("keydown", keyHandler, true);
    activeLongTextEditor = { overlay, keyHandler };

    document.body.append(overlay);
    loadSettings()
      .then((settings) => {
        if (activeLongTextEditor?.overlay !== overlay) {
          return;
        }
        for (const [key, textarea] of textareas.entries()) {
          textarea.value = settings[key] || "";
        }
        textareas.values().next().value?.focus();
      })
      .catch((error) => {
        if (activeLongTextEditor?.overlay !== overlay) {
          return;
        }
        setStatus(`${text("saveFailed")}: ${error.message || error}`, "#dc2626");
      });
  }

  return function createLongTextEditorButton(groupKey) {
    const group = fieldGroups[groupKey];
    const container = document.createElement("div");
    container.style.cssText = "display: flex; align-items: center; gap: 10px; min-width: 0;";

    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text("openEditor");
    button.style.cssText = "padding: 6px 12px; cursor: pointer;";
    button.onclick = () => openLongTextEditor(groupKey);

    const hint = document.createElement("span");
    hint.textContent = text(group.tipKey);
    hint.style.cssText = "opacity: 0.68; font-size: 0.9em; line-height: 1.35;";

    container.append(button, hint);
    return container;
  };
}
