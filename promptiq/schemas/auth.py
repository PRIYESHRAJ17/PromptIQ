"""Authentication and user schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: str
    is_active: bool
    telegram_chat_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: datetime
    iat: datetime


class TelegramLinkRequest(BaseModel):
    telegram_chat_id: str
    link_token: str


class TelegramLinkResponse(BaseModel):
    success: bool
    message: str
    user_id: str
