# ComfyUI-EasyUseAnima 백엔드 리팩토링 및 AiO Hook 확장성 통합 계획

> 기준일: 2026-07-19
> 기준 브랜치: `dev`
> 문서 성격: 기존 Python 백엔드 장기 리팩토링 계획의 AiO Hook 확장성 보강안
> 주요 연계: #184, #168, #169, #187
> 상태: 저장된 장기 계획안 — 현재 구현 범위와 분리
> 릴리즈 목표: 전체 Hook 확장성 완료 및 통합 검증 후 0.6.0

---

## 0. 계획 상태와 0.6.0 릴리즈 게이트

- 이 문서는 장기 설계와 실행 순서를 저장하는 계획 문서이며, 문서 병합만으로 Hook 구현이나 공개 API가 활성화되지는 않는다.
- 현재 진행 중인 #184/#168/#169/#187 작업은 그대로 유지한다. Hook Phase H는 각 선행 종료 조건을 만족한 조각만 백엔드 리팩토링과 병행하고, 결합 위험이 남은 조각은 리팩토링 완료 후 진행한다.
- Phase H0~H9와 이 문서의 전체 완료 기준을 충족하고 no-hook 호환성, Legacy Canvas, Node 2.0, Registry package 검증을 통과한 통합 결과를 **0.6.0 릴리즈 목표**로 삼는다.
- `dev` 통합, `main` 반영, version/tag/release/Registry publication은 기존 릴리즈 승인 절차에 따라 별도로 수행한다.

---

## 1. 문서 목적

이 계획의 목적은 Python 백엔드 리팩토링을 진행하면서 AiO Generator에 안정적인 확장 지점을 마련하는 것이다.

Hook을 단순히 `generate()` 중간에 임의 콜백으로 추가하는 것이 목표가 아니다. 최종적으로는 다음을 만족해야 한다.

1. 기존 워크플로우와 노드 계약을 보존한다.
2. AiO의 리소스 로드, conditioning, sampling, highres, detailer, upscale, postprocess, save 책임을 분리한다.
3. 써드파티가 EasyUse Anima 내부 함수를 monkey patch하지 않고 명시적인 ComfyUI 연결로 기능을 추가할 수 있다.
4. Hook API의 버전, 실행 순서, 오류, 캐시, cleanup 계약이 문서와 테스트로 고정된다.
5. Hook이 내부 `GenerationState` 구조나 private helper에 직접 의존하지 않는다.
6. Hook이 없는 기존 실행 경로에는 결과·캐시·메타데이터·성능 회귀가 없어야 한다.

---

## 2. 현재 기준점

현재 유지보수 계획은 다음 원칙을 이미 채택하고 있다.

- #184는 `nodes.py`의 동작 보존형 package 분리만 담당한다.
- #168은 AiO 설정의 single-source schema와 typed config를 담당한다.
- #169는 AiO stage pipeline과 first-pass cache 동작 변경을 담당한다.
- #187은 RuntimeServices와 전역 상태 lifecycle을 담당한다.

현재 `dev`에서는 공통 helper, Comfy adapter, image/detailer, Wildcard/NAIA, LoRA, Prompt Corrector 일부가 canonical package로 이동했다. Detailer Hook 래퍼도 `easyuse_anima/image/detailer.py`에 별도 책임으로 분리되어 있다.

반면 AiO 내부 Detailer 호출 경로는 외부 `DETAILER_HOOK`을 받을 수 있는 하위 API를 사용하면서도 AiO 단계에서는 Hook을 전달하지 않는 구조다. 따라서 다음 두 종류의 확장을 구분해 도입한다.

### 2.1 Impact Pack 호환 Detailer Hook

기존 `DETAILER_HOOK` 객체를 AiO 내부 SAM3/Impact Detailer에 전달한다.

용도:

- denoise scheduler
- noise injection
- custom sampler
- Impact preview
- crop size 조정
- 기타 Impact Pack 호환 Hook

### 2.2 EasyUse Anima 전용 AiO Hook

AiO 전체 stage에 적용되는 별도의 공개 타입을 도입한다.

권장 타입명:

```text
EASYUSE_ANIMA_AIO_HOOK
```

용도:

