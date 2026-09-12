from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String

from config import Base


class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(String(500), nullable=True)
    data_entrega = Column(Date, nullable=False)
    concluida = Column(Boolean, default=False, nullable=False)
    duracao_minutos = Column(Integer, nullable=True)
    prioridade = Column(Integer, nullable=True)
    meta_pomodoros = Column(Integer, nullable=True)
    pomodoros_concluidos = Column(Integer, default=0, nullable=True)
