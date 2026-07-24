# Prompt Studio and Autocomplete UX Release Addendum

## Document status

- Status: active release-lane addendum
- Snapshot date: 2026-07-24
- Base branch: `dev`
- Base release lane: [`release-first-stabilization-lane.md`](release-first-stabilization-lane.md)
- Release owner: [#395](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/395)
- Expanded autocomplete work: [#64](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/64)
- New release-blocking textarea bug: [#401](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/401)

This addendum records two user-facing requirements discovered after the original
release-first lane was written. While #395 is open, it overrides the relevant
queue, #64 manifest, release-candidate matrix, and resumption checklist in the
base lane. All other freeze, validation, release, and ownership rules remain in
force.

## 1. Revised critical path

```text
REL-BUG-01   #266 LoRA workflow profile provenance
  -> REL-BUG-02   #267 LoRA scrollbar pointer interaction
  -> REL-BUG-03   #401 Prompt Studio long-paste textarea autosize
  -> REL-FEAT-01  #335 locale-aware initial autocomplete source
       + REL-FEAT-02  #394 resolution orientation switch in parallel
  -> REL-FEAT-03A #64 completion edit Contract
  -> REL-FEAT-03B #64 configurable artist prefix
  -> REL-FEAT-03C #64 safe mid-text completion
  -> REL-FEAT-03D #64 bracket and weighted-selection UX
  -> REL-RC-01 integrated release-candidate validation
  -> REL-PREP-01 release preparation
  -> REL-PUBLISH-01 main/tag/Registry publication
  -> backend refactor re-audit and resume
```

The first READY task remains REL-BUG-01 / #266. This addendum does not authorize
starting #401 or #64 ahead of their prerequisites.

## 2. Revised executable queue

| Order | Task ID | Owner | State at this snapshot | Type | Prerequisites |
| ---: | --- | --- | --- | --- | --- |
| 1 | REL-BUG-01 | #266 | READY | Fix | latest `dev`; no overlapping PR |
| 2 | REL-BUG-02 | #267 | BLOCKED | Fix | REL-BUG-01 merged |
| 3 | REL-BUG-03 | #401 | BLOCKED | Fix | REL-BUG-02 merged; rebase Prompt Studio frontend |
| 4A | REL-FEAT-01 | #335 | BLOCKED | Feature/Contract | REL-BUG-03 merged |
| 4B | REL-FEAT-02 | #394 | BLOCKED | Feature | REL-BUG-03 merged; may run with 4A only when file ownership remains disjoint |
| 5A | REL-FEAT-03A | #64 | BLOCKED | Contract/test | REL-FEAT-01 and REL-FEAT-02 merged |
| 5B | REL-FEAT-03B | #64 | BLOCKED | Feature/Contract | REL-FEAT-03A merged |
| 5C | REL-FEAT-03C | #64 | BLOCKED | Fix/Feature | REL-FEAT-03B merged |
| 5D | REL-FEAT-03D | #64 | BLOCKED | Feature | REL-FEAT-03C merged |
| 6 | REL-RC-01 | #395 | BLOCKED | Integration gate | six issues and all #64 units merged |
| 7 | REL-PREP-01 | #395 | BLOCKED | Release-only | REL-RC-01 passed |
| 8 | REL-PUBLISH-01 | #395 | BLOCKED | Release | release prep reviewed and merged |

One issue may use several rollback-sized PRs when its accepted plan explicitly
requires ordered Contract and Behavior units. Do not combine #401 with #394 or
#64 merely because they touch Prompt Studio.

## 3. Verified autocomplete failure surface

The current frontend has one search range and one replacement range.

`web/js/autocomplete/text_model.js` currently:

1. scans left and right to comma or newline;
2. trims prompt-syntax prefixes and suffixes;
3. returns one `start` and `end`; and
4. lets `planAutocompleteInsertion()` replace that full range.

This means that a caret in the middle of a comma-delimited segment can cause
right-hand text in the same segment to be removed. Search context and edit
ownership are incorrectly coupled.

The accepted correction follows the editor model used by LSP
`InsertReplaceEdit` and Monaco suggestion insert/replace modes, without adding an
editor dependency:

```text
query range   != insert range != replace range
```

- query range may include a multi-word search prefix;
- insert range ends at the caret and preserves right-hand text;
- replace range may include only the proven contiguous tail of the active item;
- closing brackets, numeric weights, separators, and separate suffix tags are
  protected.

Official design references:

- https://microsoft.github.io/language-server-protocol/specifications/lsp/3.18/specification/#textDocument_completion
- https://microsoft.github.io/monaco-editor/typedoc/interfaces/editor_editor_api.editor.ISuggestOptions.html

## 4. REL-BUG-03 — Long-paste textarea autosize

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
still capture live values to prove which affected node variants reproduce the
reported clipping.

### Required implementation

```text
input or paste
  -> immediate grow
  -> bounded requestAnimationFrame remeasure
  -> optional one additional post-node-layout verification
  -> stop when content fits or retry budget is exhausted
```

Rules:

- use an input revision/epoch so stale callbacks cannot overwrite newer text;
- post-layout corrections are grow-only;
- use a small fixed retry budget, never an unbounded RAF or polling loop;
- removed/disconnected inputs make scheduled work a safe no-op;
- preserve the current auto/manual height distinction;
- manual height remains user-owned but grows when content no longer fits;
- keep `overflowY: hidden` on the textarea;
- reuse existing Advanced and Classic height/layout owners;
- do not create a document-level paste listener or global timer registry.

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
- #394 resolution behavior;
- #64 completion behavior;
- unrelated Prompt Studio refactoring.

### Rollback boundary

Revert only bounded paste/input remeasurement and its tests. Existing manual
resize, width reflow, highlight, and node-layout ownership remain intact.

## 5. REL-FEAT-03 — Expanded #64 execution plan

Issue #64 now owns three connected user outcomes:

1. configurable artist-only autocomplete prefix;
2. non-destructive completion in the middle of text; and
3. bracket-group and selected-text editing ergonomics.

It does not own textarea autosize; that remains #401.

### 5.1 Settings contract

#### Artist prefix

```text
internal key: autocomplete.artist_prefix
Comfy key: EasyUseAnima.Prompt.AutocompleteArtistPrefix
default: @
```

- trim surrounding whitespace;
- reject newline, comma, control characters, and an excessive length;
- empty or invalid values fall back to `@`;
- compare the prefix literally rather than building an unsafe dynamic regular
  expression;
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

All keys must be owned by canonical `easyuse_anima.settings` and reflected in
public settings, frontend definitions/runtime, localization, and setting parity
tests. Root settings shims must not regain implementation.

### 5.2 Range contract

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
8. allow query context to be wider than the edit range for multi-word tags;
9. use the identical edit plan for inline preview and commit.

### 5.3 Required non-destructive examples

```text
foo| bar + completion "foo tag"
  -> bar remains

(foo|, bar:1.2)
  -> (foo tag, bar:1.2)

[[artist_a, art|ist_b:0.7]]
  -> artist_a and :0.7 remain

old_t|ag
  smart  -> only proven contiguous tail may be replaced
  insert -> ag remains
```

At minimum, a complete recognized tag separated by whitespace to the right of
the caret must never be deleted. The accepted default is stronger: every
whitespace-separated suffix is protected in `smart` mode.

### 5.4 Bracket editing contract

- support consistent selected-text wrapping for `()`, `{}`, and `[[ ]]`;
- skip over an already auto-inserted closing delimiter when the user types it;
- do not auto-close or rewrite the entire bracket group on completion commit;
- preserve other comma-separated items in the same group;
- allow more than one autocomplete item inside one pair;
- optional weighted wrapping inserts `(selection:1)` as one undoable edit and
  selects `1` for immediate replacement;
- preserve nested and escaped delimiters;
- define multiline selection behavior in pure tests before enabling it.

### 5.5 Work units

#### REL-FEAT-03A — Completion edit Contract

- freeze current destructive examples as failing/regression fixtures;
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

### 5.6 PR isolation

#64 may use four ordered PRs under one issue because Contract, settings, edit
behavior, and bracket behavior have independent rollback boundaries. Each branch
uses:

```text
codex/rel-feat-03a-completion-contract
codex/rel-feat-03b-artist-prefix
codex/rel-feat-03c-safe-midtext
codex/rel-feat-03d-bracket-ux
```

Do not combine #335, #401, or broad autocomplete refactoring into these PRs.

## 6. Revised release-candidate matrix

REL-RC-01 runs only after all six issues and all #64 units are integrated on one
exact `dev` head.

Automated gates remain:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
comfy node validate
comfy node pack
```

In addition to the base lane matrix, verify:

### #401

- 100+ line paste and long wrapped-line paste;
- auto and manual textarea height modes;
- narrow width and paste/resize ordering;
- no textarea inner scrollbar;
- no stale scheduled resize after rapid input or node removal;
- Classic, Advanced, AdvancedV2, Legacy Canvas, and Node 2.0 where applicable.

### #64

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

A release candidate fails if any accepted completion deletes text outside its
reviewed edit range, or if a long-paste textarea finishes with hidden overflow.

## 7. Revised resumption gate

The ordinary backend queue remains paused until:

- #266, #267, #401, #335, #394, and #64 are complete;
- #64 REL-FEAT-03A through REL-FEAT-03D are all integrated;
- the revised REL-RC-01 passes at one exact `dev` head;
- release preparation, `main` integration, immutable tag, Registry publication,
  and read-back complete; and
- no immediate P0/P1 post-release regression remains open.

## 8. Codex instructions

### Current first task

```text
Read docs/architecture/release-first-stabilization-lane.md, then this addendum,
and Issue #395. Select REL-BUG-01 / #266. Do not start #401 or #64 early.
```

### When REL-BUG-03 becomes READY

```text
Read Issue #401 and inspect both Prompt Studio textarea families. Reproduce and
record immediate, first-frame, and post-layout scrollHeight/clientHeight values.
Implement bounded revision-owned grow-only remeasurement. Do not touch #394 or
#64. Run focused tests, the full project check, and Legacy/Node 2.0 paste smoke.
```

### When REL-FEAT-03A becomes READY

```text
Read the updated Issue #64. Start with Contract/tests only: reproduce right-text
deletion, define query/insert/replace ranges, protected suffixes, bracket-group
boundaries, and the three setting contracts. Do not jump directly to one broad
implementation PR. Execute 03A, 03B, 03C, and 03D in order and record exact
base/head SHA, rollback boundary, focused/full/live evidence, and next unit.
```
