import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

function dataModule(relativePath) {
  const source = readFileSync(new URL(relativePath, import.meta.url), "utf8");
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function createScheduler() {
  let nextHandle = 1;
  const frames = new Map();
  const timers = new Map();
  return {
    requestFrame(callback) {
      const handle = nextHandle++;
      frames.set(handle, callback);
      return handle;
    },
    cancelFrame(handle) {
      frames.delete(handle);
    },
    setTimer(callback, delay) {
      const handle = nextHandle++;
      timers.set(handle, { callback, delay });
      return handle;
    },
    clearTimer(handle) {
      timers.delete(handle);
    },
    frameCount() {
      return frames.size;
    },
    timerCount() {
      return timers.size;
    },
    timerDelays() {
      return [...timers.values()].map((entry) => entry.delay);
    },
    async flushFrames() {
      const callbacks = [...frames.values()];
      frames.clear();
      for (const callback of callbacks) {
        await callback();
      }
    },
    async flushTimers() {
      const callbacks = [...timers.values()].map((entry) => entry.callback);
      timers.clear();
      for (const callback of callbacks) {
        await callback();
      }
    },
  };
}

const controllerModule = await import(
  dataModule("../web/js/autocomplete/input_controller.js")
);
assert.deepEqual(Object.keys(controllerModule), [
  "createAutocompleteInputController",
  "invalidateAutocompleteControllerStates",
]);

const {
  createAutocompleteInputController,
  invalidateAutocompleteControllerStates,
} = controllerModule;

{
  let sharedInvalidations = 0;
  let activeInvalidations = 0;
  let detachedActiveInvalidations = 0;
  const sharedController = {
    invalidate() {
      sharedInvalidations += 1;
    },
  };
  const activeController = {
    invalidate() {
      activeInvalidations += 1;
    },
  };
  const detachedActiveController = {
    invalidate() {
      detachedActiveInvalidations += 1;
    },
  };

  invalidateAutocompleteControllerStates(
    [
      { controller: sharedController },
      { controller: sharedController },
      { controller: activeController },
      {},
      null,
    ],
    { controller: activeController },
  );
  assert.equal(
    sharedInvalidations,
    1,
    "duplicate state references must invalidate a shared controller once",
  );
  assert.equal(
    activeInvalidations,
    1,
    "the active popup clone must not invalidate its controller twice",
  );

  invalidateAutocompleteControllerStates([], {
    controller: detachedActiveController,
  });
  assert.equal(
    detachedActiveInvalidations,
    1,
    "an active popup controller must be invalidated even after input-set cleanup",
  );
}

{
  const scheduler = createScheduler();
  let updateCount = 0;
  const controller = createAutocompleteInputController({
    ...scheduler,
    async onUpdate() {
      updateCount += 1;
    },
    onError(error) {
      throw error;
    },
  });

  controller.scheduleCaretUpdate();
  controller.scheduleCaretUpdate();
  controller.scheduleCaretUpdate();
  controller.scheduleCaretUpdate();
  assert.equal(scheduler.frameCount(), 1, "caret event bursts must coalesce to one frame");
  await scheduler.flushFrames();
  assert.equal(updateCount, 1);

  controller.scheduleUpdate();
  controller.scheduleUpdate();
  controller.scheduleUpdate();
  assert.equal(scheduler.timerCount(), 1, "input event bursts must keep one debounce timer");
  assert.deepEqual(scheduler.timerDelays(), [120]);
  await scheduler.flushTimers();
  assert.equal(updateCount, 2);

  controller.scheduleUpdate();
  await controller.updateNow();
  assert.equal(scheduler.timerCount(), 0, "an immediate refresh must cancel pending debounce work");
  assert.equal(updateCount, 3);

  controller.beginComposition();
  assert.equal(controller.isComposing({}), true);
  assert.equal(controller.isComposing({ isComposing: true }), true);
  assert.equal(controller.isComposing({ keyCode: 229 }), true);
  controller.scheduleUpdate();
  assert.equal(scheduler.timerCount(), 1, "composition updates must retain debounced searching");
  controller.endComposition();
  assert.equal(controller.isComposing({}), false);
  assert.equal(controller.isCompositionEndUpdatePending(), true);
  assert.equal(scheduler.timerCount(), 0);
  assert.equal(scheduler.frameCount(), 1, "composition end must own one final caret refresh");
  controller.scheduleUpdate();
  assert.equal(
    scheduler.timerCount(),
    0,
    "the final input after compositionend must not downgrade the frame to debounce",
  );
  assert.equal(scheduler.frameCount(), 1);
  await scheduler.flushFrames();
  assert.equal(controller.isCompositionEndUpdatePending(), false);
  assert.equal(updateCount, 4);

  controller.scheduleUpdate();
  controller.invalidate();
  assert.equal(scheduler.timerCount(), 0, "close/invalidate must cancel scheduled input work");
  await scheduler.flushTimers();
  assert.equal(updateCount, 4);

  controller.scheduleCaretUpdate();
  controller.dispose();
  assert.equal(scheduler.frameCount(), 0, "dispose must cancel scheduled caret work");
  controller.scheduleCaretUpdate();
  await controller.updateNow();
  assert.equal(scheduler.frameCount(), 0);
  assert.equal(updateCount, 4, "disposed controllers must ignore future updates");
}

{
  const scheduler = createScheduler();
  const pending = new Map();
  const loaderCalls = new Map();
  const applied = [];
  const errors = [];
  let requestKey = "same";

  const controller = createAutocompleteInputController({
    ...scheduler,
    async onUpdate(context) {
      const key = requestKey;
      const result = await context.request(key, () => {
        loaderCalls.set(key, (loaderCalls.get(key) || 0) + 1);
        const request = deferred();
        pending.set(key, request);
        return request.promise;
      });
      if (context.isCurrent()) {
        applied.push(result);
      }
    },
    onError(error) {
      errors.push(error.message);
    },
  });

  const sameFirst = controller.updateNow();
  const sameSecond = controller.updateNow();
  assert.equal(loaderCalls.get("same"), 1, "same-signature in-flight requests must be shared");
  pending.get("same").resolve("same-result");
  await Promise.all([sameFirst, sameSecond]);
  assert.deepEqual(applied, ["same-result"], "only the latest waiter may publish shared results");

  requestKey = "old";
  const oldUpdate = controller.updateNow();
  requestKey = "new";
  const newUpdate = controller.updateNow();
  pending.get("new").resolve("new-result");
  await newUpdate;
  pending.get("old").reject(new Error("stale failure"));
  await oldUpdate;
  assert.deepEqual(applied, ["same-result", "new-result"]);
  assert.deepEqual(errors, [], "a stale rejection must not mutate the current popup state");

  requestKey = "current-failure";
  const currentFailure = controller.updateNow();
  pending.get("current-failure").reject(new Error("current failure"));
  await currentFailure;
  assert.deepEqual(errors, ["current failure"], "the current request must retain error handling");

  requestKey = "closed";
  const closedUpdate = controller.updateNow();
  controller.invalidate();
  pending.get("closed").resolve("closed-result");
  await closedUpdate;
  assert.deepEqual(
    applied,
    ["same-result", "new-result"],
    "close/invalidate must prevent late results from reopening autocomplete",
  );

  requestKey = "disposed";
  const disposedUpdate = controller.updateNow();
  controller.dispose();
  pending.get("disposed").resolve("disposed-result");
  await disposedUpdate;
  assert.deepEqual(applied, ["same-result", "new-result"]);
}

console.log("Autocomplete input controller smoke passed.");
