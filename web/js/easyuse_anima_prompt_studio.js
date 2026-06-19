import { app } from "../../../scripts/app.js";

const NODE_TYPE = "EasyUseAnimaPromptStudio";
const ADVANCED_NODE_TYPE = "EasyUseAnimaPromptStudioAdvanced";
const EXTEND_NODE_TYPE = "EasyUseAnimaPromptStudioExtend";
const FIELD_NAMES = [
  "lora_trigger_tags",
  "quality_tags",
  "trigger_and_artist_tags",
  "prompt",
  "trailing_quality_tags",
];
const EXTEND_FIELD_NAMES = [
  "quality_tags_1",
  "quality_tags_2",
  "naia_prompt_3",
  "general_tags_4",
  "general_tags_5",
  "general_tags_6",
  "general_tags_7",
  "general_tags_8",
  "general_tags_9",
  "trailing_tags_10",
  "trailing_tags_11",
  "negative_prompt_1",
  "negative_prompt_2",
  "negative_prompt_3",
  "negative_prompt_4",
];
const EXTEND_VISIBLE_SLOTS_PROPERTY = "easyuse_anima_extend_visible_slots";
const EXTEND_ACTIVE_SLOTS_WIDGET = "active_slots";
const EXTEND_SLOT_GROUPS = [
  { id: "quality", label: "Quality", fields: ["quality_tags_1", "quality_tags_2"] },
  { id: "naia", label: "NAIA", fields: ["naia_prompt_3"] },
  { id: "general", label: "General", fields: ["general_tags_4", "general_tags_5", "general_tags_6", "general_tags_7", "general_tags_8", "general_tags_9"] },
  { id: "trailing", label: "Trailing", fields: ["trailing_tags_10", "trailing_tags_11"] },
  { id: "negative", label: "Negative", fields: ["negative_prompt_1", "negative_prompt_2", "negative_prompt_3", "negative_prompt_4"] },
];
const EXTEND_DEFAULT_VISIBLE_FIELDS = new Set(["quality_tags_1", "general_tags_4", "trailing_tags_10"]);

const FIELD_HEIGHTS = {
  lora_trigger_tags: 42,
  quality_tags: 72,
  trigger_and_artist_tags: 72,
  prompt: 150,
  trailing_quality_tags: 72,
};
const EXTEND_FIELD_HEIGHTS = {
  quality_tags_1: 72,
  quality_tags_2: 72,
  naia_prompt_3: 150,
  general_tags_4: 120,
  general_tags_5: 120,
  general_tags_6: 120,
  general_tags_7: 120,
  general_tags_8: 120,
  general_tags_9: 120,
  trailing_tags_10: 72,
  trailing_tags_11: 72,
  negative_prompt_1: 120,
  negative_prompt_2: 120,
  negative_prompt_3: 120,
  negative_prompt_4: 120,
};

const SECTION_STYLES = {
  quality: { label: "품질", color: "#facc15", background: "rgba(202, 138, 4, 0.18)", weight: 700 },
  safety: { label: "등급", color: "#38bdf8", background: "rgba(2, 132, 199, 0.18)", weight: 600 },
  year: { label: "연도", color: "#2dd4bf", background: "rgba(13, 148, 136, 0.18)", weight: 600 },
  count: { label: "인원수", color: "#60a5fa", background: "rgba(37, 99, 235, 0.18)", weight: 700 },
  character: { label: "캐릭터", color: "#f472b6", background: "rgba(219, 39, 119, 0.18)", weight: 700 },
  artist: { label: "작가", color: "#a78bfa", background: "rgba(124, 58, 237, 0.18)", weight: 700 },
  artist_unknown: { label: "미등록 작가", color: "#f87171", background: "transparent", underline: true, weight: 400 },
  copyright: { label: "작품", color: "#fb923c", background: "rgba(234, 88, 12, 0.18)", weight: 700 },
  meta: { label: "메타", color: "#94a3b8", background: "rgba(100, 116, 139, 0.18)", weight: 600 },
  general: { label: "학습 태그", color: "#4ade80", background: "rgba(22, 163, 74, 0.16)", weight: 600 },
  natural: { label: "자연어", color: "#cbd5e1", background: "rgba(71, 85, 105, 0.16)", weight: 400 },
  unknown: { label: "미확인", color: "#cbd5e1", background: "transparent", underline: true, weight: 400 },
};

const LEGEND_ITEMS = [
  "quality",
  "safety",
  "year",
  "count",
  "character",
  "artist",
  "copyright",
  "general",
  "meta",
  "natural",
  "artist_unknown",
  "unknown",
];
const LEGEND_TOP_GAP = 14;
const LEGEND_ROW_HEIGHT = 18;
const LEGEND_COLUMNS = 2;
const STUDIO_WIDGET_VERTICAL_GAP = 8;

const WEIGHTED_TOKEN_RE = /^\((.*):[-+]?\d+(?:\.\d+)?\)$/s;
const INLINE_SPACE_RE = /[ \t]+/g;
const PROMPT_STUDIO_SETTINGS = {
  typoIndicator: true,
};
let middlePanForwardActive = false;
const ADVANCED_CONTROL_WIDGETS = [
  {
    name: "use_naia",
    label: "Fill from NAIA",
    title: "Keep filling the NAIA Prompt field with a fresh NAIA random prompt while this is enabled.",
    showInControlBar: false,
  },
  {
    name: "consume_naia_on_queue",
    label: "1x",
    title: "Save successful NAIA fills with the request flag turned off.",
    showInControlBar: false,
  },
  {
    name: "use_anima_mod_guidance",
    label: "AMG",
    title: "Send positive quality fields to Anima Mod Guidance output.",
  },
  {
    name: "pin_trigger_tags_to_front",
    label: "Pin",
    title: "Keep positive artist/trigger fields at the front.",
  },
];
const ADVANCED_WIDGET_INDEX = {
  use_naia: 0,
  consume_naia_on_queue: 1,
  use_anima_mod_guidance: 2,
  pin_trigger_tags_to_front: 3,
  advanced_fields: 4,
};
const ADVANCED_FIELDS_PROPERTY = "easyuse_anima_advanced_fields";
const ADVANCED_FIELD_SOCKET_PREFIX = "field_";
const ADVANCED_FIELD_TYPES = ["quality", "artist", "general", "naia"];
const ADVANCED_FIELD_LABELS = {
  quality: "Quality Tags",
  artist: "Artist Tags",
  general: "General Tags",
  naia: "NAIA Prompt",
};
const ADVANCED_NAIA_FILL_TITLE = (
  "When enabled, every queue fills this read-only NAIA Prompt field with a fresh NAIA random prompt. "
  + "Saved image workflows store the current result with this disabled, so reloaded images reuse it."
);
const ADVANCED_DEFAULT_FIELDS = [
  {
    id: "positive_quality",
    pane: "positive",
    type: "quality",
    label: "Quality Tags",
    text: "newest, masterpiece, best quality, score_8, score_7:, highres, absurdres, very aesthetic",
    height: 72,
    enabled: true,
  },
  {
    id: "positive_artist",
    pane: "positive",
    type: "artist",
    label: "Artist Tags",
    text: "",
    height: 72,
    enabled: true,
  },
  {
    id: "positive_general",
    pane: "positive",
    type: "general",
    label: "General Tags",
    text: "",
    height: 150,
    enabled: true,
  },
  {
    id: "positive_trailing",
    pane: "positive",
    type: "general",
    label: "General Tags",
    text: "location, (A highly aesthetic Pixiv style illustration, clean composition, high-quality digital art, detailed background, sharp focus on facial expressions.:0.6)",
    height: 72,
    enabled: true,
  },
  {
    id: "negative_general",
    pane: "negative",
    type: "general",
    label: "General Tags",
    text: "",
    height: 120,
    enabled: true,
  },
];

function findWidget(node, name) {
  return node.widgets?.find((widget) => widget.name === name);
}

