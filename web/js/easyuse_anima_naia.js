import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

const NODE_TYPE = "EasyUseAnimaNAIARandomPrompt";
const PREVIEW_MIN_HEIGHT = 92;
const PREVIEW_BOTTOM_PADDING = 16;
const STORAGE_WIDGETS = [
  "cached_prompt",
  "cached_negative_prompt",
  "cached_width",
  "cached_height",
  "cached_signature",
];
const NAIA_SETTING_WIDGETS = [
  "use_naia_settings",
  "pre_prompt",
  "post_prompt",
  "auto_hide",
  "remove_author",
  "remove_work_title",
  "remove_character_name",
  "remove_character_features",
  "remove_clothes",
  "remove_color",
  "remove_location_and_background_color",
  "remove_expression",
  "remove_pose_action",
  "remove_meta_tags",
  "remove_object_tags",
  "remove_noise_tags",
  "e621_auto_boost",
  "danbooru_auto_weight",
  "tag_implication_compression",
  "host",
  "port",
];

function firstValue(value, fallback = "") {
  if (Array.isArray(value)) {
    return value.length > 0 ? value[0] : fallback;
  }
  return value ?? fallback;
}

function findWidget(node, name) {
  return node.widgets?.find((widget) => widget.name === name);
}

function isWidgetInputLinked(node, name) {
  return !!node.inputs?.some((input) => input.widget?.name === name && input.link != null);
}

function setWidgetValue(node, name, value) {
  if (isWidgetInputLinked(node, name)) {
    return;
  }
  const widget = findWidget(node, name);
  if (!widget) {
    return;
  }
  if (widget.value === value) {
    return;
  }
  widget.value = value;
  widget.callback?.(value);
}

function hideStorageWidgets(node) {
  for (const name of STORAGE_WIDGETS) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    hideWidget(widget);
  }
}

function setWidgetVisible(widget, visible) {
  widget.hidden = !visible;
  if (widget.inputEl) {
    widget.inputEl.style.display = visible ? "" : "none";
  }
}

function hideWidget(widget) {
  widget.hidden = true;
  widget.serialize = true;
  widget.options ||= {};
  widget.options.hidden = true;
  widget.computeSize = () => [0, 0];
  widget.draw = () => {};
  if (widget.inputEl) {
    widget.inputEl.style.display = "none";
    widget.inputEl.style.pointerEvents = "none";
    widget.inputEl.tabIndex = -1;
  }
}

function getPreviewFillHeight(node, widget) {
  const nodeHeight = node.size?.[1] ?? 0;
  const widgetY = Number.isFinite(widget.y) ? widget.y : 0;
  if (!nodeHeight || !widgetY) {
    return widget.__easyuseAnimaPreviewHeight ?? 220;
  }
  return Math.max(PREVIEW_MIN_HEIGHT, Math.floor(nodeHeight - widgetY - PREVIEW_BOTTOM_PADDING));
}

function applyPreviewFillHeight(node) {
  const widget = findWidget(node, "easyuse_anima_preview");
  if (!widget || widget.hidden) {
    return;
  }
  const height = getPreviewFillHeight(node, widget);
  if (widget.__easyuseAnimaPreviewHeight === height) {
    return;
  }
  widget.__easyuseAnimaPreviewHeight = height;
  if (widget.inputEl) {
    widget.inputEl.style.minHeight = `${PREVIEW_MIN_HEIGHT}px`;
    widget.inputEl.style.height = `${height}px`;
  }
}

function refreshNodeSize(node) {
  requestAnimationFrame(() => {
    applyPreviewFillHeight(node);
    const size = node.computeSize();
    const preview = findWidget(node, "easyuse_anima_preview");
    const previewVisible = preview && !preview.hidden;
    const width = Math.max(size[0], node.size?.[0] || size[0]);
    const height = previewVisible ? Math.max(size[1], node.size?.[1] || size[1]) : size[1];
    if (
      Math.abs(width - (node.size?.[0] || 0)) > 1
      || Math.abs(height - (node.size?.[1] || 0)) > 1
    ) {
      node.setSize?.([width, height]);
    }
    applyPreviewFillHeight(node);
    app.graph.setDirtyCanvas(true, false);
  });
}

function hideNaiaSettingsWidgets(node) {
  for (const name of NAIA_SETTING_WIDGETS) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    hideWidget(widget);
  }
  refreshNodeSize(node);
}

function shouldShowPreview(node) {
  const widget = findWidget(node, "show_preview");
  return !widget || widget.value !== false;
}

function cachedPreviewValues(node) {
  return {
    prompt: String(findWidget(node, "cached_prompt")?.value ?? ""),
    negative: String(findWidget(node, "cached_negative_prompt")?.value ?? ""),
    width: Number(findWidget(node, "cached_width")?.value ?? 0),
    height: Number(findWidget(node, "cached_height")?.value ?? 0),
  };
}

