"""Serviços de streak e freeze."""

from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.sessao import Sessoes
from models.user import User


def calcular_streak_from_sessoes(user_id: int, db: Session) -> int:
    """Retorna streak atual do usuario (lido da tabela User)."""
    user = db.query(User).filter(User.id == user_id).first()
    return user.current_streak or 0 if user else 0


def atualizar_streak(user_id: int, db: Session) -> int:
    """Atualiza a sequencia de dias do usuario baseado em sessões reais."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return 0

    today = date.today()
    today_str = today.isoformat()

    # Get distinct session dates for this user
    session_dates = (
        db.query(func.distinct(Sessoes.data))
        .filter(Sessoes.user_id == user_id)
        .order_by(Sessoes.data.desc())
        .all()
    )
    session_dates = [s[0] for s in session_dates if s[0]]

    if not session_dates:
        # No sessions yet, reset streak
        user.current_streak = 0  # type: ignore[assignment]
        user.last_activity_date = today_str  # type: ignore[assignment]
        db.commit()
        return 0

    # Check if there's a session today or yesterday
    last_session_date = max(session_dates)  # Most recent session
    if isinstance(last_session_date, str):
        last_session_date = date.fromisoformat(last_session_date)
    days_since_last = (today - last_session_date).days

    if days_since_last == 0 and (user.current_streak or 0) == 0:
        user.current_streak = 1  # type: ignore[assignment]
    elif days_since_last == 1:
        # Studied yesterday, increment streak
        user.current_streak = (user.current_streak or 0) + 1  # type: ignore[assignment]
    else:
        if (user.streak_freezes or 0) > 0 and user.last_activity_date is not None:
            user.streak_freezes = (user.streak_freezes or 0) - 1
        else:
            user.current_streak = 0  # type: ignore[assignment]

    # Update longest streak if needed
    if (user.current_streak or 0) > (user.longest_streak or 0):
        user.longest_streak = user.current_streak

    user.last_activity_date = today_str  # type: ignore[assignment]
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
    user.streak_freezes = min((user.streak_freezes or 0) + 1, 4)  # type: ignore[assignment]
    user.last_freeze_grant_date = today  # type: ignore[assignment]
    db.commit()
    return user.streak_freezes or 0
