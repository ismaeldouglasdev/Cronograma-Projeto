from sqlalchemy import Column, ForeignKey, Integer, String

from config import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(String(500), nullable=False)
    categoria = Column(String(50), nullable=False)
    requisito = Column(Integer, nullable=False)
    icone = Column(String(50), nullable=True)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    unlocked_at = Column(String(40), nullable=True)
