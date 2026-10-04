"""
Playbook models for SOAR automation.
"""
import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
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


class PlaybookStatus(str, enum.Enum):
    """Playbook status."""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class PlaybookTriggerType(str, enum.Enum):
    """Playbook trigger types."""
    MANUAL = "manual"
    ALERT_CREATED = "alert_created"
    ALERT_UPDATED = "alert_updated"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_UPDATED = "incident_updated"
    IOC_MATCH = "ioc_match"
    THREAT_INTEL_UPDATE = "threat_intel_update"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    API = "api"


class PlaybookStepType(str, enum.Enum):
    """Playbook step types."""
    # Actions
    BLOCK_IP = "block_ip"
    UNBLOCK_IP = "unblock_ip"
    ISOLATE_HOST = "isolate_host"
    QUARANTINE_FILE = "quarantine_file"
    KILL_PROCESS = "kill_process"
    DISABLE_USER = "disable_user"
    RESET_PASSWORD = "reset_password"
    CREATE_TICKET = "create_ticket"
    SEND_NOTIFICATION = "send_notification"
    RUN_SCRIPT = "run_script"
    HTTP_REQUEST = "http_request"
    ENRICH_IOC = "enrich_ioc"
    LOOKUP_THREAT_INTEL = "lookup_threat_intel"
    CREATE_INCIDENT = "create_incident"
    UPDATE_INCIDENT = "update_incident"
    ADD_EVIDENCE = "add_evidence"
    RUN_QUERY = "run_query"
    EXPORT_DATA = "export_data"
    
    # Logic
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    WAIT = "wait"
    APPROVAL = "approval"
    DECISION = "decision"
    
    # AI/ML
    AI_ANALYZE = "ai_analyze"
    AI_CLASSIFY = "ai_classify"
    AI_RISK_SCORE = "ai_risk_score"
    ANOMALY_DETECT = "anomaly_detect"


class PlaybookExecutionStatus(str, enum.Enum):
    """Playbook execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class PlaybookStepStatus(str, enum.Enum):
    """Playbook step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"


class Playbook(Base):
    """Playbook model for SOAR automation workflows."""
    __tablename__ = "playbooks"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    playbook_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # incident_response, threat_hunting, etc.
    
    # Status
    status: Mapped[PlaybookStatus] = mapped_column(Enum(PlaybookStatus), default=PlaybookStatus.DRAFT, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Trigger
    trigger_type: Mapped[PlaybookTriggerType] = mapped_column(Enum(PlaybookTriggerType), nullable=False, index=True)
    trigger_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Trigger-specific configuration
    
    # Execution settings
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)  # 1 hour default
    max_retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    continue_on_failure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Approval
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_roles: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    approval_users: Mapped[Optional[List[UUID]]] = mapped_column(JSON, nullable=True)
    approval_timeout_seconds: Mapped[int] = mapped_column(Integer, default=86400, nullable=False)  # 24 hours
    
    # Variables
    variables: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # Default variables
    input_schema: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSON schema for inputs
    output_schema: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSON schema for outputs
    
    # Steps (stored as ordered list)
    steps: Mapped[List[dict]] = mapped_column(JSON, nullable=False)  # List of step configurations
    
    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    mitre_techniques: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # MITRE ATT&CK technique IDs
    
    # Statistics
    execution_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    avg_execution_time_seconds: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)
    
    # Ownership
    created_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id], lazy="selectin")
    updated_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_id], lazy="selectin")
    executions: Mapped[List["PlaybookExecution"]] = relationship("PlaybookExecution", back_populates="playbook", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_playbooks_status_category", "status", "category"),
        Index("ix_playbooks_trigger", "trigger_type"),
        Index("ix_playbooks_created_by", "created_by_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Playbook(id={self.id}, playbook_id={self.playbook_id}, name={self.name}, status={self.status.value})>"


class PlaybookStep(Base):
    """Individual step within a playbook (for detailed tracking)."""
    __tablename__ = "playbook_steps"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    playbook_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Step identification
    step_id: Mapped[str] = mapped_column(String(100), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Step config
    step_type: Mapped[PlaybookStepType] = mapped_column(Enum(PlaybookStepType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Step-specific configuration
    
    # Flow control
    condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Jinja2 condition expression
    on_failure: Mapped[str] = mapped_column(String(20), default="stop", nullable=False)  # stop, continue, retry
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_delay: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    
    # Approval
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    playbook: Mapped["Playbook"] = relationship("Playbook", lazy="selectin")
    executions: Mapped[List["PlaybookStepExecution"]] = relationship("PlaybookStepExecution", back_populates="step", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_playbook_steps_playbook_order", "playbook_id", "step_order"),
        Index("ix_playbook_steps_type", "step_type"),
    )
    
    def __repr__(self) -> str:
        return f"<PlaybookStep(playbook_id={self.playbook_id}, step_id={self.step_id}, order={self.step_order})>"


class PlaybookExecution(Base):
    """Playbook execution instance."""
    __tablename__ = "playbook_executions"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Playbook reference
    playbook_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("playbooks.id"), nullable=False, index=True)
    playbook_version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Trigger info
    trigger_type: Mapped[PlaybookTriggerType] = mapped_column(Enum(PlaybookTriggerType), nullable=False)
    trigger_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Data that triggered execution
    
    # Status
    status: Mapped[PlaybookExecutionStatus] = mapped_column(Enum(PlaybookExecutionStatus), default=PlaybookExecutionStatus.PENDING, nullable=False, index=True)
    
    # Input/Output
    input_variables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_variables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Execution context
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Runtime context
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_step_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Approval
    approval_requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approval_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Initiated by
    initiated_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    initiated_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    playbook: Mapped["Playbook"] = relationship("Playbook", back_populates="executions", lazy="selectin")
    initiated_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[initiated_by_id], lazy="selectin")
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id], lazy="selectin")
    step_executions: Mapped[List["PlaybookStepExecution"]] = relationship("PlaybookStepExecution", back_populates="execution", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_playbook_executions_playbook_status", "playbook_id", "status"),
        Index("ix_playbook_executions_initiated_by", "initiated_by_id"),
        Index("ix_playbook_executions_started", "started_at"),
    )
    
    def __repr__(self) -> str:
        return f"<PlaybookExecution(id={self.id}, execution_id={self.execution_id}, playbook_id={self.playbook_id}, status={self.status.value})>"


class PlaybookStepExecution(Base):
    """Individual step execution within a playbook execution."""
    __tablename__ = "playbook_step_executions"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # References
    execution_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("playbook_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("playbook_steps.id"), nullable=False, index=True)
    
    # Step identification
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[PlaybookStepType] = mapped_column(Enum(PlaybookStepType), nullable=False)
    step_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status
    status: Mapped[PlaybookStepStatus] = mapped_column(Enum(PlaybookStepStatus), default=PlaybookStepStatus.PENDING, nullable=False, index=True)
    
    # Input/Output
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Approval
    approval_requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approval_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    execution: Mapped["PlaybookExecution"] = relationship("PlaybookExecution", back_populates="step_executions", lazy="selectin")
    step: Mapped["PlaybookStep"] = relationship("PlaybookStep", back_populates="executions", lazy="selectin")
    approved_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    
    __table_args__ = (
        Index("ix_playbook_step_executions_execution_order", "execution_id", "step_order"),
        Index("ix_playbook_step_executions_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<PlaybookStepExecution(execution_id={self.execution_id}, step={self.step_name}, status={self.status.value})>"