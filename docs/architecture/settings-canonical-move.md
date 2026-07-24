# Settings canonical package move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Prerequisite behavior owner:
  [#163](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/163) — complete
- Roadmap unit: D-09
- PR type: Move
- Baseline: `dev@47941ff61053a07a1aba8f0264f86b2b8127d3bf`
- State: VALIDATED in PR #383
- Behavior changes: forbidden

## Responsibility boundary

The root `settings.py` contains three cohesive settings responsibilities:

1. setting defaults, accepted values, key maps, and long-text aliases;
2. file-backed settings/long-text reads and writes plus Comfy settings overlay;
3. public settings projection and feature-specific value resolvers.

D-09 moves those responsibilities to:

- `easyuse_anima.settings.schema`;
- `easyuse_anima.settings.repository`; and
- `easyuse_anima.settings.service`.

The root module becomes an explicit direct re-export shim. This is one
behavior-preserving settings Move. It does not introduce a new schema,
migration, cache, repository lifetime, validation rule, or error policy.

## Symbol inventory

Supported module-owned root constants:

- repository paths: `SETTINGS_FILE`, `LONG_TEXT_SETTINGS_FILE`;
- schema/defaults: `DEFAULT_SETTINGS`, `AUTOCOMPLETE_MODES`,
  `AUTOCOMPLETE_COMMIT_KEYS`, `NAIA_RESOLUTION_MODES`,
  `NAIA_RESOLUTION_BUCKETS`, `NAIA_PREPROCESSING_KEYS`,
  `PROMPT_STUDIO_COLOR_KEYS`, `COMFY_SETTING_KEYS`,
  `COMFY_COLOR_SETTING_KEYS`, `LONG_TEXT_SETTING_KEYS`, and
  `LONG_TEXT_SETTING_ALIASES`.

Supported module-owned root functions:

- repository: `load_long_text_settings`, `save_long_text_settings`,
  `get_settings`, and `save_setting`;
- service: `public_settings`, `resolve_metadata_filter_words`,
  `resolve_autocomplete_source`, `resolve_autocomplete_limit`,
  `resolve_autocomplete_mode`, `resolve_autocomplete_commit_key`,
  `resolve_lora_preset_strength_button_step`,
  `resolve_lora_preset_strength_drag_step`,
  `resolve_lora_preset_strength_drag_pixels`,
  `resolve_lora_preset_menu_mode`, `resolve_prompt_studio_font_family`,
  `resolve_prompt_studio_font_size`, `resolve_prompt_translation_provider`,
  `resolve_prompt_translation_source`, `resolve_prompt_translation_target`,
  `resolve_prompt_translation_settings`, `resolve_naia_port`,
  `resolve_naia_resolution_mode`, `resolve_naia_resolution_bucket`,
  `resolve_naia_resolution_scale`, `resolve_naia_resolution_max_long_edge`,
  and `resolve_naia_settings`.

The root shim must list these 39 names explicitly in `__all__` and bind each
as the identical canonical object. It must not wrap, proxy, use `import *`, or
re-export imported filesystem/translation dependencies.

Unsupported private/test-only seams are `_read_json_file`,
`_normalize_long_text_settings`, `_comfy_settings_candidates`,
`_load_comfy_settings`, `_stringify_setting_value`,
`_apply_prompt_studio_color_settings`, `_apply_comfy_settings`,
`_apply_long_text_settings`, `_resolve_lora_preset_strength_step`, and
`_resolve_settings_bool`. Tests may patch their new canonical owner; D-09 does
not promote them into the root compatibility surface.

## Caller and alias inventory

Production root consumers:

- `api.py`: repository load/save functions plus public/autocomplete/translation
  services;
- `nodes.py`: three resolver compatibility aliases;
- `wildcard_engine.py`: `get_settings`.

Canonical package consumers:

- `easyuse_anima.nodes.naia_nodes`;
- `easyuse_anima.nodes.prompt_advanced_nodes`;
- `easyuse_anima.nodes.prompt_nodes`;
- `easyuse_anima.nodes.regional_nodes`;
- `easyuse_anima.prompt.advanced`;
- `easyuse_anima.prompt.correction`; and
- `easyuse_anima.prompt.regional`.

These callers move only their settings import lines to precise canonical
owners. The package consumers no longer fall back through the root settings
shim.

`tests/test_prompt_corrector.py` imports the root module and supported symbols,
and patches repository-owned path/I/O seams. It becomes the canonical
repository/service behavior test with a separate root/canonical identity
assertion. `tests/test_wildcards.py` imports `public_settings` and moves to the
canonical service.

## Global state and lifecycle inventory

- `SETTINGS_FILE` and `LONG_TEXT_SETTINGS_FILE` remain import-time path
  snapshots derived from the D-08 canonical `USER_DATA_DIR`.
- The 11 schema containers remain single module-owned `dict`, `set`, or `list`
  objects. D-09 does not freeze, copy, reorder, or mutate their contents.
- No repository/store singleton exists. Each operation constructs the same
  `AtomicJsonStore` at call time.
- Comfy settings candidate discovery remains call-time and probes the same two
  files in the same order.
- Atomic path locks and durability remain owned by the D-08 filesystem package.
  D-09 introduces no cache, lock, initialization, or shutdown lifecycle.

## Behavior constraints

- Preserve the exact default keys/values and public projection.
- Preserve long-text aliases, precedence, normalization, versioned output,
  sort order, and return values.
- Preserve Comfy settings candidate order, aggregate/per-color precedence, and
  string conversion.
- Preserve settings read/write lock boundary, file paths, trailing newline,
  exceptions, clamping, accepted modes/buckets, and NAIA/translation results.
- Package import must not create files, load settings data, or register routes.

## Allowed-file boundary

Production:

- root `settings.py`;
- new modules under `easyuse_anima/settings/`;
- settings import lines only in the production callers listed above.

Supporting:

- settings focused/identity tests and wildcard settings import;
- Python package skeleton, import-boundary, backend analyzer, Registry scanner,
  and their exact fixtures;
- root compatibility-surface and `nodes.py` analyzer exact fixtures changed
  only by canonical settings import ownership;
- `docs/architecture/python-compatibility-shims.md`;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

## Forbidden changes

- setting keys/defaults, schema, migration, normalization, precedence, file
  paths, persistence, lock, error, API payload, or return behavior;
- profile, wildcard, autocomplete, prompt, NAIA, translation, frontend,
  dependency, Registry metadata, release, or instance behavior;
- cache/singleton/repository factory, runtime service ownership, background
  cleanup, server, browser, or live-instance work; and
- D-10, D-11, D-12, or E-series behavior/lifecycle work.

## Validation and exit

- focused settings repository/service behavior and root/canonical identity;
- existing round-trip, long-text, Comfy overlay, concurrent update, resolver,
  clamp, alias, failure, and wildcard-settings fixtures;
- package skeleton, import boundary, backend analyzer, Registry scanner, and
  actual packed-archive closure;
- official full runner at the PR checkpoint; and
- root `settings.py` contains only explicit direct re-exports while all
  production settings imports use canonical owners.

Validation evidence:

- `SettingsTests`: 23 tests passed, including root/canonical identity,
  round-trip, long-text, Comfy overlay, concurrent updates, resolvers, clamps,
  aliases, and failure handling;
- package skeleton, import-boundary, backend-analyzer, and Registry-scanner
  focused suites: 33 tests passed;
- `nodes.py` analyzer and machine-readable compatibility surface: 30 tests
  passed with three bindings moved from legacy to canonical ownership;
- focused Pyright for all three canonical settings owners: 0 diagnostics;
- old/new AST comparison found no missing or extra functions/constants and no
  function-body delta except the behavior-neutral Comfy path return cast;
- official `full`: 1,131 Python tests and 112 frontend files passed;
- `comfy node validate`: passed;
- `comfy node pack`: produced a 248-entry archive containing root `settings.py`
  and all four `easyuse_anima/settings/` files; and
- no server, browser, model, provider, workflow, or live-instance smoke was
  run because D-09 changes only Python import ownership and packaging.
