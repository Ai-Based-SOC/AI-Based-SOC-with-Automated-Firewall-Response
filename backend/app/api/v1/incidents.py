"""
Incidents API routes.

Provides CRUD operations for security incidents with investigation workflow.
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_permission
from backend.app.db.session import get_db
from backend.app.models.incident import Incident, IncidentSeverity, IncidentStatus
from backend.app.models.user import User
from backend.app.schemas.common import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
    MessageResponse,
    PaginatedResponse,
)
from backend.app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=PaginatedResponse[IncidentResponse], summary="List incidents")
def list_incidents(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query()] = None,
    severity: Annotated[IncidentSeverity | None, Query()] = None,
    status: Annotated[IncidentStatus | None, Query()] = None,
    assignee_id: Annotated[int | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    current_user: User = Depends(require_permission("incidents:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[IncidentResponse]:
    """
    List incidents with pagination, search, and filtering.
    """
    incident_service = IncidentService(db)
    incidents, total = incident_service.list_incidents(
        page=page,
        page_size=page_size,
        search=search,
        severity=severity,
        status=status,
        assignee_id=assignee_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedResponse(
        items=[IncidentResponse.model_validate(i) for i in incidents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats", summary="Get incident statistics")
def get_incident_stats(
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    current_user: User = Depends(require_permission("incidents:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get incident statistics for dashboard.
    """
    incident_service = IncidentService(db)
    return incident_service.get_stats(start_date, end_date)


@router.get("/{incident_id}", response_model=IncidentResponse, summary="Get incident by ID")
def get_incident(
    incident_id: int,
    current_user: User = Depends(require_permission("incidents:read")),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """
    Get an incident by ID with full details.
    """
    incident_service = IncidentService(db)
    incident = incident_service.get_incident(incident_id)
    
    if not incident:
        raise NotFoundError("Incident not found")
    
    return IncidentResponse.model_validate(incident)


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED, summary="Create incident")
def create_incident(
    incident_data: IncidentCreate,
    current_user: User = Depends(require_permission("incidents:write")),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """
    Create a new incident.
    """
    incident_service = IncidentService(db)
    incident = incident_service.create_incident(incident_data, current_user.id)
    
    return IncidentResponse.model_validate(incident)


@router.patch("/{incident_id}", response_model=IncidentResponse, summary="Update incident")
def update_incident(
    incident_id: int,
    incident_data: IncidentUpdate,
    current_user: User = Depends(require_permission("incidents:write")),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """
    Update an incident.
    """
    incident_service = IncidentService(db)
    incident = incident_service.update_incident(incident_id, incident_data, current_user.id)
    
    if not incident:
        raise NotFoundError("Incident not found")
    
    return IncidentResponse.model_validate(incident)


@router.post("/{incident_id}/assign", response_model=IncidentResponse, summary="Assign incident")
def assign_incident(
    incident_id: int,
    assignee_id: int,
    current_user: User = Depends(require_permission("incidents:write")),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """
    Assign an incident to a user.
    """
    incident_service = IncidentService(db)
    incident = incident_service.assign_incident(incident_id, assignee_id, current_user.id)
    
    if not incident:
        raise NotFoundError("Incident not found")
    
    return IncidentResponse.model_validate(incident)


@router.post("/{incident_id}/status", response_model=IncidentResponse, summary="Update incident status")
def update_incident_status(
    incident_id: int,
    status: IncidentStatus,
    current_user: User = Depends(require_permission("incidents:write")),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """
    Update incident status.
    """
    incident_service = IncidentService(db)
    incident = incident_service.update_status(incident_id, status, current_user.id)
    
    if not incident:
        raise NotFoundError("Incident not found")
    
    return IncidentResponse.model_validate(incident)


@router.post("/{incident_id}/timeline", response_model=IncidentResponse, summary="Add timeline entry")
def add_timeline_entry(
    incident_id: int,
    entry: str,
    entry_type: str = "note",
    current_user: User = Depends(require_permission("incidents:write")),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """
    Add a timeline entry to an incident.
    """
    incident_service = IncidentService(db)
    incident = incident_service.add_timeline_entry(incident_id, entry, entry_type, current_user.id)
    
    if not incident:
        raise NotFoundError("Incident not found")
    
    return IncidentResponse.model_validate(incident)


@router.post("/{incident_id}/evidence", response_model=IncidentResponse, summary="Add evidence")
def add_evidence(
    incident_id: int,
    evidence_type: str,
    evidence_data: dict,
    current_user: User = Depends(require_permission("incidents:write")),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """
    Add evidence to an incident.
    """
    incident_service = IncidentService(db)
    incident = incident_service.add_evidence(incident_id, evidence_type, evidence_data, current_user.id)
    
    if not incident:
        raise NotFoundError("Incident not found")
    
    return IncidentResponse.model_validate(incident)


@router.post("/{incident_id}/close", response_model=IncidentResponse, summary="Close incident")
def close_incident(
    incident_id: int,
    resolution: str,
    root_cause: str | None = None,
    lessons_learned: str | None = None,
    current_user: User = Depends(require_permission("incidents:write")),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """
    Close an incident with resolution details.
    """
    incident_service = IncidentService(db)
    incident = incident_service.close_incident(
        incident_id, 
        resolution, 
        root_cause, 
        lessons_learned, 
        current_user.id
    )
    
    if not incident:
        raise NotFoundError("Incident not found")
    
    return IncidentResponse.model_validate(incident)


@router.delete("/{incident_id}", response_model=MessageResponse, summary="Delete incident")
def delete_incident(
    incident_id: int,
    current_user: User = Depends(require_permission("incidents:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete an incident (admin only).
    """
    incident_service = IncidentService(db)
    incident_service.delete_incident(incident_id)
    
    return MessageResponse(message="Incident deleted successfully")