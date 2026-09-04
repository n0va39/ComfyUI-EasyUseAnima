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
5. 다른 노드팩의 AiO 확장을 쓸 때만 `EASYUSE_ANIMA_AIO_HOOK` 출력을
   `aio_hook`에 연결합니다. 여러 hook은 `Anima AiO Hook Combine`으로 합칩니다.

## 확장 hook

`aio_hook`은 연결하지 않아도 기존 생성과 저장 동작이 그대로 유지되는 선택
입력입니다. 현재 v1은 `first_pass/before`의 MODEL·sampler allowlist patch와 최종
postprocess의 before/after callback, 같은 shape의 `IMAGE`, 확장 metadata, 선택적
preview를 공개합니다. postprocess hook으로 바뀐 `IMAGE`는 Generator의 `LATENT`와
일치하도록 다시 인코딩되지 않습니다.

직접 hook 노드를 만들려면 [AiO Hook API v1 개발 가이드](../extensions/aio-hooks.ko.md)와
[복사 가능한 예제](../../examples/third_party_aio_hook/)를 참고하세요.

## 생성 프로필

`SAMPLER` 헤더의 프로필 버튼은 생성 설정 전체 스냅샷을 적용합니다.

- `일반`은 현재 기본값을 유지하고 선택적인 Spectrum/DCW 및 KJ 실행 최적화를
  모두 끕니다.
- `터보`는 `steps=10`, `CFG=1`, `er_sde`, `simple`을 사용합니다.
- `최적화`는 모든 샘플링 단계의 Spectrum/DCW와 권장 KJ FP16 accumulation,
  SageAttention, Sage compile, Torch Compile 값을 활성화합니다. DAVE와 Safe
  PAG는 별도 선택 기능이므로 꺼진 상태를 유지합니다.

현재 설정이 기본 프로필과 정확히 일치하지 않으면 버튼에 `커스텀`이
표시됩니다. 이름 지정 사용자 프로필은 현재 생성 설정 전체를 ComfyUI 사용자
데이터에 저장하며, 재시작 후에도 불러오기, 덮어쓰기, 이름 변경, 삭제가
가능합니다. 적용한 사용자 프로필 값을 수정하면 다시 `커스텀`으로 표시됩니다.

워크플로우에는 선택한 프로필 이름이 아니라 생성 설정 전체가 직렬화됩니다.
따라서 다른 ComfyUI 설치에 같은 이름의 프로필이 없어도 생성 설정은
유지됩니다.

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
않습니다. Highres는 기본적으로 1차 샘플러 경로를 재사용하되, `Steps`와
`Denoise`만 Highres 값으로 바꿉니다. 1차가 `spectrum_spd_speed`이면 Highres는
SPD를 재사용하지 않고 일반 KSampler 경로로 실행합니다. Highres에서 메인
샘플러 재사용을 끄면 항상 일반 KSampler만 사용합니다.

`SpectrumKSamplerAdvanced`와 `SpectrumSPDKSampler` 호출은 설치된 Spectrum
노드팩의 실제 `sample()` 입력 시그니처를 확인해 지원되는 파라미터만 전달합니다.
Sampler Details는 `/object_info`에서 발견한 추가 입력을 `Detected inputs`로
표시하고, 노드팩 tooltip이 있으면 해당 tooltip을 우선 표시합니다.

`Anima DAVE`, AuraFlow shift, KJNodes FP16 accumulation, SageAttention,
Torch Compile은 샘플러 Mode가 아니라 Advanced Options의 모델 패치/최적화
항목입니다. 켜면 선택한 1차 샘플러 실행 전에 모델에 적용됩니다.

Highres 기본값은
`Scale by=1.5`, `Denoise=0.25`입니다. Highres와 Detailer 상세창은 긴 설정을
다루기 쉽도록 1열 스크롤 레이아웃을 사용합니다.

Detailer Settings는 Face/Eye 같은 처리 블럭을 탭으로 보여줍니다. 각 탭은
이름을 바꿀 수 있고 좌우 이동 버튼으로 실행 순서를 조정할 수 있습니다.
탭 이름은 UI 정리용 메타데이터이며, 실제 실행은 안정적인 내부 키와
`detailer.order`를 사용합니다.

## 저장과 재현성

