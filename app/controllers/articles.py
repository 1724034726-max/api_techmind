# 文章草稿 / 发布路由
from fastapi import APIRouter, Query

from app.core.constants import ArticleStatus
from app.deps import CurrentUser, DbSession
from app.schemas.article import (
    ArticleListVO,
    ArticleVO,
    CreateArticleDTO,
    PublishArticleDTO,
    UpdateArticleDTO,
)
from app.schemas.common import ApiResponse
from app.schemas.engagement import CommentDTO, CommentListVO, CommentVO, EngageStateVO, FavoriteDTO
from app.services import article_service, engagement_service

router = APIRouter(tags=["articles"])


@router.post("", response_model=ApiResponse[ArticleVO], status_code=201)
def create_article(
    payload: CreateArticleDTO,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[ArticleVO]:
    # 创建草稿
    data = article_service.create_draft(db, current_user, payload)
    return ApiResponse.ok(data)


@router.get("", response_model=ApiResponse[ArticleListVO])
def list_published(
    db: DbSession,
    _: CurrentUser,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    author_id: int | None = Query(default=None),
    column_name: str | None = Query(default=None, max_length=120),
) -> ApiResponse[ArticleListVO]:
    # 已发布列表；可按作者或专栏名筛选
    name = column_name.strip() if column_name else None
    data = article_service.list_published(
        db, limit=limit, offset=offset, author_id=author_id, column_name=name or None
    )
    return ApiResponse.ok(data)


@router.get("/mine", response_model=ApiResponse[ArticleListVO])
def list_my_articles(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    status: ArticleStatus | None = Query(default=ArticleStatus.DRAFT),
) -> ApiResponse[ArticleListVO]:
    # 当前用户文章；默认草稿
    data = article_service.list_my_articles(
        db,
        current_user,
        status=status.value,
        limit=limit,
        offset=offset,
    )
    return ApiResponse.ok(data)


@router.get("/{article_id}", response_model=ApiResponse[ArticleVO])
def get_article(
    article_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[ArticleVO]:
    # 已发布公开；草稿/下架仅作者
    data = article_service.get_article(db, current_user, article_id)
    return ApiResponse.ok(data)


@router.patch("/{article_id}", response_model=ApiResponse[ArticleVO])
def update_article(
    article_id: int,
    payload: UpdateArticleDTO,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[ArticleVO]:
    # 更新草稿或已发布文
    data = article_service.update_draft(db, current_user, article_id, payload)
    return ApiResponse.ok(data)


@router.post("/{article_id}/publish", response_model=ApiResponse[ArticleVO])
def publish_article(
    article_id: int,
    db: DbSession,
    current_user: CurrentUser,
    payload: PublishArticleDTO | None = None,
) -> ApiResponse[ArticleVO]:
    # 发布草稿（可带 body 合并元数据）
    data = article_service.publish_article(
        db, current_user, article_id, payload or PublishArticleDTO()
    )
    return ApiResponse.ok(data)


@router.delete("/{article_id}", response_model=ApiResponse[None])
def delete_article(
    article_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    # 草稿删除；已发布下架
    article_service.delete_article(db, current_user, article_id)
    return ApiResponse.ok(None)


@router.put("/{article_id}/like", response_model=ApiResponse[EngageStateVO])
def like_article(
    article_id: int, db: DbSession, current_user: CurrentUser
) -> ApiResponse[EngageStateVO]:
    # 点赞
    return ApiResponse.ok(engagement_service.like(db, current_user, article_id))


@router.delete("/{article_id}/like", response_model=ApiResponse[EngageStateVO])
def unlike_article(
    article_id: int, db: DbSession, current_user: CurrentUser
) -> ApiResponse[EngageStateVO]:
    # 取消点赞
    return ApiResponse.ok(engagement_service.unlike(db, current_user, article_id))


@router.put("/{article_id}/favorite", response_model=ApiResponse[EngageStateVO])
def favorite_article(
    article_id: int,
    db: DbSession,
    current_user: CurrentUser,
    payload: FavoriteDTO = FavoriteDTO(),
) -> ApiResponse[EngageStateVO]:
    # 收藏
    folder = payload.folder
    return ApiResponse.ok(engagement_service.favorite(db, current_user, article_id, folder))


@router.delete("/{article_id}/favorite", response_model=ApiResponse[EngageStateVO])
def unfavorite_article(
    article_id: int, db: DbSession, current_user: CurrentUser
) -> ApiResponse[EngageStateVO]:
    # 取消收藏
    return ApiResponse.ok(engagement_service.unfavorite(db, current_user, article_id))


@router.get("/{article_id}/comments", response_model=ApiResponse[CommentListVO])
def list_comments(
    article_id: int, db: DbSession, _: CurrentUser
) -> ApiResponse[CommentListVO]:
    # 评论列表
    return ApiResponse.ok(engagement_service.list_comments(db, article_id))


@router.post("/{article_id}/comments", response_model=ApiResponse[CommentVO], status_code=201)
def create_comment(
    article_id: int,
    payload: CommentDTO,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[CommentVO]:
    # 发表评论
    data = engagement_service.add_comment(db, current_user, article_id, payload.content)
    return ApiResponse.ok(data)


@router.delete("/{article_id}/comments/{comment_id}", response_model=ApiResponse[None])
def remove_comment(
    article_id: int,
    comment_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    # 删除自己的评论
    engagement_service.delete_comment(db, current_user, article_id, comment_id)
    return ApiResponse.ok(None)
