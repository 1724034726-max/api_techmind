# 用户 / 资料 Schema
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.constants import UserRole, UserStatus


class UserVO(BaseModel):
    """用户对外展示对象（VO，不含密码）。"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    username: str
    email: str
    role: UserRole
    tags: list[str] = Field(default_factory=list)
    bio: str
    followers: int = Field(validation_alias="followers_count")
    following: int = Field(validation_alias="following_count")
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        # 雪花 ID 输出为字符串，避免前端精度丢失
        return str(value)
