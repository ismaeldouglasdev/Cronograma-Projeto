from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, List
import os
import re

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    ForeignKey,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker
import hashlib
import secrets
import uuid
import base64
import time
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cronograma.db")

engine_kwargs = (
    {"connect_args": {"check_same_thread": False}}
    if "sqlite" in DATABASE_URL
    else {"pool_pre_ping": True}
)
engine = create_engine(DATABASE_URL, **engine_kwargs)

Base = declarative_base()

security = HTTPBearer(auto_error=False)


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    if not re.search(r"[a-zA-Z]", password):
        return False, "Senha deve conter pelo menos uma letra"
    if not re.search(r"[0-9]", password):
        return False, "Senha deve conter pelo menos um número"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Senha deve conter pelo menos um caractere especial"
    return True, ""


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


def generate_verification_token() -> str:
    return str(uuid.uuid4())


def sendVerificationEmail(user, token: str):
    print(f"[DEBUG AUTH] ============================================")
    print(f"[DEBUG AUTH] 📧 Verification email for: {user.email}")
    print(f"[DEBUG AUTH] 🎫 Token: {token}")
    print(f"[DEBUG AUTH] 🔗 Link: http://localhost:8000/verify.html?token={token}")
    print(f"[DEBUG AUTH] ============================================")
    return True


# --- Auth Schemas ---
class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(BaseModel):
    token: str


engine = create_engine(
    "sqlite:///./cronograma.db",
    connect_args={"check_same_thread": False},
)

Base = declarative_base()


class AreaCreate(BaseModel):
    """Schema de entrada para criar uma área."""

    nome: str
    cor: Optional[str] = None
    ordem: Optional[int] = None
    tipo: Optional[str] = "online"
    dia_semana: Optional[str] = None
    horario: Optional[str] = None
    sala: Optional[str] = None
    bloco: Optional[str] = None
    professor: Optional[str] = None
    subcategoria: Optional[str] = None


class AreaResponse(BaseModel):
    """Schema de resposta ao retornar uma área."""

    id: int
    user_id: int
    nome: str
    cor: Optional[str] = None
    ordem: Optional[int] = None
    tipo: Optional[str] = "online"
    dia_semana: Optional[str] = None
    horario: Optional[str] = None
    sala: Optional[str] = None
    bloco: Optional[str] = None
    professor: Optional[str] = None
    subcategoria: Optional[str] = None

    class Config:
        from_attributes = True


class AreaPatch(BaseModel):
    """Schema para atualizar uma área."""

    nome: Optional[str] = None
    cor: Optional[str] = None
    ordem: Optional[int] = None
    tipo: Optional[str] = None
    dia_semana: Optional[str] = None
    horario: Optional[str] = None
    sala: Optional[str] = None
    bloco: Optional[str] = None
    professor: Optional[str] = None
    subcategoria: Optional[str] = None


class TaskCreate(BaseModel):
    """Schema de entrada para criar uma tarefa."""

    area_id: Optional[int] = None
    titulo: str
    descricao: Optional[str] = None
    data_entrega: date
    prioridade: Optional[int] = None  # 1=baixa, 2=media, 3=alta
    meta_pomodoros: Optional[int] = None


class TaskPatch(BaseModel):
    """Schema para atualizar uma tarefa (campos opcionais)."""

    area_id: Optional[int] = None
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data_entrega: Optional[date] = None
    concluida: Optional[bool] = None
    duracao_minutos: Optional[int] = None
    prioridade: Optional[int] = None
    meta_pomodoros: Optional[int] = None
    pomodoros_concluidos: Optional[int] = None


class TaskResponse(BaseModel):
    """Schema de resposta ao retornar uma tarefa."""

    id: int
    area_id: Optional[int] = None
    titulo: str
    descricao: Optional[str] = None
    data_entrega: date
    concluida: bool = False
    duracao_minutos: Optional[int] = None
    prioridade: Optional[int] = None
    meta_pomodoros: Optional[int] = None
    pomodoros_concluidos: Optional[int] = None

    class Config:
        from_attributes = True


class SessaoCreate(BaseModel):
    class Config:
        from_attributes = True


class SessaoCreate(BaseModel):
    """Schema de entrada para registrar uma sessão de estudo."""

    area_id: int
    duracao_minutos: int
    data: Optional[date] = None  # se omitido, usa hoje


