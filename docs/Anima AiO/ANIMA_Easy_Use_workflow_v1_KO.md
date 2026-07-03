# ANIMA Easy Use workflow v1 사용 가이드

배포 workflow:
[ANIMA_Easy_Use_workflow_v1_release_ko.json](../example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json)

English workflow:
[ANIMA_Easy_Use_workflow_v1_release_en.json](../example_workflows/ANIMA_Easy_Use_workflow_v1_release_en.json)

English guide:
[ANIMA_Easy_Use_workflow_v1_EN.md](ANIMA_Easy_Use_workflow_v1_EN.md)

이 workflow는 ANIMA 생성에 필요한 입력을 네 노드로 줄인 간단 생성 흐름입니다.
`Anima Prompt Studio Advanced v2`에서 프롬프트를 만들고,
`Anima LoRA Preset`에서 LoRA stack과 trigger word를 관리한 뒤,
`Easy Use Anima Input`에서 ANIMA 모델 세트를 선택하고,
`Anima AiO Generator`에서 생성, Highres, Detailer, Preview, Save를 실행합니다.

![ANIMA Easy Use workflow v1 guide notes](../assets/images/workflows/anima-easy-use-v1-guide-notes.webp)

## 빠른 요약

처음 실행할 때는 아래 순서만 확인하면 됩니다.

1. 필요한 모델과 커스텀 노드를 설치합니다.
2. workflow를 ComfyUI에 로드합니다.
3. `Easy Use Anima Input`에서 diffusion model, VAE, CLIP 3개가 맞는지 확인합니다.
4. `Anima LoRA Preset`에서 없는 LoRA row는 끄거나 `FIX`로 복구합니다.
5. `Anima Prompt Studio Advanced v2`의 `일반 태그` field에 원하는 프롬프트를 넣습니다.
6. 처음에는 Highres와 Detailer를 끄고 기본 생성만 실행합니다.
7. 기본 생성이 안정적이면 Highres, Detailer, DAVE, KJNodes 최적화를 필요한 것부터 켭니다.

## 필요한 모델

`Easy Use Anima Input`은 ANIMA를 checkpoint 하나로 로드하지 않습니다. 아래 세
파일을 각각 선택합니다.

| 모델 | 권장 위치 |
| --- | --- |
| `anima-base-v1.0.safetensors` | `ComfyUI/models/diffusion_models/` |
| `qwen_image_vae.safetensors` | `ComfyUI/models/vae/` |
| `qwen_3_06b_base.safetensors` | `ComfyUI/models/text_encoders/` |

workflow 안의 안내 노트에도 모델 다운로드 링크가 들어 있습니다. 파일명이 다르면
`Easy Use Anima Input`에서 직접 다시 선택하면 됩니다.

![Easy Use Anima Input](../assets/images/workflows/anima-easy-use-v1-model-input.webp)

## 필요한 커스텀 노드

기본 생성 경로에 필요한 노드팩:

