"""
Alerts API routes.

Provides CRUD operations for security alerts with filtering, search, and bulk actions.
"""
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_permission
from backend.app.db.session import get_db
from backend.app.models.alert import Alert, AlertSeverity, AlertStatus
from backend.app.models.user import User
from backend.app.schemas.common import (
    AlertCreate,
    AlertResponse,
    AlertUpdate,
    BulkActionRequest,
    BulkActionResponse,
    MessageResponse,
    PaginatedResponse,
)
from backend.app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=PaginatedResponse[AlertResponse], summary="List alerts")
def list_alerts(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query()] = None,
    severity: Annotated[AlertSeverity | None, Query()] = None,
    status: Annotated[AlertStatus | None, Query()] = None,
    source_ip: Annotated[str | None, Query()] = None,
    dest_ip: Annotated[str | None, Query()] = None,
    rule_id: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    current_user: User = Depends(require_permission("alerts:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AlertResponse]:
    """
    List alerts with pagination, search, and filtering.
    """
    alert_service = AlertService(db)
    alerts, total = alert_service.list_alerts(
        page=page,
        page_size=page_size,
        search=search,
        severity=severity,
        status=status,
        source_ip=source_ip,
        dest_ip=dest_ip,
        rule_id=rule_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats", summary="Get alert statistics")
def get_alert_stats(
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    current_user: User = Depends(require_permission("alerts:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get alert statistics for dashboard.
    """
    alert_service = AlertService(db)
    return alert_service.get_stats(start_date, end_date)


@router.get("/{alert_id}", response_model=AlertResponse, summary="Get alert by ID")
def get_alert(
    alert_id: UUID,
    current_user: User = Depends(require_permission("alerts:read")),
    db: Session = Depends(get_db),
) -> AlertResponse:
    """
    Get an alert by ID.
    """
    alert_service = AlertService(db)
    alert = alert_service.get_alert(alert_id)

    if not alert:
        raise NotFoundError("Alert not found")
    
    return AlertResponse.model_validate(alert)


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED, summary="Create alert")
def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(require_permission("alerts:write")),
    db: Session = Depends(get_db),
) -> AlertResponse:
    """
    Create a new alert.
    """
    alert_service = AlertService(db)
    alert = alert_service.create_alert(alert_data)
    
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}", response_model=AlertResponse, summary="Update alert")
def update_alert(
    alert_id: UUID,
    alert_data: AlertUpdate,
    current_user: User = Depends(require_permission("alerts:write")),
    db: Session = Depends(get_db),
) -> AlertResponse:
    """
    Update an alert.
    """
    alert_service = AlertService(db)
    alert = alert_service.update_alert(alert_id, alert_data, current_user.id)

    if not alert:
        raise NotFoundError("Alert not found")

    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse, summary="Acknowledge alert")
def acknowledge_alert(
    alert_id: UUID,
    current_user: User = Depends(require_permission("alerts:write")),
    db: Session = Depends(get_db),
) -> AlertResponse:
    """
    Acknowledge an alert.
    """
    alert_service = AlertService(db)
    alert = alert_service.acknowledge_alert(alert_id, current_user.id)

    if not alert:
        raise NotFoundError("Alert not found")

    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/resolve", response_model=AlertResponse, summary="Resolve alert")
def resolve_alert(
    alert_id: UUID,
    resolution_notes: str | None = None,
    current_user: User = Depends(require_permission("alerts:write")),
    db: Session = Depends(get_db),
) -> AlertResponse:
    """
    Resolve an alert.
    """
    alert_service = AlertService(db)
    alert = alert_service.resolve_alert(alert_id, current_user.id, resolution_notes)

    if not alert:
        raise NotFoundError("Alert not found")

    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/escalate", response_model=AlertResponse, summary="Escalate alert to incident")
def escalate_alert(
    alert_id: UUID,
    current_user: User = Depends(require_permission("alerts:write")),
    db: Session = Depends(get_db),
) -> AlertResponse:
    """
    Escalate an alert to an incident.
    """
    alert_service = AlertService(db)
    alert = alert_service.escalate_to_incident(alert_id, current_user.id)

    if not alert:
        raise NotFoundError("Alert not found")

    return AlertResponse.model_validate(alert)


@router.post("/bulk", response_model=BulkActionResponse, summary="Bulk action on alerts")
def bulk_action_alerts(
    action: BulkActionRequest,
    current_user: User = Depends(require_permission("alerts:write")),
    db: Session = Depends(get_db),
) -> BulkActionResponse:
    """
    Perform bulk action on multiple alerts.
    """
    alert_service = AlertService(db)
    result = alert_service.bulk_action(action, current_user.id)

    return BulkActionResponse(
        success_count=result["success"],
        failed_count=result["failed"],
        errors=result.get("errors", []),
    )


@router.delete("/{alert_id}", response_model=MessageResponse, summary="Delete alert")
def delete_alert(
    alert_id: UUID,
    current_user: User = Depends(require_permission("alerts:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete an alert (admin only).
    """
    alert_service = AlertService(db)
    alert_service.delete_alert(alert_id)

    return MessageResponse(message="Alert deleted successfully")