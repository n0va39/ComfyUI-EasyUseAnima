# Prompt Studio and Autocomplete UX Release Addendum

## Document status

- Status: active release-lane addendum
- Snapshot date: 2026-07-24
- Snapshot branch: `dev`
- Snapshot commit: `9a4f11593b5ea042d0883aa3ca325f6695a78bc2`
- Base release lane: [`release-first-stabilization-lane.md`](release-first-stabilization-lane.md)
- Release owner: [#395](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/395)
- Expanded autocomplete work: [#64](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/64)
- New release-blocking textarea bug: [#401](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/401)

This addendum records two user-facing requirements discovered after the original
release-first lane was written. While #395 is open, this file overrides the
relevant queue, #64 manifest, release-candidate matrix, and resumption checklist
in the base lane. All other freeze, validation, release, and ownership rules
remain in force.

## 1. Verified state and revised critical path

The original first four implementation tasks are already integrated:

- #266 profile provenance: PR #397;
- #267 profile scrollbar pointer interaction: PR #398;
- #394 resolution orientation switch: PR #399; and
- #335 locale-aware initial autocomplete source: PR #400.

Do not reopen or combine those completed scopes. The next release work is:

```text
COMPLETE: #266 / PR #397
COMPLETE: #267 / PR #398
COMPLETE: #394 / PR #399
COMPLETE: #335 / PR #400

READY:    REL-BUG-03   #401 Prompt Studio long-paste textarea autosize
  ->      REL-FEAT-03A #64 completion edit Contract
  ->      REL-FEAT-03B #64 configurable artist prefix
  ->      REL-FEAT-03C #64 safe mid-text completion
  ->      REL-FEAT-03D #64 bracket and weighted-selection UX
  ->      REL-RC-01 integrated release-candidate validation
  ->      REL-PREP-01 release preparation
  ->      REL-PUBLISH-01 main/tag/Registry publication
  ->      backend refactor re-audit and resume
```

The first task Codex must select from this addendum is **REL-BUG-03 / #401**.

## 2. Revised executable queue

| Order | Task ID | Owner | State | Type | Prerequisites |
| ---: | --- | --- | --- | --- | --- |
| 1 | REL-BUG-01 | #266 | COMPLETE | Fix | PR #397 merged |
| 2 | REL-BUG-02 | #267 | COMPLETE | Fix | PR #398 merged |
| 3 | REL-FEAT-02 | #394 | COMPLETE | Feature | PR #399 merged |
| 4 | REL-FEAT-01 | #335 | COMPLETE | Feature/Contract | PR #400 merged |
| 5 | REL-BUG-03 | #401 | READY | Fix | current `dev`; no overlapping implementation PR |
| 6A | REL-FEAT-03A | #64 | BLOCKED | Contract/test | REL-BUG-03 merged and Prompt Studio frontend rebased |
| 6B | REL-FEAT-03B | #64 | BLOCKED | Feature/Contract | REL-FEAT-03A merged |
| 6C | REL-FEAT-03C | #64 | BLOCKED | Fix/Feature | REL-FEAT-03B merged |
| 6D | REL-FEAT-03D | #64 | BLOCKED | Feature | REL-FEAT-03C merged |
| 7 | REL-RC-01 | #395 | BLOCKED | Integration gate | #401 and all #64 units merged |
| 8 | REL-PREP-01 | #395 | BLOCKED | Release-only | REL-RC-01 passed |
| 9 | REL-PUBLISH-01 | #395 | BLOCKED | Release | release prep reviewed and merged |

One issue may use several rollback-sized PRs when its accepted plan explicitly
requires ordered Contract and behavior units. Do not combine #401 with #64 or
reopen #394 merely because all three touch Prompt Studio.

## 3. Common execution protocol

Before editing:

```powershell
git fetch origin
git checkout -b codex/rel-<task-id>-<description> origin/dev
git rev-parse HEAD
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile quick
```

Then:

1. read the base release lane, this addendum, #395, and the owning issue;
2. verify current `dev` and search open PRs and branches for the task ID;
3. reproduce the current behavior before editing;
4. inventory the canonical owners, allowed files, and forbidden changes in the PR
   body;
5. implement one rollback-sized unit only; and
6. record exact base/head SHA, focused/full/live evidence, rollback boundary, and
   next task.

Every implementation PR runs:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
```

UI-visible behavior additionally requires Legacy Canvas and Node 2.0 evidence.
Package or public-surface changes additionally require:

```powershell
comfy node validate
comfy node pack
```

An unavailable live scenario is recorded as unexecuted, not passed, and remains a
REL-RC-01 gate.

## 4. Verified autocomplete failure surface

The current frontend has one search range and one replacement range.

`web/js/autocomplete/text_model.js` currently:

1. scans left and right to comma or newline;
2. trims prompt-syntax prefixes and suffixes;
3. returns one `start` and `end`; and
4. lets `planAutocompleteInsertion()` replace that full range.

This couples search context to edit ownership. A caret in the middle of a
comma-delimited segment can therefore cause right-hand text in the same segment
to be removed.

The accepted correction follows the editor model represented by LSP
`InsertReplaceEdit` and Monaco suggestion insert/replace modes without adding an
editor dependency:

```text
query range   != insert range != replace range
```

- the query range may include a multi-word search prefix;
- the insert range ends at the caret and preserves right-hand text;
- the replace range may include only the proven contiguous tail of the active
  item; and
- closing brackets, numeric weights, separators, and separate suffix tags are
  protected.

Design references:

- https://microsoft.github.io/language-server-protocol/specifications/lsp/3.18/specification/#textDocument_completion
- https://microsoft.github.io/monaco-editor/typedoc/interfaces/editor_editor_api.editor.ISuggestOptions.html

## 5. REL-BUG-03 — Long-paste textarea autosize

### Goal

After a large paste or input mutation, each affected Prompt Studio textarea must
grow until all text is visible without an internal vertical scrollbar.

### Current code gap

Both textarea families perform a same-turn content-height measurement:

- Advanced/AdvancedV2: `advanced_fields_ui.js` calls
  `advancedTextareaContentHeight()` during the `input` event;
- Classic/Extend: `studio_resizable_input.js` calls
  `desiredTextareaHeight()` during the `input` event.

Neither path verifies after browser wrapping, font/highlight work, node sizing,
and the next layout frame that `scrollHeight` actually fits `clientHeight`.

This is a confirmed missing stabilization guarantee. The implementation PR must
still capture live values to identify every affected node variant and the exact
frame where the stale height occurs.

### Required pre-fix evidence

Test at least:

```text
100+ short lines
one long wrapped line
mixed Korean/English text
brackets, weights, and Artist Mix syntax
narrow node width
paste before and after manual textarea resize
Classic, Advanced, AdvancedV2, Legacy Canvas, Node 2.0
```

Record:

```text
paste/input-turn scrollHeight, clientHeight, offsetHeight
first requestAnimationFrame values
post-node-layout frame values
stored field.height or widget.__easyuseAnimaHeight
final overflowY
```

### Required implementation

```text
input or paste
  -> immediate grow
  -> bounded requestAnimationFrame remeasure
  -> optional one additional post-node-layout verification
  -> stop when content fits or the small fixed retry budget is exhausted
```

Rules:

- use an input revision/epoch so stale callbacks cannot overwrite newer text;
- post-layout corrections are grow-only;
- use a small fixed retry budget, never an unbounded RAF or polling loop;
- removed or disconnected inputs make scheduled work a safe no-op;
- preserve the current auto/manual height distinction;
- manual height remains user-owned but grows when content no longer fits;
- keep `overflowY: hidden` on the textarea;
- reuse existing Advanced and Classic height/layout owners;
- do not create a document-level paste listener or global timer registry; and
- preserve the already merged #394 resolution component and its layout behavior.

### Exit invariant

For every affected textarea after stabilization:

```text
textarea.scrollHeight <= textarea.clientHeight + 2
textarea.style.overflowY == "hidden"
```

### Required tests

```text
long multiline paste
long wrapped single line
Korean and English mixed text
prompt brackets and weights
narrow node width
paste followed by width change
manual height followed by larger paste
rapid consecutive paste; latest revision wins
node/input removed before scheduled remeasure
save/reload value and height parity
highlight overlay height parity
Legacy Canvas and Node 2.0 live smoke
```

### Forbidden changes

- fixed oversized textarea defaults;
- inner scrolling as a substitute for correct height;
- prompt text truncation or normalization;
- repeated node `setSize()` loops;
- changes to #394 resolution semantics or controls;
- #64 completion behavior;
- unrelated Prompt Studio refactoring.

### Rollback boundary

Revert only bounded paste/input remeasurement and its tests. Existing manual
resize, width reflow, highlight, node-layout ownership, and #394 remain intact.

## 6. REL-FEAT-03 — Expanded #64 execution plan

Issue #64 owns three connected user outcomes:

1. configurable artist-only autocomplete prefix;
2. non-destructive completion in the middle of text; and
3. bracket-group and selected-text editing ergonomics.

It does not own textarea autosize; that remains #401. The #335 canonical settings
initialization contract is already integrated in PR #400 and must be reused.

### 6.1 Settings contract

#### Artist prefix

```text
internal key: autocomplete.artist_prefix
Comfy key: EasyUseAnima.Prompt.AutocompleteArtistPrefix
default: @
```

- trim surrounding whitespace;
- reject newline, comma, control characters, and excessive length;
- empty or invalid values fall back to `@`;
- compare the prefix literally rather than building an unsafe dynamic regex;
- apply it only to artist-only query and insertion;
- do not rewrite existing prompt text.

#### Completion commit mode

```text
internal key: autocomplete.commit_mode
Comfy key: EasyUseAnima.Prompt.AutocompleteCommitMode
accepted values: smart | insert | replace
default: smart
```

- `smart`: replace only a proven contiguous active-item tail and preserve
  whitespace/delimiter-separated suffix text;
- `insert`: end the edit at the caret and unconditionally preserve everything to
  the right;
- `replace`: use the reviewed syntax-aware active-item replace range, never the
  old whole comma segment.

Ambiguity is resolved in favor of preserving text.

#### Selected-parentheses weight

```text
internal key: prompt_studio.selection_parenthesis_weight
Comfy key: EasyUseAnima.Prompt.SelectionParenthesisWeight
default: false
```

- OFF: selected text plus `(` becomes `(selected)`;
- ON: it becomes `(selected:1)` and the inserted `1` is selected;
- an existing top-level numeric weight is not duplicated;
- an empty selection retains normal `()` pair behavior.

All keys are owned by canonical `easyuse_anima.settings` and reflected in public
settings, frontend definitions/runtime, localization, and setting parity tests.
Root settings shims must not regain implementation.

### 6.2 Range contract

The pure text model must expose enough information to keep search and editing
separate:

```text
queryStart/queryEnd
insertStart/insertEnd
replaceStart/replaceEnd
caret and selection
syntax group boundaries
protected suffix start
```

Required parsing rules:

1. honor an explicit non-empty selection;
2. handle escaped brackets as literals;
3. track `()`, `{}`, and `[[ ]]` nesting;
4. treat comma/newline at the active nesting level as item boundaries;
5. never include a whitespace-separated right suffix in the default replace
   range;
6. allow only the caret-adjacent contiguous tail as a `smart` replace candidate;
7. protect `:number`, `)`, `}`, and `]]` suffixes;
8. allow query context to be wider than the edit range for multi-word tags; and
9. use the identical edit plan for inline preview and commit.

### 6.3 Required non-destructive examples

```text
foo| bar + completion "foo tag"
  -> bar remains

