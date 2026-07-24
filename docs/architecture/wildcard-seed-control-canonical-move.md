# D-12d Wildcard seed-control canonical Move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Behavior prerequisites:
  [#159](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/159) and
  [#160](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/160) — complete
- Roadmap unit: D-12d
- Parent roadmap unit: D-12 Wildcard
- PR type: Move
- Baseline: `dev@e9adbe30ec8f7fdf251c515679b142942979f924`
- State: READY
- Production behavior changes: forbidden

## Responsibility boundary

D-12d moves only the wildcard seed-control leaf to:

- `easyuse_anima.wildcard.seed`.

The leaf defines the accepted backend seed domain, browser-safe next-seed
domain, after-generate control values, seed normalization, and next-seed
transition. It does not choose wildcard options or expand text.

Wildcard mode normalization, `_Selector`, NumPy/PCG64 ownership, parsing,
snapshot lifecycle, expansion, node adapters, and browser reservation
compatibility remain in their current owners. This avoids coupling the seed
Move to the package skeleton's no-eager-NumPy gate or to Behavior work.

## Supported moved surface

Seed-control constants:

- `SEED_CONTROL_FIXED`;
- `SEED_CONTROL_RANDOMIZE`;
- `SEED_CONTROL_INCREMENT`;
- `SEED_CONTROL_DECREMENT`; and
- `SEED_CONTROL_MODES`.

Seed ranges:

- `MAX_SEED`; and
- `PUBLIC_MAX_SEED`.

Functions:

- `normalize_seed`; and
- `next_seed`.

Root `wildcard_engine.py` binds every moved supported name directly to the
identical canonical object. No wrapper, proxy, duplicate constant, `import *`,
or lazy module hook is allowed.

## Caller and alias inventory

Root runtime callers:

- `_Selector.__init__` normalizes its execution seed;
- `expand_wildcard_texts` normalizes the requested seed before selector
  creation; and
- root public and compatibility consumers import seed names from
  `wildcard_engine`.

Production consumers through root:

- root `nodes.py` explicit compatibility imports;
- `easyuse_anima.nodes.wildcard_nodes`;
- Prompt Studio node adapters and their call-time root wrappers;
- `easyuse_anima.seed.compatibility` reservation validation; and
- existing workflow/node input definitions.

D-12d does not cut these callers over. Root direct aliases preserve their
identity and behavior while later D-12 slices decide mode, selector, and final
consumer ownership together.

Tests:

- wildcard seed contract tests keep range, legacy uint64, fixed, randomize,
  increment, and decrement behavior;
- the `SystemRandom` patch moves from root to canonical seed ownership;
- exact root/canonical identity is added; and
- package skeleton, Registry scanner, and backend analyzer include the
  canonical module.

## Global-state inventory

D-12d moves no mutable runtime state.

Canonical seed contains only:

- immutable strings;
- an immutable control tuple;
- immutable integer range constants;
- stateless normalization/transition functions; and
- the standard-library `random` module binding used only by `next_seed`.

It creates no mutable container, cache, lock, condition, singleton, selector,
PRNG instance, background task, factory, or cleanup hook. `SystemRandom` is
instantiated per randomize call exactly as before.

Root retains:

- wildcard mode constants and mutable alias lookup;
- `_Selector` and NumPy/PCG64 construction;
- snapshot/cache lifecycle;
- expansion state and lanes; and
- all node/workflow integration.

## Compatibility and behavior invariants

- `normalize_seed` still coerces through `int`, maps `TypeError`/`ValueError`
  to zero, clamps below zero to zero, and clamps above uint64 max;
- existing uint64 workflow seeds remain accepted by Python;
- fixed preserves the normalized current seed, including values above the
  JavaScript-safe range;
- randomize creates a fresh `SystemRandom` and samples the inclusive
  `0..PUBLIC_MAX_SEED` domain;
- increment and decrement first project legacy values into the public domain,
  then preserve existing wrap behavior;
- unknown controls return the normalized current seed;
- control values, tuple order, range values, function signatures, return
  types, and exception behavior are unchanged;
- root import identity and node/workflow serialization behavior are unchanged;
- wildcard mode, selector/PCG64, expansion, snapshot, diagnostics, API, nodes,
  frontend, and reservation behavior are unchanged; and
- canonical seed imports no root module and no NumPy.

## Allowed-file boundary

Production:

- root `wildcard_engine.py`; and
- new `easyuse_anima/wildcard/seed.py`.

Supporting:

- wildcard seed identity/behavior tests;
- package skeleton, Registry scanner, backend analyzer, and exact fixture;
- this inventory, compatibility-shim ledger, and execution roadmap.

## Forbidden

- wildcard mode constants, labels, aliases, or normalization changes;
- `_Selector` or NumPy/PCG64 movement/import-timing changes;
- seed reservation, adapter, node, workflow, or frontend caller cutover;
- random algorithm, domain, timing, or control behavior changes;
- source, snapshot, cache, expansion, budget, or diagnostics changes;
- G-03 completed-package enrollment before full D-12 completion;
- API, bootstrap, Registry metadata, release, or instance changes; and
- server, browser, live-instance, model, provider, or network execution.

## Validation and exit

- exact root/canonical identity for all nine moved supported names;
- existing seed normalization and transition tests remain unchanged;
- canonical `SystemRandom` patch proves the randomize range without real
  entropy dependence;
- package skeleton, Registry scanner, backend analyzer, and packed archive
  include canonical `seed.py`;
- canonical seed has zero root/NumPy imports and no mutable globals;
- official full runner once at the PR checkpoint; and
- root retains wildcard mode, selector, expansion, and integration callers.
