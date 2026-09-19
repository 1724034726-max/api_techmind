# 专题 Schema
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.schemas.article import ArticleListItemVO


def _strip(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


class TopicDTO(BaseModel):
    """创建或更新专题。"""

    title: str = Field(min_length=1, max_length=80)
    summary: str = Field(default="", max_length=300)

    @field_validator("title", "summary", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return _strip(value)


class UpdateTopicDTO(BaseModel):
    """更新专题（字段可选）。"""

    title: str | None = Field(default=None, min_length=1, max_length=80)
    summary: str | None = Field(default=None, max_length=300)

    @field_validator("title", "summary", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return _strip(value)


class SetTopicArticlesDTO(BaseModel):
    """替换专题下的文章。"""

    article_ids: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("article_ids")
    @classmethod
    def digits(cls, value: list[str]) -> list[str]:
        for item in value:
            if not str(item).isdigit():
                raise ValueError("文章 id 不合法")
        return [str(item) for item in value]


class TopicVO(BaseModel):
    """专题。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    title: str
    summary: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id", "owner_id")
    def serialize_ids(self, value: int) -> str:
        return str(value)


class TopicDetailVO(TopicVO):
    """专题及其已发布文章。"""

    articles: list[ArticleListItemVO]


class TopicListVO(BaseModel):
    """专题列表。"""

    items: list[TopicVO]
    total: int
