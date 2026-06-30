# Anima Prompt Builder

카테고리: `EasyUse Anima/Prompt`

출력:

- `prompt`
- `anima_mod_guidance_quality_tags`
- `use_anima_mod_guidance`
- `metadata_prompt`

NAIA와 Anima Mod Guidance workflow를 위해 여러 입력칸을 조합해 정리된
프롬프트를 만듭니다.

![Anima Prompt Builder](../images/nodes/anima-prompt-builder.png)

## 입력 필드

- `lora_trigger_tags`: LoRA Manager 등에서 받은 한 줄 trigger tag입니다.
- `quality_tags`: 앞쪽에 배치할 quality tag입니다.
- `trigger_and_artist_tags`: 수동 모델 trigger와 `@artist` 태그입니다.
- `prompt`: 본문 프롬프트입니다.
- `trailing_quality_tags`: 뒤쪽에 붙일 quality 또는 style tag입니다.

## 동작

- 줄바꿈은 쉼표 구분자로 처리합니다.
- 빈 쉼표 그룹과 중복 공백을 정리합니다.
- 조합된 프롬프트는 ANIMA prompt ordering을 거칩니다.
- `use_anima_mod_guidance=true`이면 `prompt` 출력에서 quality field를 제외하고
  별도 `anima_mod_guidance_quality_tags` 출력으로 반환합니다.
- `metadata_prompt`는 AMG mode와 무관하게 quality field를 포함합니다.
- `pin_trigger_tags_to_front=true`이면 trigger field를 quality tag 앞쪽에
  고정합니다.
