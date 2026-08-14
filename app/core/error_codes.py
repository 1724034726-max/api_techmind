# 业务错误码枚举（code -> 中文 message）
from enum import Enum


class ErrorCode(Enum):
    """错误码：调用时 raise AppException(ErrorCode.XXX)。"""

    # —— 通用 ——
    OK = ("0", "ok")
    ERR_UNKNOWN = ("err10000001", "服务器内部错误")
    ERR_VALIDATION = ("err10000002", "请求参数校验失败")
    ERR_UNAUTHORIZED = ("err10000003", "未登录或登录已失效")
    ERR_FORBIDDEN = ("err10000004", "无权限访问")
    ERR_NOT_FOUND = ("err10000005", "资源不存在")

    # —— 认证 / 用户 ——
    ERR_ACCOUNT_NOT_FOUND = ("err21234333", "账号不存在，请先注册")
    ERR_PASSWORD_WRONG = ("err21234334", "密码错误")
    ERR_ACCOUNT_EXISTS = ("err21234335", "用户名或邮箱已被注册")
    ERR_TOKEN_INVALID = ("err21234336", "无效的访问令牌")
    ERR_TOKEN_EXPIRED = ("err21234337", "访问令牌已过期")
    ERR_ACCOUNT_DISABLED = ("err21234338", "账号已禁用")
    ERR_SENSITIVE_WORD = ("err21234339", "标签包含敏感词，请修改后重试")

    # —— 文章 / 草稿 ——
    ERR_ARTICLE_NOT_FOUND = ("err31200001", "文章不存在")
    ERR_ARTICLE_NOT_AUTHOR = ("err31200004", "无权操作该文章")
    ERR_ARTICLE_STATUS = ("err31200005", "当前状态不允许该操作")
    ERR_ARTICLE_SAVE_FAILED = ("err31200006", "文章保存失败，请稍后重试")

    # —— 写作 AI ——
    ERR_AI_NOT_CONFIGURED = ("err41200001", "写作助手未配置，请联系管理员")
    ERR_AI_UPSTREAM = ("err41200002", "写作助手暂时不可用，请稍后重试")
    ERR_AI_BAD_RESPONSE = ("err41200003", "写作助手返回格式异常，请重试")

    def __init__(self, code: str, message: str) -> None:
        # 业务错误码字符串
        self.code = code
        # 对外展示文案
        self.message = message
