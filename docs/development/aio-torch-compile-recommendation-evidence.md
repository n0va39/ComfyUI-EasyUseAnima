# AiO Torch Compile Recommendation Evidence

## Evidence identity

- policy revision: `recommendation-v1`
- date: 2026-07-27
- scope: isolated synthetic transformer-block microbenchmark
- environment: Python 3.12.13, PyTorch 2.12.1+cu130, CUDA 13.0
- accelerator: CUDA, compute capability 12.0, 16,302 MiB total VRAM
- installed KJ mapping: `dynamic=false -> False`, `dynamic=auto -> None`

The device name was recorded in the local benchmark output, but the recommendation
policy does not branch on product names. The benchmark allocated no user model or
prompt data and did not start ComfyUI.

## Policy decision

The common safety axis is `inductor`, `fullgraph=false`, `mode=default`, transformer
blocks only, cache limit 64, debug off, and `disable_dynamic_vram=false`. Fixed
shapes use `dynamic=false`; variable or unknown shapes use KJ's `auto` choice.

`default` is retained as the balanced, non-aggressive compiler mode. The policy
does not claim that an autotune mode is faster for an AiO model because this bounded
run did not compare such modes. PyTorch documents `default` as balancing performance
and overhead, and describes automatic dynamic-shape behavior as preferable to
forcing `dynamic=True` in the general case:

- [torch.compile API](https://docs.pytorch.org/docs/stable/generated/torch.compile.html)
- [Dynamic shapes](https://docs.pytorch.org/docs/stable/user_guide/torch_compiler/torch.compiler_dynamic_shapes.html)

## One-run benchmark

The single policy-revision run compiled a width-512 FP16 residual MLP block on CUDA.
The fixed profile used 256 tokens repeatedly. The variable profile used 256 and 384
tokens, then warmed both shapes. Both used `backend=inductor`, `mode=default`, and
`fullgraph=false`.

| Profile | Dynamic argument | Cold first call | Shape transition | Warm median | Peak allocated / reserved | Graph variants | Recompile estimate | Graph breaks |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_shapes | `False` | 5698.251 ms | n/a | 0.246 ms | 83.252 / 104.000 MiB | 1 | 0 | 0 |
| variable_shapes | `None` (`auto`) | 58.285 ms | 1268.072 ms | 0.248 ms | 84.127 / 106.000 MiB | 2 | 1 | 0 |

`graph variants` is TorchDynamo's `unique_graphs` counter. `recompile estimate` is
`max(unique_graphs - 1, 0)` for each newly compiled callable. No graph break was
recorded in either profile.

The fixed profile ran first in the same process and paid global compiler
initialization. The variable profile could reuse initialized compiler state and the
isolated Inductor cache. Therefore the two cold-first-call values are observations,
not a valid cross-profile speed comparison. The useful result is narrower: the
fixed selection remained one graph, while the automatic variable selection accepted
one shape transition, produced one additional graph, and then served both shapes
without a graph break in the bounded run.

## Limits

- This is not a full AiO model generation, output-parity, or artifact test.
- Highres, Detailer, and USDU are represented only by a shape transition; their real
  sampling paths remain AIO-COMPILE-04 live coverage.
- Only the available high-VRAM environment was measured. Low, medium, and unknown
  VRAM behavior is a conservative pure-policy contract, not benchmarked optimality.
- LoRA, DAVE, SageAttention, dynamic VRAM, batch scaling, and other compile modes
  were not measured here.
- Cold timings are order-sensitive and should not be used as hardware rankings.

The recommendation endpoint remains read-only and never executes this benchmark or
calls `torch.compile`.
