# Python Backend Refactor Execution Roadmap

## Document status

- Status: operational execution runbook
- Snapshot date: 2026-07-24
- Snapshot branch: `dev`
- Integrated `dev` snapshot commit: `b69d33857ef85fb81388f02e9ff1cff195a092d1`
- Scope: Python backend only
- Target architecture: [`python-backend.md`](python-backend.md)
- Architecture decisions: [ADR-001](adr-001-modular-monolith.md) and
  [ADR-002](adr-002-compatibility-shims.md)
- Primary tracking: [#184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184),
  [#185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185),
  [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186),
  [#187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187), and
  [#188](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/188)

This document turns the accepted architecture into an ordered set of work units
that a maintainer or Codex can execute without redesigning the migration during
each PR. It does not replace the ADRs. If this runbook conflicts with an ADR,
the ADR wins and this file must be corrected before implementation continues.

A task is not complete because it is described here. Completion requires a
merged PR, the owning issue's evidence record, and every stated exit gate.

## 1. Current verified state

### Phase summary

| Phase | Integrated snapshot / open implementation state | Remaining exit work |
| --- | --- | --- |
| A - baseline | Complete; #191 is closed | Keep fixtures and analyzers current during later moves |
| B - `nodes.py` extraction | Integrated through B-11c30d1 / PR #347; B-11c30d0a completes in PR #348 | Execute d2-d4, then d0b and d5-d6, followed by Wildcard/NAIA and the final root shim as separate rollback units |
| C - feature contracts/behavior | Partially complete through S167-01a / PR #344 | Continue #167 and #169 in separate Contract/Move/Behavior PRs |
| D - root consolidation | Not started | Execute #186 feature by feature after the corresponding behavior contracts are stable |
| E - runtime ownership | Partial: E-02a and E-07a/E-07b integrated | Continue #187 only where canonical feature owners and explicit contracts exist |
| F - typed boundaries | Partial patterns exist | Extend typed request/result/config and pure migration patterns feature by feature |
| G - quality ratchet | G-01, G-02a/G-02b, and G-03a complete | Extend G-03 enrollment, then continue with G-04 through G-06 |
| H - shim retirement | Not started | Requires canonical release evidence and ADR-002 gates |

### Measured Phase B progress

- The Phase A baseline recorded root `nodes.py` at 12,663 lines.
- In B-11c30c2b / PR #345, root `nodes.py` measures 1,662 lines.
- The mechanical extraction has removed 11,001
  lines, approximately 86.9% of the Phase A baseline, while preserving the root
  compatibility surface.
- B-01 through B-09b2 are integrated. The latest completed implementation slice
  is the AiO generator adapter Move in PR #270.
- The public AiO generator adapter is
  canonical under `easyuse_anima.nodes.aio_nodes`; root `nodes.py` retains its
  direct class/helper aliases and remaining support seams.
- B-11a moved mapping composition to the pure `easyuse_anima.registration`
  owner in PR #292. B-11b moved route-table registration and wildcard startup
  to guarded `easyuse_anima.bootstrap` ownership in PR #293 / `f2a2ec0`.
  B-11c is split into residual-owner Moves before the final `nodes.py` shim;
  B-11c1 moved shared private input types in PR #294 / `ebeee89`, B-11c2 moved
  the read-only workflow lookup owner in PR #295 / `47fef1d`, and B-11c3 moved
  the dependency-free image tensor size helper in PR #296 / `1f18c04`.
  B-11c4 moved the AiO LoRA stack signature helper in PR #297 / `0980530`.
  B-11c5 moved the AiO Spectrum settings normalizer in PR #298 / `617ea14`.
  B-11c6 moved the AiO DiT correction normalizer in PR #299 / `bbca312`.
  B-11c7a moved the AiO special-seed constants and settings normalizer in PR
  #300 / `17343eb`. B-11c7b moved only runtime RNG generation and special-seed
  interpretation in PR #301 / `6863735`. B-11c8 moved only the two hidden-widget
  default JSON serializers in PR #302 / `40e8d94`. B-11c9 moves only the input-
  settings normalizer to the existing resource owner in PR #303; mutable defaults
  and schema ownership stay separate. B-11c10 removed only the unused private
  root `_settings_json` definition in PR #304 / `236a7f5`; live serializers
  remain unchanged. B-11c11 moved only the five Detailer target normalization
  symbols to their existing generation-normalization owner in PR #305 /
  `98812ef`. B-11c12 moved only the two live USDU tile planners to a dedicated
  owner in PR #306 / `7c2fdd5`. B-11c13 removed only the dead private root
  `_aio_usdu_tile_size` wrapper in PR #307 / `21f8c97`. B-11c14 moved only the
  Detailer enabled-target predicate in PR #308 / `5a86162`. B-11c15 moved only
  final-fit size planning in PR #309 / `05beee1`. B-11c16 moved only final-fit
  application in PR #310 / `f4ab6eb`. B-11c17 moved only the diffusion-model
  name wrapper in PR #311 / `82247d9`. B-11c18 moved only the text-encoder name
  wrapper in PR #312 / `3d7e5d2`. B-11c19 moved only the VAE name wrapper in PR
  #313 / `de57090`. B-11c20 moved only the CLIP loader-type wrapper in PR #314 /
  `43c3056`. B-11c21 moved only the AiO postprocess stage in PR #315 /
  `8b3ba38`. B-11c22 moved only the AiO highres stage in PR #316 / `9250610`.
  B-11c23 moved only the AiO upscale dispatcher in PR #317 / `6a5fd7b`.
  B-11c24 moved only the AiO Detailer stage coordinator in PR #318 / `2abc54d`.
  B-11c25 moved only the AiO ResShift leaf in PR #319 / `5e2b335`.
  B-11c26 moved only the AiO Detailer target leaf in PR #320 / `4358ee3`.
  B-11c27 moved only the AiO USDU upscale leaf in PR #321 / `eb0843d`.
  B-11c28 moved only the shared AiO image-resize helper in PR #322.
  E-07b established provider-backed call-time host wiring in PR #328, allowing
  B-11c29a to retire only the unsupported `_comfy_max_resolution` root wrapper
  in PR #329 while preserving the flat pre-bootstrap fallback.
  B-11c29b1 retires only the unsupported direct mapping node lookup in PR #330;
  loaded, requirement, CLIP, and general lookup retirements remain separate.
  B-11c29b2 retired only the unsupported loaded-node root lookup in PR #331.
  B-11c29c retired the two pure requirement root helpers together in PR #332.
  B-11c29d retired the pure CLIP invocation root helper in PR #333. B-11c29b3
  retired the final general host lookup root wrapper in PR #334. B-11c30
  inventoried the remaining binder/resolver families without production
  changes in PR #336 / `02b8c4a`. B-11c30a retires only the three
  Image/SAM3/Impact binders in PR #337 / `3647d3a`; the remaining audit
  contains 27 binders across four families. B-11c30b retires only the three
  LoRA binders in PR #338 / `cdd115d`; 24 binders across three families remain.
  B-11c30c is a production-free Contract/gate that splits the ten remaining
  Prompt/Regional binders into six feature-service binders and four node-adapter
  binders before either group enters a Move PR. PR #339 / `d0188b5` completes
  that split, producing four audited families without changing the 24-binder
  total. B-11c30c1 retires only the six feature-service binders in PR #340 /
  `4cc5cab`, leaving 18 binders across AiO, Prompt node adapters, and
  Wildcard/NAIA. B-11c30c2 completes the production-free split gate in PR
  #341 / `6a21e26`: c2a owns the Prompt Data and Classic Prompt adapters, while
  c2b owns Advanced and Regional only after their root seed-reservation
  dependency has a canonical behavior-preserving owner. B-11c30c2a completes
  the unblocked adapter Move in PR #342. S167-01 / PR #343 freezes the contract
  and exact owner-Move boundary. S167-01a / PR #344 supplies that canonical
  compatibility owner. B-11c30c2b / PR #345 retires the final two Prompt
  node-adapter binders, leaving 14 binders across the AiO and Wildcard/NAIA
  families. B-11c30d / PR #346 is a production-free gate that freezes the
  twelve AiO binders into six exact, non-overlapping Move groups and records
  their per-group resolver and repository-replacement cost. It also records two
  separate prerequisite owner Moves: d0a breaks the output/settings/sampling
  import cycle before d2 through d4, and d0b breaks the
  legacy-orchestration/node-adapter cycle before d5 and d6. d1 cache state is
  the first READY Move and remains mechanically separate from #169 cache
  Behavior. B-11c30d1 / PR #347 retires only that cache-state binder: the
  canonical cache module directly owns its existing state and imports the
  existing serialization, Prompt Data, and LoRA-signature owners. The split
  gate marks d1 retired while keeping d2 through d6 active. Thirteen binders
  remain across AiO and Wildcard/NAIA; cache key, clone, hit/miss, LRU, limit,
  and eviction behavior are unchanged. B-11c30d0a / PR #348 then moves only
  the two output-settings normalizers to the pure
  `easyuse_anima.aio.output_settings` owner. Generation normalization imports
  them directly, root aliases retain identity, and the d2-d4 import cycle is
  removed without retiring another binder or changing settings/save behavior.

### Current quality baseline

- Ruff `0.15.22` is pinned and report-only under G-01.
- Pyright `1.1.411` checks the canonical `easyuse_anima` package in `basic` mode.
- G-02a blocks new or increased diagnostic groups against the reviewed baseline.
- Newly extracted pure/service modules should be strict-clean before they are
  added to the G-02b allowlist.

## 2. Authority and source-of-truth rules

The repository currently has three different status surfaces. Never collapse
them into one ambiguous word such as "done".

1. **Issue state** records tracking and release intent.
2. **`dev` integration state** records reviewed implementation merged to the
   development branch.
3. **`main`/Registry state** records user-facing release availability.

For implementation order:

1. this file owns the executable queue and task boundaries;
2. `python-backend.md` owns the target architecture and global Definition of Done;
3. the owning issue owns feature-specific behavior and compatibility decisions;
4. ADR-001 and ADR-002 own architecture and shim policy;
5. `MAINTAINING.md` owns branch, validation, and release policy.

Before starting a task, compare this snapshot with the current `dev` head and
open PRs. If another PR already owns the same task or the prerequisites changed,
do not create a competing implementation. Update this roadmap or select the
next independent READY task.

## 3. Non-negotiable maintainability rules

1. `easyuse_anima` is the only eventual production implementation root.
2. Organize by feature ownership, not by generic technical layers. Do not create
   catch-all `utils.py`, `helpers.py`, `services.py`, or numbered variants.
3. ComfyUI node classes and HTTP routes are adapters. They parse inputs, call a
   feature service/use case, and map outputs; they do not own persistence,
   provider HTTP, migrations, caches, or cross-feature orchestration policy.
4. Domain and feature services never import node adapters, API routes,
   registration, bootstrap, or root compatibility shims.
5. Infrastructure owns transport and persistence mechanics, not feature schema
   meaning.
6. Every mutable process-wide cache, lock, client, executor, repository, and
   capability has one named owner, lifetime, thread-safety rule, and cleanup
   operation before Phase E exits.
7. Every implementation PR is exactly one of **Move**, **Contract**, or
   **Behavior**. A PR that needs two classifications must be split.
8. A Move PR preserves defaults, coercion, errors, call order, caching, seed
   semantics, serialization, and external side effects.
9. A root shim directly re-exports the canonical object. It does not wrap,
   subclass, proxy, or recreate it. Identity compatibility is tested with `is`.
10. Internal production code never imports a root shim for convenience.
11. New private root aliases require consumer evidence, an owner, and an entry in
    the compatibility registry. Tests alone are not sufficient evidence.
12. Do not introduce a dependency-injection framework. Dataclasses, Protocols,
    factories, and explicit constructors are sufficient.
13. Do not perform repository-wide formatting or opportunistic cleanup in a
    migration PR.
14. Treat the following size numbers as review triggers until G-05 makes them
    executable gates: 800 lines for a new production module, 400 lines for an
    adapter, and 120 lines for a new function/method. An exception needs an owner
    issue and a planned decomposition boundary; meaningless file splitting is
    forbidden.
15. Optional dependencies must fail only their feature and must not break package
    import when disabled or absent.

## 4. Codex execution protocol

### 4.1 Select exactly one work unit

Choose the first READY item in the queue whose prerequisites are still true.
Parallel items may run concurrently only when their allowed-file sets and
behavior owners do not overlap. Search open PRs and branches for the task ID
before creating a branch.

Use one task ID per branch and PR. Recommended branch form:

```text
codex/<task-id>-<short-description>
```

Target `dev`, not `main`, for refactor implementation PRs.

### 4.2 Preflight

Record the exact starting commit in the PR description.

```powershell
git fetch origin
git checkout -b codex/<task-id>-<description> origin/dev
git rev-parse HEAD
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile quick
```

Then read, in this order:

1. this execution roadmap;
2. the task's owning issue and recent comments;
3. `python-backend.md` and the relevant owner-matrix rows;
4. ADR-002 and `python-compatibility-shims.md` when imports or aliases move;
5. the current analyzer and contract fixtures affected by the task.

Do not use `pytest` as a substitute for the checked-in `unittest` runner.

### 4.3 Inventory before editing

For every Move task, write a short inventory in the PR body before implementation:

- symbols and classes moving;
- current callers and monkeypatch seams;
- mapped/public, transitional private, and unsupported/test-only surfaces;
- module-level mutable state and import-time calls in the slice;
- optional dependencies and failure behavior;
- exact contract tests that protect the move.

A file name is not a responsibility. If the inventory shows two independent
owners, split the task before moving code.

### 4.4 Implement the smallest complete slice

- Add the canonical implementation first.
- Move internal consumers to the canonical path.
- Add only evidence-backed direct aliases at the root boundary.
- Update analyzers, package-closure fixtures, and shim records in the same Move
  PR when the move changes those surfaces.
- Keep behavior fixtures byte/deep-equal where applicable.
- Prefer constructor arguments or narrow runtime binding functions over imports
  that reach back into `nodes.py`.

### 4.5 Validation

Run focused tests during implementation. Before requesting review, run:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
```

When packaging or entrypoint paths change, also run:

```powershell
comfy node validate
comfy node pack
```

Inspect the actual packed archive and prove that canonical modules and required
shims form a complete import closure. A source-tree import is not a substitute
for packed-archive evidence.

When a task affects node execution or workflow-visible state, record the tested
ComfyUI and frontend versions and run the task's live smoke matrix. A missing
optional model/provider may justify a documented unexecuted scenario, but it
must not be silently reported as tested.

### 4.6 PR evidence

Every PR description must include:

- task ID and owner issue;
- PR classification: Move, Contract, or Behavior;
- exact base SHA and final head SHA;
- moved/introduced symbols and target owner;
- explicitly forbidden behavior that remained unchanged;
- focused and full commands with result counts;
- public/workflow/API/persistence compatibility evidence as applicable;
- live ComfyUI evidence or a clearly stated unexecuted scenario;
- package/archive closure evidence when paths changed;
- rollback boundary;
- known residual debt and its owner issue.

### 4.7 Stop conditions

Stop expanding the PR and record a blocker when any of the following occurs:

- the baseline quick check fails before task changes;
- current `dev` moved in a way that invalidates the inventory or overlaps the
  same implementation surface;
- a Move requires changing defaults, schema, seed meaning, cache policy,
  timeout/async behavior, error mapping, or execution order;
- node mapping, class identity, input/output order, workflow serialization, or
  an API/persistence fixture changes unexpectedly;
- a canonical module would need to import a root shim or adapter;
- a new root private alias has no consumer evidence and registry owner;
- the task creates a new large module/function without a named decomposition
  owner;
- an optional dependency becomes an import-time requirement;
- the fix requires broad formatting or unrelated cleanup;
- validation cannot distinguish a mechanical move from a behavior change.

Do not hide a blocker with `Any`, a broad ignore, a wrapper class, a copied
implementation, or a weakened fixture. Open or link the appropriate Contract or
Behavior issue and keep the current PR narrowly reviewable.

## 5. Work-unit manifest template

Copy this block into the owning issue or PR before implementation.

```markdown
### <TASK-ID> — <title>

- Status: READY | BLOCKED | IN REVIEW | DONE
- Owner issue:
- PR type: Move | Contract | Behavior
- Base branch / required SHA:
- Prerequisites:
- Goal:
- Allowed production files:
- Allowed test/tool/docs files:
- Forbidden changes:
- Public/shim surfaces:
- Mutable state and lifecycle owner:
- Optional dependencies:
- Focused test commands:
- Full/package/live gates:
- Rollback boundary:
- Exit evidence:
- Follow-up debt owner:
```

## 6. Current executable queue

The ordering below records the integrated path and the current next boundary.
B-11c30d freezes the remaining AiO migration cost once; later Moves consume
their subgroup gate instead of repeating the full inventory. The two cycle
breakers remain standalone owner Moves, and #169 Behavior does not enter the
mechanical retirement series.

| Order | Task | State | Type | Owner | Prerequisites |
| ---: | --- | --- | --- | --- | --- |
| 1 | B-07f SAM3 mechanical vertical slice | COMPLETE on `dev` | Move | #184 | PR #251 / `015b8197` |
| 2 | C168-03 typed AiO config boundary | COMPLETE on `dev` | Contract | #168 | PR #252 / `7f686bed` |
| 3 | G-02b strict-clean pure/service allowlist | COMPLETE on `dev` | Contract/gate | #188 | PR #254 / `76237a60` |
| 4 | C168-04 pure version-dispatch/migration registry | COMPLETE on `dev` | Contract | #168 | PR #255 / `29aa200e` |
| 5 | C168-05 cross-surface setting omission gate | COMPLETE | Contract/gate | #168 | PR #256 merged |
| 6 | G-03a completed-package import boundary fail gate | COMPLETE on `dev` | Contract/gate | #188 | PR #258 / six reviewed zero-violation prefixes enrolled |
| 7 | C168-06 normalizer ownership move | COMPLETE on `dev` | Move | #168/#184 | PR #257 / `3ca5500` |
| 8 | B-08a through B-08e AiO support-helper extraction | COMPLETE on `dev` | Move | #184 | B-08a PR #259; B-08b1 PR #260; B-08b2 PR #261; B-08c PR #262; B-08d1 PR #263; B-08d2 PR #264; B-08e PR #265 |
| 9 | B-09a AiO input adapter move | COMPLETE in PR #268 | Move | #184 | AiO helpers canonical through B-08e |
| 10 | B-09b1 AiO legacy orchestration body move | COMPLETE on `dev` | Move | #184 | PR #269 / `7484dc7` |
| 11 | B-09b2 AiO generator adapter move | COMPLETE on `dev` | Move | #184 | PR #270 / `57d40b4` |
| 12 | B-10a machine-readable compatibility audit | COMPLETE on `dev` | Contract/gate | #184/#188 | PR #271 / `3c7b857` |
| 13 | B-10b private alias reduction | COMPLETE on `dev` through PR #291 / `c6b4680` | Contract/cleanup, split PRs | #184/#188 | Audited alias surface integrated |
| 14 | B-11 registration/bootstrap/root shim | IN PROGRESS through B-11c30d0a PR #348; d2-d4 are next, and d0b precedes d5-d6 | Move/Contract, split PRs | #184 | Frozen AiO split gate; S167-01 contract |
| 15 | S167 backend seed reservation series | S167-01 Contract COMPLETE in PR #343 and S167-01a consumer Move COMPLETE in PR #344; Behavior and Adapter remain | Contract then Move then Behavior | #167 | Canonical AiO/node seams |
| 16 | A169 stage pipeline series | BLOCKED by #168 and B exit | Contract then Behavior | #169 | Typed config and mechanical AiO move |
| 17 | A169 first-pass cache policy | BLOCKED by stage/cache ownership seam | Behavior | #169 | Mechanical cache move and benchmark harness |
| 18 | D-series canonical root consolidation | BLOCKED by relevant C contracts | Move | #186 | Phase B exit; per-feature behavior stable |
| 19 | E-series RuntimeServices/lifecycle | BLOCKED by canonical owners | Move/Contract, split PRs | #187 | Relevant D moves |
| 20 | G-04 through G-06 and H | INCREMENTAL/LATER | Gate/Contract | #188 | Appropriate package and release evidence |

Issue #199, authenticated diagnostics/settings access, is an independent security
track. It may proceed when its threat model and owner are ready, but it does not
relax or block the package-migration rules above.

## 7. Immediate task manifests

### B-07f — SAM3 mechanical vertical slice

- **Owner:** #184
- **Type:** Move
- **Goal:** remove the remaining SAM3 detection/detailer implementation from
  root `nodes.py` without changing dependency discovery, input defaults, error
  messages, mask/SEGS handling, delegation arguments, or return values.
- **Default ownership:** cohesive SAM3/Detailer behavior belongs near the existing
  image/Detailer feature, for example `easyuse_anima/image/sam3.py`. Create
  `easyuse_anima/nodes/sam3_nodes.py` only when the inventory proves that an
  actual node adapter class needs it. Do not create an empty template package.
- **Required inventory:** every SAM3 constant, resolver, formatter, detector,
  context helper, delegate, class, root caller, AiO caller, and monkeypatch seam
  remaining in `nodes.py`.
- **Allowed production files:** root `nodes.py`; cohesive new/existing modules
  under `easyuse_anima/image` and, if justified, `easyuse_anima/nodes`.
- **Allowed supporting files:** focused tests, backend/node analyzers, package
  skeleton/closure fixtures, and the compatibility-shim registry.
- **Forbidden:** changing detection text formatting, thresholds, refine count,
  `combined`/bbox/drop/contour semantics, no-SEGS behavior, Impact delegation,
  optional dependency names, AiO stage order, settings, seed, or cache behavior.
- **Compatibility:** preserve any mapped class identity; classify unmapped helper
  classes instead of automatically publishing them. Preserve call-time lookup
  where tests or optional-node loading require late binding.
- **Focused tests:**

  ```powershell
  python -m unittest discover -s tests -p "test_aio_nodes.py"
  python -m unittest discover -s tests -p "test_comfy_adapters.py"
  python -m unittest discover -s tests -p "test_node_contracts.py"
  python -m unittest discover -s tests -p "test_nodes_module_analyzer.py"
  python -m unittest discover -s tests -p "test_python_backend_analyzer.py"
  python -m unittest discover -s tests -p "test_python_package_skeleton.py"
  python -m unittest discover -s tests -p "test_registry_scanner_safety.py"
  ```

- **Exit:** root contains no SAM3 implementation beyond evidence-backed direct
  aliases or runtime binding; canonical modules do not import root; optional
  SAM3/Impact absence does not break package import; full runner passes; new
  canonical modules are Pyright-clean; package closure remains complete.
- **Manual evidence:** package import with optional dependencies absent; actual
  SAM3 detection/detailer smoke when the dependency and model are available.

### C168-03 — Typed AiO config boundary

- **Owner:** #168
- **Type:** Contract
- **Goal:** convert the reviewed manifest/normalized dictionary boundary into
  typed Python config objects while preserving the exact v1 normalized payload.
- Use small section types rather than one all-owning object. Raw dictionaries
  remain at JSON/workflow and compatibility-facade boundaries only.
- Keep `_normalize_aio_generation_settings()` as a compatibility facade until
  internal consumers have moved; do not change defaults, coercion, unknown-key
  policy, dynamic capability handling, or serialized output.
- Prefer deterministic checked-in code plus golden parity over adding a complex
  generator. Code generation is justified only when its output is stable,
  reviewable, and enforced in the official runner.
- Add conversion tests in both directions where serialization is required and
  prove deep equality with the C168-01/C168-02 fixtures.
- New typed models and pure conversion functions must be Pyright strict-clean.

### C168-04 — Pure migration/version dispatch

- **Owner:** #168
- **Type:** Contract
- Add a pure, stepwise migration registry around version detection,
  normalization, and typed conversion.
- Migrations perform no I/O and never mutate the caller's object.
- Do not invent a fake schema v2 solely to satisfy the architecture diagram. If
  no real v2 exists, test version dispatch, unsupported/future versions, legacy
  aliases, input immutability, and the registration mechanism with the current
  version and explicit fixtures.
- A failed migration must not replace persisted or workflow source data.

### C168-05 — Cross-surface setting omission gate

- **Owner:** #168
- **Type:** Contract/gate
- Make a new manifest setting fail validation when Python defaults/typed config,
  JavaScript defaults/sanitization, UI metadata, or maintained documentation is
  omitted.
- Dynamic capability-derived choices remain outside static schema ownership.
- The gate must report the exact missing field/surface and run offline in the
  official project check.
- The golden coverage ledger owns explicit Python typed, JavaScript default and
  sanitization, UI owner/exposure, and maintained-documentation records for
  every canonical field and reference site. It is validation-only and is not a
  runtime manifest/code-generation dependency.
- #168 exits only after C168-03 through C168-06 and the issue's remaining
  completion boxes pass.

### C168-06 — Normalizer ownership move

- **Owner:** #168/#184
- **Type:** Move
- Move `_merge_versioned_settings()` and `_normalize_aio_generation_settings()`
  from root `nodes.py` to cohesive canonical AiO ownership after C168-05 fixes
  every cross-surface omission contract.
- Preserve all defaults, coercion, legacy aliases, unknown-field ordering,
  dynamic capability lookup, future/invalid version tolerance, dictionary return
  identity, and caller mutation behavior. Root keeps only evidence-backed direct
  aliases/runtime bindings.
- Do not adopt C168-04 strict dispatch, add a new migration, or mix stage/cache
  work. Those require separate Contract/Behavior decisions.

### G-02b — Strict-clean pure/service allowlist

- **Owner:** #188
- **Type:** quality gate; do not combine with broad production cleanup
- Start with reviewed pure/common/feature-service modules that already report
  zero diagnostics. Add paths in small groups with an owner and focused tests.
- Keep ComfyUI dynamic objects and tensor/model `Any` at adapter boundaries.
- If enabling strict mode exposes real code problems, fix one cohesive module in
  a separate small Contract/maintenance PR or defer it; do not weaken global
  settings or add broad ignores.
- Candidate modules must include newly extracted pure services only after their
  Move PR is merged and independently clean.

### G-03a — Completed-package import boundary fail gate

- **Owner:** #188
- **Type:** Contract/gate
- Promote existing report-only checks to blocking for completed canonical
  packages, not for all legacy root debt at once.
- Reject new canonical-to-root imports, feature-to-adapter back references,
  cycles, fallback imports inside canonical packages, and registration side
  effects.
- Existing root loader compatibility may remain baseline debt until B-11/D-14;
  the gate must not be weakened to accommodate new canonical violations.
- The first blocking ledger contains exactly six reviewed prefixes:
  `common`, `image`, `infrastructure/comfy`, `lora`, `naia`, and `profiles`.
  Group id, owner issue, prefix, role, ordering, uniqueness, and the exact group
  set are validated so deleting or broadening an entry cannot silently weaken
  the gate. New Python files beneath an enrolled prefix are covered
  automatically.
- The checker consumes `analyze_python_backend.py` output without importing
  production modules. It rejects enrolled canonical imports of repository-root
  modules, references to `easyuse_anima/nodes/`,
  `easyuse_anima/api/routes/`, exact `bootstrap.py` or `registration.py`,
  runtime cyclic SCC membership, compatibility fallback imports, and narrowly
  identified import-time registration or mapping-mutation calls.
- The cycle view covers the analyzer's shipped Python inventory. Exact absolute
  imports that resolve to an inventoried local module complete the graph before
  the analyzer's own runtime-edge filter and SCC helper run, so the existing
  `TYPE_CHECKING` exclusion policy remains authoritative.
- Genuine external and optional dependencies with no repository-local target
  remain allowed. Unenrolled legacy package debt stays report-only until its
  own reviewed completion checkpoint. The official quick/full quality path
  invokes this checker exactly once per project check.

## 8. AiO mechanical extraction plan

Do not implement #169's stage protocol or cache policy during these tasks. Every
B-08/B-09 PR preserves current execution order and behavior and updates the
analyzer baseline as a readable symbol move.

### B-08 — Support-helper Move PRs

Use the actual caller/import inventory to confirm these boundaries. Do not force
one file per row when two responsibilities are inseparable, and do not combine
rows merely to reduce PR count.

| Task | Default responsibility | Candidate canonical owner | Explicitly unchanged |
| --- | --- | --- | --- |
| B-08a | resource selection/loading, model/CLIP/VAE bundles, capability lookup | `easyuse_anima/aio/resources.py` plus existing `infrastructure/comfy` ports | loader defaults, fallback order, error text, lazy dependency behavior |
| B-08b | conditioning preparation, model patches, LoRA application, model variants | cohesive modules under `easyuse_anima/aio` | conditioning metadata, model identity, patch order, LoRA strength/order |
| B-08c | sampler backend dispatch and invocation adapters | `easyuse_anima/aio/sampling.py` | backend selection, kwargs filtering, seed values, steps/CFG/scheduler, result shape |
| B-08d | preview collection/events, save adapters, output metadata | `easyuse_anima/aio/preview.py` and/or `output.py` when responsibilities justify both | preview order, UI payload, filenames, metadata keys, save backend behavior |
| B-08e | current first-pass cache implementation | `easyuse_anima/aio/first_pass_cache.py` | current entry limit, key, clone/copy behavior, hit/miss semantics, lack of new TTL/byte policy |

B-08a is complete on `dev` in PR #259. Its mechanical boundary moves resource defaults,
loaders, and AiO resource bundles to `easyuse_anima.aio.resources`, moves Impact
capability lookup to `easyuse_anima.infrastructure.comfy.capabilities`, and
keeps the root names as direct identity aliases with a call-time runtime seam.

B-08b1 is complete on `dev` in PR #260. This first B-08b mechanical slice moves shared
CLIP encoding to `easyuse_anima.infrastructure.comfy.invocation`, moves LoRA and
base-model patch preparation to `easyuse_anima.aio.model_preparation`, and moves
USDU conditioning preparation to `easyuse_anima.aio.conditioning`.

B-08b2 is complete on `dev` in PR #261. This second B-08b mechanical slice moves
Spectrum correction/forecast model variants and ephemeral model cleanup to
`easyuse_anima.aio.model_preparation`, preserving direct root identities,
call-time sub-helper replacement, optional dependency timing, and cleanup order.

B-08c is complete on `dev` in PR #262. This mechanical slice moves latent
creation, Comfy and Spectrum sampler invocation, backend dispatch, VAE
encode/decode, stage sampler selection, and highres backend selection to
`easyuse_anima.aio.sampling`, preserving direct root identities, call-time
helper replacement, seed timing, defaults, kwargs filtering, and result shape.

B-08d1 is complete on `dev` in PR #263. This first B-08d mechanical slice moves
preview stage labels, event/cache-format constants, path and file-size tagging,
preview events, and temporary WebP/PNG fallback saving to
`easyuse_anima.aio.preview`, preserving direct root identities, lazy optional
imports, metadata/event order, filenames, and fallback behavior.

B-08d2 is complete on `dev` in PR #264. This second B-08d mechanical slice moves
Image Saver hash normalization/fetching, LoRA prompt metadata, ComfyUI and Image
Saver adapters, and filename-prefix handling to `easyuse_anima.aio.output`,
preserving direct root identities, call-time helper replacement, lazy optional
imports, metadata order, filenames, save kwargs, seed timing, and error behavior.

B-08e is complete on `dev` in PR #265. This mechanical slice moves current
first-pass cache state, cache-key generation, clone/reset, and LRU helpers
to `easyuse_anima.aio.first_pass_cache`, preserving direct root identities,
call-time state/helper replacement, limit 2, key field order, clone isolation,
falsey misses, hit refresh, overwrite, and oldest-first eviction behavior.
At B-08e integration, the shared `_aio_lora_stack_signature` remained
root-owned because both `IS_CHANGED` and the cache key consume it. B-11c4 moves
the implementation to `easyuse_anima.aio.model_preparation`; both canonical
consumers continue resolving the retained root alias at call time.

Rules for every B-08 PR:

- one row per PR unless the inventory proves a smaller slice is required;
- no stage objects, `GenerationRequest`, or new cache policy;
- no direct canonical import of root `nodes.py`;
- runtime seams are explicit and narrow;
- new canonical module is Pyright-clean;
- focused behavior parity and full project checks pass;
- root aliases are added only with evidence and a shim-registry entry.

### B-09a — `EasyUseAnimaInput` adapter move

Move the public class to `easyuse_anima/nodes/aio_nodes.py` after #168 owns the
config boundary. Preserve class identity, input order/defaults, hidden inputs,
outputs, workflow serialization, and existing runtime lookup behavior. The
adapter must delegate typed normalization instead of re-owning schema logic.

B-09a is complete in PR #268. The canonical public adapter now lives in
`easyuse_anima.nodes.aio_nodes`; root package and direct-import modes bind the
same class object. Its ComfyUI contract keeps the local import-time socket
literal while resolving resource candidates, normalizers, schema/version
constants, change-key helpers, and copy helpers from the root compatibility
runtime at call time. Input order/defaults, serialized context shape, copy
boundaries, and helper evaluation order remain unchanged.

### B-09b — `EasyUseAnimaAIOGenerator` and legacy orchestration move

Move the public adapter and current orchestration to canonical ownership without
converting it to stages. The intended intermediate shape is:

```text
easyuse_anima/nodes/aio_nodes.py      # thin public ComfyUI adapters
easyuse_anima/aio/...                 # mechanically extracted current helpers
easyuse_anima/aio/legacy_generation.py  # temporary current-order orchestration if needed
```

`legacy_generation.py` is a named temporary exception, not the final design. If
it exceeds the G-05 guidance, record #169 as its decomposition owner. Do not
solve that debt by leaving the full orchestration in the node adapter or by
inventing an unreviewed framework.

B-09b is split at the existing compatibility boundary:

- B-09b1 moves only the current 329-line `generate` orchestration body to
  `easyuse_anima.aio.legacy_generation`. The root public class, `INPUT_TYPES`,
  `IS_CHANGED`, mappings, input validator, and exact `generate` signature stay
  in `nodes.py`; the method delegates through a direct private alias and a
  resolver-only call-time seam. The deterministic v1 trace freezes base
  txt2img and patched upscale-plus-intermediate-preview order, cleanup-before-
  save, metadata, UI projection, and `id(generator)` cache scope without
  introducing stage contracts.
- B-09b2 moves the public `EasyUseAnimaAIOGenerator` adapter to canonical node
  ownership after B-09b1 is integrated. It owns class/mapping identity and the
  remaining workflow/browser serialization checkpoint. B-09 is not complete
  until that adapter slice and the stated integration evidence are complete.

B-09b1 is complete in PR #269. B-09b2 is complete on `dev` in PR #270: the generator,
input signature helper, and input validator now live in
`easyuse_anima.nodes.aio_nodes`; root imports them as direct identity aliases in
both import modes. The adapter reuses the existing resolver slot so mutable
special-seed state, normalization, signature, LoRA, change-key, settings-default,
and legacy-orchestration dependencies remain call-time root compatibility seams.
No node contract, mapping ID, method signature, or execution order changed in
this Move. Its focused, full, workflow serialization, package-import, and
representative runtime checkpoints are recorded in PR #270; B-09 is complete.

Before merge, capture a deterministic execution trace fixture for the current
major phases and prove no order/result/cleanup drift. Run at least:

- one base txt2img queue with optional stages disabled;
- one representative enabled optional stage when its dependencies are available;
- load/save/reload of the 0.5.2 AiO workflow fixture;
- Legacy canvas and Node 2.0 serialization comparison;
- package import with optional providers disabled.

Record exact ComfyUI/frontend versions. An unavailable optional dependency is
reported as unexecuted, not passed.

## 9. Phase B compatibility and exit plan

### B-10a — Machine-readable compatibility surface audit

- **Status:** COMPLETE on `dev` in PR #271 / `3c7b857`.
- **Owners:** #184 and #188
- **Type:** Contract/gate
- Inventory every root export and alias after B-09.
- Classify each symbol as permanent entrypoint, supported public re-export,
  transitional private seam, or unsupported/test-only.
- Add or extend a machine-readable fixture that records canonical target, object
  identity requirement, owner issue, first release placeholder, known consumers,
  and removal gates.
- Update `python-compatibility-shims.md` from B-04-only detail to the actual
  B-04-through-B-09 state.
- Record test-only imports as unsupported/test-only; their canonical-path
  migration and any root-alias removal belong to scoped B-10b PRs. They do not
  justify public support.

### B-10b — Private alias reduction

- **Status:** B-10b1 through B-10b20 are complete on `dev` through PR #291 /
  `c6b4680`.
- **Type:** small compatibility cleanup PRs, one owner/surface at a time
- Remove unsupported/test-only aliases after tests use canonical paths.
- Retain an actual monkeypatch seam only when the consumer and call-time binding
  contract are documented and tested.
- Do not remove mapped public node-class re-exports in Phase B.
- Do not combine alias removal with feature behavior changes.

B-10b1 removes only `_comfy_checkpoint_names` from the relative and flat root
import surfaces. The SAM3 adapter already imports
`easyuse_anima.infrastructure.comfy.resources` directly; repository tests move
their deterministic patch to that canonical consumer. No other alias, mapped
class, optional-dependency behavior, or workflow contract changes in this
rollback unit.

B-10b2 removes only `_EasyUseAnimaAlignedDetailerHook` from the relative and
flat root import surfaces. Both canonical production adapters already import
`easyuse_anima.image.detailer` directly. Focused normal-package and synthetic
package-entrypoint contracts retain their class identity and construction
behavior without preserving a root-only private alias.

B-10b3 removes only `_EasyUseAnimaImpactDetailerDelegate` from the relative and
flat root import surfaces. The canonical SAM3 adapter already imports the
delegate class directly from `easyuse_anima.nodes.impact_detailer_nodes`.
Normal-package and synthetic package-entrypoint contracts retain class identity,
`INPUT_TYPES`, and the existing canonical delegation path.

B-10b4 removes only `_impact_core_module` from the relative and flat root
import surfaces. The canonical `_impact_scheduler_names` implementation calls
the helper in its own `easyuse_anima.infrastructure.comfy.capabilities` module;
the root alias is test-only and is not a working call-time monkeypatch seam.
Normal-package and synthetic package-entrypoint contracts retain canonical
Impact discovery, scheduler lookup, and optional-dependency fallback behavior.

B-10b5 removes only `_align_up`, `_aligned_size_near_scale`, and
`_alignment_value` from the relative and flat root import surfaces. Canonical
geometry, scaling, image-node, and Detailer consumers already import the
`easyuse_anima.image.geometry` owner directly. `_align_nearest` and
`_align_down` remain because root residual runtime still calls them; scaling
helper aliases remain a separate B-10b6 rollback unit.

B-10b6 removes only `_image_scale_by_multiple_size`, `_max_long_edge_value`,
`_normalize_image_scale_options`, and `_scale_by_value` from the relative and
flat root import surfaces. The canonical image adapter and scaling policy
already call `easyuse_anima.image.scaling` directly. The two scaling constants
remain root runtime-resolver seams, and the mapped image-scale node class stays
a supported root re-export.

B-10b7 removes only `_clear_aio_first_pass_cache` from the relative and flat
root import surfaces. Repository tests call the canonical
`easyuse_anima.aio.first_pass_cache` owner directly; no production caller,
runtime resolver, or monkeypatch seam consumes the root function alias. Mutable
cache state, binding, key, clone, get/put, LRU, and clear behavior stay unchanged.

B-10b8 removes only `WILDCARD_SEED_RANGE_NOTE` from the relative and flat root
import surfaces. The canonical Wildcard adapter owns and consumes its immutable
tooltip note directly; no production caller, runtime resolver, binder, mapping,
or monkeypatch seam consumes the root alias. Wildcard parsing, populated text,
mode, seed, tooltip content, and mapped class identity stay unchanged.

B-10b9 removes only `_call_impact_detailer`, `_empty_mask_for_image`,
`_empty_segs_for_image`, `_find_impact_detailer_class`,
`_find_impact_mask_to_segs_class`, `_find_sam3_detect_class`, and
`_format_sam3_detection_prompt` from the relative and flat root import
surfaces. Canonical SAM3 and Impact adapters already import their owner
directly. Context/state helpers and the runtime binder remain root seams;
resolver timing, prompt formatting, masks/SEGS, and Impact delegation do not change.

B-10b10 removes only `DEFAULT_QUALITY_TAGS` and
`DEFAULT_TRAILING_QUALITY_TAGS` from the relative and flat root import
surfaces. Canonical Prompt Builder/Studio and advanced-prompt consumers already
import the immutable defaults from `easyuse_anima.prompt.fields` directly. The
stored strings, input defaults, workflow schema, and prompt behavior do not change.

B-10b11 removes only `EasyUseAnimaPromptStudioExtend` from the relative and
flat root import surfaces. The canonical legacy class stays in
`easyuse_anima.nodes.prompt_advanced_nodes`, and frontend Extend type hooks stay
unchanged. The class is already absent from backend node/display mappings and
the reviewed workflow fixture, so node registration and saved-workflow support
do not change.

B-10b12 removes the nine unsupported/test-only `easyuse_anima.prompt.data`
root aliases recorded in the compatibility fixture. Canonical prompt-data
adapters and services already import their schema, version, socket tuples, and
helpers directly. `PROMPT_DATA_TYPE`, runtime-resolver helpers, mapped classes,
schema values, socket order, nested fallbacks, dict updates, and serialization
behavior stay unchanged.

B-10b13 removes the 13 unsupported/test-only `easyuse_anima.naia.client`
root aliases recorded in the compatibility fixture. Canonical NAIA client and
node-adapter consumers already import or call the owner directly. `LATENT_ALIGN`,
`_parse_random_response`, `_post_random`, the runtime binder, mapped class,
HTTP/host policy, timeout, prompt cleanup, resolution fitting, settings, and
workflow behavior stay unchanged.

B-10b14 removes the 16 unsupported/test-only `easyuse_anima.naia.resolution`
root aliases recorded in the compatibility fixture. Canonical resolution,
Prompt Advanced, and Regional consumers already import or call the owner
directly. Five runtime-resolved label/selection helpers remain root seams;
bucket data/order, scale/max-long-edge policy, 32-pixel snapping, nearest-fit,
input defaults, mapped classes, and workflow behavior stay unchanged.

B-10b15 removes the five unsupported/test-only
`easyuse_anima.prompt.conditioning` root aliases recorded in the compatibility
fixture. Canonical conditioning and Prompt Data consumers already import or
call the owner directly. Nine runtime-resolved conditioning seams remain;
mode/profile values, mapped classes, Spectrum old-signature fallback,
warning-once behavior, and saved-workflow contracts stay unchanged.

B-10b16 removes the 12 unsupported/test-only
`easyuse_anima.prompt.advanced` root aliases recorded in the compatibility
fixture. Canonical Advanced services and adapters already import or call the
owner directly. Twenty-two runtime-resolved Advanced seams remain; field
schema/order, workflow property, legacy Extend slots, return tuples, wildcard
normalization, prompt/artist assembly, mapped classes, and saved-workflow
contracts stay unchanged.

B-10b17 removes the 12 unsupported/test-only
`easyuse_anima.prompt.regional` root aliases recorded in the compatibility
fixture. Canonical Regional services and adapters already import or call the
owner directly. Fourteen runtime-resolved Regional seams remain; schema/type
and workflow-property strings, mask geometry, prompt/conditioning assembly,
mapped classes, frontend properties, and saved-workflow contracts stay
unchanged.

B-10b18 removes 11 private parsing/config helpers from the 53-symbol
`easyuse_anima.prompt.artist_mix` unsupported root-alias group. Canonical
Artist Mix code already calls these helpers lexically; no root runtime caller,
resolver, binder, or patch seam consumes them. The remaining 42 Artist Mix
aliases are deliberately split into a constants/mode unit and a conditioning/
tensor unit. Parser/config behavior, 25 runtime-resolved seams, mapped classes,
metadata, sockets, and saved-workflow contracts stay unchanged.

B-10b19 removes 21 mode/key/tag-position constants from the remaining
42-symbol `easyuse_anima.prompt.artist_mix` unsupported root-alias group.
Production adapters already import the canonical owner directly; the sole
repository root test consumer moves its nine affected imports to that owner.
The remaining 21 conditioning/tensor aliases are reserved for B-10b20.
Constant values and order, the mutable mode-description mapping, 25
runtime-resolved seams, mapped classes, frontend, metadata, sockets, and
saved-workflow contracts stay unchanged.

B-10b20 removes the final 21 conditioning/tensor helpers from the Artist Mix
`unsupported_test_only` root-alias group. Canonical code already consumes the
helpers lexically; no root runtime caller, test import, patch, resolver, or
binder uses them. The Artist Mix unsupported group therefore disappears while
all 25 documented transitional seams remain. Tensor math, dtype/device and
padding behavior, weights, branch ordering, metadata cloning, fallback/error
handling, mapped classes, frontend, sockets, and saved workflows stay
unchanged. The separate legacy Wildcard unsupported alias remains for D-12.

### B-11 — Registration, bootstrap, and final `nodes.py` shim

- **Owner:** #184
- **Type:** Move
- **Execution split:**
  - B-11a moves only literal node/display mapping composition to
    `easyuse_anima.registration` and preserves root mapping/class identity.
    This unit is complete on `dev` in PR #292 / `20c8b4d`.
  - B-11b moves existing route and wildcard-directory initialization to a
    guarded, idempotent `easyuse_anima.bootstrap` owner. PR #293 / `f2a2ec0`
    implements this unit without changing route handlers or wildcard behavior.
  - The B-11c readiness audit found that one cutover would combine 41 residual
    functions, 2 classes, 33 globals, and 28 runtime binders. B-11c therefore
    first moves residual owners one vertical family at a time, then migrates
    binder/resolver seams by family, and only then performs the final shim
    cutover.
  - B-11c1 moves `_AnyType`, `_FlexibleOptionalInputType`, and `_ANY_TYPE` to
    side-effect-free `easyuse_anima.nodes.input_types`, while retaining direct
    root aliases and the existing Regional, Prompt Advanced, and LoRA binder
    calls. PR #294 / `ebeee89` completes this Move-only unit.
  - B-11c2 moves only `_get_workflow_node` to side-effect-free
    `easyuse_anima.workflow`. PR #295 retains the root direct alias and the
    existing Wildcard, NAIA, Prompt Advanced, and Regional binder/resolver
    calls. Reserved wildcard seed consumption remains separate.
  - B-11c3 moves only `_image_tensor_size` to the existing side-effect-free
    `easyuse_anima.image.geometry` owner. PR #296 retains the root direct alias,
    all root stage callers, and the existing AiO preview/legacy-generation
    runtime resolvers; resize and postprocess execution remain separate.
  - B-11c4 moves only `_aio_lora_stack_signature` to the existing
    `easyuse_anima.aio.model_preparation` owner. PR #297 retains the root direct
    alias, both canonical consumer resolver paths, and call-time replacement of
    the root `_normalize_aio_lora_stack` helper; cache policy and `IS_CHANGED`
    behavior remain separate.
  - B-11c5 moves only `_normalize_aio_spectrum_settings` to its existing sole
    caller owner, `easyuse_anima.aio.generation_normalization`. PR #298 retains
    the root direct alias, the existing caller resolver, call-time coercion
    helper replacement, in-place dict semantics, and exact clamp/fallback order;
    DiT correction, seed, schema/default, and sampler behavior remain separate.
  - B-11c6 moves only `_normalize_aio_dit_corrections_settings` to the same
    generation-normalization owner. PR #299 retains the root direct alias, the
    existing caller resolver, call-time coercion helper replacement, in-place
    dict semantics, and exact DCW/SMC/CFG++/FSG clamp and fallback order;
    Spectrum, seed, schema/default, and sampler execution remain separate.
  - B-11c7a moves only `AIO_SPECIAL_SEED_RANDOM`,
    `AIO_SPECIAL_SEED_INCREMENT`, `AIO_SPECIAL_SEED_DECREMENT`,
    `AIO_SPECIAL_SEEDS`, and `_normalize_aio_seed` to the same
    generation-normalization owner. PR #300 retains direct root alias identity,
    the mutable special-seed set, and call-time root `_as_int`, `MAX_SEED`, and
    lower-bound replacement. Runtime random seed generation, special-seed
    interpretation, increment/decrement behavior, and seed reservation remain
    separate.
  - B-11c7b moves only `_new_aio_random_seed` and
    `_resolve_aio_runtime_seed` to `easyuse_anima.aio.sampling`. PR #301 retains
    direct root alias identity and call-time root `random`, `MAX_SEED`,
    `_normalize_aio_seed`, mutable `AIO_SPECIAL_SEEDS`, and nested random-helper
    replacement. RNG range/state/call order and backend seed reservation remain
    unchanged.
  - B-11c8 moves only `_aio_input_settings_json` and
    `_aio_generation_settings_json` to `easyuse_anima.nodes.aio_nodes`. PR #302
    retains direct root alias identity, the existing AiO node runtime resolver,
    call-time root `json` and mutable default-dict replacement, compact Unicode
    JSON options, insertion order, and hidden widget/workflow shape. Default
    settings ownership and normalization remain separate.
  - B-11c9 moves only `_normalize_aio_input_settings` to
    `easyuse_anima.aio.resources`. PR #303 retains direct root alias identity,
    all three existing runtime-resolver callers, and call-time root settings
    merge, schema/version, coercion helper, dtype, and device replacement.
    Defaults/schema ownership, typed settings, widget serialization, and resource
    loading behavior remain separate.
  - B-11c10 removes only the unused private root `_settings_json` definition.
    PR #304 records an explicit absence contract instead of inventing a
    canonical owner for a symbol with no production, resolver, test-import, or
    documented compatibility consumer. Root `json` and both live hidden-widget
    serializers remain unchanged.
  - B-11c11 moves `_AIO_DETAILER_RESERVED_KEYS`,
    `_AIO_DETAILER_CUSTOM_RE`, `_is_aio_detailer_target_name`,
    `_aio_detailer_target_defaults`, and `_aio_detailer_target_order` to the
    existing `easyuse_anima.aio.generation_normalization` owner. PR #305 retains
    direct root alias identity, mutable reserved-key/default state, root binding
    replacement, regex matching, trim/deduplication/order rules, deep cloning,
    and custom label suffix behavior. Detailer execution, enabled gating,
    schema/default ownership, SAM3, and Impact behavior remain separate.
  - B-11c12 moves only `_aio_usdu_auto_tile_dimension` and
    `_aio_usdu_tile_plan` to the dedicated `easyuse_anima.aio.usdu` owner. PR
    #306 retains direct root alias identity and call-time root `ceil`, alignment,
    image-size, coercion, and nested auto-dimension replacement. Tile clamp,
    fallback, scale, rounding, dict order, and stage behavior remain unchanged.
    The unused `_aio_usdu_tile_size` wrapper remained root-owned for a separate
    Contract/cleanup decision.
  - B-11c13 removes only the unused private root `_aio_usdu_tile_size`
    definition in PR #307. The compatibility fixture and flat/package contract
    record its absence; the live canonical planners and USDU stage remain
    unchanged.
  - B-11c14 moves only `_aio_detailer_has_enabled_targets` to the existing
    `easyuse_anima.aio.generation_normalization` owner in PR #308. The root
    predicate remains a direct alias and resolves boolean coercion and target
    ordering at call time; Detailer normalization and stage execution remain
    unchanged.
  - B-11c15 moves only `_aio_final_fit_size` to the dedicated
    `easyuse_anima.aio.postprocess` owner in PR #309. Root coercion, square-root,
    alignment, and latent-alignment seams remain call-time resolved. Final-fit
    application, resize, postprocess stage execution, and
    `AIO_FINAL_FIT_MODES` ownership remain separate.
  - B-11c16 moves only `_apply_aio_final_fit` to the existing postprocess owner
    in PR #310. Root image-size, final-fit planning, coercion, and shared resize
    seams remain call-time resolved; postprocess stage execution and the shared
    resize helper remain root-owned.
  - B-11c17 moves only `_comfy_diffusion_model_names` to the existing AiO
    resource owner in PR #311. The default-candidate tuple, folder lookup, and
    domain-neutral adapter remain call-time root seams; the other resource-name
    wrappers remain separate.
  - B-11c18 moves only `_comfy_text_encoder_names` to the existing AiO resource
    owner in PR #312. The default-candidate tuple, folder lookup, and domain-
    neutral adapter remain call-time root seams; the other resource-name
    wrappers remain separate.
  - B-11c19 moves only `_comfy_vae_names` to the existing AiO resource owner in
    PR #313. The default-candidate tuple, node-class finder, folder lookup, and
    domain-neutral adapter remain call-time root seams; the other resource-name
    wrappers remain separate.
  - B-11c20 moves only `_comfy_clip_loader_types` to the existing AiO resource
    owner in PR #314. The allowed-type tuple, node-class finder, and domain-
    neutral adapter remain call-time root seams; the other capability wrappers
    remain separate.
  - B-11c21 moves only `_run_aio_postprocess_stage` to the existing AiO
    postprocess owner in PR #315 / `8b3ba38`. Coercion, image-size, final-fit,
    and logger dependencies remain call-time root seams. The later E-07
    provider bridge resolves the max-resolution dependency before B-11c29a
    retires its unsupported root wrapper.
  - B-11c22 moves only `_run_aio_highres_stage` to the existing AiO legacy-
    generation owner in PR #316 / `9250610`. Sampler planning, scaler
    construction, VAE, model-patch, sampling, cleanup, resize, and metadata
    helpers remain call-time root seams; execution order and the legacy caller
    lookup remain unchanged.
  - B-11c23 moves only `_run_aio_upscale_stage` to the existing AiO legacy-
    generation owner in PR #317. Boolean coercion and both leaf stages remain
    call-time root seams; disabled, USDU, ResShift, unsupported-backend, and
    exception behavior remain unchanged.
  - B-11c24 moves only `_run_aio_detailer_stage` to the existing AiO legacy-
    generation owner in PR #318 / `2abc54d`. Target planning, SAM3 context,
    target-leaf execution, callbacks, and metadata access remain call-time root
    seams; order, chaining, and exception behavior remain unchanged.
  - B-11c25 moves only `_run_aio_resshift_upscale_stage` to the existing AiO
    legacy-generation owner in PR #319 / `5e2b335`. Provider lookup, tuple
    normalization, seed/coercion, and image-size access remain call-time root
    seams; exact errors and result identity remain unchanged.
  - B-11c26 moves only `_run_aio_detailer_target` to the existing AiO legacy-
    generation owner in PR #320. Sampler planning, model patching, SAM3 Detailer,
    coercion, cleanup, SEGS, and metadata helpers remain call-time root seams;
    kwargs, cleanup timing, result parsing, and exception behavior remain
    unchanged.
  - B-11c27 moves only `_run_aio_usdu_upscale_stage` to the existing AiO legacy-
    generation owner in PR #321. Provider lookup, model loading, tile planning,
    logging, conditioning, model patching, seed/coercion, cleanup, tuple, image-
    size, constant, and metadata helpers remain call-time root seams. The named
    temporary owner exceeds the size review trigger; #169 owns later stage
    decomposition after its Contract work, not this Move.
  - B-11c28 moves only `_resize_image_to_size_if_needed` to the existing AiO
    postprocess owner in PR #322. Root and canonical identity remain a direct
    alias while the existing postprocess binder resolves image size and the
    Comfy upscale adapter at call time. Clamp and tensor-layout order, the
    same-size identity short-circuit, method fallback, return tuple, and raw
    exception propagation remain unchanged. Host-provider, stage, schema,
    seed-reservation, and RuntimeServices contracts remain separate.
  - B-11c29a retires only `_comfy_max_resolution` in PR #329. The E-07b wiring
    keeps installed-runtime consumers on `ComfyHostProvider.max_resolution`
    and flat pre-bootstrap consumers on a fresh default provider. Lookup order,
    integer conversion, and the `16384` fallback remain unchanged.
  - B-11c29b1 retires only `_find_comfy_node_mapping_class` in PR #330.
    Installed-runtime SAM3 consumers use the provider mapping method and flat
    pre-bootstrap consumers use a fresh default provider. Attribute and
    loaded-module scanning remain excluded from this lookup.
  - B-11c29b2 retires only `_find_loaded_node_class` in PR #331. Installed
    runtime and flat pre-bootstrap consumers resolve the provider method without
    caching or importing optional packs. General lookup and current loaded-module
    order remain unchanged.
  - B-11c30c changes no production code. It splits the audited Prompt/Regional
    binder family into the six service owners under `easyuse_anima.prompt` and
    the four ComfyUI node adapters under `easyuse_anima.nodes`. The gate keeps
    all ten symbols, callers, modes, provider/root resolver names, bound globals,
    direct dependencies, and repository replacement evidence unchanged. Each
    subgroup must retire in a separate Move PR; no service and adapter binder
    removal may be combined.
  - B-11c30c1 retires only the six service binders under
    `easyuse_anima.prompt`: Regional, Advanced, Conditioning, Artist Mix,
    Prompt Fields, and Prompt Correction. Canonical services resolve canonical
    feature helpers and the existing E-07 Comfy host provider at call time.
    Node-adapter binders, schemas, mapped classes, prompt/conditioning behavior,
    provider lookup order, warning-once state, and saved workflows remain
    unchanged. B-11c30c2 owns the four node-adapter binders separately.
  - B-11c30c2 changes no production code. Its inventory proves that Prompt Data
    and Classic Prompt adapters have complete canonical/provider owners and form
    B-11c30c2a. Advanced and Regional still resolve
    `_consume_reserved_wildcard_next_seed` through their root binders from real
    build paths; they form B-11c30c2b. S167-01 / PR #343 freezes the
    request/service contract. S167-01a / PR #344 moves the consumer to
    `easyuse_anima.seed.compatibility` and leaves a direct root alias without
    changing behavior. B-11c30c2b must retire the two binders separately.
  - B-11c30c2a retires only `_bind_prompt_data_node_runtime` and
    `_bind_prompt_node_runtime` in PR #342. Prompt Data uses canonical
    prompt/AiO owners plus the existing E-07 CLIP provider at call time;
    Classic Prompt uses its canonical prompt, settings, and legacy
    knowledge-base owners directly. Advanced/Regional binders and
    seed-reservation behavior remain outside this Move.
  - B-11c30c2b retires only `_bind_prompt_advanced_node_runtime` and
    `_bind_regional_node_runtime` in PR #345. Both adapters import canonical
    common, Prompt, workflow, and S167-01a seed owners directly. Regional keeps
    CLIP encoding behind the existing E-07 provider, while Advanced reuses the
    Prompt service's call-time Wildcard module resolver to preserve
    optional-dependency timing. Fourteen AiO and Wildcard/NAIA binders remain.
  - B-11c30d changes no production code. It freezes the twelve AiO binders into
    six non-overlapping retirement groups, records incremental active/retired
    state, and identifies d0a and d0b as separate cycle-breaking owner Moves.
    d1 is independent of those prerequisites and remains separate from #169
    cache Behavior.
  - B-11c30d1 retires only `_bind_aio_first_pass_cache_runtime` in PR #347.
    The cache module directly owns its existing limit/state/clone calls and
    imports the three existing canonical helpers. Root cache aliases and all
    cache semantics remain unchanged. Thirteen AiO and Wildcard/NAIA binders
    remain.
  - B-11c30d0a moves only `_normalize_aio_hash_bundles` and
    `_normalize_aio_civitai_hash_fetchers` to
    `easyuse_anima.aio.output_settings` in PR #348. Generation normalization
    uses the pure owner directly, output re-exports the same objects, and root
    aliases retain identity. No binder or settings/save behavior changes.
  - The final B-11c cutover removes remaining root execution ownership and
    leaves the explicit supported `nodes.py` compatibility shim.
- Add `easyuse_anima/registration.py` as pure mapping composition. It performs no
  file I/O, route registration, capability discovery, service construction, or
  cache creation.
- Add `easyuse_anima/bootstrap.py` as the guarded owner of existing route and
  wildcard-directory initialization. This is the minimal Phase B bootstrap; do
  not introduce the full Phase E `RuntimeServices` in this PR.
- Make repeated initialize/import calls safe and prove route/directory work is
  not duplicated.
- Reduce root `__init__.py` to the ComfyUI entrypoint and one guarded bootstrap
  call while preserving `NODE_CLASS_MAPPINGS`, display mappings, and
  `WEB_DIRECTORY` identity/order.
- Reduce root `nodes.py` to explicit supported direct re-exports and `__all__`.
  It must contain no node execution, prompt processing, SAM3/AiO sampling,
  cache, preview, save, or metadata implementation.

Phase B exits only when:

- every mapped node class is canonical and root identity parity passes;
- node/workflow fixtures and representative `IS_CHANGED` behavior pass;
- internal package-to-root imports are zero;
- registration is pure;
- bootstrap/import is idempotent;
- full, `comfy node validate`, actual pack, archive closure, and representative
  live ComfyUI execution pass;
- the compatibility registry reflects the actual shipped surface.

## 10. Post-Phase-B Contract and Behavior sequence

### S167 — Backend seed reservation (#167)

Split into at least these rollback units:

1. **S167-01 Contract:** concrete seed payload/service interface and compatibility
   parsing for legacy `-1/-2/-3`; no reservation behavior change.
2. **S167-02 Behavior:** authoritative, atomic random/increment/decrement
   reservation including concurrent queue, failure, retry, and cancellation
   transitions.
3. **S167-03 Adapter:** browser queue interceptor becomes a compatibility/display
   adapter; headless and browser behavior parity is proven.

S167-01 uses
[`seed-reservation-contract.md`](seed-reservation-contract.md) as its exact
symbol/caller/alias/global-state inventory and allowed-file gate. The contract
does not itself move the root Prompt Studio compatibility consumer. That
behavior-preserving owner Move is S167-01a. It and B-11c30c2b remain separate
rollback units before S167-02. PR #343 completes the contract without changing
any existing runtime, payload bytes, or reservation behavior. S167-01a uses the
same document for its exact Move inventory and allowed-file gate. PR #344
completes that Move while preserving the root aliases and both node-adapter
binders for B-11c30c2b. PR #345 then retires those two binders without changing
the seed contract or beginning S167-02 Behavior.

Do not mix this sequence into B-09 or #169 stages.

### A169 — Stage pipeline (#169)

Recommended PR order:

1. A169-01 current-order trace plus `GenerationRequest`/`GenerationState` and
   stage protocol Contract;
2. A169-02 First pass stage;
3. A169-03 Highres stage;
4. A169-04 Detailer stage;
5. A169-05 Upscale stage;
6. A169-06 Postprocess stage;
7. A169-07 Save/output stage;
8. A169-08 resource/temporary-model/preview cleanup ownership;
9. A169-09 final adapter simplification and integration matrix.

Use one stage per Behavior PR unless two are demonstrably inseparable. Each PR
proves disabled no-op, pre-sampling validation, exception cleanup, metadata,
preview order, image/latent dimensions, and output parity.

### A169-CACHE — First-pass cache policy

This is a separate Behavior series after the mechanical B-08e move and a stable
orchestration seam:

1. benchmark and mutation-isolation harness;
2. immutable entry/copy-on-write contract;
3. byte budget and single-entry cap;
4. TTL, LRU, clear/disable, and resource-revision invalidation;
5. concurrency and metrics;
6. 4K/batch allocation and hit-latency evidence.

Do not remove cloning merely because it appears expensive. Change it only after
mutation isolation and peak-allocation benchmarks prove the replacement.

## 11. Phase D — Canonical root-module consolidation

Keep #186's D task identifiers, but execute leaf feature ownership before route
adapters whenever the current import graph permits it. The default dependency-
first order is:

1. D-01 translation;
2. D-08 generic filesystem primitives;
3. D-09 settings;
4. D-10 profiles;
5. D-11 autocomplete;
6. D-12 wildcard;
7. D-13 `anima_prompt`;
8. D-02 API requests/responses/errors;
9. D-03 through D-07 feature routes and router composition;
10. D-14 root shim surface freeze.

D-02 may run earlier in parallel if it remains a pure Contract/Move and does not
pull route adapters ahead of their feature services. The actual import graph,
not numeric task order, decides whether two D tasks are independent.

Every D PR moves one root implementation surface, updates internal consumers to
the canonical path, leaves an explicit root shim, and proves root/canonical
identity plus packed-archive closure. Behavior, error semantics, migration,
ranking, async, and cache changes remain in their owner issues.

## 12. Phase E — Runtime ownership and lifecycle

E-01 global-state inventory may start after Phase B establishes final node and
bootstrap surfaces. Feature ownership migration waits until that feature's D
move is complete.

Recommended sequence:

1. E-01 inventory every mutable global with owner/lifetime/lock/cleanup/test;
2. E-02 `RuntimeConfig`, base runtime factory, clock/executor/client ports;
3. E-03 settings/profile repositories and filesystem factory;
4. E-04 translation provider/client/cache;
5. E-05 autocomplete source/index/single-flight state;
6. E-06 wildcard snapshots;
7. E-07 Comfy capability/resource lookup;
8. E-08 seed/AiO cache owners from #167/#169;
9. E-09 idempotent initialize/shutdown and reverse partial-failure cleanup;
10. E-10 isolated runtime fixtures and removal of module reload/private-global
    reset patterns.

Feature services receive only narrow Protocols. They do not import or receive
the entire `RuntimeServices` object. Node adapters may use `get_runtime()` only
at the ComfyUI construction boundary.

## 13. Quality and decomposition lane

### G-04 — Public API snapshot

After B-10, snapshot explicit `__all__`, mapped classes, root/canonical identity,
public schema/result types, and actual Registry archive closure. Private helper
names are excluded unless consumer evidence explicitly supports them.

### G-05 — Size and complexity ratchet

The current Advanced Prompt move intentionally preserved behavior but left two
large canonical modules at the snapshot:

- `easyuse_anima/nodes/prompt_advanced_nodes.py`: 1,157 lines;
- `easyuse_anima/prompt/advanced.py`: 893 lines.

Do not re-mix behavior into a corrective split. Create reviewed Move tasks after
the Phase B interfaces settle:

1. separate adapter metadata/raw conversion from execution/runtime binding;
2. separate field schema/normalization from prompt assembly;
3. isolate wildcard/translation/NAIA integrations behind narrow call-time ports;
4. keep all public node classes as the same canonical objects;
5. add size-growth gates only after the responsibility boundaries are real.

Apply the same rule to any temporary `aio/legacy_generation.py`: #169 is its
named decomposition owner and it must not become a permanent monolith.

### G-06 — Test ownership

Move canonical behavior tests next to feature ownership conceptually while
retaining the repository's `unittest` runner. Distinguish:

- pure service/model tests;
- adapter integration tests;
- compatibility-shim identity tests;
- workflow/API/persistence contract fixtures;
- package/archive tests;
- live ComfyUI smoke records.

A compatibility test may import a root shim. A canonical service test may not.

### Phase H — Shim retirement

Apply ADR-002 literally. Release `N` is the first published Registry release
containing both a canonical target and its root shim. No shim is removed during
release `N`; later removal still requires every evidence gate. Public mapped
node re-exports may remain indefinitely when evidence is insufficient or their
maintenance cost is low.

## 14. Validation matrix by PR type

| Gate | Move | Contract | Behavior |
| --- | :---: | :---: | :---: |
| Compile, focused tests, full runner, diff check | Required | Required | Required |
| Analyzer/import/package-closure update | Required when paths move | Required when public/package surface changes | Required when dependencies change |
| Root/canonical identity | Required for moved supported symbols | Required for public types | Required if public object changes |
| Golden deep equality/parity | Required | Required | Baseline plus intentionally approved delta |
| Benchmark | Only to prove no accidental regression when relevant | When contract includes limits | Required for cache/performance policy |
| Live ComfyUI smoke | Required for high-risk node/entrypoint moves | Required when workflow/UI payload changes | Required for execution behavior |
| `comfy node validate` and actual pack | Required for package/entrypoint moves | Required for package/public changes | Final integration and release |
| Rollback boundary | One mechanical slice | One interface/schema unit | One behavior/policy unit |

## 15. Per-task Definition of Done

A work unit is DONE only when all applicable items are true:

- [ ] prerequisites were verified against the actual starting SHA;
- [ ] PR has exactly one Move/Contract/Behavior classification;
- [ ] inventory and owner boundaries are recorded;
- [ ] forbidden changes did not occur;
- [ ] focused tests and official full runner pass;
- [ ] no new Pyright diagnostic group or canonical import violation exists;
- [ ] public/workflow/API/persistence parity passes as applicable;
- [ ] compatibility aliases are direct, explicit, evidenced, and registered;
- [ ] package/archive closure passes when paths changed;
- [ ] live smoke is recorded or explicitly marked unexecuted with reason;
- [ ] rollback is limited to this task's owner surface;
- [ ] residual debt has an owner issue and does not rely on an undocumented
      temporary exception;
- [ ] owning issue receives the merge SHA, test evidence, and next task;
- [ ] this queue is updated when the critical path or prerequisites changed.

## 16. Codex start instruction

Use the following instruction without redesigning the roadmap:

```text
Read docs/architecture/python-backend-execution-roadmap.md first, then the
owning issue and architecture/ADR files it links. Fetch current dev and search
for an existing branch or PR with the task ID. Select the first READY task whose
prerequisites and allowed-file boundary still hold. Record an inventory before
editing. Implement one Move, Contract, or Behavior unit only. Run focused tests
and tools/check_project.ps1 -Profile full. Stop and document a blocker instead
of crossing a forbidden behavior or compatibility boundary. Open a draft PR to
dev with exact SHA, validation, live-smoke status, rollback boundary, and the
next task. Do not merge or release as part of the implementation task.
```

At this snapshot the default first task is **B-07f SAM3**. If another active PR
already owns B-07f, take **C168-03**. If both are owned, take **G-02b**. Do not
start B-08 or B-09 until #168's remaining exit conditions are complete.
