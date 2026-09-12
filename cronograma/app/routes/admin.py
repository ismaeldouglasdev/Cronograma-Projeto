"""Rotas de admin/debug/logs: /admin/*, /debug/*, /logs/*, /, /app."""

import os
import sqlite3
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import Session

from config import MIGRATION_SECRET, STATIC_DIR, get_db
from logger import get_logger
from models.schemas import ClientLogBatch, ImportData
from models.sessao import Sessoes
from models.task import Tasks
from models.user import User
from services.auth_service import get_current_user
from services.gamification_service import calcular_xp_total

log = get_logger("cronograma.main")
client_log = get_logger("cronograma.client")

router = APIRouter(tags=["admin"])


# ─── Page Endpoints ───────────────────────────────────────────────────────────


@router.get("/")
def landing():
    return FileResponse(
        STATIC_DIR / "landing.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/app")
def app_index():
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


# ─── Admin Migration Endpoints ────────────────────────────────────────────────


@router.post("/admin/init")
def init_database(user_id: int = Depends(get_current_user)):
    """Initialize database tables (requires auth)"""
    if not MIGRATION_SECRET:
        raise HTTPException(status_code=500, detail="MIGRATION_SECRET not configured")

    pg_url = os.environ.get("DATABASE_URL", "")
    if not pg_url or "sqlite" in pg_url:
        raise HTTPException(status_code=500, detail="PostgreSQL not configured")

    try:
        pg_engine = create_engine(pg_url)
        with pg_engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_verified BOOLEAN DEFAULT FALSE,
                    verification_token VARCHAR(255)
                )
            """)
            )
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS areas (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    cor VARCHAR(20),
                    ordem INTEGER,
                    tipo VARCHAR(20) DEFAULT 'online',
                    dia_semana VARCHAR(20),
                    horario VARCHAR(50),
                    sala VARCHAR(50),
                    bloco VARCHAR(50),
                    professor VARCHAR(255),
                    subcategoria VARCHAR(100),
                    user_id INTEGER NOT NULL REFERENCES users(id)
                )
            """)
            )
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    area_id INTEGER REFERENCES areas(id),
                    titulo VARCHAR(255) NOT NULL,
                    descricao VARCHAR(500),
                    data_entrega DATE,
                    concluida BOOLEAN DEFAULT FALSE,
                    duracao_minutos INTEGER,
                    prioridade INTEGER,
                    meta_pomodoros INTEGER,
                    pomodoros_concluidos INTEGER DEFAULT 0,
                    user_id INTEGER DEFAULT 1
                )
            """)
            )
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS sessoes (
                    id SERIAL PRIMARY KEY,
                    area_id INTEGER REFERENCES areas(id),
                    duracao_minutos INTEGER,
                    data DATE,
                    task_id INTEGER REFERENCES tasks(id),
                    user_id INTEGER DEFAULT 1
                )
            """)
            )
            conn.commit()
        return {"status": "ok", "message": "Tables created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/import")
