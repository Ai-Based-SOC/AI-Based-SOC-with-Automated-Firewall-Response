import math
import os
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypeVar, cast

from backend.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.database.mongodb import close_mongo, connect_mongo
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


# =========================================================
# CONFIGURATION
# =========================================================

APP_NAME = os.getenv("APP_NAME", "AI SOC Firewall")
APP_VERSION = os.getenv("APP_VERSION", "1.1.0")

ENV = os.getenv("ENV", "dev").lower()
DOCS_ENABLED = os.getenv("DOCS_ENABLED", "true").lower() == "true"

SECRET_KEY = os.getenv("SECRET_KEY", "")

if ENV == "prod" and len(SECRET_KEY) < 32:
    raise RuntimeError(
        "In production, SECRET_KEY must be set and contain at least 32 characters."
    )


CORS_ORIGINS_RAW = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:5173,http://127.0.0.1:5173",
)

CORS_ORIGINS = [
    origin.strip()
    for origin in CORS_ORIGINS_RAW.split(",")
    if origin.strip()
]

if ENV == "dev" and "*" not in CORS_ORIGINS:
    CORS_ORIGINS.append("*")


RATE_LIMIT_DEFAULT = os.getenv(
    "RATE_LIMIT_DEFAULT",
    "120/minute",
)

RATE_LIMIT_LOGIN = os.getenv(
    "RATE_LIMIT_LOGIN",
    "5/minute",
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)


# =========================================================
# DATABASE STARTUP / SHUTDOWN
# =========================================================

@app.on_event("startup")
def startup_event() -> None:
    """
    Connect to MongoDB and make sure the local SOC admin exists.
    """

    try:
        connect_mongo()
    except Exception as exc:
        # Development/test environments may use the DBService fallback.
        print(f"[WARNING] MongoDB connection failed: {exc}")

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

        print("[INFO] Seed administrator verified: admin@soc.local")

    except Exception as exc:
        print(f"[WARNING] Seed administrator creation failed: {exc}")


@app.on_event("shutdown")
def shutdown_event() -> None:
    try:
        close_mongo()
    except Exception as exc:
        print(f"[WARNING] MongoDB shutdown error: {exc}")


# =========================================================
# PROMETHEUS METRICS
# =========================================================

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


# =========================================================
# REQUEST CONTEXT MIDDLEWARE
# =========================================================

class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )

        request.state.request_id = request_id

        start = datetime.now(timezone.utc)

        response = await call_next(request)

        elapsed = (
            datetime.now(timezone.utc) - start
        ).total_seconds()

        path = request.url.path
        method = request.method
        status_code = response.status_code

        REQUEST_COUNT.labels(
            method=method,
            path=path,
            status=str(status_code),
        ).inc()

        REQUEST_LATENCY.labels(
            method=method,
            path=path,
        ).observe(elapsed)

        response.headers["X-Request-ID"] = request_id

        return response


# =========================================================
# SECURITY HEADERS
# =========================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"

        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        response.headers["X-XSS-Protection"] = "0"

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

        if request.url.scheme == "https":

            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
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


# =========================================================
# RATE LIMITING
# =========================================================

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RATE_LIMIT_DEFAULT],
)

app.state.limiter = limiter


async def rate_limit_exception_handler(
    request: Request,
    exc: Exception,
) -> Response:

    limited_exc = cast(
        RateLimitExceeded,
        exc,
    )

    handler = cast(
        Callable[
            [Request, RateLimitExceeded],
            Response | Awaitable[Response],
        ],
        _rate_limit_exceeded_handler,
    )

    result = handler(
        request,
        limited_exc,
    )

    if hasattr(result, "__await__"):

        return await cast(
            Awaitable[Response],
            result,
        )

    return cast(
        Response,
        result,
    )


app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_exception_handler,
)


# =========================================================
# ERROR HANDLING
# =========================================================

def _error_payload(
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

    payload = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }

    if details is not None:
        payload["error"]["details"] = details

    return payload


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:

    # IMPORTANT:
    # Do not hide Pydantic validation errors during development.
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_payload(
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
        content=_error_payload(
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
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred",
            request,
        ),
    )


# =========================================================
# PATHS / REPORTS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

REPORTS_DIR = os.path.join(
    BASE_DIR,
    "reports",
)

