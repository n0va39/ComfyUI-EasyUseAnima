# Python Runtime Base Contract

## Status and authority

This document is the E-02b Contract owned by
[Issue #187](https://github.com/n0va39/ComfyUI-EasyUseAnima/issues/187).
It follows the versioned
[E-01 state inventory](python-runtime-state-inventory.md) and the completed
E-02a/E-07 Comfy provider bridge.

E-02b adds only canonical types. It does not change the installed
`RuntimeServices` identity, bootstrap wiring, path discovery, feature owners, or
shutdown behavior.

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
- the existing `RuntimeServices(comfy, seed_reservations)` constructor remains
  unchanged until a separate composition Move.

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

- `RuntimeServices` remains frozen, slotted, identity-installed, and conflict-safe.
- `install_runtime` and `get_runtime` behavior and error text remain unchanged.
- Bootstrap still creates only the current Comfy and seed services and preserves
  route refresh, wildcard retry, and repeated initialization.
- Runtime import remains safe without ComfyUI host modules.
- No feature cache, provider, client, executor, repository, or monkeypatch seam moves.
- No root or bootstrap public export is added.

## Next bounded unit

E-02c is a separate Move for a bootstrap-owned config loader, a concrete system
clock, and default runtime wiring. It must preserve the current `folder_paths`
fallback, standalone package behavior, RuntimeServices identity, and initialize
ordering. Feature owner and shutdown migrations remain separate.
