# AiO capability adapters

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

## Validation

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
