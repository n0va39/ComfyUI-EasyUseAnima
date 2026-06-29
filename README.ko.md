# ComfyUI EasyUse Anima

언어: [English](README.en.md) | [한국어](README.ko.md) | [Home](README.md)

프롬프트 편집, ANIMA 프롬프트 보정, NAIA 프롬프트 연동, LoRA 프리셋 관리,
그리고 ComfyUI에서 latent-size 오류를 줄이기 위한 ANIMA DiT Detailer Hook을
제공하는 커스텀 노드팩입니다.

이 패키지는 `comfyui-naia-bridge`와 독립적으로 동작합니다. 해당 노드팩을
import하거나 덮어쓰지 않으므로, 두 노드팩을 동시에 설치할 수 있습니다.

참고 기준:

- `DNT-LAB/comfyui-naia-bridge` master `b82f98e`
- 사용하는 NAIA API endpoint:
  - `POST /api/comfyui/random`
  - `peng_override` 요청 필드

## 노드

### Anima NAIA Random Prompt

카테고리: `NAIA Bridge/API`

출력:

- `prompt`
- `negative_prompt`
- `width`
- `height`

주요 기능:

- `use_naia_bridge=false`: NAIA 호출을 비활성화하고 입력받은 `prompt`,
  `negative_prompt`, `width`, `height`를 그대로 반환합니다. 입력이 같다면
  ComfyUI 캐시를 깨지 않습니다.
- `freeze_naia_output=true`: 저장된 출력 캐시가 유효하면 NAIA를 다시 호출하지
  않고 같은 값을 반환합니다. 고정된 출력으로 downstream 캐시를 안정적으로
  유지할 수 있습니다.
- `show_preview=false`: 큰 읽기 전용 미리보기 위젯을 숨깁니다.
- 저장 이미지 워크플로우 재현: 새 NAIA 응답을 받은 뒤 저장 이미지 metadata에
  `freeze_naia_output=true`와 캐시된 출력값을 기록합니다. 해당 워크플로우를
  다시 불러오면 NAIA를 다시 호출하지 않고 같은 출력을 재현합니다.
- `use_naia_settings=false`: 현재 노드의 `pre_prompt`, `post_prompt`,
  `auto_hide`, 전처리 옵션을 NAIA 요청에 보냅니다.

`remove_*` 전처리 옵션은 advanced input으로 표시됩니다.

### Anima Prompt Corrector

카테고리: `EasyUse Anima/Prompt`

출력:

- `corrected_prompt`
- `report`

쉼표로 구분된 프롬프트를 받아 ANIMA 순서로 정규화된 프롬프트와 JSON report를
반환합니다. 노드팩 내부에 vendoring된 `anima_prompt` MVP 코어를 사용하며,
외부 character/artist export에 의존하지 않습니다.

주요 입력:

- `artist_overrides`: 쉼표 또는 줄바꿈으로 구분한 수동 작가 트리거입니다.
- `artist_exclusions`: 작가로 취급하지 않을 태그입니다.

프롬프트 문법:

- escape되지 않은 괄호는 가중치 문법으로 취급하며 보존합니다.
  예: `(long_hair:1.2)`
- 태그 이름에 들어가는 literal 괄호는 `\(`, `\)` 형태로 escape합니다.
- escape되지 않은 가중치 괄호 안의 쉼표는 최상위 태그 구분자로 나누지
  않습니다.
- 자연어 프롬프트는 기존 대소문자를 유지합니다.
- 자연어 문장 바로 뒤에 `1girl` 같은 인원수 태그가 오면 해당 태그를 분리해
  정상적으로 재정렬합니다.

### Anima Prompt Builder

카테고리: `EasyUse Anima/Prompt`

출력:

- `prompt`
- `anima_mod_guidance_quality_tags`
- `use_anima_mod_guidance`
- `metadata_prompt`

NAIA와 Anima Mod Guidance 워크플로우를 위해 여러 입력칸을 조합해 정리된
프롬프트를 만듭니다.

입력 필드:

- `lora_trigger_tags`: LoRA Manager 등에서 받는 한 줄 trigger tag입니다.
- `quality_tags`: 앞쪽에 배치할 quality tag입니다.
- `trigger_and_artist_tags`: 수동 모델 trigger 및 `@artist` 태그입니다.
- `prompt`: 본문 프롬프트입니다. NAIA 출력이 들어오는 공간으로 사용할 수
  있습니다.
- `trailing_quality_tags`: 뒤쪽에 붙일 quality 또는 style tag입니다.

동작:

- 줄바꿈은 쉼표 구분자로 처리합니다.
- 빈 쉼표 그룹과 중복 공백을 정리합니다.
- 조합된 프롬프트는 ANIMA prompt ordering을 거칩니다.
- `use_anima_mod_guidance=true`: `prompt` 출력에서 quality field를 제외하고,
  quality field는 `anima_mod_guidance_quality_tags`로 반환합니다.
