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
JSCONFIG = ROOT / "jsconfig.json"
FRONTEND_CHECK_SCRIPT = ROOT / "tools" / "check_frontend.ps1"


class SettingsFrontendTests(unittest.TestCase):
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
            "createLongTextEditorButton",
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
