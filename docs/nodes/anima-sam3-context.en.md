# Anima SAM3 Context

Category: `EasyUse Anima/Detailer`

Outputs:

- `ctx_SAM3`
- `sam3_model`
- `sam3_clip`
- `sam3_vae`

This node loads a SAM3 checkpoint through ComfyUI's native checkpoint loader and
returns an rgthree-compatible context for `Anima SAM3 Detailer`.

## Input

- `ckpt_name`: SAM3 checkpoint to load, for example
  `sam3.1_multiplex_fp16.safetensors`.

## Usage

Connect `ctx_SAM3` to the `ctx_SAM3` input on `Anima SAM3 Detailer`. The
individual `sam3_model`, `sam3_clip`, and `sam3_vae` outputs can also be used in
other workflows when needed.

## Requirements

The selected checkpoint must be available in the ComfyUI checkpoint paths.
