from __future__ import annotations

import shutil
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WHEEL_JS = ROOT / "web" / "js" / "aio" / "wheel.js"


class AIOWheelTests(unittest.TestCase):
    def test_scroll_owners_consume_wheel_even_at_boundaries(self):
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
            const makeEvent = (target, path, deltaY, deltaX = 0, deltaMode = 0) => ({
              target,
              deltaX,
              deltaY,
              deltaMode,
              prevented: 0,
              stopped: 0,
              stoppedImmediately: 0,
              composedPath: () => path,
              preventDefault() { this.prevented += 1; },
              stopPropagation() { this.stopped += 1; },
              stopImmediatePropagation() { this.stoppedImmediately += 1; },
            });

            const panel = new HTMLElement(["easyuse-anima-aio-node-panel"]);
            const settings = new HTMLElement(
              ["easyuse-anima-aio-node-settings-scroll"],
              { scrollHeight: 600, clientHeight: 200, scrollTop: 0 },
            );
            settings.parentElement = panel;
            panel.queries.set(".easyuse-anima-aio-node-settings-scroll", settings);
            const previewTarget = new HTMLElement(["preview-target"]);
            previewTarget.parentElement = panel;

            let event = makeEvent(previewTarget, [previewTarget, panel], 120);
            assert.strictEqual(findPanel(event), panel);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(settings.scrollTop, 120);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [1, 1, 1],
            );

            settings.scrollTop = 400;
            event = makeEvent(previewTarget, [previewTarget, panel], 120);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(settings.scrollTop, 400);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [1, 1, 1],
            );

            settings.scrollTop = 0;
            event = makeEvent(previewTarget, [previewTarget, panel], -120);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(settings.scrollTop, 0);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [1, 1, 1],
            );

            event = makeEvent(previewTarget, [previewTarget, panel], 2, 0, 1);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(settings.scrollTop, 32);

            const feed = new HTMLElement(
              ["easyuse-anima-aio-node-preview-feed"],
              { scrollWidth: 500, clientWidth: 200, scrollLeft: 0 },
            );
            feed.parentElement = panel;
            settings.scrollTop = 0;
            event = makeEvent(feed, [feed, panel], 100);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(feed.scrollLeft, 100);
            assert.strictEqual(settings.scrollTop, 0);

            feed.scrollLeft = 300;
            event = makeEvent(feed, [feed, panel], 100);
            assert.strictEqual(consumePanelWheel(event, panel), true);
            assert.strictEqual(feed.scrollLeft, 300);
            assert.deepStrictEqual(
              [event.prevented, event.stopped, event.stoppedImmediately],
              [1, 1, 1],
            );

            settings.scrollHeight = 200;
            settings.clientHeight = 200;
            event = makeEvent(previewTarget, [previewTarget, panel], 120);
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
