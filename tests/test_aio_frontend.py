from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AIO_JS = ROOT / "web" / "js" / "easyuse_anima_aio.js"
AUTOCOMPLETE_JS = ROOT / "web" / "js" / "easyuse_anima_autocomplete.js"
PROMPT_STUDIO_COMMON_JS = ROOT / "web" / "js" / "easyuse_anima_prompt_studio_common.js"


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
        self.assertNotIn('optimization.section.classList.toggle("hidden"', body)

    def test_highres_settings_save_stage_optimization(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function openHighresSettings")
        end = source.index("\nfunction createDetailerTargetEditor", start)
        body = source[start:end]

        self.assertIn('createStageOptimizationEditor("Highres Optimization"', body)
        self.assertIn("const optimized = optimization.values();", body)
        self.assertIn("...optimized,", body)
        self.assertNotIn("next.highres.spectrum = mergeDefaults", body)
        self.assertNotIn("next.highres.dit_corrections = mergeDefaults", body)

    def test_detailer_settings_support_custom_blocks(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function openDetailerSettings")
        end = source.index("\nfunction normalizeImageSaverHashBundles", start)
        body = source[start:end]

        self.assertIn('addBlock.textContent = aioText("button.addDetailerBlock");', body)
        self.assertIn("nextDetailerTargetName(currentOrder, detailer)", body)
        self.assertIn("Object.fromEntries(currentOrder.map", body)
        self.assertIn("isCustomDetailerTargetName(targetName)", body)
        self.assertIn("nextDetailer.order = normalizeDetailerOrder(currentOrder, nextDetailer);", body)

    def test_autocomplete_preview_filter_keeps_description_matches(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("function strictAutocompleteResults")
        end = source.index("\nfunction copyCaretMirrorStyle", start)
        body = source[start:end]

        self.assertIn("descriptionKey.includes(query)", body)
        self.assertIn("candidateKey.startsWith(query)", body)

    def test_autocomplete_refreshes_during_ime_composition_without_committing(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("  const updateNow = async () => {")
        end = source.index("  const update = debounce(updateNow);", start)
        update_body = source[start:end]

        self.assertIn("document.activeElement !== input", update_body)
        self.assertNotIn("composing || document.activeElement", update_body)
        self.assertIn('input.addEventListener("compositionupdate", update);', source)

        autocomplete_done = source.index("  input.__easyuseAnimaAutocomplete = true;")
        keydown_start = source.rindex('  input.addEventListener("keydown", (event) => {', 0, autocomplete_done)
        keydown_end = source.index("  });", keydown_start)
        keydown_body = source[keydown_start:keydown_end]

        self.assertIn("event.isComposing", keydown_body)
        self.assertIn("event.keyCode === 229", keydown_body)
        self.assertLess(
            keydown_body.index("event.isComposing"),
            keydown_body.index("!activeState"),
        )

    def test_autocomplete_arrow_navigation_keeps_adjacent_items_visible(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("function scrollActiveAutocompleteItemIntoView")
        end = source.index("\nfunction setActive", start)
        scroll_body = source[start:end]

        self.assertIn("index - 1", scroll_body)
        self.assertIn("index + 1", scroll_body)
        self.assertIn("menu.scrollTop", scroll_body)

        start = source.index("function setActive")
        end = source.index("\nfunction endsWithSentencePeriod", start)
        set_active_body = source[start:end]

        self.assertIn("const menu = ensurePopup();", set_active_body)
        self.assertIn("scrollActiveAutocompleteItemIntoView(menu, activeState.index);", set_active_body)

    def test_autocomplete_wildcards_accept_empty_and_unicode_queries(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("function currentWildcardToken")
        end = source.index("\nfunction autocompleteQuery", start)
        token_body = source[start:end]

        self.assertIn("caret >= opening + 2", token_body)
        self.assertIn(r"/[\r\n,]/.test(query)", token_body)
        self.assertNotIn(r"/^[\w.\-+/*\\]*$/i.test(query)", token_body)

        start = source.index("function normalizeWildcardSearchText")
        end = source.index("\nfunction strictAutocompleteResults", start)
        normalize_body = source[start:end]

        self.assertIn('replaceAll("\\\\", "/")', normalize_body)
        self.assertIn('replace(/[ _]+/g, "-")', normalize_body)

        start = source.index("async function searchWildcards")
        end = source.index("\nfunction scrollActiveAutocompleteItemIntoView", start)
        search_body = source[start:end]

        self.assertIn("normalizeWildcardSearchText(query)", search_body)
        self.assertIn("normalizeWildcardSearchText(item).includes(normalized)", search_body)

        start = source.index("function strictAutocompleteResults")
        end = source.index("\nfunction copyCaretMirrorStyle", start)
        strict_body = source[start:end]

        self.assertIn('return context.kind === "wildcard" ? results : [];', strict_body)

    def test_prompt_highlight_wildcards_accept_unicode_keys(self):
        source = PROMPT_STUDIO_COMMON_JS.read_text(encoding="utf-8")

        self.assertIn(r"const WILDCARD_HIGHLIGHT_RE = /(?:\d+#)?__[\p{L}\p{N}_.\-+/*\\]+?__/gu;", source)
        self.assertNotIn(r"const WILDCARD_HIGHLIGHT_RE = /(?:\d+#)?__[\w.\-+/*\\]+?__/g;", source)

        start = source.index("function renderHighlightedText")
        end = source.index("\nfunction cssPixelNumber", start)
        body = source[start:end]

        self.assertLess(body.index("hasHighlightSyntax(body)"), body.index("const baseKey = normalize(tokenBase(body));"))
        self.assertIn("html.push(syntaxHtml(body));", body)


if __name__ == "__main__":
    unittest.main()
