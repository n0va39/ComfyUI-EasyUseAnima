import assert from "node:assert/strict";
import { createLoraPresetEntryLifecycle } from "../web/js/lora_preset/entry_lifecycle.js";

function captureOf(options) {
  return options === true || !!options?.capture;
}

class FakeTarget {
  constructor() {
    this.listeners = new Map();
  }

  addEventListener(type, listener, options = false) {
    const records = this.listeners.get(type) || [];
    records.push({ listener, options });
    this.listeners.set(type, records);
  }

  removeEventListener(type, listener, options = false) {
    const capture = captureOf(options);
    const records = this.listeners.get(type) || [];
    this.listeners.set(
      type,
      records.filter((record) => record.listener !== listener || captureOf(record.options) !== capture),
    );
  }

  listenerCount(type) {
    return (this.listeners.get(type) || []).length;
  }

  emit(type, values = {}) {
    const event = { type, target: this, ...values };
    for (const { listener } of [...(this.listeners.get(type) || [])]) {
      listener(event);
    }
    return event;
  }
}

function pointInArea([x, y], [left, top, width, height]) {
  return x >= left && x <= left + width && y >= top && y <= top + height;
}

function createRuntime(hostWindow, hostDocument, app) {
  const calls = {
    applySettings: [],
    beforeRegister: [],
    disposedLocale: 0,
    hidden: 0,
    loadSettings: 0,
    menuDisposed: 0,
    menuInstalled: 0,
    refresh: 0,
    saveSync: 0,
  };
  let localeCallback = null;
  let now = 100;
  const lifecycle = createLoraPresetEntryLifecycle({
    app,
    hostDocument,
    hostWindow,
    nodeTypeName: "EasyUseAnimaLoraPreset",
    canvasWidgets: {
      pointInArea,
      profileVisibleRows: 2,
    },
    clientPointToCanvas: (event) => [event.clientX, event.clientY],
    profileCount: (node) => node.profileCount,
    saveSync: { install() { calls.saveSync += 1; } },
    async loadSettings() { calls.loadSettings += 1; },
    refreshNodes() { calls.refresh += 1; },
    watchLocale(callback) {
      localeCallback = callback;
      return () => { calls.disposedLocale += 1; };
    },
    applySettings(settings) { calls.applySettings.push(settings); },
    previewLifecycle: { hidePreview() { calls.hidden += 1; } },
    menuLifecycle: {
      install() { calls.menuInstalled += 1; },
      dispose() { calls.menuDisposed += 1; },
    },
    nodeRuntime: {
      beforeRegisterNodeDef(nodeType, nodeData) {
        calls.beforeRegister.push([nodeType, nodeData]);
      },
    },
    now: () => now,
  });
  return {
    calls,
    lifecycle,
    tick() { now += 1; },
    triggerLocale() { localeCallback?.(); },
  };
}

const hostWindow = new FakeTarget();
const hostDocument = new FakeTarget();
const app = {
  canvas: {
    canvas: { getBoundingClientRect: () => ({ left: 0, top: 0, right: 100, bottom: 100 }) },
  },
  graph: { _nodes: [] },
};
const runtime = createRuntime(hostWindow, hostDocument, app);
const node = {
  id: 1,
  comfyClass: "EasyUseAnimaLoraPreset",
  pos: [20, 20],
  size: [100, 100],
  profileCount: 4,
  dirty: 0,
  setDirtyCanvas() { this.dirty += 1; },
};
const bar = {
  type: "custom",
  listClientArea: [20, 20, 20, 20],
  listArea: [0, 0, 20, 20],
  scrollOffset: 0,
  computeSize() { return [100, 100]; },
  scrollByWheel(deltaY) {
    this.directWheels = (this.directWheels || 0) + deltaY;
    return true;
  },
};
node.__easyuseAnimaProfileBar = bar;
node.widgets = [bar, { type: "custom" }];
app.graph._nodes.push(node);

assert.equal(runtime.lifecycle.extension.init(), true);
await Promise.resolve();
assert.equal(runtime.calls.saveSync, 1);
assert.equal(runtime.calls.loadSettings, 1);
assert.equal(runtime.calls.refresh, 1, "settings completion must refresh nodes");
assert.equal(runtime.calls.menuInstalled, 1);
assert.equal(hostDocument.listenerCount("wheel"), 1);
assert.equal(hostDocument.listenerCount("pointerdown"), 1);
assert.equal(hostWindow.listenerCount("easyuse-anima-settings-updated"), 1);
assert.equal(runtime.lifecycle.extension.init(), false, "same owner must not duplicate global listeners");
assert.equal(hostDocument.listenerCount("wheel"), 1);

