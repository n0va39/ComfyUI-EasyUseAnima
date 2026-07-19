# Frontend Maintenance Roadmap

## 목적

이 문서는 Issue #14의 초기 모듈 분리 작업 이후 남은 프론트엔드 유지보수
범위를 현재 `dev` 기준으로 다시 정리한다. 과거 실행 계획과 현재 상태를
분리하고, 한 이슈가 끝없이 커지지 않도록 Issue #14 종료 범위와 후속 작업을
명시하는 것이 목적이다.

- 현재 로드맵: 이 문서
- active Goal의 task/branch/worktree와 통합 증거 ledger:
  `docs/development/frontend-maintenance-execution-plan.md`
- 초기 실행 계획과 체크리스트:
  `docs/development/issue-14-frontend-js-maintenance.md`
- 대상 이슈: `https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/14`

이 문서의 수치는 영구 기준이 아니라 점검 스냅샷이다. 구현을 시작할 때마다
`dev`, 원격 브랜치, 파일 크기, 테스트 수를 다시 확인한다.

## 점검 기준

점검일: 2026-07-15

기준 브랜치와 커밋:

```text
base branch: dev
base commit: fb5c8c9eef06be47cbb86afd5729fd9701b6c74c
worktree branch: codex/docs-browser-smoke-matrix
scope: follow-up maintenance status and dual-canvas validation contract
```

Issue #14는 PR #58 병합 후 2026-07-13에 완료 상태로 닫혔다. 다음 변경은
Issue #14 범위에서 `dev`에 병합됐다.

| PR | 병합 커밋 | 완료 범위 |
| --- | --- | --- |
| #18 | `4eb7992` | 공통 API helper, Prompt Studio 모듈 분리, no-build JS typecheck, Vite 보류 결정 |
| #46 | `e75eb96` | 미사용 코드 검사, 통합 frontend 검사 스크립트 |
| #47 | `2c818b6` | Main/Advanced와 Regional의 prompt highlight parser/renderer core 공통화 |
| #48 | `781b4c4` | Issue #14 현재 로드맵과 종료 범위 정리 |
| #49 | `c7897a8` | 저장소 소유 project/frontend/unittest 검증 명령 계약 통합 |
| #50 | `55a68ea` | Prompt Studio DOM highlight overlay geometry/preview core 공통화 |
| #51 | `83d1600` | Regional schema, resolution, serialization, mask geometry pure-data 분리 |
| #52 | `ebf9c66` | Regional UI/runtime 모듈 분리, node별 lifecycle ownership과 양쪽 canvas 검증 |
| #53 | `24b13b6` | legacy common 호환 re-export 축소, Regional adapter 직접 연결, 재귀 typecheck 확장 |
| #58 | `e302d1d` | 종료 검증, 후속 #54-#57 분리, Issue #14 완료 처리 |

## 현재 상태

### 완료된 기반

- `easyuse_anima_prompt_studio.js`는 extension 등록과 runtime 조립만 담당하는
  얇은 entry 파일이다.
- 반복되던 settings, JSON request, prompt classification 요청은
  `easyuse_anima_api.js`로 모였다.
- Main/Advanced Prompt Studio 책임은 `web/js/prompt_studio/` 아래 모듈로
  분리됐다.
- prompt 문법 파싱, token matching, highlight HTML 생성은
  `prompt_studio/highlight_core.js`가 소유한다.
- overlay geometry, text metric 복사, autocomplete preview 조합은
  `prompt_studio/highlight_overlay_core.js`가 소유한다.
- Regional의 상수, field/config schema와 migration, resolution 규칙,
  serialization 정규화, mask geometry/hit-test는
  `prompt_studio/regional/` 아래 DOM-free 모듈이 소유한다.
- Regional의 field/mask editor, layout, runtime, extension hook과 node별 cleanup은
  같은 디렉터리의 UI/runtime 모듈이 나눠 소유한다. entry 파일은 의존성 조립과
  extension 등록만 담당한다.
- Regional 화면별 text, style, tooltip, highlight state와 textarea adapter는
  `prompt_studio/regional/editor_adapter.js`가 소유한다. 기존
  `easyuse_anima_prompt_studio_common.js`는 호환 re-export만 유지한다.
