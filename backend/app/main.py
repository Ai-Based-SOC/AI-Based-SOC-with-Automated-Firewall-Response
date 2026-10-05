import asyncio
import csv
import io
import math
import os
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar, cast

from backend.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.database.mongodb import close_mongo, connect_mongo, db as mongo_db
from backend.services.db_service import DBService

from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

APP_NAME = os.getenv("APP_NAME", "AI SOC Firewall")
APP_VERSION = os.getenv("APP_VERSION", "1.1.0")
ENV = os.getenv("ENV", "dev").lower()
DOCS_ENABLED = os.getenv("DOCS_ENABLED", "true").lower() == "true"

SECRET_KEY = os.getenv("SECRET_KEY", "")

if ENV == "prod" and len(SECRET_KEY) < 32:
    raise RuntimeError(
        "In production, SECRET_KEY must be at least 32 characters."
    )

CORS_ORIGINS_RAW = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

CORS_ORIGINS = [
    origin.strip()
    for origin in CORS_ORIGINS_RAW.split(",")
    if origin.strip()
]

if ENV == "dev" and "*" not in CORS_ORIGINS:
    CORS_ORIGINS.append("*")

RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "120/minute")
RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "5/minute")


# -----------------------------------------------------------------------------
# FastAPI application
# -----------------------------------------------------------------------------

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)


# -----------------------------------------------------------------------------
# Metrics and middleware
# -----------------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency",
    ["method", "path"],
)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )

        request.state.request_id = request_id
        started = datetime.now(timezone.utc)

        response = await call_next(request)

        elapsed = (
            datetime.now(timezone.utc) - started
        ).total_seconds()

        REQUEST_COUNT.labels(
            method=request.method,
            path=request.url.path,
            status=str(response.status_code),
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            path=request.url.path,
        ).observe(elapsed)

        response.headers["X-Request-ID"] = request_id

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        return response


app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RATE_LIMIT_DEFAULT],
)

app.state.limiter = limiter


async def rate_limit_exception_handler(
    request: Request,
    exc: Exception,
) -> Response:
    handler = cast(
        Callable[
            [Request, RateLimitExceeded],
            Response | Awaitable[Response],
        ],
        _rate_limit_exceeded_handler,
    )

    result = handler(
        request,
        cast(RateLimitExceeded, exc),
    )

    if hasattr(result, "__await__"):
        return await cast(Awaitable[Response], result)

    return cast(Response, result)


app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_exception_handler,
)


def error_payload(
    code: str,
    message: str,
    request: Request | None = None,
    details: Any | None = None,
) -> dict[str, Any]:
    request_id = ""

    if request is not None:
        request_id = getattr(
            request.state,
            "request_id",
            "",
        )

    result: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }

    if details is not None:
        result["error"]["details"] = details

    return result


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload(
            "VALIDATION_ERROR",
            "Request validation failed",
            request,
            exc.errors(),
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            "HTTP_ERROR",
            str(exc.detail),
            request,
        ),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    print(
        f"[ERROR] Unhandled exception "
        f"{type(exc).__name__}: {exc}"
    )

    return JSONResponse(
        status_code=500,
        content=error_payload(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred",
            request,
        ),
    )


# -----------------------------------------------------------------------------
# Reports directory
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/reports",
    StaticFiles(directory=str(REPORTS_DIR)),
    name="reports",
)


# -----------------------------------------------------------------------------
# WebSocket manager
# -----------------------------------------------------------------------------

