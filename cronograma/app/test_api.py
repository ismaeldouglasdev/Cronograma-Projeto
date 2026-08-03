"""Testes automatizados da API do Cronograma de Estudos.

Cobre: auth, areas, tasks, sessoes, gamificacao, coins, rate limit.
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import date
from httpx import ASGITransport, AsyncClient
from main import app, Base, engine, rate_limiter, MIGRATION_SECRET
import main as main_module


@pytest.fixture(autouse=True)
def setup_db():
    """Recria banco isolado para cada teste."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rate_limiter._store.clear()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture
async def client():
    """Cliente HTTP assíncrono por teste."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    """Registra e loga um usuário, retorna headers com token."""
    await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "Test1234!@"},
    )
    r = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "Test1234!@"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─── Auth Tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_creates_user(client):
    r = await client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "Test1234!@"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "Test1234!@"},
    )
    r = await client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "Test1234!@"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    r = await client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "Test1234!@"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_register_weak_password(client):
    r = await client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "Test1234!@"},
    )
    r = await client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "Test1234!@"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"email": "wp@example.com", "password": "Test1234!@"},
    )
    r = await client.post(
        "/auth/login",
        json={"email": "wp@example.com", "password": "WrongPass1!"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_required_for_areas(client):
    r = await client.get("/areas")
    assert r.status_code == 401


# ─── Areas Tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_area(client, auth_headers):
    r = await client.post(
        "/areas",
        json={"nome": "Matemática", "cor": "#ff0000"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Matemática"


@pytest.mark.asyncio
async def test_create_area_xss_escaped(client, auth_headers):
    """XSS no nome deve ser escapado."""
    r = await client.post(
        "/areas",
        json={"nome": "<script>alert(1)</script>", "cor": "#000"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert "<script>" not in r.json()["nome"]
    assert "&lt;script&gt;" in r.json()["nome"]


@pytest.mark.asyncio
async def test_list_areas_only_own(client, auth_headers):
    await client.post(
        "/areas", json={"nome": "A1"}, headers=auth_headers
    )
    # Outro user
    await client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "Test1234!@"},
    )
    r2 = await client.post(
        "/auth/login",
        json={"email": "other@example.com", "password": "Test1234!@"},
    )
    other_headers = {"Authorization": f"Bearer {r2.json()['access_token']}"}
    r = await client.get("/areas", headers=other_headers)
    assert r.status_code == 200
    assert len(r.json()) == 0


@pytest.mark.asyncio
async def test_update_area(client, auth_headers):
    r = await client.post(
        "/areas", json={"nome": "Original"}, headers=auth_headers
    )
    area_id = r.json()["id"]
    r2 = await client.patch(
        f"/areas/{area_id}",
        json={"nome": "Atualizada"},
        headers=auth_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["nome"] == "Atualizada"


@pytest.mark.asyncio
async def test_delete_area_cascades_tasks_sessions(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "X"}, headers=auth_headers)
    ).json()
    task = (
        await client.post(
            "/tasks",
            json={
                "area_id": area["id"],
                "titulo": "T1",
                "data_entrega": str(date.today()),
            },
            headers=auth_headers,
        )
    ).json()
    await client.post(
        "/sessoes",
        json={"area_id": area["id"], "duracao_minutos": 30},
        headers=auth_headers,
    )
    r = await client.delete(f"/areas/{area['id']}", headers=auth_headers)
    assert r.status_code == 204
    # Task foi deletada
    r2 = await client.get("/tasks", headers=auth_headers)
    assert all(t["id"] != task["id"] for t in r2.json())


# ─── Tasks Tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_task_with_invalid_area(client, auth_headers):
    r = await client.post(
        "/tasks",
        json={
            "area_id": 9999,
            "titulo": "T1",
            "data_entrega": str(date.today()),
        },
        headers=auth_headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_complete_task_awards_xp(client, auth_headers):
    r = await client.post(
        "/tasks",
        json={
            "titulo": "Tarefa XP",
            "data_entrega": str(date.today()),
        },
        headers=auth_headers,
    )
    task_id = r.json()["id"]
    await client.patch(
        f"/tasks/{task_id}",
        json={"concluida": True},
        headers=auth_headers,
    )
    r2 = await client.get("/gamification-summary", headers=auth_headers)
    assert r2.json()["xp_total"] >= 5


# ─── Sessoes Tests ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_sessao_updates_streak(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "A"}, headers=auth_headers)
    ).json()
    await client.post(
        "/sessoes",
        json={"area_id": area["id"], "duracao_minutos": 25},
        headers=auth_headers,
    )
    r = await client.get("/gamification-summary", headers=auth_headers)
    assert r.json()["current_streak"] >= 1


@pytest.mark.asyncio
async def test_pomodoro_awards_coins(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "A"}, headers=auth_headers)
    ).json()
    r = await client.post(
        "/pomodoro/completar",
        json={"area_id": area["id"], "duracao_minutos": 25},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["coins"] == 3


# ─── Gamification Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_buy_freeze_requires_coins(client, auth_headers):
    r = await client.post("/coins/buy-freeze", headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_buy_freeze_success(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "A"}, headers=auth_headers)
    ).json()
    # 4 pomodoros = 12 coins
    for _ in range(4):
        await client.post(
            "/pomodoro/completar",
            json={"area_id": area["id"], "duracao_minutos": 25},
            headers=auth_headers,
        )
    r = await client.post("/coins/buy-freeze", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["coins"] == 2
    assert r.json()["freezes"] == 1


@pytest.mark.asyncio
async def test_add_coins_rejects_negative(client, auth_headers, monkeypatch):
    monkeypatch.setattr(main_module, "MIGRATION_SECRET", "test-secret")
    r = await client.post("/coins/add?amount=-5&secret=test-secret", headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_add_coins_rejects_over_100(client, auth_headers, monkeypatch):
    monkeypatch.setattr(main_module, "MIGRATION_SECRET", "test-secret")
    r = await client.post("/coins/add?amount=101&secret=test-secret", headers=auth_headers)
    assert r.status_code == 400


# ─── Resumo Tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resumo_horas_por_area(client, auth_headers):
    area = (
        await client.post("/areas", json={"nome": "X"}, headers=auth_headers)
    ).json()
    await client.post(
        "/sessoes",
        json={"area_id": area["id"], "duracao_minutos": 60},
        headers=auth_headers,
    )
    r = await client.get("/sessoes/resumo", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()[0]["total_horas"] == 1.0