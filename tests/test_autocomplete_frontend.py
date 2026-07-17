from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTOCOMPLETE_ENTRY = ROOT / "web" / "js" / "easyuse_anima_autocomplete.js"
AUTOCOMPLETE_DATA_ADAPTER = (
    ROOT / "web" / "js" / "autocomplete" / "data_adapter.js"
)
AUTOCOMPLETE_DATA_ADAPTER_SMOKE = (
    ROOT / "tests" / "frontend_autocomplete_data_adapter_smoke.mjs"
)
AUTOCOMPLETE_INPUT_CONTROLLER = (
    ROOT / "web" / "js" / "autocomplete" / "input_controller.js"
)
AUTOCOMPLETE_INPUT_CONTROLLER_SMOKE = (
    ROOT / "tests" / "frontend_autocomplete_input_controller_smoke.mjs"
)
AUTOCOMPLETE_INPUT_BINDING = (
    ROOT / "web" / "js" / "autocomplete" / "input_binding.js"
)
AUTOCOMPLETE_INPUT_BINDING_SMOKE = (
    ROOT / "tests" / "frontend_autocomplete_input_binding_smoke.mjs"
)
AUTOCOMPLETE_TEXT_MODEL = (
    ROOT / "web" / "js" / "autocomplete" / "text_model.js"
)
AUTOCOMPLETE_TEXT_MODEL_SMOKE = (
    ROOT / "tests" / "frontend_autocomplete_text_model_smoke.mjs"
)
AUTOCOMPLETE_POPUP_GEOMETRY = (
    ROOT / "web" / "js" / "autocomplete" / "popup_geometry.js"
)
AUTOCOMPLETE_POPUP_GEOMETRY_SMOKE = (
    ROOT / "tests" / "frontend_autocomplete_popup_geometry_smoke.mjs"
)
JSCONFIG = ROOT / "jsconfig.json"
FRONTEND_CHECK_SCRIPT = ROOT / "tools" / "check_frontend.ps1"


