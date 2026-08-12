# 通用 Schema（分页、统一响应体等）
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.error_codes import ErrorCode

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """全局统一返回结构：code / message / data。"""

    code: str = Field(default=ErrorCode.OK.code, description="业务错误码，0 表示成功")
    message: str = Field(default=ErrorCode.OK.message, description="提示文案")
    data: T | None = Field(default=None, description="业务数据")

    @classmethod
    def ok(cls, data: Any = None, message: str | None = None) -> "ApiResponse[Any]":
        # 成功响应
        return cls(
            code=ErrorCode.OK.code,
            message=message if message is not None else ErrorCode.OK.message,
            data=data,
        )

    @classmethod
    def fail(
        cls,
        error: ErrorCode,
        *,
        data: Any = None,
        message: str | None = None,
    ) -> "ApiResponse[Any]":
        # 失败响应（一般由全局异常过滤器构造）
        return cls(
            code=error.code,
            message=message if message is not None else error.message,
            data=data,
        )
