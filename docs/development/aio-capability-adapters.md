# AiO capability adapters

## Public Spectrum model-patch contract, 2026-10-25

Base: `387868b`. Canonical `SpectrumMossModelPatch` and `SpectrumKrea2ModelPatch`
providers no longer need `SPECTRUM_CAPABILITIES` or custom model-input metadata.
AiO validates their public `INPUT_TYPES`, MODEL output, `FUNCTION = patch` and
explicit callable arguments. Its reviewed mapping enables sampler, Highres,
Detailer and Upscale. The public `steps` argument remains compatible, while
Spectrum derives forecast scheduling from each actual sampler invocation.

When beta/fork providers still expose class or model-input capability metadata,
AiO validates those declarations and intersects their stages with its reviewed
mapping. The old `Native*` IDs remain downstream fallbacks only when the
canonical node is absent, and still require their legacy class marker. A broken
canonical node never falls through to an older ID. Public reason codes and the
AiO-owned `aio_capability_manifest` remain unchanged; runtime metadata is still
excluded from saved settings. No model defaults or sampling math change here.

Validation: the full gate passes on ComfyUI v0.42.1 (1,797 Python tests,
three conditional skips, 127 JavaScript files and TypeScript 6.0.3).
Fresh registration exposes both canonical providers and all four AiO stages
without Spectrum metadata or the removed aliases. Public AiO checkpoint runs
at 512x512 complete for MOSS SFT INT8 with uncond SLG (16 actual / 8 forecast)
and Krea2 Turbo INT8 (6 actual / 2 forecast), both with zero fallbacks and finite
saved latents. The MOSS fixed-seed RGB output matches the pre-review run exactly.
These focused runs use compilation off; previous compile/secondary-stage
evidence is reused for unchanged execution paths. No frontend DOM or saved
settings shape changed, so the earlier two-canvas browser evidence is reused.

## Completion follow-up, 2026-10-21

The implementation at `18c3f44` remains the model/GPU baseline. This follow-up
corrects a stale sampler compatibility-policy tooltip after asynchronous
provider discovery and updates the Korean/English user guides to describe
native MOSS forecasting in all four stages. Node IDs, v5 settings, model
defaults and numerical execution are unchanged. The license transition is an
independent commit with its scope and retained MIT material recorded in NOTICE.

Live verification now passes in the in-app browser on ComfyUI v0.42.1
(`63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`), frontend 1.55.18.
Chrome returned HTTP 403 while direct HTTP and the in-app browser worked.
The older browser-blocked results below describe the earlier attempts only.

- Legacy Canvas: MOSS first-pass, Highres, Face Detailer and USDU forecast
  controls were enabled, applied and saved; unsupported corrections remained
  disabled. First-pass warmup 3 and tail 2 survived a reload. The updated
  compatibility-policy tooltip displayed the supported policy explanation.
- Nodes 2.0: the same saved workflow restored all four forecast toggles and
  warmup/tail values. Each stage dialog could apply its settings. Disk read-back
  after saving matched all Anima, MOSS and Krea2 generator settings exactly.
- Returning to Legacy and reloading retained the saved Highres forecast toggle.
  The original Nodes 2.0 setting (off) was restored. No user-instance changes.
- The HTTP-served sampler module matched the final source. Live object-info
  advertised sampler/highres/detailer/upscale for the compatible native adapter.
  No new console error was observed during the tested interactions; startup
  Vite preload and core assets.seed message errors were present before testing.

The new tooltip regression smoke passed. Earlier GPU/CPU numerical evidence
below remains applicable because this follow-up changes no sampling code.
Final validation of code candidate `baf6f67` passed all 1,769 Python tests
(three skips), architecture gates and frontend checks for 126 JavaScript files
with TypeScript 6.0.3. The only initial failure was the `.comfyignore` comment's
recorded hash; the official analyzer regenerated that single hash and its
focused test passed before the final full run. Existing report-only Ruff and
Pyright baseline findings remain unchanged.
Comfy CLI 1.20.0 validation and packing passed. The 368-file archive includes
LICENSE, LICENSE-MIT, NOTICE and both Safe PAG notices, with contents matching
the source. No Registry publication or package installation was performed.
The native Spectrum adapter remains a separate local dependency at `bed5a53`;
Krea2 acceleration and MOSS Mod Guidance/SPD are still unsupported. Public
merge/release and user-instance deployment are separate from this local work.

