"""
Administration API routes.

Provides system administration, configuration, and management endpoints.
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_permission
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.common import (
    SystemConfigCreate,
    SystemConfigResponse,
    SystemConfigUpdate,
    MessageResponse,
    PaginatedResponse,
)
from backend.app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Administration"])


# =========================================================
# System Configuration
# =========================================================

@router.get("/config", response_model=PaginatedResponse[SystemConfigResponse], summary="List system configuration")
def list_config(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    search: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SystemConfigResponse]:
    """
    List system configuration with pagination and filtering.
    """
    admin_service = AdminService(db)
    configs, total = admin_service.list_config(
        page=page,
        page_size=page_size,
        search=search,
        category=category,
    )
    
    return PaginatedResponse(
        items=[SystemConfigResponse.model_validate(c) for c in configs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/config/{config_key}", response_model=SystemConfigResponse, summary="Get system configuration")
def get_config(
    config_key: str,
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> SystemConfigResponse:
    """
    Get a system configuration value by key.
    """
    admin_service = AdminService(db)
    config = admin_service.get_config(config_key)
    
    if not config:
        raise NotFoundError("Configuration not found")
    
    return SystemConfigResponse.model_validate(config)


@router.post("/config", response_model=SystemConfigResponse, status_code=status.HTTP_201_CREATED, summary="Create system configuration")
def create_config(
    config_data: SystemConfigCreate,
    current_user: User = Depends(require_permission("admin:write")),
    db: Session = Depends(get_db),
) -> SystemConfigResponse:
    """
    Create a new system configuration.
    """
    admin_service = AdminService(db)
    config = admin_service.create_config(config_data, current_user.id)
    
    return SystemConfigResponse.model_validate(config)


@router.patch("/config/{config_key}", response_model=SystemConfigResponse, summary="Update system configuration")
def update_config(
    config_key: str,
    config_data: SystemConfigUpdate,
    current_user: User = Depends(require_permission("admin:write")),
    db: Session = Depends(get_db),
) -> SystemConfigResponse:
    """
    Update a system configuration.
    """
    admin_service = AdminService(db)
    config = admin_service.update_config(config_key, config_data, current_user.id)
    
    if not config:
        raise NotFoundError("Configuration not found")
    
    return SystemConfigResponse.model_validate(config)


@router.delete("/config/{config_key}", response_model=MessageResponse, summary="Delete system configuration")
def delete_config(
    config_key: str,
    current_user: User = Depends(require_permission("admin:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a system configuration.
    """
    admin_service = AdminService(db)
    admin_service.delete_config(config_key)
    
    return MessageResponse(message="Configuration deleted successfully")


# =========================================================
# System Health & Status
# =========================================================

@router.get("/health", summary="Get system health")
def get_system_health(
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get comprehensive system health status.
    """
    admin_service = AdminService(db)
    return admin_service.get_system_health()


@router.get("/status", summary="Get system status")
def get_system_status(
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get system status including services, queues, and resources.
    """
    admin_service = AdminService(db)
    return admin_service.get_system_status()


@router.get("/metrics", summary="Get system metrics")
def get_system_metrics(
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get system performance metrics.
    """
    admin_service = AdminService(db)
    return admin_service.get_system_metrics(start_date, end_date)


# =========================================================
# Audit Logs
# =========================================================

@router.get("/audit-logs", response_model=PaginatedResponse[dict], summary="List audit logs")
def list_audit_logs(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=1000)] = 100,
    search: Annotated[str | None, Query()] = None,
    user_id: Annotated[int | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[dict]:
    """
    List audit logs with pagination and filtering.
    """
    admin_service = AdminService(db)
    logs, total = admin_service.list_audit_logs(
        page=page,
        page_size=page_size,
        search=search,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/audit-logs/stats", summary="Get audit log statistics")
def get_audit_log_stats(
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get audit log statistics.
    """
    admin_service = AdminService(db)
    return admin_service.get_audit_log_stats(start_date, end_date)


# =========================================================
# Backup & Restore
# =========================================================

@router.post("/backup", summary="Create system backup")
def create_backup(
    backup_config: dict,
    current_user: User = Depends(require_permission("admin:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Create a system backup.
    """
    admin_service = AdminService(db)
    return admin_service.create_backup(backup_config, current_user.id)


@router.get("/backups", summary="List backups")
def list_backups(
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    List available backups.
    """
    admin_service = AdminService(db)
    return admin_service.list_backups()


@router.post("/backups/{backup_id}/restore", summary="Restore from backup")
def restore_backup(
    backup_id: str,
    restore_config: dict | None = None,
    current_user: User = Depends(require_permission("admin:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Restore system from backup.
    """
    admin_service = AdminService(db)
    return admin_service.restore_backup(backup_id, restore_config, current_user.id)


@router.delete("/backups/{backup_id}", response_model=MessageResponse, summary="Delete backup")
def delete_backup(
    backup_id: str,
    current_user: User = Depends(require_permission("admin:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a backup.
    """
    admin_service = AdminService(db)
    admin_service.delete_backup(backup_id)
    
    return MessageResponse(message="Backup deleted successfully")


# =========================================================
# Maintenance
# =========================================================

@router.post("/maintenance/enable", summary="Enable maintenance mode")
def enable_maintenance(
    message: str | None = None,
    current_user: User = Depends(require_permission("admin:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Enable maintenance mode.
    """
    admin_service = AdminService(db)
    return admin_service.enable_maintenance(message, current_user.id)


@router.post("/maintenance/disable", summary="Disable maintenance mode")
def disable_maintenance(
    current_user: User = Depends(require_permission("admin:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Disable maintenance mode.
    """
    admin_service = AdminService(db)
    return admin_service.disable_maintenance(current_user.id)


@router.get("/maintenance/status", summary="Get maintenance mode status")
def get_maintenance_status(
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get maintenance mode status.
    """
    admin_service = AdminService(db)
    return admin_service.get_maintenance_status()


# =========================================================
# Feature Flags
# =========================================================

@router.get("/feature-flags", summary="List feature flags")
def list_feature_flags(
    current_user: User = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    List all feature flags.
    """
    admin_service = AdminService(db)
    return admin_service.list_feature_flags()


@router.post("/feature-flags", summary="Create feature flag")
def create_feature_flag(
    flag_data: dict,
    current_user: User = Depends(require_permission("admin:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Create a new feature flag.
    """
    admin_service = AdminService(db)
    return admin_service.create_feature_flag(flag_data, current_user.id)


@router.patch("/feature-flags/{flag_key}", summary="Update feature flag")
def update_feature_flag(
    flag_key: str,
    flag_data: dict,
    current_user: User = Depends(require_permission("admin:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Update a feature flag.
    """
    admin_service = AdminService(db)
    return admin_service.update_feature_flag(flag_key, flag_data, current_user.id)


@router.delete("/feature-flags/{flag_key}", response_model=MessageResponse, summary="Delete feature flag")
def delete_feature_flag(
    flag_key: str,
    current_user: User = Depends(require_permission("admin:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a feature flag.
    """
    admin_service = AdminService(db)
    admin_service.delete_feature_flag(flag_key)
    
    return MessageResponse(message="Feature flag deleted successfully")