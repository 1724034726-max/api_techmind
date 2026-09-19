# 用户 / 资料 Schema
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from typing import Annotated

from app.core.constants import ThemePreference, UserRole, UserStatus


class UserVO(BaseModel):
    """用户对外展示对象（VO，不含密码）。"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    username: str
    email: str
    role: UserRole
    tags: list[str] = Field(default_factory=list)
    bio: str
    theme: ThemePreference = ThemePreference.LIGHT
    followers: int = Field(validation_alias="followers_count")
    following: int = Field(validation_alias="following_count")
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        # 雪花 ID 输出为字符串，避免前端精度丢失
        return str(value)


class UpdateThemeDTO(BaseModel):
    """更新账号主题偏好。"""

    theme: ThemePreference


class PublicUserVO(BaseModel):
    """作者主页展示（不含邮箱）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: UserRole
    tags: list[str] = Field(default_factory=list)
    bio: str

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        return str(value)


InterestTag = Annotated[str, Field(min_length=1, max_length=32)]


class UpdateProfileDTO(BaseModel):
    """更新资料。"""

    username: str | None = Field(default=None, min_length=2, max_length=16)
    bio: str | None = Field(default=None, max_length=160)
    role: UserRole | None = None
    tags: list[InterestTag] | None = Field(default=None, max_length=20)

    @field_validator("username", "bio", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def strip_tags(cls, value: object) -> object:
        if value is None or not isinstance(value, list):
            return value
        return [str(item).strip() for item in value if str(item).strip()]


class ChangePasswordDTO(BaseModel):
    """修改密码。"""

    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
