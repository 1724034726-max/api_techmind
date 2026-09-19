# 点赞 / 收藏 / 评论 Schema
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.schemas.article import ArticleListItemVO


class FavoriteDTO(BaseModel):
    """收藏到指定夹。"""

    folder: str = Field(default="默认", min_length=1, max_length=32)

    @field_validator("folder", mode="before")
    @classmethod
    def strip_folder(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            return text or "默认"
        return value


class CommentDTO(BaseModel):
    """发表评论。"""

    content: str = Field(min_length=1, max_length=500)

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class EngageStateVO(BaseModel):
    """当前用户对一篇文章的点赞与收藏。"""

    like_count: int
    liked: bool
    favorited: bool
    favorite_folder: str = ""


class CommentVO(BaseModel):
    """评论。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    author_id: int
    author_name: str = ""
    content: str
    created_at: datetime

    @field_serializer("id", "article_id", "author_id")
    def serialize_ids(self, value: int) -> str:
        return str(value)


class CommentListVO(BaseModel):
    """评论列表。"""

    items: list[CommentVO]
    total: int


class FavoriteItemVO(BaseModel):
    """一条收藏。"""

    folder: str
    article: ArticleListItemVO


class FavoriteListVO(BaseModel):
    """收藏列表。"""

    items: list[FavoriteItemVO]
    total: int
    folders: list[str]
