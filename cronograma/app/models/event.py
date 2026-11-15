"""Modelo de eventos de funil (instrumentação de aquisição/ativação)."""

from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.sql import func

from config import Base


class FunnelEvent(Base):
    """Um evento de funil (signup, guest_start, guest_upgrade, pomodoro).

    Registrado em pontos-chave do produto para calcular ativação e conversão
    sem depender de analytics externo. `created_at` usa server_default para
    funcionar igual em SQLite (CURRENT_TIMESTAMP) e Postgres (now()).
    """

    __tablename__ = "funnel_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    event = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_funnel_events_created", "created_at"),
        Index("ix_funnel_events_event", "event"),
    )