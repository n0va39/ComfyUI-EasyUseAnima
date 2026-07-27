# AiO Advanced Integrations Execution Roadmap

## 문서 상태

- 상태: **PLANNED / BLOCKED**
- 기준일: 2026-07-25
- 기준 브랜치: `dev`
- 기준 커밋: `df74cf9f65d481936122245e90db269113340c78`
- 외부 차단점: [#395](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/395) Registry 0.5.5 activation
- 기능 이슈:
  - [#409](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/409): stage별 고급 MODEL patch 범위
  - [#410](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/410): KJNodes Torch Compile 자동 추천
  - [#411](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/411): ComfyUI-ppm NegPip Off/On/Turbo
- 관련 기반:
  - [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169): AiO stage pipeline/cache
  - [#187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187): runtime/provider lifecycle

이 문서는 세 기능을 같은 대형 PR로 구현하지 않도록 선행 관계, 공통 소유권,
rollback 단위와 검증 순서를 고정한다. 기능 이슈의 behavior 요구가 이 문서보다
구체적이면 해당 이슈가 우선하며, 아키텍처 ADR과 `MAINTAINING.md`는 계속
최상위 정책이다.

`#395`가 닫히기 전에는 이 문서의 production implementation을 시작하지 않는다.
문서, 조사, fixture 설계는 가능하지만 D/E/G/H 및 새 AiO behavior 구현을 병행하지
않는다.

## 1. 현재 확인된 실행 구조

### 1.1 MODEL patch가 모든 stage에 전파됨

현재 AiO는 다음 순서로 하나의 MODEL 계보를 만든다.

```text
base MODEL
  -> LoRA
  -> AuraFlow sampling
  -> DAVE
  -> Safe PAG
  -> KJNodes FP16 / Sage / Torch Compile
  -> first pass
  -> Highres
  -> Detailer
  -> USDU
```

`ModelVariantResolver`는 Mod Guidance와 Spectrum용 variant만 추가하므로 DAVE,
Safe PAG, KJNodes patch는 first pass뿐 아니라 이후 sampling stage에도 남는다.
DAVE를 first pass에만 적용하고 Highres에서 제외하려면 이미 patch된 MODEL에서
wrapper를 제거하는 것이 아니라, 깨끗한 LoRA 기준 MODEL에서 stage별 variant를
만들어야 한다.

### 1.2 DAVE와 Compile의 precedence가 명시되지 않음

ComfyUI-Anima-DAVE upstream은 Anima Block Compile과 함께 사용할 때
`Compile -> DAVE` 순서를 요구한다. 현재 Easy Use Anima의 함수 순서는 DAVE 뒤에
KJ Torch Compile을 호출한다. #409는 stage scope와 함께 deterministic patch-order
contract를 도입한다.

### 1.3 Torch Compile은 수동 설정만 제공

현재 Advanced Options는 KJNodes의 주요 compile 입력을 노출하지만 환경 진단이나
추천 기능은 없다.

```text
backend
fullgraph
mode
dynamic
compile_transformer_blocks_only
dynamo_cache_size_limit
debug_compile_keys
disable_dynamic_vram
```

#410은 compile을 실행하는 버튼이 아니라 현재 환경과 workload를 읽어 추천값,
이유, 경고를 반환하고 dialog draft에 적용하는 기능을 추가한다.

### 1.4 NegPip은 MODEL + CLIP + conditioning 경계에 걸침

ComfyUI-ppm의 `CLIPNegPip`은 MODEL과 CLIP을 함께 patch한다. 따라서 일반 MODEL
patch 목록에 단순히 한 항목을 추가해서는 안 된다. LoRA 이후, prompt encoding
이전, stage MODEL variant 생성 이전에 명시적인 MODEL/CLIP integration boundary가
필요하다.

Turbo는 추가로 다음 behavior를 소유한다.

```text
negative prompt contribution × -1
positive execution conditioning에 결합
sampling stage effective CFG = 1
원본 prompt와 저장 CFG는 보존
```

## 2. 공통 유지보수 원칙

1. 세 기능은 각각 독립 이슈와 독립 rollback 단위를 가진다.
2. settings/schema/migration 변경은 versioned contract와 golden fixture를 동반한다.
3. 기존 workflow/profile의 누락 key를 새 기본 behavior로 조용히 해석하지 않는다.
4. optional custom node는 해당 기능이 선택될 때만 요구한다.
5. 외부 custom-node source를 복사하거나 private module을 직접 import하지 않는다.
6. installed node mapping과 node-info contract를 call-time으로 확인한다.
7. MODEL/CLIP clone, wrapper, compile variant는 run owner와 cleanup owner가 명확해야 한다.
8. patch order는 dictionary 순서, UI 순서 또는 우연한 import 순서에 의존하지 않는다.
9. first-pass cache key는 실제 first-pass execution plan만 반영한다.
10. user-facing 원본 설정과 normalized/effective execution setting을 구분한다.
11. UI에서 runtime override를 숨기지 않는다.
12. disabled feature가 package import, 다른 stage 또는 Registry validation을 깨뜨리면 안 된다.
13. 한 PR에서 Move, Contract, Behavior를 섞지 않는다.
14. broad utility module이나 arbitrary plugin registry를 만들지 않는다.
15. 기존 node id, socket, output, workflow serialization은 별도 breaking issue 없이 변경하지 않는다.

## 3. 확정 실행 순서

```text
BLOCKED: #395 Registry activation 및 release lane 종료
  ↓
ADV-00 current-dev re-audit
  ↓
#409 AIO-SCOPE-01 Contract/migration
  ↓
#409 AIO-SCOPE-02 StageModelVariantResolver
  ↓
#409 AIO-SCOPE-03 DAVE UI/cutover
  ↓
#409 AIO-SCOPE-04 other-patch opt-in audit
  ↓
#410 AIO-COMPILE-01 diagnostics
  ↓
#410 AIO-COMPILE-02 recommendation evidence/policy
  ↓
#410 AIO-COMPILE-03 UI draft apply
  ↓
#410 AIO-COMPILE-04 live matrix
  ↓
#411 AIO-NEGPIP-01 external contract/license boundary
  ↓
#411 AIO-NEGPIP-02 On mode
  ↓
#411 AIO-NEGPIP-03 Turbo conditioning Contract
  ↓
#411 AIO-NEGPIP-04 Turbo implementation/UI/live matrix
  ↓
ADV-RC integrated compatibility gate
  ↓
별도 release planning
```

#410과 #411의 조사/fixture 작업은 #409 Contract 이후 파일 경계가 겹치지 않으면
병렬로 수행할 수 있다. 그러나 production implementation은 다음 공통 파일 때문에
기본적으로 직렬화한다.

```text
generation defaults/schema/migrations
model preparation/lifecycle
first-pass cache key
Advanced Options dialog
optional dependency discovery
profile fixtures
```

병렬 PR을 열려면 allowed-file set이 겹치지 않고 앞 PR의 schema revision에 의존하지
않음을 PR 본문에서 증명해야 한다.

## 4. ADV-00 — 재개 전 재감사

#395가 닫힌 직후 바로 구현하지 않고 최신 `origin/dev`에서 다음을 다시 확인한다.

- #409/#410/#411과 겹치는 열린 PR/branch
- AiO schema/version과 migration head
- `ModelVariantResolver`와 `EphemeralModelRegistry` 변경
- KJNodes `TorchCompileModelAdvanced` node input contract
- ComfyUI-Anima-DAVE wrapper/order contract
- ComfyUI-ppm `CLIPNegPip` input/output/license/version
- current full runner와 package closure
- 0.5.5 이후 새 P0/P1 bug

재감사 결과 외부 node id나 signature가 달라졌으면 issue body와 fixture부터 수정한다.
과거 조사 결과를 그대로 production contract로 사용하지 않는다.

## 5. #409 실행 manifest

### AIO-SCOPE-01 — Contract와 migration

- 유형: Contract
- 목표:
  - stage id `first_pass/highres/detailer/upscale` 고정
  - patch별 `stage_scope` schema
  - legacy scope 누락 설정의 all-stage parity migration
  - 신규 DAVE first-pass-only default
  - patch precedence revision
  - first-pass cache-key sensitivity 계약
- production behavior 변경은 migration facade에 필요한 최소 범위로 제한한다.

허용 후보:

```text
easyuse_anima/aio/generation_defaults.py
easyuse_anima/aio/generation_migrations.py
easyuse_anima/aio/generation_normalization.py
easyuse_anima/aio/schemas/*
tests/test_aio_generation_*.py
settings/profile golden fixtures
```

금지:

- stage MODEL 실제 cutover
- DAVE UI
- Torch recommendation
- NegPip

### AIO-SCOPE-02 — StageModelVariantResolver

- 유형: Behavior/architecture
- `model_with_lora`를 깨끗한 run 기준으로 보존한다.
- stage별 patch plan을 lazy 적용한다.
- 같은 signature는 run 안에서 재사용한다.
- 다른 stage/patch signature는 격리한다.
- cleanup을 `EphemeralModelRegistry` 또는 명시적 인접 owner가 담당한다.
- disabled stage/patch는 dependency lookup을 하지 않는다.

핵심 invariant:

```text
DAVE first-pass-only
  -> first-pass MODEL has anima_dave
  -> highres/detailer/upscale MODEL has no anima_dave
```

### AIO-SCOPE-03 — DAVE cutover/UI

- 유형: Feature
- First pass only / All sampling stages / Custom UI
- fresh default는 first-pass-only
- migrated legacy profile은 all-stage
- Compile과 같은 stage에서 `Compile -> DAVE`
- stage metadata와 live output comparison

### AIO-SCOPE-04 — opt-in audit

- 유형: Contract/docs/gate
- Safe PAG, FP16 accumulation, SageAttention, Torch Compile 각각의 stage 적용 가능성을 결정한다.
- run-global torch setting과 stage-local MODEL wrapper를 구분한다.
- 지원 근거가 없는 patch에 generic scope UI를 자동 추가하지 않는다.
- 결정:
  - DAVE만 현재 네 sampling stage scope를 지원한다.
  - Safe PAG는 stage-local 후보지만 temporary shared-module mutation 검증을 #440으로 분리한다.
  - SageAttention은 clone-local 후보지만 experimental/`allow_compile` 검증을 #441로 분리한다.
  - FP16 accumulation과 Torch Compile은 현재 upstream의 process-global/shared-registry 계약 때문에
    독립 stage scope를 지원하지 않는다.
  - #440/#441은 현재 `#409 -> #410 -> #411` queue를 선행하지 않는다.

## 6. #410 실행 manifest

### AIO-COMPILE-01 — Environment diagnostics

- 유형: Contract
- read-only endpoint 또는 동일한 adapter 경계
- PyTorch/CUDA/accelerator/GPU VRAM/KJ input contract 수집
- 외부 network/telemetry/지속 저장 금지
- 버튼이 compile 또는 benchmark를 실행하지 않는다는 gate

응답은 값뿐 아니라 다음을 포함한다.

```text
supported
profile id
recommended values
environment summary
reason codes
warnings
policy version
```

### AIO-COMPILE-02 — Recommendation policy

- 유형: Contract/evidence
- pure recommendation function
- workload 분류:
  - fixed_shapes
  - variable_shapes
  - unknown
- VRAM/shape/stage 조합 benchmark
- cold/warm 시간, peak VRAM, recompile, graph break 기록
- evidence 없는 조합을 최적이라고 표시하지 않는다.

공통 안전축 후보:

```text
backend = inductor
fullgraph = false
compile_transformer_blocks_only = true
debug_compile_keys = false
```

`mode`, `dynamic`, cache, dynamic-VRAM 정책은 evidence로 결정한다.

### AIO-COMPILE-03 — UI draft apply

- 유형: Feature
- `[현재 환경에 맞게 자동 설정]`
- loading/error/unsupported state
- 추천 diff, 이유, 경고 표시
- dialog control만 변경
- Cancel 시 설정 불변
- Apply 후에만 profile/settings 저장

### AIO-COMPILE-04 — Live matrix

- fixed resolution
- Highres
- Detailer crop
- USDU tiles
- LoRA
- DAVE
- SageAttention
- Legacy Canvas
- Node 2.0
- KJNodes old/new input drift

## 7. #411 실행 manifest

### AIO-NEGPIP-01 — External contract/license boundary

- 유형: Contract
- node id `CLIPNegPip`
- MODEL+CLIP input/output
- V3 `execute()`/`NodeOutput` adapter fixture
- repeated invocation/idempotency
- optional dependency failure isolation
- ComfyUI-ppm source direct-import/vendor 금지 gate

### AIO-NEGPIP-02 — On mode

- 유형: Feature
- Off parity
- On에서 PPM MODEL+CLIP patch 1회
- 기존 positive/negative conditioning과 CFG 유지
- first-pass cache mode separation
- metadata mode 기록

### AIO-NEGPIP-03 — Turbo Contract

- 유형: Contract
- negative prompt에 추가 -1 multiplier를 적용하는 pure transformer
- top-level comma/newline/nesting/escape/weight 규칙
- neutral negative conditioning shape/metadata
- sampling stage effective CFG=1
- 저장 CFG와 원본 prompt 보존
- policy revision

### AIO-NEGPIP-04 — Turbo implementation/UI

- 유형: Feature
- Off / On (standard) / Turbo selector
- dependency UX
- runtime CFG override 표시
- first/highres/detailer/USDU integration
- Artist Mix/Mod Guidance/Spectrum/DAVE/KJ compatibility matrix
- Legacy/Node 2.0/live output comparison

## 8. Patch 및 conditioning precedence

최종 precedence는 #409와 #411 Contract에서 fixture로 고정한다. 초기 목표는 다음과
같다.

```text
resource load
  -> LoRA MODEL/CLIP
  -> NegPip MODEL/CLIP (On/Turbo)
  -> prompt execution conditioning encode
  -> stage MODEL variant
       -> KJ compile
       -> DAVE
       -> 검증된 나머지 stage MODEL patches
  -> stage-specific Spectrum/Mod Guidance sampler patch
  -> sample
```

실제 Comfy wrapper nesting 때문에 prompt encode보다 MODEL variant 생성이 먼저
필요할 수 있다. 중요한 invariant는 다음과 같다.

- NegPip은 patched CLIP으로 prompt를 encode한다.
- DAVE는 Compile과 함께 사용할 때 compiled block을 대상으로 한다.
- stage에서 제외된 patch는 해당 MODEL variant에 존재하지 않는다.
- patch가 disabled이면 외부 node lookup도 하지 않는다.
- 같은 wrapper key가 queue마다 누적되지 않는다.

Contract PR에서 runtime trace로 실제 호출 순서를 증명한 뒤 위 도식을 필요에 따라
정정한다.

## 9. Settings와 migration 정책

세 기능 모두 기존 user data를 보호한다.

### #409

```text
기존 설정에 stage_scope 없음 -> legacy all-stage
새 DAVE 설정 -> first-pass-only
```

### #410

```text
기존 수동 compile 설정 -> 그대로 유지
추천 버튼 -> 명시적 클릭과 Apply가 있을 때만 변경
```

### #411

```text
기존/신규 기본 -> Off
On/Turbo -> 사용자가 선택
Turbo -> 저장 CFG를 덮어쓰지 않고 effective CFG만 1
```

각 migration은 다음을 가져야 한다.

- versioned step
- pure migration
- no-write-on-read 정책과 현재 저장 owner 준수
- profile/workflow golden fixture
- downgrade/rollback 설명
- frontend/backend default parity

## 10. Cache 및 lifecycle 계약

### Cache

first-pass cache key는 다음 실제 first-pass behavior를 구분한다.

- first-pass patch plan과 parameter
- patch precedence revision
- compile policy/variant signature
- NegPip mode/policy
- Turbo derived conditioning fingerprint
- effective first-pass CFG

Highres-only DAVE scope 변경처럼 first-pass 결과에 영향을 주지 않는 변경은 불필요한
first-pass miss를 만들지 않는다.

### Lifecycle

run 종료와 exception path에서 다음을 정리한다.

- stage MODEL clones
- compiled variants
- DAVE/Safe PAG wrappers
- NegPip MODEL/CLIP clones
- temporary sampler patches

process-global torch setting은 MODEL clone과 같은 cleanup 정책으로 다루지 않는다.
KJNodes callback contract를 사용해 pre-run/cleanup을 보장하거나, 별도 run-global
ownership 결정을 기록한다.

## 11. 공통 통합 검증

자동 검증:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
comfy node validate
comfy node pack
```

실제 archive에서 다음을 확인한다.

- 새 Python/JavaScript/locale/schema 파일
- optional dependency 없이 package import
- root shim 재확장 없음
- workflow/profile fixtures

Live matrix:

```text
Canvas: Legacy / Node 2.0
DAVE scope: first only / all / custom
Torch Compile: off / manual / recommended
NegPip: off / on / turbo
Stages: first / highres / detailer / USDU / ResShift
Prompt: empty negative / normal / weighted / nested
Patches: LoRA / Safe PAG / Sage / Spectrum / Mod Guidance
Failure: missing DAVE / KJ / PPM
Queue: repeated / concurrent / cancelled / exception
```

품질 비교:

- DAVE first-only와 all-stage의 Highres 색감/구조 비교
- compile off/on output tolerance와 artifact 확인
- NegPip On/Turbo negative concept 억제 비교
- Turbo CFG override가 모든 sampling stage에서 일관적인지 확인

## 12. Stop conditions

다음 상황에서는 현재 PR을 확장하지 않고 blocker를 기록한다.

- #395가 아직 닫히지 않음
- 최신 dev에서 동일 surface의 구현 PR이 열림
- settings migration 없이 기존 결과가 바뀜
- stage patch를 제거하려고 private MODEL dictionary를 수정해야 함
- KJ/PPM/DAVE private source import가 필요함
- 외부 node signature가 조사 fixture와 다름
- Turbo prompt 변환이 원문을 손상하거나 parser가 모호함
- compile 추천에 benchmark/evidence 없이 특정 GPU 강제값이 필요함
- disabled optional feature가 package import를 깨뜨림
- cleanup owner를 정의할 수 없음
- 한 PR에서 Contract와 Behavior를 분리할 수 없음
- full/package/live gate가 behavior regression과 구조 변경을 구분하지 못함

## 13. Codex 시작 지시

`#395`가 열려 있는 동안:

```text
이 문서와 #409/#410/#411을 읽되 production implementation을 시작하지 않는다.
새 D/E/G/H 또는 AiO advanced feature branch를 만들지 않는다.
외부 node contract 변화가 발견되면 issue와 문서만 갱신한다.
```

`#395`가 닫힌 뒤:

```text
1. 최신 origin/dev와 open PR/branch를 확인한다.
2. ADV-00 재감사를 수행한다.
3. #409 AIO-SCOPE-01 하나만 선택한다.
4. stage id, migration, precedence, cache-key Contract와 golden fixtures만 만든다.
5. StageModelVariantResolver, UI, Torch recommendation, NegPip behavior는 같은 PR에 넣지 않는다.
6. quick/full/package gate와 exact base/head SHA를 기록한다.
7. 다음 unit을 READY로 바꾸되 자동 merge/release는 수행하지 않는다.
```

## 14. 릴리스 정책

이 문서는 다음 버전 번호를 미리 예약하지 않는다. 세 기능은 독립적으로 릴리스될
수 있지만, #409의 stage/precedence contract가 안정되지 않은 상태에서 #410 또는
#411만 부분 공개하지 않는다.

release candidate를 만들 때 다음을 별도로 결정한다.

- 세 기능을 한 minor release에 묶을지
- #409/DAVE만 먼저 공개할지
- optional dependency minimum version
- workflow/profile migration note
- Registry scanner/package evidence
- 사용자에게 필요한 restart/hard-refresh 안내
