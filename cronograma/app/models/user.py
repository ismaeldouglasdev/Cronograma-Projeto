from sqlalchemy import Boolean, Column, Integer, String

from config import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(String(40), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=True)
    verification_token = Column(String(255), nullable=True)

    # Guest accounts: /auth/guest creates a row used only by guests; the
    # upgrade keeps the SAME row/user_id so all progress is preserved
    # without any data migration. is_guest=True with stale created_at is swept.
    is_guest = Column(Boolean, default=False, nullable=True)

    # Gamification fields
    current_streak = Column(Integer, default=0, nullable=True)
    longest_streak = Column(Integer, default=0, nullable=True)
    last_activity_date = Column(String(40), nullable=True)
    streak_freezes = Column(Integer, default=0, nullable=True)
    last_freeze_grant_date = Column(String(40), nullable=True)
    coins = Column(Integer, default=0, nullable=True)