Save Options는 기본적으로 켜져 있고 EasyUse 네이티브 출력 backend를 사용합니다.
기존 workflow와 profile의 호환성을 위해 직렬화된 backend ID는 `image_saver`로
유지하지만, 더 이상 `ComfyUI-Image-Saver`를 설치할 필요는 없습니다.

PNG, JPEG, WebP 모두 A1111 방식의 사람이 읽기 쉬운 `parameters` 블럭을
저장합니다. PNG는 ComfyUI prompt와 workflow를 text chunk에, JPEG/WebP는
EXIF Make/Model 표현에 저장합니다. 저장 이미지에서 같은 설정을 다시
불러오려면 `Embed workflow`를 유지하세요. PNG/WebP는 ComfyUI가 직접 읽고,
JPEG는 EasyUse의 크기 제한된 전용 파일 handler가 embedded workflow를 먼저
불러온 뒤 없으면 API prompt를 사용합니다. JPEG가 아니거나 metadata가 없거나
손상된 경우에는 기존 ComfyUI handler로 그대로 넘기며, ComfyUI가 native JPEG
metadata 지원을 제공하면 자동으로 그 경로에 위임합니다. `Save workflow JSON`을
켜면 별도 sidecar도 저장합니다. JPEG workflow가 EXIF 크기 한도를 넘으면
A1111 메타데이터는 보존하고 workflow JSON sidecar를 자동으로 남기므로
메타데이터가 빠진 부분 저장 파일을 만들지 않습니다. 이 경우 JPEG 안에는
제거된 workflow가 없으므로 같은 이름의 `.json` sidecar를 직접 여세요.

`Lossless WebP`가 꺼져 있으면 WebP를 손실 압축으로 저장하며, `JPEG/WebP
quality`로 화질과 파일 크기의 균형을 조절합니다. lossless 모드에서는 saver에
전달된 픽셀 값을 보존합니다.

저장 메타데이터의 `Steps`, `CFG`, `Sampler`, `Scheduler`, `Seed`, `Denoise`는
1차 샘플러 값을 사용합니다. `Size`는 Highres와 Detailer 이후의 최종 해상도를
사용합니다. EasyUse는 로컬에서 확인된 diffusion model, 실제 적용된
`lora_stack`, 양쪽 prompt의 `embedding:name` 참조를 SHA-256으로 계산합니다.
embedding 하위 폴더와 `(embedding:name:0.8)` 가중치를 지원하며, 존재하지 않거나
안전하지 않거나 이름이 모호한 항목은 건너뜁니다.

SHA-256 결과는 메모리 cache와 ComfyUI user-data 폴더 내부의 제한된 원자적
cache를 사용하고, cache가 없는 파일은 계산 진행률을 표시합니다. 모델, LoRA,
embedding 파일 옆에는 cache 파일을 만들지 않습니다. 로컬 hash는 A1111 호환
길이로 줄이지만 검증된 수동 hash 값은 그대로 보존하며, 로컬 `model` hash를
덮어쓸 수 없습니다. `Civitai data`는 기본적으로 꺼져 있으며, 명시적으로 켜면
고정된 `https://civitai.com/api/v1` endpoint로 로컬 및 수동 hash 정보를
보강합니다. 짧은 hash는 응답 파일의 hash와 정확히 일치할 때만 사용합니다.
조회 실패는 이미지 저장을 막지 않습니다. Civitai Hash Fetcher 항목도 username,
model name, version을 사용해 `model_name:AutoV3` 항목을 추가합니다.

## 필요 노드팩

- 필수: `ComfyUI-EasyUseAnima`
- 샘플 워크플로우 기본값: `ComfyUI-Spectrum-KSampler`
- 선택 기능: `ComfyUI-KJNodes` (SageAttention, Torch Compile), `ComfyUI-Impact-Pack` (AiO SAM3 detailer 경로), `ComfyUI-Anima-DAVE` (Anima DAVE 모델 패치)

선택 노드팩이 설치되어 있지 않으면 해당 UI는 잠기고, Queue 직전에도 해당
옵션이 비활성화되어 누락된 선택 기능으로 인한 실행 오류를 피합니다.

예제 워크플로우:

- [ANIMA_Easy_Use_workflow_v1_release_ko.json](../example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json)
- [EasyUse_Anima_AiO_generator_release_ko.json](../example_workflows/EasyUse_Anima_AiO_generator_release_ko.json)

사용 가이드: [ANIMA Easy Use workflow v1](../Anima%20AiO/ANIMA_Easy_Use_workflow_v1_KO.md)
