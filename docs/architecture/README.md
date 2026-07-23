# Python Backend Architecture

These documents define the target Python backend architecture and migration
rules for ComfyUI EasyUse Anima.

They are contracts for future work, not a claim that the target package layout
already exists. Start with the current-state section in
[`python-backend.md`](python-backend.md). While Issue #323 is open, read the
active B-11 sequencing addendum in
[`comfy-host-provider-bridge.md`](comfy-host-provider-bridge.md), then use the
current executable queue in
[`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md)
before planning an implementation PR.

The bridge addendum overrides only the ordering between the final B-11 shim and
the minimum E-02a/E-07a Comfy host-provider Contract. It does not mark Phase E
complete or replace the architecture ADRs and normal validation gates.

## Documents

- [`python-backend.md`](python-backend.md): living architecture, ownership,
  execution phases, validation gates, and overall Definition of Done.
- [`comfy-host-provider-bridge.md`](comfy-host-provider-bridge.md): active,
  narrowly scoped sequencing addendum for the seven blocked root Comfy
  capability/invocation wrappers and the minimum runtime-bound provider Contract
  required before the final B-11 shim.
- [`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md):
  current verified progress, Codex execution protocol, ordered work units,
  stop conditions, and task-level validation gates.
- [`aio-hook-extensibility-plan.md`](aio-hook-extensibility-plan.md): follow-on
  AiO extension contract, stage/cache/lifecycle sequencing, and the 0.6.0
  release gate after the required backend refactor exits are satisfied.
- [`adr-001-modular-monolith.md`](adr-001-modular-monolith.md): why the backend
  will converge on a feature-oriented modular monolith under `easyuse_anima`.
- [`adr-002-compatibility-shims.md`](adr-002-compatibility-shims.md): policy for
  introducing, supporting, and retiring root compatibility shims.
- [`python-compatibility-shims.md`](python-compatibility-shims.md): registry
  schema and initial inventory of current root/module surfaces.

## Authority and scope

- The current repository policy remains authoritative for branches, releases,
  Registry publication, and validation: [`MAINTAINING.md`](../../MAINTAINING.md).
- The development-document entry point remains
  [`docs/development/README.md`](../development/README.md).
- These documents cover the Python backend only. Frontend JavaScript,
  TypeScript, DOM, canvas, resize, and visual UX work are explicitly excluded.
- Implementation is tracked by
  [Issue #184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184),
  the long-term parent
  [Issue #185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185), the
  runtime bridge [Issue #323](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/323),
  and their related backend issues. An ADR or sequencing addendum does not
  authorize a package move, behavior change, release, or shim removal by itself.
