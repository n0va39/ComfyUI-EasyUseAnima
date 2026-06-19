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
const MIN_NODE_WIDTH = 520;
const PROFILE_CONTROLS_HEIGHT = 30;
const PROFILE_ROW_HEIGHT = 22;
const PROFILE_LIST_PADDING = 4;
const PROFILE_VISIBLE_ROWS = 6;
const LORA_HEADER_HEIGHT = 24;
const LORA_ROW_HEIGHT = 20;
const LORA_ADD_HEIGHT = 36;
const STRENGTH_STEP = 0.05;
const PREVIEW_SIZE = 360;
const missingPreviewNames = new Set();
let activeLoraMenuNode = null;
const LORA_PRESET_SETTINGS = {
  nameDisplay: "name",
};
const INTERNAL_WIDGET_DEFAULTS = {
  profile_count: "4",
  lora_name: "None",
  loras: "[]",
  profile_data: "{}",
};

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
  if (values[WIDGET_INDEX.profileCount] == null || values[WIDGET_INDEX.profileCount] === "") {
    values[WIDGET_INDEX.profileCount] = INTERNAL_WIDGET_DEFAULTS.profile_count;
  }
  if (values[WIDGET_INDEX.loraName] == null || values[WIDGET_INDEX.loraName] === "") {
    values[WIDGET_INDEX.loraName] = INTERNAL_WIDGET_DEFAULTS.lora_name;
  }
  if (Array.isArray(values[WIDGET_INDEX.loras])) {
    values[WIDGET_INDEX.loras] = JSON.stringify(values[WIDGET_INDEX.loras]);
  } else if (typeof values[WIDGET_INDEX.loras] !== "string") {
    values[WIDGET_INDEX.loras] = INTERNAL_WIDGET_DEFAULTS.loras;
  }
  if (!looksLikeProfileData(values[WIDGET_INDEX.profileData])) {
    values[WIDGET_INDEX.profileData] = INTERNAL_WIDGET_DEFAULTS.profile_data;
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

function applyLoraPresetSettings(settings = {}) {
  const value = String(settings?.["lora_preset.name_display"] || "name");
  LORA_PRESET_SETTINGS.nameDisplay = value === "path" ? "path" : "name";
}

async function loadLoraPresetSettings() {
  try {
    const response = await fetch("/easyuse_anima/settings");
    if (response.ok) {
      applyLoraPresetSettings(await response.json());
    }
  } catch {
    // Keep built-in defaults when settings are not available yet.
  }
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  if (!response.ok) {
    throw new Error(data?.message || response.statusText || "Request failed");
  }
  return data;
}

function firstValue(value, fallback = null) {
  if (Array.isArray(value)) {
    return value.length ? value[0] : fallback;
  }
  return value ?? fallback;
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

function ensureWidgetValue(node, name) {
  const widget = findWidget(node, name);
  if (!widget || !Object.prototype.hasOwnProperty.call(INTERNAL_WIDGET_DEFAULTS, name)) {
    return;
  }
  const fallback = INTERNAL_WIDGET_DEFAULTS[name];
  const input = findInputEl(widget);
  const value = input ? input.value : widget.value;
  if (value == null || value === "") {
    setWidgetValue(widget, fallback);
  }
}

function profileKey(index) {
  return String(Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(index, 10) || 1)));
}

function parseProfileData(widget) {
  return normalizeProfileDataValue(widgetValue(widget, "{}"));
}

