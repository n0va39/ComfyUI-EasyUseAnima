import {
  MAX_PROFILES,
  emptyProfile,
  isMeaningfulProfile,
  normalizeLoraEntry,
  normalizeProfileDataValue,
  profileContent,
  profileKey,
  profileSavedName,
  profileSnapshot,
  withSavedMeta,
  wrapProfileIndex,
} from "./profile_data.js";

const PROFILE_ALREADY_EXISTS_MESSAGE = "Profile already exists";

/**
 * Owns profile and LoRA-row mutations while leaving canvas rendering and node
 * lifecycle installation with their existing owners.
 */
export function createLoraPresetProfileMutations({
  findWidget,
  widgetValue,
  setWidgetValue,
  lorasWidgetValue,
  setLorasWidgetValue,
  getCanvasWidgets,
  text,
  formatText,
  apiClient,
  errorMessage = (error) => error?.message || String(error),
  host = globalThis.window,
}) {
  function renderProfileBar(node) {
    getCanvasWidgets()?.renderProfileBar(node);
  }

  function renderLoraWidgets(node) {
    getCanvasWidgets()?.renderLoraWidgets(node);
  }

  function parseProfileData(widget) {
    return normalizeProfileDataValue(widgetValue(widget, "{}"));
  }

  function writeProfileData(widget, data) {
    setWidgetValue(widget, JSON.stringify(data));
  }

  function profileCount(node) {
    return Math.max(1, Math.min(MAX_PROFILES, Number.parseInt(widgetValue(findWidget(node, "profile_count"), 4), 10) || 4));
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
    const canvasWidgets = getCanvasWidgets();
    const visibleRows = canvasWidgets?.profileVisibleRows || 1;
    const count = profileCount(node);
    const maxOffset = Math.max(0, count - visibleRows);
    const target = wrapProfileIndex(index, count);
    if (target <= (bar.scrollOffset || 0)) {
      bar.scrollOffset = Math.max(0, target - 1);
    } else if (target > (bar.scrollOffset || 0) + visibleRows) {
      bar.scrollOffset = Math.max(0, Math.min(maxOffset, target - visibleRows));
    }
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
    if (count <= 1 || !host.confirm?.(formatText("profile.deleteConfirm", { index }))) {
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

  function selectedProfilePayload(node) {
    saveCurrentProfile(node);
    const index = activeProfileIndex(node);
    const data = parseProfileData(findWidget(node, "profile_data"));
    return {
      profile_count: 1,
      profile_index: 1,
      profile_data: { "1": profileContent(data[profileKey(index)]) },
    };
  }

  function profileSaveStatus(node, index) {
    const profile = parseProfileData(findWidget(node, "profile_data"))[profileKey(index)] || {};
    const savedName = profileSavedName(profile);
    if (!savedName) {
      return { state: "unsaved", labelKey: "profile.unsaved", savedName: "" };
    }
    const dirty = String(profile.saved_snapshot || "") !== profileSnapshot(profile);
    return { state: dirty ? "changed" : "saved", labelKey: dirty ? "profile.changed" : "profile.saved", savedName };
  }

  function markSelectedProfileSaved(node, name) {
    const savedName = String(name || "").trim();
    if (!savedName) {
      return;
    }
    saveCurrentProfile(node);
    const dataWidget = findWidget(node, "profile_data");
    const data = parseProfileData(dataWidget);
    const key = profileKey(activeProfileIndex(node));
    const content = profileContent(data[key]);
    data[key] = { ...content, saved_name: savedName, saved_snapshot: profileSnapshot(content) };
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
        incomingProfiles.push({ sourceIndex, content: profileContent(sourceProfile) });
      }
    }
    if (!incomingProfiles.length) {
      host.alert?.(text("profile.noNonEmpty"));
      return;
    }
    const currentCount = profileCount(node);
    const available = MAX_PROFILES - currentCount;
    if (available <= 0) {
      host.alert?.(formatText("profile.maxReached", { max: MAX_PROFILES }));
      return;
    }
    const appendCount = Math.min(incomingProfiles.length, available);
    const targetStart = currentCount + 1;
    const data = parseProfileData(findWidget(node, "profile_data"));
    for (let offset = 0; offset < appendCount; offset += 1) {
      const targetIndex = targetStart + offset;
      const content = incomingProfiles[offset].content;
      data[profileKey(targetIndex)] = savedName
        ? { ...content, saved_name: savedName, saved_snapshot: profileSnapshot(content) }
        : content;
    }
    if (appendCount < incomingProfiles.length) {
      host.alert?.(formatText("profile.partialLoad", { count: appendCount, max: MAX_PROFILES }));
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
    const name = host.prompt?.(text("profile.savePrompt"));
    if (name == null) {
      return;
    }
    const trimmedName = name.trim();
    if (!trimmedName) {
      host.alert?.(text("profile.nameRequired"));
      return;
    }
    const payload = selectedProfilePayload(node);
    try {
      let data;
      try {
        data = await apiClient.saveProfile(trimmedName, payload, false);
      } catch (error) {
        if (errorMessage(error) !== PROFILE_ALREADY_EXISTS_MESSAGE) {
          throw error;
        }
        const confirmed = host.confirm?.(
          formatText("profile.overwriteConfirm", { name: trimmedName }),
        );
        if (!confirmed) {
          return;
        }
        data = await apiClient.saveProfile(trimmedName, payload, true);
      }
      markSelectedProfileSaved(node, data?.profile?.name || trimmedName);
      renderProfileBar(node);
      node.setDirtyCanvas?.(true, true);
    } catch (error) {
      host.alert?.(formatText("profile.saveFailed", { message: errorMessage(error) }));
    }
  }

  async function loadProfileSet(node, name) {
    try {
      const data = await apiClient.loadProfile(name);
      appendProfilePayload(node, data.profile);
    } catch (error) {
      host.alert?.(formatText("profile.loadFailed", { message: errorMessage(error) }));
    }
  }

  function fullProfilePayload(node) {
    saveCurrentProfile(node);
    return {
      profile_count: profileCount(node),
      profile_index: activeProfileIndex(node),
      profile_data: parseProfileData(findWidget(node, "profile_data")),
    };
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
    mutateLoras(node, (loras) => loras.splice(index, 1));
  }

  function moveLoraEntry(node, index, direction) {
    mutateLoras(node, (loras) => {
      const from = Number(index);
      const to = from + Number(direction || 0);
      if (!Number.isInteger(from) || !Number.isInteger(to) || !loras[from] || to < 0 || to >= loras.length) {
        return;
      }
      const [entry] = loras.splice(from, 1);
      loras.splice(to, 0, entry);
    });
  }

  return {
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
  };
}
