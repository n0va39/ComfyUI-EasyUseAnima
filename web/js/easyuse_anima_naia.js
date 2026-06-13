import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

const NODE_TYPE = "EasyUseAnimaNAIARandomPrompt";
const STORAGE_WIDGETS = [
  "cached_prompt",
  "cached_negative_prompt",
  "cached_width",
  "cached_height",
  "cached_signature",
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
  widget.value = value;
  widget.callback?.(value);
}

function hideStorageWidgets(node) {
  for (const name of STORAGE_WIDGETS) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    widget.hidden = true;
    if (widget.inputEl) {
      widget.inputEl.style.display = "none";
    }
  }
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
  widget.inputEl.readOnly = true;
  widget.inputEl.style.opacity = 0.7;
  widget.inputEl.style.fontSize = "0.75rem";
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

  const preview = ensurePreviewWidget(node);
  preview.value = previewText(status, width, height, prompt, negative);

  requestAnimationFrame(() => {
    const size = node.computeSize();
    node.onResize?.([Math.max(size[0], node.size[0]), Math.max(size[1], node.size[1])]);
    app.graph.setDirtyCanvas(true, false);
  });
}

function updatePreviewFromWidgets(node) {
  const prompt = String(findWidget(node, "cached_prompt")?.value ?? "");
  const negative = String(findWidget(node, "cached_negative_prompt")?.value ?? "");
  const width = Number(findWidget(node, "cached_width")?.value ?? 0);
  const height = Number(findWidget(node, "cached_height")?.value ?? 0);

  if (!prompt && !negative && (!width || !height)) {
    return;
  }

  const preview = ensurePreviewWidget(node);
  preview.value = previewText("loaded", width, height, prompt, negative);
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
      ensurePreviewWidget(this);
      updatePreviewFromWidgets(this);
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      onConfigure?.apply(this, arguments);
      hideStorageWidgets(this);
      updatePreviewFromWidgets(this);
    };

    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      updatePreview(this, message);
    };
  },
});
