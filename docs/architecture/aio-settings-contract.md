# AiO generation settings v1 계약

이 문서는 `easyuse_anima_aio_generation_settings` v1의 정적 계약과 소유 경계를 설명한다. 기준 manifest는
`easyuse_anima/aio/schemas/generation_settings.v1.json`이다.

기준 manifest는 [#168](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/168)의 C168-01 Contract PR에서
도입했다. C168-02는 v0.5.2 release workflow에 저장된 AiO generation settings 입력과 normalized
결과를 현재 runtime에 다시 적용해 deep equality로 고정한다. Python/JavaScript runtime은 여전히 manifest를
import하지 않으며 generator, codegen, typed model, version migration, normalizer 교체는 이 단계에 포함하지 않는다.

## 소유권

| 계약 | owner | 비고 |
| --- | --- | --- |
| v1 정적 field shape와 default | `easyuse_anima.aio.generation_settings` manifest | Python/JavaScript default와 golden equality |
| 정적 enum, min/max, coercion 분류 | manifest | 현재 backend normalizer 동작으로 검증 |
| legacy alias와 unknown-field 정책 | manifest | surface별 현재 차이도 명시 |
| Python 실행 시 정규화 | 현재 `nodes.py` | 이번 PR에서 이동하거나 변경하지 않음 |
| frontend default merge/visible merge | 현재 `web/js/aio/settings.js`, `web/js/easyuse_anima_aio.js` | 이번 PR에서 변경하지 않음 |
| Comfy/Impact sampler, scheduler, max resolution 목록 | Comfy capability adapter/runtime | manifest가 값 목록을 소유하지 않음 |
| profile envelope, ID, revision, CAS | [#163](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/163) | nested `settings` payload 내부만 #168 소유 |

manifest의 `default`는 완전한 normalized v1 기본 object다. `shape`는 field type, coercion, static enum 및
bound를 제공하고 반복되는 Spectrum/DiT correction/Detailer target은 `definitions`와 `$ref`로 표현한다.
모든 coercion 참조, array item, open JSON object value, `custom_<n>` pattern field가 manifest 내부 정의로
해결되므로 후속 consumer가 별도의 암묵 token 표 없이 계약을 해석할 수 있다. 다만 이번 PR은 실제
generator/codegen/typed model을 추가하거나 특정 generator와의 호환성을 주장하지 않는다. 현재 runtime source of
execution은 기존 코드다.

## 정적 field 정책

정규화 이후의 root는 object이며 다음 section을 갖는다.

| section | 핵심 정적 계약 |
| --- | --- |
| `schema`, `version`, `mode` | schema name 고정, current version 1, mode enum |
| `sampler` | backend/seed control enum, steps/cfg/denoise bound, Spectrum/SPD/DiT correction |
| `model_patches` | AuraFlow, DAVE, Safe PAG, KJ/torch compile |
| `mod_guidance`, `artist_mix` | mode/profile enum과 weight/layer/count bound |
| `highres`, `upscale`, `postprocess` | stage switch, method/backend enum, size/sampling bound |
| `detailer` | ordered `face`/`eye`와 `custom_<n>` target contract |
| `save`, `preview` | save backend/format/metadata와 preview feed contract |

각 normalized object는 known field를 채우면서 unknown field를 기본적으로 보존한다. 빈 extension object인
`sampler.spectrum_extra`와 `sampler.spd_extra`도 v1의 공개 확장 지점으로 유지한다.

빈 default container도 shape가 비어 있다는 뜻이 아니다. `save.image_saver.additional_hash_bundles`는 정규화된
문자열 item, `civitai_hash_fetchers`는 `enabled`, `username`, `model_name`, `version`을 갖는 item object를 소유한다.
후자는 non-object row와 identity 문자열 세 개가 모두 빈 row를 버리고 unknown item field를 보존하지 않는다.
`detailer.order` item은 `face`, `eye`, `custom_<n>`만 허용하며 중복을 제거하고 현재 backend가 `face`, `eye`를
항상 보장한다. `sampler.spectrum_extra`와 `sampler.spd_extra`의 추가 값은 JSON value contract를 따른다.

### Coercion

- Backend boolean은 첫 list/tuple 값을 사용하고 빈 list/tuple은 field default를 쓴다. `true`, `1`, `yes`,
  `on`, `enable`, `enabled` 문자열은 true이며 다른 문자열은 false다.
- Backend integer/number는 각각 Python `int()`/`float()` 변환을 사용하고 실패하면 해당 default를 쓴다.
- Generic `choice`는 첫 list/tuple 값을 trimmed string으로 만든 뒤 exact membership을 확인하고 실패하면 default를
  쓴다. 다음 field는 generic pipeline을 사용하지 않으므로 전용 coercion을 갖는다.
  - `mod_guidance.profile`: whole value를 `str(value or default)`로 바꾼 뒤 trim/case 변환 없이 exact membership을
    확인한다. list/tuple은 첫 요소가 아니라 container 전체 문자열이 되어 invalid fallback한다.
  - `upscale.usdu.prompt_mode`, Detailer target `alignment`: whole value를 먼저 `str(value or default)`로 바꾸고
    그 scalar string을 generic choice에 전달한다. 따라서 whitespace는 trim되지만 list/tuple은 첫 요소로
    취급되지 않는다. `prompt_mode`의 `quality_tags_only` alias는 string 변환 후 choice 전에만 적용한다.
- 단, runtime capability를 쓰는 dynamic choice는 preferred default가 현재 capability 목록에 있을 때만 default를
  쓴다. 없으면 첫 capability, capability가 비었으면 preferred default를 쓴다. 이는 static enum의 invalid 정책과
  다른 `default-if-present-else-first` 정책이다.
- `string-or-default`, empty-string string, trimmed string, hash bundle string/list, Civitai fetcher list,
  Detailer order, open JSON object, seed, constant token은 모두 manifest `coercions`에 정의한다. container item의
  별도 coercion 참조도 같은 registry에서 해결한다.
- Frontend boolean과 number coercion은 JavaScript 규칙을 사용한다. backend와 동일하다고 가정하지 않으며
  정확한 token/operation은 manifest의 `coercions`에 surface별로 기록한다.
- Frontend default merge는 일반 field coercion이나 schema constant 강제를 수행하지 않고 incoming value를
  보존한다. backend normalizer가 schema constant를 canonical 값으로 강제하는 동작과 혼동하지 않는다.
- Static enum과 bound는 manifest가 소유한다. sampler/scheduler 목록과 Comfy max resolution처럼 실행 환경에
  따라 달라지는 값은 `dynamic_enum`/`maximum_source`로만 참조한다.
- Static enum golden gate는 manifest의 각 member가 해당 backend field에서 round-trip되는지 확인한다. 또한 모든
  field에 sentinel을 주입해 실제 `_choice` accepted set을 캡처하고, `_choice`를 거치지 않는 profile은 runtime
  constant를 직접 사용해 manifest/명시 fixture/runtime source의 3자 equality를 검증한다. 따라서 manifest extra
  member와 runtime accepted member 누락을 모두 차단한다.

## Dynamic Comfy capability 비소유

다음 값은 설치된 ComfyUI 및 custom node capability에 따라 달라지므로 manifest가 snapshot하지 않는다.

- `comfy.samplers`: sampler name
- `comfy.schedulers`: Comfy scheduler name
- `impact.schedulers`: Detailer scheduler name
- `comfy.max_resolution`: USDU tile 및 postprocess size 상한

manifest는 이 값들의 type, capability source, invalid fallback 구조만 지정한다. 현재 목록을 static enum으로
복사하거나 default를 환경 탐색 결과로 다시 쓰지 않는다. golden test는 preferred default가 deterministic
capability에 존재하는 경우와 존재하지 않아 첫 capability로 fallback하는 경우를 분리해 검증한다.

## Legacy alias와 migration

| legacy | 현재 in-memory 처리 | canonical |
| --- | --- | --- |
| `upscale.fit` | 명시적 non-default `postprocess.fit` 값을 우선하고 나머지를 복사한 뒤 제거 | `postprocess.fit` |
| `upscale.fit.enabled` | true면 postprocess를 활성화 | `postprocess.enabled` |
| `upscale.usdu.prompt_mode = quality_tags_only` | value alias 변환 | `no_general` |
| `sampler.dave` | 제거 | `model_patches.dave` |
| `model_patches.aura_flow.enabled` | 제거 | 없음 |
| `save.filename_prefix` | 제거 | `save.image_saver.path` + `filename` |
| `save.image_saver.show_preview` | 제거 | `preview` section |

v1에는 version migration이 없다. 위 처리는 기존 legacy alias 정규화이며 저장 파일을 자동으로 다시 쓰는
migration이 아니다. Read/list/load는 원본 profile/workflow bytes, mtime, revision을 바꾸지 않아야 한다.
write-on-read는 금지한다. 후속 version migration은 명시적인 순수 함수로 추가하고, 실제 persist는 사용자가
요청한 save/update 같은 mutation에서만 수행한다.

## Unknown-field 정책과 현재 drift

확인된 현재 동작은 다음과 같다.

- Python `_merge_versioned_settings()`와 backend normalizer는 nested unknown key를 재귀적으로 보존한다. 위 표의
  known legacy path만 명시적으로 제거한다.
- Frontend `aioMergeDefaults()`도 unknown key를 보존한다.
- Frontend visible merge와 optional-dependency sanitize는 `highres.backend`를 제거한다. Python은 이 key를
  unknown field로 보존한다. 이 차이는 현재 drift이며 이번 Contract PR에서 동작을 맞추지 않는다.
- Seed 최소값은 양쪽 모두 `-3`이지만 backend 상한은 uint64
  `18446744073709551615`, frontend 상한은 현재 `1125899906842624`다.
- Backend와 frontend의 boolean/integer coercion token 및 변환 규칙도 완전히 같지 않다.

이 drift는 manifest의 `policies.known_surface_drift`와 surface-specific coercion/bound에 기록한다. 후속 동작
변경은 별도 Behavior/Migration PR에서 호환성 판단과 fixture를 갖춘 뒤 수행한다.

## 관련 이슈 경계

- [#163](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/163): profile envelope, stable identity,
  revision/CAS, AtomicJsonStore를 소유한다. profile 내부 nested generation settings shape는 이 계약이 소유한다.
- [#184](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/184): `nodes.py`의 동작 보존형 package/module 이동과
  Comfy adapter 추출을 소유한다. 이 PR은 파일 이동이나 root alias 변경을 하지 않는다.
- [#169](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/169): `GenerationRequest`/stage pipeline,
  cleanup, byte-budgeted cache 같은 실행 동작을 소유한다. 이 PR은 queue, stage, cache, result를 변경하지 않는다.
- [#168](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/168)의 후속 단계가 typed config, generator/codegen,
  pure version migration 및 normalizer facade 축소를 소유한다.

## Golden gate

`tests/test_aio_schema_contract.py`는 manifest default와 현재 Python default의 deep equality, 전체 default leaf와
field contract coverage, coercion 참조 완결성, empty container item 및 pattern/ref coverage, static enum 양방향
accepted-set/member round-trip과 min/max,
legacy/unknown 정책, dynamic capability 비소유와 fallback 양쪽 분기를 검증한다.
또한 `tests/fixtures/aio_generation_settings_0_5_2.json`에 v0.5.2 release workflow의 node 86 payload,
provenance, deterministic capability 목록과 expected normalized settings를 고정한다. 현재 normalizer를 재실행해
deep equality와 입력 비변경을 함께 검증하므로, 저장된 0.5.2 계약의 변화를 회귀로 포착한다.
`tests/frontend_aio_settings_core_smoke.mjs`는 manifest default와 현재 JavaScript default의 deep equality 및
frontend coercion/unknown-field 정책과 manifest 내부 coercion/item 정의 완결성을 검증한다.

manifest는 runtime package에 포함되어야 하므로 tracked 상태, `.comfyignore` 비제외, `git archive HEAD` 포함도
dedicated schema test에서 검증한다. 문서와 테스트는 Registry archive에서 제외되어도 된다.
