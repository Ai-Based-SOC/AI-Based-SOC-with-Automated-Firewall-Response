"""
Asset models for asset inventory management.
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
from sqlalchemy.dialects.postgresql import UUID, INET, CIDR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class AssetType(str, enum.Enum):
    """Asset types."""
    SERVER = "server"
    WORKSTATION = "workstation"
    LAPTOP = "laptop"
    MOBILE = "mobile"
    NETWORK_DEVICE = "network_device"
    FIREWALL = "firewall"
    ROUTER = "router"
    SWITCH = "switch"
    LOAD_BALANCER = "load_balancer"
    VPN = "vpn"
    PROXY = "proxy"
    DATABASE = "database"
    WEB_SERVER = "web_server"
    APP_SERVER = "app_server"
    MAIL_SERVER = "mail_server"
    DNS_SERVER = "dns_server"
    DHCP_SERVER = "dhcp_server"
    ACTIVE_DIRECTORY = "active_directory"
    CLOUD_INSTANCE = "cloud_instance"
    CONTAINER = "container"
    K8S_NODE = "k8s_node"
    K8S_POD = "k8s_pod"
    IOT_DEVICE = "iot_device"
    PRINTER = "printer"
    SCADA = "scada"
    OTHER = "other"


class AssetCriticality(str, enum.Enum):
    """Asset criticality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssetStatus(str, enum.Enum):
    """Asset status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"
    QUARANTINED = "quarantined"
    UNKNOWN = "unknown"


class OperatingSystem(str, enum.Enum):
    """Operating systems."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    IOS = "ios"
    ANDROID = "android"
    FREEBSD = "freebsd"
    SOLARIS = "solaris"
    AIX = "aix"
    VMWARE_ESXI = "vmware_esxi"
    CISCO_IOS = "cisco_ios"
    JUNOS = "junos"
    PANOS = "panos"
    FORTIOS = "fortios"
    OTHER = "other"


class Asset(Base):
    """Asset inventory model."""
    __tablename__ = "assets"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)  # Human-readable ID
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False, index=True)
    criticality: Mapped[AssetCriticality] = mapped_column(Enum(AssetCriticality), default=AssetCriticality.MEDIUM, nullable=False, index=True)
    status: Mapped[AssetStatus] = mapped_column(Enum(AssetStatus), default=AssetStatus.ACTIVE, nullable=False, index=True)
    
    # Network
    ip_addresses: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # List of IPs/CIDRs
    primary_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    mac_addresses: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    hostnames: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    fqdn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # OS and software
    operating_system: Mapped[Optional[OperatingSystem]] = mapped_column(Enum(OperatingSystem), nullable=True, index=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os_build: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Hardware
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    asset_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Location
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    datacenter: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rack: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cloud_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cloud_region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cloud_account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cloud_resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Ownership
    owner_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    owner_team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    business_unit: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Security
    is_internet_facing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dmz: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_agent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    agent_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # edr, av, monitoring
    last_agent_checkin: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Vulnerability
    vulnerability_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_vulns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_vulns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_vuln_scan: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Compliance
    compliance_frameworks: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # PCI, HIPAA, SOC2, etc.
    last_compliance_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Tags and metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Discovery
    discovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # scanner, manual, cmdb, cloud_api
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    decommissioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id], lazy="selectin")
    vulnerabilities: Mapped[List["AssetVulnerability"]] = relationship("AssetVulnerability", back_populates="asset", lazy="dynamic")
    software: Mapped[List["AssetSoftware"]] = relationship("AssetSoftware", back_populates="asset", lazy="dynamic")
    alerts: Mapped[List["Alert"]] = relationship("Alert", secondary="alert_asset_matches", back_populates="matched_assets", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_assets_type_status", "asset_type", "status"),
        Index("ix_assets_criticality_status", "criticality", "status"),
        Index("ix_assets_primary_ip", "primary_ip"),
        Index("ix_assets_owner", "owner_id"),
        Index("ix_assets_last_seen", "last_seen"),
    )
    
    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, asset_id={self.asset_id}, name={self.name}, type={self.asset_type.value})>"


class AssetVulnerability(Base):
    """Vulnerability found on an asset."""
    __tablename__ = "asset_vulnerabilities"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Vulnerability info
    cve_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # critical, high, medium, low, info
    cvss_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    cvss_vector: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Affected software
    software_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    software_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fixed_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False, index=True)  # open, mitigated, patched, accepted, false_positive
    remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Source
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # nessus, qualys, openvas, manual
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timing
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    patched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    asset: Mapped[Asset] = relationship("Asset", back_populates="vulnerabilities", lazy="selectin")
    
    __table_args__ = (
        Index("ix_asset_vulns_asset_severity", "asset_id", "severity"),
        Index("ix_asset_vulns_cve", "cve_id"),
        Index("ix_asset_vulns_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<AssetVulnerability(id={self.id}, asset_id={self.asset_id}, cve={self.cve_id}, severity={self.severity})>"


class AssetSoftware(Base):
    """Software installed on an asset."""
    __tablename__ = "asset_software"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Software info
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    install_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    install_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Type
    software_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # application, driver, update, hotfix, etc.
    is_managed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Source
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # registry, package_manager, manual
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    asset: Mapped[Asset] = relationship("Asset", back_populates="software", lazy="selectin")
    
    __table_args__ = (
        Index("ix_asset_software_asset_name", "asset_id", "name"),
        Index("ix_asset_software_name_version", "name", "version"),
    )
    
    def __repr__(self) -> str:
        return f"<AssetSoftware(id={self.id}, asset_id={self.asset_id}, name={self.name}, version={self.version})>"