from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_JS = ROOT / "web" / "js"
API_JS = WEB_JS / "easyuse_anima_api.js"


class FrontendModuleStructureTests(unittest.TestCase):
    def test_shared_api_module_exports_runtime_helpers(self):
        source = API_JS.read_text(encoding="utf-8")

        for name in (
            "easyuseAnimaFetchJson",
            "easyuseAnimaGetSettings",
            "easyuseAnimaPostJson",
            "easyuseAnimaClassifyPrompt",
            "easyuseAnimaEncodeRFC3986URIComponent",
        ):
            self.assertRegex(source, rf"export (?:async )?function {name}\(")

    def test_feature_scripts_use_shared_api_module(self):
        expected_imports = {
            "easyuse_anima_autocomplete.js",
            "easyuse_anima_lora_preset.js",
            "easyuse_anima_prompt_studio.js",
            "easyuse_anima_prompt_studio_common.js",
            "easyuse_anima_settings.js",
        }

        for filename in expected_imports:
            with self.subTest(filename=filename):
                source = (WEB_JS / filename).read_text(encoding="utf-8")
                self.assertIn('./easyuse_anima_api.js"', source)

    def test_settings_endpoint_access_is_centralized(self):
        for path in WEB_JS.glob("*.js"):
            if path.name == "easyuse_anima_api.js":
                continue
            with self.subTest(filename=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn('fetch("/easyuse_anima/settings"', source)

    def test_classify_prompt_request_is_centralized(self):
        for path in WEB_JS.glob("*.js"):
            if path.name == "easyuse_anima_api.js":
                continue
            with self.subTest(filename=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn('fetch("/easyuse_anima/classify_prompt"', source)


if __name__ == "__main__":
    unittest.main()