(foo|, bar:1.2)
  -> (foo tag, bar:1.2)

[[artist_a, art|ist_b:0.7]]
  -> artist_a and :0.7 remain

old_t|ag
  smart  -> only the proven contiguous tail may be replaced
  insert -> ag remains
```

At minimum, a complete recognized tag separated by whitespace to the right of
the caret must never be deleted. The accepted default is stronger: every
whitespace-separated suffix is protected in `smart` mode.

### 6.4 Completion edit planner

`planAutocompleteInsertion()` must choose a reviewed range according to the
commit mode rather than use one segment-wide `start/end` pair.

Return shape may evolve during 03A but must support:

```text
start/end
replacement
caretOffset or selectionStartOffset/selectionEndOffset
preservedSuffix
modeUsed
```

- `replaceInputRange()` may be extended to set a post-insert selection;
- each command remains one undoable edit;
- `execCommand("insertText")` and `setRangeText()` fallbacks produce the same
  text and selection; and
- IME composition never commits a suggestion.

### 6.5 Bracket editing contract

- support consistent selected-text wrapping for `()`, `{}`, and `[[ ]]`;
- skip over an already auto-inserted closing delimiter when the user types it;
- do not auto-close or rewrite the entire bracket group on completion commit;
- preserve other comma-separated items in the same group;
- allow more than one autocomplete item inside one pair;
- optional weighted wrapping inserts `(selection:1)` as one undoable edit and
  selects `1` for immediate replacement;
- preserve nested and escaped delimiters; and
- define multiline selection behavior in pure tests before enabling it.

Backspace pair deletion and unrelated editor conveniences are not implicitly in
scope. Add them only through a separately reviewed work unit.

### 6.6 Work units

#### REL-FEAT-03A — Completion edit Contract

- freeze current destructive examples as regression fixtures;
- define dual ranges, syntax-group boundaries, settings names/defaults, and
  insertion result shape;
- minimize production behavior changes.

#### REL-FEAT-03B — Artist prefix setting

- add canonical persistence and frontend UI;
- parameterize query, insertion, inline preview, and forced artist-only fields;
- preserve exact default `@` behavior.

#### REL-FEAT-03C — Safe mid-text completion

- implement `smart|insert|replace` edit planning;
- preserve right suffix, weights, and closers;
- make preview and commit use the same plan;
- preserve separator, period, wildcard, cancellation, and IME behavior.

#### REL-FEAT-03D — Bracket and weighted-selection UX

- implement group-aware editing and selected wrapping;
- add optional `(selection:1)` placeholder selection;
- complete Legacy Canvas, Node 2.0, keyboard, IME, undo, save/reload, and
  accessibility evidence.

### 6.7 Branch and PR isolation

#64 uses four ordered PRs because Contract, settings, edit behavior, and bracket
behavior have independent rollback boundaries:

```text
codex/rel-feat-03a-completion-contract
codex/rel-feat-03b-artist-prefix
codex/rel-feat-03c-safe-midtext
codex/rel-feat-03d-bracket-ux
```

Do not combine #401, reopen #335/#394, or perform broad autocomplete refactoring
inside these PRs.

### 6.8 Existing behavior to preserve

- source ranking, result order, category API, dataset/index format;
- wildcard autocomplete;
- natural-sentence period handling;
- append-separator and no-comma-after-period settings;
- inline preview enable/disable;
- Shift+Enter line break;
- Enter/Tab commit setting;
- forced artist-only input scope;
- workflow text and node/widget serialization; and
- autocomplete cache, cancellation, and IME lifecycle.

### 6.9 Required tests

```text
artist prefix default/custom/duplicate/persistence
forced artist-only field with custom prefix
non-artist categories unchanged
mid-segment commit with whitespace-separated right tag preserved
mid-segment commit with comma/newline suffix preserved
contiguous tail smart replace
always-insert mode preserves all right text
weight and closing syntax preserved
nested parentheses and [[ ]] active item only
multiple comma-separated items in one group
preview/commit range parity
selection -> (), {}, [[ ]]
selection + weight option -> (selection:1), numeric placeholder selected
existing numeric weight -> no duplicate :1
one undo step per edit
IME composition and popup commit
Legacy Canvas / Node 2.0 live smoke
```

## 7. Revised release-candidate matrix

REL-RC-01 runs only after #401 and all four #64 units are integrated on one exact
`dev` head. The already merged #266, #267, #335, and #394 behavior remains part
of the regression matrix.

Automated gates:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
comfy node validate
comfy node pack
```

