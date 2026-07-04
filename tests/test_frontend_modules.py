from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_JS = ROOT / "web" / "js"
API_JS = WEB_JS / "easyuse_anima_api.js"
PROMPT_STUDIO_JS = WEB_JS / "easyuse_anima_prompt_studio.js"
PROMPT_STUDIO_MODULES = WEB_JS / "prompt_studio"


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

    def test_prompt_studio_entry_imports_phase_2_modules(self):
        source = PROMPT_STUDIO_JS.read_text(encoding="utf-8")

        self.assertIn('./prompt_studio/constants.js"', source)
        self.assertIn('./prompt_studio/utils.js"', source)
        self.assertIn('./prompt_studio/schema.js"', source)
        self.assertIn('./prompt_studio/state.js"', source)
        self.assertIn('./prompt_studio/dom.js"', source)
        self.assertIn('./prompt_studio/fields.js"', source)
        self.assertIn('./prompt_studio/node_hooks.js"', source)
        self.assertIn('./prompt_studio/settings.js"', source)
        self.assertIn('./prompt_studio/style.js"', source)
        self.assertIn('./prompt_studio/layout.js"', source)
        self.assertIn('./prompt_studio/textarea.js"', source)
        self.assertIn('./prompt_studio/wheel.js"', source)
        self.assertIn('./prompt_studio/serialization.js"', source)

    def test_prompt_studio_phase_2_modules_export_expected_symbols(self):
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
        dom_source = (PROMPT_STUDIO_MODULES / "dom.js").read_text(
            encoding="utf-8"
        )
        fields_source = (PROMPT_STUDIO_MODULES / "fields.js").read_text(
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
        layout_source = (PROMPT_STUDIO_MODULES / "layout.js").read_text(
            encoding="utf-8"
        )
        textarea_source = (PROMPT_STUDIO_MODULES / "textarea.js").read_text(
            encoding="utf-8"
        )
        wheel_source = (PROMPT_STUDIO_MODULES / "wheel.js").read_text(
            encoding="utf-8"
        )
        serialization_source = (
            PROMPT_STUDIO_MODULES / "serialization.js"
        ).read_text(encoding="utf-8")

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
            "closeAdvancedHelpPopovers",
            "openAdvancedHelpPopover",
            "protectAdvancedNativeControl",
            "stopAdvancedControlEvent",
            "updateAdvancedSummary",
        ):
            with self.subTest(module="dom", symbol=name):
                self.assertIn(f"  {name},", dom_source)

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

        for name in ("ensureAdvancedStyle", "ensureExtendSlotStyle"):
            with self.subTest(module="style", symbol=name):
                self.assertIn(f"  {name},", style_source)

        for name in (
            "advancedEditorMinimumHeight",
            "advancedEditorWidgetHeight",
            "advancedMinimumNodeHeight",
            "advancedTextareaContentHeight",
            "advancedTextareaCurrentHeight",
            "advancedTextareaMinimumHeight",
            "clampAdvancedNodeToMinimumHeight",
            "updateAdvancedEditorWidth",
        ):
            with self.subTest(module="layout", symbol=name):
                self.assertIn(f"  {name},", layout_source)

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

    def test_prompt_studio_phase_2_modules_have_no_runtime_side_effects(self):
        for filename in (
            "constants.js",
            "utils.js",
            "schema.js",
            "state.js",
            "fields.js",
            "node_hooks.js",
            "layout.js",
            "textarea.js",
            "wheel.js",
            "serialization.js",
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
        for filename in ("dom.js", "settings.js", "style.js"):
            with self.subTest(filename=filename):
                source = (PROMPT_STUDIO_MODULES / filename).read_text(
                    encoding="utf-8"
                )

                self.assertNotIn("app.registerExtension", source)
                self.assertNotIn("fetch(", source)


if __name__ == "__main__":
    unittest.main()
