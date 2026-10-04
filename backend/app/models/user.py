"""
User, Role, and Permission models for authentication and authorization.
"""
import enum
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Permission(str, enum.Enum):
    """System permissions."""
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    
    # Role management
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_LIST = "role:list"
    
    # Alert management
    ALERT_READ = "alert:read"
    ALERT_UPDATE = "alert:update"
    ALERT_ACKNOWLEDGE = "alert:acknowledge"
    ALERT_ASSIGN = "alert:assign"
    ALERT_LIST = "alert:list"
    
    # Incident management
    INCIDENT_CREATE = "incident:create"
    INCIDENT_READ = "incident:read"
    INCIDENT_UPDATE = "incident:update"
    INCIDENT_DELETE = "incident:delete"
    INCIDENT_ASSIGN = "incident:assign"
    INCIDENT_ESCALATE = "incident:escalate"
    INCIDENT_CLOSE = "incident:close"
    INCIDENT_LIST = "incident:list"
    
    # Firewall management
    FIREWALL_READ = "firewall:read"
    FIREWALL_BLOCK = "firewall:block"
    FIREWALL_UNBLOCK = "firewall:unblock"
    FIREWALL_RULE_CREATE = "firewall:rule:create"
    FIREWALL_RULE_UPDATE = "firewall:rule:update"
    FIREWALL_RULE_DELETE = "firewall:rule:delete"
    FIREWALL_LIST = "firewall:list"
    
    # Threat intelligence
    THREAT_INTEL_READ = "threat_intel:read"
    THREAT_INTEL_ENRICH = "threat_intel:enrich"
    THREAT_INTEL_MANAGE = "threat_intel:manage"
    
    # Asset management
    ASSET_READ = "asset:read"
    ASSET_CREATE = "asset:create"
    ASSET_UPDATE = "asset:update"
    ASSET_DELETE = "asset:delete"
    ASSET_LIST = "asset:list"
    
    # Log management
    LOG_READ = "log:read"
    LOG_SEARCH = "log:search"
    LOG_INGEST = "log:ingest"
    
    # Reporting
    REPORT_READ = "report:read"
    REPORT_CREATE = "report:create"
    REPORT_DOWNLOAD = "report:download"
    REPORT_LIST = "report:list"
    
    # Playbook/SOAR
    PLAYBOOK_READ = "playbook:read"
    PLAYBOOK_CREATE = "playbook:create"
    PLAYBOOK_UPDATE = "playbook:update"
    PLAYBOOK_DELETE = "playbook:delete"
    PLAYBOOK_EXECUTE = "playbook:execute"
    PLAYBOOK_LIST = "playbook:list"
    
    # Threat hunting
    HUNT_READ = "hunt:read"
    HUNT_CREATE = "hunt:create"
    HUNT_EXECUTE = "hunt:execute"
    
    # Administration
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_AUDIT = "admin:audit"
    ADMIN_SYSTEM = "admin:system"
    
    # ML/AI
    ML_PREDICT = "ml:predict"
    ML_TRAIN = "ml:train"
    ML_MANAGE = "ml:manage"


class Role(str, enum.Enum):
    """System roles."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SOC_MANAGER = "soc_manager"
    SENIOR_ANALYST = "senior_analyst"
    ANALYST = "analyst"
    JUNIOR_ANALYST = "junior_analyst"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


# Association tables

class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Security
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # MFA
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mfa_backup_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    
    # Password reset
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    email_verification_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    roles: Mapped[List["RoleModel"]] = relationship(
        "RoleModel",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )
    assigned_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        foreign_keys="UserRole.assigned_by",
        back_populates="assigner",
        lazy="selectin",
    )
    created_incidents: Mapped[List["Incident"]] = relationship(
        "Incident",
        foreign_keys="Incident.created_by_id",
        back_populates="creator",
        lazy="selectin",
    )
    assigned_incidents: Mapped[List["Incident"]] = relationship(
        "Incident",
        foreign_keys="Incident.assigned_to_id",
        back_populates="assignee",
        lazy="selectin",
    )
    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent",
        foreign_keys="AuditEvent.user_id",
        back_populates="user",
        lazy="selectin",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        foreign_keys="Notification.user_id",
        back_populates="user",
        lazy="selectin",
    )
    playbook_executions: Mapped[List["PlaybookExecution"]] = relationship(
        "PlaybookExecution",
        foreign_keys="PlaybookExecution.executed_by_id",
        back_populates="executor",
        lazy="selectin",
    )
    
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
        Index("ix_users_deleted_at", "deleted_at"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class RoleModel(Base):
    """Role model."""
    __tablename__ = "roles"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[Role] = mapped_column(Enum(Role), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)  # Higher = more privileges
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    users: Mapped[List[User]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )
    permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<RoleModel(name={self.name.value})>"


class PermissionModel(Base):
    """Permission model (for dynamic permission management)."""
    __tablename__ = "permissions"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[Permission] = mapped_column(Enum(Permission), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<PermissionModel(name={self.name.value})>"


class UserRole(Base):
    """User-Role assignment with metadata."""
    __tablename__ = "user_roles"
    
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    assigned_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    user: Mapped[User] = relationship("User", foreign_keys=[user_id], back_populates="assigned_roles")
    role: Mapped[RoleModel] = relationship("RoleModel", back_populates="user_assignments")
    assigner: Mapped[Optional[User]] = relationship("User", foreign_keys=[assigned_by])
    
    __table_args__ = (
        Index("ix_user_roles_user_active", "user_id", "is_active"),
        Index("ix_user_roles_expires", "expires_at"),
    )


class RolePermission(Base):
    """Role-Permission assignment."""
    __tablename__ = "role_permissions"
    
    role_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission: Mapped[Permission] = mapped_column(Enum(Permission), primary_key=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    granted_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    role: Mapped[RoleModel] = relationship("RoleModel", back_populates="permissions")
    grantor: Mapped[Optional[User]] = relationship("User", foreign_keys=[granted_by])