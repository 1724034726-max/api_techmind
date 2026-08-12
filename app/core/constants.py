# 公共常量（角色、账号状态等）
from enum import Enum


class UserRole(str, Enum):
    """用户身份。"""

    READER = "reader"
    AUTHOR = "author"
    BOTH = "both"


class UserStatus(str, Enum):
    """账号状态。"""

    ACTIVE = "active"
    DISABLED = "disabled"


# 注册时简介缺省文案
DEFAULT_BIO = "这位用户还没有填写简介"
