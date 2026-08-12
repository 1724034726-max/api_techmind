# 密码哈希与 JWT 相关工具
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import exception


def hash_password(plain: str) -> str:
    # 明文密码转 bcrypt 哈希
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    # 校验明文与哈希是否匹配
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(*, user_id: int, username: str, role: str) -> tuple[str, int]:
    """签发访问令牌，返回 (token, expires_in_seconds)。"""
    settings = get_settings()
    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """解析并校验 JWT，失败时抛出业务异常。"""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise exception(ErrorCode.ERR_TOKEN_EXPIRED, http_status=401) from exc
    except jwt.InvalidTokenError as exc:
        raise exception(ErrorCode.ERR_TOKEN_INVALID, http_status=401) from exc
