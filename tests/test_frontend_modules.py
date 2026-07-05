from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSCONFIG = ROOT / "jsconfig.json"
WEB_JS = ROOT / "web" / "js"
API_JS = WEB_JS / "easyuse_anima_api.js"
PROMPT_STUDIO_JS = WEB_JS / "easyuse_anima_prompt_studio.js"
PROMPT_STUDIO_MODULES = WEB_JS / "prompt_studio"
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
        ):
            self.assertRegex(source, rf"export (?:async )?function {name}\(")

    def test_feature_scripts_use_shared_api_module(self):
        expected_imports = {
            "easyuse_anima_autocomplete.js": './easyuse_anima_api.js"',
            "easyuse_anima_lora_preset.js": './easyuse_anima_api.js"',
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

    def test_prompt_studio_layout_uses_explicit_dom_viewport_contract(self):
        layout_source = (PROMPT_STUDIO_MODULES / "layout.js").read_text(
            encoding="utf-8"
        )
        advanced_layout_controller_source = (
            PROMPT_STUDIO_MODULES / "advanced_layout_controller.js"
        ).read_text(encoding="utf-8")
        style_source = (PROMPT_STUDIO_MODULES / "style.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("function applyAdvancedEditorViewportStyle", layout_source)
        self.assertIn("function advancedNodeAvailableEditorViewportHeight", layout_source)
        self.assertIn("function applyAdvancedWidgetAllocation", layout_source)
        self.assertIn("widget.computedHeight = viewportHeight;", layout_source)
        self.assertIn("return advancedNodeAvailableEditorViewportHeight(node);", layout_source)
        self.assertIn("--easyuse-anima-advanced-editor-height", layout_source)
        self.assertNotIn("function advancedAllocatedEditorHeight", layout_source)
        self.assertNotIn("function advancedUserResizeActive", layout_source)
        self.assertNotIn("advancedAllocatedEditorHeight(node)", layout_source)
        self.assertNotIn("advancedUserResizeActive(node)", layout_source)
        self.assertNotIn("const allocatedHeight", layout_source)
        self.assertNotIn("const host = editor.parentElement", layout_source)
        self.assertNotIn("editor?.parentElement", layout_source)
        self.assertNotIn("host.style.height", layout_source)
        self.assertIn(
            "applyAdvancedEditorViewportStyle(editor, widgetHeight);",
            advanced_layout_controller_source,
        )
        self.assertIn(
            "applyAdvancedWidgetAllocation(node, widgetHeight);",
            advanced_layout_controller_source,
        )
        self.assertIn(
            "height: var(--easyuse-anima-advanced-editor-height, auto);",
            style_source,
        )
        self.assertNotIn("scrollbar-gutter: stable;", style_source)

    def test_prompt_studio_advanced_render_and_layout_preserve_editor_scroll(self):
        layout_source = (PROMPT_STUDIO_MODULES / "layout.js").read_text(
            encoding="utf-8"
        )
        advanced_node_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_node_ui.js"
        ).read_text(encoding="utf-8")
        advanced_layout_controller_source = (
            PROMPT_STUDIO_MODULES / "advanced_layout_controller.js"
        ).read_text(encoding="utf-8")

        self.assertIn("function readAdvancedEditorScrollState", layout_source)
        self.assertIn("function rememberAdvancedEditorScrollState", layout_source)
        self.assertIn("function preferredAdvancedEditorScrollState", layout_source)
        self.assertIn("function restoreAdvancedEditorScrollState", layout_source)
        self.assertIn("function installAdvancedEditorScrollRetention", advanced_node_ui_source)
        self.assertIn("const scrollState = preferredAdvancedEditorScrollState(node, editor);", advanced_node_ui_source)
        self.assertIn("restoreAdvancedEditorScrollState(editor, scrollState);", advanced_node_ui_source)
        self.assertIn("rememberAdvancedEditorScrollState(node, editor, scrollState);", advanced_node_ui_source)
        self.assertIn(
            "requestAnimationFrame(() => restoreAdvancedEditorScrollState(editor, scrollState));",
            advanced_node_ui_source,
        )
        self.assertIn('editor.addEventListener("pointerleave", leave);', advanced_node_ui_source)
        self.assertIn('editor.addEventListener("mouseleave", leave);', advanced_node_ui_source)
        self.assertIn("restoreAdvancedEditorScrollSoon(node, editor, state);", advanced_node_ui_source)
        self.assertIn("const scrollState = preferredAdvancedEditorScrollState(node, editor);", advanced_layout_controller_source)
        self.assertIn("restoreAdvancedEditorScrollState(editor, scrollState);", advanced_layout_controller_source)
        self.assertIn("rememberAdvancedEditorScrollState(node, editor, scrollState);", advanced_layout_controller_source)

    def test_prompt_studio_advanced_resize_remeasures_wrapped_textareas(self):
        advanced_fields_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_fields_ui.js"
        ).read_text(encoding="utf-8")
        advanced_layout_controller_source = (
            PROMPT_STUDIO_MODULES / "advanced_layout_controller.js"
        ).read_text(encoding="utf-8")
        extension_runtime_source = (
            PROMPT_STUDIO_MODULES / "extension_runtime.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "function syncAdvancedTextareaHeightsForWidth",
            advanced_fields_ui_source,
        )
        sync_start = advanced_fields_ui_source.index(
            "function syncAdvancedTextareaHeightsForWidth"
        )
        sync_end = advanced_fields_ui_source.index(
            "\nfunction createAdvancedFieldElement", sync_start
        )
        sync_body = advanced_fields_ui_source[sync_start:sync_end]

        self.assertIn("advancedTextareaAutoHeight(textarea)", sync_body)
        self.assertIn("advancedTextareaCurrentBoxHeight(textarea)", sync_body)
        self.assertIn("Number(field.height)", sync_body)
        self.assertIn(
            'const mode = field.heightMode === "manual" ? "manual" : "auto";',
            sync_body,
        )
        self.assertIn("syncField: false,", sync_body)
        self.assertNotIn("field.height = nextHeight;", sync_body)
        self.assertNotIn("hooks.writeAdvancedFields?.(node, fields", sync_body)
        self.assertIn(
            "syncAdvancedTextareaHeightsForWidth(node, hooks);",
            advanced_layout_controller_source,
        )
        self.assertIn("function markAdvancedUserResize", advanced_layout_controller_source)
        self.assertIn("node.__easyuseAnimaAdvancedUserResizing = true;", advanced_layout_controller_source)
        self.assertIn("node.__easyuseAnimaAdvancedUserResizing = false;", advanced_layout_controller_source)
        self.assertIn("markAdvancedUserResize,", extension_runtime_source)
        self.assertLess(
            advanced_layout_controller_source.index("updateAdvancedEditorWidth(node);"),
            advanced_layout_controller_source.index("syncAdvancedTextareaHeightsForWidth(node, hooks);"),
        )
        self.assertLess(
            advanced_layout_controller_source.index("syncAdvancedTextareaHeightsForWidth(node, hooks);"),
            advanced_layout_controller_source.index("clampAdvancedNodeToMinimumHeight(node);"),
        )
        self.assertIn("writeAdvancedFields,", extension_runtime_source)

    def test_prompt_studio_textarea_height_state_has_single_owner(self):
        advanced_fields_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_fields_ui.js"
        ).read_text(encoding="utf-8")
        layout_source = (PROMPT_STUDIO_MODULES / "layout.js").read_text(
            encoding="utf-8"
        )
        set_start = advanced_fields_ui_source.index(
            "function setAdvancedTextareaHeight"
        )
        set_end = advanced_fields_ui_source.index(
            "\nfunction syncAdvancedTextareaHeightsForWidth", set_start
        )
        set_body = advanced_fields_ui_source[set_start:set_end]

        self.assertIn(
            'const mode = options.mode === "manual" ? "manual" : "auto";',
            set_body,
        )
        self.assertIn("const minimumHeight = advancedTextareaMinimumHeight(textarea);", set_body)
        self.assertIn("const contentHeight = advancedTextareaContentHeight(textarea);", set_body)
        self.assertIn(
            "const requiredHeight = Math.max(minimumHeight, contentHeight);",
            set_body,
        )
        self.assertIn('textarea.style.minHeight = `${minimumHeight}px`;', set_body)
        self.assertIn('textarea.style.overflowY = "hidden";', set_body)
        self.assertNotIn('textarea.style.overflowY = mode === "manual" ? "auto" : "hidden";', set_body)
        self.assertIn("field.heightMode = mode;", set_body)
        self.assertNotIn("textarea.scrollTop = 0;", set_body)
        self.assertNotIn("textarea.scrollLeft = 0;", set_body)
        self.assertIn("function advancedTextareaCurrentBoxHeight", layout_source)
        self.assertIn("function advancedTextareaAutoHeight", layout_source)
        self.assertIn("advancedTextareaMinimumHeight(textarea),", layout_source)
        self.assertNotIn("advancedTextareaVisibleMinimumHeight(textarea),", layout_source[
            layout_source.index("function advancedTextareaCurrentHeight"):
            layout_source.index("\nfunction advancedTextareaHeightTotal")
        ])
        self.assertIn("return ADVANCED_EDITOR_MIN_VIEWPORT_HEIGHT;", layout_source)
        self.assertNotIn("Math.min(contentMinimum, advancedEditorAutoViewportCap())", layout_source)
        self.assertIn('if (field.heightMode === "manual")', advanced_fields_ui_source)
        self.assertIn('field.height || advancedTextareaCurrentBoxHeight(textarea)', advanced_fields_ui_source)
        self.assertIn("hooks.writeAdvancedFields?.(node, fields, { syncInputs: false });", advanced_fields_ui_source)
        self.assertNotIn('persistTextareaHeight(advancedTextareaCurrentHeight(textarea), "manual");', advanced_fields_ui_source)
        self.assertIn("mode,", advanced_fields_ui_source)
        self.assertIn(
            'mode: field.heightMode === "manual" ? "manual" : "auto",',
            advanced_fields_ui_source,
        )
        self.assertNotIn("if (nextHeight !== field.height)", advanced_fields_ui_source)

    def test_prompt_studio_serialization_collects_text_without_layout_height(self):
        serialization_source = (
            PROMPT_STUDIO_MODULES / "serialization.js"
        ).read_text(encoding="utf-8")
        start = serialization_source.index("function collectAdvancedEditorFields")
        end = serialization_source.index("\nfunction advancedFieldIndexLabel", start)
        body = serialization_source[start:end]

        self.assertIn("field.text = textarea.value;", body)
        self.assertNotIn("style.height", body)
        self.assertNotIn("field.height =", body)

    def test_prompt_studio_dom_widget_layout_uses_official_size_fields(self):
        advanced_node_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_node_ui.js"
        ).read_text(encoding="utf-8")
        start = advanced_node_ui_source.index("widget.computeLayoutSize = () => ({")
        end = advanced_node_ui_source.index("\n      });", start)
        body = advanced_node_ui_source[start:end]

        self.assertIn("minHeight: advancedEditorMinimumHeight(node),", body)
        self.assertIn("minWidth: 280,", body)
        self.assertNotIn("height,", body)

    def test_prompt_studio_scrollable_wheel_does_not_forward_to_canvas(self):
        wheel_source = (PROMPT_STUDIO_MODULES / "wheel.js").read_text(
            encoding="utf-8"
        )
        canvas_forwarding_source = (
            PROMPT_STUDIO_MODULES / "canvas_forwarding.js"
        ).read_text(encoding="utf-8")
        start = wheel_source.index("function shouldKeepAdvancedWheelEvent")
        end = wheel_source.index("\nexport {", start)
        body = wheel_source[start:end]
        forward_start = canvas_forwarding_source.index("function forwardAdvancedWheelToCanvas")
        forward_end = canvas_forwarding_source.index("\nfunction installMiddlePanForwarder", forward_start)
        forward_body = canvas_forwarding_source[forward_start:forward_end]

        self.assertIn("const control = advancedWheelScrollableControl(target);", body)
        self.assertIn("!isAdvancedNativeControlTarget(control)", body)
        self.assertIn("return canAdvancedControlScroll(control);", body)
        self.assertIn("function canAdvancedControlScrollWheelDelta", wheel_source)
        self.assertIn("function canAdvancedControlScroll", wheel_source)
        self.assertNotIn("return isAdvancedNativeControlTarget(target);", body)
        self.assertIn("if (canAdvancedEditorScroll(editor))", forward_body)
        self.assertIn("event.stopPropagation();", forward_body)
        self.assertIn("if (!canAdvancedEditorScrollWheelDelta(editor, deltaY))", forward_body)
        self.assertLess(
            forward_body.index("if (canAdvancedEditorScroll(editor))"),
            forward_body.index("dispatchCanvasWheelEvent(event);"),
        )

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
            "setAdvancedTextareaHeight",
            "syncAdvancedTextareaHeightsForWidth",
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
            "advancedTextareaAutoHeight",
            "advancedTextareaCurrentBoxHeight",
            "advancedEditorMinimumHeight",
            "advancedEditorWidgetHeight",
            "advancedMinimumNodeHeight",
            "advancedNodeAvailableEditorViewportHeight",
            "advancedTextareaContentHeight",
            "advancedTextareaCurrentHeight",
            "advancedTextareaMinimumHeight",
            "advancedTextareaVisibleMinimumHeight",
            "clampAdvancedNodeToMinimumHeight",
            "rememberAdvancedEditorScrollState",
            "preferredAdvancedEditorScrollState",
            "readAdvancedEditorScrollState",
            "restoreAdvancedEditorScrollState",
            "updateAdvancedEditorWidth",
            "applyAdvancedWidgetAllocation",
        ):
            with self.subTest(module="layout", symbol=name):
                self.assertIn(f"  {name},", layout_source)

        for name in (
            "applyAdvancedLayout",
            "clearAdvancedResizeEndListeners",
            "finalizeAdvancedResize",
            "installAdvancedResizeEndListeners",
            "markAdvancedUserResize",
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
            "advancedEditorMaxScrollTop",
            "canAdvancedEditorScroll",
            "canAdvancedEditorScrollWheelDelta",
            "guardAdvancedEditorNativeControlEvent",
            "isMiddlePanExcludedTarget",
            "shouldKeepAdvancedWheelEvent",
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

    def test_prompt_studio_phase_3_typedefs_are_documented(self):
        types_source = (PROMPT_STUDIO_MODULES / "types.js").read_text(
            encoding="utf-8"
        )

        for name in (
            "PromptStudioField",
            "PromptStudioFieldHeightMode",
            "PromptStudioFieldPane",
            "PromptStudioFieldType",
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

        for property_line in (
            "* @property {PromptStudioFieldPane} pane",
            "* @property {PromptStudioFieldType} type",
            "* @property {string} label",
            "* @property {string} text",
            "* @property {boolean} enabled",
            "* @property {boolean} pin",
        ):
            with self.subTest(property=property_line):
                self.assertIn(property_line, types_source)

    def test_prompt_studio_typecheck_config_tracks_current_slice(self):
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))

        self.assertTrue(config["compilerOptions"]["allowJs"])
        self.assertTrue(config["compilerOptions"]["checkJs"])
        self.assertTrue(config["compilerOptions"]["noEmit"])

        for path in (
            "web/js/easyuse_anima_prompt_studio.js",
            "web/js/prompt_studio/*.js",
        ):
            with self.subTest(path=path):
                self.assertIn(path, config["include"])

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
