# ComfyUI EasyUse Anima

언어: [English](README.en.md) | [한국어](README.ko.md) | [Home](README.md)

프롬프트 편집, ANIMA 프롬프트 보정, NAIA 프롬프트 연동, LoRA 프리셋 관리,
와일드카드 확장, AiO 생성, ANIMA/Spectrum workflow 보조 기능을 제공하는
ComfyUI 커스텀 노드팩입니다.

이 패키지는 `comfyui-naia-bridge`와 독립적으로 동작합니다. 해당 노드팩을
import하거나 덮어쓰지 않으므로, 두 노드팩을 동시에 설치할 수 있습니다.

참고 기준:

- `DNT-LAB/comfyui-naia-bridge` master `b82f98e`
- 사용하는 NAIA API endpoint:
  - `POST /api/comfyui/random`
  - `peng_override` 요청 필드

Registry 기준 외부 연동 기본값:

- NAIA 호출은 선택 기능입니다. 기본 host는 `127.0.0.1`이며, 로컬이 아닌
  host는 `EasyUse Anima -> NAIA -> 원격 API 허용`을 켜야만 사용할 수
  있습니다.
- 프롬프트 번역 기본값은 OFF입니다. Google 번역은 명시적으로 선택해야 하며,
  이 노드팩은 환경 변수에서 API key를 자동으로 읽지 않습니다.
- AiO SAM3 detailer 경로는 ComfyUI 내장 SAM3 detector와 Impact Pack class를
  명시적 선택 import로만 사용합니다. 사용자가 지정한 module 이름을 동적으로
  load하지 않습니다.

## 문서 진입점

- 노드별 상세 설명: [노드 문서](docs/nodes/README.ko.md)
- 와일드카드 문법과 예시: [와일드카드 가이드](docs/wildcards.ko.md)
- 자동완성 CSV 선택 기준: [자동완성 CSV 가이드](docs/autocomplete-csv.ko.md)
- 예시 워크플로우: [docs/example_workflows](docs/example_workflows/)
- ANIMA Easy Use workflow v1: [사용 가이드](docs/Anima%20AiO/ANIMA_Easy_Use_workflow_v1_KO.md) / [English guide](docs/Anima%20AiO/ANIMA_Easy_Use_workflow_v1_EN.md) / [workflow JSON](docs/example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json)
- 버전별 변경 사항: [RELEASE.md](RELEASE.md)

## 주요 기능

| 영역 | 설명 |
| --- | --- |
| 자동완성 | 한국어 Danbooru 태그 자동완성, 와일드카드 자동완성, 전용 노드 인라인 미리보기, 적용 범위 설정을 제공합니다. |
| 프롬프트 교정 | Simple 교정기는 프롬프트 하나를 ANIMA 문법에 맞게 정리하고, Prompt Studio 계열은 field 편집, 하이라이트, prompt data 출력을 함께 제공합니다. |
| NAIA 연동 | NAIA에서 prompt, negative prompt, 해상도를 받아 Prompt Studio에 반영하고, 저장된 workflow만으로도 같은 prompt data를 재사용할 수 있게 합니다. |
| 와일드카드 | Impact Pack 계열 문법과 호환되는 wildcard 확장, 순차 선택, `__wildcard__` 자동완성을 제공합니다. |
| LoRA 프리셋 | 스타일 프롬프트와 LoRA stack을 프로필로 저장하고, trigger word와 LoRA metadata를 workflow 안에서 관리하기 쉽게 만듭니다. |
| 호환성 노드 | Detailer crop 크기를 32배수로 정렬하거나, Highres용 이미지 크기를 유효 배율로 맞추는 보조 노드를 제공합니다. |
| AiO 생성 | `Easy Use Anima Input`과 `Anima AiO Generator`로 모델 선택, 1차 샘플링, Highres, Detailer, Preview, Save를 하나의 흐름으로 묶습니다. |

## 데모 영상

### 자동완성

<video src="https://github.com/n0va39/ComfyUI-EasyUseAnima/raw/main/docs/assets/videos/easyuse-anima-autocomplete.mp4" controls muted loop playsinline width="720"></video>

[자동완성 데모 열기](docs/assets/videos/easyuse-anima-autocomplete.mp4)

### NAIA 프롬프트 반영

<video src="https://github.com/n0va39/ComfyUI-EasyUseAnima/raw/main/docs/assets/videos/easyuse-anima-naia-fill.mp4" controls muted loop playsinline width="720"></video>

[NAIA 데모 열기](docs/assets/videos/easyuse-anima-naia-fill.mp4)

