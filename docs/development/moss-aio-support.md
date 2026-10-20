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

## Validated behavior (2026-10-20)

Environment: ComfyUI v0.42.1 (`63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`),
frontend 1.55.18, Python 3.12.13, PyTorch 2.12.1+cu130, RTX 5070 Ti 16 GB.
All runtime work used the isolated agent test instance.

Model source: [Comfy-Org/MOSS-Image](https://huggingface.co/Comfy-Org/MOSS-Image/tree/3284a1dbb351e3396d70f39f2a71cbf6ed2ef1bb).
The diffusion INT8 ConvRot and Qwen3.5 9B W4A8 GPTQ downloads passed SHA256
verification. The VAE was `flux2-vae_small.safetensors`.

- Native Comfy nodes and AiO both generated 1024 x 1024 with seed 246813579,
  25 steps, CFG 2.5, er_sde/simple, denoise 1 and shift 5. No prompt upsampler,
  SLG, LoRA, Spectrum, or secondary stage was enabled.
- Both RGB hashes were
  `fe56e30dbdcfa445bfddd7dc8e733fd618c10903c070102fc57a06efc6cde165`.
- Re-submitting the API prompt embedded in the AiO PNG under fresh node IDs
  reran the generator and produced the same RGB hash. The input context alone
  was cached; the AiO node and first-pass scope were new.
- A legacy v4 Anima settings payload without model_family generated 512 x 512
  at 4 steps and matched the native Anima graph exactly:
  `53015c4b2f0008d1a7cc471e6400a11fbf55b005c5d7b58bab7f21db5df7f65e`.
- Legacy Canvas: Anima steps 37 -> MOSS default steps 25/CFG 2.5/shift 5 ->
  MOSS steps 29 -> Anima restored steps 37 -> MOSS restored steps 29.
  Seed 43210 stayed shared. Saving and reloading retained the active family
  and both tuning snapshots in generation_settings.
- Nodes 2.0: repeated switching, edited MOSS CFG 3.3, saved and reloaded;
  the active settings and both snapshots survived. Unsupported stages were
  disabled and the sampler dialog exposed only core KSampler with the native
  Spectrum incompatibility explanation. The original Legacy renderer setting
  was restored after testing.

Final official `full` gate passed on code candidate `b481b63`: 1,749 Python
tests (3 skipped), all frontend smoke checks and 126 JavaScript files checked
with TypeScript 6.0.3. Pyright matched its accepted 14-error baseline with no
new findings; Ruff remains report-only under repository policy (25 findings).
Later changes to this document do not alter that code evidence.

These are targeted compatibility/replay checks, not performance benchmarks or
quality evaluations. No release, user-instance sync or model publication was made.

## Spectrum boundary

Upstream [Spectrum 2.12.1 moss.py](https://github.com/sorryhyun/ComfyUI-Spectrum-KSampler/blob/1baeab6f9ee94a75011353c6ef41963888cc8979/moss.py)
registers a separate `MossSpectrumKSampler`. Its custom forward expects `freq_dim`
and its SD3 patch uses a different timestep multiplier from native Comfy MOSS.
[Native MOSS implementation](https://github.com/Comfy-Org/ComfyUI/blob/v0.42.1/comfy/ldm/moss_image/model.py)
uses its own timestep embedding contract. Reusing the Anima Advanced/SPD path or
adding a missing attribute would not establish numerical compatibility.

Native MOSS Spectrum integration therefore remains unsupported. It requires a
separate adapter and native-baseline numerical/lifecycle validation. AiO fails
before resource loading when an unsupported backend or patch is requested.

## Adding another DiT family

1. Add the reviewed resource, latent-layout and backend contract to
   `aio/model_profiles.py`, with explicit family defaults and validation.
   Do not infer capabilities from a filename or enable Anima-specific patches.
2. Add the same family/defaults to `web/js/aio/model_profiles.js` and
   `web/js/aio/settings.js`, its schema enum, and capability-specific controls.
   Keep the existing top-level execution snapshot authoritative; inactive banks
   must remain inert until an explicit UI switch.
3. Add focused resource/latent/settings/cache checks and frontend switch/restore
   checks; update the schema and ownership contracts. Verify core-node parity,
   uncached replay and both canvas serializers before enabling the new family.

Resource filenames stay on the Input node. Family switching changes tuning,
not model filenames, seed, output path or common preview/postprocess preferences.

The legacy orchestration size allowance grows by 15 module lines / 8 function lines
for profile imports, validation calls and a latent callback binding. Model policy
lives in its own module; existing stage calls and monkeypatch seams are preserved.
