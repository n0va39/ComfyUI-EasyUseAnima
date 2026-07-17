import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { easyuseAnimaEncodeRFC3986URIComponent as encodeRFC3986URIComponent, easyuseAnimaFetchJson, easyuseAnimaGetSettings } from "./easyuse_anima_api.js";
import { easyuseAnimaText, easyuseAnimaWatchLocale } from "./easyuse_anima_i18n.js";
import { createLoraPresetApiClient } from "./lora_preset/api_client.js";
import { createLoraPresetCanvasWidgets } from "./lora_preset/canvas_widgets.js";
import { createLoraPresetMenuLifecycle } from "./lora_preset/menu_lifecycle.js";
import { createLoraPresetNodeRuntime } from "./lora_preset/node_runtime.js";
import { createLoraPresetProfileMutations } from "./lora_preset/profile_mutations.js";
import { createLoraPresetPreviewLifecycle } from "./lora_preset/preview_lifecycle.js";
import { createLoraPresetSaveSync } from "./lora_preset/save_sync.js";
import {
  INTERNAL_WIDGET_DEFAULTS,
  MAX_PROFILES,
  WIDGET_INDEX,
  normalizeLoraEntry,
  normalizeProfileDataValue,
  normalizeSerializedWidgets,
  profileKey,
  profileSavedName,
  wrapProfileIndex,
} from "./lora_preset/profile_data.js";
import {
  buildLoraLookup,
  hasLoraPathProblem,
  isAnyLoraFixPending,
  isLoraFixPending,
  localLoraMatch,
  loraFixPendingSet,
  normalizeLoraNameList,
  validComboEntryText,
} from "./lora_preset/lora_state.js";

const NODE_TYPE = "EasyUseAnimaLoraPreset";
const DEFAULT_STRENGTH_BUTTON_STEP = 0.05;
const DEFAULT_STRENGTH_DRAG_STEP = 0.05;
const DEFAULT_STRENGTH_DRAG_PIXELS = 8;
const PREVIEW_SIZE = 360;
let activeProfileWheelTarget = null;
let profileWheelListenerInstalled = false;
const LORA_PRESET_SETTINGS = {
  nameDisplay: "name",
  menuMode: "tree",
  strengthButtonStep: DEFAULT_STRENGTH_BUTTON_STEP,
  strengthDragStep: DEFAULT_STRENGTH_DRAG_STEP,
  strengthDragPixels: DEFAULT_STRENGTH_DRAG_PIXELS,
};

function getActiveProfileWheelTarget() {
  return activeProfileWheelTarget;
}

function setActiveProfileWheelTarget(target) {
  activeProfileWheelTarget = target;
}

