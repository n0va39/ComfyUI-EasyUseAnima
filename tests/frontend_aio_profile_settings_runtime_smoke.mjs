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

function profileExistsError(message = "Profile already exists") {
  const error = new Error(message);
  error.code = "profile_exists";
  return error;
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
  const confirmTypes = [];
  const alertCalls = [];
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
    saveProfile(name, overwrite, settings, profile) {
      return queuedResult("saveProfile", [name, overwrite, clone(settings), clone(profile)]);
    },
    renameProfile(oldName, newName, overwrite, profile, targetProfile) {
      return queuedResult("renameProfile", [
        oldName,
        newName,
        overwrite,
        clone(profile),
        clone(targetProfile),
      ]);
    },
    deleteProfile(name, profile) {
      return queuedResult("deleteProfile", [name, clone(profile)]);
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
    async prompt(message, defaultValue = "") {
      dependencyCalls += 1;
      trace.push("prompt");
      promptCalls.push({ message, defaultValue });
      return prompts.shift();
    },
    async alert(message, severity = "warn") {
      dependencyCalls += 1;
      trace.push("alert");
      alerts.push(message);
      alertCalls.push({ message, severity });
    },
    async confirm(message, type = "default") {
      dependencyCalls += 1;
      trace.push("confirm");
      confirmCalls.push(message);
      confirmTypes.push(type);
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
    confirmTypes,
    alertCalls,
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
  profile: {
    name: "Portrait Canonical",
    settings: {
      sampler: {
        backend: "spectrum_spd_speed",
        steps: 44,
        spd: { scale: 0.7, sigma_max: 1.2 },
      },
      user: true,
    },
  },
});
await buttons.apply.dispatch("click");
assert.deepEqual(fixture.apiCalls.loadProfile.at(-1), ["Portrait"]);
assert.equal(node.__easyuseAnimaGeneratorProfileValue, "user:Portrait Canonical");
assert.equal(node.settings.user, true);
assert.deepEqual(node.settings.sampler, {
  backend: "spectrum_spd_speed",
  steps: 44,
  spd: { scale: 0.7, sigma_max: 1.2 },
});
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
assert.equal(fixture.alertCalls.at(-1).severity, "error");
assert.equal(buttons.save.disabled, false);
assert.equal(buttons.cancel.disabled, false);
assert.equal(buttons.apply.disabled, false);

const saveNode = {
  settings: {
    sampler: {
      backend: "spectrum_spd_speed",
      steps: 55,
      spd: { scale: 0.8, sigma_max: 1.4 },
    },
    save_snapshot: true,
  },
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
  {
    sampler: {
      backend: "spectrum_spd_speed",
      steps: 55,
      spd: { scale: 0.8, sigma_max: 1.4 },
    },
    save_snapshot: true,
  },
  { name: "Landscape" },
]);
assert.equal(saveNode.__easyuseAnimaGeneratorProfileValue, "user:Landscape");
assert.match(saveNode.__easyuseAnimaGeneratorProfileFingerprint, /^fingerprint:/);
assert.equal(fixture.apiCalls.listProfiles.length, listCallsBeforeSave + 1);
assert.equal(fixture.trace.includes("refresh-panels"), true);
assert.equal(fixture.confirmTypes.at(-1), "overwrite");
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
assert.equal(fixture.alertCalls.at(-1).severity, "warn");
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
assert.deepEqual(fixture.apiCalls.renameProfile.at(-1), [
  "Landscape",
  "Cinematic",
  false,
  { name: "Landscape" },
  null,
]);
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
assert.equal(fixture.confirmTypes.at(-1), "delete");
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
assert.deepEqual(fixture.apiCalls.deleteProfile.at(-1), ["Cinematic", { name: "Cinematic" }]);
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
  {
    sampler: {
      backend: "spectrum_spd_speed",
      steps: 55,
      spd: { scale: 0.8, sigma_max: 1.4 },
    },
    save_snapshot: true,
  },
  null,
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

