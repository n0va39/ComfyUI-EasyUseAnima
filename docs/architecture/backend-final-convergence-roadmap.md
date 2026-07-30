# Backend Final Convergence Roadmap

## Status and authority

- Status: FC ownership/lifecycle convergence complete; mandatory Total Python
  Convergence extension active.
- Technical completion owner: reactivated Issue #593.
- Parent architecture: reactivated Issue #185.
- Compatibility ledger: Issue #186 and ADR-002.
- Lifecycle authority: E-09 / Issue #187.
- Current released baseline: 0.6.2.
- Current completed lanes: Phase D, Phase E, Phase F, G-04/G-05/G-06, P-WC,
  P-API-01, G-CLOSE, and SEC-01 through SEC-05.
- FC-01 audit base: `81e07c6c12c21f84ba0642c93d6655c8936b7c3b`.
- Completed final-convergence lanes: FC-01, FC-02A through FC-02D, FC-03A,
  FC-03B, FC-04A, FC-04B and FC-05.
- Completed extension lane: PTC-01 inventory/target Contract.
- Current READY technical task: PTC-02 AiO generation normalization Move.

The FC results remain valid for their original ownership/lifecycle Definition of Done.
[`python-total-convergence-contract.md`](python-total-convergence-contract.md) adds the
blocking per-file, size-exception and final root-cutover requirements. It does not reopen
completed Phase F/G or security work. Root deletion is authorized only in PTC-09B after
the production-free PTC-09A lifecycle/caller Contract; release, tag and Registry remain
separate operations.

## 1. Total-convergence extension after FC completion

FC-01 through FC-05 close the original ownership/lifecycle Definition of Done. The
complete role-aware owner gate, canonical API application, bootstrap-owned E-09
lifecycle and integrated validation remain authoritative.

PTC-01 found the broader completion gap: the former optional large-module lane did not
classify all 183 shipped files, did not close all 31 size exceptions, and retained 16
legacy import modules. The accepted target now requires zero unclassified files, 16
responsibility-owned canonical additions and removal of every non-entrypoint root/
`anima_prompt` compatibility module after canonical caller cutover.

## 2. FC completion and current total-convergence completion

### FC technical architecture completion (historical)

This state was reached before release N:

- `easyuse_anima` owns all production implementation;
- root Python files are the permanent entrypoint or explicit compatibility
  facades/shims;
- every canonical owner group has a blocking role-aware import/dependency gate;
- root `api.py` no longer creates the production application/runtime composition;
- bootstrap remains the single E-09 lifecycle owner;
- route, payload, error, workflow, profile, settings, node and object-identity contracts
  remain compatible;
- full, package/archive, no-host, lifecycle and representative host/API gates pass.

### Total Python convergence completion (current)

This state is blocking technical work, independent of release timing:

- all 183 current Python source files have one executable disposition;
- all 31 size exceptions have one explicit disposition and task/retain evidence;
- 16 responsibility-owned canonical files are added by the approved split tasks;
- the nine non-entrypoint root files and seven `anima_prompt` compatibility files are
  removed by PTC-09B after canonical caller and E-09 lifecycle proof;
- the final shipped Python target remains 183 files with root `__init__.py` as the only
  root production Python file;
- no replacement compatibility facade recreates a deleted legacy import path.

## 3. Ordered execution queue

```text
FC-01        original Definition-of-Done closure audit
  -> FC-02A  Prompt runtime-SCC correction
  -> FC-02B  AiO adapter-back-reference Contract
  -> FC-02C  cohesive AiO adapter-back-reference Move
  -> FC-02D  complete canonical owner-boundary gate
  -> FC-03A  root API patch-owner compatibility Contract
  -> FC-03B  canonical dependency/patch-owner Move
  -> FC-04A  canonical API application + E-09 lifecycle Contract
  -> FC-04B  cohesive production application Move
  -> FC-05   technical completion audit

EVENT FC-06  next ordinary release N
  -> FC-07   later H/D-14 compatibility re-audit
```

Only one FC task is active by default.

## 4. FC-01 — Original Definition-of-Done closure audit

Type: Contract/audit; production-free.

Map every checkbox in `python-backend.md` to current deterministic evidence and classify
it as:

```text
complete
technical gap
compatibility event
deliberate retain
```

Required checks:

- compare the import-boundary checker's reviewed groups with the complete G-06 owner
  groups and exact top-level canonical owners;
- confirm whether adapters, feature packages, infrastructure, nodes/registration and
  runtime/bootstrap have the intended role rules;
- map each root file to permanent entrypoint, explicit shim/facade, or remaining
  implementation;
- reuse P-API-01's exact root symbol and patch-time inventory;
- map E-09, typed/migration, public identity, package/archive, validation and shim gates;
- identify the exact technical tasks required before FC-05.

Do not create a duplicate inventory when the analyzer, compatibility fixture, G-06 map,
Pyright/import ledgers or direct tests already own the evidence.

Exit:

