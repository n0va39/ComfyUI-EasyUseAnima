import { app } from "../../../scripts/app.js";

const TARGETS = {
  EasyUseAnimaPromptBuilder: new Set([
    "quality_tags",
    "trigger_and_artist_tags",
    "lora_trigger_tags",
    "prompt",
    "trailing_quality_tags",
  ]),
  EasyUseAnimaPromptStudio: new Set([
    "quality_tags",
    "trigger_and_artist_tags",
    "lora_trigger_tags",
    "prompt",
    "trailing_quality_tags",
  ]),
  EasyUseAnimaPromptCorrector: new Set([
    "prompt",
    "artist_overrides",
    "artist_exclusions",
  ]),
};

const EXCLUDED_NODE_PATTERNS = [
  /lora\s*stacker/i,
  /loramanager/i,
  /lora[_\s-]*manager/i,
  /lora manager/i,
];

const EXCLUDED_INPUT_TYPE_PATTERNS = [
  /autocomplete/i,
  /lora/i,
  /embedding/i,
  /checkpoint/i,
  /model/i,
];

const GENERIC_NODE_PATTERNS = [
  /primitive.*string/i,
  /string.*primitive/i,
  /string.*multiline/i,
  /multiline.*string/i,
  /text/i,
  /prompt/i,
];

const MAX_RESULTS = 20;
const MIN_QUERY_LENGTH = 1;
const cache = new Map();

let popup = null;
let activeState = null;
let activeRefreshFrame = null;

function ensureStyle() {
  if (document.getElementById("easyuse-anima-autocomplete-style")) {
    return;
  }
  const style = document.createElement("style");
  style.id = "easyuse-anima-autocomplete-style";
  style.textContent = `
    .easyuse-anima-autocomplete {
      position: fixed;
      z-index: 100000;
      max-width: 520px;
      min-width: 280px;
      max-height: 280px;
      overflow: auto;
      overscroll-behavior: contain;
      border: 1px solid rgba(128, 128, 128, 0.45);
      border-radius: 7px;
      background: var(--comfy-menu-bg, #202124);
      color: var(--input-text, #ddd);
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35);
      font: 12px/1.35 sans-serif;
    }
    .easyuse-anima-autocomplete.hidden {
      display: none;
    }
    .easyuse-anima-autocomplete-item {
      padding: 6px 8px;
      cursor: pointer;
      border-bottom: 1px solid rgba(128, 128, 128, 0.16);
    }
    .easyuse-anima-autocomplete-item:last-child {
      border-bottom: 0;
    }
    .easyuse-anima-autocomplete-item.active,
    .easyuse-anima-autocomplete-item:hover {
      background: rgba(99, 102, 241, 0.28);
    }
    .easyuse-anima-autocomplete-tag {
      font-weight: 700;
    }
    .easyuse-anima-autocomplete-meta {
      margin-left: 6px;
      opacity: 0.62;
      font-size: 11px;
    }
    .easyuse-anima-autocomplete-desc {
      margin-top: 2px;
      opacity: 0.78;
      white-space: normal;
    }
  `;
  document.head.append(style);
}

function ensurePopup() {
  ensureStyle();
  if (popup) {
    return popup;
  }
  popup = document.createElement("div");
  popup.className = "easyuse-anima-autocomplete hidden";
  document.body.append(popup);
  return popup;
}

function hidePopup() {
  if (popup) {
    popup.classList.add("hidden");
    popup.replaceChildren();
  }
  activeState = null;
}

function refreshActiveAutocomplete() {
  if (!activeState?.input || document.activeElement !== activeState.input) {
    hidePopup();
    return;
  }
  activeState.reposition?.();
  activeState.refresh?.();
}

function scheduleActiveRefresh() {
  if (activeRefreshFrame != null) {
    cancelAnimationFrame(activeRefreshFrame);
  }
  activeRefreshFrame = requestAnimationFrame(() => {
    activeRefreshFrame = null;
    refreshActiveAutocomplete();
  });
}

function inputTypeName(inputSpec) {
  if (Array.isArray(inputSpec)) {
    return String(inputSpec[0] || "");
  }
  return String(inputSpec || "");
}

function inputOptions(inputSpec) {
  if (Array.isArray(inputSpec) && typeof inputSpec[1] === "object" && inputSpec[1] !== null) {
    return inputSpec[1];
  }
  return {};
}

function allInputSpecs(nodeData) {
  const inputs = nodeData?.input || {};
  const specs = [];
  for (const group of ["required", "optional"]) {
    const values = inputs[group] || {};
    for (const [name, spec] of Object.entries(values)) {
      specs.push([name, spec]);
    }
  }
  return specs;
}

