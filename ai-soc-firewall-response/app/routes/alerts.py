from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..core.database import init_db, log_audit
from ..policy.engine import PolicyEngine

router = APIRouter(prefix="/api/v1", tags=["alerts"])

policy_engine = PolicyEngine()

class AlertIngest(BaseModel):
    id: str
    source_ip: str
    destination_ip: str
    attack_type: str
    severity: str
    timestamp: str
    raw_message: str

class TriageRequest(BaseModel):
    alert_id: str

class PolicyDecision(BaseModel):
    action: str
    duration_minutes: int
    ip: str
    reason: str
    analyst_approved: bool = False

@router.post("/alerts", status_code=202)
def ingest_alert(alert: AlertIngest):
    """Ingest a security alert from monitoring systems."""
    init_db()
    log_audit("alert_received", alert.source_ip, alert.id)
    return {"status": "received", "alert_id": alert.id, "type": alert.attack_type}

@router.post("/triage", response_model=dict)
def mock_llm_triage(req: TriageRequest):
    """Mock LLM triage provider - classifies alert severity."""
    return {
        "alert_id": req.alert_id,
        "severity": "high",
        "confidence": 0.92,
        "classification": "potential_threat"
    }

@router.post("/policy/determine", response_model=PolicyDecision)
def determine_response(policy_data: dict):
    """Deterministic response-policy engine."""
    alert_summary = {
        "attack_type": policy_data.get("attack_type", ""),
        "severity": policy_data.get("severity", ""),
        "source_ip": policy_data.get("source_ip", "")
    }
    decision = policy_engine.evaluate(alert_summary)
    if not decision:
        raise HTTPException(status_code=404, detail="No matching policy rule")
    
    decision_dict = {
        "action": decision.action,
        "duration_minutes": decision.duration_minutes,
        "ip": decision.target_ip,
        "reason": "Policy match: " + decision.rule_id,
        "analyst_approved": False
    }
    
    log_audit(decision.action, decision.target_ip, req.alert_id if 'req' in dir() else None)
    return decision_dict

@router.post("/approval/request", response_model=dict)
def request_analyst_approval(request: dict):
    """Analyst approval flow - returns pending status."""
    return {
        "request_id": request.get("id"),
        "status": "pending_analyst",
        "expires_at": "2026-01-01T00:00:00Z"
    }

@router.get("/audit/logs")
def get_audit_logs(limit: int = 100):
    """SQLite audit logs endpoint."""
    from ..core.database import DB_PATH
    import sqlite3
    import os
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, alert_id, action_taken, ip_address, timestamp, analyst_notes "
        "FROM audit_logs ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    logs = [
        {
            "id": row[0],
            "alert_id": row[1],
            "action_taken": row[2],
            "ip_address": row[3],
            "timestamp": row[4],
            "analyst_notes": row[5]
        }
        for row in rows
    ]
    return {"logs": logs, "count": len(logs), "limit": limit}

@router.post("/security/block-temp", response_model=dict)
def block_temporary_ip(block_data: dict):
    """Simulated temporary IP blocking."""
    ip = block_data.get("ip", "")
    duration = block_data.get("duration", "30m")
    
    log_audit("temp_block", ip, block_data.get("id"))
    
    return {
        "status": "simulated_block",
        "ip": ip,
        "duration": duration,
        "note": "Blocking simulated - no actual firewall changes"
    }