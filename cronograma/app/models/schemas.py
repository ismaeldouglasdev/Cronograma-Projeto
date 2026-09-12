"""Schemas Pydantic para request/response."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ─── Auth ─────────────────────────────────────────────────────────────────────


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


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ─── Areas ────────────────────────────────────────────────────────────────────


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

    model_config = ConfigDict(from_attributes=True)


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


# ─── Tasks ────────────────────────────────────────────────────────────────────


class TaskCreate(BaseModel):
    """Schema de entrada para criar uma tarefa."""

    area_id: Optional[int] = None
    titulo: str
    descricao: Optional[str] = None
    data_entrega: Optional[date] = None
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

    model_config = ConfigDict(from_attributes=True)


# ─── Sessoes ──────────────────────────────────────────────────────────────────


class SessaoCreate(BaseModel):
    """Schema de entrada para registrar uma sessão de estudo."""

    area_id: int
    duracao_minutos: int
    data: Optional[date] = None  # se omitido, usa hoje
    task_id: Optional[int] = None


class SessaoResponse(BaseModel):
    """Schema de resposta ao retornar uma sessão."""

    id: int
    user_id: int
    area_id: int
    duracao_minutos: int
    data: date
    task_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SessaoPatch(BaseModel):
    """Schema para atualizar uma sessão."""

    area_id: Optional[int] = None
    duracao_minutos: Optional[int] = None
    data: Optional[date] = None
    task_id: Optional[int] = None


# ─── Pomodoro ─────────────────────────────────────────────────────────────────


class PomodoroComplete(BaseModel):
    """Schema para completar um pomodoro."""

    area_id: int
    duracao_minutos: int
    task_id: Optional[int] = None
    titulo: Optional[str] = "Pomodoro Timer"


# ─── Resumo ───────────────────────────────────────────────────────────────────


class HorasPorArea(BaseModel):
    """Schema para resumo de horas por área."""

    area_id: int
    area_nome: str
    area_cor: Optional[str] = None
    total_minutos: int
    total_horas: float


# ─── Admin / Import ───────────────────────────────────────────────────────────


class ImportData(BaseModel):
    users: Optional[List[dict]] = []
    areas: Optional[List[dict]] = []
    tasks: Optional[List[dict]] = []
    sessoes: Optional[List[dict]] = []


# ─── Client Logs ──────────────────────────────────────────────────────────────


class ClientLogBatch(BaseModel):
    logs: List[dict]
