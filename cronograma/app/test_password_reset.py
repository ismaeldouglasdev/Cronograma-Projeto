"""Testes da redefinição de senha - esqueci minha senha (Fase 2b).

Cobre: resposta anti-enumeração idêntica, armazenamento só com hash,
fluxo completo de redefinição, reutilização/expiração de token,
rate limit e desbloqueio de conta não verificada.
"""
import hashlib

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from config import Base, SessionLocal, engine
from main import app
from middleware import rate_limiter
from models.password_reset import PasswordResetToken
from models.user import User
from services import email_service

PASSWORD = "Test1234!@"
NEW_PASSWORD = "NovaSenha1!"


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rate_limiter._store.clear()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def resend_on(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")


@pytest.fixture
def capture_sent(monkeypatch):
    sent = []

    def fake_send(email, token):
        sent.append({"email": email, "token": token})
        return True

    monkeypatch.setattr(email_service, "send_password_reset_email", fake_send)
    return sent


def _get_user(email: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


async def _register(client, email="reset@example.com", password=PASSWORD):
    return await client.post(
        "/auth/register", json={"email": email, "password": password}
    )


async def _forgot(client, email="reset@example.com"):
    return await client.post("/auth/forgot-password", json={"email": email})


# ─── Anti-enumeração e armazenamento ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_forgot_resposta_identica_para_email_desconhecido(
    client, resend_on, capture_sent
):
    await _register(client)
    r_known = await _forgot(client)
    r_unknown = await _forgot(client, email="naoexiste@example.com")
    assert r_known.status_code == 200
    assert r_unknown.status_code == 200
    assert r_known.json() == r_unknown.json()


@pytest.mark.asyncio
async def test_forgot_armazena_apenas_hash_do_token(client, resend_on, capture_sent):
    await _register(client)
    await _forgot(client)
    assert len(capture_sent) == 1
    raw = capture_sent[0]["token"]

    db = SessionLocal()
    try:
        rows = db.query(PasswordResetToken).all()
        assert len(rows) == 1
        assert rows[0].token_hash == hashlib.sha256(raw.encode()).hexdigest()
        assert raw not in rows[0].token_hash
        assert len(rows[0].token_hash) == 64
    finally:
        db.close()


@pytest.mark.asyncio
async def test_forgot_sem_chave_nao_cria_token(client):
    await _register(client)
    r = await _forgot(client)
    assert r.status_code == 200

    db = SessionLocal()
    try:
        assert db.query(PasswordResetToken).count() == 0
    finally:
        db.close()


# ─── Fluxo completo ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fluxo_completo_redefinicao(client, resend_on, capture_sent):
    await _register(client, password=PASSWORD)
    await _forgot(client)
    token = capture_sent[0]["token"]

    r = await client.post(
        "/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}
    )
    assert r.status_code == 200

    r_old = await client.post(
        "/auth/login", json={"email": "reset@example.com", "password": PASSWORD}
    )
    assert r_old.status_code == 401

    r_new = await client.post(
        "/auth/login", json={"email": "reset@example.com", "password": NEW_PASSWORD}
    )
    assert r_new.status_code == 200
    assert r_new.json().get("access_token")


@pytest.mark.asyncio
async def test_reset_token_nao_reutilizavel(client, resend_on, capture_sent):
    await _register(client)
    await _forgot(client)
    token = capture_sent[0]["token"]

    r1 = await client.post(
        "/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}
    )
    assert r1.status_code == 200

    r2 = await client.post(
        "/auth/reset-password", json={"token": token, "password": "OutraSenha1!"}
    )
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_segundo_forgot_invalida_token_anterior(client, resend_on, capture_sent):
    await _register(client)
    await _forgot(client)
    first = capture_sent[0]["token"]
    await _forgot(client)
    second = capture_sent[1]["token"]

    r_old = await client.post(
        "/auth/reset-password", json={"token": first, "password": NEW_PASSWORD}
    )
    assert r_old.status_code == 400

    r_new = await client.post(
        "/auth/reset-password", json={"token": second, "password": NEW_PASSWORD}
    )
    assert r_new.status_code == 200


@pytest.mark.asyncio
async def test_reset_token_expirado_rejeitado(client, resend_on, capture_sent):
    await _register(client)
    await _forgot(client)
    token = capture_sent[0]["token"]

    db = SessionLocal()
    try:
        db.query(PasswordResetToken).update(
            {PasswordResetToken.expires_at: "2000-01-01T00:00:00+00:00"}
        )
        db.commit()
    finally:
        db.close()

    r = await client.post(
        "/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_reset_token_invalido_rejeitado(client):
    r = await client.post(
        "/auth/reset-password",
        json={"token": "token-inexistente", "password": NEW_PASSWORD},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_reset_senha_fraca_rejeitada(client, resend_on, capture_sent):
    await _register(client)
    await _forgot(client)
    token = capture_sent[0]["token"]

    r = await client.post(
        "/auth/reset-password", json={"token": token, "password": "fraca"}
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_reset_desbloqueia_conta_nao_verificada(client, resend_on, capture_sent):
    r = await _register(client)
    assert r.json().get("verification_required") is True

    await _forgot(client)
    token = capture_sent[0]["token"]

    r = await client.post(
        "/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}
    )
    assert r.status_code == 200

    user = _get_user("reset@example.com")
    assert bool(user.is_verified)
    assert user.verification_token is None


# ─── Rate limit ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_forgot_rate_limit(client):
    for _ in range(5):
        r = await _forgot(client, email="naoexiste@example.com")
        assert r.status_code == 200
    r = await _forgot(client, email="naoexiste@example.com")
    assert r.status_code == 429
