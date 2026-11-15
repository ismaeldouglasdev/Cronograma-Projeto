"""Rotas CRUD de áreas: GET, POST, PATCH, DELETE + progresso semanal."""

import html
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import get_db
from logger import audit, get_logger
from middleware import rate_limit
from models.area import Areas
from models.schemas import AreaCreate, AreaPatch, AreaResponse
from models.sessao import Sessoes
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
    tipo = body.tipo or "online"
    area = Areas(
        user_id=user_id,
        nome=html.escape(body.nome.strip()),
        cor=body.cor,
        ordem=body.ordem,
        tipo=tipo,
        dia_semana=body.dia_semana if tipo == "presencial" else None,
        horario=body.horario if tipo == "presencial" else None,
        sala=body.sala if tipo == "presencial" else None,
        bloco=body.bloco if tipo == "presencial" else None,
        professor=body.professor if tipo == "presencial" else None,
        subcategoria=body.subcategoria,
        meta_horas_semanal=body.meta_horas_semanal,
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

    fields_set = body.model_fields_set

    if "nome" in fields_set:
        setattr(area, "nome", html.escape(body.nome.strip()))
    if "cor" in fields_set:
        setattr(area, "cor", body.cor)
    if "ordem" in fields_set:
        setattr(area, "ordem", body.ordem)
    if "tipo" in fields_set:
        setattr(area, "tipo", body.tipo)
    if "subcategoria" in fields_set:
        setattr(area, "subcategoria", body.subcategoria)
    if "meta_horas_semanal" in fields_set:
        setattr(area, "meta_horas_semanal", body.meta_horas_semanal)

    tipo_changed_to_non_presencial = "tipo" in fields_set and body.tipo != "presencial"

    if "dia_semana" in fields_set:
        if not tipo_changed_to_non_presencial:
            setattr(area, "dia_semana", body.dia_semana)
        else:
            area.dia_semana = None
    if "horario" in fields_set:
        if not tipo_changed_to_non_presencial:
            setattr(area, "horario", body.horario)
        else:
            area.horario = None
    if "sala" in fields_set:
        if not tipo_changed_to_non_presencial:
            setattr(area, "sala", body.sala)
        else:
            area.sala = None
    if "bloco" in fields_set:
        if not tipo_changed_to_non_presencial:
            setattr(area, "bloco", body.bloco)
        else:
            area.bloco = None
    if "professor" in fields_set:
        if not tipo_changed_to_non_presencial:
            setattr(area, "professor", body.professor)
        else:
            area.professor = None

    if tipo_changed_to_non_presencial:
        area.dia_semana = None
        area.horario = None
        area.sala = None
        area.bloco = None
        area.professor = None

    db.commit()
    db.refresh(area)
    audit("area.update", user_id=user_id, area_id=area_id)
    return area


@router.get("/areas/weekly-progress")
def areas_weekly_progress(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Progresso da meta semanal (segunda a hoje) por área.

    Retorna uma lista com minutos/horas estudados na semana atual e o
    percentual da meta (meta_horas_semanal), ou None quando a área não tem
    meta definida. O frontend busca uma vez e mescla com os cards.
    """
    areas = db.query(Areas).filter(Areas.user_id == user_id).all()
    if not areas:
        return []

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    area_ids = [a.id for a in areas]

    rows = (
        db.query(
            Sessoes.area_id,
            func.coalesce(func.sum(Sessoes.duracao_minutos), 0),
        )
        .filter(
            Sessoes.user_id == user_id,
            Sessoes.area_id.in_(area_ids),
            Sessoes.data >= monday,
            Sessoes.data <= today,
        )
        .group_by(Sessoes.area_id)
        .all()
    )
    minutes_by_area = {area_id: int(total) for area_id, total in rows}

    result = []
    for area in areas:
        minutos = minutes_by_area.get(area.id, 0)
        meta = area.meta_horas_semanal
        entry = {
            "area_id": area.id,
            "meta_horas_semanal": meta,
            "minutos_estudados": minutos,
            "horas_estudadas": round(minutos / 60, 1),
            "progresso_pct": None,
        }
        if meta:
            entry["progresso_pct"] = min(round(minutos / (meta * 60) * 100), 100)
        result.append(entry)

    return result


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
