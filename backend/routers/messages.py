from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from errors import api_error

router = APIRouter(tags=["messages"])

MAX_MESSAGE_LENGTH = 1000
RECENT_MESSAGE_LIMIT = 50


def require_member(user: models.User, team_id: int) -> None:
    if user.team_id != team_id:
        raise api_error(403, "FORBIDDEN", "이 팀의 멤버가 아닙니다")


def _serialize(message: models.Message, email: str) -> dict:
    return {
        "id": message.id,
        "team_id": message.team_id,
        "user_id": message.user_id,
        "user_email": email,
        "content": message.content,
        "created_at": message.created_at,
    }


@router.post("/teams/{team_id}/messages", status_code=201)
def send_message(
    team_id: int,
    payload: schemas.MessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    require_member(current_user, team_id)

    content = payload.content
    if not content or not content.strip():
        raise api_error(400, "VALIDATION_ERROR", "메시지를 입력하세요")
    if len(content) > MAX_MESSAGE_LENGTH:
        raise api_error(
            400,
            "TOO_LONG",
            "메시지는 1000자 이내",
            limit=MAX_MESSAGE_LENGTH,
            actual=len(content),
        )

    message = models.Message(team_id=team_id, user_id=current_user.id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return _serialize(message, current_user.email)


@router.get("/teams/{team_id}/messages")
def list_messages(
    team_id: int,
    since: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    require_member(current_user, team_id)

    q = (
        db.query(models.Message, models.User.email)
        .join(models.User, models.Message.user_id == models.User.id)
        .filter(models.Message.team_id == team_id)
    )

    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise api_error(400, "VALIDATION_ERROR", "since 형식이 올바르지 않습니다")
        rows = q.filter(models.Message.created_at > since_dt).order_by(models.Message.created_at.asc()).all()
    else:
        rows = q.order_by(models.Message.created_at.desc()).limit(RECENT_MESSAGE_LIMIT).all()
        rows = list(reversed(rows))

    return [_serialize(m, email) for m, email in rows]


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise api_error(404, "NOT_FOUND", "해당 항목을 찾을 수 없습니다")

    require_member(current_user, message.team_id)

    if message.user_id != current_user.id:
        raise api_error(403, "NOT_OWNER", "본인 메시지만 삭제 가능")

    db.delete(message)
    db.commit()
    return {}
