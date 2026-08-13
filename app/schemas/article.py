# 文章 Schema（草稿 CRUD）
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.constants import ArticleStatus, ReviewStatus


class CreateArticleDTO(BaseModel):
    """创建草稿。"""

    title: str = ""
    subtitle: str = ""
    summary: str = ""
    content_md: str = ""
    tags: list[str] = Field(default_factory=list)
    category: str = "后端"
    column_name: str = ""
    cover_url: str = ""


class UpdateArticleDTO(BaseModel):
    """更新草稿（字段均可选）。"""

    title: str | None = None
    subtitle: str | None = None
    summary: str | None = None
    content_md: str | None = None
    tags: list[str] | None = None
    category: str | None = None
    column_name: str | None = None
    cover_url: str | None = None


class ArticleVO(BaseModel):
    """文章对外对象。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    author_name: str = ""
    title: str
    subtitle: str
    summary: str
    content_md: str
    tags: list[str] = Field(default_factory=list)
    category: str
    column_name: str
    cover_url: str
    status: ArticleStatus
    review_status: ReviewStatus
    allow_comment: bool
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("id", "author_id")
    def serialize_ids(self, value: int) -> str:
        return str(value)


class ArticleListItemVO(BaseModel):
    """列表项（不含正文，减负）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    title: str
    subtitle: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    category: str
    status: ArticleStatus
    updated_at: datetime
    created_at: datetime

    @field_serializer("id", "author_id")
    def serialize_ids(self, value: int) -> str:
        return str(value)


class ArticleListVO(BaseModel):
    """我的文章列表。"""

    items: list[ArticleListItemVO]
    total: int
