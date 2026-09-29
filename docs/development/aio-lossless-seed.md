# AiO lossless seed round trip (#784)

- Base: dev `3b00f885f5fb158be4b7ca5d8a42e4a0f099b16f`.
- Goal: preserve uint64 seeds through settings, UI, queue, execution publication,
  saved-image workflows and Use Last. Keep ordinary numeric seeds and random range.
- Scope: AiO settings parser/normalizer, seed UI and transaction adapter, execution
  metadata, their direct tests and generated source inventories.
- Contract: existing node IDs/settings keys/schema, -1/-2/-3, random source and
  uint64 backend semantics remain. Above JS safe integer, serialize decimal strings;
  Python already accepts these. Recover exact integer lexemes in legacy settings JSON.
  Reject already imprecise JS numbers and invalid/out-of-range edits without coercion.
- Checks: 39, 2^50+1, 2^53+1 and 2^64-1; exact serialization, stale-result protection,
  fixed/increment/decrement, Use Last; full and both canvases, uncached GPU replay.
- Stop: lost precision, changed random behavior, workflow/API regression or failed
  required environment checks. Shared-subgraph replay (#786) is separate.
- ResShift 0.27 validation and 1.3.0 metadata preparation follow separately.
  No main, release, Registry publication or user-instance changes.
