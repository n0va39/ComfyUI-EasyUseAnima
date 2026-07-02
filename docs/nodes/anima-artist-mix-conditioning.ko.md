# Anima Artist Mix Conditioning

카테고리: `EasyUse Anima/Prompt`

입력:

- `clip`
- `prompt`
- `artist_tags`
- `artist_position`
- `artist_mix_mode`
- artist mix tuning inputs

출력:

- `positive`

일반 positive prompt와 별도 작가 태그 입력을 받아 positive `CONDITIONING`을
출력하는 단독 artist mix 노드입니다. Prompt Studio Advanced v2를 쓰지 않는
workflow에서도 같은 artist mix 기법을 사용할 수 있습니다.

여기서 작가 태그는 `@`가 붙은 토큰이 아니라 `artist_tags` 입력칸에 넣은
작가 태그 문자열을 의미합니다.

## 위치 처리

`artist_position`은 작가 태그를 prompt에 배치하는 방식을 정합니다.

| 값 | 동작 |
| --- | --- |
| `correct` | 기본값입니다. `prompt`와 `artist_tags`를 합친 뒤 ANIMA prompt ordering으로 교정합니다. |
| `front` | 작가 태그를 prompt 앞에 고정합니다. |
| `back` | 작가 태그를 prompt 뒤에 고정합니다. |

`correct`는 ANIMA 문법에 맞는 순서를 우선합니다. 특정 외부 conditioning 노드나
실험용 workflow에서 작가 태그 위치를 강제로 고정해야 할 때만 `front` 또는
`back`을 사용합니다.

## Artist Mix Mode

| 값 | 비용 기준 | 설명 |
| --- | --- | --- |
| `prompt` | positive 1 branch | 작가 태그를 prompt에 넣고 한 번만 인코딩합니다. 가장 단순합니다. |
| `average` | positive 1 branch | 작가별 conditioning을 평균으로 섞습니다. 빠르고 안정적입니다. |
| `delta_rms` | positive 1 branch | base prompt 대비 artist delta를 섞고 RMS 스타일 에너지를 복원합니다. |
| `hybrid` | top K + 1 branch | 강한 작가 몇 개는 exact branch로 유지하고 나머지는 압축합니다. |
| `clustered` | cluster_count 중심 branch | 유사한 artist delta를 묶어 여러 압축 branch로 만듭니다. |
| `exact` | 작가 수 N branch | 작가마다 별도 conditioning branch를 만듭니다. 가장 정확하지만 가장 비쌉니다. |

`composite_exact`, `late_exact`, `average_late_exact`, `scheduled_average`는
기존 Prompt Data Conditioning artist mix 경로와 같은 호환 모드입니다.

## 튜닝 입력

- `artist_mix_start_percent`: late/scheduled 계열 모드가 시작되는 sampling 비율입니다.
- `artist_mix_strength_scale`: exact 계열 branch 강도 배율입니다.
- `artist_mix_style_gain`: `delta_rms`, `hybrid`, `clustered` 압축 branch의 스타일 반영 강도입니다.
- `artist_mix_rms_scale_cap`: RMS 스타일 에너지 복원 최대 배율입니다.
- `artist_mix_exact_top_k`: `hybrid`에서 exact로 유지할 상위 작가 수입니다.
- `artist_mix_cluster_count`: `clustered`에서 사용할 압축 branch 수입니다.
- `artist_mix_dominant_isolation`: dominant 작가를 cluster에 넣지 않고 exact branch로 유지합니다.
- `artist_mix_dominant_threshold`: dominant 판정 기준입니다.

## Advanced v2와의 차이

`Anima Prompt Data Conditioning`은 `EASYUSE_ANIMA_PROMPT_DATA` 안의 artist field와
artist mix 설정을 읽습니다. `Anima Artist Mix Conditioning`은 Prompt Data 없이
`prompt`와 `artist_tags` 입력만으로 같은 conditioning 출력을 만드는 단독 노드입니다.
