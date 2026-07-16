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

let innerHtmlOptionUses = 0;
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
    innerHtmlOptionUses += 1;
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
const observers = [];
let observerConstructionError = null;
let observerObserveError = null;
let observerDisconnectError = null;
class StubMutationObserver {
  constructor(callback) {
    if (observerConstructionError) {
      const error = observerConstructionError;
      observerConstructionError = null;
      throw error;
    }
    this.callback = callback;
    this.disconnected = false;
    observer = this;
    observers.push(this);
  }

  observe(target, options) {
    this.target = target;
    this.options = options;
    if (observerObserveError) {
      const error = observerObserveError;
      observerObserveError = null;
      throw error;
    }
  }

  disconnect() {
    this.disconnected = true;
    if (observerDisconnectError) {
      const error = observerDisconnectError;
      observerDisconnectError = null;
      throw error;
    }
  }
}

const animationFrames = [];
let runAnimationFramesImmediately = true;
const window = {
  requestAnimationFrame(callback) {
    animationFrames.push(callback);
    if (runAnimationFramesImmediately) {
      callback();
    }
    return animationFrames.length;
  },
};

const shownPreviews = [];
let hiddenPreviews = 0;
let hidePreviewError = null;
const previewLifecycle = {
  showPreview(name, event) {
    shownPreviews.push({ name, event });
  },
  hidePreview() {
    hiddenPreviews += 1;
    if (hidePreviewError) {
      const error = hidePreviewError;
      hidePreviewError = null;
      throw error;
    }
  },
};

const positionCalls = [];
let menuMode = "list";
let currentNode = null;
const lifecycleDependencies = {
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
};
const lifecycle = menuModule.createLoraPresetMenuLifecycle(lifecycleDependencies);

