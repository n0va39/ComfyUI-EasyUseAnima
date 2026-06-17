import { app } from "../../../scripts/app.js";

const NODE_TYPE = "EasyUseAnimaPromptStudio";
const FIELD_NAMES = [
  "lora_trigger_tags",
  "quality_tags",
  "trigger_and_artist_tags",
  "prompt",
  "trailing_quality_tags",
];

const FIELD_HEIGHTS = {
  lora_trigger_tags: 42,
  quality_tags: 72,
  trigger_and_artist_tags: 72,
  prompt: 150,
  trailing_quality_tags: 72,
};

const SECTION_STYLES = {
  count: { label: "인원수", color: "#60a5fa", background: "rgba(37, 99, 235, 0.18)", weight: 700 },
  character: { label: "캐릭터", color: "#f472b6", background: "rgba(219, 39, 119, 0.18)", weight: 700 },
  artist: { label: "@작가", color: "#a78bfa", background: "rgba(124, 58, 237, 0.18)", weight: 700 },
  copyright: { label: "작품", color: "#fb923c", background: "rgba(234, 88, 12, 0.18)", weight: 700 },
  meta: { label: "메타", color: "#94a3b8", background: "rgba(100, 116, 139, 0.18)", weight: 600 },
  general: { label: "학습 태그", color: "#4ade80", background: "rgba(22, 163, 74, 0.16)", weight: 600 },
  natural: { label: "자연어", color: "#cbd5e1", background: "rgba(71, 85, 105, 0.16)", weight: 400 },
  unknown: { label: "미확인", color: "#cbd5e1", background: "transparent", weight: 400 },
};

const LEGEND_ITEMS = ["count", "character", "artist", "copyright", "general", "meta", "natural", "unknown"];
const LEGEND_HEIGHT = 45;
const LEGEND_ROW_HEIGHT = 14;

const WEIGHTED_TOKEN_RE = /^\((.*):[-+]?\d+(?:\.\d+)?\)$/s;
const INLINE_SPACE_RE = /[ \t]+/g;

function findWidget(node, name) {
  return node.widgets?.find((widget) => widget.name === name);
}

function firstValue(value, fallback = null) {
  if (Array.isArray(value)) {
    return value.length ? value[0] : fallback;
  }
  return value ?? fallback;
}

function isWidgetInputLinked(node, name) {
  return !!node.inputs?.some((input) => input.widget?.name === name && input.link != null);
}

