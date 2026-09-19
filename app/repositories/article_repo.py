# 文章数据访问
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.user import User


def get_by_id(db: Session, article_id: int) -> Article | None:
    # 按主键查询
    return db.get(Article, article_id)


def create(db: Session, article: Article) -> Article:
    # 插入文章并 flush
    db.add(article)
    db.flush()
    return article


def list_by_author(
    db: Session,
    author_id: int,
    *,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Article], int]:
    # 作者文章列表 + 总数
    filters = [Article.author_id == author_id]
    if status:
        filters.append(Article.status == status)

    count_stmt = select(func.count()).select_from(Article).where(*filters)
    total = int(db.scalar(count_stmt) or 0)

    stmt = (
        select(Article)
        .where(*filters)
        .order_by(Article.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(db.scalars(stmt).all())
    return items, total


def list_published(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
    author_id: int | None = None,
    column_name: str | None = None,
) -> tuple[list[tuple[Article, str]], int]:
    # 已发布列表（含作者名）+ 总数
    filters = [Article.status == "published"]
    if author_id is not None:
        filters.append(Article.author_id == author_id)
    if column_name:
        filters.append(Article.column_name == column_name)
    count_stmt = select(func.count()).select_from(Article).where(*filters)
    total = int(db.scalar(count_stmt) or 0)
    stmt = (
        select(Article, User.username)
        .join(User, User.id == Article.author_id)
        .where(*filters)
        .order_by(Article.published_at.desc().nulls_last(), Article.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list(db.execute(stmt).all())
    return [(row[0], row[1]) for row in rows], total


def touch_updated(db: Session, article: Article) -> Article:
    # 刷新 updated_at
    article.updated_at = datetime.now(timezone.utc)
    db.flush()
    return article


def delete(db: Session, article: Article) -> None:
    # 删除行
    db.delete(article)
    db.flush()