- confirm or correct the FC-02 through FC-04 task boundaries;
- publish one compact closure matrix;
- select FC-02 as READY unless the audit proves a smaller prerequisite.

### FC-01 result

The audit at `81e07c6c12c21f84ba0642c93d6655c8936b7c3b` proves that a
gate-only FC-02 is not yet valid.

- The current import contract enrolls 11 package prefixes and passes its direct
  owner. The G-06 map owns 16 groups: 15 canonical package groups plus
  `runtime-bootstrap`.
- The G-06 production paths cover all 158 non-facade canonical Python modules.
  `easyuse_anima/__init__.py` is the one intentional package-facade exception.
- The current 11-prefix gate omits the complete `aio`, `nodes`, `prompt`,
  `runtime-bootstrap`, `seed`, and `wildcard` groups. It also omits the
  G-06-owned top-level paths `errors.py`, `workflow.py`, and
  `registration.py`, and does not enroll `infrastructure/__init__.py` through
  its two current subpackage prefixes.
- Projecting the current analyzer through the reviewed role rules finds two
  real owner-boundary defects: the two
  `aio/legacy_generation.py -> nodes/{image_nodes,sam3_nodes}.py` imports and
  the runtime SCC formed by `prompt/advanced.py` and `prompt/artist_mix.py`.
  These are production corrections, not gate allowlist candidates.
- `nodes/seed_adapters.py -> runtime.py` and
  `infrastructure/comfy/wiring.py -> runtime.py` are not defects. They are the
  already documented, exact call-time `get_runtime()` seams at node and Comfy
  host-adapter boundaries. The full gate must encode that narrow rule instead
  of broadly allowing adapter-to-composition imports.

The G-06 map remains the sole production-path inventory. FC-02D derives paths
from it and stores only role assignments and exact subrole overrides in the
import contract.

#### Final Definition-of-Done reconciliation

| # | Original row | Classification | Current evidence or remaining work |
|---:|---|---|---|
| 1 | `easyuse_anima` is the only production implementation root | **complete** | FC-04B gives the canonical package the publish-once application identity and complete production composition; root `api.py` only binds compatibility aliases and publishes the selected route table. |
| 2 | Root Python files are a permanent entrypoint or registered shims | **complete** | Root `__init__.py` is the permanent ComfyUI entrypoint and every other root file is an explicit compatibility facade/shim with a ledger disposition. |
| 3 | Node/API adapters contain conversion and service delegation, not repository/HTTP/migration/cache implementation | **complete** | Phase F/G owner tests and the direct API/node contracts own the intentional adapter boundaries. |
| 4 | Feature/domain/infrastructure code has no outer adapter, registration, bootstrap, or root back-reference | **complete** | FC-02A and FC-02C remove the Prompt SCC and both AiO adapter back-references; the blocking gate rejects recurrence. |
| 5 | The final owner matrix is enforced by the import gate | **complete** | FC-02D derives all production paths from the G-06 map and enforces 16 role-aware owner groups plus exact subrole rules. |
| 6 | Every runtime cache/lock/client/executor/repository/capability has an owner, lifetime, thread model, and cleanup disposition | **complete** | E-01 inventory, E-09 lifecycle contract, and E-09 completion audit have zero ambiguous owners. |
| 7 | Initialization and shutdown are idempotent, including partial failure | **complete** | E-09 owns serialized initialize/shutdown, terminal shutdown, bounded retry, and attempt-only rollback. |
| 8 | Optional dependency failure is contained | **complete** | The no-host/package owners and completed E-02/E-07 contracts retain lazy, bounded failure. |
| 9 | Runtime tests isolate user data and avoid private-global/reload cleanup | **complete** | E-10 owns the deterministic runtime test-isolation contract. |
| 10 | Settings/profile/workflow data is versioned, purely migrated, and atomically written at the persistence boundary | **complete** | The Phase F completion audit and existing schema/migration fixtures close this row. |
| 11 | API and feature boundaries use typed request/result/error contracts | **complete** | F-01/F-02a through F-02h close all six typed-boundary areas or name their intentional adapter/migration boundary. |
| 12 | 0.5.2 workflow/settings/profile/API fixtures pass | **complete** | Existing migration, compatibility, and API fixtures remain the deterministic owners. |
| 13 | Supported root/canonical surfaces preserve object identity and metadata parity | **complete** | G-04, the compatibility-surface fixture and FC-04 lifecycle owners prove exact supported identity, including the application/executor/handler/registrar graph. |
| 14 | The actual Registry package contains the final canonical/shim closure and imports with providers off | **compatibility event** | The current final shim forms need ordinary release N and Registry read-back. FC-05 owns the pre-release package proof; FC-06 owns publication. |
| 15 | Ruff and Pyright are pinned and enforced | **complete** | The official quality runner and current baselines own this row. |
| 16 | Cycle, forbidden-import, public-API, and size ratchets are in CI | **complete** | FC-02A/FC-02D close the SCC/import gaps; the current public-API, Pyright and size/complexity ratchets reject new debt. |
| 17 | Every implementation PR is classified as Move, Contract, or Behavior | **complete** | The completed phase ledgers and current task cards retain the classification. |
| 18 | Every root surface has a shim owner, evidence, and removal gate | **complete** | ADR-002 and `python-compatibility-shims.md` contain the complete current ledger. |
| 19 | Public compatibility surfaces are deliberately retained or removed only through a breaking-change event | **deliberate retain** | No root surface is removal-approved. Low-cost public shims remain supported until a later evidence-backed event. |
| 20 | Final full, quality, package/archive, compatibility, and representative host gates pass at integration/release | **complete** | FC-05 records the integrated full, quality, archive/no-host, lifecycle, 0.5.2 compatibility and isolated ComfyUI API/node execution evidence. Registry publication remains FC-06. |

