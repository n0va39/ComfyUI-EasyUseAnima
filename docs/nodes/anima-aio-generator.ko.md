# Anima AiO Generator

카테고리: `EasyUse Anima/AiO`

![Anima AiO Generator](../images/aio-generator-node.png)

`Anima AiO Generator`는 `Easy Use Anima Input`에서 전달받은 전용 context를
사용해 프롬프트 인코딩, 1차 샘플링, 선택적 Highres, 선택적 Detailer, 이미지
저장을 한 노드에서 실행합니다. Prompt Studio에서 만든 prompt data는 upstream에서
처리되므로 이 노드 UI에는 프롬프트 편집 항목이 없습니다.

## 기본 연결

1. `Anima 프롬프트 스튜디오 고급 v2`의 prompt data를 `Easy Use Anima Input`에 연결합니다.
2. `Easy Use Anima Input`에서 ANIMA diffusion model, VAE, CLIP을 각각 선택합니다.
3. `Easy Use Anima Input` 출력을 `Anima AiO Generator`의 `easy use anima input`에 연결합니다.
4. 필요하면 `Anima LoRA Preset`의 `LORA_STACK`을 `lora_stack`에 연결합니다.

## 샘플러 모드

`Sampler` 설정의 `Mode`는 실제 호출 경로를 결정합니다.

초기 기본값은 `steps=32`, `sampler=er_sde`, `scheduler=simple`,
`shift=3.0`입니다. `shift=3.0`은 Anima 모델 권장 기본값이며 항상 적용됩니다.

| Mode | 호출 경로 | 필요 노드팩 |
| --- | --- | --- |
| `comfy_ksampler` | ComfyUI 기본 KSampler. 선택 시 Spectrum model patch와 corrections를 모델 패치로 적용할 수 있음 | ComfyUI 기본, 선택 시 `ComfyUI-Spectrum-KSampler` |
| `spectrum_mod_guidance_advanced` | `KSampler (Spectrum + Mod Guidance Advanced)` 통합 샘플러 직접 호출 | `ComfyUI-Spectrum-KSampler` |
| `spectrum_spd_speed` | `KSampler (Spectrum + SPD / SPEED)` 통합 샘플러 직접 호출 | `ComfyUI-Spectrum-KSampler` |

통합 샘플러를 선택하면 일반 KSampler용 Spectrum model patch는 중복 호출하지
않습니다. Highres와 Detailer 단계는 stage sampler로 실행되며 기본적으로 메인
CFG, sampler, scheduler를 따릅니다.

`Anima DAVE`, AuraFlow shift, KJNodes FP16 accumulation, SageAttention,
Torch Compile은 샘플러 Mode가 아니라 Advanced Options의 모델 패치/최적화
항목입니다. 켜면 선택한 1차 샘플러 실행 전에 모델에 적용됩니다.

Highres는 기본적으로 메인 CFG, sampler, scheduler를 따릅니다. 기본값은
`Scale by=1.5`, `Denoise=0.25`입니다. Highres와 Detailer 상세창은 긴 설정을
다루기 쉽도록 1열 스크롤 레이아웃을 사용합니다.

Detailer Settings는 Face/Eye 같은 처리 블럭을 탭으로 보여줍니다. 각 탭은
이름을 바꿀 수 있고 좌우 이동 버튼으로 실행 순서를 조정할 수 있습니다.
탭 이름은 UI 정리용 메타데이터이며, 실제 실행은 안정적인 내부 키와
`detailer.order`를 사용합니다.

## 저장과 재현성

Save Options는 기본적으로 켜져 있고 `ComfyUI-Image-Saver` backend를 사용합니다.
`Embed workflow`를 유지하면 저장된 이미지에서 workflow를 다시 불러와 같은
설정을 재생성할 수 있습니다. Civitai Hash Fetcher 항목은 username, model name,
version을 저장하고 Image Saver의 `additional_hashes`에 `model_name:AutoV3`
형식으로 전달합니다.

저장 메타데이터의 `Steps`, `CFG`, `Sampler`, `Scheduler`, `Seed`, `Denoise`는
1차 샘플러 값을 사용합니다. `Size`는 Highres와 Detailer 이후의 최종 해상도를
사용합니다. `lora_stack`으로 적용된 LoRA는 저장 시 Image Saver 메타데이터
프롬프트에 `<lora:name:weight>` 형식으로 전달되어 Civitai LoRA resource와
weight 저장에 사용됩니다.

## 필요 노드팩

- 필수: `ComfyUI-EasyUseAnima`
- 샘플 워크플로우 기본값: `ComfyUI-Spectrum-KSampler`, `ComfyUI-Image-Saver`
- 선택 기능: `ComfyUI-KJNodes` (SageAttention, Torch Compile), `ComfyUI-Impact-Pack` (SAM3 Detailer), `ComfyUI-Anima-DAVE` (Anima DAVE 모델 패치)

선택 노드팩이 설치되어 있지 않으면 해당 UI는 잠기고, Queue 직전에도 해당
옵션이 비활성화되어 누락된 선택 기능으로 인한 실행 오류를 피합니다.

예제 워크플로우:

- [ANIMA_Easy_Use_workflow_v1_release_ko.json](../example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json)
- [EasyUse_Anima_AiO_generator_release_ko.json](../example_workflows/EasyUse_Anima_AiO_generator_release_ko.json)

사용법 초안: [ANIMA Easy Use workflow v1](../Anima%20AiO/ANIMA_Easy_Use_workflow_v1_KO.md)
