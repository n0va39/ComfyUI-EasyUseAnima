# Model-specific AiO generators

- Task: separate Anima, MOSS and Krea2 generator nodes with shared execution
  architecture and explicit model profiles for future DiT families.
- Base: dev `117e589eaeeb3c745fb528b55c9d7d834abdae17`.
- Branch: `codex/moss-aio-support`.
- Scope: AiO model profiles, resource validation, latent and sampler adapters,
  generation settings/schema, related frontend controls, direct tests and docs.
- Preserve: existing node IDs/sockets, old workflows/profiles defaulting to Anima,
  Anima sampling behavior, shared seed/output preferences, external dependency optionality.
- Current revision base: `27c948b`; continue the same owned implementation branch.
- Design: each node class fixes its model family. Profiles own defaults, resource
  identity, latent and sampling contracts. Shared generation/seed/metadata code
  remains common. Top-level settings are authoritative; old `model_settings`
  banks remain inert for data preservation. Explicit family/node mismatches fail
  with a migration instruction rather than silently reinterpreting saved tuning.
- Initial scope: MOSS txt2img with core KSampler. Upstream Spectrum 2.12.1
  uses an incompatible MOSS loader/time-embedding contract and remains gated. Unsupported Anima patches and secondary stages must fail before loading.
  No generic arbitrary plugin imports or changes to the maintained Spectrum source.
- Focused checks: fixed node defaults and mismatch rejection, settings round-trip,
  model identity, latent/sampling contracts, cache and replay identity, all three
  frontend node registrations and both canvas serializers.
- Gates: final full runner; isolated API/GPU; Legacy Canvas and Node 2.0 serialization.
- Stop conditions: official baseline fails, external contract is incompatible,
  or existing Anima behavior changes. Diagnose before expanding support.
- Excluded: release/version publishing, user-instance deployment, Layout editor,
  prompt expansion, and unverified secondary-stage enablement.

## Fixed-node revision validation (2026-10-20)

Candidate `70facce` passes the official full gate: 1,754 Python tests (3 skipped),
all frontend checks, 126 JavaScript files and TypeScript 6.0.3. The existing
Pyright 14-error baseline has no new findings; Ruff remains report-only.
The first run exposed obsolete adapter mocks/export inventory assertions; the
updated focused checks and final full run pass. A separate read-only review of
the backend model/latent/sampling/LoRA/cache/metadata contracts found no defect.

ComfyUI v0.42.1 exposes all three fixed nodes and their correct defaults via
`object_info`. The served frontend profile module matches the source bytes.
Legacy Canvas and Node 2.0 both show the model suffixes and immutable identity,
retain independent settings on save/reload, and disable unreviewed stages for
MOSS/Krea2. Anima steps 37, MOSS steps 29 and seed 43210 remain independent.
Krea2 shift 1.23 survives Legacy save/reload; Node 2.0 main-panel shift 1.17 and
advanced `FLUX shift (mu)` 1.19 save exactly, with Krea2 steps 10. The original
Legacy renderer setting was restored. An old shared-selector MOSS workflow
shows an explicit family/node mismatch message while preserving its settings.

The new MOSS node and its embedded PNG API prompt replay under fresh node IDs
both reproduce the native baseline RGB SHA256
`fe56e30dbdcfa445bfddd7dc8e733fd618c10903c070102fc57a06efc6cde165`.
The replay reruns generation; only the input context is cached.
Legacy v4 Anima input without `model_family` still matches the native reference
at RGB SHA256 `53015c4b2f0008d1a7cc471e6400a11fbf55b005c5d7b58bab7f21db5df7f65e`.

Krea2 uses the [official Turbo template](https://github.com/Comfy-Org/workflow_templates/blob/3e50a92ca02116ee513c3351db7b7c20a928aa53/templates/image_krea2_turbo_t2i_int8.json):
8 steps, Comfy CFG 1, Euler/simple, native FLUX mu 1.15, Qwen3-VL 4B encoder,
Qwen Image VAE. Equal FLUX shift endpoints keep the explicit mu constant at
every resolution. RAW weights require separate tuning; the node does not infer
RAW/Turbo from filenames. The [official inference source](https://github.com/krea-ai/krea-2/tree/db3984fbc6e13b34c0064990fc2d95ac64d00058)
uses a different CFG convention, so its RAW guidance 3.5 corresponds to Comfy
CFG 4.5, and its RAW mu varies with resolution.

The pinned INT8 Turbo and FP8 encoder downloads from
[Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2/tree/1171f4dc7e325bf3734586942e737872506c73e1)
completed with matching sizes and SHA256 hashes. Transfers were sequential with
an aggregate 5,000,000 bytes/s ceiling. The shared Qwen Image VAE also matches
the official size and SHA256.

Krea2 native nodes, the fixed AiO node, and an uncached embedded PNG API prompt
replay all generated the same 1024 x 1024 RGB SHA256:
`47e21a38e4f2a3adc50f95b34fba91199817c2efd86ea39877056e541798de16`.
Seed 246813579 and the Turbo defaults above were used. The AiO input intentionally
omitted `model_family`, steps, CFG and shift: the fixed class inferred Krea2 and
its defaults correctly. Core SaveImage preserved that partial API payload, and
replaying it under new node IDs inferred the same settings and reran generation;
only the input context was cached. Recorded elapsed times were 30.17 seconds
for native nodes, 21.84 seconds for AiO and 20.08 seconds for replay, with
different resource-loading states; these are not comparative benchmarks.
RAW weights, model-specific LoRAs and secondary stages were not GPU-validated.

## Previous shared-selector validation (2026-10-20)

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
   Keep the existing top-level execution snapshot authoritative and legacy banks inert.
3. Add a fixed-family subclass and registration with `AiO Generator (Model)` display
   name, locale names and frontend registry entry. Metadata recognizes profile node IDs.
4. Add focused resource/latent/settings/cache checks and frontend fixed-node/restore
   checks; update the schema and ownership contracts. Verify core-node parity,
   uncached replay and both canvas serializers before enabling the new family.

Resource filenames stay on the shared Input node. Choosing a generator does not
replace resource filenames or download models.

The legacy orchestration size allowance grows by 15 module lines / 8 function lines
for profile imports, validation calls and a latent callback binding. Model policy
lives in its own module; existing stage calls and monkeypatch seams are preserved.
