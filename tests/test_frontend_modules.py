from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSCONFIG = ROOT / "jsconfig.json"
FRONTEND_CHECK_SCRIPT = ROOT / "tools" / "check_frontend.ps1"
HOST_HOOK_REGISTRY_SMOKE = ROOT / "tests" / "frontend_host_hook_registry_smoke.mjs"
PROMPT_STUDIO_ADVANCED_VALUES_SMOKE = (
    ROOT / "tests" / "frontend_prompt_studio_advanced_values_smoke.mjs"
)
PROMPT_STUDIO_WILDCARD_TRANSACTION_SMOKE = (
    ROOT / "tests" / "frontend_prompt_studio_wildcard_transaction_smoke.mjs"
)
PROMPT_STUDIO_RESOLUTION_ORIENTATION_SMOKE = (
    ROOT / "tests" / "frontend_prompt_studio_resolution_orientation_smoke.mjs"
)
WILDCARD_VALUES_SMOKE = ROOT / "tests" / "frontend_wildcard_values_smoke.mjs"
WEB_JS = ROOT / "web" / "js"
HOST_HOOK_REGISTRY_JS = WEB_JS / "lifecycle" / "host_hook_registry.js"
API_JS = WEB_JS / "easyuse_anima_api.js"
AIO_JS = WEB_JS / "easyuse_anima_aio.js"
AIO_MODULES = WEB_JS / "aio"
AIO_DEPENDENCIES_JS = AIO_MODULES / "dependencies.js"
AIO_DEPENDENCY_CORE_SMOKE = ROOT / "tests" / "frontend_aio_dependency_core_smoke.mjs"
AIO_DOM_CONTROLS_JS = AIO_MODULES / "dom_controls.js"
AIO_DOM_CONTROLS_CORE_SMOKE = (
    ROOT / "tests" / "frontend_aio_dom_controls_core_smoke.mjs"
)
AIO_DIALOG_PRIMITIVES_JS = AIO_MODULES / "dialog_primitives.js"
AIO_DIALOG_PRIMITIVES_SMOKE = (
    ROOT / "tests" / "frontend_aio_dialog_primitives_smoke.mjs"
)
AIO_INPUT_SETTINGS_DIALOG_JS = AIO_MODULES / "input_settings_dialog.js"
AIO_INPUT_SETTINGS_DIALOG_SMOKE = (
    ROOT / "tests" / "frontend_aio_input_settings_dialog_smoke.mjs"
)
AIO_POSTPROCESS_SETTINGS_DIALOG_JS = AIO_MODULES / "postprocess_settings_dialog.js"
AIO_POSTPROCESS_SETTINGS_DIALOG_SMOKE = (
    ROOT / "tests" / "frontend_aio_postprocess_settings_dialog_smoke.mjs"
)
AIO_PREVIEW_SETTINGS_DIALOG_JS = AIO_MODULES / "preview_settings_dialog.js"
AIO_PREVIEW_SETTINGS_DIALOG_SMOKE = (
    ROOT / "tests" / "frontend_aio_preview_settings_dialog_smoke.mjs"
)
AIO_PROFILE_API_CLIENT_JS = AIO_MODULES / "profile_api_client.js"
AIO_PROFILE_API_CLIENT_SMOKE = (
    ROOT / "tests" / "frontend_aio_profile_api_client_smoke.mjs"
)
AIO_PROFILE_DIALOGS_JS = AIO_MODULES / "profile_dialogs.js"
AIO_PROFILE_DIALOGS_SMOKE = ROOT / "tests" / "frontend_aio_profile_dialogs_smoke.mjs"
AIO_PROFILE_SETTINGS_RUNTIME_JS = AIO_MODULES / "profile_settings_runtime.js"
AIO_PROFILE_SETTINGS_RUNTIME_SMOKE = (
    ROOT / "tests" / "frontend_aio_profile_settings_runtime_smoke.mjs"
)
AIO_GENERATOR_PANEL_RUNTIME_JS = AIO_MODULES / "generator_panel_runtime.js"
AIO_GENERATOR_PANEL_RUNTIME_SMOKE = (
    ROOT / "tests" / "frontend_aio_generator_panel_runtime_smoke.mjs"
)
AIO_EXECUTED_SEED_RUNTIME_JS = AIO_MODULES / "executed_seed_runtime.js"
AIO_EXECUTED_SEED_RUNTIME_SMOKE = (
    ROOT / "tests" / "frontend_aio_executed_seed_runtime_smoke.mjs"
)
AIO_EXTENSION_RUNTIME_JS = AIO_MODULES / "extension_runtime.js"
AIO_EXTENSION_RUNTIME_SMOKE = (
    ROOT / "tests" / "frontend_aio_extension_runtime_smoke.mjs"
)
AIO_NATIVE_PREVIEW_RUNTIME_JS = AIO_MODULES / "native_preview_runtime.js"
AIO_NATIVE_PREVIEW_RUNTIME_SMOKE = (
    ROOT / "tests" / "frontend_aio_native_preview_runtime_smoke.mjs"
)
AIO_STAGE_SETTINGS_DIALOGS_JS = AIO_MODULES / "stage_settings_dialogs.js"
AIO_STAGE_SETTINGS_DIALOGS_SMOKE = (
    ROOT / "tests" / "frontend_aio_stage_settings_dialogs_smoke.mjs"
)
AIO_DETAILER_SETTINGS_DIALOG_JS = AIO_MODULES / "detailer_settings_dialog.js"
AIO_DETAILER_SETTINGS_DIALOG_SMOKE = (
    ROOT / "tests" / "frontend_aio_detailer_settings_dialog_smoke.mjs"
)
AIO_SAMPLER_SETTINGS_DIALOG_JS = AIO_MODULES / "sampler_settings_dialog.js"
AIO_SAMPLER_SETTINGS_DIALOG_SMOKE = (
    ROOT / "tests" / "frontend_aio_sampler_settings_dialog_smoke.mjs"
)
AIO_SAVE_SETTINGS_DIALOG_JS = AIO_MODULES / "save_settings_dialog.js"
AIO_SAVE_SETTINGS_DIALOG_SMOKE = (
    ROOT / "tests" / "frontend_aio_save_settings_dialog_smoke.mjs"
)
AIO_ADVANCED_SETTINGS_DIALOG_JS = AIO_MODULES / "advanced_settings_dialog.js"
AIO_ADVANCED_SETTINGS_DIALOG_SMOKE = (
    ROOT / "tests" / "frontend_aio_advanced_settings_dialog_smoke.mjs"
)
AIO_TORCH_COMPILE_RECOMMENDATION_JS = (
    AIO_MODULES / "torch_compile_recommendation.js"
)
AIO_TORCH_COMPILE_RECOMMENDATION_SMOKE = (
    ROOT / "tests" / "frontend_aio_torch_compile_recommendation_smoke.mjs"
)
AIO_PREVIEW_JS = AIO_MODULES / "preview.js"
AIO_PREVIEW_CORE_SMOKE = ROOT / "tests" / "frontend_aio_preview_core_smoke.mjs"
AIO_PRESETS_JS = AIO_MODULES / "presets.js"
AIO_PROFILE_CORE_SMOKE = ROOT / "tests" / "frontend_aio_profile_core_smoke.mjs"
AIO_SETTINGS_JS = AIO_MODULES / "settings.js"
AIO_SETTINGS_CORE_SMOKE = ROOT / "tests" / "frontend_aio_settings_core_smoke.mjs"
PROMPT_STUDIO_JS = WEB_JS / "easyuse_anima_prompt_studio.js"
PROMPT_STUDIO_COMMON_JS = WEB_JS / "easyuse_anima_prompt_studio_common.js"
PROMPT_STUDIO_MODULES = WEB_JS / "prompt_studio"
PROMPT_STUDIO_REGIONAL_ADAPTER_JS = (
    PROMPT_STUDIO_MODULES / "regional" / "editor_adapter.js"
)
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
PROMPT_STUDIO_REGIONAL_RUNTIME_SMOKE = (
    ROOT / "tests" / "frontend_regional_runtime_smoke.mjs"
)
STATIC_IMPORT_RE = re.compile(
    r"""from\s+["']((?:\.\.?/)+[^"']+\.js)["']"""
)


