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

Snapshot: 2026-07-17 KST, after PR #123 merge/read-back and cleanup, the live
0.5.0 release-state audit, and final release-prep focused validation. The
metadata-only diff on frozen production checkpoint `f5c8694` is ready for PR.

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
- At a validated safe checkpoint, read back `origin/main`, `origin/dev`, tags,
  GitHub Releases, and Registry state; then select a non-conflicting 0.5.x bugfix
  version and complete the approved `dev` -> `main`, Release, and Registry flow.

Excluded without separate approval:

- Security or permission changes beyond the existing protected-branch flow.
- Early or partial sync to the user instance.
- Cleanup of unrelated worktrees whose ownership is not confirmed.

## Current Baseline

| Surface | Confirmed state |
| --- | --- |
| `origin/dev` | `f5c8694cd161c0c304c66666836e6eb8fa816928` |
| local `dev` | same SHA, clean |
| `origin/main` | `8d49c5584b092aa0999ae536a57c40f3ff57af42` (`v0.4.0`) |
| latest integration | PR #123, Autocomplete adapter/request epoch hardening |
| next release | 0.5.0; no conflicting tag, GitHub Release, or Registry version |
| Codex test server | stopped; port 8194 listener and related server/launcher count 0 |
| test-instance canvas setting | `Comfy.VueNodes.Enabled=false` restored |
| user v0.27.0 instance | not synced for this Goal |
| integration-owner task | `019f6a32-3b0f-7ed0-8ff6-03de8546f402` |

## Issue Dashboard

| Issue | State | Completed boundary | Remaining or next action |
| --- | --- | --- | --- |
| #54 AiO Generator | open | PR #107 lifecycle, #113 API queue/hook reentry and missing `prompt_id` no-commit regression, #119 sampler hydration owner and attached-subgraph refresh | direct concurrent API serialization/reservation, final broader matrix, #62/#66 triage, and optional #119 cycle/repeated-node/remove/root-replacement fixtures |
| #55 LoRA Preset | open | #108 menu extraction, #115/#109 lifecycle hardening, #122 canvas-widget extraction | profile mutation, initialize/configure/serialize, save-sync/wheel/entry, final matrix |
| #56 Autocomplete | open | #116 input/keyboard/composition controller and #123 adapter/result/source epoch hardening | external input hook, listener installer/entry, #98/#100, final matrix |
| #98 Autocomplete replacement syntax | open | adapter epoch prerequisite complete | preserve nested parentheses, weights, and artist prefix |
| #99 Autocomplete request epochs | closed | PR #123; focused/full/Legacy/Node 2.0 evidence and final ledger recorded | none |
| #100 Autocomplete result limit | open | none | deferred backend limit audit for configured values 51–100 |
| #102 seed range | closed | production contract #112 and Korean/English user docs #121 | none; #111 remains a separate non-blocking Node 2.0 display mismatch |
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
| #120 | `37c14f8cc10bd43fd33d3a1be76eeeeba435b920` | frontend maintenance execution ledger and repo-local coordination Skill | 396/396; 103 JS; TS 6.0.3 | not required: internal docs/procedure only | no owning feature Issue; merge/read-back and cleanup recorded here |
| #121 | `e7a2cc4c95d40930a5076c25fd5f06a9bcc78c14` | bilingual wildcard seed range and legacy workflow user documentation | 396/396; 103 JS; TS 6.0.3 | reused #112 identical production evidence; docs-only diff | #102 final ledger; Issue closed completed |
| #122 | `3f8a6c0acd25fb0819818b39d3b6f29d70d39f51` | LoRA Preset canvas drawing/hit-testing/strength-drag/widget extraction | 398/398; 104 JS; TS 6.0.3 | not repeated: mechanically identical extraction; final #55 matrix remains | #55 ledger; Issue remains open |
| #123 | `f5c8694cd161c0c304c66666836e6eb8fa816928` | Autocomplete adapter/result/source request epochs | 398/398; 104 JS; TS 6.0.3 | Legacy and Node 2.0 source switch, keyboard, commit, save/reload; errors 0 | #99 final ledger; Issue closed completed; #56 progress ledger |

## Production Lane Ownership

| Slice | Codex task | Branch / worktree | Base and status | Expected files |
| --- | --- | --- | --- | --- |
| 0.5.0 release preparation | integration owner `019f6a32-3b0f-7ed0-8ff6-03de8546f402` | `codex/release-0.5.0` / `worktrees/ComfyUI-EasyUseAnima/codex/release-0.5.0` | base `f5c8694`; production checkpoint frozen; final diff validated and ready for PR | `pyproject.toml`, release/Registry changelog and ledger, development release docs, 11 maintained workflow package versions, this checkpoint |
| remaining production lanes | none active | no branch/worktree assigned | create from latest `origin/dev` only after the release gate and ownership audit | next #54/#55/#56 reviewable slices |

