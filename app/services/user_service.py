# 用户 / 资料业务逻辑
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import ThemePreference
from app.core.error_codes import ErrorCode
from app.core.exceptions import exception
from app.core.security import hash_password, verify_password
from app.core.sensitive import find_sensitive
from app.models.user import User
from app.repositories import user_repo
from app.schemas.user import PublicUserVO, UpdateProfileDTO, UserVO


def _to_user_vo(user: User) -> UserVO:
    return UserVO.model_validate(user)


def update_theme(db: Session, user: User, theme: ThemePreference) -> UserVO:
    # 更新当前用户主题并提交
    value = theme.value if isinstance(theme, ThemePreference) else theme
    user_repo.update_theme(db, user, value)
    db.commit()
    db.refresh(user)
    return _to_user_vo(user)


def get_public(db: Session, user_id: int) -> PublicUserVO:
    # 作者公开资料
    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise exception(ErrorCode.ERR_NOT_FOUND, http_status=404)
    return PublicUserVO.model_validate(user)


def update_profile(db: Session, user: User, payload: UpdateProfileDTO) -> UserVO:
    # 更新用户名、简介、身份、兴趣标签
    data = payload.model_dump(exclude_unset=True)
    if "username" in data and data["username"] != user.username:
        taken = user_repo.get_by_username(db, data["username"])
        if taken and taken.id != user.id:
            raise exception(ErrorCode.ERR_ACCOUNT_EXISTS, http_status=409)
        user.username = data["username"]
    if "bio" in data:
        hit = find_sensitive(data["bio"] or "")
        if hit is not None:
            raise exception(ErrorCode.ERR_SENSITIVE_WORD, http_status=400, detail={"word": hit})
        user.bio = data["bio"]
    if "role" in data and data["role"] is not None:
        user.role = data["role"].value if hasattr(data["role"], "value") else data["role"]
    if "tags" in data:
        user.tags = data["tags"]
    user.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise exception(ErrorCode.ERR_ACCOUNT_EXISTS, http_status=409) from exc
    db.refresh(user)
    return _to_user_vo(user)


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    # 校验旧密码后更新哈希
    if not verify_password(old_password, user.password_hash):
        raise exception(ErrorCode.ERR_PASSWORD_WRONG, http_status=400)
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
