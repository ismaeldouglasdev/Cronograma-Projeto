"""Migrações SQLite→PostgreSQL e repair de sequences."""

import os
import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, text

from logger import get_logger

log = get_logger("cronograma.main")


def column_exists(conn, table: str, column: str) -> bool:
    """Check if column exists in table."""
    try:
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        columns = [row[1] for row in result.fetchall()]
        return column in columns
    except Exception:
        return False


def add_column_if_not_exists(conn, table: str, column: str, definition: str):
    """Add column if it doesn't exist (SQLite compatible)."""
    if not column_exists(conn, table, column):
        try:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
            conn.commit()
            return True
        except Exception as e:
            log.warning(
                "Migration add column failed",
                extra={"column": column, "table": table, "error": str(e)},
            )
            return False
    return False


def repair_postgres_sequences(engine) -> None:
    """Repara sequences PostgreSQL com MAX(id) — idempotente."""
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cronograma.db")
    if "postgres" not in DATABASE_URL:
        return
    try:
        with engine.connect() as conn:
            for table in ["users", "areas", "tasks", "sessoes"]:
                try:
                    conn.execute(
                        text(
                            "SELECT setval(pg_get_serial_sequence(:t, 'id'), "
                            "COALESCE(MAX(id), 1)) FROM "
                            + table
                        ),
                        {"t": table},
                    )
                except Exception as e:
                    log.warning(
                        "Sequence repair failed",
                        extra={"table": table, "error": str(e)},
                    )
            conn.commit()
        log.info("PostgreSQL sequences synchronized")
    except Exception as e:
        log.error("Sequence repair block failed", extra={"error": str(e)})


def run_sqlite_migrations(engine) -> None:
    """Executa migrações SQLite: CREATE TABLE IF NOT EXISTS + ADD COLUMN."""
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cronograma.db")
    if "sqlite" not in DATABASE_URL:
        return

    log.info("Using SQLite database", extra={"database_url": DATABASE_URL[:30]})
    with engine.connect() as conn:
        # Tabela de usuários
        try:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, password_hash VARCHAR(255) NOT NULL, created_at VARCHAR(20), is_verified BOOLEAN DEFAULT 0, verification_token VARCHAR(255))"
                )
            )
            conn.commit()
            log.info("Users table OK")
        except Exception as e:
            log.error("Users table error", extra={"error": str(e)})

        # User columns
        add_column_if_not_exists(conn, "users", "is_verified", "BOOLEAN DEFAULT 0")
        add_column_if_not_exists(conn, "users", "verification_token", "VARCHAR(255)")
        add_column_if_not_exists(conn, "users", "current_streak", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "users", "longest_streak", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "users", "last_activity_date", "VARCHAR(20)")
        add_column_if_not_exists(conn, "users", "streak_freezes", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "users", "last_freeze_grant_date", "VARCHAR(20)")
        add_column_if_not_exists(conn, "users", "coins", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "users", "is_guest", "BOOLEAN DEFAULT 0")
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN duracao_minutos INTEGER"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE sessoes ADD COLUMN task_id INTEGER"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(
                text("ALTER TABLE areas ADD COLUMN tipo VARCHAR(20) DEFAULT 'online'")
            )
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE areas ADD COLUMN dia_semana VARCHAR(20)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE areas ADD COLUMN horario VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE areas ADD COLUMN sala VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE areas ADD COLUMN bloco VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE areas ADD COLUMN professor VARCHAR(255)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE areas ADD COLUMN subcategoria VARCHAR(100)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN prioridade INTEGER"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN meta_pomodoros INTEGER"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(
                text("ALTER TABLE tasks ADD COLUMN pomodoros_concluidos INTEGER DEFAULT 0")
            )
            conn.commit()
        except Exception:
            pass
        # Achievements table
        try:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY, nome VARCHAR(255) NOT NULL, descricao VARCHAR(500) NOT NULL, categoria VARCHAR(50) NOT NULL, requisito INTEGER NOT NULL, icone VARCHAR(50))"
                )
            )
            conn.commit()
        except Exception:
            pass
        # User achievements table
        try:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS user_achievements (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, achievement_id INTEGER NOT NULL, unlocked_at VARCHAR(20))"
                )
            )
            conn.commit()
        except Exception:
            pass
        # Seed achievements
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM achievements"))
            row = result.fetchone()
            count = row[0] if row else 0
            if count == 0:
                achievements_data = [
                    ("Primeiros Passos", "Ganhe 100 XP", "xp", 100, "star"),
                    ("Dedicado", "Ganhe 500 XP", "xp", 500, "star"),
                    ("Estudioso", "Ganhe 1000 XP", "xp", 1000, "star"),
                    ("Mestre do Conhecimento", "Ganhe 5000 XP", "xp", 5000, "star"),
                    ("Lenda da Disciplina", "Ganhe 10000 XP", "xp", 10000, "crown"),
                    ("Inicio da Jornada", "3 dias de sequencia", "streak", 3, "fire"),
                    ("Consistente", "7 dias de sequencia", "streak", 7, "fire"),
                    ("Focado", "14 dias de sequencia", "streak", 14, "fire"),
                    ("Dedicado", "30 dias de sequencia", "streak", 30, "fire"),
                    ("Invencivel", "100 dias de sequencia", "streak", 100, "crown"),
                    ("Primeiro Pomodoro", "Complete 1 pomodoro", "pomodoro", 1, "clock"),
                    ("Aquecendo", "Complete 10 pomodoros", "pomodoro", 10, "clock"),
                    ("Produtivo", "Complete 50 pomodoros", "pomodoro", 50, "clock"),
                    ("Workaholic", "Complete 100 pomodoros", "pomodoro", 100, "clock"),
                    (
                        "Maquina de Estudo",
                        "Complete 500 pomodoros",
                        "pomodoro",
                        500,
                        "trophy",
                    ),
                    ("Primeira Tarefa", "Complete 1 tarefa", "tasks", 1, "check"),
                    ("Comecando", "Complete 10 tarefas", "tasks", 10, "check"),
                    ("Organizado", "Complete 50 tarefas", "tasks", 50, "check"),
                    ("Profissional", "Complete 100 tarefas", "tasks", 100, "check"),
                    ("Mestre das Tarefas", "Complete 500 tarefas", "tasks", 500, "medal"),
                    ("Level 2", "Atinga level 2", "level", 2, "arrow-up"),
                    ("Level 5", "Atinga level 5", "level", 5, "arrow-up"),
                    ("Level 10", "Atinga level 10", "level", 10, "arrow-up"),
                    ("Level 25", "Atinga level 25", "level", 25, "arrow-up"),
                    ("Level 50", "Atinga level 50", "level", 50, "arrow-up"),
                    # Coins achievements
                    ("Primeiras Moedas", "Acumule 10 coins", "coins", 10, "coin"),
                    ("Economizador", "Acumule 50 coins", "coins", 50, "coin"),
                    ("Poupador", "Acumule 100 coins", "coins", 100, "wallet"),
                    ("Investidor", "Acumule 500 coins", "coins", 500, "bank"),
                    ("Milionario", "Acumule 1000 coins", "coins", 1000, "gem"),
                ]
                for nome, desc, cat, req, icone in achievements_data:
                    conn.execute(
                        text(
                            "INSERT INTO achievements (nome, descricao, categoria, requisito, icone) VALUES (:n, :d, :c, :r, :i)"
                        ),
                        {"n": nome, "d": desc, "c": cat, "r": req, "i": icone},
                    )
                conn.commit()
        except Exception:
            pass


def run_postgres_migrations(engine) -> None:
    """Executa migrações PostgreSQL: widens columns + add is_guest."""
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cronograma.db")
    if "postgres" not in DATABASE_URL:
        return

    postgres_column_migrations = (
        ("users", "created_at"),
        ("users", "last_activity_date"),
        ("users", "last_freeze_grant_date"),
        ("user_achievements", "unlocked_at"),
    )
    with engine.begin() as conn:
        for table, column in postgres_column_migrations:
            try:
                conn.execute(
                    text(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR(40)")
                )
            except Exception as e:
                log.warning(
                    "Migration widen column failed",
                    extra={"table": table, "column": column, "error": str(e)},
                )
        try:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_guest BOOLEAN DEFAULT FALSE"
                )
            )
        except Exception as e:
            log.warning(
                "Migration add is_guest failed",
                extra={"error": str(e)},
            )


def run_migrations(engine) -> None:
    """Executa todas as migrações: repairs de sequence + SQLite/PostgreSQL."""
    repair_postgres_sequences(engine)
    run_sqlite_migrations(engine)
    run_postgres_migrations(engine)
