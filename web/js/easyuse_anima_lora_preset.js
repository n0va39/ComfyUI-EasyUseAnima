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
const PROFILE_BAR_HEIGHT = 30;
const LORA_HEADER_HEIGHT = 24;
const LORA_ROW_HEIGHT = 28;
const LORA_ADD_HEIGHT = 36;
const STRENGTH_STEP = 0.05;
const PREVIEW_SIZE = 360;

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
    values[WIDGET_INDEX.loras] = "[]";
  }
  if (!looksLikeProfileData(values[WIDGET_INDEX.profileData])) {
    values[WIDGET_INDEX.profileData] = "{}";
  }
}

function encodeRFC3986URIComponent(value) {
  return encodeURIComponent(value).replace(/[!'()*]/g, (char) => `%${char.charCodeAt(0).toString(16).toUpperCase()}`);
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
  if (input instanceof HTMLInputElement || input instanceof HTMLTextAreaElement) {
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

function profileKey(index) {
  return String(Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(index, 10) || 1)));
}

function parseProfileData(widget) {
  try {
    const parsed = JSON.parse(String(widgetValue(widget, "{}") || "{}"));
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function writeProfileData(widget, data) {
  setWidgetValue(widget, JSON.stringify(data));
}

function profileCount(node) {
  return Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(widgetValue(findWidget(node, "profile_count"), 4), 10) || 4));
}

function wrapProfileIndex(index, count) {
  const safeCount = Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(count, 10) || 1));
  const safeIndex = Math.max(1, Number.parseInt(index, 10) || 1);
  return ((safeIndex - 1) % safeCount) + 1;
}

function selectedProfileIndex(node) {
  return wrapProfileIndex(widgetValue(findWidget(node, "profile_index"), 1), profileCount(node));
}

function activeProfileIndex(node) {
  return wrapProfileIndex(node.__easyuseAnimaActiveProfileIndex || selectedProfileIndex(node), profileCount(node));
}

function setProfileIndex(node, index) {
  node.__easyuseAnimaSuppressProfileIndexCallback = true;
  try {
    setWidgetValue(findWidget(node, "profile_index"), wrapProfileIndex(index, profileCount(node)));
  } finally {
    node.__easyuseAnimaSuppressProfileIndexCallback = false;
  }
}

function setProfileCount(node, count) {
  node.__easyuseAnimaSuppressProfileCountCallback = true;
  try {
    setWidgetValue(findWidget(node, "profile_count"), Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(count, 10) || 1)));
  } finally {
    node.__easyuseAnimaSuppressProfileCountCallback = false;
  }
}

