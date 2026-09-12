"""Serviços de gamificação: XP, level, coins, conquistas."""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.achievement import Achievement, UserAchievement
from models.sessao import Sessoes
from models.task import Tasks
from models.user import User


def calcular_level(xp_total: int) -> int:
    """Calcula o level baseado no XP total usando curva: XP acumulado = 100 * level^1.5"""
    level = 0
    while xp_total >= int(100 * ((level + 1) ** 1.5)):
        level += 1
    return level


def xp_para_proximo_level(xp_total: int) -> tuple[int, int]:
    """Retorna (XP atual no level, XP necessario para proximo level)"""
    level = calcular_level(xp_total)
    xp_atual = xp_total - int(100 * (level ** 1.5))
    xp_proximo = int(100 * ((level + 1) ** 1.5)) - int(100 * (level ** 1.5))
    return max(0, xp_atual), max(1, xp_proximo)


def calcular_xp_total(user_id: int, db: Session) -> int:
    """Calcula XP total: 10 XP por 30 min de sessao + 5 XP por tarefa concluida"""
    # XP por minutos estudados (10 XP por 30 min = 1 XP a cada 3 min)
    result = (
        db.query(func.sum(Sessoes.duracao_minutos))
        .filter(Sessoes.user_id == user_id)
        .scalar()
    )
    minutos = int(result or 0)
    xp_sessoes = (minutos * 10) // 30  # 10 XP por 30 minutos

    # XP por tarefas concluidas (5 XP por tarefa)
    result = (
        db.query(func.count(Tasks.id))
        .filter(Tasks.user_id == user_id, Tasks.concluida == True)
        .scalar()
    )
    xp_tarefas = int(result or 0) * 5
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
    coins = user.coins or 0
    unlocked_ids = [
        ua.achievement_id
        for ua in db.query(UserAchievement)
        .filter(UserAchievement.user_id == user_id)
        .all()
    ]
    new_unlocks = []
    categories = ["xp", "streak", "pomodoro", "tasks", "level", "coins"]
    values = [xp_total, streak, pomodoros, tarefas, level, coins]
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
                        "categoria": cat,
                        "requisito": ach.requisito,
                    }
                )
    if new_unlocks:
        db.commit()
    return new_unlocks


def cleanup_stale_guests(db: Session, max_age_days: int = 30) -> int:
    """Remove contas guest antigas."""
    from datetime import date, timedelta, timezone as tz

    cutoff = (datetime.now(tz.utc) - timedelta(days=max_age_days)).isoformat()
    guests = db.query(User).filter(User.is_guest == True, User.created_at < cutoff).all()
    removed = 0
    for g in guests:
        db.query(UserAchievement).filter(UserAchievement.user_id == g.id).delete()
        db.query(Sessoes).filter(Sessoes.user_id == g.id).delete()
        db.query(Tasks).filter(Tasks.user_id == g.id).delete()
        db.query(Areas).filter(Areas.user_id == g.id).delete()
        db.delete(g)
        removed += 1
    if removed:
        db.commit()
    return removed