let prevented = 0;
let stopped = 0;
const directWheel = hostDocument.emit("wheel", {
  clientX: 25,
  clientY: 25,
  deltaY: 3,
  preventDefault() { prevented += 1; },
  stopPropagation() { stopped += 1; },
});
assert.equal(directWheel.type, "wheel");
assert.equal(bar.directWheels, 3, "client-area wheel must use the profile-bar handler");
assert.equal(prevented, 1);
assert.equal(stopped, 1);
assert.equal(runtime.lifecycle.getActiveProfileWheelTarget().node, node);

runtime.lifecycle.setActiveProfileWheelTarget(null);
bar.listClientArea = [60, 60, 10, 10];
hostDocument.emit("wheel", {
  clientX: 25,
  clientY: 25,
  deltaY: 1,
  preventDefault() { prevented += 1; },
  stopPropagation() { stopped += 1; },
});
assert.equal(bar.scrollOffset, 1, "canvas hit-testing fallback must preserve profile-list scrolling");
assert.equal(node.dirty, 1);
assert.equal(prevented, 2);
assert.equal(stopped, 2);

runtime.lifecycle.setActiveProfileWheelTarget(null);
bar.listArea = [8, 32, 84, 50];
const node2Element = {
  dataset: { nodeId: "1" },
  querySelectorAll(selector) {
    assert.equal(selector, ".lg-node-widget canvas");
    return [profileCanvas, addLoraCanvas];
  },
};
const profileCanvas = {
  tagName: "CANVAS",
  clientWidth: 100,
  clientHeight: 100,
  closest(selector) {
    if (selector === "canvas") return this;
    if (selector === ".lg-node[data-node-id]") return node2Element;
    return null;
  },
  getBoundingClientRect() {
    return { left: 300, top: 400, width: 200, height: 200 };
  },
};
const addLoraCanvas = {
  ...profileCanvas,
  closest: profileCanvas.closest,
};
hostDocument.emit("wheel", {
  target: profileCanvas,
  clientX: 340,
  clientY: 500,
  deltaY: 2,
  preventDefault() { prevented += 1; },
  stopPropagation() { stopped += 1; },
});
assert.equal(bar.directWheels, 5, "Node 2.0 profile canvas must map its local list area");
assert.equal(prevented, 3);
assert.equal(stopped, 3);

runtime.lifecycle.setActiveProfileWheelTarget(null);
hostDocument.emit("wheel", {
  target: addLoraCanvas,
  clientX: 340,
  clientY: 500,
  deltaY: 2,
  preventDefault() { prevented += 1; },
  stopPropagation() { stopped += 1; },
});
hostDocument.emit("wheel", {
  target: profileCanvas,
  clientX: 340,
  clientY: 420,
  deltaY: 2,
  preventDefault() { prevented += 1; },
  stopPropagation() { stopped += 1; },
});
assert.equal(bar.directWheels, 5, "other Node 2.0 widgets and profile controls must not capture wheel");
assert.equal(prevented, 3);
assert.equal(stopped, 3);

hostWindow.emit("easyuse-anima-settings-updated", { detail: { menuMode: "list" } });
assert.deepEqual(runtime.calls.applySettings, [{ menuMode: "list" }]);
assert.equal(runtime.calls.refresh, 2);
runtime.triggerLocale();
assert.equal(runtime.calls.refresh, 3);
await runtime.lifecycle.extension.beforeRegisterNodeDef("NodeType", { name: "LoRA" });
assert.deepEqual(runtime.calls.beforeRegister, [["NodeType", { name: "LoRA" }]]);

const replacement = createRuntime(hostWindow, hostDocument, app);
assert.equal(replacement.lifecycle.extension.init(), true, "a newer entry owner must replace stale document listeners");
assert.equal(runtime.lifecycle.isActive(), false);
assert.equal(runtime.calls.disposedLocale, 1);
assert.equal(runtime.calls.menuDisposed, 1);
assert.equal(hostDocument.listenerCount("wheel"), 1);
assert.equal(hostDocument.listenerCount("pointerdown"), 1);
assert.equal(hostWindow.listenerCount("easyuse-anima-settings-updated"), 1);

replacement.lifecycle.dispose();
replacement.lifecycle.dispose();
assert.equal(hostDocument.listenerCount("wheel"), 0);
assert.equal(hostDocument.listenerCount("pointerdown"), 0);
assert.equal(hostWindow.listenerCount("easyuse-anima-settings-updated"), 0);
assert.equal(replacement.calls.disposedLocale, 1, "entry disposal must be idempotent");
assert.equal(replacement.calls.menuDisposed, 1);

console.log("LoRA preset entry lifecycle smoke passed.");
