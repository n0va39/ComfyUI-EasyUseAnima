# Security/Admin Settings Boundary Roadmap

## Status and authority

- Status: active independent maintenance lane after Phase F/G completion.
- Owner: Issue #199.
- First READY task: SEC-01 host capability and threat-model Contract.
- Released baseline: 0.6.2.
- This lane does not reopen Phase F/G, P-API-02, D-14, or Phase H.
- Type: Security/Admin Contract first; no production behavior change before the
  access owner and deployment model are fixed.

## 1. Why this is the next executable lane

The completed backend roadmap is correctly event-gated:

```text
Phase F/G complete
P-API-01 RETAIN
D-14/H waiting for release/consumer events
```

That state does not prohibit an independent security task with its own owner and
rollback boundary. Issue #199 is P2 and is not dependent on a root-shim removal event.
It therefore becomes the next bounded maintenance lane without pretending that an
H/D-14 task is READY.

## 2. Current evidence

### ComfyUI host boundary

Current ComfyUI source exposes a `UserManager`, but its multi-user request identity is
selected by the client-provided `comfy-user` header. It validates that the selected ID
exists; it does not authenticate the caller or assign an administrator role.

The PromptServer middleware provides cache handling, deprecation warnings, optional
CORS, an origin/host check for loopback browser requests, and optional Manager
middleware. These are useful request-origin controls but do not establish an
authenticated administrator capability for custom-node routes.

Consequences:

- `comfy-user` is a storage/profile selector, not authentication;
- origin/host checks are not authorization;
- `request.remote` is not sufficient behind reverse proxies;
- arbitrary `X-Forwarded-*` or custom headers are not trusted unless a reviewed proxy
  owner verifies and strips client-supplied values;
- EasyUseAnima must not assume a host admin API that has not been demonstrated.

### EasyUseAnima settings boundary

Current EasyUseAnima settings routes:

```text
GET  /easyuse_anima/settings
POST /easyuse_anima/set_setting
```

The GET route returns `public_settings()` and the POST route writes a known setting,
then returns the same projection. The current projection includes values such as:

```text
wildcard.extra_paths
naia.host
naia.port
naia.allow_remote_api
naia.pre_prompt
naia.post_prompt
```

This is a configuration surface, not a diagnostics-only endpoint. SEC-01 must decide
whether the whole surface is intentionally trusted with the ComfyUI UI, or whether
safe UI settings and sensitive local/admin configuration require separate access
contracts.

## 3. Deployment models to classify

SEC-01 must classify each model rather than designing only for localhost:

1. single-user direct loopback;
2. LAN or remote direct bind;
3. reverse proxy without authentication;
4. reverse proxy with externally enforced authentication;
5. ComfyUI `--multi-user` profile selection;
6. managed/multi-tenant deployment where custom-node routes are reachable by users.

For each model record:

- caller trust assumption;
- source of authenticated identity, if any;
- whether forwarded headers are trusted and by whom;
- whether settings read, settings mutation, and local path diagnostics are allowed;
- whether the model is supported, conditionally supported, or explicitly unsupported.

## 4. SEC-01 — Host capability and threat-model Contract

Type: production-free Contract/gate.

### Required inventory

- current ComfyUI middleware, user-manager, request and route extension surfaces;
- current EasyUseAnima settings/status/wildcard/autocomplete routes;
- every setting or response field that contains a filesystem path, host/port, remote
  enable flag, user-authored prompt text, or other local configuration;
- frontend consumers of those fields;
- logging and request-ID/error paths that could disclose a capability, raw path, or
  secret header;
- RuntimeConfig/bootstrap seams that could own process-start configuration without
  creating a second lifecycle owner.

### Required classifications

Every relevant route and field is classified as one of:

```text
ordinary redacted status
safe UI configuration
sensitive local configuration
administrator diagnostics
secret/capability material
```

Do not classify all settings as sensitive merely because they are persisted. Base the
classification on actual disclosure or mutation impact.

### Trust rules

SEC-01 must preserve these defaults:

- no authenticated host capability is assumed without primary-source evidence;
- `comfy-user`, `request.remote`, Host, Origin, and forwarded headers do not individually
  prove administrator authority;
- ordinary status/search/classify/wildcard responses remain redacted even for an
  authorized diagnostic caller;
- no capability or token is stored in ordinary EasyUseAnima settings;
- no token is accepted in a query string or JSON body;
- no token, raw path, or secret header appears in error payloads, request-ID logs,
  access logs, or debug output;
- a diagnostics endpoint is absent by default; when disabled it should not reveal that
  a capability exists;
- no outbound telemetry or noisy import-time warning is introduced.

### E-09 lifecycle guard

If SEC-01 concludes that an EasyUseAnima-owned process capability is required, the
future owner must satisfy all of the following:

