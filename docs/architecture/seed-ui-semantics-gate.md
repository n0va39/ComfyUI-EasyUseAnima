# Seed UI Semantics Gate

## Status and authority

- Status: active feature-semantics gate for Issues #413, #414, and #415
- Snapshot branch: `dev`
- Snapshot commit: `2379faba841853422fe34ef194b9bbeb2bc6372d`
- Applies after: QSTATE-02B Contract review
- Does not change: QSTATE-02 transaction identity, event-envelope correlation, or release priority

This document prevents two different seed models from being collapsed into one
frontend publication rule:

1. Prompt Studio Wildcard uses a **concrete editable seed plus an after-generate
   transition**.
2. AiO uses rgthree-style **persistent special selection tokens** (`-1/-2/-3`)
   in addition to an ordinary concrete-seed mode.

The shared queue transaction owner decides only whether a feature may publish a
next state. It never decides what a seed value means.

## 1. Verified current contracts

### 1.1 Prompt Studio Wildcard

The Prompt Studio adapter always submits a concrete non-negative seed.
`prompt_studio_seed_execution()` creates a reservation with:

```text
selection = concrete
seed = current wildcard seed
after_generate = fixed | randomize | increment | decrement
overflow = wrap
editable domain = 0 .. Number.MAX_SAFE_INTEGER
```

The executed payload distinguishes:

```text
wildcard_execution_seed = seed used by this execution
wildcard_seed           = next concrete seed
```

The frontend also stores previous-execution history separately so a workflow can
serialize the accepted execution seed with fixed control for reproducibility while
the live editor remains on its next-run concrete seed.

### 1.2 AiO Generator

AiO accepts either a concrete seed or one of these persistent selection tokens:

```text
-1 = randomize every queue
-2 = increment from the previous concrete execution seed
-3 = decrement from the previous concrete execution seed
```

The backend translates these tokens into reservation `selection` values. The
concrete execution seed is authoritative for sampling, cache keys, and metadata,
but it is not the editable token shown to the user.

The rgthree Seed reference removes ComfyUI's separate
`control_after_generate` widget and lets the special token own repeated queue-time
selection. It changes only the submitted prompt copy and keeps the live token.

## 2. Non-interchangeable behavior

| Concern | Prompt Studio Wildcard | AiO special token | AiO concrete seed |
| --- | --- | --- | --- |
| Editable value | concrete integer | `-1`, `-2`, or `-3` | concrete integer |
| Queue-time selection | current concrete value | token-defined stream selection | current concrete value |
| `after_generate` role | computes the next concrete editable value | must not replace or advance the visible token | computes the next concrete editable value |
| Live value after accepted result | next concrete seed, if revision is current | same special token | next concrete seed, if revision is current |
| Overflow domain | wrap | stream contract; no token mutation | current AiO concrete domain policy |
| Execution seed | previous-execution history | last-seed/history only | last-seed/history and possible next-state basis |

The following abstraction is forbidden:

```text
all seed results -> write payload.next_seed into the live widget
```

The following abstraction is accepted:

```text
shared transaction gate
  -> feature adapter interprets its own seed contract
  -> feature adapter publishes only the allowed next state
```

## 3. Prompt Studio Wildcard contract

### 3.1 Required behavior

- The editable seed remains a concrete integer; negative sentinel values are not
  introduced.
- `fixed` keeps the current concrete seed.
- `randomize` chooses one new concrete next-run seed after an accepted execution.
  It is not a persistent random-mode token.
- `increment` and `decrement` compute one concrete next-run seed using the existing
  wrap domain.
- The next concrete seed is written to the live widget only when the accepted
  prompt transaction and `prompt.wildcard_seed` revision are still current.
- A stale result may update non-editable previous-execution history but cannot
  overwrite a newer seed or control edit.
- `wildcard_mode` (`populate/general` versus `sequential`) remains independent from
  `wildcard_seed_after_generate`.
- Existing previous-execution workflow serialization remains compatible unless a
  separate migration is approved.

### 3.2 Required tests

```text
seed 7 + fixed      -> execution 7, live next 7
seed 7 + increment  -> execution 7, live next 8
seed MAX + increment -> live next 0
seed 0 + decrement  -> live next MAX
seed 7 + randomize  -> one concrete next value; following queue uses it
queue seed 7 -> user edits 99 -> old result does not replace 99
old result may record execution seed 7 in non-editable history
workflow save/reload preserves the accepted reproducibility contract
```

Use deterministic random sources in tests. Do not copy AiO special-token logic
into Prompt Studio.

## 4. AiO special-token contract

### 4.1 Required observable behavior

