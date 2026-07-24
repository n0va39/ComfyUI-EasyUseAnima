# D-12f2 Wildcard selector canonical Move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Prerequisite: D-12f1 selector import-timing Contract in PR #392 — complete
- Roadmap unit: D-12f2
- Parent roadmap unit: D-12 Wildcard
- PR type: Move
- Baseline: `dev@ced62e5969487da0494661e24e2032a089bc4831`
- State: READY
- Production behavior changes: forbidden

## Responsibility boundary

D-12f2 moves only `_Selector` to:

- `easyuse_anima.wildcard.selector`.

The canonical class owns per-request sequential or PCG64-backed selection.
Root `wildcard_engine.py` retains its eager `numpy as np` binding and all
selector callers, expansion functions, snapshot lifecycle, and integration.

The D-12f1 contract is authoritative: canonical selector direct import must
not load NumPy, while non-sequential construction acquires NumPy at call time.

## Symbol, caller, alias, and global-state inventory

Moved class:

- `_Selector(seed: int, sequential: bool)`.

Moved methods:

- `count_from_range`;
- `choose_one`; and
- `choose_many`.

Root callers retained:

- `expand_wildcard_texts`;
- `_select_count`;
- dynamic prompt selection;
- wildcard quantifier selection; and
- ordinary wildcard replacement.

Aliases:

- root `_Selector` becomes the identical canonical class object;
- canonical selector keeps an empty `__all__`; and
- root `np` remains the existing NumPy module binding.

Global state:

- no mutable global moves or additions;
- every non-sequential selector keeps its own generator;
- no cached NumPy module/provider, binder, lock, cache, singleton, reset, or
  cleanup is allowed.

## Compatibility invariants

- constructor signature, stored fields, method signatures, and return types are
  unchanged;
- `normalize_seed` remains the seed normalizer;
- sequential selectors keep `rng is None`;
- random selectors keep `Generator(PCG64(normalized_seed))`;
- range clamping, inclusive bounds, modulo ordering, empty/count handling,
  weight clamping, positive-pool filtering, all-zero fallback, probability
  normalization, no-replacement selection, and option order are unchanged;
- all existing fixed-seed golden expansion outputs remain identical;
- root eager NumPy import timing and `wildcard_engine.np` remain unchanged;
- canonical direct import adds no NumPy module;
- root/canonical class identity is exact; and
- mode, seed, source, snapshot, expansion, diagnostics, nodes, workflows, API,
  frontend, and Registry metadata are unchanged.

## Allowed-file boundary

Production:

- root `wildcard_engine.py`; and
- new `easyuse_anima/wildcard/selector.py`.

Supporting:

- selector identity/import-safety and existing wildcard golden tests;
- package skeleton, Registry scanner, backend analyzer, and exact fixture;
- this Move inventory, D-12f1 contract, shim ledger, and execution roadmap.

## Forbidden

- changing/removing root `numpy as np`;
- module-level NumPy import in canonical selector;
- selector algorithm, signatures, fields, weights, probabilities, ordering, or
  exception changes;
- caller cutover or expansion ownership changes;
- mode/seed/source/snapshot/lifecycle changes;
- adapter, node, workflow, frontend, API, bootstrap, Registry metadata,
  release, or instance changes;
- E-06 lifecycle/factory/cleanup work; and
- server, browser, live-instance, model, provider, or network execution.

## Validation and exit

- exact root/canonical `_Selector` identity;
- canonical direct import leaves NumPy unloaded;
- root import still exposes the same `np` module;
- sequential and PCG64 golden behavior remains unchanged;
- package skeleton declares selector's empty surface and retains
  `new_forbidden == []`;
- Registry scanner, backend analyzer, and packed archive include selector;
- canonical selector Ruff/Pyright have zero diagnostics;
- official full runs once at the PR checkpoint; and
- root retains all expansion/lifecycle/integration callers.
