import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

class FakeClassList {
  constructor() {
    this.values = new Set();
  }

  add(...names) {
    for (const name of names) {
      this.values.add(name);
    }
  }

  contains(name) {
    return this.values.has(name);
  }
}

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.className = "";
    this.classList = new FakeClassList();
    this.textContent = "";
    this.value = "";
    this.title = "";
    this.type = "";
    this.label = "";
    this.disabled = false;
    this.isConnected = true;
    this.children = [];
    this.parentElement = null;
    this.listeners = new Map();
    this.removeCount = 0;
  }

  append(...children) {
    for (const child of children) {
      if (child && typeof child === "object") {
        child.parentElement = this;
      }
      this.children.push(child);
    }
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  async dispatch(type) {
    const results = [];
    for (const listener of [...(this.listeners.get(type) || [])]) {
      results.push(listener({ target: this }));
    }
    await Promise.all(results);
  }

  remove() {
    this.removeCount += 1;
    this.isConnected = false;
  }
}

const runtimeModule = await import(dataModule("../web/js/aio/profile_settings_runtime.js"));
assert.deepEqual(
  Object.keys(runtimeModule),
  ["aioCreateProfileSettingsRuntime"],
  "AiO profile settings runtime must expose only its factory contract",
);

function createFixture() {
  let dependencyCalls = 0;
  let currentDialog = null;
  const dialogs = [];
  const alerts = [];
  const promptCalls = [];
  const confirmCalls = [];
  const resolveCalls = [];
  const prompts = [];
  const confirms = [];
  const trace = [];
  const apiCalls = {
    listProfiles: [],
    loadProfile: [],
    saveProfile: [],
    renameProfile: [],
    deleteProfile: [],
  };
  const apiQueues = {
    listProfiles: [],
    loadProfile: [],
    saveProfile: [],
    renameProfile: [],
    deleteProfile: [],
  };

  function queuedResult(method, args) {
    dependencyCalls += 1;
    apiCalls[method].push(args);
    const value = apiQueues[method].shift();
    if (value instanceof Error) {
      return Promise.reject(value);
    }
    if (value && typeof value.then === "function") {
      return value;
    }
    return Promise.resolve(value);
  }

  const profileApi = {
    listProfiles() {
      return queuedResult("listProfiles", []);
    },
    loadProfile(name) {
      return queuedResult("loadProfile", [name]);
    },
    saveProfile(name, overwrite, settings) {
      return queuedResult("saveProfile", [name, overwrite, clone(settings)]);
    },
    renameProfile(oldName, newName, overwrite) {
      return queuedResult("renameProfile", [oldName, newName, overwrite]);
    },
    deleteProfile(name) {
      return queuedResult("deleteProfile", [name]);
    },
  };

  const fakeDocument = {
    createElement(tagName) {
      dependencyCalls += 1;
      return new FakeElement(tagName);
    },
  };

  function createDialog(title, subtitle) {
    dependencyCalls += 1;
    const dialog = {
      title,
      subtitle,
      backdrop: new FakeElement("div"),
      body: new FakeElement("div"),
      actions: new FakeElement("div"),
      controls: new Map(),
      tooltips: new Map(),
    };
    dialogs.push(dialog);
    currentDialog = dialog;
    return dialog;
  }

  function field(section, label, control, tooltipKey = "") {
    dependencyCalls += 1;
    const wrapper = new FakeElement("div");
    wrapper.append(control);
    section.append(wrapper);
    currentDialog.controls.set(label, control);
    currentDialog.tooltips.set(label, tooltipKey);
    return control;
  }

  function text(key) {
    dependencyCalls += 1;
    return `text:${key}`;
  }

  function format(key, values = {}) {
    dependencyCalls += 1;
    return `format:${key}:${JSON.stringify(values)}`;
  }

  const profileCore = {
    customValue: "custom",
    builtinIds() {
      dependencyCalls += 1;
      return ["normal", "turbo", "optimized"];
    },
    builtinSettings(profileId, defaultSettings) {
      dependencyCalls += 1;
      trace.push("builtin-settings");
      return { ...clone(defaultSettings), builtin_profile: profileId };
    },
    fingerprint(settings) {
      dependencyCalls += 1;
      trace.push("fingerprint");
      return `fingerprint:${JSON.stringify(settings)}`;
    },
    userValue(name) {
      dependencyCalls += 1;
      return `user:${String(name || "")}`;
    },
    userName(value) {
      dependencyCalls += 1;
      const textValue = String(value || "");
      return textValue.startsWith("user:") ? textValue.slice(5) : "";
    },
    findUser(profiles, name) {
      dependencyCalls += 1;
      const expected = String(name || "").toLowerCase();
      return profiles.find((profile) => String(profile?.name || "").toLowerCase() === expected) || null;
    },
    resolveValue(options) {
      dependencyCalls += 1;
      trace.push("resolve");
      resolveCalls.push({
        settings: clone(options.settings),
        defaultSettings: clone(options.defaultSettings),
        selectedValue: options.selectedValue,
        selectedFingerprint: options.selectedFingerprint,
        profiles: clone(options.profiles),
        customValue: options.customValue,
      });
      const selected = String(options.selectedValue || "");
      if (selected.startsWith("builtin:")) {
        return selected;
      }
      if (
        selected.startsWith("user:")
        && options.profiles.some((profile) => (
          `user:${String(profile.name || "")}`.toLowerCase() === selected.toLowerCase()
        ))
      ) {
        return selected;
      }
      return options.customValue;
    },
  };

  const defaultSettings = {
    schema_version: 4,
    sampler: { steps: 20 },
    future_default: { keep: true },
  };
  const settingsCore = {
    defaultSettings,
    mergeDefaults(defaults, current) {
      dependencyCalls += 1;
      trace.push("merge");
      return { ...clone(defaults), ...clone(current) };
    },
    migratePostprocess(settings) {
      dependencyCalls += 1;
      trace.push("migrate");
      return { ...settings, migrated: true };
    },
  };

  const nodeAdapter = {
    getSettings(node) {
      dependencyCalls += 1;
      trace.push("get-settings");
      return node.settings;
    },
    applyVisibleSettings(node, settings) {
      dependencyCalls += 1;
      trace.push("visible");
      node.visibleSettings = clone(settings);
    },
    writeSettings(node, settings, markDirty) {
      dependencyCalls += 1;
      trace.push(`write:${markDirty}`);
      node.settings = clone(settings);
    },
    renderPanel(node) {
      dependencyCalls += 1;
      trace.push("render");
      node.renderCount = (node.renderCount || 0) + 1;
    },
    refreshPanels() {
      dependencyCalls += 1;
      trace.push("refresh-panels");
    },
    markDirty(node) {
      dependencyCalls += 1;
      trace.push("dirty");
      node.dirtyCount = (node.dirtyCount || 0) + 1;
    },
  };

  const dialogsAdapter = {
    prompt(message, defaultValue = "") {
      dependencyCalls += 1;
      trace.push("prompt");
      promptCalls.push({ message, defaultValue });
      return prompts.shift();
    },
    alert(message) {
      dependencyCalls += 1;
      trace.push("alert");
      alerts.push(message);
    },
    confirm(message) {
      dependencyCalls += 1;
      trace.push("confirm");
      confirmCalls.push(message);
      return confirms.shift();
    },
  };

  const runtime = runtimeModule.aioCreateProfileSettingsRuntime({
    document: fakeDocument,
    createDialog,
    field,
    text,
    format,
    dialogs: dialogsAdapter,
    profileApi,
    profileCore,
    settingsCore,
    nodeAdapter,
  });

  return {
    runtime,
    apiCalls,
    apiQueues,
    dialogs,
    alerts,
    prompts,
    confirms,
    promptCalls,
    confirmCalls,
    resolveCalls,
    trace,
    defaultSettings,
    dependencyCalls: () => dependencyCalls,
  };
}

