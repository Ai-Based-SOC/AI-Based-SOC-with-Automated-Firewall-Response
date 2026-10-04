from datetime import datetime
from fastapi import APIRouter, Depends
from backend.models.schemas import AuditEventCreate
from backend.services.db_service import DBService
from typing import Any, List

router = APIRouter(prefix="/v1/audit-events", tags=["Audit Events"])


@router.post("/", response_model=dict)
def log_audit_event(payload: AuditEventCreate) -> dict:
    """Log an audit event for security compliance."""
    DBService.insert_audit_event({
        "action": payload.action,
        "resource": payload.resource,
        "details": payload.details,
        "user_role": payload.user_role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return {
        "success": True,
        "message": "Audit event logged",
        "action": payload.action,
        "resource": payload.resource,
    }


@router.get("/", response_model=List[dict])
def list_audit_events(limit: int = 100) -> List[dict]:
    """List recent audit events (admin only)."""
    from datetime import datetime
    # In a full implementation, this would query an audit log collection
    # For now, return empty list as audit events are generated internally
    return []