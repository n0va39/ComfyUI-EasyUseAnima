# FC-02B AiO Adapter Back-reference Contract

## Scope and verdict

FC-02B is a production-free Contract based on
`dev@9ed21c2aa58cf61ea37b04ec1bedb5084a5b8ca4`. It fixes the owner and
behavior boundary for the two reusable operations that currently make
`easyuse_anima.aio.legacy_generation` instantiate Comfy node adapters.

The verdict is **MOVE FEASIBLE**. FC-02C can remove both feature-to-node
back-references without a Behavior Contract because the reusable work has no
node-instance state and the existing direct tests already own its option
normalization, host lookup timing, keyword order, short circuits, results,
errors, and AiO cleanup order.

FC-02B does not authorize production, test, tool, fixture, schema, public export,
root compatibility, lifecycle, or feature-behavior changes.

## Current violation and retained adapters

The current violations are exactly:

- `_run_aio_highres_stage()` instantiates
  `EasyUseAnimaImageScaleByMultiple` to resize an image; and
- `_run_aio_detailer_target()` instantiates `EasyUseAnimaSAM3Detailer` to run
  SAM3 detection, MaskToSEGS conversion, and Impact detailing.

`EasyUseAnimaImageScaleByMultiple`, `_EasyUseAnimaImpactDetailerDelegate`, and
`EasyUseAnimaSAM3Detailer` remain Comfy node adapters. They retain their exact
class identities, metadata, `INPUT_TYPES`, function names, Python signatures,
defaults, result shapes, registration identities, and root aliases. Their
method bodies delegate to private feature operations. Feature code never
imports or instantiates these node classes after FC-02C.

## Scaling operation

`easyuse_anima.image.upscale._upscale_image_by_multiple` is the single shared
scaling operation. It has the exact callable boundary:

```python
def _upscale_image_by_multiple(
    image,
    scale_by=1.5,
    upscale_method="bicubic",
    multiple="32",
    max_long_edge=0,
): ...
```

The operation preserves this order:

1. normalize `upscale_method`, `multiple`, and `max_long_edge` with
   `_normalize_image_scale_options`;
2. convert NHWC to NCHW with `image.movedim(-1, 1)`;
3. derive width, height, and applied scale from the exact tensor shape and
   `_image_scale_by_multiple_size`;
4. call `_common_upscale_image(samples, width, height, str(upscale_method))`;
5. convert the result back to NHWC; and
6. return `(image, width, height, applied_scale)` with the existing objects and
   numeric values.

The image node calls this operation with its unchanged method arguments. The
AiO highres stage calls the same operation at the current point: after stage
sampler planning and before VAE encoding or ephemeral model creation. A scaling
failure therefore still propagates before the sampling cleanup boundary exists.

The new module is private, import-pure, has `__all__ = ()`, and creates no host,
runtime, cache, lock, registration, or lifecycle state.

## SAM3 and Impact execution operations

`easyuse_anima.image.sam3_detailer` owns two private functions:

- `_run_sam3_detailer`, the shared SAM3 operation called by the SAM3 node
  adapter and AiO; and
- `_run_impact_detailer`, the nested Impact operation called by the Impact node
  adapter and `_run_sam3_detailer`.

Both functions use the same required argument order and optional defaults as
their current node `doit` methods. `_run_impact_detailer` begins with `image,
segs, model, clip, vae, guide_size, guide_size_for, max_size, seed, steps, cfg,
sampler_name, scheduler, positive, negative, denoise, feather, noise_mask,
force_inpaint, wildcard`, followed by `cycle=1`, `alignment="impact"`,
`preserve_conditioning_metadata=True`, `fail_on_unsupported_opt=False`,
`detailer_hook=None`, `inpaint_model=False`, `noise_mask_feather=0`,
`scheduler_func_opt=None`, `tiled_encode=False`, and `tiled_decode=False`.

`_run_sam3_detailer` prepends the current SAM3 arguments `enabled, image,
ctx_SAM3, detect_prompt, detect_count, threshold, refine_iterations,
individual_masks, combined, crop_factor, bbox_fill, drop_size, contour_fill` to
the Impact execution arguments and retains the same optional defaults.

### SAM3 order

`_run_sam3_detailer` preserves the current execution order exactly:

1. create the empty mask and empty SEGS for the input image;
2. normalize `enabled`; when disabled, return
   `(image, empty_segs, empty_mask, image)`;
