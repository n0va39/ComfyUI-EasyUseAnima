# AiO Hook 기능 로드맵

> 기준일: 2026-08-12
> 추적 이슈: [#622](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/622)
> 상태: [PR #623](https://github.com/n0va39/ComfyUI-EasyUseAnima/pull/623)의 postprocess prototype과 후속 first-pass control 확장 기준. 아직 공개 릴리즈에는 포함되지 않았습니다.

이 문서는 현재 `dev` prototype으로 만들 수 있는 기능, 승격에 사용한 검증,
그리고 이후 확장 후보를 구분합니다. 공개 사용 계약은
[AiO Hook API v1 가이드](aio-hooks.ko.md)와 `easyuse_anima.extensions.aio`가
소유합니다.

## 상태 정의

| 상태 | 의미 |
| --- | --- |
| Dev prototype | 구현·검증을 마치고 `dev`에 병합됐지만 아직 릴리즈 지원은 아닌 기능 |
| Prototype 증거 | 현재 기능을 `dev`에 유지하기 위해 필요한 통합 증거 |
| 단기 예정 | 현재 v1 계약을 깨지 않고 별도 PR로 추가할 기능 |
| 탐색 예정 | 직접 evidence와 별도 계약 검토 후에만 API에 추가할 기능 |
| 비범위 | AiO Hook 대신 별도 provider/API가 소유해야 하는 기능 |

## 현재 `dev` prototype이 지원하는 기능

| 기능 | 계약과 활용 예 |
| --- | --- |
| 명시적 연결 | Generator의 optional `aio_hook` socket으로만 활성화. 자동 검색이나 monkeypatch 없음 |
| 형제 노드팩 로드 순서 | provider는 모듈 최상위 import를 피하고 node 실행 시 공개 API를 지연 import |
| postprocess 전·후 실행 | `POSTPROCESS / BEFORE`, `POSTPROCESS / AFTER` callback |
| first-pass 실행 전 | `FIRST_PASS / BEFORE`에서 실제 sampling MODEL과 allowlist sampler 설정을 patch |
| MODEL patch | provider가 `event.state.model`을 새 MODEL로 바꿔 해당 first pass에 적용 |
| sampler 설정 override | `steps`, `cfg`, `sampler_name`, `scheduler`, `denoise`만 허용. backend와 seed는 제외 |
| 이미지 후처리 | 이전과 같은 tensor shape를 유지하는 `IMAGE` 교체. 색보정, LUT, 톤·감마, 샤픈, 워터마크 등에 사용 |
| 확장 metadata | `extensions.hook_data.<hook_id>#<ordinal>` 아래 JSON-safe 기록 추가 |
| 미리보기 | hook이 처리 중간 이미지를 AiO preview transport로 보낼 수 있음 |
| 실행별 session | reusable definition과 queue 실행별 mutable session 분리 |
| 정리 callback | session `close()`는 provider 역순, 등록 cleanup은 전역 등록 역순(LIFO)으로 실행 |
| Hook 조합 | `Anima AiO Hook Combine`에서 2~4개 provider를 연결 순서대로 조합 |
| 결정적 순서 | before는 A→B, after/session close는 B→A, cleanup은 전역 LIFO |
| 캐시 변경 감지 | JSON-safe `fingerprint`를 Generator `IS_CHANGED`에 포함. 없으면 보수적으로 재실행 |
| first-pass cache 안전성 | `FIRST_PASS / BEFORE` Hook 연결 시 공유 first-pass cache를 우회 |
| fail-closed 오류 | 잘못된 descriptor, patch, shape, metadata 또는 provider 예외에서 저장을 정상 완료로 위장하지 않음 |
| no-hook 호환 | Hook 미연결 시 기존 Generator 출력·metadata·cache signature 경로를 유지 |

현재 image patch는 Generator의 최종 `IMAGE`만 바꿉니다. `LATENT`는 함께 다시
인코딩하지 않으므로 image와 latent의 픽셀 의미가 반드시 같아야 하는 후속 노드에는
이 차이를 고려해야 합니다.

## Prototype 통합 증거

다음은 새 기능이 아니라 현재 구현을 `dev`의 실제 써드파티 prototype으로
승격하는 데 사용한 필수 증거입니다.

- [완료] Registry package가 공개 API의 단일 type identity를 게시하고, EasyUse
  Anima보다 먼저 발견된 provider도 지연 import 후 정상 실행되는지 확인
- [완료] 격리된 ComfyUI에서 provider 연결/미연결 queue 실행 비교
- [완료] ComfyUI 0.27.0 / frontend 1.45.20의 Legacy Canvas와 Node 2.0에서
  optional socket을 저장·재로드하고, API prompt가 같은 provider 링크를
  `aio_hook` 입력으로 직렬화하는지 확인
- [완료] 결과 metadata에 descriptor와 hook data가 예상 namespace로 기록되는지 확인
- package/live 검증에서 production correction이 생기면 해당 focused test와 공식
  full을 최종 후보 SHA에서 다시 실행

완료된 증거는 이 표면을 `dev` prototype으로 승격하지만, 릴리즈된 SDK를
의미하지는 않습니다.

## 단기 예정 기능

### 1. Impact `DETAILER_HOOK` 호환

AiO Generator에 별도 optional `detailer_hook: DETAILER_HOOK`을 연결하고 기존
SAM3/Impact detailer 호출까지 같은 객체 identity로 전달합니다.

활용 예:

- Impact detailer noise/denoise hook
- crop sampling size alignment
- detailer preview와 custom sampler hook
- face/eye target 공통 hook

전용 AiO Hook chain과 Impact Hook은 타입·lifecycle이 다르므로 하나의 socket이나
adapter로 합치지 않습니다.

### 2. save/metadata 경계

이미지 tensor를 다시 바꾸지 않고 저장 직전 metadata를 추가하거나 검증하는
`SAVE / BEFORE` 경계를 검토합니다.

활용 예:

- provenance와 생성 정책 기록
- 외부 자산 ID 또는 파이프라인 버전 기록
- 저장 전 필수 metadata 검증

파일 경로 변경, 임의 파일 I/O, 저장 backend 교체는 이 경계에 포함하지 않습니다.

### 3. detailer·upscale 이후 이미지 경계

`DETAILER / AFTER`, `UPSCALE / AFTER`부터 단계적으로 추가합니다. 각 stage는
허용 patch, disabled-stage 의미, preview 순서와 cache 영향을 별도 PR에서 고정합니다.

활용 예:

- detailer 결과 마스크 기반 합성
- upscale 후 샤픈·디밴딩
- stage별 비교 preview와 품질 metadata

## 중기 탐색 기능

| 후보 stage | 지원할 만한 기능 | 선행 계약 |
| --- | --- | --- |
| `HIGHRES / BEFORE·AFTER` | highres 입력/결과 관찰, 같은-shape latent 또는 image 보정 | latent identity와 cache mutation 격리 |
| `FIRST_PASS / AFTER` | 1차 결과 분석, cache hit마다 재실행할 observer | canonical cache entry 불변성 |
| `CONDITIONING / AFTER` | positive/negative conditioning adapter | conditioning schema·clone·metadata 계약 |
| `RESOURCES / AFTER` | MODEL/CLIP/VAE capability adapter | clone ownership, patch order, cleanup owner |

이 stage들은 현재 `AioStage` enum에 미리 넣지 않습니다. 실제 dispatch와 검증을
제공하는 PR에서만 public enum과 patch DTO를 확장합니다.

## 향후 별도 provider가 적합한 기능

다음은 Hook callback보다 소유권이 큰 기능이므로 별도 계약을 우선합니다.

- custom sampler object 또는 sampling backend 전체 교체
- mandatory stage 건너뛰기·재배열·교체
- 비동기/background job과 외부 queue orchestration
- 새로운 save backend나 파일 라우팅
- process lifetime 모델·GPU resource registry
- workflow 밖 전역 Hook 자동 등록

필요성이 확인되면 `SamplingBackendProvider`, `StageProvider` 또는 save provider
같은 독립 API와 rollback 경계로 설계합니다.

## 계속 유지할 v1 비범위

- 내부 `GenerationState`나 `RuntimeServices` 직접 노출
- 임의 dict mutation과 core metadata 덮어쓰기
- tensor shape 변경, crop 또는 resize를 숨기는 image patch
- async hook, background thread, process-global callback registry
- 다른 Hook의 session/state 접근
- 오류 무시 후 부분 처리 이미지를 정상 저장
- 객체 `repr`, memory address, pickle hash를 fingerprint로 사용

## Promotion 순서

1. [완료] 현재 postprocess prototype의 package/live gate 완료
2. [완료] [PR #623](https://github.com/n0va39/ComfyUI-EasyUseAnima/pull/623)을 review하고 `dev`에 병합
3. `FIRST_PASS / BEFORE` MODEL·sampler allowlist와 cache bypass를 독립 검증
4. Impact `DETAILER_HOOK` 호환을 독립 PR로 구현
5. save/metadata와 post-detailer/upscale stage를 작은 PR로 확장
6. 다른 cache-sensitive stage는 실제 cache isolation evidence 후 하나씩 추가
7. public v1 사용 사례가 쌓인 뒤에만 v2 또는 별도 provider 필요성 검토

각 단계의 구현·검증·미실행 항목은 #622와 해당 PR 본문에 함께 기록합니다.
