# Anima SAM3 Detailer

Category: `EasyUse Anima/Detailer`

Outputs:

- `image`
- `segs`
- `mask`
- `raw_image`

This detailer node connects ComfyUI native SAM3 text detection, Impact
`MaskToSEGS`, and Impact Pack `DetailerForEach`.

## Main Inputs

- `enabled`: returns the original image when disabled.
- `image`: image to detail.
- `ctx_SAM3`: `Anima SAM3 Context` or a compatible rgthree context.
- `detect_prompt`: SAM3 text target. Use comma-separated targets or
  `target:count` for per-target counts.
- `detect_count`: maximum detections per target when `detect_prompt` has no
  explicit count.
- `threshold`: SAM3 detection threshold.
- `refine_iterations`: SAM decoder refinement passes.

The remaining sampling, inpaint, and hook inputs are forwarded through the
Impact `DetailerForEach` flow.

## Requirements

`ComfyUI-Impact-Pack` is required at execution time. EasyUse Anima can still
import without Impact Pack, but this node cannot run until Impact Pack is
available.