## Follow-up: all MOSS sampling stages

Bases: AiO `0eaf778`, native Spectrum adapter `3cfbd05`.
Extend native MOSS forecasting to Highres, every Detailer block and USDU
sampling, including repeated crop/tile calls. Keep model defaults, saved v5
settings, Anima behavior and unsupported guidance/correction features unchanged.
Owned changes are capability policy, stage optimization UI, adapter lifecycle
and their focused tests. Old first-pass-only provider contracts retain only
their advertised support. Require per-sampling cache isolation, partial-denoise
and short-schedule tests, the full gate, and isolated GPU stage execution.
No public PR, release or user-instance deployment. A lifecycle/numerical
regression blocks completion until resolved.

The provider's advertised stages are intersected with the four implemented AiO
stages. The shared stage editor now evaluates forecasting and DiT corrections
independently and uses the native MOSS dependency for forecasting. Advanced/SPD
sampler backends remain separately restricted to their implemented Anima path.
Missing/older providers preserve saved controls without enabling unadvertised
stages. The v5 settings schema and all model defaults are unchanged.

The Spectrum adapter now owns forecast state per Comfy `OUTER_SAMPLE`
invocation and releases it in `finally`. It uses the actual sigma schedule
length, not the nominal scheduler construction length. Detailer cycles and USDU
tiles therefore each start with fresh predictors, including identical sigma
schedules and a subsequent crop starting at a lower sigma. Unsupported direct
model-forward calls run actual forwards instead of guessing a sampling boundary.

Focused capability tests, stage/detailer/sampler frontend smokes, and the
Spectrum CPU suite (26 tests) passed. The final full gate, including the
Anima-backend isolation fix, passed 1,769 Python tests with three skips,
architecture gates and frontend checks covering 126 JavaScript files
(TypeScript 6.0.3). ComfyUI v0.42.1 / frontend 1.55.18 were used. Existing
report-only Ruff findings and the Pyright baseline were unchanged.

Five isolated RTX 5070 Ti runs completed the full pipeline: disabled Spectrum,
enabled-but-all-actual, forecast, repeat, and forecast with explicit logger
level to expose USDU's normally suppressed sampling logs. Native int8 convrot
MOSS, Qwen3.5-9B w4a8 and FLUX.2 small VAE were used with seed 246813579,
CFG 2.5, ER-SDE/Simple and shift 5. The pipeline generated 1024x1024, Highres
1152x1152, a detected teapot Detailer crop (two forced cycles), and USDU
1440x1440 with nine 704x704 tiles.

| Sampling stage | Invocations | Steps per invocation | Actual / forecast |
| --- | ---: | ---: | ---: |
| First pass | 1 | 25 | 13 / 12 |
| Highres, denoise 0.3 | 1 | 10 | 7 / 3 |
| Detailer, denoise 0.3 | 2 | 9 | 7 / 2 |
| USDU tile, denoise 0.2 | 9 | 8 | 6 / 2 |

Every invocation restarted at step one, used actual forwards for its first
three and final two steps, and used forecasts without cache vetoes.
Disabled/all-actual RGB hashes match exactly:
`8b5970f4e5b200cf66cb2f1baddbd929aa9140276d9d3b2184f68295e7031c08`.
Forecast/repeat/explicit-logging hashes match exactly:
`d14f0b279aa947bcc9c9b7287d6478f4bd9c144a25de5cd6fd393ddc6de47927`.
These checks establish execution and repeatability for this fixture, not a
representative speed or quality benchmark.

The three changed UI owners matched the isolated instance's HTTP-served bytes.
New live Legacy Canvas/Node 2.0 checks remain blocked by the previously observed
browser access failure described below. Automated smokes passed; no new live
UI verification is claimed. The test-only log probe and owned server were
removed/stopped after validation. The user instance was not modified.

## Initial patch

Base: dev `1c3c4e96996d126b6bbd1b643cdb298b6d4cf2de`.
Owned branch: `codex/aio-capability-adapters`.

Goal: preserve native model loading and saved workflows while separating model
defaults from feature/provider compatibility. Add a versioned, stage-aware
capability result shared with the frontend. Native MOSS Spectrum forecasting
uses a separately installed compatible Spectrum adapter, initially first pass
only. Krea2 acceleration and trained guidance remain unsupported.

