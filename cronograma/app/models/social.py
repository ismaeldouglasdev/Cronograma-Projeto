"""Modelos sociais: amizades, rankings, ligas, clubes, feed de atividades."""

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from config import Base


class Friendship(Base):
    """Amizade mútua entre dois usuários (bidirecional)."""
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(String(40), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_friendship_pair"),
        Index("ix_friendship_user", "user_id"),
        Index("ix_friendship_friend", "friend_id"),
    )

    user = relationship("User", foreign_keys=[user_id], backref="friendships")
    friend = relationship("User", foreign_keys=[friend_id], backref="friend_of")


class FriendRequest(Base):
    """Solicitação de amizade pendente."""
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, accepted, rejected
    created_at = Column(String(40), nullable=False)
    responded_at = Column(String(40), nullable=True)

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_friend_request_pair"),
        Index("ix_friend_request_to", "to_user_id"),
        Index("ix_friend_request_from", "from_user_id"),
    )

    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])


class LeaderboardEntry(Base):
    """Entrada de ranking (snapshot semanal/mensal/total)."""
    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    period_type = Column(String(20), nullable=False)  # weekly, monthly, alltime
    period_key = Column(String(20), nullable=False)  # ex: "2026-W45", "2026-11", "alltime"
    xp_earned = Column(Integer, default=0, nullable=False)
    rank = Column(Integer, nullable=True)
    previous_rank = Column(Integer, nullable=True)
    created_at = Column(String(40), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "period_type", "period_key", name="uq_leaderboard_user_period"),
        Index("ix_leaderboard_period", "period_type", "period_key"),
        Index("ix_leaderboard_rank", "period_type", "period_key", "rank"),
    )

    user = relationship("User", backref="leaderboard_entries")


class League(Base):
    """Liga semanal (Bronze, Silver, Gold, Platinum, Diamond, Obsidian)."""
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False)  # Bronze, Silver, Gold, Platinum, Diamond, Obsidian
    tier = Column(Integer, nullable=False)  # 1=Bronze, 2=Silver, 3=Gold, 4=Platinum, 5=Diamond, 6=Obsidian
    min_xp = Column(Integer, default=0, nullable=False)  # XP mínimo para entrar
    max_users = Column(Integer, default=30, nullable=False)  # usuários por liga
    promotion_spots = Column(Integer, default=10, nullable=False)  # top N promovidos
    demotion_spots = Column(Integer, default=5, nullable=False)  # bottom N rebaixados
    created_at = Column(String(40), nullable=False)


class UserLeague(Base):
    """Participação do usuário na liga da semana atual."""
    __tablename__ = "user_leagues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    week_key = Column(String(20), nullable=False)  # ex: "2026-W45"
    xp_this_week = Column(Integer, default=0, nullable=False)
    rank_in_league = Column(Integer, nullable=True)
    promoted = Column(Boolean, default=False, nullable=False)
    demoted = Column(Boolean, default=False, nullable=False)
    created_at = Column(String(40), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "week_key", name="uq_user_league_week"),
        Index("ix_user_league_week", "week_key"),
        Index("ix_user_league_rank", "week_key", "rank_in_league"),
    )

    user = relationship("User", backref="user_leagues")
    league = relationship("League", backref="participants")


class Club(Base):
    """Clube/Time de estudo (grupo de usuários)."""
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    invite_code = Column(String(12), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    max_members = Column(Integer, default=50, nullable=False)
    created_at = Column(String(40), nullable=False)

    __table_args__ = (
        Index("ix_club_owner", "owner_id"),
        Index("ix_club_invite", "invite_code"),
    )

    owner = relationship("User", backref="owned_clubs")
    members = relationship("ClubMember", backref="club", cascade="all, delete-orphan")


class ClubMember(Base):
    """Membro de um clube."""
    __tablename__ = "club_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member", nullable=False)  # owner, admin, member
    joined_at = Column(String(40), nullable=False)
    xp_contributed = Column(Integer, default=0, nullable=False)  # XP contribuído esta semana
    last_contribution_at = Column(String(40), nullable=True)

    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_club_member"),
        Index("ix_club_member_user", "user_id"),
    )

    user = relationship("User", backref="club_memberships")


class ClubWeeklyStats(Base):
    """Estatísticas semanais do clube (para competições entre clubes)."""
    __tablename__ = "club_weekly_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    week_key = Column(String(20), nullable=False)  # ex: "2026-W45"
    total_xp = Column(Integer, default=0, nullable=False)
    active_members = Column(Integer, default=0, nullable=False)
    rank = Column(Integer, nullable=True)
    created_at = Column(String(40), nullable=False)

    __table_args__ = (
        UniqueConstraint("club_id", "week_key", name="uq_club_weekly_stats"),
        Index("ix_club_weekly_rank", "week_key", "rank"),
    )

    club = relationship("Club", backref="weekly_stats")


class ActivityFeed(Base):
    """Feed de atividades sociais (conquistas, marcos, marcos de amigos)."""
    __tablename__ = "activity_feed"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(40), nullable=False)  # achievement_unlocked, level_up, streak_milestone, mission_completed, league_promoted, club_joined
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON com dados extras (achievement_id, level, streak_days, etc.)
    is_public = Column(Boolean, default=True, nullable=False)
    created_at = Column(String(40), nullable=False)

    __table_args__ = (
        Index("ix_activity_user", "user_id"),
        Index("ix_activity_created", "created_at"),
        Index("ix_activity_type", "activity_type"),
    )

    user = relationship("User", backref="activities")