class WebSocketManager:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast(self, event: str, data: dict[str, Any]) -> None:
        message = {
            "event": event,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        dead_connections: list[WebSocket] = []

        for websocket in list(self.connections):
            try:
                await websocket.send_json(message)
            except (
                WebSocketDisconnect,
                RuntimeError,
                ConnectionError,
            ):
                dead_connections.append(websocket)

        for websocket in dead_connections:
            self.disconnect(websocket)


ws_manager = WebSocketManager()


async def broadcast_soc_event(
    event: str,
    data: dict[str, Any],
) -> None:
    await ws_manager.broadcast(event, data)


# -----------------------------------------------------------------------------
# In-memory storage
# -----------------------------------------------------------------------------

class IncidentStore:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.blocked_ips: set[str] = set()
        self.reports: list[dict[str, Any]] = []

    def add_event(self, event: dict[str, Any]) -> dict[str, Any]:
        item = dict(event)

        item["id"] = item.get("id") or f"evt_{uuid.uuid4().hex[:12]}"
        item["timestamp"] = item.get("timestamp") or (
            datetime.now(timezone.utc).isoformat()
        )

        self.events.insert(0, item)
        self.events = self.events[:5000]

        return item

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 1000))
        return self.events[:limit]

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        for event in self.events:
            if str(event.get("id")) == str(event_id):
                return event

        return None

    def block_ip(self, ip_address: str) -> None:
        self.blocked_ips.add(ip_address)

    def unblock_ip(self, ip_address: str) -> None:
        self.blocked_ips.discard(ip_address)

    def add_report(self, report: dict[str, Any]) -> dict[str, Any]:
        self.reports.insert(0, report)
        self.reports = self.reports[:1000]
        return report


store = IncidentStore()


# -----------------------------------------------------------------------------
# Threat detection
# -----------------------------------------------------------------------------

@dataclass
class DetectionResult:
    attack_type: str
    severity: str
    risk_score: int
    confidence: float
    reason: str
    mitre_techniques: list[str]
    recommended_action: str


T = TypeVar("T")


class ThreatDetector:
    def __init__(self) -> None:
        self.ip_events: dict[
            str,
            deque[datetime],
        ] = defaultdict(
            lambda: deque(maxlen=5000)
        )

        self.failed_auth: dict[
            str,
            deque[datetime],
        ] = defaultdict(
            lambda: deque(maxlen=2000)
        )

        self.global_counts: deque[int] = deque(maxlen=1440)

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def contains_any(
        value: str,
        patterns: list[str],
    ) -> bool:
        lowered = (value or "").lower()
        return any(pattern in lowered for pattern in patterns)

    @staticmethod
    def clamp(
        value: float,
        low: float,
        high: float,
    ) -> float:
        return max(low, min(high, value))

    def count_within(
        self,
        values: deque[datetime],
        seconds: int,
        current_time: datetime,
    ) -> int:
        minimum = current_time.timestamp() - seconds

        return sum(
            1
            for item in values
            if item.timestamp() >= minimum
        )

    def anomaly_score(
        self,
        current: int,
    ) -> tuple[float, str]:
        values = list(self.global_counts)

        if len(values) < 30:
            return 0.2, "insufficient baseline"

        mean = sum(values) / len(values)

        variance = sum(
            (value - mean) ** 2
            for value in values
        ) / len(values)

        standard_deviation = (
            math.sqrt(variance)
            if variance > 0
            else 1
        )

        z_score = (
            current - mean
        ) / standard_deviation

        score = 1 / (1 + math.exp(-z_score))

        return score, f"z-score={z_score:.2f}"

    def analyze(
        self,
        event: dict[str, Any],
    ) -> DetectionResult:
        current_time = self.now()

        source_ip = str(
            event.get("source_ip") or "unknown"
        )

        message = (
            f"{event.get('raw_message', '')} "
            f"{event.get('payload', '')}"
        ).lower()

        status_code = int(
            event.get("status_code") or 0
        )

        self.ip_events[source_ip].append(current_time)

        if status_code in (401, 403):
            self.failed_auth[source_ip].append(current_time)

        request_count_10s = self.count_within(
            self.ip_events[source_ip],
            10,
            current_time,
        )

        request_count_60s = self.count_within(
            self.ip_events[source_ip],
            60,
            current_time,
        )

        failed_auth_60s = self.count_within(
            self.failed_auth[source_ip],
            60,
            current_time,
        )

        self.global_counts.append(request_count_60s)

        attack_type = (
            event.get("attack_type")
            or "Suspicious Activity"
        )

        severity = (
            event.get("severity")
            or "low"
        )

        risk_score = int(
            event.get("risk_score") or 20
        )

        confidence = 0.55
        reason = "Heuristic suspicious activity"
        mitre_techniques = ["T1595"]
        recommended_action = "watch"

        if (
            request_count_10s >= 25
            or request_count_60s >= 120
        ):
            attack_type = "DDoS / Flood"
            severity = "critical"
            risk_score = 92
            confidence = 0.93
            reason = (
                f"Traffic burst from {source_ip}: "
                f"{request_count_10s}/10s, "
                f"{request_count_60s}/60s"
            )
            mitre_techniques = ["T1498"]
            recommended_action = "block"

        elif failed_auth_60s >= 12:
            attack_type = "Brute Force"
            severity = "high"
            risk_score = 84
            confidence = 0.90
            reason = (
                f"Failed authentication burst from "
                f"{source_ip}: {failed_auth_60s}/60s"
            )
            mitre_techniques = ["T1110"]
            recommended_action = "block"

        elif self.contains_any(
            message,
            [
                " union ",
                "select ",
                "' or 1=1",
                "sleep(",
                "information_schema",
            ],
        ):
            attack_type = "SQL Injection"
            severity = "high"
            risk_score = 86
            confidence = 0.91
            reason = "SQL injection signature detected"
            mitre_techniques = ["T1190", "T1059"]
            recommended_action = "block"

        elif self.contains_any(
            message,
            [
                "<script",
                "javascript:",
                "onerror=",
                "onload=",
            ],
        ):
            attack_type = "XSS Attempt"
            severity = "medium"
            risk_score = 68
            confidence = 0.85
            reason = "Cross-site scripting signature detected"
            mitre_techniques = ["T1189", "T1059"]
            recommended_action = "alert"

        anomaly, anomaly_reason = self.anomaly_score(
            request_count_60s
        )

        risk_score = int(
            self.clamp(
                risk_score + anomaly * 10,
                0,
                100,
            )
        )

        confidence = round(
            self.clamp(
                confidence * 0.8 + anomaly * 0.2,
                0,
                0.99,
            ),
            2,
        )

        reason = (
            f"{reason}; anomaly({anomaly_reason})"
        )

        if risk_score >= 85:
            severity = "critical"
            recommended_action = "block"

        return DetectionResult(
            attack_type=attack_type,
            severity=severity,
            risk_score=risk_score,
            confidence=confidence,
            reason=reason,
            mitre_techniques=mitre_techniques,
            recommended_action=recommended_action,
        )