#### Exact current role/group matrix for FC-02D

| G-06 owner/path | Import role | Allowed canonical direction | Additional prohibition or exact exception |
|---|---|---|---|
| Every `easyuse_anima/**/__init__.py` | package facade | reviewed exports from its owning group | No application/lifecycle creation, host I/O, registration side effect, compatibility fallback, cross-owner re-export, or root import. |
| Non-facade `common/`, `errors.py` | common | common | No feature, infrastructure, adapter, composition, or root imports. |
| Non-facade `infrastructure/filesystem/` | infrastructure-core | common, infrastructure-core | No feature meaning, host/node/API adapter, runtime, bootstrap, registration, or root imports. |
| Non-facade `infrastructure/comfy/` | Comfy host adapter | common, infrastructure-core, same host-adapter group | Only `wiring.py -> runtime.get_runtime` is an accepted runtime edge; no broad composition permission. |
| Non-facade `aio`, `autocomplete`, `image`, `lora`, `naia`, `profiles`, `prompt`, `seed`, `settings`, `translation`, `wildcard` | feature/service | common, infrastructure including host adapters, feature/service | No API/node adapter, registration, bootstrap/runtime, or root back-reference. |
| Non-facade `api/` except `api/router.py` | HTTP adapter | common, infrastructure, feature/service, same HTTP-adapter group | No node adapter, registration, bootstrap/runtime, or root import. A future `api/application.py` receives an exact composition override when introduced. |
| Non-facade `nodes/` and `workflow.py` | Comfy node/workflow adapter | common, infrastructure, feature/service, same node-adapter group | Only `nodes/seed_adapters.py -> runtime.get_runtime` is accepted; no API, registration, bootstrap, or root import. |
| `registration.py`, `api/router.py` | registration adapter | node adapters for `registration.py`; injected API primitives for `api/router.py` | Literal node mappings and injected route-table composition only. `api/router.py` may not import `api/routes`; neither owner may construct services, import runtime/bootstrap/root, or register at import time. |
| `bootstrap.py`, `runtime.py` | process composition/lifecycle | all canonical roles required by composition | No root import. Bootstrap remains the only production registration and lifecycle call site; runtime remains the installed-services access owner. |

All roles additionally reject canonical-to-root imports, compatibility fallback
imports, runtime SCCs, and unowned import-time registration side effects. Exact
path overrides take precedence over a package prefix so FC-03/FC-04 can add the
future API application as composition without weakening the rest of `api/`.

#### Root disposition at FC-01

| Root surface | Disposition | Closure owner |
|---|---|---|
| `__init__.py` | permanent ComfyUI entrypoint | package/entrypoint contracts |
| `api.py` | explicit compatibility binder/route facade | FC-03B/FC-04B canonical application ownership; FC-06 publication event |
| `nodes.py`, `settings.py`, `storage.py`, `autocomplete_index.py`, `prompt_translation.py` | explicit compatibility shims, deliberately retained | ADR-002 consumer/removal gates |
| `api_contract.py`, `autocomplete_dataset.py`, `wildcard_engine.py` | explicit compatibility shims awaiting release N | FC-06 compatibility event |
| `anima_prompt/__init__.py` and its six compatibility submodules | explicit package/submodule shims awaiting release N | FC-06 compatibility event |

There is no removal-approved root surface. FC-02 through FC-05 did not delete
or deprecate any of them, and FC-06 does not authorize removal.

#### FC-03 and FC-04 decisions fixed by FC-01

The exact FC-03 canonical patch owner is the private, import-pure
`easyuse_anima.api.dependencies.ApiApplicationDependencies` bundle. It owns the
mutable request/registration-time dependency slots or resolvers currently
spread across root late-bound, profile-operation, and payload helper cells. It
does not own feature implementations, route-registration behavior, or process
lifecycle, and it imports neither bootstrap nor the future application owner.

- `api/router.py` keeps handler ordering, route signature, resolver/registrar,
  and idempotent table registration.
- `bootstrap.py` keeps concrete route-factory, dependency, correlation, and
  single production registration/lifecycle composition.
