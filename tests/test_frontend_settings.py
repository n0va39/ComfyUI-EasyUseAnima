import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SETTINGS_ENTRY = ROOT / "web" / "js" / "easyuse_anima_settings.js"
SETTINGS_COLOR_EDITOR = ROOT / "web" / "js" / "settings" / "color_editor.js"
SETTINGS_COLOR_EDITOR_SMOKE = (
    ROOT / "tests" / "frontend_settings_color_editor_smoke.mjs"
)
SETTINGS_DEFINITION_DATA = ROOT / "web" / "js" / "settings" / "definition_data.js"
SETTINGS_DEFINITION_DATA_SMOKE = (
    ROOT / "tests" / "frontend_settings_definition_data_smoke.mjs"
)
SETTINGS_LONG_TEXT_EDITOR = (
    ROOT / "web" / "js" / "settings" / "long_text_editor.js"
)
SETTINGS_LONG_TEXT_EDITOR_SMOKE = (
    ROOT / "tests" / "frontend_settings_long_text_editor_smoke.mjs"
)
SETTINGS_RESOLUTION_EDITORS = (
    ROOT / "web" / "js" / "settings" / "resolution_editors.js"
)
SETTINGS_RESOLUTION_EDITORS_SMOKE = (
    ROOT / "tests" / "frontend_settings_resolution_editors_smoke.mjs"
)
SETTINGS_RUNTIME = ROOT / "web" / "js" / "settings" / "runtime.js"
SETTINGS_RUNTIME_SMOKE = ROOT / "tests" / "frontend_settings_runtime_smoke.mjs"
SETTINGS_WILDCARD_PATH_EDITOR = (
    ROOT / "web" / "js" / "settings" / "wildcard_path_editor.js"
)
SETTINGS_WILDCARD_PATH_EDITOR_SMOKE = (
    ROOT / "tests" / "frontend_settings_wildcard_path_editor_smoke.mjs"
)
JSCONFIG = ROOT / "jsconfig.json"
FRONTEND_CHECK_SCRIPT = ROOT / "tools" / "check_frontend.ps1"