- `-1/-2/-3` remain visible after any number of accepted, rejected, cancelled, or
  out-of-order queue results.
- The backend reservation service remains the source of concrete execution seeds.
- Actual execution seeds update only last-seed/history state.
- `Use Last` is the explicit transition from a special token to one concrete fixed
  seed.
- `New Fixed Random` creates one concrete fixed seed and leaves special mode.
- Workflow serialization stores the special token, not the concrete result.
- No queue path temporarily mutates the live widget to a concrete seed.

### 4.2 Interaction with `seed_after_generate`

A special selection token already owns repeated queue-time selection. Therefore a
second after-generate transition must not create another user-visible or stream
advance.

Required effective rule:

```text
seed in {-1, -2, -3}
  -> special selection is authoritative
  -> live token is preserved
  -> effective after-generate behavior is fixed/no second transition
```

For compatibility, the stored `seed_after_generate` setting may be retained and
become active again when the user switches to a concrete seed. It must not affect
the special-mode execution sequence while a token is active.

The implementation may normalize the effective reservation request to `fixed` or
prove an equivalent backend-only result, but AIO-SEED-UI-02 cannot begin until the
Contract fixture demonstrates that there is no double advancement.

### 4.3 Required matrix

```text
-1 x every stored after_generate value
  -> each queue uses a new concrete random seed
  -> widget remains -1
  -> exactly one queue-time selection occurs

-2 x every stored after_generate value
  -> concrete executions advance by exactly +1 per accepted queue
  -> widget remains -2

-3 x every stored after_generate value
  -> concrete executions advance by exactly -1 per accepted queue
  -> widget remains -3

concrete seed x fixed/randomize/increment/decrement
  -> after_generate computes a concrete next editable value
  -> publication requires current transaction revision
```

This matrix is a hard gate, not an optional compatibility test.

## 5. Revised feature sequence

```text
QSTATE-02B  two-phase Contract
  -> QSTATE-02C transaction core
       +
     QSTATE-02D executed-event envelope bridge

QSTATE-02B 이후 병렬 가능:
  -> QSTATE-03 LoRA result replay retirement

QSTATE-02C/D 이후:
  -> QSTATE-04A Prompt Studio submitted-snapshot replay retirement
  -> QSTATE-04B Prompt Studio Wildcard concrete next-seed compare-and-commit
  -> AIO-SEED-UI-01 special/concrete intent-display Contract and full matrix
  -> AIO-SEED-UI-02 backend payload/effective-control implementation
  -> AIO-SEED-UI-03 frontend publication and last-seed UX
```

QSTATE-04A and QSTATE-04B may share one PR only when their file ownership and
rollback boundary remain small. They may not import AiO seed semantics.

AIO-SEED-UI-01 may start after the shared transaction API is frozen, but
AIO-SEED-UI-02/03 remain blocked until its full special-token matrix is reviewed.

## 6. Stop conditions

Stop and record a blocker before implementation expands if:

- the shared transaction core parses seed values or control names;
- Prompt Studio requires negative sentinel values to implement next-seed control;
- AiO special mode reuses Prompt Studio's concrete next-seed publication helper;
- a special token plus non-fixed `seed_after_generate` advances the concrete stream
  more than once per accepted queue;
- workflow serialization replaces an AiO special token with an execution seed;
- Prompt Studio previous-execution serialization must change to implement stale
  protection;
- a mapped payload with multiple items attempts an editable seed commit without a
  separate aggregation Contract.

The first three conditions require design correction. The double-advance or
serialization conditions require another focused PRO-level review before AiO seed
implementation continues.

## 7. Focused validation ownership

### QSTATE-04B

```text
frontend queue transaction smoke
Prompt Studio Advanced executed-values smoke
Prompt Studio wildcard seed/history/serialization smokes
focused Python seed adapter tests when backend payload meaning changes
git diff --check
```

### AIO-SEED-UI-01

```text
frontend AiO executed-seed Contract smoke
Python seed adapter and reservation tests
special-token x after_generate golden matrix
git diff --check
```

### AIO-SEED-UI-02/03

Add backend AiO node/generation tests only when their result construction changes.
Add the generator-panel or extension-runtime smoke only when those owners change.
Run dual-canvas live validation only on the final feature cutover, not during the
Contract edit loop.

## 8. Codex continuation rule

QSTATE-02B, QSTATE-02C/D, and QSTATE-03 may continue without another seed review.
Before QSTATE-04B or AIO-SEED-UI implementation, read this document and use separate
feature task cards and separate surface tokens:

```text
prompt.wildcard_seed
prompt.wildcard_history
aio.seed_selection
aio.last_seed
aio.concrete_next_seed
```

Names may change, but the ownership split may not collapse.
