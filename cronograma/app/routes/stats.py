"""Rotas de estatísticas: heatmap de atividade e analytics avançado.

Compartilhado por duas features (heatmap + analytics). Mantenha as
funções de agregação em services/stats_service.py para não duplicar
lógica de queries entre os dois endpoints.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import get_db
from models.area import Areas
from models.sessao import Sessoes
from models.user import User
from services.auth_service import get_current_user

router = APIRouter(tags=["stats"])


# ─── Heatmap de atividade ─────────────────────────────────────────────────────


@router.get("/heatmap")
def get_heatmap(
    days: int = 365,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna minutos estudados por dia nos últimos `days` dias.

    Formato: {"days": int, "start": "YYYY-MM-DD", "end": "YYYY-MM-DD",
              "entries": [{"date": "YYYY-MM-DD", "minutes": int, "level": 0-4}]}
    `level` é a intensidade (0=sem estudo, 4=muito) para colorir o grid.
    """
    if days < 1:
        days = 1
    if days > 730:
        days = 730

    today = date.today()
    start = today - timedelta(days=days - 1)

    rows = (
        db.query(Sessoes.data, func.sum(Sessoes.duracao_minutos))
        .filter(Sessoes.user_id == user_id, Sessoes.data >= start)
        .group_by(Sessoes.data)
        .all()
    )
    by_date: dict[str, int] = {}
    for d, minutes in rows:
        if d is None:
            continue
        key = d.isoformat() if isinstance(d, (date, datetime)) else str(d)
        by_date[key] = int(minutes or 0)

    # Limites de intensidade (minutos). Ajustáveis.
    thresholds = [0, 15, 45, 90]  # <15=lvl1, <45=lvl2, <90=lvl3, >=90=lvl4

    entries = []
    cursor = start
    while cursor <= today:
        key = cursor.isoformat()
        minutes = by_date.get(key, 0)
        if minutes <= 0:
            level = 0
        elif minutes < thresholds[1]:
            level = 1
        elif minutes < thresholds[2]:
            level = 2
        elif minutes < thresholds[3]:
            level = 3
        else:
            level = 4
        entries.append({"date": key, "minutes": minutes, "level": level})
        cursor += timedelta(days=1)

    user = db.query(User).filter(User.id == user_id).first()
    return {
        "days": days,
        "start": start.isoformat(),
        "end": today.isoformat(),
        "entries": entries,
        "current_streak": (user.current_streak or 0) if user else 0,
        "longest_streak": (user.longest_streak or 0) if user else 0,
    }


# ─── Analytics avançado ───────────────────────────────────────────────────────


@router.get("/analytics")
def get_analytics(
    days: int = 30,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Analytics de estudo: tendência, melhores dias/horas, por área.

    Formato: {
      "period": {"days", "start", "end"},
      "totals": {"minutes", "sessions", "active_days", "avg_minutes_per_active_day"},
      "trend": [{"date","minutes"}] (série diária preenchida com zeros),
      "best_day": {"date","minutes"} | None,
      "by_weekday": [7 itens, 0=Segunda],
      "by_area": [{"area_id","nome","cor","minutes","sessions"}]
    }
    """
    if days < 1:
        days = 1
    if days > 365:
        days = 365

    today = date.today()
    start = today - timedelta(days=days - 1)

    rows = (
        db.query(Sessoes.data, Sessoes.duracao_minutos)
        .filter(Sessoes.user_id == user_id, Sessoes.data >= start)
        .all()
    )

    by_date: dict[str, int] = {}
    by_weekday = [0] * 7
    total_minutes = 0
    for d, minutes in rows:
        if d is None:
            continue
        m = int(minutes or 0)
        key = d.isoformat() if isinstance(d, (date, datetime)) else str(d)
        by_date[key] = by_date.get(key, 0) + m
        total_minutes += m
        if m > 0:
            wd = (d.weekday() if isinstance(d, (date, datetime)) else date.fromisoformat(key).weekday())
            by_weekday[wd] += m

    trend = []
    cursor = start
    while cursor <= today:
        key = cursor.isoformat()
        trend.append({"date": key, "minutes": by_date.get(key, 0)})
        cursor += timedelta(days=1)

    active_days = sum(1 for v in by_date.values() if v > 0)
    best_day = None
    if by_date:
        bd_key, bd_min = max(by_date.items(), key=lambda kv: kv[1])
        if bd_min > 0:
            best_day = {"date": bd_key, "minutes": bd_min}

    area_rows = (
        db.query(
            Sessoes.area_id,
            Areas.nome,
            Areas.cor,
            func.sum(Sessoes.duracao_minutos),
            func.count(Sessoes.id),
        )
        .outerjoin(Areas, Areas.id == Sessoes.area_id)
        .filter(Sessoes.user_id == user_id, Sessoes.data >= start)
        .group_by(Sessoes.area_id, Areas.nome, Areas.cor)
        .all()
    )
    by_area = [
        {
            "area_id": aid,
            "nome": nome or "Sem área",
            "cor": cor or "#6366f1",
            "minutes": int(minutes or 0),
            "sessions": int(sessions or 0),
        }
        for aid, nome, cor, minutes, sessions in area_rows
    ]
    by_area.sort(key=lambda a: a["minutes"], reverse=True)

    avg = round(total_minutes / active_days, 1) if active_days else 0

    return {
        "period": {"days": days, "start": start.isoformat(), "end": today.isoformat()},
        "totals": {
            "minutes": total_minutes,
            "sessions": len(rows),
            "active_days": active_days,
            "avg_minutes_per_active_day": avg,
        },
        "trend": trend,
        "best_day": best_day,
        "by_weekday": by_weekday,
        "by_area": by_area,
    }