- The named dynamic profile and translation error compatibility inputs remain
  supported as fields/resolvers of the canonical bundle. Their patch point
  moves to that owner; root may expose a read-only identity alias but not a
  second mutable cell.
- Transitional private patch seams move their test patch target to the bundle.
  Arbitrary assignment interception on the root module is not a required or
  acceptable design substitute, and `api.<private_name> = replacement` is no
  longer a supported patch target after its consumer moves. Root may retain
  read-only exact aliases for explicitly supported compatibility objects.
  Unsupported owner-inspection mirrors move to canonical tests.
- FC-03B introduces the bundle while application construction remains in its
  current location. FC-04 reuses that exact object in the canonical application;
  the dependency and application modules import neither bootstrap nor root.

FC-04 then introduces one immutable canonical application identity bundle. The
application owns only the executor, handlers, definitions/signature, registrar,
and compatibility identity view. Bootstrap still owns the sole lifecycle lock,
once-only `atexit`, terminal/idempotent shutdown, and cleanup plan. Construction
must occur before `bootstrap.initialize()` freezes the plan, the exact executor
remains cleanup item 1, the fixed seven-step cleanup and attempt-only rollback
remain unchanged, and direct canonical/no-host imports create neither the
application nor lifecycle state. Package entry followed by a late root `api.py`
import must resolve the same application/executor/handler/registrar identities
without a second registration or lifecycle state.

#### Work completed before FC-05

1. Break the Prompt runtime SCC without changing Prompt/Artist Mix behavior or
   compatibility identities.
2. Replace each AiO legacy call into a node class with one feature operation
   shared by the node adapter and AiO service.
3. Enroll the complete G-06 path set in the role-aware blocking gate.
4. Move the root API patch owner, then move the immutable application identity
   while preserving every E-09 invariant.
5. Run the integrated FC-05 evidence once on the resulting candidate.

The optional large-module lane is not otherwise reopened. Its Prompt and AiO
modules are FC-05 blockers only to the minimum extent required to remove these
observed owner/cycle violations.

## 5. FC-02 — Complete canonical owner-boundary gate

The FC-01 projection found two real defects, so FC-02 is now an ordered correction
queue followed by one Contract/tool gate. Do not add temporary allowlists for the
observed edges or SCC.

### FC-02A — Prompt runtime-SCC correction

```text
Task / Issue: #593 / FC-02A
Base SHA: latest dev after FC-01 merges
Goal: remove prompt/advanced.py <-> prompt/artist_mix.py from every runtime SCC
Allowed production:
  easyuse_anima/prompt/advanced.py
  easyuse_anima/prompt/artist_mix.py
  easyuse_anima/prompt/artist_mix_primitives.py (new private lower owner)
Allowed evidence:
  direct Prompt/Artist Mix/node compatibility tests
  analyzer/import/package owners and directly changed fixtures
  this roadmap and the compatibility registry when ownership wording changes
Preserve:
  Prompt Data/Advanced/Artist Mix payloads, ordering, defaults, parsing,
  conditioning, warnings, signatures, root/canonical symbol identity, __all__
Focused tests and purpose:
  Prompt service behavior; node adapter integration; root identity;
  analyzer SCC projection; import and package closure
Promotion gates:
  changed-file static, focused owners, git diff --check, official full once;
  validate/pack/archive because a shipped module is added; no live smoke
Stop conditions:
  any payload/conditioning/signature/identity change, a new SCC, or a public export
Next: FC-02B only
```

Move only the Artist Mix constants and parsing/config primitives consumed by
`advanced.py` into the lower owner. `artist_mix.py` re-exports the same objects,
while `advanced.py` imports the lower owner directly. The existing Artist Mix
service may then retain its narrow calls into Advanced without a reverse import.

### FC-02B — AiO adapter-back-reference Contract

Production-free. This Contract fixes the operation boundary before moving the
SAM3/Impact path, where schema, host capability timing, cleanup, and error order
are coupled.

```text
Task / Issue: #593 / FC-02B
Base SHA: latest dev after FC-02A merges
Goal: freeze the two node-independent operations that replace both AiO node calls
Allowed:
  docs/architecture/python-aio-adapter-backreference-contract.md (new)
  docs/architecture/backend-final-convergence-roadmap.md
  compatibility ownership wording only when the direct identity target changes
Read-only evidence:
  aio/legacy_generation.py; image scaling/SAM3 owners; image/SAM3/Impact adapters;
  direct image, SAM3, AiO legacy, node identity, analyzer and package tests
Forbidden:
  production, test, tool or shared-fixture changes; generic utility/service locator;
  node schema, feature behavior, root shim, lifecycle or public export changes
Required decisions:
  easyuse_anima/image/upscale.py::_upscale_image_by_multiple is the shared
    scaling operation called by the image node adapter and AiO
  easyuse_anima/image/sam3_detailer.py owns private Impact and SAM3 execution
    operations called by the Impact/SAM3 node adapters and AiO
  node classes retain metadata/signatures and delegate; feature code never
    instantiates or imports a node class
Focused validation:
  targeted document/source/test consistency and git diff --check;
  no official full, package or live run
Stop conditions:
  direct service ownership cannot preserve host lookup, kwargs, cleanup,
  result or error ordering without a Behavior Contract
Next: FC-02C only
```

