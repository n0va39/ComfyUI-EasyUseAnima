# 와일드카드 가이드

EasyUse Anima 와일드카드는 프롬프트 안의 `__name__` 파일 와일드카드와
`{a|b|c}` 동적 프롬프트를 queue 실행 시 확장합니다.

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

## 문법

파일 와일드카드:

```text
__hair_color__
__style/anime__
__*/hair_color__
__style/*__
3#__hair_color__
```

동적 프롬프트:

```text
{red|blue|green}
{2::red|5::blue|3::green|white}
{2$$red|blue|green}
{1-3$$, $$red|blue|green}
{1-3$$__hair_color__}
```

지원 파일:

- `.txt`
- `.yaml`
- `.yml`

`N::candidate`는 가중치 후보입니다. 일반 채우기에서는 가중치 기반 선택에
사용되고, 순차 모드에서는 후보 1개로 계산한 뒤 `N::` prefix만 제거됩니다.

`<lora:name:weight>` 형식은 텍스트로 보존합니다. EasyUse Anima 와일드카드는
MODEL/CLIP에 LoRA를 직접 적용하지 않습니다.

## 모드

- `일반 채우기`: 원본 텍스트를 seed 기반으로 확장합니다.
- `고정`: cached expanded text가 있으면 그 값을 사용합니다.
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
