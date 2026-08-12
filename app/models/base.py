# SQLAlchemy 声明式基类
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM Model 的基类。"""

    pass
