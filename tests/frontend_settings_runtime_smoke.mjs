import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const runtimeModule = await import(dataModule("../web/js/settings/runtime.js"));

assert.deepEqual(Object.keys(runtimeModule), ["createSettingsRuntime"]);

let state;
const setStateCalls = [];
const notifyCalls = [];
const normalizeCalls = [];
const initialCalls = [];
const fetchCalls = [];
const postCalls = [];

let initialImplementation = async () => ({ source: "initial" });
let fetchImplementation = async () => ({});
let postImplementation = async () => ({});

const internalKeys = {
  "Known.Text": "known.text",
  "Known.Boolean": "known.boolean",
  "Known.Number": "known.number",
};

const runtime = runtimeModule.createSettingsRuntime({
  getSettingsState: () => state,
  setSettingsState(value) {
    state = value;
    setStateCalls.push(value);
  },
  notifySettingsUpdated(detail) {
    notifyCalls.push(detail);
  },
  internalKeys,
  normalizeValue(type, value) {
    normalizeCalls.push({ type, value });
    if (type === "boolean") {
      return value ? "true" : "false";
    }
    return String(value ?? "");
  },
  fetchInitialSettings() {
    initialCalls.push({});
    return initialImplementation();
  },
  fetchJson(route, options) {
    fetchCalls.push({ route, options });
    return fetchImplementation(route, options);
  },
  postJson(route, body, options) {
    postCalls.push({ route, body, options });
    return postImplementation(route, body, options);
  },
});

assert.deepEqual(Object.keys(runtime), [
  "updateInternalSetting",
  "readInternalSetting",
  "loadLongTextSettings",
  "saveLongTextSettings",
  "loadInitialSettings",
]);
assert.equal(state, undefined, "Factory creation must not create state");
assert.deepEqual(setStateCalls, []);
assert.deepEqual(notifyCalls, []);
assert.deepEqual(normalizeCalls, []);
assert.deepEqual(initialCalls, []);
assert.deepEqual(fetchCalls, []);
assert.deepEqual(postCalls, []);

assert.equal(runtime.readInternalSetting("missing", "fallback"), "fallback");
assert.equal(state, undefined, "Read must not create state");

state = Object.create({ inherited: "prototype value" });
Object.assign(state, {
  empty: "",
  falseValue: false,
  zero: 0,
  nullValue: null,
  undefinedValue: undefined,
});
assert.equal(runtime.readInternalSetting("empty", "fallback"), "");
assert.equal(runtime.readInternalSetting("falseValue", "fallback"), false);
assert.equal(runtime.readInternalSetting("zero", "fallback"), 0);
assert.equal(runtime.readInternalSetting("nullValue", "fallback"), null);
assert.equal(runtime.readInternalSetting("undefinedValue", "fallback"), undefined);
assert.equal(runtime.readInternalSetting("inherited", "fallback"), "fallback");

state = undefined;
runtime.updateInternalSetting("Unknown", "ignored");
assert.equal(state, undefined, "Unknown IDs must not create state");
assert.deepEqual(normalizeCalls, []);
assert.deepEqual(notifyCalls, []);

runtime.updateInternalSetting("Known.Text", null);
assert.deepEqual(normalizeCalls, [{ type: "text", value: null }]);
assert.deepEqual(state, { "known.text": "" });
assert.equal(setStateCalls.at(-1), state);
assert.deepEqual(notifyCalls, [{ "known.text": "" }]);
assert.notEqual(notifyCalls[0], state, "Notifications must use a state snapshot");

runtime.updateInternalSetting("Known.Boolean", false, "boolean");
assert.deepEqual(normalizeCalls.at(-1), { type: "boolean", value: false });
assert.deepEqual(state, {
  "known.text": "",
  "known.boolean": "false",
});
assert.deepEqual(notifyCalls.at(-1), {
  "known.text": "",
  "known.boolean": "false",
});
assert.deepEqual(
  notifyCalls[0],
  { "known.text": "" },
  "Later updates must not mutate prior notification details",
);

