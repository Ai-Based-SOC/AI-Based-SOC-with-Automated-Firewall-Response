"""
IOC (Indicator of Compromise) models for threat intelligence.
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class IOCType(str, enum.Enum):
    """IOC types."""
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    HASH_MD5 = "hash_md5"
    HASH_SHA1 = "hash_sha1"
    HASH_SHA256 = "hash_sha256"
    HASH_SHA512 = "hash_sha512"
    EMAIL = "email"
    CIDR = "cidr"
    ASN = "asn"
    REGISTRY_KEY = "registry_key"
    FILE_PATH = "file_path"
    MUTEX = "mutex"
    USER_AGENT = "user_agent"
    CERTIFICATE = "certificate"
    JA3 = "ja3"
    JA3S = "ja3s"


class IOCSource(str, enum.Enum):
    """IOC source types."""
    INTERNAL = "internal"
    VIRUSTOTAL = "virustotal"
    ABUSEIPDB = "abuseipdb"
    ALIENVAULT_OTX = "alienvault_otx"
    URLHAUS = "urlhaus"
    PHISHTANK = "phishtank"
    MALWAREBAZAAR = "malwarebazaar"
    THREATFOX = "threatfox"
    FEEDLY = "feedly"
    MISP = "misp"
    STIX_TAXII = "stix_taxii"
    CUSTOM_FEED = "custom_feed"
    MANUAL = "manual"


class IOCStatus(str, enum.Enum):
    """IOC status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FALSE_POSITIVE = "false_positive"
    WHITELISTED = "whitelisted"


class IOC(Base):
    """Indicator of Compromise model."""
    __tablename__ = "iocs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    ioc_type: Mapped[IOCType] = mapped_column(Enum(IOCType), nullable=False, index=True)
    
    # Source info
    source: Mapped[IOCSource] = mapped_column(Enum(IOCSource), nullable=False, index=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Reference ID in source
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Classification
    threat_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # malware, phishing, botnet, etc.
    malware_family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    actor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Confidence and severity
    confidence: Mapped[int] = mapped_column(Integer, default=50, nullable=False)  # 0-100
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # low, medium, high, critical
    
    # Status
    status: Mapped[IOCStatus] = mapped_column(Enum(IOCStatus), default=IOCStatus.ACTIVE, nullable=False, index=True)
    
    # Timing
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # MITRE ATT&CK
    mitre_techniques: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    mitre_tactics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Enrichment data
    enrichment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # GeoIP, WHOIS, passive DNS, etc.
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    sightings: Mapped[List["IOCSighting"]] = relationship("IOCSighting", back_populates="ioc", lazy="dynamic")
    alerts: Mapped[List["Alert"]] = relationship("Alert", secondary="alert_ioc_matches", back_populates="matched_iocs", lazy="dynamic")
    
    # Metadata
    created_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("value", "ioc_type", "source", name="uq_ioc_value_type_source"),
        Index("ix_iocs_type_status", "ioc_type", "status"),
        Index("ix_iocs_threat_type", "threat_type"),
        Index("ix_iocs_expires", "expires_at"),
        Index("ix_iocs_confidence", "confidence"),
    )
    
    def __repr__(self) -> str:
        return f"<IOC(id={self.id}, value={self.value}, type={self.ioc_type.value}, source={self.source.value})>"


class IOCSighting(Base):
    """IOC sighting in logs/alerts."""
    __tablename__ = "ioc_sightings"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ioc_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("iocs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Where it was seen
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # log, alert, network, endpoint
    source_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)  # LogEntry ID, Alert ID, etc.
    source_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Context
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    matched_field: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # source_ip, destination_ip, file_hash, etc.
    
    # Count
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Timing
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    ioc: Mapped[IOC] = relationship("IOC", back_populates="sightings", lazy="selectin")
    
    __table_args__ = (
        Index("ix_ioc_sightings_ioc_time", "ioc_id", "first_seen"),
        Index("ix_ioc_sightings_source", "source_type", "source_id"),
    )
    
    def __repr__(self) -> str:
        return f"<IOCSighting(id={self.id}, ioc_id={self.ioc_id}, source={self.source_type})>"


class ThreatFeed(Base):
    """Threat intelligence feed configuration."""
    __tablename__ = "threat_feeds"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[IOCSource] = mapped_column(Enum(IOCSource), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Feed config
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Encrypted
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Additional config
    
    # Parsing
    format: Mapped[str] = mapped_column(String(50), default="json", nullable=False)  # json, csv, stix, txt
    parser_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    max_iocs_per_poll: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    default_confidence: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    default_severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Filtering
    ioc_types: Mapped[Optional[List[IOCType]]] = mapped_column(JSON, nullable=True)  # Only ingest these types
    min_confidence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    exclude_tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Health
    last_polled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consecutive_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Stats
    total_iocs_ingested: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_iocs_new: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_iocs_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_iocs_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ThreatFeed(id={self.id}, name={self.name}, source={self.source.value})>"