function ensureHighlightStyle() {
  if (document.getElementById("easyuse-anima-highlight-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-highlight-style";
  style.textContent = `
    .easyuse-anima-highlight-input {
      color: transparent !important;
      -webkit-text-fill-color: transparent !important;
      caret-color: var(--input-text, #ddd) !important;
      background: transparent !important;
    }
    .easyuse-anima-highlight-input::selection {
      color: transparent !important;
      -webkit-text-fill-color: transparent !important;
      background: rgba(37, 99, 235, 0.28) !important;
    }
  `;
  document.head.append(style);
}

function refreshNodeSize(node) {
  requestAnimationFrame(() => {
    const size = node.computeSize();
    const width = Math.max(size[0], node.size?.[0] || size[0]);
    const height = Math.max(size[1], 80);
    if (
      Math.abs(width - (node.size?.[0] || 0)) > 1
      || Math.abs(height - (node.size?.[1] || 0)) > 1
    ) {
      node.setSize?.([width, height]);
    }
    app.graph.setDirtyCanvas(true, true);
  });
}

function debounce(fn, delay = 180) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

async function classifyPrompt(text) {
  const response = await fetch("/easyuse_anima/classify_prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, limit: 240 }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  return Array.isArray(data.tokens) ? data.tokens : [];
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function normalize(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .replaceAll("_", " ")
    .toLocaleLowerCase()
    .replace(INLINE_SPACE_RE, " ")
    .trim();
}

function tokenBase(token) {
  const value = String(token ?? "").trim();
  const weighted = WEIGHTED_TOKEN_RE.exec(value);
  if (weighted) {
    return weighted[1].trim().replace(/^@/, "");
  }
  if (value.startsWith("@")) {
    return value.slice(1).trim();
  }
  return value;
}

function splitPromptText(text) {
  const parts = [];
  let start = 0;
  let depth = 0;
  let escaped = false;
  const value = String(text ?? "");

  for (let index = 0; index < value.length; index += 1) {
    const char = value[index];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
      continue;
    }
    if (char === "(") {
      depth += 1;
      continue;
    }
    if (char === ")" && depth > 0) {
      depth -= 1;
      continue;
    }
    if ((char === "," || char === "\n") && depth === 0) {
      if (index > start) {
        parts.push({ text: value.slice(start, index), delimiter: false });
      }
      parts.push({ text: char, delimiter: true });
      start = index + 1;
    }
  }

  if (start < value.length) {
    parts.push({ text: value.slice(start), delimiter: false });
  }
  return parts;
}

function tokenStyle(token) {
  const style = SECTION_STYLES[token?.section] || SECTION_STYLES.unknown;
  const opacity = token?.learned || token?.section === "count" ? 1 : 0.88;
  const rules = [
    `color: ${style.color}`,
    `opacity: ${opacity}`,
  ];
  if (style.background && style.background !== "transparent") {
    rules.push(`background: ${style.background}`, "border-radius: 3px");
  }
  return rules.join("; ");
}

function tokenTitle(token) {
  const style = SECTION_STYLES[token?.section] || SECTION_STYLES.unknown;
  const label = token?.label || style.label || token?.section || "태그";
  const learned = token?.learned ? " / learned" : "";
  return `${label}${learned}`;
}

function renderHighlightedText(text, tokens) {
  const byBase = new Map();
  for (const token of tokens || []) {
    byBase.set(normalize(token.base || token.token), token);
  }

  let tokenIndex = 0;
  const html = [];
  for (const part of splitPromptText(text)) {
    if (part.delimiter) {
      html.push(escapeHtml(part.text));
      continue;
    }

    const match = /^(\s*)([\s\S]*?)(\s*)$/.exec(part.text);
    const leading = match?.[1] || "";
    const body = match?.[2] || "";
    const trailing = match?.[3] || "";
    if (!body) {
      html.push(escapeHtml(part.text));
      continue;
    }

    const baseKey = normalize(tokenBase(body));
    const sequential = tokens?.[tokenIndex];
    const token = normalize(sequential?.base || sequential?.token) === baseKey
      ? sequential
      : byBase.get(baseKey);
    tokenIndex += 1;

    if (!token) {
      html.push(escapeHtml(part.text));
      continue;
    }

    html.push(escapeHtml(leading));
    html.push(
      `<span style="${tokenStyle(token)}" title="${escapeHtml(tokenTitle(token))}">`
      + escapeHtml(body)
      + "</span>",
    );
    html.push(escapeHtml(trailing));
  }
  return html.join("") || " ";
}

function copyInputTextMetrics(input, overlay) {
  const style = getComputedStyle(input);
  const properties = [
    "font",
    "fontFamily",
    "fontSize",
    "fontWeight",
    "fontStyle",
    "lineHeight",
    "letterSpacing",
    "padding",
    "border",
    "borderRadius",
    "textAlign",
    "textTransform",
    "tabSize",
  ];
  for (const property of properties) {
    overlay.style[property] = style[property];
  }
}

function syncOverlayBounds(input, overlay) {
  overlay.style.left = `${input.offsetLeft}px`;
  overlay.style.top = `${input.offsetTop}px`;
  overlay.style.width = `${input.offsetWidth}px`;
  overlay.style.height = `${input.offsetHeight}px`;
  overlay.scrollTop = input.scrollTop;
  overlay.scrollLeft = input.scrollLeft;
}

function ensureHighlightOverlay(input) {
  if (input.__easyuseAnimaHighlightOverlay) {
    syncOverlayBounds(input, input.__easyuseAnimaHighlightOverlay);
    return input.__easyuseAnimaHighlightOverlay;
  }

  const parent = input.parentElement;
  if (!parent) {
    return null;
  }
  if (getComputedStyle(parent).position === "static") {
    parent.style.position = "relative";
  }

  const overlay = document.createElement("pre");
  overlay.className = "easyuse-anima-highlight-overlay";
  overlay.setAttribute("aria-hidden", "true");
  overlay.style.cssText = [
    "position: absolute",
    "box-sizing: border-box",
    "margin: 0",
    "overflow: hidden",
    "white-space: pre-wrap",
    "overflow-wrap: break-word",
    "word-break: normal",
    "pointer-events: none",
    "z-index: 0",
    "background: rgba(15, 23, 42, 0.62)",
    "color: var(--input-text, #ddd)",
  ].join("; ");
  copyInputTextMetrics(input, overlay);
  parent.insertBefore(overlay, input);

  ensureHighlightStyle();
  input.classList.add("easyuse-anima-highlight-input");
  input.style.position = input.style.position || "relative";
  input.style.zIndex = "1";
  input.style.background = "transparent";
  input.style.color = "transparent";
  input.style.caretColor = "var(--input-text, #ddd)";
  input.style.webkitTextFillColor = "transparent";

  input.addEventListener("scroll", () => syncOverlayBounds(input, overlay));
  input.__easyuseAnimaHighlightOverlay = overlay;
  syncOverlayBounds(input, overlay);
  return overlay;
}

function desiredLegendHeight(ctx, width) {
  let x = 14;
  let rows = 1;
  ctx.font = "9px sans-serif";
  for (const key of LEGEND_ITEMS) {
    const label = SECTION_STYLES[key].label;
    const itemWidth = ctx.measureText(label).width + 25;
    if (x + itemWidth > width - 12) {
      x = 14;
      rows += 1;
    }
    x += itemWidth + 10;
  }
  return Math.max(LEGEND_HEIGHT, 34 + rows * LEGEND_ROW_HEIGHT);
}

function drawLegend(ctx, node, widget, width, y) {
  const nextHeight = desiredLegendHeight(ctx, width);
  if (Math.abs(nextHeight - widget.__height) > 2) {
    widget.__height = nextHeight;
    refreshNodeSize(node);
  }
  const height = widget.__height || LEGEND_HEIGHT;
  ctx.save();
  ctx.fillStyle = "rgba(15, 23, 42, 0.58)";
  ctx.beginPath();
  ctx.roundRect?.(8, y + 5, width - 16, height - 10, 7);
  if (!ctx.roundRect) {
    ctx.rect(8, y + 5, width - 16, height - 10);
  }
  ctx.fill();

  ctx.font = "9px sans-serif";
  ctx.fillStyle = "#94a3b8";
  ctx.fillText("Color legend", 14, y + 15);

  let x = 14;
  let rowY = y + 29;
  ctx.font = "9px sans-serif";
  for (const key of LEGEND_ITEMS) {
    const style = SECTION_STYLES[key];
    const label = style.label;
    const itemWidth = ctx.measureText(label).width + 25;
    if (x + itemWidth > width - 12) {
      x = 14;
      rowY += LEGEND_ROW_HEIGHT;
    }
    ctx.fillStyle = style.background;
    ctx.fillRect(x, rowY - 8, 10, 10);
    ctx.fillStyle = style.color;
    ctx.fillText(label, x + 14, rowY);
    x += itemWidth + 6;
  }
  ctx.restore();
}

function ensureLegendWidget(node) {
  const name = "easyuse_anima_color_legend";
  let widget = findWidget(node, name);
  if (widget) {
    return widget;
  }
  widget = {
    name,
    type: "easyuse_anima_color_legend",
    serialize: false,
    __height: LEGEND_HEIGHT,
    computeSize(width) {
      return [width, this.__height];
    },
    draw(ctx, node, width, y) {
      drawLegend(ctx, node, this, width, y);
    },
  };
  node.widgets ||= [];
  node.widgets.push(widget);
  return widget;
}

function displayText(node, widget) {
  if (isWidgetInputLinked(node, widget.name) && widget.__easyuseAnimaExecutedText != null) {
    return String(widget.__easyuseAnimaExecutedText);
  }
  return String(widget?.inputEl?.value ?? widget?.value ?? "");
}

function updateHighlight(node, widget, tokens = widget.__easyuseAnimaTokens || []) {
  const input = widget?.inputEl;
  if (!(input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement)) {
    return;
  }
  const overlay = ensureHighlightOverlay(input);
  if (!overlay) {
    return;
  }
  copyInputTextMetrics(input, overlay);
  syncOverlayBounds(input, overlay);
  const value = displayText(node, widget);
  overlay.innerHTML = value
    ? renderHighlightedText(value, tokens)
    : `<span style="opacity: 0.45">${escapeHtml(input.placeholder || "")}</span>`;
}

function enhanceResizableInput(node, widget) {
  const input = widget?.inputEl;
  if (!(input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement)) {
    return;
  }

  const defaultHeight = FIELD_HEIGHTS[widget.name] || 72;
  const readInputHeight = () => {
    const styleHeight = Number.parseFloat(input.style.height || "");
    return Math.round(input.offsetHeight || input.clientHeight || styleHeight || defaultHeight);
  };

  widget.__easyuseAnimaHeight = Math.max(defaultHeight, widget.__easyuseAnimaHeight || 0);
  input.style.boxSizing = "border-box";
  input.style.resize = "vertical";
  input.style.minHeight = `${Math.min(defaultHeight, 54)}px`;
  input.style.height = `${widget.__easyuseAnimaHeight}px`;

  if (!widget.__easyuseAnimaStudioComputeWrapped) {
    const computeSize = widget.computeSize;
    widget.computeSize = function (width) {
      const base = computeSize?.apply(this, arguments) || [width, defaultHeight];
      return [base[0], Math.max(base[1], this.__easyuseAnimaHeight || defaultHeight)];
    };
    widget.__easyuseAnimaStudioComputeWrapped = true;
  }

  const syncHeight = () => {
    const height = Math.max(defaultHeight, readInputHeight());
    if (Math.abs(height - widget.__easyuseAnimaHeight) > 2) {
      widget.__easyuseAnimaHeight = height;
      input.style.height = `${height}px`;
      refreshNodeSize(node);
    }
    updateHighlight(node, widget);
  };

  updateHighlight(node, widget);
  if (input.__easyuseAnimaStudioResizable) {
    return;
  }

  input.addEventListener("mouseup", syncHeight);
  input.addEventListener("pointerup", syncHeight);
  input.addEventListener("input", syncHeight);
  input.addEventListener("scroll", () => updateHighlight(node, widget));
  input.__easyuseAnimaStudioResizable = true;
}

function hookStudioNode(node) {
  const updateByField = new Map();

  const getUpdateField = (fieldName) => {
    if (updateByField.has(fieldName)) {
      return updateByField.get(fieldName);
    }
    let classifySeq = 0;
    const update = debounce(async () => {
      const widget = findWidget(node, fieldName);
      if (!widget) {
        return;
      }
      const text = displayText(node, widget);
      if (!text.trim()) {
        widget.__easyuseAnimaTokens = [];
        updateHighlight(node, widget);
        return;
      }

      const seq = ++classifySeq;
      try {
        const tokens = await classifyPrompt(text);
        if (seq !== classifySeq) {
          return;
        }
        widget.__easyuseAnimaTokens = tokens;
        updateHighlight(node, widget, tokens);
      } catch {
        widget.__easyuseAnimaTokens = [];
        updateHighlight(node, widget);
      }
    });
    updateByField.set(fieldName, update);
    return update;
  };

  for (const name of FIELD_NAMES) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    enhanceResizableInput(node, widget);
    const updateField = getUpdateField(name);

    if (!widget.__easyuseAnimaStudioHooked) {
      const callback = widget.callback;
      widget.callback = function (value) {
        const result = callback?.apply(this, arguments);
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
        return result;
      };
      widget.inputEl?.addEventListener("input", () => {
        widget.value = widget.inputEl.value;
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
      });
      widget.inputEl?.addEventListener("click", () => updateHighlight(node, widget));
      widget.inputEl?.addEventListener("keyup", () => updateHighlight(node, widget));
      widget.__easyuseAnimaStudioHooked = true;
    }
    updateField();
  }

  ensureLegendWidget(node);
  refreshNodeSize(node);
}

function applyExecutedInputs(node, message) {
  const payload = firstValue(message?.prompt_studio_inputs, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  for (const name of FIELD_NAMES) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    widget.__easyuseAnimaExecutedText = String(payload[name] ?? "");
  }
  hookStudioNode(node);
}

app.registerExtension({
  name: "easyuse-anima.prompt-studio",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== NODE_TYPE) {
      return;
    }

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      hookStudioNode(this);
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      onConfigure?.apply(this, arguments);
      hookStudioNode(this);
    };

    const onResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function () {
      const result = onResize?.apply(this, arguments);
      for (const name of FIELD_NAMES) {
        const widget = findWidget(this, name);
        const input = widget?.inputEl;
        if (input && widget.__easyuseAnimaHeight) {
          input.style.height = `${widget.__easyuseAnimaHeight}px`;
          updateHighlight(this, widget);
        }
      }
      return result;
    };

    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      applyExecutedInputs(this, message);
    };
  },
});
