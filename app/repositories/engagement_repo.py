# 点赞 / 收藏 / 评论数据访问
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.comment import Comment
from app.models.favorite import Favorite
from app.models.like import ArticleLike
from app.models.user import User


def like_count(db: Session, article_id: int) -> int:
    # 点赞数
    stmt = select(func.count()).select_from(ArticleLike).where(ArticleLike.article_id == article_id)
    return int(db.scalar(stmt) or 0)


def has_like(db: Session, user_id: int, article_id: int) -> bool:
    # 当前用户是否已赞
    row = db.get(ArticleLike, {"user_id": user_id, "article_id": article_id})
    return row is not None


def add_like(db: Session, user_id: int, article_id: int) -> None:
    # 写入点赞
    db.add(ArticleLike(user_id=user_id, article_id=article_id))
    db.flush()


def remove_like(db: Session, user_id: int, article_id: int) -> None:
    # 取消点赞
    row = db.get(ArticleLike, {"user_id": user_id, "article_id": article_id})
    if row:
        db.delete(row)
        db.flush()


def get_favorite(db: Session, user_id: int, article_id: int) -> Favorite | None:
    # 一条收藏
    return db.get(Favorite, {"user_id": user_id, "article_id": article_id})


def save_favorite(db: Session, user_id: int, article_id: int, folder: str) -> Favorite:
    # 收藏或改夹
    row = get_favorite(db, user_id, article_id)
    if row:
        row.folder = folder
    else:
        row = Favorite(user_id=user_id, article_id=article_id, folder=folder)
        db.add(row)
    db.flush()
    return row


def remove_favorite(db: Session, user_id: int, article_id: int) -> None:
    # 取消收藏
    row = get_favorite(db, user_id, article_id)
    if row:
        db.delete(row)
        db.flush()


def list_folders(db: Session, user_id: int) -> list[str]:
    # 当前用户的夹名
    stmt = (
        select(Favorite.folder)
        .where(Favorite.user_id == user_id)
        .distinct()
        .order_by(Favorite.folder.asc())
    )
    return list(db.scalars(stmt).all())


def list_favorites(
    db: Session, user_id: int, folder: str | None, limit: int, offset: int
) -> tuple[list[tuple[Favorite, Article, str]], int]:
    # 收藏及文章、作者名
    filters = [Favorite.user_id == user_id]
    if folder:
        filters.append(Favorite.folder == folder)
    total = int(
        db.scalar(select(func.count()).select_from(Favorite).where(*filters)) or 0
    )
    stmt = (
        select(Favorite, Article, User.username)
        .join(Article, Article.id == Favorite.article_id)
        .join(User, User.id == Article.author_id)
        .where(*filters)
        .order_by(Favorite.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list(db.execute(stmt).all())
    return [(row[0], row[1], row[2]) for row in rows], total


def list_comments(
    db: Session, article_id: int, limit: int
) -> tuple[list[tuple[Comment, str]], int]:
    # 评论及作者名
    filters = [Comment.article_id == article_id]
    total = int(db.scalar(select(func.count()).select_from(Comment).where(*filters)) or 0)
    stmt = (
        select(Comment, User.username)
        .join(User, User.id == Comment.author_id)
        .where(*filters)
        .order_by(Comment.created_at.desc())
        .limit(limit)
    )
    rows = list(db.execute(stmt).all())
    return [(row[0], row[1]) for row in rows], total


def get_comment(db: Session, comment_id: int) -> Comment | None:
    # 按主键取评论
    return db.get(Comment, comment_id)


def add_comment(db: Session, comment: Comment) -> Comment:
    # 插入评论
    db.add(comment)
    db.flush()
    return comment


def delete_comment(db: Session, comment: Comment) -> None:
    # 删除评论
    db.delete(comment)
    db.flush()