const LORA_PRESET_TEXT = {
  en: {
    "profile.deleteConfirm": "Delete profile {index}?",
    "profile.unsaved": "unsaved",
    "profile.changed": "changed",
    "profile.saved": "saved",
    "profile.noNonEmpty": "No non-empty profiles were found in this saved profile set.",
    "profile.maxReached": "Cannot load more profiles. The maximum is {max}.",
    "profile.partialLoad": "Only {count} profile(s) were loaded because the maximum is {max}.",
    "profile.savePrompt": "Save LoRA profile set as",
    "profile.nameRequired": "Profile name is required.",
    "profile.saveFailed": "Failed to save profile: {message}",
    "profile.loadFailed": "Failed to load profile: {message}",
    "profile.listFailed": "Failed to list profiles: {message}",
    "profile.noneSaved": "No saved LoRA profiles found.",
    "profile.loadTitle": "Load Profile",
    "profile.header": "Profile {active}/{count}",
    "profile.load": "Load",
    "profile.save": "Save",
    "profile.fix": "FIX",
    "profile.fixResult": "Fixed {fixed} LoRA path(s). {unresolved} unresolved.",
    "profile.fixFailed": "Failed to fix LoRA paths: {message}",
    "profile.fixNoIssue": "No missing LoRA paths found.",
    "lora.moveUp": "Move Up",
    "lora.moveDown": "Move Down",
    "lora.fix": "FIX",
    "lora.fixFailed": "Failed to fix LoRA path: {message}",
    "lora.fixNoIssue": "This LoRA path exists.",
    "lora.fixUnresolved": "No matching local LoRA was found.",
    "lora.remove": "Remove",
    "lora.noneFound": "No LoRA files found. Refresh ComfyUI after adding LoRAs.",
    "lora.chooseTitle": "Choose a LoRA",
    "lora.search": "Search LoRA",
    "lora.allShort": "All",
    "lora.toggleAll": "Toggle All",
    "lora.strengthShort": "Str",
    "lora.strength": "Strength",
    "lora.strengthPrompt": "LoRA strength",
    "lora.add": "+ Add LoRA",
  },
  ko: {
    "profile.deleteConfirm": "프로필 {index}을 삭제할까요?",
    "profile.unsaved": "미저장",
    "profile.changed": "변경됨",
    "profile.saved": "저장됨",
    "profile.noNonEmpty": "저장된 프로필 세트에서 비어 있지 않은 프로필을 찾지 못했습니다.",
    "profile.maxReached": "프로필을 더 불러올 수 없습니다. 최대 개수는 {max}개입니다.",
    "profile.partialLoad": "최대 {max}개 제한 때문에 {count}개 프로필만 불러왔습니다.",
    "profile.savePrompt": "LoRA 프로필 세트 이름",
    "profile.nameRequired": "프로필 이름이 필요합니다.",
    "profile.saveFailed": "프로필 저장 실패: {message}",
    "profile.loadFailed": "프로필 불러오기 실패: {message}",
    "profile.listFailed": "프로필 목록 불러오기 실패: {message}",
    "profile.noneSaved": "저장된 LoRA 프로필이 없습니다.",
    "profile.loadTitle": "프로필 불러오기",
    "profile.header": "프로필 {active}/{count}",
    "profile.load": "불러오기",
    "profile.save": "저장",
    "profile.fix": "FIX",
    "profile.fixResult": "LoRA 경로 {fixed}개를 교정했습니다. 미해결 {unresolved}개.",
    "profile.fixFailed": "LoRA 경로 교정 실패: {message}",
    "profile.fixNoIssue": "누락된 LoRA 경로가 없습니다.",
    "lora.moveUp": "위로 이동",
    "lora.moveDown": "아래로 이동",
    "lora.fix": "FIX",
    "lora.fixFailed": "LoRA 경로 교정 실패: {message}",
    "lora.fixNoIssue": "이 LoRA 경로는 존재합니다.",
    "lora.fixUnresolved": "일치하는 로컬 LoRA를 찾지 못했습니다.",
    "lora.remove": "제거",
    "lora.noneFound": "LoRA 파일을 찾지 못했습니다. LoRA를 추가한 뒤 ComfyUI를 새로고침하세요.",
    "lora.chooseTitle": "LoRA 선택",
    "lora.search": "LoRA 검색",
    "lora.allShort": "전체",
    "lora.toggleAll": "전체 토글",
    "lora.strengthShort": "강도",
    "lora.strength": "강도",
    "lora.strengthPrompt": "LoRA 강도",
    "lora.add": "+ LoRA 추가",
  },
  ja: {
    "profile.deleteConfirm": "プロファイル {index} を削除しますか?",
    "profile.unsaved": "未保存",
    "profile.changed": "変更あり",
    "profile.saved": "保存済み",
    "profile.noNonEmpty": "保存済みプロファイルセットに空でないプロファイルがありません。",
    "profile.maxReached": "これ以上プロファイルを読み込めません。最大数は {max} です。",
    "profile.partialLoad": "最大 {max} 件の制限により、{count} 件のプロファイルだけを読み込みました。",
    "profile.savePrompt": "LoRA プロファイルセット名",
    "profile.nameRequired": "プロファイル名が必要です。",
    "profile.saveFailed": "プロファイルの保存に失敗しました: {message}",
    "profile.loadFailed": "プロファイルの読み込みに失敗しました: {message}",
    "profile.listFailed": "プロファイル一覧の取得に失敗しました: {message}",
    "profile.noneSaved": "保存済み LoRA プロファイルがありません。",
    "profile.loadTitle": "プロファイルを読み込む",
    "profile.header": "プロファイル {active}/{count}",
    "profile.load": "読み込み",
    "profile.save": "保存",
    "profile.fix": "FIX",
    "profile.fixResult": "{fixed} 件の LoRA パスを修正しました。未解決 {unresolved} 件。",
    "profile.fixFailed": "LoRA パスの修正に失敗しました: {message}",
    "profile.fixNoIssue": "欠落した LoRA パスはありません。",
    "lora.moveUp": "上へ移動",
    "lora.moveDown": "下へ移動",
    "lora.fix": "FIX",
    "lora.fixFailed": "LoRA パスの修正に失敗しました: {message}",
    "lora.fixNoIssue": "この LoRA パスは存在します。",
    "lora.fixUnresolved": "一致するローカル LoRA が見つかりません。",
    "lora.remove": "削除",
    "lora.noneFound": "LoRA ファイルが見つかりません。LoRA を追加した後に ComfyUI を更新してください。",
    "lora.chooseTitle": "LoRA を選択",
    "lora.search": "LoRA 検索",
    "lora.allShort": "全て",
    "lora.toggleAll": "全て切替",
    "lora.strengthShort": "強度",
    "lora.strength": "強度",
    "lora.strengthPrompt": "LoRA 強度",
    "lora.add": "+ LoRA 追加",
  },
  zh: {
    "profile.deleteConfirm": "删除配置 {index}？",
    "profile.unsaved": "未保存",
    "profile.changed": "已更改",
    "profile.saved": "已保存",
    "profile.noNonEmpty": "保存的配置集中没有非空配置。",
    "profile.maxReached": "无法加载更多配置。最大数量为 {max}。",
    "profile.partialLoad": "由于最大限制为 {max}，只加载了 {count} 个配置。",
    "profile.savePrompt": "LoRA 配置集名称",
    "profile.nameRequired": "需要配置名称。",
    "profile.saveFailed": "保存配置失败：{message}",
    "profile.loadFailed": "加载配置失败：{message}",
    "profile.listFailed": "获取配置列表失败：{message}",
    "profile.noneSaved": "没有保存的 LoRA 配置。",
    "profile.loadTitle": "加载配置",
    "profile.header": "配置 {active}/{count}",
    "profile.load": "加载",
    "profile.save": "保存",
    "profile.fix": "FIX",
    "profile.fixResult": "已修复 {fixed} 个 LoRA 路径。未解决 {unresolved} 个。",
    "profile.fixFailed": "修复 LoRA 路径失败：{message}",
    "profile.fixNoIssue": "没有缺失的 LoRA 路径。",
    "lora.moveUp": "上移",
    "lora.moveDown": "下移",
    "lora.fix": "FIX",
    "lora.fixFailed": "修复 LoRA 路径失败：{message}",
    "lora.fixNoIssue": "此 LoRA 路径存在。",
    "lora.fixUnresolved": "未找到匹配的本地 LoRA。",
    "lora.remove": "移除",
    "lora.noneFound": "未找到 LoRA 文件。添加 LoRA 后请刷新 ComfyUI。",
    "lora.chooseTitle": "选择 LoRA",
    "lora.search": "搜索 LoRA",
    "lora.allShort": "全部",
    "lora.toggleAll": "全部切换",
    "lora.strengthShort": "强度",
    "lora.strength": "强度",
    "lora.strengthPrompt": "LoRA 强度",
    "lora.add": "+ 添加 LoRA",
  },
};
function lpText(key) {
  return easyuseAnimaText(LORA_PRESET_TEXT, key);
}

