# 기여 가이드

언어: [English](CONTRIBUTING.md) | [한국어](CONTRIBUTING.ko.md)

ComfyUI EasyUse Anima 개선에 관심을 가져 주셔서 감사합니다. 이 프로젝트는
ComfyUI 커스텀 노드 팩이므로, 가능한 한 기존 워크플로우, 저장된 설정, 사용자
데이터와의 호환성을 유지해야 합니다.

참여하기 전에 [Code of Conduct](CODE_OF_CONDUCT.md)를 읽어 주세요.

## 언어

이슈, 토론, PR 설명은 영어 또는 한국어로 작성할 수 있습니다. 버그, 기능 요청,
기여 내용을 한국어로 설명하는 것이 더 편하다면 한국어로 작성해도 됩니다. 한국어
사용은 선택 사항이며, 영어 기여도 환영합니다.

## 프로젝트 범위

이 저장소는 다음 영역에 집중합니다.

- ANIMA/Spectrum 워크플로우용 프롬프트 편집과 보정.
- NAIA 프롬프트 가져오기와 재사용 가능한 프롬프트 메타데이터.
- 와일드카드 확장과 자동완성 동작.
- LoRA 프리셋 관리.
- AiO 생성 헬퍼와 Detailer 편의 노드.
- 공개 예제 워크플로우와 노드 문서.

관련 없는 대규모 프레임워크 변경, 노드 실행 중 런타임 패키지 설치, 난독화된
코드, 비공개 사용자 데이터를 저장해야 하는 기능은 범위 밖입니다.

## 이슈 작성

이슈를 열기 전에 README, 기존 이슈, 최근 릴리즈 노트를 확인해 주세요. 좋은
버그 리포트에는 다음 정보가 포함됩니다.

- EasyUse Anima 버전, 커밋, 또는 설치 출처.
- ComfyUI 버전 또는 Manager 설치 방식.
- 관련이 있다면 운영체제와 Python 버전.
- 워크플로우에 필요한 다른 커스텀 노드.
- 문제를 재현하는 명확한 단계.
- 기대한 동작과 실제 동작.
- 관련 줄만 정리한 ComfyUI 콘솔 로그 또는 브라우저 오류.
- 재현에 도움이 되는 최소 워크플로우 JSON 또는 스크린샷.

API 키, 토큰, 비공개 경로, 비공개 모델 출처, 개인정보는 게시하지 마세요.
로그에 비밀 정보가 포함되어 있다면 게시 전에 제거해 주세요.

보안 취약점은 public exploit 세부 내용을 올리지 말고
[Security Policy](SECURITY.md)를 따라 신고해 주세요.

## 기능 요청

기능 요청은 다음 내용을 포함하면 검토하기 쉽습니다.

- 해결하려는 워크플로우 문제.
- 영향을 받는 노드 또는 UI 영역.
- 저장 후 다시 불러온 워크플로우에서 기대하는 동작.
- 기존 노드 입력, 출력, 메타데이터, 설정이 바뀌는지 여부.
- 관련 커스텀 노드 또는 상위 ComfyUI 동작.

기존 워크플로우에 영향을 주는 기능이라면 호환성 기대치를 설명해 주세요.
하위 호환되는 변경을 강하게 선호합니다.

## Pull Request

일반 개발 PR은 `dev` 브랜치를 base로 사용해 주세요. `main`은 안정적인
사용자/설치 브랜치입니다.

PR 작성 시:

- 변경 범위를 작고 명확하게 유지합니다.
- 의도적으로 breaking change를 논의한 경우가 아니라면 기존 노드 class id,
  input 이름, output type, workflow serialization을 보존합니다.
- 동작 변경에는 테스트를 추가하거나 갱신합니다.
- UI, 노드 동작, 워크플로우 템플릿, 설정이 바뀌면 사용자 문서도 갱신합니다.
- PR 설명에 변경 전/후 동작을 적습니다.
- 실행한 검증 명령을 적습니다.
- 테스트하지 못한 항목을 명확히 적습니다.

관련 없는 리팩터링, 포맷만 바꾸는 수정, 동작 변경을 한 PR에 섞지 마세요.

## 로컬 설정

