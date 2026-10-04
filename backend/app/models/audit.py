"""
Audit logging models.
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
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class AuditAction(str, enum.Enum):
    """Audit action types."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    MFA_CHALLENGE = "mfa_challenge"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILED = "mfa_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKED = "token_revoked"
    
    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ENABLE = "user_enable"
    USER_DISABLE = "user_disable"
    ROLE_ASSIGN = "role_assign"
    ROLE_REVOKE = "role_revoke"
    
    # Alert management
    ALERT_CREATE = "alert_create"
    ALERT_UPDATE = "alert_update"
    ALERT_ACKNOWLEDGE = "alert_acknowledge"
    ALERT_DISMISS = "alert_dismiss"
    ALERT_ESCALATE = "alert_escalate"
    ALERT_ASSIGN = "alert_assign"
    
    # Incident management
    INCIDENT_CREATE = "incident_create"
    INCIDENT_UPDATE = "incident_update"
    INCIDENT_CLOSE = "incident_close"
    INCIDENT_REOPEN = "incident_reopen"
    INCIDENT_ASSIGN = "incident_assign"
    INCIDENT_COMMENT = "incident_comment"
    INCIDENT_EVIDENCE_ADD = "incident_evidence_add"
    
    # Firewall
    FIREWALL_RULE_CREATE = "firewall_rule_create"
    FIREWALL_RULE_UPDATE = "firewall_rule_update"
    FIREWALL_RULE_DELETE = "firewall_rule_delete"
    FIREWALL_RULE_ENABLE = "firewall_rule_enable"
    FIREWALL_RULE_DISABLE = "firewall_rule_disable"
    FIREWALL_BLOCK_IP = "firewall_block_ip"
    FIREWALL_UNBLOCK_IP = "firewall_unblock_ip"
    FIREWALL_BULK_ACTION = "firewall_bulk_action"
    
    # Threat Intelligence
    THREAT_INTEL_LOOKUP = "threat_intel_lookup"
    THREAT_INTEL_IMPORT = "threat_intel_import"
    IOC_CREATE = "ioc_create"
    IOC_UPDATE = "ioc_update"
    IOC_DELETE = "ioc_delete"
    
    # Asset management
    ASSET_CREATE = "asset_create"
    ASSET_UPDATE = "asset_update"
    ASSET_DELETE = "asset_delete"
    ASSET_DISCOVER = "asset_discover"
    ASSET_SCAN = "asset_scan"
    
    # Configuration
    CONFIG_UPDATE = "config_update"
    SETTINGS_CHANGE = "settings_change"
    INTEGRATION_CONFIGURE = "integration_configure"
    
    # Reports
    REPORT_GENERATE = "report_generate"
    REPORT_DOWNLOAD = "report_download"
    REPORT_SCHEDULE = "report_schedule"
    
    # Playbook/SOAR
    PLAYBOOK_CREATE = "playbook_create"
    PLAYBOOK_UPDATE = "playbook_update"
    PLAYBOOK_DELETE = "playbook_delete"
    PLAYBOOK_EXECUTE = "playbook_execute"
    PLAYBOOK_APPROVE = "playbook_approve"
    PLAYBOOK_REJECT = "playbook_reject"
    
    # System
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    MAINTENANCE_MODE = "maintenance_mode"
    
    # Data access
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    BULK_DELETE = "bulk_delete"
    
    # API
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    API_ACCESS = "api_access"


class AuditEvent(Base):
    """Audit event log for compliance and security monitoring."""
    __tablename__ = "audit_events"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Event identification
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # auth, user, alert, incident, firewall, etc.
    
    # Actor
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    impersonated_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Request context
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Target resource
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Event details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Additional structured data
    
    # Outcome
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Risk
    risk_level: Mapped[str] = mapped_column(String(20), default="low", nullable=False, index=True)  # low, medium, high, critical
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    
    # Compliance
    compliance_tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # PCI, HIPAA, SOC2, GDPR
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    impersonator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[impersonated_by_id], lazy="selectin")
    
    __table_args__ = (
        Index("ix_audit_events_user_time", "user_id", "created_at"),
        Index("ix_audit_events_action_time", "action", "created_at"),
        Index("ix_audit_events_resource", "resource_type", "resource_id"),
        Index("ix_audit_events_success_time", "success", "created_at"),
        Index("ix_audit_events_risk_time", "risk_level", "created_at"),
        Index("ix_audit_events_request_id", "request_id"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditEvent(id={self.id}, action={self.action.value}, user={self.user_email}, success={self.success})>"