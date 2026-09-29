# Easy Anima Safe PAG

Anima/Cosmos/Predict2 계열 MODEL에 적용하는 패치입니다. 추가 모델 파일이나 외부
Safe PAG 노드팩 없이 `MODEL → Easy Anima Safe PAG → KSampler`로 연결합니다.

선택한 self-attention 블록을 변형해 얻은 예측과 정상 예측의 차이로 생성 결과를
보정합니다. `scale`은 보정 강도이며 0이면 입력 MODEL을 그대로 반환합니다.
`block_indices`에는 `18` 또는 `18-20` 같은 블록 번호·범위를 지정합니다.
`perturbation_strength`는 attention 변형 강도이고, `head_indices`를 비우면 모든
head에 적용합니다. `start_percent` / `end_percent`는 적용 구간,
`rescale` / `rescale_mode`는 과도한 보정 대비를 줄이는 설정입니다.

AiO의 기존 Safe PAG 설정과 적용 단계는 같은 내장 엔진을 사용하며 저장 설정을
변경할 필요가 없습니다. 등록 ID는 `EasyAnimaSafePAG`로, 원본 `AnimaSafePAG`와
다릅니다. 두 팩을 함께 설치해도 원본 노드를 덮어쓰지 않습니다. 원본 단독 노드가
들어 있는 워크플로우는 연결을 바꾸기 전까지 원본 팩이 필요합니다.
내장 노드를 연속 적용하면 앞서 적용한 내장 Safe PAG 보정을 교체합니다.

[원본 출처와 라이선스](../../third_party/anima-safe-pag/NOTICE.md)
