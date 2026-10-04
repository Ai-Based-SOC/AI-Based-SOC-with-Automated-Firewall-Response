"""
Threat Intelligence API routes.

Provides IOC management, enrichment, and integration with external providers.
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_permission
from backend.app.db.session import get_db
from backend.app.models.ioc import IOC
from backend.app.models.ioc import IOCType
from backend.app.models.threat_intel import ThreatIntelSource
from backend.app.models.user import User
from backend.app.schemas.common import (
    BaseSchema,
    IOCBulkCreate,
    IOCCreate,
    IOCResponse,
    IOCUpdate,
    MessageResponse,
    PaginatedResponse,
    ThreatIntelEnrichmentRequest,
    ThreatIntelEnrichmentResponse,
)
from backend.app.services.threat_intel_service import ThreatIntelService
from backend.app.services.firewall_service import FirewallService

router = APIRouter(prefix="/threat-intel", tags=["Threat Intelligence"])


@router.get("/iocs", response_model=PaginatedResponse[IOCResponse], summary="List IOCs")
def list_iocs(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query()] = None,
    ioc_type: Annotated[IOCType | None, Query()] = None,
    source: Annotated[ThreatIntelSource | None, Query()] = None,
    confidence_min: Annotated[int | None, Query(ge=0, le=100)] = None,
    severity: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    current_user: User = Depends(require_permission("threat_intel:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[IOCResponse]:
    """
    List IOCs with pagination, search, and filtering.
    """
    ti_service = ThreatIntelService(db)
    iocs, total = ti_service.list_iocs(
        page=page,
        page_size=page_size,
        search=search,
        ioc_type=ioc_type,
        source=source,
        confidence_min=confidence_min,
        severity=severity,
        is_active=is_active,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedResponse(
        items=[IOCResponse.model_validate(i) for i in iocs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/iocs/stats", summary="Get IOC statistics")
def get_ioc_stats(
    current_user: User = Depends(require_permission("threat_intel:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get IOC statistics for dashboard.
    """
    ti_service = ThreatIntelService(db)
    return ti_service.get_stats()


@router.get("/iocs/{ioc_id}", response_model=IOCResponse, summary="Get IOC by ID")
def get_ioc(
    ioc_id: int,
    current_user: User = Depends(require_permission("threat_intel:read")),
    db: Session = Depends(get_db),
) -> IOCResponse:
    """
    Get an IOC by ID.
    """
    ti_service = ThreatIntelService(db)
    ioc = ti_service.get_ioc(ioc_id)
    
    if not ioc:
        raise NotFoundError("IOC not found")
    
    return IOCResponse.model_validate(ioc)