class SessaoResponse(BaseModel):
    """Schema de resposta ao retornar uma sessão."""

    id: int
    user_id: int
    area_id: int
    duracao_minutos: int
    data: date

    class Config:
        from_attributes = True


class SessaoPatch(BaseModel):
    """Schema para atualizar uma sessão."""

    area_id: Optional[int] = None
    duracao_minutos: Optional[int] = None
    data: Optional[date] = None


class PomodoroComplete(BaseModel):
    """Schema para completar um pomodoro."""

    area_id: int
    duracao_minutos: int
    task_id: Optional[int] = None
    titulo: Optional[str] = "Pomodoro Timer"


class HorasPorArea(BaseModel):
    """Schema para resumo de horas por área."""

    area_id: int
    area_nome: str
    area_cor: Optional[str] = None
    total_minutos: int
    total_horas: float


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(String(20), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=True)
    verification_token = Column(String(255), nullable=True)

    # Gamification fields
    current_streak = Column(Integer, default=0, nullable=True)
    longest_streak = Column(Integer, default=0, nullable=True)
    last_activity_date = Column(String(20), nullable=True)
    streak_freezes = Column(Integer, default=0, nullable=True)
    last_freeze_grant_date = Column(String(20), nullable=True)


class Areas(Base):
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


class Tasks(Base):
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


class Sessoes(Base):
    __tablename__ = "sessoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=False)
    duracao_minutos = Column(Integer, nullable=False)
    data = Column(Date, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(String(500), nullable=False)
    categoria = Column(String(50), nullable=False)
    requisito = Column(Integer, nullable=False)
    icone = Column(String(50), nullable=True)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    unlocked_at = Column(String(20), nullable=True)


Base.metadata.create_all(engine)

# Migrações
with engine.connect() as conn:
    # Tabela de usuários
    try:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, password_hash VARCHAR(255) NOT NULL, created_at VARCHAR(20), is_verified BOOLEAN DEFAULT 0, verification_token VARCHAR(255))"
            )
        )
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"))
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(255)")
        )
        conn.commit()
    except Exception:
        pass
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
    try:
        conn.execute(text("ALTER TABLE sessoes ADD COLUMN task_id INTEGER"))
        conn.commit()
    except Exception:
        pass

    # Gamification migrations
    try:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN current_streak INTEGER DEFAULT 0")
        )
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN longest_streak INTEGER DEFAULT 0")
        )
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN last_activity_date VARCHAR(20)")
        )
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN streak_freezes INTEGER DEFAULT 0")
        )
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN last_freeze_grant_date VARCHAR(20)")
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
        count = result.fetchone()[0]
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

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Funções de autenticação simples (sem biblioteca JWT)
SECRET_KEY = os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(user_id: int) -> str:
    expire = int(time.time()) + (ACCESS_TOKEN_EXPIRE_HOURS * 3600)
    data = f"{user_id}:{expire}"
    encoded = base64.b64encode(data.encode()).decode()
    signature = hashlib.sha256((data + SECRET_KEY).encode()).hexdigest()[:16]
    return f"{encoded}.{signature}"


def verify_token(token: str) -> tuple[bool, int]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False, 0
        encoded, signature = parts
        data = base64.b64decode(encoded.encode()).decode()
        user_id, expire_str = data.split(":")
        expire = int(expire_str)
        if time.time() > expire:
            return False, 0
        expected_sig = hashlib.sha256((data + SECRET_KEY).encode()).hexdigest()[:16]
        if signature != expected_sig:
            return False, 0
        return True, int(user_id)
    except Exception:
        return False, 0


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> int:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    valid, user_id = verify_token(credentials.credentials)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


# ============== GAMIFICATION FUNCTIONS ==============


def calcular_level(xp_total: int) -> int:
    """Calcula o level baseado no XP total usando curva: XP = 100 * level^1.5"""
    level = 1
    while True:
        xp_needed = int(100 * (level**1.5))
        if xp_total < xp_needed:
            break
        xp_total -= xp_needed
        level += 1
    return level


