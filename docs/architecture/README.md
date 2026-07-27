# Python Backend Architecture

These documents define the target Python backend architecture, migration rules,
and explicitly reviewed cross-surface execution plans for ComfyUI EasyUse Anima.

They are contracts for future work, not a claim that every target package or
feature already exists. Before selecting a task, read the bounded execution and
test-escalation policy in
[`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md).
Then follow the active sequencing notes below and read only the current task
section, owning Issue, direct owner files, and direct tests.

## Active sequencing notes

- [`codex-execution-efficiency.md`](../development/codex-execution-efficiency.md)
  applies to every active and ordinary roadmap. It defines the bounded task card,
  focused edit loop, final-full-once rule, package/live/benchmark triggers,
  evidence reuse, and current task-specific test maps. It reduces repeated work;
  it does not weaken an Issue or release gate.
- Issue [#470](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/470) is the
  active P1 post-0.6.0 regression lane. Read
  [`prompt-studio-execution-derived-projection.md`](prompt-studio-execution-derived-projection.md)
  before modifying Prompt Studio queue/result behavior. QSTATE-04C1 is the first
  READY task and targets a 0.6.1 patch.
- Issues [#413](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/413),
  [#414](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/414), and
  [#415](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/415) completed the
  original queue/live-UI hotfix and release lane. Their two-phase correlation and
  seed ownership contracts remain authoritative. Issue #470 supersedes only the
  old classification that treated linked `field_inputs` and NAIA responses as
  non-projectable submitted snapshots.
- Before Prompt Studio wildcard next-seed publication or AiO seed cutover, read
  [`seed-ui-semantics-gate.md`](seed-ui-semantics-gate.md). Prompt Studio uses a
  concrete seed plus an after-generate transition; AiO special `-1/-2/-3` values
  are persistent selection tokens. The shared transaction owner must not merge
  those feature meanings.
- Issue [#395](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/395)
  separately tracks the external Comfy Registry activation checkpoint for the
  immutable 0.5.5 release. Waiting for that external approval does not block
  confirmed P1 post-release bug fixes, and it does not authorize rewriting the
  `v0.5.5` tag.
- The DAVE stage-scope, Torch Compile recommendation, and NegPip plans are
  recorded in
  [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md).
  Issues #409, #410, and #411 and the 0.6.0 release lane #452 are complete.
- Deferred patch-specific follow-ups #440/#441, ordinary backend work,
  opportunistic cleanup, and unrelated features do not jump the active #470
  patch lane.
- The former B-11 Comfy host-provider bridge is complete. Its document remains a
  historical sequencing record and no longer overrides the active queue.

## Documents

- [`../development/codex-execution-efficiency.md`](../development/codex-execution-efficiency.md):
  cross-roadmap Codex context budget, work-packet format, test ladder, invalidation
  rules, compact evidence format, and scoped test maps for queue/UI, AiO integration,
  and ordinary backend work.
- [`prompt-studio-execution-derived-projection.md`](prompt-studio-execution-derived-projection.md):
  active Issue #470 plan separating submitted Prompt Studio snapshots from
  execution-derived linked-input and NAIA deltas; defines latest-accepted queue
  ownership, per-field revisions, persistence rules, one-envelope fan-out,
  implementation units, focused tests, dual-canvas evidence, and the 0.6.1 gate.
- [`queue-ui-two-phase-correlation-addendum.md`](queue-ui-two-phase-correlation-addendum.md):
  identity/revision correction after QSTATE-02A. It separates provisional
  submission, accepted `promptId`, and the executed-event envelope; removes
  mandatory `listIndex` from node-level stale-result correlation; and defines
  cache, subgraph, mapped-result, transaction-core, and envelope-bridge boundaries.
- [`seed-ui-semantics-gate.md`](seed-ui-semantics-gate.md): feature boundary and
  hard test gate separating Prompt Studio Wildcard concrete after-generate seed
  publication from AiO rgthree-style persistent special-token selection, including
  the special-token x stored-control no-double-advance matrix.
- [`queue-ui-execution-state-hotfix.md`](queue-ui-execution-state-hotfix.md):
  historical base runbook for stale LoRA/Prompt Studio execution results (#413),
  rgthree-compatible AiO special-seed display semantics (#414), integrated
  validation, and the completed release gate owned by #415. Its exact-identity-at-
  submission assumptions are superseded by the two-phase addendum.
- [`python-backend.md`](python-backend.md): living architecture, ownership,
  execution phases, validation gates, and overall Definition of Done.
- [`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md):
  verified backend progress, ordered work units, stop conditions, and task-level
  validation gates. Its next-work ordering is paused while #470 is open. When it
  resumes, apply the efficiency protocol instead of rerunning every historical
  inventory and broad test after each edit.
- [`aio-advanced-integrations-roadmap.md`](aio-advanced-integrations-roadmap.md):
  completed sequencing plan for stage-scoped DAVE (#409), KJNodes Torch Compile
  recommendations (#410), and ComfyUI-ppm NegPip (#411). Patch-specific follow-ups
  remain independently tracked.
- [`aio-hook-extensibility-plan.md`](aio-hook-extensibility-plan.md): follow-on AiO
  extension contract and stage/cache/lifecycle sequencing. It does not authorize
  implementation while a higher-priority bug or release gate is active.
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
- The efficiency protocol selects the smallest sufficient evidence and timing;
  it does not permit skipping explicit correctness, compatibility, package, live,
  or release gates owned by a task.
- The architecture ADRs and ordinary backend roadmap own Python package and
  lifecycle boundaries.
- Cross-surface bug and AiO plans may also cover frontend state, queue identity,
  workflow/profile compatibility, optional custom-node contracts, packaging,
  and live ComfyUI evidence when those surfaces are inseparable from the backend
  execution contract.
- The active post-0.6.0 patch is tracked by
  [#470](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/470). Completed
  #413/#414/#415 remain historical contract sources and are not reopened.
- Long-term implementation is tracked by
  [#184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184),
  [#185](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/185), and their
  child issues. Deferred patch-specific integrations are tracked independently by
  [#440](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/440) and
  [#441](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/441).
- An ADR, roadmap, or sequencing note does not authorize a behavior change,
  package move, merge, version bump, tag, or Registry publication by itself.
