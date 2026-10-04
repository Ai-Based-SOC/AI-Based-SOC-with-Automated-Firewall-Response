"""
Threat Intelligence models.
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
from sqlalchemy.dialects.postgresql import UUID
from backend.app.models.ioc import IOCType, IOCSource, IOCStatus

from sqlalchemy.orm import Mapped, mapped_column, relationship



class ThreatIntelSource(str, enum.Enum):
    """Threat intelligence source types."""
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
    CUSTOM_API = "custom_api"
    INTERNAL = "internal"
    MANUAL = "manual"


class ThreatIntelType(str, enum.Enum):
    """Threat intelligence object types."""
    IP_REPUTATION = "ip_reputation"
    DOMAIN_REPUTATION = "domain_reputation"
    URL_REPUTATION = "url_reputation"
    FILE_REPUTATION = "file_reputation"
    MALWARE_ANALYSIS = "malware_analysis"
    VULNERABILITY = "vulnerability"
    THREAT_ACTOR = "threat_actor"
    CAMPAIGN = "campaign"
    MALWARE_FAMILY = "malware_family"
    TOOL = "tool"
    TECHNIQUE = "technique"


class ThreatIntel(Base):
    """Threat intelligence enrichment data."""
    __tablename__ = "threat_intel"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Target indicator
    indicator_value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    indicator_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ip, domain, url, hash
    
    # Source
    source: Mapped[ThreatIntelSource] = mapped_column(Enum(ThreatIntelSource), nullable=False, index=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Intelligence type
    intel_type: Mapped[ThreatIntelType] = mapped_column(Enum(ThreatIntelType), nullable=False, index=True)
    
    # Enrichment data
    data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Full enrichment response
    
    # Summary fields for quick querying
    reputation_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # -100 to 100
    confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    categories: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # malicious, suspicious, phishing, etc.
    
    # MITRE ATT&CK
    mitre_techniques: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    mitre_tactics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Related entities
    related_ips: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    related_domains: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    related_hashes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    related_actors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    related_campaigns: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    related_malware: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Timing
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Cache
    is_cached: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cache_hits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("ix_threat_intel_indicator_source", "indicator_value", "indicator_type", "source"),
        Index("ix_threat_intel_type_indicator", "intel_type", "indicator_type"),
        Index("ix_threat_intel_expires", "expires_at"),
        Index("ix_threat_intel_reputation", "reputation_score"),
    )
    
    def __repr__(self) -> str:
        return f"<ThreatIntel(id={self.id}, indicator={self.indicator_value}, type={self.indicator_type}, source={self.source.value})>"


class ThreatIntelRequest(Base):
    """Track threat intelligence lookup requests for rate limiting and caching."""
    __tablename__ = "threat_intel_requests"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Request info
    indicator_value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    indicator_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sources_requested: Mapped[List[ThreatIntelSource]] = mapped_column(JSON, nullable=False)
    
    # Requester
    requested_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    request_context: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # alert, incident, hunting, manual
    
    # Results
    sources_responded: Mapped[Optional[List[ThreatIntelSource]]] = mapped_column(JSON, nullable=True)
    results_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cache_hits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Performance
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    requester: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    
    __table_args__ = (
        Index("ix_threat_intel_requests_indicator_time", "indicator_value", "created_at"),
        Index("ix_threat_intel_requests_user_time", "requested_by_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ThreatIntelRequest(id={self.id}, indicator={self.indicator_value}, sources={len(self.sources_requested)})>"


class ThreatActor(Base):
    """Threat actor/group profiles."""
    __tablename__ = "threat_actors"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Classification
    actor_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # apt, cybercrime, hacktivist, insider, nation_state
    sophistication: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # low, medium, high, advanced
    motivation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # financial, espionage, sabotage, ideology
    
    # Attribution
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    known_tools: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    known_techniques: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # MITRE technique IDs
    target_sectors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    target_countries: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # References
    references: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    source: Mapped[ThreatIntelSource] = mapped_column(Enum(ThreatIntelSource), nullable=False)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ThreatActor(id={self.id}, name={self.name}, type={self.actor_type})>"


class Campaign(Base):
    """Threat campaign tracking."""
    __tablename__ = "campaigns"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Attribution
    threat_actor_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("threat_actors.id"), nullable=True)
    
    # Timeline
    first_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # IOCs and infrastructure
    associated_iocs: Mapped[Optional[List[UUID]]] = mapped_column(JSON, nullable=True)  # IOC IDs
    infrastructure: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # C2, hosting, domains
    
    # MITRE ATT&CK
    techniques: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    tactics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Targets
    target_sectors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    target_countries: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    victim_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # References
    references: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    source: Mapped[ThreatIntelSource] = mapped_column(Enum(ThreatIntelSource), nullable=False)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    threat_actor: Mapped[Optional[ThreatActor]] = relationship("ThreatActor", lazy="selectin")
    """Indicator of Compromise."""
    __tablename__ = "iocs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    ioc_type: Mapped[IOCType] = mapped_column(Enum(IOCType), nullable=False, index=True)
    source: Mapped[IOCSource] = mapped_column(Enum(IOCSource), nullable=False, index=True)
    status: Mapped[IOCStatus] = mapped_column(Enum(IOCStatus), default=IOCStatus.ACTIVE, nullable=False, index=True)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __repr__ = lambda self: f"<IOC(id={self.id}, value={self.value}, type={self.ioc_type.value}, source={self.source.value})>"
    
    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name}, active={self.is_active})>"