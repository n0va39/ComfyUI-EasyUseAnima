# NAIA connection policy / NAIA 연결 정책

From 1.2.2, settings select an endpoint but cannot grant network permission.
The ComfyUI process operator grants exact destinations at startup through the
non-secret `EASYUSE_ANIMA_NAIA_ENDPOINTS` environment variable.

1.2.2부터 웹 설정은 접속 대상을 선택하며 접속 권한을 추가하지 않습니다.
운영자가 ComfyUI 시작 환경에 아래 JSON 목록을 지정합니다. API key나 토큰을
넣는 변수가 아닙니다. ComfyUI 설정 UI나 사용자 데이터 파일에는 저장하지 마세요.

## Examples / 예시

Default local endpoints need no variable: `127.0.0.1:7243`, `localhost:7243`
(connects to `127.0.0.1`) and `[::1]:7243`.

Windows PowerShell, additional local port and LAN service:

```powershell
$env:EASYUSE_ANIMA_NAIA_ENDPOINTS = '[{"host":"127.0.0.1","port":7244},{"host":"192.168.0.2","port":7243}]'
# Run your normal ComfyUI launcher from this same shell.
```

Linux/macOS, pinned hostname:

```sh
export EASYUSE_ANIMA_NAIA_ENDPOINTS='[{"host":"naia.lan","port":7243,"address":"192.168.0.2"}]'
# Run your normal ComfyUI launcher from this same shell.
```

Replace example addresses with your own NAIA service. For named hosts,
`address` must be a numeric IP. Requests use that address with the validated
hostname in the HTTP Host header. No runtime DNS resolution or redirect is used.
IPv6 is supported; scoped/link-local, unspecified, multicast and reserved
destinations are rejected. A numeric host cannot be remapped to another IP.

실제 NAIA 주소로 예시를 바꿔 사용하세요. 도메인의 `address`는 숫자 IP로 지정해야
하며 DNS 변경 후에도 자동으로 새 주소에 접속하지 않습니다. IP 변경 시 운영자
허용 목록을 바꾸고 ComfyUI를 재시작합니다. `localhost`를 IPv6로 쓰려면 설정의
host를 `[::1]`로 선택하세요.

The JSON list adds exact endpoints to the local defaults. Every entry requires
`host` and an integer `port` between 1 and 65535; only `address` is optional.
Unknown fields, malformed entries, and conflicting mappings disable NAIA until
corrected. An empty/unset variable retains the local defaults. Normal nodes,
image saving, and other features remain available if NAIA policy is invalid.

설정 UI에서 host·port를 선택한 뒤 원격 연결에는 기존 `원격 API 허용`도 켜야 합니다.
이 스위치만 바꾸거나 ComfyUI 설정 API를 호출해서는 승인 목록을 확대할 수 없습니다.
허용되지 않은 대상은 연결 전에 고정 오류로 차단합니다.

## Scope

NAIA uses its existing fixed HTTP POST API. It does not inherit proxy environment
variables, `.netrc` credentials, or session cookies. This policy restricts NAIA
destinations; it does not add ComfyUI authentication or make an exposed ComfyUI
server safe. Use trusted services and an authenticated gateway/firewall where
appropriate. Node IDs, saved settings keys and workflow payloads are unchanged.
