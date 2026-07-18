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
LORA_PRESET_API_CLIENT = ROOT / "web" / "js" / "lora_preset" / "api_client.js"
LORA_PRESET_API_CLIENT_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_api_client_smoke.mjs"
)
LORA_PRESET_CANVAS_WIDGETS = (
    ROOT / "web" / "js" / "lora_preset" / "canvas_widgets.js"
)
LORA_PRESET_CANVAS_WIDGETS_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_canvas_widgets_smoke.mjs"
)
LORA_PRESET_ENTRY_LIFECYCLE = (
    ROOT / "web" / "js" / "lora_preset" / "entry_lifecycle.js"
)
LORA_PRESET_ENTRY_LIFECYCLE_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_entry_lifecycle_smoke.mjs"
)
LORA_PRESET_PREVIEW_LIFECYCLE = (
    ROOT / "web" / "js" / "lora_preset" / "preview_lifecycle.js"
)
LORA_PRESET_PREVIEW_LIFECYCLE_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_preview_lifecycle_smoke.mjs"
)
LORA_PRESET_MENU_LIFECYCLE = (
    ROOT / "web" / "js" / "lora_preset" / "menu_lifecycle.js"
)
LORA_PRESET_MENU_LIFECYCLE_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_menu_lifecycle_smoke.mjs"
)
LORA_PRESET_NODE_RUNTIME = (
    ROOT / "web" / "js" / "lora_preset" / "node_runtime.js"
)
LORA_PRESET_NODE_RUNTIME_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_node_runtime_smoke.mjs"
)
LORA_PRESET_PROFILE_DATA = ROOT / "web" / "js" / "lora_preset" / "profile_data.js"
LORA_PRESET_PROFILE_DATA_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_profile_data_smoke.mjs"
)
LORA_PRESET_LORA_STATE = ROOT / "web" / "js" / "lora_preset" / "lora_state.js"
LORA_PRESET_LORA_STATE_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_lora_state_smoke.mjs"
)
LORA_PRESET_PROFILE_MUTATIONS = (
    ROOT / "web" / "js" / "lora_preset" / "profile_mutations.js"
)
LORA_PRESET_SAVE_SYNC = ROOT / "web" / "js" / "lora_preset" / "save_sync.js"
LORA_PRESET_PROFILE_MUTATIONS_SMOKE = (
    ROOT / "tests" / "frontend_lora_preset_profile_mutations_smoke.mjs"
)
JSCONFIG = ROOT / "jsconfig.json"
FRONTEND_CHECK_SCRIPT = ROOT / "tools" / "check_frontend.ps1"


