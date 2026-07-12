# Frontend Maintenance Roadmap

## 목적

이 문서는 Issue #14의 초기 모듈 분리 작업 이후 남은 프론트엔드 유지보수
범위를 현재 `dev` 기준으로 다시 정리한다. 과거 실행 계획과 현재 상태를
분리하고, 한 이슈가 끝없이 커지지 않도록 Issue #14 종료 범위와 후속 작업을
명시하는 것이 목적이다.

- 현재 로드맵: 이 문서
- 초기 실행 계획과 체크리스트:
  `docs/development/issue-14-frontend-js-maintenance.md`
- 대상 이슈: `https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/14`

이 문서의 수치는 영구 기준이 아니라 점검 스냅샷이다. 구현을 시작할 때마다
`dev`, 원격 브랜치, 파일 크기, 테스트 수를 다시 확인한다.

## 점검 기준

점검일: 2026-07-13

기준 브랜치와 커밋:

```text
branch: dev
HEAD: c7897a824b3bf28b41f826f557bb0330918e40a1
origin/dev: c7897a824b3bf28b41f826f557bb0330918e40a1
working tree: clean
```

Issue #14는 열려 있다. 다음 변경은 `dev`에 병합됐다.

| PR | 병합 커밋 | 완료 범위 |
| --- | --- | --- |
| #18 | `4eb7992` | 공통 API helper, Prompt Studio 모듈 분리, no-build JS typecheck, Vite 보류 결정 |
| #46 | `e75eb96` | 미사용 코드 검사, 통합 frontend 검사 스크립트 |
| #47 | `2c818b6` | Main/Advanced와 Regional의 prompt highlight parser/renderer core 공통화 |
| #48 | `781b4c4` | Issue #14 현재 로드맵과 종료 범위 정리 |
| #49 | `c7897a8` | 저장소 소유 project/frontend/unittest 검증 명령 계약 통합 |

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
- `tools/check_frontend.ps1`은 전체 frontend JS 문법 검사, parser/renderer와
  overlay semantic smoke, 고정 버전 TypeScript 검사를 한 번에 실행한다.
- `noUnusedLocals`와 `noUnusedParameters`가 현재 typecheck 범위에 적용된다.
- Vite/TypeScript build chain을 당장 도입하지 않고 raw ES module과 no-build
  typecheck를 유지하기로 결정했다.

### 정량 스냅샷

`web/js`에는 JavaScript 53개, 총 28,782줄이 있다. `jsconfig.json`에 명시된
include 대상은 Prompt Studio entry와 `prompt_studio/*.js` 41개, 8,485줄로
전체 라인의 29.5%다. import를 따라 추가로 검사되는 dependency는 이 수치에
포함하지 않았다.

| 파일 | 줄 수 | 전체 비율 | 현재 판단 |
| --- | ---: | ---: | --- |
| `easyuse_anima_aio.js` | 8,879 | 30.8% | 가장 큰 후속 hotspot |
| `easyuse_anima_lora_preset.js` | 2,907 | 10.1% | canvas/UI/API/state가 한 파일에 결합 |
| `easyuse_anima_prompt_studio_regional.js` | 2,284 | 7.9% | Issue #14 종료 전에 분리할 대상 |
| `easyuse_anima_autocomplete.js` | 2,067 | 7.2% | parser, popup, input runtime이 결합 |
| `easyuse_anima_settings.js` | 1,935 | 6.7% | 설정 정의와 여러 editor 구현이 결합 |
| `easyuse_anima_prompt_studio_common.js` | 1,419 | 4.9% | 현재 Regional만 import하는 legacy common layer |

상위 6개 파일이 전체 frontend JS의 약 67.7%를 차지한다. 줄 수 자체를 목표로
삼지는 않지만, 책임 경계와 검증 비용이 이 파일들에 집중돼 있다는 신호로
사용한다.

### 남은 Prompt Studio 중복과 경계 문제

- `easyuse_anima_prompt_studio_common.js`와
  `prompt_studio/highlight.js`에 남은 동일 이름 함수는 9개다.
- pixel 변환, scrollbar padding, overlay bounds, text metric 복사,
  preview HTML, overlay 위치 동기화는 DOM overlay core로 공통화됐다.
- 색상 설정, tooltip 문구, 설정 저장소, node별 highlight state와 listener
  lifecycle은 화면별 adapter에 남기는 편이 안전하다.
- Regional entry는 constants, schema, serialization, mask geometry/editor,
  DOM 생성, layout, hook 설치, extension 등록을 한 파일에서 담당한다.
