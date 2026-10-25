"""
Serviços de autenticação: JWT, hashing de senhas, verificação de tokens.

Suporta tokens legados (base64+hash) para backward compatibility durante migração.
"""

import base64
import hashlib
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session

from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    get_db,
    security,
)
from logger import get_logger

from models.user import User

auth_log = get_logger("cronograma.auth")


# ─── Password Helpers ─────────────────────────────────────────────────────────


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
        if not hashed_password:
            return False
        return _bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except (ValueError, TypeError):
        pass

    # Legacy accounts created before bcrypt migration stored SHA-256 hex
    if hashed_password and re.fullmatch(r"[0-9a-f]{64}", hashed_password):
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    auth_log.error(
        "Unsupported password hash format",
        extra={"action": "verify_password_unknown_hash"},
    )
    return False


def generate_verification_token() -> str:
    return str(uuid.uuid4())


# ─── JWT ──────────────────────────────────────────────────────────────────────


def create_access_token(
    user_id: int, is_guest: bool = False, token_version: int = 0
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "guest": is_guest,
        "ver": int(token_version or 0),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, token_version: int = 0) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "ver": int(token_version or 0),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _token_version_matches(db: Session | None, user_id: int, claim_version) -> bool:
    """Confere existência do usuário e a versão do token contra o banco.

    `db=None` mantém o modo stateless usado no logging de requisições. Nos
    pontos que autenticam de verdade (dependência e refresh) o banco é
    consultado — é o que permite revogar tokens ao trocar a senha.
    """
    if db is None:
        return True
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    return int(claim_version or 0) == int(user.token_version or 0)


def verify_refresh_token(
    refresh_token: str, db: Session | None = None
) -> tuple[bool, int]:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        auth_log.warning(
            "Refresh token expired",
            extra={"action": "refresh_token_expired"},
        )
        return False, 0
    except JWTError:
        return False, 0

    if payload.get("type") != "refresh":
        auth_log.warning(
            "Access token used as refresh token",
            extra={"action": "refresh_token_wrong_type"},
        )
        return False, 0

    sub = payload.get("sub")
    if sub is None:
        return False, 0
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        return False, 0
    if not _token_version_matches(db, user_id, payload.get("ver")):
        auth_log.warning(
            "Refresh token revoked by version mismatch",
            extra={"user_id": user_id, "action": "refresh_token_revoked"},
        )
        return False, 0
    return True, user_id


# ─── OAuth (Google) ────────────────────────────────────────────────────────────

def generate_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) using S256."""
    import base64
    import hashlib
    import secrets

    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


def generate_state() -> str:
    import secrets

    return secrets.token_urlsafe(32)


def verify_token(token: str, db: Session | None = None) -> tuple[bool, int]:
    """Verify a JWT access token.

    Handles both new python-jose tokens and legacy tokens
    for backward compatibility during migration.

    Args:
        token: The JWT token to verify
        db: optional session; when provided, checks the user still exists and
            the token's `ver` claim matches the user's current token_version.

    Returns:
        Tuple of (is_valid, user_id)
    """
    # First, try to decode as new JWT format
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type", "access")

        if token_type != "access":
            auth_log.warning(
                "Invalid token type used",
                extra={"token_type": token_type, "action": "verify_token"},
            )
            return False, 0

        if user_id is None:
            return False, 0
        parsed_user_id = int(user_id)
        if not _token_version_matches(db, parsed_user_id, payload.get("ver")):
            auth_log.warning(
                "Access token revoked by version mismatch",
                extra={"user_id": parsed_user_id, "action": "verify_token_revoked"},
            )
            return False, 0
        return True, parsed_user_id
    except ExpiredSignatureError:
        auth_log.warning(
            "Token expired",
            extra={"action": "verify_token_expired"},
        )
        return False, 0
    except JWTError:
        # Not a valid JWT, try legacy format for backward compatibility
        pass

    # Legacy token verification (for backward compatibility)
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False, 0
        encoded, signature = parts
        data = base64.b64decode(encoded.encode()).decode()
        user_id_str, expire_str = data.split(":")
        expire = int(expire_str)
        if time.time() > expire:
            return False, 0
        expected_sig = hashlib.sha256((data + SECRET_KEY).encode()).hexdigest()[:16]
        if signature != expected_sig:
            return False, 0
        legacy_user_id = int(user_id_str)
        # Legado não tem claim de versão: só continua válido enquanto o usuário
        # nunca passou por reset/logout global (versão 0).
        if not _token_version_matches(db, legacy_user_id, 0):
            return False, 0
        return True, legacy_user_id
    except Exception:
        return False, 0


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> int:
    token = credentials.credentials if credentials else request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    valid, user_id = verify_token(token, db=db)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id
