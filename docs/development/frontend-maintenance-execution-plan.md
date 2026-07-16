# Frontend Maintenance Execution Plan

## Document Contract

This is the version-controlled execution ledger for the active frontend
maintenance Goal. It complements the long-lived scope in
`frontend-maintenance-roadmap.md`; it does not replace that roadmap, the owning
GitHub Issue ledgers, or live Git/GitHub/Codex/process read-back.

- Owner: the integration-owner Codex task only.
- Update points: lane creation or clean handoff, blocker/review-fix resolution,
  frozen full/browser evidence, PR creation or merge read-back, Issue-ledger
  update or cleanup, and final user-instance sync.
- Production lanes must not edit this file, shared runner files, `jsconfig.json`,
  or `tests/frontend_support/*`.
- Before using this snapshot, fetch and reconcile the external state named in
  the relevant row.

Snapshot: 2026-07-17 KST, immediately after PR #119 cleanup.

## Goal Boundary

Objective: finish the agreed frontend maintenance boundaries for Issues #54,
#55, and #56; finish the seed dependency chain #102 -> #103 -> #104; integrate
the agreed related bug boundaries; then prepare one final manual check on the
user ComfyUI v0.27.0 instance.

Included:

- Separate production lanes with focused validation and clean local commits.
- Sequential integration audit, official full validation, required legacy and
  Node 2.0 browser smoke, `dev` PR, squash merge, Issue ledger, and cleanup.
- #102 user documentation and this coordination plan/project Skill.

Excluded without separate approval:

- `main` merge, release, tag, Registry publish, or security/permission changes.
- Early or partial sync to the user instance.
- Cleanup of unrelated worktrees whose ownership is not confirmed.

## Current Baseline

| Surface | Confirmed state |
| --- | --- |
| `origin/dev` | `4119012881f4d1b35f61a29704fb18d23602a06d` |
| local `dev` | same SHA, clean |
| latest integration | PR #119, AiO sampler hydration ownership |
| Codex test server | stopped; port 8194 listener and related server/launcher count 0 |
| test-instance canvas setting | `Comfy.VueNodes.Enabled=false` restored |
| user v0.27.0 instance | not synced for this Goal |
| integration-owner task | `019f6a32-3b0f-7ed0-8ff6-03de8546f402` |

## Issue Dashboard

| Issue | State | Completed boundary | Remaining or next action |
| --- | --- | --- | --- |
| #54 AiO Generator | open | PR #107 lifecycle, #113 API queue/hook reentry and missing `prompt_id` no-commit regression, #119 sampler hydration owner and attached-subgraph refresh | direct concurrent API serialization/reservation, final broader matrix, #62/#66 triage, and optional #119 cycle/repeated-node/remove/root-replacement fixtures |
| #55 LoRA Preset | open | #108 extraction, #115/#109 lifecycle hardening | integrate canvas-widget extraction; then profile mutation, initialize/configure/serialize, save-sync/wheel/entry, final matrix |
| #56 Autocomplete | open | #116 input/keyboard/composition controller | integrate #99 adapter epoch; then external input hook, listener installer/entry, #98/#100, final matrix |
| #102 seed range | open | production contract merged in #112 | approved Korean/English user docs; record #111 as non-blocking Node 2.0 display mismatch |
| #103 Regional seed | closed | PR #118 and final ledger | none |
| #104 subgraph Advanced seed | closed | PR #117 and final ledger | optional non-blocking settlement coverage only |
| #105 seed lifecycle | closed | PR #110 and final ledger | do not reimplement |
| #109 LoRA lifecycle | closed | PR #115 and final ledger | preserve in later #55 slices |
| #111 Node 2.0 seed display | open | root cause filed against frontend 1.45.20 behavior | wait for upstream or stable public-API boundary; do not use a private-DOM workaround in #102 docs |

## Merged Slices

