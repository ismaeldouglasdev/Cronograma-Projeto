"""Regressões das melhorias de integridade, observabilidade e validação."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from config import Base, SessionLocal, engine
from main import app
from middleware import rate_limiter
from models.achievement import Achievement, UserAchievement


pytestmark = pytest.mark.asyncio


async def _register_and_login(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Test1234!@"},
    )
    assert response.status_code == 200
    fallback_token = response.json().get("fallback_token")
    if fallback_token:
        verified = await client.post(
            "/api/v1/auth/verify-email", json={"token": fallback_token}
        )
        assert verified.status_code == 200
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Test1234!@"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rate_limiter._store.clear()


def teardown_db():
    Base.metadata.drop_all(bind=engine)


async def test_manual_session_preserves_task_link():
    setup_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _register_and_login(client, "manual@example.com")
        area = (
            await client.post("/api/v1/areas", json={"nome": "Matemática"}, headers=headers)
        ).json()
        task = (
            await client.post(
                "/api/v1/tasks",
                json={
                    "area_id": area["id"],
                    "titulo": "Revisar funções",
                    "data_entrega": "2026-12-01",
                },
                headers=headers,
            )
        ).json()
        response = await client.post(
            "/api/v1/sessoes",
            json={
                "area_id": area["id"],
                "duracao_minutos": 25,
                "task_id": task["id"],
            },
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["task_id"] == task["id"]
    teardown_db()


async def test_cross_user_task_references_are_rejected():
    setup_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        owner_headers = await _register_and_login(client, "owner@example.com")
        other_headers = await _register_and_login(client, "other@example.com")
        area = (
            await client.post("/api/v1/areas", json={"nome": "História"}, headers=owner_headers)
        ).json()
        task = (
            await client.post(
                "/api/v1/tasks",
                json={
                    "area_id": area["id"],
                    "titulo": "Estudar república",
                    "data_entrega": "2026-12-01",
                },
                headers=owner_headers,
            )
        ).json()
        other_area = (
            await client.post("/api/v1/areas", json={"nome": "História"}, headers=other_headers)
        ).json()

        manual = await client.post(
            "/api/v1/sessoes",
            json={
                "area_id": other_area["id"],
                "duracao_minutos": 25,
                "task_id": task["id"],
            },
            headers=other_headers,
        )
        assert manual.status_code == 404

        pomodoro = await client.post(
            "/api/v1/pomodoro/completar",
            json={
                "area_id": other_area["id"],
                "duracao_minutos": 25,
                "task_id": task["id"],
            },
            headers=other_headers,
        )
        assert pomodoro.status_code == 404
    teardown_db()


async def test_task_area_mismatch_is_rejected():
    setup_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _register_and_login(client, "mismatch@example.com")
        area_a = (await client.post("/api/v1/areas", json={"nome": "A"}, headers=headers)).json()
        area_b = (await client.post("/api/v1/areas", json={"nome": "B"}, headers=headers)).json()
        task = (
            await client.post(
                "/api/v1/tasks",
                json={
                    "area_id": area_a["id"],
                    "titulo": "Tarefa A",
                    "data_entrega": "2026-12-01",
                },
                headers=headers,
            )
        ).json()
        response = await client.post(
            "/api/v1/sessoes",
            json={
                "area_id": area_b["id"],
                "duracao_minutos": 25,
                "task_id": task["id"],
            },
            headers=headers,
        )
        assert response.status_code == 400
    teardown_db()


async def test_numeric_limits_return_422():
    setup_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _register_and_login(client, "limits@example.com")
        invalid_task = await client.post(
            "/api/v1/tasks",
            json={"titulo": "Prioridade inválida", "data_entrega": "2026-12-01", "prioridade": 4},
            headers=headers,
        )
        assert invalid_task.status_code == 422

        area = (await client.post("/api/v1/areas", json={"nome": "A"}, headers=headers)).json()
        invalid_session = await client.post(
            "/api/v1/sessoes",
            json={"area_id": area["id"], "duracao_minutos": 4},
            headers=headers,
        )
        assert invalid_session.status_code == 422

        invalid_pomodoro = await client.post(
            "/api/v1/pomodoro/completar",
            json={"area_id": area["id"], "duracao_minutos": -1},
            headers=headers,
        )
        assert invalid_pomodoro.status_code == 422
    teardown_db()


async def test_resumo_rejects_invalid_dates_and_reversed_range():
    setup_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _register_and_login(client, "dates@example.com")
        invalid = await client.get(
            "/api/v1/sessoes/resumo?start=not-a-date",
            headers=headers,
        )
        assert invalid.status_code == 422
        reversed_range = await client.get(
            "/api/v1/sessoes/resumo?start=2026-12-02&end=2026-12-01",
            headers=headers,
        )
        assert reversed_range.status_code == 422
    teardown_db()


async def test_task_completion_unlocks_task_achievement():
    setup_db()
    db = SessionLocal()
    db.add(
        Achievement(
            nome="Primeira tarefa",
            descricao="Concluir uma tarefa",
            categoria="tasks",
            requisito=1,
            icone="check",
        )
    )
    db.commit()
    db.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _register_and_login(client, "achievement@example.com")
        task = (
            await client.post(
                "/api/v1/tasks",
                json={"titulo": "Concluir", "data_entrega": "2026-12-01"},
                headers=headers,
            )
        ).json()
        completed = await client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"concluida": True},
            headers=headers,
        )
        assert completed.status_code == 200

    db = SessionLocal()
    try:
        assert db.query(UserAchievement).count() == 1
    finally:
        db.close()
        teardown_db()


async def test_health_split_and_request_id():
    setup_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        live = await client.get("/api/v1/health/live", headers={"X-Request-ID": "req-123"})
        assert live.status_code == 200
        assert live.headers["X-Request-ID"] == "req-123"

        ready = await client.get("/api/v1/health/ready")
        assert ready.status_code == 200
        assert ready.json()["database"] == "healthy"
        assert ready.headers["X-Request-ID"]
    teardown_db()


async def test_delete_errors_are_not_silenced(monkeypatch):
    setup_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _register_and_login(client, "delete@example.com")
        task = (
            await client.post(
                "/api/v1/tasks",
                json={"titulo": "Não apagar em silêncio", "data_entrega": "2026-12-01"},
                headers=headers,
            )
        ).json()

        def fail_delete(self, instance):
            raise RuntimeError("simulated delete failure")

        monkeypatch.setattr(Session, "delete", fail_delete)
        response = await client.delete(f"/api/v1/tasks/{task['id']}", headers=headers)
        assert response.status_code == 500
        assert response.json()["detail"] == "Erro ao excluir tarefa"
    teardown_db()
