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

Snapshot: 2026-07-17 KST, after checkpoint PR #134 and the Autocomplete
per-input binding lifecycle integration in PR #135. PR/Issue read-back,
squash-tree preservation, lane cleanup, full and dual-canvas evidence, and
Codex server cleanup are complete. The formal maintenance Goal remains active
for the open #54/#55/#56 boundaries and directly related #62/#98 work.

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
| `origin/dev` | `19a8968a15885801b43f831ef9c582380bf514f9` |
| local `dev` | same SHA, clean |
| `origin/main` | `02a9a84634c03cc3afaa20000f136c03164308ce` (`v0.5.1`) |
| local `main` | same SHA, clean |
| main/dev alignment | main is an ancestor of dev; dev additionally contains the post-release integrations and checkpoints through PR #135 |
| latest dev integration | PR #135, Autocomplete per-input binding lifecycle, squash merge `19a8968a15885801b43f831ef9c582380bf514f9` |
| GitHub Release | `v0.5.1` public/Latest with verified manual-install ZIP; broken `v0.5.0` Release/tag absent |
| Registry | live versions API on 2026-07-17: 0.5.1 and 0.4.0 `NodeVersionStatusFlagged`, 0.3.2 latest active, deleted 0.5.0 absent; read back again before release/Registry action |
| Codex test server | stopped; port 8194 listener and related server/launcher count 0 |
| test-instance canvas setting | `Comfy.VueNodes.Enabled=false` restored |
| user v0.27.0 instance | user classified the manual 0.5.0 state as invalid and planned its removal; no agent-driven replacement sync before the final Goal checkpoint |
| integration-owner task | formal Goal task `019f6f25-d26c-77a1-95dc-092cdb8e756c` |

## Issue Dashboard

| Issue | State | Completed boundary | Remaining or next action |
| --- | --- | --- | --- |
| #54 AiO Generator | open | PR #107 lifecycle, #113 API queue/hook reentry and missing `prompt_id` no-commit regression, #119 sampler hydration owner/attached-subgraph refresh, #133 preview-wheel ownership | direct concurrent API serialization/reservation, final broader matrix, #62 Detailer threshold, #66 triage, and optional #119 fixtures |
| #55 LoRA Preset | open | #108 menu extraction, #115/#109 lifecycle hardening, #122 canvas-widget extraction, #132 node initialize/configure/serialize lifecycle extraction | profile mutation, save-sync/wheel/entry, final matrix |
| #56 Autocomplete | open | #116 controller, #123 request epochs, #127 Registry import closure, #131 1-100 result limit, and #135 per-input listener/disposer lifecycle | external DOM owner disposal, global listener/window hook/prototype wrapper installer/entry lifecycle, #98, and final cumulative matrix; user-instance confirmation remains blocked until the final Goal sync |
| #98 Autocomplete replacement syntax | open | adapter epoch prerequisite complete | preserve nested parentheses, weights, and artist prefix |
| #99 Autocomplete request epochs | closed | PR #123; focused/full/Legacy/Node 2.0 evidence and final ledger recorded | none |
| #100 Autocomplete result limit | closed | PR #131; backend/API/frontend normalized 1-100 contract and completion ledger | none |
| #62 AiO Detailer/preview behavior | open | PR #133 completed the preview-wheel boundary with full and dual-canvas evidence | Detailer threshold behavior remains; do not close from the wheel slice |
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
| #126 | `1bd6ee1b727fddfb37616644a30fd95605fc9d5e` | 0.5.0 release checkpoint ledger | docs-focused checks; no production diff | not required | release state recorded before the package defect was confirmed |
| #127 | `b90286848cfb178204a33fca6493548b652fd0c4` | preserve the complete Autocomplete import closure in Registry packages | 400/400; 104 JS; TS 6.0.3; `comfy node validate`; actual package closure 8/8 | Legacy and Node 2.0 input, suggestions, keyboard select, close, save/reload; relevant errors 0 | #56 package-regression ledger; Issue remains open |
| #128 | `c74708d29b53c62b483282b2d10fbada12ee6642` | 0.5.1 package, Registry, changelog, workflow, release, and execution metadata | focused 19/19; quick runner; `comfy node validate`; actual package 138 files; two audits GO | reused exact #127 Legacy and Node 2.0 evidence; metadata/docs/workflow-only diff | release-prep merge/read-back; no feature Issue closure |
| #130 | `715384d93698009111dea158395d2541d905674e` | record the verified 0.5.1 replacement and corrected release/Registry guidance | docs/Skill-focused validation; no production diff | not required | checkpoint, merge/read-back, and cleanup recorded |
| #131 | `b5743b0da6b4f51ddbd146257cbf2803cceeddc0` | Autocomplete configured result limit 1-100 | 402/402; 104 JS; TS 6.0.3 | not required: backend/API/frontend contract regression | #100 final ledger; Issue closed completed; #56 progress ledger |
| #132 | `72d55c74e1ba02aeb6eb522ab398fc75220ae053` | LoRA Preset per-node initialize/configure/serialize lifecycle extraction | 404/404; 105 JS; TS 6.0.3 | not repeated: mechanical extraction with behavior and ownership audits | #55 ledger; Issue remains open |
| #133 | `2dc93fe0bf17623b51203bcf40db0854776ee8bf` | AiO preview/non-overflow-feed wheel ownership | 404/404; 105 JS; TS 6.0.3 | Legacy and Node 2.0 512x512 queue, preview/feed wheel, canvas forwarding, save/reload; EasyUse errors 0 | #54/#62 ledgers; both Issues remain open |
| #134 | `e4deeec6b722d2fde9b849a2358dabb4eb584e9b` | record PR #130-#133 checkpoint and lane model-selection policy | Skill validation and independent audit; no runtime diff | not required: docs/Skill-only diff | merge/read-back and cleanup recorded here |
| #135 | `19a8968a15885801b43f831ef9c582380bf514f9` | Autocomplete per-input listener, controller, timer, middle-pan, registry, and disposer lifecycle | 405/405; 106 JS; TS 6.0.3; focused 50/50; diff checks | Legacy and Node 2.0 suggestion/keyboard/Escape/blur/single-popup/save-reload; separate output-capable fixture 512x512 queue success; no new relevant browser error | #56 lifecycle ledger; Issue remains open |