- Regional 모듈은 recursive typecheck, import-cycle, no-unused와 명시적 runtime
  installation guard의 검사 대상이다.
- `tools/check_frontend.ps1`은 전체 frontend JS 문법 검사, parser/renderer와
  overlay 및 Regional pure-data/runtime lifecycle semantic smoke, 고정 버전
  TypeScript 검사를 한 번에 실행한다.
- `noUnusedLocals`와 `noUnusedParameters`가 현재 typecheck 범위에 적용된다.
- Vite/TypeScript build chain을 당장 도입하지 않고 raw ES module과 no-build
  typecheck를 유지하기로 결정했다.

### 정량 스냅샷

`web/js`에는 JavaScript 111개, 총 38,914줄이 있다. `jsconfig.json`의 명시적
include 패턴은 중복 제거 기준 107개·31,497줄로 전체 라인의 80.9%다. 이 중
Prompt Studio entry 2개와 `prompt_studio/**/*.js` 55개는 총 57개·14,587줄로
전체 라인의 37.5%다. import를 따라 추가로 검사되는 dependency는 이 수치에
포함하지 않았다.

| 파일 | 줄 수 | 전체 비율 | 현재 판단 |
| --- | ---: | ---: | --- |
| `easyuse_anima_aio.js` | 4,278 | 11.0% | 가장 큰 후속 hotspot |
| `easyuse_anima_lora_preset.js` | 943 | 2.4% | canvas/UI/state lifecycle이 남음 |
| `easyuse_anima_autocomplete.js` | 1,860 | 4.8% | popup, input runtime이 남음 |
| `easyuse_anima_settings.js` | 625 | 1.6% | 등록과 fallback lifecycle 중심 entry |
| `prompt_studio/regional/editor_adapter.js` | 1,406 | 3.6% | Regional text/style/tooltip/highlight/textarea adapter |
| `easyuse_anima_prompt_studio_common.js` | 5 | 0.0% | 이전 import 경로를 위한 호환 re-export |
| `easyuse_anima_prompt_studio_regional.js` | 64 | 0.2% | registration과 runtime 조립만 담당 |

앞의 5개 파일이 전체 frontend JS의 약 23.4%를 차지한다. 줄 수 자체를
목표로 삼지는 않지만, 책임 경계와 검증 비용이 이 파일들에 집중돼 있다는
신호로 사용한다. Regional entry의 축소는 줄 수보다 소유권 이동의 결과다.

### Phase 3 checkJs coverage ratchet (2026-07-19)

TypeScript 6.0.3으로 `web/js`의 기존 미포함 root entry를 각각 다시 측정했다.
오류가 0개인 `easyuse_anima_api.js`, `easyuse_anima_i18n.js`,
`easyuse_anima_prompt_rules.js`, `easyuse_anima_prompt_studio_common.js`는
`jsconfig.json`의 명시적 include로 승격했다. root entry는 typecheck 대상 또는
아래 debt 중 하나여야 하며, 계약 테스트가 새 미분류 entry, include 후 남은
debt, root wildcard 추가를 실패시킨다.

Phase 4a에서는 `easyuse_anima_settings.js`의 4개 오류(TS2307 1개,
TS2339 3개)를 host import 한 줄 suppression과 좁은 window alias로 해소하고
명시적 include로 승격했다. 현재 root entry 11개 중 7개가 typecheck 대상이고,
debt는 4개 entry·36개 오류다.

현재 debt ledger:

| TODO 파일 | 총 오류 | TypeScript 오류 코드별 개수 |
| --- | ---: | --- |
| `easyuse_anima_aio.js` | 16 | TS1117 4, TS2307 4, TS2339 2, TS2345 2, TS6133 4 |
| `easyuse_anima_autocomplete.js` | 5 | TS2307 1, TS2339 2, TS6133 2 |
| `easyuse_anima_lora_preset.js` | 10 | TS2304 4, TS2307 2, TS2345 1, TS6133 3 |
| `easyuse_anima_naia.js` | 5 | TS2307 2, TS2345 2, TS6133 1 |

코드는 TS1117 duplicate property, TS2304 undeclared host global, TS2307 외부
Comfy import resolution, TS2339 DOM/window property shape, TS2345 argument/shape
mismatch, TS6133 unused declaration/parameter를 뜻한다. TODO는 각 파일의 오류를
동작 변경이나 광범위한 suppression 없이 해소한 뒤, 같은 PR에서 해당 entry를
`jsconfig.json` include로 옮기고 테스트와 이 ledger의 debt에서 제거하는 것이다.

