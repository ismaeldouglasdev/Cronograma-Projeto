"""Schemas Pydantic para request/response."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    # Register com verificação de e-mail ativa: sem access_token emitido,
    # usuário precisa confirmar o e-mail antes do login. fallback_token só
    # vem preenchido quando o envio do e-mail falhou (fluxo manual).
    verification_required: bool = False
    fallback_token: Optional[str] = None


class VerifyEmailRequest(BaseModel):
    token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


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
    meta_horas_semanal: Optional[int] = None


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
    meta_horas_semanal: Optional[int] = None

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
    meta_horas_semanal: Optional[int] = None


# ─── Tasks ────────────────────────────────────────────────────────────────────


class TaskCreate(BaseModel):
    """Schema de entrada para criar uma tarefa."""

    area_id: Optional[int] = Field(default=None, ge=1)
    titulo: str = Field(min_length=1, max_length=255)
    descricao: Optional[str] = Field(default=None, max_length=500)
    # Obrigatorio: a coluna tasks.data_entrega e NOT NULL e o form do front
    # marca o campo como required. Declarar aqui como Optional deixava o
    # INSERT enviar NULL e o banco responder IntegrityError (500) em vez de
    # um 422 de validacao.
    data_entrega: date
    prioridade: Optional[int] = Field(default=None, ge=1, le=3)  # 1=baixa, 2=media, 3=alta
    meta_pomodoros: Optional[int] = Field(default=None, ge=0)


class TaskPatch(BaseModel):
    """Schema para atualizar uma tarefa (campos opcionais)."""

    area_id: Optional[int] = Field(default=None, ge=1)
    titulo: Optional[str] = Field(default=None, min_length=1, max_length=255)
    descricao: Optional[str] = Field(default=None, max_length=500)
    data_entrega: Optional[date] = None
    concluida: Optional[bool] = None
    duracao_minutos: Optional[int] = Field(default=None, ge=0)
    prioridade: Optional[int] = Field(default=None, ge=1, le=3)
    meta_pomodoros: Optional[int] = Field(default=None, ge=0)
    pomodoros_concluidos: Optional[int] = Field(default=None, ge=0)


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

    area_id: int = Field(ge=1)
    duracao_minutos: int = Field(ge=5, le=1440)
    data: Optional[date] = None  # se omitido, usa hoje
    task_id: Optional[int] = Field(default=None, ge=1)


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

    area_id: Optional[int] = Field(default=None, ge=1)
    duracao_minutos: Optional[int] = Field(default=None, ge=5, le=1440)
    data: Optional[date] = None
    task_id: Optional[int] = Field(default=None, ge=1)


# ─── Pomodoro ─────────────────────────────────────────────────────────────────


class PomodoroComplete(BaseModel):
    """Schema para completar um pomodoro."""

    area_id: int = Field(ge=1)
    duracao_minutos: int = Field(ge=1, le=1440)
    task_id: Optional[int] = Field(default=None, ge=1)
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


# ─── Missions ─────────────────────────────────────────────────────────────────


class MissionItem(BaseModel):
    key: str
    label: str
    kind: Optional[str] = None
    target: int
    progress: int
    completed: bool
    xp_reward: int


class MissionsTodayResponse(BaseModel):
    date: Optional[str] = None
    missions: List[MissionItem]
    completed_count: int
    total: int
    all_completed: bool
    coins: int
