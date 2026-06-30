# Anima Detailer Align Hook

Category: `EasyUse Anima/Detailer`

Output:

- `detailer_hook`

This node creates an Impact Pack compatible `DETAILER_HOOK` that aligns crop
sampling sizes used by Impact detailers.

![Anima Detailer Align Hook](../images/nodes/anima-detailer-align-hook.png)

## Where To Connect

Connect it to `detailer_hook` on Impact `DetailerForEach` or other
Impact-compatible SEGS detailers.

## Main Behavior

- `alignment=32` rounds crop sampling width and height upward to 32-multiples.
- This is intended for ANIMA/Spectrum workflows where 16-channel or special VAE
  paths can fail on non-32-multiple crop sizes.
- If another `detailer_hook` is connected, that hook runs first and the alignment
  adjustment is applied afterward.
- `alignment=none` keeps the original Impact Pack crop size.