- 모델 또는 conditioning 패치
- sampling 전후 latent 처리
- highres/detailer/upscale 전후 이미지 처리
- 사용자 메타데이터 추가
- 사용자 preview 발행
- 실행 관측·진단
- 향후 별도 backend/provider 확장의 기반

두 타입은 합치지 않는다. Impact `DETAILER_HOOK`은 기존 외부 프로토콜 호환 계층이고, `EASYUSE_ANIMA_AIO_HOOK`은 EasyUse Anima가 장기적으로 버전 관리하는 공개 API다.

---

## 3. 핵심 아키텍처 결정

### 3.1 명시적 연결만 지원

지원:

```text
Third-party Hook Provider
        ↓ EASYUSE_ANIMA_AIO_HOOK
Anima AiO Generator
```

지원하지 않음:

- import 시 전역 자동 등록
- entrypoint scanning
- 내부 함수 monkey patch
- `nodes.py` private helper 교체
- 전역 callback list에 써드파티가 직접 append

명시적 소켓 연결은 워크플로우 재현성, missing-node 진단, 실행 순서 확인, 배포 의존성 추적에 유리하다.

### 3.2 Hook은 stage pipeline의 부가 기능이 아니라 공식 실행 계약

최종 실행 구조는 다음과 같다.

```text
EasyUseAnimaAIOGenerator node adapter
    ↓ raw input → typed request
AioOrchestrator
    ↓
Hook definition validation
    ↓
run-scoped Hook session 생성
    ↓
StageRunner
    ├─ Resources
    ├─ Conditioning
    ├─ FirstPass
    ├─ Highres
    ├─ Detailer
    ├─ Upscale
    ├─ Postprocess
    └─ Save
        각 stage 전후에 HookDispatcher 실행
    ↓
metadata/result/UI 변환
    ↓
Hook cleanup 및 ephemeral resource cleanup
```

### 3.3 Hook definition과 run session을 분리

ComfyUI 그래프에서 전달되는 Hook 객체를 실행 중 mutable state 저장소로 사용하지 않는다.

```python
class AioHookDefinition(Protocol):
    def describe(self) -> "AioHookDescriptor": ...
    def create_session(self, context: "AioHookSessionContext") -> "AioHookSession": ...
```

```python
class AioHookSession(Protocol):
    def before_stage(self, event: "AioStageEvent") -> "AioHookPatch | None": ...
    def after_stage(self, event: "AioStageEvent") -> "AioHookPatch | None": ...
    def on_error(self, event: "AioStageErrorEvent") -> None: ...
    def close(self) -> None: ...
```

이 분리는 다음 문제를 예방한다.

- 동일 Hook provider output이 여러 실행에서 mutable state를 공유함
- 병렬 또는 재진입 실행에서 state 오염
- 이전 실행의 tensor/model reference가 다음 실행에 남음
- cleanup 누락

### 3.4 내부 state를 그대로 공개하지 않음

써드파티에 내부 `GenerationRequest` 또는 `GenerationState` 객체 자체를 전달하지 않는다.

대신 다음을 제공한다.

- 읽기 전용 request/state view
- stage별 허용 필드만 포함한 event
- 변경 사항을 명시적으로 반환하는 patch
- metadata/preview/cleanup용 제한된 service facade

이렇게 하면 내부 리팩토링과 공개 Hook API의 변경 주기를 분리할 수 있다.

---

## 4. 목표 package 구조

```text
easyuse_anima/
├─ extensions/
│  └─ aio.py                    # 써드파티가 import하는 안정적 공개 API
│
├─ aio/
│  ├─ schema.py
│  ├─ migrations.py
│  ├─ models.py                 # GenerationRequest/State/Result
│  ├─ orchestrator.py
│  ├─ resources.py
│  ├─ conditioning.py
│  ├─ preview.py
│  ├─ metadata.py
│  ├─ save.py
│  ├─ cache.py
│  │
│  ├─ hooks/
│  │  ├─ dispatcher.py
│  │  ├─ validation.py
│  │  ├─ chain.py
│  │  ├─ fingerprint.py
│  │  └─ impact_detailer.py
│  │
│  └─ stages/
│     ├─ base.py
│     ├─ resources.py
│     ├─ conditioning.py
│     ├─ first_pass.py
│     ├─ highres.py
│     ├─ detailer.py
│     ├─ upscale.py
│     ├─ postprocess.py
│     └─ save.py
│
└─ nodes/
   ├─ aio_nodes.py
   └─ aio_hook_nodes.py          # Combine 및 공식 기본 Hook provider
```

