# AiO Hook API v1 developer guide

AiO Hook is a server-side Python contract for connecting features from another
custom node pack to the explicit `aio_hook` socket on `Anima AiO Generator`.
Version 1 supports replacing the sampling MODEL and selected sampler settings at
`first_pass/before`, plus final postprocess image adjustment, extension metadata,
and optional previews. Conditioning, latent mutation, saving, and sampling
backend replacement are not public hook contracts.

A runnable minimal node pack is available under
[`examples/third_party_aio_hook`](../../examples/third_party_aio_hook/).

## Supported surface

| Item | v1 contract |
| --- | --- |
| Socket type | `EASYUSE_ANIMA_AIO_HOOK` |
| Public import | `easyuse_anima.extensions.aio` |
| Hook points | `first_pass/before`, `postprocess/before`, `postprocess/after` |
| Patch fields | First-pass `MODEL` and sampler settings, same-shape `IMAGE`, JSON-safe metadata |
| Composition | before: A → B, core, after: B → A |
| Failure policy | Invalid contracts and plugin failures fail the generation |
| Cache contract | JSON-safe `fingerprint`; `None` always reports changed |

`AioStage` contains only `FIRST_PASS` and `POSTPROCESS`, which the runtime
actually dispatches. Supported pairs are `first_pass/before` and
`postprocess/before·after`. Declare each pair explicitly with
`AioHookPoint(stage, phase)`.

## Minimal implementation

Import only the public module and output a definition through the custom socket.
ComfyUI does not guarantee sibling node-pack import order, so keep the socket
identifier as a local constant and defer the public Python import until node
execution. This lets the provider register even when it is discovered before
EasyUse Anima.

```python
from functools import lru_cache

HOOK_TYPE = "EASYUSE_ANIMA_AIO_HOOK"


@lru_cache(maxsize=1)
def _definition_type():
    from easyuse_anima.extensions.aio import (
        AioHookDescriptor,
        AioHookPatch,
        AioHookPoint,
        AioHookSessionBase,
        AioStage,
        AioStagePhase,
    )

    class MySession(AioHookSessionBase):
        def after_stage(self, event):
            image = event.state.image.mul(0.9).clamp(0.0, 1.0)
            return AioHookPatch(image=image, metadata={"strength": 0.9})

    class MyDefinition:
        def describe(self):
            return AioHookDescriptor(
                hook_id="my_pack.darkener",
                hook_version="1.0.0",
                points=frozenset({
                    AioHookPoint(AioStage.POSTPROCESS, AioStagePhase.AFTER)
                }),
                fingerprint={"strength": 0.9},
            )

        def create_session(self, context):
            return MySession()

    return MyDefinition


class MyAioHookNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = (HOOK_TYPE,)
    FUNCTION = "build"
    CATEGORY = "My Pack/AiO"

    def build(self):
        return (_definition_type()(),)
```

