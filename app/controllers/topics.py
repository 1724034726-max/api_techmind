# 专题
from fastapi import APIRouter, Query, status

from app.deps import CurrentUser, DbSession
from app.schemas.common import ApiResponse
from app.schemas.topic import (
    SetTopicArticlesDTO,
    TopicDTO,
    TopicDetailVO,
    TopicListVO,
    UpdateTopicDTO,
)
from app.services import topic_service

router = APIRouter(tags=["topics"])


@router.get("", response_model=ApiResponse[TopicListVO])
def list_topics(
    db: DbSession,
    _: CurrentUser,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[TopicListVO]:
    # 专题列表
    return ApiResponse.ok(topic_service.list_topics(db, limit, offset))


@router.post("", response_model=ApiResponse[TopicDetailVO], status_code=status.HTTP_201_CREATED)
def create_topic(
    payload: TopicDTO, db: DbSession, current_user: CurrentUser
) -> ApiResponse[TopicDetailVO]:
    # 创建专题
    data = topic_service.create_topic(db, current_user, payload.title, payload.summary)
    return ApiResponse.ok(data)


@router.get("/{topic_id}", response_model=ApiResponse[TopicDetailVO])
def get_topic(topic_id: int, db: DbSession, _: CurrentUser) -> ApiResponse[TopicDetailVO]:
    # 专题详情
    return ApiResponse.ok(topic_service.get_topic(db, topic_id))


@router.patch("/{topic_id}", response_model=ApiResponse[TopicDetailVO])
def update_topic(
    topic_id: int,
    payload: UpdateTopicDTO,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[TopicDetailVO]:
    # 更新专题
    data = topic_service.update_topic(
        db, current_user, topic_id, payload.model_dump(exclude_unset=True)
    )
    return ApiResponse.ok(data)


@router.delete("/{topic_id}", response_model=ApiResponse[None])
def delete_topic(
    topic_id: int, db: DbSession, current_user: CurrentUser
) -> ApiResponse[None]:
    # 删除专题
    topic_service.delete_topic(db, current_user, topic_id)
    return ApiResponse.ok(None)


@router.put("/{topic_id}/articles", response_model=ApiResponse[TopicDetailVO])
def set_topic_articles(
    topic_id: int,
    payload: SetTopicArticlesDTO,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[TopicDetailVO]:
    # 替换专题文章
    data = topic_service.set_articles(db, current_user, topic_id, payload.article_ids)
    return ApiResponse.ok(data)
