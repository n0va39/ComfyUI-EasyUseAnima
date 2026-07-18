import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

globalThis.Path2D = class Path2D {
  constructor(path) {
    this.path = path;
  }
};

const canvasModule = await import(
  dataModule("../web/js/lora_preset/canvas_widgets.js")
);

assert.deepEqual(Object.keys(canvasModule), ["createLoraPresetCanvasWidgets"]);

const settings = {
  strengthButtonStep: 0.05,
  strengthDragStep: 0.05,
  strengthDragPixels: 8,
};
const calls = [];
const previewCalls = [];
const promptCalls = [];
let activeProfileWheelTarget = null;
let chosenLoraCallback = null;

const canvas = {
  editor_alpha: 1,
  prompt(message, value, callback, event) {
    promptCalls.push({ message, value, callback, event });
  },
};
const liteGraph = {
  WIDGET_TEXT_COLOR: "#ddd",
  WIDGET_BGCOLOR: "#222",
  WIDGET_OUTLINE_COLOR: "#555",
};

function normalizeLoraEntry(value) {
  return {
    name: String(value?.name || ""),
    on: value?.on !== false,
    strength: Number(value?.strength ?? 1),
    strengthTwo: value?.strengthTwo ?? null,
  };
}

function updateLoraEntry(node, index, patch, options = {}) {
  calls.push(["updateLoraEntry", index, { ...patch }, { ...options }]);
  if (node.loras[index]) {
    Object.assign(node.loras[index], patch);
  }
}

function makeNode(options = {}) {
  return {
    size: [options.width ?? 520, 240],
    pos: [100, 200],
    profileCount: options.profileCount ?? 8,
    activeProfileIndex: options.activeProfileIndex ?? 2,
    pathProblem: options.pathProblem ?? true,
    loraFixPending: options.loraFixPending ?? false,
    profileFixPending: options.profileFixPending ?? false,
    loras: options.loras ?? [
      { name: "style/foo.safetensors", on: true, strength: 1, strengthTwo: null },
      { name: "style/bar.safetensors", on: false, strength: 0.8, strengthTwo: null },
    ],
    widgets: options.widgets ?? [],
    dirtyCalls: [],
    setDirtyCanvas(...args) {
      this.dirtyCalls.push(args);
    },
  };
}

const dependencies = {
  getCanvas: () => canvas,
  getLiteGraph: () => liteGraph,
  getSettings: () => settings,
  text: (key) => key,
  formatText: (key, values = {}) => `${key}:${values.active}/${values.count}`,
  normalizeLoraEntry,
  lorasWidgetValue: (node) => node.loras,
  mutateLoras(node, mutator, options = {}) {
    calls.push(["mutateLoras", { ...options }]);
    mutator(node.loras);
  },
  updateLoraEntry,
  loraResolveState: (node) => ({ pathProblem: node.pathProblem }),
  hasLoraPathProblem: (state) => state.pathProblem === true,
  isAnyLoraFixPending: (node) => node.profileFixPending,
  isLoraFixPending: (node) => node.loraFixPending,
  loraDisplayName: (name) => String(name).split("/").pop(),
  previewLifecycle: {
    showPreview(name, event) {
      previewCalls.push(["show", name, event]);
    },
    hidePreview() {
      previewCalls.push(["hide"]);
    },
  },
  openLoraMenu(node, event, pos, onChoose) {
    calls.push(["openLoraMenu", node, event, pos]);
    chosenLoraCallback = onChoose;
  },
  openLoraEntryMenu: (node, event, index) => calls.push(["openLoraEntryMenu", node, event, index]),
  addLoraEntry: (node, entry) => calls.push(["addLoraEntry", node, entry]),
  fixSingleLoraEntry: (node, index) => calls.push(["fixSingleLoraEntry", node, index]),
  profileCount: (node) => node.profileCount,
  activeProfileIndex: (node) => node.activeProfileIndex,
  profileSaveStatus: (_node, index) => ({
    state: index === 1 ? "saved" : "changed",
    savedName: index === 1 ? "Demo" : "",
    labelKey: index === 1 ? "profile.saved" : "profile.changed",
  }),
  addProfile: (node) => calls.push(["addProfile", node]),
  deleteProfile: (node, index) => calls.push(["deleteProfile", node, index]),
  saveProfileSet: (node) => calls.push(["saveProfileSet", node]),
  openProfileLoadMenu: (node, event, pos) => calls.push(["openProfileLoadMenu", node, event, pos]),
  fixProfileLoras: (node) => calls.push(["fixProfileLoras", node]),
  switchProfile: (node, index) => calls.push(["switchProfile", node, index]),
  nodePosToClient: (node, pos) => [node.pos[0] + pos[0], node.pos[1] + pos[1]],
  getActiveProfileWheelTarget: () => activeProfileWheelTarget,
  setActiveProfileWheelTarget(target) {
    activeProfileWheelTarget = target;
  },
  enforceNodeLayout(node) {
    calls.push(["enforceNodeLayout", node]);
  },
};

