"""
AI-SOC Firewall Response Application
FastAPI application with alert ingestion, policy engine, and SQLite audit logging.
"""

import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.routes.alerts import router as alerts_router
from app.routes.auth import router as auth_router

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    init_db()
    
    app = FastAPI(
        title="AI-SOC Firewall Response",
        description="Deterministic firewall response with analyst approval",
        version="1.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(auth_router)
    app.include_router(alerts_router)
    
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8001,
        reload=False
    )