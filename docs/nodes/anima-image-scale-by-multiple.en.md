# Anima Image Scale By Multiple

Category: `EasyUse Anima/Image`

Inputs:

- `image`
- `scale_by`
- `upscale_method`
- `multiple`
- `max_long_edge`

Outputs:

- `image`
- `width`
- `height`
- `applied_scale`

This node scales an image by the nearest valid ratio that preserves the source
aspect ratio while making the output width and height multiples of the selected
size. Use it in Highres, optimization, or 16-channel VAE paths that require or
prefer 32-multiple dimensions.

## Main Behavior

- `scale_by` is the requested ratio; the actual ratio is adjusted to the nearest
  valid size for the selected `multiple`.
- `multiple=32` is the safe default for ANIMA/Spectrum Highres flows.
- When `max_long_edge` is greater than 0, the node chooses the closest valid
  size that does not exceed that long-edge limit.
- The final size and actual ratio are returned as `width`, `height`, and
  `applied_scale`.

## Where To Connect

Place it before image inputs that need stable Highres dimensions, or before any
downstream node that expects width and height to be aligned to a specific
multiple.
