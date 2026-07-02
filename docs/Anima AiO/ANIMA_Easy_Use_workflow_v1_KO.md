# ANIMA Easy Use workflow v1 사용법 초안

배포 workflow:
[ANIMA_Easy_Use_workflow_v1_release_ko.json](../example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json)

이 workflow는 `Anima Prompt Studio Advanced v2`, `Anima LoRA Preset`,
`Easy Use Anima Input`, `Anima AiO Generator`를 연결한 0.2.2용 간단 생성
흐름입니다. 프롬프트 편집과 모델/LoRA 입력은 upstream 노드에서 처리하고,
생성, 미리보기, 저장은 `Anima AiO Generator`에서 처리합니다.

## 필요한 모델

`Easy Use Anima Input`은 ANIMA checkpoint를 한 파일로 로드하지 않습니다.
아래 세 파일을 각각 선택합니다.

| 모델 | 권장 위치 |
| --- | --- |
| `anima-base-v1.0.safetensors` | `ComfyUI/models/diffusion_models/` |
| `qwen_image_vae.safetensors` | `ComfyUI/models/vae/` |
| `qwen_3_06b_base.safetensors` | `ComfyUI/models/text_encoders/` |

workflow를 불러온 뒤 파일명이 다르면 `Easy Use Anima Input`에서 직접 다시
선택합니다.

## 필요한 커스텀 노드

기본 설정 그대로 실행하는 데 필요한 노드팩:

| 노드팩 | 필요한 이유 |
| --- | --- |
| `ComfyUI-EasyUseAnima` | Prompt Studio Advanced v2, LoRA Preset, Easy Use Anima Input, AiO Generator |
| `ComfyUI-Spectrum-KSampler` | 기본 sampler backend인 Spectrum Mod Guidance Advanced와 Spectrum patch 옵션 |
| `ComfyUI-Image-Saver` | WebP 저장, workflow embed, Civitai/LoRA metadata 저장 |

선택 기능에만 필요한 노드팩:

| 노드팩 | 사용되는 기능 |
| --- | --- |
| `ComfyUI-Anima-DAVE` | Advanced Options의 Anima DAVE model patch |
| `ComfyUI-KJNodes` | SageAttention, Torch Compile, FP16 accumulation |
| `ComfyUI-Impact-Pack` | AiO Detailer의 SAM3, MaskToSEGS, DetailerForEach 경로 |

선택 노드팩이 없으면 관련 UI는 잠기거나 Queue 직전에 비활성화됩니다.

## 첫 실행 순서

1. 필요한 커스텀 노드와 모델을 설치하고 ComfyUI를 재시작합니다.
2. `ANIMA_Easy_Use_workflow_v1_release_ko.json`을 ComfyUI에 로드합니다.
3. `Easy Use Anima Input`에서 diffusion model, VAE, CLIP이 올바른 파일을
   가리키는지 확인합니다.
4. `Anima LoRA Preset`에서 없는 LoRA row는 끄거나, 파일명이 같은 LoRA가
   있으면 `FIX`로 복구합니다.
5. 처음에는 Highres와 Detailer를 끄고 기본 생성 경로만 실행합니다.
6. 기본 생성이 안정적으로 동작하면 Highres, Detailer, DAVE, KJNodes 최적화를
   필요한 순서대로 켭니다.

## 주요 조작 위치

- 프롬프트:
  `Anima Prompt Studio Advanced v2`에서 positive/negative field를 편집합니다.
- LoRA:
  `Anima LoRA Preset`에서 preset 번호, row 활성화, strength를 관리합니다.
- 모델:
  `Easy Use Anima Input`에서 ANIMA diffusion model, VAE, CLIP을 선택합니다.
- 생성:
  `Anima AiO Generator`에서 seed, steps, CFG, shift, denoise, sampler,
  scheduler를 조절합니다.
- Highres/Detailer:
  AiO Generator 좌측 패널의 각 섹션에서 활성화하고 톱니 버튼으로 세부 설정을
  엽니다.
- 저장:
  Save Options는 기본 ON입니다. 기본 출력은 WebP이며 workflow embed와
  Civitai/LoRA metadata 저장을 같이 처리합니다.

## 기본 샘플러 설정

기본 sampler backend는 `spectrum_mod_guidance_advanced`입니다.

초기값:

- Steps: `32`
- Sampler: `er_sde`
- Scheduler: `simple`
- AuraFlow shift: `3`
- Denoise: `1`

`shift=3`은 ANIMA 모델 권장 기본값입니다. Highres는 기본적으로 메인 CFG,
sampler, scheduler를 따르며, 기본값은 `Scale by=1.5`, `Denoise=0.25`입니다.

## 저장과 재현성

저장 이미지는 Image Saver backend로 처리됩니다. `Embed workflow`를 유지하면
저장된 이미지에서 workflow를 다시 불러와 같은 설정으로 재생성할 수 있습니다.

저장 metadata 기준:

- `Steps`, `CFG`, `Sampler`, `Scheduler`, `Seed`, `Denoise`: 1차 샘플러 값
- `Size`: Highres/Detailer 이후 최종 해상도
- `lora_stack`: `<lora:name:weight>` 형식으로 Image Saver metadata에 전달

## 문제 해결

- `Value not in list`가 sampler/scheduler에서 발생하면 설치된
  `ComfyUI-Spectrum-KSampler`와 ComfyUI sampler 목록을 확인합니다.
- Image Saver 관련 오류가 나면 `ComfyUI-Image-Saver` 설치 여부와 Save Options
  backend 설정을 확인합니다.
- LoRA 파일을 찾지 못하면 LoRA row를 끄거나 `FIX`를 실행합니다. `FIX`는
  저장된 경로가 달라도 파일명이 같으면 복구할 수 있습니다.
- 선택 노드팩이 없는데 관련 기능을 켠 경우, 해당 기능을 끄거나 노드팩을
  설치한 뒤 ComfyUI를 재시작합니다.