const tokenFixture = createFixture();
const sourceV1 = {
  name: "Source",
  profile_id: "11111111-1111-4111-8111-111111111111",
  revision: 1,
};
const targetV4 = {
  name: "Target",
  profile_id: "22222222-2222-4222-8222-222222222222",
  revision: 4,
};
tokenFixture.apiQueues.listProfiles.push({ profiles: [sourceV1, targetV4] });
await tokenFixture.runtime.loadProfiles();
const tokenNode = {
  settings: { sampler: { steps: 61 } },
  __easyuseAnimaGeneratorProfileValue: "user:Source",
  __easyuseAnimaGeneratorProfileFingerprint: "source-fingerprint",
};
tokenFixture.runtime.open(tokenNode);
let tokenDialog = tokenFixture.dialogs.at(-1);
let tokenButtons = dialogButtons(tokenDialog);
tokenButtons.select.value = "user:Source";

const targetV5 = { ...targetV4, revision: 5 };
tokenFixture.prompts.push("Target");
tokenFixture.confirms.push(true);
tokenFixture.apiQueues.saveProfile.push({ profile: targetV5 });
tokenFixture.apiQueues.listProfiles.push(new Error("save refresh failed"));
await tokenButtons.save.dispatch("click");
assert.deepEqual(tokenFixture.apiCalls.saveProfile.at(-1), [
  "Target",
  true,
  { sampler: { steps: 61 } },
  targetV4,
]);
assert.deepEqual(
  (await tokenFixture.runtime.loadProfiles()).find((profile) => profile.name === "Target"),
  targetV5,
  "save response metadata must survive a failed list refresh",
);

const targetV6 = { ...targetV4, revision: 6 };
tokenFixture.prompts.push("Target");
tokenFixture.confirms.push(true);
tokenFixture.apiQueues.saveProfile.push({ profile: targetV6 });
tokenFixture.apiQueues.listProfiles.push(new Error("second save refresh failed"));
await tokenButtons.save.dispatch("click");
assert.deepEqual(tokenFixture.apiCalls.saveProfile.at(-1).at(-1), targetV5);

tokenButtons.select.value = "user:Source";
tokenFixture.prompts.push("Target");
tokenFixture.confirms.push(true);
const renamedTarget = { ...sourceV1, name: "Target" };
tokenFixture.apiQueues.renameProfile.push({ profile: renamedTarget });
tokenFixture.apiQueues.listProfiles.push(new Error("rename refresh failed"));
await tokenButtons.rename.dispatch("click");
assert.deepEqual(tokenFixture.apiCalls.renameProfile.at(-1), [
  "Source",
  "Target",
  true,
  sourceV1,
  targetV6,
]);

tokenButtons.select.value = "user:Target";
tokenFixture.confirms.push(true);
tokenFixture.apiQueues.deleteProfile.push({ profile: renamedTarget });
tokenFixture.apiQueues.listProfiles.push(new Error("delete refresh failed"));
await tokenButtons.delete.dispatch("click");
assert.deepEqual(tokenFixture.apiCalls.deleteProfile.at(-1), ["Target", renamedTarget]);
assert.equal(
  (await tokenFixture.runtime.loadProfiles()).some((profile) => profile.name === "Target"),
  false,
  "delete success must remove cached metadata even when refresh fails",
);

const caseFixture = createFixture();
const caseProfile = {
  name: "Case Name",
  profile_id: "33333333-3333-4333-8333-333333333333",
  revision: 2,
};
caseFixture.apiQueues.listProfiles.push({ profiles: [caseProfile] });
await caseFixture.runtime.loadProfiles();
const caseNode = {
  settings: { keep: true },
  __easyuseAnimaGeneratorProfileValue: "user:Case Name",
  __easyuseAnimaGeneratorProfileFingerprint: "case-fingerprint",
};
caseFixture.runtime.open(caseNode);
const caseButtons = dialogButtons(caseFixture.dialogs.at(-1));
caseButtons.select.value = "user:Case Name";
caseFixture.prompts.push("case name");
caseFixture.apiQueues.renameProfile.push({
  profile: { ...caseProfile, name: "case name" },
});
caseFixture.apiQueues.listProfiles.push({
  profiles: [{ ...caseProfile, name: "case name" }],
});
await caseButtons.rename.dispatch("click");
assert.deepEqual(caseFixture.apiCalls.renameProfile.at(-1), [
  "Case Name",
  "case name",
  false,
  caseProfile,
  null,
]);
assert.deepEqual(caseFixture.confirmCalls, [], "case-only rename must not confirm overwrite");

