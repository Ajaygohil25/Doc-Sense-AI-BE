from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class UserSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class UpdateUserSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserResponse(BaseModel):
    first_name: str
    last_name: str
    email: str

class UserLoginSchema(BaseModel):
    username: str
    password: str

class TokenData(BaseModel):
    email: str | None = None
    user_id: UUID | None = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    task_id : str | None = None
    user_id: UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    class Config:
        from_attributes = True

class NewToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

    class Config:
        from_attributes = True


class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    class Config:
        from_attributes = True

class ResetPasswordSchema(BaseModel):
    new_password: str
    confirm_password: str
    class Config:
        from_attributes = True

class UserMail(BaseModel):
    email: str

class TokenSchema(BaseModel):
    token : str

class LoginSchema(BaseModel):
    username: str
    password: str

class LogoutSchema(BaseModel):
    access_token: str
    refresh_token: str

class CeleryTaskSchema(BaseModel):
    email: str
    schedule_time: datetime

class TaskIDSchema(BaseModel):
    task_id: str

class RescheduleTaskSchema(BaseModel):
    task_id: str
    email: str
    schedule_time: datetime