detector = ThreatDetector()


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=6, max_length=256)


class SignupRequest(BaseModel):
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=120,
    )

    email: str = Field(
        ...,
        min_length=3,
        max_length=120,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=256,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    role: str


class AttackLogIn(BaseModel):
    source_ip: str
    destination_ip: str
    attack_type: str = Field(..., min_length=2, max_length=120)
    severity: str = "low"
    timestamp: datetime
    raw_message: str | None = ""
    status_code: int | None = 0
    payload: str | None = ""


class FirewallActionRequest(BaseModel):
    ip_address: str = Field(..., min_length=3, max_length=64)
    reason: str = Field(
        default="SOC analyst action",
        min_length=2,
        max_length=200,
    )


class FirewallActionResponse(BaseModel):
    success: bool
    message: str
    ip_address: str
    action: str
    reason: str | None = None
    performed_at: str | None = None


class ReportRequest(BaseModel):
    incident_id: str


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[dict[str, Any]] = Field(default_factory=list)


class AssistantMessageRequest(AssistantRequest):
    """Backward-compatible request model name."""
    pass


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=3, max_length=120)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=6, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=256)


class ThreatIntelRequest(BaseModel):
    ip: str


class SimulationRequest(BaseModel):
    target_ip: str = "192.0.2.10"
    attack_type: str = "Synthetic DoS"
    duration_seconds: int = Field(default=30, ge=1, le=300)


# -----------------------------------------------------------------------------
# Authentication helpers
# -----------------------------------------------------------------------------

def authenticate_user(
    email: str,
    password: str,
) -> dict[str, Any]:
    normalized_email = email.strip().lower()

    user = DBService.get_user_by_email(
        normalized_email
    )

    if (
        not user
        and normalized_email == "admin@soc.local"
    ):
        user = {
            "id": "seed-admin-1",
            "email": "admin@soc.local",
            "full_name": "SOC Admin",
            "role": "admin",
            "password_hash": hash_password("Admin@123"),
            "disabled": False,
        }

        DBService.upsert_seed_user(user)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    if user.get("disabled") is True:
        raise HTTPException(
            status_code=403,
            detail="User is disabled",
        )

    password_hash = str(
        user.get("password_hash") or ""
    )

    if not password_hash or not verify_password(
        password,
        password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    return user


def get_current_user(
    authorization: str | None,
) -> dict[str, Any]:
    if (
        not authorization
        or not authorization.lower().startswith("bearer ")
    ):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    token = authorization.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )

    user_id = str(payload.get("sub") or "")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
        )

    user = DBService.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if user.get("disabled") is True:
        raise HTTPException(
            status_code=403,
            detail="User is disabled",
        )

    return user