function dialogButtons(dialog) {
  const section = dialog.body.children[0];
  const managerActions = section.children.at(-1);
  return {
    select: dialog.controls.get("Profile"),
    save: managerActions.children[0],
    rename: managerActions.children[1],
    delete: managerActions.children[2],
    cancel: dialog.actions.children[0],
    apply: dialog.actions.children[1],
  };
}

function profileOptions(select) {
  return select.children.map((child) => ({
    tagName: child.tagName,
    label: child.label,
    value: child.value,
    textContent: child.textContent,
    options: child.children.map((option) => ({
      value: option.value,
      textContent: option.textContent,
    })),
  }));
}

function userProfileOptions(dialog) {
  const userGroup = profileOptions(dialogButtons(dialog).select).find(
    (entry) => entry.label === "text:profile.groupUser",
  );
  return userGroup?.options || [];
}

const fixture = createFixture();
assert.deepEqual(Object.keys(fixture.runtime).sort(), [
  "displayLabel",
  "loadProfiles",
  "open",
  "syncValue",
]);
assert.equal(fixture.dependencyCalls(), 0, "factory creation must have no side effects");

const firstList = deferred();
fixture.apiQueues.listProfiles.push(firstList.promise);
const firstLoad = fixture.runtime.loadProfiles();
const concurrentLoad = fixture.runtime.loadProfiles();
const forcedConcurrentLoad = fixture.runtime.loadProfiles({ force: true });
assert.equal(fixture.apiCalls.listProfiles.length, 1, "concurrent loads must share one request");
firstList.resolve({
  profiles: [
    { name: "Portrait", modified: 1 },
    { name: "  " },
    { name: "Landscape", modified: 2 },
  ],
});
assert.deepEqual(await firstLoad, [
  { name: "Portrait", modified: 1 },
  { name: "Landscape", modified: 2 },
]);
assert.deepEqual(await concurrentLoad, await firstLoad);
assert.deepEqual(await forcedConcurrentLoad, await firstLoad);
assert.deepEqual(await fixture.runtime.loadProfiles(), await firstLoad);
assert.equal(fixture.apiCalls.listProfiles.length, 1, "loaded cache must avoid another request");

