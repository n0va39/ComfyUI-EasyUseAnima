# Backend Roadmap Resume Checkpoint after 0.6.2

## Status and authority

- Status: D-08 and Phase E (E-01 through E-10) are completed;
  the D-14
  readiness audit retains every root surface and blocks retirement/final-freeze work.
- E-10c completion-audit base:
  `dev@87a1689f7c5d6452888e7bb8a8f92856d3f2f76f` after E-10b / PR #560.
- Document baseline: completed E-10 isolated runtime test fixture Contract.
- Released baseline: 0.6.2.
- Scope: completed D-08 evidence, the D-14 readiness decision, completed #187
  E-01/E-02/E-03/E-04 work, the E-05a Contract, the E-05b snapshot owner Move,
  the E-05c index-store owner Move, the E-05d composition Move, the E-05e
  completion audit Contract, the E-06a wildcard snapshot ownership Contract, the
  E-06b snapshot owner Move, the E-06c canonical service/internal caller Move, the
  E-06d narrow RuntimeServices/bootstrap composition Move, the E-06e completion
  audit Contract, the completed E-07 bridge, the E-08a AiO first-pass cache
  ownership Contract, the E-08b owner Move, the E-08c narrow composition Move, and
  the E-08d completion audit Contract, the E-09a lifecycle Contract, the E-09b
  cohesive LIFECYCLE implementation, the E-09c completion audit Contract, the E-10a
  isolated-runtime-fixture Contract, the E-10b test-only owner Move, and the E-10c
  completion audit Contract. Phase E is complete; this audit does not itself
  authorize D-14 implementation, release, or Registry work.
- This document owns the current immediate queue and supersedes the stale queue and
  broad preflight command in `python-backend-execution-roadmap.md`.
- `python-backend.md`, ADR-001, ADR-002, and the compatibility-shim registry still own
  target architecture and compatibility policy.
- Registry review/activation is external release administration and does not block
  this `dev` queue. Do not poll, republish, mutate, or replace 0.6.2.

## 1. Current code review

No P0/P1 correctness defect was found in the reviewed D-08 route-composition surface.
The current structure is a valid transitional state:

- root `api.py` is a 640-line compatibility/composition facade;
- `easyuse_anima/bootstrap.py` owns the private composition helpers moved through
  D-08s and the production initialization call site;
- canonical `api/routes/*` modules remain request/response adapters;
- `api/router.py` owns injected handler order, route definitions/signature, resolver,
  registrar, and idempotent registration;
- merged evidence covers route order/signature, request correlation, error redaction,
  profile persistence/CAS, package import, repeated initialization, and isolated API
  behavior;
- import-boundary and package-skeleton gates show no new canonical-to-root back edge.

The remaining debt is explicit:

1. Seven profile handlers are still factory-composed and correlated directly in root
   `api.py`: two loads, two saves, two AiO mutations, and one LoRA fix handler.
2. Root `api.py` still constructs compatibility payload/runtime helpers and the route
   registrar. Those responsibilities are not automatically part of the remaining
   composition Move.
3. Evidence-backed aliases and dynamic monkeypatch seams must remain until a separate
   compatibility gate permits removal.
4. `bootstrap.py` must never import root `api.py`; doing so would invert dependency
   direction and create a cycle.
5. Translation executors, file-I/O lifecycle, repositories, request parsing, error
   policy, route behavior, and persistence stay outside D-08 composition work.

## 2. Cohesive remaining queue

The seven remaining handlers share the same feature family, owner, production files,
PR classification, and validation surface. Splitting them into four nearly identical
PRs would add review/full-test overhead without a meaningful rollback benefit and
would conflict with the policy against one PR per tiny mechanical extraction.

```text
DONE  D-08q  Torch Compile recommendation composition   PR #518
DONE  D-08r  LoRA preview/catalog composition            PR #519
DONE  D-08s  LoRA/AiO profile-list composition           PR #520
DONE  D-08t  remaining profile route composition          PR #524
DONE  D-08u  integrated D-08 exit Contract/gate
NOT REQUIRED D-08v  no remaining D-08 production Move
```

Do not start D-14, Phase E, quality cleanup, or unrelated feature work before D-08u.

