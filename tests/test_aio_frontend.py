from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AIO_JS = ROOT / "web" / "js" / "easyuse_anima_aio.js"
AUTOCOMPLETE_JS = ROOT / "web" / "js" / "easyuse_anima_autocomplete.js"


class AIOFrontendSourceTests(unittest.TestCase):
    def test_detailer_target_editor_builds_optimization_before_visibility_refresh(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function createDetailerTargetEditor")
        end = source.index("\nfunction openDetailerSettings", start)
        body = source[start:end]

        self.assertLess(
            body.index("const optimization = createStageOptimizationEditor"),
            body.index("updateInheritedRows();"),
        )

    def test_autocomplete_preview_filter_keeps_description_matches(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("function strictAutocompleteResults")
        end = source.index("\nfunction copyCaretMirrorStyle", start)
        body = source[start:end]

        self.assertIn("descriptionKey.includes(query)", body)
        self.assertIn("candidateKey.startsWith(query)", body)


if __name__ == "__main__":
    unittest.main()