const runtime = canvasModule.createLoraPresetCanvasWidgets(dependencies);
assert.deepEqual(Object.keys(runtime).sort(), [
  "AddLoraWidget",
  "LoraHeaderWidget",
  "LoraRowWidget",
  "ProfileBarWidget",
  "clearLoraStrengthDrag",
  "ensureProfileBar",
  "minNodeWidth",
  "pointInArea",
  "profileVisibleRows",
  "renderLoraWidgets",
  "renderProfileBar",
]);
assert.equal(runtime.minNodeWidth, 520);
assert.equal(runtime.profileVisibleRows, 6);
assert.equal(runtime.pointInArea([10, 20], [10, 20, 30, 40]), true);
assert.equal(runtime.pointInArea([40, 60], [10, 20, 30, 40]), true);
assert.equal(runtime.pointInArea([40.1, 60], [10, 20, 30, 40]), false);

function fakeContext() {
  const textCalls = [];
  return {
    textCalls,
    save() {},
    restore() {},
    beginPath() {},
    roundRect() {},
    moveTo() {},
    lineTo() {},
    quadraticCurveTo() {},
    rect() {},
    clip() {},
    arc() {},
    fill() {},
    stroke() {},
    measureText(value) {
      return { width: String(value).length * 6 };
    },
    fillText(value, x, y) {
      textCalls.push({ value, x, y });
    },
  };
}

const profileWidget = new runtime.ProfileBarWidget();
const headerWidget = new runtime.LoraHeaderWidget();
const rowWidget = new runtime.LoraRowWidget(0);
const addWidget = new runtime.AddLoraWidget();
for (const widget of [profileWidget, headerWidget, rowWidget, addWidget]) {
  assert.equal(widget.type, "custom");
  assert.equal(widget.serialize, false);
  assert.deepEqual(widget.options, { serialize: false });
}
assert.equal(profileWidget.name, "easyuse_anima_profile_bar");
assert.equal(headerWidget.name, "easyuse_anima_lora_header");
assert.equal(rowWidget.name, "easyuse_anima_lora_0");
assert.equal(addWidget.name, "easyuse_anima_add_lora");
assert.deepEqual(profileWidget.computeSize(undefined, makeNode({ profileCount: 1 })), [520, 60]);
assert.deepEqual(profileWidget.computeSize(undefined, makeNode({ profileCount: 8 })), [520, 170]);
assert.deepEqual(headerWidget.computeSize(), [520, 24]);
assert.deepEqual(rowWidget.computeSize(), [520, 20]);
assert.deepEqual(addWidget.computeSize(), [520, 36]);

