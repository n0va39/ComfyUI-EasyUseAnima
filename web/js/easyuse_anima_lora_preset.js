import { app } from "../../../scripts/app.js";

const NODE_TYPE = "EasyUseAnimaLoraPreset";
const MAX_PROFILES = 16;
const LORA_SYNTAX_RE = /<\s*lora\s*:\s*([^:>]+?)\s*:\s*([-+]?\d*\.?\d+)(?:\s*:\s*([-+]?\d*\.?\d+))?\s*>/gi;
const WIDGET_INDEX = {
  stylePrompt: 0,
  profileIndex: 1,
  profileCount: 2,
  text: 3,
  loras: 4,
  profileData: 5,
};
const MIN_NODE_WIDTH = 460;
let loraManagerModulesPromise = null;

async function loadLoraManagerModules() {
  if (!loraManagerModulesPromise) {
    loraManagerModulesPromise = import("../../comfyui-lora-manager/autocomplete.js")
    .then((autocompleteModule) => ({
      AutoComplete: autocompleteModule.AutoComplete,
    })).catch((error) => {
      console.warn("EasyUse Anima: LoraManager autocomplete is unavailable.", error);
      return null;
    });
  }
  return loraManagerModulesPromise;
}

function findWidget(node, name) {
  return node.__easyuseAnimaHiddenWidgets?.[name]
    || node.widgets?.find((widget) => widget.name === name);
}

function findInputEl(widget) {
  const input = widget?.inputEl;
  if (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement) {
    return input;
  }
  return null;
}

function widgetValue(widget, fallback = "") {
  if (!widget) {
    return fallback;
  }
  const input = findInputEl(widget);
  if (input) {
    return input.value ?? fallback;
  }
  return widget.value ?? fallback;
}

function setWidgetValue(widget, value) {
  if (!widget) {
    return;
  }
  widget.value = value;
  const input = findInputEl(widget);
  if (input && input.value !== value) {
    input.value = value;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }
  widget.callback?.(value);
}

function parseProfileData(widget) {
  try {
    const value = widgetValue(widget, "{}");
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function looksLikeProfileData(value) {
  if (typeof value !== "string") {
    return false;
  }
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" && !Array.isArray(parsed);
  } catch {
    return false;
  }
}

function normalizeSerializedWidgets(info) {
  const values = info?.widgets_values;
  if (!Array.isArray(values)) {
    return;
  }

  if (!Array.isArray(values[WIDGET_INDEX.loras])) {
    const lorasIndex = values.findIndex((value, index) => (
      index > WIDGET_INDEX.loras
      && Array.isArray(value)
      && value.every((item) => item && typeof item === "object" && "name" in item)
    ));
    values[WIDGET_INDEX.loras] = lorasIndex >= 0 ? values[lorasIndex] : [];
  }

  if (!looksLikeProfileData(values[WIDGET_INDEX.profileData])) {
    const profileDataIndex = values.findIndex((value, index) => (
      index > WIDGET_INDEX.profileData && looksLikeProfileData(value)
    ));
    if (profileDataIndex >= 0) {
      values[WIDGET_INDEX.profileData] = values[profileDataIndex];
    }
  }
}

function writeProfileData(widget, data) {
  setWidgetValue(widget, JSON.stringify(data));
}

function profileKey(index) {
  return String(Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(index, 10) || 1)));
}

function profileCount(node) {
  const widget = findWidget(node, "profile_count");
  return Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(widgetValue(widget, 4), 10) || 4));
}

function setProfileCount(node, count) {
  const nextCount = Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(count, 10) || 1));
  node.__easyuseAnimaSuppressProfileCountCallback = true;
  try {
    setWidgetValue(findWidget(node, "profile_count"), nextCount);
  } finally {
    node.__easyuseAnimaSuppressProfileCountCallback = false;
  }
}

function wrapProfileIndex(index, count) {
  const profileCountValue = Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(count, 10) || 1));
  const profileIndexValue = Math.max(1, Number.parseInt(index, 10) || 1);
  return ((profileIndexValue - 1) % profileCountValue) + 1;
}

