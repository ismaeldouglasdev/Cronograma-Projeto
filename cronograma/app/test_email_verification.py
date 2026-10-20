"""Testes da verificação de e-mail por Resend (Fase 2a).

Cobre: register condicional (auto-verify legado sem chave / pendente com
chave), gate de login, verificação por link GET, token manual POST,
token expirado, reenvio e rate limits.
"""
import time
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from config import Base, SessionLocal, engine
from main import app
from middleware import rate_limiter
from models.user import User
from services import email_service

PASSWORD = "Test1234!@"


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

    monkeypatch.setattr(email_service, "send_verification_email", fake_send)
    return sent


def _get_user(email: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def _set_token(email: str, token: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        user.verification_token = token
        db.commit()
    finally:
        db.close()


async def _register(client, email="verify@example.com"):
    return await client.post(
        "/auth/register", json={"email": email, "password": PASSWORD}
    )


# ─── Register condicional ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_com_chave_cria_nao_verificado(client, resend_on, capture_sent):
    r = await _register(client)
    assert r.status_code == 200
    data = r.json()
    assert data["verification_required"] is True
    assert data["access_token"] == ""
    assert data["fallback_token"] is None

    user = _get_user("verify@example.com")
    assert user.is_verified is False or user.is_verified == 0
    assert "." in user.verification_token
    expiry = int(user.verification_token.rsplit(".", 1)[1])
    assert expiry > time.time()
    assert capture_sent == [
        {"email": "verify@example.com", "token": user.verification_token}
    ]


@pytest.mark.asyncio
async def test_register_sem_chave_auto_verifica(client):
    r = await _register(client)
    data = r.json()
    assert data["verification_required"] is False
    assert data["access_token"]

    user = _get_user("verify@example.com")
    assert user.is_verified is True or user.is_verified == 1


@pytest.mark.asyncio
async def test_fallback_token_quando_envio_falha(client, resend_on, monkeypatch):
    monkeypatch.setattr(
        email_service, "send_verification_email", lambda email, token: False
    )
    r = await _register(client)
    data = r.json()
    assert data["verification_required"] is True
    assert data["fallback_token"]
    assert data["fallback_token"] == _get_user("verify@example.com").verification_token


# ─── Login gate ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_bloqueado_ate_verificar(client, resend_on, capture_sent):
    await _register(client)
    r = await client.post(
        "/auth/login", json={"email": "verify@example.com", "password": PASSWORD}
    )
    assert r.status_code == 403
    assert "não verificada" in r.json()["detail"]


@pytest.mark.asyncio
async def test_login_libera_apos_verificar(client, resend_on, capture_sent):
    await _register(client)
    token = capture_sent[0]["token"]
    r = await client.get("/auth/verify-email", params={"token": token})
    assert r.status_code == 200

    r = await client.post(
        "/auth/login", json={"email": "verify@example.com", "password": PASSWORD}
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


# ─── Verificação por link (GET) ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_link_get_verifica_conta(client, resend_on, capture_sent):
    await _register(client)
    token = capture_sent[0]["token"]
    r = await client.get("/auth/verify-email", params={"token": token})
    assert r.status_code == 200
    assert "verificado" in r.text.lower()
    assert _get_user("verify@example.com").verification_token is None


@pytest.mark.asyncio
async def test_link_get_token_invalido(client, resend_on, capture_sent):
    await _register(client)
    r = await client.get("/auth/verify-email", params={"token": "garbage"})
    assert r.status_code == 400
    assert "inválido" in r.text.lower()


@pytest.mark.asyncio
async def test_link_get_token_expirado_mostra_resend(client, resend_on, capture_sent):
    await _register(client)
    expired = f"{uuid.uuid4()}.{int(time.time()) - 3600}"
    _set_token("verify@example.com", expired)

    r = await client.get("/auth/verify-email", params={"token": expired})
    assert r.status_code == 400
    assert "expirado" in r.text.lower()
    assert "/auth/verify-email/resend?token=" in r.text


@pytest.mark.asyncio
async def test_token_legado_sem_ponto_nao_expira(client, resend_on, capture_sent):
    await _register(client)
    legacy = str(uuid.uuid4())
    _set_token("verify@example.com", legacy)
    r = await client.get("/auth/verify-email", params={"token": legacy})
    assert r.status_code == 200


# ─── Token manual (POST) ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_manual_verifica(client, resend_on, capture_sent):
    await _register(client)
    r = await client.post(
        "/auth/verify-email", json={"token": capture_sent[0]["token"]}
    )
    assert r.status_code == 200
    assert r.json()["success"] is True


@pytest.mark.asyncio
async def test_post_manual_token_expirado_rejeitado(client, resend_on, capture_sent):
    await _register(client)
    expired = f"{uuid.uuid4()}.{int(time.time()) - 3600}"
    _set_token("verify@example.com", expired)
    r = await client.post("/auth/verify-email", json={"token": expired})
    assert r.json()["success"] is False


@pytest.mark.asyncio
async def test_post_manual_rate_limit(client, resend_on, capture_sent):
    await _register(client)
    for _ in range(10):
        r = await client.post("/auth/verify-email", json={"token": "x"})
        assert r.status_code == 200
    r = await client.post("/auth/verify-email", json={"token": "x"})
    assert r.status_code == 429


# ─── Reenvio ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resend_regenera_token(client, resend_on, capture_sent):
    await _register(client)
    old_token = capture_sent[0]["token"]

    r = await client.get("/auth/verify-email/resend", params={"token": old_token})
    assert r.status_code == 200
    assert len(capture_sent) == 2
    new_token = capture_sent[1]["token"]
    assert new_token != old_token

    r = await client.get("/auth/verify-email", params={"token": old_token})
    assert r.status_code == 400

    r = await client.get("/auth/verify-email", params={"token": new_token})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_resend_rate_limit(client, resend_on, capture_sent):
    await _register(client)
    token = capture_sent[0]["token"]
    for _ in range(5):
        r = await client.get("/auth/verify-email/resend", params={"token": token})
        assert r.status_code == 200
        token = capture_sent[-1]["token"]
    r = await client.get("/auth/verify-email/resend", params={"token": token})
    assert r.status_code == 429
