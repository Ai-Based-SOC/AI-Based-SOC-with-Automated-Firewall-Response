"""
Asset Management API routes.

Provides asset inventory, discovery, and vulnerability management.
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_permission
from backend.app.db.session import get_db
from backend.app.models.asset import Asset, AssetType, AssetCriticality
from backend.app.models.user import User
from backend.app.schemas.common import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    MessageResponse,
    PaginatedResponse,
)
from backend.app.services.asset_service import AssetService

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=PaginatedResponse[AssetResponse], summary="List assets")
def list_assets(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query()] = None,
    asset_type: Annotated[AssetType | None, Query()] = None,
    criticality: Annotated[AssetCriticality | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    environment: Annotated[str | None, Query()] = None,
    owner_id: Annotated[int | None, Query()] = None,
    has_vulnerabilities: Annotated[bool | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    current_user: User = Depends(require_permission("assets:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AssetResponse]:
    """
    List assets with pagination, search, and filtering.
    """
    asset_service = AssetService(db)
    assets, total = asset_service.list_assets(
        page=page,
        page_size=page_size,
        search=search,
        asset_type=asset_type,
        criticality=criticality,
        status=status,
        environment=environment,
        owner_id=owner_id,
        has_vulnerabilities=has_vulnerabilities,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedResponse(
        items=[AssetResponse.model_validate(a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats", summary="Get asset statistics")
def get_asset_stats(
    current_user: User = Depends(require_permission("assets:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get asset statistics for dashboard.
    """
    asset_service = AssetService(db)
    return asset_service.get_stats()


@router.get("/{asset_id}", response_model=AssetResponse, summary="Get asset by ID")
def get_asset(
    asset_id: int,
    current_user: User = Depends(require_permission("assets:read")),
    db: Session = Depends(get_db),
) -> AssetResponse:
    """
    Get an asset by ID with full details.
    """
    asset_service = AssetService(db)
    asset = asset_service.get_asset(asset_id)
    
    if not asset:
        raise NotFoundError("Asset not found")
    
    return AssetResponse.model_validate(asset)


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED, summary="Create asset")
def create_asset(
    asset_data: AssetCreate,
    current_user: User = Depends(require_permission("assets:write")),
    db: Session = Depends(get_db),
) -> AssetResponse:
    """
    Create a new asset.
    """
    asset_service = AssetService(db)
    asset = asset_service.create_asset(asset_data, current_user.id)
    
    return AssetResponse.model_validate(asset)


@router.patch("/{asset_id}", response_model=AssetResponse, summary="Update asset")
def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    current_user: User = Depends(require_permission("assets:write")),
    db: Session = Depends(get_db),
) -> AssetResponse:
    """
    Update an asset.
    """
    asset_service = AssetService(db)
    asset = asset_service.update_asset(asset_id, asset_data, current_user.id)
    
    if not asset:
        raise NotFoundError("Asset not found")
    
    return AssetResponse.model_validate(asset)


@router.post("/{asset_id}/scan", summary="Trigger vulnerability scan")
def trigger_scan(
    asset_id: int,
    scan_type: str = "full",
    current_user: User = Depends(require_permission("assets:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Trigger a vulnerability scan for an asset.
    """
    asset_service = AssetService(db)
    return asset_service.trigger_scan(asset_id, scan_type, current_user.id)


@router.get("/{asset_id}/vulnerabilities", summary="Get asset vulnerabilities")
def get_asset_vulnerabilities(
    asset_id: int,
    current_user: User = Depends(require_permission("assets:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get vulnerabilities for an asset.
    """
    asset_service = AssetService(db)
    return asset_service.get_vulnerabilities(asset_id)


@router.delete("/{asset_id}", response_model=MessageResponse, summary="Delete asset")
def delete_asset(
    asset_id: int,
    current_user: User = Depends(require_permission("assets:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete an asset (admin only).
    """
    asset_service = AssetService(db)
    asset_service.delete_asset(asset_id)
    
    return MessageResponse(message="Asset deleted successfully")


# =========================================================
# Asset Discovery
# =========================================================

@router.post("/discover", summary="Discover assets")
def discover_assets(
    discovery_config: dict,
    current_user: User = Depends(require_permission("assets:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Discover assets using network scanning or cloud APIs.
    """
    asset_service = AssetService(db)
    return asset_service.discover_assets(discovery_config, current_user.id)


@router.get("/discovery/jobs", summary="List discovery jobs")
def list_discovery_jobs(
    current_user: User = Depends(require_permission("assets:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    List asset discovery jobs.
    """
    asset_service = AssetService(db)
    return asset_service.list_discovery_jobs()


@router.get("/discovery/jobs/{job_id}", summary="Get discovery job status")
def get_discovery_job(
    job_id: int,
    current_user: User = Depends(require_permission("assets:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get status of a discovery job.
    """
    asset_service = AssetService(db)
    return asset_service.get_discovery_job(job_id)