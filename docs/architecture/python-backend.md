# Python Backend Architecture

## Document status

- Status: target architecture and migration contract
- Decision record: [ADR-001](adr-001-modular-monolith.md) and
  [ADR-002](adr-002-compatibility-shims.md)
- Primary tracking: [Issue #191](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/191)
- Baseline: `dev` commit `247252a97aba3d0fea3da23e5310dd1eecb8163b`,
  package/workflow compatibility version 0.5.2
- Scope: Python backend only

This document describes the state the backend must converge toward. It does not
mark a phase complete merely because its target is documented.

## Current implementation state

At the current Phase B state, the migration is in progress:

- The tracked `easyuse_anima/` production package contains common value and
  serialization primitives, image geometry/scaling and Detailer hook behavior,
  domain-neutral Comfy adapters, and the first vertical node adapter module,
  `easyuse_anima.nodes.image_nodes`.
- `nodes.py` directly re-exports the B-04 image-scale and Detailer-align objects
  while it remains the implementation module for the other mapped node classes
  and substantial Prompt, Regional, Wildcard, NAIA, LoRA, AiO, cache, save, and
  metadata behavior.
- Root `__init__.py` imports 18 mapped node classes from `nodes.py`, imports
  `api.py` for route-registration side effects, creates the default wildcard
  directory, and owns the node/display mappings.
- `api.py`, `settings.py`, `storage.py`, `autocomplete_dataset.py`,
  `wildcard_engine.py`, `prompt_translation.py`, and `anima_prompt/` are still
  implementation modules, not compatibility shims.
- Issue #165 Phase C adds root `api_contract.py` as a temporary implementation
  surface for JSON-object parsing, typed request fields, and additive stable
  error payloads. D-02 moves that responsibility to
  `easyuse_anima.api.requests`/`responses`/`errors`; D-14 freezes any root shim
  that consumer evidence still requires.
- PR [#189](https://github.com/n0va39/ComfyUI-EasyUseAnima/pull/189)
  introduced the 0.5.2 node/workflow contract and import-boundary seeds;
  subsequent Phase A/B work added the deterministic whole-backend inventory,
  package/archive skeleton, common primitives, Comfy adapters, and incremental
  vertical moves.

The `nodes.py` extraction in
[Issue #184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184)
is an intermediate state. The final canonical structure belongs to Issues
[#185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185) through
[#188](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/188).

## Goals and exclusions

The backend migration must make feature ownership, dependencies, process-wide
state, persisted-data contracts, and supported import paths explicit. It must
preserve existing node, workflow, profile, settings, and API behavior while
mechanical moves are in progress.

The following work is excluded from this architecture track:

- frontend JavaScript or TypeScript refactoring;
- [Issue #166](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/166)
  frontend lifecycle registry work, which is adjacent tracking only and has no
  Python backend phase dependency;
- Prompt Studio DOM structure or lifecycle;
- legacy-canvas or Node 2.0 canvas event handling;
- node, textarea, preview, or panel resizing;
- CSS, accessibility UI, and other visual UX work; and
- new user-facing features.

If a backend move exposes a behavior defect, the behavior change must be owned
by its existing feature issue or a separate Behavior PR.

## Architecture and dependency direction

The canonical production import root is `easyuse_anima`. The required direction is:

```text
ComfyUI entrypoint / bootstrap / registration
                         |
                         v
       node adapters and HTTP API adapters
                         |
                         v
       feature services, use cases, typed contracts
                         |
                         v
      feature domain and infrastructure ports/adapters
```

Bootstrap composes concrete repositories, providers, and infrastructure.
Feature services receive the narrow contracts they need; they do not locate
adapters or the process runtime themselves.

Forbidden back references are:

```text
feature/domain       -> easyuse_anima.nodes
feature/domain       -> easyuse_anima.api.routes
feature/domain       -> registration or bootstrap
feature/domain       -> root compatibility shims
infrastructure       -> node classes
infrastructure       -> aiohttp request/response types
infrastructure       -> feature schema meaning
internal production  -> any root compatibility shim
registration         -> storage, network, routes, or service construction
```

`get_runtime()` is allowed only at bootstrap and adapter boundaries where
ComfyUI constructs a node class directly. Domain and feature-service code must
use constructor arguments or narrow Protocols instead.

## Target directory and ownership

The following is the canonical ownership tree. Leaf modules are created only
when they have a real responsibility; every feature is not required to have the
same `models.py`/`service.py`/`repository.py` template.

```text
ComfyUI-EasyUseAnima/
|-- __init__.py                         # ComfyUI entrypoint
|-- nodes.py                            # public node compatibility shim
|-- api.py                              # temporary API compatibility shim
|-- api_contract.py                     # temporary Phase C implementation; D-02/D-14 target
|-- settings.py                         # temporary settings shim
|-- storage.py                          # temporary storage shim
|-- autocomplete_dataset.py             # temporary autocomplete shim
|-- wildcard_engine.py                  # temporary wildcard shim
|-- prompt_translation.py               # temporary translation shim
|-- anima_prompt/                       # temporary prompt-package shim
`-- easyuse_anima/
    |-- __init__.py                     # minimal canonical public surface
    |-- bootstrap.py                    # production composition and lifecycle
    |-- runtime.py                      # RuntimeConfig/RuntimeServices access
    |-- registration.py                 # pure node/display mapping composition
    |-- errors.py                       # common feature error taxonomy
    |-- common/                         # only truly cross-feature primitives
    |   |-- values.py
    |   `-- serialization.py
    |-- nodes/
    |   |-- prompt_nodes.py
    |   |-- regional_nodes.py
    |   |-- wildcard_nodes.py
    |   |-- naia_nodes.py
    |   |-- image_nodes.py
    |   |-- lora_nodes.py
    |   `-- aio_nodes.py
    |-- api/
    |   |-- router.py
    |   |-- requests.py
    |   |-- responses.py
    |   |-- errors.py
    |   `-- routes/
    |       |-- settings.py
    |       |-- profiles.py
    |       |-- autocomplete.py
    |       |-- wildcards.py
    |       |-- translation.py
    |       `-- naia.py
    |-- prompt/
    |-- wildcard/
    |-- autocomplete/
    |-- profiles/
    |-- settings/
    |-- translation/
    |   `-- providers/
    |-- naia/
    |-- image/
    |-- aio/
    |   `-- stages/
    `-- infrastructure/
        |-- comfy/
        |-- filesystem/
        `-- http/
```

### Owner matrix

| Surface | Owner | May own | Must not own or import |
| --- | --- | --- | --- |
| Root `__init__.py` | ComfyUI entrypoint | `WEB_DIRECTORY`, exported mappings, one guarded bootstrap call | feature rules, repositories, caches, route implementations |
| Root compatibility files | [shim registry](python-compatibility-shims.md) | explicit direct re-exports and `__all__` | wrappers/subclasses, star imports, new logic, I/O, clients, caches |
| `bootstrap.py` | production composition | `RuntimeConfig`, factories, concrete route factory/dependency/correlation wiring, the single production route-registration call site, user-directory initialization, initialize/shutdown | Prompt rules, schemas, ranking, AiO stages |
| `runtime.py` | process runtime | access to the single production `RuntimeServices`, lifecycle state | feature behavior or request-local mutable state |
| `registration.py` | node registration | class/display mapping composition | file/network access, routes, service creation, cache initialization |
| `nodes/*_nodes.py` | ComfyUI adapters | node metadata, raw-to-typed conversion, service call, ComfyUI output/UI conversion | persistence, migration, provider HTTP, cache implementation, invoking another node class for reuse |
| `api/router.py` | HTTP routing infrastructure | injected handler order, route definitions/signature, resolver/registrar, idempotent route-table registration | concrete route factories, `api/routes/*` imports, feature dependency wiring, provider construction |
| `api/routes/*` | HTTP feature adapters | request parse, service call, response/error mapping | route-table lifecycle/registration, repository internals, filesystem writes, source scanning, provider construction, mutable module cache |
| Feature packages | feature owner | domain rules, typed request/result/config, validation, use cases, feature migrations and ports | node/API adapters, registration/bootstrap, root shims |
| `infrastructure/comfy` | ComfyUI integration | capability discovery, invocation, resources, events, paths | feature schema meaning, node classes |
| `infrastructure/filesystem` | generic persistence | atomic JSON publish, locks, path primitives | profile revisions, settings keys, workflow semantics |
| `infrastructure/http` | transport | client lifecycle, timeout and transport primitives | provider-specific feature policy |
| `common` | cross-feature primitives | coercion/serialization proven to be domain-neutral | Prompt, AiO, profile, or settings meaning; miscellaneous helpers |

Here, router composition means binding injected handlers to the canonical
ordered route definitions. Bootstrap owns the concrete route factories,
dependency callbacks, and correlation wiring, then invokes registration from
the single production call site. “Single” is not process-once: every
`initialize` refreshes the current route table, identical signatures remain
idempotent, and a new table is registered. During the transition, root
`api.py` only forwards legacy callback mappings into bootstrap; it is not the
durable composition owner and remains subject to the existing removal gate.

## RuntimeServices and lifecycle

`RuntimeServices` is the process-lifetime owner of service/repository instances
and all mutable shared resources reachable from them. This includes caches,
locks, provider and HTTP clients, executors, repositories, and ComfyUI
capability/resource lookup state.

```python
@dataclass
class RuntimeServices:
    settings: SettingsService
    profiles: ProfileService
    autocomplete: AutocompleteRepository
    wildcards: WildcardService
    translation: TranslationService
    naia: NaiaService
    comfy: ComfyCapabilities
    seed_reservations: SeedReservationService
    aio: AioOrchestrator
    executor: ExecutorService
    clock: Clock

    def close(self) -> None:
        ...
```

The exact members may evolve, but the ownership rules do not:

- configuration and user paths are resolved once by bootstrap;
- optional provider clients are created lazily only when enabled;
- a repository/service owns its cache and lock and exposes clear/close as
  required;
- request-local state never leaks into a process-lifetime service field;
- `initialize()` called twice does not duplicate routes, directories, clients,
  executors, or caches;
- `shutdown()` called twice is safe;
- partial initialization failure closes already-created resources in reverse
  order; and
- tests can create isolated runtimes with in-memory repositories, fake clients,
  fake clocks, deterministic executors, and separate user-data roots.

Phase E is not complete until an inventory maps every mutable process-wide
cache/lock/client/executor/repository/capability to an owner, lifetime,
thread-safety rule, cleanup operation, and test fixture.

## Persistence and error contracts

Settings, profiles, and persisted workflow-owned backend data use the same
versioned pipeline:

```text
raw JSON object
  -> schema/version detection
  -> one-step pure migrations (v1 -> v2 -> v3)
  -> validation and normalization
  -> typed model
  -> atomic publish at the final write boundary
```

Each feature documents unknown-field preservation, downgrade support, and
failure behavior. Migrations do no file I/O. A failed migration does not replace
the original file or last known-good data.

The shared taxonomy starts with these feature-level categories:

```text
EasyUseAnimaError
|-- ValidationError
|-- ConflictError
|-- NotFoundError
|-- CapabilityUnavailableError
|-- UpstreamTimeoutError
`-- StorageError
```

Feature code does not know HTTP status codes or ComfyUI UI payloads. API
adapters map feature errors to stable `status`/`code`/`message`/request-id
responses. Node adapters map them to the existing user-visible RuntimeError or
UI-status contract. Error-contract changes are Contract or Behavior PRs, never
hidden in a Move PR.

## Compatibility contract

The 0.5.2 fixtures and shipped surfaces are the migration baseline, not a
promise that every private helper is public.

| Surface | Compatibility requirement |
| --- | --- |
| Node mappings | Preserve mapping keys/order, display names, mapped class identity, inputs/defaults/ranges/flags, outputs, `FUNCTION`, `CATEGORY`, `OUTPUT_NODE`, and representative `IS_CHANGED`. |
| Workflows | Preserve 0.5.2 class IDs, hidden inputs, `widgets_values` order/meaning, and load/save/reload behavior. |
| Profiles/settings | Read existing files, preserve identity/revision and long-text behavior, run versioned migrations, and keep last known-good data on failure. |
| HTTP API | Preserve endpoint URLs and existing success/error fields during migration; additive changes require the owning API contract PR. |
| Python imports | A supported root symbol re-exports the same canonical object; wrappers and subclasses do not satisfy identity compatibility. |
| Registry package | Include the canonical package and required shims in the actual archive, prove static/local import closure, and keep optional providers from breaking package import when disabled. |

Removal policy and evidence live in
[`python-compatibility-shims.md`](python-compatibility-shims.md). Every shim stays
for at least one published release after its canonical target ships. If there
is no trustworthy consumer/telemetry evidence, retention is conservative.

## PR classification

Every backend refactor PR is exactly one of these types:

| Type | Allowed | Forbidden in the same PR |
| --- | --- | --- |
| Move | file moves, import updates, explicit identity aliases, parity tests, archive inclusion | cache/timeout/seed/error/schema-default behavior changes |
| Contract | dataclass/Protocol, request/result schema, migration, public interface | large mechanical moves, performance-policy changes |
| Behavior | async/offload, cache policy, seed reservation, error mapping, performance work | unrelated moves or broad contract redesign |

Examples that must be split include moving `cache.py` while adding a byte
budget, moving an API route while changing all status codes, or moving storage
while changing profile migration semantics.

## Phase and PR execution contract

| Phase | PR units and prerequisites | Exit condition |
| --- | --- | --- |
| Phase A - baseline | A-01 whole-backend AST inventory; A-02 public node/workflow snapshot; A-03 report-only import gate; A-04 ADR/shim policy. PR #189 is only an A-02/A-03 seed. | Deterministic inventory, real current-surface reports, versioned public fixtures, and these docs exist independently. No production move is hidden here. |
| Phase B - `nodes.py` extraction | B-01 package/archive skeleton; B-02 common primitives; B-03 Comfy adapters; B-04 through B-10 vertical Move PRs; B-11 registration/bootstrap and `nodes.py` shim. Owned by #184. | `nodes.py` is an explicit re-export shim, node implementations live under `easyuse_anima`, and node/workflow parity plus package closure pass. |
| Phase C - feature contracts/behavior | #162 Autocomplete, #163 profile/storage, #164 translation, #165 API, #167 seed, #168 AiO schema, #169 AiO stage/cache. #166 is the adjacent frontend lifecycle registry and is explicitly excluded; it does not gate this or any other Python backend phase. These Python PRs remain separate from moves. | Each feature's contract and behavior are stable enough for its D/E move; unresolved behavior is not smuggled into a move. |
| Phase D - root consolidation | D-01 translation; D-02 API contracts; D-03 through D-07 route groups and injected route-table composition, with concrete wiring in bootstrap; D-08 filesystem; D-09 settings; D-10 profiles; D-11 autocomplete; D-12 wildcard; D-13 `anima_prompt`; D-14 root shim surface freeze. Owned by #186. | All production implementations use `easyuse_anima`; root files are entrypoints or explicit shims; internal root-shim imports are zero. |
| Phase E - runtime ownership | E-01 global-state inventory; E-02 base runtime; E-03 through E-08 feature owners; E-09 idempotent lifecycle; E-10 isolated test runtime. Owned by #187. | Every process-wide cache/lock/client/executor/repository/capability has one owner and tested initialize/shutdown/partial-failure behavior. |
| Phase F - typed boundaries | Extend #163/#165/#168 patterns to settings/profile/workflow, API, Prompt, Wildcard, Autocomplete, and AiO; establish the common error taxonomy. | Raw dictionaries remain only at adapter/migration boundaries; migrations and error mappings are versioned and tested. |
| Phase G - quality ratchet | G-01 Ruff report-only; G-02 Pyright baseline; G-03 import-boundary fail gate; G-04 public API snapshot; G-05 size/complexity ratchet; G-06 test ownership layout. Owned by #188. | Fixed-version, offline-reproducible gates reject new violations without hiding existing debt. |
| Phase H - shim retirement | Introduce canonical paths, migrate internal consumers, verify at least one release, remove private aliases first, and decide public re-exports separately. | Every removal meets ADR-002 and registry gates; public removal has a breaking-change issue and release note, or is documented as long-term support. |

The dependency is A before large B moves; feature-specific C contracts before
their D/E migration; D before final H retirement. F and early G report-only
work can advance incrementally, but they may not be used to claim D/E complete.

## Quality ratchet

Quality gates are staged rather than applied as a repository-wide rewrite:

1. Record current debt without changing production code.
2. Enforce the rule on new/changed modules.
3. Expand to completed feature packages.
4. Enforce across the canonical package.
5. Enable root-shim retirement gates.

G-series minimums are:

- G-01: pinned Ruff maintenance tooling, initially `F`, `E4`, `E7`, `E9`,
  `I`, and safe `UP`; it is not a runtime dependency.
- G-02: Pyright `basic` for the canonical package, with strict allowlists
  expanding from pure feature models/services. Dynamic Comfy/tensor types stay
  in adapters.
- G-03: reject new cycles, feature-to-adapter back references, internal root
  shim imports, registration side effects, and relative/absolute fallback
  imports.
- G-04: snapshot node mappings, supported public classes, root/canonical object
  identity, explicit `__all__`, public schema/result types, and Registry archive
  closure.
- G-05: after A-01 establishes the baseline, use reviewable ratchets. Initial
  guidance is 800 lines for a new production module, 400 for an adapter, and
  120 for a new function/method. Existing exceptions require an owner issue;
  meaningless `utils2.py`/`misc.py` splits are forbidden.
- G-06: align unit, integration, contract, and packaging tests with canonical
  feature ownership while retaining the repository's `unittest` runner.

### G-01 implementation contract

G-01 pins Ruff `0.15.22` as maintenance tooling and runs it through
`tools/check_python_quality.ps1` from both project-check profiles. The initial
production report covers `F`, `E4`, `E7`, `E9`, `I`, and safe `UP` rules for
Python 3.10 while excluding test and maintenance-tool sources.

Lint findings remain visible but non-blocking through Ruff's `--exit-zero`
mode. A missing `uvx`, an invalid Ruff configuration, or another execution
failure still fails the project check. The runner never applies `--fix` or
formatting and disables Ruff's repository cache. This report-only step does
not establish a new-violation ratchet, complete G-02 or later phases, or close
Issue #188.

### G-02a implementation contract

G-02a pins Pyright `1.1.411` as npm-based maintenance tooling and applies
`basic` checking to the complete canonical `easyuse_anima` package for Python
3.10. The reviewed settings live in `pyrightconfig.json`; the baseline checker
rejects any setting or value change so an ignore path or weaker mode cannot
silently lower the diagnostic count. `reportMissingModuleSource` is disabled
because availability of source alongside installed stubs is an environment
property, while missing imports and all ordinary basic diagnostics remain
visible.

`tests/fixtures/pyright_baseline.json` records the current diagnostic debt by
repository-relative path, rule, severity, and count. The official quick/full
runner permits a diagnostic group to shrink, but fails when an existing group
grows or a new path/rule/severity group appears. Pyright exit code 1 is accepted
only as a successfully generated diagnostic report; fatal, configuration, and
CLI failures remain blocking. Production files, broad ignore paths, and inline
suppression comments are not changed to establish the baseline.

The project runner uses cache-preferred resolution by default. Passing
`-OfflineMaintenanceTools` to `tools/check_project.ps1` (or `-Offline` to the
quality runner) disables network access for both pinned Ruff and Pyright after
their packages have been cached. This provides the Phase G offline
reproducibility check without adding either tool as a runtime dependency.

### G-02b implementation contract

G-02b keeps the complete canonical package in `basic` mode and promotes only
reviewed pure/service paths through Pyright's `strict` allowlist. The first
owned group is `profiles-contract` under Issue #188 and contains
`easyuse_anima/profiles/contract.py` and
`easyuse_anima/profiles/mutation.py`. Both paths were made independently
strict-clean before the gate was enabled.

The baseline fixture records each strict group ID, owner, and sorted canonical
paths. The checker requires the flattened owned paths to exactly match
`pyrightconfig.json`, rejects duplicate ownership, and forbids baseline
diagnostic debt for a strict path. Removing a reviewed path, adding an unowned
path, weakening the global mode, or introducing a strict-path diagnostic fails
the official quick/full runner.

This slice changes no production module, runtime dependency, adapter `Any`
boundary, or public compatibility surface. New strict groups require their own
reviewed owner and focused evidence. Import direction, public API, size, and
test-ownership gates remain G-03 through G-06.

### G-03a implementation contract

G-03a adds a blocking import-boundary checker for six completed canonical
prefixes: `common`, `image`, `infrastructure/comfy`, `lora`, `naia`, and
`profiles`. Its checked-in ledger records exact group ids, owner issues,
prefixes, and roles. The checker also owns the reviewed exact group set, so a
missing, duplicated, reordered, empty, renamed, or reassigned ledger entry
fails rather than reducing coverage. Every new Python file below an enrolled
prefix is included automatically.

The checker consumes the deterministic AST report from
`tools/analyze_python_backend.py`; it does not import production modules. For
enrolled sources it rejects repository-local targets outside
`easyuse_anima`, references to `easyuse_anima/nodes/`,
`easyuse_anima/api/routes/`, exact canonical `bootstrap.py` or
`registration.py`, runtime cyclic SCC membership, compatibility fallback
imports, and narrowly classified import-time route/registration or explicit
mapping-mutation calls. External and optional dependencies without a local
target remain valid. Infrastructure use by feature packages is not newly
restricted in this slice because that direction does not yet have a separate
reviewed contract.

Cycle enforcement uses the analyzer's shipped Python inventory as its node
scope. The checker completes that graph only when an absolute import exactly
matches an inventoried local module, then delegates runtime-edge filtering and
SCC calculation to the analyzer's existing helpers. This keeps
`TYPE_CHECKING` exclusion identical to the report policy while preventing an
absolute canonical edge from bypassing the cycle gate.

`tools/check_python_quality.ps1` runs the checker once in the shared quality
path used by both quick and full project profiles. Existing unenrolled debt in
root loaders, Prompt, and node adapters remains visible in the analyzer report
but does not block this first package gate. Enrolling another prefix requires a
separate reviewed zero-violation checkpoint and an intentional update to both
the ledger and checker-owned expected set.

## Overall Definition of Done

The Python backend refactor is complete only when all of the following hold.

### Structure and dependencies

- [ ] `easyuse_anima` is the only production implementation root.
- [ ] Root Python files are the ComfyUI entrypoint or registered shims.
- [ ] Node/API adapters call feature services and contain no repository,
      external HTTP, migration, or cache implementation.
- [ ] Feature/domain and infrastructure code have no adapter, registration,
      bootstrap, or root-shim back references.
- [ ] The final owner matrix is enforced by an import-boundary gate.

### State and lifecycle

- [ ] Every process-wide cache, lock, client, executor, repository, and
      capability has an owner, lifetime, thread-safety, and cleanup contract.
- [ ] Initialize and shutdown are idempotent, including partial-failure cleanup.
- [ ] Optional dependency failure is contained to its feature.
- [ ] Runtime fixtures isolate user data and do not rely on private-global
      patch/reload cleanup.

### Data and compatibility

- [ ] Settings, profiles, and workflow-owned backend data use versioned pure
      migrations and atomic final writes.
- [ ] API request/result/error and feature boundaries are typed.
- [ ] 0.5.2 node/workflow/profile/settings/API fixtures pass.
- [ ] Supported root and canonical objects have identity parity.
- [ ] The actual Registry package contains the complete canonical/shim import
      closure and imports with optional providers disabled.

### Quality and operations

- [ ] Pinned Ruff/Pyright or approved equivalents run in the official runner.
- [ ] Cycle, forbidden import, public API, and size-growth ratchets block new
      debt.
- [ ] Every merged implementation PR is classified Move, Contract, or Behavior.
- [ ] The shim registry has owners, evidence, and removal gates for every root
      compatibility surface.
- [ ] Private shims are retired only after the support window; each public shim
      is either deliberately retained or removed through a reviewed breaking
      change.
- [ ] Final full runner, `comfy node validate`, actual `comfy node pack`, archive
      closure, 0.5.2 compatibility, and representative ComfyUI execution gates
      pass at the release/integration stage.

## Tracking relationships

The follow-on [`AiO Hook extensibility plan`](aio-hook-extensibility-plan.md)
preserves this phase ordering. Its contract-only seams may proceed alongside
the refactor only after their stated prerequisites are met; coupled behavior
work waits until the relevant backend exits are complete. Completion of that
plan and its integration gates is the target scope for release 0.6.0.

- [#162](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/162): Autocomplete repository/index
- [#163](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/163): Profile identity/storage migration
- [#164](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/164): Translation provider/async boundary
- [#165](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/165): API request/error contract
- [#166](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/166): Frontend lifecycle registry; explicitly excluded, with no Python backend phase dependency
- [#167](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/167): Backend seed reservation
- [#168](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/168): AiO typed schema
- [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169): AiO stage/cache behavior
- [#184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184): Intermediate `nodes.py` extraction
- [#185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185): Long-term architecture parent
- [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186): Root package consolidation
- [#187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187): RuntimeServices and lifecycle
- [#188](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/188): Quality ratchet and shim retirement