function normalizeProfileDataValue(value) {
  try {
    const parsed = typeof value === "string" ? JSON.parse(String(value || "{}")) : value;
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

function scrollProfileBarTo(node, index) {
  const bar = node.__easyuseAnimaProfileBar;
  if (!bar) {
    return;
  }
  const count = profileCount(node);
  const maxOffset = Math.max(0, count - PROFILE_VISIBLE_ROWS);
  const target = wrapProfileIndex(index, count);
  if (target <= (bar.scrollOffset || 0)) {
    bar.scrollOffset = Math.max(0, target - 1);
  } else if (target > (bar.scrollOffset || 0) + PROFILE_VISIBLE_ROWS) {
    bar.scrollOffset = Math.max(0, Math.min(maxOffset, target - PROFILE_VISIBLE_ROWS));
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

function profileContent(profile) {
  return {
    style_prompt: String(profile?.style_prompt || ""),
    loras: Array.isArray(profile?.loras)
      ? profile.loras.map(normalizeLoraEntry).filter((entry) => entry.name)
      : [],
  };
}

function profileSnapshot(profile) {
  return JSON.stringify(profileContent(profile));
}

function isMeaningfulProfile(profile) {
  const content = profileContent(profile);
  return !!content.style_prompt.trim() || content.loras.length > 0;
}

function profileSavedName(profile) {
  return String(profile?.saved_name || "").trim();
}

function withSavedMeta(content, previous) {
  const profile = profileContent(content);
  const savedName = profileSavedName(previous);
  const savedSnapshot = String(previous?.saved_snapshot || "");
  if (savedName && savedSnapshot) {
    profile.saved_name = savedName;
    profile.saved_snapshot = savedSnapshot;
  }
  return profile;
}

function currentProfileContent(node) {
  return {
    style_prompt: String(widgetValue(findWidget(node, "style_prompt"), "")),
    loras: lorasWidgetValue(node).map(normalizeLoraEntry).filter((entry) => entry.name),
  };
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
  data[key] = withSavedMeta(currentProfileContent(node), data[key]);
  writeProfileData(dataWidget, data);
}

function saveCurrentProfile(node) {
  saveProfile(node, activeProfileIndex(node));
}

function emptyProfile(index = 1) {
  return {
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
    data[key] = options.initializeFromCurrent ? currentProfileContent(node) : emptyProfile(index);
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
  scrollProfileBarTo(node, nextIndex);
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

function deleteProfile(node, index) {
  const count = profileCount(node);
  if (count <= 1) {
    return;
  }
  if (!window.confirm(`Delete profile ${index}?`)) {
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
    nextWriteIndex += 1;
  }
  writeProfileData(findWidget(node, "profile_data"), nextData);
  setProfileCount(node, count - 1);
  const nextActive = Math.min(index, count - 1);
  node.__easyuseAnimaActiveProfileIndex = nextActive;
  setProfileIndex(node, nextActive);
  loadProfile(node, nextActive);
  scrollProfileBarTo(node, nextActive);
  renderProfileBar(node);
  node.setDirtyCanvas?.(true, true);
}

function profilePayload(node) {
  saveCurrentProfile(node);
  return {
    profile_count: profileCount(node),
    profile_index: activeProfileIndex(node),
    profile_data: parseProfileData(findWidget(node, "profile_data")),
  };
}

function profileSaveStatus(node, index) {
  const profile = parseProfileData(findWidget(node, "profile_data"))[profileKey(index)] || {};
  const savedName = profileSavedName(profile);
  if (!savedName) {
    return { state: "unsaved", label: "unsaved", savedName: "" };
  }
  const dirty = String(profile.saved_snapshot || "") !== profileSnapshot(profile);
  return {
    state: dirty ? "changed" : "saved",
    label: dirty ? "changed" : "saved",
    savedName,
  };
}

function markProfilesSaved(node, name) {
  const savedName = String(name || "").trim();
  if (!savedName) {
    return;
  }
  saveCurrentProfile(node);
  const dataWidget = findWidget(node, "profile_data");
  const data = parseProfileData(dataWidget);
  const count = profileCount(node);
  for (let index = 1; index <= count; index += 1) {
    const key = profileKey(index);
    const content = profileContent(data[key]);
    data[key] = {
      ...content,
      saved_name: savedName,
      saved_snapshot: profileSnapshot(content),
    };
  }
  writeProfileData(dataWidget, data);
  loadProfile(node, activeProfileIndex(node));
}

function appendProfilePayload(node, payload) {
  saveCurrentProfile(node);
  const profile = payload?.profile || payload || {};
  const incomingData = normalizeProfileDataValue(profile.profile_data);
  const savedName = String(profile.name || "").trim();
  const incomingCount = Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(profile.profile_count, 10) || Object.keys(incomingData).length || 1));
  const incomingProfiles = [];
  for (let sourceIndex = 1; sourceIndex <= incomingCount; sourceIndex += 1) {
    const sourceProfile = incomingData[profileKey(sourceIndex)];
    if (isMeaningfulProfile(sourceProfile)) {
      incomingProfiles.push({
        sourceIndex,
        content: profileContent(sourceProfile),
      });
    }
  }
  if (!incomingProfiles.length) {
    window.alert("No non-empty profiles were found in this saved profile set.");
    return;
  }
  const currentCount = profileCount(node);
  const available = MAX_PROFILES - currentCount;
  if (available <= 0) {
    window.alert(`Cannot load more profiles. The maximum is ${MAX_PROFILES}.`);
    return;
  }
  const appendCount = Math.min(incomingProfiles.length, available);
  const targetStart = currentCount + 1;
  const data = parseProfileData(findWidget(node, "profile_data"));
  for (let offset = 0; offset < appendCount; offset += 1) {
    const targetIndex = targetStart + offset;
    const content = incomingProfiles[offset].content;
    data[profileKey(targetIndex)] = savedName
      ? {
        ...content,
        saved_name: savedName,
        saved_snapshot: profileSnapshot(content),
      }
      : content;
  }
  if (appendCount < incomingProfiles.length) {
    window.alert(`Only ${appendCount} profile(s) were loaded because the maximum is ${MAX_PROFILES}.`);
  }
  const selectedSourceIndex = wrapProfileIndex(profile.profile_index || 1, incomingCount);
  const selectedOffset = incomingProfiles.findIndex((item) => item.sourceIndex === selectedSourceIndex);
  const nextIndex = targetStart + Math.max(0, Math.min(appendCount - 1, selectedOffset < 0 ? 0 : selectedOffset));
  setProfileCount(node, currentCount + appendCount);
  writeProfileData(findWidget(node, "profile_data"), data);
  setProfileIndex(node, nextIndex);
  node.__easyuseAnimaActiveProfileIndex = nextIndex;
  loadProfile(node, nextIndex);
  scrollProfileBarTo(node, nextIndex);
  renderProfileBar(node);
  renderLoraWidgets(node);
  node.setDirtyCanvas?.(true, true);
}

async function saveProfileSet(node) {
  const name = window.prompt("Save LoRA profile set as");
  if (name == null) {
    return;
  }
  const trimmedName = name.trim();
  if (!trimmedName) {
    window.alert("Profile name is required.");
    return;
  }
  try {
    const data = await fetchJson("/easyuse_anima/lora_profiles/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: trimmedName,
        ...profilePayload(node),
      }),
    });
    markProfilesSaved(node, data?.profile?.name || trimmedName);
    renderProfileBar(node);
    node.setDirtyCanvas?.(true, true);
  } catch (error) {
    window.alert(`Failed to save profile: ${error.message || error}`);
  }
}

async function loadProfileSet(node, name) {
  try {
    const data = await fetchJson(`/easyuse_anima/lora_profiles/load?name=${encodeRFC3986URIComponent(name)}`);
    appendProfilePayload(node, data.profile);
  } catch (error) {
    window.alert(`Failed to load profile: ${error.message || error}`);
  }
}

async function openProfileLoadMenu(node, event, pos) {
  let profiles = [];
  try {
    const data = await fetchJson("/easyuse_anima/lora_profiles");
    profiles = Array.isArray(data?.profiles) ? data.profiles : [];
  } catch (error) {
    window.alert(`Failed to list profiles: ${error.message || error}`);
    return;
  }
  if (!profiles.length) {
    window.alert("No saved LoRA profiles found.");
    return;
  }
  const values = profiles.map((profile) => String(profile.name || "")).filter(Boolean);
  const clientPoint = menuClientPoint(node, pos, event);
  new LiteGraph.ContextMenu(values, {
    event: makeMenuEvent(clientPoint),
    title: "Load Profile",
    scale: Math.max(1, Number(app.canvas?.ds?.scale) || 1),
    className: "dark",
    callback: (value) => {
      const name = String(value?.content ?? value ?? "").trim();
      if (name) {
        loadProfileSet(node, name);
      }
    },
  });
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
  ensureWidgetValue(node, name);
  widget.__easyuseAnimaHidden = true;
  widget.hidden = true;
  widget.serialize = true;
  widget.computeSize = () => [0, 0];
  widget.draw = () => {};
}

function finalizeInternalWidgets(node) {
  hideInternalWidget(node, "profile_data");
  hideInternalWidget(node, "profile_count");
  hideInternalWidget(node, "lora_name");
  hideInternalWidget(node, "loras");
}

function enforceNodeLayout(node) {
  if (!node?.size || typeof node.setSize !== "function") {
    return;
  }
  const currentWidth = Number(node.size[0]) || 0;
  const currentHeight = Number(node.size[1]) || 0;
  const computed = typeof node.computeSize === "function" ? node.computeSize() : null;
  const nextWidth = currentWidth || MIN_NODE_WIDTH;
  const nextHeight = Math.max(120, Number(computed?.[1]) || currentHeight);
  if (nextWidth !== currentWidth || nextHeight !== currentHeight) {
    node.setSize([nextWidth, nextHeight]);
  }
  node.setDirtyCanvas?.(true, true);
}

function nodeWidgetWidth(node, fallbackWidth) {
  return Math.max(1, Number(node?.size?.[0]) || Number(fallbackWidth) || MIN_NODE_WIDTH);
}

function ensureLoraStackInput(node) {
  if (!node.inputs?.some((input) => input.name === "lora_stack")) {
    node.addInput?.("lora_stack", "LORA_STACK");
  }
}

function canvasPointToClient(point) {
  const canvas = app.canvas?.canvas;
  const rect = canvas?.getBoundingClientRect?.();
  const ds = app.canvas?.ds;
  const scale = Number(ds?.scale) || 1;
  const offset = Array.isArray(ds?.offset) ? ds.offset : [0, 0];
  if (!rect || !Array.isArray(point)) {
    return [window.innerWidth / 2, window.innerHeight / 2];
  }
  return [
    rect.left + (Number(point[0]) + Number(offset[0] || 0)) * scale,
    rect.top + (Number(point[1]) + Number(offset[1] || 0)) * scale,
  ];
}

function nodePosToClient(node, pos) {
  if (node?.pos && Array.isArray(pos)) {
    return canvasPointToClient([
      Number(node.pos[0] || 0) + Number(pos[0] || 0),
      Number(node.pos[1] || 0) + Number(pos[1] || 0),
    ]);
  }
  return null;
}

function makeMenuEvent(clientPoint) {
  const x = Number(clientPoint?.[0]) || window.innerWidth / 2;
  const y = Number(clientPoint?.[1]) || window.innerHeight / 2;
  return new MouseEvent("click", {
    clientX: x,
    clientY: y,
    screenX: x,
    screenY: y,
    bubbles: true,
  });
}

function menuClientPoint(node, pos, event) {
  const nodePoint = nodePosToClient(node, pos);
  if (nodePoint) {
    return [nodePoint[0] + 8, nodePoint[1] + 8];
  }
  if (Number.isFinite(event?.clientX) && Number.isFinite(event?.clientY)) {
    return [event.clientX + 8, event.clientY + 8];
  }
  return [window.innerWidth / 2, window.innerHeight / 2];
}

function positionMenu(menu, clientPoint) {
  if (!menu || !Array.isArray(clientPoint)) {
    return;
  }
  const margin = 8;
  const rect = menu.getBoundingClientRect();
  const width = rect.width || 260;
  const height = rect.height || 280;
  let left = Number(clientPoint[0]) || margin;
  let top = Number(clientPoint[1]) || margin;
  if (left + width > window.innerWidth - margin) {
    left = Math.max(margin, window.innerWidth - width - margin);
  }
  if (top + height > window.innerHeight - margin) {
    top = Math.max(margin, window.innerHeight - height - margin);
  }
  menu.style.left = `${left}px`;
  menu.style.top = `${top}px`;
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
    hidePreview();
    return;
  }
  if (missingPreviewNames.has(name)) {
    hidePreview();
    return;
  }
  let preview = document.querySelector(".easyuse-anima-lora-preview");
  if (!preview) {
    preview = createEl("img", { className: "easyuse-anima-lora-preview" });
    preview.addEventListener("error", () => {
      const failedName = preview.getAttribute("data-name");
      if (failedName) {
        missingPreviewNames.add(failedName);
      }
      preview.style.display = "none";
      preview.removeAttribute("data-name");
      preview.removeAttribute("data-loaded");
      preview.removeAttribute("data-visible");
    });
    preview.addEventListener("load", () => {
      preview.setAttribute("data-loaded", "1");
      if (preview.getAttribute("data-name") && preview.getAttribute("data-visible") === "1") {
        preview.style.display = "block";
      }
    });
    document.body.appendChild(preview);
  }
  preview.setAttribute("data-visible", "1");
  positionPreview(preview, event);
  const src = `/easyuse_anima/lora_preview?name=${encodeRFC3986URIComponent(name)}`;
  if (preview.getAttribute("data-name") !== name) {
    preview.setAttribute("data-name", name);
    preview.removeAttribute("data-loaded");
    preview.style.display = "none";
    preview.src = src;
    return;
  }
  if (preview.getAttribute("data-loaded") === "1" && preview.naturalWidth > 0) {
    preview.style.display = "block";
  }
}