FC-02B completed from `dev@9ed21c2aa58cf61ea37b04ec1bedb5084a5b8ca4`
with the production-free
`python-aio-adapter-backreference-contract.md`. The direct evidence converges on
one design: AiO and the image node share
`easyuse_anima.image.upscale._upscale_image_by_multiple`; AiO and the SAM3 node
share `easyuse_anima.image.sam3_detailer._run_sam3_detailer`; and that operation
and the Impact adapter share the same module's `_run_impact_detailer`. Host
provider lookup remains call-time, while AiO retains planning, ephemeral-model
cleanup, result inspection, metadata, and stage ordering. No Behavior Contract
or strengthened review is required before FC-02C.

### FC-02C — Cohesive AiO adapter-back-reference Move

```text
Task / Issue: #593 / FC-02C
Base SHA: latest dev after FC-02B merges
Goal: remove both legacy_generation -> node-class imports/invocations through
  the two operation owners fixed by FC-02B
Allowed production:
  easyuse_anima/aio/legacy_generation.py
  easyuse_anima/image/upscale.py (new private operation owner)
  easyuse_anima/image/sam3.py
  easyuse_anima/image/sam3_detailer.py (new private operation owner)
  easyuse_anima/nodes/image_nodes.py
  easyuse_anima/nodes/sam3_nodes.py
  easyuse_anima/nodes/impact_detailer_nodes.py
Allowed evidence:
  tests/test_image_scale.py
  tests/test_sam3_nodes.py
  tests/test_aio_legacy_generation.py
  directly affected node/analyzer/import/package owners and fixtures
  the FC-02B Contract, this roadmap, and compatibility wording when required
Preserve:
  image option normalization, interpolation and result tuple;
  SAM3 detection, mask/SEGS and Impact kwargs/order;
  disabled/empty short circuits, alignment, warnings, errors and cleanup;
  node metadata/signatures/results, AiO stage order, root identities and __all__
Exact private operations:
  easyuse_anima.image.upscale._upscale_image_by_multiple;
  easyuse_anima.image.sam3_detailer._run_sam3_detailer;
  easyuse_anima.image.sam3_detailer._run_impact_detailer
Additional fixed guards:
  empty mask/SEGS creation remains before the SAM3 enabled short circuit;
  SAM3, MaskToSEGS and DetailerForEach lookup remains call-time;
  Impact signature filtering preserves keyword insertion order;
  AiO owns stage planning and try/finally cleanup, then SEGS/metadata projection;
  both new modules remain private/import-pure with __all__ = ()
Focused tests and purpose:
  image and SAM3/Impact operation parity; AiO highres/detailer parity;
  node schema/identity; analyzer removal of both exact back-references;
  import and package closure
Promotion gates:
  changed-file static, focused owners, git diff --check, official full once;
  validate/pack/archive because shipped modules are added; no live smoke
Stop conditions:
  host capability timing, schema, kwargs, cleanup, result identity, error order,
  public export, or another owner direction must change
Next: FC-02D only
```

This is one rollback unit because both violations are the same AiO orchestration
owner invoking Comfy node adapters for reusable behavior. The adapters keep
their host-facing metadata; the shared image operations own execution.

FC-02C removes both exact `legacy_generation -> nodes` edges through the owners
fixed by FC-02B. The image, SAM3, and Impact node classes retain their original
host-facing schemas and method signatures while delegating to
`_upscale_image_by_multiple`, `_run_sam3_detailer`, and
`_run_impact_detailer`. Provider discovery remains call-time, AiO still owns
stage planning and `try/finally` model cleanup, and both operation modules have
empty public surfaces and no import-time side effects. The analyzer inventory
grows from 177 to 179 shipped modules, and the reviewed SAM3 function-size
exception moves from the node method to the exact shared operation. After the
cohesive Move merges, FC-02D is the only authorized next task.

### FC-02D — Complete owner-boundary Contract/tool

Use the G-06 production-path groups as the sole current owner inventory and the
existing AST analyzer as the sole import graph. Migrate the existing import
contract rather than creating another checker or path inventory.

```text
Task / Issue: #593 / FC-02D
Base SHA: latest dev after FC-02C merges
Goal: block every G-06 production path with the FC-01 role/direction matrix
Allowed:
  tools/check_python_import_boundaries.py
  tests/test_python_import_boundaries.py
  tests/fixtures/python_import_boundary_contract.v1.json (remove after migration)
  tests/fixtures/python_import_boundary_contract.v2.json (single replacement)
  docs/architecture/backend-final-convergence-roadmap.md
  direct import/analyzer/test-ownership documentation only when required
Forbidden:
  production changes, duplicated production-path inventory, broad allowlists,
  root-shim/lifecycle/application changes, public export or behavior changes
Focused tests and purpose:
  import contract validation and five universal rules; G-06 source-map equality;
  analyzer determinism; package facade/no-host import; quality-runner invocation
Promotion gates:
  changed-file static, focused owners, git diff --check, official full once;
  reuse package/live evidence
Stop conditions:
  any remaining real edge/SCC, an unclassified current path, role ambiguity,
  or a gate that can silently weaken when the G-06 map changes
Next: FC-03A only
```

