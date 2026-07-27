from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_MODULES = (
    "easyuse_anima",
    "easyuse_anima.bootstrap",
    "easyuse_anima.workflow",
    "easyuse_anima.aio",
    "easyuse_anima.aio.conditioning",
    "easyuse_anima.aio.first_pass_cache",
    "easyuse_anima.aio.legacy_generation",
    "easyuse_anima.aio.generation_detailer_stage",
    "easyuse_anima.aio.generation_first_pass",
    "easyuse_anima.aio.generation_highres",
    "easyuse_anima.aio.generation_lifecycle",
    "easyuse_anima.aio.generation_pipeline",
    "easyuse_anima.aio.generation_postprocess_stage",
    "easyuse_anima.aio.generation_save_output_stage",
    "easyuse_anima.aio.generation_upscale_stage",
    "easyuse_anima.aio.generation_normalization",
    "easyuse_anima.aio.generation_values",
    "easyuse_anima.aio.model_preparation",
    "easyuse_anima.aio.output",
    "easyuse_anima.aio.postprocess",
    "easyuse_anima.aio.preview",
    "easyuse_anima.aio.sampling",
    "easyuse_anima.aio.generation_sampling",
    "easyuse_anima.aio.generation_features",
    "easyuse_anima.aio.generation_detailer",
    "easyuse_anima.aio.generation_output",
    "easyuse_anima.aio.generation_defaults",
    "easyuse_anima.aio.input_defaults",
    "easyuse_anima.aio.input_context",
    "easyuse_anima.aio.generation_migrations",
    "easyuse_anima.aio.generation_settings",
    "easyuse_anima.aio.resources",
    "easyuse_anima.aio.usdu",
    "easyuse_anima.api",
    "easyuse_anima.api.errors",
    "easyuse_anima.api.requests",
    "easyuse_anima.api.responses",
    "easyuse_anima.api.routes",
    "easyuse_anima.api.routes.aio_torch_compile",
    "easyuse_anima.api.routes.autocomplete",
    "easyuse_anima.api.routes.lora_catalog",
    "easyuse_anima.api.routes.long_text_settings",
    "easyuse_anima.api.routes.translation",
    "easyuse_anima.api.routes.translation_execution",
    "easyuse_anima.api.routes.wildcards",
    "easyuse_anima.autocomplete",
    "easyuse_anima.autocomplete.classification",
    "easyuse_anima.autocomplete.dataset",
    "easyuse_anima.autocomplete.index",
    "easyuse_anima.autocomplete.search",
    "easyuse_anima.common",
    "easyuse_anima.common.values",
    "easyuse_anima.common.serialization",
    "easyuse_anima.image",
    "easyuse_anima.image.geometry",
    "easyuse_anima.image.sam3",
    "easyuse_anima.infrastructure",
    "easyuse_anima.infrastructure.filesystem",
    "easyuse_anima.infrastructure.filesystem.atomic_json",
    "easyuse_anima.infrastructure.filesystem.paths",
    "easyuse_anima.infrastructure.comfy",
    "easyuse_anima.infrastructure.comfy.capabilities",
    "easyuse_anima.infrastructure.comfy.invocation",
    "easyuse_anima.infrastructure.comfy.resources",
    "easyuse_anima.lora",
    "easyuse_anima.naia",
    "easyuse_anima.nodes",
    "easyuse_anima.nodes.aio_nodes",
    "easyuse_anima.nodes.input_types",
    "easyuse_anima.nodes.impact_detailer_nodes",
    "easyuse_anima.nodes.prompt_advanced_nodes",
    "easyuse_anima.nodes.prompt_data_nodes",
    "easyuse_anima.nodes.regional_nodes",
    "easyuse_anima.nodes.sam3_nodes",
    "easyuse_anima.profiles",
    "easyuse_anima.profiles.aio",
    "easyuse_anima.profiles.contract",
    "easyuse_anima.profiles.lora",
    "easyuse_anima.profiles.mutation",
    "easyuse_anima.profiles.repository",
    "easyuse_anima.settings",
    "easyuse_anima.settings.repository",
    "easyuse_anima.settings.schema",
    "easyuse_anima.settings.service",
    "easyuse_anima.translation",
    "easyuse_anima.translation.contracts",
    "easyuse_anima.translation.markers",
    "easyuse_anima.translation.providers",
    "easyuse_anima.translation.providers.google",
    "easyuse_anima.translation.service",
    "easyuse_anima.wildcard",
    "easyuse_anima.wildcard.expansion",
    "easyuse_anima.wildcard.library",
    "easyuse_anima.wildcard.mode",
    "easyuse_anima.wildcard.models",
    "easyuse_anima.wildcard.seed",
    "easyuse_anima.wildcard.selector",
    "easyuse_anima.wildcard.snapshot",
    "easyuse_anima.wildcard.sources",
    "easyuse_anima.seed.execution_identity",
    "easyuse_anima.seed.execution_session",
    "easyuse_anima.seed.service",
    "easyuse_anima.prompt",
    "easyuse_anima.prompt.anima",
    "easyuse_anima.prompt.advanced",
    "easyuse_anima.prompt.artist_mix",
    "easyuse_anima.prompt.conditioning",
    "easyuse_anima.prompt.data",
    "easyuse_anima.prompt.regional",
)