This active-Goal snapshot starts at PR #106. Earlier maintenance history remains
in the roadmap and owning Issue ledgers.

| PR | Dev merge SHA | Boundary | Full | Browser | Ledger |
| --- | --- | --- | --- | --- | --- |
| #106 | `7dea0bd1ec023f1480c5f1b8c0bcf2fa0703df33` | Prompt Studio queue seed reservation | complete | status recorded in owning Issue | recorded |
| #107 | `a672af4c7d4fbb6627bdfdc03b16fcf88162b26a` | AiO extension lifecycle extraction | complete | status recorded in owning Issue | recorded |
| #108 | `bfe2307872c86cf1d3d001f331196ca46dfe4dae` | LoRA menu lifecycle extraction | complete | status recorded in owning Issue | recorded |
| #110 | `aa7b47d7b430a45ce6979fcaae9c532aadd82b91` | queue seed state lifecycle cleanup | complete | status recorded in owning Issue | recorded |
| #112 | `82a8cebdc4354e6035211d3a7c0964d3e16d4223` | JavaScript/Python wildcard seed range contract | complete | status recorded in #102 | recorded |
| #113 | `2fc21d82c16875d4885387037165c6d179b6e0bb` | AiO queue/API and hook reentry safety | complete | status recorded in #54 | recorded |
| #114 | `595e550dacc39efe9cd14f80c73fc3682bc9a119` | native Wildcard consecutive queue reservation | complete | status recorded in #103 | recorded |
| #115 | `3eec01ed96641154a4f2d62129238df585f67844` | LoRA menu/preview/install-dispose hardening | complete | status recorded in #109/#55 | recorded |
| #116 | `98fe264e7157efd5b0080f03e2d05d61f12119af` | Autocomplete input controller lifecycle | complete | status recorded in #56 | recorded |
| #117 | `4b68cc4dfc1b402070939f51fd216c40e8b632a8` | Advanced node native-subgraph reservation | complete | status recorded in #104 | recorded |
| #118 | `44eb91c1335f563e7ec05a9bf65fa74e1e219676` | Regional queue seed reservation | 395/395; 103 JS; TS 6.0.3 | Legacy and Node 2.0, 512×512 rapid queue 3/3 each | #103 final ledger |
| #119 | `4119012881f4d1b35f61a29704fb18d23602a06d` | AiO sampler hydration single owner and attached-subgraph refresh | 396/396; 103 JS; TS 6.0.3 | Legacy and Node 2.0 512×512 queue/save-reload; attached native subgraph; EasyUse errors 0 | #54 ledger; Issue remains open |

## Production Lane Ownership

| Slice | Codex task | Branch / worktree | Base and status | Expected files |
| --- | --- | --- | --- | --- |
| #55 canvas widgets | `019f6b77-702f-7863-8706-cc5db859b360` | `codex/extract-lora-canvas-widgets`; `worktrees/ComfyUI-EasyUseAnima/codex/extract-lora-canvas-widgets` | clean HEAD `6d2386777181d24472b6cfa4ce090ee630a12d71` on `4119012`; focused checks and two audits passed | `web/js/lora_preset/canvas_widgets.js`, LoRA entry, dedicated smoke and unittest |
| #56/#99 adapter epoch | `019f6bc5-c33b-7960-b84e-0f2300525f2a` | `codex/fix-autocomplete-adapter-epoch`; `worktrees/ComfyUI-EasyUseAnima/codex/fix-autocomplete-adapter-epoch` | clean HEAD `f34bdaa224a34c2bd3097c24e77cd45258486079` on `4119012`; focused 43/43 and two audits passed | `web/js/autocomplete/data_adapter.js`, dedicated adapter smoke |
| coordination plan/Skill | integration owner | `codex/docs-frontend-maintenance-plan`; `worktrees/ComfyUI-EasyUseAnima/codex/docs-frontend-maintenance-plan` | base `4119012`; active | this plan, repo-local Skill, development-doc links only |
| #102 user docs | queued | branch/worktree/task not created | start from latest `origin/dev` after coordination PR cleanup | `docs/wildcards.ko.md`, `docs/wildcards.en.md`; optional canonical links only |