재현 명령은 `jsconfig.json`과 같은 compiler option을 파일별로 적용한다.

```powershell
$files = @(
  "web/js/easyuse_anima_aio.js",
  "web/js/easyuse_anima_autocomplete.js",
  "web/js/easyuse_anima_lora_preset.js",
  "web/js/easyuse_anima_naia.js"
)
foreach ($file in $files) {
  npx --yes --package "typescript@6.0.3" -- tsc `
    --allowJs --checkJs --noEmit --target ES2022 --module ES2022 `
    --moduleResolution Bundler --lib "ES2022,DOM,DOM.Iterable" `
    --skipLibCheck --noUnusedLocals --noUnusedParameters --strict false `
    --pretty false $file
}
```

### Prompt Studio adapter 경계

- `prompt_studio/regional/editor_adapter.js`와 `prompt_studio/highlight.js`에는
  화면별 highlight adapter 흐름이 각각 남아 있다.
- pixel 변환, scrollbar padding, overlay bounds, text metric 복사,
  preview HTML, overlay 위치 동기화는 DOM overlay core로 공통화됐다.
- 색상 설정, tooltip 문구, 설정 저장소, node별 highlight state와 listener
  lifecycle은 화면별 adapter에 남기는 편이 안전하다.
- Regional entry에서 constants, schema/migration, resolution, serialization,
  mask geometry/hit-test뿐 아니라 DOM editor, layout, runtime, hook 설치와
  lifecycle cleanup도 분리됐다.
- Regional entry는 `editor_adapter.js`를 직접 import한다.
  `easyuse_anima_prompt_studio_common.js`는 이전 경로 호환용 re-export만 유지하며
  settings, tooltip, style, listener lifecycle을 소유하지 않는다.

## 과거 문서에서 바로잡는 내용

초기 계획 문서는 PR #18의 실행 기록으로 보존한다. 현재 작업 기준으로는 다음
내용을 그대로 사용하면 안 된다.

1. PR #18은 더 이상 active PR이 아니다. 이미 `dev`에 squash merge됐다.
2. 초기 tracking checklist의 Phase 1-4 완료 표시는 당시 합의한 범위의
   완료를 뜻한다. frontend 전체가 모듈화 또는 typecheck됐다는 뜻이 아니다.
3. typecheck의 명시적 include는 frontend 전체가 아니라 Prompt Studio 중심
   범위다.
4. Vite/TypeScript는 도입 완료가 아니라 도입 보류 결정이 완료된 상태다.
5. v0.24.0 smoke 기록은 PR #18의 과거 증거다. 이후 변경의 현재 runtime
   검증을 대신하지 않는다.
6. 저장소가 문서화하고 실제 helper가 실행하는 전체 Python suite는
   `python -m unittest discover -s tests`다. `pytest` 호환성은 현재
   `pyproject.toml`에 구성돼 있지 않으므로 별도 결정을 거치기 전에는 공식
   full-suite 계약으로 간주하지 않는다.

## 범위 원칙

- PR 하나에는 한 종류의 위험과 하나의 reviewable ownership 경계를 넣는다.
- 기계적인 pure extraction을 지나치게 쪼개지 않고 관련 helper 2-3개 또는
  하나의 lifecycle 경계를 묶는다. 실제 동작 변경은 별도 PR로 유지한다.
- pure data와 pure rendering helper를 DOM lifecycle보다 먼저 분리한다.
- 이동과 동작 변경을 같은 PR에 섞지 않는다.
- node type, widget/socket 이름, `widgets_values` 순서, serialized property,
  API route와 payload를 유지한다.
- helper import만으로 extension 등록, fetch, 전역 DOM 변경이 발생하지 않게
  한다.
- 새 모듈은 `// @ts-check`, JSDoc, no-unused gate에 포함한다.
- Node 2.0 DOM UI와 legacy canvas를 별도 검증 표면으로 취급한다.
- line count 감소보다 소유권, 의존 방향, 독립 테스트 가능성을 우선한다.
- Vite 도입은 raw module 배포가 실제 장애가 되거나 no-build 검사로 잡지 못하는
  문제가 반복될 때 다시 평가한다.
