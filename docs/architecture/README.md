# Python Backend Architecture

These documents define the target backend architecture, migration rules and reviewed
cross-surface contracts. They do not imply that every target state is implemented.

Read the bounded execution policy first, then only the current READY or event task, its
owning Issue, direct source and direct tests. When neither exists, do not reopen a
completed lane.

## Current sequencing

- Final-convergence completion and event plan:
  [`backend-final-convergence-roadmap.md`](backend-final-convergence-roadmap.md)
- Technical completion owner: completed Issue
  [#593](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/593)
- Total Python Convergence Contract:
  [`python-total-convergence-contract.md`](python-total-convergence-contract.md)
- READY backend refactor task after this cutover merges: PTC-10 completion audit.
- Parent architecture: completed Issue
  [#185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185)
- Compatibility/release ledger: Issue
  [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- E-09 lifecycle owner: completed Issue
  [#187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187)

```text
COMPLETE Phase D/E/F/G and G-CLOSE
COMPLETE P-WC Wildcard direct-shim conversion
COMPLETE SEC-01 through SEC-05 security/admin lane
COMPLETE FC-01, FC-02 and FC-03 final-convergence prerequisites
COMPLETE FC-04A canonical API application/E-09 lifecycle Contract
COMPLETE FC-04B canonical API application cohesive Move
COMPLETE FC-05 technical architecture completion

COMPLETE PTC-01 through PTC-09B total structure, support and root cutover
READY    PTC-10 final audit

EVENT    ordinary release N
```

FC-01 through FC-05 closed the initial ownership and lifecycle Definition of Done.
PTC-01 through PTC-09B complete the per-file, size, support-ownership and E-09-safe
root cutover. PTC-10 is the remaining completion audit. Release events remain separate
from this sequence.

## Current code boundary

The FC backend boundary was functionally validated at
`dev@bb1452c9996293f1f77bb361e7317ddb2664ae19`. PTC-01 is based on
`dev@39997c5423847d4280737f0d78d353d3c6273e07` and extends that boundary without
reopening completed feature, lifecycle or security work.

### Completed boundaries

- node implementations live in canonical packages and the retired root `nodes.py`
  facade is absent;
- feature routes, typed boundaries, migrations and common error categories are owned by
  canonical packages;
- RuntimeServices ownership, cleanup, rollback and isolated test runtime are complete;
- Wildcard production consumers use canonical owners and the root
  `wildcard_engine.py` shim is absent;
- public API coverage, size-growth ratchet and canonical test ownership are executable
  gates;
- the complete 16-group role-aware import gate covers the G-06 production owner map;
- canonical application owners create the API identity and bootstrap remains the sole
  lifecycle/composition owner; the root `api.py` binder is absent;
- sensitive settings responses use safe logging and `no-store` under the completed
  TRUSTED_DEPLOYMENT_ONLY security boundary.

### FC technical completion and PTC extension

FC-05 reconciled the original ownership/lifecycle Definition-of-Done rows and recorded
the integrated full, owner, package/no-host, lifecycle, 0.5.2 compatibility and
isolated ComfyUI API/node execution gates. PTC now completes the broader objective:
every Python file has an explicit disposition, oversized modules are closed, and legacy
root import paths are removed after canonical callers are proven.

### Legacy import boundary

Root `__init__.py` remains the permanent ComfyUI entrypoint. PTC-09B removes the other
nine root Python modules and seven `anima_prompt` compatibility modules after canonical
entrypoint/caller ownership and the E-09 lifecycle identity sequence are proven. Those
legacy import paths are intentionally unsupported and must not be recreated.

## Fixed owner model

The target owner matrix remains:

| Surface | Owner and durable responsibility |
| --- | --- |
| Root `__init__.py` | permanent ComfyUI entrypoint; exported mappings and one guarded startup path |
| Retired root import paths | absent after PTC-09B; canonical owners only, no replacement facade |
| `bootstrap.py` | sole lifecycle/composition owner, RuntimeConfig, initialize/shutdown and concrete wiring |
| `runtime.py` | installed RuntimeServices identity and process runtime access |
| `registration.py` | pure node mapping composition |
| `nodes/*` | raw ComfyUI-to-feature adapters |
| `api/application*` | canonical API application identity, compatibility parts and exact handler wiring; one cohesive owner with no new size exception |
| `api/router.py` | route order/signature/resolver/registrar infrastructure |
| `api/routes/*` | request parse, feature call and response/error mapping |
| Feature packages | domain rules, typed contracts, migrations and feature ports |
| `infrastructure/*` | generic Comfy/filesystem/HTTP integration without feature meaning |
| `common` | proven domain-neutral primitives only |

FC-02D enforces this complete role model without forcing adapters and composition
modules through feature-only rules.

## E-09 lifecycle invariants

All final-convergence work preserves:

- bootstrap as the only lifecycle owner;
- one initialize/shutdown lock and one atexit registration;
- terminal/idempotent shutdown and no hot reinitialize;
- repeated initialize preserving runtime identity while refreshing routes;
- one translation route executor created before cleanup-plan composition;
- executor shutdown as cleanup item 1;
- the fixed seven-step cleanup order;
- expected-identity rollback and preservation of the original startup error;
- retained route marker/routes and no invented route deregistration;
- no file-I/O limiter or provider/client cleanup without a separate contract.

FC-03 changes patch ownership only. FC-04 moved application construction only after
its lifecycle Contract proved these invariants.

## Core current documents

- [`backend-final-convergence-roadmap.md`](backend-final-convergence-roadmap.md):
  completed FC ownership/lifecycle convergence, active PTC queue, release events,
  validation and Codex resume instruction.
- [`python-total-convergence-contract.md`](python-total-convergence-contract.md):
  explicit 183-file disposition, 31 size-exception decisions, exact target tree,
  root canonical cutover and the blocking completion definition.
- [`python-ptc09-root-cutover-contract.md`](python-ptc09-root-cutover-contract.md):
  selected private bootstrap package-start sequence, exact legacy retirement boundary,
  E-09 proof obligations and the PTC-09B task card.
- [`python-backend.md`](python-backend.md): target architecture, phases and original
  Definition of Done.
- [`python-api-papi01-e09-lifecycle-gate.md`](python-api-papi01-e09-lifecycle-gate.md):
  current API identity graph, RETAIN verdict, root patch-time seam inventory and revisit
  events.
- [`python-api-fc04-application-lifecycle-contract.md`](python-api-fc04-application-lifecycle-contract.md):
  selected canonical application identity, bootstrap composition sequence, root binder,
  E-09 gates and the exact FC-04B task card.
- [`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md):
  authoritative lifecycle and cleanup/rollback contract.
- [`python-compatibility-shims.md`](python-compatibility-shims.md): current root surfaces,
  release evidence and ADR-002 gates.
- [`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md):
  task-card, focused validation, evidence reuse and context policy.

## Completed evidence documents

Read only when the active task touches the boundary:

- [`backend-roadmap-resume-0.6.2.md`](backend-roadmap-resume-0.6.2.md): completed D-08
  and Phase E execution record.
- [`python-phase-fg-completion-audit.md`](python-phase-fg-completion-audit.md): completed
  typed/quality lane under its scoped criteria.
- [`python-public-api-g04a-audit.md`](python-public-api-g04a-audit.md)
- [`python-size-complexity-g05a-contract.md`](python-size-complexity-g05a-contract.md)
- [`python-test-ownership-g06a-contract.md`](python-test-ownership-g06a-contract.md)
- [`python-wildcard-pwc01-facade-feasibility.md`](python-wildcard-pwc01-facade-feasibility.md)
- [`security-admin-settings-roadmap.md`](security-admin-settings-roadmap.md)
- [`python-runtime-base-contract.md`](python-runtime-base-contract.md)
- [`python-runtime-state-inventory.md`](python-runtime-state-inventory.md)
- [`python-runtime-e03-repository-filesystem-contract.md`](python-runtime-e03-repository-filesystem-contract.md)
- [`python-runtime-e04-translation-contract.md`](python-runtime-e04-translation-contract.md)
- [`python-runtime-e05-autocomplete-contract.md`](python-runtime-e05-autocomplete-contract.md)
- [`python-runtime-e06-wildcard-contract.md`](python-runtime-e06-wildcard-contract.md)
- [`python-runtime-e08-aio-cache-contract.md`](python-runtime-e08-aio-cache-contract.md)
- [`python-runtime-e10-test-isolation-contract.md`](python-runtime-e10-test-isolation-contract.md)

## Cross-surface references

Read only when needed:

- [`queue-ui-two-phase-correlation-addendum.md`](queue-ui-two-phase-correlation-addendum.md)
- [`prompt-studio-execution-derived-projection.md`](prompt-studio-execution-derived-projection.md)
- [`seed-ui-semantics-gate.md`](seed-ui-semantics-gate.md)
- [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md)
- [`comfy-host-provider-bridge.md`](comfy-host-provider-bridge.md)

## Authority

- Branch/release/validation policy: [`MAINTAINING.md`](../../MAINTAINING.md)
- Development entrypoint: [`../development/README.md`](../development/README.md)
- Active technical queue: `backend-final-convergence-roadmap.md`
- Target architecture: `python-backend.md`, ADR-001 and ADR-002
- Compatibility decisions: Issue #186 plus the shim registry
- Feature behavior: owning Issue

Only the staged PTC-09A/PTC-09B Contract authorizes removal of the reviewed legacy import
paths. No document here independently authorizes release publication, tags or Registry
actions.
