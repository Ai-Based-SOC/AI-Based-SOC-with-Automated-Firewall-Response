"""
MITRE ATT&CK models for technique and tactic mapping.
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


class MITREPlatform(str, enum.Enum):
    """MITRE ATT&CK platforms."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    NETWORK = "network"
    CLOUD = "cloud"
    CONTAINERS = "containers"
    ICS = "ics"
    MOBILE = "mobile"
    PRE = "pre"
    SAAS = "saas"
    OFFICE_365 = "office_365"
    AZURE_AD = "azure_ad"
    GOOGLE_WORKSPACE = "google_workspace"


class MITREDataSource(str, enum.Enum):
    """MITRE ATT&CK data sources."""
    PROCESS_CREATION = "process_creation"
    PROCESS_COMMAND_LINE = "process_command_line"
    PROCESS_MODULE_LOAD = "process_module_load"
    FILE_CREATION = "file_creation"
    FILE_MODIFICATION = "file_modification"
    FILE_DELETION = "file_deletion"
    FILE_METADATA = "file_metadata"
    NETWORK_TRAFFIC = "network_traffic"
    NETWORK_CONNECTION = "network_connection"
    DNS_REQUEST = "dns_request"
    HTTP_REQUEST = "http_request"
    EMAIL = "email"
    USER_LOGON = "user_logon"
    USER_LOGOFF = "user_logoff"
    AUTHENTICATION = "authentication"
    PERMISSION_MODIFICATION = "permission_modification"
    REGISTRY_MODIFICATION = "registry_modification"
    SERVICE_CREATION = "service_creation"
    SERVICE_MODIFICATION = "service_modification"
    SCHEDULED_TASK_CREATION = "scheduled_task_creation"
    SCHEDULED_TASK_MODIFICATION = "scheduled_task_modification"
    WMI_EVENT = "wmi_event"
    POWERSHELL_LOG = "powershell_log"
    SCRIPT_EXECUTION = "script_execution"
    MODULE_LOAD = "module_load"
    DRIVER_LOAD = "driver_load"
    KERNEL_MODULE_LOAD = "kernel_module_load"
    CONTAINER_CREATION = "container_creation"
    CONTAINER_MODIFICATION = "container_modification"
    CLOUD_API_CALL = "cloud_api_call"
    CLOUD_LOG = "cloud_log"
    FIREWALL_LOG = "firewall_log"
    PROXY_LOG = "proxy_log"
    VPN_LOG = "vpn_log"
    IDS_ALERT = "ids_alert"
    ANTIVIRUS_ALERT = "antivirus_alert"
    EDR_ALERT = "edr_alert"


class MITRETechnique(Base):
    """MITRE ATT&CK technique model."""
    __tablename__ = "mitre_techniques"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Technique identification
    technique_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)  # T1234 or T1234.001
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Hierarchy
    tactic_id: Mapped[str] = mapped_column(String(20), ForeignKey("mitre_tactics.tactic_id"), nullable=False, index=True)
    is_subtechnique: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_technique_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("mitre_techniques.technique_id"), nullable=True, index=True)
    
    # Platforms
    platforms: Mapped[List[MITREPlatform]] = mapped_column(JSON, nullable=False)
    
    # Data sources
    data_sources: Mapped[List[MITREDataSource]] = mapped_column(JSON, nullable=False)
    
    # Detection
    detection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detection_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Mitigation
    mitigations: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Mitigation IDs
    
    # References
    references: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)  # [{url, description}]
    
    # Metadata
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deprecated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Coverage tracking
    detection_coverage: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)  # 0-100
    detection_rules: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Rule IDs
    
    # Relationships
    tactic: Mapped["MITRETactic"] = relationship("MITRETactic", back_populates="techniques", lazy="selectin")
    parent_technique: Mapped[Optional["MITRETechnique"]] = relationship("MITRETechnique", remote_side=[technique_id], lazy="selectin")
    subtechniques: Mapped[List["MITRETechnique"]] = relationship("MITRETechnique", back_populates="parent_technique", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_mitre_techniques_tactic_platform", "tactic_id", "platforms"),
        Index("ix_mitre_techniques_parent", "parent_technique_id"),
        Index("ix_mitre_techniques_deprecated", "deprecated"),
    )
    
    def __repr__(self) -> str:
        return f"<MITRETechnique(technique_id={self.technique_id}, name={self.name}, tactic={self.tactic_id})>"


