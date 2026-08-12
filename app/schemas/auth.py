# 认证相关 Schema
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import UserRole
from app.schemas.user import UserVO


class RegisterDTO(BaseModel):
    """注册入参 DTO。"""

    username: str = Field(min_length=2, max_length=16)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.READER
    tags: list[str] = Field(default_factory=list)
    bio: str | None = Field(default=None, max_length=80)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        # 去掉首尾空白
        return value.strip()

    @field_validator("tags")
    @classmethod
    def tags_not_empty(cls, value: list[str]) -> list[str]:
        # 至少选择一个兴趣标签
        if not value:
            raise ValueError("请至少选择 1 个兴趣标签")
        return value


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
