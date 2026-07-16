// @ts-check

const GENERATOR_DOM_WIDGET = "easyuse_anima_generator_panel";
const GENERATOR_NODE_MIN_WIDTH = 560;
const GENERATOR_NODE_DEFAULT_WIDTH = 620;
const GENERATOR_PANEL_CONTROL_SELECTOR = "input, select, textarea, button";

/**
 * @typedef {object} AioGeneratorPanelControls
 * @property {(value: any, step?: string) => any} numberInput
 * @property {(value: any) => any} checkbox
 * @property {(options: any[], value: any) => any} selectInput
 * @property {(label: any, control: any, className?: string, tooltipKey?: string) => any} createNodeField
 */

/**
 * @typedef {object} AioGeneratorPanelText
 * @property {(key: string) => string} get
 * @property {(key: string, values?: Record<string, any>) => string} format
 * @property {(element: any, key: string) => any} applyTooltip
 */

/**
 * @typedef {object} AioGeneratorPanelSettingsCore
 * @property {any} defaultGenerationSettings
 * @property {number} specialSeedRandom
 * @property {any[]} fallbackSamplerNames
 * @property {any[]} fallbackSchedulerNames
 * @property {(defaults: any, current: any) => any} mergeDefaults
 * @property {(value: any) => string} normalizeSeedControl
 * @property {(value: any, fallback?: number) => number} normalizeSeedValue
 * @property {(value: any, fallback: number, min: number, max: number) => number} clampNumber
 * @property {(usdu: any) => any} normalizeUsduAutoTileRange
 * @property {(settings: any, value: number) => void} setUsduAutoTileTarget
 * @property {(order: any, detailer?: any) => string[]} normalizeDetailerOrder
 * @property {(targetName: string) => any} detailerTargetDefaults
 * @property {(targetName: string, target: any, index?: number) => string} detailerTargetTitle
 */

/**
 * @typedef {object} AioGeneratorPanelNodeAdapter
 * @property {(node: any) => any} getSettings
 * @property {(node: any, settings: any) => void} applyVisibleSettings
 * @property {(node: any, settings: any, markDirty?: boolean) => void} writeSettings
 * @property {(node: any) => void} syncSettingsFromVisible
 * @property {(node: any, name: string, fallback: any) => any} widgetValue
 * @property {(node: any, name: string, fallback: any[]) => any[]} widgetOptions
 * @property {(node: any, name: string, value: any) => void} setWidgetValueIfChanged
 * @property {(node: any, seed: number) => void} commitSeedValue
 * @property {(node: any) => void} markDirty
 * @property {() => void} ensureStyle
 * @property {(node: any, options?: Record<string, any>) => void} suppressDefaultPreview
 * @property {(node: any) => void} markNativePreviewHidden
 * @property {(image: any) => string} imageUrl
 * @property {() => number} randomSeed
 * @property {(event: any) => any} forwardPanelWheel
 */

/**
 * @typedef {object} AioGeneratorPanelProfileAdapter
 * @property {(node: any, settings?: any) => string} syncValue
 * @property {(value: string) => string} displayLabel
 */

/**
 * @typedef {object} AioGeneratorPanelPreviewAdapter
 * @property {(node: any, images: any[]) => any} mainImage
 * @property {(node: any, images: any[]) => number} selectedIndex
 * @property {(image: any) => string} imageLabel
 * @property {(image: any) => string} imageName
 * @property {(image: any) => string} imageResolution
 * @property {(image: any) => string} imageFileSize
 */

/**
 * @typedef {object} AioGeneratorPanelActions
 * @property {(node: any) => void} openProfileSettings
 * @property {(node: any) => void} openSaveSettings
 * @property {(node: any) => void} openSamplerSettings
 * @property {(node: any) => void} openAdvancedSettings
 * @property {(node: any) => void} openHighresSettings
 * @property {(node: any) => void} openDetailerSettings
 * @property {(node: any) => void} openUpscaleSettings
 * @property {(node: any) => void} openPostprocessSettings
 * @property {(node: any) => void} openPreviewSettings
 */

/**
 * @typedef {object} AioGeneratorPanelRuntimeDependencies
 * @property {any} document
 * @property {any} window
 * @property {(callback: (...args: any[]) => any) => any} requestAnimationFrame
 * @property {(frame: any) => void} cancelAnimationFrame
 * @property {number} panelMinHeight
 * @property {AioGeneratorPanelControls} controls
 * @property {AioGeneratorPanelText} text
 * @property {AioGeneratorPanelSettingsCore} settingsCore
 * @property {AioGeneratorPanelNodeAdapter} nodeAdapter
 * @property {AioGeneratorPanelProfileAdapter} profileAdapter
 * @property {AioGeneratorPanelPreviewAdapter} previewAdapter
 * @property {AioGeneratorPanelActions} actions
 */

/**
 * Own the AiO generator panel DOM, render, summary, preview, seed controls, and
 * per-node layout lifecycle. Extension hooks, queue preparation, serialized
 * widget ownership, dialogs, native-preview events, CSS, and the global wheel
 * router remain in the entry module and are supplied as adapters.
 *
 * @param {AioGeneratorPanelRuntimeDependencies} dependencies
 */
