# E-10 Isolated Runtime Test Fixture Contract

## Scope and authority

E-10 started from `dev@5e99b702731b896ce6a424b7315e98eaff21133f` after
the production-free E-09c lifecycle completion audit. E-10b merged as PR #560 at
`87a1689f7c5d6452888e7bb8a8f92856d3f2f76f`; E-10c records the completion
audit. Issue #187 owns the decision ledger. The executable source is
`tests/fixtures/python_runtime_test_isolation_contract.v1.json`, checked by
`tests/test_python_runtime_test_isolation_contract.py`.

E-10 changes test ownership, not the production lifecycle. The E-09 terminal
bootstrap contract remains authoritative: shutdown is process-terminal, no hot
shutdown-to-reinitialize contract exists, and production exposes no reset API.

## Completion inventory

The repository has zero test calls to `importlib.reload()` or `reload()`. E-10b moved
all seven lifecycle-global mutations from the five former test owners into
`tests/runtime_test_support.py`. The helper is now the only mutation owner and the
direct-private-mutation inventory outside it is empty.

Direct tests may continue to read private lifecycle state when the assertion proves
identity, terminal state, or rollback behavior. E-10 moves reset and mutation
ownership; it does not hide the state under test.

## One test-only owner

E-10b adds `tests/runtime_test_support.py` as the only test-only owner allowed to
mutate the seven lifecycle globals listed by the executable fixture. The helper is
not shipped and adds no production import or export.

It provides three distinct modes:

1. **Constructed runtime:** build independent `RuntimeServices` values from injected
   paths and fake services without installing a global. These values are safe to use
   concurrently because they share no runtime identity.
2. **Installed runtime:** under one test-support lock, temporarily install a runtime
   for adapter tests and restore the exact prior runtime identity in `finally`.
3. **Bootstrap lifecycle:** under the same lock, snapshot the bootstrap/runtime/
   translation-facade identities and scalar lifecycle state, suppress real atexit
   registration, and restore every prior value in `finally`.

Process-global installed and bootstrap fixtures are serialized for their entire
lifetime. E-10 does not claim that two global installations can safely overlap.
Parallel tests use independently constructed runtimes or separate processes.

## Compatibility and side-effect boundary

The helper must preserve:

- `RuntimeServices`, `install_runtime()`, `get_runtime()`, private expected-identity
  detach, bootstrap `initialize()`/`shutdown()`, and all current public surfaces;
- terminal shutdown, repeated initialize, route refresh, wildcard retry, cleanup
  order, and partial-startup rollback behavior from E-09;
- Comfy provider fake behavior and existing root/helper identities; and
- current test order, exceptions, callback counts, and assertions.

The helper restores prior identities after success or failure, registers no real
atexit hook, and leaves no route, host, file-I/O, thread, or executor side effect.
It must not add production `reset_runtime`, ContextVar runtime selection, hot
reinitialize behavior, route deregistration/rollback, provider close, or a public
export.

## Completed queue

1. **E-10a Contract — complete:** froze the inventory, the one test-only owner,
   isolation modes, migration files, validation, and stop conditions. Production
   changes: zero.
2. **E-10b Move — complete:** added the helper and migrated the five direct mutation
   owners in one cohesive test-only rollback boundary.
3. **E-10c Contract — complete:** records reload sites `[]`, direct private mutation
   outside the helper `[]`, retained direct lifecycle assertions, and the Phase E
   completion audit without production changes.

E-10b is one cohesive migration because all five former sites manipulate the same
process-global runtime identity. Splitting the helper from its consumers would leave
two competing reset owners. E-10c closes Phase E. That completion does not itself
authorize D-14 implementation, release, or Registry work; those remain governed by
their existing roadmap gates.

## Validation and evidence reuse

E-10b passed the E-10 Contract/support tests, E-01/E-09 Contracts, direct bootstrap,
runtime, Comfy host, and translation owners, package/no-host import, current import
boundaries, analyzer, and `git diff --check`. Its official full on candidate
`6d1d65198385122bfdb6d31e0b0f1513b2714502` passed 1,431 Python tests and 120
frontend files exactly once.

E-10c runs changed-file JSON/Python syntax, the E-10/E-01/E-09 Contracts,
package/no-host import, current import boundaries, analyzer, maintained-document
links, and `git diff --check`, then runs official full once on its exact final
candidate SHA. E-10b and E-10c change no production, import closure, archive,
metadata, or host-visible behavior, so package/live evidence is reused.

## Stop conditions

Stop if E-10b requires a production reset API, hot shutdown-to-reinitialize,
ContextVar runtime behavior, overlapping global installs, safe route rollback,
provider/client close, public-surface change, or a feature behavior change. Record
the smallest new behavior Contract rather than broadening test infrastructure.