function selectedProfileIndex(node) {
  const widget = findWidget(node, "profile_index");
  return wrapProfileIndex(widgetValue(widget, 1), profileCount(node));
}

function setProfileIndex(node, index) {
  const nextIndex = wrapProfileIndex(index, profileCount(node));
  node.__easyuseAnimaSuppressProfileIndexCallback = true;
  try {
    setWidgetValue(findWidget(node, "profile_index"), nextIndex);
  } finally {
    node.__easyuseAnimaSuppressProfileIndexCallback = false;
  }
}

function activeProfileIndex(node) {
  return wrapProfileIndex(node.__easyuseAnimaActiveProfileIndex || selectedProfileIndex(node), profileCount(node));
}

function lorasWidgetValue(node) {
  const widget = findWidget(node, "loras");
  const value = widgetValue(widget, []);
  if (value && typeof value === "object" && Array.isArray(value.__value__)) {
    return value.__value__;
  }
  if (Array.isArray(value)) {
    return value;
  }
  return [];
}

function setLorasWidgetValue(node, loras) {
  const widget = findWidget(node, "loras");
  if (!widget) {
    return;
  }
  const value = Array.isArray(loras) ? loras : [];
  widget.value = value;
  widget.callback?.(value);
}

function parseLoraSyntaxText(text) {
  const loras = [];
  LORA_SYNTAX_RE.lastIndex = 0;
  let match = LORA_SYNTAX_RE.exec(String(text || ""));
  while (match) {
    const strength = Number(match[2]);
    const clipStrength = match[3] == null ? strength : Number(match[3]);
    if (match[1] && Number.isFinite(strength) && Number.isFinite(clipStrength)) {
      loras.push({
        name: match[1].trim(),
        strength,
        clipStrength,
        active: true,
      });
    }
    match = LORA_SYNTAX_RE.exec(String(text || ""));
  }
  return loras;
}

function mergeParsedLoras(parsedLoras, currentLoras) {
  const byName = new Map(parsedLoras.map((lora) => [lora.name, lora]));
  const result = [];
  const used = new Set();

  for (const current of currentLoras) {
    const parsed = byName.get(current.name);
    if (!parsed) {
      continue;
    }
    result.push({
      ...current,
      strength: parsed.strength,
      clipStrength: parsed.clipStrength,
      active: current.active ?? true,
    });
    used.add(current.name);
  }

  for (const parsed of parsedLoras) {
    if (!used.has(parsed.name)) {
      result.push(parsed);
    }
  }
  return result;
}

function lorasSignature(loras) {
  return JSON.stringify((Array.isArray(loras) ? loras : []).map((lora) => ({
    name: lora.name,
    strength: lora.strength,
    clipStrength: lora.clipStrength,
    active: lora.active ?? true,
  })));
}

function syncTextToLoras(node) {
  if (node.__easyuseAnimaLoadingProfile) {
    return;
  }
  const textWidget = findWidget(node, "text");
  const lorasWidget = findWidget(node, "loras");
  if (!textWidget || !lorasWidget) {
    return;
  }
  const input = findInputEl(textWidget);
  if (input) {
    textWidget.value = input.value;
  }
  const text = String(widgetValue(textWidget, ""));
  const parsedLoras = parseLoraSyntaxText(text);
  if (!parsedLoras.length && text.trim()) {
    return;
  }
  const mergedLoras = parsedLoras.length ? mergeParsedLoras(parsedLoras, lorasWidgetValue(node)) : [];
  if (lorasSignature(mergedLoras) === lorasSignature(lorasWidgetValue(node))) {
    saveCurrentProfile(node);
    return;
  }
  setLorasWidgetValue(node, mergedLoras);
  saveCurrentProfile(node);
}

function scheduleLoraSync(node, delay = 120) {
  clearTimeout(node.__easyuseAnimaLoraSyncTimer);
  node.__easyuseAnimaLoraSyncTimer = setTimeout(() => {
    node.__easyuseAnimaLoraSyncTimer = null;
    syncTextToLoras(node);
  }, delay);
}