fixture.apiQueues.listProfiles.push({ profiles: [{ name: "Refreshed" }] });
assert.deepEqual(await fixture.runtime.loadProfiles({ force: true }), [{ name: "Refreshed" }]);
assert.equal(fixture.apiCalls.listProfiles.length, 2);

const retryFixture = createFixture();
const listError = new Error("list failed");
retryFixture.apiQueues.listProfiles.push(listError, { profiles: [{ name: "Recovered" }] });
await assert.rejects(
  retryFixture.runtime.loadProfiles(),
  (error) => error === listError,
  "list failure must propagate",
);
assert.deepEqual(await retryFixture.runtime.loadProfiles(), [{ name: "Recovered" }]);
assert.equal(retryFixture.apiCalls.listProfiles.length, 2, "failed loads must release the retry gate");

fixture.apiQueues.listProfiles.push({
  profiles: [{ name: "Portrait" }, { name: "Landscape" }],
});
await fixture.runtime.loadProfiles({ force: true });

const node = {
  settings: { sampler: { steps: 31 }, current: true },
  __easyuseAnimaGeneratorProfileValue: "custom",
  __easyuseAnimaGeneratorProfileFingerprint: "stale",
};
fixture.runtime.open(node);
let dialog = fixture.dialogs.at(-1);
let buttons = dialogButtons(dialog);
assert.deepEqual(fixture.resolveCalls.at(-1), {
  settings: { sampler: { steps: 31 }, current: true },
  defaultSettings: fixture.defaultSettings,
  selectedValue: "custom",
  selectedFingerprint: "stale",
  profiles: [{ name: "Portrait" }, { name: "Landscape" }],
  customValue: "custom",
});
assert.equal(dialog.title, "text:dialog.profile.title");
assert.equal(dialog.subtitle, "text:dialog.profile.subtitle");
assert.equal(dialog.body.classList.contains("easyuse-anima-aio-one-column"), true);
assert.equal(dialog.tooltips.get("Profile"), "profile.selectTip");
assert.equal(buttons.select.title, "text:profile.selectTip");
assert.deepEqual(profileOptions(buttons.select), [
  {
    tagName: "OPTION",
    label: "",
    value: "custom",
    textContent: "text:profile.custom",
    options: [],
  },
  {
    tagName: "OPTGROUP",
    label: "text:profile.groupBuiltIn",
    value: "",
    textContent: "",
    options: [
      { value: "builtin:normal", textContent: "text:profile.normal" },
      { value: "builtin:turbo", textContent: "text:profile.turbo" },
      { value: "builtin:optimized", textContent: "text:profile.optimized" },
    ],
  },
  {
    tagName: "OPTGROUP",
    label: "text:profile.groupUser",
    value: "",
    textContent: "",
    options: [
      { value: "user:Portrait", textContent: "Portrait" },
      { value: "user:Landscape", textContent: "Landscape" },
    ],
  },
]);
assert.equal(buttons.select.value, "custom");
assert.equal(buttons.save.disabled, false);
assert.equal(buttons.rename.disabled, true);
assert.equal(buttons.delete.disabled, true);
assert.equal(buttons.cancel.disabled, false);
assert.equal(buttons.apply.disabled, true);