function lpFormat(key, values = {}) {
  return lpText(key).replace(/\{(\w+)\}/g, (_match, name) => values[name] ?? "");
}

function errorMessage(error) {
  return String(error?.message || error || "");
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
  const menuMode = String(settings?.["lora_preset.menu_mode"] || "tree");
  LORA_PRESET_SETTINGS.menuMode = menuMode === "list" ? "list" : "tree";
  LORA_PRESET_SETTINGS.strengthButtonStep = parseStrengthStep(
    settings?.["lora_preset.strength_button_step"],
    DEFAULT_STRENGTH_BUTTON_STEP,
    0.5,
  );
  LORA_PRESET_SETTINGS.strengthDragStep = parseStrengthStep(
    settings?.["lora_preset.strength_drag_step"],
    DEFAULT_STRENGTH_DRAG_STEP,
    0.2,
  );
  LORA_PRESET_SETTINGS.strengthDragPixels = parseStrengthDragPixels(settings?.["lora_preset.strength_drag_pixels"]);
}

function parseStrengthStep(value, fallback, maxValue) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return fallback;
  }
  return Math.max(0.001, Math.min(maxValue, number));
}

function parseStrengthDragPixels(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return DEFAULT_STRENGTH_DRAG_PIXELS;
  }
  return Math.max(1, Math.min(100, Math.round(number)));
}

