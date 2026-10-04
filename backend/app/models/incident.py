"""
Incident model for security incidents.
"""
import enum
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class IncidentStatus(str, enum.Enum):
    """Incident status."""
    OPEN = "open"
    TRIAGE = "triage"
    INVESTIGATING = "investigating"
    CONTAINMENT = "containment"
    ERADICATION = "eradication"
    RECOVERY = "recovery"
    POST_INCIDENT = "post_incident"
    CLOSED = "closed"
    REJECTED = "rejected"


class IncidentSeverity(str, enum.Enum):
    """Incident severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType(str, enum.Enum):
    """Incident types."""
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    PHISHING = "phishing"
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    LATERAL_MOVEMENT = "lateral_movement"
    PERSISTENCE = "persistence"
    RECONNAISSANCE = "reconnaissance"
    DENIAL_OF_SERVICE = "denial_of_service"
    INSIDER_THREAT = "insider_threat"
    POLICY_VIOLATION = "policy_violation"
    UNKNOWN = "unknown"


class Incident(Base):
    """Security incident model."""
    __tablename__ = "incidents"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)  # Human-readable ID
    
    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    incident_type: Mapped[IncidentType] = mapped_column(Enum(IncidentType), nullable=False, index=True)
    severity: Mapped[IncidentSeverity] = mapped_column(Enum(IncidentSeverity), nullable=False, index=True)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False, index=True)
    
    # MITRE ATT&CK
    mitre_techniques: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    mitre_tactics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Assignment
    created_by_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timeline
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    triaged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    contained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    eradicated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # SLA
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Impact
    affected_assets: Mapped[Optional[List[UUID]]] = mapped_column(JSON, nullable=True)  # Asset IDs
    affected_users: Mapped[Optional[List[UUID]]] = mapped_column(JSON, nullable=True)  # User IDs
    data_classification: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # public, internal, confidential, restricted
    estimated_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Response
    containment_actions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    eradication_actions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    recovery_actions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Playbook
    playbook_execution_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("playbook_executions.id"), nullable=True)
    
    # Raw data
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], back_populates="created_incidents", lazy="selectin")
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_incidents", lazy="selectin")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="incident", lazy="selectin")
    notes: Mapped[List["IncidentNote"]] = relationship("IncidentNote", back_populates="incident", lazy="selectin", cascade="all, delete-orphan")
    evidence: Mapped[List["IncidentEvidence"]] = relationship("IncidentEvidence", back_populates="incident", lazy="selectin", cascade="all, delete-orphan")
    timeline_events: Mapped[List["IncidentTimelineEvent"]] = relationship("IncidentTimelineEvent", back_populates="incident", lazy="selectin", cascade="all, delete-orphan")
    playbook_execution: Mapped[Optional["PlaybookExecution"]] = relationship("PlaybookExecution", back_populates="incident", lazy="selectin")
    
    __table_args__ = (
        Index("ix_incidents_status_severity", "status", "severity"),
        Index("ix_incidents_type_time", "incident_type", "detected_at"),
        Index("ix_incidents_assignee_status", "assigned_to_id", "status"),
        Index("ix_incidents_sla_due", "sla_due_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, incident_id={self.incident_id}, type={self.incident_type.value}, severity={self.severity.value}, status={self.status.value})>"


class IncidentNote(Base):
    """Notes/comments on incidents."""
    __tablename__ = "incident_notes"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_timeline_event: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    incident: Mapped[Incident] = relationship("Incident", back_populates="notes", lazy="selectin")
    user: Mapped["User"] = relationship("User", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<IncidentNote(id={self.id}, incident_id={self.incident_id})>"


class IncidentEvidence(Base):
    """Evidence attached to incidents."""
    __tablename__ = "incident_evidence"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # File info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # log, pcap, memory_dump, screenshot, etc.
    is_malicious: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    incident: Mapped[Incident] = relationship("Incident", back_populates="evidence", lazy="selectin")
    uploader: Mapped["User"] = relationship("User", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<IncidentEvidence(id={self.id}, incident_id={self.incident_id}, filename={self.filename})>"


class IncidentTimelineEvent(Base):
    """Timeline events for incidents."""
    __tablename__ = "incident_timeline_events"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Event info
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # created, assigned, status_change, note, evidence, containment, etc.
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    
    # Timing
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    incident: Mapped[Incident] = relationship("Incident", back_populates="timeline_events", lazy="selectin")
    user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    
    __table_args__ = (
        Index("ix_incident_timeline_incident_time", "incident_id", "occurred_at"),
    )
    
    def __repr__(self) -> str:
        return f"<IncidentTimelineEvent(id={self.id}, incident_id={self.incident_id}, type={self.event_type})>"