"""Rotas de autenticação: register, login, logout, guest, refresh, verify-email."""

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
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
    get_client_ip,
    hash_password,
    rate_limit,
    validate_email,
    validate_password,
    verify_password,
)
from models.user import User
from models.password_reset import PasswordResetToken
from models.schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    VerifyEmailRequest,
)
from services import email_service
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


VERIFICATION_TTL_HOURS = 24


def _make_verification_token() -> str:
    expiry = int(
        (datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TTL_HOURS)).timestamp()
    )
    return f"{uuid.uuid4()}.{expiry}"


def _verification_token_expired(token: str) -> bool:
    # Token legado (pré-Resend) era só uuid4 sem ponto, sem expiração —
    # continua aceito para não invalidar nada que já exista.
    if "." not in token:
        return False
    try:
        expiry = int(token.rsplit(".", 1)[1])
    except ValueError:
        return True
    return int(datetime.now(timezone.utc).timestamp()) > expiry


def _verify_page(
    title: str, message: str, ok: bool, resend_token: str = ""
) -> HTMLResponse:
    resend_html = ""
    if resend_token:
        resend_html = (
            '<p><a href="/auth/verify-email/resend?token='
            + escape(resend_token)
            + '">Enviar novo email de verificação</a></p>'
        )
    color = "#22c55e" if ok else "#f87171"
    body = (
        "<!DOCTYPE html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>"
        + escape(title)
        + " — Cronograma</title><style>"
        "body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;"
        "display:flex;justify-content:center;align-items:center;min-height:100vh;"
        "margin:0}.card{background:#1e293b;border-radius:12px;padding:2rem;"
        "max-width:420px;text-align:center}h1{color:"
        + color
        + ";font-size:1.25rem}p{line-height:1.5}a{color:#818cf8}"
        "</style></head><body><div class=\"card\"><h1>"
        + escape(title)
        + "</h1><p>"
        + escape(message)
        + "</p>"
        + resend_html
        + '<p><a href="/app">Ir para o app</a></p></div></body></html>'
    )
    return HTMLResponse(content=body, status_code=200 if ok else 400)


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
    client_ip = get_client_ip(request)

    # Validação local primeiro: é O(1), não toca o banco e não revela nada
    # sobre outras contas. Não consome cota de rate limit de propósito — antes
    # o limite ficava no topo do handler, então cada 400 de senha fraca gastava
    # uma das 5 vagas e o 2o erro que o usuário via já era 429 em vez do
    # motivo real.
    if not validate_email(body.email):
        raise HTTPException(status_code=400, detail="Email inválido")

    senha_valida, msg_erro = validate_password(body.password)
    if not senha_valida:
        raise HTTPException(status_code=400, detail=msg_erro)

    # Limite de spam, generoso: conta só os pedidos que passaram na validação.
    rate_limit(f"register:{client_ip}", max_req=20, window=60)

    # Limite de enumeração, apertado: cada uma destas tentativas consulta o
    # banco e diz se o email existe, então precisa ser bem mais restrito.
    rate_limit(f"register-enum:{client_ip}", max_req=5, window=60)

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado — faça login.")

    # Sem RESEND_API_KEY (dev/teste) mantém o auto-verify legado — os testes
    # existentes e o fluxo local sem Resend configurado dependem dele.
    verification_required = email_service.is_configured()
    token = _make_verification_token() if verification_required else None

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        created_at=datetime.now(timezone.utc).isoformat(),
        is_verified=not verification_required,
        verification_token=token,
        verification_sent_at=(
            datetime.now(timezone.utc).isoformat() if verification_required else None
        ),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if verification_required:
        sent = email_service.send_verification_email(user.email, token)
        # Fallback manual: o token só aparece na resposta quando o envio
        # falhou — se o email chegou, quem o recebeu já tem o link com token.
        fallback_token = token if not sent else None
        if not sent:
            auth_log.warning(
                "Verification email failed; manual token fallback",
                extra={"user_id": user.id, "action": "register_email_failed"},
            )
        auth_log.info(
            "User registered (verification pending)",
            extra={"user_id": user.id, "email": user.email, "action": "register"},
        )
        return TokenResponse(
            access_token="",
            verification_required=True,
            fallback_token=fallback_token,
        )

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
    client_ip = get_client_ip(request)
    rate_limit(f"login:{client_ip}", max_req=10, window=60)
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        auth_log.warning(
            "Login failed",
            extra={"email": body.email, "action": "login_failed"},
        )
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    # Só bloqueia quem tem token pendente: usuário legado sem token (criado
    # com auto-verify ou via OAuth) entra direto. A mensagem precisa conter
    # "não verificada" — static/auth.js usa esse substring para redirecionar
    # para a tela de verificação.
    if not user.is_verified and user.verification_token:
        auth_log.warning(
            "Login blocked: email not verified",
            extra={"user_id": user.id, "action": "login_unverified"},
        )
        raise HTTPException(
            status_code=403,
            detail="Conta não verificada — verifique seu email antes de entrar",
        )

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
    client_ip = get_client_ip(request)
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
            return _verify_page(
                "Link inválido",
                "Este link de verificação não é válido. Verifique se você copiou "
                "o link completo do email.",
                ok=False,
            )
        if _verification_token_expired(token):
            return _verify_page(
                "Link expirado",
                "Este link de verificação expirou. Solicite um novo abaixo.",
                ok=False,
                resend_token=token,
            )

        user.is_verified = True
        user.verification_token = None
        db.commit()

        auth_log.info(
            "User verified via link",
            extra={"user_id": user.id, "action": "verify_email_link"},
        )
        return _verify_page(
            "Email verificado!",
            "Sua conta foi ativada. Já pode fazer login.",
            ok=True,
        )

    except Exception as e:
        auth_log.error(
            "Verify email error",
            extra={"error": str(e), "action": "verify_email"},
        )
        return _verify_page(
            "Erro",
            "Não foi possível verificar o email. Tente novamente.",
            ok=False,
        )