- 기계적 이동은 behavior와 test-contract 감사를 거친다. 실제 동작 변경이나
  복잡한 UI lifecycle은 architecture 감사를 추가한다.
- 병합된 경계, 검증 증거, 보류 finding은 owning Issue의 누적 ledger에 남긴다.
- GitHub mutation이 abort 또는 timeout으로 끝나면 재시도 전에 원격 상태를
  read-back한다.

## Issue #14 종료 로드맵

아래 작업까지 Issue #14 범위로 본다. AiO, LoRA Preset, Autocomplete,
Settings의 대형 분리는 별도 후속 이슈로 넘긴다.

예상 시간은 구현과 로컬 검증에 필요한 순수 작업 시간이며, 리뷰 대기와 사용자
수동 확인 시간은 포함하지 않는다.

### R0. 현재 로드맵 정리

예상: 0.25일

- 이 문서를 현재 source of truth로 연결한다.
- 초기 계획 문서를 historical record로 표시한다.
- 완료, 잔여, 후속 범위를 분리한다.

완료 기준:

- 개발 문서 진입점에서 현재 로드맵과 과거 계획을 구분할 수 있다.
- 근거 커밋, 수치 산출 기준, 갱신 명령이 문서에 있다.

### R1. 검증 명령 계약 정리

예상: 0.5일

결정:

- 공식 project 검사는 `tools/check_project.ps1`로 통합한다.
- 공식 frontend 검사는 이 entrypoint가 호출하는
  `tools/check_frontend.ps1`로 유지한다.
- 공식 Python full suite는 `unittest discover`로 고정한다.
- `pytest`는 공식 runner로 지원하지 않는다. 현재 custom-node root package를
  top-level `__init__` module로 수집해 test body 실행 전에 실패하며,
  import mode, rootdir, ignore 옵션만으로 해결되지 않는다.
- workspace의 ComfyUI 테스트 지침과 helper는 저장소가 소유한 runner 계약을
  우선하도록 정렬한다.

이 PR에는 frontend 구조 변경을 넣지 않는다.

### R2. DOM highlight overlay core 공통화

예상: 0.5-1일

구현:

- `prompt_studio/highlight_overlay_core.js`가 geometry, text metric,
  autocomplete preview 조합을 소유한다.
- Main/Advanced와 Regional adapter는 화면별 renderer와 escape 함수만
  factory에 주입한다.
- 설정, tooltip, node/field state, listener와 classification lifecycle은
  기존 adapter에 유지한다.
- `frontend_highlight_overlay_core_smoke.mjs`가 scrollbar padding, bounds,
  metric 복사, scroll 동기화, preview와 stale-preview fallback을 검증한다.

공통화 범위:

- CSS pixel parsing과 scrollbar padding
- input/textarea bounds 측정
- text metric 복사
- autocomplete preview HTML 조합
- overlay bounds와 scroll 위치 동기화

화면별 adapter에 유지할 항목:

- 색상과 tooltip 내용
- settings 반영
- node/field별 state
- listener 설치와 제거 정책
- classification 예약 정책

완료 기준:

- overlay geometry와 preview 조합의 구현이 한 곳에 있다.
- Main/Advanced와 Regional adapter의 공개 함수와 호출 순서는 유지된다.
- semantic smoke가 두 adapter의 동일한 geometry/preview 계약을 검증한다.
- Advanced와 Regional에서 overlay 수, scroll alignment, autocomplete preview,
  tooltip 충돌을 확인한다.

### R3. Regional pure data 분리

예상: 1-1.5일

우선 분리 후보:

```text
web/js/prompt_studio/regional/
  constants.js
  schema.js
  resolution.js
  serialization.js
  mask_geometry.js
```

현재 구현:

- 위 5개 모듈이 `web/js/prompt_studio/regional/`에 분리돼 있다.
- `frontend_regional_pure_data_smoke.mjs`가 field/config migration,
  resolution, mask geometry, save/reload 정규화를 DOM 없이 검증한다.
- legacy common은 기존 Regional 상수 export를 호환 re-export로 유지한다.

완료 기준:

