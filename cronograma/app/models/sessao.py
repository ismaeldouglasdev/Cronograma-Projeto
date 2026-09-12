from sqlalchemy import Column, Date, ForeignKey, Integer

from config import Base


class Sessoes(Base):
    __tablename__ = "sessoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=False)
    duracao_minutos = Column(Integer, nullable=False)
    data = Column(Date, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