buttons.select.value = "user:Portrait";
await buttons.select.dispatch("change");
assert.equal(buttons.rename.disabled, false);
assert.equal(buttons.delete.disabled, false);
assert.equal(buttons.apply.disabled, false);
buttons.select.value = "builtin:normal";
await buttons.select.dispatch("change");
assert.equal(buttons.rename.disabled, true);
assert.equal(buttons.delete.disabled, true);
assert.equal(buttons.apply.disabled, false);

const dialogsBeforeCancel = fixture.dialogs.length;
await buttons.cancel.dispatch("click");
assert.equal(dialog.backdrop.isConnected, false);
assert.equal(fixture.dialogs.length, dialogsBeforeCancel, "Cancel must not reopen the dialog");

fixture.runtime.open(node);
dialog = fixture.dialogs.at(-1);
buttons = dialogButtons(dialog);
buttons.select.value = "builtin:normal";
fixture.trace.length = 0;
await buttons.apply.dispatch("click");
assert.deepEqual(fixture.trace, [
  "builtin-settings",
  "merge",
  "migrate",
  "visible",
  "write:true",
  "get-settings",
  "fingerprint",
  "render",
  "dirty",
]);
assert.equal(dialog.backdrop.isConnected, false);
assert.equal(node.__easyuseAnimaGeneratorProfileValue, "builtin:normal");
assert.equal(node.settings.builtin_profile, "normal");
assert.equal(node.settings.migrated, true);
assert.equal(node.renderCount, 1);
assert.equal(node.dirtyCount, 1);
assert.equal(fixture.apiCalls.loadProfile.length, 0, "built-in apply must remain local");

fixture.runtime.open(node);
dialog = fixture.dialogs.at(-1);
buttons = dialogButtons(dialog);
buttons.select.value = "user:Portrait";
fixture.apiQueues.loadProfile.push({
  profile: { name: "Portrait Canonical", settings: { sampler: { steps: 44 }, user: true } },
});
await buttons.apply.dispatch("click");
assert.deepEqual(fixture.apiCalls.loadProfile.at(-1), ["Portrait"]);
assert.equal(node.__easyuseAnimaGeneratorProfileValue, "user:Portrait Canonical");
assert.equal(node.settings.user, true);
assert.equal(dialog.backdrop.isConnected, false);

