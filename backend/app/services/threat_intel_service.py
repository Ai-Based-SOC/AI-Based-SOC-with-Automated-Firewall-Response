"""Threat Intelligence Service.
Provides IOC management, auto-block functionality, and enrichment
integration with external providers.
"""

from typing import Optional

from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.models.ioc import IOC, IOCType, IOCStatus
from backend.app.services.firewall_service import FirewallService
from uuid import uuid4


class ThreatIntelService:
    """Service for threat intelligence operations."""

    def __init__(self, db: Session):
        self.db = db
        self.firewall_service = FirewallService(db)
def get_ioc(self, ioc_id: int) -> Optional[IOC]:
        """Get an IOC by ID."""
def _should_auto_block(self, ioc: IOC) -> bool:
        """Check whether an IOC meets the auto-block criteria."""
def _auto_block_ioc(self, ioc: IOC, user_id: UUID, db: Session) -> dict:
        """Auto-block an IOC by triggering firewall block."""
def get_stats(self) -> dict:
        """Get threat intelligence statistics."""
        from sqlalchemy import func, select

        # Total IOCs
        total_iocs = self.db.query(IOC).count()

        # By type
        type_counts = (
            self.db.query(IOCType, func.count(IOC.id))
            .join(IOC)
            .group_by(IOCType)
            .all()
        )

        # By severity
        severity_counts = (
            self.db.query(IOC.severity, func.count(IOC.id))
            .filter(IOC.severity.isnot(None))
            .group_by(IOC.severity)
            .all()
        )

        # Active IOCs
        active_iocs = self.db.query(IOC).filter(IOC.status == IOCStatus.ACTIVE).count()

        # Recent IOCs (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_iocs = self.db.query(IOC).filter(
            IOC.first_seen >= thirty_days_ago
        ).count()

        return {
            "total_iocs": total_iocs,
            "active_iocs": active_iocs,
            "recent_iocs": recent_iocs,
            "by_type": {str(t): c for t, c in type_counts},
            "by_severity": {s or "unknown": c for s, c in severity_counts},
        }
        # Only IP addresses can be auto-blocked
        if ioc.ioc_type != IOCType.IP:
            return {
                "success": False,
                "message": "Only IP addresses can be auto-blocked",
                "ioc_value": ioc.value,
                "rule_id": None,
            }

        # Check if already blocked
        existing_rule = self.db.query(FirewallRule).filter(
            FirewallRule.source_ip == ioc.value,
            FirewallRule.action == "block",
            FirewallRule.status == "active",
            FirewallRule.enabled == True,
        ).first()

        if existing_rule:
            return {
                "success": True,
                "message": "IOC is already blocked",
                "ioc_value": ioc.value,
                "rule_id": str(existing_rule.id),
            }

        # Trigger firewall block through FirewallService
        from backend.app.schemas.firewall import FirewallActionRequest

        request = FirewallActionRequest(
            ip_address=ioc.value,
            action="block",
            requested_by=user_id,
            reason=f"Threat intel auto-block: IOC {ioc.value} exceeds criteria",
            simulation_mode=False,
        )

        result = self.firewall_service.block_ip(request)

        return {
            "success": result.success,
            "message": result.message,
            "ioc_value": ioc.value,
            "rule_id": str(result.rule_id) if result.rule_id else None,
        }
        # Must have auto-block enabled
        if not settings.THREAT_INTEL_AUTO_BLOCK_ENABLED:
            return False

        # Only IP addresses can be auto-blocked
        if ioc.ioc_type != IOCType.IP:
            return False

        # Confidence must be above threshold
        if ioc.confidence < settings.THREAT_INTEL_AUTO_BLOCK_CONFIDENCE_THRESHOLD:
            return False

        # Severity must be at or above threshold
        severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        ioc_severity = (ioc.severity or "low").lower()
        threshold_severity = settings.THREAT_INTEL_AUTO_BLOCK_SEVERITY_THRESHOLD.lower()

        if severity_order.get(ioc_severity, 1) < severity_order.get(threshold_severity, 3):
            return False

        return True
        return self.db.query(IOC).filter(IOC.id == ioc_id).first()