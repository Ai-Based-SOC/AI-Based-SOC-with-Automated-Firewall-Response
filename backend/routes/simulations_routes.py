from fastapi import APIRouter, Depends, HTTPException
from backend.models.schemas import SimulationRequest
from backend.services.db_service import DBService
from typing import Any

router = APIRouter(prefix="/v1/simulations", tags=["Simulations"])


@router.post("/dos", response_model=dict)
def dos_simulation(payload: SimulationRequest) -> dict:
    """Run a simulated DoS attack test (safe, synthetic only)."""
    # Validate target IP is RFC 5737 documentation range
    ip = payload.target_ip
    is_rfc5737 = (
        ip.startswith("192.0.2.") or  # TEST-NET-1
        ip.startswith("198.51.100.") or  # TEST-NET-2
        ip.startswith("203.0.113.") or  # TEST-NET-3
        ip in ("::1", "2001:db8::")  # IPv6 TEST-NET
    )
    if not is_rfc5737:
        raise HTTPException(
            status_code=400,
            detail="Simulation limited to RFC 5737 documentation IPs for safety",
        )

    # Record the simulation event as an audit event
    DBService.insert_audit_event({
        "action": "dos_simulation_started",
        "resource": f"target_ip={ip}, duration={payload.duration}",
        "details": payload.description or "DoS simulation training",
        "user_role": "analyst",
    })

    # Generate synthetic alert data (no real traffic)
    import json
    from datetime import datetime, timezone

    synthetic_alert = {
        "id": f"dos-{ip.replace('.', '-')}-{datetime.now(timezone.utc).timestamp()}",
        "source_ip": ip,
        "destination_ip": "10.0.0.1",
        "attack_type": "tcp_syn_flood",
        "severity": "high",
        "status": "generated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_score": 85,
        "simulated": True,
        "note": "No real traffic generated - simulation only",
    }

    # Store the synthetic alert
    DBService.insert_attack(synthetic_alert)

    return {
        "success": True,
        "message": "DoS simulation completed (synthetic only)",
        "alert": synthetic_alert,
        "banner": "No real traffic is generated during simulation",
    }


@router.get("/status", response_model=dict)
def simulation_status() -> dict:
    """Get simulation status and recent results."""
    attacks = DBService.list_attacks(limit=50)
    recent_dos = [a for a in attacks if a.get("attack_type") == "tcp_syn_flood" and a.get("simulated")]
    return {
        "simulation_mode": "active",
        "note": "All simulation endpoints generate synthetic alerts only. No real traffic is generated.",
        "recent_simulations": len(recent_dos),
        "total_simulations_today": len(recent_dos),
    }