3. resolve `model` then `clip` from `ctx_SAM3` and raise the existing missing
   context error when either is absent;
4. format the detection prompt and encode it with the SAM3 CLIP;
5. resolve `SAM3_Detect` at call time, call `execute` with the current ordered
   keywords, normalize its output tuple, and preserve the no-mask error;
6. resolve `MaskToSEGS` at call time, call `doit` with the current positional
   arguments, normalize its output tuple, and preserve the no-SEGS error;
7. test SEGS contents; when empty, emit the current info log and return the
   original image, SEGS, mask, and original image;
8. call `_run_impact_detailer` with the existing ordered keyword set, take its
   first result, and return `(detailed_image, segs, mask, image)`.

Creating empty outputs before the enabled short circuit is intentional current
behavior and is not reordered by the Move.

### Impact order

`_run_impact_detailer` preserves the current execution order exactly:

1. normalize the alignment text and value;
2. emit the existing warning when conditioning metadata preservation is false;
3. wrap the supplied detailer hook only when alignment requires it;
4. resolve `DetailerForEach` at call time and instantiate that host class;
5. call `_call_impact_detailer` with the current keyword insertion order, which
   retains all keywords for `**kwargs` methods and otherwise filters them by the
   live method signature; and
6. normalize dict, tuple, and scalar results exactly, including the existing
   empty-tuple error and one-element image tuple.

`fail_on_unsupported_opt` remains accepted but otherwise unused, matching the
current adapter. No new warning, fallback, provider cache, or capability lookup
is added.

## Host lookup, imports, and patch targets

SAM3, MaskToSEGS, and DetailerForEach discovery remains lazy and call-time. The
new operation module imports only canonical feature, common, and infrastructure
helpers. It does not import a node adapter, root module, registration,
bootstrap, runtime, or the complete RuntimeServices object.

The existing low-level discovery and signature-adaptation helpers remain in
`easyuse_anima.image.sam3`; FC-02C does not move or cache provider resolution.
Direct tests patch the canonical operation owner after the Move. Existing
private patch names on node or AiO modules are test implementation details, not
additional compatibility surfaces. Public/root node class identities remain the
same objects.

## AiO cleanup and result boundary

AiO retains all request parsing and stage orchestration. It computes every
target default in the current order, creates the ephemeral stage model, calls
`_run_sam3_detailer` inside the existing `try`, and calls
`_cleanup_aio_ephemeral_model(stage_model, model)` in the existing `finally`.

Consequently:

- planner failure still occurs before ephemeral cleanup is established;
- operation lookup or execution failure still triggers cleanup;
- cleanup failure still has the current Python `finally` precedence;
- SEGS inspection and JSON-safe sampler metadata still occur only after cleanup;
- metadata key order remains `enabled`, `detected`, `sampler`; and
- the detailed image remains result item 0 and SEGS remains result item 1.

The Move does not absorb AiO planning, model patching/cleanup, target parsing,
metadata, callbacks, or stage chaining into the image operation owners.

## FC-02C implementation and rollback boundary

FC-02C is one cohesive Move and one rollback unit:

1. add the two private, import-pure operation modules;
2. delegate the three node methods without changing their host-facing surfaces;
3. replace the two AiO node imports/calls with the exact shared operations;
4. move direct private patch targets to their canonical owners; and
5. update only the analyzer/package fixtures required by the actual module and
   edge changes.

Rollback reverts the complete FC-02C commit/PR. There is no schema, persistence,
workflow, settings, API, lifecycle, or data migration to roll back separately.

Stop FC-02C if preserving any call-time host lookup, ordered keyword/default,
disabled/empty result, warning/error, AiO cleanup/metadata order, node signature
or identity, private export status, or allowed import direction requires a
behavior change. Such evidence requires a separate Behavior Contract rather
than widening this Move.

## Evidence and validation

The deterministic owners are `tests/test_image_scale.py`,
`tests/test_sam3_nodes.py`, `tests/test_aio_legacy_generation.py`, the direct
node identity/schema tests, analyzer/import-boundary tests, and package/no-host
tests. FC-02B changes no executable evidence because those owners already cover
the fixed contract. Its validation is targeted document/source/test
consistency plus `git diff --check`; official full, package, and live validation
belong to FC-02C as stated in the roadmap.
