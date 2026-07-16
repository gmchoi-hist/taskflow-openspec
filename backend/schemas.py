from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    team_id: Optional[int] = None


class TokenResponse(BaseModel):
    token: str
    user: UserOut


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=30)


class TeamJoinRequest(BaseModel):
    invite_code: str


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    invite_code: str
    owner_id: int
    created_at: datetime


class TeamInfoOut(BaseModel):
    id: int
    name: str
    invite_code: str
    owner_id: int
    member_count: int


class MemberOut(BaseModel):
    id: int
    email: str
    is_owner: bool
    created_at: datetime


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    assignee_id: Optional[int] = None


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    assignee_id: Optional[int] = None
    clear_assignee: bool = False


class TaskStatusUpdateRequest(BaseModel):
    status: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    title: str
    status: str
    creator_id: int
    assignee_id: Optional[int] = None
    created_at: datetime


class MessageCreateRequest(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: int
    team_id: int
    user_id: int
    user_email: str
    content: str
    created_at: datetime
