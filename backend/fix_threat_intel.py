with open('C:/Users/abhishek/Downloads/ai-based soc/backend/app/api/v1/threat_intel_new.py', 'r') as f:
    content = f.read()

old = '''return [ThreatIntelEnrichmentResponse(**r) for r in results]


@router.delete("/iocs/{ioc_id}", response_model=MessageResponse, summary="Delete IOC")
def delete_ioc(
    ioc_id: int,
    current_user: User = Depends(require_permission("threat_intel:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete an IOC (admin only).
    """
    ti_service = ThreatIntelService(db)
    ti_service.delete_ioc(ioc_id)

    return MessageResponse(message="IOC deleted successfully")


# =========================================================
# Threat Intelligence Sources
# ========================================================='''

new = '''return [ThreatIntelEnrichmentResponse(**r) for r in results]


# =========================================================
# Threat Intel + Firewall Integration
# =========================================================

from backend.app.core.config import settings
from backend.app.schemas.common import BaseSchema, Field


class AutoBlockTriggerRequest(BaseSchema):
    """Request to trigger auto-block for an IOC."""
    ioc_id: int
    reason: str = Field(default="Threat intelligence auto-block", min_length=2, max_length=500)


class AutoBlockTriggerResponse(BaseSchema):
    """Response from auto-block trigger."""
    success: bool
    message: str
    ioc_value: str
    rule_id: str | None = None
    expires_at: str | None = None


@router.post("/iocs/{ioc_id}/auto-block", response_model=AutoBlockTriggerResponse, summary="Trigger auto-block for IOC")
def trigger_auto_block(
    ioc_id: int,
    request: AutoBlockTriggerRequest,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> AutoBlockTriggerResponse:
    """
    Manually trigger firewall block for an IOC based on threat intelligence.

    This endpoint allows analysts to manually trigger the firewall integration
    for a specific IOC that has been enriched with threat intelligence.
    """
    ti_service = ThreatIntelService(db)
    ioc = ti_service.get_ioc(ioc_id)

    if not ioc:
        raise NotFoundError("IOC not found")

    if ioc.ioc_type != "ip":
        raise ValidationError("Only IP addresses can be blocked")

    # Trigger the auto-block
    result = ti_service._auto_block_ioc(ioc, current_user.id, db)

    return AutoBlockTriggerResponse(**result)


@router.get("/iocs/{ioc_id}/auto-block/check", summary="Check if IOC meets auto-block criteria")
def check_auto_block_criteria(
    ioc_id: int,
    current_user: User = Depends(require_permission("threat_intel:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Check if an IOC meets the criteria for auto-blocking without actually blocking.

    Returns the evaluation of auto-block thresholds against the IOC's
    threat intelligence enrichment results.
    """
    ti_service = ThreatIntelService(db)
    ioc = ti_service.get_ioc(ioc_id)

    if not ioc:
        raise NotFoundError("IOC not found")

    should_block = ti_service._should_auto_block(ioc)

    return {
        "ioc_value": ioc.value,
        "ioc_type": ioc.ioc_type,
        "confidence": ioc.confidence,
        "severity": ioc.severity,
        "confidence_threshold": settings.THREAT_INTEL_AUTO_BLOCK_CONFIDENCE_THRESHOLD,
        "severity_threshold": settings.THREAT_INTEL_AUTO_BLOCK_SEVERITY_THRESHOLD,
        "auto_block_enabled": settings.THREAT_INTEL_AUTO_BLOCK_ENABLED,
        "meets_criteria": should_block,
        "reason": (
            "Auto-block disabled" if not settings.THREAT_INTEL_AUTO_BLOCK_ENABLED else
            "Not an IP address" if ioc.ioc_type != "ip" else
            f"Confidence {ioc.confidence}% below threshold {settings.THREAT_INTEL_AUTO_BLOCK_CONFIDENCE_THRESHOLD}%" if ioc.confidence < settings.THREAT_INTEL_AUTO_BLOCK_CONFIDENCE_THRESHOLD else
            f"Severity {ioc.severity} below threshold {settings.THREAT_INTEL_AUTO_BLOCK_SEVERITY_THRESHOLD}" if 
            {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(ioc.severity.lower(), 1) < 
            {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(settings.THREAT_INTEL_AUTO_BLOCK_SEVERITY_THRESHOLD.lower(), 3) else
            "Meets all criteria"
        ),
    }


@router.delete("/iocs/{ioc_id}", response_model=MessageResponse, summary="Delete IOC")
def delete_ioc(
    ioc_id: int,
    current_user: User = Depends(require_permission("threat_intel:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete an IOC (admin only).
    """
    ti_service = ThreatIntelService(db)
    ti_service.delete_ioc(ioc_id)

    return MessageResponse(message="IOC deleted successfully")


# =========================================================
# Threat Intelligence Sources
# ========================================================='''

if old in content:
    content = content.replace(old, new)
    with open('C:/Users/abhishek/Downloads/ai-based soc/backend/app/api/v1/threat_intel_new.py', 'w') as f:
        f.write(content)
    print('Replacement successful')
else:
    print('Old text not found')
    print('Searching for partial match...')
    if 'return [ThreatIntelEnrichmentResponse(**r) for r in results]' in content:
        print('Found return statement')
    if '@router.delete("/iocs/{ioc_id}"' in content:
        print('Found delete route')