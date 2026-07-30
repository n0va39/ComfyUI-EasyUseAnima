# Python Runtime E-02 Completion Audit

## Status and authority

This is the production-free E-02 completion audit owned by
[Issue #187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187).
It follows the E-01 state inventory and the E-02b/E-02c runtime base contract.
The versioned ownership fixture remains the executable source of truth.

## Audited entries

### Filesystem runtime paths — E-02c complete

`easyuse_anima.infrastructure.filesystem.paths` still owns the import-stable
`PACKAGE_ROOT`, `PACKAGE_DATA_DIR`, and `USER_DATA_DIR` values. E-02c projects those
exact objects into the default `RuntimeConfig`; it does not duplicate resolution,
fallback, directory creation, or root alias behavior.

No further E-02 Move is required for this entry. Settings, profile, wildcard, and
autocomplete consumers migrate only with their feature owner.

### Autocomplete index root — E-05

`_AUTOCOMPLETE_INDEX_DIR` is not a base-runtime path by itself. Its effective
semantics include:

- package-fallback disables writable index publication;
- tests patch the root together with index availability and fallback behavior;
- per-path publication locks live in the autocomplete index owner; and
- dataset snapshots and single-flight state are also targeted at E-05.

Moving this value before E-05 would split one feature lifecycle across phases.
The ledger therefore assigns the index root to E-05 without changing production.

### Prompt knowledge path — E-02d complete

Before E-02d, `easyuse_anima.prompt.anima.knowledge.PACKAGE_DATA_DIR` was locally
resolved from the installed package location. The current built-in knowledge
implementation performs no file I/O with it, but the root ANIMA compatibility surface
and its direct test still preserve the value.

E-02d replaces the duplicate local resolution with the canonical filesystem
`PACKAGE_DATA_DIR` object. It preserves value/identity compatibility, direct imports,
root aliases, no-host import, and current knowledge behavior. It removes no symbol
and adds no RuntimeServices access.

## Decision

E-02 is complete through E-02d. The next bounded unit is an E-03 repository/filesystem
Contract; no E-03 production Move is authorized by this audit alone. No PRO review is
required: current owners, callers, and direct tests select one disposition for each
entry.
