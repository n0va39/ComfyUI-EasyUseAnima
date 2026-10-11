# Easy Anima IP-Adapter Hook

설치된 [LuciferTC Anima IP-Adapter](https://github.com/LuciferTC9527/ComfyUI-Anima_IP-Adapter)를
Anima AiO Generator의 첫 생성 단계에 연결합니다. 외부 노드와 모델 가중치는 별도로 필요합니다.
EasyUse Anima는 외부 코드나 가중치를 포함하거나 자동 설치하지 않습니다.

## 연결

1. 외부 노드팩과 해당 README의 SigLIP2·IP-Adapter 가중치를 설치하고 ComfyUI를 재시작합니다.
2. `Anima IP-Adapter Loader (SigLIP2)`의 출력을 이 노드의 `ip_adapter`에 연결합니다.
3. `Load Image`의 IMAGE 출력을 `ref_image`에 연결합니다.
4. 이 노드의 `aio_hook` 출력을 `Anima AiO Generator`의 `aio_hook`에 연결합니다.

외부 `Apply` 노드를 따로 연결하지 않습니다. AiO가 준비한 모델에 샘플링 직전 적용합니다.
Highres, Detailer, Upscale에는 IP-Adapter를 자동 전파하지 않습니다.
연결하지 않은 기존 AiO 워크플로우는 외부 노드 없이 그대로 작동합니다.

## 지원 범위

- 검토한 외부 버전: `6b77cd0c367d76402174ace2be50d3cb6aa77855`.
  설치 폴더명이 아닌 등록된 Apply 클래스와 소스 지문을 검사합니다.
  다른 버전 또는 동명 노드는 오류로 안내하며 무시하고 생성하지 않습니다.
- 28블록 Anima와 28블록 체크포인트, RGB 참조 이미지 한 장, 생성 배치 1.
- 기본 CUDA 장치, 일반 ComfyUI sampler와 표준 CFG.
- Dynamic VRAM은 꺼야 합니다(`--disable-dynamic-vram`). 샘플링 모델 전체가 GPU에 올라가야 합니다.
  부분 로딩 오류가 발생하면 충분한 VRAM 환경에서 `--highvram`을 사용합니다.
- Compile, 다중 GPU, Spectrum 가속, 기존 IP-Adapter 패치 및 CFG/model wrapper 충돌 조합은 지원하지 않습니다.
  공유 Q projection 또는 MLP 이전 주입을 요구하는 체크포인트도 지원하지 않습니다.

설정은 외부 Apply의 의미를 그대로 따릅니다. `siglip_layer`는 가중치 학습 설정에 맞추고,
`ref_image_size`는 16의 배수로 지정하세요. `ip_cfg_separate`는 별도 IP CFG를 위한
추가 모델 계산을 수행하므로 시간이 더 걸릴 수 있습니다. `use_lora`는 외부 IP 체크포인트에
포함된 LoRA 사용 여부이며, AiO의 일반 LoRA 스택을 끄는 설정이 아닙니다.

## 적용 수명과 재현

모델 로딩 및 일반 LoRA 적용이 끝난 `SAMPLER_SAMPLE` 경계에서 외부 Apply를 호출합니다.
첫 샘플러 반환·예외·중단 시 추가된 IP 모듈, attention 훅, forward, LoRA 계층을 복구합니다.
외부 인코더의 device 배치도 복구합니다. 모델을 다시 로드하는 동안 임시 계층이 노출되지 않게 합니다.
동일 Hook 구현의 실행은 잠금으로 직렬화하며, 외부 도구가 같은 모델을 병렬로 직접 사용하는 것은 지원 범위 밖입니다.

이미지와 외부 가중치는 안정적인 JSON 캐시 키가 아니므로 Hook 연결 시 AiO 결과 캐시를 재사용하지 않습니다.
워크플로우에는 외부 Loader·참조 이미지·Hook 설정을 함께 보존해야 합니다.

구현 및 검증 추적: [Issue #800](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/800).
