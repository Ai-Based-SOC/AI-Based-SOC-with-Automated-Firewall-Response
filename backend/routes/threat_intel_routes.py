import ipaddress

from backend.core.security import require_role
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.models.schemas import ThreatIntelResponse, ThreatIntelMetric
from pydantic import BaseModel

router = APIRouter(prefix="/v1/threat-intelligence", tags=["Threat Intelligence"])


def build_intel(ip: str):
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address")

    is_local = (
        ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10.")
    )
    return {
        "ip": ip,
        "reputation_score": 8 if is_local else 76,
        "malicious": False if is_local else True,
        "country": "Local/Private" if is_local else "Unknown",
        "isp": "Local Network" if is_local else "Unknown ISP",
        "source": "mock",
    }


class ThreatIntelRequest(BaseModel):
    ip: str


@router.get(
    "/check",
    response_model=ThreatIntelResponse,
    dependencies=[Depends(require_role(["admin", "analyst"]))],
)
def check_ip_get(ip: str = Query(..., description="IPv4/IPv6 address")):
    return build_intel(ip)


@router.post(
    "/check",
    response_model=ThreatIntelResponse,
    dependencies=[Depends(require_role(["admin", "analyst"]))],
)
def check_ip_post(payload: ThreatIntelRequest):
    return build_intel(payload.ip)


@router.get("/metrics", response_model=list[ThreatIntelMetric])
def threat_intel_metrics() -> list[ThreatIntelMetric]:
    """Get threat intelligence metric cards."""
    return [
        ThreatIntelMetric(label="Total IOCs", value="1542"),
        ThreatIntelMetric(label="Malicious IOCs", value="342"),
        ThreatIntelMetric(label="IP Reputation", value="76/100"),
        ThreatIntelMetric(label="Botnet C2", value="12"),
    ]


@router.get("/feed", response_model=list[dict])
def threat_intel_feed() -> list[dict]:
    """Get threat feed list."""
    from backend.services.db_service import DBService
    iocs = DBService.list_iocs(limit=50)
    return [
        {
            "id": ioc.get("id", ""),
            "type": ioc.get("type", "ip"),
            "value": ioc.get("value", ""),
            " reputation_score": ioc.get("reputation_score", 0),
            "first_seen": ioc.get("first_seen", ""),
        }
        for ioc in iocs
    ]