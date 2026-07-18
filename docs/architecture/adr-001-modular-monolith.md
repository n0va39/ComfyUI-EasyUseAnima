# ADR-001: Feature-Oriented Python Modular Monolith

- Status: Accepted
- Decision date: 2026-07-19
- Owners: [Issue #185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185)
  with migration work in Issues
  [#184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184) and
  [#186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Scope: Python backend only

## Context

The current backend is split between a large root `nodes.py` and several root
implementation modules. Node contracts, HTTP adapters, feature behavior,
persistence, external providers, ComfyUI invocation, and process-wide mutable
state do not yet have consistent package ownership.

PR [#189](https://github.com/n0va39/ComfyUI-EasyUseAnima/pull/189)
established useful node/workflow and import-analyzer seeds, but the baseline
still contains no production `easyuse_anima/` package. This ADR therefore
records a target and migration constraint, not completed implementation.

Issue #184 reduces the immediate `nodes.py` risk. It intentionally leaves
`api.py`, `settings.py`, `storage.py`, `autocomplete_dataset.py`,
`wildcard_engine.py`, `prompt_translation.py`, and `anima_prompt/` at the root,
so its completion is an intermediate architecture rather than the final one.

## Decision

The Python backend will converge on a small, feature-oriented modular monolith
whose canonical production import root is `easyuse_anima`.

The dependency direction is:

```text
node and API adapters
        -> feature services/use cases
        -> feature domain and infrastructure contracts/adapters
```

Bootstrap is the composition root. `RuntimeServices` owns process-lifetime
repositories, caches, locks, clients, executors, and ComfyUI capabilities.
Registration remains a pure mapping surface. No inner layer imports node/API
adapters, registration/bootstrap, or a root compatibility shim.

Features are grouped vertically (`prompt`, `wildcard`, `autocomplete`,
`profiles`, `settings`, `translation`, `naia`, `image`, and `aio`). Generic
filesystem, HTTP, and ComfyUI integration live under `infrastructure`. Files are
created for real responsibilities, not to impose an identical package template
on every feature.

Root files remain the ComfyUI entrypoint or temporary explicit re-export shims
under [ADR-002](adr-002-compatibility-shims.md). Settings/profile/workflow
migrations and the shared feature-error taxonomy follow the contracts in
[`python-backend.md`](python-backend.md).

Mechanical moves, contract changes, and behavior changes are separate PRs. This
ADR does not authorize a package move or behavior change by itself.

## Consequences

Positive consequences:

- a feature's primary code and tests have a discoverable owner;
- ComfyUI and aiohttp types are confined to adapters;
- repositories/providers can be tested through narrow Protocols;
- process-wide state has explicit lifecycle and cleanup;
- import direction, public identity, and Registry archive closure can be
  checked automatically; and
- individual Move PRs remain reviewable and reversible.

Costs and constraints:

- root and canonical import paths coexist during migration;
- bootstrap wiring and explicit contracts add some code;
- feature moves must wait for unstable #162-#169 behavior/contract work where
  applicable;
- the target cannot be reached by a single `nodes.py` split; and
- the repository must maintain compatibility fixtures and a shim registry
  through at least one published release.

## Alternatives considered

### Keep the root-module structure

Rejected because ownership, back references, state lifecycle, and Registry
closure would remain implicit. Smaller files alone would not prevent a new
monolith.

### Stop after Issue #184

Rejected as the final architecture. It is the correct first extraction, but it
would leave two production import systems and the existing root modules as
long-term implementations.

### Apply a framework-heavy Clean Architecture or DI container

Rejected for current scale. Dataclasses, Protocols, constructors, and factory
functions provide the required seams without adding a runtime framework or
forcing ceremonial layers.

### Organize only by technical layer

Rejected because repository-wide `models/`, `services/`, and `repositories/`
directories scatter one feature across the tree. Vertical feature packages
make the change surface easier to find while preserving explicit adapter and
infrastructure boundaries.

## Reconsideration conditions

Review this decision if one of the following becomes true:

- a feature becomes a separately distributed Python package or process;
- multiple independent ComfyUI entrypoints require incompatible runtime
  compositions;
- an intentionally supported external Python SDK needs a stable boundary that
  the feature packages cannot provide;
- measured startup, memory, or import isolation requirements cannot be met by a
  single process-lifetime runtime; or
- the import/ownership gates show that the chosen feature boundaries repeatedly
  create cycles despite completed migrations.

Reconsideration requires a new ADR. Temporary migration friction, file count,
or a desire to remove shims early is not sufficient.

## Explicit non-scope

Frontend JavaScript/TypeScript, DOM, canvas, legacy-canvas/Node 2.0 layout,
resize, CSS, and visual UX are not governed by this ADR.
