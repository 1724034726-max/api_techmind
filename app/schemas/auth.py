# 认证相关 Schema
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import UserRole
from app.schemas.user import UserVO

InterestTag = Annotated[str, Field(min_length=1, max_length=32)]


class RegisterDTO(BaseModel):
    """注册入参 DTO。"""

    username: str = Field(min_length=2, max_length=16)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.READER
    tags: list[InterestTag] = Field(default_factory=list, min_length=1, max_length=20)
    bio: str | None = Field(default=None, max_length=80)

    @field_validator("username", "bio", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def strip_tags(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return [str(t).strip() for t in value if str(t).strip()]


class LoginDTO(BaseModel):
    """登录入参 DTO。"""

    account: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("account")
    @classmethod
    def strip_account(cls, value: str) -> str:
        return value.strip()


class TokenVO(BaseModel):
    """登录 / 注册成功返回 VO。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserVO
