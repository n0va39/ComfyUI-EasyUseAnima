from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSCONFIG = ROOT / "jsconfig.json"
FRONTEND_CHECK_SCRIPT = ROOT / "tools" / "check_frontend.ps1"
WEB_JS = ROOT / "web" / "js"
API_JS = WEB_JS / "easyuse_anima_api.js"
PROMPT_STUDIO_JS = WEB_JS / "easyuse_anima_prompt_studio.js"
PROMPT_STUDIO_COMMON_JS = WEB_JS / "easyuse_anima_prompt_studio_common.js"
PROMPT_STUDIO_MODULES = WEB_JS / "prompt_studio"
PROMPT_STUDIO_HIGHLIGHT_JS = PROMPT_STUDIO_MODULES / "highlight.js"
PROMPT_STUDIO_HIGHLIGHT_CORE_JS = PROMPT_STUDIO_MODULES / "highlight_core.js"
PROMPT_STUDIO_HIGHLIGHT_OVERLAY_CORE_JS = (
    PROMPT_STUDIO_MODULES / "highlight_overlay_core.js"
)
PROMPT_STUDIO_REGIONAL_JS = WEB_JS / "easyuse_anima_prompt_studio_regional.js"
PROMPT_STUDIO_REGIONAL_MODULES = PROMPT_STUDIO_MODULES / "regional"
PROMPT_STUDIO_REGIONAL_PURE_DATA_SMOKE = (
    ROOT / "tests" / "frontend_regional_pure_data_smoke.mjs"
)
STATIC_IMPORT_RE = re.compile(r"""from\s+["'](\./[^"']+\.js)["']""")


