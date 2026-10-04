from fastapi import APIRouter, Depends
from backend.models.schemas import DashboardKPI, IncidentCreate, IncidentResponse, ThreatIntelMetric, SystemHealthMetric, SimulationRequest, AuditEventCreate
from backend.services.db_service import DBService
from typing import List, Dict, Any

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard"])


@router.get("/kpi", response_model=List[DashboardKPI])
def get_dashboard_kpi() -> List[DashboardKPI]:
    """Get KPI data for dashboard."""
    attacks = DBService.list_attacks(limit=1000)
    incidents = DBService.list_attacks(limit=1000)  # reuse attacks collection for incidents

    # Blocked IPs (simulated - count unique IPs from attacks)
    blocked_ips = len(set(a.get("source_ip", "") for a in attacks if a.get("severity") in ("high", "critical")))

    # Active incidents
    active_incidents = len([a for a in attacks if a.get("status") in ("open", "investigating")])

    # Assets monitored
    assets_monitored = 892  # seeded value

    # Threat intel matches
    threat_intel_matches = 34  # seeded value from threat intel

    kpis = [
        DashboardKPI(label="Blocked IPs", value=blocked_ips, kind="critical", icon="ShieldAlert"),
        DashboardKPI(label="Active Incidents", value=active_incidents, kind="warning", icon="AlertTriangle"),
        DashboardKPI(label="Assets Monitored", value=assets_monitored, kind="info", icon="Activity"),
        DashboardKPI(label="Threat Intel Matches", value=threat_intel_matches, kind="good", icon="BrainCircuit"),
    ]
    return kpis


@router.get("/incidents-summary", response_model=Dict[str, Any])
def get_incidents_summary() -> Dict[str, Any]:
    """Get incidents summary for dashboard."""
    attacks = DBService.list_attacks(limit=1000)
    total = len(attacks)
    open_incidents = len([a for a in attacks if a.get("status") == "open"])
    investigating = len([a for a in attacks if a.get("status") == "investigating"])
    resolved = len([a for a in attacks if a.get("status") == "resolved"])
    severity_counts = {}
    for a in attacks:
        s = a.get("severity", "low")
        severity_counts[s] = severity_counts.get(s, 0) + 1
    return {
        "total": total,
        "open": open_incidents,
        "investigating": investigating,
        "resolved": resolved,
        "severity_counts": severity_counts,
    }