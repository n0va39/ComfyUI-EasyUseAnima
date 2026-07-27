# AiO generation settings v2 계약

이 문서는 `easyuse_anima_aio_generation_settings` v2의 정적 계약과 소유 경계를 설명한다. 현재 기준 manifest는
`easyuse_anima/aio/schemas/generation_settings.v2.json`이며 v1 manifest는 migration 입력 계약으로 보존한다.

기준 manifest는 [#168](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/168)의 C168-01 Contract PR에서
도입했다. C168-02는 v0.5.2 release workflow에 저장된 AiO generation settings 입력과 normalized
결과를 현재 runtime에 다시 적용해 deep equality로 고정한다. C168-03은 기존 Python normalizer가 만든 완전한
v1 object를 checked-in typed config로 변환하고 다시 독립된 가변 dictionary로 복원하는 경계를 추가한다.
Python/JavaScript runtime은 manifest를 import하지 않는다. AIO-SCOPE-01은 pure v1→v2 migration을 runtime의
기존 compatibility facade 앞에 연결하지만 stage MODEL cutover나 DAVE UI는 수행하지 않는다.

## 소유권

| 계약 | owner | 비고 |
| --- | --- | --- |
| v2 정적 field shape와 default | `easyuse_anima.aio.generation_settings` manifest | Python/JavaScript default와 golden equality |
| 정적 enum, min/max, coercion 분류 | manifest | 현재 backend normalizer 동작으로 검증 |
| legacy alias와 unknown-field 정책 | manifest | surface별 현재 차이도 명시 |
| Python 실행 시 정규화 | 현재 `nodes.py` | 이번 PR에서 이동하거나 변경하지 않음 |
| normalized Python v2 typed boundary | `easyuse_anima/aio/generation_*.py` DAG | 정규화 이후 순수 양방향 변환, dictionary compatibility facade 유지 |
| frontend v1→v2 in-memory migration/default merge | `web/js/aio/settings.js` | 저장 object 불변, explicit save 전 write 없음 |
| Comfy/Impact sampler, scheduler, max resolution 목록 | Comfy capability adapter/runtime | manifest가 값 목록을 소유하지 않음 |
| profile envelope, ID, revision, CAS | [#163](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/163) | nested `settings` payload 내부만 #168 소유 |

manifest의 `default`는 완전한 normalized v2 기본 object다. `shape`는 field type, coercion, static enum 및
bound를 제공하고 반복되는 Spectrum/DiT correction/Detailer target은 `definitions`와 `$ref`로 표현한다.
모든 coercion 참조, array item, open JSON object value, `custom_<n>` pattern field가 manifest 내부 정의로
해결되므로 후속 consumer가 별도의 암묵 token 표 없이 계약을 해석할 수 있다. 다만 이번 PR은 실제
generator/codegen/typed model을 추가하거나 특정 generator와의 호환성을 주장하지 않는다. 현재 runtime source of
execution은 기존 코드다.

## 정적 field 정책

정규화 이후의 root는 object이며 다음 section을 갖는다.

| section | 핵심 정적 계약 |
| --- | --- |
| `schema`, `version`, `mode` | schema name 고정, current version 2, mode enum |
| `sampler` | backend/seed control enum, steps/cfg/denoise bound, Spectrum/SPD/DiT correction |
| `model_patches` | AuraFlow, DAVE와 4-stage scope, Safe PAG, KJ/torch compile |
| `mod_guidance`, `artist_mix` | mode/profile enum과 weight/layer/count bound |
| `highres`, `upscale`, `postprocess` | stage switch, method/backend enum, size/sampling bound |
| `detailer` | ordered `face`/`eye`와 `custom_<n>` target contract |
| `save`, `preview` | save backend/format/metadata와 preview feed contract |

각 normalized object는 known field를 채우면서 unknown field를 기본적으로 보존한다. 빈 extension object인
`sampler.spectrum_extra`와 `sampler.spd_extra`도 기존 공개 확장 지점으로 유지한다.

DAVE의 `stage_scope` stage id는 `first_pass`, `highres`, `detailer`, `upscale`로 고정한다. fresh v2 default는
first pass만 true다. `upscale`은 sampling MODEL을 사용하는 USDU 계약이며 ResShift, postprocess, save는 이
scope에 포함하지 않는다. patch-order revision 1은 KJ Torch Compile과 DAVE가 함께 선택된 stage에서
`kj.torch_compile → dave` precedence edge만 승인한다.

AIO-SCOPE-04 audit는 Anima Safe PAG `905b0107`과 KJNodes `e27a505b`의 public source,
그리고 current ComfyUI `ModelPatcher.clone()`의 `model_options` deep-copy 계약을 기준으로 했다.
generic scope UI는 승인하지 않고 patch별 owner를 다음처럼 고정했다.

| patch | stage-scope 결정 | 근거와 후속 |
| --- | --- | --- |
| DAVE | 지원 | 네 sampling stage를 현재 schema/runtime/UI가 소유한다. |
| Safe PAG | 후속 검증 필요 | MODEL clone과 sampler callback을 사용하지만 shared attention module을 일시적으로 바꾸므로 precedence/cleanup/live 증명을 [#440](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/440)에서 분리한다. |
| KJ FP16 accumulation | stage scope 미지원 | pre-run/cleanup callback이 process-global torch flag를 바꾸므로 run-global 설정으로 유지한다. |
| KJ SageAttention | 후속 검증 필요 | clone-local `model_options` override이지만 upstream experimental 계약과 `allow_compile`을 [#441](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/441)에서 검증한다. |
| KJ Torch Compile | stage scope 미지원 | compiled module registry가 shared BaseModel을 key로 쓰고 Dynamo config도 process-global이므로 현재는 run-global 설정으로 유지한다. #410은 진단/추천만 소유하며 generic scope를 추가하지 않는다. |

Safe PAG와 KJ 설정에 저장된 unknown `stage_scope`는 보존할 수 있지만 현재 patch selection을 부분 변경하지
않는다. 지원되지 않은 field 때문에 기존 all-stage 실행 의미가 조용히 달라지지 않는 것이 rollback 계약이다.

## Python typed config 경계

`generation_values.py`가 frozen JSON primitive와 unknown-field ordering state만 소유하고,
`generation_sampling.py`가 sampling shape, `generation_features.py`가 stage와 model feature,
`generation_detailer.py`가 SAM3/Detailer, `generation_output.py`가 save/preview shape를 소유한다.
`generation_settings.py`는 이 단방향 DAG를 root `AIOGenerationConfig`로 조합하고 dictionary facade만 제공한다.

`AIOGenerationConfig`는 root identity와 section ownership을 명시한다. Spectrum, SPD, DiT correction,
model patch 하위 설정, Mod Guidance, Artist Mix, highres, upscale/USDU/ResShift, postprocess/fit, SAM3/Detailer target,
save/Image Saver/Civitai fetcher, preview의 manifest known field는 서로 교환할 수 없는 section-specific frozen
dataclass가 소유한다. 각 section의 unknown JSON value는 별도 frozen extension state에 보관된다. dictionary에서
typed config로 변환할 때와 typed config에서 dictionary로 복원할 때 모두 nested object와 array를 새로 구성하므로
caller input, typed state, 반환 dictionary 사이에 공유되는 mutable reference가 없다. non-object `custom_<n>`처럼
target shape가 아닌 값도 unknown extension으로 원래 순서와 scalar type을 유지한다.

이 경계는 `_normalize_aio_generation_settings()`의 마지막에만 적용된다. 기존 normalizer가 dynamic Comfy/Impact
capability를 조회하고 coercion, legacy alias 제거, unknown-field 처리를 끝낸 뒤 typed round-trip을 수행한다.
호환 facade의 이름과 mutable dictionary 반환 계약은 유지되며 runtime consumer는 typed object를 직접 사용하지 않는다.
typed layer 자체는 Comfy runtime을 import하거나 default/capability cache와 같은 mutable global state를 소유하지 않는다.

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

v2는 pure v1→v2 migration을 가진다. v1의 `model_patches.dave` object에 `stage_scope`가 없으면 네 sampling
stage를 모두 true로 채워 기존 all-stage 실행 의미를 보존한다. explicit scope는 덮어쓰지 않고 unknown JSON도
보존한다. Read/list/load는 원본 profile/workflow bytes, mtime, revision을 바꾸지 않으며 실제 persist는 사용자가
요청한 save/update 같은 mutation에서만 수행한다.

`easyuse_anima/aio/generation_migrations.py`의 strict detector와 immutable registry는 shipped 1→2 step을
소유한다. `_normalize_aio_generation_settings()`는 canonical schema와 지원 범위의 integer version에만 dispatcher를
적용한다. schema가 없거나 invalid/future version인 기존 compatibility 입력은 이전처럼 normalization facade에서
처리하므로 이번 Contract가 별도 strict rejection behavior를 추가하지 않는다. frontend parse/compact 경계도 raw
v1 object를 defaults merge 전에 migrate한다. 양쪽 모두 migration은 in-memory clone이며 write-on-read가 아니다.

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
- [#168](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/168)의 C168-03이 typed config와 dictionary
  compatibility facade를 소유한다. 후속 단계가 pure version migration과 omission gate를 각각 소유한다.

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
`tests/test_aio_generation_settings.py`는 default와 v0.5.2 expected normalized payload의 typed round-trip,
root/nested unknown field, custom Detailer order/target, Spectrum/SPD extension object, legacy 비복원 및 mutable
reference 격리를 검증한다.

`tests/fixtures/aio_generation_settings_surface_coverage.v2.json`은 manifest의 canonical field와 `$ref` site를
기준으로 Python default/typed owner, JavaScript default owner, sanitization owner, UI owner/exposure, 유지 문서 heading을
명시하는 golden coverage ledger다. entry 전체 또는 surface 하나가 빠지거나 owner module/document heading이
사라지면 gate는 `/<contract-path>: missing surface <surface>`로 실패한다. Python 쪽은 각 normalized default
leaf를 하나씩 제거했을 때 typed conversion이 반드시 거부하는지도 검증하므로, unknown extension 보존이 새 known
field의 typed 누락을 숨길 수 없다. manifest shape와 default의 불일치는 `manifest_default` 또는
`manifest_shape` surface로 별도 보고한다. empty Civitai fetcher item은 대표 row를 합성해 같은 ownership을
확인한다.

frontend smoke는 manifest와 JavaScript default의 leaf set을 비교하고, default를 compact serialization한 결과가
동일한 leaf set을 보존하는지 별도로 확인한다. 따라서 default 추가와 sanitization 경로 추가는 독립된 surface로
보고된다. coverage ledger는 runtime에서 import하지 않으며 dynamic capability choice, dialog 동작, optional
dependency policy를 변경하지 않는다.

manifest는 runtime package에 포함되어야 하므로 tracked 상태, `.comfyignore` 비제외, `git archive HEAD` 포함도
dedicated schema test에서 검증한다. 문서와 테스트는 Registry archive에서 제외되어도 된다.