The v2 contract references G-06 group names and derives their
`production_paths`; it records only group roles, exact subrole overrides, and
the exact package-facade rules. Longest exact-path matching precedes prefix matching.
It rejects canonical-to-root imports, forbidden role directions,
compatibility-fallback imports, runtime SCCs, and unowned registration side
effects. It preserves intentional adapter-to-feature, composition-to-adapter,
and the two exact adapter-time `get_runtime()` directions.

Exit: every current canonical production path is included in a blocking
role-specific owner gate or an exact permanent package-facade rule, with zero
real violations.

FC-02D replaces the 11-prefix v1 ledger with one v2 role contract. The checker
derives all 16 group names and every `production_paths` selector directly from
the G-06 test-ownership map, so an added, removed, or renamed owner cannot leave
the blocking gate silently unchanged. Four ordered path overrides distinguish
the API router, Comfy host adapter, registration owner, and workflow adapter;
only the two exact `get_runtime` imports are retained as edge exceptions. The
root package facade may import only the reviewed `seed` group, nested package
facades may import only their owning group, and every current canonical path
passes the five universal rules with zero violations. FC-03A is the only
authorized next task after this Contract/tool gate merges.

## 6. FC-03 — Root API patch-owner migration

P-API-01 retained root `api.py` because canonical candidates could not preserve both
E-09 timing and request-time root-global patch semantics. FC-03 intentionally satisfies
its first recorded revisit event before reevaluating application placement.

### FC-03A — Compatibility Contract

Production-free.

The completed Contract is
[`python-api-fc03-patch-owner-contract.md`](python-api-fc03-patch-owner-contract.md).
It reuses P-API-01's exact root inventory and fixes one private canonical
`ApiApplicationDependencies` bundle, seven typed leaf families, one canonical
private cell/root identity alias, call-time field patching, and the exact FC-03B
rollback boundary. It creates no duplicate machine inventory. Direct evidence
leaves one acyclic design, so FC-03B is READY after FC-03A merges and no PRO
review is required.

For each root API symbol family, classify:

```text
supported host/API behavior
supported named dynamic compatibility seam
transitional private patch seam
unsupported test-only owner inspection
production-only implementation detail
```

Required decisions:

- retain route methods, paths, order, signature, marker, response/error and request-ID
  behavior;
- retain the specifically supported dynamic profile/translation error seams;
- move repository-only owner inspection to canonical tests;
- assign request/registration-time mutable dependencies to the private
  `easyuse_anima.api.dependencies.ApiApplicationDependencies` patch/injection owner;
- define the minimum long-lived root facade surface;
- forbid a canonical-to-root back reference.

### FC-03B — Dependency/patch-owner Move

Introduce the typed/private
`easyuse_anima.api.dependencies.ApiApplicationDependencies` owner fixed by
FC-01. Do not add it to a public package `__all__`.

- handlers and registrar resolve supported call-time dependencies through that owner;
- root compatibility patching, where deliberately retained, targets the same canonical
  owner rather than a second root-owned cell;
- the named dynamic profile/translation error inputs remain supported at canonical
  patch points; transitional private seams also move to canonical patch targets;
- the dependency module imports neither bootstrap, the future application owner, nor
  a root module;
- test-only root mirrors are migrated to direct canonical owner tests;
- application construction remains in its current location during FC-03B;
- route behavior, payloads, errors, lifecycle, public exports and execution order remain
  unchanged.

Implementation ordering is exact: root application composition creates the
executor/helpers and uncalled handler closures, fixes the 21-route table and
signature, publishes one fully populated dependency bundle, then resolves the
initial host table and creates the registrar. The closures cannot be invoked
before publication. This preserves observable import and E-09 initialization
order while allowing the host family to own the final definitions/signature.

FC-03B is complete: all named request/registration-time seams now resolve the
single private canonical bundle, while root application/executor/handler and
E-09 lifecycle identities remain unchanged. Its #593-owned G-05A root-module
baseline is a reviewed transitional overage whose exact reduction boundary is
the FC-04B application move; further growth is forbidden. FC-04A is the only
next task.

Exit: a future canonical application can preserve every supported seam without importing
root `api.py`.

## 7. FC-04 — Canonical API application and E-09 convergence

### FC-04A — Lifecycle Contract

Production-free first. Define one immutable application bundle containing the exact
translation route executor, handlers, route definitions/signature, registrar and
compatibility identity view.

Frozen requirements:

- exactly one application and one translation route executor per process;
- application creation occurs before `bootstrap.initialize()` freezes the RuntimeServices
  cleanup plan;