- `metadata_prompt`는 AMG 모드와 무관하게 quality field를 포함합니다.
- `pin_trigger_tags_to_front=true`: trigger field를 quality tag 앞쪽에 고정합니다.
  false인 경우 leading quality tag 뒤에 배치됩니다.

### Anima Prompt Studio

카테고리: `EasyUse Anima/Prompt`

`Anima Prompt Builder`와 같은 출력 및 프롬프트 조합 동작을 사용하지만, 노드
UI에서 편집하기 위한 기능을 추가한 버전입니다.

- LoRA trigger 입력칸이 노드 상단에 배치됩니다.
- 프롬프트 입력칸의 높이를 노드 안에서 조절할 수 있습니다.
- 텍스트 입력칸에 태그 자동완성과 카테고리별 하이라이트가 적용됩니다.
- 외부 연결로 받은 텍스트도 워크플로우 실행 후 미리보기/하이라이트에
  반영됩니다.
- 입력한 텍스트는 워크플로우 저장에 포함됩니다.

### Anima Prompt Studio Advanced

카테고리: `EasyUse Anima/Prompt`

출력:

- `positive_prompt`
- `negative_prompt`
- `anima_mod_guidance_quality_tags`
- `use_anima_mod_guidance`
- `metadata_prompt`
- `metadata_negative_prompt`
- `width`
- `height`

큰 워크플로우를 위한 확장형 Prompt Studio 노드입니다.

화면 예시:

**Advanced 노드 전체 화면**
출력 소켓, 프롬프트 필드, 해상도 설정, positive/negative prompt 영역이 함께
보이는 전체 배치입니다.

![Anima Prompt Studio Advanced 전체 화면](docs/images/prompt-studio-advanced-overview.png)

**입력과 상단 설정**
주요 입력 소켓, `mod guidance` 토글, 해상도 버켓 선택, 프롬프트 필드 조작
버튼을 보여줍니다.

![Anima Prompt Studio Advanced 입력과 상단 설정](docs/images/prompt-studio-advanced-controls.png)

**NAIA 프롬프트 필드**
NAIA 응답으로 프롬프트를 채우고, 저장된 결과를 워크플로우에서 다시 수정 및
재현할 수 있는 필드입니다.

![Anima Prompt Studio Advanced NAIA 필드](docs/images/prompt-studio-advanced-naia.png)

**해상도 버켓 선택**
버켓과 해상도 선택 UI입니다. 저장 워크플로우 재현을 위한 `NAIA`와 `Custom`
모드도 포함합니다.

![Anima Prompt Studio Advanced 해상도 버켓 선택](docs/images/prompt-studio-advanced-resolution.png)

필드 구조:

- positive prompt와 negative prompt를 별도 field group으로 편집합니다.
- field는 추가, 삭제, 순서 변경, 활성화, 비활성화할 수 있습니다.
- positive field type은 quality, artist, trigger, general, NAIA를 지원합니다.
  negative prompt에도 NAIA field를 1개 추가할 수 있습니다.
- negative field도 가능한 범위에서 같은 prompt correction 및 metadata 흐름을
  사용합니다.
- NAIA field는 마지막 NAIA 결과를 워크플로우에 저장하며, 채워진 뒤에도 직접
  수정할 수 있습니다.
- trigger field는 연결된 `trigger_words` 입력을 표시할 수 있고, 실행 후에도
  직접 수정할 수 있습니다. front 고정 또는 ANIMA ordering 적용을 선택할 수
  있습니다.
- latent image 해상도 선택은 `mod guidance` 바로 아래에 표시됩니다. 첫 칸은
  bucket, 두 번째 칸은 `width * height (ratio)` 형식의 해상도이며, 비율
  오름차순으로 정렬됩니다.
- 해상도 bucket은 각 bucket 값의 제곱 픽셀 면적에 가까운 해상도를 묶습니다.
  (`512`, `768`, `896`, `1024`, `1280`, `1536`) 32배수 해상도만 노출하며,
  가로/세로 반전 쌍은 같은 bucket에 함께 둡니다.
- `Custom` bucket에서는 width와 height를 직접 입력할 수 있습니다. Custom
  값은 워크플로우에 저장되며, 호환성을 위해 32배수로 보정됩니다.
- `NAIA` bucket은 prompt field를 채우는 것과 같은 NAIA 응답에서 width와
  height를 가져옵니다. 저장 이미지 워크플로우에는 이 해상도를 `Custom`으로
  저장합니다.

NAIA 동작:

- `Fill from NAIA`가 켜져 있으면 queue 실행 때마다 NAIA에서 새 프롬프트를
  받아 NAIA field를 채웁니다.
