"""Content synchronization DTOs."""

from pydantic import BaseModel


class SyncRequestDTO(BaseModel):
    """Common dry-run/confirm payload for content sync endpoints."""

    dry_run: bool = True
    confirm: bool = False
