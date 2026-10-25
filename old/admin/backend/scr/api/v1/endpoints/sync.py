"""Unified content synchronization endpoints."""

from fastapi import APIRouter, Depends

from scr.api.v1.dependencies import get_backend_index_sync_service, get_site_config_sync_service
from scr.schemas.common import MutationPlanDTO
from scr.schemas.sync import SyncRequestDTO
from scr.services.content.sync.backend_index_sync_service import BackendIndexSyncService
from scr.services.content.sync.site_config_sync_service import SiteConfigSyncService


router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/backend-index", response_model=MutationPlanDTO, response_model_exclude_none=True)
def sync_backend_index(
    payload: SyncRequestDTO,
    backend_index_sync_service: BackendIndexSyncService = Depends(get_backend_index_sync_service),
) -> MutationPlanDTO:
    """Rebuild admin backend source files from actual site content."""
    return backend_index_sync_service.sync(dry_run=payload.dry_run, confirm=payload.confirm)


@router.post("/site-config", response_model=MutationPlanDTO, response_model_exclude_none=True)
def sync_site_config(
    payload: SyncRequestDTO,
    site_config_sync_service: SiteConfigSyncService = Depends(get_site_config_sync_service),
) -> MutationPlanDTO:
    """Synchronize Docusaurus config files from actual site content."""
    return site_config_sync_service.sync(dry_run=payload.dry_run, confirm=payload.confirm)
