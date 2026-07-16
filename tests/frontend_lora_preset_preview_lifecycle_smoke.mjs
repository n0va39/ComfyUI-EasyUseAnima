import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createFakeDocument } from "./frontend_support/fake_dom.mjs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const previewModule = await import(
  dataModule("../web/js/lora_preset/preview_lifecycle.js")
);

assert.deepEqual(Object.keys(previewModule).sort(), [
  "createLoraPresetPreviewLifecycle",
  "loraPreviewPosition",
]);

assert.deepEqual(
  previewModule.loraPreviewPosition(
    { clientX: 20, clientY: 30 },
    { width: 800, height: 600 },
    360,
  ),
  [38, 48],
);
assert.deepEqual(
  previewModule.loraPreviewPosition(
    { clientX: 780, clientY: 590 },
    { width: 800, height: 600 },
    360,
  ),
  [402, 228],
);

const document = createFakeDocument();
document.body.boundingClientRect = { left: 0, top: 0, width: 800, height: 600 };
document.querySelector = (selector) => document.body.querySelector(selector);
document.body.appendChild = (child) => {
  document.body.append(child);
  return child;
};
const createElement = document.createElement.bind(document);
document.createElement = (tagName) => {
  const element = createElement(tagName);
  element.removeAttribute = (name) => element.attributes.delete(String(name));
  return element;
};

const encodedNames = [];
const lifecycle = previewModule.createLoraPresetPreviewLifecycle({
  document,
  encodeURIComponent(value) {
    encodedNames.push(value);
    return `encoded:${value}`;
  },
  previewSize: 360,
});

assert.deepEqual(Object.keys(lifecycle).sort(), [
  "forgetMissingPreview",
  "hidePreview",
  "showPreview",
]);
assert.equal(document.body.children.length, 0, "factory creation must not create DOM state");

lifecycle.showPreview("", { clientX: 20, clientY: 30 });
lifecycle.showPreview("None", { clientX: 20, clientY: 30 });
assert.equal(document.body.children.length, 0);
assert.deepEqual(encodedNames, []);

const firstName = "style/foo.safetensors";
lifecycle.showPreview(firstName, { clientX: 20, clientY: 30 });
assert.equal(document.body.children.length, 1);
const preview = document.body.children[0];
assert.equal(preview.className, "easyuse-anima-lora-preview");
assert.equal(preview.listenerCount("error"), 1);
assert.equal(preview.listenerCount("load"), 1);
assert.equal(preview.getAttribute("data-name"), firstName);
assert.equal(preview.getAttribute("data-visible"), "1");
assert.equal(preview.getAttribute("data-loaded"), null);
assert.equal(preview.style.display, "none");
assert.equal(preview.style.left, "38px");
assert.equal(preview.style.top, "48px");
assert.equal(
  preview.src,
  "/easyuse_anima/lora_preview?name=encoded:style/foo.safetensors",
);
assert.deepEqual(encodedNames, [firstName]);

preview.naturalWidth = 512;
preview.emit("load");
assert.equal(preview.getAttribute("data-loaded"), "1");
assert.equal(preview.style.display, "block");

lifecycle.hidePreview();
assert.equal(preview.getAttribute("data-visible"), null);
assert.equal(preview.style.display, "none");

lifecycle.showPreview(firstName, { clientX: 780, clientY: 590 });
assert.equal(document.body.children[0], preview, "the lifecycle must reuse its singleton image");
assert.equal(preview.getAttribute("data-visible"), "1");
assert.equal(preview.style.display, "block");
assert.equal(preview.style.left, "402px");
assert.equal(preview.style.top, "228px");

preview.emit("error");
assert.equal(preview.getAttribute("data-name"), null);
assert.equal(preview.getAttribute("data-loaded"), null);
assert.equal(preview.getAttribute("data-visible"), null);
assert.equal(preview.style.display, "none");

lifecycle.showPreview(firstName, { clientX: 40, clientY: 50 });
assert.equal(document.body.children.length, 1);
assert.equal(preview.getAttribute("data-name"), null);
assert.deepEqual(
  encodedNames,
  [firstName, firstName],
  "a cached failed name must not request another preview URL",
);

lifecycle.forgetMissingPreview(firstName);
lifecycle.showPreview(firstName, { clientX: 40, clientY: 50 });
assert.equal(preview.getAttribute("data-name"), firstName);
assert.equal(preview.getAttribute("data-visible"), "1");
assert.equal(preview.style.display, "none");
assert.deepEqual(encodedNames, [firstName, firstName, firstName]);
preview.emit("error");

const secondName = "style/bar.safetensors";
lifecycle.showPreview(secondName, { clientX: 40, clientY: 50 });
assert.equal(document.body.children[0], preview);
assert.equal(preview.getAttribute("data-name"), secondName);
assert.equal(preview.getAttribute("data-visible"), "1");
assert.equal(preview.style.display, "none");
assert.equal(preview.style.left, "58px");
assert.equal(preview.style.top, "68px");
assert.equal(
  preview.src,
  "/easyuse_anima/lora_preview?name=encoded:style/bar.safetensors",
);
assert.deepEqual(encodedNames, [firstName, firstName, firstName, secondName]);

console.log("LoRA preset preview lifecycle smoke passed.");
