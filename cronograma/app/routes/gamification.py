"""Rotas de gamification: summary, coins shop."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import FREEZE_COST, MIGRATION_SECRET, get_db
from models.achievement import Achievement, UserAchievement
from models.schemas import HorasPorArea
from models.user import User
from services.auth_service import get_current_user
from services.gamification_service import (
    calcular_level,
    calcular_xp_total,
    contar_pomodoros,
    contar_tarefas_concluidas,
    xp_para_proximo_level,
)

router = APIRouter(tags=["gamification"])


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/gamification-summary")
def gamification_summary(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retorna todos os dados de gamificacao do usuario"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
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
    for cat in ["xp", "streak", "pomodoro", "tasks", "level", "coins"]:
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
        "coins": user.coins or 0,
        "total_pomodoros": pomodoros,
        "tarefas_concluidas": tarefas,
        "achievements": all_achievements,
        "conquistas_desbloqueadas": len(unlocked_ids),
        "total_conquistas": db.query(Achievement).count(),
    }


@router.post("/coins/buy-freeze")
def buy_freeze(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """Compra um freeze usando coins."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    current_coins = user.coins or 0
    current_freezes = user.streak_freezes or 0

    if current_coins < FREEZE_COST:
        raise HTTPException(
            status_code=400,
            detail=f"Coins insuficientes. Você tem {current_coins} coins, precisa de {FREEZE_COST}.",
        )

    if current_freezes >= 4:
        raise HTTPException(
            status_code=400, detail="Limite máximo de freezes atingido (4)."
        )

    # Deduct coins and add freeze
    user.coins = current_coins - FREEZE_COST
    user.streak_freezes = current_freezes + 1
    db.commit()

    return {
        "success": True,
        "message": "Freeze comprado com sucesso!",
        "coins": user.coins,
        "freezes": user.streak_freezes,
    }


@router.post("/coins/add")
def add_coins(
    amount: int = 1,
    secret: str = "",
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Adiciona coins ao usuário (para testing/dev). Limite: 100 por chamada."""
    if not MIGRATION_SECRET or secret != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Acesso administrativo negado")
    if amount < 0:
        raise HTTPException(
            status_code=400, detail="Valor não pode ser negativo"
        )
    if amount > 100:
        raise HTTPException(
            status_code=400, detail="Limite máximo de 100 coins por chamada"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.coins = (user.coins or 0) + amount
    db.commit()

    return {"coins": user.coins}