@router.get("/verify-email/resend")
def verify_email_resend(token: str, request: Request, db: Session = Depends(get_db)):
    # Token-gated: só quem tem o token atual pode pedir reenvio, então a
    # resposta não revela se um email existe (anti-enumeração).
    rate_limit(f"verify-resend:{get_client_ip(request)}", max_req=5, window=60)
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        return _verify_page(
            "Link inválido",
            "Token inválido ou já utilizado.",
            ok=False,
        )

    new_token = _make_verification_token()
    user.verification_token = new_token
    user.verification_sent_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    email_service.send_verification_email(user.email, new_token)

    auth_log.info(
        "Verification email resent",
        extra={"user_id": user.id, "action": "verify_email_resend"},
    )
    return _verify_page(
        "Novo email enviado",
        "Confira sua caixa de entrada (e o spam). O link anterior foi invalidado.",
        ok=True,
    )


@router.post("/verify-email")
def verify_email_post(
    body: VerifyEmailRequest, request: Request, db: Session = Depends(get_db)
):
    rate_limit(f"verify:{get_client_ip(request)}", max_req=10, window=60)
    try:
        user = db.query(User).filter(User.verification_token == body.token).first()
        if not user or _verification_token_expired(body.token):
            return {"success": False, "message": "Token inválido ou expirado"}

        user.is_verified = True  # type: ignore[assignment]
        user.verification_token = None  # type: ignore[assignment]
        db.commit()

        auth_log.info(
            "User verified via manual token",
            extra={"user_id": user.id, "action": "verify_email_manual"},
        )
        return {"success": True, "message": "Email verificado com sucesso!"}

    except Exception as e:
        auth_log.error(
            "Verify email manual error",
            extra={"error": str(e), "action": "verify_email_manual"},
        )
        return {"success": False, "message": "Erro ao verificar email"}


# ─── Password Reset ───────────────────────────────────────────────────────────

RESET_TTL_MINUTES = 30

# Mensagem idêntica com email cadastrado ou não — evita enumeração de contas.
FORGOT_GENERIC_MESSAGE = (
    "Se este email estiver cadastrado, você receberá um link de redefinição."
)


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/forgot-password")
def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    client_ip = get_client_ip(request)
    rate_limit(f"forgot:{client_ip}", max_req=5, window=60)

    user = db.query(User).filter(User.email == body.email).first()

    # Token só é criado se o envio de email está configurado; sem envio o
    # link seria inútil e só desperdiçaria linhas no banco.
    if user and email_service.is_configured():
        raw_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        # Um token ativo por usuário: o mais recente invalida os anteriores.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).update(
            {PasswordResetToken.used_at: now.isoformat()},
            synchronize_session=False,
        )
        reset = PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_reset_token(raw_token),
            created_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=RESET_TTL_MINUTES)).isoformat(),
        )
        db.add(reset)
        db.commit()
        background_tasks.add_task(
            email_service.send_password_reset_email, user.email, raw_token
        )
        auth_log.info(
            "Password reset requested",
            extra={"user_id": user.id, "action": "forgot_password"},
        )

    return {"message": FORGOT_GENERIC_MESSAGE}


