from pydantic import BaseModel
from typing import Optional
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "audit.db")

class Alert(BaseModel):
    id: str
    source_ip: str
    destination_ip: str
    attack_type: str
    severity: str
    timestamp: str
    raw_message: str

class PolicyDecision(BaseModel):
    action: str
    duration_minutes: int
    ip: str
    reason: str
    analyst_approved: bool = False

class AuditLog(BaseModel):
    id: int
    alert_id: str
    action_taken: str
    ip_address: str
    timestamp: str
    analyst_notes: Optional[str] = None

def init_db():
    """Initialize SQLite database for audit logging."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT NOT NULL,
            action_taken TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            analyst_notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_audit(action: str, ip: str, alert_id: str = None, notes: str = None):
    """Write an audit log entry."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = __import__("datetime").datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO audit_logs (alert_id, action_taken, ip_address, timestamp, analyst_notes) VALUES (?, ?, ?, ?, ?)",
        (alert_id, action, ip, timestamp, notes)
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid