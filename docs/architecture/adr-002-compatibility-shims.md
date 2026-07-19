# ADR-002: Python Compatibility Shim Lifecycle

- Status: Accepted
- Decision date: 2026-07-19
- Owners: [Issue #188](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/188)
  with root moves in
  [Issue #186](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/186)
- Registry: [python-compatibility-shims.md](python-compatibility-shims.md)

## Context

The backend currently exposes implementation through root `nodes.py`,
`api.py`, `settings.py`, `storage.py`, `autocomplete_dataset.py`,
`wildcard_engine.py`, `prompt_translation.py`, and `anima_prompt/`. Some paths
are used internally, some are exercised by tests, and public node classes may
also be imported by consumers outside this repository.

Moving implementations to `easyuse_anima` without a lifecycle policy can
silently change class identity, break 0.5.2 workflows or API consumers, omit
files from the Registry archive, or leave permanent shims that regain business
logic.

## Decision

Every compatibility shim is an explicit, registered migration surface.

### Shim shape

- A shim directly re-exports a canonical object. It does not wrap, subclass,
  proxy, copy, or recreate that object.
- Supported symbols are named explicitly in imports and `__all__`; star imports
  are forbidden.
- A shim contains no feature behavior, persistence, migration, route
  implementation, filesystem initialization, client, cache, or lock.
- Internal production code imports only `easyuse_anima`. Root shims are for
  consumers at the migration boundary, never for internal convenience.
- Public identity tests use `Legacy is Canonical`, not only equivalent names or
  behavior.

### Minimum support window

Let release `N` be the first published Registry release that contains the
canonical target and its compatibility shim. The shim remains supported for
the whole of release `N`; removal is no earlier than a later release and only
after all removal gates pass.

This is a minimum, not an automatic deadline. Public node-class re-exports may
remain indefinitely when their maintenance cost is low. If telemetry or
consumer evidence is unavailable, ambiguous, or privacy-sensitive, the default
is to retain the shim.

The project does not add outbound telemetry merely to justify removal. Useful
evidence includes repository import analysis, public docs/examples, issue and
support reports, package/install smoke, and privacy-safe local warnings or logs
that already exist.

### Staged retirement

1. Introduce the canonical path and direct root re-export in a Move PR.
2. Migrate production imports, tests, and maintained docs/examples to the
   canonical path.
3. Publish and validate at least one release with both paths in the actual
   Registry archive.
4. Remove undocumented/private aliases first, each through its own reviewed
   change.
5. Decide each public re-export separately. Removal requires a breaking-change
   issue, compatibility impact, release note, and rollback plan.

Deprecation warnings are optional. An import-time warning that is noisy in
ComfyUI or affects package validation must not be added solely for this policy.

### Removal gates

A shim may be removed only when all applicable gates pass:

- its registry entry has an owner, canonical target, introduction release,
  known dependents, evidence, and proposed earliest release;
- at least one published release has contained both canonical and shim paths;
- internal production imports of the shim are zero;
- maintained tests/docs/examples use the canonical path except explicit
  compatibility tests;
- root/canonical object identity and public API snapshots have passed for the
  support window;
- 0.5.2 workflow, API, profile, and settings compatibility gates pass;
- `comfy node validate`, actual `comfy node pack`, and packed-archive import
  closure pass with required canonical modules and remaining shims;
- optional providers disabled at import time do not break the package;
- available consumer evidence supports removal; lack of evidence causes
  conservative retention; and
- a public removal has separate breaking-change approval and release notes.

No calendar date or version is promised before these conditions are satisfied.

## Consequences

Positive consequences:

- object identity and workflow mappings remain stable through moves;
- Registry packaging is treated as part of compatibility, not an afterthought;
- internal code converges on one import root instead of depending on shims;
- removal decisions are evidence-based and reversible; and
- unsupported private helpers can be retired before stable public classes.

Costs and constraints:

- the archive contains duplicate import entry paths during migration;
- every shim needs ownership and compatibility tests;
- public re-exports may live longer than the implementation move; and
- a missing consumer signal delays removal rather than accelerating it.

## Alternatives considered

### Remove root modules in the same PR as the move

Rejected because it combines a mechanical move with a breaking contract and
provides no release window for external consumers.

### Keep all root symbols forever

Rejected as a blanket rule because private/test-only aliases expand the public
surface and invite internal back references. Long-term support remains a valid
per-symbol decision.

### Use wrappers or subclasses for compatibility

Rejected because class identity, `__module__`, mappings, serialization, and
consumer type checks can change even when behavior looks equivalent.

### Remove on a preselected date

Rejected because releases, Registry evidence, and consumer adoption do not
follow a reliable calendar. Gates are safer than speculative dates.

## Reconsideration conditions

Review this policy if:

- the project publishes a formal external Python API with a defined semantic
  versioning policy;
- ComfyUI or the Registry introduces an authoritative alias/deprecation
  mechanism that preserves identity and archive behavior;
- privacy-safe, reliable consumer telemetry becomes available; or
- long-lived shims create a demonstrated security, startup, or packaging risk.

Any change requires a new ADR and an update to the shim registry.