function currentProfile(node) {
  return {
    style_prompt: String(widgetValue(findWidget(node, "style_prompt"), "")),
    text: String(widgetValue(findWidget(node, "text"), "")),
    loras: lorasWidgetValue(node),
  };
}

function defaultProfileName(index) {
  return `Profile ${index}`;
}

function saveProfile(node, index) {
  const dataWidget = findWidget(node, "profile_data");
  if (!dataWidget) {
    return;
  }
  const data = parseProfileData(dataWidget);
  const key = profileKey(index);
  const previous = data[key] && typeof data[key] === "object" ? data[key] : {};
  data[key] = {
    ...currentProfile(node),
    name: String(previous.name || defaultProfileName(index)),
  };
  writeProfileData(dataWidget, data);
}

function saveCurrentProfile(node) {
  if (node.__easyuseAnimaLoadingProfile) {
    return;
  }
  saveProfile(node, activeProfileIndex(node));
}

function emptyProfile(index = 1) {
  return {
    name: defaultProfileName(index),
    style_prompt: "",
    text: "",
    loras: [],
  };
}

function loadProfile(node, index, options = {}) {
  const dataWidget = findWidget(node, "profile_data");
  if (!dataWidget) {
    return;
  }
  const data = parseProfileData(dataWidget);
  const key = profileKey(index);
  if (!Object.prototype.hasOwnProperty.call(data, key)) {
    data[key] = options.initializeFromCurrent
      ? { ...currentProfile(node), name: defaultProfileName(index) }
      : emptyProfile(index);
    writeProfileData(dataWidget, data);
  }
  const profile = data[key] ?? {};
  node.__easyuseAnimaLoadingProfile = true;
  try {
    setWidgetValue(findWidget(node, "style_prompt"), String(profile.style_prompt ?? ""));
    setWidgetValue(findWidget(node, "text"), String(profile.text ?? ""));
    setLorasWidgetValue(node, Array.isArray(profile.loras) ? profile.loras : []);
  } finally {
    node.__easyuseAnimaLoadingProfile = false;
  }
}

function switchProfile(node, index) {
  const nextIndex = wrapProfileIndex(index, profileCount(node));
  const currentIndex = activeProfileIndex(node);
  if (nextIndex === currentIndex) {
    renderTabs(node);
    return;
  }
  saveProfile(node, currentIndex);
  setProfileIndex(node, nextIndex);
  loadProfile(node, nextIndex);
  node.__easyuseAnimaActiveProfileIndex = nextIndex;
  renderTabs(node);
  node.setDirtyCanvas?.(true, true);
}

function profileLabel(node, index) {
  const dataWidget = findWidget(node, "profile_data");
  const profile = parseProfileData(dataWidget)[profileKey(index)];
  return String(profile?.name || defaultProfileName(index));
}

function addProfile(node) {
  const count = profileCount(node);
  if (count >= MAX_PROFILES) {
    return;
  }
  saveCurrentProfile(node);
  const nextIndex = count + 1;
  const dataWidget = findWidget(node, "profile_data");
  const data = parseProfileData(dataWidget);
  data[profileKey(nextIndex)] = emptyProfile(nextIndex);
  writeProfileData(dataWidget, data);
  setProfileCount(node, nextIndex);
  switchProfile(node, nextIndex);
}

function renameProfile(node, index) {
  saveCurrentProfile(node);
  const dataWidget = findWidget(node, "profile_data");
  const data = parseProfileData(dataWidget);
  const key = profileKey(index);
  const currentName = String(data[key]?.name || defaultProfileName(index));
  const nextName = window.prompt("Profile name", currentName);
  if (nextName == null) {
    return;
  }
  const cleaned = nextName.trim();
  data[key] = {
    ...(data[key] && typeof data[key] === "object" ? data[key] : emptyProfile(index)),
    name: cleaned || defaultProfileName(index),
  };
  writeProfileData(dataWidget, data);
  renderTabs(node);
  node.setDirtyCanvas?.(true, true);
}

