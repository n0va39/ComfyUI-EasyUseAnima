# SEC-02 Response Confidentiality Contract

## Status and authority

- Issue: [#199](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/199).
- Base: `185021175cb5c9a535c20d49fc6fd5eb8dd3b8ce` (`origin/dev`, merged PR #589).
- Primary class: `CONTRACT`; implemented by SEC-03 without changing the frozen owner
  or rollback boundary.
- Result: **FEASIBLE** inside the direct response owners.
- SEC-03 status: complete.
- Next: SEC-05 completion audit is READY; SEC-04 was skipped because no frontend
  behavior changed.

This Contract fixed one executable owner set and rollback boundary. SEC-03 implemented
that exact boundary in the three production owners and its existing direct test owner.

## Frozen response flow

The current composition order is:

```text
settings / long-text handler factory
  -> raw handler
  -> bootstrap.build_settings_route_group
  -> request-correlation wrapper
  -> ordered route definition / registrar
```

This order permits a raw settings handler to carry one private sensitivity marker.
The existing shared correlation wrapper closes over that raw handler, so it can apply
response confidentiality after either normal completion or its own unexpected-error
normalization. No root `api.py` callback, bootstrap signature, router definition,
middleware, public export, or lifecycle owner needs to change.

## Exact logging Contract

For an unexpected non-HTTP exception crossing the shared request-correlation boundary:

1. Preserve the existing correlated JSON response exactly:
   - status `500`;
   - code `internal_error`;
   - message `An unexpected server error occurred.`;
   - one server-generated request ID in body and `X-Request-ID` header.
2. Emit exactly
   `logger.error("Unhandled EasyUseAnima API error (request_id=%s)", request_id)`.
3. Do not call traceback-bearing `logger.exception` and do not pass `exc_info`,
   `stack_info`, exception text/arguments/type, request object, body, query, URL,
   headers, filesystem path, token, capability, or secret material to the logger.
4. Preserve `asyncio.CancelledError` propagation with no log or normalization.
5. Preserve aiohttp `HTTPException` propagation, body/status, and correlated request-ID
   header. It is not converted to the generic 500 and is not logged.

The implementation remains in `easyuse_anima/api/responses.py`. It does not configure
ComfyUI, aiohttp access logs, a reverse proxy, or the global logging subsystem.

## Exact sensitive-response Contract

The following four routes are sensitive as complete response surfaces:

```text
GET  /easyuse_anima/settings
POST /easyuse_anima/set_setting
GET  /easyuse_anima/long_text_settings
POST /easyuse_anima/long_text_settings/save
```

Their raw factory handlers carry the private boolean marker
`_easyuse_anima_sensitive_response = True`. The marker:

- is attached before bootstrap applies the existing request-correlation wrapper;
- is not part of any module `__all__`, public API, route signature, or serialized
  payload;
- is copied naturally to the wrapped handler by the existing `functools.wraps`
  behavior but is consumed from the closed-over raw handler;
- does not classify wildcard, autocomplete, translation, profile, LoRA, or AiO routes.

For a marked handler, the correlation wrapper sets the exact header
`Cache-Control: no-store` on every response it returns or re-raises:

- successful read or mutation;
- request-contract validation error;
- unknown-setting error;
- unexpected exception normalized to the generic correlated 500;
- aiohttp `HTTPException`, if one crosses that handler boundary.

The header is applied without changing response status, body, content type, existing
headers, request ID, handler identity, or payload identity. Ordinary wildcard and
autocomplete responses remain redacted and do not gain this sensitive marker or a new
cache contract in SEC-03.

## Owner and dependency decision

The complete SEC-03 production owner set is:

| File | Exact responsibility |
| --- | --- |
| `easyuse_anima/api/responses.py` | Consume the private marker, add `no-store` on all correlated sensitive outcomes, and replace traceback-bearing unexpected-error logging with the fixed safe event. |
| `easyuse_anima/api/routes/settings.py` | Mark only the two settings handlers as sensitive before returning them from the factory. |
| `easyuse_anima/api/routes/long_text_settings.py` | Mark only the two long-text settings handlers as sensitive before returning them from the factory. |

No additional owner is necessary. In particular:

- `api.py` dependency mappings stay unchanged;
- `easyuse_anima/bootstrap.py` continues to wrap the same ordered four handlers;
- `easyuse_anima/api/router.py` keeps the exact route order/signature/registrar;
- RuntimeConfig and RuntimeServices gain no capability or cleanup state;
- frontend settings loading and persistence behavior stay unchanged.

The private marker string is an internal response contract, not authentication or an
authorization capability. A caller cannot gain access by setting it on a request.

## Preserved invariants

- Exact 21-route order, signature, handler names/identity, registration marker, and
  idempotent/repeated route refresh.
- Dynamic root monkeypatch seams and injected response/persistence callbacks.
- Settings and long-text parsing, defaults, file-I/O dispatch, mutation order,
  payload identity/merge shape, status/error taxonomy, and request correlation.
- Wildcard/autocomplete path redaction and all ordinary endpoint payloads.
- E-09 single lifecycle owner, shared initialize/shutdown lock, once atexit,
  terminal/idempotent shutdown, translation executor identity and cleanup item 1,
  fixed seven-step cleanup, rollback, and no-reset/no-hot-reinitialize rules.
- Canonical/root `__all__` and public bootstrap/router surfaces.

## Verification ownership

Existing deterministic tests can express the entire implementation Contract. No new
fixture is justified.

- `ApiRequestCorrelationTests` owns safe fixed logging, sensitive success/error/header
  correlation, CancelledError, HTTPException, and ordinary-route non-marking.
- `ApiSettingsRouteTests` owns both settings handlers, all success/error paths, dynamic
  dependencies, raw values, and payload shapes.
- `ApiLongTextSettingsRouteTests` owns both long-text handlers, legacy/wrapped input,
  dynamic dependencies, and payload shapes.
- `ApiPathRedactionTests` owns the unchanged ordinary wildcard/autocomplete redaction.
- `PromptTranslationApiTests` owns unchanged translation error taxonomy while the
  shared correlation boundary emits the fixed safe logging event.
- `PythonBootstrapTests`, package-skeleton direct import, import-boundary, and analyzer
  owners prove that composition/lifecycle/import surfaces did not expand.

SEC-03 changes production and tests, so it runs official full exactly once on its final
candidate SHA. Package/live/browser are not triggered while the implementation stays
inside this fixed pure log/header boundary. An isolated live HTTP smoke becomes
required only if status/body/request-ID behavior or host logger integration changes;
browser smoke becomes required only if frontend files or interaction change.

## SEC-03 implementation record

SEC-03 implemented the fixed logging event and private sensitive-response marker in
`easyuse_anima/api/responses.py`, marked only the four settings/long-text handlers in
their two route modules, and extended `tests/test_api_contract.py`. The generated
analyzer baseline records only those owner deltas. No status, body, request-ID, route,
bootstrap, lifecycle, persistence, schema, or frontend behavior changed.

Direct response contracts, path redaction, bootstrap, package import, import-boundary,
and analyzer gates passed. The final candidate runs official full exactly once; its
result is the promotion evidence consumed by SEC-05. Package/live/browser remain
untriggered because the implementation stayed inside this pure log/header boundary.

## Rollback and stop boundary

Rollback is one SEC-03 commit/PR. Reverting it removes the private marker, restores the
previous logging call, and removes the four cache headers. There is no runtime state,
storage, schema, migration, or frontend rollback.

Stop SEC-03 instead of widening it if any of the following is required:

- changing `api.py`, bootstrap/router public signatures, route registration, or E-09
  lifecycle state;
- configuring ComfyUI/aiohttp/proxy access logging or trusting a proxy/header identity;
- adding authentication, a token/capability, diagnostics, settings split, persistence
  migration, or frontend behavior;
- changing response status/body/request-ID/content type or ordinary endpoint payloads;
- an analyzer/import failure that cannot be explained by the exact three-file owner
  change.
