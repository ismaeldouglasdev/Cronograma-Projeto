"""Modelo de missões diárias."""

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String

from config import Base


class DailyMission(Base):
    """Uma missão do dia para um usuário.

    `mission_date` é String(10) no formato ISO 'YYYY-MM-DD', seguindo o
    padrão de datas já usado em `User.last_activity_date`. A escolha de
    String (em vez de Date) evita divergência de tipo entre SQLite e
    Postgres e casa com o restante do schema de gamificação.
    """

    __tablename__ = "daily_missions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mission_date = Column(String(10), nullable=False)
    template_key = Column(String(40), nullable=False)
    target = Column(Integer, nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    xp_reward = Column(Integer, default=0, nullable=False)
    created_at = Column(String(40), nullable=True)

    __table_args__ = (
        Index("ix_daily_missions_user_date", "user_id", "mission_date"),
    )
