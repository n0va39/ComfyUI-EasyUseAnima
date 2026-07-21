// @ts-check

/**
 * @typedef {object} AioProfileDialogDependencies
 * @property {() => any} getExtensionManager
 * @property {(key: string) => string} text
 */

/**
 * Adapt ComfyUI's extension dialog and toast services for AiO profile CRUD.
 * Browser-native prompt/confirm/alert APIs are unavailable in some ComfyUI
 * Desktop webviews, while this host service is shared by Desktop and browser.
 *
 * @param {AioProfileDialogDependencies} dependencies
 */
export function aioCreateProfileDialogs(dependencies) {
  const { getExtensionManager, text } = dependencies;

  function services() {
    const extensionManager = getExtensionManager();
    const dialog = extensionManager?.dialog;
    const toast = extensionManager?.toast;
    if (typeof dialog?.prompt !== "function" || typeof dialog?.confirm !== "function") {
      throw new Error("ComfyUI dialog service is unavailable");
    }
    return { dialog, toast };
  }

  /**
   * @param {string} message
   * @param {string} [defaultValue]
   * @returns {Promise<string | null>}
   */
  async function prompt(message, defaultValue = "") {
    const result = await services().dialog.prompt({
      title: text("dialog.profile.title"),
      message,
      defaultValue,
      placeholder: "",
    });
    return typeof result === "string" ? result : null;
  }

  /**
   * @param {string} message
   * @param {"default" | "overwrite" | "delete" | "info"} [type]
   * @returns {Promise<boolean>}
   */
  async function confirm(message, type = "default") {
    const result = await services().dialog.confirm({
      title: text("dialog.profile.title"),
      message,
      type,
    });
    return result === true;
  }

  /**
   * @param {string} message
   * @param {"info" | "success" | "warn" | "error"} [severity]
   * @returns {Promise<void>}
   */
  async function alert(message, severity = "warn") {
    const { toast } = services();
    if (typeof toast?.add !== "function") {
      throw new Error("ComfyUI toast service is unavailable");
    }
    toast.add({
      severity,
      summary: text("dialog.profile.title"),
      detail: message,
      life: 5000,
    });
  }

  return Object.freeze({ prompt, alert, confirm });
}
