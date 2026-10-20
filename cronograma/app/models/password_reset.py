from sqlalchemy import Column, Integer, String

from config import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    # Armazena apenas o hash SHA-256 do token; o cru fica no email e nunca
    # no banco nem em log.
    token_hash = Column(String(64), nullable=False, unique=True)
    created_at = Column(String(40), nullable=True)
    expires_at = Column(String(40), nullable=True)
    used_at = Column(String(40), nullable=True)
