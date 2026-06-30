# Anima SAM3 Context

카테고리: `EasyUse Anima/Detailer`

출력:

- `ctx_SAM3`
- `sam3_model`
- `sam3_clip`
- `sam3_vae`

ComfyUI native checkpoint loader로 SAM3 checkpoint를 로드하고, `Anima SAM3
Detailer`에서 사용할 수 있는 rgthree-compatible context를 반환합니다.

## 입력

- `ckpt_name`: 로드할 SAM3 checkpoint입니다. 예: `sam3.1_multiplex_fp16.safetensors`

## 사용 방법

`ctx_SAM3` 출력을 `Anima SAM3 Detailer`의 `ctx_SAM3` 입력에 연결합니다.
필요하면 `sam3_model`, `sam3_clip`, `sam3_vae` 개별 출력도 다른 workflow에
연결할 수 있습니다.

## 요구 사항

선택한 checkpoint가 ComfyUI checkpoint 경로에 있어야 합니다.
