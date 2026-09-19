# 点赞 / 收藏 / 评论
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import ArticleStatus
from app.core.error_codes import ErrorCode
from app.core.exceptions import exception
from app.core.sensitive import find_sensitive
from app.core.snowflake import next_id
from app.models.comment import Comment
from app.models.user import User
from app.repositories import article_repo, engagement_repo
from app.schemas.article import ArticleListItemVO
from app.schemas.engagement import (
    CommentListVO,
    CommentVO,
    EngageStateVO,
    FavoriteItemVO,
    FavoriteListVO,
)


def _published(db: Session, article_id: int):
    # 仅已发布文章可互动
    article = article_repo.get_by_id(db, article_id)
    if not article or article.status != ArticleStatus.PUBLISHED.value:
        raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
    return article


def state(db: Session, user: User, article_id: int) -> EngageStateVO:
    # 点赞数与当前用户关系
    fav = engagement_repo.get_favorite(db, user.id, article_id)
    return EngageStateVO(
        like_count=engagement_repo.like_count(db, article_id),
        liked=engagement_repo.has_like(db, user.id, article_id),
        favorited=fav is not None,
        favorite_folder=fav.folder if fav else "",
    )


def like(db: Session, user: User, article_id: int) -> EngageStateVO:
    # 点赞（已赞则保持）
    _published(db, article_id)
    if not engagement_repo.has_like(db, user.id, article_id):
        try:
            engagement_repo.add_like(db, user.id, article_id)
            db.commit()
        except IntegrityError:
            db.rollback()
    return state(db, user, article_id)


def unlike(db: Session, user: User, article_id: int) -> EngageStateVO:
    # 取消点赞
    _published(db, article_id)
    engagement_repo.remove_like(db, user.id, article_id)
    db.commit()
    return state(db, user, article_id)


def favorite(db: Session, user: User, article_id: int, folder: str) -> EngageStateVO:
    # 收藏到夹；并发插入撞主键时改为更新夹名
    _published(db, article_id)
    try:
        engagement_repo.save_favorite(db, user.id, article_id, folder)
        db.commit()
    except IntegrityError:
        db.rollback()
        engagement_repo.save_favorite(db, user.id, article_id, folder)
        db.commit()
    return state(db, user, article_id)


def unfavorite(db: Session, user: User, article_id: int) -> EngageStateVO:
    # 取消收藏
    engagement_repo.remove_favorite(db, user.id, article_id)
    db.commit()
    return state(db, user, article_id)


def list_favorites(
    db: Session, user: User, folder: str | None, limit: int, offset: int
) -> FavoriteListVO:
    # 按夹列出收藏
    rows, total = engagement_repo.list_favorites(db, user.id, folder, limit, offset)
    items = [
        FavoriteItemVO(
            folder=fav.folder,
            article=ArticleListItemVO.model_validate(article).model_copy(
                update={"author_name": name}
            ),
        )
        for fav, article, name in rows
    ]
    return FavoriteListVO(
        items=items,
        total=total,
        folders=engagement_repo.list_folders(db, user.id),
    )


def list_comments(db: Session, article_id: int) -> CommentListVO:
    # 评论列表
    article = article_repo.get_by_id(db, article_id)
    if not article or article.status != ArticleStatus.PUBLISHED.value:
        raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
    rows, total = engagement_repo.list_comments(db, article_id, 50)
    items = [
        CommentVO.model_validate(comment).model_copy(update={"author_name": name})
        for comment, name in rows
    ]
    return CommentListVO(items=items, total=total)


def add_comment(db: Session, user: User, article_id: int, content: str) -> CommentVO:
    # 发表评论
    article = _published(db, article_id)
    if not article.allow_comment:
        raise exception(ErrorCode.ERR_COMMENT_CLOSED, http_status=400)
    hit = find_sensitive(content)
    if hit is not None:
        raise exception(ErrorCode.ERR_SENSITIVE_WORD, http_status=400, detail={"word": hit})
    comment = engagement_repo.add_comment(
        db,
        Comment(
            id=next_id(),
            article_id=article_id,
            author_id=user.id,
            content=content,
        ),
    )
    db.commit()
    db.refresh(comment)
    return CommentVO.model_validate(comment).model_copy(update={"author_name": user.username})


def delete_comment(db: Session, user: User, article_id: int, comment_id: int) -> None:
    # 作者删除自己的评论
    comment = engagement_repo.get_comment(db, comment_id)
    if not comment or comment.article_id != article_id or comment.author_id != user.id:
        raise exception(ErrorCode.ERR_COMMENT_NOT_FOUND, http_status=404)
    engagement_repo.delete_comment(db, comment)
    db.commit()
