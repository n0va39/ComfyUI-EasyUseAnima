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

Snapshot: 2026-07-17 KST, after the complete 0.5.0 release checkpoint:
release-prep PR #124, main release PR #125, annotated tag, GitHub Release,
Registry publish/metadata sync, and tree-identical main-to-dev ancestry
alignment. Registry 0.5.0 is published and pending administrator review.
A later user-manual 0.5.0 application produced a separate #56 runtime failure
report; reproduction surface and installation completeness remain unconfirmed.

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
- Agent-driven early or partial sync to the user instance. The user's later
  manual 0.5.0 application is diagnostic input, not an agent sync checkpoint.
- Cleanup of unrelated worktrees whose ownership is not confirmed.

## Current Baseline

| Surface | Confirmed state |
| --- | --- |
| `origin/dev` | `a590b1a9fe3130708e96b6d545a471cae3256aa2` |
| local `dev` | same SHA, clean |
| `origin/main` | `f559993a33f86f1345ce027e83100834da8c600f` (`v0.5.0`) |
| local `main` | same SHA, clean |
| main/dev alignment | main is an ancestor of dev; both tree `6089f47214a004eb350301fdb626981b1a35aa53` |
| latest dev integration | PR #124, 0.5.0 release preparation; ancestry alignment `a590b1a` |
| GitHub Release | `v0.5.0`, published with manual-install ZIP |
| Registry | 0.5.0 published; metadata matches; `NodeVersionStatusPending` |
| Codex test server | stopped; port 8194 listener and related server/launcher count 0 |
| test-instance canvas setting | `Comfy.VueNodes.Enabled=false` restored |
| user v0.27.0 instance | user manually applied 0.5.0; tag tooltip works but typed Autocomplete suggestions never appear; exact canvas/settings/load state not yet confirmed |
| integration-owner task | `019f6a32-3b0f-7ed0-8ff6-03de8546f402` |

## Issue Dashboard

| Issue | State | Completed boundary | Remaining or next action |
| --- | --- | --- | --- |
| #54 AiO Generator | open | PR #107 lifecycle, #113 API queue/hook reentry and missing `prompt_id` no-commit regression, #119 sampler hydration owner and attached-subgraph refresh | direct concurrent API serialization/reservation, final broader matrix, #62/#66 triage, and optional #119 cycle/repeated-node/remove/root-replacement fixtures |
| #55 LoRA Preset | open | #108 menu extraction, #115/#109 lifecycle hardening, #122 canvas-widget extraction | profile mutation, initialize/configure/serialize, save-sync/wheel/entry, final matrix |
| #56 Autocomplete | open | #116 input/keyboard/composition controller and #123 adapter/result/source epoch hardening | highest-priority separate 0.5.0 runtime failure report: tooltip works but suggestions never appear; diagnose before calling it a code regression or associating it with #98/#99/#100, then external input hook, listener installer/entry, #98/#100, and final matrix |
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
| #124 | `1c614ad3f6d617b47f137d7d65d7414d0cd0721b` | 0.5.0 package, Registry, changelog, workflow, release, and execution metadata | release-focused tests, quick runner, `comfy node validate`, and two audits passed; reused frozen production full 398/398 | reused #123 valid Legacy and Node 2.0 evidence; metadata-only diff | release-prep merge/read-back; no feature Issue closure |

## 0.5.0 Release Checkpoint

| Surface | Final evidence |
| --- | --- |
| release-prep PR | #124, squash merge `1c614ad3f6d617b47f137d7d65d7414d0cd0721b` |
| main release PR | #125, squash merge `f559993a33f86f1345ce027e83100834da8c600f` |
| tag | annotated `v0.5.0`; tag object `7dd2c4a0211a2679be279208bf84e74ba3aca3b3`; peeled commit `f559993a` |
| GitHub Release | `https://github.com/n0va39/ComfyUI-EasyUseAnima/releases/tag/v0.5.0` |
| manual ZIP | `ComfyUI-EasyUseAnima-0.5.0-manual-install.zip`, 27,157,336 bytes, SHA256 `5AB89C901D24547CF5228AB86505DC72E3913E4F5CA4B5FD20F984090507CC87` |
| Registry publish | workflow run `29554118840`, main `f559993a`, success; validation and upload successful |
| Registry metadata | workflow run `29554178068`, main `f559993a`, success; final dry-run is a metadata no-op |
| Registry status | 0.5.0 `NodeVersionStatusPending`; 0.4.0 `NodeVersionStatusFlagged`; administrator review remains external |
| dev alignment | `a590b1a9fe3130708e96b6d545a471cae3256aa2`, tree-identical merge of `origin/main` into `dev` |

The release checkpoint does not close the maintenance Goal. Open #54, #55,
and #56 boundaries and the agreed related bugs remain scheduled before the
single final user-instance sync.

## Production Lane Ownership

| Slice | Codex task | Branch / worktree | Base and status | Expected files |
| --- | --- | --- | --- | --- |
| 0.5.0 release checkpoint ledger | integration owner `019f6a32-3b0f-7ed0-8ff6-03de8546f402` | `codex/record-0.5.0-release-checkpoint` / `worktrees/ComfyUI-EasyUseAnima/codex/record-0.5.0-release-checkpoint` | base `a590b1a`; docs-only checkpoint active | this execution ledger and development entry index only |
| remaining production lanes | none active | no branch/worktree assigned | create from latest `origin/dev` only after this checkpoint merge/cleanup and ownership audit | next #54/#55/#56 reviewable slices |

