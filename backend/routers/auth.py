from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from auth import create_access_token, get_current_user, hash_password, verify_password
from database import get_db
from errors import api_error

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: models.User) -> dict:
    return {"id": user.id, "email": user.email, "team_id": user.team_id}


@router.post("/signup", status_code=201)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise api_error(409, "EMAIL_TAKEN", "이미 가입된 이메일입니다")

    user = models.User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return {"token": token, "user": _user_out(user)}


@router.post("/login")
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise api_error(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 일치하지 않습니다")

    token = create_access_token(user.id)
    return {"token": token, "user": _user_out(user)}


@router.get("/me")
def me(current_user: models.User = Depends(get_current_user)):
    return _user_out(current_user)


@router.post("/logout")
def logout(current_user: models.User = Depends(get_current_user)):
    return {}
