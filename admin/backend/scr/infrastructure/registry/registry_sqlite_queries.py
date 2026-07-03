"""SQLite query helpers for the registry index."""

from __future__ import annotations

from typing import Any

from scr.core.exceptions import BadRequestError
from scr.infrastructure.registry.registry_sqlite_schema import SORTABLE_FIELDS


def validate_sort(sort: str) -> None:
    """Validate the public sort field before it is interpolated into SQL."""
    if sort not in SORTABLE_FIELDS:
        raise BadRequestError("sort 字段不支持。", code="invalid_sort_field", details={"sort": sort})


def build_entity_filters(
    *,
    entity_type: str | None,
    status: str,
    q: str | None,
) -> tuple[str, list[Any]]:
    """Build the registry_entities WHERE clause and bound parameters."""
    clauses: list[str] = []
    params: list[Any] = []
    if entity_type:
        clauses.append("entity_type = ?")
        params.append(entity_type)
    if status != "all":
        clauses.append("status = ?")
        params.append(status)
    if q:
        clauses.append("(entity_key LIKE ? OR title LIKE ? OR display_name LIKE ? OR description LIKE ? OR summary LIKE ?)")
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern, pattern, pattern])
    return (f"WHERE {' AND '.join(clauses)}" if clauses else "", params)


def table_exists(conn, name: str) -> bool:
    """Return whether a table or virtual table exists in the SQLite database."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE name = ? AND type IN ('table', 'virtual table')",
        (name,),
    ).fetchone()
    return row is not None

