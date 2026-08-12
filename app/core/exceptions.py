# 自定义业务异常（配合 ErrorCode 抛出）
from __future__ import annotations

from typing import Any

from app.core.error_codes import ErrorCode


class AppException(Exception):
    """业务异常：raise AppException(ErrorCode.ERR_PASSWORD_WRONG)。"""

    def __init__(
        self,
        error: ErrorCode,
        *,
        detail: Any = None,
        http_status: int = 400,
    ) -> None:
        # 错误码枚举
        self.error = error
        # 对外错误码
        self.code = error.code
        # 对外错误文案
        self.message = error.message
        # 可选附加信息（校验细节等）
        self.detail = detail
        # 映射的 HTTP 状态码
        self.http_status = http_status
        super().__init__(self.message)


# 短别名，便于 raise exception(ErrorCode.XXX)
exception = AppException