- positive NAIA, negative NAIA, NAIA 해상도는 queue 1회당 NAIA 요청 1번만
  공유해서 사용합니다.
- 저장 이미지 워크플로우에는 채워진 텍스트를 저장하고 요청 flag를 off로
  저장합니다. 다시 불러온 워크플로우는 저장된 결과를 재사용합니다.
- 설정에서 NAIA field 위쪽의 general field를 자동으로 off/on 하는 옵션을
  사용할 수 있습니다. 이 동작은 NAIA field 자체의 on/off 상태를 기준으로
  합니다.

하이라이트 및 문법:

- quality, safety/rating, year, count, character, artist, copyright, metadata,
  learned general tag, natural language, syntax error, unknown tag가 서로 다른
  색으로 표시됩니다.
- 하이라이트 색상 설정은 `Anima Prompt Studio`와 공유됩니다.
- `\(`, `\)`처럼 escape된 literal prompt 문자는 일반 태그 텍스트로 취급하며
  오타로 표시하지 않습니다.
- `(score_8:0.65)` 같은 가중치 문법은 태그 텍스트와 가중치 숫자만 표시합니다.
  괄호와 `:`는 하이라이트하지 않습니다.
- `(highres, absurdres, very aesthetic:0.8)`처럼 쉼표로 구분된 가중치 그룹은
  내부 태그를 각각 분류합니다.
- 닫히지 않은 괄호는 syntax error로 표시됩니다.
- 긴 프롬프트는 개별 textarea 내부 스크롤바가 아니라 Advanced editor 전체
  스크롤로 처리됩니다. textarea는 현재 텍스트 줄 수에 맞춰 높이를 유지하므로
  스크롤바가 하이라이트나 글자를 덮지 않습니다.
- 하이라이트 overlay는 입력칸의 font family, size, spacing, wrapping 관련
  설정을 따라가도록 동기화됩니다.

### Anima LoRA Preset

카테고리: `EasyUse Anima/LoRA`

출력:

- `style_prompt`
- `LORA_STACK`
- `trigger_words`
- `active_loras`
- `profile_index`

ANIMA 워크플로우에서 재사용할 LoRA/style profile을 저장하는 노드입니다.

화면 예시:

**LoRA Preset 노드**
선택된 LoRA, strength, 활성화 상태, trigger word 출력, profile 저장/불러오기
컨트롤을 보여줍니다.

![Anima LoRA Preset 노드](docs/images/lora-preset-node.png)

**LoRA 검색**
ComfyUI LoRA 경로를 folder-tree로 보고, 검색해서 LoRA를 선택하는 화면입니다.

![Anima LoRA Preset LoRA 검색](docs/images/lora-preset-search.png)

**Profile 불러오기**
노드팩 내부 profile 폴더에 저장된 profile을 불러와 새 profile로 추가하는
화면입니다.

![Anima LoRA Preset profile 불러오기](docs/images/lora-preset-profile-load.png)

주요 동작:

- 한 노드 안에 여러 profile을 저장할 수 있습니다.
- `profile_index`는 수동 또는 input으로 제어할 수 있습니다. profile 개수를
  넘는 index는 전체 개수 기준으로 wrap됩니다.
- profile은 style prompt, 선택한 LoRA, LoRA strength, 활성화 상태를
  워크플로우에 저장합니다.
- profile은 `easyuse_anima`용 ComfyUI 사용자 데이터 디렉토리 아래 JSON 파일로
  저장하고 불러올 수 있습니다.
- 저장된 profile을 불러오면 현재 profile을 덮어쓰지 않고 새 profile로
  추가합니다.

LoRA UI:

- `Add LoRA`는 ComfyUI LoRA 경로 기반 folder-tree chooser를 엽니다.
- chooser에서 검색할 수 있습니다.
- 선택한 LoRA는 rgthree Power Lora Loader와 유사한 compact list로 표시됩니다.
- 각 row는 enable/disable, strength 조절, 우클릭 또는 menu button을 통한
  move up, move down, remove를 지원합니다.
- `i` preview button은 LoRA 파일 근처의 같은 이름 preview image를 찾습니다.
  예: `.webp` preview
- ComfyUI Settings에서 row label을 파일명만 표시할지, 전체 상대 경로로
  표시할지 선택할 수 있습니다.

Trigger words:

- LoRA Manager 방식 metadata JSON sidecar가 있으면 trigger word를 읽습니다.
- trigger word는 중복 제거 후 쉼표로 구분된 문자열로 출력되어 Prompt Studio
  trigger field에 연결할 수 있습니다.

### Anima Detailer Align Hook

카테고리: `EasyUse Anima/Detailer`

출력:

- `detailer_hook`

