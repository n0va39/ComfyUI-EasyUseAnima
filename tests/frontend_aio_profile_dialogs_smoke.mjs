import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

const module = await import(dataModule("../web/js/aio/profile_dialogs.js"));
assert.deepEqual(
  Object.keys(module),
  ["aioCreateProfileDialogs"],
  "profile dialogs must expose only their factory contract",
);

const calls = { prompt: [], confirm: [], toast: [] };
const promptResults = ["Spectrum SPD", null, 42];
const confirmResults = [true, false, null];
let managerReads = 0;
const extensionManager = {
  dialog: {
    async prompt(options) {
      calls.prompt.push(options);
      return promptResults.shift();
    },
    async confirm(options) {
      calls.confirm.push(options);
      return confirmResults.shift();
    },
  },
  toast: {
    add(options) {
      calls.toast.push(options);
    },
  },
};
const dialogs = module.aioCreateProfileDialogs({
  getExtensionManager() {
    managerReads += 1;
    return extensionManager;
  },
  text(key) {
    return `text:${key}`;
  },
});

assert.deepEqual(Object.keys(dialogs), ["prompt", "alert", "confirm"]);
assert.equal(Object.isFrozen(dialogs), true);
assert.equal(managerReads, 0, "factory creation must not read host services eagerly");

assert.equal(await dialogs.prompt("Save profile", "Current"), "Spectrum SPD");
assert.deepEqual(calls.prompt.at(-1), {
  title: "text:dialog.profile.title",
  message: "Save profile",
  defaultValue: "Current",
  placeholder: "",
});
assert.equal(await dialogs.prompt("Cancel"), null);
assert.equal(await dialogs.prompt("Invalid host result"), null);

assert.equal(await dialogs.confirm("Overwrite?", "overwrite"), true);
assert.equal(await dialogs.confirm("Delete?", "delete"), false);
assert.equal(await dialogs.confirm("Dismissed"), false);
assert.deepEqual(calls.confirm, [
  {
    title: "text:dialog.profile.title",
    message: "Overwrite?",
    type: "overwrite",
  },
  {
    title: "text:dialog.profile.title",
    message: "Delete?",
    type: "delete",
  },
  {
    title: "text:dialog.profile.title",
    message: "Dismissed",
    type: "default",
  },
]);

await dialogs.alert("Profile operation failed", "error");
assert.deepEqual(calls.toast, [{
  severity: "error",
  summary: "text:dialog.profile.title",
  detail: "Profile operation failed",
  life: 5000,
}]);

const missingDialogs = module.aioCreateProfileDialogs({
  getExtensionManager: () => ({}),
  text: (key) => key,
});
await assert.rejects(
  missingDialogs.prompt("Unavailable"),
  /ComfyUI dialog service is unavailable/,
);

console.log("AiO profile host dialogs smoke passed.");
