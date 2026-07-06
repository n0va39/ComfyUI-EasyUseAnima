# 자동완성 CSV 가이드

EasyUse Anima의 자동완성 CSV는 프롬프트 입력 보조와 Prompt Studio
하이라이트에 사용하는 Danbooru 태그 검색 데이터입니다.

이 CSV는 LoRA 파일, LoRA 트리거, NAIA 결과를 자동 생성하지 않습니다.
LoRA 트리거는 LoRA Preset/LoRA Manager metadata 흐름에서 따로 처리하고,
NAIA 출력은 NAIA 요청 결과를 사용합니다.

## 설정 위치

ComfyUI Settings의 EasyUse Anima 항목에서 다음 값을 설정합니다.

- `자동완성 적용 범위`
- `자동완성 CSV`
- `자동완성 추천 수`
- `자동완성 인라인 미리보기`
- `닫는 괄호 미리입력`

CSV를 변경하면 새 자동완성 요청부터 선택한 CSV가 사용됩니다. 열린
자동완성 팝업은 닫히고 내부 검색 캐시는 초기화됩니다. 브라우저 새로고침은
보통 필요하지 않습니다.

## 자동완성 적용 범위

- `off`
  - EasyUse Anima 자동완성을 전부 끕니다.
  - 자동완성 API 요청을 보내지 않습니다.
- `easyuse_nodes`
  - EasyUse Anima 프롬프트 노드에서만 자동완성을 사용합니다.
  - 일반 multiline `STRING` 위젯에는 붙이지 않습니다.
- `compatible_global`
  - 기본값입니다.
  - EasyUse Anima 노드와 호환 가능한 일반 prompt/text 위젯에 적용합니다.
  - LoRA Manager, LoRA Stacker처럼 자체 자동완성이나 LoRA 전용 입력을 가진
    노드는 제외합니다.

## 포함된 CSV

### `danbooru_2025-09-01.csv`

설정 키: `dbr_danbooru_2025_09_01`

- 기본값이며 대부분의 사용자에게 권장하는 소스입니다.
- `DraconicDragon/dbr-e621-lists-archive` 기반 데이터입니다.
- 원본 라이선스: Unlicense.
- 한국어 설명 없이 최신 Danbooru 태그명과 alias를 포함합니다.
- 비한국어 사용자와 일반 Danbooru 프롬프트 자동완성에 권장합니다.

### `e621_2025-09-01.csv`

설정 키: `dbr_e621_2025_09_01`

- `DraconicDragon/dbr-e621-lists-archive` 기반 데이터입니다.
- 원본 라이선스: Unlicense.
- e621 태그명과 alias를 포함합니다.
- EasyUse Anima는 species/lore 전용 하이라이트 색상을 따로 제공하지 않으므로
  e621 species/lore 카테고리는 기존 학습 태그 색상으로 표시합니다.

### `danbooru_e621_merged_2025-09-01.csv`

설정 키: `dbr_danbooru_e621_merged_2025_09_01`

- `DraconicDragon/dbr-e621-lists-archive` 기반 데이터입니다.
- 원본 라이선스: Unlicense.
- Danbooru와 e621을 하나의 CSV로 합쳐 더 넓은 자동완성 후보를 제공합니다.
- 단일 혼합 소스가 필요할 때만 사용하세요. upstream archive는 병합 포맷이
  future-proof하지 않다고 경고합니다. e621 category 번호를 Danbooru의 invalid
  range로 밀어 넣는 방식이라, 이후 category 변경이 있으면 병합/category 충돌이
  생길 수 있습니다.

### `danbooru_tags_classified.csv`

설정 키: `localsmile_kr_wiki`

- 한국어 검색용 소스입니다.
- `Localsmile/danbooru_KR_wiki_tag_search` 기반 데이터입니다.
- 태그 카테고리 분리가 되어 있어 Prompt Studio 하이라이트와 함께 쓰기 좋습니다.
- 한국어 검색을 우선 사용할 때 권장합니다.

