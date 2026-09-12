"""
Cronograma App — Entry Point.

FastAPI setup, startup event, middleware, routers.
A lógica de negócio ficou em services/, models/, routes/.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import ICON_IMAGES_DIR, STATIC_DIR, get_db, security
from logger import get_logger
from middleware import (
    security_headers_middleware,
    log_requests_middleware,
    setup_cors,
)
from services.auth_service import verify_token
from services.gamification_service import cleanup_stale_guests
from services.migration_service import run_migrations

# Import models para registrar tabelas no Base.metadata
import models  # noqa: F401

# Import routes
from routes.auth import router as auth_router
from routes.areas import router as areas_router
from routes.tasks import router as tasks_router
from routes.sessoes import router as sessoes_router
from routes.gamification import router as gamification_router
from routes.admin import router as admin_router

log = get_logger("cronograma.main")

app = FastAPI()


@app.on_event("startup")
def _startup():
    """Cria tabelas, roda migrações e limpa guests antigos."""
    from config import engine, SessionLocal, Base

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

# ─── Include routers ──────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(areas_router)
app.include_router(tasks_router)
app.include_router(sessoes_router)
app.include_router(gamification_router)
app.include_router(admin_router)
