# 认证业务逻辑
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_BIO, ThemePreference, UserRole, UserStatus
from app.core.error_codes import ErrorCode
from app.core.exceptions import exception
from app.core.security import create_access_token, hash_password, verify_password
from app.core.sensitive import first_sensitive_in_tags
from app.core.snowflake import next_id
from app.models.user import User
from app.repositories import user_repo
from app.schemas.auth import LoginDTO, RegisterDTO, TokenVO
from app.schemas.user import UserVO


def _to_user_vo(user: User) -> UserVO:
    # ORM 转用户 VO
    return UserVO.model_validate(user)


def _build_token_vo(user: User) -> TokenVO:
    # 签发 JWT 并组装返回
    token, expires_in = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )
    return TokenVO(
        access_token=token,
        expires_in=expires_in,
        user=_to_user_vo(user),
    )


def register(db: Session, payload: RegisterDTO) -> TokenVO:
    # 规范化邮箱
    email = str(payload.email).lower()

    # 清洗标签并做敏感词校验
    tags = [t.strip() for t in payload.tags if t and t.strip()]
    hit = first_sensitive_in_tags(tags)
    if hit is not None:
        raise exception(ErrorCode.ERR_SENSITIVE_WORD, http_status=400, detail={"word": hit})

    # 组装用户并落库
    bio = (payload.bio or "").strip() or DEFAULT_BIO
    user = User(
        id=next_id(),
        username=payload.username,
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role.value if isinstance(payload.role, UserRole) else payload.role,
        tags=tags,
        bio=bio,
        theme=ThemePreference.LIGHT.value,
        followers_count=0,
        following_count=0,
        status=UserStatus.ACTIVE.value,
    )
    try:
        with db.begin():
            user_repo.create(db, user)
    except IntegrityError as exc:
        # 用户名或邮箱已存在
        raise exception(ErrorCode.ERR_ACCOUNT_EXISTS, http_status=409) from exc

    db.refresh(user)
    return _build_token_vo(user)


def login(db: Session, payload: LoginDTO) -> TokenVO:
    # 按账号查找用户
    user = user_repo.get_by_account(db, payload.account)
    if not user:
        raise exception(ErrorCode.ERR_ACCOUNT_NOT_FOUND, http_status=400)

    # 禁用账号不可登录
    if user.status != UserStatus.ACTIVE.value:
        raise exception(ErrorCode.ERR_ACCOUNT_DISABLED, http_status=403)

    # 校验密码
    if not verify_password(payload.password, user.password_hash):
        raise exception(ErrorCode.ERR_PASSWORD_WRONG, http_status=400)

    # 更新最近登录时间
    user_repo.update_login_time(db, user)
    db.commit()
    db.refresh(user)
    return _build_token_vo(user)


def get_me(user: User) -> UserVO:
    # 返回当前登录用户
    return _to_user_vo(user)
