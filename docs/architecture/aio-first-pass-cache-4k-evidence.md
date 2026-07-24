# AiO first-pass cache 4K/batch allocation and latency evidence

- Owner issue: [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169)
- Roadmap unit: A169-CACHE-06
- PR type: Contract/docs/gate
- Baseline: `dev` commit
  `3f83ca2af96a038b70eb80d4059dcace76372238`
- State: VALIDATED
- Production changes: forbidden

CACHE-06 completes the first-pass cache policy evidence with one explicit,
bounded 4K batch-1 memory/copy/latency profile and a batch-2 admission guard.
It does not start ComfyUI, load Torch/models, or change cache behavior.

## Symbol, caller, alias, and global-state inventory

### Existing benchmark owner

- `tools/benchmark_aio_first_pass_cache.py` imports the canonical cache owner
  and exercises real clear/put/get functions with an in-memory mutable tensor
  stand-in.
- The current schema reports deterministic clone counts/logical bytes,
  elapsed/average nanoseconds, `tracemalloc` peak bytes, and mutation
  isolation.
- Payload is currently symmetric, defaults to 64 KiB per tensor, and is capped
  at 4 MiB per tensor/100 iterations/64 MiB logical copy per operation.
- The harness has no width/height/batch profile and no process RSS/peak working
  set evidence.

### Production and compatibility boundary

- `easyuse_anima.aio.first_pass_cache`, typed stage callers, root aliases,
  metrics, locks, keys, entries, and policy are read-only.
- The harness runs in a separate CLI process for actual 4K evidence. Its test
  contract uses patched small dimensions/caps and does not allocate 4K buffers
  during the full suite.
- No benchmark state is imported by production code or exported through root.

## 4K workload contract

The fixed actual profile models the current decoded image/latent cache shape:

- width/height: `4096 × 4096`;
- batch: `1`;
- decoded image: 3 channels × 4 bytes;
- latent: 4 channels × 4 bytes at 1/8 width and height;
- batch-1 entry: 192 MiB image + 4 MiB latent = 196 MiB;
- batch-2 projection: 392 MiB.

The current 256 MiB single-entry cap must admit batch-1 and reject batch-2.

Safety bounds:

- actual 4K profile iterations default to 3 and may not exceed 3;
- materialized batch-1 entry may not exceed 224 MiB;
- per-operation logical copy may not exceed 768 MiB;
- batch-2 uses a one-byte physical sentinel with declared logical `nbytes` and
  must be rejected before clone;
- focused/full tests patch dimensions and the cap to small values;
- the one actual profile command receives an outer 45-second timeout and is
  never part of ordinary full validation.

## Evidence schema

Schema version 2 adds:

- profile name and asymmetric latent/image byte counts;
- width, height, batch, channel, element-byte, and downscale inputs;
- current RSS and process peak RSS before/after each operation where supported;
- process peak RSS growth alongside existing `tracemalloc` peak;
- batch-2 projected bytes, admission result, clone-zero result, and skip metric;
- existing elapsed/average nanoseconds and deterministic clone/logical-copy
  counters; and
- existing source-after-put and returned-hit mutation isolation.

Latency, traced peak, and RSS values are host/interpreter evidence, not
cross-machine pass/fail thresholds. Deterministic workload math, safety bounds,
clone counts, cap admission, and isolation remain gated.

## Allowed-file boundary

CACHE-06 may change only:

- `tools/benchmark_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_cache_benchmark.py`;
- this document; and
- `docs/architecture/python-backend-execution-roadmap.md`.

Read-only evidence:

- `easyuse_anima/aio/first_pass_cache.py`;
- `easyuse_anima/aio/generation_first_pass.py`;
- `easyuse_anima/aio/legacy_generation.py`;
- root `nodes.py`;
- `tests/test_aio_first_pass_cache.py`;
- `tests/test_aio_first_pass_stage.py`;
- `tests/test_python_backend_analyzer.py`; and
- `tests/fixtures/python_compatibility_surface.v1.json`.

Forbidden:

- any production Python/frontend, cache policy, metrics, key, entry, lock,
  budget, clone, stage, caller, root alias, workflow, or output change;
- Torch/model tensor allocation, ComfyUI server, browser, user instance,
  network, release, or Registry work;
- unbounded CLI dimensions, batch, payload, iterations, or physical allocation;
- committed latency/RSS/peak thresholds or claims that one host predicts every
  production device; and
- CACHE-07 or unrelated optimization.

## Required validation

Focused validation must prove:

- existing bounded profile schema/count/isolation remains valid;
- exact 4K/batch byte math and cap relationship;
- small patched 4K-profile execution matches clone/logical-copy/admission
  contracts without large allocation;
- batch-2 preflight performs zero clone and increments one skip;
- RSS snapshot fields are null or non-negative, with the Windows evidence run
  requiring supported non-null values;
- CLI selection/defaults and invalid profile/iteration bounds;
- production/read-only files remain untouched; and
- analyzer/import-boundary/full gates remain unchanged.

After focused validation, run the actual 4K profile exactly once in a fresh
bounded CLI process, record informational evidence here, then run one official
full validation. Do not start a server, model, or browser.

## Observed 4K evidence

Observed on 2026-07-24 in a fresh Windows Python process using:

```powershell
python -B -X utf8 tools\benchmark_aio_first_pass_cache.py `
  --profile 4k-batch1 --iterations 3
```

The final evidence process completed in 1.1 seconds inside the 45-second outer
limit.

Deterministic workload/admission:

- batch-1 entry: 205,520,896 bytes (196 MiB), below the 268,435,456-byte
  single-entry cap;
- batch-2 projection: 411,041,792 bytes (392 MiB), not admitted;
- batch-2 preflight: 0 detach/clone/cpu calls, 0 logical copied bytes, 1 skip;
- put-overwrite and get-hit: 3 operations, 6 tensor clones, 616,562,688 logical
  copied bytes each; and
- source-after-put and returned-hit mutation isolation: both true.

Informational host/interpreter measurements:

- put-overwrite: 119,923,300 ns total, 39,974,433 ns average,
  411,044,356 traced peak bytes, 411,074,560 process peak-RSS growth, and
  640,028,672 process peak RSS;
- get-hit: 120,983,900 ns total, 40,327,966 ns average,
  205,522,254 traced peak bytes, and 640,045,056 process peak RSS; and
- get-hit peak-RSS growth was only 16,384 bytes because the earlier put phase
  had already established the process high-water mark.

An initial workload run completed before the WinAPI function signatures were
declared, so its RSS fields were null and it was not accepted as final RSS
evidence. The helper was corrected with explicit `restype`/`argtypes`, verified
on a 16-byte bounded profile, and the final evidence above was then collected.
The workload, clone, admission, and isolation results agreed across both runs.

## Validation

- Focused benchmark contract:
  `tests.test_aio_first_pass_cache_benchmark` — 8 tests passed.
- Targeted static checks:
  Ruff passed for the benchmark tool and fatal test rules; both changed Python
  files passed `py_compile`.
- Import boundary:
  6 completed package groups, 0 violations.
- Actual bounded evidence:
  the 4K batch-1 profile above completed once after the WinAPI correction,
  within its 45-second outer limit.
- Official full runner:
  1,128 Python tests and 112 frontend JavaScript checks passed; the Pyright
  ratchet remained at 88 files, 14 errors, and 0 warnings.
- Production boundary:
  no production, analyzer baseline, server, model, browser, workflow, Registry,
  release, or user-instance change was made.
