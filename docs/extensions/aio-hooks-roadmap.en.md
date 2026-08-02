# AiO Hook feature roadmap

> Baseline: 2026-08-02
> Tracking issue: [#622](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/622)
> Status: describes the `codex/aio-hook-v1` PR candidate; it is not yet on `dev` or in a public release.

This roadmap separates what the current candidate can do, the evidence required
to promote it as a usable third-party prototype, and later extension candidates.
The supported usage contract remains the [AiO Hook API v1 guide](aio-hooks.en.md)
and `easyuse_anima.extensions.aio`.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| PR candidate | Implemented and tested on the current branch, but not released support |
| Prototype gate | Integration evidence required before merging the current surface |
| Near term | Additive work that can use the existing v1 contract in a separate PR |
| Exploration | Requires direct evidence and a separate contract review |
| Out of scope | Better owned by a distinct provider/API |

## Current PR candidate

| Capability | Contract and example uses |
| --- | --- |
| Explicit connection | Optional Generator `aio_hook` socket only; no discovery or monkeypatching |
| Sibling load order | Providers avoid top-level imports and load the public API when the node executes |
| Postprocess callbacks | `POSTPROCESS / BEFORE` and `POSTPROCESS / AFTER` |
| Image postprocessing | Same-shape `IMAGE` replacement for color, tone, gamma, sharpen, LUT, or watermark operations |
| Extension metadata | JSON-safe values under `extensions.hook_data.<hook_id>#<ordinal>` |
| Preview emission | Send intermediate hook images through the AiO preview transport |
| Per-run sessions | Reusable definitions are separated from mutable queue-run sessions |
| Cleanup | Reverse-order session close and registered cleanup callbacks |
| Composition | Combine two to four providers in socket order |
| Deterministic order | A→B before; B→A after, close, and cleanup |
| Cache change detection | JSON-safe `fingerprint` participates in Generator `IS_CHANGED`; missing fingerprints rerun conservatively |
| Fail closed | Invalid descriptors, patches, shapes, metadata, and provider exceptions stop the run |
| No-hook compatibility | The disconnected output, metadata, and cache-signature path remains unchanged |

An image patch changes the final Generator `IMAGE`, not its `LATENT`. Downstream
nodes that assume pixel-equivalent image and latent values must account for that
difference.

## Prototype promotion gate

- [Done] Confirm the Registry package publishes one public type identity and
  that a provider discovered first can execute through a deferred public import.
- [Done] Compare connected and disconnected provider queues in isolated ComfyUI.
- [Pending] Verify optional-socket workflow round trips and prompt serialization
  in Legacy Canvas and Node 2.0.
- [Done] Read back the result descriptor and hook-data metadata namespaces.
- If package/live work requires a production correction, rerun its focused test
  and one official full validation on the final candidate SHA.

Until these gates pass, v1 is a PR candidate rather than a released SDK.

## Near-term additions

### Impact `DETAILER_HOOK` compatibility

Add a separate optional `detailer_hook: DETAILER_HOOK` socket and preserve exact
object identity through SAM3/Impact detailer calls. Representative uses include
noise/denoise hooks, crop-size alignment, detail previews, custom samplers, and
a common face/eye hook. Impact and AiO hooks retain separate types and lifecycles.

### Save/metadata boundary

Evaluate `SAVE / BEFORE` for metadata addition or validation without replacing
the image tensor. Provenance, pipeline version, and external asset identifiers
fit this boundary; path mutation, arbitrary file I/O, and save-backend replacement
do not.

### Post-detailer and post-upscale image boundaries

Add `DETAILER / AFTER` and `UPSCALE / AFTER` incrementally. Each PR must define
its patch allowlist, disabled-stage behavior, preview order, and cache impact.

## Medium-term exploration

| Candidate stage | Potential uses | Required evidence |
| --- | --- | --- |
| `HIGHRES / BEFORE·AFTER` | Observe or adjust highres inputs/results | Latent identity and cache-mutation isolation |
| `FIRST_PASS / AFTER` | First-pass analysis and cache-hit observers | Canonical cache entry immutability |
| `CONDITIONING / AFTER` | Positive/negative conditioning adapters | Conditioning schema, clone, and metadata contract |
| `RESOURCES / AFTER` | MODEL/CLIP/VAE capability adapters | Clone ownership, patch order, and cleanup owner |

Stages are not added to the public enum before a PR provides real dispatch and
validation for them.

## Better served by separate providers

- Replacing the sampling algorithm or scheduler
- Skipping, reordering, or replacing mandatory stages
- Async/background jobs and external queue orchestration
- New save backends or file routing
- Process-lifetime model/GPU registries
- Workflow-independent global hook discovery

These should become distinct contracts such as `SamplingBackendProvider`,
`StageProvider`, or a save provider when concrete demand exists.

## Persistent v1 non-goals

- Direct access to internal `GenerationState` or `RuntimeServices`
- Arbitrary dictionary mutation or core metadata overwrite
- Hidden resize/crop or tensor-shape changes
- Async hooks, background threads, or process-global callback registries
- Access to another hook's session/state
- Ignoring failures and saving partially processed output as success
- Object `repr`, memory addresses, or pickle hashes as fingerprints

## Promotion order

1. Finish package/live evidence for the postprocess prototype.
2. Review and merge the `codex/aio-hook-v1 -> dev` Draft PR.
3. Implement Impact `DETAILER_HOOK` compatibility independently.
4. Add save/metadata and post-detailer/upscale stages in small PRs.
5. Add cache-sensitive stages only after cache-isolation evidence.
6. Consider v2 or separate providers only after real v1 usage accumulates.

Record implementation, validation, and unverified surfaces in #622 and each PR.
