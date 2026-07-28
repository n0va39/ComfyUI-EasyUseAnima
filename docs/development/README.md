# EasyUse Anima Development Entry

Use this file as the first development-doc entry point for a new Codex session.
Read only the sections needed by the active task.

## Read order

1. `docs/development/current-policies.md`
2. [`codex-execution-efficiency.md`](codex-execution-efficiency.md)
   - create one bounded task card;
   - use focused edit-loop tests;
   - run official full once on the final candidate SHA;
   - run package/live/benchmark only when triggered.
3. Active backend queue:
   [`../architecture/backend-roadmap-resume-0.6.2.md`](../architecture/backend-roadmap-resume-0.6.2.md)
   - D-08 is completed; use its audit verdict as evidence and do not restart D-08t;
   - it supersedes the stale immediate queue and broad preflight in the older
     execution roadmap.
4. Backend target architecture and compatibility policy:
   [`../architecture/README.md`](../architecture/README.md)
   - E-01 runtime state ledger:
     [`../architecture/python-runtime-state-inventory.md`](../architecture/python-runtime-state-inventory.md)
   - E-02b/E-02c runtime base and composition Contract:
     [`../architecture/python-runtime-base-contract.md`](../architecture/python-runtime-base-contract.md)
   - E-02 completion audit:
     [`../architecture/python-runtime-e02-completion-audit.md`](../architecture/python-runtime-e02-completion-audit.md)
   - E-03 repository/filesystem Contract:
     [`../architecture/python-runtime-e03-repository-filesystem-contract.md`](../architecture/python-runtime-e03-repository-filesystem-contract.md)
   - E-04 translation runtime ownership Contract:
     [`../architecture/python-runtime-e04-translation-contract.md`](../architecture/python-runtime-e04-translation-contract.md)
   - E-05 autocomplete runtime ownership Contract:
     [`../architecture/python-runtime-e05-autocomplete-contract.md`](../architecture/python-runtime-e05-autocomplete-contract.md)
   - E-06 wildcard snapshot runtime ownership Contract:
     [`../architecture/python-runtime-e06-wildcard-contract.md`](../architecture/python-runtime-e06-wildcard-contract.md)
   - E-08 AiO first-pass cache ownership Contract:
     [`../architecture/python-runtime-e08-aio-cache-contract.md`](../architecture/python-runtime-e08-aio-cache-contract.md)
   - E-09 runtime shutdown and cleanup Contract:
     [`../architecture/python-runtime-e09-lifecycle-contract.md`](../architecture/python-runtime-e09-lifecycle-contract.md)
   - E-10 isolated runtime test fixture Contract:
     [`../architecture/python-runtime-e10-test-isolation-contract.md`](../architecture/python-runtime-e10-test-isolation-contract.md)
5. Read [`codex-blocker-escalation.md`](codex-blocker-escalation.md) only after a
   documented hard stop or unresolved cross-owner failure. Ordinary implementation
   and test failures remain local task work.
6. Read a topic guide only when the task actually touches it:
   - queue identity: `../architecture/queue-ui-two-phase-correlation-addendum.md`
   - Prompt Studio execution projection: `../architecture/prompt-studio-execution-derived-projection.md`
   - dual-canvas UI checks: `browser-smoke-matrix.md`
   - custom-node integrations: `custom-node-integrations.md`
   - Registry scanner prevention for a future release:
     [docs/development/registry-scanner-safety.md](registry-scanner-safety.md)
   - workflows: `../Anima AiO/Workflow_Management.md`
7. Confirm `git status --short`, current branch/worktree, direct source, and direct
   tests.

Do not read every roadmap, closed Issue, or historical PR. Registry activation is
external release administration; do not poll or modify an immutable release during
ordinary `dev` roadmap work.

## Active state

- Released baseline: 0.6.2.
- Issue #187 and Phase E are complete. Issue #186 remains open as the retained
  D-14/shim decision ledger.
