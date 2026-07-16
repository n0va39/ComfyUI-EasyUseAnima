import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  createFakeDocument,
  descendants,
} from "./frontend_support/fake_dom.mjs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const menuModule = await import(
  dataModule("../web/js/lora_preset/menu_lifecycle.js")
);

assert.deepEqual(Object.keys(menuModule), ["createLoraPresetMenuLifecycle"]);

const document = createFakeDocument();

function addDomCompat(element) {
  if (element.__menuSmokeDomCompat) {
    return element;
  }
  element.__menuSmokeDomCompat = true;
  const addEventListener = element.addEventListener.bind(element);
  element.__listenerOptions = new Map();
  element.addEventListener = (type, handler, options = false) => {
    const entries = element.__listenerOptions.get(type) || [];
    entries.push(options);
    element.__listenerOptions.set(type, entries);
    addEventListener(type, handler, options);
  };
  element.appendChild = (child) => {
    element.append(child);
    return child;
  };
  element.insertBefore = (child, reference) => {
    child.parentElement = element;
    const index = element.children.indexOf(reference);
    if (index < 0) {
      element.children.push(child);
    } else {
      element.children.splice(index, 0, child);
    }
    return child;
  };
  Object.defineProperty(element, "firstChild", {
    configurable: true,
    get() {
      return element.children[0] || null;
    },
  });
  return element;
}

addDomCompat(document.body);
document.head = addDomCompat(document.createElement("head"));

function createElement(tagName, options = {}) {
  const element = addDomCompat(document.createElement(tagName));
  if (options.className != null) {
    element.className = String(options.className);
  }
  if (options.textContent != null) {
    element.textContent = String(options.textContent);
  }
  if (options.style) {
    Object.assign(element.style, options.style);
  }
  if (options.innerHTML != null) {
    element.innerHTML = String(options.innerHTML);
    if (element.innerHTML.includes("easyuse-anima-combo-folder-arrow")) {
      const arrow = createElement("span", {
        className: "easyuse-anima-combo-folder-arrow",
        textContent: "▶",
      });
      element.appendChild(arrow);
    }
  }
  return element;
}

function validComboEntryText(value, depth = 0) {
  if (value == null || depth > 2) {
    return "";
  }
  if (typeof value === "string" || typeof value === "number") {
    const text = String(value).trim();
    return text && text !== "None" && text !== "[object Object]" ? text : "";
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const text = validComboEntryText(item, depth + 1);
      if (text) {
        return text;
      }
    }
    return "";
  }
  if (typeof value === "object") {
    for (const key of ["value", "content", "name", "title", "text", "label", "path", "filename"]) {
      const text = validComboEntryText(value[key], depth + 1);
      if (text) {
        return text;
      }
    }
  }
  return "";
}

function installMenuSelectors(menu) {
  const originalQuerySelectorAll = menu.querySelectorAll.bind(menu);
  menu.querySelectorAll = (selector) => {
    if (selector === ".litemenu-entry:not(.easyuse-anima-combo-folder)") {
      return descendants(menu).filter(
        (element) => element.classList.contains("litemenu-entry")
          && !element.classList.contains("easyuse-anima-combo-folder"),
      );
    }
    return originalQuerySelectorAll(selector);
  };
  return menu;
}

function makeMenu(entryCount, options = {}) {
  const menu = installMenuSelectors(createElement("div", {
    className: "litecontextmenu easyuse-anima-lora-menu",
  }));
  if (options.existingSearch) {
    menu.appendChild(createElement("input", {
      className: "comfy-context-menu-filter",
    }));
  }
  for (let index = 0; index < entryCount; index += 1) {
    const entry = createElement("div", { className: "litemenu-entry" });
    entry.textContent = index === 0 ? "[object Object]" : "";
    menu.appendChild(entry);
  }
  return menu;
}

let observer = null;
class StubMutationObserver {
  constructor(callback) {
    assert.equal(observer, null, "install must create one observer");
    this.callback = callback;
    this.disconnected = false;
    observer = this;
  }

  observe(target, options) {
    this.target = target;
    this.options = options;
  }

  disconnect() {
    this.disconnected = true;
  }
}

const animationFrames = [];
const window = {
  requestAnimationFrame(callback) {
    animationFrames.push(callback);
    callback();
    return animationFrames.length;
  },
};

const shownPreviews = [];
let hiddenPreviews = 0;
const previewLifecycle = {
  showPreview(name, event) {
    shownPreviews.push({ name, event });
  },
  hidePreview() {
    hiddenPreviews += 1;
  },
};

