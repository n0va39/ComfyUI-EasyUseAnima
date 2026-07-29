# Python Backend Architecture

These documents define the target backend architecture, migration rules and reviewed
cross-surface contracts. They do not imply that every target state is implemented.

Read the bounded execution policy first, then only the active task, its owning Issue,
direct source and direct tests.

## Active sequencing

- Active final-convergence plan:
  [`backend-final-convergence-roadmap.md`](backend-final-convergence-roadmap.md)
- Active owner: Issue
  [#593](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/593)
- First READY task: FC-01 original Definition-of-Done closure audit.
- Parent architecture: Issue
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

READY    none for backend refactoring

EVENT    ordinary release N
  ->     later H/D-14 compatibility re-audit
```

The prior `no READY task` conclusion was correct for completed F/G/security work and
compatibility deletion. It did not mean that the initial architecture Definition of
Done had been fully reconciled.

## Current code boundary

The backend is functionally validated and technically complete at
`dev@bb1452c9996293f1f77bb361e7317ddb2664ae19`.

### Completed boundaries

- node implementations live in canonical packages and root `nodes.py` is an explicit
  compatibility facade;
- feature routes, typed boundaries, migrations and common error categories are owned by
  canonical packages;
- RuntimeServices ownership, cleanup, rollback and isolated test runtime are complete;
- Wildcard production consumers use canonical owners and root `wildcard_engine.py` is
  import-only;
- public API coverage, size-growth ratchet and canonical test ownership are executable
  gates;
- the complete 16-group role-aware import gate covers the G-06 production owner map;
- canonical application owners create the API identity while root `api.py` is an exact
  compatibility binder and bootstrap remains the sole lifecycle/composition owner;
- sensitive settings responses use safe logging and `no-store` under the completed
  TRUSTED_DEPLOYMENT_ONLY security boundary.

### Technical completion

FC-05 reconciles every original Definition-of-Done row and records the integrated
full, owner, package/no-host, lifecycle, 0.5.2 compatibility and isolated ComfyUI
API/node execution gates. No technical backend refactor task remains READY.

### Compatibility boundary

Actual root-shim removal remains event-gated:

- final forms need an ordinary published release N;
- consumer and harm evidence must be considered;
- public removal needs breaking-change approval, release notes and rollback;
- low-cost shims may be deliberately retained.

Technical architecture completion does not require deleting every public shim.

## Fixed owner model

The target owner matrix remains:

| Surface | Owner and durable responsibility |
| --- | --- |
| Root `__init__.py` | permanent ComfyUI entrypoint; exported mappings and one guarded startup path |
| Root compatibility files | explicit aliases/facades only; no new feature, I/O, cache or lifecycle logic |
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

## Core active documents

- [`backend-final-convergence-roadmap.md`](backend-final-convergence-roadmap.md):
  FC-01 through FC-07, technical versus compatibility completion, optional large-module
  disposition, validation and Codex resume instruction.
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

No document here independently authorizes root deletion, a public breaking change,
release publication, tags or Registry actions.