### 공개/비공개 경계

써드파티가 import할 수 있는 공식 surface:

```python
from easyuse_anima.extensions.aio import (
    AIO_HOOK_API_VERSION,
    AioHookDefinition,
    AioHookDescriptor,
    AioHookSession,
    AioHookPatch,
    AioStage,
    AioStagePhase,
)
```

써드파티가 import하면 안 되는 내부 surface:

```text
easyuse_anima.aio.orchestrator
easyuse_anima.aio.models.GenerationState
easyuse_anima.aio.stages.*
easyuse_anima.aio.hooks.dispatcher
nodes.py의 underscore helper
```

공개 module의 `__all__`과 필드 snapshot을 contract test로 고정한다.

---

## 5. Hook API v1 계약

### 5.1 버전과 식별자

```python
AIO_HOOK_API_VERSION = 1
```

각 Hook descriptor는 최소 다음을 제공한다.

```python
@dataclass(frozen=True)
class AioHookDescriptor:
    hook_id: str
    hook_version: str
    api_version: int
    stages: frozenset[AioStage]
    phases: frozenset[AioStagePhase]
    required_capabilities: frozenset[str]
    fingerprint: JsonValue | None
```

규칙:

- `hook_id`는 패키지 간 충돌을 피할 수 있는 안정적인 문자열을 사용한다.
- `api_version` major 불일치는 sampling 전에 오류 처리한다.
- `fingerprint`는 JSON-safe하고 결정적이어야 한다.
- Hook object 자체를 pickle 또는 JSON으로 저장하지 않는다.
- 실행 metadata에는 descriptor의 안전한 요약만 기록한다.

### 5.2 공식 stage 이름

```text
resources
conditioning
first_pass
highres
detailer
upscale
postprocess
save
```

stage 이름은 공개 API의 일부이므로 문자열을 임의 변경하지 않는다. 내부 class 이름이 바뀌어도 공개 stage ID는 유지한다.

### 5.3 호출 순서

Hook chain이 `A → B`일 때:

```text
A.before_stage
  → B.before_stage
    → stage.run
  → B.after_stage
→ A.after_stage
```

오류 알림과 cleanup도 역순으로 수행한다.

이 순서는 middleware nesting으로 문서화하고 테스트 fixture로 고정한다.

### 5.4 변경 방식

Hook은 event object를 직접 수정하지 않고 patch를 반환한다.

```python
@dataclass(frozen=True)
class AioHookPatch:
    model: object = UNSET
    positive: object = UNSET
    negative: object = UNSET
    latent: object = UNSET
    image: object = UNSET
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
```

stage별로 허용되지 않은 필드를 반환하면 `HookContractError`를 발생시킨다.

권장 v1 write 정책:

| Stage/Phase | 허용 변경 |
| --- | --- |
| resources/after | model, clip 또는 공개 허용 resource variant |
| conditioning/after | positive, negative |
| first_pass/before | model, positive, negative, latent |
| first_pass/after | latent, image |
| highres/before·after | model, positive, negative, latent, image |
| detailer/before·after | model, positive, negative, image |
| upscale/before·after | model, positive, negative, latent, image |
| postprocess/before·after | image |
| save/before | image, metadata |
| 모든 stage | Hook namespace 아래 metadata 추가 |

실제 허용 필드는 구현 시 stage invariant와 함께 더 좁게 확정한다.

### 5.5 v1에서 금지할 기능

- 임의 stage 건너뛰기
- mandatory stage 교체
- orchestrator 내부 stage list 변경
- RuntimeServices 전체 접근
- 다른 Hook의 session/state 직접 접근
- first-pass cache에 raw tensor를 직접 삽입
- Hook 오류 무시 후 정상 결과로 저장

