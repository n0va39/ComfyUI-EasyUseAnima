# Anima NAIA Random Prompt

카테고리: `NAIA Bridge/API`

출력:

- `prompt`
- `negative_prompt`
- `width`
- `height`

NAIA remote API에서 prompt, negative prompt, width, height를 받아오는 노드입니다.
`comfyui-naia-bridge`를 import하거나 덮어쓰지 않고, 같은 remote API만 사용합니다.

## 주요 동작

- `use_naia_bridge=false`이면 NAIA 호출 없이 입력값을 그대로 반환합니다.
- `freeze_naia_output=true`이면 저장된 캐시 출력이 유효할 때 NAIA를 다시 호출하지
  않습니다.
- `show_preview=false`이면 큰 읽기 전용 preview widget을 숨깁니다.
- `use_naia_settings=false`이면 현재 노드의 `pre_prompt`, `post_prompt`,
  `auto_hide`, 전처리 옵션을 NAIA 요청에 보냅니다.
- 저장 이미지 workflow에는 캐시된 출력값과 `freeze_naia_output=true`가 기록되어
  다시 불러왔을 때 같은 결과를 재현합니다.

## 참고

`remove_*` 전처리 옵션은 advanced input으로 표시됩니다. NAIA service가
`POST /api/comfyui/random` endpoint를 노출해야 합니다.