## Integration Gates

Only one row may enter push/PR/merge at a time.

| Order | Slice | Focused / audit | Full | Browser | Blocker / finding | Gate |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | coordination plan/Skill | structure, link, YAML, and Skill validation plus two final audits passed after review-fix | run once on final diff | not required: internal docs/procedure only | no known blocker | current |
| 2 | #102 user docs | production evidence already merged; docs review pending | run once on final diff | reuse #112 identical production evidence; docs do not change runtime | #111 is non-blocking and separately tracked | queued |
| 3 | #55 canvas widgets | focused tests and two extraction audits passed | integration owner registers smoke, then one full run | omit for mechanical extraction; final #55 matrix remains required before Issue close | no known blocker | queued |
| 4 | #56/#99 adapter epoch | focused 43/43, range-diff, and two audits passed | one full run | required once per final behavior diff on legacy and Node 2.0 | no known blocker | queued |
| 5 | remaining #54/#55/#56 slices | create only after file ownership and priority audit | per PR-ready diff | per behavior diff; final Issue matrices required | sequence and overlap audit required | backlog |
| 6 | final user-instance sync | all agreed Issues/bugs reconciled first | use merged `dev` evidence | one manual v0.27.0 confirmation | blocked by remaining Goal work and prerequisites | queued |

Known validation note: Windows sandbox may fail before command/test setup with
`CreateProcessAsUserW 1312`. Record cwd, TEMP variables, runner, and failure
phase; rerun only the identical focused or approved full command outside the
sandbox. Do not report the environment spawn error as a code failure.

## Current Blockers And Findings

- Blocking the current coordination gate: none known.
- Non-blocking #111: ComfyUI frontend 1.45.20 Node 2.0 can display a newly
  entered unsafe seed while the widget and saved workflow retain max-safe.
  Prefer an upstream fix or stable public-API boundary over a private-DOM hook.
- Non-blocking #119 coverage gap: explicit cycle, repeated generator object,
  hydration-before-remove, and root-replacement fixtures remain optional.
- Environment: sandbox `CreateProcessAsUserW 1312` is a pre-test process-spawn
  failure, not a repository blocker, when the identical approved rerun passes.

## Approval Gates

- Validated maintenance PRs may be squash-merged to `dev` one at a time without
  another approval during this Goal.
- User documentation for #102 and the coordination plan/repo-local Skill are
  explicitly approved.
- `main`, release, tag, Registry publish, and early user-instance changes are not
  approved.
- GitHub mutation timeout/abort always requires state read-back before retry.

## Cleanup And Sync

- The #103 Regional lane and #54 sampler-hydration lane branches/worktrees were
  removed after merge-tree equality and clean-state checks.
- Existing unrelated `codex/*`, `fix/*`, and `feature/*` worktrees are untouched.
- The Codex test server is stopped and port 8194 is free.
- The user v0.27.0 instance remains untouched until all agreed maintenance and
  related bug work is merged. At that point sync the compatible full bundle
  once immediately before the manual check.

## Checkpoint Rules

At every safe checkpoint, update this file with:

1. current `origin/dev` and local `dev` SHA/dirty state;
2. Issue state and merged PR/SHA;
3. active and queued task id, branch, worktree, base, owner, and expected files;
4. focused, audit, official full, legacy, Node 2.0, and user-instance evidence;
5. blockers, stable findings, approval gates, next action, and cleanup state.

Do not mark a lane integrated until PR and merge SHA are read back. Do not mark
the Goal complete until all agreed boundaries are merged, Issue ledgers are
reconciled, cleanup is complete, and the final user-instance preparation is
recorded.
