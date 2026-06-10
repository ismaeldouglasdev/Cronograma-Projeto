"""Import data from data_export.json to Supabase PostgreSQL."""
import json
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import declarative_base

SUPABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:7FjE2ouGsNgMO0ky@db.zslcbywlnccgjbaddgnm.supabase.co:5432/postgres"
)

JSON_PATH = Path(__file__).parent / "app" / "data_export.json"

Base = declarative_base()

class UsersModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(String(30), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=True)
    verification_token = Column(String(255), nullable=True)
    current_streak = Column(Integer, default=0, nullable=True)
    longest_streak = Column(Integer, default=0, nullable=True)
    last_activity_date = Column(String(30), nullable=True)
    streak_freezes = Column(Integer, default=0, nullable=True)
    last_freeze_grant_date = Column(String(30), nullable=True)
    coins = Column(Integer, default=0, nullable=True)

class AreasModel(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    cor = Column(String(20), nullable=True)
    ordem = Column(Integer, nullable=True)
    tipo = Column(String(20), default="online", nullable=True)
    dia_semana = Column(String(20), nullable=True)
    horario = Column(String(50), nullable=True)
    sala = Column(String(50), nullable=True)
    bloco = Column(String(50), nullable=True)
    professor = Column(String(255), nullable=True)
    subcategoria = Column(String(100), nullable=True)

class TasksModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(String(500), nullable=True)
    data_entrega = Column(Date, nullable=False)
    concluida = Column(Boolean, default=False, nullable=False)
    duracao_minutos = Column(Integer, nullable=True)
    prioridade = Column(Integer, nullable=True)
    meta_pomodoros = Column(Integer, nullable=True)
    pomodoros_concluidos = Column(Integer, default=0, nullable=True)

class SessoesModel(Base):
    __tablename__ = "sessoes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=False)
    duracao_minutos = Column(Integer, nullable=False)
    data = Column(Date, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

class AchievementModel(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(String(500), nullable=False)
    categoria = Column(String(50), nullable=False)
    requisito = Column(Integer, nullable=False)
    icone = Column(String(50), nullable=True)

class UserAchievementModel(Base):
    __tablename__ = "user_achievements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    unlocked_at = Column(String(30), nullable=True)

def main():
    # Load JSON data
    if not JSON_PATH.exists():
        print(f"[ERROR] JSON file not found: {JSON_PATH}")
        sys.exit(1)

    with open(JSON_PATH) as f:
        data = json.load(f)

    print(f"[IMPORT] Loaded: {len(data.get('users',[]))} users, {len(data.get('areas',[]))} areas, "
          f"{len(data.get('tasks',[]))} tasks, {len(data.get('sessoes',[]))} sessoes")

    # Connect to Supabase
    engine = create_engine(SUPABASE_URL)

    print("[IMPORT] Creating tables...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("[IMPORT] Tables created successfully")

    conn = engine.connect()

    try:
        # Clear existing data (fresh import)
        for table in ["user_achievements", "sessoes", "tasks", "areas", "achievements", "users"]:
            conn.execute(text(f"DELETE FROM {table}"))
        conn.commit()
        print("[IMPORT] Cleared existing data")

        # Seed achievements
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
            ("Maquina de Estudo", "Complete 500 pomodoros", "pomodoro", 500, "trophy"),
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
            ("Primeiras Moedas", "Acumule 10 coins", "coins", 10, "coin"),
            ("Economizador", "Acumule 50 coins", "coins", 50, "coin"),
            ("Poupador", "Acumule 100 coins", "coins", 100, "wallet"),
            ("Investidor", "Acumule 500 coins", "coins", 500, "bank"),
            ("Milionario", "Acumule 1000 coins", "coins", 1000, "gem"),
        ]
        for nome, desc, cat, req, icone in achievements_data:
            conn.execute(
                text("INSERT INTO achievements (nome, descricao, categoria, requisito, icone) "
                      "VALUES (:n, :d, :c, :r, :i)"),
                {"n": nome, "d": desc, "c": cat, "r": req, "i": icone},
            )
        conn.commit()
        print(f"[IMPORT] Seeded {len(achievements_data)} achievements")

        # Import users
        for u in data.get("users", []):
            is_ver = bool(u.get("is_verified")) if u.get("is_verified") is not None else False
            conn.execute(
                text("INSERT INTO users (id, email, password_hash, created_at, is_verified, verification_token) "
                      "VALUES (:id, :email, :password_hash, :created_at, :is_verified, :verification_token)"),
                {
                    "id": u["id"],
                    "email": u["email"],
                    "password_hash": u["password_hash"],
                    "created_at": u.get("created_at"),
                    "is_verified": is_ver,
                    "verification_token": u.get("verification_token"),
                },
            )
        conn.commit()
        print(f"[IMPORT] Imported {len(data.get('users',[]))} users")

        # Import areas
        for a in data.get("areas", []):
            conn.execute(
                text("INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria, user_id) "
                      "VALUES (:id, :nome, :cor, :ordem, :tipo, :dia_semana, :horario, :sala, :bloco, :professor, :subcategoria, :user_id)"),
                {
                    "id": a["id"],
                    "nome": a["nome"],
                    "cor": a.get("cor"),
                    "ordem": a.get("ordem"),
                    "tipo": a.get("tipo", "online"),
                    "dia_semana": a.get("dia_semana"),
                    "horario": a.get("horario"),
                    "sala": a.get("sala"),
                    "bloco": a.get("bloco"),
                    "professor": a.get("professor"),
                    "subcategoria": a.get("subcategoria"),
                    "user_id": a.get("user_id", 1),
                },
            )
        conn.commit()
        print(f"[IMPORT] Imported {len(data.get('areas',[]))} areas")

        # Import tasks
        for t in data.get("tasks", []):
            conc = bool(t.get("concluida")) if t.get("concluida") is not None else False
            conn.execute(
                text("INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, "
                      "duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos, user_id) "
                      "VALUES (:id, :area_id, :titulo, :descricao, :data_entrega, :concluida, "
                      ":duracao_minutos, :prioridade, :meta_pomodoros, :pomodoros_concluidos, :user_id)"),
                {
                    "id": t["id"],
                    "area_id": t.get("area_id"),
                    "titulo": t["titulo"],
                    "descricao": t.get("descricao"),
                    "data_entrega": t["data_entrega"],
                    "concluida": conc,
                    "duracao_minutos": t.get("duracao_minutos"),
                    "prioridade": t.get("prioridade"),
                    "meta_pomodoros": t.get("meta_pomodoros"),
                    "pomodoros_concluidos": t.get("pomodoros_concluidos", 0),
                    "user_id": t.get("user_id", 1),
                },
            )
        conn.commit()
        print(f"[IMPORT] Imported {len(data.get('tasks',[]))} tasks")

        # Import sessoes
        for s in data.get("sessoes", []):
            conn.execute(
                text("INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id, user_id) "
                      "VALUES (:id, :area_id, :duracao_minutos, :data, :task_id, :user_id)"),
                {
                    "id": s["id"],
                    "area_id": s["area_id"],
                    "duracao_minutos": s["duracao_minutos"],
                    "data": s["data"],
                    "task_id": s.get("task_id"),
                    "user_id": s.get("user_id", 1),
                },
            )
        conn.commit()
        print(f"[IMPORT] Imported {len(data.get('sessoes',[]))} sessoes")

        # Verify
        for table in ["users", "areas", "tasks", "sessoes", "achievements"]:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"[IMPORT] Verification: {table} = {count} rows")

        print("\n[IMPORT] ✅ All data imported successfully!")

    except Exception as e:
        conn.rollback()
        print(f"[IMPORT] ❌ Error: {e}")
        raise
    finally:
        conn.close()
        engine.dispose()

if __name__ == "__main__":
    main()