### 와일드카드 자동완성

<video src="https://github.com/n0va39/ComfyUI-EasyUseAnima/raw/main/docs/assets/videos/easyuse-anima-wildcard-autocomplete.mp4" controls muted loop playsinline width="720"></video>

[와일드카드 데모 열기](docs/assets/videos/easyuse-anima-wildcard-autocomplete.mp4)

## 빠른 가이드: Anima AiO 생성 흐름

`Anima AiO Generator`는 prompt data context를 받아 1차 샘플링, Highres,
Detailer, 미리보기, 이미지 저장을 한 노드에서 처리합니다. 프롬프트 작성은
`Anima Prompt Studio Advanced v2`와 `Easy Use Anima Input`에서 끝내고, 생성
노드에는 생성 관련 설정만 남기는 구조입니다.

기본 연결:

1. `Anima Prompt Studio Advanced v2`의 `EASYUSE_ANIMA_PROMPT_DATA`를 `Easy Use Anima Input`에 연결합니다.
2. `Easy Use Anima Input`에서 ANIMA diffusion model, VAE, CLIP을 각각 선택합니다.
3. `Easy Use Anima Input` 출력을 `Anima AiO Generator`의 `easy use anima input`에 연결합니다.
4. LoRA를 같이 쓰면 `Anima LoRA Preset`의 `LORA_STACK`을 `lora_stack`에 연결합니다.

기본 노드 화면에서는 seed, steps, CFG, shift, denoise, sampler, scheduler,
Highres, Detailer, Preview, Save만 조작합니다. 모델 패치와 최적화는
`Advanced Options`, 저장 메타데이터는 `Save Options`, 이미지 비교와 피드는
Preview 설정에서 관리합니다. 저장은 기본 ON이며, Image Saver를 사용하면
workflow embed와 Civitai/LoRA metadata 저장까지 한 번에 처리할 수 있습니다.

자세한 설정 기준: [Anima AiO Generator 문서](docs/nodes/anima-aio-generator.ko.md)

배포용 간단 워크플로우:
[ANIMA_Easy_Use_workflow_v1_release_ko.json](docs/example_workflows/ANIMA_Easy_Use_workflow_v1_release_ko.json)
/
[사용 가이드](docs/Anima%20AiO/ANIMA_Easy_Use_workflow_v1_KO.md)

## 빠른 가이드: Artist Mix Conditioning

`Anima Artist Mix Conditioning`은 Prompt Data 없이도 일반 prompt와 별도
`artist_tags` 입력으로 artist mix positive `CONDITIONING`을 만드는 단독
노드입니다. Prompt Studio Advanced v2를 쓰지 않는 간단한 workflow나,
작가 태그 conditioning만 따로 실험할 때 사용합니다.

처음에는 `artist_position=correct`를 유지하고 `artist_mix_mode`는 `prompt`
또는 `average`로 시작하는 것이 안전합니다. 여러 작가의 영향 분리가 필요하면
`hybrid`, 작가 수가 적고 분리도가 더 중요하면 `exact`를 사용합니다. 튜닝
파라미터는 강도를 올리기 전에 branch 비용이 늘어나는 모드인지 먼저 확인하는
것이 좋습니다.

자세한 모드 설명: [Anima Artist Mix Conditioning 문서](docs/nodes/anima-artist-mix-conditioning.ko.md)

## 노드

