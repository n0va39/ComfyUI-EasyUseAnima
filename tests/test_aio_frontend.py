from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AIO_JS = ROOT / "web" / "js" / "easyuse_anima_aio.js"
AUTOCOMPLETE_JS = ROOT / "web" / "js" / "easyuse_anima_autocomplete.js"
PROMPT_STUDIO_COMMON_JS = ROOT / "web" / "js" / "easyuse_anima_prompt_studio_common.js"


class AIOFrontendSourceTests(unittest.TestCase):
    def test_generator_keeps_native_output_preview_suppressed_after_execution(self):
        source = AIO_JS.read_text(encoding="utf-8")
        registration_start = source.index("async beforeRegisterNodeDef")
        generator_block = source[source.index("if (nodeData.name === GENERATOR_NODE_TYPE)", registration_start):]
        start = generator_block.index("nodeType.prototype.onExecuted = function")
        end = generator_block.index("\n      const onResize", start)
        body = generator_block[start:end]

        self.assertIn("nodeType.prototype.hideOutputImages = true", source)
        self.assertIn("module?.useNodeOutputStore || module?.cn || module?.L", source)
        self.assertIn("outputStore.revokePreviewsByLocatorId?.(locator);", source)
        self.assertIn('Object.defineProperty(node, "imgs"', source)
        self.assertIn("lockGeneratorLegacyCanvasPreview(node);", source)
        self.assertIn(".lg-node:has(.easyuse-anima-aio-node-panel) .text-node-component-header-text", source)
        self.assertIn(".lg-node:has(.easyuse-anima-aio-node-panel) .pt-2.text-center.text-xs.text-base-foreground", source)
        self.assertIn("scheduleGeneratorDefaultPreviewSuppression(this);", body)
        self.assertIn("updateGeneratorExecutedStatus(this, message);", body)
        self.assertNotIn("onExecuted?.apply", body)

    def test_generator_preview_meta_keeps_dedicated_resolution_label(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function updateGeneratorDomPreview")
        end = source.index("\nfunction cssEscape", start)
        body = source[start:end]
        meta_start = body.index("const parts = [")
        meta_end = body.index("].filter", meta_start)
        meta_parts = body[meta_start:meta_end]

        self.assertIn("generatorPreviewImageName(currentImage)", meta_parts)
        self.assertIn("generatorPreviewResolution(currentImage)", meta_parts)
        self.assertIn("generatorPreviewFileSize(currentImage)", meta_parts)

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

    def test_upscale_settings_offer_single_backend_and_usdu_helpers(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function openUpscaleSettings")
        end = source.index("\nfunction openPostprocessSettings", start)
        body = source[start:end]

        self.assertIn('selectInput(["usdu", "resshift"]', body)
        self.assertIn('backend.value === "usdu"', body)
        self.assertIn('createStageOptimizationEditor("USDU Spectrum/DCW"', body)
        self.assertIn('"no_general"', body)
        self.assertIn('"quality_tags_only" ? "no_general"', body)
        self.assertIn("auto_tile_size: autoTile.checked", body)
        self.assertIn("auto_tile_target: Math.trunc", body)
        self.assertIn("auto_tile_min: Math.trunc", body)
        self.assertIn("auto_tile_max: Math.trunc", body)
        self.assertIn("normalizeGeneratorUsduAutoTileRange", body)
        self.assertNotIn('textContent: aioStaticText("Final Size Fit")', body)
        self.assertNotIn("fit: {", body)
        self.assertNotIn("max_long_edge: Math.trunc", body)
        self.assertNotIn("max_megapixels: clampGeneratorNumber", body)
        self.assertIn('nodeInputChoiceOptions("upscaleModelLoader", "model_name"', body)
        self.assertIn('nodeInputChoiceOptions("resShiftLoader", "student_name"', body)
        self.assertIn("upscaleBackendMissingPacks(backend.value)", body)
        self.assertIn("enabled: enabled.checked && missingPacks.length === 0", body)
        self.assertIn("resshiftSection", body)
        self.assertIn("resshift:", body)

    def test_postprocess_settings_own_final_fit_controls(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function openPostprocessSettings")
        end = source.index("\nfunction createDetailerTargetEditor", start)
        body = source[start:end]

        self.assertIn('createDialog(', body)
        self.assertIn('"Postprocess Settings"', body)
        self.assertIn('textContent: aioStaticText("Final Size Fit")', body)
        self.assertIn('"Enable postprocess"', body)
        self.assertIn('"max_long_edge"', body)
        self.assertIn('"megapixels"', body)
        self.assertIn("next.postprocess = {", body)
        self.assertIn("fit: {", body)
        self.assertIn("max_long_edge: Math.trunc", body)
        self.assertIn("max_megapixels: clampGeneratorNumber", body)
        self.assertIn("delete next.upscale?.fit", body)

    def test_upscale_optional_dependency_sanitizer_disables_missing_backend(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function sanitizeGeneratorSettingsForOptionalDependencies")
        end = source.index("\nfunction applyVisibleGeneratorSettings", start)
        body = source[start:end]

        self.assertIn("disableGeneratorSpectrumOptions(next.upscale)", body)
        self.assertIn("upscaleBackendMissingPacks(next.upscale.backend).length", body)
        self.assertIn("next.upscale.enabled = false", body)

    def test_optional_dependency_query_reports_results_without_treating_errors_as_missing(self):
        source = AIO_JS.read_text(encoding="utf-8")
        fetch_start = source.index("async function fetchGeneratorOptionalDependencies")
        fetch_end = source.index("\nfunction optionalDependencyResultLabel", fetch_start)
        fetch_body = source[fetch_start:fetch_end]
        available_start = source.index("function optionalDependencyAvailable")
        available_end = source.index("\nfunction backendDependencyMissing", available_start)
        available_body = source[available_start:available_end]
        report_start = source.index("function reportGeneratorOptionalDependencyStatus")
        report_end = source.index("\nfunction loadGeneratorOptionalDependencies", report_start)
        report_body = source[report_start:report_end]

        self.assertIn('nextStatus[key] = "error"', fetch_body)
        self.assertNotIn("next[key] = false", fetch_body)
        self.assertIn('optionalDependencyStatus(key) !== "missing"', available_body)
        self.assertIn('console.info("[EasyUseAnima] AiO optional dependency query result", rows)', report_body)
        self.assertIn('severity: failed.length ? "warn" : "info"', report_body)
        self.assertIn("app.ui.dialog.show", report_body)

    def test_optional_dependency_query_retries_errors_before_queueing(self):
        source = AIO_JS.read_text(encoding="utf-8")
        load_start = source.index("function loadGeneratorOptionalDependencies")
        load_end = source.index("\nfunction optionalDependencyStatus", load_start)
        load_body = source[load_start:load_end]
        queue_start = source.index("function installGeneratorQueuePromptHook")
        queue_end = source.index("\nfunction ensureButton", queue_start)
        queue_body = source[queue_start:queue_end]

        self.assertIn("retryErrors = false", load_body)
        self.assertIn('includes("error")', load_body)
        self.assertIn("generatorOptionalDependencyState.loading = null", load_body)
        self.assertIn("loadGeneratorOptionalDependencies({ retryErrors: true })", queue_body)

    def test_generator_panel_renders_upscale_after_detailer(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function renderGeneratorPanel")
        end = source.index("\nfunction ensureGeneratorPanel", start)
        body = source[start:end]

        self.assertLess(body.index("const detailerBlock"), body.index("const upscaleBlock"))
        self.assertLess(body.index("const upscaleBlock"), body.index("const postprocessBlock"))
        self.assertIn("settingsScroll.append(samplerGrid, highresBlock, detailerBlock, upscaleBlock, postprocessBlock)", body)
        self.assertIn("openUpscaleSettings(node)", body)
        self.assertIn("openPostprocessSettings(node)", body)
        self.assertIn("settings.upscale.steps", body)
        self.assertIn("settings.upscale.denoise", body)
        self.assertIn("usdu.auto_tile_size", body)
        self.assertIn("usdu.auto_tile_target", body)
        self.assertIn("setGeneratorUsduAutoTileTarget(nextSettings, value)", body)
        self.assertNotIn("backendBadge", body)

    def test_safe_pag_advanced_labels_do_not_reuse_generic_labels(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function openAdvancedSettings")
        end = source.index("\nfunction openGeneratorSettings", start)
        body = source[start:end]

        self.assertIn('"Safe PAG scale"', body)
        self.assertIn('"Safe PAG blocks"', body)
        self.assertIn('"PAG perturbation"', body)
        self.assertIn('"PAG start percent"', body)
        self.assertIn('"PAG end percent"', body)
        self.assertIn('"PAG rescale"', body)
        self.assertNotIn('field(safePag, "Scale"', body)
        self.assertNotIn('field(safePag, "Start"', body)
        self.assertNotIn('field(safePag, "End"', body)
        self.assertNotIn('field(safePag, "Rescale"', body)

    def test_save_settings_expose_prompt_metadata_toggle(self):
        source = AIO_JS.read_text(encoding="utf-8")
        defaults_start = source.index("const DEFAULT_GENERATION_SETTINGS")
        defaults_end = source.index("\nconst AIO_TEXT", defaults_start)
        defaults_body = source[defaults_start:defaults_end]
        start = source.index("function openSaveSettings")
        end = source.index("\nfunction openAdvancedSettings", start)
        body = source[start:end]

        self.assertIn("save_prompt_metadata: true", defaults_body)
        self.assertIn('field(metadata, "Save prompt metadata"', body)
        self.assertIn("checkbox(imageSaver.save_prompt_metadata)", body)
        self.assertIn("save_prompt_metadata: savePromptMetadata.checked", body)
        self.assertIn('"Save prompt metadata": "tip.savePromptMetadata"', source)

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
        self.assertIn("candidateKey.includes(query)", body)

    def test_autocomplete_refreshes_during_ime_composition_without_committing(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("  const updateNow = async () => {")
        end = source.index("  const update = debounce(updateNow);", start)
        update_body = source[start:end]

        self.assertIn("document.activeElement !== input", update_body)
        self.assertNotIn("composing || document.activeElement", update_body)
        self.assertIn('input.addEventListener("compositionupdate", update);', source)

        autocomplete_done = source.index("  input.__easyuseAnimaAutocompleteHooked = true;")
        keydown_start = source.rindex('  input.addEventListener("keydown", (event) => {', 0, autocomplete_done)
        keydown_end = source.index("  });", keydown_start)
        keydown_body = source[keydown_start:keydown_end]

        self.assertIn("event.isComposing", keydown_body)
        self.assertIn("event.keyCode === 229", keydown_body)
        self.assertLess(
            keydown_body.index("event.isComposing"),
            keydown_body.index("!activeState"),
        )

    def test_autocomplete_public_flag_tracks_enabled_state(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")

        self.assertIn("const hookedAutocompleteInputs = new Set();", source)
        self.assertIn("input.__easyuseAnimaAutocompleteHooked", source)
        self.assertNotIn("if (input.__easyuseAnimaAutocomplete) {", source)

        start = source.index("function syncAutocompleteInputFlag")
        end = source.index("\nasync function refreshAutocompleteSettings", start)
        sync_body = source[start:end]

        self.assertIn("input.__easyuseAnimaAutocomplete = autocompleteEnabledForState(state);", sync_body)
        self.assertIn("hookedAutocompleteInputs.delete(input);", sync_body)

        start = source.index("function setAutocompleteMode")
        end = source.index("\nfunction isEasyUseAnimaNode", start)
        mode_body = source[start:end]

        self.assertIn("syncAutocompleteInputFlags();", mode_body)

        start = source.index("function hookInput")
        end = source.index("\nfunction hookWidget", start)
        hook_body = source[start:end]

        self.assertIn("if (input.__easyuseAnimaAutocompleteHooked) {", hook_body)
        self.assertIn("syncAutocompleteInputFlag(input, existing);", hook_body)
        self.assertIn("hookedAutocompleteInputs.add(input);", hook_body)
        self.assertIn("syncAutocompleteInputFlag(input, state);", hook_body)

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

    def test_autocomplete_resets_scroll_for_new_result_sets(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("function hidePopup")
        end = source.index("\nfunction hideTrainedTagTooltips", start)
        hide_body = source[start:end]

        self.assertIn("markAutocompleteInputInactive(input);", hide_body)
        self.assertIn("resetAutocompleteMenuToTop(popup);", hide_body)
        self.assertLess(hide_body.index("popup.replaceChildren();"), hide_body.index("resetAutocompleteMenuToTop(popup);"))
        self.assertLess(hide_body.index("resetAutocompleteMenuToTop(popup);"), hide_body.index('popup.classList.add("hidden");'))

        start = source.index("function markAutocompleteInputInactive")
        end = source.index("\nfunction hideTrainedTagTooltips", start)
        inactive_body = source[start:end]

        self.assertIn('state.lastAutocompleteSignature = "";', inactive_body)

        self.assertIn("overflow-anchor: none;", source)

        start = source.index("function resetAutocompleteMenuToTop")
        end = source.index("\nfunction resetActiveAutocompleteMenu", start)
        reset_top_body = source[start:end]

        self.assertIn("menu.scrollTop = 0;", reset_top_body)
        self.assertIn("menu.scrollLeft = 0;", reset_top_body)

        start = source.index("function resetActiveAutocompleteMenu")
        end = source.index("\nfunction resetVisibleAutocompleteMenuSoon", start)
        reset_body = source[start:end]

        self.assertIn("activeState.index = 0;", reset_body)
        self.assertIn("resetAutocompleteMenuToTop(menu);", reset_body)

        start = source.index("function resetVisibleAutocompleteMenuSoon")
        end = source.index("\nfunction endsWithSentencePeriod", start)
        visible_reset_body = source[start:end]

        self.assertIn("resetAutocompleteMenuToTop(menu);", visible_reset_body)
        self.assertIn("requestAnimationFrame(() => {", visible_reset_body)
        self.assertIn('!menu.classList.contains("hidden")', visible_reset_body)
        self.assertNotIn("resetActiveAutocompleteMenu(menu);", visible_reset_body)

        start = source.index("function renderResults")
        end = source.index("\nfunction isCaretInComment", start)
        body = source[start:end]

        self.assertIn("resetAutocompleteMenuToTop(menu);", body)
        self.assertIn("index: 0,", body)
        self.assertIn('menu.classList.remove("hidden");', body)
        self.assertIn("resetActiveAutocompleteMenu(menu);", body)
        self.assertIn("resetVisibleAutocompleteMenuSoon(menu, state.input);", body)
        self.assertLess(body.index("resetAutocompleteMenuToTop(menu);"), body.index("menu.replaceChildren();"))
        self.assertLess(body.index("menu.replaceChildren();"), body.index("resetActiveAutocompleteMenu(menu);"))
        self.assertLess(body.index("resetActiveAutocompleteMenu(menu);"), body.index("positionPopup(state.input);"))
        self.assertLess(body.index('menu.classList.remove("hidden");'), body.rindex("resetActiveAutocompleteMenu(menu);"))
        self.assertLess(body.index('menu.classList.remove("hidden");'), body.index("resetVisibleAutocompleteMenuSoon(menu, state.input);"))
        self.assertLess(body.index("resetVisibleAutocompleteMenuSoon(menu, state.input);"), body.index("updateAutocompletePreview();"))

        start = source.index("  const updateNow = async () => {")
        end = source.index("    const seq = ++updateSeq;", start)
        update_body = source[start:end]

        self.assertIn("lastAutocompleteSignature: undefined", source)
        self.assertIn("const previousSignature = state.lastAutocompleteSignature;", update_body)
        self.assertIn("state.lastAutocompleteSignature = signature;", update_body)
        self.assertIn("previousSignature !== undefined && previousSignature !== signature", update_body)
        self.assertIn("resetActiveAutocompleteMenu(ensurePopup());", update_body)

        start = source.index("function handleOutsideAutocompletePointer")
        end = source.index("\ndocument.addEventListener(\"pointerdown\"", start)
        pointer_body = source[start:end]

        self.assertIn("popup?.contains(event.target)", pointer_body)
        self.assertIn("event.target === input", pointer_body)
        self.assertIn("markAutocompleteInputInactive(input);", pointer_body)
        self.assertIn("hidePopup();", pointer_body)
        self.assertIn('document.addEventListener("pointerdown", handleOutsideAutocompletePointer, true);', source)
        self.assertIn('document.addEventListener("mousedown", handleOutsideAutocompletePointer, true);', source)

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

    def test_autocomplete_strips_prompt_syntax_from_search_query(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")

        start = source.index("function autocompleteQuery")
        end = source.index("\nfunction wildcardAutocompleteQuery", start)
        query_body = source[start:end]

        self.assertIn("const query = parsed.query;", query_body)
        self.assertNotIn("artistOnly ? parsed.query : raw.trim()", query_body)

        start = source.index("function parseAutocompleteText")
        end = source.index("\nfunction normalizeWildcardSearchText", start)
        parse_body = source[start:end]

        self.assertIn('query = query.replace(/^\\[\\[\\s*/g, "");', parse_body)
        self.assertIn('query = query.replace(/^\\(\\s*/g, "");', parse_body)
        self.assertIn("query = stripPromptSyntaxClosingParens(query);", parse_body)
        self.assertIn(
            'query = query.replace(/:\\s*[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)\\s*$/, "");',
            parse_body,
        )
        self.assertNotIn('query = query.replace(/\\)+\\s*$/, "");', parse_body)

        start = source.index("function trimPromptSyntaxSuffix")
        end = source.index("\nfunction currentToken", start)
        trim_body = source[start:end]

        self.assertIn('value[cursor - 1] === ")" && !isEscaped(value, cursor - 1)', trim_body)

    def test_autocomplete_supports_nodes_v2_specs_and_dom_widgets(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")

        start = source.index("function inputTypeName")
        end = source.index("\nfunction isExcludedInput", start)
        spec_body = source[start:end]

        self.assertIn("inputSpec.widgetType || inputSpec.type", spec_body)
        self.assertIn("nodeData?.inputs", spec_body)
        self.assertIn("inputSpec.options || {}", spec_body)
        self.assertIn("typeNames.some((item) => item === \"STRING\" || item === \"TEXTAREA\")", source)
        self.assertIn("typeNames.includes(\"TEXTAREA\")", source)

        start = source.index("function findInputEl")
        end = source.index("\nfunction isEscaped", start)
        input_body = source[start:end]

        self.assertIn("widget?.inputEl || widget?.element", input_body)
        self.assertIn('querySelector?.("textarea, input")', input_body)

    def test_autocomplete_avoids_double_callback_for_nodes_v2_dom_widgets(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("function widgetValueSetterCallsCallback")
        end = source.index("\nfunction renderResults", start)
        sync_body = source[start:end]

        self.assertIn("return !!widget?.element;", sync_body)
        self.assertIn("state.widget.value = state.input.value;", sync_body)
        self.assertIn("if (!widgetValueSetterCallsCallback(state.widget))", sync_body)
        self.assertIn("syncWidgetValue(state);", source)
        self.assertNotIn("state.widget.callback?.(state.input.value);", source[:source.index("function widgetValueSetterCallsCallback")])

    def test_autocomplete_hooks_focused_nodes_v2_dom_inputs(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("function hookFocusedDomInput")
        end = source.index("\nfunction installExternalInputHook", start)
        focus_body = source[start:end]

        self.assertIn("isAutocompleteDomInput(input)", focus_body)
        self.assertIn("const node = nodeFromDomElement(input);", focus_body)
        self.assertIn("if (!node)", focus_body)
        self.assertIn("const targets = nodeData ? targetWidgets(nodeData) : null;", focus_body)
        self.assertIn("const widget = widgetForDomInput(node, input);", focus_body)
        self.assertIn("hookInput(input", focus_body)
        self.assertIn('document.addEventListener("focusin"', source)
        self.assertIn("hookFocusedDomInput(document.activeElement);", source)
        self.assertNotIn("easyuseAnimaDebugAutocomplete", source)

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
