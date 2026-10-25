"""Revogação de JWT: reset de senha, logout global e tokens legados."""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from config import ALGORITHM, SECRET_KEY, Base, SessionLocal, engine
from main import app
from middleware import rate_limiter
from models.user import User
from services import email_service

PASSWORD = "Test1234!@"
NEW_PASSWORD = "NovaSenha1!"
EMAIL = "revoke@example.com"


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


def _db_user(email: str) -> User:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


async def _register_and_login(client, email: str = EMAIL) -> str:
    await client.post(
        "/auth/register", json={"email": email, "password": PASSWORD}
    )
    r = await client.post(
        "/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert r.status_code == 200
    return r.json()["access_token"]


async def _reset_password(client, monkeypatch, email: str = EMAIL) -> None:
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    sent = []
    monkeypatch.setattr(
        email_service,
        "send_password_reset_email",
        lambda to, token: sent.append(token) or True,
    )
    r = await client.post("/auth/forgot-password", json={"email": email})
    assert r.status_code == 200 and len(sent) == 1

    r = await client.post(
        "/auth/reset-password", json={"token": sent[0], "password": NEW_PASSWORD}
    )
    assert r.status_code == 200


async def _check(client, access_token: str) -> int:
    r = await client.get(
        "/auth/check", headers={"Authorization": f"Bearer {access_token}"}
    )
    return r.status_code


@pytest.mark.asyncio
async def test_reset_password_revokes_old_access_token(client, monkeypatch):
    old_token = await _register_and_login(client)
    assert await _check(client, old_token) == 200

    await _reset_password(client, monkeypatch)

    assert await _check(client, old_token) == 401
    assert await _check(client, "token-invalido") == 401

    r = await client.post(
        "/auth/login", json={"email": EMAIL, "password": NEW_PASSWORD}
    )
    assert r.status_code == 200
    assert await _check(client, r.json()["access_token"]) == 200


@pytest.mark.asyncio
async def test_reset_password_revokes_old_refresh_token(client, monkeypatch):
    await _register_and_login(client)
    old_refresh = client.cookies.get("refresh_token")
    assert old_refresh

    await _reset_password(client, monkeypatch)

    r = await client.post(
        "/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_logout_all_revokes_current_and_refresh_tokens(client):
    token = await _register_and_login(client)
    old_refresh = client.cookies.get("refresh_token")

    r = await client.post(
        "/auth/logout-all", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200

    assert await _check(client, token) == 401

    r = await client.post(
        "/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_token_without_ver_claim_still_valid_at_version_zero(client):
    await _register_and_login(client)
    user = _db_user(EMAIL)
    assert user.token_version in (None, 0)

    now = datetime.now(timezone.utc)
    legacy_payload = {
        "sub": str(user.id),
        "exp": now + timedelta(minutes=15),
        "iat": now,
        "type": "access",
    }
    legacy_token = jwt.encode(legacy_payload, SECRET_KEY, algorithm=ALGORITHM)

    assert await _check(client, legacy_token) == 200

    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user.id).update({User.token_version: 1})
        db.commit()
    finally:
        db.close()

    assert await _check(client, legacy_token) == 401


@pytest.mark.asyncio
async def test_token_for_deleted_user_is_rejected(client):
    token = await _register_and_login(client)

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == EMAIL).delete()
        db.commit()
    finally:
        db.close()

    assert await _check(client, token) == 401
