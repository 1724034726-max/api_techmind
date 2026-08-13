# 用户数据访问
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    # 按主键查询
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> User | None:
    # 按用户名精确查询
    stmt = select(User).where(User.username == username)
    return db.scalars(stmt).first()


def get_by_email(db: Session, email: str) -> User | None:
    # 按邮箱查询（调用方传入小写）
    stmt = select(User).where(User.email == email)
    return db.scalars(stmt).first()


def get_by_account(db: Session, account: str) -> User | None:
    # 用户名精确匹配，或邮箱小写匹配
    email = account.lower()
    stmt = select(User).where(or_(User.username == account, User.email == email))
    return db.scalars(stmt).first()


def create(db: Session, user: User) -> User:
    # 插入用户并 flush 拿到持久化状态
    db.add(user)
    db.flush()
    return user


def update_login_time(db: Session, user: User) -> User:
    # 更新最近登录时间
    now = datetime.now(timezone.utc)
    user.last_login_at = now
    user.updated_at = now
    db.flush()
    return user


def update_theme(db: Session, user: User, theme: str) -> User:
    # 更新主题偏好
    now = datetime.now(timezone.utc)
    user.theme = theme
    user.updated_at = now
    db.flush()
    return user
