"""
Configurações centralizadas do Cronograma App.

Exporta engine, session, Base, dependências HTTP, constantes JWT,
e diretórios estáticos. Substitui as variáveis globais espalhadas
pelo antigo main.py monolítico.
"""

import hashlib
import os
from pathlib import Path

from fastapi.security import HTTPBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ─── Database ─────────────────────────────────────────────────────────────────

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./cronograma.db")

if "sqlite" in DATABASE_URL:
    engine_kwargs: dict = {"connect_args": {"check_same_thread": False}}
else:
    engine_kwargs = {}

engine = create_engine(DATABASE_URL, **engine_kwargs)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# ─── JWT ──────────────────────────────────────────────────────────────────────

SECRET_KEY: str = os.environ.get(
    "JWT_SECRET", hashlib.sha256(DATABASE_URL.encode()).hexdigest()
)
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# ─── HTTP Security ────────────────────────────────────────────────────────────

security = HTTPBearer(auto_error=False)

# ─── Admin / Migration ────────────────────────────────────────────────────────

MIGRATION_SECRET: str = os.environ.get("MIGRATION_SECRET", "")

# ─── Static Files ─────────────────────────────────────────────────────────────

STATIC_DIR: Path = Path(__file__).parent / "static"
ICON_IMAGES_DIR: Path = Path(__file__).parent.parent.parent / "icon_images"

# ─── CORS Origins ─────────────────────────────────────────────────────────────

CORS_ORIGINS: list[str] = [
    "https://meu-portfolio-ebon-omega.vercel.app",
    "https://meu-portfolio.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]

# ─── Coins ────────────────────────────────────────────────────────────────────

FREEZE_COST: int = 10


def get_db():
    """Dependency FastAPI: fornece sessão SQLAlchemy por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
