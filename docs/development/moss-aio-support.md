# AiO model-family settings and MOSS

- Task: user-requested MOSS support with separate settings for future DiT families.
- Base: dev `117e589eaeeb3c745fb528b55c9d7d834abdae17`.
- Branch: `codex/moss-aio-support`.
- Scope: AiO model profiles, resource validation, latent and sampler adapters,
  generation settings/schema, related frontend controls, direct tests and docs.
- Preserve: existing node IDs/sockets, old workflows/profiles defaulting to Anima,
  Anima sampling behavior, shared seed/output preferences, external dependency optionality.
- Design: top-level settings are the active execution snapshot; `model_family`
  selects a reviewed profile and `model_settings` stores inactive tuning snapshots.
  Switching families saves/restores tuning without restoring an old seed/output path.
- Initial scope: MOSS txt2img with core KSampler. Upstream Spectrum 2.12.1
  uses an incompatible MOSS loader/time-embedding contract and remains gated. Unsupported Anima patches and secondary stages must fail before loading.
  No generic arbitrary plugin imports or changes to the maintained Spectrum source.
- Focused checks: settings migration/round-trip, model identity and option validation,
  latent dimensions, sampler arguments, cache identity, frontend family switching.
- Gates: final full runner; isolated API/GPU; Legacy Canvas and Node 2.0 serialization.
- Stop conditions: official baseline fails, external contract is incompatible,
  or existing Anima behavior changes. Diagnose before expanding support.
- Excluded: release/version publishing, user-instance deployment, Layout editor,
  prompt expansion, and unverified secondary-stage enablement.

Validation evidence and confirmed support limits will be recorded below.

The legacy orchestration size allowance grows by 15 module lines / 8 function lines
for profile imports, validation calls and a latent callback binding. Model policy
lives in its own module; existing stage calls and monkeypatch seams are preserved.