### D-08t — Remaining profile route composition

Type: Move.

Goal: move only factory invocation and request-correlation composition for:

```text
LoRA/AiO profile load
LoRA/AiO profile save
AiO profile delete/rename
LoRA profile fix
```

The implementation may use one private profile-group builder or a small set of private
sub-builders inside `bootstrap.py`, but it must present one cohesive root call-site and
must not add a public bootstrap export.

Allowed production files:

```text
api.py
easyuse_anima/bootstrap.py
```

Allowed support files:

```text
tests/test_api_contract.py
current bootstrap/runtime owner tests
tests/fixtures/python_backend_baseline.json
compatibility/package-skeleton tests only when directly affected
```

Required preservation:

- exact seven handler objects and route ordering;
- all current dependency callbacks and late-bound root seams;
- load query defaults and route-specific error tuples;
- save parsing, optional profile ID/revision, strict CAS, and response shape;
- delete/rename source and target preconditions, overwrite semantics, and error order;
- LoRA fix input-object forwarding and read-only projection meaning;
- bounded file-I/O dispatch, request correlation, route signature, registration,
  repeated initialize behavior, and root compatibility aliases.

Forbidden:

- profile repository, schema, migration, persistence, or error-policy changes;
- request/response or route method/path/order changes;
- translation worker, file-I/O lifecycle, or RuntimeServices changes;
- root alias removal or new public bootstrap/router exports;
- bootstrap importing root `api.py`;
- unrelated formatting or cleanup.

A focused failure in one subgroup does not justify splitting the PR automatically.
Split only when the inventory proves an independent behavior owner or an incompatible
rollback boundary.

### D-08u — Integrated D-08 exit audit

Type: Contract/gate. If production movement is still required, open optional D-08v as
a separate Move PR after the audit.

The audit must prove:

- all 21 handlers are created by canonical route factories;
- all concrete factory invocation and correlation wiring is owned by private bootstrap
  composition helpers;
- root `api.py` has no direct concrete route-factory import;
- `api/router.py` still has no concrete `api/routes/*` dependency;
- exact route order, signature, marker, idempotence, mismatch behavior, and repeated
  `initialize()` semantics are unchanged;
- root dynamic seams and supported identities are classified before deletion;
- root `api.py` has not gained new implementation;
- package/no-host import remains safe except for explicitly retained compatibility
  runtime construction;
- the remaining payload/runtime helper and registrar ownership is either accepted as
  a documented shim or assigned to a named follow-up gate.

D-08u does not authorize D-14 shim retirement. It only determines whether a D-14
readiness Contract has enough release and consumer evidence to begin.

### D-08u audit verdict

The integrated executable Contract records the following completed boundary:

- all 21 route definitions retain their exact method, path, handler name, canonical
  factory module, request-correlation marker, and order;
- all 14 concrete handler factories are imported and called once by seven private
  bootstrap composition helpers;
- root `api.py` imports and calls only those seven bootstrap helpers for handler
  composition, while `api/router.py` has no concrete `api/routes/*` dependency;
- bootstrap has no root `api.py` back-reference and still exports only `initialize`;
- marker, signature mismatch, partial failure, same-table idempotence, new-table
  refresh, and repeated `initialize()` contracts remain covered by their direct
  owners;
- supported root callback and identity seams remain in place and are not deletion
  candidates inside D-08.

The remaining root `api.py` payload/runtime helper construction and injected registrar
facade are accepted transitional shim responsibilities until a separate D-14 readiness
Contract classifies consumer and release evidence. D-08v is not required.

## 3. Validation policy

### D-08t edit loop

Run only:

```text
changed-file Python syntax/static check
direct profile load/save/mutation/fix route contracts
route-composition owner test
bootstrap/runtime owner tests affected by the diff
current import-boundary/analyzer fixture
git diff --check
```

Do not run the broad `quick` profile as preflight or per-edit validation. A clean latest
`dev`, focused tests, and integrated evidence are sufficient preflight.

### D-08t final candidate

Run the official full profile once on the exact final code/test SHA.

Package/live evidence may be reused when all are true:

- diff is limited to `api.py`, `bootstrap.py`, direct tests, and analyzer baseline;
- no shipped file is added, removed, or renamed;
- no dependency, `.comfyignore`, registration table, route signature/order, public
  response, error taxonomy, persistence, worker/lifecycle owner, or optional import
  changes;
- each canonical route already has package and isolated live evidence from its
  extraction PR;
- package-skeleton/import-boundary tests cover the changed composition edge.

Record reused evidence explicitly as `not retriggered`. Do not repeat package and live
checks solely because the same two production files changed again.

Run package/live in D-08t if any trigger occurs:

- shipped module or material import closure changes;
- route definition/signature/registration or `__all__` changes;
- optional dependency moves to import time;
- parsing, errors, file-I/O, persistence, payload, or runtime lifecycle changes;
- focused evidence cannot distinguish Move from Behavior.

### D-08u exit validation

At the integrated exit candidate, run once:

```text
official full
comfy node validate
comfy node pack + CRC/archive closure inspection
package/no-host import
repeated initialize/idempotence
representative isolated profile API smoke
```

The live matrix covers list, load, save, delete/rename, fix, request correlation, one
safe error path, and queue-count stability. It need not duplicate every route-specific
fixture already proven by focused tests.

## 4. Review and stop conditions

Codex resolves ordinary implementation and test failures inside D-08t. Stop only if:

- bootstrap would need to import root `api.py`;
- a supported dynamic seam or object identity cannot be preserved;
- route order/signature, response, error mapping, persistence, or execution order must
  change;
- a new public bootstrap/router API is required;
- an optional dependency becomes import-time required;
- root facade reduction requires an undocumented consumer decision;
- the Move cannot be separated from Behavior or lifecycle work.

Technical PRO review is needed only when several valid architecture choices remain
across bootstrap/router/root-shim boundaries, the existing injection pattern cannot
avoid a cycle, or compatibility evidence cannot select safely. Ordinary failures and
small implementation choices do not require PRO review.

## 5. D-14 readiness result and next owner

The D-08u audit found no required D-08v. After D-08:

1. Issue #186, local release-tag trees, production consumers, and the compatibility
   registry were reconciled at `dev@597d1c9`;
2. there are zero removal-approved surfaces: `api.py` and `wildcard_engine.py` retain
   production/lifecycle owners, three final shims have no release N, and the other
   public shims lack removal-supporting consumer evidence;
3. D-14 retirement/final-freeze work remains blocked and no root file or alias is
   removed;
4. #187 E-01 global-state inventory is complete and versioned; the narrow
   E-02a/E-07a/E-07b bridge is already complete through #323;
5. E-02b fixes RuntimeConfig, Clock, and idempotent RuntimeResource contracts;
6. E-02c composes RuntimeConfig and a private system clock into the default
   RuntimeServices while preserving path compatibility and initialize behavior;
7. the E-02 completion audit assigns the autocomplete index root to E-05, records
   filesystem paths as complete, and selects E-02d for the prompt knowledge path;
8. E-02d canonicalizes the prompt knowledge path and completes E-02;
9. E-03a fixes current repository constructors, path inputs, lock order, revision/CAS,
   dynamic dependencies, and monkeypatch seams without changing production;
10. the first READY follow-up is the E-03b stateless filesystem factory Move only; and
11. E-03b adds `create_atomic_json_store` as a stateless canonical-constructor seam
    without adding a lock registry or root export;
12. E-03c adds a private per-call settings repository without capturing an
    import-time default or mutable process state;
13. E-03d adds a shared private per-call profile repository while retaining the
    canonical store factory and profile directory coordinator as the state owners;
14. E-03e reconciles both E-01 owners with E-03, records zero ambiguous
    repository/filesystem state owners, and completes E-03;
15. E-04a keeps provider registry/client, service cache/per-key single-flight, and
    API route executor as three distinct translation-owned resources, rejects a
    generic executor/client port, and records the unproven client-close gap; and
16. E-04b moves provider factories, lazy instances, and registry locking behind one
    private registry while retaining a call-time default seam and unchanged lazy
    optional client behavior; and
17. E-04c composes one runtime-owned translation port from the process clock, bounded
    cache, and per-key single-flight service while preserving the canonical facade;
    and