class PythonPackageSkeletonTests(unittest.TestCase):
    def test_direct_imports_have_empty_surface_and_no_runtime_side_effects(self):
        script = f"""
import importlib
import json
import os
import socket
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, {str(ROOT)!r})
sys.dont_write_bytecode = True
modules = {json.dumps(PACKAGE_MODULES)}
forbidden_roots = {{
    "aiohttp",
    "comfy",
    "folder_paths",
    "numpy",
    "requests",
    "server",
    "torch",
}}
before = set(sys.modules)

def blocked(name):
    def fail(*_args, **_kwargs):
        raise AssertionError(f"package import attempted {{name}}")
    return fail

with ExitStack() as stack:
    for owner, name in (
        (os, "makedirs"),
        (os, "mkdir"),
        (os, "remove"),
        (os, "rename"),
        (os, "replace"),
        (os, "unlink"),
        (Path, "mkdir"),
        (Path, "rename"),
        (Path, "replace"),
        (Path, "touch"),
        (Path, "unlink"),
        (Path, "write_bytes"),
        (Path, "write_text"),
        (socket, "create_connection"),
        (socket.socket, "connect"),
    ):
        stack.enter_context(patch.object(owner, name, blocked(f"{{owner}}.{{name}}")))
    imported = [importlib.import_module(name) for name in modules]

new_forbidden = sorted(
    root
    for root in forbidden_roots
    if root in sys.modules and root not in before
)
print(json.dumps({{
    "declared_all": [module.__all__ for module in imported],
    "modules": [module.__name__ for module in imported],
    "new_forbidden": new_forbidden,
}}))
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["modules"], list(PACKAGE_MODULES))
        expected_all = [[] for _ in PACKAGE_MODULES]
        expected_all[PACKAGE_MODULES.index("easyuse_anima.bootstrap")] = ["initialize"]
        expected_all[PACKAGE_MODULES.index("easyuse_anima.api.errors")] = [
            "ApiContractError"
        ]
        expected_all[PACKAGE_MODULES.index("easyuse_anima.api.requests")] = [
            "parse_json_object",
            "json_object",
            "json_string",
            "json_boolean",
            "json_integer",
            "json_uuid_string",
        ]
        expected_all[PACKAGE_MODULES.index("easyuse_anima.api.responses")] = [
            "REQUEST_ID_HEADER",
            "error_payload",
            "create_request_id",
            "attach_request_id_header",
            "correlate_response",
        ]
        expected_all[
            PACKAGE_MODULES.index(
                "easyuse_anima.api.routes.aio_torch_compile"
            )
        ] = ["build_aio_torch_compile_recommend_handler"]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.api.routes.autocomplete")
        ] = [
            "build_autocomplete_handlers",
            "build_classify_prompt_handler",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.api.routes.lora_catalog")
        ] = ["build_loras_handler"]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.api.routes.long_text_settings")
        ] = ["build_long_text_settings_handlers"]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.api.routes.translation")
        ] = ["build_translate_prompt_handler"]
        expected_all[
            PACKAGE_MODULES.index(
                "easyuse_anima.api.routes.translation_execution"
            )
        ] = ["PromptTranslationRouteExecutor"]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.api.routes.wildcards")
        ] = ["build_wildcards_handler"]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.autocomplete.classification")
        ] = ["classify_prompt_text"]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.autocomplete.dataset")
        ] = [
            "DBR_TAG_ARCHIVE_SOURCE",
            "DBR_TAG_ARCHIVE_LICENSE",
            "DBR_DANBOORU_AUTOCOMPLETE_CSV",
            "DBR_E621_AUTOCOMPLETE_CSV",
            "DBR_MERGED_AUTOCOMPLETE_CSV",
            "LOCALSMILE_AUTOCOMPLETE_CSV",
            "AUTOCOMPLETE_CSV",
            "DEFAULT_AUTOCOMPLETE_SOURCE",
            "AUTOCOMPLETE_SOURCES",
            "AutocompleteEntry",
            "resolve_autocomplete_source",
            "available_autocomplete_sources",
            "autocomplete_status",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.autocomplete.index")
        ] = [
            "AUTOCOMPLETE_INDEX_SCHEMA_VERSION",
            "AutocompleteIndexSource",
            "IndexedAutocompleteEntry",
            "AutocompleteIndexDiagnostics",
            "AutocompleteIndexResult",
            "AutocompleteIndexUnavailable",
            "search_autocomplete_index",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.autocomplete.search")
        ] = ["search_autocomplete"]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.aio.generation_pipeline")
        ] = [
            "AIO_GENERATION_STAGE_ORDER",
            "ConditioningBundle",
            "GenerationCapabilities",
            "GenerationRequest",
            "GenerationStage",
            "GenerationState",
            "PromptExecutionData",
            "ResourceBundle",
            "WorkflowContext",
        ]
        expected_all[PACKAGE_MODULES.index("easyuse_anima.nodes.aio_nodes")] = [
            "EasyUseAnimaInput",
            "EasyUseAnimaAIOGenerator",
        ]
        expected_all[PACKAGE_MODULES.index("easyuse_anima.seed.service")] = [
            "InMemorySeedReservationService",
            "SeedReservationCapacityError",
            "SeedReservationConflictError",
            "SeedReservationServiceError",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.seed.execution_identity")
        ] = [
            "SEED_EXECUTION_IDENTITY_VERSION",
            "SeedExecutionContext",
            "SeedExecutionIdentity",
            "SeedExecutionIdentityError",
            "read_comfy_execution_context",
            "resolve_seed_execution_identity",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.seed.execution_session")
        ] = [
            "is_comfy_processing_interruption",
            "seed_execution_session",
        ]
        expected_all[PACKAGE_MODULES.index("easyuse_anima.prompt.anima")] = [
            "CorrectionResult",
            "KnowledgeBaseNotFound",
            "ParsedPrompt",
            "PromptKnowledgeBase",
            "TagInfo",
            "TagToken",
            "correct_prompt",
            "inspect_prompt",
            "load_knowledge_base",
        ]
        expected_all[
            PACKAGE_MODULES.index(
                "easyuse_anima.infrastructure.filesystem.atomic_json"
            )
        ] = ["AtomicJsonStore"]
        expected_all[
            PACKAGE_MODULES.index(
                "easyuse_anima.infrastructure.filesystem.paths"
            )
        ] = [
            "PACKAGE_DATA_DIR",
            "PACKAGE_ROOT",
            "SYSTEM_USER_NAME",
            "USER_DATA_DIR",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.settings.repository")
        ] = [
            "LONG_TEXT_SETTINGS_FILE",
            "SETTINGS_FILE",
            "get_settings",
            "load_long_text_settings",
            "save_long_text_settings",
            "save_setting",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.settings.schema")
        ] = [
            "AUTOCOMPLETE_COMMIT_KEYS",
            "AUTOCOMPLETE_COMMIT_MODES",
            "AUTOCOMPLETE_MODES",
            "COMFY_COLOR_SETTING_KEYS",
            "COMFY_SETTING_KEYS",
            "DEFAULT_SETTINGS",
            "LONG_TEXT_SETTING_ALIASES",
            "LONG_TEXT_SETTING_KEYS",
            "NAIA_PREPROCESSING_KEYS",
            "NAIA_RESOLUTION_BUCKETS",
            "NAIA_RESOLUTION_MODES",
            "PROMPT_STUDIO_COLOR_KEYS",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.settings.service")
        ] = [
            "public_settings",
            "resolve_autocomplete_commit_key",
            "resolve_autocomplete_commit_mode",
            "resolve_autocomplete_limit",
            "resolve_autocomplete_mode",
            "resolve_autocomplete_source",
            "resolve_lora_preset_menu_mode",
            "resolve_lora_preset_strength_button_step",
            "resolve_lora_preset_strength_drag_pixels",
            "resolve_lora_preset_strength_drag_step",
            "resolve_metadata_filter_words",
            "resolve_naia_port",
            "resolve_naia_resolution_bucket",
            "resolve_naia_resolution_max_long_edge",
            "resolve_naia_resolution_mode",
            "resolve_naia_resolution_scale",
            "resolve_naia_settings",
            "resolve_prompt_studio_font_family",
            "resolve_prompt_studio_font_size",
            "resolve_prompt_translation_provider",
            "resolve_prompt_translation_settings",
            "resolve_prompt_translation_source",
            "resolve_prompt_translation_target",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.translation.contracts")
        ] = [
            "DEFAULT_PROMPT_TRANSLATION_SOURCE",
            "DEFAULT_PROMPT_TRANSLATION_TARGET",
            "MAX_PROMPT_TRANSLATION_MARKER_CHARACTERS",
            "MAX_PROMPT_TRANSLATION_MARKERS",
            "MAX_PROMPT_TRANSLATION_TOTAL_CHARACTERS",
            "PROMPT_TRANSLATION_CACHE_MAX_ENTRIES",
            "PROMPT_TRANSLATION_CACHE_TTL_SECONDS",
            "PROMPT_TRANSLATION_PROVIDER_GOOGLE",
            "PROMPT_TRANSLATION_PROVIDER_OFF",
            "PROMPT_TRANSLATION_PROVIDER_TIMEOUT_SECONDS",
            "PROMPT_TRANSLATION_PROVIDERS",
            "PromptTranslationError",
            "PromptTranslationLimitError",
            "PromptTranslationSettings",
            "TranslationBusyError",
            "TranslationCacheKey",
            "TranslationCancelledError",
            "TranslationMarkerCountError",
            "TranslationMarkerSizeError",
            "TranslationProvider",
            "TranslationProviderUnavailableError",
            "TranslationTimeoutError",
            "TranslationTotalSizeError",
            "TranslationUpstreamError",
            "normalize_prompt_translation_language",
            "normalize_prompt_translation_provider",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.translation.markers")
        ] = [
            "PROMPT_TRANSLATION_MARKER_LABEL",
            "has_prompt_translation_markers",
            "iter_prompt_translation_markers",
        ]
        expected_all[
            PACKAGE_MODULES.index(
                "easyuse_anima.translation.providers.google"
            )
        ] = ["GoogleTranslationProvider"]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.translation.service")
        ] = [
            "BoundedTranslationCache",
            "PromptTranslationService",
            "get_translation_provider",
            "google_translate_text",
            "strip_prompt_translation_markers",
            "translate_prompt_markers",
        ]
        expected_all[PACKAGE_MODULES.index("easyuse_anima.wildcard.expansion")] = [
            "COMMENT_RE",
            "DYNAMIC_RE",
            "WILDCARD_RE",
            "WILDCARD_FULL_RE",
            "WILDCARD_QUANTIFIER_RE",
            "COUNT_SPEC_RE",
            "has_wildcard_syntax",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.wildcard.mode")
        ] = [
            "WILDCARD_MODE_POPULATE",
            "WILDCARD_MODE_FIXED",
            "WILDCARD_MODE_SEQUENTIAL",
            "WILDCARD_MODE_REPRODUCE",
            "WILDCARD_MODES",
            "WILDCARD_MODE_LABELS",
            "PROMPT_STUDIO_WILDCARD_MODE_LABELS",
            "WILDCARD_MODE_ALIASES",
            "normalize_wildcard_mode",
            "normalize_prompt_studio_wildcard_mode",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.wildcard.models")
        ] = [
            "MAX_EXPANSION_DEPTH",
            "REPLACE_DEPTH",
            "DEFAULT_MAX_EXPANSION_DEPTH",
            "DEFAULT_MAX_EXPANSION_REPLACEMENTS",
            "DEFAULT_MAX_EXPANSION_OUTPUT_CHARS",
            "DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS",
            "MAX_EXPANSION_REPLACEMENTS",
            "MAX_EXPANSION_OUTPUT_CHARS",
            "MAX_EXPANSION_GROWTH_PER_PASS",
            "WildcardOption",
            "WildcardExpansionBudget",
            "WildcardExpansionResult",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.wildcard.seed")
        ] = [
            "SEED_CONTROL_FIXED",
            "SEED_CONTROL_RANDOMIZE",
            "SEED_CONTROL_INCREMENT",
            "SEED_CONTROL_DECREMENT",
            "SEED_CONTROL_MODES",
            "MAX_SEED",
            "PUBLIC_MAX_SEED",
            "normalize_seed",
            "next_seed",
        ]
        expected_all[
            PACKAGE_MODULES.index("easyuse_anima.wildcard.sources")
        ] = [
            "WILDCARD_DIR_NAME",
            "DEFAULT_TEST_WILDCARD_FILE",
            "DEFAULT_TEST_WILDCARD_TEXT",
            "WILDCARD_EXTENSIONS",
            "default_wildcard_root",
            "ensure_default_wildcard_root",
            "parse_wildcard_extra_paths",
            "resolve_wildcard_roots",
        ]
        self.assertEqual(payload["declared_all"], expected_all)
        self.assertEqual(payload["new_forbidden"], [])


if __name__ == "__main__":
    unittest.main()
