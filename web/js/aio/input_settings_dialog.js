// @ts-check

/**
 * @typedef {object} AioInputSettingsDialogDependencies
 * @property {any} document
 * @property {(title: any, subtitle: any) => {backdrop: any, body: any, actions: any}} createDialog
 * @property {(section: any, label: any, control: any, tooltipKey?: string) => any} field
 * @property {(options: any[], value: any) => any} selectInput
 * @property {(value: any) => string} staticText
 * @property {(key: string) => string} text
 * @property {any} defaultInputSettings
 * @property {string} inputSettingsWidget
 * @property {(node: any, name: string) => any} findWidget
 * @property {(widget: any, defaults: any) => any} parseSettings
 * @property {(defaults: any, current: any) => any} mergeDefaults
 * @property {(node: any, widget: any, settings: any) => void} writeSettings
 */

/**
 * Build the Input Settings opener from shared DOM and settings adapters.
 * Extension lifecycle and node registration remain owned by the entry module.
 *
 * @param {AioInputSettingsDialogDependencies} dependencies
 * @returns {(node: any) => void}
 */
export function aioCreateInputSettingsDialog(dependencies) {
  const {
    document,
    createDialog,
    field,
    selectInput,
    staticText,
    text,
    defaultInputSettings,
    inputSettingsWidget,
    findWidget,
    parseSettings,
    mergeDefaults,
    writeSettings,
  } = dependencies;

  return function openInputSettings(node) {
    const widget = findWidget(node, inputSettingsWidget);
    const settings = parseSettings(widget, defaultInputSettings);
    const { backdrop, body, actions } = createDialog(
      "Easy Use Anima Input Settings",
      "Advanced resource options are saved internally with the workflow.",
    );
    const section = document.createElement("section");
    section.className = "easyuse-anima-aio-section full";
    section.append(Object.assign(document.createElement("h3"), { textContent: staticText("Loader Options") }));
    const weightDtype = field(
      section,
      "UNET weight dtype",
      selectInput(["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"], settings.resources.unet_weight_dtype),
    );
    const clipDevice = field(
      section,
      "CLIP device",
      selectInput(["default", "cpu"], settings.resources.clip_device),
    );
    const loaderMode = document.createElement("p");
    loaderMode.textContent = text("text.inputLoaderMode");
    section.append(loaderMode);
    body.append(section);

    const cancel = document.createElement("button");
    cancel.textContent = text("button.cancel");
    const apply = document.createElement("button");
    apply.className = "primary";
    apply.textContent = text("button.apply");
    actions.append(cancel, apply);
    cancel.addEventListener("click", () => backdrop.remove());
    apply.addEventListener("click", () => {
      const next = mergeDefaults(defaultInputSettings, settings);
      next.resources.loader_mode = "split";
      next.resources.clip_loader = "single";
      next.resources.unet_weight_dtype = weightDtype.value || "default";
      next.resources.clip_device = clipDevice.value || "default";
      writeSettings(node, widget, next);
      backdrop.remove();
    });
  };
}