18. never remove root files merely to make the directory tree appear complete.

## 6. E-01/E-02/E-03/E-04c result and Codex resume instruction

```text
D-08 is complete. Do not restart D-08t or create D-08v without new contrary
production evidence.

D-14 retirement is blocked. Retain every root file and alias. Do not turn the
readiness audit into removal, deprecation, or release work.

E-01 is owned by python-runtime-state-inventory.md and
tests/fixtures/python_runtime_state_ownership.v1.json. Its direct gate requires
every analyzer mutable global to be runtime-owned or declarative-only, maps every
owner candidate, and adds manual singleton/path/import-effect coverage.

E-02b is owned by python-runtime-base-contract.md. It adds only frozen/slotted
RuntimeConfig, Clock.monotonic(), and idempotent RuntimeResource.close() canonical
types. Generic executor/client ports are rejected because current feature semantics
do not share one useful contract.

E-02c adds required config/clock fields to RuntimeServices. A private bootstrap loader
projects the existing canonical path objects without re-resolving them, and a private
system clock delegates to time.monotonic(). Existing path constants, feature consumers,
and root surfaces remain unchanged.

The E-02 completion audit is owned by
python-runtime-e02-completion-audit.md. It assigns the autocomplete index root to
E-05, records filesystem paths as E-02c complete, and E-02d canonicalizes the prompt
knowledge path. E-02 is complete.

E-03a is owned by python-runtime-e03-repository-filesystem-contract.md and
tests/fixtures/python_repository_filesystem_contract.v1.json. The filesystem factory
is a stateless AtomicJsonStore constructor seam; the canonical atomic module keeps the
single process path-lock registry. The profile directory coordinator remains a
separate shared CAS transaction dependency.

E-03b adds `create_atomic_json_store(path, *, backup=True)`. It delegates directly to
the canonical `AtomicJsonStore`, creates no state, preserves root `storage.py`, and
proves direct/factory stores share one normalized-path lock.

E-03c and E-03d add private per-call settings and profile repository values. They
retain current path and monkeypatch seams, the canonical stateless store factory, and
the shared profile directory coordinator. They own no mutable process state.

E-03e reconciles E-01 ownership targets with those completed Moves and records zero
ambiguous repository/filesystem state owners. E-03 is complete.

E-04a is owned by python-runtime-e04-translation-contract.md and
tests/fixtures/python_translation_runtime_contract.v1.json. Provider registry/client,
service cache/per-key single-flight, and API route executor remain three distinct
translation-owned resources. Bootstrap is the target concrete composition root;
generic executor/client ports and unproven provider-client close calls are rejected.

E-04b moves provider factories, lazy instances, and registry locking behind one
private translation provider registry. The canonical public facade resolves the
current default registry on every call. Optional import, provider/client reuse,
timeouts, errors, and public/root identities are unchanged.

E-04c adds a translation-owned narrow port to RuntimeServices. Bootstrap composes the
process clock, bounded cache, and service, and installs the same service identity
behind the canonical call-time facade. Service close clears only its cache;
provider/client cleanup and whole-runtime close ordering remain separate.

E-04d moves route executor construction and `atexit` lifecycle registration from
the root API facade into private bootstrap composition while preserving every
dynamic root seam and route contract.

E-04e reconciles all three translation resources with E-01 and records zero
ambiguous owners. Optional-client import remains lazy, feature cleanup dispositions
are explicit, and whole-runtime ordering remains assigned to E-09. E-04 is complete.

E-05a classifies one declarative source policy and two runtime resource boundaries.
Dataset snapshots plus the cache-key Future map form one owner. The immutable index
root plus normalized-path SQLite publication locks form a second owner. Their locks,
failure semantics, and cleanup remain separate; no generic cache/lock port is added.

E-05b moves completed snapshots, cache-key Futures, and their Lock behind one
private `_AutocompleteSnapshotStore` referenced by
`_DEFAULT_AUTOCOMPLETE_SNAPSHOTS`. Call-time parser/stat/build/await facades,
source-change retries, follower settlement, status behavior, and public identities
are unchanged. `clear()` affects only completed snapshots and no duplicate module
dict/lock/Future state remains.

E-05c moves the import-stable Path-or-None root and retained normalized-path Locks
behind one private `_AutocompleteIndexStore` referenced by
`_DEFAULT_AUTOCOMPLETE_INDEX_STORE`. The owner-level isolated-store injection seam,
standalone disablement, Windows pre-directory lock identity, rebuild/atomic
publication/fallback diagnostics, and public explicit-root compatibility function
are unchanged. `close()` is an idempotent no-op for the non-disposable process locks.

E-05d composes the existing default snapshot and index-store owners behind one
private `_AutocompleteService`, installs only its narrow `AutocompletePort` on
`RuntimeServices`, and makes root API callbacks resolve that port with their
canonical pre-initialize fallback. Canonical feature identities, call-time root
patch seams, owner identities, bootstrap retry/refresh behavior, and no-host import
safety remain unchanged.

E-05e reconciles the three E-01 autocomplete entries with exactly two owners,
records completed-cache `clear()` and retained-lock no-op `close()` dispositions,
proves direct root identities and package/no-host import safety, and records zero
ambiguous autocomplete state without changing production. E-05 is complete.

E-06a fixes the verified-snapshot LRU, building-key set, and Condition as one
wildcard-specific runtime resource. It selects one private
`_WildcardSnapshotStore` referenced by `_DEFAULT_WILDCARD_SNAPSHOTS`, preserves the
root call-time source/build seams, and records completed-cache-only `clear()` while
whole-runtime ordering remains E-09. The bounded E-06 queue is E-06a Contract,
E-06b snapshot owner Move, E-06c canonical service/internal caller Move, E-06d
narrow bootstrap composition Move, and E-06e completion audit Contract.

E-06b moves those three raw states behind one canonical private
`_DEFAULT_WILDCARD_SNAPSHOTS` identity. Root lifecycle delegates with call-time
source/build dependencies, completed-cache `clear()` leaves active build settlement
intact, and no duplicate root state remains.

E-06c installs a root-independent private wildcard service, converts canonical node,
Prompt Studio, and seed consumers away from root `wildcard_engine`, and retains root
signatures, behavior, exact snapshot identities, and call-time source/build seams.

E-06d types the exact `_DEFAULT_WILDCARD_SNAPSHOTS` identity behind one private
`WildcardSnapshotPort` and installs it directly as
`RuntimeServices.wildcard_snapshots`. Feature modules do not import the runtime,
and initialize order/retry plus wildcard-directory lifecycle remain unchanged.

E-06e reconciles the single E-01 wildcard entry with the exact default owner,
records completed-cache-only cleanup, preserves feature import direction,
package/no-host safety, direct root identities, and the narrow runtime binding, and
records zero ambiguous wildcard state without production changes. E-06 is complete.

E-07a/E-07b were already completed through #323 as the E-02 bridge. Do not repeat
them. E-08a reconciles the one E-01 AiO cache entry with the six mutable module
states, freezes the seven direct root aliases and legacy runtime/stage injection
path, and selects one private `_AIOFirstPassCacheStore` default instance as the
owner target without production changes. E-08b moves all six mutable states behind
that default owner, removes the raw enabled/generation/metrics/lock globals, and
retains mapping/order only as exact owner aliases for root identity and call-time
replacement seams. E-08c adds one private `AIOFirstPassCachePort`, installs the exact
default owner as `RuntimeServices.aio_first_pass_cache`, and preserves the existing
`FirstPassRuntime` caller path, feature import direction, and repeated initialize
behavior. The queue remains E-08a Contract, E-08b owner Move, E-08c narrow
RuntimeServices/bootstrap composition, and E-08d completion audit. E-08d reconciles
the single E-01 entry, feature cleanup, import direction, seven root identities, and
the exact narrow runtime binding, and records zero ambiguous AiO cache state without
production changes. E-08 is complete. E-09a fixed one bootstrap-owned terminal
lifecycle, reverse cleanup order, partial-initialization rollback, and explicit
file-I/O/route/provider/warning no-op dispositions. E-09b implemented the cohesive
lifecycle and E-09c reconciled E-01 with zero ambiguous owners without production
changes. E-10 then centralized test-only reset ownership and completed the Phase E
audit. D-14 retirement, release, and Registry work remain blocked by their existing
roadmap gates.
```

