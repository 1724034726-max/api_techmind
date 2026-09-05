# 认证路由：登录 / 注册 / 当前用户 / 登出
from fastapi import APIRouter, Response, status

from app.core.auth_cookie import clear_access_token_cookie, set_access_token_cookie
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
def register(
    payload: RegisterDTO, db: DbSession, response: Response
) -> ApiResponse[TokenVO]:
    # 用户注册（成功即登录）
    data = auth_service.register(db, payload)
    set_access_token_cookie(response, data.access_token, data.expires_in)
    return ApiResponse.ok(data)


@router.post("/login", response_model=ApiResponse[TokenVO])
def login(payload: LoginDTO, db: DbSession, response: Response) -> ApiResponse[TokenVO]:
    # 用户登录
    data = auth_service.login(db, payload)
    set_access_token_cookie(response, data.access_token, data.expires_in)
    return ApiResponse.ok(data)


@router.post("/logout", response_model=ApiResponse[None])
def logout(response: Response) -> ApiResponse[None]:
    # 登出
    clear_access_token_cookie(response)
    return ApiResponse.ok(None)


@router.get("/me", response_model=ApiResponse[UserVO])
def me(current_user: CurrentUser) -> ApiResponse[UserVO]:
    # 获取当前登录用户
    data = auth_service.get_me(current_user)
    return ApiResponse.ok(data)
