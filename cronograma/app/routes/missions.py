"""Rotas de missões diárias."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config import get_db
from models.user import User
from services.auth_service import get_current_user
from services.mission_service import (
    MISSIONS_PER_DAY,
    _BY_KEY,
    compute_and_update_progress,
)

router = APIRouter(tags=["missions"])


@router.get("/missions/today")
def missions_today(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retorna as missões de hoje (progresso já computado) + resumo."""
    missions = compute_and_update_progress(user_id, db)

    items = []
    for m in missions:
        tpl = _BY_KEY.get(m.template_key, {})
        items.append(
            {
                "key": m.template_key,
                "label": tpl.get("label", m.template_key),
                "kind": tpl.get("kind"),
                "target": m.target,
                "progress": m.progress,
                "completed": bool(m.completed),
                "xp_reward": m.xp_reward,
            }
        )

    completed_count = sum(1 for i in items if i["completed"])
    user = db.query(User).filter(User.id == user_id).first()
    return {
        "date": missions[0].mission_date if missions else None,
        "missions": items,
        "completed_count": completed_count,
        "total": len(items),
        "all_completed": completed_count >= MISSIONS_PER_DAY and len(items) > 0,
        "coins": (user.coins or 0) if user else 0,
    }
