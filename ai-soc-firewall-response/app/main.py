from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI-SOC Firewall Response",
    description="Deterministic firewall response with analyst approval",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["root"])
def root():
    return {"message": "AI-SOC Firewall Response API", "status": "active"}

@app.post("/api/v1/alerts", tags=["alerts"])
def ingest_alert(alert: dict):
    """Ingest a security alert from monitoring systems."""
    return {"status": "received", "alert_id": alert.get("id"), "type": "alert"}

@app.post("/api/v1/triage", tags=["llm"])
def mock_llm_triage(alert_id: str):
    """Mock LLM triage provider - classifies alert severity."""
    return {
        "alert_id": alert_id,
        "severity": "high",
        "confidence": 0.92,
        "classification": "potential_threat"
    }

@app.post("/api/v1/policy/determine", tags=["policy"])
def determine_response(policy_data: dict):
    """Deterministic response-policy engine."""
    return {
        "action": "block_ip",
        "duration_minutes": 30,
        "ip": policy_data.get("source_ip"),
        "reason": "Detected attack pattern"
    }

@app.post("/api/v1/approval/request", tags=["approval"])
def request_analyst_approval(request: dict):
    """Analyst approval flow - returns pending status."""
    return {
        "request_id": request.get("id"),
        "status": "pending_analyst",
        "expires_at": "2024-01-01T00:00:00Z"
    }

@app.get("/api/v1/audit/logs", tags=["audit"])
def get_audit_logs(limit: int = 100):
    """SQLite audit logs endpoint."""
    return {"logs": [], "count": 0, "limit": limit}

@app.post("/api/v1/security/block-temp", tags=["blocking"])
def block_temporary_ip(block_data: dict):
    """Simulated temporary IP blocking."""
    return {
        "status": "simulated_block",
        "ip": block_data.get("ip"),
        "duration": block_data.get("duration", "30m"),
        "note": "Blocking simulated - no actual firewall changes"
    }