function findInputEl(widget) {
  const input = widget?.inputEl;
  if (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement) {
    return input;
  }
  return null;
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

function ensureAdvancedStyle() {
  if (document.getElementById("easyuse-anima-advanced-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-advanced-style";
  style.textContent = `
    .easyuse-anima-advanced-editor {
      box-sizing: border-box;
      width: 100%;
      min-width: 280px;
      color: var(--fg-color, #ddd);
      font: 12px sans-serif;
      user-select: none;
    }
    .easyuse-anima-advanced-panes {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .easyuse-anima-advanced-editor.is-narrow .easyuse-anima-advanced-panes {
      flex-direction: column;
    }
    .easyuse-anima-advanced-controlbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 5px;
      margin-bottom: 7px;
    }
    .easyuse-anima-advanced-toggle {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 34px;
      height: 21px;
      padding: 0 7px;
      border: 1px solid rgba(148, 163, 184, 0.36);
      background: rgba(30, 41, 59, 0.78);
      color: rgba(226, 232, 240, 0.72);
      font: 10px sans-serif;
      line-height: 1;
      cursor: pointer;
    }
    .easyuse-anima-advanced-toggle.is-on {
      border-color: rgba(96, 165, 250, 0.78);
      background: rgba(37, 99, 235, 0.68);
      color: #fff;
      font-weight: 700;
    }
    .easyuse-anima-advanced-toggle.is-linked {
      opacity: 0.55;
      cursor: default;
    }
    .easyuse-anima-advanced-pane {
      min-width: 0;
      border: 1px solid rgba(148, 163, 184, 0.28);
      background: rgba(15, 23, 42, 0.28);
      padding: 6px;
      box-sizing: border-box;
    }
    .easyuse-anima-advanced-pane-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      margin-bottom: 6px;
      color: rgba(226, 232, 240, 0.82);
      font-weight: 700;
    }
    .easyuse-anima-advanced-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      justify-content: flex-end;
    }
    .easyuse-anima-advanced-actions button,
    .easyuse-anima-field-tools button {
      border: 1px solid rgba(148, 163, 184, 0.34);
      background: rgba(30, 41, 59, 0.8);
      color: rgba(226, 232, 240, 0.9);
      font: 11px sans-serif;
      min-height: 20px;
      padding: 1px 6px;
      cursor: pointer;
    }
    .easyuse-anima-advanced-actions button:disabled,
    .easyuse-anima-field-tools button:disabled {
      opacity: 0.35;
      cursor: default;
    }
    .easyuse-anima-advanced-field {
      margin: 0 0 6px;
    }
    .easyuse-anima-advanced-field.is-disabled {
      opacity: 0.58;
    }
    .easyuse-anima-field-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      min-height: 20px;
      color: rgba(203, 213, 225, 0.86);
    }
    .easyuse-anima-field-label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .easyuse-anima-field-tools {
      display: flex;
      gap: 3px;
      flex: 0 0 auto;
    }
    .easyuse-anima-field-tools button.easyuse-anima-naia-fill {
      min-width: 78px;
      font-weight: 700;
    }
    .easyuse-anima-field-tools button.is-on {
      border-color: rgba(96, 165, 250, 0.78);
      background: rgba(37, 99, 235, 0.58);
      color: #fff;
    }
    .easyuse-anima-advanced-field textarea {
      box-sizing: border-box;
      width: 100%;
      min-height: 42px;
      resize: vertical;
      border: 1px solid rgba(148, 163, 184, 0.28);
      background: rgba(10, 10, 12, 0.78);
      color: var(--input-text, #ddd);
      padding: 6px;
      font: 12px monospace;
      line-height: 1.35;
      outline: none;
    }
    .easyuse-anima-advanced-field textarea:focus {
      border-color: rgba(96, 165, 250, 0.7);
    }
    .easyuse-anima-advanced-field textarea.is-linked {
      opacity: 0.72;
      border-style: dashed;
      cursor: default;
    }
    .easyuse-anima-advanced-field.is-naia textarea {
      border-style: dashed;
      background: rgba(15, 23, 42, 0.74);
      cursor: default;
    }
    .easyuse-anima-empty-pane {
      padding: 10px 4px;
      color: rgba(148, 163, 184, 0.72);
      font-size: 11px;
    }
  `;
  document.head.append(style);
}

function ensureExtendSlotStyle() {
  if (document.getElementById("easyuse-anima-extend-slot-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-extend-slot-style";
  style.textContent = `
    .easyuse-anima-extend-slots {
      box-sizing: border-box;
      width: 100%;
      padding-bottom: 4px;
      color: var(--fg-color, #ddd);
      font: 11px sans-serif;
      user-select: none;
    }
    .easyuse-anima-extend-slot-row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 5px;
      width: 100%;
    }
    .easyuse-anima-extend-slot-hide-row {
      display: flex;
      flex-wrap: wrap;
      margin-top: 5px;
    }
    .easyuse-anima-extend-slot-row button {
      box-sizing: border-box;
      min-width: 0;
      height: 24px;
      border: 1px solid rgba(148, 163, 184, 0.38);
      border-radius: 4px;
      background: rgba(17, 24, 39, 0.7);
      color: var(--fg-color, #ddd);
      font: 11px sans-serif;
      cursor: pointer;
    }
    .easyuse-anima-extend-slot-row button:hover:not(:disabled) {
      border-color: rgba(96, 165, 250, 0.74);
      background: rgba(30, 64, 175, 0.5);
    }
    .easyuse-anima-extend-slot-row button:disabled {
      opacity: 0.42;
      cursor: default;
    }
    .easyuse-anima-extend-slot-hide-row button {
      flex: 0 1 auto;
      height: 21px;
      padding: 0 6px;
      font-size: 10px;
    }
  `;
  document.head.append(style);
}

function refreshNodeSize(node, options = {}) {
  const update = () => {
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
  };
  if (options.immediate) {
    update();
  } else {
    requestAnimationFrame(update);
  }
}

function debounce(fn, delay = 180) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function isHexColor(value) {
  return /^#[0-9a-f]{6}$/i.test(String(value || ""));
}

function hexToRgba(value, alpha) {
  if (!isHexColor(value)) {
    return "transparent";
  }
  const red = Number.parseInt(value.slice(1, 3), 16);
  const green = Number.parseInt(value.slice(3, 5), 16);
  const blue = Number.parseInt(value.slice(5, 7), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function parseColorSettings(value) {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function applyPromptStudioSettings(settings) {
  PROMPT_STUDIO_SETTINGS.typoIndicator = settings?.["prompt_studio.typo_indicator"] !== "false";
  const colors = parseColorSettings(settings?.["prompt_studio.colors"]);
  for (const [key, color] of Object.entries(colors)) {
    if (!SECTION_STYLES[key] || !isHexColor(color)) {
      continue;
    }
    SECTION_STYLES[key].color = color;
    if (SECTION_STYLES[key].background && SECTION_STYLES[key].background !== "transparent") {
      SECTION_STYLES[key].background = hexToRgba(color, 0.18);
    }
  }
}

async function loadPromptStudioSettings() {
  try {
    const response = await fetch("/easyuse_anima/settings");
    if (!response.ok) {
      return;
    }
    applyPromptStudioSettings(await response.json());
    app.graph?.setDirtyCanvas(true, true);
  } catch {
    // Keep built-in defaults if the settings endpoint is not available yet.
  }
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
  if (style.underline && PROMPT_STUDIO_SETTINGS.typoIndicator && !token?.weighted) {
    rules.push(
      "text-decoration-line: underline",
      "text-decoration-style: wavy",
      "text-decoration-color: #ef4444",
      "text-underline-offset: 2px",
    );
  }
  return rules.join("; ");
}

function tokenTitle(token) {
  const style = SECTION_STYLES[token?.section] || SECTION_STYLES.unknown;
  const label = token?.label || style.label || token?.section || "태그";
  const learned = token?.learned ? " / learned" : "";
  return `${label}${learned}`;
}

function tokenSpanHtml(text, token) {
  return `<span style="${tokenStyle(token)}" title="${escapeHtml(tokenTitle(token))}">`
    + escapeHtml(text)
    + "</span>";
}

function findTokenMatch(body, offset, token) {
  let start = offset;
  while (start < body.length && /\s/.test(body[start])) {
    start += 1;
  }

  const candidates = [
    String(token?.token || ""),
    String(token?.base || ""),
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (body.slice(start, start + candidate.length) === candidate) {
      return { start, end: start + candidate.length };
    }
    const normalized = normalize(candidate);
    const maxEnd = Math.min(body.length, start + candidate.length + 32);
    for (let end = start + 1; end <= maxEnd; end += 1) {
      const prefix = normalize(body.slice(start, end));
      if (prefix === normalized) {
        return { start, end };
      }
      if (prefix.length > normalized.length + 8) {
        break;
      }
    }
  }
  return null;
}

function renderSequentialBody(body, tokens, startIndex) {
  let cursor = 0;
  let index = startIndex;
  let matched = 0;
  const html = [];

  while (index < (tokens?.length || 0)) {
    const token = tokens[index];
    const match = findTokenMatch(body, cursor, token);
    if (!match) {
      break;
    }
    html.push(escapeHtml(body.slice(cursor, match.start)));
    html.push(tokenSpanHtml(body.slice(match.start, match.end), token));
    cursor = match.end;
    index += 1;
    matched += 1;
    if (!body.slice(cursor).trim()) {
      break;
    }
  }

  if (!matched) {
    return null;
  }
  html.push(escapeHtml(body.slice(cursor)));
  return { html: html.join(""), nextIndex: index };
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

    if (token) {
      tokenIndex += 1;
      html.push(escapeHtml(leading));
      html.push(tokenSpanHtml(body, token));
      html.push(escapeHtml(trailing));
      continue;
    }

    const rendered = renderSequentialBody(body, tokens, tokenIndex);
    if (rendered) {
      tokenIndex = rendered.nextIndex;
      html.push(escapeHtml(leading));
      html.push(rendered.html);
      html.push(escapeHtml(trailing));
      continue;
    }

    html.push(escapeHtml(part.text));
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

function textareaContentHeight(input, minimumHeight) {
  if (!input) {
    return minimumHeight;
  }
  const previousHeight = input.style.height;
  const previousOverflow = input.style.overflowY;
  input.style.height = "auto";
  input.style.overflowY = "hidden";
  const contentHeight = Math.ceil(Number(input.scrollHeight) || 0);
  input.style.height = previousHeight;
  input.style.overflowY = previousOverflow;
  return Math.max(minimumHeight, contentHeight);
}

function desiredTextareaHeight(input, currentHeight, minimumHeight, options = {}) {
  const includeCurrent = options.includeCurrent !== false;
  const contentHeight = textareaContentHeight(input, minimumHeight);
  return Math.max(
    minimumHeight,
    includeCurrent ? Math.round(Number(currentHeight) || 0) : 0,
    contentHeight,
  );
}

function studioVisualMinimumHeight(widget) {
  return Math.min(studioDefaultHeight(widget), 54);
}

function studioMinimumHeight(widget, input = findInputEl(widget)) {
  return studioVisualMinimumHeight(widget);
}

function studioContentHeight(widget, input = findInputEl(widget)) {
  return desiredTextareaHeight(input, 0, studioVisualMinimumHeight(widget), { includeCurrent: false });
}

function studioCurrentHeight(widget, input = findInputEl(widget)) {
  const styleHeight = Number.parseFloat(input?.style?.height || "");
  return Math.round(
    Number(input?.offsetHeight)
    || Number(input?.clientHeight)
    || styleHeight
    || Number(widget?.__easyuseAnimaHeight)
    || studioDefaultHeight(widget),
  );
}

function setStudioInputHeight(node, widget, height, refresh = false) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const minimumHeight = studioMinimumHeight(widget, input);
  const nextHeight = Math.max(minimumHeight, Math.round(Number(height) || 0));
  widget.__easyuseAnimaLayoutHeight = nextHeight + STUDIO_WIDGET_VERTICAL_GAP;
  if (Math.abs(nextHeight - (widget.__easyuseAnimaHeight || 0)) > 1) {
    widget.__easyuseAnimaHeight = nextHeight;
    input.style.height = `${nextHeight}px`;
    if (refresh) {
      refreshNodeSize(node, { immediate: refresh === "immediate" });
    }
  } else {
    input.style.height = `${nextHeight}px`;
    if (refresh === "immediate") {
      refreshNodeSize(node, { immediate: true });
    }
  }
  syncStudioOverflow(widget);
  updateHighlight(node, widget);
}

function syncStudioOverflow(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const height = studioCurrentHeight(widget, input);
  const contentHeight = textareaContentHeight(input, studioVisualMinimumHeight(widget));
  input.style.overflowY = contentHeight > height + 2 ? "auto" : "hidden";
  if (input.__easyuseAnimaHighlightOverlay) {
    input.__easyuseAnimaHighlightOverlay.style.overflow = "hidden";
  }
}

function growStudioManualHeightToContent(node, widget, refresh = false) {
  const input = findInputEl(widget);
  if (!input || !widget.__easyuseAnimaManualHeight || widget.__easyuseAnimaExtendHidden) {
    return false;
  }
  const currentHeight = studioCurrentHeight(widget, input);
  const contentHeight = studioContentHeight(widget, input);
  if (contentHeight > currentHeight + 2) {
    setStudioInputHeight(node, widget, contentHeight, refresh);
    return true;
  }
  syncStudioOverflow(widget);
  updateHighlight(node, widget);
  return false;
}

function setStudioManualHeight(node, widget) {
  const input = findInputEl(widget);
  if (!input || widget.__easyuseAnimaExtendHidden) {
    return;
  }
  widget.__easyuseAnimaManualHeight = true;
  setStudioInputHeight(
    node,
    widget,
    Math.max(studioCurrentHeight(widget, input), studioContentHeight(widget, input)),
    "immediate",
  );
}

function expandStudioInputToContent(node, widget, refresh = false) {
  const input = findInputEl(widget);
  if (!input || widget.__easyuseAnimaExtendHidden) {
    return;
  }
  if (widget.__easyuseAnimaManualHeight) {
    growStudioManualHeightToContent(node, widget, refresh);
    return;
  }
  const height = studioContentHeight(widget, input);
  setStudioInputHeight(node, widget, height, refresh);
}

function visibleStudioWidgets(node) {
  return studioFieldNames(node)
    .map((name) => findWidget(node, name))
    .filter((widget) => {
      const input = findInputEl(widget);
      return widget && input && !widget.hidden && !widget.__easyuseAnimaExtendHidden;
    });
}

function rebalanceStudioInputHeights(node) {
  const widgets = visibleStudioWidgets(node);
  if (!widgets.length) {
    return;
  }

  const currentHeights = widgets.map((widget) => studioCurrentHeight(widget));
  const minimumHeights = widgets.map((widget) => studioMinimumHeight(widget));
  const currentTotal = currentHeights.reduce((sum, value) => sum + value, 0);
  const minimumTotal = minimumHeights.reduce((sum, value) => sum + value, 0);
  const computedHeight = Number(node.computeSize?.()[1]) || currentTotal;
  const nonInputHeight = Math.max(0, computedHeight - currentTotal);
  const targetInputTotal = Math.max(minimumTotal, (Number(node.size?.[1]) || computedHeight) - nonInputHeight);

  if (targetInputTotal < currentTotal - 2) {
    const currentExtra = Math.max(0, currentTotal - minimumTotal);
    const targetExtra = Math.max(0, targetInputTotal - minimumTotal);
    const ratio = currentExtra > 0 ? targetExtra / currentExtra : 0;
    for (const [index, widget] of widgets.entries()) {
      const nextHeight = minimumHeights[index] + (currentHeights[index] - minimumHeights[index]) * ratio;
      setStudioInputHeight(node, widget, nextHeight);
    }
    refreshNodeSize(node, { immediate: true });
    return;
  }

  for (const widget of widgets) {
    expandStudioInputToContent(node, widget);
  }
  refreshNodeSize(node, { immediate: true });
}

function desiredLegendHeight() {
  return LEGEND_TOP_GAP + 16 + Math.ceil(LEGEND_ITEMS.length / LEGEND_COLUMNS) * LEGEND_ROW_HEIGHT;
}

function drawLegend(ctx, node, widget, width, y) {
  const nextHeight = desiredLegendHeight();
  if (Math.abs(nextHeight - widget.__height) > 2) {
    widget.__height = nextHeight;
    refreshNodeSize(node);
  }
  ctx.save();

  ctx.font = "9px sans-serif";
  ctx.fillStyle = "#94a3b8";
  ctx.fillText("Color legend", 14, y + LEGEND_TOP_GAP + 12);

  const left = 14;
  const availableWidth = Math.max(160, width - 28);
  ctx.font = "9px sans-serif";
  const maxItemWidth = Math.max(
    ...LEGEND_ITEMS.map((key) => 14 + ctx.measureText(SECTION_STYLES[key].label).width),
  );
  const columnWidth = Math.min(
    availableWidth / LEGEND_COLUMNS,
    Math.ceil(maxItemWidth + 24),
  );
  const rows = Math.ceil(LEGEND_ITEMS.length / LEGEND_COLUMNS);
  for (const [index, key] of LEGEND_ITEMS.entries()) {
    const style = SECTION_STYLES[key];
    const label = style.label;
    const column = Math.floor(index / rows);
    const row = index % rows;
    const x = left + column * columnWidth;
    const rowY = y + LEGEND_TOP_GAP + 29 + row * LEGEND_ROW_HEIGHT;
    ctx.fillStyle = style.background;
    ctx.fillRect(x, rowY - 8, 10, 10);
    ctx.fillStyle = style.color;
    ctx.fillText(label, x + 14, rowY);
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
    __height: desiredLegendHeight(),
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

function isExtendNode(node) {
  return node?.type === EXTEND_NODE_TYPE || node?.comfyClass === EXTEND_NODE_TYPE;
}

function studioFieldNames(node) {
  return isExtendNode(node) ? EXTEND_FIELD_NAMES : FIELD_NAMES;
}

function parseExtendSlots(raw) {
  if (Array.isArray(raw)) {
    return new Set(raw.filter((name) => EXTEND_FIELD_NAMES.includes(name)));
  }
  if (typeof raw === "string" && raw.trim()) {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return new Set(parsed.filter((name) => EXTEND_FIELD_NAMES.includes(name)));
      }
    } catch {
      return new Set();
    }
  }
  return new Set();
}

function extendVisibleSlotsState(node) {
  const propertyRaw = node?.properties?.[EXTEND_VISIBLE_SLOTS_PROPERTY];
  if (propertyRaw != null) {
    return { slots: parseExtendSlots(propertyRaw), explicit: true };
  }
  return { slots: new Set(EXTEND_DEFAULT_VISIBLE_FIELDS), explicit: true };
}

function extendVisibleSlots(node) {
  return extendVisibleSlotsState(node).slots;
}

function writeExtendVisibleSlots(node, slots) {
  const filtered = [...slots].filter((name) => EXTEND_FIELD_NAMES.includes(name));
  node.properties ||= {};
  node.properties[EXTEND_VISIBLE_SLOTS_PROPERTY] = filtered;
  const widget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
  if (widget) {
    widget.value = JSON.stringify(filtered);
  }
}

function extendSlotShouldShow(node, fieldName, state = extendVisibleSlotsState(node)) {
  if (isWidgetInputLinked(node, fieldName)) {
    return true;
  }
  return state.slots.has(fieldName);
}

function setExtendWidgetHidden(widget, hidden) {
  if (!widget) {
    return;
  }
  if (!widget.__easyuseAnimaExtendOriginalComputeSize) {
    widget.__easyuseAnimaExtendOriginalComputeSize = widget.computeSize;
  }
  if (!widget.__easyuseAnimaExtendOriginalDraw) {
    widget.__easyuseAnimaExtendOriginalDraw = widget.draw;
  }

  widget.__easyuseAnimaExtendHidden = hidden;
  widget.hidden = hidden;
  widget.options ||= {};
  widget.options.hidden = hidden;
  if (hidden) {
    widget.computeSize = () => [0, -4];
    widget.draw = () => {};
  } else {
    widget.computeSize = widget.__easyuseAnimaExtendOriginalComputeSize;
    widget.draw = widget.__easyuseAnimaExtendOriginalDraw;
  }

  const input = findInputEl(widget);
  if (input) {
    input.style.display = hidden ? "none" : "";
    input.style.pointerEvents = hidden ? "none" : "";
    if (input.__easyuseAnimaHighlightOverlay) {
      input.__easyuseAnimaHighlightOverlay.style.display = hidden ? "none" : "";
    }
  }
}

function hideExtendStateWidget(node) {
  const widget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
  if (!widget || widget.__easyuseAnimaExtendStateHidden) {
    return;
  }
  widget.__easyuseAnimaExtendStateHidden = true;
  widget.hidden = true;
  widget.serialize = true;
  widget.options ||= {};
  widget.options.hidden = true;
  widget.computeSize = () => [0, -4];
  widget.draw = () => {};
  const input = findInputEl(widget);
  if (input) {
    input.style.display = "none";
  }
}

function applyExtendSlotVisibility(node) {
  if (!isExtendNode(node)) {
    return;
  }
  hideExtendStateWidget(node);
  const state = extendVisibleSlotsState(node);
  const visible = new Set(state.slots);
  for (const fieldName of EXTEND_FIELD_NAMES) {
    const shouldShow = extendSlotShouldShow(node, fieldName, state);
    if (shouldShow) {
      visible.add(fieldName);
    }
    setExtendWidgetHidden(findWidget(node, fieldName), !shouldShow);
  }
  writeExtendVisibleSlots(node, visible);
}

function measureExtendSlotControlsHeight(node) {
  const container = node.__easyuseAnimaExtendSlotControlsEl;
  if (!container) {
    return 30;
  }
  return Math.max(
    30,
    Math.ceil(
      Number(container.scrollHeight)
      || Number(container.getBoundingClientRect?.().height)
      || 0,
    ) + 4,
  );
}

function refreshExtendSlotControlsSize(node) {
  const widget = findWidget(node, "easyuse_anima_extend_slot_controls");
  if (widget) {
    widget.__height = measureExtendSlotControlsHeight(node);
  }
}

function refreshExtendLayoutAfterSlotChange(node) {
  refreshExtendSlotControlsSize(node);
  for (const widget of visibleStudioWidgets(node)) {
    expandStudioInputToContent(node, widget);
  }
  refreshNodeSize(node, { immediate: true });
  requestAnimationFrame(() => {
    refreshExtendSlotControlsSize(node);
    for (const widget of visibleStudioWidgets(node)) {
      expandStudioInputToContent(node, widget);
    }
    refreshNodeSize(node, { immediate: true });
  });
}

function addNextExtendSlot(node, group) {
  const visible = extendVisibleSlots(node);
  const next = group.fields.find((fieldName) => !extendSlotShouldShow(node, fieldName));
  if (!next) {
    return;
  }
  visible.add(next);
  writeExtendVisibleSlots(node, visible);
  applyExtendSlotVisibility(node);
  renderExtendSlotControls(node);
  refreshExtendLayoutAfterSlotChange(node);
}

function hideExtendSlot(node, fieldName) {
  if (!EXTEND_FIELD_NAMES.includes(fieldName) || isWidgetInputLinked(node, fieldName)) {
    return;
  }
  const visible = extendVisibleSlots(node);
  visible.delete(fieldName);
  writeExtendVisibleSlots(node, visible);
  applyExtendSlotVisibility(node);
  renderExtendSlotControls(node);
  refreshExtendLayoutAfterSlotChange(node);
}

function extendSlotShortLabel(fieldName) {
  if (fieldName === "naia_prompt_3") {
    return "NAIA3";
  }
  const match = /_(\d+)$/.exec(fieldName);
  const index = match?.[1] || "";
  if (fieldName.startsWith("quality_")) {
    return `Q${index}`;
  }
  if (fieldName.startsWith("general_")) {
    return `G${index}`;
  }
  if (fieldName.startsWith("trailing_")) {
    return `T${index}`;
  }
  if (fieldName.startsWith("negative_")) {
    return `N${index}`;
  }
  return fieldName;
}

function renderExtendSlotControls(node) {
  const container = node.__easyuseAnimaExtendSlotControlsEl;
  if (!container) {
    return;
  }
  container.innerHTML = "";
  const row = document.createElement("div");
  row.className = "easyuse-anima-extend-slot-row";
  for (const group of EXTEND_SLOT_GROUPS) {
    const shown = group.fields.filter((fieldName) => extendSlotShouldShow(node, fieldName)).length;
    const next = group.fields.find((fieldName) => !extendSlotShouldShow(node, fieldName));
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `+ ${group.label} ${shown}/${group.fields.length}`;
    button.disabled = !next;
    button.title = next ? `${next} input slot show` : "No hidden slots left";
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      addNextExtendSlot(node, group);
    });
    row.append(button);
  }
  container.append(row);

  const visibleFields = EXTEND_SLOT_GROUPS
    .flatMap((group) => group.fields)
    .filter((fieldName) => extendSlotShouldShow(node, fieldName) && !isWidgetInputLinked(node, fieldName));
  if (visibleFields.length) {
    const hideRow = document.createElement("div");
    hideRow.className = "easyuse-anima-extend-slot-row easyuse-anima-extend-slot-hide-row";
    for (const fieldName of visibleFields) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = `Hide ${extendSlotShortLabel(fieldName)}`;
      button.title = `${fieldName} input slot hide`;
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        hideExtendSlot(node, fieldName);
      });
      hideRow.append(button);
    }
    container.append(hideRow);
  }
  refreshExtendSlotControlsSize(node);
}

function ensureExtendSlotControls(node) {
  if (!isExtendNode(node)) {
    return;
  }
  ensureExtendSlotStyle();
  if (!node.__easyuseAnimaExtendSlotControlsEl) {
    const container = document.createElement("div");
    container.className = "easyuse-anima-extend-slots";
    node.__easyuseAnimaExtendSlotControlsEl = container;
    node.addDOMWidget?.("easyuse_anima_extend_slot_controls", "EasyUseAnimaExtendSlotControls", container, {
      serialize: false,
      hideOnZoom: false,
      getMinHeight: () => measureExtendSlotControlsHeight(node),
    });
  }
  renderExtendSlotControls(node);
}

function studioDefaultHeight(widget) {
  return EXTEND_FIELD_HEIGHTS[widget.name] || FIELD_HEIGHTS[widget.name] || 72;
}

function updateHighlight(node, widget, tokens = widget.__easyuseAnimaTokens || []) {
  const input = findInputEl(widget);
  if (!input) {
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
  const input = findInputEl(widget);
  if (!input) {
    return;
  }

  const defaultHeight = studioDefaultHeight(widget);
  const minimumHeight = Math.min(defaultHeight, 54);

  widget.__easyuseAnimaHeight = Math.max(minimumHeight, widget.__easyuseAnimaHeight || defaultHeight);
  widget.__easyuseAnimaLayoutHeight = widget.__easyuseAnimaHeight + STUDIO_WIDGET_VERTICAL_GAP;
  input.style.boxSizing = "border-box";
  input.style.resize = "vertical";
  input.style.overflowY = "hidden";
  input.style.minHeight = `${minimumHeight}px`;
  input.style.height = `${widget.__easyuseAnimaHeight}px`;

  if (!widget.__easyuseAnimaStudioComputeWrapped) {
    const computeSize = widget.computeSize;
    widget.computeSize = function (width) {
      const base = computeSize?.apply(this, arguments) || [width, minimumHeight];
      const layoutHeight = (this.__easyuseAnimaHeight || minimumHeight) + STUDIO_WIDGET_VERTICAL_GAP;
      this.__easyuseAnimaLayoutHeight = layoutHeight;
      return [base[0], Math.max(base[1], layoutHeight)];
    };
    widget.__easyuseAnimaStudioComputeWrapped = true;
  }

  const syncHeight = () => {
    if (widget.__easyuseAnimaManualHeight) {
      if (!growStudioManualHeightToContent(node, widget, "immediate")) {
        refreshNodeSize(node, { immediate: true });
      }
      return;
    }
    const height = desiredTextareaHeight(input, 0, minimumHeight, { includeCurrent: false });
    setStudioInputHeight(node, widget, height, "immediate");
  };
  const rememberResizeStart = () => {
    widget.__easyuseAnimaResizeStartHeight = studioCurrentHeight(widget, input);
  };
  const captureManualResize = () => {
    const startHeight = Number(widget.__easyuseAnimaResizeStartHeight || widget.__easyuseAnimaHeight || 0);
    const currentHeight = studioCurrentHeight(widget, input);
    widget.__easyuseAnimaResizeStartHeight = currentHeight;
    if (Math.abs(currentHeight - startHeight) > 2) {
      setStudioManualHeight(node, widget);
    } else {
      updateHighlight(node, widget);
    }
  };

  requestAnimationFrame(() => expandStudioInputToContent(node, widget, true));
  if (input.__easyuseAnimaStudioResizable) {
    return;
  }

  input.addEventListener("mousedown", rememberResizeStart);
  input.addEventListener("pointerdown", rememberResizeStart);
  input.addEventListener("mouseup", captureManualResize);
  input.addEventListener("pointerup", captureManualResize);
  input.addEventListener("input", syncHeight);
  input.addEventListener("scroll", () => updateHighlight(node, widget));
  input.__easyuseAnimaStudioResizable = true;
}

function syncWidgetValue(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  widget.value = input.value;
}

function syncStudioValues(node, serialized = null) {
  const fieldNames = studioFieldNames(node);
  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (widget) {
      syncWidgetValue(widget);
    }
  }

  if (!serialized || !Array.isArray(node.widgets) || !Array.isArray(serialized.widgets_values)) {
    return;
  }
  if (isExtendNode(node)) {
    applyExtendSlotVisibility(node);
    const activeSlotsValue = JSON.stringify([...extendVisibleSlots(node)]);
    const activeSlotsWidget = findWidget(node, EXTEND_ACTIVE_SLOTS_WIDGET);
    if (activeSlotsWidget) {
      activeSlotsWidget.value = activeSlotsValue;
    }
    serialized.properties ||= {};
    serialized.properties[EXTEND_VISIBLE_SLOTS_PROPERTY] = [...parseExtendSlots(activeSlotsValue)];
  }

  for (const name of fieldNames) {
    const widgetIndex = node.widgets.findIndex((widget) => widget?.name === name);
    const widget = widgetIndex >= 0 ? node.widgets[widgetIndex] : null;
    if (widgetIndex >= 0 && widget) {
      serialized.widgets_values[widgetIndex] = widget.value ?? "";
    }
  }

  if (isExtendNode(node)) {
    const widgetIndex = node.widgets.findIndex((widget) => widget?.name === EXTEND_ACTIVE_SLOTS_WIDGET);
    const widget = widgetIndex >= 0 ? node.widgets[widgetIndex] : null;
    if (widgetIndex >= 0 && widget) {
      serialized.widgets_values[widgetIndex] = widget.value ?? JSON.stringify([...extendVisibleSlots(node)]);
    }
  }
}

function restoreInputFromWidget(widget) {
  const input = findInputEl(widget);
  if (!input) {
    return;
  }
  const value = String(widget?.value ?? input.value ?? "");
  if (input.value !== value) {
    input.value = value;
  }
}

function hookStudioNode(node, attempt = 0) {
  const fieldNames = studioFieldNames(node);
  const updateByField = new Map();
  let pendingInput = false;

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
        widget.__easyuseAnimaLastClassifiedText = "";
        widget.__easyuseAnimaPendingClassifyText = null;
        updateHighlight(node, widget);
        return;
      }
      if (
        widget.__easyuseAnimaLastClassifiedText === text
        && Array.isArray(widget.__easyuseAnimaTokens)
      ) {
        updateHighlight(node, widget, widget.__easyuseAnimaTokens);
        return;
      }
      if (widget.__easyuseAnimaPendingClassifyText === text) {
        return;
      }

      const seq = ++classifySeq;
      widget.__easyuseAnimaPendingClassifyText = text;
      try {
        const tokens = await classifyPrompt(text);
        if (seq !== classifySeq) {
          return;
        }
        widget.__easyuseAnimaLastClassifiedText = text;
        widget.__easyuseAnimaTokens = tokens;
        updateHighlight(node, widget, tokens);
      } catch {
        widget.__easyuseAnimaTokens = [];
        updateHighlight(node, widget);
      } finally {
        if (widget.__easyuseAnimaPendingClassifyText === text) {
          widget.__easyuseAnimaPendingClassifyText = null;
        }
      }
    });
    updateByField.set(fieldName, update);
    return update;
  };

  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    const input = findInputEl(widget);
    if (!input) {
      pendingInput = true;
      continue;
    }
    restoreInputFromWidget(widget);
    if (isExtendNode(node) && name === "naia_prompt_3") {
      input.readOnly = true;
      input.placeholder = "NAIA result";
      input.title = "Read-only NAIA result slot. Enable fill_naia_prompt to update it from NAIA.";
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
      input.addEventListener("input", () => {
        widget.value = input.value;
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
      });
      input.addEventListener("change", () => {
        widget.value = input.value;
        widget.__easyuseAnimaExecutedText = null;
        updateHighlight(node, widget);
        updateField();
      });
      input.addEventListener("blur", () => syncWidgetValue(widget));
      input.addEventListener("click", () => updateHighlight(node, widget));
      input.addEventListener("keyup", () => updateHighlight(node, widget));
      widget.__easyuseAnimaStudioHooked = true;
    }
    updateField();
  }

  if (isExtendNode(node)) {
    applyExtendSlotVisibility(node);
    ensureExtendSlotControls(node);
  }
  ensureLegendWidget(node);
  refreshNodeSize(node);
  if (pendingInput && attempt < 12) {
    setTimeout(() => hookStudioNode(node, attempt + 1), 80);
  }
}

