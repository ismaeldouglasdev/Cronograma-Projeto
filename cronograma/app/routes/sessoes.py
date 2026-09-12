"""Rotas de sessões de estudo: CRUD + resumo de horas + pomodoro."""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from config import get_db
from logger import audit
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
from services.gamification_service import verificar_conquistas
from services.streak_service import atualizar_streak

router = APIRouter(tags=["sessoes"])


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

    data_sessao = body.data or date.today()
    sessao = Sessoes(
        user_id=user_id,
        area_id=body.area_id,
        duracao_minutos=body.duracao_minutos,
        data=data_sessao,
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
    start: Optional[str] = None,
    end: Optional[str] = None,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna total de minutos/horas de estudo por área. Pode filtrar por período."""
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
    if start:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            query = query.filter(Sessoes.data >= start_date)
        except ValueError:
            pass  # Invalid date format, ignore

    if end:
        try:
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            query = query.filter(Sessoes.data <= end_date)
        except ValueError:
            pass  # Invalid date format, ignore

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
    if body.area_id is not None:
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
    if body.duracao_minutos is not None:
        setattr(sessao, "duracao_minutos", body.duracao_minutos)
    if body.data is not None:
        setattr(sessao, "data", body.data)
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
    except Exception:
        db.rollback()
        pass
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
                "UPDATE tasks SET pomodoros_concluidos = pomodoros_concluidos + 1 WHERE id = :id"
            ),
            {"id": body.task_id},
        )

    db.commit()

    # Update streak and check achievements
    atualizar_streak(user_id, db)
    novas_conquistas = verificar_conquistas(user_id, db)

    db.refresh(sessao)

    # Read updated coins
    user = db.query(User).filter(User.id == user_id).first()
    return {
        "sessao": sessao,
        "novas_conquistas": novas_conquistas,
        "coins": user.coins if user else 0,
    }
