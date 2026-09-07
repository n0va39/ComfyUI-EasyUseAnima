# 1.2.1 버그 수정 릴리즈

- 목표: AiO 실행 메타데이터/LoRA 수정과 공개 main의 후속 버그 수정을 GitHub Release 및 Comfy Registry에 배포한다.
- 기준: 공개 main `88cec830164e3ca80b84d9682356992bfa71e947`. dev의 수정 `14f225540755cd411aa22c2f3e4b63b4c9e680ba`만 cherry-pick한다. dev 전용 Easy Save Image / Easy Image Metadata / Easy Civitai Lookup 노드 및 개발 기능은 포함하지 않는다.
- 소유: `codex/release-1.2.1`, main 대상 릴리즈 PR. 버전과 릴리즈 메타데이터는 별도 dev 동기화 PR로 반영한다. AiO 기능 수정은 이미 dev에 존재한다.
- 허용 변경: #785의 코드/테스트/검증 문서, main 파일 구성에 맞춘 생성 기준선, pyproject 버전, RELEASE.md, Registry 변경 안내/메타데이터, 이 기록.
- 보존: node id/소켓/설정/프로필, 선택적 메타데이터, 기본/외부 저장 노드 계약. 사용자 설치본은 변경하지 않는다.
- 검증: cherry-pick production diff 대조, 관련 focused, 최종 후보 full, Registry validate/pack 및 아카이브 검사. 같은 프런트엔드 코드의 Legacy/Node 2.0 검증을 재사용하고 실제 릴리즈 패키지의 PNG 재생성은 격리 인스턴스에서 확인한다.
- 완료: main 병합, 불변 annotated tag, 루트 폴더가 있는 수동 ZIP/SHA-256/GitHub Release, Registry 게시 및 API 상태/변경 안내/다운로드 확인, 메타데이터 dry-run/apply/no-op 확인, dev 메타데이터 동기화.
- 중단: 버전 충돌, 잘못된 publisher, 실패한 필수 검사나 예상 밖 패키지 파일은 게시 전에 해결한다. Registry Pending/Flagged는 업로드 성공과 구분하고 외부 상태로 보고한다.

## 검증 기록

- dev 원본 #785는 최종 full 1,683 tests(기존 skip 3), JS 125개 및 TypeScript 6.0.3을 통과했다. 일반 노드 PNG의 Legacy Canvas/Node 2.0 재로드 후 캐시 없는 재생성 픽셀 일치와 설정 변경 이후 이전 파일 불변성을 확인했다.
- main cherry-pick 충돌은 생성 기준선 및 소유권 파일 수에 한정됐다. main의 201개 production 파일에 새 실행 메타데이터 모듈 하나를 더해 202개로, 지원 파일은 215개에서 216개로 조정했다. native image output의 기존 main 동작은 보존한다.
- 최종 코드 후보 `8154562`: ComfyUI 0.34.0 (`12d5279438bfefc058a269eae805ceab6047777f`), frontend 1.49.6, Python 3.12.13에서 full 통과. Python 1,649 tests(기존 skip 3), JavaScript 123개, TypeScript 6.0.3 및 정적/계약 검사를 통과했다. 최초 full의 유일한 실패인 공개 샘플 3개 버전 표기를 수정하고 workflow focused 12 tests 후 full을 재검증했다. Registry release copy focused 4 tests도 통과했다.
- 공식 comfy-cli 1.20.0 validate/pack 통과. 배포 파일 347개, 제외된 tracked 파일 476개, 버전 1.2.1. 패키지 생성 후 변경된 것은 패키지에서 제외되는 샘플 버전과 이 검증 기록뿐이므로 아카이브 검증은 재사용한다.
- 해당 Registry 패키지를 격리 인스턴스에 설치한 후 두 PNG의 내장 API/workflow로 실제 GPU 재생성을 확인했다. 384x512 / seed 784435166335536 / 6 steps / CFG 4.5 / er_sde와 576x768 / seed 456 / 9 steps / CFG 6.2 / euler + Highres 조건을 각각 실행했다. LoRA 7개, first-pass cache false이며 두 이미지 모두 원본 RGB SHA-256과 일치했다. 내장 workflow widget, 실행 기록, API settings, parameters seed도 일치했다.
- main port production 변경과 #785의 patch-id는 동일하다. 동일 프런트엔드의 Legacy Canvas/Node 2.0 저장·재로드 증거를 재사용하며, dev 전용 추가 노드나 동작을 이번 릴리즈 검증으로 확대하지 않는다. 독립 코드/메타데이터 리뷰에서 차단사항은 없었다.
- dev 동기화는 버전, 사용자 안내, Registry 메타데이터, 샘플 버전 및 검증 기록만 반영한다. runtime 코드는 변경하지 않으며 기존 dev full과 동기화 후보의 Registry 4/workflow 12 focused 통과 증거를 사용한다.
