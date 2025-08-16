import traceback
from typing import Union

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from tradingapi.schemas.response import APIResponse


class BusinessException(Exception):
    """业务异常基类"""

    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationException(BusinessException):
    """数据验证异常"""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class ResourceNotFoundException(BusinessException):
    """资源未找到异常"""

    def __init__(self, resource: str, identifier: Union[str, int]):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, "RESOURCE_NOT_FOUND")


class DatabaseException(BusinessException):
    """数据库操作异常"""

    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


# 全局异常处理器
async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    logger.warning(f"Business exception: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=400, content=APIResponse.fail(exc.message, exc.code).model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数验证异常处理器"""
    logger.warning(f"Validation error: {exc.errors()}")
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        error_details.append(f"{field}: {error['msg']}")

    return JSONResponse(
        status_code=422,
        content=APIResponse.fail(
            "Request validation failed", data={"details": error_details}
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse.fail(str(exc.detail)).model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.error(f"Unhandled exception [trace_id: {trace_id}]: {str(exc)}")
    logger.debug(f"Exception traceback: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content=APIResponse.fail(
            "Internal server error, ", data={"trace_id": trace_id}
        ).model_dump(),
    )
