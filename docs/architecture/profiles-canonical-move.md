# Profiles canonical package move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Prerequisite behavior owner:
  [#163](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/163) — complete
- Roadmap unit: D-10
- PR type: Move
- Baseline: `dev@01510e6d9c8a1e8b2b9d76e2306a85ea538fc84a`
- State: READY
- Behavior changes: forbidden

## Responsibility boundary

The root `api.py` still owns four profile implementation responsibilities that
are independent of HTTP transport:

1. shared filename validation, JSON reads, path discovery, and list metadata;
2. LoRA profile normalization, persistence, and repair against installed LoRAs;
3. AiO profile normalization, persistence, delete, and rename; and
4. profile directory, limit, reserved-name, and size-policy constants.

D-10 moves those responsibilities to:

- `easyuse_anima.profiles.repository`;
- `easyuse_anima.profiles.lora`; and
- `easyuse_anima.profiles.aio`.

The existing `contract.py` continues to own the v2 envelope and pure legacy
interpretation. The existing `mutation.py` continues to own CAS errors,
precondition verification, and the process-local directory coordinator.

`api.py` retains request parsing, `_run_file_io`, handler registration,
`_profile_error_response`, and response construction. It imports explicit
canonical aliases for the synchronous operations used by those handlers. This
is one behavior-preserving Profiles Move; it is not the later API route move.

## Symbol inventory

Shared repository candidates currently implemented in `api.py`:

- policy/state: `INVALID_PROFILE_NAME_CHARS`,
  `WINDOWS_RESERVED_FILE_BASENAMES`, and `InvalidProfileDataError`;
- filename helpers: `_windows_profile_filename_identity` and
  `_sanitize_profile_name`;
- persistence/list helpers: `_read_profile_json` and `_profile_list_item`.

AiO/LoRA path construction and discovery keep their existing feature-specific
bodies. The shared profile repository must not learn AiO settings fields or
LoRA payload schema.

LoRA profile candidates:

- policy/state: `LORA_PROFILE_DIR` and `MAX_LORA_PROFILES`;
- name/path: `_sanitize_lora_profile_name`, `_lora_profile_path`, and
  `_find_lora_profile_path`;
- normalization: `_as_lora_profile_count`, `_as_lora_profile_index`,
  `_normalize_lora_profile_data`, and `_normalize_lora_profile_payload`;
- persistence: `_list_lora_profiles`, `_save_lora_profile`, and
  `_load_lora_profile`;
- repair/capability lookup: `_clear_folder_paths_cache`, `_list_loras`,
  `_lora_full_path`, `_dedupe_text_values`, `_lora_file_key`, `_put_unique`,
  `_lora_path_exists`, `_build_lora_fix_index`, `_resolve_lora_for_fix`,
  `_apply_lora_fix`, and `_fix_lora_profile_payload`.

AiO profile candidates:

- policy/state: `AIO_PROFILE_DIR`, `MAX_AIO_PROFILES`,
  `MAX_AIO_PROFILE_BYTES`, and `AIO_RESERVED_PROFILE_NAMES`;
- name/path: `_sanitize_aio_profile_name`, `_aio_profile_path`, and
  `_find_aio_profile_path`;
- normalization: `_normalize_aio_profile_payload`,
  `_validate_aio_profile_size`, `_normalize_stored_aio_profile_payload`, and
  `_rename_aio_profile_payload`;
- persistence: `_list_aio_profiles`, `_save_aio_profile`,
  `_load_aio_profile`, `_delete_aio_profile`, and `_rename_aio_profile`.

The root `api.py` aliases used by its handlers remain identical to the
canonical functions and classes. Private helpers that are not route
dependencies are tested at their canonical owner and are not promoted into a
new public API.

## Caller and alias inventory

Production callers:

- `api.py` is the only production caller of the profile persistence,
  normalization, and repair operations;
- profile route handlers call the synchronous aliases through the existing
  bounded `_run_file_io` adapter;
- `_profile_error_response` consumes `InvalidProfileDataError` and
  `ProfileMutationError`;
- `_SAFE_PROFILE_VALIDATION_MESSAGES` consumes `MAX_AIO_PROFILES`; and
- LoRA preview resolution is a separate API surface and remains in `api.py`.

Existing package-internal ownership:

- `easyuse_anima.profiles.contract` owns envelope constants, identity,
  migration interpretation, create/update, and rename document composition;
- `easyuse_anima.profiles.mutation` owns strict preconditions, conflict
  taxonomy, and `PROFILE_MUTATION_COORDINATOR`.

Test callers:

- `tests/test_aio_profiles.py` and `tests/test_lora_profiles.py` exercise the
  current root private seams and patch directory/size policy aliases;
- route-level tests patch the operation aliases in `api.py`;
- `tests/test_profile_contract.py` already tests `contract.py` and
  `mutation.py` directly; and
- analyzer, package skeleton, scanner, and archive tests record the current
  import/package closure.

Focused behavior tests move directory, size, normalization, persistence, and
repair patches to the canonical owner. Route tests keep patching the
`api.py` operation alias because that is the HTTP adapter seam.

## Global state and lifecycle inventory

- `LORA_PROFILE_DIR` and `AIO_PROFILE_DIR` remain import-time path snapshots
  derived from canonical `USER_DATA_DIR`.
- `AIO_RESERVED_PROFILE_NAMES` and `WINDOWS_RESERVED_FILE_BASENAMES` retain
  their current set contents and mutability. D-10 does not freeze or copy them
  at call time.
- `INVALID_PROFILE_NAME_CHARS` remains one compiled regular expression.
- `PROFILE_MUTATION_COORDINATOR` remains the single module-owned,
  process-local lock coordinator in `mutation.py`.
- Every read/write/delete/replace continues to construct `AtomicJsonStore` at
  the same operation boundary.
- `folder_paths` remains a call-time optional import used only by LoRA repair;
  D-10 introduces no import-time Comfy lookup or cache mutation.
- `_run_file_io`, its per-event-loop limiter, and request cancellation
  behavior remain owned by `api.py`.
- No new cache, executor, initialize, shutdown, migration, or cleanup owner is
  introduced. Those belong to the E-series lifecycle work.

## Behavior constraints

- Preserve exact filename sanitization, truncation, Windows reserved-name and
  case-insensitive identity behavior.
- Preserve profile paths, directory defaults, sort order, list metadata,
  maximum counts/bytes, reserved AiO names, and validation messages.
- Preserve the v1/v2 read view, no-write-on-read migration, UUID/revision
  creation, overwrite/delete/rename CAS order, lock boundary, backup behavior,
  return payloads, and exception taxonomy.
- Preserve LoRA payload normalization and repair lookup/cache-clearing order.
- Preserve route URLs, request fields, HTTP status/code/message/details,
  response shapes, file-I/O limiter, and cancellation behavior.
- Package import must not create directories/files, read profile data, inspect
  installed LoRAs, mutate cache, or register routes.

## Allowed-file boundary

Production:

- profile implementation/import lines in root `api.py`;
- `easyuse_anima/profiles/__init__.py`;
- new `easyuse_anima/profiles/repository.py`;
- new `easyuse_anima/profiles/lora.py`; and
- new `easyuse_anima/profiles/aio.py`.

Supporting:

- profile focused tests and API adapter tests where canonical patch ownership
  changes;
- Python package skeleton, import-boundary, backend analyzer, Registry scanner,
  compatibility surface, and their exact fixtures;
- `docs/architecture/python-compatibility-shims.md` if the recorded alias
  surface changes;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

## Forbidden changes

- profile schema, migration, normalization, validation, collision, CAS,
  persistence, lock, backup, path, API payload, error, or response behavior;
- HTTP route extraction or composition, async/file-I/O policy, frontend,
  workflow, node, settings, autocomplete, wildcard, prompt, translation,
  dependency, Registry metadata, release, or instance behavior;
- cache/singleton/repository factory, runtime-service ownership, background
  cleanup, server, browser, or live-instance work; and
- D-11, D-12, D-13, D-02 through D-07, or E-series behavior/lifecycle work.

## Validation and exit

- focused AiO/LoRA profile behavior and API adapter tests;
- canonical/root operation identity and canonical global patch ownership;
- exact legacy/v2, Windows path/case, collision, size, corruption, atomic
  recovery, concurrent CAS, rename/delete, and LoRA repair fixtures;
- package skeleton, import boundary, backend analyzer, Registry scanner, and
  actual packed-archive closure;
- official full runner once at the PR checkpoint; and
- `api.py` contains only explicit profile aliases plus HTTP adapter behavior,
  while profile implementation resides under `easyuse_anima/profiles/`.
