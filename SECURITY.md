# Security Policy

Language: [English](#english) | [한국어](#한국어)

## English

### Supported Versions

Security fixes are handled for the latest `main` branch and the latest tagged
release. Older releases and development branches are handled on a best-effort
basis.

### Reporting a Vulnerability

Please do not open a public issue with exploit details, secret values, private
paths, or private workflow data.

Use GitHub's private vulnerability reporting from the repository Security tab if
it is available. If private vulnerability reporting is not available, email the
maintainer at `fulgensnova39@gmail.com`.

If neither private channel is available, open a public issue with only a
high-level request for a security contact and do not include exploit details
until a private channel is established.

Helpful report details:

- Affected EasyUse Anima version, tag, or commit.
- ComfyUI version and installation method.
- Operating system and Python version when relevant.
- Minimal steps to reproduce the issue.
- Expected impact and affected feature or file.
- Sanitized logs or proof-of-concept data without secrets or private paths.

### Security Scope

Please report issues such as:

- Arbitrary command execution.
- Arbitrary file read or write outside the expected ComfyUI user data paths.
- Path traversal through workflow, wildcard, LoRA preset, or metadata handling.
- Injection or unsafe parsing that can execute code or alter files unexpectedly.
- Accidental exposure of tokens, API keys, private paths, or personal data.
- Vulnerable dependencies that affect this node pack at runtime.

Issues that require a fully trusted local user to intentionally run unsafe code
may be treated as lower priority, but they can still be reported if the impact
is unclear.

### Handling

This is a small project, so response time is best effort. Maintainers may ask
for reproduction details, prepare a fix on `dev`, and release the fix through
the normal release process. Public credit can be given if the reporter wants it.

### Responsible Disclosure

Do not publicly disclose exploit details before a fix is available or before the
maintainer agrees that disclosure is appropriate. Do not test against systems,
data, or accounts that you do not own or have permission to inspect.

## 한국어

### 지원 버전

보안 수정은 최신 `main` 브랜치와 최신 tag release를 기준으로 처리합니다. 오래된
release와 개발 브랜치는 가능한 범위에서만 지원합니다.

### 취약점 신고

취약점 세부 내용, secret 값, 비공개 경로, 비공개 workflow 데이터는 public issue에
올리지 마세요.

저장소 Security 탭에서 GitHub private vulnerability reporting을 사용할 수 있다면
그 기능으로 신고해 주세요. 사용할 수 없다면 maintainer에게
`fulgensnova39@gmail.com`으로 이메일을 보내 주세요.

두 private 채널을 모두 사용할 수 없다면 public issue에는 보안 연락 채널 요청만
높은 수준으로 남기고, exploit 세부 내용은 private 채널이 생긴 뒤 공유해 주세요.

신고에 도움이 되는 정보:

- 영향을 받는 EasyUse Anima 버전, tag, 또는 commit.
- ComfyUI 버전과 설치 방식.
- 관련이 있다면 운영체제와 Python 버전.
- 문제를 재현하는 최소 단계.
- 예상 영향과 영향을 받는 기능 또는 파일.
- secret이나 비공개 경로를 제거한 로그 또는 proof-of-concept 데이터.

### 보안 범위

다음과 같은 문제를 신고해 주세요.

- 임의 명령 실행.
- 예상된 ComfyUI user data 경로 밖의 임의 파일 읽기 또는 쓰기.
- workflow, wildcard, LoRA preset, metadata 처리에서 발생하는 path traversal.
- 코드 실행 또는 예상치 못한 파일 변경으로 이어질 수 있는 injection 또는 안전하지
  않은 parsing.
- token, API key, 비공개 경로, 개인정보의 accidental exposure.
- 이 node pack 런타임에 영향을 주는 dependency 취약점.

신뢰할 수 있는 로컬 사용자가 의도적으로 unsafe code를 실행해야만 발생하는 문제는
우선순위가 낮을 수 있습니다. 영향이 불명확하다면 신고해도 됩니다.

### 처리 방식

이 프로젝트는 작은 프로젝트이므로 응답 시간은 best effort입니다. Maintainer는
재현 정보를 요청하고, `dev`에서 수정한 뒤 일반 release 절차로 배포할 수 있습니다.
신고자가 원하면 public credit을 제공할 수 있습니다.

### 책임 있는 공개

수정이 준비되었거나 maintainer가 공개에 동의하기 전에는 exploit 세부 내용을
공개하지 마세요. 본인이 소유하지 않았거나 점검 권한이 없는 시스템, 데이터, 계정을
대상으로 테스트하지 마세요.
