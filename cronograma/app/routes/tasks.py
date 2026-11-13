"""Rotas CRUD de tarefas: GET, POST, PATCH, DELETE."""

from datetime import datetime

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_db
from logger import audit, get_logger
from middleware import rate_limit
from models.area import Areas
from models.schemas import TaskCreate, TaskPatch, TaskResponse
from models.task import Tasks
from services.auth_service import get_current_user

log = get_logger("cronograma.main")

router = APIRouter(tags=["tasks"])


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/tasks", response_model=List[TaskResponse])
def listar_tasks(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(Tasks).filter(Tasks.user_id == user_id).all()


@router.post("/tasks", response_model=TaskResponse)
def criar_task(
    body: TaskCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit(f"crud:tasks:post:{user_id}", max_req=60, window=60)
    if body.area_id is not None:
        area = (
            db.query(Areas)
            .filter(Areas.id == body.area_id, Areas.user_id == user_id)
            .first()
        )
        if not area:
            raise HTTPException(
                status_code=404, detail="Área não encontrada ou não pertence ao usuário"
            )

    task = Tasks(
        user_id=user_id,
        area_id=body.area_id,
        titulo=body.titulo,
        descricao=body.descricao,
        data_entrega=body.data_entrega,
        prioridade=body.prioridade,
        meta_pomodoros=body.meta_pomodoros,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    audit("task.create", user_id=user_id, task_id=task.id, titulo=task.titulo)
    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def atualizar_task(
    task_id: int,
    body: TaskPatch,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit(f"crud:tasks:patch:{user_id}", max_req=60, window=60)
    task = db.query(Tasks).filter(Tasks.id == task_id, Tasks.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    fields_set = body.model_fields_set

    if "area_id" in fields_set:
        if body.area_id is not None:
            area = (
                db.query(Areas)
                .filter(Areas.id == body.area_id, Areas.user_id == user_id)
                .first()
            )
            if not area:
                raise HTTPException(
                    status_code=404, detail="Área não encontrada ou não pertence ao usuário"
                )
        setattr(task, "area_id", body.area_id)
    if "titulo" in fields_set:
        setattr(task, "titulo", body.titulo)
    if "descricao" in fields_set:
        setattr(task, "descricao", body.descricao)
    if "data_entrega" in fields_set:
        setattr(task, "data_entrega", body.data_entrega)
    if "concluida" in fields_set:
        if body.concluida and not task.concluida:
            setattr(task, "concluida_em", datetime.now().isoformat())
        elif not body.concluida:
            setattr(task, "concluida_em", None)
        setattr(task, "concluida", body.concluida)
    if "duracao_minutos" in fields_set:
        setattr(task, "duracao_minutos", body.duracao_minutos)
    if "prioridade" in fields_set:
        setattr(task, "prioridade", body.prioridade)
    if "meta_pomodoros" in fields_set:
        setattr(task, "meta_pomodoros", body.meta_pomodoros)
    if "pomodoros_concluidos" in fields_set:
        setattr(task, "pomodoros_concluidos", body.pomodoros_concluidos)

    db.commit()
    db.refresh(task)
    audit("task.update", user_id=user_id, task_id=task_id)
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def excluir_task(
    task_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rate_limit(f"crud:tasks:delete:{user_id}", max_req=60, window=60)
    task = db.query(Tasks).filter(Tasks.id == task_id, Tasks.user_id == user_id).first()
    if not task:
        log.warning(
            "Task not found for delete",
            extra={"task_id": task_id, "user_id": user_id, "action": "task_delete"},
        )
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    try:
        from models.sessao import Sessoes

        db.query(Sessoes).filter(
            Sessoes.task_id == task_id, Sessoes.user_id == user_id
        ).delete(synchronize_session="fetch")
        db.delete(task)
        db.commit()
    except Exception:
        db.rollback()
        pass
    audit("task.delete", user_id=user_id, task_id=task_id)
    return None