| 노드 | 카테고리 | 요약 |
| --- | --- | --- |
| [Anima NAIA Random Prompt](docs/nodes/anima-naia-random-prompt.ko.md) | `NAIA Bridge/API` | NAIA remote API에서 prompt, negative prompt, 해상도를 받습니다. |
| [Anima Prompt Corrector](docs/nodes/anima-prompt-corrector.ko.md) | `EasyUse Anima/Prompt` | 쉼표 프롬프트를 ANIMA 순서로 정규화하고 JSON report를 반환합니다. |
| [Anima Prompt Corrector Simple](docs/nodes/anima-prompt-corrector.ko.md#simple-버전) | `EasyUse Anima/Prompt` | 프롬프트 하나를 받아 교정된 프롬프트 하나만 출력합니다. |
| [Anima Prompt Builder](docs/nodes/anima-prompt-builder.ko.md) | `EasyUse Anima/Prompt` | 여러 프롬프트 필드를 조합하고 AMG용 quality 출력을 분리합니다. |
| [Anima Prompt Studio](docs/nodes/anima-prompt-studio.ko.md) | `EasyUse Anima/Prompt` | Prompt Builder에 UI 편집, 자동완성, 하이라이트를 추가합니다. |
| [Anima Prompt Studio Advanced](docs/nodes/anima-prompt-studio-advanced.ko.md) | `EasyUse Anima/Prompt` | positive/negative field, NAIA, 해상도, 와일드카드 제어를 포함합니다. |
| [Anima Prompt Studio Advanced v2](docs/nodes/anima-prompt-studio-advanced.ko.md) | `EasyUse Anima/Prompt` | `EASYUSE_ANIMA_PROMPT_DATA` dict 출력으로 downstream 노드가 key 기반으로 값을 읽게 합니다. |
| [EASYUSE_ANIMA_PROMPT_DATA](docs/nodes/anima-prompt-studio-advanced.ko.md) | `EasyUse Anima/Prompt` | prompt data를 통과시키고 필요한 호환 출력으로 펼칩니다. |
| [Anima Prompt Data Conditioning](docs/nodes/anima-prompt-studio-advanced.ko.md) | `EasyUse Anima/Prompt` | prompt data에서 conditioning, 모델 패치, latent image를 생성합니다. |
| [Anima Artist Mix Conditioning](docs/nodes/anima-artist-mix-conditioning.ko.md) | `EasyUse Anima/Prompt` | 일반 prompt와 별도 artist_tags 입력으로 artist mix positive CONDITIONING을 출력합니다. |
| [Anima Wildcard](docs/nodes/anima-wildcard.ko.md) | `EasyUse Anima/Prompt` | Prompt Studio 없이 와일드카드 문자열만 확장합니다. |
| [Anima LoRA Preset](docs/nodes/anima-lora-preset.ko.md) | `EasyUse Anima/LoRA` | LoRA profile, style prompt, trigger word를 저장하고 출력합니다. |
| [Easy Use Anima Input](docs/nodes/anima-aio-generator.ko.md) | `EasyUse Anima/AiO` | prompt data와 ANIMA diffusion model, VAE, CLIP 선택을 AiO 전용 context로 묶습니다. |
| [Anima AiO Generator](docs/nodes/anima-aio-generator.ko.md) | `EasyUse Anima/AiO` | prompt data context를 받아 샘플링, Highres, Detailer, 미리보기, 저장을 한 노드에서 실행합니다. |
| [Anima Image Scale By Multiple](docs/nodes/anima-image-scale-by-multiple.ko.md) | `EasyUse Anima/Image` | 원본 비율을 유지하면서 Highres에 안전한 유효 배율과 크기 배수로 이미지를 확대합니다. |
| [Anima Detailer Align Hook](docs/nodes/anima-detailer-align-hook.ko.md) | `EasyUse Anima/Detailer` | Impact detailer crop sampling 크기를 지정 배수로 정렬합니다. |

## 공통 프론트엔드 기능

자동완성:

- Prompt Builder, Prompt Corrector, Prompt Studio, Prompt Studio Advanced,
  일반 multiline `STRING` prompt/text widget에서 bundled Danbooru, e621,
  Danbooru+e621 병합, 한국어 Danbooru autocomplete CSV를 사용할 수 있습니다.
- 자동완성 적용 범위는 ComfyUI Settings에서 `off`, `easyuse_nodes`,
  `compatible_global` 중 선택합니다.
- 자동완성과 Prompt Studio 하이라이트에 사용할 CSV는 ComfyUI Settings의
  `EasyUse Anima: Autocomplete CSV`에서 선택할 수 있습니다.
- `__` 또는 `__partial`을 입력하면 와일드카드 자동완성이 열리고,
  `__relative/key__` 형식으로 삽입합니다.
- 자동완성 인라인 미리보기를 켜면 선택 후보를 적용했을 때 들어갈 나머지
  텍스트가 입력칸 하이라이트 위에 ghost text처럼 표시됩니다.
- 닫는 괄호 미리입력을 켜면 `(`, `[`, `{` 같은 여는 괄호 입력 시 닫는
  괄호를 커서 오른쪽에 넣어 편집기처럼 사용할 수 있습니다.
- 자세한 CSV 선택 기준과 포맷은
  [자동완성 CSV 가이드](docs/autocomplete-csv.ko.md)를 참고하세요.

Prompt Studio 하이라이트:

- quality, safety/rating, year, count, character, artist, copyright, metadata,
  learned general tag, natural language, syntax error, unknown tag를 구분해
  표시합니다.
- 와일드카드 문법은 일반 태그와 별도의 색상으로 표시하며, Settings에서 색상을
  변경할 수 있습니다.
- `(tag:1.2)` 프롬프트 가중치와 `[[artist_a, artist_b:0.7]]` Artist Mix
  그룹은 설정에서 밑줄 표시를 켤 수 있습니다.
- `(@artist name)` 또는 `(highres, long hair)`처럼 가중치 없이 괄호로 감싼
  태그도 내부 태그 기준으로 분류하고 색상을 표시합니다.

ComfyUI Settings:

- NAIA 요청 host, port, Prompt Engineering option, preprocessing option을
  EasyUse Anima settings panel에서 설정합니다.
- NAIA 요청은 기본적으로 localhost에만 허용됩니다. 신뢰하는 원격 NAIA
  endpoint를 사용할 때만 `원격 API 허용`을 켜세요.
- EasyUse Anima는 별도 언어 설정을 저장하지 않습니다. 노드 정보, 입력/출력
  힌트, 설정창, 커스텀 DOM 버튼과 툴팁은 ComfyUI 기본 언어 설정을 따릅니다.
- Prompt metadata filter word는 metadata prompt output에만 적용됩니다.
- Prompt Studio 오타 표시와 카테고리/와일드카드 색상을 수동으로 변경할 수
  있습니다.
- Prompt Studio 자동완성 미리보기, 닫는 괄호 미리입력, 가중치 문법 밑줄
  표시를 켜거나 끌 수 있습니다.
- Prompt Studio는 NAIA field 위쪽 general field를 자동 토글할 수 있습니다.
- Wildcard extra paths는 항목 추가 방식으로 기존 사용자 와일드카드 폴더를
  등록합니다.
- LoRA Preset row label은 파일명만 표시하거나 전체 경로로 표시할 수 있습니다.

## 요구 사항

NAIA는 `comfyui-naia-bridge`가 사용하는 ComfyUI API를 노출해야 합니다.
기본 권장 endpoint는 localhost이며, 원격 NAIA endpoint는 `원격 API 허용`
설정이 켜져 있어야 사용할 수 있습니다.

AiO Generator의 선택 SAM3 detailer 경로는 실행 시점에 `ComfyUI-Impact-Pack`이
필요합니다. 이것은 Python package dependency가 아니라 ComfyUI custom node
dependency이므로 `pyproject.toml`의 Python dependencies에는 넣지 않습니다.

연동 노드팩:

- [ComfyUI-Spectrum-KSampler](https://github.com/sorryhyun/ComfyUI-Spectrum-KSampler): Spectrum sampler, Mod Guidance, Spectrum/DCW 계열 모델 패치에 사용합니다. 최신 버전을 권장합니다.
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes): Torch Compile, SageAttention 등 최적화 옵션에 사용합니다.
- [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack): Impact detailer, AiO SAM3 detailer 흐름에 필요합니다.
- [ComfyUI-Lora-Manager](https://github.com/willmiao/ComfyUI-Lora-Manager): LoRA trigger word와 metadata 관리에 권장합니다.
- [ComfyUI-Image-Saver](https://github.com/alexopus/ComfyUI-Image-Saver): AiO Save Options에서 workflow embed, Civitai/LoRA metadata 저장에 사용합니다.
- [ComfyUI-Anima-DAVE](https://github.com/sorryhyun/ComfyUI-Anima-DAVE): 생성 다양성을 위한 선택 model patch입니다.

Python dependency 설치:

```bash
pip install -r requirements.txt
```

노드팩 설치 또는 업데이트 후 ComfyUI를 재시작해야 합니다.

## 설치

`ComfyUI/custom_nodes` 아래에 clone합니다.

```bash
git clone https://github.com/n0va39/ComfyUI-EasyUseAnima
```

ComfyUI Python 환경에서 dependency를 설치합니다.

```bash
pip install -r ComfyUI-EasyUseAnima/requirements.txt
```

설치 후 ComfyUI를 재시작합니다.

설정값, LoRA 프리셋 프로필, 기본 와일드카드 폴더는 커스텀 노드 설치 폴더가
아니라 ComfyUI 사용자 데이터 디렉토리에 저장됩니다. 따라서 Manager 업데이트나
git 재설치로 노드팩 폴더가 바뀌어도 사용자 데이터가 유지됩니다.

## ComfyUI Manager / Registry

이 저장소는 향후 Comfy Registry 등록을 위한 `pyproject.toml` metadata를 포함합니다.
Registry node id는 `comfyui-easyuse-anima`입니다.

Registry에 publish하기 전에 `[tool.comfy].PublisherId`가 실제 Comfy Registry
publisher id와 일치하는지 확인해야 합니다.
