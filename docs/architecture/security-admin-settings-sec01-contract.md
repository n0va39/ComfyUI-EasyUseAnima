# SEC-01 Security/Admin Settings Contract

## Status and authority

- Issue: [#199](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/199).
- Base: `7e8b323007b4ae3d858eeae273f647f9f0233fba` (`origin/dev`, merged PR #588).
- Type: production-free deployment, capability, sensitivity, and redaction audit.
- Primary verdict: **TRUSTED_DEPLOYMENT_ONLY**.
- Follow-up: one SEC-02 response-confidentiality Contract is justified; no
  authentication, capability token, diagnostics route, settings split, or frontend
  migration is authorized by this document.

This document classifies supported trust assumptions. It does not add enforcement to
the current routes. An unsupported deployment remains technically reachable when an
operator exposes ComfyUI without an adequate external boundary.

## Primary-source capability finding

The current ComfyUI source was reviewed at commit
[`e651b7bef55a5376343dcb1c0edb79f0142c985e`](https://github.com/Comfy-Org/ComfyUI/commit/e651b7bef55a5376343dcb1c0edb79f0142c985e).

- [`UserManager`](https://github.com/Comfy-Org/ComfyUI/blob/e651b7bef55a5376343dcb1c0edb79f0142c985e/app/user_manager.py)
  uses `comfy-user` to select an existing user-data profile in multi-user mode. It
  does not authenticate that header, assign an administrator role, or expose an
  authenticated-admin capability to custom-node routes.
- [`PromptServer`](https://github.com/Comfy-Org/ComfyUI/blob/e651b7bef55a5376343dcb1c0edb79f0142c985e/server.py)
  provides origin/Host checks and optional CORS behavior. Those are browser-origin
  controls, not principal authentication or route authorization.
- EasyUseAnima settings are resolved once from a process-owned `USER_DATA_DIR` and
  stored in `settings.json` and `long_text_settings.json`. Route requests do not
  select a different repository through `comfy-user`.

Consequently, `comfy-user`, `request.remote`, Host, Origin, or any one forwarded
header is never accepted as administrator proof. Forwarded headers have meaning only
inside an explicitly configured external proxy trust boundary; EasyUseAnima does not
interpret them as authority.

### Candidate disposition

| Candidate | Result | Reason |
| --- | --- | --- |
| `HOST_CAPABILITY` | Rejected | No stable authenticated-admin capability is available to these custom-node routes in the reviewed host source. |
| `PROCESS_CAPABILITY` | Rejected for this lane | RuntimeConfig/bootstrap could own immutable process-start data without changing E-09, but safely conveying a capability to the browser would require a new authentication or trusted-gateway design. No current route needs such a token under the selected deployment boundary. |
| `TRUSTED_DEPLOYMENT_ONLY` | **Selected** | The current UI legitimately consumes raw local/network configuration, while no in-process administrator identity is available. The whole settings surface therefore stays inside one trusted operator boundary. |
| `NO_DIAGNOSTICS` | Incorporated, not primary | Administrator diagnostics remain absent, but settings are an existing configuration surface rather than a diagnostics-only feature. |

No focused PRO review is required: primary-source evidence leaves one viable boundary
without proxy/header normalization or E-09 lifecycle redesign.

## Deployment and threat matrix

`Ordinary redacted routes` below means wildcard and autocomplete status/search/classify
responses whose path-bearing internal state is removed. Redaction is not authentication
and does not make an otherwise unsupported server exposure safe.

| Deployment | Effective trust boundary | Sensitive settings read/mutation | Ordinary redacted routes | Support verdict |
| --- | --- | --- | --- | --- |
| Single-user direct loopback | Local OS account, browser session, and ComfyUI process are one trusted operator boundary. No administrator identity is inferred from loopback itself. | Allowed under the single trusted-operator assumption. | Allowed; redaction remains mandatory. | **Supported** for a trusted single operator. |
| LAN or remote direct bind | Network reachability is the only boundary; ComfyUI supplies no authenticated admin principal to the routes. | Not an approved exposure. Any reachable client could read or mutate the process-wide settings. | Redaction remains mandatory but does not authorize remote exposure. | **Unsupported** unless an external boundary changes the model. |
| Reverse proxy without authentication | The proxy only forwards reachability. Host, Origin, remote address, and forwarded headers are spoofable or routing metadata, not authority. | Not approved. | Redaction remains mandatory. | **Unsupported**. |
| Reverse proxy with external authentication | The proxy or gateway owns authentication before ComfyUI. It must cover every route, reject bypass access, and strip or replace client-supplied authentication/forwarding headers. | Conditionally allowed only when every authenticated principal is a trusted operator with equal settings authority. EasyUseAnima does not distinguish viewer/admin roles. | Allowed behind the same boundary; still redacted. | **Conditionally supported** as an all-operators trusted deployment, not as EasyUseAnima authorization. |
| ComfyUI `--multi-user` | `comfy-user` selects host user data; it is not authentication. EasyUseAnima settings remain in one process-resolved repository. | No per-user isolation or admin boundary. Allowed only if all users are mutually trusted operators under another supported deployment boundary. | Allowed only under that surrounding boundary; redaction remains mandatory. | **Conditionally supported** for mutually trusted profiles; **unsupported** as a security boundary. |
| Managed or multi-tenant | Tenants require authenticated identity, role separation, isolation, and audit guarantees not supplied by the reviewed host/custom-node contract. | Not approved. | Endpoint redaction alone is insufficient for tenant isolation. | **Unsupported** until a separately proven host/gateway capability and storage-isolation contract exists. |

For the conditionally supported authenticated-proxy case, the deployment owner also
owns TLS, session security, proxy access-log redaction, cache policy enforcement, and
prevention of direct ComfyUI bypass. A proxy that authenticates users but grants some
of them read-only or non-administrator status does not satisfy this Contract because
EasyUseAnima currently cannot consume that role distinction.

## Route and field sensitivity inventory

### Route classification

| Route | Current data flow | Classification and Contract |
| --- | --- | --- |
| `GET /easyuse_anima/settings` | Returns the complete public settings projection, including raw local/network configuration. The frontend loads it during extension setup. | **Sensitive local configuration** as a whole. Trusted-deployment only; future response hardening must use `Cache-Control: no-store`. |
| `POST /easyuse_anima/set_setting` | Mutates a known key and returns the complete projection. No current frontend caller was found, but the route remains a supported API surface. | **Sensitive local configuration** regardless of the mutated key because the response contains the mixed projection. Trusted-deployment only and `no-store`. |
| `GET /easyuse_anima/long_text_settings` | Returns long-text values plus the complete projection; the long-text editors consume it. | **Sensitive local configuration** and authored prompt content. Trusted-deployment only and `no-store`. |
| `POST /easyuse_anima/long_text_settings/save` | Mutates long-text values and returns the saved values plus complete projection. | **Sensitive local configuration** and authored prompt content. Trusted-deployment only and `no-store`. |
| `GET /easyuse_anima/wildcards` | Resolves raw roots internally, but returns root IDs/labels/existence and wildcard items without absolute root paths. | **Ordinary redacted status/content**. Never add raw roots, repository paths, capability material, or secrets. |
| `GET /easyuse_anima/autocomplete_status` | Builds status from source/index state and strips path fields. | **Ordinary redacted status**. Never add local source/index paths or secrets. |
| `GET /easyuse_anima/autocomplete` | Returns matches and redacted nested status. | **Ordinary redacted search**. Query and results do not gain administrator semantics. |
| `POST /easyuse_anima/classify_prompt` | Returns classification and redacted nested status. | **Ordinary redacted classification**. Prompt input must not be copied to error or request-ID logs. |

The settings frontend directly consumes `/settings`, `/long_text_settings`, and
`/long_text_settings/save`. Its wildcard-path editor and NAIA endpoint controls need
the raw values, so silently redacting the existing settings projection would break a
real consumer. A settings split is therefore neither required nor authorized by the
selected trusted-deployment verdict.

### Field classes

| Sensitivity class | Current examples | Contract |
| --- | --- | --- |
| Ordinary redacted status | Request ID; wildcard root opaque ID/label/existence and wildcard items; autocomplete source identity/count/state; matches and classifications with path fields removed. | May be returned by ordinary endpoints, but never with resolved filesystem paths, request headers, or capability/secret material. |
| Safe UI configuration | Autocomplete mode/source/limit/commit preferences; LoRA preset display/strength preferences; Prompt Studio visual and interaction preferences; translation provider/source/target choices; NAIA resolution and preprocessing choices. | Safe relative to the other settings fields, but the current mixed settings responses remain sensitive as a whole. Translation/NAIA choices can affect outbound behavior and must not be represented as authorization. |
| Sensitive local configuration | `wildcard.extra_paths`; `naia.host`; `naia.port`; `naia.allow_remote_api`; `prompt.metadata_filter_words`; `naia.pre_prompt`; `naia.post_prompt`; `naia.auto_hide`; the process-resolved settings repository location. | Available only inside the trusted deployment boundary. Do not place values in logs, error details, URLs, or diagnostics. |
| Administrator diagnostics | Resolved absolute wildcard roots; autocomplete source/index paths; settings/user-data file paths; traceback, environment, storage, and host-integration details. | No route currently exposes these, and SEC-01 authorizes none. Keep them absent unless a later Contract proves an authorization owner and benefit. |
| Secret or capability material | External `Authorization`/cookie/session data, proxy identity assertions, future process capability values, API tokens, and secret headers. | Not settings fields and never serializable. Do not accept them through URL/query settings, echo them, persist them in EasyUseAnima settings, or emit them to any log/debug output. |

## Logging and redaction Contract

The following rules apply regardless of deployment trust:

1. Client errors expose only the stable status/code/default message and correlated
   request ID already owned by the API contract. Raw exception text, traceback,
   filesystem path, request body, query secret, capability, token, cookie, and secret
   header are forbidden.
2. Request-correlation logs may contain the request ID and a fixed event/category only.
   They must not format `str(exc)`, `repr(exc)`, exception arguments, request content,
   raw URLs/query strings, or headers.
3. Generic traceback logging is not safe at this boundary: an exception message and
   stack can contain raw configuration and local paths. Debug mode does not relax the
   redaction rule.
4. EasyUseAnima must not add secret/capability material to access-log fields. A host or
   external proxy that owns authentication must independently redact its access and
   debug logs; that external guarantee is a condition of the supported deployment.
5. The four sensitive settings responses use `Cache-Control: no-store`. Ordinary
   wildcard/autocomplete endpoints stay redacted even if a future deployment adds
   authentication.

Current deterministic tests prove safe client payloads and path removal, but the
shared request correlator still calls `logger.exception(...)`, which records the active
exception traceback, and the sensitive settings responses have no explicit `no-store`
owner. These are response-confidentiality gaps, not evidence for adding authentication
or a process capability.

## E-09 lifecycle disposition

No lifecycle change is required. Bootstrap remains the only lifecycle owner;
initialize/shutdown keep the same lock; atexit remains once-registered; shutdown stays
terminal/idempotent; repeated initialize retains runtime identity and route refresh;
the translation executor remains cleanup item 1; fixed rollback and cleanup ordering
remain unchanged. SEC-01 adds no RuntimeConfig field, second lock, reset, close item,
or hot reinitialize API.

## Completion

SEC-02 completed with a direct-owner **FEASIBLE** result in
[`security-admin-settings-sec02-response-contract.md`](security-admin-settings-sec02-response-contract.md).
SEC-03 completed sanitized unexpected-error logging and `no-store` on the four
sensitive settings responses without entering any forbidden boundary. SEC-04 was
skipped because frontend behavior did not change. SEC-05 completed the production-free
audit with no follow-up. The primary verdict remains **TRUSTED_DEPLOYMENT_ONLY** and
administrator diagnostics remain absent. Authentication, tokens, diagnostics, settings
projection changes, and frontend migration remain forbidden.
