# Release-First Stabilization Lane Before Further Backend Refactor

## Document status

- Status: active execution-order override
- Snapshot date: 2026-07-24
- Snapshot branch: `dev`
- Snapshot commit: `bf61d1eb5fb015a9ca21d011aa9809e4e20a8e00`
- Primary execution issue: [#395](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/395)
- Release-blocking bugs: [#266](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/266), [#267](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/267)
- Required user features: [#335](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/335), [#394](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/394), [#64](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/64)
- Scope: cross-surface release sequencing; it does not redefine Python package ownership

While #395 is open, this document overrides the **next-work ordering** in
[`python-backend-execution-roadmap.md`](python-backend-execution-roadmap.md).
It does not roll back completed refactors, replace ADRs, or weaken their gates.
It pauses new D/E/G/H and AiO Hook implementation so the repository can deliver
user-visible fixes and features from a stable integration point.

The active critical path is:

```text
#266 LoRA workflow profile provenance bug
  -> #267 LoRA scrollbar pointer bug
  -> #335 locale-aware initial autocomplete source
       + #394 Prompt Studio resolution orientation switch in parallel
  -> #64 configurable artist autocomplete prefix
  -> integrated release-candidate validation
  -> release preparation
  -> main/tag/Registry publication
  -> re-audit and resume backend refactor
```

## 1. Verified starting state

At the snapshot:

- B-11 final root shim work is complete.
- The #167 seed series and #169 stage/cache series have completed their current
  implementation path.
- D-01, D-08, D-09, D-10, D-11a/b, and D-12a through D-12f2 have reached their
  reviewed integration points; D-12f2 was merged in PR #393.
- No open pull request owns #266, #267, #335, #394, or #64.
- The package version remains `0.5.4`.
- The open issues carrying the `bug` label are #266 and #267.

The next structural D-12 lifecycle/expansion slice is deliberately no longer
READY. Completed canonical owners remain authoritative and must be used by the
release work; the release work must not reopen root implementation ownership.

## 2. Priority and freeze rules

### 2.1 Work that is READY or may become READY

Only these categories may start while this lane is active:

1. one of the release tasks listed in section 3;
2. a new P0/P1 regression discovered while validating those tasks;
3. documentation or test infrastructure strictly required to prove a release
   task; or
4. release preparation after the integrated release gate passes.

### 2.2 Work that is paused

Do not start a new implementation PR for:

- additional D-series root consolidation;
- E-series lifecycle or service migration;
- G/H quality or shim-retirement work unless required to prevent a release
  regression;
- AiO Hook public API or extension work;
- opportunistic package cleanup, file splitting, alias retirement, or formatting;
- behavior changes outside #266, #267, #335, #394, and #64.

An already completed refactor is not reverted. An urgent bug fix may use its
canonical owner, but it may not bundle the next refactor milestone.

### 2.3 Pull-request isolation

- One issue per PR.
- Do not combine #266 and #267 even though both affect LoRA Preset.
- Do not combine #335 and #64 even though both affect settings/autocomplete.
- Use `codex/rel-<task-id>-<description>` from the latest `origin/dev`.
- Search open PRs and branches before editing.
- Record exact base and head SHAs in every PR.
- A release task is a Fix, Feature/Contract, or Release-only PR. It is not a Move
  PR unless the owning issue explicitly proves that a missing owner blocks the
  user behavior.

## 3. Active executable queue

| Order | Task ID | Owner | State | Type | Prerequisites |
| ---: | --- | --- | --- | --- | --- |
| 1 | REL-BUG-01 | #266 | READY | Fix | current `dev`; no overlapping PR |
| 2 | REL-BUG-02 | #267 | BLOCKED | Fix | REL-BUG-01 merged; rebase LoRA frontend |
| 3A | REL-FEAT-01 | #335 | BLOCKED | Feature/Contract | both bug fixes merged |
| 3B | REL-FEAT-02 | #394 | BLOCKED | Feature | both bug fixes merged; may run parallel with 3A if files remain disjoint |
| 4 | REL-FEAT-03 | #64 | BLOCKED | Feature/Contract | REL-FEAT-01 merged |
| 5 | REL-RC-01 | #395 | BLOCKED | Integration gate | all five issue PRs merged |
| 6 | REL-PREP-01 | #395 | BLOCKED | Release-only | REL-RC-01 passed |
| 7 | REL-PUBLISH-01 | #395 | BLOCKED | Release | release prep reviewed and merged |

The first task Codex must select is **REL-BUG-01 / #266**.

## 4. Common implementation protocol

Before editing:

```powershell
git fetch origin
git checkout -b codex/rel-<task-id>-<description> origin/dev
git rev-parse HEAD
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile quick
```

Then:

1. read this file and #395;
2. read the owning issue and recent comments;
3. inspect current canonical owners and open PRs;
4. reproduce the current behavior before changing it;
5. write an allowed-file and forbidden-change inventory in the PR body; and
6. implement the smallest complete correction or feature.

Every implementation PR must run:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
```

UI or workflow-visible changes additionally require the owning task's Legacy
Canvas and Node 2.0 matrix. Package/public-surface changes additionally require:

```powershell
comfy node validate
comfy node pack
```

A missing live environment is recorded as an unexecuted release gate. It is not
reported as passed and must be completed in REL-RC-01.

## 5. REL-BUG-01 — Local profile provenance for shared workflows

### Goal

A portable workflow must not make serialized author-local `saved_name` or
`saved_snapshot` metadata appear to be verified current-user storage state.

### Required behavior

- Rehydrated workflow metadata begins unverified.
- `saved` is shown only after the current profile store proves the relevant
  profile exists and its identity/content contract matches.
- Same-name but different local profiles are not treated as the same profile.
- Workflow metadata never becomes an overwrite/CAS token by itself.
- Reopening a workflow in the same local environment can restore `saved` after
  current-store verification.

### Allowed production surface

Use the current LoRA Preset frontend profile-data, mutation, runtime, and API
adapter owners discovered during preflight. Backend profile contracts may change
only when required to expose an existing identity/content check; do not redesign
profile persistence.

### Forbidden changes

- scrollbar geometry or event routing from #267;
- profile naming rules or unrelated CRUD UI;
- workflow node IDs, row contents, mapping, or public API shape;
- implicit trust in serialized `saved_name`, snapshot text, or stale token;
- unrelated profile repository refactor.

### Required tests

```text
external workflow + empty local store -> not saved
external workflow + same name/different identity or content -> not saved
external workflow + verified matching local profile -> saved
workflow metadata -> no overwrite/CAS token adoption
same-local workflow reopen -> saved only after verification
serialized workflow remains portable and contains no newly privileged token
```

### Live gate

Create a workflow in one user-data environment, transfer it to another with an
empty or conflicting profile store, and verify the displayed state and save flow.

### Rollback boundary

Revert only the profile-provenance verification and its tests. Do not revert
canonical profile ownership or other LoRA UI fixes.

## 6. REL-BUG-02 — LoRA profile scrollbar pointer interaction

### Goal

With at least seven profiles, the visible scrollbar track and thumb must respond
to actual host pointer routing in both canvas modes.

### Required pre-fix evidence

Measure or otherwise prove:

- the widget width passed to draw;
- `node.size[0]`;
- widget-local pointer coordinates;
- track and thumb rectangles; and
- whether pointerdown reaches the custom widget.

Do not commit permanent diagnostic logging. The measurement belongs in the PR
record or a deterministic host-routing test.

### Required behavior

- track click changes the offset predictably;
- thumb drag updates offset continuously;
- pointerup and pointercancel end drag state;
- wheel scrolling and row selection continue to work;
- resize recalculates geometry without leaving stale hit areas.

### Forbidden changes

- #266 profile-provenance logic;
- global permanent listeners that leak after node removal;
- speculative event-name replacement without host evidence;
- list order, profile CRUD, or wheel ownership changes.

### Required tests

```text
non-zero widget origin and host-supplied width
track click
thumb pointerdown/move/up
pointercancel cleanup
resize then hit-test
wheel and row-click regression
Legacy Canvas live interaction
Node 2.0 live interaction
```

## 7. REL-FEAT-01 — Locale-aware initial autocomplete source

### Goal

Select a locale-derived autocomplete source only when neither settings store has
an explicit source key.

### Precedence

```text
explicit Comfy setting
  > explicit EasyUse Anima setting
  > locale-derived initial value
```

Locale-derived initial values:

```text
Korean locale -> localsmile_kr_wiki
other/unknown -> dbr_danbooru_2025_09_01
```

### Current ownership

Use the canonical `easyuse_anima.settings` and `easyuse_anima.autocomplete`
owners plus frontend settings/i18n. Do not reintroduce implementation into root
`settings.py` or `autocomplete_dataset.py` shims.

### Required behavior

- Key presence, not equality with the old default, identifies an explicit user
  choice.
- Existing Danbooru, e621, merged, or Korean selections remain unchanged.
- Locale is consulted once for missing-value initialization, not on every read.
- Later locale changes do not silently switch an initialized source.
- A missing Korean CSV safely falls back to bundled Danbooru without damaging
  stored settings.
- Backend/public settings and frontend setting display agree.

### Forbidden changes

- source ranking, autocomplete query API, or index policy;
- migration of existing explicit values;
- a frontend-only default that disagrees with backend persistence;
- unrelated D/E settings or autocomplete refactor.

### Required tests

```text
missing/missing + ko and ko-KR -> Korean source
missing/missing + en/ja/zh/unknown -> Danbooru
explicit internal source + Korean locale -> preserve
explicit Comfy source + Korean locale -> preserve
explicit Danbooru + Korean locale -> preserve
initialized value + later locale change -> preserve
missing Korean CSV -> safe Danbooru
frontend/backend parity and source-cache invalidation
```

## 8. REL-FEAT-02 — Prompt Studio resolution orientation switch

### Goal

Add a keyboard-accessible orientation switch to the Advanced and AdvancedV2
resolution UI without changing backend resolution semantics.

### Required behavior

Preset bucket:

- choose the exact inverse `height × width` option in the same bucket;
- square values are a no-op;
- if the exact inverse does not exist, preserve the current value and disable or
  explain the action;
- never choose an approximate aspect ratio.

Custom resolution:

- swap custom width and height;
- update both number inputs, hidden widgets, `resolution_size`, summary,
  callbacks, queue value, and serialization consistently;
- preserve existing 32-pixel normalization and minimum rules.

NAIA resolution:

- do not silently change to Custom or break NAIA ownership;
- initial implementation keeps the action disabled with localized explanation
  unless current contracts prove a safe direct swap.

### Forbidden changes

- new resolution buckets or approximate selection;
- Regional canvas/mask rotation;
- image rotation or backend latent/sampling changes;
- linked input overwrite;
- node height or textarea-layout mutation.

### Required tests

```text
portrait preset -> exact landscape
landscape preset -> exact portrait
square -> no-op
missing inverse -> preserve
custom swap -> all widgets/summary synchronized
popup close/reopen and workflow reload
linked input protection
NAIA no silent Custom conversion
Advanced/AdvancedV2 parity
Legacy Canvas and Node 2.0
```

## 9. REL-FEAT-03 — Configurable artist autocomplete prefix

### Goal

Persist a user-selected prefix for artist-only autocomplete trigger and result
insertion while preserving `@` as the default.

### Required behavior

- The setting persists through restart and browser reload.
- The configured prefix starts artist-only search.
- Selecting an artist result inserts exactly one configured prefix.
- General, character, copyright, and other categories are unchanged.
- Forced artist-only fields preserve their existing scope behavior.
- The default configuration remains `@artist name`.
- An empty or invalid value does not invent a new mode; until explicitly
  specified otherwise, normalize it back to `@`.

### Dependency on #335

Reuse #335's canonical settings ownership and explicit/missing-value rules.
Do not change locale-based source initialization while adding the artist-prefix
setting.

### Forbidden changes

- autocomplete ranking, source API, or dataset format;
- prefixes for non-artist categories;
- migration or rewriting of existing prompt text;
- combining #335 implementation into this PR;
- broad autocomplete module refactor.

### Required tests

```text
default @ search and insertion
custom prefix artist-only search
custom prefix insertion
no duplicate prefix
non-artist categories unchanged
forced artist-only input parity
settings save/read/reload
IME composition and popup commit
Legacy Canvas and Node 2.0
```

## 10. REL-RC-01 — Integrated release-candidate gate

All five implementation PRs must be merged to the latest `dev` head before this
gate runs. Issue closure alone is not sufficient.

### Automated gates

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
comfy node validate
comfy node pack
```

Inspect the actual archive and verify required Python, JavaScript, locale, CSV,
workflow, and changelog inputs are present. Source-tree import success is not an
archive-closure substitute.

### Installation matrices

1. clean user-data installation;
2. update from 0.5.4 settings, profiles, and maintained workflows;
3. Legacy Canvas;
4. Node 2.0;
5. Korean and non-Korean Comfy locale;
6. sender/receiver user-data split for LoRA workflow provenance.

### Required user flows

- #266 cross-user workflow profile state;
- #267 track click and thumb drag;
- #335 fresh Korean/non-Korean source and explicit-value preservation;
- #394 preset/custom/NAIA orientation action;
- #64 default/custom artist prefix, IME, insertion, and reload;
- no browser console error from EasyUse Anima;
- no package import or optional-feature regression.

If this gate finds a regression, create a separate `bug`/`type: fix` issue and
insert it before REL-PREP-01. Do not patch production code inside the release-prep
PR.

## 11. REL-PREP-01 — Release preparation

The release-prep PR is metadata/documentation only. It must not change production
Python or JavaScript.

Required work:

- select a semantic version;
- update `pyproject.toml` and aligned release metadata;
- add a user-facing changelog section;
- update maintained workflow package metadata where required;
- align README summaries and release instructions;
- run the full release validation again; and
- record the exact candidate commit and tested ComfyUI/frontend versions.

Because this lane contains backward-compatible UI and behavior additions,
`MAINTAINING.md` classifies it as a minor release. From `0.5.4`, the default
candidate is **0.6.0** unless the release PR records a different compliant
choice.

The older AiO Hook plan's 0.6.0 target is not a prerequisite for this release.
If this stabilization release uses 0.6.0, assign the public Hook API to a later
minor version in its next planning update.

## 12. REL-PUBLISH-01 — Main, tag, and Registry

Follow `MAINTAINING.md` exactly:

1. merge the validated release candidate into protected `main`;
2. create the immutable annotated tag from the released `main` commit;
3. dispatch the manual Registry publish workflow with the exact version;
4. read back Registry version, changelog, and download state;
5. run metadata synchronization and prove the final dry-run is a no-op; and
6. verify a normal user update from the published package.

Do not tag `dev`, reuse an existing version, rewrite a published tag, or publish
before the release candidate has live ComfyUI evidence.

## 13. Refactor resumption gate

The ordinary backend queue becomes selectable again only after:

- #266, #267, #335, #394, and #64 are complete;
- REL-RC-01 has passed at one exact integrated `dev` head;
- release preparation and main integration are complete;
- tag and Registry publication/read-back are complete; and
- no immediate P0/P1 post-release regression remains open.

At that point, re-run the backend analyzer, inspect open issues and PRs, and
choose the next D/E/G/H task from current evidence. Do not automatically resume
the task that was next before this freeze.

## 14. Codex start instruction

```text
Read docs/architecture/release-first-stabilization-lane.md and Issue #395 before
any other roadmap queue. While #395 is open, do not start a new D/E/G/H or AiO
Hook implementation task.

Select REL-BUG-01 / Issue #266. Create one branch from the latest origin/dev,
reproduce the cross-user workflow profile-state bug, inventory current canonical
LoRA profile owners, and implement only current-store provenance verification.
Do not touch scrollbar behavior from #267 or perform unrelated refactoring.

Run focused tests, tools/check_project.ps1 -Profile full, and the sender/receiver
user-data live smoke. Record exact base/head SHA, reproduction, root cause,
compatibility evidence, rollback boundary, and the next release task. Do not
merge, version, tag, or publish from the implementation PR.
```
