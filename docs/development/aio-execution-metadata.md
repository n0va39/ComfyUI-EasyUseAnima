# AiO 실행 메타데이터 수정 (#783)

- 목표: 매 생성에서 변경한 설정과 실제 해석된 시드를 해당 이미지의 workflow/API/EXIF에 저장한다. 다음 실행의 UI 설정과 이전 이미지의 저장 데이터를 분리한다.
- 기준: dev `1447789dd9bcca54ba1bf091ddb6904c765b08af`; branch `codex/fix-aio-execution-metadata`.
- 변경 경계: AiO 실행/저장 메타데이터, 원본 출력 URL, LoRA Preset 상대 경로, 관련 회귀 테스트 및 필수 소유권 목록.
- 보존 계약: 노드 ID와 소켓, 기존 설정 스키마와 프로필, 생성 시드 제어, 메타데이터 비활성화, JPEG 초과 크기 sidecar. 실행 중인 API PROMPT를 수정하지 않는다.
- 검증: 연속 생성 설정 변경/실행 스냅샷 불변성/파일 메타데이터 read-back, LoRA 하위 폴더 중복 이름, 출력 원본 URL; 공식 focused runner와 최종 full, 격리된 ComfyUI v0.34.0에서 Legacy Canvas/Node 2.0 저장 및 재로드 경계.
- 완료: 확인된 결함 수정, 검증과 한계 기록, dev 대상 Draft PR 및 Issue 연결. main/배포/사용자 인스턴스 변경은 범위 밖이다.
- 중단 조건: 공식 테스트 환경 갱신 실패는 환경 문제로 분리한다. 외부 모델/LoRA/와일드카드 파일의 변경이나 GPU 비결정성은 동일 이미지 보장의 전제 조건으로 명시한다.
