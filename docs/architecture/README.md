# Python Backend Architecture

These documents define the target Python backend architecture, migration rules,
and explicitly reviewed follow-on integration plans for ComfyUI EasyUse Anima.

They are contracts for future work, not a claim that every target package or
feature already exists. Start with the current-state section in
[`python-backend.md`](python-backend.md), then use the current executable queue in
[`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md).

## Active sequencing notes

- Issue [#395](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/395)
  remains the active release checkpoint until Comfy Registry 0.5.5 activation is
  confirmed. Do not start a new D/E/G/H or AiO advanced-feature implementation
  while that issue remains open.
- The post-0.5.5 DAVE stage-scope, Torch Compile recommendation, and NegPip plans
  are recorded in
  [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md).
  That roadmap is PLANNED/BLOCKED and starts with Issue #409 only after #395 exits.
- The former B-11 Comfy host-provider bridge is complete. Its document remains a
  historical sequencing record and no longer overrides the active queue.

## Documents

- [`python-backend.md`](python-backend.md): living architecture, ownership,
  execution phases, validation gates, and overall Definition of Done.
- [`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md):
  verified backend progress, Codex execution protocol, ordered work units, stop
  conditions, and task-level validation gates.
- [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md):
  blocked post-0.5.5 execution plan for stage-scoped DAVE and other MODEL patches
  (#409), KJNodes Torch Compile environment recommendations (#410), and
  ComfyUI-ppm NegPip Off/On/Turbo conditioning (#411).
- [`aio-hook-extensibility-plan.md`](aio-hook-extensibility-plan.md): follow-on AiO
  extension contract and stage/cache/lifecycle sequencing. It does not authorize
  implementation while a higher-priority release or integration gate is active.
- [`comfy-host-provider-bridge.md`](comfy-host-provider-bridge.md): completed
  historical sequencing addendum for the seven former root Comfy capability and
  invocation wrappers and the minimum runtime-bound provider Contract required
  before the final B-11 shim.
- [`adr-001-modular-monolith.md`](adr-001-modular-monolith.md): why the backend
  converges on a feature-oriented modular monolith under `easyuse_anima`.
- [`adr-002-compatibility-shims.md`](adr-002-compatibility-shims.md): policy for
  introducing, supporting, and retiring root compatibility shims.
- [`python-compatibility-shims.md`](python-compatibility-shims.md): registry schema
  and inventory of root/module compatibility surfaces.

## Authority and scope

- Repository policy remains authoritative for branches, releases, Registry
  publication, and validation: [`MAINTAINING.md`](../../MAINTAINING.md).
- The development-document entry point remains
  [`docs/development/README.md`](../development/README.md).
- The architecture ADRs and ordinary backend roadmap own Python package and
  lifecycle boundaries.
- Cross-surface AiO plans may also cover frontend settings, optional custom-node
  contracts, workflow/profile compatibility, packaging, and live ComfyUI evidence
  when those surfaces are inseparable from the backend execution contract.
- Long-term implementation is tracked by
  [Issue #184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184),
  [Issue #185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185), and
  their child issues. The new advanced integrations are tracked independently by
  [#409](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/409),
  [#410](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/410), and
  [#411](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/411).
- An ADR, roadmap, or sequencing note does not authorize a behavior change,
  package move, merge, version bump, tag, or Registry publication by itself.
