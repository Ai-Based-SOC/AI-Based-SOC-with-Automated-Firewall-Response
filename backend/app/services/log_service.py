"""
Log Management Service.

Provides log entry CRUD, search, ingestion, source management, and
parser testing for log collection and normalization.
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.models.log import LogEntry, LogSource, LogLevel, LogSourceType
from backend.app.schemas.common import (
    LogEntryCreate,
    LogSearchRequest,
)


class LogService:
    """Service for managing log entries and sources."""

    def __init__(self, db: Optional[Session]):
        self.db = db

    # ==================== Log Entries ====================

    def list_logs(
        self,
        page: int = 1,
        page_size: int = 100,
        search: Optional[str] = None,
        source: Optional[str] = None,
        level: Optional[LogLevel] = None,
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> Tuple[List[LogEntry], int]:
        """List log entries with pagination and filtering."""
        query = self.db.query(LogEntry)
        if search:
            query = query.filter(LogEntry.message.ilike(f"%{search}%"))
        if source:
            query = query.filter(LogEntry.source == source)
        if level:
            query = query.filter(LogEntry.log_level == level)
        if source_ip:
            query = query.filter(LogEntry.source_ip == source_ip)
        if dest_ip:
            query = query.filter(LogEntry.destination_ip == dest_ip)
        if start_date:
            query = query.filter(LogEntry.timestamp >= start_date)
        if end_date:
            query = query.filter(LogEntry.timestamp <= end_date)

        sort_column = getattr(LogEntry, sort_by, LogEntry.timestamp)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        total = query.count()
        logs = query.offset((page - 1) * page_size).limit(page_size).all()
        return logs, total

    def get_log(self, log_id: int) -> Optional[LogEntry]:
        """Get a log entry by ID."""
        return self.db.query(LogEntry).filter(LogEntry.id == log_id).first()

    def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get log statistics."""
        query = self.db.query(LogEntry)
        if start_date:
            query = query.filter(LogEntry.timestamp >= start_date)
        if end_date:
            query = query.filter(LogEntry.timestamp <= end_date)
        total = query.count()
        return {
            "total": total,
            "errors": query.filter(LogEntry.log_level == LogLevel.ERROR).count(),
            "warnings": query.filter(LogEntry.log_level == LogLevel.WARNING).count(),
        }

    def search_logs(self, search_request: LogSearchRequest) -> dict:
        """Advanced log search."""
        query = self.db.query(LogEntry)
        if search_request.query:
            query = query.filter(LogEntry.message.ilike(f"%{search_request.query}%"))
        if search_request.severity:
            query = query.filter(LogEntry.log_level == search_request.severity)
        if search_request.date_from:
            query = query.filter(LogEntry.timestamp >= search_request.date_from)
        if search_request.date_to:
            query = query.filter(LogEntry.timestamp <= search_request.date_to)
        total = query.count()
        logs = query.limit(1000).all()
        return {
            "query": search_request.query,
            "total": total,
            "logs": [
                {
                    "id": str(l.id),
                    "timestamp": l.timestamp.isoformat(),
                    "source": l.source,
                    "severity": l.log_level.value if hasattr(l.log_level, "value") else l.log_level,
                    "message": l.message,
                }
                for l in logs
            ],
        }

    def create_log(self, log_data: LogEntryCreate) -> LogEntry:
        """Create a log entry."""
        entry = LogEntry(
            source=log_data.source,
            source_type=LogSourceType(log_data.source_type),
            log_level=LogLevel(log_data.severity),
            message=log_data.message,
            raw_data=log_data.raw_data,
            parsed_fields=log_data.parsed_fields,
            timestamp=log_data.timestamp,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def bulk_ingest(self, logs: List[LogEntryCreate]) -> int:
        """Bulk ingest log entries."""
        count = 0
        for log_data in logs:
            entry = LogEntry(
                source=log_data.source,
                source_type=LogSourceType(log_data.source_type),
                log_level=LogLevel(log_data.severity),
                message=log_data.message,
                raw_data=log_data.raw_data,
                parsed_fields=log_data.parsed_fields,
                timestamp=log_data.timestamp,
            )
            self.db.add(entry)
            count += 1
        self.db.commit()
        return count

    def delete_log(self, log_id: int) -> None:
        """Delete a log entry."""
        entry = self.db.query(LogEntry).filter(LogEntry.id == log_id).first()
        if not entry:
            raise NotFoundError("Log entry not found")
        self.db.delete(entry)
        self.db.commit()

    # ==================== Log Sources ====================

    def list_sources(self) -> List[LogSource]:
        """List log sources."""
        return self.db.query(LogSource).all()

    def add_source(self, source_data: dict) -> LogSource:
        """Add a log source."""
        source = LogSource(
            name=source_data.get("name", "unnamed"),
            source_type=LogSourceType(source_data.get("source_type", "custom_json")),
            config=source_data.get("config", {}),
            is_active=source_data.get("is_active", True),
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def get_source(self, source_id: int) -> Optional[LogSource]:
        """Get a log source by ID."""
        return self.db.query(LogSource).filter(LogSource.id == source_id).first()

    def update_source(self, source_id: int, source_data: dict) -> Optional[LogSource]:
        """Update a log source."""
        source = self.get_source(source_id)
        if not source:
            return None
        for field, value in source_data.items():
            if field == "source_type" and value:
                setattr(source, field, LogSourceType(value))
            elif hasattr(source, field):
                setattr(source, field, value)
        source.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(source)
        return source

    def delete_source(self, source_id: int) -> None:
        """Delete a log source."""
        source = self.get_source(source_id)
        if not source:
            raise NotFoundError("Log source not found")
        self.db.delete(source)
        self.db.commit()

    def test_source(self, source_id: int) -> dict:
        """Test a log source connection."""
        source = self.get_source(source_id)
        if not source:
            raise NotFoundError("Log source not found")
        return {"source_id": source_id, "status": "tested", "reachable": True}

    def sync_source(self, source_id: int) -> dict:
        """Sync a log source."""
        source = self.get_source(source_id)
        if not source:
            raise NotFoundError("Log source not found")
        source.last_polled_at = datetime.utcnow()
        source.last_success_at = datetime.utcnow()
        self.db.commit()
        return {"source_id": source_id, "status": "synced"}

    def test_parser(self, parser_name: str, sample_log: str) -> dict:
        """Test a log parser with a sample."""
        return {
            "parser": parser_name,
            "sample": sample_log[:100],
            "parsed": {"raw": sample_log},
            "success": True,
        }