function hidePreview() {
  const preview = document.querySelector(".easyuse-anima-lora-preview");
  if (preview) {
    preview.removeAttribute("data-visible");
    preview.style.display = "none";
  }
}

function loraDisplayName(name) {
  const text = String(name || "");
  if (LORA_PRESET_SETTINGS.nameDisplay === "path") {
    return text;
  }
  return text.replace(/\\/g, "/").split("/").pop() || text;
}

function openLoraMenu(node, event, pos, onChoose) {
  const values = loraNameValues(node);
  if (!values.length) {
    window.alert("No LoRA files found. Refresh ComfyUI after adding LoRAs.");
    return;
  }
  const clientPoint = menuClientPoint(node, pos, event);
  node.__easyuseAnimaOpeningLoraMenu = true;
  node.__easyuseAnimaLoraMenuPoint = clientPoint;
  activeLoraMenuNode = node;
  new LiteGraph.ContextMenu(values, {
    event: makeMenuEvent(clientPoint),
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

function updateLoraMenuTree(menu, node) {
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
  positionMenu(menu, node?.__easyuseAnimaLoraMenuPoint);
}

class ProfileBarWidget {
  constructor() {
    this.name = "easyuse_anima_profile_bar";
    this.type = "custom";
    this.options = { serialize: false };
    this.serialize = false;
    this.__easyuseAnimaControlWidget = true;
    this.hitAreas = [];
    this.scrollOffset = 0;
    this.listArea = null;
  }

  computeSize(_width, node) {
    const count = node || this.node ? profileCount(node || this.node) : 1;
    const visibleRows = Math.max(1, Math.min(PROFILE_VISIBLE_ROWS, count));
    return [
      MIN_NODE_WIDTH,
      PROFILE_CONTROLS_HEIGHT + PROFILE_LIST_PADDING * 2 + visibleRows * PROFILE_ROW_HEIGHT,
    ];
  }

  draw(ctx, node, width, y, height) {
    const drawWidth = nodeWidgetWidth(node, width);
    this.hitAreas = [];
    this.listArea = null;
    const active = activeProfileIndex(node);
    const count = profileCount(node);
    const maxOffset = Math.max(0, count - PROFILE_VISIBLE_ROWS);
    this.scrollOffset = Math.max(0, Math.min(maxOffset, this.scrollOffset || 0));

    const buttonY = y + 4;
    const buttonH = 22;
    const gap = 4;

    ctx.save();
    ctx.font = "13px sans-serif";
    ctx.textBaseline = "middle";
    ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
    ctx.globalAlpha = app.canvas.editor_alpha * 0.75;
    ctx.textAlign = "left";
    ctx.fillText(`Profile ${active}/${count}`, 10, buttonY + buttonH / 2);
    ctx.globalAlpha = 1;

    let x = Math.max(120, drawWidth - 8);

    const drawButton = (id, label, buttonW, selected = false, disabled = false) => {
      x -= buttonW;
      if (x < 8) {
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
      ctx.textAlign = "center";
      ctx.fillText(label, x + buttonW / 2, buttonY + buttonH / 2);
      x -= gap;
      ctx.globalAlpha = 1;
    };

    drawButton("load", "Load", 44);
    drawButton("save", "Save", 44);
    drawButton("delete", "X", 28, false, count <= 1);
    drawButton("add", "+", 28);

    const listX = 8;
    const listY = y + PROFILE_CONTROLS_HEIGHT + PROFILE_LIST_PADDING;
    const listW = Math.max(0, drawWidth - 16);
    const visibleRows = Math.max(1, Math.min(PROFILE_VISIBLE_ROWS, count));
    const listH = visibleRows * PROFILE_ROW_HEIGHT;
    this.listArea = [listX, listY, listW, listH];

    ctx.save();
    ctx.beginPath();
    ctx.rect(listX, listY, listW, listH);
    ctx.clip();
    for (let row = 0; row < visibleRows; row += 1) {
      const index = this.scrollOffset + row + 1;
      if (index > count) {
        break;
      }
      const rowY = listY + row * PROFILE_ROW_HEIGHT;
      const selected = index === active;
      const status = profileSaveStatus(node, index);
      const rowArea = [listX, rowY + 1, listW, PROFILE_ROW_HEIGHT - 2];
      this.hitAreas.push([...rowArea, `profile:${index}`, false]);
      ctx.fillStyle = selected ? "#3f79d8" : "rgba(255,255,255,0.045)";
      ctx.strokeStyle = selected ? "#6fa2ff" : "rgba(255,255,255,0.12)";
      ctx.beginPath();
      roundedRect(ctx, ...rowArea, 4);
      ctx.fill();
      ctx.stroke();

      const stateColor = {
        saved: "#8ecf8e",
        changed: "#e3ba66",
        unsaved: "#b8b8b8",
      }[status.state] || "#b8b8b8";
      const leftText = `${index}. ${status.savedName || "unsaved"}`;
      const rightText = status.label;
      ctx.font = "12px sans-serif";
      const rightWidth = Math.min(82, Math.max(58, ctx.measureText(rightText).width + 16));
      ctx.textAlign = "left";
      ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
      ctx.fillText(fitCanvasText(ctx, leftText, Math.max(20, listW - rightWidth - 18)), listX + 8, rowY + PROFILE_ROW_HEIGHT / 2);
      ctx.textAlign = "right";
      ctx.fillStyle = stateColor;
      ctx.fillText(rightText, listX + listW - 8, rowY + PROFILE_ROW_HEIGHT / 2);
    }
    ctx.restore();

    if (count > visibleRows) {
      const barW = 3;
      const barH = Math.max(14, listH * (visibleRows / count));
      const barY = listY + (listH - barH) * (this.scrollOffset / Math.max(1, maxOffset));
      ctx.fillStyle = "rgba(255,255,255,0.25)";
      ctx.fillRect(listX + listW - barW - 2, barY, barW, barH);
    }
    ctx.restore();
  }

  mouse(event, pos, node) {
    if (event.type === "wheel" && pointInArea(pos, this.listArea)) {
      const count = profileCount(node);
      const maxOffset = Math.max(0, count - PROFILE_VISIBLE_ROWS);
      const direction = Number(event.deltaY || 0) > 0 ? 1 : -1;
      this.scrollOffset = Math.max(0, Math.min(maxOffset, (this.scrollOffset || 0) + direction));
      node.setDirtyCanvas?.(true, true);
      return true;
    }
    if (event.type !== "pointerdown" || event.button !== 0) {
      return false;
    }
    for (const [x, y, width, height, id, disabled] of this.hitAreas) {
      if (disabled || !pointInArea(pos, [x, y, width, height])) {
        continue;
      }
      if (id === "add") {
        addProfile(node);
      } else if (id === "delete") {
        deleteProfile(node, activeProfileIndex(node));
      } else if (id === "save") {
        saveProfileSet(node);
      } else if (id === "load") {
        openProfileLoadMenu(node, event, pos);
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

  computeSize() {
    return [MIN_NODE_WIDTH, LORA_HEADER_HEIGHT];
  }

  draw(ctx, node, width, y, height) {
    const drawWidth = nodeWidgetWidth(node, width);
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
    ctx.fillText(drawWidth < 320 ? "All" : "Toggle All", margin + this.toggleArea[2] + 4, midY);
    ctx.textAlign = "center";
    ctx.fillText(drawWidth < 320 ? "Str" : "Strength", Math.max(margin + 90, drawWidth - margin - 28), midY);
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

  computeSize() {
    return [MIN_NODE_WIDTH, LORA_ROW_HEIGHT];
  }

  draw(ctx, node, width, y, height) {
    const drawWidth = nodeWidgetWidth(node, width);
    this.hitAreas = {};
    const lora = normalizeLoraEntry(lorasWidgetValue(node)[this.index]);
    if (!lora.name) {
      return;
    }
    const margin = drawWidth < 340 ? 6 : 10;
    const inner = drawWidth < 340 ? 2 : 4;
    const rowX = margin;
    const rowW = Math.max(0, drawWidth - margin * 2);
    const rowH = Math.max(16, height - 2);
    const rowY = y + 1;
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

    const showStrength = drawWidth >= 230;
    const showInfo = drawWidth >= 310;
    let nameRight = right - inner;
    if (showStrength) {
      const number = drawNumberPart(ctx, right - inner, rowY, rowH, lora.strength);
      this.hitAreas.dec = number.dec;
      this.hitAreas.value = number.value;
      this.hitAreas.inc = number.inc;
      this.hitAreas.strengthAny = number.any;
      nameRight = number.dec[0] - inner;

      if (showInfo) {
        const infoSize = 16;
        const infoX = number.dec[0] - infoSize - inner * 2;
        this.hitAreas.info = [infoX, rowY + 2, infoSize, Math.max(12, rowH - 4)];
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("i", infoX + infoSize / 2, midY);
        nameRight = infoX - inner;
      } else {
        this.hitAreas.info = null;
      }
    } else {
      this.hitAreas.dec = null;
      this.hitAreas.value = null;
      this.hitAreas.inc = null;
      this.hitAreas.strengthAny = null;
      this.hitAreas.info = null;
    }

    const nameW = Math.max(0, nameRight - posX - inner);
    this.hitAreas.lora = [posX, y, nameW, height];
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    if (nameW > 4) {
      ctx.fillText(fitCanvasText(ctx, loraDisplayName(lora.name), nameW), posX, midY);
    }
    ctx.restore();
  }

  mouse(event, pos, node) {
    const lora = normalizeLoraEntry(lorasWidgetValue(node)[this.index]);
    if (!lora.name) {
      return false;
    }
    if (event.type === "pointerout" || event.type === "pointerleave" || event.type === "pointercancel") {
      hidePreview();
      this.dragging = false;
      this.moved = false;
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
      openLoraMenu(node, event, pos, (entry) => updateLoraEntry(node, this.index, entry));
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

  computeSize() {
    return [MIN_NODE_WIDTH, LORA_ADD_HEIGHT];
  }

  draw(ctx, node, width, y, height) {
    const drawWidth = nodeWidgetWidth(node, width);
    const margin = 15;
    const buttonY = y + 5;
    const buttonH = height - 10;
    this.hitArea = [margin, buttonY, Math.max(0, drawWidth - margin * 2), buttonH];
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
    ctx.fillText("+ Add LoRA", drawWidth / 2, buttonY + buttonH / 2);
    ctx.restore();
  }

  mouse(event, pos, node) {
    if (event.type !== "pointerdown" || event.button !== 0 || !pointInArea(pos, this.hitArea)) {
      return false;
    }
    openLoraMenu(node, event, pos, (entry) => addLoraEntry(node, entry));
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

function applyExecutedProfile(node, message) {
  const payload = firstValue(message?.lora_preset_profile, null);
  const index = Number.parseInt(payload?.profile_index, 10);
  if (!Number.isFinite(index)) {
    return;
  }
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
  scrollProfileBarTo(node, nextIndex);
  renderProfileBar(node);
  renderLoraWidgets(node);
  node.setDirtyCanvas?.(true, true);
}

function refreshLoraPresetNodes() {
  const nodes = app.graph?._nodes || [];
  for (const node of nodes) {
    if (node?.comfyClass !== NODE_TYPE) {
      continue;
    }
    renderLoraWidgets(node);
    renderProfileBar(node);
    node.setDirtyCanvas?.(true, true);
  }
}

function initializeNode(node) {
  if (node.__easyuseAnimaLoraPresetInitialized) {
    return;
  }
  node.__easyuseAnimaLoraPresetInitialized = true;
  node.serialize_widgets = true;
  ensureLoraStackInput(node);
  ensureProfileBar(node);
  for (const name of Object.keys(INTERNAL_WIDGET_DEFAULTS)) {
    ensureWidgetValue(node, name);
  }
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
    scrollProfileBarTo(node, index);
    renderProfileBar(node);
  });

  const originalOnSerialize = node.onSerialize;
  node.onSerialize = function (workflowNode) {
    saveCurrentProfile(this);
    originalOnSerialize?.apply(this, arguments);
    const dataWidget = findWidget(this, "profile_data");
    if (workflowNode?.widgets_values && dataWidget) {
      workflowNode.widgets_values[WIDGET_INDEX.profileCount] = String(widgetValue(findWidget(this, "profile_count"), profileCount(this)) || "4");
      workflowNode.widgets_values[WIDGET_INDEX.loraName] = widgetValue(findWidget(this, "lora_name"), "None");
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
      scrollProfileBarTo(this, selectedProfileIndex(this));
      renderProfileBar(this);
      enforceNodeLayout(this);
    });
  };

  window.requestAnimationFrame(() => {
    finalizeInternalWidgets(node);
    node.__easyuseAnimaActiveProfileIndex = selectedProfileIndex(node);
    loadProfile(node, selectedProfileIndex(node), { initializeFromCurrent: true });
    scrollProfileBarTo(node, selectedProfileIndex(node));
    renderProfileBar(node);
    enforceNodeLayout(node);
  });
}

app.registerExtension({
  name: "EasyUseAnima.LoraPreset",
  init() {
    loadLoraPresetSettings().then(refreshLoraPresetNodes);
    window.addEventListener("easyuse-anima-settings-updated", (event) => {
      applyLoraPresetSettings(event.detail || {});
      refreshLoraPresetNodes();
    });
    document.addEventListener("pointerdown", hidePreview, true);

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
      const node = activeLoraMenuNode || app.canvas?.current_node;
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
            updateLoraMenuTree(added, node);
            node.__easyuseAnimaOpeningLoraMenu = false;
            activeLoraMenuNode = null;
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
    const originalOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      originalOnExecuted?.apply(this, arguments);
      applyExecutedProfile(this, message);
    };
  },
});