function applyExecutedInputs(node, message) {
  const slotPayload = firstValue(message?.prompt_studio_slots, null);
  const payload = slotPayload || firstValue(message?.prompt_studio_inputs, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  const fieldNames = studioFieldNames(node);
  for (const name of fieldNames) {
    const widget = findWidget(node, name);
    if (!widget) {
      continue;
    }
    if (slotPayload && Object.prototype.hasOwnProperty.call(payload, name)) {
      widget.value = String(payload[name] ?? "");
      restoreInputFromWidget(widget);
      widget.__easyuseAnimaExecutedText = null;
      expandStudioInputToContent(node, widget, true);
    } else {
      widget.__easyuseAnimaExecutedText = String(payload[name] ?? "");
      expandStudioInputToContent(node, widget, true);
    }
  }
  if (slotPayload) {
    if (payload.active_slots != null) {
      writeExtendVisibleSlots(node, parseExtendSlots(payload.active_slots));
    }
    const fillNaia = findWidget(node, "fill_naia_prompt");
    if (fillNaia && payload.fill_naia_prompt != null) {
      fillNaia.value = !!payload.fill_naia_prompt;
    }
  }
  hookStudioNode(node);
}

function advancedDefaultFields() {
  return JSON.parse(JSON.stringify(ADVANCED_DEFAULT_FIELDS));
}

function advancedDefaultFieldsValue() {
  return JSON.stringify(advancedDefaultFields().map((field, index) => normalizeAdvancedField(field, index)));
}

function advancedWidget(node) {
  return findWidget(node, "advanced_fields");
}

function advancedFieldsBackup(node) {
  const value = node?.properties?.[ADVANCED_FIELDS_PROPERTY];
  return typeof value === "string" && value.trim() ? value : "";
}

function syncAdvancedFieldsBackup(node, value) {
  node.properties ||= {};
  node.properties[ADVANCED_FIELDS_PROPERTY] = String(value || "");
}

function normalizeAdvancedFieldsValue(value) {
  if (value == null) {
    return "";
  }
  try {
    const parsed = typeof value === "string" ? JSON.parse(value || "[]") : value;
    if (!Array.isArray(parsed) || !parsed.length) {
      return "";
    }
    return JSON.stringify(parsed.map((field, index) => normalizeAdvancedField(field, index)));
  } catch {
    return "";
  }
}

function serializedAdvancedFieldsValue(serialized) {
  const propertyValue = normalizeAdvancedFieldsValue(serialized?.properties?.[ADVANCED_FIELDS_PROPERTY]);
  if (propertyValue) {
    return propertyValue;
  }
  const widgetsValue = normalizeAdvancedFieldsValue(serialized?.widgets_values?.[ADVANCED_WIDGET_INDEX.advanced_fields]);
  return widgetsValue || "";
}

function captureAdvancedConfigure(node, serialized) {
  const value = serializedAdvancedFieldsValue(serialized);
  if (!value) {
    return;
  }
  node.__easyuseAnimaPendingAdvancedFieldsValue = value;
  syncAdvancedFieldsBackup(node, value);
  const widget = advancedWidget(node);
  if (widget) {
    widget.value = value;
  }
}

function ensureAdvancedWidgetValue(node) {
  const widget = advancedWidget(node);
  if (!widget) {
    return;
  }
  if (node.__easyuseAnimaPendingAdvancedFieldsValue) {
    widget.value = node.__easyuseAnimaPendingAdvancedFieldsValue;
    syncAdvancedFieldsBackup(node, widget.value);
    delete node.__easyuseAnimaPendingAdvancedFieldsValue;
    return;
  }
  const backup = advancedFieldsBackup(node);
  const widgetValue = String(widget.value || "");
  if (
    backup
    && (!widgetValue.trim() || widgetValue === advancedDefaultFieldsValue())
  ) {
    widget.value = backup;
  }
}

function hideAdvancedInternalWidget(node, name) {
  const widget = findWidget(node, name);
  if (!widget || widget.__easyuseAnimaAdvancedHidden) {
    return;
  }
  widget.__easyuseAnimaAdvancedHidden = true;
  widget.hidden = true;
  widget.serialize = true;
  widget.computeSize = () => [0, 0];
  widget.draw = () => {};
}

function hideAdvancedControlWidgets(node) {
  for (const { name } of ADVANCED_CONTROL_WIDGETS) {
    hideAdvancedInternalWidget(node, name);
  }
}

function normalizeAdvancedField(field, index = 0) {
  const pane = field?.pane === "negative" ? "negative" : "positive";
  let type = ADVANCED_FIELD_TYPES.includes(field?.type) ? field.type : "general";
  if (pane === "negative" && type === "naia") {
    type = "general";
  }
  const label = String(field?.label || ADVANCED_FIELD_LABELS[type] || "General Tags");
  return {
    id: String(field?.id || `${pane}_${type}_${index + 1}`),
    pane,
    type,
    label,
    text: String(field?.text || ""),
    height: Math.max(42, Math.round(Number(field?.height) || 72)),
    enabled: field?.enabled !== false,
  };
}

function parseAdvancedFields(node) {
  ensureAdvancedWidgetValue(node);
  const widget = advancedWidget(node);
  const sourceValue = String(widget?.value || advancedFieldsBackup(node) || "[]");
  try {
    const parsed = JSON.parse(sourceValue);
    if (Array.isArray(parsed) && parsed.length) {
      const fields = [];
      let seenNaia = false;
      parsed.forEach((field, index) => {
        const normalized = normalizeAdvancedField(field, index);
        if (normalized.type === "naia") {
          if (seenNaia) {
            return;
          }
          seenNaia = true;
          normalized.pane = "positive";
        }
        fields.push(normalized);
      });
      return fields.length ? fields : advancedDefaultFields();
    }
  } catch {
    // Fall through to default fields.
  }
  return advancedDefaultFields();
}

function collectAdvancedEditorFields(node) {
  const fields = (node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node))
    .map((field, index) => normalizeAdvancedField(field, index));
  const editor = node.__easyuseAnimaAdvancedEditorEl;
  if (!editor) {
    return fields;
  }

  const byId = new Map(fields.map((field) => [field.id, field]));
  editor.querySelectorAll("textarea[data-easyuse-anima-advanced-field-id]").forEach((textarea) => {
    const id = textarea.dataset.easyuseAnimaAdvancedFieldId;
    const field = byId.get(id);
    if (!field || advancedFieldInputLinked(node, field)) {
      return;
    }
    field.text = textarea.value;
    const height = Number.parseInt(textarea.style.height || "", 10);
    if (Number.isFinite(height) && height > 0) {
      field.height = Math.max(field.height || 42, height);
    }
  });
  return fields;
}

