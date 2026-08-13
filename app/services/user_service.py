# 用户 / 资料业务逻辑
from sqlalchemy.orm import Session

from app.core.constants import ThemePreference
from app.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserVO


def _to_user_vo(user: User) -> UserVO:
    return UserVO.model_validate(user)


def update_theme(db: Session, user: User, theme: ThemePreference) -> UserVO:
    # 更新当前用户主题并提交
    value = theme.value if isinstance(theme, ThemePreference) else theme
    user_repo.update_theme(db, user, value)
    db.commit()
    db.refresh(user)
    return _to_user_vo(user)