- field/config normalization과 migration이 DOM 없이 테스트된다.
- resolution과 mask geometry helper가 canvas나 app 전역을 참조하지 않는다.
- 기존 workflow의 field id, label, value, mask id/geometry, resolution 설정이
  save/reload 후 동일하다.
- value-only 변경이 input socket 순서를 바꾸지 않는다.

### R4. Regional UI와 runtime 분리

예상: 1.5-2.5일

우선 분리 후보:

```text
web/js/prompt_studio/regional/
  field_editor.js
  mask_editor.js
  layout.js
  lifecycle.js
  runtime.js
  extension.js
```

현재 구현:

- `easyuse_anima_prompt_studio_regional.js`는 64줄의 composition entry로
  축소됐고 extension 등록은 이 파일 한 곳에서만 수행한다.
- `runtime.js`는 widget/config/socket/serialization/executed state를,
  `field_editor.js`는 field DOM과 add/delete/move/rename을 소유한다.
- `mask_editor.js`는 mask canvas draw와 modal/popover를,
  `layout.js`는 editor size/highlight scheduling을 소유한다.
- `lifecycle.js`는 node별 animation frame과 cleanup resource를 keyed state로
  관리하고 node 제거 시 listener, popover, modal, editor를 해제한다.
- `extension.js`의 prototype/app wrapper는 original return value와 `this`를
  보존하고 중복 설치를 차단한다. extension setup은 초기화 전 `app.graph`를
  읽지 않는다.
- `frontend_regional_runtime_smoke.mjs`가 wrapper, lifecycle replacement와
  dispose, field move, save/queue sync, 초기 graph 접근 금지를 DOM 없이
  검증한다.

브라우저 검증:

- ComfyUI 0.27.0 Codex test instance의 legacy canvas와 Node 2.0에서 workflow
  load, field add/delete/move/rename, mask 생성/편집/할당, resize와 editor wheel
  소유권, save/reload를 각각 확인했다.
- Node 2.0에서 mask popover를 연 상태로 node를 제거했을 때 editor, popover,
  modal이 함께 정리되고 undo 후 node가 복구되는 것을 확인했다.
- queue 제출과 Regional save-sync wrapper 실행은 확인했다. 테스트 workflow의
  실제 생성은 test instance에 `comfyui-spectrum-ksampler`가 없어
  `AnimaModGuidance` dependency 오류로 종료됐으며 Regional refactor 오류는
  아니었다.

완료 기준:

- `easyuse_anima_prompt_studio_regional.js`는 extension 등록과 runtime 조립을
  중심으로 축소된다.
- mask canvas draw/hit-test와 editor lifecycle이 분리된다.
- hook wrapping은 original return value와 `this`를 보존하고 중복 설치를 막는다.
- listener, observer, animation frame, popover가 node 제거 시 정리된다.
- Regional workflow load, mask 편집, field add/delete/move/rename, queue,
  save/reload를 직접 검증한다.
- Node 2.0과 legacy canvas에서 resize/wheel 소유권을 각각 확인한다.

### R5. Legacy common 정리와 typecheck 확장

상태: 구현 및 검증 완료

- Regional entry가 화면별 `editor_adapter.js`를 직접 사용한다.
- `easyuse_anima_prompt_studio_common.js`는 이전 import 경로를 위한 5줄짜리
  호환 re-export로 축소했다.
- `prompt_studio/**/*.js`를 `jsconfig.json`의 재귀 typecheck 범위에 포함했다.
- 재귀 import cycle, adapter unused export, `@ts-check`, 명시적 runtime 설치와
  top-level side-effect guard를 추가했다.

검증 결과:

- 공식 full validation은 Python 325개와 frontend JavaScript 65개 검사를
  통과했다.
- ComfyUI 0.27.0 Codex test instance에서 legacy canvas와 Node 2.0을 각각
  활성화해 Regional editor 연결, Vue node 구분, style 중복 부재를 확인했다.
- browser load마다 ComfyUI의 기존 `ComfyApp graph accessed before initialization`
  로그가 반복됐지만, R6의 페이지 초기 계측에서 ComfyUI 0.27.0 core
  `dialogService`의 VueUse computed가 extension 등록 전에 `rootGraph`를 읽는
  경로로 확인했다. Regional setup smoke는 setup 단계의 `app.graph` 접근이
  0회임을 별도로 검증하며 R5 adapter에는 해당 접근이 없다.

