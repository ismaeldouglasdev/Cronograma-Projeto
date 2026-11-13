"""Serviços sociais: amizades, rankings, ligas, clubes, feed de atividades."""

import json
import random
import string
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import and_, case, desc, func, or_, text
from sqlalchemy.orm import Session

from models.achievement import UserAchievement
from models.mission import DailyMission
from models.sessao import Sessoes
from models.social import (
    ActivityFeed,
    Club,
    ClubMember,
    ClubWeeklyStats,
    FriendRequest,
    Friendship,
    LeaderboardEntry,
    League,
    UserLeague,
)
from models.task import Tasks
from models.user import User


# ─── Constantes ────────────────────────────────────────────────────────────────

LEAGUE_TIERS = [
    {"name": "Bronze", "tier": 1, "min_xp": 0, "max_users": 30, "promotion": 15, "demotion": 0},
    {"name": "Prata", "tier": 2, "min_xp": 100, "max_users": 30, "promotion": 10, "demotion": 5},
    {"name": "Ouro", "tier": 3, "min_xp": 500, "max_users": 30, "promotion": 10, "demotion": 5},
    {"name": "Platina", "tier": 4, "min_xp": 1500, "max_users": 30, "promotion": 5, "demotion": 10},
    {"name": "Diamante", "tier": 5, "min_xp": 3000, "max_users": 30, "promotion": 3, "demotion": 10},
    {"name": "Obsidiana", "tier": 6, "min_xp": 6000, "max_users": 15, "promotion": 0, "demotion": 5},
]

WEEK_KEY_FMT = "%Y-W%U"  # ISO week


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _week_key(dt: Optional[date] = None) -> str:
    d = dt or date.today()
    return d.strftime(WEEK_KEY_FMT)


def _month_key(dt: Optional[date] = None) -> str:
    d = dt or date.today()
    return d.strftime("%Y-%m")


