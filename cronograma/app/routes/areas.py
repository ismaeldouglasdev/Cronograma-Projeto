"""Rotas CRUD de áreas: GET, POST, PATCH, DELETE."""

import html
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_db
from logger import audit, get_logger
from middleware import rate_limit
from models.area import Areas
from models.schemas import AreaCreate, AreaPatch, AreaResponse
from services.auth_service import get_current_user

log = get_logger("cronograma.main")

router = APIRouter(tags=["areas"])


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/areas", response_model=List[AreaResponse])
def listar_areas(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(Areas).filter(Areas.user_id == user_id).all()


@router.post("/areas", response_model=AreaResponse)
def criar_area(
    body: AreaCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit(f"crud:areas:post:{user_id}", max_req=60, window=60)
    area = Areas(
        user_id=user_id,
        nome=html.escape(body.nome.strip()),
        cor=body.cor,
        ordem=body.ordem,
        tipo=body.tipo or "online",
        dia_semana=body.dia_semana,
        horario=body.horario,
        sala=body.sala,
        bloco=body.bloco,
        professor=body.professor,
        subcategoria=body.subcategoria,
    )
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


@router.patch("/areas/{area_id}", response_model=AreaResponse)
def atualizar_area(
    area_id: int,
    body: AreaPatch,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit(f"crud:areas:patch:{user_id}", max_req=60, window=60)
    area = db.query(Areas).filter(Areas.id == area_id, Areas.user_id == user_id).first()
    if not area:
        log.warning(
            "Area not found for update",
            extra={"area_id": area_id, "user_id": user_id, "action": "area_update"},
        )
        raise HTTPException(status_code=404, detail="Área não encontrada")
    if body.nome is not None:
        setattr(area, "nome", html.escape(body.nome.strip()))
    if body.cor is not None:
        setattr(area, "cor", body.cor)
    if body.ordem is not None:
        setattr(area, "ordem", body.ordem)
    if body.tipo is not None:
        setattr(area, "tipo", body.tipo)
    if body.dia_semana is not None:
        setattr(area, "dia_semana", body.dia_semana)
    if body.horario is not None:
        setattr(area, "horario", body.horario)
    if body.sala is not None:
        setattr(area, "sala", body.sala)
    if body.bloco is not None:
        setattr(area, "bloco", body.bloco)
    if body.professor is not None:
        setattr(area, "professor", body.professor)
    if body.subcategoria is not None:
        setattr(area, "subcategoria", body.subcategoria)
    db.commit()
    db.refresh(area)
    audit("area.update", user_id=user_id, area_id=area_id)
    return area


@router.delete("/areas/{area_id}", status_code=204)
def excluir_area(
    area_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit(f"crud:areas:delete:{user_id}", max_req=60, window=60)
    area = db.query(Areas).filter(Areas.id == area_id, Areas.user_id == user_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    try:
        from models.task import Tasks
        from models.sessao import Sessoes

        db.query(Tasks).filter(Tasks.area_id == area_id, Tasks.user_id == user_id).delete(
            synchronize_session="fetch"
        )
        db.query(Sessoes).filter(
            Sessoes.area_id == area_id, Sessoes.user_id == user_id
        ).delete(synchronize_session="fetch")
        db.delete(area)
        db.commit()
    except Exception:
        db.rollback()
        # Idempotent: already deleted by concurrent request
        pass
    audit("area.delete", user_id=user_id, area_id=area_id)
    return None
