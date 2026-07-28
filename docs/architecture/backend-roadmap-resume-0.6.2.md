# Backend Roadmap Resume Checkpoint after 0.6.2

## Status and authority

- Status: D-08, E-01, E-02, E-03a, E-03b, E-03c, and the E-03d profile repositories
  Move are completed; the D-14 readiness audit retains every root surface and blocks
  retirement/final-freeze work.
- Code-review base: `dev@2ccf6f91a1bf458fc4afbc6352c66fb67a934a6d`
  after E-03c / PR #534.
- Document baseline: E-03d profile repositories Move.
- Released baseline: 0.6.2.
- Scope: completed D-08 evidence, the D-14 readiness decision, completed #187
  E-01/E-02/E-03a/E-03b/E-03c/E-03d work, and the next bounded E-03e completion
  Contract/audit.
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
12. the first READY follow-up is the E-03c settings repository Move only; and
13. never remove root files merely to make the directory tree appear complete.

## 6. E-01/E-02/E-03a/E-03b result and Codex resume instruction

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

Start only #187 E-03e from latest origin/dev. Reconcile E-01 ownership targets with
the completed E-03 factory/repository Moves and prove no repository/filesystem state
is ambiguously owned before E-04. E-03e is a production-free Contract/audit. Do not
start E-04 through E-10, D-14 retirement, release, or Registry work inside E-03e.
```