def _generate_invite_code() -> str:
    """Gera código de convite único (8 chars alfanuméricos)."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


# ─── Inicialização de Ligas ────────────────────────────────────────────────────

def init_leagues(db: Session) -> None:
    """Cria as ligas padrão se não existirem."""
    if db.query(League).count() > 0:
        return
    for t in LEAGUE_TIERS:
        league = League(
            name=t["name"],
            tier=t["tier"],
            min_xp=t["min_xp"],
            max_users=t["max_users"],
            promotion_spots=t["promotion"],
            demotion_spots=t["demotion"],
            created_at=_now_iso(),
        )
        db.add(league)
    db.commit()


# ─── Amizades ──────────────────────────────────────────────────────────────────

def send_friend_request(from_user_id: int, to_user_id: int, db: Session) -> FriendRequest:
    """Envia solicitação de amizade."""
    if from_user_id == to_user_id:
        raise ValueError("Não pode adicionar a si mesmo")

    # Verificar se já são amigos
    existing = db.query(Friendship).filter(
        or_(
            and_(Friendship.user_id == from_user_id, Friendship.friend_id == to_user_id),
            and_(Friendship.user_id == to_user_id, Friendship.friend_id == from_user_id),
        )
    ).first()
    if existing:
        raise ValueError("Já são amigos")

    # Verificar solicitação pendente
    existing_req = db.query(FriendRequest).filter(
        or_(
            and_(FriendRequest.from_user_id == from_user_id, FriendRequest.to_user_id == to_user_id),
            and_(FriendRequest.from_user_id == to_user_id, FriendRequest.to_user_id == from_user_id),
        ),
        FriendRequest.status == "pending",
    ).first()
    if existing_req:
        raise ValueError("Solicitação já pendente")

    req = FriendRequest(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        status="pending",
        created_at=_now_iso(),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def respond_friend_request(request_id: int, user_id: int, accept: bool, db: Session) -> FriendRequest:
    """Responde a uma solicitação de amizade."""
    req = db.query(FriendRequest).filter(
        FriendRequest.id == request_id,
        FriendRequest.to_user_id == user_id,
        FriendRequest.status == "pending",
    ).first()
    if not req:
        raise ValueError("Solicitação não encontrada")

    if accept:
        req.status = "accepted"
        req.responded_at = _now_iso()
        # Criar amizade bidirecional
        f1 = Friendship(user_id=req.from_user_id, friend_id=req.to_user_id, created_at=_now_iso())
        f2 = Friendship(user_id=req.to_user_id, friend_id=req.from_user_id, created_at=_now_iso())
        db.add_all([f1, f2])
        # Feed: amizade aceita
        add_activity(req.from_user_id, "friend_accepted", f"Você e {req.to_user.full_name or 'um usuário'} agora são amigos!", db)
        add_activity(req.to_user_id, "friend_accepted", f"Você e {req.from_user.full_name or 'um usuário'} agora são amigos!", db)
    else:
        req.status = "rejected"
        req.responded_at = _now_iso()

    db.commit()
    db.refresh(req)
    return req


def remove_friend(user_id: int, friend_id: int, db: Session) -> bool:
    """Remove amizade (bidirecional)."""
    deleted = db.query(Friendship).filter(
        or_(
            and_(Friendship.user_id == user_id, Friendship.friend_id == friend_id),
            and_(Friendship.user_id == friend_id, Friendship.friend_id == user_id),
        )
    ).delete(synchronize_session=False)
    if deleted:
        db.commit()
    return deleted > 0


def get_friends(user_id: int, db: Session) -> list[User]:
    """Retorna lista de amigos do usuário."""
    friendships = db.query(Friendship).filter(Friendship.user_id == user_id).all()
    friend_ids = [f.friend_id for f in friendships]
    if not friend_ids:
        return []
    return db.query(User).filter(User.id.in_(friend_ids)).all()


def get_friend_requests(user_id: int, db: Session) -> list[FriendRequest]:
    """Retorna solicitações de amizade recebidas pendentes."""
    return db.query(FriendRequest).filter(
        FriendRequest.to_user_id == user_id,
        FriendRequest.status == "pending",
    ).order_by(FriendRequest.created_at.desc()).all()


def get_sent_friend_requests(user_id: int, db: Session) -> list[FriendRequest]:
    """Retorna solicitações de amizade enviadas pendentes."""
    return db.query(FriendRequest).filter(
        FriendRequest.from_user_id == user_id,
        FriendRequest.status == "pending",
    ).order_by(FriendRequest.created_at.desc()).all()


def search_users(query: str, exclude_user_id: int, db: Session, limit: int = 20) -> list[User]:
    """Busca usuários por nome/email para adicionar como amigo."""
    return db.query(User).filter(
        User.id != exclude_user_id,
        or_(
            User.name.ilike(f"%{query}%"),
            User.display_name.ilike(f"%{query}%"),
            User.email.ilike(f"%{query}%"),
        )
    ).limit(limit).all()


# ─── Rankings (Leaderboards) ───────────────────────────────────────────────────

def _calc_user_xp(user_id: int, db: Session, period_type: str, period_key: str) -> int:
    """Calcula XP ganho no período."""
    if period_type == "alltime":
        # Usar a função existente
        from services.gamification_service import calcular_xp_total
        return calcular_xp_total(user_id, db)

    today = date.today()
    if period_type == "weekly":
        # Última semana (segunda a domingo)
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
    elif period_type == "monthly":
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1) - timedelta(days=1)
    else:
        return 0

    start_str = start.isoformat()
    end_str = end.isoformat()

    # XP por sessões no período (10 XP por 30 min)
    sessao_xp = db.query(func.sum(Sessoes.duracao_minutos)).filter(
        Sessoes.user_id == user_id,
        Sessoes.data >= start_str,
        Sessoes.data <= end_str,
    ).scalar() or 0
    sessao_xp = (int(sessao_xp) * 10) // 30

    # XP por tarefas concluídas no período (5 XP por tarefa)
    try:
        task_xp = db.query(func.count(Tasks.id)).filter(
            Tasks.user_id == user_id,
            Tasks.concluida == True,  # noqa: E712
            Tasks.concluida_em != None,  # noqa: E711
            func.date(Tasks.concluida_em) >= start_str,
            func.date(Tasks.concluida_em) <= end_str,
        ).scalar() or 0
    except Exception:
        task_xp = db.query(func.count(Tasks.id)).filter(
            Tasks.user_id == user_id,
            Tasks.concluida == True,  # noqa: E712
        ).scalar() or 0
    task_xp = int(task_xp) * 5

    return sessao_xp + task_xp


def update_leaderboard(period_type: str, period_key: str, db: Session) -> list[LeaderboardEntry]:
    """Atualiza ranking para um período (chamado por job/cron)."""
    # Buscar todos usuários ativos (não guest)
    users = db.query(User).filter(User.is_guest != True).all()  # noqa: E712

    entries = []
    for u in users:
        xp = _calc_user_xp(u.id, db, period_type, period_key)
        entry = LeaderboardEntry(
            user_id=u.id,
            period_type=period_type,
            period_key=period_key,
            xp_earned=xp,
            created_at=_now_iso(),
        )
        entries.append(entry)

    # Ordenar por XP decrescente
    entries.sort(key=lambda e: e.xp_earned, reverse=True)

    # Atribuir ranks
    for i, entry in enumerate(entries):
        entry.rank = i + 1

    # Upsert: deletar antigos e inserir novos
    db.query(LeaderboardEntry).filter(
        LeaderboardEntry.period_type == period_type,
        LeaderboardEntry.period_key == period_key,
    ).delete(synchronize_session=False)

    db.add_all(entries)
    db.commit()
    return entries


def get_leaderboard(period_type: str, period_key: str, db: Session, limit: int = 100, offset: int = 0) -> list[LeaderboardEntry]:
    """Retorna ranking para um período."""
    return db.query(LeaderboardEntry).filter(
        LeaderboardEntry.period_type == period_type,
        LeaderboardEntry.period_key == period_key,
    ).order_by(LeaderboardEntry.rank).offset(offset).limit(limit).all()


def get_user_rank(user_id: int, period_type: str, period_key: str, db: Session) -> Optional[LeaderboardEntry]:
    """Retorna posição do usuário no ranking."""
    return db.query(LeaderboardEntry).filter(
        LeaderboardEntry.user_id == user_id,
        LeaderboardEntry.period_type == period_type,
        LeaderboardEntry.period_key == period_key,
    ).first()


# ─── Ligas (Leagues) ───────────────────────────────────────────────────────────

def get_current_league_week() -> str:
    return _week_key()


def assign_user_to_league(user_id: int, db: Session) -> UserLeague:
    """Atribui usuário a uma liga para a semana atual (baseado no XP total)."""
    week = get_current_league_week()

    # Verificar se já tem liga esta semana
    existing = db.query(UserLeague).filter(
        UserLeague.user_id == user_id,
        UserLeague.week_key == week,
    ).first()
    if existing:
        return existing

    # Calcular XP total do usuário
    from services.gamification_service import calcular_xp_total
    xp_total = calcular_xp_total(user_id, db)

    # Encontrar liga apropriada (maior tier onde min_xp <= xp_total)
    league = db.query(League).filter(League.min_xp <= xp_total).order_by(League.tier.desc()).first()
    if not league:
        league = db.query(League).order_by(League.tier.asc()).first()

    # Verificar se a liga tem vaga
    current_count = db.query(UserLeague).filter(
        UserLeague.league_id == league.id,
        UserLeague.week_key == week,
    ).count()

    # Se liga cheia, tentar a de baixo
    while current_count >= league.max_users and league.tier > 1:
        league = db.query(League).filter(League.tier == league.tier - 1).first()
        current_count = db.query(UserLeague).filter(
            UserLeague.league_id == league.id,
            UserLeague.week_key == week,
        ).count()

    user_league = UserLeague(
        user_id=user_id,
        league_id=league.id,
        week_key=week,
        xp_this_week=0,
        created_at=_now_iso(),
    )
    db.add(user_league)
    db.commit()
    db.refresh(user_league)
    return user_league


def update_league_progress(user_id: int, xp_gained: int, db: Session) -> UserLeague:
    """Atualiza XP da semana na liga e recalcula ranks."""
    week = get_current_league_week()
    ul = db.query(UserLeague).filter(
        UserLeague.user_id == user_id,
        UserLeague.week_key == week,
    ).first()
    if not ul:
        ul = assign_user_to_league(user_id, db)

    ul.xp_this_week = (ul.xp_this_week or 0) + xp_gained
    db.commit()

    # Recalcular ranks na liga
    participants = db.query(UserLeague).filter(
        UserLeague.league_id == ul.league_id,
        UserLeague.week_key == week,
    ).order_by(UserLeague.xp_this_week.desc()).all()

    for i, p in enumerate(participants):
        p.rank_in_league = i + 1
    db.commit()
    db.refresh(ul)
    return ul


def get_league_standings(league_id: int, week_key: str, db: Session) -> list[UserLeague]:
    """Retorna classificação da liga."""
    return db.query(UserLeague).filter(
        UserLeague.league_id == league_id,
        UserLeague.week_key == week_key,
    ).order_by(UserLeague.rank_in_league).all()


def get_user_league_info(user_id: int, db: Session) -> dict:
    """Retorna info completa da liga do usuário."""
    week = get_current_league_week()
    ul = db.query(UserLeague).filter(
        UserLeague.user_id == user_id,
        UserLeague.week_key == week,
    ).first()
    if not ul:
        ul = assign_user_to_league(user_id, db)

    league = db.query(League).filter(League.id == ul.league_id).first()
    standings = get_league_standings(ul.league_id, week, db)

    return {
        "league": {
            "id": league.id,
            "name": league.name,
            "tier": league.tier,
            "promotion_spots": league.promotion_spots,
            "demotion_spots": league.demotion_spots,
        },
        "user": {
            "xp_this_week": ul.xp_this_week,
            "rank": ul.rank_in_league,
            "promoted": ul.promoted,
            "demoted": ul.demoted,
        },
        "standings": [
            {
                "user_id": s.user_id,
                "name": s.user.name or s.user.display_name or s.user.email,
                "avatar_url": s.user.avatar_url,
                "xp_this_week": s.xp_this_week,
                "rank": s.rank_in_league,
            }
            for s in standings
        ],
    }


def process_weekly_league_reset(db: Session) -> dict:
    """Processa reset semanal das ligas (promoção/rebaixamento). Chamado por cron na segunda-feira."""
    last_week = _week_key(date.today() - timedelta(days=1))  # semana anterior
    this_week = get_current_league_week()

    results = {"promoted": 0, "demoted": 0, "leagues_processed": 0}

    # Para cada liga da semana passada
    leagues = db.query(League).all()
    for league in leagues:
        # Buscar participantes da semana passada ordenados por rank
        participants = db.query(UserLeague).filter(
            UserLeague.league_id == league.id,
            UserLeague.week_key == last_week,
        ).order_by(UserLeague.rank_in_league).all()

        if not participants:
            continue

        results["leagues_processed"] += 1

        # Promover top N
        for i, p in enumerate(participants):
            if i < league.promotion_spots and league.tier < 6:
                # Encontrar liga superior
                next_league = db.query(League).filter(League.tier == league.tier + 1).first()
                if next_league:
                    # Criar entrada na nova liga para esta semana
                    new_ul = UserLeague(
                        user_id=p.user_id,
                        league_id=next_league.id,
                        week_key=this_week,
                        xp_this_week=0,
                        created_at=_now_iso(),
                    )
                    db.add(new_ul)
                    p.promoted = True
                    results["promoted"] += 1
                    # Feed
                    add_activity(p.user_id, "league_promoted", f"Promovido para {next_league.name}!", {"from_tier": league.tier, "to_tier": next_league.tier}, db)

        # Rebaixar bottom N
        for i, p in enumerate(reversed(participants)):
            if i < league.demotion_spots and league.tier > 1:
                prev_league = db.query(League).filter(League.tier == league.tier - 1).first()
                if prev_league:
                    new_ul = UserLeague(
                        user_id=p.user_id,
                        league_id=prev_league.id,
                        week_key=this_week,
                        xp_this_week=0,
                        created_at=_now_iso(),
                    )
                    db.add(new_ul)
                    p.demoted = True
                    results["demoted"] += 1
                    add_activity(p.user_id, "league_demoted", f"Rebaixado para {prev_league.name}.", {"from_tier": league.tier, "to_tier": prev_league.tier}, db)

        # Manter os demais na mesma liga
        for i, p in enumerate(participants):
            if not p.promoted and not p.demoted:
                new_ul = UserLeague(
                    user_id=p.user_id,
                    league_id=league.id,
                    week_key=this_week,
                    xp_this_week=0,
                    created_at=_now_iso(),
                )
                db.add(new_ul)

    db.commit()
    return results


# ─── Clubes ────────────────────────────────────────────────────────────────────

def create_club(name: str, description: str, owner_id: int, is_public: bool, db: Session) -> Club:
    """Cria um novo clube."""
    invite_code = _generate_invite_code()
    # Garantir código único
    while db.query(Club).filter(Club.invite_code == invite_code).first():
        invite_code = _generate_invite_code()

    club = Club(
        name=name,
        description=description,
        invite_code=invite_code,
        owner_id=owner_id,
        is_public=is_public,
        created_at=_now_iso(),
    )
    db.add(club)
    db.flush()

    # Adicionar owner como membro
    member = ClubMember(
        club_id=club.id,
        user_id=owner_id,
        role="owner",
        joined_at=_now_iso(),
    )
    db.add(member)
    db.commit()
    db.refresh(club)
    return club


def join_club(invite_code: str, user_id: int, db: Session) -> ClubMember:
    """Entra em um clube via código de convite."""
    club = db.query(Club).filter(Club.invite_code == invite_code.upper()).first()
    if not club:
        raise ValueError("Código de convite inválido")

    # Verificar se já é membro
    existing = db.query(ClubMember).filter(
        ClubMember.club_id == club.id,
        ClubMember.user_id == user_id,
    ).first()
    if existing:
        raise ValueError("Já é membro deste clube")

    # Verificar limite
    member_count = db.query(ClubMember).filter(ClubMember.club_id == club.id).count()
    if member_count >= club.max_members:
        raise ValueError("Clube cheio")

    member = ClubMember(
        club_id=club.id,
        user_id=user_id,
        role="member",
        joined_at=_now_iso(),
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    add_activity(user_id, "club_joined", f"Entrou no clube {club.name}", {"club_id": club.id}, db)
    return member


def leave_club(club_id: int, user_id: int, db: Session) -> bool:
    """Sai de um clube."""
    member = db.query(ClubMember).filter(
        ClubMember.club_id == club_id,
        ClubMember.user_id == user_id,
    ).first()
    if not member:
        return False

    if member.role == "owner":
        # Owner não pode sair, deve transferir ou deletar
        raise ValueError("Owner não pode sair. Transfira a propriedade ou delete o clube.")

    db.delete(member)
    db.commit()
    return True


def get_user_clubs(user_id: int, db: Session) -> list[Club]:
    """Retorna clubes do usuário."""
    memberships = db.query(ClubMember).filter(ClubMember.user_id == user_id).all()
    club_ids = [m.club_id for m in memberships]
    if not club_ids:
        return []
    return db.query(Club).filter(Club.id.in_(club_ids)).all()


def get_club_members(club_id: int, db: Session) -> list[ClubMember]:
    """Retorna membros de um clube."""
    return db.query(ClubMember).filter(ClubMember.club_id == club_id).all()


def search_public_clubs(query: str, db: Session, limit: int = 20) -> list[Club]:
    """Busca clubes públicos."""
    return db.query(Club).filter(
        Club.is_public == True,  # noqa: E712
        Club.name.ilike(f"%{query}%"),
    ).limit(limit).all()


def update_club_weekly_xp(user_id: int, xp_gained: int, db: Session) -> None:
    """Atualiza XP contribuído para o clube esta semana."""
    week = get_current_league_week()
    memberships = db.query(ClubMember).filter(ClubMember.user_id == user_id).all()
    for m in memberships:
        m.xp_contributed = (m.xp_contributed or 0) + xp_gained
        m.last_contribution_at = _now_iso()
    db.commit()


def update_club_weekly_stats(db: Session) -> None:
    """Atualiza stats semanais dos clubes (chamado por cron)."""
    week = get_current_league_week()

    # Deletar stats antigos desta semana
    db.query(ClubWeeklyStats).filter(ClubWeeklyStats.week_key == week).delete(synchronize_session=False)

    # Calcular por clube
    clubs = db.query(Club).all()
    stats_list = []
    for club in clubs:
        members = db.query(ClubMember).filter(ClubMember.club_id == club.id).all()
        total_xp = sum(m.xp_contributed or 0 for m in members)
        active = sum(1 for m in members if (m.xp_contributed or 0) > 0)

        stats = ClubWeeklyStats(
            club_id=club.id,
            week_key=week,
            total_xp=total_xp,
            active_members=active,
            created_at=_now_iso(),
        )
        stats_list.append(stats)

    # Ordenar e atribuir ranks
    stats_list.sort(key=lambda s: s.total_xp, reverse=True)
    for i, s in enumerate(stats_list):
        s.rank = i + 1

    db.add_all(stats_list)
    db.commit()


# ─── Feed de Atividades ────────────────────────────────────────────────────────

ACTIVITY_TYPES = {
    "achievement_unlocked": "Conquista desbloqueada",
    "level_up": "Subiu de nível",
    "streak_milestone": "Marco de streak",
    "mission_completed": "Missão completada",
    "league_promoted": "Promovido de liga",
    "league_demoted": "Rebaixado de liga",
    "club_joined": "Entrou no clube",
    "friend_accepted": "Nova amizade",
}

def add_activity(
    user_id: int,
    activity_type: str,
    title: str,
    metadata: Optional[dict] = None,
    db: Session = None,
    is_public: bool = True,
) -> ActivityFeed:
    """Adiciona atividade ao feed."""
    if db is None:
        raise ValueError("db session required")

    activity = ActivityFeed(
        user_id=user_id,
        activity_type=activity_type,
        title=title,
        description=ACTIVITY_TYPES.get(activity_type, ""),
        metadata_json=json.dumps(metadata) if metadata else None,
        is_public=is_public,
        created_at=_now_iso(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_friends_activity(user_id: int, db: Session, limit: int = 50, offset: int = 0) -> list[ActivityFeed]:
    """Retorna atividades dos amigos."""
    # Buscar amigos
    friendships = db.query(Friendship).filter(Friendship.user_id == user_id).all()
    friend_ids = [f.friend_id for f in friendships]
    if not friend_ids:
        return []

    # Incluir próprio usuário
    friend_ids.append(user_id)

    return db.query(ActivityFeed).filter(
        ActivityFeed.user_id.in_(friend_ids),
        ActivityFeed.is_public == True,  # noqa: E712
    ).order_by(ActivityFeed.created_at.desc()).offset(offset).limit(limit).all()


def get_user_activity(user_id: int, db: Session, limit: int = 50, offset: int = 0) -> list[ActivityFeed]:
    """Retorna atividades do próprio usuário."""
    return db.query(ActivityFeed).filter(
        ActivityFeed.user_id == user_id,
    ).order_by(ActivityFeed.created_at.desc()).offset(offset).limit(limit).all()


# ─── Integração com XP (chamado quando usuário ganha XP) ────────────────────────

def on_xp_gained(user_id: int, xp_amount: int, source: str, db: Session) -> dict:
    """Hook chamado quando usuário ganha XP (sessão, tarefa, missão)."""
    results = {}

    # Atualizar progresso na liga
    ul = update_league_progress(user_id, xp_amount, db)
    results["league"] = {
        "xp_this_week": ul.xp_this_week,
        "rank": ul.rank_in_league,
    }

    # Atualizar contribuição do clube
    update_club_weekly_xp(user_id, xp_amount, db)

    # Verificar level up
    from services.gamification_service import calcular_xp_total, calcular_level
    xp_total = calcular_xp_total(user_id, db)
    level = calcular_level(xp_total)
    user = db.query(User).filter(User.id == user_id).first()
    if user and (user.roadmap_xp or 0) < xp_total:  # roadmap_xp usado como cache do level anterior
        old_level = calcular_level((user.roadmap_xp or 0))
        if level > old_level:
            user.roadmap_xp = xp_total  # cache
            add_activity(user_id, "level_up", f"Alcançou o nível {level}!", {"level": level, "xp_total": xp_total}, db)
            results["level_up"] = {"new_level": level}

    # Verificar streak milestones
    if user and user.current_streak in [7, 14, 30, 60, 100, 365]:
        add_activity(user_id, "streak_milestone", f"{user.current_streak} dias de streak! 🔥", {"streak": user.current_streak}, db)
        results["streak_milestone"] = {"streak": user.current_streak}

    db.commit()
    return results