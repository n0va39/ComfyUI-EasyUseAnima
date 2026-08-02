# AiO Hook API v1 개발 가이드

AiO Hook은 다른 커스텀 노드팩이 `Anima AiO Generator`의 명시적인
`aio_hook` 소켓에 기능을 연결하는 서버 측 Python 계약입니다. v1은 최종
postprocess 경계에서 이미지를 보정하거나 확장 메타데이터·미리보기를 추가하는
용도만 지원합니다. 모델 로딩, conditioning, sampler, latent, 저장 동작은 공개
hook 계약에 포함되지 않습니다.

바로 실행 가능한 최소 노드팩은
[`examples/third_party_aio_hook`](../../examples/third_party_aio_hook/)에 있습니다.

## 지원 범위

| 항목 | v1 계약 |
| --- | --- |
| 소켓 타입 | `EASYUSE_ANIMA_AIO_HOOK` |
| 공개 import | `easyuse_anima.extensions.aio` |
| hook point | `postprocess/before`, `postprocess/after` |
| 반환 patch | 같은 shape의 `IMAGE`, JSON-safe metadata |
| 조합 순서 | before: A → B, core, after: B → A |
| 실패 정책 | 잘못된 계약이나 plugin 예외가 있으면 생성을 실패시킴 |
| 캐시 계약 | JSON-safe `fingerprint`; `None`이면 매번 변경된 것으로 취급 |

`AioStage`에는 실제로 dispatch되는 `POSTPROCESS`만 있습니다. stage와 phase의
임의 조합 대신 `AioHookPoint(stage, phase)`를 각각 선언해야 합니다. 이 방식은
아직 호출되지 않는 미래 지점을 실수로 공개 계약처럼 사용하지 않게 합니다.

## 최소 구현

다른 노드팩은 공개 모듈만 import하고 definition 객체를 커스텀 소켓으로
출력합니다. 단, ComfyUI는 형제 노드팩의 import 순서를 보장하지 않습니다.
소켓 문자열은 로컬 상수로 선언하고 공개 Python API는 아래처럼 node 실행 시점에
지연 import하세요. 그러면 EasyUse Anima보다 provider 노드팩이 먼저 발견되어도
노드 등록이 실패하지 않습니다.

```python
from functools import lru_cache

HOOK_TYPE = "EASYUSE_ANIMA_AIO_HOOK"


@lru_cache(maxsize=1)
def _definition_type():
    from easyuse_anima.extensions.aio import (
        AioHookDescriptor,
        AioHookPatch,
        AioHookPoint,
        AioHookSessionBase,
        AioStage,
        AioStagePhase,
    )

    class MySession(AioHookSessionBase):
        def after_stage(self, event):
            image = event.state.image.mul(0.9).clamp(0.0, 1.0)
            return AioHookPatch(image=image, metadata={"strength": 0.9})

    class MyDefinition:
        def describe(self):
            return AioHookDescriptor(
                hook_id="my_pack.darkener",
                hook_version="1.0.0",
                points=frozenset({
                    AioHookPoint(AioStage.POSTPROCESS, AioStagePhase.AFTER)
                }),
                fingerprint={"strength": 0.9},
            )

        def create_session(self, context):
            return MySession()

    return MyDefinition


class MyAioHookNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = (HOOK_TYPE,)
    FUNCTION = "build"
    CATEGORY = "My Pack/AiO"

    def build(self):
        return (_definition_type()(),)
```