function hasCachedPreviewData(node) {
  const cached = cachedPreviewValues(node);
  return !!(cached.prompt || cached.negative || cached.width || cached.height);
}

function setPreviewVisible(node, visible) {
  const widget = findWidget(node, "easyuse_anima_preview");
  if (!widget) {
    return;
  }
  setWidgetVisible(widget, visible);
  refreshNodeSize(node);
}

function updatePreviewVisibility(node) {
  if (!shouldShowPreview(node)) {
    setPreviewVisible(node, false);
    return;
  }

  const preview = findWidget(node, "easyuse_anima_preview");
  if (preview) {
    setPreviewVisible(node, hasCachedPreviewData(node) || !!preview.value);
  } else if (hasCachedPreviewData(node)) {
    updatePreviewFromWidgets(node);
  } else {
    refreshNodeSize(node);
  }
}

function hookShowPreviewWidget(node) {
  const widget = findWidget(node, "show_preview");
  if (!widget || widget.__easyuseAnimaHooked) {
    return;
  }
  const callback = widget.callback;
  widget.callback = function (value) {
    const result = callback?.apply(this, arguments);
    updatePreviewVisibility(node);
    return result;
  };
  widget.__easyuseAnimaHooked = true;
}

function ensurePreviewWidget(node) {
  let widget = findWidget(node, "easyuse_anima_preview");
  if (widget) {
    return widget;
  }
  widget = ComfyWidgets["STRING"](
    node,
    "easyuse_anima_preview",
    ["STRING", { multiline: true }],
    app,
  ).widget;
  widget.serialize = false;
  widget.__easyuseAnimaPreviewHeight = 160;
  widget.computeSize = function (width) {
    return [width, PREVIEW_MIN_HEIGHT];
  };
  widget.inputEl.readOnly = true;
  widget.inputEl.style.opacity = 0.7;
  widget.inputEl.style.fontSize = "0.75rem";
  widget.inputEl.style.minHeight = `${PREVIEW_MIN_HEIGHT}px`;
  widget.inputEl.style.height = "160px";
  widget.inputEl.style.resize = "none";
  return widget;
}

function previewText(status, width, height, prompt, negative) {
  return [
    `status: ${status || "unknown"}`,
    `size: ${width}x${height}`,
    "",
    "[prompt]",
    prompt,
    "",
    "[negative]",
    negative,
  ].join("\n");
}

function updatePreview(node, message) {
  const prompt = String(firstValue(message.prompt));
  const negative = String(firstValue(message.negative_prompt));
  const width = Number(firstValue(message.width, 0));
  const height = Number(firstValue(message.height, 0));
  const status = String(firstValue(message.status, ""));
  const signature = String(firstValue(message.cached_signature, ""));

  if (status !== "disabled") {
    setWidgetValue(node, "cached_prompt", prompt);
    setWidgetValue(node, "cached_negative_prompt", negative);
    setWidgetValue(node, "cached_width", width);
    setWidgetValue(node, "cached_height", height);
    setWidgetValue(node, "cached_signature", signature);
  }

  if (shouldShowPreview(node)) {
    const preview = ensurePreviewWidget(node);
    preview.value = previewText(status, width, height, prompt, negative);
    setPreviewVisible(node, true);
  }

  refreshNodeSize(node);
}

function updatePreviewFromWidgets(node) {
  const { prompt, negative, width, height } = cachedPreviewValues(node);

  if (!prompt && !negative && (!width || !height)) {
    return;
  }

  if (shouldShowPreview(node)) {
    const preview = ensurePreviewWidget(node);
    preview.value = previewText("loaded", width, height, prompt, negative);
    setPreviewVisible(node, true);
  }
}

app.registerExtension({
  name: "easyuse-anima.naia-random-prompt",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== NODE_TYPE) {
      return;
    }

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      hideStorageWidgets(this);
      hookShowPreviewWidget(this);
      hideNaiaSettingsWidgets(this);
      updatePreviewVisibility(this);
      updatePreviewFromWidgets(this);
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      onConfigure?.apply(this, arguments);
      hideStorageWidgets(this);
      hookShowPreviewWidget(this);
      hideNaiaSettingsWidgets(this);
      updatePreviewVisibility(this);
      updatePreviewFromWidgets(this);
    };

    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      updatePreview(this, message);
    };

    const onResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function () {
      const result = onResize?.apply(this, arguments);
      applyPreviewFillHeight(this);
      return result;
    };

    const onDrawForeground = nodeType.prototype.onDrawForeground;
    nodeType.prototype.onDrawForeground = function () {
      const result = onDrawForeground?.apply(this, arguments);
      applyPreviewFillHeight(this);
      return result;
    };
  },
});
