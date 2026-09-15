# Anima Safe PAG provenance

- Repository: https://github.com/iljung1106/comfyui-anima-safe-pag
- Commit: `905b0107d1f924fc6acbcac3b6a879b566ff671c`
- Source: `__init__.py`, Git blob `b1c7970a7d45407fd9c68b0aed09d9477a232988`
- Source SHA-256 (UTF-8/LF): `e894ce01f7fcebe957eb3e682f959fa7b7826579af4534e001539aacd246bf37`
- License: MIT; the accompanying LICENSE retains the upstream's unnamed
  `Copyright (c) 2026` exactly. Repository author/account: `iljung1106`.
- Derived files: `easyuse_anima/aio/safe_pag.py` and
  `easyuse_anima/nodes/safe_pag_nodes.py`.
- No model weights, adapter or calibration assets are included or required.

Changes: separated the standalone schema and AiO engine; used a unique Easy Anima
node ID; retained numerical PAG/attention/rescale and padded-batch behavior;
restored partial attention setup on all exit paths; deduplicated shared attention
objects and native reapplication; isolated concurrent sibling calls with an owner
token and scoped lock; made prediction state local to an execution context; kept
zero-scale identity and lazy host imports. Existing sampler callbacks remain in
the chain. Temporary instance attributes are removed if absent before inference.

Tests use frozen numerical outputs generated from the source above. The MIT
license and this provenance file ship alongside the implementation.
