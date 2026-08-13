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


class ThemePreference(str, Enum):
    """账号主题偏好（未登录前端固定 light）。"""

    LIGHT = "light"
    DARK = "dark"


class ArticleStatus(str, Enum):
    """文章状态（本迭代仅开放 draft）。"""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ReviewStatus(str, Enum):
    """审核状态（发布流程未做，默认 none）。"""

    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# 注册时简介缺省文案
DEFAULT_BIO = "这位用户还没有填写简介"

# 文章分类白名单（草稿可先用默认）
ARTICLE_CATEGORIES = ("后端", "前端", "AI", "云原生")