os.makedirs(
    REPORTS_DIR,
    exist_ok=True,
)

app.mount(
    "/reports",
    StaticFiles(directory=REPORTS_DIR),
    name="reports",
)


# =========================================================
# WEBSOCKET MANAGER
# =========================================================

class WSConnectionManager:

    def __init__(self) -> None:

        self.connections: set[WebSocket] = set()

    async def connect(
        self,
        websocket: WebSocket,
    ) -> None:

        await websocket.accept()

        self.connections.add(
            websocket
        )

    def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:

        self.connections.discard(
            websocket
        )

    async def broadcast_json(
        self,
        payload: dict[str, Any],
    ) -> None:

        dead: list[WebSocket] = []

        for websocket in list(self.connections):

            try:

                await websocket.send_json(
                    payload
                )

            except (
                WebSocketDisconnect,
                RuntimeError,
            ):

                dead.append(websocket)

        for websocket in dead:

            self.disconnect(
                websocket
            )


# =========================================================
# IN-MEMORY INCIDENT STORE
# =========================================================

class IncidentStore:

    def __init__(self) -> None:

        self.events: list[
            dict[str, Any]
        ] = []

        self.blocked_ips: set[str] = set()

        self.reports: list[
            dict[str, Any]
        ] = []

    def add_event(
        self,
        event: dict[str, Any],
    ) -> dict[str, Any]:

        item = dict(event)

        item["id"] = (
            item.get("id")
            or f"evt_{uuid.uuid4().hex[:10]}"
        )

        item["timestamp"] = (
            item.get("timestamp")
            or datetime.now(
                timezone.utc
            ).isoformat()
        )

        self.events.insert(
            0,
            item,
        )

        self.events = self.events[:5000]

        return item

    def list_events(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:

        limit = max(
            1,
            min(limit, 1000),
        )

        return self.events[:limit]

    def block_ip(
        self,
        ip: str,
    ) -> None:

        if ip:
            self.blocked_ips.add(ip)

    def unblock_ip(
        self,
        ip: str,
    ) -> None:

        self.blocked_ips.discard(ip)

    def add_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:

        self.reports.insert(
            0,
            report,
        )

        self.reports = self.reports[:1000]

        return report


store = IncidentStore()


# =========================================================
# THREAT DETECTOR
# =========================================================

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

        self.ip_failed_auth: dict[
            str,
            deque[datetime],
        ] = defaultdict(
            lambda: deque(maxlen=2000)
        )

        self.global_count: deque[int] = deque(
            maxlen=1440
        )

    @staticmethod
    def _now() -> datetime:

        return datetime.now(
            timezone.utc
        )

    @staticmethod
    def _contains_any(
        text: str,
        needles: list[str],
    ) -> bool:

        text = (text or "").lower()

        return any(
            needle in text
            for needle in needles
        )

    @staticmethod
    def _clamp(
        value: float,
        low: float,
        high: float,
    ) -> float:

        return max(
            low,
            min(high, value),
        )

    def _push(
        self,
        bucket: deque[T],
        value: T,
    ) -> None:

        bucket.append(value)

    def _count_within(
        self,
        bucket: deque[datetime],
        seconds: int,
        now: datetime,
    ) -> int:

        edge = now - timedelta(
            seconds=seconds
        )

        return sum(
            1
            for value in bucket
            if value >= edge
        )

    def _anomaly(
        self,
        current: int,
    ) -> tuple[float, str]:

        values = list(
            self.global_count
        )

        if len(values) < 30:

            return (
                0.2,
                "Insufficient baseline",
            )

        mean = sum(values) / len(values)

        variance = (
            sum(
                (value - mean) ** 2
                for value in values
            )
            / len(values)
        )

        std = (
            math.sqrt(variance)
            if variance > 0
            else 1.0
        )

        z = (
            current - mean
        ) / std

        score = 1 / (
            1 + math.exp(-z)
        )

        return (
            score,
            f"z-score={z:.2f}",
        )

    def analyze(
        self,
        event: dict[str, Any],
    ) -> DetectionResult:

        now = self._now()

        source_ip = event.get(
            "source_ip",
            "unknown",
        )

        message = (
            f"{event.get('raw_message', '')} "
            f"{event.get('payload', '')}"
        ).lower()

        status_code = int(
            event.get(
                "status_code",
                0,
            )
            or 0
        )

        self._push(
            self.ip_events[source_ip],
            now,
        )

        if status_code in (401, 403):

            self._push(
                self.ip_failed_auth[source_ip],
                now,
            )

        count_10 = self._count_within(
            self.ip_events[source_ip],
            10,
            now,
        )

        count_60 = self._count_within(
            self.ip_events[source_ip],
            60,
            now,
        )

        failed_60 = self._count_within(
            self.ip_failed_auth[source_ip],
            60,
            now,
        )

        self._push(
            self.global_count,
            count_60,
        )

        attack_type = (
            event.get("attack_type")
            or "Suspicious Activity"
        )

        severity = (
            event.get("severity")
            or "low"
        )

        risk = int(
            event.get(
                "risk_score",
                20,
            )
            or 20
        )

        confidence = 0.55

        reason = (
            "Heuristic suspicious activity"
        )

        mitre = ["T1595"]

        action = "watch"

        # DDoS / flood
        if (
            count_10 >= 25
            or count_60 >= 120
        ):

            (
                attack_type,
                severity,
                risk,
                confidence,
                reason,
                mitre,
                action,
            ) = (
                "DDoS / Flood",
                "critical",
                92,
                0.93,
                (
                    f"Burst from "
                    f"{source_ip}: "
                    f"{count_10}/10s, "
                    f"{count_60}/60s"
                ),
                ["T1498"],
                "block",
            )

        # Brute force
        elif failed_60 >= 12:

            (
                attack_type,
                severity,
                risk,
                confidence,
                reason,
                mitre,
                action,
            ) = (
                "Brute Force",
                "high",
                84,
                0.90,
                (
                    f"Failed auth burst "
                    f"from {source_ip}: "
                    f"{failed_60}/60s"
                ),
                ["T1110"],
                "block",
            )

        # SQL injection
        elif self._contains_any(
            message,
            [
                " union ",
                "select ",
                "' or 1=1",
                "sleep(",
                "information_schema",
            ],
        ):

            (
                attack_type,
                severity,
                risk,
                confidence,
                reason,
                mitre,
                action,
            ) = (
                "SQL Injection",
                "high",
                86,
                0.91,
                "SQLi signature found",
                ["T1190", "T1059"],
                "block",
            )

        # XSS
        elif self._contains_any(
            message,
            [
                "<script",
                "javascript:",
                "onerror=",
                "onload=",
            ],
        ):

            (
                attack_type,
                severity,
                risk,
                confidence,
                reason,
                mitre,
                action,
            ) = (
                "XSS Attempt",
                "medium",
                68,
                0.85,
                "XSS signature found",
                ["T1189", "T1059"],
                "alert",
            )

        anomaly_score, anomaly_reason = (
            self._anomaly(count_60)
        )

        risk = int(
            self._clamp(
                risk + anomaly_score * 10,
                0,
                100,
            )
        )

        confidence = float(
            self._clamp(
                confidence * 0.8
                + anomaly_score * 0.2,
                0,
                0.99,
            )
        )

        reason = (
            f"{reason}. "
            f"anomaly({anomaly_reason})"
        )

        if risk >= 85:

            severity = "critical"
            action = "block"

        return DetectionResult(
            attack_type=attack_type,
            severity=severity,
            risk_score=risk,
            confidence=round(
                confidence,
                2,
            ),
            reason=reason,
            mitre_techniques=mitre,
            recommended_action=action,
        )


detector = ThreatDetector()

ws_manager = WSConnectionManager()


# =========================================================
# AUTHENTICATION SCHEMAS
# =========================================================

class LoginRequest(BaseModel):

    email: str = Field(
        ...,
        min_length=3,
        max_length=120,
    )

    password: str = Field(
        ...,
        min_length=6,
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


# =========================================================
# AUTHENTICATION HELPERS
# =========================================================

def _authenticate_user(
    email: str,
    password: str,
) -> dict[str, Any]:

    normalized_email = (
        email.strip().lower()
    )

    user = DBService.get_user_by_email(
        normalized_email
    )

    # Local development fallback
    if (
        not user
        and normalized_email
        == "admin@soc.local"
    ):

        DBService.upsert_seed_user(
            {
                "id": "seed-admin-1",
                "email": "admin@soc.local",
                "full_name": "SOC Admin",
                "role": "admin",
                "password_hash": hash_password(
                    "Admin@123"
                ),
                "disabled": False,
            }
        )

        user = DBService.get_user_by_email(
            normalized_email
        )

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
        user.get(
            "password_hash",
            "",
        )
    )

    if not password_hash:

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    if not verify_password(
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
        or not authorization.lower().startswith(
            "bearer "
        )
    ):

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    token = authorization.split(
        " ",
        1,
    )[1].strip()

    if not token:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    payload = decode_access_token(
        token
    )

    user_id = str(
        payload.get(
            "sub",
            "",
        )
    ).strip()

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
        )

    user = DBService.get_user_by_id(
        user_id
    )

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


