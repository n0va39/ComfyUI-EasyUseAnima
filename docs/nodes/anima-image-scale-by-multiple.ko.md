# Anima Image Scale By Multiple

카테고리: `EasyUse Anima/Image`

입력:

- `image`
- `scale_by`
- `upscale_method`
- `multiple`
- `max_long_edge`

출력:

- `image`
- `width`
- `height`
- `applied_scale`

원본 비율을 유지하면서 출력 너비와 높이가 지정 배수에 맞도록 가장 가까운 유효
배율로 이미지를 확대합니다. Highres, 최적화 노드, 16채널 VAE처럼 32배수 크기를
요구하거나 선호하는 흐름에서 사용합니다.

## 주요 동작

- `scale_by`는 요청 배율이고, 실제 적용 배율은 선택한 `multiple`에 맞는 가장
  가까운 값으로 보정됩니다.
- `multiple=32`는 ANIMA/Spectrum 계열 Highres 흐름에서 기본적으로 안전한 값입니다.
- `max_long_edge`를 0보다 크게 설정하면 긴 변이 이 값을 넘지 않는 유효 크기 중
  요청 배율에 가장 가까운 크기를 선택합니다.
- 최종 크기와 실제 적용 배율은 `width`, `height`, `applied_scale` 출력으로 확인할
  수 있습니다.

## 사용 위치

Highres 전후 이미지 크기를 안정적으로 맞추거나, downstream 노드가 특정 배수의
width/height를 요구할 때 이미지 입력 앞에 연결합니다.
