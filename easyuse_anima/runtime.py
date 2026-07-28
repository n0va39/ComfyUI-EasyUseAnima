"""Process-runtime installation and access contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .aio.ports import AIOFirstPassCachePort
from .autocomplete.ports import AutocompletePort
from .infrastructure.comfy.provider import ComfyHostProvider
from .seed.reservation import SeedReservationService
from .translation.ports import PromptTranslationPort
from .wildcard.ports import WildcardSnapshotPort


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Process paths resolved by a bootstrap-owned config loader."""

    package_root: Path
    package_data_dir: Path
    user_data_dir: Path


class Clock(Protocol):
    """Monotonic time source for process-owned caches and deadlines."""

    def monotonic(self) -> float: ...


class RuntimeResource(Protocol):
    """Process-owned resource whose close operation must be idempotent."""

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class RuntimeServices:
    """Process-lifetime services currently ready for composition."""

    comfy: ComfyHostProvider
    seed_reservations: SeedReservationService
    config: RuntimeConfig
    clock: Clock
    translation: PromptTranslationPort
    autocomplete: AutocompletePort
    wildcard_snapshots: WildcardSnapshotPort
    aio_first_pass_cache: AIOFirstPassCachePort


_RUNTIME_SERVICES: RuntimeServices | None = None


def install_runtime(runtime: RuntimeServices) -> RuntimeServices:
    """Install the process runtime, allowing only an identical repeat."""

    global _RUNTIME_SERVICES

    installed = _RUNTIME_SERVICES
    if installed is None:
        _RUNTIME_SERVICES = runtime
        return runtime
    if installed is runtime:
        return installed
    raise RuntimeError(
        "[EasyUseAnima] A different RuntimeServices instance is already installed."
    )


def get_runtime() -> RuntimeServices:
    """Return the installed process runtime."""

    runtime = _RUNTIME_SERVICES
    if runtime is None:
        raise RuntimeError("[EasyUseAnima] RuntimeServices has not been installed.")
    return runtime


__all__ = (
    "Clock",
    "RuntimeConfig",
    "RuntimeResource",
    "RuntimeServices",
    "get_runtime",
    "install_runtime",
)