const sanitizedSaveFixture = createFixture();
sanitizedSaveFixture.apiQueues.listProfiles.push({ profiles: [] });
await sanitizedSaveFixture.runtime.loadProfiles();
const sanitizedSaveNode = {
  settings: { sampler: { steps: 71 }, sanitized: true },
  __easyuseAnimaGeneratorProfileValue: "custom",
};
sanitizedSaveFixture.runtime.open(sanitizedSaveNode);
const sanitizedSaveButtons = dialogButtons(sanitizedSaveFixture.dialogs.at(-1));
const sanitizedTarget = {
  name: "foo_bar",
  profile_id: "44444444-4444-4444-8444-444444444444",
  revision: 7,
};
const sanitizedSaved = { ...sanitizedTarget, revision: 8 };
sanitizedSaveFixture.prompts.push("foo?bar");
sanitizedSaveFixture.apiQueues.saveProfile.push(profileExistsError("localized conflict"));
sanitizedSaveFixture.apiQueues.loadProfile.push({ profile: sanitizedTarget });
sanitizedSaveFixture.confirms.push(true);
sanitizedSaveFixture.apiQueues.saveProfile.push({ profile: sanitizedSaved });
sanitizedSaveFixture.apiQueues.listProfiles.push(new Error("sanitized refresh failed"));
await sanitizedSaveButtons.save.dispatch("click");
assert.deepEqual(sanitizedSaveFixture.apiCalls.saveProfile, [
  ["foo?bar", false, { sampler: { steps: 71 }, sanitized: true }, null],
  ["foo?bar", true, { sampler: { steps: 71 }, sanitized: true }, sanitizedTarget],
]);
assert.deepEqual(sanitizedSaveFixture.apiCalls.loadProfile, [["foo?bar"]]);
assert.match(sanitizedSaveFixture.confirmCalls.at(-1), /foo_bar/);
assert.deepEqual(
  (await sanitizedSaveFixture.runtime.loadProfiles()).find((profile) => profile.name === "foo_bar"),
  sanitizedSaved,
  "conflict save response metadata must survive a failed list refresh",
);

const declineFixture = createFixture();
declineFixture.apiQueues.listProfiles.push({ profiles: [] });
await declineFixture.runtime.loadProfiles();
declineFixture.runtime.open({ settings: { decline: true }, __easyuseAnimaGeneratorProfileValue: "custom" });
const declineButtons = dialogButtons(declineFixture.dialogs.at(-1));
const declineTarget = {
  name: "decline_canonical",
  profile_id: "55555555-5555-4555-8555-555555555555",
  revision: 3,
};
declineFixture.prompts.push("decline?alias");
declineFixture.apiQueues.saveProfile.push(profileExistsError());
declineFixture.apiQueues.loadProfile.push({ profile: declineTarget });
declineFixture.confirms.push(false);
await declineButtons.save.dispatch("click");
assert.equal(declineFixture.apiCalls.saveProfile.length, 1);
assert.deepEqual(declineFixture.apiCalls.loadProfile, [["decline?alias"]]);
assert.match(declineFixture.confirmCalls.at(-1), /decline_canonical/);
assert.deepEqual(await declineFixture.runtime.loadProfiles(), [declineTarget]);

const messageFixture = createFixture();
messageFixture.apiQueues.listProfiles.push({ profiles: [] });
await messageFixture.runtime.loadProfiles();
messageFixture.runtime.open({ settings: { message: true }, __easyuseAnimaGeneratorProfileValue: "custom" });
const messageButtons = dialogButtons(messageFixture.dialogs.at(-1));
messageFixture.prompts.push("Message Conflict");
messageFixture.apiQueues.saveProfile.push(new Error("Profile already exists"));
await messageButtons.save.dispatch("click");
assert.equal(messageFixture.apiCalls.saveProfile.length, 1);
assert.equal(messageFixture.apiCalls.loadProfile.length, 0);
assert.equal(messageFixture.confirmCalls.length, 0);
assert.match(messageFixture.alerts.at(-1), /Profile already exists/);