export function aioCreateGeneratorPanelRuntime(dependencies) {
  const {
    document,
    window,
    requestAnimationFrame,
    cancelAnimationFrame,
    panelMinHeight: GENERATOR_PANEL_MIN_HEIGHT,
    controls,
    text,
    settingsCore,
    nodeAdapter,
    profileAdapter,
    previewAdapter,
    actions,
  } = dependencies;
  const {
    numberInput,
    checkbox,
    selectInput,
    createNodeField,
  } = controls;
  const {
    get: aioText,
    format: aioFormat,
    applyTooltip,
  } = text;
  const {
    defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,
    specialSeedRandom: GENERATOR_SPECIAL_SEED_RANDOM,
    fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,
    fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,
    mergeDefaults,
    normalizeSeedControl,
    normalizeSeedValue,
    clampNumber: clampGeneratorNumber,
    normalizeUsduAutoTileRange: normalizeGeneratorUsduAutoTileRange,
    setUsduAutoTileTarget: setGeneratorUsduAutoTileTarget,
    normalizeDetailerOrder,
    detailerTargetDefaults,
    detailerTargetTitle,
  } = settingsCore;
  const {
    getSettings: generatorSettings,
    applyVisibleSettings: applyVisibleGeneratorSettings,
    writeSettings: writeGeneratorSettingsFromState,
    syncSettingsFromVisible: syncGeneratorSettingsFromVisible,
    widgetValue,
    widgetOptions,
    setWidgetValueIfChanged,
    commitSeedValue,
    markDirty: markNodeDirty,
    ensureStyle,
    suppressDefaultPreview: suppressGeneratorDefaultPreview,
    markNativePreviewHidden: markGeneratorNativeLivePreviewHidden,
    imageUrl: generatorImageUrl,
    randomSeed,
    forwardPanelWheel: forwardGeneratorPanelWheel,
  } = nodeAdapter;
  const {
    syncValue: syncGeneratorProfileValue,
    displayLabel: generatorProfileDisplayLabel,
  } = profileAdapter;
  const {
    mainImage: aioMainPreviewImage,
    selectedIndex: aioSelectedPreviewIndex,
    imageLabel: aioPreviewImageLabel,
    imageName: aioPreviewImageName,
    imageResolution: aioPreviewResolution,
    imageFileSize: aioPreviewFileSize,
  } = previewAdapter;
  const {
    openProfileSettings: openGeneratorProfileSettings,
    openSaveSettings,
    openSamplerSettings,
    openAdvancedSettings,
    openHighresSettings,
    openDetailerSettings,
    openUpscaleSettings,
    openPostprocessSettings,
    openPreviewSettings,
  } = actions;

  const generatorPanelLifecycleStates = new WeakMap();
  const disposedGeneratorPanelNodes = new WeakSet();

  function createGeneratorPanelLifecycleState() {
    return {
      frames: new Map(),
      sliderDragCleanups: new Set(),
    };
  }

  function activateGeneratorPanel(node) {
    if (!node) {
      return null;
    }
    disposedGeneratorPanelNodes.delete(node);
    if (!generatorPanelLifecycleStates.has(node)) {
      generatorPanelLifecycleStates.set(node, createGeneratorPanelLifecycleState());
    }
    return generatorPanelLifecycleStates.get(node) || null;
  }

  function generatorPanelLifecycleState(node) {
    if (!node || disposedGeneratorPanelNodes.has(node)) {
      return null;
    }
    return generatorPanelLifecycleStates.get(node) || null;
  }

  function isGeneratorPanelLifecycleCurrent(node, state) {
    return (
      !!state
      && !disposedGeneratorPanelNodes.has(node)
      && generatorPanelLifecycleStates.get(node) === state
    );
  }

  function scheduleGeneratorPanelFrame(node, key, callback) {
    const state = generatorPanelLifecycleState(node);
    if (!state) {
      return null;
    }
    const existing = state.frames.get(key);
    if (existing) {
      return existing.frame;
    }
    const pending = { frame: null };
    state.frames.set(key, pending);
    pending.frame = requestAnimationFrame(() => {
      if (state.frames.get(key) !== pending) {
        return;
      }
      state.frames.delete(key);
      if (isGeneratorPanelLifecycleCurrent(node, state)) {
        callback(state);
      }
    });
    return pending.frame;
  }

  function cleanupGeneratorSliderDrags(state) {
    let hasError = false;
    let firstError = null;
    for (const cleanup of [...(state?.sliderDragCleanups || [])]) {
      try {
        cleanup();
      } catch (error) {
        if (!hasError) {
          hasError = true;
          firstError = error;
        }
      }
    }
    state?.sliderDragCleanups?.clear?.();
    if (hasError) {
      throw firstError;
    }
  }

  function disposeGeneratorPanel(node) {
    if (!node || disposedGeneratorPanelNodes.has(node)) {
      return false;
    }
    disposedGeneratorPanelNodes.add(node);
    let hasError = false;
    let firstError = null;
    const cleanup = (callback) => {
      try {
        callback?.();
      } catch (error) {
        if (!hasError) {
          hasError = true;
          firstError = error;
        }
      }
    };
    const state = generatorPanelLifecycleStates.get(node);
    if (state) {
      for (const pending of state.frames.values()) {
        cleanup(() => cancelAnimationFrame(pending.frame));
      }
      state.frames.clear();
      cleanup(() => cleanupGeneratorSliderDrags(state));
    }
    generatorPanelLifecycleStates.delete(node);
    node.__easyuseAnimaGeneratorLayoutScheduled = false;
    const panel = node.__easyuseAnimaGeneratorPanelEl;
    const widget = node.__easyuseAnimaGeneratorPanelWidget;
    cleanup(() => panel?.__easyuseAnimaAioDisposeListeners?.());
    cleanup(() => widget?.onRemove?.());
    cleanup(() => panel?.replaceChildren?.());
    cleanup(() => panel?.remove?.());
    if (widget && Array.isArray(node.widgets)) {
      cleanup(() => {
        const widgetIndex = node.widgets.indexOf(widget);
        if (widgetIndex >= 0) {
          node.widgets.splice(widgetIndex, 1);
        }
      });
    }
    delete node.__easyuseAnimaGeneratorPanelWidget;
    delete node.__easyuseAnimaGeneratorPanelEl;
    if (hasError) {
      throw firstError;
    }
    return true;
  }

  function generatorPanelFocusControls(panel) {
    return Array.from(panel?.querySelectorAll?.(GENERATOR_PANEL_CONTROL_SELECTOR) || []);
  }

  function generatorPanelFocusSignature(element) {
    return {
      tagName: String(element?.tagName || ""),
      type: String(element?.type || ""),
      className: String(element?.className || ""),
    };
  }

  function generatorPanelFocusMatches(element, signature) {
    const next = generatorPanelFocusSignature(element);
    return (
      next.tagName === signature?.tagName
      && next.type === signature?.type
      && next.className === signature?.className
    );
  }

  function captureGeneratorPanelViewState(panel) {
    const settingsScroll = panel?.querySelector?.(".easyuse-anima-aio-node-settings-scroll");
    const previewFeed = panel?.querySelector?.("[data-aio-preview-feed]");
    const controls = generatorPanelFocusControls(panel);
    const activeElement = document?.activeElement;
    const activeIndex = controls.indexOf(activeElement);
    let focus = null;
    if (activeIndex >= 0) {
      focus = {
        key: activeElement.getAttribute?.("data-aio-focus-key") || "",
        index: activeIndex,
        signature: generatorPanelFocusSignature(activeElement),
      };
    }
    return {
      scrollTop: Number(settingsScroll?.scrollTop) || 0,
      scrollLeft: Number(settingsScroll?.scrollLeft) || 0,
      previewFeedScrollLeft: Number(previewFeed?.scrollLeft) || 0,
      focus,
    };
  }

  function restoreGeneratorPanelViewState(panel, viewState) {
    const settingsScroll = panel?.querySelector?.(".easyuse-anima-aio-node-settings-scroll");
    const previewFeed = panel?.querySelector?.("[data-aio-preview-feed]");
    const controls = generatorPanelFocusControls(panel);
    const focus = viewState?.focus;
    let target = null;
    if (focus?.key) {
      target = controls.find(
        (control) => control.getAttribute?.("data-aio-focus-key") === focus.key,
      ) || null;
    } else if (focus && focus.index >= 0) {
      const candidate = controls[focus.index] || null;
      target = generatorPanelFocusMatches(candidate, focus.signature) ? candidate : null;
    }
    if (target && !target.disabled) {
      target.focus?.({ preventScroll: true });
    }
    if (settingsScroll) {
      settingsScroll.scrollTop = Number(viewState?.scrollTop) || 0;
      settingsScroll.scrollLeft = Number(viewState?.scrollLeft) || 0;
    }
    if (previewFeed) {
      previewFeed.scrollLeft = Number(viewState?.previewFeedScrollLeft) || 0;
    }
  }

  function generatorDenoisePreviewLabel(preview) {
    const base = aioText("text.previewDenoise");
    const value = Number(preview?.value);
    const max = Number(preview?.max);
    if (Number.isFinite(value) && Number.isFinite(max) && max > 0) {
      const current = Math.max(0, Math.min(max, Math.round(value)));
      return `${base} · ${current}/${Math.round(max)}`;
    }
    return base;
  }

  function createGeneratorPreviewPlaceholder() {
    const placeholder = document.createElement("div");
    placeholder.className = "easyuse-anima-aio-node-preview-placeholder";
    const title = document.createElement("strong");
    title.textContent = aioText("text.previewTitle");
    const subtitle = document.createElement("span");
    subtitle.textContent = aioText("text.previewSubtitle");
    placeholder.append(title, subtitle);
    return placeholder;
  }

  function stopGeneratorControlPropagation(root) {
    if (!root || root.__easyuseAnimaAioStopPropagation) {
      return;
    }
    const stop = (event) => {
      if (event.target?.closest?.(GENERATOR_PANEL_CONTROL_SELECTOR)) {
        event.stopPropagation();
      }
    };
    const eventNames = [
      "pointerdown",
      "mousedown",
      "pointerup",
      "mouseup",
      "click",
      "dblclick",
      "keydown",
      "keyup",
    ];
    for (const eventName of eventNames) {
      root.addEventListener(eventName, stop);
    }
    // Legacy canvas bubbles DOM-widget wheel events through the panel. Keep this
    // local guard as a fallback; Node 2.0 still needs the window capture router
    // installed below because its Vue ancestor can handle wheel first.
    root.addEventListener("wheel", forwardGeneratorPanelWheel, {
      capture: true,
      passive: false,
    });
    root.__easyuseAnimaAioDisposeListeners = () => {
      for (const eventName of eventNames) {
        root.removeEventListener(eventName, stop);
      }
      root.removeEventListener("wheel", forwardGeneratorPanelWheel, true);
      delete root.__easyuseAnimaAioDisposeListeners;
      delete root.__easyuseAnimaAioStopPropagation;
    };
    root.__easyuseAnimaAioStopPropagation = true;
  }

  function samplerModeLabel(settingsOrBackend) {
    const settings = typeof settingsOrBackend === "object" && settingsOrBackend
      ? settingsOrBackend
      : null;
    const sampler = settings?.sampler || {};
    const backend = String(settings ? sampler.backend : settingsOrBackend || "comfy_ksampler");
    const corrections = !!sampler?.dit_corrections?.enabled;
    const spectrum = !!sampler?.spectrum?.enabled;
    switch (backend) {
      case "spectrum_mod_guidance_advanced":
        return corrections ? "Spectrum Mod Guidance + Corrections" : "Spectrum Mod Guidance";
      case "spectrum_spd_speed":
        return "Spectrum SPD / SPEED";
      case "comfy_ksampler": {
        const extras = [];
        if (spectrum) {
          extras.push("Spectrum Patch");
        }
        if (corrections) {
          extras.push("Corrections");
        }
        return extras.length ? `${extras.join(" + ")} / Comfy KSampler` : "Standard Comfy KSampler";
      }
      default:
        return "Standard Comfy KSampler";
    }
  }

  function generatorPanelWidth(node) {
    return Math.max(240, Math.floor((Number(node?.size?.[0]) || GENERATOR_NODE_DEFAULT_WIDTH) - 20));
  }

  function applyGeneratorLayout(node) {
    if (!generatorPanelLifecycleState(node)) {
      return;
    }
    const panel = node?.__easyuseAnimaGeneratorPanelEl;
    if (!panel) {
      return;
    }
    const width = generatorPanelWidth(node);
    panel.style.width = `${width}px`;
    panel.style.maxWidth = `${width}px`;
    // ComfyUI owns the node and DOM-widget viewport height. AiO owns only child
    // content: the settings column scrolls while the preview stays in that host
    // viewport. Never derive height from node.size or write node.setSize here.
    panel.style.removeProperty("height");
    panel.style.removeProperty("max-height");
    markNodeDirty(node);
  }

  function scheduleGeneratorLayout(node) {
    const state = generatorPanelLifecycleState(node);
    if (!state || !node?.__easyuseAnimaGeneratorPanelEl) {
      return;
    }
    if (state.frames.has("layout")) {
      return state.frames.get("layout")?.frame ?? null;
    }
    node.__easyuseAnimaGeneratorLayoutScheduled = true;
    return scheduleGeneratorPanelFrame(node, "layout", () => {
      node.__easyuseAnimaGeneratorLayoutScheduled = false;
      applyGeneratorLayout(node);
    });
  }

  function updateGeneratorSettings(node, updater, markDirty = true) {
    const settings = generatorSettings(node);
    updater?.(settings);
    settings.sampler.seed_after_generate = normalizeSeedControl(settings.sampler.seed_after_generate);
    applyVisibleGeneratorSettings(node, settings);
    writeGeneratorSettingsFromState(node, settings, markDirty);
    return settings;
  }

  function updateGeneratorDomSummary(node) {
    if (!generatorPanelLifecycleState(node)) {
      return;
    }
    const panel = node?.__easyuseAnimaGeneratorPanelEl;
    if (!panel) {
      return;
    }
    const settings = generatorSettings(node);
    const profileValue = syncGeneratorProfileValue(node, settings);
    const profileButtonEl = panel.querySelector("[data-aio-profile-button]");
    if (profileButtonEl) {
      profileButtonEl.textContent = generatorProfileDisplayLabel(profileValue);
      profileButtonEl.title = aioText("profile.selectTip");
    }
    const backendSummaryEl = panel.querySelector("[data-aio-backend-summary]");
    const saveButtonEl = panel.querySelector("[data-aio-save-button]");
    if (saveButtonEl) {
      saveButtonEl.classList.toggle("active", !!settings.save.enabled);
      saveButtonEl.title = settings.save.enabled ? aioText("button.saveOn") : aioText("button.saveOff");
    }
    if (backendSummaryEl) {
      backendSummaryEl.textContent = samplerModeLabel(settings);
      backendSummaryEl.title = samplerModeLabel(settings);
    }
    updateGeneratorDomPreview(node);
  }

  function scheduleGeneratorSummary(node) {
    if (!node?.__easyuseAnimaGeneratorPanelEl) {
      return null;
    }
    return scheduleGeneratorPanelFrame(node, "summary", () => {
      updateGeneratorDomSummary(node);
    });
  }

  function generatorPreviewFeedSignature(images, settings, selectedIndex, options = {}) {
    return JSON.stringify([
      !!settings.preview.image_feed,
      !!options.showPending,
      selectedIndex,
      images.map((image, index) => [
        index,
        generatorImageUrl(image),
        aioPreviewImageLabel(image),
      ]),
    ]);
  }

  function renderGeneratorPreviewFeed(node, panel, images, settings, selectedIndex, options = {}) {
    const feed = panel?.querySelector?.("[data-aio-preview-feed]");
    if (!feed) {
      return;
    }
    const showPending = !!options.showPending;
    const state = generatorPanelLifecycleState(node);
    const signature = generatorPreviewFeedSignature(
      images,
      settings,
      selectedIndex,
      options,
    );
    if (state?.previewFeedElement === feed && state.previewFeedSignature === signature) {
      return;
    }
    const rememberRenderedFeed = () => {
      if (state) {
        state.previewFeedElement = feed;
        state.previewFeedSignature = signature;
      }
    };
    const hasRenderableImage = images.some((image) => !!generatorImageUrl(image));
    feed.replaceChildren();
    feed.hidden = !settings.preview.image_feed || (!hasRenderableImage && !showPending);
    if (feed.hidden) {
      rememberRenderedFeed();
      return;
    }
    let selectedThumb = null;
    let pendingThumb = null;
    for (const [index, image] of images.entries()) {
      const thumbUrl = generatorImageUrl(image);
      if (!thumbUrl) {
        continue;
      }
      const thumb = document.createElement("button");
      thumb.type = "button";
      thumb.className = "easyuse-anima-aio-node-preview-thumb";
      if (index === selectedIndex) {
        thumb.classList.add("active");
        selectedThumb = thumb;
      }
      thumb.title = aioPreviewImageLabel(image);
      const thumbImage = document.createElement("img");
      thumbImage.src = thumbUrl;
      thumbImage.alt = "";
      thumbImage.loading = "lazy";
      const label = document.createElement("span");
      label.textContent = aioPreviewImageLabel(image);
      thumb.append(thumbImage, label);
      thumb.addEventListener("click", () => {
        node.__easyuseAnimaSelectedPreviewIndex = index;
        updateGeneratorDomPreview(node);
      });
      feed.append(thumb);
    }
    if (showPending) {
      const pendingLabel = aioText("text.previewGenerating");
      pendingThumb = document.createElement("button");
      pendingThumb.type = "button";
      pendingThumb.className = "easyuse-anima-aio-node-preview-thumb pending";
      pendingThumb.disabled = true;
      pendingThumb.title = pendingLabel;
      pendingThumb.setAttribute("aria-label", pendingLabel);
      const label = document.createElement("span");
      label.textContent = pendingLabel;
      pendingThumb.append(label);
      feed.append(pendingThumb);
    }
    (pendingThumb || selectedThumb)?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
    rememberRenderedFeed();
  }

  function updateGeneratorDomPreview(node) {
    const panel = node?.__easyuseAnimaGeneratorPanelEl;
    const previewBox = panel?.querySelector?.("[data-aio-preview-box]");
    if (!previewBox) {
      return;
    }
    const settings = generatorSettings(node);
    const denoisePreview = node.__easyuseAnimaGeneratorDenoisePreview;
    if (denoisePreview?.url) {
      const label = generatorDenoisePreviewLabel(denoisePreview);
      const preview = document.createElement("div");
      preview.className = "easyuse-anima-aio-node-denoise-preview";
      const img = document.createElement("img");
      img.src = denoisePreview.url;
      img.alt = "";
      img.decoding = "async";
      const labelEl = document.createElement("div");
      labelEl.className = "easyuse-anima-aio-node-denoise-preview-label";
      labelEl.textContent = label;
      labelEl.title = label;
      preview.append(img, labelEl);
      previewBox.replaceChildren(preview);
      const feedImages = Array.isArray(node.__easyuseAnimaGeneratorPreviewImages)
        ? node.__easyuseAnimaGeneratorPreviewImages
        : [];
      renderGeneratorPreviewFeed(
        node,
        panel,
        feedImages,
        settings,
        aioSelectedPreviewIndex(node, feedImages),
        { showPending: true },
      );
      const metaEl = panel.querySelector("[data-aio-preview-meta]");
      if (metaEl) {
        metaEl.textContent = "";
        metaEl.title = "";
      }
      return;
    }
    const images = Array.isArray(node.__easyuseAnimaGeneratorPreviewImages)
      ? node.__easyuseAnimaGeneratorPreviewImages
      : [];
    if (!images.length) {
      previewBox.replaceChildren(createGeneratorPreviewPlaceholder());
      const metaEl = panel.querySelector("[data-aio-preview-meta]");
      if (metaEl) {
        metaEl.textContent = "-";
        metaEl.title = "";
      }
      renderGeneratorPreviewFeed(node, panel, images, settings, -1);
      return;
    }
    const selectedIndex = aioSelectedPreviewIndex(node, images);
    const currentImage = aioMainPreviewImage(node, images);
    const imageUrl = generatorImageUrl(currentImage);
    if (!currentImage || !imageUrl) {
      previewBox.replaceChildren(createGeneratorPreviewPlaceholder());
      const metaEl = panel.querySelector("[data-aio-preview-meta]");
      if (metaEl) {
        metaEl.textContent = "-";
        metaEl.title = "";
      }
      renderGeneratorPreviewFeed(node, panel, images, settings, selectedIndex);
      return;
    }
    const metaEl = panel.querySelector("[data-aio-preview-meta]");
    if (metaEl) {
      const parts = [
        aioPreviewImageName(currentImage),
        aioPreviewResolution(currentImage),
        aioPreviewFileSize(currentImage),
      ].filter((part) => part && part !== "-");
      const metaText = parts.length ? parts.join(" · ") : "-";
      metaEl.textContent = metaText;
      metaEl.title = metaText === "-" ? "" : metaText;
    }

    const makeImage = (image) => {
      const img = document.createElement("img");
      img.src = generatorImageUrl(image);
      img.alt = "";
      img.loading = "lazy";
      return img;
    };
    const makeLayer = (className, image) => {
      const pane = document.createElement("div");
      pane.className = `easyuse-anima-aio-node-preview-layer ${className}`.trim();
      pane.append(makeImage(image));
      return pane;
    };
    const makeCompareLabel = (className, label) => {
      const labelEl = document.createElement("div");
      labelEl.className = `easyuse-anima-aio-node-preview-pane-label ${className}`.trim();
      labelEl.textContent = label;
      labelEl.title = label;
      return labelEl;
    };
    const previousImage = selectedIndex > 0 ? images[selectedIndex - 1] : null;
    const canCompare = (
      settings.preview.compare_previous
      && previousImage
      && generatorImageUrl(previousImage)
    );
    if (canCompare) {
      const compare = document.createElement("div");
      compare.className = "easyuse-anima-aio-node-preview-compare";
      compare.style.setProperty("--aio-compare-x", "50%");
      const updateCompareX = (event) => {
        const rect = compare.getBoundingClientRect();
        const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
        const percent = rect.width > 0 ? (x / rect.width) * 100 : 50;
        compare.style.setProperty("--aio-compare-x", `${percent.toFixed(2)}%`);
      };
      for (const eventName of ["pointerdown", "pointermove"]) {
        compare.addEventListener(eventName, (event) => {
          event.stopPropagation();
          updateCompareX(event);
        });
      }
      const labels = document.createElement("div");
      labels.className = "easyuse-anima-aio-node-preview-compare-labels";
      labels.append(
        makeCompareLabel("current", `${aioText("text.previewCurrent")} · ${aioPreviewImageLabel(currentImage)}`),
        makeCompareLabel("previous", `${aioText("text.previewPrevious")} · ${aioPreviewImageLabel(previousImage)}`),
      );
      compare.append(
        makeLayer("before", currentImage),
        makeLayer("after", previousImage),
        Object.assign(document.createElement("div"), { className: "easyuse-anima-aio-node-preview-divider" }),
        labels,
      );
      previewBox.replaceChildren(compare);
    } else {
      previewBox.replaceChildren(makeImage(currentImage));
    }

    renderGeneratorPreviewFeed(node, panel, images, settings, selectedIndex);
  }

  function applyGeneratorControlFocusKey(control, options = {}) {
    if (options.focusKey) {
      control?.setAttribute?.("data-aio-focus-key", String(options.focusKey));
    }
    return control;
  }

  function createDomNumberControl(node, name, value, step = "1") {
    const input = numberInput(value, step);
    input.addEventListener("input", () => {
      const nextValue = name === "seed"
        ? normalizeSeedValue(input.value, GENERATOR_SPECIAL_SEED_RANDOM)
        : Number(input.value || 0);
      setWidgetValueIfChanged(node, name, nextValue);
      syncGeneratorSettingsFromVisible(node);
      updateGeneratorDomSummary(node);
      if (name === "seed") {
        refreshGeneratorSeedButtons(node);
      }
      markNodeDirty(node);
    });
    return input;
  }

  function createDomSliderNumberControl(node, name, value, options = {}) {
    const min = Number(options.min ?? 0);
    const max = Number(options.max ?? 100);
    const step = Number(options.step ?? 1);
    const decimals = Number(options.decimals ?? 0);
    const clamp = (next) => Math.max(min, Math.min(max, Number(next)));
    const snap = (next) => {
      const clamped = clamp(next);
      if (!Number.isFinite(step) || step <= 0) {
        return clamped;
      }
      return min + Math.round((clamped - min) / step) * step;
    };
    const round = (next) => {
      const factor = 10 ** decimals;
      return Math.round(clamp(snap(next)) * factor) / factor;
    };
    const currentValue = round(value);
    const wrapper = document.createElement("div");
    wrapper.className = "easyuse-anima-aio-node-slider-control";
    const input = numberInput(currentValue, String(step));
    input.min = String(min);
    input.max = String(max);
    const track = document.createElement("div");
    track.className = "easyuse-anima-aio-node-slider-track";
    const rail = document.createElement("div");
    rail.className = "easyuse-anima-aio-node-slider-rail";
    const fill = document.createElement("div");
    fill.className = "easyuse-anima-aio-node-slider-fill";
    const thumb = document.createElement("div");
    thumb.className = "easyuse-anima-aio-node-slider-thumb";
    track.append(rail, fill, thumb);

    const normalizeValue = typeof options.normalize === "function"
      ? options.normalize
      : (next) => (name === "steps" ? Math.trunc(next) : next);
    const commit = (nextValue) => {
      const next = round(nextValue);
      input.value = String(next);
      const normalized = normalizeValue(next);
      if (typeof options.onCommit === "function") {
        options.onCommit(normalized);
      } else {
        setWidgetValueIfChanged(node, name, normalized);
        syncGeneratorSettingsFromVisible(node);
      }
      scheduleGeneratorSummary(node);
      updateSlider();
      markNodeDirty(node);
    };
    const updateSlider = () => {
      const next = round(input.value || currentValue);
      const percent = max <= min ? 0 : ((next - min) / (max - min)) * 100;
      const clampedPercent = Math.max(0, Math.min(100, percent));
      fill.style.width = `${clampedPercent}%`;
      thumb.style.left = `${clampedPercent}%`;
    };
    const valueFromPointer = (pointerEvent) => {
      const rect = track.getBoundingClientRect();
      const relative = rect.width > 0 ? (pointerEvent.clientX - rect.left) / rect.width : 0;
      return round(min + Math.max(0, Math.min(1, relative)) * (max - min));
    };

    input.addEventListener("input", () => commit(input.value));
    track.addEventListener("pointerdown", (event) => {
      const state = generatorPanelLifecycleState(node);
      if (!state) {
        return;
      }
      cleanupGeneratorSliderDrags(state);
      event.preventDefault();
      event.stopPropagation();
      const pointerId = event.pointerId;
      track.setPointerCapture?.(pointerId);
      let active = true;
      function cleanup() {
        if (!active) {
          return;
        }
        active = false;
        try {
          track.releasePointerCapture?.(pointerId);
        } catch {
          // Pointer capture may already be released by cancel, blur, or removal.
        }
        window.removeEventListener("pointermove", move, true);
        window.removeEventListener("pointerup", finish, true);
        window.removeEventListener("pointercancel", finish, true);
        window.removeEventListener("blur", finish, true);
        state.sliderDragCleanups.delete(cleanup);
      }
      function move(moveEvent) {
        if (!isGeneratorPanelLifecycleCurrent(node, state)) {
          cleanup();
          return;
        }
        moveEvent.preventDefault();
        moveEvent.stopPropagation();
        commit(valueFromPointer(moveEvent));
      }
      function finish(finishEvent) {
        finishEvent?.stopPropagation?.();
        cleanup();
      }
      state.sliderDragCleanups.add(cleanup);
      window.addEventListener("pointermove", move, true);
      window.addEventListener("pointerup", finish, true);
      window.addEventListener("pointercancel", finish, true);
      window.addEventListener("blur", finish, true);
      commit(valueFromPointer(event));
    });
    wrapper.append(input, track);
    updateSlider();
    return wrapper;
  }

  function createDomSettingsSliderNumberControl(node, value, options, updater) {
    return createDomSliderNumberControl(node, "__settings__", value, {
      ...options,
      onCommit(nextValue) {
        updateGeneratorSettings(node, (settings) => {
          updater?.(settings, nextValue);
        });
      },
    });
  }

  function createDomSettingsCheckboxControl(node, value, updater, options = {}) {
    const input = applyGeneratorControlFocusKey(checkbox(value), options);
    input.addEventListener("change", () => {
      updateGeneratorSettings(node, (settings) => {
        updater?.(settings, input.checked);
      });
      if (options.rerender) {
        renderGeneratorPanel(node);
      } else {
        updateGeneratorDomSummary(node);
        scheduleGeneratorLayout(node);
        markNodeDirty(node);
      }
    });
    return input;
  }

  function createDomSettingsNumberControl(node, value, step, updater, options = {}) {
    const input = applyGeneratorControlFocusKey(numberInput(value, step), options);
    if (options.min != null) {
      input.min = String(options.min);
    }
    if (options.max != null) {
      input.max = String(options.max);
    }
    const decimals = Number(options.decimals ?? 0);
    const commit = () => {
      const fallback = Number(value) || 0;
      const min = Number(options.min ?? -Infinity);
      const max = Number(options.max ?? Infinity);
      const factor = 10 ** decimals;
      const clamped = clampGeneratorNumber(input.value, fallback, min, max);
      const nextValue = decimals > 0 ? Math.round(clamped * factor) / factor : Math.trunc(clamped);
      input.value = nextValue;
      updateGeneratorSettings(node, (settings) => {
        updater?.(settings, nextValue);
      });
      if (options.rerender) {
        renderGeneratorPanel(node);
      } else {
        updateGeneratorDomSummary(node);
        scheduleGeneratorLayout(node);
        markNodeDirty(node);
      }
    };
    input.addEventListener("input", commit);
    return input;
  }

  function createDomSettingsSelectControl(node, value, options, updater, settings = {}) {
    const select = applyGeneratorControlFocusKey(
      selectInput(options, String(value ?? "")),
      settings,
    );
    select.addEventListener("change", () => {
      updateGeneratorSettings(node, (nextSettings) => {
        updater?.(nextSettings, select.value);
      });
      if (settings.rerender) {
        renderGeneratorPanel(node);
      } else {
        updateGeneratorDomSummary(node);
        scheduleGeneratorLayout(node);
        markNodeDirty(node);
      }
    });
    return select;
  }

  function createDomSelectControl(node, name, value, fallbackOptions = []) {
    const select = selectInput(widgetOptions(node, name, fallbackOptions), String(value ?? ""));
    select.addEventListener("change", () => {
      setWidgetValueIfChanged(node, name, select.value);
      syncGeneratorSettingsFromVisible(node);
      updateGeneratorDomSummary(node);
      markNodeDirty(node);
    });
    return select;
  }

  function updateGeneratorSeed(node, value, options = {}) {
    const seed = normalizeSeedValue(value, GENERATOR_SPECIAL_SEED_RANDOM);
    commitSeedValue(node, seed);
    const panel = node?.__easyuseAnimaGeneratorPanelEl;
    const seedInput = panel?.querySelector?.("[data-aio-seed-input]");
    if (seedInput) {
      seedInput.value = seed;
    }
    try {
      updateGeneratorDomSummary(node);
      refreshGeneratorSeedButtons(node);
    } catch {
      // The seed transaction is already committed. A stale/disposed panel must
      // not make the queue wrapper treat that durable state change as failed.
    }
    if (options.markDirty !== false) {
      markNodeDirty(node);
    }
    return seed;
  }

  function setGeneratorSeedFromUi(node, value) {
    return updateGeneratorSeed(node, value);
  }

  function refreshGeneratorSeedButtons(node) {
    if (!generatorPanelLifecycleState(node)) {
      return;
    }
    const panel = node?.__easyuseAnimaGeneratorPanelEl;
    if (!panel) {
      return;
    }
    const lastSeed = node.__easyuseAnimaLastQueuedSeed;
    const currentSeed = normalizeSeedValue(widgetValue(node, "seed", GENERATOR_SPECIAL_SEED_RANDOM));
    const lastButton = panel.querySelector("[data-aio-seed-last]");
    if (lastButton) {
      const hasLastSeed = lastSeed != null;
      lastButton.disabled = !hasLastSeed || Number(lastSeed) === currentSeed;
      lastButton.textContent = hasLastSeed
        ? aioFormat("button.useLast", { seed: lastSeed })
        : aioText("button.useLastNone");
      lastButton.title = aioText("tip.useLast");
    }
  }

  function renderGeneratorPanel(node, expectedLifecycle = null) {
    const lifecycleState = generatorPanelLifecycleState(node);
    if (
      !lifecycleState
      || (expectedLifecycle && lifecycleState !== expectedLifecycle)
    ) {
      return;
    }
    const panel = node?.__easyuseAnimaGeneratorPanelEl;
    if (!panel) {
      return;
    }
    const viewState = captureGeneratorPanelViewState(panel);
    cleanupGeneratorSliderDrags(lifecycleState);
    const settings = generatorSettings(node);
    panel.replaceChildren();

    const makeButton = (label, callback, className = "", tooltipKey = "") => {
      const button = document.createElement("button");
      button.className = `easyuse-anima-aio-node-button ${className}`.trim();
      button.type = "button";
      button.textContent = label;
      applyTooltip(button, tooltipKey);
      button.addEventListener("click", callback);
      return button;
    };
    const makeIconButton = (label, callback, tooltipKey = "") => {
      const button = document.createElement("button");
      button.className = "easyuse-anima-aio-node-icon-button";
      button.type = "button";
      button.textContent = label;
      applyTooltip(button, tooltipKey);
      button.addEventListener("click", callback);
      return button;
    };
    const makeCardHeader = (title, actions = []) => {
      const header = document.createElement("div");
      header.className = "easyuse-anima-aio-node-card-header";
      const titleEl = document.createElement("div");
      titleEl.className = "easyuse-anima-aio-node-card-title";
      titleEl.textContent = title;
      const actionBox = document.createElement("div");
      actionBox.className = "easyuse-anima-aio-node-card-actions";
      actionBox.append(...actions.filter(Boolean));
      header.append(titleEl, actionBox);
      return header;
    };
    const makeStageHeader = (title, toggle, tooltipKey = "", actions = []) => {
      const header = document.createElement("div");
      header.className = "easyuse-anima-aio-node-stage-header";
      const titleEl = document.createElement("div");
      titleEl.className = "easyuse-anima-aio-node-stage-title";
      titleEl.textContent = title;
      applyTooltip(titleEl, tooltipKey);
      const toggleLabel = document.createElement("label");
      toggleLabel.className = "easyuse-anima-aio-node-stage-toggle";
      toggleLabel.append(toggle, document.createTextNode(aioText("label.enabled")));
      applyTooltip(toggleLabel, tooltipKey);
      const actionBox = document.createElement("div");
      actionBox.className = "easyuse-anima-aio-node-stage-tools";
      actionBox.append(...actions.filter(Boolean), toggleLabel);
      header.append(titleEl, actionBox);
      return header;
    };
    const makeNote = (textKey, tooltipKey = "") => {
      const note = document.createElement("div");
      note.className = "easyuse-anima-aio-node-stage-note";
      note.textContent = aioText(textKey);
      applyTooltip(note, tooltipKey);
      return note;
    };
    const moveDetailerTarget = (targetName, delta) => {
      updateGeneratorSettings(node, (nextSettings) => {
        const order = normalizeDetailerOrder(nextSettings.detailer?.order, nextSettings.detailer);
        const currentIndex = order.indexOf(targetName);
        const nextIndex = currentIndex + delta;
        if (currentIndex < 0 || nextIndex < 0 || nextIndex >= order.length) {
          return;
        }
        [order[currentIndex], order[nextIndex]] = [order[nextIndex], order[currentIndex]];
        nextSettings.detailer ||= {};
        nextSettings.detailer.order = order;
      });
      renderGeneratorPanel(node);
    };

    const main = document.createElement("div");
    main.className = "easyuse-anima-aio-node-main";

    const samplerCard = document.createElement("section");
    samplerCard.className = "easyuse-anima-aio-node-card easyuse-anima-aio-node-settings";
    const profileValue = syncGeneratorProfileValue(node, settings);
    const profileButton = makeButton(
      generatorProfileDisplayLabel(profileValue),
      () => openGeneratorProfileSettings(node),
      "easyuse-anima-aio-node-profile-button",
      "profile.selectTip",
    );
    profileButton.setAttribute("data-aio-profile-button", "");
    const saveIcon = makeIconButton("💾", () => openSaveSettings(node), "tip.saveOptions");
    saveIcon.setAttribute("data-aio-save-button", "");
    const samplerHeader = makeCardHeader(aioText("title.sampler"), [
      profileButton,
      makeIconButton("⚙", () => openSamplerSettings(node), "tip.samplerDetails"),
      makeIconButton("⋯", () => openAdvancedSettings(node), "tip.advancedOptions"),
      saveIcon,
    ]);
    const settingsScroll = document.createElement("div");
    settingsScroll.className = "easyuse-anima-aio-node-settings-scroll";

    const samplerGrid = document.createElement("div");
    samplerGrid.className = "easyuse-anima-aio-node-sampler-grid";

    const seedBlock = document.createElement("div");
    const seedInput = createDomNumberControl(node, "seed", settings.sampler.seed);
    seedInput.setAttribute("data-aio-seed-input", "");
    seedInput.setAttribute("data-aio-focus-key", "sampler.seed");
    applyTooltip(seedInput, "tip.seed");
    const seedActions = document.createElement("div");
    seedActions.className = "easyuse-anima-aio-node-seed-actions";
    const seedRandomEach = makeButton(
      aioText("button.randomEach"),
      () => setGeneratorSeedFromUi(node, GENERATOR_SPECIAL_SEED_RANDOM),
      "",
      "tip.randomEach",
    );
    const seedNewFixed = makeButton(
      aioText("button.newFixed"),
      () => setGeneratorSeedFromUi(node, randomSeed()),
      "",
      "tip.newFixed",
    );
    const seedLast = makeButton(
      aioText("button.useLastNone"),
      () => {
        if (node.__easyuseAnimaLastQueuedSeed == null) {
          return;
        }
        setGeneratorSeedFromUi(node, node.__easyuseAnimaLastQueuedSeed);
      },
      "",
      "tip.useLast",
    );
    seedLast.setAttribute("data-aio-seed-last", "");
    seedActions.append(seedRandomEach, seedNewFixed, seedLast);
    seedBlock.append(seedInput, seedActions);

    const modeBadge = Object.assign(document.createElement("div"), {
      className: "easyuse-anima-aio-node-mode-badge",
    });
    modeBadge.setAttribute("data-aio-backend-summary", "");
    samplerGrid.append(
      createNodeField(aioText("label.mode"), modeBadge, "wide", "tip.mode"),
      createNodeField(aioText("label.seed"), seedBlock, "seed", "tip.seed"),
      createNodeField(
        aioText("label.steps"),
        createDomSliderNumberControl(node, "steps", settings.sampler.steps, {
          min: 1,
          max: 75,
          step: 1,
          decimals: 0,
        }),
        "wide",
        "tip.steps",
      ),
      createNodeField(
        aioText("label.cfg"),
        createDomSliderNumberControl(node, "cfg", settings.sampler.cfg, {
          min: 1,
          max: 10,
          step: 0.1,
          decimals: 1,
        }),
        "wide",
        "tip.cfg",
      ),
      createNodeField(
        aioText("label.shift"),
        createDomSettingsSliderNumberControl(
          node,
          settings.model_patches.aura_flow.shift ?? DEFAULT_GENERATION_SETTINGS.model_patches.aura_flow.shift,
          {
            min: 1,
            max: 10,
            step: 0.5,
            decimals: 1,
          },
          (nextSettings, value) => {
            nextSettings.model_patches.aura_flow ||= {};
            delete nextSettings.model_patches.aura_flow.enabled;
            nextSettings.model_patches.aura_flow.shift = value;
          },
        ),
        "wide",
        "tip.shift",
      ),
      createNodeField(
        aioText("label.denoise"),
        createDomNumberControl(node, "denoise", settings.sampler.denoise, "0.01"),
        "",
        "tip.denoise",
      ),
      createNodeField(
        aioText("label.sampler"),
        createDomSelectControl(node, "sampler_name", settings.sampler.sampler_name, GENERATOR_FALLBACK_SAMPLER_NAMES),
        "wide",
        "tip.sampler",
      ),
      createNodeField(
        aioText("label.scheduler"),
        createDomSelectControl(node, "scheduler", settings.sampler.scheduler, GENERATOR_FALLBACK_SCHEDULER_NAMES),
        "wide",
        "tip.scheduler",
      ),
    );

    const highresBlock = document.createElement("div");
    highresBlock.className = "easyuse-anima-aio-node-stage-block";
    const highresEnabled = createDomSettingsCheckboxControl(
      node,
      settings.highres.enabled,
      (nextSettings, value) => {
        nextSettings.highres ||= {};
        nextSettings.highres.enabled = value;
      },
      { rerender: true, focusKey: "highres.enabled" },
    );
    highresBlock.append(makeStageHeader(
      aioText("title.highres"),
      highresEnabled,
      "tip.highresEnabled",
      [makeIconButton("⚙", () => openHighresSettings(node), "tip.highresSettings")],
    ));
    const highresBody = document.createElement("div");
    highresBody.className = "easyuse-anima-aio-node-stage-body";
    if (settings.highres.enabled) {
      const mainBackendIsSpd = settings.sampler.backend === "spectrum_spd_speed";
      const highresFollowsMain = !!settings.highres.inherit_sampler_settings;
      const followMain = createDomSettingsCheckboxControl(
        node,
        highresFollowsMain,
        (nextSettings, value) => {
          nextSettings.highres ||= {};
          nextSettings.highres.inherit_sampler_settings = value;
        },
        { rerender: true, focusKey: "highres.inherit-sampler-settings" },
      );
      const stageMode = Object.assign(document.createElement("div"), {
        className: "easyuse-anima-aio-node-mode-badge",
        textContent: samplerModeLabel({
          sampler: {
            backend: settings.highres.backend || "comfy_ksampler",
            spectrum: settings.highres.spectrum || {},
            dit_corrections: settings.highres.dit_corrections || {},
          },
        }),
      });
      const noteKey = mainBackendIsSpd && highresFollowsMain
        ? "text.highresSpdManualRequired"
        : (highresFollowsMain ? "text.inheritsMainSampler" : "text.usesStageSamplerOverride");
      highresBody.append(
        createNodeField(aioText("label.followMainSampler"), followMain, "wide", "tip.highresFollow"),
        makeNote(noteKey, "tip.highresFollow"),
        ...(highresFollowsMain ? [] : [
          createNodeField(aioText("label.mode"), stageMode, "wide", "tip.highresBackend"),
        ]),
        createNodeField(
          aioText("label.scaleBy"),
          createDomSettingsSliderNumberControl(
            node,
            settings.highres.scale_by,
            { min: 1, max: 4, step: 0.05, decimals: 2 },
            (nextSettings, value) => {
              nextSettings.highres ||= {};
              nextSettings.highres.scale_by = value;
            },
          ),
          "wide",
          "tip.highresScale",
        ),
        createNodeField(
          aioText("label.steps"),
          createDomSettingsSliderNumberControl(
            node,
            settings.highres.steps,
            { min: 1, max: 75, step: 1, decimals: 0 },
            (nextSettings, value) => {
              nextSettings.highres ||= {};
              nextSettings.highres.steps = Math.trunc(value);
            },
          ),
          "wide",
          "tip.highresSteps",
        ),
        createNodeField(
          aioText("label.denoise"),
          createDomSettingsSliderNumberControl(
            node,
            settings.highres.denoise,
            { min: 0, max: 1, step: 0.01, decimals: 2 },
            (nextSettings, value) => {
              nextSettings.highres ||= {};
              nextSettings.highres.denoise = value;
            },
          ),
          "wide",
          "tip.highresDenoise",
        ),
        createNodeField(
          aioText("label.maxLongEdge"),
          createDomSettingsNumberControl(
            node,
            settings.highres.max_long_edge,
            "32",
            (nextSettings, value) => {
              nextSettings.highres ||= {};
              nextSettings.highres.max_long_edge = Math.trunc(value);
            },
            { min: 0, max: 16384, decimals: 0 },
          ),
          "wide",
          "tip.highresMaxEdge",
        ),
      );
    } else {
      highresBody.append(makeNote("text.highresDisabled", "tip.highresEnabled"));
    }
    highresBlock.append(highresBody);

    const detailerBlock = document.createElement("div");
    detailerBlock.className = "easyuse-anima-aio-node-stage-block";
    const detailerEnabled = createDomSettingsCheckboxControl(
      node,
      settings.detailer.enabled,
      (nextSettings, value) => {
        nextSettings.detailer ||= {};
        nextSettings.detailer.enabled = value;
      },
      { rerender: true, focusKey: "detailer.enabled" },
    );
    detailerBlock.append(makeStageHeader(
      aioText("title.detailer"),
      detailerEnabled,
      "tip.detailerEnabled",
      [makeIconButton("⚙", () => openDetailerSettings(node), "tip.detailerSettings")],
    ));
    const detailerBody = document.createElement("div");
    detailerBody.className = "easyuse-anima-aio-node-stage-body";
    if (settings.detailer.enabled) {
      const order = normalizeDetailerOrder(settings.detailer.order, settings.detailer);
      for (const [index, targetName] of order.entries()) {
        const defaults = detailerTargetDefaults(targetName);
        const target = mergeDefaults(defaults, settings.detailer[targetName] || {});
        const targetBlock = document.createElement("div");
        targetBlock.className = "easyuse-anima-aio-node-stage-mini";
        applyTooltip(targetBlock, "tip.detailerBlock");
        const targetHeader = document.createElement("div");
        targetHeader.className = "easyuse-anima-aio-node-stage-mini-header";
        const targetTitle = document.createElement("div");
        targetTitle.className = "easyuse-anima-aio-node-stage-mini-title";
        targetTitle.textContent = `${index + 1}. ${detailerTargetTitle(targetName, target, index)}`;
        applyTooltip(targetTitle, "tip.detailerBlock");
        const targetTools = document.createElement("div");
        targetTools.className = "easyuse-anima-aio-node-stage-tools";
        const moveUp = makeIconButton("↑", () => moveDetailerTarget(targetName, -1), "tip.detailerOrder");
        const moveDown = makeIconButton("↓", () => moveDetailerTarget(targetName, 1), "tip.detailerOrder");
        moveUp.setAttribute("data-aio-focus-key", `detailer.${targetName}.move-up`);
        moveDown.setAttribute("data-aio-focus-key", `detailer.${targetName}.move-down`);
        moveUp.disabled = index === 0;
        moveDown.disabled = index === order.length - 1;
        targetTools.append(moveUp, moveDown);
        targetHeader.append(targetTitle, targetTools);
        targetBlock.append(targetHeader);

        const targetGrid = document.createElement("div");
        targetGrid.className = "easyuse-anima-aio-node-stage-body";
        const targetEnabled = createDomSettingsCheckboxControl(
          node,
          target.enabled,
          (nextSettings, value) => {
            nextSettings.detailer ||= {};
            nextSettings.detailer[targetName] ||= {};
            nextSettings.detailer[targetName].enabled = value;
          },
          { rerender: true, focusKey: `detailer.${targetName}.enabled` },
        );
        targetGrid.append(createNodeField(aioText("label.enabled"), targetEnabled, "wide", "tip.detailerBlock"));
        if (target.enabled) {
          const followMain = createDomSettingsCheckboxControl(
            node,
            target.inherit_sampler_settings,
            (nextSettings, value) => {
              nextSettings.detailer ||= {};
              nextSettings.detailer[targetName] ||= {};
              nextSettings.detailer[targetName].inherit_sampler_settings = value;
            },
            { rerender: true, focusKey: `detailer.${targetName}.inherit-sampler-settings` },
          );
          targetGrid.append(
            createNodeField(aioText("label.followMainSampler"), followMain, "wide", "tip.detailerFollow"),
            makeNote(
              target.inherit_sampler_settings ? "text.inheritsMainSampler" : "text.usesStageSamplerOverride",
              "tip.detailerFollow",
            ),
            createNodeField(
              aioText("label.steps"),
              createDomSettingsSliderNumberControl(
                node,
                target.steps,
                { min: 1, max: 75, step: 1, decimals: 0 },
                (nextSettings, value) => {
                  nextSettings.detailer ||= {};
                  nextSettings.detailer[targetName] ||= {};
                  nextSettings.detailer[targetName].steps = Math.trunc(value);
                },
              ),
              "wide",
              "tip.detailerSteps",
            ),
            createNodeField(
              aioText("label.denoise"),
              createDomSettingsSliderNumberControl(
                node,
                target.denoise,
                { min: 0, max: 1, step: 0.01, decimals: 2 },
                (nextSettings, value) => {
                  nextSettings.detailer ||= {};
                  nextSettings.detailer[targetName] ||= {};
                  nextSettings.detailer[targetName].denoise = value;
                },
              ),
              "wide",
              "tip.detailerDenoise",
            ),
          );
        }
        targetBlock.append(targetGrid);
        detailerBody.append(targetBlock);
      }
    } else {
      detailerBody.append(makeNote("text.detailerDisabled", "tip.detailerEnabled"));
    }
    detailerBlock.append(detailerBody);

    const upscaleBlock = document.createElement("div");
    upscaleBlock.className = "easyuse-anima-aio-node-stage-block";
    const upscaleEnabled = createDomSettingsCheckboxControl(
      node,
      settings.upscale.enabled,
      (nextSettings, value) => {
        nextSettings.upscale ||= {};
        nextSettings.upscale.enabled = value;
      },
      { rerender: true, focusKey: "upscale.enabled" },
    );
    upscaleBlock.append(makeStageHeader(
      aioText("title.upscale"),
      upscaleEnabled,
      "tip.upscaleEnabled",
      [makeIconButton("⚙", () => openUpscaleSettings(node), "tip.upscaleSettings")],
    ));
    const upscaleBody = document.createElement("div");
    upscaleBody.className = "easyuse-anima-aio-node-stage-body";
    if (settings.upscale.enabled) {
      const backend = createDomSettingsSelectControl(
        node,
        settings.upscale.backend || "usdu",
        ["usdu", "resshift"],
        (nextSettings, value) => {
          nextSettings.upscale ||= {};
          nextSettings.upscale.backend = value || "usdu";
        },
        { rerender: true, focusKey: "upscale.backend" },
      );
      upscaleBody.append(
        createNodeField(aioText("label.mode"), backend, "wide", "tip.upscaleBackend"),
      );
      if (settings.upscale.backend === "usdu") {
        const usdu = normalizeGeneratorUsduAutoTileRange(
          mergeDefaults(DEFAULT_GENERATION_SETTINGS.upscale.usdu, settings.upscale.usdu || {}),
        );
        upscaleBody.append(
          createNodeField(
            aioText("label.scaleBy"),
            createDomSettingsSliderNumberControl(
              node,
              settings.upscale.scale_by,
              { min: 1, max: 4, step: 0.05, decimals: 2 },
              (nextSettings, value) => {
                nextSettings.upscale ||= {};
                nextSettings.upscale.scale_by = value;
              },
            ),
            "wide",
            "tip.upscaleScale",
          ),
          createNodeField(
            aioText("label.steps"),
            createDomSettingsSliderNumberControl(
              node,
              settings.upscale.steps,
              { min: 1, max: 75, step: 1, decimals: 0 },
              (nextSettings, value) => {
                nextSettings.upscale ||= {};
                nextSettings.upscale.steps = Math.trunc(value);
              },
            ),
            "wide",
            "tip.steps",
          ),
          createNodeField(
            aioText("label.denoise"),
            createDomSettingsSliderNumberControl(
              node,
              settings.upscale.denoise,
              { min: 0, max: 1, step: 0.01, decimals: 2 },
              (nextSettings, value) => {
                nextSettings.upscale ||= {};
                nextSettings.upscale.denoise = value;
              },
            ),
            "wide",
            "tip.denoise",
          ),
          createNodeField(
            aioText("field.autoTileSize"),
            createDomSettingsCheckboxControl(
              node,
              usdu.auto_tile_size,
              (nextSettings, value) => {
                nextSettings.upscale ||= {};
                nextSettings.upscale.usdu ||= {};
                nextSettings.upscale.usdu.auto_tile_size = value;
              },
              { rerender: true, focusKey: "upscale.usdu.auto-tile-size" },
            ),
            "wide",
            "tip.usduAutoTile",
          ),
        );
        if (usdu.auto_tile_size) {
          upscaleBody.append(
            createNodeField(
              aioText("field.autoTileTarget"),
              createDomSettingsSliderNumberControl(
                node,
                usdu.auto_tile_target,
                { min: 256, max: 2048, step: 64, decimals: 0 },
                (nextSettings, value) => {
                  setGeneratorUsduAutoTileTarget(nextSettings, value);
                },
              ),
              "wide",
              "tip.usduAutoTile",
            ),
          );
        }
        upscaleBody.append(
          makeNote(
            usdu.auto_tile_size ? "text.usduAutoTile" : "text.usduManualTile",
            usdu.auto_tile_size ? "tip.usduAutoTile" : "tip.usduTile",
          ),
        );
      } else {
        upscaleBody.append(makeNote(`ResShift ${settings.upscale.resshift?.scale || "x2"}`, "tip.resshiftScale"));
      }
    } else {
      upscaleBody.append(makeNote("text.upscaleDisabled", "tip.upscaleEnabled"));
    }
    upscaleBlock.append(upscaleBody);

    const postprocess = mergeDefaults(DEFAULT_GENERATION_SETTINGS.postprocess, settings.postprocess || {});
    const postprocessBlock = document.createElement("div");
    postprocessBlock.className = "easyuse-anima-aio-node-stage-block";
    const postprocessEnabled = createDomSettingsCheckboxControl(
      node,
      postprocess.enabled,
      (nextSettings, value) => {
        nextSettings.postprocess ||= {};
        nextSettings.postprocess.enabled = value;
      },
      { rerender: true, focusKey: "postprocess.enabled" },
    );
    postprocessBlock.append(makeStageHeader(
      aioText("title.postprocess"),
      postprocessEnabled,
      "tip.postprocessEnabled",
      [makeIconButton("⚙", () => openPostprocessSettings(node), "tip.postprocessSettings")],
    ));
    const postprocessBody = document.createElement("div");
    postprocessBody.className = "easyuse-anima-aio-node-stage-body";
    if (postprocess.enabled) {
      const fit = mergeDefaults(DEFAULT_GENERATION_SETTINGS.postprocess.fit, postprocess.fit || {});
      const fitText = fit.mode === "megapixels"
        ? `Fit <= ${fit.max_megapixels || 4}MP`
        : `Fit <= ${fit.max_long_edge || 2048}px`;
      postprocessBody.append(makeNote(fitText, "tip.finalFit"));
    } else {
      postprocessBody.append(makeNote("text.postprocessDisabled", "tip.postprocessEnabled"));
    }
    postprocessBlock.append(postprocessBody);

    settingsScroll.append(samplerGrid, highresBlock, detailerBlock, upscaleBlock, postprocessBlock);

    samplerCard.append(samplerHeader, settingsScroll);

    const previewCard = document.createElement("section");
    previewCard.className = "easyuse-anima-aio-node-card easyuse-anima-aio-node-preview";
    const previewHeader = makeCardHeader(aioText("title.preview"), [
      makeIconButton("⚙", () => openPreviewSettings(node), "tip.previewOptions"),
    ]);
    const previewBox = document.createElement("div");
    previewBox.className = "easyuse-anima-aio-node-preview-box";
    previewBox.setAttribute("data-aio-preview-box", "");
    previewBox.append(createGeneratorPreviewPlaceholder());

    const previewMeta = document.createElement("div");
    previewMeta.className = "easyuse-anima-aio-node-preview-meta";
    previewMeta.setAttribute("data-aio-preview-meta", "");
    previewMeta.textContent = "-";
    applyTooltip(previewMeta, "tip.size");

    const previewFeed = document.createElement("div");
    previewFeed.className = "easyuse-anima-aio-node-preview-feed";
    previewFeed.setAttribute("data-aio-preview-feed", "");
    previewFeed.hidden = true;

    previewCard.append(previewHeader, previewBox, previewMeta, previewFeed);

    main.append(samplerCard, previewCard);
    panel.append(main);
    stopGeneratorControlPropagation(panel);
    updateGeneratorDomSummary(node);
    refreshGeneratorSeedButtons(node);
    scheduleGeneratorLayout(node);
    restoreGeneratorPanelViewState(panel, viewState);
  }

  function ensureGeneratorPanel(node) {
    const lifecycleState = activateGeneratorPanel(node);
    if (!lifecycleState) {
      return;
    }
    ensureStyle();
    node.serialize_widgets = true;
    suppressGeneratorDefaultPreview(node, { markDirty: false });
    node.minWidth = Math.max(Number(node.minWidth) || 0, GENERATOR_NODE_MIN_WIDTH);
    if (Array.isArray(node.size)) {
      node.size[0] = Math.max(Number(node.size[0]) || 0, GENERATOR_NODE_DEFAULT_WIDTH);
    }
    if (!node.__easyuseAnimaGeneratorPanelEl) {
      const panel = document.createElement("div");
      panel.className = "easyuse-anima-aio-node-panel";
      node.__easyuseAnimaGeneratorPanelEl = panel;
      const widget = node.addDOMWidget?.(GENERATOR_DOM_WIDGET, "EasyUseAnimaGeneratorPanel", panel, {
        serialize: false,
        hideOnZoom: false,
        getMinHeight: () => GENERATOR_PANEL_MIN_HEIGHT,
      });
      if (widget) {
        node.__easyuseAnimaGeneratorPanelWidget = widget;
      }
    }
    markGeneratorNativeLivePreviewHidden(node);
    renderGeneratorPanel(node, lifecycleState);
    markGeneratorNativeLivePreviewHidden(node);
  }

  return {
    activatePanel: activateGeneratorPanel,
    disposePanel: disposeGeneratorPanel,
    ensurePanel: ensureGeneratorPanel,
    renderPanel: renderGeneratorPanel,
    scheduleSummary: scheduleGeneratorSummary,
    updateSummary: updateGeneratorDomSummary,
    scheduleLayout: scheduleGeneratorLayout,
    refreshSeedButtons: refreshGeneratorSeedButtons,
    updateSeed: updateGeneratorSeed,
  };
}
