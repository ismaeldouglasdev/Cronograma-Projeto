"""
Configurações centralizadas do Cronograma App.

Exporta engine, session, Base, dependências HTTP, constantes JWT,
e diretórios estáticos. Substitui as variáveis globais espalhadas
pelo antigo main.py monolítico.
"""

import hashlib
import logging
import os
from pathlib import Path

from fastapi.security import HTTPBearer
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

# ─── Database ─────────────────────────────────────────────────────────────────

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./cronograma.db")

if "sqlite" in DATABASE_URL:
    engine_kwargs: dict = {"connect_args": {"check_same_thread": False}}
else:
    # Neon (Postgres serverless) encerra conexões ociosas: valida no checkout
    # (pool_pre_ping) e recicla antes do timeout de idle (pool_recycle).
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 180,
        "pool_size": 5,
        "max_overflow": 5,
    }

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Habilita WAL mode no SQLite para melhor concorrência (leitores não bloqueiam escritores)
if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# ─── JWT ──────────────────────────────────────────────────────────────────────

logger = logging.getLogger("cronograma.config")


def _resolve_secret_key() -> str:
    """
    Resolve a chave de assinatura JWT.

    JWT_SECRET é OBRIGATÓRIO em todos os ambientes. Derivar de DATABASE_URL
    fazia a chave mudar toda vez que a senha do banco rotaciona, o que invalida
    todos os tokens e derruba o ambiente inteiro. Ver docs/rotacao-credenciais.md.
    """
    from_env = os.environ.get("JWT_SECRET")
    if from_env:
        return from_env

    # Fallback apenas para compatibilidade com instalações antigas (dev).
    # Em produção SEMPRE falha. Em dev, loga warning e usa derivado temporário.
    derived = hashlib.sha256(DATABASE_URL.encode()).hexdigest()
    env = os.environ.get("ENVIRONMENT", "development").lower()
    if env == "production":
        logger.error(
            "JWT_SECRET ausente em produção: chave derivada de DATABASE_URL. "
            "Rotacionar a senha do banco vai invalidar todos os tokens e deslogar "
            "todos os usuários. Defina JWT_SECRET no ambiente antes de continuar."
        )
        raise ValueError(
            "JWT_SECRET environment variable is required in production. "
            "Set it to avoid session invalidation when database credentials rotate."
        )
    logger.warning(
        "JWT_SECRET não definido: usando chave derivada de DATABASE_URL (apenas dev). "
        "Defina JWT_SECRET no .env para evitar invalidação de tokens ao rotacionar credenciais."
    )
    return derived


SECRET_KEY: str = _resolve_secret_key()
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

# ─── Google OAuth ─────────────────────────────────────────────────────────────

GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI: str = os.environ.get(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
)
APP_URL: str = os.environ.get("APP_URL", "http://localhost:8000")
GOOGLE_OAUTH_SCOPES: list[str] = ["openid", "email", "profile"]

# ─── Coins ────────────────────────────────────────────────────────────────────

FREEZE_COST: int = 10

# ─── Rate Limiter IP Resolution ───────────────────────────────────────────────

# Headers confiáveis para identificar IP real do cliente (ordem de prioridade).
# CF-Connecting-IP: Cloudflare substitui pelo IP real do visitante.
# X-Real-IP: nginx/proxy padrão.
# X-Forwarded-For: primeira entrada (menos confiável, controlável pelo cliente).
# Configure via env para adicionar/remover headers conforme sua infraestrutura.
RATE_LIMIT_TRUSTED_HEADERS: list[str] = [
    h.strip() for h in os.environ.get(
        "RATE_LIMIT_TRUSTED_HEADERS",
        "cf-connecting-ip,x-real-ip"
    ).split(",") if h.strip()
]

# Se True, ignora IPs privados (RFC1918) nos headers confiáveis e cai no peer TCP.
RATE_LIMIT_REJECT_PRIVATE_IPS: bool = os.environ.get(
    "RATE_LIMIT_REJECT_PRIVATE_IPS", "true"
).lower() == "true"


def get_db():
    """Dependency FastAPI: fornece sessão SQLAlchemy por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()