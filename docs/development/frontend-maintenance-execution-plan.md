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

Snapshot: 2026-07-18 KST, after the integration owner merged PR #150, closed
#54 and #55 from their final ledgers, and opened the isolated 0.5.2 release-prep
worktree. The agreed #54/#55/#56 boundaries and directly related #62/#66/#98
bugs are integrated and closed. The formal Goal remains active only for the
approved protected-main release, Registry publish/read-back, and final cleanup.

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
| `origin/dev` | `50a8209ce47f7c5ba2902b1c6b63b20673a46ed0` |
| local `dev` | same SHA, clean |
| `origin/main` | `02a9a84634c03cc3afaa20000f136c03164308ce` (`v0.5.1`) |
| local `main` | same SHA, clean |
| main/dev alignment | main remains the 0.5.1 release tree; dev contains the validated post-release maintenance integrations through PR #150 |
| latest dev integration | PR #150, Legacy Autocomplete delayed-DOM binding, squash merge `50a8209ce47f7c5ba2902b1c6b63b20673a46ed0` |
| GitHub Release | `v0.5.1` public/Latest with verified manual-install ZIP; broken `v0.5.0` Release/tag absent |
| Registry | live 2026-07-18: 0.5.1 and 0.4.0 are `NodeVersionStatusFlagged` for the known informational NAIA `requests.post` scanner; 0.3.2 remains latest active; 0.5.2 is unused |
| final production validation | Python 412/412; frontend 110 JS; TypeScript 6.0.3; diff check; shared AiO queue 512x512 to 1024x1024 success |
| Codex test server | running only for the final compatibility checkpoint; stop and restore the normal merged-dev install during final cleanup |
| test-instance canvas setting | `Comfy.VueNodes.Enabled=false` is the required final restored state |
| user v0.27.0 instance | compatible full bundle reflected; Legacy AiO, LoRA Preset, and Autocomplete loaded with LoRA Manager and no new EasyUse Anima error; no user workflow saved |
| integration-owner task | formal Goal task `019f6f25-d26c-77a1-95dc-092cdb8e756c` |

## Issue Dashboard

