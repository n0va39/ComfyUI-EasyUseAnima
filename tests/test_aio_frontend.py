from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AIO_JS = ROOT / "web" / "js" / "easyuse_anima_aio.js"
AIO_POSTPROCESS_SETTINGS_DIALOG_JS = (
    ROOT / "web" / "js" / "aio" / "postprocess_settings_dialog.js"
)
AIO_PROFILE_API_CLIENT_JS = (
    ROOT / "web" / "js" / "aio" / "profile_api_client.js"
)
AIO_PROFILE_SETTINGS_RUNTIME_JS = (
    ROOT / "web" / "js" / "aio" / "profile_settings_runtime.js"
)
AIO_GENERATOR_PANEL_RUNTIME_JS = (
    ROOT / "web" / "js" / "aio" / "generator_panel_runtime.js"
)
AIO_GENERATOR_QUEUE_RUNTIME_JS = (
    ROOT / "web" / "js" / "aio" / "generator_queue_runtime.js"
)
AIO_EXTENSION_RUNTIME_JS = (
    ROOT / "web" / "js" / "aio" / "extension_runtime.js"
)
AIO_NATIVE_PREVIEW_RUNTIME_JS = (
    ROOT / "web" / "js" / "aio" / "native_preview_runtime.js"
)
AIO_STAGE_SETTINGS_DIALOGS_JS = (
    ROOT / "web" / "js" / "aio" / "stage_settings_dialogs.js"
)
AIO_DETAILER_SETTINGS_DIALOG_JS = (
    ROOT / "web" / "js" / "aio" / "detailer_settings_dialog.js"
)
AIO_SAVE_SETTINGS_DIALOG_JS = (
    ROOT / "web" / "js" / "aio" / "save_settings_dialog.js"
)
AIO_ADVANCED_SETTINGS_DIALOG_JS = (
    ROOT / "web" / "js" / "aio" / "advanced_settings_dialog.js"
)
AIO_PREVIEW_JS = ROOT / "web" / "js" / "aio" / "preview.js"
AIO_SETTINGS_JS = ROOT / "web" / "js" / "aio" / "settings.js"
AIO_WHEEL_JS = ROOT / "web" / "js" / "aio" / "wheel.js"
AIO_PRESETS_JS = ROOT / "web" / "js" / "aio" / "presets.js"
AUTOCOMPLETE_JS = ROOT / "web" / "js" / "easyuse_anima_autocomplete.js"
AUTOCOMPLETE_DATA_ADAPTER_JS = (
    ROOT / "web" / "js" / "autocomplete" / "data_adapter.js"
)
AUTOCOMPLETE_INPUT_CONTROLLER_JS = (
    ROOT / "web" / "js" / "autocomplete" / "input_controller.js"
)
AUTOCOMPLETE_INPUT_BINDING_JS = (
    ROOT / "web" / "js" / "autocomplete" / "input_binding.js"
)
AUTOCOMPLETE_ENTRY_LIFECYCLE_JS = (
    ROOT / "web" / "js" / "autocomplete" / "entry_lifecycle.js"
)
AUTOCOMPLETE_TEXT_MODEL_JS = (
    ROOT / "web" / "js" / "autocomplete" / "text_model.js"
)
PROMPT_STUDIO_REGIONAL_ADAPTER_JS = (
    ROOT / "web" / "js" / "prompt_studio" / "regional" / "editor_adapter.js"
)
PROMPT_STUDIO_HIGHLIGHT_CORE_JS = ROOT / "web" / "js" / "prompt_studio" / "highlight_core.js"


