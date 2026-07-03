"""DTO mappers for SQLite registry rows."""

from __future__ import annotations

import json
import sqlite3

from scr.schemas.registry_index import RegistryIndexItemDTO, RegistryIndexSyncResultDTO


def item_from_row(row: sqlite3.Row) -> RegistryIndexItemDTO:
    """Map a registry_entities row to the API DTO."""
    metadata = {}
    if row["metadata_json"]:
        try:
            metadata = json.loads(row["metadata_json"])
        except json.JSONDecodeError:
            metadata = {}
    return RegistryIndexItemDTO(
        id=int(row["id"]),
        entity_type=str(row["entity_type"]),
        entity_key=str(row["entity_key"]),
        slug=row["slug"],
        title=row["title"],
        display_name=row["display_name"],
        description=row["description"],
        summary=row["summary"],
        status=str(row["status"]),
        visibility=str(row["visibility"]),
        sort_order=int(row["sort_order"]),
        priority=int(row["priority"]),
        source_kind=str(row["source_kind"]),
        source_path=row["source_path"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=str(row["synced_at"]),
        metadata=metadata,
    )


def sync_result(
    *,
    database_path: str,
    sync_id: int,
    sync_type: str,
    status: str,
    scanned_files: int,
    changed_files: int,
    upserted_entities: int,
    deleted_entities: int,
    error_count: int,
    message: str | None,
) -> RegistryIndexSyncResultDTO:
    """Build a registry sync result DTO."""
    return RegistryIndexSyncResultDTO(
        sync_id=sync_id,
        sync_type=sync_type,
        status=status,
        database_path=database_path,
        scanned_files=scanned_files,
        changed_files=changed_files,
        upserted_entities=upserted_entities,
        deleted_entities=deleted_entities,
        error_count=error_count,
        message=message,
    )
