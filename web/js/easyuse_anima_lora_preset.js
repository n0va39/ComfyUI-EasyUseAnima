import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "EasyUseAnimaLoraPreset";
const MAX_PROFILES = 16;
const WIDGET_INDEX = {
  stylePrompt: 0,
  profileIndex: 1,
  profileCount: 2,
  loraName: 3,
  loras: 4,
  profileData: 5,
};
const MIN_NODE_WIDTH = 460;
const LORA_ROW_HEIGHT = 28;
const LORA_STRENGTH_STEP = 0.05;
const LORA_PANEL_PADDING = 10;
const LORA_PANEL_HEADER_HEIGHT = 34;
const LORA_PANEL_ROW_HEIGHT = 34;
const LORA_PANEL_ADD_HEIGHT = 38;
const PREVIEW_IMAGE_WIDTH = 384;
const PREVIEW_IMAGE_HEIGHT = 384;
let rgthreeInfoDialogPromise = null;
let loraPreviewImages = {};
let loraPreviewImagesPromise = null;

async function loadRgthreeInfoDialog() {
  if (!rgthreeInfoDialogPromise) {
    rgthreeInfoDialogPromise = import("../../rgthree-comfy/comfyui/dialog_info.js")
      .then((module) => module.RgthreeLoraInfoDialog)
      .catch((error) => {
        console.warn("EasyUse Anima: rgthree LoRA info dialog is unavailable.", error);
        return null;
      });
  }
  return rgthreeInfoDialogPromise;
}

