from sqlalchemy import Boolean, Column, Integer, String

from config import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    created_at = Column(String(40), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=True)
    verification_token = Column(String(255), nullable=True)

    # Guest accounts: /auth/guest creates a row used only by guests; the
    # upgrade keeps the SAME row/user_id so all progress is preserved
    # without any data migration. is_guest=True with stale created_at is swept.
    is_guest = Column(Boolean, default=False, nullable=True)

    # OAuth / Profile fields
    auth_provider = Column(String(20), nullable=True, default="password")  # 'password'|'google'|'both'
    google_provider_id = Column(String(255), nullable=True)
    email_verified_at = Column(String(40), nullable=True)
    display_name = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    avatar_type = Column(String(20), nullable=True)  # 'preset'|'google'|'upload'
    avatar_source = Column(String(20), nullable=True)  # 'preset'|'google'|'upload'
    profile_completed = Column(Boolean, default=False, nullable=True)
    has_seen_tutorial = Column(Boolean, default=False, nullable=True)
    onboarded_at = Column(String(40), nullable=True)

    # Gamification fields
    current_streak = Column(Integer, default=0, nullable=True)
    longest_streak = Column(Integer, default=0, nullable=True)
    last_activity_date = Column(String(40), nullable=True)
    streak_freezes = Column(Integer, default=0, nullable=True)
    last_freeze_grant_date = Column(String(40), nullable=True)
    coins = Column(Integer, default=0, nullable=True)