## 0.5.0 Release And Withdrawal Checkpoint

| Surface | Final evidence |
| --- | --- |
| release-prep PR | #124, squash merge `1c614ad3f6d617b47f137d7d65d7414d0cd0721b` |
| main release PR | #125, squash merge `f559993a33f86f1345ce027e83100834da8c600f` |
| tag | former annotated `v0.5.0` tag object `7dd2c4a0211a2679be279208bf84e74ba3aca3b3`; remote and local tag now deleted |
| GitHub Release | Release and asset deleted after 0.5.1 replacement verification |
| manual ZIP | deleted public asset; historical digest was SHA256 `5AB89C901D24547CF5228AB86505DC72E3913E4F5CA4B5FD20F984090507CC87` |
| Registry publish | workflow run `29554118840`, main `f559993a`, success; validation and upload successful |
| Registry metadata | workflow run `29554178068`, main `f559993a`, success; final dry-run is a metadata no-op |
| Registry status | 0.5.0 is now `NodeVersionStatusDeleted`; its CDN object can still return the old payload and must not be treated as active |
| dev alignment | `a590b1a9fe3130708e96b6d545a471cae3256aa2`, tree-identical merge of `origin/main` into `dev` |

The 0.5.0 package is withdrawn because `.comfyignore` omitted required
Autocomplete controller modules. The defect is fixed in PR #127; 0.5.0 must
not be republished. Both 0.5.1 archives were independently downloaded and
verified before the broken public 0.5.0 GitHub surfaces were removed.

## 0.5.1 Replacement Checkpoint

