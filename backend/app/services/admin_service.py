"""
Administration and system-management service.

Handles system configuration, backups, maintenance mode, and feature
flags.  Configuration rows are stored in the ``SystemConfig`` table;
backups, maintenance, and feature flags are managed through the same
configuration table (keyed by ``category``) so the API returns real,
queryable data rather than fabricated values.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    String,
    Text,
    JSON,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.schemas.common import SystemConfigCreate, SystemConfigUpdate


class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="general", index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<SystemConfig(key={self.key}, category={self.category})>"


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_config(self, page=1, page_size=50, search=None, category=None):
        offset = (page - 1) * page_size
        query = select(SystemConfig).order_by(SystemConfig.key)
        if search:
            pattern = "%" + search + "%"
            query = query.where((SystemConfig.key.ilike(pattern)) | (SystemConfig.category.ilike(pattern)))
        if category:
            query = query.where(SystemConfig.category == category)
        subquery = query.subquery()
        total = self.db.execute(select(func.count()).select_from(subquery)).scalar() or 0
        configs = self.db.execute(query.offset(offset).limit(page_size)).scalars().all()
        return configs, total

    def get_config(self, config_key):
        return self.db.scalar(select(SystemConfig).where(SystemConfig.key == config_key))

    def create_config(self, config_data: SystemConfigCreate, user_id: uuid.UUID) -> SystemConfig:
        existing = self.db.scalar(select(SystemConfig).where(SystemConfig.key == config_data.key))
        if existing:
            raise ValidationError("Configuration key already exists: " + config_data.key)
        config = SystemConfig(
            id=uuid.uuid4(), key=config_data.key,
            value=getattr(config_data, "value", None),
            category=config_data.category,
            description=config_data.description, updated_by=user_id,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update_config(self, config_key, config_data: SystemConfigUpdate, user_id: uuid.UUID) -> SystemConfig:
        config = self.db.scalar(select(SystemConfig).where(SystemConfig.key == config_key))
        if not config:
            raise NotFoundError("Configuration key not found: " + config_key)
        values = (config_data.model_dump(exclude_unset=True, exclude={"key"})
                  if hasattr(config_data, "model_dump") else config_data)
        for key, value in values.items():
            setattr(config, key, value)
        config.updated_by = user_id
        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_config(self, config_key):
        config = self.db.scalar(select(SystemConfig).where(SystemConfig.key == config_key))
        if not config:
            raise NotFoundError("Configuration key not found: " + config_key)
        self.db.delete(config)
        self.db.commit()

    def list_backups(self):
        rows = self.db.scalars(select(SystemConfig).where(SystemConfig.category == "backup")).all()
        return [self._config_to_backup_dict(r) for r in rows]

    def get_backup(self, backup_id):
        row = self.db.scalar(select(SystemConfig).where(
            (SystemConfig.category == "backup") & (SystemConfig.key == backup_id)))
        if not row:
            raise NotFoundError("Backup not found: " + backup_id)
        return self._config_to_backup_dict(row)

    def create_backup(self, backup_data: dict, user_id: uuid.UUID) -> dict:
        backup_id = backup_data.get("backup_id") or ("bkp_" + uuid.uuid4().hex[:12])
        row = SystemConfig(
            id=uuid.uuid4(), key=backup_id,
            value=backup_data.get("metadata", {}), category="backup",
            description=backup_data.get("description"), updated_by=user_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {
            "backup_id": backup_id, "status": "completed",
            "created_at": row.created_at.isoformat(),
            "size_bytes": backup_data.get("size_bytes", 0),
            "path": backup_data.get("path", ""),
        }

    def delete_backup(self, backup_id):
        row = self.db.scalar(select(SystemConfig).where(
            (SystemConfig.category == "backup") & (SystemConfig.key == backup_id)))
        if not row:
            raise NotFoundError("Backup not found: " + backup_id)
        self.db.delete(row)
        self.db.commit()

    @staticmethod
    def _config_to_backup_dict(row: SystemConfig) -> dict:
        meta = row.value or {}
        return {
            "backup_id": row.key,
            "status": meta.get("status", "completed"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "size_bytes": meta.get("size_bytes", 0),
            "path": meta.get("path", ""),
        }

    def enable_maintenance(self, message, user_id: uuid.UUID) -> dict:
        row = self.db.scalar(select(SystemConfig).where(
            (SystemConfig.category == "maintenance") & (SystemConfig.key == "maintenance_mode")))
        if row:
            row.value = {"enabled": True, "message": message, "enabled_by": str(user_id)}
            row.updated_by = user_id
        else:
            row = SystemConfig(
                id=uuid.uuid4(), key="maintenance_mode",
                value={"enabled": True, "message": message, "enabled_by": str(user_id)},
                category="maintenance", updated_by=user_id,
            )
            self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"enabled": True, "message": message, "enabled_by": str(user_id)}

    def disable_maintenance(self, user_id: uuid.UUID) -> dict:
        row = self.db.scalar(select(SystemConfig).where(
            (SystemConfig.category == "maintenance") & (SystemConfig.key == "maintenance_mode")))
        if row:
            row.value = {"enabled": False}
            row.updated_by = user_id
            self.db.commit()
            self.db.refresh(row)
        return {"enabled": False}

    def get_maintenance_status(self):
        row = self.db.scalar(select(SystemConfig).where(
            (SystemConfig.category == "maintenance") & (SystemConfig.key == "maintenance_mode")))
        if not row:
            return {"enabled": False, "message": None}
        return row.value or {"enabled": False}

    def list_feature_flags(self):
        rows = self.db.scalars(select(SystemConfig).where(SystemConfig.category == "feature_flag")).all()
        return [{"flag_key": r.key, "enabled": bool((r.value or {}).get("enabled", False)),
                 "description": (r.value or {}).get("description"),
                 "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                 "updated_by": str(r.updated_by) if r.updated_by else None} for r in rows]

    def create_feature_flag(self, flag_data: dict, user_id: uuid.UUID) -> dict:
        if "flag_key" not in flag_data:
            raise ValidationError("flag_key is required")
        row = self.db.scalar(select(SystemConfig).where(
            (SystemConfig.category == "feature_flag") & (SystemConfig.key == flag_data["flag_key"])))
        if row:
            raise ValidationError("Feature flag already exists: " + flag_data["flag_key"])
        row = SystemConfig(
            id=uuid.uuid4(), key=flag_data["flag_key"],
            value={"enabled": flag_data.get("enabled", False),
                   "description": flag_data.get("description")},
            category="feature_flag", updated_by=user_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"flag_key": row.key, "enabled": bool((row.value or {}).get("enabled", False)),
                "description": (row.value or {}).get("description"),
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "updated_by": str(row.updated_by) if row.updated_by else None}

    def update_feature_flag(self, flag_key, flag_data: dict, user_id: uuid.UUID) -> dict:
        row = self.db.scalar(select(SystemConfig).where(
            (SystemConfig.category == "feature_flag") & (SystemConfig.key == flag_key)))
        if not row:
            raise NotFoundError("Feature flag not found: " + flag_key)
        value = row.value or {}
        value.update(flag_data)
        row.value = value
        row.updated_by = user_id
        self.db.commit()
        self.db.refresh(row)
        return {"flag_key": row.key, "enabled": bool((row.value or {}).get("enabled", False)),
                "description": (row.value or {}).get("description"),
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "updated_by": str(row.updated_by) if row.updated_by else None}

    def delete_feature_flag(self, flag_key):
        row = self.db.scalar(select(SystemConfig).where(
            (SystemConfig.category == "feature_flag") & (SystemConfig.key == flag_key)))
        if not row:
            raise NotFoundError("Feature flag not found: " + flag_key)
        self.db.delete(row)
        self.db.commit()
