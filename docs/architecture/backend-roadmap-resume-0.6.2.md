# Backend Roadmap Resume Checkpoint after 0.6.2

## Status and authority

- Status: active execution correction for Issue #186.
- Reviewed baseline: `dev@a509e87c7021257d514e66710f4ca4afb74c4a05` after D-08s / PR #520.
- Released baseline: 0.6.2.
- Scope: the remaining root `api.py` consolidation and its immediate exit gate.
- This document supersedes the stale immediate queue and broad preflight command in
  `python-backend-execution-roadmap.md` for the current D-08 continuation only.
- The target architecture in `python-backend.md`, ADR-001, ADR-002, and the
  compatibility-shim registry remain authoritative.
- Comfy Registry review or activation status is external release administration and
  does not block this `dev` refactor queue. Codex must not poll, republish, mutate, or
  replace 0.6.2 while executing this roadmap.

## 1. Current code review

The current D-08 direction is sound. No P0/P1 correctness defect was found in the
reviewed route-composition surface.

Verified structure at the reviewed baseline:

- root `api.py` is still a transitional 640-line compatibility/composition facade;
- `easyuse_anima/bootstrap.py` is 173 lines and owns the private composition helpers
  already moved through D-08s;
- canonical route modules remain request/response adapters and do not own route-table
  registration;
- `api/router.py` owns the injected route order, signature, resolver, registrar, and
  idempotent registration mechanics;
- `bootstrap.initialize()` remains the single production call site that invokes the
  registrar;
- package import, route order/signature, request correlation, error redaction, profile
  persistence/CAS, and repeated initialization were covered by the merged D-08 evidence;
- import-boundary and package-skeleton gates report no new canonical-to-root back edge.

The current remaining debt is deliberate, but it must not become permanent:

1. Seven handlers are still factory-composed and correlated directly in root `api.py`:
   two profile loads, two profile saves, two AiO profile mutations, and one LoRA
   profile-fix handler.
2. Root `api.py` still constructs compatibility payload/runtime helpers and the route
   registrar. Those responsibilities are not automatically part of the remaining
   handler-composition Moves.
3. The root facade retains many evidence-backed aliases and dynamic monkeypatch seams.
   They cannot be deleted merely because canonical owners exist.
4. `bootstrap.py` must never import root `api.py` to finish the move; that would invert
   the dependency direction and create a cycle.
5. Translation executor creation, file-I/O lifecycle, profile repositories, request
   parsing, error policy, and route behavior stay outside D-08 composition Moves.

## 2. Exact remaining D-08 queue

Execute one task at a time from the latest `origin/dev`. Search open PRs and branches
for the task ID before creating a competing implementation.

```text
DONE  D-08q  AiO Torch Compile recommendation composition      PR #518
DONE  D-08r  LoRA preview/catalog composition                   PR #519
DONE  D-08s  LoRA/AiO profile-list composition                  PR #520
READY D-08t  LoRA/AiO profile-load composition
NEXT  D-08u  LoRA/AiO profile-save composition
NEXT  D-08v  AiO profile delete/rename composition
NEXT  D-08w  LoRA profile-fix composition
NEXT  D-08x  D-08 exit audit and final composition checkpoint
```

Do not skip to D-14, Phase E, quality cleanup, or shim removal while one of D-08t
through D-08x is incomplete.

### D-08t — Profile load composition

Type: Move.

Goal:

- move only `build_profile_load_handlers()` invocation and request-correlation wrapping
  from root `api.py` to a private bootstrap composition helper;
- preserve the two handler objects, dependency callbacks, error tuples, response
  payloads, route order, and root dynamic load seams.

Allowed production files:

```text
api.py
easyuse_anima/bootstrap.py
```

Allowed support files:

```text
tests/test_api_contract.py
tests/test_bootstrap.py or the current bootstrap owner test
tests/fixtures/python_backend_baseline.json
```

Forbidden:

- profile repository or error-policy changes;
- query/default/response changes;
- route-definition or registration changes;
- root alias removal;
- importing root `api.py` from bootstrap.

### D-08u — Profile save composition

Type: Move.

Move only the two save factory invocations and correlation wrapping. Preserve JSON
validation, optional profile identity/revision fields, strict CAS behavior, error
mapping, file-I/O dispatch, and success payloads.

Do not combine delete/rename behavior, persistence changes, or profile schema changes.

### D-08v — AiO profile mutation composition

Type: Move.

Move only delete/rename factory invocation and correlation wrapping. Preserve source
and target preconditions, overwrite semantics, multi-token CAS, error ordering, and
response shapes.

### D-08w — LoRA profile-fix composition

Type: Move.

Move only the fix factory invocation and correlation wrapping. Preserve the current
read-only projection meaning, input-object forwarding, file-I/O dispatch, and safe
error boundary. Do not turn the fix endpoint into a persistence operation.

### D-08x — D-08 exit audit

Type: Contract/gate first. If a final Move is necessary, use a separate PR.

The audit must prove:

- all 21 route handlers are created through canonical route factories;
- all concrete route factory invocation and correlation wiring is owned by private
  bootstrap composition helpers;