# -----------------------------------------------------------------------------
# Health data and health broadcasting
# -----------------------------------------------------------------------------

def health_payload() -> dict[str, Any]:
    return {
        "status": "Operational",
        "api_status": "Operational",
        "websocket_status": (
            "Operational"
            if ws_manager.connections
            else "Waiting"
        ),
        "database_status": "Operational",
        "uptime": "99.98%",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "cpu": "42%",
            "memory": "68%",
            "disk": "56%",
            "network": "32%",
        },
        "services": [
            {
                "name": "Backend API",
                "status": "Operational",
            },
            {
                "name": "Database",
                "status": "Operational",
            },
            {
                "name": "Firewall Service",
                "status": "Operational",
            },
            {
                "name": "WebSocket",
                "status": (
                    "Operational"
                    if ws_manager.connections
                    else "Waiting"
                ),
            },
            {
                "name": "AI/ML Models",
                "status": "Operational",
            },
        ],
    }


async def health_broadcast_loop() -> None:
    while True:
        try:
            await broadcast_soc_event(
                "system_health",
                health_payload(),
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(
                f"[WARNING] Health broadcast failed: {exc}"
            )

        await asyncio.sleep(10)


health_task: asyncio.Task | None = None


@app.on_event("startup")
async def startup_event() -> None:
    global health_task

    try:
        connect_mongo()
    except Exception as exc:
        print(
            f"[WARNING] MongoDB connection failed: {exc}"
        )

    try:
        DBService.upsert_seed_user(
            {
                "id": "seed-admin-1",
                "email": "admin@soc.local",
                "full_name": "SOC Admin",
                "role": "admin",
                "password_hash": hash_password("Admin@123"),
                "disabled": False,
            }
        )
    except Exception as exc:
        print(
            f"[WARNING] Seed user setup failed: {exc}"
        )

    health_task = asyncio.create_task(
        health_broadcast_loop()
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    global health_task

    if health_task is not None:
        health_task.cancel()

        try:
            await health_task
        except asyncio.CancelledError:
            pass

        health_task = None

    try:
        close_mongo()
    except Exception as exc:
        print(
            f"[WARNING] MongoDB shutdown error: {exc}"
        )


# -----------------------------------------------------------------------------
# Core endpoints
# -----------------------------------------------------------------------------

@app.get("/")
def root() -> dict[str, Any]:
    return {
        "message": "AI SOC Firewall backend is running",
        "api_base": "/api/v1",
        "health": "/api/v1/health",
        "system_health": "/api/v1/system/health",
        "websocket": "/ws/attacks",
        "docs": "/docs" if DOCS_ENABLED else "disabled",
    }


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
        "env": ENV,
    }


@app.get("/api/v1/system/health")
def system_health() -> dict[str, Any]:
    return health_payload()


@app.get("/api/v1/metrics")
def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# -----------------------------------------------------------------------------
# Authentication endpoints
# -----------------------------------------------------------------------------

@app.post(
    "/api/v1/auth/login",
    response_model=TokenResponse,
)
@limiter.limit(RATE_LIMIT_LOGIN)
def login(
    request: Request,
    payload: LoginRequest,
) -> dict[str, Any]:
    user = authenticate_user(
        payload.email,
        payload.password,
    )

    token = create_access_token(
        data={
            "sub": str(user["id"]),
            "email": str(user["email"]),
            "role": str(user["role"]),
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": str(user["role"]),
    }


@app.post("/api/v1/auth/signup", response_model=TokenResponse, tags=["Auth"])
@limiter.limit(RATE_LIMIT_LOGIN)
def signup(
    request: Request,
    req: SignupRequest,
) -> dict[str, Any]:
    email = req.email.strip().lower()
    full_name = req.full_name.strip()

    if DBService.get_user_by_email(email):
        raise HTTPException(
            status_code=409,
            detail="Email already exists",
        )

    user = DBService.create_user(
        {
            "id": str(uuid.uuid4()),
            "email": email,
            "full_name": full_name,
            "role": "analyst",
            "password_hash": hash_password(req.password),
            "disabled": False,
        }
    )

    token = create_access_token(
        data={
            "sub": str(user["id"]),
            "email": str(user["email"]),
            "role": str(user["role"]),
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": str(user["role"]),
    }


# -----------------------------------------------------------------------------
# Current user
# -----------------------------------------------------------------------------

@app.get(
    "/api/v1/auth/me",
    response_model=UserProfile,
)
def me(
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    user = get_current_user(authorization)

    return {
        "id": str(user["id"]),
        "email": str(user["email"]),
        "full_name": str(user.get("full_name") or ""),
        "role": str(user.get("role") or "analyst"),
    }


# -----------------------------------------------------------------------------
# WebSocket endpoint
# -----------------------------------------------------------------------------

@app.websocket("/ws/attacks")
async def attacks_websocket(
    websocket: WebSocket,
) -> None:
    await ws_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except RuntimeError:
        ws_manager.disconnect(websocket)


# -----------------------------------------------------------------------------
# Attack endpoints
# -----------------------------------------------------------------------------

@app.get("/api/v1/attacks")
@limiter.limit(RATE_LIMIT_DEFAULT)
def list_attacks(
    request: Request,
    limit: int = Query(300, ge=1, le=1000),
    authorization: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    get_current_user(authorization)
    return store.list_events(limit)


@app.get("/api/v1/attacks/{attack_id}")
def get_attack(
    attack_id: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    event = store.get_event(attack_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Attack not found",
        )

    return event


@app.post("/api/v1/attacks")
@limiter.limit(RATE_LIMIT_DEFAULT)
async def create_attack(
    request: Request,
    payload: AttackLogIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    event = payload.model_dump()
    event["timestamp"] = payload.timestamp.isoformat()

    detection = detector.analyze(event)

    event.update(
        {
            "attack_type": detection.attack_type,
            "severity": detection.severity,
            "risk_score": detection.risk_score,
            "confidence": detection.confidence,
            "reason": detection.reason,
            "mitre_techniques": detection.mitre_techniques,
            "recommended_action": detection.recommended_action,
            "action_taken": "none",
            "status": "active",
        }
    )

    if detection.recommended_action == "block":
        store.block_ip(payload.source_ip)
        event["action_taken"] = "blocked"

    saved = store.add_event(event)

    await broadcast_soc_event(
        "new_attack",
        saved,
    )

    return saved


# -----------------------------------------------------------------------------
# Firewall endpoints
# -----------------------------------------------------------------------------

@app.post(
    "/api/v1/firewall/block",
    response_model=FirewallActionResponse,
)
@limiter.limit(RATE_LIMIT_DEFAULT)
async def block_ip(
    request: Request,
    payload: FirewallActionRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    ip_address = payload.ip_address.strip()

    store.block_ip(ip_address)

    result = {
        "success": True,
        "message": f"IP {ip_address} blocked",
        "ip_address": ip_address,
        "action": "block",
        "reason": payload.reason,
        "performed_at": datetime.now(timezone.utc).isoformat(),
    }

    await broadcast_soc_event(
        "firewall_action",
        result,
    )

    return result


@app.post(
    "/api/v1/firewall/unblock",
    response_model=FirewallActionResponse,
)
@limiter.limit(RATE_LIMIT_DEFAULT)
async def unblock_ip(
    request: Request,
    payload: FirewallActionRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    ip_address = payload.ip_address.strip()

    store.unblock_ip(ip_address)

    result = {
        "success": True,
        "message": f"IP {ip_address} unblocked",
        "ip_address": ip_address,
        "action": "unblock",
        "reason": payload.reason,
        "performed_at": datetime.now(timezone.utc).isoformat(),
    }

    await broadcast_soc_event(
        "firewall_action",
        result,
    )

    return result


@app.get("/api/v1/db/firewall-rules")
def firewall_rules(
    authorization: str | None = Header(default=None),
) -> list[dict[str, str]]:
    get_current_user(authorization)

    return [
        {
            "ip_address": ip_address,
            "status": "blocked",
        }
        for ip_address in sorted(store.blocked_ips)
    ]


# -----------------------------------------------------------------------------
# Threat intelligence and geolocation
# -----------------------------------------------------------------------------

@app.get("/api/v1/threat-intel/check")
def threat_intel_get(
    ip: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    score = sum(ord(char) for char in ip) % 100

    return {
        "ip": ip,
        "reputation_score": score,
        "malicious": score >= 70,
        "country": "Unknown",
        "isp": "MockISP",
        "source": "mock",
    }


@app.post("/api/v1/threat-intel/check")
def threat_intel_post(
    payload: ThreatIntelRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return threat_intel_get(
        payload.ip,
        authorization,
    )


@app.get("/api/v1/geo/lookup")
def geo_lookup(
    ip: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    seed = sum(ord(char) for char in ip)

    return {
        "ip": ip,
        "latitude": (seed % 140) - 70,
        "longitude": ((seed * 3) % 360) - 180,
        "country": "Unknown",
        "city": "Unknown",
    }


# -----------------------------------------------------------------------------
# Reports
# -----------------------------------------------------------------------------

@app.get("/api/v1/reports")
def list_reports(
    authorization: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    get_current_user(authorization)
    return store.reports


@app.post("/api/v1/reports/generate")
@limiter.limit(RATE_LIMIT_DEFAULT)
async def generate_report(
    request: Request,
    payload: ReportRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    incident = store.get_event(payload.incident_id)

    if incident is None:
        failure = {
            "incident_id": payload.incident_id,
            "message": "incident_id not found",
        }

        await broadcast_soc_event(
            "report_failed",
            failure,
        )

        raise HTTPException(
            status_code=404,
            detail="incident_id not found",
        )

    filename = f"incident_{payload.incident_id}.pdf"
    absolute_path = REPORTS_DIR / filename

    pdf = canvas.Canvas(
        str(absolute_path),
        pagesize=A4,
    )

    y_position = 800

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(
        50,
        y_position,
        "AI SOC Firewall Incident Report",
    )

    y_position -= 30
    pdf.setFont("Helvetica", 11)

    lines = [
        f"Incident ID: {incident.get('id')}",
        f"Timestamp: {incident.get('timestamp')}",
        f"Source IP: {incident.get('source_ip')}",
        f"Destination IP: {incident.get('destination_ip')}",
        f"Attack Type: {incident.get('attack_type')}",
        f"Severity: {incident.get('severity')}",
        f"Risk Score: {incident.get('risk_score')}",
        f"Confidence: {incident.get('confidence')}",
        f"Reason: {incident.get('reason')}",
        "MITRE: " + ", ".join(
            incident.get("mitre_techniques") or []
        ),
        f"Action Taken: {incident.get('action_taken')}",
        "Generated At: "
        + datetime.now(timezone.utc).isoformat(),
    ]

    for line in lines:
        pdf.drawString(
            50,
            y_position,
            str(line),
        )

        y_position -= 18

        if y_position < 60:
            pdf.showPage()
            y_position = 800
            pdf.setFont("Helvetica", 11)

    pdf.save()

    report = {
        "report_name": filename,
        "report_path": f"reports/{filename}",
        "incident_id": payload.incident_id,
        "report_type": "incident",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    store.add_report(report)

    await broadcast_soc_event(
        "report_generated",
        report,
    )

    return report


# -----------------------------------------------------------------------------
# Logs
# -----------------------------------------------------------------------------

@app.get("/api/v1/logs")
def list_logs(
    limit: int = Query(300, ge=1, le=1000),
    search: str | None = None,
    severity: str | None = None,
    attack_type: str | None = None,
    source_ip: str | None = None,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    rows = list(store.events)

    if search:
        query = search.lower()

        rows = [
            row
            for row in rows
            if query in str(row).lower()
        ]

    if severity:
        rows = [
            row
            for row in rows
            if str(row.get("severity", "")).lower()
            == severity.lower()
        ]

    if attack_type:
        rows = [
            row
            for row in rows
            if str(row.get("attack_type", "")).lower()
            == attack_type.lower()
        ]

    if source_ip:
        rows = [
            row
            for row in rows
            if row.get("source_ip") == source_ip
        ]

    rows = rows[:limit]

    return {
        "total": len(rows),
        "items": rows,
    }


@app.get("/api/v1/logs/export")
def export_logs(
    severity: str | None = None,
    attack_type: str | None = None,
    authorization: str | None = Header(default=None),
) -> Response:
    get_current_user(authorization)

    rows = list(store.events)

    if severity:
        rows = [
            row
            for row in rows
            if str(row.get("severity", "")).lower()
            == severity.lower()
        ]

    if attack_type:
        rows = [
            row
            for row in rows
            if str(row.get("attack_type", "")).lower()
            == attack_type.lower()
        ]

    output = io.StringIO()

    fieldnames = [
        "id",
        "timestamp",
        "source_ip",
        "destination_ip",
        "attack_type",
        "severity",
        "risk_score",
        "action_taken",
        "status",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
    )

    writer.writeheader()

    for row in rows:
        writer.writerow(
            {
                field: row.get(field, "")
                for field in fieldnames
            }
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; filename=attack_logs.csv"
            )
        },
    )


# -----------------------------------------------------------------------------
# Assistant and settings
# -----------------------------------------------------------------------------

@app.post("/api/v1/assistant")
def assistant(
    payload: AssistantRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    message = payload.message.lower()

    if "critical" in message:
        count = sum(
            1
            for event in store.events
            if str(event.get("severity", "")).lower()
            == "critical"
        )

        answer = (
            f"There are currently {count} critical events."
        )

    elif "firewall" in message:
        answer = (
            "The firewall currently tracks "
            f"{len(store.blocked_ips)} blocked IP addresses."
        )

    elif "health" in message:
        answer = (
            "The backend API is operational. "
            "The WebSocket health broadcaster is active."
        )

    else:
        answer = (
            "I can summarize critical threats, firewall activity, "
            "attack logs, reports, and system health."
        )

    return {
        "answer": answer,
        "source": "local-deterministic-assistant",
    }


@app.get("/api/v1/settings")
def get_settings(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    user = get_current_user(authorization)

    return {
        "full_name": user.get("full_name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", ""),
        "notifications": True,
        "appearance": "dark",
    }


@app.patch("/api/v1/settings/profile")
def update_profile(
    payload: ProfileUpdateRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    user = get_current_user(authorization)

    user["full_name"] = payload.full_name.strip()
    user["email"] = payload.email.strip().lower()

    DBService.upsert_seed_user(user)

    return {
        "id": str(user["id"]),
        "email": str(user["email"]),
        "full_name": str(user["full_name"]),
        "role": str(user["role"]),
    }


@app.post("/api/v1/settings/password")
def change_password(
    payload: PasswordChangeRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    user = get_current_user(authorization)

    if not verify_password(
        payload.current_password,
        str(user.get("password_hash") or ""),
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect.",
        )

    user["password_hash"] = hash_password(
        payload.new_password
    )

    DBService.upsert_seed_user(user)

    return {
        "message": "Password changed successfully."
    }


# -----------------------------------------------------------------------------
# Safe synthetic simulation
# -----------------------------------------------------------------------------

@app.post("/api/v1/simulations/dos")
@limiter.limit(RATE_LIMIT_DEFAULT)
async def simulate_dos(
    request: Request,
    payload: SimulationRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    get_current_user(authorization)

    event = {
        "id": f"sim_{uuid.uuid4().hex[:10]}",
        "source_ip": "198.51.100.10",
        "destination_ip": payload.target_ip,
        "attack_type": payload.attack_type,
        "severity": "medium",
        "risk_score": 72,
        "confidence": 1.0,
        "reason": (
            "Synthetic SOC validation event. "
            "No real network traffic was generated."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_taken": "blocked",
        "status": "simulation",
        "simulation": True,
        "duration_seconds": payload.duration_seconds,
    }

    saved = store.add_event(event)

    await broadcast_soc_event(
        "new_attack",
        saved,
    )

    await broadcast_soc_event(
        "simulation_completed",
        saved,
    )

    return saved


print(
    f"[INFO] {APP_NAME} v{APP_VERSION} | ENV={ENV}"
)