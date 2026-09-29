# Easy Anima Safe PAG

Anima/Cosmos/Predict2 model patch. No extra checkpoint or external Safe PAG node
pack is needed. Connect `MODEL → Easy Anima Safe PAG → KSampler`.

The node perturbs selected self-attention blocks to produce a weaker prediction
and uses its difference from the normal prediction as additional guidance.

- `scale`: correction strength; 0 returns the input MODEL unchanged.
- `block_indices`: block numbers or ranges, such as `18` or `18-20`.
- `perturbation_strength`: attention blend; 0 preserves normal attention, 1 uses
  the full value/identity path.
- `head_indices`: optional attention heads; empty selects all heads.
- `start_percent` / `end_percent`: active part of sampling, between 0 and 1.
- `rescale` / `rescale_mode`: reduce excessive correction contrast/energy.

The defaults match the original node. AiO uses this same engine through its
Advanced settings and existing Safe PAG stage controls. Existing AiO workflows
require no migration. The standalone ID is `EasyAnimaSafePAG`; installing the
original pack alongside EasyUse does not replace its `AnimaSafePAG` node.
Existing workflows containing that external node still require it until rewired.
Reapplying the native node replaces its own correction instead of stacking it.

Safe PAG is intended for Anima-family models, not a generic image upscaler.
Upstream source and license: [provenance](../../third_party/anima-safe-pag/NOTICE.md).
