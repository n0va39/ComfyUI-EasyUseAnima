# 와일드카드 가이드

EasyUse Anima 와일드카드는 프롬프트 안의 `__name__` 파일 와일드카드와
`{a|b|c}` 동적 프롬프트를 queue 실행 시 확장합니다.

노드별 사용 위치:

- `Anima Prompt Studio Advanced`: `와일드카드 시드` 버튼으로 설정 팝업을 열어
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
| `{red\|blue\|green}` | inline 후보 중 1개 선택 |
| `{2::red\|5::blue\|green}` | 가중치 후보 중 1개 선택. 가중치가 없으면 1로 계산 |
| `{2$$red\|blue\|green}` | inline 후보 중 2개 선택, 기본 구분자 `, ` 사용 |
| `{1-3$$, $$red\|blue\|green}` | 1개에서 3개까지 선택하고 `, `로 연결 |
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

- 설정 UI에서 항목을 추가하고, 각 항목에는 폴더 경로 하나만 입력합니다.
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

## Seed 범위와 기존 workflow 호환성

이 범위 계약은 `Anima Prompt Studio Advanced`,
`Anima Prompt Studio Advanced v2`, `Anima Prompt Studio Regional`,
`Anima Wildcard`의 와일드카드 seed에 공통으로 적용됩니다.

- 브라우저에서 새로 입력하거나 편집하는 현재 seed와 일반적인 다음 seed의 공개
  범위는 `0..Number.MAX_SAFE_INTEGER` (`0..9007199254740991`)이며 양 끝값을
  포함합니다.
- `fixed`는 현재 seed를 그대로 유지합니다.
- `increment`는 최댓값 다음에 `0`으로 돌아가고, `decrement`는 `0` 다음에
  최댓값으로 돌아갑니다.
- `randomize`도 같은 공개 범위 전체에서 seed를 선택하며 `0`과 최댓값을 모두
  포함할 수 있습니다.
- 새 편집값은 이 범위 안의 부호 없는 10진 숫자만 사용할 수 있습니다. `+`나
  `-` 부호, 소수, 지수 표기와 최댓값 초과 입력은 실제 widget이나 저장
  workflow에 반영하지 않고 이전 seed를 유지합니다.

Python backend는 기존 workflow 호환을 위해 uint64 범위
`0..18446744073709551615`를 계속 읽습니다. EasyUse Anima는 이미 저장된 공개
범위 초과 seed를 의도적으로 공개 범위로 clamp하지 않으며, 브라우저가 정확히
표현할 수 있는 값은 load/save에서 그대로 보존합니다. backend는 현재 generation에
그 seed를 사용하고 `fixed`는 값을 유지합니다. 다만 JavaScript는 모든 큰 정수의
정밀도를 보장하지 못하므로 정확한 화면 표시와 save/reload round-trip은
best-effort입니다. `increment`, `decrement`, `randomize`로 상태를 진행하면 다음
seed는 다시 공개 범위로 들어옵니다.

일부 Node 2.0 frontend에서는 거부된 최댓값 초과 문자열이 입력칸에 일시적으로
남을 수 있습니다. 이 경우에도 실제 widget과 저장 workflow는 이전 유효 seed를
유지하며, workflow를 다시 열면 저장된 값이 표시됩니다.

## Prompt Studio Advanced

`Anima Prompt Studio Advanced`에는 `와일드카드 시드` 버튼과 현재 설정 요약이
표시됩니다. 버튼을 누르면 와일드카드 설정 팝업이 열립니다.

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
  표시하며, ComfyUI Settings에서 색상을 변경할 수 있습니다.