def xp_para_proximo_level(xp_total: int) -> tuple[int, int]:
    """Retorna (XP atual no level, XP necessario para proximo level)"""
    level = calcular_level(xp_total)
    xp_needed = int(100 * (level**1.5))
    xp_in_level = xp_total
    for l in range(1, level):
        xp_in_level -= int(100 * (l**1.5))
    return max(0, xp_in_level), xp_needed


def calcular_xp_total(user_id: int, db: Session) -> int:
    """Calcula XP total: 1 XP por minuto de sessao + 50 XP por tarefa concluida"""
    result = (
        db.query(func.sum(Sessoes.duracao_minutos))
        .filter(Sessoes.user_id == user_id)
        .scalar()
    )
    xp_sessoes = int(result or 0)
    result = (
        db.query(func.count(Tasks.id))
        .filter(Tasks.user_id == user_id, Tasks.concluida == True)
        .scalar()
    )
    xp_tarefas = int(result or 0) * 50
    return xp_sessoes + xp_tarefas


def contar_pomodoros(user_id: int, db: Session) -> int:
    """Conta total de sessoes (pomodoros) do usuario"""
    result = (
        db.query(func.count(Sessoes.id)).filter(Sessoes.user_id == user_id).scalar()
    )
    return int(result or 0)


def contar_tarefas_concluidas(user_id: int, db: Session) -> int:
    """Conta tarefas concluidas do usuario"""
    result = (
        db.query(func.count(Tasks.id))
        .filter(Tasks.user_id == user_id, Tasks.concluida == True)
        .scalar()
    )
    return int(result or 0)


def atualizar_streak(user_id: int, db: Session) -> int:
    """Atualiza a sequencia de dias do usuario"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return 0
    today = date.today().isoformat()
    if user.last_activity_date == today:
        return user.current_streak or 0
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if user.last_activity_date == yesterday:
        user.current_streak = (user.current_streak or 0) + 1
    elif user.last_activity_date is None or user.last_activity_date < yesterday:
        if (user.streak_freezes or 0) > 0 and user.last_activity_date is not None:
            user.streak_freezes = (user.streak_freezes or 0) - 1
        else:
            user.current_streak = 1
    else:
        user.current_streak = 1
    if (user.current_streak or 0) > (user.longest_streak or 0):
        user.longest_streak = user.current_streak
    user.last_activity_date = today
    db.commit()
    return user.current_streak or 0


def atualizar_freezes(user_id: int, db: Session) -> int:
    """Concede freeze semanal (max 4)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return 0
    today = date.today().isoformat()
    last_grant = user.last_freeze_grant_date
    if last_grant:
        last_date = datetime.fromisoformat(last_grant).date()
        days_since = (date.today() - last_date).days
        if days_since < 7:
            return user.streak_freezes or 0
    user.streak_freezes = min((user.streak_freezes or 0) + 1, 4)
    user.last_freeze_grant_date = today
    db.commit()
    return user.streak_freezes or 0


