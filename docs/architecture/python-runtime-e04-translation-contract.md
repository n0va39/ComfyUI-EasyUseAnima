# E-04 Translation Runtime Ownership Contract

## Scope and authority

E-04a is a production-free Contract created at
`dev@d952f15f637732ce45a1ab7d9a0006bd1a3362bc`. E-04b makes provider registry
ownership explicit. E-04c composes the process translation service/cache into
RuntimeServices. E-04d completes the third bounded Move by moving concrete route
executor construction and lifecycle registration behind private bootstrap
composition.

The executable source is
`tests/fixtures/python_translation_runtime_contract.v1.json`, checked by
`tests/test_python_translation_runtime_contract.py`. Existing translation service
and API tests remain the behavior authorities.

## Three distinct resource boundaries

### Provider registry and optional client

`easyuse_anima.translation.service._DEFAULT_TRANSLATION_PROVIDER_REGISTRY` is the
process owner. Its private `_TranslationProviderRegistry` owns a copied provider
factory mapping, lazy instance mapping, and registry `RLock`. The public service
facade resolves the current default registry on every call. The first Google request
constructs one `GoogleTranslationProvider`; that provider has a separate `RLock` and
lazily imports and constructs the optional `googletrans` client on first use.

The provider registry owns lookup, construction, publication, and reuse. Tests create
isolated registries instead of mutating module-level factory and instance maps. The
registry does not own cache policy or API admission. The current client protocol
exposes only `translate`, so a client `close` contract is not proven. E-04 must not
invent one.

### Default service, cache, and per-key single-flight

Bootstrap constructs one `_SystemClock`, one bounded TTL/LRU cache using that
clock's `monotonic` method, and one `PromptTranslationService`. RuntimeServices owns
the service through the translation-owned `PromptTranslationPort`; the canonical
service facade installs and resolves the same identity for current node/API calls.
A standalone canonical import retains its local compatibility default until
production bootstrap composition.

Cache entries use one `RLock`; flight registration uses a second `RLock`; each cache
key gets its own `Lock`, so different translation keys can proceed independently.
`PromptTranslationService.close()` idempotently clears its owned cache, and each
flight removes itself after the last user settles. It does not close providers,
cancel work, or create a terminal closed state. API and Prompt-node paths continue
to converge through `translate_prompt_markers()`.

### API route executor

Private `easyuse_anima.bootstrap.build_translation_route_runtime()` invokes the
canonical `build_translation_runtime()` factory and owns the concrete executor/error
types plus `atexit` registration. Root `api.py` invokes only that private composition
helper and assigns `_PROMPT_TRANSLATION_WORKER` plus three helper closures as dynamic
compatibility seams. The canonical `PromptTranslationRouteExecutor` lazily creates a
one-thread executor, permits one in-flight request, and keeps admission occupied
after timeout or cancellation until the synchronous worker actually settles.

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
2. **E-04b Move — provider registry/client ownership — complete:** factories,
   instances, and registry locking are owned by one private provider registry; the
   call-time default facade, lazy client behavior, and errors are preserved.
3. **E-04c Move — default service/cache composition — complete:** bootstrap composes
   the clock/cache/service, RuntimeServices owns the narrow port, and current node/API
   callers retain the call-time service facade.
4. **E-04d Move — route executor/bootstrap lifecycle wiring — complete:** concrete
   worker construction and `atexit` lifecycle registration are bootstrap-owned while
   root retains every dynamic compatibility seam.
5. **E-04e Contract — completion audit — complete:** reconciles E-01 targets, proves
   one owner per resource, optional-import safety, cleanup disposition, and zero
   ambiguous translation state before E-05.

Each Move is a separate rollback boundary. E-09 still owns whole-runtime
initialize/shutdown ordering and partial-failure cleanup; E-04 supplies the
translation-owned resources and idempotent cleanup shapes that E-09 will compose.

## Completion audit result

The E-01 and E-04 fixtures agree on all three translation resources:

| E-01 entry | E-04 owner | Completed phase | Cleanup disposition |
| --- | --- | --- | --- |
| `root-translation-route-worker` | `route-executor` | E-04d | idempotent `shutdown()` and one `atexit` registration; whole-runtime ordering remains E-09 |
| `translation-default-service` | `default-service` | E-04c | idempotent cache-only `close()`; whole-runtime ordering remains E-09 |
| `translation-provider-registry` | `provider-registry-client` | E-04b | intentional no-close because the proven optional-client protocol exposes no cleanup method |

There are zero ambiguous translation state owners. `googletrans` remains a local
import inside `GoogleTranslationProvider._create_translator`, so package/no-host
imports do not require the optional client. The route executor, default service, and
provider registry retain separate locks, lifetimes, and cleanup semantics; no generic
executor/client port or duplicate module state is introduced.

E-04 is complete. The next bounded unit is a separate E-05 autocomplete
source/index/single-flight ownership Contract. E-04e changes no production,
analyzer baseline, public surface, or runtime behavior and does not authorize E-09
cleanup implementation, D-14 retirement, release, or Registry work.

## Stop conditions

Stop the owning Move if it would require a generic executor/client port, a
feature-to-runtime/API/bootstrap/root back-reference, an import-time optional
dependency, loss of a supported identity/dynamic seam, changed cache/provider/error
or admission behavior, or an unproven client cleanup call.

The direct evidence and existing ADRs select one resource partition, so E-04a does
not trigger additional PRO review.