const positionCalls = [];
let menuMode = "list";
let currentNode = null;
const lifecycle = menuModule.createLoraPresetMenuLifecycle({
  document,
  window,
  MutationObserver: StubMutationObserver,
  createElement,
  validComboEntryText,
  previewLifecycle,
  positionMenu(menu, point) {
    positionCalls.push({ menu, point });
  },
  text(key) {
    return key === "lora.search" ? "Search LoRA" : key;
  },
  getMenuMode() {
    return menuMode;
  },
  getCurrentNode() {
    return currentNode;
  },
  nodeType: "EasyUseAnimaLoraPreset",
  previewSize: 360,
});

assert.deepEqual(Object.keys(lifecycle).sort(), [
  "activateMenu",
  "createMenuItems",
  "install",
]);
assert.equal(document.head.children.length, 0, "factory creation must not install DOM state");

const escapedItems = lifecycle.createMenuItems([
  "None",
  "",
  { value: "style/x<&\"'.safetensors" },
]);
assert.deepEqual(escapedItems, [{
  content: "style/x&lt;&amp;&quot;&#39;.safetensors",
  value: "style/x<&\"'.safetensors",
}]);

lifecycle.install();
assert.equal(document.head.children.length, 1);
assert.equal(document.head.children[0].tagName, "STYLE");
assert.match(document.head.children[0].textContent, /easyuse-anima-lora-search/);
assert.match(document.head.children[0].textContent, /easyuse-anima-lora-preview/);
assert.ok(observer);
assert.equal(observer.target, document.body);
assert.deepEqual(observer.options, { childList: true, subtree: false });

const listNode = {
  comfyClass: "EasyUseAnimaLoraPreset",
};
currentNode = listNode;
const listValues = [
  "style/foo.safetensors",
  "style/x-y.safetensors",
];
const listItems = lifecycle.createMenuItems(listValues);
lifecycle.activateMenu(listNode, [140, 160], listItems);
assert.equal(listNode.__easyuseAnimaOpeningLoraMenu, true);
assert.deepEqual(listNode.__easyuseAnimaLoraMenuPoint, [140, 160]);
assert.deepEqual(listNode.__easyuseAnimaLoraMenuValues, listValues);

const listMenu = makeMenu(listItems.length);
observer.callback([{ addedNodes: [listMenu], removedNodes: [] }]);
assert.equal(listNode.__easyuseAnimaOpeningLoraMenu, false);
assert.equal(listMenu.__easyuseAnimaListReady, true);

const listEntries = listMenu.querySelectorAll(
  ".litemenu-entry:not(.easyuse-anima-combo-folder)",
);
assert.equal(listEntries.length, 2);
assert.equal(listEntries[0].textContent, listValues[0]);
assert.equal(listEntries[0].getAttribute("data-value"), listValues[0]);
assert.equal(listEntries[0].getAttribute("title"), listValues[0]);
assert.equal(
  listEntries[0].getAttribute("data-search"),
  "style foo.safetensors style foo.safetensors",
);
assert.equal(listEntries[0].listenerCount("mouseover"), 1);
assert.equal(listEntries[0].listenerCount("mousemove"), 1);
assert.equal(listEntries[0].listenerCount("mouseout"), 1);
for (const eventName of ["mouseover", "mousemove", "mouseout"]) {
  assert.deepEqual(listEntries[0].__listenerOptions.get(eventName), [
    { passive: true },
  ]);
}

const hoverEvent = { clientX: 12, clientY: 24 };
listEntries[0].emit("mouseover", hoverEvent);
listEntries[0].emit("mousemove", hoverEvent);
listEntries[0].emit("mouseout");
assert.equal(shownPreviews.length, 2);
assert.equal(shownPreviews[0].name, listValues[0]);
assert.equal(shownPreviews[0].event.target, listEntries[0]);
assert.equal(shownPreviews[0].event.clientX, 12);
assert.equal(shownPreviews[1].name, listValues[0]);
assert.equal(shownPreviews[1].event.clientY, 24);
assert.equal(hiddenPreviews, 1);

const listSearch = listMenu.querySelector("input");
assert.ok(listSearch);
assert.equal(listMenu.children[0], listSearch);
assert.equal(listSearch.type, "search");
assert.equal(listSearch.placeholder, "Search LoRA");
assert.equal(listSearch.focused, true);

listSearch.value = "FOO";
listSearch.emit("input");
assert.equal(listEntries[0].style.display, "");
assert.equal(listEntries[1].style.display, "none");

