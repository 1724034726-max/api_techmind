# FastAPI 公共依赖（数据库会话、当前用户等）
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.constants import UserStatus
from app.core.error_codes import ErrorCode
from app.core.exceptions import exception
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories import user_repo

# Bearer 鉴权方案（不自动抛 403，便于转业务错误码）
_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    # 校验 Authorization Bearer
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise exception(ErrorCode.ERR_UNAUTHORIZED, http_status=401)

    # 解析 JWT
    payload = decode_access_token(credentials.credentials)
    sub = payload.get("sub")
    if not sub:
        raise exception(ErrorCode.ERR_TOKEN_INVALID, http_status=401)

    try:
        user_id = int(sub)
    except (TypeError, ValueError) as exc:
        raise exception(ErrorCode.ERR_TOKEN_INVALID, http_status=401) from exc

    # 查库确认用户仍有效
    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise exception(ErrorCode.ERR_UNAUTHORIZED, http_status=401)
    if user.status != UserStatus.ACTIVE.value:
        raise exception(ErrorCode.ERR_ACCOUNT_DISABLED, http_status=403)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
