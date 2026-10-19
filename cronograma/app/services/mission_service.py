"""Serviço de missões diárias.

Cada usuário recebe 3 missões por dia, escolhidas de forma DETERMINÍSTICA
a partir de (user_id, data) — então as mesmas missões aparecem durante
todo o dia e não se embaralham a cada refresh.

Sobre recompensa: XP é DERIVADO (calcular_xp_total soma sessões + tarefas),
não existe coluna `xp` no User. Portanto as missões NÃO armazenam XP real:
- `xp_reward` é um valor de exibição (quanto "vale" a missão);
- ao completar, concedemos COINS reais (`User.coins`) no valor de
  `xp_reward // 5` (mínimo 1), usando UPDATE atômico — mesmo padrão de
  routes/sessoes.py. A concessão é idempotente (só na transição
  completed False -> True).
"""

import random
from datetime import date

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from logger import audit, get_logger
from models.mission import DailyMission
from models.sessao import Sessoes
from models.task import Tasks

log = get_logger("cronograma.missions")

# ─── Pool de templates ────────────────────────────────────────────────────────
# kind determina como o progresso é calculado:
#   pomodoro -> nº de sessões hoje
#   minutes  -> minutos totais hoje
#   task     -> tarefas concluídas (ver NOTA em _compute_progress)
MISSION_TEMPLATES = [
    {"key": "pomodoro_1", "label": "Complete 1 pomodoro", "kind": "pomodoro", "target": 1, "xp": 15},
    {"key": "pomodoro_2", "label": "Complete 2 pomodoros", "kind": "pomodoro", "target": 2, "xp": 20},
    {"key": "pomodoro_3", "label": "Complete 3 pomodoros", "kind": "pomodoro", "target": 3, "xp": 25},
    {"key": "minutes_30", "label": "Estude 30 minutos", "kind": "minutes", "target": 30, "xp": 15},
    {"key": "minutes_60", "label": "Estude 60 minutos", "kind": "minutes", "target": 60, "xp": 20},
    {"key": "minutes_90", "label": "Estude 90 minutos", "kind": "minutes", "target": 90, "xp": 25},
    {"key": "task_1", "label": "Conclua 1 tarefa", "kind": "task", "target": 1, "xp": 15},
    {"key": "task_2", "label": "Conclua 2 tarefas", "kind": "task", "target": 2, "xp": 20},
]

_BY_KEY = {t["key"]: t for t in MISSION_TEMPLATES}

MISSIONS_PER_DAY = 3


def _today_str() -> str:
    return date.today().isoformat()


def get_or_create_daily_missions(user_id: int, db: Session) -> list[DailyMission]:
    """Garante que o usuário tem as 3 missões de hoje; cria se faltarem."""
    today = _today_str()
    existing = (
        db.query(DailyMission)
        .filter(DailyMission.user_id == user_id, DailyMission.mission_date == today)
        .order_by(DailyMission.id)
        .all()
    )
    if len(existing) >= MISSIONS_PER_DAY:
        return existing[:MISSIONS_PER_DAY]

    # Seleção determinística por (user_id, data): mesma seed => mesmas missões.
    rng = random.Random(f"{user_id}-{today}")
    pool = list(MISSION_TEMPLATES)
    rng.shuffle(pool)

    # Tenta garantir variedade de `kind` ao pegar as 3 primeiras.
    chosen = []
    seen_kinds = set()
    for tpl in pool:
        if len(chosen) >= MISSIONS_PER_DAY:
            break
        if tpl["kind"] in seen_kinds and len(chosen) < MISSIONS_PER_DAY - 1:
            continue
        chosen.append(tpl)
        seen_kinds.add(tpl["kind"])
    # Completa se a heurística de variedade deixou faltando.
    for tpl in pool:
        if len(chosen) >= MISSIONS_PER_DAY:
            break
        if tpl not in chosen:
            chosen.append(tpl)

    created: list[DailyMission] = []
    for tpl in chosen[:MISSIONS_PER_DAY]:
        mission = DailyMission(
            user_id=user_id,
            mission_date=today,
            template_key=tpl["key"],
            target=tpl["target"],
            progress=0,
            completed=False,
            xp_reward=tpl["xp"],
            created_at=f"{today}T00:00:00",
        )
        db.add(mission)
        created.append(mission)
    db.commit()
    for m in created:
        db.refresh(m)
    return created


def _compute_progress(user_id: int, db: Session) -> dict[str, int]:
    """Progresso do dia, por tipo: pomodoros, minutos, tarefas.

    NOTA sobre `task`: a tabela `tasks` NÃO guarda data de conclusão
    (não há coluna concluida_em). Sem isso, o único proxy honesto para
    "tarefas concluídas HOJE" é a contagem total de concluídas — que
    superconta em relação a "hoje". Usamos a contagem total como
    aproximação conservadora (nunca subconta) e documentamos aqui.
    """
    today = date.today()

    pomodoros = (
        db.query(func.count(Sessoes.id))
        .filter(Sessoes.user_id == user_id, Sessoes.data == today)
        .scalar()
        or 0
    )
    minutos = (
        db.query(func.sum(Sessoes.duracao_minutos))
        .filter(Sessoes.user_id == user_id, Sessoes.data == today)
        .scalar()
        or 0
    )
    tarefas = (
        db.query(func.count(Tasks.id))
        .filter(Tasks.user_id == user_id, Tasks.concluida == True)  # noqa: E712
        .scalar()
        or 0
    )
    return {"pomodoro": int(pomodoros), "minutes": int(minutos), "task": int(tarefas)}


def compute_and_update_progress(user_id: int, db: Session) -> list[DailyMission]:
    """Atualiza progresso das missões de hoje e concede coins na conclusão."""
    missions = get_or_create_daily_missions(user_id, db)
    progress = _compute_progress(user_id, db)

    newly_completed: list[DailyMission] = []
    for m in missions:
        tpl = _BY_KEY.get(m.template_key)
        if not tpl:
            continue
        value = progress.get(tpl["kind"], 0)
        m.progress = min(value, m.target)  # type: ignore[assignment]
        if not m.completed and m.progress >= m.target:
            m.completed = True  # type: ignore[assignment]
            newly_completed.append(m)

    if newly_completed:
        # Concede coins uma única vez por missão concluída.
        # `xp_reward // 5` (mín. 1) mantém a moeda alinhada à escala de XP.
        coins_granted = 0
        for m in newly_completed:
            coins_granted += max(1, (m.xp_reward or 0) // 5)
        if coins_granted:
            db.execute(
                text(
                    "UPDATE users SET coins = COALESCE(coins, 0) + :amount WHERE id = :id"
                ),
                {"amount": coins_granted, "id": user_id},
            )
        for m in newly_completed:
            audit("mission.complete", user_id=user_id, template_key=m.template_key)
        log.info(
            "Missions completed",
            extra={"user_id": user_id, "count": len(newly_completed)},
        )

    db.commit()
    for m in missions:
        db.refresh(m)
    return missions