function isExcludedInput(inputSpec) {
  const type = inputTypeName(inputSpec);
  const options = inputOptions(inputSpec);
  const values = [
    type,
    options.widgetType,
    options.placeholder,
    options.tooltip,
  ].filter(Boolean).map((value) => String(value));
  return values.some((value) => EXCLUDED_INPUT_TYPE_PATTERNS.some((pattern) => pattern.test(value)));
}

function isGenericStringNode(nodeData) {
  const values = [nodeData?.name, nodeData?.display_name, nodeData?.category]
    .filter(Boolean)
    .map((value) => String(value));
  return values.some((value) => GENERIC_NODE_PATTERNS.some((pattern) => pattern.test(value)));
}

function isPromptLikeWidgetName(name) {
  return /prompt|tag|text|string|caption|positive|negative/i.test(String(name || ""));
}

function isTargetStringInput(nodeData, name, inputSpec) {
  const type = inputTypeName(inputSpec);
  const options = inputOptions(inputSpec);
  if (!type.split(",").map((item) => item.trim()).includes("STRING")) {
    return false;
  }
  if (isExcludedInput(inputSpec)) {
    return false;
  }
  if (options.multiline === true) {
    return isGenericStringNode(nodeData) || isPromptLikeWidgetName(name);
  }
  return isGenericStringNode(nodeData) && isPromptLikeWidgetName(name);
}

function targetWidgets(nodeData) {
  if (TARGETS[nodeData.name]) {
    return TARGETS[nodeData.name];
  }
  if (shouldSkipNode(null, nodeData)) {
    return null;
  }
  const names = new Set();
  for (const [name, spec] of allInputSpecs(nodeData)) {
    if (isTargetStringInput(nodeData, name, spec)) {
      names.add(name);
    }
  }
  return names.size ? names : null;
}

function shouldSkipNode(node, nodeData) {
  const values = [nodeData?.name, nodeData?.display_name, nodeData?.category, node?.type, node?.title]
    .filter(Boolean)
    .map((value) => String(value));
  return values.some((value) => EXCLUDED_NODE_PATTERNS.some((pattern) => pattern.test(value)));
}

function findInputEl(widget) {
  const input = widget?.inputEl;
  if (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement) {
    return input;
  }
  return null;
}

function currentToken(input) {
  const value = input.value || "";
  const caret = input.selectionStart ?? value.length;
  let start = caret;
  while (start > 0 && value[start - 1] !== "," && value[start - 1] !== "\n") {
    start -= 1;
  }
  let end = caret;
  while (end < value.length && value[end] !== "," && value[end] !== "\n") {
    end += 1;
  }
  const raw = value.slice(start, caret);
  return {
    value,
    start,
    end,
    caret,
    query: raw.trim(),
  };
}

function positionPopup(input) {
  const menu = ensurePopup();
  const rect = input.getBoundingClientRect();
  const top = Math.min(window.innerHeight - 80, rect.bottom + 4);
  const left = Math.min(window.innerWidth - 300, Math.max(4, rect.left));
  menu.style.left = `${left}px`;
  menu.style.top = `${Math.max(4, top)}px`;
  menu.style.width = `${Math.max(280, Math.min(rect.width, 520))}px`;
}

async function search(query) {
  const key = query.toLocaleLowerCase();
  if (cache.has(key)) {
    return cache.get(key);
  }
  const response = await fetch(
    `/easyuse_anima/autocomplete?q=${encodeURIComponent(query)}&limit=${MAX_RESULTS}`,
  );
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  const results = Array.isArray(data.results) ? data.results : [];
  cache.set(key, results);
  return results;
}

function setActive(index) {
  if (!activeState) {
    return;
  }
  const count = activeState.results.length;
  if (!count) {
    return;
  }
  activeState.index = (index + count) % count;
  [...ensurePopup().children].forEach((child, childIndex) => {
    child.classList.toggle("active", childIndex === activeState.index);
  });
}

function commitSuggestion(state, entry) {
  const token = currentToken(state.input);
  const before = token.value.slice(0, token.start);
  const after = token.value.slice(token.end);
  const prefix = before && !/[\s,\n]$/.test(before) ? `${before} ` : before;
  const suffix = after.startsWith(",") || after.startsWith("\n") || after === "" ? after : `, ${after}`;
  const insert = entry.tag;
  state.input.value = `${prefix}${insert}${suffix}`;
  const caret = prefix.length + insert.length;
  state.input.setSelectionRange(caret, caret);
  state.input.dispatchEvent(new Event("input", { bubbles: true }));
  state.widget.value = state.input.value;
  state.widget.callback?.(state.input.value);
  hidePopup();
}

