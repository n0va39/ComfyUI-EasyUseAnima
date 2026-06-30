# 와일드카드 가이드

EasyUse Anima 와일드카드는 프롬프트 안의 `__name__` 파일 와일드카드와
`{a|b|c}` 동적 프롬프트를 queue 실행 시 확장합니다.

노드별 사용 위치:

- `Anima Prompt Studio Advanced`: `mod guidance` 아래의 와일드카드 제어 영역에서
  mode, seed, seed after generate를 설정합니다.
- `Anima Wildcard`: Prompt Studio 없이 문자열만 확장할 때 사용합니다.

## Quick Syntax Reference

| 문법 | 의미 |
| --- | --- |
| `__hair_color__` | `hair_color.txt`, `hair_color.yaml`, `hair_color.yml` 후보 중 1개 선택 |
| `__style/anime__` | 하위 경로의 `style/anime` key 후보 중 1개 선택 |
| `__*/hair_color__` | 어느 하위 폴더에 있든 basename이 `hair_color`인 key 검색 |
| `__style/*__` | `style/` 아래 모든 key 후보를 합쳐 1개 선택 |
| `3#__hair_color__` | 파일 와일드카드 후보 중 3개를 선택해 `, `로 연결 |
| `{red|blue|green}` | inline 후보 중 1개 선택 |
| `{2::red|5::blue|green}` | 가중치 후보 중 1개 선택. 가중치가 없으면 1로 계산 |
| `{2$$red|blue|green}` | inline 후보 중 2개 선택, 기본 구분자 `, ` 사용 |
| `{1-3$$, $$red|blue|green}` | 1개에서 3개까지 선택하고 `, `로 연결 |
| `{2$$__hair_color__}` | 파일 와일드카드 후보를 펼친 뒤 2개 선택 |

가중치 예시:

```text
{2::red|5::blue|3::green|white}
```

위 예시는 red, blue, green, white가 각각 2, 5, 3, 1의 가중치로 선택됩니다.

여러 개 선택 예시:

```text
{2$$red|blue|green}
{1-3$$, $$red|blue|green}
3#__hair_color__
```

`$$` 앞은 선택 개수입니다. `1-3`처럼 범위를 쓰면 seed에 따라 개수가 정해집니다.
`count$$separator$$options` 형태로 구분자를 지정할 수 있습니다.

## 기본 폴더

노드팩을 로드하면 기본 와일드카드 폴더와 간단한 테스트 파일을 만듭니다.

```text
ComfyUI/user/__easyuse_anima/wildcards/easyuse_anima_test.txt
```

테스트 토큰:

```text
__easyuse_anima_test__
```

파일은 UTF-8 텍스트를 기준으로 읽습니다. 빈 줄과 `#`로 시작하는 줄은 후보에서
제외됩니다.

## 추가 경로

ComfyUI Settings의 EasyUse Anima `Wildcard` 섹션에서 추가 와일드카드 경로를
등록할 수 있습니다.

- 한 줄에 하나씩 입력하거나 `;`로 구분합니다.
- 절대 경로와 ComfyUI root 기준 상대 경로를 사용할 수 있습니다.
- 추가 경로가 기본 폴더보다 먼저 탐색됩니다.
- 같은 key가 여러 경로에 있으면 먼저 발견된 경로가 우선됩니다.
- 자동완성 응답에는 상대 key만 표시되고 로컬 절대 경로는 표시되지 않습니다.

## 파일 문법

지원 파일:

- `.txt`
- `.yaml`
- `.yml`

텍스트 파일 예시:

```text
# wildcards/hair_color.txt
black hair
white hair
2::pink hair
```

사용:

```text
__hair_color__
3#__hair_color__
```

YAML 파일 예시:

```yaml
hair_color:
  - black hair
  - white hair
style:
  anime:
    - cel shading
    - flat color
```

사용:

```text
__hair_color__
__style/anime__
```

`N::candidate`는 가중치 후보입니다. 일반 채우기에서는 가중치 기반 선택에
사용되고, 순차 모드에서는 후보 1개로 계산한 뒤 `N::` prefix만 제거됩니다.

`<lora:name:weight>` 형식은 텍스트로 보존합니다. EasyUse Anima 와일드카드는
MODEL/CLIP에 LoRA를 직접 적용하지 않습니다.

## 모드

- `일반 채우기`: 원본 텍스트를 seed 기반으로 확장합니다.
- `고정`: 같은 원문, 같은 seed, 같은 와일드카드 파일 상태에서 같은 확장 결과를
  만듭니다.
- `순차`: 각 후보 목록에서 `seed % candidate_count` index를 선택합니다.
  seed control은 자동으로 `increment`가 됩니다.
- `재현`: 저장된 결과 workflow에서 확장된 텍스트를 그대로 재사용하기 위한
  모드입니다.

seed control:

- `fixed`
- `randomize`
- `increment`
- `decrement`

## Prompt Studio Advanced

`Anima Prompt Studio Advanced`에는 `mod guidance` 아래 와일드카드 제어 영역이
있습니다.

- mode
- wildcard seed
- seed after generate

실행 시 `advanced_fields`의 텍스트를 확장합니다. live workflow에는 원본
와일드카드 텍스트와 다음 seed 상태를 유지하고, 저장 이미지 workflow에는 확장된
텍스트와 `재현` 모드 정보를 기록합니다.

NAIA 채우기와 같이 사용할 때는 NAIA 결과를 먼저 받은 뒤 와일드카드를 확장합니다.

## Anima Wildcard 노드

`Anima Wildcard` 노드는 Prompt Studio 없이 문자열만 확장할 때 사용합니다.

출력:

- `text`: 확장된 프롬프트
- `seed`: seed control 적용 후 다음 seed

저장 이미지 workflow에는 확장 결과가 `populated_text`에 기록되고 모드는 `재현`으로
저장됩니다.

## 자동완성 및 하이라이트

- `__` 또는 `__partial`을 입력하면 와일드카드 후보가 자동완성에 표시됩니다.
- 선택하면 현재 토큰을 `__relative/key__` 형식으로 교체합니다.
- Prompt Studio 하이라이트는 와일드카드 문법을 일반 태그 색상과 별도로
  표시합니다.
