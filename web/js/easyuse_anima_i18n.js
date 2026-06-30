import { app } from "../../../scripts/app.js";

let localeWatchInstalled = false;
let lastLanguage = null;
const localeListeners = new Set();

export function easyuseAnimaReadSettingValue(id) {
  try {
    if (typeof app?.ui?.settings?.getSettingValue === "function") {
      const value = app.ui.settings.getSettingValue(id);
      if (value && typeof value === "object" && "value" in value) {
        return value.value;
      }
      if (value !== undefined) {
        return value;
      }
    }
  } catch {}
  return undefined;
}

export function easyuseAnimaLanguage() {
  const value = String(easyuseAnimaReadSettingValue("Comfy.Locale") || "").toLowerCase();
  if (value === "ko" || value.startsWith("ko-") || value.includes("korean") || value.includes("한국어")) {
    return "ko";
  }
  if (value === "ja" || value.startsWith("ja-") || value === "jp" || value.includes("japanese") || value.includes("日本語")) {
    return "ja";
  }
  if (
    value === "zh" ||
    value.startsWith("zh-") ||
    value === "cn" ||
    value.includes("chinese") ||
    value.includes("中文") ||
    value.includes("简体") ||
    value.includes("簡體") ||
    value.includes("繁体") ||
    value.includes("繁體")
  ) {
    return "zh";
  }
  return "en";
}

export function easyuseAnimaIsKorean() {
  return easyuseAnimaLanguage() === "ko";
}

export function easyuseAnimaText(map, key) {
  const language = easyuseAnimaLanguage();
  return map?.[language]?.[key] || map?.en?.[key] || key;
}

export function easyuseAnimaLocaleText(item, fallback = "") {
  const language = easyuseAnimaLanguage();
  return item?.[language] || item?.en || fallback;
}

function notifyLocaleListeners(language) {
  for (const listener of [...localeListeners]) {
    try {
      listener(language);
    } catch (error) {
      console.warn("[EasyUseAnima] locale listener failed", error);
    }
  }
}

function checkLocaleChange() {
  const language = easyuseAnimaLanguage();
  if (language === lastLanguage) {
    return;
  }
  lastLanguage = language;
  notifyLocaleListeners(language);
}

function patchComfyLocaleSetting() {
  const setting = app?.ui?.settings?.settingsLookup?.["Comfy.Locale"];
  if (!setting || setting.__easyuseAnimaLocalePatched || typeof setting.onChange !== "function") {
    return;
  }
  const originalOnChange = setting.onChange;
  setting.onChange = function () {
    const result = originalOnChange.apply(this, arguments);
    setTimeout(checkLocaleChange, 0);
    return result;
  };
  setting.__easyuseAnimaLocalePatched = true;
}

function installLocaleWatch() {
  if (localeWatchInstalled) {
    return;
  }
  localeWatchInstalled = true;
  lastLanguage = easyuseAnimaLanguage();
  patchComfyLocaleSetting();
  window.addEventListener("focus", checkLocaleChange);
  document.addEventListener("visibilitychange", checkLocaleChange);
  window.addEventListener("easyuse-anima-settings-updated", checkLocaleChange);
}

export function easyuseAnimaWatchLocale(callback) {
  if (typeof callback !== "function") {
    return () => {};
  }
  installLocaleWatch();
  localeListeners.add(callback);
  return () => localeListeners.delete(callback);
}
