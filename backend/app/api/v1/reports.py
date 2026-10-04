"""
Reports API routes.

Provides report generation, scheduling, and management.
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_permission
from backend.app.db.session import get_db
from backend.app.models.report import Report, ReportType, ReportFormat, ReportStatus
from backend.app.models.user import User
from backend.app.schemas.common import (
    ReportCreate,
    ReportResponse,
    ReportUpdate,
    ReportGenerateRequest,
    MessageResponse,
    PaginatedResponse,
)
from backend.app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=PaginatedResponse[ReportResponse], summary="List reports")
def list_reports(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query()] = None,
    report_type: Annotated[ReportType | None, Query()] = None,
    status: Annotated[ReportStatus | None, Query()] = None,
    created_by: Annotated[int | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    current_user: User = Depends(require_permission("reports:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ReportResponse]:
    """
    List reports with pagination, search, and filtering.
    """
    report_service = ReportService(db)
    reports, total = report_service.list_reports(
        page=page,
        page_size=page_size,
        search=search,
        report_type=report_type,
        status=status,
        created_by=created_by,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats", summary="Get report statistics")
def get_report_stats(
    current_user: User = Depends(require_permission("reports:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get report statistics for dashboard.
    """
    report_service = ReportService(db)
    return report_service.get_stats()


@router.get("/templates", summary="List report templates")
def list_templates(
    current_user: User = Depends(require_permission("reports:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    List available report templates.
    """
    report_service = ReportService(db)
    return report_service.list_templates()


@router.get("/{report_id}", response_model=ReportResponse, summary="Get report by ID")
def get_report(
    report_id: int,
    current_user: User = Depends(require_permission("reports:read")),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Get a report by ID.
    """
    report_service = ReportService(db)
    report = report_service.get_report(report_id)
    
    if not report:
        raise NotFoundError("Report not found")
    
    return ReportResponse.model_validate(report)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED, summary="Create report")
def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(require_permission("reports:write")),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Create a new report definition.
    """
    report_service = ReportService(db)
    report = report_service.create_report(report_data, current_user.id)
    
    return ReportResponse.model_validate(report)


@router.post("/generate", response_model=ReportResponse, summary="Generate report")
def generate_report(
    generate_request: ReportGenerateRequest,
    current_user: User = Depends(require_permission("reports:write")),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Generate a report on-demand.
    """
    report_service = ReportService(db)
    report = report_service.generate_report(generate_request, current_user.id)
    
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}", response_model=ReportResponse, summary="Update report")
def update_report(
    report_id: int,
    report_data: ReportUpdate,
    current_user: User = Depends(require_permission("reports:write")),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Update a report definition.
    """
    report_service = ReportService(db)
    report = report_service.update_report(report_id, report_data, current_user.id)
    
    if not report:
        raise NotFoundError("Report not found")
    
    return ReportResponse.model_validate(report)


@router.post("/{report_id}/regenerate", response_model=ReportResponse, summary="Regenerate report")
def regenerate_report(
    report_id: int,
    current_user: User = Depends(require_permission("reports:write")),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Regenerate an existing report.
    """
    report_service = ReportService(db)
    report = report_service.regenerate_report(report_id, current_user.id)
    
    if not report:
        raise NotFoundError("Report not found")
    
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/download", summary="Download report file")
def download_report(
    report_id: int,
    current_user: User = Depends(require_permission("reports:read")),
    db: Session = Depends(get_db),
):
    """
    Download a generated report file.
    """
    report_service = ReportService(db)
    return report_service.download_report(report_id)


@router.delete("/{report_id}", response_model=MessageResponse, summary="Delete report")
def delete_report(
    report_id: int,
    current_user: User = Depends(require_permission("reports:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a report (admin only).
    """
    report_service = ReportService(db)
    report_service.delete_report(report_id)
    
    return MessageResponse(message="Report deleted successfully")


# =========================================================
# Scheduled Reports
# =========================================================

@router.get("/schedules", summary="List scheduled reports")
def list_schedules(
    current_user: User = Depends(require_permission("reports:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    List scheduled report jobs.
    """
    report_service = ReportService(db)
    return report_service.list_schedules()


@router.post("/schedules", summary="Create scheduled report")
def create_schedule(
    schedule_data: dict,
    current_user: User = Depends(require_permission("reports:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Create a new scheduled report job.
    """
    report_service = ReportService(db)
    return report_service.create_schedule(schedule_data, current_user.id)


@router.get("/schedules/{schedule_id}", summary="Get scheduled report")
def get_schedule(
    schedule_id: int,
    current_user: User = Depends(require_permission("reports:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get a scheduled report job.
    """
    report_service = ReportService(db)
    return report_service.get_schedule(schedule_id)


@router.patch("/schedules/{schedule_id}", summary="Update scheduled report")
def update_schedule(
    schedule_id: int,
    schedule_data: dict,
    current_user: User = Depends(require_permission("reports:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Update a scheduled report job.
    """
    report_service = ReportService(db)
    return report_service.update_schedule(schedule_id, schedule_data, current_user.id)


@router.post("/schedules/{schedule_id}/enable", summary="Enable scheduled report")
def enable_schedule(
    schedule_id: int,
    current_user: User = Depends(require_permission("reports:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Enable a scheduled report job.
    """
    report_service = ReportService(db)
    return report_service.enable_schedule(schedule_id, current_user.id)


@router.post("/schedules/{schedule_id}/disable", summary="Disable scheduled report")
def disable_schedule(
    schedule_id: int,
    current_user: User = Depends(require_permission("reports:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Disable a scheduled report job.
    """
    report_service = ReportService(db)
    return report_service.disable_schedule(schedule_id, current_user.id)


@router.delete("/schedules/{schedule_id}", response_model=MessageResponse, summary="Delete scheduled report")
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(require_permission("reports:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a scheduled report job.
    """
    report_service = ReportService(db)
    report_service.delete_schedule(schedule_id)
    
    return MessageResponse(message="Scheduled report deleted successfully")