Inspect the actual archive for required Python, JavaScript, locale, CSV,
workflow, and changelog inputs.

### #401 flows

- 100+ line paste and long wrapped-line paste;
- auto and manual textarea height modes;
- narrow width and paste/resize ordering;
- no textarea inner scrollbar;
- no stale scheduled resize after rapid input or node removal;
- Classic, Advanced, AdvancedV2, Legacy Canvas, and Node 2.0 where applicable.

### #64 flows

- default and custom artist prefix search/insertion/persistence;
- no duplicate prefix and no non-artist category change;
- whitespace-, comma-, and newline-separated right suffix preservation;
- complete right-hand tag preservation;
- `smart`, `insert`, and `replace` modes;
- numeric weight and closing-bracket preservation;
- multiple items in one bracket group;
- inline preview/commit parity;
- `()`, `{}`, and `[[ ]]` selection wrapping;
- optional `(selection:1)` with the numeric placeholder selected;
- IME, keyboard, undo, save/reload, Legacy Canvas, and Node 2.0.

### Previously merged regression flows

- #266 cross-user profile provenance;
- #267 track click and thumb drag;
- #335 fresh locale default and explicit-value preservation; and
- #394 preset/custom/NAIA orientation switching.

A release candidate fails if any accepted completion deletes text outside its
reviewed edit range, or if a long-paste textarea finishes with hidden overflow.

