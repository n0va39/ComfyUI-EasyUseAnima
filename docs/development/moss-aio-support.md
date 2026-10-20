# Model-specific AiO generators

## Compatible extras revision

- Base: `7a9fc36`, continuing the same owned branch and worktree.
- Goal: enable reviewed model-independent AiO stages and optional acceleration
  for MOSS/Krea2 using explicit per-feature capabilities.
- Allowed files: AiO profiles/validation/stage adapters, related frontend
  controls/locales, focused tests and this guide.
- Preserve: Anima behavior, fixed model node identities, saved explicit settings,
  optional dependency loading, scoped patch cleanup and replay metadata.
- Mod Guidance remains disabled for new families until upstream supplies matching
  trained support. Spectrum acceleration requires a compatible upstream patch;
  do not substitute an Anima forward or modify the external node pack.
- Checks: nested capability rejection, stage/default contracts, GPU generation
  and uncached replay, both canvas serializers, final repository full gate.
- Completion: every enabled feature has direct contract evidence and appropriate
  validation; explain incompatible or unavailable dependency boundaries.
- Stop: native baseline regression, incompatible external contract, or shared
  model mutation that cannot be scoped and restored.

### Reviewed capability boundary

Both native families use the shared Highres, SAM3/Impact Detailer and USDU/
ResShift stages. These pass model-owned conditioning and VAE latents through
Comfy sampling instead of assuming an Anima latent channel count. Impact's
image detailer explicitly handles Wan-style 5D VAE output. KJ attention supports
MOSS BND and Krea2 HND/GQA inputs; its compile block selection recognizes
MOSS `layers` and Krea2 `blocks`, but GPU validation restricts TorchCompile to
Krea2 because MOSS's native kernels do not currently compile. Artist Mix works on generic conditioning
dimensions, and the hook protocol cannot change the model family or backend.
The Anima IP-Adapter hook now checks the actual model family before patching.

MOSS NegPip uses the optional [ComfyUI-ppm native adapter](https://github.com/pamparamm/ComfyUI-ppm/blob/bf69c9f9f8746d48cc0703a73bd7a2256b6c47fd/src/negpip/moss_negpip.py).
Both returned MODEL and CLIP must carry upstream's successful-application
marker. Older silent no-op versions are rejected. Krea2 has no reviewed PPM
encoder/model dispatch and remains blocked.

Anima DAVE/Safe PAG and trained Mod Guidance remain gated. Native MOSS has
`layers` rather than the Anima DAVE block contract; Krea2's joint text/image
tokens and the Anima DAVE mask need a separate numerical review. Neither
architecture provides Safe PAG's Anima `self_attn.compute_attention` contract.

Spectrum upstream remains at `1baeab6f` (2.12.1). Its
[generic patch](https://github.com/sorryhyun/ComfyUI-Spectrum-KSampler/blob/1baeab6f9ee94a75011353c6ef41963888cc8979/spectrum.py#L1008)
requires Anima head components (`final_layer`, `t_embedder`,
`t_embedding_norm`, `unpatchify`) absent from native Krea2/MOSS. The MOSS-specific
patch also misses native fused-head captures and uses a different timestep
multiplier. Acceleration and DiT corrections are rejected at every active
sampling stage, not just first pass. Turbo's 8 steps also offer no forecast
steps with upstream's default warmup 6 plus actual tail 3. No external Spectrum
source was modified or approximation silently substituted.

### Compatible extras validation (2026-10-20)

The final code passes `check_custom_node.ps1 -Profile full`: 1,761 Python tests
(3 skipped), all frontend checks across 126 JavaScript files, and TypeScript
6.0.3. Pyright retains its accepted 14-error baseline, with no new findings;
Ruff remains report-only. The initial snapshot failure was resolved by updating
only the two new nodes' default contracts; the Anima snapshot is unchanged.
A separate read-only integration review found no actionable defect.

GPU checks use isolated ComfyUI v0.42.1, frontend 1.55.18, PyTorch 2.12.1+cu130
and an RTX 5070 Ti. Native MOSS SFT and Krea2 Turbo int8 weights are exercised:

- Both models complete Highres (1024 to 1152), SAM3 detection and Impact crop
  sampling, USDU (to 1440), and the shipped generic brightness hook.
  Logs confirm actual detected-region sampling and nine USDU tiles.
- Both saved PNG prompts execute again with new node IDs. The generator is
  absent from the cached-node list; final RGB hashes match the original run:
  MOSS `1f17ca26b8ff7d50d69346462a9a7b95f2afe02524b61148b887e52847102079`,
  Krea2 `64d5fc3b8e65f1c76fef5d3793b1e957b0c39dae882319a64e29abf42c109051`.
- Both models complete SageAttention auto plus FP16 accumulation, and Artist
  Mix average with two artist entries. MOSS also completes native PPM NegPip
  with a negative-weight token.
- Krea2 completes ResShift x2 to 2048 pixels. Its first attempt correctly
  rejected absent local weights; copying the existing shared weights into the
  test inventory resolves the environment issue without a download.
- Krea2 completes a two-step TorchCompile/Inductor smoke. MOSS with the default
  Comfy Kitchen attention fails in Dynamo's FakeTensor/DLPack boundary; this is
  an upstream attention/compiler combination, not a sampling-family mismatch.
  Selecting KJ SageAttention gets past attention but fails on the fused
  quantized `linear_input_act` kernel for the same FakeTensor boundary.
  MOSS TorchCompile is therefore disabled in both the profile validator and
  UI; its SageAttention and FP16 accumulation options remain available.

Legacy Canvas and Node 2.0 both expose compatible controls and lock unsupported
ones. UI save/reload preserves Krea2 Highres scale 1.125/4 steps and FP16
accumulation. A new custom Krea2 detailer block starts at 8 steps, CFG 1,
Euler/Simple with Spectrum disabled. Node 2.0 saves and reloads MOSS NegPip On.
Existing explicitly saved stage values remain intact. The test canvas setting
is restored to Legacy after validation.
The saved Krea2 UI settings also execute through the API and produce the
expected 1152-pixel Highres output. After all patch attempts, uncached ordinary
generation again matches the earlier native baseline RGB hashes for both
families, confirming that optional patches did not leak into the next run.

These checks establish execution, serialization and replay compatibility, not
image quality, acceleration benchmarks, all optional combinations, or Krea2
RAW-weight validation. Mod Guidance, Spectrum/SPD, DiT corrections, Anima DAVE,
Safe PAG and Anima IP-Adapter remain unavailable for the native new families.

## Initial fixed-node contract

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
