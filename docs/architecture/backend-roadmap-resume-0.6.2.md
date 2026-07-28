# Backend Roadmap Resume Checkpoint after 0.6.2

## Status and authority

- Status: D-08 completed by the D-08u integrated Contract/gate.
- Code-review baseline: `dev@d07a7116fd2f93ad60ce3438739f99e51640aa43`
  after D-08t / PR #524.
- Document baseline: PR #522 / `fc88de042e60e2b39ecc7e4594696bdfeacab000`,
  with the development-entry link repair from PR #523.
- Released baseline: 0.6.2.
- Scope: remaining root `api.py` route composition and the D-08 exit gate.
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

## 5. After D-08

The D-08u audit found no required D-08v. After D-08:

1. reconcile Issue #186 and the compatibility-shim registry;
2. create a D-14 readiness Contract only when canonical-plus-shim release evidence and
   actual consumer inventory are sufficient;
3. if D-14 remains blocked, record why and select the first independent READY Phase E
   task with an existing canonical owner and lifecycle Contract;
4. never remove root files merely to make the directory tree appear complete.

## 6. Codex resume instruction

```text
D-08 is complete. Do not restart D-08t or create D-08v without new contrary
production evidence.

Before a separate D-14 readiness Contract:
- reconcile Issue #186 and the compatibility-shim registry;
- read the latest #186 checkpoint and the current shim policy;
- classify consumer and release evidence for each root alias before removal;
- keep root api.py payload/runtime helpers and the injected registrar facade intact.

Do not begin Phase E, release, or Registry work from this completed D-08 runbook.
```