function deleteProfile(node, index) {
  const count = profileCount(node);
  if (count <= 1) {
    return;
  }

  const label = profileLabel(node, index);
  if (!window.confirm(`Delete profile "${label}"?`)) {
    return;
  }

  const activeIndex = activeProfileIndex(node);
  if (index !== activeIndex) {
    saveProfile(node, activeIndex);
  }

  const dataWidget = findWidget(node, "profile_data");
  const data = parseProfileData(dataWidget);
  const nextData = {};
  let nextWriteIndex = 1;
  for (let sourceIndex = 1; sourceIndex <= count; sourceIndex += 1) {
    if (sourceIndex === index) {
      continue;
    }
    const source = data[profileKey(sourceIndex)] || emptyProfile(nextWriteIndex);
    nextData[profileKey(nextWriteIndex)] = {
      ...source,
      name: String(source.name || defaultProfileName(nextWriteIndex)),
    };
    nextWriteIndex += 1;
  }

  writeProfileData(dataWidget, nextData);
  const nextCount = count - 1;
  setProfileCount(node, nextCount);
  const nextActive = index === activeIndex
    ? Math.min(index, nextCount)
    : activeIndex > index
      ? activeIndex - 1
      : activeIndex;
  node.__easyuseAnimaActiveProfileIndex = nextActive;
  setProfileIndex(node, nextActive);
  loadProfile(node, nextActive);
  renderTabs(node);
  node.setDirtyCanvas?.(true, true);
}

function hideInternalWidget(node, name) {
  const widget = findWidget(node, name);
  if (!widget || widget.__easyuseAnimaHidden) {
    return;
  }
  widget.__easyuseAnimaHidden = true;
  widget.hidden = true;
  widget.serialize = true;
  widget.computeSize = () => [0, 0];
  widget.draw = () => {};
  widget.type = "hidden";
}

function detachInternalWidget(node, name) {
  const widget = findWidget(node, name);
  if (!widget || !node.widgets?.includes(widget)) {
    return;
  }
  hideInternalWidget(node, name);
  node.__easyuseAnimaHiddenWidgets ??= {};
  node.__easyuseAnimaHiddenWidgets[name] = widget;
  const index = node.widgets.indexOf(widget);
  if (index >= 0) {
    node.widgets.splice(index, 1);
  }
}

function finalizeInternalWidgets(node) {
  detachInternalWidget(node, "profile_data");
  detachInternalWidget(node, "profile_count");
}

function enforceNodeLayout(node) {
  if (!node?.size || typeof node.setSize !== "function") {
    return;
  }
  const currentWidth = Number(node.size[0]) || 0;
  const currentHeight = Number(node.size[1]) || 0;
  const computed = typeof node.computeSize === "function" ? node.computeSize() : null;
  const nextWidth = currentWidth < MIN_NODE_WIDTH ? MIN_NODE_WIDTH : currentWidth;
  const nextHeight = Math.max(currentHeight, Number(computed?.[1]) || 0);
  if (nextWidth !== currentWidth || nextHeight !== currentHeight) {
    node.setSize([nextWidth, nextHeight]);
  }
  node.setDirtyCanvas?.(true, true);
}

function ensureLoraStackInput(node) {
  if (!node.inputs?.some((input) => input.name === "lora_stack")) {
    node.addInput?.("lora_stack", "LORA_STACK");
  }
}

function styleTabsContainer(container) {
  container.style.display = "flex";
  container.style.flexWrap = "nowrap";
  container.style.gap = "4px";
  container.style.padding = "4px 0";
  container.style.width = "100%";
  container.style.minWidth = "0";
  container.style.boxSizing = "border-box";
  container.style.alignItems = "center";
}

function styleProfileButton(button, width = "28px") {
  button.style.height = "26px";
  button.style.width = width;
  button.style.flex = `0 0 ${width}`;
  button.style.border = "1px solid #555";
  button.style.borderRadius = "4px";
  button.style.background = "#252525";
  button.style.color = "#d4d4d4";
  button.style.cursor = "pointer";
  button.style.fontSize = "12px";
  button.style.padding = "0";
}

