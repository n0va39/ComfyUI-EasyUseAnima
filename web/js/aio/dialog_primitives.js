// @ts-check

/**
 * @typedef {object} AioDialogPrimitiveDependencies
 * @property {any} document
 * @property {() => void} ensureStyle
 * @property {(value: any) => string} staticText
 * @property {(key: string) => string} text
 * @property {(label: any, tooltipKey: string) => {displayLabel: string, tooltipText: string}} resolveFieldPresentation
 * @property {(element: any, key: string) => void} applyTooltip
 * @property {(element: any, text: string) => void} applyTooltipText
 */

/**
 * Build the DOM-only primitives shared by the AiO node panel and settings
 * dialogs. Translation, tooltip, and style ownership stay with the entry and
 * are injected explicitly so this module remains import-safe and lifecycle
 * neutral.
 *
 * @param {AioDialogPrimitiveDependencies} dependencies
 */
export function aioCreateDialogPrimitives(dependencies) {
  const {
    document,
    ensureStyle,
    staticText,
    text,
    resolveFieldPresentation,
    applyTooltip,
    applyTooltipText,
  } = dependencies;

  /**
   * @param {any} label
   * @param {any} control
   * @param {string} [className]
   * @param {string} [tooltipKey]
   */
  function createNodeField(label, control, className = "", tooltipKey = "") {
    const wrapper = document.createElement("div");
    wrapper.className = `easyuse-anima-aio-node-field ${className}`.trim();
    const labelEl = document.createElement("label");
    applyTooltip(wrapper, tooltipKey);
    applyTooltip(labelEl, tooltipKey);
    applyTooltip(control, tooltipKey);
    if (control?.type === "checkbox") {
      wrapper.classList.add("checkbox");
      const labelText = document.createElement("span");
      labelText.textContent = label;
      labelEl.append(labelText, control);
      wrapper.append(labelEl);
    } else {
      labelEl.textContent = label;
      wrapper.append(labelEl, control);
    }
    return wrapper;
  }

  /**
   * @param {any} section
   * @param {any} label
   * @param {any} control
   * @param {string} [tooltipKey]
   */
  function field(section, label, control, tooltipKey = "") {
    const row = document.createElement("div");
    row.className = "easyuse-anima-aio-field";
    const labelEl = document.createElement("label");
    const { displayLabel, tooltipText } = resolveFieldPresentation(label, tooltipKey);
    applyTooltipText(row, tooltipText);
    applyTooltipText(labelEl, tooltipText);
    applyTooltipText(control, tooltipText);
    if (control?.type === "checkbox") {
      row.classList.add("checkbox");
      const labelText = document.createElement("span");
      labelText.textContent = displayLabel;
      labelEl.append(labelText, control);
      row.append(labelEl);
    } else {
      labelEl.textContent = displayLabel;
      row.append(labelEl, control);
    }
    section.append(row);
    return control;
  }

  /**
   * @param {any} title
   * @param {any} subtitle
   */
  function createDialog(title, subtitle) {
    ensureStyle();
    const backdrop = document.createElement("div");
    backdrop.className = "easyuse-anima-aio-backdrop";
    const dialog = document.createElement("div");
    dialog.className = "easyuse-anima-aio-dialog";
    const header = document.createElement("header");
    const titleBox = document.createElement("div");
    const heading = document.createElement("h2");
    heading.textContent = staticText(title);
    const description = document.createElement("p");
    description.textContent = staticText(subtitle);
    titleBox.append(heading, description);
    const close = document.createElement("button");
    close.className = "easyuse-anima-aio-close";
    close.textContent = text("button.close");
    header.append(titleBox, close);
    const body = document.createElement("div");
    body.className = "easyuse-anima-aio-body";
    const actions = document.createElement("div");
    actions.className = "easyuse-anima-aio-actions";
    dialog.append(header, body, actions);
    backdrop.append(dialog);
    close.addEventListener("click", () => backdrop.remove());
    backdrop.addEventListener("pointerdown", (event) => {
      if (event.target === backdrop) {
        backdrop.remove();
      }
    });
    document.body.append(backdrop);
    return { backdrop, body, actions };
  }

  return Object.freeze({
    createDialog,
    createNodeField,
    field,
  });
}
