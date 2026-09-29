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

## Result and validation (2026-09-29)

- Runtime candidate: `30b5133`. Ordinary seeds retain numeric JSON; seeds above
  `2^53-1` use decimal strings. Legacy integer literals in settings and profile
  responses are preserved before browser number conversion. Already rounded
  numeric inputs are rejected; lost digits in old corrupted files cannot be recovered.
- The random range and -1/-2/-3 controls are unchanged. Increment/decrement for
  explicit seeds above `2^50` use uint64 clamp bounds; ordinary seeds retain
  the previous bounds. Both reservation-service and fallback paths are covered.
- Full passed on ComfyUI 0.37.0 / frontend 1.52.7: 1,719 Python tests (3 skips),
  frontend checks for 125 JavaScript files and required static/ownership gates.
  Initial failures were a profile sampler type narrowing error and a stale
  frontend export contract; both were fixed without relaxing the gates.
- Packaged 358 runtime files, installed only in the isolated test instance.
  Served settings module matched the source; both Legacy Canvas and Node 2.0
  preserved 39, `2^50+1`, `2^53+1`, `2^64-1` through DOM editing and workflow
  serialization, disk save and reload. Both also reopened the generated PNG.
- Actual 28-block Anima generation: uint64 maximum, 256x256, Euler/simple,
  3 steps, CFG 3, RTX 5070 Ti. Use Last restored the exact execution seed.
  Restarted the server; replay used no cached nodes and produced identical RGB
  pixels (`7061c2cc226b0c129eb40d016c6d868c47e0a6b46a83a33305ef9a2c09a0f411`).
  No browser page errors. Test canvas/locale settings were restored and server stopped.
- The browser harness initially raced Node 2.0 startup workflow restoration;
  waiting for initialization resolved the mismatch without a product-code change.
- Shared-subgraph instance replay remains outside this fix (#786).