function writeAdvancedFields(node, fields, { render = false } = {}) {
  const widget = advancedWidget(node);
  if (!widget) {
    return;
  }
  widget.value = JSON.stringify(fields.map((field, index) => normalizeAdvancedField(field, index)));
  syncAdvancedFieldsBackup(node, widget.value);
  node.__easyuseAnimaAdvancedFields = fields;
  syncAdvancedFieldInputs(node, fields);
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  if (render) {
    renderAdvancedEditor(node);
  }
}

function advancedFieldInputName(field) {
  const raw = String(field?.id || "field")
    .replace(/[^a-zA-Z0-9_]/g, "_")
    .replace(/^_+|_+$/g, "");
  return `${ADVANCED_FIELD_SOCKET_PREFIX}${raw || "field"}`;
}

function advancedFieldIndexLabel(fields, field) {
  const paneFields = (fields || []).filter((item) => item.pane === field.pane);
  const paneIndex = paneFields.findIndex((item) => item.id === field.id);
  const number = Math.max(0, paneIndex) + 1;
  return field.pane === "negative" ? `neg${number}` : `${number}`;
}

function isAdvancedFieldInput(input) {
  return !!input?.__easyuseAnimaAdvancedFieldInput
    || String(input?.name || "").startsWith(ADVANCED_FIELD_SOCKET_PREFIX);
}

