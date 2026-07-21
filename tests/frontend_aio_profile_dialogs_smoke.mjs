import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

class FakeClassList {
  constructor(owner) {
    this.owner = owner;
  }

  add(...tokens) {
    const classes = new Set(String(this.owner.className || "").split(/\s+/).filter(Boolean));
    for (const token of tokens) {
      classes.add(token);
    }
    this.owner.className = [...classes].join(" ");
  }

  contains(token) {
    return String(this.owner.className || "").split(/\s+/).includes(token);
  }
}

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.type = "";
    this.className = "";
    this.textContent = "";
    this.value = "";
    this.children = [];
    this.parentElement = null;
    this.listeners = new Map();
    this.attributes = new Map();
    this.isConnected = true;
    this.focused = false;
    this.selected = false;
    this.classList = new FakeClassList(this);
  }

  append(...children) {
    for (const child of children) {
      child.parentElement = this;
      this.children.push(child);
    }
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  dispatch(type, properties = {}) {
    let prevented = false;
    const event = {
      target: this,
      preventDefault() {
        prevented = true;
      },
      ...properties,
    };
    for (const listener of this.listeners.get(type) || []) {
      listener(event);
    }
    return { prevented };
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  focus() {
    this.focused = true;
  }

  select() {
    this.selected = true;
  }

  remove() {
    this.isConnected = false;
    if (this.parentElement) {
      this.parentElement.children = this.parentElement.children.filter((child) => child !== this);
      this.parentElement = null;
    }
  }
}

const [profileModule, primitiveModule] = await Promise.all([
  import(dataModule("../web/js/aio/profile_dialogs.js")),
  import(dataModule("../web/js/aio/dialog_primitives.js")),
]);
assert.deepEqual(
  Object.keys(profileModule),
  ["aioCreateProfileDialogs"],
  "profile dialogs must expose only their factory contract",
);

const body = new FakeElement("body");
const fakeDocument = {
  body,
  createElement(tagName) {
    return new FakeElement(tagName);
  },
};
const text = (key) => `text:${key}`;
const primitives = primitiveModule.aioCreateDialogPrimitives({
  document: fakeDocument,
  ensureStyle() {},
  staticText: (value) => String(value),
  text,
  resolveFieldPresentation: (label) => ({ displayLabel: label, tooltipText: "" }),
  applyTooltip() {},
  applyTooltipText() {},
});
const dialogs = profileModule.aioCreateProfileDialogs({
  document: fakeDocument,
  createDialog: primitives.createDialog,
  text,
});
assert.deepEqual(Object.keys(dialogs), ["prompt", "alert", "confirm"]);
assert.equal(Object.isFrozen(dialogs), true);

const parent = primitives.createDialog("Parent", "Settings");
assert.equal(body.children.length, 1);

const promptResult = dialogs.prompt("Save profile", "Current");
assert.equal(body.children.length, 2, "nested prompts must be appended after the parent AiO modal");
const promptBackdrop = body.children.at(-1);
const promptDialog = promptBackdrop.children[0];
const promptInput = promptDialog.children[1].children[0];
const promptActions = promptDialog.children[2];
assert.equal(promptDialog.classList.contains("easyuse-anima-aio-dialog-compact"), true);
assert.equal(promptInput.value, "Current");
assert.equal(promptInput.getAttribute("aria-label"), "Save profile");
assert.equal(promptInput.focused, true);
assert.equal(promptInput.selected, true);
promptInput.value = "Spectrum SPD";
promptActions.children[1].dispatch("click");
assert.equal(await promptResult, "Spectrum SPD");
assert.deepEqual(body.children, [parent.backdrop], "accepting a prompt must keep the parent modal open");

const enterResult = dialogs.prompt("Rename profile", "Old");
const enterDialog = body.children.at(-1).children[0];
const enterInput = enterDialog.children[1].children[0];
enterInput.value = "New";
const enterEvent = enterInput.dispatch("keydown", { key: "Enter" });
assert.equal(enterEvent.prevented, true);
assert.equal(await enterResult, "New");

const escapeResult = dialogs.prompt("Cancel profile");
const escapeInput = body.children.at(-1).children[0].children[1].children[0];
const escapeEvent = escapeInput.dispatch("keydown", { key: "Escape" });
assert.equal(escapeEvent.prevented, true);
assert.equal(await escapeResult, null);

const dismissedPrompt = dialogs.prompt("Dismiss profile");
const dismissPromptBackdrop = body.children.at(-1);
dismissPromptBackdrop.dispatch("pointerdown", { target: dismissPromptBackdrop });
assert.equal(await dismissedPrompt, null, "backdrop dismissal must settle prompts as cancelled");

const confirmed = dialogs.confirm("Overwrite?", "overwrite");
const confirmDialog = body.children.at(-1).children[0];
confirmDialog.children[2].children[1].dispatch("click");
assert.equal(await confirmed, true);

const cancelled = dialogs.confirm("Delete?", "delete");
const cancelDialog = body.children.at(-1).children[0];
cancelDialog.children[2].children[0].dispatch("click");
assert.equal(await cancelled, false);

const dismissedConfirm = dialogs.confirm("Dismiss?");
const dismissConfirmDialog = body.children.at(-1).children[0];
dismissConfirmDialog.children[0].children[1].dispatch("click");
assert.equal(await dismissedConfirm, false, "close buttons must settle confirmations as cancelled");

const alertResult = dialogs.alert("Install the required pack", "warn", "Dependency required");
const alertDialog = body.children.at(-1).children[0];
assert.equal(alertDialog.children[0].children[0].children[0].textContent, "Dependency required");
assert.equal(alertDialog.children[0].children[0].children[1].textContent, "Install the required pack");
assert.equal(alertDialog.classList.contains("easyuse-anima-aio-dialog-alert-warn"), true);
alertDialog.children[2].children[0].dispatch("click");
await alertResult;

assert.deepEqual(body.children, [parent.backdrop]);
parent.close();
assert.equal(body.children.length, 0);

console.log("AiO nested profile dialogs smoke passed.");
