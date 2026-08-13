# 文章草稿路由（本迭代不含发布）
from fastapi import APIRouter, Query

from app.deps import CurrentUser, DbSession
from app.schemas.article import (
    ArticleListVO,
    ArticleVO,
    CreateArticleDTO,
    UpdateArticleDTO,
)
from app.schemas.common import ApiResponse
from app.services import article_service

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


@router.get("/mine", response_model=ApiResponse[ArticleListVO])
def list_my_articles(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[ArticleListVO]:
    # 当前用户草稿列表
    data = article_service.list_my_drafts(
        db, current_user, limit=limit, offset=offset
    )
    return ApiResponse.ok(data)


@router.get("/{article_id}", response_model=ApiResponse[ArticleVO])
def get_article(
    article_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[ArticleVO]:
    # 草稿详情（仅作者）
    data = article_service.get_draft(db, current_user, article_id)
    return ApiResponse.ok(data)


@router.patch("/{article_id}", response_model=ApiResponse[ArticleVO])
def update_article(
    article_id: int,
    payload: UpdateArticleDTO,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[ArticleVO]:
    # 更新草稿
    data = article_service.update_draft(db, current_user, article_id, payload)
    return ApiResponse.ok(data)


@router.delete("/{article_id}", response_model=ApiResponse[None])
def delete_article(
    article_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    # 删除草稿
    article_service.delete_draft(db, current_user, article_id)
    return ApiResponse.ok(None)