class SettingsFrontendTests(unittest.TestCase):
    def test_runtime_module_boundary(self):
        module_source = SETTINGS_RUNTIME.read_text(encoding="utf-8")
        entry_source = SETTINGS_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createSettingsRuntime"],
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            r"\b(?:window|CustomEvent|app|registerExtension|document|localStorage)\b",
        )

        self.assertIn(
            'import { createSettingsRuntime } from "./settings/runtime.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s*\{\s*"
            r"updateInternalSetting\s*,\s*"
            r"readInternalSetting\s*,\s*"
            r"loadLongTextSettings\s*,\s*"
            r"saveLongTextSettings\s*,\s*"
            r"loadInitialSettings\s*,?\s*"
            r"\}\s*=\s*createSettingsRuntime"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        self.assertEqual(
            {
                line.strip().rstrip(",")
                for line in factory_match.group("dependencies").splitlines()
                if line.strip()
            },
            {
                "getSettingsState: () => window.__easyuseAnimaSettings",
                "setSettingsState: (value) => {",
                "window.__easyuseAnimaSettings = value;",
                "}",
                "notifySettingsUpdated: (detail) => {",
                "window.dispatchEvent(",
                'new CustomEvent("easyuse-anima-settings-updated", { detail })',
                ");",
                "internalKeys: INTERNAL_KEYS",
                "normalizeValue",
                "fetchInitialSettings: easyuseAnimaGetSettings",
                "fetchJson: easyuseAnimaFetchJson",
                "postJson: easyuseAnimaPostJson",
            },
        )

        for moved_name in (
            "updateInternalSetting",
            "readInternalSetting",
            "loadLongTextSettings",
            "saveLongTextSettings",
            "loadInitialSettings",
        ):
            with self.subTest(moved_name=moved_name):
                self.assertNotRegex(
                    entry_source,
                    rf"(?:async\s+)?function\s+{re.escape(moved_name)}\b",
                )
                self.assertIn(moved_name, module_source)

        for endpoint in (
            '"/easyuse_anima/long_text_settings"',
            '"/easyuse_anima/long_text_settings/save"',
        ):
            with self.subTest(endpoint=endpoint):
                self.assertNotIn(endpoint, entry_source)
                self.assertIn(endpoint, module_source)

        self.assertIn(
            'new CustomEvent("easyuse-anima-settings-updated", { detail })',
            entry_source,
        )
        self.assertRegex(entry_source, r"function\s+addSettingsFallback\(")
        self.assertEqual(entry_source.count("app.registerExtension("), 1)
        setup_match = re.search(
            r"app\.registerExtension\(\{.*?async\s+setup\(\)\s*\{"
            r"(?P<body>.*?)\}\s*,?\s*\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(setup_match)
        self.assertIn('name: "easyuse-anima.settings"', setup_match.group(0))
        self.assertIn(
            "settings: EASYUSE_ANIMA_SETTINGS",
            setup_match.group(0),
        )
        self.assertRegex(
            setup_match.group("body"),
            r"window\.__easyuseAnimaSettings\s*=\s*await\s+loadInitialSettings\(\);"
            r"\s*addSettingsFallback\(\);",
        )
        self.assertTrue(SETTINGS_RUNTIME_SMOKE.is_file())
        self.assertIn("web/js/settings/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_settings_runtime_smoke.mjs"',
            frontend_check_source,
        )

    def test_runtime_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(SETTINGS_RUNTIME_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_color_editor_module_boundary(self):
        module_source = SETTINGS_COLOR_EDITOR.read_text(encoding="utf-8")
        entry_source = SETTINGS_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createPromptStudioColorEditorButtonFactory"],
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            r"\b(?:window|app|api|fetch|registerExtension|CustomEvent|localStorage)\b",
        )

        self.assertIn(
            'import { createPromptStudioColorEditorButtonFactory } from '
            '"./settings/color_editor.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+createPromptStudioColorEditorButton\s*=\s*"
            r"createPromptStudioColorEditorButtonFactory"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        self.assertEqual(
            {
                line.strip().rstrip(",")
                for line in factory_match.group("dependencies").splitlines()
                if line.strip()
            },
            {
                "document",
                "text: t",
                "label",
                "tip",
                "readInternalSetting",
                "updateInternalSetting",
            },
        )

        for moved_name in (
            "PROMPT_STUDIO_COLORS",
            "PROMPT_STUDIO_COLOR_GROUPS",
            "activePromptStudioColorEditor",
            "parseColors",
            "promptStudioColorSettingValue",
            "serializePromptStudioColors",
            "persistPromptStudioColorSettings",
            "openPromptStudioColorEditor",
            "closePromptStudioColorEditor",
        ):
            with self.subTest(moved_name=moved_name):
                self.assertNotRegex(
                    entry_source,
                    rf"\b(?:const|let|var|function|class)\s+{re.escape(moved_name)}\b",
                )
                self.assertIn(moved_name, module_source)
        self.assertNotRegex(
            entry_source,
            r"function\s+createPromptStudioColorEditorButton\b",
        )
        self.assertIn(
            "function createPromptStudioColorEditorButton(_name, setter, value)",
            module_source,
        )
        self.assertNotIn("easyuse-anima-prompt-color-overlay", entry_source)
        self.assertNotIn("easyuse-anima-prompt-color-panel", entry_source)
        self.assertIn("easyuse-anima-prompt-color-overlay", module_source)
        self.assertIn("easyuse-anima-prompt-color-panel", module_source)

        setting_match = re.search(
            r'customSetting\(\{\s*id:\s*"EasyUseAnima\.Prompt\.HighlightColors",'
            r"(?P<body>.*?)\}\),",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(setting_match)
        self.assertIn(
            "render: createPromptStudioColorEditorButton,",
            setting_match.group("body"),
        )
        self.assertRegex(entry_source, r"function\s+label\(")
        self.assertRegex(entry_source, r"function\s+tip\(")
        self.assertTrue(SETTINGS_COLOR_EDITOR_SMOKE.is_file())
        self.assertIn("web/js/settings/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_settings_color_editor_smoke.mjs"',
            frontend_check_source,
        )

    def test_color_editor_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(SETTINGS_COLOR_EDITOR_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_wildcard_path_editor_module_boundary(self):
        module_source = SETTINGS_WILDCARD_PATH_EDITOR.read_text(encoding="utf-8")
        entry_source = SETTINGS_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createWildcardExtraPathsEditorFactory"],
        )
        module_import = re.search(
            r'^import\s*\{(?P<names>[^}]*)\}\s*from\s*"\./definition_data\.js";',
            module_source,
            re.MULTILINE,
        )
        self.assertIsNotNone(module_import)
        self.assertEqual(
            {
                name.strip().rstrip(",")
                for name in module_import.group("names").splitlines()
                if name.strip()
            },
            {
                "parseWildcardExtraPathItems",
                "serializeWildcardExtraPathItems",
            },
        )
        self.assertNotRegex(
            module_source,
            r"\b(?:window|app|api|fetch|registerExtension|CustomEvent)\b",
        )

        self.assertIn(
            'import { createWildcardExtraPathsEditorFactory } from '
            '"./settings/wildcard_path_editor.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+createWildcardExtraPathsEditor\s*=\s*"
            r"createWildcardExtraPathsEditorFactory"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        self.assertEqual(
            {
                line.strip().rstrip(",")
                for line in factory_match.group("dependencies").splitlines()
                if line.strip()
            },
            {
                "document",
                "text: t",
                "readInternalSetting",
                "updateInternalSetting",
            },
        )
        self.assertNotRegex(
            entry_source,
            r"(?:function|const|let|var)\s+wildcardExtraPathsSettingValue\b",
        )
        self.assertNotRegex(
            entry_source,
            r"function\s+createWildcardExtraPathsEditor\b",
        )
        self.assertIn("function wildcardExtraPathsSettingValue(value)", module_source)
        self.assertIn("function createWildcardExtraPathsEditor(name, setter, value)", module_source)

        setting_match = re.search(
            r'customSetting\(\{\s*id:\s*"EasyUseAnima\.Wildcard\.ExtraPaths",'
            r"(?P<body>.*?)\}\),",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(setting_match)
        self.assertIn(
            "render: createWildcardExtraPathsEditor,",
            setting_match.group("body"),
        )
        self.assertTrue(SETTINGS_WILDCARD_PATH_EDITOR_SMOKE.is_file())
        self.assertIn("web/js/settings/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_settings_wildcard_path_editor_smoke.mjs"',
            frontend_check_source,
        )

    def test_wildcard_path_editor_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(SETTINGS_WILDCARD_PATH_EDITOR_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_resolution_editors_module_boundary(self):
        module_source = SETTINGS_RESOLUTION_EDITORS.read_text(encoding="utf-8")
        entry_source = SETTINGS_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createResolutionEditors"],
        )
        module_import = re.search(
            r'^import\s*\{(?P<names>[^}]*)\}\s*from\s*"\./definition_data\.js";',
            module_source,
            re.MULTILINE,
        )
        self.assertIsNotNone(module_import)
        self.assertEqual(
            {
                name.strip().rstrip(",")
                for name in module_import.group("names").splitlines()
                if name.strip()
            },
            {
                "NAIA_RESOLUTION_MODE_BUCKET",
                "NAIA_RESOLUTION_MODE_SCALE",
                "normalizeNaiaResolutionModeValue",
                "normalizeNaiaResolutionScaleValue",
            },
        )
        self.assertNotRegex(
            module_source,
            r"\b(?:window|app|api|fetch|registerExtension|CustomEvent)\b",
        )

        self.assertIn(
            'import { createResolutionEditors } from '
            '"./settings/resolution_editors.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s*\{\s*"
            r"createNaiaResolutionModeEditor\s*,\s*"
            r"createNaiaResolutionScaleEditor\s*,?\s*"
            r"\}\s*=\s*createResolutionEditors"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        self.assertEqual(
            {
                line.strip().rstrip(",")
                for line in factory_match.group("dependencies").splitlines()
                if line.strip()
            },
            {
                "document",
                "text: t",
                "readInternalSetting",
                "updateInternalSetting",
            },
        )

        for moved_name in (
            "naiaResolutionModeSettingValue",
            "createNaiaResolutionModeEditor",
            "naiaResolutionScaleSettingValue",
            "createNaiaResolutionScaleEditor",
        ):
            with self.subTest(moved_name=moved_name):
                self.assertNotRegex(
                    entry_source,
                    rf"(?:function|const|let|var)\s+{re.escape(moved_name)}\b",
                )
                self.assertIn(moved_name, module_source)

        for setting_id, render_name in (
            (
                "EasyUseAnima.NAIA.ResolutionMode",
                "createNaiaResolutionModeEditor",
            ),
            (
                "EasyUseAnima.NAIA.ResolutionScale",
                "createNaiaResolutionScaleEditor",
            ),
        ):
            with self.subTest(setting_id=setting_id):
                setting_match = re.search(
                    rf'customSetting\(\{{\s*id:\s*"{re.escape(setting_id)}",'
                    r"(?P<body>.*?)\}\),",
                    entry_source,
                    re.DOTALL,
                )
                self.assertIsNotNone(setting_match)
                self.assertIn(
                    f"render: {render_name},",
                    setting_match.group("body"),
                )

        self.assertIn("window.__easyuseAnimaSettings", entry_source)
        self.assertTrue(SETTINGS_RESOLUTION_EDITORS_SMOKE.is_file())
        self.assertIn("web/js/settings/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_settings_resolution_editors_smoke.mjs"',
            frontend_check_source,
        )

    def test_resolution_editors_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(SETTINGS_RESOLUTION_EDITORS_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_long_text_editor_module_boundary(self):
        module_source = SETTINGS_LONG_TEXT_EDITOR.read_text(encoding="utf-8")
        entry_source = SETTINGS_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createLongTextEditorButtonFactory"],
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            r"\b(?:app|api|registerExtension|window|CustomEvent)\b",
        )
        self.assertNotIn("/easyuse_anima/long_text_settings", module_source)

        self.assertIn(
            'import { createLongTextEditorButtonFactory } from '
            '"./settings/long_text_editor.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+createLongTextEditorButton\s*=\s*"
            r"createLongTextEditorButtonFactory"
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
                "fieldGroups: LONG_TEXT_FIELD_GROUPS",
                "text: t",
                "loadSettings: loadLongTextSettings",
                "saveSettings: saveLongTextSettings",
                "schedule: setTimeout",
            },
        )

        for moved_name in (
            "activeLongTextEditor",
            "openLongTextEditor",
            "closeLongTextEditor",
        ):
            with self.subTest(moved_name=moved_name):
                self.assertNotIn(moved_name, entry_source)
                self.assertIn(moved_name, module_source)
        self.assertNotRegex(
            entry_source,
            r"function\s+createLongTextEditorButton\(",
        )
        self.assertNotIn("easyuse-anima-long-text-overlay", entry_source)
        self.assertNotIn("easyuse-anima-long-text-panel", entry_source)
        self.assertIn("easyuse-anima-long-text-overlay", module_source)
        self.assertIn("easyuse-anima-long-text-panel", module_source)

        self.assertIn("window.__easyuseAnimaSettings", entry_source)
        self.assertIn('new CustomEvent("easyuse-anima-settings-updated"', entry_source)

        self.assertTrue(SETTINGS_LONG_TEXT_EDITOR_SMOKE.is_file())
        self.assertIn("web/js/settings/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_settings_long_text_editor_smoke.mjs"',
            frontend_check_source,
        )

    def test_long_text_editor_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(SETTINGS_LONG_TEXT_EDITOR_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_definition_data_module_boundary(self):
        module_source = SETTINGS_DEFINITION_DATA.read_text(encoding="utf-8")
        entry_source = SETTINGS_ENTRY.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")
        expected_exports = {
            "INTERNAL_KEYS",
            "LONG_TEXT_FIELDS",
            "LONG_TEXT_FIELD_GROUPS",
            "NAIA_PREPROCESSING_OPTIONS",
            "NAIA_RESOLUTION_BUCKET_OPTIONS",
            "NAIA_RESOLUTION_MODE_BUCKET",
            "NAIA_RESOLUTION_MODE_SCALE",
            "ROOT_CATEGORY",
            "normalizeNaiaResolutionModeValue",
            "normalizeNaiaResolutionScaleValue",
            "normalizeValue",
            "parseWildcardExtraPathItems",
            "serializeWildcardExtraPathItems",
        }
        resolution_imports = {
            "NAIA_RESOLUTION_MODE_BUCKET",
            "NAIA_RESOLUTION_MODE_SCALE",
            "normalizeNaiaResolutionModeValue",
            "normalizeNaiaResolutionScaleValue",
        }
        wildcard_imports = {
            "parseWildcardExtraPathItems",
            "serializeWildcardExtraPathItems",
        }
        expected_imports = (
            expected_exports
            - {"LONG_TEXT_FIELDS"}
            - resolution_imports
            - wildcard_imports
        )

        exported_names = set(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            )
        )
        self.assertEqual(exported_names, expected_exports)

        import_match = re.search(
            r'^import\s*\{(?P<names>[^}]*)\}\s*from\s*"\./settings/definition_data\.js";',
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
        self.assertNotRegex(module_source, re.compile(r"^\s*import\b", re.MULTILINE))
        self.assertNotRegex(
            module_source,
            (
                r"\b(?:document|window|app|api|fetch|registerExtension|"
                r"addEventListener|removeEventListener|CustomEvent|"
                r"HTMLElement|HTMLInputElement|HTMLTextAreaElement)\b"
            ),
        )

        for name in expected_exports:
            with self.subTest(moved_declaration=name):
                self.assertNotRegex(
                    entry_source,
                    rf"\b(?:const|let|var|function|class)\s+{re.escape(name)}\b",
                )
        self.assertNotIn(
            "for (const [key] of NAIA_PREPROCESSING_OPTIONS)",
            entry_source,
        )

        for adapter in (
            "setting",
            "customSetting",
            "addSettingsFallback",
        ):
            with self.subTest(entry_adapter=adapter):
                self.assertRegex(
                    entry_source,
                    rf"(?:async\s+)?function\s+{re.escape(adapter)}\(",
                )
        self.assertIn("const EASYUSE_ANIMA_SETTINGS = [", entry_source)
        self.assertEqual(entry_source.count("app.registerExtension("), 1)

        self.assertTrue(SETTINGS_DEFINITION_DATA_SMOKE.is_file())
        self.assertIn("web/js/settings/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_settings_definition_data_smoke.mjs"',
            frontend_check_source,
        )

    def test_definition_data_module_semantics(self):
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(SETTINGS_DEFINITION_DATA_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())


if __name__ == "__main__":
    unittest.main()