const escapeEvent = listSearch.emit("keydown", { key: "Escape" });
assert.equal(escapeEvent.defaultPrevented, true);
assert.equal(escapeEvent.propagationStopped, true);
assert.equal(listSearch.value, "");
assert.equal(listEntries[1].style.display, "");

listNode.__easyuseAnimaOpeningLoraMenu = true;
observer.callback([{ addedNodes: [listMenu], removedNodes: [] }]);
assert.equal(listEntries[0].listenerCount("mouseover"), 1);
assert.equal(listSearch.listenerCount("input"), 1);

const removedMenu = createElement("div", { className: "litecontextmenu" });
observer.callback([{ addedNodes: [], removedNodes: [removedMenu] }]);
assert.equal(hiddenPreviews, 2);

menuMode = "tree";
const treeNode = {
  comfyClass: "EasyUseAnimaLoraPreset",
};
currentNode = treeNode;
const treeValues = [
  "styles/anime/foo.safetensors",
  "styles/real/bar.safetensors",
  "flat.safetensors",
];
const treeItems = lifecycle.createMenuItems(treeValues);
lifecycle.activateMenu(treeNode, [220, 240], treeItems);
const treeMenu = makeMenu(treeItems.length);
observer.callback([{ addedNodes: [treeMenu], removedNodes: [] }]);
assert.equal(treeNode.__easyuseAnimaOpeningLoraMenu, false);
assert.equal(treeMenu.__easyuseAnimaTreeReady, true);

const treeFolders = treeMenu.querySelectorAll(".easyuse-anima-combo-folder");
const treeContainers = treeMenu.querySelectorAll(
  ".easyuse-anima-combo-folder-contents",
);
assert.equal(treeFolders.length, 3);
assert.equal(treeContainers.length, 3);

const treeEntries = treeMenu.querySelectorAll(
  ".litemenu-entry:not(.easyuse-anima-combo-folder)",
);
assert.equal(treeEntries.length, 3);
assert.equal(
  treeEntries.filter((entry) => entry.querySelector(".easyuse-anima-combo-prefix")).length,
  2,
);

const topFolder = treeFolders.find((folder) => folder.style.paddingLeft === "5px");
assert.ok(topFolder);
const topContainer = topFolder.parentElement.children[
  topFolder.parentElement.children.indexOf(topFolder) + 1
];
assert.equal(topContainer.style.display, "none");
const folderClick = topFolder.emit("click");
assert.equal(folderClick.propagationStopped, true);
assert.equal(topContainer.__easyuseAnimaOpen, true);
assert.equal(topContainer.style.display, "block");
assert.equal(
  topFolder.querySelector(".easyuse-anima-combo-folder-arrow").textContent,
  "▼",
);

const treeSearch = treeMenu.querySelector("input");
treeSearch.value = "anime foo";
treeSearch.emit("input");
assert.ok(treeFolders.every((folder) => folder.style.display === "none"));
assert.ok(treeContainers.every((container) => container.style.display === "block"));
assert.equal(
  treeEntries.filter((entry) => entry.style.display !== "none").length,
  1,
);

treeSearch.value = "";
treeSearch.emit("input");
assert.ok(treeFolders.every((folder) => folder.style.display === ""));
assert.equal(topContainer.style.display, "block");
assert.equal(
  treeContainers.filter((container) => container !== topContainer)
    .every((container) => container.style.display === "none"),
  true,
);

const existingNode = {
  comfyClass: "EasyUseAnimaLoraPreset",
};
currentNode = existingNode;
menuMode = "list";
const existingValues = ["native/search.safetensors"];
lifecycle.activateMenu(
  existingNode,
  [300, 320],
  lifecycle.createMenuItems(existingValues),
);
const existingSearchMenu = makeMenu(1, { existingSearch: true });
const existingSearch = existingSearchMenu.children[0];
observer.callback([{ addedNodes: [existingSearchMenu], removedNodes: [] }]);
assert.equal(existingSearchMenu.querySelectorAll("input").length, 1);
assert.equal(existingSearch.listenerCount("input"), 1);
assert.equal(existingSearch.focused, true);

const positionCount = positionCalls.length;
currentNode = { comfyClass: "DifferentNode" };
observer.callback([{
  addedNodes: [makeMenu(1)],
  removedNodes: [removedMenu],
}]);
assert.equal(positionCalls.length, positionCount);
assert.equal(hiddenPreviews, 2);

console.log("LoRA preset menu lifecycle smoke passed.");
