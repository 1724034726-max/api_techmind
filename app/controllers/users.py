# 用户资料、设置路由
from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.schemas.common import ApiResponse
from app.schemas.user import UpdateThemeDTO, UserVO
from app.services import user_service

router = APIRouter(tags=["users"])


@router.patch("/me/theme", response_model=ApiResponse[UserVO])
def update_my_theme(
    payload: UpdateThemeDTO,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[UserVO]:
    # 更新当前登录用户的主题偏好
    data = user_service.update_theme(db, current_user, payload.theme)
    return ApiResponse.ok(data)