def import_data(
    data: ImportData, secret: str = "", user_id: int = Depends(get_current_user)
):
    """Import data from JSON (for migration from SQLite)"""
    if not MIGRATION_SECRET:
        raise HTTPException(status_code=500, detail="MIGRATION_SECRET not configured")
    if secret != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    pg_url = os.environ.get("DATABASE_URL", "")
    if not pg_url or "sqlite" in pg_url:
        raise HTTPException(status_code=500, detail="PostgreSQL not configured")

    report = {"tables": [], "errors": []}

    try:
        pg_engine = create_engine(pg_url)

        if data.users:
            with pg_engine.connect() as conn:
                for user in data.users:
                    is_ver = (
                        bool(user.get("is_verified"))
                        if user.get("is_verified")
                        else False
                    )
                    conn.execute(
                        text("""
                        INSERT INTO users (id, email, password_hash, created_at, is_verified, verification_token)
                        VALUES (:id, :email, :password_hash, :created_at, :is_verified, :verification_token)
                        ON CONFLICT (id) DO NOTHING
                    """),
                        {
                            "id": user["id"],
                            "email": user["email"],
                            "password_hash": user["password_hash"],
                            "created_at": user.get("created_at"),
                            "is_verified": is_ver,
                            "verification_token": user.get("verification_token"),
                        },
                    )
                conn.commit()
            report["tables"].append(
                {"name": "users", "records": len(data.users), "status": "ok"}
            )

        if data.areas:
            with pg_engine.connect() as conn:
                for area in data.areas:
                    conn.execute(
                        text("""
                        INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria, user_id)
                        VALUES (:id, :nome, :cor, :ordem, :tipo, :dia_semana, :horario, :sala, :bloco, :professor, :subcategoria, :user_id)
                        ON CONFLICT (id) DO NOTHING
                    """),
                        {**area, "user_id": user_id},
                    )
                conn.commit()
            report["tables"].append(
                {"name": "areas", "records": len(data.areas), "status": "ok"}
            )

        if data.tasks:
            with pg_engine.connect() as conn:
                for task in data.tasks:
                    conc = (
                        bool(task.get("concluida")) if task.get("concluida") else False
                    )
                    conn.execute(
                        text("""
                        INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos, user_id)
                        VALUES (:id, :area_id, :titulo, :descricao, :data_entrega, :concluida, :duracao_minutos, :prioridade, :meta_pomodoros, :pomodoros_concluidos, :user_id)
                        ON CONFLICT (id) DO NOTHING
                    """),
                        {
                            "id": task["id"],
                            "area_id": task["area_id"],
                            "titulo": task["titulo"],
                            "descricao": task.get("descricao"),
                            "data_entrega": task["data_entrega"],
                            "concluida": conc,
                            "duracao_minutos": task.get("duracao_minutos"),
                            "prioridade": task.get("prioridade"),
                            "meta_pomodoros": task.get("meta_pomodoros"),
                            "pomodoros_concluidos": task.get("pomodoros_concluidos"),
                            "user_id": user_id,
                        },
                    )
                conn.commit()
            report["tables"].append(
                {"name": "tasks", "records": len(data.tasks), "status": "ok"}
            )

        if data.sessoes:
            with pg_engine.connect() as conn:
                for sessao in data.sessoes:
                    conn.execute(
                        text("""
                        INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id, user_id)
                        VALUES (:id, :area_id, :duracao_minutos, :data, :task_id, :user_id)
                        ON CONFLICT (id) DO NOTHING
                    """),
                        {**sessao, "user_id": user_id},
                    )
                conn.commit()
            report["tables"].append(
                {"name": "sessoes", "records": len(data.sessoes), "status": "ok"}
            )

    except Exception as e:
        report["errors"].append(str(e))

    return report


@router.post("/admin/migrate")
def migrate_data(secret: str = "", user_id: int = Depends(get_current_user)):
    if not MIGRATION_SECRET:
        raise HTTPException(status_code=500, detail="MIGRATION_SECRET not configured")
    if secret != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    report = {"tables": [], "errors": []}

    sqlite_path = Path(__file__).parent.parent / "cronograma.db"
    if not sqlite_path.exists():
        report["errors"].append("SQLite database not found at " + str(sqlite_path))
        return report

    pg_url = os.environ.get("DATABASE_URL", "")
    if not pg_url or "sqlite" in pg_url:
        report["errors"].append("PostgreSQL not configured")
        return report

    try:
        sqlite_conn = sqlite3.connect(str(sqlite_path))
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()

        pg_engine = create_engine(pg_url)
        pg_conn = pg_engine.connect()

        # WHITELIST de tabelas permitidas - NUNCA usar input do usuário diretamente
        ALLOWED_TABLES = {"users", "areas", "tasks", "sessoes"}
        tables = ["users", "areas", "tasks", "sessoes"]

        for table in tables:
            # Validar que table está na whitelist (proteção extra)
            if table not in ALLOWED_TABLES:
                continue
            try:
                sqlite_cur.execute(f"SELECT * FROM {table}")
                rows = sqlite_cur.fetchall()
                if not rows:
                    report["tables"].append(
                        {"name": table, "records": 0, "status": "empty"}
                    )
                    continue

                columns = [desc[0] for desc in sqlite_cur.description]
                count = 0

                for row in rows:
                    data = dict(zip(columns, row))

                    if "is_verified" in data:
                        data["is_verified"] = (
                            bool(data["is_verified"]) if data["is_verified"] else False
                        )
                    if "concluida" in data:
                        data["concluida"] = (
                            bool(data["concluida"]) if data["concluida"] else False
                        )
                    if "created_at" in data and data["created_at"]:
                        data["created_at"] = str(data["created_at"])

                    data_clean = {k: v for k, v in data.items() if v is not None}

                    try:
                        cols = ", ".join(data_clean.keys())
                        placeholders = ", ".join([f":{k}" for k in data_clean.keys()])
                        pg_conn.execute(
                            text(
                                f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
                            ),
                            data_clean,
                        )
                        pg_conn.commit()
                        count += 1
                    except Exception:
                        pass

                report["tables"].append(
                    {"name": table, "records": count, "status": "ok"}
                )
                log.info(
                    "Migration data copied",
                    extra={"table": table, "records": count, "action": "migration"},
                )

            except Exception as e:
                report["errors"].append(f"{table}: {str(e)}")
                report["tables"].append(
                    {"name": table, "records": 0, "status": "error"}
                )

        sqlite_conn.close()
        pg_conn.close()

    except Exception as e:
        report["errors"].append(str(e))

    return report


