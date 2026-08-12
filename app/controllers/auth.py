# 认证路由：登录 / 注册 / 当前用户
from fastapi import APIRouter, status

from app.deps import CurrentUser, DbSession
from app.schemas.auth import LoginDTO, RegisterDTO, TokenVO
from app.schemas.common import ApiResponse
from app.schemas.user import UserVO
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post(
    "/register",
    response_model=ApiResponse[TokenVO],
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterDTO, db: DbSession) -> ApiResponse[TokenVO]:
    # 用户注册（成功即登录）
    data = auth_service.register(db, payload)
    return ApiResponse.ok(data)


@router.post("/login", response_model=ApiResponse[TokenVO])
def login(payload: LoginDTO, db: DbSession) -> ApiResponse[TokenVO]:
    # 用户登录
    data = auth_service.login(db, payload)
    return ApiResponse.ok(data)


@router.get("/me", response_model=ApiResponse[UserVO])
def me(current_user: CurrentUser) -> ApiResponse[UserVO]:
    # 获取当前登录用户
    data = auth_service.get_me(current_user)
    return ApiResponse.ok(data)
