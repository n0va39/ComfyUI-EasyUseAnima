"""Shared semantic error categories for feature and adapter boundaries."""

from __future__ import annotations


class EasyUseAnimaError(Exception):
    """Base class for errors raised by EasyUse Anima feature code."""


class ValidationError(EasyUseAnimaError):
    """A feature input or persisted contract is invalid."""


class ConflictError(EasyUseAnimaError):
    """A requested operation conflicts with retained feature state."""


class NotFoundError(EasyUseAnimaError):
    """A required feature-owned resource is absent."""


class CapabilityUnavailableError(EasyUseAnimaError):
    """A requested feature capability is currently unavailable."""


class UpstreamTimeoutError(EasyUseAnimaError):
    """An upstream dependency did not settle within its time budget."""


class StorageError(EasyUseAnimaError):
    """A feature-owned storage operation failed."""


__all__ = (
    "EasyUseAnimaError",
    "ValidationError",
    "ConflictError",
    "NotFoundError",
    "CapabilityUnavailableError",
    "UpstreamTimeoutError",
    "StorageError",
)
