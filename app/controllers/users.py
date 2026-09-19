# 用户资料、设置路由
from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.schemas.common import ApiResponse
from app.schemas.user import ChangePasswordDTO, PublicUserVO, UpdateProfileDTO, UpdateThemeDTO, UserVO
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


@router.patch("/me", response_model=ApiResponse[UserVO])
def update_me(
    payload: UpdateProfileDTO,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[UserVO]:
    # 更新资料
    return ApiResponse.ok(user_service.update_profile(db, current_user, payload))


@router.post("/me/password", response_model=ApiResponse[None])
def change_password(
    payload: ChangePasswordDTO,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    # 修改密码
    user_service.change_password(db, current_user, payload.old_password, payload.new_password)
    return ApiResponse.ok(None)


@router.get("/{user_id}", response_model=ApiResponse[PublicUserVO])
def get_user(user_id: int, db: DbSession, _: CurrentUser) -> ApiResponse[PublicUserVO]:
    # 作者公开资料
    return ApiResponse.ok(user_service.get_public(db, user_id))
