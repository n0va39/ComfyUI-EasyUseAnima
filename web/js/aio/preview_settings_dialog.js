// @ts-check

/**
 * @typedef {object} AioPreviewSettingsDialogDependencies
 * @property {any} document
 * @property {(title: any, subtitle: any) => {backdrop: any, body: any, actions: any}} createDialog
 * @property {(section: any, label: any, control: any, tooltipKey?: string) => any} field
 * @property {(value: any) => any} checkbox
 * @property {(value: any, step?: string) => any} numberInput
 * @property {(value: any) => string} staticText
 * @property {(key: string) => string} text
 * @property {any} defaultGenerationSettings
 * @property {string} generatorSettingsWidget
 * @property {(node: any, name: string) => any} findWidget
 * @property {(node: any) => any} generatorSettings
 * @property {(defaults: any, current: any) => any} mergeDefaults
 * @property {(value: any, fallback: number, min: number, max: number) => number} clampNumber
 * @property {(images: any[]) => number} defaultPreviewIndex
 * @property {(node: any, settings: any) => void} applyVisibleSettings
 * @property {(node: any, widget: any, settings: any) => void} writeSettings
 * @property {(node: any) => void} renderGeneratorPanel
 */

/**
 * Build the Preview Settings opener from shared DOM, settings, and preview adapters.
 * Extension lifecycle and generator panel ownership remain in the entry module.
 *
 * @param {AioPreviewSettingsDialogDependencies} dependencies
 * @returns {(node: any) => void}
 */
export function aioCreatePreviewSettingsDialog(dependencies) {
  const {
    document,
    createDialog,
    field,
    checkbox,
    numberInput,
    staticText,
    text,
    defaultGenerationSettings,
    generatorSettingsWidget,
    findWidget,
    generatorSettings,
    mergeDefaults,
    clampNumber,
    defaultPreviewIndex,
    applyVisibleSettings,
    writeSettings,
    renderGeneratorPanel,
  } = dependencies;

  return function openPreviewSettings(node) {
    const widget = findWidget(node, generatorSettingsWidget);
    const settings = generatorSettings(node);
    const preview = mergeDefaults(defaultGenerationSettings.preview, settings.preview || {});
    const { backdrop, body, actions } = createDialog(
      "Preview Options",
      text("text.previewOptionsSubtitle"),
    );
    const section = document.createElement("section");
    section.className = "easyuse-anima-aio-section full";
    section.append(Object.assign(document.createElement("h3"), { textContent: staticText("Node Preview") }));
    const intermediate = field(
      section,
      "Intermediate images",
      checkbox(preview.intermediate_images),
      "tip.previewIntermediate",
    );
    const comparePrevious = field(
      section,
      "Compare previous",
      checkbox(preview.compare_previous),
      "tip.previewComparePrevious",
    );
    const imageFeed = field(
      section,
      "Image feed",
      checkbox(preview.image_feed),
      "tip.previewImageFeed",
    );
    const feedCount = field(
      section,
      "Feed count",
      numberInput(preview.feed_count, "1"),
      "tip.previewFeedCount",
    );
    feedCount.min = "1";
    feedCount.max = "100";
    const syncFeedCount = () => {
      feedCount.disabled = !imageFeed.checked;
    };
    imageFeed.addEventListener("change", syncFeedCount);
    syncFeedCount();
    body.append(section);

    const cancel = document.createElement("button");
    cancel.textContent = text("button.cancel");
    const apply = document.createElement("button");
    apply.className = "primary";
    apply.textContent = text("button.apply");
    actions.append(cancel, apply);
    cancel.addEventListener("click", () => backdrop.remove());
    apply.addEventListener("click", () => {
      const next = mergeDefaults(defaultGenerationSettings, settings);
      next.preview = {
        intermediate_images: intermediate.checked,
        compare_previous: comparePrevious.checked,
        image_feed: imageFeed.checked,
        feed_count: Math.trunc(clampNumber(feedCount.value, preview.feed_count, 1, 100)),
      };
      if (Array.isArray(node.__easyuseAnimaGeneratorPreviewFeedImages)) {
        node.__easyuseAnimaGeneratorPreviewFeedImages = node.__easyuseAnimaGeneratorPreviewFeedImages.slice(
          -next.preview.feed_count,
        );
      }
      node.__easyuseAnimaGeneratorPreviewImages = next.preview.image_feed
        ? (node.__easyuseAnimaGeneratorPreviewFeedImages || [])
        : (node.__easyuseAnimaGeneratorCurrentRunImages || []);
      node.__easyuseAnimaSelectedPreviewIndex = defaultPreviewIndex(node.__easyuseAnimaGeneratorPreviewImages);
      applyVisibleSettings(node, next);
      writeSettings(node, widget, next);
      renderGeneratorPanel(node);
      backdrop.remove();
    });
  };
}
