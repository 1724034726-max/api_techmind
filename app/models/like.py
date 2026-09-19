# 点赞关系
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ArticleLike(Base):
    """用户对文章的点赞。"""

    __tablename__ = "article_likes"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("articles.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
