import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, Header
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import models
from database import get_db
from errors import api_error

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    authorization: str = Header(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    if not authorization or not authorization.startswith("Bearer "):
        raise api_error(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")

    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise api_error(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise api_error(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")

    return user
