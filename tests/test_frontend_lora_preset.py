from __future__ import annotations

import json
import re
import shutil
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LORA_PRESET_ENTRY = ROOT / "web" / "js" / "easyuse_anima_lora_preset.js"
LORA_PRESET_PROFILE_DATA = ROOT / "web" / "js" / "lora_preset" / "profile_data.js"
LORA_PRESET_PROFILE_DATA_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_profile_data_smoke.mjs"
)
LORA_PRESET_LORA_STATE = ROOT / "web" / "js" / "lora_preset" / "lora_state.js"
LORA_PRESET_LORA_STATE_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_lora_state_smoke.mjs"
)
JSCONFIG = ROOT / "jsconfig.json"
FRONTEND_CHECK_SCRIPT = ROOT / "tools" / "check_frontend.ps1"


class LoraPresetFrontendTests(unittest.TestCase):
    def test_lora_state_module_boundary(self):
        module_source = LORA_PRESET_LORA_STATE.read_text(encoding="utf-8")
        entry_source = LORA_PRESET_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")
        expected_exports = {
            "buildLoraLookup",
            "comboEntryText",
            "hasLoraPathProblem",
            "isAnyLoraFixPending",
            "isLoraFixPending",
            "localLoraMatch",
            "loraFileKey",
            "loraFixPendingSet",
            "normalizeLoraKey",
            "normalizeLoraNameList",
            "validComboEntryText",
        }
        expected_imports = expected_exports - {
            "comboEntryText",
            "loraFileKey",
            "normalizeLoraKey",
        }

        exported_names = set(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            )
        )
        self.assertEqual(exported_names, expected_exports)

        import_match = re.search(
            r'^import\s*\{(?P<names>[^}]*)\}\s*from\s*"\./lora_preset/lora_state\.js";',
            entry_source,
            re.MULTILINE,
        )
        self.assertIsNotNone(import_match)
        imported_names = {
            name.strip().rstrip(",")
            for name in import_match.group("names").splitlines()
            if name.strip()
        }
        self.assertEqual(imported_names, expected_imports)

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            (
                r"\b(?:document|window|app|api|fetch|registerExtension|"
                r"addEventListener|removeEventListener|MutationObserver|"
                r"HTMLElement|HTMLInputElement|HTMLTextAreaElement)\b"
            ),
        )
        for name in expected_exports | {"putUniqueLoraMatch"}:
            with self.subTest(moved_declaration=name):
                self.assertNotRegex(
                    entry_source,
                    rf"\b(?:const|let|var|function|class)\s+{re.escape(name)}\b",
                )

        for adapter in (
            "comboValues",
            "loraNameValues",
            "loraResolveState",
            "setLoraLookup",
            "fetchLoraNameValues",
            "refreshLoraAvailability",
            "fixProfileLoras",
            "fixSingleLoraEntry",
        ):
            with self.subTest(entry_adapter=adapter):
                self.assertIn(f"function {adapter}(", entry_source)
        self.assertIn(
            "return localLoraMatch(normalizeLoraEntry(lora), node?.__easyuseAnimaLoraLookup);",
            entry_source,
        )
        self.assertIn("return normalizeLoraNameList(comboValues(", entry_source)
        self.assertIn("node.__easyuseAnimaLoraLookup = buildLoraLookup(values);", entry_source)

        self.assertTrue(LORA_PRESET_LORA_STATE_SMOKE.is_file())
        self.assertIn("web/js/lora_preset/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_lora_preset_lora_state_smoke.mjs"',
            frontend_check_source,
        )

    def test_lora_state_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(LORA_PRESET_LORA_STATE_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_profile_data_module_boundary(self):
        module_source = LORA_PRESET_PROFILE_DATA.read_text(encoding="utf-8")
        entry_source = LORA_PRESET_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        expected_exports = {
            "INTERNAL_WIDGET_DEFAULTS",
            "MAX_PROFILES",
            "WIDGET_INDEX",
            "emptyProfile",
            "isMeaningfulProfile",
            "normalizeLoraEntry",
            "normalizeProfileDataValue",
            "normalizeSerializedWidgets",
            "profileContent",
            "profileKey",
            "profileSavedName",
            "profileSnapshot",
            "withSavedMeta",
            "wrapProfileIndex",
        }
        exported_names = set(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            )
        )
        self.assertEqual(exported_names, expected_exports)

        import_match = re.search(
            r'^import\s*\{(?P<names>[^}]*)\}\s*from\s*"\./lora_preset/profile_data\.js";',
            entry_source,
            re.MULTILINE,
        )
        self.assertIsNotNone(import_match)
        imported_names = {
            name.strip().rstrip(",")
            for name in import_match.group("names").splitlines()
            if name.strip()
        }
        self.assertEqual(imported_names, expected_exports)

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            r"\b(?:document|window|app|api|LiteGraph|fetch|registerExtension)\b",
        )
        for name in expected_exports:
            with self.subTest(moved_declaration=name):
                self.assertNotRegex(
                    entry_source,
                    rf"\b(?:const|let|var|function|class)\s+{re.escape(name)}\b",
                )

        self.assertTrue(LORA_PRESET_PROFILE_DATA_SMOKE.is_file())
        self.assertIn("web/js/lora_preset/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_lora_preset_profile_data_smoke.mjs"',
            frontend_check_source,
        )

    def test_profile_data_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(LORA_PRESET_PROFILE_DATA_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

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
            const profileDataPath = process.argv[2];
            const loraStatePath = process.argv[3];
            let profileDataSource = fs.readFileSync(profileDataPath, "utf8");
            profileDataSource = profileDataSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let loraStateSource = fs.readFileSync(loraStatePath, "utf8");
            loraStateSource = loraStateSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let source = fs.readFileSync(sourcePath, "utf8");
            source = source.replace(/^import[\s\S]*?;\r?\n/gm, "");
            source = `${profileDataSource}\n${loraStateSource}\n${source}`;
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
                prompt() { globalThis.__promptCount = (globalThis.__promptCount || 0) + 1; },
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
              LORA_PRESET_SETTINGS.strengthButtonStep = 0.05;
              assert.strictEqual(row.mouse({ type: "pointerdown", button: 0 }, [282, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 1.05);
            }

            {
              const node = makeNode();
              const row = makeRow();
              LORA_PRESET_SETTINGS.strengthButtonStep = 0.05;
              assert.strictEqual(row.mouse({ type: "pointerdown", button: 0 }, [234, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 0.95);
            }

            {
              const node = makeNode();
              const row = makeRow();
              applyLoraPresetSettings({
                "lora_preset.strength_drag_step": "0.01",
                "lora_preset.strength_drag_pixels": "1",
              });
              assert.strictEqual(row.mouse({ type: "pointerdown", button: 0 }, [250, 10], node), true);
              assert.strictEqual(row.mouse({ type: "pointermove" }, [252, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 1.02);
            }

            {
              const node = makeNode();
              const row = makeRow();
              applyLoraPresetSettings({
                "lora_preset.strength_drag_step": "0.05",
                "lora_preset.strength_drag_pixels": "8",
              });
              assert.strictEqual(row.mouse({ type: "pointerdown", button: 0 }, [250, 10], node), true);
              assert.strictEqual(row.mouse({ type: "pointermove" }, [257, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 1);
              assert.strictEqual(row.mouse({ type: "pointermove" }, [258, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 1.05);
            }

            {
              const node = makeNode();
              const row = makeRow();
              applyLoraPresetSettings({
                "lora_preset.strength_button_step": "0.02",
                "lora_preset.strength_drag_step": "0.05",
                "lora_preset.strength_drag_pixels": "8",
              });
              assert.strictEqual(row.mouse({ type: "pointerdown", button: 0 }, [282, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 1.02);
            }

            {
              const node = makeNode();
              const row = makeRow();
              context.__promptCount = 0;
              applyLoraPresetSettings({
                "lora_preset.strength_button_step": "0.05",
                "lora_preset.strength_drag_step": "0.05",
                "lora_preset.strength_drag_pixels": "8",
              });
              assert.strictEqual(row.mouse({ type: "pointerdown", button: 0 }, [250, 10], node), true);
              assert.strictEqual(row.mouse({ type: "pointermove" }, [282, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 1.2);
              assert.strictEqual(row.mouse({ type: "pointerup" }, [282, 10], node), true);
              assert.strictEqual(loras(node)[0].strength, 1.2);
              assert.strictEqual(context.__promptCount, 0);
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
              applyLoraPresetSettings({
                "lora_preset.strength_button_step": "0.2",
                "lora_preset.strength_drag_step": "0.025",
                "lora_preset.strength_drag_pixels": "12",
              });
              assert.strictEqual(LORA_PRESET_SETTINGS.strengthButtonStep, 0.2);
              assert.strictEqual(LORA_PRESET_SETTINGS.strengthDragStep, 0.025);
              assert.strictEqual(LORA_PRESET_SETTINGS.strengthDragPixels, 12);
            }
            """
        )

        completed = subprocess.run(
            [
                node_bin,
                "-e",
                runner,
                str(LORA_PRESET_ENTRY),
                str(LORA_PRESET_PROFILE_DATA),
                str(LORA_PRESET_LORA_STATE),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())


if __name__ == "__main__":
    unittest.main()