class FrontendModuleStructureTests(unittest.TestCase):
    def test_host_hook_registry_phase_2_is_owned_and_focused(self):
        registry_source = HOST_HOOK_REGISTRY_JS.read_text(encoding="utf-8")
        node_hooks_source = (
            PROMPT_STUDIO_MODULES / "node_hooks.js"
        ).read_text(encoding="utf-8")
        extension_runtime_source = (
            PROMPT_STUDIO_MODULES / "extension_runtime.js"
        ).read_text(encoding="utf-8")
        regional_extension_source = (
            PROMPT_STUDIO_REGIONAL_MODULES / "extension.js"
        ).read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))

        self.assertTrue(HOST_HOOK_REGISTRY_SMOKE.is_file())
        self.assertIn("web/js/lifecycle/**/*.js", config["include"])
        self.assertIn(
            r'node "tests\frontend_host_hook_registry_smoke.mjs"',
            frontend_check_source,
        )
        self.assertIn("export function registerHostHookCallbacks", registry_source)
        self.assertIn("export function createHostHookRuntimeLifecycle", registry_source)
        self.assertIn("segments: new Set()", registry_source)
        self.assertIn("current === record.topState.wrapper", registry_source)
        self.assertIn("target[methodName] = state.wrapper", registry_source)
        self.assertIn('../lifecycle/host_hook_registry.js"', node_hooks_source)
        self.assertIn('../../lifecycle/host_hook_registry.js"', regional_extension_source)
        self.assertIn('../lifecycle/host_hook_registry.js"', extension_runtime_source)

        for source, owner, lease, disposer in (
            (
                extension_runtime_source,
                "PROMPT_STUDIO_GLOBAL_HOOK_RUNTIME_OWNER",
                '"advanced-save-sync"',
                "dispose: disposeRuntime",
            ),
            (
                regional_extension_source,
                "REGIONAL_GLOBAL_HOOK_RUNTIME_OWNER",
                '"regional-save-sync"',
                "dispose: disposeGlobalHooks",
            ),
        ):
            self.assertIn("createHostHookRuntimeLifecycle(", source)
            self.assertIn(owner, source)
            self.assertIn(lease, source)
            self.assertIn(disposer, source)

        for source in (node_hooks_source, regional_extension_source):
            self.assertIn("registerHostHookCallbacks({", source)
        self.assertNotIn("__easyuseAnimaAdvancedWrapped", node_hooks_source)
        self.assertNotIn("serialize.__easyuseAnimaRegionalWrapped", regional_extension_source)

        aio_extension_source = AIO_EXTENSION_RUNTIME_JS.read_text(encoding="utf-8")
        lora_save_sync_source = (
            WEB_JS / "lora_preset" / "save_sync.js"
        ).read_text(encoding="utf-8")
        self.assertNotIn("host_hook_registry.js", aio_extension_source)
        self.assertIn('../lifecycle/host_hook_registry.js"', lora_save_sync_source)
        self.assertNotIn("createHostHookRuntimeLifecycle(", aio_extension_source)
        self.assertIn("createHostHookRuntimeLifecycle(", lora_save_sync_source)
        self.assertIn("registerHostHookCallbacks({", lora_save_sync_source)

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
            "prompt_studio/regional/editor_adapter.js": '../../easyuse_anima_api.js"',
            "easyuse_anima_settings.js": './easyuse_anima_api.js"',
            "prompt_studio/highlight.js": '../easyuse_anima_api.js"',
        }

        for filename, import_path in expected_imports.items():
            with self.subTest(filename=filename):
                source = (WEB_JS / filename).read_text(encoding="utf-8")
                self.assertIn(import_path, source)

    def test_aio_profile_core_module_owns_dom_free_resolution_rules(self):
        source = AIO_PRESETS_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        for helper in ("aioFindUserProfileByName", "aioResolvedProfileValue"):
            with self.subTest(helper=helper):
                self.assertIn(f"export function {helper}(", source)
                self.assertIn(helper, entry_source)

        self.assertNotRegex(source, r"\b(?:document|window|app)\b")
        self.assertNotIn("fetch(", source)
        self.assertTrue(AIO_PROFILE_CORE_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_profile_core_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_profile_api_client_has_closed_transport_boundary(self):
        source = AIO_PROFILE_API_CLIENT_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source),
            ["createAioProfileApiClient"],
        )
        self.assertLessEqual(len(source.splitlines()), 80)
        self.assertNotRegex(source, re.compile(r"^\s*import\s", re.MULTILINE))
        self.assertNotRegex(source, r"\b(?:document|window|app|api)\b")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)

        self.assertIn(
            'import { createAioProfileApiClient } from "./aio/profile_api_client.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+generatorProfileApi\s*=\s*createAioProfileApiClient"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        self.assertIn(
            "fetchJson: (url, options) => easyuseAnimaFetchComfyJson(api, url, options)",
            factory_match.group("dependencies"),
        )
        self.assertIn("encodeURIComponent", factory_match.group("dependencies"))

        for path in (
            "/easyuse_anima/aio_profiles",
            "/easyuse_anima/aio_profiles/save",
            "/easyuse_anima/aio_profiles/load",
            "/easyuse_anima/aio_profiles/rename",
            "/easyuse_anima/aio_profiles/delete",
        ):
            with self.subTest(path=path):
                self.assertIn(path, source)
                self.assertNotIn(path, entry_source)

        self.assertTrue(AIO_PROFILE_API_CLIENT_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_profile_api_client_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_profile_settings_runtime_has_closed_controller_boundary(self):
        source = AIO_PROFILE_SETTINGS_RUNTIME_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        extension_source = AIO_EXTENSION_RUNTIME_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source),
            ["aioCreateProfileSettingsRuntime"],
        )
        self.assertLessEqual(len(source.splitlines()), 480)
        self.assertNotRegex(source, re.compile(r"^\s*import\s", re.MULTILINE))
        self.assertNotRegex(source, r"\b(?:window|app|api)\b")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertNotRegex(
            source,
            re.compile(r"^(?:globalThis)\.[A-Za-z_$]", re.MULTILINE),
        )

        self.assertIn(
            'import { aioCreateProfileSettingsRuntime } from '
            '"./aio/profile_settings_runtime.js";',
            entry_source,
        )
        self.assertIn(
            'import { aioCreateProfileDialogs } from "./aio/profile_dialogs.js";',
            entry_source,
        )
        self.assertNotRegex(entry_source, r"window\.(?:prompt|confirm|alert)\(")
        self.assertIn(
            "const generatorProfileDialogs = aioCreateProfileDialogs({",
            entry_source,
        )
        self.assertIn(
            "document,\n  createDialog,\n  text: aioText,",
            entry_source,
        )
        self.assertIn(
            "const generatorProfileRuntime = aioCreateProfileSettingsRuntime({",
            entry_source,
        )
        factory_match = re.search(
            r"const\s+generatorProfileRuntime\s*=\s*"
            r"aioCreateProfileSettingsRuntime\(\{(?P<dependencies>.*?)\n\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        runtime_dependencies = factory_match.group("dependencies")
        for dependency in (
            "document,",
            "createDialog,",
            "field,",
            "text: aioText,",
            "format: aioFormat,",
            "profileApi: generatorProfileApi,",
        ):
            with self.subTest(dependency=dependency):
                self.assertRegex(
                    runtime_dependencies,
                    rf"(?m)^  {re.escape(dependency)}$",
                )

        nested_dependencies = {
            "profileCore": [
                "customValue: GENERATOR_PROFILE_CUSTOM_VALUE,",
                "builtinIds: aioBuiltinProfileIds,",
                "builtinSettings: aioBuiltinProfileSettings,",
                "fingerprint: aioProfileSettingsFingerprint,",
                "userValue: aioUserProfileValue,",
                "userName: aioUserProfileName,",
                "findUser: aioFindUserProfileByName,",
                "resolveValue: aioResolvedProfileValue,",
            ],
            "settingsCore": [
                "defaultSettings: DEFAULT_GENERATION_SETTINGS,",
                "mergeDefaults,",
                "migratePostprocess: migrateGeneratorPostprocessSettings,",
            ],
            "nodeAdapter": [
                "getSettings: generatorSettings,",
                "applyVisibleSettings: applyVisibleGeneratorSettings,",
                "writeSettings: writeGeneratorSettingsFromState,",
                "renderPanel: renderGeneratorPanel,",
                "refreshPanels: refreshGeneratorPanels,",
                "markDirty: markNodeDirty,",
            ],
        }
        for group_name, expected_lines in nested_dependencies.items():
            with self.subTest(dependency_group=group_name):
                group_match = re.search(
                    rf"(?ms)^  {group_name}: \{{\n(?P<body>.*?)^  \}},$",
                    runtime_dependencies,
                )
                self.assertIsNotNone(group_match)
                self.assertEqual(
                    [line.strip() for line in group_match.group("body").splitlines()],
                    expected_lines,
                )

        self.assertRegex(runtime_dependencies, r"(?m)^  dialogs: generatorProfileDialogs,$")

        self.assertIn(
            "loadProfiles: loadGeneratorUserProfiles,",
            entry_source,
        )
        self.assertIn("syncValue: syncGeneratorProfileValue,", entry_source)
        self.assertIn("displayLabel: generatorProfileDisplayLabel,", entry_source)
        self.assertIn("open: openGeneratorProfileSettings,", entry_source)

        for local_function in (
            "generatorProfileErrorMessage",
            "generatorUserProfileByName",
            "loadGeneratorUserProfiles",
            "postGeneratorProfile",
            "loadGeneratorUserProfile",
            "applyGeneratorProfileSettings",
            "applyGeneratorProfile",
            "saveGeneratorUserProfile",
            "renameGeneratorUserProfile",
            "deleteGeneratorUserProfile",
            "resolvedGeneratorProfileValue",
            "syncGeneratorProfileValue",
            "generatorProfileDisplayLabel",
            "openGeneratorProfileSettings",
        ):
            with self.subTest(local_function=local_function):
                self.assertNotRegex(
                    entry_source,
                    rf"\bfunction\s+{local_function}\(",
                )

        setup_start = extension_source.index("    async setup() {")
        setup_end = extension_source.index(
            "\n    async beforeRegisterNodeDef", setup_start
        )
        setup_body = extension_source[setup_start:setup_end]
        self.assertEqual(setup_body.count("loadSamplerOptions()"), 1)
        self.assertEqual(setup_body.count("loadUserProfiles()"), 1)
        self.assertEqual(setup_body.count(".then(refreshPanels)"), 2)
        self.assertIn("loadSamplerOptions: loadGeneratorSamplerOptions,", entry_source)
        self.assertIn("loadUserProfiles: loadGeneratorUserProfiles,", entry_source)
        self.assertIn("refreshPanels: refreshGeneratorPanels,", entry_source)
        self.assertNotIn("__easyuseAnimaGeneratorProfileValue", source[source.index("return {"):])

        self.assertTrue(AIO_PROFILE_SETTINGS_RUNTIME_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_profile_settings_runtime_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_profile_dialogs_use_nested_aio_dialogs(self):
        source = AIO_PROFILE_DIALOGS_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source),
            ["aioCreateProfileDialogs"],
        )
        self.assertNotRegex(source, r"window\.(?:prompt|confirm|alert)\(")
        self.assertNotIn("extensionManager", source)
        self.assertIn("const { document, createDialog, text } = dependencies", source)
        self.assertIn('input.type = "text"', source)
        self.assertIn('event.key === "Enter"', source)
        self.assertIn('event.key === "Escape"', source)
        self.assertIn("modal.close()", source)
        self.assertIn("title = text(\"dialog.profile.title\")", source)
        self.assertTrue(AIO_PROFILE_DIALOGS_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_profile_dialogs_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_extension_runtime_owns_registration_lifecycle(self):
        source = AIO_EXTENSION_RUNTIME_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(STATIC_IMPORT_RE.findall(source), [])
        self.assertNotIn("app.registerExtension", source)
        self.assertEqual(
            re.findall(
                r"^export function ([A-Za-z0-9_]+)\(", source, re.MULTILINE
            ),
            ["aioListAttachedGeneratorNodes", "aioCreateExtensionRuntime"],
        )
        self.assertIn(
            'const EXTENSION_SETUP_HOST_MARKER = '
            '"__easyuseAnimaAioExtensionSetupInstalled";',
            source,
        )
        self.assertIn("function extensionSetupState(api)", source)
        self.assertIn("completedSteps: new Set(),", source)
        self.assertIn("function runExtensionSetupStep(state, step, install)", source)
        self.assertIn("setupState.complete = true;", source)
        self.assertIn("const originalDescriptors = new Map(", source)
        self.assertIn("Object.defineProperty(nodeType.prototype, prototypeHookMarker", source)
        self.assertIn("throw error;", source)
        self.assertIn(
            "import {\n"
            "  aioCreateExtensionRuntime,\n"
            "  aioListAttachedGeneratorNodes,\n"
            '} from "./aio/extension_runtime.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+aioExtensionRuntime\s*=\s*"
            r"aioCreateExtensionRuntime\(\{(?P<dependencies>.*?)\n\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        dependencies = factory_match.group("dependencies")
        for expected_wiring in (
            "api,",
            "inputNodeType: INPUT_NODE_TYPE,",
            "generatorNodeType: GENERATOR_NODE_TYPE,",
            "generatorPreviewEvent: GENERATOR_PREVIEW_EVENT,",
            "installWheelForwarder: installGeneratorWheelForwarder,",
            "watchLocale: easyuseAnimaWatchLocale,",
            "refreshPanels: refreshGeneratorPanels,",
            "handlePreviewEvent: handleGeneratorPreviewEvent,",
            "handleProgressEvent: handleGeneratorProgressEvent,",
            "handleProgressStateEvent: handleGeneratorProgressStateEvent,",
            "handleDenoisePreviewEvent: handleGeneratorDenoisePreviewEvent,",
            "handleExecutingEvent: handleGeneratorExecutingEvent,",
            "clearDenoisePreviews: clearGeneratorDenoisePreviews,",
            "loadSamplerOptions: loadGeneratorSamplerOptions,",
            "loadUserProfiles: loadGeneratorUserProfiles,",
            "suppressDefaultPreview: suppressGeneratorDefaultPreview,",
            "hookInputNode,",
            "hookGeneratorNode,",
            "syncSerializedWidgets: syncGeneratorSerializedWidgets,",
            "scheduleDefaultPreviewSuppression: scheduleGeneratorDefaultPreviewSuppression,",
            "updateExecutedStatus: updateGeneratorExecutedStatus,",
            "scheduleLayout: scheduleGeneratorLayout,",
            "disposePanel: disposeGeneratorPanel,",
            "disposeNativePreviewLifecycle: disposeGeneratorNativePreviewLifecycle,",
        ):
            with self.subTest(factory_wiring=expected_wiring):
                self.assertIn(expected_wiring, dependencies)

        for entry_forbidden_lifecycle in (
            "async setup()",
            "beforeRegisterNodeDef",
            "api.addEventListener",
            "nodeType.prototype",
        ):
            with self.subTest(entry_forbidden_lifecycle=entry_forbidden_lifecycle):
                self.assertNotIn(entry_forbidden_lifecycle, entry_source)
        self.assertEqual(entry_source.count("app.registerExtension("), 1)
        self.assertRegex(
            entry_source,
            re.compile(
                r'app\.registerExtension\(\{\s*'
                r'name:\s*"easyuse-anima\.aio",\s*'
                r'\.\.\.aioExtensionRuntime,\s*'
                r'\}\);\s*$',
                re.DOTALL,
            ),
        )
        self.assertTrue(AIO_EXTENSION_RUNTIME_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_extension_runtime_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_generator_panel_runtime_has_closed_view_boundary(self):
        source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source),
            ["aioCreateGeneratorPanelRuntime"],
        )
        self.assertNotRegex(source, re.compile(r"^\s*import\s", re.MULTILINE))
        self.assertNotRegex(source, r"\b(?:app|api)\b")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertNotRegex(
            source,
            re.compile(r"^(?:window|globalThis)\.[A-Za-z_$]", re.MULTILINE),
        )

        self.assertIn(
            'import { aioCreateGeneratorPanelRuntime } from '
            '"./aio/generator_panel_runtime.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+generatorPanelRuntime\s*=\s*"
            r"aioCreateGeneratorPanelRuntime\(\{(?P<dependencies>.*?)\n\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        runtime_dependencies = factory_match.group("dependencies")
        for dependency in (
            "document,",
            "window,",
            "requestAnimationFrame: (callback) => requestAnimationFrame(callback),",
            "panelMinHeight: GENERATOR_PANEL_MIN_HEIGHT,",
        ):
            with self.subTest(top_level_dependency=dependency):
                self.assertRegex(
                    runtime_dependencies,
                    rf"(?m)^  {re.escape(dependency)}$",
                )

        nested_dependencies = {
            "controls": [
                "numberInput,",
                "checkbox,",
                "textareaInput,",
                "selectInput,",
                "createNodeField,",
            ],
            "text": [
                "get: aioText,",
                "format: aioFormat,",
                "applyTooltip,",
            ],
            "settingsCore": [
                "defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,",
                "specialSeedRandom: GENERATOR_SPECIAL_SEED_RANDOM,",
                "fallbackSamplerNames: GENERATOR_FALLBACK_SAMPLER_NAMES,",
                "fallbackSchedulerNames: GENERATOR_FALLBACK_SCHEDULER_NAMES,",
                "mergeDefaults,",
                "normalizeSeedControl,",
                "normalizeSeedValue,",
                "clampNumber: clampGeneratorNumber,",
                "normalizeUsduAutoTileRange: normalizeGeneratorUsduAutoTileRange,",
                "setUsduAutoTileTarget: setGeneratorUsduAutoTileTarget,",
                "normalizeDetailerOrder,",
                "detailerTargetDefaults,",
                "detailerTargetTitle,",
            ],
            "nodeAdapter": [
                "getSettings: generatorSettings,",
                "applyVisibleSettings: applyVisibleGeneratorSettings,",
                "writeSettings: writeGeneratorSettingsFromState,",
                "syncSettingsFromVisible: syncGeneratorSettingsFromVisible,",
                "widgetValue,",
                "widgetOptions,",
                "setWidgetValueIfChanged,",
                "commitSeedValue: commitGeneratorSeedValue,",
                "markDirty: markNodeDirty,",
                "ensureStyle,",
                "suppressDefaultPreview: suppressGeneratorDefaultPreview,",
                "markNativePreviewHidden: markGeneratorNativeLivePreviewHidden,",
                "imageUrl: generatorImageUrl,",
                "randomSeed,",
                "forwardPanelWheel: forwardGeneratorPanelWheel,",
            ],
            "profileAdapter": [
                "syncValue: syncGeneratorProfileValue,",
                "displayLabel: generatorProfileDisplayLabel,",
            ],
            "previewAdapter": [
                "mainImage: aioMainPreviewImage,",
                "selectedIndex: aioSelectedPreviewIndex,",
                "imageLabel: aioPreviewImageLabel,",
                "imageName: aioPreviewImageName,",
                "imageResolution: aioPreviewResolution,",
                "imageFileSize: aioPreviewFileSize,",
            ],
            "actions": [
                "openProfileSettings: openGeneratorProfileSettings,",
                "openSaveSettings,",
                "openSamplerSettings,",
                "openAdvancedSettings,",
                "openHighresSettings,",
                "openDetailerSettings,",
                "openUpscaleSettings,",
                "openPostprocessSettings,",
                "openPreviewSettings,",
            ],
        }
        for group_name, expected_lines in nested_dependencies.items():
            with self.subTest(dependency_group=group_name):
                group_match = re.search(
                    rf"(?ms)^  {group_name}: \{{\n(?P<body>.*?)^  \}},$",
                    runtime_dependencies,
                )
                self.assertIsNotNone(group_match)
                self.assertEqual(
                    [line.strip() for line in group_match.group("body").splitlines()],
                    expected_lines,
                )

        wrappers = {
            "activateGeneratorPanel": ("node", "activatePanel", "node"),
            "disposeGeneratorPanel": ("node", "disposePanel", "node"),
            "renderGeneratorPanel": (
                "node, expectedLifecycle = null",
                "renderPanel",
                "node, expectedLifecycle",
            ),
            "ensureGeneratorPanel": ("node", "ensurePanel", "node"),
            "updateGeneratorDomSummary": ("node", "updateSummary", "node"),
            "scheduleGeneratorLayout": ("node", "scheduleLayout", "node"),
            "scheduleGeneratorSummary": ("node", "scheduleSummary", "node"),
            "refreshGeneratorSeedButtons": ("node", "refreshSeedButtons", "node"),
        }
        for wrapper, (parameters, method, arguments) in wrappers.items():
            with self.subTest(public_wrapper=wrapper):
                self.assertRegex(
                    entry_source,
                    rf"function {wrapper}\({re.escape(parameters)}\) \{{\n"
                    rf"  return generatorPanelRuntime\.{method}"
                    rf"\({re.escape(arguments)}\);\n\}}",
                )

        for moved_function in (
            "generatorDenoisePreviewLabel",
            "stopGeneratorControlPropagation",
            "samplerModeLabel",
            "generatorPanelWidth",
            "applyGeneratorLayout",
            "updateGeneratorSettings",
            "renderGeneratorPreviewFeed",
            "updateGeneratorDomPreview",
            "createDomNumberControl",
            "createDomSliderNumberControl",
            "createDomSettingsSliderNumberControl",
            "createDomSettingsCheckboxControl",
            "createDomSettingsNumberControl",
            "createDomSettingsSelectControl",
            "createDomSettingsTextareaControl",
            "createDomSelectControl",
            "updateGeneratorSeed",
            "setGeneratorSeedFromUi",
        ):
            with self.subTest(moved_function=moved_function):
                self.assertNotRegex(
                    entry_source,
                    rf"\bfunction\s+{moved_function}\(",
                )
                self.assertRegex(source, rf"\bfunction\s+{moved_function}\(")

        for removed_function in (
            "createDomTextControl",
            "createDomCheckboxControl",
            "createDomSettingsTextControl",
            "createSeedControlSelect",
        ):
            with self.subTest(removed_dead_function=removed_function):
                self.assertNotIn(removed_function, entry_source)
                self.assertNotIn(removed_function, source)

        for entry_owned_function in (
            "commitGeneratorSeedValue",
            "syncGeneratorSerializedWidgets",
            "installGeneratorWheelForwarder",
            "hookGeneratorNode",
        ):
            with self.subTest(entry_owned_function=entry_owned_function):
                self.assertRegex(
                    entry_source,
                    rf"\bfunction\s+{entry_owned_function}\(",
                )
                self.assertNotRegex(
                    source,
                    rf"\bfunction\s+{entry_owned_function}\(",
                )

        seed_commit_start = entry_source.index("function commitGeneratorSeedValue")
        seed_commit_end = entry_source.index(
            "\nfunction syncGeneratorSerializedWidgets",
            seed_commit_start,
        )
        seed_commit_body = entry_source[seed_commit_start:seed_commit_end]
        self.assertLess(
            seed_commit_body.index("seedWidget.value = seed;"),
            seed_commit_body.index("seedWidget?.callback?.(seed);"),
        )
        self.assertLess(
            seed_commit_body.index("settingsWidget.value = serializedSettings;"),
            seed_commit_body.index("settingsWidget?.callback?.(serializedSettings);"),
        )
        self.assertEqual(seed_commit_body.count("} catch {"), 2)
        self.assertNotIn("previousSeedWidgetValue", seed_commit_body)
        self.assertNotIn("previousSettingsWidgetValue", seed_commit_body)

        self.assertLess(
            entry_source.index("const openPreviewSettings"),
            entry_source.index("const generatorPanelRuntime"),
        )
        self.assertLess(
            entry_source.index("const generatorPanelRuntime"),
            entry_source.index("function hookInputNode"),
        )
        self.assertIn(
            "nextSettings.detailer[targetName].wildcard = value;",
            source,
        )
        self.assertTrue(AIO_GENERATOR_PANEL_RUNTIME_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_generator_panel_runtime_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_executed_seed_runtime_uses_shared_correlation_owners(self):
        source = AIO_EXECUTED_SEED_RUNTIME_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source),
            ["createAioSeedTransaction"],
        )
        self.assertEqual(STATIC_IMPORT_RE.findall(source), [])
        self.assertNotRegex(source, r"\b(?:document|window|app)\b")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertIn(
            'import { createAioSeedTransaction } from '
            '"./aio/executed_seed_runtime.js";',
            entry_source,
        )
        self.assertIn(
            "aioSeedTransaction = createAioSeedTransaction({",
            entry_source,
        )
        self.assertIn(
            "void aioSeedTransaction.consumeExecution(node, message);",
            entry_source,
        )
        self.assertIn(
            'const AIO_SEED_SELECTION_SURFACE = "aio.seed_selection";',
            source,
        )
        for shared_contract_call in (
            "owner.captureProvisional({",
            "owner.acceptPrompt(entry.transaction, promptId)",
            "owner.markEdited(node, [AIO_SEED_SELECTION_SURFACE])",
            "owner.canCommit(transaction, {",
            "owner.settle(transaction, pending.envelope)",
            "executedContext.consumeWithinTurn(output)",
        ):
            with self.subTest(shared_contract_call=shared_contract_call):
                self.assertIn(shared_contract_call, source)
        for shared_import in (
            '"./lifecycle/queue_ui_transaction.js";',
            '"./lifecycle/executed_event_context.js";',
            '"./lifecycle/host_hook_registry.js";',
        ):
            with self.subTest(shared_import=shared_import):
                self.assertIn(shared_import, entry_source)
        for retired_symbol in (
            "generatorQueueRuntime",
            "aioCreateGeneratorQueueRuntime",
            "aioInstallGeneratorQueuePromptHook",
            "installGeneratorQueuePromptHook",
            "__easyuseAnimaLastQueuedSeed",
        ):
            self.assertNotIn(retired_symbol, entry_source)
        self.assertFalse((AIO_MODULES / "generator_queue_runtime.js").exists())
        self.assertTrue(AIO_EXECUTED_SEED_RUNTIME_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_executed_seed_runtime_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_native_preview_runtime_owns_dom_store_scheduler_and_event_lifecycle(self):
        source = AIO_NATIVE_PREVIEW_RUNTIME_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        extension_source = AIO_EXTENSION_RUNTIME_JS.read_text(encoding="utf-8")
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        preview_source = AIO_PREVIEW_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("// @ts-check\n"))
        self.assertEqual(STATIC_IMPORT_RE.findall(source), [])
        self.assertNotRegex(source, re.compile(r"^\s*import\s", re.MULTILINE))
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertNotIn("api.addEventListener", source)
        self.assertNotIn("nodeType.prototype", source)
        self.assertEqual(
            re.findall(r"^export function ([A-Za-z0-9_]+)\(", source, re.MULTILINE),
            ["aioCreateNativePreviewRuntime"],
        )
        self.assertEqual(len(re.findall(r"(?m)^export\s+", source)), 1)
        self.assertIn(
            'import { aioCreateNativePreviewRuntime } from '
            '"./aio/native_preview_runtime.js";',
            entry_source,
        )

        moved_functions = {
            "activateGeneratorNativePreviewLifecycle",
            "cssEscape",
            "disposeGeneratorNativePreviewLifecycle",
            "generatorVueNodeRoots",
            "generatorNativePreviewRootMatchesNode",
            "addGeneratorPreviewLocatorCandidate",
            "generatorPreviewLocatorCandidates",
            "hideGeneratorNativeLivePreviewElement",
            "isGeneratorNativeDimensionLabel",
            "hideGeneratorComfyOutputPreviewElements",
            "hideGeneratorNativeLivePreviewElements",
            "markGeneratorNativeLivePreviewHidden",
            "generatorDialogServiceAssetUrl",
            "generatorNativePreviewStores",
            "purgeGeneratorNativeLivePreviewStore",
            "scheduleGeneratorNativeLivePreviewPurge",
            "stopGeneratorNativeLivePreviewObserver",
            "ensureGeneratorNativeLivePreviewObserver",
            "scheduleGeneratorNativeLivePreviewHidden",
            "suppressGeneratorDefaultPreview",
            "scheduleGeneratorDefaultPreviewSuppression",
            "findGeneratorNodeByQualifiedId",
            "handleGeneratorPreviewEvent",
            "findGeneratorNodeForDenoisePreview",
            "handleGeneratorProgressEvent",
            "handleGeneratorProgressStateEvent",
            "handleGeneratorDenoisePreviewEvent",
            "handleGeneratorExecutingEvent",
            "clearGeneratorDenoisePreviews",
        }
        for moved_function in sorted(moved_functions):
            with self.subTest(moved_function=moved_function):
                self.assertRegex(source, rf"\bfunction\s+{moved_function}\(")
                self.assertNotRegex(
                    entry_source,
                    rf"\bfunction\s+{moved_function}\(",
                )

        for moved_state in (
            "generatorNativePreviewStoresPromise",
            "generatorDialogServiceAssetUrlPromise",
        ):
            with self.subTest(moved_state=moved_state):
                self.assertRegex(source, rf"\blet\s+{moved_state}\s*=")
                self.assertNotRegex(entry_source, rf"\blet\s+{moved_state}\s*=")

        expected_facades = {
            "activateGeneratorNativePreviewLifecycle",
            "disposeGeneratorNativePreviewLifecycle",
            "markGeneratorNativeLivePreviewHidden",
            "suppressGeneratorDefaultPreview",
            "scheduleGeneratorDefaultPreviewSuppression",
            "handleGeneratorPreviewEvent",
            "handleGeneratorProgressEvent",
            "handleGeneratorProgressStateEvent",
            "handleGeneratorDenoisePreviewEvent",
            "handleGeneratorExecutingEvent",
            "clearGeneratorDenoisePreviews",
        }
        return_match = re.search(
            r"(?ms)^  return \{(?P<facades>[A-Za-z0-9_,\s]+)\};\s*\}\s*$",
            source,
        )
        self.assertIsNotNone(return_match)
        self.assertEqual(
            set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", return_match.group("facades"))),
            expected_facades,
        )

        composition_match = re.search(
            r"const\s+\{(?P<facades>[A-Za-z0-9_,\s]+?)\}\s*=\s*"
            r"aioCreateNativePreviewRuntime\(\{(?P<dependencies>.*?)\n\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(composition_match)
        self.assertEqual(
            set(
                re.findall(
                    r"\b[A-Za-z_][A-Za-z0-9_]*\b",
                    composition_match.group("facades"),
                )
            ),
            expected_facades,
        )

        dependencies = composition_match.group("dependencies")
        expected_dependency_groups = {
            "environment": {
                "document",
                "window",
                "MutationObserver",
                "requestAnimationFrame",
                "cancelAnimationFrame",
                "setTimeout",
                "clearTimeout",
            },
            "constants": {
                "generatorNodeType",
                "generatorVueNodeClass",
            },
            "storeAdapter": {
                "getLegacyPreviewImages",
                "loadDirectStoreModules",
                "fetchFrontendHtml",
                "importAssetModule",
            },
            "previewCore": {
                "deleteStoreEntry",
                "eventDetail",
                "images",
                "nodeIdsFromDetail",
                "suppressDefaultPreview",
            },
            "nodeAdapter": {
                "getGraph",
                "listGeneratorNodes",
                "addPreviewImages",
                "clearDenoisePreview",
                "setDenoisePreview",
                "markDirty",
            },
            "progressAdapter": {
                "remember",
                "rememberState",
                "clear",
            },
        }
        actual_dependency_groups = set(
            re.findall(r"(?m)^  ([A-Za-z_][A-Za-z0-9_]*): \{$", dependencies)
        )
        self.assertEqual(actual_dependency_groups, set(expected_dependency_groups))
        for group_name, expected_keys in expected_dependency_groups.items():
            with self.subTest(dependency_group=group_name):
                group_match = re.search(
                    rf"(?ms)^  {group_name}: \{{\n(?P<body>.*?)^  \}},?$",
                    dependencies,
                )
                self.assertIsNotNone(group_match)
                actual_keys = set(
                    re.findall(
                        r"(?m)^    ([A-Za-z_][A-Za-z0-9_]*)(?:\s*:|,)",
                        group_match.group("body"),
                    )
                )
                self.assertEqual(actual_keys, expected_keys)

        expected_adapter_values = {
            "legacy preview store getter": (
                r"getLegacyPreviewImages\s*:\s*\(\s*\)\s*=>\s*"
                r"app\.nodePreviewImages"
            ),
            "entry-relative direct store imports": (
                r"loadDirectStoreModules\s*:\s*\(\s*\)\s*=>\s*"
                r"Promise\.all\(\s*\[\s*"
                r"// @ts-expect-error ComfyUI provides this host module at runtime\.\s*"
                r'import\(\s*"\.\./\.\./\.\./stores/nodeOutputStore\.js"\s*\)\s*'
                r"\.catch\(\s*\(\s*\)\s*=>\s*null\s*\)\s*,\s*"
                r"// @ts-expect-error ComfyUI provides this host module at runtime\.\s*"
                r'import\(\s*"\.\./\.\./\.\./platform/workflow/management/'
                r'stores/workflowStore\.js"\s*\)\s*'
                r"\.catch\(\s*\(\s*\)\s*=>\s*null\s*\)\s*,?\s*"
                r"\]\s*\)"
            ),
            "frontend HTML fetch": (
                r"fetchFrontendHtml\s*:\s*\(\s*\)\s*=>\s*"
                r'easyuseAnimaFetchText\(\s*"/"\s*\)'
            ),
            "lazy asset importer": (
                r"importAssetModule\s*:\s*\(\s*url\s*\)\s*=>\s*"
                r"import\(\s*url\s*\)"
            ),
            "live graph getter": (
                r"getGraph\s*:\s*\(\s*\)\s*=>\s*app\.graph"
            ),
            "animation frame canceler": (
                r"cancelAnimationFrame\s*:\s*\(\s*frame\s*\)\s*=>\s*"
                r"cancelAnimationFrame\(\s*frame\s*\)"
            ),
        }
        for adapter_name, pattern in expected_adapter_values.items():
            with self.subTest(composition_adapter_value=adapter_name):
                self.assertRegex(dependencies, re.compile(pattern, re.DOTALL))

        self.assertLess(
            entry_source.index("const openAdvancedSettings"),
            composition_match.start(),
        )
        self.assertLess(
            composition_match.end(),
            entry_source.index("const generatorPanelRuntime"),
        )
        self.assertLess(
            entry_source.index("const generatorPanelRuntime"),
            entry_source.index("function hookInputNode"),
        )
        self.assertIn(
            "suppressDefaultPreview: suppressGeneratorDefaultPreview,",
            entry_source,
        )
        self.assertIn(
            "markNativePreviewHidden: markGeneratorNativeLivePreviewHidden,",
            entry_source,
        )
        self.assertNotRegex(
            panel_source,
            r"\bfunction\s+(?:suppressGeneratorDefaultPreview|"
            r"markGeneratorNativeLivePreviewHidden)\(",
        )

        suppress_match = re.search(
            r"(?ms)^  function suppressGeneratorDefaultPreview\(node, options = \{\}\) \{"
            r"(?P<body>.*?)^  \}",
            source,
        )
        self.assertIsNotNone(suppress_match)
        suppress_body = suppress_match.group("body")
        self.assertIn("aioSuppressDefaultPreview(node, {", suppress_body)
        self.assertIn("markDirty: options.markDirty", suppress_body)
        self.assertIn("markNodeDirty,", suppress_body)
        self.assertNotIn('Object.defineProperty(node, "imgs"', suppress_body)
        self.assertIn(
            'Object.defineProperty(node, "imgs"',
            preview_source,
        )
        self.assertNotRegex(preview_source, r"\b(?:document|window|app)\b")

        for entry_owned_function in (
            "generatorGraphNodes",
            "clearGeneratorDenoisePreview",
            "setGeneratorDenoisePreview",
            "addGeneratorPreviewImagesToNode",
            "updateGeneratorExecutedStatus",
            "hookGeneratorNode",
        ):
            with self.subTest(entry_owned_function=entry_owned_function):
                self.assertRegex(
                    entry_source,
                    rf"\bfunction\s+{entry_owned_function}\(",
                )
                self.assertNotRegex(
                    source,
                    rf"\bfunction\s+{entry_owned_function}\(",
                )

        hook_start = entry_source.index("function hookGeneratorNode")
        hook_end = entry_source.index(
            "\nfunction addGeneratorPreviewImagesToNode", hook_start
        )
        hook_body = entry_source[hook_start:hook_end]
        self.assertIn("activateGeneratorNativePreviewLifecycle(node);", hook_body)
        self.assertLess(
            hook_body.index("activateGeneratorNativePreviewLifecycle(node);"),
            hook_body.index("suppressGeneratorDefaultPreview(node"),
        )

        for progress_facade in (
            "rememberGeneratorProgress",
            "rememberGeneratorProgressState",
            "generatorProgressForPreviewDetail",
            "clearGeneratorPreviewProgress",
        ):
            with self.subTest(entry_owned_progress_facade=progress_facade):
                self.assertIn(progress_facade, entry_source)
                self.assertNotRegex(
                    source,
                    rf"\b(?:const|let|function)\s+{progress_facade}\b",
                )

        self.assertIn("app.registerExtension({", entry_source)
        for listener_registration in (
            "api.addEventListener(GENERATOR_PREVIEW_EVENT, handlePreviewEvent);",
            'api.addEventListener("progress", handleProgressEvent);',
            'api.addEventListener("progress_state", handleProgressStateEvent);',
            'api.addEventListener("b_preview_with_metadata", '
            "handleDenoisePreviewEvent, true);",
            'api.addEventListener("executing", handleExecutingEvent);',
            'api.addEventListener("execution_error", clearDenoisePreviews);',
            'api.addEventListener("execution_interrupted", clearDenoisePreviews);',
            'api.addEventListener("execution_success", clearDenoisePreviews);',
        ):
            with self.subTest(runtime_owned_listener_registration=listener_registration):
                self.assertIn(listener_registration, extension_source)
        self.assertNotIn("api.addEventListener", entry_source)
        for prototype_hook in (
            "onNodeCreated",
            "onConfigure",
            "onSerialize",
            "onExecuted",
            "onResize",
            "onRemoved",
        ):
            with self.subTest(runtime_owned_prototype_hook=prototype_hook):
                self.assertIn(
                    f"nodeType.prototype.{prototype_hook}", extension_source
                )
                self.assertNotIn(f"nodeType.prototype.{prototype_hook}", entry_source)
                self.assertNotIn(f"nodeType.prototype.{prototype_hook}", source)

        self.assertTrue(AIO_NATIVE_PREVIEW_RUNTIME_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_native_preview_runtime_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_stage_settings_dialogs_have_closed_lifecycle_boundary(self):
        source = AIO_STAGE_SETTINGS_DIALOGS_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("// @ts-check\n"))
        self.assertEqual(STATIC_IMPORT_RE.findall(source), [])
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertEqual(
            re.findall(r"^export function ([A-Za-z0-9_]+)\(", source, re.MULTILINE),
            ["aioCreateStageSettingsDialogs"],
        )
        self.assertIn(
            'import { aioCreateStageSettingsDialogs } from "./aio/stage_settings_dialogs.js";',
            entry_source,
        )
        for moved_function in (
            "createStageOptimizationEditor",
            "openHighresSettings",
            "openUpscaleSettings",
        ):
            with self.subTest(moved_function=moved_function):
                self.assertRegex(source, rf"\bfunction\s+{moved_function}\(")
                self.assertNotRegex(entry_source, rf"\bfunction\s+{moved_function}\(")
        return_match = re.search(
            r"(?ms)^  return \{(?P<facades>[A-Za-z0-9_,\s]+)\};\s*\}\s*$",
            source,
        )
        self.assertIsNotNone(return_match)
        expected_facades = {
            "createStageOptimizationEditor",
            "openHighresSettings",
            "openUpscaleSettings",
        }
        self.assertEqual(
            set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", return_match.group("facades"))),
            expected_facades,
        )
        composition_match = re.search(
            r"(?ms)const\s*\{(?P<facades>[A-Za-z0-9_,\s]+?)\}\s*=\s*"
            r"aioCreateStageSettingsDialogs\(\{",
            entry_source,
        )
        self.assertIsNotNone(composition_match)
        self.assertEqual(
            set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", composition_match.group("facades"))),
            expected_facades,
        )
        composition_start = composition_match.start()
        composition_end = entry_source.index(
            "\n\nconst openDetailerSettings", composition_start
        )
        composition = entry_source[composition_start:composition_end]
        for expected in (
            "createStageOptimizationEditor,",
            "openHighresSettings,",
            "openUpscaleSettings,",
            "createDialog,",
            "defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,",
            "normalizeUsduAutoTileRange: normalizeGeneratorUsduAutoTileRange,",
            "getSettings: generatorSettings,",
            "renderPanel: renderGeneratorPanel,",
            "reconcileSelectInput,",
            "upscaleBackendMissingPacks,",
            "load: loadGeneratorOptionalDependencies,",
        ):
            with self.subTest(composition_dependency=expected):
                self.assertIn(expected, composition)
        self.assertLess(
            composition_match.start(),
            entry_source.index("const openDetailerSettings"),
        )
        self.assertTrue(AIO_STAGE_SETTINGS_DIALOGS_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_stage_settings_dialogs_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_detailer_settings_dialog_has_closed_lifecycle_boundary(self):
        source = AIO_DETAILER_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        stage_source = AIO_STAGE_SETTINGS_DIALOGS_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("// @ts-check\n"))
        self.assertEqual(STATIC_IMPORT_RE.findall(source), [])
        self.assertNotRegex(source, r"(?m)^\s*import\s")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertEqual(
            re.findall(r"^export function ([A-Za-z0-9_]+)\(", source, re.MULTILINE),
            ["aioCreateDetailerSettingsDialog"],
        )
        self.assertIn(
            'import { aioCreateDetailerSettingsDialog } from "./aio/detailer_settings_dialog.js";',
            entry_source,
        )
        for moved_function in ("createDetailerTargetEditor", "openDetailerSettings"):
            with self.subTest(moved_function=moved_function):
                self.assertRegex(source, rf"\bfunction\s+{moved_function}\(")
                self.assertNotRegex(entry_source, rf"\bfunction\s+{moved_function}\(")
                self.assertNotRegex(stage_source, rf"\bfunction\s+{moved_function}\(")

        composition_start = entry_source.index(
            "const openDetailerSettings = aioCreateDetailerSettingsDialog({"
        )
        composition_end = entry_source.index("\n\nconst openSamplerSettings", composition_start)
        composition = entry_source[composition_start:composition_end]
        for expected in (
            "createDialog,",
            "textareaInput,",
            "defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,",
            "normalizeDetailerOrder,",
            "stageOptimizationEditor: createStageOptimizationEditor,",
            "getSettings: generatorSettings,",
            "nodeInputChoiceOptions,",
            "reconcileSelectInput,",
            "renderPanel: renderGeneratorPanel,",
            "load: loadGeneratorOptionalDependencies,",
        ):
            with self.subTest(composition_dependency=expected):
                self.assertIn(expected, composition)
        stage_composition = entry_source.index("aioCreateStageSettingsDialogs({")
        sampler_composition = entry_source.index("const openSamplerSettings")
        self.assertLess(stage_composition, composition_start)
        self.assertLess(composition_start, sampler_composition)

        editor_start = source.index("function createDetailerTargetEditor")
        editor_end = source.index("\n  function openDetailerSettings", editor_start)
        editor_body = source[editor_start:editor_end]
        self.assertIn(
            "createStageOptimizationEditor(`${title} Optimization`, target, defaults)",
            editor_body,
        )
        for field_contract in (
            'guide_size_for: guideSizeFor.value === "bbox"',
            'wildcard: String(wildcard.value || "")',
            "inpaint_model: inpaintModel.checked",
            "tiled_encode: tiledEncode.checked",
            "tiled_decode: tiledDecode.checked",
        ):
            with self.subTest(detailer_field_contract=field_contract):
                self.assertIn(field_contract, editor_body)
        for destructive_default in (
            "guide_size_for: false",
            "inpaint_model: false",
            "tiled_encode: false",
            "tiled_decode: false",
        ):
            with self.subTest(destructive_default=destructive_default):
                self.assertNotIn(destructive_default, editor_body)
        self.assertIn("return openDetailerSettings;", source)
        self.assertTrue(AIO_DETAILER_SETTINGS_DIALOG_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_detailer_settings_dialog_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_sampler_settings_dialog_has_closed_lifecycle_boundary(self):
        source = AIO_SAMPLER_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("// @ts-check\n"))
        self.assertEqual(STATIC_IMPORT_RE.findall(source), [])
        self.assertNotRegex(source, r"(?m)^\s*import\s")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertEqual(
            re.findall(r"^export function ([A-Za-z0-9_]+)\(", source, re.MULTILINE),
            ["aioCreateSamplerSettingsDialog"],
        )
        self.assertEqual(len(re.findall(r"(?m)^export\s+", source)), 1)
        self.assertIn(
            'import { aioCreateSamplerSettingsDialog } from "./aio/sampler_settings_dialog.js";',
            entry_source,
        )
        for moved_function in (
            "applyNodeInputInfo",
            "createDynamicNodeInputEditor",
            "openSamplerSettings",
        ):
            with self.subTest(moved_function=moved_function):
                self.assertRegex(source, rf"\bfunction\s+{moved_function}\(")
                self.assertNotRegex(entry_source, rf"\bfunction\s+{moved_function}\(")
        for moved_constant in (
            "SPECTRUM_ADVANCED_KNOWN_INPUTS",
            "SPECTRUM_SPD_KNOWN_INPUTS",
        ):
            with self.subTest(moved_constant=moved_constant):
                self.assertRegex(source, rf"\bconst\s+{moved_constant}\s*=")
                self.assertNotRegex(entry_source, rf"\bconst\s+{moved_constant}\s*=")

        composition_start = entry_source.index(
            "const openSamplerSettings = aioCreateSamplerSettingsDialog({"
        )
        composition_end = entry_source.index("\n\nconst openSaveSettings", composition_start)
        composition = entry_source[composition_start:composition_end]
        for expected in (
            "createDialog,",
            "nodeInputControlForSpec,",
            "valueFromNodeInputControl,",
            "defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,",
            "seedControls: GENERATOR_SEED_CONTROLS,",
            "specialSeedRandom: GENERATOR_SPECIAL_SEED_RANDOM,",
            "mergeVisibleSettings: mergeVisibleGeneratorSettings,",
            "applyVisibleSettings: applyVisibleGeneratorSettings,",
            "writeSettings,",
            "renderPanel: renderGeneratorPanel,",
            "backendDependencies: AIO_BACKEND_DEPENDENCIES,",
            "isLoaded: () => generatorOptionalDependencyState.loaded,",
            "nodeInputMap,",
            "nodeInputTooltip,",
            "nodeInputSupported,",
            "load: loadGeneratorOptionalDependencies,",
        ):
            with self.subTest(composition_dependency=expected):
                self.assertIn(expected, composition)
        detailer_composition = entry_source.index("const openDetailerSettings")
        save_composition = entry_source.index("const openSaveSettings")
        self.assertLess(detailer_composition, composition_start)
        self.assertLess(composition_start, save_composition)
        self.assertIn("return openSamplerSettings;", source)
        self.assertTrue(AIO_SAMPLER_SETTINGS_DIALOG_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_sampler_settings_dialog_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_save_settings_dialog_has_closed_lifecycle_boundary(self):
        source = AIO_SAVE_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("// @ts-check\n"))
        self.assertEqual(STATIC_IMPORT_RE.findall(source), [])
        self.assertNotRegex(source, r"(?m)^\s*import\s")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertEqual(
            re.findall(r"^export function ([A-Za-z0-9_]+)\(", source, re.MULTILINE),
            ["aioCreateSaveSettingsDialog"],
        )
        self.assertEqual(len(re.findall(r"(?m)^export\s+", source)), 1)
        self.assertIn(
            'import { aioCreateSaveSettingsDialog } from "./aio/save_settings_dialog.js";',
            entry_source,
        )
        for moved_function in (
            "normalizeImageSaverHashBundles",
            "normalizeImageSaverCivitaiHashFetchers",
            "createImageSaverHashBundleEditor",
            "createImageSaverCivitaiHashFetcherEditor",
            "openSaveSettings",
        ):
            with self.subTest(moved_function=moved_function):
                self.assertRegex(source, rf"\bfunction\s+{moved_function}\(")
                self.assertNotRegex(entry_source, rf"\bfunction\s+{moved_function}\(")

        composition_start = entry_source.index(
            "const openSaveSettings = aioCreateSaveSettingsDialog({"
        )
        composition_end = entry_source.index(
            "const openAdvancedSettings = aioCreateAdvancedSettingsDialog({",
            composition_start,
        )
        composition = entry_source[composition_start:composition_end]
        for expected in (
            "createDialog,",
            "field,",
            "checkbox,",
            "selectInput,",
            "textInput,",
            "numberInput,",
            "textareaInput,",
            "staticText: aioStaticText,",
            "get: aioText,",
            "format: aioFormat,",
            "applyTooltip,",
            "applyTooltipText,",
            "defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,",
            "asBool,",
            "mergeDefaults,",
            "generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,",
            "findWidget,",
            "getSettings: generatorSettings,",
            "applyVisibleSettings: applyVisibleGeneratorSettings,",
            "writeSettings,",
            "renderPanel: renderGeneratorPanel,",
            "available: optionalDependencyAvailable,",
            "pack: optionalDependencyPack,",
            "load: loadGeneratorOptionalDependencies,",
        ):
            with self.subTest(composition_dependency=expected):
                self.assertIn(expected, composition)
        sampler_composition = entry_source.index("const openSamplerSettings")
        advanced_composition = entry_source.index("const openAdvancedSettings")
        self.assertLess(sampler_composition, composition_start)
        self.assertLess(composition_start, advanced_composition)
        self.assertIn("return openSaveSettings;", source)
        self.assertTrue(AIO_SAVE_SETTINGS_DIALOG_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_save_settings_dialog_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_torch_compile_recommendation_has_bounded_data_contract(self):
        source = AIO_TORCH_COMPILE_RECOMMENDATION_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("// @ts-check\n"))
        self.assertEqual(STATIC_IMPORT_RE.findall(source), [])
        self.assertNotRegex(source, r"(?m)^\s*import\s")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertNotRegex(
            source,
            re.compile(r"^(?:window|globalThis)\.[A-Za-z_$]", re.MULTILINE),
        )
        self.assertEqual(
            re.findall(r"^export function ([A-Za-z0-9_]+)\(", source, re.MULTILINE),
            [
                "aioTorchCompileRecommendationRequest",
                "aioNormalizeTorchCompileRecommendation",
                "aioTorchCompileRecommendationDiff",
                "createAioTorchCompileRecommendationClient",
            ],
        )
        self.assertIn(
            'from "./aio/torch_compile_recommendation.js";',
            entry_source,
        )
        self.assertIn(
            "const torchCompileRecommendationClient = "
            "createAioTorchCompileRecommendationClient({",
            entry_source,
        )
        self.assertIn(
            "fetchJson: (url, options) => easyuseAnimaFetchComfyJson(api, url, options),",
            entry_source,
        )
        self.assertTrue(AIO_TORCH_COMPILE_RECOMMENDATION_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_torch_compile_recommendation_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_advanced_settings_dialog_has_closed_lifecycle_boundary(self):
        source = AIO_ADVANCED_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("// @ts-check\n"))
        self.assertEqual(STATIC_IMPORT_RE.findall(source), [])
        self.assertNotRegex(source, r"(?m)^\s*import\s")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("app.registerExtension", source)
        self.assertEqual(
            re.findall(r"^export function ([A-Za-z0-9_]+)\(", source, re.MULTILINE),
            ["aioCreateAdvancedSettingsDialog"],
        )
        self.assertEqual(len(re.findall(r"(?m)^export\s+", source)), 1)
        self.assertIn(
            'import { aioCreateAdvancedSettingsDialog } from '
            '"./aio/advanced_settings_dialog.js";',
            entry_source,
        )
        self.assertRegex(source, r"\bfunction\s+openAdvancedSettings\(")
        self.assertNotRegex(entry_source, r"\bfunction\s+openAdvancedSettings\(")
        self.assertNotRegex(source, r"\bfunction\s+openGeneratorSettings\(")

        composition_start = entry_source.index(
            "const openAdvancedSettings = aioCreateAdvancedSettingsDialog({"
        )
        composition_end = entry_source.index(
            "const generatorPanelRuntime = aioCreateGeneratorPanelRuntime({",
            composition_start,
        )
        composition = entry_source[composition_start:composition_end]
        for expected in (
            "createDialog,",
            "field,",
            "checkbox,",
            "textInput,",
            "numberInput,",
            "selectInput,",
            "staticText: aioStaticText,",
            "get: aioText,",
            "format: aioFormat,",
            "defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS,",
            "mergeDefaults,",
            "clampNumber: clampGeneratorNumber,",
            "generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET,",
            "findWidget,",
            "getSettings: generatorSettings,",
            "writeSettings,",
            "renderPanel: renderGeneratorPanel,",
            "available: optionalDependencyAvailable,",
            "pack: optionalDependencyPack,",
            "load: loadGeneratorOptionalDependencies,",
            "recommend: (settings, context) =>",
            "torchCompileRecommendationClient.recommend(settings, context)",
            "diff: aioTorchCompileRecommendationDiff,",
        ):
            with self.subTest(composition_dependency=expected):
                self.assertIn(expected, composition)
        save_composition = entry_source.index("const openSaveSettings")
        generator_panel_composition = entry_source.index("const generatorPanelRuntime")
        self.assertLess(save_composition, composition_start)
        self.assertLess(composition_start, generator_panel_composition)
        self.assertIn("return openAdvancedSettings;", source)
        self.assertTrue(AIO_ADVANCED_SETTINGS_DIALOG_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_advanced_settings_dialog_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_dependency_core_module_owns_dom_free_capability_rules(self):
        source = AIO_DEPENDENCIES_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")

        expected_constants = {
            "AIO_BACKEND_DEPENDENCIES",
            "AIO_OPTIONAL_DEPENDENCY_SPECS",
        }
        exported_constants = set(
            re.findall(r"export const ([A-Za-z0-9_]+)\s*=", source)
        )
        self.assertEqual(exported_constants, expected_constants)

        expected_functions = {
            "aioChoiceOptionsWithCurrent",
            "aioChoiceSpecValues",
            "aioNodeInputMap",
            "aioNodeInputSpec",
            "aioNodeInputSupported",
            "aioNodeInputTooltip",
            "aioOptionalDependencyAvailable",
            "aioOptionalDependencyPack",
            "aioOptionalDependencyStatus",
            "aioQueryOptionalDependencies",
            "aioUpscaleBackendDependencyKeys",
            "aioUpscaleBackendMissingPacks",
        }
        exported_functions = set(
            re.findall(r"export (?:async )?function ([A-Za-z0-9_]+)\(", source)
        )
        self.assertEqual(exported_functions, expected_functions)

        import_match = re.search(
            r'import\s+\{(?P<names>[^}]*)\}\s+from\s+'
            r'"\./aio/dependencies\.js";',
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(import_match)
        imported_names = {
            name.strip()
            for name in import_match.group("names").split(",")
            if name.strip()
        }
        self.assertEqual(
            imported_names,
            {
                "AIO_BACKEND_DEPENDENCIES",
                "AIO_OPTIONAL_DEPENDENCY_SPECS",
                "aioChoiceOptionsWithCurrent",
                "aioChoiceSpecValues",
                "aioNodeInputMap",
                "aioNodeInputSpec",
                "aioNodeInputSupported",
                "aioNodeInputTooltip",
                "aioOptionalDependencyAvailable",
                "aioOptionalDependencyPack",
                "aioOptionalDependencyStatus",
                "aioQueryOptionalDependencies",
                "aioUpscaleBackendDependencyKeys",
                "aioUpscaleBackendMissingPacks",
            },
        )

        self.assertNotRegex(source, r"\b(?:document|window|app)\b")
        self.assertNotIn("app.registerExtension", source)
        self.assertNotIn("fetch(", source)
        self.assertNotIn("const GENERATOR_OPTIONAL_DEPENDENCY_SPECS", entry_source)
        self.assertNotIn("const GENERATOR_BACKEND_DEPENDENCIES", entry_source)
        self.assertNotIn("function choiceSpecValues", entry_source)
        self.assertNotIn("function optionsWithCurrent", entry_source)
        self.assertNotRegex(entry_source, r"\boptionsWithCurrent\s*\(")
        self.assertNotIn("function upscaleBackendDependencyKeys", entry_source)

        for delegation in (
            "aioOptionalDependencyStatus(generatorOptionalDependencyState, key)",
            "aioOptionalDependencyAvailable(generatorOptionalDependencyState, key)",
            "aioUpscaleBackendMissingPacks(generatorOptionalDependencyState, backend)",
            "aioNodeInputMap(generatorOptionalDependencyState, dependencyKey)",
            "aioNodeInputSpec(generatorOptionalDependencyState, dependencyKey, inputName)",
            "aioNodeInputTooltip(generatorOptionalDependencyState, dependencyKey, inputName)",
            "aioNodeInputSupported(generatorOptionalDependencyState, dependencyKey, inputName)",
        ):
            with self.subTest(delegation=delegation):
                self.assertIn(delegation, entry_source)

        self.assertTrue(AIO_DEPENDENCY_CORE_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_dependency_core_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_preview_core_module_owns_dom_free_preview_rules(self):
        source = AIO_PREVIEW_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")

        expected_functions = {
            "aioAppendPreviewFeed",
            "aioCreatePreviewProgressTracker",
            "aioDefaultPreviewIndex",
            "aioDeletePreviewStoreEntry",
            "aioMainPreviewImage",
            "aioMergePreviewImages",
            "aioPreviewEventDetail",
            "aioPreviewFileSize",
            "aioPreviewImageLabel",
            "aioPreviewImageName",
            "aioPreviewImages",
            "aioPreviewNodeIdsFromDetail",
            "aioPreviewResolution",
            "aioPreviewRunId",
            "aioRemovePreviewRun",
            "aioResolveTerminalPreviewState",
            "aioSelectedPreviewIndex",
            "aioSuppressDefaultPreview",
            "aioTagPreviewRun",
        }
        exported_functions = set(
            re.findall(r"export (?:async )?function ([A-Za-z0-9_]+)\(", source)
        )
        self.assertEqual(exported_functions, expected_functions)
        self.assertNotRegex(source, r"export const [A-Za-z0-9_]+\s*=")

        import_match = re.search(
            r'import\s+\{(?P<names>[^}]*)\}\s+from\s+'
            r'"\./aio/preview\.js";',
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(import_match)
        imported_names = {
            name.strip()
            for name in import_match.group("names").split(",")
            if name.strip()
        }
        self.assertEqual(imported_names, expected_functions)

        self.assertNotRegex(source, r"\b(?:document|window|app)\b")
        self.assertNotIn("app.registerExtension", source)
        self.assertNotIn("fetch(", source)
        self.assertNotIn("const GENERATOR_PROGRESS_BY_NODE", entry_source)
        self.assertIn("aioCreatePreviewProgressTracker();", entry_source)
        for local_function in (
            "appendGeneratorPreviewFeed",
            "deleteGeneratorPreviewStoreEntry",
            "generatorDefaultPreviewIndex",
            "generatorMainPreviewImage",
            "generatorNodeIdsFromDetail",
            "generatorPreviewEventDetail",
            "generatorPreviewFeedLimit",
            "generatorPreviewFileSize",
            "generatorPreviewIdentity",
            "generatorPreviewImageLabel",
            "generatorPreviewImageName",
            "generatorPreviewImages",
            "generatorPreviewResolution",
            "generatorPreviewRunId",
            "generatorSelectedPreviewIndex",
            "lockGeneratorLegacyCanvasPreview",
            "mergeGeneratorPreviewImages",
            "normalizeGeneratorNodeId",
            "removeGeneratorPreviewRun",
            "tagGeneratorPreviewRun",
        ):
            with self.subTest(local_function=local_function):
                self.assertNotIn(f"function {local_function}(", entry_source)

        self.assertTrue(AIO_PREVIEW_CORE_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_preview_core_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_settings_core_module_owns_dom_free_storage_rules(self):
        source = AIO_SETTINGS_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")

        expected_constants = {
            "AIO_DEFAULT_GENERATION_SETTINGS",
            "AIO_DEFAULT_INPUT_SETTINGS",
            "AIO_GENERATOR_MAX_SEED",
            "AIO_GENERATOR_SEED_CONTROLS",
            "AIO_GENERATOR_SPECIAL_SEED_DECREMENT",
            "AIO_GENERATOR_SPECIAL_SEED_INCREMENT",
            "AIO_GENERATOR_SPECIAL_SEED_RANDOM",
        }
        expected_internal_constants = {"AIO_GENERATION_STAGE_IDS"}
        exported_constants = set(
            re.findall(r"export const ([A-Za-z0-9_]+)\s*=", source)
        )
        self.assertEqual(
            exported_constants,
            expected_constants | expected_internal_constants,
        )

        expected_functions = {
            "aioAsBool",
            "aioCloneJson",
            "aioMergeDefaults",
            "aioMigrateGeneratorPostprocessSettings",
            "aioNormalizeGeneratorPreviewSettings",
            "aioNormalizeSeedControl",
            "aioNormalizeSeedValue",
            "aioParseSettingsValue",
            "aioSettingsToCompactJson",
        }
        expected_internal_functions = {"aioMigrateGenerationSettingsVersion"}
        exported_functions = set(
            re.findall(r"export (?:async )?function ([A-Za-z0-9_]+)\(", source)
        )
        self.assertEqual(
            exported_functions,
            expected_functions | expected_internal_functions,
        )

        import_match = re.search(
            r'import\s+\{(?P<names>[^}]*)\}\s+from\s+'
            r'"\./aio/settings\.js";',
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(import_match)
        imported_exports = {
            name.strip().split(" as ", 1)[0].strip()
            for name in import_match.group("names").split(",")
            if name.strip()
        }
        self.assertEqual(imported_exports, expected_constants | expected_functions)

        self.assertNotRegex(source, r"\b(?:document|window|app|api)\b")
        self.assertNotIn("app.registerExtension", source)
        self.assertNotIn("fetch(", source)
        for ui_dependency in (
            "findWidget",
            "widgetValue",
            "setWidgetValue",
            "setDirtyCanvas",
        ):
            with self.subTest(ui_dependency=ui_dependency):
                self.assertNotIn(ui_dependency, source)

        for local_constant in (
            "DEFAULT_GENERATION_SETTINGS",
            "DEFAULT_INPUT_SETTINGS",
            "GENERATOR_MAX_SEED",
            "GENERATOR_SEED_CONTROLS",
            "GENERATOR_SPECIAL_SEED_RANDOM",
            "GENERATOR_SPECIAL_SEED_INCREMENT",
            "GENERATOR_SPECIAL_SEED_DECREMENT",
        ):
            with self.subTest(local_constant=local_constant):
                self.assertNotRegex(
                    entry_source,
                    rf"const\s+{local_constant}\s*=",
                )

        for local_function in (
            "asBool",
            "clone",
            "mergeDefaults",
            "migrateGeneratorPostprocessSettings",
            "normalizeGeneratorPreviewSettings",
            "normalizeSeedControl",
            "normalizeSeedValue",
            "settingsToCompactJson",
        ):
            with self.subTest(local_function=local_function):
                self.assertNotIn(f"function {local_function}(", entry_source)

        self.assertNotIn("JSON.parse(widget.value ||", entry_source)
        self.assertTrue(AIO_SETTINGS_CORE_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_settings_core_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_dom_controls_core_module_owns_native_control_construction(self):
        source = AIO_DOM_CONTROLS_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")

        expected_functions = {
            "aioCreateCheckboxInput",
            "aioCreateNumberInput",
            "aioCreateSelectInput",
            "aioReconcileSelectInput",
            "aioCreateTextInput",
            "aioCreateTextareaInput",
            "aioNodeInputControlForSpec",
            "aioNodeInputDefault",
            "aioValueFromNodeInputControl",
        }
        exported_functions = set(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source)
        )
        self.assertEqual(exported_functions, expected_functions)
        self.assertNotRegex(source, r"export const [A-Za-z0-9_]+\s*=")

        import_match = re.search(
            r'import\s+\{(?P<names>[^}]*)\}\s+from\s+'
            r'"\./aio/dom_controls\.js";',
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(import_match)
        imported_exports = {
            name.strip().split(" as ", 1)[0].strip()
            for name in import_match.group("names").split(",")
            if name.strip()
        }
        self.assertEqual(
            imported_exports,
            expected_functions - {"aioNodeInputDefault"},
        )

        self.assertNotRegex(source, re.compile(r"^\s*import\s", re.MULTILINE))
        self.assertNotRegex(source, r"\b(?:app|api)\b")
        self.assertNotIn("app.registerExtension", source)
        self.assertNotIn("fetch(", source)
        self.assertNotRegex(
            source,
            re.compile(r"^(?:window|globalThis)\.[A-Za-z_$]", re.MULTILINE),
        )

        for local_function in (
            "checkbox",
            "nodeInputControlForSpec",
            "nodeInputDefault",
            "numberInput",
            "selectInput",
            "textInput",
            "textareaInput",
            "valueFromNodeInputControl",
        ):
            with self.subTest(local_function=local_function):
                self.assertNotRegex(
                    entry_source,
                    rf"\bfunction\s+{local_function}\(",
                )

        self.assertTrue(AIO_DOM_CONTROLS_CORE_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_dom_controls_core_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_dialog_primitives_module_owns_shared_dom_shells(self):
        source = AIO_DIALOG_PRIMITIVES_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source),
            ["aioCreateDialogPrimitives"],
        )
        self.assertNotRegex(source, re.compile(r"^\s*import\s", re.MULTILINE))
        self.assertNotRegex(source, r"\b(?:app|api)\b")
        self.assertNotIn("app.registerExtension", source)
        self.assertNotIn("fetch(", source)
        self.assertNotRegex(
            source,
            re.compile(r"^(?:window|globalThis)\.[A-Za-z_$]", re.MULTILINE),
        )

        self.assertIn(
            'import { aioCreateDialogPrimitives } from "./aio/dialog_primitives.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+\{\s*createDialog,\s*createNodeField,\s*field,\s*\}\s*="
            r"\s*aioCreateDialogPrimitives\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        for dependency in (
            "document",
            "ensureStyle",
            "staticText: aioStaticText",
            "text: aioText",
            "resolveFieldPresentation: aioFieldPresentation",
            "applyTooltip",
            "applyTooltipText",
        ):
            with self.subTest(dependency=dependency):
                self.assertIn(dependency, factory_match.group("dependencies"))

        presentation_start = entry_source.index("function aioFieldPresentation")
        presentation_end = entry_source.index(
            "\nfunction applyTooltip", presentation_start
        )
        presentation_body = entry_source[presentation_start:presentation_end]
        self.assertIn("aioFieldLabel(label)", presentation_body)
        self.assertIn(
            "tooltipKey || AIO_FIELD_TOOLTIP_KEYS[label]",
            presentation_body,
        )
        self.assertIn('aioFormat("tip.fieldGeneric"', presentation_body)

        for local_function in ("createDialog", "createNodeField", "field"):
            with self.subTest(local_function=local_function):
                self.assertNotRegex(
                    entry_source,
                    rf"\bfunction\s+{local_function}\(",
                )

        self.assertTrue(AIO_DIALOG_PRIMITIVES_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_dialog_primitives_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_input_settings_dialog_has_closed_controller_boundary(self):
        source = AIO_INPUT_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source),
            ["aioCreateInputSettingsDialog"],
        )
        self.assertLessEqual(len(source.splitlines()), 100)
        self.assertNotRegex(source, re.compile(r"^\s*import\s", re.MULTILINE))
        self.assertNotRegex(source, r"\b(?:app|api)\b")
        self.assertNotIn("app.registerExtension", source)
        self.assertNotIn("fetch(", source)
        self.assertNotRegex(
            source,
            re.compile(r"^(?:window|globalThis)\.[A-Za-z_$]", re.MULTILINE),
        )

        self.assertIn(
            'import { aioCreateInputSettingsDialog } from "./aio/input_settings_dialog.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+openInputSettings\s*=\s*aioCreateInputSettingsDialog"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        dependency_entries = {
            line.strip().removesuffix(",")
            for line in factory_match.group("dependencies").splitlines()
            if line.strip()
        }
        self.assertEqual(
            dependency_entries,
            {
                "document",
                "createDialog",
                "field",
                "selectInput",
                "staticText: aioStaticText",
                "text: aioText",
                "defaultInputSettings: DEFAULT_INPUT_SETTINGS",
                "inputSettingsWidget: INPUT_SETTINGS_WIDGET",
                "findWidget",
                "parseSettings",
                "mergeDefaults",
                "writeSettings",
            },
        )

        self.assertNotRegex(entry_source, r"\bfunction\s+openInputSettings\(")
        self.assertIn(
            "const openPreviewSettings = aioCreatePreviewSettingsDialog",
            entry_source,
        )

        hook_start = entry_source.index("function hookInputNode")
        hook_end = entry_source.index("\nfunction hookGeneratorNode", hook_start)
        hook_body = entry_source[hook_start:hook_end]
        self.assertIn(
            'ensureButton(node, "easyuse_anima_input_settings", "Settings...", '
            '() => openInputSettings(node));',
            hook_body,
        )
        self.assertEqual(entry_source.count("openInputSettings(node)"), 1)

        self.assertTrue(AIO_INPUT_SETTINGS_DIALOG_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_input_settings_dialog_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_postprocess_settings_dialog_has_closed_controller_boundary(self):
        source = AIO_POSTPROCESS_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source),
            ["aioCreatePostprocessSettingsDialog"],
        )
        self.assertLessEqual(len(source.splitlines()), 150)
        self.assertNotRegex(source, re.compile(r"^\s*import\s", re.MULTILINE))
        self.assertNotRegex(source, r"\b(?:app|api)\b")
        self.assertNotIn("app.registerExtension", source)
        self.assertNotIn("fetch(", source)
        self.assertNotRegex(
            source,
            re.compile(r"^(?:window|globalThis)\.[A-Za-z_$]", re.MULTILINE),
        )

        self.assertIn(
            'import { aioCreatePostprocessSettingsDialog } from '
            '"./aio/postprocess_settings_dialog.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+openPostprocessSettings\s*=\s*"
            r"aioCreatePostprocessSettingsDialog"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        dependency_entries = {
            line.strip().removesuffix(",")
            for line in factory_match.group("dependencies").splitlines()
            if line.strip()
        }
        self.assertEqual(
            dependency_entries,
            {
                "document",
                "createDialog",
                "field",
                "checkbox",
                "selectInput",
                "numberInput",
                "staticText: aioStaticText",
                "text: aioText",
                "defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS",
                "generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET",
                "findWidget",
                "generatorSettings",
                "mergeDefaults",
                "clampNumber: clampGeneratorNumber",
                "writeSettings",
                "renderGeneratorPanel",
            },
        )

        self.assertNotRegex(entry_source, r"\bfunction\s+openPostprocessSettings\(")
        self.assertIn(
            "const openPreviewSettings = aioCreatePreviewSettingsDialog",
            entry_source,
        )
        self.assertIn("const openInputSettings = aioCreateInputSettingsDialog", entry_source)

        self.assertIn("openPostprocessSettings(node)", panel_source)
        self.assertEqual(panel_source.count("openPostprocessSettings(node)"), 1)

        self.assertIn("...postprocess", source)
        self.assertIn("...fit", source)
        self.assertTrue(AIO_POSTPROCESS_SETTINGS_DIALOG_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_postprocess_settings_dialog_smoke.mjs"',
            frontend_check_source,
        )

    def test_aio_preview_settings_dialog_has_closed_controller_boundary(self):
        source = AIO_PREVIEW_SETTINGS_DIALOG_JS.read_text(encoding="utf-8")
        entry_source = AIO_JS.read_text(encoding="utf-8")
        panel_source = AIO_GENERATOR_PANEL_RUNTIME_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(source.splitlines()[0], "// @ts-check")
        self.assertEqual(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", source),
            ["aioCreatePreviewSettingsDialog"],
        )
        self.assertLessEqual(len(source.splitlines()), 150)
        self.assertNotRegex(source, re.compile(r"^\s*import\s", re.MULTILINE))
        self.assertNotRegex(source, r"\b(?:app|api)\b")
        self.assertNotIn("app.registerExtension", source)
        self.assertNotIn("fetch(", source)
        self.assertNotRegex(
            source,
            re.compile(r"^(?:window|globalThis)\.[A-Za-z_$]", re.MULTILINE),
        )

        self.assertIn(
            'import { aioCreatePreviewSettingsDialog } from '
            '"./aio/preview_settings_dialog.js";',
            entry_source,
        )
        factory_match = re.search(
            r"const\s+openPreviewSettings\s*=\s*"
            r"aioCreatePreviewSettingsDialog"
            r"\(\{(?P<dependencies>.*?)\}\);",
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(factory_match)
        dependency_entries = {
            line.strip().removesuffix(",")
            for line in factory_match.group("dependencies").splitlines()
            if line.strip()
        }
        self.assertEqual(
            dependency_entries,
            {
                "document",
                "createDialog",
                "field",
                "checkbox",
                "numberInput",
                "staticText: aioStaticText",
                "text: aioText",
                "defaultGenerationSettings: DEFAULT_GENERATION_SETTINGS",
                "generatorSettingsWidget: GENERATOR_SETTINGS_WIDGET",
                "findWidget",
                "generatorSettings",
                "mergeDefaults",
                "clampNumber: clampGeneratorNumber",
                "defaultPreviewIndex: aioDefaultPreviewIndex",
                "applyVisibleSettings: applyVisibleGeneratorSettings",
                "writeSettings",
                "renderGeneratorPanel",
            },
        )

        self.assertNotRegex(entry_source, r"\bfunction\s+openPreviewSettings\(")
        self.assertIn("openPreviewSettings(node)", panel_source)
        self.assertEqual(panel_source.count("openPreviewSettings(node)"), 1)

        self.assertTrue(AIO_PREVIEW_SETTINGS_DIALOG_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_aio_preview_settings_dialog_smoke.mjs"',
            frontend_check_source,
        )

    def test_legacy_regional_common_is_thin_compatibility_adapter(self):
        common_source = PROMPT_STUDIO_COMMON_JS.read_text(encoding="utf-8")
        entry_source = PROMPT_STUDIO_REGIONAL_JS.read_text(encoding="utf-8")

        self.assertLessEqual(len(common_source.splitlines()), 6)
        self.assertIn(
            'export * from "./prompt_studio/regional/editor_adapter.js";',
            common_source,
        )
        self.assertNotIn("easyuseAnimaGetSettings", common_source)
        self.assertNotIn("window.addEventListener", common_source)
        self.assertIn(
            'from "./prompt_studio/regional/editor_adapter.js"',
            entry_source,
        )
        self.assertNotIn("easyuse_anima_prompt_studio_common.js", entry_source)

    def test_regional_adapter_function_exports_are_consumed_by_entry(self):
        adapter_source = PROMPT_STUDIO_REGIONAL_ADAPTER_JS.read_text(
            encoding="utf-8"
        )
        entry_source = PROMPT_STUDIO_REGIONAL_JS.read_text(encoding="utf-8")
        import_match = re.search(
            r'import\s+\{(?P<names>[^}]*)\}\s+from\s+'
            r'"\./prompt_studio/regional/editor_adapter\.js";',
            entry_source,
            re.DOTALL,
        )
        self.assertIsNotNone(import_match)
        imported_functions = {
            name.strip()
            for name in import_match.group("names").split(",")
            if name.strip()
        }
        exported_functions = set(
            re.findall(r"export function ([A-Za-z0-9_]+)\(", adapter_source)
        )

        self.assertEqual(exported_functions, imported_functions)

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
        node_hooks_source = (
            PROMPT_STUDIO_MODULES / "node_hooks.js"
        ).read_text(encoding="utf-8")
        advanced_node_ui_source = (
            PROMPT_STUDIO_MODULES / "advanced_node_ui.js"
        ).read_text(encoding="utf-8")

        self.assertIn("app.registerExtension", source)
        self.assertIn('../../../scripts/api.js"', source)
        self.assertIn("createPromptStudioExtensionRuntime(app, api)", source)
        self.assertIn('./prompt_studio/extension_runtime.js"', source)
        self.assertIn("./constants.js", extension_runtime_source)
        self.assertIn('./advanced_controls.js"', advanced_node_ui_source)
        self.assertIn("./advanced_node_ui.js", extension_runtime_source)
        self.assertIn('./advanced_fields_ui.js"', advanced_node_ui_source)
        self.assertIn("./advanced_fields_state.js", extension_runtime_source)
        self.assertIn("./advanced_values.js", extension_runtime_source)
        self.assertIn("./wildcard_seed_transaction.js", extension_runtime_source)
        self.assertIn("../lifecycle/queue_ui_transaction.js", extension_runtime_source)
        self.assertIn("../lifecycle/executed_event_context.js", extension_runtime_source)
        self.assertIn('"advanced-wildcard-seed-transaction"', extension_runtime_source)
        self.assertIn("queueHost: api", extension_runtime_source)
        self.assertNotIn("./advanced_queue_seed_runtime.js", extension_runtime_source)
        self.assertNotIn("./queue_seed_bridge.js", extension_runtime_source)
        self.assertNotIn("installAdvancedQueueSeedQueueHook", extension_runtime_source)
        self.assertNotIn("shouldApplyExecutedSeed", extension_runtime_source)
        self.assertNotIn("attachAdvancedQueueSeedNode", node_hooks_source)
        self.assertNotIn("detachAdvancedQueueSeedNode", node_hooks_source)
        self.assertTrue(WILDCARD_VALUES_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_wildcard_values_smoke.mjs"',
            FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8"),
        )
        advanced_values_source = (
            PROMPT_STUDIO_MODULES / "advanced_values.js"
        ).read_text(encoding="utf-8")
        studio_values_source = (
            PROMPT_STUDIO_MODULES / "studio_values.js"
        ).read_text(encoding="utf-8")
        self.assertNotIn("shouldApplyExecutedSeed", advanced_values_source)
        self.assertNotIn("applyAdvancedExecutedInputs", advanced_values_source)
        self.assertNotIn("applyExecutedInputs", studio_values_source)
        self.assertNotIn("hooks.applyExecutedInputs", node_hooks_source)
        self.assertIn("publishAdvancedWildcardExecution", advanced_values_source)
        self.assertIn("wildcard_execution_seed", advanced_values_source)
        self.assertIn("writePreviousWildcardExecution", advanced_values_source)
        self.assertTrue(PROMPT_STUDIO_ADVANCED_VALUES_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_prompt_studio_advanced_values_smoke.mjs"',
            FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8"),
        )
        self.assertTrue(PROMPT_STUDIO_WILDCARD_TRANSACTION_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_prompt_studio_wildcard_transaction_smoke.mjs"',
            FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8"),
        )
        self.assertTrue(PROMPT_STUDIO_RESOLUTION_ORIENTATION_SMOKE.is_file())
        self.assertIn(
            r'node "tests\frontend_prompt_studio_resolution_orientation_smoke.mjs"',
            FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8"),
        )
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
        regional_source = PROMPT_STUDIO_REGIONAL_ADAPTER_JS.read_text(
            encoding="utf-8"
        )
        constants_source = (PROMPT_STUDIO_MODULES / "constants.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('from "./highlight_core.js"', modular_source)
        self.assertIn(
            'from "../highlight_core.js"', regional_source
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
        regional_source = PROMPT_STUDIO_REGIONAL_ADAPTER_JS.read_text(
            encoding="utf-8"
        )
        constants_source = (PROMPT_STUDIO_MODULES / "constants.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('from "./highlight_overlay_core.js"', modular_source)
        self.assertIn(
            'from "../highlight_overlay_core.js"', regional_source
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
        adapter_source = PROMPT_STUDIO_REGIONAL_ADAPTER_JS.read_text(
            encoding="utf-8"
        )
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")
        regional_sources = {
            path.name: path.read_text(encoding="utf-8")
            for path in PROMPT_STUDIO_REGIONAL_MODULES.glob("*.js")
        }
        combined_regional_source = "\n".join(regional_sources.values())
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
                self.assertIn(f'"./{filename}"', combined_regional_source)

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
            'from "./constants.js"',
            adapter_source,
        )
        self.assertNotIn(
            "export const PROMPT_STUDIO_RESOLUTION_BUCKETS",
            adapter_source,
        )
        self.assertTrue(PROMPT_STUDIO_REGIONAL_PURE_DATA_SMOKE.is_file())
        self.assertIn(
            'node "tests\\frontend_regional_pure_data_smoke.mjs"',
            frontend_check_source,
        )

        runtime_source = regional_sources["runtime.js"]
        write_fields_source = runtime_source[
            runtime_source.index("function writeRegionalFields"):
            runtime_source.index("function writeRegionalConfig")
        ]
        write_config_source = runtime_source[
            runtime_source.index("function writeRegionalConfig"):
            runtime_source.index("function updateRegionalConfigCanvas")
        ]
        self.assertIn("options.syncInputs !== false", write_fields_source)
        self.assertIn("syncRegionalFieldInputs(node, normalized)", write_fields_source)
        self.assertNotIn("syncRegionalFieldInputs", write_config_source)

    def test_regional_ui_runtime_modules_have_owned_lifecycle(self):
        entry_source = PROMPT_STUDIO_REGIONAL_JS.read_text(encoding="utf-8")
        frontend_check_source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")
        combined_regional_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in PROMPT_STUDIO_REGIONAL_MODULES.glob("*.js")
        )
        expected_modules = {
            "editor_adapter.js": (
                "installPromptStudioRegionalAdapter",
                "refreshPromptStudioHighlights",
            ),
            "extension.js": (
                "createRegionalExtensionRuntime",
                "installRegionalSaveSync",
                "registerRegionalNodeHooks",
            ),
            "field_editor.js": (
                "createRegionalFieldEditor",
                "moveRegionalFieldInPane",
            ),
            "layout.js": (
                "createRegionalLayout",
                "REGIONAL_NODE_MIN_WIDTH",
            ),
            "lifecycle.js": (
                "disposeRegionalNodeLifecycle",
                "scheduleRegionalNodeFrame",
                "setRegionalNodeCleanup",
            ),
            "mask_editor.js": (
                "createRegionalMaskEditor",
                "drawMaskCanvas",
                "canvasPoint",
            ),
            "runtime.js": (
                "createRegionalRuntime",
            ),
        }

        for filename, symbols in expected_modules.items():
            with self.subTest(module=filename):
                path = PROMPT_STUDIO_REGIONAL_MODULES / filename
                self.assertTrue(path.is_file())
                source = path.read_text(encoding="utf-8")
                self.assertTrue(source.startswith("// @ts-check"))
                self.assertNotIn("app.registerExtension", source)
                self.assertNotRegex(
                    source,
                    re.compile(r"^(?:document|window)\.", re.MULTILINE),
                )
                for symbol in symbols:
                    self.assertRegex(source, rf"\b{symbol}\b")
                if filename == "lifecycle.js":
                    self.assertIn('"./lifecycle.js"', combined_regional_source)
                else:
                    self.assertIn(
                        f'./prompt_studio/regional/{filename}"',
                        entry_source,
                    )

        self.assertLess(len(entry_source.splitlines()), 100)
        self.assertEqual(entry_source.count("app.registerExtension("), 1)
        self.assertNotIn("function openMaskEditor", entry_source)
        self.assertNotIn("function renderRegionalEditor", entry_source)
        self.assertNotIn("prototype.onRemoved", entry_source)
        self.assertTrue(PROMPT_STUDIO_REGIONAL_RUNTIME_SMOKE.is_file())
        self.assertIn(
            'node "tests\\frontend_regional_runtime_smoke.mjs"',
            frontend_check_source,
        )

    def test_prompt_studio_wildcard_seed_controls_share_public_contract(self):
        contract_source = (
            PROMPT_STUDIO_MODULES / "wildcard_seed_contract.js"
        ).read_text(encoding="utf-8")
        advanced_source = (
            PROMPT_STUDIO_MODULES / "advanced_controls.js"
        ).read_text(encoding="utf-8")
        regional_source = (
            PROMPT_STUDIO_REGIONAL_MODULES / "field_editor.js"
        ).read_text(encoding="utf-8")
        wildcard_values_source = (
            PROMPT_STUDIO_MODULES / "wildcard_values.js"
        ).read_text(encoding="utf-8")
        node_hooks_source = (
            PROMPT_STUDIO_MODULES / "node_hooks.js"
        ).read_text(encoding="utf-8")

        self.assertIn("Number.MAX_SAFE_INTEGER", contract_source)
        self.assertIn("BigInt(decimal)", contract_source)
        self.assertIn("bindWildcardSeedInput", contract_source)
        self.assertIn("normalizeWildcardSeedInput", contract_source)
        self.assertIn("nextWildcardSeed", contract_source)
        self.assertIn("normalizeWildcardSeedControl", contract_source)
        self.assertIn("globalThis.requestAnimationFrame", contract_source)
        self.assertIn("input.isConnected !== true", contract_source)
        self.assertIn("!state.dirty", contract_source)
        extension_source = (
            PROMPT_STUDIO_MODULES / "extension_runtime.js"
        ).read_text(encoding="utf-8")
        self.assertIn("hookWildcardSeedWidget,", extension_source)
        self.assertIn("hookWildcardSeedWidget", wildcard_values_source)
        self.assertIn(
            "hooks.hookWildcardSeedWidget?.(this, { resetSeedControl: false });",
            node_hooks_source,
        )
        self.assertIn(
            "hooks.hookWildcardSeedWidget?.(this, { resetSeedControl: true });",
            node_hooks_source,
        )
        for source in (advanced_source, regional_source):
            with self.subTest(module="seed-control"):
                self.assertIn("wildcard_seed_contract.js", source)
                self.assertIn("bindWildcardSeedInput", source)
                self.assertGreaterEqual(
                    source.count("normalizeWildcardSeedControl"),
                    2,
                )
        self.assertIn(
            'const ADVANCED_WILDCARD_MODES = ["일반", "순차"];',
            (PROMPT_STUDIO_MODULES / "constants.js").read_text(encoding="utf-8"),
        )
        self.assertIn(
            'export const PROMPT_STUDIO_WILDCARD_MODES = ["일반", "순차"];',
            (PROMPT_STUDIO_REGIONAL_MODULES / "constants.js").read_text(encoding="utf-8"),
        )
        self.assertIn(
            'const ADVANCED_WILDCARD_SEED_CONTROLS = ["fixed", "randomize", "increment"];',
            (PROMPT_STUDIO_MODULES / "constants.js").read_text(encoding="utf-8"),
        )
        self.assertIn(
            'export const PROMPT_STUDIO_WILDCARD_SEED_CONTROLS = ["fixed", "randomize", "increment"];',
            (PROMPT_STUDIO_REGIONAL_MODULES / "constants.js").read_text(encoding="utf-8"),
        )
        self.assertIn('headerHelpKey: "advanced.wildcardHelp"', advanced_source)
        self.assertIn("controlSelect.addEventListener(\"change\", syncControl);", advanced_source)
        self.assertIn("controlSelect.addEventListener(\"change\", syncControl);", regional_source)

    def test_prompt_studio_wildcard_tooltips_follow_the_selected_mode(self):
        constants_source = (PROMPT_STUDIO_MODULES / "constants.js").read_text(
            encoding="utf-8"
        )
        advanced_source = (
            PROMPT_STUDIO_MODULES / "advanced_controls.js"
        ).read_text(encoding="utf-8")
        regional_source = (
            PROMPT_STUDIO_REGIONAL_MODULES / "field_editor.js"
        ).read_text(encoding="utf-8")

        for mode_key in ("populate", "sequential"):
            with self.subTest(mode=mode_key):
                locale_key = f'"advanced.wildcardMode.{mode_key}Title"'
                self.assertEqual(constants_source.count(locale_key), 4)
        for removed_mode_key in ("fixed", "reproduce"):
            self.assertNotIn(
                f'"advanced.wildcardMode.{removed_mode_key}Title"',
                constants_source,
            )

        self.assertEqual(constants_source.count('"advanced.wildcardHelp"'), 4)
        self.assertEqual(constants_source.count('"advanced.wildcardHelpLabel"'), 4)
        for control_key in ("fixed", "randomize", "increment"):
            with self.subTest(control=control_key):
                self.assertEqual(
                    constants_source.count(f'"advanced.wildcardSeedControl.{control_key}"'),
                    4,
                )

        for syntax in (
            "__name__",
            "{a|b|c}",
            "N::candidate",
            "{n$$...}",
            "{min-max$$separator$$...}",
            "N#__name__",
        ):
            with self.subTest(syntax=syntax):
                self.assertGreaterEqual(constants_source.count(syntax), 4)

        self.assertNotIn(
            "Wildcard expansion mode used when the node is queued.",
            constants_source,
        )
        self.assertIn("function advancedWildcardModeTitle", advanced_source)
        self.assertIn("option.title = advancedWildcardModeTitle(mode);", advanced_source)
        self.assertIn(
            "applyAdvancedWildcardModeTitle(modeRow, modeSelect, nextMode);",
            advanced_source,
        )
        self.assertIn('select.setAttribute("aria-description", title);', advanced_source)
        self.assertIn("function wildcardModeTitle", regional_source)
        self.assertIn("option.title = wildcardModeTitle(mode);", regional_source)
        self.assertIn('modeSelect.setAttribute("aria-description", selectedModeTitle);', regional_source)
        self.assertIn("row.title = `${selectedModeTitle}\\n", regional_source)

    def test_prompt_studio_phase_2_modules_export_expected_symbols(self):
        advanced_controls_source = (
            PROMPT_STUDIO_MODULES / "advanced_controls.js"
        ).read_text(encoding="utf-8")
        wildcard_seed_history_source = (
            PROMPT_STUDIO_MODULES / "wildcard_seed_history.js"
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
            "PREVIOUS_WILDCARD_EXECUTION_PROPERTY",
            "normalizePreviousWildcardExecution",
            "readPreviousWildcardExecution",
            "serializePreviousWildcardExecution",
            "wildcardModeWidgetValue",
            "writePreviousWildcardExecution",
        ):
            with self.subTest(module="wildcard_seed_history", symbol=name):
                self.assertIn(f"  {name},", wildcard_seed_history_source)

        self.assertIn("advanced.wildcardPreviousSeedReuse", advanced_controls_source)
        self.assertIn('serialized.widgets_values[index] = value;', wildcard_seed_history_source)

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
            "publishAdvancedWildcardExecution",
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
            "restoreInputFromWidget",
            "syncStudioValues",
            "syncWidgetValue",
        ):
            with self.subTest(module="studio_values", symbol=name):
                self.assertIn(f"  {name},", studio_values_source)

        for name in (
            "applyWildcardExecutedInputs",
            "hookWildcardSeedWidget",
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

    def test_prompt_studio_paste_autosize_is_bounded_revision_owned_and_grow_only(self):
        stabilizer_source = (
            PROMPT_STUDIO_MODULES / "textarea_stabilization.js"
        ).read_text(encoding="utf-8")
        classic_source = (
            PROMPT_STUDIO_MODULES / "studio_resizable_input.js"
        ).read_text(encoding="utf-8")
        advanced_source = (
            PROMPT_STUDIO_MODULES / "advanced_fields_ui.js"
        ).read_text(encoding="utf-8")
        widgets_source = (
            PROMPT_STUDIO_MODULES / "widgets.js"
        ).read_text(encoding="utf-8")
        runner_source = (
            ROOT / "tools" / "check_frontend.ps1"
        ).read_text(encoding="utf-8")

        self.assertIn("const TEXTAREA_STABILIZATION_FRAMES = 2", stabilizer_source)
        self.assertIn("let revision = 0", stabilizer_source)
        self.assertIn("const ownedRevision = revision", stabilizer_source)
        self.assertIn("textarea?.isConnected === false", stabilizer_source)
        self.assertIn("remainingFrames > 0 && (grew || !fits)", stabilizer_source)
        self.assertIn('textarea.style.overflowY = "hidden"', stabilizer_source)
        self.assertNotIn("setInterval", stabilizer_source)
        self.assertNotIn("setTimeout", stabilizer_source)

        for source in (classic_source, advanced_source):
            self.assertIn("createTextareaGrowStabilizer", source)
            self.assertIn("heightStabilizer.schedule()", source)
            self.assertIn("currentHeight", source)
            self.assertIn("nextHeight", source)

        self.assertIn("widget?.__easyuseAnimaStudioInput", widgets_source)
        self.assertIn("widget?.inputEl", widgets_source)
        self.assertIn("widget?.element", widgets_source)
        self.assertIn('candidate?.querySelector?.("textarea, input")', widgets_source)
        self.assertIn("input.isConnected !== false", widgets_source)

        resolver_source = (
            PROMPT_STUDIO_MODULES / "studio_input_resolver.js"
        ).read_text(encoding="utf-8")
        self.assertIn('".lg-node[data-node-id]"', resolver_source)
        self.assertIn('"aria-label"', resolver_source)
        self.assertIn("anonymousFieldNames.indexOf(widget.name)", resolver_source)
        self.assertIn("widget.__easyuseAnimaStudioInput = input", resolver_source)
        self.assertNotIn("addEventListener", resolver_source)
        self.assertNotIn("MutationObserver", resolver_source)

        self.assertIn(
            'node "tests\\frontend_prompt_studio_paste_autosize_smoke.mjs"',
            runner_source,
        )

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
            "web/js/aio/**/*.js",
            "web/js/easyuse_anima_prompt_studio.js",
            "web/js/easyuse_anima_prompt_studio_regional.js",
            "web/js/prompt_studio/**/*.js",
        ):
            with self.subTest(path=path):
                self.assertIn(path, config["include"])

    def test_root_entry_typecheck_coverage_has_explicit_debt(self):
        config = json.loads(JSCONFIG.read_text(encoding="utf-8"))
        covered_root_entries = {
            entry
            for entry in config["include"]
            if entry.startswith("web/js/")
            and "/" not in entry.removeprefix("web/js/")
            and "*" not in entry
        }
        debt_root_entries = set()
        actual_root_entries = {
            path.relative_to(ROOT).as_posix()
            for path in WEB_JS.glob("*.js")
        }

        for entry in config["include"]:
            if entry.startswith("web/js/"):
                first_component = entry.removeprefix("web/js/").split("/", 1)[0]
                self.assertFalse(
                    any(marker in first_component for marker in "*?["),
                    f"Root-level wildcard would bypass the explicit debt ledger: {entry}",
                )

        self.assertTrue(covered_root_entries.isdisjoint(debt_root_entries))
        self.assertEqual(
            actual_root_entries,
            covered_root_entries | debt_root_entries,
        )

    def test_frontend_check_script_runs_syntax_and_typecheck(self):
        source = FRONTEND_CHECK_SCRIPT.read_text(encoding="utf-8")

        self.assertIn('Get-ChildItem -File -Recurse -Path "web\\js"', source)
        self.assertIn("& node --check", source)
        self.assertIn(r'& node "tests\frontend_highlight_core_smoke.mjs"', source)
        self.assertIn(
            r'& node "tests\frontend_highlight_overlay_core_smoke.mjs"', source
        )
        self.assertIn(
            r'& node "tests\frontend_aio_profile_core_smoke.mjs"', source
        )
        self.assertIn(
            r'& node "tests\frontend_aio_dependency_core_smoke.mjs"', source
        )
        self.assertIn(
            r'& node "tests\frontend_aio_preview_core_smoke.mjs"', source
        )
        self.assertIn(
            r'& node "tests\frontend_aio_native_preview_runtime_smoke.mjs"',
            source,
        )
        self.assertIn(
            r'& node "tests\frontend_aio_settings_core_smoke.mjs"', source
        )
        self.assertIn(
            r'& node "tests\frontend_lora_preset_profile_mutations_smoke.mjs"',
            source,
        )
        self.assertIn('"typescript@$TypeScriptVersion"', source)
        self.assertIn("tsc -p jsconfig.json", source)

    def test_prompt_studio_split_modules_start_with_ts_check(self):
        for path in sorted(PROMPT_STUDIO_MODULES.rglob("*.js")):
            relative = path.relative_to(PROMPT_STUDIO_MODULES).as_posix()
            with self.subTest(filename=relative):
                first_line = path.read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(first_line, "// @ts-check")

    def test_prompt_studio_split_modules_have_no_import_cycles(self):
        module_paths = {
            path.relative_to(PROMPT_STUDIO_MODULES).as_posix(): path
            for path in sorted(PROMPT_STUDIO_MODULES.rglob("*.js"))
        }
        graph = {name: [] for name in module_paths}
        for name, path in module_paths.items():
            source = path.read_text(encoding="utf-8")
            for import_path in STATIC_IMPORT_RE.findall(source):
                target_path = (path.parent / import_path).resolve()
                try:
                    target = target_path.relative_to(
                        PROMPT_STUDIO_MODULES.resolve()
                    ).as_posix()
                except ValueError:
                    continue
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
            "wildcard_seed_contract.js",
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

    def test_regional_modules_have_explicit_runtime_installation(self):
        for path in sorted(PROMPT_STUDIO_REGIONAL_MODULES.glob("*.js")):
            with self.subTest(filename=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn("app.registerExtension", source)
                self.assertNotIn("fetch(", source)
                self.assertNotRegex(
                    source,
                    re.compile(r"^(?:document|window)\.", re.MULTILINE),
                )

        adapter_source = PROMPT_STUDIO_REGIONAL_ADAPTER_JS.read_text(
            encoding="utf-8"
        )
        extension_source = (
            PROMPT_STUDIO_REGIONAL_MODULES / "extension.js"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "export function installPromptStudioRegionalAdapter()",
            adapter_source,
        )
        self.assertNotIn(
            'if (typeof window !== "undefined") {\n'
            "  loadPromptStudioCommonSettings();",
            adapter_source,
        )
        self.assertIn("hooks.installRegionalAdapter();", extension_source)
        self.assertLess(
            extension_source.index("hooks.installRegionalAdapter();"),
            extension_source.index("installSaveSync();", extension_source.index("async setup()")),
        )


if __name__ == "__main__":
    unittest.main()