| Issue | State | Completed boundary | Remaining or next action |
| --- | --- | --- | --- |
| #54 AiO Generator | closed | direct concurrent queue reservation, preview/wheel, hydration, lifecycle, full/shared queue, difference-surface and final user compatibility ledgers complete through #140/#150 checkpoint | none; optional in-flight node-removal semantics remain out of scope |
| #55 LoRA Preset | closed | lifecycle, profile/save-sync, canonical serialization, entry/listener and Node 2.0 wheel/redraw boundaries complete through #149 | none; optional exact-pixel/extreme-scroll coverage remains non-blocking |
| #56 Autocomplete | closed | package closure, request/input/entry lifecycle, syntax preservation, result limit, Legacy delayed-DOM compatibility and final user read-back complete through #150 | none |
| #98 Autocomplete replacement syntax | closed | nested parentheses, weights, and artist prefix preservation merged in #142 | none |
| #99 Autocomplete request epochs | closed | PR #123; focused/full/Legacy/Node 2.0 evidence and final ledger recorded | none |
| #100 Autocomplete result limit | closed | PR #131; backend/API/frontend normalized 1-100 contract and completion ledger | none |
| #62 AiO Detailer/preview behavior | closed | preview-wheel boundary #133 and Detailer threshold #143 complete | none |
| #66 AiO resource/Detailer choices | closed | live choice hydration and Detailer catalog/wildcard contract fixes #145-#148 complete | none |
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
| #119 | `4119012881f4d1b35f61a29704fb18d23602a06d` | AiO sampler hydration single owner and attached-subgraph refresh | 396/396; 103 JS; TS 6.0.3 | Legacy and Node 2.0 512×512 queue/save-reload; attached native subgraph; EasyUse errors 0 | #54 progress ledger at merge; later closed |
| #120 | `37c14f8cc10bd43fd33d3a1be76eeeeba435b920` | frontend maintenance execution ledger and repo-local coordination Skill | 396/396; 103 JS; TS 6.0.3 | not required: internal docs/procedure only | no owning feature Issue; merge/read-back and cleanup recorded here |
| #121 | `e7a2cc4c95d40930a5076c25fd5f06a9bcc78c14` | bilingual wildcard seed range and legacy workflow user documentation | 396/396; 103 JS; TS 6.0.3 | reused #112 identical production evidence; docs-only diff | #102 final ledger; Issue closed completed |
| #122 | `3f8a6c0acd25fb0819818b39d3b6f29d70d39f51` | LoRA Preset canvas drawing/hit-testing/strength-drag/widget extraction | 398/398; 104 JS; TS 6.0.3 | not repeated: mechanically identical extraction; final #55 matrix remains | #55 progress ledger at merge; later closed |
| #123 | `f5c8694cd161c0c304c66666836e6eb8fa816928` | Autocomplete adapter/result/source request epochs | 398/398; 104 JS; TS 6.0.3 | Legacy and Node 2.0 source switch, keyboard, commit, save/reload; errors 0 | #99 final ledger; Issue closed completed; #56 progress ledger |
| #124 | `1c614ad3f6d617b47f137d7d65d7414d0cd0721b` | 0.5.0 package, Registry, changelog, workflow, release, and execution metadata | release-focused tests, quick runner, `comfy node validate`, and two audits passed; reused frozen production full 398/398 | reused #123 valid Legacy and Node 2.0 evidence; metadata-only diff | release-prep merge/read-back; no feature Issue closure |
| #126 | `1bd6ee1b727fddfb37616644a30fd95605fc9d5e` | 0.5.0 release checkpoint ledger | docs-focused checks; no production diff | not required | release state recorded before the package defect was confirmed |
| #127 | `b90286848cfb178204a33fca6493548b652fd0c4` | preserve the complete Autocomplete import closure in Registry packages | 400/400; 104 JS; TS 6.0.3; `comfy node validate`; actual package closure 8/8 | Legacy and Node 2.0 input, suggestions, keyboard select, close, save/reload; relevant errors 0 | #56 package-regression ledger; later closed |
| #128 | `c74708d29b53c62b483282b2d10fbada12ee6642` | 0.5.1 package, Registry, changelog, workflow, release, and execution metadata | focused 19/19; quick runner; `comfy node validate`; actual package 138 files; two audits GO | reused exact #127 Legacy and Node 2.0 evidence; metadata/docs/workflow-only diff | release-prep merge/read-back; no feature Issue closure |
| #130 | `715384d93698009111dea158395d2541d905674e` | record the verified 0.5.1 replacement and corrected release/Registry guidance | docs/Skill-focused validation; no production diff | not required | checkpoint, merge/read-back, and cleanup recorded |
| #131 | `b5743b0da6b4f51ddbd146257cbf2803cceeddc0` | Autocomplete configured result limit 1-100 | 402/402; 104 JS; TS 6.0.3 | not required: backend/API/frontend contract regression | #100 final ledger; Issue closed completed; #56 progress ledger |
| #132 | `72d55c74e1ba02aeb6eb522ab398fc75220ae053` | LoRA Preset per-node initialize/configure/serialize lifecycle extraction | 404/404; 105 JS; TS 6.0.3 | not repeated: mechanical extraction with behavior and ownership audits | #55 progress ledger at merge; later closed |
| #133 | `2dc93fe0bf17623b51203bcf40db0854776ee8bf` | AiO preview/non-overflow-feed wheel ownership | 404/404; 105 JS; TS 6.0.3 | Legacy and Node 2.0 512x512 queue, preview/feed wheel, canvas forwarding, save/reload; EasyUse errors 0 | #54/#62 progress ledgers; both later closed |
| #134 | `e4deeec6b722d2fde9b849a2358dabb4eb584e9b` | record PR #130-#133 checkpoint and lane model-selection policy | Skill validation and independent audit; no runtime diff | not required: docs/Skill-only diff | merge/read-back and cleanup recorded here |
| #135 | `19a8968a15885801b43f831ef9c582380bf514f9` | Autocomplete per-input listener, controller, timer, middle-pan, registry, and disposer lifecycle | 405/405; 106 JS; TS 6.0.3; focused 50/50; diff checks | Legacy and Node 2.0 suggestion/keyboard/Escape/blur/single-popup/save-reload; separate output-capable fixture 512x512 queue success; no new relevant browser error | #56 lifecycle progress ledger; later closed |
| #136 | `3ddcd5a8bc06730c241e1994235dd142649a21cd` | record PR #134/#135 checkpoint, live Registry Flagged gate, and next-lane order | diff checks and independent consistency audit; no runtime diff | not required: docs-only diff | merge/read-back and cleanup recorded here |
| #137 | `4d65170e5c3986e037d7e28be3efb8f53b1d6745` | record the initial #56/#54/#55 lane ownership and model-selection checkpoint | docs-focused validation; no runtime diff | not required: docs-only diff | merged and cleaned; task ownership corrected at the next checkpoint |
| #138 | `86c1a304bf130fef7954892c1f2da5b7ad1e47a7` | Autocomplete entry, external DOM owner, and global installer lifecycle | 406/406; 107 JS; TS 6.0.3; diff checks | Legacy and Node 2.0 one-popup/20-result/keyboard/close/reload matrix; resources 200/no-store; EasyUse errors 0 | #56 progress ledger; #98/final matrix later closed |
| #139 | `ca251bce05ac45cf036b7fb144896ac532f0fb89` | task ownership checkpoint | docs-only | not required | execution ledger checkpoint |
| #140 | `e1429f8e58ce06fb4ef4c9eb66267325dc10cdbe` | AiO concurrent direct-API seed reservation | 406/406; 107 JS; TS 6.0.3 | deterministic direct API evidence; no canvas behavior change | #54 ledger |
| #141 | `b313e8548048b6e29bfa0ba72d9e359eaa4e4030` | LoRA profile mutation, save-sync, canonical serialization | 408/408; 109 JS; TS 6.0.3 | Legacy and Node 2.0 profile/save-reload; one queue per shared contract | #55 ledger |
| #142 | `4603f682aa4574adcbf0930a0582721053f5b23e` | Autocomplete nested syntax and artist-prefix preservation | focused and full complete | relevant input/replacement surfaces | #98 final ledger; Issue closed |
| #143 | `6dd497af45146298b0a98a93dfd450f0384fcd42` | AiO external Detailer threshold control | focused and full complete | changed external-panel surface | #62 final ledger; Issue closed |
| #144 | `6c0fe8e5ab6d7b298c6b5344f381c66d2c1b2cdd` | LoRA entry/listener/wheel owner lifecycle | 411/411; 110 JS; TS 6.0.3 | deterministic ownership; final difference surface deferred to #149 | #55 ledger |
| #145 | `40fc5aecf491d49cad28baf73d2f93298b6ca198` | AiO resource-choice hydration after live catalog load | focused and full complete | relevant live choice surface | #66 ledger |
| #146 | `ea060ca4c1624eeaa70acecaeef177ec01d6e71f` | AiO Detailer settings contract | focused and full complete | relevant external settings surface | #66 ledger |
| #147 | `7da54ac1dd52501b8d4401056f494d387987b218` | AiO live catalog, wildcard, and multiline textarea contract | focused and full complete | Legacy external textarea and Node 2.0 contract evidence as applicable | #66 ledger |
| #148 | `b0aad7ed94aca53070a02158db6a1653059bff3b` | AiO extracted choice helper call-site repair | 412/412; 110 JS; TS 6.0.3 | live runtime crash path removed | #66 final ledger; Issue closed |
| #149 | `716f3b25686877b60bb56d4c1bf57716d9a19364` | Node 2.0 LoRA profile wheel ownership and redraw | 412/412; 110 JS; TS 6.0.3 | Node 2.0 list wheel/redraw; Legacy evidence reused | #55 ledger |
| #150 | `50a8209ce47f7c5ba2902b1c6b63b20673a46ed0` | Legacy Autocomplete delayed DOM mount compatibility | 412/412; 110 JS; TS 6.0.3 | Legacy with LoRA Manager; Node 2.0 evidence reused | #56 post-close ledger |

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
| GitHub Release | `https://github.com/n0va39/ComfyUI-EasyUseAnima/releases/tag/v0.5.1`; public and Latest; user-facing body simplified and read back on 2026-07-18 |
| manual ZIP | 27,163,430 bytes; exact 345-file tagged tree under `ComfyUI-EasyUseAnima/`; SHA256 `AC9813B49E87C83CC22F66C5BC9A444720615663270A2811DC6AA7C505362552` |
| production tree | frozen at PR #127; release preparation changes metadata, docs, and maintained workflow versions only |
| frozen full | Python unittest 400/400; 104 frontend JavaScript files; TypeScript 6.0.3; diff checks |
| Registry publish | run `29558688905`, exact main `02a9a84`, success; validation and upload passed |
| Registry metadata | run `29558759993`, exact main `02a9a84`, success; final dry-run no-op |
| Registry archive | 12,883,225 bytes; 138 files; every file byte-equal to exact-main Git blobs; package version 0.5.1; Autocomplete closure 8/8; SHA256 `30A5AB952D478DB3E9A05F12F928FB3663C8119264389A4AF5BC0BB16CA241D9` |
| Registry status | at the 0.5.1 publish checkpoint: 0.5.1 `NodeVersionStatusPending`, 0.4.0 `NodeVersionStatusFlagged`; the current live 0.5.1 state has since changed to `NodeVersionStatusFlagged` and is tracked below |
| browser | Legacy and Node 2.0 input, 20-result popup, keyboard select, Escape close, and save/reload passed; relevant module/404 errors 0 |
| dev alignment | `1efcb401a999c42246d41bf21371b12912297b6e`, tree-identical merge of `origin/main` into `dev` |

