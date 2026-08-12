# 全局异常过滤器：统一转成 ApiResponse
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.schemas.common import ApiResponse


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。"""

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        # 业务异常 → 统一响应体
        body = ApiResponse.fail(exc.error, data=exc.detail, message=exc.message)
        return JSONResponse(status_code=exc.http_status, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # 参数校验失败
        body = ApiResponse.fail(ErrorCode.ERR_VALIDATION, data=exc.errors())
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        # FastAPI / Starlette HTTPException 映射到业务码
        error = _map_http_status(exc.status_code)
        detail = exc.detail if not isinstance(exc.detail, str) else None
        message = exc.detail if isinstance(exc.detail, str) else error.message
        body = ApiResponse.fail(error, data=detail, message=message)
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
        # 未捕获异常兜底（避免把堆栈直接暴露给前端）
        body = ApiResponse.fail(ErrorCode.ERR_UNKNOWN)
        return JSONResponse(status_code=500, content=body.model_dump())


def _map_http_status(status_code: int) -> ErrorCode:
    # 将常见 HTTP 状态映射到错误码
    if status_code == 401:
        return ErrorCode.ERR_UNAUTHORIZED
    if status_code == 403:
        return ErrorCode.ERR_FORBIDDEN
    if status_code == 404:
        return ErrorCode.ERR_NOT_FOUND
    if status_code == 422:
        return ErrorCode.ERR_VALIDATION
    return ErrorCode.ERR_UNKNOWN
