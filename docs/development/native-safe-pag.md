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
