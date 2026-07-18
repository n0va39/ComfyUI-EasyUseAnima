from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


AUTOCOMPLETE_INDEX_SCHEMA_VERSION = 1
_SQLITE_TIMEOUT_SECONDS = 0.1


@dataclass(frozen=True, slots=True)
class AutocompleteIndexSource:
    resolved_path: str
    revision: str

    @property
    def identity(self) -> str:
        normalized = os.path.normcase(self.resolved_path)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class IndexedAutocompleteEntry:
    tag: str
    category: str
    count: int
    description: str


@dataclass(frozen=True, slots=True)
class AutocompleteIndexDiagnostics:
    outcome: str
    reason: str
    backend: str
    source_revision: str
    entry_count: int
    index_path: Path | None


@dataclass(frozen=True, slots=True)
class AutocompleteIndexResult:
    entries: tuple[IndexedAutocompleteEntry, ...]
    diagnostics: AutocompleteIndexDiagnostics


class AutocompleteIndexUnavailable(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _InvalidAutocompleteIndex(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


_INDEX_LOCKS: dict[str, threading.Lock] = {}
_INDEX_LOCKS_GUARD = threading.Lock()


def _index_path(root: Path, source: AutocompleteIndexSource) -> Path:
    return Path(root) / f"autocomplete-{source.identity[:24]}.sqlite3"


def _index_lock(path: Path) -> threading.Lock:
    # Do not use Path.resolve() here. On Windows its canonicalization can
    # differ before and after the index directory is created, splitting first
    # access across two locks for the same eventual file.
    key = os.path.normcase(os.path.abspath(path))
    with _INDEX_LOCKS_GUARD:
        lock = _INDEX_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _INDEX_LOCKS[key] = lock
        return lock


def _is_locked_error(error: BaseException) -> bool:
    message = str(error).casefold()
    return "locked" in message or "busy" in message


def _readonly_connection(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise _InvalidAutocompleteIndex("missing")
    uri = f"{path.resolve().as_uri()}?mode=ro"
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(
            uri,
            uri=True,
            timeout=_SQLITE_TIMEOUT_SECONDS,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection
    except sqlite3.OperationalError as error:
        if connection is not None:
            connection.close()
        if _is_locked_error(error):
            raise AutocompleteIndexUnavailable("locked") from error
        raise _InvalidAutocompleteIndex("unreadable") from error
    except (OSError, sqlite3.DatabaseError) as error:
        if connection is not None:
            connection.close()
        raise _InvalidAutocompleteIndex("unreadable") from error


def _read_metadata(
    connection: sqlite3.Connection,
    source: AutocompleteIndexSource,
) -> tuple[int, str]:
    try:
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        row = connection.execute(
            "SELECT schema_version, source_identity, source_revision, "
            "entry_count, backend FROM autocomplete_index_metadata WHERE id = 1"
        ).fetchone()
    except sqlite3.OperationalError as error:
        if _is_locked_error(error):
            raise AutocompleteIndexUnavailable("locked") from error
        raise _InvalidAutocompleteIndex("corrupt") from error
    except sqlite3.DatabaseError as error:
        raise _InvalidAutocompleteIndex("corrupt") from error

    if row is None:
        raise _InvalidAutocompleteIndex("corrupt")
    try:
        schema_version = int(row["schema_version"])
    except (TypeError, ValueError) as error:
        raise _InvalidAutocompleteIndex("corrupt") from error
    if user_version != AUTOCOMPLETE_INDEX_SCHEMA_VERSION or (
        schema_version != AUTOCOMPLETE_INDEX_SCHEMA_VERSION
    ):
        raise _InvalidAutocompleteIndex("schema_mismatch")
    if str(row["source_identity"]) != source.identity:
        raise _InvalidAutocompleteIndex("source_identity_mismatch")
    if str(row["source_revision"]) != source.revision:
        raise _InvalidAutocompleteIndex("source_revision_mismatch")

    backend = str(row["backend"])
    if backend not in {"fts5_trigram", "sqlite_prefix"}:
        raise _InvalidAutocompleteIndex("schema_mismatch")
    try:
        entry_count = int(row["entry_count"])
    except (TypeError, ValueError) as error:
        raise _InvalidAutocompleteIndex("corrupt") from error
    if entry_count < 0:
        raise _InvalidAutocompleteIndex("corrupt")
    return entry_count, backend


def _prefix_upper_bound(value: str) -> str | None:
    codepoints = [ord(character) for character in value]
    for index in range(len(codepoints) - 1, -1, -1):
        if codepoints[index] < 0x10FFFF:
            codepoints[index] += 1
            return "".join(chr(codepoint) for codepoint in codepoints[: index + 1])
    return None


def _like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _category_clause(categories: set[str]) -> tuple[str, list[str]]:
    if not categories:
        return "", []
    ordered = sorted(categories)
    placeholders = ", ".join("?" for _ in ordered)
    return f" AND e.category IN ({placeholders})", ordered


def _fetch_tier(
    connection: sqlite3.Connection,
    from_clause: str,
    conditions: str,
    parameters: list[object],
    categories: set[str],
    limit: int,
) -> list[sqlite3.Row]:
    if limit <= 0:
        return []
    category_sql, category_parameters = _category_clause(categories)
    sql = (
        "SELECT e.tag, e.category, e.count, e.description "
        f"FROM {from_clause} WHERE {conditions}{category_sql} "
        "ORDER BY e.count DESC, e.tag ASC, e.id ASC LIMIT ?"
    )
    try:
        return list(
            connection.execute(
                sql,
                [*parameters, *category_parameters, limit],
            ).fetchall()
        )
    except sqlite3.OperationalError as error:
        if _is_locked_error(error):
            raise AutocompleteIndexUnavailable("locked") from error
        raise _InvalidAutocompleteIndex("corrupt") from error
    except sqlite3.DatabaseError as error:
        raise _InvalidAutocompleteIndex("corrupt") from error


def _query_rows(
    connection: sqlite3.Connection,
    normalized_query: str,
    categories: set[str],
    limit: int,
    backend: str,
) -> tuple[IndexedAutocompleteEntry, ...]:
    rows: list[sqlite3.Row] = []

    rows.extend(
        _fetch_tier(
            connection,
            "autocomplete_entries AS e",
            "e.tag_key = ?",
            [normalized_query],
            categories,
            limit,
        )
    )

    remaining = limit - len(rows)
    upper_bound = _prefix_upper_bound(normalized_query)
    if remaining > 0 and upper_bound is not None:
        rows.extend(
            _fetch_tier(
                connection,
                "autocomplete_entries AS e",
                "e.tag_key >= ? AND e.tag_key < ? AND e.tag_key <> ?",
                [normalized_query, upper_bound, normalized_query],
                categories,
                remaining,
            )
        )

    remaining = limit - len(rows)
    use_trigram = backend == "fts5_trigram" and len(normalized_query) >= 3
    if remaining > 0:
        if use_trigram:
            from_clause = (
                "autocomplete_entries_fts AS f "
                "JOIN autocomplete_entries AS e ON e.id = f.rowid"
            )
            conditions = (
                "f.tag_key LIKE ? ESCAPE '\\' "
                "AND instr(e.tag_key, ?) > 0 "
                "AND substr(e.tag_key, 1, length(?)) <> ?"
            )
            parameters = [
                _like_pattern(normalized_query),
                normalized_query,
                normalized_query,
                normalized_query,
            ]
        else:
            from_clause = "autocomplete_entries AS e"
            conditions = (
                "instr(e.tag_key, ?) > 0 "
                "AND substr(e.tag_key, 1, length(?)) <> ?"
            )
            parameters = [normalized_query, normalized_query, normalized_query]
        rows.extend(
            _fetch_tier(
                connection,
                from_clause,
                conditions,
                parameters,
                categories,
                remaining,
            )
        )

    remaining = limit - len(rows)
    if remaining > 0:
        if use_trigram:
            from_clause = (
                "autocomplete_entries_fts AS f "
                "JOIN autocomplete_entries AS e ON e.id = f.rowid"
            )
            conditions = (
                "f.search LIKE ? ESCAPE '\\' "
                "AND instr(e.search, ?) > 0 AND instr(e.tag_key, ?) = 0"
            )
            parameters = [
                _like_pattern(normalized_query),
                normalized_query,
                normalized_query,
            ]
        else:
            from_clause = "autocomplete_entries AS e"
            conditions = "instr(e.search, ?) > 0 AND instr(e.tag_key, ?) = 0"
            parameters = [normalized_query, normalized_query]
        rows.extend(
            _fetch_tier(
                connection,
                from_clause,
                conditions,
                parameters,
                categories,
                remaining,
            )
        )

    return tuple(
        IndexedAutocompleteEntry(
            tag=str(row["tag"]),
            category=str(row["category"]),
            count=int(row["count"]),
            description=str(row["description"]),
        )
        for row in rows
    )


def _query_index(
    path: Path,
    source: AutocompleteIndexSource,
    normalized_query: str,
    categories: set[str],
    limit: int,
) -> tuple[tuple[IndexedAutocompleteEntry, ...], int, str]:
    connection = _readonly_connection(path)
    try:
        entry_count, backend = _read_metadata(connection, source)
        rows = _query_rows(
            connection,
            normalized_query,
            categories,
            limit,
            backend,
        )
        return rows, entry_count, backend
    finally:
        connection.close()


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE autocomplete_index_metadata (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            schema_version INTEGER NOT NULL,
            source_identity TEXT NOT NULL,
            source_revision TEXT NOT NULL,
            entry_count INTEGER NOT NULL,
            backend TEXT NOT NULL
        );
        CREATE TABLE autocomplete_entries (
            id INTEGER PRIMARY KEY,
            tag TEXT NOT NULL,
            tag_key TEXT NOT NULL,
            category TEXT NOT NULL,
            count INTEGER NOT NULL,
            description TEXT NOT NULL,
            search TEXT NOT NULL
        );
        """
    )


def _build_index(
    path: Path,
    source: AutocompleteIndexSource,
    entries: Iterable[object],
    validate_source: Callable[[], None],
) -> tuple[int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(temporary_path, timeout=_SQLITE_TIMEOUT_SECONDS)
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("BEGIN IMMEDIATE")
        _create_schema(connection)
        connection.executemany(
            "INSERT INTO autocomplete_entries "
            "(id, tag, tag_key, category, count, description, search) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                (
                    index,
                    entry.tag,
                    entry.tag_key,
                    entry.category,
                    entry.count,
                    entry.description,
                    entry.search,
                )
                for index, entry in enumerate(entries, start=1)
            ),
        )
        entry_count = int(
            connection.execute("SELECT COUNT(*) FROM autocomplete_entries").fetchone()[0]
        )
        connection.executescript(
            """
            CREATE INDEX autocomplete_entries_tag_key_idx
                ON autocomplete_entries(tag_key);
            CREATE INDEX autocomplete_entries_category_tag_key_idx
                ON autocomplete_entries(category, tag_key);
            """
        )

        backend = "sqlite_prefix"
        try:
            connection.execute(
                "CREATE VIRTUAL TABLE autocomplete_entries_fts USING fts5("
                "tag_key, search, content='autocomplete_entries', content_rowid='id', "
                "tokenize='trigram')"
            )
            connection.execute(
                "INSERT INTO autocomplete_entries_fts(autocomplete_entries_fts) "
                "VALUES ('rebuild')"
            )
            backend = "fts5_trigram"
        except sqlite3.OperationalError:
            connection.execute("DROP TABLE IF EXISTS autocomplete_entries_fts")

        connection.execute(
            "INSERT INTO autocomplete_index_metadata "
            "(id, schema_version, source_identity, source_revision, entry_count, backend) "
            "VALUES (1, ?, ?, ?, ?, ?)",
            (
                AUTOCOMPLETE_INDEX_SCHEMA_VERSION,
                source.identity,
                source.revision,
                entry_count,
                backend,
            ),
        )
        connection.execute(f"PRAGMA user_version = {AUTOCOMPLETE_INDEX_SCHEMA_VERSION}")
        connection.commit()
        connection.close()
        connection = None

        validate_source()
        os.replace(temporary_path, path)
        return entry_count, backend
    finally:
        if connection is not None:
            connection.close()
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def _query_or_invalid(
    path: Path,
    source: AutocompleteIndexSource,
    normalized_query: str,
    categories: set[str],
    limit: int,
) -> tuple[tuple[IndexedAutocompleteEntry, ...], int, str]:
    try:
        return _query_index(path, source, normalized_query, categories, limit)
    except AutocompleteIndexUnavailable:
        raise
    except _InvalidAutocompleteIndex:
        raise
    except sqlite3.OperationalError as error:
        if _is_locked_error(error):
            raise AutocompleteIndexUnavailable("locked") from error
        raise _InvalidAutocompleteIndex("corrupt") from error
    except sqlite3.DatabaseError as error:
        raise _InvalidAutocompleteIndex("corrupt") from error
    except OSError as error:
        raise AutocompleteIndexUnavailable("unreadable") from error


def search_autocomplete_index(
    *,
    root: Path | None,
    source: AutocompleteIndexSource,
    normalized_query: str,
    categories: set[str],
    limit: int,
    load_entries: Callable[[], Iterable[object]],
    validate_source: Callable[[], None],
) -> AutocompleteIndexResult:
    if root is None:
        raise AutocompleteIndexUnavailable("disabled")

    path = _index_path(Path(root), source)
    try:
        rows, entry_count, backend = _query_or_invalid(
            path,
            source,
            normalized_query,
            categories,
            limit,
        )
    except _InvalidAutocompleteIndex:
        with _index_lock(path):
            try:
                rows, entry_count, backend = _query_or_invalid(
                    path,
                    source,
                    normalized_query,
                    categories,
                    limit,
                )
            except _InvalidAutocompleteIndex as current_invalid:
                rebuild_reason = current_invalid.reason
                try:
                    _build_index(
                        path,
                        source,
                        load_entries(),
                        validate_source,
                    )
                    rows, entry_count, backend = _query_or_invalid(
                        path,
                        source,
                        normalized_query,
                        categories,
                        limit,
                    )
                except AutocompleteIndexUnavailable:
                    raise
                except _InvalidAutocompleteIndex as error:
                    raise AutocompleteIndexUnavailable("rebuild_unreadable") from error
                except sqlite3.OperationalError as error:
                    reason = "locked" if _is_locked_error(error) else "build_failed"
                    raise AutocompleteIndexUnavailable(reason) from error
                except (OSError, sqlite3.DatabaseError) as error:
                    raise AutocompleteIndexUnavailable("build_failed") from error
                diagnostics = AutocompleteIndexDiagnostics(
                    outcome="rebuild",
                    reason=rebuild_reason,
                    backend=backend,
                    source_revision=source.revision,
                    entry_count=entry_count,
                    index_path=path,
                )
                return AutocompleteIndexResult(entries=rows, diagnostics=diagnostics)
            else:
                diagnostics = AutocompleteIndexDiagnostics(
                    outcome="hit",
                    reason="concurrent_reuse",
                    backend=backend,
                    source_revision=source.revision,
                    entry_count=entry_count,
                    index_path=path,
                )
                return AutocompleteIndexResult(entries=rows, diagnostics=diagnostics)
    else:
        diagnostics = AutocompleteIndexDiagnostics(
            outcome="hit",
            reason="valid",
            backend=backend,
            source_revision=source.revision,
            entry_count=entry_count,
            index_path=path,
        )
        return AutocompleteIndexResult(entries=rows, diagnostics=diagnostics)

    raise AssertionError("unreachable autocomplete index state")