### R6. 종료 검증과 Issue 갱신

상태: 구현, 검증, PR #58 병합과 Issue #14 종료 완료

검증 결과:

- 공식 full validation에서 Python 325개와 frontend JavaScript 65개 검사를
  통과했다. TypeScript 6.0.3 기반 recursive typecheck, import-cycle,
  no-unused, semantic smoke와 `git diff --check`가 포함된다.
- ComfyUI 0.27.0 Codex test instance에서 저장된 Advanced+Regional 결합
  workflow를 legacy canvas와 Node 2.0에 각각 load했다.
- 두 모드에서 Advanced editor 3개와 Regional editor 2개를 확인했다.
  legacy canvas는 Vue node 0개, Node 2.0은 Vue node 8개로 분리 확인했다.
- 두 모드에서 workflow 저장 후 reload했으며 주요 Advanced/Regional field 값이
  유지됐다.
- 두 모드에서 queue가 서버 실행 경로까지 도달했다. 테스트 인스턴스에
  `comfyui-spectrum-ksampler`가 없어 `AnimaModGuidance` dependency 오류로
  종료됐으며 frontend 구조 변경 오류는 아니었다.
- 새 module 404, SyntaxError, ReferenceError, unhandled rejection,
  listener/observer 반복 오류는 없었다.
- 반복되는 `ComfyApp graph accessed before initialization`은 ComfyUI 0.27.0
  core 초기화 기준선으로 스택을 확인했다. EasyUseAnima 우회 코드는 추가하지
  않았다.
- 대형 후속 트랙은 #54 AiO, #55 LoRA Preset, #56 Autocomplete,
  #57 Settings로 분리했다. 이 이슈들은 Issue #14 종료를 막지 않는다.

PR #58은 #18, #46-#53과 위 검증 결과를 요약해 `dev`에 squash merge됐고,
Issue #14는 완료 상태로 닫혔다.

## Issue #14 예상 잔여 시간

남은 작업은 없다. 구현과 closure validation, PR #58 병합, 종료 코멘트와
Issue 상태 갱신이 2026-07-13에 완료됐다. #54-#57은 독립된 후속 트랙이다.

## Issue #14 이후 후속 트랙

아래 작업은 Issue #14 종료를 막지 않는다. 각각 별도 이슈와 여러 PR로 진행한다.

### F1. AiO Generator 분리 (#54)

상태: 진행 중. entry는 초기 8,879줄에서 7,676줄로 축소됐다.

병합된 경계:

- #59: profile 판정 pure-data
- #60: optional dependency와 backend capability 판정
- #61: preview state와 native-preview suppression primitive
- #63: settings schema, normalization, storage와 migration
- #65: DOM controls와 dialog primitives
- #67: Input Settings dialog lifecycle
- #68: Postprocess Settings dialog lifecycle
- #74: Preview Options dialog lifecycle

남은 주요 경계:

- profile API, CRUD와 profile settings dialog
- generator panel view/render lifecycle
- Sampler, Highres/Upscale, Detailer, Save, Advanced dialog
- native-preview store, observer와 event runtime
- queue preparation, node hooks와 extension entry
- 최종 AiO load, queue, save/reload dual-canvas matrix와 완료 ledger

관련 pure helper 2-3개 또는 하나의 lifecycle 경계를 묶는 기준으로 약 6-7개
reviewable slice를 예상한다.

### F2. LoRA Preset 분리 (#55)

상태: 진행 중. entry는 초기 2,907줄에서 2,670줄로 축소됐다.

병합된 경계:

- #69: profile data와 serialization pure rules
- #72: LoRA lookup과 FIX pending state
- #76: profile, FIX와 LoRA API client

남은 주요 경계:

- menu, search, preview, style과 observer lifecycle
- canvas drawing, hit testing, strength drag와 canvas widget class
- profile mutation, node initialize/configure/serialize runtime
- save sync, wheel listener와 extension entry
- 최종 load, edit, FIX, queue, save/reload dual-canvas matrix와 완료 ledger

약 3개 lifecycle slice를 예상한다.

### F3. Autocomplete 분리 (#56)

상태: 진행 중. entry는 초기 2,067줄에서 1,739줄로 축소됐으며 열린 세
트랙 중 종료에 가장 가깝다.

