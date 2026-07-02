# Anima Prompt Studio Advanced

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

큰 workflow를 위한 확장형 Prompt Studio 노드입니다.

![Anima Prompt Studio Advanced](../images/nodes/anima-prompt-studio-advanced.png)

## 필드 구조

- positive prompt와 negative prompt를 별도 field group으로 편집합니다.
- field는 추가, 삭제, 순서 변경, 활성화, 비활성화할 수 있습니다.
- positive field type은 quality, artist, trigger, general, NAIA를 지원합니다.
- negative prompt에도 NAIA field를 1개 추가할 수 있습니다.
- NAIA field는 마지막 NAIA 결과를 workflow에 저장하며, 채워진 뒤에도 직접
  수정할 수 있습니다.
- trigger field는 연결된 `trigger_words` 입력을 표시할 수 있고, front 고정
  또는 ANIMA ordering 적용을 선택할 수 있습니다.

## 해상도

- latent image 해상도 선택은 `mod guidance` 바로 아래에 표시됩니다.
- bucket은 `512`, `768`, `896`, `1024`, `1280`, `1536`을 지원합니다.
- `Custom` bucket에서는 width와 height를 직접 입력하고 workflow에 저장합니다.
- `NAIA` bucket은 prompt field를 채우는 것과 같은 NAIA 응답에서 width와
  height를 가져옵니다.
- 저장 이미지 workflow에는 해결된 해상도를 `Custom`으로 저장해 같은 결과를
  다시 만들 수 있게 합니다.

## 와일드카드

`mod guidance` 아래의 와일드카드 제어 영역에서 mode, seed, seed after generate를
설정합니다.

- live workflow는 원본 와일드카드 텍스트와 다음 seed 상태를 유지합니다.
- 저장 이미지 workflow는 확장 결과를 `재현` mode로 저장합니다.
- NAIA 채우기와 같이 사용할 때는 NAIA 결과를 먼저 받은 뒤 와일드카드를
  확장합니다.

문법은 [와일드카드 가이드](../wildcards.ko.md)를 참고하세요.

## Artist Mix

`Anima Prompt Studio Advanced v2`는 기존 문자열 출력 대신
`EASYUSE_ANIMA_PROMPT_DATA` 하나를 출력합니다. 이 prompt data 안에는 artist
field 텍스트와 `artist_mix` 설정이 별도 key로 저장됩니다.

- artist field는 `@`가 붙은 토큰을 찾는 방식이 아니라 Advanced의 작가 태그
  입력 field를 의미합니다.
- artist mix를 끄면 artist field 텍스트는 기존처럼 positive prompt에 포함됩니다.
- artist mix를 켜면 base prompt에서는 artist field 텍스트를 분리하고,
  `Anima Prompt Data Conditioning`이 선택한 artist mix mode로 positive
  `CONDITIONING`을 만듭니다.
- Prompt Data 없이 일반 prompt와 작가 태그만 처리하려면
  [Anima Artist Mix Conditioning](anima-artist-mix-conditioning.ko.md)을 사용합니다.

## 하이라이트

- quality, safety/rating, year, count, character, artist, copyright, metadata,
  learned general tag, natural language, syntax error, unknown tag를 구분해
  표시합니다.
- `__wildcard__`, `3#__wildcard__`, `{a|b|c}` 같은 와일드카드 문법은 일반
  태그와 별도 색상으로 표시합니다.
- overlay는 입력칸의 font family, size, spacing, wrapping 설정을 따라가도록
  동기화됩니다.