ComfyUI가 노드를 발견하도록 노드팩의 `__init__.py`에서 고유한 이름으로
`NODE_CLASS_MAPPINGS`에 등록합니다. 공식 ComfyUI의
[custom-node lifecycle](https://docs.comfy.org/custom-nodes/backend/lifecycle)과
[서버 노드 속성](https://docs.comfy.org/custom-nodes/backend/server_overview)을
함께 참고하세요.

## definition과 session

definition은 workflow 실행 전에도 호출될 수 있는 가벼운 설정 객체입니다.

- `describe()`는 부작용 없이 같은 설정에 대해 같은 descriptor를 반환해야 합니다.
- `create_session(context)`는 실제 한 번의 postprocess 실행을 위한 상태를 만듭니다.
- 파일, 핸들, 임시 캐시 같은 실행 자원은 definition에 두지 말고 session에서
  만들고 `close()` 또는 `context.services.register_cleanup(callback)`으로
  정리합니다.
- session은 한 번의 생성 실행 밖에서 재사용된다고 가정하지 마세요.

Generator는 descriptor 전체를 모델·VAE 같은 무거운 자원을 열기 전에
검증합니다. session은 postprocess 직전에만 만들며, after callback이 끝나면
저장 단계로 넘어가기 전에 닫습니다. 따라서 그보다 앞선 sampler/Highres/Detailer
실패에는 session이 생성되지 않습니다. session 생성 도중 실패해도 이미 등록된
cleanup과 앞선 session은 역순으로 정리됩니다.

## event와 patch

`AioStageEvent`는 변경할 수 없는 view를 제공합니다.

- `event.request`: normalized mode, node ID, generation settings
- `event.state`: 현재 `image`, width, height, core metadata, extension metadata
- `event.services.emit_preview(stage, image, label=None)`: 선택적 중간 미리보기
- `event.services.register_cleanup(callback)`: run 종료 시 전역 등록 역순(LIFO) 정리

`event.state` 내부 dict를 직접 수정하거나 입력 image를 in-place로 바꾸지 말고
새 `AioHookPatch`를 반환하세요. v1 image patch는 이전 image와 동일하고 읽을 수
있는 tensor shape를 가져야 합니다. 일반적인 ComfyUI `IMAGE` shape는 BHWC입니다.

중요: hook이 바꾸는 것은 Generator의 `IMAGE` 출력뿐입니다. `LATENT` 출력은
core pipeline이 마지막으로 만든 latent이며 hook 결과 image와 일치하도록 다시
인코딩되지 않습니다. 정확한 최종 픽셀이 필요한 downstream에는 `IMAGE` 출력을
연결하세요.

metadata는 hook별 `extensions.hook_data["<hook_id>#<ordinal>"]` 아래에 저장됩니다.
각 patch의 metadata는 JSON-safe dict여야 하고 최대 64 KiB입니다. 같은 hook이
한 실행에서 같은 최상위 metadata key를 두 번 쓰면 오타나 순서 의존을 숨기지
않도록 오류가 발생합니다.

## 순서와 조합

`Anima AiO Hook Combine`은 2~4개의 hook을 연결 순서대로 합칩니다.

```text
hook_a.before → hook_b.before → core postprocess
              → hook_b.after → hook_a.after
close hook_b → close hook_a
cleanup callbacks → 전체 callback의 등록 역순(LIFO)
```

이는 중첩 middleware와 같은 순서입니다. 여러 hook을 쓸 때는 before에서 입력을
준비하고 after에서 결과를 감싸는 방식으로 생각하면 됩니다. wrapper 순서의
일반적인 참고 사례는 [pluggy hook wrappers](https://pluggy.readthedocs.io/en/stable/)를,
역순 자원 정리는 Python
[`ExitStack`](https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack)을
참고할 수 있습니다. session `close()`는 provider의 역순으로 실행됩니다. cleanup
callback은 provider별로 묶이지 않고 전체 등록 순서를 기준으로 역순 실행되므로,
before/after에서 늦게 등록한 callback이 먼저 실행됩니다.

## fingerprint와 재현성

`fingerprint`에는 출력에 영향을 주는 모든 definition 설정을 JSON-safe 값으로
넣습니다. dict key 순서와 무관하게 canonical JSON 형태로 change token이
계산되며 descriptor에서 읽을 때 깊은 복사됩니다. 최대 크기는 16 KiB입니다.

```python
fingerprint={
    "strength": self.strength,
    "preview": self.preview,
    "algorithm": "v1",
}
```

tensor, model, 열린 파일, callback, 세션별 ID처럼 mutable하거나 JSON으로
직렬화할 수 없는 값은 넣지 마세요. 안정적인 fingerprint를 만들 수 없으면
`None`을 사용하세요. 이 경우 AiO Generator의 `IS_CHANGED`는 항상 변경으로
처리되어 오래된 결과를 재사용하지 않습니다.

## 오류 처리

- descriptor는 hook ID, API version, point, fingerprint를 session 생성 전에
  검증합니다.
- plugin callback의 일반 예외는 hook ID/version/point를 포함한
  `AioHookExecutionError`로 전달됩니다.
- 계약 위반은 `AioHookContractError`입니다.
- 별도의 `on_error` callback은 v1에 없습니다. 자원 정리는 `close()`와
  `register_cleanup()`에 둡니다.
- `KeyboardInterrupt`와 `SystemExit`는 plugin 오류로 래핑하지 않습니다. 등록된
  정리 작업을 시도한 뒤 원래 종료 신호를 그대로 전달합니다. Python의 공식
  [exception hierarchy](https://docs.python.org/3/library/exceptions.html#exception-hierarchy)도
  참고하세요.

AiO Hook은 sandbox가 아닙니다. provider 노드팩은 EasyUse Anima 및 ComfyUI와
같은 Python 프로세스에서 실행되며 파일·네트워크·호스트 상태에 접근할 수
있습니다. 출처와 코드를 신뢰할 수 있는 provider만 설치하고 연결하세요.

## 체크리스트와 문제 해결

- public API version은 `AIO_HOOK_API_VERSION == 1`인지 확인합니다.
- 형제 노드팩의 모듈 최상위에서는 공개 API를 import하지 말고 node 실행 시점에
  지연 import합니다.
- `hook_id`는 노드팩 namespace를 포함한 안정적인 ASCII ID로 정합니다.
- image 연산은 out-of-place이고 shape를 보존하는지 확인합니다.
- `fingerprint`에 모든 출력 영향 설정이 들어가는지 확인합니다.
- `NODE_CLASS_MAPPINGS`에 출력 노드를 등록하고 ComfyUI를 재시작합니다.
- 여러 hook의 순서가 중요하면 `Anima AiO Hook Combine`의 socket 순서를 확인합니다.
- `repeated metadata keys` 오류가 나면 before/after가 서로 다른 key를 반환하게
  수정합니다.
- `must preserve shape` 오류가 나면 resize/crop을 v1 hook 밖에서 수행하거나
  원래 BHWC shape로 되돌립니다.

전체 예제에는 설정 widget, 미리보기, fingerprint, metadata, 등록 코드가 모두
포함되어 있습니다: [`examples/third_party_aio_hook`](../../examples/third_party_aio_hook/).
