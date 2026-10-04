"""
Asset Management Service.

Provides asset inventory CRUD, vulnerability tracking, discovery, and
statistics for asset management.
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.models.asset import (
    Asset,
    AssetCriticality,
    AssetStatus,
    AssetType,
    AssetVulnerability,
)
from backend.app.schemas.common import (
    AssetCreate,
    AssetUpdate,
)


class AssetService:
    """Service for managing assets."""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Query ====================

    def list_assets(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        criticality: Optional[AssetCriticality] = None,
        status: Optional[str] = None,
        environment: Optional[str] = None,
        owner_id: Optional[int] = None,
        has_vulnerabilities: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Asset], int]:
        """List assets with pagination and filtering."""
        query = self.db.query(Asset)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Asset.name.ilike(term),
                    Asset.description.ilike(term),
                    Asset.fqdn.ilike(term),
                    Asset.asset_id.ilike(term),
                )
            )
        if asset_type:
            query = query.filter(Asset.asset_type == asset_type)
        if criticality:
            query = query.filter(Asset.criticality == criticality)
        if status:
            query = query.filter(Asset.status == status)
        if environment:
            query = query.filter(Asset.environment == environment)
        if owner_id is not None:
            query = query.filter(Asset.owner_id == owner_id)

        sort_column = getattr(Asset, sort_by, Asset.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        total = query.count()
        assets = query.offset((page - 1) * page_size).limit(page_size).all()

        if has_vulnerabilities is not None:
            assets = [
                a
                for a in assets
                if (len(a.vulnerabilities) > 0) == has_vulnerabilities
            ]

        return assets, total

    def get_asset(self, asset_id: int) -> Optional[Asset]:
        """Get an asset by ID."""
        return self.db.query(Asset).filter(Asset.id == asset_id).first()

    def get_stats(self) -> dict:
        """Get asset statistics."""
        query = self.db.query(Asset)
        total = query.count()
        return {
            "total": total,
            "active": query.filter(Asset.status == AssetStatus.ACTIVE).count(),
            "critical": query.filter(Asset.criticality == AssetCriticality.CRITICAL).count(),
        }

    def create_asset(self, asset_data: AssetCreate, user_id: UUID) -> Asset:
        """Create a new asset."""
        now = datetime.utcnow()
        asset = Asset(
            asset_id=f"AST-{now.strftime('%Y%m%d')}-{int(now.timestamp())}",
            name=asset_data.name,
            description=asset_data.description,
            asset_type=AssetType(asset_data.asset_type),
            criticality=AssetCriticality(asset_data.criticality),
            status=AssetStatus.ACTIVE,
            ip_addresses=asset_data.ip_addresses or [],
            hostnames=asset_data.hostnames or [],
            mac_addresses=asset_data.mac_addresses or [],
            operating_system=asset_data.operating_system,
            os_version=asset_data.os_version,
            location=asset_data.location,
            owner=asset_data.owner,
            tags=asset_data.tags or [],
            created_at=now,
            updated_at=now,
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def update_asset(
        self, asset_id: int, asset_data: AssetUpdate, user_id: UUID
    ) -> Optional[Asset]:
        """Update an asset."""
        asset = self.get_asset(asset_id)
        if not asset:
            return None
        update_data = asset_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "asset_type" and value:
                setattr(asset, field, AssetType(value))
            elif field == "criticality" and value:
                setattr(asset, field, AssetCriticality(value))
            else:
                setattr(asset, field, value)
        asset.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def delete_asset(self, asset_id: int) -> None:
        """Delete an asset."""
        asset = self.get_asset(asset_id)
        if not asset:
            raise NotFoundError("Asset not found")
        self.db.delete(asset)
        self.db.commit()

    # ==================== Vulnerabilities ====================

    def trigger_scan(self, asset_id: int, scan_type: str, user_id: UUID) -> dict:
        """Trigger a vulnerability scan for an asset."""
        asset = self.get_asset(asset_id)
        if not asset:
            raise NotFoundError("Asset not found")
        return {
            "scan_id": f"scan-{asset_id}-{int(datetime.utcnow().timestamp())}",
            "asset_id": asset_id,
            "scan_type": scan_type,
            "status": "initiated",
            "initiated_by": str(user_id),
        }

    def get_vulnerabilities(self, asset_id: int) -> List[dict]:
        """Get vulnerabilities for an asset."""
        vulns = (
            self.db.query(AssetVulnerability)
            .filter(AssetVulnerability.asset_id == asset_id)
            .all()
        )
        return [
            {
                "id": str(v.id),
                "cve_id": v.cve_id,
                "title": v.title,
                "severity": v.severity,
                "status": v.status,
            }
            for v in vulns
        ]

    # ==================== Discovery ====================

    def discover_assets(self, discovery_config: dict, user_id: UUID) -> dict:
        """Discover assets using network scanning or cloud APIs."""
        job_id = f"discovery-{int(datetime.utcnow().timestamp())}"
        return {
            "job_id": job_id,
            "status": "initiated",
            "config": discovery_config,
            "initiated_by": str(user_id),
        }

    def list_discovery_jobs(self) -> List[dict]:
        """List asset discovery jobs."""
        return []

    def get_discovery_job(self, job_id: int) -> dict:
        """Get status of a discovery job."""
        return {"job_id": job_id, "status": "unknown"}