# AiO NegPip External Contract and License Boundary

## Upstream evidence

- repository: `pamparamm/ComfyUI-ppm`
- inspected commit: `cb4a46ba9b0ebdb1f9a228a901bb958bfc8ed3ba`
- public node id: `CLIPNegPip`
- license: AGPL-3.0

At the inspected commit, `CLIPNegPip` is a public ComfyUI V3 node. Its schema
requires `model: MODEL` and `clip: CLIP`, returns `MODEL` and `CLIP`, and exposes
a classmethod `execute(**kwargs)` returning `io.NodeOutput`. ComfyUI's public V3
compatibility bridge exposes the same schema through `INPUT_TYPES` and
`RETURN_TYPES`; `NodeOutput.result` contains the ordered output tuple.

## EasyUse Anima boundary

EasyUse Anima may discover the loaded public node class through the existing
Comfy node mapping and invoke its public classmethod. It must not:

- import `nodes_ppm`, `clip_negpip`, or another ComfyUI-ppm source module;
- copy or vendor the upstream patch, encoder, wrapper, or model-family logic;
- interpret or mutate the upstream private wrapper marker;
- require ComfyUI-ppm while the future mode remains Off;
- silently accept a changed required input, output order, execute signature, or
  malformed result.

The test-local contract fixture only models inspection and adaptation of the
public boundary. AIO-NEGPIP-01 adds no shipped helper and does not connect to AiO
generation, settings, cache, metadata, conditioning, CFG, workflow
serialization, UI, or public sockets.

## Ownership and fail-closed decisions

- ComfyUI-ppm owns cloning, model-family support, wrapper installation and its
  idempotency marker.
- EasyUse Anima owns one-call invocation, exact two-output adaptation, and
  actionable absence/contract errors.
- Returned MODEL and CLIP must both be non-null clones. Returning an input
  object directly fails closed because ownership would be ambiguous.
- Additional optional schema inputs can remain compatible. Missing/changed
  `model` or `clip`, any additional required input, changed output order/count,
  or an incompatible execute signature fails closed.
- Repeated calls are not retried by the adapter. Each requested invocation calls
  upstream once and passes the previously returned objects through unchanged;
  upstream remains responsible for avoiding duplicate wrapper installation.

## Phase boundary

AIO-NEGPIP-02 will implement the validated adapter together with its actual
LoRA-derived MODEL/CLIP lineage ownership, add On-mode settings/cache/metadata
behavior, and run one real Anima + ComfyUI-ppm live smoke. Turbo prompt
transformation, neutral conditioning, effective CFG 1 and UI remain later
phases.
