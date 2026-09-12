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
from fastapi import Depends, HTTPException
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
        return _bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except (ValueError, TypeError):
        pass

    # Legacy accounts created before bcrypt migration stored SHA-256 hex
    if re.fullmatch(r"[0-9a-f]{64}", hashed_password):
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    auth_log.error(
        "Unsupported password hash format",
        extra={"action": "verify_password_unknown_hash"},
    )
    return False


def generate_verification_token() -> str:
    return str(uuid.uuid4())


def sendVerificationEmail(user, token: str):
    auth_log.info(
        "Verification email",
        extra={
            "action": "send_verification_email",
            "email": user.email,
            "token_preview": token[:8] + "...",
        },
    )
    return True


# ─── JWT ──────────────────────────────────────────────────────────────────────


def create_access_token(user_id: int, is_guest: bool = False) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "guest": is_guest,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_refresh_token(refresh_token: str) -> tuple[bool, int]:
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
        return True, int(sub)
    except (TypeError, ValueError):
        return False, 0


def verify_token(token: str) -> tuple[bool, int]:
    """Verify a JWT access token.

    Handles both new python-jose tokens and legacy tokens
    for backward compatibility during migration.

    Args:
        token: The JWT token to verify

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
        return True, int(user_id)
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
        return True, int(user_id_str)
    except Exception:
        return False, 0


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> int:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    valid, user_id = verify_token(credentials.credentials)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id