async function loadLoraPresetSettings() {
  try {
    const settings = await easyuseAnimaGetSettings({ fallback: null });
    if (settings) {
      applyLoraPresetSettings(settings);
    }
  } catch {
    // Keep built-in defaults when settings are not available yet.
  }
}

async function fetchJson(url, options = {}) {
  const fetcher = typeof api?.fetchApi === "function"
    ? (requestUrl, requestOptions) => api.fetchApi(requestUrl, requestOptions)
    : fetch;
  return easyuseAnimaFetchJson(url, { ...options, fetcher });
}

const loraPresetApi = createLoraPresetApiClient({
  fetchJson,
  encodeURIComponent: encodeRFC3986URIComponent,
});
const loraPreviewLifecycle = createLoraPresetPreviewLifecycle({
  document,
  encodeURIComponent: encodeRFC3986URIComponent,
  previewSize: PREVIEW_SIZE,
});
const loraMenuLifecycle = createLoraPresetMenuLifecycle({
  document,
  window,
  MutationObserver,
  createElement: createEl,
  validComboEntryText,
  previewLifecycle: loraPreviewLifecycle,
  positionMenu,
  text: lpText,
  getMenuMode: () => LORA_PRESET_SETTINGS.menuMode,
  getCurrentNode: () => app.canvas?.current_node,
  nodeType: NODE_TYPE,
  previewSize: PREVIEW_SIZE,
});
let loraCanvasWidgets;
const loraProfileMutations = createLoraPresetProfileMutations({
  findWidget,
  widgetValue,
  setWidgetValue,
  lorasWidgetValue,
  setLorasWidgetValue,
  getCanvasWidgets: () => loraCanvasWidgets,
  text: lpText,
  formatText: lpFormat,
  apiClient: loraPresetApi,
  errorMessage,
  host: window,
});
const {
  parseProfileData,
  writeProfileData,
  profileCount,
  selectedProfileIndex,
  activeProfileIndex,
  setProfileIndex,
  setProfileCount,
  scrollProfileBarTo,
  currentProfileContent,
  saveProfile,
  saveCurrentProfile,
  loadProfile,
  switchProfile,
  addProfile,
  deleteProfile,
  selectedProfilePayload,
  profileSaveStatus,
  appendProfilePayload,
  saveProfileSet,
  loadProfileSet,
  fullProfilePayload,
  mutateLoras,
  addLoraEntry,
  updateLoraEntry,
  removeLoraEntry,
  moveLoraEntry,
} = loraProfileMutations;
loraCanvasWidgets = createLoraPresetCanvasWidgets({
  getCanvas: () => app.canvas,
  getLiteGraph: () => LiteGraph,
  getSettings: () => LORA_PRESET_SETTINGS,
  text: lpText,
  formatText: lpFormat,
  normalizeLoraEntry,
  lorasWidgetValue,
  mutateLoras,
  updateLoraEntry,
  loraResolveState,
  hasLoraPathProblem,
  isAnyLoraFixPending,
  isLoraFixPending,
  loraDisplayName,
  previewLifecycle: loraPreviewLifecycle,
  openLoraMenu,
  openLoraEntryMenu,
  addLoraEntry,
  fixSingleLoraEntry,
  profileCount,
  activeProfileIndex,
  profileSaveStatus,
  addProfile,
  deleteProfile,
  saveProfileSet,
  openProfileLoadMenu,
  fixProfileLoras,
  switchProfile,
  nodePosToClient,
  getActiveProfileWheelTarget,
  setActiveProfileWheelTarget,
  enforceNodeLayout,
});
const loraPresetNodeRuntime = createLoraPresetNodeRuntime({
  nodeTypeName: NODE_TYPE,
  internalWidgetDefaults: INTERNAL_WIDGET_DEFAULTS,
  widgetIndex: WIDGET_INDEX,
  findWidget,
  findInputEl,
  widgetValue,
  ensureWidgetValue,
  resetInternalLoraSelector,
  normalizeSerializedWidgets,
  profileCount,
  selectedProfileIndex,
  activeProfileIndex,
  wrapProfileIndex,
  setProfileIndex,
  lorasWidgetValue,
  saveProfile,
  saveCurrentProfile,
  loadProfile,
  scrollProfileBarTo,
  refreshLoraAvailability,
  canvasWidgets: loraCanvasWidgets,
  enforceNodeLayout,
  requestAnimationFrame: (callback) => window.requestAnimationFrame(callback),
});
const loraPresetSaveSync = createLoraPresetSaveSync({
  app,
  nodeTypeName: NODE_TYPE,
  saveCurrentProfile,
});

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

