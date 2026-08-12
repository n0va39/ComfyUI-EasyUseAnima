# Third-Party AiO Hook Agent Guide

This directory is a copyable sibling ComfyUI custom-node example. Keep changes
small, runnable, and limited to the stable public API.

## Public boundary

- Output the literal socket type `EASYUSE_ANIMA_AIO_HOOK`.
- Defer `easyuse_anima.extensions.aio` imports until the provider node executes.
  ComfyUI does not guarantee sibling node-pack import order.
- Do not import `easyuse_anima.aio.*`, `GenerationRequest`, `GenerationState`,
  `RuntimeServices`, or another private EasyUse Anima module.
- Keep the definition immutable and reusable. Put per-run mutable state and
  resources in the session returned by `create_session(context)`.

## Supported stage patches

Use only hook points that the runtime actually dispatches:

- `FIRST_PASS / BEFORE`
  - read `event.state.model`
  - return a new sampling MODEL with `AioHookPatch(model=...)`
  - optionally return `settings={"sampler": ...}` with only `steps`, `cfg`,
    `sampler_name`, `scheduler`, and `denoise`
- `POSTPROCESS / BEFORE` and `POSTPROCESS / AFTER`
  - return an out-of-place, same-shape `IMAGE`
  - remember that the Generator does not re-encode `LATENT` after an image patch
- every supported point may add JSON-safe namespaced metadata

Do not add `backend`, seed, Spectrum/SPD/DCW dictionaries, arbitrary settings
sections, a custom sampler object, stage replacement, or hidden in-place core
state mutation. Propose those as separate contracts.

## Lifecycle, order, and cache

- `describe()` must be side-effect free and return a deterministic descriptor.
- Include every output-affecting provider setting in the JSON-safe
  `fingerprint`. Use `None` only when stability is impossible.
- Combined hooks run before callbacks in connection order and after callbacks
  in reverse order. Session `close()` runs in reverse provider order; cleanup
  callbacks run in global reverse-registration order (LIFO).
- Register temporary-resource cleanup through
  `context.services.register_cleanup(callback)` or `close()`.
- A first-pass hook bypasses the shared first-pass cache. Do not add a second
  private cache around MODEL or sampler results without a separate contract.
- Provider code runs in ComfyUI's trusted Python process, not a sandbox.

## Minimal implementation shape

```python
class Session(AioHookSessionBase):
    def before_stage(self, event):
        model = apply_provider_patch(event.state.model)
        return AioHookPatch(
            model=model,
            settings={"sampler": {"sampler_name": "euler"}},
        )
```

Keep `apply_provider_patch()` inside the provider pack and make it return a new
MODEL. The AiO runtime validates the public patch; it does not own provider
dependencies or discover providers globally.

## Required validation

From the EasyUse Anima repository worktree, run exact focused targets one at a
time:

```powershell
powershell -ExecutionPolicy Bypass -File <workspace>\tools\run_focused_unittest.ps1 `
  -Project <absolute-worktree-path> `
  -TestTarget tests.test_aio_hook_example
```

When public contract or pipeline behavior changes, also run
`tests.test_aio_hook_runtime` and the repository `quick` gate. A final PR
candidate requires the repository-owned `full` gate. Backend registration
changes require a ComfyUI restart; frontend module changes require a hard
refresh. Validate the optional socket and prompt serialization on Legacy Canvas
and Node 2.0 when the node contract changes.
