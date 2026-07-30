"""Small helpers for isolated API-module tests."""

from __future__ import annotations

import sys
import importlib
import logging
import uuid
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


@contextmanager
def replace_sys_modules(
    replacements: Mapping[str, ModuleType],
) -> Generator[None, None, None]:
    """Replace exact modules without rolling back unrelated imports."""

    missing = object()
    previous = {
        name: sys.modules.get(name, missing)
        for name in replacements
    }
    sys.modules.update(replacements)
    try:
        yield
    finally:
        for name, module in previous.items():
            if module is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


@dataclass(frozen=True, slots=True)
class CanonicalApiTestContext:
    application: Any
    bootstrap: ModuleType
    router: ModuleType
    requests: ModuleType
    responses: ModuleType
    file_io: ModuleType
    runtime: ModuleType
    aio_profiles: ModuleType
    lora_profiles: ModuleType
    profile_contract: ModuleType
    profile_mutation: ModuleType
    profile_repository: ModuleType
    settings_repository: ModuleType
    settings_service: ModuleType
    translation_contracts: ModuleType
    translation_service: ModuleType
    translation_routes: ModuleType
    lora_preview_routes: ModuleType
    wildcard_service: ModuleType
    wildcard_sources: ModuleType
    autocomplete_dataset: ModuleType
    autocomplete_search: ModuleType
    autocomplete_classification: ModuleType
    torch_compile_diagnostics: ModuleType
    torch_compile_recommendation: ModuleType


def load_canonical_api_application(
    *,
    root: Path,
    server: ModuleType,
    aiohttp: ModuleType,
    register: bool,
) -> CanonicalApiTestContext:
    """Compose one isolated canonical API application without a root facade."""

    package_name = f"easyuse_anima_api_contract_test_package_{uuid.uuid4().hex}"
    package = ModuleType(package_name)
    package.__path__ = [str(root)]
    sys.modules[package_name] = package
    prefix = f"{package_name}.easyuse_anima"

    with replace_sys_modules({"server": server, "aiohttp": aiohttp}):
        bootstrap = importlib.import_module(f"{prefix}.bootstrap")
        application = bootstrap._compose_api_application(
            logger=logging.getLogger(f"{prefix}.api"),
            publish_routes=lambda _target: None,
        )
        if register:
            application.register_routes()

    def owner(name: str) -> ModuleType:
        return sys.modules[f"{prefix}.{name}"]

    return CanonicalApiTestContext(
        application=application,
        bootstrap=bootstrap,
        router=owner("api.router"),
        requests=owner("api.requests"),
        responses=owner("api.responses"),
        file_io=owner("api.file_io"),
        runtime=owner("runtime"),
        aio_profiles=owner("profiles.aio"),
        lora_profiles=owner("profiles.lora"),
        profile_contract=owner("profiles.contract"),
        profile_mutation=owner("profiles.mutation"),
        profile_repository=owner("profiles.repository"),
        settings_repository=owner("settings.repository"),
        settings_service=owner("settings.service"),
        translation_contracts=owner("translation.contracts"),
        translation_service=owner("translation.service"),
        translation_routes=owner("api.routes.translation"),
        lora_preview_routes=owner("api.routes.lora_preview"),
        wildcard_service=owner("wildcard.service"),
        wildcard_sources=owner("wildcard.sources"),
        autocomplete_dataset=owner("autocomplete.dataset"),
        autocomplete_search=owner("autocomplete.search"),
        autocomplete_classification=owner("autocomplete.classification"),
        torch_compile_diagnostics=owner("aio.torch_compile_diagnostics"),
        torch_compile_recommendation=owner("aio.torch_compile_recommendation"),
    )


__all__ = (
    "CanonicalApiTestContext",
    "load_canonical_api_application",
    "replace_sys_modules",
)
