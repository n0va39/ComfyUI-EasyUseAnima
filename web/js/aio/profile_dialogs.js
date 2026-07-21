// @ts-check

/**
 * @typedef {object} AioProfileDialogDependencies
 * @property {any} document
 * @property {(title: any, subtitle: any, onClose?: () => void) => {dialog: any, body: any, actions: any, close: () => void}} createDialog
 * @property {(key: string) => string} text
 */

/**
 * Build Promise-based prompt, confirm, and alert dialogs in AiO's own modal
 * layer. Keeping nested dialogs in the same layer prevents host dialogs and
 * toasts from being obscured by the AiO settings backdrop.
 *
 * @param {AioProfileDialogDependencies} dependencies
 */
export function aioCreateProfileDialogs(dependencies) {
  const { document, createDialog, text } = dependencies;

  function actionButton(label, className = "") {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.textContent = label;
    return button;
  }

  /**
   * @param {string} message
   * @param {string} [defaultValue]
   * @returns {Promise<string | null>}
   */
  function prompt(message, defaultValue = "") {
    return new Promise((resolve) => {
      let settled = false;
      let modal;
      const finish = (value) => {
        if (settled) {
          return;
        }
        settled = true;
        modal.close();
        resolve(value);
      };
      modal = createDialog(text("dialog.profile.title"), message, () => finish(null));
      modal.dialog.classList.add("easyuse-anima-aio-dialog-compact");

      const input = document.createElement("input");
      input.type = "text";
      input.className = "easyuse-anima-aio-dialog-text-input";
      input.value = String(defaultValue ?? "");
      input.setAttribute("aria-label", String(message));
      const cancel = actionButton(text("button.cancel"));
      const apply = actionButton(text("button.apply"), "primary");
      cancel.addEventListener("click", () => finish(null));
      apply.addEventListener("click", () => finish(input.value));
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          finish(input.value);
        } else if (event.key === "Escape") {
          event.preventDefault();
          finish(null);
        }
      });
      modal.body.append(input);
      modal.actions.append(cancel, apply);
      input.focus();
      input.select();
    });
  }

  /**
   * @param {string} message
   * @param {"default" | "overwrite" | "delete" | "info"} [type]
   * @returns {Promise<boolean>}
   */
  function confirm(message, type = "default") {
    void type;
    return new Promise((resolve) => {
      let settled = false;
      let modal;
      const finish = (value) => {
        if (settled) {
          return;
        }
        settled = true;
        modal.close();
        resolve(value);
      };
      modal = createDialog(text("dialog.profile.title"), message, () => finish(false));
      modal.dialog.classList.add("easyuse-anima-aio-dialog-compact");
      const cancel = actionButton(text("button.cancel"));
      const apply = actionButton(text("button.apply"), "primary");
      cancel.addEventListener("click", () => finish(false));
      apply.addEventListener("click", () => finish(true));
      modal.actions.append(cancel, apply);
    });
  }

  /**
   * @param {string} message
   * @param {"info" | "success" | "warn" | "error"} [severity]
   * @param {string} [title]
   * @returns {Promise<void>}
   */
  function alert(message, severity = "warn", title = text("dialog.profile.title")) {
    return new Promise((resolve) => {
      let settled = false;
      let modal;
      const finish = () => {
        if (settled) {
          return;
        }
        settled = true;
        modal.close();
        resolve();
      };
      modal = createDialog(title, message, finish);
      modal.dialog.classList.add(
        "easyuse-anima-aio-dialog-compact",
        "easyuse-anima-aio-dialog-alert",
        `easyuse-anima-aio-dialog-alert-${severity}`,
      );
      const close = actionButton(text("button.close"), "primary");
      close.addEventListener("click", finish);
      modal.actions.append(close);
    });
  }

  return Object.freeze({ prompt, alert, confirm });
}