# =========================================================
# API SCHEMAS
# =========================================================

class AttackLogIn(BaseModel):

    source_ip: str

    destination_ip: str

    attack_type: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    severity: str

    timestamp: datetime

    raw_message: str | None = ""

    status_code: int | None = 0

    payload: str | None = ""


class FirewallActionRequest(BaseModel):

    ip_address: str

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


class ThreatIntelRequest(BaseModel):

    ip: str


class ThreatIntelResponse(BaseModel):

    ip: str

    reputation_score: int

    malicious: bool

    country: str | None = None

    isp: str | None = None

    source: str | None = "mock"


class ReportRequest(BaseModel):

    incident_id: str


class ReportResponse(BaseModel):

    report_name: str

    report_path: str

    generated_at: str | None = None


class ThreatHuntRequest(BaseModel):

    source_ip: str | None = None

    attack_type: str | None = None

    severity: str | None = None


class ThreatHuntResponse(BaseModel):

    total: int

    results: list[dict[str, Any]]


class MLPredictRequest(BaseModel):

    source_port: int

    dest_port: int

    bytes_sent: int

    bytes_received: int

    failed_logins: int

    request_rate: int

    is_internal_src: int

    proto: str

    severity_num: int


class IngestFileRequest(BaseModel):

    file_path: str


