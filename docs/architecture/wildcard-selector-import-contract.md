# D-12f1 Wildcard selector import-timing Contract

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Behavior prerequisites:
  [#159](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/159) and
  [#160](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/160) — complete
- Roadmap unit: D-12f1
- Parent roadmap unit: D-12 Wildcard
- Follow-up Move: D-12f2
- PR type: Contract/docs/gate
- Baseline: `dev@f5184d3a1fc1c7bc860c914efbfb136dcec7095e`
- State: READY
- Production behavior changes: forbidden

## Why a Contract precedes the Move

Root `wildcard_engine.py` currently imports NumPy eagerly and owns `_Selector`.
The canonical package skeleton, however, requires every directly imported
`easyuse_anima.*` module to avoid introducing NumPy into `sys.modules`.

Moving the class with its module-level `import numpy as np` would weaken that
gate. Moving it while also changing dependency timing without a frozen
contract would mix an import-boundary decision into a Move. D-12f1 therefore
defines the supported boundary first and changes no production file.

## Selector symbol inventory

D-12f2 may move exactly one class:

- `_Selector`.

Constructor contract:

- signature remains `(seed: int, sequential: bool)`;
- `seed` is normalized through canonical wildcard seed ownership;
- `sequential` is stored unchanged; and
- `rng` is `None` for sequential selection or a NumPy
  `Generator(PCG64(normalized_seed))` for random selection.

Method contract:

- `count_from_range(minimum, maximum)`;
- `choose_one(options)`; and
- `choose_many(options, count)`.

The class remains private. Canonical `selector.py` has an empty `__all__`, and
root retains `_Selector` as the identical class object.

## Caller and alias inventory

Root callers:

- `expand_wildcard_texts` constructs one selector for an expansion request;
- `_select_count` calls `count_from_range`;
- dynamic prompt expansion calls `choose_many`;
- wildcard quantifier expansion calls `choose_many`; and
- wildcard replacement calls `choose_one`.

Tests:

- sequential mode observes `rng is None` and seed-modulo ordering;
- random mode observes a PCG64 bit generator;
- fixed-seed golden cases cover ordinary, weighted, multiselect, and combined
  expansion; and
- D-12f2 adds exact root/canonical class identity and direct-import safety.

No production caller is cut over in D-12f2. Root callers continue resolving
the root `_Selector` name, which becomes a direct canonical alias.

## NumPy import-timing contract

Supported root behavior:

- root `wildcard_engine.py` continues importing `numpy as np` at module load;
- root keeps the existing `wildcard_engine.np` binding during D-12f2; and
- importing root therefore has exactly the same eager NumPy timing as before.

Canonical package behavior:

- importing `easyuse_anima.wildcard.selector` must not import NumPy;
- constructing a non-sequential `_Selector` may acquire NumPy at call time;
- that acquisition must still create `Generator(PCG64(normalized_seed))`;
- sequential construction must not create a generator; and
- no stdlib RNG fallback or alternate bit generator is permitted.

The package skeleton remains strict: `numpy` stays in `forbidden_roots`, and
the new selector module must be enrolled with an empty declared surface.

## Global-state inventory

D-12f1 authorizes no mutable global state.

D-12f2 canonical selector may own only:

- the `_Selector` class definition;
- imported immutable/type references; and
- call-local NumPy acquisition used for generator construction.

It must not add a cached NumPy module, provider registry, mutable dependency
slot, PRNG singleton, lock, condition, cache, task, factory, binder, reset, or
cleanup hook. Each non-sequential selector owns its own generator exactly as
before.

Root retains:

- its existing `np` module binding;
- snapshot/cache lifecycle;
- mode and seed direct aliases;
- expansion functions and per-request selector construction; and
- all node/workflow integration.

## Compatibility and behavior invariants

- normalized seed domain and stored `seed` are unchanged;
- sequential range and option selection remain seed-modulo based;
- sequential multi-selection remains ordered, wrapping, and without duplicate
  indices until the requested count reaches the option count;
- random range bounds remain inclusive;
- non-positive counts and empty options still return an empty list;
- negative weights still clamp to zero;
- a positive-weight pool still excludes zero-weight entries;
- an all-zero pool still falls back to unweighted selection;
- random multiselect remains without replacement;
- NumPy probability normalization, draw order, and returned option order remain
  unchanged;
- root/canonical class identity is exact;
- root import timing and `wildcard_engine.np` remain unchanged; and
- source, snapshot, mode, seed, expansion, diagnostics, nodes, workflows, API,
  frontend, and Registry metadata remain unchanged.

## D-12f2 allowed-file boundary

Production:

- root `wildcard_engine.py`; and
- new `easyuse_anima/wildcard/selector.py`.

Supporting:

- selector identity/import-safety and existing wildcard golden tests;
- package skeleton, Registry scanner, backend analyzer, and exact fixture;
- this contract, compatibility-shim ledger, and execution roadmap.

## Forbidden

- changing/removing root `numpy as np` in D-12f2;
- module-level NumPy import in canonical selector;
- cached dependency/provider/binder state;
- selector signature, field, algorithm, weight, probability, count, ordering,
  or exception changes;
- mode/seed/source/snapshot/expansion ownership changes;
- expansion consumer cutover or adapter/node/frontend changes;
- E-06 lifecycle/factory/cleanup work;
- G-03 completed-package enrollment before full D-12 completion;
- API, bootstrap, Registry metadata, release, or instance changes; and
- server, browser, live-instance, model, provider, or network execution.

## Contract exit

- symbol/caller/alias/global-state inventory is reviewed;
- root eager-NumPy and canonical no-eager-NumPy surfaces are both explicit;
- D-12f2 Move boundary and forbidden changes are exact;
- existing PCG64 golden behavior remains the acceptance source; and
- this docs-only Contract merges before D-12f2 production work starts.
