# Python Runtime State Ownership Inventory

## Status and authority

This is the E-01 Contract owned by
[Issue #187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187).
The executable source of truth is
`tests/fixtures/python_runtime_state_ownership.v1.json`; the direct contract test
rejects stale symbols, missing evidence, analyzer owner candidates without an owner,
and mutable globals without an explicit disposition.

E-01 records the current state. It does not move state, add lifecycle behavior, or
claim that Phase E is complete.

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
| `aio-first-pass-cache` | canonical AiO cache module, process lifetime with count/byte/TTL bounds | one `RLock`; explicit clear plus test-only metric/config reset | E-08 |
| `api-file-io-limiters` | canonical API file-I/O module, weak per-event-loop limiter | registry `Lock`; weak expiry, no explicit close | E-09 |
| `autocomplete-dataset-cache` | canonical dataset snapshot and Future single-flight maps | one `Lock`; test-only clear | E-05 |
| `autocomplete-index-locks` | canonical index per-path lock registry | guard plus per-path locks; no clear | E-05 |
| `autocomplete-index-root` | import-resolved user-data index path | immutable after import; test patch coupled to index fallback/publication | E-05 |
| `atomic-json-path-locks` | filesystem atomic JSON per-path lock registry | guard plus per-path `RLock`; no clear | E-03 |
| `bootstrap-initialize-state` | bootstrap default runtime and wildcard completion state | initialize `Lock`; private-global test reset, no shutdown | E-09 |
| `filesystem-runtime-paths` | import-resolved package/user-data paths projected into the default RuntimeConfig | immutable after import; bootstrap composition does not re-resolve | E-02c complete |
| `package-bootstrap-effect` | root import invokes bootstrap route/directory initialization | bootstrap `Lock`; retry behavior, no package shutdown | E-09 |
| `profile-directory-mutation-coordinator` | canonical process coordinator with weak per-directory locks | guard plus per-directory `RLock`; weak expiry | E-03 |
| prompt warning-dedupe entries | two canonical Prompt feature modules, process lifetime | unprotected sets; direct-test clear only | E-09 |
| `prompt-knowledge-path` | canonical filesystem package path re-exported for ANIMA root compatibility | immutable after import | E-02d complete |
| `root-route-registration` | injected router registrar called by bootstrap | serialized refresh; idempotent marker, no deregistration | E-09 |
| `root-translation-route-worker` | root compatibility runtime owns lazy single-thread executor | internal `RLock`; idempotent `atexit` shutdown only | E-04 |
| `runtime-services` | identity-installed process runtime with Comfy and seed capabilities | bootstrap-serialized install; private-global test reset, no close | E-09 |
| `translation-default-service` | canonical default cache/single-flight service | cache and flight `RLock`s; cache clear exists, no process reset | E-04 |
| `translation-provider-registry` | canonical lazy provider-client registry | one `RLock`; test patch only, no provider close | E-04 |
| `wildcard-snapshot-cache` | root verified-snapshot LRU and build single-flight | one `Condition`; no owner reset/close | E-06 |

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

## E-02 audit result and next bounded unit

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
E-02 is complete; the next bounded unit is an E-03 Contract. E-03 through E-09
feature/lifecycle Moves remain separate and use this fixture's target phases and
cleanup gaps.