class MITRETactic(Base):
    """MITRE ATT&CK tactic model."""
    __tablename__ = "mitre_tactics"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Tactic identification
    tactic_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)  # TA0001
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # initial-access, execution, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Order in kill chain
    kill_chain_order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Color for visualization
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # Hex color
    
    # Metadata
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Coverage tracking
    technique_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    covered_technique_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coverage_percentage: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)  # 0-100
    
    # Relationships
    techniques: Mapped[List["MITRETechnique"]] = relationship("MITRETechnique", back_populates="tactic", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_mitre_tactics_order", "kill_chain_order"),
    )
    
    def __repr__(self) -> str:
        return f"<MITRETactic(tactic_id={self.tactic_id}, name={self.name}, short_name={self.short_name})>"


class MITREGroup(Base):
    """MITRE ATT&CK group (threat actor) model."""
    __tablename__ = "mitre_groups"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Group identification
    group_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)  # G0001
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Associated techniques
    techniques: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # Technique IDs
    
    # Software used
    software: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Software IDs
    
    # References
    references: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deprecated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        return f"<MITREGroup(group_id={self.group_id}, name={self.name})>"


class MITRESoftware(Base):
    """MITRE ATT&CK software (malware/tool) model."""
    __tablename__ = "mitre_software"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Software identification
    software_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)  # S0001
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Type
    software_type: Mapped[str] = mapped_column(String(50), nullable=False)  # malware, tool
    
    # Platforms
    platforms: Mapped[List[MITREPlatform]] = mapped_column(JSON, nullable=False)
    
    # Associated techniques
    techniques: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # Technique IDs
    
    # Groups using this software
    groups: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Group IDs
    
    # References
    references: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deprecated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        return f"<MITRESoftware(software_id={self.software_id}, name={self.name}, type={self.software_type})>"


class MITRECoverage(Base):
    """MITRE ATT&CK coverage tracking for the organization."""
    __tablename__ = "mitre_coverage"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Technique reference
    technique_id: Mapped[str] = mapped_column(String(20), ForeignKey("mitre_techniques.technique_id"), nullable=False, index=True)
    
    # Coverage status
    status: Mapped[str] = mapped_column(String(20), default="none", nullable=False, index=True)  # none, partial, full
    coverage_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100
    
    # Detection rules
    detection_rules: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Rule IDs
    detection_log_sources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Data source names
    
    # Mitigations implemented
    mitigations_implemented: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Mitigation IDs
    
    # Assessment
    assessed_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assessment_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Next review
    next_review_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    technique: Mapped["MITRETechnique"] = relationship("MITRETechnique", lazy="selectin")
    assessed_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    
    __table_args__ = (
        Index("ix_mitre_coverage_status", "status"),
        Index("ix_mitre_coverage_score", "coverage_score"),
    )
    
    def __repr__(self) -> str:
        return f"<MITRECoverage(technique_id={self.technique_id}, status={self.status}, score={self.coverage_score})>"


class MITREMapping(Base):
    """Mapping between internal detections and MITRE techniques."""
    __tablename__ = "mitre_mappings"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Internal detection
    detection_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Internal rule/alert ID
    detection_name: Mapped[str] = mapped_column(String(255), nullable=False)
    detection_type: Mapped[str] = mapped_column(String(50), nullable=False)  # rule, alert, playbook, etc.
    
    # MITRE technique
    technique_id: Mapped[str] = mapped_column(String(20), ForeignKey("mitre_techniques.technique_id"), nullable=False, index=True)
    
    # Mapping confidence
    confidence: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # low, medium, high
    confidence_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)  # 0-100
    
    # Mapping details
    mapping_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mapped_fields: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Fields used for mapping
    
    # Validation
    validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validated_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    technique: Mapped["MITRETechnique"] = relationship("MITRETechnique", lazy="selectin")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id], lazy="selectin")
    validated_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[validated_by_id], lazy="selectin")
    
    __table_args__ = (
        Index("ix_mitre_mappings_detection", "detection_id", "detection_type"),
        Index("ix_mitre_mappings_technique", "technique_id"),
        Index("ix_mitre_mappings_confidence", "confidence"),
    )
    
    def __repr__(self) -> str:
        return f"<MITREMapping(detection_id={self.detection_id}, technique_id={self.technique_id}, confidence={self.confidence})>"