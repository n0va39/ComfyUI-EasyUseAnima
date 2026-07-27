# AIO-SAFEPAG-04 Risk-based Live Matrix

## 결론

- production 기준: `dev@fa016174f81a68ee551b08dd30ddb672697f91e8`
- 범위: Issue #440의 Safe PAG `first_pass/highres/detailer/upscale`
  stage-scope와 Legacy Canvas / Node 2.0 저장·재로드·queue parity
- 결과: **PASS**
- production, public node socket, workflow schema와 외부 custom-node는 변경하지
  않았다. 전체 optional-integration Cartesian matrix도 실행하지 않았다.

## 고정한 live 경계

- `AnimaSafePAG` object-info는 현재 production adapter가 요구하는 MODEL과 8개
  Safe PAG parameter를 그대로 제공했다.
- source와 Codex test instance 설치본의 Safe PAG schema, migration,
  normalization, model-preparation, Advanced UI owner hash가 일치했다.
- 다음 frontend module은 source, installed, HTTP served SHA-256이 각각
  일치했고 served response는 모두 HTTP 200이었다.

| Module | SHA-256 |
| --- | --- |
| `web/js/aio/settings.js` | `CCD288D2814DD499405D16F8477331267DF7EFCFAE75438CD8EAB7DB9AA7FFBC` |
| `web/js/aio/advanced_settings_dialog.js` | `3D7F76A2E0ACA994432DA0EFC2FC2F6E0B3047549EBD37339F76098485E908E2` |
| `web/js/easyuse_anima_aio.js` | `C1DCA1104DBECFFCE9F175C0424D09DD2CF54CB05B756CE59796D1C6DCD125A0` |

## 선택 live matrix

| Surface / risk | 설정과 저장·재로드 관측 | Terminal / output |
| --- | --- | --- |
| Legacy Canvas fresh scope | Modern Node Design off. 기존 v1 workflow를 실제 Advanced UI에서 v3로 적용했다. Safe PAG on, `first_pass_only`; Highres, Detailer, Upscale off. 저장 후 hard reload와 재로드에서 preset과 네 stage boolean이 동일했다. | success/completed, 약 13.43 s, 512×512 image 1개, running 0, pending 0 |
| Node 2.0 custom scope | Modern Node Design on, Vue node signal 8. Safe PAG `custom`에서 Highres만 true; first pass, Detailer, Upscale false. Highres 1.25×, 1 step. 저장 후 hard reload와 재로드에서 custom checkbox와 hidden v3 settings가 동일했다. | success/completed, 약 11.86 s, Highres 결과 640×640 image 1개, running 0, pending 0 |

Legacy case는 선택되지 않은 후속 sampling stage를 비활성화해 first-pass lineage만
실행했다. Node 2.0 case는 first pass를 Safe PAG scope에서 제외하고 Highres만
선택했으며, 512×512 first pass 뒤 640×640 output이 생성되어 Highres stage가
실제로 실행됐음을 확인했다. Detailer와 USDU의 deterministic selected/unselected
lineage는 repository fixture가 소유하고 live matrix에서는 중복 조합을 추가하지
않았다.

## UI, error, cleanup

- 두 표면 모두 실제 Safe PAG-owned preset/custom controls를 사용했다.
- Apply 뒤 hidden settings는 `version: 3`과 exact stage booleans를 보존했다.
- reload 뒤 Advanced UI의 preset/custom 표시와 serialized settings가 일치했다.
- 두 queue의 EasyUse Anima page error와 Safe PAG 관련 browser error는 0건이었다.
- user CSS, autocomplete와 subgraph endpoint 404, 타 custom-node의 optional Python
  dependency 누락, frontend deprecation warning은 startup baseline으로 분리했다.
- 시작 canvas mode인 Legacy를 복구했다. disposable workflow와 output, headless
  browser profile을 제거하고 browser/server process tree를 종료했다. 종료 후 test
  ports에 listener가 남지 않았다.

## Fallback

Safe PAG는 기존 `enabled` switch로 전체 비활성화할 수 있고, 각 stage는 feature-owned
scope boolean으로 독립적으로 제외할 수 있다. Legacy settings에 scope가 없으면 기존
all-stage 결과를 보존하며, malformed explicit scope는 all-disabled로 fail-closed한다.
