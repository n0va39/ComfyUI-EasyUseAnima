# AIO-SAGE-04 Risk-based Live Matrix

## 결론

- production 기준: `dev@116629a45739ccbdc22b5cb6c550349dab011000`
- 범위: Issue #441의 SageAttention `first_pass/highres/detailer/upscale`
  stage-scope, v3 -> v4 migration, Legacy Canvas / Node 2.0 저장·재로드·queue
  parity
- 결과: **PASS**
- production JavaScript/Python, public node socket, workflow schema와 외부
  custom-node는 변경하지 않았다. 전체 optional-integration Cartesian matrix도
  실행하지 않았다.

## 고정한 live 경계

- KJNodes `PathchSageAttentionKJ` object-info는 `model`,
  `sage_attention`, optional `allow_compile` 계약을 제공했다.
- Sage mode는 `auto`를 사용했고 shared/eager compile owner는 추가하지 않았다.
- DAVE, Safe PAG와 Torch Compile은 representative pairwise 조합만 실행했다.
- source, Codex test instance 설치본과 HTTP served frontend module의 SHA-256이
  일치했다.

## 선택 live matrix

| Surface / risk | 설정과 저장·재로드 관측 | Terminal / output |
| --- | --- | --- |
| Legacy Canvas first-pass-only | Modern Node Design off. Sage `auto`, `first_pass_only`, `allow_compile=false`; DAVE on, Safe PAG off, Torch Compile off. 저장과 hard reload 뒤 preset과 네 stage boolean이 동일했다. | success/completed, 512x512 image 1개, running 0, pending 0 |
| Node 2.0 v3 missing-scope migration | Modern Node Design on. 기존 v3의 missing `sage_stage_scope`가 실제 Advanced UI에서 `all_sampling_stages`로 열렸다. 이후 Sage `auto`, all-stage, `allow_compile=false`; Safe PAG on, DAVE와 Torch Compile off로 저장·재로드했다. | success/completed, 512x512 image 1개, running 0, pending 0 |
| Node 2.0 custom Highres-only | Sage `auto`, `custom`에서 Highres만 true; first pass, Detailer, Upscale false. `allow_compile=true`, Torch Compile on, DAVE와 Safe PAG off. Highres 1.25x, 1 step. 저장·재로드 뒤 scope와 Highres 설정이 동일했다. | success/completed, 640x640 image 1개, running 0, pending 0 |

첫 Node 2.0 case는 migration UI가 legacy all-stage 결과를 보존한 뒤 v4로
저장되는 경계를 검증했다. custom case는 512x512 first pass 뒤 640x640 output이
생성되어 Highres sampling이 실제로 실행됐고, Sage scope가 Highres에만 선택된
상태에서 Torch Compile과 함께 완료됨을 확인했다. Detailer와 USDU의
deterministic selected/unselected lineage는 repository fixture가 소유하므로 live
matrix에서 중복 조합을 추가하지 않았다.

## Serialization, error, cleanup

- 두 disposable workflow의 AiO settings는
  `easyuse_anima_aio_generation_settings` version 4로 저장됐다.
- Legacy serialization은 Sage scope
  `{first_pass: true, highres: false, detailer: false, upscale: false}`와
  `allow_compile=false`를 보존했다.
- 최종 Node 2.0 serialization은 Sage scope
  `{first_pass: false, highres: true, detailer: false, upscale: false}`와
  `allow_compile=true`, Torch Compile enabled를 보존했다.
- 세 queue의 history는 모두 success/completed였고 failed history, pending queue와
  남은 running item이 없었다.
- 시작 canvas mode인 Legacy를 복구했다. disposable workflow 두 개와 browser
  session을 제거하고 격리 server process tree를 종료했다. 종료 후 8194/8195
  listener와 관련 server process는 0이었다.

## Fallback

SageAttention은 mode를 `disabled`로 바꿔 전체 비활성화할 수 있고, 각 stage는
feature-owned `sage_stage_scope` boolean으로 독립적으로 제외할 수 있다. v3에
scope가 없으면 기존 all-stage 결과를 보존해 v4로 migration하며, malformed
explicit scope와 알 수 없는 stage는 repository Contract대로 fail-closed한다.