function updateNodeInputLinkSlots(node) {
  if (!node?.inputs || !app.graph?.links) {
    return;
  }
  const expectedLinks = new Set();
  node.inputs.forEach((input, index) => {
    if (input?.link == null) {
      return;
    }
    const link = app.graph.links[input.link];
    if (link) {
      expectedLinks.add(Number(input.link));
      link.target_id = node.id;
      link.target_slot = index;
    }
  });

  for (const [rawLinkId, link] of Object.entries(app.graph.links)) {
    const linkId = Number(rawLinkId);
    if (!link || Number(link.target_id) !== Number(node.id)) {
      continue;
    }
    const targetInput = node.inputs?.[link.target_slot];
    if (targetInput?.link === linkId) {
      continue;
    }
    const originNode = app.graph.getNodeById?.(link.origin_id);
    const originOutput = originNode?.outputs?.[link.origin_slot];
    if (Array.isArray(originOutput?.links)) {
      originOutput.links = originOutput.links.filter((id) => Number(id) !== linkId);
    }
    if (!expectedLinks.has(linkId)) {
      delete app.graph.links[rawLinkId];
    }
  }
}

function syncAdvancedFieldInputs(node, fields) {
  if (!node || typeof node.addInput !== "function") {
    return;
  }

  const wanted = new Map();
  (fields || []).forEach((field) => {
    if (field?.type === "naia") {
      return;
    }
    wanted.set(advancedFieldInputName(field), { field, indexLabel: advancedFieldIndexLabel(fields, field) });
  });

  for (let index = (node.inputs?.length || 0) - 1; index >= 0; index -= 1) {
    const input = node.inputs[index];
    if (isAdvancedFieldInput(input) && !wanted.has(input.name)) {
      node.removeInput?.(index);
    }
  }

  for (const [name, { field, indexLabel }] of wanted) {
    let input = node.inputs?.find((item) => item.name === name);
    if (!input) {
      node.addInput(name, "STRING");
      input = node.inputs?.find((item) => item.name === name);
    }
    if (!input) {
      continue;
    }
    input.type = "STRING";
    input.label = `${indexLabel}. ${advancedFieldLabel(field)}`;
    input.__easyuseAnimaAdvancedFieldInput = true;
    input.__easyuseAnimaAdvancedFieldId = field.id;
  }

  const fieldInputs = [];
  for (const [name] of wanted) {
    const input = node.inputs?.find((item) => item.name === name);
    if (input) {
      fieldInputs.push(input);
    }
  }
  const otherInputs = (node.inputs || []).filter((input) => !isAdvancedFieldInput(input));
  node.inputs = [...fieldInputs, ...otherInputs];
  updateNodeInputLinkSlots(node);
}

