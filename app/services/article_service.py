# 文章 / 草稿业务逻辑（本迭代不含发布）
from sqlalchemy.orm import Session

from app.core.constants import (
    ARTICLE_CATEGORIES,
    ArticleStatus,
    ReviewStatus,
    UserRole,
)
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

    # 校验分类白名单
    category = payload.category.strip() or "后端"
    if category not in ARTICLE_CATEGORIES:
        raise exception(ErrorCode.ERR_VALIDATION, http_status=422)

    # 组装并落库草稿
    article = Article(
        id=next_id(),
        author_id=user.id,
        title=(payload.title or "").strip()[:200],
        subtitle=(payload.subtitle or "").strip()[:200],
        summary=(payload.summary or "").strip()[:500],
        content_md=payload.content_md or "",
        tags=list(payload.tags or [])[:8],
        category=category,
        column_name=(payload.column_name or "").strip()[:120],
        cover_url=(payload.cover_url or "").strip()[:512],
        status=ArticleStatus.DRAFT.value,
        review_status=ReviewStatus.NONE.value,
    )
    article_repo.create(db, article)
    db.commit()
    db.refresh(article)
    return _to_vo(article, user.username)


def update_draft(
    db: Session, user: User, article_id: int, payload: UpdateArticleDTO
) -> ArticleVO:
    _ensure_can_write(user)
    article = _get_owned_draft(db, user, article_id)

    # 按传入字段局部更新
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"] is not None:
        article.title = str(data["title"]).strip()[:200]
    if "subtitle" in data and data["subtitle"] is not None:
        article.subtitle = str(data["subtitle"]).strip()[:200]
    if "summary" in data and data["summary"] is not None:
        article.summary = str(data["summary"]).strip()[:500]
    if "content_md" in data and data["content_md"] is not None:
        article.content_md = str(data["content_md"])
    if "tags" in data and data["tags"] is not None:
        article.tags = list(data["tags"])[:8]
    if "category" in data and data["category"] is not None:
        category = str(data["category"]).strip() or "后端"
        if category not in ARTICLE_CATEGORIES:
            raise exception(ErrorCode.ERR_VALIDATION, http_status=422)
        article.category = category
    if "column_name" in data and data["column_name"] is not None:
        article.column_name = str(data["column_name"]).strip()[:120]
    if "cover_url" in data and data["cover_url"] is not None:
        article.cover_url = str(data["cover_url"]).strip()[:512]

    article_repo.touch_updated(db, article)
    db.commit()
    db.refresh(article)
    return _to_vo(article, user.username)


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
    article_repo.delete(db, article)
    db.commit()
