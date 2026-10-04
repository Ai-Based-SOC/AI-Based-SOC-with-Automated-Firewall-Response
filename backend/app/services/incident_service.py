"""
Incident Management Service.

Provides CRUD operations, investigation workflow, timeline, evidence,
and lifecycle management for security incidents.
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.models.incident import (
    Incident,
    IncidentEvidence,
    IncidentNote,
    IncidentSeverity,
    IncidentStatus,
    IncidentTimelineEvent,
    IncidentType,
)
from backend.app.schemas.common import (
    IncidentCreate,
    IncidentUpdate,
)


class IncidentService:
    """Service for managing security incidents."""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Query ====================

    def list_incidents(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        severity: Optional[IncidentSeverity] = None,
        status: Optional[IncidentStatus] = None,
        assignee_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Incident], int]:
        """List incidents with pagination, search, and filtering."""
        query = self.db.query(Incident)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Incident.title.ilike(term),
                    Incident.description.ilike(term),
                    Incident.incident_id.ilike(term),
                )
            )
        if severity:
            query = query.filter(Incident.severity == severity)
        if status:
            query = query.filter(Incident.status == status)
        if assignee_id is not None:
            query = query.filter(Incident.assigned_to_id == assignee_id)
        if start_date:
            query = query.filter(Incident.detected_at >= start_date)
        if end_date:
            query = query.filter(Incident.detected_at <= end_date)

        sort_column = getattr(Incident, sort_by, Incident.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        total = query.count()
        incidents = query.offset((page - 1) * page_size).limit(page_size).all()
        return incidents, total

    def get_incident(self, incident_id: int) -> Optional[Incident]:
        """Get an incident by ID."""
        return self.db.query(Incident).filter(Incident.id == incident_id).first()

    def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get incident statistics for dashboard."""
        query = self.db.query(Incident)
        if start_date:
            query = query.filter(Incident.detected_at >= start_date)
        if end_date:
            query = query.filter(Incident.detected_at <= end_date)

        total = query.count()
        return {
            "total": total,
            "open": query.filter(Incident.status == IncidentStatus.OPEN).count(),
            "investigating": query.filter(
                Incident.status == IncidentStatus.INVESTIGATING
            ).count(),
            "closed": query.filter(Incident.status == IncidentStatus.CLOSED).count(),
            "critical": query.filter(
                Incident.severity == IncidentSeverity.CRITICAL
            ).count(),
        }

    def create_incident(
        self, incident_data: IncidentCreate, user_id: UUID
    ) -> Incident:
        """Create a new incident."""
        now = datetime.utcnow()
        incident = Incident(
            incident_id=f"INC-{now.strftime('%Y%m%d')}-{int(now.timestamp())}",
            title=incident_data.title,
            description=incident_data.description,
            severity=IncidentSeverity(incident_data.severity),
            status=IncidentStatus.OPEN,
            incident_type=IncidentType.UNKNOWN,
            detected_at=now,
            created_by_id=user_id,
            assigned_to_id=getattr(incident_data, "assigned_to", None),
            mitre_techniques=[],
            mitre_tactics=[],
            affected_assets=[],
            affected_users=[],
            created_at=now,
            updated_at=now,
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def update_incident(
        self, incident_id: int, incident_data: IncidentUpdate, user_id: UUID
    ) -> Optional[Incident]:
        """Update an incident."""
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        update_data = incident_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "severity" and value:
                setattr(incident, field, IncidentSeverity(value))
            elif field == "status" and value:
                setattr(incident, field, IncidentStatus(value))
            elif field == "assigned_to" and value:
                setattr(incident, "assigned_to_id", value)
            else:
                setattr(incident, field, value)
        incident.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def delete_incident(self, incident_id: int) -> None:
        """Delete an incident."""
        incident = self.get_incident(incident_id)
        if not incident:
            raise NotFoundError("Incident not found")
        self.db.delete(incident)
        self.db.commit()

    # ==================== Workflow ====================

    def update_status(
        self, incident_id: int, status: IncidentStatus, user_id: UUID
    ) -> Optional[Incident]:
        """Update incident status."""
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        incident.status = status
        now = datetime.utcnow()
        incident.updated_at = now
        if status == IncidentStatus.CONTAINMENT:
            incident.contained_at = now
        elif status == IncidentStatus.CLOSED:
            incident.closed_at = now
        self.add_timeline_entry(
            incident_id, f"Status changed to {status.value}", "status_change", user_id
        )
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def add_timeline_entry(
        self, incident_id: int, entry: str, entry_type: str, user_id: UUID
    ) -> Optional[Incident]:
        """Add a timeline entry to an incident."""
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        event = IncidentTimelineEvent(
            incident_id=incident.id,
            user_id=user_id,
            event_type=entry_type,
            title=entry,
            description=entry,
            occurred_at=datetime.utcnow(),
        )
        self.db.add(event)
        incident.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def add_evidence(
        self,
        incident_id: int,
        evidence_type: str,
        evidence_data: dict,
        user_id: UUID,
    ) -> Optional[Incident]:
        """Add evidence to an incident."""
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        now = datetime.utcnow()
        evidence = IncidentEvidence(
            incident_id=incident.id,
            uploaded_by_id=user_id,
            filename=evidence_data.get("filename", "evidence"),
            original_filename=evidence_data.get("filename", "evidence"),
            file_path=evidence_data.get("file_path", ""),
            file_size=evidence_data.get("file_size", 0),
            mime_type=evidence_data.get("mime_type", "application/octet-stream"),
            file_hash=evidence_data.get("file_hash", ""),
            evidence_type=evidence_type,
            created_at=now,
        )
        self.db.add(evidence)
        incident.updated_at = now
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def close_incident(
        self,
        incident_id: int,
        resolution: str,
        root_cause: Optional[str] = None,
        lessons_learned: Optional[str] = None,
        user_id: UUID = None,
    ) -> Optional[Incident]:
        """Close an incident with resolution details."""
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        incident.status = IncidentStatus.CLOSED
        now = datetime.utcnow()
        incident.closed_at = now
        incident.updated_at = now
        note = IncidentNote(
            incident_id=incident.id,
            user_id=user_id,
            content=f"Resolution: {resolution}",
            is_internal=False,
            is_timeline_event=False,
            created_at=now,
            updated_at=now,
        )
        self.db.add(note)
        self.add_timeline_entry(incident_id, "Incident closed", "closed", user_id)
        self.db.commit()
        self.db.refresh(incident)
        return incident