node.__easyuseAnimaGeneratorProfileValue = "user:Portrait";
fixture.runtime.open(node);
dialog = fixture.dialogs.at(-1);
buttons = dialogButtons(dialog);
buttons.select.value = "user:Portrait";
fixture.apiQueues.loadProfile.push({ profile: null });
const dialogsBeforeLoadError = fixture.dialogs.length;
await buttons.apply.dispatch("click");
assert.equal(dialog.backdrop.isConnected, true, "failed apply must keep the dialog open");
assert.equal(fixture.dialogs.length, dialogsBeforeLoadError);
assert.match(fixture.alerts.at(-1), /profile\.requestFailed/);
assert.match(fixture.alerts.at(-1), /Profile settings are missing/);
assert.equal(buttons.save.disabled, false);
assert.equal(buttons.cancel.disabled, false);
assert.equal(buttons.apply.disabled, false);

const saveNode = {
  settings: { sampler: { steps: 55 }, save_snapshot: true },
  __easyuseAnimaGeneratorProfileValue: "user:Portrait",
  __easyuseAnimaGeneratorProfileFingerprint: "old-fingerprint",
};
fixture.runtime.open(saveNode);
dialog = fixture.dialogs.at(-1);
buttons = dialogButtons(dialog);
fixture.prompts.push(" Landscape ");
fixture.confirms.push(true);
fixture.apiQueues.saveProfile.push({ profile: { name: "Landscape" } });
fixture.apiQueues.listProfiles.push({ profiles: [{ name: "Landscape" }, { name: "Portrait" }] });
const dialogsBeforeSave = fixture.dialogs.length;
const listCallsBeforeSave = fixture.apiCalls.listProfiles.length;
fixture.trace.length = 0;
await buttons.save.dispatch("click");
assert.deepEqual(fixture.promptCalls.at(-1), {
  message: "text:profile.savePrompt",
  defaultValue: "Portrait",
});
assert.match(fixture.confirmCalls.at(-1), /Landscape/);
assert.deepEqual(fixture.apiCalls.saveProfile.at(-1), [
  "Landscape",
  true,
  { sampler: { steps: 55 }, save_snapshot: true },
]);
assert.equal(saveNode.__easyuseAnimaGeneratorProfileValue, "user:Landscape");
assert.match(saveNode.__easyuseAnimaGeneratorProfileFingerprint, /^fingerprint:/);
assert.equal(fixture.apiCalls.listProfiles.length, listCallsBeforeSave + 1);
assert.equal(fixture.trace.includes("refresh-panels"), true);
assert.equal(dialog.backdrop.isConnected, false);
assert.equal(fixture.dialogs.length, dialogsBeforeSave + 1, "successful save must reopen");
const reopenedAfterSave = fixture.dialogs.at(-1);
assert.equal(reopenedAfterSave.backdrop.isConnected, true);
assert.deepEqual(userProfileOptions(reopenedAfterSave), [
  { value: "user:Landscape", textContent: "Landscape" },
  { value: "user:Portrait", textContent: "Portrait" },
]);

dialog = reopenedAfterSave;
buttons = dialogButtons(dialog);
fixture.prompts.push(null);
const saveCallsBeforePromptCancel = fixture.apiCalls.saveProfile.length;
const dialogsBeforePromptCancel = fixture.dialogs.length;
await buttons.save.dispatch("click");
assert.equal(fixture.apiCalls.saveProfile.length, saveCallsBeforePromptCancel);
assert.equal(dialog.backdrop.isConnected, false);
assert.equal(
  fixture.dialogs.length,
  dialogsBeforePromptCancel + 1,
  "prompt cancel is currently treated as a successful CRUD callback and reopens",
);

dialog = fixture.dialogs.at(-1);
buttons = dialogButtons(dialog);
fixture.prompts.push("   ");
const dialogsBeforeBlankName = fixture.dialogs.length;
await buttons.save.dispatch("click");
assert.equal(fixture.alerts.at(-1), "text:profile.nameRequired");
assert.equal(dialog.backdrop.isConnected, false);
assert.equal(fixture.dialogs.length, dialogsBeforeBlankName + 1);