function stopCanvasEvent(event) {
  event.stopPropagation();
}

function closeProfileMenu(node) {
  const state = node.__easyuseAnimaProfileMenu;
  if (!state) {
    return;
  }
  state.menu.remove();
  document.removeEventListener("pointerdown", state.closeHandler, true);
  window.removeEventListener("resize", state.closeHandler, true);
  node.__easyuseAnimaProfileMenu = null;
}

function openProfileMenu(node, anchor) {
  closeProfileMenu(node);
  const count = profileCount(node);
  const selected = activeProfileIndex(node);
  const rect = anchor.getBoundingClientRect();
  const menu = document.createElement("div");
  menu.style.position = "fixed";
  menu.style.left = `${rect.left}px`;
  menu.style.top = `${rect.bottom + 4}px`;
  menu.style.width = `${Math.max(180, rect.width)}px`;
  menu.style.maxHeight = "220px";
  menu.style.overflowY = "auto";
  menu.style.boxSizing = "border-box";
  menu.style.padding = "4px";
  menu.style.border = "1px solid #555";
  menu.style.borderRadius = "4px";
  menu.style.background = "#202020";
  menu.style.boxShadow = "0 8px 22px rgba(0, 0, 0, 0.42)";
  menu.style.zIndex = "10000";
  menu.addEventListener("pointerdown", stopCanvasEvent);
  menu.addEventListener("mousedown", stopCanvasEvent);
  menu.addEventListener("click", stopCanvasEvent);

  for (let index = 1; index <= count; index += 1) {
    const option = document.createElement("button");
    option.type = "button";
    option.textContent = `${index}. ${profileLabel(node, index)}`;
    option.style.display = "block";
    option.style.width = "100%";
    option.style.height = "26px";
    option.style.padding = "0 7px";
    option.style.margin = "0";
    option.style.border = "0";
    option.style.borderRadius = "3px";
    option.style.textAlign = "left";
    option.style.overflow = "hidden";
    option.style.textOverflow = "ellipsis";
    option.style.whiteSpace = "nowrap";
    option.style.background = index === selected ? "#2f6feb" : "transparent";
    option.style.color = index === selected ? "#ffffff" : "#d4d4d4";
    option.style.cursor = "pointer";
    option.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeProfileMenu(node);
      switchProfile(node, index);
    });
    menu.appendChild(option);
  }

  const closeHandler = (event) => {
    if (event.target === anchor || menu.contains(event.target)) {
      return;
    }
    closeProfileMenu(node);
  };
  document.body.appendChild(menu);
  node.__easyuseAnimaProfileMenu = { menu, closeHandler };
  setTimeout(() => {
    document.addEventListener("pointerdown", closeHandler, true);
    window.addEventListener("resize", closeHandler, true);
  }, 0);
}

