import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SETTINGS_ENTRY = ROOT / "web" / "js" / "easyuse_anima_settings.js"
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
JSCONFIG = ROOT / "jsconfig.json"
FRONTEND_CHECK_SCRIPT = ROOT / "tools" / "check_frontend.ps1"


class SettingsFrontendTests(unittest.TestCase):
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

        self.assertIn("async function loadLongTextSettings()", entry_source)
        self.assertIn("async function saveLongTextSettings(values)", entry_source)
        self.assertIn('"/easyuse_anima/long_text_settings"', entry_source)
        self.assertIn('"/easyuse_anima/long_text_settings/save"', entry_source)
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
        expected_imports = expected_exports - {"LONG_TEXT_FIELDS"}

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
            "updateInternalSetting",
            "loadLongTextSettings",
            "saveLongTextSettings",
            "createPromptStudioColorEditorButton",
            "createWildcardExtraPathsEditor",
            "createNaiaResolutionModeEditor",
            "createNaiaResolutionScaleEditor",
            "setting",
            "customSetting",
            "loadInitialSettings",
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