dialog = fixture.dialogs.at(-1);
buttons = dialogButtons(dialog);
buttons.select.value = "user:Landscape";
await buttons.select.dispatch("change");
fixture.prompts.push("Portrait");
fixture.confirms.push(false);
const renameCallsBeforeDecline = fixture.apiCalls.renameProfile.length;
const dialogsBeforeRenameDecline = fixture.dialogs.length;
await buttons.rename.dispatch("click");
assert.equal(fixture.apiCalls.renameProfile.length, renameCallsBeforeDecline);
assert.equal(dialog.backdrop.isConnected, false);
assert.equal(fixture.dialogs.length, dialogsBeforeRenameDecline + 1);

dialog = fixture.dialogs.at(-1);
buttons = dialogButtons(dialog);
buttons.select.value = "user:Landscape";
await buttons.select.dispatch("change");
saveNode.__easyuseAnimaGeneratorProfileValue = "user:Landscape";
fixture.prompts.push("Cinematic");
fixture.apiQueues.renameProfile.push({ profile: { name: "Cinematic" } });
fixture.apiQueues.listProfiles.push({ profiles: [{ name: "Portrait" }, { name: "Cinematic" }] });
const dialogsBeforeRename = fixture.dialogs.length;
const listCallsBeforeRename = fixture.apiCalls.listProfiles.length;
fixture.trace.length = 0;
await buttons.rename.dispatch("click");
assert.ok(
  fixture.trace.indexOf("resolve") < fixture.trace.indexOf("prompt"),
  "rename must sync the current selection before prompting",
);
assert.deepEqual(fixture.apiCalls.renameProfile.at(-1), ["Landscape", "Cinematic", false]);
assert.equal(saveNode.__easyuseAnimaGeneratorProfileValue, "user:Cinematic");
assert.equal(fixture.apiCalls.listProfiles.length, listCallsBeforeRename + 1);
assert.equal(fixture.trace.includes("refresh-panels"), true);
assert.equal(dialog.backdrop.isConnected, false);
assert.equal(fixture.dialogs.length, dialogsBeforeRename + 1);
const reopenedAfterRename = fixture.dialogs.at(-1);
assert.equal(reopenedAfterRename.backdrop.isConnected, true);
assert.deepEqual(userProfileOptions(reopenedAfterRename), [
  { value: "user:Portrait", textContent: "Portrait" },
  { value: "user:Cinematic", textContent: "Cinematic" },
]);

dialog = reopenedAfterRename;
buttons = dialogButtons(dialog);
buttons.select.value = "user:Cinematic";
await buttons.select.dispatch("change");
fixture.confirms.push(false);
const deleteCallsBeforeDecline = fixture.apiCalls.deleteProfile.length;
const dialogsBeforeDeleteDecline = fixture.dialogs.length;
await buttons.delete.dispatch("click");
assert.equal(fixture.apiCalls.deleteProfile.length, deleteCallsBeforeDecline);
assert.equal(dialog.backdrop.isConnected, false);
assert.equal(fixture.dialogs.length, dialogsBeforeDeleteDecline + 1);

