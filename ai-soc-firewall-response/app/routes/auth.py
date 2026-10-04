from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os
import hashlib

router = APIRouter(prefix="/api/v1", tags=["auth"])

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "audit.db")

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    email: str
    role: str
    token: str

@router.post("/login")
def login(req: LoginRequest):
    """Analyst login endpoint."""
    # Simple mock authentication
    if req.email == "analyst@soc.local" and req.password == "Admin@123":
        return UserResponse(
            email=req.email,
            role="analyst",
            token="mock-jwt-token-analyst-12345"
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/me")
def me():
    """Get current user info."""
    return {"email": "analyst@soc.local", "role": "analyst"}