function resetInternalLoraSelector(node) {
  const widget = findWidget(node, "lora_name");
  if (!widget) {
    return;
  }
  if (widgetValue(widget, "") !== INTERNAL_WIDGET_DEFAULTS.lora_name) {
    setWidgetValue(widget, INTERNAL_WIDGET_DEFAULTS.lora_name);
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
    loraCanvasWidgets.renderLoraWidgets(node);
  } else {
    node.setDirtyCanvas?.(true, true);
  }
}

async function openProfileLoadMenu(node, event, pos) {
  let profiles = [];
  try {
    const data = await loraPresetApi.listProfiles();
    profiles = Array.isArray(data?.profiles) ? data.profiles : [];
  } catch (error) {
    window.alert(lpFormat("profile.listFailed", { message: errorMessage(error) }));
    return;
  }
  if (!profiles.length) {
    window.alert(lpText("profile.noneSaved"));
    return;
  }
  const values = profiles.map((profile) => String(profile.name || "")).filter(Boolean);
  const clientPoint = menuClientPoint(node, pos, event);
  new LiteGraph.ContextMenu(values, {
    event: makeMenuEvent(clientPoint),
    title: lpText("profile.loadTitle"),
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

function profileHasLoraPathProblems(node) {
  const data = parseProfileData(findWidget(node, "profile_data"));
  const count = profileCount(node);
  for (let index = 1; index <= count; index += 1) {
    const profile = data[profileKey(index)];
    const loras = Array.isArray(profile?.loras) ? profile.loras : [];
    for (const lora of loras) {
      if (hasLoraPathProblem(loraResolveState(node, lora))) {
        return true;
      }
    }
  }
  return false;
}

async function refreshLoraLookupForFix(node) {
  await fetchLoraNameValues(node);
}

function applyFixedProfilePayload(node, payload) {
  const dataWidget = findWidget(node, "profile_data");
  if (!dataWidget || !payload || typeof payload !== "object") {
    return;
  }
  const previousData = parseProfileData(dataWidget);
  const nextData = normalizeProfileDataValue(payload.profile_data);
  for (const [key, profile] of Object.entries(nextData)) {
    const previous = previousData[key];
    const savedName = profileSavedName(previous);
    const savedSnapshot = String(previous?.saved_snapshot || "");
    if (savedName && savedSnapshot) {
      profile.saved_name = savedName;
      profile.saved_snapshot = savedSnapshot;
    }
  }
  const nextCount = Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(payload.profile_count, 10) || profileCount(node)));
  const nextIndex = wrapProfileIndex(payload.profile_index || activeProfileIndex(node), nextCount);
  setProfileCount(node, nextCount);
  writeProfileData(dataWidget, nextData);
  setProfileIndex(node, nextIndex);
  node.__easyuseAnimaActiveProfileIndex = nextIndex;
  loadProfile(node, nextIndex);
  scrollProfileBarTo(node, nextIndex);
  loraCanvasWidgets.renderProfileBar(node);
  loraCanvasWidgets.renderLoraWidgets(node);
  refreshLoraAvailability(node);
  node.setDirtyCanvas?.(true, true);
}

async function fixProfileLoras(node) {
  if (isAnyLoraFixPending(node)) {
    return;
  }
  node.__easyuseAnimaProfileFixPending = true;
  loraCanvasWidgets.renderProfileBar(node);
  loraCanvasWidgets.renderLoraWidgets(node);
  try {
    await refreshLoraLookupForFix(node);
    saveCurrentProfile(node);
    if (!profileHasLoraPathProblems(node)) {
      window.alert(lpText("profile.fixNoIssue"));
      return;
    }
    const data = await loraPresetApi.fixProfile(fullProfilePayload(node));
    const profile = data?.profile || data || {};
    applyFixedProfilePayload(node, profile);
    window.alert(lpFormat("profile.fixResult", {
      fixed: Array.isArray(profile.fixed) ? profile.fixed.length : 0,
      unresolved: Array.isArray(profile.unresolved) ? profile.unresolved.length : 0,
    }));
  } catch (error) {
    window.alert(lpFormat("profile.fixFailed", { message: errorMessage(error) }));
  } finally {
    node.__easyuseAnimaProfileFixPending = false;
    loraCanvasWidgets.renderProfileBar(node);
    loraCanvasWidgets.renderLoraWidgets(node);
  }
}

async function fixSingleLoraEntry(node, index) {
  if (isLoraFixPending(node, index)) {
    return;
  }
  loraFixPendingSet(node).add(index);
  loraCanvasWidgets.renderLoraWidgets(node);
  saveCurrentProfile(node);
  const loras = lorasWidgetValue(node).map(normalizeLoraEntry);
  const lora = loras[index];
  if (!lora?.name) {
    loraFixPendingSet(node).delete(index);
    loraCanvasWidgets.renderLoraWidgets(node);
    return;
  }
  try {
    await refreshLoraLookupForFix(node);
    if (!hasLoraPathProblem(loraResolveState(node, lora))) {
      window.alert(lpText("lora.fixNoIssue"));
      return;
    }
    const data = await loraPresetApi.fixProfile({
      profile_count: 1,
      profile_index: 1,
      profile_data: {
        "1": {
          style_prompt: "",
          loras: [lora],
        },
      },
    });
    const profile = data?.profile || data || {};
    const fixedLora = normalizeLoraEntry(profile?.profile_data?.["1"]?.loras?.[0] || {});
    const fixedCount = Array.isArray(profile.fixed) ? profile.fixed.length : 0;
    const unresolvedCount = Array.isArray(profile.unresolved) ? profile.unresolved.length : 0;
    if (fixedLora.name && (fixedCount > 0 || fixedLora.name !== lora.name)) {
      mutateLoras(node, (nextLoras) => {
        if (nextLoras[index]) {
          nextLoras[index] = fixedLora;
        }
      });
      refreshLoraAvailability(node);
      return;
    }
    if (unresolvedCount > 0 || hasLoraPathProblem(loraResolveState(node, lora))) {
      window.alert(lpText("lora.fixUnresolved"));
    }
  } catch (error) {
    window.alert(lpFormat("lora.fixFailed", { message: errorMessage(error) }));
  } finally {
    loraFixPendingSet(node).delete(index);
    loraCanvasWidgets.renderLoraWidgets(node);
  }
}

function comboValues(widget) {
  const raw = widget?.options?.values || widget?.values || widget?.inputSpec?.[0] || [];
  if (Array.isArray(raw)) {
    return raw;
  }
  if (raw && typeof raw === "object") {
    return Object.entries(raw).flatMap(([key, value]) => [key, value]);
  }
  return [];
}

function loraNameValues(node) {
  return normalizeLoraNameList(comboValues(findWidget(node, "lora_name")));
}

function loraResolveState(node, lora) {
  return localLoraMatch(normalizeLoraEntry(lora), node?.__easyuseAnimaLoraLookup);
}

function setLoraLookup(node, values) {
  if (!node) {
    return;
  }
  node.__easyuseAnimaLoraLookup = buildLoraLookup(values);
  loraCanvasWidgets.renderLoraWidgets(node);
}

async function fetchLoraNameValues(node) {
  try {
    const data = await loraPresetApi.listLoras();
    const values = normalizeLoraNameList(data?.loras);
    for (const name of values) {
      loraPreviewLifecycle.forgetMissingPreview(name);
    }
    setLoraLookup(node, values);
    return values;
  } catch (error) {
    console.warn("[EasyUse Anima] failed to refresh LoRA list; using cached widget values", error);
    const values = loraNameValues(node);
    setLoraLookup(node, values);
    return values;
  }
}

function refreshLoraAvailability(node) {
  fetchLoraNameValues(node).catch((error) => {
    console.warn("[EasyUse Anima] failed to refresh LoRA availability", error);
  });
}

function loraEntryFromName(name, base = {}) {
  return normalizeLoraEntry({
    name,
    on: base.on ?? true,
    strength: base.strength ?? 1,
    strengthTwo: base.strengthTwo ?? null,
  });
}

function openLoraEntryMenu(node, event, index) {
  const lora = normalizeLoraEntry(lorasWidgetValue(node)[index]);
  if (!lora.name) {
    return;
  }
  const loras = lorasWidgetValue(node);
  const state = loraResolveState(node, lora);
  const items = [
    {
      content: lpText("lora.moveUp"),
      disabled: index <= 0,
      callback: () => moveLoraEntry(node, index, -1),
    },
    {
      content: lpText("lora.moveDown"),
      disabled: index >= loras.length - 1,
      callback: () => moveLoraEntry(node, index, 1),
    },
    null,
  ];
  if (hasLoraPathProblem(state)) {
    items.push({
      content: lpText("lora.fix"),
      disabled: isLoraFixPending(node, index),
      callback: () => fixSingleLoraEntry(node, index),
    }, null);
  }
  items.push(
    {
      content: lpText("lora.remove"),
      callback: () => removeLoraEntry(node, index),
    },
  );
  new LiteGraph.ContextMenu(items, {
    event,
    title: loraDisplayName(lora.name),
    scale: Math.max(1, Number(app.canvas?.ds?.scale) || 1),
    className: "dark",
  });
}

function enforceNodeLayout(node) {
  if (!node?.size || typeof node.setSize !== "function") {
    return;
  }
  const currentWidth = Number(node.size[0]) || 0;
  const currentHeight = Number(node.size[1]) || 0;
  const computed = typeof node.computeSize === "function" ? node.computeSize() : null;
  const nextWidth = currentWidth || loraCanvasWidgets.minNodeWidth;
  const nextHeight = Math.max(120, Number(computed?.[1]) || currentHeight);
  if (nextWidth !== currentWidth || nextHeight !== currentHeight) {
    node.setSize([nextWidth, nextHeight]);
  }
  node.setDirtyCanvas?.(true, true);
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

function clientPointToCanvas(event) {
  const canvas = app.canvas?.canvas;
  if (app.canvas?.convertEventToCanvasOffset) {
    return app.canvas.convertEventToCanvasOffset(event);
  }
  const rect = canvas?.getBoundingClientRect?.();
  const ds = app.canvas?.ds;
  const scale = Number(ds?.scale) || 1;
  const offset = Array.isArray(ds?.offset) ? ds.offset : [0, 0];
  if (!rect) {
    return [0, 0];
  }
  return [
    (Number(event?.clientX || 0) - rect.left) / scale - Number(offset[0] || 0),
    (Number(event?.clientY || 0) - rect.top) / scale - Number(offset[1] || 0),
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

function loraDisplayName(name) {
  const text = String(name || "");
  if (LORA_PRESET_SETTINGS.nameDisplay === "path") {
    return text;
  }
  return text.replace(/\\/g, "/").split("/").pop() || text;
}

async function openLoraMenu(node, event, pos, onChoose) {
  const clientPoint = menuClientPoint(node, pos, event);
  const values = await fetchLoraNameValues(node);
  const menuItems = loraMenuLifecycle.createMenuItems(values);
  if (!menuItems.length) {
    window.alert(lpText("lora.noneFound"));
    return;
  }
  loraMenuLifecycle.activateMenu(node, clientPoint, menuItems);
  new LiteGraph.ContextMenu(menuItems, {
    event: makeMenuEvent(clientPoint),
    title: lpText("lora.chooseTitle"),
    scale: Math.max(1, Number(app.canvas?.ds?.scale) || 1),
    className: "dark easyuse-anima-lora-menu",
    callback: (value) => {
      const name = validComboEntryText(value);
      if (name) {
        onChoose(loraEntryFromName(name));
      }
    },
  });
}

function refreshLoraPresetNodes() {
  const nodes = app.graph?._nodes || [];
  for (const node of nodes) {
    if (node?.comfyClass !== NODE_TYPE) {
      continue;
    }
    loraCanvasWidgets.renderLoraWidgets(node);
    loraCanvasWidgets.renderProfileBar(node);
    node.setDirtyCanvas?.(true, true);
  }
}

function scrollProfileListFromWheel(event) {
  const clientPos = [Number(event?.clientX || 0), Number(event?.clientY || 0)];
  if (
    activeProfileWheelTarget?.node?.comfyClass === NODE_TYPE
    && activeProfileWheelTarget?.widget
    && (performance.now() - activeProfileWheelTarget.time) < 30000
    && (app.graph?._nodes || []).includes(activeProfileWheelTarget.node)
  ) {
    if (!loraCanvasWidgets.pointInArea(clientPos, activeProfileWheelTarget.widget.listClientArea)) {
      activeProfileWheelTarget = null;
    } else {
      activeProfileWheelTarget.time = performance.now();
      const handled = activeProfileWheelTarget.widget.scrollByWheel(event.deltaY, activeProfileWheelTarget.node);
      if (handled) {
        event.preventDefault?.();
        event.stopPropagation?.();
        return true;
      }
    }
  }

  const nodesByZ = [...(app.graph?._nodes || [])].reverse();
  for (const node of nodesByZ) {
    const bar = node?.comfyClass === NODE_TYPE ? node.__easyuseAnimaProfileBar : null;
    if (!bar || !loraCanvasWidgets.pointInArea(clientPos, bar.listClientArea)) {
      continue;
    }
    const handled = bar.scrollByWheel(event.deltaY, node);
    if (handled) {
      activeProfileWheelTarget = {
        node,
        widget: bar,
        time: performance.now(),
      };
      event.preventDefault?.();
      event.stopPropagation?.();
      return true;
    }
  }

  const canvas = app.canvas?.canvas;
  const rect = canvas?.getBoundingClientRect?.();
  if (
    !canvas
    || !rect
    || Number(event?.clientX || 0) < rect.left
    || Number(event?.clientX || 0) > rect.right
    || Number(event?.clientY || 0) < rect.top
    || Number(event?.clientY || 0) > rect.bottom
  ) {
    return false;
  }
  const graphPoint = clientPointToCanvas(event);
  for (const node of nodesByZ) {
    if (node?.comfyClass !== NODE_TYPE || !node.__easyuseAnimaProfileBar || !Array.isArray(node.pos)) {
      continue;
    }
    const localPos = [
      Number(graphPoint[0] || 0) - Number(node.pos[0] || 0),
      Number(graphPoint[1] || 0) - Number(node.pos[1] || 0),
    ];
    const bar = node.__easyuseAnimaProfileBar;
    if (!loraCanvasWidgets.pointInArea(localPos, bar.listArea)) {
      continue;
    }
    const count = profileCount(node);
    const maxOffset = Math.max(0, count - loraCanvasWidgets.profileVisibleRows);
    if (maxOffset <= 0) {
      return false;
    }
    const direction = Number(event.deltaY || 0) > 0 ? 1 : -1;
    const nextOffset = Math.max(0, Math.min(maxOffset, (bar.scrollOffset || 0) + direction));
    if (nextOffset !== bar.scrollOffset) {
      bar.scrollOffset = nextOffset;
      node.setDirtyCanvas?.(true, true);
    }
    event.preventDefault?.();
    event.stopPropagation?.();
    return true;
  }
  return false;
}

function installProfileWheelListener() {
  if (profileWheelListenerInstalled) {
    return;
  }
  profileWheelListenerInstalled = true;
  document.addEventListener("wheel", scrollProfileListFromWheel, { capture: true, passive: false });
}

app.registerExtension({
  name: "EasyUseAnima.LoraPreset",
  init() {
    loraPresetSaveSync.install();
    loadLoraPresetSettings().then(refreshLoraPresetNodes);
    easyuseAnimaWatchLocale(refreshLoraPresetNodes);
    window.addEventListener("easyuse-anima-settings-updated", (event) => {
      applyLoraPresetSettings(event.detail || {});
      refreshLoraPresetNodes();
    });
    document.addEventListener("pointerdown", loraPreviewLifecycle.hidePreview, true);
    installProfileWheelListener();
    loraMenuLifecycle.install();
  },
  setup() {
    loraPresetSaveSync.install();
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    loraPresetNodeRuntime.beforeRegisterNodeDef(nodeType, nodeData);
  },
});