function advancedFieldInputLinked(node, field) {
  const name = advancedFieldInputName(field);
  return !!node.inputs?.some((input) => input.name === name && input.link != null);
}

function advancedFieldDisplayText(node, field) {
  const name = advancedFieldInputName(field);
  const values = node.__easyuseAnimaAdvancedFieldInputValues || {};
  if (advancedFieldInputLinked(node, field) && Object.prototype.hasOwnProperty.call(values, name)) {
    return String(values[name] ?? "");
  }
  return String(field?.text || "");
}

function advancedFieldLabel(field) {
  const base = ADVANCED_FIELD_LABELS[field.type] || "General Tags";
  return field.label && field.label !== base ? `${base} - ${field.label}` : base;
}

function setAdvancedControlValue(node, name, value) {
  const widget = findWidget(node, name);
  if (!widget || isWidgetInputLinked(node, name)) {
    return false;
  }
  widget.value = !!value;
  widget.callback?.(widget.value);
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  return true;
}

function createAdvancedControlBar(node) {
  const bar = document.createElement("div");
  bar.className = "easyuse-anima-advanced-controlbar";
  for (const control of ADVANCED_CONTROL_WIDGETS) {
    if (control.showInControlBar === false) {
      continue;
    }
    const widget = findWidget(node, control.name);
    if (!widget) {
      continue;
    }
    const linked = isWidgetInputLinked(node, control.name);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "easyuse-anima-advanced-toggle";
    button.classList.toggle("is-on", !!widget.value);
    button.classList.toggle("is-linked", linked);
    button.textContent = control.label;
    button.title = linked ? `${control.title} Linked input controls this value.` : control.title;
    button.disabled = linked;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      setAdvancedControlValue(node, control.name, !widget.value);
      renderAdvancedEditor(node);
    });
    bar.append(button);
  }
  return bar;
}

function advancedPaneFields(node, pane) {
  return (node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node))
    .filter((field) => field.pane === pane);
}

function hasPositiveNaia(node) {
  return (node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node))
    .some((field) => field.pane === "positive" && field.type === "naia");
}

function advancedEditorWidth(node) {
  return Math.max(280, Math.round((Number(node?.size?.[0]) || 360) - 24));
}

function syncAdvancedNodeSize(node) {
  requestAnimationFrame(() => {
    const editor = node.__easyuseAnimaAdvancedEditorEl;
    if (!editor || !node.size || typeof node.setSize !== "function") {
      return;
    }
    const width = Number(node.size[0]) || 360;
    editor.style.width = `${advancedEditorWidth(node)}px`;
    editor.style.maxWidth = `${advancedEditorWidth(node)}px`;
    editor.classList.toggle("is-narrow", width < 620);
    const computed = node.computeSize?.();
    const nextHeight = Math.max(220, Number(computed?.[1]) || editor.scrollHeight || 0);
    if (nextHeight && Math.abs(nextHeight - Number(node.size[1] || 0)) > 2) {
      node.setSize([width, nextHeight]);
    }
    app.graph?.setDirtyCanvas?.(true, true);
    requestAnimationFrame(() => app.graph?.setDirtyCanvas?.(true, true));
  });
}

