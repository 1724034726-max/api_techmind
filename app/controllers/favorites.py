# 收藏列表
from fastapi import APIRouter, Query

from app.deps import CurrentUser, DbSession
from app.schemas.common import ApiResponse
from app.schemas.engagement import FavoriteListVO
from app.services import engagement_service

router = APIRouter(tags=["favorites"])


@router.get("", response_model=ApiResponse[FavoriteListVO])
def list_favorites(
    db: DbSession,
    current_user: CurrentUser,
    folder: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[FavoriteListVO]:
    # 按夹列出收藏
    name = folder.strip() if folder else None
    data = engagement_service.list_favorites(
        db, current_user, name or None, limit, offset
    )
    return ApiResponse.ok(data)
