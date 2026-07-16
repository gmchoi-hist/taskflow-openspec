import random
import re
import string

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from errors import api_error

router = APIRouter(prefix="/teams", tags=["teams"])

INVITE_CODE_RE = re.compile(r"^[A-Z]{4}-[0-9]{4}$")


def require_member(user: models.User, team_id: int) -> None:
    if user.team_id != team_id:
        raise api_error(403, "FORBIDDEN", "이 팀의 멤버가 아닙니다")


def generate_invite_code(db: Session) -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=4)) + "-" + "".join(random.choices(string.digits, k=4))
        if not db.query(models.Team).filter(models.Team.invite_code == code).first():
            return code


def _team_or_404(db: Session, team_id: int) -> models.Team:
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise api_error(404, "NOT_FOUND", "해당 항목을 찾을 수 없습니다")
    return team


@router.post("", status_code=201)
def create_team(
    payload: schemas.TeamCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.team_id is not None:
        raise api_error(409, "ALREADY_IN_TEAM", "이미 다른 팀에 소속되어 있습니다")

    team = models.Team(
        name=payload.name,
        invite_code=generate_invite_code(db),
        owner_id=current_user.id,
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    current_user.team_id = team.id
    db.commit()

    return {
        "id": team.id,
        "name": team.name,
        "invite_code": team.invite_code,
        "owner_id": team.owner_id,
        "created_at": team.created_at,
    }


@router.post("/join")
def join_team(
    payload: schemas.TeamJoinRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.team_id is not None:
        raise api_error(409, "ALREADY_IN_TEAM", "이미 다른 팀에 소속되어 있습니다")

    code = (payload.invite_code or "").strip().upper()
    if not INVITE_CODE_RE.match(code):
        raise api_error(400, "VALIDATION_ERROR", "형식이 올바르지 않습니다")

    team = db.query(models.Team).filter(models.Team.invite_code == code).first()
    if not team:
        raise api_error(404, "NOT_FOUND", "해당 초대코드를 찾을 수 없습니다")

    current_user.team_id = team.id
    db.commit()

    member_count = db.query(models.User).filter(models.User.team_id == team.id).count()
    return {
        "team": {"id": team.id, "name": team.name, "member_count": member_count},
        "redirect": f"/teams/{team.id}",
    }


@router.get("/{team_id}")
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    require_member(current_user, team_id)
    team = _team_or_404(db, team_id)
    member_count = db.query(models.User).filter(models.User.team_id == team_id).count()
    return {
        "id": team.id,
        "name": team.name,
        "invite_code": team.invite_code,
        "owner_id": team.owner_id,
        "member_count": member_count,
    }


@router.get("/{team_id}/members")
def list_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    require_member(current_user, team_id)
    team = _team_or_404(db, team_id)
    members = db.query(models.User).filter(models.User.team_id == team_id).all()
    return [
        {
            "id": m.id,
            "email": m.email,
            "is_owner": m.id == team.owner_id,
            "created_at": m.created_at,
        }
        for m in members
    ]


@router.delete("/{team_id}/leave")
def leave_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    require_member(current_user, team_id)
    team = _team_or_404(db, team_id)

    if team.owner_id == current_user.id:
        raise api_error(403, "OWNER_CANNOT_LEAVE", "팀 소유자는 탈퇴할 수 없습니다")

    current_user.team_id = None
    db.commit()
    return {}
