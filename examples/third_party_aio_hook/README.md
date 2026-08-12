# Third-party AiO hook example

This folder is a minimal copyable ComfyUI custom node pack. It includes a
same-shape final-image brightness hook and a first-pass sampler-settings hook.
Both record their settings in namespaced metadata.

1. Copy this folder into `ComfyUI/custom_nodes/example_easyuse_anima_aio_hook`.
2. Keep `ComfyUI-EasyUseAnima` installed in the same ComfyUI instance.
3. Restart ComfyUI.
4. Add `Example AiO Brightness Hook` or `Example AiO Sampling Settings Hook`.
5. Connect its `aio_hook` output to `Anima AiO Generator` → `aio_hook`.

The example imports only `easyuse_anima.extensions.aio`. That is the supported
public boundary. The import is intentionally deferred until the node executes,
because ComfyUI does not guarantee sibling node-pack load order. See the
[English guide](../../docs/extensions/aio-hooks.en.md) or
[Korean guide](../../docs/extensions/aio-hooks.ko.md) before adapting it.

The sampling example overrides only the public allowlist: `steps`, `cfg`,
`sampler_name`, `scheduler`, and `denoise`. See the guide for the equivalent
`model=` patch pattern. Replacing the sampling backend is a separate contract.

Coding agents adapting this directory should also follow the scoped
[AGENTS.md](AGENTS.md), which records the public import boundary, supported
patch allowlist, lifecycle, cache, and validation rules.
