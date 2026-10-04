"""
API v1 package.

This module aggregates all v1 API routers.
"""
from backend.app.api.v1 import (
    auth,
    users,
    alerts,
    incidents,
    firewall,
    threat_intel,
    assets,
    logs,
    reports,
    notifications,
    admin,
)

__all__ = [
    "auth",
    "users",
    "alerts",
    "incidents",
    "firewall",
    "threat_intel",
    "assets",
    "logs",
    "reports",
    "notifications",
    "admin",
]