- root `api.py` has no remaining direct concrete route-factory import;
- `api/router.py` still has no concrete `api/routes/*` dependency;
- exact route order, signature, marker, idempotence, mismatch behavior, and repeated
  `initialize()` behavior remain unchanged;
- root compatibility aliases and dynamic seams are classified in the compatibility
  registry before any deletion;
- root `api.py` does not gain new implementation while the final facade is audited;
- package/no-host import remains side-effect-safe except for the explicitly preserved
  root compatibility runtime.

D-08x does not authorize D-14 shim retirement. It only records whether D-14 has enough
release and consumer evidence to start a separate Contract gate.

## 3. Validation policy for D-08t through D-08w

### Edit loop

Run only:

```text
changed-file Python syntax/static check
owning route direct contract tests
route-composition owner test
bootstrap/runtime owner tests directly affected by the diff
current import-boundary/analyzer fixture
`git diff --check`
```

Do not run the repository `quick` profile as a baseline or per-edit command. A clean
latest `dev`, the owning focused tests, and existing integrated evidence are the
preflight.

### Final PR candidate

Run the official full profile once on the exact final code/test SHA.

### Evidence reuse

For D-08t through D-08w, package and live evidence may be reused when all of the
following remain true:

- the diff is limited to `api.py`, `bootstrap.py`, direct tests, and the analyzer
  baseline;
- no shipped file is added, removed, or renamed;
- no dependency, `.comfyignore`, registration table, route method/path/order, public
  response, error taxonomy, worker/lifecycle owner, or optional import changes;
- the corresponding canonical route already passed direct package and isolated live
  evidence in its earlier extraction PR;
- the composition change is covered by package-skeleton/import-boundary tests.

Under those conditions, record package/live as `evidence reused; not retriggered`.
Do not repeat `comfy node pack` and an isolated server/browser run merely because the
same two production files changed again.

### Immediate escalation triggers

Run package and/or live validation in the same PR if any of the following occurs:

- a shipped module or import closure changes beyond already-packed canonical modules;
- route order/signature/registration or `__all__` changes;
- an optional dependency moves to import time;
- request parsing, error mapping, file-I/O, persistence, response shape, or runtime
  lifecycle changes;
- the focused tests cannot distinguish a mechanical composition move from behavior.

### D-08x exit validation

At the integrated D-08x candidate, run once:

```text
official full
comfy node validate
comfy node pack + CRC/archive closure inspection
package/no-host import and repeated initialize/idempotence
representative isolated ComfyUI API smoke for all remaining profile groups
```

The live checkpoint must cover at least list, load, save, delete/rename, fix, request
correlation, one safe error path, and queue-count stability. It need not repeat every
per-route matrix already proven by focused tests.

## 4. Review and stop conditions

Codex should resolve ordinary focused failures inside the owning task. Stop and record
a blocker only when:

- bootstrap would need to import root `api.py`;
- a root dynamic seam or supported object identity cannot be preserved;
- route order/signature, public response, error mapping, persistence, or execution
  order must change;
- the change requires a new public bootstrap/router export;
- an optional dependency becomes import-time required;
- the root facade cannot be reduced without an undocumented consumer decision;
- a Move cannot be separated from a Behavior or lifecycle change.

A technical PRO review is warranted only if several valid architecture choices remain
across bootstrap/router/root-shim boundaries, a cycle cannot be removed by the existing
injection pattern, or compatibility evidence is insufficient to choose safely. Normal
implementation or test failures do not require PRO review.

## 5. After D-08

After D-08x:

1. reconcile Issue #186 and the compatibility-shim registry;
2. create a D-14 readiness Contract only if canonical-plus-shim release evidence and
   actual consumer inventory are sufficient;
3. if D-14 is still blocked, record the blocker and select the first independent READY
   Phase E task whose canonical owner and lifecycle Contract already exist;
4. do not remove root files merely to make the directory tree look complete.

The Registry activation state of 0.6.2 does not select or block these tasks.

## 6. Codex resume instruction

```text
Start D-08t only from the latest origin/dev.

Read:
- current-policies.md
- codex-execution-efficiency.md universal rules
- this document's D-08t and validation sections
- Issue #186 latest checkpoint
- api.py, bootstrap.py, profile_loads.py, and direct tests

Do not reread the full historical backend roadmap or all D-08 PRs.

Create one bounded task card. Confirm no open PR owns D-08t.
Move only profile-load factory invocation and correlation wrapping into a private
bootstrap helper. Preserve every dynamic dependency, error tuple, handler identity,
route order/signature, and root compatibility seam.

Edit loop: changed-file syntax, direct profile-load/API owner tests,
bootstrap/runtime/import-boundary/analyzer tests, git diff --check.
Run official full once on the final candidate SHA.
Do not run package/live unless an escalation trigger in this document occurs.
Push and open a dev-targeted Draft PR. Review and squash-merge after the Move boundary
and evidence are confirmed. Then continue to D-08u.

Do not poll Registry status, republish 0.6.2, start D-14, or begin Phase E.
```