Impact Pack과 호환되는 `DETAILER_HOOK`을 만들어 Impact detailer의 crop
sampling 크기를 정렬합니다. Impact `DetailerForEach` 또는 Impact 호환 SEGS
detailer의 `detailer_hook` 입력에 연결합니다.

주요 동작:

- `alignment=32`는 crop sampling width/height를 32배수로 올림 보정합니다.
  ANIMA/Spectrum 워크플로우에서 16채널 VAE나 특수 VAE 경로가 32배수가 아닌
  crop 크기에서 실패하는 문제를 줄이기 위한 옵션입니다.
- 기존 `detailer_hook`을 연결하면 기존 hook 동작을 먼저 실행한 뒤 크기
  정렬을 적용합니다.
- `alignment=none`은 Impact Pack 원본 crop 크기를 유지합니다.

### Anima SAM3 Detailer

카테고리: `EasyUse Anima/Detailer`

SAM3 기반 Impact Pack detailer workflow를 편하게 쓰기 위한 노드입니다.
`Anima SAM3 Detailer`는 ComfyUI native SAM3 detection, Impact `MaskToSEGS`,
Impact Pack `DetailerForEach`를 연결합니다.

이 노드는 실행 시점에 `ComfyUI-Impact-Pack`이 필요합니다. 의존성은 노드 실행
시점에 확인하므로 Impact Pack이 없어도 EasyUse Anima의 다른 노드 import는
실패하지 않습니다.

## 공통 프론트엔드 기능

자동완성:

- Prompt Builder, Prompt Corrector, Prompt Studio, Prompt Studio Advanced,
  일반 multiline `STRING` prompt/text widget에서 bundled Korean Danbooru
  autocomplete를 사용할 수 있습니다.
- 자동완성 적용 범위는 ComfyUI Settings에서 `off`, `easyuse_nodes`,
  `compatible_global` 중 선택합니다.
  - `off`: EasyUse Anima 자동완성과 API 요청을 끕니다.
  - `easyuse_nodes`: EasyUse Anima 프롬프트 노드에만 적용합니다.
  - `compatible_global`: 기본값이며 기존처럼 호환 가능한 일반 prompt/text
    widget에도 적용합니다.
- 자동완성과 Prompt Studio 하이라이트에 사용할 CSV는 ComfyUI Settings의
  `EasyUse Anima: Autocomplete CSV`에서 선택할 수 있습니다.
- 영어 태그 또는 설명/키워드의 한국어 단어를 입력한 뒤 방향키와 Enter/Tab으로
  suggestion을 삽입합니다.
- LoRA Manager / Lora Stacker처럼 자체 LoRA/autocomplete widget을 가진 노드나
  입력칸은 제외됩니다.

포함된 autocomplete CSV:

- 기본값: `danbooru_tags_classified.csv`
- `KR_danbooru_tags_with_description v3_modified.csv`: 제작자 허가를 받아 포함
- `danbooru_tags_classified.csv`: `Localsmile/danbooru_KR_wiki_tag_search` 기반

자세한 CSV 선택 기준, 검색 방식, 개발자용 CSV 포맷은
[자동완성 CSV 가이드](docs/autocomplete-csv.ko.md)를 참고하세요.

ComfyUI Settings:

- NAIA 요청 host, port, Prompt Engineering option, preprocessing option은
  EasyUse Anima settings panel에서 설정합니다.
- EasyUse Anima는 별도 언어 설정을 저장하지 않습니다. 노드 정보, 입력/출력
  힌트, 설정창, 커스텀 DOM 버튼과 툴팁은 ComfyUI 기본 언어 설정을 따릅니다.
- Prompt metadata filter word는 metadata prompt output에만 적용됩니다.
- Prompt Studio 오타 표시와 카테고리 색상을 수동으로 변경할 수 있습니다.
- Prompt Studio는 NAIA field 위쪽 general field를 자동 토글할 수 있습니다.
- LoRA Preset row label은 파일명만 표시하거나 전체 경로로 표시할 수 있습니다.

## 릴리즈 노트

버전별 변경 사항은 [RELEASE.md](RELEASE.md)를 참고하세요.

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

설정값과 LoRA 프리셋 프로필은 커스텀 노드 설치 폴더가 아니라
`folder_paths.get_system_user_directory("easyuse_anima")`로 얻은 ComfyUI 사용자
데이터 디렉토리에 저장됩니다. 따라서 Manager 업데이트나 git 재설치로 노드팩
폴더가 바뀌어도 사용자 데이터가 유지됩니다.

## ComfyUI Manager / Registry

이 저장소는 향후 Comfy Registry 등록을 위한 `pyproject.toml` metadata를 포함합니다.
Registry node id는 `comfyui-easyuse-anima`입니다.

Registry에 publish하기 전에 `[tool.comfy].PublisherId`가 실제 Comfy Registry
publisher id와 일치하는지 확인해야 합니다.
