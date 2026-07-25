# Python Backend Architecture

These documents define the target Python backend architecture, migration rules,
and explicitly reviewed cross-surface execution plans for ComfyUI EasyUse Anima.

They are contracts for future work, not a claim that every target package or
feature already exists. Start with the current-state section in
[`python-backend.md`](python-backend.md), then follow the active sequencing notes
below before selecting work from the ordinary backend roadmap.

## Active sequencing notes

- Issue [#415](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/415)
  is the current implementation and release owner for the queue/live-UI
  regressions in [#413](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/413)
  and [#414](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/414).
  While #415 is open, read
  [`queue-ui-execution-state-hotfix.md`](queue-ui-execution-state-hotfix.md)
  **before** the ordinary backend roadmap or any AiO advanced-integration plan.
- Issue [#395](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/395)
  separately tracks the external Comfy Registry activation checkpoint for the
  immutable 0.5.5 release. Waiting for that external approval does not block
  confirmed P1 post-release bug fixes, and it does not authorize rewriting the
  `v0.5.5` tag.
- The DAVE stage-scope, Torch Compile recommendation, and NegPip plans are
  recorded in
  [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md).
  Issues #409, #410, and #411 remain blocked until the #415 hotfix release exits
  and the dependency order is re-audited against the then-current `dev` head.
- New D/E/G/H, AiO Hook, opportunistic cleanup, and unrelated feature work also
  remain paused while the hotfix lane is active.
- The former B-11 Comfy host-provider bridge is complete. Its document remains a
  historical sequencing record and no longer overrides the active queue.

## Documents

- [`queue-ui-execution-state-hotfix.md`](queue-ui-execution-state-hotfix.md):
  active queue-first runbook for stale LoRA/Prompt Studio execution results
  (#413), rgthree-compatible AiO special-seed display semantics (#414), the
  shared transaction/revision Contract, integrated validation, and the patch
  release gate owned by #415.
- [`python-backend.md`](python-backend.md): living architecture, ownership,
  execution phases, validation gates, and overall Definition of Done.
- [`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md):
  verified backend progress, Codex execution protocol, ordered work units, stop
  conditions, and task-level validation gates. Its next-work ordering is paused
  while #415 is open.
- [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md):
  blocked follow-on plan for stage-scoped DAVE and other MODEL patches (#409),
  KJNodes Torch Compile environment recommendations (#410), and ComfyUI-ppm
  NegPip Off/On/Turbo conditioning (#411).
- [`aio-hook-extensibility-plan.md`](aio-hook-extensibility-plan.md): follow-on AiO
  extension contract and stage/cache/lifecycle sequencing. It does not authorize
  implementation while a higher-priority bug, release, or integration gate is
  active.
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
- Cross-surface bug and AiO plans may also cover frontend state, queue identity,
  workflow/profile compatibility, optional custom-node contracts, packaging,
  and live ComfyUI evidence when those surfaces are inseparable from the backend
  execution contract.
- The active hotfix is tracked by
  [#413](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/413),
  [#414](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/414), and
  [#415](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/415).
- Long-term implementation is tracked by
  [#184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184),
  [#185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185), and their
  child issues. The blocked advanced integrations are tracked independently by
  [#409](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/409),
  [#410](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/410), and
  [#411](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/411).
- An ADR, roadmap, or sequencing note does not authorize a behavior change,
  package move, merge, version bump, tag, or Registry publication by itself.