class AutocompleteFrontendBoundaryTests(unittest.TestCase):
    def test_input_controller_has_exact_lifecycle_boundary(self):
        module_source = AUTOCOMPLETE_INPUT_CONTROLLER.read_text(encoding="utf-8")
        entry_source = AUTOCOMPLETE_ENTRY.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            [
                "invalidateAutocompleteControllerStates",
                "createAutocompleteInputController",
            ],
        )
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
        import_match = re.search(
            (
                r'^import\s*\{(?P<names>[^}]*)\}\s*from\s*'
                r'"\./autocomplete/input_controller\.js";'
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
        self.assertEqual(
            imported_names,
            {
                "createAutocompleteInputController",
                "invalidateAutocompleteControllerStates",
            },
        )
        self.assertEqual(
            entry_source.count("createAutocompleteInputController({"),
            1,
        )

        hook_start = entry_source.index("function hookInput")
        hook_end = entry_source.index("\nfunction hookWidget", hook_start)
        hook_body = entry_source[hook_start:hook_end]
        self.assertNotIn("let composing", hook_body)
        self.assertNotIn("let updateSeq", hook_body)
        self.assertNotIn("requestAnimationFrame(updateNow)", hook_body)
        self.assertNotIn("setTimeout(updateNow, 0)", hook_body)
        self.assertIn("const controller = createAutocompleteInputController({", hook_body)
        self.assertIn("state.binding = createAutocompleteInputBinding({", hook_body)
        self.assertIn("const results = await request(", hook_body)
        self.assertIn("isCurrent()", hook_body)
        self.assertIn("state?.controller?.invalidate();", entry_source)

        invalidate_start = entry_source.index(
            "function invalidateAutocompleteDataRequests"
        )
        invalidate_end = entry_source.index(
            "\nfunction refreshActiveAutocomplete", invalidate_start
        )
        invalidate_body = entry_source[invalidate_start:invalidate_end]
        self.assertIn(
            "invalidateAutocompleteControllerStates(states, activeState);",
            invalidate_body,
        )
        self.assertIn("for (const input of [...hookedAutocompleteInputs])", invalidate_body)
        self.assertIn("states.push(state);", invalidate_body)
        self.assertIn("if (document.activeElement === input) {", invalidate_body)
        self.assertIn("hidePopup({ preserveController: true });", invalidate_body)
        self.assertIn("focusedState.controller.scheduleUpdate();", invalidate_body)
        self.assertIn("autocompleteEnabledForState(focusedState)", invalidate_body)
        self.assertLess(
            invalidate_body.index(
                "invalidateAutocompleteControllerStates(states, activeState);"
            ),
            invalidate_body.index("hidePopup({ preserveController: true });"),
        )
        self.assertLess(
            invalidate_body.index("hidePopup({ preserveController: true });"),
            invalidate_body.index("focusedState.controller.scheduleUpdate();"),
        )

        refresh_start = entry_source.index(
            "async function refreshAutocompleteSettings"
        )
        refresh_end = entry_source.index("\nfunction ensureStyle", refresh_start)
        refresh_body = entry_source[refresh_start:refresh_end]
        self.assertIn(
            "let dataRequestsInvalidated = autocompleteData.syncSourceSettings(",
            refresh_body,
        )
        self.assertIn(
            "const previousMode = autocompleteMode;",
            refresh_body,
        )
        self.assertRegex(
            refresh_body,
            re.compile(
                r"autocompleteData\.syncSourceSettings\(\s*"
                r"settings,\s*\{ initialize: true \},\s*\)",
                re.DOTALL,
            ),
        )
        self.assertIn(
            "const previousDetectNaturalSentences = "
            "autocompleteDetectNaturalSentences;",
            refresh_body,
        )
        self.assertIn(
            "const previousPreviewCompletion = autocompletePreviewCompletion;",
            refresh_body,
        )
        self.assertIn(
            "if (autocompleteDetectNaturalSentences !== "
            "previousDetectNaturalSentences) {",
            refresh_body,
        )
        self.assertIn(
            "if (autocompletePreviewCompletion !== previousPreviewCompletion) {",
            refresh_body,
        )
        self.assertIn(
            "invalidateAutocompleteDataRequests();",
            refresh_body,
        )
        self.assertIn(
            "if (dataRequestsInvalidated) {\n"
            "      invalidateAutocompleteDataRequests();\n"
            "    }",
            refresh_body,
        )

        settings_start = entry_source.index(
            'window.addEventListener("easyuse-anima-settings-updated"'
        )
        settings_end = entry_source.index(
            "\n\napp.registerExtension({", settings_start
        )
        settings_body = entry_source[settings_start:settings_end]
        self.assertIn("let dataRequestsInvalidated = false;", settings_body)
        self.assertIn("dataRequestsInvalidated = true;", settings_body)
        self.assertIn(
            'const nextMaxResults = clampMaxResults(detail["autocomplete.limit"]);',
            settings_body,
        )
        self.assertIn("if (nextMaxResults !== maxResults) {", settings_body)
        self.assertIn(
            "if (autocompleteMode !== previousMode) {\n"
            "      dataRequestsInvalidated = true;\n"
            "    }",
            settings_body,
        )
        self.assertIn(
            "if (autocompleteData.syncSourceSettings(detail)) {\n"
            "    dataRequestsInvalidated = true;\n"
            "  }",
            settings_body,
        )
        self.assertIn(
            "const previousDetectNaturalSentences = "
            "autocompleteDetectNaturalSentences;",
            settings_body,
        )
        self.assertIn(
            "const previousPreviewCompletion = autocompletePreviewCompletion;",
            settings_body,
        )
        self.assertIn(
            "if (autocompleteDetectNaturalSentences !== "
            "previousDetectNaturalSentences) {",
            settings_body,
        )
        self.assertIn(
            "if (autocompletePreviewCompletion !== previousPreviewCompletion) {",
            settings_body,
        )
        self.assertIn(
            "invalidateAutocompleteDataRequests();",
            settings_body,
        )
        self.assertIn(
            "} else {\n    scheduleActiveRefresh();\n  }",
            settings_body,
        )
        self.assertNotIn("hidePopup();", settings_body)

    def test_input_controller_module_semantics(self):
        self.assertTrue(AUTOCOMPLETE_INPUT_CONTROLLER_SMOKE.is_file())
        self.assertTrue(AUTOCOMPLETE_INPUT_BINDING_SMOKE.is_file())
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            r'node "tests\frontend_autocomplete_input_controller_smoke.mjs"',
            frontend_check_source,
        )
        self.assertIn(
            r'node "tests\frontend_autocomplete_input_binding_smoke.mjs"',
            frontend_check_source,
        )

        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(AUTOCOMPLETE_INPUT_CONTROLLER_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_input_binding_has_exact_listener_lifecycle_boundary(self):
        module_source = AUTOCOMPLETE_INPUT_BINDING.read_text(encoding="utf-8")
        entry_source = AUTOCOMPLETE_ENTRY.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createAutocompleteInputBinding"],
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            (
                r"\b(?:document|window|app|api|fetch|registerExtension|"
                r"MutationObserver|HTMLElement|HTMLInputElement|"
                r"HTMLTextAreaElement)\b"
            ),
        )
        self.assertIn(
            'import { createAutocompleteInputBinding } from '
            '"./autocomplete/input_binding.js";',
            entry_source,
        )
        self.assertEqual(entry_source.count("createAutocompleteInputBinding({"), 1)

        hook_start = entry_source.index("function hookInput")
        hook_end = entry_source.index("\nfunction hookWidget", hook_start)
        hook_body = entry_source[hook_start:hook_end]
        self.assertIn("state.binding = createAutocompleteInputBinding({", hook_body)
        self.assertIn("return existing.dispose;", hook_body)
        self.assertIn("return state.dispose;", hook_body)
        self.assertNotIn("input.addEventListener(", hook_body)

        self.assertIn('listen("compositionstart", controller.beginComposition);', module_source)
        self.assertIn('listen("compositionupdate", controller.scheduleUpdate);', module_source)
        self.assertIn('listen("compositionend", controller.endComposition);', module_source)
        self.assertEqual(module_source.count('listen("keydown"'), 3)
        self.assertIn("input.removeEventListener(type, listener, options);", module_source)
        self.assertIn("controller.dispose();", module_source)
        self.assertIn("clearTimer(blurTimer);", module_source)
        self.assertIn("middlePanCleanup?.();", module_source)
        self.assertIn(
            "const staleDispose = input.__easyuseAnimaAutocompleteDispose;",
            module_source,
        )
        self.assertIn('typeof staleDispose === "function"', module_source)
        self.assertIn("staleDispose();", module_source)

        dispose_start = entry_source.index("function disposeAutocompleteInput")
        dispose_end = entry_source.index("\nfunction syncAutocompleteInputFlags", dispose_start)
        dispose_body = entry_source[dispose_start:dispose_end]
        self.assertIn(
            "const staleDispose = input.__easyuseAnimaAutocompleteDispose;",
            dispose_body,
        )
        self.assertIn("staleDispose();", dispose_body)
        self.assertIn("expectedState.binding?.dispose();", dispose_body)
        self.assertIn("expectedState.controller?.dispose?.();", dispose_body)
        self.assertIn("input.__easyuseAnimaAutocompleteState === expectedState", dispose_body)
        self.assertIn("input?.isConnected === false", dispose_body)
        self.assertIn("pruneDisconnectedAutocompleteInputs(input);", hook_body)

    def test_popup_geometry_has_exact_dom_free_boundary(self):
        module_source = AUTOCOMPLETE_POPUP_GEOMETRY.read_text(encoding="utf-8")
        entry_source = AUTOCOMPLETE_ENTRY.read_text(encoding="utf-8")
        expected_exports = {
            "calculateAutocompletePopupGeometry",
            "calculateCaretMirrorGeometry",
            "normalizeCaretClientRect",
        }

        exported_names = set(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            )
        )
        self.assertEqual(exported_names, expected_exports)
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

        import_match = re.search(
            (
                r'^import\s*\{(?P<names>[^}]*)\}\s*from\s*'
                r'"\./autocomplete/popup_geometry\.js";'
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
        self.assertEqual(imported_names, expected_exports)

        caret_start = entry_source.index("function caretClientRect")
        popup_start = entry_source.index("\nfunction positionPopup", caret_start)
        scroll_start = entry_source.index(
            "\nfunction scrollActiveAutocompleteItemIntoView",
            popup_start,
        )
        caret_body = entry_source[caret_start:popup_start]
        popup_body = entry_source[popup_start:scroll_start]
        self.assertIn("calculateCaretMirrorGeometry(", caret_body)
        self.assertIn("normalizeCaretClientRect(", caret_body)
        self.assertRegex(
            caret_body,
            re.compile(
                r"const fallbackLineHeight = \(\s*"
                r"Number\.isFinite\(markerRect\.left\)\s*"
                r"&& Number\.isFinite\(markerRect\.top\)\s*"
                r"&& !markerRect\.height\s*\)\s*"
                r"\? Number\.parseFloat\("
                r"getComputedStyle\(input\)\.lineHeight\)\s*"
                r": 0;",
                re.DOTALL,
            ),
        )
        self.assertIn("calculateAutocompletePopupGeometry(", popup_body)
        self.assertRegex(
            popup_body,
            re.compile(
                r"const fallbackLineHeight = caretRect\.height\s*"
                r"\? 0\s*"
                r": Number\.parseFloat\("
                r"getComputedStyle\(input\)\.lineHeight\);",
                re.DOTALL,
            ),
        )
        self.assertNotIn("Math.max(260", popup_body)
        self.assertNotIn("const caretLeft =", popup_body)

    def test_popup_geometry_module_semantics(self):
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")
        self.assertTrue(AUTOCOMPLETE_POPUP_GEOMETRY_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_autocomplete_popup_geometry_smoke.mjs"',
            frontend_check_source,
        )

        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node executable is not available")

        completed = subprocess.run(
            [node_bin, str(AUTOCOMPLETE_POPUP_GEOMETRY_SMOKE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            self.fail((completed.stdout + completed.stderr).strip())

    def test_data_adapter_has_exact_io_boundary(self):
        module_source = AUTOCOMPLETE_DATA_ADAPTER.read_text(encoding="utf-8")
        entry_source = AUTOCOMPLETE_ENTRY.read_text(encoding="utf-8")

        self.assertEqual(module_source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(
                r"^export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)",
                module_source,
                re.MULTILINE,
            ),
            ["createAutocompleteDataAdapter"],
        )
        self.assertNotRegex(
            module_source,
            re.compile(r"^\s*import\b", re.MULTILINE),
        )
        self.assertNotRegex(
            module_source,
            (
                r"\b(?:document|window|app|api|registerExtension|"
                r"addEventListener|removeEventListener|MutationObserver|"
                r"HTMLElement|HTMLInputElement|HTMLTextAreaElement)\b"
            ),
        )

        self.assertIn(
            'import { createAutocompleteDataAdapter } from '
            '"./autocomplete/data_adapter.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+autocompleteData\s*=\s*"
            r"createAutocompleteDataAdapter"
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
                "fetchJson: easyuseAnimaFetchJson",
                "normalizeWildcardSearchText",
                "getLimit: () => maxResults",
            },
        )

        for moved_declaration in (
            "cache",
            "wildcardItemsCache",
            "search",
            "loadWildcardItems",
            "searchWildcards",
        ):
            with self.subTest(moved_declaration=moved_declaration):
                self.assertNotRegex(
                    entry_source,
                    rf"\b(?:const|let|var|function|class)\s+"
                    rf"{re.escape(moved_declaration)}\b",
                )

        self.assertNotIn("/easyuse_anima/autocomplete", entry_source)
        self.assertNotIn("/easyuse_anima/wildcards", entry_source)
        self.assertEqual(entry_source.count("autocompleteData.search("), 1)
        self.assertEqual(
            entry_source.count("autocompleteData.searchWildcards("),
            1,
        )
        self.assertEqual(
            entry_source.count("autocompleteData.clearResults()"),
            3,
        )
        self.assertEqual(
            entry_source.count("autocompleteData.clearWildcards()"),
            0,
        )
        self.assertEqual(
            entry_source.count("autocompleteData.syncSourceSettings("),
            2,
        )
        self.assertIn("app.registerExtension({", entry_source)
        self.assertIn('document.addEventListener("pointerdown"', entry_source)
        self.assertIn("function hookInput(", entry_source)

    def test_data_adapter_is_in_static_and_semantic_runners(self):
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(AUTOCOMPLETE_DATA_ADAPTER_SMOKE.is_file())
        self.assertIn("web/js/autocomplete/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_autocomplete_data_adapter_smoke.mjs"',
            frontend_check_source,
        )

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
