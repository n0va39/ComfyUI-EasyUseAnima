// @ts-check

/**
 * @typedef {object} AioPostprocessSettingsDialogDependencies
 * @property {any} document
 * @property {(title: any, subtitle: any) => {backdrop: any, body: any, actions: any}} createDialog
 * @property {(section: any, label: any, control: any, tooltipKey?: string) => any} field
 * @property {(value: any) => any} checkbox
 * @property {(options: any[], value: any) => any} selectInput
 * @property {(value: any, step?: string) => any} numberInput
 * @property {(value: any) => string} staticText
 * @property {(key: string) => string} text
 * @property {any} defaultGenerationSettings
 * @property {string} generatorSettingsWidget
 * @property {(node: any, name: string) => any} findWidget
 * @property {(node: any) => any} generatorSettings
 * @property {(defaults: any, current: any) => any} mergeDefaults
 * @property {(value: any, fallback: number, min: number, max: number) => number} clampNumber
 * @property {(node: any, widget: any, settings: any) => void} writeSettings
 * @property {(node: any) => void} renderGeneratorPanel
 */

/**
 * Build the Postprocess Settings opener from shared DOM and settings adapters.
 * Extension lifecycle and generator panel ownership remain in the entry module.
 *
 * @param {AioPostprocessSettingsDialogDependencies} dependencies
 * @returns {(node: any) => void}
 */
export function aioCreatePostprocessSettingsDialog(dependencies) {
  const {
    document,
    createDialog,
    field,
    checkbox,
    selectInput,
    numberInput,
    staticText,
    text,
    defaultGenerationSettings,
    generatorSettingsWidget,
    findWidget,
    generatorSettings,
    mergeDefaults,
    clampNumber,
    writeSettings,
    renderGeneratorPanel,
  } = dependencies;

  return function openPostprocessSettings(node) {
    const widget = findWidget(node, generatorSettingsWidget);
    const settings = generatorSettings(node);
    const postprocess = mergeDefaults(defaultGenerationSettings.postprocess, settings.postprocess || {});
    const fit = mergeDefaults(defaultGenerationSettings.postprocess.fit, postprocess.fit || {});
    const { backdrop, body, actions } = createDialog(
      "Postprocess Settings",
      "Final size fit runs after Detailer and Upscale, before Save. Cap by long edge or megapixels.",
    );
    body.classList.add("easyuse-anima-aio-one-column");

    const fitSection = document.createElement("section");
    fitSection.className = "easyuse-anima-aio-section";
    fitSection.append(Object.assign(document.createElement("h3"), { textContent: staticText("Final Size Fit") }));
    const enabled = field(fitSection, "Enable postprocess", checkbox(postprocess.enabled), "tip.postprocessEnabled");
    const fitMode = field(
      fitSection,
      "Fit by",
      selectInput([
        { value: "max_long_edge", label: "Max long edge" },
        { value: "megapixels", label: "Megapixels" },
      ], fit.mode || "max_long_edge"),
      "tip.finalFit",
    );
    const fitMaxLongEdge = field(fitSection, "Max long edge", numberInput(fit.max_long_edge, "64"), "tip.finalFit");
    const fitMaxMegapixels = field(fitSection, "Max megapixels", numberInput(fit.max_megapixels, "0.1"), "tip.finalFit");
    const fitMethod = field(
      fitSection,
      "Fit method",
      selectInput(["bicubic", "lanczos", "area", "bilinear", "nearest-exact"], fit.method || "bicubic"),
      "tip.finalFit",
    );

    const updateVisibility = () => {
      const fitDisplay = enabled.checked ? "" : "none";
      for (const control of [fitMode, fitMethod]) {
        if (control?.parentElement) {
          control.parentElement.style.display = fitDisplay;
        }
      }
      const longEdgeDisplay = enabled.checked && fitMode.value === "max_long_edge" ? "" : "none";
      const megapixelsDisplay = enabled.checked && fitMode.value === "megapixels" ? "" : "none";
      if (fitMaxLongEdge?.parentElement) {
        fitMaxLongEdge.parentElement.style.display = longEdgeDisplay;
      }
      if (fitMaxMegapixels?.parentElement) {
        fitMaxMegapixels.parentElement.style.display = megapixelsDisplay;
      }
    };
    enabled.addEventListener("change", updateVisibility);
    fitMode.addEventListener("change", updateVisibility);
    body.append(fitSection);
    updateVisibility();

    const cancel = document.createElement("button");
    cancel.textContent = text("button.cancel");
    const apply = document.createElement("button");
    apply.className = "primary";
    apply.textContent = text("button.apply");
    actions.append(cancel, apply);
    cancel.addEventListener("click", () => backdrop.remove());
    apply.addEventListener("click", () => {
      const next = mergeDefaults(defaultGenerationSettings, settings);
      next.postprocess = {
        ...postprocess,
        enabled: enabled.checked,
        fit: {
          ...fit,
          mode: fitMode.value || "max_long_edge",
          max_long_edge: Math.trunc(clampNumber(fitMaxLongEdge.value, 2048, 64, 16384)),
          max_megapixels: clampNumber(fitMaxMegapixels.value, 4, 0.1, 256),
          method: fitMethod.value || "bicubic",
        },
      };
      delete next.upscale?.fit;
      writeSettings(node, widget, next);
      renderGeneratorPanel(node);
      backdrop.remove();
    });
  };
}