## 8. Revised resumption gate

The ordinary backend queue remains paused until:

- #266, #267, #335, and #394 remain integrated and regression-clean;
- #401 is complete;
- #64 REL-FEAT-03A through REL-FEAT-03D are all integrated;
- the revised REL-RC-01 passes at one exact `dev` head;
- release preparation, `main` integration, immutable tag, Registry publication,
  and read-back complete; and
- no immediate P0/P1 post-release regression remains open.

## 9. Codex instructions

### Current first task

```text
Read docs/architecture/release-first-stabilization-lane.md, then
prompt-studio-autocomplete-release-addendum.md, Issue #395, and Issue #401.
Confirm PRs #397 through #400 are integrated and no open PR owns REL-BUG-03.

Create codex/rel-bug-03-prompt-studio-paste from latest origin/dev. Reproduce the
long-paste clipping in each Prompt Studio textarea family and record immediate,
first-frame, and post-layout scrollHeight/clientHeight values. Implement only
bounded revision-owned grow-only remeasurement. Preserve #394 and do not touch
#64 completion behavior.

Run focused tests, tools/check_project.ps1 -Profile full, and Legacy/Node 2.0
paste smoke. Record exact base/head SHA, affected variants, final fit invariant,
rollback boundary, and next task REL-FEAT-03A. Do not merge, version, tag, or
publish from this implementation task.
```

### When REL-FEAT-03A becomes READY

```text
Read the updated Issue #64. Start with Contract/tests only: reproduce right-text
deletion and define query/insert/replace ranges, protected suffixes,
bracket-group boundaries, and all three setting contracts. Do not jump directly
to one broad implementation PR. Execute 03A, 03B, 03C, and 03D in order and
record exact base/head SHA, rollback boundary, focused/full/live evidence, and
next unit.
```