@router.post("/reset-password")
def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = get_client_ip(request)
    rate_limit(f"reset:{client_ip}", max_req=10, window=60)

    senha_valida, msg_erro = validate_password(body.password)
    if not senha_valida:
        raise HTTPException(status_code=400, detail=msg_erro)

    token_hash = _hash_reset_token(body.token)
    reset = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )
    if not reset or reset.used_at is not None:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    if datetime.fromisoformat(reset.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    user.password_hash = hash_password(body.password)
    # Possuir o token prova que o dono controla o email — desbloqueia contas
    # ainda pendentes de verificação.
    user.is_verified = True
    user.verification_token = None
    reset.used_at = datetime.now(timezone.utc).isoformat()
    db.add(user)
    db.add(reset)
    db.commit()

    auth_log.info(
        "Password reset completed",
        extra={"user_id": user.id, "action": "reset_password"},
    )
    return {"message": "Senha redefinida com sucesso. Faça login."}


# ─── Google OAuth ─────────────────────────────────────────────────────────────

@router.get("/google")
def google_auth(request: Request, response: Response):
    """Initiate Google OAuth (Auth Code + PKCE + state)."""
    from config import GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI, GOOGLE_OAUTH_SCOPES, APP_URL
    from services.auth_service import generate_pkce_pair, generate_state

    code_verifier, code_challenge = generate_pkce_pair()
    state = generate_state()

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_OAUTH_SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "online",
        "prompt": "select_account",
    }
    from urllib.parse import urlencode

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

    from fastapi.responses import RedirectResponse

    # IMPORTANTE: os cookies precisam ser setados no MESMO objeto retornado.
    # Setá-los no `response` injetado é silenciosamente descartado quando
    # retornamos um RedirectResponse (comportamento do FastAPI), o que fazia o
    # callback falhar sempre com `oauth_invalid_state`.
    is_secure = os.environ.get("ENVIRONMENT", "development") == "production"
    resp = RedirectResponse(url=auth_url)
    resp.set_cookie(
        key="google_oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )
    resp.set_cookie(
        key="google_oauth_verifier",
        value=code_verifier,
        max_age=600,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )
    return resp


@router.get("/google/callback")
def google_callback(
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Handle Google OAuth callback. Exchanges code, creates/links user, sets session."""
    from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, APP_URL
    from fastapi.responses import RedirectResponse
    from datetime import datetime, timezone

    try:
        if not code or not state:
            return RedirectResponse(url=f"{APP_URL}/app?error=oauth_missing_params")

    stored_state = request.cookies.get("google_oauth_state")
    stored_verifier = request.cookies.get("google_oauth_verifier")

    if not stored_state or not stored_verifier or stored_state != state:
        return RedirectResponse(url=f"{APP_URL}/app?error=oauth_invalid_state")

    # Exchange code
    try:
        import httpx

        token_resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "code_verifier": stored_verifier,
            },
            timeout=10.0,
        )
    except Exception as e:
        auth_log.error("Google token exchange error", extra={"error": str(e)})
        return RedirectResponse(url=f"{APP_URL}/app?error=oauth_token_exchange_failed")

    if token_resp.status_code != 200:
        auth_log.error(
            "Google token exchange failed", extra={"status": token_resp.status_code}
        )
        return RedirectResponse(url=f"{APP_URL}/app?error=oauth_token_exchange_failed")

    token_data = token_resp.json()
    access_token_google = token_data.get("access_token")

    # Get userinfo
    try:
        import httpx

        userinfo_resp = httpx.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token_google}"},
            timeout=10.0,
        )
    except Exception as e:
        auth_log.error("Google userinfo error", extra={"error": str(e)})
        return RedirectResponse(url=f"{APP_URL}/app?error=oauth_userinfo_failed")

    if userinfo_resp.status_code != 200:
        return RedirectResponse(url=f"{APP_URL}/app?error=oauth_userinfo_failed")

    info = userinfo_resp.json()
    email = info.get("email")
    if not email:
        return RedirectResponse(url=f"{APP_URL}/app?error=oauth_missing_email")

    google_sub = info.get("sub")
    google_name = info.get("name") or ""
    google_picture = info.get("picture") or ""
    email_verified = bool(info.get("email_verified", False))

    # Find or create user
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new OAuth user
        user = User(
            email=email,
            password_hash=None,
            created_at=datetime.now(timezone.utc).isoformat(),
            is_verified=email_verified or True,
            verification_token=None,
            is_guest=False,
            auth_provider="google",
            google_provider_id=google_sub,
            email_verified_at=datetime.now(timezone.utc).isoformat()
            if email_verified
            else None,
            display_name=google_name or email.split("@")[0],
            name=google_name or email.split("@")[0],
            avatar_url=google_picture or None,
            avatar_type="google" if google_picture else None,
            avatar_source="google" if google_picture else None,
            profile_completed=False,
            has_seen_tutorial=False,
            onboarded_at=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        auth_log.info(
            "User created via Google OAuth",
            extra={"user_id": user.id, "email": user.email, "action": "google_signup"},
        )
    else:
        # Account linking or login
        updated = False
        if not user.auth_provider or user.auth_provider == "password":
            user.auth_provider = "both"
            updated = True
        elif user.auth_provider == "google":
            user.auth_provider = "google"
        if not user.google_provider_id:
            user.google_provider_id = google_sub
            updated = True
        if email_verified and not user.email_verified_at:
            user.email_verified_at = datetime.now(timezone.utc).isoformat()
            updated = True
        if not user.avatar_url and google_picture:
            user.avatar_url = google_picture
            user.avatar_type = "google"
            user.avatar_source = "google"
            updated = True
        if not user.name and google_name:
            user.name = google_name
            user.display_name = google_name
            updated = True
        if not user.is_verified and email_verified:
            user.is_verified = True
            updated = True
        if updated:
            db.commit()
            db.refresh(user)
        auth_log.info(
            "User logged in via Google OAuth",
            extra={"user_id": user.id, "email": user.email, "action": "google_login"},
        )

    # Issue tokens
    from services.auth_service import create_access_token, create_refresh_token

    access_token = create_access_token(user.id, is_guest=bool(user.is_guest))
    refresh_token = create_refresh_token(user.id)

    # IMPORTANTE: os cookies (tanto o delete dos cookies OAuth temporários quanto
    # o set de access/refresh) precisam ficar no MESMO objeto retornado; setá-los
    # no `response` injetado é descartado ao retornar um RedirectResponse.
    redirect_url = f"{APP_URL}/app"
    is_secure = os.environ.get("ENVIRONMENT", "development") == "production"
    resp = RedirectResponse(url=redirect_url)
    resp.delete_cookie("google_oauth_state", httponly=True, secure=is_secure, samesite="lax")
    resp.delete_cookie("google_oauth_verifier", httponly=True, secure=is_secure, samesite="lax")
    _set_auth_cookies(resp, access_token, refresh_token)
    return resp
    except Exception as e:
        auth_log.error(
            "Google OAuth callback unhandled error",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        return RedirectResponse(url=f"{APP_URL}/app?error=oauth_internal_error")


# ─── Dependências ─────────────────────────────────────────────────────────────

# get_db: from config (imported below)
# get_current_user: from services.auth_service (imported below)

@router.get("/me")
def get_me(current_user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "avatar_type": user.avatar_type,
        "avatar_source": user.avatar_source,
        # NULL (contas antigas, anteriores ao campo) => None, para NÃO forçar
        # onboarding. Contas novas (ex.: via Google) gravam False explicitamente.
        "profile_completed": bool(user.profile_completed) if user.profile_completed is not None else None,
        "has_seen_tutorial": bool(user.has_seen_tutorial) if user.has_seen_tutorial is not None else None,
        "auth_provider": user.auth_provider or "password",
        "is_guest": bool(user.is_guest) if user.is_guest is not None else False,
    }

@router.patch("/profile")
def update_profile(
    data: dict,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    name = data.get("name") or data.get("display_name")
    if name is not None:
        user.name = name
        user.display_name = name
    if data.get("avatar_url") is not None:
        user.avatar_url = data.get("avatar_url")
    if data.get("avatar_source") is not None:
        user.avatar_source = data.get("avatar_source")
    if data.get("avatar_type") is not None:
        user.avatar_type = data.get("avatar_type")
    if data.get("has_seen_tutorial") is not None:
        user.has_seen_tutorial = bool(data.get("has_seen_tutorial"))
    # Mark profile completed if not explicitly false? Keep existing behavior: setting profile fields implies completion
    user.profile_completed = True
    from datetime import datetime, timezone

    if not user.onboarded_at:
        user.onboarded_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "name": user.name,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "avatar_source": user.avatar_source,
        "avatar_type": user.avatar_type,
        "profile_completed": bool(user.profile_completed),
        "has_seen_tutorial": bool(getattr(user, "has_seen_tutorial", False)),
    }
