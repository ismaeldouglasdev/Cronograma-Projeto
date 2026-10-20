"""Testes de headers de segurança: CSP, CORS e headers gerais."""
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from main import app
from middleware import setup_cors


@pytest.mark.asyncio
async def test_security_headers_present():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/")
    # Headers de segurança devem estar presentes
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    csp = r.headers.get("content-security-policy", "")
    assert "script-src" in csp
    assert "script-src 'self'" in csp
    assert "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0]  # script-src sem unsafe-inline
    assert "https://cdn.jsdelivr.net" in csp


@pytest.mark.asyncio
async def test_csp_no_unsafe_inline():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/static/index.html")
    csp = r.headers.get("content-security-policy", "")
    script_src = csp.split("script-src")[1].split(";")[0]
    assert "'unsafe-inline'" not in script_src


def test_cors_headers_restringidos():
    test_app = FastAPI()
    setup_cors(test_app)
    from fastapi.middleware.cors import CORSMiddleware

    cors = next(m for m in test_app.user_middleware if m.cls.__name__ == "CORSMiddleware")
    assert "*" not in cors.kwargs.get("allow_headers", [])
    assert "Authorization" in cors.kwargs["allow_headers"]
    assert "Content-Type" in cors.kwargs["allow_headers"]
    assert cors.kwargs.get("allow_credentials") is True
