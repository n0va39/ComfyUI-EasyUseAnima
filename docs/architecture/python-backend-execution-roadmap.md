# Python Backend Refactor Execution Roadmap

## Document status

- Status: operational execution runbook
- Snapshot date: 2026-07-22
- Snapshot branch: `dev`
- Snapshot commit: `9827dab527d1346ce8fc8aad28e6cd903fde36a9`
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

| Phase | State at the snapshot | Remaining exit work |
| --- | --- | --- |
| A - baseline | Complete; #191 is closed | Keep fixtures and analyzers current during later moves |
| B - `nodes.py` extraction | In progress through B-08d1 | Continue B-08d2 through B-09 AiO extraction, compatibility audit, registration/bootstrap, final root shim |
| C - feature contracts/behavior | Partially complete | Finish #168; then #167 and #169 in separate Contract/Behavior PRs |
| D - root consolidation | Not started | Execute #186 feature by feature after the corresponding behavior contracts are stable |
| E - runtime ownership | Not started | Execute #187 after canonical feature owners exist; E-01 inventory may start earlier |
| F - typed boundaries | Partial patterns exist | Extend typed request/result/config and pure migration patterns feature by feature |
| G - quality ratchet | G-01, G-02a/G-02b, and G-03a complete | Extend G-03 enrollment, then continue with G-04 through G-06 |
| H - shim retirement | Not started | Requires canonical release evidence and ADR-002 gates |

### Measured Phase B progress

- The Phase A baseline recorded root `nodes.py` at 12,663 lines.
- At the B-08d1 snapshot, root `nodes.py` is 3,527 lines.
- The mechanical extraction has therefore removed 9,136 lines, approximately
  72.2% of the baseline, while preserving the root compatibility surface.
- B-01 through B-08d1 are integrated. The latest completed slice is the AiO
  preview runtime Move in PR #263.
- Root `nodes.py` still owns substantial AiO implementation.
- Root `__init__.py` still imports `api.py` for route-registration side effects,
  initializes the wildcard directory during package import, and owns mapping
  composition. B-11 is therefore not complete.

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

The ordering below is the default critical path at the snapshot. B-07f,
C168-03, and G-02b may proceed in parallel because they should own disjoint
surfaces. AiO mechanical extraction must not start until #168 exits.

| Order | Task | State | Type | Owner | Prerequisites |
| ---: | --- | --- | --- | --- | --- |
| 1 | B-07f SAM3 mechanical vertical slice | COMPLETE on `dev` | Move | #184 | PR #251 / `015b8197` |
| 2 | C168-03 typed AiO config boundary | COMPLETE on `dev` | Contract | #168 | PR #252 / `7f686bed` |
| 3 | G-02b strict-clean pure/service allowlist | COMPLETE on `dev` | Contract/gate | #188 | PR #254 / `76237a60` |
| 4 | C168-04 pure version-dispatch/migration registry | COMPLETE on `dev` | Contract | #168 | PR #255 / `29aa200e` |
| 5 | C168-05 cross-surface setting omission gate | COMPLETE | Contract/gate | #168 | PR #256 merged |
| 6 | G-03a completed-package import boundary fail gate | COMPLETE on `dev` | Contract/gate | #188 | PR #258 / six reviewed zero-violation prefixes enrolled |
| 7 | C168-06 normalizer ownership move | COMPLETE on `dev` | Move | #168/#184 | PR #257 / `3ca5500` |
| 8 | B-08a through B-08e AiO support-helper extraction | B-08a/B-08b1/B-08b2/B-08c/B-08d1 COMPLETE; B-08d2 READY/SEQUENTIAL | Move | #184 | B-08a PR #259; B-08b1 PR #260; B-08b2 PR #261; B-08c PR #262; B-08d1 PR #263; later slices remain sequential |
| 9 | B-09a/B-09b AiO node and legacy orchestration move | BLOCKED by B-08 | Move | #184 | AiO helpers canonical |
| 10 | B-10 compatibility/private-alias audit | BLOCKED by B-09 | Contract/cleanup, split PRs | #184/#188 | All node implementations canonical |
| 11 | B-11 registration/bootstrap/root shim | BLOCKED by B-10 | Move | #184 | Alias surface frozen |
| 12 | S167 backend seed reservation series | BLOCKED by B exit/interface | Contract then Behavior | #167 | Canonical AiO/node seams |
| 13 | A169 stage pipeline series | BLOCKED by #168 and B exit | Contract then Behavior | #169 | Typed config and mechanical AiO move |
| 14 | A169 first-pass cache policy | BLOCKED by stage/cache ownership seam | Behavior | #169 | Mechanical cache move and benchmark harness |
| 15 | D-series canonical root consolidation | BLOCKED by relevant C contracts | Move | #186 | Phase B exit; per-feature behavior stable |
| 16 | E-series RuntimeServices/lifecycle | BLOCKED by canonical owners | Move/Contract, split PRs | #187 | Relevant D moves |
| 17 | G-04 through G-06 and H | INCREMENTAL/LATER | Gate/Contract | #188 | Appropriate package and release evidence |

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
- Test-only imports must migrate to canonical paths; they do not justify a root
  alias.

### B-10b — Private alias reduction

- **Type:** small compatibility cleanup PRs, one owner/surface at a time
- Remove unsupported/test-only aliases after tests use canonical paths.
- Retain an actual monkeypatch seam only when the consumer and call-time binding
  contract are documented and tested.
- Do not remove mapped public node-class re-exports in Phase B.
- Do not combine alias removal with feature behavior changes.

### B-11 — Registration, bootstrap, and final `nodes.py` shim

- **Owner:** #184
- **Type:** Move
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