custom sampling backend나 stage replacement는 Hook v1에 넣지 않고 향후 별도의 `SamplingBackendProvider` 또는 `StageProvider` 계약으로 분리한다.

---

## 6. Impact `DETAILER_HOOK` 지원 계획

### 6.1 공개 입력

AiO Generator의 optional input 마지막에 추가한다.

```python
"detailer_hook": ("DETAILER_HOOK", {
    "forceInput": True,
    "tooltip": "Impact-compatible hook applied to AiO detailer targets.",
})
```

기존 workflow의 widget 순서에는 영향을 주지 않는 연결 전용 optional input으로 유지한다.

### 6.2 전달 경로

```text
EasyUseAnimaAIOGenerator.generate
  → AioOrchestrator
    → DetailerStage
      → DetailerService
        → EasyUseAnimaSAM3Detailer / Impact DetailerForEach
```

현재 alignment wrapper 정책을 유지한다.

```text
기존 Impact Hook touch_scaled_size
  → EasyUse Anima alignment 보정
```

### 6.3 초기 제한

첫 버전은 공통 Hook 하나를 모든 활성 detailer target에 순서대로 적용한다.

```text
face → eye → 향후 추가 target
```

다음은 후속 기능으로 분리한다.

- face 전용 Hook
- eye 전용 Hook
- target별 Hook chain
- target 이름을 Impact Hook에 전달하는 별도 adapter

### 6.4 변경 감지

외부 `DETAILER_HOOK` 객체는 안정적인 fingerprint를 보장하지 않을 수 있다.

정책:

1. `cache_key()` 또는 지원되는 descriptor가 있으면 stable signature에 포함한다.
2. signature를 만들 수 없으면 AiO node의 `IS_CHANGED`는 해당 실행을 강제로 재실행한다.
3. Detailer Hook은 first-pass 이후에만 실행되므로 first-pass cache 자체는 그대로 사용할 수 있다.
4. Hook object repr, memory address 또는 pickle hash를 cache key로 사용하지 않는다.

---

## 7. 캐시와 Hook의 상호작용

### 7.1 기본 원칙

Hook이 캐시 결과를 조용히 오염시키거나 stale 결과를 재사용하게 해서는 안 된다.

### 7.2 first-pass cache 저장 시점

권장 정책:

```text
FirstPassStage.run 결과 생성
  → canonical first-pass result를 cache 저장
  → after_stage Hook 실행
```

즉, `after first_pass` Hook 결과는 cache entry에 저장하지 않고 cache hit마다 다시 실행한다.

장점:

- Hook의 in-place 변화가 공용 cache entry를 오염시키는 위험 감소
- Hook 버전 변경 후에도 canonical first-pass 결과 재사용 가능
- Hook 실행 결과가 cache clone 정책과 결합되지 않음

### 7.3 fingerprint 규칙

Hook이 다음 단계 이전에 결과에 영향을 주면 fingerprint가 cache key에 포함되어야 한다.

- resources
- conditioning
- first_pass/before

정책:

```text
영향 있음 + fingerprint 있음
  → fingerprint를 first-pass cache key에 포함

영향 있음 + fingerprint 없음
  → 해당 실행에서 first-pass cache bypass

first-pass 이후만 영향
  → first-pass cache key에는 미포함
  → AiO node 전체 change signature에는 포함
```

### 7.4 Hook metadata

최종 metadata 예시:

```json
{
  "extensions": {
    "hooks": [
      {
        "hook_id": "com.example.color_finish",
        "hook_version": "1.2.0",
        "api_version": 1,
        "stages": ["postprocess"],
        "cache_policy": "post_first_pass"
      }
    ]
  }
}
```

Hook이 추가하는 metadata는 다음 namespace 아래에 둔다.

```text
extensions.hook_data.<hook_id>#<ordinal>
```

core metadata key 덮어쓰기는 금지한다.

---

## 8. 오류, validation, lifecycle

### 8.1 사전 validation

가능한 검증은 모델 로드와 sampling 전에 완료한다.

- API version
- stage ID
- phase ID
- required capability
- descriptor/fingerprint JSON-safe 여부
- fingerprint 크기 상한
- Hook chain 구조
- duplicate/cycle 방지

### 8.2 실행 오류

