# 文章 Schema（草稿 CRUD + 发布）
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.constants import ARTICLE_CATEGORIES, ArticleStatus, ReviewStatus

# 与 Model 列长 / 业务上限对齐
TITLE_MAX = 200
SUBTITLE_MAX = 200
SUMMARY_MAX = 500
CONTENT_MD_MAX = 12000
TAG_ITEM_MAX = 32
TAGS_MAX = 8
CATEGORY_MAX = 32
COLUMN_NAME_MAX = 120
COVER_URL_MAX = 512

TagItem = Annotated[str, Field(min_length=1, max_length=TAG_ITEM_MAX)]


def _strip_str(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


class CreateArticleDTO(BaseModel):
    """创建草稿。"""

    title: str = Field(default="", max_length=TITLE_MAX)
    subtitle: str = Field(default="", max_length=SUBTITLE_MAX)
    summary: str = Field(default="", max_length=SUMMARY_MAX)
    content_md: str = Field(default="", max_length=CONTENT_MD_MAX)
    tags: list[TagItem] = Field(default_factory=list, max_length=TAGS_MAX)
    category: str = Field(default="后端", max_length=CATEGORY_MAX)
    column_name: str = Field(default="", max_length=COLUMN_NAME_MAX)
    cover_url: str = Field(default="", max_length=COVER_URL_MAX)

    @field_validator(
        "title", "subtitle", "summary", "content_md", "column_name", "cover_url", "category",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value: object) -> object:
        return _strip_str(value)

    @field_validator("tags", mode="before")
    @classmethod
    def strip_tags(cls, value: object) -> object:
        # 去掉空白标签
        if not isinstance(value, list):
            return value
        return [str(t).strip() for t in value if str(t).strip()]

    @field_validator("category")
    @classmethod
    def category_whitelist(cls, value: str) -> str:
        # 空则默认后端；必须在白名单内
        category = value or "后端"
        if category not in ARTICLE_CATEGORIES:
            raise ValueError(f"分类不合法，可选：{', '.join(ARTICLE_CATEGORIES)}")
        return category


class UpdateArticleDTO(BaseModel):
    """更新草稿（字段均可选）。"""

    title: str | None = Field(default=None, max_length=TITLE_MAX)
    subtitle: str | None = Field(default=None, max_length=SUBTITLE_MAX)
    summary: str | None = Field(default=None, max_length=SUMMARY_MAX)
    content_md: str | None = Field(default=None, max_length=CONTENT_MD_MAX)
    tags: list[TagItem] | None = Field(default=None, max_length=TAGS_MAX)
    category: str | None = Field(default=None, max_length=CATEGORY_MAX)
    column_name: str | None = Field(default=None, max_length=COLUMN_NAME_MAX)
    cover_url: str | None = Field(default=None, max_length=COVER_URL_MAX)

    @field_validator(
        "title", "subtitle", "summary", "content_md", "column_name", "cover_url", "category",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value: object) -> object:
        return _strip_str(value)

    @field_validator("tags", mode="before")
    @classmethod
    def strip_tags(cls, value: object) -> object:
        if value is None or not isinstance(value, list):
            return value
        return [str(t).strip() for t in value if str(t).strip()]

    @field_validator("category")
    @classmethod
    def category_whitelist(cls, value: str | None) -> str | None:
        if value is None:
            return value
        category = value or "后端"
        if category not in ARTICLE_CATEGORIES:
            raise ValueError(f"分类不合法，可选：{', '.join(ARTICLE_CATEGORIES)}")
        return category


class PublishArticleDTO(BaseModel):
    """发布时可合并的元数据（均可选；空 body 用当前存盘内容）。"""

    title: str | None = Field(default=None, max_length=TITLE_MAX)
    subtitle: str | None = Field(default=None, max_length=SUBTITLE_MAX)
    summary: str | None = Field(default=None, max_length=SUMMARY_MAX)
    content_md: str | None = Field(default=None, max_length=CONTENT_MD_MAX)
    tags: list[TagItem] | None = Field(default=None, max_length=TAGS_MAX)
    category: str | None = Field(default=None, max_length=CATEGORY_MAX)
    column_name: str | None = Field(default=None, max_length=COLUMN_NAME_MAX)
    cover_url: str | None = Field(default=None, max_length=COVER_URL_MAX)
    allow_comment: bool | None = Field(default=None)

    @field_validator(
        "title", "subtitle", "summary", "content_md", "column_name", "cover_url", "category",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value: object) -> object:
        return _strip_str(value)

    @field_validator("tags", mode="before")
    @classmethod
    def strip_tags(cls, value: object) -> object:
        if value is None or not isinstance(value, list):
            return value
        return [str(t).strip() for t in value if str(t).strip()]

    @field_validator("category")
    @classmethod
    def category_whitelist(cls, value: str | None) -> str | None:
        if value is None:
            return value
        category = value or "后端"
        if category not in ARTICLE_CATEGORIES:
            raise ValueError(f"分类不合法，可选：{', '.join(ARTICLE_CATEGORIES)}")
        return category


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
    like_count: int = 0
    liked: bool = False
    favorited: bool = False
    favorite_folder: str = ""

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
    author_name: str = ""
    published_at: datetime | None = None
    updated_at: datetime
    created_at: datetime

    @field_serializer("id", "author_id")
    def serialize_ids(self, value: int) -> str:
        return str(value)


class ArticleListVO(BaseModel):
    """我的文章列表。"""

    items: list[ArticleListItemVO]
    total: int