assert.deepEqual(Object.keys(lifecycle).sort(), [
  "activateMenu",
  "createMenuItems",
  "dispose",
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

const lifecycleDispose = lifecycle.install();
assert.equal(lifecycleDispose, lifecycle.dispose);
assert.equal(document.head.children.length, 1);
assert.equal(document.head.children[0].tagName, "STYLE");
assert.match(document.head.children[0].textContent, /easyuse-anima-lora-search/);
assert.match(document.head.children[0].textContent, /easyuse-anima-lora-preview/);
assert.match(
  document.head.children[0].textContent,
  /easyuse-anima-combo-folder-label\s*\{[^}]*margin-left:\s*0\.25em;/,
);
assert.ok(observer);
assert.equal(observer.target, document.body);
assert.deepEqual(observer.options, { childList: true, subtree: false });
const firstObserver = observer;
const firstStyle = document.head.children[0];
assert.equal(lifecycle.install(), lifecycleDispose);
assert.equal(observers.length, 1, "repeated install must reuse the current observer");
assert.equal(document.head.children.length, 1, "repeated install must reuse the current style");
assert.equal(firstObserver.disconnected, false);

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

const unrelatedRemovedMenu = createElement("div", { className: "litecontextmenu" });
observer.callback([{ addedNodes: [], removedNodes: [unrelatedRemovedMenu] }]);
assert.equal(hiddenPreviews, 1, "unrelated context-menu removal must not hide the preview");
const ownedRemovedMenu = createElement("div", {
  className: "litecontextmenu easyuse-anima-lora-menu",
});
observer.callback([{ addedNodes: [], removedNodes: [ownedRemovedMenu] }]);
assert.equal(hiddenPreviews, 2);

menuMode = "tree";
const treeNode = {
  comfyClass: "EasyUseAnimaLoraPreset",
};
currentNode = treeNode;
const treeValues = [
  "styles/anime/foo.safetensors",
  "styles/real/bar.safetensors",
  "unsafe/<img src=x onerror=alert(1)>/baz.safetensors",
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
assert.equal(treeFolders.length, 5);
assert.equal(treeContainers.length, 5);
assert.equal(innerHtmlOptionUses, 0, "folder rendering must not use innerHTML");
const folderLabels = treeMenu.querySelectorAll(".easyuse-anima-combo-folder-label");
assert.equal(folderLabels.length, treeFolders.length);
assert.ok(
  folderLabels.some((label) => label.textContent === "<img src=x onerror=alert(1)>"),
);
assert.equal(treeMenu.querySelector("img"), null, "folder text must not create markup nodes");

const treeEntries = treeMenu.querySelectorAll(
  ".litemenu-entry:not(.easyuse-anima-combo-folder)",
);
assert.equal(treeEntries.length, 4);
assert.equal(
  treeEntries.filter((entry) => entry.querySelector(".easyuse-anima-combo-prefix")).length,
  3,
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
  removedNodes: [unrelatedRemovedMenu],
}]);
assert.equal(positionCalls.length, positionCount);
assert.equal(hiddenPreviews, 2, "unrelated removal must remain inert after node selection changes");
const selectedAwayOwnedMenu = createElement("div", {
  className: "litecontextmenu easyuse-anima-lora-menu",
});
observer.callback([{ addedNodes: [], removedNodes: [selectedAwayOwnedMenu] }]);
assert.equal(hiddenPreviews, 3, "removed menus must hide previews after node selection changes");

observerConstructionError = new Error("observer construction failed");
const constructionFailureLifecycle = menuModule.createLoraPresetMenuLifecycle(
  lifecycleDependencies,
);
assert.throws(() => constructionFailureLifecycle.install(), /observer construction failed/);
assert.equal(firstObserver.disconnected, false, "failed replacement must retain the old owner");
assert.equal(document.head.children.length, 1);
assert.equal(document.head.children[0], firstStyle);
assert.equal(
  document.createdElements.filter((element) => element.tagName === "STYLE").at(-1).removed,
  true,
  "constructor failure must clean its detached style",
);
assert.equal(hiddenPreviews, 3);

observerObserveError = new Error("observer observe failed");
const observeFailureLifecycle = menuModule.createLoraPresetMenuLifecycle(
  lifecycleDependencies,
);
assert.throws(() => observeFailureLifecycle.install(), /observer observe failed/);
const failedObserver = observers.at(-1);
assert.equal(failedObserver.disconnected, true, "observe failure must disconnect its observer");
assert.equal(firstObserver.disconnected, false);
assert.equal(document.head.children.length, 1);
assert.equal(document.head.children[0], firstStyle);
assert.equal(
  document.createdElements.filter((element) => element.tagName === "STYLE").at(-1).removed,
  true,
  "observe failure must remove its appended style",
);
assert.equal(hiddenPreviews, 3, "failed replacement must not dispose the active owner");

runAnimationFramesImmediately = false;
menuMode = "list";
const nestedFrameNode = {
  comfyClass: "EasyUseAnimaLoraPreset",
};
currentNode = nestedFrameNode;
const nestedFrameItems = lifecycle.createMenuItems(["nested/frame.safetensors"]);
lifecycle.activateMenu(nestedFrameNode, [360, 380], nestedFrameItems);
const nestedFrameMenu = makeMenu(nestedFrameItems.length);
const menuFrameIndex = animationFrames.length;
firstObserver.callback([{ addedNodes: [nestedFrameMenu], removedNodes: [] }]);
assert.equal(nestedFrameMenu.__easyuseAnimaListReady, undefined);
animationFrames[menuFrameIndex]();
assert.equal(nestedFrameMenu.__easyuseAnimaListReady, true);
const nestedSearch = nestedFrameMenu.querySelector("input");
assert.equal(nestedSearch.focused, false);
const nestedSearchFrameIndex = animationFrames.length - 1;
const nestedPositionCount = positionCalls.length;

const staleNode = {
  comfyClass: "EasyUseAnimaLoraPreset",
};
currentNode = staleNode;
const staleItems = lifecycle.createMenuItems(["stale/menu.safetensors"]);
lifecycle.activateMenu(staleNode, [400, 420], staleItems);
const staleMenu = makeMenu(staleItems.length);
const staleFrameIndex = animationFrames.length;
firstObserver.callback([{ addedNodes: [staleMenu], removedNodes: [] }]);
assert.equal(staleMenu.__easyuseAnimaListReady, undefined);

const replacementLifecycle = menuModule.createLoraPresetMenuLifecycle(lifecycleDependencies);
assert.equal(document.head.children.length, 1, "factory creation must not replace the owner");
const replacementDispose = replacementLifecycle.dispose;
const previousOwnerError = new Error("previous owner preview cleanup failed");
hidePreviewError = previousOwnerError;
assert.throws(
  () => replacementLifecycle.install(),
  (error) => error === previousOwnerError,
  "owner replacement must preserve the prior teardown error",
);
assert.equal(firstObserver.disconnected, true, "owner replacement must disconnect the old observer");
assert.equal(firstStyle.removed, true, "owner replacement must remove the old style");
assert.equal(staleNode.__easyuseAnimaOpeningLoraMenu, false);
assert.equal(hiddenPreviews, 4, "owner replacement must clean up an active preview");
assert.equal(document.head.children.length, 1);
assert.equal(observers.length, 3);
const replacementObserver = observer;
const replacementStyle = document.head.children[0];
replacementObserver.callback([{ addedNodes: [], removedNodes: [listMenu] }]);
assert.equal(hiddenPreviews, 4, "replacement owners must ignore stale owned-menu removal");

animationFrames[nestedSearchFrameIndex]();
assert.equal(nestedSearch.focused, false, "disposed nested search frames must stay inert");
assert.equal(positionCalls.length, nestedPositionCount);
animationFrames[staleFrameIndex]();
assert.equal(staleMenu.__easyuseAnimaListReady, undefined, "disposed owner frames must stay inert");
runAnimationFramesImmediately = true;

const disposedShownPreviewCount = shownPreviews.length;
const disposedHiddenPreviewCount = hiddenPreviews;
const disposedPositionCount = positionCalls.length;
listSearch.value = "FOO";
listSearch.emit("input");
assert.equal(listEntries[0].style.display, "");
assert.equal(listEntries[1].style.display, "");
assert.equal(positionCalls.length, disposedPositionCount);
const disposedEscape = listSearch.emit("keydown", { key: "Escape" });
assert.equal(listSearch.value, "FOO");
assert.equal(disposedEscape.defaultPrevented, false);
assert.equal(disposedEscape.propagationStopped, false);
listEntries[0].emit("mouseover", { clientX: 50, clientY: 60 });
listEntries[0].emit("mousemove", { clientX: 70, clientY: 80 });
listEntries[0].emit("mouseout");
assert.equal(shownPreviews.length, disposedShownPreviewCount);
assert.equal(hiddenPreviews, disposedHiddenPreviewCount);
const disposedFolderDisplay = topContainer.style.display;
const disposedFolderOpen = topContainer.__easyuseAnimaOpen;
const disposedFolderArrow = topFolder.querySelector(
  ".easyuse-anima-combo-folder-arrow",
).textContent;
const disposedFolderClick = topFolder.emit("click");
assert.equal(disposedFolderClick.propagationStopped, false);
assert.equal(topContainer.style.display, disposedFolderDisplay);
assert.equal(topContainer.__easyuseAnimaOpen, disposedFolderOpen);
assert.equal(
  topFolder.querySelector(".easyuse-anima-combo-folder-arrow").textContent,
  disposedFolderArrow,
);

assert.equal(lifecycle.dispose(), false, "disposing a replaced owner must be idempotent");
assert.equal(replacementObserver.disconnected, false);
assert.equal(document.head.children[0], replacementStyle);
assert.equal(hiddenPreviews, 4);
assert.equal(replacementLifecycle.install(), replacementDispose);
assert.equal(observers.length, 3, "replacement install must also be idempotent");

assert.equal(replacementLifecycle.dispose(), true);
assert.equal(replacementObserver.disconnected, true);
assert.equal(replacementStyle.removed, true);
assert.equal(document.head.children.length, 0);
assert.equal(hiddenPreviews, 5);
assert.equal(replacementLifecycle.dispose(), false);
assert.equal(hiddenPreviews, 5, "repeated dispose must not repeat preview cleanup");

assert.equal(replacementLifecycle.install(), replacementDispose);
assert.equal(document.head.children.length, 1);
assert.equal(observers.length, 4, "install after dispose must create a fresh observer");
assert.notEqual(observer, replacementObserver);
const disconnectFailure = new Error("observer disconnect failed");
observerDisconnectError = disconnectFailure;
assert.throws(
  () => replacementLifecycle.dispose(),
  (error) => error === disconnectFailure,
  "dispose must preserve the first cleanup error",
);
assert.equal(observer.disconnected, true);
assert.equal(document.head.children.length, 0);
assert.equal(hiddenPreviews, 6);
assert.equal(
  replacementLifecycle.dispose(),
  false,
  "failed cleanup must still leave the lifecycle disposed",
);

const ownerKey = Symbol.for("easyuse-anima.lora-preset.menu-lifecycle-owner");
let refusingOwnerCalls = 0;
const refusingOwner = () => {
  refusingOwnerCalls += 1;
};
document[ownerKey] = refusingOwner;
const refusedLifecycle = menuModule.createLoraPresetMenuLifecycle(lifecycleDependencies);
const observerCountBeforeRefusal = observers.length;
assert.throws(
  () => refusedLifecycle.install(),
  /previous LoRA preset menu lifecycle did not release ownership/,
);
assert.equal(refusingOwnerCalls, 1);
assert.equal(document[ownerKey], refusingOwner, "install must not steal retained ownership");
assert.equal(observers.length, observerCountBeforeRefusal + 1);
assert.equal(observers.at(-1).disconnected, true);
assert.equal(document.head.children.length, 0);
assert.equal(hiddenPreviews, 6, "failed owner replacement must not clean unrelated preview state");
assert.equal(refusedLifecycle.dispose(), false);
delete document[ownerKey];

console.log("LoRA preset menu lifecycle smoke passed.");