Register a unique node name in your pack's `NODE_CLASS_MAPPINGS`. See ComfyUI's
official [custom-node lifecycle](https://docs.comfy.org/custom-nodes/backend/lifecycle)
and [server node properties](https://docs.comfy.org/custom-nodes/backend/server_overview).

## Definitions and sessions

A definition is lightweight configuration that may be inspected before a run.

- `describe()` must be side-effect free and stable for the same configuration.
- `create_session(context)` creates state for one Generator execution.
- Acquire run resources in the session, not the definition. Release them with
  `close()` or `context.services.register_cleanup(callback)`.
- Do not assume a session is reused across generation runs.

The Generator validates the complete descriptor chain before opening heavy
model or VAE resources. Sessions are created immediately before first pass and
closed after postprocess, before save output. Sampler, Highres, Detailer, and
postprocess failures still unwind sessions and cleanup callbacks in reverse
order. A partial creation failure also unwinds resources already registered.

## Events and patches

`AioStageEvent` provides immutable views:

- `event.request`: normalized mode, node ID, and generation settings
- `event.state`: current stage model, image, dimensions, core metadata, and extension metadata
- `event.services.emit_preview(stage, image, label=None)`: optional preview
- `event.services.register_cleanup(callback)`: global reverse-registration (LIFO) cleanup

Do not mutate dictionaries in the views or modify the input image in place.
Return a new `AioHookPatch`. A v1 image patch must have the same readable tensor
shape as the previous image; normal ComfyUI `IMAGE` tensors use BHWC layout.

### First-pass MODEL and sampler settings

At `first_pass/before`, pass `event.state.model` through a provider-owned patch
function and return the new MODEL with `AioHookPatch(model=...)`. The same
patch may override only these keys under its `settings["sampler"]` section:

```text
steps, cfg, sampler_name, scheduler, denoise
```

```python
class MySession(AioHookSessionBase):
    def before_stage(self, event):
        # A provider-owned patch function returns a new MODEL.
        model = apply_my_model_patch(event.state.model, strength=0.7)
        return AioHookPatch(
            model=model,
            settings={
                "sampler": {
                    "steps": 24,
                    "cfg": 4.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                }
            },
            metadata={"model_patch": "my_patch_v1"},
        )
```

MODEL and settings patches are accepted only at `first_pass/before`. With a
combined chain, each provider sees the MODEL/settings returned by earlier
providers. A hook-affected first pass bypasses the shared first-pass cache so a
cached latent/image cannot skip the provider's model patch. The returned MODEL
is used for first-pass sampling only; it does not automatically replace the
separate Highres, Detailer, or Upscale stage models.

`backend`, `seed`, nested Spectrum/SPD/DCW options, and arbitrary top-level
sections fail closed. Custom sampler objects or complete sampling backend
replacement require a separate provider contract.

Important: a postprocess image patch changes the Generator's `IMAGE` output
only. The `LATENT` output remains the last latent produced by the core pipeline
and is not re-encoded to match the postprocess hook image. Connect `IMAGE` when
downstream code needs the exact final pixels.

Metadata is stored below
`extensions.hook_data["<hook_id>#<ordinal>"]`. Each patch must provide a
JSON-safe mapping no larger than 64 KiB. Reusing the same top-level metadata key
from the same hook during one run is rejected to expose accidental ordering
dependencies.

## Ordering and composition

`Anima AiO Hook Combine` composes two to four hooks in socket order.

```text
hook_a.before → hook_b.before → core postprocess
              → hook_b.after → hook_a.after
close hook_b → close hook_a
cleanup callbacks → global reverse-registration order (LIFO)
```

This is nested middleware ordering: before callbacks prepare input and after
callbacks wrap the result. For related established designs, see
[pluggy hook wrappers](https://pluggy.readthedocs.io/en/stable/) and Python's
reverse-order [`ExitStack`](https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack).
Session `close()` methods run in reverse provider order. Cleanup callbacks are
not grouped by provider: the most recently registered callback runs first, so a
callback registered during before/after runs before earlier creation callbacks.

## Fingerprints and reproducibility

Include every definition setting that affects output in `fingerprint`. It is
deep-copied when read and used in a deterministic JSON change token independent
of dictionary insertion order. The limit is 16 KiB.

```python
fingerprint={
    "strength": self.strength,
    "preview": self.preview,
    "algorithm": "v1",
}
```

Do not include tensors, models, open files, callbacks, per-run IDs, or other
mutable/non-JSON values. Use `None` if a stable fingerprint is impossible. The
Generator then reports itself changed so an old result is not reused. Hooks
using `first_pass/before` also bypass the shared first-pass cache.

## Error handling

- Descriptor ID, API version, points, and fingerprint are checked before
  session creation.
- Ordinary plugin callback failures become `AioHookExecutionError` with hook
  ID, version, and point context.
- Contract violations raise `AioHookContractError`.
- v1 has no `on_error` callback. Put all release logic in `close()` and
  `register_cleanup()`.
- `KeyboardInterrupt` and `SystemExit` are not wrapped as plugin failures. The
  runtime attempts cleanup, then propagates the original termination signal.
  See Python's official
  [exception hierarchy](https://docs.python.org/3/library/exceptions.html#exception-hierarchy).

AiO Hook is not a sandbox. A provider pack executes in the same Python process
as EasyUse Anima and ComfyUI and can access files, the network, and host state.
Only install and connect providers whose source and code you trust.

## Checklist and troubleshooting

- Confirm `AIO_HOOK_API_VERSION == 1`.
- Defer the public API import until node execution instead of importing it at
  the top level of a sibling node pack.
- Use a stable, namespaced ASCII `hook_id`.
- Keep image operations out-of-place and shape-preserving.
- Return MODEL patches only at `first_pass/before` and avoid mutating the core MODEL in place.
- Keep sampler overrides inside the documented allowlist.
- Include every output-affecting setting in `fingerprint`.
- Export the producer node through `NODE_CLASS_MAPPINGS`, then restart ComfyUI.
- Check Combine socket order when multiple hooks interact.
- For `repeated metadata keys`, return distinct keys from before and after.
- For `must preserve shape`, move resize/crop outside v1 or restore the original
  BHWC shape.

The complete example includes widgets, preview emission, fingerprinting,
metadata, and registration:
[`examples/third_party_aio_hook`](../../examples/third_party_aio_hook/).