- executor shutdown remains cleanup item 1;
- application construction remains outside initialize unless a separate Behavior
  Contract explicitly changes rollback timing;
- bootstrap remains the only lock/atexit/terminal/cleanup owner;
- no application `close`, reset registry, second lifecycle lock or hot reinitialize;
- entrypoint and late root API import resolve the same application identities;
- no canonical module imports a root compatibility module;
- direct canonical/no-host imports do not create the application or lifecycle state.

Compare only evidence-backed shapes after FC-03. Request focused technical PRO review
only when at least two shapes satisfy every lifecycle and compatibility condition.

FC-04A is complete in
[`python-api-fc04-application-lifecycle-contract.md`](python-api-fc04-application-lifecycle-contract.md).
The single feasible concrete shape combines a canonical publish-once immutable
application identity with bootstrap-owned private outer composition and a root exact
binder. FC-03B removed the former patch-time conflict; eager canonical construction,
root-direct factory ownership, bootstrap-owned application identity and continued root
production composition each fail at least one frozen owner/import gate. No PRO trigger
remains. FC-04B implements that selected shape as one cohesive Move.

### FC-04B — Cohesive Move

Expected production surface, subject to FC-04A:

```text
__init__.py
api.py
easyuse_anima/api/application.py
easyuse_anima/api/application_compatibility.py
easyuse_anima/api/application_routes.py
easyuse_anima/bootstrap.py
```

Together with direct tests, analyzer/contract fixtures and docs.

- move production application construction into the canonical package;
- have bootstrap private outer composition call the canonical application factory once
  before `initialize()` freezes the cleanup plan;
- make root `api.py` an explicit compatibility facade/binder over exact canonical
  objects;
- forbid `api/dependencies.py` and all `api/application*` modules from importing
  bootstrap or a root module;
- reduce root `api.py` below the 400-line adapter limit and keep every new application
  module below current adapter/function thresholds without a new exception;
- preserve E-09 cleanup order, rollback, repeated initialize, route refresh, terminal
  shutdown and late-import identity;
- preserve package/flat import and all supported host/API contracts.

This is one rollback unit. Do not split executor/application identity and entrypoint
wiring across separately deployable intermediate states.

FC-04B completes this Move with three private canonical composition modules:
`api/application.py` owns the publish-once immutable application identity,
`api/application_compatibility.py` owns guarded compatibility parts, and
`api/application_routes.py` owns explicit 21-handler wiring. Bootstrap has the sole
private production composition call site, while root `api.py` binds exact aliases and
publishes the selected route table. The three exact files are classified as
`process-composition` path overrides in the blocking import contract; the surrounding
`api` group remains an HTTP adapter. Root `api.py` is below 400 lines with its reviewed
exception removed, all three application modules pass existing size/function limits,
and the E-09 executor/cleanup identities remain unchanged. FC-05 was the only next task
after the cohesive Move merged and now records the integrated completion evidence below.

## 8. FC-05 — Technical completion audit

Type: integrated Contract/gate.

Reconcile the original Definition of Done after FC-04 and any mandatory FC-02 correction.

Required promotion evidence on one integrated candidate:

```text
official full
pinned Pyright/Ruff and complete owner-boundary gates
comfy node validate
actual comfy node pack and archive/CRC/import closure
root/canonical identity and no internal root implementation imports
no-host canonical imports
fresh-process E-09 terminal lifecycle
0.5.2 workflow/profile/settings/API compatibility fixtures
representative isolated ComfyUI API/node execution smoke
```

Record technical architecture completion and close the implementation lane of #185.
Issue #186 remains open only as the compatibility/release ledger.

### FC-05 result

The integrated code candidate is `dev@bb1452c9996293f1f77bb361e7317ddb2664ae19`.
Its tree is byte-for-byte identical to the validated FC-04B candidate
`2cd66806f0cd114cef051f52c7c7462328e5c8da`, so the code/full/package evidence is
reused without repeating the same broad gates after this documentation-only audit.

| Gate | Result |
| --- | --- |
| Official full | 1,490 Python tests and 120 frontend files passed on the identical FC-04B tree. |
| Pinned quality and complete ownership | Pyright checked 166 files with the existing 14-error baseline and zero new diagnostics; Ruff retained 128 report-only findings; 16 owner groups had zero violations; size/complexity passed. |
| Validate and actual archive | `comfy node validate` passed. The actual 0.6.2 archive had 325 entries, clean CRC, the complete application closure and SHA-256 `3470af5200110152aa2ef394616786fd4518572d546848b999076660cb9675c9`. |
| Identity, no-host and lifecycle | Package-to-late-API identity, canonical no-host imports, fixed E-09 cleanup, terminal shutdown, retry/rollback and root/canonical compatibility owners all passed on merged `dev`. |
| 0.5.2 compatibility | Node, AiO generation/schema, profile, settings and API compatibility owners passed on merged `dev`; the official full covers the remaining workflow fixtures. |
| Isolated ComfyUI | The canonical test install matched the merged source hashes, loaded once, served the settings route, exposed `EasyUseAnimaWildcard`, and completed a queued Wildcard-to-text workflow with `blue flower`; the owned server was then stopped with no listener or child process left. |

