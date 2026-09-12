"""Middleware: rate limiter, security headers, request logging."""

import os
import re
import secrets
import threading
import time
from html import escape

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from config import CORS_ORIGINS
from logger import get_logger, log_request

log = get_logger("cronograma.main")


# ─── Rate Limiter (in-memory) ─────────────────────────────────────────────────


class RateLimiter:
    """Simple in-memory sliding-window rate limiter. Thread-safe."""

    def __init__(self):
        self._store: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 60.0
        self._last_cleanup = time.time()

    def _cleanup(self):
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        cutoff = now - 60.0
        expired = [k for k, v in self._store.items() if all(t < cutoff for t in v)]
        for k in expired:
            del self._store[k]
        self._last_cleanup = now

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        with self._lock:
            self._cleanup()
            now = time.time()
            window_start = now - window_seconds
            if key not in self._store:
                self._store[key] = []
            self._store[key] = [t for t in self._store[key] if t > window_start]
            if len(self._store[key]) >= max_requests:
                return False
            self._store[key].append(now)
            return True


rate_limiter = RateLimiter()


def rate_limit(key: str, max_req: int = 30, window: int = 60):
    if not rate_limiter.check(key, max_req, window):
        raise HTTPException(status_code=429, detail="Muitas requisições. Tente novamente em instantes.")


# ─── Security Headers Middleware ────────────────────────────────────────────────


async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"  # Desliga legacy, usamos CSP
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # Estáticos: sempre revalidar via ETag (evita cache stale após deploys)
    if request.url.path.startswith("/static") or request.url.path.startswith("/icon_images"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    # CSP permissivo para app com CDN/Chart.js inline
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "font-src 'self' https://fonts.gstatic.com; "
        "frame-ancestors 'none'"
    )
    return response


# ─── Request Logging Middleware ──────────────────────────────────────────────────


async def log_requests_middleware(request, call_next):
    """Loga todas as requisições HTTP com duração."""
    # General rate limit: 120 req/min por IP (pula para /static/)
    if not request.url.path.startswith("/static"):
        ip = request.client.host if request.client else "unknown"
        try:
            rate_limit(f"general:{ip}", max_req=120, window=60)
        except HTTPException as e:
            return Response(status_code=e.status_code, content={"detail": e.detail})

    start_time = time.time()
    ip = request.client.host if request.client else None
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    # Extract user_id from auth header if present
    user_id = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header[len("Bearer "):]
            valid, uid = verify_token(token)
            if valid:
                user_id = uid
        except Exception:
            pass

    log_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        ip=ip,
    )
    return response


# ─── Helper Functions ───────────────────────────────────────────────────────────


def verify_token(token: str):
    """Helper: verifica token JWT (usado no middleware de logging)."""
    # Esta é uma versão simplificada para o middleware.
    # Em produção, usaria auth_service.verify_token()
    try:
        from jose import JWTError, jwt
        from config import SECRET_KEY, ALGORITHM

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return True, int(user_id)
        return False, 0
    except Exception:
        return False, 0


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    if not re.search(r"[a-zA-Z]", password):
        return False, "Senha deve conter pelo menos uma letra"
    if not re.search(r"[0-9]", password):
        return False, "Senha deve conter pelo menos um número"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Senha deve conter pelo menos um caractere especial"
    return True, ""


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except (ValueError, TypeError):
        pass
    # Legacy accounts created before bcrypt migration stored SHA-256 hex
    if re.fullmatch(r"[0-9a-f]{64}", hashed_password):
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    return False


def generate_verification_token() -> str:
    import uuid
    return str(uuid.uuid4())


def sendVerificationEmail(user, token: str):
    log = get_logger("cronograma.auth")
    log.info(
        "Verification email",
        extra={
            "action": "send_verification_email",
            "email": user.email,
            "token_preview": token[:8] + "...",
        },
    )
    return True


# ─── CORS Setup ────────────────────────────────────────────────────────────────


def setup_cors(app):
    """Configura CORS para o FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT", "HEAD", "OPTIONS"],
        allow_headers=["*"],
    )