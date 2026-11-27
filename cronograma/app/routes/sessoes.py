"""Rotas de sessões de estudo: CRUD + resumo de horas + pomodoro."""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from config import get_db
from logger import audit, get_logger
from middleware import rate_limit
from models.area import Areas
from models.schemas import (
    HorasPorArea,
    PomodoroComplete,
    SessaoCreate,
    SessaoPatch,
    SessaoResponse,
)
from models.sessao import Sessoes
from models.task import Tasks
from models.user import User
from services.auth_service import get_current_user
from services.funnel_service import record_event
from services.gamification_service import verificar_conquistas
from services.streak_service import atualizar_streak

log = get_logger("cronograma.sessoes")

router = APIRouter(tags=["sessoes"])


def _validate_task_reference(
    db: Session,
    user_id: int,
    task_id: Optional[int],
    area_id: Optional[int],
) -> None:
    """Garante que a tarefa existe, pertence ao usuário e combina com a área."""
    if task_id is None:
        return

    task = (
        db.query(Tasks)
        .filter(Tasks.id == task_id, Tasks.user_id == user_id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=404, detail="Tarefa não encontrada ou não pertence ao usuário"
        )
    if task.area_id is not None and area_id is not None and task.area_id != area_id:
        raise HTTPException(
            status_code=400, detail="A tarefa não pertence à área informada"
        )


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/sessoes", response_model=List[SessaoResponse])
def listar_sessoes(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Sessoes)
        .filter(Sessoes.user_id == user_id)
        .order_by(Sessoes.data.desc())
        .all()
    )


@router.post("/sessoes", response_model=SessaoResponse)
def criar_sessao(
    body: SessaoCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    area = (
        db.query(Areas)
        .filter(Areas.id == body.area_id, Areas.user_id == user_id)
        .first()
    )
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")

    if body.duracao_minutos < 5:
        raise HTTPException(
            status_code=400,
            detail="Duração mínima de 5 minutos por sessão"
        )

    _validate_task_reference(db, user_id, body.task_id, body.area_id)

    data_sessao = body.data or date.today()
    sessao = Sessoes(
        user_id=user_id,
        area_id=body.area_id,
        duracao_minutos=body.duracao_minutos,
        data=data_sessao,
        task_id=body.task_id,
    )
    db.add(sessao)
    audit(
        "sessao.create",
        user_id=user_id,
        area_id=body.area_id,
        duracao_minutos=body.duracao_minutos,
    )

    # Coins are earned only via pomodoro completions (3 per pomodoro).
    # Manual sessions do not award coins to keep the system consistent.
    db.commit()

    # Update streak and check achievements
    atualizar_streak(user_id, db)
    novas_conquistas = verificar_conquistas(user_id, db)

    db.refresh(sessao)
    return sessao


@router.get("/sessoes/resumo", response_model=List[HorasPorArea])
def resumo_horas(
    start: Optional[date] = None,
    end: Optional[date] = None,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna total de minutos/horas de estudo por área. Pode filtrar por período."""
    if start is not None and end is not None and start > end:
        raise HTTPException(status_code=422, detail="start não pode ser maior que end")
    query = (
        db.query(
            Sessoes.area_id,
            Areas.nome,
            Areas.cor,
            func.sum(Sessoes.duracao_minutos).label("total_minutos"),
        )
        .join(Areas, (Sessoes.area_id == Areas.id) & (Areas.user_id == user_id))
        .filter(Sessoes.user_id == user_id)
    )

    # Apply date filtering if provided
    if start is not None:
        query = query.filter(Sessoes.data >= start)

    if end is not None:
        query = query.filter(Sessoes.data <= end)

    rows = query.group_by(Sessoes.area_id, Areas.nome, Areas.cor).all()
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


@router.patch("/sessoes/{sessao_id}", response_model=SessaoResponse)
def atualizar_sessao(
    sessao_id: int,
    body: SessaoPatch,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit(f"crud:sessoes:patch:{user_id}", max_req=60, window=60)
    sessao = (
        db.query(Sessoes)
        .filter(Sessoes.id == sessao_id, Sessoes.user_id == user_id)
        .first()
    )
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    fields_set = body.model_fields_set

    if "area_id" in fields_set:
        if body.area_id is None:
            raise HTTPException(status_code=422, detail="area_id não pode ser nulo")
        area = (
            db.query(Areas)
            .filter(Areas.id == body.area_id, Areas.user_id == user_id)
            .first()
        )
        if not area:
            raise HTTPException(
                status_code=404, detail="Área não encontrada ou não pertence ao usuário"
            )
        setattr(sessao, "area_id", body.area_id)
    if "duracao_minutos" in fields_set:
        if body.duracao_minutos is None:
            raise HTTPException(status_code=422, detail="duracao_minutos não pode ser nulo")
        setattr(sessao, "duracao_minutos", body.duracao_minutos)
    if "data" in fields_set:
        if body.data is None:
            raise HTTPException(status_code=422, detail="data não pode ser nula")
        setattr(sessao, "data", body.data)
    if "task_id" in fields_set:
        setattr(sessao, "task_id", body.task_id)

    effective_area_id = sessao.area_id
    effective_task_id = sessao.task_id
    _validate_task_reference(db, user_id, effective_task_id, effective_area_id)

    db.commit()
    db.refresh(sessao)
    return sessao


@router.delete("/sessoes/{sessao_id}", status_code=204)
def excluir_sessao(
    sessao_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit(f"crud:sessoes:delete:{user_id}", max_req=60, window=60)
    sessao = (
        db.query(Sessoes)
        .filter(Sessoes.id == sessao_id, Sessoes.user_id == user_id)
        .first()
    )
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    try:
        db.delete(sessao)
        db.commit()
    except Exception as e:
        db.rollback()
        log.exception(
            "Sessao delete failed",
            extra={"sessao_id": sessao_id, "user_id": user_id, "action": "sessao_delete"},
        )
        raise HTTPException(status_code=500, detail="Erro ao excluir sessão") from e
    return None


@router.post("/pomodoro/completar")
def completar_pomodoro(
    body: PomodoroComplete,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria uma sessão de estudo ao completar um pomodoro."""
    area = (
        db.query(Areas)
        .filter(Areas.id == body.area_id, Areas.user_id == user_id)
        .first()
    )
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")

    _validate_task_reference(db, user_id, body.task_id, body.area_id)

    sessao = Sessoes(
        user_id=user_id,
        area_id=body.area_id,
        duracao_minutos=body.duracao_minutos,
        data=date.today(),
        task_id=body.task_id,
    )
    db.add(sessao)

    # Atomic coins increment to avoid lost updates under concurrency
    db.execute(
        text("UPDATE users SET coins = COALESCE(coins, 0) + 3 WHERE id = :id"),
        {"id": user_id},
    )

    if body.task_id:
        db.execute(
            text(
                "UPDATE tasks SET pomodoros_concluidos = COALESCE(pomodoros_concluidos, 0) + 1 "
                "WHERE id = :id AND user_id = :user_id"
            ),
            {"id": body.task_id, "user_id": user_id},
        )

    db.commit()

    # Update streak and check achievements
    atualizar_streak(user_id, db)
    novas_conquistas = verificar_conquistas(user_id, db)

    record_event(db, "pomodoro", user_id)

    db.refresh(sessao)

    # Read updated coins
    user = db.query(User).filter(User.id == user_id).first()
    return {
        "sessao": sessao,
        "novas_conquistas": novas_conquistas,
        "coins": user.coins if user else 0,
    }