{
  const node = makeNode({
    widgets: [
      { name: "style_prompt" },
      { name: "stale_control", __easyuseAnimaControlWidget: true },
      { name: "lora_name" },
      { name: "loras" },
      { name: "stale_lora", __easyuseAnimaLoraWidget: true },
    ],
  });
  runtime.ensureProfileBar(node);
  assert.deepEqual(node.widgets.map((widget) => widget.name), [
    "style_prompt",
    "easyuse_anima_profile_bar",
    "lora_name",
    "loras",
    "easyuse_anima_lora_header",
    "easyuse_anima_lora_0",
    "easyuse_anima_lora_1",
    "easyuse_anima_add_lora",
  ]);
  const firstBar = node.__easyuseAnimaProfileBar;
  runtime.ensureProfileBar(node);
  assert.equal(node.__easyuseAnimaProfileBar, firstBar);
  assert.equal(node.widgets.filter((widget) => widget.name === "easyuse_anima_profile_bar").length, 1);
  node.loras = [];
  runtime.renderLoraWidgets(node);
  assert.deepEqual(node.widgets.map((widget) => widget.name), [
    "style_prompt",
    "easyuse_anima_profile_bar",
    "lora_name",
    "loras",
    "easyuse_anima_add_lora",
  ]);
}

{
  const node = makeNode({ profileCount: 8 });
  const widget = new runtime.ProfileBarWidget();
  let drawRequests = 0;
  widget.triggerDraw = () => { drawRequests += 1; };
  const ctx = fakeContext();
  widget.draw(ctx, node, 520, 0, 170);
  assert.deepEqual(widget.hitAreas.slice(0, 5).map((area) => area[4]), [
    "load",
    "save",
    "fix",
    "delete",
    "add",
  ]);
  assert.deepEqual(widget.listArea, [8, 34, 504, 132]);
  assert.deepEqual(widget.listClientArea, [108, 234, 504, 132]);
  assert.ok(widget.scrollTrackArea);
  assert.ok(widget.scrollThumbArea);

  const clickArea = (id) => {
    const area = widget.hitAreas.find((candidate) => candidate[4] === id);
    assert.ok(area, `missing hit area ${id}`);
    const event = { type: "pointerdown", button: 0 };
    const pos = [area[0] + area[2] / 2, area[1] + area[3] / 2];
    assert.equal(widget.mouse(event, pos, node), true);
  };
  for (const id of ["add", "delete", "save", "load", "fix", "profile:3"]) {
    clickArea(id);
  }
  assert.ok(calls.some((call) => call[0] === "addProfile"));
  assert.ok(calls.some((call) => call[0] === "deleteProfile" && call[2] === 2));
  assert.ok(calls.some((call) => call[0] === "saveProfileSet"));
  assert.ok(calls.some((call) => call[0] === "openProfileLoadMenu"));
  assert.ok(calls.some((call) => call[0] === "fixProfileLoras"));
  assert.ok(calls.some((call) => call[0] === "switchProfile" && call[2] === 3));

  assert.equal(widget.mouse({ type: "wheel", deltaY: 1 }, [20, 50], node), true);
  assert.equal(widget.scrollOffset, 1);
  assert.equal(drawRequests, 1, "Node 2.0 custom-widget canvas must redraw after wheel scrolling");
  assert.equal(widget.mouse({ type: "pointermove" }, [20, 50], node), false);
  assert.equal(activeProfileWheelTarget.node, node);
  assert.equal(activeProfileWheelTarget.widget, widget);
  assert.equal(widget.mouse({ type: "pointerout" }, [700, 700], node), false);
  assert.equal(activeProfileWheelTarget, null);

  const thumb = widget.scrollThumbArea;
  const thumbPos = [thumb[0] + 1, thumb[1] + 1];
  assert.equal(widget.mouse({ type: "pointerdown", button: 0 }, thumbPos, node), true);
  assert.equal(widget.scrollDragging, true);
  assert.equal(widget.mouse({ type: "pointermove" }, [thumbPos[0], widget.scrollTrackArea[1] + widget.scrollTrackArea[3]], node), true);
  assert.equal(drawRequests, 2, "Node 2.0 custom-widget canvas must redraw after scrollbar dragging");
  assert.equal(widget.mouse({ type: "pointerup" }, thumbPos, node), true);
  assert.equal(widget.scrollDragging, false);
}