class LoraPresetFrontendTests(unittest.TestCase):
    def test_node_runtime_module_boundary(self):
        module_source = LORA_PRESET_NODE_RUNTIME.read_text(encoding="utf-8")
        entry_source = LORA_PRESET_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createLoraPresetNodeRuntime"],
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            (
                r"\b(?:document|window|app|api|LiteGraph|registerExtension|"
                r"MutationObserver)\b"
            ),
        )
        self.assertIn(
            'import { createLoraPresetNodeRuntime } from '
            '"./lora_preset/node_runtime.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+loraPresetNodeRuntime\s*=\s*"
            r"createLoraPresetNodeRuntime"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        dependency_entries = {
            line.strip().rstrip(",")
            for line in factory_match.group("dependencies").splitlines()
            if line.strip()
        }
        self.assertEqual(
            dependency_entries,
            {
                "nodeTypeName: NODE_TYPE",
                "internalWidgetDefaults: INTERNAL_WIDGET_DEFAULTS",
                "widgetIndex: WIDGET_INDEX",
                "findWidget",
                "findInputEl",
                "widgetValue",
                "ensureWidgetValue",
                "resetInternalLoraSelector",
                "normalizeSerializedWidgets",
                "profileCount",
                "selectedProfileIndex",
                "activeProfileIndex",
                "wrapProfileIndex",
                "setProfileIndex",
                "lorasWidgetValue",
                "saveProfile",
                "saveCurrentProfile",
                "loadProfile",
                "scrollProfileBarTo",
                "refreshLoraAvailability",
                "canvasWidgets: loraCanvasWidgets",
                "enforceNodeLayout",
                "requestAnimationFrame: (callback) => window.requestAnimationFrame(callback)",
            },
        )
        for moved_declaration in (
            "hideInternalWidget",
            "restoreInternalWidgetsForConfigure",
            "finalizeInternalWidgets",
            "ensureLoraStackInput",
            "wrapWidgetCallback",
            "applyExecutedProfile",
            "initializeNode",
        ):
            with self.subTest(moved_declaration=moved_declaration):
                self.assertNotRegex(
                    entry_source,
                    rf"\bfunction\s+{re.escape(moved_declaration)}\b",
                )
                self.assertRegex(
                    module_source,
                    rf"\bfunction\s+{re.escape(moved_declaration)}\b",
                )
        self.assertIn("nodeRuntime: loraPresetNodeRuntime,", entry_source)
        self.assertTrue(LORA_PRESET_NODE_RUNTIME_SMOKE.is_file())
        self.assertIn("web/js/lora_preset/**/*.js", config["include"])

    def test_node_runtime_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(LORA_PRESET_NODE_RUNTIME_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_api_client_module_boundary(self):
        module_source = LORA_PRESET_API_CLIENT.read_text(encoding="utf-8")
        entry_source = LORA_PRESET_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createLoraPresetApiClient"],
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            (
                r"\b(?:document|window|app|api|fetch|LiteGraph|registerExtension|"
                r"addEventListener|removeEventListener|MutationObserver)\b"
            ),
        )

        self.assertIn(
            'import { createLoraPresetApiClient } from '
            '"./lora_preset/api_client.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+loraPresetApi\s*=\s*"
            r"createLoraPresetApiClient"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        dependency_entries = {
            line.strip().rstrip(",")
            for line in factory_match.group("dependencies").splitlines()
            if line.strip()
        }
        self.assertEqual(
            dependency_entries,
            {
                "fetchJson",
                "encodeURIComponent: encodeRFC3986URIComponent",
            },
        )

        self.assertNotIn("/easyuse_anima/lora_profiles", entry_source)
        self.assertNotIn('"/easyuse_anima/loras"', entry_source)
        self.assertEqual(
            len(
                re.findall(
                    r'fetchJson\("/easyuse_anima/lora_profiles"\)',
                    module_source,
                )
            ),
            1,
        )
        for route in (
            "/easyuse_anima/lora_profiles/load?name=",
            "/easyuse_anima/lora_profiles/save",
            "/easyuse_anima/lora_profiles/fix",
            "/easyuse_anima/loras",
        ):
            with self.subTest(route=route):
                self.assertEqual(module_source.count(route), 1)

        self.assertEqual(entry_source.count("loraPresetApi.listProfiles()"), 1)
        self.assertEqual(entry_source.count("loraPresetApi.loadProfile(name)"), 0)
        self.assertEqual(entry_source.count("loraPresetApi.saveProfile("), 0)
        self.assertEqual(entry_source.count("loraPresetApi.fixProfile("), 2)
        self.assertEqual(entry_source.count("loraPresetApi.listLoras()"), 1)
        self.assertIn(
            "loraPresetApi.fixProfile(fullProfilePayload(node))",
            entry_source,
        )
        self.assertIn("async function fetchJson(url, options = {})", entry_source)
        self.assertIn("api.fetchApi(requestUrl, requestOptions)", entry_source)
        self.assertIn("easyuseAnimaFetchJson(url, { ...options, fetcher })", entry_source)

        self.assertTrue(LORA_PRESET_API_CLIENT_SMOKE.is_file())
        self.assertIn("web/js/lora_preset/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_lora_preset_api_client_smoke.mjs"',
            frontend_check_source,
        )

    def test_api_client_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(LORA_PRESET_API_CLIENT_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_canvas_widgets_module_boundary(self):
        module_source = LORA_PRESET_CANVAS_WIDGETS.read_text(encoding="utf-8")
        entry_source = LORA_PRESET_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createLoraPresetCanvasWidgets"],
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            (
                r"\b(?:document|window|app|api|fetch|registerExtension|"
                r"MutationObserver)\b"
            ),
        )
        self.assertIn(
            'import { createLoraPresetCanvasWidgets } from '
            '"./lora_preset/canvas_widgets.js";',
            entry_source,
        )

        factory_match = re.search(
            r"loraCanvasWidgets\s*=\s*"
            r"createLoraPresetCanvasWidgets"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        dependency_entries = {
            line.strip().rstrip(",")
            for line in factory_match.group("dependencies").splitlines()
            if line.strip()
        }
        self.assertEqual(
            dependency_entries,
            {
                "getCanvas: () => app.canvas",
                "getLiteGraph: () => LiteGraph",
                "getSettings: () => LORA_PRESET_SETTINGS",
                "text: lpText",
                "formatText: lpFormat",
                "normalizeLoraEntry",
                "lorasWidgetValue",
                "mutateLoras",
                "updateLoraEntry",
                "loraResolveState",
                "hasLoraPathProblem",
                "isAnyLoraFixPending",
                "isLoraFixPending",
                "loraDisplayName",
                "previewLifecycle: loraPreviewLifecycle",
                "openLoraMenu",
                "openLoraEntryMenu",
                "addLoraEntry",
                "fixSingleLoraEntry",
                "profileCount",
                "activeProfileIndex",
                "profileSaveStatus",
                "addProfile",
                "deleteProfile",
                "saveProfileSet",
                "openProfileLoadMenu",
                "fixProfileLoras",
                "switchProfile",
                "nodePosToClient",
                "getActiveProfileWheelTarget: () => loraPresetEntryLifecycle?.getActiveProfileWheelTarget() || null",
                "setActiveProfileWheelTarget: (target) => loraPresetEntryLifecycle?.setActiveProfileWheelTarget(target)",
                "enforceNodeLayout",
            },
        )

        moved_declarations = {
            "MIN_NODE_WIDTH",
            "PROFILE_CONTROLS_HEIGHT",
            "PROFILE_ROW_HEIGHT",
            "PROFILE_LIST_PADDING",
            "PROFILE_VISIBLE_ROWS",
            "LORA_HEADER_HEIGHT",
            "LORA_ROW_HEIGHT",
            "LORA_ADD_HEIGHT",
            "roundStrength",
            "clearLoraStrengthDrag",
            "beginLoraStrengthDrag",
            "handleLoraStrengthDrag",
            "fitCanvasText",
            "roundedRect",
            "pointInArea",
            "drawToggle",
            "drawNumberPart",
            "nodeWidgetWidth",
            "ProfileBarWidget",
            "LoraHeaderWidget",
            "LoraRowWidget",
            "AddLoraWidget",
            "renderProfileBar",
            "renderLoraWidgets",
            "ensureProfileBar",
        }
        for name in moved_declarations:
            with self.subTest(moved_declaration=name):
                self.assertNotRegex(
                    entry_source,
                    rf"\b(?:const|let|var|function|class)\s+{re.escape(name)}\b",
                )

        for class_name in (
            "ProfileBarWidget",
            "LoraHeaderWidget",
            "LoraRowWidget",
            "AddLoraWidget",
        ):
            with self.subTest(canvas_widget_class=class_name):
                self.assertIn(f"class {class_name}", module_source)
        self.assertEqual(module_source.count("this.serialize = false;"), 4)
        self.assertEqual(
            module_source.count('this.options = { serialize: false };'),
            4,
        )
        self.assertIn(
            'import { createLoraPresetEntryLifecycle } from '
            '"./lora_preset/entry_lifecycle.js";',
            entry_source,
        )
        self.assertIn(
            "loraPresetEntryLifecycle = createLoraPresetEntryLifecycle({",
            entry_source,
        )
        self.assertIn("app.registerExtension(loraPresetEntryLifecycle.extension);", entry_source)
        self.assertNotIn('document.addEventListener("wheel"', entry_source)
        self.assertNotIn("function scrollProfileListFromWheel(", entry_source)
        self.assertIn("let loraCanvasWidgets;", entry_source)
        self.assertIn("getCanvasWidgets: () => loraCanvasWidgets", entry_source)
        self.assertTrue(LORA_PRESET_CANVAS_WIDGETS_SMOKE.is_file())
        self.assertIn("web/js/lora_preset/**/*.js", config["include"])

    def test_canvas_widgets_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(LORA_PRESET_CANVAS_WIDGETS_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_entry_lifecycle_module_boundary(self):
        module_source = LORA_PRESET_ENTRY_LIFECYCLE.read_text(encoding="utf-8")
        entry_source = LORA_PRESET_ENTRY.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createLoraPresetEntryLifecycle"],
        )
        self.assertNotRegex(module_source, re.compile(r"^\s*import\b", re.MULTILINE))
        self.assertNotIn("registerExtension(", module_source)
        self.assertIn('listen(hostDocument, "wheel", scrollProfileListFromWheel, { capture: true, passive: false });', module_source)
        self.assertIn("target.removeEventListener(type, listener, options);", module_source)
        self.assertIn("previousOwner.dispose?.();", module_source)
        self.assertIn("runCleanup(() => menuLifecycle.dispose?.());", module_source)
        self.assertIn("loraPresetEntryLifecycle = createLoraPresetEntryLifecycle({", entry_source)
        self.assertIn("app.registerExtension(loraPresetEntryLifecycle.extension);", entry_source)
        self.assertTrue(LORA_PRESET_ENTRY_LIFECYCLE_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_lora_preset_entry_lifecycle_smoke.mjs"',
            frontend_check_source,
        )

    def test_entry_lifecycle_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(LORA_PRESET_ENTRY_LIFECYCLE_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_preview_lifecycle_module_boundary(self):
        module_source = LORA_PRESET_PREVIEW_LIFECYCLE.read_text(encoding="utf-8")
        entry_source = LORA_PRESET_ENTRY.read_text(encoding="utf-8")
        canvas_widgets_source = LORA_PRESET_CANVAS_WIDGETS.read_text(
            encoding="utf-8"
        )
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            set(
                re.findall(
                    r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                    module_source,
                    re.MULTILINE,
                )
            ),
            {
                "createLoraPresetPreviewLifecycle",
                "loraPreviewPosition",
            },
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            r"\b(?:app|api|LiteGraph|registerExtension|MutationObserver)\b",
        )
        self.assertIn(
            'import { createLoraPresetPreviewLifecycle } from '
            '"./lora_preset/preview_lifecycle.js";',
            entry_source,
        )

        factory_match = re.search(
            r"const\s+loraPreviewLifecycle\s*=\s*"
            r"createLoraPresetPreviewLifecycle"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        dependency_entries = {
            line.strip().rstrip(",")
            for line in factory_match.group("dependencies").splitlines()
            if line.strip()
        }
        self.assertEqual(
            dependency_entries,
            {
                "document",
                "encodeURIComponent: encodeRFC3986URIComponent",
                "previewSize: PREVIEW_SIZE",
            },
        )

        for moved_name in (
            "missingPreviewNames",
            "positionPreview",
            "showPreview",
            "hidePreview",
        ):
            with self.subTest(moved_declaration=moved_name):
                self.assertNotRegex(
                    entry_source,
                    rf"\b(?:const|let|var|function|class)\s+{moved_name}\b",
                )
        self.assertEqual(entry_source.count("loraPreviewLifecycle.showPreview"), 0)
        self.assertEqual(entry_source.count("loraPreviewLifecycle.hidePreview"), 0)
        self.assertIn("previewLifecycle: loraPreviewLifecycle,", entry_source)
        self.assertEqual(canvas_widgets_source.count("previewLifecycle.showPreview"), 2)
        self.assertEqual(canvas_widgets_source.count("previewLifecycle.hidePreview"), 3)
        self.assertEqual(
            entry_source.count("loraPreviewLifecycle.forgetMissingPreview"),
            1,
        )
        self.assertTrue(LORA_PRESET_PREVIEW_LIFECYCLE_SMOKE.is_file())
        self.assertIn("web/js/lora_preset/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_lora_preset_preview_lifecycle_smoke.mjs"',
            frontend_check_source,
        )

    def test_preview_lifecycle_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(LORA_PRESET_PREVIEW_LIFECYCLE_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_menu_lifecycle_module_boundary(self):
        module_source = LORA_PRESET_MENU_LIFECYCLE.read_text(encoding="utf-8")
        entry_source = LORA_PRESET_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createLoraPresetMenuLifecycle"],
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            r"\b(?:app|api|registerExtension)\b",
        )
        self.assertIn(
            'import { createLoraPresetMenuLifecycle } from '
            '"./lora_preset/menu_lifecycle.js";',
            entry_source,
        )

        factory_match = re.search(
            r"const\s+loraMenuLifecycle\s*=\s*"
            r"createLoraPresetMenuLifecycle"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        dependency_entries = {
            line.strip().rstrip(",")
            for line in factory_match.group("dependencies").splitlines()
            if line.strip()
        }
        self.assertEqual(
            dependency_entries,
            {
                "document",
                "window",
                "MutationObserver",
                "createElement: createEl",
                "validComboEntryText",
                "previewLifecycle: loraPreviewLifecycle",
                "positionMenu",
                "text: lpText",
                "getMenuMode: () => LORA_PRESET_SETTINGS.menuMode",
                "getCurrentNode: () => app.canvas?.current_node",
                "nodeType: NODE_TYPE",
                "previewSize: PREVIEW_SIZE",
            },
        )

        for moved_name in (
            "normalizeSearchText",
            "escapeHtml",
            "loraMenuItems",
            "ensureLoraMenuSearch",
            "applyLoraMenuSearch",
            "loraMenuElementValue",
            "addLoraMenuEntryHandlers",
            "normalizeLoraMenuEntries",
            "updateLoraMenuList",
            "updateLoraMenuTree",
            "updateLoraMenu",
        ):
            with self.subTest(moved_declaration=moved_name):
                self.assertNotRegex(
                    entry_source,
                    rf"\b(?:const|let|var|function|class)\s+{moved_name}\b",
                )

        self.assertEqual(
            entry_source.count("loraMenuLifecycle.createMenuItems(values)"),
            1,
        )
        self.assertEqual(
            entry_source.count(
                "loraMenuLifecycle.activateMenu(node, clientPoint, menuItems)"
            ),
            1,
        )
        self.assertIn("menuLifecycle: loraMenuLifecycle,", entry_source)
        self.assertNotIn("new MutationObserver", entry_source)
        self.assertNotIn("easyuse-anima-lora-search {", entry_source)
        self.assertIn("new MutationObserver", module_source)
        self.assertIn("easyuse-anima-lora-search {", module_source)

        self.assertTrue(LORA_PRESET_MENU_LIFECYCLE_SMOKE.is_file())
        self.assertIn("web/js/lora_preset/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_lora_preset_menu_lifecycle_smoke.mjs"',
            frontend_check_source,
        )

    def test_menu_lifecycle_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(LORA_PRESET_MENU_LIFECYCLE_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

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
        self.assertEqual(
            imported_names,
            {
                "INTERNAL_WIDGET_DEFAULTS",
                "MAX_PROFILES",
                "WIDGET_INDEX",
                "normalizeLoraEntry",
                "normalizeProfileDataValue",
                "normalizeSerializedWidgets",
                "profileKey",
                "profileSavedName",
                "wrapProfileIndex",
            },
        )

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

    def test_profile_mutations_and_save_sync_module_boundary(self):
        mutations_source = LORA_PRESET_PROFILE_MUTATIONS.read_text(encoding="utf-8")
        save_sync_source = LORA_PRESET_SAVE_SYNC.read_text(encoding="utf-8")
        entry_source = LORA_PRESET_ENTRY.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(mutations_source.splitlines()[0], "import {")
        self.assertEqual(save_sync_source.splitlines()[0], "/** Installs the graph-save and queue-preparation synchronization hooks. */")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                mutations_source,
                re.MULTILINE,
            ),
            ["createLoraPresetProfileMutations"],
        )
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                save_sync_source,
                re.MULTILINE,
            ),
            ["createLoraPresetSaveSync"],
        )
        self.assertIn(
            'import { createLoraPresetProfileMutations } from '
            '"./lora_preset/profile_mutations.js";',
            entry_source,
        )
        self.assertIn(
            'import { createLoraPresetSaveSync } from "./lora_preset/save_sync.js";',
            entry_source,
        )
        self.assertIn("const loraProfileMutations = createLoraPresetProfileMutations({", entry_source)
        self.assertIn("const loraPresetSaveSync = createLoraPresetSaveSync({", entry_source)
        self.assertIn("saveSync: loraPresetSaveSync,", entry_source)
        self.assertEqual(entry_source.count('"profile.overwriteConfirm":'), 4)
        self.assertTrue(LORA_PRESET_PROFILE_MUTATIONS_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_lora_preset_profile_mutations_smoke.mjs"',
            frontend_check_source,
        )

    def test_profile_mutations_and_save_sync_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(LORA_PRESET_PROFILE_MUTATIONS_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_lora_row_controls_and_api_wiring_runtime(self):
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
            const apiClientPath = process.argv[4];
            const previewLifecyclePath = process.argv[5];
            const menuLifecyclePath = process.argv[6];
            const canvasWidgetsPath = process.argv[7];
            const nodeRuntimePath = process.argv[8];
            const profileMutationsPath = process.argv[9];
            const saveSyncPath = process.argv[10];
            const entryLifecyclePath = process.argv[11];
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
            let apiClientSource = fs.readFileSync(apiClientPath, "utf8");
            apiClientSource = apiClientSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let previewLifecycleSource = fs.readFileSync(previewLifecyclePath, "utf8");
            previewLifecycleSource = previewLifecycleSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let menuLifecycleSource = fs.readFileSync(menuLifecyclePath, "utf8");
            menuLifecycleSource = menuLifecycleSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let canvasWidgetsSource = fs.readFileSync(canvasWidgetsPath, "utf8");
            canvasWidgetsSource = canvasWidgetsSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let nodeRuntimeSource = fs.readFileSync(nodeRuntimePath, "utf8");
            nodeRuntimeSource = nodeRuntimeSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let profileMutationsSource = fs.readFileSync(profileMutationsPath, "utf8");
            profileMutationsSource = profileMutationsSource.replace(/^import[\s\S]*?;\r?\n/gm, "");
            profileMutationsSource = profileMutationsSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let saveSyncSource = fs.readFileSync(saveSyncPath, "utf8");
            saveSyncSource = saveSyncSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let entryLifecycleSource = fs.readFileSync(entryLifecyclePath, "utf8");
            entryLifecycleSource = entryLifecycleSource.replace(
              /^export\s+(?=(?:const|function|class)\b)/gm,
              "",
            );
            let source = fs.readFileSync(sourcePath, "utf8");
            source = source.replace(/^import[\s\S]*?;\r?\n/gm, "");
            source = `${profileDataSource}\n${loraStateSource}\n${apiClientSource}\n${previewLifecycleSource}\n${menuLifecycleSource}\n${canvasWidgetsSource}\n${nodeRuntimeSource}\n${profileMutationsSource}\n${saveSyncSource}\n${entryLifecycleSource}\n${source}`;
            source += "\nglobalThis.__loraPresetTest = { loraCanvasWidgets, LORA_PRESET_SETTINGS, applyLoraPresetSettings, loraPresetApi, loraPreviewLifecycle, loraMenuLifecycle, saveProfileSet };\n";

            const mutationObservers = [];
            class StubMutationObserver {
              constructor(callback) {
                this.callback = callback;
                mutationObservers.push(this);
              }
              observe(target, options) {
                this.target = target;
                this.options = options;
              }
              disconnect() {}
            }

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
              MutationObserver: StubMutationObserver,
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
              encodeRFC3986URIComponent: (value) => String(value),
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
              loraCanvasWidgets,
              LORA_PRESET_SETTINGS,
              applyLoraPresetSettings,
              loraPresetApi,
              loraPreviewLifecycle,
              loraMenuLifecycle,
              saveProfileSet,
            } = context.__loraPresetTest;
            const { LoraRowWidget } = loraCanvasWidgets;

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
              const shown = [];
              let hidden = 0;
              const originalShowPreview = loraPreviewLifecycle.showPreview;
              const originalHidePreview = loraPreviewLifecycle.hidePreview;
              loraPreviewLifecycle.showPreview = (name, event) => {
                shown.push({ name, event });
              };
              loraPreviewLifecycle.hidePreview = () => {
                hidden += 1;
              };

              const hoverEvent = { type: "pointermove", clientX: 205, clientY: 10 };
              assert.strictEqual(row.mouse(hoverEvent, [205, 10], node), false);
              assert.strictEqual(shown.length, 1);
              assert.strictEqual(shown[0].name, "style/foo.safetensors");
              assert.strictEqual(shown[0].event, hoverEvent);
              assert.strictEqual(row.mouse({ type: "pointermove" }, [10, 10], node), false);
              assert.strictEqual(hidden, 1);
              assert.strictEqual(row.mouse({ type: "pointerout" }, [10, 10], node), false);
              assert.strictEqual(hidden, 2);

              loraPreviewLifecycle.showPreview = originalShowPreview;
              loraPreviewLifecycle.hidePreview = originalHidePreview;
            }

            {
              const node = makeNode();
              context.app.canvas.current_node = node;
              let hidden = 0;
              const originalHidePreview = loraPreviewLifecycle.hidePreview;
              loraPreviewLifecycle.hidePreview = () => {
                hidden += 1;
              };

              context.app.__extension.init();
              assert.strictEqual(mutationObservers.length, 1);
              assert.ok(loraMenuLifecycle);
              const removedMenu = {
                classList: {
                  contains(className) {
                    return className === "litecontextmenu"
                      || className === "easyuse-anima-lora-menu";
                  },
                },
              };
              mutationObservers[0].callback([{
                removedNodes: [removedMenu],
                addedNodes: [],
              }]);
              assert.strictEqual(hidden, 1);

              loraPreviewLifecycle.hidePreview = originalHidePreview;
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

            (async () => {
              const node = makeNode();
              let saveCall = null;
              loraPresetApi.saveProfile = async (name, payload, overwrite) => {
                saveCall = { name, payload, overwrite };
                return { profile: { name } };
              };
              context.window.prompt = () => "  Demo  ";

              await saveProfileSet(node);

              assert.ok(saveCall, "saveProfileSet must call the API client");
              assert.strictEqual(saveCall.name, "Demo");
              assert.strictEqual(saveCall.overwrite, false);
              const payload = JSON.parse(JSON.stringify(saveCall.payload));
              assert.strictEqual(payload.profile_count, 1);
              assert.strictEqual(payload.profile_index, 1);
              assert.strictEqual(payload.profile_data["1"].style_prompt, "");
              assert.strictEqual(
                payload.profile_data["1"].loras[0].name,
                "style/foo.safetensors",
              );
            })().catch((error) => {
              console.error(error);
              process.exitCode = 1;
            });
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
                str(LORA_PRESET_API_CLIENT),
                str(LORA_PRESET_PREVIEW_LIFECYCLE),
                str(LORA_PRESET_MENU_LIFECYCLE),
                str(LORA_PRESET_CANVAS_WIDGETS),
                str(LORA_PRESET_NODE_RUNTIME),
                str(LORA_PRESET_PROFILE_MUTATIONS),
                str(LORA_PRESET_SAVE_SYNC),
                str(LORA_PRESET_ENTRY_LIFECYCLE),
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
