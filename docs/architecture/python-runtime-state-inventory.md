# Python Runtime State Ownership Inventory

## Status and authority

This is the E-01 Contract owned by
[Issue #187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187).
The executable source of truth is
`tests/fixtures/python_runtime_state_ownership.v1.json`; the direct contract test
rejects stale symbols, missing evidence, analyzer owner candidates without an owner,
and mutable globals without an explicit disposition.

E-01 records the current state. It did not move state or add lifecycle behavior; the
separate E-10c completion audit now confirms that every recorded Phase E owner has a
completed disposition.

## Method

The inventory combines:

1. `tools/analyze_python_backend.py` mutable-global and owner-candidate output;
2. direct review of cache, lock, Future, executor, provider, repository, capability,
   path-resolution, route-registration, and directory-initialization owners; and
3. current reset, close, synchronization, and test evidence.

The analyzer's `__all__` lists are excluded as export metadata. Every other detected
mutable global is partitioned exactly once:

- **runtime-owned**: mutated, populated, or identity-installed during process work;
- **declarative-only**: a Python mutable container used as an immutable table or
  public metadata surface.

Declarative-only does not grant mutation permission. It records why those containers
are not lifecycle resources and makes any newly introduced mutable global fail the
E-01 drift gate until classified.

## Runtime owners and migration targets

| Entry | Current owner and lifetime | Synchronization / cleanup today | Target |
| --- | --- | --- | --- |
| `aio-first-pass-cache` | one private default AiO cache store owns entries/order/enabled/generation/metrics/`RLock`; bootstrap installs that exact owner behind a narrow private runtime port | owner clear/disable invalidate entries and generation while preserving metrics; metric reset is separate | E-08 complete; E-08d audited |
| `api-file-io-limiters` | canonical API file-I/O module, weak per-event-loop limiter | registry `Lock`; weak expiry and no explicit close; E-09 retains this as a lifecycle no-op | E-09 complete; E-09c audited |
| `autocomplete-dataset-cache` | canonical dataset snapshot and Future single-flight owner, injected into the bootstrap-composed narrow service | one owner `Lock`; completed-snapshot clear only | E-05 complete; E-05e audited |
| `autocomplete-index-locks` | canonical index-store per-path lock owner, injected into the bootstrap-composed narrow service | guard plus retained per-path locks; idempotent no-op close | E-05 complete; E-05e audited |
| `autocomplete-index-root` | immutable user-data index root retained by the canonical index-store owner | isolated-store injection; no mutable raw root | E-05 complete; E-05e audited |
| `atomic-json-path-locks` | filesystem atomic JSON per-path lock registry shared by direct/factory stores | guard plus per-path `RLock`; no clear | E-03b complete |
| `bootstrap-initialize-state` | bootstrap default runtime, wildcard completion, executor, atexit, and terminal state | shared initialize/shutdown `Lock`; expected-identity detach and once-only cleanup | E-09 complete; E-09c audited |
| `filesystem-runtime-paths` | import-resolved package/user-data paths projected into the default RuntimeConfig | immutable after import; bootstrap composition does not re-resolve | E-02c complete |
| `native-civitai-lookup-cache` | native image metadata owns two bounded successful-result LRU caches for Civitai lookups | `functools.lru_cache`; transport and parse failures are not cached | native image output complete |
| `native-image-output-runtime` | native image output owns one process save lock | serializes output-name reservation and publication; no reset | native image output complete |
| `native-resource-hash-runtime` | native resource hashing owns a bounded process LRU and validated persistent cache under the ComfyUI user directory | persistent-cache `Lock`, atomic JSON replacement, 128-entry and 1 MiB bounds; no reset | native image metadata parity complete |
| `package-bootstrap-effect` | root import invokes bootstrap route/directory initialization | bootstrap `Lock`; retry behavior plus once-registered terminal `atexit` shutdown | E-09 complete; E-09c audited |
| `profile-directory-mutation-coordinator` | canonical process coordinator with weak per-directory locks | guard plus per-directory `RLock`; weak expiry | E-03d complete |
| prompt warning-dedupe entries | Conditioning owns the canonical process warning set; the callerless Artist Mix duplicate is removed | canonical set remains process-lifetime with its accepted benign race | E-09 complete; E-09c audited |
| `prompt-knowledge-path` | canonical filesystem package path re-exported for ANIMA root compatibility | immutable after import | E-02d complete |
| `root-route-registration` | injected router registrar called by bootstrap | serialized refresh, idempotent marker, and retained routes with no deregistration | E-09 complete; E-09c audited |
| `root-translation-route-worker` | bootstrap composes the lazy single-thread executor; root retains its compatibility reference | internal `RLock`; bootstrap cleanup plan closes admission first without waiting | E-04d owner; E-09 lifecycle audited |
| `runtime-services` | identity-installed process runtime with Comfy, seed, config/clock, and narrow translation/autocomplete/wildcard capabilities | bootstrap-serialized install/detach; private once-only reverse cleanup plan | E-09 complete; E-09c audited |
| `translation-default-service` | RuntimeServices-owned translation port, mirrored by the canonical call-time facade | cache and flight `RLock`s; compare-and-restore facade then idempotent service close | E-04c owner; E-09 lifecycle audited |
| `translation-provider-registry` | private process-owned lazy provider-client registry | one owned `RLock`; no provider close/reset | E-04b complete |
| `wildcard-snapshot-cache` | canonical private default snapshot-store owner, directly injected through the narrow runtime port | one owned `Condition`; completed-cache-only `clear()` preserves active builds | E-06 complete; E-06e audited |

The fixture contains exact symbols, tests, owner, lifetime, thread-safety, and
reset/close status. This table is a review index, not a second machine-readable
source.

## E-01 exit result

- All current analyzer owner candidates map to a runtime owner.
- All analyzer mutable globals other than `__all__` have exactly one runtime-owned or
  declarative-only disposition.
- Manual gaps cover RuntimeServices identity, bootstrap state, weak registries,
  Conditions, scalar cache state, provider/default-service instances, profile
  coordination, path resolution, root translation executor, and package/route
  initialization effects.
- The completed E-02a/E-07 Comfy provider bridge remains unchanged.
- No production Python, analyzer heuristic, public surface, cache policy, or
  lifecycle behavior changes in E-01.

## E-02 and E-03 result

E-02b is owned by
[`python-runtime-base-contract.md`](python-runtime-base-contract.md). It fixes
`RuntimeConfig`, `Clock`, and the idempotent `RuntimeResource.close()` shape. Direct
source evidence rejects a shared executor/client abstraction: those ports remain
feature-owned because their admission, cancellation, timeout, reuse, and transport
contracts differ.

E-02c adds required config/clock fields to the installed runtime. Its private
bootstrap loader projects the current canonical path objects, and its private system
clock delegates to `time.monotonic()`. It changes no path constant, fallback, feature
consumer, root surface, or shutdown behavior.

The
[`python-runtime-e02-completion-audit.md`](python-runtime-e02-completion-audit.md)
assigns the autocomplete index root to E-05 and records the filesystem paths as E-02c
complete. E-02d then replaces the duplicate prompt knowledge path resolution with the
canonical filesystem Path object while preserving the root compatibility alias.
E-02 is complete. The production-free
[`python-runtime-e03-repository-filesystem-contract.md`](python-runtime-e03-repository-filesystem-contract.md)
fixes the current settings/profile paths, atomic store construction, path and
directory lock ownership, revision/CAS boundary, dynamic dependencies, and
monkeypatch seams. E-03b adds a stateless factory that delegates to the canonical
store constructor and keeps the same process path-lock owner. E-03c adds a private
per-call settings repository value without capturing an import-time default. E-03d
adds the shared private per-call profile repository value while retaining the
canonical store factory and profile directory coordinator as the only mutable-state
owners. The E-03e cross-fixture audit reconciles both E-01 owner entries with those
E-03 owners and records zero ambiguous repository/filesystem state owners. The next
bounded unit is the separate E-04 translation provider/client/cache Contract.

## E-04 completion result

The production-free
[`python-runtime-e04-translation-contract.md`](python-runtime-e04-translation-contract.md)
keeps three translation-owned resource boundaries distinct:

- E-04b owns the provider factory/instance registry and lazy optional client;
- E-04c owns the process default service, bounded cache, and per-key single-flight;
- E-04d owns the API route executor construction and bootstrap lifecycle wiring.

No generic executor/client port is introduced. Bootstrap remains the target concrete
composition root, feature/domain code does not import the complete runtime, and the
current optional client protocol does not prove a close operation. E-04a therefore
records that cleanup gap instead of inventing a provider-client lifecycle call.

E-04b replaces the service module's separate factory map, instance map, and lock with
one private `_TranslationProviderRegistry`. The process default remains in the
canonical service module, and `get_translation_provider()` resolves that default at
call time. Provider/client laziness, reuse, optional imports, timeout and error
normalization remain unchanged.

E-04c adds a translation-owned narrow port to RuntimeServices. Bootstrap constructs
the process clock, bounded cache, and service together, then installs that exact
service identity behind the existing node/API facade. `PromptTranslationService`
implements the E-02 idempotent resource shape by clearing only its owned cache;
per-key flights still self-remove and provider/client cleanup remains separate.

E-04d moves the canonical route-runtime factory invocation, concrete executor/error
types, and `atexit` registration into one private bootstrap composition helper. Root
`api.py` retains the worker and three helper closures only as the existing dynamic
compatibility seams. Lazy executor creation, one-admission settlement, route
identity, and repeated bootstrap registration remain unchanged.

The production-free E-04e audit reconciles the three translation entries with the
E-04 owners and records zero ambiguous state. Route-executor and service cleanup
shapes are idempotent while whole-runtime ordering remains E-09; provider/client
close remains intentionally absent because no supported cleanup interface is proven.
E-04 is complete. E-05a fixes the autocomplete source/index/single-flight
ownership Contract, and E-05b and E-05c place snapshot/single-flight state and
index root/path-lock state
behind two distinct feature-private default owners. E-05d injects those exact
identities into one private bootstrap-composed autocomplete service and adds only
its narrow port to RuntimeServices. No duplicate cache, Future map, root, or lock
registry is introduced. Whole-runtime cleanup ordering remains assigned to E-09;
the production-free E-05e audit reconciles all three E-01 entries with those two
owners, records their explicit cleanup dispositions, preserves package/no-host and
root identity contracts, and records zero ambiguous autocomplete state. E-05 is
complete. The production-free
[`python-runtime-e06-wildcard-contract.md`](python-runtime-e06-wildcard-contract.md)
reconciles the wildcard entry with one verified-snapshot LRU/building-key/Condition
resource, preserves root dynamic seams and immutable D-12 materialization, selects a
private `_WildcardSnapshotStore` default owner, and records completed-cache-only
cleanup. E-06b moves the LRU, building-key set, Condition, and capacity behind that
exact default owner; root delegates with call-time source/build seams and retains no
raw duplicate lifecycle globals. E-06c moves the snapshot-backed service facade and
canonical internal callers to `easyuse_anima.wildcard` without a root back-reference.
E-06d injects the exact default owner through one narrow runtime port without a
wrapper or replacement identity. The production-free E-06e audit reconciles the
single E-01 entry with that owner, records completed-cache-only cleanup, preserves
feature import direction, package/no-host safety, and direct root identities, and
records zero ambiguous wildcard state. E-06 is complete. Because the E-02a/E-07a/
E-07b Comfy provider bridge was already completed through #323, it is not repeated.

The production-free E-08a Contract reconciles the one E-01 AiO first-pass cache
entry with its six mutable module globals, records the immutable entry, key/clone
helpers, and size/count/TTL limits as behavior or policy rather than state owners,
and selects one private `_AIOFirstPassCacheStore` instance named
`_DEFAULT_AIO_FIRST_PASS_CACHE` as the E-08b target. It preserves the seven direct
root aliases and the legacy runtime/stage injection path, and fixes the queue as
E-08a Contract, E-08b owner Move, E-08c narrow RuntimeServices/bootstrap
composition, and E-08d completion audit.

E-08b installs the selected private default owner. The former raw enabled,
generation, metrics, and lock globals are removed; mapping/order remain only as exact
aliases to the owner's objects so root identities and call-time replacement evidence
remain intact. Isolated stores share no collection, metric dictionary, generation,
enabled state, or lock.

E-08c adds the private `AIOFirstPassCachePort` with only `get` and `put`, installs
the exact `_DEFAULT_AIO_FIRST_PASS_CACHE` identity as
`RuntimeServices.aio_first_pass_cache`, and leaves the existing canonical key/get/put
to `FirstPassRuntime` to stage caller path unchanged. Feature code does not import
the runtime or bootstrap, repeated initialize reuses the same installed runtime, and
no root alias or public export changes.

The production-free E-08d audit reconciles the single E-01 entry with that exact
owner, records feature cleanup complete while whole-runtime ordering remains E-09,
preserves package/no-host safety, feature import direction, all seven root identities,
and the narrow runtime binding, and records zero ambiguous AiO cache state. E-08 is
complete. The next bounded unit is a separate E-09 runtime shutdown and cleanup
Contract.

## E-09 completion result

The production-free E-09a
[`python-runtime-e09-lifecycle-contract.md`](python-runtime-e09-lifecycle-contract.md)
selects bootstrap as the one serialized lifecycle owner and fixes a terminal,
idempotent shutdown plus bounded unexpected-initialization rollback. The reverse
cleanup plan closes translation route admission, then AiO, wildcard, autocomplete,
translation-facade, and translation-service resources using their existing feature
semantics. It does not clear weak API file-I/O limiters, deregister routes, close an
unproven provider/client, drain running work, or create a hot reinitialize contract.

E-09b implements that one cohesive lifecycle, and the production-free E-09c audit
reconciles the seven E-01 lifecycle targets as `E-09-complete`. The callerless Artist
Mix warning set is removed, the Conditioning set remains process-lifetime, all six
feature cleanup owners retain their existing semantics, package/import surfaces are
unchanged, and `ambiguous_state_owners=[]`. E-09 is complete.

## E-10 and Phase E completion result

The production-free E-10a Contract selected one test-only runtime fixture owner.
E-10b moved the five former mutation sites behind that owner while preserving direct
read-only lifecycle assertions and exact prior identity/state restoration. E-10c
records module reload sites `[]`, direct private lifecycle mutation outside
`tests/runtime_test_support.py` `[]`, and ambiguous test reset owners `[]`. Every E-01
target disposition ends in `-complete`; Phase E is complete without a production,
public-surface, package, import, or host-visible behavior change.