{
  const ctx = fakeContext();
  const narrow = makeNode({ width: 229 });
  const row = new runtime.LoraRowWidget(0);
  row.draw(ctx, narrow, 520, 0, 20);
  assert.equal(row.hitAreas.toggle[0], 6);
  assert.equal(row.hitAreas.strengthAny, null);
  assert.equal(row.hitAreas.menu, null);
  assert.equal(row.hitAreas.info, null);
  assert.equal(row.hitAreas.fix, null);

  for (const [width, expected] of [
    [230, { strength: true, menu: false, info: false, fix: false }],
    [280, { strength: true, menu: true, info: false, fix: false }],
    [310, { strength: true, menu: true, info: true, fix: false }],
    [330, { strength: true, menu: true, info: true, fix: true }],
  ]) {
    const thresholdNode = makeNode({ width });
    row.draw(fakeContext(), thresholdNode, 520, 0, 20);
    assert.equal(!!row.hitAreas.strengthAny, expected.strength, `strength at ${width}`);
    assert.equal(!!row.hitAreas.menu, expected.menu, `menu at ${width}`);
    assert.equal(!!row.hitAreas.info, expected.info, `info at ${width}`);
    assert.equal(!!row.hitAreas.fix, expected.fix, `fix at ${width}`);
  }
  const wide = makeNode({ width: 340 });
  row.draw(fakeContext(), wide, 520, 0, 20);
  assert.equal(row.hitAreas.toggle[0], 10);

  const shortHeaderContext = fakeContext();
  headerWidget.draw(shortHeaderContext, makeNode({ width: 319 }), 520, 0, 24);
  assert.ok(shortHeaderContext.textCalls.some((call) => call.value === "lora.allShort"));
  assert.ok(shortHeaderContext.textCalls.some((call) => call.value === "lora.strengthShort"));
  const fullHeaderContext = fakeContext();
  headerWidget.draw(fullHeaderContext, makeNode({ width: 320 }), 520, 0, 24);
  assert.ok(fullHeaderContext.textCalls.some((call) => call.value === "lora.toggleAll"));
  assert.ok(fullHeaderContext.textCalls.some((call) => call.value === "lora.strength"));
}

function rowWithHitAreas() {
  const row = new runtime.LoraRowWidget(0);
  row.hitAreas = {
    toggle: [0, 0, 10, 20],
    fix: [20, 0, 10, 20],
    lora: [40, 0, 10, 20],
    menu: [60, 0, 10, 20],
    info: [80, 0, 10, 20],
    dec: [100, 0, 9, 20],
    value: [112, 0, 32, 20],
    inc: [148, 0, 9, 20],
    strengthAny: [100, 0, 57, 20],
  };
  return row;
}

{
  const node = makeNode();
  let row = rowWithHitAreas();
  assert.equal(row.mouse({ type: "pointerdown", button: 0 }, [5, 10], node), true);
  assert.equal(node.loras[0].on, false);
  row = rowWithHitAreas();
  assert.equal(row.mouse({ type: "pointerdown", button: 0 }, [25, 10], node), true);
  assert.ok(calls.some((call) => call[0] === "fixSingleLoraEntry"));
  row = rowWithHitAreas();
  assert.equal(row.mouse({ type: "pointerdown", button: 0 }, [45, 10], node), true);
  assert.ok(chosenLoraCallback);
  chosenLoraCallback({ name: "replacement.safetensors" });
  assert.equal(node.loras[0].name, "replacement.safetensors");
  row = rowWithHitAreas();
  assert.equal(row.mouse({ type: "pointerdown", button: 0 }, [65, 10], node), true);
  assert.ok(calls.some((call) => call[0] === "openLoraEntryMenu"));
  row = rowWithHitAreas();
  assert.equal(row.mouse({ type: "pointermove" }, [85, 10], node), false);
  assert.equal(previewCalls.at(-1)[0], "show");
  assert.equal(row.mouse({ type: "pointermove" }, [15, 10], node), false);
  assert.deepEqual(previewCalls.at(-1), ["hide"]);
  assert.equal(row.mouse({ type: "pointerout" }, [15, 10], node), false);
  assert.deepEqual(previewCalls.at(-1), ["hide"]);
  assert.equal(row.mouse({ type: "pointercancel" }, [15, 10], node), false);
  assert.deepEqual(previewCalls.at(-1), ["hide"]);
  row = rowWithHitAreas();
  assert.equal(row.mouse({ type: "pointerdown", button: 2 }, [300, 10], node), true);

  node.loras[0].strength = 1;
  row = rowWithHitAreas();
  assert.equal(row.mouse({ type: "pointerdown", button: 0 }, [104, 10], node), true);
  assert.equal(node.loras[0].strength, 0.95);
  row = rowWithHitAreas();
  assert.equal(row.mouse({ type: "pointerdown", button: 0 }, [152, 10], node), true);
  assert.equal(node.loras[0].strength, 1);
}

