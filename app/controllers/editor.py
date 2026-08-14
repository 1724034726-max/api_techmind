# 写作助手 AI 路由
from fastapi import APIRouter

from app.deps import CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.editor_ai import (
    ExpandDTO,
    ExpandVO,
    OpeningDTO,
    OpeningVO,
    SummaryDTO,
    SummaryVO,
    TopicAnalyzeDTO,
    TopicAnalyzeVO,
)
from app.services import editor_ai_service

router = APIRouter(tags=["editor-ai"])


@router.post("/ai/topic-analyze", response_model=ApiResponse[TopicAnalyzeVO])
def topic_analyze(
    payload: TopicAnalyzeDTO,
    current_user: CurrentUser,
) -> ApiResponse[TopicAnalyzeVO]:
    # 选题分析（需登录）
    _ = current_user
    data = editor_ai_service.analyze_topic(payload)
    return ApiResponse.ok(data)


@router.post("/ai/expand", response_model=ApiResponse[ExpandVO])
def expand(
    payload: ExpandDTO,
    current_user: CurrentUser,
) -> ApiResponse[ExpandVO]:
    # 大纲扩写
    _ = current_user
    data = editor_ai_service.expand_draft(payload)
    return ApiResponse.ok(data)


@router.post("/ai/summary", response_model=ApiResponse[SummaryVO])
def summary(
    payload: SummaryDTO,
    current_user: CurrentUser,
) -> ApiResponse[SummaryVO]:
    # 导读候选
    _ = current_user
    data = editor_ai_service.polish_summary(payload)
    return ApiResponse.ok(data)


@router.post("/ai/opening", response_model=ApiResponse[OpeningVO])
def opening(
    payload: OpeningDTO,
    current_user: CurrentUser,
) -> ApiResponse[OpeningVO]:
    # 开头候选
    _ = current_user
    data = editor_ai_service.polish_opening(payload)
    return ApiResponse.ok(data)
