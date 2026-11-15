"""Registro de eventos de funil (signup, guest_start, guest_upgrade, pomodoro)."""

from logger import get_logger
from models.event import FunnelEvent

log = get_logger("cronograma.funnel")


def record_event(db, event: str, user_id=None) -> None:
    """Registra um evento de funil. Nunca quebra o fluxo principal.

    Instrumentação é best-effort: se a escrita falhar (tabela ausente em
    ambientes antigos, banco indisponível, etc.), só loga e segue.
    """
    try:
        db.add(FunnelEvent(user_id=user_id, event=event))
        db.commit()
    except Exception:
        log.exception(
            "funnel event failed",
            extra={"event": event, "user_id": user_id, "action": "funnel_event"},
        )