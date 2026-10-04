from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.models.schemas import SystemHealthMetric
from backend.services.db_service import DBService
from typing import List, Any


router = APIRouter(prefix="/v1/system-health", tags=["System Health"])


@router.get("/metrics", response_model=list[SystemHealthMetric])
def system_health_metrics() -> list[SystemHealthMetric]:
    """Get system health metrics."""
    attacks = DBService.list_attacks(limit=1000)
    # Simulate resource metrics based on attack load
    total_alerts = len(attacks)
    blocked = len([a for a in attacks if a.get("severity") in ("high", "critical")])
    return [
        SystemHealthMetric(
            name="CPU Usage",
            value=65.0,
            status="good",
            trend="stable",
        ),
        SystemHealthMetric(
            name="Memory",
            value=80.0,
            status="good",
            trend="stable",
        ),
        SystemHealthMetric(
            name="Disk",
            value=75.0,
            status="good",
            trend="stable",
        ),
        SystemHealthMetric(
            name="Active Alerts",
            value=total_alerts,
            status="warning" if total_alerts > 100 else "good",
            trend="up" if total_alerts > 50 else "stable",
        ),
        SystemHealthMetric(
            name="Blocked Connections",
            value=blocked,
            status="good" if blocked < 200 else "warning",
            trend="up",
        ),
    ]


@router.get("/service-status", response_model=list[dict])
def service_status() -> list[dict]:
    """Get service status table."""
    return [
        {"service": "API", "status": "online", "response_time": "42ms"},
        {"service": "Database", "status": "online", "response_time": "15ms"},
        {"service": "Firewall", "status": "active", "response_time": "-" },
        {"service": "Threat Intel", "status": "online", "response_time": "210ms"},
        {"service": "SIEM", "status": "online", "response_time": "88ms"},
    ]