Verdict at the FC-05 checkpoint: **technical architecture completion was recorded.**
Rows 1 through 13, 15 through 18 and 20 were complete; row 14 remained the FC-06
Registry publication event and row 19 was a deliberate retain. PTC-01 later extended
the completion definition, so PTC-02 is now the READY backend refactor task.

## 9. Superseded optional MD lane — large-module disposition

After FC-01, audit the current G-05 exception ledger without changing production.
Classify each exception as:

```text
cohesive-retain
split-ready
blocked-by-contract
event-driven
```

Priority review candidates:

- `easyuse_anima/aio/generation_normalization.py`
- `easyuse_anima/aio/legacy_generation.py`
- `easyuse_anima/prompt/artist_mix.py`
- `easyuse_anima/nodes/prompt_advanced_nodes.py`
- `easyuse_anima/prompt/advanced.py`

Do not split the E-09 bootstrap lifecycle or the atomic JSON transaction owner merely
to satisfy a line threshold. Legacy root modules are removed only through the
PTC-09A/PTC-09B canonical caller cutover.

A split is allowed only when it has:

- independently named responsibility and owner;
- direct behavior/contract tests;
- measurable reduction in change collision or review scope;
- one bounded rollback unit;
- no new generic `utils`, `misc` or service-locator module.

The following historical FC rule is superseded by PTC-01: the MD lane was not an FC-05
blocker unless it found an owner/import violation or a module that prevented FC-03/FC-04
convergence.

## 10. Release N and H/D-14

### FC-06 — Ordinary release N

Do not publish solely for PTC. An ordinary pre-PTC feature/bug release remains valid but
does not satisfy total convergence. The first post-PTC release must record the exact tag,
SHA, archive hash, absence of the sixteen legacy paths, canonical entrypoint identity,
internal root-import scan and validate/pack/read-back.

### FC-07 — Later compatibility re-audit

This is now a historical compatibility re-audit lane. PTC-01 supersedes its release-window
prerequisite for the sixteen explicitly inventoried legacy paths. Issue #186 remains an
evidence ledger until PTC-09B/PTC-10 prove canonical callers, delete the paths and close
the rollback boundary; unrelated compatibility surfaces still follow ADR-002.

## 11. Validation efficiency

### Edit loop

```text
changed-file syntax/static
direct task-specific focused owners
current analyzer/contract projection
git diff --check
```

Do not run the broad quick/full suite in the edit loop.

### Promotion

- official full once on the exact final code/test/tool/fixture SHA;
- validate/pack/archive for import, entrypoint, registration, package or release changes;
- isolated live ComfyUI only for host-visible behavior or the FC-05 integrated gate;
- reuse evidence when only documentation changes and its source tree is unchanged.

Keep one active task by default. FC-02 and the optional MD audit may run in parallel
only when their allowed files and evidence owners are explicitly disjoint.

## 12. Stop and PRO conditions

Codex resolves ordinary implementation and focused-test failures inside the current
owner. Stop and request focused technical PRO review only when:

- FC-03 leaves multiple API application/lifecycle shapes that all satisfy E-09 and
  compatibility gates;
- executor-before-cleanup timing requires dynamic cleanup-plan mutation or a second
  lifecycle owner;
- a supported root seam cannot be represented without canonical-to-root import;
- the full owner gate exposes an actual cycle or ownership ambiguity not expressible by
  the reviewed role model;
- a behavior-preserving Move cannot be separated from lifecycle/compatibility Behavior.

## 13. Codex resume instruction

PTC-02 is READY after PTC-01 merges. Read only current policy/universal efficiency,
[`python-total-convergence-contract.md`](python-total-convergence-contract.md)'s PTC-02
card, Issue #593's latest checkpoint, the four allowed production files and direct tests.
Do not rerun FC-01 through FC-05 or the external reference audit.

Complete and merge one PTC task before starting the next. Root/API compatibility removal
does not start before PTC-09A fixes the canonical entrypoint and E-09 lifecycle sequence.
An ordinary bug-fix release may proceed in its own lane when independently required, but
it does not complete or replace the PTC queue and must not recreate removed shims.

## 14. Mandatory Total Python Convergence queue

The executable disposition, target tree, task cards, root cutover gate and corrected
Definition of Done are owned by
[`python-total-convergence-contract.md`](python-total-convergence-contract.md).

```text
COMPLETE  PTC-01 inventory/target Contract
READY     PTC-02 AiO generation normalization Move
NEXT      PTC-03 -> PTC-04 -> PTC-05 -> PTC-06 -> PTC-07A -> PTC-07B
          -> PTC-08 -> PTC-09A -> PTC-09B -> PTC-10
```

FC-06 release and Registry publication remain separate from this technical queue.
