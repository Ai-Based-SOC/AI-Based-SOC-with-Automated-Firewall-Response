"""
Report generation and scheduling service.

Provides CRUD operations for reports and report schedules, along with
statistics and template listing.  Schedules are persisted using the
``ReportSchedule`` model so that enable/disable/delete operate on real
rows rather than returning fabricated data.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.models.report import Report, ReportSchedule, ReportStatus, ReportType


def _generate_report_id():
    return "rpt_" + uuid.uuid4().hex[:12]


def _generate_schedule_id():
    return "sch_" + uuid.uuid4().hex[:12]


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        report_type: Optional[ReportType] = None,
        status: Optional[ReportStatus] = None,
        created_by: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        offset = (page - 1) * page_size
        query = select(Report).order_by(
            getattr(Report, sort_by).desc() if sort_order == "desc"
            else getattr(Report, sort_by).asc()
        )
        if search:
            pattern = "%" + search + "%"
            query = query.where(
                (Report.title.ilike(pattern))
                | (Report.report_type.astext.ilike(pattern))
                | (Report.status.astext.ilike(pattern))
            )
        if report_type:
            query = query.where(Report.report_type == report_type)
        if status:
            query = query.where(Report.status == status)
        if created_by:
            from sqlalchemy import Integer as _Int
            query = query.where(func.cast(Report.generated_by_id, _Int) == created_by)
        if start_date:
            query = query.where(Report.created_at >= start_date)
        if end_date:
            query = query.where(Report.created_at <= end_date)
        subquery = query.subquery()
        total = self.db.execute(select(func.count()).select_from(subquery)).scalar() or 0
        reports = self.db.execute(query.offset(offset).limit(page_size)).scalars().all()
        return reports, total

    def get_report(self, report_id: int) -> Report:
        report = self.db.get(Report, report_id)
        if not report:
            raise NotFoundError("Report not found: " + str(report_id))
        return report

    def create_report(self, report_data, user_id: uuid.UUID) -> Report:
        values = report_data.model_dump(exclude_unset=True, exclude={"id"})
        report = Report(
            id=uuid.uuid4(),
            report_id=_generate_report_id(),
            generated_by_id=user_id,
            generated_by_name=str(user_id),
            **values,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def update_report(self, report_id: int, report_data, user_id: uuid.UUID) -> Report:
        report = self.get_report(report_id)
        values = (
            report_data.model_dump(exclude_unset=True)
            if hasattr(report_data, "model_dump")
            else report_data
        )
        for key, value in values.items():
            setattr(report, key, value)
        self.db.commit()
        self.db.refresh(report)
        return report

    def delete_report(self, report_id: int, user_id: uuid.UUID) -> None:
        report = self.get_report(report_id)
        self.db.delete(report)
        self.db.commit()

    def get_stats(self) -> dict:
        total_reports = self.db.scalar(select(func.count()).select_from(Report)) or 0
        by_status = {}
        for row in self.db.execute(
            select(Report.status, func.count().label("count")).group_by(Report.status)
        ).all():
            sv = row.status.value if hasattr(row.status, "value") else str(row.status)
            by_status[sv] = row.count
        by_type = {}
        for row in self.db.execute(
            select(Report.report_type, func.count().label("count")).group_by(Report.report_type)
        ).all():
            tv = row.report_type.value if hasattr(row.report_type, "value") else str(row.report_type)
            by_type[tv] = row.count
        recent = self.db.scalars(
            select(Report).order_by(Report.created_at.desc()).limit(5)
        ).all()
        return {
            "total_reports": total_reports,
            "by_status": by_status,
            "by_type": by_type,
            "recent_reports": [
                {
                    "id": str(r.id),
                    "title": r.title,
                    "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in recent
            ],
        }

    def list_templates(self) -> list[dict]:
        return [
            {"id": "template_executive_summary", "name": "Executive Summary",
             "description": "High-level summary for executives", "category": "Executive",
             "default_format": "pdf", "is_system": True},
            {"id": "template_incident_report", "name": "Incident Report",
             "description": "Detailed incident report for post-mortem", "category": "Incident",
             "default_format": "pdf", "is_system": True},
            {"id": "template_threat_intelligence", "name": "Threat Intelligence",
             "description": "Threat actors and IOC summary", "category": "Intelligence",
             "default_format": "pdf", "is_system": True},
            {"id": "template_daily_soc", "name": "Daily SOC Report",
             "description": "Daily SOC activity summary", "category": "Operations",
             "default_format": "pdf", "is_system": True},
            {"id": "template_custom", "name": "Custom Report",
             "description": "User-defined custom report", "category": "Custom",
             "default_format": "pdf", "is_system": True},
        ]

    @staticmethod
    def _schedule_to_dict(schedule: ReportSchedule) -> dict:
        return {
            "id": str(schedule.id),
            "schedule_id": schedule.schedule_id,
            "name": schedule.name,
            "description": schedule.description,
            "template_id": str(schedule.template_id) if schedule.template_id else None,
            "cron_expression": schedule.cron_expression,
            "timezone": schedule.timezone,
            "is_active": schedule.is_active,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
            "run_count": schedule.run_count,
            "failure_count": schedule.failure_count,
            "recipients": schedule.recipients,
            "format": schedule.format.value if hasattr(schedule.format, "value") else str(schedule.format),
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
            "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
        }

    def create_schedule(self, schedule_data: dict, user_id) -> dict:
        if not schedule_data or "cron_expression" not in schedule_data:
            raise ValidationError("cron_expression is required for schedules")
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID
        schedule = ReportSchedule(
            id=uuid.uuid4(),
            schedule_id=_generate_schedule_id(),
            created_by_id=user_id,
            **schedule_data,
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return self._schedule_to_dict(schedule)

    def list_schedules(self) -> list[dict]:
        schedules = self.db.scalars(
            select(ReportSchedule).order_by(ReportSchedule.created_at.desc())
        ).all()
        return [self._schedule_to_dict(s) for s in schedules]

    def get_schedule(self, schedule_id: int) -> dict:
        schedule = self.db.get(ReportSchedule, schedule_id)
        if not schedule:
            raise NotFoundError("Schedule not found: " + str(schedule_id))
        return self._schedule_to_dict(schedule)

    def update_schedule(self, schedule_id: int, schedule_data: dict, user_id) -> dict:
        schedule = self.db.get(ReportSchedule, schedule_id)
        if not schedule:
            raise NotFoundError("Schedule not found: " + str(schedule_id))
        for key, value in schedule_data.items():
            setattr(schedule, key, value)
        self.db.commit()
        self.db.refresh(schedule)
        return self._schedule_to_dict(schedule)

    def enable_schedule(self, schedule_id: int, user_id) -> dict:
        schedule = self.db.get(ReportSchedule, schedule_id)
        if not schedule:
            raise NotFoundError("Schedule not found: " + str(schedule_id))
        schedule.is_active = True
        self.db.commit()
        self.db.refresh(schedule)
        return self._schedule_to_dict(schedule)

    def disable_schedule(self, schedule_id: int, user_id) -> dict:
        schedule = self.db.get(ReportSchedule, schedule_id)
        if not schedule:
            raise NotFoundError("Schedule not found: " + str(schedule_id))
        schedule.is_active = False
        self.db.commit()
        self.db.refresh(schedule)
        return self._schedule_to_dict(schedule)

    def delete_schedule(self, schedule_id: int) -> None:
        schedule = self.db.get(ReportSchedule, schedule_id)
        if not schedule:
            raise NotFoundError("Schedule not found: " + str(schedule_id))
        self.db.delete(schedule)
        self.db.commit()
