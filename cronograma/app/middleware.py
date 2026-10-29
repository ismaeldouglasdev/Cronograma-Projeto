"""Middleware: rate limiter, security headers, request logging."""

import atexit
import json
import os
import re
import secrets
import sys
import threading
import time
from html import escape

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from config import CORS_ORIGINS
from logger import get_logger, log_request

log = get_logger("cronograma.main")


# ─── Rate Limiter (memória + persistência) ────────────────────────────────────


class RateLimiter:
    """Sliding-window rate limiter thread-safe, com persistência opcional.

    Camada L1 (memória) é a fonte de verdade durante a vida do processo; um
    write-through descarrega as janelas ativas no banco a cada ~5s, e o
    primeiro check() carrega o que existir no banco — assim um restart do
    uvicorn (deploy, crash, dormência do Render free) não zera a cota.

    Persistência desligada sob pytest (não polui o cronograma.db de dev e
    mantém os testes existentes determinísticos); os testes de persistência
    constroem um RateLimiter explícito com session_factory temporário.
    """

    def __init__(self, persist=None, session_factory=None):
        self._store: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 60.0
        self._last_cleanup = time.time()
        if persist is None:
            persist = "pytest" not in sys.modules
        self._persist = persist
        self._session_factory = session_factory
        self._loaded = not persist
        self._dirty: set[str] = set()
        self._last_flush = time.time()
        self._flush_interval = 5.0
        if persist:
            atexit.register(self.flush)

    def _get_session_factory(self):
        if self._session_factory is not None:
            return self._session_factory
        from config import SessionLocal

        return SessionLocal

    def _ensure_loaded(self):
        """Carrega buckets do banco uma única vez (lazy, no primeiro check)."""
        if self._loaded:
            return
        self._loaded = True
        try:
            factory = self._get_session_factory()
            db = factory()
            try:
                db.execute(
                    text(
                        "CREATE TABLE IF NOT EXISTS rate_limit_buckets ("
                        "key TEXT PRIMARY KEY, hits TEXT NOT NULL, "
                        "updated_at FLOAT NOT NULL)"
                    )
                )
                db.commit()
                rows = db.execute(
                    text("SELECT key, hits FROM rate_limit_buckets")
                ).fetchall()
                cutoff = time.time() - 3600.0
                for key, hits_json in rows:
                    try:
                        hits = [float(h) for h in json.loads(hits_json)]
                    except (TypeError, ValueError):
                        continue
                    hits = [h for h in hits if h > cutoff]
                    if hits:
                        self._store[key] = hits
            finally:
                db.close()
        except Exception as e:
            # DB fora do ar: rate limit segue em memória (defesa em profundidade,
            # não vale derrubar request por causa dele).
            log.warning("Rate limiter: load from DB failed", extra={"error": str(e)})

    def _flush_locked(self):
        """Descarrega buckets sujos no banco. Chamar COM o lock ou após snapshot."""
        if not self._persist or not self._dirty:
            return
        with self._lock:
            dirty = set(self._dirty)
            snapshot = {k: list(self._store.get(k, [])) for k in dirty}
        if not snapshot:
            return
        try:
            factory = self._get_session_factory()
            db = factory()
            try:
                db.execute(
                    text(
                        "CREATE TABLE IF NOT EXISTS rate_limit_buckets ("
                        "key TEXT PRIMARY KEY, hits TEXT NOT NULL, "
                        "updated_at FLOAT NOT NULL)"
                    )
                )
                now = time.time()
                cutoff = now - 3600.0
                for key, hits in snapshot.items():
                    hits = [h for h in hits if h > cutoff]
                    db.execute(
                        text("DELETE FROM rate_limit_buckets WHERE key = :k"),
                        {"k": key},
                    )
                    if hits:
                        db.execute(
                            text(
                                "INSERT INTO rate_limit_buckets "
                                "(key, hits, updated_at) VALUES (:k, :h, :t)"
                            ),
                            {"k": key, "h": json.dumps(hits), "t": now},
                        )
                # prune global barato: remove linhas velhas de outras chaves
                db.execute(
                    text("DELETE FROM rate_limit_buckets WHERE updated_at < :c"),
                    {"c": cutoff},
                )
                db.commit()
            finally:
                db.close()
            # Only clear dirty set AFTER successful commit
            with self._lock:
                self._dirty.difference_update(dirty)
        except Exception as e:
            log.warning("Rate limiter: flush to DB failed", extra={"error": str(e)})

    def flush(self):
        """Ponto público para flush forçado (atexit + testes)."""
        if not self._persist:
            return
        self._flush_locked()

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
            self._ensure_loaded()
            self._cleanup()
            now = time.time()
            window_start = now - window_seconds
            if key not in self._store:
                self._store[key] = []
            self._store[key] = [t for t in self._store[key] if t > window_start]
            if len(self._store[key]) >= max_requests:
                self._dirty.add(key)
                allowed = False
            else:
                self._store[key].append(now)
                self._dirty.add(key)
                allowed = True
            should_flush = (
                self._persist and now - self._last_flush >= self._flush_interval
            )
            if should_flush:
                self._last_flush = now
        if should_flush:
            self._flush_locked()
        return allowed

    def retry_after(self, key: str, window_seconds: int = 60) -> int:
        """Segundos ate a janela liberar uma vaga (minimo 1, nunca 0)."""
        with self._lock:
            hits = self._store.get(key) or []
            if not hits:
                return 1
            oldest = min(hits)
            return max(1, int(window_seconds - (time.time() - oldest)) + 1)


