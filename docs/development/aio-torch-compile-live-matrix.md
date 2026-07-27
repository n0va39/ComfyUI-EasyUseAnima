# AIO-COMPILE-04 Risk-based Live Matrix

## 결론

- 기준: `dev@3cd9edc3048b4a98d7186288319311f4e703eea8`
- 범위: `#410`의 fixed, Highres, Detailer/USDU, LoRA, DAVE,
  SageAttention, Legacy Canvas, Node 2.0, KJ input/signature drift
- 결과: **PASS with bounded Detailer detector limitation**
- production, workflow/public socket, 외부 custom-node 버전과 model asset은
  변경하지 않았다. Cartesian product도 실행하지 않았다.

격리 환경은 Python 3.12.13, PyTorch 2.12.1 + CUDA 13.0, compute capability
12.0, 약 16 GiB VRAM과 현재 설치된 KJNodes/DAVE/Impact Pack/USDU를 사용했다.
공통 workflow에는 7개 LoRA가 활성화되어 있었다.

## Source / installed / served closure

격리 queue 전에 동기화한 다음 frontend 파일은 source, installed, HTTP served
SHA-256이 각각 일치했다.

| 파일 | SHA-256 | 결과 |
| --- | --- | --- |
| `web/js/aio/torch_compile_recommendation.js` | `C9DC87C5D18D3DA09BC9A8BDDBAF3BD4C76BBEDEEAAB911A966D8C7A0751D652` | equal |
| `web/js/aio/advanced_settings_dialog.js` | `D1D5D7F86640214FF987F3151013528C3B545FF59F243DEC6E11B71C03862920` | equal |
| `web/js/easyuse_anima_aio.js` | `EF1067BDF527CC5E42063E4333D0CC18C35EC6868D10FBF51333E28C1309A2C8` | equal |

## Bounded live matrix

| Surface / risk | 설정과 관측 | Terminal / output |
| --- | --- | --- |
| Legacy fixed shape | 512x512, 1 step, Compile on, manual `dynamic=false`, DAVE off, LoRA stack active | success; total 31.55 s, compile/forward 15.03 s; 512x512 output. 1-step 특성의 noisy image였고 black frame, NaN 또는 기하학적 손상은 없었다. |
| Node 2.0 Highres variable shape | Highres on, Highres 1 step, Compile on, `dynamic=auto`, DAVE `first_pass`; recommendation은 `stable_variable_shapes`와 `highres_changes_shape`를 반환 | success; total 24.04 s, first pass 약 2.00 s, Highres variant 약 9.40 s; invalid frame 없음 |
| Node 2.0 Detailer + USDU | face Detailer on, Detailer 1 step, USDU 1.25x/1 step/auto tile, Compile on, `dynamic=auto`; recommendation reasons는 `detailer_uses_variable_crops`, `usdu_uses_tiles` | success; total 17.48 s. USDU가 640x640 auto tile을 1x1 tile로 실행해 640x640 output을 생성했다. SAM3는 threshold .52에서 SEGS를 만들지 않아 Detailer는 fail-safe no-op이었다. |
| Highest-risk approved patch chain | LoRA + Compile + DAVE `first_pass` + Sage `auto`, `allow_compile=true`; 기존 stage plan은 `Compile -> DAVE -> Sage`를 소유 | success; total 11.22 s. 로그에서 DAVE armed와 Sage auto 적용 후 model completion을 확인했다. |

Legacy fixed case와 Node 2.0 variable cases 모두 실제 queue를 사용했다. 자동 추천
버튼 자체는 compile이나 queue를 시작하지 않았고, 사용자가 적용한 draft 설정만 기존
queue 경로가 소비했다.

## Detailer detector limitation

실제 crop sampling을 확인하기 위해 4-step 얼굴 output으로 face Detailer를 다시
실행했고 detector threshold를 .52에서 .20으로 한 번 낮췄다. 두 경우 모두 SAM3가
SEGS를 반환하지 않아 crop sampler는 live에서 실행되지 않았다. queue terminal,
Compile, base sampling과 cleanup은 정상이며 실패 계층은 detector input/result에
국소화됐다.

이 단계는 detector tuning이나 asset 변경을 허용하지 않으므로 추가 threshold 탐색을
중단했다. deterministic Detailer crop/stage fixture는 계속 통과하며, 이 matrix는
실행되지 않은 crop 조합을 안전하다고 주장하지 않는다. detector별 실제 crop 품질
검증이 필요하면 별도 bounded follow-up으로 다룬다.

## KJ current / old-new drift

현재 설치된 `TorchCompileModelAdvanced` object-info는 production positional adapter와
일치했다. required input은 `model`, `backend`, `fullgraph`, `mode`, `dynamic`,
`compile_transformer_blocks_only`, `dynamo_cache_size_limit`, `debug_compile_keys`이고,
`disable_dynamic_vram`은 optional이다.

외부 KJNodes를 downgrade/upgrade하지 않고 다음 기존 fake contract fixture로 drift를
검증했다.

- required input 추가/삭제: `kj_input_contract_drift`로 fail-closed
- matching schema에서 patch signature 변경: `kj_patch_signature_drift`로 fail-closed
- stage order: Compile만 DAVE 앞으로 이동하고 Sage/FP16은 검증된 후속 순서를 유지
- 실제 KJ adapter: FP16/Sage/Compile argument와 return chain을 보존

네 focused unittest는 모두 PASS했다.

## Errors, cleanup, fallback

- EasyUse Anima extension 범위의 browser error는 0건이었다.
- host/core startup에서 graph early access와 Vite preload error가 각 1건 있었지만,
  모든 live queue와 extension UI가 정상 동작했고 feature failure와 상관되지 않았다.
- 종료 전 queue running/pending은 0이었고 Node 2.0 setting을 원래 값으로 복구했다.
  browser tab을 닫고 격리 서버와 wrapper를 종료했으며 port 8194 listener가 남지
  않았음을 확인했다.
- fixed shape는 수동 `dynamic=false`, variable shape는 `dynamic=auto`가 보수적
  fallback이다. 문제 발생 시 Compile, DAVE, Sage, Detailer, USDU를 기존 setting으로
  각각 독립적으로 비활성화할 수 있다.
- production/package tree가 바뀌지 않았으므로 AIO-COMPILE-03의 validate/pack
  증거를 재사용한다.
