# Filesystem canonical package move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Prerequisite behavior owner:
  [#163](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/163) — complete
- Roadmap unit: D-08
- PR type: Move
- Baseline: `dev@98e2ddd5681873e9899c5ce47b2943036350f725`
- State: VALIDATED in PR #382
- Behavior changes: forbidden

## Responsibility boundary

The root `storage.py` currently combines two filesystem responsibilities:

1. package/user data path discovery; and
2. durable atomic JSON storage, backup recovery, shared path locks, replace,
   rollback, and directory durability helpers.

D-08 moves those responsibilities to
`easyuse_anima.infrastructure.filesystem.paths` and
`easyuse_anima.infrastructure.filesystem.atomic_json`. The root module remains
an explicit direct re-export shim. This is one behavior-preserving Move, not a
path, persistence, recovery, migration, locking, or lifecycle change.

## Symbol inventory

Supported root compatibility symbols are the module-owned public constants and
class:

- `PACKAGE_ROOT`;
- `PACKAGE_DATA_DIR`;
- `SYSTEM_USER_NAME`;
- `USER_DATA_DIR`; and
- `AtomicJsonStore`.

The root shim must list these names explicitly in `__all__` and bind each name
as the identical canonical object. It must not wrap, proxy, subclass, or use
`import *`.

Unsupported private/test-only seams are `_resolve_user_data_dir`, `_T`,
`_MISSING`, `_PATH_LOCKS`, `_PATH_LOCKS_GUARD`, `_RECOVERABLE_READ_ERRORS`,
`_UNSUPPORTED_DIRECTORY_FSYNC_ERRORS`, `_resolved_path`, `_path_lock_key`,
`_path_lock`, `_locked_paths`, `_fsync_directory`, and
`_unlink_if_present`. Canonical tests may patch the owning canonical module;
these private names and imported `os`/`tempfile` modules are not added to the
root compatibility surface.

## Caller and alias inventory

Production consumers:

- `api.py`: `AtomicJsonStore` and `USER_DATA_DIR`;
- `settings.py`: `AtomicJsonStore` and `USER_DATA_DIR`;
- `autocomplete_dataset.py`: `PACKAGE_DATA_DIR` and `USER_DATA_DIR`; and
- `wildcard_engine.py`: `USER_DATA_DIR`.

D-08 changes only those storage import lines to precise canonical modules.
Root compatibility imports remain for external/legacy consumers and direct
identity tests.

Test consumers:

- `tests/test_storage.py` currently imports and patches root implementation
  globals. It becomes the canonical paths/store behavior test with a separate
  root/canonical identity assertion.
- package, analyzer, import-boundary, and Registry scanner fixtures must
  reflect the new shipped modules and public shim entrypoint.

## Global state and lifecycle inventory

- `USER_DATA_DIR` remains one import-time path snapshot derived from the same
  `folder_paths` probes and package fallback.
- `_PATH_LOCKS` and `_PATH_LOCKS_GUARD` remain process-local state owned by the
  atomic JSON module.
- Stores for the same normalized path continue sharing one reentrant lock.
- No lock eviction, initialization, shutdown, repository factory, or runtime
  ownership policy is introduced in this Move; those remain E-03 follow-ups.

## Path and behavior constraints

- Canonical `PACKAGE_ROOT` must still resolve to the custom-node repository
  root, not the new filesystem package directory.
- `PACKAGE_DATA_DIR`, system/user directory probing, Windows case folding,
  same-directory backup validation, temp placement, flush/fsync order,
  publication order, rollback order, exceptions, JSON encoding, and return
  values must remain unchanged.
- The generic filesystem package must not learn setting keys, profile schemas,
  migration rules, API payloads, wildcard syntax, or autocomplete behavior.

## Allowed-file boundary

Production:

- `storage.py`;
- new modules under `easyuse_anima/infrastructure/filesystem/`;
- `api.py`, `settings.py`, `autocomplete_dataset.py`, and
  `wildcard_engine.py`, storage import lines only.

Supporting:

- storage focused/identity tests;
- Python package skeleton, import-boundary, backend analyzer, Registry scanner,
  and their exact fixtures;
- `docs/architecture/python-compatibility-shims.md`;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

## Forbidden changes

- path selection, directory names, case normalization, lock identity/order,
  backup/read recovery, temp/fsync/replace/delete/rollback semantics, JSON
  format, error types/messages, or public return values;
- settings/profile migration or normalization, API routes, wildcard,
  autocomplete, workflow, frontend, dependency, Registry metadata, release,
  or instance files;
- schema-aware filesystem helpers, new background cleanup, lock eviction,
  server, browser, or live instance work; and
- D-09, D-10, or E-03 behavior/lifecycle work.

## Validation and exit

- focused storage behavior and root/canonical identity tests;
- Windows/case-folding, recovery, rollback, concurrent path-lock, and
  path-probe fixtures remain unchanged;
- package skeleton, import boundary, backend analyzer, Registry scanner, and
  actual packed-archive closure;
- official full runner at the PR checkpoint; and
- root `storage.py` contains only explicit direct re-exports while all
  production storage imports use canonical modules.

Validation evidence:

- `tests.test_storage`: 20 tests passed, including root/canonical identity,
  path probing, recovery, rollback, and shared path-lock behavior;
- package skeleton, import-boundary, backend-analyzer, and Registry-scanner
  focused suites: 43 tests passed;
- focused Pyright for both canonical filesystem modules: 0 diagnostics;
- official `full`: 1,130 Python tests and 112 frontend files passed;
- `comfy node validate`: passed;
- `comfy node pack`: produced a 244-entry archive containing `storage.py` and
  all three `easyuse_anima/infrastructure/filesystem/` modules; and
- no server, browser, model, provider, workflow, or live-instance smoke was
  run because D-08 changes only Python import ownership and packaging.