const overwriteErrorFixture = createFixture();
const overwriteExisting = {
  name: "Existing",
  profile_id: "66666666-6666-4666-8666-666666666666",
  revision: 4,
};
overwriteErrorFixture.apiQueues.listProfiles.push({ profiles: [overwriteExisting] });
await overwriteErrorFixture.runtime.loadProfiles();
overwriteErrorFixture.runtime.open({ settings: { overwrite: true }, __easyuseAnimaGeneratorProfileValue: "custom" });
const overwriteErrorButtons = dialogButtons(overwriteErrorFixture.dialogs.at(-1));
overwriteErrorFixture.prompts.push("Existing");
overwriteErrorFixture.confirms.push(true);
overwriteErrorFixture.apiQueues.saveProfile.push(profileExistsError("stale overwrite"));
await overwriteErrorButtons.save.dispatch("click");
assert.deepEqual(overwriteErrorFixture.apiCalls.saveProfile, [
  ["Existing", true, { overwrite: true }, overwriteExisting],
]);
assert.equal(overwriteErrorFixture.apiCalls.loadProfile.length, 0);
assert.equal(overwriteErrorFixture.confirmCalls.length, 1);

const tokenlessFixture = createFixture();
tokenlessFixture.apiQueues.listProfiles.push({ profiles: [] });
await tokenlessFixture.runtime.loadProfiles();
tokenlessFixture.runtime.open({ settings: { legacy: true }, __easyuseAnimaGeneratorProfileValue: "custom" });
const tokenlessButtons = dialogButtons(tokenlessFixture.dialogs.at(-1));
const tokenlessTarget = { name: "legacy_name" };
tokenlessFixture.prompts.push("legacy?name");
tokenlessFixture.apiQueues.saveProfile.push(
  profileExistsError(),
  profileExistsError("retry conflict"),
);
tokenlessFixture.apiQueues.loadProfile.push({ profile: tokenlessTarget });
tokenlessFixture.confirms.push(true);
await tokenlessButtons.save.dispatch("click");
assert.deepEqual(tokenlessFixture.apiCalls.saveProfile, [
  ["legacy?name", false, { legacy: true }, null],
  ["legacy?name", true, { legacy: true }, tokenlessTarget],
]);
assert.equal(Object.hasOwn(tokenlessFixture.apiCalls.saveProfile[1][3], "profile_id"), false);
assert.equal(Object.hasOwn(tokenlessFixture.apiCalls.saveProfile[1][3], "revision"), false);
assert.equal(tokenlessFixture.apiCalls.loadProfile.length, 1);
assert.equal(tokenlessFixture.confirmCalls.length, 1);

const staleRenameFixture = createFixture();
const renameSource = {
  name: "Source",
  profile_id: "77777777-7777-4777-8777-777777777777",
  revision: 2,
};
const renameTarget = {
  name: "foo_bar",
  profile_id: "88888888-8888-4888-8888-888888888888",
  revision: 5,
};
staleRenameFixture.apiQueues.listProfiles.push({ profiles: [renameSource] });
await staleRenameFixture.runtime.loadProfiles();
const staleRenameNode = {
  settings: { rename: true },
  __easyuseAnimaGeneratorProfileValue: "user:Source",
  __easyuseAnimaGeneratorProfileFingerprint: "source-fingerprint",
};
staleRenameFixture.runtime.open(staleRenameNode);
const staleRenameButtons = dialogButtons(staleRenameFixture.dialogs.at(-1));
staleRenameButtons.select.value = "user:Source";
staleRenameFixture.prompts.push("foo?bar");
staleRenameFixture.apiQueues.renameProfile.push(profileExistsError());
staleRenameFixture.apiQueues.loadProfile.push({ profile: renameTarget });
staleRenameFixture.confirms.push(true);
const renamedSource = { ...renameSource, name: "foo_bar" };
staleRenameFixture.apiQueues.renameProfile.push({ profile: renamedSource });
staleRenameFixture.apiQueues.listProfiles.push({ profiles: [renamedSource] });
await staleRenameButtons.rename.dispatch("click");
assert.deepEqual(staleRenameFixture.apiCalls.renameProfile, [
  ["Source", "foo?bar", false, renameSource, null],
  ["Source", "foo?bar", true, renameSource, renameTarget],
]);
assert.deepEqual(staleRenameFixture.apiCalls.loadProfile, [["foo?bar"]]);
assert.match(staleRenameFixture.confirmCalls.at(-1), /foo_bar/);
assert.equal(staleRenameNode.__easyuseAnimaGeneratorProfileValue, "user:foo_bar");

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
