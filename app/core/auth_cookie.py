# 访问令牌 Cookie
from fastapi import Response

from app.config import get_settings

ACCESS_TOKEN_COOKIE = "tm_access_token"


def set_access_token_cookie(response: Response, token: str, max_age: int) -> None:
    """登录/注册成功后写入 httpOnly Cookie。"""
    settings = get_settings()
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=max_age,
        path="/",
        httponly=True,
        samesite="none",
        secure=settings.cookie_secure,
        domain=settings.cookie_domain.strip() or None,
    )


def clear_access_token_cookie(response: Response) -> None:
    """登出时清除访问令牌 Cookie。"""
    settings = get_settings()
    domain = settings.cookie_domain.strip() or None
    _delete_access_token_cookie(response, settings.cookie_secure, domain)
    if domain:
        _delete_access_token_cookie(response, settings.cookie_secure, None)


def _delete_access_token_cookie(
    response: Response, secure: bool, domain: str | None
) -> None:
    """按指定 Domain 过期访问令牌（无 Domain 的旧票也要清）。"""
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
        samesite="none",
        secure=secure,
        domain=domain,
    )
