# 文章 / 草稿业务逻辑（含发布）
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import ArticleStatus, ReviewStatus, UserRole
from app.core.error_codes import ErrorCode
from app.core.exceptions import exception
from app.core.sensitive import find_sensitive, first_sensitive_in_tags
from app.core.snowflake import next_id
from app.models.article import Article
from app.models.user import User
from app.repositories import article_repo, user_repo
from app.services import engagement_service
from app.schemas.article import (
    SUMMARY_MAX,
    ArticleListItemVO,
    ArticleListVO,
    ArticleVO,
    CreateArticleDTO,
    PublishArticleDTO,
    UpdateArticleDTO,
)


def _ensure_can_write(user: User) -> None:
    # 仅作者身份可写草稿 / 发布
    if user.role not in (UserRole.AUTHOR.value, UserRole.BOTH.value):
        raise exception(ErrorCode.ERR_FORBIDDEN, http_status=403)


def _to_vo(article: Article, author_name: str = "") -> ArticleVO:
    return ArticleVO.model_validate(article).model_copy(
        update={"author_name": author_name}
    )


def _get_owned(db: Session, user: User, article_id: int) -> Article:
    # 按 id 取文并校验归属
    article = article_repo.get_by_id(db, article_id)
    if not article or article.author_id != user.id:
        raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
    return article


def _get_owned_draft(db: Session, user: User, article_id: int) -> Article:
    # 归属校验后再要求草稿态
    article = _get_owned(db, user, article_id)
    if article.status != ArticleStatus.DRAFT.value:
        raise exception(ErrorCode.ERR_ARTICLE_STATUS, http_status=400)
    return article


def _get_owned_editable(db: Session, user: User, article_id: int) -> Article:
    # 草稿或已发布可改；已下架不可
    article = _get_owned(db, user, article_id)
    if article.status == ArticleStatus.ARCHIVED.value:
        raise exception(ErrorCode.ERR_ARTICLE_STATUS, http_status=400)
    return article


def _author_name(db: Session, author_id: int) -> str:
    author = user_repo.get_by_id(db, author_id)
    return author.username if author else ""


def _apply_fields(article: Article, data: dict) -> None:
    # 按传入字段局部更新（跳过 None）
    for key, value in data.items():
        if value is not None:
            setattr(article, key, value)


def _check_sensitive_fields(article: Article) -> None:
    # 标题 / 导读 / 正文 / 标签敏感词
    for text in (article.title, article.summary, article.content_md):
        hit = find_sensitive(text or "")
        if hit is not None:
            raise exception(
                ErrorCode.ERR_SENSITIVE_WORD, http_status=400, detail={"word": hit}
            )
    tag_hit = first_sensitive_in_tags(list(article.tags or []))
    if tag_hit is not None:
        raise exception(
            ErrorCode.ERR_SENSITIVE_WORD, http_status=400, detail={"word": tag_hit}
        )


def _generate_summary(title: str, content_md: str) -> str:
    # 空摘要时按正文截断生成；正文空则用标题兜底
    body = " ".join((content_md or "").replace("#", " ").split())
    if not body:
        text = (title or "").strip() or "（无摘要）"
    else:
        text = body
    if len(text) > SUMMARY_MAX:
        return text[: SUMMARY_MAX - 1].rstrip() + "…"
    return text


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
    article = _get_owned_editable(db, user, article_id)

    # 按传入字段局部更新
    _apply_fields(article, payload.model_dump(exclude_unset=True))

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


def get_article(db: Session, user: User, article_id: int) -> ArticleVO:
    # 已发布谁都能读；其余仅作者
    article = article_repo.get_by_id(db, article_id)
    if not article:
        raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
    if article.status != ArticleStatus.PUBLISHED.value and article.author_id != user.id:
        raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
    vo = _to_vo(article, _author_name(db, article.author_id))
    flags = engagement_service.state(db, user, article.id)
    return vo.model_copy(update=flags.model_dump())


def list_my_articles(
    db: Session,
    user: User,
    *,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> ArticleListVO:
    limit = max(1, min(limit, 50))
    offset = max(0, offset)

    items, total = article_repo.list_by_author(
        db,
        user.id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return ArticleListVO(
        items=[ArticleListItemVO.model_validate(a) for a in items],
        total=total,
    )


def list_published(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
    author_id: int | None = None,
    column_name: str | None = None,
) -> ArticleListVO:
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    rows, total = article_repo.list_published(
        db,
        limit=limit,
        offset=offset,
        author_id=author_id,
        column_name=column_name,
    )
    items = [
        ArticleListItemVO.model_validate(article).model_copy(
            update={"author_name": name}
        )
        for article, name in rows
    ]
    return ArticleListVO(items=items, total=total)


def delete_article(db: Session, user: User, article_id: int) -> None:
    # 草稿硬删；已发布改为下架
    _ensure_can_write(user)
    article = _get_owned(db, user, article_id)
    if article.status == ArticleStatus.ARCHIVED.value:
        raise exception(ErrorCode.ERR_ARTICLE_STATUS, http_status=400)

    try:
        if article.status == ArticleStatus.DRAFT.value:
            article_repo.delete(db, article)
        else:
            article.status = ArticleStatus.ARCHIVED.value
            article_repo.touch_updated(db, article)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise exception(ErrorCode.ERR_ARTICLE_SAVE_FAILED, http_status=409) from exc


def publish_article(
    db: Session, user: User, article_id: int, payload: PublishArticleDTO
) -> ArticleVO:
    # 合并可选 body → 校验 → 敏感词 → 空摘要生成 → 置为已发布
    _ensure_can_write(user)
    article = _get_owned_draft(db, user, article_id)

    _apply_fields(article, payload.model_dump(exclude_unset=True))

    title = (article.title or "").strip()
    content = (article.content_md or "").strip()
    if not title:
        raise exception(ErrorCode.ERR_ARTICLE_TITLE_REQUIRED, http_status=400)
    if not content:
        raise exception(ErrorCode.ERR_ARTICLE_CONTENT_REQUIRED, http_status=400)

    article.title = title
    if not (article.summary or "").strip():
        article.summary = _generate_summary(title, article.content_md)

    _check_sensitive_fields(article)

    now = datetime.now(timezone.utc)
    article.status = ArticleStatus.PUBLISHED.value
    article.review_status = ReviewStatus.PENDING.value
    if article.published_at is None:
        article.published_at = now

    try:
        article_repo.touch_updated(db, article)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise exception(ErrorCode.ERR_ARTICLE_SAVE_FAILED, http_status=409) from exc

    fresh = article_repo.get_by_id(db, article_id)
    if not fresh:
        raise exception(ErrorCode.ERR_ARTICLE_NOT_FOUND, http_status=404)
    return _to_vo(fresh, user.username)