def verificar_conquistas(user_id: int, db: Session) -> list:
    """Verifica e desbloqueia conquistas"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    xp_total = calcular_xp_total(user_id, db)
    level = calcular_level(xp_total)
    streak = user.current_streak or 0
    pomodoros = contar_pomodoros(user_id, db)
    tarefas = contar_tarefas_concluidas(user_id, db)
    unlocked_ids = [
        ua.achievement_id
        for ua in db.query(UserAchievement)
        .filter(UserAchievement.user_id == user_id)
        .all()
    ]
    new_unlocks = []
    categories = ["xp", "streak", "pomodoro", "tasks", "level"]
    values = [xp_total, streak, pomodoros, tarefas, level]
    for cat, val in zip(categories, values):
        achievements = db.query(Achievement).filter(Achievement.categoria == cat).all()
        for ach in achievements:
            if ach.id not in unlocked_ids and val >= ach.requisito:
                ua = UserAchievement(
                    user_id=user_id,
                    achievement_id=ach.id,
                    unlocked_at=datetime.utcnow().isoformat(),
                )
                db.add(ua)
                unlocked_ids.append(ach.id)
                new_unlocks.append(
                    {
                        "id": ach.id,
                        "nome": ach.nome,
                        "descricao": ach.descricao,
                        "icone": ach.icone,
                    }
                )
    if new_unlocks:
        db.commit()
    return new_unlocks


app = FastAPI()

STATIC_DIR = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# --- Admin Migration Endpoint ---
MIGRATION_SECRET = os.environ.get("MIGRATION_SECRET", "")


@app.post("/admin/init")
def init_database():
    """Initialize database tables"""
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
                    user_id INTEGER DEFAULT 1
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


# --- Import Data Endpoint ---
class ImportData(BaseModel):
    users: Optional[List[dict]] = []
    areas: Optional[List[dict]] = []
    tasks: Optional[List[dict]] = []
    sessoes: Optional[List[dict]] = []


@app.post("/admin/import")
def import_data(data: ImportData, secret: str = ""):
    """Import data from JSON (for migration from SQLite)"""
    if MIGRATION_SECRET and secret != MIGRATION_SECRET:
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
                        VALUES (:id, :nome, :cor, :ordem, :tipo, :dia_semana, :horario, :sala, :bloco, :professor, :subcategoria, 1)
                        ON CONFLICT (id) DO NOTHING
                    """),
                        area,
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
                        VALUES (:id, :area_id, :titulo, :descricao, :data_entrega, :concluida, :duracao_minutos, :prioridade, :meta_pomodoros, :pomodoros_concluidos, 1)
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
                        VALUES (:id, :area_id, :duracao_minutos, :data, :task_id, 1)
                        ON CONFLICT (id) DO NOTHING
                    """),
                        sessao,
                    )
                conn.commit()
            report["tables"].append(
                {"name": "sessoes", "records": len(data.sessoes), "status": "ok"}
            )

    except Exception as e:
        report["errors"].append(str(e))

    return report


# --- Admin Migration Endpoint ---
MIGRATION_SECRET = os.environ.get("MIGRATION_SECRET", "")


@app.post("/admin/migrate")
def migrate_data(secret: str = ""):
    if MIGRATION_SECRET and secret != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    report = {"tables": [], "errors": []}

    sqlite_path = Path(__file__).parent / "cronograma.db"
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
                print(f"[MIGRATION] {table}: {count} records")

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


# --- Auth Endpoints ---
@app.post("/auth/register", response_model=TokenResponse)
def register(body: UserRegister, db: Session = Depends(get_db)):
    if not validate_email(body.email):
        raise HTTPException(status_code=400, detail="Email inválido")

    senha_valida, msg_erro = validate_password(body.password)
    if not senha_valida:
        raise HTTPException(status_code=400, detail=msg_erro)

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    verification_token = generate_verification_token()

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        created_at=datetime.utcnow().isoformat(),
        is_verified=False,
        verification_token=verification_token,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    print(f"[DEBUG AUTH] User created: {user.email} (id={user.id})")

    sendVerificationEmail(user, verification_token)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if user.is_verified is False:
        print(f"[DEBUG AUTH] Login blocked (not verified): {user.email}")
        raise HTTPException(
            status_code=403, detail="Conta não verificada. Verifique seu email."
        )

    print(f"[DEBUG AUTH] Login success: {user.email}")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@app.get("/auth/check")
def check_auth(user_id: int = Depends(get_current_user)):
    return {"user_id": user_id, "authenticated": True}


@app.get("/auth/verify-email")
def verify_email_get(token: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            return {"success": False, "message": "Token inválido ou expirado"}

        user.is_verified = True
        user.verification_token = None
        db.commit()

        print(f"[DEBUG AUTH] User verified via link: {user.email}")
        return {"success": True, "message": "Email verificado com sucesso!"}

    except Exception as e:
        print(f"[DEBUG AUTH] Verify error: {e}")
        return {"success": False, "message": "Erro ao verificar email"}


@app.post("/auth/verify-email")
def verify_email_post(body: VerifyEmailRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.verification_token == body.token).first()
        if not user:
            return {"success": False, "message": "Token inválido ou expirado"}

        user.is_verified = True
        user.verification_token = None
        db.commit()

        print(f"[DEBUG AUTH] User verified via manual token: {user.email}")
        return {"success": True, "message": "Email verificado com sucesso!"}

    except Exception as e:
        print(f"[DEBUG AUTH] Verify error: {e}")
        return {"success": False, "message": "Erro ao verificar email"}


@app.get("/")
def index():
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/areas", response_model=List[AreaResponse])
def listar_areas(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(Areas).filter(Areas.user_id == user_id).all()


@app.post("/areas", response_model=AreaResponse)
def criar_area(
    body: AreaCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    area = Areas(
        user_id=user_id,
        nome=body.nome,
        cor=body.cor,
        ordem=body.ordem,
        tipo=body.tipo or "online",
        dia_semana=body.dia_semana,
        horario=body.horario,
        sala=body.sala,
        bloco=body.bloco,
        professor=body.professor,
        subcategoria=body.subcategoria,
    )
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


@app.patch("/areas/{area_id}", response_model=AreaResponse)
def atualizar_area(area_id: int, body: AreaPatch, db: Session = Depends(get_db)):
    area = db.query(Areas).filter(Areas.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    if body.nome is not None:
        setattr(area, "nome", body.nome)
    if body.cor is not None:
        setattr(area, "cor", body.cor)
    if body.ordem is not None:
        setattr(area, "ordem", body.ordem)
    if body.tipo is not None:
        setattr(area, "tipo", body.tipo)
    if body.dia_semana is not None:
        setattr(area, "dia_semana", body.dia_semana)
    if body.horario is not None:
        setattr(area, "horario", body.horario)
    if body.sala is not None:
        setattr(area, "sala", body.sala)
    if body.bloco is not None:
        setattr(area, "bloco", body.bloco)
    if body.professor is not None:
        setattr(area, "professor", body.professor)
    if body.subcategoria is not None:
        setattr(area, "subcategoria", body.subcategoria)
    db.commit()
    db.refresh(area)
    return area


@app.delete("/areas/{area_id}", status_code=204)
def excluir_area(area_id: int, db: Session = Depends(get_db)):
    area = db.query(Areas).filter(Areas.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    db.query(Tasks).filter(Tasks.area_id == area_id).delete()
    db.query(Sessoes).filter(Sessoes.area_id == area_id).delete()
    db.delete(area)
    db.commit()
    return None


# --- Tasks ---
@app.get("/tasks", response_model=List[TaskResponse])
def listar_tasks(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(Tasks).filter(Tasks.user_id == user_id).all()


@app.post("/tasks", response_model=TaskResponse)
def criar_task(
    body: TaskCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = Tasks(
        user_id=user_id,
        area_id=body.area_id,
        titulo=body.titulo,
        descricao=body.descricao,
        data_entrega=body.data_entrega,
        prioridade=body.prioridade,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def atualizar_task(task_id: int, body: TaskPatch, db: Session = Depends(get_db)):
    task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    if body.area_id is not None:
        setattr(task, "area_id", body.area_id)
    if body.titulo is not None:
        setattr(task, "titulo", body.titulo)
    if body.descricao is not None:
        setattr(task, "descricao", body.descricao)
    if body.data_entrega is not None:
        setattr(task, "data_entrega", body.data_entrega)

    if body.concluida is not None:
        if (
            body.concluida
            and body.duracao_minutos is not None
            and body.duracao_minutos > 0
        ):
            sessao = Sessoes(
                area_id=task.area_id,
                duracao_minutos=body.duracao_minutos,
                data=date.today(),
                task_id=task.id,
            )
            db.add(sessao)
        elif not body.concluida:
            db.query(Sessoes).filter(Sessoes.task_id == task_id).delete()
        setattr(task, "concluida", body.concluida)
    if body.duracao_minutos is not None:
        setattr(task, "duracao_minutos", body.duracao_minutos)
    if body.prioridade is not None:
        setattr(task, "prioridade", body.prioridade)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def excluir_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    db.query(Sessoes).filter(Sessoes.task_id == task_id).delete()
    db.delete(task)
    db.commit()
    return None


# --- Sessões de estudo ---
@app.get("/sessoes", response_model=List[SessaoResponse])
def listar_sessoes(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Sessoes)
        .filter(Sessoes.user_id == user_id)
        .order_by(Sessoes.data.desc())
        .all()
    )


@app.post("/sessoes", response_model=SessaoResponse)
def criar_sessao(
    body: SessaoCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data_sessao = body.data or date.today()
    sessao = Sessoes(
        user_id=user_id,
        area_id=body.area_id,
        duracao_minutos=body.duracao_minutos,
        data=data_sessao,
    )
    db.add(sessao)
    db.commit()
    db.refresh(sessao)
    return sessao


@app.patch("/sessoes/{sessao_id}", response_model=SessaoResponse)
def atualizar_sessao(sessao_id: int, body: SessaoPatch, db: Session = Depends(get_db)):
    sessao = db.query(Sessoes).filter(Sessoes.id == sessao_id).first()
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if body.area_id is not None:
        setattr(sessao, "area_id", body.area_id)
    if body.duracao_minutos is not None:
        setattr(sessao, "duracao_minutos", body.duracao_minutos)
    if body.data is not None:
        setattr(sessao, "data", body.data)
    db.commit()
    db.refresh(sessao)
    return sessao


@app.delete("/sessoes/{sessao_id}", status_code=204)
def excluir_sessao(sessao_id: int, db: Session = Depends(get_db)):
    sessao = db.query(Sessoes).filter(Sessoes.id == sessao_id).first()
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    db.delete(sessao)
    db.commit()
    return None


@app.post("/pomodoro/completar", response_model=SessaoResponse)
def completar_pomodoro(
    body: PomodoroComplete,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria uma sessão de estudo ao completar um pomodoro."""
    sessao = Sessoes(
        user_id=user_id,
        area_id=body.area_id,
        duracao_minutos=body.duracao_minutos,
        data=date.today(),
        task_id=body.task_id,
    )
    db.add(sessao)

    if body.task_id:
        task = db.query(Tasks).filter(Tasks.id == body.task_id).first()
        if task:
            db.execute(
                text(
                    "UPDATE tasks SET pomodoros_concluidos = pomodoros_concluidos + 1 WHERE id = :id"
                ),
                {"id": body.task_id},
            )

    db.commit()
    db.refresh(sessao)
    return sessao