| Surface | Final evidence |
| --- | --- |
| release-prep PR | #128, squash merge `c74708d29b53c62b483282b2d10fbada12ee6642` |
| main release PR | #129, squash merge `02a9a84634c03cc3afaa20000f136c03164308ce` |
| tag | annotated `v0.5.1`; tag object `07fb6fcc8ed06fdb7390107b01e2bd75e812906d`; peeled commit `02a9a846` |
| GitHub Release | `https://github.com/n0va39/ComfyUI-EasyUseAnima/releases/tag/v0.5.1`; public and Latest |
| manual ZIP | 27,163,430 bytes; exact 345-file tagged tree under `ComfyUI-EasyUseAnima/`; SHA256 `AC9813B49E87C83CC22F66C5BC9A444720615663270A2811DC6AA7C505362552` |
| production tree | frozen at PR #127; release preparation changes metadata, docs, and maintained workflow versions only |
| frozen full | Python unittest 400/400; 104 frontend JavaScript files; TypeScript 6.0.3; diff checks |
| Registry publish | run `29558688905`, exact main `02a9a84`, success; validation and upload passed |
| Registry metadata | run `29558759993`, exact main `02a9a84`, success; final dry-run no-op |
| Registry archive | 12,883,225 bytes; 138 files; every file byte-equal to exact-main Git blobs; package version 0.5.1; Autocomplete closure 8/8; SHA256 `30A5AB952D478DB3E9A05F12F928FB3663C8119264389A4AF5BC0BB16CA241D9` |
| Registry status | at the 0.5.1 publish checkpoint: 0.5.1 `NodeVersionStatusPending`, 0.4.0 `NodeVersionStatusFlagged`; the current live 0.5.1 state has since changed to `NodeVersionStatusFlagged` and is tracked below |
| browser | Legacy and Node 2.0 input, 20-result popup, keyboard select, Escape close, and save/reload passed; relevant module/404 errors 0 |
| dev alignment | `1efcb401a999c42246d41bf21371b12912297b6e`, tree-identical merge of `origin/main` into `dev` |

This replacement checkpoint also does not close the maintenance Goal. Open
#54, #55, and #56 boundaries and the agreed related bugs remain scheduled
before the single final user-instance sync.

## Production Lane Ownership

| Slice | Codex task | Branch / worktree | Base and status | Expected files |
| --- | --- | --- | --- | --- |
| #135 checkpoint ledger | integration owner `019f6f25-d26c-77a1-95dc-092cdb8e756c` | `codex/record-maintenance-checkpoint-135` / `worktrees/ComfyUI-EasyUseAnima/codex/record-maintenance-checkpoint-135` | base `19a8968`; docs-only checkpoint active | this execution ledger only |
| remaining production lanes | none active | no branch/worktree assigned | create from latest `origin/dev` only after this checkpoint merge/cleanup and ownership audit | next #56 installer/entry lifecycle; then bounded #54/#55 slices and direct #62/#98 blockers |

## Integration Gates

Only one row may enter push/PR/merge at a time.

