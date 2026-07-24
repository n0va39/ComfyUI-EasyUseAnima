# Python Backend Architecture

These documents define the target Python backend architecture and migration
rules for ComfyUI EasyUse Anima.

They are contracts for future work, not a claim that the target package layout
already exists. Start with the current-state section in
[`python-backend.md`](python-backend.md).

While Issue [#395](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/395)
is open, read
[`release-first-stabilization-lane.md`](release-first-stabilization-lane.md)
**before** selecting a task from the normal executable queue. The release lane
pauses new D/E/G/H and AiO Hook implementation, orders #266, #267, #335, #394,
and #64, and requires an integrated release before structural work resumes.

After the release lane exits, use the current executable queue in
[`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md)
and re-audit its next task against the then-current `dev` head.

The former B-11 Comfy host-provider bridge is complete. Its document remains a
historical sequencing record and no longer overrides the active queue.

## Documents

- [`release-first-stabilization-lane.md`](release-first-stabilization-lane.md):
  active cross-surface execution override for release-blocking LoRA bugs, required
  autocomplete and Prompt Studio features, integrated release validation, and
  the refactor resumption gate.
- [`python-backend.md`](python-backend.md): living architecture, ownership,
  execution phases, validation gates, and overall Definition of Done.
- [`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md):
  verified backend progress, Codex execution protocol, ordinary ordered work
  units, stop conditions, and task-level validation gates. Its next-work ordering
  is paused while #395 is open.
- [`comfy-host-provider-bridge.md`](comfy-host-provider-bridge.md): completed
  historical sequencing addendum for the seven former root Comfy
  capability/invocation wrappers and the minimum runtime-bound provider Contract
  required before the final B-11 shim.
- [`aio-hook-extensibility-plan.md`](aio-hook-extensibility-plan.md): follow-on
  AiO extension contract and stage/cache/lifecycle sequencing. Its older 0.6.0
  target does not block the active stabilization release; assign the Hook public
  API to a later minor if the stabilization release uses 0.6.0.
- [`adr-001-modular-monolith.md`](adr-001-modular-monolith.md): why the backend
  converges on a feature-oriented modular monolith under `easyuse_anima`.
- [`adr-002-compatibility-shims.md`](adr-002-compatibility-shims.md): policy for
  introducing, supporting, and retiring root compatibility shims.
- [`python-compatibility-shims.md`](python-compatibility-shims.md): registry
  schema and inventory of root/module compatibility surfaces.

## Authority and scope

- The repository policy remains authoritative for branches, releases, Registry
  publication, and validation: [`MAINTAINING.md`](../../MAINTAINING.md).
- The development-document entry point remains
  [`docs/development/README.md`](../development/README.md).
- The architecture ADRs and ordinary backend roadmap cover Python backend
  ownership. Frontend JavaScript, TypeScript, DOM, canvas, resize, and visual UX
  work normally stays in development documents.
- The release-first stabilization lane is intentionally cross-surface because a
  release gate must order backend settings, frontend UX, workflow compatibility,
  packaging, and live ComfyUI evidence together. It does not redefine feature
  ownership or authorize unrelated refactoring.
- Long-term implementation is tracked by
  [Issue #184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184),
  [Issue #185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185), and
  their child issues. The active release override is tracked by
  [Issue #395](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/395).
- An ADR, roadmap, or sequencing addendum does not authorize a package move,
  behavior change, merge, version bump, tag, or Registry publication by itself.
