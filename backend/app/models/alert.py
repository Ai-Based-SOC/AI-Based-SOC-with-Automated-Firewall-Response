"""
Alert model for security alerts.
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


class AlertStatus(str, enum.Enum):
    """Alert status."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    BENIGN = "benign"
    ESCALATED = "escalated"
    CLOSED = "closed"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSource(str, enum.Enum):
    """Alert source types."""
    SIEM = "siem"
    IDS_IPS = "ids_ips"
    EDR = "edr"
    FIREWALL = "firewall"
    WAF = "waf"
    EMAIL_SECURITY = "email_security"
    CLOUD_SECURITY = "cloud_security"
    THREAT_INTEL = "threat_intel"
    USER_REPORT = "user_report"
    ML_MODEL = "ml_model"
    MANUAL = "manual"


class Alert(Base):
    """Security alert model."""
    __tablename__ = "alerts"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)  # External ID
    
    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity), nullable=False, index=True)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.NEW, nullable=False, index=True)
    source: Mapped[AlertSource] = mapped_column(Enum(AlertSource), nullable=False, index=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Reference ID in source system
    
    # Network info
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    source_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    source_asn: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    destination_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    destination_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    destination_country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # MITRE ATT&CK
    mitre_techniques: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # List of technique IDs
    mitre_tactics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # List of tactic IDs
    
    # Threat intelligence
    threat_intel_matches: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    ioc_matches: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # IOC IDs
    
    # ML/AI scoring
    ml_score: Mapped[Optional[float]] = mapped_column(nullable=True)  # 0-1 anomaly score
    ml_classification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # 0-100
    
    # Assignment
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    acknowledged_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Incident linking
    incident_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True, index=True)
    
    # Raw data
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Original alert data
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_alerts", lazy="selectin")
    acknowledged_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[acknowledged_by_id], lazy="selectin")
    incident: Mapped[Optional["Incident"]] = relationship("Incident", back_populates="alerts", lazy="selectin")
    notes: Mapped[List["AlertNote"]] = relationship("AlertNote", back_populates="alert", lazy="selectin", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_alerts_status_severity", "status", "severity"),
        Index("ix_alerts_source_time", "source", "first_seen"),
        Index("ix_alerts_source_ip_time", "source_ip", "first_seen"),
        Index("ix_alerts_dest_ip_time", "destination_ip", "first_seen"),
        Index("ix_alerts_risk_score", "risk_score"),
    )
    
    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, alert_id={self.alert_id}, severity={self.severity.value}, status={self.status.value})>"


class AlertNote(Base):
    """Notes/comments on alerts."""
    __tablename__ = "alert_notes"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    alert: Mapped[Alert] = relationship("Alert", back_populates="notes", lazy="selectin")
    user: Mapped["User"] = relationship("User", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<AlertNote(id={self.id}, alert_id={self.alert_id})>"