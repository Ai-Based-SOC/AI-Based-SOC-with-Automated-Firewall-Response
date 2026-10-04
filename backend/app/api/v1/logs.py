"""
Log Ingestion & Search API routes.

Provides log ingestion, search, and normalization capabilities.
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_permission
from backend.app.db.session import get_db
from backend.app.models.log import LogEntry, LogLevel, LogSourceType
from backend.app.models.user import User
from backend.app.schemas.common import (
    LogEntryCreate,
    LogEntryResponse,
    LogSearchRequest,
    LogSearchResponse,
    MessageResponse,
    PaginatedResponse,
)
from backend.app.services.log_service import LogService

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("", response_model=PaginatedResponse[LogEntryResponse], summary="List log entries")
def list_logs(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=1000)] = 100,
    search: Annotated[str | None, Query()] = None,
    source: Annotated[LogSourceType | None, Query()] = None,
    level: Annotated[LogLevel | None, Query()] = None,
    source_ip: Annotated[str | None, Query()] = None,
    dest_ip: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "timestamp",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    current_user: User = Depends(require_permission("logs:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[LogEntryResponse]:
    """
    List log entries with pagination, search, and filtering.
    """
    log_service = LogService(db)
    logs, total = log_service.list_logs(
        page=page,
        page_size=page_size,
        search=search,
        source=source,
        level=level,
        source_ip=source_ip,
        dest_ip=dest_ip,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedResponse(
        items=[LogEntryResponse.model_validate(l) for l in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats", summary="Get log statistics")
def get_log_stats(
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    current_user: User = Depends(require_permission("logs:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get log statistics for dashboard.
    """
    log_service = LogService(db)
    return log_service.get_stats(start_date, end_date)


@router.post("/search", response_model=LogSearchResponse, summary="Search logs")
def search_logs(
    search_request: LogSearchRequest,
    current_user: User = Depends(require_permission("logs:read")),
    db: Session = Depends(get_db),
) -> LogSearchResponse:
    """
    Advanced log search with full-text and structured queries.
    """
    log_service = LogService(db)
    result = log_service.search_logs(search_request)
    
    return LogSearchResponse(**result)


@router.get("/{log_id}", response_model=LogEntryResponse, summary="Get log entry by ID")
def get_log(
    log_id: int,
    current_user: User = Depends(require_permission("logs:read")),
    db: Session = Depends(get_db),
) -> LogEntryResponse:
    """
    Get a log entry by ID.
    """
    log_service = LogService(db)
    log = log_service.get_log(log_id)
    
    if not log:
        raise NotFoundError("Log entry not found")
    
    return LogEntryResponse.model_validate(log)


@router.post("", response_model=LogEntryResponse, status_code=status.HTTP_201_CREATED, summary="Create log entry")
def create_log(
    log_data: LogEntryCreate,
    current_user: User = Depends(require_permission("logs:write")),
    db: Session = Depends(get_db),
) -> LogEntryResponse:
    """
    Create a new log entry (manual entry).
    """
    log_service = LogService(db)
    log = log_service.create_log(log_data)
    
    return LogEntryResponse.model_validate(log)


