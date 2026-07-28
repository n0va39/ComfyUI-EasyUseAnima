"""Test-only Comfy host providers for E-07 wiring coverage."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import DEFAULT, Mock, patch


class FakeSeedReservationService:
    def reserve(self, request):
        raise AssertionError(f"unexpected seed reservation: {request!r}")

    def settle(self, reservation_id, settlement):
        raise AssertionError(
            f"unexpected seed settlement: {reservation_id!r} {settlement!r}"
        )


class FakeClock:
    def monotonic(self) -> float:
        return 0.0


class FakeComfyHostProvider:
    def __init__(
        self,
        *,
        max_resolution: int = 16384,
        node_classes: dict[str, object] | None = None,
        mapping_classes: dict[str, object] | None = None,
        loaded_classes: dict[str, object] | None = None,
    ) -> None:
        self.max_resolution_value = max_resolution
        self.node_classes = dict(node_classes or {})
        self.mapping_classes = dict(mapping_classes or {})
        self.loaded_classes = dict(loaded_classes or {})

    def max_resolution(self) -> int:
        return self.max_resolution_value

    def find_node_class(self, node_id: str):
        return self.node_classes.get(node_id)

    def find_node_mapping_class(self, node_id: str):
        return self.mapping_classes.get(node_id)

    def find_loaded_node_class(self, node_id: str):
        return self.loaded_classes.get(node_id)


class _LayeredFakeComfyHostProvider:
    def __init__(self, base, symbol: str, replacement) -> None:
        self._base = base
        self._symbol = symbol
        self._replacement = replacement

    def max_resolution(self) -> int:
        if self._symbol == "_comfy_max_resolution":
            return self._replacement()
        return self._base.max_resolution()

    def find_node_class(self, node_id: str):
        if self._symbol in {
            "_find_comfy_node_class",
            "_require_custom_node_class",
            "_require_any_custom_node_class",
        }:
            return self._replacement(node_id)
        if (
            self._symbol == "_encode_with_comfy_clip"
            and node_id == "CLIPTextEncode"
        ):
            replacement = self._replacement

            class ClipTextEncode:
                def encode(self, clip, text):
                    return (replacement(clip, text),)

            return ClipTextEncode
        return self._base.find_node_class(node_id)

    def find_node_mapping_class(self, node_id: str):
        if self._symbol == "_find_comfy_node_mapping_class":
            return self._replacement(node_id)
        return self._base.find_node_mapping_class(node_id)

    def find_loaded_node_class(self, node_id: str):
        if self._symbol == "_find_loaded_node_class":
            return self._replacement(node_id)
        return self._base.find_loaded_node_class(node_id)


def _runtime_module_for(root_module):
    package = root_module.__package__
    module_name = (
        f"{package}.easyuse_anima.runtime"
        if package
        else "easyuse_anima.runtime"
    )
    runtime_module = sys.modules.get(module_name)
    if runtime_module is None:
        raise AssertionError(f"Runtime module is not loaded: {module_name}")
    return runtime_module


def _runtime_support(runtime_module):
    installed = runtime_module._RUNTIME_SERVICES
    if installed is not None:
        return installed.config, installed.clock
    return (
        runtime_module.RuntimeConfig(
            package_root=Path("package-root"),
            package_data_dir=Path("package-data"),
            user_data_dir=Path("user-data"),
        ),
        FakeClock(),
    )


@contextmanager
def use_fake_comfy_host(root_module, provider):
    runtime_module = _runtime_module_for(root_module)
    config, clock = _runtime_support(runtime_module)
    runtime = runtime_module.RuntimeServices(
        comfy=provider,
        seed_reservations=FakeSeedReservationService(),
        config=config,
        clock=clock,
    )
    with patch.object(runtime_module, "_RUNTIME_SERVICES", runtime):
        yield provider


@contextmanager
def patch_comfy_helper(
    root_module,
    symbol: str,
    new=DEFAULT,
    **mock_kwargs,
):
    """Replace an E-07 root-test seam through a layered fake provider."""

    if new is DEFAULT:
        replacement = Mock(**mock_kwargs)
    else:
        if mock_kwargs:
            raise TypeError("mock options are invalid when an explicit replacement is used")
        replacement = new

    runtime_module = _runtime_module_for(root_module)
    installed = runtime_module._RUNTIME_SERVICES
    base = (
        installed.comfy
        if installed is not None
        else FakeComfyHostProvider()
    )
    provider = _LayeredFakeComfyHostProvider(base, symbol, replacement)
    config, clock = _runtime_support(runtime_module)
    runtime = runtime_module.RuntimeServices(
        comfy=provider,
        seed_reservations=FakeSeedReservationService(),
        config=config,
        clock=clock,
    )
    with patch.object(runtime_module, "_RUNTIME_SERVICES", runtime):
        yield replacement
