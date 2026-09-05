import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const geometry = await import(dataModule("../web/js/autocomplete/popup_geometry.js"));

assert.deepEqual(Object.keys(geometry).sort(), [
  "calculateAutocompletePopupGeometry",
  "calculateCaretMirrorGeometry",
  "normalizeCaretClientRect",
].sort());

const {
  calculateAutocompletePopupGeometry,
  calculateCaretMirrorGeometry,
  normalizeCaretClientRect,
} = geometry;

function rect(left, top, width, height) {
  return {
    left,
    right: left + width,
    top,
    bottom: top + height,
    width,
    height,
  };
}

assert.deepEqual(
  calculateCaretMirrorGeometry(rect(10, 20, 400, 180), 200, 120),
  {
    layoutWidth: 200,
    layoutHeight: 120,
    scaleX: 2,
    scaleY: 1.5,
  },
);
assert.deepEqual(
  calculateCaretMirrorGeometry(rect(10, 20, 0, 0), 0, 0),
  {
    layoutWidth: 1,
    layoutHeight: 1,
    scaleX: 1,
    scaleY: 1,
  },
);

const inputRect = rect(100, 50, 420, 160);
const markerRect = rect(240, 120, 1, 0);
assert.deepEqual(
  normalizeCaretClientRect(markerRect, inputRect, 24),
  { ...markerRect, height: 24 },
);
const invalidMarker = { ...markerRect, left: Number.NaN };
assert.equal(normalizeCaretClientRect(invalidMarker, inputRect, 24), inputRect);

assert.deepEqual(
  calculateAutocompletePopupGeometry(
    inputRect,
    rect(240, 120, 1, 24),
    { width: 1024, height: 768 },
    18,
  ),
  {
    left: 240,
    top: 180,
    width: 380,
    maxHeight: 280,
  },
);

assert.deepEqual(
  calculateAutocompletePopupGeometry(
    rect(900, 700, 200, 60),
    rect(1200, 800, 1, 0),
    { width: 1024, height: 768 },
    20,
  ),
  {
    left: 760,
    top: 704,
    width: 260,
    maxHeight: 56,
  },
);

for (const fixture of [
  {
    name: "caret below the clipped editor viewport",
    input: rect(100, 200, 420, 1800),
    caret: rect(240, 1137.61, 1, 14),
    top: 656,
    maxHeight: 56,
  },
  {
    name: "caret above the viewport after scrolling",
    input: rect(100, -400, 420, 600),
    caret: rect(240, -300, 1, 20),
    top: 4,
    maxHeight: 280,
  },
  {
    name: "lower edge with enough room for normal placement",
    input: rect(100, 500, 420, 160),
    caret: rect(240, 590, 1, 24),
    top: 650,
    maxHeight: 62,
  },
  {
    name: "lower edge requiring the minimum menu budget",
    input: rect(100, 500, 420, 160),
    caret: rect(240, 630, 1, 24),
    top: 656,
    maxHeight: 56,
  },
]) {
  const viewport = { width: 1280, height: 720 };
  const popup = calculateAutocompletePopupGeometry(fixture.input, fixture.caret, viewport, 18);
  assert.equal(popup.top, fixture.top, fixture.name);
  assert.equal(popup.maxHeight, fixture.maxHeight, fixture.name);
  assert.ok(popup.top >= 4, `${fixture.name}: popup must remain below the top margin`);
  assert.ok(popup.maxHeight >= 56, `${fixture.name}: popup must retain its minimum height budget`);
  assert.ok(popup.top + popup.maxHeight <= viewport.height - 8, `${fixture.name}: popup must fit above the bottom margin`);
}

console.log("frontend autocomplete popup geometry smoke passed");
