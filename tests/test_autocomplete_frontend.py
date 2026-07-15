from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTOCOMPLETE_ENTRY = ROOT / "web" / "js" / "easyuse_anima_autocomplete.js"
AUTOCOMPLETE_TEXT_MODEL = (
    ROOT / "web" / "js" / "autocomplete" / "text_model.js"
)
AUTOCOMPLETE_TEXT_MODEL_SMOKE = (
    ROOT / "tests" / "frontend_autocomplete_text_model_smoke.mjs"
)
JSCONFIG = ROOT / "jsconfig.json"
FRONTEND_CHECK_SCRIPT = ROOT / "tools" / "check_frontend.ps1"


class AutocompleteFrontendBoundaryTests(unittest.TestCase):
    def test_text_model_has_exact_dom_free_boundary(self):
        module_source = AUTOCOMPLETE_TEXT_MODEL.read_text(encoding="utf-8")
        entry_source = AUTOCOMPLETE_ENTRY.read_text(encoding="utf-8")
        expected_exports = {
            "autocompleteQuery",
            "currentToken",
            "currentWildcardToken",
            "isCaretInComment",
            "isCaretInPromptTranslationMarker",
            "normalizeWildcardSearchText",
            "parseAutocompleteText",
            "planAutocompleteInsertion",
            "wildcardAutocompleteQuery",
        }
        expected_imports = {
            "autocompleteQuery",
            "currentToken as currentAutocompleteToken",
            "currentWildcardToken as currentAutocompleteWildcardToken",
            "isCaretInComment",
            (
                "isCaretInPromptTranslationMarker "
                "as caretInPromptTranslationMarker"
            ),
            "normalizeWildcardSearchText",
            "parseAutocompleteText",
            "planAutocompleteInsertion",
            "wildcardAutocompleteQuery",
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
            (
                r'^import\s*\{(?P<names>[^}]*)\}\s*from\s*'
                r'"\./autocomplete/text_model\.js";'
            ),
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

    def test_entry_delegates_text_rules_without_duplicate_ownership(self):
        source = AUTOCOMPLETE_ENTRY.read_text(encoding="utf-8")
        moved_declarations = {
            "autocompleteQuery",
            "isCaretInComment",
            "normalizeWildcardSearchText",
            "parseAutocompleteText",
            "planAutocompleteInsertion",
            "wildcardAutocompleteQuery",
        }
        moved_private_helpers = {
            "endsWithSentencePeriod",
            "insertPrefixForBefore",
            "insertSuffixForAfter",
            "insertSuffixPlanForAfter",
            "isEscaped",
            "isSentencePeriod",
            "naturalSentenceEnd",
            "naturalSentenceStart",
            "startsWithSentencePeriod",
            "stripPromptSyntaxClosingParens",
            "trimPromptSyntaxPrefix",
            "trimPromptSyntaxSuffix",
        }

        for name in moved_declarations | moved_private_helpers:
            with self.subTest(moved_declaration=name):
                self.assertNotRegex(
                    source,
                    rf"\b(?:const|let|var|function|class)\s+{re.escape(name)}\b",
                )

        current_start = source.index("function currentToken")
        wildcard_start = source.index("\nfunction currentWildcardToken", current_start)
        marker_start = source.index(
            "\nfunction isCaretInPromptTranslationMarker",
            wildcard_start,
        )
        signature_start = source.index(
            "\nfunction autocompleteStateSignature",
            marker_start,
        )
        current_body = source[current_start:wildcard_start]
        wildcard_body = source[wildcard_start:marker_start]
        marker_body = source[marker_start:signature_start]

        self.assertIn("currentAutocompleteToken(", current_body)
        self.assertIn(
            "detectNaturalSentences: autocompleteDetectNaturalSentences",
            current_body,
        )
        self.assertIn(
            "previewCompletion: autocompletePreviewCompletion",
            current_body,
        )
        self.assertIn("currentAutocompleteWildcardToken(", wildcard_body)
        self.assertIn("caretInPromptTranslationMarker(", marker_body)
        for adapter_body in (current_body, wildcard_body, marker_body):
            self.assertNotIn("while (", adapter_body)
            self.assertNotIn(".indexOf(", adapter_body)

        commit_start = source.index("function commitSuggestion")
        commit_end = source.index("\nfunction displayTagText", commit_start)
        preview_start = source.index("function completionPreviewPlan")
        preview_end = source.index(
            "\nfunction updateAutocompletePreview",
            preview_start,
        )
        commit_body = source[commit_start:commit_end]
        preview_body = source[preview_start:preview_end]
        self.assertIn(
            'if (entry?.kind === "wildcard" && !wildcardToken)',
            preview_body,
        )
        for plan_consumer in (commit_body, preview_body):
            self.assertIn("planAutocompleteInsertion(", plan_consumer)
            self.assertIn(
                "appendSeparator: autocompleteAppendSeparator",
                plan_consumer,
            )
            self.assertIn(
                "noCommaAfterPeriod: autocompleteNoCommaAfterPeriod",
                plan_consumer,
            )
            self.assertIn("plan.replacement", plan_consumer)
            self.assertIn("plan.start", plan_consumer)
            self.assertIn("plan.end", plan_consumer)

        self.assertEqual(source.count("planAutocompleteInsertion("), 2)
        self.assertIn("app.registerExtension({", source)
        self.assertIn('document.addEventListener("pointerdown"', source)
        self.assertIn("function hookInput(", source)

    def test_text_model_is_in_static_and_semantic_runners(self):
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(AUTOCOMPLETE_TEXT_MODEL_SMOKE.is_file())
        self.assertIn("web/js/autocomplete/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_autocomplete_text_model_smoke.mjs"',
            frontend_check_source,
        )


if __name__ == "__main__":
    unittest.main()