function dispatchCanvasMouseEvent(type, sourceEvent, overrides = {}) {
  const canvas = app.canvas?.canvas;
  if (!canvas) {
    return;
  }
  const event = new MouseEvent(type, {
    bubbles: true,
    cancelable: true,
    view: window,
    clientX: sourceEvent.clientX,
    clientY: sourceEvent.clientY,
    screenX: sourceEvent.screenX,
    screenY: sourceEvent.screenY,
    button: overrides.button ?? sourceEvent.button,
    buttons: overrides.buttons ?? sourceEvent.buttons,
    ctrlKey: sourceEvent.ctrlKey,
    shiftKey: sourceEvent.shiftKey,
    altKey: sourceEvent.altKey,
    metaKey: sourceEvent.metaKey,
  });
  Object.defineProperty(event, "__easyuseAnimaForwarded", { value: true });
  canvas.dispatchEvent(event);
}

function dispatchCanvasPointerEvent(type, sourceEvent, overrides = {}) {
  const canvas = app.canvas?.canvas;
  if (!canvas || typeof PointerEvent === "undefined") {
    return;
  }
  const event = new PointerEvent(type, {
    bubbles: true,
    cancelable: true,
    view: window,
    clientX: sourceEvent.clientX,
    clientY: sourceEvent.clientY,
    screenX: sourceEvent.screenX,
    screenY: sourceEvent.screenY,
    button: overrides.button ?? sourceEvent.button,
    buttons: overrides.buttons ?? sourceEvent.buttons,
    ctrlKey: sourceEvent.ctrlKey,
    shiftKey: sourceEvent.shiftKey,
    altKey: sourceEvent.altKey,
    metaKey: sourceEvent.metaKey,
    pointerId: sourceEvent.pointerId || 1,
    pointerType: sourceEvent.pointerType || "mouse",
    isPrimary: sourceEvent.isPrimary ?? true,
  });
  Object.defineProperty(event, "__easyuseAnimaForwarded", { value: true });
  canvas.dispatchEvent(event);
}

function isCanvasAreaEvent(event) {
  const canvas = app.canvas?.canvas;
  const rect = canvas?.getBoundingClientRect?.();
  if (!canvas || !rect || event.target === canvas) {
    return false;
  }
  return (
    event.clientX >= rect.left
    && event.clientX <= rect.right
    && event.clientY >= rect.top
    && event.clientY <= rect.bottom
  );
}

function isMiddlePanExcludedTarget(target) {
  if (!(target instanceof Element)) {
    return false;
  }
  return !!target.closest([
    ".comfy-menu",
    ".comfy-modal",
    ".comfyui-menu",
    ".comfyui-settings",
    ".litegraph.litemenu",
    ".easyuse-anima-autocomplete",
    ".easyuse-anima-lora-menu",
  ].join(","));
}

function shouldForwardMiddlePan(event) {
  return (
    !event.__easyuseAnimaForwarded
    && event.button === 1
    && isCanvasAreaEvent(event)
    && !isMiddlePanExcludedTarget(event.target)
  );
}

function startCanvasPanFromDom(event) {
  if (!shouldForwardMiddlePan(event)) {
    return false;
  }
  if (middlePanForwardActive) {
    event.preventDefault();
    event.stopPropagation();
    return true;
  }
  middlePanForwardActive = true;
  event.preventDefault();
  event.stopPropagation();
  document.activeElement?.blur?.();
  dispatchCanvasPointerEvent("pointerdown", event, { button: 1, buttons: 4 });
  dispatchCanvasMouseEvent("mousedown", event, { button: 1, buttons: 4 });

  const move = (moveEvent) => {
    if (moveEvent.__easyuseAnimaForwarded) {
      return;
    }
    moveEvent.preventDefault();
    moveEvent.stopPropagation();
    dispatchCanvasPointerEvent("pointermove", moveEvent, { button: 1, buttons: 4 });
    dispatchCanvasMouseEvent("mousemove", moveEvent, { button: 1, buttons: 4 });
  };
  const stop = (upEvent) => {
    if (upEvent.__easyuseAnimaForwarded) {
      return;
    }
    upEvent.preventDefault();
    upEvent.stopPropagation();
    dispatchCanvasPointerEvent("pointerup", upEvent, { button: 1, buttons: 0 });
    dispatchCanvasMouseEvent("mouseup", upEvent, { button: 1, buttons: 0 });
    middlePanForwardActive = false;
    document.removeEventListener("pointermove", move, true);
    document.removeEventListener("pointerup", stop, true);
    document.removeEventListener("pointercancel", stop, true);
    document.removeEventListener("mousemove", move, true);
    document.removeEventListener("mouseup", stop, true);
  };
  document.addEventListener("pointermove", move, true);
  document.addEventListener("pointerup", stop, true);
  document.addEventListener("pointercancel", stop, true);
  document.addEventListener("mousemove", move, true);
  document.addEventListener("mouseup", stop, true);
  return true;
}

function installMiddlePanForwarder() {
  if (window.__easyuseAnimaMiddlePanForwarderInstalled) {
    return;
  }
  window.__easyuseAnimaMiddlePanForwarderInstalled = true;
  document.addEventListener("pointerdown", startCanvasPanFromDom, true);
  document.addEventListener("mousedown", startCanvasPanFromDom, true);
  document.addEventListener("auxclick", (event) => {
    if (shouldForwardMiddlePan(event)) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);
}

function createAdvancedFieldElement(node, field) {
  const fields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
  const globalIndex = fields.findIndex((item) => item.id === field.id);
  const samePane = fields.filter((item) => item.pane === field.pane);
  const paneIndex = samePane.findIndex((item) => item.id === field.id);
  const block = document.createElement("div");
  block.className = "easyuse-anima-advanced-field";
  block.classList.toggle("is-naia", field.type === "naia");
  block.classList.toggle("is-disabled", field.enabled === false);

  const header = document.createElement("div");
  header.className = "easyuse-anima-field-header";
  const label = document.createElement("div");
  label.className = "easyuse-anima-field-label";
  label.textContent = `${advancedFieldIndexLabel(fields, field)}. ${advancedFieldLabel(field)}`;
  const tools = document.createElement("div");
  tools.className = "easyuse-anima-field-tools";

  const move = (direction) => {
    const currentFields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
    const paneFields = currentFields
      .map((item, index) => ({ item, index }))
      .filter(({ item }) => item.pane === field.pane);
    const current = paneFields.findIndex(({ item }) => item.id === field.id);
    const target = current + direction;
    if (current < 0 || target < 0 || target >= paneFields.length) {
      return;
    }
    const from = paneFields[current].index;
    const to = paneFields[target].index;
    const [removed] = currentFields.splice(from, 1);
    currentFields.splice(to, 0, removed);
    writeAdvancedFields(node, currentFields, { render: true });
  };

  const addTool = (text, title, callback, disabled = false) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text;
    button.title = title;
    button.disabled = disabled;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (!button.disabled) {
        callback();
      }
    });
    if (text === "ON") {
      button.classList.add("is-on");
    }
    tools.append(button);
    return button;
  };

  const toggleButton = addTool(
    field.enabled === false ? "OFF" : "ON",
    "Enable or disable this field in prompt output",
    () => {
      field.enabled = field.enabled === false;
      writeAdvancedFields(node, fields, { render: true });
    },
  );
  toggleButton.classList.toggle("is-on", field.enabled !== false);
  if (field.type === "naia") {
    const useNaiaWidget = findWidget(node, "use_naia");
    const linkedUseNaia = isWidgetInputLinked(node, "use_naia");
    const fillButton = addTool("Fill from NAIA", ADVANCED_NAIA_FILL_TITLE, () => {
      const currentFields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
      const target = currentFields.find((item) => item.id === field.id);
      if (target) {
        target.enabled = true;
      }
      const nextValue = !findWidget(node, "use_naia")?.value;
      setAdvancedControlValue(node, "consume_naia_on_queue", true);
      setAdvancedControlValue(node, "use_naia", nextValue);
      writeAdvancedFields(node, currentFields, { render: true });
    }, linkedUseNaia);
    fillButton.classList.add("easyuse-anima-naia-fill");
    fillButton.classList.toggle("is-on", !!useNaiaWidget?.value);
    fillButton.classList.toggle("is-linked", linkedUseNaia);
  }
  addTool("↑", "Move up", () => move(-1), paneIndex <= 0);
  addTool("↓", "Move down", () => move(1), paneIndex >= samePane.length - 1);
  addTool("X", "Delete field", () => {
    const currentFields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
    currentFields.splice(globalIndex, 1);
    writeAdvancedFields(node, currentFields, { render: true });
  });

  const textarea = document.createElement("textarea");
  const linked = advancedFieldInputLinked(node, field);
  const readonly = linked || field.type === "naia";
  textarea.value = advancedFieldDisplayText(node, field);
  textarea.style.height = `${field.height || 72}px`;
  textarea.style.overflowY = "hidden";
  textarea.placeholder = field.type === "naia"
    ? "NAIA result appears here after queue"
    : field.type === "artist" ? "@artist_tag" : "prompt tags";
  textarea.readOnly = readonly;
  textarea.classList.toggle("is-linked", linked);
  textarea.title = field.type === "naia"
    ? "Read-only NAIA result field. Use Fill from NAIA and queue the workflow to update it."
    : linked ? "Connected STRING input controls this field during execution." : "";
  textarea.dataset.easyuseAnimaAdvancedFieldId = field.id;
  const syncHeight = () => {
    const height = desiredTextareaHeight(
      textarea,
      Math.max(textarea.offsetHeight || 0, field.height || 0),
      42,
    );
    if (height > (field.height || 0)) {
      textarea.style.height = `${height}px`;
      field.height = height;
    }
    writeAdvancedFields(node, fields);
    syncAdvancedNodeSize(node);
  };
  textarea.addEventListener("input", () => {
    if (readonly) {
      return;
    }
    field.text = textarea.value;
    syncHeight();
  });
  textarea.addEventListener("mouseup", syncHeight);
  textarea.addEventListener("pointerup", syncHeight);
  textarea.addEventListener("change", syncHeight);
  requestAnimationFrame(syncHeight);

  header.append(label, tools);
  block.append(header, textarea);
  return block;
}

