from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from errors import api_error

router = APIRouter(tags=["tasks"])

VALID_STATUSES = {"TODO", "DOING", "DONE"}


def require_member(user: models.User, team_id: int) -> None:
    if user.team_id != team_id:
        raise api_error(403, "FORBIDDEN", "이 팀의 멤버가 아닙니다")


def _task_or_404(db: Session, task_id: int) -> models.Task:
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise api_error(404, "NOT_FOUND", "해당 항목을 찾을 수 없습니다")
    return task


def _serialize(task: models.Task) -> dict:
    return {
        "id": task.id,
        "team_id": task.team_id,
        "title": task.title,
        "status": task.status,
        "creator_id": task.creator_id,
        "assignee_id": task.assignee_id,
        "created_at": task.created_at,
    }


@router.post("/teams/{team_id}/tasks", status_code=201)
def create_task(
    team_id: int,
    payload: schemas.TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    require_member(current_user, team_id)

    if payload.assignee_id is not None:
        assignee = (
            db.query(models.User)
            .filter(models.User.id == payload.assignee_id, models.User.team_id == team_id)
            .first()
        )
        if not assignee:
            raise api_error(400, "VALIDATION_ERROR", "담당자가 이 팀의 멤버가 아닙니다")

    task = models.Task(
        team_id=team_id,
        title=payload.title,
        status="TODO",
        creator_id=current_user.id,
        assignee_id=payload.assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _serialize(task)


@router.get("/teams/{team_id}/tasks")
def list_tasks(
    team_id: int,
    filter: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    require_member(current_user, team_id)

    q = db.query(models.Task).filter(models.Task.team_id == team_id)
    if filter == "me":
        q = q.filter(models.Task.assignee_id == current_user.id)
    elif filter == "unassigned":
        q = q.filter(models.Task.assignee_id.is_(None))

    tasks = q.order_by(models.Task.created_at.desc()).all()
    return [_serialize(t) for t in tasks]


@router.get("/tasks/{task_id}")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = _task_or_404(db, task_id)
    require_member(current_user, task.team_id)
    return _serialize(task)


@router.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    payload: schemas.TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = _task_or_404(db, task_id)
    require_member(current_user, task.team_id)

    if payload.title is not None:
        task.title = payload.title

    if payload.clear_assignee:
        task.assignee_id = None
    elif payload.assignee_id is not None:
        assignee = (
            db.query(models.User)
            .filter(models.User.id == payload.assignee_id, models.User.team_id == task.team_id)
            .first()
        )
        if not assignee:
            raise api_error(400, "VALIDATION_ERROR", "담당자가 이 팀의 멤버가 아닙니다")
        task.assignee_id = payload.assignee_id

    db.commit()
    db.refresh(task)
    return _serialize(task)


@router.patch("/tasks/{task_id}/status")
def update_task_status(
    task_id: int,
    payload: schemas.TaskStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = _task_or_404(db, task_id)
    require_member(current_user, task.team_id)

    if payload.status not in VALID_STATUSES:
        raise api_error(400, "VALIDATION_ERROR", "올바른 상태값이 아닙니다")

    task.status = payload.status
    db.commit()
    db.refresh(task)
    return _serialize(task)


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = _task_or_404(db, task_id)
    require_member(current_user, task.team_id)

    team = db.query(models.Team).filter(models.Team.id == task.team_id).first()
    if current_user.id != task.creator_id and current_user.id != team.owner_id:
        raise api_error(403, "FORBIDDEN", "권한이 없습니다")

    db.delete(task)
    db.commit()
    return {}