function encodeRFC3986URIComponent(value) {
  return encodeURIComponent(value).replace(/[!'()*]/g, (char) => `%${char.charCodeAt(0).toString(16).toUpperCase()}`);
}

async function loadLoraPreviewImages() {
  if (!loraPreviewImagesPromise) {
    loraPreviewImagesPromise = api.fetchApi("/pysssss/images/loras")
      .then((response) => response.ok ? response.json() : {})
      .then((images) => {
        loraPreviewImages = images && typeof images === "object" ? images : {};
        return loraPreviewImages;
      })
      .catch(() => {
        loraPreviewImages = {};
        return loraPreviewImages;
      });
  }
  return loraPreviewImagesPromise;
}

function createEl(tagName, options = {}) {
  const element = document.createElement(tagName);
  if (options.className) {
    element.className = options.className;
  }
  if (options.textContent != null) {
    element.textContent = options.textContent;
  }
  if (options.innerHTML != null) {
    element.innerHTML = options.innerHTML;
  }
  if (options.style) {
    Object.assign(element.style, options.style);
  }
  return element;
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

  if (Array.isArray(values[WIDGET_INDEX.loras])) {
    values[WIDGET_INDEX.loras] = JSON.stringify(values[WIDGET_INDEX.loras]);
  } else if (typeof values[WIDGET_INDEX.loras] !== "string") {
    const lorasIndex = values.findIndex((value, index) => (
      index > WIDGET_INDEX.loras
      && Array.isArray(value)
      && value.every((item) => item && typeof item === "object" && "name" in item)
    ));
    values[WIDGET_INDEX.loras] = JSON.stringify(lorasIndex >= 0 ? values[lorasIndex] : []);
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
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}

function setLorasWidgetValue(node, loras) {
  const widget = findWidget(node, "loras");
  if (!widget) {
    return;
  }
  const value = Array.isArray(loras) ? loras : [];
  const serialized = JSON.stringify(value);
  widget.value = serialized;
  widget.callback?.(serialized);
  renderLoraRows(node);
}

function currentProfile(node) {
  return {
    style_prompt: String(widgetValue(findWidget(node, "style_prompt"), "")),
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
  detachInternalWidget(node, "lora_name");
  detachInternalWidget(node, "loras");
}

function enforceNodeLayout(node) {
  if (!node?.size || typeof node.setSize !== "function") {
    return;
  }
  const currentWidth = Number(node.size[0]) || 0;
  const currentHeight = Number(node.size[1]) || 0;
  const computed = typeof node.computeSize === "function" ? node.computeSize() : null;
  const nextWidth = currentWidth < MIN_NODE_WIDTH ? MIN_NODE_WIDTH : currentWidth;
  const nextHeight = Math.max(120, Number(computed?.[1]) || currentHeight);
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

function roundStrength(value) {
  return Math.round(Number(value || 0) * 100) / 100;
}

function formatStrength(value) {
  return roundStrength(value).toFixed(2);
}

function mutateLoras(node, mutator) {
  const loras = lorasWidgetValue(node).map((lora) => ({ ...lora }));
  mutator(loras);
  setLorasWidgetValue(node, loras);
  saveCurrentProfile(node);
}

function addLoraEntry(node, entry) {
  if (!entry?.name) {
    return;
  }
  mutateLoras(node, (loras) => {
    const existing = loras.find((lora) => lora.name === entry.name);
    if (existing) {
      existing.strength = entry.strength;
      existing.clipStrength = entry.clipStrength;
      existing.active = entry.active;
      return;
    }
    loras.push(entry);
  });
}

function updateLoraEntry(node, index, patch) {
  mutateLoras(node, (loras) => {
    const current = loras[index];
    if (!current) {
      return;
    }
    const oldStrength = Number(current.strength ?? 1);
    const oldClip = Number(current.clipStrength ?? oldStrength);
    Object.assign(current, patch);
    if (Object.prototype.hasOwnProperty.call(patch, "strength") && Math.abs(oldClip - oldStrength) < 0.0001) {
      current.clipStrength = patch.strength;
    }
  });
}

function removeLoraEntry(node, index) {
  mutateLoras(node, (loras) => {
    loras.splice(index, 1);
  });
}

function loraEntryFromName(name, base = {}) {
  const modelStrength = Number.isFinite(Number(base.strength)) ? Number(base.strength) : 1;
  const clipStrength = Number.isFinite(Number(base.clipStrength)) ? Number(base.clipStrength) : modelStrength;
  return {
    name: String(name || "").trim(),
    strength: modelStrength,
    clipStrength,
    active: base.active ?? true,
  };
}

function comboValues(widget) {
  const raw = widget?.options?.values || widget?.values || widget?.inputSpec?.[0] || [];
  if (Array.isArray(raw)) {
    return raw;
  }
  if (raw && typeof raw === "object") {
    return Object.keys(raw);
  }
  return [];
}

function loraNameValues(node) {
  return comboValues(findWidget(node, "lora_name"))
    .map((value) => String(value || "").trim())
    .filter((value) => value && value !== "None");
}

function handleLoraNameSelected(node, value) {
  if (node.__easyuseAnimaLoadingProfile || node.__easyuseAnimaSuppressLoraNameCallback) {
    return;
  }
  const name = String(value || "").trim();
  if (!name || name === "None") {
    return;
  }
  addLoraEntry(node, loraEntryFromName(name));
}

function menuEvent(event) {
  if (event instanceof Event) {
    return event;
  }
  const mouse = app.canvas?.last_mouse;
  return app.canvas?.last_mouse_event || new MouseEvent("click", {
    clientX: Array.isArray(mouse) ? mouse[0] : window.innerWidth / 2,
    clientY: Array.isArray(mouse) ? mouse[1] : window.innerHeight / 2,
  });
}

function openLoraMenu(node, event, onChoose) {
  const values = loraNameValues(node);
  if (!values.length) {
    window.alert("No LoRA files found. Refresh ComfyUI after adding LoRAs.");
    return;
  }
  node.__easyuseAnimaOpeningLoraMenu = true;
  new LiteGraph.ContextMenu(values, {
    event: menuEvent(event),
    title: "Choose a LoRA",
    scale: Math.max(1, Number(app.canvas?.ds?.scale) || 1),
    className: "dark",
    callback: (value) => {
      const name = String(value?.content ?? value ?? "").trim();
      if (!name) {
        return;
      }
      node.__easyuseAnimaSuppressLoraNameCallback = true;
      try {
        setWidgetValue(findWidget(node, "lora_name"), name);
      } finally {
        node.__easyuseAnimaSuppressLoraNameCallback = false;
      }
      onChoose(loraEntryFromName(name));
    },
  });
}

async function showLoraInfo(name) {
  const InfoDialog = await loadRgthreeInfoDialog();
  if (!InfoDialog || !name || name === "None") {
    return;
  }
  new InfoDialog(name).show();
}

function fitCanvasText(ctx, text, maxWidth) {
  const value = String(text || "");
  if (ctx.measureText(value).width <= maxWidth) {
    return value;
  }
  let result = value;
  while (result.length > 1 && ctx.measureText(`${result}...`).width > maxWidth) {
    result = result.slice(0, -1);
  }
  return `${result}...`;
}

function roundedRect(ctx, x, y, width, height, radius) {
  if (typeof ctx.roundRect === "function") {
    ctx.roundRect(x, y, width, height, radius);
    return;
  }
  const r = Math.min(radius, width / 2, height / 2);
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + width - r, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + r);
  ctx.lineTo(x + width, y + height - r);
  ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  ctx.lineTo(x + r, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
}

function positionComboMenu(menu) {
  const mouse = app.canvas?.last_mouse || [window.innerWidth / 2, window.innerHeight / 2];
  let left = Number(mouse[0] || 0) - 10;
  let top = Number(mouse[1] || 0) - 10;
  const bodyRect = document.body.getBoundingClientRect();
  const menuRect = menu.getBoundingClientRect();

  if (bodyRect.width && left > bodyRect.width - menuRect.width - 10) {
    left = bodyRect.width - menuRect.width - 10;
  }
  if (bodyRect.height && top > bodyRect.height - menuRect.height - 10) {
    top = bodyRect.height - menuRect.height - 10;
  }
  menu.style.left = `${Math.max(0, left)}px`;
  menu.style.top = `${Math.max(0, top)}px`;
}

function calculateImagePosition(relativeToEl, imageEl) {
  let { top, left, right } = relativeToEl.getBoundingClientRect();
  const bodyRect = document.body.getBoundingClientRect();
  const isSpaceRight = right + PREVIEW_IMAGE_WIDTH <= bodyRect.width;
  left = isSpaceRight ? right : left - PREVIEW_IMAGE_WIDTH;
  top -= PREVIEW_IMAGE_HEIGHT / 2;
  if (top + PREVIEW_IMAGE_HEIGHT > bodyRect.height) {
    top = bodyRect.height - PREVIEW_IMAGE_HEIGHT;
  }
  if (top < 0) {
    top = 0;
  }
  imageEl.style.left = `${Math.round(left)}px`;
  imageEl.style.top = `${Math.round(top)}px`;
  imageEl.classList.toggle("left", !isSpaceRight);
}

function addLoraPreviewHandler(item, imageHost) {
  const value = item.getAttribute("data-value")?.trim();
  const image = value ? loraPreviewImages[value] : null;
  if (!image) {
    return;
  }
  item.appendChild(document.createTextNode("*"));
  item.addEventListener("mouseover", () => {
    imageHost.src = `/pysssss/view/${encodeRFC3986URIComponent(image)}?${Date.now()}`;
    document.body.appendChild(imageHost);
    calculateImagePosition(item, imageHost);
  }, { passive: true });
  item.addEventListener("mouseout", () => imageHost.remove(), { passive: true });
  item.addEventListener("click", () => imageHost.remove(), { passive: true });
}

function updateLoraNameComboMenu(menu, imageHost) {
  const position = menu.getBoundingClientRect();
  menu.style.maxHeight = `${Math.max(120, window.innerHeight - position.top - 20)}px`;

  const items = Array.from(menu.querySelectorAll(".litemenu-entry"));
  const folderMap = new Map();
  const itemsSymbol = Symbol("items");
  const splitBy = (navigator.platform || navigator.userAgent).includes("Win") ? /\/|\\/ : /\//;

  for (const item of items) {
    const value = item.getAttribute("data-value")?.trim();
    if (!value) {
      continue;
    }
    const path = value.split(splitBy);
    item.textContent = path[path.length - 1];
    if (path.length > 1) {
      const prefix = createEl("span", {
        className: "easyuse-anima-combo-prefix",
        textContent: `${path.slice(0, -1).join("/")}/`,
      });
      item.prepend(prefix);
    }
    addLoraPreviewHandler(item, imageHost);
    if (path.length === 1) {
      continue;
    }
    item.remove();
    let currentLevel = folderMap;
    for (let index = 0; index < path.length - 1; index += 1) {
      const folder = path[index];
      if (!currentLevel.has(folder)) {
        currentLevel.set(folder, new Map());
      }
      currentLevel = currentLevel.get(folder);
    }
    if (!currentLevel.has(itemsSymbol)) {
      currentLevel.set(itemsSymbol, []);
    }
    currentLevel.get(itemsSymbol).push(item);
  }

  const parentElement = items[0]?.parentElement || menu;
  const createFolderElement = (name, level) => createEl("div", {
    className: "litemenu-entry easyuse-anima-combo-folder",
    innerHTML: `<span class="easyuse-anima-combo-folder-arrow">▶</span> ${name}`,
    style: { paddingLeft: `${level * 10 + 5}px` },
  });

  const insertFolderStructure = (parent, map, level = 0) => {
    for (const [folderName, content] of map.entries()) {
      if (folderName === itemsSymbol) {
        continue;
      }
      const folderElement = createFolderElement(folderName, level);
      const childContainer = createEl("div", {
        className: "easyuse-anima-combo-folder-contents",
        style: { display: "none" },
      });
      const childItems = content.get(itemsSymbol) || [];
      for (const item of childItems) {
        item.style.paddingLeft = `${(level + 1) * 10 + 14}px`;
        childContainer.appendChild(item);
      }
      insertFolderStructure(childContainer, content, level + 1);
      folderElement.addEventListener("click", (event) => {
        event.stopPropagation();
        const arrow = folderElement.querySelector(".easyuse-anima-combo-folder-arrow");
        const isClosed = childContainer.style.display === "none";
        childContainer.style.display = isClosed ? "block" : "none";
        if (arrow) {
          arrow.textContent = isClosed ? "▼" : "▶";
        }
      });
      parent.appendChild(folderElement);
      parent.appendChild(childContainer);
    }
  };

  insertFolderStructure(parentElement, folderMap);
  positionComboMenu(menu);
}

class EasyUseAnimaLoraPanelWidget {
  constructor() {
    this.name = "easyuse_anima_lora_panel";
    this.type = "custom";
    this.options = { serialize: false };
    this.serialize = false;
    this.__easyuseAnimaLoraRowWidget = true;
    this.hitAreas = {};
    this.rowHitAreas = [];
    this.node = null;
  }

  computeSize(width) {
    const rows = this.node ? lorasWidgetValue(this.node).length : 0;
    return [width, LORA_PANEL_PADDING * 2 + LORA_PANEL_HEADER_HEIGHT + rows * LORA_PANEL_ROW_HEIGHT + LORA_PANEL_ADD_HEIGHT + 12];
  }

  draw(ctx, node, width, y, height) {
    this.node = node;
    this.hitAreas = {};
    this.rowHitAreas = [];
    const loras = lorasWidgetValue(node);
    const pad = LORA_PANEL_PADDING;
    const panelX = pad;
    const panelY = y + 4;
    const panelW = width - pad * 2;
    const panelH = LORA_PANEL_HEADER_HEIGHT + loras.length * LORA_PANEL_ROW_HEIGHT + LORA_PANEL_ADD_HEIGHT + pad * 2;
    const allActive = loras.length > 0 && loras.every((lora) => lora.active !== false);

    ctx.save();
    ctx.fillStyle = "rgba(38, 42, 51, 0.92)";
    ctx.beginPath();
    roundedRect(ctx, panelX, panelY, panelW, panelH, 7);
    ctx.fill();

    const toggleSize = 24;
    const headerY = panelY + pad;
    this.hitAreas.toggleAll = [panelX + pad, headerY + 5, toggleSize, toggleSize];
    ctx.fillStyle = allActive ? "#8fa1c9" : "#4b4f57";
    ctx.beginPath();
    roundedRect(ctx, ...this.hitAreas.toggleAll, 4);
    ctx.fill();

    ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
    ctx.font = "18px sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText("Toggle All", panelX + pad + toggleSize + 12, headerY + LORA_PANEL_HEADER_HEIGHT / 2);
    ctx.textAlign = "right";
    ctx.fillText("Strength", panelX + panelW - pad, headerY + LORA_PANEL_HEADER_HEIGHT / 2);

    let rowY = headerY + LORA_PANEL_HEADER_HEIGHT;
    for (let index = 0; index < loras.length; index += 1) {
      const lora = loras[index] || {};
      const active = lora.active !== false;
      const rowX = panelX + pad;
      const rowW = panelW - pad * 2;
      const rowH = LORA_PANEL_ROW_HEIGHT - 4;
      const midY = rowY + rowH / 2;
      const right = rowX + rowW;
      const toggleW = 28;
      const infoW = 28;
      const arrowW = 26;
      const valueW = 54;
      const deleteW = 22;
      const areas = {
        toggle: [rowX + 6, rowY + 7, toggleW, 18],
        info: [right - deleteW - arrowW * 2 - valueW - infoW - 10, rowY + 4, infoW, rowH - 4],
        dec: [right - deleteW - arrowW * 2 - valueW, rowY + 4, arrowW, rowH - 4],
        value: [right - deleteW - arrowW - valueW, rowY + 4, valueW, rowH - 4],
        inc: [right - deleteW - arrowW, rowY + 4, arrowW, rowH - 4],
        delete: [right - deleteW, rowY + 4, deleteW, rowH - 4],
      };
      const nameX = areas.toggle[0] + toggleW + 12;
      const nameW = areas.info[0] - nameX - 8;
      this.rowHitAreas[index] = areas;

      ctx.globalAlpha = active ? 1 : 0.45;
      ctx.fillStyle = "rgba(56, 67, 90, 0.55)";
      ctx.beginPath();
      roundedRect(ctx, rowX, rowY + 2, rowW, rowH, 8);
      ctx.fill();
      ctx.fillStyle = active ? "#8fa1c9" : "#555";
      ctx.beginPath();
      roundedRect(ctx, ...areas.toggle, 8);
      ctx.fill();

      ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
      ctx.font = "18px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(fitCanvasText(ctx, lora.name || "None", nameW), nameX, midY);
      ctx.textAlign = "center";
      ctx.font = "17px sans-serif";
      ctx.fillText("ⓘ", areas.info[0] + infoW / 2, midY);
      ctx.fillText("◀", areas.dec[0] + arrowW / 2, midY);
      ctx.fillText(formatStrength(lora.strength ?? 1), areas.value[0] + valueW / 2, midY);
      ctx.fillText("▶", areas.inc[0] + arrowW / 2, midY);
      ctx.fillText("×", areas.delete[0] + deleteW / 2, midY);
      ctx.globalAlpha = 1;
      rowY += LORA_PANEL_ROW_HEIGHT;
    }

    const addY = rowY + 6;
    this.hitAreas.add = [panelX + pad, addY, panelW - pad * 2, LORA_PANEL_ADD_HEIGHT - 8];
    ctx.strokeStyle = "rgba(180, 180, 185, 0.5)";
    ctx.fillStyle = "rgba(30, 31, 35, 0.6)";
    ctx.beginPath();
    roundedRect(ctx, ...this.hitAreas.add, 5);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
    ctx.font = "18px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("+ Add Lora", panelX + panelW / 2, addY + (LORA_PANEL_ADD_HEIGHT - 8) / 2);
    ctx.restore();
  }

  contains(pos, area) {
    const hit = this.hitAreas[area];
    return !!hit
      && pos[0] >= hit[0]
      && pos[0] <= hit[0] + hit[2]
      && pos[1] >= hit[1]
      && pos[1] <= hit[1] + hit[3];
  }

  mouse(event, pos, node) {
    if (event.type !== "pointerdown") {
      return false;
    }
    if (this.contains(pos, "add")) {
      openLoraMenu(node, event, (entry) => addLoraEntry(node, entry));
      return true;
    }
    if (this.contains(pos, "toggleAll")) {
      const loras = lorasWidgetValue(node);
      const nextActive = !(loras.length > 0 && loras.every((lora) => lora.active !== false));
      mutateLoras(node, (items) => {
        for (const item of items) {
          item.active = nextActive;
        }
      });
      return true;
    }
    for (let index = 0; index < this.rowHitAreas.length; index += 1) {
      const areas = this.rowHitAreas[index];
      const lora = lorasWidgetValue(node)[index];
      if (!areas || !lora) {
        continue;
      }
      const hit = (area) => {
        const bounds = areas[area];
        return bounds
          && pos[0] >= bounds[0]
          && pos[0] <= bounds[0] + bounds[2]
          && pos[1] >= bounds[1]
          && pos[1] <= bounds[1] + bounds[3];
      };
      if (hit("toggle")) {
        updateLoraEntry(node, index, { active: lora.active === false });
        return true;
      }
      if (hit("delete")) {
        removeLoraEntry(node, index);
        return true;
      }
      if (hit("info")) {
        showLoraInfo(lora.name);
        return true;
      }
      if (hit("dec")) {
        updateLoraEntry(node, index, { strength: roundStrength((lora.strength ?? 1) - LORA_STRENGTH_STEP) });
        return true;
      }
      if (hit("inc")) {
        updateLoraEntry(node, index, { strength: roundStrength((lora.strength ?? 1) + LORA_STRENGTH_STEP) });
        return true;
      }
      if (hit("value")) {
        app.canvas.prompt("LoRA strength", lora.strength ?? 1, (value) => {
          const next = Number(value);
          if (Number.isFinite(next)) {
            updateLoraEntry(node, index, { strength: roundStrength(next) });
          }
        }, event);
        return true;
      }
    }
    return false;
  }
}

function renderLoraRows(node) {
  if (!node.widgets) {
    return;
  }
  node.widgets = node.widgets.filter((widget) => !widget.__easyuseAnimaLoraRowWidget);
  const panel = new EasyUseAnimaLoraPanelWidget();
  panel.node = node;
  node.widgets.push(panel);
  enforceNodeLayout(node);
}

function profileOptions(node) {
  const count = profileCount(node);
  const options = [];
  for (let index = 1; index <= count; index += 1) {
    options.push(`${index}. ${profileLabel(node, index)}`);
  }
  return options;
}

function profileOptionIndex(value) {
  const match = String(value || "").match(/^(\d+)\./);
  return Math.max(1, Number.parseInt(match?.[1] || "1", 10) || 1);
}

function renderTabs(node) {
  const selector = node.__easyuseAnimaProfileSelector;
  if (!selector) {
    return;
  }
  const options = profileOptions(node);
  selector.options.values = options;
  const selectedLabel = options[activeProfileIndex(node) - 1] || options[0] || defaultProfileName(1);
  node.__easyuseAnimaSuppressProfileSelectorCallback = true;
  try {
    selector.value = selectedLabel;
  } finally {
    node.__easyuseAnimaSuppressProfileSelectorCallback = false;
  }
  const deleteButton = node.__easyuseAnimaDeleteProfileButton;
  if (deleteButton) {
    deleteButton.disabled = profileCount(node) <= 1;
  }
  enforceNodeLayout(node);
}

function ensureTabsWidget(node) {
  if (node.__easyuseAnimaProfileSelector || typeof node.addWidget !== "function") {
    return;
  }
  const selector = node.addWidget(
    "combo",
    "profile",
    profileOptions(node)[activeProfileIndex(node) - 1] || defaultProfileName(1),
    (value) => {
      if (node.__easyuseAnimaSuppressProfileSelectorCallback) {
        return;
      }
      switchProfile(node, profileOptionIndex(value));
    },
    { values: profileOptions(node) },
  );
  selector.serialize = false;
  node.__easyuseAnimaProfileSelector = selector;

  const addButton = node.addWidget("button", "add_profile", "+", () => addProfile(node));
  addButton.serialize = false;

  const renameButton = node.addWidget("button", "rename_profile", "Rename", () => {
    renameProfile(node, activeProfileIndex(node));
  });
  renameButton.serialize = false;

  const deleteButton = node.addWidget("button", "delete_profile", "Delete", () => {
    deleteProfile(node, activeProfileIndex(node));
  });
  deleteButton.serialize = false;
  node.__easyuseAnimaDeleteProfileButton = deleteButton;

  for (const widget of [selector, addButton, renameButton, deleteButton]) {
    if (widget) {
      widget.__easyuseAnimaControlWidget = true;
    }
  }
  const controls = [selector, addButton, renameButton, deleteButton].filter(Boolean);
  const insertBeforeIndex = node.widgets?.findIndex((widget) => widget.name === "lora_name" || widget.name === "loras") ?? -1;
  if (insertBeforeIndex >= 0 && controls.length) {
    node.widgets = node.widgets.filter((widget) => !widget.__easyuseAnimaControlWidget);
    node.widgets.splice(insertBeforeIndex, 0, ...controls);
  }
  renderTabs(node);
  renderLoraRows(node);
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
  wrapWidgetCallback(node, "lora_name", function () {
    handleLoraNameSelected(node, widgetValue(findWidget(node, "lora_name"), ""));
  });
  wrapWidgetCallback(node, "loras", () => syncAfterWidgetChange(node));
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
      workflowNode.widgets_values[WIDGET_INDEX.loras] = JSON.stringify(lorasWidgetValue(this));
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
  init() {
    document.head.appendChild(createEl("style", {
      textContent: `
        .easyuse-anima-combo-image {
          position: absolute;
          left: 0;
          top: 0;
          width: ${PREVIEW_IMAGE_WIDTH}px;
          height: ${PREVIEW_IMAGE_HEIGHT}px;
          object-fit: contain;
          object-position: top left;
          z-index: 9999;
          pointer-events: none;
        }
        .easyuse-anima-combo-image.left {
          object-position: top right;
        }
        .easyuse-anima-combo-folder {
          opacity: 0.72;
        }
        .easyuse-anima-combo-folder-arrow {
          display: inline-block;
          width: 15px;
        }
        .easyuse-anima-combo-folder:hover {
          background-color: rgba(255, 255, 255, 0.1);
        }
        .easyuse-anima-combo-prefix {
          display: none;
        }
        .litecontextmenu:has(input:not(:placeholder-shown)) .easyuse-anima-combo-folder-contents {
          display: block !important;
        }
        .litecontextmenu:has(input:not(:placeholder-shown)) .easyuse-anima-combo-folder {
          display: none;
        }
        .litecontextmenu:has(input:not(:placeholder-shown)) .easyuse-anima-combo-prefix {
          display: inline;
        }
        .litecontextmenu:has(input:not(:placeholder-shown)) .litemenu-entry {
          padding-left: 2px !important;
        }
      `,
    }));

    loadLoraPreviewImages();
    const refreshComboInNodes = app.refreshComboInNodes;
    app.refreshComboInNodes = async function (...args) {
      const result = await refreshComboInNodes?.apply(this, args);
      loraPreviewImagesPromise = null;
      await loadLoraPreviewImages();
      return result;
    };

    const imageHost = createEl("img", { className: "easyuse-anima-combo-image" });
    const observer = new MutationObserver((mutations) => {
      const node = app.canvas?.current_node;
      if (!node || node.comfyClass !== NODE_TYPE) {
        return;
      }
      for (const mutation of mutations) {
        for (const removed of mutation.removedNodes) {
          if (removed.classList?.contains("litecontextmenu")) {
            imageHost.remove();
          }
        }
        for (const added of mutation.addedNodes) {
          if (!added.classList?.contains("litecontextmenu")) {
            continue;
          }
          const overWidget = app.canvas?.getWidgetAtCursor?.();
          if (overWidget?.name !== "lora_name" && !node.__easyuseAnimaOpeningLoraMenu) {
            continue;
          }
          requestAnimationFrame(async () => {
            if (!added.querySelector(".comfy-context-menu-filter")) {
              node.__easyuseAnimaOpeningLoraMenu = false;
              return;
            }
            await loadLoraPreviewImages();
            updateLoraNameComboMenu(added, imageHost);
            node.__easyuseAnimaOpeningLoraMenu = false;
          });
          return;
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: false });
  },
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