Allowed: capability owner, model validation and forecast dispatch, generator
capability metadata, frontend dependency/profile/sampler controls, focused tests
and corresponding architecture fixtures. Spectrum implementation belongs to a
separate worktree based on upstream `1baeab6f`; no vendored Spectrum kernels.

Preserve: public node IDs/sockets, generation settings v5, explicit inactive
settings, Anima execution behavior, external optional dependencies, user instance.
Provider package version alone never enables an unimplemented adapter contract.
Unknown contract versions or missing required controls fail closed.

Checks: model/settings/provider contract tests, first-pass routing, frontend
missing/compatible/incompatible dependency behavior, required full gate,
native MOSS cache-off equivalence and actual forecast execution, isolated
Legacy Canvas/Nodes 2.0 saved-setting behavior.

Completion: reviewed local patches and focused/full/runtime evidence.
No PR, release or user-instance installation in this task. Stop for a real
numerical/lifecycle regression or failed required environment gate.

## Extension rules

`model_profiles.py` owns resource choices, defaults and sampler backends.
`capabilities.py` owns feature policy and reviewed external adapter contracts.
Generator object-info publishes that policy as runtime metadata; it is not
written into generation settings or workflow widgets.

Each feature reports support, availability status, stages, provider, adapter
and a reason code. Availability is refreshed from the installed provider.
Missing or incompatible providers do not erase saved controls. An explicitly
enabled unsupported feature fails validation before resource loading.

For another model, add its fixed generator/profile and reviewed feature policy.
For another provider integration, add an explicit resolver and dispatch path;
do not infer support from a package version or a similar class name. A provider
may advertise additional features or stages, but AiO enables them only after
its own adapter and stage lifecycle are implemented and tested.

Contract version 1 requires the native MOSS MODEL input/output and explicit
patch arguments. Breaking semantics require a new contract version and an
explicit adapter or migration. Additional optional controls can be introduced
without changing existing saved settings. Forecast acceleration, trained
guidance and SPD are separate integrations; enabling one never enables another.

## Initial-patch validation

The required `full` gate passed on ComfyUI v0.42.1
(`63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`), frontend 1.55.18:
1,767 Python tests, three skips, all architecture gates and frontend checks
covering 126 JavaScript files. Existing report-only Ruff findings and the
Pyright diagnostic baseline remain; this is not a claim of a warning-free tree.

Focused coverage includes provider absence, incompatible contracts and
signatures, dynamic availability, stage policy, model dispatch, preservation of
inactive values, and runtime metadata exclusion from saved defaults. Frontend
tests cover pending-to-available refresh, availability loss, disabled controls,
and unsupported stage/backend setting preservation.

All four changed frontend owner files matched source, installed copy and the
HTTP-served bytes in the isolated test instance. Live Legacy Canvas/Node 2.0
checks could not start: the available Chrome surface blocked localhost with
`ERR_BLOCKED_BY_CLIENT`, and the in-app browser was unavailable. No locale or
canvas setting was changed. New live UI language/save/reload verification
remains outstanding; automated smokes do not replace it.

Seven native MOSS GPU executions passed on RTX 5070 Ti, using the int8
convrot model, Qwen3.5-9B w4a8 encoder and FLUX.2 small VAE. Settings:
1024x1024, seed 246813579, 25 steps, CFG 2.5, ER-SDE/Simple, shift 5.

- Disabled Spectrum, enabled-but-all-actual, and disabled-again outputs share
  RGB SHA256 `fe56e30dbdcfa445bfddd7dc8e733fd618c10903c070102fc57a06efc6cde165`.
- Forecast and repeat share
  `6fe4df2b3ef953adcabfe9d70da70bd41cdb9fd80d37deed72368637b89d96d3`.
  Logs record 15 actual and 10 cached steps, with no cache vetoes.
- A changed prompt produces the requested different subject.
- Forecast first pass followed by ordinary four-step highres completes at
  1152x1152. Spectrum logs remain limited to the first 25-step pass.

These are correctness and repeatability checks, not a representative speed or
quality benchmark. Native head parity, shared-base isolation and exception
cleanup are additionally covered by the Spectrum CPU suite (22 tests).
The user instance was not modified. MOSS acceleration requires the separate
local Spectrum patch; it is not claimed available in the public upstream release.