function renderResults(state, results) {
  const menu = ensurePopup();
  menu.replaceChildren();
  activeState = { ...state, results, index: 0 };

  if (!results.length) {
    hidePopup();
    return;
  }

  for (const [index, entry] of results.entries()) {
    const item = document.createElement("div");
    item.className = "easyuse-anima-autocomplete-item";
    if (index === 0) {
      item.classList.add("active");
    }

    const top = document.createElement("div");
    const tag = document.createElement("span");
    tag.className = "easyuse-anima-autocomplete-tag";
    tag.textContent = entry.tag || "";

    const meta = document.createElement("span");
    meta.className = "easyuse-anima-autocomplete-meta";
    const count = Number(entry.count || 0).toLocaleString();
    meta.textContent = `${entry.category || "tag"} · ${count}`;
    top.append(tag, meta);
    item.append(top);

    if (entry.description) {
      const desc = document.createElement("div");
      desc.className = "easyuse-anima-autocomplete-desc";
      desc.textContent = entry.description;
      item.append(desc);
    }

    item.addEventListener("mousedown", (event) => {
      event.preventDefault();
      commitSuggestion(activeState, entry);
    });
    menu.append(item);
  }

  positionPopup(state.input);
  menu.classList.remove("hidden");
}

function debounce(fn, delay = 120) {
  let timer = null;
  const wrapped = (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
  wrapped.cancel = () => clearTimeout(timer);
  return wrapped;
}

function hookWidget(node, widget) {
  const input = findInputEl(widget);
  if (!input || input.__easyuseAnimaAutocomplete) {
    return;
  }

  let composing = false;
  let updateSeq = 0;
  const state = { node, widget, input };

  const updateNow = async () => {
    if (composing || document.activeElement !== input) {
      return;
    }
    const token = currentToken(input);
    if (token.query.length < MIN_QUERY_LENGTH) {
      hidePopup();
      return;
    }
    const seq = ++updateSeq;
    try {
      const results = await search(token.query);
      if (document.activeElement === input && seq === updateSeq) {
        renderResults(state, results);
      }
    } catch {
      hidePopup();
    }
  };
  const update = debounce(updateNow);
  const updateFromCaret = () => {
    update.cancel();
    updateNow();
  };
  const updateAfterCaretMove = () => {
    update.cancel();
    requestAnimationFrame(updateNow);
    setTimeout(updateNow, 0);
  };
  state.refresh = updateFromCaret;
  state.reposition = () => positionPopup(input);

  input.addEventListener("compositionstart", () => {
    composing = true;
  });
  input.addEventListener("compositionend", () => {
    composing = false;
    updateAfterCaretMove();
  });
  input.addEventListener("input", update);
  input.addEventListener("focus", updateFromCaret);
  input.addEventListener("click", updateAfterCaretMove);
  input.addEventListener("mousedown", updateAfterCaretMove);
  input.addEventListener("mouseup", updateAfterCaretMove);
  input.addEventListener("pointerup", updateAfterCaretMove);
  input.addEventListener("keyup", (event) => {
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", "PageUp", "PageDown"].includes(event.key)) {
      updateAfterCaretMove();
    }
  });
  input.addEventListener("select", updateAfterCaretMove);
  input.addEventListener("blur", () => {
    setTimeout(() => {
      if (activeState?.input === input) {
        hidePopup();
      }
    }, 120);
  });
  input.addEventListener("keydown", (event) => {
    if (!activeState || activeState.input !== input) {
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive(activeState.index + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive(activeState.index - 1);
    } else if (event.key === "Enter" || event.key === "Tab") {
      event.preventDefault();
      commitSuggestion(activeState, activeState.results[activeState.index]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      hidePopup();
    }
  });

  input.__easyuseAnimaAutocomplete = true;
}

function hookNode(node, nodeData) {
  const names = targetWidgets(nodeData);
  if (!names || shouldSkipNode(node, nodeData)) {
    return;
  }
  for (const widget of node.widgets || []) {
    if (names.has(widget.name)) {
      hookWidget(node, widget);
    }
  }
}

document.addEventListener("scroll", (event) => {
  if (popup?.contains(event.target)) {
    return;
  }
  scheduleActiveRefresh();
}, true);
document.addEventListener("wheel", (event) => {
  if (popup?.contains(event.target)) {
    return;
  }
  scheduleActiveRefresh();
}, true);
document.addEventListener("selectionchange", scheduleActiveRefresh);
window.addEventListener("resize", scheduleActiveRefresh);

app.registerExtension({
  name: "easyuse-anima.autocomplete",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!targetWidgets(nodeData)) {
      return;
    }

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      hookNode(this, nodeData);
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      onConfigure?.apply(this, arguments);
      hookNode(this, nodeData);
    };
  },
});
