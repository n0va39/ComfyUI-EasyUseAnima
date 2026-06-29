from __future__ import annotations

import shutil
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LoraPresetFrontendTests(unittest.TestCase):
    def test_lora_row_non_toggle_controls_do_not_throw(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        runner = textwrap.dedent(
            r"""
            const assert = require("assert");
            const fs = require("fs");
            const vm = require("vm");

            const sourcePath = process.argv[1];
            let source = fs.readFileSync(sourcePath, "utf8");
            source = source.replace(/^import\s+.*;\r?\n/gm, "");
            source += "\nglobalThis.__loraPresetTest = { LoraRowWidget, LORA_PRESET_SETTINGS, applyLoraPresetSettings, loraMenuElementValue, loraMenuItems };\n";

            class StubElement {
              constructor(tagName = "div") {
                this.tagName = tagName;
                this.children = [];
                this.className = "";
                this.style = {};
                this.dataset = {};
                this.value = "";
                this.tabIndex = 0;
              }
              appendChild(child) { this.children.push(child); return child; }
              remove() {}
              addEventListener() {}
              dispatchEvent() {}
              focus() {}
              querySelector() { return null; }
              querySelectorAll() { return []; }
              getBoundingClientRect() { return { left: 0, top: 0, width: 260, height: 120 }; }
              set textContent(value) { this.__textContent = value; }
              get textContent() { return this.__textContent || ""; }
            }

            const context = {
              console,
              setTimeout,
              clearTimeout,
              Path2D: class { constructor(path) { this.path = path; } },
              Event: class { constructor(type, options = {}) { this.type = type; Object.assign(this, options); } },
              MouseEvent: class { constructor(type, options = {}) { this.type = type; Object.assign(this, options); } },
              HTMLInputElement: class {},
              HTMLTextAreaElement: class {},
              MutationObserver: class { constructor() {} observe() {} disconnect() {} },
              LiteGraph: {
                WIDGET_TEXT_COLOR: "#ddd",
                WIDGET_BGCOLOR: "#222",
                WIDGET_OUTLINE_COLOR: "#555",
                ContextMenu: function ContextMenu(items, options) {
                  globalThis.__lastContextMenu = { items, options };
                },
              },
              api: {
                fetchApi: async () => ({ ok: true, json: async () => ({ loras: [] }) }),
              },
              easyuseAnimaText: (maps, key) => maps.en[key] || key,
              easyuseAnimaWatchLocale: () => {},
            };
            context.globalThis = context;
            context.self = context;
            context.window = {
              innerWidth: 1920,
              innerHeight: 1080,
              addEventListener() {},
              requestAnimationFrame(callback) { return callback(); },
              alert() {},
              confirm() { return true; },
              prompt() { return null; },
            };
            context.document = {
              body: new StubElement("body"),
              head: new StubElement("head"),
              createElement: (tagName) => new StubElement(tagName),
              querySelector: () => null,
              querySelectorAll: () => [],
              addEventListener() {},
            };
            context.document.body.getBoundingClientRect = () => ({ left: 0, top: 0, width: 1920, height: 1080 });
            context.app = {
              canvas: {
                editor_alpha: 1,
                ds: { scale: 1, offset: [0, 0] },
                canvas: { getBoundingClientRect: () => ({ left: 0, top: 0, width: 1920, height: 1080 }) },
                prompt() {},
              },
              graph: { _nodes: [] },
              registerExtension(extension) { this.__extension = extension; },
              queuePrompt() {},
            };

            vm.createContext(context);
            vm.runInContext(source, context, { filename: sourcePath });

            const {
              LoraRowWidget,
              LORA_PRESET_SETTINGS,
              applyLoraPresetSettings,
              loraMenuElementValue,
              loraMenuItems,
            } = context.__loraPresetTest;

            function widget(name, value) {
              return { name, value };
            }

            function makeNode() {
              return {
                comfyClass: "EasyUseAnimaLoraPreset",
                size: [520, 220],
                widgets: [
                  widget("style_prompt", ""),
                  widget("profile_index", 1),
                  widget("profile_count", "1"),
                  widget("lora_name", "None"),
                  widget("loras", JSON.stringify([{ name: "style/foo.safetensors", on: true, strength: 1, strengthTwo: null }])),
                  widget("profile_data", "{}"),
                ],
                setDirtyCanvas() {},
              };
            }

            function makeRow() {
              const row = new LoraRowWidget(0);
              row.hitAreas = {
                toggle: [0, 0, 20, 20],
                fix: null,
                lora: [40, 0, 120, 20],
                menu: [170, 0, 20, 20],
                info: [200, 0, 20, 20],
                dec: [230, 0, 9, 20],
                value: [242, 0, 32, 20],
                inc: [278, 0, 9, 20],
                strengthAny: [230, 0, 57, 20],
              };
              return row;
            }

            function loras(node) {
              return JSON.parse(node.widgets.find((item) => item.name === "loras").value);
            }

            {
              const node = makeNode();
              const row = makeRow();
              assert.strictEqual(row.mouse({ type: "pointerdown", button: 0 }, [282, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 1.05);
            }

            {
              const node = makeNode();
              const row = makeRow();
              assert.strictEqual(row.mouse({ type: "pointerdown", button: 0 }, [234, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 0.95);
            }

            {
              const node = makeNode();
              const row = makeRow();
              LORA_PRESET_SETTINGS.strengthDragStep = 0.01;
              assert.strictEqual(row.mouse({ type: "pointerdown", button: 0 }, [250, 10], node), true);
              assert.strictEqual(row.mouse({ type: "pointermove", deltaX: 2 }, [252, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 1.02);
            }

            {
              const items = loraMenuItems(["style/foo.safetensors", "style/x<y.safetensors"]);
              assert.strictEqual(items[0].content, "style/foo.safetensors");
              assert.strictEqual(items[0].value, "style/foo.safetensors");
              assert.strictEqual(items[1].content, "style/x&lt;y.safetensors");

              const badDomItem = {
                dataset: {},
                textContent: "[object Object]",
                value: null,
                __value: null,
                getAttribute(name) {
                  return name === "data-value" ? "[object Object]" : null;
                },
              };
              assert.strictEqual(
                loraMenuElementValue(badDomItem, "fixed/path.safetensors"),
                "fixed/path.safetensors",
              );

              applyLoraPresetSettings({ "lora_preset.menu_mode": "list" });
              assert.strictEqual(LORA_PRESET_SETTINGS.menuMode, "list");
              applyLoraPresetSettings({ "lora_preset.menu_mode": "bad" });
              assert.strictEqual(LORA_PRESET_SETTINGS.menuMode, "tree");
            }
            """
        )

        completed = subprocess.run(
            [node_bin, "-e", runner, str(ROOT / "web" / "js" / "easyuse_anima_lora_preset.js")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())


if __name__ == "__main__":
    unittest.main()
