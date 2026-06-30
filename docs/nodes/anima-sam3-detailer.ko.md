# Anima SAM3 Detailer

카테고리: `EasyUse Anima/Detailer`

출력:

- `image`
- `segs`
- `mask`
- `raw_image`

ComfyUI native SAM3 text detection, Impact `MaskToSEGS`, Impact Pack
`DetailerForEach`를 연결하는 detailer 노드입니다.

## 주요 입력

- `enabled`: 꺼두면 원본 이미지를 반환합니다.
- `image`: detail 대상 이미지입니다.
- `ctx_SAM3`: `Anima SAM3 Context` 또는 호환 rgthree context입니다.
- `detect_prompt`: SAM3 text target입니다. 쉼표로 여러 target을 쓰거나
  `target:count` 형식으로 개별 count를 지정할 수 있습니다.
- `detect_count`: `detect_prompt`에 count가 없을 때 target당 최대 detection 수입니다.
- `threshold`: SAM3 detection threshold입니다.
- `refine_iterations`: SAM decoder refinement 횟수입니다.

나머지 sampling, inpaint, hook 입력은 Impact `DetailerForEach` 흐름으로 전달됩니다.

## 요구 사항

실행 시점에 `ComfyUI-Impact-Pack`이 필요합니다. Impact Pack이 없어도 EasyUse
Anima의 다른 노드 import는 실패하지 않지만, 이 노드는 실행할 수 없습니다.