runtime.updateInternalSetting("Known.Number", 0, "number");
assert.deepEqual(normalizeCalls.at(-1), { type: "number", value: 0 });
assert.equal(state["known.number"], "0");
const notifyCountBeforeRepeat = notifyCalls.length;
runtime.updateInternalSetting("Known.Number", 0, "number");
assert.equal(
  notifyCalls.length,
  notifyCountBeforeRepeat + 1,
  "Known updates must notify even when the normalized value is unchanged",
);

state = { keep: "original", shared: "before" };
fetchImplementation = async () => ({
  settings: { shared: "settings", fromSettings: "yes" },
  values: { shared: "values", fromValues: "yes" },
});
const notifyCountBeforeLoad = notifyCalls.length;
const loaded = await runtime.loadLongTextSettings();
assert.deepEqual(fetchCalls.at(-1), {
  route: "/easyuse_anima/long_text_settings",
  options: { fallbackJson: {} },
});
assert.deepEqual(state, {
  keep: "original",
  shared: "values",
  fromSettings: "yes",
  fromValues: "yes",
});
assert.deepEqual(loaded, state);
assert.notEqual(loaded, state, "Long-text load must return a shallow clone");
loaded.keep = "changed clone";
assert.equal(state.keep, "original");
assert.equal(notifyCalls.length, notifyCountBeforeLoad, "Long-text load must not notify");

const stateBeforeLoadFailure = { ...state };
const loadFailure = new Error("load failed");
fetchImplementation = async () => {
  throw loadFailure;
};
await assert.rejects(runtime.loadLongTextSettings(), (error) => error === loadFailure);
assert.deepEqual(state, stateBeforeLoadFailure);
assert.equal(notifyCalls.length, notifyCountBeforeLoad);

const saveResponse = {
  settings: { shared: "save settings", fromSaveSettings: "yes" },
  values: { shared: "save values", fromSaveValues: "yes" },
  marker: "raw response",
};
postImplementation = async () => saveResponse;
const values = { field: "submitted" };
const notifyCountBeforeSave = notifyCalls.length;
const saved = await runtime.saveLongTextSettings(values);
assert.deepEqual(postCalls.at(-1), {
  route: "/easyuse_anima/long_text_settings/save",
  body: { values },
  options: { fallbackJson: {} },
});
assert.equal(saved, saveResponse, "Save must return the raw API response object");
assert.equal(state.shared, "save values");
assert.equal(state.fromSaveSettings, "yes");
assert.equal(state.fromSaveValues, "yes");
assert.equal(notifyCalls.length, notifyCountBeforeSave + 1);
assert.deepEqual(notifyCalls.at(-1), state);
assert.notEqual(notifyCalls.at(-1), state);

const stateBeforeSaveFailure = { ...state };
const saveFailure = new Error("save failed");
postImplementation = async () => {
  throw saveFailure;
};
await assert.rejects(
  runtime.saveLongTextSettings({ field: "rejected" }),
  (error) => error === saveFailure,
);
assert.deepEqual(state, stateBeforeSaveFailure);
assert.equal(notifyCalls.length, notifyCountBeforeSave + 1);

postImplementation = async () => ({});
const notifyCountBeforeEmptySave = notifyCalls.length;
const emptySave = await runtime.saveLongTextSettings({});
assert.deepEqual(emptySave, {});
assert.deepEqual(state, stateBeforeSaveFailure);
assert.equal(
  notifyCalls.length,
  notifyCountBeforeEmptySave + 1,
  "An empty fallback response must still preserve the existing save notification",
);

const stateBeforeInitialLoad = state;
const notifyCountBeforeInitialLoad = notifyCalls.length;
const initialResponse = { initial: "settings" };
initialImplementation = async () => initialResponse;
assert.equal(await runtime.loadInitialSettings(), initialResponse);
assert.equal(state, stateBeforeInitialLoad, "Initial load must not assign host state itself");
assert.equal(notifyCalls.length, notifyCountBeforeInitialLoad);

initialImplementation = async () => {
  throw new Error("initial failed");
};
assert.deepEqual(await runtime.loadInitialSettings(), {});
assert.equal(state, stateBeforeInitialLoad);
assert.equal(notifyCalls.length, notifyCountBeforeInitialLoad);
assert.equal(initialCalls.length, 2);

console.log("Settings runtime smoke passed.");
