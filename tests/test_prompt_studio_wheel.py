from __future__ import annotations

import shutil
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WHEEL_JS = ROOT / "web" / "js" / "prompt_studio" / "wheel.js"


class PromptStudioWheelTests(unittest.TestCase):
    def test_scrollbar_consumes_wheel_even_at_boundaries(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        runner = textwrap.dedent(
            r"""
            const assert = require("assert");
            const fs = require("fs");

            global.Element = class Element {
              closest() { return null; }
            };
            global.HTMLElement = class HTMLElement extends Element {
              constructor(scrollHeight, clientHeight, scrollTop = 0) {
                super();
                this.scrollHeight = scrollHeight;
                this.clientHeight = clientHeight;
                this.scrollTop = scrollTop;
                this.classList = { contains: (name) => name === "easyuse-anima-advanced-editor" };
              }
            };

            let source = fs.readFileSync(process.argv[1], "utf8");
            source = source.replace(
              /import\s*\{[\s\S]*?\}\s*from\s*"\.\/constants\.js";/,
              'const ADVANCED_NATIVE_CONTROL_SELECTOR = "textarea, input, select, button";',
            );
            source = source.replace(
              /export\s*\{([\s\S]*?)\};\s*$/,
              "globalThis.__wheelExports = {$1};",
            );
            eval(source);

            const consumeWheel = globalThis.__wheelExports.consumeAdvancedEditorWheel;
            const findEditor = globalThis.__wheelExports.advancedEditorFromWheelEvent;
            const makeEvent = (deltaY, deltaMode = 0) => ({
              deltaY,
              deltaMode,
              prevented: 0,
              stopped: 0,
              stoppedImmediately: 0,
              preventDefault() { this.prevented += 1; },
              stopPropagation() { this.stopped += 1; },
              stopImmediatePropagation() { this.stoppedImmediately += 1; },
            });

            const editor = new HTMLElement(500, 200, 0);
            assert.strictEqual(findEditor({ composedPath: () => [{}, editor] }), editor);
            let event = makeEvent(120);
            assert.strictEqual(consumeWheel(event, editor), true);
            assert.strictEqual(editor.scrollTop, 120);
            assert.strictEqual(event.prevented, 1);
            assert.strictEqual(event.stopped, 1);
            assert.strictEqual(event.stoppedImmediately, 1);

            editor.scrollTop = 300;
            event = makeEvent(120);
            assert.strictEqual(consumeWheel(event, editor), true);
            assert.strictEqual(editor.scrollTop, 300);
            assert.strictEqual(event.prevented, 1);
            assert.strictEqual(event.stopped, 1);
            assert.strictEqual(event.stoppedImmediately, 1);

            editor.scrollTop = 0;
            event = makeEvent(-120);
            assert.strictEqual(consumeWheel(event, editor), true);
            assert.strictEqual(editor.scrollTop, 0);
            assert.strictEqual(event.prevented, 1);
            assert.strictEqual(event.stopped, 1);
            assert.strictEqual(event.stoppedImmediately, 1);

            editor.scrollTop = 0;
            event = makeEvent(2, 1);
            assert.strictEqual(consumeWheel(event, editor), true);
            assert.strictEqual(editor.scrollTop, 32);

            const noScrollbar = new HTMLElement(200, 200, 0);
            event = makeEvent(120);
            assert.strictEqual(consumeWheel(event, noScrollbar), false);
            assert.strictEqual(noScrollbar.scrollTop, 0);
            assert.strictEqual(event.prevented, 0);
            assert.strictEqual(event.stopped, 0);
            assert.strictEqual(event.stoppedImmediately, 0);
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