## Integration Gates

Only one row may enter push/PR/merge at a time.

| Order | Slice | Focused / audit | Full | Browser | Blocker / finding | Gate |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | 0.5.0 release preparation | workflow 9/9, validation contract 4/4, scanner safety 4/4, changelog extraction, Registry dry-run, official quick runner (104 JS; TS 6.0.3), `comfy node validate`, diff check, and two no-blocker audits passed | reused frozen `f5c8694` production evidence: unittest 398/398; no repeat because production code/base are unchanged | reused valid #123 Legacy and Node 2.0 evidence | P2 subgraph wording corrected; Registry 0.4.0 is scanner-flagged and 0.5.0 may require administrator approval after publish | ready for release-prep PR |
| 2 | 0.5.0 dev -> main, tag, Release, Registry | enter after release-prep PR squash merge/read-back | release metadata checks must remain valid | no repeat for metadata-only integration | mutation timeout/abort requires read-back before retry | queued |
| 3 | remaining #54/#55/#56 slices | create only after release read-back, cleanup, file ownership, and priority audit | per PR-ready diff | per behavior diff; final Issue matrices required | sequence and overlap audit required | backlog |
| 4 | final user-instance sync | all agreed Issues/bugs reconciled first | use merged `dev` evidence | one manual v0.27.0 confirmation | blocked by remaining Goal work and prerequisites | queued |

Known validation note: Windows sandbox may fail before command/test setup with
`CreateProcessAsUserW 1312`. Record cwd, TEMP variables, runner, and failure
phase; rerun only the identical focused or approved full command outside the
sandbox. Do not report the environment spawn error as a code failure.

## Current Blockers And Findings

- Completed #99 finding: adapter-only epoch clearing could leave pending input
  authority current, and source-key or query-shaping changes could leave a stale
  token query current. PR #123 now invalidates the complete controller request
  authority only when relevant source or query state changes. The first Node 2.0
  stale-tab attempt was excluded; a fresh exact-diff tab passed the full matrix.
- Registry 0.4.0 is `NodeVersionStatusFlagged` because the informational
  network-request scanner detects the explicit, timeout-bound NAIA
  `requests.post` path. The latest active Registry version is therefore 0.3.2.
  Publishing 0.5.0 may succeed but remain unavailable pending administrator
  review. This is not a code blocker and must be reported after publish.
- Registry metadata dry-run showed live 0.3.1, 0.3.0, and 0.2.7 deprecated while
  the previous checked-in ledger marked them active. Release preparation aligns
  those flags so later metadata sync cannot reactivate historical versions.
- Non-blocking #111: ComfyUI frontend 1.45.20 Node 2.0 can display a newly
  entered unsafe seed while the widget and saved workflow retain max-safe.
  Prefer an upstream fix or stable public-API boundary over a private-DOM hook.
- Non-blocking #119 coverage gap: explicit cycle, repeated generator object,
  hydration-before-remove, and root-replacement fixtures remain optional.
- Non-blocking #55 coverage gap: the dedicated smoke is registered and runs in
  the official frontend runner, but no Python static assertion locks that runner
  line; exact canvas paint pixels and extreme scroll counts remain optional.
- Environment: sandbox `CreateProcessAsUserW 1312` is a pre-test process-spawn
  failure, not a repository blocker, when the identical approved rerun passes.

## Approval Gates

- Validated maintenance PRs may be squash-merged to `dev` one at a time without
  another approval during this Goal.
- User documentation for #102 and the coordination plan/repo-local Skill are
  explicitly approved.
- The live main/dev/tag/Release/Registry read-back selected 0.5.0 as the next
  non-conflicting version. After release-prep validation, `main` merge, the
  GitHub Release, and Registry publish/registration are explicitly approved.
  Do not pull any open or unfrozen maintenance lane into that release.
- Early user-instance changes remain unapproved.
- GitHub mutation timeout/abort always requires state read-back before retry.

## Cleanup And Sync

- The #103 Regional, #54 sampler-hydration, #120 coordination, #121 user-doc,
  #122 LoRA canvas, and #123 Autocomplete source/integration branches and
  worktrees were removed after merge-tree equality and clean-state checks.
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
