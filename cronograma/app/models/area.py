from sqlalchemy import Column, ForeignKey, Integer, String

from config import Base


class Areas(Base):
    __tablename__ = "areas"
    __mapper_args__ = {"confirm_deleted_rows": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    cor = Column(String(20), nullable=True)
    ordem = Column(Integer, nullable=True)
    tipo = Column(String(20), default="online", nullable=True)
    dia_semana = Column(String(20), nullable=True)
    horario = Column(String(50), nullable=True)
    sala = Column(String(50), nullable=True)
    bloco = Column(String(50), nullable=True)
    professor = Column(String(255), nullable=True)
    subcategoria = Column(String(100), nullable=True)