dialog = fixture.dialogs.at(-1);
buttons = dialogButtons(dialog);
buttons.select.value = "user:Cinematic";
await buttons.select.dispatch("change");
saveNode.__easyuseAnimaGeneratorProfileValue = "user:Cinematic";
saveNode.__easyuseAnimaGeneratorProfileFingerprint = "delete-me";
fixture.confirms.push(true);
fixture.apiQueues.deleteProfile.push({ profile: { name: "Cinematic" } });
fixture.apiQueues.listProfiles.push({ profiles: [{ name: "Portrait" }] });
const dialogsBeforeDelete = fixture.dialogs.length;
const listCallsBeforeDelete = fixture.apiCalls.listProfiles.length;
fixture.trace.length = 0;
await buttons.delete.dispatch("click");
assert.deepEqual(fixture.apiCalls.deleteProfile.at(-1), ["Cinematic"]);
assert.equal(saveNode.__easyuseAnimaGeneratorProfileValue, "custom");
assert.equal(Object.hasOwn(saveNode, "__easyuseAnimaGeneratorProfileFingerprint"), false);
assert.equal(fixture.apiCalls.listProfiles.length, listCallsBeforeDelete + 1);
assert.equal(fixture.trace.includes("refresh-panels"), true);
assert.equal(dialog.backdrop.isConnected, false);
assert.equal(fixture.dialogs.length, dialogsBeforeDelete + 1);
const reopenedAfterDelete = fixture.dialogs.at(-1);
assert.equal(reopenedAfterDelete.backdrop.isConnected, true);
assert.deepEqual(userProfileOptions(reopenedAfterDelete), [
  { value: "user:Portrait", textContent: "Portrait" },
]);

dialog = reopenedAfterDelete;
buttons = dialogButtons(dialog);
buttons.select.value = "user:Portrait";
await buttons.select.dispatch("change");
assert.equal(buttons.rename.disabled, false);
assert.equal(buttons.delete.disabled, false);
assert.equal(buttons.apply.disabled, false);
fixture.prompts.push("Busy Save", "must-not-run");
const saveDeferred = deferred();
fixture.apiQueues.saveProfile.push(saveDeferred.promise);
fixture.apiQueues.listProfiles.push({ profiles: [{ name: "Portrait" }, { name: "Busy Save" }] });
const saveCallCountBeforeBusy = fixture.apiCalls.saveProfile.length;
const promptCallCountBeforeBusy = fixture.promptCalls.length;
const pendingSave = buttons.save.dispatch("click");
await Promise.resolve();
assert.equal(buttons.save.disabled, true);
assert.equal(buttons.cancel.disabled, true);
assert.equal(buttons.rename.disabled, true);
assert.equal(buttons.delete.disabled, true);
assert.equal(buttons.apply.disabled, true);
const ignoredSave = buttons.save.dispatch("click");
await Promise.resolve();
assert.equal(fixture.apiCalls.saveProfile.length, saveCallCountBeforeBusy + 1);
assert.equal(fixture.promptCalls.length, promptCallCountBeforeBusy + 1);
dialog.backdrop.remove();
saveDeferred.resolve({ profile: { name: "Busy Save" } });
await Promise.all([pendingSave, ignoredSave]);
assert.equal(
  fixture.dialogs.at(-1) === dialog,
  false,
  "successful CRUD must reopen even if the original backdrop closed while busy",
);
const reopenedAfterBusySave = fixture.dialogs.at(-1);
assert.equal(reopenedAfterBusySave.backdrop.isConnected, true);
assert.deepEqual(userProfileOptions(reopenedAfterBusySave), [
  { value: "user:Portrait", textContent: "Portrait" },
  { value: "user:Busy Save", textContent: "Busy Save" },
]);
assert.equal(fixture.prompts.shift(), "must-not-run");

dialog = reopenedAfterBusySave;
buttons = dialogButtons(dialog);
fixture.prompts.push("Failure");
const saveError = new Error("save failed");
fixture.apiQueues.saveProfile.push(saveError);
const dialogsBeforeSaveError = fixture.dialogs.length;
await buttons.save.dispatch("click");
assert.equal(dialog.backdrop.isConnected, true, "failed CRUD must retain its dialog");
assert.equal(fixture.dialogs.length, dialogsBeforeSaveError);
assert.match(fixture.alerts.at(-1), /save failed/);
assert.equal(buttons.save.disabled, false);
assert.equal(buttons.cancel.disabled, false);