| Order | Slice | Focused / audit | Full | Browser | Blocker / finding | Gate |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | #56 Registry package hotfix | PR #127 merged; actual archive/import-closure validation and audits complete | 400/400; 104 JS; TS 6.0.3 | Legacy and Node 2.0 complete | no production finding remains | complete |
| 2 | 0.5.1 release preparation | PR #128 focused validation, actual package, and two audits complete | reused exact PR #127 frozen full | reused exact PR #127 dual-canvas evidence | production-tree neutral | complete |
| 3 | 0.5.1 publish and replacement | PR #129, tag, GitHub asset, Registry runs, both public archive read-backs, and 0.5.0 removal complete | no repeat; production tree unchanged | no repeat; production tree unchanged | publish checkpoint was Pending; current live 0.5.1 status is Flagged and reopens the next-release gate | complete |
| 4 | post-release ledger/docs | PR #130 merged and cleaned | no runtime/full repeat | no browser repeat | no production code change | complete |
| 5 | #100 Autocomplete result limit | PR #131 merged; correctness and regression audits GO | 402/402; 104 JS; TS 6.0.3 | deterministic backend/API/frontend boundary; no browser repeat | no finding remains; Issue #100 closed | complete |
| 6 | #55 LoRA node lifecycle extraction | PR #132 merged; behavior and ownership audits GO | 404/404; 105 JS; TS 6.0.3 | mechanical extraction; no browser repeat | #55 remains open for profile/save-sync/entry/final matrix | complete |
| 7 | #54/#62 AiO preview wheel | PR #133 merged; three audits GO | 404/404; 105 JS; TS 6.0.3 | Legacy and Node 2.0 512x512 queue/wheel/save-reload complete | live feed did not overflow; deterministic X-scroll/boundary regression passed; Detailer threshold remains | complete |
| 8 | #130-#133 checkpoint ledger/Skill | PR #134 merged, read back, and cleaned | no runtime/full repeat | no browser repeat | no production code change | complete |
| 9 | #56 per-input binding lifecycle | PR #135 merged; correctness/test/scope audits and Issue read-back complete | 405/405; 106 JS; TS 6.0.3 | Legacy and Node 2.0 popup lifecycle/save-reload and queue complete | package failure remains attributed to #127; installer/global lifecycle remains | complete |
| 10 | #135 checkpoint ledger | current docs-only branch; focused validation and read-back required | no runtime/full repeat | no browser repeat | no production code change | active |
| 11 | #56 installer/entry lifecycle | create after checkpoint merge/cleanup from current `origin/dev` | per PR-ready diff | dual-canvas re-entry and final cumulative input matrix | external DOM owner disposal and global installer authority remain | queued |
| 12 | remaining #54/#55/#62/#98 slices | bounded lanes from the then-current `origin/dev` | per PR-ready diff | per behavior diff; final Issue matrices required | sequence and overlap audit required | backlog |
| 13 | release, Registry, and final user-instance sync | all agreed boundaries and direct blockers reconciled first | final merged `dev` full | final dual-canvas plus one compatible v0.27.0 bundle confirmation | blocked by remaining Goal work | queued |

Known validation note: Windows sandbox may fail before command/test setup with
`CreateProcessAsUserW 1312`. Record cwd, TEMP variables, runner, and failure
phase; rerun only the identical focused or approved full command outside the
sandbox. Do not report the environment spawn error as a code failure.

## Current Blockers And Findings

- Resolved #56 release blocker: the user-visible 0.5.0 failure came from an
  incomplete Registry archive, not the earlier #98/#99/#100 behavior bugs.
  `.comfyignore` excluded `web/js/autocomplete/`, while tooltip metadata still
  loaded through a separate path. PR #127 anchors the root data directory only,
  recursively validates the entry import closure, and passed actual packaged
  Legacy/Node 2.0 checks. The dedicated final ledger is Issue #56 comment
  `4999279403`; Issue #56 remains open for its other planned boundaries.

- Completed #99 finding: adapter-only epoch clearing could leave pending input
  authority current, and source-key or query-shaping changes could leave a stale
  token query current. PR #123 now invalidates the complete controller request
  authority only when relevant source or query state changes. The first Node 2.0
  stale-tab attempt was excluded; a fresh exact-diff tab passed the full matrix.
- Completed #100 finding: the backend capped candidate scanning at 50 even when
  a configured/API limit requested 51-100. PR #131 normalizes one effective
  1-100 limit and uses it for both scanning and final slicing; direct/API and
  frontend cache-partition regressions passed. Issue #100 is closed.
- Completed #135 boundary: per-input Autocomplete registration now has one
  disposer for its 18 DOM listeners, blur timer, controller, middle-pan
  forwarding, registry, and input expandos. Detached inputs, missing state
  expandos, stale markers, and owner replacement no longer leave duplicate
  listeners/controllers. The prior 0.5.0 popup failure remains a #127 package
  omission, not a retroactive lifecycle diagnosis. Issue #56 stays open for
  external DOM owner disposal, global installer/entry re-entry, #98, and its
  cumulative final matrix. The Autocomplete-only browser fixture has no output
  node, so its expected `Prompt has no outputs` signal was recorded and queue
  evidence came from the established output-capable AiO fixture on both
  surfaces.
