from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from backend.models.schemas import IncidentCreate, IncidentResponse
from backend.services.db_service import DBService
from typing import List, Any

router = APIRouter(prefix="/v1/incidents", tags=["Incidents"])


@router.get("/", response_model=List[IncidentResponse])
def list_incidents() -> List[IncidentResponse]:
    """List all incidents."""
    attacks = DBService.list_attacks(limit=1000)
    # Map attack fields to incident response model
    results = []
    for a in attacks:
        results.append(IncidentResponse(
            id=str(a.get("id", "")),
            title=a.get("attack_type", "Unnamed Incident"),
            description=a.get("raw_message", ""),
            source_ip=a.get("source_ip", "0.0.0.0"),
            severity=a.get("severity", "low"),
            status=a.get("status", "open"),
            assigned_to=a.get("assigned_to", ""),
            created_at=a.get("timestamp", ""),
        ))
    return results


@router.post("/", response_model=IncidentResponse)
def create_incident(payload: IncidentCreate) -> IncidentResponse:
    """Create a new incident."""
    attack = DBService.insert_attack({
        "attack_type": payload.title,
        "source_ip": payload.source_ip,
        "severity": payload.severity,
        "status": payload.status,
        "raw_message": payload.description or "",
        "timestamp": datetime.now(timezone.utc),
    })
    return IncidentResponse(
        id=str(attack.get("id", "")),
        title=payload.title,
        description=payload.description,
        source_ip=payload.source_ip,
        severity=payload.severity,
        status=payload.status,
        assigned_to=payload.assigned_to or "",
        created_at=attack.get("timestamp", "").isoformat() if hasattr(attack.get("timestamp"), 'isoformat') else str(attack.get("timestamp", "")),
    )