class AIOFrontendSourceTests(unittest.TestCase):
    def test_generator_profile_ui_uses_versioned_settings_and_user_storage_api(self):
        source = AIO_JS.read_text(encoding="utf-8")
        presets_source = AIO_PRESETS_JS.read_text(encoding="utf-8")
        api_client_source = AIO_PROFILE_API_CLIENT_JS.read_text(encoding="utf-8")
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        serialize_start = source.index("function syncGeneratorSerializedWidgets")
        serialize_end = source.index("\nfunction markNodeDirty", serialize_start)
        serialize_body = source[serialize_start:serialize_end]

        self.assertIn('from "./aio/presets.js"', source)
        self.assertIn("aioProfileSettingsFingerprint", source)
        for helper in ("aioFindUserProfileByName", "aioResolvedProfileValue"):
            with self.subTest(profile_core_helper=helper):
                self.assertIn(f"export function {helper}(", presets_source)
                self.assertIn(helper, source)
        self.assertIn(
            'from "./aio/profile_api_client.js"',
            source,
        )
        self.assertIn(
            'from "./aio/profile_settings_runtime.js"',
            source,
        )
        self.assertIn('"profile.custom": "Custom"', source)
        self.assertIn('"normal", "turbo", "optimized"', presets_source)
        self.assertIn('settings.sampler.steps = 10', presets_source)
        self.assertIn('settings.sampler.cfg = 1.0', presets_source)
        self.assertIn('target.dit_corrections.dcw_mode = enabled ? "auto" : "off"', presets_source)
        self.assertIn('kj.sage_attention = enabled ? "auto" : "disabled"', presets_source)
        self.assertIn("compile.enabled = enabled", presets_source)
        self.assertIn("syncGeneratorProfileValue(node, settings)", panel_source)
        self.assertIn(
            'profileButton.setAttribute("data-aio-profile-button", "")',
            panel_source,
        )
        self.assertIn(
            'panel.querySelector("[data-aio-profile-button]")',
            panel_source,
        )
        self.assertIn("generatorProfileDisplayLabel(profileValue)", panel_source)
        self.assertNotIn("function openGeneratorProfileSettings", source)
        self.assertIn("open: openGeneratorProfileSettings,", source)
        self.assertIn("openProfileSettings: openGeneratorProfileSettings,", source)
        self.assertIn("panel.append(main)", panel_source)
        self.assertNotIn("profileBar", panel_source)
        for path in (
            "/easyuse_anima/aio_profiles",
            "/easyuse_anima/aio_profiles/save",
            "/easyuse_anima/aio_profiles/load",
            "/easyuse_anima/aio_profiles/rename",
            "/easyuse_anima/aio_profiles/delete",
        ):
            self.assertIn(path, api_client_source)
            self.assertNotIn(path, source)
        self.assertIn(
            "fetchJson: (url, options) => easyuseAnimaFetchComfyJson(api, url, options)",
            source,
        )
        self.assertIn("profileApi: generatorProfileApi", source)
        self.assertIn("getSettings: generatorSettings", source)
        self.assertIn("writeSettings: writeGeneratorSettingsFromState", source)
        self.assertNotIn("__easyuseAnimaGeneratorProfileValue", serialize_body)

    def test_generator_panel_height_is_owned_by_comfyui(self):
        source = AIO_JS.read_text(encoding="utf-8")
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        panel_start = source.index("    .easyuse-anima-aio-node-panel {")
        panel_end = source.index("\n    .easyuse-anima-aio-node-panel *", panel_start)
        panel_style = source[panel_start:panel_end]
        main_start = source.index("    .easyuse-anima-aio-node-main {")
        main_end = source.index("\n    .easyuse-anima-aio-node-card {", main_start)
        main_style = source[main_start:main_end]
        settings_start = source.index("    .easyuse-anima-aio-node-settings {")
        settings_end = source.index("\n    .easyuse-anima-aio-node-settings-scroll {", settings_start)
        settings_style = source[settings_start:settings_end]
        scroll_start = settings_end + 1
        scroll_end = source.index("\n    .easyuse-anima-aio-node-settings-scroll::-webkit-scrollbar", scroll_start)
        scroll_style = source[scroll_start:scroll_end]
        preview_start = source.index("    .easyuse-anima-aio-node-preview {")
        preview_end = source.index("\n    .easyuse-anima-aio-node-sampler-actions {", preview_start)
        preview_style = source[preview_start:preview_end]
        preview_box_start = source.index("    .easyuse-anima-aio-node-preview-box {")
        preview_box_end = source.index("\n    .easyuse-anima-aio-node-preview-box img {", preview_box_start)
        preview_box_style = source[preview_box_start:preview_box_end]
        self.assertIn("getMinHeight: () => GENERATOR_PANEL_MIN_HEIGHT", panel_source)
        self.assertNotIn("getHeight:", panel_source)
        self.assertNotIn("computeLayoutSize", panel_source)
        combined_source = source + panel_source
        self.assertNotIn("computedHeight =", combined_source)
        self.assertNotIn("generatorNodeChromeOffset", combined_source)
        self.assertNotIn("generatorAvailablePanelHeight", combined_source)
        self.assertNotIn("generatorPanelHeight", combined_source)
        self.assertNotIn("node.setSize?.(", panel_source)
        self.assertNotIn("node.setSize(", panel_source)
        self.assertNotIn("panel.style.height =", panel_source)
        self.assertIn('panel.style.removeProperty("height")', panel_source)
        self.assertIn('panel.style.removeProperty("max-height")', panel_source)

        self.assertIn("flex: 1 1 0%;", panel_style)
        self.assertIn("contain: size;", panel_style)
        self.assertIn("min-height: 0;", main_style)
        self.assertIn("overflow: hidden;", main_style)
        self.assertNotIn("height: 100%;", main_style)
        self.assertNotIn("min-height: 284px;", main_style)
        self.assertNotIn("height: 100%;", settings_style)
        self.assertIn("flex: 1 1 0%;", scroll_style)
        self.assertIn("overflow-y: auto;", scroll_style)
        self.assertIn("overscroll-behavior: contain;", scroll_style)
        self.assertIn("min-height: 0;", preview_style)
        self.assertIn("overflow: hidden;", preview_style)
        self.assertNotIn("height: 100%;", preview_style)
        self.assertNotIn("min-height: 284px;", preview_style)
        self.assertIn("min-height: 0;", preview_box_style)
        self.assertNotIn("min-height: 210px;", preview_box_style)

    def test_generator_wheel_router_decides_scroll_ownership_before_canvas(self):
        source = AIO_JS.read_text(encoding="utf-8")
        extension_source = AIO_EXTENSION_RUNTIME_JS.read_text(encoding="utf-8")
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        wheel_source = AIO_WHEEL_JS.read_text(encoding="utf-8")
        forward_start = source.index("function forwardGeneratorPanelWheel")
        forward_end = source.index("\nfunction installGeneratorWheelForwarder", forward_start)
        forward_body = source[forward_start:forward_end]
        install_start = forward_end + 1
        install_end = source.index("\nfunction generatorSettings", install_start)
        install_body = source[install_start:install_end]
        setup_start = extension_source.index("    async setup() {")
        setup_end = extension_source.index(
            "\n    async beforeRegisterNodeDef", setup_start
        )
        setup_body = extension_source[setup_start:setup_end]

        self.assertIn('from "./aio/wheel.js"', source)
        self.assertIn(
            'root.addEventListener("wheel", forwardGeneratorPanelWheel',
            panel_source,
        )
        self.assertIn("capture: true", panel_source)
        self.assertIn("passive: false", panel_source)
        self.assertIn("consumeAioPanelWheel(event, panel)", forward_body)
        self.assertLess(
            forward_body.index("consumeAioPanelWheel(event, panel)"),
            forward_body.index("dispatchGeneratorCanvasWheelEvent(event)"),
        )
        self.assertIn('window.addEventListener("wheel", forwardGeneratorPanelWheel', install_body)
        self.assertIn("capture: true", install_body)
        self.assertIn("passive: false", install_body)
        self.assertIn("installWheelForwarder();", setup_body)
        self.assertIn(
            "installWheelForwarder: installGeneratorWheelForwarder,", source
        )
        self.assertIn(
            'const AIO_PREVIEW_SELECTOR = ".easyuse-anima-aio-node-preview";',
            wheel_source,
        )
        self.assertIn("The preview surface always owns wheel input", wheel_source)
        self.assertIn("unrelated panel space available", wheel_source)

    def test_generator_keeps_native_output_preview_suppressed_after_execution(self):
        source = AIO_JS.read_text(encoding="utf-8")
        extension_source = AIO_EXTENSION_RUNTIME_JS.read_text(encoding="utf-8")
        native_preview_source = AIO_NATIVE_PREVIEW_RUNTIME_JS.read_text(
            encoding="utf-8"
        )
        preview_source = AIO_PREVIEW_JS.read_text(encoding="utf-8")
        registration_start = extension_source.index("async beforeRegisterNodeDef")
        generator_block = extension_source[
            extension_source.index(
                "if (nodeData.name === GENERATOR_NODE_TYPE)", registration_start
            ):
        ]
        start = generator_block.index("nodeType.prototype.onExecuted = function")
        end = generator_block.index("const onResize = nodeType.prototype.onResize;", start)
        body = generator_block[start:end]

        self.assertIn("nodeType.prototype.hideOutputImages = true", extension_source)
        for store_alias in (
            "module?.useNodeOutputStore,",
            "module?.cn,",
            "module?.L,",
            "module?.useWorkflowStore,",
            "module?.M,",
        ):
            self.assertIn(store_alias, native_preview_source)
        self.assertGreaterEqual(
            native_preview_source.count(
                '.find((candidate) => typeof candidate === "function")'
            ),
            2,
        )
        self.assertIn(
            "outputStore.revokePreviewsByLocatorId?.(locator);",
            native_preview_source,
        )
        self.assertIn("getLegacyPreviewImages: () => app.nodePreviewImages", source)
        self.assertIn(
            "aioDeletePreviewStoreEntry(legacyPreviewImages, id);",
            native_preview_source,
        )
        self.assertIn(
            "aioDeletePreviewStoreEntry(outputStore.nodePreviewImages, locator);",
            native_preview_source,
        )
        self.assertIn('Object.defineProperty(node, "imgs"', preview_source)
        self.assertIn("lockLegacyCanvasPreview(node);", preview_source)
        self.assertIn("aioSuppressDefaultPreview", native_preview_source)
        self.assertIn(".lg-node:has(.easyuse-anima-aio-node-panel) .text-node-component-header-text", source)
        self.assertIn(".lg-node:has(.easyuse-anima-aio-node-panel) .pt-2.text-center.text-xs.text-base-foreground", source)
        self.assertIn("scheduleDefaultPreviewSuppression(this);", body)
        self.assertIn("updateExecutedStatus(this, message);", body)
        self.assertIn(
            "scheduleDefaultPreviewSuppression(this, { purgeStore: false });",
            body,
        )
        self.assertEqual(
            body.count("scheduleDefaultPreviewSuppression(this"),
            2,
        )
        self.assertLess(
            body.index("scheduleDefaultPreviewSuppression(this);"),
            body.index("updateExecutedStatus(this, message);"),
        )
        self.assertLess(
            body.index("updateExecutedStatus(this, message);"),
            body.index(
                "scheduleDefaultPreviewSuppression(this, "
                "{ purgeStore: false });"
            ),
        )
        self.assertNotIn("onExecuted?.apply", body)
        self.assertIn(
            "scheduleDefaultPreviewSuppression: "
            "scheduleGeneratorDefaultPreviewSuppression,",
            source,
        )
        self.assertIn(
            "updateExecutedStatus: updateGeneratorExecutedStatus,", source
        )

        suppression_start = native_preview_source.index(
            "function scheduleGeneratorDefaultPreviewSuppression"
        )
        suppression_end = native_preview_source.index(
            "\n  function findGeneratorNodeByQualifiedId", suppression_start
        )
        suppression_body = native_preview_source[suppression_start:suppression_end]
        delayed_start = suppression_body.index("const suppress =")
        delayed_end = suppression_body.index(
            "\n    scheduleGeneratorNativePreviewFrame", delayed_start
        )
        delayed_body = suppression_body[delayed_start:delayed_end]
        self.assertIn(
            "scheduleGeneratorNativeLivePreviewPurge(node, purgeDetail);",
            suppression_body[:delayed_start],
        )
        self.assertNotIn(
            "scheduleGeneratorNativeLivePreviewPurge(",
            delayed_body,
        )

    def test_generator_native_preview_lifecycle_disposes_on_generator_removal(self):
        source = AIO_JS.read_text(encoding="utf-8")
        extension_source = AIO_EXTENSION_RUNTIME_JS.read_text(encoding="utf-8")
        registration_start = extension_source.index("async beforeRegisterNodeDef")
        configure_start = extension_source.index(
            "const onConfigure = nodeType.prototype.onConfigure;",
            registration_start,
        )
        generator_hooks_start = extension_source.index(
            "      if (nodeData.name === GENERATOR_NODE_TYPE) {",
            configure_start,
        )
        generator_hooks_end = extension_source.index(
            "\n      }\n    },\n  };",
            generator_hooks_start,
        )
        generator_hooks = extension_source[
            generator_hooks_start:generator_hooks_end
        ]

        self.assertNotIn(
            "const onRemoved = nodeType.prototype.onRemoved;",
            extension_source[registration_start:generator_hooks_start],
        )
        self.assertEqual(
            extension_source.count(
                "const onRemoved = nodeType.prototype.onRemoved;"
            ),
            1,
        )
        on_removed_start = generator_hooks.index(
            "const onRemoved = nodeType.prototype.onRemoved;"
        )
        on_removed_end = generator_hooks.index("};", on_removed_start)
        on_removed_body = generator_hooks[on_removed_start:on_removed_end]

        original_return = on_removed_body.index(
            "return onRemoved?.apply(this, arguments);"
        )
        outer_finally = on_removed_body.index("finally", original_return)
        panel_cleanup = on_removed_body.index(
            "disposePanel(this);",
            outer_finally,
        )
        nested_finally = on_removed_body.index("finally", panel_cleanup)
        native_cleanup = on_removed_body.index(
            "disposeNativePreviewLifecycle(this);",
            nested_finally,
        )

        self.assertLess(on_removed_body.index("try"), original_return)
        self.assertLess(original_return, outer_finally)
        self.assertLess(outer_finally, panel_cleanup)
        self.assertLess(panel_cleanup, nested_finally)
        self.assertLess(nested_finally, native_cleanup)
        self.assertEqual(on_removed_body.count("disposePanel(this);"), 1)
        self.assertEqual(
            on_removed_body.count("disposeNativePreviewLifecycle(this);"),
            1,
        )
        self.assertIn("disposePanel: disposeGeneratorPanel,", source)
        self.assertIn(
            "disposeNativePreviewLifecycle: "
            "disposeGeneratorNativePreviewLifecycle,",
            source,
        )

    def test_generator_panel_runtime_exposes_cancellable_lifecycle_facades(self):
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")

        factory_start = panel_source.index(
            "export function aioCreateGeneratorPanelRuntime(dependencies)"
        )
        dependency_end = panel_source.index("} = dependencies;", factory_start)
        dependency_block = panel_source[factory_start:dependency_end]
        for dependency in ("requestAnimationFrame", "cancelAnimationFrame"):
            with self.subTest(runtime_dependency=dependency):
                self.assertRegex(dependency_block, rf"\b{dependency}\s*,")

        return_start = panel_source.rindex("\n  return {")
        return_end = panel_source.index("\n  };", return_start)
        return_body = panel_source[return_start:return_end]
        for public_method in ("disposePanel", "scheduleSummary"):
            with self.subTest(runtime_public_method=public_method):
                self.assertRegex(
                    return_body,
                    rf"(?m)^\s*{public_method}(?:\s*:\s*[A-Za-z_$][\w$]*)?,\s*$",
                )

        dispose_start = panel_source.index("function disposeGeneratorPanel(node)")
        dispose_end = panel_source.index("\n  function ", dispose_start + 1)
        dispose_body = panel_source[dispose_start:dispose_end]
        self.assertIn("cancelAnimationFrame(", dispose_body)

        summary_start = panel_source.index("function scheduleGeneratorSummary(node)")
        summary_end = panel_source.index("\n  function ", summary_start + 1)
        summary_body = panel_source[summary_start:summary_end]
        self.assertIn(
            'scheduleGeneratorPanelFrame(node, "summary"',
            summary_body,
        )
        self.assertNotIn("requestAnimationFrame", summary_body)

        entry_factory_start = entry_source.index(
            "const generatorPanelRuntime = aioCreateGeneratorPanelRuntime({"
        )
        entry_factory_end = entry_source.index("\n});", entry_factory_start)
        entry_factory = entry_source[entry_factory_start:entry_factory_end]
        self.assertRegex(
            entry_factory,
            r"cancelAnimationFrame:\s*\([^)]*\)\s*=>\s*cancelAnimationFrame\([^)]*\),",
        )

        dispose_wrapper_start = entry_source.index(
            "function disposeGeneratorPanel(node)"
        )
        dispose_wrapper_end = entry_source.index(
            "\nfunction ",
            dispose_wrapper_start + 1,
        )
        dispose_wrapper = entry_source[dispose_wrapper_start:dispose_wrapper_end]
        self.assertIn("generatorPanelRuntime.disposePanel(node)", dispose_wrapper)

    def test_generator_preview_summary_uses_runtime_scheduler_facade(self):
        source = AIO_JS.read_text(encoding="utf-8")

        wrapper_start = source.index("function scheduleGeneratorSummary(node)")
        wrapper_end = source.index("\nfunction ", wrapper_start + 1)
        wrapper_body = source[wrapper_start:wrapper_end]
        self.assertIn("generatorPanelRuntime.scheduleSummary(node)", wrapper_body)

        preview_start = source.index("function addGeneratorPreviewImagesToNode")
        preview_end = source.index(
            "\nfunction updateGeneratorExecutedStatus",
            preview_start,
        )
        preview_body = source[preview_start:preview_end]
        self.assertIn("scheduleGeneratorSummary(node);", preview_body)
        self.assertNotIn("requestAnimationFrame", preview_body)

    def test_generator_terminal_empty_uses_pure_preview_state(self):
        source = AIO_JS.read_text(encoding="utf-8")
        preview_import_end = source.index('from "./aio/preview.js";')
        self.assertIn(
            "aioResolveTerminalPreviewState,",
            source[:preview_import_end],
        )

        preview_start = source.index("function addGeneratorPreviewImagesToNode")
        preview_end = source.index(
            "\nfunction updateGeneratorExecutedStatus",
            preview_start,
        )
        preview_body = source[preview_start:preview_end]
        empty_start = preview_body.index("if (!nextImages.length)")
        normal_preview_start = preview_body.index(
            "\n  clearGeneratorDenoisePreview(node);",
            empty_start,
        )
        empty_body = preview_body[empty_start:normal_preview_start]

        self.assertEqual(empty_body.count("aioResolveTerminalPreviewState("), 1)
        self.assertIn("clearGeneratorDenoisePreview(node);", empty_body)
        for assignment in (
            "node.__easyuseAnimaGeneratorCurrentRunImages = terminalState.currentRunImages;",
            "node.__easyuseAnimaGeneratorPreviewFeedImages = terminalState.previewFeedImages;",
            "node.__easyuseAnimaGeneratorPreviewImages = terminalState.previewImages;",
            "node.__easyuseAnimaSelectedPreviewIndex = terminalState.selectedIndex;",
        ):
            with self.subTest(terminal_assignment=assignment):
                self.assertIn(assignment, empty_body)
        self.assertIn("delete node.__easyuseAnimaSelectedPreviewIndex;", empty_body)
        self.assertIn("updateGeneratorDomSummary(node);", empty_body)
        self.assertIn("scheduleGeneratorSummary(node);", empty_body)
        self.assertIn("scheduleGeneratorLayout(node);", empty_body)
        self.assertNotIn("aioRemovePreviewRun(", empty_body)

        helper_call = empty_body.index("aioResolveTerminalPreviewState(")
        self.assertLess(empty_body.index("clearGeneratorDenoisePreview(node);"), helper_call)
        self.assertLess(
            helper_call,
            empty_body.index("scheduleGeneratorSummary(node);"),
        )

    def test_generator_denoise_blob_cleanup_stays_native_lifecycle_owned(self):
        source = AIO_JS.read_text(encoding="utf-8")
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        native_source = AIO_NATIVE_PREVIEW_RUNTIME_JS.read_text(encoding="utf-8")

        clear_start = source.index("function clearGeneratorDenoisePreview")
        clear_end = source.index("\nfunction setGeneratorDenoisePreview", clear_start)
        clear_body = source[clear_start:clear_end]
        revoke = clear_body.index("URL.revokeObjectURL(preview.url);")
        delete = clear_body.index(
            "delete node.__easyuseAnimaGeneratorDenoisePreview;"
        )
        self.assertLess(revoke, delete)

        native_factory_start = source.index("aioCreateNativePreviewRuntime({")
        native_factory_end = source.index("\n});", native_factory_start)
        native_factory = source[native_factory_start:native_factory_end]
        self.assertIn(
            "clearDenoisePreview: clearGeneratorDenoisePreview,",
            native_factory,
        )
        dispose_start = native_source.index(
            "function disposeGeneratorNativePreviewLifecycle(node)"
        )
        dispose_end = native_source.index("\n  function ", dispose_start + 1)
        dispose_body = native_source[dispose_start:dispose_end]
        self.assertIn("clearGeneratorDenoisePreview(node, false);", dispose_body)
        self.assertNotIn("URL.revokeObjectURL", panel_source)

    def test_generator_sampler_hydration_refresh_has_single_owner(self):
        source = AIO_JS.read_text(encoding="utf-8")
        extension_source = AIO_EXTENSION_RUNTIME_JS.read_text(encoding="utf-8")
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")

        hook_start = source.index("function hookGeneratorNode(node)")
        hook_end = source.index(
            "\nfunction addGeneratorPreviewImagesToNode", hook_start
        )
        hook_body = source[hook_start:hook_end]
        self.assertEqual(hook_body.count("ensureGeneratorPanel(node);"), 1)
        self.assertNotIn("loadGeneratorSamplerOptions(", hook_body)
        self.assertNotIn("renderGeneratorPanel(", hook_body)

        ensure_start = panel_source.index("  function ensureGeneratorPanel(node)")
        ensure_end = panel_source.index("\n\n  return {", ensure_start)
        ensure_body = panel_source[ensure_start:ensure_end]
        self.assertEqual(
            ensure_body.count("renderGeneratorPanel(node, lifecycleState);"),
            1,
        )

        setup_start = extension_source.index("    async setup() {")
        setup_end = extension_source.index(
            "\n    async beforeRegisterNodeDef", setup_start
        )
        setup_body = extension_source[setup_start:setup_end]
        self.assertEqual(
            setup_body.count("loadSamplerOptions().then(refreshPanels);"),
            1,
        )
        refresh_start = source.index("function refreshGeneratorPanels()")
        refresh_end = source.index("\nfunction findWidget", refresh_start)
        refresh_body = source[refresh_start:refresh_end]
        self.assertIn(
            "aioListAttachedGeneratorNodes(app.graph, isGeneratorGraphNode)",
            refresh_body,
        )
        self.assertNotIn("generatorGraphNodes()", refresh_body)
        self.assertIn(
            "export function aioListAttachedGeneratorNodes(",
            extension_source,
        )
        self.assertIn("Array.isArray(graph?.nodes)", extension_source)
        self.assertIn("node.subgraph", extension_source)
        self.assertIn("visitedGraphs", extension_source)
        self.assertIn("visitedNodes", extension_source)
        self.assertIn(
            "loadSamplerOptions: loadGeneratorSamplerOptions,", source
        )

    def test_generator_panel_lifecycle_keeps_entry_behavior_boundaries(self):
        source = AIO_JS.read_text(encoding="utf-8")
        extension_source = AIO_EXTENSION_RUNTIME_JS.read_text(encoding="utf-8")
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        queue_source = AIO_GENERATOR_QUEUE_RUNTIME_JS.read_text(encoding="utf-8")

        for entry_owned_function in (
            "loadGeneratorSamplerOptions",
            "installGeneratorQueuePromptHook",
            "installGeneratorWheelForwarder",
        ):
            with self.subTest(entry_owned_function=entry_owned_function):
                self.assertRegex(
                    source,
                    rf"\bfunction\s+{entry_owned_function}\(",
                )
                self.assertNotRegex(
                    panel_source,
                    rf"\bfunction\s+{entry_owned_function}\(",
                )

        for queue_owned_function in (
            "resolveQueuedSeed",
            "preparePrompt",
        ):
            with self.subTest(queue_owned_function=queue_owned_function):
                self.assertRegex(
                    queue_source,
                    rf"\bfunction\s+{queue_owned_function}\(",
                )
        self.assertNotIn("resolveGeneratorSeedForQueue", source)
        self.assertNotIn("prepareGeneratorPromptForQueue", source)

        setup_start = extension_source.index("    async setup() {")
        setup_end = extension_source.index(
            "\n    async beforeRegisterNodeDef", setup_start
        )
        setup_body = extension_source[setup_start:setup_end]
        self.assertIn("installWheelForwarder();", setup_body)
        self.assertIn("installGlobalHooks();", setup_body)
        self.assertIn(
            "installWheelForwarder: installGeneratorWheelForwarder,", source
        )
        self.assertIn(
            "installQueuePromptHook: installGeneratorQueuePromptHook,", source
        )

        for unchanged_adapter in (
            "specialSeedRandom: GENERATOR_SPECIAL_SEED_RANDOM,",
            "fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,",
            "fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,",
            "randomSeed,",
        ):
            with self.subTest(unchanged_panel_adapter=unchanged_adapter):
                self.assertIn(unchanged_adapter, source)

    def test_generator_preview_meta_keeps_dedicated_resolution_label(self):
        source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        meta_start = source.index("const parts = [")
        meta_end = source.index("].filter", meta_start)
        meta_parts = source[meta_start:meta_end]

        self.assertIn("aioPreviewImageName(currentImage)", meta_parts)
        self.assertIn("aioPreviewResolution(currentImage)", meta_parts)
        self.assertIn("aioPreviewFileSize(currentImage)", meta_parts)

    def test_detailer_target_editor_builds_optimization_before_visibility_refresh(self):
        source = AIO_DETAILER_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        start = source.index("function createDetailerTargetEditor")
        end = source.index("\n  function openDetailerSettings", start)
        body = source[start:end]

        self.assertLess(
            body.index("const optimization = createStageOptimizationEditor"),
            body.index("updateInheritedRows();"),
        )
        self.assertNotIn('optimization.section.classList.toggle("hidden"', body)

    def test_highres_settings_save_stage_optimization(self):
        source = AIO_STAGE_SETTINGS_DIALOGS_JS.read_text(encoding="utf-8")
        start = source.index("function openHighresSettings")
        end = source.index("\n  function openUpscaleSettings", start)
        body = source[start:end]

        self.assertIn('createStageOptimizationEditor("Highres Optimization"', body)
        self.assertIn("const optimized = optimization.values();", body)
        self.assertIn("...optimized,", body)
        self.assertNotIn("next.highres.spectrum = mergeDefaults", body)
        self.assertNotIn("next.highres.dit_corrections = mergeDefaults", body)

    def test_upscale_settings_offer_single_backend_and_usdu_helpers(self):
        source = AIO_STAGE_SETTINGS_DIALOGS_JS.read_text(encoding="utf-8")
        start = source.index("function openUpscaleSettings")
        end = source.index("\n\n  return {", start)
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
        self.assertIn("reconcileSelectInput(", body)
        self.assertIn("upscaleModel.value", body)
        self.assertIn("closed || backdrop.isConnected === false", body)
        self.assertIn("upscaleBackendMissingPacks(backend.value)", body)
        self.assertIn("enabled: enabled.checked && missingPacks.length === 0", body)
        self.assertIn("resshiftSection", body)
        self.assertIn("resshift:", body)

    def test_sam3_checkpoint_uses_checkpoint_loader_catalog_and_late_hydration(self):
        body = AIO_DETAILER_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")

        self.assertIn('"checkpointLoader"', body)
        self.assertIn('"ckpt_name"', body)
        self.assertIn("selectInput(", body)
        self.assertIn("reconcileSelectInput(", body)
        self.assertIn("checkpoint.value", body)
        self.assertIn("closed || backdrop.isConnected === false", body)

    def test_postprocess_settings_own_final_fit_controls(self):
        body = AIO_POSTPROCESS_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")

        self.assertIn('createDialog(', body)
        self.assertIn('"Postprocess Settings"', body)
        self.assertIn('textContent: staticText("Final Size Fit")', body)
        self.assertIn('"Enable postprocess"', body)
        self.assertIn('"max_long_edge"', body)
        self.assertIn('"megapixels"', body)
        self.assertIn("next.postprocess = {", body)
        self.assertIn("fit: {", body)
        self.assertIn("max_long_edge: Math.trunc", body)
        self.assertIn("max_megapixels: clampNumber", body)
        self.assertIn("...postprocess", body)
        self.assertIn("...fit", body)
        self.assertIn("delete next.upscale?.fit", body)

    def test_upscale_optional_dependency_sanitizer_disables_missing_backend(self):
        source = AIO_JS.read_text(encoding="utf-8")
        start = source.index("function sanitizeGeneratorSettingsForOptionalDependencies")
        end = source.index("\nfunction applyVisibleGeneratorSettings", start)
        body = source[start:end]

        self.assertIn("disableGeneratorSpectrumOptions(next.upscale)", body)
        self.assertIn("upscaleBackendMissingPacks(next.upscale.backend).length", body)
        self.assertIn("next.upscale.enabled = false", body)

    def test_optional_dependency_query_adapter_updates_cache_and_reports_results(self):
        source = AIO_JS.read_text(encoding="utf-8")
        fetch_start = source.index("async function fetchGeneratorOptionalDependencies")
        fetch_end = source.index("\nfunction optionalDependencyResultLabel", fetch_start)
        fetch_body = source[fetch_start:fetch_end]
        report_start = source.index("function reportGeneratorOptionalDependencyStatus")
        report_end = source.index("\nfunction loadGeneratorOptionalDependencies", report_start)
        report_body = source[report_start:report_end]

        self.assertIn("aioQueryOptionalDependencies(", fetch_body)
        self.assertIn("AIO_OPTIONAL_DEPENDENCY_SPECS", fetch_body)
        self.assertIn(
            "easyuseAnimaFetchComfyJson(api, `/object_info/${encodeURIComponent(spec.nodeId)}`)",
            fetch_body,
        )
        self.assertIn("return data?.[spec.nodeId] || null", fetch_body)
        for cache_name in ("available", "status", "nodeInfo", "errors"):
            with self.subTest(cache_name=cache_name):
                self.assertIn(
                    f"generatorOptionalDependencyState.{cache_name} = next.{cache_name}",
                    fetch_body,
                )
        self.assertIn('console.info("[EasyUseAnima] AiO optional dependency query result", rows)', report_body)
        self.assertIn('severity: failed.length ? "warn" : "info"', report_body)
        self.assertIn("app.ui.dialog.show", report_body)

    def test_optional_dependency_query_retries_errors_before_queueing(self):
        source = AIO_JS.read_text(encoding="utf-8")
        queue_source = AIO_GENERATOR_QUEUE_RUNTIME_JS.read_text(encoding="utf-8")
        load_start = source.index("function loadGeneratorOptionalDependencies")
        load_end = source.index("\nfunction optionalDependencyStatus", load_start)
        load_body = source[load_start:load_end]
        composition_start = source.index(
            "const generatorQueueRuntime = aioCreateGeneratorQueueRuntime({"
        )
        composition_end = source.index("\n});", composition_start)
        composition_body = source[composition_start:composition_end]

        self.assertIn("retryErrors = false", load_body)
        self.assertIn('includes("error")', load_body)
        self.assertIn("generatorOptionalDependencyState.loading = null", load_body)
        self.assertIn(
            "loadOptionalDependencies: loadGeneratorOptionalDependencies,",
            composition_body,
        )
        self.assertIn(
            "loadOptionalDependencies({ retryErrors: true })",
            queue_source,
        )

    def test_generator_panel_renders_upscale_after_detailer(self):
        body = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")

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
        source = AIO_ADVANCED_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        start = source.index("function openAdvancedSettings")
        end = source.index("  return openAdvancedSettings;", start)
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
        entry_source = AIO_JS.read_text(encoding="utf-8")
        source = AIO_SAVE_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        settings_source = AIO_SETTINGS_JS.read_text(encoding="utf-8")
        start = source.index("function openSaveSettings")
        end = source.index("\n\n  return openSaveSettings", start)
        body = source[start:end]

        self.assertIn("save_prompt_metadata: true", settings_source)
        self.assertIn('field(metadata, "Save prompt metadata"', body)
        self.assertIn("checkbox(imageSaver.save_prompt_metadata)", body)
        self.assertIn("save_prompt_metadata: savePromptMetadata.checked", body)
        self.assertIn('"Save prompt metadata": "tip.savePromptMetadata"', entry_source)

    def test_detailer_settings_support_custom_blocks(self):
        source = AIO_DETAILER_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        start = source.index("function openDetailerSettings")
        end = source.index("\n\n  return openDetailerSettings", start)
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
        controller_source = AUTOCOMPLETE_INPUT_CONTROLLER_JS.read_text(
            encoding="utf-8"
        )
        binding_source = AUTOCOMPLETE_INPUT_BINDING_JS.read_text(encoding="utf-8")
        hook_start = source.index("function hookInput")
        hook_end = source.index("\nfunction hookWidget", hook_start)
        hook_body = source[hook_start:hook_end]

        self.assertIn("document.activeElement !== input", hook_body)
        self.assertIn(
            'listen("compositionstart", controller.beginComposition);',
            binding_source,
        )
        self.assertIn(
            'listen("compositionupdate", controller.scheduleUpdate);',
            binding_source,
        )
        self.assertIn(
            'listen("compositionend", controller.endComposition);',
            binding_source,
        )
        self.assertIn("function beginComposition()", controller_source)
        self.assertIn("function endComposition()", controller_source)
        self.assertIn("function scheduleUpdate()", controller_source)
        self.assertIn("function isComposing(event = null)", controller_source)
        self.assertIn(
            "if (!controller.isComposing(event) "
            "&& handleBracketPreviewKeydown(state, event))",
            binding_source,
        )

        keydown_start = binding_source.index("function handleNavigation")
        keydown_end = binding_source.index("\n\n  listen(", keydown_start)
        keydown_body = binding_source[keydown_start:keydown_end]

        self.assertIn("controller.isComposing(event)", keydown_body)
        self.assertLess(
            keydown_body.index("controller.isComposing(event)"),
            keydown_body.index("const active = activeForInput();"),
        )

    def test_autocomplete_public_flag_tracks_enabled_state(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        binding_source = AUTOCOMPLETE_INPUT_BINDING_JS.read_text(encoding="utf-8")

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

        self.assertIn(
            'existing?.owner === autocompleteInputOwner && typeof existing.dispose === "function"',
            hook_body,
        )
        self.assertIn("syncAutocompleteInputFlag(input, existing);", hook_body)
        self.assertIn(
            "input.__easyuseAnimaAutocompleteDispose = existing.dispose;",
            hook_body,
        )
        self.assertIn("state.binding = createAutocompleteInputBinding({", hook_body)
        self.assertIn("owner: autocompleteInputOwner,", hook_body)
        self.assertIn("registry: hookedAutocompleteInputs,", hook_body)
        self.assertIn("registry.add(input);", binding_source)
        self.assertIn("syncAutocompleteInputFlag(input, state);", hook_body)
        self.assertIn("return existing.dispose;", hook_body)
        self.assertIn("return state.dispose;", hook_body)

    def test_autocomplete_arrow_navigation_keeps_adjacent_items_visible(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("function scrollActiveAutocompleteItemIntoView")
        end = source.index("\nfunction setActive", start)
        scroll_body = source[start:end]

        self.assertIn("index - 1", scroll_body)
        self.assertIn("index + 1", scroll_body)
        self.assertIn("menu.scrollTop", scroll_body)

        start = source.index("function setActive")
        end = source.index("\nfunction resetAutocompleteMenuToTop", start)
        set_active_body = source[start:end]

        self.assertIn("const menu = ensurePopup();", set_active_body)
        self.assertIn("scrollActiveAutocompleteItemIntoView(menu, activeState.index);", set_active_body)

    def test_autocomplete_resets_scroll_for_new_result_sets(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        start = source.index("function hidePopup")
        end = source.index("\nfunction hideTrainedTagTooltips", start)
        hide_body = source[start:end]

        self.assertIn("markAutocompleteInputInactive(input);", hide_body)
        self.assertIn("controller?.invalidate();", hide_body)
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
        end = source.index("\nfunction replaceInputRange", start)
        visible_reset_body = source[start:end]

        self.assertIn("resetAutocompleteMenuToTop(menu);", visible_reset_body)
        self.assertIn("requestAnimationFrame(() => {", visible_reset_body)
        self.assertIn('!menu.classList.contains("hidden")', visible_reset_body)
        self.assertNotIn("resetActiveAutocompleteMenu(menu);", visible_reset_body)

        start = source.index("function renderResults")
        end = source.index("\nfunction isTextEditingShortcut", start)
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

        start = source.index("    onUpdate: async ({ isCurrent, request }) => {")
        end = source.index("      const results = await request(", start)
        update_body = source[start:end]

        self.assertIn("lastAutocompleteSignature: undefined", source)
        self.assertIn("const previousSignature = state.lastAutocompleteSignature;", update_body)
        self.assertIn("state.lastAutocompleteSignature = signature;", update_body)
        self.assertIn("previousSignature !== undefined && previousSignature !== signature", update_body)
        self.assertIn("resetActiveAutocompleteMenu(ensurePopup());", update_body)

        start = source.index("function handleOutsideAutocompletePointer")
        end = source.index("\nfunction handleAutocompleteSettingsUpdated", start)
        pointer_body = source[start:end]

        self.assertIn("popup?.contains(event.target)", pointer_body)
        self.assertIn("event.target === input", pointer_body)
        self.assertIn("markAutocompleteInputInactive(input);", pointer_body)
        self.assertIn("hidePopup();", pointer_body)
        self.assertIn(
            "handleOutsidePointer: handleOutsideAutocompletePointer",
            source,
        )
        lifecycle_source = AUTOCOMPLETE_ENTRY_LIFECYCLE_JS.read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'listen(hostDocument, "pointerdown", handleOutsidePointer, true);',
            lifecycle_source,
        )
        self.assertIn(
            'listen(hostDocument, "mousedown", handleOutsidePointer, true);',
            lifecycle_source,
        )

    def test_autocomplete_wildcards_accept_empty_and_unicode_queries(self):
        source = AUTOCOMPLETE_JS.read_text(encoding="utf-8")
        data_adapter_source = AUTOCOMPLETE_DATA_ADAPTER_JS.read_text(encoding="utf-8")
        model_source = AUTOCOMPLETE_TEXT_MODEL_JS.read_text(encoding="utf-8")
        start = model_source.index("export function currentWildcardToken")
        end = model_source.index(
            "\nexport function isCaretInPromptTranslationMarker",
            start,
        )
        token_body = model_source[start:end]

        self.assertIn("safeCaret >= opening + 2", token_body)
        self.assertIn(r"/[\r\n,]/.test(query)", token_body)
        self.assertNotIn(r"/^[\w.\-+/*\\]*$/i.test(query)", token_body)

        start = model_source.index("export function normalizeWildcardSearchText")
        end = model_source.index("\nfunction endsWithSentencePeriod", start)
        normalize_body = model_source[start:end]

        self.assertIn('replaceAll("\\\\", "/")', normalize_body)
        self.assertIn('replace(/[ _]+/g, "-")', normalize_body)

        start = data_adapter_source.index("function searchWildcards")
        end = data_adapter_source.index("\n\n  return {", start)
        search_body = data_adapter_source[start:end]

        self.assertIn("normalizeWildcardSearchText(query)", search_body)
        self.assertIn("normalizeWildcardSearchText(item).includes(normalized)", search_body)

        start = source.index("function strictAutocompleteResults")
        end = source.index("\nfunction copyCaretMirrorStyle", start)
        strict_body = source[start:end]

        self.assertIn('return context.kind === "wildcard" ? results : [];', strict_body)

    def test_autocomplete_strips_prompt_syntax_from_search_query(self):
        source = AUTOCOMPLETE_TEXT_MODEL_JS.read_text(encoding="utf-8")

        start = source.index("export function autocompleteQuery")
        end = source.index("\nexport function wildcardAutocompleteQuery", start)
        query_body = source[start:end]

        self.assertIn("const query = parsed.query;", query_body)
        self.assertNotIn("artistOnly ? parsed.query : raw.trim()", query_body)

        start = source.index("export function parseAutocompleteText")
        end = source.index("\nexport function autocompleteQuery", start)
        parse_body = source[start:end]

        self.assertIn(
            "query = query.slice(trimPromptSyntaxPrefix(query, 0, query.length));",
            parse_body,
        )
        self.assertIn("query = stripPromptSyntaxClosingParens(query);", parse_body)
        self.assertIn(
            'query = query.replace(/:\\s*[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)\\s*$/, "");',
            parse_body,
        )
        self.assertNotIn('query = query.replace(/\\)+\\s*$/, "");', parse_body)

        start = source.index("function trimPromptSyntaxSuffix")
        end = source.index("\nexport function currentToken", start)
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
        end = source.index("\nfunction currentToken", start)
        input_body = source[start:end]

        self.assertIn(
            "for (const candidate of [widget?.inputEl, widget?.element])",
            input_body,
        )
        self.assertIn("candidate.isConnected !== false", input_body)
        self.assertIn('candidate?.querySelector?.("textarea, input")', input_body)
        self.assertIn("nested.isConnected !== false", input_body)

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
        owner_start = source.index("function autocompleteDomInputOwner")
        owner_end = source.index("\nfunction hookFocusedDomInput", owner_start)
        owner_body = source[owner_start:owner_end]

        self.assertIn("const ancestryNode = nodeFromDomElement(input);", owner_body)
        self.assertIn("for (const node of autocompleteGraphNodes())", owner_body)
        self.assertIn("const widget = widgetForDomInput(node, input);", owner_body)
        self.assertIn("return { node, widget };", owner_body)
        self.assertIn("Array.isArray(graph?._nodes)", source)
        self.assertIn("Object.values(graph?._nodes_by_id || {})", source)

        start = source.index("function hookFocusedDomInput")
        end = source.index("\nfunction handleAutocompleteScroll", start)
        focus_body = source[start:end]

        self.assertIn("isAutocompleteDomInput(input)", focus_body)
        self.assertIn("const owner = autocompleteDomInputOwner(input);", focus_body)
        self.assertIn("if (!owner)", focus_body)
        self.assertIn("const { node, widget } = owner;", focus_body)
        self.assertIn("const targets = nodeData ? targetWidgets(nodeData) : null;", focus_body)
        self.assertIn("hookInput(input", focus_body)
        self.assertIn("hookFocusedInput: hookFocusedDomInput", source)
        lifecycle_source = AUTOCOMPLETE_ENTRY_LIFECYCLE_JS.read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'listen(hostDocument, "focusin", focusHook, true);',
            lifecycle_source,
        )
        self.assertIn("hookFocusedInput(hostDocument.activeElement);", lifecycle_source)
        self.assertNotIn("easyuseAnimaDebugAutocomplete", source)

    def test_prompt_highlight_wildcards_accept_unicode_keys(self):
        source = PROMPT_STUDIO_HIGHLIGHT_CORE_JS.read_text(encoding="utf-8")
        common_source = PROMPT_STUDIO_REGIONAL_ADAPTER_JS.read_text(
            encoding="utf-8"
        )

        self.assertIn(r"const WILDCARD_HIGHLIGHT_RE = /(?:\d+#)?__[\p{L}\p{N}_.\-+/*\\]+?__/gu;", source)
        self.assertNotIn(r"const WILDCARD_HIGHLIGHT_RE = /(?:\d+#)?__[\w.\-+/*\\]+?__/g;", source)

        start = source.index("function renderHighlightedText")
        end = source.index("\n  return renderHighlightedText;", start)
        body = source[start:end]

        self.assertLess(
            body.index("preferSyntaxBeforeToken && hasHighlightSyntax(body)"),
            body.index("const baseKey = normalize(tokenBase(body));"),
        )
        self.assertIn("html.push(syntaxHtml(body));", body)
        self.assertIn("preferSyntaxBeforeToken: true", common_source)


if __name__ == "__main__":
    unittest.main()
