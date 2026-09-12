"""Rotas de autenticação: register, login, logout, guest, refresh, verify-email."""

import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    get_db,
    security,
)
from logger import get_logger
from middleware import (
    generate_verification_token,
    hash_password,
    rate_limit,
    sendVerificationEmail,
    validate_email,
    validate_password,
    verify_password,
)
from models.user import User
from models.schemas import (
    TokenResponse,
    UserLogin,
    UserRegister,
    VerifyEmailRequest,
)
from services.auth_service import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_refresh_token,
)

auth_log = get_logger("cronograma.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    is_secure = os.environ.get("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )


# ─── Refresh Token Request ────────────────────────────────────────────────────


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/register", response_model=TokenResponse)
def register(
    response: Response,
    body: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    rate_limit(f"register:{client_ip}", max_req=5, window=60)
    if not validate_email(body.email):
        raise HTTPException(status_code=400, detail="Email inválido")

    senha_valida, msg_erro = validate_password(body.password)
    if not senha_valida:
        raise HTTPException(status_code=400, detail=msg_erro)

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        created_at=datetime.now(timezone.utc).isoformat(),
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)

    auth_log.info(
        "User registered (auto-verified)",
        extra={
            "user_id": user.id,
            "email": user.email,
            "action": "register",
        },
    )

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(
    response: Response,
    body: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate user and return access token + refresh token.

    Sets httpOnly cookies for both tokens for enhanced security.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limit(f"login:{client_ip}", max_req=10, window=60)
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        auth_log.warning(
            "Login failed",
            extra={"email": body.email, "action": "login_failed"},
        )
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not user.password_hash.startswith("$2"):
        user.password_hash = hash_password(body.password)
        db.add(user)
        db.commit()
        auth_log.info(
            "Password hash upgraded to bcrypt",
            extra={"user_id": user.id, "action": "password_hash_upgrade"},
        )

    auth_log.info(
        "Login success",
        extra={"user_id": user.id, "email": user.email, "action": "login"},
    )

    access_token = create_access_token(user.id, is_guest=bool(user.is_guest))
    refresh_token = create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db),
):
    """Valida o refresh token e emite novo par de tokens.

    Aceita o refresh token do cookie httpOnly (preferido) ou do body
    (fallback para clientes de API). Rotaciona também o refresh token.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token and body:
        refresh_token = body.refresh_token

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token não fornecido")

    valid, user_id = verify_refresh_token(refresh_token)
    if not valid:
        auth_log.warning(
            "Invalid refresh token used",
            extra={"action": "refresh_token_invalid"},
        )
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    is_guest = False
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        is_guest = bool(user.is_guest)

    new_access_token = create_access_token(user_id, is_guest=is_guest)
    new_refresh_token = create_refresh_token(user_id)

    is_secure = os.environ.get("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )

    auth_log.info(
        "Access token refreshed",
        extra={"user_id": user_id, "action": "token_refresh"},
    )

    return TokenResponse(access_token=new_access_token)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
):
    """Limpa os cookies de sessão (tokens são stateless)."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Logout realizado com sucesso"}


@router.get("/check")
def check_auth(user_id: int = Depends(get_current_user)):
    return {"user_id": user_id, "authenticated": True}


@router.post("/guest", response_model=TokenResponse)
def guest_login(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    rate_limit(f"guest:{client_ip}", max_req=20, window=60)

    email = f"guest-{uuid.uuid4().hex[:12]}@local.guest"
    guest_password = secrets.token_urlsafe(24)
    user = User(
        email=email,
        password_hash=hash_password(guest_password),
        created_at=datetime.now(timezone.utc).isoformat(),
        is_verified=True,
        is_guest=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id, is_guest=True)
    refresh_token = create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)

    auth_log.info(
        "Guest session created",
        extra={"user_id": user.id, "email": email, "action": "guest_login"},
    )
    return TokenResponse(access_token=access_token)


@router.post("/upgrade", response_model=TokenResponse)
def upgrade_guest(
    response: Response,
    body: UserRegister,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    if not user.is_guest:
        raise HTTPException(status_code=400, detail="Conta não é convidada")

    if not validate_email(body.email):
        raise HTTPException(status_code=400, detail="Email inválido")

    senha_valida, msg_erro = validate_password(body.password)
    if not senha_valida:
        raise HTTPException(status_code=400, detail=msg_erro)

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user.email = body.email
    user.password_hash = hash_password(body.password)
    user.is_guest = False
    user.is_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id, is_guest=False)
    refresh_token = create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)

    auth_log.info(
        "Guest account upgraded to real account",
        extra={"user_id": user.id, "email": user.email, "action": "guest_upgrade"},
    )
    return TokenResponse(access_token=access_token)


@router.get("/verify-email")
def verify_email_get(token: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            return {"success": False, "message": "Token inválido ou expirado"}

        user.is_verified = True
        user.verification_token = None
        db.commit()

        auth_log.info(
            "User verified via link",
            extra={"email": user.email, "action": "verify_email_link"},
        )
        return {"success": True, "message": "Email verificado com sucesso!"}

    except Exception as e:
        auth_log.error(
            "Verify email error",
            extra={"error": str(e), "action": "verify_email"},
        )
        return {"success": False, "message": "Erro ao verificar email"}


@router.post("/verify-email")
def verify_email_post(body: VerifyEmailRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.verification_token == body.token).first()
        if not user:
            return {"success": False, "message": "Token inválido ou expirado"}

        user.is_verified = True  # type: ignore[assignment]
        user.verification_token = None  # type: ignore[assignment]
        db.commit()

        auth_log.info(
            "User verified via manual token",
            extra={"email": user.email, "action": "verify_email_manual"},
        )
        return {"success": True, "message": "Email verificado com sucesso!"}

    except Exception as e:
        auth_log.error(
            "Verify email manual error",
            extra={"error": str(e), "action": "verify_email_manual"},
        )
        return {"success": False, "message": "Erro ao verificar email"}


# ─── Dependências ─────────────────────────────────────────────────────────────

# get_db: from config (imported below)
# get_current_user: from services.auth_service (imported below)
