# E-03 Repository and Filesystem Contract

## Scope

E-03a is a production-free Contract at
`dev@204e74ab5897e1dc1f769067f9520ecee6803803`. It inventories the current
settings, LoRA profile, AiO profile, atomic JSON, and profile mutation boundaries
before any factory or repository Move.

The executable source of this inventory is
`tests/fixtures/python_repository_filesystem_contract.v1.json`, checked by
`tests/test_python_repository_filesystem_contract.py`. Existing storage, settings,
profile contract, LoRA, and AiO tests remain the behavior authorities.

## Current owners

### Atomic JSON mechanics

`easyuse_anima.infrastructure.filesystem.atomic_json.AtomicJsonStore` accepts a
primary path and optional same-directory backup. It expands and resolves the path,
then uses the canonical module's process registry to share one `RLock` among every
store for the same normalized primary path.

The store owns JSON encoding, durable temporary files, fsync, backup recovery,
atomic publication, delete, and same-directory replacement. Multi-path replacement
acquires normalized path keys in sorted order and releases them in reverse order.
The process registry has no explicit cleanup today.

This owner remains shared by direct `AtomicJsonStore(path)` callers and stores created
through `create_atomic_json_store(path, backup=...)`. The E-03b factory delegates to
the canonical constructor and creates no lock registry of its own.

### Profile transaction coordination

`easyuse_anima.profiles.mutation.PROFILE_MUTATION_COORDINATOR` owns a guarded weak
registry of per-directory `RLock` objects. LoRA and AiO mutations acquire the
directory lock before discovery, identity-before-revision verification, and
publication. Atomic store path locks are acquired inside that directory transaction.

The coordinator is feature transaction policy, not generic filesystem mechanics.
It therefore remains a separate shared dependency and is not absorbed into the
filesystem factory.

## Path and dependency inputs

| Lane | Current path inputs | Other dynamic inputs |
| --- | --- | --- |
| settings | `SETTINGS_FILE`, `LONG_TEXT_SETTINGS_FILE` from `USER_DATA_DIR` | per-call Comfy `folder_paths.get_user_directory()` overlay discovery |
| shared profile helpers | caller-supplied profile file | profile kind, filename, document |
| LoRA profile | `LORA_PROFILE_DIR`, optional `profile_dir` helper arguments | per-call Comfy LoRA list/full-path lookup for repair |
| AiO profile | `AIO_PROFILE_DIR`, optional `profile_dir` helper arguments | none |

Settings and profile repositories receive explicit paths and a narrow store factory.
The private profile repository value additionally receives the shared directory
coordinator. The LoRA and AiO builders resolve their current module directory, factory,
and coordinator symbols on every call. No feature repository receives the complete
`RuntimeServices` object.

Dynamic Comfy `folder_paths` lookup stays late-bound in the owning feature. Moving it
into a filesystem factory would mix host discovery with persistence mechanics and
would break the current optional-host behavior.

## Lock and revision invariants

The required acquisition order is:

1. profile mutation operations acquire the profile directory `RLock`;
2. they discover source and target files and verify identity before revision;
3. they acquire one or more atomic store path `RLock` objects;
4. they publish, restore, or delete while the directory transaction remains held.

Settings use only atomic path locks. `save_setting()` deliberately holds the settings
path `RLock` while calling `get_settings()`, which can re-enter the same normalized
path lock. The lock therefore remains reentrant.

Repository construction does not own profile schema meaning. The following stay with
the existing profile contract and feature owners:

- server-owned profile IDs and legacy identity projection;
- revision one on create and increment on normal overwrite;
- identity mismatch before revision mismatch;
- source and target preconditions for rename;
- rename revision preservation;
- overwrite, missing, invalid-data, backup, rollback, and response error policy.

## Compatibility and monkeypatch seams

Current direct tests patch settings/profile path constants on their canonical
modules. API route tests patch root operation aliases after route construction, and
the callbacks resolve those aliases dynamically. The root also exposes identity
aliases for the profile coordinator, profile directories, and profile operations.

No E-03 Move may capture a default repository at import in a way that bypasses these
seams. A future module-level compatibility wrapper may construct or resolve an
explicit repository from the current canonical path symbols at call time. Removing a
seam requires separate consumer evidence and the compatibility-shim process.

`AtomicJsonStore` itself remains the canonical/root identity-compatible class with
its current constructor and methods.

## Factory decision

The E-03b filesystem factory is the stateless
`create_atomic_json_store(path, *, backup=True)` seam:

```text
explicit path + backup policy -> canonical AtomicJsonStore
```

It owns no cache, lock registry, host lookup, schema, error translation, or lifecycle.
The canonical atomic JSON module continues to own process path locks. This is the
smallest boundary that permits repository construction without weakening direct
constructor compatibility or introducing a dependency-injection framework.

## Bounded Move queue

1. **E-03b Move — filesystem factory — complete:** the stateless constructor seam
   delegates to `AtomicJsonStore`; direct and factory-created stores share the
   canonical path lock and backup policy.
2. **E-03c Move — settings repository — complete:** a private per-call repository
   value now binds the current settings paths to the canonical store factory behind
   the existing functions and monkeypatch seams.
3. **E-03d Move — profile repositories — complete:** a shared private per-call value
   binds each current LoRA/AiO directory to the canonical store factory and shared
   coordinator behind the existing canonical functions and root aliases.
4. **E-03e Contract — completion audit — READY:** reconcile E-01 ownership targets and prove
   no repository/filesystem state remains ambiguously owned before E-04.

Each Move is a separate rollback boundary. A Move may be split further when direct
source review proves that preserving AiO rename/delete transactions would otherwise
mix behavior with mechanical construction.

## Preserved and forbidden

E-03a changes no production code, analyzer, existing feature test, package surface,
bootstrap, RuntimeServices, persistence, schema, error, lock, response, or lifecycle
behavior. Package/no-host and live evidence from the preceding runtime work remains
valid.

E-03d changes only private profile repository construction and its direct contract
evidence. It does not authorize the E-03e audit, E-04 or later work, root alias
retirement, D-14 retirement, release, or Registry actions.

The direct evidence leaves one owner for each boundary, so no material PRO review is
required.