# =========================================================
# CORE / HEALTH
# =========================================================

@app.get("/")
def root():

    return {
        "message": "AI SOC Firewall backend is running",
        "health": "/api/v1/health",
        "ready": "/api/v1/ready",
        "metrics": "/api/v1/metrics",
        "docs": (
            "/docs"
            if DOCS_ENABLED
            else "disabled"
        ),
        "api_base": "/api/v1",
    }


@app.get(
    "/api/v1/health",
    tags=["Health"],
)
def health():

    return {
        "status": "ok",
        "time": datetime.now(
            timezone.utc
        ).isoformat(),
        "env": ENV,
    }


@app.get(
    "/api/v1/ready",
    tags=["Health"],
)
def ready():

    return {
        "status": "ready",
        "checks": {
            "database": "unknown",
            "redis": "unknown",
        },
        "time": datetime.now(
            timezone.utc
        ).isoformat(),
    }


@app.get(
    "/api/v1/metrics",
    tags=["Observability"],
)
def metrics():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# =========================================================
# AUTH LOGIN
# =========================================================

@app.post(
    "/api/v1/auth/login",
    response_model=TokenResponse,
    tags=["Auth"],
)
@limiter.limit(RATE_LIMIT_LOGIN)
def login(
    request: Request,
    req: LoginRequest,
):

    email = req.email.strip()

    password = req.password

    if not email or not password:

        raise HTTPException(
            status_code=400,
            detail="email/password required",
        )

    user = _authenticate_user(
        email,
        password,
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


# =========================================================
# CURRENT USER
# =========================================================

@app.get(
    "/api/v1/auth/me",
    response_model=UserProfile,
    tags=["Auth"],
)
def me(
    authorization: str | None = Header(
        default=None
    ),
):

    user = get_current_user(
        authorization
    )

    return {
        "id": str(user["id"]),
        "email": str(user["email"]),
        "full_name": str(
            user.get(
                "full_name",
                "",
            )
        ),
        "role": str(user["role"]),
    }


# =========================================================
# WEBSOCKET
# =========================================================

@app.websocket("/ws/attacks")
async def ws_attacks(
    websocket: WebSocket,
):

    await ws_manager.connect(
        websocket
    )

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        ws_manager.disconnect(
            websocket
        )

    except RuntimeError:

        ws_manager.disconnect(
            websocket
        )


# =========================================================
# ATTACKS
# =========================================================

@app.get(
    "/api/v1/attacks",
    tags=["Attacks"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def list_attacks(
    request: Request,
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    return store.list_events(
        limit
    )


@app.post(
    "/api/v1/attacks",
    tags=["Attacks"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
async def create_attack(
    request: Request,
    payload: AttackLogIn,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    event = payload.model_dump()

    event["timestamp"] = (
        payload.timestamp.isoformat()
    )

    detection = detector.analyze(
        event
    )

    event["risk_score"] = (
        detection.risk_score
    )

    event["confidence"] = (
        detection.confidence
    )

    event["reason"] = (
        detection.reason
    )

    event["mitre_techniques"] = (
        detection.mitre_techniques
    )

    event["recommended_action"] = (
        detection.recommended_action
    )

    event["action_taken"] = "none"

    if (
        detection.recommended_action
        == "block"
    ):

        store.block_ip(
            payload.source_ip
        )

        event["action_taken"] = (
            "blocked"
        )

    saved = store.add_event(
        event
    )

    await ws_manager.broadcast_json(
        {
            "event": "new_attack",
            "data": saved,
        }
    )

    return saved


# =========================================================
# FIREWALL
# =========================================================

@app.post(
    "/api/v1/firewall/block",
    response_model=FirewallActionResponse,
    tags=["Firewall"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def block_ip(
    request: Request,
    req: FirewallActionRequest,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    store.block_ip(
        req.ip_address
    )

    return {
        "success": True,
        "message": (
            f"IP {req.ip_address} blocked"
        ),
        "ip_address": req.ip_address,
        "action": "block",
    }


@app.post(
    "/api/v1/firewall/unblock",
    response_model=FirewallActionResponse,
    tags=["Firewall"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def unblock_ip(
    request: Request,
    req: FirewallActionRequest,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    store.unblock_ip(
        req.ip_address
    )

    return {
        "success": True,
        "message": (
            f"IP {req.ip_address} unblocked"
        ),
        "ip_address": req.ip_address,
        "action": "unblock",
    }


# =========================================================
# THREAT INTELLIGENCE
# =========================================================

@app.get(
    "/api/v1/threat-intel/check",
    response_model=ThreatIntelResponse,
    tags=["Threat Intelligence"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def check_ip_get(
    request: Request,
    ip: str,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    score = sum(
        ord(character)
        for character in ip
    ) % 100

    return {
        "ip": ip,
        "reputation_score": score,
        "malicious": score >= 70,
        "country": "Unknown",
        "isp": "MockISP",
        "source": "mock",
    }


@app.post(
    "/api/v1/threat-intel/check",
    response_model=ThreatIntelResponse,
    tags=["Threat Intelligence"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def check_ip_post(
    request: Request,
    payload: ThreatIntelRequest,
    authorization: str | None = Header(
        default=None
    ),
):

    return check_ip_get(
        request,
        payload.ip,
        authorization,
    )


# =========================================================
# REPORTS
# =========================================================

@app.post(
    "/api/v1/reports/generate",
    response_model=ReportResponse,
    tags=["Reports"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def generate_report(
    request: Request,
    payload: ReportRequest,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    incident = next(
        (
            event
            for event in store.events
            if event.get("id")
            == payload.incident_id
        ),
        None,
    )

    if not incident:

        raise HTTPException(
            status_code=404,
            detail="incident_id not found",
        )

    filename = (
        f"incident_{payload.incident_id}.pdf"
    )

    absolute_path = os.path.join(
        REPORTS_DIR,
        filename,
    )

    relative_path = (
        f"reports/{filename}"
    )

    pdf = canvas.Canvas(
        absolute_path,
        pagesize=A4,
    )

    y = 800

    pdf.setFont(
        "Helvetica-Bold",
        16,
    )

    pdf.drawString(
        50,
        y,
        "AI SOC Firewall Incident Report",
    )

    y -= 30

    pdf.setFont(
        "Helvetica",
        11,
    )

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
        (
            "MITRE: "
            + ", ".join(
                incident.get(
                    "mitre_techniques",
                    [],
                )
            )
        ),
        f"Action Taken: {incident.get('action_taken')}",
        (
            "Generated At: "
            + datetime.now(
                timezone.utc
            ).isoformat()
        ),
    ]

    for line in lines:

        pdf.drawString(
            50,
            y,
            str(line),
        )

        y -= 18

        if y < 60:

            pdf.showPage()

            y = 800

            pdf.setFont(
                "Helvetica",
                11,
            )

    pdf.save()

    report = {
        "report_name": filename,
        "report_path": relative_path,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    store.add_report(
        report
    )

    return report


# =========================================================
# THREAT HUNTING
# =========================================================

@app.post(
    "/api/v1/hunting/search",
    response_model=ThreatHuntResponse,
    tags=["Threat Hunting"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def search_hunts(
    request: Request,
    payload: ThreatHuntRequest,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    rows = store.events

    if payload.source_ip:

        rows = [
            row
            for row in rows
            if row.get("source_ip")
            == payload.source_ip
        ]

    if payload.attack_type:

        rows = [
            row
            for row in rows
            if (
                row.get(
                    "attack_type",
                    "",
                )
                or ""
            ).lower()
            == payload.attack_type.lower()
        ]

    if payload.severity:

        rows = [
            row
            for row in rows
            if (
                row.get(
                    "severity",
                    "",
                )
                or ""
            ).lower()
            == payload.severity.lower()
        ]

    return {
        "total": len(rows),
        "results": rows[:300],
    }


# =========================================================
# DATABASE ADMIN
# =========================================================

@app.get(
    "/api/v1/db/firewall-rules",
    tags=["DB Admin"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def list_firewall_rules(
    request: Request,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    return [
        {
            "ip_address": ip,
            "status": "blocked",
        }
        for ip in sorted(
            store.blocked_ips
        )
    ]


# =========================================================
# LOG INGESTION
# =========================================================

@app.post(
    "/api/v1/ingestion/file",
    tags=["Log Ingestion"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def ingest_from_file(
    request: Request,
    payload: IngestFileRequest,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    path = Path(
        payload.file_path
    )

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="file_path not found",
        )

    if path.is_dir():

        raise HTTPException(
            status_code=400,
            detail="file_path must be a file",
        )

    return {
        "message": "File ingestion queued",
        "file_path": str(path),
    }


# =========================================================
# MACHINE LEARNING
# =========================================================

@app.post(
    "/api/v1/ml/predict",
    tags=["ML"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def predict(
    request: Request,
    payload: MLPredictRequest,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    score = min(
        100,
        max(
            0,
            int(
                payload.request_rate * 0.5
                + payload.failed_logins * 3
                + payload.bytes_sent / 10000
                + payload.bytes_received / 10000
                + payload.severity_num * 10
            ),
        ),
    )

    label = (
        "anomaly"
        if score >= 70
        else "normal"
    )

    return {
        "risk_score": score,
        "label": label,
    }


# =========================================================
# GEO LOCATION
# =========================================================

@app.get(
    "/api/v1/geo/lookup",
    tags=["Geo"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def geo_lookup(
    request: Request,
    ip: str,
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    seed = sum(
        ord(character)
        for character in ip
    )

    latitude = (
        seed % 140
    ) - 70

    longitude = (
        (seed * 3) % 360
    ) - 180

    return {
        "ip": ip,
        "latitude": latitude,
        "longitude": longitude,
        "country": "Mockland",
        "city": "Mock City",
    }


# =========================================================
# SIEM EXPORT
# =========================================================

@app.get(
    "/api/v1/siem/export",
    tags=["SIEM"],
)
@limiter.limit(RATE_LIMIT_DEFAULT)
def export_siem(
    request: Request,
    limit: int = Query(
        500,
        ge=1,
        le=5000,
    ),
    authorization: str | None = Header(
        default=None
    ),
):

    get_current_user(
        authorization
    )

    return {
        "count": min(
            limit,
            len(store.events),
        ),
        "events": store.events[:limit],
    }


# =========================================================
# APPLICATION STARTUP MESSAGE
# =========================================================

print(
    f"[INFO] {APP_NAME} v{APP_VERSION}"
    f" | ENV={ENV}"
)