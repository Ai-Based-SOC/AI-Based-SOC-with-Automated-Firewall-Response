"""
Database session access.

Re-exports the session factory and FastAPI dependency from
``backend.app.db.base`` so that API routers and services can import
``get_db`` / ``get_db_session`` from a single canonical location.
"""
from backend.app.db.base import (
    SessionLocal,
    engine,
    get_db,
    get_db_context,
    get_db_session,
)

__all__ = [
    "SessionLocal",
    "engine",
    "get_db",
    "get_db_context",
    "get_db_session",
]