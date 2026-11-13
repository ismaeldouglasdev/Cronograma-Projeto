"""Rotas sociais: amizades, rankings, ligas, clubes, feed."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import get_db
from models.social import Club, ClubMember, FriendRequest, Friendship, League, UserLeague
from models.user import User
from services.auth_service import get_current_user
from services.social_service import (
    add_activity,
    assign_user_to_league,
    create_club,
    get_club_members,
    get_friends,
    get_friend_requests,
    get_leaderboard,
    get_sent_friend_requests,
    get_user_activity,
    get_user_clubs,
    get_user_league_info,
    get_user_rank,
    init_leagues,
    join_club,
    leave_club,
    on_xp_gained,
    process_weekly_league_reset,
    remove_friend,
    respond_friend_request,
    search_public_clubs,
    search_users,
    send_friend_request,
    update_club_weekly_stats,
    update_leaderboard,
)

router = APIRouter(tags=["social"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class FriendRequestCreate(BaseModel):
    to_user_id: int

class FriendRequestResponse(BaseModel):
    request_id: int
    accept: bool

class ClubCreate(BaseModel):
    name: str
    description: str = ""
    is_public: bool = True

class ClubJoin(BaseModel):
    invite_code: str

class ActivityResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str]
    activity_type: str
    title: str
    description: str
    metadata: Optional[dict]
    created_at: str


# ─── Amizades ─────────────────────────────────────────────────────────────────

@router.post("/friends/request")
def create_friend_request(
    data: FriendRequestCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Envia solicitação de amizade."""
    try:
        req = send_friend_request(user_id, data.to_user_id, db)
        return {"id": req.id, "status": req.status, "message": "Solicitação enviada"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/friends/request/respond")
def respond_to_friend_request(
    data: FriendRequestResponse,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aceita ou rejeita solicitação de amizade."""
    try:
        req = respond_friend_request(data.request_id, user_id, data.accept, db)
        return {"id": req.id, "status": req.status, "message": "Aceita" if data.accept else "Rejeitada"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/friends/{friend_id}")
def delete_friend(
    friend_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove amizade."""
    success = remove_friend(user_id, friend_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Amizade não encontrada")
    return {"success": True, "message": "Amizade removida"}


@router.get("/friends")
def list_friends(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista amigos do usuário."""
    friends = get_friends(user_id, db)
    return [
        {
            "id": f.id,
            "name": f.name or f.display_name or f.email,
            "avatar_url": f.avatar_url,
            "level": f.roadmap_xp,  # usando como proxy temporário
            "current_streak": f.current_streak or 0,
            "coins": f.coins or 0,
        }
        for f in friends
    ]


@router.get("/friends/requests/received")
def list_received_requests(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista solicitações recebidas."""
    requests = get_friend_requests(user_id, db)
    return [
        {
            "id": r.id,
            "from_user_id": r.from_user_id,
            "from_name": r.from_user.name or r.from_user.display_name or r.from_user.email,
            "from_avatar": r.from_user.avatar_url,
            "created_at": r.created_at,
        }
        for r in requests
    ]


@router.get("/friends/requests/sent")
def list_sent_requests(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista solicitações enviadas."""
    requests = get_sent_friend_requests(user_id, db)
    return [
        {
            "id": r.id,
            "to_user_id": r.to_user_id,
            "to_name": r.to_user.name or r.to_user.display_name or r.to_user.email,
            "to_avatar": r.to_user.avatar_url,
            "created_at": r.created_at,
        }
        for r in requests
    ]


@router.get("/friends/search")
def search_users_endpoint(
    q: str = Query(..., min_length=2),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Busca usuários para adicionar como amigo."""
    users = search_users(q, user_id, db)
    return [
        {
            "id": u.id,
            "name": u.name or u.display_name or u.email,
            "avatar_url": u.avatar_url,
            "email": u.email,
        }
        for u in users
    ]


# ─── Rankings (Leaderboards) ──────────────────────────────────────────────────

@router.get("/leaderboard")
def get_leaderboard_endpoint(
    period: str = Query("weekly", pattern="^(weekly|monthly|alltime)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna ranking do período."""
    period_key = {
        "weekly": _week_key(),
        "monthly": _month_key(),
        "alltime": "alltime",
    }[period]

    entries = get_leaderboard(period, period_key, db, limit, offset)
    user_rank = get_user_rank(user_id, period, period_key, db)

    return {
        "period": period,
        "period_key": period_key,
        "entries": [
            {
                "rank": e.rank,
                "user_id": e.user_id,
                "name": e.user.name or e.user.display_name or e.user.email,
                "avatar_url": e.user.avatar_url,
                "xp_earned": e.xp_earned,
            }
            for e in entries
        ],
        "user_rank": {
            "rank": user_rank.rank,
            "xp_earned": user_rank.xp_earned,
        } if user_rank else None,
    }


@router.post("/leaderboard/update")
def update_leaderboard_endpoint(
    period: str = Query("weekly", pattern="^(weekly|monthly|alltime)$"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Força atualização do ranking (admin ou manual)."""
    period_key = {
        "weekly": _week_key(),
        "monthly": _month_key(),
        "alltime": "alltime",
    }[period]

    entries = update_leaderboard(period, period_key, db)
    return {"updated": len(entries), "period": period, "period_key": period_key}


# ─── Ligas ────────────────────────────────────────────────────────────────────

@router.get("/league/me")
def get_my_league(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna info da liga do usuário."""
    init_leagues(db)
    return get_user_league_info(user_id, db)


@router.get("/league/standings")
def get_league_standings_endpoint(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna classificação completa da liga do usuário."""
    init_leagues(db)
    info = get_user_league_info(user_id, db)
    return info["standings"]


@router.post("/league/process-reset")
def process_league_reset(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Processa reset semanal das ligas (admin)."""
    result = process_weekly_league_reset(db)
    return result


# ─── Clubes ───────────────────────────────────────────────────────────────────

@router.post("/clubs")
def create_club_endpoint(
    data: ClubCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria um novo clube."""
    club = create_club(data.name, data.description, user_id, data.is_public, db)
    return {
        "id": club.id,
        "name": club.name,
        "invite_code": club.invite_code,
        "is_public": club.is_public,
    }


@router.post("/clubs/join")
def join_club_endpoint(
    data: ClubJoin,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Entra em um clube via código de convite."""
    try:
        member = join_club(data.invite_code, user_id, db)
        return {"success": True, "club_id": member.club_id, "message": "Entrou no clube"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/clubs/{club_id}/leave")
def leave_club_endpoint(
    club_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sai de um clube."""
    try:
        success = leave_club(club_id, user_id, db)
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clubs/me")
def list_my_clubs(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista clubes do usuário."""
    clubs = get_user_clubs(user_id, db)
    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "invite_code": c.invite_code,
            "is_public": c.is_public,
            "member_count": len(c.members),
            "owner_id": c.owner_id,
        }
        for c in clubs
    ]


@router.get("/clubs/{club_id}/members")
def list_club_members(
    club_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista membros de um clube."""
    # Verificar se é membro
    membership = db.query(ClubMember).filter(
        ClubMember.club_id == club_id,
        ClubMember.user_id == user_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Não é membro deste clube")

    members = get_club_members(club_id, db)
    return [
        {
            "user_id": m.user_id,
            "name": m.user.name or m.user.display_name or m.user.email,
            "avatar_url": m.user.avatar_url,
            "role": m.role,
            "xp_contributed": m.xp_contributed or 0,
            "joined_at": m.joined_at,
        }
        for m in members
    ]


@router.get("/clubs/search")
def search_clubs_endpoint(
    q: str = Query(..., min_length=2),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Busca clubes públicos."""
    clubs = search_public_clubs(q, db)
    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "member_count": len(c.members),
            "is_public": c.is_public,
        }
        for c in clubs
    ]


@router.delete("/clubs/{club_id}")
def delete_club_endpoint(
    club_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deleta um clube (apenas owner)."""
    club = db.query(Club).filter(Club.id == club_id, Club.owner_id == user_id).first()
    if not club:
        raise HTTPException(status_code=403, detail="Apenas o dono pode excluir o clube")
    db.delete(club)
    db.commit()
    return {"success": True, "message": "Clube excluído"}


@router.delete("/friends/requests/sent/{request_id}")
def cancel_sent_request(
    request_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancela uma solicitação de amizade enviada."""
    req = db.query(FriendRequest).filter(
        FriendRequest.id == request_id,
        FriendRequest.from_user_id == user_id,
        FriendRequest.status == "pending",
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    db.delete(req)
    db.commit()
    return {"success": True, "message": "Solicitação cancelada"}


# ─── Feed de Atividades ───────────────────────────────────────────────────────

@router.get("/activity/friends")
def get_friends_activity_endpoint(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna atividades dos amigos."""
    activities = get_friends_activity(user_id, db, limit, offset)
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "user_name": a.user.name or a.user.display_name or a.user.email,
            "user_avatar": a.user.avatar_url,
            "activity_type": a.activity_type,
            "title": a.title,
            "description": a.description,
            "metadata": a.metadata_json,
            "created_at": a.created_at,
        }
        for a in activities
    ]


@router.get("/activity/me")
def get_my_activity_endpoint(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna atividades do próprio usuário."""
    activities = get_user_activity(user_id, db, limit, offset)
    return [
        {
            "id": a.id,
            "activity_type": a.activity_type,
            "title": a.title,
            "description": a.description,
            "metadata": a.metadata_json,
            "created_at": a.created_at,
        }
        for a in activities
    ]


# ─── XP Hook (interno) ────────────────────────────────────────────────────────

@router.post("/internal/xp-gained")
def xp_gained_hook(
    xp_amount: int,
    source: str,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hook chamado quando usuário ganha XP (interno)."""
    init_leagues(db)
    result = on_xp_gained(user_id, xp_amount, source, db)
    return result


# Helpers
def _week_key() -> str:
    from datetime import date
    return date.today().strftime("%Y-W%U")


def _month_key() -> str:
    from datetime import date
    return date.today().strftime("%Y-%m")