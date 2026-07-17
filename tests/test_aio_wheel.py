from __future__ import annotations

import shutil
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WHEEL_JS = ROOT / "web" / "js" / "aio" / "wheel.js"


class AIOWheelTests(unittest.TestCase):
    def test_preview_settings_and_canvas_wheel_ownership(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        runner = textwrap.dedent(
            r"""
            const assert = require("assert");
            const fs = require("fs");

            global.Element = class Element {
              constructor(classNames = []) {
                this.classNames = new Set(classNames);
                this.parentElement = null;
              }
              matches(selector) {
                return selector.startsWith(".") && this.classNames.has(selector.slice(1));
              }
              closest(selector) {
                for (let current = this; current; current = current.parentElement) {
                  if (current.matches(selector)) return current;
                }
                return null;
              }
              contains(candidate) {
                for (let current = candidate; current; current = current.parentElement) {
                  if (current === this) return true;
                }
                return false;
              }
            };
            global.HTMLElement = class HTMLElement extends Element {
              constructor(classNames = [], geometry = {}) {
                super(classNames);
                Object.assign(this, {
                  scrollHeight: 0,
                  clientHeight: 0,
                  scrollTop: 0,
                  scrollWidth: 0,
                  clientWidth: 0,
                  scrollLeft: 0,
                }, geometry);
                this.queries = new Map();
              }
              querySelector(selector) {
                return this.queries.get(selector) || null;
              }
            };

            let source = fs.readFileSync(process.argv[1], "utf8");
            source = source.replace(
              /export\s*\{([\s\S]*?)\};\s*$/,
              "globalThis.__aioWheelExports = {$1};",
            );
            eval(source);

            const findPanel = globalThis.__aioWheelExports.aioPanelFromWheelEvent;
            const consumePanelWheel = globalThis.__aioWheelExports.consumeAioPanelWheel;
            const makeEvent = (target, path, deltaY, deltaX = 0, deltaMode = 0) => {
              const event = {
                target,
                deltaX,
                deltaY,
                deltaMode,
                prevented: 0,
                stopped: 0,
                stoppedImmediately: 0,
                preventDefault() { this.prevented += 1; },
                stopPropagation() { this.stopped += 1; },
                stopImmediatePropagation() { this.stoppedImmediately += 1; },
              };
              if (path !== null) event.composedPath = () => path;
              return event;
            };

            const panel = new HTMLElement(["easyuse-anima-aio-node-panel"]);
            const settings = new HTMLElement(
              ["easyuse-anima-aio-node-settings-scroll"],
              { scrollHeight: 600, clientHeight: 200, scrollTop: 0 },
            );
            settings.parentElement = panel;
            const settingsTarget = new HTMLElement(["settings-target"]);
            settingsTarget.parentElement = settings;
            const previewCard = new HTMLElement(["easyuse-anima-aio-node-preview"]);
            previewCard.parentElement = panel;
            const previewTarget = new HTMLElement(["preview-target"]);
            previewTarget.parentElement = previewCard;

            // The main preview consumes wheel input without moving settings or
            // allowing the caller to forward the event to canvas zoom.
            let event = makeEvent(previewTarget, [previewTarget, previewCard, panel], 120);
            assert.strictEqual(findPanel(event), panel);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(settings.scrollTop, 0);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [1, 1, 1],
            );

            // A non-overflowing preview feed has the same ownership. Omitting
            // composedPath exercises the target.closest() fallback.
            const feed = new HTMLElement(
              ["easyuse-anima-aio-node-preview-feed"],
              { scrollWidth: 200, clientWidth: 200, scrollLeft: 0 },
            );
            feed.parentElement = previewCard;
            const feedTarget = new HTMLElement(["feed-target"]);
            feedTarget.parentElement = feed;
            event = makeEvent(feedTarget, null, 100);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(feed.scrollLeft, 0);
            assert.strictEqual(settings.scrollTop, 0);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [1, 1, 1],
            );

            // An overflowing feed translates the vertical wheel delta to X.
            feed.scrollWidth = 500;
            event = makeEvent(feedTarget, [feedTarget, feed, previewCard, panel], 100);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(feed.scrollLeft, 100);
            assert.strictEqual(settings.scrollTop, 0);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [1, 1, 1],
            );

            feed.scrollLeft = 300;
            event = makeEvent(feedTarget, [feedTarget, feed, previewCard, panel], 100);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(feed.scrollLeft, 300);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [1, 1, 1],
            );

            // Settings owns vertical wheel input only when the event target is
            // inside the settings scroll surface.
            event = makeEvent(settingsTarget, [settingsTarget, settings, panel], 120);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(settings.scrollTop, 120);

            settings.scrollTop = 400;
            event = makeEvent(settingsTarget, [settingsTarget, settings, panel], 120);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(settings.scrollTop, 400);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [1, 1, 1],
            );

            settings.scrollTop = 0;
            event = makeEvent(settingsTarget, [settingsTarget, settings, panel], 2, 0, 1);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(settings.scrollTop, 32);

            // Unrelated panel space remains unconsumed for canvas forwarding.
            settings.scrollTop = 0;
            const panelTarget = new HTMLElement(["panel-target"]);
            panelTarget.parentElement = panel;
            event = makeEvent(panelTarget, [panelTarget, panel], 120);
            assert.strictEqual(consumePanelWheel(event, panel), false);
            assert.strictEqual(settings.scrollTop, 0);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [0, 0, 0],
            );
            """
        )
        completed = subprocess.run(
            [node_bin, "-e", runner, str(WHEEL_JS)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
