"""Process-runtime installation and access contract."""

from __future__ import annotations

from dataclasses import dataclass

from .infrastructure.comfy.provider import ComfyHostProvider
from .seed.reservation import SeedReservationService


@dataclass(frozen=True, slots=True)
class RuntimeServices:
    """Process-lifetime services currently ready for composition."""

    comfy: ComfyHostProvider
    seed_reservations: SeedReservationService


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


__all__ = ("RuntimeServices", "get_runtime", "install_runtime")
