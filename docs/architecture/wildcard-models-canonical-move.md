# D-12a Wildcard models canonical Move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Behavior prerequisites:
  [#159](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/159) and
  [#160](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/160) — complete
- Roadmap unit: D-12a
- Parent roadmap unit: D-12 Wildcard
- PR type: Move
- Baseline: `dev@7fdee04d4102a1273025624f57e955b3295e4a8a`
- State: VALIDATED in PR #387
- Production behavior changes: forbidden

## Responsibility boundary

Root `wildcard_engine.py` combines immutable public models, source discovery and
snapshot state, selector/PRNG logic, and expansion orchestration. Moving the
whole module would mix the D-12 Move with E-06 snapshot lifecycle ownership and
make review of the seed/expansion behavior contract unnecessarily broad.

D-12a moves only the dependency-free immutable model leaf to:

- `easyuse_anima.wildcard.models`.

Source scanning, snapshot publication, filesystem paths, YAML loading, selector
state, seeded choice, seed control, parsing, expansion, limits enforcement, and
diagnostics production remain in root for later D-12 slices.

## Supported moved surface

Budget constants:

- `MAX_EXPANSION_DEPTH`;
- `REPLACE_DEPTH`;
- `DEFAULT_MAX_EXPANSION_DEPTH`;
- `DEFAULT_MAX_EXPANSION_REPLACEMENTS`;
- `DEFAULT_MAX_EXPANSION_OUTPUT_CHARS`;
- `DEFAULT_MAX_EXPANSION_GROWTH_PER_PASS`;
- `MAX_EXPANSION_REPLACEMENTS`;
- `MAX_EXPANSION_OUTPUT_CHARS`; and
- `MAX_EXPANSION_GROWTH_PER_PASS`.

Immutable models:

- `WildcardOption`;
- `WildcardExpansionBudget`; and
- `WildcardExpansionResult`.

Root binds every moved supported name directly to the identical canonical
object. No wrapper, proxy, subclass, duplicate constant, `import *`, or lazy
module hook is allowed.

## Private symbol inventory

The canonical model owner also takes the model-only coercion helpers:

- `_bounded_int`; and
- `_bounded_float`.

They are private implementation details of `WildcardExpansionBudget` and are
not added to the root compatibility surface.

## Caller and alias inventory

Production:

- root `wildcard_engine.py` continues using every model and constant while
  owning source/snapshot/expansion behavior;
- no canonical package module currently imports these model names directly;
  later D-12 source/snapshot/expansion slices will do so; and
- node/API/bootstrap imports of root source, expansion, and seed helpers remain
  unchanged in this slice.

Tests:

- `tests/test_wildcards.py` retains root behavior imports, adds exact
  root/canonical identity coverage, and may use the canonical model owner for
  private model construction;
- package skeleton and Registry scanner gain the wildcard package and model
  module; and
- backend analyzer fixtures enroll both shipped/runtime modules without
  declaring D-12 package completion in G-03.

Aliases:

- `REPLACE_DEPTH is MAX_EXPANSION_DEPTH` remains a value alias;
- root model class objects are direct canonical aliases; and
- there are no compatibility aliases for `_bounded_int` or `_bounded_float`.

## Global-state inventory

D-12a moves no mutable global state.

The following remain root-owned and unchanged:

- `_SNAPSHOT_CONDITION`;
- `_SNAPSHOT_CACHE`;
- `_SNAPSHOT_BUILDING`;
- `_SNAPSHOT_CACHE_LIMIT`; and
- all selector, library, expansion-lane, and per-call expansion state.

Their owner/lifetime/lock/cleanup migration belongs to later D-12 slices and
E-06. D-12a creates no singleton, lock, cache, background task, cleanup hook,
factory, or dependency-injection seam.

## Compatibility and behavior invariants

- dataclass frozen state, field order, defaults, equality, repr, and accepted
  constructor inputs are unchanged;
- budget coercion, invalid-number fallback, finite-float policy, min/max
  clamping, and hard ceilings are unchanged;
- result tuple defaults and `limit_reason` semantics are unchanged;
- wildcard option text/weight defaults are unchanged;
- seed, selection, PCG64, source, snapshot, YAML, path, ordering, expansion,
  output, diagnostics, and exception behavior are unchanged; and
- no Node, workflow, API, frontend, or Registry metadata behavior changes.

## Allowed-file boundary

Production:

- root `wildcard_engine.py`;
- new `easyuse_anima/wildcard/__init__.py`; and
- new `easyuse_anima/wildcard/models.py`.

Supporting:

- wildcard identity/model tests;
- package skeleton, Registry scanner, backend analyzer, and exact fixture;
- this inventory, compatibility-shim ledger, and execution roadmap.

## Forbidden

- source/path scanning, YAML loading, snapshot/cache/lock/lifecycle changes;
- selector, PRNG, seed, mode, parsing, expansion, budget enforcement, or
  diagnostics behavior changes;
- moving source/snapshot/expansion helpers in this PR;
- G-03 completed-package enrollment before the full D-12 package is canonical;
- node, API, bootstrap, frontend, workflow, Registry metadata, release, or
  instance changes; and
- server, browser, live-instance, model, provider, or network execution.

## Validation and exit

- exact root/canonical identity for every moved supported name;
- model defaults, coercion, clamping, frozen state, and result fields;
- wildcard behavior suite remains unchanged;
- package skeleton, Registry scanner, backend analyzer, and packed archive
  include the root shim path and both canonical wildcard modules;
- canonical model module has zero root imports;
- official full runner once at the PR checkpoint; and
- root retains all source/snapshot/selector/seed/expansion implementation.

Validation evidence:

- wildcard behavior and root/canonical identity: 72 tests passed;
- package skeleton: 1 test passed;
- Registry scanner: 8 tests passed;
- backend analyzer: 18 tests passed, 127 shipped/runtime modules and zero
  unreachable modules;
- G-03 import boundary: 16 tests passed;
- canonical model Pyright diagnostics: 0;
- official full: 1,135 Python tests and 112 frontend files passed; G-03 kept
  10 completed package groups with zero violations and the existing Pyright
  baseline remained 14 errors; and
- `comfy node validate` passed; `comfy node pack` produced 257 entries and
  included root `wildcard_engine.py` plus canonical wildcard `__init__.py` and
  `models.py`.