## 7. E-09 runtime shutdown and cleanup queue

```text
E-09a  Contract   owner/disposition/order/rollback gate        complete
E-09b  LIFECYCLE  one cohesive terminal shutdown implementation complete
E-09c  Contract   zero-ambiguity completion audit              complete
```

E-09a is production-free. It selects bootstrap as the one serialized lifecycle owner,
retains weak per-loop file-I/O limiter self-expiry and installed routes as explicit
no-ops, removes only the callerless Artist Mix warning set in E-09b, and retains the
Conditioning warning set for process lifetime. Cleanup order and rollback are owned by
[`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md).

E-09b is one rollback boundary rather than several Move PRs because terminal state,
RuntimeServices close, executor admission, feature cleanup order, global detach, and
unexpected-startup rollback share one lifecycle/concurrency invariant. E-09c changes
no production and reconciles `ambiguous_state_owners=[]`, the seven completed E-01
lifecycle dispositions, package/import safety, and the E-09b promotion evidence.
E-09 is complete. E-10a fixed the test-isolation migration boundary, E-10b completed
the test-only Move, and E-10c closes Phase E. D-14, release, and Registry work remain
governed by their existing blockers.

### E-09a validation

Run changed-file JSON/Python syntax, the new lifecycle Contract, E-01/E-04/E-05/E-06/
E-08 direct contracts, package/no-host import, current import boundary, analyzer, and
`git diff --check`. Run official full once on the exact final candidate. Production,
import closure, archive, metadata, and host-visible behavior do not change, so reuse
E-08c package/live evidence unless a focused gate proves material drift.

### E-09c validation

Run changed-file JSON/Python syntax, the E-09 lifecycle and E-01 ownership Contracts,
the E-04/E-05/E-06/E-08 direct Contracts, package/no-host import, current import
boundaries, analyzer, maintained-document links, and `git diff --check`. Run official
full once on the exact final candidate. Because E-09c changes no production, import
closure, archive, metadata, or host-visible behavior, reuse E-09b validate/pack/live
evidence.

## 8. E-10 isolated runtime test fixture queue

```text
E-10a  Contract   current reset inventory and one test-only owner gate complete
E-10b  Move       cohesive helper and five-owner migration              complete
E-10c  Contract   zero-direct-reset and Phase E completion audit        complete
```

The executable inventory records zero module-reload sites and one serialized
`tests/runtime_test_support.py` mutation owner. There are zero direct private runtime
mutation sites outside that helper, while independently constructed RuntimeServices
values remain parallel-safe. Direct lifecycle assertions keep reading private state;
only reset/mutation ownership moved.

[`python-runtime-e10-test-isolation-contract.md`](python-runtime-e10-test-isolation-contract.md)
forbids a production reset API, hot shutdown-to-reinitialize, ContextVar runtime
behavior, overlapping global installs, route rollback, provider close, and public
export changes. E-10c records zero direct private reset outside the helper and Phase E
is complete. That completion does not waive the existing D-14, release, or Registry
gates.

### E-10a validation

Run changed-file JSON/Python syntax, the E-10 Contract, E-01/E-09 direct Contracts,
bootstrap/runtime/Comfy direct owners, package/no-host import, current import
boundaries, analyzer, maintained-document links, and `git diff --check`. Run official
full once on the exact final candidate. Because E-10a changes no production, import
closure, archive, metadata, or host-visible behavior, reuse E-09b package/live
evidence.

### E-10b and E-10c validation

E-10b passed its direct runtime/bootstrap/host/translation owners, E-10/E-01/E-09
Contracts, package/no-host import, current import boundaries, analyzer, and diff gate.
Official full at candidate `6d1d65198385122bfdb6d31e0b0f1513b2714502`
passed 1,431 Python tests and 120 frontend files exactly once.

E-10c runs changed-file JSON/Python syntax, E-10/E-01/E-09 Contracts,
package/no-host import, current import boundaries, analyzer, maintained-document links,
and `git diff --check`. Run official full exactly once on the final candidate SHA.
Because both tasks change no production, import closure, archive, metadata, or
host-visible behavior, package/live evidence is reused.
