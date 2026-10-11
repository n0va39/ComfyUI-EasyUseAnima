# Easy Anima IP-Adapter Hook

Connect the installed [LuciferTC Anima IP-Adapter](https://github.com/LuciferTC9527/ComfyUI-Anima_IP-Adapter)
to the first pass of Anima AiO Generator. External code and weights are neither bundled nor automatically installed.

## Wiring

1. Install the external pack and its SigLIP2 and IP-Adapter weights; restart ComfyUI.
2. Connect `Anima IP-Adapter Loader (SigLIP2)` to `ip_adapter`.
3. Connect one RGB `Load Image` output to `ref_image`.
4. Connect this node's `aio_hook` output to the Generator's `aio_hook` input.

Do not also apply the external Apply node. The hook uses AiO's prepared model.
IP-Adapter affects only the first pass, not Highres, Detailer or Upscale.
Existing unconnected workflows work without the external pack.

## Supported configuration

- Reviewed upstream commit: `6b77cd0c367d76402174ace2be50d3cb6aa77855`.
  The registered Apply implementation is checked by source fingerprint, independent of installation folder name.
  Other revisions and conflicting nodes produce an explicit error pending compatibility review.
- 28-block Anima and adapter, one reference image, generation batch size 1.
- Default CUDA device, standard ComfyUI sampler and standard CFG.
- Start ComfyUI with `--disable-dynamic-vram`. The diffusion model must fit fully on the GPU;
  use `--highvram` with sufficient VRAM if partial loading is reported.
- Compile, multi-GPU, Spectrum acceleration, existing IP patches and conflicting CFG/model wrappers are unsupported.
  Checkpoints requiring shared Q projections or injection before MLP are unsupported.

Settings retain the upstream Apply meanings. Match `siglip_layer` to checkpoint training and use
a multiple of 16 for `ref_image_size`. Independent IP CFG (`ip_cfg_separate`) costs additional model evaluations.
`use_lora` controls LoRA stored inside the IP checkpoint, not the ordinary AiO LoRA stack.

## Lifecycle

Apply runs at `SAMPLER_SAMPLE`, after loading and ordinary LoRA patching. A transaction restores
added modules, attention hooks, block forwards and cross-attention layers on success, error or interruption,
before ComfyUI sampling cleanup and later AiO stages. Encoder device placements are restored too.
Calls through this integration are serialized; unrelated tools concurrently mutating the same model are unsupported.
The hook does not reuse AiO output caches because external mutable weights and image tensors are not a stable
JSON fingerprint. Save the Loader, reference image and hook settings with the workflow.

Implementation and validation: [Issue #800](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/800).