This replacement checkpoint did not close the maintenance Goal at that time.
The later PRs through #150 completed #54, #55, #56, and the agreed related bugs
before the single final user-instance sync.

## Production Lane Ownership

| Slice | Codex task | Branch / worktree | Base and status | Expected files |
| --- | --- | --- | --- | --- |
| 0.5.2 release preparation | integration owner `019f6f25-d26c-77a1-95dc-092cdb8e756c` | `codex/prepare-0.5.2-release` / `worktrees/ComfyUI-EasyUseAnima/codex/prepare-0.5.2-release` | base `50a8209`; metadata/docs/workflow/test-only candidate in progress | version, current Registry changelog, release/development notes, workflow package metadata, ledger, copy regression |
| completed production lanes | former sidebar tasks with explicit assigned model/reasoning | former #54/#55/#56 and related bug worktrees | PRs #138-#150 merged; owned worktrees/branches cleaned when confirmed | historical evidence remains in merged slices and Issue ledgers |

## Integration Gates

Only one row may enter push/PR/merge at a time.

| Order | Slice | Focused / audit | Full | Browser | Blocker / finding | Gate |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | #56 Registry package hotfix | PR #127 merged; actual archive/import-closure validation and audits complete | 400/400; 104 JS; TS 6.0.3 | Legacy and Node 2.0 complete | no production finding remains | complete |
| 2 | 0.5.1 release preparation | PR #128 focused validation, actual package, and two audits complete | reused exact PR #127 frozen full | reused exact PR #127 dual-canvas evidence | production-tree neutral | complete |
| 3 | 0.5.1 publish and replacement | PR #129, tag, GitHub asset, Registry runs, both public archive read-backs, and 0.5.0 removal complete | no repeat; production tree unchanged | no repeat; production tree unchanged | publish checkpoint was Pending; current Flagged status is the known informational NAIA network-request scanner finding | complete |
| 4 | post-release ledger/docs | PR #130 merged and cleaned | no runtime/full repeat | no browser repeat | no production code change | complete |
| 5 | #100 Autocomplete result limit | PR #131 merged; correctness and regression audits GO | 402/402; 104 JS; TS 6.0.3 | deterministic backend/API/frontend boundary; no browser repeat | no finding remains; Issue #100 closed | complete |
| 6 | #55 LoRA node lifecycle extraction | PR #132 merged; behavior and ownership audits GO | 404/404; 105 JS; TS 6.0.3 | mechanical extraction; no browser repeat | profile/save-sync/entry/final matrix remained at this checkpoint and later completed | complete |
| 7 | #54/#62 AiO preview wheel | PR #133 merged; three audits GO | 404/404; 105 JS; TS 6.0.3 | Legacy and Node 2.0 512x512 queue/wheel/save-reload complete | live feed did not overflow; deterministic X-scroll/boundary regression passed; the later Detailer threshold slice completed #62 | complete |
| 8 | #130-#133 checkpoint ledger/Skill | PR #134 merged, read back, and cleaned | no runtime/full repeat | no browser repeat | no production code change | complete |
| 9 | #56 per-input binding lifecycle | PR #135 merged; correctness/test/scope audits and Issue read-back complete | 405/405; 106 JS; TS 6.0.3 | Legacy and Node 2.0 popup lifecycle/save-reload and queue complete | package failure remains attributed to #127; installer/global lifecycle later completed | complete |
| 10 | #135 checkpoint ledger | PR #136 merged, read back, and cleaned | no runtime/full repeat | no browser repeat | the then-unresolved Registry flag was recorded without inference; later read-back identified the known NAIA scanner finding | complete |
| 11 | initial active-lane ownership checkpoint | PR #137 merged, read back, and cleaned | no runtime/full repeat | no browser repeat | initial task ownership text superseded by the actual sidebar-task read-back below | complete |
| 12 | #56 installer/entry lifecycle | PR #138 merged; full, dual-canvas, resource/module, Issue read-back, and cleanup complete | 406/406; 107 JS; TS 6.0.3 | Legacy and Node 2.0 re-entry/reload matrix complete | apparent reload failure was ambiguous target selection, not a module/lifecycle failure; #98/final user matrix later completed | complete |
| 13 | #54 concurrent API contract | PR #140 merged; deterministic FIFO/no-commit/tail-reuse evidence | 406/406; 107 JS; TS 6.0.3 | no canvas behavior change | complete | complete |
| 14 | #55 profile/save-sync and entry/wheel | PRs #141/#144/#149 merged; focused ownership evidence complete | final production checkpoint 412/412; 110 JS; TS 6.0.3 | Legacy save/reload plus Node 2.0 wheel/redraw difference surface | Issue closed | complete |
| 15 | #62/#66/#98 and final #54/#56 compatibility | PRs #142/#143/#145-#148/#150 merged | final production checkpoint 412/412; 110 JS; TS 6.0.3 | changed surfaces only; final user v0.27.0 bundle with LoRA Manager | Issues closed | complete |
| 16 | 0.5.2 release preparation | current-version copy 17/17, Skill validation, workflow metadata, Registry dry-run, `comfy node validate`, official quick, and actual committed package check passed (144 entries; version 0.5.2; Autocomplete 7/7) | reuse exact final production full 412/412; quick runner passed 110 JS and TS 6.0.3 | no production browser repeat | protected main/tag/Release/Registry still pending | ready |
| 17 | public release and cleanup | pending exact main PR, annotated tag, GitHub asset, Registry publish/metadata/read-back | no repeat unless production tree changes | reuse final surface evidence | external Registry review may remain Pending/Flagged | queued |