@router.post("/iocs", response_model=IOCResponse, status_code=status.HTTP_201_CREATED, summary="Create IOC")
def create_ioc(
    ioc_data: IOCCreate,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> IOCResponse:
    """
    Create a new IOC.
    """
    ti_service = ThreatIntelService(db)
    ioc = ti_service.create_ioc(ioc_data, current_user.id)
    
    return IOCResponse.model_validate(ioc)


@router.post("/iocs/bulk", response_model=list[IOCResponse], status_code=status.HTTP_201_CREATED, summary="Bulk create IOCs")
def bulk_create_iocs(
    ioc_data: IOCBulkCreate,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> list[IOCResponse]:
    """
    Create multiple IOCs in bulk.
    """
    ti_service = ThreatIntelService(db)
    iocs = ti_service.bulk_create_iocs(ioc_data.iocs, current_user.id)
    
    return [IOCResponse.model_validate(i) for i in iocs]


@router.patch("/iocs/{ioc_id}", response_model=IOCResponse, summary="Update IOC")
def update_ioc(
    ioc_id: int,
    ioc_data: IOCUpdate,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> IOCResponse:
    """
    Update an IOC.
    """
    ti_service = ThreatIntelService(db)
    ioc = ti_service.update_ioc(ioc_id, ioc_data, current_user.id)
    
    if not ioc:
        raise NotFoundError("IOC not found")
    
    return IOCResponse.model_validate(ioc)


@router.post("/iocs/{ioc_id}/enrich", response_model=ThreatIntelEnrichmentResponse, summary="Enrich IOC")
def enrich_ioc(
    ioc_id: int,
    enrichment_request: ThreatIntelEnrichmentRequest | None = None,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> ThreatIntelEnrichmentResponse:
    """
    Enrich an IOC with external threat intelligence.
    """
    ti_service = ThreatIntelService(db)
    result = ti_service.enrich_ioc(ioc_id, enrichment_request)
    
    return ThreatIntelEnrichmentResponse(**result)


@router.post("/iocs/enrich", response_model=ThreatIntelEnrichmentResponse, summary="Enrich IOC by value")
def enrich_ioc_by_value(
    enrichment_request: ThreatIntelEnrichmentRequest,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> ThreatIntelEnrichmentResponse:
    """
    Enrich an IOC value with external threat intelligence.
    """
    ti_service = ThreatIntelService(db)
    result = ti_service.enrich_value(enrichment_request)
    
    return ThreatIntelEnrichmentResponse(**result)


@router.post("/iocs/bulk-enrich", response_model=list[ThreatIntelEnrichmentResponse], summary="Bulk enrich IOCs")
def bulk_enrich_iocs(
    enrichment_requests: list[ThreatIntelEnrichmentRequest],
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> list[ThreatIntelEnrichmentResponse]:
    """
    Enrich multiple IOCs in bulk.
    """
    ti_service = ThreatIntelService(db)
    results = ti_service.bulk_enrich(enrichment_requests)
    
    return [ThreatIntelEnrichmentResponse(**r) for r in results]


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
# =========================================================

@router.get("/sources", summary="List threat intelligence sources")
def list_sources(
    current_user: User = Depends(require_permission("threat_intel:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    List configured threat intelligence sources.
    """
    ti_service = ThreatIntelService(db)
    return ti_service.list_sources()


@router.get("/sources/{source_name}/status", summary="Get source status")
def get_source_status(
    source_name: str,
    current_user: User = Depends(require_permission("threat_intel:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get status of a threat intelligence source.
    """
    ti_service = ThreatIntelService(db)
    return ti_service.get_source_status(source_name)


@router.post("/sources/{source_name}/sync", summary="Sync threat intelligence source")
def sync_source(
    source_name: str,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Manually trigger sync for a threat intelligence source.
    """
    ti_service = ThreatIntelService(db)
    return ti_service.sync_source(source_name)


@router.post("/sources/{source_name}/test", summary="Test threat intelligence source")
def test_source(
    source_name: str,
    config: dict | None = None,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Test connection to a threat intelligence source.
    """
    ti_service = ThreatIntelService(db)
    return ti_service.test_source(source_name, config)


# =========================================================
# Feeds
# =========================================================

@router.get("/feeds", summary="List threat intelligence feeds")
def list_feeds(
    current_user: User = Depends(require_permission("threat_intel:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    List configured threat intelligence feeds.
    """
    ti_service = ThreatIntelService(db)
    return ti_service.list_feeds()


@router.post("/feeds", summary="Add threat intelligence feed")
def add_feed(
    feed_data: dict,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Add a new threat intelligence feed.
    """
    ti_service = ThreatIntelService(db)
    return ti_service.add_feed(feed_data)


@router.delete("/feeds/{feed_id}", response_model=MessageResponse, summary="Delete threat intelligence feed")
def delete_feed(
    feed_id: int,
    current_user: User = Depends(require_permission("threat_intel:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a threat intelligence feed.
    """
    ti_service = ThreatIntelService(db)
    ti_service.delete_feed(feed_id)
    
    return MessageResponse(message="Feed deleted successfully")


# =========================================================
# Auto-Block Endpoints
# =========================================================

class AutoBlockTriggerResponse(BaseSchema):
    """Response from an auto-block trigger."""

    success: bool
    message: str
    ioc_value: str
    rule_id: str | None = None
    expires_at: str | None = None


@router.post(
    "/iocs/{ioc_id}/auto-block",
    response_model=AutoBlockTriggerResponse,
    summary="Trigger auto-block for IOC",
)
def trigger_auto_block(
    ioc_id: int,
    current_user: User = Depends(require_permission("threat_intel:write")),
    db: Session = Depends(get_db),
) -> AutoBlockTriggerResponse:
    """Manually trigger a firewall block for an IOC based on threat intelligence.

    Evaluates the IOC against the auto-block criteria (enabled setting, IP type,
    confidence threshold, severity threshold) and, if met, triggers the firewall
    block through the threat intelligence service.
    """
    ti_service = ThreatIntelService(db)
    ioc = ti_service.get_ioc(ioc_id)

    if not ioc:
        raise NotFoundError("IOC not found")

    if ioc.ioc_type != IOCType.IP:
        raise ValidationError("Only IP addresses can be auto-blocked")

    if not ti_service._should_auto_block(ioc):
        return AutoBlockTriggerResponse(
            success=False,
            message="IOC does not meet auto-block criteria",
            ioc_value=ioc.value,
        )

    result = ti_service._auto_block_ioc(ioc, current_user.id, db)
    return AutoBlockTriggerResponse(**result)


@router.get(
    "/iocs/{ioc_id}/auto-block/check",
    summary="Check if IOC meets auto-block criteria",
)
def check_auto_block_criteria(
    ioc_id: int,
    current_user: User = Depends(require_permission("threat_intel:read")),
    db: Session = Depends(get_db),
) -> dict:
    """Check whether an IOC meets the auto-block criteria without blocking.

    Evaluates the enabled setting, IP type, confidence threshold, and severity
    threshold and returns the evaluation details.
    """
    ti_service = ThreatIntelService(db)
    ioc = ti_service.get_ioc(ioc_id)

    if not ioc:
        raise NotFoundError("IOC not found")

    should_block = ti_service._should_auto_block(ioc)

    severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    ioc_severity = (ioc.severity or "low").lower()
    threshold_severity = settings.THREAT_INTEL_AUTO_BLOCK_SEVERITY_THRESHOLD.lower()

    reasons = []
    if not settings.THREAT_INTEL_AUTO_BLOCK_ENABLED:
        reasons.append("Auto-block disabled")
    if ioc.ioc_type != IOCType.IP:
        reasons.append("Not an IP address")
    elif ioc.confidence < settings.THREAT_INTEL_AUTO_BLOCK_CONFIDENCE_THRESHOLD:
        reasons.append(
            f"Confidence {ioc.confidence}% below threshold "
            f"{settings.THREAT_INTEL_AUTO_BLOCK_CONFIDENCE_THRESHOLD}%"
        )
    if severity_order.get(ioc_severity, 1) < severity_order.get(threshold_severity, 3):
        reasons.append(
            f"Severity {ioc.severity} below threshold "
            f"{settings.THREAT_INTEL_AUTO_BLOCK_SEVERITY_THRESHOLD}"
        )

    return {
        "ioc_value": ioc.value,
        "ioc_type": ioc.ioc_type,
        "confidence": ioc.confidence,
        "severity": ioc.severity,
        "auto_block_enabled": settings.THREAT_INTEL_AUTO_BLOCK_ENABLED,
        "confidence_threshold": settings.THREAT_INTEL_AUTO_BLOCK_CONFIDENCE_THRESHOLD,
        "severity_threshold": settings.THREAT_INTEL_AUTO_BLOCK_SEVERITY_THRESHOLD,
        "meets_criteria": should_block,
        "reason": "; ".join(reasons) if not should_block else "Meets all criteria",
    }