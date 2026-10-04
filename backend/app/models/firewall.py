"""
Firewall models for automated firewall response.
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
from sqlalchemy.dialects.postgresql import UUID, INET, CIDR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class FirewallAction(str, enum.Enum):
    """Firewall action types."""
    BLOCK = "block"
    UNBLOCK = "unblock"
    ALLOW = "allow"
    DENY = "deny"
    RATE_LIMIT = "rate_limit"
    QUARANTINE = "quarantine"


class FirewallProvider(str, enum.Enum):
    """Supported firewall providers."""
    WINDOWS_FIREWALL = "windows_firewall"
    UFW = "ufw"
    IPTABLES = "iptables"
    PFSENSE = "pfsense"
    AWS_SECURITY_GROUP = "aws_security_group"
    AZURE_NSG = "azure_nsg"
    GCP_FIREWALL = "gcp_firewall"
    CISCO_ASA = "cisco_asa"
    PALO_ALTO = "palo_alto"
    FORTINET = "fortinet"
    CHECKPOINT = "checkpoint"
    CLOUDFLARE = "cloudflare"
    CUSTOM = "custom"


class FirewallRuleStatus(str, enum.Enum):
    """Firewall rule status."""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SIMULATED = "simulated"


class FirewallRule(Base):
    """Firewall rule model."""
    __tablename__ = "firewall_rules"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Rule details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action: Mapped[FirewallAction] = mapped_column(Enum(FirewallAction), nullable=False)
    provider: Mapped[FirewallProvider] = mapped_column(Enum(FirewallProvider), nullable=False, index=True)
    provider_rule_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)  # ID in the firewall system
    
    # Network targeting
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)  # Single IP or CIDR
    source_ips: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Multiple IPs/CIDRs
    destination_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    destination_ips: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    source_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    destination_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # tcp, udp, icmp, any
    direction: Mapped[str] = mapped_column(String(20), default="inbound", nullable=False)  # inbound, outbound, both
    
    # Rule metadata
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    status: Mapped[FirewallRuleStatus] = mapped_column(Enum(FirewallRuleStatus), default=FirewallRuleStatus.PENDING, nullable=False, index=True)
    
    # Approval workflow
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Simulation mode
    is_simulation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    simulation_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timing
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rollback_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Context
    created_by_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    incident_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True, index=True)
    alert_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=True, index=True)
    playbook_execution_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("playbook_executions.id"), nullable=True)
    
    # Raw data
    raw_rule: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Provider-specific rule format
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], lazy="selectin")
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id], lazy="selectin")
    rejector: Mapped[Optional["User"]] = relationship("User", foreign_keys=[rejected_by_id], lazy="selectin")
    incident: Mapped[Optional["Incident"]] = relationship("Incident", lazy="selectin")
    alert: Mapped[Optional["Alert"]] = relationship("Alert", lazy="selectin")
    playbook_execution: Mapped[Optional["PlaybookExecution"]] = relationship("PlaybookExecution", lazy="selectin")
    audit_logs: Mapped[List["FirewallAuditLog"]] = relationship("FirewallAuditLog", back_populates="rule", lazy="selectin", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_firewall_rules_provider_status", "provider", "status"),
        Index("ix_firewall_rules_source_ip_status", "source_ip", "status"),
        Index("ix_firewall_rules_expires", "expires_at"),
        Index("ix_firewall_rules_incident", "incident_id"),
    )
    
    def __repr__(self) -> str:
        return f"<FirewallRule(id={self.id}, rule_id={self.rule_id}, action={self.action.value}, provider={self.provider.value}, status={self.status.value})>"


class FirewallAuditLog(Base):
    """Audit log for firewall rule changes."""
    __tablename__ = "firewall_audit_logs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("firewall_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Action
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # created, applied, rolled_back, expired, approved, rejected, updated
    previous_status: Mapped[Optional[FirewallRuleStatus]] = mapped_column(Enum(FirewallRuleStatus), nullable=True)
    new_status: Mapped[Optional[FirewallRuleStatus]] = mapped_column(Enum(FirewallRuleStatus), nullable=True)
    
    # Details
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Provider response
    provider_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    rule: Mapped[FirewallRule] = relationship("FirewallRule", back_populates="audit_logs", lazy="selectin")
    user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    
    __table_args__ = (
        Index("ix_firewall_audit_rule_time", "rule_id", "created_at"),
        Index("ix_firewall_audit_user_time", "user_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<FirewallAuditLog(id={self.id}, rule_id={self.rule_id}, action={self.action})>"


class FirewallProviderConfig(Base):
    """Firewall provider configuration."""
    __tablename__ = "firewall_provider_configs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider: Mapped[FirewallProvider] = mapped_column(Enum(FirewallProvider), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Connection config (encrypted sensitive fields)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # host, port, api_key, credentials, etc.
    
    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    simulation_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_expire_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    max_rules: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    
    # Health check
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    health_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    health_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<FirewallProviderConfig(provider={self.provider.value}, name={self.name}, active={self.is_active})>"