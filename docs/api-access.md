# EasyUse API access

## Local ComfyUI

Open ComfyUI at `http://127.0.0.1:8188`, `http://localhost:8188`, or an IPv6
loopback address. Ordinary local use needs no additional login. EasyUse checks
the actual socket peer and a literal loopback/localhost Host before running
any of its HTTP handlers. Browser mutations also require same-origin JSON.

This is a single trusted local operator boundary, not user authentication.
Forwarded headers do not grant access. A reverse proxy or tunnel can hide an
external caller behind a local connection, so any proxy/tunnel deployment must
use the authenticated mode below, even when ComfyUI listens only on loopback.

## Authenticated remote access

Set `EASYUSE_ANIMA_API_TOKEN` to a long, randomly generated secret in the
environment that starts ComfyUI, then restart ComfyUI. Keep the value outside
the repository and ComfyUI settings/user files. EasyUse captures its digest at
startup; changing a web setting cannot change or disclose the credential.

When the token is set, **every EasyUse API request requires authentication**,
including requests from loopback and local proxies. Use standard HTTP Basic:

- Username: `easyuse`
- Password: the value of `EASYUSE_ANIMA_API_TOKEN`

For browser use, visit `/easyuse_anima/settings` on the same ComfyUI origin to
complete the browser's HTTP authentication prompt, then return to ComfyUI.
The shared realm also covers preview image requests. Credentials stay out of
EasyUse JavaScript, workflow JSON, settings and URLs. A wrong or missing
credential returns `401` with a Basic authentication challenge.

API clients send the same Basic authorization header. Existing JSON mutation
requests still need `Content-Type: application/json` and matching `Origin` and
`Host`. Use HTTPS through an authenticated gateway for remote connections:
HTTP Basic encodes credentials but does not encrypt them. An existing gateway
can supply the credential only after authenticating the caller; it must replace
client-supplied authorization and prevent direct backend access.

Preserve the browser's original Host at the backend so the existing Origin
check accepts POST requests. A proxy using its own separate Basic credentials
cannot also forward another Basic credential in the same Authorization header;
use the same credential or a different gateway authentication mechanism.

To rotate the secret, change the startup environment and restart ComfyUI.
Clearing the variable restores local-only access. An unavailable EasyUse runtime
fails closed with `503`; it does not downgrade to local mode.

## Scope and compatibility

Node IDs, profile data, settings keys, workflows and API success payloads stay
unchanged. Direct unauthenticated LAN access to EasyUse routes is no longer
supported. Existing local clients using a custom hostname should use a literal
loopback address or configure authentication.

This access check covers `/easyuse_anima/*` routes. It does not authenticate
ComfyUI's `/prompt`, core settings, or another extension's routes. Protect the
whole ComfyUI service at the gateway when exposing it remotely. The independent
[NAIA destination policy](naia-network-policy.md) still applies to queued node
execution, including requests submitted through `/prompt`.
