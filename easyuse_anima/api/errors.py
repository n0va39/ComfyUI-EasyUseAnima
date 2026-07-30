from __future__ import annotations

from typing import Any, Mapping


class ApiContractError(ValueError):
    """A public request-contract error with a stable HTTP mapping."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = dict(details) if details is not None else None


def _field_error(field: str, expectation: str) -> ApiContractError:
    return ApiContractError(
        422,
        "invalid_request",
        f"{field} must be {expectation}.",
        details={"field": field},
    )


__all__ = ("ApiContractError",)
