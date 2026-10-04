"""
Alert Service for managing security alerts.

Provides CRUD operations, bulk actions, statistics, and alert lifecycle management.
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import desc, func, or_, and_
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.db.base import get_db_session
from backend.app.models.alert import Alert, AlertSeverity, AlertStatus, AlertSource
from backend.app.models.user import User
from backend.app.schemas.common import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    BulkActionRequest,
    BulkActionResponse,
    PaginatedResponse,
)


class AlertService:
    """Service for managing security alerts."""

    def __init__(self, db: Session):
        self.db = db

    def list_alerts(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
        rule_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Alert], int]:
        """List alerts with pagination, search, and filtering."""
        query = self.db.query(Alert)

        # Apply filters
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Alert.title.ilike(search_filter),
                    Alert.description.ilike(search_filter),
                    Alert.source_ip.ilike(search_filter),
                    Alert.destination_ip.ilike(search_filter),
                    Alert.alert_id.ilike(search_filter),
                )
            )

        if severity:
            query = query.filter(Alert.severity == severity)

        if status:
            query = query.filter(Alert.status == status)

        if source_ip:
            query = query.filter(Alert.source_ip == source_ip)

        if dest_ip:
            query = query.filter(Alert.destination_ip == dest_ip)

        if rule_id:
            query = query.filter(Alert.alert_id == rule_id)

        if start_date:
            query = query.filter(Alert.first_seen >= start_date)

        if end_date:
            query = query.filter(Alert.first_seen <= end_date)

        # Apply sorting
        sort_column = getattr(Alert, sort_by, Alert.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # Get total count
        total = query.count()

        # Apply pagination
        alerts = query.offset((page - 1) * page_size).limit(page_size).all()

        return alerts, total

    def get_alert(self, alert_id: UUID) -> Optional[Alert]:
        """Get an alert by ID."""
        return self.db.query(Alert).filter(Alert.id == alert_id).first()

    def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get alert statistics for dashboard."""
        query = self.db.query(Alert)

        if start_date:
            query = query.filter(Alert.first_seen >= start_date)
        if end_date:
            query = query.filter(Alert.first_seen <= end_date)

        total = query.count()
        critical = query.filter(Alert.severity == AlertSeverity.CRITICAL).count()
        high = query.filter(Alert.severity == AlertSeverity.HIGH).count()
        medium = query.filter(Alert.severity == AlertSeverity.MEDIUM).count()
        low = query.filter(Alert.severity == AlertSeverity.LOW).count()
        info = query.filter(Alert.severity == AlertSeverity.INFO).count()

        new = query.filter(Alert.status == AlertStatus.NEW).count()
        acknowledged = query.filter(Alert.status == AlertStatus.ACKNOWLEDGED).count()
        investigating = query.filter(Alert.status == AlertStatus.INVESTIGATING).count()
        resolved = query.filter(Alert.status == AlertStatus.TRUE_POSITIVE).count() + \
                   query.filter(Alert.status == AlertStatus.FALSE_POSITIVE).count()
        closed = query.filter(Alert.status == AlertStatus.CLOSED).count()
        escalated = query.filter(Alert.status == AlertStatus.ESCALATED).count()

        return {
            "total": total,
            "by_severity": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
                "info": info,
            },
            "by_status": {
                "new": new,
                "acknowledged": acknowledged,
                "investigating": investigating,
                "resolved": resolved,
                "closed": closed,
                "escalated": escalated,
            },
        }

    def create_alert(self, alert_data: AlertCreate) -> Alert:
        """Create a new alert."""
        try:
            alert = Alert(
                title=alert_data.title,
                description=alert_data.description,
                severity=AlertSeverity(alert_data.severity),
                status=AlertStatus.NEW,
                source=AlertSource.MANUAL,
                source_ref=None,
                source_ip=alert_data.source_ip,
                destination_ip=alert_data.destination_ip,
                protocol=None,
                mitre_techniques=alert_data.mitre_techniques or [],
                mitre_tactics=[],
                threat_intel_matches=None,
                ioc_matches=None,
                ml_score=None,
                confidence=None,
                risk_score=None,
                assigned_to_id=None,
                acknowledged_by_id=None,
                acknowledged_at=None,
                incident_id=None,
                raw_data=alert_data.raw_data,
                tags=[],
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            return alert
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create alert: {str(e)}")

    def update_alert(self, alert_id: UUID, alert_data: AlertUpdate, user_id: UUID) -> Optional[Alert]:
        """Update an alert."""
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        try:
            update_data = alert_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                if field == "severity" and value:
                    setattr(alert, field, AlertSeverity(value))
                elif field == "status" and value:
                    setattr(alert, field, AlertStatus(value))
                elif field == "assigned_to":
                    setattr(alert, "assigned_to_id", value)
                else:
                    setattr(alert, field, value)

            alert.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(alert)
            return alert
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update alert: {str(e)}")

    def acknowledge_alert(self, alert_id: UUID, user_id: UUID) -> Optional[Alert]:
        """Acknowledge an alert."""
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(alert)
        return alert