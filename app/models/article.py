# 文章 ORM 模型
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ArticleStatus, ReviewStatus
from app.models.base import Base


class Article(Base):
    """文章主表（草稿与已发布共用；本迭代仅写 draft）。"""

    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_articles_status",
        ),
        CheckConstraint(
            "review_status IN ('none', 'pending', 'approved', 'rejected')",
            name="ck_articles_review",
        ),
        Index("idx_articles_author_status", "author_id", "status", "updated_at"),
        Index("idx_articles_status_published", "status", "published_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="", server_default="")
    subtitle: Mapped[str] = mapped_column(String(200), nullable=False, default="", server_default="")
    summary: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    category: Mapped[str] = mapped_column(
        String(32), nullable=False, default="后端", server_default="后端"
    )
    column_name: Mapped[str] = mapped_column(
        String(120), nullable=False, default="", server_default=""
    )
    cover_url: Mapped[str] = mapped_column(
        String(512), nullable=False, default="", server_default=""
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=ArticleStatus.DRAFT.value,
        server_default=ArticleStatus.DRAFT.value,
    )
    review_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=ReviewStatus.NONE.value,
        server_default=ReviewStatus.NONE.value,
    )
    allow_comment: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