fixture.prompts.push("Refresh Failure");
fixture.apiQueues.saveProfile.push({ profile: { name: "Refresh Failure" } });
const refreshError = new Error("refresh failed");
fixture.apiQueues.listProfiles.push(refreshError);
const dialogsBeforeRefreshError = fixture.dialogs.length;
const listCallsBeforeRefreshError = fixture.apiCalls.listProfiles.length;
await buttons.save.dispatch("click");
assert.deepEqual(fixture.apiCalls.saveProfile.at(-1), [
  "Refresh Failure",
  false,
  { sampler: { steps: 55 }, save_snapshot: true },
]);
assert.equal(fixture.apiCalls.listProfiles.length, listCallsBeforeRefreshError + 1);
assert.equal(dialog.backdrop.isConnected, true, "refresh failure must retain its dialog");
assert.equal(fixture.dialogs.length, dialogsBeforeRefreshError);
assert.match(fixture.alerts.at(-1), /refresh failed/);
assert.equal(buttons.save.disabled, false);
assert.equal(buttons.cancel.disabled, false);
fixture.apiQueues.listProfiles.push({ profiles: [{ name: "Recovered After Refresh" }] });
assert.deepEqual(await fixture.runtime.loadProfiles({ force: true }), [
  { name: "Recovered After Refresh" },
]);

const preserveFixture = createFixture();
preserveFixture.apiQueues.listProfiles.push({
  profiles: [{ name: "Current" }, { name: "Managed" }],
});
await preserveFixture.runtime.loadProfiles();
const preserveNode = {
  settings: { sampler: { steps: 42 } },
  __easyuseAnimaGeneratorProfileValue: "user:Current",
  __easyuseAnimaGeneratorProfileFingerprint: "keep-fingerprint",
};
preserveFixture.runtime.open(preserveNode);
let preserveDialog = preserveFixture.dialogs.at(-1);
let preserveButtons = dialogButtons(preserveDialog);
preserveButtons.select.value = "user:Managed";
await preserveButtons.select.dispatch("change");
preserveFixture.prompts.push("Managed Renamed");
preserveFixture.apiQueues.renameProfile.push({ profile: { name: "Managed Renamed" } });
preserveFixture.apiQueues.listProfiles.push({
  profiles: [{ name: "Current" }, { name: "Managed Renamed" }],
});
await preserveButtons.rename.dispatch("click");
assert.equal(preserveNode.__easyuseAnimaGeneratorProfileValue, "user:Current");
assert.equal(preserveNode.__easyuseAnimaGeneratorProfileFingerprint, "keep-fingerprint");

preserveDialog = preserveFixture.dialogs.at(-1);
preserveButtons = dialogButtons(preserveDialog);
preserveButtons.select.value = "user:Managed Renamed";
await preserveButtons.select.dispatch("change");
preserveFixture.confirms.push(true);
preserveFixture.apiQueues.deleteProfile.push({ profile: { name: "Managed Renamed" } });
preserveFixture.apiQueues.listProfiles.push({ profiles: [{ name: "Current" }] });
await preserveButtons.delete.dispatch("click");
assert.equal(preserveNode.__easyuseAnimaGeneratorProfileValue, "user:Current");
assert.equal(preserveNode.__easyuseAnimaGeneratorProfileFingerprint, "keep-fingerprint");

assert.equal(fixture.runtime.displayLabel("custom"), "text:profile.custom");
assert.equal(fixture.runtime.displayLabel("user:Portrait"), "Portrait");
assert.equal(fixture.runtime.displayLabel("builtin:turbo"), "text:profile.turbo");
assert.equal(fixture.runtime.displayLabel("builtin:unknown"), "text:profile.custom");

const transientNode = {
  settings: { keep: true },
  __easyuseAnimaGeneratorProfileValue: "user:Missing",
  __easyuseAnimaGeneratorProfileFingerprint: "remove-me",
};
assert.equal(fixture.runtime.syncValue(transientNode), "custom");
assert.equal(transientNode.__easyuseAnimaGeneratorProfileValue, "custom");
assert.equal(Object.hasOwn(transientNode, "__easyuseAnimaGeneratorProfileFingerprint"), false);

console.log("AiO profile settings runtime smoke passed.");