{
  const node = makeNode({ loras: [{ name: "drag.safetensors", on: true, strength: 1 }] });
  const row = rowWithHitAreas();
  assert.equal(row.mouse({ type: "pointerdown", button: 0 }, [120, 10], node), true);
  assert.deepEqual(node.__easyuseAnimaStrengthDrag, {
    index: 0,
    startX: 120,
    startStrength: 1,
    lastSteps: 0,
    moved: false,
    promptOnClick: true,
  });
  const previewCountBeforeDragOut = previewCalls.length;
  assert.equal(addWidget.mouse({ type: "pointerout" }, [127, 10], node), true);
  assert.equal(previewCalls.length, previewCountBeforeDragOut);
  assert.equal(headerWidget.mouse({ type: "pointermove" }, [127, 10], node), true);
  assert.equal(node.loras[0].strength, 1);
  assert.equal(headerWidget.mouse({ type: "pointermove" }, [128, 10], node), true);
  assert.equal(node.loras[0].strength, 1.05);
  assert.equal(headerWidget.mouse({ type: "pointermove" }, [136, 10], node), true);
  assert.equal(node.loras[0].strength, 1.1);
  assert.equal(headerWidget.mouse({ type: "pointermove" }, [120, 10], node), true);
  assert.equal(node.loras[0].strength, 1);
  assert.equal(headerWidget.mouse({ type: "pointerup" }, [120, 10], node), true);
  assert.equal(node.__easyuseAnimaStrengthDrag, null);
  assert.equal(promptCalls.length, 0);

  assert.equal(row.mouse({ type: "pointerdown", button: 0 }, [120, 10], node), true);
  const pointerUpEvent = { type: "pointerup" };
  assert.equal(addWidget.mouse(pointerUpEvent, [120, 10], node), true);
  assert.equal(promptCalls.length, 1);
  assert.equal(promptCalls[0].message, "lora.strengthPrompt");
  assert.equal(promptCalls[0].value, 1);
  assert.equal(promptCalls[0].event, pointerUpEvent);
  promptCalls[0].callback("1.2345");
  assert.equal(node.loras[0].strength, 1.235);

  assert.equal(row.mouse({ type: "pointerdown", button: 0 }, [120, 10], node), true);
  assert.equal(profileWidget.mouse({ type: "pointercancel" }, [120, 10], node), true);
  assert.equal(node.__easyuseAnimaStrengthDrag, null);
  assert.equal(promptCalls.length, 1);
}

{
  const node = makeNode();
  const header = new runtime.LoraHeaderWidget();
  header.toggleArea = [0, 0, 20, 20];
  assert.equal(header.mouse({ type: "pointerdown", button: 0 }, [5, 5], node), true);
  assert.ok(node.loras.every((lora) => lora.on === true));

  const add = new runtime.AddLoraWidget();
  add.hitArea = [0, 0, 100, 20];
  assert.equal(add.mouse({ type: "pointerdown", button: 0 }, [5, 5], node), true);
  chosenLoraCallback({ name: "added.safetensors" });
  assert.ok(calls.some((call) => call[0] === "addLoraEntry" && call[2].name === "added.safetensors"));
}

console.log("LoRA preset canvas widgets smoke passed.");