- `easyuse_anima_prompt_studio_common.js`는 Regional만 사용하므로 이름과 역할이
  현재 구조를 설명하지 못한다. Regional 분리 후 제거하거나 얇은 호환 adapter로
  축소해야 한다.

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

- PR 하나에는 한 종류의 위험만 넣는다.
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
  runtime.js
  extension.js
```

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

예상: 0.5-1일

- Regional이 새 모듈을 직접 사용하도록 import를 정리한다.
- `easyuse_anima_prompt_studio_common.js`를 제거하거나 얇은 호환 adapter로
  축소한다.
- 새 Regional 모듈을 `jsconfig.json`에 포함한다.
- import cycle, unused export, top-level side effect guard를 확장한다.

완료 기준:

- Prompt Studio의 Main/Advanced와 Regional 책임 경계가 파일 이름에 드러난다.
- 새 모듈에 typecheck warning과 unused code가 없다.
- common layer가 화면별 settings, tooltip, layout lifecycle을 다시 소유하지
  않는다.

### R6. 종료 검증과 Issue 갱신

예상: 0.5-1일

- frontend 통합 검사와 focused/full Python suite를 실행한다.
- 기존 Advanced와 Regional workflow를 load, queue, save/reload한다.
- Node 2.0과 legacy canvas에서 hard refresh 후 module 404, SyntaxError,
  ReferenceError, 반복 listener/observer 오류가 없는지 확인한다.
- Issue #14에 #18, #46, #47과 후속 PR 결과를 요약한다.
- AiO, LoRA Preset, Autocomplete, Settings는 별도 이슈로 연결하고 Issue #14를
  닫는다.

## Issue #14 예상 잔여 시간

R1-R6은 약 4-7 작업일로 본다. 가장 큰 변수는 Regional mask/editor의 browser
smoke와 workflow compatibility 확인이다. 한 PR로 묶지 않고 다음 정도로
나누는 것이 적절하다.

1. validation contract
2. overlay core
3. Regional pure data
4. Regional UI/runtime
5. common retirement와 typecheck
6. closure validation과 Issue update

## Issue #14 이후 후속 트랙

아래 작업은 Issue #14 종료를 막지 않는다. 각각 별도 이슈와 여러 PR로 진행한다.

### F1. AiO Generator 분리

현재 8,879줄이며 frontend 전체의 30.8%다. 가장 큰 장기 위험이다.

분리 순서:

1. settings schema, normalization, preset/profile data
2. optional dependency와 backend capability 조회
3. preview state와 native preview suppression
4. DOM control builders와 settings dialogs
5. queue/runtime hooks와 extension entry
6. typecheck와 browser regression matrix

예상: 4-6개 PR, 5-8 작업일

### F2. LoRA Preset 분리

분리 순서:

1. profile API와 serialization
2. LoRA lookup/fix state
3. menu/search/preview lifecycle
4. canvas rendering과 hit testing
5. extension hooks와 typecheck

예상: 2-3개 PR, 2-3 작업일

### F3. Autocomplete 분리

분리 순서:

1. token/query parser와 insertion plan
2. search/data adapter
3. caret geometry와 popup view
4. input controller와 extension hooks

예상: 2개 PR, 1.5-2.5 작업일

### F4. Settings UI 분리

분리 순서:

1. setting definitions와 normalization
2. long-text, color, path, resolution editor
3. persistence adapter와 extension registration

예상: 2개 PR, 1.5-2.5 작업일

## 공통 검증 기준

모든 frontend refactor PR:

```powershell
powershell -ExecutionPolicy Bypass -File tools/check_frontend.ps1
python -m unittest <focused test modules>
git diff --check
```

주요 checkpoint와 PR 준비:

```powershell
python -m unittest discover -s tests
python -m compileall -q .
```

브라우저에서 확인할 공통 항목:

- hard refresh 후 module request 200
- console에 새 SyntaxError, ReferenceError, unhandled rejection 없음
- 기존 workflow load와 queue 성공
- save/reload와 copy/paste 후 serialized data 유지
- Node 2.0과 legacy canvas에서 DOM widget layout 확인
- textarea/input/select wheel이 canvas로 잘못 전달되지 않음
- listener, observer, animation frame 중복 설치 없음

Python, API, workflow schema를 건드리지 않은 작은 pure-helper PR에서는 focused
검사를 먼저 실행하고, full suite와 browser smoke는 주요 checkpoint에서
실행한다. 생략한 검증은 PR에 명시한다.

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
