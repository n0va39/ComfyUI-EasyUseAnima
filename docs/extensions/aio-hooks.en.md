# AiO Hook API v1 developer guide

AiO Hook is a server-side Python contract for connecting features from another
custom node pack to the explicit `aio_hook` socket on `Anima AiO Generator`.
Version 1 only supports final postprocess image adjustment, extension metadata,
and optional previews. Model loading, conditioning, sampling, latent mutation,
and saving are not public hook contracts.

A runnable minimal node pack is available under
[`examples/third_party_aio_hook`](../../examples/third_party_aio_hook/).

## Supported surface

| Item | v1 contract |
| --- | --- |
| Socket type | `EASYUSE_ANIMA_AIO_HOOK` |
| Public import | `easyuse_anima.extensions.aio` |
| Hook points | `postprocess/before`, `postprocess/after` |
| Patch fields | Same-shape `IMAGE`, JSON-safe metadata |
| Composition | before: A → B, core, after: B → A |
| Failure policy | Invalid contracts and plugin failures fail the generation |
| Cache contract | JSON-safe `fingerprint`; `None` always reports changed |

`AioStage` only contains the stage that v1 actually dispatches. Declare each
supported pair with `AioHookPoint(stage, phase)`; stages and phases are not
combined as a Cartesian product.

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
- `create_session(context)` creates state for one postprocess execution.
- Acquire run resources in the session, not the definition. Release them with
  `close()` or `context.services.register_cleanup(callback)`.
- Do not assume a session is reused across generation runs.

The Generator validates the complete descriptor chain before opening heavy
model or VAE resources. Sessions are created immediately before postprocess and
closed before save output. Earlier sampler, Highres, or Detailer failures never
create a session. A partial creation failure still unwinds registered cleanup
callbacks and already-created sessions in reverse order.

## Events and patches

`AioStageEvent` provides immutable views:

- `event.request`: normalized mode, node ID, and generation settings
- `event.state`: current image, dimensions, core metadata, and extension metadata
- `event.services.emit_preview(stage, image, label=None)`: optional preview
- `event.services.register_cleanup(callback)`: reverse-order run cleanup

Do not mutate dictionaries in the views or modify the input image in place.
Return a new `AioHookPatch`. A v1 image patch must have the same readable tensor
shape as the previous image; normal ComfyUI `IMAGE` tensors use BHWC layout.

Important: a hook changes the Generator's `IMAGE` output only. The `LATENT`
output remains the last latent produced by the core pipeline and is not
re-encoded to match the hook image. Connect `IMAGE` when downstream code needs
the exact final pixels.

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
close hook_b → close hook_a → cleanup hook_b → cleanup hook_a
```

This is nested middleware ordering: before callbacks prepare input and after
callbacks wrap the result. For related established designs, see
[pluggy hook wrappers](https://pluggy.readthedocs.io/en/stable/) and Python's
reverse-order [`ExitStack`](https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack).

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
Generator then reports itself changed so an old result is not reused.

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

## Checklist and troubleshooting

- Confirm `AIO_HOOK_API_VERSION == 1`.
- Defer the public API import until node execution instead of importing it at
  the top level of a sibling node pack.
- Use a stable, namespaced ASCII `hook_id`.
- Keep image operations out-of-place and shape-preserving.
- Include every output-affecting setting in `fingerprint`.
- Export the producer node through `NODE_CLASS_MAPPINGS`, then restart ComfyUI.
- Check Combine socket order when multiple hooks interact.
- For `repeated metadata keys`, return distinct keys from before and after.
- For `must preserve shape`, move resize/crop outside v1 or restore the original
  BHWC shape.

The complete example includes widgets, preview emission, fingerprinting,
metadata, and registration:
[`examples/third_party_aio_hook`](../../examples/third_party_aio_hook/).
