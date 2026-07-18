from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any


PROFILE_ENVELOPE_VERSION = 2
PROFILE_KIND_AIO = "aio"
PROFILE_KIND_LORA = "lora"
PROFILE_ID_NAMESPACE = uuid.UUID("7d89dd90-6095-4dca-a80f-8e0b10868aaf")

_PROFILE_KINDS = frozenset({PROFILE_KIND_AIO, PROFILE_KIND_LORA})
_ENVELOPE_FIELDS = frozenset({"version", "profile_id", "revision", "name"})


class ProfileContractError(ValueError):
    """A stored profile does not satisfy the supported envelope taxonomy."""


def normalize_profile_filename_identity(name: str) -> str:
    """Return the Windows-compatible identity used by legacy profile files."""

    return str(name or "").rstrip(" .").casefold()


def legacy_profile_id(profile_kind: str, filename: str) -> str:
    """Derive the stable identity for a legacy profile without mutating it."""

    _validate_profile_kind(profile_kind)
    identity = normalize_profile_filename_identity(filename)
    return str(uuid.uuid5(PROFILE_ID_NAMESPACE, f"{profile_kind}:{identity}"))


def read_profile_metadata(
    profile_kind: str,
    filename: str,
    document: Mapping[str, Any],
) -> tuple[str, int]:
    """Interpret v2 metadata or derive the pure legacy migration identity."""

    _validate_profile_kind(profile_kind)
    if not isinstance(document, Mapping):
        raise ProfileContractError("Profile data is invalid")

    version = document.get("version")
    if version is not None and type(version) is not int:
        raise ProfileContractError("Profile version is invalid")
    has_v2_envelope = all(
        field in document
        for field in ("profile_id", "revision", "name")
    )
    if version in (None, 1) or (
        version == PROFILE_ENVELOPE_VERSION
        and not has_v2_envelope
    ):
        return legacy_profile_id(profile_kind, filename), 0
    if version != PROFILE_ENVELOPE_VERSION:
        raise ProfileContractError("Profile version is invalid")
    if not isinstance(document["name"], str) or not document["name"].strip():
        raise ProfileContractError("Profile name is invalid")

    return _parse_profile_id(document["profile_id"]), _parse_revision(document["revision"])


def build_profile_document(
    *,
    name: str,
    profile_id: str,
    revision: int,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Compose a v2 envelope while preventing payload metadata overrides."""

    if not isinstance(payload, Mapping):
        raise ProfileContractError("Profile payload is invalid")
    document = {
        key: value
        for key, value in payload.items()
        if key not in _ENVELOPE_FIELDS
    }
    return {
        "version": PROFILE_ENVELOPE_VERSION,
        "profile_id": _parse_profile_id(profile_id),
        "revision": _parse_revision(revision),
        "name": _parse_profile_name(name),
        **document,
    }


def interpret_profile_document(
    profile_kind: str,
    filename: str,
    document: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the additive v2 view of stored bytes without writing migration state."""

    profile_id, revision = read_profile_metadata(profile_kind, filename, document)
    return build_profile_document(
        name=filename,
        profile_id=profile_id,
        revision=revision,
        payload=document,
    )


def create_profile_document(
    profile_kind: str,
    name: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Create a server-owned UUID4 profile at content revision one."""

    _validate_profile_kind(profile_kind)
    return build_profile_document(
        name=name,
        profile_id=str(uuid.uuid4()),
        revision=1,
        payload=payload,
    )


def update_profile_document(
    profile_kind: str,
    filename: str,
    current_document: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Preserve identity and advance content revision for a normal overwrite."""

    profile_id, revision = read_profile_metadata(
        profile_kind,
        filename,
        current_document,
    )
    return build_profile_document(
        name=filename,
        profile_id=profile_id,
        revision=revision + 1,
        payload=payload,
    )


def rename_profile_document(
    profile_kind: str,
    source_filename: str,
    target_filename: str,
    current_document: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Preserve source identity and content revision across a display rename."""

    profile_id, revision = read_profile_metadata(
        profile_kind,
        source_filename,
        current_document,
    )
    return build_profile_document(
        name=target_filename,
        profile_id=profile_id,
        revision=revision,
        payload=payload,
    )


def _validate_profile_kind(profile_kind: str) -> None:
    if profile_kind not in _PROFILE_KINDS:
        raise ValueError(f"Unknown profile kind: {profile_kind}")


def _parse_profile_id(value: Any) -> str:
    if not isinstance(value, str):
        raise ProfileContractError("Profile ID is invalid")
    try:
        return str(uuid.UUID(value))
    except (AttributeError, ValueError) as exc:
        raise ProfileContractError("Profile ID is invalid") from exc


def _parse_revision(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ProfileContractError("Profile revision is invalid")
    return value


def _parse_profile_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfileContractError("Profile name is invalid")
    return value


__all__ = ()
