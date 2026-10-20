"""Envio de e-mails transacionais via Resend (API REST, sem SDK).

Lê RESEND_API_KEY/EMAIL_FROM do ambiente a cada chamada (não no import)
para permitir testes com monkeypatch sem reimportar o módulo. Sem a chave,
is_configured() devolve False e o register cai no auto-verify legado —
comportamento de dev/teste preservado até o Resend ser configurado no
Render.
"""

import os

import httpx

from config import APP_URL
from logger import get_logger

email_log = get_logger("cronograma.email")

RESEND_API_URL = "https://api.resend.com/emails"
DEFAULT_FROM = "Cronograma <onboarding@resend.dev>"


def is_configured() -> bool:
    return bool(os.environ.get("RESEND_API_KEY"))


def _send(to: str, subject: str, html: str, text: str) -> bool:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        email_log.warning(
            "Email skipped: RESEND_API_KEY ausente",
            extra={"action": "email_not_configured"},
        )
        return False

    try:
        resp = httpx.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": os.environ.get("EMAIL_FROM", DEFAULT_FROM),
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
            },
            timeout=10.0,
        )
    except Exception as e:
        email_log.error(
            "Resend request failed",
            extra={"action": "email_send_error", "error": str(e)},
        )
        return False

    if resp.status_code != 200:
        # Nunca logar o token de verificação — só o status/erro da API.
        email_log.error(
            "Resend rejected email",
            extra={
                "action": "email_send_rejected",
                "status_code": resp.status_code,
            },
        )
        return False

    return True


def send_verification_email(to: str, token: str) -> bool:
    link = f"{APP_URL}/auth/verify-email?token={token}"
    html = (
        "<div style='font-family:sans-serif;max-width:480px;margin:0 auto;'>"
        "<h2>Confirme seu e-mail</h2>"
        "<p>Olá! Criei sua conta no Cronograma de Estudos. "
        "Para ativar, confirme este e-mail clicando no botão abaixo:</p>"
        f"<p style='text-align:center;margin:28px 0;'>"
        f"<a href='{link}' style='background:#4f46e5;color:#fff;"
        "padding:12px 24px;border-radius:8px;text-decoration:none;"
        "font-weight:bold;'>Confirmar e-mail</a></p>"
        "<p>O link expira em 24 horas. Se você não criou esta conta, "
        "ignore esta mensagem.</p></div>"
    )
    text_body = f"Confirme seu e-mail acessando: {link}"
    ok = _send(to, "Confirme seu e-mail — Cronograma", html, text_body)
    if ok:
        # Só o preview do token (8 chars) — o token cru jamais entra em log.
        email_log.info(
            "Verification email sent",
            extra={"action": "email_verification_sent", "token_preview": token[:8] + "..."},
        )
    return ok


def send_password_reset_email(to: str, token: str) -> bool:
    link = f"{APP_URL}/app?reset_token={token}"
    html = (
        "<div style='font-family:sans-serif;max-width:480px;margin:0 auto;'>"
        "<h2>Redefinição de senha</h2>"
        "<p>Recebemos um pedido para redefinir a senha da sua conta. "
        "Clique no botão abaixo para escolher uma nova senha:</p>"
        f"<p style='text-align:center;margin:28px 0;'>"
        f"<a href='{link}' style='background:#4f46e5;color:#fff;"
        "padding:12px 24px;border-radius:8px;text-decoration:none;"
        "font-weight:bold;'>Redefinir senha</a></p>"
        "<p>O link expira em 30 minutos e só pode ser usado uma vez. "
        "Se você não pediu esta redefinição, ignore esta mensagem.</p></div>"
    )
    text_body = f"Redefina sua senha acessando: {link}"
    ok = _send(to, "Redefinição de senha — Cronograma", html, text_body)
    if ok:
        email_log.info(
            "Password reset email sent",
            extra={"action": "email_reset_sent", "token_preview": token[:8] + "..."},
        )
    return ok