class FrontendModuleStructureTests(unittest.TestCase):
    def test_shared_api_module_exports_runtime_helpers(self):
        source = API_JS.read_text(encoding="utf-8")

        for name in (
            "easyuseAnimaFetchJson",
            "easyuseAnimaGetSettings",
            "easyuseAnimaPostJson",
            "easyuseAnimaClassifyPrompt",
            "easyuseAnimaEncodeRFC3986URIComponent",
            "easyuseAnimaFetchComfyJson",
            "easyuseAnimaFetchText",
        ):
            self.assertRegex(source, rf"export (?:async )?function {name}\(")

    def test_feature_scripts_use_shared_api_module(self):
        expected_imports = {
            "easyuse_anima_autocomplete.js": './easyuse_anima_api.js"',
            "easyuse_anima_lora_preset.js": './easyuse_anima_api.js"',
            "easyuse_anima_aio.js": './easyuse_anima_api.js"',
            "easyuse_anima_prompt_studio_common.js": './easyuse_anima_api.js"',
            "easyuse_anima_settings.js": './easyuse_anima_api.js"',
            "prompt_studio/highlight.js": '../easyuse_anima_api.js"',
        }

        for filename, import_path in expected_imports.items():
            with self.subTest(filename=filename):
                source = (WEB_JS / filename).read_text(encoding="utf-8")
                self.assertIn(import_path, source)

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

    def test_fetch_access_is_centralized(self):
        for path in WEB_JS.rglob("*.js"):
            if path.name == "easyuse_anima_api.js":
                continue
            with self.subTest(filename=str(path.relative_to(WEB_JS))):
                source = path.read_text(encoding="utf-8")
                self.assertNotRegex(source, r"\bfetch\s*\(")
                self.assertNotIn("XMLHttpRequest", source)
                self.assertNotIn("new Function", source)

    def test_registry_scanner_sensitive_bind_pattern_is_not_used(self):
        for path in WEB_JS.rglob("*.js"):
            with self.subTest(filename=str(path.relative_to(WEB_JS))):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn(".bind(", source)

    def test_prompt_studio_entry_imports_phase_2_modules(self):
        source = PROMPT_STUDIO_JS.read_text(encoding="utf-8")
        extension_runtime_source = (
            PROMPT_STUDIO_MODULES / "extension_runtime.js"
        ).read_text(encoding="utf-8")
        advanced_fields_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_fields_ui.js"
        ).read_text(encoding="utf-8")
        studio_node_ui_source = (
            PROMPT_STUDIO_MODULES / "studio_node_ui.js"
        ).read_text(encoding="utf-8")
        advanced_node_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_node_ui.js"
        ).read_text(encoding="utf-8")

        self.assertIn("app.registerExtension", source)
        self.assertIn('./prompt_studio/extension_runtime.js"', source)
        self.assertIn("./constants.js", extension_runtime_source)
        self.assertIn('./advanced_controls.js"', advanced_node_ui_source)
        self.assertIn("./advanced_node_ui.js", extension_runtime_source)
        self.assertIn('./advanced_fields_ui.js"', advanced_node_ui_source)
        self.assertIn("./advanced_fields_state.js", extension_runtime_source)
        self.assertIn("./advanced_values.js", extension_runtime_source)
        self.assertIn('./utils.js"', studio_node_ui_source)
        self.assertIn("./canvas_forwarding.js", extension_runtime_source)
        self.assertIn("./extend_slot_controls.js", extension_runtime_source)
        self.assertIn("./extend_slots.js", extension_runtime_source)
        self.assertIn("./extend_layout.js", extension_runtime_source)
        self.assertIn('./fields.js"', advanced_fields_ui_source)
        self.assertIn("./advanced_highlights.js", extension_runtime_source)
        self.assertIn("./highlight.js", extension_runtime_source)
        self.assertIn("./highlight_ui.js", extension_runtime_source)
        self.assertIn("./legend.js", extension_runtime_source)
        self.assertIn("./node_hooks.js", extension_runtime_source)
        self.assertIn("./settings.js", extension_runtime_source)
        self.assertIn('./style.js"', advanced_node_ui_source)
        self.assertIn('./text.js"', studio_node_ui_source)
        self.assertIn("./tooltip.js", extension_runtime_source)
        self.assertIn("./widgets.js", extension_runtime_source)
        self.assertIn("./layout.js", extension_runtime_source)
        self.assertIn("./advanced_layout_controller.js", extension_runtime_source)
        self.assertIn("./studio_resizable_input.js", extension_runtime_source)
        self.assertIn("./studio_textareas.js", extension_runtime_source)
        self.assertIn("./studio_node_ui.js", extension_runtime_source)
        self.assertIn("./studio_values.js", extension_runtime_source)
        self.assertIn("./wildcard_values.js", extension_runtime_source)
        self.assertIn('./textarea.js"', advanced_fields_ui_source)
        self.assertIn('./wheel.js"', advanced_node_ui_source)
        self.assertIn("./serialization.js", extension_runtime_source)
        self.assertIn("./runtime_canvas.js", extension_runtime_source)

    def test_prompt_highlight_parser_and_renderer_are_shared(self):
        core_source = PROMPT_STUDIO_HIGHLIGHT_CORE_JS.read_text(encoding="utf-8")
        modular_source = PROMPT_STUDIO_HIGHLIGHT_JS.read_text(encoding="utf-8")
        regional_source = PROMPT_STUDIO_COMMON_JS.read_text(encoding="utf-8")
        constants_source = (PROMPT_STUDIO_MODULES / "constants.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('from "./highlight_core.js"', modular_source)
        self.assertIn(
            'from "./prompt_studio/highlight_core.js"', regional_source
        )
        self.assertIn("preferSyntaxBeforeToken: false", modular_source)
        self.assertIn("preferSyntaxBeforeToken: true", regional_source)
        self.assertIn("  createPromptHighlightRenderer,", core_source)

        for name in (
            "normalize",
            "splitPromptText",
            "artistMixGroupParts",
            "findTokenMatch",
            "renderSequentialBody",
            "renderHighlightedText",
        ):
            with self.subTest(symbol=name):
                self.assertIn(f"function {name}", core_source)
                self.assertNotIn(f"function {name}", modular_source)
                self.assertNotIn(f"function {name}", regional_source)

        for source in (modular_source, regional_source, constants_source):
            self.assertNotIn("WILDCARD_HIGHLIGHT_RE", source)

    def test_prompt_highlight_overlay_core_is_shared(self):
        core_source = PROMPT_STUDIO_HIGHLIGHT_OVERLAY_CORE_JS.read_text(
            encoding="utf-8"
        )
        modular_source = PROMPT_STUDIO_HIGHLIGHT_JS.read_text(encoding="utf-8")
        regional_source = PROMPT_STUDIO_COMMON_JS.read_text(encoding="utf-8")
        constants_source = (PROMPT_STUDIO_MODULES / "constants.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('from "./highlight_overlay_core.js"', modular_source)
        self.assertIn(
            'from "./prompt_studio/highlight_overlay_core.js"', regional_source
        )
        for source in (modular_source, regional_source):
            self.assertIn(
                "const highlightOverlayHtml = createHighlightOverlayRenderer({",
                source,
            )

        for name in (
            "cssPixelNumber",
            "cssPixel",
            "overlayScrollbarPadding",
            "applyOverlayScrollbarPadding",
            "overlayBounds",
            "autocompletePreviewSpanHtml",
            "highlightOverlayPreviewHtml",
            "highlightOverlayHtml",
            "copyInputTextMetrics",
            "syncOverlayBounds",
        ):
            with self.subTest(symbol=name):
                self.assertIn(f"function {name}", core_source)
                self.assertNotIn(f"function {name}", modular_source)
                self.assertNotIn(f"function {name}", regional_source)

        self.assertIn("const HIGHLIGHT_TEXT_METRIC_PROPERTIES", core_source)
        for source in (modular_source, regional_source, constants_source):
            self.assertNotIn("const HIGHLIGHT_TEXT_METRIC_PROPERTIES", source)

        for name in (
            "HIGHLIGHT_TEXT_METRIC_PROPERTIES",
            "copyInputTextMetrics",
            "createHighlightOverlayRenderer",
            "overlayBounds",
            "overlayScrollbarPadding",
            "syncOverlayBounds",
        ):
            with self.subTest(export=name):
                self.assertIn(f"  {name},", core_source)

    def test_regional_pure_data_modules_own_dom_free_rules(self):
        entry_source = PROMPT_STUDIO_REGIONAL_JS.read_text(encoding="utf-8")
        common_source = PROMPT_STUDIO_COMMON_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")
        expected_modules = {
            "constants.js": (
                "REGIONAL_WIDGET_INDEX",
                "PROMPT_STUDIO_RESOLUTION_BUCKETS",
                "PROMPT_STUDIO_VARIANT_FIELD_TYPES",
            ),
            "resolution.js": (
                "ratioLabel",
                "normalizeResolutionBucket",
                "readRegionalResolutionValues",
            ),
            "schema.js": (
                "createDefaultRegionalFields",
                "normalizeRegionalField",
                "normalizeRegionalConfig",
            ),
            "serialization.js": (
                "normalizeRegionalFieldsString",
                "normalizeRegionalConfigString",
                "serializedRegionalValue",
            ),
            "mask_geometry.js": (
                "normalizeGeometry",
                "findMaskAt",
                "moveGeometry",
                "resizeGeometry",
            ),
        }

        for filename, symbols in expected_modules.items():
            with self.subTest(module=filename):
                path = PROMPT_STUDIO_REGIONAL_MODULES / filename
                self.assertTrue(path.is_file())
                source = path.read_text(encoding="utf-8")
                self.assertTrue(source.startswith("// @ts-check"))
                self.assertNotRegex(source, r"\b(?:document|window|app)\b")
                for symbol in symbols:
                    self.assertRegex(
                        source,
                        rf"export (?:const|function) {symbol}\b",
                    )
                self.assertIn(
                    f'./prompt_studio/regional/{filename}"',
                    entry_source,
                )

        for name in (
            "ratioLabel",
            "resolutionLabel",
            "resolutionOptions",
            "normalizeResolutionBucket",
            "normalizeResolutionSize",
            "snapResolution32",
            "defaultFields",
            "normalizeMaskIds",
            "normalizeField",
            "normalizeFieldsValue",
            "normalizeGeometry",
            "geometryToCanvasRect",
            "maskHandlePoints",
            "findMaskHandleAt",
            "findMaskAt",
            "moveGeometry",
            "resizeGeometry",
        ):
            with self.subTest(extracted=name):
                self.assertNotIn(f"function {name}", entry_source)

        self.assertIn(
            'from "./prompt_studio/regional/constants.js"',
            common_source,
        )
        self.assertNotIn(
            "export const PROMPT_STUDIO_RESOLUTION_BUCKETS",
            common_source,
        )
        self.assertTrue(PROMPT_STUDIO_REGIONAL_PURE_DATA_SMOKE.is_file())
        self.assertIn(
            'node "tests\\frontend_regional_pure_data_smoke.mjs"',
            frontend_check_source,
        )

        write_fields_source = entry_source[
            entry_source.index("function writeRegionalFields"):
            entry_source.index("function writeRegionalConfig")
        ]
        write_config_source = entry_source[
            entry_source.index("function writeRegionalConfig"):
            entry_source.index("function updateRegionalConfigCanvas")
        ]
        self.assertIn("if (syncInputs)", write_fields_source)
        self.assertIn("syncRegionalFieldInputs(node, normalized)", write_fields_source)
        self.assertNotIn("syncRegionalFieldInputs", write_config_source)

    def test_prompt_studio_phase_2_modules_export_expected_symbols(self):
        advanced_controls_source = (
            PROMPT_STUDIO_MODULES / "advanced_controls.js"
        ).read_text(encoding="utf-8")
        advanced_fields_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_fields_ui.js"
        ).read_text(encoding="utf-8")
        advanced_fields_state_source = (
            PROMPT_STUDIO_MODULES / "advanced_fields_state.js"
        ).read_text(encoding="utf-8")
        advanced_values_source = (
            PROMPT_STUDIO_MODULES / "advanced_values.js"
        ).read_text(encoding="utf-8")
        constants_source = (PROMPT_STUDIO_MODULES / "constants.js").read_text(
            encoding="utf-8"
        )
        utils_source = (PROMPT_STUDIO_MODULES / "utils.js").read_text(
            encoding="utf-8"
        )
        schema_source = (PROMPT_STUDIO_MODULES / "schema.js").read_text(
            encoding="utf-8"
        )
        state_source = (PROMPT_STUDIO_MODULES / "state.js").read_text(
            encoding="utf-8"
        )
        canvas_forwarding_source = (
            PROMPT_STUDIO_MODULES / "canvas_forwarding.js"
        ).read_text(encoding="utf-8")
        dom_source = (PROMPT_STUDIO_MODULES / "dom.js").read_text(
            encoding="utf-8"
        )
        extend_slot_controls_source = (
            PROMPT_STUDIO_MODULES / "extend_slot_controls.js"
        ).read_text(encoding="utf-8")
        extend_slots_source = (
            PROMPT_STUDIO_MODULES / "extend_slots.js"
        ).read_text(encoding="utf-8")
        extend_layout_source = (
            PROMPT_STUDIO_MODULES / "extend_layout.js"
        ).read_text(encoding="utf-8")
        fields_source = (PROMPT_STUDIO_MODULES / "fields.js").read_text(
            encoding="utf-8"
        )
        highlight_source = (PROMPT_STUDIO_MODULES / "highlight.js").read_text(
            encoding="utf-8"
        )
        highlight_ui_source = (
            PROMPT_STUDIO_MODULES / "highlight_ui.js"
        ).read_text(encoding="utf-8")
        legend_source = (PROMPT_STUDIO_MODULES / "legend.js").read_text(
            encoding="utf-8"
        )
        node_hooks_source = (PROMPT_STUDIO_MODULES / "node_hooks.js").read_text(
            encoding="utf-8"
        )
        settings_source = (PROMPT_STUDIO_MODULES / "settings.js").read_text(
            encoding="utf-8"
        )
        style_source = (PROMPT_STUDIO_MODULES / "style.js").read_text(
            encoding="utf-8"
        )
        text_source = (PROMPT_STUDIO_MODULES / "text.js").read_text(
            encoding="utf-8"
        )
        tooltip_source = (PROMPT_STUDIO_MODULES / "tooltip.js").read_text(
            encoding="utf-8"
        )
        widgets_source = (PROMPT_STUDIO_MODULES / "widgets.js").read_text(
            encoding="utf-8"
        )
        layout_source = (PROMPT_STUDIO_MODULES / "layout.js").read_text(
            encoding="utf-8"
        )
        advanced_layout_controller_source = (
            PROMPT_STUDIO_MODULES / "advanced_layout_controller.js"
        ).read_text(encoding="utf-8")
        advanced_node_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_node_ui.js"
        ).read_text(encoding="utf-8")
        advanced_highlights_source = (
            PROMPT_STUDIO_MODULES / "advanced_highlights.js"
        ).read_text(encoding="utf-8")
        studio_textareas_source = (
            PROMPT_STUDIO_MODULES / "studio_textareas.js"
        ).read_text(encoding="utf-8")
        studio_resizable_input_source = (
            PROMPT_STUDIO_MODULES / "studio_resizable_input.js"
        ).read_text(encoding="utf-8")
        studio_node_ui_source = (
            PROMPT_STUDIO_MODULES / "studio_node_ui.js"
        ).read_text(encoding="utf-8")
        studio_values_source = (
            PROMPT_STUDIO_MODULES / "studio_values.js"
        ).read_text(encoding="utf-8")
        wildcard_values_source = (
            PROMPT_STUDIO_MODULES / "wildcard_values.js"
        ).read_text(encoding="utf-8")
        textarea_source = (PROMPT_STUDIO_MODULES / "textarea.js").read_text(
            encoding="utf-8"
        )
        wheel_source = (PROMPT_STUDIO_MODULES / "wheel.js").read_text(
            encoding="utf-8"
        )
        serialization_source = (
            PROMPT_STUDIO_MODULES / "serialization.js"
        ).read_text(encoding="utf-8")
        runtime_canvas_source = (
            PROMPT_STUDIO_MODULES / "runtime_canvas.js"
        ).read_text(encoding="utf-8")
        extension_runtime_source = (
            PROMPT_STUDIO_MODULES / "extension_runtime.js"
        ).read_text(encoding="utf-8")

        for name in (
            "advancedCustomResolution",
            "advancedResolutionSummary",
            "advancedWildcardSummary",
            "createAdvancedControlBar",
            "createAdvancedResolutionBar",
            "createAdvancedWildcardBar",
            "setAdvancedControlValue",
            "setAdvancedWidgetValue",
        ):
            with self.subTest(module="advanced_controls", symbol=name):
                self.assertIn(f"  {name},", advanced_controls_source)

        for name in (
            "addAdvancedField",
            "createAdvancedFieldElement",
            "createAdvancedPane",
            "remeasureAdvancedTextareaHeightsForWidth",
            "setAdvancedTextareaHeight",
        ):
            with self.subTest(module="advanced_fields_ui", symbol=name):
                self.assertIn(f"  {name},", advanced_fields_ui_source)

        for name in (
            "advancedFieldLabel",
            "advancedWidget",
            "applyAdvancedNaiaGeneralAutoToggle",
            "hideAdvancedControlWidgets",
            "hideAdvancedInternalWidget",
            "parseAdvancedFields",
            "removeAdvancedInternalInputSockets",
            "repairAdvancedInternalWidgetValues",
            "writeAdvancedFields",
        ):
            with self.subTest(module="advanced_fields_state", symbol=name):
                self.assertIn(f"  {name},", advanced_fields_state_source)

        for name in (
            "applyAdvancedExecutedInputs",
            "syncAdvancedValues",
        ):
            with self.subTest(module="advanced_values", symbol=name):
                self.assertIn(f"  {name},", advanced_values_source)

        for name in (
            "NODE_TYPE",
            "ADVANCED_NODE_TYPE",
            "PROMPT_STUDIO_TEXT",
            "ADVANCED_FIELDS_PROPERTY",
            "ADVANCED_DEFAULT_FIELDS",
        ):
            with self.subTest(module="constants", symbol=name):
                self.assertIn(f"  {name},", constants_source)

        for name in (
            "debounce",
            "escapeHtml",
            "escapeAttr",
            "parseColorSettings",
            "advancedResolutionLabel",
            "snapResolution32",
        ):
            with self.subTest(module="utils", symbol=name):
                self.assertIn(f"  {name},", utils_source)

        for name in (
            "advancedDefaultFields",
            "advancedDefaultFieldsValue",
            "normalizeAdvancedField",
            "normalizeAdvancedFieldsValue",
            "normalizeAdvancedWidgetQueueValue",
            "advancedFieldInputName",
            "normalizeAdvancedResolutionBucket",
            "normalizeAdvancedResolutionSize",
        ):
            with self.subTest(module="schema", symbol=name):
                self.assertIn(f"  {name},", schema_source)

        for name in (
            "findHiddenWidget",
            "getAdvancedEditorElement",
            "setAdvancedEditorElement",
            "getAdvancedFields",
            "setAdvancedFields",
            "setPendingAdvancedFieldsValue",
            "clearPendingAdvancedFieldsValue",
        ):
            with self.subTest(module="state", symbol=name):
                self.assertIn(f"  {name},", state_source)

        for name in (
            "forwardAdvancedWheelToCanvas",
            "installAdvancedWheelForwarder",
            "installMiddlePanForwarder",
        ):
            with self.subTest(module="canvas_forwarding", symbol=name):
                self.assertIn(f"  {name},", canvas_forwarding_source)

        for name in (
            "closeAdvancedHelpPopovers",
            "openAdvancedHelpPopover",
            "protectAdvancedNativeControl",
            "stopAdvancedControlEvent",
            "updateAdvancedSummary",
        ):
            with self.subTest(module="dom", symbol=name):
                self.assertIn(f"  {name},", dom_source)

        for name in (
            "ensureExtendSlotControls",
            "measureExtendSlotControlsHeight",
            "renderExtendSlotControls",
        ):
            with self.subTest(module="extend_slot_controls", symbol=name):
                self.assertIn(f"  {name},", extend_slot_controls_source)

        for name in (
            "applyExtendSlotVisibility",
            "extendSlotShouldShow",
            "extendVisibleSlots",
            "parseExtendSlots",
            "writeExtendVisibleSlots",
        ):
            with self.subTest(module="extend_slots", symbol=name):
                self.assertIn(f"  {name},", extend_slots_source)

        for name in (
            "firstExtendPromptY",
            "layoutExtendPromptWidgets",
            "visibleExtendPromptWidgets",
        ):
            with self.subTest(module="extend_layout", symbol=name):
                self.assertIn(f"  {name},", extend_layout_source)

        for name in (
            "advancedPaneFields",
            "hasAdvancedNaia",
            "hasPositiveNaia",
            "hasPositiveTrigger",
            "moveAdvancedFieldInPane",
        ):
            with self.subTest(module="fields", symbol=name):
                self.assertIn(f"  {name},", fields_source)

        for name in (
            "classifyPrompt",
            "ensureHighlightOverlay",
            "highlightOverlayHtml",
            "installPromptHighlightOverlayRefresh",
            "overlayScrollbarPadding",
            "refreshAllPromptHighlights",
            "requestOverlaySync",
        ):
            with self.subTest(module="highlight", symbol=name):
                self.assertIn(f"  {name},", highlight_source)

        for name in (
            "displayText",
            "updateHighlight",
        ):
            with self.subTest(module="highlight_ui", symbol=name):
                self.assertIn(f"  {name},", highlight_ui_source)

        for name in (
            "desiredLegendHeight",
            "ensureLegendWidget",
        ):
            with self.subTest(module="legend", symbol=name):
                self.assertIn(f"  {name},", legend_source)

        for name in (
            "isAdvancedNode",
            "isAdvancedNodeName",
            "isExtendNode",
            "isPromptStudioNodeName",
            "isWildcardNode",
            "installAdvancedSaveSync",
            "registerPromptStudioNodeHooks",
            "syncAdvancedNodes",
        ):
            with self.subTest(module="node_hooks", symbol=name):
                self.assertIn(f"  {name},", node_hooks_source)

        for name in (
            "PROMPT_STUDIO_SETTINGS",
            "applyPromptStudioSettings",
            "applyPromptStudioTextStyle",
            "loadPromptStudioSettings",
        ):
            with self.subTest(module="settings", symbol=name):
                self.assertIn(f"  {name},", settings_source)

        for name in (
            "ensureAdvancedStyle",
            "ensureExtendSlotStyle",
            "ensureHighlightStyle",
            "ensureTrainedTagTooltipStyle",
        ):
            with self.subTest(module="style", symbol=name):
                self.assertIn(f"  {name},", style_source)

        for name in (
            "psFormat",
            "psText",
            "sectionLabel",
        ):
            with self.subTest(module="text", symbol=name):
                self.assertIn(f"  {name},", text_source)

        for name in (
            "hideTrainedTagTooltip",
            "installTrainedTagTooltipListeners",
        ):
            with self.subTest(module="tooltip", symbol=name):
                self.assertIn(f"  {name},", tooltip_source)

        for name in (
            "findInputEl",
            "findWidget",
            "firstValue",
            "isWidgetInputLinked",
        ):
            with self.subTest(module="widgets", symbol=name):
                self.assertIn(f"  {name},", widgets_source)

        for name in (
            "advancedEditorWidth",
            "advancedTextareaContentHeight",
            "advancedTextareaCurrentHeight",
            "advancedTextareaMinimumHeight",
            "updateAdvancedEditorWidth",
        ):
            with self.subTest(module="layout", symbol=name):
                self.assertIn(f"  {name},", layout_source)

        for name in (
            "applyAdvancedLayout",
            "clearAdvancedResizeEndListeners",
            "disconnectAdvancedEditorWidthObserver",
            "finalizeAdvancedResize",
            "installAdvancedResizeEndListeners",
            "observeAdvancedEditorWidth",
            "scheduleAdvancedLayout",
            "scheduleAdvancedResizeFinalize",
        ):
            with self.subTest(module="advanced_layout_controller", symbol=name):
                self.assertIn(f"  {name},", advanced_layout_controller_source)

        for name in (
            "hookAdvancedNode",
            "renderAdvancedEditor",
            "scheduleHookAdvancedNode",
        ):
            with self.subTest(module="advanced_node_ui", symbol=name):
                self.assertIn(f"  {name},", advanced_node_ui_source)

        for name in (
            "advancedHighlightState",
            "refreshAdvancedHighlights",
            "registerAdvancedAutocompleteInput",
            "scheduleAdvancedFieldHighlight",
            "scheduleAdvancedHighlights",
            "updateAdvancedFieldHighlight",
        ):
            with self.subTest(module="advanced_highlights", symbol=name):
                self.assertIn(f"  {name},", advanced_highlights_source)

        for name in (
            "desiredTextareaHeight",
            "expandStudioInputToContent",
            "growStudioManualHeightToContent",
            "rebalanceStudioInputHeights",
            "setStudioInputHeight",
            "setStudioManualHeight",
            "studioCurrentHeight",
            "studioDefaultHeight",
            "syncStudioOverflow",
            "textareaContentHeight",
            "visibleStudioWidgets",
            "widgetHeight",
        ):
            with self.subTest(module="studio_textareas", symbol=name):
                self.assertIn(f"  {name},", studio_textareas_source)

        for name in (
            "enhanceResizableInput",
        ):
            with self.subTest(module="studio_resizable_input", symbol=name):
                self.assertIn(f"  {name},", studio_resizable_input_source)

        for name in (
            "hookStudioNode",
        ):
            with self.subTest(module="studio_node_ui", symbol=name):
                self.assertIn(f"  {name},", studio_node_ui_source)

        for name in (
            "applyExecutedInputs",
            "restoreInputFromWidget",
            "syncStudioValues",
            "syncWidgetValue",
        ):
            with self.subTest(module="studio_values", symbol=name):
                self.assertIn(f"  {name},", studio_values_source)

        for name in (
            "applyWildcardExecutedInputs",
            "setRegularWidgetValue",
        ):
            with self.subTest(module="wildcard_values", symbol=name):
                self.assertIn(f"  {name},", wildcard_values_source)

        for name in (
            "advancedFieldTextareaPlaceholder",
            "advancedFieldTextareaTitle",
            "captureAdvancedTextareaManualResize",
            "rememberAdvancedTextareaResizeStart",
            "syncAdvancedTextareaLinkedInputValue",
        ):
            with self.subTest(module="textarea", symbol=name):
                self.assertIn(f"  {name},", textarea_source)

        for name in (
            "advancedEditorFromWheelEvent",
            "advancedEditorMaxScrollTop",
            "advancedWheelDeltaPixels",
            "consumeAdvancedEditorWheel",
            "guardAdvancedEditorNativeControlEvent",
            "isMiddlePanExcludedTarget",
        ):
            with self.subTest(module="wheel", symbol=name):
                self.assertIn(f"  {name},", wheel_source)

        for name in (
            "advancedFieldDisplayText",
            "advancedFieldIndexLabel",
            "advancedFieldInputLinked",
            "advancedFieldsBackup",
            "captureAdvancedConfigure",
            "collectAdvancedEditorFields",
            "ensureAdvancedWidgetValue",
            "isAdvancedFieldInput",
            "mergeAdvancedFieldInputValues",
            "pruneDisconnectedAdvancedFieldInputValues",
            "serializedAdvancedFieldsValue",
            "syncAdvancedFieldInputs",
            "syncAdvancedFieldsBackup",
            "updateNodeInputLinkSlots",
        ):
            with self.subTest(module="serialization", symbol=name):
                self.assertIn(f"  {name},", serialization_source)

        for name in (
            "markCanvasDirty",
            "markGraphDirty",
            "markNodeDirty",
            "refreshNodeSize",
        ):
            with self.subTest(module="runtime_canvas", symbol=name):
                self.assertIn(f"  {name},", runtime_canvas_source)

        for name in (
            "createPromptStudioExtensionRuntime",
        ):
            with self.subTest(module="extension_runtime", symbol=name):
                self.assertIn(f"  {name},", extension_runtime_source)

    def test_advanced_width_reflow_grows_content_without_owning_node_height(self):
        controller_source = (PROMPT_STUDIO_MODULES / "advanced_layout_controller.js").read_text(
            encoding="utf-8"
        )
        fields_ui_source = (PROMPT_STUDIO_MODULES / "advanced_fields_ui.js").read_text(
            encoding="utf-8"
        )
        runtime_source = (PROMPT_STUDIO_MODULES / "extension_runtime.js").read_text(
            encoding="utf-8"
        )

        remeasure_start = fields_ui_source.index(
            "function remeasureAdvancedTextareaHeightsForWidth"
        )
        remeasure_end = fields_ui_source.index(
            "\nfunction createAdvancedFieldElement", remeasure_start
        )
        remeasure_body = fields_ui_source[remeasure_start:remeasure_end]

        self.assertIn("new ResizeObserver", controller_source)
        self.assertIn("advancedEditorClientWidth(editor)", controller_source)
        self.assertIn("scheduleAdvancedWidthRemeasure(node, hooks)", controller_source)
        self.assertIn(
            "hooks.remeasureAdvancedTextareaHeightsForWidth?.(node)",
            controller_source,
        )
        self.assertIn('scheduleAdvancedLayout(node, "width", hooks)', controller_source)
        self.assertIn("ADVANCED_RESIZE_SETTLE_DELAY", controller_source)
        self.assertIn("width: 2", controller_source)
        self.assertIn('reason !== "width"', controller_source)
        self.assertNotIn("scheduleAdvancedScrollbarRemeasure", controller_source)
        self.assertNotIn("advancedEditorLayoutMetricsChanged", controller_source)

        self.assertIn(
            'querySelectorAll("textarea[data-easyuse-anima-advanced-field-id]")',
            remeasure_body,
        )
        self.assertIn("advancedTextareaCurrentHeight(textarea)", remeasure_body)
        self.assertIn("setAdvancedTextareaHeight(", remeasure_body)
        self.assertIn("if (nextHeight >", remeasure_body)
        self.assertNotIn("field.heightMode =", remeasure_body)
        self.assertIn(
            "hooks.writeAdvancedFields?.(node, fields, { syncInputs: false })",
            remeasure_body,
        )
        self.assertIn("remeasureAdvancedTextareaHeightsForWidth,", runtime_source)

        advanced_node_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_node_ui.js"
        ).read_text(encoding="utf-8")
        node_hooks_source = (PROMPT_STUDIO_MODULES / "node_hooks.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("observeAdvancedEditorWidth(node);", advanced_node_ui_source)
        self.assertIn("disconnectAdvancedEditorWidthObserver?.(this);", node_hooks_source)

    def test_advanced_editor_scrollbar_exclusively_owns_wheel_events(self):
        wheel_source = (PROMPT_STUDIO_MODULES / "wheel.js").read_text(
            encoding="utf-8"
        )
        forwarding_source = (PROMPT_STUDIO_MODULES / "canvas_forwarding.js").read_text(
            encoding="utf-8"
        )
        advanced_node_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_node_ui.js"
        ).read_text(encoding="utf-8")
        runtime_source = (PROMPT_STUDIO_MODULES / "extension_runtime.js").read_text(
            encoding="utf-8"
        )
        consume_start = wheel_source.index("function consumeAdvancedEditorWheel")
        consume_end = wheel_source.index("\nexport {", consume_start)
        consume_body = wheel_source[consume_start:consume_end]
        forward_start = forwarding_source.index("function forwardAdvancedWheelToCanvas")
        forward_end = forwarding_source.index("\nfunction installAdvancedWheelForwarder", forward_start)
        forward_body = forwarding_source[forward_start:forward_end]
        install_start = forwarding_source.index("function installAdvancedWheelForwarder")
        install_end = forwarding_source.index("\nfunction installMiddlePanForwarder", install_start)
        install_body = forwarding_source[install_start:install_end]

        self.assertIn("if (maxScrollTop <= 1)", consume_body)
        self.assertIn("event.preventDefault?.()", consume_body)
        self.assertIn("event.stopPropagation?.()", consume_body)
        self.assertIn("event.stopImmediatePropagation?.()", consume_body)
        self.assertIn("editor.scrollTop = nextScrollTop", consume_body)
        self.assertIn("return true", consume_body)
        self.assertNotIn("canAdvancedEditorScrollWheelDelta", wheel_source)
        self.assertNotIn("shouldKeepAdvancedWheelEvent", wheel_source)

        consume_call = "if (consumeAdvancedEditorWheel(event, editor))"
        self.assertIn("advancedEditorFromWheelEvent(event)", forward_body)
        self.assertIn(consume_call, forward_body)
        self.assertLess(
            forward_body.index(consume_call),
            forward_body.index("dispatchCanvasWheelEvent(event)"),
        )
        self.assertIn(
            'hostWindow.addEventListener("wheel", forwardAdvancedWheelToCanvas',
            install_body,
        )
        self.assertIn("capture: true", install_body)
        self.assertIn("passive: false", install_body)
        self.assertNotIn('editor.addEventListener("wheel"', advanced_node_ui_source)
        self.assertIn("installAdvancedWheelForwarder();", runtime_source)

    def test_advanced_dom_widget_height_is_host_owned(self):
        advanced_node_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_node_ui.js"
        ).read_text(encoding="utf-8")
        layout_source = (PROMPT_STUDIO_MODULES / "layout.js").read_text(
            encoding="utf-8"
        )
        controller_source = (
            PROMPT_STUDIO_MODULES / "advanced_layout_controller.js"
        ).read_text(encoding="utf-8")
        style_source = (PROMPT_STUDIO_MODULES / "style.js").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "getMinHeight: () => ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT",
            advanced_node_ui_source,
        )
        self.assertNotIn("getHeight:", advanced_node_ui_source)
        self.assertNotIn("widget.computeLayoutSize =", advanced_node_ui_source)
        self.assertNotRegex(
            advanced_node_ui_source + layout_source + controller_source,
            r"\.computedHeight\s*=",
        )

        for forbidden in (
            "advancedAvailableEditorViewportHeight",
            "advancedEditorWidgetHeight",
            "advancedMinimumNodeHeight",
            "advancedNodeChromeOffset",
            "clampAdvancedNodeToMinimumHeight",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, layout_source)
                self.assertNotIn(forbidden, controller_source)

        self.assertNotIn("node.setSize(", controller_source)
        self.assertNotIn("node.setSize?.(", controller_source)
        self.assertNotRegex(
            controller_source,
            r"editor\.style\.(?:height|maxHeight)\s*=",
        )

        editor_style_start = style_source.index(
            ".easyuse-anima-advanced-editor {"
        )
        editor_style_end = style_source.index("\n    }", editor_style_start)
        editor_style = style_source[editor_style_start:editor_style_end]
        self.assertIn(
            "min-height: ${ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT}px;",
            editor_style,
        )
        self.assertIn("flex: 1 1 0%;", editor_style)
        self.assertIn("contain: size;", editor_style)
        self.assertIn("overflow-y: auto;", editor_style)

    def test_prompt_studio_phase_3_typedefs_are_documented(self):
        types_source = (PROMPT_STUDIO_MODULES / "types.js").read_text(
            encoding="utf-8"
        )

        for name in (
            "PromptStudioField",
            "PromptStudioFieldHeightMode",
            "PromptStudioState",
            "AdvancedEditorNode",
            "ComfyNodeLike",
            "ComfyWidgetLike",
            "PromptStudioInputElement",
            "PromptStudioAdvancedTextarea",
            "PromptStudioAutocompleteTooltip",
            "PromptStudioWindow",
            "PromptClassificationResult",
            "EasyUseAnimaSettings",
            "ApiJsonResponse",
            "LayoutMeasureResult",
            "ResizeFinalizeState",
        ):
            with self.subTest(typedef=name):
                self.assertIn(f" {name}", types_source)

    def test_prompt_studio_typecheck_config_tracks_current_slice(self):
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))

        self.assertTrue(config["compilerOptions"]["allowJs"])
        self.assertTrue(config["compilerOptions"]["checkJs"])
        self.assertTrue(config["compilerOptions"]["noEmit"])
        self.assertTrue(config["compilerOptions"]["noUnusedLocals"])
        self.assertTrue(config["compilerOptions"]["noUnusedParameters"])

        for path in (
            "web/js/easyuse_anima_prompt_studio.js",
            "web/js/prompt_studio/*.js",
        ):
            with self.subTest(path=path):
                self.assertIn(path, config["include"])

    def test_frontend_check_script_runs_syntax_and_typecheck(self):
        source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertIn('Get-ChildItem -File -Recurse -Path "web\\js"', source)
        self.assertIn("& node --check", source)
        self.assertIn(r'& node "tests\frontend_highlight_core_smoke.mjs"', source)
        self.assertIn(
            r'& node "tests\frontend_highlight_overlay_core_smoke.mjs"', source
        )
        self.assertIn('"typescript@$TypeScriptVersion"', source)
        self.assertIn("tsc -p jsconfig.json", source)

    def test_prompt_studio_split_modules_start_with_ts_check(self):
        for path in sorted(PROMPT_STUDIO_MODULES.glob("*.js")):
            with self.subTest(filename=path.name):
                first_line = path.read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(first_line, "// @ts-check")

    def test_prompt_studio_split_modules_have_no_import_cycles(self):
        module_paths = {
            path.name: path for path in sorted(PROMPT_STUDIO_MODULES.glob("*.js"))
        }
        graph = {name: [] for name in module_paths}
        for name, path in module_paths.items():
            source = path.read_text(encoding="utf-8")
            for import_path in STATIC_IMPORT_RE.findall(source):
                target = Path(import_path).name
                if target in module_paths:
                    graph[name].append(target)

        visiting = set()
        visited = set()

        def visit(name, stack):
            if name in visiting:
                cycle = " -> ".join([*stack, name])
                self.fail(f"Prompt Studio import cycle detected: {cycle}")
            if name in visited:
                return
            visiting.add(name)
            for target in graph[name]:
                visit(target, [*stack, name])
            visiting.remove(name)
            visited.add(name)

        for name in graph:
            visit(name, [])

    def test_prompt_studio_phase_2_modules_have_no_runtime_side_effects(self):
        for filename in (
            "constants.js",
            "utils.js",
            "schema.js",
            "state.js",
            "advanced_fields_state.js",
            "advanced_values.js",
            "extend_layout.js",
            "extend_slots.js",
            "fields.js",
            "highlight_core.js",
            "highlight_overlay_core.js",
            "highlight_ui.js",
            "legend.js",
            "node_hooks.js",
            "text.js",
            "widgets.js",
            "layout.js",
            "studio_textareas.js",
            "studio_resizable_input.js",
            "studio_node_ui.js",
            "studio_values.js",
            "wildcard_values.js",
            "textarea.js",
            "wheel.js",
            "serialization.js",
            "runtime_canvas.js",
            "types.js",
        ):
            with self.subTest(filename=filename):
                source = (PROMPT_STUDIO_MODULES / filename).read_text(
                    encoding="utf-8"
                )
                self.assertNotIn("app.registerExtension", source)
                self.assertNotIn("document.", source)
                self.assertNotIn("window.", source)
                self.assertNotIn("fetch(", source)

    def test_prompt_studio_dom_module_has_no_registration_or_network_side_effects(self):
        for filename in (
            "advanced_controls.js",
            "advanced_fields_ui.js",
            "advanced_highlights.js",
            "advanced_layout_controller.js",
            "advanced_node_ui.js",
            "canvas_forwarding.js",
            "dom.js",
            "extension_runtime.js",
            "extend_slot_controls.js",
            "settings.js",
            "style.js",
            "tooltip.js",
        ):
            with self.subTest(filename=filename):
                source = (PROMPT_STUDIO_MODULES / filename).read_text(
                    encoding="utf-8"
                )

                self.assertNotIn("app.registerExtension", source)
                self.assertNotIn("fetch(", source)


if __name__ == "__main__":
    unittest.main()