기본 정책은 fail-closed다.

사용자 오류 메시지에는 다음을 포함한다.

```text
hook_id
hook_version
stage
phase
오류 요약
```

서버 로그에는 원본 stack trace와 run ID를 기록한다.

Hook v1에는 `ignore_errors=true` 같은 옵션을 제공하지 않는다. 이미지가 일부만 처리된 상태에서 정상 저장되는 것을 방지한다.

### 8.3 cleanup

- 각 definition은 실행마다 새 session을 생성한다.
- session은 `ExitStack` 또는 동등한 run-scoped registry로 관리한다.
- `close()`는 Hook chain 역순으로 호출한다.
- Hook은 `register_cleanup(callback)`을 통해 임시 resource 정리를 등록할 수 있다.
- stage 예외, Hook 예외, 사용자 중단, save 실패에서도 cleanup을 실행한다.
- core ephemeral model cleanup과 Hook cleanup의 실행 순서를 고정한다.

권장 순서:

```text
Hook on_error 역순
Hook session close 역순
Hook 등록 cleanup 역순
AiO ephemeral model/temp cleanup
```

실제 model ownership과 충돌하지 않도록 Hook이 core-owned model을 직접 해제하는 것은 금지한다.

---

## 9. RuntimeServices와의 관계

Hook definition과 session은 process-wide service가 아니다.

### process lifetime

- `AioOrchestrator`
- `HookValidator`
- `FirstPassCache`
- `PreviewTransport`
- `ComfyCapabilities`

### run lifetime

- `GenerationRequest`
- `GenerationState`
- Hook chain/session
- cleanup registry
- stage trace
- preview collection

`RuntimeServices`에는 다음 정도만 포함한다.

```python
@dataclass
class RuntimeServices:
    aio: AioOrchestrator
    comfy: ComfyCapabilities
    seed_reservations: SeedReservationService
    # 기타 feature services
```

Hook session이 `get_runtime()`을 직접 호출하는 API는 제공하지 않는다. 필요한 기능은 제한된 `AioHookServices` facade로 전달한다.

권장 facade:

```python
class AioHookServices(Protocol):
    def emit_preview(self, stage: str, image, label: str | None = None) -> None: ...
    def add_metadata(self, namespace: str, values: Mapping[str, JsonValue]) -> None: ...
    def register_cleanup(self, callback: Callable[[], None]) -> None: ...
    def has_capability(self, name: str) -> bool: ...
```

---

## 10. 단계별 실행 계획

리팩토링과 Hook 구현을 다음처럼 분리한다.

### Phase R — 기존 리팩토링 선행 작업

#### R-1. #184 Prompt/Artist/Regional Move 완료

- Prompt fields/Builder/Studio
- Prompt data/Artist Mix/Conditioning
- Regional

Hook 기능은 추가하지 않는다.

#### R-2. #168 typed config와 migration 완료

- typed `AioGenerationConfig`
- pure migration
- 기존 workflow normalized config parity
- normalizer facade 축소

Hook 객체는 generation settings JSON에 저장하지 않는다. 소켓 연결과 provider node 설정이 source of truth다.

#### R-3. #184 AiO service 기계적 추출

이동:

- resource resolver
- LoRA/model patch
- conditioning
- sampling adapter
- highres/detailer/upscale/postprocess helper
- preview/save/metadata
- 기존 cache 구현

이 PR은 Move PR이며 Hook 실행을 추가하지 않는다.

---

### Phase H0 — Hook 요구사항과 공개 계약 baseline

PR 유형: Contract/Documentation

추가:

```text
docs/architecture/adr-00x-aio-extension-points.md
docs/extensions/aio-hook-api-v1.md
tests/contracts/test_aio_hook_public_api.py
tests/fixtures/aio_hook_api_v1.json
```

고정:

- 공개 import path
- API version
- stage/phase ID
- descriptor 필드
- chain 순서
- 오류 정책
- cache fingerprint 정책
- v1 비범위

runtime 변경 없음.

---

### Phase H1 — #169 request/state/stage contract

PR 유형: Contract

추가:

```python
GenerationRequest
GenerationState
GenerationResult
GenerationStage
StageRunner
StageTrace
```

