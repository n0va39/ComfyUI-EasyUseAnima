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
