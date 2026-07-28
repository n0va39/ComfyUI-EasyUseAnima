# E-09 Runtime Shutdown and Cleanup Contract

## Scope and authority

E-09a is a production-free Contract created from
`dev@4ad6bc947ba59db2df3cf5212ab07789757d7b96` after the completed E-08d
AiO ownership audit. The executable source is
`tests/fixtures/python_runtime_lifecycle_contract.v1.json`, checked by
`tests/test_python_runtime_lifecycle_contract.py`.

Issue #187 owns the Phase E decision ledger. The current source, direct owner tests,
and the separate Sol/max PRO review converge on one bounded sequence:

1. E-09a freezes the lifecycle Contract without production changes;
2. E-09b implements one cohesive `LIFECYCLE` rollback boundary; and
3. E-09c performs a production-free completion audit before E-10.

Multiple Move PRs and a broader roadmap redesign are rejected. Shutdown ordering,
partial-initialization rollback, and terminal process state are one shared concurrency
contract and are easier to review and roll back as one implementation.

## One lifecycle owner

`easyuse_anima.bootstrap` owns the production lifecycle. `initialize()` and the
canonical `shutdown()` added by E-09b share `_INITIALIZE_LOCK`. Bootstrap registers
its shutdown with `atexit` exactly once and owns the composed translation route
executor identity used by the root compatibility facade.

The lifecycle is terminal:

- `initialize(); initialize()` preserves the installed runtime identity, refreshes
  the current route table on every call, initializes the wildcard directory once,
  and retains the existing wildcard `OSError` retry behavior;
- `shutdown(); shutdown()` is safe and performs cleanup at most once; and
- `initialize()` after shutdown raises before route, wildcard, or host callbacks run.

E-09b exports only `easyuse_anima.bootstrap.shutdown` beside `initialize`. Root
`__all__`, the package entrypoint, runtime `__all__`, `install_runtime()` identity
rules, `get_runtime()` error behavior, node/API identities, and all route signatures
remain unchanged. The root package continues to invoke only `initialize()`; process
shutdown is delivered through the bootstrap-owned `atexit` registration.

## RuntimeServices close plan

`RuntimeServices.close()` delegates to a private once-only cleanup plan. Bootstrap
supplies the default plan while existing explicit/fake RuntimeServices construction
remains compatible. Shutdown first marks the bootstrap terminal and detaches only
globals that still hold the expected runtime identity. It then executes the plan in
this fixed reverse-composition order:

1. shut down translation route admission without waiting for a running worker;
2. clear the AiO first-pass cache;
3. clear completed wildcard snapshots;
4. invoke the autocomplete index store's idempotent no-op `close()`;
5. clear completed autocomplete dataset snapshots;
6. compare-and-restore the captured translation facade only if it still names the
   closing runtime service; and
7. close the runtime translation service cache.

Translation executor shutdown keeps its current semantics: new admission fails,
pending futures are cancelled, shutdown does not wait, and already-running work may
settle. AiO clear preserves enabled state and metrics. Wildcard and autocomplete
snapshot clears do not cancel active builds, Futures, or waiter settlement. The
autocomplete index locks remain retained. Translation flights self-remove after their
last user settles.

Seed reservations, Comfy provider, immutable config, and clock own no additional
close operation and expire with runtime references. The provider registry/client has
no supported close protocol, so E-09 must not invent one.

## Initialization rollback

Returning `False` from route registration remains nonterminal. A wildcard directory
`OSError` remains a warning-and-retry state and retains the installed runtime.

An unexpected route or wildcard exception rolls back only resources created or bound
by that initialization attempt:

- the attempt-created RuntimeServices value;
- the attempt-installed runtime identity;
- the attempt-published bootstrap runtime; and
- the attempt replacement of the translation facade.

Rollback uses expected-identity compare-and-restore operations, continues cleanup
after a cleanup failure, and preserves the original startup exception. It does not
attempt to undo directory effects, partially registered routes, pre-created
translation route executor state, or process-global feature cache owners. E-09 stops
instead of inventing safe route rollback or concurrent-request draining.

## Explicit retained no-op boundaries

### Route registration

Routes and their marker remain installed. ComfyUI exposes no reviewed safe route
deregistration contract, while current same-table idempotence, signature mismatch,
and new-table refresh behavior are already direct-tested. Shutdown therefore performs
no route removal and does not clear the marker.

### API file-I/O limiters

`easyuse_anima.api.file_io` retains its module-owned `WeakKeyDictionary` of weak
semaphore references. Weak loop keys and weak values self-expire, and active requests
retain their limiter until the real `asyncio.to_thread` work settles. Shutdown must
not clear the registry, cancel work, release slots, or add the limiter to
RuntimeServices.

### Warning dedupe

The callerless duplicate
`easyuse_anima.prompt.artist_mix._SPECTRUM_ANIMA_MOD_GUIDANCE_OLD_SIGNATURE_WARNED`
set is removed in E-09b. The canonical set in
`easyuse_anima.prompt.conditioning` remains process-lifetime, keeps its existing
benign duplicate-warning race, and is not cleared or locked by shutdown.

### Provider/client

The translation provider registry remains lazy and process-owned. No supported
provider/client close or reset operation has been proven. E-09 records that no-op
instead of adding a generic client lifecycle.

## Bounded implementation queue

1. **E-09a Contract:** freeze owner/disposition, cleanup order, rollback, no-op,
   compatibility, validation, and stop conditions. Production changes: zero.
2. **E-09b LIFECYCLE:** implement the complete fixed contract in
   `easyuse_anima/runtime.py`, `easyuse_anima/bootstrap.py`,
   `easyuse_anima/api/routes/translation.py`,
   `easyuse_anima/translation/service.py`,
   `easyuse_anima/prompt/artist_mix.py`, and `__init__.py`, with only the direct
   tests/fixtures/baseline required by actual-code gates.
3. **E-09c Contract:** reconcile E-01, lifecycle, cleanup, import/package safety, and
   `ambiguous_state_owners=[]` without production changes.

E-10 remains blocked until E-09c merges. D-14 retirement, release, and Registry work
remain blocked by the active roadmap.

## Validation and evidence reuse

E-09a edit-loop evidence is limited to changed-file JSON/Python syntax, the new
Contract test, the existing E-01/E-04/E-05/E-06/E-08 contracts, package/no-host
import, current import boundaries, analyzer, maintained-document links, and
`git diff --check`.

Run the official full profile once on the exact E-09a final candidate SHA. E-09a
changes no production, import closure, archive, metadata, or host-visible behavior,
so reuse E-08c package/live evidence unless a focused promotion gate proves material
drift.

E-09b runs its direct lifecycle/concurrency/rollback tests, official full once,
`comfy node validate`, actual pack/archive inspection, and one isolated ComfyUI
import/reload/shutdown smoke. A Legacy/Node 2.0 canvas matrix is not triggered by a
backend-only process lifecycle. E-09c reuses unchanged E-09b package/live evidence.

## Stop conditions

Stop E-09b if implementation requires a safe route deregistration or rollback,
immediate active-request draining, clearing/cancelling/releasing file-I/O limiters,
provider/client close, hot shutdown-to-reinitialize, root public-surface change, or
observed ComfyUI hot-unload behavior absent from the fixed Contract. Record the
smallest new behavior Contract rather than broadening E-09.