기존 실행 결과를 trace fixture로 고정한다. Hook dispatcher는 아직 실행하지 않는다.

Exit criteria:

- 기존 stage 순서 parity
- disabled stage no-op parity
- metadata/preview/save 결과 parity
- no-hook 실제 queue parity

---

### Phase H2 — 내부 Hook dispatcher와 no-op seam

PR 유형: Contract/Internal

추가:

```text
AioHookDescriptor validator
HookChain
HookDispatcher
NoopHookDispatcher
run-scoped session registry
```

StageRunner는 dispatcher를 받지만 production 기본값은 no-op이다.

검증:

- no-op 경로에서 호출 결과 동일
- tensor clone 추가 없음
- stage별 dispatch trace
- exception/cleanup ordering

공개 AiO node input은 아직 추가하지 않는다.

---

### Phase H3 — Impact `DETAILER_HOOK` AiO 연결

PR 유형: Behavior + additive node contract

변경:

- AiO Generator optional `detailer_hook` 추가
- `IS_CHANGED` signature 처리
- DetailerStage → DetailerService → Impact adapter 전달
- alignment wrapper 순서 보존

검증:

- Hook 없음 parity
- 기존 Align Hook
- 외부 Denoise/Noise/Preview Hook 대표 사례
- face/eye 순차 target
- Hook 예외 cleanup
- Legacy/Node 2.0 workflow load/save

이 PR에서는 전용 `EASYUSE_ANIMA_AIO_HOOK`을 추가하지 않는다.

---

### Phase H4 — 공개 AiO Hook API와 provider node

PR 유형: Contract

추가:

```text
easyuse_anima/extensions/aio.py
EasyUseAnimaAIOHookCombine
최소 예제 Hook provider
```

Generator 입력은 아직 추가하지 않거나 feature flag 아래에 둔다. 공개 API import와 Combine chain만 contract test로 검증한다.

---

### Phase H5 — `EASYUSE_ANIMA_AIO_HOOK` Generator 연결

PR 유형: Behavior + additive node contract

변경:

```python
"aio_hook": ("EASYUSE_ANIMA_AIO_HOOK", {"forceInput": True})
```

- descriptor validation
- session 생성
- stage before/after dispatch
- patch validation/apply
- namespaced metadata
- structured error
- cleanup

처음에는 다음 stage부터 적용한다.

1. postprocess
2. save/metadata
3. detailer 전후

이 단계들은 first-pass cache와 결합도가 낮다.

---

### Phase H6 — sampling 계열 Hook 확장

PR 유형: Behavior, stage별 분리

순서:

1. resources/after
2. conditioning/after
3. first_pass/before·after
4. highres/before·after
5. upscale/before·after

한 PR에 하나 또는 두 stage만 이관한다.

각 PR에서 다음을 검증한다.

- allowed patch field
- shape/type invariant
- model/conditioning identity 처리
- no-hook parity
- stage trace
- cleanup

---

### Phase H7 — #169 cache policy와 Hook fingerprint 통합

PR 유형: Behavior

stage 전환 PR과 분리한다.

구현:

- Hook change token
- first-pass 영향 stage 판정
- fingerprint 포함
- fingerprint 없음 시 bypass
- cache hit 후 Hook 재실행
- metrics에 hook-bypass reason 추가

검증:

- fingerprint 변경 후 miss
- postprocess-only Hook은 first-pass cache hit 유지
- first-pass-before Hook fingerprint 없음 시 bypass
- cache entry mutation isolation
- concurrent run에서 session/cache state 분리

---

### Phase H8 — #187 RuntimeServices wiring

PR 유형: Move/Contract

- AioOrchestrator process lifetime 재사용
- HookValidator/dispatcher factory 소유권 명시
- Hook session은 request scoped
- global Hook registry 없음
- initialize/shutdown idempotency
- test runtime에서 fake Hook/fake clock/fake cache 주입

Hook 동작 의미는 변경하지 않는다.

---

### Phase H9 — SDK 문서와 써드파티 예제

추가:

```text
docs/extensions/aio-hooks.md
docs/extensions/aio-hook-compatibility.md
examples/third_party_aio_hook/
```

예제:

- metadata observer
- postprocess image transformer
- conditioning patch
- preview emitter
- cleanup 등록
- Combine 순서

문서에 private API 비호환 정책과 supported import path를 명시한다.

---

## 11. PR 분리 원칙

| PR 종류 | 허용 | 금지 |
| --- | --- | --- |
| Move PR | 파일 이동, import, alias, 동일 동작 | Hook 실행, cache 정책 변경 |
| Contract PR | Protocol, dataclass, version, snapshot, migration | sampling 결과 변경 |
| Behavior PR | stage dispatch, Hook 적용, cache 의미 변경 | 대규모 파일 이동 |
| Documentation PR | ADR, SDK, 예제 | runtime 의미 변경 |

특히 다음 조합은 금지한다.

- AiO service 이동 + Hook 입력 추가
- stage pipeline 전환 + byte-budget cache
- Hook API contract + 모든 stage 적용
- `DETAILER_HOOK` 호환 + 전용 AiO Hook API
- RuntimeServices migration + Hook 실행 의미 변경

---

## 12. 테스트 계획

### 12.1 공개 계약

- `EASYUSE_ANIMA_AIO_HOOK` type 이름
- public import path와 `__all__`
- API version
- descriptor/event/patch field snapshot
- stage/phase enum
- Combine node contract
- AiO Generator optional input append parity

### 12.2 Hook chain

- 빈 chain
- 단일 Hook
- A/B before 순서
- B/A after 순서
- 오류 역순 전파
- close 역순
- 동일 definition에서 실행별 session 분리
- partial session creation 실패 cleanup

### 12.3 Stage integration

각 stage별:

- enabled 시 before/after 각 1회
- disabled 시 callback 정책 고정
- Hook 없음 결과 parity
- 허용 patch 반영
- 금지 patch 거부
- 잘못된 tensor shape 거부
- metadata namespace 충돌 방지
- preview 순서 유지

### 12.4 Detailer 호환

- Align Hook 단독
- 기존 Hook + Align wrapper
- crop size 호출 순서
- custom sampler/noise Hook 전달
- face/eye target 순서
- detection 없음
- Hook 예외

### 12.5 Cache/change detection

- Hook fingerprint stable key
- fingerprint 변경
- fingerprint 없음
- first-pass 영향 여부
- cache hit 후 after Hook 재실행
- Hook이 cache entry를 오염하지 않음
- `IS_CHANGED` 강제 실행 정책

### 12.6 Lifecycle/concurrency

- 실행 중 예외 후 session/thread/tensor reference 잔존 없음
- 동일 Hook definition을 연속 실행
- 별도 runtime 간 격리
- concurrent cache mutation과 Hook session 분리
- initialize/initialize/shutdown/shutdown

### 12.7 실제 통합

- 기존 0.5.2 workflow
- 최신 release workflow
- Legacy Canvas
- Node 2.0
- no-hook AiO 실제 queue
- Impact detailer Hook 실제 queue
- 샘플 third-party AiO Hook 실제 queue
- Registry packed archive에서 public extension module import

### 12.8 성능 기준

no-hook fast path는 다음을 만족해야 한다.

- 추가 tensor clone 없음
- 추가 model load 없음
- cache hit/miss 의미 변화 없음
- stage dispatcher가 no-op일 때 관측 가능한 GPU 메모리 증가 없음
- baseline 대비 실행 시간과 peak allocation을 기록하고 의미 있는 회귀가 있으면 원인 분석

고정 퍼센트만을 기계적으로 gate로 사용하기보다 동일 장비 baseline과 allocation trace를 함께 보관한다.

---

## 13. 주요 위험과 대응