# ─── Client Logs ──────────────────────────────────────────────────────────────


@router.post("/logs/client")
def receive_client_logs(
    body: ClientLogBatch,
    user_id: int = Depends(get_current_user),
):
    """Recebe lotes de logs do frontend e persiste no arquivo."""
    for entry in body.logs:
        level = entry.get("level", "INFO")
        message = entry.get("message", "")
        context = entry.get("context", {})
        context["client_timestamp"] = entry.get("timestamp")
        context["url"] = entry.get("url")

        extra = {
            "user_id": user_id,
            "client_log": True,
            **context,
        }

        if level == "ERROR":
            client_log.error(f"[CLIENT] {message}", extra=extra)
        elif level == "WARN":
            client_log.warning(f"[CLIENT] {message}", extra=extra)
        elif level == "DEBUG":
            client_log.debug(f"[CLIENT] {message}", extra=extra)
        else:
            client_log.info(f"[CLIENT] {message}", extra=extra)

    return {"received": len(body.logs)}


# ─── Debug Endpoints ──────────────────────────────────────────────────────────


@router.get("/debug/stats")
def debug_stats(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Endpoint de debug para verificar estatísticas brutas do banco."""
    # Contar sessões
    total_sessoes = (
        db.query(func.count(Sessoes.id)).filter(Sessoes.user_id == user_id).scalar()
        or 0
    )

    # Total de minutos
    minutos_total = (
        db.query(func.sum(Sessoes.duracao_minutos))
        .filter(Sessoes.user_id == user_id)
        .scalar()
        or 0
    )

    # Tarefas totais
    total_tarefas = (
        db.query(func.count(Tasks.id)).filter(Tasks.user_id == user_id).scalar() or 0
    )

    # Tarefas concluídas
    tarefas_concluidas = (
        db.query(func.count(Tasks.id))
        .filter(Tasks.user_id == user_id, Tasks.concluida == True)
        .scalar()
        or 0
    )

    # Calcular XP esperado
    xp_sessoes = (minutos_total * 10) // 30
    xp_tarefas = tarefas_concluidas * 5
    xp_total_esperado = xp_sessoes + xp_tarefas

    return {
        "user_id": user_id,
        "total_sessoes": total_sessoes,
        "minutos_total": minutos_total,
        "total_tarefas": total_tarefas,
        "tarefas_concluidas": tarefas_concluidas,
        "xp_por_sessoes": xp_sessoes,
        "xp_por_tarefas": xp_tarefas,
        "xp_total_calculado": xp_total_esperado,
    }


@router.post("/admin/recalculate-xp")
def recalculate_all_xp(
    secret: str = "",
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recalcula XP de todos os usuários (ação administrativa)."""
    if not MIGRATION_SECRET or secret != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Acesso administrativo negado")
    users = db.query(User).all()
    results = []

    for user in users:
        # Calcular minutos totais
        minutos_result = (
            db.query(func.sum(Sessoes.duracao_minutos))
            .filter(Sessoes.user_id == user.id)
            .scalar()
        )
        minutos = int(minutos_result or 0)

        # Calcular tarefas concluídas
        tarefas_result = (
            db.query(func.count(Tasks.id))
            .filter(Tasks.user_id == user.id, Tasks.concluida == True)
            .scalar()
        )
        tarefas = int(tarefas_result or 0)

        # Calcular XP: 10 XP por 30 min + 5 XP por tarefa
        xp_sessoes = (minutos * 10) // 30
        xp_tarefas = tarefas * 5
        xp_total = xp_sessoes + xp_tarefas

        # Calcular level
        level = 1
        xp_temp = xp_total
        while xp_temp >= int(100 * (level**1.5)):
            xp_temp -= int(100 * (level**1.5))
            level += 1

        results.append(
            {
                "user_id": user.id,
                "email": user.email,
                "minutos": minutos,
                "tarefas_concluidas": tarefas,
                "xp_total": xp_total,
                "level": level,
            }
        )

    return {"results": results, "message": "XP recalculado com sucesso"}
