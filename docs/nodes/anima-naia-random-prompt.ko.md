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
- endpoint와 Prompt Engineering 값은 전역 EasyUse Anima 설정을 사용합니다.
  `NAIA Desktop Prompt Engineering 사용` 설정이 이 전역 override를 NAIA에
  보낼지 결정합니다.
- 저장 이미지 workflow에는 캐시된 출력값과 `freeze_naia_output=true`가 기록되어
  다시 불러왔을 때 같은 결과를 재현합니다.

## 참고

`remove_*` 전처리 옵션은 advanced input으로 표시됩니다. NAIA service가
`POST /api/comfyui/random` endpoint를 노출해야 합니다.

기존 workflow schema 호환성을 위해 노드는 `use_naia_settings`, `pre_prompt`,
`post_prompt`, `auto_hide`, 전처리, `host`, `port` 입력 이름을 계속 선언합니다.
frontend는 이 호환성 값을 숨기며 backend는 저장된 값을 사용하지 않습니다.
endpoint, Prompt Engineering과 원격 API 권한은 전역 EasyUse Anima 설정에서
구성합니다. 전역 `원격 API 허용` 보안 설정을 켜지 않으면 원격 host는 계속
차단됩니다.