rate_limiter = RateLimiter()


class RateLimitExceeded(HTTPException):
    """429 com Retry-After, para o cliente poder esperar o tempo exato."""

    def __init__(self, retry_after: int, detail: str):
        super().__init__(status_code=429, detail=detail, headers={"Retry-After": str(retry_after)})
        self.retry_after = retry_after


def rate_limit(key: str, max_req: int = 30, window: int = 60):
    if not rate_limiter.check(key, max_req, window):
        retry_after = rate_limiter.retry_after(key, window)
        raise RateLimitExceeded(
            retry_after,
            f"Muitas requisições. Tente novamente em {retry_after}s.",
        )


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
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self'; "
        "font-src 'self' https://fonts.gstatic.com; "
        "frame-ancestors 'none'"
    )
    return response


# ─── Request Logging Middleware ──────────────────────────────────────────────────


async def log_requests_middleware(request, call_next):
    """Loga todas as requisições HTTP com duração."""
    # General rate limit: 120 req/min por IP (pula para /static/)
    ip = get_client_ip(request)
    if not request.url.path.startswith("/static"):
        try:
            rate_limit(f"general:{ip}", max_req=120, window=60)
        except HTTPException as e:
            # JSONResponse, não Response: content tem de ser str/bytes. Passar
            # o dict direto fazia o limiter geral estourado responder 500 em
            # vez de 429 ("'dict' object has no attribute 'encode'").
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=getattr(e, "headers", None) or {},
            )

    start_time = time.time()
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


def _is_private(host: str) -> bool:
    """True para loopback/private/link-local — nunca é o IP real de um cliente."""
    try:
        import ipaddress

        return ipaddress.ip_address(host).is_private or ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def get_client_ip(request) -> str:
    """Resolve o IP real do cliente para usar como chave de rate limit.

    O uvicorn roda com --proxy-headers ligado e reescreve `request.client.host`
    com a entrada MAIS À ESQUERDA do X-Forwarded-For — que é o que o cliente
    mandar. Usar isso como chave deixa o rate limit burlável: verificado em
    produção, 8 requests com `X-Forwarded-For` variando passaram todos, com
    limite de 5/min.

    Ordem de confiança:
      1. CF-Connecting-IP — a Cloudflare SUBSTITUI esse header pelo IP real do
         visitante (nunca anexa o valor do cliente). Confirmado que a Cloudflare
         esta na frente: todo response volta com `server: cloudflare` + `cf-ray`.
      2. Peer TCP — nunca falsificavel. O startCommand desliga a confiança em
         X-Forwarded-For (`--forwarded-allow-ips=""`) justamente para que
         `request.client.host` seja o peer de verdade e nao um header.

    X-Forwarded-For e ignorado de proposito: nenhuma das entradas dele e
    confiavel quando o cliente pode escolher o proprio header.

    Ressalva: se a Cloudflare um dia sair de frente, todo mundo cai no peer TCP
    (compartilhado no Render) e o limite volta a ser global em vez de por IP.
    Nesse caso o certo e apontar um proxy proprio ou trocar a estrategia.
    """
    connecting_ip = request.headers.get("cf-connecting-ip")
    if connecting_ip and not _is_private(connecting_ip):
        return connecting_ip

    return request.client.host if request.client else "unknown"


def verify_token(token: str):
    """Verifica token JWT — delega à fonte única (services.auth_service)."""
    from services.auth_service import verify_token as _verify_token

    return _verify_token(token)


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


# Regras de senha. Mantidas em Python e espelhadas em static/auth.js
# (PASSWORD_RULES) — as duas listas precisam continuar iguais, senao o
# frontend aceita o que o backend rejeita (e vice-versa).
# O teste test_api.py::test_regras_de_senha_js_e_python_batem_valida a paridade.
PASSWORD_MIN_LENGTH = 8
PASSWORD_RULES: tuple[tuple[str, str], ...] = (
    (r".{%d,}" % PASSWORD_MIN_LENGTH, f"Senha deve ter pelo menos {PASSWORD_MIN_LENGTH} caracteres"),
    (r"[a-zA-Z]", "Senha deve conter pelo menos uma letra"),
    (r"[0-9]", "Senha deve conter pelo menos um número"),
)


def validate_password(password: str) -> tuple[bool, str]:
    """Valida a senha e devolve a PRIMEIRA regra violada, em pt-BR.

    Devolve a mensagem em vez de so um bool porque a UI precisa dizer qual
    regra faltou — um 400 com "senha inválida" não ajuda ninguém a corrigir.
    """
    for pattern, message in PASSWORD_RULES:
        if not re.search(pattern, password):
            return False, message
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


# ─── CORS Setup ────────────────────────────────────────────────────────────────


def setup_cors(app):
    """Configura CORS para o FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT", "HEAD", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
