"""
Cronograma App — Entry Point.

FastAPI setup, startup, middleware, routers.
A lógica de negócio ficou em services/, models/, routes/.
"""

from contextlib import asynccontextmanager
import time

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from config import ICON_IMAGES_DIR, STATIC_DIR
from logger import get_logger
from middleware import log_requests_middleware, security_headers_middleware, setup_cors
from services.gamification_service import cleanup_stale_guests
from services.migration_service import run_migrations

# Import models para registrar tabelas no Base.metadata
import models  # noqa: F401

# Import routes
from routes.admin import router as admin_router
from routes.areas import router as areas_router
from routes.auth import router as auth_router
from routes.gamification import router as gamification_router
from routes.missions import router as missions_router
from routes.sessoes import router as sessoes_router
from routes.social import router as social_router
from routes.stats import router as stats_router
from routes.tasks import router as tasks_router

log = get_logger("cronograma.main")

# ─── Prometheus Metrics ──────────────────────────────────────────────────────────

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Cria tabelas, roda migrações e limpa guests antigos."""
    from config import Base, SessionLocal, engine

    Base.metadata.create_all(engine)
    run_migrations(engine)

    try:
        db = SessionLocal()
        try:
            removed = cleanup_stale_guests(db)
            if removed:
                log.info("Stale guest accounts removed", extra={"removed": removed})
        finally:
            db.close()
    except Exception as e:
        log.warning("Guest cleanup failed", extra={"error": str(e)})

    yield


app = FastAPI(lifespan=lifespan)


# ─── Metrics Middleware ──────────────────────────────────────────────────────────


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect Prometheus metrics for each request."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    # Normalize endpoint for metrics (strip IDs)
    path = request.url.path
    for prefix in [
        "/api/v1/areas/",
        "/api/v1/tasks/",
        "/api/v1/sessoes/",
        "/api/v1/friends/",
        "/api/v1/clubs/",
        "/areas/",
        "/tasks/",
        "/sessoes/",
        "/friends/",
        "/clubs/",
    ]:
        if path.startswith(prefix):
            path = prefix.rstrip("/") + "/:id"
            break

    http_requests_total.labels(
        method=request.method,
        endpoint=path,
        status=response.status_code,
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=path,
    ).observe(duration)

    return response


@app.get("/metrics")
@app.get("/api/v1/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ─── Health Check ──────────────────────────────────────────────────────────────


@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    from sqlalchemy import text

    from config import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {e}"
    finally:
        db.close()

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0",
    }


# ─── CORS ─────────────────────────────────────────────────────────────────────

setup_cors(app)

# ─── Middlewares HTTP ──────────────────────────────────────────────────────────

app.middleware("http")(security_headers_middleware)
app.middleware("http")(log_requests_middleware)

# ─── Static files ─────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
if ICON_IMAGES_DIR.exists():
    app.mount(
        "/icon_images", StaticFiles(directory=str(ICON_IMAGES_DIR)), name="icon_images"
    )

# ─── Routers ──────────────────────────────────────────────────────────────────
# Estratégia de compatibilidade:
# - Páginas (/, /app) e endpoints que precisam ficar na raiz (auth/OAuth/emails,
#   /logs/client, /admin/* legados, /debug/*) continuam acessíveis sem prefixo.
# - APIs de dados ficam sob /api/v1 (nova convenção) e também sem prefixo para
#   manter compatibilidade com clientes antigos/local.
# - Auth router (prefixo interno /auth) é montado na raiz e em /api/v1 para
#   suportar OAuth callback, links de e-mail e testes/clientes v1.

API_PREFIX = "/api/v1"

# Auth: /auth/* e /api/v1/auth/*
app.include_router(auth_router)
app.include_router(auth_router, prefix=API_PREFIX)

# APIs de dados: /api/v1/* e também raiz (compatibilidade)
for router in (
    areas_router,
    tasks_router,
    sessoes_router,
    gamification_router,
    stats_router,
    missions_router,
    social_router,
):
    app.include_router(router, prefix=API_PREFIX)
    app.include_router(router)

# Admin/debug/páginas/logs (router sem prefixo interno): raiz e /api/v1
app.include_router(admin_router)
app.include_router(admin_router, prefix=API_PREFIX)