| 노드팩 | 필요한 이유 |
| --- | --- |
| [ComfyUI-EasyUseAnima](https://github.com/n0va39/ComfyUI-EasyUseAnima) | Prompt Studio Advanced v2, LoRA Preset, Easy Use Anima Input, AiO Generator |
| [ComfyUI-Spectrum-KSampler](https://github.com/sorryhyun/ComfyUI-Spectrum-KSampler) | 기본 sampler backend와 Spectrum 최적화 |
| [ComfyUI-Image-Saver](https://github.com/alexopus/ComfyUI-Image-Saver) | WebP 저장, workflow embed, Civitai/LoRA metadata 저장 |

사용하면 좋은 노드팩:

| 노드팩 | 사용되는 기능 |
| --- | --- |
| [ComfyUI-Lora-Manager](https://github.com/willmiao/ComfyUI-Lora-Manager) | LoRA trigger word와 metadata 관리 |
| [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | SageAttention, Torch Compile, FP16 accumulation |
| [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) | SAM3, MaskToSEGS, DetailerForEach 기반 Detailer |
| [ComfyUI-Anima-DAVE](https://github.com/sorryhyun/ComfyUI-Anima-DAVE) | 생성 다양성을 위한 선택 model patch |

`ComfyUI-EasyUseAnima`는 0.2.2 이상이 필요합니다. 선택 노드팩이 없으면 관련 UI는
잠기거나 Queue 직전에 비활성화됩니다.

## LoRA 프리셋

`Anima LoRA Preset`은 스타일 프롬프트와 LoRA stack을 프로필로 저장합니다.
workflow에 포함된 LoRA들은 필수 모델이 아니라 샘플 스타일 재현용입니다.

![Anima LoRA Preset](../assets/images/workflows/anima-easy-use-v1-lora-preset.webp)

주요 동작:

- `프로필 인덱스`로 저장된 LoRA 조합을 선택합니다.
- row별 toggle과 strength로 적용 여부와 강도를 조절합니다.
- 출력 `LORA_STACK`은 `Anima AiO Generator`의 `lora_stack`에 연결됩니다.
- 출력 `트리거 워드`는 Prompt Studio의 trigger field로 들어갑니다.
- LoRA 경로가 바뀐 경우 파일명이 같으면 `FIX`로 복구할 수 있습니다.
- LoRA Manager에서 trigger word와 metadata를 scan/refresh 해두면 관리가 쉽습니다.

## 프롬프트 입력

프롬프트는 `Anima Prompt Studio Advanced v2`에서 편집합니다. 이 노드는
`EASYUSE_ANIMA_PROMPT_DATA`를 출력하며, downstream 노드는 문자열 출력 순서가
아니라 prompt data key를 기준으로 값을 읽습니다.

![Anima Prompt Studio Advanced v2](../assets/images/workflows/anima-easy-use-v1-prompt-studio.webp)

기본 field 역할:

| Field | 역할 |
| --- | --- |
| `1. 트리거` | LoRA Preset의 trigger word가 연결되면 실행 시 값이 덮어써집니다. |
| `2. 품질 태그` | score, quality, highres 계열 태그를 둡니다. |
| `3. 작가 태그` | 작가 태그 또는 artist mix용 태그를 둡니다. |
| `4. 일반 태그` | 사용자가 주로 편집하는 subject/general prompt 영역입니다. |
| `NAIA 프롬프트` | NAIA 결과를 받을 때 사용합니다. 필요 없으면 꺼둘 수 있습니다. |
| `negative fields` | 품질 negative와 일반 negative를 나눠 관리합니다. |

와일드카드와 자동완성도 이 화면에서 사용할 수 있습니다. 와일드카드 문법은
[와일드카드 가이드](../wildcards.ko.md), Prompt Studio 세부 기능은
[Prompt Studio Advanced 문서](../nodes/anima-prompt-studio-advanced.ko.md)를
참고하세요.

## 생성

`Anima AiO Generator`는 실제 생성 실행 노드입니다. 왼쪽에는 sampler, Highres,
Detailer 설정이 있고, 가운데에는 현재 이미지와 이전 단계 비교 preview가 표시됩니다.

![Anima AiO Generator](../assets/images/workflows/anima-easy-use-v1-aio-generator.webp)

기본 sampler backend는 `Spectrum Mod Guidance`입니다. 초기값은 아래와 같습니다.

| 항목 | 기본값 |
| --- | --- |
| Steps | `32` |
| Sampler | `er_sde` |
| Scheduler | `sgm_uniform` |
| AuraFlow shift | `3` |
| Denoise | `1` |

샘플러 상세 설정은 sampler 섹션의 톱니 버튼에서 엽니다. 이 workflow는
`comfy_ksampler`, `spectrum_mod_guidance_advanced`, `spectrum_spd_speed` 경로를
지원합니다. 잘 모르면 기본값인 `Spectrum Mod Guidance`를 유지하면 됩니다.

Spectrum 속도 최적화에서 가장 먼저 볼 값은 `Flex window`와 `Warmup steps`입니다.
속도를 더 원하면 `Flex window`를 조금 올리고, 품질이 떨어지면 `Warmup steps`를
조금 늘리는 방식으로 조정합니다. 더 자세한 sampler 옵션은
[ComfyUI-Spectrum-KSampler](https://github.com/sorryhyun/ComfyUI-Spectrum-KSampler)
문서를 기준으로 확인하세요.

## Highres와 Detailer

Highres와 Detailer는 처음 실행할 때는 끄고 시작하는 것이 안전합니다. 기본 생성이
정상 동작한 뒤 필요한 것부터 켭니다.

![Highres and Detailer settings](../assets/images/workflows/anima-easy-use-v1-highres-detailer.webp)

Highres:

- `메인 샘플러 따름`을 켜면 backend, CFG, sampler, scheduler는 1차 샘플러 값을
  이어받고, steps와 denoise는 Highres 값을 사용합니다.
- 1차 샘플러가 SPD 경로여도 Highres에서는 `comfy_ksampler` 경로로 fallback됩니다.
- Spectrum, DCW, CFG++, FSG, SMC 같은 correction/forecast 계열 값은 Highres
  상세 설정에서 별도로 켜고 조정할 수 있습니다.
- 크기는 `Anima Image Scale By Multiple` 경로를 통해 지정 배수에 맞춰 조정됩니다.
- 기본값은 `Scale by=1.25`, `Steps=19`, `Denoise=0.29`, `Max long edge=2560`입니다.

Detailer:

- Face, Eye 같은 detailer block을 켜고 끌 수 있습니다.
- 상세 설정에서 detailer block을 추가하고 block별 감지 prompt, step, denoise,
  sampler patch 옵션을 조정할 수 있습니다.
- block 순서는 위/아래 버튼으로 바꿀 수 있습니다.
- SAM3 기반 감지와 Impact Pack의 MaskToSEGS/DetailerForEach 흐름을 사용합니다.
- Mod Guidance는 AiO Generator 공통 설정을 이어받습니다.
- Spectrum, DCW, CFG++, FSG, SMC 같은 correction/forecast 계열 값은 block별 상세
  설정에서 별도로 켜고 조정할 수 있습니다.
- crop 크기는 `Anima Detailer Align Hook` 계열 로직으로 32배수에 맞춰 안정성을 높입니다.

## 미리보기와 저장

Preview 섹션은 생성 중간 이미지, 이전 단계와 비교, image feed를 표시할 수 있습니다.
이 설정은 노드 UI에만 적용되고 저장 이미지 metadata는 바꾸지 않습니다.

Save Options는 기본 ON입니다. 기본 backend는 Image Saver이며, WebP 저장,
workflow embed, Civitai/LoRA metadata 저장을 함께 처리합니다.

저장 metadata 기준:

- `Steps`, `CFG`, `Sampler`, `Scheduler`, `Seed`, `Denoise`: 1차 샘플러 값
- `Size`: Highres/Detailer 이후 최종 해상도
- `lora_stack`: `<lora:name:weight>` 형식으로 Image Saver metadata에 전달

`Embed workflow`를 유지하면 저장된 이미지에서 workflow를 다시 불러와 같은 설정으로
재생성할 수 있습니다.

## 문제 해결

- `Value not in list`가 sampler/scheduler에서 발생하면 설치된
  `ComfyUI-Spectrum-KSampler` 버전과 ComfyUI sampler 목록을 확인합니다.
- Image Saver 관련 오류가 나면 `ComfyUI-Image-Saver` 설치 여부와 Save Options
  backend 설정을 확인합니다.
- LoRA 파일을 찾지 못하면 해당 row를 끄거나 `FIX`를 실행합니다.
- 선택 노드팩이 없는데 관련 기능을 켠 경우, 해당 기능을 끄거나 노드팩을 설치한 뒤
  ComfyUI를 재시작합니다.
- 처음부터 Highres/Detailer까지 모두 켜서 실패하면 기본 생성만 먼저 통과시킨 뒤
  기능을 하나씩 켜서 원인을 좁힙니다.
