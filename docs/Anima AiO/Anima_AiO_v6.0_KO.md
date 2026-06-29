# Anima AiO v6.0 한국어 설명서

Anima AiO v6.0은 ANIMA 기반 ComfyUI 워크플로우입니다. T2I, I2I, HighRes, Inpainting, Face/Eye Detailer, Upscale, Image Save 경로를 한 파일에서 사용할 수 있게 구성되어 있습니다.

## 워크플로우 파일

- [Anima_AiO_v6.0_release_ko.json](../../example_workflows/Anima_AiO_v6.0_release_ko.json)

ComfyUI에서 워크플로우를 불러온 뒤, 각 섹션 상단의 Markdown 가이드 노드를 먼저 확인하세요.

## 필수 모델

아래 파일은 사용하는 섹션에 맞는 ComfyUI 모델 폴더에 넣어야 합니다.

| 용도 | 파일 | 위치 |
|---|---|---|
| Text encoder | [qwen_3_06b_base.safetensors](https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/text_encoders/qwen_3_06b_base.safetensors?download=true) | `models/text_encoders/` |
| Diffusion model | [anima-base-v1.0.safetensors](https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/diffusion_models/anima-base-v1.0.safetensors) | `models/diffusion_models/` |
| VAE | [qwen_image_vae.safetensors](https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/vae/qwen_image_vae.safetensors?download=true) | `models/vae/` |
| Utility LoRA | [Cosmos-Predict2.5-2B-base-distilled-LoRA.safetensors](https://huggingface.co/hanzogak/Anima-Comradeship/resolve/main/LoRA/Cosmos-Predict2.5-2B-base-distilled-LoRA.safetensors?download=true) | `models/loras/` |
| Inpainting | [anima-lllite-inpainting-v1.safetensors](https://huggingface.co/kohya-ss/Anima-LLLite/resolve/main/anima-lllite-inpainting-v1.safetensors) | `models/controlnet/` |
| Upscale | [2x-AnimeSharpV4_Fast_RCAN_PU.safetensors](https://huggingface.co/Kim2091/2x-AnimeSharpV4/resolve/main/2x-AnimeSharpV4_Fast_RCAN_PU.safetensors?download=true) | `models/upscale_models/` |

## 커스텀 노드

ComfyUI Manager 자동 설치가 실패하면 아래 저장소를 수동 설치한 뒤 ComfyUI를 재시작하세요.

- [ComfyUI-EasyUseAnima](https://github.com/n0va39/ComfyUI-EasyUseAnima)
- [ComfyUI-Anima-DAVE](https://github.com/sorryhyun/ComfyUI-Anima-DAVE)
- [ComfyUI-Anima-LLLite](https://github.com/kohya-ss/ComfyUI-Anima-LLLite)
- [ComfyUI-DCW](https://github.com/namemechan/ComfyUI-DCW)
- [ComfyUI-Spectrum-KSampler](https://github.com/sorryhyun/ComfyUI-Spectrum-KSampler)
- [ComfyUI-Spectrum-sdxl](https://github.com/ruwwww/ComfyUI-Spectrum-sdxl)
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
- [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
- [rgthree-comfy](https://github.com/rgthree/rgthree-comfy)
- [ComfyUI Image Saver](https://github.com/alexopus/ComfyUI-Image-Saver)

## 기본 사용 순서

1. `LoRA` 섹션에서 스타일 LoRA 프리셋과 트리거 프롬프트를 확인합니다.
2. 새 이미지는 `T2I`, 입력 이미지를 쓰는 경우는 `I2I`를 사용합니다.
3. `2. 모델 로드`와 `3. ANIMA 생성`이 기본 생성 경로입니다.
4. 기본 생성이 정상 동작한 뒤 `HighRes`, `Inpainting`, `Face/Eye Detailer`, `Upscale`을 필요한 만큼 켭니다.
5. `이미지 저장` 섹션에서 저장 파일명과 메타데이터 저장 옵션을 확인합니다.

## 섹션별 요약

### LoRA

배포본 프리셋과 같은 그림체를 재현하려면 워크플로우 안의 프리셋용 LoRA 링크 노드를 확인해 LoRA를 설치하세요. `Anima LoRA Preset`의 `FIX`는 파일명이 같을 때만 경로를 복구할 수 있습니다.

### T2I / I2I

`width`와 `height`는 기본 생성 해상도입니다. 처음에는 배포본 기본값으로 테스트하고, I2I에서는 `LoadImage`의 `example.png`를 실제 입력 이미지로 교체하세요.

### 모델 로드

`unet_name`, `clip_name`, `vae_name`이 ANIMA 기본 모델 파일을 가리키는지 확인하세요. SageAttention을 쓰려면 실행 환경에 맞는 패키지 설치가 필요할 수 있습니다. 설치가 맞지 않으면 모델 로드나 샘플러 단계에서 오류가 날 수 있으므로 먼저 꺼둔 상태로 테스트하세요.

### ANIMA 생성

기본 생성 경로입니다. DCW, Spectrum, Modulation Guidance 같은 패치는 환경과 모델 조합에 따라 오류가 날 수 있습니다. 오류가 나면 먼저 해당 스위치를 끄고 기본 샘플러만 확인하세요.

### HighRes

기본 결과를 더 큰 해상도로 다시 샘플링합니다. 해상도와 VAE 경로에 민감하므로, 기본 생성이 안정된 뒤 켜는 것이 좋습니다.

### Inpainting / Anima LLLite

`PreviewBridge`에서 마스크를 편집하고, `Anima LLLite` 모델로 인페인팅 경로를 보정합니다. 마스크 편집 상태나 임시 미리보기 이미지는 세션 상태에 영향을 받을 수 있습니다.

### Face / Eye Detailer

Impact Pack 기반 SEGS 디테일러입니다. `guide_size`, `max_size`, `denoise`, `feather`, `SEGS_crop_factor`가 결과에 큰 영향을 줍니다. 얼굴과 눈 디테일러는 같은 구조를 사용하며 세부 파라미터만 다르게 조정합니다.

### Upscale

최종 이미지를 업스케일합니다. 업스케일 모델 파일이 없거나 VRAM이 부족하면 실패할 수 있으므로, 저장 경로까지 확인한 뒤 켜세요.

### Image Save

파일명, 저장 형식, 메타데이터 저장 옵션을 관리합니다. 프롬프트와 LoRA 정보가 나중에 확인 가능하도록 메타데이터 저장 옵션을 유지하는 것을 권장합니다.

## 오류가 날 때

- 먼저 optional optimization 블록을 끄세요: Torch Compile, SageAttention, fp16 accumulation, DCW, Spectrum.
- 그다음 HighRes, Inpainting, Detailer, Upscale 섹션을 하나씩 끄고 기본 생성 경로를 확인하세요.
- 모델 파일명과 저장 위치가 맞는지 확인하세요.
- 커스텀 노드를 새로 설치했다면 ComfyUI를 재시작하세요.
