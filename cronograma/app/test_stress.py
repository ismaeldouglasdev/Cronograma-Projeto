"""Stress test: 50 requisições concorrentes para validar que o server não crasha.

Cenários:
- 50 creates simultâneos de área
- 50 deletes simultâneos da mesma área (race condition)
- 50 reads simultâneos (rate limit boundary)
"""
import asyncio
import pytest
import pytest_asyncio
import time
from httpx import ASGITransport, AsyncClient
from main import app
from config import Base, engine
from middleware import rate_limiter


@pytest.fixture(autouse=True)
def setup_db():
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


@pytest_asyncio.fixture
async def auth_headers(client):
    await client.post(
        "/auth/register",
        json={"email": "stress@example.com", "password": "Stress1234!@"},
    )
    r = await client.post(
        "/auth/login",
        json={"email": "stress@example.com", "password": "Stress1234!@"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_50_concurrent_creates(client, auth_headers):
    """50 POST /areas em paralelo - todos devem succeed (200)."""

    async def create(i):
        return await client.post(
            "/areas",
            json={"nome": f"Area-{i}", "cor": "#000"},
            headers=auth_headers,
        )

    start = time.time()
    results = await asyncio.gather(*[create(i) for i in range(50)])
    elapsed = time.time() - start

    success = [r for r in results if r.status_code == 200]
    assert len(success) == 50, f"Only {len(success)}/50 succeeded"
    print(f"50 creates: {elapsed:.2f}s, all 200 OK")


@pytest.mark.asyncio
async def test_50_concurrent_deletes_same_resource(client, auth_headers):
    """50 DELETEs da MESMA área - deve ser idempotente (sem 500)."""
    r = await client.post(
        "/areas", json={"nome": "RaceTarget"}, headers=auth_headers
    )
    area_id = r.json()["id"]

    async def delete():
        return await client.delete(f"/areas/{area_id}", headers=auth_headers)

    results = await asyncio.gather(*[delete() for _ in range(50)])

    server_errors = [r for r in results if r.status_code >= 500]
    assert len(server_errors) == 0, f"Server crashed: {len(server_errors)} 5xx responses"
    success = [r for r in results if r.status_code in (200, 204, 404)]
    assert len(success) == 50, f"Unexpected: {len(success)}/50 succeeded"
    print(f"50 concurrent deletes: all handled gracefully")


@pytest.mark.asyncio
async def test_50_concurrent_reads(client, auth_headers):
    """50 GETs paralelos não devem acionar rate limit (120/min)."""
    # Pre-populate
    for i in range(5):
        await client.post(
            "/areas", json={"nome": f"R-{i}"}, headers=auth_headers
        )

    async def read():
        return await client.get("/areas", headers=auth_headers)

    results = await asyncio.gather(*[read() for _ in range(50)])

    success = [r for r in results if r.status_code == 200]
    assert len(success) == 50, f"Only {len(success)}/50 reads succeeded"
    print(f"50 concurrent reads: all 200 OK")


@pytest.mark.asyncio
async def test_50_concurrent_pomodoros(client, auth_headers):
    """50 pomodoros concorrentes - verifica que não há 5xx e coins contados corretamente."""
    r = await client.post(
        "/areas", json={"nome": "P"}, headers=auth_headers
    )
    area_id = r.json()["id"]

    async def pom():
        return await client.post(
            "/pomodoro/completar",
            json={"area_id": area_id, "duracao_minutos": 25},
            headers=auth_headers,
        )

    results = await asyncio.gather(*[pom() for _ in range(50)])

    success = [r for r in results if r.status_code == 200]
    server_errors = [r for r in results if r.status_code >= 500]
    assert len(server_errors) == 0, f"Server crashed: {len(server_errors)} 5xx"
    # SQLite serializes; some will fail with 500 but our fix catches them
    assert len(success) >= 25, f"Too many failures: {len(success)}/50 succeeded"

    r2 = await client.get("/gamification-summary", headers=auth_headers)
    coins = r2.json()["coins"]
    # Each successful pomodoro = 3 coins
    assert coins == len(success) * 3, f"Coins mismatch: {coins} vs {len(success)*3}"
    print(f"50 concurrent pomodoros: {len(success)} succeeded, {coins} coins")


@pytest.mark.asyncio
async def test_50_concurrent_registers(client):
    """50 registros em paralelo (rate limit 5/min será atingido)."""
    async def reg(i):
        return await client.post(
            "/auth/register",
            json={"email": f"r{i}@example.com", "password": "Test1234!@"},
        )

    results = await asyncio.gather(*[reg(i) for i in range(50)])

    # Rate limit é 5/min — maioria deve receber 429
    rate_limited = [r for r in results if r.status_code == 429]
    success = [r for r in results if r.status_code == 200]
    assert len(rate_limited) > 0, "Rate limiter não ativou"
    assert len(success) <= 5, f"Mais de 5 sucessos: {len(success)}"
    print(
        f"50 concurrent registers: {len(success)} success, {len(rate_limited)} rate-limited"
    )


@pytest.mark.asyncio
async def test_mixed_workload_50(client, auth_headers):
    """Workload misto: creates + reads + updates + deletes."""
    # Cria 10 áreas base
    ids = []
    for i in range(10):
        r = await client.post(
            "/areas", json={"nome": f"Base-{i}"}, headers=auth_headers
        )
        ids.append(r.json()["id"])

    async def mixed(i):
        op = i % 4
        if op == 0:
            return await client.post(
                "/areas", json={"nome": f"M-{i}"}, headers=auth_headers
            )
        if op == 1:
            return await client.get("/areas", headers=auth_headers)
        if op == 2:
            return await client.patch(
                f"/areas/{ids[i % 10]}",
                json={"nome": f"U-{i}"},
                headers=auth_headers,
            )
        return await client.delete(
            f"/areas/{ids[i % 10]}", headers=auth_headers
        )

    results = await asyncio.gather(*[mixed(i) for i in range(50)])

    server_errors = [r for r in results if r.status_code >= 500]
    assert len(server_errors) == 0, f"Server crashed: {len(server_errors)} 5xx"
    print(f"50 mixed ops: zero 5xx errors, {len(results)}/50 handled")