@app.get("/sessoes/resumo", response_model=List[HorasPorArea])
def resumo_horas(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retorna total de minutos/horas de estudo por área."""
    rows = (
        db.query(
            Sessoes.area_id,
            Areas.nome,
            Areas.cor,
            func.sum(Sessoes.duracao_minutos).label("total_minutos"),
        )
        .join(Areas, (Sessoes.area_id == Areas.id) & (Areas.user_id == user_id))
        .filter(Sessoes.user_id == user_id)
        .group_by(Sessoes.area_id)
        .all()
    )
    return [
        HorasPorArea(
            area_id=r.area_id,
            area_nome=r.nome,
            area_cor=r.cor,
            total_minutos=int(r.total_minutos or 0),
            total_horas=round((r.total_minutos or 0) / 60, 1),
        )
        for r in rows
    ]


@app.get("/gamification-summary")
def gamification_summary(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retorna todos os dados de gamificacao do usuario"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    xp_total = calcular_xp_total(user_id, db)
    level = calcular_level(xp_total)
    xp_atual, xp_proximo = xp_para_proximo_level(xp_total)
    pomodoros = contar_pomodoros(user_id, db)
    tarefas = contar_tarefas_concluidas(user_id, db)
    unlocked = (
        db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()
    )
    unlocked_ids = [ua.achievement_id for ua in unlocked]
    all_achievements = {}
    for cat in ["xp", "streak", "pomodoro", "tasks", "level"]:
        achievements = db.query(Achievement).filter(Achievement.categoria == cat).all()
        all_achievements[cat] = [
            {
                "id": a.id,
                "nome": a.nome,
                "descricao": a.descricao,
                "requisito": a.requisito,
                "icone": a.icone,
                "desbloqueado": a.id in unlocked_ids,
                "desbloqueado_em": next(
                    (ua.unlocked_at for ua in unlocked if ua.achievement_id == a.id),
                    None,
                ),
            }
            for a in achievements
        ]
    return {
        "xp_total": xp_total,
        "level": level,
        "xp_atual_no_level": xp_atual,
        "xp_para_proximo_level": xp_proximo,
        "progresso_level": round((xp_atual / xp_proximo) * 100, 1)
        if xp_proximo > 0
        else 100,
        "current_streak": user.current_streak or 0,
        "longest_streak": user.longest_streak or 0,
        "streak_freezes": user.streak_freezes or 0,
        "total_pomodoros": pomodoros,
        "tarefas_concluidas": tarefas,
        "achievements": all_achievements,
        "conquistas_desbloqueadas": len(unlocked_ids),
        "total_conquistas": db.query(Achievement).count(),
    }