Known validation note: Windows sandbox may fail before command/test setup with
`CreateProcessAsUserW 1312`. Record cwd, TEMP variables, runner, and failure
phase; rerun only the identical focused or approved full command outside the
sandbox. Do not report the environment spawn error as a code failure.

## Current Blockers And Findings

- There is no remaining code blocker for the 0.5.2 maintenance release. Issues
  #54, #55, #56, #62, #66, and #98 are closed with final ledger read-back.
  Issue #111 remains open as a documented non-blocking upstream Node 2.0 display
  mismatch.
- Resolved #56 release blocker: the user-visible 0.5.0 failure came from an
  incomplete Registry archive, not the earlier #98/#99/#100 behavior bugs.
  `.comfyignore` excluded `web/js/autocomplete/`, while tooltip metadata still
  loaded through a separate path. PR #127 anchors the root data directory only,
  recursively validates the entry import closure, and passed actual packaged
  Legacy/Node 2.0 checks. The package finding is recorded in Issue #56 comment
  `4999279403`; the cumulative final read-back is comment `5010252202`, and
  Issue #56 is closed after PR #150.

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
  omission, not a retroactive lifecycle diagnosis. At that checkpoint, Issue
  #56 still required external DOM owner disposal, global installer/entry
  re-entry, #98, and its cumulative final matrix. The Autocomplete-only browser
  fixture has no output
  node, so its expected `Prompt has no outputs` signal was recorded and queue
  evidence came from the established output-capable AiO fixture on both
  surfaces.
