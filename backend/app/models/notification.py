"""
Notification models for multi-channel notifications.
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


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    PUSH = "push"
    IN_APP = "in_app"
    PAGERDUTY = "pagerduty"
    OPSGENIE = "opsgenie"
    VICTOROPS = "victorops"
    TELEGRAM = "telegram"
    DISCORD = "discord"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class NotificationStatus(str, enum.Enum):
    """Notification delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Notification(Base):
    """Notification model for multi-channel alerting."""
    __tablename__ = "notifications"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    notification_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Notification content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    html_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Classification
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # alert, incident, system, report, etc.
    priority: Mapped[NotificationPriority] = mapped_column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False, index=True)
    
    # Channels
    channels: Mapped[List[NotificationChannel]] = mapped_column(JSON, nullable=False)
    
    # Recipients
    recipient_users: Mapped[Optional[List[UUID]]] = mapped_column(JSON, nullable=True)  # User IDs
    recipient_emails: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    recipient_groups: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Role names, team names
    recipient_webhooks: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Related resources
    related_resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    related_resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Template
    template_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    template_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Delivery tracking
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Per-channel status
    channel_status: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {channel: status}
    channel_errors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {channel: error}
    
    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Retry
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    custom_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Created by
    created_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    
    __table_args__ = (
        Index("ix_notifications_category_priority", "category", "priority"),
        Index("ix_notifications_status_time", "status", "created_at"),
        Index("ix_notifications_scheduled", "scheduled_at"),
        Index("ix_notifications_resource", "related_resource_type", "related_resource_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, notification_id={self.notification_id}, title={self.title}, priority={self.priority.value})>"


class NotificationTemplate(Base):
    """Notification templates for reusable notification content."""
    __tablename__ = "notification_templates"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    template_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Template info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Template content
    subject_template: Mapped[str] = mapped_column(String(500), nullable=False)
    text_template: Mapped[str] = mapped_column(Text, nullable=False)
    html_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Default settings
    default_priority: Mapped[NotificationPriority] = mapped_column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
    default_channels: Mapped[List[NotificationChannel]] = mapped_column(JSON, nullable=False)
    
    # Variables
    variables: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)  # Variable definitions with types, defaults
    
    # Metadata
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Ownership
    created_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<NotificationTemplate(id={self.id}, template_id={self.template_id}, name={self.name})>"


class NotificationChannelConfig(Base):
    """Configuration for notification channels."""
    __tablename__ = "notification_channel_configs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Channel
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False, unique=True, index=True)
    
    # Configuration
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Channel-specific config (API keys, webhooks, etc.)
    
    # Settings
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority_override: Mapped[Optional[NotificationPriority]] = mapped_column(Enum(NotificationPriority), nullable=True)
    
    # Rate limiting
    rate_limit_per_minute: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rate_limit_per_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rate_limit_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Retry
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_test_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<NotificationChannelConfig(id={self.id}, channel={self.channel.value}, enabled={self.is_enabled})>"


class NotificationPreference(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Channel preferences
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    slack_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    teams_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Priority thresholds per channel
    email_min_priority: Mapped[NotificationPriority] = mapped_column(Enum(NotificationPriority), default=NotificationPriority.LOW, nullable=False)
    sms_min_priority: Mapped[NotificationPriority] = mapped_column(Enum(NotificationPriority), default=NotificationPriority.HIGH, nullable=False)
    slack_min_priority: Mapped[NotificationPriority] = mapped_column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
    teams_min_priority: Mapped[NotificationPriority] = mapped_column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
    push_min_priority: Mapped[NotificationPriority] = mapped_column(Enum(NotificationPriority), default=NotificationPriority.HIGH, nullable=False)
    in_app_min_priority: Mapped[NotificationPriority] = mapped_column(Enum(NotificationPriority), default=NotificationPriority.LOW, nullable=False)
    
    # Category preferences (JSON: {category: {channel: bool}})
    category_preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Quiet hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    quiet_hours_timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Digest
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    digest_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # daily, weekly
    digest_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<NotificationPreference(user_id={self.user_id})>"