## Integration Gates

Only one row may enter push/PR/merge at a time.

| Order | Slice | Focused / audit | Full | Browser | Blocker / finding | Gate |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | 0.5.0 release checkpoint | PR #124/#125, tag, Release, ZIP digest, publish run, metadata run, Registry dry-run, and main/dev ancestry/tree read-back complete | reused frozen `f5c8694` production full 398/398; release-only metadata focused checks passed | reused valid #123 Legacy and Node 2.0 evidence | Registry 0.5.0 is pending external administrator review | complete |
| 2 | post-release execution ledger | docs entry and this ledger only; diff check and content audit required | no runtime/full repeat | no browser repeat | no production code or runtime behavior change | active |
| 3 | #56 0.5.0 runtime failure report | first determine Legacy/Node 2.0 surface, settings/source, input/composition and external DOM hooks, listener/extension install, popup DOM/visibility, served modules/cache, and console/API errors | focused diagnosis first; regression coverage required after a code root cause | Legacy and Node 2.0 input/select/close/save-reload required after any fix | keep separate from #98/#99/#100 until evidence identifies the cause | next blocker |
| 4 | remaining #54/#55/#56 slices | create only after checkpoint merge/cleanup, file ownership, and priority audit | per PR-ready diff | per behavior diff; final Issue matrices required | sequence and overlap audit required | backlog |
| 5 | final user-instance sync | all agreed Issues/bugs and the new #56 runtime failure reconciled first | use merged `dev` evidence | one final manual v0.27.0 confirmation | blocked by the new runtime failure report and remaining Goal work | queued |

Known validation note: Windows sandbox may fail before command/test setup with
`CreateProcessAsUserW 1312`. Record cwd, TEMP variables, runner, and failure
phase; rerun only the identical focused or approved full command outside the
sandbox. Do not report the environment spawn error as a code failure.

## Current Blockers And Findings

- New #56 runtime blocker from the user-manually-updated 0.5.0 instance:
  hover tag-meaning tooltips work, but typing never shows the Autocomplete
  suggestion list. Tooltip success proves only that part of tag metadata is
  available; it does not prove suggestion controller or input-hook ownership.
  The exact canvas surface, settings/source, input/composition hook, external
  DOM input hook, listener/extension installation, popup DOM/visibility, module
  import/404/API console state, and browser-loaded module cache are unconfirmed.
  Audit every `web/js/autocomplete/*` dependency and served response, not only
  the entry-file hash, because the manual update may have been partial. Keep
  this separate from #98/#99/#100 until a root cause is reproduced. The
  dedicated checklist is recorded in Issue #56 comment `4998957365`.

- Completed #99 finding: adapter-only epoch clearing could leave pending input
  authority current, and source-key or query-shaping changes could leave a stale
  token query current. PR #123 now invalidates the complete controller request
  authority only when relevant source or query state changes. The first Node 2.0
  stale-tab attempt was excluded; a fresh exact-diff tab passed the full matrix.
- Registry 0.5.0 upload and metadata sync succeeded, but the version is
  `NodeVersionStatusPending` until external administrator review completes.
  Registry 0.4.0 remains `NodeVersionStatusFlagged` because the informational
  network-request scanner detects the explicit, timeout-bound NAIA
  `requests.post` path. The latest active Registry version remains 0.3.2.
  This external review state is reported and is not a maintenance code blocker.
- Registry node metadata, every checked-in version changelog, and historical
  deprecation flags now match the live service. The final metadata dry-run is
  a no-op and cannot reactivate 0.3.1, 0.3.0, or 0.2.7.
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
- The approved 0.5.0 `main` merge, GitHub Release, and Registry publish are
  complete. The release did not include open or unfrozen maintenance lanes.
  Any later release still requires a new state read-back and safe checkpoint.
- Agent-driven early user-instance changes remain unapproved. User-performed
  manual state is diagnostic input and does not expand agent sync authority.
- GitHub mutation timeout/abort always requires state read-back before retry.

## Cleanup And Sync

- The #103 Regional, #54 sampler-hydration, #120 coordination, #121 user-doc,
  #122 LoRA canvas, and #123 Autocomplete source/integration branches and
  worktrees were removed after merge-tree equality and clean-state checks.
- The #124 release-prep branch/worktree and remote branch were removed after
  squash-merge tree equality and local/remote read-back.
- Main `f559993a` is an ancestor of dev `a590b1a`, and their trees are equal.
- The temporary release ZIP, GitHub notes, and extracted changelog were removed
  after the uploaded asset digest and public Release were read back.
- Existing unrelated `codex/*`, `fix/*`, and `feature/*` worktrees are untouched.
- The Codex test server is stopped and port 8194 is free.
- The integration owner has not synced the user v0.27.0 instance. The user
  manually applied 0.5.0 and reported the #56 suggestion-popup failure.
  Read-only diagnosis is now required; do not treat this as the final sync.
  After all agreed maintenance and related bugs are merged, apply one compatible
  full bundle immediately before the final manual confirmation.

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