function lorasWidgetValue(node) {
  const value = widgetValue(findWidget(node, "loras"), "[]");
  if (Array.isArray(value)) {
    return value;
  }
  if (value && typeof value === "object" && Array.isArray(value.__value__)) {
    return value.__value__;
  }
  try {
    const parsed = JSON.parse(String(value || "[]"));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function normalizeLoraEntry(entry) {
  const name = String(entry?.name ?? entry?.lora ?? "").trim();
  const strength = Number.isFinite(Number(entry?.strength)) ? Number(entry.strength) : 1;
  const strengthTwoRaw = entry?.strengthTwo ?? entry?.clipStrength;
  const strengthTwo = strengthTwoRaw == null || strengthTwoRaw === "" ? null : Number(strengthTwoRaw);
  return {
    name,
    on: entry?.on ?? entry?.active ?? true,
    strength,
    strengthTwo: Number.isFinite(strengthTwo) ? strengthTwo : null,
  };
}

function setLorasWidgetValue(node, loras, options = {}) {
  const widget = findWidget(node, "loras");
  if (!widget) {
    return;
  }
  const value = Array.isArray(loras)
    ? loras.map(normalizeLoraEntry).filter((entry) => entry.name)
    : [];
  setWidgetValue(widget, JSON.stringify(value));
  if (options.render !== false) {
    renderLoraWidgets(node);
  } else {
    node.setDirtyCanvas?.(true, true);
  }
}

function currentProfile(node) {
  return {
    name: profileLabel(node, activeProfileIndex(node)),
    style_prompt: String(widgetValue(findWidget(node, "style_prompt"), "")),
    loras: lorasWidgetValue(node).map(normalizeLoraEntry).filter((entry) => entry.name),
  };
}

function defaultProfileName(index) {
  return `Profile ${index}`;
}

function profileLabel(node, index) {
  const profile = parseProfileData(findWidget(node, "profile_data"))[profileKey(index)];
  return String(profile?.name || defaultProfileName(index));
}

function saveProfile(node, index) {
  if (node.__easyuseAnimaLoadingProfile) {
    return;
  }
  const dataWidget = findWidget(node, "profile_data");
  if (!dataWidget) {
    return;
  }
  const data = parseProfileData(dataWidget);
  const key = profileKey(index);
  const previous = data[key] && typeof data[key] === "object" ? data[key] : {};
  data[key] = {
    ...currentProfile(node),
    name: String(previous.name || currentProfile(node).name || defaultProfileName(index)),
  };
  writeProfileData(dataWidget, data);
}

function saveCurrentProfile(node) {
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
    data[key] = options.initializeFromCurrent ? currentProfile(node) : emptyProfile(index);
    data[key].name = String(data[key].name || defaultProfileName(index));
    writeProfileData(dataWidget, data);
  }
  const profile = data[key] || emptyProfile(index);
  node.__easyuseAnimaLoadingProfile = true;
  try {
    setWidgetValue(findWidget(node, "style_prompt"), String(profile.style_prompt || ""));
    setLorasWidgetValue(node, Array.isArray(profile.loras) ? profile.loras : []);
  } finally {
    node.__easyuseAnimaLoadingProfile = false;
  }
}

function switchProfile(node, index) {
  const nextIndex = wrapProfileIndex(index, profileCount(node));
  const currentIndex = activeProfileIndex(node);
  if (nextIndex === currentIndex) {
    renderProfileBar(node);
    return;
  }
  saveProfile(node, currentIndex);
  setProfileIndex(node, nextIndex);
  node.__easyuseAnimaActiveProfileIndex = nextIndex;
  loadProfile(node, nextIndex);
  renderProfileBar(node);
  node.setDirtyCanvas?.(true, true);
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
  data[key] = {
    ...(data[key] && typeof data[key] === "object" ? data[key] : emptyProfile(index)),
    name: nextName.trim() || defaultProfileName(index),
  };
  writeProfileData(dataWidget, data);
  renderProfileBar(node);
  node.setDirtyCanvas?.(true, true);
}

function deleteProfile(node, index) {
  const count = profileCount(node);
  if (count <= 1) {
    return;
  }
  if (!window.confirm(`Delete profile "${profileLabel(node, index)}"?`)) {
    return;
  }
  const data = parseProfileData(findWidget(node, "profile_data"));
  const nextData = {};
  let nextWriteIndex = 1;
  for (let sourceIndex = 1; sourceIndex <= count; sourceIndex += 1) {
    if (sourceIndex === index) {
      continue;
    }
    nextData[profileKey(nextWriteIndex)] = data[profileKey(sourceIndex)] || emptyProfile(nextWriteIndex);
    nextData[profileKey(nextWriteIndex)].name ||= defaultProfileName(nextWriteIndex);
    nextWriteIndex += 1;
  }
  writeProfileData(findWidget(node, "profile_data"), nextData);
  setProfileCount(node, count - 1);
  const nextActive = Math.min(index, count - 1);
  node.__easyuseAnimaActiveProfileIndex = nextActive;
  setProfileIndex(node, nextActive);
  loadProfile(node, nextActive);
  renderProfileBar(node);
  node.setDirtyCanvas?.(true, true);
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

function roundStrength(value) {
  return Math.round(Number(value || 0) * 100) / 100;
}

function loraEntryFromName(name, base = {}) {
  return normalizeLoraEntry({
    name,
    on: base.on ?? true,
    strength: base.strength ?? 1,
    strengthTwo: base.strengthTwo ?? null,
  });
}

function mutateLoras(node, mutator, options = {}) {
  const loras = lorasWidgetValue(node).map(normalizeLoraEntry);
  mutator(loras);
  setLorasWidgetValue(node, loras, options);
  saveCurrentProfile(node);
}

function addLoraEntry(node, entry) {
  const nextEntry = normalizeLoraEntry(entry);
  if (!nextEntry.name) {
    return;
  }
  mutateLoras(node, (loras) => {
    const existing = loras.find((lora) => lora.name === nextEntry.name);
    if (existing) {
      Object.assign(existing, nextEntry);
    } else {
      loras.push(nextEntry);
    }
  });
}

function updateLoraEntry(node, index, patch, options = {}) {
  mutateLoras(node, (loras) => {
    if (!loras[index]) {
      return;
    }
    const current = loras[index];
    const oldStrength = Number(current.strength ?? 1);
    const oldClip = current.strengthTwo == null ? oldStrength : Number(current.strengthTwo);
    Object.assign(current, patch);
    if (Object.prototype.hasOwnProperty.call(patch, "strength") && Math.abs(oldClip - oldStrength) < 0.0001) {
      current.strengthTwo = null;
    }
  }, options);
}

function removeLoraEntry(node, index) {
  mutateLoras(node, (loras) => {
    loras.splice(index, 1);
  });
}

function fitCanvasText(ctx, text, maxWidth) {
  const value = String(text || "");
  if (ctx.measureText(value).width <= maxWidth) {
    return value;
  }
  const ellipsis = "...";
  let result = value;
  while (result.length > 1 && ctx.measureText(`${result}${ellipsis}`).width > maxWidth) {
    result = result.slice(0, -1);
  }
  return `${result}${ellipsis}`;
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

function pointInArea(pos, area) {
  return !!area
    && pos[0] >= area[0]
    && pos[0] <= area[0] + area[2]
    && pos[1] >= area[1]
    && pos[1] <= area[1] + area[3];
}

function drawToggle(ctx, x, y, height, value) {
  const width = height * 1.5;
  ctx.save();
  ctx.globalAlpha = app.canvas.editor_alpha * 0.25;
  ctx.fillStyle = "rgba(255,255,255,0.45)";
  ctx.beginPath();
  roundedRect(ctx, x + 4, y + 4, width - 8, height - 8, height / 2);
  ctx.fill();
  ctx.globalAlpha = app.canvas.editor_alpha;
  ctx.fillStyle = value ? "#89B" : "#888";
  ctx.beginPath();
  ctx.arc(value ? x + height : x + height * 0.5, y + height * 0.5, height * 0.36, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
  return [x, y, width, height];
}

function drawNumberPart(ctx, x, y, height, value) {
  const arrowWidth = 9;
  const arrowHeight = 10;
  const inner = 3;
  const numberWidth = 32;
  const total = arrowWidth + inner + numberWidth + inner + arrowWidth;
  const startX = x - total;
  const midY = y + height / 2;
  ctx.save();
  ctx.fill(new Path2D(`M ${startX} ${midY} l ${arrowWidth} ${arrowHeight / 2} l 0 -${arrowHeight} L ${startX} ${midY} z`));
  const textX = startX + arrowWidth + inner;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(Number(value ?? 1).toFixed(2), textX + numberWidth / 2, midY);
  const rightX = textX + numberWidth + inner;
  ctx.fill(new Path2D(`M ${rightX} ${midY - arrowHeight / 2} l ${arrowWidth} ${arrowHeight / 2} l -${arrowWidth} ${arrowHeight / 2} v -${arrowHeight} z`));
  ctx.restore();
  return {
    dec: [startX, y, arrowWidth, height],
    value: [textX, y, numberWidth, height],
    inc: [rightX, y, arrowWidth, height],
    any: [startX, y, total, height],
  };
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
  node.widgets.splice(node.widgets.indexOf(widget), 1);
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
  const nextWidth = Math.max(MIN_NODE_WIDTH, currentWidth);
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

function menuEvent(event) {
  if (event instanceof Event) {
    return event;
  }
  const mouse = app.canvas?.last_mouse || [window.innerWidth / 2, window.innerHeight / 2];
  return new MouseEvent("click", { clientX: mouse[0], clientY: mouse[1] });
}

function positionPreview(element, event) {
  const body = document.body.getBoundingClientRect();
  let left = Number(event?.clientX || body.width / 2) + 18;
  let top = Number(event?.clientY || body.height / 2) + 18;
  if (left + PREVIEW_SIZE > body.width) {
    left = Math.max(0, Number(event?.clientX || body.width / 2) - PREVIEW_SIZE - 18);
  }
  if (top + PREVIEW_SIZE > body.height) {
    top = Math.max(0, body.height - PREVIEW_SIZE - 12);
  }
  element.style.left = `${left}px`;
  element.style.top = `${top}px`;
}

function showPreview(name, event) {
  if (!name || name === "None") {
    return;
  }
  let preview = document.querySelector(".easyuse-anima-lora-preview");
  if (!preview) {
    preview = createEl("img", { className: "easyuse-anima-lora-preview" });
    preview.addEventListener("error", () => {
      preview.style.display = "none";
      preview.removeAttribute("data-name");
    });
    preview.addEventListener("load", () => {
      preview.style.display = "block";
    });
    document.body.appendChild(preview);
  }
  const src = `/easyuse_anima/lora_preview?name=${encodeRFC3986URIComponent(name)}&t=${Date.now()}`;
  if (preview.getAttribute("data-name") !== name) {
    preview.setAttribute("data-name", name);
    preview.src = src;
  }
  positionPreview(preview, event);
  preview.style.display = "block";
}

function hidePreview() {
  const preview = document.querySelector(".easyuse-anima-lora-preview");
  if (preview) {
    preview.style.display = "none";
  }
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
    className: "dark easyuse-anima-lora-menu",
    callback: (value) => {
      const name = String(value?.content ?? value ?? "").trim();
      if (name) {
        onChoose(loraEntryFromName(name));
      }
    },
  });
}

function updateLoraMenuTree(menu) {
  const items = Array.from(menu.querySelectorAll(".litemenu-entry"));
  if (!items.length || menu.__easyuseAnimaTreeReady) {
    return;
  }
  menu.__easyuseAnimaTreeReady = true;
  const folderMap = new Map();
  const itemsSymbol = Symbol("items");
  const splitBy = /\/|\\/;

  for (const item of items) {
    const value = String(item.getAttribute("data-value") || item.textContent || "").trim();
    if (!value) {
      continue;
    }
    item.setAttribute("data-value", value);
    const parts = value.split(splitBy).filter(Boolean);
    item.textContent = parts[parts.length - 1] || value;
    if (parts.length > 1) {
      item.prepend(createEl("span", {
        className: "easyuse-anima-combo-prefix",
        textContent: `${parts.slice(0, -1).join("/")}/`,
      }));
    }
    item.addEventListener("mouseover", (event) => showPreview(value, event), { passive: true });
    item.addEventListener("mousemove", (event) => showPreview(value, event), { passive: true });
    item.addEventListener("mouseout", hidePreview, { passive: true });
    if (parts.length <= 1) {
      continue;
    }
    item.remove();
    let level = folderMap;
    for (const folder of parts.slice(0, -1)) {
      if (!level.has(folder)) {
        level.set(folder, new Map());
      }
      level = level.get(folder);
    }
    if (!level.has(itemsSymbol)) {
      level.set(itemsSymbol, []);
    }
    level.get(itemsSymbol).push(item);
  }

  const parent = items[0]?.parentElement || menu;
  const insertFolders = (target, map, depth = 0) => {
    for (const [folder, content] of map.entries()) {
      if (folder === itemsSymbol) {
        continue;
      }
      const folderEl = createEl("div", {
        className: "litemenu-entry easyuse-anima-combo-folder",
        innerHTML: `<span class="easyuse-anima-combo-folder-arrow">▶</span> ${folder}`,
        style: { paddingLeft: `${depth * 10 + 5}px` },
      });
      const childContainer = createEl("div", {
        className: "easyuse-anima-combo-folder-contents",
        style: { display: "none" },
      });
      for (const child of content.get(itemsSymbol) || []) {
        child.style.paddingLeft = `${(depth + 1) * 10 + 14}px`;
        childContainer.appendChild(child);
      }
      insertFolders(childContainer, content, depth + 1);
      folderEl.addEventListener("click", (event) => {
        event.stopPropagation();
        const open = childContainer.style.display === "none";
        childContainer.style.display = open ? "block" : "none";
        folderEl.querySelector(".easyuse-anima-combo-folder-arrow").textContent = open ? "▼" : "▶";
      });
      target.appendChild(folderEl);
      target.appendChild(childContainer);
    }
  };

  insertFolders(parent, folderMap);
}

class ProfileBarWidget {
  constructor() {
    this.name = "easyuse_anima_profile_bar";
    this.type = "custom";
    this.options = { serialize: false };
    this.serialize = false;
    this.__easyuseAnimaControlWidget = true;
    this.hitAreas = [];
  }

  computeSize(width) {
    return [width, PROFILE_BAR_HEIGHT];
  }

  draw(ctx, node, width, y) {
    this.hitAreas = [];
    const active = activeProfileIndex(node);
    const count = profileCount(node);
    let x = 8;
    const buttonY = y + 4;
    const buttonH = 22;
    const gap = 4;

    ctx.save();
    ctx.font = "13px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    const drawButton = (id, label, buttonW, selected = false, disabled = false) => {
      if (x + buttonW > width - 8) {
        return;
      }
      this.hitAreas.push([x, buttonY, buttonW, buttonH, id, disabled]);
      ctx.globalAlpha = disabled ? 0.45 : 1;
      ctx.fillStyle = selected ? "#3f79d8" : LiteGraph.WIDGET_BGCOLOR;
      ctx.strokeStyle = selected ? "#6fa2ff" : LiteGraph.WIDGET_OUTLINE_COLOR;
      ctx.beginPath();
      roundedRect(ctx, x, buttonY, buttonW, buttonH, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
      ctx.fillText(label, x + buttonW / 2, buttonY + buttonH / 2);
      x += buttonW + gap;
      ctx.globalAlpha = 1;
    };

    for (let index = 1; index <= count; index += 1) {
      drawButton(`profile:${index}`, String(index), 26, index === active);
    }
    drawButton("add", "+", 28);
    drawButton("rename", "R", 28);
    drawButton("delete", "X", 28, false, count <= 1);
    ctx.restore();
  }

  mouse(event, pos, node) {
    if (event.type !== "pointerdown" || event.button !== 0) {
      return false;
    }
    for (const [x, y, width, height, id, disabled] of this.hitAreas) {
      if (disabled || !pointInArea(pos, [x, y, width, height])) {
        continue;
      }
      if (id === "add") {
        addProfile(node);
      } else if (id === "rename") {
        renameProfile(node, activeProfileIndex(node));
      } else if (id === "delete") {
        deleteProfile(node, activeProfileIndex(node));
      } else if (String(id).startsWith("profile:")) {
        switchProfile(node, Number.parseInt(String(id).slice(8), 10));
      }
      return true;
    }
    return false;
  }
}

class LoraHeaderWidget {
  constructor() {
    this.name = "easyuse_anima_lora_header";
    this.type = "custom";
    this.options = { serialize: false };
    this.serialize = false;
    this.__easyuseAnimaLoraWidget = true;
    this.toggleArea = null;
  }

  computeSize(width) {
    return [width, LORA_HEADER_HEIGHT];
  }

  draw(ctx, node, width, y, height) {
    const loras = lorasWidgetValue(node);
    if (!loras.length) {
      return;
    }
    const allOn = loras.every((lora) => normalizeLoraEntry(lora).on !== false);
    const margin = 10;
    const midY = y + height / 2 + 1;
    ctx.save();
    this.toggleArea = drawToggle(ctx, margin, y + 2, height, allOn);
    ctx.globalAlpha = app.canvas.editor_alpha * 0.55;
    ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText("Toggle All", margin + this.toggleArea[2] + 4, midY);
    ctx.textAlign = "center";
    ctx.fillText("Strength", width - margin - 28, midY);
    ctx.restore();
  }

  mouse(event, pos, node) {
    if (event.type !== "pointerdown" || event.button !== 0 || !pointInArea(pos, this.toggleArea)) {
      return false;
    }
    const nextOn = !lorasWidgetValue(node).every((lora) => normalizeLoraEntry(lora).on !== false);
    mutateLoras(node, (loras) => {
      for (const lora of loras) {
        lora.on = nextOn;
      }
    });
    return true;
  }
}

class LoraRowWidget {
  constructor(index) {
    this.name = `easyuse_anima_lora_${index}`;
    this.type = "custom";
    this.options = { serialize: false };
    this.serialize = false;
    this.__easyuseAnimaLoraWidget = true;
    this.index = index;
    this.hitAreas = {};
    this.dragging = false;
    this.moved = false;
  }

  computeSize(width) {
    return [width, LORA_ROW_HEIGHT];
  }

  draw(ctx, node, width, y, height) {
    const lora = normalizeLoraEntry(lorasWidgetValue(node)[this.index]);
    if (!lora.name) {
      return;
    }
    const margin = 10;
    const inner = 4;
    const rowX = margin;
    const rowW = width - margin * 2;
    const rowH = height - 4;
    const rowY = y + 2;
    const midY = y + height / 2;
    const right = rowX + rowW;

    ctx.save();
    ctx.fillStyle = LiteGraph.WIDGET_BGCOLOR;
    ctx.strokeStyle = LiteGraph.WIDGET_OUTLINE_COLOR;
    ctx.beginPath();
    roundedRect(ctx, rowX, rowY, rowW, rowH, rowH / 2);
    ctx.fill();
    ctx.stroke();

    this.hitAreas.toggle = drawToggle(ctx, rowX, rowY, rowH, lora.on !== false);
    let posX = rowX + this.hitAreas.toggle[2] + inner;

    if (lora.on === false) {
      ctx.globalAlpha = app.canvas.editor_alpha * 0.4;
    }
    ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;

    const number = drawNumberPart(ctx, right - inner, rowY, rowH, lora.strength);
    this.hitAreas.dec = number.dec;
    this.hitAreas.value = number.value;
    this.hitAreas.inc = number.inc;
    this.hitAreas.strengthAny = number.any;

    const infoSize = 18;
    const infoX = number.dec[0] - infoSize - inner * 2;
    this.hitAreas.info = [infoX, rowY + 2, infoSize, rowH - 4];
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("i", infoX + infoSize / 2, midY);

    const nameW = Math.max(20, infoX - posX - inner);
    this.hitAreas.lora = [posX, y, nameW, height];
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(fitCanvasText(ctx, lora.name, nameW), posX, midY);
    ctx.restore();
  }

  mouse(event, pos, node) {
    const lora = normalizeLoraEntry(lorasWidgetValue(node)[this.index]);
    if (!lora.name) {
      return false;
    }
    if (event.type === "pointermove") {
      if (pointInArea(pos, this.hitAreas.info)) {
        showPreview(lora.name, event);
      } else {
        hidePreview();
      }
      if (this.dragging && event.deltaX) {
        this.moved = true;
        updateLoraEntry(
          node,
          this.index,
          { strength: roundStrength((lora.strength ?? 1) + event.deltaX * STRENGTH_STEP) },
          { render: false },
        );
        return true;
      }
    }
    if (event.type === "pointerup" && this.dragging) {
      const prompt = !this.moved && pointInArea(pos, this.hitAreas.value);
      this.dragging = false;
      this.moved = false;
      if (prompt) {
        this.promptStrength(event, node, lora);
      }
      return true;
    }
    if (event.type !== "pointerdown") {
      return false;
    }
    if (event.button === 2 && pointInArea(pos, [0, this.hitAreas.lora?.[1] ?? 0, node.size[0], LORA_ROW_HEIGHT])) {
      new LiteGraph.ContextMenu(["Delete"], {
        event,
        title: lora.name,
        scale: Math.max(1, Number(app.canvas?.ds?.scale) || 1),
        className: "dark",
        callback: () => removeLoraEntry(node, this.index),
      });
      return true;
    }
    if (event.button !== 0) {
      return false;
    }
    if (pointInArea(pos, this.hitAreas.toggle)) {
      updateLoraEntry(node, this.index, { on: lora.on === false });
      return true;
    }
    if (pointInArea(pos, this.hitAreas.lora)) {
      openLoraMenu(node, event, (entry) => updateLoraEntry(node, this.index, entry));
      return true;
    }
    if (pointInArea(pos, this.hitAreas.info)) {
      showPreview(lora.name, event);
      return true;
    }
    if (pointInArea(pos, this.hitAreas.dec)) {
      updateLoraEntry(node, this.index, { strength: roundStrength((lora.strength ?? 1) - STRENGTH_STEP) });
      return true;
    }
    if (pointInArea(pos, this.hitAreas.inc)) {
      updateLoraEntry(node, this.index, { strength: roundStrength((lora.strength ?? 1) + STRENGTH_STEP) });
      return true;
    }
    if (pointInArea(pos, this.hitAreas.strengthAny)) {
      this.dragging = true;
      this.moved = false;
      return true;
    }
    return false;
  }

  promptStrength(event, node, lora) {
    app.canvas.prompt("LoRA strength", lora.strength ?? 1, (value) => {
      const next = Number(value);
      if (Number.isFinite(next)) {
        updateLoraEntry(node, this.index, { strength: roundStrength(next) });
      }
    }, event);
  }
}

class AddLoraWidget {
  constructor() {
    this.name = "easyuse_anima_add_lora";
    this.type = "custom";
    this.options = { serialize: false };
    this.serialize = false;
    this.__easyuseAnimaLoraWidget = true;
    this.hitArea = null;
  }

  computeSize(width) {
    return [width, LORA_ADD_HEIGHT];
  }

  draw(ctx, node, width, y, height) {
    const margin = 15;
    const buttonY = y + 5;
    const buttonH = height - 10;
    this.hitArea = [margin, buttonY, width - margin * 2, buttonH];
    ctx.save();
    ctx.fillStyle = LiteGraph.WIDGET_BGCOLOR;
    ctx.strokeStyle = LiteGraph.WIDGET_OUTLINE_COLOR;
    ctx.beginPath();
    roundedRect(ctx, ...this.hitArea, 5);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("+ Add LoRA", width / 2, buttonY + buttonH / 2);
    ctx.restore();
  }

  mouse(event, pos, node) {
    if (event.type !== "pointerdown" || event.button !== 0 || !pointInArea(pos, this.hitArea)) {
      return false;
    }
    openLoraMenu(node, event, (entry) => addLoraEntry(node, entry));
    return true;
  }
}

function renderProfileBar(node) {
  if (node.__easyuseAnimaProfileBar) {
    node.__easyuseAnimaProfileBar.node = node;
  }
  enforceNodeLayout(node);
}

function renderLoraWidgets(node) {
  if (!node.widgets) {
    return;
  }
  node.widgets = node.widgets.filter((widget) => !widget.__easyuseAnimaLoraWidget);
  const loras = lorasWidgetValue(node);
  if (loras.length) {
    node.widgets.push(new LoraHeaderWidget());
  }
  for (let index = 0; index < loras.length; index += 1) {
    node.widgets.push(new LoraRowWidget(index));
  }
  node.widgets.push(new AddLoraWidget());
  enforceNodeLayout(node);
}

function ensureProfileBar(node) {
  if (node.__easyuseAnimaProfileBar || !node.widgets) {
    return;
  }
  const profileBar = new ProfileBarWidget();
  profileBar.node = node;
  node.__easyuseAnimaProfileBar = profileBar;
  node.widgets = node.widgets.filter((widget) => !widget.__easyuseAnimaControlWidget);
  const insertBeforeIndex = node.widgets.findIndex((widget) => widget.name === "lora_name" || widget.name === "loras");
  if (insertBeforeIndex >= 0) {
    node.widgets.splice(insertBeforeIndex, 0, profileBar);
  } else {
    node.widgets.push(profileBar);
  }
  renderProfileBar(node);
  renderLoraWidgets(node);
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
  renderProfileBar(node);
}

function initializeNode(node) {
  if (node.__easyuseAnimaLoraPresetInitialized) {
    return;
  }
  node.__easyuseAnimaLoraPresetInitialized = true;
  node.serialize_widgets = true;
  ensureLoraStackInput(node);
  ensureProfileBar(node);
  hideInternalWidget(node, "profile_data");
  hideInternalWidget(node, "profile_count");

  wrapWidgetCallback(node, "style_prompt", () => syncAfterWidgetChange(node));
  wrapWidgetCallback(node, "loras", () => syncAfterWidgetChange(node));
  wrapWidgetCallback(node, "profile_count", () => {
    if (!node.__easyuseAnimaSuppressProfileCountCallback) {
      saveCurrentProfile(node);
      renderProfileBar(node);
    }
  });
  wrapWidgetCallback(node, "profile_index", () => {
    if (node.__easyuseAnimaSuppressProfileIndexCallback) {
      return;
    }
    const index = selectedProfileIndex(node);
    const current = activeProfileIndex(node);
    if (index !== current) {
      saveProfile(node, current);
    }
    node.__easyuseAnimaActiveProfileIndex = index;
    loadProfile(node, index);
    renderProfileBar(node);
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
      ensureProfileBar(this);
      this.__easyuseAnimaActiveProfileIndex = selectedProfileIndex(this);
      loadProfile(this, selectedProfileIndex(this), { initializeFromCurrent: true });
      renderProfileBar(this);
      enforceNodeLayout(this);
    });
  };

  window.requestAnimationFrame(() => {
    finalizeInternalWidgets(node);
    node.__easyuseAnimaActiveProfileIndex = selectedProfileIndex(node);
    loadProfile(node, selectedProfileIndex(node), { initializeFromCurrent: true });
    renderProfileBar(node);
    enforceNodeLayout(node);
  });
}

app.registerExtension({
  name: "EasyUseAnima.LoraPreset",
  init() {
    document.head.appendChild(createEl("style", {
      textContent: `
        .easyuse-anima-lora-preview {
          position: fixed;
          width: ${PREVIEW_SIZE}px;
          height: ${PREVIEW_SIZE}px;
          object-fit: contain;
          background: rgba(20, 20, 22, 0.96);
          border: 1px solid rgba(180, 180, 185, 0.45);
          z-index: 10000;
          pointer-events: none;
          display: none;
        }
        .easyuse-anima-lora-menu .easyuse-anima-combo-folder {
          opacity: 0.72;
        }
        .easyuse-anima-lora-menu .easyuse-anima-combo-folder-arrow {
          display: inline-block;
          width: 15px;
        }
        .easyuse-anima-lora-menu .easyuse-anima-combo-folder:hover {
          background-color: rgba(255, 255, 255, 0.1);
        }
        .easyuse-anima-lora-menu .easyuse-anima-combo-prefix {
          display: none;
        }
        .easyuse-anima-lora-menu:has(input:not(:placeholder-shown)) .easyuse-anima-combo-folder-contents {
          display: block !important;
        }
        .easyuse-anima-lora-menu:has(input:not(:placeholder-shown)) .easyuse-anima-combo-folder {
          display: none;
        }
        .easyuse-anima-lora-menu:has(input:not(:placeholder-shown)) .easyuse-anima-combo-prefix {
          display: inline;
        }
        .easyuse-anima-lora-menu:has(input:not(:placeholder-shown)) .litemenu-entry {
          padding-left: 2px !important;
        }
      `,
    }));

    const observer = new MutationObserver((mutations) => {
      const node = app.canvas?.current_node;
      if (!node || node.comfyClass !== NODE_TYPE) {
        return;
      }
      for (const mutation of mutations) {
        for (const removed of mutation.removedNodes) {
          if (removed.classList?.contains("litecontextmenu")) {
            hidePreview();
          }
        }
        for (const added of mutation.addedNodes) {
          if (!added.classList?.contains("litecontextmenu") || !node.__easyuseAnimaOpeningLoraMenu) {
            continue;
          }
          window.requestAnimationFrame(() => {
            updateLoraMenuTree(added);
            node.__easyuseAnimaOpeningLoraMenu = false;
          });
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
