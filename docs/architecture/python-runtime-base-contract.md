# Python Runtime Base Contract

## Status and authority

This document is the E-02b Contract owned by
[Issue #187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187).
It follows the versioned
[E-01 state inventory](python-runtime-state-inventory.md) and the completed
E-02a/E-07 Comfy provider bridge.

E-02b added only canonical types. E-02c composes the config and clock into the
installed `RuntimeServices` while preserving its identity, path discovery behavior,
feature owners, and shutdown behavior.

## Locked canonical types

`easyuse_anima.runtime` owns:

```python
@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    package_root: Path
    package_data_dir: Path
    user_data_dir: Path

class Clock(Protocol):
    def monotonic(self) -> float: ...

class RuntimeResource(Protocol):
    def close(self) -> None: ...
```

The contract means:

- bootstrap will resolve the three paths once and then construct `RuntimeConfig`;
- constructing `RuntimeConfig` performs no `.resolve()`, host import, directory
  creation, environment read, or other I/O;
- feature caches receive only `Clock`, not the complete runtime;
- a process-owned resource implements an idempotent `close()`; concrete creation,
  reverse close ordering, and partial-failure cleanup remain E-09 work; and
- E-02c may add the base contracts to `RuntimeServices` only at the composition
  boundary; feature consumers still receive narrow protocols rather than the complete
  runtime.

## E-02c composition

`RuntimeServices` now requires `config: RuntimeConfig` and `clock: Clock` in addition
to the existing Comfy and seed services. The default runtime supplies them exactly
once during its first serialized bootstrap initialization:

- the private bootstrap config loader reads the existing `PACKAGE_ROOT`,
  `PACKAGE_DATA_DIR`, and `USER_DATA_DIR` objects from the canonical path module;
- it does not duplicate `.resolve()`, `folder_paths` probing, fallback policy,
  directory creation, or other I/O;
- the private system clock delegates each call to `time.monotonic()`; and
- repeated initialize calls reinstall the same runtime identity, refresh routes, and
  preserve wildcard once/retry behavior.

`paths.py`, root storage aliases, and every settings/profile/wildcard/autocomplete
path consumer remain unchanged. Their later feature-owner migrations are not part of
E-02c.

## Why executor and client remain feature-owned

There is no evidence for one useful generic executor or client port:

- `PromptTranslationRouteExecutor` owns single admission, busy/cancelled/timeout
  errors, lazy thread creation, and in-flight settlement;
- API file I/O owns a weak per-event-loop semaphore and `asyncio.to_thread`;
- Google translation owns a lazy reusable optional client under a provider lock;
- NAIA currently performs one `requests.post` per call with its own host and timeout
  policy.

Collapsing these shapes in E-02b would erase feature semantics and create an unused
abstraction. E-02b therefore shares only `Clock` and the lifecycle `close()` shape.
E-04 owns translation executor/provider/client ports; other features define a port
only when a real consumer requires it.

This is a boundary correction to the earlier “common clock/executor/client ports”
wording, not a Phase E sequence change. The evidence selects one conservative design,
so no PRO review is required.

## Preserved contracts

- `RuntimeServices` remains frozen, slotted, identity-installed, and conflict-safe;
  only its composition fields expand to include the required config and clock.
- `install_runtime` and `get_runtime` behavior and error text remain unchanged.
- Bootstrap creates the current Comfy and seed services plus the base config and
  clock, while preserving route refresh, wildcard retry, and repeated initialization.
- Runtime import remains safe without ComfyUI host modules.
- No feature cache, provider, client, executor, repository, or monkeypatch seam moves.
- No root or bootstrap public export is added.

## Next bounded unit

The
[`python-runtime-e02-completion-audit.md`](python-runtime-e02-completion-audit.md)
records one remaining bounded **E-02d** Move: replace the prompt knowledge module's
duplicate package-data resolution with the canonical filesystem Path object. The
autocomplete index root moves with E-05. E-03 remains unauthorized until E-02d
lands; feature owner and shutdown migrations remain separate.