- E-10c completion and D-14 post-Phase-E audit base: PR #561 at
  `121ee8a1cae826fc1b5227208f964d143b5b6324`.
- D-08u integrated exit audit is complete.
- D-08v is not required; the audit found no remaining D-08 production Move.
- D-14 post-Phase-E readiness retains every root surface. Lifecycle ownership is
  complete, but direct production imports, missing release windows, and insufficient
  consumer evidence still block retirement/final freeze.
- E-01 through E-10 and Phase E are complete with `ambiguous_state_owners=[]`, zero
  module reload sites, and zero direct private runtime mutation outside the test-only
  helper. The #323
  E-02a/E-07 bridge remains completed evidence, not authorization for unrelated
  feature migration.
- Completed #470 and the 0.6.1 Prompt Studio lane are behavior-contract references,
  not the active queue.
- Do not remove root compatibility aliases or start release/Registry work outside
  the active roadmap gates.

## Completed D-08 composition audit surface

```text
api.py
easyuse_anima/bootstrap.py
easyuse_anima/api/routes/profile_loads.py
easyuse_anima/api/routes/profile_saves.py
easyuse_anima/api/routes/aio_profile_mutations.py
easyuse_anima/api/routes/lora_profile_fix.py
tests/test_api_contract.py
current bootstrap/runtime owner tests
tests/fixtures/python_backend_baseline.json
```

Use targeted symbol search to confirm current owners. Do not automatically read all
files under `easyuse_anima/api/`.

## Completed D-08t boundary

Move factory invocation and request-correlation composition for:

```text
LoRA/AiO profile load
LoRA/AiO profile save
AiO profile delete/rename
LoRA profile fix
```

Keep one cohesive Move PR because all seven handlers share the same owner, production
files, classification, and validation surface. Do not split solely to create smaller
commits.

Preserve:

- dynamic root callback and monkeypatch seams;
- parsing, query defaults, error tuples/order, payloads, and handler identities;
- profile IDs, revisions, strict CAS, overwrite and target preconditions;
- file-I/O dispatch, route order/signature/registration, request correlation;
- root compatibility aliases and repeated initialize behavior.

Do not change repositories, persistence, schemas, route behavior, translation worker,
file-I/O lifecycle, RuntimeServices, public bootstrap/router exports, or import root
`api.py` from bootstrap.

## Validation

### Edit loop

```text
changed-file Python syntax/static check
direct profile route contracts
route-composition owner test
affected bootstrap/runtime tests
current import-boundary/analyzer fixture
git diff --check
```

The repository `quick` profile is broad and is not a task preflight or per-edit
command.

### Final D-08t candidate

- Run official full once on the exact final code/test SHA.
- Reuse earlier package/live evidence when the diff is limited to existing
  `api.py`/`bootstrap.py` composition and direct tests, with no shipped file,
  dependency, route signature, public behavior, error, persistence, optional-import,
  or lifecycle change.
- Escalate package/live immediately when one of those boundaries changes.

### D-08u exit gate

Run once on the integrated candidate:

```text
official full
comfy node validate
comfy node pack and archive/CRC closure
package/no-host import
repeated initialize/idempotence
representative profile list/load/save/delete/rename/fix live smoke
```

## Other policy notes

- Current release notes are in `RELEASE.md`; package version is in `pyproject.toml`.
- Workflow JSON belongs under `docs/example_workflows/`.
- A version marker is not a publish action.
- Technical PRO review is for unresolved cross-boundary architecture choices,
  unavoidable cycles, or insufficient compatibility evidence—not routine failures.
- D-14 post-Phase-E readiness is recorded and authorizes no removal. E-09/E-10 and
  Phase E are complete, but `api.py` and `wildcard_engine.py` still have direct
  production consumers and final post-v0.6.2 forms without release N. Do not infer
  root deletion, release publication, or Registry actions.
