# E-04 Translation Runtime Ownership Contract

## Scope and authority

E-04a is a production-free Contract at
`dev@d952f15f637732ce45a1ab7d9a0006bd1a3362bc`. It inventories the current
translation provider registry/client, default service cache/per-key single-flight,
and API route executor before any E-04 Move.

The executable source is
`tests/fixtures/python_translation_runtime_contract.v1.json`, checked by
`tests/test_python_translation_runtime_contract.py`. Existing translation service
and API tests remain the behavior authorities.

## Three distinct resource boundaries

### Provider registry and optional client

`easyuse_anima.translation.service` owns the provider factory mapping, lazy instance
mapping, and registry `RLock`. The first Google request constructs one
`GoogleTranslationProvider`; that provider has a separate `RLock` and lazily imports
and constructs the optional `googletrans` client on first use.

The provider registry owns lookup, construction, publication, and reuse. It does not
own cache policy or API admission. The current client protocol exposes only
`translate`, so a client `close` contract is not proven. E-04 must not invent one.

### Default service, cache, and per-key single-flight

The canonical service module constructs `_DEFAULT_TRANSLATION_SERVICE` at import.
That service owns one bounded TTL/LRU cache and a per-key single-flight registry.
Cache entries use one `RLock`; flight registration uses a second `RLock`; each cache
key gets its own `Lock`, so different translation keys can proceed independently.

`BoundedTranslationCache.clear()` exists, and each flight removes itself after the
last user settles. The module default service has no process reset or idempotent
close. API and Prompt-node paths currently converge through
`translate_prompt_markers()`.

### API route executor

Root `api.py` invokes the canonical `build_translation_runtime()` factory at module
import and assigns `_PROMPT_TRANSLATION_WORKER` plus three helper closures. The
canonical `PromptTranslationRouteExecutor` lazily creates a one-thread executor,
permits one in-flight request, and keeps admission occupied after timeout or
cancellation until the synchronous worker actually settles.

The worker has idempotent `shutdown()`, registered once with `atexit`, but package
shutdown and partial-initialization cleanup do not own it. The root worker, sync
function, timeout, settings resolver, translation function, and error response remain
dynamic compatibility/test seams.

## Target ownership decision

E-04 does not create a generic executor or client abstraction. Direct evidence shows
three different contracts:

- provider registry/client: lazy optional dependency, reusable provider identity,
  provider-specific timeout and error normalization;
- service/cache: marker budgets, TTL/LRU, cache-key partitioning, and per-key
  single-flight settlement;
- API route executor: single admission, busy/cancel/timeout mapping, event-loop
  offload, and late worker settlement.

Each remains a translation-owned narrow resource/port. Bootstrap is the only target
production composition root for their concrete instances and lifecycle registration.
Adapters receive or resolve only the translation port they need. Feature/domain code
must not import `RuntimeServices`, bootstrap, API adapters, or root shims.

This refines the ADR statement that `RuntimeServices` owns process resources: any
runtime expansion is made only by the owning Move and contains narrow
translation-owned ports, not a shared generic executor/client or the complete
runtime passed into feature code.

## Preserved behavior and compatibility

All E-04 Moves preserve:

- root `prompt_translation.py` identity re-exports and canonical public `__all__`;
- marker syntax, off-mode unwrapping, settings defaults, budgets, and error classes;
- cache key `(provider, source, target, text)`, TTL boundary, LRU bound, and
  per-key single-flight;
- lazy optional import, one provider/client reuse, provider timeout, HTML unescape,
  and unavailable/timeout/upstream error normalization;
- one route worker, no shared executor use, busy admission, cancellation/timeout
  response, late settlement, and event-loop responsiveness;
- dynamic root worker/sync/timeout/settings/translation patch seams;
- request parsing, payload/status/error mapping, request correlation, route identity,
  registration, and repeated bootstrap behavior;
- package/no-host import with the provider disabled.

No E-04 Move may add a provider close call without direct supported-client evidence.
Cache policy, timeout values, error meaning, admission count, and cancellation
semantics are Behavior and remain out of scope.

## Bounded Move queue

1. **E-04a Contract — complete:** current owners, callers, locks, cleanup gaps,
   compatibility seams, optional import, and Move order are versioned.
2. **E-04b Move — provider registry/client ownership — READY:** move factories,
   instances, and registry locking behind one explicit translation provider registry
   while preserving lazy client behavior and errors.
3. **E-04c Move — default service/cache composition — pending:** compose one
   process translation service with its cache and flights, then wire current node/API
   callers through narrow seams.
4. **E-04d Move — route executor/bootstrap lifecycle wiring — pending:** move worker
   construction and lifecycle registration from root `api.py` into bootstrap-owned
   composition while preserving every dynamic root seam.
5. **E-04e Contract — completion audit — pending:** reconcile E-01 targets, prove
   one owner per resource, optional-import safety, cleanup disposition, and zero
   ambiguous translation state before E-05.

Each Move is a separate rollback boundary. E-09 still owns whole-runtime
initialize/shutdown ordering and partial-failure cleanup; E-04 supplies the
translation-owned resources and idempotent cleanup shapes that E-09 will compose.

## Stop conditions

Stop the owning Move if it would require a generic executor/client port, a
feature-to-runtime/API/bootstrap/root back-reference, an import-time optional
dependency, loss of a supported identity/dynamic seam, changed cache/provider/error
or admission behavior, or an unproven client cleanup call.

The direct evidence and existing ADRs select one resource partition, so E-04a does
not trigger additional PRO review.