function renderTabs(node) {
  const container = node.__easyuseAnimaLoraPresetTabs;
  if (!container) {
    return;
  }
  closeProfileMenu(node);
  const count = profileCount(node);
  const selected = activeProfileIndex(node);
  container.replaceChildren();
  styleTabsContainer(container);
  container.addEventListener("pointerdown", stopCanvasEvent);
  container.addEventListener("mousedown", stopCanvasEvent);
  container.addEventListener("click", stopCanvasEvent);

  const selector = document.createElement("button");
  selector.type = "button";
  selector.textContent = `${selected}. ${profileLabel(node, selected)}`;
  selector.title = "Open profile selector. Double click: rename. Right click: delete.";
  selector.style.flex = "1 1 auto";
  selector.style.minWidth = "0";
  selector.style.maxWidth = "100%";
  selector.style.height = "26px";
  selector.style.boxSizing = "border-box";
  selector.style.background = "#252525";
  selector.style.color = "#d4d4d4";
  selector.style.border = "1px solid #555";
  selector.style.borderRadius = "4px";
  selector.style.padding = "0 22px 0 7px";
  selector.style.fontSize = "12px";
  selector.style.textAlign = "left";
  selector.style.overflow = "hidden";
  selector.style.textOverflow = "ellipsis";
  selector.style.whiteSpace = "nowrap";
  selector.style.cursor = "pointer";
  selector.style.position = "relative";
  selector.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (node.__easyuseAnimaProfileMenu) {
      closeProfileMenu(node);
    } else {
      openProfileMenu(node, selector);
    }
  });
  selector.addEventListener("dblclick", (event) => {
    event.preventDefault();
    event.stopPropagation();
    closeProfileMenu(node);
    renameProfile(node, activeProfileIndex(node));
  });
  selector.addEventListener("contextmenu", (event) => {
    event.preventDefault();
    event.stopPropagation();
    closeProfileMenu(node);
    deleteProfile(node, activeProfileIndex(node));
  });
  const arrow = document.createElement("span");
  arrow.textContent = "▾";
  arrow.style.position = "absolute";
  arrow.style.right = "7px";
  arrow.style.top = "3px";
  arrow.style.pointerEvents = "none";
  selector.appendChild(arrow);
  container.appendChild(selector);

  if (count < MAX_PROFILES) {
    const addButton = document.createElement("button");
    addButton.type = "button";
    addButton.textContent = "+";
    addButton.title = "Add profile";
    styleProfileButton(addButton);
    addButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      addProfile(node);
    });
    container.appendChild(addButton);
  }

  const renameButton = document.createElement("button");
  renameButton.type = "button";
  renameButton.textContent = "R";
  renameButton.title = "Rename selected profile";
  styleProfileButton(renameButton);
  renameButton.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    renameProfile(node, activeProfileIndex(node));
  });
  container.appendChild(renameButton);

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.textContent = "X";
  deleteButton.title = "Delete selected profile";
  styleProfileButton(deleteButton);
  deleteButton.disabled = count <= 1;
  if (deleteButton.disabled) {
    deleteButton.style.opacity = "0.45";
    deleteButton.style.cursor = "not-allowed";
  }
  deleteButton.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    deleteProfile(node, activeProfileIndex(node));
  });
  container.appendChild(deleteButton);
  enforceNodeLayout(node);
}

function ensureTabsWidget(node) {
  if (node.__easyuseAnimaLoraPresetTabs || typeof node.addDOMWidget !== "function") {
    return;
  }
  const container = document.createElement("div");
  node.__easyuseAnimaLoraPresetTabs = container;
  const tabsWidget = node.addDOMWidget("profile_tabs", "EASYUSE_ANIMA_LORA_PROFILE_TABS", container, {
    serialize: false,
    getMinHeight() {
      return 36;
    },
  });
  if (tabsWidget) {
    tabsWidget.serialize = false;
  }
  renderTabs(node);
}

function wrapWidgetCallback(node, name, callback) {
  const widget = findWidget(node, name);
  if (!widget || widget.__easyuseAnimaLoraWrapped) {
    return;
  }
  widget.__easyuseAnimaLoraWrapped = true;
  const previous = widget.callback;
  widget.callback = function (...args) {
    const result = previous?.apply(this, args);
    callback?.();
    return result;
  };
}

async function hookLoraManagerAutocomplete(node, attempt = 0) {
  const textWidget = findWidget(node, "text");
  const input = findInputEl(textWidget);
  if (!textWidget || !input) {
    if (attempt < 12) {
      setTimeout(() => hookLoraManagerAutocomplete(node, attempt + 1), 80);
    }
    return;
  }
  if (input.__easyuseAnimaLoraManagerAutocomplete) {
    return;
  }

  const modules = await loadLoraManagerModules();
  if (!modules?.AutoComplete) {
    return;
  }

  input.__easyuseAnimaLoraManagerAutocomplete = true;
  node.__easyuseAnimaLoraManagerAutocomplete = new modules.AutoComplete(input, "loras", {
    minChars: 1,
    maxItems: 50,
    pageSize: 20,
    visibleItems: 8,
    showPreview: false,
  });

  const sync = () => scheduleLoraSync(node);
  input.addEventListener("input", sync);
  input.addEventListener("change", sync);
  textWidget.callback = function (value) {
    const result = textWidget.__easyuseAnimaPreviousCallback?.call(this, value);
    sync();
    return result;
  };
  scheduleLoraSync(node, 0);
}

