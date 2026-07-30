"""Internal typed result contracts for Autocomplete payloads."""

from __future__ import annotations

from typing import TypedDict


class AutocompleteSourcePayload(TypedDict):
    key: str
    label: str
    source: str
    license: str
    path: str
    exists: bool
    selected: bool


class AutocompletePublicSourcePayload(TypedDict):
    key: str
    label: str
    source: str
    license: str
    exists: bool
    selected: bool


class AutocompleteStatusPayload(TypedDict):
    path: str
    exists: bool
    count: int
    mtime: float


class AutocompletePublicStatusPayload(TypedDict):
    exists: bool
    count: int
    mtime: float


class AutocompletePublicStatusResultPayload(AutocompletePublicStatusPayload):
    source: str
    source_label: str
    sources: list[AutocompletePublicSourcePayload]


class AutocompleteSearchEntryPayload(TypedDict):
    tag: str
    category: str
    count: int
    description: str


class _AutocompleteSearchPayloadRequired(TypedDict):
    query: str
    results: list[AutocompleteSearchEntryPayload]
    status: AutocompleteStatusPayload
    elapsed_ms: float


class AutocompleteSearchPayload(_AutocompleteSearchPayloadRequired, total=False):
    category: str


class _AutocompletePublicSearchPayloadRequired(TypedDict):
    query: str
    results: list[AutocompleteSearchEntryPayload]
    status: AutocompletePublicStatusPayload
    elapsed_ms: float


class AutocompletePublicSearchPayload(
    _AutocompletePublicSearchPayloadRequired,
    total=False,
):
    category: str


class AutocompleteClassificationTokenPayload(TypedDict):
    token: str
    base: str
    section: str
    label: str
    learned: bool
    weighted: bool
    count: int
    description: str


class AutocompleteClassificationPayload(TypedDict):
    tokens: list[AutocompleteClassificationTokenPayload]
    status: AutocompleteStatusPayload


class AutocompletePublicClassificationPayload(TypedDict):
    tokens: list[AutocompleteClassificationTokenPayload]
    status: AutocompletePublicStatusPayload


__all__ = ()