| 위험 | 대응 |
| --- | --- |
| 써드파티가 내부 invariant 파괴 | immutable view + stage별 patch allowlist + runtime validation |
| 내부 구조가 공개 API로 굳음 | `extensions/aio.py`에 최소 DTO만 공개, internal state 비공개 |
| Hook 변경 후 stale cache | fingerprint 포함 또는 보수적 cache bypass |
| Hook object의 실행 간 state 공유 | definition/session 분리 |
| Hook 오류가 정상 이미지로 저장 | v1 fail-closed |
| 실행 순서 혼란 | Combine 연결 순서와 middleware trace 고정 |
| Hook이 core resource를 잘못 해제 | ownership 문서화, core-owned resource cleanup 금지 |
| API가 너무 강력해 유지 불가 | v1 stage skip/replacement 금지, provider API로 별도 분리 |
| optional dependency가 전체 pack import 실패 | Hook provider node에서 lazy import, capability prevalidation |
| workflow 계약 회귀 | optional forceInput append, node/workflow snapshot, Legacy/Node 2.0 검증 |
| global plugin registry 오염 | 명시적 소켓 연결, request-scoped chain만 지원 |

---

## 14. 완료 기준

### 백엔드 구조

- [ ] AiO node adapter에 실제 sampling/detailer/save 구현이 없다.
- [ ] `AioOrchestrator`는 request/state/stage 조립만 담당한다.
- [ ] stage가 독립 validation/run 계약을 가진다.
- [ ] Hook dispatcher와 cache는 명시적 owner를 가진다.

### Hook API

- [ ] `EASYUSE_ANIMA_AIO_HOOK` 공개 타입이 존재한다.
- [ ] 공개 API version과 import path가 snapshot으로 고정된다.
- [ ] Hook definition과 run session이 분리된다.
- [ ] stage별 read/write 계약이 문서화되고 검증된다.
- [ ] Combine 순서, 오류, cleanup 순서가 테스트된다.
- [ ] global 자동 등록이나 monkey patch가 필요 없다.

### 호환성

- [ ] Hook 미연결 기존 workflow 결과 계약이 유지된다.
- [ ] `DETAILER_HOOK`이 AiO 내부 Detailer에 전달된다.
- [ ] 기존 node ID, required input, output, widget serialization이 유지된다.
- [ ] Legacy Canvas와 Node 2.0을 모두 검증한다.

### 캐시·상태

- [ ] Hook fingerprint가 `IS_CHANGED`와 cache policy에 반영된다.
- [ ] fingerprint 없는 영향 Hook은 보수적으로 재실행/bypass된다.
- [ ] first-pass cache entry가 Hook에 의해 오염되지 않는다.
- [ ] Hook session과 cleanup이 run scoped다.

### 써드파티 지원

- [ ] 최소 예제 custom node pack이 제공된다.
- [ ] 공개 import 외 private import 비지원 정책이 명시된다.
- [ ] missing dependency/capability 오류가 이해 가능한 메시지를 제공한다.
- [ ] extension metadata에 Hook ID/version/API version이 기록된다.

---

## 15. 즉시 착수할 작업

```text
1. AiO Hook extension ADR 작성
2. 기존 AiO stage 순서·metadata·preview trace fixture 고정
3. Hook API v1 public DTO/Protocol 초안과 snapshot test 작성
4. #184 Prompt/Artist/Regional 및 AiO mechanical extraction 계속 진행
5. #168 typed config/migration 완료
6. #169 GenerationRequest/State/StageRunner contract 도입
7. no-op HookDispatcher seam 추가
8. `DETAILER_HOOK` 연결 PR을 독립적으로 구현
9. postprocess/save부터 전용 AiO Hook dispatch를 단계적으로 적용
10. 마지막에 first-pass cache fingerprint와 RuntimeServices ownership을 연결
```

---

## 16. 최종 결정 요약

```text
기존 Impact Detailer 확장
  → DETAILER_HOOK 입력으로 직접 지원

AiO 전체 확장
  → EASYUSE_ANIMA_AIO_HOOK 별도 공개 API

확장 발견 방식
  → 워크플로우의 명시적 연결만 지원

실행 상태
  → definition과 run-scoped session 분리

변경 방식
  → immutable event + validated patch

실행 순서
  → A.before → B.before → stage → B.after → A.after

캐시
  → fingerprint 포함 또는 보수적 bypass

오류
  → fail-closed, hook/stage/phase 명시

v1 비범위
  → stage skip/replacement, global registry, internal state 직접 노출
```

이 설계를 따르면 현재의 동작 보존형 백엔드 분해 원칙을 유지하면서, stage pipeline 완성 시점에 써드파티 확장 API를 안정적으로 연결할 수 있다.
