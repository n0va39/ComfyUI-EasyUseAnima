# Native Safe PAG (#766)

## Task contract

- Base: dev `acd53db04bff571601a92efe379da4459b29176b`.
- Goal: one internal Safe PAG engine for AiO and standalone `Easy Anima Safe PAG`.
- Public ID: `EasyAnimaSafePAG`; do not register or replace `AnimaSafePAG`.
- Scope: internal engine/node, AiO leaf and capability, locales/docs, tests and
  required backend inventories. DAVE is a separate branch/PR (#765).
- Preserve: existing Safe PAG settings/defaults/stage scope and numerical math,
  Compile/DAVE/Sage order, existing sampler callbacks and unrelated MODEL clones.
- Verify: upstream tensor parity, temporary attention restoration including setup
  failure and interruption, dependency absence/coexistence, full/package and
  isolated GPU plus Legacy Canvas/Node 2.0 save/reload.
- Stop on unsupported host/model contracts or uncertain source rights; no unsafe
  loader, network/model download or silent external fallback.
- No version/release/user-instance changes. Spectrum stays external.

The user explicitly authorized this implementation and the separately named
standalone node on 2026-09-15, extending #766's AiO-only scope.

## Implementation and validation (2026-09-15)

Code candidate: `02486544a45d` (subsequent validation-record changes are docs only).

- The native engine retains the pinned upstream attention/guidance arithmetic.
  Temporary attention replacement uses a shared lock and call token, restores
  inherited methods as inherited methods, and cleans up partial setup, errors,
  and interruption. Predictions are isolated by execution context. Reapplying
  the native node replaces its own callbacks while retaining unrelated ones.
- A review found that Compile can rebuild the underlying model. The callback
  now resolves the actual execution model's blocks; a regression covers copied
  callbacks with distinct replacement blocks.
- Nine focused native tests passed, including frozen upstream attention/rescale
  parity, 28/40-block cleanup, shared-module siblings, previous callbacks,
  repeated application, zero-scale identity and AiO/standalone delegation.
- Workspace full passed: **1,704 unittest tests, 3 skips**, all frontend checks
  (125 JavaScript files), static/baseline/ownership checks and `git diff --check`.
- Official `comfy node pack` produced 357 files and installed the package in the
  isolated test instance. The engine, standalone adapter, upstream MIT LICENSE
  and NOTICE are included. The served dependency module matched the source.
- Environment: ComfyUI **v0.35.0**, frontend **1.51.10**, Python 3.12.13,
  PyTorch 2.12.1+cu130, RTX 5070 Ti. The direct GPU comparison used
  `anima_baseV10` (28 blocks), 256×256, seed 39, 3 Euler/simple steps and CFG 3.
  Pinned upstream, standalone node and AiO leaf produced exactly equal latents.
- With the external Safe PAG pack removed from the isolated runtime, the new
  node registered and AiO generated successfully. Legacy Canvas and Node 2.0
  both applied and restored non-default Safe PAG settings, retained the unique
  standalone ID/widgets, and produced the same backend settings.
- After restoring the external pack and restarting the server, both distinct
  node IDs registered. Loading the saved PNG restored the settings and a fresh
  AiO execution used no cached nodes. Both generated images were pixel-identical
  (SHA-256 `26f64a8e04f19ba35c3a183f4310f59a98f6a2acba7a348b946216e4e3219f6b`).
  Saved settings retained enabled state, scale 3.5, blocks 17–18, head 0 and seed
  39. The browser replay reported no page errors.

The 40-block boundary is covered by focused tensor/lifecycle checks; a real
40-block generation, actual Torch Compile optimization and multi-GPU execution
were not exercised. Existing stage/cache tests passed in full; the new GPU
smoke exercises first pass. DAVE remains a separate adoption decision (#765).

The external test pack and Canvas/locale settings were restored. Only the
isolated test installation was replaced; user instances were not changed.