- process-start configuration is loaded by RuntimeConfig/bootstrap before route use;
- bootstrap remains the single lifecycle owner;
- no second lock, atexit hook, shutdown/reset API, mutable application registry, or hot
  reinitialize behavior is added;
- the capability is immutable for the process lifetime unless a separate Behavior
  Contract explicitly changes E-09;
- no close operation is invented for immutable capability data;
- package/no-host import remains safe when the capability is absent.

SEC-01 does not implement that owner.

## 5. Allowed SEC-01 verdicts

The audit must return exactly one primary verdict.

### HOST_CAPABILITY

Use only when a stable ComfyUI authenticated-admin contract is proven and available to
custom-node routes. Record the exact API, supported versions, failure behavior, and
fallback when unavailable.

### PROCESS_CAPABILITY

Use when a dedicated EasyUseAnima process-start capability is necessary and can be
owned by RuntimeConfig/bootstrap without weakening E-09. Produce one bounded SEC-02
Contract card; do not implement a token in SEC-01.

### TRUSTED_DEPLOYMENT_ONLY

Use when the settings/configuration API should remain inside the same trusted boundary
as the ComfyUI server and no safe in-process administrator capability is justified.
Record supported deployment assumptions, required external authentication for remote
exposure, and any field-level redaction or route split still needed.

### NO_DIAGNOSTICS

Use when no reliable authorization owner exists and path diagnostics provide
insufficient benefit. Keep diagnostics unavailable and identify only independent
settings-hardening work, if any.

A combined result may include one primary verdict plus an exact field-level follow-up,
but must not leave multiple mutually exclusive access models for implementation to
choose later.

## 6. Conditional follow-up queue

No task after SEC-01 is automatically READY.

```text
READY       SEC-01 threat model / capability owner / field classification
CONDITIONAL SEC-02 exact access and response Contract
CONDITIONAL SEC-03 narrow backend implementation
CONDITIONAL SEC-04 frontend settings migration, only if UI behavior changes
CONDITIONAL SEC-05 security/package/live completion audit
```

Examples of valid SEC-02 boundaries:

- split safe settings projection from sensitive configuration;
- guard sensitive mutation without changing ordinary status routes;
- add a disabled-by-default diagnostics route with an already approved owner;
- document trusted external-auth deployment and remove an unjustified internal
  diagnostics proposal.

Do not combine all examples into one implementation.

## 7. Validation

### SEC-01

- direct source and route-consumer inventory;
- focused settings/API/redaction/security contract tests already present;
- source/fixture consistency and `git diff --check`;
- official full only when a test/tool/shared fixture changes;
- no package/live for a docs-only Contract.

### Future backend implementation

Run only when triggered by the selected contract:

- direct route and settings persistence tests;
- disabled/wrong/correct capability cases, when a capability exists;
- loopback/direct-remote/forwarded/reverse-proxy cases fixed by deterministic request
  fixtures;
- error/log redaction and `Cache-Control: no-store` where appropriate;
- package/no-host import and E-09 lifecycle regression;
- isolated live HTTP smoke for the changed backend surface;
- browser smoke only when the settings UI or interaction changes.

## 8. Stop and PRO conditions

Codex handles ordinary inventory, threat-model writing, field classification, and
focused test work without PRO review.

Request focused technical PRO review only when primary-source evidence leaves multiple
security architectures that are all viable, for example:

- two host/proxy capability models with materially different trust guarantees;
- a capability owner cannot be selected without changing E-09 lifecycle semantics;
- a reverse-proxy trust contract requires subtle header normalization or spoofing
  analysis beyond the bounded route owner;
- a settings split creates unavoidable compatibility or data-migration alternatives;
- logging/redaction guarantees cannot be proven across several independent owners.

User preference is not used as a substitute for security evidence. A missing host
admin capability by itself is not a PRO blocker; it is an input to the SEC-01 verdict.

## 9. Codex resume instruction

```text
Start Issue #199 / SEC-01 from latest origin/dev.

Read only:
- current-policies.md
- codex-execution-efficiency.md universal rules
- this document
- Issue #199 latest checkpoint
- current EasyUseAnima settings/status/wildcard/autocomplete route owners and direct tests
- current settings public projection and frontend consumers
- current ComfyUI PromptServer middleware and UserManager primary source
- E-09 lifecycle Contract only for the process-capability guard

Do not reopen Phase F/G, P-API-02, D-14, release, or Registry work.
Do not implement authentication, a token, a diagnostics route, or a settings split in
SEC-01.

Produce:
- deployment/threat matrix
- route/field sensitivity inventory
- host capability verdict
- logging/redaction contract
- one primary verdict: HOST_CAPABILITY, PROCESS_CAPABILITY,
  TRUSTED_DEPLOYMENT_ONLY, or NO_DIAGNOSTICS
- exact SEC-02 task card only when implementation is justified

Reuse existing deterministic tests. Add a fixture only for a real unowned contract.
Package/live are not triggered by a docs-only SEC-01 result.
```