병합된 경계:

- #71: token/query parser와 insertion plan
- #75: tag/wildcard search data adapter와 cold/warm cache semantics

남은 주요 경계:

- caret geometry와 popup view
- input, keyboard와 composition controller
- external DOM input hook, listener installer와 extension entry
- 최종 입력, 선택, 닫기, save/reload dual-canvas matrix와 완료 ledger

약 2개 lifecycle slice를 예상한다.

### F4. Settings UI 분리 (#57)

상태: 완료 (2026-07-15)

- #73: setting definition data와 normalization
- #77-#80: long-text, resolution, wildcard, color editor lifecycle
- #81: persistence runtime
- #82: 52개 setting definition 조립과 color inherited-key hardening
- #83: settings smoke 공용 Fake DOM test harness 후속 정리

최종 #82 검증은 Python unittest 359개와 frontend 85개 파일을 통과했다.
legacy canvas와 Node 2.0에서 설정 중복, 일반 설정, resolution, long-text,
wildcard, color persistence/reset 및 queue success를 각각 확인했고 Issue
#57에 완료 ledger를 남겼다. #83은 production 변경이 없는 test-only 후속
조각이며 Python unittest 360개와 frontend 85개 파일을 통과했다.

## 공통 검증 기준

구현 중에는 변경 경계의 focused 검사만 실행한다. 예:

```powershell
node --check web/js/<changed-file>.js
node tests/<focused-frontend-smoke>.mjs
python -m unittest <focused test modules>
git diff --check
```

PR 최종 diff가 확정되면 저장소가 소유한 공식 full runner를 한 번 실행한다.

```powershell
powershell -ExecutionPolicy Bypass -File tools/check_project.ps1 -Profile full
```

브라우저에서 확인할 공통 항목:

반복 절차는 `docs/development/browser-smoke-matrix.md`를 따른다.

- hard refresh 후 module request 200
- console에 새 SyntaxError, ReferenceError, unhandled rejection 없음
- 기존 workflow load와 queue 성공
- save/reload와 copy/paste 후 serialized data 유지
- Node 2.0과 legacy canvas에서 DOM widget layout 확인
- textarea/input/select wheel이 canvas로 잘못 전달되지 않음
- listener, observer, animation frame 중복 설치 없음

frontend 실제 동작이 바뀐 PR은 final diff에서 legacy canvas와 Node 2.0을
각각 한 번 검증한다. Issue-close checkpoint에서도 현재 final diff의 양쪽
surface 증거를 확인한다. pure extraction과 test-only 조각은 browser smoke를
생략할 수 있으며 이유를 PR에 기록한다. 같은 final diff의 유효한 증거는
반복하지 않고, 코드 변경이나 환경 오류로 무효화된 경우에만 재실행 이유와
함께 다시 검증한다. 사용자 v0.27.0 인스턴스는 전체 maintenance goal 완료 후
한 번만 반영하고 수동 확인한다.

## Issue #14 완료 정의

다음을 모두 만족하면 Issue #14를 닫는다.

- 초기 API helper와 Main/Advanced 모듈 분리가 유지된다.
- prompt parser/renderer와 DOM overlay의 공통 소유권이 명확하다.
- Regional entry가 registration/orchestration 중심으로 축소된다.
- Regional의 schema, serialization, mask geometry, UI/runtime 경계가 분리된다.
- 새 모듈이 typecheck와 no-unused gate에 포함된다.
- import cycle과 top-level side effect guard가 통과한다.
- 기존 Advanced와 Regional workflow 호환성이 확인된다.
- Node 2.0과 legacy canvas smoke 결과가 기록된다.
- 남은 대형 파일은 별도 이슈로 전환돼 Issue #14 범위를 무한정 확장하지 않는다.

## 스냅샷 갱신 명령

```powershell
git status --short --branch
git rev-parse HEAD
git rev-parse origin/dev
Get-ChildItem -Recurse -File web\js -Filter *.js |
  ForEach-Object {
    [pscustomobject]@{
      Lines = (Get-Content -LiteralPath $_.FullName).Count
      File = $_.FullName
    }
  } |
  Sort-Object Lines -Descending
```

수치나 완료 상태가 달라지면 이 문서의 점검일과 근거 커밋을 같이 갱신한다.