- Completed #138 boundary: process-wide listeners, external input and tooltip
  hooks, popup UI, retry timer, and prototype wrappers now have a
  generation-aware entry owner. Legacy and Node 2.0 reloads restored multiple
  prompt textareas; explicitly selecting the textarea containing the query
  produced one 20-result popup and passed keyboard, close, and re-entry checks.
  The earlier apparent post-reload failure was the diagnostic guard refusing an
  ambiguous target, not a missing served module or failed lifecycle. The later
  #98 integration and final cumulative/user-instance matrix completed that
  boundary and closed Issue #56.
- Completed #133 wheel boundary: main preview and non-overflow feed now consume
  wheel input in both canvas modes, while unrelated panel space preserves canvas
  forwarding. The live workflow did not produce an overflowing feed, so X-axis
  movement and boundary consumption remain deterministic focused evidence. The
  repeated core `ComfyApp graph accessed before initialization` reload message
  is the previously traced ComfyUI 0.27.0/frontend 1.45.20 baseline; EasyUse
  warning/error logs were empty. The later Detailer threshold boundary closed
  Issue #62.
- Registry live read-back on 2026-07-18 reports both 0.5.1 and 0.4.0 as
  `NodeVersionStatusFlagged`; 0.3.2 remains the latest active version and the
  deleted 0.5.0 is absent from the versions response. The verified 0.5.1 CDN
  archive remains available. Both flags report the informational
  `any-network-requests` scanner finding for the explicit, timeout-bound NAIA
  `requests.post` path; 0.5.1 also remains in external extraction review with
  `comfy_node_extract_status=pending`. These known external review states do not
  block publishing a validated 0.5.2, but the final report must preserve their
  exact live status rather than claim approval.
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
  broken 0.5.0 GitHub withdrawal are complete. Fresh Git, tag, GitHub Release,
  asset, and Registry read-back found no 0.5.2 collision, so 0.5.2 is the
  approved next patch after the validated checkpoint.
