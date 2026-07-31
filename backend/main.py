import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logger import (
    logger, correlation_id_ctx, request_id_ctx
)
from backend.core.metrics import (
    get_metrics_export, REQUEST_LATENCY
)
from database.postgres import init_db, SessionLocal
from backend.models.schema import User, UserRole
from backend.auth.jwt import get_password_hash

# Import APIRouters
from backend.api.auth import router as auth_router
from backend.api.agent import router as agent_router
from backend.api.audit import router as audit_router
from backend.api.explain import router as explain_router
from backend.api.redact import router as redact_router
from backend.api.health import router as health_router


def seed_default_enterprise_users():
    """
    Automatically seed test accounts (admin, auditor, developer, customer)
    if database users table is empty.
    """
    db: Session = SessionLocal()
    try:
        if db.query(User).count() == 0:
            logger.info("Seeding default enterprise accounts for RBAC verification...")
            test_accounts = [
                ("admin@traceai.enterprise", "AdminSecret123!", UserRole.ADMIN.value),
                ("auditor@traceai.enterprise", "AuditorSecret123!", UserRole.AUDITOR.value),
                ("dev@traceai.enterprise", "DevSecret123!", UserRole.DEVELOPER.value),
                ("customer@traceai.enterprise", "CustomerSecret123!", UserRole.CUSTOMER.value),
            ]
            for email, raw_pw, role in test_accounts:
                db.add(User(
                    email=email,
                    role=role,
                    password_hash=get_password_hash(raw_pw)
                ))
            db.commit()
            logger.info("Seeded 4 test users (admin, auditor, dev, customer)")
    except Exception as exc:
        logger.warning("User seeding notice", error=str(exc))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application Startup
    logger.info("Booting Decision Path Auditor API Server...", environment=settings.ENVIRONMENT)
    init_db()
    seed_default_enterprise_users()
    yield
    # Application Shutdown
    logger.info("Shutting down Decision Path Auditor API Server")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Governance Platform capturing the complete reasoning chain behind AI Agent decisions.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_and_metrics_middleware(request: Request, call_next):
    """
    Injects Correlation ID and Request ID into contextvars and response headers,
    and measures HTTP latency for Prometheus histograms.
    """
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    corr_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    request_id_ctx.set(req_id)
    correlation_id_ctx.set(corr_id)

    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    # Record Prometheus metrics
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=str(response.status_code)
    ).observe(duration)

    response.headers["X-Request-ID"] = req_id
    response.headers["X-Correlation-ID"] = corr_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception middleware returning structured JSON error responses.
    """
    logger.error(
        "Unhandled server exception",
        path=request.url.path,
        error=str(exc)
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
            "correlation_id": correlation_id_ctx.get(),
            "request_id": request_id_ctx.get()
        }
    )


# Prometheus Metrics Route
@app.get("/metrics", tags=["Observability"])
def get_prometheus_metrics():
    """
    Prometheus scrape endpoint for Grafana monitoring.
    """
    payload, content_type = get_metrics_export()
    return Response(content=payload, media_type=content_type)


# Register API Routers under /api/v1 and root
app.include_router(auth_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(explain_router, prefix="/api/v1")
app.include_router(redact_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root_info():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
        "metrics_url": "/metrics"
    }