function addAdvancedField(node, pane, type) {
  const fields = node.__easyuseAnimaAdvancedFields || parseAdvancedFields(node);
  if (type === "naia" && hasPositiveNaia(node)) {
    return;
  }
  const nextId = `${pane}_${type}_${Date.now().toString(36)}`;
  fields.push({
    id: nextId,
    pane,
    type,
    label: ADVANCED_FIELD_LABELS[type] || "General Tags",
    text: "",
    height: type === "general" || type === "naia" ? 120 : 72,
    enabled: true,
  });
  if (type === "naia") {
    setAdvancedControlValue(node, "consume_naia_on_queue", true);
    setAdvancedControlValue(node, "use_naia", true);
  }
  writeAdvancedFields(node, fields, { render: true });
}

function createAdvancedPane(node, pane, title) {
  const section = document.createElement("section");
  section.className = "easyuse-anima-advanced-pane";

  const header = document.createElement("div");
  header.className = "easyuse-anima-advanced-pane-title";
  const heading = document.createElement("span");
  heading.textContent = title;
  const actions = document.createElement("div");
  actions.className = "easyuse-anima-advanced-actions";
  const addButton = (type, label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.disabled = type === "naia" && hasPositiveNaia(node);
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      addAdvancedField(node, pane, type);
    });
    actions.append(button);
  };
  addButton("quality", "+ Quality");
  addButton("artist", "+ Artist");
  addButton("general", "+ General");
  if (pane === "positive") {
    addButton("naia", "+ NAIA");
  }
  header.append(heading, actions);
  section.append(header);

  const fields = advancedPaneFields(node, pane);
  if (!fields.length) {
    const empty = document.createElement("div");
    empty.className = "easyuse-anima-empty-pane";
    empty.textContent = "No fields";
    section.append(empty);
  } else {
    for (const field of fields) {
      section.append(createAdvancedFieldElement(node, field));
    }
  }
  return section;
}

function renderAdvancedEditor(node) {
  const editor = node.__easyuseAnimaAdvancedEditorEl;
  if (!editor) {
    return;
  }
  node.__easyuseAnimaAdvancedFields = parseAdvancedFields(node);
  editor.innerHTML = "";
  editor.style.width = `${advancedEditorWidth(node)}px`;
  editor.style.maxWidth = `${advancedEditorWidth(node)}px`;
  editor.classList.toggle("is-narrow", Number(node.size?.[0] || 0) < 620);
  const panes = document.createElement("div");
  panes.className = "easyuse-anima-advanced-panes";
  panes.append(
    createAdvancedPane(node, "positive", "Positive Prompt"),
    createAdvancedPane(node, "negative", "Negative Prompt"),
  );
  editor.append(createAdvancedControlBar(node), panes);
  writeAdvancedFields(node, node.__easyuseAnimaAdvancedFields);
  syncAdvancedNodeSize(node);
}

function hookAdvancedNode(node) {
  ensureAdvancedStyle();
  installAdvancedSaveSync();
  ensureAdvancedWidgetValue(node);
  hideAdvancedInternalWidget(node, "advanced_fields");
  hideAdvancedControlWidgets(node);
  node.serialize_widgets = true;
  if (!node.__easyuseAnimaAdvancedEditorEl) {
    const editor = document.createElement("div");
    editor.className = "easyuse-anima-advanced-editor";
    node.__easyuseAnimaAdvancedEditorEl = editor;
    node.addDOMWidget?.("easyuse_anima_advanced_editor", "EasyUseAnimaAdvancedEditor", editor, {
      serialize: false,
      hideOnZoom: false,
      getMinHeight: () => Math.max(220, editor.scrollHeight || editor.offsetHeight || 220),
    });
  }
  renderAdvancedEditor(node);
}

function syncAdvancedValues(node, serialized = null) {
  const fields = collectAdvancedEditorFields(node);
  writeAdvancedFields(node, fields);
  if (!serialized || !Array.isArray(node.widgets) || !Array.isArray(serialized.widgets_values)) {
    return;
  }
  const fieldsValue = advancedWidget(node)?.value || JSON.stringify(fields);
  syncAdvancedFieldsBackup(node, fieldsValue);
  serialized.properties ||= {};
  serialized.properties[ADVANCED_FIELDS_PROPERTY] = fieldsValue;

  for (const name of Object.keys(ADVANCED_WIDGET_INDEX)) {
    const index = ADVANCED_WIDGET_INDEX[name];
    const widget = findWidget(node, name);
    while (serialized.widgets_values.length <= index) {
      serialized.widgets_values.push(null);
    }
    if (name === "advanced_fields") {
      serialized.widgets_values[index] = fieldsValue;
    } else if (widget) {
      serialized.widgets_values[index] = widget.value;
    }
  }
}

function applyAdvancedExecutedInputs(node, message) {
  const payload = firstValue(message?.prompt_studio_advanced, null);
  if (!payload || typeof payload !== "object") {
    return;
  }
  node.__easyuseAnimaAdvancedFieldInputValues =
    payload.field_inputs && typeof payload.field_inputs === "object" ? payload.field_inputs : {};
  const widget = advancedWidget(node);
  if (widget && payload.advanced_fields != null) {
    widget.value = String(payload.advanced_fields);
    syncAdvancedFieldsBackup(node, widget.value);
  }
  const useNaia = findWidget(node, "use_naia");
  if (useNaia && payload.use_naia != null) {
    useNaia.value = !!payload.use_naia;
  }
  renderAdvancedEditor(node);
}

function isAdvancedNode(node) {
  return node?.type === ADVANCED_NODE_TYPE || node?.comfyClass === ADVANCED_NODE_TYPE;
}

function syncAllAdvancedNodes() {
  const nodes = app.graph?._nodes || [];
  for (const node of nodes) {
    if (isAdvancedNode(node)) {
      syncAdvancedValues(node);
    }
  }
}

function installAdvancedSaveSync() {
  const graphProto = globalThis.LGraph?.prototype || app.graph?.constructor?.prototype;
  if (graphProto?.serialize && !graphProto.serialize.__easyuseAnimaAdvancedWrapped) {
    const serialize = graphProto.serialize;
    graphProto.serialize = function () {
      syncAllAdvancedNodes();
      return serialize.apply(this, arguments);
    };
    graphProto.serialize.__easyuseAnimaAdvancedWrapped = true;
  }

  if (app.queuePrompt && !app.queuePrompt.__easyuseAnimaAdvancedWrapped) {
    const queuePrompt = app.queuePrompt;
    app.queuePrompt = function () {
      syncAllAdvancedNodes();
      return queuePrompt.apply(this, arguments);
    };
    app.queuePrompt.__easyuseAnimaAdvancedWrapped = true;
  }
}

app.registerExtension({
  name: "easyuse-anima.prompt-studio",
  async setup() {
    installMiddlePanForwarder();
    installAdvancedSaveSync();
    await loadPromptStudioSettings();
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (
      nodeData.name !== NODE_TYPE
      && nodeData.name !== ADVANCED_NODE_TYPE
      && nodeData.name !== EXTEND_NODE_TYPE
    ) {
      return;
    }

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE) {
        requestAnimationFrame(() => hookAdvancedNode(this));
      } else {
        hookStudioNode(this);
      }
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (serialized) {
      onConfigure?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE) {
        captureAdvancedConfigure(this, serialized);
        requestAnimationFrame(() => hookAdvancedNode(this));
      } else {
        hookStudioNode(this);
      }
    };

    const onResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function () {
      const result = onResize?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE) {
        syncAdvancedNodeSize(this);
        return result;
      }
      if (isExtendNode(this)) {
        applyExtendSlotVisibility(this);
        renderExtendSlotControls(this);
      }
      rebalanceStudioInputHeights(this);
      return result;
    };

    const onSerialize = nodeType.prototype.onSerialize;
    nodeType.prototype.onSerialize = function (serialized) {
      const result = onSerialize?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE) {
        syncAdvancedValues(this, serialized);
      } else {
        syncStudioValues(this, serialized);
      }
      return result;
    };

    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      if (nodeData.name === ADVANCED_NODE_TYPE) {
        applyAdvancedExecutedInputs(this, message);
      } else {
        applyExecutedInputs(this, message);
      }
    };
  },
});
