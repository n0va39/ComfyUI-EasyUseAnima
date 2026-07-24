# D-12e Wildcard mode contract canonical Move

- Owner issue: [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Behavior prerequisites:
  [#159](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/159) and
  [#160](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/160) — complete
- Roadmap unit: D-12e
- Parent roadmap unit: D-12 Wildcard
- PR type: Move
- Baseline: `dev@9ecbe3543d02461ff8984eb092ccd12c02b2badb`
- State: VALIDATED
- Production behavior changes: forbidden

## Responsibility boundary

D-12e moves only the wildcard mode contract to:

- `easyuse_anima.wildcard.mode`.

The leaf owns the accepted standalone mode values, Korean display labels,
legacy aliases, and the standalone/Prompt Studio normalization projections.
It does not choose wildcard options or expand text.

`_Selector` and NumPy/PCG64 ownership remain in root `wildcard_engine.py`.
Moving them in this slice would change the package skeleton's no-eager-NumPy
boundary and mix selection/import-timing decisions into a mode-contract Move.
Snapshot lifecycle, expansion, node adapters, and consumer cutover also remain
in their current owners.

## Supported moved surface

Mode constants:

- `WILDCARD_MODE_POPULATE`;
- `WILDCARD_MODE_FIXED`;
- `WILDCARD_MODE_SEQUENTIAL`;
- `WILDCARD_MODE_REPRODUCE`; and
- `WILDCARD_MODES`.

Labels and aliases:

- `WILDCARD_MODE_LABELS`;
- `PROMPT_STUDIO_WILDCARD_MODE_LABELS`; and
- `WILDCARD_MODE_ALIASES`.

Functions:

- `normalize_wildcard_mode`; and
- `normalize_prompt_studio_wildcard_mode`.

Root `wildcard_engine.py` binds all ten names directly to the identical
canonical objects. No wrapper, proxy, copied mapping, duplicate constant,
`import *`, or lazy module hook is allowed.

## Caller and alias inventory

Root runtime callers:

- `expand_wildcard_texts` normalizes the requested standalone mode;
- `normalize_prompt_studio_wildcard_mode` projects all non-sequential values
  to populate; and
- root expansion paths compare the canonical mode strings after
  normalization.

Production consumers through root:

- root `nodes.py` explicit compatibility imports;
- `easyuse_anima.nodes.wildcard_nodes`;
- `easyuse_anima.seed.compatibility`, which resolves root mode normalization
  at call time;
- Prompt Studio's `easyuse_anima.prompt.advanced` call-time wrapper; and
- existing workflow/node input definitions.

Existing adapter-local literals remain outside this Move:

- `easyuse_anima.nodes.prompt_advanced_nodes` and
  `easyuse_anima.nodes.regional_nodes` keep their two-mode labels and
  sequential comparison constant;
- `easyuse_anima.prompt.advanced` keeps its local UI labels/control constants
  and call-time wrapper; and
- `easyuse_anima.nodes.wildcard_nodes` keeps its display-label mapping.

D-12e does not cut any consumer over. Root direct aliases preserve the current
import path and exact object identity while later D-12 slices decide selector,
expansion, and final consumer ownership separately.

Tests:

- wildcard mode tests retain mode order, label order, alias normalization, and
  Prompt Studio projection behavior;
- exact root/canonical identity is added for all ten moved names;
- mutable alias-map identity and lookup behavior are frozen; and
- package skeleton, Registry scanner, import-boundary, and backend analyzer
  coverage include the canonical module.

## Global-state inventory

D-12e moves one mutable lookup object:

- `WILDCARD_MODE_ALIASES`, a process-lifetime dictionary populated once at
  import and read by `normalize_wildcard_mode`.

The canonical module becomes its sole owner. Root imports the same dictionary
object directly, so any existing process-local mutation through the root name
continues to affect canonical normalization exactly as before. D-12e does not
freeze, copy, proxy, reset, lock, or clean up this mapping.

All other moved objects are immutable strings/tuples or stateless functions.
The canonical leaf creates no cache, lock, condition, PRNG instance,
background task, factory, or cleanup hook.

Root retains:

- `_Selector` and NumPy/PCG64 construction;
- snapshot/cache lifecycle;
- expansion state and lanes;
- source verification and publication; and
- all node/workflow integration.

## Compatibility and behavior invariants

- standalone mode tuple order remains populate, fixed, sequential, reproduce;
- Korean label tuple order remains 일반, 고정, 순차, 재현;
- Prompt Studio label tuple remains 일반, 순차;
- aliases retain exact spelling and case-sensitive lookup behavior;
- input is still coerced with `str(mode or "").strip()`;
- unknown, empty, and falsey values still normalize to populate;
- Prompt Studio still maps only normalized sequential to sequential and every
  other standalone/legacy value to populate;
- function signatures, return types, and exception behavior are unchanged;
- root aliases preserve exact identity, including the mutable alias dictionary;
- adapter-local literals, workflows, node schemas, saved values, and
  reservation validation remain unchanged; and
- selector/PCG64, seed, source, snapshot, expansion, diagnostics, API, nodes,
  frontend, and bootstrap behavior remain unchanged.

## Allowed-file boundary

Production:

- root `wildcard_engine.py`; and
- new `easyuse_anima/wildcard/mode.py`.

Supporting:

- wildcard mode identity/behavior tests;
- package skeleton, Registry scanner, import-boundary, backend analyzer, and
  exact fixture;
- this inventory, compatibility-shim ledger, and execution roadmap.

## Forbidden

- `_Selector` or NumPy/PCG64 movement/import-timing changes;
- mode value, alias, label, fallback, or normalization behavior changes;
- adapter/node/workflow/frontend caller cutover or duplicate-literal cleanup;
- seed-control, reservation, source, snapshot, cache, expansion, budget, or
  diagnostics changes;
- E-06 lifecycle/factory/cleanup ownership;
- G-03 completed-package enrollment before full D-12 completion;
- API, bootstrap, Registry metadata, release, or instance changes; and
- server, browser, live-instance, model, provider, or network execution.

## Validation and exit

- exact root/canonical identity for all ten moved names;
- existing mode normalization and Prompt Studio projection tests remain
  unchanged;
- alias-dictionary identity and process-local mutation behavior are explicit;
- package skeleton, Registry scanner, import-boundary, backend analyzer, and
  packed archive include canonical `mode.py`;
- canonical mode has zero root/NumPy imports;
- official full runner once at the PR checkpoint; and
- root retains selector, expansion, lifecycle, and integration callers.

## Validation evidence

- root/canonical mode identity and mutable alias lookup: 1 focused test passed;
- existing standalone/Prompt Studio mode behavior: 1 focused test passed;
- package skeleton: 1 test passed;
- Registry scanner safety: 8 tests passed;
- Python import boundaries: 16 tests passed;
- backend analyzer: 18 tests passed;
- canonical `mode.py` Ruff: 0 findings;
- canonical `mode.py` Pyright 1.1.411: 0 diagnostics;
- official full: 1,139 Python tests and 112 frontend files passed, G-03a
  remained 10 completed groups with 0 violations, and the existing 14-error
  Pyright baseline passed; and
- local Registry validation passed; the 261-entry archive contained root
  `wildcard_engine.py` and canonical wildcard `__init__.py`, `mode.py`,
  `models.py`, `seed.py`, `sources.py`, and `snapshot.py`.