- Completed #133 wheel boundary: main preview and non-overflow feed now consume
  wheel input in both canvas modes, while unrelated panel space preserves canvas
  forwarding. The live workflow did not produce an overflowing feed, so X-axis
  movement and boundary consumption remain deterministic focused evidence. The
  repeated core `ComfyApp graph accessed before initialization` reload message
  is the previously traced ComfyUI 0.27.0/frontend 1.45.20 baseline; EasyUse
  warning/error logs were empty. Issue #62 remains open for Detailer threshold.
- Registry live read-back on 2026-07-17 reports both 0.5.1 and 0.4.0 as
  `NodeVersionStatusFlagged`; 0.3.2 remains the latest active version and the
  deleted 0.5.0 is absent from the versions response. The verified 0.5.1 CDN
  archive remains available. The cause of the new 0.5.1 flag is not yet
  established, and the `dev`-only, unreleased PR #135 cannot have changed the
  published 0.5.1 artifact. It does not block the current bounded feature
  lanes, but its cause and live status must be reconciled before the next
  release and Goal completion. Registry 0.4.0 was previously flagged because
  the informational
  network-request scanner detects the explicit, timeout-bound NAIA
  `requests.post` path.
- The 0.5.1 metadata list intentionally omits deleted 0.5.0 so metadata sync
  cannot present it as a current target. Historical deprecated versions remain
  unchanged and cannot be reactivated by the planned sync.
- Resolved release-doc finding in the PR #134 docs checkpoint:
  `MAINTAINING.md` now follows the mode/version `comfy node publish` workflow
  and pre-publish annotated-tag gate; `registry-scanner-safety.md` spells the
  root-only `/autocomplete/` pattern and its runtime-directory hazard.
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
- For newly created Codex production tasks, the integration owner selects the
  available model and reasoning level from slice complexity, risk, latency, and
  review needs. Do not default every lane to `sol`/`max`, and do not claim a
  speed setting that the task API does not expose.
- The user explicitly authorized protected `main` merge, GitHub Release, and
  Registry publish for safe checkpoints. The approved 0.5.1 replacement and
  broken 0.5.0 GitHub withdrawal are complete. Any later release still requires
  a fresh state read-back and validated checkpoint.
- Agent-driven early user-instance changes remain unapproved. User-performed
  manual state is diagnostic input and does not expand agent sync authority.
- GitHub mutation timeout/abort always requires state read-back before retry.

## Cleanup And Sync

- The #103 Regional, #54 sampler-hydration, #120 coordination, #121 user-doc,
  #122 LoRA canvas, and #123 Autocomplete source/integration branches and
  worktrees were removed after merge-tree equality and clean-state checks.
- The #124 and #126 release/checkpoint branches, worktrees, and remote branches were removed after
  squash-merge tree equality and local/remote read-back.
- The #127 hotfix branch/worktree and remote branch were removed after squash
  merge, tree equality, package/browser validation, and Issue ledger read-back.
- The #128 release-prep branch/worktree and remote branch were removed after
  the dev/main merges, public archive read-backs, and tree-equality checks.
- The #130 checkpoint, #131 Autocomplete limit, #132 LoRA node runtime, #133
  AiO preview-wheel, #134 checkpoint, and #135 Autocomplete input-binding
  branches/worktrees and remote branches were removed after the applicable
  squash-tree/read-back, Issue ledger, and clean-state checks.
- Main `02a9a84` is an ancestor of dev `19a8968`; dev now contains the verified
  post-release maintenance and documentation checkpoints through PR #135.
- The current `record-maintenance-checkpoint-135` branch/worktree is owned only
  by the integration task and will be removed after its docs-only PR merge and
  read-back.
- Existing unrelated `codex/*`, `fix/*`, and `feature/*` worktrees are untouched.
- The Codex test server is stopped and port 8194 is free.
- The integration owner has not synced the user v0.27.0 instance. The user
  classified the manual 0.5.0 state as invalid and planned its removal after
  reporting the #56 suggestion-popup failure. The package root cause is fixed,
  but do not treat any manual 0.5.0 state as the final sync.
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
