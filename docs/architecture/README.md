# Python Backend Architecture

These documents define the target Python backend architecture and migration
rules for ComfyUI EasyUse Anima.

They are contracts for future work, not a claim that the target package layout
already exists. Start with the current-state section in
[`python-backend.md`](python-backend.md) before planning an implementation PR.

## Documents

- [`python-backend.md`](python-backend.md): living architecture, ownership,
  execution phases, validation gates, and overall Definition of Done.
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
  [Issue #191](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/191)
  and its related backend issues. An ADR does not authorize a package move,
  behavior change, release, or shim removal by itself.