@router.post("/bulk", response_model=MessageResponse, status_code=status.HTTP_201_CREATED, summary="Bulk ingest logs")
def bulk_ingest_logs(
    logs: list[LogEntryCreate],
    current_user: User = Depends(require_permission("logs:write")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Bulk ingest log entries.
    """
    log_service = LogService(db)
    count = log_service.bulk_ingest(logs)
    
    return MessageResponse(message=f"Successfully ingested {count} log entries")


@router.delete("/{log_id}", response_model=MessageResponse, summary="Delete log entry")
def delete_log(
    log_id: int,
    current_user: User = Depends(require_permission("logs:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a log entry (admin only).
    """
    log_service = LogService(db)
    log_service.delete_log(log_id)
    
    return MessageResponse(message="Log entry deleted successfully")


# =========================================================
# Log Sources
# =========================================================

@router.get("/sources", summary="List log sources")
def list_log_sources(
    current_user: User = Depends(require_permission("logs:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    List configured log sources.
    """
    log_service = LogService(db)
    return log_service.list_sources()


@router.post("/sources", summary="Add log source")
def add_log_source(
    source_data: dict,
    current_user: User = Depends(require_permission("logs:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Add a new log source configuration.
    """
    log_service = LogService(db)
    return log_service.add_source(source_data)


@router.get("/sources/{source_id}", summary="Get log source")
def get_log_source(
    source_id: int,
    current_user: User = Depends(require_permission("logs:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get a log source configuration.
    """
    log_service = LogService(db)
    return log_service.get_source(source_id)


@router.patch("/sources/{source_id}", summary="Update log source")
def update_log_source(
    source_id: int,
    source_data: dict,
    current_user: User = Depends(require_permission("logs:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Update a log source configuration.
    """
    log_service = LogService(db)
    return log_service.update_source(source_id, source_data)


@router.delete("/sources/{source_id}", response_model=MessageResponse, summary="Delete log source")
def delete_log_source(
    source_id: int,
    current_user: User = Depends(require_permission("logs:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a log source configuration.
    """
    log_service = LogService(db)
    log_service.delete_source(source_id)
    
    return MessageResponse(message="Log source deleted successfully")


@router.post("/sources/{source_id}/test", summary="Test log source connection")
def test_log_source(
    source_id: int,
    current_user: User = Depends(require_permission("logs:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Test connection to a log source.
    """
    log_service = LogService(db)
    return log_service.test_source(source_id)


@router.post("/sources/{source_id}/sync", summary="Sync log source")
def sync_log_source(
    source_id: int,
    current_user: User = Depends(require_permission("logs:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Manually trigger sync for a log source.
    """
    log_service = LogService(db)
    return log_service.sync_source(source_id)


# =========================================================
# Log Parsers
# =========================================================

@router.get("/parsers", summary="List log parsers")
def list_parsers(
    current_user: User = Depends(require_permission("logs:read")),
) -> list[dict]:
    """
    List available log parsers.
    """
    return [
        {"name": "syslog", "display_name": "Syslog (RFC 3164/5424)", "supported_sources": ["linux", "network"]},
        {"name": "windows_event", "display_name": "Windows Event Logs", "supported_sources": ["windows"]},
        {"name": "apache", "display_name": "Apache Access/Error Logs", "supported_sources": ["web"]},
        {"name": "nginx", "display_name": "Nginx Access/Error Logs", "supported_sources": ["web"]},
        {"name": "suricata", "display_name": "Suricata IDS/IPS", "supported_sources": ["ids"]},
        {"name": "snort", "display_name": "Snort IDS/IPS", "supported_sources": ["ids"]},
        {"name": "zeek", "display_name": "Zeek Network Security Monitor", "supported_sources": ["network"]},
        {"name": "pfsense", "display_name": "pfSense Firewall Logs", "supported_sources": ["firewall"]},
        {"name": "cisco_asa", "display_name": "Cisco ASA Firewall", "supported_sources": ["firewall"]},
        {"name": "aws_cloudtrail", "display_name": "AWS CloudTrail", "supported_sources": ["cloud"]},
        {"name": "azure_logs", "display_name": "Azure Activity Logs", "supported_sources": ["cloud"]},
        {"name": "m365", "display_name": "Microsoft 365 Audit Logs", "supported_sources": ["cloud"]},
        {"name": "docker", "display_name": "Docker Container Logs", "supported_sources": ["container"]},
        {"name": "kubernetes", "display_name": "Kubernetes Audit Logs", "supported_sources": ["container"]},
        {"name": "json", "display_name": "Generic JSON Logs", "supported_sources": ["custom"]},
        {"name": "cef", "display_name": "Common Event Format (CEF)", "supported_sources": ["siem"]},
        {"name": "leef", "display_name": "Log Event Extended Format (LEEF)", "supported_sources": ["siem"]},
    ]


@router.post("/parsers/test", summary="Test log parser")
def test_parser(
    parser_name: str,
    sample_log: str,
    current_user: User = Depends(require_permission("logs:read")),
) -> dict:
    """
    Test a log parser with a sample log entry.
    """
    log_service = LogService(None)  # No DB needed for parser test
    return log_service.test_parser(parser_name, sample_log)