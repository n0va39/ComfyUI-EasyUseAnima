from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

from ...autocomplete.contracts import (
    AutocompleteClassificationPayload,
    AutocompletePublicClassificationPayload,
    AutocompletePublicSearchPayload,
    AutocompletePublicSourcePayload,
    AutocompletePublicStatusPayload,
    AutocompletePublicStatusResultPayload,
    AutocompleteSearchPayload,
    AutocompleteSourcePayload,
    AutocompleteStatusPayload,
)


class _SearchAutocomplete(Protocol):
    def __call__(
        self,
        query: str,
        *,
        limit: int,
        path: Path,
        category: str | None,
    ) -> AutocompleteSearchPayload: ...


class _ClassifyPromptText(Protocol):
    def __call__(
        self,
        text: str,
        *,
        limit: int,
        path: Path,
    ) -> AutocompleteClassificationPayload: ...


def build_autocomplete_payloads(
    *,
    resolve_autocomplete_source: Callable[[], str],
    resolve_autocomplete_source_path: Callable[[str], tuple[str, Path]],
    autocomplete_status: Callable[[Path], AutocompleteStatusPayload],
    available_autocomplete_sources: Callable[
        [str | None],
        list[AutocompleteSourcePayload],
    ],
    resolve_autocomplete_limit: Callable[[], int],
    search_autocomplete: _SearchAutocomplete,
    classify_prompt_text: _ClassifyPromptText,
    public_autocomplete_status: Callable[[object], dict[str, object]],
    public_autocomplete_payload: Callable[[object], dict[str, object]],
) -> tuple[
    Callable[[], AutocompletePublicStatusResultPayload],
    Callable[[object], dict[str, object]],
    Callable[[object], dict[str, object]],
    Callable[[str, str | None, str | None], AutocompletePublicSearchPayload],
    Callable[[str, int], AutocompletePublicClassificationPayload],
]:
    """Build redacted autocomplete payloads with runtime-resolved owners."""

    def _autocomplete_status_payload_sync() -> AutocompletePublicStatusResultPayload:
        selected_source = resolve_autocomplete_source()
        source_key, path = resolve_autocomplete_source_path(selected_source)
        status = cast(
            AutocompletePublicStatusPayload,
            public_autocomplete_status(autocomplete_status(path)),
        )
        sources: list[AutocompletePublicSourcePayload] = []
        source_label = source_key
        for source in available_autocomplete_sources(source_key):
            public_source = cast(
                AutocompletePublicSourcePayload,
                {
                    key: value
                    for key, value in source.items()
                    if key != "path"
                },
            )
            sources.append(public_source)
            if public_source.get("selected"):
                source_label = str(public_source.get("label") or source_key)
        return {
            **status,
            "source": source_key,
            "source_label": source_label,
            "sources": sources,
        }

    def _public_autocomplete_status(status: object) -> dict[str, object]:
        public_status = (
            cast(dict[str, object], dict(status))
            if isinstance(status, dict)
            else {}
        )
        public_status.pop("path", None)
        return public_status

    def _public_autocomplete_payload(payload: object) -> dict[str, object]:
        public_payload = (
            cast(dict[str, object], dict(payload))
            if isinstance(payload, dict)
            else {}
        )
        if "status" in public_payload:
            public_payload["status"] = public_autocomplete_status(
                public_payload["status"]
            )
        return public_payload

    def _search_autocomplete_payload_sync(
        query: str,
        requested_limit: str | None,
        category_filter: str | None,
    ) -> AutocompletePublicSearchPayload:
        default_limit = resolve_autocomplete_limit()
        try:
            limit = (
                int(requested_limit)
                if requested_limit is not None
                else default_limit
            )
        except ValueError:
            limit = default_limit
        _, path = resolve_autocomplete_source_path(resolve_autocomplete_source())
        return cast(
            AutocompletePublicSearchPayload,
            public_autocomplete_payload(
                search_autocomplete(
                    query,
                    limit=limit,
                    path=path,
                    category=category_filter,
                )
            )
        )

    def _classify_prompt_payload_sync(
        text: str,
        limit: int,
    ) -> AutocompletePublicClassificationPayload:
        _, path = resolve_autocomplete_source_path(resolve_autocomplete_source())
        return cast(
            AutocompletePublicClassificationPayload,
            public_autocomplete_payload(
                classify_prompt_text(text, limit=limit, path=path)
            ),
        )

    return (
        _autocomplete_status_payload_sync,
        _public_autocomplete_status,
        _public_autocomplete_payload,
        _search_autocomplete_payload_sync,
        _classify_prompt_payload_sync,
    )


def build_autocomplete_handlers(
    *,
    run_file_io,
    autocomplete_status_payload,
    search_autocomplete_payload,
    json_response,
):
    """Build the read-only autocomplete routes without loading dataset adapters."""

    async def autocomplete_status_handler(request):
        return json_response(
            await run_file_io(autocomplete_status_payload)
        )

    async def autocomplete_handler(request):
        query = request.query.get("q", "")
        category = request.query.get("category", "")
        category_filter = {
            "artist": "artist",
            "artist_or_general": "artist,general",
        }.get(category)
        return json_response(
            await run_file_io(
                search_autocomplete_payload,
                query,
                request.query.get("limit"),
                category_filter,
            )
        )

    return autocomplete_status_handler, autocomplete_handler


def build_classify_prompt_handler(
    *,
    parse_json_object,
    json_string,
    json_integer,
    contract_error_type,
    contract_error_response,
    run_file_io,
    classify_prompt_payload,
    json_response,
):
    """Build the prompt-classification route without loading feature adapters."""

    async def classify_prompt_handler(request):
        try:
            data = await parse_json_object(request)
            text = json_string(data, "text")
            limit = json_integer(
                data,
                "limit",
                default=240,
                minimum=1,
                maximum=500,
            )
        except contract_error_type as exc:
            return contract_error_response(exc)
        return json_response(
            await run_file_io(classify_prompt_payload, text, limit)
        )

    return classify_prompt_handler


__all__ = (
    "build_autocomplete_handlers",
    "build_classify_prompt_handler",
)