## 검색 방식

자동완성은 다음 값을 검색합니다.

- 영어 태그명
- 태그명의 공백/언더바 변형
- CSV description 또는 wiki 텍스트
- 선택한 CSV에 한국어 텍스트가 포함된 경우 한국어 설명과 키워드

예를 들어 CSV 설명에 `장발`이 들어 있으면 `long hair`를 한국어로 검색할 수
있습니다.

Prompt Studio 하이라이트는 선택한 CSV와 내장 메타 태그 규칙을 함께 사용합니다.
내장 메타/품질 태그는 자동완성 후보로 추가하지 않지만, 오타 판정과 색상 표시에
사용됩니다.

자동완성 인라인 미리보기를 켜면 현재 선택 후보를 적용했을 때 입력될 나머지
글자가 Prompt Studio 하이라이트 overlay에 ghost text로 표시됩니다. 이 옵션이
켜져 있을 때는 커서가 실제 태그 텍스트 위에 있을 때만 후보를 엄격하게
표시하며, 괄호나 쉼표 같은 문법 문자 위에서는 팝업을 열지 않습니다.

닫는 괄호 미리입력은 편집기 보조 기능입니다. 여는 괄호를 입력하면 닫는 괄호를
커서 오른쪽에 넣지만, 자동완성 후보를 적용하는 것만으로 여러 항목을 담는 괄호
그룹을 강제로 닫지는 않습니다.

## 아티스트 태그 정책

아티스트 태그는 CSV의 artist category 데이터로 취급합니다.

- 프롬프트 표기는 `@artist name` 형태를 기준으로 합니다.
- general category 태그를 아티스트 후보로 동시에 취급하지 않습니다.
- 어떤 작가가 general category로 들어 있다면 런타임에서 우회 처리하지 않고,
  CSV 데이터 자체를 수정하거나 올바른 데이터 소스를 선택하는 것이 기준입니다.

## 태그 표기 규칙

- 일반 Danbooru/meta/artist 태그는 프롬프트 출력에서 공백 표기를 기본으로
  사용합니다.
  - 예: `very_aesthetic` -> `very aesthetic`
  - 예: `@artist_name` -> `@artist name`
- Pony score 태그만 예외로 언더바를 유지합니다.
  - 예: `score_9`, `score_8`, `score_7:`
- literal 괄호가 들어간 태그는 자동완성 삽입 시 프롬프트 문법 충돌을 피하도록
  escape합니다.
  - 예: `western comics (style)` -> `western comics \(style\)`

이 규칙은 자동완성 삽입, Prompt Studio 미리보기, 프롬프트 교정 결과가 서로
충돌하지 않도록 맞춰져 있습니다.

## 개발자용 CSV 포맷

현재 설정 UI는 유지보수 중인 번들 CSV를 사용합니다. 사용자 임의 CSV 파일 경로를
UI에서 직접 추가하는 기능은 없습니다.

개발자가 새 source를 코드에 추가할 경우 CSV는 UTF-8 또는 UTF-8 with BOM을
권장합니다. 다음 두 포맷을 읽을 수 있습니다.

헤더 없는 4열 포맷:

```csv
tag,category,count,description
long hair,0,100,"[패션] 긴 머리, 장발"
artist name,1,80,"[작가] 작가 설명"
```

헤더 포함 포맷:

```csv
name,category,post_count,description
long hair,0,100,"[패션] 긴 머리, 장발"
hatsune miku,4,90,"[캐릭터] 하츠네 미쿠"
```

지원하는 category 값:

- `0`: general
- `1`: artist
- `3`: copyright
- `4`: character
- `5`: meta

헤더 포함 포맷에서는 `name` 대신 `tag`, `post_count` 대신 `count`,
`description` 대신 `wiki`도 사용할 수 있습니다.
