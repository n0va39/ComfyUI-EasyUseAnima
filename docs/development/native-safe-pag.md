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

## Attention container compatibility task (2026-09-29)

- Base: `fcd17d81ccbd1d9ba49a8a9daff6a5d938a18c6f`, continuing PR #793.
- Scope: native attention adapter, direct regression tests, provenance and validation records.
- Preserve: tensor arithmetic, token isolation, upstream container ownership, node IDs and saved settings.
- Fix: inspect containers with `peek()` only for PAG; pass the original objects to normal attention.
- Checks: tensor/container parity for absent, invalid, normal, PAG-only and mixed labels; native focused suite; full and latest-stable host smoke.
- Stop: failed host/dependency update or changed attention contract beyond this adapter.

### Validation (2026-09-29)

Runtime source SHA-256 (LF):
`edc88a909c5471f160ee0f8c8dcec078943bac12d50c76702b3d6a3fb46b9657`.

- Focused native suite: 10 tests passed. The new regression covers tensor and
  single-use container inputs, ownership tokens, absent/invalid labels, normal,
  PAG-only and mixed batches, original object identity and consumption counts.
- Final workspace `check_custom_node.ps1 -Profile full`: 1,705 Python tests,
  3 existing skips; frontend checks for 125 JavaScript files and TypeScript
  6.0.3; import, size, ownership and diff gates passed. The first run found only
  stale analyzer source metrics; regenerated the snapshot, passed its exact
  focused test, then passed full. No gate or baseline allowance was weakened.
- Official `comfy-cli==1.20.0` package: 357 files, installed in the isolated
  stable test instance with the previous install retained. Installed engine
  hash matches the source; MIT LICENSE and updated NOTICE are included.

| Core | Actual boundary and result |
|---|---|
| v0.27.0 (`bb131be9e83d2f773c90f1d6f1e4b248a498c8c5`) | Separate compatibility checkout/venv with its pinned frontend 1.45.20, kitchen 0.2.16 and aimdo 0.4.10; `pip check` passed. Real `Attention.forward` tensor path and 28-block GPU generation passed. |
| Latest stable v0.37.0 (`73c9bad4d21e7addbe1d13bc92eee0f1431b017d`) | Frontend 1.52.7. Its Predict2 caller still passes tensors. Packaged standalone and actual AiO API image generation passed; `/object_info` proved `EasyAnimaSafePAG` and original `AnimaSafePAG` register from distinct packs. |
| Development snapshot `a7169322485d0049380fb207fa17e9fb3ec40486` | Real container-based `Attention.forward` reproduced the original `AttributeError`. Patched native attention and 28-block GPU generation passed. This is supplementary development-branch evidence, not the official stable release. |

GPU probes used RTX 5070 Ti, Python 3.12.13, PyTorch 2.12.1+cu130,
`anima_baseV10`, 256x256, seed 39, Euler/simple, 3 steps, CFG 3.
On both v0.27.0 and the development snapshot, the standalone and AiO leaf
latents exactly matched the pinned original with only the reported `peek()`
adaptation applied. Original attention references were restored. The v0.27.0
venv reuses unpinned dependencies from the Codex test environment while its
version-pinned packages are installed locally; no user environment was changed.
This proves within-version parity, not identical output across core versions.

The direct GPU harnesses emitted ComfyUI `ModelPatcher.__del__` warnings during
interpreter teardown after assertions completed; API generation on the stable
server completed successfully. These are separate from the fixed attention error.

No frontend/serialization code changed in this follow-up; the earlier Legacy
Canvas/Node 2.0 evidence remains the UI evidence. Real 40-block generation,
optimized Torch Compile and multi-GPU remain unverified. DAVE is deferred by
the user's 2026-09-29 decision; existing external behavior is unchanged.

## Earlier implementation evidence (2026-09-15)

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
