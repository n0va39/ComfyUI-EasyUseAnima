# EasyUse Anima 언어 관리

EasyUse Anima는 ComfyUI 기본 언어 설정을 따른다. 노드 정보, 입력/출력 이름,
tooltip처럼 ComfyUI가 자체적으로 번역할 수 있는 영역은 공식 커스텀 노드
locale 구조를 사용하고, 커스텀 DOM UI처럼 ComfyUI가 자동 번역하지 못하는
영역만 JS text map으로 관리한다.

## 기준

- 영어 문구는 Python과 JavaScript의 기본 fallback으로 둔다.
- 공개 노드 정의 번역은 `locales/ko`, `locales/ja`, `locales/zh`,
  `locales/zh-CN`의 `nodeDefs.json`에 모두 둔다.
- EasyUse Anima 전용 언어 설정은 만들지 않는다.
- 표준 노드 정보와 힌트를 번역하기 위해 JavaScript에서 `/object_info` 또는
  node definition을 직접 덮어쓰지 않는다.

## 노드 정보, 입력, 출력

Impact Pack과 같은 ComfyUI 공식 locale 구조를 사용한다.

```text
locales/
  ko/nodeDefs.json
  ja/nodeDefs.json
  zh/nodeDefs.json
  zh-CN/nodeDefs.json
```

`nodeDefs.json`은 ComfyUI custom node manager가 수집하고 `/i18n`으로 제공한다.
구조는 다음 형식을 따른다.

```json
{
  "EasyUseAnimaNodeClassName": {
    "display_name": "한국어 표시 이름",
    "description": "정보 패널 설명",
    "inputs": {
      "input_name": {
        "name": "한국어 입력 이름",
        "tooltip": "한국어 입력 tooltip"
      }
    },
    "outputs": {
      "0": {
        "name": "한국어 출력 이름",
        "tooltip": "한국어 출력 tooltip"
      }
    }
  }
}
```

Python 노드 클래스에는 비한국어 환경을 위한 영어 fallback을 유지한다.

- `DESCRIPTION`
- `INPUT_TYPES()`의 `tooltip`
- `RETURN_NAMES`
- `OUTPUT_TOOLTIPS`

## 커스텀 DOM과 설정창

`nodeDefs.json`은 다음 영역을 자동 번역하지 않는다.

- 커스텀 DOM widget
- canvas에 직접 그리는 버튼
- 커스텀 context menu
- `alert`, `prompt`
- EasyUse Anima 설정 패널

이 영역은 JS text map으로 관리한다.

- 영어 문구를 fallback으로 둔다.
- 한국어 문구를 같은 키 구조로 둔다.
- ComfyUI 기본 언어가 한국어이면 한국어를 선택한다.
- 그 외 언어는 영어 fallback을 사용한다.
- 별도 EasyUse Anima 언어 설정은 저장하지 않는다.
- DOM 팝업의 제목, 섹션 제목, 필드 라벨, 버튼, tooltip은 JS text map을
  통하도록 한다. 새 하드코딩 문자열을 추가하면 같은 작업에서 text map 키와
  한국어 값을 함께 추가한다.

## 새 노드 추가 시 체크리스트

1. Python 클래스에 영어 `DESCRIPTION`을 추가한다.
2. 출력이 있으면 영어 `OUTPUT_TOOLTIPS`를 추가한다.
3. `locales/ko`, `locales/ja`, `locales/zh`, `locales/zh-CN`의
   `nodeDefs.json`에 같은 class id 항목을 추가한다.
4. 비한국어 locale 파일에는 한글 문자열을 넣지 않는다.
5. locale key는 `NODE_CLASS_MAPPINGS`의 class id와 정확히 일치해야 한다.
6. required input과 output index가 빠지지 않았는지 확인한다.
7. `nodeDefs.json`을 JSON으로 검증한다.

## 검증

```powershell
python -m unittest tests.test_locales
```

라이브 ComfyUI 인스턴스에 반영한 뒤에는 ComfyUI 재시작 또는 브라우저 새로고침이
필요할 수 있다. `/i18n`과 `/object_info`가 다시 로드되어야 정보 패널과 힌트가
갱신된다.