- The final compatible bundle was applied once to the user v0.27.0 instance
  after all production lanes merged. The user-instance check is complete; do
  not perform another sync for release-metadata-only changes.
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
  AiO preview-wheel, #134/#136/#137 checkpoints, and #135 Autocomplete input-binding
  branches/worktrees and remote branches were removed after the applicable
  squash-tree/read-back, Issue ledger, and clean-state checks.
- The PR #138 Autocomplete entry branch/worktree and remote branch were removed
  after tree equality, full/browser/resource checks, and #56 ledger read-back.
- The #54, #55, #56, #62, #66, and #98 completion lanes through PR #150 were
  removed after merge-tree equality, focused/full evidence, applicable browser
  checks, Issue ledger read-back, and clean-state checks.
- Main `02a9a84` is an ancestor of dev `50a8209`; dev now contains the verified
  maintenance checkpoint through PR #150.
- The current `prepare-0.5.2-release` branch/worktree is owned only by the
  integration task and will be removed after its release-prep PR merge and
  read-back.
- Existing unrelated `codex/*`, `fix/*`, and `feature/*` worktrees are untouched.
- The Codex test server and temporary final-validation install remain pending
  final cleanup. Re-read process ownership, restore the normal test-instance
  package path from merged dev, remove only the authorized temporary install and
  fixtures, stop the Codex-owned server, and confirm port 8194 is free.
- The user v0.27.0 instance received the final compatible production bundle
  once. AiO Generator, LoRA Preset, and Autocomplete rendered together without
  new EasyUse Anima errors, and no user workflow was saved. Release metadata
  changes do not require another user-instance sync; only close the unsaved
  browser fixtures without saving during final cleanup.

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
