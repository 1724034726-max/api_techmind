# 文章 / 草稿业务逻辑（本迭代不含发布）
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import ArticleStatus, ReviewStatus, UserRole
from app.core.error_codes import ErrorCode
from app.core.exceptions import exception
from app.core.snowflake import next_id
from app.models.article import Article
from app.models.user import User
from app.repositories import article_repo
from app.schemas.article import (
    ArticleListItemVO,
    ArticleListVO,
    ArticleVO,
    CreateArticleDTO,
    UpdateArticleDTO,
)


def _ensure_can_write(user: User) -> None:
    # 仅作者身份可写草稿
    if user.role not in (UserRole.AUTHOR.value, UserRole.BOTH.value):
        raise exception(ErrorCode.ERR_FORBIDDEN, http_status=403)


def _to_vo(article: Article, author_name: str = "") -> ArticleVO:
    return ArticleVO.model_validate(article).model_copy(
        update={"author_name": author_name}
    )


def _get_owned_draft(db: Session, user: User, article_id: int) -> Article:
    # 按 id 取文并校验归属与草稿态
    article = article_repo.get_by_id(db, article_id)
    if not article:
        raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
    if article.author_id != user.id:
        # 防枚举：非作者统一当不存在
        raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
    if article.status != ArticleStatus.DRAFT.value:
        raise exception(ErrorCode.ERR_ARTICLE_STATUS, http_status=400)
    return article


def create_draft(db: Session, user: User, payload: CreateArticleDTO) -> ArticleVO:
    _ensure_can_write(user)

    # 组装并落库草稿
    article = Article(
        id=next_id(),
        author_id=user.id,
        title=payload.title,
        subtitle=payload.subtitle,
        summary=payload.summary,
        content_md=payload.content_md,
        tags=list(payload.tags),
        category=payload.category,
        column_name=payload.column_name,
        cover_url=payload.cover_url,
        status=ArticleStatus.DRAFT.value,
        review_status=ReviewStatus.NONE.value,
    )
    try:
        article_repo.create(db, article)
        db.commit()
    except IntegrityError as exc:
        # 约束冲突（如主键撞车、作者外键失效）
        db.rollback()
        raise exception(ErrorCode.ERR_ARTICLE_SAVE_FAILED, http_status=409) from exc

    db.refresh(article)
    return _to_vo(article, user.username)


def update_draft(
    db: Session, user: User, article_id: int, payload: UpdateArticleDTO
) -> ArticleVO:
    _ensure_can_write(user)
    article = _get_owned_draft(db, user, article_id)

    # 按传入字段局部更新
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is not None:
            setattr(article, key, value)

    try:
        article_repo.touch_updated(db, article)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise exception(ErrorCode.ERR_ARTICLE_SAVE_FAILED, http_status=409) from exc

    # 确认文章仍存在
    fresh = article_repo.get_by_id(db, article_id)
    if not fresh:
        raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
    return _to_vo(fresh, user.username)


def get_draft(db: Session, user: User, article_id: int) -> ArticleVO:
    _ensure_can_write(user)
    article = _get_owned_draft(db, user, article_id)
    return _to_vo(article, user.username)


def list_my_drafts(
    db: Session,
    user: User,
    *,
    limit: int = 20,
    offset: int = 0,
) -> ArticleListVO:
    _ensure_can_write(user)
    limit = max(1, min(limit, 50))
    offset = max(0, offset)

    # 只列当前用户草稿
    items, total = article_repo.list_by_author(
        db,
        user.id,
        status=ArticleStatus.DRAFT.value,
        limit=limit,
        offset=offset,
    )
    return ArticleListVO(
        items=[ArticleListItemVO.model_validate(a) for a in items],
        total=total,
    )


def delete_draft(db: Session, user: User, article_id: int) -> None:
    _ensure_can_write(user)
    article = _get_owned_draft(db, user, article_id)

    # 硬删草稿
    try:
        article_repo.delete(db, article)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise exception(ErrorCode.ERR_ARTICLE_SAVE_FAILED, http_status=409) from exc