수동 테스트를 위해 저장소를 ComfyUI custom node 디렉터리에 clone합니다.

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/n0va39/ComfyUI-EasyUseAnima
cd ComfyUI-EasyUseAnima
```

ComfyUI가 사용하는 같은 Python 환경에 의존성을 설치합니다.

```bash
pip install -r requirements.txt
```

설치, 업데이트, Python 파일 변경 후에는 ComfyUI를 재시작해야 합니다.
프론트엔드 JavaScript를 변경했다면 브라우저 hard refresh가 필요할 수 있습니다.

## 검증

변경한 파일에 맞는 검증을 실행해 주세요. 저장소 루트에서:

```bash
python -m unittest discover -s tests
python -m compileall -q .
git diff --check
```

프론트엔드 JavaScript 파일을 변경했다면:

```bash
node --check web/js/<changed-file>.js
```

워크플로우 템플릿을 변경했다면:

```bash
python -m unittest discover -s tests -p test_workflows.py
```

PowerShell에서는 다음 명령으로 저장소 전체 검증을 실행할 수 있습니다.

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_project.ps1 -Profile full
```

Python suite의 공식 runner는 `unittest`입니다. 이 custom-node package
구조에서는 pytest를 full-suite runner로 지원하지 않습니다.

변경이 실제 ComfyUI 동작에 의존한다면 실제 ComfyUI 인스턴스에서도 테스트하고,
PR에 테스트한 ComfyUI 버전을 적어 주세요.

## 코드 작성 기준

- 수정 범위는 대상 노드, 설정, route, UI 동작에 맞게 제한합니다.
- 이 저장소의 기존 helper와 패턴을 우선 사용합니다.
- Python 노드 정의는 명확하게 유지합니다: `INPUT_TYPES`, `RETURN_TYPES`,
  `RETURN_NAMES`, `FUNCTION`, `CATEGORY`.
- persistent cache key나 저장된 워크플로우 데이터에 Python `hash()`를 사용하지
  않습니다.
- 노드 실행 중 shell command를 실행하지 않습니다.
- 필요한 경우가 아니라면 의존성을 추가하지 않습니다. 추가해야 한다면
  `pyproject.toml`과 `requirements.txt`에 모두 기록합니다.
- 사용자 데이터는 저장소 밖에 유지합니다. 설정, LoRA 프로필, 와일드카드는
  ComfyUI user data 경로에 있어야 합니다.

## 프론트엔드 기준

- ComfyUI frontend extension은 `web/js/` 아래에 둡니다.
- Python input 값으로 필요한 hidden widget은 serialized 상태로 유지합니다.
- workflow serialization은 명시적으로 갱신합니다. DOM 상태만으로는 충분하지
  않습니다.
- input, mousemove, render, layout loop에서 반복 API polling을 만들지 않습니다.
- 가능하면 ComfyUI frontend API를 사용합니다.
- custom DOM widget을 변경했다면 저장된 워크플로우를 다시 불러오는 동작을
  확인합니다.

## 문서와 워크플로우

- 사용자용 노드 문서는 `docs/nodes/` 아래에 둡니다.
- 공개 예제 워크플로우 파일과 preview/source 이미지는
  `docs/example_workflows/` 아래에 둡니다.
- 릴리즈 워크플로우 파일명은 `*_release_en.json`, `*_release_ko.json`,
  `*_release_ja.json`, `*_release_zh.json`처럼 언어별 release suffix를
  유지합니다.
- 개인 테스트 워크플로우, local LoRA 경로, 임시 preview URL, clipspace 이미지,
  비공개 모델 경로를 커밋하지 마세요.
- 릴리즈 워크플로우 템플릿을 수정할 때는 `extra.easyuse_anima_workflow`
  메타데이터를 최신 상태로 유지합니다.

## 다국어 지원

표준 노드 다국어 지원은 ComfyUI locale 파일인
`locales/<lang>/nodeDefs.json`을 사용합니다. Python 노드 정의에는 영어 fallback
텍스트를 유지합니다. Frontend text map은 ComfyUI locale 파일로 처리할 수 없는
custom DOM widget, 메뉴, alert, prompt, settings panel에만 사용합니다.

locale 파일을 변경했다면 JSON을 검증해 주세요.

```bash
python -m json.tool locales/ko/nodeDefs.json
```

수정한 언어에 맞게 경로를 바꿔 실행하면 됩니다.

## 유지보수자 전용 작업

릴리즈 publish, Comfy Registry publish, version tag 생성, 이미 공개된 release
history 변경은 유지보수자 작업입니다. API key, publisher token, release secret을
이슈, PR, 문서, workflow 파일, 테스트 데이터에 포함하지 마세요.
