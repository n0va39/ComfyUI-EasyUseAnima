# ComfyUI EasyUse Anima

언어: [English](README.en.md) | [한국어](README.ko.md) | [Home](README.md)

프롬프트 편집, ANIMA 프롬프트 보정, NAIA 프롬프트 연동, LoRA 프리셋 관리,
와일드카드 확장, ANIMA/Spectrum workflow용 detailer 보조 노드를 제공하는
ComfyUI 커스텀 노드팩입니다.

이 패키지는 `comfyui-naia-bridge`와 독립적으로 동작합니다. 해당 노드팩을
import하거나 덮어쓰지 않으므로, 두 노드팩을 동시에 설치할 수 있습니다.

참고 기준:

- `DNT-LAB/comfyui-naia-bridge` master `b82f98e`
- 사용하는 NAIA API endpoint:
  - `POST /api/comfyui/random`
  - `peng_override` 요청 필드

## 문서 진입점

- 노드별 상세 설명: [노드 문서](docs/nodes/README.ko.md)
- 와일드카드 문법과 예시: [와일드카드 가이드](docs/wildcards.ko.md)
- 자동완성 CSV 선택 기준: [자동완성 CSV 가이드](docs/autocomplete-csv.ko.md)
- 예시 워크플로우: [docs/example_workflows](docs/example_workflows/)
- 버전별 변경 사항: [RELEASE.md](RELEASE.md)

## 노드

| 노드 | 카테고리 | 요약 |
| --- | --- | --- |
| [Anima NAIA Random Prompt](docs/nodes/anima-naia-random-prompt.ko.md) | `NAIA Bridge/API` | NAIA remote API에서 prompt, negative prompt, 해상도를 받습니다. |
| [Anima Prompt Corrector](docs/nodes/anima-prompt-corrector.ko.md) | `EasyUse Anima/Prompt` | 쉼표 프롬프트를 ANIMA 순서로 정규화하고 JSON report를 반환합니다. |
| [Anima Prompt Builder](docs/nodes/anima-prompt-builder.ko.md) | `EasyUse Anima/Prompt` | 여러 프롬프트 필드를 조합하고 AMG용 quality 출력을 분리합니다. |
| [Anima Prompt Studio](docs/nodes/anima-prompt-studio.ko.md) | `EasyUse Anima/Prompt` | Prompt Builder에 UI 편집, 자동완성, 하이라이트를 추가합니다. |
| [Anima Prompt Studio Advanced](docs/nodes/anima-prompt-studio-advanced.ko.md) | `EasyUse Anima/Prompt` | positive/negative field, NAIA, 해상도, 와일드카드 제어를 포함합니다. |
| [Anima Artist Mix Conditioning](docs/nodes/anima-artist-mix-conditioning.ko.md) | `EasyUse Anima/Prompt` | 일반 prompt와 별도 artist_tags 입력으로 artist mix positive CONDITIONING을 출력합니다. |
| [Anima Wildcard](docs/nodes/anima-wildcard.ko.md) | `EasyUse Anima/Prompt` | Prompt Studio 없이 와일드카드 문자열만 확장합니다. |
| [Anima LoRA Preset](docs/nodes/anima-lora-preset.ko.md) | `EasyUse Anima/LoRA` | LoRA profile, style prompt, trigger word를 저장하고 출력합니다. |
| [Anima Detailer Align Hook](docs/nodes/anima-detailer-align-hook.ko.md) | `EasyUse Anima/Detailer` | Impact detailer crop sampling 크기를 지정 배수로 정렬합니다. |
| [Anima SAM3 Context](docs/nodes/anima-sam3-context.ko.md) | `EasyUse Anima/Detailer` | SAM3 checkpoint를 rgthree-compatible context로 로드합니다. |
| [Anima SAM3 Detailer](docs/nodes/anima-sam3-detailer.ko.md) | `EasyUse Anima/Detailer` | SAM3 text detection, Impact MaskToSEGS, DetailerForEach를 연결합니다. |

## 공통 프론트엔드 기능

자동완성:

- Prompt Builder, Prompt Corrector, Prompt Studio, Prompt Studio Advanced,
  일반 multiline `STRING` prompt/text widget에서 bundled Korean Danbooru
  autocomplete를 사용할 수 있습니다.
- 자동완성 적용 범위는 ComfyUI Settings에서 `off`, `easyuse_nodes`,
  `compatible_global` 중 선택합니다.
- 자동완성과 Prompt Studio 하이라이트에 사용할 CSV는 ComfyUI Settings의
  `EasyUse Anima: Autocomplete CSV`에서 선택할 수 있습니다.
- `__` 또는 `__partial`을 입력하면 와일드카드 자동완성이 열리고,
  `__relative/key__` 형식으로 삽입합니다.
- 자세한 CSV 선택 기준과 포맷은
  [자동완성 CSV 가이드](docs/autocomplete-csv.ko.md)를 참고하세요.

Prompt Studio 하이라이트:

- quality, safety/rating, year, count, character, artist, copyright, metadata,
  learned general tag, natural language, syntax error, unknown tag를 구분해
  표시합니다.
- 와일드카드 문법은 일반 태그와 별도의 색상으로 표시하며, Settings에서 색상을
  변경할 수 있습니다.

ComfyUI Settings:

- NAIA 요청 host, port, Prompt Engineering option, preprocessing option을
  EasyUse Anima settings panel에서 설정합니다.
- EasyUse Anima는 별도 언어 설정을 저장하지 않습니다. 노드 정보, 입력/출력
  힌트, 설정창, 커스텀 DOM 버튼과 툴팁은 ComfyUI 기본 언어 설정을 따릅니다.
- Prompt metadata filter word는 metadata prompt output에만 적용됩니다.
- Prompt Studio 오타 표시와 카테고리/와일드카드 색상을 수동으로 변경할 수
  있습니다.
- Prompt Studio는 NAIA field 위쪽 general field를 자동 토글할 수 있습니다.
- Wildcard extra paths는 항목 추가 방식으로 기존 사용자 와일드카드 폴더를
  등록합니다.
- LoRA Preset row label은 파일명만 표시하거나 전체 경로로 표시할 수 있습니다.

## 요구 사항

NAIA는 `comfyui-naia-bridge`가 사용하는 ComfyUI remote API를 노출해야 합니다.

SAM3 detailer 계열 노드는 실행 시점에 `ComfyUI-Impact-Pack`이 필요합니다. 이것은
Python package dependency가 아니라 ComfyUI custom node dependency이므로
`pyproject.toml`의 Python dependencies에는 넣지 않습니다.

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
