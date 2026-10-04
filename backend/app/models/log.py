"""
Log models for log collection and normalization.
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


class LogSourceType(str, enum.Enum):
    """Log source types."""
    WINDOWS_EVENT = "windows_event"
    LINUX_SYSLOG = "linux_syslog"
    APACHE = "apache"
    NGINX = "nginx"
    SURICATA = "suricata"
    SNORT = "snort"
    ZEEK = "zeek"
    PFSENSE = "pfsense"
    CISCO_ASA = "cisco_asa"
    AWS_CLOUDTRAIL = "aws_cloudtrail"
    AZURE_LOGS = "azure_logs"
    M365 = "m365"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    CUSTOM_JSON = "custom_json"
    FIREWALL = "firewall"
    WAF = "waf"
    EDR = "edr"
    PROXY = "proxy"
    DNS = "dns"
    DHCP = "dhcp"
    VPN = "vpn"
    DATABASE = "database"
    APPLICATION = "application"


class LogLevel(str, enum.Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class LogSource(Base):
    """Log source configuration."""
    __tablename__ = "log_sources"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[LogSourceType] = mapped_column(Enum(LogSourceType), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Connection config
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # host, port, path, credentials, etc.
    
    # Parsing config
    parser_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # regex, format, timezone, etc.
    normalization_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    batch_size: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    
    # Health
    last_polled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consecutive_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Stats
    total_logs_ingested: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_logs_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    log_entries: Mapped[List["LogEntry"]] = relationship("LogEntry", back_populates="source", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_log_sources_type_active", "source_type", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<LogSource(id={self.id}, name={self.name}, type={self.source_type.value})>"


class LogEntry(Base):
    """Normalized log entry."""
    __tablename__ = "log_entries"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("log_sources.id"), nullable=False, index=True)
    
    # Original log info
    raw_log: Mapped[str] = mapped_column(Text, nullable=False)
    raw_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    log_level: Mapped[Optional[LogLevel]] = mapped_column(Enum(LogLevel), nullable=True, index=True)
    
    # Normalized fields
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Network fields
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    source_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_user: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    destination_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    destination_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    destination_hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # HTTP fields
    http_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    http_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    http_user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    http_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    http_referrer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Process fields
    process_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    process_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    process_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    command_line: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_process_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parent_process_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # File fields
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)  # SHA256
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Authentication fields
    auth_user: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auth_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auth_result: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # success, failure, locked
    auth_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # password, key, mfa, etc.
    
    # DNS fields
    dns_query: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dns_query_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    dns_response_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    dns_answers: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Cloud fields
    cloud_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cloud_region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cloud_resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cloud_resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Kubernetes fields
    k8s_namespace: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    k8s_pod: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    k8s_container: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    k8s_node: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # MITRE ATT&CK
    mitre_techniques: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    mitre_tactics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Threat intelligence
    threat_intel_matches: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    ioc_matches: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # ML scoring
    ml_anomaly_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    ml_classification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Tags and metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    extra_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Additional parsed fields
    
    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processing_errors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    source: Mapped[LogSource] = relationship("LogSource", back_populates="log_entries", lazy="selectin")
    
    __table_args__ = (
        Index("ix_log_entries_timestamp", "timestamp"),
        Index("ix_log_entries_source_ip_time", "source_ip", "timestamp"),
        Index("ix_log_entries_dest_ip_time", "destination_ip", "timestamp"),
        Index("ix_log_entries_level_time", "log_level", "timestamp"),
        Index("ix_log_entries_file_hash", "file_hash"),
        Index("ix_log_entries_processed", "is_processed"),
    )
    
    def __repr__(self) -> str:
        return f"<LogEntry(id={self.id}, source_id={self.source_id}, timestamp={self.timestamp})>"