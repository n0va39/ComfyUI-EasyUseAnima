import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

// Execute the production global-overlay scheduler with a deterministic clock.
const source = readFileSync(new URL("../web/js/prompt_studio/highlight.js", import.meta.url), "utf8");
const start = source.indexOf("let promptHighlightRefreshRaf = 0;");
const end = source.indexOf("function installPromptHighlightOverlayRefresh", start);
assert(start >= 0 && end > start);
let now = 0;
let nextId = 0;
let refreshes = 0;
const frames = new Map();
const timers = new Map();
const context = vm.createContext({
  document: { querySelectorAll() { refreshes += 1; return []; } },
  requestAnimationFrame(callback) { const id = ++nextId; frames.set(id, callback); return id; },
  setTimeout(callback, delay) { const id = ++nextId; timers.set(id, { callback, at: now + delay }); return id; },
  clearTimeout(id) { timers.delete(id); },
});
vm.runInContext(`${source.slice(start, end)}\nglobalThis.schedule = requestConnectedHighlightOverlayRefresh;`, context);
function flushTimers() {
  for (const [id, timer] of [...timers]) {
    if (timer.at <= now) { timers.delete(id); timer.callback(); }
  }
}
for (let frame = 0; frame < 60; frame++) {
  now = frame * 1000 / 60;
  flushTimers();
  for (let event = 0; event < 3; event++) context.schedule();
  assert.equal(timers.size, 1, "Continuous wheel events must share one final stabilization timer");
  const batch = [...frames.values()];
  frames.clear();
  for (const callback of batch) callback();
}
assert.equal(refreshes, 60, "One whole-editor measurement per animation frame during the gesture");
now += 100;
flushTimers();
assert.equal(refreshes, 61, "Exactly one final refresh after the gesture");
assert.equal(timers.size, 0);
assert.equal(frames.size, 0);
console.log("Prompt Studio canvas scroll refresh smoke passed: 180 requests, 61 passes, no pending work.");