function syncAfterWidgetChange(node) {
  if (node.__easyuseAnimaLoadingProfile) {
    return;
  }
  saveCurrentProfile(node);
  renderTabs(node);
}

function initializeNode(node) {
  if (node.__easyuseAnimaLoraPresetInitialized) {
    return;
  }
  node.__easyuseAnimaLoraPresetInitialized = true;
  node.serialize_widgets = true;
  ensureLoraStackInput(node);
  ensureTabsWidget(node);
  hideInternalWidget(node, "profile_data");
  hideInternalWidget(node, "profile_count");
  enforceNodeLayout(node);

  wrapWidgetCallback(node, "style_prompt", () => syncAfterWidgetChange(node));
  wrapWidgetCallback(node, "text", () => syncAfterWidgetChange(node));
  wrapWidgetCallback(node, "loras", () => syncAfterWidgetChange(node));
  const textWidget = findWidget(node, "text");
  if (textWidget && !textWidget.__easyuseAnimaPreviousCallback) {
    textWidget.__easyuseAnimaPreviousCallback = textWidget.callback;
  }
  hookLoraManagerAutocomplete(node);
  wrapWidgetCallback(node, "profile_count", () => {
    if (node.__easyuseAnimaSuppressProfileCountCallback) {
      return;
    }
    renderTabs(node);
    saveCurrentProfile(node);
  });
  wrapWidgetCallback(node, "profile_index", () => {
    if (node.__easyuseAnimaSuppressProfileIndexCallback) {
      return;
    }
    const index = selectedProfileIndex(node);
    const currentIndex = activeProfileIndex(node);
    if (index !== currentIndex) {
      saveProfile(node, currentIndex);
    }
    loadProfile(node, index);
    node.__easyuseAnimaActiveProfileIndex = index;
    renderTabs(node);
  });

  const originalOnSerialize = node.onSerialize;
  node.onSerialize = function (workflowNode) {
    saveCurrentProfile(this);
    originalOnSerialize?.apply(this, arguments);
    const dataWidget = findWidget(this, "profile_data");
    if (workflowNode?.widgets_values && dataWidget) {
      workflowNode.widgets_values[WIDGET_INDEX.loras] = lorasWidgetValue(this);
      workflowNode.widgets_values[WIDGET_INDEX.profileData] = widgetValue(dataWidget, "{}");
    }
  };

  const originalOnConfigure = node.onConfigure;
  node.onConfigure = function (...args) {
    originalOnConfigure?.apply(this, args);
    window.requestAnimationFrame(() => {
      finalizeInternalWidgets(this);
      ensureTabsWidget(this);
      this.__easyuseAnimaActiveProfileIndex = selectedProfileIndex(this);
      loadProfile(this, selectedProfileIndex(this), { initializeFromCurrent: true });
      renderTabs(this);
      enforceNodeLayout(this);
    });
  };

  window.requestAnimationFrame(() => {
    finalizeInternalWidgets(node);
    node.__easyuseAnimaActiveProfileIndex = selectedProfileIndex(node);
    loadProfile(node, selectedProfileIndex(node), { initializeFromCurrent: true });
    renderTabs(node);
    enforceNodeLayout(node);
  });
}

app.registerExtension({
  name: "EasyUseAnima.LoraPreset",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== NODE_TYPE) {
      return;
    }

    const originalConfigure = nodeType.prototype.configure;
    nodeType.prototype.configure = function (info) {
      normalizeSerializedWidgets(info);
      return originalConfigure?.apply(this, arguments);
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function (...args) {
      const result = originalOnNodeCreated?.apply(this, args);
      initializeNode(this);
      return result;
    };
  },
});
