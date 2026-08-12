import sys

from .easyuse_anima.bootstrap import _initialize_package
from .easyuse_anima.registration import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
)

_initialize_package()


def _publish_canonical_backend_aliases():
    """Expose one runtime-owned package identity to sibling custom nodes."""

    package_prefix = f"{__name__}.easyuse_anima"
    package_module = sys.modules.get(package_prefix)
    existing_package = sys.modules.get("easyuse_anima")
    if existing_package is not None:
        if existing_package is package_module:
            return
        raise RuntimeError("Conflicting canonical EasyUse Anima backend package")
    aliases = sorted(
        (
            ("easyuse_anima" + loaded_name[len(package_prefix):], module)
            for loaded_name, module in tuple(sys.modules.items())
            if loaded_name == package_prefix
            or loaded_name.startswith(f"{package_prefix}.")
        ),
        key=lambda item: (item[0].count("."), item[0]),
    )
    if package_module is None or not aliases or aliases[0][0] != "easyuse_anima":
        raise RuntimeError("EasyUse Anima canonical backend package was not loaded")
    for canonical_name, module in aliases:
        existing = sys.modules.get(canonical_name)
        if existing is not None and existing is not module:
            raise RuntimeError(
                f"Conflicting canonical EasyUse Anima module: {canonical_name}"
            )
        sys.modules[canonical_name] = module


_publish_canonical_backend_aliases()

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
