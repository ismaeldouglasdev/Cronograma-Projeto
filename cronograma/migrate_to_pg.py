"""
Script de migracao de dados do SQLite para PostgreSQL
Execute localmente: python migrate_to_pg.py
"""

import sqlite3
import os
from sqlalchemy import create_engine, text

# Configuracao
SQLITE_PATH = "app/cronograma.db"
PG_URL = "postgresql://cronograma_uszp_user:M6znQJoNAgA3jYWLrlZdV1JEjGGTRmCG@dpg-d6ge2k1drdic73c4et8g-a/cronograma_uszp"


def load_sqlite_data():
    """Carrega dados do SQLite"""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    data = {}

    for table in ["users", "areas", "tasks", "sessoes"]:
        cur.execute(f"SELECT * FROM {table}")
        data[table] = [dict(row) for row in cur.fetchall()]

    conn.close()
    return data


def create_tables(engine):
    """Cria tabelas no PostgreSQL"""
    with engine.connect() as conn:
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
                subcategoria VARCHAR(100)
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
                pomodoros_concluidos INTEGER DEFAULT 0
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
                task_id INTEGER REFERENCES tasks(id)
            )
        """)
        )

        conn.commit()


def migrate():
    """Migra dados para PostgreSQL"""
    print("=== Migracao SQLite -> PostgreSQL ===")

    print("1. Carregando dados do SQLite...")
    data = load_sqlite_data()
    for table, rows in data.items():
        print(f"   {table}: {len(rows)} registros")

    print("\n2. Conectando no PostgreSQL...")
    engine = create_engine(PG_URL)

    print("3. Criando tabelas...")
    create_tables(engine)
    print("   OK")

    print("\n4. Importando usuarios...")
    with engine.connect() as conn:
        for user in data["users"]:
            is_verified = (
                bool(user.get("is_verified")) if user.get("is_verified") else False
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
                    "created_at": user["created_at"],
                    "is_verified": is_verified,
                    "verification_token": user.get("verification_token"),
                },
            )
        conn.commit()
    print(f"   {len(data['users'])} usuarios importados")

    print("5. Importando areas...")
    with engine.connect() as conn:
        for area in data["areas"]:
            conn.execute(
                text("""
                INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria)
                VALUES (:id, :nome, :cor, :ordem, :tipo, :dia_semana, :horario, :sala, :bloco, :professor, :subcategoria)
                ON CONFLICT (id) DO NOTHING
            """),
                area,
            )
        conn.commit()
    print(f"   {len(data['areas'])} areas importadas")

    print("6. Importando tarefas...")
    with engine.connect() as conn:
        for task in data["tasks"]:
            concluida = bool(task.get("concluida")) if task.get("concluida") else False
            conn.execute(
                text("""
                INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos)
                VALUES (:id, :area_id, :titulo, :descricao, :data_entrega, :concluida, :duracao_minutos, :prioridade, :meta_pomodoros, :pomodoros_concluidos)
                ON CONFLICT (id) DO NOTHING
            """),
                {
                    "id": task["id"],
                    "area_id": task["area_id"],
                    "titulo": task["titulo"],
                    "descricao": task.get("descricao"),
                    "data_entrega": task["data_entrega"],
                    "concluida": concluida,
                    "duracao_minutos": task.get("duracao_minutos"),
                    "prioridade": task.get("prioridade"),
                    "meta_pomodoros": task.get("meta_pomodoros"),
                    "pomodoros_concluidos": task.get("pomodoros_concluidos"),
                },
            )
        conn.commit()
    print(f"   {len(data['tasks'])} tarefas importadas")

    print("7. Importando sessoes...")
    with engine.connect() as conn:
        for sessao in data["sessoes"]:
            conn.execute(
                text("""
                INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id)
                VALUES (:id, :area_id, :duracao_minutos, :data, :task_id)
                ON CONFLICT (id) DO NOTHING
            """),
                sessao,
            )
        conn.commit()
    print(f"   {len(data['sessoes'])} sessoes importadas")

    print("\n8. Verificando dados no PostgreSQL...")
    with engine.connect() as conn:
        for table in ["users", "areas", "tasks", "sessoes"]:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f"   {table}: {count} registros")

    print("\nMigracao concluida!")


if __name__ == "__main__":
    migrate()
